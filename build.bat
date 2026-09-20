@echo off
REM ============================================================================
REM Atlas Build Helper (delegates to scripts\build_windows.bat)
REM ============================================================================
call "%~dp0scripts\build_windows.bat" %*
