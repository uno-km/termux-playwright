"""Atomic and verifiable patcher for Playwright coreBundle.js.

Provides transactional byte-level patch injection, verification,
backup, and rollback capabilities without silent corruption.
"""

import os
import shutil
import importlib.util
from typing import Optional
from .exceptions import PatchingError

PATCH_SIGNATURE = 'Object.defineProperty(process, "platform", {value: "linux"});'
PATCH_PAYLOAD = (
    'Object.defineProperty(process, "platform", {value: "linux"});\n'
    'Object.defineProperty(require("os"), "platform", {value: () => "linux"});\n'
)

def locate_playwright_package_dir() -> str:
    """Locate installed playwright package directory across venv, conda, or global sites."""
    try:
        spec = importlib.util.find_spec("playwright")
        if spec and spec.submodule_search_locations:
            path = list(spec.submodule_search_locations)[0]
            if os.path.isdir(path):
                return path
    except Exception:
        pass

    try:
        import playwright
        if hasattr(playwright, "__file__") and playwright.__file__:
            path = os.path.dirname(playwright.__file__)
            if os.path.isdir(path):
                return path
    except Exception:
        pass

    raise PatchingError(
        "Playwright Python package is not installed or cannot be imported in the current environment."
    )

def locate_core_bundle_path() -> str:
    """Return the absolute path to driver coreBundle.js."""
    pw_dir = locate_playwright_package_dir()
    core_bundle = os.path.join(pw_dir, "driver", "package", "lib", "coreBundle.js")
    if not os.path.isfile(core_bundle):
        raise PatchingError(f"Playwright coreBundle.js not found at expected path: {core_bundle}")
    return core_bundle

def is_core_bundle_patched(target_path: Optional[str] = None) -> bool:
    """Verify if target coreBundle.js already has the platform bypass injected."""
    path = target_path or locate_core_bundle_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            header = f.read(512)
            return PATCH_SIGNATURE in header
    except Exception as e:
        raise PatchingError(f"Failed to read coreBundle.js: {e}") from e

def apply_core_bundle_patch(target_path: Optional[str] = None) -> bool:
    """Atomically inject platform bypass into coreBundle.js with backup and verification.
    
    Returns:
        bool: True if newly patched, False if already patched.
    Raises:
        PatchingError: If write or verification fails.
    """
    path = target_path or locate_core_bundle_path()
    
    if is_core_bundle_patched(path):
        return False

    backup_path = path + ".bak"
    tmp_path = path + ".tmp"

    try:
        # 1. Create backup if not present
        if not os.path.exists(backup_path):
            shutil.copy2(path, backup_path)

        # 2. Read original content
        with open(path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # 3. Write to temporary file
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(PATCH_PAYLOAD + original_content)

        # 4. Atomic file replace
        os.replace(tmp_path, path)

        # 5. Post-condition verification
        if not is_core_bundle_patched(path):
            raise PatchingError("Post-patch verification failed: Signature not detected after write.")

        return True

    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise PatchingError(f"Atomic patch application failed on {path}: {e}") from e

def rollback_core_bundle_patch(target_path: Optional[str] = None) -> bool:
    """Restore original coreBundle.js from backup file."""
    path = target_path or locate_core_bundle_path()
    backup_path = path + ".bak"

    if not os.path.isfile(backup_path):
        raise PatchingError(f"Cannot rollback: Backup file does not exist at {backup_path}")

    try:
        os.replace(backup_path, path)
        return True
    except Exception as e:
        raise PatchingError(f"Rollback failed: {e}") from e
