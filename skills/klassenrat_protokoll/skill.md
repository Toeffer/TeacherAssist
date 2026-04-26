---
name: klassenrat_protokoll
version: 1.0.0
author: LehrerAgent
description: Unterstützt bei der Vorbereitung und Protokollierung eines Klassenrats – mit Tagesordnung, Gesprächsregeln, Protokollvorlage und Aufgabenliste für die nächste Sitzung.
category: bildung
language: de
priority: 9

triggers:
  - "klassenrat"
  - "klassen rat"
  - "klassenratprotokoll"
  - "protokoll klassenrat"
  - "schülerversammlung"
  - "klassenversammlung"
  - "gesprächskreis klasse"
  - "demokratie in der klasse"
  - "tagesordnung klassenrat"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - klasse
  optional:
    - datum
    - themen
    - letzte_aufgaben
    - modus
---

# Skill: Klassenrat protokollieren

## Zweck

Dieser Skill unterstützt Lehrkräfte bei der strukturierten Vorbereitung und Nachbereitung
eines Klassenrats. Er erstellt:
1. Eine Tagesordnung mit Zeitplanung
2. Gesprächsregeln (für den Aushang)
3. Eine ausfüllbare Protokollvorlage (für SuS-Protokollant/in)
4. Eine Aufgabenliste mit Verantwortlichen für die nächste Sitzung

**Grundprinzip:** Der Klassenrat gehört den SuS – die Lehrkraft moderiert nur,
greift nicht inhaltlich ein und enthält sich.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Sitzung vorbereiten

Falls `themen` nicht angegeben: Standardstruktur anbieten:
1. Nachbesprechung letzter Aufgaben
2. Aktuelles (SuS-Anliegen, Konflikte, Lob)
3. Neues Thema / Planung (z. B. Klassenausflug, Projekt)
4. Aufgabenverteilung

Falls `datum` fehlt: leer lassen (auszufüllen).

### Schritt 2 – Protokollvorlage erstellen

Erstelle eine Vorlage, die eine SuS-Schriftführer/in ausfüllen kann.
Einfache, klare Sprache (Klasse 3–4 anders als Klasse 9–10 anpassen).

### Schritt 3 – Protokoll speichern

Speichere leere Vorlage (oder ausgefülltes Protokoll falls Inhalte angegeben wurden)
optional in Memory.

---

## Ausgabeformat

*(zwei Teile: A = Vorbereitung / B = Protokollvorlage)*

---

### Teil A: Vorbereitung für die Lehrkraft

---

#### 📋 Klassenrat – Vorbereitung

**Klasse:** {klasse}
**Datum:** {datum}
**Dauer:** ca. {dauer} Minuten (empfohlen: 30–45 Min, max. 60 Min)
**Sitzordnung:** Stuhlkreis (alle auf gleicher Höhe)

---

#### 🗓️ Tagesordnung

| # | Punkt | Zeit | Verantwortlich |
|---|-------|------|---------------|
| 1 | Begrüßung + Wahl der Sitzungsleitung | 3 Min | Lehrkraft (1. Mal) / SuS |
| 2 | Protokoll der letzten Sitzung | 5 Min | Protokollant/in |
| 3 | {thema_1} | {t1} Min | {verantwortlich} |
| 4 | {thema_2} | {t2} Min | {verantwortlich} |
| 5 | Aufgabenverteilung + nächstes Datum | 5 Min | Sitzungsleitung |
| 6 | Abschlussrunde (1 Wort wie war die Sitzung?) | 3 Min | alle |

---

#### 📌 Gesprächsregeln (zum Aushängen)

```
Regeln für unseren Klassenrat
━━━━━━━━━━━━━━━━━━━━━━━━━━
✋ Wer reden will, meldet sich.
👂 Wir hören zu, wenn jemand spricht.
💬 Wir reden über Probleme, nicht über Personen.
🤝 Wir suchen gemeinsam Lösungen.
📝 Alles Wichtige wird aufgeschrieben.
🔒 Was im Klassenrat besprochen wird, bleibt im Klassenrat
   (außer es geht jemanden in Gefahr).
```

---

#### 💡 Tipps für die Moderation

- **Lehrkraft hält sich zurück** – nur moderieren, nicht inhaltlich lenken.
- **Redezeit begrenzen** – max. 2 Minuten pro Wortmeldung.
- **Lösungsorientiert** – bei Konflikten immer fragen: „Was wäre eine Lösung?"
- **Abstimmen** – Mehrheitsentscheidungen für weniger wichtige Punkte,
  Konsens für wichtige Entscheidungen anstreben.

---

### Teil B: Protokollvorlage (für SuS-Schriftführer/in)

---

#### 📝 Protokoll – Klassenrat {klasse}

**Datum:** _________________ **Uhrzeit:** _______
**Sitzungsleitung:** _________________________
**Protokoll geführt von:** ___________________
**Anwesend:** ______ von ______ SuS

---

**Nachbesprechung letzte Sitzung:**
*Welche Aufgaben wurden erledigt?*

| Aufgabe | Erledigt? |
|---------|-----------|
| | ☐ ja  ☐ nein |
| | ☐ ja  ☐ nein |

---

**Besprochen heute:**

Punkt 1: ______________________________
Ergebnis / Beschluss: _________________
________________________________________

Punkt 2: ______________________________
Ergebnis / Beschluss: _________________
________________________________________

Punkt 3: ______________________________
Ergebnis / Beschluss: _________________
________________________________________

---

**Aufgaben bis zur nächsten Sitzung:**

| Aufgabe | Wer? | Bis wann? |
|---------|------|-----------|
| | | |
| | | |
| | | |

---

**Nächste Sitzung:** _______________________

**Unterschrift Sitzungsleitung:** ___________
**Unterschrift Protokollant/in:** ___________

---

## Verhaltensregeln

1. **SuS-Eigentum** – Klassenrat ist nicht Lehrerveranstaltung; Inhalt gehört den SuS.
2. **Datenschutz** – Protokolle enthalten keine vertraulichen Einzelfallprobleme mit Namen.
   Bei Konflikten: nur anonymisierte Beschlüsse festhalten.
3. **Altersangepasst** – Sprache und Komplexität an die Klasse anpassen.
4. **Am Ende fragen:**
   "Soll ich die Aufgabenliste aus diesem Protokoll als Erinnerung speichern?"
