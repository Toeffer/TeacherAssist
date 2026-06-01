# LehrerAgent – Technische Setup-Anleitung

> **Für Endnutzer:** Bitte [README.md](README.md) verwenden — dort reicht ein Doppelklick auf `install.bat`.
> Diese Datei richtet sich an Entwickler und technisch versierte Nutzer.

Vollständige manuelle Einrichtung auf einem neuen Rechner. Reihenfolge einhalten.

---

## Voraussetzungen

| Software | Version | Download |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Tesseract OCR | 5.x | https://github.com/UB-Mannheim/tesseract/wiki (Windows) |
| Poppler | aktuell | https://github.com/oschwartz10612/poppler-windows/releases (Windows) |
| Ollama (optional, Pflicht für DSGVO-Skills) | aktuell | https://ollama.com/download |
| Git | aktuell | https://git-scm.com/ |

> **Legacy:** Flutter und OpenClaw werden in v4 nicht mehr benötigt. iOS-/Flutter-Clients sind dokumentiert, aber nicht angebunden — siehe CLAUDE.md.

---

## Schritt 1 – Repository klonen

```bash
git clone https://github.com/Toeffer/TeacherAssist.git
cd TeacherAssist
```

---

## Schritt 2 – Python-Umgebung für Tools einrichten

```bash
cd tools

# Windows:
setup.bat

# Linux/macOS:
bash setup.sh
```

Das Skript erstellt `.venv/` im `tools/`-Ordner und installiert alle Abhängigkeiten.

### Tesseract (Windows)
1. Installer von https://github.com/UB-Mannheim/tesseract/wiki herunterladen
2. Bei der Installation: **Zusatzpaket "German"** anwählen
3. Installationspfad notieren (z. B. `C:\Program Files\Tesseract-OCR\`)
4. Pfad zur PATH-Umgebungsvariable hinzufügen **oder** in `tools/ocr_reader.py` eintragen:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Poppler (Windows)
1. Release von https://github.com/oschwartz10612/poppler-windows/releases herunterladen
2. Entpacken, z. B. nach `C:\poppler\`
3. `C:\poppler\Library\bin` zur PATH-Umgebungsvariable hinzufügen

---

## Schritt 3 – Tool-Server starten und konfigurieren

In v4 gibt es keinen separaten OpenClaw-Dienst mehr. `tool_server.py` läuft als einziger
Prozess auf Port **8789** und liefert Frontend und API aus.

```bat
:: Aus dem Projektordner:
start.bat
```

`start.bat` prüft das venv unter `tools\.venv`, probiert `GET /health` und beendet einen
hängenden Vor-Prozess auf Port 8789 falls vorhanden. Browser öffnet sich automatisch.

API-Key und Provider werden in der Web-UI unter *Einstellungen → Provider* eingetragen
und in `settings.json` (im Projektroot) gespeichert. Keine Umgebungsvariable nötig.

**Ollama (optional, Pflicht für DSGVO-Skills):**

```bat
:: nach Installation von https://ollama.com/download
ollama pull gemma3:e4b
ollama serve   :: läuft normalerweise automatisch als Hintergrunddienst
```

DSGVO-Pflicht-Skills (`schuelerarbeit_bewerten`, `zeugnis_formulieren`,
`foerderplan_erstellen`, `lerntagebuch_feedback`, `klassenstatistik`) werden
serverseitig zwingend auf Ollama geroutet. Wenn Ollama offline ist und ein solcher
Skill verlangt wird, gibt die UI eine Fehlermeldung aus — **kein Cloud-Fallback**.

---

## Schritt 4 – Verbindung testen

```bat
:: Server-Status
curl http://localhost:8789/health
:: Erwartet: {"status":"ok","version":"1.1","ollama":true}

:: Tool direkt aus venv testen:
tools\.venv\Scripts\python.exe tools\memory_reader.py
```

Server-Log liegt unter `logs\tool_server.log` (rotierend, 1 MB × 3).

---

## Schritt 5 – Onboarding (beim ersten Start)

In der Web-UI den Onboarding-Skill starten:
> "Ich möchte den Agenten einrichten"

Der Agent führt durch die Einrichtung des Lehrerprofils. Profil wird unter
`memory\lehrerprofil.md` gespeichert.

---

## Verzeichnisstruktur nach Setup

```
TeacherAssist/
├── tool_server.py          # Einziger Server (Port 8789)
├── start.bat               # Startet tool_server.py (HTTP /health-Probe)
├── install.bat             # Erstinstallation Python + Tesseract + venv
├── settings.json           # Provider-/Modell-/API-Key-Settings (auto)
├── index.html, app.jsx, components.jsx, tweaks-panel.jsx
├── skills/                 # Markdown-Skills (LLM-Instruktionen)
├── tools/
│   ├── .venv/              # Python-venv (gitignored, von install.bat angelegt)
│   ├── chroma_db/          # ChromaDB-Vektorspeicher (gitignored)
│   ├── requirements.txt
│   └── *.py                # Python-Tools (pdf_reader, ocr_reader, memory_*, …)
├── memory/                 # Markdown-Memory (lehrerprofil, lehrplan_index, …)
├── logs/tool_server.log    # Rotierendes Server-Log (auto)
├── uploads/                # Temp PDF-Uploads
├── SETUP.md                # Diese Datei
└── CLAUDE.md               # Bauplan für Claude Code
```

> Es gibt **kein** `~/.openclaw/`-Verzeichnis mehr. Alle Pfade sind projektrelativ.

---

## Häufige Fehler

| Fehler | Lösung |
|---|---|
| `Python-venv nicht gefunden` (beim Start) | `install.bat` ausführen — legt `tools\.venv` an |
| Browser zeigt „Tool-Server offline" | `logs\tool_server.log` prüfen, `start.bat` neu starten |
| Port 8789 belegt, `/health` timeoutet | Stale Prozess — `start.bat` ab v4 räumt selbst auf |
| `tesseract is not installed` | Tesseract installieren + PATH setzen |
| `Unable to get page count. Is poppler installed` | Poppler installieren + PATH setzen |
| `chromadb` ImportError | `tools\.venv\Scripts\pip install -r tools\requirements.txt` |
| DSGVO-Skill schlägt mit „Ollama nicht verfügbar" fehl | Ollama installieren + `ollama serve` läuft? |
