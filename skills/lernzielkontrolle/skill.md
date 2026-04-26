---
name: lernzielkontrolle
version: 1.0.0
author: LehrerAgent
description: Erstellt einen kurzen Wissenstest (10–15 Min) zum Abschluss einer Unterrichtseinheit – mit Musterlösung und Selbstkorrekturbogen. Kein Notendruck, formative Funktion.
category: bildung
language: de
priority: 14

triggers:
  - "lernzielkontrolle"
  - "kurzer test"
  - "exit ticket"
  - "lernstandserhebung"
  - "wissenscheck"
  - "stundenabschlusstest"
  - "abschlussaufgabe reihe"
  - "quiz zum abschluss"
  - "tick the box"
  - "formative bewertung"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md
  - lehrplan_index.md

parameters:
  required:
    - fach
    - klasse
    - thema
  optional:
    - zeitstunden
    - aufgabenanzahl
    - format
    - mit_selbstkorrektur
---

# Skill: Lernzielkontrolle erstellen

## Zweck

Dieser Skill erstellt einen kompakten Wissenstest (10–15 Minuten) zum Abschluss einer
Unterrichtsreihe oder -einheit. **Keine Klassenarbeit** – sondern ein diagnostisches
Instrument, das der Lehrkraft zeigt, ob die Lernziele erreicht wurden.

Formate: Multiple Choice, Kurzantworten, Zuordnung, Lückentexte, Zeichnen/Skizzieren.
Output: Schülerversion (ohne Lösungen) + Musterlösung + optionaler Selbstkorrekturbogen.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md` → Schulform (beeinflusst Schwierigkeitsgrad).
Suche in `lehrplan_index.md` nach Kompetenzen für `{fach}` + `{klasse}` + `{thema}`.

### Schritt 2 – Parameter klären

Falls `zeitstunden` fehlt: Standard = **10 Minuten**.
Falls `aufgabenanzahl` fehlt:
- 10 Min → 4–5 Aufgaben
- 15 Min → 6–8 Aufgaben

Falls `format` nicht angegeben: Mix aus MC + Kurzantwort wählen.
Falls `mit_selbstkorrektur` nicht angegeben: Standard = Ja (Selbstkorrektur inklusive).

### Schritt 3 – Aufgaben entwickeln

Alle drei AFB-Stufen berücksichtigen:
- **AFB I (Reproduktion):** Definitionen, Fakten, Begriffe benennen (~40%)
- **AFB II (Reorganisation):** Zusammenhänge erklären, anwenden (~40%)
- **AFB III (Transfer):** Übertragung auf neue Situation (~20%)

Aufgaben müssen:
- ohne Hilfsmittel lösbar sein
- eindeutig formuliert sein (keine Doppeldeutigkeiten)
- mit dem Unterricht der Reihe übereinstimmen (nicht über den Rand hinaus)

### Schritt 4 – Test erstellen

Erstelle Schülerversion, Musterlösung und Selbstkorrekturbogen.

---

## Ausgabeformat

---

### 📄 Lernzielkontrolle – Schülerversion

**Fach:** {fach} | **Klasse:** {klasse} | **Thema:** {thema}
**Zeit:** {zeitstunden} Minuten | **Hilfsmittel:** keine

Name: ______________________________ Datum: ______________

---

*(Aufgaben nach AFB-Stufe geordert)*

**Aufgabe 1** *(AFB I – {punkte} P)*
{aufgabentext}

{antwortfeld – Linien / Kästchen / MC-Optionen}

---

**Aufgabe 2** *(AFB I – {punkte} P)*
{aufgabentext}

{antwortfeld}

---

**Aufgabe 3** *(AFB II – {punkte} P)*
{aufgabentext}

{antwortfeld}

---

**Aufgabe 4** *(AFB II – {punkte} P)*
{aufgabentext}

{antwortfeld}

---

**Aufgabe 5** *(AFB III – {punkte} P)*
{aufgabentext}

{antwortfeld}

---

**Gesamt: _____ / {max_punkte} Punkte**

---

### ✅ Musterlösung *(nur für Lehrkraft)*

| Aufgabe | Erwartete Antwort | Punkte |
|---------|------------------|--------|
| 1 | {loesung_1} | {p1} |
| 2 | {loesung_2} | {p2} |
| 3 | {loesung_3} | {p3} |
| 4 | {loesung_4} | {p4} |
| 5 | {loesung_5} | {p5} |
| **Gesamt** | | **{max_punkte}** |

**Auswertungshinweis:**
- {max_punkte} – {obergrenze_sehr_gut} P → Lernziel vollständig erreicht ✅
- {grenze_gut} – {grenze_befriedigend} P → Lernziel weitgehend erreicht 🟡
- unter {grenze_ausreichend} P → Lernziel noch nicht erreicht ❌ → Förderhinweis

---

### 🔄 Selbstkorrekturbogen *(optional, für SuS)*

Tauscht eure Blätter mit dem/der Sitznachbar/in.
Benutzt die Musterlösung an der Tafel und tragt die Punkte ein.

| Aufgabe | Richtig? | Punkte |
|---------|----------|--------|
| 1 | ☐ ja  ☐ teilweise  ☐ nein | |
| 2 | ☐ ja  ☐ teilweise  ☐ nein | |
| 3 | ☐ ja  ☐ teilweise  ☐ nein | |
| 4 | ☐ ja  ☐ teilweise  ☐ nein | |
| 5 | ☐ ja  ☐ teilweise  ☐ nein | |
| **Gesamt** | | **_____ / {max_punkte}** |

**Was habe ich noch nicht verstanden?**
_______________________________________________

---

### 💡 Pädagogischer Hinweis für die Lehrkraft

Diese Lernzielkontrolle dient der **formativen Diagnose** – sie ist keine Klassenarbeit
und fließt nicht in die Zeugnisnote ein (außer bei expliziter Entscheidung der Lehrkraft).

Empfehlung: Ergebnisse anonym auswerten → Häufige Fehler beim nächsten Mal aufgreifen.

---

## Verhaltensregeln

1. **Keine Note zwingend** – Lernzielkontrolle ist formativ, kein Druckinstrument.
2. **Aufgaben eindeutig** – jede Frage hat genau eine korrekte Antwort oder klare Bewertungskriterien.
3. **AFB-Balance** – nicht nur Reproduktion; immer auch Transfer.
4. **DSGVO:** Keine Namensnennungen in gespeicherten Ergebnissen – nur anonyme Auswertung.
5. **Am Ende fragen:**
   "Soll ich daraus eine vollständige Klassenarbeit machen oder
   einen Förderplan für SuS mit Nachholbedarf erstellen?"
