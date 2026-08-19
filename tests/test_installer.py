import json
import pytest
from unittest.mock import MagicMock
from termux_playwright.installer import (
    resolve_latest_compatible_version,
    fetch_pypi_wheel_info,
    install_system_dependencies,
    doctor,
    DEFAULT_PLAYWRIGHT_VERSION,
)
from termux_playwright.exceptions import InstallationError

def test_resolve_latest_compatible_version_success(monkeypatch):
    fake_data = json.dumps({"info": {"version": "1.65.0"}}).encode("utf-8")
    
    class FakeResponse:
        status = 200
        def read(self):
            return fake_data
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: FakeResponse())
    assert resolve_latest_compatible_version() == "1.65.0"

def test_resolve_latest_compatible_version_fallback_emits_warning(monkeypatch):
    def mock_urlopen_fail(req, timeout=10):
        raise ConnectionError("PyPI unreachable")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_fail)
    with pytest.warns(RuntimeWarning) as warning_info:
        ver = resolve_latest_compatible_version()
    assert ver == DEFAULT_PLAYWRIGHT_VERSION
    assert "Could not query PyPI" in str(warning_info[0].message)

def test_fetch_pypi_wheel_info_default_uses_verified_lts(monkeypatch):
    fake_data = json.dumps({
        "urls": [
            {
                "filename": "playwright-1.48.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
                "url": "https://fake.pypi/playwright-1.48.0.whl",
            }
        ]
    }).encode("utf-8")

    class FakeResponse:
        status = 200
        def read(self):
            return fake_data
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("termux_playwright.installer.get_cpu_architecture", lambda: "aarch64")
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=15: FakeResponse())

    url, filename, version = fetch_pypi_wheel_info()
    assert url == "https://fake.pypi/playwright-1.48.0.whl"
    assert "aarch64" in filename
    assert version == "1.48.0"

def test_fetch_pypi_wheel_info_latest_flag(monkeypatch):
    fake_data = json.dumps({
        "urls": [
            {
                "filename": "playwright-1.62.0-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
                "url": "https://fake.pypi/playwright-1.62.0.whl",
            }
        ]
    }).encode("utf-8")

    class FakeResponse:
        status = 200
        def read(self):
            return fake_data
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("termux_playwright.installer.get_cpu_architecture", lambda: "aarch64")
    monkeypatch.setattr("termux_playwright.installer.resolve_latest_compatible_version", lambda: "1.62.0")
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=15: FakeResponse())

    url, filename, version = fetch_pypi_wheel_info(version="latest")
    assert version == "1.62.0"

def test_install_system_dependencies_pkg_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    with pytest.raises(InstallationError) as exc_info:
        install_system_dependencies()
    assert "pkg' package manager was not found" in str(exc_info.value)

def test_install_system_dependencies_success(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: "/data/data/com.termux/files/usr/bin/pkg" if cmd == "pkg" else None)
    
    executed_cmds = []
    class FakeProc:
        returncode = 0
        stdout = "Installed"
        stderr = ""

    def mock_run(cmd, *args, **kwargs):
        executed_cmds.append(cmd)
        return FakeProc()

    monkeypatch.setattr("subprocess.run", mock_run)
    
    # 1. Default: lean packages (chromium, nodejs, python-greenlet) - NO 1.2GB clang
    install_system_dependencies()
    assert len(executed_cmds) == 1
    pkg_cmd = executed_cmds[0]
    assert "chromium" in pkg_cmd
    assert "nodejs" in pkg_cmd
    assert "python-greenlet" in pkg_cmd
    assert "procps" in pkg_cmd
    assert "termux-api" in pkg_cmd
    assert "clang" not in pkg_cmd

    # 2. With build tools: includes clang, make
    install_system_dependencies(include_build_tools=True)
    assert len(executed_cmds) == 2
    pkg_cmd_with_build = executed_cmds[1]
    assert "clang" in pkg_cmd_with_build
    assert "make" in pkg_cmd_with_build



def test_doctor_healthy(monkeypatch):
    monkeypatch.setattr("termux_playwright.installer.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.installer.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.installer.get_cpu_architecture", lambda: "aarch64")
    monkeypatch.setattr("termux_playwright.installer.find_node_binary", lambda: "/mock/node")
    monkeypatch.setattr("termux_playwright.installer.find_chromium_binary", lambda: "/mock/chromium")
    monkeypatch.setattr("termux_playwright.installer.locate_playwright_package_dir", lambda: "/mock/playwright")
    monkeypatch.setattr("termux_playwright.installer.is_core_bundle_patched", lambda: True)

    assert doctor() is True

def test_doctor_unhealthy_when_binary_missing(monkeypatch):
    from termux_playwright.exceptions import BinaryNotFoundError

    monkeypatch.setattr("termux_playwright.installer.is_termux", lambda: True)
    monkeypatch.setattr("termux_playwright.installer.check_preflight_storage", lambda: 500)
    monkeypatch.setattr("termux_playwright.installer.get_cpu_architecture", lambda: "aarch64")
    monkeypatch.setattr("termux_playwright.installer.find_node_binary", lambda: "/mock/node")
    
    def mock_find_chrome():
        raise BinaryNotFoundError("Chromium not found")
    monkeypatch.setattr("termux_playwright.installer.find_chromium_binary", mock_find_chrome)
    monkeypatch.setattr("termux_playwright.installer.locate_playwright_package_dir", lambda: "/mock/playwright")
    monkeypatch.setattr("termux_playwright.installer.is_core_bundle_patched", lambda: True)

    assert doctor() is False
