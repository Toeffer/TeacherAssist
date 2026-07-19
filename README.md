# LehrerAgent

KI-Assistent für Lehrkräfte. Hilft bei Unterrichtsplanung, Bewertungserstellung und Korrekturen – datenschutzkonform und selbst gehostet.

---

## Installation (Windows)

### Was du vorher brauchst

- Einen **OpenRouter API-Schlüssel** (kostenlos unter [openrouter.ai/keys](https://openrouter.ai/keys)) – wird später in den Einstellungen im Browser eingegeben. Alternativ kannst du einen eigenen OpenAI-kompatiblen Endpunkt eintragen.
- *Empfohlen, und Pflicht für datenschutzkritische Aufgaben:* **Ollama** lokal installiert, siehe [ollama.com/download](https://ollama.com/download). Skills wie *Schülerarbeit bewerten* oder *Zeugnis formulieren* werden automatisch über Ollama verarbeitet und verlassen den Rechner nicht – ohne laufendes Ollama schlagen diese Skills mit einer Fehlermeldung fehl (kein Cloud-Fallback).

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

**Beim ersten Start:** API-Schlüssel und Modell in der Web-UI unter *Einstellungen* eintragen. Der Schlüssel wird sicher im Windows-Anmeldeinformationsspeicher hinterlegt, nicht als Klartext auf der Festplatte.

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

Der LehrerAgent läuft vollständig auf **deinem eigenen Computer**. Es werden keine Schülerdaten an Dritte weitergegeben. Anfragen an ein Cloud-Modell (über OpenRouter) verlassen das Gerät nur, wenn keine personenbezogenen Schülerinformationen erkannt wurden – erkennt der Server solche Informationen oder nutzt du einen DSGVO-Pflicht-Skill, wird automatisch und ohne Ausweichmöglichkeit auf ein lokales Ollama-Modell umgeschaltet.

---

## Probleme?

**Installation schlägt fehl:**
Stelle sicher, dass du mit dem Internet verbunden bist und führe `install.bat` nochmal aus.

**Browser zeigt „Tool-Server offline":**
Schliesse das gestartete schwarze Fenster und starte `start.bat` neu. Wenn das nicht hilft: Log unter `%LOCALAPPDATA%\TeacherAssist\logs\tool_server.log` prüfen.

**Kein API-Schlüssel:**
Registrierung unter [openrouter.ai](https://openrouter.ai/), dort unter „Keys" einen neuen Schlüssel erstellen und in der Web-UI unter *Einstellungen → Provider → OpenRouter* eintragen.

**Lokales Modell für DSGVO-Aufgaben:**
Für Schülerarbeiten, Zeugnisse, Förderpläne, Klassenstatistiken und Lerntagebuch-Feedback wird ein lokales Modell erzwungen. [Ollama installieren](https://ollama.com/download) und z. B. `ollama pull gemma3:4b` ausführen.

---

*Technische Dokumentation und Entwickler-Setup: → [SETUP.md](SETUP.md)*
