# TeacherAssist (LehrerAgent) – CLAUDE.md
> Bauplan für Claude Code. Wird bei jeder Session automatisch geladen.
> Letzte Aktualisierung: 2026-07-19 (v5 – teacherassist_core, Vite-Build, mobile Clients entfernt)

---

## Projektziel

KI-Assistent für deutsche Lehrkräfte. Self-hosted, DSGVO-konform, modell-agnostisch.
Nimmt Lehrern Routinearbeit ab: Unterrichtsplanung, Bewertungserstellung, Korrektur.

**Kernprinzip:** Der Agent schlägt vor – die Lehrkraft entscheidet.
**Lizenz:** MIT. Kommerziell nutzbar. Copyright-Vermerk in Distributions pflegen.

---

## Architektur (v5)

**Ein einziger Prozess.** `tool_server.py` (Python-Stdlib-`http.server`, kein Framework)
liefert auf Port **8789** sowohl die statischen Frontend-Dateien als auch alle
`/api/v1/*`-Endpunkte aus. Es gibt keinen zweiten Webserver und kein OpenClaw-Gateway
mehr – beide sind aus früheren Versionen entfernt.

```
┌──────────────────────────────────────────────────────────────┐
│                 DESKTOP (Windows, lokal)                     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  tool_server.py  (:8789)                              │   │
│  │  • Static: web_dist/ (Vite-Build, bevorzugt) oder     │   │
│  │    Repo-Root-Fallback (index.html, app.jsx, …)        │   │
│  │  • /api/v1/* – siehe Routentabelle unten              │   │
│  │  • Session/CSRF via teacherassist_core.security       │   │
│  │  • DSGVO-Filter via teacherassist_core.privacy        │   │
│  │  • Secrets via teacherassist_core.runtime              │   │
│  │    (Windows Credential Manager, nie Klartext)         │   │
│  │  • Verschlüsselter Chat-/Profil-State via              │   │
│  │    teacherassist_core.storage (Fernet)                │   │
│  │  • Skills via teacherassist_core.skills               │   │
│  │    (SkillRegistry, validiert gegen skills_index.json) │   │
│  └───────────────────────┬────────────────────────────────┘  │
│                          │ HTTP                              │
│  ┌───────────────────────┴────────────────────────────────┐  │
│  │  Ollama (:11434, separater Prozess, optional/Pflicht    │  │
│  │  für DSGVO-Skills)                                      │  │
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
                            ▲
                            │ Browser → http://localhost:8789/
```

**Mobile Clients (iOS/Flutter) existieren nicht mehr im aktiven Code.** Sie sprachen
ein WebSocket-Protokoll zu einem OpenClaw-Gateway auf Port 18789, das nie Teil dieser
Architektur wurde. Die Quellen sind vollständig entfernt und auf dem Branch
`archive/mobile-clients` erhalten, falls sie je reaktiviert werden sollen.

---

## Laufzeit-Datenverzeichnis (wichtig!)

Alle veränderlichen Daten liegen **nicht mehr im Repo**, sondern unter:

```
%LOCALAPPDATA%\TeacherAssist\        (Windows, Standard)
~/.teacherassist/                    (Fallback ohne LOCALAPPDATA, z. B. Linux/macOS)
```

Override per Umgebungsvariable: `TEACHERASSIST_DATA_DIR`.

Siehe `teacherassist_core/runtime.py` (`RuntimePaths.from_environment`):

| Pfad | Zweck |
|------|-------|
| `<root>/memory/` | Memory-Markdown-Dateien (beim ersten Start aus `./memory/`-Templates im Repo kopiert) |
| `<root>/uploads/` | Temporäre PDF-Uploads |
| `<root>/exports/` | Export-Dateien (`/api/v1/export-file`) |
| `<root>/logs/tool_server.log` | Rotierendes Server-Log (1 MB × 3 Backups) |
| `<root>/chroma_db/` | ChromaDB-Vektorspeicher |
| `<root>/settings.json` | Nicht-geheime Einstellungen (Provider, Modellnamen) |
| `<root>/state.enc` | Fernet-verschlüsselter Chat-/Profil-State |

Secrets (OpenRouter-/Custom-API-Key, der Fernet-Datenschlüssel) liegen **nicht** in
`settings.json`, sondern im Windows Credential Manager (`keyring`-Paket). Ohne
`keyring` fällt der Server auf einen In-Memory-Fallback zurück (Secrets gehen beim
Neustart verloren) – siehe `teacherassist_core/runtime.py: CredentialStore`.

Das repo-lokale `./memory/` bleibt als **Template-Quelle** bestehen; die App liest/
schreibt zur Laufzeit ausschliesslich unter `<root>/memory/`.

---

## Einstellungen (`settings.json`, `SETTINGS_KEYS`)

`teacherassist_core/runtime.py: SETTINGS_KEYS` ist die **Allowlist**, gegen die
`SettingsStore` jeden gespeicherten Schlüssel filtert (`_write`, `public`,
`migrate_legacy_settings` – siehe deren Aufrufstellen in `runtime.py`). Die
OCR-Konsens-Pipeline hat folgende Schlüssel zu `SETTINGS_KEYS`/`DEFAULT_SETTINGS`
hinzugefügt:

`ocrEngines`, `ocrVisionModel`, `ocrHtrModel`, `ocrPaddleModel`,
`ocrPaddleBackend`, `ocrTargetDpi`, `ocrMinAgreement`, `ocrMinConfidence`,
`ocrSubject`, `ocrLanguage`, `ocrRetentionDays`, `ocrDeleteAfterApproval`,
`ocrAutoApproveNonStudent`, `ocrDevice`, `ocrRequireEngines`, `ocrMaxPages`,
`ocrVerifyEngines`, `ocrMaxVerifyRegions`, `ocrVlmTimeoutS`.

**Die Allowlist-Falle (hat dieses Projekt schon einmal gebissen, wird es
wieder tun):** Ein Schlüssel, der nur in `DEFAULT_SETTINGS` steht, aber
NICHT in `SETTINGS_KEYS`, wird beim allernächsten Speichern still
verworfen – kein Fehler, keine Warnung, der Wert ist nach dem nächsten
`POST`/`PATCH /api/v1/settings` einfach wieder weg. Jeder neue
Einstellungs-Schlüssel muss in **beide** Strukturen eingetragen werden.
Regressionstest: `tests/test_http_api.py::test_new_ocr_settings_survive_round_trip`.

---

## Tech-Stack

| Schicht | Technologie | Zweck |
|---------|-------------|-------|
| Server | `tool_server.py` (Python-Stdlib `http.server`) | Static + `/api/v1/*`, DSGVO-Filter, Skill-Router, Streaming |
| Core-Bibliothek | `teacherassist_core/` | Privacy-Klassifikation, Security (Session/CSRF/SSRF), Runtime-Pfade & Credentials, verschlüsselter State, Skill-Registry |
| Frontend-Build | Vite 8 + React 18 (`package.json`, `vite.config.js`) | Baut `src/main.jsx` + `app.jsx`/`components.jsx`/`tweaks-panel.jsx` zu `web_dist/` |
| Frontend-Rendering | `react-markdown` + `rehype-sanitize` | Sicheres Markdown-Rendering im Chat |
| API-Client | `api-client.js` | CSRF-Bootstrap gegen `/api/v1/bootstrap`, Alias-Mapping alter Pfade → `/api/v1/*` |
| PDF-Parsing | `pypdf`, `pypdfium2` | Text-PDFs (Lehrpläne) |
| OCR | `pytesseract` + `Pillow` | Gescannte PDFs / Fotos von Schülerarbeiten |
| Vektorspeicher | `chromadb` (lokal) | Lehrplan-Einträge semantisch durchsuchbar (RAG) |
| Embeddings | `sentence-transformers` | Lokal, kein API-Call |
| Secrets | `keyring` (Windows Credential Manager) | API-Keys, Fernet-Datenschlüssel |
| Verschlüsselung | `cryptography` (Fernet) | Chat-/Profil-State at rest |
| Passwort-Hashing | `argon2-cffi` | (falls für zukünftige Auth-Erweiterung benötigt) |
| Export | `python-docx`, `docx2pdf`, `reportlab` | Bewertungen/Wortgutachten als DOCX/PDF |
| LLM-Provider | OpenRouter (Cloud) / Ollama (lokal, `:11434`) / Custom-Endpoint | Modellwahl in den Einstellungen |
| Tests | `pytest` | `tests/*.py`, Venv unter `tools/.venv` |

**Kein Anthropic-API-Key-Feld.** Provider sind OpenRouter, Ollama oder ein
selbst konfigurierter Custom-Endpoint (OpenAI-kompatibel).

---

## Projektstruktur (aktuell)

```
TeacherAssist/
├── CLAUDE.md                       ← Diese Datei
├── README.md                       ← Schnelleinstieg für Lehrer
├── SETUP.md                        ← Entwickler-/Technik-Setup
│
├── tool_server.py                  ← Einziger Server (Port 8789)
├── teacherassist_core/             ← Gehärtete Kernbibliothek
│   ├── privacy.py                  ← Fail-closed DSGVO-Klassifikation (decide_privacy)
│   ├── security.py                 ← Session/CSRF, Host-/Origin-Validierung, SSRF-Schutz
│   ├── runtime.py                  ← RuntimePaths, SettingsStore, CredentialStore
│   ├── storage.py                  ← EncryptedStateStore (Fernet, Chats + Profil)
│   ├── skills.py                   ← SkillRegistry (validiert gegen skills_index.json)
│   ├── documents.py                ← PDF-Download/-Extraktion (SSRF-sicher)
│   └── ocr/                        ← Konsens-OCR-Pipeline + Freigabe-Gate,
│                                      siehe docs/architektur.md
│
├── index.html, src/main.jsx        ← Vite-Entry-Point
├── app.jsx, components.jsx,        ← Anwendungscode (window-global, per <script>
│   tweaks-panel.jsx                  dynamisch importiert aus src/main.jsx)
├── api-client.js                   ← CSRF-Bootstrap + Legacy-Pfad-Aliase
├── package.json, vite.config.js    ← Frontend-Build (→ web_dist/)
├── web_dist/                       ← Gebauter Frontend-Output, **committed**
│                                      (Node.js nur nötig, wenn web_dist/ fehlt)
│
├── install.bat                     ← Erstinstallation: Python-venv, Tesseract,
│                                      npm-Build (übersprungen falls web_dist/ existiert)
├── start.bat                       ← Startet tool_server.py (HTTP `/api/v1/health`-
│                                      Probe, Zombie-Kill, Venv-Zwang)
├── repair.bat                      ← Reinstalliert aus tools/requirements.lock
│
├── skills/                         ← Markdown-Skills (LLM-Instruktionen, kein Code)
│   └── <name>/skill.md
├── skills_index.json               ← Skill-Registrierung (name, folder, triggers)
│
├── tools/                          ← Aktive Python-Hilfsmodule
│   ├── student_store.py            ← Schülerdaten-Verwaltung
│   ├── document_export.py          ← DOCX/PDF-Export
│   ├── usage_tracker.py            ← Token-/Kosten-Tracking
│   ├── requirements.txt            ← Pip-Abhängigkeiten (ungepinnt-kompatibel)
│   ├── requirements.lock           ← Pip-Freeze der aktuellen .venv (für repair.bat)
│   └── .venv/                      ← Projekt-Venv (gitignored, von install.bat angelegt)
│
├── memory/                         ← Markdown-Templates (werden beim ersten Start
│                                      nach %LOCALAPPDATA%\TeacherAssist\memory kopiert)
├── tests/                          ← pytest-Suite
├── conftest.py                     ← Fügt Repo-Root zu sys.path hinzu
├── scripts/
│   ├── create_shortcut.ps1         ← Desktop-Verknüpfung (von install.bat aufgerufen)
│   ├── capability_check.py         ← Prüft installierte optionale Abhängigkeiten
│   └── generate-service-worker.mjs ← Erzeugt web_dist/service-worker.js mit
│                                      Content-Hash-Precache-Liste
└── docs/
    ├── architektur.md
    ├── deployment.md
    └── datenschutz.md
```

**Entfernt (siehe `archive/mobile-clients`-Branch für Historie):** `app/` (Flutter),
`app_ios/` (Swift), `files/` (Duplikat), mobile CI-Configs (`codemagic.yaml`,
`project.yml`, `export_options.plist`), sowie die alte `tools/`-CLI-Schicht
(`memory_reader.py`, `memory_writer.py`, `pdf_reader.py`, `ocr_reader.py`,
`lehrplan_indexer.py`, `lehrplan_searcher.py`, `image_receiver.py`) – `tool_server.py`
ruft diese nicht mehr auf, sondern nutzt `teacherassist_core` und direkte
Lazy-Imports (`pytesseract`, `chromadb`, `pypdf`/`pypdfium2`) im selben Prozess.

---

## HTTP-API-Referenz (`tool_server.py`)

Alle Endpunkte liegen unter `/api/v1/*` und erfordern (ausser den `PUBLIC_PATHS`
`/api/v1/health` und `/api/v1/bootstrap`) eine gültige Session: Cookie
`ta_session` + Header `X-CSRF-Token`, ausgestellt von `/api/v1/bootstrap`.
Zusätzlich prüft `_authorize()` den `Host`-Header (nur `localhost`/`127.0.0.1`/`[::1]`)
und blockiert Cross-Site-Requests (`Sec-Fetch-Site: cross-site`).

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/`, `/index.html`, `/app.jsx`, `/components.jsx`, `/tweaks-panel.jsx`, `/api-client.js`, `/manifest.json`, `/service-worker.js`, `/favicon.ico`, `/teacherassist.ico`, `/assets/*` | Statische Frontend-Dateien (bevorzugt aus `web_dist/`) |
| GET | `/api/v1/health` | Status-Check (öffentlich) |
| GET | `/api/v1/bootstrap` | Session/CSRF erstellen, Settings/Capabilities/Skills/State liefern (öffentlich) |
| GET | `/api/v1/settings` | Öffentliche Settings (ohne Secrets) |
| GET | `/api/v1/collections` | Anzahl ChromaDB-Chunks |
| GET | `/api/v1/backup` | Memory-Verzeichnis als ZIP |
| GET | `/api/v1/rasters` | Bewertungsraster auflisten |
| GET | `/api/v1/memory-list`, `/memory-read`, `/memory-versions` | Memory-Dateien lesen/versionieren |
| GET | `/api/v1/search?q=...` | Semantische Lehrplan-Suche (RAG) |
| GET | `/api/v1/chats`, `/api/v1/chats/{id}` | Chat-Liste / einzelner Chat |
| GET | `/api/v1/profile` | Lehrerprofil lesen |
| GET | `/api/v1/exports/{filename}` | Export-Datei herunterladen |
| GET | `/api/v1/ocr/jobs` | OCR-Jobs auflisten |
| GET | `/api/v1/ocr/jobs/{id}` | OCR-Job-Status/-Ergebnis abrufen (Transkript-Text erst nach Freigabe, siehe `docs/architektur.md`) |
| GET | `/api/v1/ocr/jobs/{id}/pages/{n}` | Seiten-PNG eines OCR-Jobs (optional `?region=` für eine Region) |
| POST | `/api/v1/chat` | LLM-Chat, SSE-Streaming, DSGVO-Routing |
| POST | `/api/v1/upload`, `/api/v1/ingest` | PDF hochladen / in ChromaDB indexieren (mit Klassifikation `public_curriculum`/`personal`/`unknown`) |
| POST | `/api/v1/clear` | Wissensdatenbank leeren |
| POST | `/api/v1/download-url` | Lehrplan per URL holen (SSRF-geprüft) |
| POST | `/api/v1/settings` (auch PATCH) | Einstellungen speichern |
| POST | `/api/v1/export-file` | Datei exportieren (md/txt/html) |
| POST | `/api/v1/save-raster` | Bewertungsraster speichern |
| POST | `/api/v1/restore` | Backup aus ZIP wiederherstellen |
| POST | `/api/v1/memory-write`, `/memory-restore-version` | Memory-Datei schreiben/zurücksetzen |
| POST | `/api/v1/ollama-pull` | Ollama-Modell nachladen |
| POST | `/api/v1/shutdown` | Server beenden |
| POST | `/api/v1/ocr-image` | Bild per OCR in Text umwandeln |
| POST | `/api/v1/session-summary`, `/api/v1/chats/{id}/summary` | Chat-Verlauf zusammenfassen |
| POST | `/api/v1/chats` | Neuen Chat anlegen |
| POST | `/api/v1/chats/{id}/messages` | Nachricht senden (streamt Antwort) |
| POST | `/api/v1/ocr/jobs` | Neuen OCR-Job aus Bild/PDF anlegen (Konsens-Pipeline) |
| POST | `/api/v1/ocr/jobs/{id}/approve` | OCR-Job freigeben (Freigabe-Gate, siehe `docs/architektur.md`) |
| POST | `/api/v1/ocr/models/download` | OCR-Modell (HTR/VLM) nachladen |
| POST/PATCH | `/api/v1/profile` | Lehrerprofil setzen |
| PATCH | `/api/v1/state` | Gesamten State ersetzen (Browser-Migration) |
| PATCH | `/api/v1/ocr/jobs/{id}/regions/{regionId}` | Einzelne Region einer Abschrift korrigieren |
| POST | `/api/v1/migration/browser-state` | Alten Browser-`localStorage`-State importieren |
| DELETE | `/api/v1/chats/{id}` | Chat löschen |
| DELETE | `/api/v1/ocr/jobs/{id}` | OCR-Job löschen |

Quelle der Wahrheit ist der Routing-Block in `tool_server.py` (`do_GET` / `do_POST` /
`do_PATCH` / `do_DELETE`). Bei Änderungen diese Tabelle synchron halten.

`api-client.js` mappt alte Pfade (`/health`, `/chat`, `/settings`, …) transparent auf
`/api/v1/*` und hängt automatisch Cookie/CSRF-Header an – das Frontend selbst
referenziert grösstenteils noch die alten, kurzen Pfade.

---

## DSGVO-Modell-Routing (fail-closed, in `teacherassist_core/privacy.py`)

Die Entscheidung "Cloud erlaubt oder lokales Modell erzwungen" trifft
`decide_privacy()` **serverseitig**, nicht im Frontend – sie kann von der UI nicht
umgangen werden.

```python
def decide_privacy(*, messages, profile=None, skill_id=None,
                    requested_mode="auto", sticky_mode="auto",
                    document_classifications=(), rag_context=None) -> PrivacyDecision:
    ...
```

`local_required` wird `True`, sobald **irgendeiner** dieser Gründe zutrifft:
- Nutzer oder Chat hat explizit lokal angefordert (`requested_mode`/`sticky_mode`).
- `skill_id` ist ein DSGVO-Pflicht-Skill (`SENSITIVE_SKILLS`: `schuelerarbeit_bewerten`,
  `zeugnis_formulieren`, `foerderplan_erstellen`, `lerntagebuch_feedback`,
  `klassenstatistik`).
- Ein eingebundenes RAG-Dokument ist NICHT als `public_curriculum` klassifiziert
  (`document_classifications`, gesetzt beim `/api/v1/ingest`).
- Regex-Treffer (`PERSONAL_PATTERNS`: E-Mail, Telefon, Geburtsdatum,
  Schüler-Kontextwörter, Namen-Muster, Schülerkennungen) in Nachrichten, Profil
  oder RAG-Kontext.

Bei `local_required=True`: Server routet auf Ollama (`:11434`) oder einen als
loopback validierten Custom-Endpoint. Ist keins davon erreichbar, wird **kein**
Cloud-Fallback versucht – der Client bekommt einen Fehler (`LOCAL_MODEL_REQUIRED`).
Zusätzlich wird das an Cloud-Provider gesendete Profil über
`minimize_cloud_profile()` auf eine Allowlist reduziert (`bundesland`, `schulform`,
`faecher`, `style_formality`, `style_detail`).

**Wichtig für zukünftige Änderungen:** `search_rag()` in `tool_server.py` muss die
`classification`-Metadaten der ChromaDB-Treffer zurückgeben (nicht hart `"unknown"`
annehmen) – sonst wird jeder RAG-Treffer fälschlich als nicht-öffentlich behandelt
und jeder Chat mit Lehrplan-Kontext auf lokal erzwungen, selbst wenn das indexierte
Dokument als `public_curriculum` eingelesen wurde.

---

## Skills (Markdown-Instruktionen, kein Code)

Skills sind reine Prompt-Bausteine unter `skills/<name>/skill.md`, registriert in
`skills_index.json` (`name`, `folder`, `triggers`). `teacherassist_core.skills.
SkillRegistry` lädt und validiert sie (Skill-IDs müssen `^[a-z_][a-z0-9_]*$`
entsprechen, `skill.md` muss existieren).

Es gibt **keinen** Tool-Call-/Subprozess-Mechanismus mehr (kein OpenClaw). Der
passende Skill wird per Trigger-Match (`SkillRegistry.match()`) gefunden und sein
Markdown-Inhalt direkt in den System-Prompt injiziert (`_stream_chat_payload` →
`stream_llm`). Das `begleiter`-Skill (Mila-Charakter) wird zusätzlich bei jedem
lokal-erzwungenen Gespräch injiziert (`SKILL_REGISTRY.companion_prompt()`).

Aktive Skills: `onboarding`, `unterricht_planen`, `bewertung_erstellen`,
`arbeitsblatt_erstellen`, `pruefung_erstellen`, `elternbrief_schreiben`,
`zeugnis_formulieren`, `foerderplan_erstellen`, `klassenstatistik`,
`reihenplanung`, `jahresplanung`, `vertretungsstunde`, `lernzielkontrolle`,
`tafelbild_entwerfen`, `klassenrat_protokoll`, `lerntagebuch_feedback`,
`schuelerarbeit_bewerten`, `lehrplan_einlesen`, `methodenrotation`,
`lehrplan_coverage`, `begleiter` (kein User-Trigger, immer aktiv bei lokalem Modus).

---

## Persönlichkeit des Assistenten (Mila)

`build_system_prompt()` in `tool_server.py` injiziert bei jedem Chat einen
festen Persönlichkeits-Block (Name konfigurierbar über `profile.assistant_name`,
Standard „Mila"): warmherzig-kollegialer Ton, Vorschläge statt Anweisungen,
AFB-Verteilung (~30/40/30 % I/II/III) und Zeitangaben-Konventionen für
Stundenentwürfe, keine Schülernamen (SuS-01/SuS-02 statt Klarnamen). Stil lässt
sich über `profile.style_formality` (`locker`/`formal`) und `profile.style_detail`
(`knapp`/`ausführlich`) weiter anpassen.

---

## Installation & Betrieb (Windows – primäres Zielsystem)

```bat
:: 1. Erstinstallation
install.bat
:: Legt tools\.venv an, installiert requirements.txt + Tesseract,
:: baut das Frontend NUR falls web_dist\index.html noch fehlt (sonst
:: übersprungen – Node.js dann nicht nötig), erstellt Desktop-Verknüpfung.

:: 2. Ollama installieren (Pflicht fuer DSGVO-Skills)
:: https://ollama.com/download
ollama pull gemma3:4b

:: 3. App starten
start.bat
:: Prüft tools\.venv\Scripts\python.exe (kein System-Python-Fallback),
:: probiert HTTP GET /api/v1/health, killt einen hängenden Vor-Prozess
:: auf Port 8789 falls die Probe fehlschlägt, öffnet den Browser.

:: Reparatur bei kaputtem venv:
repair.bat
:: Reinstalliert aus tools\requirements.lock (pip freeze der zuletzt
:: funktionierenden .venv), prüft pip check + capability_check.py.
```

**Status prüfen:**
```powershell
Invoke-WebRequest -Uri http://localhost:8789/api/v1/health -UseBasicParsing -TimeoutSec 3
Get-NetTCPConnection -LocalPort 8789 -State Listen |
  ForEach-Object { Get-Process -Id $_.OwningProcess | Select Id, Path }
Get-Content "$env:LOCALAPPDATA\TeacherAssist\logs\tool_server.log" -Tail 50 -Wait
```

Zombie-Listener (Port belegt, aber `/api/v1/health` antwortet nicht): meist ein mit
System-Python statt Venv gestarteter Prozess, bei dem `chromadb`/`torch`-Imports
hängen. `start.bat` erkennt das selbst und beendet den hängenden Prozess vor dem
Neustart.

---

## Frontend-Entwicklung

```bash
npm install
npm run dev     # Vite-Dev-Server, proxied /api → http://127.0.0.1:8789
npm run build   # → web_dist/ (muss nach Änderungen committed werden –
                 #    Endnutzer bauen das Frontend nicht selbst)
```

`app.jsx`, `components.jsx`, `tweaks-panel.jsx` sind weiterhin der eigentliche
Anwendungscode (window-global, per dynamischem `import()` aus `src/main.jsx`
geladen) – keine eigenständigen Legacy-Dateien. Eine echte Modularisierung in
ESM-Komponenten ist offene technische Schuld, aber keine akute Baustelle.

---

## Wichtige Regeln

### Datenschutz (DSGVO – nicht verhandelbar)
- Schülernamen werden nicht in Memory gespeichert (Standard: anonym, SuS-01/SuS-02).
- Keine personenbezogenen Daten in Cloud-LLM-Calls – durchgesetzt von
  `decide_privacy()`, nicht nur im Frontend.
- Bei erzwungenem lokalem Modus: kein Cloud-Fallback, auch nicht wenn Ollama down ist.
- Alle Memory-/State-Dateien bleiben lokal unter `%LOCALAPPDATA%\TeacherAssist`.

### Sprache & Ton
- Alle Skills und Tool-Ausgaben auf Deutsch, professionell-kollegial.
- Bewertungen immer als „Vorschlag" kennzeichnen.

### Pädagogische Korrektheit
- Lehrplanbezüge ohne Quelle mit `[*]` markieren.
- AFB-Verteilung: ~30 % I / ~40 % II / ~30 % III.
- Zeitangaben: Einstieg max. 10 min, Sicherung min. 5 min.

### Code-Qualität
- Kein Hardcoding von Ports/IPs/API-Keys – über `teacherassist_core.runtime` /
  Umgebungsvariablen.
- Alle Dateizugriffe unter `MEMORY_DIR`/`UPLOAD_DIR`/`EXPORT_DIR` gegen
  Path-Traversal prüfen (`.resolve()` + `.relative_to()`), siehe bestehende
  Handler als Vorlage.
- Neue HTTP-Handler: JSON-Body immer über `self._read_json()` lesen (liefert
  einheitliche `ValueError`/`RequestTooLarge`-Fehlerbehandlung).

---

## Bekannte Stolperstellen

**Start/Betrieb**
- `start.bat`/`repair.bat` müssen bei jeder Routen-Änderung in `tool_server.py`
  synchron gehalten werden (siehe `tests/test_http_api.py` für einen
  Script-Konsistenz-Test gegen genau dieses Risiko).
- Zombie-Listener auf 8789 → siehe Abschnitt *Installation & Betrieb*.

**RAG/DSGVO**
- `search_rag()` muss `classification`-Metadaten durchreichen – siehe Abschnitt
  *DSGVO-Modell-Routing* oben.
- `pypdf`/`pypdfium2` liefert leeren Text bei gescannten PDFs → OCR-Pfad
  (`pytesseract`) greift automatisch in `_ocr_image`/Ingest, aber nur wenn
  Tesseract im PATH ist.

**Frontend**
- `web_dist/` muss nach jeder Änderung an `app.jsx`/`components.jsx`/
  `tweaks-panel.jsx`/`src/main.jsx` neu gebaut (`npm run build`) und committed
  werden – der Server bevorzugt `web_dist/` gegenüber den Repo-Root-Quellen.
- Vite 8 verlangt Node.js ≥ 20.19 oder ≥ 22.12; ältere 20.x-Patch-Versionen bauen
  mit einer Warnung, aber funktionieren.

**Secrets**
- Ohne `keyring`-Backend (z. B. Windows Credential Manager nicht verfügbar)
  werden Secrets nur In-Memory gehalten und gehen bei jedem Neustart verloren –
  `CredentialStore.status()["credentialPersistence"]` zeigt das an.

---

## Weiterführende Docs

- `docs/architektur.md` – Architekturdiagramm
- `docs/deployment.md` – VPS-/Schulserver-Setup (TODO)
- `docs/datenschutz.md` – DSGVO-Checkliste
- `SETUP.md` – Entwickler-Setup (ausführlicher als README.md)
