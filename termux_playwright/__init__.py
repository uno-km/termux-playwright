"""Termux-Playwright: Automated Playwright integration and runtime optimizer for Android Termux (aarch64)."""

from .browser import (
    launch,
    launch_sync,
    get_default_args,
    find_chromium,
    find_nodejs,
    is_termux,
    auto_init,
    DEFAULT_CHROMIUM_ARGS,
)
from .installer import (
    doctor,
    patch_core_bundle,
    run_post_install,
    get_playwright_dir,
)

__version__ = "1.61.1"

__all__ = [
    "launch",
    "launch_sync",
    "get_default_args",
    "find_chromium",
    "find_nodejs",
    "is_termux",
    "auto_init",
    "DEFAULT_CHROMIUM_ARGS",
    "doctor",
    "patch_core_bundle",
    "run_post_install",
    "get_playwright_dir",
    "__version__",
]

# 패키지 임포트 시 Termux 환경이면 자동으로 환경변수 바인딩
auto_init()
