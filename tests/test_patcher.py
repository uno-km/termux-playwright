import os
import pytest
from termux_playwright.patcher import (
    apply_core_bundle_patch,
    is_core_bundle_patched,
    rollback_core_bundle_patch,
    PATCH_SIGNATURE,
)
from termux_playwright.exceptions import PatchingError

def test_atomic_patch_and_rollback(tmp_path):
    mock_bundle = tmp_path / "coreBundle.js"
    original_code = 'console.log("Playwright driver starting...");\nmodule.exports = {};\n'
    mock_bundle.write_text(original_code, encoding="utf-8")

    # 1. Check initial unpatched state
    assert is_core_bundle_patched(str(mock_bundle)) is False

    # 2. Apply patch
    newly_patched = apply_core_bundle_patch(str(mock_bundle))
    assert newly_patched is True
    assert is_core_bundle_patched(str(mock_bundle)) is True

    # Check that backup file was created
    backup_file = tmp_path / "coreBundle.js.bak"
    assert backup_file.is_file()
    assert backup_file.read_text(encoding="utf-8") == original_code

    # Check content of patched file
    patched_content = mock_bundle.read_text(encoding="utf-8")
    assert PATCH_SIGNATURE in patched_content
    assert original_code in patched_content

    # 3. Idempotency test (second patch attempt should return False)
    assert apply_core_bundle_patch(str(mock_bundle)) is False

    # 4. Rollback test
    assert rollback_core_bundle_patch(str(mock_bundle)) is True
    assert is_core_bundle_patched(str(mock_bundle)) is False
    assert mock_bundle.read_text(encoding="utf-8") == original_code

def test_patch_nonexistent_file():
    with pytest.raises(PatchingError):
        apply_core_bundle_patch("/non/existent/path/coreBundle.js")
