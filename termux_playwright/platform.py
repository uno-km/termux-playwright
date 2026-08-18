"""Platform and environment detection engine.

Provides deterministic inspection of CPU architecture, Termux prefix paths,
and binary availability without mutating global process state.
"""

import os
import platform
import shutil
from typing import Dict
from .exceptions import UnsupportedPlatformError, BinaryNotFoundError

# Supported target architectures mapped to manylinux wheel tags
SUPPORTED_ARCHITECTURES: Dict[str, str] = {
    "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "arm64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "armv8l": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "x86_64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
    "amd64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
}

def is_termux() -> bool:
    """Check if current execution is happening inside Android Termux environment."""
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or os.path.exists("/data/data/com.termux")

def get_termux_prefix() -> str:
    """Return the absolute path to Termux base prefix directory."""
    if "PREFIX" in os.environ:
        return os.environ["PREFIX"]
    default_prefix = "/data/data/com.termux/files/usr"
    if os.path.isdir(default_prefix):
        return default_prefix
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

def find_chromium_binary() -> str:
    """Locate Chromium executable.
    
    Raises:
        BinaryNotFoundError: When no valid Chromium binary is located on system.
    """
    # 1. Environment variable override
    env_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # 2. PATH resolution
    candidates = ["chromium-browser", "chromium", "google-chrome", "chrome"]
    for name in candidates:
        found = shutil.which(name)
        if found and os.access(found, os.X_OK):
            return found

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
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

    raise BinaryNotFoundError(
        "Chromium executable not found. "
        "Inside Termux, install it via: 'pkg install chromium'. "
        "Or set PLAYWRIGHT_CHROMIUM_PATH to a valid executable."
    )

def find_node_binary() -> str:
    """Locate Node.js executable.
    
    Raises:
        BinaryNotFoundError: When no valid Node.js binary is located on system.
    """
    env_path = os.environ.get("PLAYWRIGHT_NODEJS_PATH")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    found = shutil.which("node")
    if found and os.access(found, os.X_OK):
        return found

    prefix = get_termux_prefix()
    if prefix:
        termux_node = os.path.join(prefix, "bin", "node")
        if os.path.isfile(termux_node) and os.access(termux_node, os.X_OK):
            return termux_node

    raise BinaryNotFoundError(
        "Node.js executable not found. "
        "Inside Termux, install it via: 'pkg install nodejs'. "
        "Or set PLAYWRIGHT_NODEJS_PATH to a valid executable."
    )
