import os
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
)
from termux_playwright.exceptions import UnsupportedPlatformError, BinaryNotFoundError, StorageExhaustionError

def test_is_termux_with_prefix(monkeypatch):
    monkeypatch.setenv("PREFIX", "/data/data/com.termux/files/usr")
    assert is_termux() is True

def test_is_termux_without_prefix(monkeypatch):
    monkeypatch.delenv("PREFIX", raising=False)
    if not os.path.exists("/data/data/com.termux"):
        assert is_termux() is False

def test_get_cpu_architecture_mapping(monkeypatch):
    monkeypatch.setattr("platform.machine", lambda: "aarch64")
    assert get_cpu_architecture() == "aarch64"
    assert get_wheel_tag_for_arch("aarch64") == SUPPORTED_ARCHITECTURES["aarch64"]

    monkeypatch.setattr("platform.machine", lambda: "arm64")
    assert get_cpu_architecture() == "aarch64"

    monkeypatch.setattr("platform.machine", lambda: "armv8l")
    assert get_cpu_architecture() == "aarch64"
    assert get_wheel_tag_for_arch("armv8l") == SUPPORTED_ARCHITECTURES["armv8l"]

    monkeypatch.setattr("platform.machine", lambda: "x86_64")
    assert get_cpu_architecture() == "x86_64"

def test_unsupported_32bit_architecture_raises(monkeypatch):
    monkeypatch.setattr("platform.machine", lambda: "armv7l")
    with pytest.raises(UnsupportedPlatformError) as exc_info:
        get_cpu_architecture()
    assert "32-bit architecture detected" in str(exc_info.value)

def test_find_chromium_binary_env_override(monkeypatch, tmp_path):
    mock_chrome = tmp_path / "mock-chromium"
    mock_chrome.write_text("#!/bin/sh\nexit 0")
    mock_chrome.chmod(0o755)

    monkeypatch.setenv("PLAYWRIGHT_CHROMIUM_PATH", str(mock_chrome))
    assert find_chromium_binary() == os.path.realpath(str(mock_chrome))

def test_find_chromium_binary_not_found(monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_CHROMIUM_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("os.path.isfile", lambda _: False)
    
    with pytest.raises(BinaryNotFoundError):
        find_chromium_binary()

def test_find_node_binary_not_found(monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_NODEJS_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("os.path.isfile", lambda _: False)

    with pytest.raises(BinaryNotFoundError):
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
