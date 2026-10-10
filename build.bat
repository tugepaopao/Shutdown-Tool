@echo off
REM ============================================================
REM  Build script - Haozaizi Auto Shutdown Tool   (author @wenhao)
REM  Step 1: generate icons
REM  Step 2: build portable single-file exe with PyInstaller
REM  Step 3: build installer (with uninstaller) with Inno Setup
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo [1/3] Generating icon files ...
".venv\Scripts\python.exe" tools\make_icon.py
if errorlevel 1 goto :err

echo [2/3] Building portable exe ...
".venv\Scripts\pyinstaller.exe" --noconfirm --workpath build_work --distpath dist build.spec
if errorlevel 1 goto :err

echo [3/3] Building installer ...
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    "%ISCC%" installer\setup.iss
    if errorlevel 1 goto :err
) else (
    echo WARNING: Inno Setup 6 not found. Install it first:
    echo   winget install -e --id JRSoftware.InnoSetup
)

echo.
echo ================ DONE ================
echo Portable exe : dist\
echo Installer    : output\
exit /b 0

:err
echo.
echo *** BUILD FAILED ***
exit /b 1
