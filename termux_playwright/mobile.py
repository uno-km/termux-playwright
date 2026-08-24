"""Dual-Mode Cellular IP Rotator for termux-playwright.

Supports Termux Native device execution and PC ADB Bridge execution to rotate
mobile carrier LTE/5G IP addresses via airplane mode toggling, followed by
fast public IP verification polling.
"""

import asyncio
import enum
import logging
import os
import shutil
import subprocess
import time
import urllib.request
from typing import Optional, List, Dict, Any, Union, Tuple
from .platform import is_termux

logger = logging.getLogger(__name__)

DEFAULT_IP_ENDPOINTS = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://ifconfig.me/ip",
]


class RotationMode(str, enum.Enum):
    """Execution mode for mobile IP rotation."""
    AUTO = "auto"
    TERMUX_NATIVE = "termux_native"
    PC_ADB_BRIDGE = "pc_adb_bridge"


class CellularIpRotator:
    """Orchestrates cellular IP rotation via Android airplane mode toggling."""

    def __init__(
        self,
        mode: Union[RotationMode, str] = RotationMode.AUTO,
        device_id: Optional[str] = None,
        toggle_wait_seconds: float = 1.5,
        settle_wait_seconds: float = 1.5,
        timeout: float = 6.0,
        ip_endpoints: Optional[List[str]] = None,
    ):
        if isinstance(mode, str):
            try:
                self.mode = RotationMode(mode.lower())
            except ValueError:
                self.mode = RotationMode.AUTO
        else:
            self.mode = mode

        self.device_id = device_id or os.environ.get("ANDROID_SERIAL")
        self.toggle_wait_seconds = max(0.5, toggle_wait_seconds)
        self.settle_wait_seconds = max(0.5, settle_wait_seconds)
        self.timeout = max(2.0, timeout)
        self.ip_endpoints = ip_endpoints or list(DEFAULT_IP_ENDPOINTS)

    def _resolve_mode(self) -> RotationMode:
        if self.mode != RotationMode.AUTO:
            return self.mode
        return RotationMode.TERMUX_NATIVE if is_termux() else RotationMode.PC_ADB_BRIDGE

    def _build_cmd(self, sub_command: str) -> List[str]:
        effective_mode = self._resolve_mode()
        if effective_mode == RotationMode.PC_ADB_BRIDGE:
            adb_bin = shutil.which("adb") or "adb"
            cmd = [adb_bin]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["shell", sub_command])
            return cmd
        else:
            # Termux Native
            return ["sh", "-c", sub_command]

    def _execute_shell(self, command_str: str) -> bool:
        cmd = self._build_cmd(command_str)
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
            )
            return res.returncode == 0
        except Exception as e:
            logger.debug(f"CellularIpRotator command failed: {e}")
            return False

    async def _execute_shell_async(self, command_str: str) -> bool:
        cmd = self._build_cmd(command_str)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                return proc.returncode == 0
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return False
        except Exception as e:
            logger.debug(f"CellularIpRotator async command failed: {e}")
            return False

    def get_public_ip_sync(self, timeout: float = 2.5) -> Optional[str]:
        """Fetches the current public IP address synchronously using redundant endpoints."""
        for endpoint in self.ip_endpoints:
            try:
                req = urllib.request.Request(
                    endpoint,
                    headers={"User-Agent": "Mozilla/5.0 (termux-playwright IP Rotator)"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    ip = resp.read().decode("utf-8").strip()
                    if ip and (len(ip.split(".")) == 4 or ":" in ip):
                        return ip
            except Exception:
                continue
        return None

    async def get_public_ip(self, timeout: float = 2.5) -> Optional[str]:
        """Fetches the current public IP address asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_public_ip_sync, timeout)

    def _get_toggle_commands(self) -> Tuple[str, str]:
        # Modern cmd connectivity airplane-mode
        cmd_enable = "cmd connectivity airplane-mode enable || (settings put global airplane_mode_on 1 && am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true)"
        cmd_disable = "cmd connectivity airplane-mode disable || (settings put global airplane_mode_on 0 && am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false)"
        return cmd_enable, cmd_disable

    def rotate_ip_sync(self, verify_ip_change: bool = True) -> Dict[str, Any]:
        """Rotates cellular IP by toggling airplane mode synchronously.

        Returns:
            Dict containing success, old_ip, new_ip, and elapsed_seconds.
        """
        start_time = time.time()
        old_ip = self.get_public_ip_sync(timeout=2.0) if verify_ip_change else None

        cmd_enable, cmd_disable = self._get_toggle_commands()

        # Step 1: Enable airplane mode
        self._execute_shell(cmd_enable)
        time.sleep(self.toggle_wait_seconds)

        # Step 2: Disable airplane mode
        self._execute_shell(cmd_disable)
        time.sleep(self.settle_wait_seconds)

        new_ip = None
        if verify_ip_change:
            # Poll for new IP
            poll_deadline = time.time() + self.timeout
            while time.time() < poll_deadline:
                curr = self.get_public_ip_sync(timeout=1.5)
                if curr and curr != old_ip:
                    new_ip = curr
                    break
                time.sleep(0.4)
            if new_ip is None:
                new_ip = self.get_public_ip_sync(timeout=1.5)

        elapsed = round(time.time() - start_time, 2)
        success = True if not verify_ip_change or (new_ip and (old_ip is None or new_ip != old_ip)) else False

        return {
            "success": success,
            "old_ip": old_ip,
            "new_ip": new_ip or old_ip,
            "elapsed_seconds": elapsed,
            "mode": self._resolve_mode().value,
        }

    async def rotate_ip(self, verify_ip_change: bool = True) -> Dict[str, Any]:
        """Rotates cellular IP by toggling airplane mode asynchronously."""
        start_time = time.time()
        old_ip = await self.get_public_ip(timeout=2.0) if verify_ip_change else None

        cmd_enable, cmd_disable = self._get_toggle_commands()

        # Step 1: Enable airplane mode
        await self._execute_shell_async(cmd_enable)
        await asyncio.sleep(self.toggle_wait_seconds)

        # Step 2: Disable airplane mode
        await self._execute_shell_async(cmd_disable)
        await asyncio.sleep(self.settle_wait_seconds)

        new_ip = None
        if verify_ip_change:
            poll_deadline = time.time() + self.timeout
            while time.time() < poll_deadline:
                curr = await self.get_public_ip(timeout=1.5)
                if curr and curr != old_ip:
                    new_ip = curr
                    break
                await asyncio.sleep(0.4)
            if new_ip is None:
                new_ip = await self.get_public_ip(timeout=1.5)

        elapsed = round(time.time() - start_time, 2)
        success = True if not verify_ip_change or (new_ip and (old_ip is None or new_ip != old_ip)) else False

        return {
            "success": success,
            "old_ip": old_ip,
            "new_ip": new_ip or old_ip,
            "elapsed_seconds": elapsed,
            "mode": self._resolve_mode().value,
        }
