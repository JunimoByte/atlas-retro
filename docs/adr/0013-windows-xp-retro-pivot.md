# 13. Targeting Windows XP: Python 3.4, PyQt4, and Platform Trimming
Date: 2026-09-20

## Context
Atlas originally targeted modern desktop operating systems (Windows 10/11, modern Linux distributions, and FreeBSD), leveraging modern Python 3.8+ language constructs and packaging formats such as MSIX for the Microsoft Store, AppImage, Debian packages, and FreeBSD pkg archives.

To serve retro-computing environments, legacy workstations, and offline machines running Windows XP (NT 5.1 / NT 5.2), the application required a fundamental pivot: reducing runtime requirements to the final officially supported Python release on Windows XP (Python 3.4.4) and adopting PyQt4 (Qt 4.8), while eliminating packaging debt that cannot function on legacy systems.

## Decision
1. **Target Runtime**: Downgrade the baseline target to **Python 3.4.4** on **Windows XP SP3 (x86/x64)**.
2. **GUI Framework**: Adopt **PyQt4** (Qt 4.8) as the primary GUI toolkit on Windows XP, maintaining an adaptive compatibility shim in `atlas.compatibility.qt` that strictly switches between PyQt4 and PyQt5 (PyQt6 is dropped).
3. **Syntax & Standard Library Constraints**:
   - Strictly prohibit Python 3.6+ features: no f-strings (PEP 498), no variable type annotations (PEP 526 `var: type = val`), no `enum.auto()`.
   - Work around Python 3.5+ standard library omissions: use fallback directory scanning (`safe_scandir`) in place of `os.scandir`, avoid `pathlib.Path.read_text()` / `write_text()` / `home()`, and replace `subprocess.run` with `subprocess.call`.
   - Ensure all `zipfile.ZipFile` invocations avoid Python 3.7+ / 3.8+ keyword arguments (`compresslevel`, `strict_timestamps`).
4. **Platform Scope Adjustments**:
   - **FreeBSD / GhostBSD**: Completely dropped. All BSD installation scripts, packaging configs, and OS normalizations are deleted.
   - **Linux**: AppImage and Debian package builders dropped; core CLI/source execution viability is preserved.
   - **Windows Modern / Store**: Microsoft Store MSIX packaging and associated manifests dropped.
5. **Win32 API Adaptation for Windows XP**:
   - Use `SHGetFolderPathW` (`CSIDL_PERSONAL`, `CSIDL_PROFILE`) and registry queries rather than Vista+ `SHGetKnownFolderPath`.
   - Guard against `dwmapi.dll` which is absent on Windows XP; allow native Windows XP Luna and Classic styles to render without intrusive modern stylesheets.

## Consequences
- **Positive**: Atlas operates seamlessly on Windows XP SP3, 2003, and later versions using Python 3.4.4. The codebase is significantly leaner with 0 extraneous packaging scripts for discontinued platforms.
- **Negative**: Development requires maintaining Python 3.4 syntax discipline (enforced via AST validation in test suites) and handling PyQt4/PyQt5 API differences.
