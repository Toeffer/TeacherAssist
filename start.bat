@echo off
chcp 65001 >nul 2>&1
title TeacherAssist
cd /d "%~dp0"

echo.
echo  Starte TeacherAssist...
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

:: Pruefen ob index.html vorhanden
if not exist "%~dp0index.html" (
    echo  PROBLEM: index.html nicht gefunden.
    echo  Bitte sicherstellen, dass alle Dateien vollstaendig sind.
    echo.
    pause
    exit /b 1
)

:: Tool-Server starten (Web-App, PDF-Upload, OCR, Lehrplan-Suche)
echo  Starte Tool-Server...
powershell -NoProfile -Command "try { $c = [Net.Sockets.TcpClient]::new('127.0.0.1', 8789); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    start "TeacherAssist Tool" /min "%PYTHON%" "%~dp0tool_server.py"
) else (
    echo  Tool-Server laeuft bereits.
)

:: Kurz warten bis Server bereit ist
timeout /t 3 /nobreak >nul

:: Server pruefen, damit Startfehler sichtbar bleiben
set "TOOL_OK="

echo  Pruefe Tool-Server...
for /l %%I in (1,1,15) do (
    powershell -NoProfile -Command "try { $c = [Net.Sockets.TcpClient]::new('127.0.0.1', 8789); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "TOOL_OK=1"
        goto tool_ready
    )
    timeout /t 1 /nobreak >nul
)

:tool_ready
if not defined TOOL_OK (
    echo.
    echo  PROBLEM: Tool-Server auf http://localhost:8789/health ist nicht erreichbar.
    echo  Bitte pruefen, ob Port 8789 bereits belegt ist oder tool_server.py beim Start abstuerzt.
    echo.
    pause
    exit /b 1
)

:: Browser oeffnen
echo  Oeffne Browser...
explorer.exe "http://localhost:8789/"
if errorlevel 1 start "" "http://localhost:8789/"

echo.
echo  TeacherAssist laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.

:: Fenster offen lassen damit der User sieht wenn etwas schieflaeuft
timeout /t 5 /nobreak >nul
exit /b 0
