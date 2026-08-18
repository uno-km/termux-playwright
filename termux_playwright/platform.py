"""Platform, architecture, and storage inspection engine for Termux Playwright.

Provides symlink-safe binary resolution, Android SDK/W^X policy inspection,
and pre-flight storage threshold checks without global mutation.
"""

import logging
import os
import platform
import shutil
import subprocess
import tempfile
from typing import Dict, Optional, Tuple, List
from .exceptions import UnsupportedPlatformError, BinaryNotFoundError, StorageExhaustionError

logger = logging.getLogger(__name__)

SUPPORTED_ARCHITECTURES: Dict[str, str] = {
    "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "arm64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "armv8l": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "x86_64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
    "amd64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
}

KNOWN_TERMUX_PREFIXES: Tuple[str, ...] = (
    "com.termux",
    "com.termux.float",
    "com.termux.nix",
    "io.neoterm",
)

MINIMUM_REQUIRED_STORAGE_MB: int = 50
ANDROID_10_SDK_VERSION: int = 29

def is_termux() -> bool:
    """Check if current execution is happening inside Android Termux or compatible environment."""
    prefix = os.environ.get("PREFIX", "")
    if any(sig in prefix for sig in KNOWN_TERMUX_PREFIXES):
        return True
    if "TERMUX_VERSION" in os.environ:
        return True
    for pkg in KNOWN_TERMUX_PREFIXES:
        if os.path.exists(f"/data/data/{pkg}"):
            return True
    return False

def get_termux_prefix() -> str:
    """Return the absolute path to Termux base prefix directory."""
    if "PREFIX" in os.environ:
        return os.path.realpath(os.environ["PREFIX"])
    for pkg in KNOWN_TERMUX_PREFIXES:
        default_prefix = f"/data/data/{pkg}/files/usr"
        if os.path.isdir(default_prefix):
            return os.path.realpath(default_prefix)
    return ""

def get_cpu_architecture() -> str:
    """Normalize and validate machine CPU architecture.
    
    Raises:
        UnsupportedPlatformError: If running on a 32-bit ARM (armv7l) or unsupported arch.
    """
    raw_arch = platform.machine().lower()
    
    if raw_arch in ["aarch64", "arm64", "armv8l"]:
        return "aarch64"
    elif raw_arch in ["x86_64", "amd64"]:
        return "x86_64"
    elif raw_arch in ["armv7l", "arm", "armv7", "i686", "i386"]:
        raise UnsupportedPlatformError(
            f"32-bit architecture detected: '{raw_arch}'. "
            f"Playwright upstream only provides 64-bit binaries (aarch64, x86_64). "
            f"Termux on 32-bit Android devices is not supported."
        )
    else:
        raise UnsupportedPlatformError(
            f"Unsupported CPU architecture: '{raw_arch}'. "
            f"Supported architectures: {list(SUPPORTED_ARCHITECTURES.keys())}"
        )

def get_wheel_tag_for_arch(arch: str) -> str:
    """Return the manylinux wheel tag for the detected architecture."""
    if arch not in SUPPORTED_ARCHITECTURES:
        raise UnsupportedPlatformError(
            f"Unsupported CPU architecture: '{arch}'. "
            f"termux-playwright supports: {list(SUPPORTED_ARCHITECTURES.keys())}"
        )
    return SUPPORTED_ARCHITECTURES[arch]

def get_android_sdk_version() -> int:
    """Inspect Android SDK version via getprop.
    
    Returns:
        int: Android API level (e.g., 29 for Android 10).
             Returns 0 if not running on Android.
             If inside Termux and getprop inspection fails, returns conservative
             safe default (SDK 29) to enforce W^X memory protection and prevent crash.
    """
    if not is_termux():
        return 0
        
    getprop = shutil.which("getprop")
    if getprop:
        try:
            res = subprocess.run(
                [getprop, "ro.build.version.sdk"],
                capture_output=True, text=True, timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
            logger.warning(
                "getprop returned non-numeric SDK version: rc=%d, stdout=%r",
                res.returncode, res.stdout.strip(),
            )
        except Exception as e:
            logger.warning("Failed to query Android SDK version via getprop: %s", e)
            
    # Conservative safe default for Android Termux: Enforce W^X policy compliance
    logger.info(
        "Defaulting to Android SDK %d for Termux to guarantee W^X memory policy safety.",
        ANDROID_10_SDK_VERSION,
    )
    return ANDROID_10_SDK_VERSION

def check_preflight_storage(target_dir: Optional[str] = None) -> int:
    """Verify that the target directory has sufficient disk space.
    
    Returns:
        int: Available storage in megabytes.
    Raises:
        StorageExhaustionError: If available space is below MINIMUM_REQUIRED_STORAGE_MB.
    """
    check_path = target_dir or os.environ.get("TMPDIR") or (os.path.join(get_termux_prefix(), "tmp") if get_termux_prefix() else tempfile.gettempdir())
    
    try:
        usage = shutil.disk_usage(check_path if os.path.exists(check_path) else "/")
        free_mb = usage.free // (1024 * 1024)
        if free_mb < MINIMUM_REQUIRED_STORAGE_MB:
            raise StorageExhaustionError(
                f"Insufficient disk space in '{check_path}': {free_mb}MB available, "
                f"minimum required: {MINIMUM_REQUIRED_STORAGE_MB}MB."
            )
        return free_mb
    except StorageExhaustionError:
        raise
    except (OSError, ValueError) as e:
        raise StorageExhaustionError(
            f"Cannot verify available disk space at '{check_path}': {e}. "
            f"Ensure the filesystem is accessible, or pass a valid target_dir."
        ) from e

def _get_candidate_prefix_paths() -> List[str]:
    """Return all possible prefix root directories for binary discovery."""
    prefixes: List[str] = []
    active_prefix = get_termux_prefix()
    if active_prefix and active_prefix not in prefixes:
        prefixes.append(active_prefix)
    for pkg in KNOWN_TERMUX_PREFIXES:
        p = os.path.realpath(f"/data/data/{pkg}/files/usr")
        if p not in prefixes:
            prefixes.append(p)
    return prefixes

def find_chromium_binary() -> str:
    """Locate Chromium executable with symlink resolution across standard and Termux paths.
    
    Raises:
        BinaryNotFoundError: When no valid Chromium binary is located on system.
    """
    # 1. Environment variable override
    env_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
    if env_path:
        real_path = os.path.realpath(env_path)
        if os.path.isfile(real_path) and os.access(real_path, os.X_OK):
            return real_path

    # 2. PATH resolution
    candidates = ["chromium-browser", "chromium", "google-chrome", "chrome"]
    for name in candidates:
        found = shutil.which(name)
        if found:
            real_found = os.path.realpath(found)
            if os.path.isfile(real_found) and os.access(real_found, os.X_OK):
                return real_found

    # 3. Termux prefix candidate inspection across all known terminal forks
    for prefix in _get_candidate_prefix_paths():
        termux_paths = [
            os.path.join(prefix, "bin", "chromium-browser"),
            os.path.join(prefix, "bin", "chromium"),
        ]
        for path in termux_paths:
            real_p = os.path.realpath(path)
            if os.path.isfile(real_p) and os.access(real_p, os.X_OK):
                return real_p

    raise BinaryNotFoundError(
        "Chromium executable not found. "
        "Inside Termux, install it via: 'pkg install chromium'. "
        "Or set PLAYWRIGHT_CHROMIUM_PATH to a valid executable."
    )

def find_node_binary() -> str:
    """Locate Node.js executable with symlink resolution across standard and Termux paths.
    
    Raises:
        BinaryNotFoundError: When no valid Node.js binary is located on system.
    """
    env_path = os.environ.get("PLAYWRIGHT_NODEJS_PATH")
    if env_path:
        real_path = os.path.realpath(env_path)
        if os.path.isfile(real_path) and os.access(real_path, os.X_OK):
            return real_path

    found = shutil.which("node")
    if found:
        real_found = os.path.realpath(found)
        if os.path.isfile(real_found) and os.access(real_found, os.X_OK):
            return real_found

    for prefix in _get_candidate_prefix_paths():
        termux_node = os.path.join(prefix, "bin", "node")
        real_p = os.path.realpath(termux_node)
        if os.path.isfile(real_p) and os.access(real_p, os.X_OK):
            return real_p

    raise BinaryNotFoundError(
        "Node.js executable not found. "
        "Inside Termux, install it via: 'pkg install nodejs'. "
        "Or set PLAYWRIGHT_NODEJS_PATH to a valid executable."
    )
