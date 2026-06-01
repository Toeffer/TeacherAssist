@echo off
chcp 65001 >nul 2>&1
title TeacherAssist
cd /d "%~dp0"

echo.
echo  Starte TeacherAssist...
echo.

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
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8789/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo  Tool-Server laeuft bereits.
    goto open_browser
)

:: /health antwortet nicht. Falls jemand auf Port 8789 lauscht: haengender Prozess, beenden.
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8789 -State Listen -ErrorAction SilentlyContinue; if ($c) { foreach ($x in $c) { Write-Host '  Beende haengende Instanz PID' $x.OwningProcess; Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue }; Start-Sleep -Milliseconds 800 }"

echo  Starte Tool-Server...
start "TeacherAssist Tool" /min "%PYTHON%" "%~dp0tool_server.py"

:: Auf /health warten - HTTP, nicht TCP. ChromaDB/Torch-Import dauert beim ersten Start.
echo  Warte auf Tool-Server...
set "TOOL_OK="
for /l %%I in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8789/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
        set "TOOL_OK=1"
        goto tool_ready
    )
)

:tool_ready
if not defined TOOL_OK (
    echo.
    echo  PROBLEM: Tool-Server antwortet nicht auf http://localhost:8789/health
    echo  Log pruefen: %~dp0logs\tool_server.log
    echo.
    pause
    exit /b 1
)

:open_browser
if defined NOBROWSER (
    echo  Tool-Server bereit ^(Browser nicht geoeffnet wegen NOBROWSER=%NOBROWSER%^).
) else (
    echo  Oeffne Browser...
    start "" "http://localhost:8789/"
)

echo.
echo  TeacherAssist laeuft!
echo  (Dieses Fenster kann minimiert werden)
echo.
timeout /t 5 /nobreak >nul
exit /b 0
