"""termux_playwright.adapter — Orchestrator Adapter."""
from __future__ import annotations
from termux_playwright.control.component import PlaywrightControl

class PlaywrightOrchestratorAdapter:
    def __init__(self, control: PlaywrightControl | None = None) -> None:
        self._control = control or PlaywrightControl()
    def info(self) -> dict: return self._control.component_info()
    def health(self) -> dict: return self._control.doctor_lite()
    def instances(self) -> dict: return self._control.list_instances()
    async def start_browser(self, req: dict) -> dict: return await self._control.start_instance(req)
    async def stop_browser(self, instance_id: str) -> dict: return await self._control.stop_instance(instance_id)
