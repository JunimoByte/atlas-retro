<div align="center">
  <img src="assets/icons/Icon.svg" alt="Atlas icon" width="104" height="104">
  <h1>Atlas</h1>
  <p><strong>Reliable, offline browser-profile backups for Windows XP and vintage computing.</strong></p>
  <p>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.4%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.4 or later">
    </a>
    <a href="https://riverbankcomputing.com/software/pyqt/">
      <img src="https://img.shields.io/badge/PyQt-4%20|%205-41CD52?logo=qt&amp;logoColor=white" alt="PyQt4 / PyQt5">
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg" alt="License: AGPL-3.0-or-later">
    </a>
  </p>
</div>

## Information

Atlas creates portable ZIP backups of browser profiles while never writing to any browser directory. Specifically tailored for retro computing and legacy workstations running Windows XP (NT 5.1/5.2) and modern systems alike, Atlas runs on Python 3.4.4 (the final official Python release for Windows XP) with PyQt4.

## Features

- Supports 300+ Chromium, Gecko, and legacy browser variants (including vintage Internet Explorer, retro Mozilla Firefox, Pale Moon, K-Meleon, and Netscape).
- Excludes caches and temporary data, often reducing a 1 GB+ profile to about 100 MB while preserving settings, history, and bookmarks.
- Strict read-only source model: live browser profiles are never touched, modified, or written to.
- Atomically creates ZIP archives in user-selected locations (`My Documents\Backup`, `Downloads\Backup`, or adjacent to the executable).
- Native Windows XP support: uses `SHGetFolderPathW` and registry lookups, guards against Vista+ API dependencies, and respects native Luna/Classic visual styles.
- Unified GUI layer: switches strictly between PyQt4 (Qt 4.8 on Windows XP) and PyQt5, with seamless enum and execution shims.
- Fully operational headless/CLI mode (`--cli`) for scripts, recovery consoles, or automated tasks.

## Privacy & Offline Guarantee

Atlas is an offline-first tool that respects user privacy:

- **100% Offline:** Zero telemetry, zero analytics, zero crash reporting, and zero cloud synchronization.
- **Physical Network Exclusion:** Standalone executable builds physically exclude standard networking libraries (`socket`, `ssl`, `http`, `QtNetwork`).
- **Read-Only Operation:** Live browser folders are opened strictly in read-only mode and are never modified, written to, or deleted.
- **No Password Decryption:** Atlas does not decrypt DPAPI credentials, master keys, or saved browser passwords.
- **Local Control:** All archives remain on your local drive and are completely under your ownership and control.

For full details, see the [Privacy Policy](PRIVACY.md).

## Requirements

- Python 3.4.4+ (Windows XP SP3 x86/x64 target; Python 3.4.4 is the last official XP release)
- PyQt4 or PyQt5 (PyQt4 is the primary target on Windows XP; PyQt5 is the modern fallback)
- Windows XP SP3, Windows Server 2003, Windows Vista, 7, 10, 11, or Linux (CLI/source)

## Install and run

```bash
pip install .
atlas
```

For purely headless terminal usage (e.g. recovery console, scripts, or safe mode) you can bypass the graphical UI entirely:

```bash
atlas --cli
atlas --version
```

## Compiling for Windows XP

To compile a standalone, single-file portable executable (`Atlas-x86-Portable.exe`) and Inno Setup installer (`Atlas-x86-Setup.exe`) on a Windows XP machine:

```cmd
build.bat
```

For complete step-by-step prerequisite installer links (Python 3.4.4 MSI, PyQt4 binary installer, PyInstaller 3.2.1, Inno Setup 5), see the **[Windows XP Compilation Guide](docs/compiling_on_windows_xp.md)**.

For development:

```bash
pip install -e ".[dev]"
python -m atlas.main
```

## Test

```bash
pytest
```

For headless Linux or CI execution:

```bash
QT_QPA_PLATFORM=offscreen pytest
```

## Build

### Windows XP Portable Executable

Build a standalone portable single-file binary using PyInstaller:

```cmd
pyinstaller main.spec
```

The output is:
- `dist\Atlas-Retro-x86-Portable.exe` (32-bit Windows XP)
- `dist\Atlas-Retro-x86_64-Portable.exe` (64-bit Windows XP / modern Windows)

### Inno Setup Installer

Use Inno Setup 5 (ANSI or Unicode) with `installer/Atlas.iss` to build the Windows XP native setup installer (`dist\Atlas-Retro-Setup.exe`).

## Structure

| Location | Purpose |
| --- | --- |
| `src/atlas/` | Application code and tests |
| `configs/` | Browser definitions and backup policy |
| `assets/` | Application images and icons |
| `scripts/` | Development environment setup scripts |
| `installer/` | Inno Setup Windows installer script (`Atlas.iss`) |

## License

GNU Affero General Public License v3.0 or later. See [LICENSE](LICENSE).
