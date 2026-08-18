import pytest
from termux_playwright.browser import build_chromium_args, configure_environment, CORE_ANDROID_CHROMIUM_ARGS
from termux_playwright.exceptions import BinaryNotFoundError

def test_build_chromium_args_default():
    args = build_chromium_args()
    for core_arg in CORE_ANDROID_CHROMIUM_ARGS:
        assert core_arg in args
    assert "--disable-dev-shm-usage" in args
    assert "--disk-cache-dir=/dev/null" in args
    assert "--no-sandbox" in args

def test_build_chromium_args_with_session_and_custom():
    custom = ["--window-size=1920,1080"]
    args = build_chromium_args(custom, session_token="test_sess_123")
    assert "--termux-session-id=test_sess_123" in args
    assert "--window-size=1920,1080" in args

def test_configure_environment_strict_raises_on_missing(monkeypatch):
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: (_ for _ in ()).throw(BinaryNotFoundError("Missing Chrome")))
    
    with pytest.raises(BinaryNotFoundError):
        configure_environment(strict=True)
