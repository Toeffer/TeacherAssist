# Tool API Dokumentation

> Schnittstellendokumentation für die Python-Tools des LehrerAgent-Systems
> Version: 1.0.0 | Letzte Aktualisierung: April 2026

## Übersicht

Die Tools (Ebene 2) sind Python-Skripte, die von OpenClaw Skills aufgerufen werden. Sie folgen einem einheitlichen JSON-Input/Output-Format und werden als Subprozesse ausgeführt.

## Aufrufkonvention

```python
# Alle Tools: stdin = JSON-Input, stdout = JSON-Output, stderr = Fehler
# OpenClaw ruft auf: python tools/tool_name.py '{"param1": "value1"}'
import sys, json
args = json.loads(sys.argv[1])
result = do_something(args)
print(json.dumps(result))
```

## Tool-Liste

### 1. `memory_reader.py`

**Zweck:** Liest Memory-Dateien im OpenClaw-Memory-Verzeichnis.

**Input:**
```json
{
  "filepath": "lehrerprofil.md",
  "section": "Persönliche Angaben",
  "key": "Bundesland"
}
```

**Parameter:**
- `filepath` (string, erforderlich): Relativer Pfad zu Memory-Datei
- `section` (string, optional): Nur diesen ##-Abschnitt zurückgeben
- `key` (string, optional): Nach "- **Key:** Value"-Einträgen suchen

**Output:**
```json
{
  "success": true,
  "content": "Bayern",
  "exists": true,
  "error": null
}
```

**Fehlerfälle:**
- Datei existiert nicht: `exists: false`, `content: ""`
- Section nicht gefunden: `content: ""`
- Key nicht gefunden: `content: ""`

---

### 2. `memory_writer.py`

**Zweck:** Schreibt Memory-Dateien strukturiert.

**Input:**
```json
{
  "filepath": "lehrerprofil.md",
  "mode": "update_section",
  "content": "# Neue Inhalte\n\nHier steht Text.",
  "section": "Persönliche Angaben"
}
```

**Parameter:**
- `filepath` (string, erforderlich): Relativer Pfad zu Memory-Datei
- `mode` (string, erforderlich): `"overwrite"`, `"append"`, `"update_section"`
- `content` (string, erforderlich): Markdown-Inhalt
- `section` (string, optional): Bei `mode="update_section"`: Abschnittsname

**Output:**
```json
{
  "success": true,
  "filepath": "/home/user/.openclaw/memory/lehrerprofil.md",
  "error": null
}
```

**Modi:**
- `overwrite`: Überschreibt gesamte Datei
- `append`: Hängt Inhalt an Datei an
- `update_section`: Ersetzt/erstellt bestimmten ##-Abschnitt

---

### 3. `pdf_reader.py`

**Zweck:** Liest Text-PDFs (Lehrpläne, die nicht gescannt sind).

**Input:**
```json
{
  "filepath": "/path/to/lehrplan.pdf",
  "pages": [1, 2, 3]
}
```

**Parameter:**
- `filepath` (string, erforderlich): Absoluter Pfad zum PDF
- `pages` (array[int], optional): Nur bestimmte Seiten (1-indexed)

**Output:**
```json
{
  "success": true,
  "text": "Extrahierter Volltext...",
  "page_count": 42,
  "warning": "Warnung: Extrahierter Text ist sehr kurz (45 Zeichen)...",
  "error": null
}
```

**Besonderheiten:**
- Bei Textlänge < 100 Zeichen: `warning` mit Hinweis auf möglichen Scan
- Fallback auf `ocr_reader.py` empfohlen bei Warnung

---

### 4. `ocr_reader.py`

**Zweck:** OCR für gescannte PDFs und Fotos von Schülerarbeiten.

**Input:**
```json
{
  "filepath": "/path/to/schuelerarbeit.jpg",
  "language": "deu"
}
```

**Parameter:**
- `filepath` (string, erforderlich): Absoluter Pfad zu PDF oder Bild
- `language` (string, optional): Tesseract-Sprachcode (default: "deu")

**Output:**
```json
{
  "success": true,
  "text": "OCR-erkannter Text...",
  "confidence": 78.5,
  "warning": "Warnung: OCR-Konfidenz ist niedrig (45.2%)...",
  "error": null
}
```

**Unterstützte Dateiformate:**
- PDF (gescannt)
- JPG, PNG, GIF, BMP, TIFF, WEBP

**Systemabhängigkeiten:**
- Tesseract OCR muss installiert sein
- Deutsch-Sprachpaket: `tesseract-ocr-deu`

---

### 5. `lehrplan_indexer.py`

**Zweck:** Indiziert Lehrplan-Text in ChromaDB für semantische Suche.

**Input:**
```json
{
  "text": "Volltext des Lehrplans...",
  "metadata": {
    "bundesland": "Bayern",
    "schulform": "Gymnasium",
    "fach": "Mathematik",
    "klasse": "7",
    "quelle": "Kultusministerium Bayern"
  },
  "chunk_size": 500
}
```

**Parameter:**
- `text` (string, erforderlich): Volltext des Lehrplans
- `metadata` (object, erforderlich): Metadaten mit Pflichtfeldern
- `chunk_size` (int, optional): Zeichen pro Chunk (default: 500)

**Pflichtfelder in metadata:**
- `bundesland`
- `schulform`
- `fach`
- `klasse`

**Output:**
```json
{
  "success": true,
  "chunks_indexed": 24,
  "collection": "lehrplan_bayern_gymnasium_mathematik_7_a1b2c3d4",
  "db_path": "/home/user/.openclaw/memory/lehrplan_vectordb",
  "error": null
}
```

**Technische Details:**
- Embedding-Modell: `paraphrase-multilingual-MiniLM-L12-v2`
- Läuft vollständig lokal (DSGVO-konform)
- Chunks mit 50 Zeichen Überlappung

---

### 6. `lehrplan_searcher.py`

**Zweck:** Semantische Suche in indizierten Lehrplänen.

**Input:**
```json
{
  "query": "Bruchrechnung Klasse 7",
  "n_results": 3,
  "filter": {
    "bundesland": "Bayern",
    "fach": "Mathematik",
    "klasse": "7"
  }
}
```

**Parameter:**
- `query` (string, erforderlich): Suchanfrage
- `n_results` (int, optional): Anzahl Ergebnisse (default: 3)
- `filter` (object, optional): Filter nach Metadaten

**Output:**
```json
{
  "success": true,
  "results": [
    {
      "text": "Gefundener Lehrplan-Text...",
      "metadata": {
        "bundesland": "Bayern",
        "schulform": "Gymnasium",
        "fach": "Mathematik",
        "klasse": "7",
        "quelle": "Kultusministerium Bayern",
        "chunk_index": 5,
        "total_chunks": 24,
        "collection": "lehrplan_bayern_gymnasium_mathematik_7_a1b2c3d4"
      },
      "distance": 0.15,
      "similarity_score": 0.85
    }
  ],
  "total_collections_searched": 1,
  "total_results_found": 3,
  "error": null
}
```

**Metriken:**
- `distance`: 0 = perfekte Übereinstimmung, höher = schlechter
- `similarity_score`: 1.0 - distance (für bessere Lesbarkeit)

---

## Fehlerbehandlung

### Allgemeines Fehlerformat
```json
{
  "success": false,
  "error": "Fehlermeldung",
  ... weitere felder je nach tool ...
}
```

### Häufige Fehler
1. **Datei nicht gefunden:** `FileNotFoundError`
2. **Ungültige Parameter:** `ValueError`
3. **Import-Fehler:** `ImportError` (fehlende Abhängigkeiten)
4. **System-Fehler:** `RuntimeError` (z.B. Tesseract nicht installiert)

### Debugging
- Alle Tools schreiben Fehler auf `stderr`
- OpenClaw protokolliert Tool-Aufrufe mit Input/Output
- Bei `success: false`: Prüfe `error`-Feld

---

## Integration mit Skills

### Beispiel: Skill ruft Tool auf
```markdown
# In skill.md:
Rufe tool_call("pdf_reader", {"filepath": "{uploaded_file}"}) auf.
Verwende den zurückgegebenen Text für die weitere Verarbeitung.
```

### Datenfluss-Beispiele

**Lehrplan einlesen:**
```
Skill → pdf_reader → (bei Scan) → ocr_reader → lehrplan_indexer → memory_writer
```

**Unterricht planen:**
```
Skill → memory_reader → lehrplan_searcher → (LLM) → memory_writer
```

**Schülerarbeit bewerten:**
```
Skill → ocr_reader → memory_reader → (LLM) → memory_writer
```

---

## Entwicklungshinweise

### Neue Tools erstellen
1. Template kopieren:
```python
#!/usr/bin/env python3
import sys, json

def main():
    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
        # Verarbeitung
        result = {"success": True, "data": "..."}
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        
if __name__ == "__main__":
    main()
```

2. In `requirements.txt` eintragen
3. In dieser Dokumentation dokumentieren

### Testing
```bash
# Manueller Test
python tools/pdf_reader.py '{"filepath": "test.pdf"}'

# Integrationstest
python -c "import json; print(json.dumps({'query': 'Test'}))" | python tools/lehrplan_searcher.py
```

---

## Versionierung

- **1.0.0** (April 2026): Initiale Version
- Alle Tools: Rückwärtskompatibilität wird gewahrt
- Neue Parameter: immer optional mit Default-Wert

---

## Support & Fehlerbehebung

### Bekannte Probleme
1. **Tesseract auf Windows:** Pfad muss in `ocr_reader.py` konfiguriert werden
2. **ChromaDB Lock:** Nur ein Prozess kann gleichzeitig schreiben
3. **UTF-8 Encoding:** Immer `encoding='utf-8'` verwenden

### Logging
- Tools loggen auf `stderr`
- OpenClaw sammelt Logs in `~/.openclaw/logs/`
- Bei Problemen: Logs prüfen und `error`-Feld auswerten