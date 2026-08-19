import os
import signal
import pytest
from termux_playwright.reaper import (
    ProcessReaper,
    TermuxWakeLock,
    SIGKILL_SIGNAL,
    SIGTERM_SIGNAL,
    _terminate_pid_gracefully,
)
from termux_playwright.exceptions import ProcessLifecycleError

@pytest.fixture(autouse=True)
def reset_reaper_state(monkeypatch):
    ProcessReaper._tracked_pids.clear()
    ProcessReaper._tracked_sessions.clear()
    monkeypatch.setattr(ProcessReaper, "_install_hooks_if_needed", lambda: None)
    yield
    ProcessReaper._tracked_pids.clear()
    ProcessReaper._tracked_sessions.clear()

def test_process_reaper_session_and_pid_lifecycle():
    token = "session_alpha_1"
    ProcessReaper.register_session_token(token)
    assert token in ProcessReaper._tracked_sessions
    ProcessReaper.unregister_session_token(token)
    assert token not in ProcessReaper._tracked_sessions

    pid = 9999999
    ProcessReaper.register_pid(pid)
    assert pid in ProcessReaper._tracked_pids
    ProcessReaper.unregister_pid(pid)
    assert pid not in ProcessReaper._tracked_pids

def test_process_reaper_discover_session_pids_empty():
    pids = ProcessReaper.discover_session_pids("non_existent_token_xyz")
    assert isinstance(pids, set)
    assert len(pids) == 0

def test_termux_wake_lock_strict_raises(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    lock = TermuxWakeLock(fail_silently=False)
    with pytest.raises(ProcessLifecycleError) as exc_info:
        lock.acquire()
    assert "termux-wake-lock binary not found" in str(exc_info.value)

def test_termux_wake_lock_timeout_raises(monkeypatch):
    import subprocess
    monkeypatch.setattr("shutil.which", lambda _: "/mock/termux-wake-lock")
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="termux-wake-lock", timeout=3)
    monkeypatch.setattr("subprocess.run", mock_run)

    lock = TermuxWakeLock(fail_silently=False)
    with pytest.raises(ProcessLifecycleError) as exc_info:
        lock.acquire()
    assert "Timeout (3s)" in str(exc_info.value)
    assert "Termux:API" in str(exc_info.value)

def test_termux_wake_lock_graceful_when_explicit(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    lock = TermuxWakeLock(fail_silently=True)
    assert lock.acquire() is False
    assert lock.release() is False

def test_terminate_pid_gracefully_immediate_exit(monkeypatch):
    signals_sent = []
    def mock_kill(pid, sig):
        signals_sent.append((pid, sig))
        if sig == 0:
            raise ProcessLookupError() # Process exited cleanly after SIGTERM

    monkeypatch.setattr("os.kill", mock_kill)
    monkeypatch.setattr("os.waitpid", lambda pid, flags: (0, 0))
    assert _terminate_pid_gracefully(1234, graceful_timeout=0.05) is True
    assert (1234, SIGTERM_SIGNAL) in signals_sent
    assert (1234, SIGKILL_SIGNAL) not in signals_sent

def test_terminate_pid_gracefully_waitpid_reaps_child(monkeypatch):
    """Direct child process is reaped immediately via waitpid without spinning sleep loop on POSIX."""
    signals_sent = []
    def mock_kill(pid, sig):
        signals_sent.append((pid, sig))

    monkeypatch.setattr("termux_playwright.reaper.HAS_POSIX_WAITPID", True)
    monkeypatch.setattr("os.kill", mock_kill)
    # waitpid returns (pid, status) immediately for direct child
    monkeypatch.setattr("os.waitpid", lambda pid, flags: (pid, 0))
    
    assert _terminate_pid_gracefully(3344, graceful_timeout=0.1) is True
    assert (3344, SIGTERM_SIGNAL) in signals_sent
    assert (3344, SIGKILL_SIGNAL) not in signals_sent

def test_terminate_pid_gracefully_grandchild_process(monkeypatch):
    """Grandchild process (where waitpid raises ChildProcessError) is reaped via bounded kill polling."""
    signals_sent = []
    def mock_kill(pid, sig):
        signals_sent.append((pid, sig))
        if sig == 0:
            raise ProcessLookupError()  # Grandchild exited after SIGTERM

    def mock_waitpid(pid, flags):
        raise ChildProcessError(10, "No child processes")  # Grandchild is not direct child

    monkeypatch.setattr("os.kill", mock_kill)
    monkeypatch.setattr("os.waitpid", mock_waitpid)
    
    assert _terminate_pid_gracefully(9988, graceful_timeout=0.05) is True
    assert (9988, SIGTERM_SIGNAL) in signals_sent
    assert (9988, SIGKILL_SIGNAL) not in signals_sent

def test_terminate_pid_gracefully_lingering_process(monkeypatch):
    signals_sent = []
    def mock_kill(pid, sig):
        signals_sent.append((pid, sig))
        # Never raises ProcessLookupError, simulating lingering process

    def mock_waitpid(pid, flags):
        raise ChildProcessError(10, "No child processes")

    monkeypatch.setattr("os.kill", mock_kill)
    monkeypatch.setattr("os.waitpid", mock_waitpid)
    assert _terminate_pid_gracefully(5678, graceful_timeout=0.04) is True
    assert (5678, SIGTERM_SIGNAL) in signals_sent
    assert (5678, SIGKILL_SIGNAL) in signals_sent

def test_kill_all_tracked_snapshots_and_terminates(monkeypatch):
    killed_pids = []
    reaped_sessions = []

    def mock_kill(pid, sig):
        killed_pids.append((pid, sig))
        if sig == 0:
            raise ProcessLookupError()

    def mock_reap(*args):
        for arg in args:
            if isinstance(arg, str):
                reaped_sessions.append(arg)
        return 1

    monkeypatch.setattr("os.kill", mock_kill)
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", mock_reap)

    ProcessReaper.register_pid(101)
    ProcessReaper.register_pid(102)
    ProcessReaper.register_session_token("tok_a")
    ProcessReaper.register_session_token("tok_b")

    ProcessReaper.kill_all_tracked()

    # Sets must be cleared immediately
    assert len(ProcessReaper._tracked_pids) == 0
    assert len(ProcessReaper._tracked_sessions) == 0

    assert (101, SIGTERM_SIGNAL) in killed_pids
    assert (102, SIGTERM_SIGNAL) in killed_pids
    assert "tok_a" in reaped_sessions
    assert "tok_b" in reaped_sessions

def test_kill_all_tracked_concurrent_serialization(monkeypatch):
    import threading
    import time
    
    execution_order = []
    def slow_reap(token):
        execution_order.append(f"start_{token}")
        time.sleep(0.05)
        execution_order.append(f"end_{token}")
        return 1

    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", slow_reap)

    ProcessReaper.register_session_token("tok_sync")
    t1 = threading.Thread(target=ProcessReaper.kill_all_tracked)
    t2 = threading.Thread(target=ProcessReaper.kill_all_tracked)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Verify both threads synchronized without race condition
    assert "start_tok_sync" in execution_order
    assert "end_tok_sync" in execution_order

def test_signal_safe_kill_all_executes_direct_kill(tmp_path, monkeypatch):
    """Ensure _signal_safe_kill_all only uses os.kill without invoking subprocess."""
    killed_pids = []
    def mock_kill(pid, sig):
        killed_pids.append((pid, sig))

    # If subprocess is called, fail the test
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: pytest.fail("subprocess.run must NOT be called in signal handler!"))
    monkeypatch.setattr("os.kill", mock_kill)

    fake_proc_dir = tmp_path / "proc" / "8888"
    fake_proc_dir.mkdir(parents=True)
    cmdline = fake_proc_dir / "cmdline"
    cmdline.write_bytes(b"chromium\x00--termux-session-id=sigsafe123\x00")
    monkeypatch.setattr("glob.glob", lambda pattern: [str(cmdline)])

    ProcessReaper._tracked_pids = {777}
    ProcessReaper._tracked_sessions = {"sigsafe123"}

    ProcessReaper._signal_safe_kill_all()

    assert (777, SIGKILL_SIGNAL) in killed_pids
    assert (8888, SIGKILL_SIGNAL) in killed_pids

def test_discover_session_pids_tier1_proc(tmp_path, monkeypatch):
    fake_proc_dir = tmp_path / "proc" / "54321"
    fake_proc_dir.mkdir(parents=True)
    cmdline = fake_proc_dir / "cmdline"
    cmdline.write_bytes(b"chromium\x00--termux-session-id=alpha_sess_99\x00--headless\x00")

    monkeypatch.setattr("glob.glob", lambda pattern: [str(cmdline)])
    
    pids = ProcessReaper.discover_session_pids("alpha_sess_99")
    assert pids == {54321}

def test_discover_session_pids_tier2_pgrep(monkeypatch):
    monkeypatch.setattr("glob.glob", lambda pattern: [])
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/pgrep" if cmd == "pgrep" else None)

    class FakeOut:
        returncode = 0
        stdout = "7771\n7772\n"
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: FakeOut())

    pids = ProcessReaper.discover_session_pids("target_session_token")
    assert pids == {7771, 7772}

def test_discover_session_pids_tier3_ps_header_detection():
    header1 = "  PID TTY          TIME CMD"
    assert ProcessReaper._detect_pid_column(header1) == 0

    header2 = "UID        PID  PPID  C STIME TTY          TIME CMD"
    assert ProcessReaper._detect_pid_column(header2) == 1

    header3 = "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"
    assert ProcessReaper._detect_pid_column(header3) == 1

    header4 = "CUSTOM_HEADER_WITHOUT_EXPLICIT_PID"
    assert ProcessReaper._detect_pid_column(header4) is None

def test_discover_session_pids_tier3_ps_execution(monkeypatch):
    monkeypatch.setattr("glob.glob", lambda pattern: [])
    monkeypatch.setattr("shutil.which", lambda cmd: "/system/bin/ps" if cmd == "ps" else None)
    monkeypatch.setattr("sys.platform", "linux")

    class FakeOut:
        returncode = 0
        stdout = "HEADER_WITHOUT_PID\nu0_a123 5544 1 0 12:00 ? 00:00:01 chromium --termux-session-id=ps_sess_test\n"

    monkeypatch.setattr("subprocess.run", lambda *a, **kw: FakeOut())
    pids = ProcessReaper._discover_via_ps("--termux-session-id=ps_sess_test")
    assert pids == {5544}

def test_cli_reap_orphans_runs(monkeypatch, tmp_path, capsys):
    from termux_playwright.reaper import cli_reap_orphans

    fake_proc_dir = tmp_path / "proc" / "9988"
    fake_proc_dir.mkdir(parents=True)
    cmdline = fake_proc_dir / "cmdline"
    cmdline.write_bytes(b"chromium\x00--termux-session-id=orphan_token_1\x00")

    monkeypatch.setattr("glob.glob", lambda pattern: [str(cmdline)])
    killed = []
    
    def mock_kill(pid, sig):
        killed.append((pid, sig))
        if sig == 0:
            raise ProcessLookupError()

    monkeypatch.setattr("os.kill", mock_kill)

    cli_reap_orphans()
    captured = capsys.readouterr()
    assert "Terminated orphaned process: PID 9988" in captured.out
    assert (9988, SIGTERM_SIGNAL) in killed

def test_process_reaper_disk_ledger_persistence_and_orphan_recovery(monkeypatch, tmp_path):
    monkeypatch.setattr(ProcessReaper, "_get_ledger_dir", lambda: str(tmp_path / "ledger"))
    
    # 1. Register session writes ledger entry
    token = "sess_crash_recovery_1"
    ProcessReaper.register_session_token(token)
    ledger_file = tmp_path / "ledger" / f"{token}.session"
    assert ledger_file.exists()
    assert f"pid={os.getpid()}" in ledger_file.read_text(encoding="utf-8")

    # 2. Clean unregister deletes ledger entry
    ProcessReaper.unregister_session_token(token)
    assert not ledger_file.exists()

    # 3. Simulate a previous hard crash (SIGKILL/LMK): dead PID entry left in ledger
    crashed_token = "crashed_session_999"
    crashed_file = tmp_path / "ledger" / f"{crashed_token}.session"
    crashed_file.write_text("pid=888888\ntime=1000.0\n", encoding="utf-8")

    reaped_sessions = []
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", lambda tok: reaped_sessions.append(tok) or 1)

    # reap_untracked_ledger_orphans discovers dead process and reaps it
    recovered_count = ProcessReaper.reap_untracked_ledger_orphans()
    assert recovered_count == 1
    assert reaped_sessions == [crashed_token]
    assert not crashed_file.exists()


