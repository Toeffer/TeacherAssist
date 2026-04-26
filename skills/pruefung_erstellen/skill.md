---
name: pruefung_erstellen
version: 1.0.0
author: LehrerAgent
description: >
  Erstellt vollständige, lehrplankonforme Klassenarbeiten, Klausuren und
  Kurztest – mit Erwartungshorizont, Notenschlüssel, Aufgaben über alle
  Anforderungsbereiche und optionaler Differenzierung.
category: bildung
language: de
priority: 10

triggers:
  - "prüfung erstellen"
  - "klassenarbeit erstellen"
  - "klausur erstellen"
  - "test erstellen"
  - "klassenarbeit"
  - "klausur"
  - "schreibe eine prüfung"
  - "erstelle einen test"
  - "prüfungsaufgaben"
  - "leistungsüberprüfung"
  - "schulaufgabe"
  - "stegreifaufgabe"

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
    - thema
  optional:
    - art                  # klassenarbeit | klausur | kurztest | stegreif | muendlich (Standard: klassenarbeit)
    - gesamtpunkte         # Standard: 50 (Klassenarbeit) / 20 (Kurztest)
    - zeitrahmen           # Standard: 45min (Kurztest: 15–20min, Klausur: 90min)
    - notenschluessel      # standard | mild | verschaerft (Standard: standard)
    - schwierigkeitsgrad   # einfach | mittel | anspruchsvoll | gemischt (Standard: gemischt)
    - afb_schwerpunkt      # I | II | III | gemischt (Standard: gemischt)
    - mit_erwartungshorizont # ja | nein (Standard: ja)
    - differenzierung      # ja | nein (Standard: nein – Prüfungen meist einheitlich)
    - hilfsmittel          # keine | taschenrechner | atlas | wörterbuch | formelsammlung
    - themen_ausschluss    # Themen, die NICHT abgefragt werden sollen
---

# Skill: Prüfung / Klassenarbeit erstellen

## Zweck

Dieser Skill generiert eine vollständige, druckfertige Klassenarbeit oder Prüfung
mit Deckblatt, Aufgaben, Erwartungshorizont und Notenschlüssel.

Die Aufgaben decken alle drei Anforderungsbereiche (AFB I–III) ab und orientieren
sich am Lehrplan des Bundeslandes der Lehrkraft.

---

## Ablauf

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md`:
- Bundesland → Lehrplanbezug
- Schulform → Anspruchsniveau

Durchsuche `lehrplan_index.md` nach `{fach}` + `{klasse}` für passende Kompetenzen.

### Schritt 2 – Fehlende Parameter erfragen

Falls `art` unklar:
```
Was für eine Prüfung soll ich erstellen?
  1 – Klassenarbeit (45 min, 50 Punkte)
  2 – Klausur (90 min, 100 Punkte)
  3 – Kurztest (15–20 min, 20 Punkte)
  4 – Stegreifaufgabe (10–15 min, ohne Ankündigung)
  5 – Mündliche Prüfung (Fragenkatalog)
```

Falls `thema` zu weit gefasst, präzisiere:
```
Das Thema "{thema}" ist recht breit. Welche Aspekte soll die Prüfung abdecken?
(z. B. "nur lineare Gleichungen, keine Ungleichungen")
```

Falls `mit_erwartungshorizont` nicht genannt: erstelle ihn immer – er ist Standard.

Falls `hilfsmittel` nicht genannt:
```
Welche Hilfsmittel sind erlaubt?
(Standard: keine – außer du sagst etwas anderes)
```

### Schritt 3 – Lehrplanbezug herstellen

Suche in `lehrplan_index.md` nach dem Thema.
Falls kein Eintrag: formuliere Kompetenzbezug nach KMK-Bildungsstandards, markiere mit `[*]`.

### Schritt 4 – Aufgaben planen

Plane die Aufgabenstruktur:

**Verteilung AFB (Anforderungsbereiche):**
- AFB I (Reproduktion): ~30% der Punkte
  Operatoren: Nenne, Beschreibe, Berechne, Ordne zu, Zeichne
- AFB II (Reorganisation/Anwendung): ~40% der Punkte
  Operatoren: Erkläre, Vergleiche, Analysiere, Stelle dar, Wende an
- AFB III (Transfer/Bewertung): ~30% der Punkte
  Operatoren: Beurteile, Entwickle, Übertrage, Begründe deine Entscheidung

**Aufgabenarten je nach Fach:**
- Mathematik: Rechenaufgaben, Textaufgaben, Beweisführung, Skizzen
- Deutsch: Textanalyse, Grammatikaufgaben, Aufsatz, Sprachreflexion
- Englisch/Fremdsprachen: Leseverstehen, Vokabeln, Grammatik, Schreiben
- Naturwissenschaften: Experiment beschreiben, Diagramme auswerten, Hypothesen
- Geschichte/SoWi: Quellen analysieren, Einordnen, Urteile begründen

**Format-Hinweise:**
- Aufgaben mit Punktzahl und Operator klar kennzeichnen
- Lösungsraum einplanen (Linien, Tabellen, Skizzen-Felder)
- Schwierigkeitsgrad von Aufgabe 1 → letzter Aufgabe steigern

### Schritt 5 – Erwartungshorizont erstellen

Für jede Aufgabe:
- Musterlösung vollständig ausformulieren
- Teilpunkte definieren
- Häufige Fehler antizipieren

### Schritt 6 – Notenschlüssel berechnen

Berechne automatisch aus `gesamtpunkte` + `notenschluessel`:

| Typ | Note 4 | Note 3 | Note 2 | Note 1 |
|-----|--------|--------|--------|--------|
| standard | ≥50% | ≥65% | ≥80% | ≥95% |
| mild | ≥40% | ≥55% | ≥70% | ≥87% |
| verschaerft | ≥55% | ≥70% | ≥82% | ≥95% |

### Schritt 7 – Angebot am Ende

```
✅ Die Prüfung ist fertig!

Klicke auf 📄 für die Schülerversion (ohne Lösungen).
Klicke erneut auf 📄 nach dem Erwartungshorizont für die Lehrerkopie.

Soll ich noch:
• Eine vereinfachte Version für Schüler*innen mit Nachteilsausgleich erstellen?
• Einen Elternbrief zur Ankündigung dieser Prüfung schreiben?
• Das Bewertungsraster für die Korrektur abspeichern?
```

---

## Ausgabeformat

Das Ausgabeformat besteht aus **zwei Teilen**:

### Teil 1 – Schülerversion (zum Ausdrucken)

---

# {art}: {thema}

**Fach:** {fach} | **Klasse:** {klasse} | **Datum:** ________________

**Name:** _______________________________ | **Punkte:** _______ / {gesamtpunkte}

**Bearbeitungszeit:** {zeitrahmen} Minuten

**Erlaubte Hilfsmittel:** {hilfsmittel}

---

> **Lies alle Aufgaben sorgfältig durch, bevor du beginnst.**
> Zeige deinen vollständigen Lösungsweg.

---

#### Aufgabe 1 – {kurztitel} ({punkte} Punkte) | AFB I

{aufgabenstellung – klar und eindeutig}

{ggf. Informationstext / Tabelle / Diagramm}

_____________________________________________
_____________________________________________
_____________________________________________

---

#### Aufgabe 2 – {kurztitel} ({punkte} Punkte) | AFB I–II

{aufgabenstellung}

---

*(weitere Aufgaben nach demselben Schema, steigender Schwierigkeit)*

---

#### Aufgabe {n} – {kurztitel} ({punkte} Punkte) | AFB III

{anspruchsvolle Transferaufgabe}

---

### Punkteübersicht

| Aufgabe | Max. Punkte | AFB | Erreicht |
|---------|-------------|-----|---------|
| 1 | {p} | I | |
| 2 | {p} | II | |
| … | … | … | |
| **Gesamt** | **{gesamt}** | | |

---

*(Seitenumbruch – nur in der Lehrerkopie)*

---

### Teil 2 – Erwartungshorizont *(nur für Lehrkraft)*

---

#### Aufgabe 1 – Musterlösung

**Erwartete Antwort:**
{vollständige Lösung}

**Teilpunkte:**
- {kriterium_1}: {p} Punkte
- {kriterium_2}: {p} Punkte

**Häufige Fehler:**
- {fehler_1}

---

*(weitere Aufgaben analog)*

---

### Notenschlüssel

| Note | Bezeichnung | Punkte | Prozent |
|------|-------------|--------|---------|
| 1 | Sehr gut | {p1} – {gesamt} P | ≥ {pct1}% |
| 2 | Gut | {p2} – {p1-0.5} P | ≥ {pct2}% |
| 3 | Befriedigend | {p3} – {p2-0.5} P | ≥ {pct3}% |
| 4 | Ausreichend | {p4} – {p3-0.5} P | ≥ {pct4}% |
| 5 | Mangelhaft | {p5} – {p4-0.5} P | ≥ {pct5}% |
| 6 | Ungenügend | 0 – {p5-0.5} P | < {pct5}% |

> ⚠️ Vorschlag – Endentscheidung liegt bei der Lehrkraft.

---

## Verhaltensregeln

1. **Schülerversion komplett ohne Lösungen** – nie Lösungshinweise in den
   Aufgabentext schreiben.

2. **Operator zum AFB passend** – AFB I: Nenne, Berechne, Zeichne;
   AFB II: Erkläre, Vergleiche; AFB III: Beurteile, Entwickle, Übertrage.

3. **Lösungsraum realistisch** – Platz unter Aufgaben muss für die erwartete
   Antwort reichen. Knappe Linien frustrieren SuS.

4. **Gesamtpunkte immer anzeigen** – SuS sollen die Menge der Arbeit einschätzen können.

5. **Kein "Trick-Modus"** – Prüfungen testen, was unterrichtet wurde.
   Keine Aufgaben, die bewusst verwirren oder auf Nebendetails abzielen.

6. **Erwartungshorizont vor dem Druck prüfen** – Musterlösung selbst
   durchrechnen, bevor die Arbeit ausgeteilt wird.

7. **Am Ende immer anbieten:** vereinfachte Version für Nachteilsausgleich,
   Elternbrief zur Ankündigung, Bewertungsraster zum direkten Korrigieren.
