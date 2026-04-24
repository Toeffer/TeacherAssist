# LehrerAgent

KI-Assistent für Lehrkräfte. Hilft bei Unterrichtsplanung, Bewertungserstellung und Korrekturen – datenschutzkonform und selbst gehostet.

---

## Installation (Windows)

### Was du vorher brauchst

- Einen **Anthropic API-Schlüssel** (kostenlos unter [console.anthropic.com](https://console.anthropic.com/))
- **OpenClaw** installiert auf deinem Computer *(Installationsanleitung: → an dieser Stelle einfügen)*

### Schritt 1 – Dateien herunterladen

Klicke oben rechts auf dieser Seite auf **Code → Download ZIP**, dann entpacke die ZIP-Datei an einen Ort deiner Wahl (z. B. `Dokumente\LehrerAgent`).

### Schritt 2 – Einmalig installieren

Öffne den entpackten Ordner und mache einen **Doppelklick auf `install.bat`**.

Das Programm erledigt automatisch:
- Installation aller benötigten Komponenten
- Einrichtung der Konfiguration
- Abfrage deines API-Schlüssels (du wirst danach gefragt)
- Erstellung einer Verknüpfung auf deinem Desktop

*Der Vorgang dauert ca. 5–10 Minuten. Das Fenster darf nicht geschlossen werden.*

### Schritt 3 – Täglich nutzen

Mache einen **Doppelklick auf "LehrerAgent starten"** auf deinem Desktop.

Der Browser öffnet sich automatisch mit dem Assistenten.

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

**"OpenClaw nicht gefunden":**
OpenClaw muss zuerst installiert werden *(Link → einfügen)*.

**Kein API-Schlüssel:**
Registrierung unter [console.anthropic.com](https://console.anthropic.com/), dort unter „API Keys" einen neuen Schlüssel erstellen.

---

*Technische Dokumentation und Entwickler-Setup: → [SETUP.md](SETUP.md)*
