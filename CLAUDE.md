# LehrerAgent – CLAUDE.md
> Vollständiger Bauplan für Claude Code. Wird bei jeder Session automatisch geladen.
> Letzte Aktualisierung: April 2026 (v3 – iOS WiFi-App + Web-UI ergänzt)

---

## Projektziel

KI-Assistent für deutsche Lehrkräfte. Self-hosted, DSGVO-konform, modell-agnostisch.
Nimmt Lehrern Routinearbeit ab: Unterrichtsplanung, Bewertungserstellung, Korrektur.

**Kernprinzip:** Der Agent schlägt vor – die Lehrkraft entscheidet.
**Lizenz:** MIT (OpenClaw). Kommerziell nutzbar. Copyright-Vermerk in Distributions pflegen.

---

## Die 3 Ebenen des Systems

```
┌─────────────────────────────────────────────────────────────┐
│  EBENE 1 – SKILLS  (Markdown, fertig ✅)                    │
│  Was der Agent tun soll. Reine Instruktionen für das LLM.   │
│  Kein ausführbarer Code. Trigger → Ablauf → Ausgabeformat.  │
├─────────────────────────────────────────────────────────────┤
│  EBENE 2 – TOOLS  (Python, fertig ✅)                       │
│  Was der Agent nicht selbst kann: PDFs lesen, Dateien       │
│  schreiben, OCR, Bildempfang. Werden von Skills aufgerufen. │
├─────────────────────────────────────────────────────────────┤
│  EBENE 3 – CLIENTS  (mehrere, verschiedene Reifegrade)      │
│  3a: Web-UI   – HTML/React, bereits fertig ✅               │
│  3b: iOS App  – Swift/SwiftUI, WLAN-only, fertig ✅         │
│  3c: Flutter  – Desktop + Mobile, in Entwicklung 🔨         │
└─────────────────────────────────────────────────────────────┘
```

**Wichtig:** Skills bleiben immer Markdown. Sie werden NICHT zu Python-Skripten.
Der LLM liest die skill.md und folgt den Anweisungen – wie ein aktivierter Prompt.
Python-Code schreiben wir nur für Tools (Ebene 2).

---

## Gesamtarchitektur

```
┌──────────────────────────────────────────────────────────┐
│                  DESKTOP (lokal / VPS)                    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  OpenClaw Runtime (:18789)                      │    │
│  │  Brain (LLM) ←→ Skills (Markdown) ←→ Tools     │    │
│  │  Memory (~/.openclaw/memory/*.md)               │    │
│  └─────────────────────────────────────────────────┘    │
│                          ↕                               │
│  ┌──────────────────────────────────────────────┐       │
│  │  Tool-Server (:8789)   Web-Server (:8788)    │       │
│  │  PDF-Upload/OCR/RAG    index.html + app.jsx  │       │
│  └──────────────────────────────────────────────┘       │
└──────────────────────────┬───────────────────────────────┘
                           │ WLAN / Tailscale VPN
              ┌────────────┴─────────────┐
              │                          │
      iOS App (Swift)          Flutter App
      WLAN WebSocket           Desktop + Mobile
      Kamera → OCR             Chat-Interface
```

---

## Tech-Stack

| Schicht | Technologie | Version | Warum |
|---------|-------------|---------|-------|
| Agent-Runtime | OpenClaw | MIT, aktuell | Self-hosted, model-agnostic, Skills-System |
| LLM | Claude Sonnet (claude-sonnet-4-6) | aktuell | Bestes Modell für Deutsch + Strukturaufgaben |
| Tools | Python | 3.11+ | PDF-Parsing, Dateisystem, OCR, Bildempfang |
| PDF-Parsing | pypdf | 4.x | Text-PDFs; zuverlässig, kein C-Build nötig |
| OCR | pytesseract + Pillow | aktuell | Gescannte PDFs und Schülerarbeitsfotos |
| Vektorspeicher | chromadb (lokal) | 0.5.x | Lehrplan-Einträge semantisch durchsuchbar |
| Embeddings | sentence-transformers | aktuell | Lokal, kein API-Call, DSGVO-sicher |
| Web-UI | React 18 (CDN) + HTML | — | Kein Build-Schritt, sofort nutzbar im Browser |
| Tool-Server | Python http.server | 3.11+ | PDF-Upload, OCR, RAG-Suche, Settings (:8789) |
| iOS App | Swift / SwiftUI | iOS 16+ | Natives Kamera-Interface, WLAN-WebSocket |
| Flutter App | Flutter | 3.x (Dart 3) | Eine Codebase → Android, iOS, Windows, macOS |
| VPN | Tailscale | aktuell | Kein Port-Forwarding, DSGVO-sicher, kostenlos/3 Nutzer |
| Memory | Markdown-Dateien (lokal) | — | Kein Drittanbieter, transparent, editierbar |
| VPS optional | Hetzner CX22 | ~5€/Monat | Multi-User / Schulserver |

---

## Vollständige Projektstruktur

```
lehreragent/
├── CLAUDE.md                              ← Diese Datei (Projektwurzel)
├── README.md                              ← Schnelleinstieg für Lehrer
├── SETUP.md                               ← Detaillierte Einrichtungsanleitung
│
├── index.html                             ← Web-UI Entry Point (Port 8788)
├── app.jsx                                ← React-App: Chat, Provider-Switch, Upload
├── components.jsx                         ← React-Komponenten: Settings, Onboarding, etc.
├── tweaks-panel.jsx                       ← Erweiterte Einstellungen (Panel)
├── tool_server.py                         ← Tool-Server (Port 8789): Upload, OCR, RAG, Settings
├── start.bat                              ← Startet Web-Server + Tool-Server + OpenClaw
├── install.bat                            ← Erstinstallation: Python-Env, Abhängigkeiten
├── openclaw_config_template.yaml          ← OpenClaw-Konfiguration (Provider, Fallback)
├── settings.json                          ← Persistierte Provider-Einstellungen (auto-generiert)
│
├── scripts/                               ← Windows-Hilfsscripte
│   ├── setup_config.ps1                   ← OpenClaw-Konfiguration einrichten
│   ├── setup_apikey.ps1                   ← API-Key in Umgebungsvariable speichern
│   └── create_shortcut.ps1               ← Desktop-Verknüpfung erstellen
│
├── skills/                                ← EBENE 1: OpenClaw Skills (Markdown)
│   ├── onboarding/
│   │   └── skill.md                      ← Ersteinrichtung, auto-trigger bei Erststart
│   ├── unterricht_planen/
│   │   └── skill.md                      ← Stundenentwürfe, liest lehrplan_index
│   ├── bewertung_erstellen/
│   │   └── skill.md                      ← Erwartungshorizont + Notenschlüssel
│   ├── arbeitsblatt_erstellen/
│   │   └── skill.md                      ← Druckfertige Aufgabenblätter mit Differenzierung ✅
│   ├── pruefung_erstellen/
│   │   └── skill.md                      ← Klassenarbeiten, Klausuren, Kurztest + Erwartungshorizont ✅
│   ├── elternbrief_schreiben/
│   │   └── skill.md                      ← Elternbriefe für alle Anlässe, druckfertig ✅
│   ├── zeugnis_formulieren/
│   │   └── skill.md                      ← Zeugnisformulierungen (3 Varianten je SuS) ✅
│   ├── foerderplan_erstellen/
│   │   └── skill.md                      ← Individuelle Förderpläne mit SMART-Zielen ✅
│   ├── klassenstatistik/
│   │   └── skill.md                      ← Notenauswertung, Notenspiegel, Aufgabenanalyse ✅
│   ├── schuelerarbeit_bewerten/
│   │   └── skill.md                      ← Korrektur gegen Bewertungsraster
│   └── lehrplan_einlesen/
│       └── skill.md                      ← Delegiert an tool: pdf_reader / ocr_reader
│
├── tools/                                 ← EBENE 2: Python-Tools (ausführbarer Code)
│   ├── __init__.py
│   ├── image_receiver.py                 ← Base64-Bilder vom iPhone empfangen + temp. speichern ✅
│   ├── pdf_reader.py                     ← Lehrplan-PDFs parsen (Text-PDFs) ✅
│   ├── ocr_reader.py                     ← Gescannte PDFs / Fotos → Text (pytesseract) ✅
│   ├── memory_writer.py                  ← Strukturiertes Schreiben in Memory-Dateien ✅
│   ├── memory_reader.py                  ← Memory-Dateien lesen + nach Schlüsseln suchen ✅
│   ├── lehrplan_indexer.py               ← Text → ChromaDB (Vektorsuche für Lehrpläne) ✅
│   ├── lehrplan_searcher.py              ← Semantische Suche in Lehrplan-Vektordatenbank ✅
│   ├── usage_tracker.py                  ← Token- & Kosten-Tracking für LLM-API ✅
│   ├── requirements.txt                  ← Alle Python-Abhängigkeiten
│   ├── setup.bat                         ← Windows: Python-Venv einrichten
│   └── setup.sh                          ← Linux/macOS: Python-Venv einrichten
│
├── memory/                                ← OpenClaw Memory-Dateien (Markdown-Templates)
│   ├── lehrerprofil.md                   ← Profil: Bundesland, Schulform, Fächer, Klassen
│   ├── lehrplan_index.md                 ← Menschenlesbare Lehrplaneinträge
│   ├── lehrplan_vectordb/                ← ChromaDB-Verzeichnis (auto-generiert)
│   ├── vergangene_stunden.md             ← Protokoll geplanter Stunden + Feedback
│   ├── korrekturprotokoll.md             ← Aggregiertes Korrekturprotokoll (anonym)
│   ├── onboarding_complete.md            ← Existenz = Onboarding wurde durchgeführt
│   └── bewertungsraster/
│       └── README.md                     ← Ablageort für {fach}_{klasse}_{thema}.md
│
├── uploads/                               ← Temporäre PDF-Uploads (via Tool-Server)
│
├── app_ios/                               ← EBENE 3b: iOS App (Swift/SwiftUI) ✅ fertig
│   └── LehrerAgent/
│       ├── LehrerAgentApp.swift           ← Entry Point, TabView-Router
│       ├── Info_additions.plist           ← Berechtigungen: Kamera, Galerie, LAN
│       ├── Services/
│       │   ├── ConnectionService.swift    ← WebSocket-Client (URLSessionWebSocketTask)
│       │   └── ImageService.swift        ← Kamera, Galerie, Skalierung, Perspektivkorrektur
│       ├── Models/
│       │   └── UploadViewModel.swift     ← Upload-State-Machine, EvaluationResult
│       └── Views/
│           ├── ConnectView.swift         ← IP eingeben, verbinden, UserDefaults
│           └── CaptureView.swift         ← Foto, Kontext (Fach/Klasse/Aufgabe), Ergebnis
│
├── app/                                   ← EBENE 3c: Flutter App (in Entwicklung 🔨)
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart                     ← Entry point, Router, Theme (Material 3)
│       ├── config/app_config.dart        ← Host, Port, VPN-Hostname aus ENV
│       ├── services/
│       │   ├── openclaw_service.dart     ← WebSocket-Client zu OpenClaw (:18789)
│       │   ├── connection_manager.dart   ← WLAN → Tailscale → Offline Fallback
│       │   ├── offline_queue.dart        ← Aufträge zwischenspeichern
│       │   ├── notification_service.dart ← FCM (Android) + APNs (iOS)
│       │   └── tailscale_service.dart    ← Tailscale VPN Management
│       ├── screens/
│       │   ├── chat_screen.dart          ← Haupt-Chat-Interface
│       │   ├── tasks_screen.dart         ← Laufende Agentenaufgaben + Status
│       │   ├── results_screen.dart       ← Fertige Ergebnisse, drucken/exportieren
│       │   ├── memory_screen.dart        ← Lehrerprofil + Memory-Übersicht
│       │   └── settings_screen.dart      ← Verbindung, Modell, Benachrichtigungen
│       └── widgets/
│           ├── message_bubble.dart
│           ├── file_upload_button.dart
│           ├── quick_actions.dart
│           └── connection_indicator.dart
│
└── docs/
    ├── architektur.md                    ← Diagramme, ADRs
    ├── deployment.md                     ← VPS-Setup, Schulserver, Reverse Proxy
    ├── datenschutz.md                    ← DSGVO-Checkliste, AVV-Vorlage
    └── tool_api.md                       ← Schnittstellendokumentation Tools ↔ Skills
```

---

## Tool-Spezifikationen (Ebene 2)

Jedes Tool ist ein Python-Skript mit einer klar definierten Signatur.
OpenClaw ruft Tools als Subprozess auf und bekommt JSON zurück.

### Aufrufkonvention

```python
# Alle Tools: stdin = JSON-Input, stdout = JSON-Output, stderr = Fehler
# OpenClaw ruft auf: python tools/pdf_reader.py '{"filepath": "..."}'
import sys, json
args = json.loads(sys.argv[1])
result = do_something(args)
print(json.dumps(result))
```

---

### `image_receiver.py` ✅

**Zweck:** Base64-kodierte Bilder vom iPhone empfangen, temporär speichern, Pfad zurückgeben.
Wird von `schuelerarbeit_bewerten` aufgerufen bevor `ocr_reader.py` läuft.

```python
# Input (action: "receive"):
{
  "action": "receive",
  "image_data": str,        # Base64-JPEG (mit oder ohne data:image-Prefix)
  "format": "jpeg",         # jpeg | png | webp | heic
  "session_id": str         # UUID aus der iOS-App (für Tracking)
}

# Output:
{
  "success": bool,
  "filepath": str,          # z. B. "/tmp/openclaw_images/openclaw_abc123_1714000000.jpeg"
  "session_id": str,
  "filesize_kb": int,
  "error": str | None
}

# Input (action: "cleanup"):
{ "action": "cleanup", "filepath": str }

# Input (action: "cleanup_old"):
{ "action": "cleanup_old", "max_age_minutes": 30 }
```

**DSGVO:** Bilder werden AUSSCHLIESSLICH in `/tmp/openclaw_images/` gespeichert.
Nach OCR/Auswertung sofort löschen via `cleanup`-Action.
Automatische Bereinigung via `cleanup_old` (Heartbeat-Skill alle 30 Min).

**Stolperstelle:** HEIC (iPhone-Standard) muss ggf. konvertiert werden.
iOS-App sendet immer JPEG (explizit in `ImageService.swift` konfiguriert).

---

### `pdf_reader.py` ✅

**Zweck:** Text-PDFs einlesen (Lehrpläne, die nicht gescannt sind)

```python
# Input:
{
  "filepath": str,          # absoluter Pfad zum PDF
  "pages": list[int] | None # optional: nur bestimmte Seiten (1-indexed)
}

# Output:
{
  "success": bool,
  "text": str,              # extrahierter Volltext
  "page_count": int,
  "error": str | None
}
```

**Library:** `pypdf` (4.x)
**Stolperstelle:** Viele Kultusministeriums-PDFs sind Scans → `text` ist dann leer.
In dem Fall: Fallback auf `ocr_reader.py` triggern (prüfen: `len(text.strip()) < 100`).

---

### `ocr_reader.py` ✅

**Zweck:** Gescannte PDFs und Fotos von Schülerarbeiten → maschinenlesbarer Text

```python
# Input:
{
  "filepath": str,          # PDF oder Bilddatei (jpg, png, webp)
  "language": str           # "deu" für Deutsch (Tesseract-Code)
}

# Output:
{
  "success": bool,
  "text": str,
  "confidence": float,      # 0–100, Tesseract-Konfidenzwert
  "error": str | None
}
```

**Libraries:** `pytesseract`, `Pillow`, `pdf2image`
**Systemabhängigkeit:** `tesseract-ocr` + `tesseract-ocr-deu` muss installiert sein.
**Stolperstelle:** Handschriftliche Schülerarbeiten haben niedrige Konfidenz (<60).
Bei confidence < 60: Warnung in Output, Lehrer darauf hinweisen.

---

### `memory_writer.py` ✅

**Zweck:** Memory-Markdown-Dateien strukturiert schreiben/aktualisieren

```python
# Input:
{
  "filepath": str,          # relativ zu ~/.openclaw/memory/
  "mode": "overwrite" | "append" | "update_section",
  "content": str,           # Markdown-Inhalt
  "section": str | None     # bei mode="update_section": Abschnittsname (##-Heading)
}

# Output:
{
  "success": bool,
  "filepath": str,          # absoluter Pfad der geschriebenen Datei
  "error": str | None
}
```

**Stolperstelle:** Encoding immer explizit `utf-8` setzen. Windows schreibt sonst cp1252.

---

### `memory_reader.py` ✅

**Zweck:** Memory-Dateien lesen, optional nach Schlüsseln filtern

```python
# Input:
{
  "filepath": str,          # relativ zu ~/.openclaw/memory/
  "section": str | None,    # nur diesen ##-Abschnitt zurückgeben
  "key": str | None         # nach "- **Key:** Value"-Einträgen suchen
}

# Output:
{
  "success": bool,
  "content": str,           # Markdown-Inhalt (gefiltert oder vollständig)
  "exists": bool,           # false wenn Datei noch nicht existiert
  "error": str | None
}
```

---

### `lehrplan_indexer.py` ✅

**Zweck:** Lehrplan-Text in ChromaDB als Vektoren speichern

```python
# Input:
{
  "text": str,              # Volltext des Lehrplans
  "metadata": {
    "bundesland": str,
    "schulform": str,
    "fach": str,
    "klasse": str,
    "quelle": str
  },
  "chunk_size": int         # Default: 500 (Zeichen pro Chunk)
}

# Output:
{
  "success": bool,
  "chunks_indexed": int,
  "collection": str,
  "error": str | None
}
```

**DB-Pfad:** `~/.openclaw/memory/lehrplan_vectordb/`
**Embedding-Modell:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(läuft vollständig lokal, kein API-Call, DSGVO-konform)

---

### `lehrplan_searcher.py` ✅

**Zweck:** Semantische Suche in indizierten Lehrplänen

```python
# Input:
{
  "query": str,             # z. B. "Bruchrechnung Klasse 7 Bayern"
  "n_results": int,         # Default: 3
  "filter": {               # optional: nur bestimmte Metadaten
    "bundesland": str | None,
    "fach": str | None,
    "klasse": str | None
  }
}

# Output:
{
  "success": bool,
  "results": [
    {
      "text": str,
      "metadata": dict,
      "distance": float     # 0 = perfekte Übereinstimmung
    }
  ],
  "error": str | None
}
```

---

### `usage_tracker.py` ✅

**Zweck:** Token- und Kosten-Tracking für LLM-API-Nutzung (Claude, OpenRouter, lokal)

```python
# Input für Tracking:
{
  "model": str,             # Modellname, z.B. "claude-sonnet-4-6"
  "input_tokens": int,
  "output_tokens": int,
  "skill_name": str | None,
  "request_id": str | None,
  "timestamp": str | None   # ISO-Format
}

# Output für Tracking:
{
  "success": bool,
  "tracking": {
    "model": str,
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "input_cost_usd": float,
    "output_cost_usd": float,
    "total_cost_usd": float,
    "skill": str | None,
    "timestamp": str,
    "day_key": str,         # "YYYY-MM-DD"
    "month_key": str        # "YYYY-MM"
  },
  "totals": {
    "total_tokens": int,
    "total_cost_usd": float,
    "total_requests": int
  },
  "warnings": list[str]     # Budget-Warnungen
}

# Input für Kostenschätzung:
{
  "model": str,
  "estimated_input_tokens": int,
  "estimated_output_tokens": int
}
```

**Funktionen:** Token-Tracking, Kostenberechnung, Budget-Warnungen (75%/90%), tägliche/monatliche Reports, JSON/CSV-Export, Kostenschätzung vor Requests.

**Claude API Preise (Stand: April 2026):**
- `claude-sonnet-4-6`: $3.00/M Input, $15.00/M Output
- `claude-opus-4-7`: $15.00/M Input, $75.00/M Output
- `claude-haiku-4-5`: $0.25/M Input, $1.25/M Output

**Daten-Speicherung:** `~/.openclaw/usage/usage_data.json`
**Standard-Budget:** $100/Monat

---

## Skill ↔ Tool Schnittstelle

Skills (Markdown) rufen Tools auf über OpenClaw's `tool_call`-Syntax im Prompt.
Der Brain erkennt diese Syntax und führt das Tool als Subprozess aus.

```
# In einer skill.md steht z. B.:
Rufe tool_call("pdf_reader", {"filepath": "{uploaded_file}"}) auf
und verwende den zurückgegebenen Text als Grundlage für die Extraktion.
```

**Welcher Skill ruft welche Tools auf:**

| Skill | Tools (in Reihenfolge) |
|-------|----------------------|
| `onboarding` | `memory_writer` (lehrerprofil.md schreiben) |
| `lehrplan_einlesen` | `pdf_reader` → bei leerem Text: `ocr_reader` → `lehrplan_indexer` → `memory_writer` |
| `unterricht_planen` | `memory_reader` (profil + index) → `lehrplan_searcher` |
| `bewertung_erstellen` | `memory_reader` (lehrplan_index) → `memory_writer` (bewertungsraster) |
| `arbeitsblatt_erstellen` | `memory_reader` (profil + lehrplan_index) → `lehrplan_searcher` → `memory_writer` (optional) |
| `pruefung_erstellen` | `memory_reader` (profil + lehrplan_index) → `lehrplan_searcher` → `memory_writer` (bewertungsraster) |
| `elternbrief_schreiben` | `memory_reader` (lehrerprofil) |
| `zeugnis_formulieren` | `memory_reader` (lehrerprofil) |
| `foerderplan_erstellen` | `memory_reader` (lehrerprofil) → `memory_writer` (foerderplaene) |
| `klassenstatistik` | `memory_reader` (lehrerprofil) |
| `schuelerarbeit_bewerten` | `image_receiver` (falls iPhone-Upload) → `ocr_reader` → `memory_reader` (bewertungsraster) → `memory_writer` (protokoll) |

---

## Skill-Datenfluss (vollständig)

```
Onboarding
  → memory_writer → lehrerprofil.md
  → memory_writer → onboarding_complete.md

lehrplan_einlesen
  → pdf_reader (oder ocr_reader falls Scan)
  → lehrplan_indexer → lehrplan_vectordb/
  → memory_writer → lehrplan_index.md (menschenlesbar)

unterricht_planen
  ← memory_reader ← lehrerprofil.md
  ← lehrplan_searcher ← lehrplan_vectordb/
  → [LLM generiert Stundenentwurf]
  → memory_writer → vergangene_stunden.md

bewertung_erstellen
  ← memory_reader ← lehrerprofil.md
  ← lehrplan_searcher ← lehrplan_vectordb/
  → [LLM generiert Erwartungshorizont]
  → memory_writer → bewertungsraster/{fach}_{klasse}_{thema}.md

schuelerarbeit_bewerten (Desktop/Web-UI)
  ← ocr_reader (wenn PDF/Scan übergeben)
  ← memory_reader ← bewertungsraster/{name}.md
  → [LLM bewertet Kriterium für Kriterium]
  → memory_writer → korrekturprotokoll.md

schuelerarbeit_bewerten (iPhone-Weg)
  ← image_receiver (Base64-JPEG vom iPhone)
  ← ocr_reader (Bild → Text)
  ← memory_reader ← bewertungsraster/{name}.md
  → [LLM bewertet]
  → memory_writer → korrekturprotokoll.md
  → image_receiver (cleanup – Bild löschen)
```

---

## OpenClaw Skill-Format (Referenz)

```
---
name: skill_name
triggers: ["phrase 1", "phrase 2"]
permissions: [read_memory, write_memory]
memory_files: [lehrerprofil.md, ...]
parameters:
  required: [param1]
  optional: [param2]
priority: 10          # höher = wird zuerst geprüft; onboarding hat 99
auto_trigger:         # optional: ohne Nutzereingabe auslösen
  condition: memory_file_missing
  file: onboarding_complete.md
---

# Skill: Name
## Ablauf
Schritt 1 – ...
## Ausgabeformat
...
## Verhaltensregeln
...
```

**Der Brain liest die skill.md als Prompt-Erweiterung.**
Skills sind keine ausführbaren Programme. Niemals Python-Code in skill.md schreiben.

---

## Web-UI – Architektur (Ebene 3a)

### Übersicht

```
Browser (Port 8788)          Tool-Server (Port 8789)
   index.html                   tool_server.py
   app.jsx          ←──────────► /upload        (PDF hochladen)
   components.jsx               /ingest         (PDF → ChromaDB)
   tweaks-panel.jsx             /search         (RAG-Suche)
                                /settings       (Provider speichern)
                                /health         (Status)
                                /clear          (DB leeren)
                                /save-raster    (Bewertungsraster speichern) ✅
                                /list-raster    (Raster auflisten) ✅

   app.jsx ──────── WebSocket/HTTP ──────► OpenClaw (:18789)
                    (callLLM via OpenRouter oder Ollama)
```

### Hauptfunktionen

- **Provider-Switch:** OpenRouter (cloud) ↔ Ollama (lokal), persistiert in `settings.json`
- **Auto-Fallback:** Wenn OpenRouter offline → automatisch Ollama; Banner + Label im Header
- **Streaming:** LLM-Antworten werden Wort für Wort gestreamt (SSE / fetch-Stream)
- **PDF-Upload:** Lehrplan hochladen → `/upload` → `/ingest` → ChromaDB indexiert
- **RAG-Suche:** Vor jedem LLM-Call Lehrplan-Kontext via `/search` injizieren
- **DSGVO-Hinweis:** Nur wenn Provider = OpenRouter und kein Ollama aktiv
- **Dark/Light Mode:** System-Präferenz + manueller Toggle
- **Export / Drucken:** Jede Bot-Antwort kann mit einem Klick als druckfertiges HTML geöffnet werden (Print-CSS, kein Tool-Server nötig) ✅
- **Bewertungsraster-Editor:** Eigene View-Seite in der Sidebar – Raster erstellen, Kriterien editieren, Notenschlüssel wählen, speichern, drucken ✅

### Dateien

| Datei | Zweck |
|-------|-------|
| `index.html` | HTML-Wrapper, CSS-Variablen, React CDN-Import |
| `app.jsx` | App-State, Chat-Loop, Provider-Logik, LLM-Calls |
| `components.jsx` | SettingsView, OnboardingView, ChatInput, MessageBubble |
| `tweaks-panel.jsx` | Erweiterte Einstellungen (Temperatur, System-Prompt, etc.) |
| `tool_server.py` | Python HTTP-Server Port 8789, CORS, alle Tool-Endpunkte |
| `start.bat` | Startet Web-Server (:8788) + Tool-Server (:8789) + OpenClaw |

---

## iOS App – Architektur & Protokoll (Ebene 3b)

### Verbindung (Phase 1: nur gleiches WLAN)

```
iPhone (iOS App)                    Mac (OpenClaw :18789)
      │                                      │
      │── WebSocket ws://192.168.x.x:18789 ──│
      │                                      │
      │── JSON: {type:"upload", ...} ────────→ image_receiver.py
      │                                      → ocr_reader.py
      │                                      → schuelerarbeit_bewerten
      │← JSON: {type:"progress", percent:30} │
      │← JSON: {type:"progress", percent:70} │
      │← JSON: {type:"result", note:"3"} ────│
```

**IP-Adresse:** Lehrer gibt die lokale Mac-IP einmalig in der App ein.
Wird in `UserDefaults` gespeichert (`openclaw_host`).
**Port:** 18789 (OpenClaw Gateway Standard).

### iOS Nachrichtenprotokoll (JSON over WebSocket)

```json
// iPhone → Mac: Bild senden
{
  "type": "upload",
  "id": "uuid-1234",
  "skill": "schuelerarbeit_bewerten",
  "image": { "data": "<base64-JPEG>", "format": "jpeg", "width_px": 1600, "height_px": 2263 },
  "context": { "fach": "Mathematik", "klasse": "7a", "aufgabe": "Bruchrechnung Test 3" }
}

// Mac → iPhone: Fortschritt
{ "type": "progress", "id": "uuid-1234", "step": "OCR läuft...", "percent": 30 }

// Mac → iPhone: Ergebnis
{ "type": "result", "id": "uuid-1234", "punkte": "34/50", "note": "3", "feedback": "..." }

// Mac → iPhone: Fehler
{ "type": "error", "id": "uuid-1234", "message": "OCR fehlgeschlagen: ..." }
```

### iOS Bildoptimierung (vor dem Senden)

```
Original (iPhone): 12 MP, ~4–8 MB HEIC
       ↓
1. UIImagePickerController liefert UIImage
2. ImageService.perspectiveCorrect(): CIDetectorTypeRectangle
3. ImageService.scale(): auf max. 1600px Breite/Höhe
4. UIImage.jpegData(compressionQuality: 0.85): ~200–400 KB
5. Data.base64EncodedString() → in UploadMessage.image.data
```

### iOS State-Machine (UploadState enum)

```
idle → optimizing → uploading(progress) → processing(step, percent) → done(result)
                                                                     ↘ failed(message)
```

### iOS Berechtigungen (Info.plist)

| Key | Grund |
|-----|-------|
| `NSCameraUsageDescription` | Schülerarbeiten fotografieren |
| `NSPhotoLibraryUsageDescription` | Fotos aus Galerie laden |
| `NSLocalNetworkUsageDescription` | WebSocket zum Mac im WLAN |
| `NSAppTransportSecurity.NSAllowsLocalNetworking` | HTTP/WS (kein HTTPS) im LAN |

### iOS Xcode-Einrichtung

```
1. Neues Xcode-Projekt: File → New → Project → iOS App
   - Product Name: LehrerAgent | Interface: SwiftUI | Min iOS: 16.0

2. Swift-Dateien aus app_ios/LehrerAgent/ in Xcode-Projektordner ziehen

3. Info.plist: Einträge aus Info_additions.plist einfügen
   (Target → Info → Custom iOS Target Properties)

4. Signing: Team auswählen (kostenloses Apple-Konto reicht für Sideload, 7 Tage)

5. iPhone per USB → Trust bestätigen → Run ▶
```

---

## Flutter App – Design-Prinzipien (Ebene 3c)

- **Kein eigenes Backend** – App ist reines Interface zu OpenClaw
- **Adaptive UI:** Mobile = Chat-first; Desktop = Chat + Sidebar (Memory-Übersicht)
- **Offline-Modus:** zeigt letzte Ergebnisse aus lokalem Cache
- **Kein Schülerdaten-Upload** über die App – nur über Desktop-Client (DSGVO)
- Flutter: **Material 3**, adaptive Layouts, keine fixen Pixel-Breakpoints
- Dart: **null-safety** durchgehend, keine deprecated APIs

### Verbindungslogik (Priorität)

```
1. Selbes WLAN → direkte lokale IP (aus app_config)
2. Tailscale → VPN-Hostname (aus app_config)
3. Kein Zugriff → Offline-Modus → Auftrag in offline_queue speichern
```

```dart
// Immer dart:io WebSocket verwenden (nicht dart:html – funktioniert nur im Browser)
// Reconnect mit exponential backoff: 1s → 2s → 4s → 8s → max 30s
// Heartbeat-Ping alle 30s
```

---

## Wichtige Regeln

### Datenschutz (DSGVO – nicht verhandelbar)
- Schülernamen werden NICHT in Memory gespeichert (Standard: anonym)
- Keine personenbezogenen Daten in LLM-API-Calls bei Cloud-Provider
- OCR-Ergebnisse von Schülerarbeiten: nur temporär im RAM, nicht persistent auf Disk
- iPhone-Fotos: sofort nach OCR via `image_receiver.cleanup` löschen
- Anonymisierung: SuS-01, SuS-02 statt Namen
- Alle Memory-Dateien bleiben lokal auf dem Gerät der Lehrkraft

### Sprache & Ton
- Alle Skills und Tool-Ausgaben auf Deutsch
- Ton: professionell-kollegial ("wie ein erfahrener Kollege")
- Niemals abwertend über Schülerleistungen formulieren
- Bewertungen immer als "Vorschlag" kennzeichnen

### Pädagogische Korrektheit
- Lehrplanbezüge ohne Quelle mit `[*]` markieren
- AFB-Verteilung: ~30% AFB I (Reproduktion) / ~40% AFB II (Reorganisation) / ~30% AFB III (Transfer)
- Zeitangaben: Einstieg max. 10 min, Sicherung min. 5 min

### Code-Qualität
- Kein Hardcoding von Ports, IPs oder API-Keys → aus Config/ENV
- Tools: immer Try/Except mit sauberem JSON-Error-Output
- Flutter: keine `print()`-Statements in Production, nur `debugPrint()`
- Swift: keine `print()` in Production, nur `os_log` oder `Logger`
- Alle Dateipfade über `os.path.expanduser()` auflösen

---

## Entwicklungsphasen & Arbeitsplan für Claude Code

### ✅ Phase 0 – Skills & Memory (abgeschlossen)
- [x] `skills/onboarding/skill.md`
- [x] `skills/unterricht_planen/skill.md`
- [x] `skills/bewertung_erstellen/skill.md`
- [x] `skills/arbeitsblatt_erstellen/skill.md` ← Druckfertige Aufgabenblätter
- [x] `skills/pruefung_erstellen/skill.md` ← Klassenarbeiten, Klausuren, Kurztests
- [x] `skills/elternbrief_schreiben/skill.md` ← Elternbriefe für alle Anlässe
- [x] `skills/zeugnis_formulieren/skill.md` ← Zeugnisformulierungen (3 Varianten)
- [x] `skills/foerderplan_erstellen/skill.md` ← Individuelle Förderpläne
- [x] `skills/klassenstatistik/skill.md` ← Notenauswertung + Notenspiegel
- [x] `skills/schuelerarbeit_bewerten/skill.md`
- [x] `skills/lehrplan_einlesen/skill.md`
- [x] Memory-Templates (alle .md-Dateien)

### ✅ Phase 1 – Python Tools + Tool-Server (abgeschlossen)
- [x] `tools/requirements.txt`
- [x] `tools/memory_reader.py`
- [x] `tools/memory_writer.py`
- [x] `tools/pdf_reader.py`
- [x] `tools/ocr_reader.py`
- [x] `tools/lehrplan_indexer.py`
- [x] `tools/lehrplan_searcher.py`
- [x] `tools/usage_tracker.py`
- [x] `tools/image_receiver.py` ← Base64-Bildempfang + DSGVO-Cleanup
- [x] `tool_server.py` ← HTTP-Server Port 8789 (Upload, OCR, RAG, Settings)

### ✅ Phase 2a – Web-UI (abgeschlossen)
- [x] `index.html` – HTML-Wrapper + CSS Design-System
- [x] `app.jsx` – Chat, Provider-Switch (OpenRouter/Ollama), Streaming, RAG
- [x] `components.jsx` – Settings, Onboarding, Fallback-Banner
- [x] `tweaks-panel.jsx` – Erweiterte Einstellungen
- [x] `start.bat` – Startet alle Server + OpenClaw
- [x] `openclaw_config_template.yaml` – Provider-Env-Vars, Fallback-Config
- [x] Export-Button: Jede Antwort per Klick als druckfertiges HTML exportieren
- [x] Bewertungsraster-Editor: eigene View, Kriterien-Editor, 3 Notenschlüssel, Speichern + Drucken

### ✅ Phase 2b – iOS App, WLAN-only (abgeschlossen)
- [x] `app_ios/.../ConnectionService.swift` – WebSocket, Ping, Reconnect (exponential backoff)
- [x] `app_ios/.../ImageService.swift` – Kamera, Galerie, Skalierung, Perspektivkorrektur
- [x] `app_ios/.../UploadViewModel.swift` – State-Machine, Server-Nachrichten
- [x] `app_ios/.../ConnectView.swift` – IP-Eingabe, UserDefaults
- [x] `app_ios/.../CaptureView.swift` – Foto, Kontextform, Fortschritt, Ergebnis
- [x] `app_ios/.../LehrerAgentApp.swift` – Entry Point, TabView
- [x] `app_ios/.../Info_additions.plist` – Kamera/Galerie/LAN-Berechtigungen
- [ ] In Xcode einrichten + auf echtem Gerät testen
- [ ] End-to-End-Test: iPhone → WLAN → Mac → OCR → Note → iPhone

### 🔨 Phase 3 – Flutter Desktop App (in Entwicklung)
- [x] Grundgerüst + Dart-Dateien vorhanden
- [ ] Widgets implementieren: `message_bubble.dart`, `connection_indicator.dart`
- [ ] `memory_screen.dart` – Lehrerprofil + Memory-Übersicht (Desktop-Sidebar)
- [ ] End-to-End-Test: App → OpenClaw → Skill → Tool → Antwort

### 📡 Phase 4 – Remote-Zugriff (Tailscale)
- [ ] Tailscale auf Mac + iPhone einrichten
- [ ] iOS `ConnectionService` erweitern: WLAN-IP → Tailscale-Hostname → Offline-Queue
- [ ] Flutter `connection_manager.dart` mit Tailscale-Fallback
- [ ] CLAUDE.md: iOS-Abschnitt um Tailscale-Variante ergänzen

### 🔔 Phase 5 – Push & Hintergrund
- [ ] OpenClaw als Tray-App (Desktop Heartbeat-Config)
- [ ] Heartbeat-Skill: `cleanup_old` für Temp-Bilder alle 30 Min
- [ ] iOS: `UNUserNotificationCenter` – Benachrichtigung bei fertigem Task
- [ ] Flutter: `notification_service.dart` (FCM + APNs)

---

## Installation & Setup

```bash
# 1. OpenClaw installieren (Node 22 LTS oder Node 24)
npm install -g openclaw

# 2. Skills + Memory deployen
cp -r skills/* ~/.openclaw/skills/
cp -r memory/* ~/.openclaw/memory/
openclaw skill load onboarding unterricht_planen bewertung_erstellen \
  schuelerarbeit_bewerten lehrplan_einlesen

# 3. Python-Umgebung für Tools
cd tools/
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Tesseract installieren (für OCR)
# macOS:   brew install tesseract tesseract-lang
# Ubuntu:  sudo apt install tesseract-ocr tesseract-ocr-deu
# Windows: Installer von github.com/UB-Mannheim/tesseract

# 5. Tools in OpenClaw registrieren (~/.openclaw/config.yaml)
# tools_path: /absoluter/pfad/zu/lehreragent/tools
# tools_python: /absoluter/pfad/zu/lehreragent/tools/.venv/bin/python

# 6. Agent starten – WICHTIG: --host 0.0.0.0 damit iPhone erreichbar ist
openclaw start --host 0.0.0.0 --port 18789
# Mac-IP herausfinden:
ipconfig getifaddr en0   # macOS
# Diese IP in der iOS-App eingeben

# 7. Web-UI starten (Windows: start.bat doppelklicken)
python -m http.server 8788          # Web-UI
python tool_server.py               # Tool-Server
# → Browser öffnet http://localhost:8788
```

```
iOS App in Xcode einrichten:
1. Xcode → File → New → Project → iOS App
   Name: LehrerAgent | SwiftUI | Swift | Min iOS: 16.0
2. Alle Dateien aus app_ios/LehrerAgent/ ins Xcode-Projekt ziehen
   (Services/, Models/, Views/ als Gruppen beibehalten)
3. Info.plist: Einträge aus Info_additions.plist einfügen
4. iPhone per USB verbinden → Trust bestätigen
5. Signing: kostenloses Apple-Konto reicht für Sideload (7 Tage)
6. Run ▶ → App auf iPhone installieren
7. App öffnen → Mac-IP eingeben → Verbinden
```

---

## Bekannte Stolperstellen

**OpenClaw**
- Gateway startet nicht → Port 18789 belegt? `lsof -i :18789` / `netstat -ano | findstr 18789`
- Skills triggern nicht → Trigger-Phrase zu ungenau? `/skills list` zum Debuggen
- iPhone kann nicht verbinden → `openclaw start` ohne `--host 0.0.0.0` lauscht nur auf localhost

**Python Tools**
- `pypdf` gibt leeren Text zurück → PDF ist ein Scan → Fallback auf `ocr_reader.py`
- `pytesseract` findet Tesseract nicht → `pytesseract.pytesseract.tesseract_cmd` explizit setzen
- ChromaDB-Pfad: immer `os.path.expanduser("~/.openclaw/memory/lehrplan_vectordb")` verwenden
- Memory-Dateien: `open(path, encoding="utf-8")` – niemals ohne encoding-Parameter

**iOS App**
- `NSLocalNetworkUsageDescription` fehlt → App verbindet sich nie, kein Fehler sichtbar (iOS blockiert still)
- Simulator hat keine Kamera → GalleryPicker testen, auf echtem Gerät deployen
- iOS 16 Minimum: `URLSessionWebSocketTask` + `PHPickerViewController` benötigen iOS 13+, SwiftUI-Features 16+
- `UploadViewModel` doppelt initialisiert → `@StateObject` in `RootView` anlegen, per `.environmentObject()` weitergeben
- Reconnect: `ConnectionService` versucht 5× mit exponential backoff (1s → 2s → 4s → 8s → 16s)

**Web-UI**
- Tool-Server nicht gestartet → Upload/RAG/Settings funktionieren nicht (Port 8789)
- CORS-Fehler → Tool-Server läuft auf anderem Port oder nicht gestartet
- Ollama nicht gefunden → `ollama serve` muss laufen, dann /health prüfen
- OpenRouter-Fallback zeigt Warnung → Provider-Status wird alle 30s geprüft

**Flutter**
- WebSocket auf Desktop: `dart:io` importieren, nicht `dart:html`
- Datei-Upload auf Desktop: `file_picker` Package, nicht `image_picker`
- Tailscale-Hostname auf Android: keine `.local`-Domains → immer IP oder Tailscale-DNS

---

## `tools/requirements.txt`

```
pypdf==4.3.1
pytesseract==0.3.13
Pillow==10.4.0
pdf2image==1.17.0
chromadb==0.5.23
sentence-transformers==3.2.1
python-frontmatter==1.1.0
```

---

## Weiterführende Docs & Links

- `docs/architektur.md` – Detaildiagramme, Architektur-Entscheidungen (ADRs)
- `docs/deployment.md` – VPS-Setup Hetzner, Schulserver, Reverse Proxy
- `docs/datenschutz.md` – DSGVO-Checkliste, AVV-Vorlage für Schulen
- `docs/tool_api.md` – Vollständige Tool-Schnittstellendokumentation
- OpenClaw Docs: https://docs.openclaw.ai
- Flutter Docs: https://docs.flutter.dev
- ChromaDB Docs: https://docs.trychroma.com
- Sentence Transformers: https://www.sbert.net
- Anthropic API: https://docs.anthropic.com/en/api/overview
- Tailscale: https://tailscale.com/kb

---

## Roadmap – Nächste Skills

| Skill | Tools die er braucht | Priorität |
|-------|---------------------|-----------|
| `arbeitsblatt_erstellen` | memory_reader, memory_writer, lehrplan_searcher | ✅ fertig |
| `pruefung_erstellen` | memory_reader, memory_writer, lehrplan_searcher | ✅ fertig |
| `elternbrief_schreiben` | memory_reader, memory_writer | ✅ fertig |
| `zeugnis_formulieren` | memory_reader, memory_writer | ✅ fertig |
| `klassenstatistik` | memory_reader | ✅ fertig |
| `foerderplan_erstellen` | memory_reader, memory_writer | ✅ fertig |
