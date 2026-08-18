"""Termux-Playwright: Hardened, Architecture-Aware Playwright Integration for Android Termux."""

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
)
from .browser import (
    launch,
    launch_sync,
    build_chromium_args,
    configure_environment,
    CORE_ANDROID_CHROMIUM_ARGS,
    LOW_MEMORY_CHROMIUM_ARGS,
    JITLESS_CHROMIUM_ARGS,
)
from .reaper import (
    ProcessReaper,
    TermuxWakeLock,
)
from .patcher import (
    apply_core_bundle_patch,
    rollback_core_bundle_patch,
    is_core_bundle_patched,
    locate_core_bundle_path,
)
from .installer import (
    doctor,
    run_installation_pipeline,
    fetch_pypi_wheel_info,
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
    "StorageExhaustionError",
    # Platform
    "is_termux",
    "get_cpu_architecture",
    "get_termux_prefix",
    "find_chromium_binary",
    "find_node_binary",
    "check_preflight_storage",
    "get_android_sdk_version",
    # Browser
    "launch",
    "launch_sync",
    "build_chromium_args",
    "configure_environment",
    "CORE_ANDROID_CHROMIUM_ARGS",
    "LOW_MEMORY_CHROMIUM_ARGS",
    "JITLESS_CHROMIUM_ARGS",
    # Process & WakeLock
    "ProcessReaper",
    "TermuxWakeLock",
    # Patcher
    "apply_core_bundle_patch",
    "rollback_core_bundle_patch",
    "is_core_bundle_patched",
    "locate_core_bundle_path",
    # Installer & Diagnostics
    "doctor",
    "run_installation_pipeline",
    "fetch_pypi_wheel_info",
    "__version__",
]
