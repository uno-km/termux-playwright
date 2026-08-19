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

def test_cleanup_backup(tmp_path):
    from termux_playwright.patcher import cleanup_backup
    mock_bundle = tmp_path / "coreBundle.js"
    mock_bundle.write_text("dummy", encoding="utf-8")
    mock_bak = tmp_path / "coreBundle.js.bak"
    mock_bak.write_text("backup_content", encoding="utf-8")

    assert cleanup_backup(str(mock_bundle)) is True
    assert not mock_bak.exists()
    assert cleanup_backup(str(mock_bundle)) is False

def test_locate_core_bundle_path_recursive_fallback(tmp_path, monkeypatch):
    from termux_playwright.patcher import locate_core_bundle_path
    
    deep_nested = tmp_path / "playwright_custom" / "sub" / "lib"
    deep_nested.mkdir(parents=True)
    custom_bundle = deep_nested / "coreBundle.js"
    custom_bundle.write_text("console.log('custom')", encoding="utf-8")

    monkeypatch.setattr("termux_playwright.patcher.locate_playwright_package_dir", lambda: str(tmp_path / "playwright_custom"))
    found = locate_core_bundle_path()
    assert found == str(custom_bundle)

def test_cli_patch_core_bundle_stdout(tmp_path, monkeypatch, capsys):
    from termux_playwright.patcher import cli_patch_core_bundle
    mock_bundle = tmp_path / "coreBundle.js"
    mock_bundle.write_text("console.log('original');", encoding="utf-8")

    monkeypatch.setattr("termux_playwright.patcher.locate_core_bundle_path", lambda: str(mock_bundle))
    
    # 1. First run: successfully applied
    cli_patch_core_bundle()
    captured = capsys.readouterr()
    assert "Successfully applied platform bypass patch" in captured.out

    # 2. Second run: already patched
    cli_patch_core_bundle()
    captured = capsys.readouterr()
    assert "is already patched and verified" in captured.out


