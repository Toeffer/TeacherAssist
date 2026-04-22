---
name: lehrplan_einlesen
version: 1.0.0
author: LehrerAgent
description: >
  Liest einen Lehrplan ein – als PDF-Upload, URL oder manuelle Eingabe –
  und speichert die relevanten Kompetenzen strukturiert in lehrplan_index.md,
  damit alle anderen Skills lehrplankonform arbeiten können.
category: bildung
language: de

triggers:
  - "lehrplan einlesen"
  - "lehrplan hochladen"
  - "lehrplan hinzufügen"
  - "lehrplan speichern"
  - "kompetenz eintragen"
  - "lehrplan aktualisieren"
  - "bildungsstandard"
  - "ich schick dir den lehrplan"
  - "hier ist der lehrplan"

permissions:
  - read_memory
  - write_memory
  - read_files

memory_files:
  - lehrerprofil.md
  - lehrplan_index.md

input_types:
  - pdf
  - text
  - url
  - manual

parameters:
  required: []
  optional:
    - fach
    - klasse
    - bundesland
    - schulform
    - quelle_url
---

# Skill: Lehrplan einlesen & indexieren

## Zweck

Dieser Skill verarbeitet Lehrpläne in verschiedenen Formaten und speichert
die relevanten Kompetenzerwartungen strukturiert im `lehrplan_index.md`.

Dadurch können alle anderen Skills (besonders `unterricht_planen` und
`bewertung_erstellen`) echte, verankerte Lehrplanbezüge verwenden.

---

## Ablauf

### Schritt 1 – Lehrerprofil laden

Lade `lehrerprofil.md` für Standard-Bundesland und -Schulform.

### Schritt 2 – Eingabemodus bestimmen

Prüfe, was die Lehrkraft bereitgestellt hat:

**Fall A – PDF wurde hochgeladen:**
→ Weiter mit "PDF verarbeiten" (Schritt 3a)

**Fall B – URL wurde genannt:**
→ Weiter mit "URL laden" (Schritt 3b)

**Fall C – Nur Fach + Klasse genannt, kein Dokument:**
→ Weiter mit "Manueller Eintrag" (Schritt 3c)

**Fall D – Nichts angegeben:**
```
Wie möchtest du den Lehrplan einpflegen?

  📄 PDF schicken – ich lese ihn automatisch aus
  🔗 URL nennen – ich rufe ihn direkt ab
  ✏️  Manuell eingeben – ich frage dich Schritt für Schritt

Was schickst du mir?
```

---

### Schritt 3a – PDF verarbeiten

Lies das PDF vollständig aus.

Suche nach diesen Strukturelementen:
- Kompetenzerwartungen / Lernziele
- Inhaltsbereiche / Themenfelder
- Klassenstufen / Jahrgangsstufen
- Anforderungsbereiche (AFB I, II, III oder äquivalent)
- Prozess- vs. Inhaltsbezogene Kompetenzen

Falls das PDF mehrere Fächer oder Jahrgänge enthält:
```
Das Dokument enthält Lehrplaninhalte für mehrere Bereiche.
Für welches Fach und welche Klasse soll ich zuerst einlesen?
Oder soll ich alles auf einmal erfassen?
```

→ Dann weiter mit Schritt 4.

---

### Schritt 3b – URL laden

Rufe die URL ab und extrahiere den Text.

Falls es sich um eine offizielle Kultusministeriums-Seite handelt
(erkennbar an .de-Domains wie lehrplanplus.bayern.de, schulentwicklung.nrw.de etc.):
Vermerke die Quelle als "offiziell verifiziert" in `lehrplan_index.md`.

→ Dann weiter mit Schritt 4.

---

### Schritt 3c – Manueller Eintrag

Falls kein Dokument vorliegt, stelle gezielte Fragen:

```
Kein Problem, ich trage das manuell ein. Ein paar Fragen:

1. Fach: ?
2. Klasse / Jahrgang: ?
3. Bundesland: ? (oder ich nehme dein gespeichertes: {bundesland})
4. Schulform: ? (oder: {schulform})
5. Was ist der Kompetenzbereich / das Themenfeld?
6. Was sollen die SuS am Ende können? (Lernzielformulierung)
7. Gibt es eine offizielle Quelle / Seitenzahl?
```

→ Dann weiter mit Schritt 4.

---

### Schritt 4 – Inhalte strukturieren

Extrahiere aus dem Dokument oder den Angaben folgende Felder pro Eintrag:

```
bundesland, schulform, fach, klasse_von, klasse_bis,
kompetenzbereich, inhalte[], lernziele[], afb[], quelle
```

Gruppiere sinnvoll: Nicht für jede Zeile des Lehrplans einen eigenen Eintrag,
sondern nach logischen Themenblöcken (1 Eintrag = 1 Unterrichtseinheit wert).

### Schritt 5 – In lehrplan_index.md speichern

Hänge die neuen Einträge an `memory/lehrplan_index.md` an.

Format pro Eintrag:

```markdown
---
### {bundesland} | {schulform} | {fach} | Klasse {klasse_von}–{klasse_bis}
**Kompetenzbereich:** {name}

**Inhaltsbereiche:**
- {inhalt_1}
- {inhalt_2}
- {inhalt_3}

**Kompetenzerwartungen (Lernziele):**
- AFB I: Die SuS {lernziel_afb1}
- AFB II: Die SuS {lernziel_afb2}
- AFB III: Die SuS {lernziel_afb3}

**Mögliche Unterrichtsthemen:**
- {thema_1}
- {thema_2}

**Quelle:** {quelle_mit_datum}
**Verifiziert:** {ja (offiziell) | nein (KI-Schätzung) | manuell eingetragen}
---
```

---

### Schritt 6 – Zusammenfassung ausgeben

```
✅ Lehrplan erfolgreich eingelesen!

📚 Eingetragen für: {fach}, {klasse}, {bundesland}
📝 Anzahl neuer Einträge: {anzahl}
🗂️  Gespeichert in: memory/lehrplan_index.md

Folgende Kompetenzbereiche sind jetzt abrufbar:
  • {bereich_1}
  • {bereich_2}
  • {bereich_3}
  (…)

Ab sofort werden deine Stundenpläne und Bewertungen mit echten
Lehrplanbezügen aus diesem Dokument arbeiten.

Möchtest du gleich eine Stunde für {fach} Klasse {klasse} planen?
```

---

## Besondere Fälle

### Lehrplan bereits vorhanden

Falls für die Kombination {bundesland}+{schulform}+{fach}+{klasse} bereits
ein Eintrag existiert:

```
Für {fach} Klasse {klasse} in {bundesland} habe ich bereits Einträge.

Möchtest du:
  1. Den bestehenden Eintrag ergänzen
  2. Den bestehenden Eintrag ersetzen
  3. Beide Versionen behalten (mit Datum markiert)
```

### Lehrplan nicht erkennbar / schlechte PDF-Qualität

Falls das Dokument kein erkennbarer Lehrplan ist oder schlecht gescannt:

```
Das Dokument scheint kein Lehrplan zu sein (oder ich kann es nicht
gut genug lesen). Ich habe {was_ich_erkannt_habe} gefunden.

Möchtest du die Inhalte manuell eingeben?
Oder schick mir eine bessere Version des Dokuments.
```

### Mehrere Bundesländer / Schulformen im Dokument

Falls das PDF einen übergreifenden Bildungsstandard enthält
(z. B. KMK-Bildungsstandards):

Erstelle Einträge mit `bundesland: "KMK (bundesweit)"` und vermerke,
dass diese für alle Bundesländer gelten.

---

## Verhaltensregeln

1. **Nie erfinden** – Falls keine Quelle vorliegt, markiere den Eintrag
   ausdrücklich als `Verifiziert: nein (KI-Schätzung)`.

2. **Qualität über Quantität** – Lieber 5 präzise Einträge als 50 vage.

3. **Immer Quelle vermerken** – Dateiname des PDFs, URL oder "manuell eingegeben".

4. **Lehrplan-Index wächst** – Neue Einträge immer anfügen, nie löschen
   (außer explizite Aufforderung der Lehrkraft).
