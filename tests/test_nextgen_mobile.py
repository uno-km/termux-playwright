import pytest
from termux_playwright.mobile import (
    RotationMode,
    CellularIpRotator,
    DEFAULT_IP_ENDPOINTS,
)


def test_rotation_mode_resolution():
    rotator_adb = CellularIpRotator(mode=RotationMode.PC_ADB_BRIDGE, device_id="emulator-5554")
    assert rotator_adb.mode == RotationMode.PC_ADB_BRIDGE
    assert rotator_adb.device_id == "emulator-5554"

    cmd = rotator_adb._build_cmd("cmd connectivity airplane-mode enable")
    assert "shell" in cmd
    assert "-s" in cmd
    assert "emulator-5554" in cmd

    rotator_termux = CellularIpRotator(mode=RotationMode.TERMUX_NATIVE)
    cmd_termux = rotator_termux._build_cmd("cmd connectivity airplane-mode enable")
    assert cmd_termux[0] == "sh"
    assert cmd_termux[1] == "-c"


def test_get_public_ip_sync_mock(monkeypatch):
    rotator = CellularIpRotator()

    class MockResponse:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def read(self):
            return b"203.0.113.45\n"

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout: MockResponse())

    ip = rotator.get_public_ip_sync()
    assert ip == "203.0.113.45"


@pytest.mark.asyncio
async def test_rotate_ip_mocked(monkeypatch):
    rotator = CellularIpRotator(
        mode=RotationMode.TERMUX_NATIVE,
        toggle_wait_seconds=0.01,
        settle_wait_seconds=0.01,
    )

    async def mock_exec_async(cmd):
        return True

    monkeypatch.setattr(rotator, "_execute_shell_async", mock_exec_async)

    ips = ["198.51.100.1", "198.51.100.2"]
    call_count = 0

    async def mock_get_ip(timeout=2.0):
        nonlocal call_count
        ip = ips[min(call_count, len(ips) - 1)]
        call_count += 1
        return ip

    monkeypatch.setattr(rotator, "get_public_ip", mock_get_ip)

    result = await rotator.rotate_ip(verify_ip_change=True)
    assert result["success"] is True
    assert result["old_ip"] == "198.51.100.1"
    assert result["new_ip"] == "198.51.100.2"
    assert result["mode"] == "termux_native"
