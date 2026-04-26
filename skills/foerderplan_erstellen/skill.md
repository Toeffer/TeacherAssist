---
name: foerderplan_erstellen
version: 1.0.0
author: LehrerAgent
description: >
  Erstellt einen strukturierten, pädagogisch fundierten Förderplan für
  Schülerinnen und Schüler mit besonderem Förderbedarf – mit konkreten
  Maßnahmen, Zielen, Zeitrahmen und Evaluationskriterien.
category: bildung
language: de
priority: 8

triggers:
  - "förderplan"
  - "förderpla"
  - "fördermaßnahmen"
  - "individual förderung"
  - "individuelle förderung"
  - "schüler fördern"
  - "förderung erstellen"
  - "sonderpädagogisch"
  - "lrs förderplan"
  - "adhs förderplan"
  - "nachteilsausgleich"
  - "eingliederungshilfe"
  - "förderkonzept"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - foerderbereich      # Lesen | Schreiben | Rechnen | Sozialverhalten | Sprache | Konzentration | Allgemein
  optional:
    - klasse
    - fach
    - ausgangslage        # kurze Beschreibung der aktuellen Situation (anonym)
    - ziele               # was soll erreicht werden
    - zeitrahmen          # z. B. "bis Schuljahresende", "6 Wochen" (Standard: 1 Schulhalbjahr)
    - massnahmen_pref     # bevorzugte Maßnahmen (z. B. "Lautleseverfahren", "Mathe-Förder-App")
    - beteiligte          # Lehrkraft | Eltern | Schulbegleitung | Förderlehrer | alle
    - nachteilsausgleich  # ja | nein | prüfen (Standard: prüfen)
---

# Skill: Förderplan erstellen

## Zweck

Dieser Skill erstellt einen vollständigen, dokumentierbaren Förderplan
für Schülerinnen und Schüler mit besonderem Unterstützungsbedarf.

Der Plan orientiert sich an den offiziellen Förderplan-Standards der meisten
deutschen Bundesländer und ist sofort verwendbar.

**DSGVO:** Der Förderplan wird ohne Schülernamen erstellt.
Die Lehrkraft ersetzt den Platzhalter „SuS-XX" manuell.

---

## Ablauf

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md`:
- Schulform → beeinflusst Förderansatz (Grundschule / Inklusion / Förderschule)
- Bundesland → ggf. unterschiedliche Terminologie und Rechtsgrundlage

### Schritt 2 – Fehlende Parameter erfragen

Falls `foerderbereich` unklar:
```
In welchem Bereich soll der Förderplan erstellt werden?
  1 – Lesen / LRS (Legasthenie-Verdacht oder Leseverzögerung)
  2 – Schreiben / Rechtschreibung
  3 – Rechnen / Dyskalkulie-Verdacht
  4 – Sprache / Sprachentwicklung / DaZ
  5 – Konzentration / Aufmerksamkeit (ADHS-Umfeld)
  6 – Sozialverhalten / Emotionale Regulation
  7 – Allgemeiner Förderbedarf (mehrere Bereiche)
```

Falls `ausgangslage` fehlt:
```
Beschreibe kurz die aktuelle Situation des Schülers / der Schülerin
– ohne Namen, nur Stichworte.
(z. B. "liest stockend, vertauscht Buchstaben, vermeidet Lesen vor der Klasse")
```

Falls `zeitrahmen` fehlt: verwende **1 Schulhalbjahr** als Standard.

### Schritt 3 – Ziele definieren (SMART-Methode)

Formuliere Förderziele nach dem SMART-Prinzip:
- **S**pezifisch: klare, messbare Kompetenz
- **M**essbar: Testformat oder Beobachtungskriterium angeben
- **A**ngemessen: erreichbar im Zeitrahmen
- **R**elevant: bezogen auf Lehrplan-Mindeststandard
- **T**erminiert: Datum der Überprüfung

Unterscheide:
- **Hauptziel** (was bis {zeitrahmen} erreicht sein soll)
- **Teilziele** (2–3 Zwischenstufen / Meilensteine)

### Schritt 4 – Maßnahmen auswählen

Wähle konkrete, umsetzbare Maßnahmen je nach Bereich:

**Lesen/LRS:**
- Lautleseverfahren (Partner-Lesen, Lesetraining)
- Leseförder-Software (Antolin, Lautlese-Trainer)
- Schriftgröße / Zeilenabstand anpassen
- Nachteilsausgleich: mehr Lesezeit, keine Benotung der Rechtschreibung

**Schreiben/Rechtschreibung:**
- Rechtschreibstrategien (Silbenmethode, Ableitung)
- Wörterheft mit persönlichem Grundwortschatz
- Diktat-Alternativen (freies Schreiben, Lückentexte)

**Rechnen/Dyskalkulie:**
- Handlungsorientierte Zugänge (Rechenmaterial, Zahlenstrahl)
- Taschenrechner-Erlaubnis (Nachteilsausgleich)
- Rechenmethoden schriftlich sichern

**Konzentration/ADHS:**
- Sitzplatz-Optimierung (vorne, störarme Umgebung)
- Aufgaben in Teilschritte zerlegen
- Pausen-Rituale, Bewegungsanlässe
- Timer / Visualisierung der Arbeitszeit

**Sozialverhalten:**
- Klassenrat-Teilnahme
- Soziales Kompetenztraining
- Gesprächsregeln-Visualisierung

**Sprache/DaZ:**
- Wortschatz-Aufbau durch Bilder-Glossare
- Scaffolding (Satzrahmen, Redemittel)
- Vorlesen-Hören (Hörbücher, Texte)

### Schritt 5 – Förderplan im Ausgabeformat erstellen

Erstelle den vollständigen Plan (siehe Ausgabeformat unten).

### Schritt 6 – In Memory speichern (optional)

Speichere unter:
`memory/foerderplaene/{fach}_{klasse}_{datum}.md`

Frage vorher:
```
Soll ich diesen Förderplan in deiner Wissensdatenbank speichern,
damit du beim nächsten Mal schnell darauf zugreifen kannst?
(Der Plan enthält keine Schülernamen – DSGVO-konform.)
```

### Schritt 7 – Angebot am Ende

```
✅ Der Förderplan ist fertig!

Klicke auf 📄, um ihn druckfertig zu öffnen.

Soll ich noch:
• Ein Elternbrief zu diesem Förderplan erstellen?
• Konkrete Übungsmaterialien für die ersten 2 Wochen vorschlagen?
• Eine Vorlage für das Evaluationsgespräch erstellen?
```

---

## Ausgabeformat

---

# Förderplan

**Schuljahr:** {schuljahr}
**Klasse:** {klasse}
**Fach / Bereich:** {foerderbereich}
**Erstellungsdatum:** {datum}
**Gültig bis / Überprüfung am:** {zeitrahmen_ende}

> **Hinweis:** Schüler*innen-Kürzel: **SuS-XX**
> *(Bitte manuell durch den tatsächlichen Namen ersetzen – nicht digital speichern)*

---

### 1. Ausgangslage

{kurze, sachliche Beschreibung der Ist-Situation – ohne Schuldzuweisungen}

**Beobachtete Stärken:**
- {staerke_1}
- {staerke_2}

**Festgestellter Förderbedarf:**
- {bedarf_1}
- {bedarf_2}

---

### 2. Förderziele

**Hauptziel** *(bis {zeitrahmen_ende}):*
> SuS-XX {ziel_hauptsatz – SMART formuliert, messbar}

**Teilziele / Meilensteine:**

| # | Teilziel | Überprüfung am | Methode |
|---|----------|----------------|---------|
| 1 | {teilziel_1} | {datum_1} | {beobachtung/test} |
| 2 | {teilziel_2} | {datum_2} | {beobachtung/test} |
| 3 | {teilziel_3} | {datum_3} | {beobachtung/test} |

---

### 3. Fördermaßnahmen

| Maßnahme | Wer | Wann / Häufigkeit | Material / Hinweis |
|----------|-----|-------------------|--------------------|
| {massnahme_1} | {wer_1} | {haeufigkeit_1} | {hinweis_1} |
| {massnahme_2} | {wer_2} | {haeufigkeit_2} | {hinweis_2} |
| {massnahme_3} | {wer_3} | {haeufigkeit_3} | {hinweis_3} |

---

### 4. Nachteilsausgleich

{wenn nachteilsausgleich: ja oder prüfen}

Folgende Maßnahmen des Nachteilsausgleichs werden empfohlen / bereits gewährt:

- ☐ Verlängerte Bearbeitungszeit ({prozent}% Zuschlag)
- ☐ Vorlesen von Aufgaben
- ☐ Nutzung von Hilfsmitteln ({hilfsmittel})
- ☐ Kein Abzug für Rechtschreibfehler bei Inhaltsleistungen
- ☐ Sonstiges: ___________________________

> ⚠️ Nachteilsausgleich erfordert i.d.R. ärztliche/psychologische Bescheinigung.
> Rücksprache mit Schulleitung und Eltern empfohlen.

---

### 5. Beteiligte und Verantwortlichkeiten

| Person / Funktion | Aufgabe |
|-------------------|---------|
| Klassenlehrkraft | Koordination, Beobachtung, Elternkontakt |
| {beteiligter_2} | {aufgabe_2} |
| Eltern | Häusliche Förderung, Termine einhalten |

---

### 6. Evaluationsplan

**Nächstes Gespräch:** {datum_gespraech}
**Teilnehmer:** Lehrkraft, Eltern{ggf. Schulbegleitung}

**Evaluationsfragen:**
- Hat SuS-XX Teilziel 1 erreicht? (Beleg: {beleg})
- Hat SuS-XX Teilziel 2 erreicht? (Beleg: {beleg})
- Welche Maßnahmen haben gewirkt? Welche nicht?
- Wird der Plan fortgeführt / angepasst / beendet?

**Unterschriften beim Evaluationsgespräch:**

Lehrkraft: ____________________   Datum: __________

Erziehungsberechtigte: ____________________

---

## Verhaltensregeln

1. **Stärkenorientiert beginnen** – Jeder Förderplan hebt zuerst hervor,
   was das Kind gut kann. Das ist pädagogisch wirksam und gesetzlich erwartet.

2. **SMART-Ziele** – Vage Ziele ("soll sich verbessern") sind nicht
   evaluierbar. Immer spezifisch und messbar formulieren.

3. **Nachteilsausgleich ist kein Mitleid** – klare rechtliche Grundlage,
   nie als Gefallen darstellen. Nur wenn sachlich begründbar.

4. **Keine Diagnosen setzen** – "zeigt Merkmale, die auf LRS hindeuten"
   statt "hat LRS". Diagnosen stellen nur Fachärzte / Psychologen.

5. **Eltern als Partner** – Formulierungen einbeziehen, nicht beschuldigen.
   "Gemeinsam arbeiten wir daran..." statt "Eltern müssen...".

6. **Datenschutz** – Keine Klarnamen in gespeicherten Plänen.
   Ausfüllen des Namens erst auf dem ausgedruckten, lokal gespeicherten Exemplar.
