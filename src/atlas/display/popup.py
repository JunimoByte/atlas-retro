"""Atlas | Display | Popup.

Flexible popup dialog system for Atlas.
Supports various message types with proper theming.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import logging
import sys
from typing import Optional

from atlas.compatibility.qt import QtCore, QtGui, QtWidgets
from atlas.lib.themes import apply as _apply_theme
from atlas.lib.themes import icon as _apply_icon

# =============================================================================
# LOGGING
# =============================================================================

LOGGER = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

_MB = QtWidgets.QMessageBox

_ICON_INFO = getattr(_MB.Icon, "Information", getattr(_MB, "Information", 1))
_ICON_WARN = getattr(_MB.Icon, "Warning", getattr(_MB, "Warning", 2))
_ICON_CRIT = getattr(_MB.Icon, "Critical", getattr(_MB, "Critical", 3))
_ICON_QUES = getattr(_MB.Icon, "Question", getattr(_MB, "Question", 4))

_BTN_OK = getattr(_MB.StandardButton, "Ok", getattr(_MB, "Ok", 1024))
_BTN_CANCEL = getattr(
    _MB.StandardButton, "Cancel", getattr(_MB, "Cancel", 4194304)
)
_BTN_YES = getattr(_MB.StandardButton, "Yes", getattr(_MB, "Yes", 16384))
_BTN_NO = getattr(_MB.StandardButton, "No", getattr(_MB, "No", 65536))

ICON_MAP = {
    "INFORMATION": _ICON_INFO,
    "WARNING": _ICON_WARN,
    "CRITICAL": _ICON_CRIT,
    "QUESTION": _ICON_QUES,
}

BUTTON_MAP = {
    "ACKNOWLEDGE": _BTN_OK,
    "CONFIRM_DECLINE": _BTN_YES | _BTN_NO,
    "ACKNOWLEDGE_CANCEL": _BTN_OK | _BTN_CANCEL,
    "CONFIRM_DECLINE_CANCEL": _BTN_YES | _BTN_NO | _BTN_CANCEL,
}

DEFAULT_BUTTON = {
    "ACKNOWLEDGE": _BTN_OK,
    "CONFIRM_DECLINE": _BTN_YES,
    "ACKNOWLEDGE_CANCEL": _BTN_OK,
    "CONFIRM_DECLINE_CANCEL": _BTN_YES,
}

DEFAULT_STAY_ON_TOP = True

# =============================================================================
# FUNCTIONS
# =============================================================================


def show(
    title: str,
    text: str,
    icon: str = "INFORMATION",
    buttons: str = "ACKNOWLEDGE",
    informative_text: Optional[str] = None,
    detailed_text: Optional[str] = None,
    stay_on_top: bool = DEFAULT_STAY_ON_TOP,
) -> int:
    """Show a flexible popup dialog with theming support.

    Args:
        title: Window title.
        text: Main message text.
        icon: Icon type (INFORMATION, WARNING, CRITICAL, QUESTION).
        buttons: Button group type.
        informative_text: Optional informative text.
        detailed_text: Optional detailed text.
        stay_on_top: Whether the window stays on top.

    Returns:
        Result of the message box execution.

    """
    try:
        existing_app = QtWidgets.QApplication.instance()
        app = existing_app or QtWidgets.QApplication(sys.argv)
        if existing_app is None:
            app.setQuitOnLastWindowClosed(True)

        msg = QtWidgets.QMessageBox()
        msg.setObjectName("PopupMessageBox")
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(ICON_MAP.get(icon, _ICON_INFO))
        msg.setStandardButtons(
            BUTTON_MAP.get(buttons, _BTN_OK)
        )
        msg.setDefaultButton(
            DEFAULT_BUTTON.get(
                buttons, _BTN_OK
            )
        )

        if informative_text:
            msg.setInformativeText(informative_text)
        if detailed_text:
            msg.setDetailedText(detailed_text)

        flags = (
            QtCore.Qt.WindowType.Dialog
            | QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint
        )
        if stay_on_top:
            flags |= QtCore.Qt.WindowType.WindowStaysOnTopHint
        msg.setWindowFlags(flags)

        for button in msg.buttons():
            button.setIcon(QtGui.QIcon())

        try:
            _apply_theme(msg)
            _apply_icon(msg)
        except Exception as error:
            LOGGER.debug("Theme application failed: %s", error)

        exec_fn = getattr(msg, "exec_", None) or getattr(msg, "exec")
        return exec_fn()
    except Exception as error:
        LOGGER.error("Failed to show popup: %s", error, exc_info=True)
        return int(_BTN_OK)


# =============================================================================
# WRAPPERS
# =============================================================================


def show_warning(
    title: str, message: str, details: Optional[str] = None
) -> None:
    """Show a warning popup.

    Args:
        title: Window title.
        message: Warning message.
        details: Additional details.

    """
    show(
        title,
        "<b>{}</b>".format(message),
        icon="WARNING",
        buttons="ACKNOWLEDGE",
        informative_text=details,
        stay_on_top=True,
    )


def show_error(
    title: str, message: str, details: Optional[str] = None
) -> None:
    """Show a critical error popup.

    Args:
        title: Window title.
        message: Error message.
        details: Additional details.

    """
    show(
        title,
        "<b>{}</b>".format(message),
        icon="CRITICAL",
        buttons="ACKNOWLEDGE",
        informative_text=details,
        stay_on_top=True,
    )


def show_info(title: str, message: str, details: Optional[str] = None) -> int:
    """Show an informational popup.

    Args:
        title: Window title.
        message: Informational message.
        details: Additional details.

    Returns:
        Result of the message box execution.

    """
    return show(
        title,
        "<b>{}</b>".format(message),
        icon="INFORMATION",
        buttons="ACKNOWLEDGE",
        informative_text=details,
        stay_on_top=False,
    )


def show_question(
    title: str,
    message: str,
    details: Optional[str] = None,
    cancel_button: bool = False,
) -> bool:
    """Show a question popup with Yes/No (and optional Cancel) buttons.

    Args:
        title: Window title.
        message: Question text.
        details: Additional details.
        cancel_button: Whether to include Cancel button.

    Returns:
        True if user clicked Yes, False otherwise.

    """
    buttons = "CONFIRM_DECLINE_CANCEL" if cancel_button else "CONFIRM_DECLINE"
    return (
        show(
            title,
            "<b>{}</b>".format(message),
            icon="QUESTION",
            buttons=buttons,
            informative_text=details,
            stay_on_top=False,
        )
        == _BTN_YES
    )
