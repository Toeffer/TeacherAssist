---
name: unterricht_planen
version: 1.0.0
author: LehrerAgent
description: Plant eine vollständige Unterrichtsstunde anhand des deutschen Lehrplans – inklusive Lernziele, Phasierung, Methoden und Differenzierung.
category: bildung
language: de
priority: 10

triggers:
  - "plane eine stunde"
  - "unterrichtsstunde"
  - "stundenentwurf"
  - "unterricht vorbereiten"
  - "lehrplan"
  - "ich brauche eine stunde zu"
  - "was kann ich mit klasse"
  - "unterrichtsplanung"

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
    - bundesland
    - zeitstunden
    - schwerpunkt
    - differenzierung
    - vorwissen
---

# Skill: Unterrichtsstunde planen

## Zweck

Dieser Skill erstellt einen vollständigen, lehrplankonformen Stundenentwurf für
eine Lehrkraft. Er berücksichtigt das Fach, die Klassenstufe, das Thema sowie
das persönliche Lehrerprofil aus dem Memory.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Kontext aus Memory laden

Lade `lehrerprofil.md` und prüfe:
- Bundesland der Lehrkraft (für Lehrplanbezug)
- Fächer, die sie unterrichtet
- Bevorzugte Methoden oder Notizen aus vergangenen Stunden

Falls kein Lehrerprofil vorhanden: verweise auf Onboarding:
```
Ich sehe, du hast dein Profil noch nicht eingerichtet.
Schreib "start" und ich richte alles in 2 Minuten ein.
```

### Schritt 2 – Fehlende Parameter erfragen

Falls Fach, Klasse oder Thema nicht genannt wurden, frage gezielt nach:
```
Für welches Fach und welche Klasse soll ich die Stunde planen?
Und was ist das Thema der Stunde?
```
Falls `zeitstunden` fehlt, nehme **45 Minuten** als Standard an.

### Schritt 3 – Lehrplanbezug herstellen

Suche in `lehrplan_index.md` nach dem passenden Lehrplaneintrag für:
`{fach}` + `{klasse}` + `{bundesland}`

Falls kein Eintrag vorhanden: formuliere plausiblen Lehrplanbezug basierend
auf deutschen Bildungsstandards und markiere ihn mit `[*]` als nicht verifizierten Bezug.
Empfehle: "Für einen echten Lehrplanbezug schreib: 'Lehrplan einlesen'"

### Schritt 4 – Stundenentwurf erstellen

Erstelle den Entwurf im Ausgabeformat (siehe unten).

### Schritt 5 – In Memory speichern

Hänge Zusammenfassung an `vergangene_stunden.md`:

```markdown
## {datum} – {fach} Klasse {klasse}: {thema}
- Lernziel: {hauptlernziel}
- Methoden: {verwendete_methoden}
- Feedback nach der Stunde: (bitte nach dem Unterricht ergänzen)
```

---

## Ausgabeformat

---

### 📋 Stundenentwurf

**Fach:** {fach}
**Klasse/Jahrgang:** {klasse}
**Thema:** {thema}
**Zeitrahmen:** {zeitstunden} Minuten
**Datum:** (wird von Lehrer eingetragen)

---

### 🎯 Lernziele

**Hauptlernziel:**
Die Schülerinnen und Schüler können {konkrete_kompetenz} anhand von {methode/material}.

**Teilziele:**
- Die SuS **kennen** … (Wissen)
- Die SuS **verstehen** … (Verstehen)
- Die SuS **können anwenden** … (Anwenden)

**Lehrplanbezug:**
> {lehrplan_kompetenzbereich}, {bundesland} {schulform}, Klasse {klasse}

---

### ⏱️ Phasierung

| Phase | Zeit | Inhalt | Sozialform | Material |
|-------|------|--------|------------|----------|
| Einstieg | {t1} min | {beschreibung} | {sozialform} | {material} |
| Erarbeitung I | {t2} min | {beschreibung} | {sozialform} | {material} |
| Erarbeitung II | {t3} min | {beschreibung} | {sozialform} | {material} |
| Sicherung | {t4} min | {beschreibung} | {sozialform} | {material} |
| Reflexion/Ausblick | {t5} min | {beschreibung} | {sozialform} | {material} |

---

### 🧠 Methodendetails

**Einstieg – {methode}:**
{detaillierte beschreibung wie der Einstieg konkret gestaltet wird}

**Erarbeitung – {methode}:**
{beschreibung der Erarbeitungsphase mit konkreten Aufgabenstellungen}

**Sicherung – {methode}:**
{wie Ergebnisse gesichert und visualisiert werden}

---

### 📚 Materialien & Vorbereitung

**Benötigte Materialien:**
- {material_1}
- {material_2}

**Vorbereitung durch Lehrkraft:**
- {vorbereitung_1}
- {vorbereitung_2}

---

### 🔀 Differenzierung

**Für leistungsstarke SuS:**
{konkrete aufgabe oder erweiterung}

**Für leistungsschwächere SuS:**
{vereinfachung, scaffold oder zusätzliche hilfe}

---

### ⚠️ Mögliche Herausforderungen

{1-2 realistische Hinweise was schiefgehen könnte}

---

### 💡 Ideen für Folgestunden

- {folgestunde_1}
- {folgestunde_2}

---

## Verhaltensregeln

1. **Keine Fantasiematerialien erfinden** – nur reale, bekannte Materialien
   oder "selbst zu erstellen".
2. **Methoden immer konkret beschreiben** – nicht nur benennen.
3. **Zeitangaben realistisch halten** – Einstieg max. 10 min, Sicherung min. 5 min.
4. **Ton:** professionell und kollegial.
5. **Am Ende immer fragen:**
   "Soll ich für diese Stunde noch ein Arbeitsblatt, einen
   Erwartungshorizont oder ein Bewertungsraster erstellen?"
