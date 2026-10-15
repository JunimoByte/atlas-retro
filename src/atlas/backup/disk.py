"""Atlas | Archive | Filesystem Utilities.

Filesystem helpers for archive operations.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
import os
import stat
from pathlib import Path
from typing import List, Optional

try:
    from os import scandir as _os_scandir
except ImportError:
    try:
        from scandir import scandir as _os_scandir
    except ImportError:
        _os_scandir = None

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

# =============================================================================
# SCANDIR FALLBACK FOR PYTHON 3.4
# =============================================================================


class _FallbackDirEntry:
    """Fallback directory entry emulator for Python 3.4."""

    def __init__(self, dir_path, name):
        self.name = name
        self.path = os.path.join(dir_path, name)
        self._stat = None
        self._lstat = None

    def is_dir(self, follow_symlinks=False):
        try:
            st = self.stat(follow_symlinks=follow_symlinks)
            return stat.S_ISDIR(st.st_mode)
        except OSError:
            return False

    def is_file(self, follow_symlinks=False):
        try:
            st = self.stat(follow_symlinks=follow_symlinks)
            return stat.S_ISREG(st.st_mode)
        except OSError:
            return False

    def is_symlink(self):
        try:
            st = self.stat(follow_symlinks=False)
            return stat.S_ISLNK(st.st_mode)
        except OSError:
            return False

    def stat(self, follow_symlinks=False):
        if follow_symlinks:
            if self._stat is None:
                self._stat = os.stat(self.path)
            return self._stat
        else:
            if self._lstat is None:
                try:
                    self._lstat = os.lstat(self.path)
                except AttributeError:
                    self._lstat = os.stat(self.path)
            return self._lstat


class _ScandirContextWrapper:
    """Ensure scandir iterator works as context manager on Python 3.5."""

    def __init__(self, iterator):
        self._iterator = iterator

    def __enter__(self):
        return self._iterator

    def __exit__(self, exc_type, exc_val, exc_tb):
        close_fn = getattr(self._iterator, "close", None)
        if callable(close_fn):
            close_fn()


class _FallbackScandir:
    """Fallback context manager for os.scandir in Python 3.4."""

    def __init__(self, dir_path):
        self.dir_path = str(dir_path)

    def __enter__(self):
        try:
            names = os.listdir(self.dir_path)
        except OSError:
            names = []
        return (_FallbackDirEntry(self.dir_path, n) for n in names)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def safe_scandir(path):
    """Return a scandir iterator with fallback for Python 3.4/3.5."""
    if _os_scandir is not None:
        entries = _os_scandir(str(path))
        if hasattr(entries, "__enter__"):
            return entries
        return _ScandirContextWrapper(entries)
    return _FallbackScandir(path)


# =============================================================================
# FUNCTIONS
# =============================================================================


def safe_unlink(path: Path) -> None:
    """Safely delete a file, suppressing errors and clearing read-only flags.

    Args:
        path (Path): Path to the file to delete.

    """
    try:
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                # On Windows, read-only files raise PermissionError on unlink.
                # Clear the read-only attribute and retry.
                try:
                    os.chmod(str(path), stat.S_IWRITE)
                    path.unlink()
                except Exception:
                    raise
    except (OSError, FileNotFoundError) as error:
        LOGGER.warning("Failed to delete {}: {}".format(path, error))


def find_base_path(file_path: Path, sources: List[Path]) -> Optional[Path]:
    """Find which source directory contains the file.

    Args:
        file_path (Path): File to locate.
        sources (List[Path]): List of source directories.

    Returns:
        Optional[Path]: The base path if found, None otherwise.

    """
    for source in sources:
        if source in file_path.parents:
            return source

    try:
        norm_file = os.path.normcase(os.path.abspath(str(file_path)))
        for source in sources:
            norm_source = os.path.normcase(os.path.abspath(str(source)))
            if not norm_source.endswith((os.sep, "/")):
                norm_source += os.sep
            if norm_file.startswith(norm_source):
                return source
    except Exception:
        pass

    return None


def relative_zip_path(file_path: Path, base_path: Path) -> str:
    """Return a relative path for ZIP entries, safe for NUL bytes.

    Args:
        file_path (Path): Path to the file.
        base_path (Path): Base directory path.

    Returns:
        str: Sanitized relative path string.

    """
    try:
        rel = file_path.relative_to(base_path)
    except ValueError:
        try:
            rel = os.path.relpath(str(file_path), str(base_path))
        except (ValueError, OSError):
            rel = file_path.name
    rel_path = "{}/{}".format(base_path.name, rel)
    rel_path = rel_path.replace("\\", "/").replace(os.sep, "/")
    rel_path = rel_path.replace("\x00", "_")
    return rel_path
