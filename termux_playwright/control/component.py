"""
termux_playwright.control.component
AMEVA Component Protocol v1 — PlaywrightControl

model 관련 모든 명령 → OPERATION_NOT_SUPPORTED
instance = Browser Context / Worker
기존 installer.check_health() + platform.find_chromium_binary() Adapter
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from ameva_component import (
    ComponentInfo, ComponentStateFile,
    ControlMode, InstanceRegistry, InstanceState, InstanceStatus,
    OperationNotSupported, now_timestamps, log_stderr, PROTOCOL_COMPONENT,
)
from ameva_component.control import ComponentControl


class PlaywrightControl(ComponentControl):
    """
    termux-playwright ComponentControl.

    브라우저 자동화 패키지이므로 모델 개념 없음.
    list_models, install_model, activate_model, deactivate_model, model_status
    → 전부 OPERATION_NOT_SUPPORTED.
    """

    COMPONENT_ID   = "termux-playwright"
    COMPONENT_TYPE = "browser"
    CAPABILITIES   = ("browser.navigate", "browser.extract",
                      "browser.screenshot", "browser.action")

    def __init__(self) -> None:
        self._state_file = ComponentStateFile(self.COMPONENT_ID)
        self._inst_reg   = InstanceRegistry(self.COMPONENT_ID)

    def _get_version(self) -> str:
        try:
            from termux_playwright import __version__; return __version__
        except Exception: return "1.80.1"

    def component_info(self) -> dict:
        info = ComponentInfo(
            protocol=PROTOCOL_COMPONENT, component_id=self.COMPONENT_ID,
            component_type=self.COMPONENT_TYPE, version=self._get_version(),
            capabilities=self.CAPABILITIES,
        )
        info.validate()
        return info.to_dict()

    def doctor_lite(self) -> dict:
        """
        경량 진단.
        실제 브라우저 실행 금지 (doctor_full에서만).
        Chromium 바이너리 경로 + 실행 권한 확인만.
        """
        ts = now_timestamps()
        state_data = self._state_file.read()
        stale = self._state_file.is_stale(threshold_ms=30_000)

        chromium_path, chromium_ok = self._check_chromium()
        worker_pids = self._get_worker_pids()
        instances = self._inst_reg.list_all()

        ready = chromium_ok
        degraded = stale or not chromium_ok

        return {
            "protocol": "ameva-component-status/1",
            "component_id": self.COMPONENT_ID, "component_type": self.COMPONENT_TYPE,
            "version": self._get_version(), "ready": ready, "degraded": degraded,
            **ts,
            "chromium": {"path": chromium_path, "executable": chromium_ok},
            "capabilities": list(self.CAPABILITIES),
            "browser_workers": len(worker_pids),
            "worker_pids": worker_pids,
            "instances": [{"instance_id": i.instance_id, "state": i.state.value,
                           "active_jobs": i.active_jobs} for i in instances],
            "errors": [state_data.get("last_error")] if state_data and state_data.get("last_error") else [],
            "state_file": {"path": str(self._state_file.path), "stale": stale,
                           "updated_at": state_data.get("updated_at") if state_data else None},
        }

    def _check_chromium(self) -> tuple[str | None, bool]:
        """Chromium 바이너리 존재 + 실행 권한 확인 — 실행 금지."""
        try:
            from termux_playwright.platform import find_chromium_binary
            path = find_chromium_binary()
            if path and os.access(str(path), os.X_OK):
                return str(path), True
            return str(path) if path else None, False
        except Exception:
            return None, False

    def _get_worker_pids(self) -> list[int]:
        """실제 실행 중인 Browser Worker PID 목록. os.kill(pid, 0)으로 확인."""
        try:
            from termux_playwright.reaper import ProcessReaper
            reaper = ProcessReaper()
            pids = []
            for pid in (reaper.get_pids() if hasattr(reaper, "get_pids") else []):
                try:
                    os.kill(pid, 0)
                    pids.append(pid)
                except Exception:
                    pass
            return pids
        except Exception:
            return []

    def doctor_full(self) -> dict:
        """기존 installer.run_doctor() 전체 실행 — 실제 Chromium 실행 포함."""
        lite = self.doctor_lite()
        try:
            from termux_playwright.installer import run_doctor
            result = run_doctor()
            lite["full_doctor"] = result if isinstance(result, dict) else {"output": str(result)}
        except Exception as e:
            lite["doctor_error"] = str(e)
        lite["doctor_level"] = "full"
        return lite

    # ------------------------------------------------------------------
    # 모델 관련 — 전부 OPERATION_NOT_SUPPORTED
    # ------------------------------------------------------------------

    def list_models(self) -> dict:
        raise OperationNotSupported("list_models", self.COMPONENT_ID)

    def model_status(self, model_id=None) -> dict:
        raise OperationNotSupported("model_status", self.COMPONENT_ID)

    def install_model(self, request: dict) -> dict:
        raise OperationNotSupported("install_model", self.COMPONENT_ID)

    async def activate_model(self, request: dict) -> dict:
        raise OperationNotSupported("activate_model", self.COMPONENT_ID)

    async def deactivate_model(self, request: dict) -> dict:
        raise OperationNotSupported("deactivate_model", self.COMPONENT_ID)

    # ------------------------------------------------------------------
    # Browser Worker Instance 관리
    # ------------------------------------------------------------------

    def list_instances(self) -> dict:
        pids = self._get_worker_pids()
        instances = self._inst_reg.list_all()
        return {
            "browser_workers": [i.to_dict() for i in instances],
            "live_pids":       pids,
            "total":           len(instances),
        }

    async def start_instance(self, request: dict) -> dict:
        headless = request.get("headless", True)
        instance_id = request.get("instance_id") or f"browser-{int(time.time())}"
        inst = InstanceStatus(
            instance_id=instance_id, component_id=self.COMPONENT_ID,
            model_id="chromium", state=InstanceState.HOT,
            active_jobs=0, queue_depth=0, max_concurrency=10,
            backend="chromium", started_at=time.time(), last_heartbeat=time.time(),
            last_error=None, control_mode=ControlMode.SUBPROCESS,
        )
        self._inst_reg.register(inst)
        self._write_state()
        return {"instance_id": instance_id, "state": InstanceState.HOT.value, "headless": headless}

    async def drain_instance(self, instance_id: str) -> dict:
        from ameva_component import InstanceNotFound
        if not self._inst_reg.get(instance_id): raise InstanceNotFound(instance_id)
        self._inst_reg.update_state(instance_id, InstanceState.DRAINING)
        return {"instance_id": instance_id, "state": InstanceState.DRAINING.value}

    async def stop_instance(self, instance_id: str) -> dict:
        from ameva_component import InstanceNotFound
        if not self._inst_reg.get(instance_id): raise InstanceNotFound(instance_id)
        self._inst_reg.update_state(instance_id, InstanceState.STOPPED)
        self._inst_reg.remove(instance_id)
        self._write_state()
        return {"instance_id": instance_id, "state": InstanceState.STOPPED.value}

    def _write_state(self, *, ready: bool | None = None, last_error: str | None = None) -> None:
        ts = now_timestamps()
        _, chromium_ok = self._check_chromium()
        _ready = chromium_ok if ready is None else ready
        self._state_file.write({
            "protocol": "ameva-component-status/1", "component_id": self.COMPONENT_ID,
            "component_type": self.COMPONENT_TYPE, "version": self._get_version(),
            "ready": _ready, "degraded": not _ready, **ts,
            "last_error": last_error,
        })
