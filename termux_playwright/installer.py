"""Automated installation and dependency resolution engine for Termux Playwright.

Executes verifiable, fail-safe installation of native system packages,
aarch64/x86_64 bypass wheels, and JS platform patches with strict error validation.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from typing import Tuple, Optional

from .exceptions import InstallationError, UnsupportedPlatformError, PatchingError
from .platform import (
    is_termux,
    get_cpu_architecture,
    get_wheel_tag_for_arch,
    find_chromium_binary,
    find_node_binary,
)
from .patcher import apply_core_bundle_patch, is_core_bundle_patched, locate_playwright_package_dir

DEFAULT_PLAYWRIGHT_VERSION = "1.61.0"
SUBPROCESS_TIMEOUT_SECONDS = 300

def fetch_pypi_wheel_info(version: str = DEFAULT_PLAYWRIGHT_VERSION) -> Tuple[str, str]:
    """Query PyPI JSON API for the exact matching architecture wheel URL and filename."""
    arch = get_cpu_architecture()
    tag = get_wheel_tag_for_arch(arch)
    api_url = f"https://pypi.org/pypi/playwright/{version}/json"

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "termux-playwright-installer"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                raise InstallationError(f"PyPI API returned HTTP {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
            
            urls = data.get("urls", [])
            for item in urls:
                filename = item.get("filename", "")
                if tag in filename and filename.endswith(".whl"):
                    download_url = item.get("url")
                    if download_url:
                        return download_url, filename

        raise InstallationError(f"No suitable wheel with tag '{tag}' found on PyPI for version {version}")

    except Exception as e:
        raise InstallationError(f"Failed to resolve wheel from PyPI: {e}") from e

def install_system_dependencies() -> None:
    """Install native Termux Chromium and Node.js packages via pkg."""
    pkg_bin = shutil.which("pkg")
    if not pkg_bin:
        raise InstallationError("Termux 'pkg' package manager was not found in PATH.")

    cmd = [pkg_bin, "install", "-y", "chromium", "nodejs"]
    print(f"[*] Executing system package installation: {' '.join(cmd)}")
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        if res.returncode != 0:
            raise InstallationError(
                f"Failed to install system packages via pkg (code {res.returncode}):\n{res.stderr or res.stdout}"
            )
    except subprocess.TimeoutExpired as e:
        raise InstallationError(f"System package installation timed out after {SUBPROCESS_TIMEOUT_SECONDS}s") from e

def install_playwright_wheel(version: str = DEFAULT_PLAYWRIGHT_VERSION) -> None:
    """Download architecture wheel, rename to bypass platform checks, and install with force-reinstall."""
    download_url, filename = fetch_pypi_wheel_info(version)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        download_target = os.path.join(temp_dir, filename)
        renamed_target = os.path.join(temp_dir, f"playwright-{version}-py3-none-any.whl")

        print(f"[*] Downloading Playwright wheel from: {download_url}")
        try:
            urllib.request.urlretrieve(download_url, download_target)
        except Exception as e:
            raise InstallationError(f"Failed to download wheel from {download_url}: {e}") from e

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
                raise InstallationError(
                    f"pip installation of renamed wheel failed (code {res.returncode}):\n{res.stderr}"
                )
        except subprocess.TimeoutExpired as e:
            raise InstallationError(f"pip install timed out after {SUBPROCESS_TIMEOUT_SECONDS}s") from e

def install_python_dependencies() -> None:
    """Install core Python dependencies required by Playwright."""
    deps = ["greenlet>=3.1.1", "pyee>=13.0.0", "typing-extensions>=4.12.0"]
    pip_cmd = [sys.executable, "-m", "pip", "install"] + deps
    print(f"[*] Installing Python dependencies: {deps}")
    try:
        res = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        if res.returncode != 0:
            raise InstallationError(f"Failed to install Python dependencies:\n{res.stderr}")
    except subprocess.TimeoutExpired as e:
        raise InstallationError(f"Python dependency installation timed out after {SUBPROCESS_TIMEOUT_SECONDS}s") from e

def run_installation_pipeline(version: str = DEFAULT_PLAYWRIGHT_VERSION) -> None:
    """Execute complete end-to-end installation and verification pipeline."""
    print("=" * 60)
    print("🚀 [Termux-Playwright] Deterministic Installation Pipeline")
    print("=" * 60)

    if not is_termux():
        print("[!] Non-Termux environment detected. Installing standard upstream Playwright...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", f"playwright=={version}"], check=False, timeout=SUBPROCESS_TIMEOUT_SECONDS)
        if res.returncode != 0:
            raise InstallationError(f"Standard playwright install failed with code {res.returncode}")
        print("[+] Standard Playwright installation complete.")
        return

    # 1. Check Architecture
    arch = get_cpu_architecture()
    print(f"[*] Detected CPU architecture: {arch}")

    # 2. System Packages
    print("[1/4] Installing native Termux packages (Chromium, Node.js)...")
    install_system_dependencies()

    # 3. Wheel Bypass
    print("[2/4] Downloading and installing patched Playwright wheel...")
    install_playwright_wheel(version)

    # 4. Dependencies
    print("[3/4] Installing Python dependency packages...")
    install_python_dependencies()

    # 5. JS Platform Patch
    print("[4/4] Applying atomic platform verification bypass patch...")
    apply_core_bundle_patch()

    print("\n[+] Installation and patching successfully completed!")
    doctor()

def doctor() -> bool:
    """Perform diagnostic health check and report system readiness."""
    print("\n" + "=" * 60)
    print("🩺 [Termux-Playwright] Diagnostic Health Check")
    print("=" * 60)

    all_healthy = True
    
    # 1. Environment
    tmx = is_termux()
    print(f"[*] 1. Termux Environment : {'[OK] Detected' if tmx else '[!] Standard OS'}")

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

    print("=" * 60)
    print(f"Overall Status: {'[HEALTHY]' if all_healthy else '[UNHEALTHY - ACTION REQUIRED]'}\n")
    return all_healthy

if __name__ == "__main__":
    try:
        run_installation_pipeline()
    except Exception as err:
        print(f"\n[-] Installation Pipeline Failed: {err}", file=sys.stderr)
        sys.exit(1)
