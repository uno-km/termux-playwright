import pytest
from termux_playwright.browser import (
    build_chromium_args,
    configure_environment,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
)
from termux_playwright.exceptions import BinaryNotFoundError
from termux_playwright.reaper import ProcessReaper

@pytest.fixture(autouse=True)
def reset_reaper_state(monkeypatch):
    ProcessReaper._tracked_pids.clear()
    ProcessReaper._tracked_sessions.clear()
    ProcessReaper._cleaning_up = False
    monkeypatch.setattr(ProcessReaper, "_install_hooks_if_needed", lambda: None)
    yield
    ProcessReaper._tracked_pids.clear()
    ProcessReaper._tracked_sessions.clear()
    ProcessReaper._cleaning_up = False

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
    assert "--renderer-process-limit=1" in args
    js_flags = [a for a in args if a.startswith("--js-flags=")]
    assert len(js_flags) == 1
    assert "--max-old-space-size=128" in js_flags[0]

def test_build_chromium_args_jitless():
    args = build_chromium_args(jitless=True)
    js_flags = [a for a in args if a.startswith("--js-flags=")]
    assert len(js_flags) == 1
    assert "--jitless" in js_flags[0]

def test_build_chromium_args_v8_flags_unified_without_collision():
    """Ensure multiple V8 flags merge into a single canonical --js-flags argument."""
    custom_args = ["--js-flags=--expose-gc", "--window-size=1920,1080"]
    args = build_chromium_args(
        extra_args=custom_args,
        low_memory_mode=True,
        jitless=True,
    )
    # MUST contain exactly ONE --js-flags argument
    js_flags_args = [a for a in args if a.startswith("--js-flags=")]
    assert len(js_flags_args) == 1, f"Found multiple --js-flags: {js_flags_args}"

    single_v8_arg = js_flags_args[0]
    assert "--expose-gc" in single_v8_arg
    assert "--max-old-space-size=128" in single_v8_arg
    assert "--jitless" in single_v8_arg
    assert "--window-size=1920,1080" in args

def test_build_chromium_args_v8_flags_split_syntax_parsed():
    """Ensure ['--js-flags', '--expose-gc'] does not leak subflags into Chromium top-level args."""
    custom_args = ["--js-flags", "--expose-gc", "--window-size=1920,1080"]
    args = build_chromium_args(
        extra_args=custom_args,
        low_memory_mode=True,
    )
    assert "--expose-gc" not in args  # Must NOT be a top-level Chromium arg!
    assert "--js-flags" not in args   # Standalone --js-flags must be consumed!
    
    js_flags_args = [a for a in args if a.startswith("--js-flags=")]
    assert len(js_flags_args) == 1
    assert "--expose-gc" in js_flags_args[0]
    assert "--max-old-space-size=128" in js_flags_args[0]

def test_build_chromium_args_v8_flags_key_value_override():
    """Ensure user explicit --max-old-space-size=512 takes precedence without duplicate key collision."""
    custom_args = ["--js-flags=--max-old-space-size=512"]
    args = build_chromium_args(
        extra_args=custom_args,
        low_memory_mode=True,  # default is 128
    )
    js_flags_args = [a for a in args if a.startswith("--js-flags=")]
    assert len(js_flags_args) == 1
    assert "--max-old-space-size=512" in js_flags_args[0]
    assert "--max-old-space-size=128" not in js_flags_args[0]

def test_build_chromium_args_key_value_override_replaces_default():
    """Ensure user custom key-value arg overrides default with same prefix without duplicates."""
    custom = ["--disk-cache-dir=/custom/cache/dir", "--media-cache-size=50"]
    args = build_chromium_args(custom)
    assert "--disk-cache-dir=/custom/cache/dir" in args
    assert "--disk-cache-dir=/dev/null" not in args
    assert "--media-cache-size=50" in args
    assert "--media-cache-size=1" not in args

def test_build_chromium_args_with_session_and_custom():
    custom = ["--window-size=1920,1080"]
    args = build_chromium_args(custom, session_token="test_sess_123")
    # Must be at index 0 to guarantee immunity against Android Toybox ps 80-column line-truncation
    assert args[0] == "--termux-session-id=test_sess_123"
    assert "--window-size=1920,1080" in args

def test_build_chromium_args_standalone_mode():
    """Ensure standalone_mode injects anti-throttling flags for solo fortress execution."""
    args = build_chromium_args(standalone_mode=True)
    assert "--disable-background-timer-throttling" in args
    assert "--disable-backgrounding-occluded-windows" in args
    assert "--disable-renderer-backgrounding" in args
    assert "--disable-ipc-flooding-protection" in args

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
    assert "--max-old-space-size=512" in cfg["NODE_OPTIONS"]

def test_configure_environment_preserves_quoted_and_complex_node_options(monkeypatch):
    from termux_playwright.browser import configure_environment
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr("termux_playwright.browser.find_node_binary", lambda: "/mock/node")
    monkeypatch.setenv("NODE_OPTIONS", '--trace-warnings --require "/custom path/shim.js"')
    
    cfg = configure_environment(strict=True)
    assert "--max-old-space-size=512" in cfg["NODE_OPTIONS"]
    assert "--trace-warnings" in cfg["NODE_OPTIONS"]
    assert "/custom path/shim.js" in cfg["NODE_OPTIONS"]

@pytest.mark.asyncio
async def test_launch_async_success(monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    reaped_on_disconnect = []
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", lambda tok: reaped_on_disconnect.append(tok) or 1)

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
    assert len(token) == 8
    assert token in ProcessReaper._tracked_sessions

    for cb in disconnect_callbacks:
        cb()
    await asyncio.sleep(0.05)
    assert token in reaped_on_disconnect
    assert token not in ProcessReaper._tracked_sessions

def test_launch_disconnect_thread_reaps_even_without_loop(monkeypatch):
    """Verify that disconnect cleanup thread executes and completes even after the asyncio loop is closed."""
    import asyncio
    import time
    from unittest.mock import MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    reaped_on_disconnect = []
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", lambda tok: reaped_on_disconnect.append(tok) or 1)

    mock_browser = MagicMock()
    disconnect_callbacks = []
    mock_browser.on = lambda event, cb: disconnect_callbacks.append(cb) if event == "disconnected" else None

    mock_playwright = MagicMock()
    async def _mock_launch(**kwargs):
        return mock_browser
    mock_playwright.chromium.launch = _mock_launch

    browser = asyncio.run(launch(mock_playwright))
    assert browser == mock_browser

    session_token = list(ProcessReaper._tracked_sessions)[0]

    # Fire callback when the main asyncio event loop is already completely closed!
    for cb in disconnect_callbacks:
        cb()
    time.sleep(0.05)

    assert session_token in reaped_on_disconnect
    assert session_token not in ProcessReaper._tracked_sessions

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

@pytest.mark.asyncio
async def test_launch_unpatched_self_heal_failure_raises_patching_error(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.exceptions import PatchingError

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.is_core_bundle_patched", lambda: False)
    monkeypatch.setattr("termux_playwright.browser.apply_core_bundle_patch", lambda: False)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock()

    with pytest.raises(PatchingError) as exc_info:
        await launch(mock_playwright)
    assert "Playwright coreBundle.js is not patched" in str(exc_info.value)
    mock_playwright.chromium.launch.assert_not_called()

def test_launch_sync_success_and_disconnect(monkeypatch):
    from unittest.mock import MagicMock
    from termux_playwright.browser import launch_sync
    from termux_playwright.reaper import ProcessReaper

    reaped_on_disconnect = []
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies", lambda tok: reaped_on_disconnect.append(tok) or 1)

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
    assert len(token) == 8
    assert token in ProcessReaper._tracked_sessions

    for cb in disconnect_callbacks:
        cb()
    assert token in reaped_on_disconnect
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

def test_launch_wires_configure_environment_sets_node_options(monkeypatch):
    import os
    from unittest.mock import MagicMock
    from termux_playwright.browser import launch_sync

    monkeypatch.delenv("NODE_OPTIONS", raising=False)
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr("termux_playwright.browser.find_node_binary", lambda: "/mock/node")

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = MagicMock(return_value=MagicMock())

    launch_sync(mock_playwright)
    # Must ensure NODE_OPTIONS is populated with memory cap inside Termux
    assert "--max-old-space-size=512" in os.environ.get("NODE_OPTIONS", "")

def test_configure_environment_does_not_pollute_non_termux(monkeypatch):
    import os
    from termux_playwright.browser import configure_environment

    monkeypatch.delenv("NODE_OPTIONS", raising=False)
    res = configure_environment(strict=False)
    assert res == {}
    assert "NODE_OPTIONS" not in os.environ

def test_verify_runtime_dependencies_termux_missing_greenlet_raises(monkeypatch):
    import builtins
    from termux_playwright.browser import verify_runtime_dependencies

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "greenlet":
            raise ImportError("No module named greenlet")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    with pytest.raises(RuntimeError) as exc_info:
        verify_runtime_dependencies()
    assert "termux-playwright-install" in str(exc_info.value)

def test_verify_runtime_dependencies_venv_guidance(monkeypatch, tmp_path):
    import builtins
    import sys
    from termux_playwright.browser import verify_runtime_dependencies

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "fake_venv"))
    monkeypatch.setattr(sys, "base_prefix", "/usr")

    real_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if name == "greenlet":
            raise ImportError("No module named greenlet")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    with pytest.raises(RuntimeError) as exc_info:
        verify_runtime_dependencies()
    assert "--system-site-packages" in str(exc_info.value)

def test_verify_runtime_dependencies_non_termux_noop(monkeypatch):
    import os
    from termux_playwright.browser import verify_runtime_dependencies
    monkeypatch.delenv("NODE_OPTIONS", raising=False)
    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: False)
    # Should not raise even if greenlet is not checked
    verify_runtime_dependencies()
    assert "NODE_OPTIONS" not in os.environ

@pytest.mark.asyncio
async def test_block_heavy_resources_async():
    from termux_playwright.browser import block_heavy_resources
    
    routed_patterns = []
    class MockPage:
        async def route(self, pattern, handler):
            routed_patterns.append(pattern)

    page = MockPage()
    await block_heavy_resources(page, images=True, media=True, fonts=True, custom_patterns=["**/*.analytics.js"])
    assert len(routed_patterns) == 2
    assert "png" in routed_patterns[0]
    assert "mp4" in routed_patterns[0]
    assert "woff2" in routed_patterns[0]
    assert routed_patterns[1] == "**/*.analytics.js"

def test_block_heavy_resources_sync():
    from termux_playwright.browser import block_heavy_resources_sync
    
    routed_patterns = []
    class MockPage:
        def route(self, pattern, handler):
            routed_patterns.append(pattern)

    page = MockPage()
    block_heavy_resources_sync(page, images=True, media=False, fonts=False)
    assert len(routed_patterns) == 1
    assert "png" in routed_patterns[0]
    assert "mp4" not in routed_patterns[0]

@pytest.mark.asyncio
async def test_launch_async_standalone_mode_and_wake_lock(monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.reaper import ProcessReaper, TermuxWakeLock

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr(ProcessReaper, "reap_session_zombies_async", AsyncMock(return_value=1))

    wake_locks_acquired = []
    wake_locks_released = []
    monkeypatch.setattr(TermuxWakeLock, "acquire", lambda self: wake_locks_acquired.append(True) or True)
    monkeypatch.setattr(TermuxWakeLock, "release", lambda self: wake_locks_released.append(True) or True)

    mock_browser = MagicMock()
    disconnect_callbacks = []
    mock_browser.on = lambda event, cb: disconnect_callbacks.append(cb) if event == "disconnected" else None

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    browser = await launch(mock_playwright, standalone_mode=True, wake_lock=True)
    assert browser == mock_browser
    assert len(wake_locks_acquired) == 1

    _, kwargs = mock_playwright.chromium.launch.call_args
    # Check standalone flags
    assert "--disable-background-timer-throttling" in kwargs["args"]
    # Check ephemeral profile dir injected
    user_data_args = [a for a in kwargs["args"] if a.startswith("--user-data-dir=")]
    assert len(user_data_args) == 1
    ephemeral_dir = user_data_args[0].split("=")[1]
    assert "tp_solo_" in ephemeral_dir

    # Trigger disconnect
    for cb in disconnect_callbacks:
        cb()
    await asyncio.sleep(0.05)
    assert len(wake_locks_released) == 1

def test_purge_stale_ephemeral_profiles(tmp_path, monkeypatch):
    import os
    import time
    from termux_playwright.browser import _purge_stale_ephemeral_profiles
    from termux_playwright.reaper import ProcessReaper

    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    # 1. Stale profile (older than 60s)
    stale_dir = tmp_path / "tp_solo_stale123"
    stale_dir.mkdir()
    (stale_dir / "profile.lock").write_text("lock")
    old_time = time.time() - 120.0
    os.utime(str(stale_dir), (old_time, old_time))

    # 2. Fresh profile (created 5s ago by another active worker)
    fresh_dir = tmp_path / "tp_solo_fresh456"
    fresh_dir.mkdir()
    (fresh_dir / "profile.lock").write_text("lock")

    # 3. Crash profile (created 3s ago by a dead process)
    crash_dir = tmp_path / "tp_solo_crash999"
    crash_dir.mkdir()

    # 4. Active profile in current process
    active_dir = tmp_path / "tp_solo_active789"
    active_dir.mkdir()
    os.utime(str(active_dir), (old_time, old_time))
    monkeypatch.setattr(ProcessReaper, "_tracked_sessions", {"active789"})

    # 5. Irrelevant folder
    other_dir = tmp_path / "other_app_folder"
    other_dir.mkdir()

    # Mock discover_session_pids: only fresh456 has an alive PID
    monkeypatch.setattr(
        ProcessReaper,
        "discover_session_pids",
        lambda token: {9999} if token == "fresh456" else set()
    )

    purged = _purge_stale_ephemeral_profiles(max_age_seconds=60.0)
    assert purged == 2
    assert not stale_dir.exists()
    assert not crash_dir.exists()
    assert fresh_dir.exists()
    assert active_dir.exists()
    assert other_dir.exists()

def test_build_chromium_args_stealth_and_single_process():
    from termux_playwright.browser import build_chromium_args
    args = build_chromium_args(stealth=True, single_process=True)
    assert "--disable-blink-features=AutomationControlled" in args
    assert "--disable-features=IsolateOrigins,site-per-process" in args
    assert "--disable-infobars" in args
    assert "--single-process" in args

@pytest.mark.asyncio
async def test_setup_stealth_context_async():
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import setup_stealth_context

    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_context.set_extra_http_headers = AsyncMock()
    mock_context.add_cookies = AsyncMock()
    mock_context.add_init_script = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    custom_cookies = [{"name": "sid", "value": "xyz123", "domain": "example.com", "path": "/"}]
    ctx = await setup_stealth_context(
        mock_browser,
        extra_headers={"X-Custom-Auth": "secret123"},
        cookies=custom_cookies,
    )
    assert ctx == mock_context
    assert mock_browser.new_context.called
    assert mock_context.add_cookies.called
    assert mock_context.add_init_script.called

def test_setup_stealth_context_sync():
    from unittest.mock import MagicMock
    from termux_playwright.browser import setup_stealth_context_sync

    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_context.set_extra_http_headers = MagicMock()
    mock_context.add_cookies = MagicMock()
    mock_context.add_init_script = MagicMock()
    mock_browser.new_context = MagicMock(return_value=mock_context)

    custom_cookies = [{"name": "token", "value": "abc999", "domain": "example.com", "path": "/"}]
    ctx = setup_stealth_context_sync(
        mock_browser,
        extra_headers={"X-Custom-Header": "val1"},
        cookies=custom_cookies,
    )
    assert ctx == mock_context
    assert mock_browser.new_context.called
    assert mock_context.add_cookies.called
    assert mock_context.add_init_script.called

def test_stealth_init_script_properties():
    from termux_playwright.browser import STEALTH_INIT_SCRIPT
    assert "delete proto.webdriver" in STEALTH_INIT_SCRIPT
    assert "delete navigator.webdriver" in STEALTH_INIT_SCRIPT
    assert "window.chrome = {" in STEALTH_INIT_SCRIPT
    assert "PDF Viewer" in STEALTH_INIT_SCRIPT

@pytest.mark.asyncio
async def test_launch_storage_exhaustion_auto_purge_rescue(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from termux_playwright.browser import launch
    from termux_playwright.exceptions import StorageExhaustionError

    monkeypatch.setattr("termux_playwright.browser.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.browser.find_chromium_binary", lambda: "/mock/chromium")

    check_calls = 0
    def mock_check_storage():
        nonlocal check_calls
        check_calls += 1
        if check_calls == 1:
            raise StorageExhaustionError("Low storage")
        return 100

    monkeypatch.setattr("termux_playwright.browser.check_preflight_storage", mock_check_storage)
    monkeypatch.setattr("termux_playwright.browser._purge_stale_ephemeral_profiles", lambda max_age_seconds: 2)

    mock_browser = MagicMock()
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    browser = await launch(mock_playwright)
    assert browser == mock_browser
    assert check_calls == 2


