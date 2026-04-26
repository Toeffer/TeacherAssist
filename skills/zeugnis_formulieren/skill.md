---
name: zeugnis_formulieren
version: 1.0.0
author: LehrerAgent
description: >
  Generiert professionelle, pädagogisch korrekte Zeugnisformulierungen für
  Halbjahres- und Jahreszeugnisse – anhand kurzer Stichworte der Lehrkraft,
  stilsicher und für alle Noten / Leistungsniveaus.
category: bildung
language: de
priority: 10

triggers:
  - "zeugnis"
  - "zeugnistext"
  - "zeugnisformulierung"
  - "zeugnisse schreiben"
  - "bemerkungen für zeugnis"
  - "zeugnis formulieren"
  - "zeugnistexte"
  - "beurteilung für zeugnis"
  - "halbjahreszeugnis"
  - "jahreszeugnis"
  - "schulbericht"
  - "lernentwicklungsbericht"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - note_oder_niveau     # 1–6 oder "sehr gut" / "gut" / "ausreichend" usw.
    - fach
  optional:
    - klasse
    - staerken             # Stichworte: was das Kind gut kann
    - schwaechen           # Stichworte: wo Entwicklungsbedarf besteht
    - verhalten            # aufmerksam | ablenkend | kooperativ | ruhig | lebhaft
    - mitarbeit            # aktiv | regelmäßig | selten | ausbaufähig
    - besonderheiten       # z. B. Sprachentwicklung, Freude am Lesen, Mathe-Stärke
    - art                  # halbjahr | jahr | lernentwicklung (Standard: jahr)
    - anzahl               # wie viele Formulierungsvorschläge (Standard: 3)
    - klasse_stufe         # Grundschule | Mittelstufe | Oberstufe (aus Profil)
---

# Skill: Zeugnisformulierungen erstellen

## Zweck

Dieser Skill nimmt kurze Stichworte der Lehrkraft über einen Schüler / eine
Schülerin entgegen und formuliert daraus mehrere stilsichere, pädagogisch
korrekte Zeugnistexte – angepasst an Note, Schulform und Zeugnisart.

**DSGVO:** Der Agent speichert KEINE Schülernamen. Die Formulierungen werden
in der Chat-Antwort ausgegeben und können von der Lehrkraft kopiert werden.
Pronomen werden als {er/sie} angegeben – Lehrkraft ersetzt sie manuell.

---

## Ablauf

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md`:
- Schulform → beeinflusst Ton und Formulierungstiefe
- Bundesland → ggf. Lehrplan-Terminologie

### Schritt 2 – Fehlende Parameter erfragen

Falls `note_oder_niveau` fehlt:
```
Welche Note hat das Kind in {fach} erhalten?
(1–6 oder "sehr gut" / "gut" / "befriedigend" / "ausreichend" / "mangelhaft")
```

Falls `fach` fehlt:
```
Für welches Fach benötigst du die Formulierung?
```

Falls noch keine Stichworte zu Stärken/Verhalten gegeben:
```
Nenn mir kurz 2–3 Stichworte zum Kind – was fällt dir auf?
(z. B. "liest gern, Rechnen schwächer, arbeitet fleißig mit")
Das muss kein vollständiger Satz sein.
```

Falls `anzahl` nicht genannt: erstelle **3 Varianten** mit unterschiedlichem Fokus.

### Schritt 3 – Formulierungen generieren

Beachte beim Formulieren:

**Sprachliche Regeln für Zeugnisse:**
- Keine Verneinungen ("nicht", "kein") als Hauptaussage → immer positiv umformulieren
- Keine Diagnosen oder medizinischen Begriffe
- Keine direkten Notenverweise im Fließtext ("Note 3") → stattdessen: "befriedigend", "sicher"
- Keine Füllwörter wie "sehr", "sehr gut" ohne inhaltliche Substanz
- Keine Vergleiche mit anderen Schülern
- Indikativ (nicht Konjunktiv): "zeigt Interesse" – nicht "würde zeigen"
- Keine negativen Zuschreibungen ("faul", "schwierig", "problematisch")

**Formelhafte Bausteine je Note:**

Note 1 / sehr gut:
- "zeigt hervorragendes Verständnis"
- "bewältigt auch komplexe Aufgaben souverän"
- "engagiert sich vorbildlich"

Note 2 / gut:
- "zeigt ein sicheres Verständnis"
- "arbeitet zuverlässig und sorgfältig"
- "beteiligt sich regelmäßig und konstruktiv"

Note 3 / befriedigend:
- "verfügt über solide Grundkenntnisse"
- "arbeitet mit erkennbarem Einsatz"
- "beteiligt sich bei geeigneten Aufgabenstellungen"

Note 4 / ausreichend:
- "verfügt über grundlegende Kenntnisse"
- "kann einfache Aufgaben in der Regel lösen"
- "Ausdauer und Konzentration können noch ausgebaut werden"

Note 5 / mangelhaft:
- "zeigt erste Ansätze des Verständnisses"
- "benötigt für die Aufgabenbewältigung häufig Unterstützung"
- "Es bestehen noch Lücken, die durch regelmäßiges Üben geschlossen werden können"

Note 6 / ungenügend:
- "konnte die Mindestanforderungen trotz Unterstützung nicht erfüllen"
- "benötigt intensive Förderung in den grundlegenden Bereichen"

### Schritt 4 – Varianten ausgeben

Gib die vereinbarte Anzahl Varianten aus (Standard: 3), mit kurzem Label:
- **Variante A – Kompakt** (2–3 Sätze): Für Schulformen mit knappem Raum
- **Variante B – Ausführlich** (4–5 Sätze): Mit Stärken, Entwicklung, Ausblick
- **Variante C – Entwicklungsorientiert** (3–4 Sätze): Fokus auf Potential und Wachstum

### Schritt 5 – Angebot am Ende

```
✅ Hier sind {anzahl} Formulierungsvorschläge für {fach}.

Ersetze {er/sie/es} mit dem richtigen Pronomen.
Klicke auf den 📄-Button, um sie zum Kopieren geöffnet zu bekommen.

Soll ich noch:
• Eine weitere Variante mit anderem Fokus erstellen?
• Formulierungen für weitere Fächer / SuS generieren?
• Den Ton anpassen (formeller / wärmer)?
```

---

## Ausgabeformat

---

### Zeugnisformulierungen – {fach}, Note {note_oder_niveau}

*Stichworte: {zusammenfassung_der_eingabe}*

---

**Variante A – Kompakt**

{formulierung_a – 2–3 Sätze, alle Pronomen als {er/sie}}

---

**Variante B – Ausführlich**

{formulierung_b – 4–5 Sätze mit Stärken, Verhalten, Entwicklungshinweis}

---

**Variante C – Entwicklungsorientiert**

{formulierung_c – 3–4 Sätze, Fokus auf Potential und nächste Schritte}

---

> 💡 **Hinweis:** Alle Pronomen sind als {er/sie} markiert.
> Bitte manuell anpassen. Keine Schülernamen in diesem Dokument.

---

## Verhaltensregeln

1. **Niemals Schülernamen verwenden oder nachfragen** – Anonymität ist Pflicht.
   Pronomen neutral lassen: {er/sie/es} oder "das Kind", "die Schülerin".

2. **Keine negativen Zuschreibungen** – selbst bei Note 5/6 formuliert man
   das Defizit als Entwicklungspotenzial, nicht als Versagen.

3. **Keine Diagnosen** – "hat Schwierigkeiten beim Lesen" statt "ist Legastheniker".
   Keine Verweise auf vermutete LRS, ADHS o. ä.

4. **Varianten immer mit unterschiedlichem Fokus** – nicht drei fast identische Texte.

5. **Schulform beachten:**
   - Grundschule: wärmer, entwicklungsorientiert, wenig Fachsprache
   - Haupt-/Realschule: kompetenzorientiert, praxisnah
   - Gymnasium: sachlich, kompetenzorientiert, mit Fachbegriffen

6. **Immer anbieten**, den Text weiter anzupassen – Lehrkräfte kennen das Kind.
