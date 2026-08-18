"""Platform, architecture, and storage inspection engine for Termux Playwright.

Provides symlink-safe binary resolution, Android SDK/W^X policy inspection,
and pre-flight storage threshold checks without global mutation.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from typing import Dict, Optional
from .exceptions import UnsupportedPlatformError, BinaryNotFoundError, StorageExhaustionError

SUPPORTED_ARCHITECTURES: Dict[str, str] = {
    "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "arm64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "armv8l": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "x86_64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
    "amd64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
}

MINIMUM_REQUIRED_STORAGE_MB: int = 50

def is_termux() -> bool:
    """Check if current execution is happening inside Android Termux environment."""
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or os.path.exists("/data/data/com.termux")

def get_termux_prefix() -> str:
    """Return the absolute path to Termux base prefix directory."""
    if "PREFIX" in os.environ:
        return os.path.realpath(os.environ["PREFIX"])
    default_prefix = "/data/data/com.termux/files/usr"
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
    """Inspect Android SDK version via getprop. Returns 0 if not on Android."""
    if not is_termux():
        return 0
    getprop = shutil.which("getprop")
    if getprop:
        try:
            res = subprocess.run([getprop, "ro.build.version.sdk"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
    return 0

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
    except (OSError, ValueError) as e:
        if isinstance(e, StorageExhaustionError):
            raise
        return 999  # Non-blocking if storage inspection fails on unsupported virtual mount

def find_chromium_binary() -> str:
    """Locate Chromium executable with symlink resolution.
    
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

    # 3. Termux prefix candidate inspection
    prefix = get_termux_prefix()
    if prefix:
        termux_paths = [
            os.path.join(prefix, "bin", "chromium-browser"),
            os.path.join(prefix, "bin", "chromium"),
            "/data/data/com.termux/files/usr/bin/chromium-browser",
            "/data/data/com.termux/files/usr/bin/chromium",
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
    """Locate Node.js executable with symlink resolution.
    
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

    prefix = get_termux_prefix()
    if prefix:
        termux_node = os.path.join(prefix, "bin", "node")
        real_p = os.path.realpath(termux_node)
        if os.path.isfile(real_p) and os.access(real_p, os.X_OK):
            return real_p

    raise BinaryNotFoundError(
        "Node.js executable not found. "
        "Inside Termux, install it via: 'pkg install nodejs'. "
        "Or set PLAYWRIGHT_NODEJS_PATH to a valid executable."
    )
