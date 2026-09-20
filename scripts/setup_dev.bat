@echo off
REM ============================================================================
REM Atlas dev environment setup (Windows XP / Python 3.4 / PyQt4)
REM ============================================================================

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_PATH=%PROJECT_ROOT%\venv"

REM ---------------------------------------------------------------------------
REM 1. Create venv if it doesn't exist
REM ---------------------------------------------------------------------------
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv --system-site-packages "%VENV_PATH%"
    if errorlevel 1 (
        echo Fallback: trying virtualenv...
        virtualenv --system-site-packages "%VENV_PATH%"
        if errorlevel 1 (
            echo ERROR: Failed to create virtual environment.
            echo Ensure Python 3.4+ is installed and on PATH.
            exit /b 1
        )
    )
) else (
    echo Existing virtual environment found.
)

REM ---------------------------------------------------------------------------
REM 2. Activate
REM ---------------------------------------------------------------------------
echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"

REM ---------------------------------------------------------------------------
REM 3. Install dependencies
REM ---------------------------------------------------------------------------
echo Installing dependencies...
python -m pip install -e "%PROJECT_ROOT%[dev]"

echo.
echo NOTE for Windows XP:
echo PyQt4 for Python 3.4 is typically installed via the official binary installer:
echo   PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe
echo or by wheel if available.
echo.
echo Dev environment configured!
endlocal