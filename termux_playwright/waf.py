"""WAF and bot challenge evaluator for termux-playwright.

Detects Cloudflare Turnstile, Cloudflare Managed Challenge, hCaptcha, and reCAPTCHA.
Provides coordinated auto-resolution via HumanMouse interaction models.
"""

import asyncio
import enum
import logging
import random
from typing import Optional, Any
from .physics import HumanMouse

logger = logging.getLogger(__name__)


class WafChallengeType(str, enum.Enum):
    """Known web application firewall bot challenge types."""
    CLOUDFLARE_TURNSTILE = "cloudflare_turnstile"
    CLOUDFLARE_MANAGED = "cloudflare_managed"
    HCAPTCHA = "hcaptcha"
    RECAPTCHA = "recaptcha"
    NONE = "none"


class TurnstileEvaluator:
    """Evaluates page state for Cloudflare Turnstile / WAF challenges and executes human interaction."""

    CLOUDFLARE_SELECTORS = [
        "iframe[src*='challenges.cloudflare.com']",
        "iframe[src*='cf-turnstile']",
        "#cf-stage",
        "#turnstile-wrapper",
        "div[class*='cf-turnstile']",
    ]

    HCAPTCHA_SELECTORS = [
        "iframe[src*='hcaptcha.com']",
        "div.h-captcha",
    ]

    RECAPTCHA_SELECTORS = [
        "iframe[src*='google.com/recaptcha']",
        "iframe[src*='recaptcha']",
        "div.g-recaptcha",
    ]

    @classmethod
    def _get_first(cls, loc: Any) -> Any:
        if hasattr(loc, "first"):
            first_val = getattr(loc, "first")
            return first_val() if callable(first_val) else first_val
        return loc

    @classmethod
    async def detect_challenge(cls, page: Any) -> WafChallengeType:
        """Detects the presence of WAF challenge widgets on the current page."""
        try:
            for sel in cls.CLOUDFLARE_SELECTORS:
                loc = cls._get_first(page.locator(sel))
                if await loc.count() > 0:
                    return WafChallengeType.CLOUDFLARE_TURNSTILE

            title = (await page.title()).lower() if hasattr(page, "title") else ""
            if "just a moment" in title or "attention required" in title:
                return WafChallengeType.CLOUDFLARE_MANAGED

            for sel in cls.HCAPTCHA_SELECTORS:
                loc = cls._get_first(page.locator(sel))
                if await loc.count() > 0:
                    return WafChallengeType.HCAPTCHA

            for sel in cls.RECAPTCHA_SELECTORS:
                loc = cls._get_first(page.locator(sel))
                if await loc.count() > 0:
                    return WafChallengeType.RECAPTCHA

        except Exception as e:
            logger.debug(f"Challenge detection error: {e}")

        return WafChallengeType.NONE

    @classmethod
    async def solve_turnstile(
        cls,
        page: Any,
        human_mouse: Optional[HumanMouse] = None,
        timeout: float = 12.0,
    ) -> bool:
        """Locates the Cloudflare Turnstile iframe and clicks the verification checkbox using human mouse movement."""
        mouse = human_mouse or HumanMouse(page)
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            try:
                for frame_sel in cls.CLOUDFLARE_SELECTORS:
                    frame_loc = cls._get_first(page.locator(frame_sel))
                    if await frame_loc.count() > 0:
                        box = await frame_loc.bounding_box()
                        if box and box["width"] > 20 and box["height"] > 20:
                            # Target the checkbox inside the Turnstile widget (approx 30px from left, 50% height)
                            target_x = box["x"] + min(36.0, box["width"] * 0.2) + random.uniform(-4, 4)
                            target_y = box["y"] + (box["height"] * 0.5) + random.uniform(-4, 4)

                            await mouse.click(
                                target=(target_x, target_y),
                                steps=random.randint(25, 38),
                                jitter=True,
                                overshoot=True,
                            )
                            # Wait for challenge resolution
                            await asyncio.sleep(0.5)
                            return True
            except Exception as e:
                logger.debug(f"Solve Turnstile attempt error: {e}")

            await asyncio.sleep(0.1)

        return False
