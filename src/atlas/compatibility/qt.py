"""Atlas | Compatibility | Qt.

Unified Qt API layer. Detects and binds to the available
Qt implementation (PyQt4 or PyQt5) at import time.

All Atlas modules must import Qt classes through this
module rather than importing directly from PyQt.

Usage::

    from atlas.compatibility.qt import QtCore
    from atlas.compatibility.qt import QtGui
    from atlas.compatibility.qt import QtWidgets
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
import os
import sys

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

_TILING_WINDOW_MANAGERS = {
    "amethyst",
    "awesome",
    "berry",
    "bspwm",
    "cage",
    "dwl",
    "dwm",
    "exwm",
    "herbstluftwm",
    "hyprland",
    "i3",
    "leftwm",
    "lspwm",
    "niri",
    "notched",
    "qtile",
    "ratpoison",
    "river",
    "spectrwm",
    "stumpwm",
    "sway",
    "wingo",
    "worm",
    "xmonad",
}
_LINUX_SESSION_VARIABLES = (
    "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP",
    "DESKTOP_SESSION",
)

# =============================================================================
# LINUX ENVIRONMENT CONFIGURATION
# =============================================================================


def _configure_frozen_linux_environment() -> None:
    """Suppress GIO module conflicts when running as a frozen binary.

    PyInstaller bundles GLib from the build system (Ubuntu 20.04). On
    newer distros (Ubuntu 22.04+), GIO tries to load system modules
    compiled against a newer GLib, producing ``undefined symbol``
    errors. Setting ``GIO_MODULE_DIR`` to an empty string prevents GIO
    from searching the system module directory entirely.

    ``NO_AT_BRIDGE`` silences the ATK accessibility-bridge signature
    mismatch warning that appears on GNOME 46+ desktops.

    Only applied when the process is a frozen PyInstaller build so
    development runs are unaffected.

    """
    if not sys.platform.startswith("linux"):
        return
    if not getattr(sys, "frozen", False):
        return

    try:
        os.environ.setdefault("GIO_MODULE_DIR", "")
        os.environ.setdefault("NO_AT_BRIDGE", "1")
        LOGGER.debug(
            "Frozen Linux: GIO_MODULE_DIR and NO_AT_BRIDGE suppressed."
        )
    except Exception:
        LOGGER.error(
            "Failed to configure frozen Linux environment", exc_info=True
        )


def _is_tiling_window_manager() -> bool:
    """Return whether the current Linux session is a known tiling WM."""
    if not sys.platform.startswith("linux"):
        return False
    if "SWAYSOCK" in os.environ:
        return True

    session_name = " ".join(
        os.environ.get(variable, "").lower()
        for variable in _LINUX_SESSION_VARIABLES
    )
    return any(manager in session_name for manager in _TILING_WINDOW_MANAGERS)


def _configure_linux_environment() -> None:
    """Use XCB unless the user explicitly selects another Qt backend.

    This retains working X11/XWayland support for every desktop, including
    tiling window managers. ``QT_QPA_PLATFORM`` always takes precedence.
    """
    if not sys.platform.startswith("linux") or os.environ.get(
        "QT_QPA_PLATFORM"
    ):
        return

    os.environ["QT_QPA_PLATFORM"] = "xcb"
    LOGGER.debug("QT_QPA_PLATFORM set to 'xcb' for Linux.")


_configure_frozen_linux_environment()
_configure_linux_environment()

# =============================================================================
# QT BINDING RESOLUTION
# =============================================================================

QT_API = ""
"""Name of the active Qt binding ('PyQt4' or 'PyQt5')."""

try:
    try:
        import sip
        for _api in (
            "QString",
            "QVariant",
            "QDate",
            "QDateTime",
            "QTextStream",
            "QTime",
            "QUrl",
        ):
            try:
                sip.setapi(_api, 2)
            except (AttributeError, ValueError):
                pass
    except ImportError:
        pass

    from PyQt4 import QtCore, QtGui
    QtWidgets = QtGui
    if not hasattr(QtGui, "QGuiApplication"):
        QtGui.QGuiApplication = getattr(QtGui, "QApplication", None)
    QT_API = "PyQt4"
except ImportError:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: F401
        QT_API = "PyQt5"
    except ImportError as error:
        raise ImportError(
            "Atlas requires PyQt4 or PyQt5. Neither package was found."
        ) from error

if not hasattr(QtGui, "QGuiApplication"):
    QtGui.QGuiApplication = getattr(QtGui, "QApplication", None)

if not hasattr(QtCore.Qt, "HighDpiScaleFactorRoundingPolicy"):
    class _RoundingPolicy:
        Round = 1
        Ceil = 2
        Floor = 3
        RoundPreferFloor = 4
        PassThrough = 5
    try:
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy = _RoundingPolicy
    except (AttributeError, TypeError):
        pass

# Shim scoped enums for PyQt4 and PyQt5 compatibility
class _MetaScope(type):
    """Metaclass that proxies scoped enum attribute access to parent and target."""

    def __getattr__(cls, name):
        if hasattr(cls._parent, name):
            return getattr(cls._parent, name)
        if cls._target and hasattr(cls._target, name):
            return getattr(cls._target, name)
        raise AttributeError(
            "type object '{}' has no attribute '{}'".format(cls.__name__, name)
        )

    def __instancecheck__(cls, instance):
        if cls._target and isinstance(cls._target, type):
            return isinstance(instance, cls._target) or isinstance(instance, int)
        return isinstance(instance, int)


for _parent, _attr in [
    (QtCore.Qt, "WindowType"),
    (QtCore.Qt, "AlignmentFlag"),
    (QtCore.Qt, "Orientation"),
    (QtCore.Qt, "ItemDataRole"),
    (QtCore.Qt, "CheckState"),
    (QtWidgets.QSizePolicy, "Policy"),
    (QtWidgets.QDialogButtonBox, "StandardButton"),
    (QtWidgets.QMessageBox, "StandardButton"),
    (QtWidgets.QMessageBox, "Icon"),
]:
    _target = getattr(_parent, _attr, None)
    _wrapped = _MetaScope(
        _attr,
        (object,),
        {"_parent": _parent, "_target": _target},
    )
    try:
        setattr(_parent, _attr, _wrapped)
    except (AttributeError, TypeError):
        pass

if not hasattr(QtCore.Qt, "ColorScheme"):
    class _ColorScheme:
        Unknown = 0
        Light = 1
        Dark = 2
    try:
        QtCore.Qt.ColorScheme = _ColorScheme
    except (AttributeError, TypeError):
        pass

# Ensure both .exec_() and .exec() exist on application and dialog classes
for _target_cls in (QtWidgets.QApplication, QtWidgets.QDialog):
    if hasattr(_target_cls, "exec_") and not hasattr(_target_cls, "exec"):
        setattr(_target_cls, "exec", getattr(_target_cls, "exec_"))
    elif hasattr(_target_cls, "exec") and not hasattr(_target_cls, "exec_"):
        setattr(_target_cls, "exec_", getattr(_target_cls, "exec"))

# Safe translate shim for PyQt4 to avoid SIP overload errors on unicode strings
if QT_API == "PyQt4":
    _orig_translate = getattr(QtCore.QCoreApplication, "translate", None)
    if _orig_translate is not None:
        def _safe_translate(context, key, disambiguation=None, encoding=None, n=-1):
            try:
                utf8 = getattr(QtGui.QApplication, "UnicodeUTF8", None)
                if encoding is None and utf8 is not None:
                    return _orig_translate(context, key, disambiguation, utf8)
                elif encoding is not None:
                    return _orig_translate(context, key, disambiguation, encoding)
                return _orig_translate(context, key)
            except Exception:
                return key
        QtCore.QCoreApplication.translate = staticmethod(_safe_translate)

LOGGER.debug("Qt binding resolved: %s", QT_API)
