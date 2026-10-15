"""Unit tests for archive management in atlas.backup.archive.

Covers ZIP creation, file scanning, blacklist enforcement, and path
normalization.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os
import sys
import zipfile
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

import atlas.backup.filter as backup_filter
from atlas.backup import archive

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_output_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide an isolated ZIP output directory patched into the archive."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    monkeypatch.setattr(archive, "ZIP_OUTPUT_DIR", output_dir)
    return output_dir


@pytest.fixture
def mock_blacklist(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the blacklist globals to known test values."""
    monkeypatch.setattr(backup_filter, "SKIP_FOLDERS", {"__pycache__"})
    monkeypatch.setattr(backup_filter, "SKIP_FILE_EXTENSION", {".log"})


# =============================================================================
# HELPERS
# =============================================================================


def create_files(base: Path, names: List[str]) -> None:
    """Create simple text files under *base* for testing.

    Args:
        base: The root directory in which to create the files.
        names: An iterable of relative path strings to create.

    """
    for name in names:
        file_path = base / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("content")


# =============================================================================
# TESTS — Relative path
# =============================================================================


def test_relative_zip_path_uses_forward_slashes(tmp_path: Path) -> None:
    """Verify that relative_zip_path uses forward slashes."""
    base = tmp_path / "source"
    base.mkdir()
    file_path = base / "subdir" / "file.txt"
    file_path.parent.mkdir()
    file_path.write_text("data")

    result = archive.relative_zip_path(file_path, base)

    assert "/" in result
    assert "\\" not in result
    assert result.startswith("source/")


# =============================================================================
# TESTS — Scan files
# =============================================================================


def test_scan_files_respects_blacklist(
    tmp_path: Path, mock_blacklist: None
) -> None:
    """Verify that scan_files excludes blacklisted items."""
    source = tmp_path / "source"
    source.mkdir()

    create_files(
        source,
        [
            "valid.txt",
            "skip.log",
            "__pycache__/ignored.pyc",
        ],
    )

    results = list(archive.scan_files([source]))
    names = [f.name for _, f in results]

    assert "valid.txt" in names
    assert "skip.log" not in names
    assert "ignored.pyc" not in names


# =============================================================================
# TESTS — Compress
# =============================================================================


def test_compress_creates_zip(
    tmp_path: Path, temp_output_dir: Path, mock_blacklist: None
) -> None:
    """Compress should produce a ZIP containing all scanned source files."""
    source = tmp_path / "source"
    source.mkdir()
    create_files(source, ["file1.txt", "file2.txt"])

    result = archive.compress(source, "test.zip")

    assert result is not None
    assert result.exists()

    with zipfile.ZipFile(result, "r") as zf:
        assert len(zf.namelist()) == 2


def test_compress_renames_only_colliding_source_directories(
    tmp_path: Path, temp_output_dir: Path, mock_blacklist: None
) -> None:
    """Keep source names unless another source uses the same archive root."""
    first_profile = tmp_path / "first" / "profile-data"
    second_profile = tmp_path / "second" / "profile-data"
    distinct_source = tmp_path / "third" / "cache-data"

    for source, content in (
        (first_profile, "first"),
        (second_profile, "second"),
        (distinct_source, "cache"),
    ):
        source.mkdir(parents=True)
        (source / "Local State").write_text(content)

    result = archive.compress(
        [first_profile, second_profile, distinct_source], "test.zip"
    )

    assert result is not None
    with zipfile.ZipFile(result, "r") as zf:
        assert sorted(zf.namelist()) == [
            "cache-data/Local State",
            "profile-data(1)/Local State",
            "profile-data/Local State",
        ]
        assert zf.read("profile-data/Local State") == b"first"
        assert zf.read("profile-data(1)/Local State") == b"second"


def test_compress_deduplicates_identical_source_paths(
    tmp_path: Path, temp_output_dir: Path, mock_blacklist: None
) -> None:
    """Do not archive the same discovered source twice."""
    source = tmp_path / "profile-data"
    source.mkdir()
    (source / "Local State").write_text("profile")

    result = archive.compress([source, source], "test.zip")

    assert result is not None
    with zipfile.ZipFile(result, "r") as zf:
        assert zf.namelist() == ["profile-data/Local State"]


def test_compress_rejects_invalid_input(temp_output_dir: Path) -> None:
    """Compress should return None when given a non-Path source argument."""
    result = archive.compress(12345, "test.zip")
    assert result is None


def test_resolve_output_zip_path_stays_within_output_dir(
    temp_output_dir: Path,
) -> None:
    """Resolve a normal ZIP path inside the configured output directory."""
    result = archive._resolve_output_zip_path("test.zip")
    assert result == temp_output_dir.resolve() / "test.zip"


def test_resolve_output_zip_path_rejects_parent_traversal(
    temp_output_dir: Path,
) -> None:
    """Reject ZIP paths that escape the configured output directory."""
    with pytest.raises(ValueError):
        archive._resolve_output_zip_path("../escape.zip")


def test_write_zip_cleans_temp_file_when_cancelled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Delete the temporary ZIP file when cancellation occurs mid-write."""
    source = tmp_path / "source"
    source.mkdir()
    create_files(source, ["file1.txt", "file2.txt"])

    files = [
        (source, source / "file1.txt"),
        (source, source / "file2.txt"),
    ]
    zip_path = tmp_path / "archive.zip"
    temp_zip_path = zip_path.with_suffix(".zip.tmp")
    callback_count = {"value": 0}

    def cancel_callback() -> bool:
        """Cancel on the second loop-level cancellation check."""
        callback_count["value"] += 1
        return callback_count["value"] > 1

    def write_stub(
        zip_file: zipfile.ZipFile,
        file_path: Path,
        zip_info: zipfile.ZipInfo,
        cancel_callback=None,
    ) -> bool:
        """Write a small entry without consulting cancellation."""
        del file_path
        del cancel_callback
        zip_file.writestr(zip_info, "content")
        return True

    monkeypatch.setattr(archive, "_write_file_to_zip", write_stub)

    archive.write_zip(files, zip_path, cancel_callback)

    assert not temp_zip_path.exists()
    assert not zip_path.exists()


def test_write_zip_raises_on_file_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Abort the archive when _write_file_to_zip raises unexpectedly."""
    source = tmp_path / "source"
    source.mkdir()
    create_files(source, ["file1.txt"])

    files = [(source, source / "file1.txt")]
    zip_path = tmp_path / "archive.zip"
    temp_zip_path = zip_path.with_suffix(".zip.tmp")

    def fatal_write(*args: object) -> bool:
        raise RuntimeError("simulated unexpected write failure")

    monkeypatch.setattr(archive, "_write_file_to_zip", fatal_write)

    with pytest.raises(RuntimeError):
        archive.write_zip(files, zip_path)

    assert not temp_zip_path.exists()
    assert not zip_path.exists()


def test_compress_returns_none_when_no_files(
    tmp_path: Path,
    temp_output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compress should return None when scan_files yields no files."""
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(archive, "scan_files", lambda x, y=None: [])
    result = archive.compress(source, "test.zip")
    assert result is None


def test_compress_returns_none_when_write_zip_fails(
    tmp_path: Path,
    temp_output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compress should return None when _write_file_to_zip raises."""
    source = tmp_path / "source"
    source.mkdir()
    create_files(source, ["file1.txt"])

    def fatal_write(*args: object) -> bool:
        raise RuntimeError("simulated unexpected write failure")

    monkeypatch.setattr(archive, "_write_file_to_zip", fatal_write)

    result = archive.compress(source, "test.zip")

    assert result is None
    assert not (temp_output_dir / "test.zip").exists()


def test_compress_zip_contains_actual_content(
    tmp_path: Path,
    temp_output_dir: Path,
    mock_blacklist: None,
) -> None:
    """Compress should faithfully store file contents inside the ZIP."""
    source = tmp_path / "source"
    source.mkdir()

    file_path = source / "hello.txt"
    file_path.write_text("atlas")

    result = archive.compress(source, "test.zip")

    with zipfile.ZipFile(result, "r") as zf:
        data = zf.read(next(iter(zf.namelist()))).decode("utf-8")
        assert data == "atlas"


def test_compress_rejects_zip_name_that_escapes_output_dir(
    tmp_path: Path, temp_output_dir: Path, mock_blacklist: None
) -> None:
    """Return None when the ZIP name would escape the output directory."""
    source = tmp_path / "source"
    source.mkdir()
    create_files(source, ["file1.txt"])

    result = archive.compress(source, "../escape.zip")

    assert result is None
    assert not (tmp_path / "escape.zip").exists()


def test_write_file_to_zip_python34_writestr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify writing files via writestr on Python 3.4 (no open mode 'w')."""
    monkeypatch.setattr(sys, "version_info", (3, 4, 4, "final", 0))

    source_file = tmp_path / "sample.txt"
    source_file.write_text("retro test content")

    zip_path = tmp_path / "out.zip"
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        zip_info = archive.create_zip_info(source_file)
        zip_info.filename = "sample.txt"
        success = archive._write_file_to_zip(zf, source_file, zip_info)
        assert success is True

    with zipfile.ZipFile(str(zip_path), "r") as zf:
        assert zf.namelist() == ["sample.txt"]
        assert zf.read("sample.txt") == b"retro test content"
        info = zf.getinfo("sample.txt")
        assert info.compress_type == zipfile.ZIP_DEFLATED


def test_unique_sources_handles_nonexistent_paths(tmp_path: Path) -> None:
    """Ensure nonexistent paths do not raise in _unique_sources."""
    existing = tmp_path / "existing"
    existing.mkdir()
    nonexistent = tmp_path / "does_not_exist"

    sources = archive._unique_sources([existing, nonexistent])
    assert len(sources) == 1
    assert sources[0].name == "existing"


def test_safe_unlink_read_only_file(tmp_path: Path) -> None:
    """Verify safe_unlink clears read-only attributes to delete file."""
    import stat

    from atlas.backup.disk import safe_unlink

    sample = tmp_path / "readonly.txt"
    sample.write_text("protected content")
    os.chmod(str(sample), stat.S_IREAD)

    safe_unlink(sample)
    assert not sample.exists()


def test_get_zip_output_dir_fallback_on_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify get_zip_output_dir falls back to tempdir if mkdir fails."""
    import tempfile

    monkeypatch.setattr(archive, "ZIP_OUTPUT_DIR", None)

    orig_makedirs = os.makedirs

    def fail_makedirs(name, exist_ok=False):
        if "Backup" in str(name) and tempfile.gettempdir() not in str(name):
            raise OSError("Permission denied")
        return orig_makedirs(name, exist_ok=exist_ok)

    monkeypatch.setattr(os, "makedirs", fail_makedirs)
    out_dir = archive.get_zip_output_dir()
    assert out_dir is not None
    assert str(out_dir).startswith(tempfile.gettempdir())
    monkeypatch.setattr(archive, "ZIP_OUTPUT_DIR", None)


def test_write_file_to_zip_handles_memory_error(tmp_path: Path) -> None:
    """Verify _write_file_to_zip skips file on MemoryError."""
    sample = tmp_path / "big_sample.bin"
    sample.write_bytes(b"data")
    zi = zipfile.ZipInfo("big_sample.bin")

    zip_dest = tmp_path / "test.zip"
    with zipfile.ZipFile(str(zip_dest), "w") as zf:
        with patch.object(Path, "open", side_effect=MemoryError("OOM")):
            result = archive._write_file_to_zip(zf, sample, zi)
            assert result is False


def test_is_within_output_dir_casing(tmp_path: Path) -> None:
    """Verify _is_within_output_dir handles case and traversal."""
    out = tmp_path / "Backup"
    target = out / "sub" / "archive.zip"
    assert archive._is_within_output_dir(target, out) is True

    # Sibling directory starting with same prefix should be rejected
    sibling = tmp_path / "Backup_other" / "archive.zip"
    assert archive._is_within_output_dir(sibling, out) is False


def test_generate_zip_name_normal_and_strftime_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify generate_zip_name has safe strftime fallback."""
    name = archive.generate_zip_name()
    assert name.startswith("Unknown_")
    assert name.endswith(".zip")

    class FakeDatetime:
        year = 1899
        month = 5
        day = 12
        hour = 8
        minute = 30
        second = 15
        microsecond = 123456

        def strftime(self, fmt):
            raise ValueError("year=1899 is before 1900")

    class FakeDatetimeClass:
        @classmethod
        def now(cls):
            return FakeDatetime()

    monkeypatch.setattr(archive, "datetime", FakeDatetimeClass)
    fallback_name = archive.generate_zip_name()
    assert fallback_name.startswith("Unknown_19800512_083015_123456.zip")


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
