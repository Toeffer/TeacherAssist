@echo off
chcp 65001 >nul 2>&1
title TeacherAssist - Installation
setlocal EnableDelayedExpansion

:: Arbeitsverzeichnis = Speicherort dieser Datei
cd /d "%~dp0"
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

cls
echo.
echo  ====================================================
echo   TeacherAssist - Automatische Installation
echo  ====================================================
echo.
echo  Dieser Vorgang dauert ca. 5-10 Minuten.
echo  Bitte das Fenster NICHT schliessen.
echo.
pause

:: -- 1. Python pruefen / installieren -----------------------------------------
echo.
echo  [1/4]  Pruefe Python...

python --version >nul 2>&1
if %errorlevel% equ 0 goto python_ok

echo         Nicht gefunden - installiere Python automatisch...
winget install --id Python.Python.3.11 --source winget --scope user ^
    --silent --accept-package-agreements --accept-source-agreements

:: PATH fuer diese Sitzung ergaenzen
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
    "%APPDATA%\Python\Python311\Scripts"
) do set "PATH=!PATH!;%%~P"

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
for /f "tokens=2 delims=. " %%v in ('python --version 2^>^&1') do set "PY_MAJOR=%%v"
for /f "tokens=3 delims=. " %%v in ('python --version 2^>^&1') do set "PY_MINOR=%%v"
if not "%PY_MAJOR%"=="3" goto python_bad_version
if "%PY_MINOR%"=="11" goto python_version_ok
if "%PY_MINOR%"=="12" goto python_version_ok
:python_bad_version
echo PROBLEM: TeacherAssist requires Python 3.11 or 3.12.
exit /b 1
:python_version_ok
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         OK: %%v


:: -- 2. Tesseract OCR installieren --------------------------------------------
echo.
echo  [2/4]  Pruefe Tesseract OCR (fuer Fotos und gescannte Dokumente)...

tesseract --version >nul 2>&1
if %errorlevel% equ 0 (
    echo         OK: Tesseract bereits installiert.
    goto tesseract_ok
)

echo         Nicht gefunden - installiere Tesseract automatisch...
winget install --id UB-Mannheim.TesseractOCR --source winget ^
    --silent --accept-package-agreements --accept-source-agreements

:: Installationspfad suchen und zu PATH hinzufuegen
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
    "$existing = [Environment]::GetEnvironmentVariable('PATH', 'User'); $tess = '%TESS_PATH%'; if ($existing -notlike ('*' + $tess + '*')) { [Environment]::SetEnvironmentVariable('PATH', ($existing + ';' + $tess).TrimStart(';'), 'User') }" >nul 2>&1
echo         OK: Tesseract installiert.

:tesseract_ok


:: -- 3. Python-venv + Abhaengigkeiten -----------------------------------------
:: tool_server.py erwartet zwingend tools\.venv\Scripts\python.exe.
:: start.bat verweigert den Start ohne dieses venv.
echo.
echo  [3/4]  Installiere Programm-Komponenten in tools\.venv (ca. 3-5 Minuten)...

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
.venv\Scripts\python.exe -m pip check
if errorlevel 1 (
    echo PROBLEM: Abhaengigkeitskonflikte wurden gefunden.
    cd ..
    exit /b 1
)
cd ..

:: Optionale Handschrifterkennung (HTR, ~1.3 GB Modell-Download separat ueber
:: die Web-UI, hier nur die Python-Abhaengigkeiten). torch/transformers sind
:: bereits transitiv ueber sentence-transformers installiert -- dieser
:: Schritt pinnt sie nur explizit nach. Schlaegt er fehl (z.B. keine
:: Internetverbindung), bleibt TeacherAssist trotzdem voll installierbar und
:: nutzbar (Tesseract-OCR reicht dafuer aus) -- deshalb KEIN exit /b 1 hier.
echo.
echo  [opt]  Installiere Handschrifterkennung (HTR, optional)...
tools\.venv\Scripts\pip install -r tools\requirements-ocr.txt -q
if errorlevel 1 (
    echo         HINWEIS: HTR-Abhaengigkeiten konnten nicht installiert werden.
    echo         Handschrifterkennung ist vorerst nicht verfuegbar, alles andere
    echo         funktioniert weiterhin normal.
) else (
    echo         OK: HTR-Abhaengigkeiten installiert.
)

tools\.venv\Scripts\python.exe -m pip check
if errorlevel 1 (
    echo PROBLEM: Abhaengigkeitskonflikte wurden gefunden.
    exit /b 1
)
tools\.venv\Scripts\python.exe scripts\capability_check.py
if errorlevel 1 exit /b 1
echo         OK: Alle Komponenten installiert und geprueft.

if exist "web_dist\index.html" (
    echo         OK: Frontend-Build bereits vorhanden ^(web_dist\^), Node.js nicht benoetigt.
    goto frontend_ok
)

where node >nul 2>&1
if errorlevel 1 (
    echo PROBLEM: Kein Frontend-Build vorhanden und Node.js wurde nicht gefunden.
    echo Installiere Node.js 20+ LTS und starte install.bat erneut,
    echo oder verwende ein Release-ZIP mit bereits enthaltenem web_dist\-Ordner.
    exit /b 1
)
call npm ci
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1

:frontend_ok


:: -- 4. Desktop-Verknuepfung --------------------------------------------------
:: tool_server.py legt memory/, logs/, uploads/, exports/, tools/chroma_db/ beim
:: ersten Start selbst an - wir erzwingen keine Spiegelung nach %USERPROFILE%.
:: Settings (Provider, Modell, API-Key) werden zur Laufzeit ueber die Web-UI in
:: settings.json gespeichert. Keine separate Config-Datei mehr noetig.
echo.
echo  [4/4]  Erstelle Desktop-Verknuepfung...

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%INSTALL_DIR%\scripts\create_shortcut.ps1" ^
    -InstallDir "%INSTALL_DIR%"


:: -- Fertig --------------------------------------------------------------------
echo.
echo  ====================================================
echo   Installation abgeschlossen!
echo  ====================================================
echo.
echo   So startest du TeacherAssist:
echo.
echo     Doppelklick auf "LehrerAgent starten" auf deinem Desktop
echo     (oder direkt start.bat aus diesem Ordner)
echo.
echo   Beim ersten Start oeffnet sich der Browser auf
echo   http://localhost:8789/ und der Assistent fuehrt
echo   dich durch die Einrichtung deines Profils.
echo.
echo   API-Key und Provider werden in den Einstellungen
echo   der Web-UI hinterlegt (gespeichert in settings.json).
echo.
echo  ====================================================
echo.
pause
