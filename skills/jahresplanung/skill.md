---
name: jahresplanung
version: 1.0.0
author: LehrerAgent
description: Erstellt eine Jahresstoffverteilung für ein Fach und eine Klasse – inklusive Unterrichtsreihen, Klassenarbeitstermine und Pufferzeiträume.
category: bildung
language: de
priority: 11

triggers:
  - "jahresplanung"
  - "stoffverteilung"
  - "jahresübersicht"
  - "schuljahr planen"
  - "was nehme ich wann dran"
  - "planung für das schuljahr"
  - "jahresplan erstellen"
  - "überblick schuljahr"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md
  - lehrplan_index.md

parameters:
  required:
    - fach
    - klasse
  optional:
    - schuljahr
    - anzahl_klassenarbeiten
    - schulwochen_gesamt
    - besondere_termine
---

# Skill: Jahresplanung / Stoffverteilung

## Zweck

Dieser Skill erstellt eine strukturierte Jahresstoffverteilung für ein Fach und eine Klasse.
Er gibt einen realistischen Überblick über Unterrichtsreihen, Zeitrahmen, Klassenarbeitstermine
und einzuplanende Pufferzeiträume (Ausfälle, Feiertage, Projekttage).

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md` → Bundesland, Schulform.
Lade `lehrplan_index.md` → Kompetenzbereiche für `{fach}` + `{klasse}`.
Falls kein Lehrerprofil: Onboarding empfehlen.

### Schritt 2 – Parameter klären

Falls `schulwochen_gesamt` fehlt: Standard = **36 Wochen** (ca. 170–180 Unterrichtsstunden bei 5 Std/Woche).
Falls `anzahl_klassenarbeiten` fehlt: frage nach:
```
Wie viele Klassenarbeiten sind für {fach} in {klasse} vorgeschrieben?
(Schulgesetz / Fachkonferenz-Beschluss)
```
Falls `schuljahr` fehlt: aktuelles Schuljahr annehmen und mit `[*]` markieren.

### Schritt 3 – Lehrplan-Themen strukturieren

Identifiziere alle Themenblöcke/Kompetenzfelder aus dem Lehrplan für dieses Fach und diese Klasse.
Ordne sie didaktisch sinnvoll an:
- Spiralcurriculum berücksichtigen (aufbauend auf Vorjahresklassen)
- Klassenarbeiten strategisch platzieren (nach Abschluss einer Reihe, genug Übungszeit danach)
- Schuljahresbeginn: Wiederholung / Diagnostik einplanen
- Vor Ferien: abgeschlossene Einheiten, keine neuen Kernthemen starten

### Schritt 4 – Jahresplan erstellen

Erstelle den Plan nach dem Ausgabeformat.

### Schritt 5 – In Memory speichern

Speichere Kurzübersicht in `lehrplan_index.md` als neuen Abschnitt:
```markdown
## Jahresplanung {fach} Klasse {klasse} – Schuljahr {schuljahr}
Erstellt: {datum}
{liste der reihen mit ungefähren terminen}
```

---

## Ausgabeformat

---

### 📅 Jahresplanung

**Fach:** {fach}
**Klasse/Jahrgang:** {klasse}
**Schuljahr:** {schuljahr}
**Unterrichtsstunden gesamt:** ca. {stunden_gesamt} Std. ({schulwochen} Wochen × {std_pro_woche} Std.)
**Klassenarbeiten:** {anzahl} (je ca. 45–90 Min, inkl. Besprechung)
**Puffer eingeplant:** ca. {puffer_prozent}% (Ausfälle, Projekttage, Feiertage)
**Effektive Lehrzeit:** ca. {effektive_stunden} Std.

---

### 🗓️ Übersicht nach Halbjahr

#### 1. Halbjahr (ca. {hw1_wochen} Wochen / {hw1_stunden} Std.)

| Zeitraum | Reihe / Themenblock | Std. | KA | Kompetenzbereich |
|----------|---------------------|------|-----|-----------------|
| {zeitraum} | {reihe_1} | {std} | – | {lehrplan_bezug} |
| {zeitraum} | {reihe_2} | {std} | ✏️ KA 1 | {lehrplan_bezug} |
| {zeitraum} | {reihe_3} | {std} | – | {lehrplan_bezug} |
| {zeitraum} | *Puffer / Vertiefung* | {std} | – | |

**Halbjahreszeugnis:** {datum_hw1}

---

#### 2. Halbjahr (ca. {hw2_wochen} Wochen / {hw2_stunden} Std.)

| Zeitraum | Reihe / Themenblock | Std. | KA | Kompetenzbereich |
|----------|---------------------|------|-----|-----------------|
| {zeitraum} | {reihe_4} | {std} | – | {lehrplan_bezug} |
| {zeitraum} | {reihe_5} | {std} | ✏️ KA 2 | {lehrplan_bezug} |
| {zeitraum} | {reihe_6} | {std} | – | {lehrplan_bezug} |
| {zeitraum} | *Puffer / Wiederholung* | {std} | – | |

**Jahreszeugnis:** {datum_hw2}

---

### 📝 Klassenarbeitstermine (Vorschläge)

| KA | Nach Reihe | Vorgeschlagener Zeitraum | Themen |
|----|-----------|--------------------------|--------|
| KA 1 | {reihe_name} | {zeitraum} | {themen_liste} |
| KA 2 | {reihe_name} | {zeitraum} | {themen_liste} |
| *(KA 3)* | {reihe_name} | {zeitraum} | {themen_liste} |

> ⚠️ Klassenarbeitstermine müssen mit der Schulleitung / Jahrgangsstufe abgestimmt werden.

---

### ⚠️ Planungshinweise

**Einzuplanende Ausfälle (Erfahrungswerte):**
- Feiertage: ca. 3–5 Unterrichtsstunden pro Halbjahr
- Projekttage / Wandertage: ca. 2–4 Stunden
- Krankheit / Vertretung: ca. 2–3 Stunden
→ Empfohlener Puffer: **10–15% der Gesamtstunden** nicht verplanen.

**Kritische Zeiträume:**
- Oktober/November: Elternsprechtage, oft Stundenausfall
- Januar/Februar: Zeugnisse, Fachkonferenzen
- Mai/Juni: Prüfungsphase (ggf. andere Klassen übernehmen)

---

### 🔗 Querverbindungen zu anderen Fächern

{falls bekannt: inhaltliche Verbindungen zu anderen Fächern, die die Lehrkraft unterrichtet}
*(z. B. Textanalyse in Deutsch parallel zu Sachquellen in Geschichte)*

---

## Verhaltensregeln

1. **Keine fixen Daten nennen** – nur Zeiträume (z. B. "Ende Oktober"), da Schuljahresbeginn variiert.
2. **Puffer explizit einplanen** – nie 100% der Stunden verplanen.
3. **Lehrplanbezug** – jeden Themenblock einem Kompetenzfeld zuordnen; unklar → `[*]`.
4. **Am Ende fragen:**
   "Soll ich für eine dieser Reihen direkt einen Reihenplan oder
   einzelne Stundenentwürfe erstellen?"
