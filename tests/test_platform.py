import os
import sys
import shutil
import pytest
from termux_playwright.platform import (
    is_termux,
    get_cpu_architecture,
    get_wheel_tag_for_arch,
    find_chromium_binary,
    find_node_binary,
    check_preflight_storage,
    get_android_sdk_version,
    SUPPORTED_ARCHITECTURES,
    ANDROID_10_SDK_VERSION,
)
from termux_playwright.exceptions import UnsupportedPlatformError, BinaryNotFoundError, StorageExhaustionError

def test_is_termux_with_prefix(monkeypatch):
    monkeypatch.setenv("PREFIX", "/data/data/com.termux/files/usr")
    assert is_termux() is True

def test_is_termux_with_custom_termux_variants(monkeypatch):
    monkeypatch.setenv("PREFIX", "/data/data/io.neoterm/files/usr")
    assert is_termux() is True

    monkeypatch.setenv("PREFIX", "/data/data/com.termux.float/files/usr")
    assert is_termux() is True

    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.setenv("TERMUX_VERSION", "0.118.0")
    assert is_termux() is True

def test_is_termux_without_prefix(monkeypatch):
    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.delenv("TERMUX_VERSION", raising=False)
    monkeypatch.delenv("TERMUX_APP_PID", raising=False)
    monkeypatch.delenv("TERMUX_MAIN_PACKAGE", raising=False)
    monkeypatch.setattr("sys.executable", "/usr/bin/python3")
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("os.path.isdir", lambda path: False)
    assert is_termux() is False

def test_is_termux_other_android_app_isolation_no_false_positive(monkeypatch):
    """If running in Pydroid3/QPython, having Termux folder on disk must not trigger is_termux."""
    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.delenv("TERMUX_VERSION", raising=False)
    monkeypatch.delenv("TERMUX_APP_PID", raising=False)
    monkeypatch.delenv("TERMUX_MAIN_PACKAGE", raising=False)
    monkeypatch.setattr("sys.executable", "/data/data/ru.iiec.pydroid3/files/bin/python3")
    monkeypatch.setattr("sys.prefix", "/data/data/ru.iiec.pydroid3/files")
    # Even if Termux folder exists on disk, permission denied (os.access = False) prevents false positive
    monkeypatch.setattr("os.path.isdir", lambda path: True if "com.termux" in path else False)
    monkeypatch.setattr("os.access", lambda path, mode: False)
    assert is_termux() is False

def test_get_cpu_architecture_mapping(monkeypatch):
    monkeypatch.setattr("platform.machine", lambda: "aarch64")
    assert get_cpu_architecture() == "aarch64"
    assert get_wheel_tag_for_arch("aarch64") == SUPPORTED_ARCHITECTURES["aarch64"]

    monkeypatch.setattr("platform.machine", lambda: "arm64")
    assert get_cpu_architecture() == "aarch64"
    assert get_wheel_tag_for_arch("arm64") == SUPPORTED_ARCHITECTURES["arm64"]

    monkeypatch.setattr("platform.machine", lambda: "armv8l")
    assert get_cpu_architecture() == "aarch64"

    monkeypatch.setattr("platform.machine", lambda: "x86_64")
    assert get_cpu_architecture() == "x86_64"
    assert get_wheel_tag_for_arch("x86_64") == SUPPORTED_ARCHITECTURES["x86_64"]

    monkeypatch.setattr("platform.machine", lambda: "amd64")
    assert get_cpu_architecture() == "x86_64"

def test_get_cpu_architecture_unsupported(monkeypatch):
    monkeypatch.setattr("platform.machine", lambda: "i686")
    with pytest.raises(UnsupportedPlatformError, match="Unsupported CPU architecture: i686"):
        get_cpu_architecture()

    monkeypatch.setattr("platform.machine", lambda: "armv7l")
    with pytest.raises(UnsupportedPlatformError, match="Unsupported CPU architecture: armv7l"):
        get_cpu_architecture()

def test_get_wheel_tag_unsupported():
    with pytest.raises(UnsupportedPlatformError, match="No pre-built Playwright wheel tag mapped for architecture: mips"):
        get_wheel_tag_for_arch("mips")

def test_find_chromium_binary_from_env(monkeypatch, tmp_path):
    fake_chromium = tmp_path / "my_custom_chromium"
    fake_chromium.write_text("dummy binary", encoding="utf-8")
    monkeypatch.setenv("PLAYWRIGHT_CHROMIUM_PATH", str(fake_chromium))
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert find_chromium_binary() == os.path.realpath(str(fake_chromium))

def test_find_chromium_binary_termux_native(monkeypatch, tmp_path):
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM_PATH", raising=False)
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: True)
    
    mock_prefix = tmp_path / "usr"
    mock_prefix.mkdir(parents=True, exist_ok=True)
    chromium_launcher = mock_prefix / "lib" / "chromium" / "chromium-launcher.sh"
    chromium_launcher.parent.mkdir(parents=True, exist_ok=True)
    chromium_launcher.write_text("#!/bin/sh\nexec true", encoding="utf-8")
    
    monkeypatch.setattr("termux_playwright.platform.get_termux_prefix", lambda: str(mock_prefix))
    monkeypatch.setattr("shutil.which", lambda _: None)
    
    found = find_chromium_binary()
    assert os.path.realpath(str(chromium_launcher)) == found

def test_find_chromium_binary_not_found(monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM_PATH", raising=False)
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: False)
    monkeypatch.setattr("termux_playwright.platform.get_termux_prefix", lambda: "/tmp/nonexistent_prefix_path")
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("glob.glob", lambda _: [])
    monkeypatch.setattr("os.path.isfile", lambda _: False)
    monkeypatch.setattr(sys, "platform", "linux")

    with pytest.raises(BinaryNotFoundError, match="Native Chromium binary was not found"):
        find_chromium_binary()

def test_find_node_binary_success(monkeypatch, tmp_path):
    fake_node = tmp_path / "node"
    fake_node.write_text("dummy node", encoding="utf-8")
    monkeypatch.setattr("shutil.which", lambda cmd: str(fake_node) if cmd == "node" else None)
    assert find_node_binary() == os.path.realpath(str(fake_node))

def test_find_node_binary_not_found(monkeypatch):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(BinaryNotFoundError, match="Node.js binary not found in PATH"):
        find_node_binary()

def test_check_preflight_storage_exhaustion(monkeypatch, tmp_path):
    # Mock disk_usage to return 10MB free (< 50MB)
    class FakeUsage:
        free = 10 * 1024 * 1024
    monkeypatch.setattr("shutil.disk_usage", lambda _: FakeUsage())

    with pytest.raises(StorageExhaustionError) as exc_info:
        check_preflight_storage(str(tmp_path))
    assert "Insufficient disk space" in str(exc_info.value)

def test_check_preflight_storage_healthy(monkeypatch, tmp_path):
    class FakeUsage:
        free = 500 * 1024 * 1024
    monkeypatch.setattr("shutil.disk_usage", lambda _: FakeUsage())

    free_mb = check_preflight_storage(str(tmp_path))
    assert free_mb == 500

def test_check_preflight_storage_custom_env_override(monkeypatch, tmp_path):
    import termux_playwright.platform as plat
    monkeypatch.setattr(plat, "MINIMUM_REQUIRED_STORAGE_MB", 300)
    class FakeUsage:
        free = 200 * 1024 * 1024
    monkeypatch.setattr("shutil.disk_usage", lambda _: FakeUsage())

    with pytest.raises(StorageExhaustionError):
        check_preflight_storage(str(tmp_path))

def test_get_android_sdk_version_non_android(monkeypatch):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: False)
    assert get_android_sdk_version() == 0

def test_get_android_sdk_version_termux_success(monkeypatch):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: True)
    if hasattr(sys, "getandroidapilevel"):
        monkeypatch.delattr(sys, "getandroidapilevel")
    monkeypatch.setattr("shutil.which", lambda cmd: "/bin/getprop" if cmd == "getprop" else None)
    
    class FakeProc:
        returncode = 0
        stdout = "31\n"
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: FakeProc())
    assert get_android_sdk_version() == 31

def test_get_android_sdk_version_termux_fallback_on_failure(monkeypatch):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: True)
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("os.path.isfile", lambda _: False)
    if hasattr(sys, "getandroidapilevel"):
        monkeypatch.delattr(sys, "getandroidapilevel")
    # Must return safe default SDK 29 to protect against SELinux W^X violation
    assert get_android_sdk_version() == ANDROID_10_SDK_VERSION

def test_get_android_sdk_version_tier1_sys_api_level(monkeypatch):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: True)
    monkeypatch.setattr(sys, "getandroidapilevel", lambda: 26, raising=False)
    assert get_android_sdk_version() == 26

def test_get_android_sdk_version_tier3_build_prop(monkeypatch, tmp_path):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: True)
    monkeypatch.setattr("shutil.which", lambda _: None)
    if hasattr(sys, "getandroidapilevel"):
        monkeypatch.delattr(sys, "getandroidapilevel")
    
    mock_prop = tmp_path / "build.prop"
    mock_prop.write_text("ro.build.version.release=8.0.0\nro.build.version.sdk=26\n", encoding="utf-8")
    
    orig_open = open
    def fake_isfile(p):
        return p == "/system/build.prop"
    def fake_open(p, *a, **kw):
        if p == "/system/build.prop":
            return orig_open(str(mock_prop), "r", encoding="utf-8")
        return orig_open(p, *a, **kw)

    monkeypatch.setattr("os.path.isfile", fake_isfile)
    monkeypatch.setattr("builtins.open", fake_open)
    assert get_android_sdk_version() == 26

def test_find_chromium_binary_windows_desktop_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr("termux_playwright.platform.is_termux", lambda: False)
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM_PATH", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("shutil.which", lambda _: None)
    
    fake_chrome = tmp_path / "chrome.exe"
    fake_chrome.write_text("mock binary", encoding="utf-8")
    
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    target_chrome = tmp_path / "Google" / "Chrome" / "Application" / "chrome.exe"
    target_chrome.parent.mkdir(parents=True, exist_ok=True)
    target_chrome.write_text("mock chrome", encoding="utf-8")
    
    found = find_chromium_binary()
    assert os.path.realpath(str(target_chrome)) == found

def test_get_installed_chromium_version_success(monkeypatch, tmp_path):
    import termux_playwright.platform as tp_platform
    from termux_playwright.platform import get_installed_chromium_version
    import subprocess

    tp_platform._cached_chromium_stat = None

    fake_chrome = tmp_path / "chromium"
    fake_chrome.write_text("mock binary", encoding="utf-8")
    monkeypatch.setattr("termux_playwright.platform.find_chromium_binary", lambda: str(fake_chrome))
    def mock_run(cmd, *args, **kwargs):
        class MockRes:
            returncode = 0
            stdout = b"Chromium 131.0.6778.85 Built on Ubuntu"
        return MockRes()
    monkeypatch.setattr(subprocess, "run", mock_run)

    full_v, major_v = get_installed_chromium_version()
    assert full_v == "131.0.6778.85"
    assert major_v == "131"
    tp_platform._cached_chromium_stat = None

def test_get_installed_chromium_version_mtime_invalidation(monkeypatch, tmp_path):
    import time
    import termux_playwright.platform as tp_platform
    from termux_playwright.platform import get_installed_chromium_version
    import subprocess

    tp_platform._cached_chromium_stat = None

    fake_chrome = tmp_path / "chromium"
    fake_chrome.write_text("mock binary v1", encoding="utf-8")
    monkeypatch.setattr("termux_playwright.platform.find_chromium_binary", lambda: str(fake_chrome))

    call_count = 0
    def mock_run(cmd, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        class MockRes:
            returncode = 0
            stdout = f"Chromium 13{call_count}.0.0.0".encode("utf-8")
        return MockRes()
    monkeypatch.setattr(subprocess, "run", mock_run)

    # 1. First call -> executes subprocess
    v1, m1 = get_installed_chromium_version()
    assert v1 == "131.0.0.0"
    assert call_count == 1

    # 2. Second call with unchanged mtime -> hits cache (no subprocess execution)
    v2, m2 = get_installed_chromium_version()
    assert v2 == "131.0.0.0"
    assert call_count == 1

    # 3. Modify mtime (simulating `pkg upgrade chromium`) -> refreshes cache!
    new_time = time.time() + 10.0
    os.utime(str(fake_chrome), (new_time, new_time))
    v3, m3 = get_installed_chromium_version()
    assert v3 == "132.0.0.0"
    assert call_count == 2

    tp_platform._cached_chromium_stat = None

def test_get_installed_chromium_version_fallback_on_error(monkeypatch):
    import termux_playwright.platform as tp_platform
    from termux_playwright.platform import get_installed_chromium_version
    tp_platform._cached_chromium_stat = None

    monkeypatch.setattr("termux_playwright.platform.find_chromium_binary", lambda: (_ for _ in ()).throw(Exception("binary missing")))

    full_v, major_v = get_installed_chromium_version()
    assert full_v == "130.0.0.0"
    assert major_v == "130"
    tp_platform._cached_chromium_stat = None
