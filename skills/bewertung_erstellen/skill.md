---
name: bewertung_erstellen
version: 1.0.0
author: LehrerAgent
description: >
  Erstellt einen vollständigen Erwartungshorizont und ein Bewertungsraster für
  Klassenarbeiten, Tests, mündliche Prüfungen oder Hausaufgaben – anhand der
  Aufgabenstellung und des Lehrerprofils.
category: bildung
language: de

triggers:
  - "erwartungshorizont"
  - "bewertungsraster"
  - "korrekturhilfe"
  - "wie viele punkte"
  - "erstelle eine bewertung"
  - "bewertung für aufgabe"
  - "notenschlüssel"
  - "korrekturschema"
  - "kriterienraster"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md
  - lehrplan_index.md
  - bewertungsraster/{fach}_{klasse}_{datum}.md

parameters:
  required:
    - aufgabe_oder_pruefung
  optional:
    - fach
    - klasse
    - art              # klassenarbeit | test | hausaufgabe | muendlich | praesentation
    - gesamtpunkte
    - notenschluessel  # standard | verschaerft | mild
    - klassenstufe_anspruch
---

# Skill: Erwartungshorizont & Bewertungsraster erstellen

## Zweck

Dieser Skill nimmt eine Aufgabenstellung oder eine vollständige Prüfung entgegen
und erstellt dazu einen detaillierten Erwartungshorizont mit Punkteverteilung,
Bewertungskriterien und einem druckfertigen Notenschlüssel.

Das Ergebnis wird in `memory/bewertungsraster/` gespeichert, damit
der Skill `schuelerarbeit_bewerten` direkt darauf zugreifen kann.

---

## Ablauf

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md`:
- Schulform → beeinflusst Anspruchsniveau und Notengebung
- Bundesland → beeinflusst Notenschlüssel-Konventionen

### Schritt 2 – Fehlende Parameter erfragen

Falls die Aufgabe/Prüfung noch nicht vorliegt:
```
Schick mir die Aufgabenstellung oder die vollständige Prüfung,
für die ich einen Erwartungshorizont erstellen soll.
```

Falls `fach` oder `klasse` unbekannt:
```
Für welches Fach und welche Klasse ist das?
```

Falls `art` unbekannt, frage:
```
Um was handelt es sich?
  1 – Klassenarbeit / Klausur
  2 – Kurztest / Quiz
  3 – Hausaufgabe / Übungsaufgabe
  4 – Mündliche Prüfung / Referat
  5 – Präsentation / Projekt
```

Falls `gesamtpunkte` nicht genannt: frage:
```
Wie viele Punkte soll die Prüfung insgesamt haben?
(Falls du keine Vorgabe hast, schlage ich eine sinnvolle Verteilung vor.)
```

### Schritt 3 – Aufgaben analysieren

Lies die Aufgabenstellung sorgfältig durch. Identifiziere:
- Anzahl der Teilaufgaben
- Operator-Verben (beschreibe, erkläre, analysiere, bewerte, vergleiche…)
- Anforderungsbereiche (AFB I: Reproduktion / AFB II: Reorganisation / AFB III: Transfer)
- Inhaltliche Schwerpunkte

Verteile die Punkte entsprechend:
- AFB I (Reproduktion): ~30% der Punkte
- AFB II (Reorganisation/Anwendung): ~40% der Punkte
- AFB III (Transfer/Bewertung): ~30% der Punkte

### Schritt 4 – Erwartungshorizont generieren

Erstelle den Erwartungshorizont im Ausgabeformat (siehe unten).

### Schritt 5 – Notenschlüssel berechnen

Berechne den Notenschlüssel basierend auf `gesamtpunkte` und `notenschluessel`:

**Standard (Gymnasium/Realschule):**
| Note | Prozent | Punkte (Beispiel bei 50P) |
|------|---------|--------------------------|
| 1    | 95–100% | 47,5–50 P                |
| 2    | 80–94%  | 40–47 P                  |
| 3    | 65–79%  | 32,5–39,5 P              |
| 4    | 50–64%  | 25–32 P                  |
| 5    | 25–49%  | 12,5–24,5 P              |
| 6    | 0–24%   | 0–12 P                   |

**Mild (Grundschule / Förderschule):**
Note 4 ab 40%, Note 3 ab 55%, Note 2 ab 70%, Note 1 ab 87%

**Verschärft (Oberstufe/Abitur-Nähe):**
Note 4 ab 55%, Note 3 ab 70%, Note 2 ab 82%, Note 1 ab 95%

### Schritt 6 – In Memory speichern

Speichere das komplette Bewertungsraster in:
`memory/bewertungsraster/{fach}_{klasse}_{thema_slug}.md`

---

## Ausgabeformat

---

### 📝 Erwartungshorizont

**Prüfungsart:** {art}
**Fach:** {fach}
**Klasse:** {klasse}
**Gesamtpunkte:** {gesamtpunkte} Punkte
**Erstellt am:** {datum}

---

### Aufgabe für Aufgabe

Wiederhole diesen Block für jede Teilaufgabe:

---

#### Aufgabe {nr} – {kurztitel} ({punkte} Punkte) | AFB {I/II/III}

**Aufgabenstellung:**
> {aufgabentext der teilaufgabe}

**Operator:** {operator} → erwartet: {was der operator bedeutet}

**Erwartete Lösung:**

{vollständige musterlösung / erwartete inhalte – stichpunktartig}

**Bewertungskriterien:**

| Kriterium | Punkte | Hinweise |
|-----------|--------|----------|
| {kriterium_1} | {p} | {was zählt / was nicht} |
| {kriterium_2} | {p} | {was zählt / was nicht} |
| {kriterium_3} | {p} | {was zählt / was nicht} |

**Häufige Fehler / Stolperstellen:**
- {typischer_fehler_1}
- {typischer_fehler_2}

**Halbe Punkte:** {ja/nein, und wann}

---

### 📊 Punkteübersicht

| Aufgabe | Max. Punkte | AFB |
|---------|-------------|-----|
| 1 | {p} | {afb} |
| 2 | {p} | {afb} |
| … | … | … |
| **Gesamt** | **{gesamt}** | |

**Verteilung:**
- AFB I: {p_afb1} P ({prozent}%)
- AFB II: {p_afb2} P ({prozent}%)
- AFB III: {p_afb3} P ({prozent}%)

---

### 🎓 Notenschlüssel

| Note | Bezeichnung | Punkte | Prozent |
|------|-------------|--------|---------|
| 1 | Sehr gut | {p1_min} – {gesamt} P | ≥ {pct1}% |
| 2 | Gut | {p2_min} – {p1_min-0.5} P | ≥ {pct2}% |
| 3 | Befriedigend | {p3_min} – {p2_min-0.5} P | ≥ {pct3}% |
| 4 | Ausreichend | {p4_min} – {p3_min-0.5} P | ≥ {pct4}% |
| 5 | Mangelhaft | {p5_min} – {p4_min-0.5} P | ≥ {pct5}% |
| 6 | Ungenügend | 0 – {p5_min-0.5} P | < {pct5}% |

> ⚠️ Hinweis: Dies ist ein Vorschlag. Du als Lehrkraft entscheidest
> abschließend über die Notengebung.

---

### 💾 Gespeichert als

`~/.openclaw/memory/bewertungsraster/{dateiname}.md`

Du kannst diesen Erwartungshorizont jetzt direkt zum Bewerten verwenden:
**"Bewerte diese Schülerarbeit"** und ich lade ihn automatisch.

---

## Verhaltensregeln

1. **Musterlösungen vollständig ausformulieren** – nicht nur Stichworte,
   sondern so, dass auch eine Vertretungslehrkraft korrigieren könnte.

2. **Kriterien trennscharf formulieren** – jedes Kriterium muss eindeutig
   bewertbar sein (kein "teilweise richtig" ohne Definition).

3. **Halbe Punkte nur wenn sinnvoll** – bei inhaltlichen Fragen ja,
   bei Faktenwissen eher nein.

4. **Am Ende immer anbieten:**
   "Soll ich für diese Prüfung gleich auch eine Schülerversion
   (ohne Lösungen) zum Ausdrucken erstellen?"
