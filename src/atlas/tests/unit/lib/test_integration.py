"""Atlas | Tests | Packages | Integration.

Unit tests for integration.py OS folder helpers.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from atlas.backup import archive as Archive  # noqa: N812
from atlas.lib import integration

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_folder(tmp_path: Path) -> Path:
    """Create a temporary folder for testing."""
    folder = tmp_path / "test_folder"
    folder.mkdir()
    return folder


@pytest.fixture
def missing_folder(tmp_path: Path) -> Path:
    """Provide a folder path that does not exist."""
    return tmp_path / "missing_folder"


@pytest.fixture
def mock_warning(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock show_warning to verify warning messages."""
    mock = MagicMock()
    monkeypatch.setattr("atlas.lib.integration.show_warning", mock)
    return mock


# =============================================================================
# TESTS — open_folder
# =============================================================================


def test_open_folder_with_valid_path(temp_folder: Path) -> None:
    """Verify that valid folders are opened without errors."""
    with patch("atlas.lib.integration._open_folder_platform") as mock_open:
        integration.open_folder(temp_folder)
        mock_open.assert_called_once_with(temp_folder)


def test_open_folder_none_uses_zip_output_dir(
    tmp_path: Path,
) -> None:
    """Verify fallback to ZIP_OUTPUT_DIR from a prior run."""
    fake_dir = tmp_path / "archive_dir"
    fake_dir.mkdir()
    with patch.object(Archive, "ZIP_OUTPUT_DIR", fake_dir):
        with patch("atlas.lib.integration._open_folder_platform") as mock_open:
            integration.open_folder(None)
            mock_open.assert_called_once_with(fake_dir)


def test_open_folder_none_uses_default_output_dir(
    tmp_path: Path,
) -> None:
    """Verify fallback to _get_default_output_dir."""
    fake_dir = tmp_path / "default_dir"
    fake_dir.mkdir()
    with patch.object(Archive, "ZIP_OUTPUT_DIR", None):
        with patch.object(
            Archive, "_get_default_output_dir", return_value=fake_dir
        ):
            with patch(
                "atlas.lib.integration._open_folder_platform"
            ) as mock_open:
                integration.open_folder(None)
                mock_open.assert_called_once_with(fake_dir)


def test_open_folder_none_and_archive_none(
    mock_warning: MagicMock,
) -> None:
    """Verify warning is shown if no path resolves."""
    missing = Path("/tmp/_atlas_nonexistent_12345")
    with patch.object(Archive, "ZIP_OUTPUT_DIR", None):
        with patch.object(
            Archive, "_get_default_output_dir", return_value=missing
        ):
            integration.open_folder(None)
            mock_warning.assert_called_once()
            args = mock_warning.call_args[1]
            assert "Folder Not Found" in args["message"]


def test_open_folder_missing_folder(
    missing_folder: Path, mock_warning: MagicMock
) -> None:
    """Verify that a warning is shown for nonexistent folders."""
    integration.open_folder(missing_folder)
    mock_warning.assert_called_once()
    args = mock_warning.call_args[1]
    assert "Folder Not Found" in args["message"]


def test_clean_posix_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify sensitive environment variables are stripped."""
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/lib")
    monkeypatch.setenv("LD_PRELOAD", "/tmp/preload.so")
    monkeypatch.setenv("PYTHONPATH", "/tmp/py")
    monkeypatch.setenv("PYTHONHOME", "/tmp/home")
    monkeypatch.setenv("_MEIPASS2", "/tmp/mei")
    monkeypatch.setenv("KEEP_VAR", "preserved")

    cleaned = integration._clean_posix_environ()
    assert "LD_LIBRARY_PATH" not in cleaned
    assert "LD_PRELOAD" not in cleaned
    assert "PYTHONPATH" not in cleaned
    assert "PYTHONHOME" not in cleaned
    assert "_MEIPASS2" not in cleaned
    assert cleaned.get("KEEP_VAR") == "preserved"


def test_open_posix_cmd_success() -> None:
    """Verify _open_posix_cmd spawns subprocess.Popen detached."""
    with patch("subprocess.Popen") as mock_popen:
        env = {"PATH": "/bin"}
        assert integration._open_posix_cmd(["xdg-open", "/test"], env) is True
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["xdg-open", "/test"]
        assert kwargs["env"] == env


def test_open_posix_cmd_failure() -> None:
    """Verify _open_posix_cmd returns False on exception."""
    with patch("subprocess.Popen", side_effect=OSError("Command not found")):
        assert integration._open_posix_cmd(["bad-cmd", "/test"], {}) is False


def test_open_folder_platform_windows_startfile(temp_folder: Path) -> None:
    """Verify Windows calls os.startfile when available."""
    with patch("platform.system", return_value="windows"):
        with patch("os.startfile", create=True) as mock_start:
            integration._open_folder_platform(temp_folder)
            mock_start.assert_called_once_with(str(temp_folder))


def test_open_folder_platform_windows_fallback(temp_folder: Path) -> None:
    """Verify Windows falls back to explorer.exe if startfile fails."""
    with patch("platform.system", return_value="windows"):
        with patch(
            "os.startfile",
            side_effect=OSError("Startfile failed"),
            create=True,
        ):
            with patch("subprocess.Popen") as mock_popen:
                integration._open_folder_platform(temp_folder)
                mock_popen.assert_called_once_with(
                    ["explorer.exe", str(temp_folder)]
                )


def test_open_folder_platform_windows_all_fail(temp_folder: Path) -> None:
    """Verify RuntimeError is raised when all Windows launchers fail."""
    with patch("platform.system", return_value="windows"):
        with patch("os.startfile", side_effect=OSError("Fail"), create=True):
            with patch("subprocess.Popen", side_effect=OSError("Fail")):
                with pytest.raises(
                    RuntimeError, match="Could not open folder on Windows"
                ):
                    integration._open_folder_platform(temp_folder)


def test_open_folder_platform_darwin(temp_folder: Path) -> None:
    """Verify macOS uses subprocess.Popen with 'open'."""
    with patch("platform.system", return_value="darwin"):
        with patch("subprocess.Popen") as mock_popen:
            integration._open_folder_platform(temp_folder)
            mock_popen.assert_called_once_with(["open", str(temp_folder)])


def test_open_folder_platform_posix_qdesktop_success(
    temp_folder: Path,
) -> None:
    """Verify POSIX first tries Qt QDesktopServices.openUrl."""
    with patch("platform.system", return_value="linux"):
        mock_gui = MagicMock()
        mock_gui.QDesktopServices.openUrl.return_value = True
        mock_core = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "atlas.compatibility.qt": MagicMock(
                    QtGui=mock_gui, QtCore=mock_core
                )
            },
        ):
            integration._open_folder_platform(temp_folder)
            mock_gui.QDesktopServices.openUrl.assert_called_once()


def test_open_folder_platform_posix_xdg_open_fallback(
    temp_folder: Path,
) -> None:
    """Verify POSIX falls back to xdg-open if QDesktopServices fails."""
    with patch("platform.system", return_value="linux"):
        with patch.dict("sys.modules", {"atlas.compatibility.qt": None}):
            with patch(
                "atlas.lib.integration._open_posix_cmd", side_effect=[True]
            ) as mock_cmd:
                integration._open_folder_platform(temp_folder)
                mock_cmd.assert_called_once()
                assert mock_cmd.call_args[0][0] == [
                    "xdg-open",
                    str(temp_folder),
                ]


def test_open_folder_platform_bsd_file_manager_fallback(
    temp_folder: Path,
) -> None:
    """Verify BSD falls back to desktop file manager if xdg-open fails."""
    with patch("platform.system", return_value="freebsd"):
        with patch.dict("sys.modules", {"atlas.compatibility.qt": None}):
            with patch(
                "shutil.which", side_effect=lambda cmd, **kw: "/usr/bin/" + cmd
            ):
                with patch(
                    "atlas.lib.integration._open_posix_cmd",
                    side_effect=[False, True],
                ) as mock_cmd:
                    integration._open_folder_platform(temp_folder)
                    assert mock_cmd.call_count == 2
                    assert mock_cmd.call_args_list[0][0][0] == [
                        "xdg-open",
                        str(temp_folder),
                    ]
                    assert mock_cmd.call_args_list[1][0][0] == [
                        "gio",
                        "open",
                        str(temp_folder),
                    ]


def test_open_folder_platform_posix_all_fail(temp_folder: Path) -> None:
    """Verify RuntimeError is raised when all POSIX/BSD openers fail."""
    with patch("platform.system", return_value="linux"):
        with patch.dict("sys.modules", {"atlas.compatibility.qt": None}):
            with patch(
                "atlas.lib.integration._open_posix_cmd", return_value=False
            ):
                with pytest.raises(
                    RuntimeError, match="Could not open folder on POSIX/BSD"
                ):
                    integration._open_folder_platform(temp_folder)


def test_open_folder_handles_exception(
    temp_folder: Path, mock_warning: MagicMock
) -> None:
    """Verify exception handling during folder opening."""
    with patch(
        "atlas.lib.integration._open_folder_platform",
        side_effect=Exception("Boom"),
    ):
        integration.open_folder(temp_folder)
        mock_warning.assert_called_once()
        args = mock_warning.call_args[1]
        assert "Failed to Open Folder" in args["message"]


def test_is_tiling_window_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify tiling window manager detection."""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("I3SOCK", raising=False)
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    assert integration._is_tiling_window_manager() is False

    monkeypatch.setenv("SWAYSOCK", "/tmp/sway.sock")
    assert integration._is_tiling_window_manager() is True

    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "i3")
    assert integration._is_tiling_window_manager() is True


def test_is_kde(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify KDE desktop environment detection."""
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("KDE_SESSION_VERSION", raising=False)
    monkeypatch.delenv("KDE_FULL_SESSION", raising=False)
    assert integration._is_kde() is False

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    assert integration._is_kde() is True

    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.setenv("KDE_SESSION_VERSION", "5")
    assert integration._is_kde() is True


def test_is_mate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify MATE desktop environment detection."""
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("MATE_DESKTOP_SESSION_ID", raising=False)
    assert integration._is_mate() is False

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "MATE")
    assert integration._is_mate() is True


def test_is_xfce(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify XFCE desktop environment detection."""
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    assert integration._is_xfce() is False

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    assert integration._is_xfce() is True


def test_get_clean_desktop_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify LD_LIBRARY_PATH_ORIG restoration and Qt env clearing."""
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/usr/lib/host")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/appimage/lib")
    monkeypatch.setenv("QT_PLUGIN_PATH", "/tmp/qt/plugins")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("GIO_MODULE_DIR", "/tmp/gio")
    monkeypatch.setenv("PYTHONPATH", "/tmp/venv")

    clean = integration._get_clean_desktop_environment()
    assert clean["LD_LIBRARY_PATH"] == "/usr/lib/host"
    assert "LD_LIBRARY_PATH_ORIG" not in clean
    assert "QT_PLUGIN_PATH" not in clean
    assert "QT_QPA_PLATFORM" not in clean
    assert "GIO_MODULE_DIR" not in clean
    assert "PYTHONPATH" not in clean


def test_get_linux_file_manager_candidates_kde(
    temp_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify KDE candidates order."""
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    candidates = integration._get_linux_file_manager_candidates(temp_folder)
    commands = [cmd[0] for cmd in candidates]
    assert commands[0] == "xdg-open"
    assert "dolphin" in commands
    assert "kde-open" in commands
    assert "kioclient" in commands


def test_get_linux_file_manager_candidates_mate(
    temp_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify MATE (GhostBSD) candidates order prioritizes caja."""
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "MATE")
    candidates = integration._get_linux_file_manager_candidates(temp_folder)
    commands = [cmd[0] for cmd in candidates]
    assert commands[0] == "xdg-open"
    assert commands[1] == "caja"
    assert "mate-open" in commands


def test_get_linux_file_manager_candidates_general(
    temp_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify general candidates order includes retro and common tools."""
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("KDE_SESSION_VERSION", raising=False)
    monkeypatch.delenv("MATE_DESKTOP_SESSION_ID", raising=False)
    candidates = integration._get_linux_file_manager_candidates(temp_folder)
    commands = [cmd[0] for cmd in candidates]
    assert "xdg-open" in commands
    assert "gio" in commands
    assert "gvfs-open" in commands
    assert "nautilus" in commands
    assert "thunar" in commands
    assert "pcmanfm" in commands
    assert "caja" in commands
    assert "xfe" in commands


def test_run_linux_open_success(temp_folder: Path) -> None:
    """Verify _run_linux_open returns True when an opener succeeds."""
    with patch(
        "atlas.lib.integration._open_posix_cmd", return_value=True
    ) as mock_cmd:
        assert integration._run_linux_open(temp_folder) is True
        mock_cmd.assert_called_once()


def test_open_folder_platform_mate_caja_fallback(
    temp_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify MATE (GhostBSD) prioritizes caja if xdg-open fails."""
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "MATE")
    with patch("platform.system", return_value="freebsd"):
        with patch.dict("sys.modules", {"atlas.compatibility.qt": None}):
            with patch(
                "shutil.which", side_effect=lambda cmd, **kw: "/usr/bin/" + cmd
            ):
                with patch(
                    "atlas.lib.integration._open_posix_cmd",
                    side_effect=[False, True],
                ) as mock_cmd:
                    integration._open_folder_platform(temp_folder)
                    assert mock_cmd.call_count == 2
                    assert mock_cmd.call_args_list[0][0][0] == [
                        "xdg-open",
                        str(temp_folder),
                    ]
                    assert mock_cmd.call_args_list[1][0][0] == [
                        "caja",
                        str(temp_folder),
                    ]


def test_is_tiling_window_manager_sunos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify SunOS is recognized for tiling window manager detection."""
    monkeypatch.setattr(sys, "platform", "sunos5")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "i3")
    assert integration._is_tiling_window_manager() is True


def test_build_terminal_command() -> None:
    """Verify command structure for various terminal emulators."""
    target = "/home/user/backup"
    assert integration._build_terminal_command("foot", "mc", target) == [
        "foot", "mc", target
    ]
    assert integration._build_terminal_command("kitty", "ranger", target) == [
        "kitty", "ranger", target
    ]
    assert integration._build_terminal_command("wezterm", "nnn", target) == [
        "wezterm", "start", "--", "nnn", target
    ]
    assert integration._build_terminal_command(
        "xfce4-terminal", "mc", target
    ) == ["xfce4-terminal", "-e", "mc /home/user/backup"]
    assert integration._build_terminal_command(
        "ghostty", "yazi", target
    ) == ["ghostty", "-e", "yazi /home/user/backup"]
    assert integration._build_terminal_command(
        "gnome-terminal", "lf", target
    ) == ["gnome-terminal", "--", "lf", target]
    assert integration._build_terminal_command("xterm", "mc", target) == [
        "xterm", "-e", "mc", target
    ]


def test_get_terminal_file_manager_candidates_found() -> None:
    """Verify candidate building when terminal and manager are available."""
    target = "/tmp/test"
    with patch(
        "shutil.which",
        side_effect=lambda cmd, **kw: "/usr/bin/" + cmd if cmd in (
            "mc", "ranger", "xterm"
        ) else None,
    ):
        candidates = integration._get_terminal_file_manager_candidates(target)
        assert len(candidates) == 2
        assert candidates[0] == ["xterm", "-e", "ranger", target]
        assert candidates[1] == ["xterm", "-e", "mc", target]


def test_get_terminal_file_manager_candidates_none() -> None:
    """Verify empty list returned when no terminal or manager is present."""
    target = "/tmp/test"
    with patch("shutil.which", return_value=None):
        assert integration._get_terminal_file_manager_candidates(target) == []


def test_open_posix_cmd_dispatcher_timeout() -> None:
    """Verify dispatcher timeout triggers process termination."""
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.wait.side_effect = subprocess.TimeoutExpired("xdg-open", 3)
        mock_popen.return_value = proc
        assert integration._open_posix_cmd(
            ["xdg-open", "/test"], {"PATH": "/bin"}
        ) is False
        proc.kill.assert_called_once()


def test_open_posix_cmd_dispatcher_nonzero_exit() -> None:
    """Verify dispatcher exiting with error code returns False."""
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.wait.return_value = None
        proc.poll.return_value = 2
        mock_popen.return_value = proc
        assert integration._open_posix_cmd(
            ["xdg-open", "/test"], {"PATH": "/bin"}
        ) is False


def test_open_posix_cmd_direct_fm_success() -> None:
    """Verify direct file manager spawns detached and succeeds."""
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.wait.return_value = None
        proc.poll.return_value = None
        mock_popen.return_value = proc
        assert integration._open_posix_cmd(
            ["dolphin", "/test"], {"PATH": "/bin"}
        ) is True


def test_open_posix_cmd_direct_fm_instant_crash() -> None:
    """Verify direct file manager crashing immediately returns False."""
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.wait.return_value = None
        proc.poll.return_value = 127
        mock_popen.return_value = proc
        assert integration._open_posix_cmd(
            ["dolphin", "/test"], {"PATH": "/bin"}
        ) is False


def test_get_linux_file_manager_candidates_modern_and_term(
    temp_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify modern desktop FMs and terminal candidates are included."""
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    monkeypatch.delenv("KDE_SESSION_VERSION", raising=False)
    monkeypatch.delenv("MATE_DESKTOP_SESSION_ID", raising=False)
    with patch(
        "atlas.lib.integration._get_terminal_file_manager_candidates",
        return_value=[["xterm", "-e", "mc", str(temp_folder)]],
    ):
        candidates = integration._get_linux_file_manager_candidates(
            temp_folder
        )
        commands = [cmd[0] for cmd in candidates]
        assert "cosmic-files" in commands
        assert "pantheon-files" in commands
        assert "xterm" in commands


def test_dispatch_open_folder_warning(
    temp_folder: Path, mock_warning: MagicMock
) -> None:
    """Verify warning dispatch invokes show_warning."""
    with patch.dict("sys.modules", {"atlas.compatibility.qt": None}):
        integration._dispatch_open_folder_warning(temp_folder)
        mock_warning.assert_called_once()
        args = mock_warning.call_args[1]
        assert "Failed to Open Folder" in args["message"]


# =============================================================================
# TEST EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
