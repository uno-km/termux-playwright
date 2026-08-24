import math
import pytest
from termux_playwright.physics import (
    Point,
    CubicBezierTrajectory,
    HumanMouse,
    HumanKeyboard,
)


def test_point_representation():
    p = Point(10.5, 20.25)
    assert p.x == 10.5
    assert p.y == 20.25


def test_fitts_easing_monotonic_in_range():
    # Easing at 0 should be 0, at 1 should be 1
    assert math.isclose(CubicBezierTrajectory.fitts_easing(0.0), 0.0, abs_tol=1e-5)
    assert math.isclose(CubicBezierTrajectory.fitts_easing(1.0), 1.0, abs_tol=1e-5)
    assert 0.0 <= CubicBezierTrajectory.fitts_easing(0.5) <= 1.0


def test_cubic_bezier_trajectory_curvature():
    start = (0.0, 0.0)
    target = (500.0, 500.0)
    steps = 35

    trajectory = CubicBezierTrajectory.generate_trajectory(
        start=start,
        target=target,
        steps=steps,
        jitter=True,
        overshoot=False,
    )

    assert len(trajectory) == steps
    assert math.isclose(trajectory[0].x, 0.0, abs_tol=1e-3)
    assert math.isclose(trajectory[0].y, 0.0, abs_tol=1e-3)
    assert math.isclose(trajectory[-1].x, 500.0, abs_tol=1e-3)
    assert math.isclose(trajectory[-1].y, 500.0, abs_tol=1e-3)

    # 0-point check: trajectory must NOT be a pure straight line (x == y for all points)
    is_non_linear = any(abs(pt.x - pt.y) > 0.5 for pt in trajectory[5:-5])
    assert is_non_linear, "Mouse trajectory should exhibit non-linear curvature"


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


class MockPage:
    def __init__(self):
        self.mouse = MockMouse()


@pytest.mark.asyncio
async def test_human_mouse_move_and_record():
    mock_page = MockPage()
    mouse = HumanMouse(mock_page)

    trajectory = await mouse.move_and_record(10, 10, 200, 300, steps=25)
    assert len(trajectory) == 25
    assert len(mock_page.mouse.moves) == 25
    assert mouse.current_x == 200
    assert mouse.current_y == 300


@pytest.mark.asyncio
async def test_human_mouse_click():
    mock_page = MockPage()
    mouse = HumanMouse(mock_page)

    await mouse.click(target=(150, 250), steps=10)
    assert mock_page.mouse.downs == 1
    assert mock_page.mouse.ups == 1
    assert mouse.current_x == 150
    assert mouse.current_y == 250


class MockKeyboard:
    def __init__(self):
        self.typed = []

    async def type(self, char: str):
        self.typed.append(char)


@pytest.mark.asyncio
async def test_human_keyboard_typing():
    mock_keyboard = MockKeyboard()
    text = "Termux"

    await HumanKeyboard.type_text(
        mock_keyboard,
        text,
        mean_delay=0.001,
        std_dev=0.0005,
        min_delay=0.0005,
        max_delay=0.002,
    )

    assert "".join(mock_keyboard.typed) == "Termux"
