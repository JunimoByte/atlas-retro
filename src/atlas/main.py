"""Atlas | Entry Point.

Main entry point for the Atlas browser backup application.
Handles initialization, configuration verification, UI setup, and execution.
"""

# =============================================================================
# RUNTIME COMPATIBILITY SHIMS (Must run before any other imports)
# =============================================================================

import os
import sys
import types

# 1. Fallback for 'typing' module if missing on Python 3.4
try:
    import typing  # noqa: F401
except ImportError:
    class _TypingPlaceholder:
        def __getitem__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            return self

        def __repr__(self):
            return "Any"

    _stub = types.ModuleType("typing")
    for _name in (
        "Any", "Callable", "Dict", "Generator", "Iterable",
        "List", "Mapping", "Optional", "Sequence", "Set",
        "Tuple", "Union", "TypeVar", "Generic", "cast"
    ):
        setattr(_stub, _name, _TypingPlaceholder())
    sys.modules["typing"] = _stub

# 2. Ensure Path.mkdir supports exist_ok on Python 3.4
try:
    import inspect
    from pathlib import Path

    if "exist_ok" not in inspect.signature(Path.mkdir).parameters:
        _orig_path_mkdir = Path.mkdir

        def _compat_mkdir(self, mode=0o777, parents=False, exist_ok=False):
            try:
                _orig_path_mkdir(self, mode=mode, parents=parents)
            except OSError:
                if not (exist_ok and self.is_dir()):
                    raise

        Path.mkdir = _compat_mkdir
except Exception:
    pass

# 3. Protection against None stdout/stderr in PyInstaller windowed mode


class _NullStream:
    def write(self, *args, **kwargs):
        pass

    def flush(self):
        pass


if sys.stdout is None:
    sys.stdout = _NullStream()
if sys.stderr is None:
    sys.stderr = _NullStream()

# =============================================================================
# IMPORTS & LOGGING
# =============================================================================

import logging  # noqa: E402
import traceback  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

LOGGER = logging.getLogger(__name__)

# =============================================================================
# FUNCTIONS
# =============================================================================


def _show_fatal_dialog(tb_text: str) -> None:
    """Write crash log and show diagnostic message box if on Windows."""
    try:
        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "."))
        crash_log = os.path.join(temp_dir, "atlas_crash.log")
        with open(crash_log, "w", encoding="utf-8") as fh:
            fh.write(tb_text)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                "Atlas encountered an error during startup:\n\n"
                + tb_text
                + "\n\nA crash log was saved to %TEMP%\\atlas_crash.log",
                "Atlas Startup Error",
                0x10,  # MB_ICONERROR
            )
        except Exception:
            pass


def main() -> None:
    """Launch Atlas.

    Routes execution to either the CLI or GUI based on parsed arguments.
    """
    from atlas.args import parse_args

    args = parse_args()

    if args.cli:
        from atlas.cli import run_cli

        sys.exit(run_cli(args))
    else:
        # On POSIX/Linux, check if a graphical display is available.
        # If no DISPLAY or WAYLAND_DISPLAY is set (e.g. over SSH/console),
        # gracefully fall back to headless CLI mode rather than crashing.
        if (
            os.name == "posix"
            and sys.platform != "darwin"
            and not os.environ.get("DISPLAY")
            and not os.environ.get("WAYLAND_DISPLAY")
        ):
            LOGGER.info(
                "No graphical display detected ($DISPLAY is unset). "
                "Launching in headless CLI mode."
            )
            from atlas.cli import run_cli

            sys.exit(run_cli(args))

        try:
            from atlas.gui import run_gui

            sys.exit(run_gui(args))
        except ImportError as err:
            # If PyQt is missing on Linux, inform the user and fall back to CLI
            if "PyQt" in str(err) or "qt" in str(err).lower():
                LOGGER.warning(
                    "PyQt GUI runtime not found (%s). "
                    "Falling back to headless CLI mode.",
                    err,
                )
                from atlas.cli import run_cli

                sys.exit(run_cli(args))
            raise


# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        LOGGER.error("Fatal error during execution:\n%s", tb)
        _show_fatal_dialog(tb)
        sys.exit(1)
