@echo off
:: LehrerAgent – Python Tool-Umgebung einrichten (Windows)
:: Führe dieses Skript einmalig aus, bevor du OpenClaw startest.

echo.
echo  LehrerAgent Tool-Setup (Windows)
echo  ===================================

:: Prüfen ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden. Bitte Python 3.11+ installieren.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [1/4] Erstelle virtuelle Umgebung...
python -m venv .venv
if errorlevel 1 (
    echo FEHLER: Konnte virtuelle Umgebung nicht erstellen.
    pause
    exit /b 1
)

echo [2/4] Aktualisiere pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet

echo [3/4] Installiere Abhängigkeiten aus requirements.txt...
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Pip install fehlgeschlagen. Prüfe requirements.txt und Internetverbindung.
    pause
    exit /b 1
)

echo [4/4] Prüfe Installation...
.venv\Scripts\python.exe -c "import pypdf, pytesseract, PIL, chromadb, sentence_transformers; print('  Alle Pakete OK')"
if errorlevel 1 (
    echo WARNUNG: Nicht alle Pakete konnten importiert werden.
    echo          Tesseract und Poppler müssen separat installiert werden (siehe SETUP.md).
) else (
    echo.
    echo  Setup erfolgreich!
)

echo.
echo WICHTIG: Trage den Python-Pfad in deine OpenClaw-Konfiguration ein:
echo   python: "%CD%\.venv\Scripts\python.exe"
echo.
pause
