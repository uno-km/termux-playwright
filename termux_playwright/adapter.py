"""
termux_playwright.adapter
==========================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)

오케스트레이터 v0.8.1이 ameva.components Entry Point로 탐색합니다.
Playwright 패키지의 단일 진실 원천: PlaywrightControl.
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from termux_playwright.control.component import PlaywrightControl


class PlaywrightOrchestratorAdapter(BaseOrchestratorAdapter):
    """Playwright Orchestrator Adapter.

    PlaywrightControl을 통해 단일 진실 원천을 보장합니다.

    Playwright 패키지 특성:
    - 브라우저 자동화 패키지이므로 모델(LLM weights) 개념 없음
    - activate_model / deactivate_model / models → OPERATION_NOT_SUPPORTED
    - instance = Browser Context / Worker 프로세스
    - infer() → OPERATION_NOT_SUPPORTED (추론 패키지 아님)
    - drain_instance → 진행 중인 브라우저 세션 완료 후 신규 접수 중단
    """

    COMPONENT_ID = "termux-playwright"

    def __init__(self, control: PlaywrightControl | None = None) -> None:
        self._control = control or PlaywrightControl()

    # ── models: 브라우저 패키지는 모델 목록 없음 ──

    def models(self) -> dict[str, Any]:
        return self._not_supported("models")

    # ── activate / deactivate: 브라우저 패키지는 모델 활성화 없음 ──

    async def activate(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._not_supported("activate")

    async def deactivate(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._not_supported("deactivate")

    # ── infer: 브라우저 자동화 패키지는 streaming inference 미지원 ──

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """termux-playwright는 브라우저 자동화 패키지입니다.
        LLM Streaming inference는 OPERATION_NOT_SUPPORTED.
        """
        yield self._not_supported("infer")


def create_adapter() -> PlaywrightOrchestratorAdapter:
    """Entry Point Factory. 오케스트레이터가 ameva.components 그룹에서 호출합니다."""
    return PlaywrightOrchestratorAdapter()
