"""Atlas | Tests | Backup | Size Management.

Unit tests for backup/size.py.
Covers directory size calculation, size formatting, disk space checking,
and output directory creation.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os
import sys
from pathlib import Path

import pytest

import atlas.backup.size as size_module
from atlas.backup.size import (
    check_disk_space,
    create_output_dir,
    format_size,
    get_directory_size,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def clean_blacklist(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure SKIP_FOLDERS is a known set for all tests."""
    monkeypatch.setattr(size_module, "SKIP_FOLDERS", {"__pycache__"})


# =============================================================================
# TESTS — Format size
# =============================================================================


@pytest.mark.parametrize(
    "value, expected",
    [
        (512, "512 B"),
        (1024, "1 KB"),
        (1024**2, "1 MB"),
        (1024**3, "1 GB"),
        (0, "0 B"),
        (-1, "Invalid size"),
        ("not a number", "Unknown size"),
    ],
)
def test_format_size_variations(value: object, expected: str) -> None:
    """Verify size formatting for various inputs and edge cases."""
    assert format_size(value) == expected


def test_format_size_fractional() -> None:
    """Verify fractional KB formatting."""
    assert "1.5 KB" in format_size(1536)


# =============================================================================
# TESTS — Get directory size
# =============================================================================


def test_get_directory_size_sums_files(tmp_path: Path) -> None:
    """Verify that directory size is the sum of its files."""
    (tmp_path / "a.txt").write_bytes(b"x" * 100)
    (tmp_path / "b.txt").write_bytes(b"x" * 200)
    assert get_directory_size(tmp_path) == 300


def test_get_directory_size_excludes_blacklisted_folder(
    tmp_path: Path,
) -> None:
    """Verify that blacklisted folders are excluded from size calculation."""
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "hidden.pyc").write_bytes(b"x" * 500)
    (tmp_path / "visible.txt").write_bytes(b"x" * 100)
    assert get_directory_size(tmp_path) == 100


def test_get_directory_size_empty_directory(tmp_path: Path) -> None:
    """Verify that empty directories have zero size."""
    assert get_directory_size(tmp_path) == 0


def test_get_directory_size_missing_path() -> None:
    """Verify that nonexistent paths have zero size."""
    assert get_directory_size("/no/such/path") == 0


def test_get_directory_size_recursive(tmp_path: Path) -> None:
    """Verify recursive size calculation."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "file.txt").write_bytes(b"x" * 50)
    assert get_directory_size(tmp_path) == 50


# =============================================================================
# TESTS — Check disk space
# =============================================================================


def test_check_disk_space_returns_tuple(tmp_path: Path) -> None:
    """Verify that a (bool, str) tuple is returned."""
    ok, available = check_disk_space(0, tmp_path)
    assert isinstance(ok, bool)
    assert isinstance(available, str)


def test_check_disk_space_zero_size_always_passes(tmp_path: Path) -> None:
    """Verify that zero size always passes the disk check."""
    ok, _ = check_disk_space(0, tmp_path)
    assert ok is True


def test_check_disk_space_enormous_size_fails(tmp_path: Path) -> None:
    """Verify that insufficient disk space is correctly detected."""
    ok, available = check_disk_space(99_999_999_999_999, tmp_path)
    assert ok is False
    assert isinstance(available, str)


def test_check_disk_space_failure_blocks_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return False when the disk-space probe itself fails."""
    target = tmp_path / "output"
    target.mkdir()

    def raise_disk_usage(path: Path) -> None:
        """Raise an error while probing disk space."""
        del path
        raise OSError("disk probe failed")

    monkeypatch.setattr(size_module.shutil, "disk_usage", raise_disk_usage)

    ok, available = check_disk_space(1024, target)

    assert ok is False
    assert available == "Unknown"


def test_check_disk_space_handles_mkdir_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify check_disk_space continues using parent if mkdir fails."""
    target = tmp_path / "protected_subdir"

    def fail_makedirs(path, exist_ok=False):
        if str(target) in str(path):
            raise OSError("Permission denied creating folder")
        return None

    monkeypatch.setattr(os, "makedirs", fail_makedirs)
    ok, available = check_disk_space(1024, target)
    # The parent tmp_path exists and has free space, so check succeeds
    assert ok is True
    assert available != "Unknown"


# =============================================================================
# TESTS — Create output directory
# =============================================================================


@pytest.mark.parametrize("pre_exists", [False, True])
def test_create_output_dir(tmp_path: Path, pre_exists: bool) -> None:
    """Verify that the output directory is created successfully."""
    target = tmp_path / "output"
    if pre_exists:
        target.mkdir()
    result = create_output_dir(target)
    assert isinstance(result, Path)
    assert result.exists()
    assert result.is_dir()


def test_get_directory_size_skips_exceeding_max_depth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify get_directory_size respects MAX_DIR_DEPTH limit."""
    import atlas.backup.size as size_mod

    monkeypatch.setattr(size_mod, "MAX_DIR_DEPTH", 2)
    current = tmp_path
    for i in range(4):
        current = current / "dir{}".format(i)
        current.mkdir()
        (current / "file.txt").write_bytes(b"x" * 100)

    total = size_mod.get_directory_size(tmp_path)
    assert total <= 300


def test_get_directory_size_handles_root_oserror(tmp_path: Path) -> None:
    """Verify get_directory_size returns 0 if checking root raises OSError."""
    from unittest.mock import patch

    with patch.object(Path, "exists", side_effect=OSError("Access denied")):
        assert get_directory_size(tmp_path) == 0


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
