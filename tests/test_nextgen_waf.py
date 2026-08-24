import pytest
from termux_playwright.waf import (
    WafChallengeType,
    TurnstileEvaluator,
)
from termux_playwright.physics import HumanMouse


class MockLocator:
    def __init__(self, match_count=0, box=None):
        self._count = match_count
        self._box = box or {"x": 100, "y": 200, "width": 300, "height": 65}

    @property
    def first(self):
        return self

    async def count(self):
        return self._count

    async def bounding_box(self):
        return self._box


class MockPage:
    def __init__(self, detected_selector=None, title="Test Page"):
        self.detected_selector = detected_selector
        self._title = title
        self.mouse = MockMouse()

    def locator(self, selector: str):
        if self.detected_selector and selector == self.detected_selector:
            return MockLocator(match_count=1)
        return MockLocator(match_count=0)

    async def title(self):
        return self._title


class MockMouse:
    def __init__(self):
        self.moves = []
        self.downs = 0
        self.ups = 0

    async def move(self, x: float, y: float):
        self.moves.append((x, y))

    async def down(self):
        self.downs += 1

    async def up(self):
        self.ups += 1


@pytest.mark.asyncio
async def test_waf_challenge_detection():
    # Cloudflare Turnstile
    cf_page = MockPage(detected_selector="iframe[src*='challenges.cloudflare.com']")
    detected = await TurnstileEvaluator.detect_challenge(cf_page)
    assert detected == WafChallengeType.CLOUDFLARE_TURNSTILE

    # Cloudflare Managed
    managed_page = MockPage(title="Just a moment...")
    detected_managed = await TurnstileEvaluator.detect_challenge(managed_page)
    assert detected_managed == WafChallengeType.CLOUDFLARE_MANAGED

    # None
    clean_page = MockPage()
    detected_none = await TurnstileEvaluator.detect_challenge(clean_page)
    assert detected_none == WafChallengeType.NONE


@pytest.mark.asyncio
async def test_waf_solve_turnstile_mock():
    page = MockPage(detected_selector="iframe[src*='challenges.cloudflare.com']")
    solved = await TurnstileEvaluator.solve_turnstile(page, timeout=1.0)
    assert solved is True
    assert page.mouse.downs == 1
    assert page.mouse.ups == 1
