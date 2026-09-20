"""Atlas | Size Management.

File size formatting and disk space checking utilities for Atlas.
Provides human-readable size formatting and disk space validation.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
import math
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, Union

from atlas.backup.archive import get_zip_output_dir
from atlas.backup.disk import safe_scandir
from atlas.lib.read import load_json

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

# =============================================================================
# JSONS
# =============================================================================

try:
    BLACKLIST_JSON = load_json("blacklist.json")
    SKIP_FOLDERS = {f.lower() for f in BLACKLIST_JSON.get("SKIP_FOLDERS", [])}
except Exception as error:
    LOGGER.error("Failed to load blacklist.json: {}".format(error))
    raise RuntimeError(
        "Failed to load required blacklist configuration"
    ) from error

# =============================================================================
# CONSTANTS
# =============================================================================

MAX_SCAN_TIME = 300

# =============================================================================
# EXCEPTIONS
# =============================================================================


class ScanTimeoutError(RuntimeError):
    """Raised when a directory size scan exceeds MAX_SCAN_TIME.

    The size returned would be partial and unsafe to use for
    disk-space decisions so callers should treat this conservatively.
    """


class ScanError(RuntimeError):
    """Raised when a directory scan encounters inaccessible files or folders.

    Like timeouts, incomplete scans mean the size estimate is unreliable
    and should not be trusted for disk-space approval.
    """


# =============================================================================
# FUNCTIONS
# =============================================================================


def format_size(bytes_size: Union[int, float]) -> str:
    """Format a byte size into a human-readable string.

    Args:
        bytes_size (Union[int, float]): Size in bytes.

    Returns:
        str: Formatted string (e.g., "1.5 MB").

    """
    try:
        bytes_size = float(bytes_size)
        if bytes_size < 0 or math.isnan(bytes_size) or math.isinf(bytes_size):
            return "Invalid size"

        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        for i, unit in enumerate(units):
            if bytes_size < 1024 or i == len(units) - 1:
                if bytes_size.is_integer():
                    return "{} {}".format(int(bytes_size), unit)
                return "{:.2f}".format(bytes_size).rstrip("0").rstrip(
                    "."
                ) + " {}".format(unit)
            bytes_size /= 1024
    except (ValueError, TypeError):
        return "Unknown size"
    return "Unknown size"


def get_directory_size(  # noqa: C901
    path_str: Union[str, Path],
    cancel_callback: Union[None, callable] = None,
) -> int:
    """Recursively compute the total size of a directory.

    Uses ``os.scandir`` with a manual stack for performance. On Windows,
    ``DirEntry.stat()`` reuses the result from ``FindNextFile``, avoiding
    extra syscalls. Symlink check is folded into
    ``is_file(follow_symlinks=False)``.

    Args:
        path_str (Union[str, Path]): Path to the directory.
        cancel_callback (Optional[callable]): Callback to check for
            cancellation.

    Returns:
        int: Total size in bytes.

    """
    total = 0
    start_time = time.monotonic()

    try:
        root = Path(os.path.abspath(str(path_str)))
    except Exception:
        root = Path(path_str)

    if not root.exists() or not root.is_dir():
        return 0

    stack = [str(root)]

    while stack:
        if cancel_callback and cancel_callback():
            raise InterruptedError("Directory size scan cancelled by user")

        current_dir = stack.pop()

        if time.monotonic() - start_time > MAX_SCAN_TIME:
            raise ScanTimeoutError(
                "Directory scan timed out after {}s: {}".format(
                    MAX_SCAN_TIME, path_str
                )
            )

        try:
            with safe_scandir(current_dir) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name.lower() not in SKIP_FOLDERS:
                                stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError as error:
                        LOGGER.debug(
                            "Error accessing %s: %s", entry.path, error
                        )
        except OSError as error:
            LOGGER.debug("Cannot scan directory %s: %s", current_dir, error)

    return total


def _get_free_disk_space(path_str: str) -> Optional[int]:
    """Get free disk space in bytes for path, with Windows XP fallbacks."""
    try:
        _, _, free = shutil.disk_usage(str(path_str))
        return free
    except OSError:
        # Fallback to drive root (e.g. C:\) if subfolder path fails
        try:
            drive = os.path.splitdrive(str(path_str))[0]
            if drive:
                drive_root = drive + "\\" if not drive.endswith("\\") else drive
                if drive_root != str(path_str):
                    _, _, free = shutil.disk_usage(drive_root)
                    return free
        except OSError:
            pass
    except Exception as error:
        LOGGER.debug("disk_usage error on %s: %s", path_str, error)

    return None


def check_disk_space(
    estimated_size_bytes: int, output_path: Union[str, Path, None] = None
) -> Tuple[bool, str]:
    """Check if there's sufficient disk space for the backup.

    Args:
        estimated_size_bytes (int): Estimated backup size in bytes.
        output_path (Union[str, Path, None]): Optional custom output path.

    Returns:
        Tuple[bool, str]: (True if sufficient space,
            Formatted available space).

    """
    if estimated_size_bytes < 0:
        LOGGER.warning(
            "check_disk_space called with negative size: %d",
            estimated_size_bytes,
        )
        return False, "Unknown"

    try:
        if output_path:
            output_dir = Path(os.path.abspath(str(output_path)))
        else:
            output_dir = get_zip_output_dir()

        output_dir_str = str(output_dir)
        if not os.path.isdir(output_dir_str):
            os.makedirs(output_dir_str, exist_ok=True)
        free = _get_free_disk_space(output_dir_str)
        if free is None:
            LOGGER.warning("Could not determine free disk space for %s", output_dir)
            return False, "Unknown"

        required_space = int(estimated_size_bytes * 1.5)
        has_sufficient_space = free >= required_space

        return has_sufficient_space, format_size(free)

    except OSError as error:
        LOGGER.error("Error checking disk space: {}".format(error))
        return False, "Unknown"


def create_output_dir(output_path: Union[str, Path, None] = None) -> Path:
    """Create the output directory after disk space check.

    Args:
        output_path (Union[str, Path, None]): Optional custom output path.

    Returns:
        Path: Path to the created output directory.

    """
    if output_path:
        output_dir = Path(os.path.abspath(str(output_path)))
    else:
        output_dir = get_zip_output_dir()

    try:
        output_dir_str = str(output_dir)
        if not os.path.isdir(output_dir_str):
            os.makedirs(output_dir_str, exist_ok=True)
        LOGGER.info("Output directory ready: %s", output_dir)
    except OSError as error:
        LOGGER.error("Failed to create output directory: %s", error)
        raise
    return output_dir
