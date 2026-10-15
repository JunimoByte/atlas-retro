"""Atlas | Tests | Backup | Filesystem Utilities.

Unit tests for backup/disk.py.
Covers safe file deletion, base path resolution, and ZIP path sanitization.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import sys
from pathlib import Path

import pytest

from atlas.backup import disk

# =============================================================================
# TESTS — Safe unlink
# =============================================================================


def test_safe_unlink_deletes_existing_file(tmp_path: Path) -> None:
    """Verify that safe_unlink deletes an existing file."""
    f = tmp_path / "file.txt"
    f.write_text("data")
    disk.safe_unlink(f)
    assert not f.exists()


def test_safe_unlink_does_not_raise_on_missing_file(tmp_path: Path) -> None:
    """Verify that safe_unlink does not raise on missing files."""
    disk.safe_unlink(tmp_path / "ghost.txt")


# =============================================================================
# TESTS — Find base path
# =============================================================================


def test_find_base_path_finds_correct_source(tmp_path: Path) -> None:
    """Verify that the source containing the file is returned."""
    source_a = tmp_path / "a"
    source_b = tmp_path / "b"
    source_a.mkdir()
    source_b.mkdir()
    file_path = source_a / "sub" / "file.txt"
    file_path.parent.mkdir()
    file_path.write_text("data")

    result = disk.find_base_path(file_path, [source_a, source_b])
    assert result == source_a


def test_find_base_path_returns_none_when_no_match(tmp_path: Path) -> None:
    """Verify that None is returned if no source matches."""
    source = tmp_path / "source"
    source.mkdir()
    unrelated = tmp_path / "other" / "file.txt"
    assert disk.find_base_path(unrelated, [source]) is None


def test_find_base_path_empty_sources(tmp_path: Path) -> None:
    """Verify that None is returned for an empty sources list."""
    assert disk.find_base_path(tmp_path / "file.txt", []) is None


# =============================================================================
# TESTS — Relative path
# =============================================================================


@pytest.fixture
def zipped_file(tmp_path: Path) -> tuple:
    """Return a (file, base) pair ready for relative_zip_path tests."""
    base = tmp_path / "source"
    base.mkdir()
    f = base / "sub" / "file.txt"
    f.parent.mkdir()
    f.write_text("data")
    return f, base


def test_relative_zip_path(zipped_file: tuple) -> None:
    """Verify forward slashes, base prefix, and lack of NUL bytes."""
    f, base = zipped_file
    result = disk.relative_zip_path(f, base)
    assert "/" in result
    assert "\\" not in result
    assert result.startswith("source/")
    assert "\x00" not in result


def test_relative_zip_path_fallback_on_unrelated_path(tmp_path: Path) -> None:
    """Verify relative_zip_path falls back safely if path is unrelated."""
    f = tmp_path / "somewhere_else" / "file.txt"
    base = tmp_path / "base"
    result = disk.relative_zip_path(f, base)
    assert result.startswith("base/")
    assert "file.txt" in result
    assert "\\" not in result


def test_fallback_direntry_methods(tmp_path: Path) -> None:
    """Verify _FallbackDirEntry is_dir, is_file, is_symlink, and stat."""
    f = tmp_path / "regular.txt"
    f.write_text("hello")
    d = tmp_path / "folder"
    d.mkdir()

    entry_f = disk._FallbackDirEntry(str(tmp_path), "regular.txt")
    assert entry_f.is_file() is True
    assert entry_f.is_dir() is False
    assert entry_f.is_symlink() is False
    assert entry_f.stat().st_size == 5

    entry_d = disk._FallbackDirEntry(str(tmp_path), "folder")
    assert entry_d.is_file() is False
    assert entry_d.is_dir() is True
    assert entry_d.is_symlink() is False


def test_scandir_context_wrapper() -> None:
    """Verify _ScandirContextWrapper manages lifecycle and calls close."""
    closed = []

    class DummyIter:
        def __iter__(self):
            return iter([1, 2, 3])

        def close(self):
            closed.append(True)

    dummy = DummyIter()
    with disk._ScandirContextWrapper(dummy) as it:
        items = list(it)
        assert items == [1, 2, 3]
    assert closed == [True]


def test_find_base_path_normcase_fallback(tmp_path: Path) -> None:
    """Verify find_base_path matches even when path casing differs."""
    source = tmp_path / "SourceDir"
    source.mkdir()
    child = source / "sub" / "file.txt"
    child.parent.mkdir()
    child.write_text("content")

    matched = disk.find_base_path(child, [source])
    assert matched == source


def test_relative_zip_path_preserves_nested_structure(tmp_path: Path) -> None:
    """Verify relative_zip_path preserves nested folders in fallback."""
    base = tmp_path / "my_base"
    base.mkdir()
    nested = base / "level1" / "level2" / "target.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("data")

    rel = disk.relative_zip_path(nested, base)
    assert rel == "my_base/level1/level2/target.txt"


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
