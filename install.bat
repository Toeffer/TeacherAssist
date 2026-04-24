@echo off
chcp 65001 >nul 2>&1
title LehrerAgent – Installation
setlocal EnableDelayedExpansion

:: Arbeitsverzeichnis = Speicherort dieser Datei
cd /d "%~dp0"
set "INSTALL_DIR=%~dp0"
:: Trailing-Backslash entfernen
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

cls
echo.
echo  ====================================================
echo   LehrerAgent - Automatische Installation
echo  ====================================================
echo.
echo  Dieser Vorgang dauert ca. 5-10 Minuten.
echo  Bitte das Fenster NICHT schliessen.
echo.
pause

:: ── 1. Python prüfen / installieren ─────────────────────────────────────────
echo.
echo  [1/6]  Pruefe Python...

python --version >nul 2>&1
if %errorlevel% equ 0 goto python_ok

echo         Nicht gefunden - installiere Python automatisch...
winget install --id Python.Python.3.11 --source winget --scope user ^
    --silent --accept-package-agreements --accept-source-agreements

:: PATH für diese Sitzung ergänzen
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
    "%APPDATA%\Python\Python311\Scripts"
) do set "PATH=%PATH%;%%~P"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  PROBLEM: Python konnte nicht automatisch installiert werden.
    echo.
    echo  Bitte manuell installieren:
    echo    1. Oeffne deinen Browser
    echo    2. Gehe zu:  https://www.python.org/downloads/
    echo    3. Klicke auf "Download Python" und installiere das Programm
    echo    4. Starte dann install.bat erneut
    echo.
    pause
    exit /b 1
)

:python_ok
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         OK: %%v


:: ── 2. Tesseract OCR installieren ────────────────────────────────────────────
echo.
echo  [2/6]  Pruefe Tesseract OCR (fuer Fotos und gescannte Dokumente)...

tesseract --version >nul 2>&1
if %errorlevel% equ 0 (
    echo         OK: Tesseract bereits installiert.
    goto tesseract_ok
)

echo         Nicht gefunden - installiere Tesseract automatisch...
winget install --id UB-Mannheim.TesseractOCR --source winget ^
    --silent --accept-package-agreements --accept-source-agreements

:: Installationspfad suchen und zu PATH hinzufügen
for %%P in (
    "C:\Program Files\Tesseract-OCR"
    "C:\Program Files (x86)\Tesseract-OCR"
    "%LOCALAPPDATA%\Programs\Tesseract-OCR"
) do (
    if exist "%%~P\tesseract.exe" (
        set "TESS_PATH=%%~P"
        goto tess_found
    )
)

echo         HINWEIS: Tesseract konnte nicht automatisch installiert werden.
echo         Fotos und gescannte Dokumente koennen vorerst nicht eingelesen werden.
echo         Alles andere funktioniert weiterhin normal.
goto tesseract_ok

:tess_found
set "PATH=%PATH%;%TESS_PATH%"
powershell -NoProfile -Command ^
    "[Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';%TESS_PATH%', 'User')" >nul 2>&1
echo         OK: Tesseract installiert.

:tesseract_ok


:: ── 3. Python-Pakete installieren ────────────────────────────────────────────
echo.
echo  [3/6]  Installiere Programm-Komponenten (ca. 3-5 Minuten)...

cd tools

if not exist ".venv" python -m venv .venv

.venv\Scripts\python.exe -m pip install --upgrade pip -q >nul 2>&1
.venv\Scripts\pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo.
    echo  PROBLEM: Komponenten konnten nicht installiert werden.
    echo  Bitte Internetverbindung pruefen und install.bat nochmal starten.
    cd ..
    pause
    exit /b 1
)
echo         OK: Alle Komponenten installiert.
cd ..


:: ── 4. Programmverzeichnis einrichten ────────────────────────────────────────
echo.
echo  [4/6]  Richte Programmverzeichnis ein...

set "OC_DIR=%USERPROFILE%\.openclaw"
if not exist "%OC_DIR%"                            mkdir "%OC_DIR%"
if not exist "%OC_DIR%\memory"                     mkdir "%OC_DIR%\memory"
if not exist "%OC_DIR%\memory\bewertungsraster"    mkdir "%OC_DIR%\memory\bewertungsraster"
if not exist "%OC_DIR%\skills"                     mkdir "%OC_DIR%\skills"
if not exist "%OC_DIR%\logs"                       mkdir "%OC_DIR%\logs"

:: Memory-Vorlagen kopieren (nur wenn noch nicht vorhanden)
for %%f in (lehrerprofil.md lehrplan_index.md korrekturprotokoll.md vergangene_stunden.md) do (
    if not exist "%OC_DIR%\memory\%%f" copy "memory\%%f" "%OC_DIR%\memory\%%f" >nul
)

:: Skills kopieren (immer aktuell halten)
xcopy "skills" "%OC_DIR%\skills" /E /I /Y /Q >nul 2>&1

echo         OK: Programmverzeichnis eingerichtet.


:: ── 5. Konfiguration erstellen ───────────────────────────────────────────────
echo.
echo  [5/6]  Konfiguration einrichten...

set "CONFIG=%OC_DIR%\config.yaml"

if not exist "%CONFIG%" (
    powershell -NoProfile -ExecutionPolicy Bypass ^
        -File "%INSTALL_DIR%\scripts\setup_config.ps1" ^
        -InstallDir "%INSTALL_DIR%" ^
        -ConfigFile "%CONFIG%"
) else (
    echo         OK: Konfiguration bereits vorhanden.
)

:: API-Schlüssel abfragen
powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%INSTALL_DIR%\scripts\setup_apikey.ps1" ^
    -ConfigFile "%CONFIG%"


:: ── 6. Desktop-Verknüpfung erstellen ─────────────────────────────────────────
echo.
echo  [6/6]  Erstelle Desktop-Verknuepfung...

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%INSTALL_DIR%\scripts\create_shortcut.ps1" ^
    -InstallDir "%INSTALL_DIR%"


:: ── Fertig ────────────────────────────────────────────────────────────────────
echo.
echo  ====================================================
echo   Installation abgeschlossen!
echo  ====================================================
echo.
echo   So startest du den LehrerAgent:
echo.
echo     Doppelklick auf "LehrerAgent starten" auf deinem Desktop
echo.
echo   Beim ersten Start wird der Assistent dich durch
echo   die Einrichtung deines Profils fuehren.
echo.
echo  ====================================================
echo.
pause
