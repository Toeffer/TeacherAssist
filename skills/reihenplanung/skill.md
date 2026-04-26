---
name: reihenplanung
version: 1.0.0
author: LehrerAgent
description: Plant eine vollständige Unterrichtsreihe (4–8 Stunden) inklusive Kompetenzaufbau, Stundenüberblick, Materialhinweise und eingebettete Lernzielkontrolle.
category: bildung
language: de
priority: 12

triggers:
  - "unterrichtsreihe"
  - "reihenplanung"
  - "plane eine reihe"
  - "mehrere stunden zu"
  - "sequenzplanung"
  - "reihe planen"
  - "unterrichtssequenz"
  - "einheit planen"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md
  - lehrplan_index.md
  - vergangene_stunden.md

parameters:
  required:
    - fach
    - klasse
    - thema
  optional:
    - anzahl_stunden
    - schulwochen
    - schwerpunkt
    - klassenarbeit_am_ende
---

# Skill: Unterrichtsreihe planen

## Zweck

Dieser Skill erstellt eine komplett strukturierte Unterrichtsreihe mit 4–8 Einzelstunden.
Er verbindet Jahresplanung (groß) und Einzelstundenentwurf (klein) zur mittleren Planungsebene.
Jede Stunde enthält Lernziel, Hauptmethode, Materialhinweis und Anknüpfung zur Folgestunde.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md` → Bundesland, Schulform, Fach.
Suche in `lehrplan_index.md` nach `{fach}` + `{klasse}`.
Falls kein Lehrerprofil: verweise auf Onboarding.

### Schritt 2 – Parameter klären

Falls `anzahl_stunden` fehlt: Standard = **6 Stunden**.
Falls `klassenarbeit_am_ende` nicht angegeben: frage kurz nach:
```
Soll am Ende der Reihe eine Klassenarbeit stehen?
```

### Schritt 3 – Didaktische Analyse

Überlege:
- Welche **Voraussetzungen** brauchen die SuS? (Vorwissen)
- Welcher **Kompetenzaufbau** ist sinnvoll? (vom Einfachen zum Komplexen)
- Wo liegt der **Kern der Reihe** (Stunden 3–4)?
- Wie endet die Reihe? (Sicherung, Reflexion, Leistungsfeststellung)

### Schritt 4 – Reihenplan erstellen

Erstelle den Überblick nach dem Ausgabeformat (siehe unten).

### Schritt 5 – In Memory speichern

Füge Kurzeintrag in `vergangene_stunden.md` ein:
```markdown
## Reihe: {fach} Klasse {klasse} – {thema} ({anzahl_stunden} Stunden)
- Geplant: {datum}
- Kompetenz: {hauptkompetenz}
- Klassenarbeit: {ja/nein}
```

---

## Ausgabeformat

---

### 📚 Reihenplanung

**Fach:** {fach}
**Klasse/Jahrgang:** {klasse}
**Thema der Reihe:** {thema}
**Umfang:** {anzahl_stunden} Unterrichtsstunden (à 45 Min)
**Zeitraum:** ca. {schulwochen} Schulwochen

---

### 🎯 Kompetenzziel der Reihe

Die Schülerinnen und Schüler können am Ende der Reihe:
{übergeordnete_kompetenz – konkret, messbar}

**Lehrplanbezug:**
> {lehrplan_kompetenzbereich}, {bundesland} {schulform}, Klasse {klasse}

---

### 🗓️ Stundenübersicht

| Std. | Thema | Lernziel (Die SuS können …) | Methode | Material | Hinweise |
|------|-------|----------------------------|---------|----------|----------|
| 1 | {einstieg_thema} | {lernziel_1} | {methode} | {material} | Vorwissen aktivieren |
| 2 | {aufbau_thema} | {lernziel_2} | {methode} | {material} | |
| 3 | {kern_thema_1} | {lernziel_3} | {methode} | {material} | Kern der Reihe |
| 4 | {kern_thema_2} | {lernziel_4} | {methode} | {material} | Vertiefung |
| 5 | {anwendung_thema} | {lernziel_5} | {methode} | {material} | Transfer + Übung |
| 6 | {abschluss_thema} | {lernziel_6} | {methode} | {material} | Sicherung + Reflexion |

*(Bei Klassenarbeit: Stunde 7 = Klassenarbeit, Stunde 8 = Besprechung)*

---

### 🔗 Didaktischer Roten Faden

**Einstiegsphase (Std. 1–2):** {beschreibung – wie wird Vorwissen aktiviert, Interesse geweckt}

**Erarbeitungsphase (Std. 3–4):** {beschreibung – wie wird der Kern vermittelt, welche Vertiefungen}

**Sicherungsphase (Std. 5–6):** {beschreibung – wie werden Ergebnisse gesichert, was wird bewertet}

---

### 🔀 Differenzierungskonzept für die Reihe

**Leistungsstarke SuS:** {übergreifende Fördermaßnahme für die Reihe}
**Leistungsschwächere SuS:** {übergreifende Unterstützungsmaßnahme}
**DaZ/Förderbedarf:** {sprachsensible Maßnahmen falls relevant}

---

### 📋 Materialübersicht (alle Stunden)

| Stunde | Material | Selbst erstellen / Bereits vorhanden |
|--------|----------|--------------------------------------|
| 1 | {material} | {status} |
| 2 | {material} | {status} |
| 3 | {material} | {status} |
| 4 | {material} | {status} |
| 5 | {material} | {status} |
| 6 | {material} | {status} |

---

### 📝 Leistungsfeststellung

{Falls Klassenarbeit: Hinweis auf pruefung_erstellen-Skill}
{Falls Lernzielkontrolle: Hinweis auf lernzielkontrolle-Skill}
{Falls keine: kurze formative Beobachtungshinweise}

---

## Verhaltensregeln

1. **Kompetenzaufbau** – jede Stunde baut auf der vorherigen auf, kein Sprung ohne Brücke.
2. **Zeitrealismus** – max. 6 neue Konzepte pro Reihe; lieber weniger und tiefer.
3. **Lehrplanbezug** – immer angeben; unklar → mit `[*]` markieren.
4. **Am Ende fragen:**
   "Soll ich einen einzelnen Stundenentwurf, ein Arbeitsblatt oder
   eine Klassenarbeit für diese Reihe erstellen?"
