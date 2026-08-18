"""Termux-Playwright: Production-Grade Playwright Integration for Android Termux."""

from .exceptions import (
    TermuxPlaywrightError,
    UnsupportedPlatformError,
    BinaryNotFoundError,
    PatchingError,
    InstallationError,
    ProcessLifecycleError,
)
from .platform import (
    is_termux,
    get_cpu_architecture,
    get_termux_prefix,
    find_chromium_binary,
    find_node_binary,
)
from .browser import (
    launch,
    launch_sync,
    build_chromium_args,
    configure_environment,
    CORE_ANDROID_CHROMIUM_ARGS,
)
from .reaper import (
    ProcessReaper,
    TermuxWakeLock,
)
from .patcher import (
    apply_core_bundle_patch,
    rollback_core_bundle_patch,
    is_core_bundle_patched,
)
from .installer import (
    doctor,
    run_installation_pipeline,
)

__version__ = "1.61.1"

__all__ = [
    # Exceptions
    "TermuxPlaywrightError",
    "UnsupportedPlatformError",
    "BinaryNotFoundError",
    "PatchingError",
    "InstallationError",
    "ProcessLifecycleError",
    # Platform
    "is_termux",
    "get_cpu_architecture",
    "get_termux_prefix",
    "find_chromium_binary",
    "find_node_binary",
    # Browser
    "launch",
    "launch_sync",
    "build_chromium_args",
    "configure_environment",
    "CORE_ANDROID_CHROMIUM_ARGS",
    # Process & WakeLock
    "ProcessReaper",
    "TermuxWakeLock",
    # Patcher
    "apply_core_bundle_patch",
    "rollback_core_bundle_patch",
    "is_core_bundle_patched",
    # Installer & Diagnostics
    "doctor",
    "run_installation_pipeline",
    "__version__",
]
