"""Physics and human interaction engine for termux-playwright.

Implements Cubic Bézier curve trajectories, Fitts's Law acceleration/deceleration,
micro-jitter, target overshoot, and Gaussian randomized keyboard typing.
All behaviors are parameterized and toggleable.
"""

import asyncio
import math
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union, Any


@dataclass
class Point:
    """Represents a 2D coordinate point."""
    x: float
    y: float


class CubicBezierTrajectory:
    """Cubic Bézier trajectory generator with Fitts's Law easing, overshoot, and jitter."""

    @staticmethod
    def calculate_bezier_point(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
        """Calculates a single coordinate point along a cubic Bézier curve at time t in [0, 1]."""
        u = 1.0 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        x = uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x
        y = uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y
        return Point(x, y)

    @staticmethod
    def fitts_easing(t: float) -> float:
        """Applies Fitts's Law inspired S-curve easing (acceleration -> steady -> deceleration)."""
        # Sine-based smoothstep S-curve
        return 0.5 * (1.0 - math.cos(t * math.pi))

    @classmethod
    def generate_trajectory(
        cls,
        start: Union[Point, Tuple[float, float]],
        target: Union[Point, Tuple[float, float]],
        steps: int = 30,
        jitter: bool = True,
        overshoot: bool = True,
        deviation: float = 0.25,
    ) -> List[Point]:
        """Generates a list of Point coordinates simulating a natural human mouse stroke.

        Args:
            start: Starting coordinates (Point or tuple of (x, y)).
            target: Destination coordinates (Point or tuple of (x, y)).
            steps: Number of intermediate discrete steps (default 30).
            jitter: Whether to add subtle sub-pixel muscle jitter (default True).
            overshoot: Whether to simulate human target overshooting and correction (default True).
            deviation: Random curve deviation factor for control points (default 0.25).

        Returns:
            List of Point objects forming a non-linear human-like trajectory.
        """
        p0 = Point(start[0], start[1]) if isinstance(start, (tuple, list)) else Point(start.x, start.y)
        p3 = Point(target[0], target[1]) if isinstance(target, (tuple, list)) else Point(target.x, target.y)

        if steps <= 1:
            return [p0, p3]

        dx = p3.x - p0.x
        dy = p3.y - p0.y
        dist = math.hypot(dx, dy)

        # Generate control points with random perpendicular deviation
        perp_x = -dy
        perp_y = dx
        rand_sign1 = 1 if random.random() > 0.5 else -1
        rand_sign2 = 1 if random.random() > 0.5 else -1

        dev1 = random.uniform(0.1, deviation) * rand_sign1
        dev2 = random.uniform(0.1, deviation) * rand_sign2

        p1 = Point(
            p0.x + dx * 0.25 + perp_x * dev1,
            p0.y + dy * 0.25 + perp_y * dev1,
        )
        p2 = Point(
            p0.x + dx * 0.75 + perp_x * dev2,
            p0.y + dy * 0.75 + perp_y * dev2,
        )

        trajectory: List[Point] = []

        # Handle overshoot target
        target_point = p3
        if overshoot and dist > 40:
            overshoot_dist = random.uniform(2.0, min(8.0, dist * 0.08))
            angle = math.atan2(dy, dx)
            overshoot_p = Point(
                p3.x + math.cos(angle) * overshoot_dist,
                p3.y + math.sin(angle) * overshoot_dist,
            )
            main_steps = max(2, int(steps * 0.85))
            correct_steps = steps - main_steps

            for i in range(main_steps):
                raw_t = i / (main_steps - 1)
                eased_t = cls.fitts_easing(raw_t)
                pt = cls.calculate_bezier_point(p0, p1, p2, overshoot_p, eased_t)
                if jitter and 0 < i < main_steps - 1:
                    pt.x += random.gauss(0, 0.4)
                    pt.y += random.gauss(0, 0.4)
                trajectory.append(pt)

            # Correction stroke to true target
            for i in range(1, correct_steps + 1):
                raw_t = i / correct_steps
                eased_t = cls.fitts_easing(raw_t)
                cx = overshoot_p.x + (p3.x - overshoot_p.x) * eased_t
                cy = overshoot_p.y + (p3.y - overshoot_p.y) * eased_t
                trajectory.append(Point(cx, cy))
        else:
            for i in range(steps):
                raw_t = i / (steps - 1)
                eased_t = cls.fitts_easing(raw_t)
                pt = cls.calculate_bezier_point(p0, p1, p2, target_point, eased_t)
                if jitter and 0 < i < steps - 1:
                    pt.x += random.gauss(0, 0.4)
                    pt.y += random.gauss(0, 0.4)
                trajectory.append(pt)

        # Ensure exact end point matches destination
        trajectory[-1] = Point(p3.x, p3.y)
        return trajectory


class HumanMouse:
    """Simulates realistic human mouse behavior using Bézier curves and Fitts's Law."""

    def __init__(self, page_or_mouse: Any, current_x: float = 0.0, current_y: float = 0.0):
        self.page_or_mouse = page_or_mouse
        self.current_x = current_x
        self.current_y = current_y

    def _get_mouse(self) -> Any:
        if hasattr(self.page_or_mouse, "mouse"):
            return self.page_or_mouse.mouse
        return self.page_or_mouse

    async def move_to(
        self,
        x: float,
        y: float,
        steps: int = 30,
        jitter: bool = True,
        overshoot: bool = True,
        min_step_delay: float = 0.003,
        max_step_delay: float = 0.012,
    ) -> None:
        """Moves the mouse naturally to (x, y) asynchronously."""
        mouse = self._get_mouse()
        trajectory = CubicBezierTrajectory.generate_trajectory(
            start=Point(self.current_x, self.current_y),
            target=Point(x, y),
            steps=steps,
            jitter=jitter,
            overshoot=overshoot,
        )

        for pt in trajectory:
            if hasattr(mouse, "move"):
                await mouse.move(pt.x, pt.y)
            self.current_x = pt.x
            self.current_y = pt.y
            delay = random.uniform(min_step_delay, max_step_delay)
            if delay > 0:
                await asyncio.sleep(delay)

        self.current_x = x
        self.current_y = y

    def move_to_sync(
        self,
        x: float,
        y: float,
        steps: int = 30,
        jitter: bool = True,
        overshoot: bool = True,
        min_step_delay: float = 0.003,
        max_step_delay: float = 0.012,
    ) -> None:
        """Moves the mouse naturally to (x, y) synchronously."""
        mouse = self._get_mouse()
        trajectory = CubicBezierTrajectory.generate_trajectory(
            start=Point(self.current_x, self.current_y),
            target=Point(x, y),
            steps=steps,
            jitter=jitter,
            overshoot=overshoot,
        )

        for pt in trajectory:
            if hasattr(mouse, "move"):
                mouse.move(pt.x, pt.y)
            self.current_x = pt.x
            self.current_y = pt.y
            delay = random.uniform(min_step_delay, max_step_delay)
            if delay > 0:
                time.sleep(delay)

        self.current_x = x
        self.current_y = y

    async def move_and_record(
        self,
        start_x: float,
        start_y: float,
        target_x: float,
        target_y: float,
        steps: int = 30,
        jitter: bool = True,
        overshoot: bool = True,
    ) -> List[Point]:
        """Generates and executes trajectory while recording all intermediate coordinates."""
        self.current_x = start_x
        self.current_y = start_y
        trajectory = CubicBezierTrajectory.generate_trajectory(
            start=Point(start_x, start_y),
            target=Point(target_x, target_y),
            steps=steps,
            jitter=jitter,
            overshoot=overshoot,
        )
        mouse = self._get_mouse()
        for pt in trajectory:
            if hasattr(mouse, "move"):
                await mouse.move(pt.x, pt.y)
        self.current_x = target_x
        self.current_y = target_y
        return trajectory

    async def click(
        self,
        target: Union[str, Tuple[float, float], Point],
        steps: int = 30,
        jitter: bool = True,
        overshoot: bool = True,
        click_delay_min: float = 0.06,
        click_delay_max: float = 0.16,
    ) -> None:
        """Moves to target coordinates/selector and performs a human-like mouse click asynchronously."""
        mouse = self._get_mouse()
        x, y = 0.0, 0.0

        if isinstance(target, str):
            # Selector string
            if hasattr(self.page_or_mouse, "locator"):
                loc = self.page_or_mouse.locator(target).first
                box = await loc.bounding_box()
                if box:
                    # Randomize click point inside element bounds
                    offset_x = random.uniform(box["width"] * 0.25, box["width"] * 0.75)
                    offset_y = random.uniform(box["height"] * 0.25, box["height"] * 0.75)
                    x = box["x"] + offset_x
                    y = box["y"] + offset_y
        elif isinstance(target, (tuple, list)):
            x, y = float(target[0]), float(target[1])
        elif isinstance(target, Point):
            x, y = target.x, target.y

        await self.move_to(x, y, steps=steps, jitter=jitter, overshoot=overshoot)

        # Dwell time before down
        await asyncio.sleep(random.uniform(0.02, 0.06))
        if hasattr(mouse, "down"):
            await mouse.down()
        # Hold duration
        await asyncio.sleep(random.uniform(click_delay_min, click_delay_max))
        if hasattr(mouse, "up"):
            await mouse.up()


class HumanKeyboard:
    """Simulates realistic human typing with Gaussian randomized keystroke delays."""

    @staticmethod
    def get_gaussian_delay(mean: float = 0.12, std_dev: float = 0.035, min_d: float = 0.02, max_d: float = 0.4) -> float:
        """Returns a Gaussian-distributed keystroke delay clamped within [min_d, max_d]."""
        delay = random.gauss(mean, std_dev)
        return max(min_d, min(max_d, delay))

    @classmethod
    async def type_text(
        cls,
        page_or_keyboard: Any,
        text: str,
        selector: Optional[str] = None,
        mean_delay: float = 0.12,
        std_dev: float = 0.035,
        min_delay: float = 0.02,
        max_delay: float = 0.4,
    ) -> None:
        """Types text character by character with human-like Gaussian delays asynchronously."""
        if selector and hasattr(page_or_keyboard, "locator"):
            await page_or_keyboard.locator(selector).first.focus()

        keyboard = page_or_keyboard.keyboard if hasattr(page_or_keyboard, "keyboard") else page_or_keyboard

        for char in text:
            if hasattr(keyboard, "type"):
                await keyboard.type(char)
            delay = cls.get_gaussian_delay(mean_delay, std_dev, min_delay, max_delay)
            # Occasional pause for punctuation or spaces
            if char in " ,.!?\n":
                delay += random.uniform(0.05, 0.15)
            await asyncio.sleep(delay)

    @classmethod
    def type_text_sync(
        cls,
        page_or_keyboard: Any,
        text: str,
        selector: Optional[str] = None,
        mean_delay: float = 0.12,
        std_dev: float = 0.035,
        min_delay: float = 0.02,
        max_delay: float = 0.4,
    ) -> None:
        """Types text character by character with human-like Gaussian delays synchronously."""
        if selector and hasattr(page_or_keyboard, "locator"):
            page_or_keyboard.locator(selector).first.focus()

        keyboard = page_or_keyboard.keyboard if hasattr(page_or_keyboard, "keyboard") else page_or_keyboard

        for char in text:
            if hasattr(keyboard, "type"):
                keyboard.type(char)
            delay = cls.get_gaussian_delay(mean_delay, std_dev, min_delay, max_delay)
            if char in " ,.!?\n":
                delay += random.uniform(0.05, 0.15)
            time.sleep(delay)
