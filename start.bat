@echo off
chcp 65001 >nul 2>&1
title TeacherAssist
cd /d "%~dp0"

echo.
echo  Starte TeacherAssist...
echo.

:: Port wie in tool_server.py (TEACHERASSIST_PORT, Standard 8789).
if not defined TEACHERASSIST_PORT set "TEACHERASSIST_PORT=8789"
:: Das Server-Log liegt im Laufzeit-Datenverzeichnis, nicht im Programmordner.
set "LOG_FILE=%LOCALAPPDATA%\TeacherAssist\logs\tool_server.log"
if defined TEACHERASSIST_DATA_DIR set "LOG_FILE=%TEACHERASSIST_DATA_DIR%\logs\tool_server.log"

:: Python AUSSCHLIESSLICH aus venv (von install.bat angelegt).
:: Kein System-Python-Fallback, weil dort die Abhaengigkeiten fehlen
:: und der Server beim ersten Request haengen bleibt (Port belegt, /health Timeout).
set "PYTHON=%~dp0tools\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo  PROBLEM: Python-venv nicht gefunden.
    echo  Erwartet: %PYTHON%
    echo  Bitte zuerst install.bat ausfuehren.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0index.html" (
    echo  PROBLEM: index.html nicht gefunden.
    echo  Bitte sicherstellen, dass alle Dateien vollstaendig sind.
    echo.
    pause
    exit /b 1
)

:: HTTP /health pruefen (nicht nur TCP) - TCP allein erkennt Zombie-Prozesse nicht.
echo  Pruefe Tool-Server...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:%TEACHERASSIST_PORT%/api/v1/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo  Tool-Server laeuft bereits.
    goto open_browser
)

:: /health antwortet nicht. Lauscht trotzdem ein Python-Prozess auf dem Port, ist
:: es eine haengende TeacherAssist-Instanz: beenden. Andere Programme bleiben
:: unangetastet - dann stattdessen TEACHERASSIST_PORT auf einen freien Port setzen.
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort %TEACHERASSIST_PORT% -State Listen -ErrorAction SilentlyContinue; foreach ($x in $c) { $p = Get-Process -Id $x.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -match '^pythonw?$') { Write-Host '  Beende haengende Instanz PID' $x.OwningProcess; Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 800 } elseif ($p) { Write-Host ('  Port %TEACHERASSIST_PORT% ist von ' + $p.ProcessName + ' belegt. Bitte TEACHERASSIST_PORT auf einen freien Port setzen.') } }"

echo  Starte Tool-Server...
start "TeacherAssist Tool" /min "%PYTHON%" "%~dp0tool_server.py"

:: Auf /health warten - HTTP, nicht TCP. ChromaDB/Torch-Import dauert beim ersten Start.
:: Start-Sleep statt "timeout": timeout bricht ohne interaktive Konsole sofort
:: ab (z. B. in der CI), dann liefe die Schleife ohne zu warten durch.
echo  Warte auf Tool-Server...
set "TOOL_OK="
for /l %%I in (1,1,30) do (
    powershell -NoProfile -Command "Start-Sleep -Seconds 1; try { $r = Invoke-WebRequest -Uri 'http://localhost:%TEACHERASSIST_PORT%/api/v1/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "TOOL_OK=1"
        goto tool_ready
    )
)

:tool_ready
:: Bewusst ohne ( ... )-Block: Pfade wie %LOG_FILE% werden in Bloecken schon
:: beim Einlesen eingesetzt, und eine ")" im Benutzernamen beendete den Block.
if defined TOOL_OK goto open_browser
echo.
echo  PROBLEM: Tool-Server antwortet nicht auf http://localhost:%TEACHERASSIST_PORT%/api/v1/health
echo  Log pruefen: %LOG_FILE%
echo.
pause
exit /b 1

:open_browser
if defined NOBROWSER (
    echo  Tool-Server bereit ^(Browser nicht geoeffnet wegen NOBROWSER=%NOBROWSER%^).
) else (
    echo  Oeffne Browser...
    start "" "http://localhost:%TEACHERASSIST_PORT%/"
)

echo.
echo  TeacherAssist laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.
timeout /t 5 /nobreak >nul
exit /b 0
