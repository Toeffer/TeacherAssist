---
name: vertretungsstunde
version: 1.0.0
author: LehrerAgent
description: Erstellt in 2 Minuten einen einsatzbereiten Vertretungsplan für eine Stunde – mit minimaler Vorbereitung, ohne Vorwissen über den aktuellen Stand der Klasse.
category: bildung
language: de
priority: 20

triggers:
  - "vertretungsstunde"
  - "vertretung"
  - "ich muss eine klasse vertreten"
  - "spontaner unterricht"
  - "crashplan"
  - "stunde ohne vorbereitung"
  - "überbrückungsstunde"
  - "fremde klasse"
  - "einspringen"
  - "kurzer plan"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - fach_oder_thema
    - klasse
  optional:
    - zeitstunden
    - materialverfuegbar
    - digitale_ausstattung
---

# Skill: Vertretungsstunde planen

## Zweck

Dieser Skill erstellt einen sofort einsetzbaren Vertretungsplan für eine unbekannte Klasse.
Ziel: In 5 Minuten eine sinnvolle, ruhig verlaufende Stunde stehen haben –
ohne Kenntnis des aktuellen Unterrichtsstands, ohne spezifische Materialien.

**Grundprinzip:** Lieber einen guten Einstieg mit offener Erarbeitungsphase als
einen übertakteten Plan, der durch fehlendes Vorwissen scheitert.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Situation erfassen

Frage falls nicht angegeben:
```
Für welche Klasse und welches Fach? Und: Wie lange dauert die Stunde?
Hast du Zugang zu Arbeitsblättern / digitalen Geräten?
```

Falls Fach nicht zur Kompetenz der Vertretungslehrkraft passt:
→ Fächerübergreifende Alternativen anbieten (Lesen, Diskussion, stilles Arbeiten).

### Schritt 2 – Strategie wählen

**Strategie A – Fachinhaltlich (wenn Fach bekannt):**
Wähle ein Thema, das keine Vorkenntnisse aus dem aktuellen Unterricht voraussetzt.
Geeignet: Wiederholungen, Grundprinzipien, Anwendungsaufgaben.

**Strategie B – Fächerübergreifend (wenn Fach fremd):**
Wähle aus: Lektüre + Diskussion, kreatives Schreiben, Denksport/Rätsel, stummes Plakat,
Lernkartenarbeit zu beliebigem Thema.

**Strategie C – Strukturiert still (Notfall):**
Stille Einzelarbeit mit klarer Aufgabenstellung → gut für unruhige Klassen.

### Schritt 3 – Plan erstellen

Erstelle sofort einsetzbaren Plan nach Ausgabeformat.
Keine langen Erklärungen – die Lehrkraft braucht konkrete Handlungsanweisungen.

---

## Ausgabeformat

---

### ⚡ Vertretungsplan

**Klasse:** {klasse}
**Fach / Thema:** {fach_oder_thema}
**Dauer:** {zeitstunden} Minuten
**Strategie:** {A / B / C}

---

### ✅ Was du sofort brauchst

- {material_1} *(z. B. Tafel/Whiteboard + Kreide/Marker)*
- {material_2}
- *(optional: {material_3})*

---

### ⏱️ Ablauf

**0–5 Min – Ankommen & Orientierung**
Begrüße die Klasse, stelle dich kurz vor. Erkläre klar die Stunde:
> „Ich vertrete heute {lehrkraft_optional}. Wir machen heute {kurzbeschreibung}.
> Ihr braucht: {materialien}. Bitte {sitzordnung_hinweis}."

---

**5–{t2} Min – Einstieg**
{konkrete Einstiegsaufgabe oder Impuls – muss ohne Vorwissen funktionieren}

Mögliche Einstiege:
- Frage an die Klasse: „{offene_frage_zum_thema}"
- Bild / Zitat / Phänomen an die Tafel schreiben
- Quiz-Frage mit Abstimmung (Handzeichen)

---

**{t2}–{t3} Min – Erarbeitung**
{konkrete Aufgabe die die SuS selbstständig bearbeiten können}

Aufgabenstellung für die Tafel / Ausgabe:
```
{aufgabentext – kopierfertig, klar formuliert}
```

---

**{t3}–{t4} Min – Ergebnissicherung**
{wie werden Ergebnisse vorgestellt / besprochen}
Möglichkeit: 2–3 SuS vorstellen lassen, kurzes Unterrichtsgespräch, Tafelanschrieb.

---

**{t4}–Ende – Puffer + Abschluss**
Pufferaufgabe falls Zeit übrig:
> {pufferaufgabe – z. B. Mindmap, Zusammenfassung, Weiterdenken}

Abschluss: Kurzes Feedback von den SuS (Daumen hoch/mittel/runter) oder kurze Reflexionsfrage.

---

### 🛑 Klassenmanagement-Tipps

- **Namen nicht nötig:** Zeige Präsenz, stelle klare Erwartungen zu Beginn.
- **Bei Unruhe:** Stille Einzelarbeit anordnen, 5 Minuten warten, dann fortfahren.
- **Bei zu schnell fertig:** Immer eine Puffer-/Zusatzaufgabe parat haben (s. o.).
- **Bei Widerstand:** Nicht eskalieren – schriftliche Aufgabe anordnen und Vorfall notieren.

---

### 📝 Notizen für die Klassenleitung

*(bitte nach der Stunde ausfüllen und im Lehrerzimmer hinterlassen oder an KL weiterleiten)*

| | |
|---|---|
| Klasse | {klasse} |
| Datum / Stunde | |
| Vertretungslehrkraft | |
| Verlauf | ☐ reibungslos  ☐ kleinere Störungen  ☐ größere Probleme |
| Besonderheiten | |

---

## Verhaltensregeln

1. **Kein Vorwissen voraussetzen** – Plan muss für jede Klasse im Fach funktionieren.
2. **Maximal 2 Materialien** – nichts was erst kopiert/gedruckt werden muss.
3. **Puffer immer einbauen** – Vertretungsstunden sind selten optimal getaktet.
4. **Ton:** pragmatisch und direkt – die Lehrkraft hat keine Zeit für Theorie.
5. **Am Ende fragen:**
   "Soll ich auch ein Arbeitsblatt für diese Stunde erstellen?
   Das kann ich in 2 Minuten fertigmachen."
