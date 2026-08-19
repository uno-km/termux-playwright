"""Platform, architecture, and storage inspection engine for Termux Playwright.

Provides symlink-safe binary resolution, Android SDK/W^X policy inspection,
and pre-flight storage threshold checks without global mutation.
"""

import glob
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from typing import Dict, Optional, Tuple, List
from .exceptions import UnsupportedPlatformError, BinaryNotFoundError, StorageExhaustionError

logger = logging.getLogger(__name__)

SUPPORTED_ARCHITECTURES: Dict[str, str] = {
    "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "arm64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "armv8l": "manylinux_2_17_aarch64.manylinux2014_aarch64",
    "x86_64": "manylinux1_x86_64",
    "amd64": "manylinux1_x86_64",
}

KNOWN_TERMUX_PREFIXES: Tuple[str, ...] = (
    "com.termux",
    "com.termux.float",
    "com.termux.nix",
    "io.neoterm",
)

MINIMUM_REQUIRED_STORAGE_MB: int = int(os.environ.get("TERMUX_PLAYWRIGHT_MIN_STORAGE_MB", "150"))
ANDROID_10_SDK_VERSION: int = 29

def is_termux() -> bool:
    """Check if current execution is happening inside Android Termux or compatible environment.
    
    Verifies process identity via environment variables, running python executable path,
    and actual filesystem access rights, preventing false-positive hijacking in other Android Python apps
    (such as Pydroid 3, QPython, Chaquopy).
    """
    # Tier 1: Explicit Termux environment variables
    prefix = os.environ.get("PREFIX", "")
    if prefix and any(sig in prefix for sig in KNOWN_TERMUX_PREFIXES):
        return True
    if "TERMUX_VERSION" in os.environ:
        return True
    if "TERMUX_APP_PID" in os.environ or "TERMUX_MAIN_PACKAGE" in os.environ:
        return True

    # Tier 2: Running interpreter / sys.prefix lineage
    exec_path = sys.executable or ""
    sys_prefix = getattr(sys, "prefix", "") or ""
    if any(sig in exec_path for sig in KNOWN_TERMUX_PREFIXES) or any(sig in sys_prefix for sig in KNOWN_TERMUX_PREFIXES):
        return True

    # Tier 3: Verify real access rights on Termux prefix directory (never blindly trust os.path.exists)
    for pkg in KNOWN_TERMUX_PREFIXES:
        candidate_prefix = f"/data/data/{pkg}/files/usr"
        if os.path.isdir(candidate_prefix) and os.access(candidate_prefix, os.R_OK | os.X_OK):
            # Also ensure we are running on Android before claiming Termux
            if hasattr(sys, "getandroidapilevel") or "ANDROID_ROOT" in os.environ or os.path.exists("/system/bin/getprop"):
                if os.access(os.path.join(candidate_prefix, "bin"), os.R_OK | os.X_OK):
                    return True

    return False

def get_termux_prefix() -> str:
    """Return the absolute path to Termux base prefix directory."""
    if "PREFIX" in os.environ:
        return os.path.realpath(os.environ["PREFIX"])
    
    # Check running interpreter's prefix
    sys_prefix = getattr(sys, "prefix", "")
    if sys_prefix and any(sig in sys_prefix for sig in KNOWN_TERMUX_PREFIXES):
        return os.path.realpath(sys_prefix)

    for pkg in KNOWN_TERMUX_PREFIXES:
        default_prefix = f"/data/data/{pkg}/files/usr"
        if os.path.isdir(default_prefix) and os.access(default_prefix, os.R_OK | os.X_OK):
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
    """Inspect Android SDK version via multi-tier fallback (sys.getandroidapilevel -> getprop -> build.prop).
    
    Returns:
        int: Android API level (e.g. 26 for Android 8.0, 29 for Android 10).
             Returns 0 if not running on Android.
             If inside Termux and inspection fails, returns conservative
             safe default (SDK 29) to enforce W^X memory protection and prevent crash.
    """
    if not is_termux():
        return 0
        
    # Tier 1: Python standard C-runtime Android API level (Most reliable if compiled for Android)
    if hasattr(sys, "getandroidapilevel"):
        try:
            lvl = int(sys.getandroidapilevel())
            if lvl > 0:
                return lvl
        except Exception as e:
            logger.debug("sys.getandroidapilevel failed: %s", e)

    # Tier 2: Android getprop command line tool
    getprop = shutil.which("getprop")
    if getprop:
        try:
            res = subprocess.run(
                [getprop, "ro.build.version.sdk"],
                capture_output=True, text=True, timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception as e:
            logger.debug("getprop check failed: %s", e)

    # Tier 3: Direct /system/build.prop parsing fallback
    build_prop_candidates = ["/system/build.prop", "/default.prop", "/vendor/build.prop"]
    for prop_file in build_prop_candidates:
        if os.path.isfile(prop_file):
            try:
                with open(prop_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("ro.build.version.sdk="):
                            val = line.split("=", 1)[1].strip()
                            if val.isdigit():
                                return int(val)
            except Exception as e:
                logger.debug("build.prop check failed on %s: %s", prop_file, e)
            
    # Conservative safe default for Android Termux: Enforce W^X policy compliance
    logger.info(
        "Defaulting to Android SDK %d for Termux to guarantee W^X memory policy safety.",
        ANDROID_10_SDK_VERSION,
    )
    return ANDROID_10_SDK_VERSION

def check_preflight_storage(target_dir: Optional[str] = None, min_mb: Optional[int] = None) -> int:
    """Verify that the target directory has sufficient disk space.
    
    Args:
        target_dir: Directory path to inspect disk space.
        min_mb: Minimum required space in megabytes. Defaults to MINIMUM_REQUIRED_STORAGE_MB.
        
    Returns:
        int: Available storage in megabytes.
    Raises:
        StorageExhaustionError: If available space is below required threshold.
    """
    required_mb = min_mb if min_mb is not None else MINIMUM_REQUIRED_STORAGE_MB
    check_path = target_dir or os.environ.get("TMPDIR") or (os.path.join(get_termux_prefix(), "tmp") if get_termux_prefix() else tempfile.gettempdir())
    
    try:
        fallback_path = get_termux_prefix() or os.path.expanduser("~") or "."
        actual_path = check_path if os.path.exists(check_path) else (fallback_path if os.path.exists(fallback_path) else ".")
        usage = shutil.disk_usage(actual_path)
        free_mb = usage.free // (1024 * 1024)
        if free_mb < required_mb:
            raise StorageExhaustionError(
                f"Insufficient disk space in '{actual_path}': {free_mb}MB available, "
                f"minimum required: {required_mb}MB. "
                f"Free up storage via 'pkg clean' / 'rm -rf $TMPDIR/*', or "
                f"override via TERMUX_PLAYWRIGHT_MIN_STORAGE_MB environment variable."
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

    # 3. Windows standard desktop installations fallback (dynamic wildcard search)
    if sys.platform == "win32":
        for base in filter(None, [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")]):
            for pattern in (r"*\Chrome\Application\chrome.exe", r"*\Edge\Application\msedge.exe", r"*\Chromium\Application\chrome.exe"):
                matches = glob.glob(os.path.join(base, pattern))
                if matches and os.path.isfile(matches[0]):
                    return os.path.realpath(matches[0])

    # 4. Termux prefix candidate inspection across all known terminal forks
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

_cached_chromium_stat: Optional[Tuple[str, float, str, str]] = None

def get_installed_chromium_version() -> Tuple[str, str]:
    """Inspect and extract installed Chromium full version and major version with stat-based cache invalidation.
    
    Checks binary modification timestamp (mtime). If binary was upgraded on disk (e.g. pkg upgrade chromium),
    automatically refreshes version extraction to prevent fingerprint mismatch.
    
    Returns:
        Tuple[str, str]: (full_version, major_version)
                         e.g. ("130.0.6723.58", "130")
                         Defaults to ("130.0.0.0", "130") on failure/unavailable.
    """
    global _cached_chromium_stat
    default_full = "130.0.0.0"
    default_major = "130"
    
    try:
        chrome_bin = find_chromium_binary()
        stat_res = os.stat(chrome_bin)
        curr_mtime = stat_res.st_mtime

        if _cached_chromium_stat is not None:
            cached_bin, cached_mtime, cached_full, cached_major = _cached_chromium_stat
            if cached_bin == chrome_bin and cached_mtime == curr_mtime:
                return cached_full, cached_major

        res = subprocess.run([chrome_bin, "--version"], capture_output=True, timeout=3, check=False)
        if res.returncode == 0 and res.stdout:
            stdout_str = res.stdout.decode("utf-8", errors="ignore")
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", stdout_str)
            if match:
                full_v = match.group(1)
                major_v = full_v.split(".")[0]
                _cached_chromium_stat = (chrome_bin, curr_mtime, full_v, major_v)
                return full_v, major_v
    except Exception as e:
        logger.debug("Failed to detect installed Chromium version: %s", e)

    return default_full, default_major
