"""Process lifecycle, targeted session zombie reaper, and Android WakeLock manager.

Ensures deterministic destruction of Chromium child processes without collateral damage
to unrelated user processes, protects against multi-threading race conditions,
and preserves OS signal handlers (SIG_IGN / SIG_DFL) cleanly.
"""

import atexit
import asyncio
import os
import signal
import subprocess
import shutil
import sys
import glob
import threading
from typing import Set, Optional, Callable, Dict, Any, List
from .exceptions import ProcessLifecycleError

class ProcessReaper:
    """Thread-safe manager that tracks and reaps Chromium processes scoped strictly to this session."""

    _lock: threading.RLock = threading.RLock()
    _tracked_pids: Set[int] = set()
    _tracked_sessions: Set[str] = set()
    _installed_handlers: bool = False
    _original_signal_handlers: Dict[int, Any] = {}

    @classmethod
    def register_pid(cls, pid: int) -> None:
        """Register a child process PID for lifecycle tracking in a thread-safe manner."""
        with cls._lock:
            cls._install_hooks_if_needed()
            if pid > 0:
                cls._tracked_pids.add(pid)

    @classmethod
    def unregister_pid(cls, pid: int) -> None:
        """Remove a cleanly exited child PID from tracking."""
        with cls._lock:
            cls._tracked_pids.discard(pid)

    @classmethod
    def register_session_token(cls, session_token: str) -> None:
        """Register a unique session token for targeted process discovery."""
        with cls._lock:
            cls._install_hooks_if_needed()
            cls._tracked_sessions.add(session_token)

    @classmethod
    def unregister_session_token(cls, session_token: str) -> None:
        """Remove session token when session closes cleanly."""
        with cls._lock:
            cls._tracked_sessions.discard(session_token)

    @classmethod
    def kill_all_tracked(cls) -> None:
        """Forcefully terminate only registered child processes and session-tagged processes."""
        with cls._lock:
            # 1. Kill directly tracked PIDs
            for pid in list(cls._tracked_pids):
                try:
                    os.kill(pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
                finally:
                    cls._tracked_pids.discard(pid)

            # 2. Reap session-scoped orphaned processes via multi-tier inspection (No blind pkill)
            for token in list(cls._tracked_sessions):
                cls.reap_session_zombies(token)
                cls._tracked_sessions.discard(token)

    @classmethod
    def discover_session_pids(cls, session_token: str) -> Set[int]:
        """Multi-tier inspection to discover PIDs specifically tagged with this session token.
        
        Tier 1: Direct /proc/[pid]/cmdline inspection (Fastest on Linux).
        Tier 2: pgrep -f scanning (If procps is installed).
        Tier 3: ps -ef / busybox ps / ps -A fallback (Works on Android 11+ SELinux).
        """
        found_pids: Set[int] = set()
        if not session_token:
            return found_pids

        session_flag = f"--termux-session-id={session_token}"
        session_flag_bytes = session_flag.encode("utf-8")

        # Tier 1: Inspect /proc/[pid]/cmdline
        proc_entries = glob.glob("/proc/[0-9]*/cmdline")
        for cmdline_file in proc_entries:
            try:
                with open(cmdline_file, "rb") as f:
                    cmd_bytes = f.read()
                    if session_flag_bytes in cmd_bytes:
                        pid_str = cmdline_file.split("/")[2]
                        if pid_str.isdigit():
                            found_pids.add(int(pid_str))
            except (OSError, ValueError, PermissionError):
                continue

        # Tier 2: pgrep fallback
        if not found_pids and shutil.which("pgrep"):
            try:
                out = subprocess.run(
                    ["pgrep", "-f", session_flag],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                if out.returncode == 0:
                    for line in out.stdout.strip().split("\n"):
                        if line.strip().isdigit():
                            found_pids.add(int(line.strip()))
            except Exception:
                pass

        # Tier 3: ps / busybox ps / toolbox ps fallback for Android 11+ SELinux
        if not found_pids:
            ps_commands: List[List[str]] = [
                ["ps", "-ef"],
                ["busybox", "ps", "-ef"],
                ["ps", "-A", "-o", "pid,args"],
                ["ps"],
            ]
            for ps_cmd in ps_commands:
                if not shutil.which(ps_cmd[0]):
                    continue
                try:
                    res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=5, check=False)
                    if res.returncode == 0:
                        for line in res.stdout.splitlines():
                            if session_flag in line:
                                parts = line.strip().split()
                                # Typically PID is column 0 or 1
                                for part in parts[:3]:
                                    if part.isdigit():
                                        found_pids.add(int(part))
                                        break
                    if found_pids:
                        break
                except Exception:
                    continue

        return found_pids

    @classmethod
    def reap_session_zombies(cls, session_token: str) -> int:
        """Targeted synchronous cleanup: Kills ONLY Chromium instances tagged with this exact session token.
        
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
    async def reap_session_zombies_async(cls, session_token: str) -> int:
        """Non-blocking asynchronous version of reap_session_zombies."""
        return await asyncio.to_thread(cls.reap_session_zombies, session_token)

    @classmethod
    def _install_hooks_if_needed(cls) -> None:
        """Install atexit and chained signal handlers without hijacking parent frameworks."""
        with cls._lock:
            if cls._installed_handlers:
                return

            atexit.register(cls.kill_all_tracked)

            def _chained_signal_handler(signum, frame):
                cls.kill_all_tracked()
                prev_handler = cls._original_signal_handlers.get(signum)
                
                # Critical: If parent ignored the signal, preserve SIG_IGN and do NOT exit!
                if prev_handler == signal.SIG_IGN:
                    return
                elif callable(prev_handler):
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
                    # Signal registration fails if called from a non-main thread; gracefully skip
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
