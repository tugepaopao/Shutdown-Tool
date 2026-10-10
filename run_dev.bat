@echo off
REM Run the tool from source (development mode) - author @wenhao
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" "src\main.py" %*
