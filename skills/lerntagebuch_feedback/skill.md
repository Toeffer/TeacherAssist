---
name: lerntagebuch_feedback
version: 1.0.0
author: LehrerAgent
description: Generiert kurze, individuelle Rückmeldungen auf SuS-Lerntagebucheinträge – wertschätzend, lernförderlich und DSGVO-konform (keine Namen gespeichert).
category: bildung
language: de
priority: 8

triggers:
  - "lerntagebuch"
  - "lerntagebuch feedback"
  - "reflexion der schüler"
  - "schüler reflexion kommentieren"
  - "rückmeldung lerntagebuch"
  - "kommentar auf reflexion"
  - "portfolio feedback"
  - "schülerantworten kommentieren"
  - "wochenrückblick feedback"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - eintrag
  optional:
    - klasse
    - fach
    - kontext
    - anzahl_feedbacks
    - feedbacktyp
---

# Skill: Lerntagebuch-Feedback generieren

## Zweck

Dieser Skill erstellt kurze, individuelle Rückmeldungen auf SuS-Lerntagebucheinträge,
Wochenrückblicke oder Portfolio-Reflexionen. Ziel: Die Lehrkraft gibt in kurzer Zeit
(< 2 Min pro SuS) eine lernwirksame Rückmeldung.

**Feedbacktypen:**
- **Bestätigend** – was die SuS gut erkannt hat, wird gespiegelt
- **Fragend** – eine weiterführende Frage öffnet neue Denkmöglichkeiten
- **Ermutigend** – bei negativen Selbstbewertungen Stärken sichtbar machen
- **Korrektiv** – sanfte Richtigstellung bei sachlichen Fehlern in der Reflexion

**DSGVO:** Lerntagebuchinhalte werden NICHT gespeichert. Nur die Rückmeldung wird ausgegeben.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Eintrag analysieren

Lies den übergebenen Lerntagebucheintrag sorgfältig.
Identifiziere:
- **Was hat das Kind/der/die Jugendliche erkannt?** (inhaltlich)
- **Welches Selbstbild zeigt sich?** (positiv, resigniert, übermäßig kritisch, realistisch)
- **Gibt es sachliche Fehler** in der Selbsteinschätzung?
- **Welche Frage könnte das Denken weiterentwickeln?**

### Schritt 2 – Feedbacktyp wählen

Wähle je nach Analyse automatisch den passenden Typ:
- Eintrag sehr positiv und inhaltlich korrekt → **Bestätigend + Fragend**
- Eintrag selbstkritisch aber fair → **Bestätigend + Ermutigend**
- Eintrag resigniert / negatives Selbstbild → **Ermutigend + Fragend**
- Eintrag enthält sachlichen Fehler → **Bestätigend + Korrektiv**

### Schritt 3 – Feedback formulieren

Feedback-Regeln:
- **Länge:** 3–5 Sätze (nicht mehr – sonst wird es nicht gelesen)
- **Anrede:** „Du" (Schüler/in direkt ansprechen)
- **Keine Note:** kein Vergleich mit anderen SuS
- **Konkret:** immer auf etwas Konkretes im Eintrag Bezug nehmen
- **Positiv beginnen:** immer mit etwas Anerkennungsvollem starten
- **Frage am Ende:** jedes Feedback endet mit einer offenen Frage

### Schritt 4 – Mehrere Einträge

Falls `anzahl_feedbacks` > 1: für jeden Eintrag einzeln wiederholen.
Reihenfolge beibehalten wie eingegeben.

---

## Ausgabeformat

---

### 💬 Rückmeldung auf Lerntagebucheintrag

*(Feedbacktyp: {bestätigend / fragend / ermutigend / korrektiv})*

---

{feedback_text}

*(3–5 Sätze, positive Eröffnung, konkreter Bezug, offene Frage am Ende)*

---

**Beispiel-Rückmeldungen nach Typ:**

**Bestätigend + Fragend:**
> „Du hast sehr treffend erkannt, dass der Übergang von der Schreibweise in
> Dezimalbrüche der schwierigste Teil war. Das zeigt, dass du genau weißt, wo
> du noch üben musst – das ist eine wichtige Fähigkeit! Was könntest du konkret
> anders machen, wenn du diesen Schritt das nächste Mal wieder üben willst?"

**Ermutigend:**
> „Ich lese heraus, dass du dir bei diesem Thema nicht so sicher bist.
> Schau dir noch einmal an, was du in deinem Eintrag selbst beschrieben hast –
> du hast den Ablauf eigentlich sehr gut erklärt! Manchmal fühlt sich etwas schwerer
> an, als es wirklich ist. Was war der Moment in der Stunde, wo es kurz mal
> ‚Klick' gemacht hat?"

**Korrektiv:**
> „Du schreibst, dass du bei Aufgabe 3 alles verstanden hast. Ich habe in deiner
> Lösung aber gesehen, dass beim letzten Schritt noch ein kleiner Denkfehler
> passiert ist – das ist ganz normal in dieser Phase. Was glaubst du: Wo genau
> liegt der Unterschied zwischen ‚fertig' und ‚richtig gelöst'?"

---

### 📊 Überblick (bei mehreren Einträgen)

*(nur wenn anzahl_feedbacks > 1)*

| SuS-ID | Feedbacktyp | Kernbotschaft |
|--------|------------|---------------|
| {id_1} | {typ} | {eine_zeile_zusammenfassung} |
| {id_2} | {typ} | {eine_zeile_zusammenfassung} |

**Auffälligkeiten für die Lehrkraft:**
{falls mehrere SuS denselben Fehler beschreiben: kurzer Hinweis "Thema X scheint mehreren SuS unklar"}

---

## Verhaltensregeln

1. **Kein Namenspeichern** – Lerntagebuchinhalte sind DSGVO-sensibel;
   falls Eintrag Namen enthält → intern ignorieren, nicht speichern, nicht wiederholen.
2. **Nie vergleichen** – kein „andere haben das besser gemacht".
3. **Nie abwerten** – keine Formulierungen die das Selbstbild beschädigen.
4. **Frage am Ende** – jedes Feedback endet mit einer offenen Frage; nie mit Auftrag.
5. **Am Ende fragen:**
   "Soll ich die Überblickstabelle als anonyme Notiz speichern,
   damit wir beim nächsten Mal sehen, was besser geworden ist?"
