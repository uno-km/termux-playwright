import pytest
from termux_playwright.reaper import ProcessReaper, TermuxWakeLock

def test_process_reaper_pid_lifecycle():
    pid = 9999999
    ProcessReaper.register_pid(pid)
    assert pid in ProcessReaper._tracked_pids
    ProcessReaper.unregister_pid(pid)
    assert pid not in ProcessReaper._tracked_pids

def test_termux_wake_lock_graceful(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    lock = TermuxWakeLock(fail_silently=True)
    assert lock.acquire() is False
    assert lock.release() is False
