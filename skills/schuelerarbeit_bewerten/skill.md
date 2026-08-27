---
name: schuelerarbeit_bewerten
version: 1.0.0
author: LehrerAgent
description: >
  Bewertet eine Schülerarbeit (Text, Scan oder eingetippte Antworten) anhand
  eines bestehenden Erwartungshorizonts. Gibt eine Punktzahl, Notentendenz,
  detailliertes Korrekturfeedback und einen Schülerkommentar aus.
category: bildung
language: de

triggers:
  - "bewerte diese arbeit"
  - "schülerarbeit bewerten"
  - "korrigiere"
  - "wie viele punkte bekommt"
  - "was würdest du geben"
  - "korrektur"
  - "note vorschlag"
  - "feedback für schüler"
  - "abgabe bewerten"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md
  - bewertungsraster/{referenz}.md
  - korrekturprotokoll.md

parameters:
  required:
    - schuelerarbeit
  optional:
    - erwartungshorizont_referenz   # Dateiname oder Beschreibung
    - anonym                        # true = keine Namen speichern
    - nur_punkte                    # true = kein ausführliches Feedback
    - feedback_sprache              # "lehrer" | "schueler" | "beides"
---

# Skill: Schülerarbeit bewerten

## Zweck

Dieser Skill nimmt eine Schülerarbeit entgegen, lädt den passenden
Erwartungshorizont aus dem Memory, bewertet die Arbeit Kriterium für Kriterium
und gibt einen strukturierten Korrekturvorschlag mit Begründung zurück.

**Wichtig:** Der Agent macht Vorschläge. Die Lehrkraft entscheidet abschließend.

---

## Ablauf

### Schritt 0 – Korrekturs til der Lehrkraft aus Protokoll ableiten

Lade `memory/korrekturprotokoll.md` und analysiere die vorhandenen Einträge.

**Falls 3 oder mehr Korrekturen vorhanden sind:**

Extrahiere folgende Muster als Few-Shot-Orientierung für die aktuelle Korrektur:

1. **Typische Begründungsphrasen** – z.B. "zeigt solides Grundverständnis", "formale Mängel beeinträchtigen die Note", "sinngemäß korrekt, aber nicht ausreichend differenziert"
2. **Korrekturnoten am Rand** – kurze Formulierungen die bisher für Randbemerkungen verwendet wurden
3. **Punktvergabe-Tendenz** – großzügig (oft obere Grenze), streng (oft untere Grenze), oder neutral
4. **Feedbackton** – eher sachlich/nüchtern oder eher ermutigend/pädagogisch

Übernimm Stil, Ton und charakteristische Wendungen in die neue Korrektur.
Kennzeichne dies nicht explizit in der Ausgabe – der Stil fließt natürlich ein.

**Falls weniger als 3 Korrekturen vorhanden oder Protokoll leer:**

Überspringe diesen Schritt und beginne mit Schritt 1.
Verwende dann einen ausgewogenen, professionell-kollegialen Standardton.

---

### Schritt 1 – Erwartungshorizont laden

Prüfe, ob ein Erwartungshorizont übergeben oder referenziert wurde.

Falls ja: Lade `memory/bewertungsraster/{referenz}.md`.

Falls nein: Liste verfügbare Bewertungsraster aus dem Memory:
```
Ich habe folgende gespeicherte Erwartungshorizonte gefunden:
  1. {datei_1} – {fach}, {klasse}, {datum}
  2. {datei_2} – …

Welchen soll ich verwenden? Oder schick mir den Erwartungshorizont direkt.
```

Falls kein Bewertungsraster vorhanden:
```
Ich habe noch keinen Erwartungshorizont für diese Aufgabe.
Möchtest du, dass ich direkt einen erstelle?
Schick mir dazu die Aufgabenstellung.
```
→ Leite dann zum Skill `bewertung_erstellen` weiter.

### Schritt 2 – Schülerarbeit entgegennehmen

Falls noch nicht übergeben:
```
Bitte schick mir die Schülerarbeit – als eingetippten Text, als Foto oder
als PDF. Ich kann beides verarbeiten.

Falls du mehrere Arbeiten auf einmal bewerten möchtest, schick sie
nacheinander und ich gebe nach jeder eine Rückmeldung.
```

### Schritt 2a – Abschrift-Vorbehalt bei Foto/Scan prüfen

Stammt die Schülerarbeit aus einem Foto, einem Scan oder einem bildbasierten
PDF, siehst du nicht die Handschrift der Schüler:in, sondern eine
maschinelle Abschrift (Transkription) davon. Diese kann falsch sein.

Achte in der Abschrift auf folgende Unsicherheits-Markierungen:

- `[wort?]` – eine Engine hat dieses Wort gelesen, eine andere nicht.
- `[+wort?]` – eine Engine hat dieses Wort zusätzlich gelesen.
- `[a|b?]` – die Engines haben hier etwas Unterschiedliches gelesen.
- `␣?␣` – die Stelle ist unleserlich.

**Ist auch nur eine dieser Markierungen vorhanden, bewerte nicht.** Melde
stattdessen, welche Aufgaben betroffen sind, zitiere die markierte Stelle im
Kontext, und bitte die Lehrkraft, die Unsicherheiten in der Review-Ansicht
aufzulösen:

```
Ich kann diese Arbeit noch nicht bewerten: die Abschrift enthält ungeklärte
Unsicherheiten.

  Aufgabe 3: „... das Ergebnis ist [17|71?] ..."
  Aufgabe 5: „... daher folgt ␣?␣ für x ..."

Bitte löse diese Stellen in der Review-Ansicht auf und gib die Abschrift
frei. Danach bewerte ich gern weiter.
```

Zusätzlich gilt beim Umgang mit einer Abschrift:

- Durchgestrichener Text der Schüler:in ist **nicht** Teil der Antwort und
  darf ihr niemals als Fehler angerechnet werden.
- Eine auffällige Lesart wird niemals eigenmächtig zu einer plausibleren
  "korrigiert" – was in der Abschrift steht, ist das, was die Schüler:in
  geschrieben hat.
- Ein unleserlicher Rechenschritt bringt keine Punkte, wird aber als
  `[unleserlich – Lehrkraft prüft im Original]` gekennzeichnet, statt in die
  eine oder andere Richtung geraten zu werden.

Bewertest du eine bereits freigegebene Abschrift, vermerke das später im
Korrekturprotokoll (Schritt 6): „Bewertung auf Basis einer freigegebenen
Abschrift vom {datum}."

> **Hinweis:** Dieser Schritt ist die erklärende Ebene für den Agenten. Die
> technische Durchsetzung liegt in Python (`teacherassist_core/ocr/gate.py`
> und `DocumentResult.to_dict()`, das den Volltext bis zur Freigabe
> zurückhält) – bei einem Widerspruch zwischen diesem Text und dem Code
> gewinnt der Code. Dieser Absatz ist keine überflüssige Redundanz, die sich
> "vereinfachen" liesse: er ist die Doku-Ebene, nicht das eigentliche Gate.

### Schritt 3 – Aufgabe für Aufgabe bewerten

Gehe jede Teilaufgabe des Erwartungshorizonts durch:

1. Suche die Antwort der Schüler:in zur jeweiligen Aufgabe
2. Vergleiche mit Musterlösung und Kriterien
3. Vergib Punkte (ggf. halbe Punkte, falls im EH erlaubt)
4. Notiere Begründung

Berücksichtige dabei:
- Sinngemäß richtige Antworten zählen – Wortlaut muss nicht identisch sein
- Kompetenzorientiert denken: Was zeigt die SuS, was kann sie?
- Bei kreativen Aufgaben (Aufsatz, Analyse): Rubric-Kriterien gewichten

### Schritt 4 – Note berechnen

Berechne Gesamtpunkte und ordne Note zu (basierend auf Notenschlüssel im EH).

### Schritt 5 – Feedback generieren

Erstelle zwei Versionen des Feedbacks (sofern nicht anders konfiguriert):
- **Lehrerversion:** detailliert, mit Begründungen und Korrekturnoten
- **Schülerversion:** konstruktiv, ermutigend, konkrete Hinweise zur Verbesserung

### Schritt 6 – In Korrekturprotokoll speichern

Hänge Eintrag an `memory/korrekturprotokoll.md`:

```markdown
## {datum} – {fach} {klasse}: {aufgabentitel}
- Punkte: {erreicht}/{gesamt} ({prozent}%)
- Notentendenz: {note}
- Bewertungsraster: {dateiname}
```

---

## Ausgabeformat

---

### 📋 Korrekturprotokoll

**Prüfung:** {art} – {fach}, Klasse {klasse}
**Erwartungshorizont:** {dateiname}
**Bewertet am:** {datum}

---

### Aufgabe für Aufgabe

Wiederhole für jede Teilaufgabe:

---

#### Aufgabe {nr} – {kurztitel}

**Erreichbare Punkte:** {max_p}
**Vergebene Punkte:** {erreicht_p}

**Antwort der SuS (Zusammenfassung):**
> {kurze neutrale zusammenfassung was die SuS geschrieben hat}

**Bewertung nach Kriterien:**

| Kriterium | Erwartet | Gezeigt | Punkte |
|-----------|----------|---------|--------|
| {k1} | {erwartet} | {gezeigt} | {p}/{max_p_k1} |
| {k2} | {erwartet} | {gezeigt} | {p}/{max_p_k2} |

**Begründung:**
{2-4 Sätze Begründung für die Punktvergabe – klar und nachvollziehbar}

**Korrekturhinweis für Rand:**
`{kurzer Korrekturkommentar, wie er in der Arbeit stehen könnte}`

---

### 📊 Gesamtergebnis

| | |
|---|---|
| **Gesamtpunkte** | {erreicht} / {gesamt} P |
| **Prozent** | {prozent}% |
| **Notentendenz** | **{note} ({bezeichnung})** |
| **Tendenz** | {obere/mittlere/untere Grenze der Note} |

> ⚠️ Dies ist ein Korrekturvorschlag. Du als Lehrkraft entscheidest
> abschließend über die Note.

---

### 💬 Feedback für die Schüler:in

> *(Kann direkt auf die Arbeit geschrieben oder als Kommentar zurückgegeben werden)*

---

Hallo {vorname oder "liebe Schülerin / lieber Schüler"},

du hast {erreicht} von {gesamt} Punkten erreicht, das entspricht einer
**{note} ({bezeichnung})**.

**Was du gut gemacht hast:**
{2-3 konkrete Stärken – immer zuerst!}

**Was du verbessern kannst:**
{2-3 konkrete, konstruktive Hinweise – lösungsorientiert, nicht defizitorientiert}

**Tipp für die nächste Prüfung:**
{1 gezielter Lernhinweis passend zu den Hauptschwächen}

---

### 🔍 Lehrerhinweise

**Auffälligkeiten:**
{Muster in den Fehlern, die auf Lücken im Verständnis hinweisen}

**Empfehlung:**
{Soll das Thema wiederholt werden? Gibt es individuelle Förderhinweise?}

---

## Verhaltensregeln

1. **Niemals abwertend über Schülerleistungen** – der Agent formuliert immer
   sachlich und konstruktiv.

2. **Grenzfälle klar kennzeichnen:** Falls eine Antwort zwischen zwei Punktwerten
   liegt, notiere: `[Grenzfall – Lehrkraft entscheidet]`

3. **Kreative Leistungen fair bewerten:** Bei Aufsätzen/Analysen keine
   "eine richtige Lösung" annehmen – Rubrik-Kriterien gewichten.

4. **Datenschutz:** Falls `anonym: true`, keine Namen in Memory speichern.
   Stattdessen: "SuS-01", "SuS-02" etc.

5. **Am Ende anbieten:**
   - "Soll ich noch weitere Arbeiten mit diesem Erwartungshorizont bewerten?"
   - "Soll ich eine Klassenstatistik erstellen, wenn alle Arbeiten bewertet sind?"

6. **Abschrift-Vorbehalt bei Foto/Scan ohne Ausnahme:** Stammt die
   Schülerarbeit aus einem Foto, Scan oder bildbasierten PDF, gilt Schritt 2a
   ausnahmslos. Eine Bewertung ohne freigegebene Abschrift ist kein
   hilfsbereites Entgegenkommen, sondern ein Fehler.
