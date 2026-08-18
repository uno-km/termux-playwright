import pytest
from termux_playwright.reaper import ProcessReaper, TermuxWakeLock
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
