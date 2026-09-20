# Compiling Atlas on Windows XP (32-bit / 64-bit)

This guide details how to set up the environment and compile Atlas into a standalone portable executable (`Atlas-x86-Portable.exe`) and Inno Setup installer (`Atlas-x86-Setup.exe`) on **Windows XP Professional (32-bit SP3 / 64-bit SP2)**.

---

## Technical Background: Why Can't Pip "Just Grab" PyQt4 on XP?

When setting up on Windows XP, automated tools like `pip` cannot automatically download or compile PyQt4 for three main reasons:
1. **TLS 1.2 / Modern HTTPS Deprecation**: Windows XP only supported TLS 1.0 out of the box. Modern package repositories (such as PyPI and Python.org) require TLS 1.2 or TLS 1.3, preventing un-patched XP systems and Python 3.4's bundled pip from communicating over HTTPS directly.
2. **PyQt4 Distribution Model**: PyPI never hosted pre-compiled Windows binary wheels for PyQt4 on Python 3.4. Running `pip install PyQt4` on PyPI attempts to compile PyQt4 from C++ source via `sip` and Visual C++ 2010 with Qt 4.8 headers, which fails without a full native SDK.
3. **Official Binary Installers**: On Windows XP, PyQt4 was officially distributed by Riverbank Computing as a standalone executable installer that deploys Qt 4.8.7 runtime DLLs, plugins, and Python bindings directly into `C:\Python34\Lib\site-packages`.

---

## Required Prerequisites (Install Once)

Download these official installers on a modern machine (or via a USB drive / local share) and run them on your Windows XP machine in this order:

### 1. Python 3.4.4 (32-bit x86)
* **File:** `python-3.4.4.msi`
* **Download:** [Python 3.4.4 Release Archives](https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi)
* **Installation Note:** In the installer, scroll to the bottom of the component tree and enable **"Add python.exe to Path"**.

### 2. PyQt4 for Python 3.4 (32-bit x86)
* **File:** `PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe`
* **Download:** [SourceForge Riverbank Archives](https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/)
* **Installation Note:** Run the `.exe` installer. It automatically detects your Python 3.4 installation at `C:\Python34` and places all Qt 4.8.7 libraries in `Lib\site-packages\PyQt4`.
* *(Alternative)* If you have the pre-compiled wheel `PyQt4-4.11.4-cp34-cp34m-win32.whl`, you can install it offline:
  ```cmd
  python -m pip install PyQt4-4.11.4-cp34-cp34m-win32.whl
  ```

### 3. PyWin32 for Python 3.4 (32-bit x86)
* **File:** `pywin32-219.win32-py3.4.exe` (or build 220)
* **Download:** [GitHub pywin32 Releases](https://github.com/mhammond/pywin32/releases)
* **Installation Note:** Run the installer to register Win32 API extensions for Python.

### 4. PyInstaller 3.2.1 or 3.3.1
* Modern PyInstaller 5+ dropped Python 3.4 and Windows XP. **PyInstaller 3.2.1** is the recommended, battle-tested version for Windows XP:
  ```cmd
  python -m pip install pyinstaller==3.2.1
  ```
* *(Offline alternative)* If your machine is completely offline, copy the `PyInstaller-3.2.1.tar.gz` archive to the machine and run:
  ```cmd
  python -m pip install PyInstaller-3.2.1.tar.gz
  ```

### 5. Inno Setup 5 (Optional - for generating Setup EXE)
* **File:** `isetup-5.5.9-unicode.exe`
* **Download:** [Inno Setup 5 Downloads](https://files.jrsoftware.org/ispack/ispack-5.5.9.exe)
* **Note:** Inno Setup 6 dropped Windows XP support; version 5.5.9 or 5.6.1 is required.

---

## Compiling Atlas

Once the prerequisites above are installed, open a Command Prompt in the Atlas folder and run:

```cmd
build.bat
```

The script will automatically:
1. Verify Python 3.4 (32-bit) on `PATH`.
2. Confirm PyQt4 is available and ready.
3. Confirm PyInstaller is present.
4. Execute `python -m PyInstaller main.spec --clean --noconfirm`.
5. Check for Inno Setup 5 (`ISCC.exe`) and automatically compile `installer\Atlas.iss`.
6. Output the binaries into the `dist\` folder:
   - **`dist\Atlas-x86-Portable.exe`**: Standalone, single-file portable executable. Runs on any Windows XP machine without needing Python or Qt installed!
   - **`dist\Atlas-x86-Setup.exe`**: Inno Setup installer configured for Windows XP (`MinVersion=5.1.2600`).

---

## Running Atlas from Source on Windows XP

If you want to run or test Atlas directly without compiling an executable:

```cmd
python -m atlas.main
```
Or for command-line headless mode:
```cmd
python -m atlas.main --cli
```
