---
name: methodenrotation
version: 1.0.0
author: LehrerAgent
description: >
  Analysiert die verwendeten Unterrichtsmethoden und warnt vor
  methodischer Einseitigkeit. Schlägt abwechslungsreiche Alternativen vor.
category: bildung
language: de

triggers:
  - "methodenrotation"
  - "welche methoden habe ich benutzt"
  - "methoden analysieren"
  - "zu viel frontalunterricht"
  - "methodenvielfalt"
  - "methoden wiederholt"
  - "methodenvielfalt prüfen"
  - "welche methode als nächstes"
  - "abwechslung im unterricht"

permissions:
  - read_memory

memory_files:
  - vergangene_stunden.md
  - lehrerprofil.md
---

# Skill: Methodenrotation

## Zweck

Analysiert die letzten Unterrichtsstunden aus `memory/vergangene_stunden.md`
auf Methodenvielfalt und warnt, wenn dieselbe Methode zu häufig hintereinander
oder insgesamt zu dominant eingesetzt wurde.

**Faustregel:** Keine Methode mehr als 3× in Folge oder mehr als 40% der
Stunden eines Zeitraums – außer die Lehrkraft hat explizit Präferenzen
in `lehrerprofil.md` hinterlegt (die dann berücksichtigt werden).

---

## Ablauf

### Schritt 1 – Verlaufsprotokoll und Profil laden

Lade `memory/vergangene_stunden.md` und `memory/lehrerprofil.md`.

Extrahiere für jede Stunde:
- Datum, Fach, Klasse
- Sozialform (Einzel-, Partner-, Gruppenarbeit, Plenum)
- Methode (z.B. Direkte Instruktion, Stationsarbeit, Diskussion, Experiment)
- Arbeitsform (Frontalunterricht, offenes Lernen, kooperativ, projektorientiert)

Falls leer/nicht vorhanden: Hinweis ausgeben, dass noch keine Stunden
protokolliert sind, und das Protokollieren kurz erklären.

### Schritt 2 – Präferenzen der Lehrkraft berücksichtigen

Falls `lehrerprofil.md` Methoden-Präferenzen enthält
(z.B. "kein reiner Frontalunterricht", "Stationenarbeit bevorzugt"):
→ Wende diese als Filter/Verstärker auf die Empfehlungen an.

### Schritt 3 – Muster erkennen

Berechne:
1. Häufigkeit jeder Methode (absolut + prozentual)
2. Maximale Länge aufeinanderfolgender gleicher Methoden
3. Letzte 5 Stunden als Methodenfolge visualisieren

### Schritt 4 – Warnung und Empfehlung

Falls eine Methode ≥ 3× in Folge oder ≥ 40% gesamt vorkommt:
→ Deutliche Warnung mit konkretem Alternativ-Vorschlag

Falls keine kritische Häufung:
→ Positives Feedback + leichte Optimierungshinweise

---

## Ausgabeformat

---

### 🔄 Methoden-Analyse: {Fach oder "alle Fächer"} – letzte {N} Stunden

#### Methodenverteilung

| Methode / Sozialform | Anzahl | Anteil | Letzte 5 Std. |
|----------------------|--------|--------|----------------|
| {Methode} | {n} | {%}% | {◼◼◻◻◻} |

*(◼ = angewendet, ◻ = nicht angewendet in dieser Stunde)*

---

#### {⚠️ Warnung / ✅ Gute Vielfalt}

**Befund:** {Konkrete Beschreibung der erkannten Muster oder der guten Vielfalt}

---

#### 💡 Methodenvorschläge für die nächsten Stunden

Für {Fach/Klasse} empfehle ich abwechslungsweise:

1. **{Methode}** – {kurze Begründung: warum jetzt passend, welche Kompetenzen gefördert}
2. **{Methode}** – {kurze Begründung}
3. **{Methode}** – {kurze Begründung}

**Tipp:** {Ein konkreter pädagogischer Hinweis passend zur Klasse/Schulform}

---

> Hinweis: Passe die Vorschläge an das aktuelle Unterrichtsthema und
> die Bedürfnisse der Lerngruppe an. Methodenvielfalt ist ein Mittel,
> kein Selbstzweck.
