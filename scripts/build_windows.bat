@echo off
REM ============================================================================
REM Atlas Windows XP / 32-bit Compilation and Packaging Script
REM ============================================================================

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

echo ========================================================
echo   Atlas Windows Build ^& Packaging
echo ========================================================
echo.

REM ---------------------------------------------------------------------------
REM 1. Verify Python
REM ---------------------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo.
    echo On Windows XP 32-bit, please install Python 3.4.4:
    echo   File: python-3.4.4.msi
    echo   URL:  https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi
    echo Ensure "Add python.exe to Path" is selected during installation.
    exit /b 1
)

for /f "tokens=*" %%V in ('python -c "import sys; print(sys.version.split()[0])"') do set "PY_VER=%%V"
for /f "tokens=*" %%B in ('python -c "import struct; print('32-bit' if struct.calcsize('P') == 4 else '64-bit')"') do set "PY_BITS=%%B"

echo [OK] Python %PY_VER% (%PY_BITS%) detected.

REM ---------------------------------------------------------------------------
REM 2. Verify Qt Binding (PyQt4 preferred, PyQt5 fallback)
REM ---------------------------------------------------------------------------
python -c "import PyQt4.QtCore" >nul 2>&1
if not errorlevel 1 (
    echo [OK] PyQt4 detected.
    goto qt_found
)

python -c "import PyQt5.QtCore" >nul 2>&1
if not errorlevel 1 (
    echo [OK] PyQt5 detected.
    goto qt_found
)

echo.
echo [ERROR] Neither PyQt4 nor PyQt5 was found in your Python environment.
echo.
echo For Windows XP 32-bit, PyQt4 is required.
echo Because PyPI no longer supports Windows XP / TLS 1.0, install PyQt4 via
echo the official Windows binary installer:
echo.
echo   Installer: PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe
echo   Archive:   https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/
echo.
echo Or install using a pre-compiled wheel:
echo   python -m pip install PyQt4-4.11.4-cp34-cp34m-win32.whl
echo.
exit /b 1

:qt_found

REM ---------------------------------------------------------------------------
REM 3. Verify PyInstaller
REM ---------------------------------------------------------------------------
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller is not installed.
    echo.
    echo For Python 3.4.4 on Windows XP, install PyInstaller 3.2.1 or 3.3.1:
    echo   python -m pip install pyinstaller==3.2.1 pywin32
    echo.
    exit /b 1
)

echo [OK] PyInstaller detected.
echo.

REM ---------------------------------------------------------------------------
REM 4. Compile Standalone Executable via main.spec
REM ---------------------------------------------------------------------------
echo Compiling Atlas standalone executable with PyInstaller...
python -m PyInstaller main.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo [OK] Executable compiled successfully in dist\
echo.

REM ---------------------------------------------------------------------------
REM 5. Compile Inno Setup 5 Installer (Optional)
REM ---------------------------------------------------------------------------
set "ISCC_EXE="
if exist "%ProgramFiles%\Inno Setup 5\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 5\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"

if not defined ISCC_EXE (
    where iscc >nul 2>&1
    if not errorlevel 1 set "ISCC_EXE=iscc"
)

if defined ISCC_EXE (
    echo Compiling Windows XP installer with Inno Setup 5...
    "%ISCC_EXE%" installer\Atlas.iss
    if errorlevel 1 (
        echo [WARNING] Inno Setup compilation had issues.
    ) else (
        echo [OK] Installer compiled in dist\
    )
) else (
    echo [INFO] Inno Setup 5 (ISCC.exe) not found.
    echo        To build the setup installer on Windows XP, install Inno Setup 5.5.9:
    echo        https://files.jrsoftware.org/ispack/ispack-5.5.9.exe
)

echo.
echo ========================================================
echo   Build Complete!
echo ========================================================
dir dist
endlocal
