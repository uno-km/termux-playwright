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
import logging
import warnings
from typing import Set, Optional, Callable, Dict, Any, List
from .exceptions import ProcessLifecycleError

logger = logging.getLogger(__name__)

SIGKILL_SIGNAL = getattr(signal, "SIGKILL", getattr(signal, "SIGTERM", 9))

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
        """Forcefully terminate only registered child processes and session-tagged processes.
        
        Design: Snapshots tracked state under lock, then performs expensive I/O
        (subprocess calls for session zombie reaping) OUTSIDE the lock to prevent
        deadlock/freezing during atexit or signal handling.
        """
        # 1. Snapshot and clear under lock — O(1) swap, no I/O
        with cls._lock:
            pids_snapshot = set(cls._tracked_pids)
            sessions_snapshot = set(cls._tracked_sessions)
            cls._tracked_pids.clear()
            cls._tracked_sessions.clear()

        # 2. Kill directly tracked PIDs — no lock held, no subprocess calls
        for pid in pids_snapshot:
            try:
                os.kill(pid, SIGKILL_SIGNAL)
            except (ProcessLookupError, PermissionError):
                pass

        # 3. Reap session-scoped orphaned processes — no lock held
        #    Each session cleanup is isolated: one failure must not prevent others
        for token in sessions_snapshot:
            try:
                cls.reap_session_zombies(token)
            except Exception as exc:
                try:
                    logger.debug("Session zombie cleanup failed for %s: %s", token, exc)
                except Exception:
                    pass

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
                        pid_str = os.path.basename(os.path.dirname(cmdline_file))
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
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("pgrep fallback failed for session %s: %s", session_token, e)

        # Tier 3: ps / busybox ps / toolbox ps fallback for Android 11+ SELinux
        if not found_pids:
            found_pids.update(cls._discover_via_ps(session_flag))

        return found_pids

    @classmethod
    def _discover_via_ps(cls, session_flag: str) -> Set[int]:
        """Parse ps output to find processes matching session flag.
        Uses header-based PID column detection for cross-platform reliability."""
        found_pids: Set[int] = set()
        ps_commands: List[List[str]] = [
            ["ps", "-A", "-o", "pid,args"],
            ["ps", "-ef"],
            ["busybox", "ps", "-ef"],
            ["ps"],
        ]
        for ps_cmd in ps_commands:
            if not shutil.which(ps_cmd[0]):
                continue
            try:
                res = subprocess.run(
                    ps_cmd, capture_output=True, text=True, timeout=5, check=False
                )
                if res.returncode != 0:
                    continue
                lines = res.stdout.splitlines()
                if len(lines) < 2:
                    continue
                pid_col = cls._detect_pid_column(lines[0])
                for line in lines[1:]:
                    if session_flag not in line:
                        continue
                    parts = line.strip().split()
                    if pid_col < len(parts) and parts[pid_col].isdigit():
                        found_pids.add(int(parts[pid_col]))
                if found_pids:
                    break
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("ps fallback '%s' failed: %s", ' '.join(ps_cmd), e)
                continue
        return found_pids

    @staticmethod
    def _detect_pid_column(header_line: str) -> int:
        """Detect PID column index from ps header line.
        Returns 0-based column index. Falls back to 0 if PID header not found."""
        parts = header_line.strip().upper().split()
        for i, part in enumerate(parts):
            if part == "PID":
                return i
        return 0

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
                os.kill(pid, SIGKILL_SIGNAL)
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
                    warnings.warn(
                        f"Cannot install signal handler for {sig.name} "
                        f"(likely called from a non-main thread). "
                        f"Orphaned Chromium processes may not be cleaned up on {sig.name}. "
                        f"atexit cleanup is still registered.",
                        RuntimeWarning,
                        stacklevel=3,
                    )

            cls._installed_handlers = True


def cli_reap_orphans() -> None:
    """CLI entry point: Scan for and terminate orphaned Chromium processes
    tagged with termux-playwright session markers.
    
    Scans /proc/*/cmdline for any process containing --termux-session-id= flag
    and terminates them. Intended for manual cleanup of leaked browser processes.
    """
    session_flag = "--termux-session-id="
    session_flag_bytes = session_flag.encode("utf-8")
    found_pids: Set[int] = set()
    current_pid = os.getpid()

    # Primary: /proc scan
    proc_entries = glob.glob("/proc/[0-9]*/cmdline")
    for cmdline_file in proc_entries:
        try:
            with open(cmdline_file, "rb") as f:
                cmd_bytes = f.read()
                if session_flag_bytes in cmd_bytes:
                    pid_str = os.path.basename(os.path.dirname(cmdline_file))
                    if pid_str.isdigit():
                        pid = int(pid_str)
                        if pid != current_pid:
                            found_pids.add(pid)
        except (OSError, ValueError, PermissionError):
            continue

    # Secondary: pgrep
    if not found_pids:
        pgrep_bin = shutil.which("pgrep")
        if pgrep_bin:
            try:
                out = subprocess.run(
                    [pgrep_bin, "-f", session_flag],
                    capture_output=True, text=True, timeout=5, check=False,
                )
                if out.returncode == 0:
                    for line in out.stdout.strip().split("\n"):
                        stripped = line.strip()
                        if stripped.isdigit():
                            pid = int(stripped)
                            if pid != current_pid:
                                found_pids.add(pid)
            except (subprocess.TimeoutExpired, OSError):
                pass

    # Tertiary: ps / busybox ps for Android 11+ SELinux when pgrep is absent
    if not found_pids:
        ps_pids = ProcessReaper._discover_via_ps(session_flag)
        for pid in ps_pids:
            if pid != current_pid:
                found_pids.add(pid)

    if not found_pids:
        print("[*] No orphaned termux-playwright Chromium processes found.")
        return

    reaped = 0
    for pid in found_pids:
        try:
            os.kill(pid, SIGKILL_SIGNAL)
            reaped += 1
            print(f"[+] Killed orphaned process: PID {pid}")
        except ProcessLookupError:
            print(f"[*] Process {pid} already exited.")
        except PermissionError:
            print(f"[!] Permission denied for PID {pid}. Run as same user or root.")

    print(f"\n[*] Reap complete: {reaped}/{len(found_pids)} processes terminated.")


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
