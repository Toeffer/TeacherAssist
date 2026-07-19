@echo off
setlocal
cd /d "%~dp0"
if not exist "tools\.venv\Scripts\python.exe" (
  echo TeacherAssist environment is missing. Run install.bat first.
  exit /b 1
)
tools\.venv\Scripts\python.exe -m pip install --requirement tools\requirements.lock --upgrade --force-reinstall
if errorlevel 1 exit /b 1
tools\.venv\Scripts\python.exe -m pip check
if errorlevel 1 exit /b 1
tools\.venv\Scripts\python.exe scripts\capability_check.py
