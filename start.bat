@echo off
chcp 65001 >nul 2>&1
title TeacherAssist
cd /d "%~dp0"

:: Desktop-Verknüpfung mit Icon anlegen (einmalig)
set "SHORTCUT=%USERPROFILE%\Desktop\TeacherAssist.lnk"
if not exist "%SHORTCUT%" (
    :: PowerShell-Script zum Erstellen der .lnk-Datei
    powershell -Command ^
        $ws = New-Object -ComObject WScript.Shell; ^
        $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
        $sc.TargetPath = '%~dp0start.bat'; ^
        $sc.WorkingDirectory = '%~dp0'; ^
        $sc.Description = 'TeacherAssist – KI-Assistent für Lehrer'; ^
        $sc.IconLocation = '%~dp0teacherassist.ico'; ^
        $sc.Save(); ^
        Write-Host '✅ Desktop-Verknüpfung angelegt'
)

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
start "TeacherAssist Web" /min "%PYTHON%" -m http.server 8788

:: Tool-Server starten (PDF-Upload, OCR, Lehrplan-Suche)
echo  Starte Tool-Server...
start "TeacherAssist Tool" /min "%PYTHON%" "%~dp0tool_server.py"

:: Kurz warten bis Server bereit ist
timeout /t 3 /nobreak >nul

:: Browser öffnen
echo  Oeffne Browser...
start "" http://localhost:8788

echo.
echo  TeacherAssist laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.

:: Fenster offen lassen damit der User sieht wenn etwas schiefläuft
timeout /t 5 /nobreak >nul
