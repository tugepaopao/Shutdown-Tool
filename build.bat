@echo off
setlocal
cd /d "%~dp0"
set "SHUTDOWN_BUILD_LAYOUT="
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --workpath build_portable --distpath dist build.spec
if errorlevel 1 exit /b 1
set "SHUTDOWN_BUILD_LAYOUT=onedir"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --workpath build_installed --distpath installed build.spec
if errorlevel 1 exit /b 1
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
 "%ISCC%" "/DSrcExeDir=..\installed\定时关机工具" installer\setup.iss
 if errorlevel 1 exit /b 1
) else (
 echo EXE builds complete. Install Inno Setup 6.5+ to build the installer.
)
