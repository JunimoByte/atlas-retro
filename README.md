<div align="center">
  <img src="assets/icons/Icon.svg" alt="Atlas icon" width="104" height="104">
  <h1>Atlas</h1>
  <p><strong>Reliable, offline browser-profile backups.</strong></p>
  <p>
    <a href="https://github.com/JunimoByte/atlas/actions/workflows/ci.yml">
      <img src="https://github.com/JunimoByte/atlas/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status">
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.4%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.4 or later">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg" alt="License: AGPL-3.0-or-later">
    </a>
  </p>
</div>

---

## Overview

**Atlas** creates safe, compact, and completely portable ZIP backups of browser profiles without ever modifying the source files. 

Engineered specifically for retro computing, older workstations, and preservation hobbyists, Atlas is built from the ground up to run on **Windows XP (NT 5.1/5.2, 32-bit & 64-bit)** using **Python 3.4.4** (the final official Python release for Windows XP) and **PyQt4 / PyQt5**, as well as older **Linux** desktops of that era (Debian 8 Jessie, Ubuntu 14.04 Trusty, etc.).

---

## Supported Platforms & Release Packages

To guarantee stability, lightweight performance, and authentic compatibility with legacy hardware, Atlas provides pre-compiled, ready-to-run release packages for every target platform:

### Supported Operating Systems & Package Formats

- **Windows XP & Modern Windows (32-bit & 64-bit)**:
  - **Standalone Executables**: `Atlas-x86-Portable.exe` and `Atlas-x86_64-Portable.exe` (run immediately with zero installation or external dependencies).
  - **Setup Installer**: `Atlas-x86-Setup.exe` built with Inno Setup 5 (native Luna / Classic integration).
- **Linux (Older & Modern Distributions)**:
  - **AppImage**: Standalone, self-contained `Atlas-x86_64.AppImage` and `Atlas-x86.AppImage` (runs across older distros like Debian 8 / Ubuntu 14.04 up to modern Ubuntu 24.04).
  - **Debian / Ubuntu Package (`.deb`)**: Native package installation (`sudo apt install ./Atlas-x86_64.deb`).
  - **Standalone Portable Binary**: Pre-built executable for lightweight environments.
- **FreeBSD & GhostBSD**:
  - **Portable Release Bundle**: `FreeBSD_Release.tar.gz` containing the executable, icon, and `install_bsd.sh` for desktop integration.
  - **Native FreeBSD Package (`.pkg`)**: Native `pkg add` distribution.

### Technical Architecture & Compatibility Standards

- **PyQt4 & PyQt5 Frameworks**: Standardized on PyQt4 and PyQt5 for authentic native widget rendering across retro systems (Windows XP Luna, classic X11 styles) and modern desktops without modern runtime bloat.
- **Strict Backward Compatibility**: The core codebase strictly complies with Python 3.4+ syntax (zero dependencies on Python 3.5+ f-strings, variable type annotations, or newer OS APIs), guaranteeing that the exact same application logic executes reliably across all supported platforms.

---

## Features

- **300+ Supported Browsers**: Detects and backs up profiles for older Internet Explorer (IE 6, 7, 8), retro Mozilla Firefox, Pale Moon, K-Meleon, Netscape, Opera Presto (12.x), SeaMonkey, Chromium, and hundreds of derivatives.
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

## Linux Installation & Packages

Atlas provides pre-compiled, self-contained packages for Linux distributions (Debian, Ubuntu, CentOS, Fedora, Arch, and derivatives):

### AppImage (Recommended)
1. Download `Atlas-x86_64.AppImage` (or `Atlas-x86.AppImage` for 32-bit).
2. Make it executable and launch:
   ```bash
   chmod +x Atlas-x86_64.AppImage
   ./Atlas-x86_64.AppImage
   ```

### Debian / Ubuntu Package (.deb)
Install directly using `apt`:
```bash
sudo apt install ./Atlas-x86_64.deb
```
This deploys Atlas to `/opt/atlas` and automatically registers desktop integration and application menu shortcuts.

### Building Linux Packages (Developers)
- **Build AppImage:** `bash scripts/build_appimage.sh`
- **Build Debian Package:** `bash scripts/build_deb.sh`
- **Run from Source:** `python3 main.py`

---

## FreeBSD & GhostBSD (Packages & Portable Bundle)

Atlas supports FreeBSD and GhostBSD through both native `.pkg` packages and standalone release bundles:

### Portable Release Bundle
The pre-bundled archive contains the self-contained executable, application icon, and installation helper script:

```
FreeBSD_Release/
├── Atlas-x86_64-Portable   # (or Atlas-x86-Portable on 32-bit BSD)
├── Icon.svg
└── install_bsd.sh
```

1. Extract the release archive:
   ```bash
   tar -xzf FreeBSD_Release.tar.gz
   cd FreeBSD_Release
   ```
2. **Run directly (portable mode):**
   ```bash
   ./Atlas-x86_64-Portable
   # or on 32-bit BSD:
   ./Atlas-x86-Portable
   ```
3. **Install to system (optional desktop integration):**
   ```bash
   sudo sh install_bsd.sh
   ```
   *(Installs to `/usr/local/bin/atlas`, installs desktop icons, and configures the application menu).*

### Native FreeBSD Package (.pkg)
```bash
sudo pkg add ./Atlas-amd64.pkg
```

### Building BSD Packages from Source (Developers)
- **Build .pkg:** `bash scripts/build_pkg.sh`
- **Build Portable Binary:** `pyinstaller main.spec --clean --noconfirm`
- **Run from Source:** `python3 main.py`

---

## Running Atlas

### Graphical Mode
- **Standalone:** Double-click `Atlas-x86-Portable.exe` (Windows) or execute the portable binary on Linux/BSD.
- **From Source:** Run `python -m atlas.main` (or `python main.py`).
- Atlas scans discovered browser profiles, estimates compressed size, and prompts you to begin backup. Archives are saved to `My Documents\Backup` (Windows XP) or `~/Downloads/Backup` (Linux/BSD).

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
| `scripts/` | Build scripts (`build_windows.bat`, `build_appimage.sh`, `build_deb.sh`, `build_pkg.sh`, `install_bsd.sh`) |
| `installer/` | Packaging metadata for Inno Setup (`Atlas.iss`), AppImage, and Debian |
| `docs/` | Architecture records and platform setup guides |
| `main.spec` | PyInstaller standalone packaging specification |
| `appimage.spec` | PyInstaller specification for AppImage and Debian payloads |
| `build.bat` | One-click Windows automated build script |

---

## License

GNU Affero General Public License v3.0 or later. See [LICENSE](LICENSE) for details.
