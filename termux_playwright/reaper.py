"""Process lifecycle, zombie process reaper, and Android WakeLock manager.

Ensures deterministic destruction of Chromium child processes and manages
Android wake-locks during 24/7 crawler lifecycles.
"""

import atexit
import os
import signal
import subprocess
import shutil
import sys
from typing import Set, Optional
from .exceptions import ProcessLifecycleError

class ProcessReaper:
    """Tracks and deterministically reaps orphaned Chromium processes."""

    _tracked_pids: Set[int] = set()
    _installed_handlers: bool = False

    @classmethod
    def register_pid(cls, pid: int) -> None:
        """Register a child process PID for lifecycle tracking."""
        cls._install_hooks_if_needed()
        cls._tracked_pids.add(pid)

    @classmethod
    def unregister_pid(cls, pid: int) -> None:
        """Remove a cleanly exited child PID from tracking."""
        cls._tracked_pids.discard(pid)

    @classmethod
    def kill_all_tracked(cls) -> None:
        """Forcefully terminate all registered child processes."""
        for pid in list(cls._tracked_pids):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            finally:
                cls._tracked_pids.discard(pid)

    @classmethod
    def reap_zombie_chromium(cls) -> int:
        """Scans for and kills orphaned Chromium processes belonging to the current user."""
        if shutil.which("pkill"):
            try:
                result = subprocess.run(
                    ["pkill", "-9", "-f", "chromium"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return 1 if result.returncode == 0 else 0
            except Exception as e:
                raise ProcessLifecycleError(f"Failed to execute pkill for zombie cleanup: {e}") from e
        return 0

    @classmethod
    def _install_hooks_if_needed(cls) -> None:
        if cls._installed_handlers:
            return
        atexit.register(cls.kill_all_tracked)
        
        # Signal handler for graceful termination
        def _signal_handler(signum, frame):
            cls.kill_all_tracked()
            sys.exit(128 + signum)

        for sig in [signal.SIGINT, signal.SIGTERM]:
            try:
                signal.signal(sig, _signal_handler)
            except (ValueError, AttributeError):
                # Signals might not be trapable in non-main threads
                pass
        cls._installed_handlers = True


class TermuxWakeLock:
    """Context manager for acquiring and releasing Termux CPU WakeLock.
    
    Prevents Android Doze mode and CPU deep-sleep from suspending active crawlers.
    """

    def __init__(self, fail_silently: bool = True):
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
                raise ProcessLifecycleError("termux-wake-lock binary not found in PATH")
            return False
            
        try:
            res = subprocess.run([self._lock_bin], check=True, capture_output=True)
            self._acquired = (res.returncode == 0)
            return self._acquired
        except Exception as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(f"Failed to acquire WakeLock: {e}") from e
            return False

    def release(self) -> bool:
        """Release CPU WakeLock."""
        if not self._acquired or not self._unlock_bin:
            return False
            
        try:
            res = subprocess.run([self._unlock_bin], check=True, capture_output=True)
            self._acquired = False
            return res.returncode == 0
        except Exception as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(f"Failed to release WakeLock: {e}") from e
            return False
