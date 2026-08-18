import pytest
from termux_playwright.browser import (
    build_chromium_args,
    configure_environment,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
    JITLESS_CHROMIUM_ARGS,
)
from termux_playwright.exceptions import BinaryNotFoundError

def test_build_chromium_args_default():
    args = build_chromium_args()
    for core_arg in CORE_ANDROID_CHROMIUM_ARGS:
        assert core_arg in args
    assert "--disable-dev-shm-usage" in args
    assert "--disk-cache-dir=/dev/null" in args
    assert "--no-sandbox" in args
    # SSL certificate validation must be enabled by default (security)
    assert "--ignore-certificate-errors" not in args

def test_build_chromium_args_low_memory():
    args = build_chromium_args(low_memory_mode=True)
    for low_arg in LOW_MEMORY_CHROMIUM_ARGS:
        assert low_arg in args

def test_build_chromium_args_jitless():
    args = build_chromium_args(jitless=True)
    for jit_arg in JITLESS_CHROMIUM_ARGS:
        assert jit_arg in args

def test_build_chromium_args_with_session_and_custom():
    custom = ["--window-size=1920,1080"]
    args = build_chromium_args(custom, session_token="test_sess_123")
    assert "--termux-session-id=test_sess_123" in args
    assert "--window-size=1920,1080" in args

def test_build_chromium_args_ignore_cert_errors_opt_in():
    """--ignore-certificate-errors must only appear when explicitly requested."""
    args_default = build_chromium_args()
    assert "--ignore-certificate-errors" not in args_default
    
    args_enabled = build_chromium_args(ignore_certificate_errors=True)
    assert "--ignore-certificate-errors" in args_enabled

def test_configure_environment_sets_node_memory_and_checks_strict(monkeypatch):
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr("termux_playwright.browser.find_node_binary", lambda: "/mock/node")
    monkeypatch.delenv("NODE_OPTIONS", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM_PATH", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_NODEJS_PATH", raising=False)
    
    cfg = configure_environment(strict=True)
    assert "--max-old-space-size=256" in cfg["NODE_OPTIONS"]

@pytest.mark.asyncio
async def test_launch_async_success(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    mock_browser = MagicMock()
    disconnect_callbacks = []
    mock_browser.on = lambda event, cb: disconnect_callbacks.append(cb) if event == "disconnected" else None

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    browser = await launch(mock_playwright, headless=True, ignore_certificate_errors=True)
    assert browser == mock_browser

    # Verify launch parameters
    mock_playwright.chromium.launch.assert_called_once()
    _, kwargs = mock_playwright.chromium.launch.call_args
    assert kwargs["headless"] is True
    assert kwargs["executable_path"] == "/mock/chromium"
    assert "--no-sandbox" in kwargs["args"]
    assert "--ignore-certificate-errors" in kwargs["args"]

    # Verify session tracking
    session_arg = [a for a in kwargs["args"] if a.startswith("--termux-session-id=")][0]
    token = session_arg.split("=")[1]
    assert token in ProcessReaper._tracked_sessions

    # Trigger disconnection
    for cb in disconnect_callbacks:
        cb()
    assert token not in ProcessReaper._tracked_sessions

@pytest.mark.asyncio
async def test_launch_async_failure_triggers_cleanup(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    reaped_sessions = []
    async def mock_reap_async(token):
        reaped_sessions.append(token)
        return 1
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies_async", mock_reap_async)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(side_effect=RuntimeError("Simulated Launch Crash"))

    with pytest.raises(RuntimeError) as exc_info:
        await launch(mock_playwright)
    assert "Simulated Launch Crash" in str(exc_info.value)
    assert len(reaped_sessions) == 1
    # Verify token is unregistered
    assert reaped_sessions[0] not in ProcessReaper._tracked_sessions

def test_launch_sync_success_and_disconnect(monkeypatch):
    from unittest.mock import MagicMock
    from termux_playwright.browser import launch_sync
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    mock_browser = MagicMock()
    disconnect_callbacks = []
    mock_browser.on = lambda event, cb: disconnect_callbacks.append(cb) if event == "disconnected" else None

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = MagicMock(return_value=mock_browser)

    browser = launch_sync(mock_playwright, low_memory_mode=True)
    assert browser == mock_browser

    _, kwargs = mock_playwright.chromium.launch.call_args
    assert "--renderer-process-limit=1" in kwargs["args"]
    assert "--js-flags=--max-old-space-size=128" in kwargs["args"]

    session_arg = [a for a in kwargs["args"] if a.startswith("--termux-session-id=")][0]
    token = session_arg.split("=")[1]
    assert token in ProcessReaper._tracked_sessions

    for cb in disconnect_callbacks:
        cb()
    assert token not in ProcessReaper._tracked_sessions

def test_launch_sync_failure_cleans_up(monkeypatch):
    from unittest.mock import MagicMock
    from termux_playwright.browser import launch_sync
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    reaped_sessions = []
    def mock_reap(token):
        reaped_sessions.append(token)
        return 1
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", mock_reap)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = MagicMock(side_effect=RuntimeError("Sync Launch Failed"))

    with pytest.raises(RuntimeError):
        launch_sync(mock_playwright)
    assert len(reaped_sessions) == 1
    assert reaped_sessions[0] not in ProcessReaper._tracked_sessions

