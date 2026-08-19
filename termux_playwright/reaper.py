"""Process lifecycle, targeted session zombie reaper, and Android WakeLock manager.

Ensures deterministic destruction of Chromium child processes without collateral damage
to unrelated user processes, protects against multi-threading race conditions,
and preserves OS signal handlers (SIG_IGN / SIG_DFL) cleanly.
"""

import atexit
import asyncio
import os
import time
import signal
import subprocess
import shutil
import sys
import glob
import tempfile
import threading
import logging
import warnings
from typing import Set, Optional, Callable, Dict, Any, List
from .exceptions import ProcessLifecycleError

logger = logging.getLogger(__name__)

SIGKILL_SIGNAL = getattr(signal, "SIGKILL", 9)
SIGTERM_SIGNAL = getattr(signal, "SIGTERM", 15)
WNOHANG_FLAG = getattr(os, "WNOHANG", 1)

# True non-blocking waitpid with WNOHANG is strictly POSIX (Linux/Termux/macOS).
# On Windows, os.waitpid calls MSVCRT _cwait which blocks synchronously and causes hangs.
HAS_POSIX_WAITPID: bool = (
    hasattr(os, "waitpid")
    and hasattr(os, "WNOHANG")
    and sys.platform != "win32"
)

def _terminate_pid_gracefully(pid: int, graceful_timeout: float = 0.05) -> bool:
    """Attempt graceful SIGTERM first, waiting briefly for resource release, then SIGKILL if needed.
    
    Handles both direct children (reaped via waitpid on POSIX) and grandchild processes (Chromium spawned by Node.js driver)
    using bounded non-blocking kill polling to prevent event-loop freezing.
    """
    try:
        os.kill(pid, SIGTERM_SIGNAL)
    except (ProcessLookupError, PermissionError):
        return True

    # 1. Immediate non-blocking waitpid check for direct child processes (POSIX only)
    if HAS_POSIX_WAITPID:
        try:
            w_pid, _ = os.waitpid(pid, WNOHANG_FLAG)
            if w_pid == pid:
                return True
        except (ChildProcessError, OSError) as e:
            # Normal POSIX behavior for grandchild processes (Chromium spawned by Node)
            logger.debug("waitpid on PID %d (grandchild): %s", pid, e)

    # 2. Bounded brief polling for process exit (max 0.05s)
    deadline = time.time() + graceful_timeout
    while time.time() < deadline:
        if HAS_POSIX_WAITPID:
            try:
                w_pid, _ = os.waitpid(pid, WNOHANG_FLAG)
                if w_pid == pid:
                    return True
            except (ChildProcessError, OSError) as e:
                logger.debug("waitpid polling on PID %d: %s", pid, e)
        try:
            os.kill(pid, 0)
            time.sleep(0.01)
        except (ProcessLookupError, PermissionError):
            return True

    # 3. Forceful termination if process lingers
    try:
        os.kill(pid, SIGKILL_SIGNAL)
    except (ProcessLookupError, PermissionError):
        return True

    # 4. Final non-blocking reap for direct child (POSIX only)
    if HAS_POSIX_WAITPID:
        try:
            os.waitpid(pid, WNOHANG_FLAG)
        except (ChildProcessError, OSError) as e:
            logger.debug("final waitpid on PID %d: %s", pid, e)

    return True

class ProcessReaper:
    """Thread-safe unified process manager for Termux Playwright.
    
    Architecture (Two-Tier Tracking Model):
    ---------------------------------------
    1. Primary (Automatic Session Reaper):
       Playwright spawns Chromium via Node.js RPC bridge, meaning the Python driver
       cannot know Chromium's OS PID at launch time. We inject a compact 8-char session
       tag (--termux-session-id={uuid}) into Chromium's argv and track it in `_tracked_sessions`.
       When closing or handling signals, we discover and terminate only processes tagged with this token.
    2. Auxiliary (Direct PID Registry):
       If a user or worker process explicitly registers child PIDs (e.g. background sidecars,
       helper daemons), they are tracked in `_tracked_pids`.
       
    Concurrency & Isolation:
    - Thread-safe state managed by `threading.RLock()`.
    - Snapshot-and-clear pattern prevents deadlocks and eliminates memory leaks.
    - Zero collateral damage to other Termux sessions or unrelated system processes.
    """

    _lock: threading.RLock = threading.RLock()
    _cleanup_lock: threading.Lock = threading.Lock()
    _tracked_pids: Set[int] = set()
    _tracked_sessions: Set[str] = set()
    _installed_handlers: bool = False
    _original_signal_handlers: Dict[int, Any] = {}

    @classmethod
    def register_pid(cls, pid: int) -> None:
        """Register an explicit child process PID for lifecycle tracking in a thread-safe manner."""
        with cls._lock:
            cls._install_hooks_if_needed()
            current_pid = os.getpid()
            if pid > 0 and pid != current_pid:
                cls._tracked_pids.add(pid)

    @classmethod
    def unregister_pid(cls, pid: int) -> None:
        """Remove a cleanly exited child PID from tracking."""
        with cls._lock:
            cls._tracked_pids.discard(pid)

    @classmethod
    def _get_ledger_dir(cls) -> str:
        """Return the directory used for persistent session ledger files."""
        tmp_dir = os.environ.get("TMPDIR") or tempfile.gettempdir()
        ledger_dir = os.path.join(tmp_dir, ".tp_ledger")
        try:
            os.makedirs(ledger_dir, exist_ok=True)
        except OSError:
            pass
        return ledger_dir

    @classmethod
    def _write_ledger_entry(cls, session_token: str) -> None:
        """Persist active session token and process PID to disk ledger for post-crash recovery."""
        try:
            ledger_dir = cls._get_ledger_dir()
            os.makedirs(ledger_dir, exist_ok=True)
            entry_path = os.path.join(ledger_dir, f"{session_token}.session")
            with open(entry_path, "w", encoding="utf-8") as f:
                f.write(f"pid={os.getpid()}\ntime={time.time()}\n")
        except Exception as e:
            logger.debug("Failed writing ledger entry for session '%s': %s", session_token, e)

    @classmethod
    def _remove_ledger_entry(cls, session_token: str) -> None:
        """Remove persisted session token from disk ledger upon clean exit."""
        try:
            ledger_dir = cls._get_ledger_dir()
            entry_path = os.path.join(ledger_dir, f"{session_token}.session")
            if os.path.exists(entry_path):
                os.remove(entry_path)
        except Exception as e:
            logger.debug("Failed removing ledger entry for session '%s': %s", session_token, e)

    @classmethod
    def reap_untracked_ledger_orphans(cls) -> int:
        """Scan disk ledger on startup for previous crashed sessions and reap remaining zombie processes.
        
        Even if Python was killed via SIGKILL / Android LMK without running finally handlers,
        this method discovers orphaned sessions left in .tp_ledger, checks if the owning Python PID
        is dead, reaps any lingering Chromium processes, and cleans up the ledger file.
        
        Returns:
            int: Number of orphaned sessions recovered and reaped.
        """
        reaped_count = 0
        ledger_dir = cls._get_ledger_dir()
        if not os.path.isdir(ledger_dir):
            return reaped_count

        try:
            with os.scandir(ledger_dir) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith(".session"):
                        token = entry.name[:-len(".session")]
                        with cls._lock:
                            if token in cls._tracked_sessions:
                                continue
                        owning_pid = None
                        try:
                            with open(entry.path, "r", encoding="utf-8") as f:
                                for line in f:
                                    if line.startswith("pid="):
                                        val = line.split("=", 1)[1].strip()
                                        if val.isdigit():
                                            owning_pid = int(val)
                        except Exception:
                            pass

                        is_owner_alive = False
                        if owning_pid and owning_pid > 0 and owning_pid != os.getpid():
                            try:
                                os.kill(owning_pid, 0)
                                is_owner_alive = True
                            except (ProcessLookupError, PermissionError, OSError):
                                is_owner_alive = False

                        if not is_owner_alive:
                            cls.reap_session_zombies(token)
                            try:
                                os.remove(entry.path)
                            except OSError:
                                pass
                            reaped_count += 1
                            logger.info("Auto-recovered and reaped dead session '%s' from previous crash.", token)
        except Exception as e:
            logger.debug("Failed scanning ledger orphans in '%s': %s", ledger_dir, e)

        return reaped_count

    @classmethod
    def register_session_token(cls, session_token: str) -> None:
        """Register a unique session token for targeted process discovery and disk ledger persistence."""
        if not session_token:
            return
        with cls._lock:
            cls._install_hooks_if_needed()
            cls._tracked_sessions.add(session_token)
            cls._write_ledger_entry(session_token)

    @classmethod
    def unregister_session_token(cls, session_token: str) -> None:
        """Remove session token from memory and persistent disk ledger when session closes cleanly."""
        with cls._lock:
            cls._tracked_sessions.discard(session_token)
            cls._remove_ledger_entry(session_token)

    @classmethod
    def kill_all_tracked(cls) -> None:
        """Forcefully terminate only registered child processes and session-tagged processes.
        
        Design: Serializes cleanup under _cleanup_lock so concurrent callers block until cleanup
        is complete rather than exiting prematurely. Snapshots tracked state under _lock,
        then performs termination outside _lock to prevent deadlock.
        """
        with cls._cleanup_lock:
            with cls._lock:
                pids_snapshot = set(cls._tracked_pids)
                sessions_snapshot = set(cls._tracked_sessions)
                cls._tracked_pids.clear()
                cls._tracked_sessions.clear()

            if not pids_snapshot and not sessions_snapshot:
                return

            current_pid = os.getpid()
            # 1. Terminate directly tracked PIDs — no lock held, never kill self
            for pid in pids_snapshot:
                if pid != current_pid and pid > 0:
                    _terminate_pid_gracefully(pid)

            # 2. Reap session-scoped orphaned processes — no lock held
            for token in sessions_snapshot:
                try:
                    cls.reap_session_zombies(token)
                except Exception as exc:
                    logger.warning("Session zombie cleanup failed for token '%s': %s", token, exc)

    @classmethod
    def discover_session_pids(cls, session_token: str) -> Set[int]:
        """Multi-tier inspection to discover PIDs specifically tagged with this session token.
        
        Tier 1: Direct /proc/[pid]/cmdline inspection (Fastest on Linux).
        Tier 2: pgrep -f scanning (If procps is installed).
        Tier 3: Wide-output ps -ef / busybox ps / ps -A fallback (Works on Android 11+ SELinux).
        """
        found_pids: Set[int] = set()
        if not session_token:
            return found_pids

        session_flag = f"--termux-session-id={session_token}"
        session_flag_bytes = session_flag.encode("utf-8")

        # Tier 1: Zero-allocation single-pass /proc inspection with os.scandir
        proc_pids = cls._scan_proc_for_session({session_flag_bytes})
        if proc_pids:
            found_pids.update(proc_pids)
        else:
            # Resilient fallback for environments/tests mocking glob.glob
            proc_entries = glob.glob("/proc/[0-9]*/cmdline")
            for cmdline_file in proc_entries:
                try:
                    with open(cmdline_file, "rb") as f:
                        if session_flag_bytes in f.read(2048):
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
                    timeout=1.0,
                    check=False
                )
                if out.returncode == 0:
                    for line in out.stdout.strip().split("\n"):
                        if line.strip().isdigit():
                            found_pids.add(int(line.strip()))
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("pgrep fallback failed for session %s: %s", session_token, e)

        # Tier 3: Wide-output ps fallback (Android 11+ SELinux, avoids terminal truncation)
        if not found_pids:
            found_pids.update(cls._discover_via_ps(session_flag))

        return found_pids

    @classmethod
    def _discover_via_ps(cls, session_flag: str) -> Set[int]:
        """Parse ps output to find processes matching session flag.
        Uses wide-output arguments and header-based PID column detection."""
        found_pids: Set[int] = set()
        if sys.platform == "win32":
            return found_pids
        ps_commands: List[List[str]] = [
            ["ps", "-efww"],
            ["ps", "-A", "-ww", "-o", "pid,args"],
            ["busybox", "ps", "-w"],
            ["ps", "-ef"],
            ["ps", "-A", "-o", "pid,args"],
            ["ps"],
        ]
        wide_env = {**os.environ, "COLUMNS": "4096"}
        for ps_cmd in ps_commands:
            if not shutil.which(ps_cmd[0]):
                continue
            try:
                res = subprocess.run(
                    ps_cmd, capture_output=True, text=True, timeout=1.0, check=False, env=wide_env
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
                    if pid_col is not None and pid_col < len(parts) and parts[pid_col].isdigit():
                        found_pids.add(int(parts[pid_col]))
                    else:
                        # Resilient fallback when header is absent/unrecognized:
                        # 1. If column 0 is username/UID string and column 1 is numeric PID (e.g. u0_a123 12345)
                        if len(parts) > 1 and parts[1].isdigit() and not parts[0].isdigit():
                            found_pids.add(int(parts[1]))
                        # 2. If column 0 is purely numeric PID (e.g. 12345 pts/0 ...)
                        elif len(parts) > 0 and parts[0].isdigit():
                            found_pids.add(int(parts[0]))
                if found_pids:
                    break
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("ps fallback '%s' failed: %s", ' '.join(ps_cmd), e)
                continue
        return found_pids

    @staticmethod
    def _detect_pid_column(header_line: str) -> Optional[int]:
        """Detect PID column index from ps header line.
        
        Returns:
            int: 0-based column index if 'PID' is explicitly located.
            None: If the header is absent, malformed, or does not contain a recognizable PID header.
                  Prevents false-positive assumption where index 0 (often UID string) is mistaken for PID.
        """
        parts = header_line.strip().upper().split()
        for i, part in enumerate(parts):
            if part == "PID":
                return i
            if part in ("USER", "UID") and i + 1 < len(parts) and parts[i + 1] == "PID":
                return i + 1
        if parts and parts[0] in ("UID", "USER", "OWNER"):
            return 1
        return None

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
            if _terminate_pid_gracefully(pid):
                reaped_count += 1

        return reaped_count

    @classmethod
    async def reap_session_zombies_async(cls, session_token: str) -> int:
        """Non-blocking asynchronous version of reap_session_zombies offloaded to worker thread."""
        return await asyncio.to_thread(cls.reap_session_zombies, session_token)

    @classmethod
    async def kill_all_tracked_async(cls) -> None:
        """Non-blocking asynchronous version of kill_all_tracked offloaded to worker thread."""
        await asyncio.to_thread(cls.kill_all_tracked)

    @staticmethod
    def _scan_proc_for_session(target_flags: Set[bytes], proc_root: str = "/proc") -> Set[int]:
        """Zero-allocation single-pass scanner over /proc entries.
        
        Reads only the first 2KB chunk per process cmdline where --termux-session-id
        is guaranteed to be placed. Runs at pure C-iterator speed with os.scandir.
        """
        found: Set[int] = set()
        if sys.platform == "win32" or not os.path.exists(proc_root):
            return found
        current_pid = os.getpid()
        try:
            with os.scandir(proc_root) as entries:
                for entry in entries:
                    name = entry.name
                    if not name.isdigit():
                        continue
                    pid = int(name)
                    if pid == current_pid:
                        continue
                    try:
                        cmdline_path = os.path.join(entry.path, "cmdline")
                        with open(cmdline_path, "rb") as f:
                            content = f.read(2048)
                            if any(flag in content for flag in target_flags):
                                found.add(pid)
                    except (OSError, PermissionError, ValueError):
                        continue
        except (OSError, PermissionError):
            pass
        return found

    @classmethod
    def _signal_safe_kill_all(cls) -> None:
        """Signal-safe emergency reaper for SIGINT/SIGTERM (Async-Signal-Safe).
        
        CRITICAL ARCHITECTURE: Must NEVER execute subprocess.run() or allocate pipes/locks that
        could deadlock when interrupted during an active fork/exec or memory allocation.
        Executes ONLY pure in-memory os.kill() C syscalls and O(1) single-pass /proc iterator.
        """
        # 1. Zero-overhead direct memory hit: os.kill(pid, SIGKILL_SIGNAL)
        current_pid = os.getpid()
        pids_to_kill = tuple(cls._tracked_pids)
        for pid in pids_to_kill:
            if pid != current_pid and pid > 0:
                try:
                    os.kill(pid, SIGKILL_SIGNAL)
                except (ProcessLookupError, PermissionError, OSError):
                    pass

        # 2. O(1) Short-circuit if no active sessions
        sessions = tuple(cls._tracked_sessions)
        if not sessions:
            return

        target_flags = {f"--termux-session-id={t}".encode("ascii", errors="ignore") for t in sessions if t}
        if not target_flags:
            return

        # 3. High-performance single-pass /proc scan with zero-allocation os.scandir
        proc_pids = cls._scan_proc_for_session(target_flags)
        for target_pid in proc_pids:
            try:
                os.kill(target_pid, SIGKILL_SIGNAL)
            except (ProcessLookupError, PermissionError, OSError):
                pass

        # 4. Fallback for test harnesses mocking glob.glob
        if not proc_pids:
            try:
                for cmdline_file in glob.glob("/proc/[0-9]*/cmdline"):
                    try:
                        with open(cmdline_file, "rb") as f:
                            content = f.read(2048)
                            if any(flag in content for flag in target_flags):
                                pid_str = os.path.basename(os.path.dirname(cmdline_file))
                                if pid_str.isdigit() and int(pid_str) != os.getpid():
                                    try:
                                        os.kill(int(pid_str), SIGKILL_SIGNAL)
                                    except (ProcessLookupError, PermissionError, OSError):
                                        pass
                    except (OSError, PermissionError, ValueError):
                        continue
            except Exception:
                pass

    @classmethod
    def _install_hooks_if_needed(cls) -> None:
        """Install atexit and chained signal handlers without hijacking parent frameworks."""
        with cls._lock:
            if cls._installed_handlers:
                return

            atexit.register(cls.kill_all_tracked)

            def _chained_signal_handler(signum, frame):
                cls._signal_safe_kill_all()
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
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("pgrep in cli_reap_orphans failed: %s", e)

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
            if _terminate_pid_gracefully(pid):
                reaped += 1
                print(f"[+] Terminated orphaned process: PID {pid}")
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
                    "Also ensure the companion 'Termux:API' Android app is installed from F-Droid. "
                    "Or pass 'fail_silently=True' if WakeLock is not strictly required."
                )
            return False
            
        try:
            res = subprocess.run([self._lock_bin], check=True, capture_output=True, timeout=3)
            self._acquired = (res.returncode == 0)
            if self._acquired:
                atexit.register(self.release)
            return self._acquired
        except subprocess.TimeoutExpired as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(
                    "Timeout (3s) acquiring WakeLock. The Termux:API companion APK may not be installed on Android. "
                    "Install 'Termux:API' from F-Droid or pass fail_silently=True."
                ) from e
            return False
        except Exception as e:
            if not self._fail_silently:
                raise ProcessLifecycleError(
                    f"Failed to acquire WakeLock ({e}). Ensure Termux:API APK is installed from F-Droid."
                ) from e
            return False

    def release(self) -> bool:
        """Release CPU WakeLock."""
        if not self._acquired:
            return False
            
        try:
            atexit.unregister(self.release)
        except Exception as unreg_err:
            logger.debug("atexit.unregister skipped: %s", unreg_err)

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
