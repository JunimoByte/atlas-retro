<div align="center">
  <img src="assets/icons/Icon.svg" alt="Atlas icon" width="104" height="104">
  <h1>Atlas</h1>
  <p><strong>Reliable, offline browser-profile backups.</strong></p>
  <p>
    <a href="https://github.com/JunimoByte/atlas/actions/workflows/ci.yml">
      <img src="https://github.com/JunimoByte/atlas/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status">
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.8 or later">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg" alt="License: AGPL-3.0-or-later">
    </a>
  </p>
</div>

---

## Overview

**Atlas** creates safe, compact, and completely portable ZIP backups of browser profiles without ever modifying the source files. 

Engineered specifically for retro computing, vintage workstations, and preservation hobbyists, Atlas is built from the ground up to run on **Windows XP (NT 5.1/5.2, 32-bit & 64-bit)** using **Python 3.4.4** (the final official Python release for Windows XP) and **PyQt4 / PyQt5**, as well as vintage **Linux** desktops of that era (Debian 8 Jessie, Ubuntu 14.04 Trusty, etc.).

---

## Supported vs. Unsupported Platforms

To guarantee stability, zero bloat, and authentic compatibility with legacy hardware, platform support is strictly defined:

### Supported
- **Windows XP (32-bit SP3 & 64-bit SP2)** and **Windows Server 2003**: The primary target. Uses native Win32 APIs (`SHGetFolderPathW`, CSIDL), bypasses UAC restrictions, and renders native Windows XP Luna (Blue, Olive, Silver) and Classic UI styles.
- **Vintage Linux (Python 3.4 era)**: Debian 8 (Jessie), Ubuntu 14.04 (Trusty), CentOS 7, and similar X11 desktop environments with `python3-pyqt4` or `python3-pyqt5`.
- **Modern Windows (Vista, 7, 8, 10, 11)**: Supported in backward-compatibility mode via Python 3.4+ / PyQt5.

### What Is NOT Supported (Intentionally Removed)
- **NO BSD / FreeBSD / GhostBSD**: Packaging and platform-specific shell hooks have been removed.
- **NO Linux AppImage / Debian Packages (`.deb`)**: Legacy Linux runs directly from source (`python3 main.py`) or virtual environments.
- **NO Microsoft Store / MSIX Packaging**: Modern Universal Windows Platform (UWP/MSIX) packaging is completely excluded.
- **NO PyQt6**: PyQt6 dropped 32-bit Windows XP and Python 3.4 years ago; Atlas exclusively targets PyQt4 and PyQt5.
- **NO Python 3.5+ Syntax**: The codebase contains zero f-strings (PEP 498), zero variable type annotations (PEP 526), and zero dependencies on modern Windows APIs like `dwmapi.dll` or `SHGetKnownFolderPath`.

---

## Features

- **300+ Supported Browsers**: Detects and backs up profiles for vintage Internet Explorer (IE 6, 7, 8), retro Mozilla Firefox, Pale Moon, K-Meleon, Netscape, Opera Presto (12.x), SeaMonkey, Chromium, and hundreds of derivatives.
- **De-cluttered Backups**: Automatically strips web caches, code caches, GPU caches, crash dumps, and temporary logs, shrinking 1 GB+ profiles down to a few dozen megabytes.
- **Strict Read-Only Source Model**: Never writes to, locks, or alters the live browser profile directories during backup.
- **Atomic ZIP Compression**: Creates safe `.zip.tmp` archives and atomically renames them upon successful completion. Compatible with Python 3.4's read-only `ZipFile.open` via native `writestr` deflate streaming.
- **Headless CLI Mode**: Run `Atlas.exe --cli` or `python main.py --cli` for automated backups, scheduled tasks, or server environments without starting a graphical interface.

---

## Privacy & Offline Guarantee

Atlas is strictly **100% offline**:
- **Zero Network Traffic**: Contains no analytics, no telemetry, no crash reporting, and no update checks.
- **Network Stack Physically Excluded**: Standalone executable builds physically exclude standard networking modules (`socket`, `ssl`, `http`, `urllib.request`, `QtNetwork`).
- **No Password Decryption**: Atlas does not touch, decrypt, or export Windows DPAPI credentials or browser password databases.
- **Local Ownership**: Backups remain entirely on your local machine (`My Documents\Backup` or adjacent to the executable).

For full details, see the [Privacy Policy](PRIVACY.md).

---

## Windows XP Setup & Compilation Guide

Because Windows XP dropped out of mainstream support and modern HTTPS (TLS 1.2/1.3) is required by modern PyPI, setting up a compilation environment on Windows XP requires installing a few official runtime packages directly.

### 1. Download & Install Python 3.4.4
Download the official Windows installer from python.org:
- **32-bit XP:** [`python-3.4.4.msi`](https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi)
- **64-bit XP:** [`python-3.4.4.amd64.msi`](https://www.python.org/ftp/python/3.4.4/python-3.4.4.amd64.msi)

> [!IMPORTANT]
> During Python installation, scroll to the bottom of the component selection tree and select **"Add python.exe to Path"**.

### 2. Install PyQt4 for Python 3.4
PyPI does not host binary wheels for PyQt4. Install the official pre-compiled Riverbank binary installer:
- **File:** `PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe`
- **Download:** [SourceForge Riverbank Archives](https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/)
- Run the installer; it automatically detects `C:\Python34` and deploys Qt 4.8.7 DLLs and PyQt4 bindings into `Lib\site-packages\PyQt4`.

### 3. Install PyInstaller via Pip (Specific XP Version)
Modern PyInstaller (v4, v5, v6) does **not** work on Windows XP. You must use **PyInstaller 3.2.1** or **3.3.1**:

```cmd
python -m pip install pyinstaller==3.2.1
```

*(If pip fails to connect over HTTPS due to legacy TLS on XP, download `PyInstaller-3.2.1.tar.gz` on a modern machine, copy it over via USB, and run `python -m pip install PyInstaller-3.2.1.tar.gz`).*

### 4. (Optional) Inno Setup 5
To compile the setup installer (`dist\Atlas-x86-Setup.exe`):
- **File:** `isetup-5.5.9-unicode.exe` (Inno Setup 6 dropped XP support; Inno Setup 5.5.x or 5.6.x is required).
- **Download:** [Inno Setup 5 Downloads](https://files.jrsoftware.org/ispack/ispack-5.5.9.exe)

---

## Compiling the Binaries

Once the prerequisites are installed, open a Command Prompt inside the Atlas directory:

### Automated One-Click Build
Run the included build script:
```cmd
build.bat
```
The script will automatically detect Python 3.4, verify PyQt4, run PyInstaller, compile the Inno Setup script, and place the output in `dist\`:
- **`dist\Atlas-x86-Portable.exe`**: Standalone portable single-file binary. Runs on any Windows XP machine without Python or Qt installed!
- **`dist\Atlas-x86-Setup.exe`**: Native Windows XP installer (`MinVersion=5.1.2600`).

### Manual Build
```cmd
python -m PyInstaller main.spec --clean --noconfirm
```

---

## Vintage Linux Setup & Usage

On Debian 8 (Jessie), Ubuntu 14.04 (Trusty), or other vintage Linux distributions:

1. Install Python 3 and PyQt4 or PyQt5:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-pyqt4
   # (Or for PyQt5: sudo apt-get install python3-pyqt5)
   ```

2. Run Atlas directly from source:
   ```bash
   python3 main.py
   ```

3. Run in headless CLI mode:
   ```bash
   python3 main.py --cli
   ```

---

## Running Atlas

### Graphical Mode
- **Standalone:** Double-click `Atlas-x86-Portable.exe`.
- **From Source:** Run `python -m atlas.main` (or `python main.py`).
- Atlas scans discovered browser profiles, estimates compressed size, and prompts you to begin backup. Archives are saved to `My Documents\Backup` (Windows XP) or `~/Downloads/Backup` (Linux).

### Headless CLI Mode
For scripts, remote shells, or system maintenance:
```cmd
Atlas-x86-Portable.exe --cli
```
Or from source:
```bash
python -m atlas.main --cli
```

Available flags:
- `--cli`: Run in text-only headless mode without displaying the Qt interface.
- `--version`: Display application version and system information.
- `--help`: Show usage instructions.

---

## Testing & Quality Assurance

Run the automated test suite using `pytest`:

```bash
pytest
```

To run tests in a headless environment:
```bash
QT_QPA_PLATFORM=offscreen pytest
```

---

## Repository Structure

| Path | Purpose |
| --- | --- |
| `src/atlas/` | Application source code and unit tests |
| `configs/` | Browser profiles (`browsers.json`) and path rules (`types.json`) |
| `assets/` | Icons (`Icon.ico`, `Icon.svg`) and visual assets (`Backdrop.png`) |
| `scripts/` | `build_windows.bat` and development environment scripts |
| `installer/` | Inno Setup 5 configuration script (`Atlas.iss`) |
| `docs/` | Windows XP compilation guide and architecture records |
| `main.spec` | PyInstaller standalone packaging specification |
| `build.bat` | One-click Windows XP automated build batch script |

---

## License

GNU Affero General Public License v3.0 or later. See [LICENSE](LICENSE) for details.
