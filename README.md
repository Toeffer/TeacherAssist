# LehrerAgent

KI-Assistent für Lehrkräfte. Hilft bei Unterrichtsplanung, Bewertungserstellung und Korrekturen – datenschutzkonform und selbst gehostet.

---

## Installation (Windows)

### Was du vorher brauchst

- Einen **Anthropic API-Schlüssel** (kostenlos unter [console.anthropic.com](https://console.anthropic.com/)) – wird später in den Einstellungen im Browser eingegeben.
- *Empfohlen für datenschutzkritische Aufgaben:* **Ollama** lokal installiert, siehe [ollama.com/download](https://ollama.com/download). Skills wie *Schülerarbeit bewerten* oder *Zeugnis formulieren* werden automatisch über Ollama verarbeitet und verlassen den Rechner nicht.

### Schritt 1 – Dateien herunterladen

Klicke oben rechts auf dieser Seite auf **Code → Download ZIP**, dann entpacke die ZIP-Datei an einen Ort deiner Wahl (z. B. `Dokumente\LehrerAgent`).

### Schritt 2 – Einmalig installieren

Öffne den entpackten Ordner und mache einen **Doppelklick auf `install.bat`**.

Das Programm erledigt automatisch:
- Installation von Python und Tesseract (für OCR), falls noch nicht vorhanden
- Anlegen der Python-Umgebung unter `tools\.venv\`
- Erstellung einer Verknüpfung auf deinem Desktop

*Der Vorgang dauert ca. 5–10 Minuten. Das Fenster darf nicht geschlossen werden.*

### Schritt 3 – Täglich nutzen

Mache einen **Doppelklick auf "LehrerAgent starten"** auf deinem Desktop (oder direkt auf `start.bat`).

Der Browser öffnet sich automatisch unter `http://localhost:8789/` mit dem Assistenten.

**Beim ersten Start:** API-Schlüssel und Modell in der Web-UI unter *Einstellungen* eintragen. Die Werte werden lokal in `settings.json` gespeichert.

---

## Was kann der LehrerAgent?

| Funktion | Beispiel |
|---|---|
| **Unterricht planen** | „Plane eine Stunde zum Thema Bruchrechnung für Klasse 7" |
| **Lehrplan einlesen** | PDF des Lehrplans hochladen → wird automatisch indexiert |
| **Bewertungsraster erstellen** | „Erstelle ein Bewertungsraster für eine Erörterung in Klasse 10" |
| **Schülerarbeiten bewerten** | Foto oder Scan hochladen → KI gibt strukturiertes Feedback |
| **Stunden dokumentieren** | Vergangene Stunden werden automatisch protokolliert |

---

## Datenschutz

Der LehrerAgent läuft vollständig auf **deinem eigenen Computer**. Es werden keine Schülerdaten an Dritte weitergegeben. Nur deine Anfragen an das KI-Modell (Claude von Anthropic) verlassen das Gerät – ohne personenbezogene Schülerinformationen.

---

## Probleme?

**Installation schlägt fehl:**
Stelle sicher, dass du mit dem Internet verbunden bist und führe `install.bat` nochmal aus.

**Browser zeigt „Tool-Server offline":**
Schliesse das gestartete schwarze Fenster und starte `start.bat` neu. Wenn das nicht hilft: Log unter `logs\tool_server.log` prüfen.

**Kein API-Schlüssel:**
Registrierung unter [console.anthropic.com](https://console.anthropic.com/), dort unter „API Keys" einen neuen Schlüssel erstellen und in der Web-UI unter *Einstellungen → Provider → Anthropic* eintragen.

**Lokales Modell für DSGVO-Aufgaben:**
Für Schülerarbeiten, Zeugnisse und Förderpläne wird ein lokales Modell erzwungen. [Ollama installieren](https://ollama.com/download) und z. B. `ollama pull gemma3:e4b` ausführen.

---

*Technische Dokumentation und Entwickler-Setup: → [SETUP.md](SETUP.md)*
