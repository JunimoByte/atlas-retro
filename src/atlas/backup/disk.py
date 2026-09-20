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

    def stat(self, follow_symlinks=False):
        if self._stat is None:
            if follow_symlinks:
                self._stat = os.stat(self.path)
            else:
                try:
                    self._stat = os.lstat(self.path)
                except AttributeError:
                    self._stat = os.stat(self.path)
        return self._stat


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
    """Return a scandir iterator with fallback for Python 3.4."""
    if _os_scandir is not None:
        return _os_scandir(str(path))
    return _FallbackScandir(path)


# =============================================================================
# FUNCTIONS
# =============================================================================


def safe_unlink(path: Path) -> None:
    """Safely delete a file, suppressing errors.

    Args:
        path (Path): Path to the file to delete.

    """
    try:
        if path.exists():
            path.unlink()
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
    return None


def relative_zip_path(file_path: Path, base_path: Path) -> str:
    """Return a relative path for ZIP entries, safe for NUL bytes.

    Args:
        file_path (Path): Path to the file.
        base_path (Path): Base directory path.

    Returns:
        str: Sanitized relative path string.

    """
    rel_path = "{}/{}".format(base_path.name, file_path.relative_to(base_path))
    rel_path = rel_path.replace(os.sep, "/")
    rel_path = rel_path.replace("\x00", "_")
    return rel_path
