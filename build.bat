@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --workpath build_work --distpath dist build.spec
if errorlevel 1 exit /b 1
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
 "%ISCC%" installer\setup.iss
 if errorlevel 1 exit /b 1
) else (
 echo Portable build complete. Install Inno Setup 6.5+ to build the installer.
)
