# Datenschutz – LehrerAssistent (DSGVO)

> Checkliste für Schulen (TODO)

## Grundsätze

- Schülernamen werden **nicht** in Memory gespeichert (`anonym: true` Standard)
- Keine personenbezogenen Daten in LLM-API-Calls
- Alle Memory-Dateien bleiben lokal auf dem Gerät der Lehrkraft
- Anonymisierung: SuS-01, SuS-02 statt Namen

## Klassifikation `student_submission`

Jedes hochgeladene Dokument/jeder OCR-Job trägt eine Klassifikation aus
`teacherassist_core/privacy.py: DOCUMENT_CLASSIFICATIONS`
(`public_curriculum`, `personal`, `unknown`, `student_submission`). Ein
Scan/Foto einer Schülerarbeit bekommt standardmäßig `student_submission`
(siehe `_create_ocr_job`/`_ocr_image` in `tool_server.py`), und diese
Klassifikation ist die einzige, die in
`CLOUD_FORBIDDEN_CLASSIFICATIONS` steht: `cloud_allowed_for_classification()`
gibt für sie unbedingt `False` zurück. Eine Schülerarbeit kann diese
Klassifikation **nicht** durch Einstellungen, Request-Parameter oder
Skill-Auswahl umgehen und ins Cloud-Routing gelangen – das ist keine
Heuristik, sondern eine feste Zuordnung im Code.

## Code-seitige Durchsetzung: `assert_local_only` / `CloudBlocked`

Jede OCR-Engine, die einen Netzwerk-Socket öffnet, ruft
`teacherassist_core/ocr/privacy_guard.py: assert_local_only()` als
allererste Anweisung auf, noch vor Verbindungsaufbau. Ist die Klassifikation
nicht `public_curriculum` und der Ziel-Endpunkt kein vertrauenswürdiger
Loopback-Endpunkt, wirft die Funktion `CloudBlocked` – das ist der
Code-seitige Block, nicht nur eine Konvention.

Sichtbar wird das je nach Aufrufpfad unterschiedlich:

- **Synchron** (`process_single_image_sync`, direkt aus einem
  HTTP-Request-Handler): `CloudBlocked` schlägt bis in die HTTP-Schicht
  durch und erscheint dem Nutzer als Fehler.
- **Asynchron** (`OCRJobStore._run_job()` auf dem Hintergrund-Worker,
  `store.py`): Es gibt keinen lebenden Call-Stack mehr, der die Exception
  tragen könnte. `store.py` fängt sie deshalb an der Executor-Grenze ab und
  terminiert den Job als `FAILED` mit dem maschinenlesbaren Marker
  `CLOUD_BLOCKED_ERROR_CODE` (`"cloud_blocked"`) in `DocumentResult.error_code`
  – nie als gewöhnlicher `engine_failure`, der bloß `needs_review` ergäbe.
  Der HTTP-Client sieht das als `errorCode: "cloud_blocked"`.

`CloudBlocked` wird innerhalb der Pipeline (`pipeline.py`:
`process_page`/`process_document`) niemals stillschweigend abgefangen – kein
Fallback auf eine andere Engine, kein "catch and continue".

### Risikoklasse: ein lokaler Endpunkt, der selbst weiterleitet

`assert_local_only()` prüft nur die **Endpunkt-URL** – das reicht nicht,
wenn der Dienst an dieser URL selbst ein Proxy ist. Ollama ist so ein Fall:
neben lokal ausgeführten Modellen kann es Modell-Tags mit `-cloud`-Suffix
bedienen (z. B. `qwen3-vl:235b-cloud`), die auf Ollamas eigener gehosteter
Infrastruktur laufen. Der HTTP-Request bleibt dabei auf `127.0.0.1:11434`
– `assert_local_only()` sieht einen vertrauenswürdigen Loopback-Endpunkt
und lässt ihn passieren –, aber Ollama leitet Bild und Prompt danach an
einen entfernten Rechner weiter. Für eine `student_submission` würde das
bedeuten, dass eine Schülerarbeit unbemerkt das Gerät verlässt, obwohl die
Endpunkt-Prüfung grün ist.

`teacherassist_core/ocr/engines/ollama_vlm.py: _is_remote_model()` schließt
diese Lücke unabhängig von `assert_local_only()`: Modell-Tags, die einen der
in `REMOTE_MODEL_MARKERS` gelisteten Marker tragen, werden in
`_resolve_vision_model()` **vor** jeder Präfix-Prüfung aus der
Kandidatenmenge entfernt, sobald die Klassifikation Cloud-Zugriff verbietet
– auch wenn das betreffende Tag explizit über `ocrVisionModel` konfiguriert
wurde. Bleibt dadurch kein nutzbares Modell übrig, wirft die Engine
`EngineError("remote_model_forbidden:<tag>")`, statt still auf das
Cloud-Tag auszuweichen; `status()` spiegelt dieselbe Ablehnung
(`available=False`, derselbe `reason`), damit die Settings-UI das anzeigt,
statt einen grünen Haken für eine Engine zu zeigen, die zur Laufzeit
verweigert.

**Für die nächste Engine, die einen Netzwerk-Endpunkt anspricht:** Prüfe
nicht nur, ob der Endpunkt selbst lokal ist, sondern auch, ob der Dienst an
diesem Endpunkt Betriebsmodi kennt, die die Anfrage an einen Drittanbieter
oder eine gehostete Infrastruktur weiterreichen (Modell-Auswahl,
Backend-Flag, Routing-Header o. Ä.). Eine Endpunkt-Prüfung allein reicht
nur, wenn der Endpunkt garantiert kein Proxy ist.

## Schülerarbeiten und ChromaDB

Schülerarbeiten laufen ausschließlich durch die OCR-Job-Pipeline
(`teacherassist_core/ocr/`, `OCR_JOBS`/`OCRJobStore`) und werden dort unter
`<datenwurzel>/ocr/` gespeichert (siehe unten). Sie berühren **niemals**
ChromaDB: Die einzige Stelle, die Inhalte in ChromaDB schreibt, ist
`/api/v1/ingest` (Lehrplan-PDFs, `public_curriculum`/`personal`/`unknown`),
und im gesamten `teacherassist_core/ocr/`-Paket gibt es keinen Import von
`chromadb` oder Embeddings. Eine Schülerarbeit landet also weder als
Rohtext noch als Embedding in der semantisch durchsuchbaren
Wissensdatenbank.

## Scan-Speicherung, Aufbewahrung und Purge

OCR-Jobs (Seiten-PNGs, Kandidatentexte, Metadaten) liegen unter
`<datenwurzel>/ocr/` (`RuntimePaths.ocr`, siehe `teacherassist_core/runtime.py`
und `CLAUDE.md` → *Laufzeit-Datenverzeichnis*) – also demselben, nicht im
Repo liegenden Datenwurzelverzeichnis wie Memory, Uploads und der
verschlüsselte State.

Zwei Einstellungen steuern die Aufbewahrung:

- `ocrRetentionDays` (Standard `7`) – Jobs, deren `created_at` älter als
  diese Anzahl Tage ist, werden bei jedem Serverstart per
  `OCRJobStore.purge_expired()` entfernt (`shutil.rmtree` auf den
  Job-Ordner). Zusätzlich fegt `purge_expired()` verwaiste Ordner mit, die
  in keinem Cache-Eintrag stecken (z. B. ein beim Start als kaputt
  übersprungenes `job.json`) – ohne diesen zweiten Sweep könnten solche
  Ordner nie entfernt werden.
- `ocrDeleteAfterApproval` (Standard `False`) – als Einstellung registriert
  (`SETTINGS_KEYS`/`DEFAULT_SETTINGS` in `runtime.py`) und rundtrip-getestet
  (`tests/test_http_api.py::test_new_ocr_settings_survive_round_trip`),
  aber **aktuell an keiner Stelle im Code ausgewertet** – kein Handler löscht
  einen Job tatsächlich sofort nach Freigabe. Wer sich auf diese Einstellung
  verlässt, sollte das nicht tun, bis das implementiert ist.

## Pseudonymisierung ist lehrkraft-bestätigt, nicht automatisch

`teacherassist_core/ocr/pseudonyms.py: PseudonymMap.detect()` schlägt
Namenskandidaten in einer Abschrift vor (Namensfeld-Muster, erste Zeile,
`privacy.PERSONAL_PATTERNS`), ersetzt aber **nichts** automatisch.
`pseudonymize()` ersetzt ausschließlich die Namen, die die Lehrkraft explizit
bestätigt hat – nie automatisch alle von `detect()` vorgeschlagenen
Kandidaten.

Der Grund: Eine automatische Ersetzung wäre unzuverlässig (Nachnamen, die mit
Fachvokabular kollidieren, ein OCR-Fehler mitten im Namen selbst) und eine
falsche Ersetzung würde die Abschrift, auf der anschließend die Bewertung
läuft, still korrumpieren – der Fehler würde unbemerkt in die Note
weiterlaufen. Deshalb bestätigt die Lehrkraft jeden Namen einzeln in der UI,
bevor er ersetzt wird; die Ersetzung selbst greift nur an Wortgrenzen, damit
ein bestätigtes "Tim" nicht auch "Timo" oder "Timur" verstümmelt.

## `PseudonymMap` ohne Schlüssel: nur In-Memory

Wie `EncryptedStateStore` (`teacherassist_core/storage.py`) und der
`CredentialStore` (`teacherassist_core/runtime.py`) ist `PseudonymMap`
Fernet-verschlüsselt auf der Platte gespeichert – aber nur, wenn ein
Schlüssel aus dem Windows Credential Manager verfügbar ist
(`raw_key` gesetzt). Ohne Schlüssel (`raw_key=None`) läuft die
Alias-Zuordnung rein im Prozessspeicher weiter und wird **niemals** auf die
Platte geschrieben, weder verschlüsselt noch im Klartext. Es gibt dabei
keinen Fehler und keinen Schreibversuch – der degradierte Zustand zeigt sich
nur daran, dass die Zuordnungsdatei nach einem Prozessende schlicht nicht
existiert. Nach einem Neustart ohne persistente Zuordnung kann `restore()`
Aliase (`SuS-01` etc.) nicht mehr auf echte Namen zurückführen; Aufrufer, die
Aliase in der UI anzeigen, sollten `PseudonymMap.persistent` prüfen und
diesen Zustand der Lehrkraft sichtbar machen.
