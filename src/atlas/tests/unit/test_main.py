"""Atlas | Tests | Main.

Unit tests for main.py covering routing, version flag, and error handling.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import sys
from unittest.mock import patch

import pytest

from atlas import main

# =============================================================================
# TESTS — Routing & Version Flag
# =============================================================================


def test_main_version_flag(capsys: pytest.CaptureFixture) -> None:
    """Verify --version prints the version and exits cleanly."""
    with patch.object(sys, "argv", ["atlas", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Atlas 1.2" in captured.out or "Atlas 1.2" in captured.err


def test_main_routes_to_cli() -> None:
    """Verify --cli flag routes execution to run_cli."""
    with patch.object(sys, "argv", ["atlas", "--cli"]):
        with patch("atlas.cli.run_cli", return_value=0) as mock_cli:
            with pytest.raises(SystemExit) as exc_info:
                main.main()
            assert exc_info.value.code == 0
            mock_cli.assert_called_once()


def test_main_routes_to_gui() -> None:
    """Verify default invocation routes execution to run_gui."""
    with patch.object(sys, "argv", ["atlas"]):
        with patch("atlas.gui.run_gui", return_value=0) as mock_gui:
            with pytest.raises(SystemExit) as exc_info:
                main.main()
            assert exc_info.value.code == 0
            mock_gui.assert_called_once()


def test_main_routes_to_cli_when_no_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify headless POSIX environment without DISPLAY falls back to CLI."""
    monkeypatch.setattr(main.os, "name", "posix")
    monkeypatch.setattr(main.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    with patch.object(sys, "argv", ["atlas"]):
        with patch("atlas.cli.run_cli", return_value=0) as mock_cli:
            with pytest.raises(SystemExit) as exc_info:
                main.main()
            assert exc_info.value.code == 0
            mock_cli.assert_called_once()


def test_main_routes_to_cli_when_pyqt_missing() -> None:
    """Verify missing PyQt falls back to CLI."""
    with patch.object(sys, "argv", ["atlas"]):
        with patch(
            "atlas.gui.run_gui",
            side_effect=ImportError("No module named 'PyQt4'"),
        ):
            with patch("atlas.cli.run_cli", return_value=0) as mock_cli:
                with pytest.raises(SystemExit) as exc_info:
                    main.main()
                assert exc_info.value.code == 0
                mock_cli.assert_called_once()
