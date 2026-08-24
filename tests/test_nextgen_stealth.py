import pytest
from termux_playwright.stealth import (
    generate_stealth_script,
    CanvasNoiseInjector,
    AudioNoiseInjector,
    StealthEngine,
)


def test_generate_stealth_script_defaults():
    script = generate_stealth_script()
    assert "navigator.webdriver" in script
    assert "window.chrome" in script
    assert "Sub-pixel Canvas 2D LSB Noise Injector" in script
    assert "AudioContext Frequency Deviation Noise Injector" in script
    assert "WebGL context proxy" in script


def test_generate_stealth_script_granular_toggles():
    # Disable canvas and audio noise
    script_disabled = generate_stealth_script(
        enable_canvas_noise=False,
        enable_audio_noise=False,
        enable_webgl_mask=False,
    )
    assert "Sub-pixel Canvas 2D LSB Noise Injector" not in script_disabled
    assert "AudioContext Frequency Deviation Noise Injector" not in script_disabled
    assert "WebGL context proxy" not in script_disabled
    assert "window.chrome" in script_disabled

    # Canvas only
    script_canvas_only = generate_stealth_script(
        enable_canvas_noise=True,
        enable_audio_noise=False,
        enable_webgl_mask=False,
        enable_webdriver_mask=False,
        enable_chrome_mock=False,
        enable_permissions_mock=False,
        enable_plugins_mock=False,
        canvas_noise_seed=42,
    )
    assert "Sub-pixel Canvas 2D LSB Noise Injector" in script_canvas_only
    assert "const SEED_OFFSET = 42;" in script_canvas_only
    assert "navigator.webdriver" not in script_canvas_only


def test_stealth_engine_build_script():
    script = StealthEngine.build_script(enable_audio_noise=True, canvas_noise_seed=99)
    assert "SEED_OFFSET = 99" in script
    assert "AudioBuffer" in script


class MockPage:
    def __init__(self):
        self.injected_scripts = []

    async def add_init_script(self, script: str):
        self.injected_scripts.append(script)

    def add_init_script_sync(self, script: str):
        self.injected_scripts.append(script)


@pytest.mark.asyncio
async def test_canvas_noise_injector_async():
    mock_page = MockPage()
    await CanvasNoiseInjector.inject(mock_page, seed=123)
    assert len(mock_page.injected_scripts) == 1
    assert "SEED_OFFSET = 123" in mock_page.injected_scripts[0]
    assert "CanvasRenderingContext2D" in mock_page.injected_scripts[0]


@pytest.mark.asyncio
async def test_audio_noise_injector_async():
    mock_page = MockPage()
    await AudioNoiseInjector.inject(mock_page)
    assert len(mock_page.injected_scripts) == 1
    assert "AudioBuffer" in mock_page.injected_scripts[0]
    assert "AnalyserNode" in mock_page.injected_scripts[0]
