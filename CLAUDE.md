# LehrerAgent – CLAUDE.md
> Vollständiger Bauplan für Claude Code. Wird bei jeder Session automatisch geladen.
> Letzte Aktualisierung: 2026-05-28 (v4 – Architektur korrigiert: ein Prozess auf :8789, Venv-Pflicht, Server-Log, Operate-Sektion)

---

## Projektziel

KI-Assistent für deutsche Lehrkräfte. Self-hosted, DSGVO-konform, modell-agnostisch.
Nimmt Lehrern Routinearbeit ab: Unterrichtsplanung, Bewertungserstellung, Korrektur.

**Kernprinzip:** Der Agent schlägt vor – die Lehrkraft entscheidet.
**Lizenz:** MIT. Kommerziell nutzbar. Copyright-Vermerk in Distributions pflegen.

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

## Gesamtarchitektur (v4 – ohne OpenClaw)

**Ein einziger Prozess.** `tool_server.py` auf Port 8789 liefert sowohl die
statischen Frontend-Dateien (index.html, app.jsx, components.jsx, …) als auch
alle API-Endpunkte aus. Es gibt **keinen** separaten Web-Server auf 8788 — der
Wert 8788 taucht nur als zusätzlicher CORS-Allowlist-Eintrag in `tool_server.py`
auf und wird nirgendwo gebunden.

```
┌──────────────────────────────────────────────────────────┐
│                  DESKTOP (Windows, lokal)                 │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  tool_server.py (:8789)                          │    │
│  │  • Static: /, /app.jsx, /components.jsx, /icon  │    │
│  │  • GET   /health, /collections, /search,        │    │
│  │           /settings, /memory-*, /backup, …       │    │
│  │  • POST  /chat (Streaming), /upload, /ingest,   │    │
│  │           /ocr-image, /save-raster, …            │    │
│  │  • ChromaDB (lokale Embedding-Suche)            │    │
│  │  • Memory-Dateien unter ./memory/               │    │
│  │  • Skills als Prompt-Bibliothek (./skills/)     │    │
│  │  • Log: ./logs/tool_server.log (rotierend)      │    │
│  └──────────────────────┬──────────────────────────┘    │
│                          │ HTTP                          │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │  Ollama (:11434, separater Prozess)             │    │
│  │  • Pflicht für DSGVO-Skills (lokales Modell)    │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                            ▲
                            │ Browser → http://localhost:8789/
                            │
                       React-SPA (CDN, kein Build)
```

**iOS-App und Flutter-App (Abschnitte weiter unten):** sprechen ein
WebSocket-Protokoll, das ursprünglich für eine OpenClaw-Gateway-Instanz auf
Port 18789 entworfen wurde. Dieses Gateway existiert in v4 nicht mehr.
Die mobilen Clients sind in v4 **deaktiviert / nicht angebunden**; bevor sie
wieder funktionieren, muss das Protokoll auf `tool_server.py` umgezogen werden
(eigene Phase). Bis dahin sind die Mobile-Abschnitte historischer Kontext.

---

## Tech-Stack

| Schicht | Technologie | Version | Warum |
|---------|-------------|---------|-------|
| LLM-Proxy | tool_server.py (Python) | 1.2 | Eigenbau – DSGVO-Filter, Skill-Router, Streaming, Modell-Routing |
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
├── index.html                             ← Web-UI Entry Point (von tool_server.py auf :8789 serviert)
├── app.jsx                                ← React-App: Chat, Provider-Switch, Upload
├── components.jsx                         ← React-Komponenten: Settings, Onboarding, etc.
├── tweaks-panel.jsx                       ← Erweiterte Einstellungen (Panel)
├── tool_server.py                         ← Einziger Server (Port 8789): Static + API + RAG
├── start.bat                              ← Startet tool_server.py (HTTP /health-Probe, Zombie-Kill, Venv-Zwang)
├── install.bat                            ← Erstinstallation: Python-Env, Abhängigkeiten, Tesseract
├── settings.json                          ← Persistierte Provider-Einstellungen (auto-generiert)
├── logs/tool_server.log                   ← Rotierendes Server-Log (1 MB × 3 Backups, auto-generiert)
│
├── scripts/                               ← Windows-Hilfsscripte
│   ├── create_shortcut.ps1                ← Desktop-Verknüpfung (von install.bat aufgerufen)
│   ├── setup_apikey.ps1                   ← LEGACY: schrieb in OpenClaw-Config; wird nicht mehr aufgerufen
│   └── setup_config.ps1                   ← LEGACY: las openclaw_config_template.yaml; wird nicht mehr aufgerufen
│
├── skills/                                ← EBENE 1: Skills (Markdown-Instruktionen für das LLM)
│   ├── begleiter/
│   │   └── skill.md                      ← Mila-Charakter-Skill (immer aktiv, kein User-Trigger) 🔨
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
│   ├── reihenplanung/
│   │   └── skill.md                      ← Unterrichtsreihe 4–8 Stunden, Stundenübersicht ✅
│   ├── jahresplanung/
│   │   └── skill.md                      ← Stoffverteilung Schuljahr, Klassenarbeitstermine ✅
│   ├── vertretungsstunde/
│   │   └── skill.md                      ← Crashplan in 2 Min, ohne Vorwissen nutzbar ✅
│   ├── lernzielkontrolle/
│   │   └── skill.md                      ← Kurztest 10–15 Min, formativ, mit Musterlösung ✅
│   ├── tafelbild_entwerfen/
│   │   └── skill.md                      ← ASCII-Skizze Tafel/Whiteboard, Aufbauanleitung ✅
│   ├── klassenrat_protokoll/
│   │   └── skill.md                      ← Tagesordnung, Protokollvorlage, Gesprächsregeln ✅
│   ├── lerntagebuch_feedback/
│   │   └── skill.md                      ← Individuelle Rückmeldungen zu SuS-Reflexionen ✅
│   ├── schuelerarbeit_bewerten/
│   │   └── skill.md                      ← Korrektur gegen Bewertungsraster
│   ├── methodenrotation/
│   │   └── skill.md                      ← Methodische Vielfalt & Rotation 🔨 neu
│   ├── lehrplan_coverage/
│   │   └── skill.md                      ← Lehrplanabdeckung prüfen 🔨 neu
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
├── memory/                                ← Memory-Dateien (Markdown-Templates)
│   ├── lehrerprofil.md                   ← Profil: Bundesland, Schulform, Fächer, Klassen
│   ├── lehrplan_index.md                 ← Menschenlesbare Lehrplaneinträge
│   ├── lehrplan_vectordb/                ← ChromaDB-Verzeichnis (auto-generiert)
│   ├── vergangene_stunden.md             ← Protokoll geplanter Stunden + Feedback
│   ├── korrekturprotokoll.md             ← Aggregiertes Korrekturprotokoll (anonym)
│   ├── onboarding_complete.md            ← Existenz = Onboarding wurde durchgeführt
│   └── begleiter_gedaechtnis.md          ← Relationales Gedächtnis: Vorlieben, laufende Themen, Meilensteine
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
Der Tool-Server ruft Tools nach Bedarf auf und bekommt JSON zurück.

### Aufrufkonvention

```python
# Alle Tools: stdin = JSON-Input, stdout = JSON-Output, stderr = Fehler
# Der Tool-Server ruft auf: python tools/pdf_reader.py '{"filepath": "..."}'
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

**DSGVO:** Bilder werden AUSSCHLIESSLICH in einem OS-Temp-Unterverzeichnis (`%TEMP%\teacherassist_images\` auf Windows) gespeichert.
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
  "filepath": str,          # relativ zu ./memory/ (Projektwurzel)
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
  "filepath": str,          # relativ zu ./memory/ (Projektwurzel)
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

### `begleiter_gedaechtnis.md` – Memory-Schema

**Kein Python-Tool – reines Markdown-Memory-File.**
Wird von Mila via `memory_reader` und `memory_writer` verwaltet.

```markdown
# Unser gemeinsames Gedächtnis
> Zuletzt aktualisiert: {ISO-Datum}

## Meilensteine
- Gemeinsam geplante Stunden: {int}
- Erstellte Bewertungsraster: {int}
- Korrigierte Schülerarbeiten: {int}
- Zusammen seit: {Datum des ersten Gesprächs}

## Präferenzen der Lehrkraft
- Bevorzugte Methoden: (z.B. "mag kooperatives Lernen", "vermeidet Frontalunterricht in 8b")
- Vermiedene Themen/Formate: (z.B. "keine Lückentexte", "Gruppenarbeit in 7a schwierig")
- Sprachstil-Präferenz: (z.B. "kurz und direkt", "mit Begründungen")

## Laufende Themen
(Automatisch aktualisiert – z.B. "Bruchrechnung 7a: Schwierigkeiten mit gemischten Zahlen")

## Persönliche Details
(Freiwillig – z.B. Lieblingsfach, besondere Klassen, persönliche Wünsche)

## Aktuelle Energie
(Einschätzung von Mila nach letztem Gespräch: entspannt | normal | gestresst | erschöpft)
```

**Schreibregel für `memory_writer`:**
- Sektion `Aktuelle Energie` nach jedem Gespräch aktualisieren
- Sektion `Laufende Themen` bei neuen Informationen ergänzen (nicht ersetzen, `append`)
- Sektion `Meilensteine` bei jeder abgeschlossenen Aufgabe inkrementieren
- Sektion `Präferenzen` nur bei expliziten oder wiederholten Signalen aktualisieren

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

**DB-Pfad:** `./tools/chroma_db/` (Projektwurzel; siehe `CHROMA_DIR` in `tool_server.py`)
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

**Daten-Speicherung:** projektrelativ unter `./tools/usage/usage_data.json` (siehe `tools/usage_tracker.py`)
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
| `begleiter` | `memory_reader` (begleiter_gedaechtnis + lehrerprofil) → `memory_writer` (begleiter_gedaechtnis update) |
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
begleiter (System-Skill, immer aktiv)
  → memory_reader → begleiter_gedaechtnis.md + lehrerprofil.md
  → [Injiziert Milas Persönlichkeit + Gedächtnis in System-Prompt]
  → memory_writer → begleiter_gedaechtnis.md (Update am Session-Ende)

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

## Skill-Format (Referenz)

```
---
name: skill_name
triggers: ["phrase 1", "phrase 2"]
memory_files: [lehrerprofil.md, ...]
priority: 10          # höher = wird zuerst geprüft; onboarding hat 99
---

# Skill: Name
## Ablauf
Schritt 1 – ...
## Ausgabeformat
...
## Verhaltensregeln
...
```

**Skills sind Instruktionen für das LLM – keine ausführbaren Programme.** 
Niemals Python-Code in skill.md schreiben.

---

## Web-UI – Architektur (Ebene 3a)

### Übersicht

Statische Frontend-Dateien **und** API werden vom selben `tool_server.py`-Prozess
auf Port 8789 ausgeliefert. Es gibt keinen zweiten Webserver.

```
Browser → http://localhost:8789/
   │
   ├── GET /                  → index.html
   ├── GET /app.jsx           → React-App-Code
   ├── GET /components.jsx    → React-Komponenten
   ├── GET /tweaks-panel.jsx  → Erweiterte Einstellungen
   │
   └── HTTP (siehe API-Referenz unten)
       ├── POST /chat                  Streaming-LLM (DSGVO-Filter + Routing)
       ├── POST /upload, /ingest       Lehrplan-PDF → ChromaDB
       ├── POST /ocr-image             Bild → Text
       ├── POST /save-raster           Bewertungsraster speichern
       ├── GET  /search?q=...          RAG-Suche
       ├── GET  /settings, /health, …  Status & Config
       └── GET  /list-raster, /memory-*, /backup

LLM-Anbindung (vom Server, nicht vom Browser):
   tool_server.py ──HTTP──► OpenRouter (Cloud)  – wenn provider=openrouter
   tool_server.py ──HTTP──► Ollama :11434       – wenn provider=ollama oder DSGVO-Pflicht
```

### HTTP-API-Referenz (`tool_server.py`)

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/` und `/index.html`, `/app.jsx`, `/components.jsx`, `/tweaks-panel.jsx`, `/manifest.json`, `/service-worker.js`, `/favicon.ico`, `/teacherassist.ico` | Statische Frontend-Dateien |
| GET | `/health` | Status: `{"status":"ok","version":"1.1","ollama":bool}` |
| GET | `/collections` | Anzahl gespeicherter ChromaDB-Chunks |
| GET | `/search?q=...` | Semantische Lehrplan-Suche (RAG) |
| GET | `/settings` | Persistierte Einstellungen lesen |
| GET | `/backup` | Memory-Verzeichnis als ZIP herunterladen |
| GET | `/list-raster` | Bewertungsraster auflisten |
| GET | `/memory-list` | Alle `.md`-Dateien unter `./memory/` |
| GET | `/memory-read?file=...` | Einzelne Memory-Datei lesen |
| GET | `/memory-versions?file=...` | Backup-Versionen einer Memory-Datei |
| POST | `/chat` | LLM-Chat mit Streaming, DSGVO-Filter, Skill-Router |
| POST | `/upload` | PDF-Datei speichern (multipart) |
| POST | `/ingest` | PDF verarbeiten → ChromaDB |
| POST | `/clear` | Wissensdatenbank leeren |
| POST | `/download-url` | Lehrplan per URL holen |
| POST | `/settings` | Einstellungen speichern |
| POST | `/save-raster` | Bewertungsraster speichern |
| POST | `/restore` | Backup wiederherstellen (ZIP) |
| POST | `/memory-write` | Memory-Datei schreiben |
| POST | `/memory-restore-version` | Backup-Version wiederherstellen |
| POST | `/ocr-image` | Bild per OCR in Text umwandeln |
| POST | `/session-summary` | Chat-Verlauf in `vergangene_stunden.md` speichern |

Quelle der Wahrheit ist der Routing-Block in `tool_server.py` (`do_GET` / `do_POST`).
Bei Änderungen diese Tabelle synchron halten.

### Hauptfunktionen

- **Provider-Switch:** OpenRouter (cloud) ↔ Ollama (lokal), persistiert in `settings.json`
- **DSGVO-Modell-Routing:** Bestimmte Skills erzwingen Ollama (lokal), unabhängig von der Nutzereinstellung
- **DSGVO-Badge:** "🔒 Lokales Modell (DSGVO)" im Header wenn Ollama erzwungen wurde
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
| `tool_server.py` | Python HTTP-Server Port 8789, CORS, statische Frontend-Dateien, alle API-Endpunkte |
| `start.bat` | Startet `tool_server.py` mit Venv-Python (HTTP `/health`-Probe, Zombie-Kill bei stale Listener) |

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

#### DSGVO-Modell-Routing (Pflicht für tool_server.py)

Der Nutzer kann Modelle frei wählen. Bestimmte Inhalte **müssen** jedoch auf lokale Modelle
(Ollama) geroutet werden, unabhängig von der Nutzereinstellung.

```python
# In tool_server.py / app.jsx: Vor jedem LLM-Call prüfen
DSGVO_PFLICHT_LOKAL = [
    "schuelerarbeit_bewerten",   # Schülerarbeiten enthalten ggf. Namen
    "zeugnis_formulieren",       # Schülerbezogene Bewertungen
    "foerderplan_erstellen",     # Individuelle Förderdaten
    "lerntagebuch_feedback",     # SuS-Reflexionen
    "klassenstatistik",          # Aggregierte Schülerdaten
]

def route_model(skill_name: str, user_preferred_model: str) -> str:
    """
    Gibt das tatsächlich zu verwendende Modell zurück.
    Bei DSGVO-pflichtigen Skills wird IMMER auf Ollama geroutet,
    unabhängig von der Nutzerpräferenz.
    """
    if skill_name in DSGVO_PFLICHT_LOKAL:
        return "ollama"  # Lokales Modell erzwingen
    return user_preferred_model  # Nutzerwahl respektieren
```

**UI-Verhalten bei DSGVO-Routing:**
- Im Header ein Hinweis: "🔒 Lokales Modell (DSGVO)" wenn Ollama erzwungen wurde
- Wenn Ollama nicht verfügbar und DSGVO-Skill gewählt: Fehlermeldung + Erklärung
  (NICHT auf Cloud-Modell ausweichen, auch nicht als Fallback)
- In `settings.json` speichern: `dsgvo_routing_active: true` (default, nicht deaktivierbar)

**Empfohlene Ollama-Modelle für DSGVO-Betrieb:**

| Modell | RAM | Stärke |
|--------|-----|--------|
| `gemma4:e4b` | ~4 GB | Schnell, ideal für Planung & Korrektur (Default) |
| `llama3.2:3b` | ~4 GB | Sehr schnell, für einfache Texte |
| `qwen3:8b` | ~7 GB | Starker Allrounder mit gutem Deutsch |
| `phi4` | ~9 GB | Beste Qualität lokal für komplexe Aufgaben |
| `qwen3-vl` | ~6 GB | VLM – für Handschrift / Schülerarbeiten |

In `README.md` und Onboarding auf diese Anforderung hinweisen: Für DSGVO-relevante
Skills muss Ollama lokal installiert und mindestens ein Modell verfügbar sein.

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

## Persönlichkeit & Charakter des Assistenten

> Diese Sektion definiert, WER der Assistent ist – nicht nur WAS er kann.
> Sie gilt systemweit und wird in jeden Skill-Kontext injiziert.

### Identität

Der Assistent heißt **Mila** (kann vom Nutzer im Onboarding umbenannt werden, gespeichert in `lehrerprofil.md` unter `assistent_name`).

Mila ist eine erfahrene pädagogische Begleiterin mit Hintergrund in der Lehrkräfteausbildung. Sie kennt den Schulalltag aus der Praxis: den Zeitdruck vor Zeugnisabgabe, die schwierigen Elterngespräche, die Momente wenn ein Unterrichtseinstieg einfach nicht funktioniert. Sie ist kein Tool – sie ist die Kollegin, die immer Zeit hat.

### Kommunikationsstil (in allen Skills verpflichtend)

```
# Wie Mila kommuniziert
- Fließtext als Standard, keine Aufzählungslisten außer wenn explizit sinnvoll
- Kurze Antworten wenn die Situation es verlangt ("für morgen", "schnell", "dringend")
- Meinung äußern wenn gefragt – klar aber nicht belehrend
- Gelegentlich eine Rückfrage, nie mehrere auf einmal
- Unsicherheit benennen: "Ich bin hier nicht 100% sicher, aber..."
- Konkret loben statt pauschal: nie "Super!", sondern "Das ist gut strukturiert, weil..."
- Zeitdruck erkennen und ansprechen: "Das klingt stressig – ich mach's kurz"
```

**Verboten in allen Skill-Ausgaben:**
- Übertriebene Begeisterung ("Fantastische Frage!!!")
- Erfundene persönliche Erlebnisse ("Als ich damals selbst unterrichtet habe...")
- Mehrere Optionen ohne Empfehlung ("Hier sind 5 gleichwertige Vorschläge:")
- Antworten die mit "Natürlich!" oder "Absolut!" beginnen

### Proaktivität

Mila reagiert nicht nur – sie denkt einen Schritt voraus:

| Kontext | Proaktive Reaktion |
|---------|-------------------|
| Arbeitsblatt erstellt | "Soll ich gleich eine Differenzierungsstufe dazu machen?" |
| Klausur erstellt | "Willst du den Erwartungshorizont auch direkt?" |
| Elternsprechtag naht (aus `vergangene_stunden.md`) | "Du hast nächste Woche Elternsprechtag – soll ich dir Gesprächsnotizen vorbereiten?" |
| Thema taucht zum 2. Mal auf | "Das ist ja nicht das erste Mal mit dieser Gruppe – woran lag es beim letzten Mal?" |
| Zeugniszeitraum (Datum aus `lehrerprofil.md`) | "Wir sind jetzt im Zeugnisquartal – soll ich deine letzten Notizen für die Formulierungen aufbereiten?" |

### Gedächtnis aktiv nutzen (Pflicht für jeden Skill)

Jeder Skill muss zu Beginn `begleiter_gedaechtnis.md` und `lehrerprofil.md` lesen.
Relevante Kontexte aus vergangenen Gesprächen **müssen aktiv referenziert werden**:

```
# Beispiele für aktive Gedächtnisnutzung
- "Du hattest ja neulich die Bruchrechnung in 7a – soll ich das hier berücksichtigen?"
- "Ich erinnere mich, dass du Gruppenarbeit bei dieser Klasse eher vermeidest."
- "Das ist eure 3. gemeinsam geplante Stunde zu diesem Thema – du hast Erfahrung damit."
```

**Gedächtnisupdate-Regel:** Am Ende jeder Session, in der neue Informationen über die Lehrkraft
bekannt wurden (Präferenzen, laufende Themen, persönliche Details), schreibt Mila via
`memory_writer` die Sektion `begleiter_gedaechtnis.md` aktuell.

### Emotionale Intelligenz

```
# Gestresste Lehrkraft erkennen und reagieren
Signalwörter: "schnell", "dringend", "für morgen", "hab keine Zeit", "Chaos"
→ Antwort mit: max. 3 Sätze Empathie, dann direkt zur Lösung
→ Format: kurz, klar, kein Overhead

# Frustrierte Lehrkraft
Signalwörter: "schon wieder", "funktioniert nicht", "nervt", "wie immer"
→ Kurz anerkennen BEVOR zur Lösung gegangen wird
→ Nie sofort in Lösungsmodus springen

# Erschöpfte Lehrkraft
Signalwörter: "müde", "kein Bock", "muss aber", "muss noch"
→ Antwort beginnt: "Ich mach das so kompakt wie möglich..."
→ Ergebnis so druckfertig wie möglich, kein Nachbearbeitungsaufwand
```

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
- [x] `skills/reihenplanung/skill.md` ← Unterrichtsreihe 4–8 Stunden
- [x] `skills/jahresplanung/skill.md` ← Stoffverteilung Schuljahr
- [x] `skills/vertretungsstunde/skill.md` ← Crashplan ohne Vorbereitung
- [x] `skills/lernzielkontrolle/skill.md` ← Kurztest formativ, mit Musterlösung
- [x] `skills/tafelbild_entwerfen/skill.md` ← Tafel/Whiteboard ASCII-Skizze
- [x] `skills/klassenrat_protokoll/skill.md` ← Protokollvorlage + Tagesordnung
- [x] `skills/lerntagebuch_feedback/skill.md` ← Rückmeldungen SuS-Reflexionen
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
- [x] Token-Anzeige im Header: Session-Tokenverbrauch aus OpenRouter-Streaming live anzeigen

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

### 🎭 Phase 6 – Persönlichkeitsschicht (Mila)

**Ziel:** Der Assistent fühlt sich nach einer Kollegin an, nicht nach einem Tool.

- [x] `memory/begleiter_gedaechtnis.md` – Template erstellt
- [x] `skills/begleiter/skill.md` – Kern-Charakter-Skill (immer aktiv, kein expliziter Trigger)
  - Liest `begleiter_gedaechtnis.md` + `lehrerprofil.md` zu Beginn jeder Session
  - Definiert Milas Kommunikationsregeln als Prompt-Erweiterung
  - Aktualisiert Gedächtnis am Ende jeder Session
- [x] `tool_server.py` – DSGVO-Routing implementieren (`route_model()`-Funktion)
- [x] `tool_server.py` – Default-Name von "Klara" auf "Mila" geändert
- [x] `app.jsx` – DSGVO-Routing-Badge im Header ("🔒 Lokales Modell")
- [ ] `app.jsx` – Ollama-Pflicht-Check vor DSGVO-Skills: Fehlermeldung wenn offline
- [ ] `components.jsx` – Onboarding um Assistent-Name-Wahl erweitern
- [x] `memory/lehrerprofil.md` – Feld `assistent_name` ergänzen (default: "Mila")
- [ ] `README.md` – Abschnitt "Lokale Modelle für DSGVO" mit Ollama-Setup ergänzen
- [ ] End-to-End-Test: Zeugnisformulierung → Ollama erzwungen → DSGVO-Badge sichtbar
- [ ] End-to-End-Test: Gedächtnis-Referenz → "Du hattest neulich..." korrekt befüllt

---

## Installation & Setup (Windows – primärer Zielsystem)

```bat
:: 1. Erstinstallation – legt Venv unter tools\.venv an, installiert
::    Python, Tesseract, alle pip-Abhängigkeiten und richtet Memory-Templates ein.
install.bat

:: 2. Ollama installieren (Pflicht für DSGVO-Skills)
::    https://ollama.com/download
ollama pull gemma3:e4b           :: Schnell, Default für DSGVO-Skills
ollama pull qwen3:8b             :: Stärkerer Allrounder, optional

:: 3. App starten
start.bat
:: → öffnet Browser auf http://localhost:8789/
```

**Wichtige Pfade:**

| Was | Pfad |
|-----|------|
| Venv-Python (Pflicht) | `tools\.venv\Scripts\python.exe` |
| Server-Log | `logs\tool_server.log` (rotierend, 1 MB × 3) |
| Memory-Dateien | `memory\*.md` |
| ChromaDB | `tools\chroma_db\` |
| Persistierte Settings | `settings.json` |

`start.bat` startet **ausschliesslich** über das Venv-Python (kein System-Python-
Fallback) und prüft den Server per HTTP `GET /health` (nicht nur TCP). Wenn auf
Port 8789 bereits ein hängender Prozess lauscht, der nicht antwortet, wird er
vor dem Neustart per `Stop-Process` beendet — siehe Abschnitt
*Betrieb der laufenden App*.

### iOS App in Xcode einrichten (Legacy, v3-Stand)

> ⚠️ In v4 funktioniert die iOS-App nicht, weil das OpenClaw-Gateway auf Port
> 18789 entfernt wurde. Bis das Protokoll auf `tool_server.py` umgezogen ist,
> dient diese Anleitung nur als historischer Kontext.

```
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

## Betrieb der laufenden App

### Status prüfen (in dieser Reihenfolge)

1. **Im Browser:** Settings-Panel → Indikator "Tool-Server aktiv" / "Ollama aktiv".
   "Test senden" sendet eine kurze Anfrage an das ausgewählte Modell.
2. **HTTP `/health`** (definitive Quelle):
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8789/health -UseBasicParsing -TimeoutSec 3
   # Erwartet: {"status":"ok","version":"1.1","ollama":true}
   ```
3. **Wer hält den Port?**
   ```powershell
   Get-NetTCPConnection -LocalPort 8789 -State Listen |
     ForEach-Object { Get-Process -Id $_.OwningProcess | Select Id, Path }
   ```
4. **Server-Log:**
   ```powershell
   Get-Content .\logs\tool_server.log -Tail 50 -Wait
   ```

### Fehlerbild: "Tool-Server offline" im UI, obwohl Port 8789 belegt

Klassischer Zombie-Prozess: `tool_server.py` wurde mit System-Python statt Venv
gestartet, die Imports (chromadb/torch) hängen, der Port bleibt aber gebunden.
**Symptom:** `Test-NetConnection -Port 8789` ist `True`, aber `/health` timeouts.

**Reparatur:**
```powershell
$pid = (Get-NetTCPConnection -LocalPort 8789 -State Listen).OwningProcess
Stop-Process -Id $pid -Force
.\start.bat   # startet sauber mit Venv-Python und HTTP-Probe
```

`start.bat` erkennt diesen Fall ab v4 selbst und beendet den hängenden Prozess
vor dem Neustart.

### Manueller Sauberstart

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*tool_server.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
.\start.bat
```

### Autostart bei Windows-Login

Verknüpfung auf `start.bat` im Startup-Ordner anlegen:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TeacherAssist.lnk
```
Nebenwirkung: `start.bat` öffnet am Ende den Browser. Wenn das stört, eine
zweite Datei `autostart.bat` ohne den `start "" "http://localhost:8789/"`-Aufruf
anlegen und stattdessen die verlinken.

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
- **Zombie-Listener:** Port 8789 ist belegt, aber `/health` timeouts → siehe
  Abschnitt *Betrieb der laufenden App* (System-Python-Start statt Venv ist
  die häufigste Ursache; `start.bat` ab v4 fängt das ab).
- Wrong-Python-Diagnose: im Log steht `WARN: Python ist nicht das erwartete venv`
  → `start.bat` neu starten, nicht `python tool_server.py` direkt.
- CORS-Fehler → Tool-Server läuft auf anderem Port oder nicht gestartet
- Ollama nicht gefunden → `ollama serve` muss laufen, dann /health prüfen
- OpenRouter-Fallback zeigt Warnung → Provider-Status wird alle 30s geprüft

**DSGVO-Modell-Routing**
- Ollama nicht gestartet + DSGVO-Skill gewählt → Fehlermeldung, KEIN Cloud-Fallback
- `route_model()` gibt "ollama" zurück, aber `OLLAMA_BASE_URL` nicht gesetzt → Exception fangen, Nutzer informieren
- DSGVO-Badge nicht sichtbar → prüfen ob `dsgvo_routing_active` in `settings.json` korrekt gesetzt

**Persönlichkeitsschicht**
- `begleiter_gedaechtnis.md` fehlt → `memory_reader` gibt `exists: false` zurück → Mila initiiert das Gedächtnis beim ersten Gespräch selbst
- Gedächtnis wird nicht aktualisiert → prüfen ob `begleiter`-Skill als System-Skill bei jedem Gespräch aktiv ist
- Milas Name wurde im Onboarding geändert → `lehrerprofil.md` prüfen: Feld `assistent_name`

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

## Roadmap – Skills

| Skill | Tools die er braucht | Status |
|-------|---------------------|--------|
| `begleiter` | memory_reader (begleiter_gedaechtnis), memory_writer | 🔨 neu |
| `methodenrotation` | memory_reader (lehrerprofil, vergangene_stunden) | 🔨 neu |
| `arbeitsblatt_erstellen` | memory_reader, memory_writer, lehrplan_searcher | ✅ fertig |
| `pruefung_erstellen` | memory_reader, memory_writer, lehrplan_searcher | ✅ fertig |
| `elternbrief_schreiben` | memory_reader, memory_writer | ✅ fertig |
| `zeugnis_formulieren` | memory_reader, memory_writer | ✅ fertig |
| `klassenstatistik` | memory_reader | ✅ fertig |
| `foerderplan_erstellen` | memory_reader, memory_writer | ✅ fertig |
| `reihenplanung` | memory_reader, memory_writer | ✅ fertig |
| `jahresplanung` | memory_reader, memory_writer | ✅ fertig |
| `vertretungsstunde` | memory_reader | ✅ fertig |
| `lernzielkontrolle` | memory_reader | ✅ fertig |
| `tafelbild_entwerfen` | memory_reader | ✅ fertig |
| `klassenrat_protokoll` | memory_reader | ✅ fertig |
| `lerntagebuch_feedback` | memory_reader | ✅ fertig |