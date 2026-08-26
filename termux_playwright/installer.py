"""Automated installation and dependency resolution engine for Termux Playwright.

Executes verifiable, fail-safe installation of native system packages,
aarch64/x86_64 bypass wheels, and JS platform patches with exponential backoff and timeout enforcement.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import tempfile
import urllib.request
from typing import Tuple, Optional, List

from .exceptions import InstallationError, UnsupportedPlatformError, PatchingError
from .platform import (
    is_termux,
    get_cpu_architecture,
    get_wheel_tag_for_arch,
    find_chromium_binary,
    find_node_binary,
    check_preflight_storage,
)
from .patcher import apply_core_bundle_patch, is_core_bundle_patched, locate_playwright_package_dir, cleanup_backup

DEFAULT_PLAYWRIGHT_VERSION: str = "1.48.0"
VERIFIED_COMPATIBLE_VERSIONS: Tuple[str, ...] = ("1.50.0", "1.49.0", "1.48.0", "1.47.0", "1.40.0")
SUBPROCESS_TIMEOUT_SECONDS: int = 300
MAX_NETWORK_RETRIES: int = 3

def resolve_latest_compatible_version() -> str:
    """Query PyPI API to discover the latest compatible Playwright release."""
    api_url = "https://pypi.org/pypi/playwright/json"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "termux-playwright-installer"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                info = data.get("info", {})
                latest = info.get("version")
                if latest:
                    return latest
    except Exception as e:
        import warnings
        warnings.warn(
            f"Could not query PyPI for latest Playwright version ({e}). "
            f"Using known-compatible version {DEFAULT_PLAYWRIGHT_VERSION}. "
            f"To override, pass an explicit version parameter.",
            RuntimeWarning,
            stacklevel=2,
        )
    return DEFAULT_PLAYWRIGHT_VERSION

def fetch_pypi_wheel_info(version: Optional[str] = None) -> Tuple[str, str, str]:
    """Query PyPI JSON API for the exact matching architecture wheel URL and filename.
    
    Args:
        version: Specific version string. If None, defaults to known-good verified
                 LTS release (DEFAULT_PLAYWRIGHT_VERSION). If 'latest', dynamically
                 queries the bleeding-edge release from PyPI.
    """
    arch = get_cpu_architecture()
    tag = get_wheel_tag_for_arch(arch)
    if version == "latest":
        target_version = resolve_latest_compatible_version()
    else:
        target_version = version or DEFAULT_PLAYWRIGHT_VERSION
    api_url = f"https://pypi.org/pypi/playwright/{target_version}/json"

    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "termux-playwright-installer"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    raise InstallationError(f"PyPI API returned HTTP {resp.status}")
                data = json.loads(resp.read().decode("utf-8"))
                
                urls = data.get("urls", [])
                for item in urls:
                    filename = item.get("filename", "")
                    if tag in filename and filename.endswith(".whl"):
                        download_url = item.get("url")
                        if download_url:
                            return download_url, filename, target_version

            raise InstallationError(f"No suitable wheel with tag '{tag}' found on PyPI for version {target_version}")

        except Exception as e:
            if attempt == MAX_NETWORK_RETRIES:
                raise InstallationError(f"Failed to resolve wheel from PyPI after {MAX_NETWORK_RETRIES} attempts: {e}") from e
            time.sleep(2 ** attempt)

    raise InstallationError("Exhausted retries resolving Playwright wheel.")

REQUIRED_TERMUX_SYSTEM_PACKAGES: List[str] = [
    "x11-repo",
    "chromium",
    "nodejs",
    "python-greenlet",
    "procps",
    "termux-api",
]

OPTIONAL_TERMUX_BUILD_PACKAGES: List[str] = [
    "clang",
    "python",
    "make",
]

def _format_error_report(phase: str, reason: str, details: Optional[str] = None, remedies: Optional[List[str]] = None) -> str:
    """Construct a clean, structured, highly readable English error report."""
    lines = [
        "",
        "=" * 70,
        f"[-] INSTALLATION FAILED AT: {phase.upper()}",
        "=" * 70,
        f"Error Description: {reason}",
    ]
    if details:
        lines.append(f"\nUnderlying System Output:\n{details.strip()}")
    if remedies:
        lines.append("\nRecommended Actions to Resolve:")
        for idx, remedy in enumerate(remedies, 1):
            lines.append(f"  {idx}. {remedy}")
    lines.append("=" * 70)
    return "\n".join(lines)

def install_system_dependencies(include_build_tools: bool = False) -> None:
    """Install native Termux Chromium, Node.js, and pre-compiled Python C-extensions via pkg with retry.
    
    Implements Two-Phase Repository Provisioning:
    1. First bootstraps 'x11-repo' and synchronizes package indexes so that 'chromium' becomes resolvable.
    2. Then provisions native Chromium, Node.js, and python-greenlet without pulling in 1.2GB Clang/LLVM.
    
    Args:
        include_build_tools: If True, also installs clang and make (~1.2GB toolchain).
            Defaults to False for lean storage footprint and fast installation.
    """
    pkg_bin = shutil.which("pkg")
    if not pkg_bin:
        msg = _format_error_report(
            phase="Native System Package Provisioning",
            reason="Termux 'pkg' package manager was not found in system PATH.",
            remedies=[
                "Ensure you are running inside a standard Termux environment on Android.",
                "If running in a custom proot/chroot, verify your PATH contains '/data/data/com.termux/files/usr/bin'."
            ]
        )
        raise InstallationError(msg)

    # -------------------------------------------------------------------------
    # Phase 1: Bootstrap X11 Repository & Synchronize APT Package Index
    # -------------------------------------------------------------------------
    print("[*] [Phase 1/2] Bootstrapping 'x11-repo' and synchronizing Termux package index...")
    x11_cmd = [pkg_bin, "install", "-y", "x11-repo"]
    try:
        subprocess.run(x11_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        # Update package lists so APT discovers chromium inside the x11 repository
        update_cmd = [pkg_bin, "update", "-y"]
        subprocess.run(update_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
    except Exception as e:
        logger.warning("Phase 1 x11-repo bootstrap encountered warning (will proceed to main install): %s", e)

    # -------------------------------------------------------------------------
    # Phase 2: Provision Native System Packages (Chromium, Node.js, Greenlet, etc.)
    # -------------------------------------------------------------------------
    packages = [pkg for pkg in REQUIRED_TERMUX_SYSTEM_PACKAGES if pkg != "x11-repo"]
    if include_build_tools:
        packages.extend(OPTIONAL_TERMUX_BUILD_PACKAGES)

    cmd = [pkg_bin, "install", "-y"] + packages
    print(f"[*] [Phase 2/2] Executing system package installation: {' '.join(cmd)}")
    
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            if res.returncode == 0:
                print("[+] System package installation succeeded.")
                return

            # Tier 2: Attempt apt-get --fix-missing recovery if available
            apt_bin = shutil.which("apt-get") or shutil.which("apt")
            if apt_bin:
                print(f"[!] 'pkg install' encountered errors. Attempting Tier 2 recovery with '{apt_bin} install --fix-missing'...")
                fix_cmd = [apt_bin, "install", "-y", "--fix-missing"] + packages
                fix_res = subprocess.run(fix_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
                if fix_res.returncode == 0:
                    print("[+] Tier 2 package recovery succeeded.")
                    return

            if attempt == MAX_NETWORK_RETRIES:
                raw_out = (res.stderr or res.stdout or "No output captured").strip()
                print("\n" + "=" * 65)
                print(" [!] CRITICAL: Termux Package Mirror Error")
                print(" 👉 Run 'termux-change-repo' in Termux to switch to a healthy mirror")
                print("    (e.g., choose 'Mirrors by Tsinghua' or 'Mirrors by BFSU').")
                print(" 👉 Then run: pkg update -y && termux-playwright-install")
                print("=" * 65 + "\n")
                msg = _format_error_report(
                    phase="Native System Package Provisioning (pkg install)",
                    reason=f"'pkg install' exited with non-zero status code {res.returncode} after {MAX_NETWORK_RETRIES} attempts (possible mirror 404 or network outage).",
                    details=raw_out,
                    remedies=[
                        "Switch package mirror: Run 'termux-change-repo' and pick a fast mirror",
                        "Update repository index: Run 'pkg update -y'",
                        f"Attempt manual install: pkg install -y x11-repo && pkg update -y && pkg install -y {' '.join(packages)}",
                        "Ensure your device has active internet access."
                    ]
                )
                raise InstallationError(msg)
            print(f"[!] pkg install failed (attempt {attempt}/{MAX_NETWORK_RETRIES}). Retrying in {2 ** attempt}s...")
            time.sleep(2 ** attempt)
        except subprocess.TimeoutExpired as e:
            if attempt == MAX_NETWORK_RETRIES:
                msg = _format_error_report(
                    phase="Native System Package Provisioning (pkg install)",
                    reason=f"Subprocess timed out after {SUBPROCESS_TIMEOUT_SECONDS} seconds.",
                    remedies=[
                        "Check your network latency or mirror download speed.",
                        "Run 'termux-change-repo' to select a faster geographic mirror."
                    ]
                )
                raise InstallationError(msg) from e
                raise InstallationError(msg) from e

def install_playwright_wheel(version: Optional[str] = None) -> None:
    """Download architecture wheel with retry, rename to bypass platform checks, and install."""
    try:
        download_url, filename, resolved_version = fetch_pypi_wheel_info(version)
    except Exception as e:
        msg = _format_error_report(
            phase="Playwright Wheel Resolution from PyPI",
            reason=f"Failed to locate matching architecture wheel on PyPI: {e}",
            remedies=[
                "Verify device has internet access to https://pypi.org.",
                "Specify a known LTS version explicitly: termux-playwright-install (or set version='1.61.0')."
            ]
        )
        raise InstallationError(msg) from e
    
    with tempfile.TemporaryDirectory() as temp_dir:
        download_target = os.path.join(temp_dir, filename)
        renamed_target = os.path.join(temp_dir, f"playwright-{resolved_version}-py3-none-any.whl")

        print(f"[*] Downloading Playwright {resolved_version} wheel from: {download_url}")
        for attempt in range(1, MAX_NETWORK_RETRIES + 1):
            try:
                req = urllib.request.Request(download_url, headers={"User-Agent": "termux-playwright-installer"})
                with urllib.request.urlopen(req, timeout=30) as resp, open(download_target, "wb") as out_f:
                    shutil.copyfileobj(resp, out_f, length=64 * 1024)
                break
            except Exception as e:
                if attempt == MAX_NETWORK_RETRIES:
                    msg = _format_error_report(
                        phase="Playwright Wheel Download",
                        reason=f"Network transfer failed after {MAX_NETWORK_RETRIES} attempts: {e}",
                        remedies=[
                            "Check network stability and DNS configuration.",
                            f"Test downloading manually via curl: curl -LO {download_url}"
                        ]
                    )
                    raise InstallationError(msg) from e
                time.sleep(2 ** attempt)

        # Atomic rename to any platform
        os.replace(download_target, renamed_target)

        pip_cmd = [
            sys.executable, "-m", "pip", "install",
            renamed_target,
            "--force-reinstall",
            "--no-deps",
            "--no-cache-dir",
            "-q"
        ]
        print(f"[*] Installing modified wheel into Python environment...")
        try:
            res = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            if res.returncode != 0:
                msg = _format_error_report(
                    phase="Pip Wheel Installation (Bypass Injection)",
                    reason=f"pip failed to install renamed wheel (code {res.returncode}).",
                    details=res.stderr or res.stdout,
                    remedies=[
                        "Upgrade pip and setuptools: pip install --upgrade pip setuptools",
                        "Ensure your user has write permissions to Python site-packages."
                    ]
                )
                raise InstallationError(msg)
        except subprocess.TimeoutExpired as e:
            msg = _format_error_report(
                phase="Pip Wheel Installation",
                reason=f"pip command timed out after {SUBPROCESS_TIMEOUT_SECONDS}s.",
                remedies=["Verify storage I/O speed and available disk space."]
            )
            raise InstallationError(msg) from e

def install_python_dependencies() -> None:
    """Install core Python dependencies required by Playwright."""
    deps = ["pyee>=8.1.0,<=13.0.0", "typing-extensions>=4.12.0"]
    try:
        import greenlet  # Check if provided by native python-greenlet package
    except ImportError:
        deps.insert(0, "greenlet>=3.1.1")

    pip_cmd = [sys.executable, "-m", "pip", "install", "--prefer-binary"] + deps
    print(f"[*] Installing Python dependencies: {deps}")
    try:
        res = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        if res.returncode != 0:
            msg = _format_error_report(
                phase="Python Dependencies Installation",
                reason=f"Failed to install required Python libraries {deps} (code {res.returncode}).",
                details=res.stderr or res.stdout,
                remedies=[
                    "If building greenlet failed due to missing C-compiler, install native package: pkg install -y python-greenlet",
                    "Upgrade pip: pip install --upgrade pip",
                    f"Attempt manual install: pip install --prefer-binary {' '.join(deps)}"
                ]
            )
            raise InstallationError(msg)
    except subprocess.TimeoutExpired as e:
        msg = _format_error_report(
            phase="Python Dependencies Installation",
            reason=f"pip timed out after {SUBPROCESS_TIMEOUT_SECONDS}s.",
            remedies=["Check network connectivity."]
        )
        raise InstallationError(msg) from e

def run_installation_pipeline(version: Optional[str] = None) -> None:
    """Execute complete end-to-end installation and verification pipeline."""
    print("=" * 60)
    print("[*] [Termux-Playwright] Deterministic Installation Pipeline")
    print("=" * 60)

    if is_termux():
        try:
            check_preflight_storage(min_mb=300)
        except StorageExhaustionError as e:
            msg = _format_error_report(
                phase="Pre-flight Storage Health Check",
                reason=str(e),
                remedies=[
                    "Clean cached apt/pkg packages: pkg clean",
                    "Clean temporary directory: rm -rf $TMPDIR/* /tmp/*",
                    "Remove unused pip cache: pip cache purge"
                ]
            )
            raise InstallationError(msg) from e

    if not is_termux():
        target_v = version or DEFAULT_PLAYWRIGHT_VERSION
        print(f"[!] Non-Termux environment detected. Installing standard upstream Playwright ({target_v})...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", f"playwright=={target_v}"], check=False, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        if res.returncode != 0:
            msg = _format_error_report(
                phase="Standard Playwright Installation (Non-Termux)",
                reason=f"pip install playwright=={target_v} failed with exit code {res.returncode}.",
                remedies=["Check internet connection and pip configuration."]
            )
            raise InstallationError(msg)
        print("[+] Standard Playwright installation complete.")
        return

    # 1. Check Architecture
    try:
        arch = get_cpu_architecture()
        print(f"[*] Detected CPU architecture: {arch}")
    except UnsupportedPlatformError as e:
        msg = _format_error_report(
            phase="CPU Architecture Validation",
            reason=str(e),
            remedies=[
                "Termux-Playwright requires a 64-bit ARM CPU (aarch64/arm64) or x86_64.",
                "32-bit ARM (armv7l) does not have compatible Chromium / Node.js binaries."
            ]
        )
        raise InstallationError(msg) from e

    # 2. System Packages
    print("[1/4] Installing native Termux packages (Chromium, Node.js, python-greenlet)...")
    install_system_dependencies()

    # 3. Wheel Bypass
    print("[2/4] Downloading and installing patched Playwright wheel...")
    install_playwright_wheel(version)

    # 4. Dependencies
    print("[3/4] Installing Python dependency packages...")
    install_python_dependencies()

    # 5. JS Platform Patch
    print("[4/4] Applying atomic platform verification bypass patch...")
    try:
        apply_core_bundle_patch()
        try:
            cleanup_backup()
        except Exception as cleanup_err:
            print(f"[*] Optional backup cleanup skipped: {cleanup_err}")
    except PatchingError as e:
        msg = _format_error_report(
            phase="coreBundle.js Platform Patch",
            reason=f"Failed to inject platform verification bypass: {e}",
            remedies=[
                "Verify Playwright package is installed: python -c 'import playwright; print(playwright.__file__)'",
                "Run manual patcher CLI: termux-playwright-patch"
            ]
        )
        raise InstallationError(msg) from e

    print("\n[+] Installation and patching successfully completed!")
    doctor()

def doctor() -> bool:
    """Perform diagnostic health check and report system readiness."""
    print("\n" + "=" * 60)
    print("[*] [Termux-Playwright] Diagnostic Health Check")
    print("=" * 60)

    all_healthy = True
    
    # 1. Environment & Storage
    tmx = is_termux()
    print(f"[*] 1. Termux Environment : {'[OK] Detected' if tmx else '[!] Standard OS'}")
    if tmx:
        try:
            free_mb = check_preflight_storage()
            print(f"[*]    Available Storage  : [OK] {free_mb} MB available")
        except Exception as e:
            print(f"[*]    Available Storage  : [FAIL] {e}")
            all_healthy = False

    # 2. CPU Arch
    try:
        arch = get_cpu_architecture()
        tag = get_wheel_tag_for_arch(arch)
        print(f"[*] 2. CPU Architecture   : [OK] {arch} (Wheel tag: {tag})")
    except UnsupportedPlatformError as e:
        print(f"[*] 2. CPU Architecture   : [FAIL] {e}")
        all_healthy = False

    # 3. Node.js
    try:
        node_path = find_node_binary()
        print(f"[*] 3. Node.js Binary     : [OK] {node_path}")
    except Exception as e:
        print(f"[*] 3. Node.js Binary     : [FAIL] {e}")
        all_healthy = False

    # 4. Chromium
    try:
        chrome_path = find_chromium_binary()
        print(f"[*] 4. Chromium Binary   : [OK] {chrome_path}")
    except Exception as e:
        print(f"[*] 4. Chromium Binary   : [FAIL] {e}")
        all_healthy = False

    # 5. Playwright Python Package
    try:
        pw_dir = locate_playwright_package_dir()
        print(f"[*] 5. Playwright Package : [OK] {pw_dir}")
    except Exception as e:
        print(f"[*] 5. Playwright Package : [FAIL] {e}")
        all_healthy = False
        pw_dir = None

    # 6. coreBundle.js Patch
    if pw_dir:
        try:
            patched = is_core_bundle_patched()
            status_str = "[OK] Applied" if patched else "[FAIL] Not patched (Run termux-playwright-patch)"
            print(f"[*] 6. JS Bypass Patch    : {status_str}")
            if not patched:
                all_healthy = False
        except Exception as e:
            print(f"[*] 6. JS Bypass Patch    : [FAIL] Error checking patch: {e}")
            all_healthy = False
    else:
        print(f"[*] 6. JS Bypass Patch    : [FAIL] Package missing")
        all_healthy = False

    # 7. Power Management (termux-wake-lock)
    if tmx:
        wake_lock_bin = shutil.which("termux-wake-lock")
        if wake_lock_bin:
            try:
                res = subprocess.run([wake_lock_bin], capture_output=True, timeout=2, check=False)
                if res.returncode == 0:
                    print(f"[*] 7. Power Management   : [OK] {wake_lock_bin} (Service responsive)")
                    unlock_bin = shutil.which("termux-wake-unlock")
                    if unlock_bin:
                        subprocess.run([unlock_bin], capture_output=True, timeout=2, check=False)
                else:
                    print(f"[*] 7. Power Management   : [!] termux-wake-lock exited with code {res.returncode}")
            except subprocess.TimeoutExpired:
                print(f"[*] 7. Power Management   : [!] termux-wake-lock timed out. Termux:API APK may be missing.")
        else:
            print(f"[*] 7. Power Management   : [!] 'termux-wake-lock' missing (pkg install termux-api + Termux:API APK)")

    # 8. Virtual Environment Integrity
    if hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
        print(f"[*] 8. Virtualenv Check   : [!] Running inside venv ({sys.prefix})")
        print("                           Note: If greenlet is not found, recreate venv with: python -m venv --system-site-packages")

    print("=" * 60)
    print(f"Overall Status: {'[HEALTHY]' if all_healthy else '[UNHEALTHY - ACTION REQUIRED]'}\n")
    return all_healthy

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("doctor", "--doctor", "-d"):
        healthy = doctor()
        sys.exit(0 if healthy else 1)
    else:
        try:
            target_version = sys.argv[1] if len(sys.argv) > 1 else None
            run_installation_pipeline(version=target_version)
        except Exception as err:
            print(f"\n{err}", file=sys.stderr)
            sys.exit(1)
