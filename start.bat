@echo off
chcp 65001 >nul 2>&1
title LehrerAgent
cd /d "%~dp0"

echo.
echo  Starte LehrerAgent...
echo.

:: Prüfen ob OpenClaw installiert ist
where openclaw >nul 2>&1
if %errorlevel% neq 0 (
    echo  PROBLEM: OpenClaw wurde nicht gefunden.
    echo.
    echo  Bitte stelle sicher, dass OpenClaw installiert ist.
    echo  Hilfe: siehe SETUP.md im Programmordner.
    echo.
    pause
    exit /b 1
)

:: Prüfen ob Konfiguration vorhanden ist
set "CONFIG=%USERPROFILE%\.openclaw\config.yaml"
if not exist "%CONFIG%" (
    echo  PROBLEM: Konfigurationsdatei nicht gefunden.
    echo.
    echo  Bitte zuerst install.bat ausfuehren.
    echo.
    pause
    exit /b 1
)

:: Prüfen ob API-Schlüssel gesetzt ist
findstr /C:"ANTHROPIC_API_KEY" "%CONFIG%" >nul 2>&1
if %errorlevel% equ 0 (
    echo  HINWEIS: Kein API-Schluessel konfiguriert.
    echo.
    echo  Bitte install.bat erneut ausfuehren oder den Schluessel
    echo  manuell in %CONFIG% eintragen.
    echo.
    pause
    exit /b 1
)

:: OpenClaw starten (im Hintergrund)
echo  OpenClaw wird gestartet...
start "" /min openclaw start --config "%CONFIG%"

:: Kurz warten bis OpenClaw bereit ist
timeout /t 3 /nobreak >nul

:: Browser öffnen
echo  Oeffne Browser...
start "" http://localhost:18789

echo.
echo  LehrerAgent laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.

:: Fenster offen lassen damit der User sieht wenn etwas schiefläuft
timeout /t 5 /nobreak >nul
