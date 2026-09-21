# Overview

Atlas is a specialized, offline utility designed to safeguard your web browsing data on legacy and retro systems, specifically targeting Windows XP (NT 5.1 / 5.2) and modern operating systems alike.

## Features
Atlas supports over **300+** different browser variants. It detects and backs up not just modern releases, but also older versions and retro engines:
*   **Legacy Browsers & Retro Engines** (Older Internet Explorer, Firefox 2.x-52.x ESR, Pale Moon, K-Meleon, Netscape, Opera Presto)
*   **Standard Chromium & Gecko Releases**
*   **Development & Canary Channels**

> **Disclaimer:** Due to Chromium's hardware-level encryption (DPAPI), logins must be manually exported/imported. All other data (Bookmarks, History, Settings) is fully backed up.

### 🖥️ OS & Runtime Compatibility
Engineered for reliable execution across legacy and modern platforms:
*   **Windows XP (NT 5.1 / 5.2)**: Primary deployment target running Python 3.4.4 and PyQt4 (Qt 4.8). Uses Windows XP Win32 APIs (`SHGetFolderPathW`), legacy shell folders (`%USERPROFILE%\My Documents\Backup`), and guards against modern DWM/Vista+ APIs.
*   **Modern Windows (Vista, 7, 8, 10, 11)**: Full compatibility supported.
*   **Linux**: CLI and source execution supported via Python.

### 📦 Self-Contained Architecture
Atlas packages its Python application and Qt resources into a portable single-file executable or native Inno Setup 5 installer configured for Windows XP (`MinVersion=5.1.2600`). For building on Windows XP, see [Compiling on Windows XP](compiling_on_windows_xp.md).

## Running Atlas

**From Source:**
```bash
python -m atlas.main
python -m atlas.main --cli
python -m atlas.main --version
```

**As a Package:**
```bash
pip install .
atlas
atlas --cli
atlas --version
```

## Project Structure

```
Atlas/
├── pyproject.toml         # Project metadata and dependencies (>=3.4)
├── main.spec              # Windows XP portable PyInstaller specification
├── src/                   # Source code
│   └── atlas/             # Main package
│       ├── main.py        # Bootstrapper router
│       ├── gui.py         # Graphical entry point (PyQt4/5)
│       ├── cli.py         # Headless entry point
│       ├── args.py        # Command-line parser & version resolution
│       ├── compatibility/ # Cross-binding Qt abstraction layer
│       │   └── qt.py      # PyQt4/PyQt5 dual-switch & enums shim
│       ├── lib/           # Core utilities
│       │   ├── browsers.py
│       │   ├── directories.py
│       │   ├── integration.py
│       │   ├── permissions.py
│       │   ├── read.py
│       │   ├── system.py
│       │   └── themes.py
│       ├── backup/        # Backup logic
│       │   ├── worker.py
│       │   ├── runner.py
│       │   ├── pipeline.py
│       │   ├── archive.py
│       │   ├── filter.py
│       │   ├── attribute.py
│       │   ├── disk.py
│       │   ├── profile.py
│       │   └── size.py
│       ├── display/       # UI components
│       │   ├── window.py
│       │   ├── controller.py
│       │   ├── signals.py
│       │   ├── controls.py
│       │   └── popup.py
│       ├── ui/            # UI layouts
│       │   └── interface.py
│       └── tests/         # Unit and integration test suite
├── assets/                # Application resources
│   ├── icons/             # Application icons
│   └── images/            # UI images
├── configs/               # JSON configuration files
│   ├── browsers.json
│   ├── types.json
│   └── blacklist.json
├── installer/             # Inno Setup Windows XP installer (Atlas.iss)
├── scripts/               # Environment setup scripts
└── docs/                  # Documentation and ADRs
```
