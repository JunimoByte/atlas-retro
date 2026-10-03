"""Tests for Qt compatibility layer focusing on PyQt4 and PyQt5 switching."""

import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest


def test_qt_resolution_raises_when_neither_pyqt4_nor_pyqt5_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify ImportError is raised when neither PyQt4 nor PyQt5 is present."""
    # Prevent importing PyQt4 and PyQt5
    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.startswith(("PyQt4", "PyQt5")):
            raise ImportError("No module named {}".format(name))
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    sys.modules.pop("atlas.compatibility.qt", None)

    with pytest.raises(ImportError) as exc_info:
        importlib.import_module("atlas.compatibility.qt")

    assert "Atlas requires PyQt4 or PyQt5" in str(exc_info.value)
    sys.modules.pop("atlas.compatibility.qt", None)


def test_qt_resolution_switches_to_pyqt4_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify PyQt4 is selected as primary toolkit when present."""
    mock_pyqt4 = MagicMock()
    mock_qtcore = MagicMock()
    mock_qtgui = MagicMock()
    mock_pyqt4.QtCore = mock_qtcore
    mock_pyqt4.QtGui = mock_qtgui

    # Simulate flat enums on Qt and QMessageBox
    mock_qtcore.Qt = type(
        "Qt", (), {"Dialog": 3, "AlignTop": 32, "Horizontal": 1}
    )()
    mock_qtgui.QMessageBox = type(
        "QMessageBox", (), {"Ok": 1024, "Information": 1}
    )()
    mock_qtgui.QSizePolicy = type("QSizePolicy", (), {"Expanding": 7})()
    mock_qtgui.QDialogButtonBox = type("QDialogButtonBox", (), {"Ok": 1024})()
    mock_qtgui.QApplication = type(
        "QApplication", (), {"exec_": lambda self: 0}
    )()
    mock_qtgui.QDialog = type("QDialog", (), {"exec_": lambda self: 0})()

    monkeypatch.setitem(sys.modules, "PyQt4", mock_pyqt4)
    monkeypatch.setitem(sys.modules, "PyQt4.QtCore", mock_qtcore)
    monkeypatch.setitem(sys.modules, "PyQt4.QtGui", mock_qtgui)
    sys.modules.pop("atlas.compatibility.qt", None)

    qt_mod = importlib.import_module("atlas.compatibility.qt")

    try:
        assert qt_mod.QT_API == "PyQt4"
        assert qt_mod.QtWidgets is qt_mod.QtGui
        # Verify scoped enum shims work on PyQt4
        assert qt_mod.QtCore.Qt.WindowType.Dialog == 3
        assert qt_mod.QtCore.Qt.AlignmentFlag.AlignTop == 32
        assert qt_mod.QtCore.Qt.Orientation.Horizontal == 1
        assert qt_mod.QtWidgets.QMessageBox.StandardButton.Ok == 1024
        assert qt_mod.QtWidgets.QMessageBox.Icon.Information == 1
        # Verify exec alias exists
        assert hasattr(qt_mod.QtWidgets.QApplication, "exec")
        assert hasattr(qt_mod.QtWidgets.QDialog, "exec")
    finally:
        sys.modules.pop("atlas.compatibility.qt", None)


def test_active_qt_binding_is_pyqt4_or_pyqt5() -> None:
    """Verify current environment resolves to either PyQt4 or PyQt5."""
    sys.modules.pop("atlas.compatibility.qt", None)
    qt_mod = importlib.import_module("atlas.compatibility.qt")
    assert qt_mod.QT_API in ("PyQt4", "PyQt5")
    assert qt_mod.QT_API != "PyQt6"


def test_configure_linux_environment_respects_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify existing QT_QPA_PLATFORM is preserved."""
    from atlas.compatibility import qt

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setitem(os.environ, "QT_QPA_PLATFORM", "offscreen")

    qt._configure_linux_environment()
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"


def test_configure_linux_environment_wayland_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify pure Wayland sessions configure wayland;xcb fallback."""
    from atlas.compatibility import qt

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delitem(os.environ, "QT_QPA_PLATFORM", raising=False)
    monkeypatch.setitem(os.environ, "WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.delitem(os.environ, "DISPLAY", raising=False)

    qt._configure_linux_environment()
    assert os.environ["QT_QPA_PLATFORM"] == "wayland;xcb"


def test_configure_linux_environment_xcb_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify standard X11/XWayland sessions configure xcb;wayland fallback."""
    from atlas.compatibility import qt

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delitem(os.environ, "QT_QPA_PLATFORM", raising=False)
    monkeypatch.setitem(os.environ, "DISPLAY", ":0")
    monkeypatch.delitem(os.environ, "WAYLAND_DISPLAY", raising=False)

    qt._configure_linux_environment()
    assert os.environ["QT_QPA_PLATFORM"] == "xcb;wayland"


def test_configure_frozen_linux_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify frozen Linux session sets GIO_MODULE_DIR and NO_AT_BRIDGE."""
    from atlas.compatibility import qt

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delitem(os.environ, "GIO_MODULE_DIR", raising=False)
    monkeypatch.delitem(os.environ, "NO_AT_BRIDGE", raising=False)

    qt._configure_frozen_linux_environment()
    assert os.environ.get("GIO_MODULE_DIR") == ""
    assert os.environ.get("NO_AT_BRIDGE") == "1"
