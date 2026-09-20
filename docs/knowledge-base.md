# Atlas Knowledge Base

## Purpose

Atlas is an offline desktop utility that discovers browser profiles and
creates portable ZIP backups. Its operational model is deliberately defensive:
browser profile directories are read only and archives are written only to a
user-controlled output location.

## Supported Environments

Atlas is targeted at Windows XP (NT 5.1/5.2) setups, vintage computing
workstations, and modern desktop environments. The supported baseline runtime is
Python 3.4.4 (the final official release for Windows XP) with PyQt4 (Qt 4.8).
PyQt5 is also supported as the modern fallback via compatibility shims.

Linux is supported for CLI and source execution. Windows XP support includes native
Win32 folder resolution (`SHGetFolderPathW`), legacy shell folders (`My Documents\Backup`),
and complete isolation from modern DWM and compositing APIs.

## Startup and Application Flow

The executable entry point is `atlas.main`, also exposed as the `atlas`
console command. The bootstrapper delegates argument parsing and version
resolution to `atlas.args` and routes execution:

**Graphical Mode (`gui.py`)**:
1. Refuse elevated/admin execution.
2. Load and validate browser and path-type configuration.
3. Create `QApplication` and the main `Window`.
4. Initialize the window theme, application icon, and backdrop.
5. Enter the Qt event loop (`app.exec_()`).

**CLI Mode (`cli.py`)**:
1. Refuse elevated/admin execution (prints warning).
2. Load and validate browser configuration.
3. Construct `Pipeline` with console standard output callbacks.
4. Execute pipeline and exit.

The backup operation follows a separate staged flow:

```text
Scan profiles -> estimate size -> validate free space -> create ZIP archives
```

The pipeline is cancelable and runs away from the main GUI thread.

## Qt Compatibility Boundary

`atlas.compatibility.qt` is the single Qt import boundary. Application code
imports `QtCore`, `QtGui`, and `QtWidgets` from this module rather than from a
specific PyQt package. The module switches strictly between PyQt4 first (aliasing `QtWidgets = QtGui`)
and PyQt5, and raises an import error if neither binding is installed.

This boundary also shims scoped enum namespaces (`WindowType`, `AlignmentFlag`,
`Orientation`, `StandardButton`, `Icon`, etc.) so that code written for modern Qt
operates seamlessly on PyQt4 and PyQt5.

## Interface and Window Model

`atlas.ui.interface.UiDialog` owns the static widget tree. It constructs:

- A title and backdrop.
- Four mutually exclusive status labels: initial description, progress,
  completion, and cancellation.
- An elapsed-time label and progress bar.
- A standard OK/Cancel dialog button box.

The layout has a nominal 407 x 290 minimum size and uses layout managers,
scaled fonts, word-wrapped labels, and Qt translation calls. The main
`atlas.display.window.Window` owns behavior rather than layout. It changes
the visible widgets and button actions through four modes:

| Mode | Visible content | Primary action | Secondary action |
| --- | --- | --- | --- |
| Idle | Introduction | Start scan | Close |
| Scanning | Progress and elapsed time | Hidden | Cancel |
| Completed | Completion text | Open output folder | Close |
| Error/cancelled | Cancellation text | Hidden | Close |

Buttons use a declarative configuration and are reconnected as the mode
changes.

## Event and Background-Work Design

`display.signals.Signals` is the UI event contract. It carries backup start,
finish, cancellation, progress, estimated size, scan status, elapsed time,
disk-space errors, no-profile results, and worker failures.

`display.controller.Controller` manages worker thread lifetime and coordinates
between the GUI and backup pipeline using an airtight finite state machine.

## Packaging and Delivery

The Windows PyInstaller specification (`main.spec`) produces standalone, portable
single-file executables:
- `Atlas-Retro-x86-Portable.exe` (32-bit Windows XP)
- `Atlas-Retro-x86_64-Portable.exe` (64-bit Windows XP / modern Windows)

`installer/Atlas.iss` provides an Inno Setup 5 installer configured with `MinVersion=5.1.2600`
to produce `Atlas-Retro-Setup.exe` that natively installs onto Windows XP and later.

## Code Map

| Location | Responsibility |
| --- | --- |
| `src/atlas/main.py` | Bootstrapper router; delegates argument parsing and routes to GUI or CLI. |
| `src/atlas/gui.py` | Graphical entry point (Qt application launch). |
| `src/atlas/cli.py` | Headless entry point (CLI application launch). |
| `src/atlas/args.py` | CLI argument parser and dynamic version resolution from `pyproject.toml`. |
| `src/atlas/compatibility/qt.py` | Qt binding selection (PyQt4/5/6) and scoped enum shims. |
| `src/atlas/ui/interface.py` | Static main-dialog widgets and layout. |
| `src/atlas/display/` | Window modes, controller, signals, controls, dialogs. |
| `src/atlas/backup/` | Discovery, sizing, validation, filtering, and archiving. |
| `src/atlas/lib/` | Configuration, themes, permissions, folders, OS integration. |
| `configs/` | Browser locations, path types, and blacklist policy. |
| `main.spec` | PyInstaller packaging definition for portable Windows XP executables. |
| `installer/Atlas.iss` | Windows XP Inno Setup installer definition. |
| `scripts/setup_dev.bat` | Windows developer environment configuration script. |
| `scripts/setup_dev.sh` | Linux developer environment configuration script. |

## Testing and Headless Use

Unit tests are located in `src/atlas/tests/unit`; integration tests are in
`src/atlas/tests/integration`. GUI tests can run without a desktop by setting
`QT_QPA_PLATFORM=offscreen`. The repository's standard unit-test command is:

```powershell
python -m pytest src/atlas/tests/unit --tb=short -q
```
