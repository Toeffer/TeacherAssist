# Architektur - LehrerAssistent

## Ein Prozess, ein Port

`tool_server.py` ist der einzige Server, auf Port `8789`. Er liefert sowohl das
gebaute Frontend (`web_dist/`, per `npm run build` erzeugt und committed) als auch
alle `/api/v1/*`-Endpunkte aus. Es gibt keinen zweiten Webserver und keinen
separaten Port für die UI.

## Kernbibliothek

Sicherheits- und Datenschutz-kritische Logik ist von der HTTP-Schicht getrennt in
`teacherassist_core/`:

- `security.py` – Session-/CSRF-Verwaltung, Host-/Origin-Validierung, SSRF-sichere
  URL-Prüfung für ausgehende Requests (Lehrplan-Download, Custom-Endpoint).
- `privacy.py` – Fail-closed-Klassifikation, ob ein Gespräch lokal verarbeitet
  werden muss (`decide_privacy`), plus Profil-Minimierung für Cloud-Requests.
- `runtime.py` – Laufzeitpfade (`RuntimePaths`), nicht-geheime Einstellungen
  (`SettingsStore`), Secrets über den Windows-Anmeldeinformationsspeicher
  (`CredentialStore`).
- `storage.py` – Fernet-verschlüsselter Chat-/Profil-State (`EncryptedStateStore`).
- `skills.py` – Validierte Skill-Registrierung (`SkillRegistry`), lädt
  `skills/*/skill.md` gemäss `skills_index.json`.
- `documents.py` – SSRF-sicherer PDF-Download und Textextraktion.
- `ocr/` – Konsens-OCR-Pipeline für gescannte/fotografierte Schülerarbeiten
  (Engines, Konsensbildung, Freigabe-Gate), siehe eigener Abschnitt unten.

`tool_server.py` bleibt der dünne HTTP-Adapter darüber (Routing, Streaming,
Multipart-Parsing, ChromaDB-Zugriff).

## OCR-Pipeline (`teacherassist_core/ocr/`)

Gescannte oder fotografierte Schülerarbeiten laufen durch eine eigene, von
der HTTP-Schicht getrennte Konsens-Pipeline:

- `types.py` – reine Datenstrukturen (`OCRCandidate`, `Region`, `PageResult`,
  `DocumentResult`, `OCRStatus`) und deren JSON-Serialisierung. Frei von
  schweren Abhängigkeiten.
- `consensus.py` – Tokenisierung, Alignment und Konsensbildung zwischen den
  Engine-Kandidaten (`align`, `build_region`, `render_consensus`,
  `decide_status`).
- `critical_tokens.py` – klassifiziert Diskrepanzen als kritisch (Zahl,
  Einheit, Verneinung, Symbol, Fachbegriff) oder harmlos.
- `markup.py` – parst die Modell-Markup-Sprache (`<uncertain>`, `<deleted>`,
  `<unclear/>`) fail-closed in Klartext plus Strukturinfo.
- `engines/` – Engine-Registry und -Implementierungen (`tesseract.py`,
  `htr.py`, `ollama_vlm.py`, `fake.py`), siehe unten.
- `segmentation.py`, `preprocess.py`, `page_render.py`, `image_quality.py` –
  Bildvorverarbeitung, Regionensegmentierung, Qualitätsmetriken.
- `pipeline.py` – orchestriert Engines pro Region/Seite/Dokument
  (`process_page`, `process_document`, `process_single_image_sync`,
  `process_student_pdf`), inklusive selektiver Verifikation langsamer
  Engines (`verify_engines`).
- `privacy_guard.py` – `assert_local_only`/`CloudBlocked`, siehe
  `docs/datenschutz.md`.
- `pseudonyms.py` – `PseudonymMap`, siehe `docs/datenschutz.md`.
- `gate.py` – `evaluate_grading_gate`, das Freigabe-Gate zwischen OCR und dem
  Bewertungs-Skill.
- `store.py` – `OCRJobStore`: Job-Lebenszyklus, Persistenz unter
  `<datenwurzel>/ocr/`, Aufbewahrung/Purge (`ocrRetentionDays`).

### Engine-Abstraktion und Lazy-Import-Vertrag

`teacherassist_core/ocr/engines/` definiert das `OCREngine`-Protocol
(`base.py`) und eine Factory-Registry (`ENGINE_FACTORIES`) für `tesseract`,
`htr`, `ollama_vlm` (und künftig `paddleocr_vl`).

**Lazy-Import-Vertrag:** `import teacherassist_core.ocr.engines` darf keine
schweren Abhängigkeiten (torch, transformers, pytesseract, PIL, paddle,
numpy) auf Modulebene importieren – `is_available()` prüft nur
`importlib.util.find_spec(...)`, der echte Import steckt ausschließlich im
Körper von `recognize()`/`warmup()` einer konkreten Engine. `tool_server.py`
importiert dieses Paket bei jedem Serverstart, daher muss der Bootstrap-Pfad
schnell bleiben; `tests/test_ocr_engines.py::test_engines_import_without_heavy_deps`
erzwingt den Vertrag mit einem `sys.meta_path`-Blocker.

### Konsens- und Critical-Token-Ansatz

Jede Region wird von mehreren Engines gelesen; `consensus.align()`/
`build_region()` vergleichen die Kandidaten tokenweise und rendern
Abweichungen als sichtbare Markierungen im `consensusText` (niemals im
rohen `selectedText`):

- `[wort?]` – eine Engine las dieses Wort, eine andere nicht.
- `[+wort?]` – eine Engine las dieses Wort zusätzlich.
- `[a|b?]` – die Engines lasen etwas Unterschiedliches.
- `␣?␣` – als unleserlich markierte Stelle (`markup.UNCLEAR_SENTINEL`).

`critical_tokens.classify_span()` entscheidet, ob eine Abweichung *kritisch*
ist (Zahl, Einheit, Verneinung/kritisches Wort, Symbol, Fachbegriff) – nur
kritische Diskrepanzen blockieren die Freigabe (`Region.has_critical_uncertainty`);
harmlose Abweichungen lassen die Region zwar `needs_review`, aber ohne den
Freigabe-Block aus Ebene 1 unten.

### Die drei Ebenen des Freigabe-Gates (in dieser Reihenfolge)

1. **`DocumentResult.to_dict()`** (`teacherassist_core/ocr/types.py`) hält
   den Volltext (`text`/`selectedText`) grundsätzlich zurück, solange
   `status` nicht `APPROVED` ist – nur die Konsens-Markierungen sind immer
   sichtbar. **Das ist die eigentliche Durchsetzung.**
2. **`evaluate_grading_gate()`** (`teacherassist_core/ocr/gate.py`),
   aufgerufen aus `_stream_chat_payload` in `tool_server.py`, lehnt eine
   Bewertungsanfrage mit referenzierten, nicht freigegebenen OCR-Jobs mit
   HTTP 409 ab – **vor** den SSE-Headern, damit der Client den Fehler als
   normale JSON-Antwort sieht statt mitten in einem Stream.
3. **Der Skill-Text** (`skills/schuelerarbeit_bewerten/skill.md`,
   Schritt 2a) erklärt dem Modell die Markierungen und weist es an, bei
   ungeklärter Unsicherheit nicht zu bewerten.

Ebenen 2 und 3 sind Defence in Depth. Ebene 1 ist die einzige Stelle, die
tatsächlich verhindert, dass unfreigegebener Text die Review-UI verlässt –
ein Widerspruch zwischen Ebene 3 und Ebene 1 wird immer zugunsten von
Ebene 1 aufgelöst.

### Gemessene VLM-Laufzeit (Beobachtung, keine Spezifikation)

Auf dieser Maschine, gegen eine lokale Ollama-Instanz mit `qwen3-vl:latest`
(reine CPU-Inferenz), wurde gemessen:

| Eingabe | Ausgabe | Wandzeit |
|---|---|---|
| eine Zeile, 2800×360 px | ~40 Zeichen | 90,6 s |
| 8 Zeilen, 3200×1560 px | ~350 Zeichen | Timeout bei 540 s (nicht fertig geworden) |
| dieselben 8 Zeilen, auf 1024 px herunterskaliert | ~350 Zeichen | Timeout bei 420 s (Herunterskalieren half nicht) |

Die Kosten hängen an der Länge der autoregressiv erzeugten Ausgabe, nicht an
der Eingabegröße. Deshalb läuft die VLM-Engine nicht als Massenleser über
jede Region, sondern nur selektiv zur Verifikation einzelner unsicherer
Regionen (`pipeline.py`: `verify_engines`). Diese Zahlen wurden auf dieser
Maschine mit diesem Modell gemessen und werden auf anderer Hardware oder mit
anderen Modellen abweichen – sie sind eine Beobachtung, keine Spezifikation.

## Datenverzeichnis

Alle veränderlichen Daten (Memory, Uploads, Exports, Logs, ChromaDB,
Einstellungen, verschlüsselter State) liegen unter
`%LOCALAPPDATA%\TeacherAssist\` (überschreibbar per `TEACHERASSIST_DATA_DIR`),
nicht im Repository. Details siehe `teacherassist_core/runtime.py` und
`CLAUDE.md` → Abschnitt *Laufzeit-Datenverzeichnis*.

## Frontend-Build

`src/main.jsx` ist der Vite-Entry-Point; er lädt `app.jsx`, `components.jsx` und
`tweaks-panel.jsx` (weiterhin der eigentliche Anwendungscode, window-global) per
dynamischem `import()`. `npm run build` erzeugt `web_dist/`, das der Server
gegenüber den Repo-Root-Quellen bevorzugt ausliefert. Endnutzer benötigen daher
kein Node.js — der Build ist Teil des Repositorys.

## LLM-Anbindung

`tool_server.py` ruft Provider serverseitig auf (nie direkt vom Browser):

```
tool_server.py ──HTTP──► OpenRouter (Cloud)         – wenn provider=openrouter und Cloud erlaubt
tool_server.py ──HTTP──► Ollama :11434 (lokal)      – wenn provider=ollama oder DSGVO-Pflicht
tool_server.py ──HTTP──► Custom-Endpoint (loopback  – wenn provider=custom
                          oder validierte HTTPS-URL)
```

Ob Cloud erlaubt ist, entscheidet ausschliesslich `decide_privacy()` in
`teacherassist_core/privacy.py` — siehe `CLAUDE.md` für die vollständige Logik.

## Mobile Clients

Frühere iOS- (Swift) und Flutter-Clients sprachen ein WebSocket-Protokoll zu
einem OpenClaw-Gateway auf Port 18789, das nie Teil dieser Architektur wurde.
Die Quellen sind entfernt und auf dem Branch `archive/mobile-clients` erhalten.
