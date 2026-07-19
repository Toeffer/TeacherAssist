# LehrerAgent – Technische Setup-Anleitung

> **Für Endnutzer:** Bitte [README.md](README.md) verwenden — dort reicht ein Doppelklick auf `install.bat`.
> Diese Datei richtet sich an Entwickler und technisch versierte Nutzer.

Vollständige manuelle Einrichtung auf einem neuen Rechner. Reihenfolge einhalten.

---

## Voraussetzungen

| Software | Version | Download |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Tesseract OCR | 5.x | https://github.com/UB-Mannheim/tesseract/wiki (Windows) |
| Ollama (optional, Pflicht für DSGVO-Skills) | aktuell | https://ollama.com/download |
| Git | aktuell | https://git-scm.com/ |
| Node.js | 20.19+ oder 22.12+ | https://nodejs.org/ — **nur nötig, wenn du den Frontend-Build selbst neu erzeugen willst**; das Repo enthält bereits einen fertigen Build unter `web_dist/` |

> **Legacy:** Flutter, iOS und OpenClaw werden nicht mehr benötigt. Die früheren
> mobilen Clients sind vollständig entfernt und auf dem Branch
> `archive/mobile-clients` erhalten.

---

## Schritt 1 – Repository klonen

```bash
git clone https://github.com/Toeffer/TeacherAssist.git
cd TeacherAssist
```

---

## Schritt 2 – Python-Umgebung einrichten

`install.bat` erledigt das automatisch (venv unter `tools\.venv`, `pip install -r
tools\requirements.txt`, Tesseract-Installation). Für eine manuelle Einrichtung:

```bat
cd tools
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd ..
```

### Tesseract (Windows)
1. Installer von https://github.com/UB-Mannheim/tesseract/wiki herunterladen
2. Bei der Installation: **Zusatzpaket "German"** anwählen
3. Installationspfad zur PATH-Umgebungsvariable hinzufügen (z. B. `C:\Program Files\Tesseract-OCR\`)

---

## Schritt 3 – Frontend bauen (nur bei Quellcode-Änderungen nötig)

```bash
npm install
npm run build
```

Baut `web_dist/` aus `src/main.jsx` + `app.jsx`/`components.jsx`/`tweaks-panel.jsx`.
`web_dist/` ist committed — wer nur die App nutzen will, braucht diesen Schritt
nicht. `install.bat` überspringt ihn automatisch, wenn `web_dist\index.html`
bereits existiert.

Für Entwicklung mit Hot-Reload:
```bash
npm run dev
```
Startet den Vite-Dev-Server; API-Requests werden zu `http://127.0.0.1:8789` proxied
(siehe `vite.config.js`). `tool_server.py` muss dafür separat laufen (Schritt 4).

---

## Schritt 4 – Tool-Server starten und konfigurieren

`tool_server.py` läuft als einziger Prozess auf Port **8789** und liefert Frontend
und API aus.

```bat
:: Aus dem Projektordner:
start.bat
```

`start.bat` prüft das venv unter `tools\.venv`, probiert `GET /api/v1/health` und
beendet einen hängenden Vor-Prozess auf Port 8789 falls vorhanden. Browser öffnet
sich automatisch.

API-Key und Provider werden in der Web-UI unter *Einstellungen → Provider*
eingetragen. Der API-Key wird im Windows-Anmeldeinformationsspeicher gespeichert
(`keyring`-Paket), nicht als Klartext — nicht-geheime Einstellungen liegen unter
`%LOCALAPPDATA%\TeacherAssist\settings.json`.

**Ollama (optional, Pflicht für DSGVO-Skills):**

```bat
:: nach Installation von https://ollama.com/download
ollama pull gemma3:4b
ollama serve   :: läuft normalerweise automatisch als Hintergrunddienst
```

DSGVO-Pflicht-Skills (`schuelerarbeit_bewerten`, `zeugnis_formulieren`,
`foerderplan_erstellen`, `lerntagebuch_feedback`, `klassenstatistik`) werden
serverseitig zwingend auf Ollama geroutet — ebenso jeder Chat, in dem
personenbezogene Daten erkannt werden oder ein eingelesenes Dokument nicht als
`public_curriculum` klassifiziert wurde. Wenn Ollama offline ist und lokale
Verarbeitung erforderlich ist, gibt die UI eine Fehlermeldung aus — **kein
Cloud-Fallback**.

---

## Schritt 5 – Verbindung testen

```bat
:: Server-Status
curl http://localhost:8789/api/v1/health
:: Erwartet: {"status":"ok","version":"2.0"}
```

Server-Log liegt unter `%LOCALAPPDATA%\TeacherAssist\logs\tool_server.log`
(rotierend, 1 MB × 3).

---

## Schritt 6 – Onboarding (beim ersten Start)

In der Web-UI den Onboarding-Skill starten:
> "Ich möchte den Agenten einrichten"

Der Agent führt durch die Einrichtung des Lehrerprofils. Profil wird
verschlüsselt unter `%LOCALAPPDATA%\TeacherAssist\state.enc` gespeichert.

---

## Tests

```bat
tools\.venv\Scripts\python.exe -m pytest tests\ -v
```

---

## Verzeichnisstruktur nach Setup

Siehe `CLAUDE.md` → Abschnitt *Projektstruktur* für die vollständige,
aktuell gehaltene Übersicht.

---

## Häufige Fehler

| Fehler | Lösung |
|---|---|
| `Python-venv nicht gefunden` (beim Start) | `install.bat` ausführen — legt `tools\.venv` an |
| Browser zeigt „Tool-Server offline" | `%LOCALAPPDATA%\TeacherAssist\logs\tool_server.log` prüfen, `start.bat` neu starten |
| Port 8789 belegt, `/api/v1/health` timeoutet | Stale Prozess — `start.bat` räumt selbst auf |
| `tesseract is not installed` | Tesseract installieren + PATH setzen |
| `chromadb`/`sentence_transformers` ImportError | `tools\.venv\Scripts\pip install -r tools\requirements.txt` |
| DSGVO-Skill schlägt mit „Ollama nicht verfügbar" fehl | Ollama installieren + `ollama serve` läuft? |
| `npm run build` schlägt fehl / Warnung zu Node-Version | Node.js 20.19+ oder 22.12+ installieren |
