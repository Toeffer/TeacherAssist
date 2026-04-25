@echo off
chcp 65001 >nul 2>&1
title LehrerAgent
cd /d "%~dp0"

echo.
echo  Starte LehrerAgent...
echo.

:: Python bestimmen (venv bevorzugt, dann System-Python)
set "PYTHON=%~dp0tools\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo  PROBLEM: Python wurde nicht gefunden.
        echo  Bitte zuerst install.bat ausfuehren.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON=python"
)

:: Prüfen ob index.html vorhanden
if not exist "%~dp0index.html" (
    echo  PROBLEM: index.html nicht gefunden.
    echo  Bitte sicherstellen, dass alle Dateien vollstaendig sind.
    echo.
    pause
    exit /b 1
)

:: Web-Server starten
echo  Starte Web-Server...
start "" /min "%PYTHON%" -m http.server 8788

:: Tool-Server starten (PDF-Upload, OCR, Lehrplan-Suche)
echo  Starte Tool-Server...
start "" /min "%PYTHON%" "%~dp0tool_server.py"

:: Kurz warten bis Server bereit ist
timeout /t 3 /nobreak >nul

:: OpenClaw starten (falls installiert)
where openclaw >nul 2>&1
if %errorlevel% equ 0 (
    echo  Starte OpenClaw...
    set "BRAIN_PROVIDER=openrouter"
    set "BRAIN_MODEL=deepseek/deepseek-chat"
    set "BRAIN_API_KEY="
    set "BRAIN_FALLBACK_MODEL=deepseek/deepseek-chat"
    set "BRAIN_LOCAL_MODEL=gemma3:4b"
    if exist "%~dp0settings.json" (
        for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "try { $s=(Get-Content '%~dp0settings.json' -Raw | ConvertFrom-Json); $s.provider } catch { 'openrouter' }"`) do set "BRAIN_PROVIDER=%%a"
        for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "try { $s=(Get-Content '%~dp0settings.json' -Raw | ConvertFrom-Json); $s.ollamaModel } catch { 'gemma3:4b' }"`) do set "BRAIN_LOCAL_MODEL=%%a"
        for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "try { $s=(Get-Content '%~dp0settings.json' -Raw | ConvertFrom-Json); $s.model } catch { '' }"`) do set "BRAIN_MODEL=%%a"
    )
    if "%BRAIN_PROVIDER%"=="ollama" set "BRAIN_MODEL=%BRAIN_LOCAL_MODEL%"
    start "" /min openclaw start
    echo  OpenClaw gestartet ^(Provider: %BRAIN_PROVIDER%^)
) else (
    echo  OpenClaw nicht installiert – wird uebersprungen.
    echo  ^(npm install -g openclaw um es zu installieren^)
)

:: Browser öffnen
echo  Oeffne Browser...
start "" http://localhost:8788

echo.
echo  LehrerAgent laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.

:: Fenster offen lassen damit der User sieht wenn etwas schiefläuft
timeout /t 5 /nobreak >nul
