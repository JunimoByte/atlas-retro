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
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from atlas.backup import archive as Archive  # noqa: N812
from atlas.display.popup import show_warning

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

# =============================================================================
# DESKTOP ENVIRONMENT DETECTION
# =============================================================================

_TILING_WINDOW_MANAGERS = {
    "amethyst", "awesome", "berry", "bspwm", "cage", "dwl", "dwm",
    "exwm", "herbstluftwm", "hyprland", "i3", "leftwm", "lspwm",
    "niri", "notched", "qtile", "ratpoison", "river", "spectrwm",
    "stumpwm", "sway", "wingo", "worm", "xmonad",
}

_LINUX_SESSION_VARIABLES = (
    "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP",
    "DESKTOP_SESSION",
)


def _is_tiling_window_manager() -> bool:
    """Return True if the current Linux session is a known tiling WM."""
    if not sys.platform.startswith(
        ("linux", "freebsd", "openbsd", "netbsd", "dragonfly")
    ):
        return False
    if "SWAYSOCK" in os.environ or "I3SOCK" in os.environ:
        return True
    session = " ".join(
        os.environ.get(v, "").lower() for v in _LINUX_SESSION_VARIABLES
    )
    return any(wm in session for wm in _TILING_WINDOW_MANAGERS)


def _is_kde() -> bool:
    """Return True if the current desktop environment is KDE Plasma."""
    desktop = ":".join(
        os.environ.get(v, "") for v in _LINUX_SESSION_VARIABLES
    ).lower()
    return (
        "kde" in desktop
        or "plasma" in desktop
        or "KDE_SESSION_VERSION" in os.environ
        or "KDE_FULL_SESSION" in os.environ
    )


def _is_mate() -> bool:
    """Return True if the current desktop environment is MATE."""
    desktop = ":".join(
        os.environ.get(v, "") for v in _LINUX_SESSION_VARIABLES
    ).lower()
    return "mate" in desktop or "MATE_DESKTOP_SESSION_ID" in os.environ


def _is_xfce() -> bool:
    """Return True if the current desktop environment is XFCE."""
    desktop = ":".join(
        os.environ.get(v, "") for v in _LINUX_SESSION_VARIABLES
    ).lower()
    return "xfce" in desktop or "xubuntu" in desktop


# =============================================================================
# ENVIRONMENT SANITIZATION
# =============================================================================


def _get_clean_desktop_environment() -> Dict[str, str]:
    """Sanitize environment variables for spawning desktop file managers.

    Frozen builds (PyInstaller/AppImage) and Atlas runtime settings
    modify variables such as ``LD_LIBRARY_PATH``, ``QT_PLUGIN_PATH``,
    ``QT_QPA_PLATFORM``, and ``GIO_MODULE_DIR``. If inherited by system
    utilities like ``xdg-open`` or KDE Dolphin, these overrides cause
    severe ABI mismatches, missing platform plugins, or crashes.

    Returns:
        Dict[str, str]: A cleaned copy of ``os.environ``.

    """
    env = os.environ.copy()

    # Restore the original system library path if PyInstaller modified it.
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env.pop("LD_LIBRARY_PATH_ORIG")
    else:
        env.pop("LD_LIBRARY_PATH", None)

    # Remove Qt, GLib, and loader overrides so child processes use host libs.
    for var in (
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "QT_QPA_PLATFORM",
        "QT_STYLE_OVERRIDE",
        "QML_IMPORT_PATH",
        "QML2_IMPORT_PATH",
        "GIO_MODULE_DIR",
        "NO_AT_BRIDGE",
        "LD_PRELOAD",
    ):
        env.pop(var, None)

    # Remove Python overrides so host Python helpers execute cleanly.
    for var in ("PYTHONPATH", "PYTHONHOME", "_MEIPASS2"):
        env.pop(var, None)

    return env


# Alias for backward compatibility with existing tests
_clean_posix_environ = _get_clean_desktop_environment


# =============================================================================
# CANDIDATE RESOLUTION
# =============================================================================


def _get_linux_file_manager_candidates(
    folder_path: Path,
) -> List[List[str]]:
    """Return ordered command candidates to open a folder on Linux/POSIX.

    Detects the active desktop session (prioritizing KDE, MATE, XFCE,
    or GNOME tools accordingly) and includes comprehensive fallbacks
    for older distributions (gvfs-open, gnome-open, kde-open) and
    lightweight/retro window managers.

    Args:
        folder_path (Path): Path to the folder to open.

    Returns:
        List[List[str]]: Candidate command arguments.

    """
    target = str(folder_path)
    candidates = [["xdg-open", target]]

    if _is_kde():
        candidates.extend([
            ["dolphin", target],
            ["kde-open6", target],
            ["kde-open5", target],
            ["kde-open", target],
            ["kioclient6", "exec", target],
            ["kioclient5", "exec", target],
            ["kioclient", "exec", target],
            ["kfmclient", "openURL", target],
            ["konqueror", target],
            ["gio", "open", target],
            ["gvfs-open", target],
        ])
    elif _is_mate():
        candidates.extend([
            ["caja", target],
            ["mate-open", target],
            ["gio", "open", target],
            ["gvfs-open", target],
        ])
    elif _is_xfce():
        candidates.extend([
            ["thunar", target],
            ["exo-open", target],
            ["gio", "open", target],
            ["gvfs-open", target],
        ])

    # General / default ordering matching user app architecture + retro tools
    candidates.extend([
        ["gio", "open", target],
        ["gvfs-open", target],       # Ubuntu 14.04 / Debian 8 (GLib < 2.50)
        ["dolphin", target],
        ["nautilus", target],
        ["thunar", target],
        ["pcmanfm", target],
        ["caja", target],
        ["nemo", target],
        ["pcmanfm-qt", target],
        ["exo-open", target],
        ["mate-open", target],
        ["gnome-open", target],
        ["kde-open", target],
        ["konqueror", target],
        ["xfe", target],
        ["spacefm", target],
        ["rox-filer", target],
        ["rox", target],
        ["doublecmd", target],
        ["krusader", target],
    ])

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for cmd in candidates:
        key = tuple(cmd)
        if key not in seen:
            seen.add(key)
            deduped.append(cmd)

    return deduped


# =============================================================================
# PROCESS EXECUTION
# =============================================================================


def _open_posix_cmd(cmd: List[str], env: Dict[str, str]) -> bool:
    """Attempt to launch a command non-blocking and detached.

    Args:
        cmd (List[str]): Command arguments.
        env (Dict[str, str]): Cleaned environment variables.

    Returns:
        bool: True if process was spawned or completed successfully,
            False if spawning failed or exited immediately with error.

    """
    try:
        kwargs = {
            "env": env,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if hasattr(os, "setsid"):
            kwargs["preexec_fn"] = os.setsid

        proc = subprocess.Popen(cmd, **kwargs)

        # For launcher scripts that exit immediately (xdg-open, gio, etc.),
        # give a tiny moment (50ms) to detect immediate launch failures.
        exe = cmd[0]
        if exe in (
            "xdg-open", "gio", "gvfs-open",
            "gnome-open", "mate-open", "exo-open",
        ):
            try:
                proc.wait(timeout=0.05)
            except Exception:
                pass
            returncode = proc.poll()
            if (
                returncode is not None
                and isinstance(returncode, int)
                and returncode != 0
            ):
                LOGGER.debug(
                    "Opener '%s' failed (exit code %s)", exe, returncode
                )
                return False

        return True
    except Exception as err:
        LOGGER.debug("Failed to launch %s: %s", cmd[0], err)
        return False


def _run_linux_open(folder_path: Path) -> bool:
    """Execute candidate commands to open a folder on Linux/POSIX.

    Iterates through candidate file openers, executing each with a
    sanitized desktop environment until one launches successfully.

    Args:
        folder_path (Path): Path to the folder to open.

    Returns:
        bool: True if a file manager was successfully spawned,
            False otherwise.

    """
    env = _get_clean_desktop_environment()
    candidates = _get_linux_file_manager_candidates(folder_path)

    for cmd in candidates:
        exe = cmd[0]
        # Always attempt xdg-open; for other tools check binary
        # presence in PATH if PATH is set.
        if (
            exe != "xdg-open"
            and env.get("PATH")
            and shutil.which(exe, path=env.get("PATH")) is None
        ):
            continue

        if _open_posix_cmd(cmd, env):
            LOGGER.info("Opened folder using %s: %s", exe, folder_path)
            return True

    LOGGER.warning(
        "Could not open folder '%s' with any available file manager.",
        folder_path,
    )
    return False


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

    # 2. Iterate through candidate desktop openers
    if _run_linux_open(folder_path):
        return

    raise RuntimeError("Could not open folder on POSIX/BSD system")


def _open_windows(folder_path: Path) -> None:
    """Open a folder on Windows using os.startfile with explorer fallback."""
    start = getattr(os, "startfile", None)
    if start is not None:
        try:
            start(str(folder_path))
            LOGGER.info("Opened folder: %s", folder_path)
            return
        except Exception as err:
            LOGGER.debug("os.startfile failed: %s", err)

    try:
        subprocess.Popen(["explorer.exe", str(folder_path)])
        LOGGER.info("Opened folder via explorer.exe: %s", folder_path)
    except Exception as err:
        LOGGER.warning("explorer.exe fallback failed: %s", err)
        raise RuntimeError("Could not open folder on Windows")


def _open_folder_platform(folder_path: Path) -> None:
    """Open a folder using the platform's native file manager.

    Dispatches to the appropriate OS command:
    - Windows: ``os.startfile`` with ``explorer.exe`` fallback.
    - macOS:   ``open``
    - Linux/BSD: Qt ``QDesktopServices.openUrl``, ``xdg-open``, or
      desktop file managers (``dolphin``, ``caja``, ``thunar``,
      ``nautilus``, ``pcmanfm``, ``gvfs-open``, etc.) with
      sanitized environment and detached process spawning.

    Args:
        folder_path (Path): Absolute path to open.

    """
    system = platform.system().lower()

    if system == "windows":
        _open_windows(folder_path)
    elif system == "darwin":
        subprocess.Popen(["open", str(folder_path)])
        LOGGER.info("Opened folder: %s", folder_path)
    else:
        _open_posix(folder_path)


# =============================================================================
# PUBLIC API
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
        LOGGER.debug("Dispatched open folder request: %s", folder)

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
