# LehrerAgent – CLAUDE.md
> Vollständiger Bauplan für Claude Code. Wird bei jeder Session automatisch geladen.
> Letzte Aktualisierung: April 2026 (v3 – iOS WiFi-App ergänzt)

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
│  EBENE 3 – APP  (Swift/iOS + Flutter Desktop, Phase 3 📱)   │
│  iOS: Swift/SwiftUI, natives Kamera-Interface, WiFi-only    │
│  Desktop: Flutter. Beide kommunizieren über WebSocket.      │
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
├── app_ios/                               ← EBENE 3a: iOS App (Swift/SwiftUI) ✅ fertig
│   └── LehrerAgent/
│       ├── LehrerAgentApp.swift           ← Entry Point, TabView-Router
│       ├── Info_additions.plist           ← Berechtigungen: Kamera, Galerie, LAN
│       ├── Services/
│       │   ├── ConnectionService.swift    ← WebSocket-Client (URLSessionWebSocketTask)
│       │   │                                Reconnect mit exponential backoff
│       │   └── ImageService.swift        ← Kamera, Galerie, Skalierung auf 1600px,
│       │                                    Perspektivkorrektur (CIDetectorTypeRectangle)
│       ├── Models/
│       │   └── UploadViewModel.swift     ← Upload-State-Machine, Server-Nachrichten,
│       │                                    UploadState enum, EvaluationResult
│       └── Views/
│           ├── ConnectView.swift         ← IP eingeben, verbinden, in UserDefaults speichern
│           └── CaptureView.swift         ← Foto, Kontextform (Fach/Klasse/Aufgabe),
│                                            Fortschrittsanzeige, Ergebniscard
│
├── app/                                   ← EBENE 3b: Flutter Desktop App (geplant)
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart                     ← Entry point, Router, Theme (Material 3)
│   │   ├── config/
│   │   │   └── app_config.dart           ← Host, Port, VPN-Hostname aus ENV
│   │   ├── services/
│   │   │   ├── openclaw_service.dart     ← WebSocket-Client zu OpenClaw (:18789)
│   │   │   ├── connection_manager.dart   ← WLAN → Tailscale → Offline Fallback
│   │   │   ├── offline_queue.dart        ← Aufträge zwischenspeichern bei kein Netz
│   │   │   └── notification_service.dart ← FCM (Android) + APNs (iOS)
│   │   ├── screens/
│   │   │   ├── chat_screen.dart          ← Haupt-Chat-Interface
│   │   │   ├── tasks_screen.dart         ← Laufende Agentenaufgaben + Status
│   │   │   ├── results_screen.dart       ← Fertige Ergebnisse, drucken/exportieren
│   │   │   ├── memory_screen.dart        ← Lehrerprofil + Memory-Übersicht (Desktop)
│   │   │   └── settings_screen.dart      ← Verbindung, Modell, Benachrichtigungen
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

### `image_receiver.py` ✅ fertig

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
iOS-App sendet immer JPEG (explizit so konfiguriert in `ImageService.swift`).

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

## iOS App – Architektur & Protokoll (Ebene 3a)

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
Sie wird in `UserDefaults` gespeichert (`openclaw_host`).
**Port:** 18789 (OpenClaw Gateway Standard).

### iOS Nachrichtenprotokoll (JSON over WebSocket)

```json
// iPhone → Mac: Bild senden
{
  "type": "upload",
  "id": "uuid-1234",
  "skill": "schuelerarbeit_bewerten",
  "image": {
    "data": "<base64-JPEG>",
    "format": "jpeg",
    "width_px": 1600,
    "height_px": 2263
  },
  "context": {
    "fach": "Mathematik",
    "klasse": "7a",
    "aufgabe": "Bruchrechnung Test 3"
  }
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
1. In CaptureView: UIImagePickerController liefert UIImage
2. ImageService.perspectiveCorrect(): CIDetectorTypeRectangle
3. ImageService.scale(): auf max. 1600px Breite/Höhe
4. UIImage.jpegData(compressionQuality: 0.85): ~200–400 KB
5. Data.base64EncodedString() → in UploadMessage.image.data
```

### iOS State-Machine (UploadState enum)

```
idle
  → [Foto aufnehmen] → idle (mit capturedImage)
  → [Auswerten tippen] → optimizing
optimizing
  → [Perspektivkorrektur + Skalierung OK] → uploading(progress: 0.1)
uploading
  → [WebSocket.send() OK] → uploading(progress: 1.0)
  → [Server erste Antwort] → processing(step:, percent:)
processing
  → [Server: type="result"] → done(result: EvaluationResult)
  → [Server: type="error"] → failed(message:)
done / failed
  → [Nächste Arbeit tippen] → idle
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
   - Product Name: LehrerAgent
   - Interface: SwiftUI
   - Language: Swift
   - Minimum iOS: 16.0

2. Swift-Dateien aus app_ios/LehrerAgent/ in Xcode-Projekt ziehen

3. Info.plist: Einträge aus Info_additions.plist einfügen

4. Signing: Team auswählen (Apple Developer Account nötig für echtes Gerät)
   Für Simulator: kein Account nötig

5. Testen im Simulator:
   - Kamera nicht verfügbar → Gallery-Picker verwenden
   - IP: Mac-IP aus WLAN-Einstellungen
```

### iOS Stolperstellen

- `NSLocalNetworkUsageDescription` vergessen → App kann keine WebSocket-Verbindung aufbauen (iOS blockiert still)
- `dart:io` vs `URLSessionWebSocketTask`: In Swift immer `URLSessionWebSocketTask` (seit iOS 13 nativ, keine Library)
- HEIC-Format: `UIImagePickerController` liefert `UIImage` – `jpegData()` konvertiert automatisch
- Simulator hat keine Kamera → immer `GalleryPicker` als Fallback einbauen (bereits implementiert)
- Reconnect: `ConnectionService` versucht 5x mit exponential backoff (1s → 2s → 4s → 8s → 16s)

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

### 🔨 Phase 1 – Python Tools (aktuell)
Reihenfolge einhalten – jedes Tool braucht das vorherige:

- [ ] `tools/requirements.txt` anlegen
- [ ] `tools/memory_reader.py`
- [ ] `tools/memory_writer.py`
- [x] `tools/image_receiver.py` ← fertig (Base64-Empfang, temp. Speichern, Cleanup)
- [ ] `tools/pdf_reader.py`
- [ ] `tools/ocr_reader.py` ← auch für iPhone-Bilder zuständig
- [ ] `tools/lehrplan_indexer.py`
- [ ] `tools/lehrplan_searcher.py`
- [ ] Integrationstest: iPhone-Foto → image_receiver → ocr_reader → bewerten

### ✅ Phase 2 – iOS App, WLAN-only (abgeschlossen)
- [x] `ConnectionService.swift` – WebSocket, Ping, Reconnect
- [x] `ImageService.swift` – Kamera, Galerie, Skalierung, Perspektivkorrektur
- [x] `UploadViewModel.swift` – State-Machine, Server-Nachrichten
- [x] `ConnectView.swift` – IP-Eingabe, UserDefaults
- [x] `CaptureView.swift` – Foto, Kontextform, Fortschritt, Ergebnis
- [x] `LehrerAgentApp.swift` – Entry Point, TabView
- [x] `Info_additions.plist` – Kamera/Galerie/LAN-Berechtigungen
- [ ] In Xcode einrichten + auf echtem Gerät testen
- [ ] End-to-End-Test: iPhone → WLAN → Mac → OCR → Note → iPhone

### 📱 Phase 3 – Flutter Desktop App
- [ ] `app/` Grundgerüst (`flutter create`)
- [ ] `app_config.dart` mit ENV-Variablen
- [ ] `openclaw_service.dart` WebSocket-Client (dart:io, nicht dart:html)
- [ ] `chat_screen.dart` Basis-Chat-Interface
- [ ] `file_upload_button.dart` für PDFs (file_picker Package)
- [ ] Adaptives Layout: Desktop = Chat + Sidebar, Mobile = Chat-first

### 🌐 Phase 4 – Remote-Zugriff (Tailscale)
- [ ] Tailscale auf Mac + iPhone einrichten
- [ ] `connection_manager.dart` / iOS `ConnectionService` erweitern:
  Priorität: 1. WLAN-IP → 2. Tailscale-Hostname → 3. Offline-Queue
- [ ] `offline_queue` (iOS: UserDefaults/CoreData, Flutter: shared_preferences)
- [ ] CLAUDE.md: iOS-Abschnitt um Tailscale-Variante ergänzen

### 🔔 Phase 5 – Push & Hintergrund
- [ ] OpenClaw Heartbeat: Tray-Icon + Hintergrund-Modus (Desktop)
- [ ] `notification_service.dart` / iOS `UNUserNotificationCenter`
- [ ] Benachrichtigung: "Deine Stunde für Montag ist fertig"
- [ ] Automatischer Heartbeat-Skill: `cleanup_old` für Temp-Bilder alle 30 Min

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

# 5. Tesseract installieren (für OCR – Schülerarbeiten + Scans)
# macOS:   brew install tesseract tesseract-lang
# Ubuntu:  sudo apt install tesseract-ocr tesseract-ocr-deu
# Windows: Installer von github.com/UB-Mannheim/tesseract

# 6. Tools in OpenClaw registrieren (~/.openclaw/config.yaml)
# tools_path: /absoluter/pfad/zu/lehreragent/tools
# tools_python: /absoluter/pfad/zu/lehreragent/tools/.venv/bin/python

# 7. Agent starten – Gateway auf allen Interfaces lauschen (wichtig für iOS!)
openclaw start --host 0.0.0.0 --port 18789
# → Mac-IP im WLAN herausfinden:
ipconfig getifaddr en0   # macOS
# → Diese IP in der iOS-App eingeben
```

```
iOS App in Xcode einrichten:
1. Xcode → File → New → Project → iOS App
   Name: LehrerAgent | SwiftUI | Swift | Min iOS: 16.0
2. Dateien aus app_ios/LehrerAgent/ ins Projekt ziehen
3. Info.plist: Einträge aus Info_additions.plist einfügen
4. iPhone per USB verbinden → Trust bestätigen
5. Signing: kostenloses Apple-Konto reicht für Sideload (7 Tage)
6. Run ▶ → App auf iPhone installieren
7. App öffnen → Mac-IP eingeben → Verbinden
```

```bash
# Flutter Desktop App (Phase 3, noch nicht implementiert)
cd app/
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

**iOS App**
- `NSLocalNetworkUsageDescription` fehlt → App verbindet sich nie, kein Fehler sichtbar
- `openclaw start` ohne `--host 0.0.0.0` → lauscht nur auf localhost, iPhone kann nicht erreichen
- Simulator hat keine Kamera → GalleryPicker testen, auf echtem Gerät deployen
- iOS 16 Minimum: `URLSessionWebSocketTask` und `PHPickerViewController` benötigen iOS 13+, aber SwiftUI-Features erfordern 16+
- UploadViewModel doppelt initialisiert → StateObject korrekt in RootView anlegen, per environmentObject weitergeben (Hinweis in LehrerAgentApp.swift)

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
