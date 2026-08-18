import os
import signal
import pytest
from termux_playwright.reaper import ProcessReaper, TermuxWakeLock, SIGKILL_SIGNAL
from termux_playwright.exceptions import ProcessLifecycleError

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

def test_termux_wake_lock_graceful_when_explicit(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    lock = TermuxWakeLock(fail_silently=True)
    assert lock.acquire() is False
    assert lock.release() is False

def test_kill_all_tracked_snapshots_and_terminates(monkeypatch):
    killed_pids = []
    reaped_sessions = []

    monkeypatch.setattr("os.kill", lambda pid, sig: killed_pids.append((pid, sig)))
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", lambda token: reaped_sessions.append(token))

    ProcessReaper.register_pid(101)
    ProcessReaper.register_pid(102)
    ProcessReaper.register_session_token("tok_a")
    ProcessReaper.register_session_token("tok_b")

    ProcessReaper.kill_all_tracked()

    # Sets must be cleared immediately
    assert len(ProcessReaper._tracked_pids) == 0
    assert len(ProcessReaper._tracked_sessions) == 0

    assert (101, SIGKILL_SIGNAL) in killed_pids
    assert (102, SIGKILL_SIGNAL) in killed_pids
    assert "tok_a" in reaped_sessions
    assert "tok_b" in reaped_sessions

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

def test_cli_reap_orphans_runs(monkeypatch, tmp_path, capsys):
    from termux_playwright.reaper import cli_reap_orphans

    fake_proc_dir = tmp_path / "proc" / "9988"
    fake_proc_dir.mkdir(parents=True)
    cmdline = fake_proc_dir / "cmdline"
    cmdline.write_bytes(b"chromium\x00--termux-session-id=orphan_token_1\x00")

    monkeypatch.setattr("glob.glob", lambda pattern: [str(cmdline)])
    killed = []
    monkeypatch.setattr("os.kill", lambda pid, sig: killed.append((pid, sig)))

    cli_reap_orphans()
    captured = capsys.readouterr()
    assert "Killed orphaned process: PID 9988" in captured.out
    assert (9988, SIGKILL_SIGNAL) in killed


