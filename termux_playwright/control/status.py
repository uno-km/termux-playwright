"""
termux_playwright.control.status — Playwright 상태 파일 Writer + Heartbeat

브라우저 특화 동작:
  - notify_job_start() → Browser Task 시작
  - notify_job_end()   → Browser Task 완료
  - notify_error()     → Chromium 크래시 등 오류 기록
"""
from __future__ import annotations
from typing import Any
from ameva_component.heartbeat import HeartbeatWriter


class PlaywrightStatusWriter(HeartbeatWriter):
    """PlaywrightControl 상태를 10초마다 상태 파일에 원자적으로 기록합니다."""

    def __init__(self, control: Any) -> None:
        super().__init__(control, name="playwright")
