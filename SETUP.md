# LehrerAgent – Setup-Anleitung

Vollständige Einrichtung auf einem neuen Rechner. Reihenfolge einhalten.

---

## Voraussetzungen

| Software | Version | Download |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Tesseract OCR | 5.x | https://github.com/UB-Mannheim/tesseract/wiki (Windows) |
| Poppler | aktuell | https://github.com/oschwartz10612/poppler-windows/releases (Windows) |
| Flutter SDK | 3.x | https://docs.flutter.dev/get-started/install |
| OpenClaw | aktuell | (intern) |
| Git | aktuell | https://git-scm.com/ |

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

## Schritt 3 – OpenClaw konfigurieren

```bash
# Konfigurationsverzeichnis anlegen
mkdir -p ~/.openclaw/memory
mkdir -p ~/.openclaw/skills
mkdir -p ~/.openclaw/logs

# Config-Template kopieren und anpassen
cp openclaw_config_template.yaml ~/.openclaw/config.yaml
```

Dann `~/.openclaw/config.yaml` öffnen und diese Felder anpassen:

```yaml
brain:
  api_key: "${ANTHROPIC_API_KEY}"   # oder direkt eintragen

tools:
  path: "/absoluter/pfad/zu/TeacherAssist/tools"
  python: "/absoluter/pfad/zu/TeacherAssist/tools/.venv/bin/python"
  # Windows:
  # python: "C:\\Pfad\\zu\\TeacherAssist\\tools\\.venv\\Scripts\\python.exe"
```

### Skills und Memory verknüpfen

```bash
# Skills ins OpenClaw-Verzeichnis kopieren (oder symlink)
cp -r skills/. ~/.openclaw/skills/

# Memory-Templates kopieren (werden vom Agenten befüllt)
cp memory/lehrerprofil.md ~/.openclaw/memory/
cp memory/lehrplan_index.md ~/.openclaw/memory/
cp memory/korrekturprotokoll.md ~/.openclaw/memory/
cp memory/vergangene_stunden.md ~/.openclaw/memory/
mkdir -p ~/.openclaw/memory/bewertungsraster
```

### API-Key setzen

```bash
# Windows (PowerShell, dauerhaft):
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")

# Linux/macOS (~/.bashrc oder ~/.zshrc):
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Schritt 4 – Flutter App einrichten

> Nur nötig wenn du die App lokal bauen willst. Für reine OpenClaw-Nutzung (Browser/Terminal) diesen Schritt überspringen.

```bash
cd app

# Platform-Dateien generieren (einmalig):
flutter create --project-name teacher_assist .

# Abhängigkeiten auflösen:
flutter pub get

# Auf Fehler prüfen:
flutter analyze

# Desktop-App starten (Windows):
flutter run -d windows

# Desktop-App starten (macOS):
flutter run -d macos

# Android (Gerät angeschlossen):
flutter run -d android
```

---

## Schritt 5 – OpenClaw starten

```bash
openclaw start --config ~/.openclaw/config.yaml
```

OpenClaw läuft dann auf Port **18789** (WebSocket + HTTP).

---

## Schritt 6 – Verbindung testen

```bash
# Einfacher Test ob OpenClaw erreichbar ist:
curl http://localhost:18789/health

# Tool direkt testen:
cd tools
.venv/Scripts/python memory_reader.py  # Windows
.venv/bin/python memory_reader.py      # Linux/macOS
```

---

## Schritt 7 – Onboarding (beim ersten Start)

In der App oder über OpenClaw den Onboarding-Skill starten:
> "Ich möchte den Agenten einrichten"

Der Agent führt durch die Einrichtung des Lehrerprofils.

---

## Verzeichnisstruktur nach Setup

```
TeacherAssist/
├── app/                    # Flutter UI
│   ├── android/            # (generiert durch flutter create)
│   ├── windows/            # (generiert durch flutter create)
│   ├── lib/                # Dart-Quellcode
│   └── pubspec.yaml
├── skills/                 # Markdown-Skills für OpenClaw
├── tools/                  # Python-Tools
│   ├── .venv/              # (gitignored – wird durch setup.bat/sh erstellt)
│   ├── requirements.txt
│   └── *.py
├── memory/                 # Memory-Templates (leer, werden vom Agent befüllt)
├── openclaw_config_template.yaml
├── SETUP.md                # Diese Datei
└── CLAUDE.md               # Bauplan für Claude Code

~/.openclaw/               # Laufzeit-Daten (NICHT im Repo)
├── config.yaml            # Deine persönliche Konfiguration
├── memory/                # Vom Agenten befüllte Memory-Dateien
├── skills/                # Kopie der Skills aus dem Repo
└── logs/
```

---

## Häufige Fehler

| Fehler | Lösung |
|---|---|
| `tesseract is not installed` | Tesseract installieren + PATH setzen |
| `Unable to get page count. Is poppler installed` | Poppler installieren + PATH setzen |
| `chromadb` ImportError | `pip install chromadb` in `.venv` |
| Flutter: `No supported devices found` | Zielplattform installieren (Android Studio / VS Build Tools) |
| OpenClaw: `Connection refused` | OpenClaw starten + Port 18789 prüfen |
| `ANTHROPIC_API_KEY not set` | Umgebungsvariable setzen (siehe Schritt 3) |
