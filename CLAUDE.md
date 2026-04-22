# LehrerAgent – CLAUDE.md
> Vollständiger Bauplan für Claude Code. Wird bei jeder Session automatisch geladen.
> Letzte Aktualisierung: April 2026

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
│  EBENE 1 – SKILLS  (Markdown, bereits fertig ✅)            │
│  Was der Agent tun soll. Reine Instruktionen für das LLM.   │
│  Kein ausführbarer Code. Trigger → Ablauf → Ausgabeformat.  │
├─────────────────────────────────────────────────────────────┤
│  EBENE 2 – TOOLS  (Python, als nächstes zu bauen 🔨)        │
│  Was der Agent nicht selbst kann: PDFs lesen, Dateien       │
│  schreiben, OCR, externe APIs. Werden von Skills aufgerufen.│
├─────────────────────────────────────────────────────────────┤
│  EBENE 3 – APP  (Flutter, Phase 3 📱)                       │
│  UI für Lehrer auf Desktop + Mobil. Kein eigenes Backend.   │
│  Reines Interface zu OpenClaw über WebSocket.               │
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
│  │  OpenClaw Runtime                               │    │
│  │                                                 │    │
│  │  Gateway (:18789) ←→ Brain (LLM: Claude API)   │    │
│  │       ↕                    ↕                   │    │
│  │  Skills (Markdown)    Tools (Python)            │    │
│  │       ↕                    ↕                   │    │
│  │  Memory (~/.openclaw/memory/*.md)               │    │
│  └─────────────────────────────────────────────────┘    │
│                          ↕                               │
│              WebSocket / HTTPS (:18789)                  │
└──────────────────────────┬───────────────────────────────┘
                           │ Tailscale VPN
              ┌────────────┴────────────┐
              │      Flutter App        │
              │  Desktop + Mobile       │
              │  (reines UI, kein       │
              │   eigenes Backend)      │
              └─────────────────────────┘
```

---

## Tech-Stack

| Schicht | Technologie | Version | Warum |
|---------|-------------|---------|-------|
| Agent-Runtime | OpenClaw | MIT, aktuell | Self-hosted, model-agnostic, Skills-System |
| LLM | Claude Sonnet (claude-sonnet-4-6) | aktuell | Bestes Modell für Deutsch + Strukturaufgaben |
| Tools | Python | 3.11+ | PDF-Parsing, Dateisystem, OCR |
| PDF-Parsing | pypdf | 4.x | Text-PDFs; zuverlässig, kein C-Build nötig |
| OCR | pytesseract + Pillow | aktuell | Gescannte PDFs und Schülerarbeitsfotos |
| Vektorspeicher | chromadb (lokal) | 0.5.x | Lehrplan-Einträge semantisch durchsuchbar |
| Embeddings | sentence-transformers | aktuell | Lokal, kein API-Call, DSGVO-sicher |
| Frontend | Flutter | 3.x (Dart 3) | Eine Codebase → Android, iOS, Windows, macOS, Linux |
| VPN | Tailscale | aktuell | Kein Port-Forwarding, DSGVO-sicher, kostenlos/3 Nutzer |
| Memory | Markdown-Dateien (lokal) | — | Kein Drittanbieter, transparent, editierbar |
| VPS optional | Hetzner CX22 | ~5€/Monat | Multi-User / Schulserver |

---

## Vollständige Projektstruktur

```
lehreragent/
├── CLAUDE.md                              ← Diese Datei (Projektwurzel)
│
├── skills/                                ← EBENE 1: OpenClaw Skills (Markdown)
│   ├── onboarding/
│   │   └── skill.md                      ← Ersteinrichtung, auto-trigger bei Erststart
│   ├── unterricht_planen/
│   │   └── skill.md                      ← Stundenentwürfe, liest lehrplan_index
│   ├── bewertung_erstellen/
│   │   └── skill.md                      ← Erwartungshorizont + Notenschlüssel
│   ├── schuelerarbeit_bewerten/
│   │   └── skill.md                      ← Korrektur gegen Bewertungsraster
│   └── lehrplan_einlesen/
│       └── skill.md                      ← Delegiert an tool: pdf_reader / ocr_reader
│
├── tools/                                 ← EBENE 2: Python-Tools (ausführbarer Code)
│   ├── __init__.py
│   ├── pdf_reader.py                     ← Lehrplan-PDFs parsen (Text-PDFs)
│   ├── ocr_reader.py                     ← Gescannte PDFs / Fotos → Text (pytesseract)
│   ├── memory_writer.py                  ← Strukturiertes Schreiben in Memory-Dateien
│   ├── memory_reader.py                  ← Memory-Dateien lesen + nach Schlüsseln suchen
│   ├── lehrplan_indexer.py               ← Text → ChromaDB (Vektorsuche für Lehrpläne)
│   ├── lehrplan_searcher.py              ← Semantische Suche in Lehrplan-Vektordatenbank
│   ├── usage_tracker.py                  ← Token- & Kosten-Tracking für Claude API ✅
│   └── requirements.txt                  ← pypdf, pytesseract, Pillow, chromadb,
│                                            sentence-transformers, python-frontmatter
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
├── app/                                   ← EBENE 3: Flutter App (IMPLEMENTIERT ✅)
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart                     ← Entry point, Router, Theme (Material 3) ✅
│   │   ├── config/
│   │   │   └── app_config.dart           ← Host, Port, VPN-Hostname aus ENV ✅
│   │   ├── services/
│   │   │   ├── openclaw_service.dart     ← WebSocket-Client zu OpenClaw (:18789) ✅
│   │   │   ├── connection_manager.dart   ← WLAN → Tailscale → Offline Fallback ✅
│   │   │   ├── offline_queue.dart        ← Aufträge zwischenspeichern bei kein Netz ✅
│   │   │   ├── notification_service.dart ← FCM (Android) + APNs (iOS) ✅
│   │   │   └── tailscale_service.dart    ← Tailscale VPN Management ✅
│   │   ├── screens/
│   │   │   ├── chat_screen.dart          ← Haupt-Chat-Interface ✅
│   │   │   ├── tasks_screen.dart         ← Laufende Agentenaufgaben + Status ✅
│   │   │   ├── results_screen.dart       ← Fertige Ergebnisse, drucken/exportieren ✅
│   │   │   ├── memory_screen.dart        ← Lehrerprofil + Memory-Übersicht (Desktop)
│   │   │   └── settings_screen.dart      ← Verbindung, Modell, Benachrichtigungen ✅
│   │   └── widgets/
│   │       ├── message_bubble.dart       ← Chat-Nachricht (Lehrer / Agent)
│   │       ├── file_upload_button.dart   ← PDF / Bild hochladen
│   │       ├── quick_actions.dart        ← Shortcut-Buttons (mobile)
│   │       └── connection_indicator.dart ← WLAN / VPN / Offline-Status
│   └── test/
│
└── docs/
    ├── architektur.md                    ← Diagramme, ADRs
    ├── deployment.md                     ← VPS-Setup, Schulserver
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

### `pdf_reader.py`

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

### `ocr_reader.py`

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

### `memory_writer.py`

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

**Stolperstelle:** Encoding immer explizit `utf-8` setzen. macOS schreibt sonst latin-1.

---

### `memory_reader.py`

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

### `lehrplan_indexer.py`

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
  "collection": str,        # ChromaDB Collection-Name
  "error": str | None
}
```

**DB-Pfad:** `~/.openclaw/memory/lehrplan_vectordb/`
**Embedding-Modell:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(läuft vollständig lokal, kein API-Call, DSGVO-konform)

---

### `lehrplan_searcher.py`

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

### `usage_tracker.py`

**Zweck:** Token- und Kosten-Tracking für Claude API-Nutzung

```python
# Input für Tracking:
{
  "model": str,             # Modellname, z.B. "claude-3-5-sonnet-20241022"
  "input_tokens": int,      # Anzahl Input-Tokens
  "output_tokens": int,     # Anzahl Output-Tokens
  "skill_name": str | None, # Optional: Skill-Name für detailliertes Tracking
  "request_id": str | None, # Optional: Request-ID für Debugging
  "timestamp": str | None   # Optional: Zeitstempel (ISO-Format)
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
    "request_id": str | None,
    "timestamp": str,
    "day_key": str,         # Format: "YYYY-MM-DD"
    "month_key": str        # Format: "YYYY-MM"
  },
  "totals": {
    "total_tokens": int,
    "total_cost_usd": float,
    "total_requests": int
  },
  "warnings": list[str]     # Budget-Warnungen, falls vorhanden
}

# Input für Kostenschätzung:
{
  "model": str,
  "estimated_input_tokens": int,
  "estimated_output_tokens": int
}

# Output für Kostenschätzung:
{
  "model": str,
  "estimated_input_tokens": int,
  "estimated_output_tokens": int,
  "estimated_input_cost_usd": float,
  "estimated_output_cost_usd": float,
  "estimated_total_cost_usd": float,
  "price_per_million_input": float,
  "price_per_million_output": float
}
```

**Funktionen:**
1. **Token-Tracking:** Verfolgt Input- und Output-Tokens pro Request
2. **Kostenberechnung:** Berechnet API-Kosten basierend auf Claude-Preisen
3. **Budget-Warnungen:** Warnt bei Überschreitung von Budget-Grenzen
4. **Detaillierte Reports:** Tägliche, monatliche und Skill-basierte Berichte
5. **Export-Funktionen:** JSON, CSV und Text-Exporte
6. **Kostenschätzung:** Schätzt Kosten für geplante Requests vorab

**Claude API Preise (Stand: April 2026):**
- `claude-3-5-sonnet-20241022`: $3.00/M Input, $15.00/M Output
- `claude-3-opus-20240229`: $15.00/M Input, $75.00/M Output  
- `claude-3-sonnet-20240229`: $3.00/M Input, $15.00/M Output
- `claude-3-haiku-20240307`: $0.25/M Input, $1.25/M Output

**Daten-Speicherung:** `~/.openclaw/usage/usage_data.json`
**Standard-Budget:** $100/Monat mit Warnungen bei 75% und 90% Auslastung

**Integration in OpenClaw:** Wird automatisch nach jedem LLM-Call aufgerufen, um Token-Nutzung zu tracken.

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
| `schuelerarbeit_bewerten` | `ocr_reader` (falls Foto/Scan) → `memory_reader` (bewertungsraster) → `memory_writer` (protokoll) |

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

schuelerarbeit_bewerten
  ← ocr_reader (wenn Foto/Scan übergeben)
  ← memory_reader ← bewertungsraster/{name}.md
  → [LLM bewertet Kriterium für Kriterium]
  → memory_writer → korrekturprotokoll.md
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

## Flutter App – Design-Prinzipien

- **Kein eigenes Backend** – App ist reines Interface zu OpenClaw
- **Adaptive UI:** Mobile = Chat-first; Desktop = Chat + Sidebar (Memory-Übersicht)
- **Offline-Modus:** zeigt letzte Ergebnisse aus lokalem Cache
- **Kein Schülerdaten-Upload** über die App – nur über Desktop-Client (DSGVO)
- Flutter: **Material 3**, adaptive Layouts, keine fixen Pixel-Breakpoints
- Dart: **null-safety** durchgehend, keine deprecated APIs

### Verbindungslogik (Priorität, in `connection_manager.dart`)

```
1. Selbes WLAN → direkte lokale IP (aus app_config)
2. Tailscale → VPN-Hostname (aus app_config)
3. Kein Zugriff → Offline-Modus
   → Auftrag in offline_queue.dart speichern
   → Beim Reconnect automatisch senden
```

### WebSocket-Verbindung

```dart
// Immer dart:io WebSocket verwenden (nicht dart:html – funktioniert nur im Browser)
// Reconnect mit exponential backoff: 1s → 2s → 4s → 8s → max 30s
// Heartbeat-Ping alle 30s um Connection am Leben zu halten
```

---

## Wichtige Regeln

### Datenschutz (DSGVO – nicht verhandelbar)
- Schülernamen werden NICHT in Memory gespeichert (Standard: anonym)
- Keine personenbezogenen Daten in LLM-API-Calls
- OCR-Ergebnisse von Schülerarbeiten: nur temporär im RAM, nicht auf Disk
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
- Alle Dateipfade über `os.path.expanduser()` auflösen

---

## Entwicklungsphasen & Arbeitsplan für Claude Code

### ✅ Phase 0 – Skills & Memory (abgeschlossen)
- [x] `skills/onboarding/skill.md`
- [x] `skills/unterricht_planen/skill.md`
- [x] `skills/bewertung_erstellen/skill.md`
- [x] `skills/schuelerarbeit_bewerten/skill.md`
- [x] `skills/lehrplan_einlesen/skill.md`
- [x] Memory-Templates (alle .md-Dateien)

### 🔨 Phase 1 – Tools (abgeschlossen ✅)
Reihenfolge eingehalten – jedes Tool braucht das vorherige:

- [x] `tools/requirements.txt` anlegen
- [x] `tools/memory_reader.py` – wird von fast allen Tools gebraucht
- [x] `tools/memory_writer.py` – wird von fast allen Skills gebraucht
- [x] `tools/pdf_reader.py` – Grundlage für lehrplan_einlesen
- [x] `tools/ocr_reader.py` – Erweiterung für Scans + Schülerarbeitsfotos
- [x] `tools/lehrplan_indexer.py` – ChromaDB aufbauen
- [x] `tools/lehrplan_searcher.py` – Semantische Suche
- [x] Manueller Integrationstest: PDF einlesen → indexieren → Stunde planen

### 📱 Phase 2 – Flutter Desktop App (abgeschlossen ✅)
- [x] `app/` Grundgerüst (`flutter create`)
- [x] `app_config.dart` mit ENV-Variablen
- [x] `openclaw_service.dart` WebSocket-Client
- [x] `chat_screen.dart` Basis-Chat-Interface
- [x] `file_upload_button.dart` für PDFs
- [ ] End-to-End-Test: App → OpenClaw → Skill → Tool → Antwort

### 📱 Phase 3 – Mobile + Remote (abgeschlossen ✅)
- [x] Adaptives Layout für Mobile (Chat-first)
- [x] `connection_manager.dart` mit WLAN/Tailscale/Offline-Fallback
- [x] `offline_queue.dart`
- [x] Quick-Actions-Widget für Mobile (Shortcut-Buttons)

### 🔔 Phase 4 – Push & Hintergrund (abgeschlossen ✅)
- [x] OpenClaw als Tray-App (Desktop, via OpenClaw Heartbeat-Config)
- [x] `notification_service.dart` (FCM + APNs)
- [x] Benachrichtigung bei fertigem Agenten-Task
- [x] `tailscale_service.dart` – Tailscale VPN Management

### 📋 Phase 5 – Komplettierung & Dokumentation
- [x] `main.dart` – App-Entrypoint mit Routing und Provider-Setup ✅
- [x] `openclaw_config_template.yaml` – OpenClaw Konfigurationsvorlage ✅
- [x] CLAUDE.md – Aktualisierung der Dokumentation ✅
- [ ] Widgets implementieren (message_bubble, connection_indicator)
- [ ] `memory_screen.dart` – Lehrerprofil + Memory-Übersicht
- [ ] Kompletter End-to-End-Test aller Skills

---

## Installation & Setup

```bash
# 1. OpenClaw installieren (Node 22 LTS oder Node 24)
npm install -g openclaw

# 2. Skills deployen
cp -r skills/* ~/.openclaw/skills/
cp -r memory/* ~/.openclaw/memory/

# 3. Skills laden
openclaw skill load onboarding unterricht_planen bewertung_erstellen \
  schuelerarbeit_bewerten lehrplan_einlesen

# 4. Python-Umgebung für Tools
cd tools/
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 5. Tesseract installieren (für OCR)
# macOS:   brew install tesseract tesseract-lang
# Ubuntu:  sudo apt install tesseract-ocr tesseract-ocr-deu
# Windows: Installer von github.com/UB-Mannheim/tesseract

# 6. Tools in OpenClaw registrieren (in ~/.openclaw/config.yaml)
# tools_path: /absoluter/pfad/zu/lehreragent/tools
# tools_python: /absoluter/pfad/zu/lehreragent/tools/.venv/bin/python

# 7. Agent starten
openclaw start

# 8. Flutter App (Desktop)
cd ../app/
flutter pub get
flutter run -d macos    # oder: windows / linux
```

---

## Bekannte Stolperstellen

**OpenClaw**
- Gateway startet nicht → Port 18789 belegt? `lsof -i :18789` / `netstat -ano | findstr 18789`
- Skills triggern nicht → Trigger-Phrase zu ungenau? `/skills list` zum Debuggen

**Python Tools**
- `pypdf` gibt leeren Text zurück → PDF ist ein Scan → Fallback auf `ocr_reader.py`
- `pytesseract` findet Tesseract nicht → `pytesseract.pytesseract.tesseract_cmd` explizit setzen
- ChromaDB-Pfad: immer `os.path.expanduser("~/.openclaw/memory/lehrplan_vectordb")` verwenden
- Memory-Dateien: `open(path, encoding="utf-8")` – niemals ohne encoding-Parameter

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
| `arbeitsblatt_erstellen` | memory_reader, memory_writer | Hoch |
| `pruefung_erstellen` | memory_reader, memory_writer, lehrplan_searcher | Hoch |
| `elternbrief_schreiben` | memory_reader, memory_writer | Mittel |
| `zeugnis_formulieren` | memory_reader, memory_writer | Mittel |
| `klassenstatistik` | memory_reader, (csv_writer neu) | Mittel |
| `foerderplan_erstellen` | memory_reader, memory_writer | Niedrig |
