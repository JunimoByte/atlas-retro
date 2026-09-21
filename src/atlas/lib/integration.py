"""Atlas | Packages | Integration.

User-facing operating system integration helpers for Atlas.

Provides safe, cross-platform access to desktop features such as
opening folders in the system file manager.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from atlas.backup import archive as Archive  # noqa: N812
from atlas.display.popup import show_warning

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

# =============================================================================
# FUNCTIONS
# =============================================================================


def open_folder(folder_path: Optional[Path] = None) -> None:
    """Resolve and open the selected folder in the file manager.

    If no folder is provided, attempt to open the archive output
    directory.  Display a user-facing warning if the folder does
    not exist or cannot be opened automatically.

    Args:
        folder_path (Optional[Path]): Specific path to open.
            Defaults to None.

    """
    try:
        if folder_path is None:
            # Use the raw stored path or compute the default without calling
            # get_zip_output_dir(), which always calls mkdir() and would
            # silently recreate a folder the user just deleted.
            folder_path = (
                Archive.ZIP_OUTPUT_DIR
                if Archive.ZIP_OUTPUT_DIR is not None
                else Archive._get_default_output_dir()
            )

        if folder_path is None:
            LOGGER.warning("No folder path available to open")
            show_warning(
                title="Caution",
                message="Folder Not Found",
                details=(
                    "The selected folder could not be "
                    "found.\n\n"
                    "It may have been moved or deleted."
                ),
            )
            return

        try:
            folder = Path(os.path.abspath(str(folder_path)))
        except Exception:
            folder = folder_path

        if not folder.exists():
            LOGGER.warning("Selected folder missing: %s", folder)
            show_warning(
                title="Caution",
                message="Folder Not Found",
                details=(
                    "The selected folder could not be "
                    "found.\n\n"
                    "It may have been moved or deleted."
                ),
            )
            return

        _open_folder_platform(folder)
        LOGGER.info("Opened folder: %s", folder)

    except FileNotFoundError as error:
        LOGGER.warning(
            "Failed to open folder: %s",
            error,
            exc_info=True,
        )
        show_warning(
            title="Caution",
            message="Failed to Open Folder",
            details=(
                "Atlas could not open the selected folder "
                "automatically.\n\n"
                "Please open it manually using your file "
                "manager."
            ),
        )

    except Exception as error:
        LOGGER.warning(
            "Failed to open folder: %s",
            error,
            exc_info=True,
        )
        show_warning(
            title="Caution",
            message="Failed to Open Folder",
            details=(
                "Atlas ran into an error while trying to "
                "open the selected folder.\n\n"
                "Please try again later."
            ),
        )


def _clean_posix_environ() -> Dict[str, str]:
    """Return environment copy with PyInstaller and loader vars stripped."""
    env = os.environ.copy()
    for var in (
        "LD_LIBRARY_PATH",
        "LD_PRELOAD",
        "PYTHONPATH",
        "PYTHONHOME",
        "_MEIPASS2",
    ):
        env.pop(var, None)
    return env


def _open_posix_cmd(cmd: List[str], env: Dict[str, str]) -> bool:
    """Attempt to launch a command non-blocking and detached."""
    try:
        kwargs = {
            "env": env,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if hasattr(os, "setsid"):
            kwargs["preexec_fn"] = os.setsid
        subprocess.Popen(cmd, **kwargs)
        return True
    except Exception as err:
        LOGGER.debug("Failed to launch %s: %s", cmd[0], err)
        return False


def _open_windows(folder_path: Path) -> None:
    """Open a folder on Windows using os.startfile with explorer fallback."""
    start = getattr(os, "startfile", None)
    if start is not None:
        try:
            start(str(folder_path))
            return
        except Exception as err:
            LOGGER.debug("os.startfile failed: %s", err)

    try:
        subprocess.Popen(["explorer.exe", str(folder_path)])
    except Exception as err:
        LOGGER.warning("explorer.exe fallback failed: %s", err)
        raise RuntimeError("Could not open folder on Windows")


def _open_posix(folder_path: Path) -> None:
    """Open a folder on POSIX/BSD with multi-stage fallbacks."""
    # 1. First try Qt's native QDesktopServices if available
    try:
        from atlas.compatibility.qt import QtCore, QtGui

        url = QtCore.QUrl.fromLocalFile(str(folder_path))
        if QtGui.QDesktopServices.openUrl(url):
            LOGGER.debug("Opened folder via QDesktopServices: %s", folder_path)
            return
    except Exception as err:
        LOGGER.debug("QDesktopServices.openUrl failed: %s", err)

    # 2. Try xdg-open with sanitized environment (detached process)
    env = _clean_posix_environ()
    if _open_posix_cmd(["xdg-open", str(folder_path)], env):
        return

    # 3. Fallback to common desktop file managers
    for fm in (
        "nautilus", "caja", "thunar", "dolphin", "pcmanfm", "nemo", "gio"
    ):
        cmd = (
            ["gio", "open", str(folder_path)]
            if fm == "gio"
            else [fm, str(folder_path)]
        )
        if _open_posix_cmd(cmd, env):
            LOGGER.info("Opened folder via fallback file manager: %s", fm)
            return

    raise RuntimeError("Could not open folder on POSIX/BSD system")


def _open_folder_platform(folder_path: Path) -> None:
    """Open a folder using the platform's native file manager.

    Dispatches to the appropriate OS command:
    - Windows: ``os.startfile`` with ``explorer.exe`` fallback.
    - macOS:   ``open``
    - Linux/BSD: Qt ``QDesktopServices.openUrl``, ``xdg-open``, or
      desktop file managers (``nautilus``, ``caja``, etc.) with
      detached process spawning.

    Args:
        folder_path (Path): Absolute path to open.

    """
    system = platform.system().lower()

    if system == "windows":
        _open_windows(folder_path)
    elif system == "darwin":
        subprocess.Popen(["open", str(folder_path)])
    else:
        _open_posix(folder_path)
