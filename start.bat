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

:: Browser öffnen
echo  Oeffne Browser...
start "" http://localhost:8788

echo.
echo  LehrerAgent laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.

:: Fenster offen lassen damit der User sieht wenn etwas schiefläuft
timeout /t 5 /nobreak >nul
