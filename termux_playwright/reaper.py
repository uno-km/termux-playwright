"""Process lifecycle, targeted session zombie reaper, and Android WakeLock manager.

Ensures deterministic destruction of Chromium child processes without collateral damage
to unrelated user processes, and chains OS signal handlers cleanly.
"""

import atexit
import os
import signal
import subprocess
import shutil
import sys
import glob
from typing import Set, Optional, Callable, Dict, Any
from .exceptions import ProcessLifecycleError

class ProcessReaper:
    """Tracks and deterministically reaps Chromium processes scoped strictly to this session."""

    _tracked_pids: Set[int] = set()
    _tracked_sessions: Set[str] = set()
    _installed_handlers: bool = False
    _original_signal_handlers: Dict[int, Any] = {}

    @classmethod
    def register_pid(cls, pid: int) -> None:
        """Register a child process PID for lifecycle tracking."""
        cls._install_hooks_if_needed()
        if pid > 0:
            cls._tracked_pids.add(pid)

    @classmethod
    def unregister_pid(cls, pid: int) -> None:
        """Remove a cleanly exited child PID from tracking."""
        cls._tracked_pids.discard(pid)

    @classmethod
    def register_session_token(cls, session_token: str) -> None:
        """Register a unique session token for targeted process discovery."""
        cls._install_hooks_if_needed()
        cls._tracked_sessions.add(session_token)

    @classmethod
    def unregister_session_token(cls, session_token: str) -> None:
        """Remove session token when session closes cleanly."""
        cls._tracked_sessions.discard(session_token)

    @classmethod
    def kill_all_tracked(cls) -> None:
        """Forcefully terminate only registered child processes and session-tagged processes."""
        # 1. Kill directly tracked PIDs
        for pid in list(cls._tracked_pids):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            finally:
                cls._tracked_pids.discard(pid)

        # 2. Reap session-scoped orphaned processes via /proc inspection (No blind pkill)
        for token in list(cls._tracked_sessions):
            cls.reap_session_zombies(token)
            cls._tracked_sessions.discard(token)

    @classmethod
    def discover_session_pids(cls, session_token: str) -> Set[int]:
        """Inspect /proc to find PIDs specifically tagged with this session token."""
        found_pids: Set[int] = set()
        if not session_token:
            return found_pids

        # On Linux / Android Termux: inspect /proc/[pid]/cmdline
        proc_entries = glob.glob("/proc/[0-9]*/cmdline")
        for cmdline_file in proc_entries:
            try:
                with open(cmdline_file, "rb") as f:
                    cmd_bytes = f.read()
                    if f"--termux-session-id={session_token}".encode("utf-8") in cmd_bytes:
                        pid_str = cmdline_file.split("/")[2]
                        found_pids.add(int(pid_str))
            except (OSError, ValueError, PermissionError):
                continue

        # Fallback to pgrep -f strictly with session token
        if not found_pids and shutil.which("pgrep"):
            try:
                out = subprocess.run(
                    ["pgrep", "-f", f"--termux-session-id={session_token}"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if out.returncode == 0:
                    for line in out.stdout.strip().split("\n"):
                        if line.isdigit():
                            found_pids.add(int(line))
            except Exception:
                pass

        return found_pids

    @classmethod
    def reap_session_zombies(cls, session_token: str) -> int:
        """Targeted cleanup: Kills ONLY Chromium instances tagged with this exact session token.
        
        Zero collateral damage to other user browser sessions or background tasks.
        """
        target_pids = cls.discover_session_pids(session_token)
        reaped_count = 0
        current_pid = os.getpid()

        for pid in target_pids:
            if pid == current_pid:
                continue  # Never kill self
            try:
                os.kill(pid, signal.SIGKILL)
                reaped_count += 1
            except (ProcessLookupError, PermissionError):
                pass

        return reaped_count

    @classmethod
    def _install_hooks_if_needed(cls) -> None:
        """Install atexit and chained signal handlers without hijacking parent frameworks."""
        if cls._installed_handlers:
            return

        atexit.register(cls.kill_all_tracked)

        def _chained_signal_handler(signum, frame):
            cls.kill_all_tracked()
            prev_handler = cls._original_signal_handlers.get(signum)
            if callable(prev_handler):
                prev_handler(signum, frame)
            elif prev_handler == signal.SIG_DFL:
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum)
            else:
                sys.exit(128 + signum)

        for sig in [signal.SIGINT, signal.SIGTERM]:
            try:
                cls._original_signal_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, _chained_signal_handler)
            except (ValueError, AttributeError):
                # Signals cannot be trapped in non-main threads
                pass

        cls._installed_handlers = True


class TermuxWakeLock:
    """Context manager for acquiring and releasing Termux CPU WakeLock.
    
    Prevents Android Doze mode and CPU deep-sleep from suspending active crawlers.
    Strict by default: Raises ProcessLifecycleError if Termux API tools are missing.
    """

    def __init__(self, fail_silently: bool = False):
        self._acquired = False
        self._fail_silently = fail_silently
        self._lock_bin = shutil.which("termux-wake-lock")
        self._unlock_bin = shutil.which("termux-wake-unlock")

    def __enter__(self) -> "TermuxWakeLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def acquire(self) -> bool:
        """Acquire CPU WakeLock via Termux API."""
        if not self._lock_bin:
            if not self._fail_silently:
                raise ProcessLifecycleError(
                    "termux-wake-lock binary not found in PATH. "
                    "Inside Termux, install it via: 'pkg install termux-api'. "
                    "Or pass 'fail_silently=True' if WakeLock is not strictly required."
                )
            return False
            
        try:
            res = subprocess.run([self._lock_bin], check=True, capture_output=True, timeout=10)
            self._acquired = (res.returncode == 0)
            return self._acquired
        except Exception as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(f"Failed to acquire WakeLock: {e}") from e
            return False

    def release(self) -> bool:
        """Release CPU WakeLock."""
        if not self._acquired:
            return False
            
        if not self._unlock_bin:
            if not self._fail_silently:
                raise ProcessLifecycleError("termux-wake-unlock binary not found in PATH")
            return False

        try:
            res = subprocess.run([self._unlock_bin], check=True, capture_output=True, timeout=10)
            self._acquired = False
            return res.returncode == 0
        except Exception as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(f"Failed to release WakeLock: {e}") from e
            return False
