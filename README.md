<div align="center">
  <img src="assets/icons/Icon.svg" alt="Atlas icon" width="104" height="104">
  <h1>Atlas</h1>
  <p><strong>Reliable, offline browser-profile backups.</strong></p>
  <p>
    <a href="https://github.com/JunimoByte/atlas-retro/actions/workflows/ci.yml">
      <img src="https://github.com/JunimoByte/atlas-retro/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status">
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.4%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.4+">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg" alt="License: AGPL-3.0-or-later">
    </a>
  </p>
</div>

Atlas creates portable, lightweight ZIP backups of browser profiles while
never writing to any browser directory. Engineered for retro computing, older
workstations, and preservation, Atlas natively targets **Windows XP (NT 5.1/5.2)**
and vintage Unix environments while seamlessly running across modern operating systems.

## Features

- **300+ Supported Browsers:** Comprehensive auto-detection for classic and
  modern Chromium, Gecko, Goanna, and legacy engines (Internet Explorer 6–8,
  classic Firefox, Pale Moon, K-Meleon, Netscape, Opera Presto 12.x, SeaMonkey,
  Chrome, Brave, Floorp, Vivaldi, and 290+ more).
- **Intelligent Cache Stripping:** Excludes caches and disposable data,
  often shrinking 1 GB+ profiles to ~100 MB while preserving bookmarks,
  history, extensions, passwords, and preferences.
- **Strictly Read-Only:** Live browser folders are opened exclusively in
  read-only mode and are never modified, written to, or altered.
- **Headless & Automation Ready:** Full graphical interface (classic Luna and
  X11 styles via PyQt4/PyQt5) and headless CLI mode (`--cli`) with cron-safe logging.
- **Cross-Platform & Retro-Compatible:** Native support for Windows (XP SP3
  through 11, 32-bit & 64-bit), legacy Linux (glibc 2.19+, Ubuntu 14.04 Trusty /
  Debian 8 Jessie up to modern distributions), and BSD (FreeBSD 10.x+, GhostBSD 4.x+).

## Privacy & Offline Guarantee

Atlas is engineered from the ground up to respect user privacy:

- **100% Offline:** Zero telemetry, analytics, crash reporting, or cloud sync.
- **Physical Network Exclusion:** Standalone binary builds physically exclude
  standard networking libraries (`socket`, `ssl`, `http`, `QtNetwork`).
- **No Credential Decryption:** Atlas never decrypts DPAPI credentials,
  master keys, or saved browser passwords.
- **Local Ownership:** All archives remain on your local storage under your
  complete control.

> [!NOTE]
> CI builds the Linux payload and executes the test suite in a
> network-disabled container. Any attempt by the application to initiate
> a network connection immediately fails the build.

For full details, see the [Privacy Policy](PRIVACY.md).

## Quickstart

### Prebuilt Binaries

Download native executables and packages from [Releases](../../releases):

- **Windows (XP SP3 through 11):** Standalone portable `.exe` (32-bit & 64-bit)
  or Inno Setup installer (`Atlas-x86-Setup.exe`)
- **Linux (glibc 2.19+ / Ubuntu 14.04+ / Debian 8+):** Standalone `.AppImage`
  (32-bit & 64-bit) or native `.deb` package
- **FreeBSD / GhostBSD (10.x+):** Standalone portable release bundle
  (`FreeBSD_Release.tar.gz` with `install_bsd.sh`) or native `.pkg` package

### Run from Source / Command Line

```bash
# Launch GUI
python main.py

# Headless backup (default: My Documents\Backup on Windows, ~/Downloads/Backup on Linux/BSD)
python main.py --cli

# Headless backup to custom directory
python main.py --cli -o /mnt/backups
```

*(Or using standalone executables: `Atlas.exe --cli` or `./Atlas-x86_64-Portable --cli`)*

*If installing into a Python virtual environment: `pip install .`*

## How It Works

1. **Auto-Detection:** Atlas scans standard locations across your system
   to identify installed browsers and their active profiles.
2. **Selective Archiving:** Disposable caches, crash dumps, and temporary
   files are bypassed during archive creation.
3. **Atomic Packaging:** Profiles are packaged into standard, non-proprietary
   ZIP archives.
4. **Transparent Restoration:** Because backups use standard folder layouts,
   restoring a profile is as simple as unzipping the archive back into the
   browser profile folder.

## Development

### Setup Environment

- **Linux / macOS / BSD** (`bash` or `zsh`):
  ```bash
  source scripts/setup_dev.sh
  ```
- **Windows** (Command Prompt or PowerShell):
  ```cmd
  scripts\setup_dev.bat
  ```
- **Windows XP Setup:** For instructions on configuring Python 3.4.4 and PyQt4
  on legacy Windows XP hardware, see the [Windows XP Compilation Guide](docs/compiling_on_windows_xp.md).

### Running Tests

```bash
pytest

# Headless Linux or CI execution:
QT_QPA_PLATFORM=offscreen pytest
```

### Building Releases

| Target Platform | Command | Output Artifact |
| :--- | :--- | :--- |
| **Windows (XP–11)** | `build.bat` *(or `pyinstaller main.spec`)* | `dist/*-Portable.exe`, `dist/*-Setup.exe` |
| **Linux AppImage** | `bash scripts/build_appimage.sh` | `dist/*.AppImage` |
| **Debian / Ubuntu** | `bash scripts/build_deb.sh` | `dist/*.deb` |
| **FreeBSD / GhostBSD** | `bash scripts/build_pkg.sh` | `dist/*.pkg`, `FreeBSD_Release.tar.gz` |

*For advanced packaging options and platform notes, see the [docs](docs/).*

## Structure

| Location | Purpose |
| :--- | :--- |
| `src/atlas/` | Application code and unit tests |
| `configs/` | Browser profiles, rules, and blacklist |
| `assets/` | Application icons and graphics |
| `scripts/` | Environment setup and build scripts |
| `installer/` | Platform packaging metadata (Inno Setup, AppImage, Debian) |
| `docs/` | Architecture and platform documentation |

## License

GNU Affero General Public License v3.0 or later. See [LICENSE](LICENSE).
