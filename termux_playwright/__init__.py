"""Termux-Playwright: Hardened, Architecture-Aware Playwright Integration for Android Termux.

Next-Gen Autonomous Scraping & Evasion Engine (Python & Node.js Dual Engine).
Includes Kernel ProcessReaper, eMMC Storage Protection, Sub-pixel Canvas 2D LSB Noise,
AudioContext Frequency Deviation, Cubic Bézier Physics, and Dual-Mode Cellular IP Rotator.
"""

from .exceptions import (
    TermuxPlaywrightError,
    UnsupportedPlatformError,
    BinaryNotFoundError,
    PatchingError,
    InstallationError,
    ProcessLifecycleError,
    StorageExhaustionError,
)
from .platform import (
    is_termux,
    get_cpu_architecture,
    get_termux_prefix,
    find_chromium_binary,
    find_node_binary,
    check_preflight_storage,
    get_android_sdk_version,
    get_installed_chromium_version,
)
from .browser import (
    launch,
    launch_sync,
    build_chromium_args,
    configure_environment,
    async_playwright_termux,
    sync_playwright_termux,
    verify_runtime_dependencies,
    block_heavy_resources,
    block_heavy_resources_sync,
    setup_stealth_context,
    setup_stealth_context_sync,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
    STEALTH_CHROMIUM_ARGS,
)
from .stealth import (
    generate_stealth_script,
    CanvasNoiseInjector,
    AudioNoiseInjector,
    StealthEngine,
)
from .physics import (
    Point,
    CubicBezierTrajectory,
    HumanMouse,
    HumanKeyboard,
)
from .mobile import (
    RotationMode,
    CellularIpRotator,
)
from .waf import (
    WafChallengeType,
    TurnstileEvaluator,
)
from .reaper import (
    ProcessReaper,
    TermuxWakeLock,
    cli_reap_orphans,
)
from .patcher import (
    apply_core_bundle_patch,
    rollback_core_bundle_patch,
    is_core_bundle_patched,
    locate_core_bundle_path,
    cleanup_backup,
    cli_patch_core_bundle,
)
from .installer import (
    doctor,
    run_installation_pipeline,
    fetch_pypi_wheel_info,
)

__version__ = "1.80.0"

__all__ = [
    # Exceptions
    "TermuxPlaywrightError",
    "UnsupportedPlatformError",
    "BinaryNotFoundError",
    "PatchingError",
    "InstallationError",
    "ProcessLifecycleError",
    "StorageExhaustionError",
    # Platform
    "is_termux",
    "get_cpu_architecture",
    "get_termux_prefix",
    "find_chromium_binary",
    "find_node_binary",
    "check_preflight_storage",
    "get_android_sdk_version",
    "get_installed_chromium_version",
    # Browser
    "launch",
    "launch_sync",
    "build_chromium_args",
    "configure_environment",
    "async_playwright_termux",
    "sync_playwright_termux",
    "verify_runtime_dependencies",
    "block_heavy_resources",
    "block_heavy_resources_sync",
    "setup_stealth_context",
    "setup_stealth_context_sync",
    "CORE_ANDROID_CHROMIUM_ARGS",
    "LOW_MEMORY_CHROMIUM_ARGS",
    "STEALTH_CHROMIUM_ARGS",
    # Stealth
    "generate_stealth_script",
    "CanvasNoiseInjector",
    "AudioNoiseInjector",
    "StealthEngine",
    # Physics
    "Point",
    "CubicBezierTrajectory",
    "HumanMouse",
    "HumanKeyboard",
    # Mobile
    "RotationMode",
    "CellularIpRotator",
    # WAF
    "WafChallengeType",
    "TurnstileEvaluator",
    # Process & WakeLock
    "ProcessReaper",
    "TermuxWakeLock",
    "cli_reap_orphans",
    # Patcher
    "apply_core_bundle_patch",
    "rollback_core_bundle_patch",
    "is_core_bundle_patched",
    "locate_core_bundle_path",
    "cleanup_backup",
    "cli_patch_core_bundle",
    # Installer & Diagnostics
    "doctor",
    "run_installation_pipeline",
    "fetch_pypi_wheel_info",
    "__version__",
]

# Auto-configure process environment safely (idempotent, no-op outside Termux)
configure_environment(strict=False)
