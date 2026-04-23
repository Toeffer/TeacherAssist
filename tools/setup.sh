#!/bin/bash
# LehrerAgent – Python Tool-Umgebung einrichten (Linux/macOS)
# Führe dieses Skript einmalig aus, bevor du OpenClaw startest.

set -e

echo ""
echo " LehrerAgent Tool-Setup (Linux/macOS)"
echo " ======================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python-Version prüfen
if ! command -v python3 &>/dev/null; then
    echo "FEHLER: python3 nicht gefunden. Bitte Python 3.11+ installieren."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION gefunden"

echo ""
echo "[1/4] Erstelle virtuelle Umgebung..."
python3 -m venv .venv

echo "[2/4] Aktualisiere pip..."
.venv/bin/pip install --upgrade pip --quiet

echo "[3/4] Installiere Abhängigkeiten aus requirements.txt..."
.venv/bin/pip install -r requirements.txt

echo "[4/4] Prüfe Installation..."
if .venv/bin/python -c "import pypdf, pytesseract, PIL, chromadb, sentence_transformers; print('  Alle Pakete OK')" 2>/dev/null; then
    echo ""
    echo " Setup erfolgreich!"
else
    echo "WARNUNG: Nicht alle Pakete konnten importiert werden."
    echo "         Tesseract und Poppler müssen separat installiert werden (siehe SETUP.md)."
fi

echo ""
echo "WICHTIG: Trage den Python-Pfad in deine OpenClaw-Konfiguration ein:"
echo "  python: \"$SCRIPT_DIR/.venv/bin/python\""
echo ""
