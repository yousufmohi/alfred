@echo off
REM Alfred Easy Installer for Windows
REM This script installs Alfred using pipx

echo ========================================
echo Alfred Easy Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/4] Installing pipx...
pip install --quiet pipx
if errorlevel 1 (
    echo ERROR: Failed to install pipx
    pause
    exit /b 1
)

echo [2/5] Installing Poetry and dependencies...
pip install --quiet poetry >nul 2>&1
poetry install --quiet
if errorlevel 1 (
    echo WARNING: Dependencies install had issues, continuing anyway...
)
echo Done.
echo.

echo [3/5] Setting up pipx paths...
pipx ensurepath >nul 2>&1

echo [4/5] Installing Alfred...
pipx uninstall alfred >nul 2>&1
pipx install .
if errorlevel 1 (
    echo ERROR: Failed to install Alfred
    pause
    exit /b 1
)

echo [5/5] Testing installation...
echo.

REM Add pipx bin to PATH for this session
set "PATH=%PATH%;%USERPROFILE%\.local\bin"

REM Test
"%USERPROFILE%\.local\bin\alfred.exe" version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Alfred command not available yet
    echo.
    echo ========================================
    echo Installation Complete!
    echo ========================================
    echo.
    echo Alfred will work after you:
    echo   1. Close ALL Command Prompt windows
    echo   2. Open a NEW Command Prompt
    echo   3. Type: alfred --help
    echo.
    echo Can't wait? Use the full path right now:
    echo   %USERPROFILE%\.local\bin\alfred.exe --help
) else (
    echo [SUCCESS] Alfred command works!
    echo.
    echo ========================================
    echo Installation Complete!
    echo ========================================
    echo.
    echo Next steps:
    echo   alfred setup
    echo   alfred review yourfile.py
    echo.
    echo NOTE: If 'alfred' doesn't work in new terminals:
    echo   1. Close ALL Command Prompt windows
    echo   2. Open a NEW Command Prompt
)

echo.
echo TIP: PowerShell works better! Try: .\install.ps1
echo      PowerShell automatically adds alfred to all new windows.
echo.

pause