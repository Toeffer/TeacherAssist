---
name: arbeitsblatt_erstellen
version: 1.0.0
author: LehrerAgent
description: >
  Erstellt ein druckfertiges, lehrplankonformes Arbeitsblatt mit Aufgaben,
  Differenzierung und optionaler Musterlösung – für Übung, Hausaufgaben oder
  Stundeneinstiege.
category: bildung
language: de
priority: 10

triggers:
  - "erstelle ein arbeitsblatt"
  - "arbeitsblatt"
  - "aufgabenblatt"
  - "übungsblatt"
  - "aufgaben für klasse"
  - "aufgaben zu"
  - "hausaufgaben erstellen"
  - "übungsaufgaben"
  - "lernblatt"
  - "aufgabenstellung erstellen"
  - "ich brauche aufgaben"

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
    - aufgabenanzahl      # Standard: 4–6
    - schwierigkeitsgrad  # einfach | mittel | herausfordernd | gemischt (Standard: gemischt)
    - zeitrahmen          # Standard: 45 Minuten (oder "Hausaufgabe")
    - differenzierung     # ja | nein (Standard: ja)
    - art                 # übung | einstieg | sicherung | hausaufgabe | test (Standard: übung)
    - mit_loesungen       # ja | nein (Standard: nein)
    - afb_schwerpunkt     # I | II | III | gemischt (Standard: gemischt)
---

# Skill: Arbeitsblatt erstellen

## Zweck

Dieser Skill generiert ein vollständiges, druckfertiges Arbeitsblatt für eine
Lehrkraft. Es berücksichtigt Fach, Klasse, Thema, Lehrplanbezug, Differenzierung
und die gewünschte Aufgabenart.

Das Ergebnis ist sofort einsetzbar – ggf. mit einem Klick exportierbar.

---

## Ablauf

### Schritt 1 – Lehrerprofil laden

Lade `lehrerprofil.md` und prüfe:
- Bundesland → beeinflusst Lehrplanbezug und Terminologie
- Schulform → beeinflusst Schwierigkeitsniveau
- Bevorzugte Methoden → beeinflusst Aufgabenformat

### Schritt 2 – Fehlende Parameter erfragen

Falls `fach` oder `klasse` fehlen:
```
Für welches Fach und welche Klasse soll ich das Arbeitsblatt erstellen?
```

Falls `thema` fehlt:
```
Was ist das Thema des Arbeitsblattes?
(z.B. "Bruchrechnung", "Klimawandel", "Gedichtanalyse")
```

Falls `art` nicht klar ist, frage gezielt:
```
Was soll das Arbeitsblatt leisten?
  1 – Übungsaufgaben (Erarbeitung / Vertiefung)
  2 – Hausaufgaben
  3 – Stundeneinstieg / Wiederholung
  4 – Leistungsnachweis / kurzer Test
```

Falls `mit_loesungen` nicht genannt: frage:
```
Soll ich auch eine Musterlösung / Lösungsseite anhängen?
(Gut für deine Korrekturhilfe oder für differenzierte SuS)
```

### Schritt 3 – Lehrplanbezug herstellen

Suche in `lehrplan_index.md` nach dem passenden Eintrag für
`{fach}` + `{klasse}` + `{bundesland}`.

Falls kein Eintrag: formuliere kompetenzorientierten Bezug nach deutschen
Bildungsstandards, markiere ihn mit `[*]`.

### Schritt 4 – Aufgaben generieren

Erstelle die Aufgaben nach diesem Prinzip:
- **AFB I (Reproduktion):** ~30% – Fakten nennen, Grundbegriffe, einfaches Anwenden
- **AFB II (Reorganisation):** ~40% – Zusammenhänge erklären, Anwenden auf neuen Kontext
- **AFB III (Transfer):** ~30% – Beurteilen, vergleichen, kreativ gestalten, übertragen

Bei `differenzierung: ja` (Standard):
- **Pflichtaufgaben:** für alle SuS (AFB I + II)
- **Zusatzaufgaben (★):** für schnelle/leistungsstarke SuS (AFB III)
- **Hilfestellungen (✦):** optional – Tipp-Kästen für SuS mit Förderbedarf

### Schritt 5 – Arbeitsblatt im Ausgabeformat erstellen

Erstelle das vollständige Arbeitsblatt (siehe Ausgabeformat unten).

### Schritt 6 – Angebot am Ende

```
✅ Das Arbeitsblatt ist fertig!

Du kannst es direkt ausdrucken – klicke dazu auf den 📄-Button
unter dieser Nachricht.

Soll ich noch:
• Ein Bewertungsraster für dieses Arbeitsblatt erstellen?
• Die Musterlösung ergänzen?
• Eine vereinfachte Version für SuS mit Förderbedarf erstellen?
```

---

## Ausgabeformat

Das Arbeitsblatt folgt exakt dieser Struktur:

---

# Arbeitsblatt: {thema}

**Fach:** {fach} | **Klasse:** {klasse} | **Datum:** ________________

**Name:** _______________________________ | **Punkte:** _______ / {gesamtpunkte}

---

### Lernziele

> Nach diesem Arbeitsblatt kannst du…
> - {lernziel_1} (AFB I)
> - {lernziel_2} (AFB II)
> - {lernziel_3} (AFB III)

*Lehrplanbezug: {lehrplanstelle_oder_sternchen}*

---

### Aufgabe 1 – {kurztitel} ({punkte} Punkte) | AFB {I/II/III}

{aufgabenstellung – präzise, schülergerecht formuliert}

{ggf. Informationstext, Quelle, Tabelle, Diagrammbeschreibung}

_____________________________________________
_____________________________________________
_____________________________________________

---

### Aufgabe 2 – {kurztitel} ({punkte} Punkte) | AFB {I/II/III}

{aufgabenstellung}

*(bei Bedarf: Lösungsraum als Linien, Tabelle, Diagramm-Skizze)*

---

*(weitere Aufgaben nach demselben Schema)*

---

### ★ Zusatzaufgabe (für schnelle SuS) – ({punkte} Punkte) | AFB III

{anspruchsvollere Aufgabe, die über den Pflichtteil hinausgeht}

---

### ✦ Tipp-Kasten (bei Bedarf)

> 💡 **Hilfe zu Aufgabe {nr}:** {konkreter Hinweis, der den Denkprozess anstößt}

---

### Übersicht

| Aufgabe | Punkte | AFB | Erledigt? |
|---------|--------|-----|-----------|
| 1 | {p} | {afb} | ☐ |
| 2 | {p} | {afb} | ☐ |
| ★ Zusatz | {p} | III | ☐ |
| **Gesamt** | **{gesamt}** | | |

---

*(Wenn `mit_loesungen: ja`: Musterlösung als eigener Abschnitt nach Seitenumbruch)*

---

### Musterlösung *(nur für Lehrkraft)*

**Aufgabe 1:** {vollständige Lösung}
**Aufgabe 2:** {vollständige Lösung}
…

---

## Verhaltensregeln

1. **Aufgabenstellungen schülergerecht** – klare Operatoren, keine Doppeldeutigkeit.
   - Reproduktion: „Nenne", „Beschreibe", „Berechne", „Ordne zu"
   - Reorganisation: „Erkläre", „Vergleiche", „Analysiere", „Stelle dar"
   - Transfer: „Beurteile", „Entwickle", „Übertrage", „Gestalte"

2. **Punkte realistisch** – pro Aufgabe 1–10 Punkte, Gesamtpunkte i.d.R. 20–50.

3. **Lösungsraum planen** – genug Platz unter jeder Aufgabe vorsehen.

4. **Differenzierung einbauen** – Zusatzaufgaben (★) für alle, Tipp-Kästen (✦) für
   SuS mit Förderbedarf.

5. **Ton:** sachlich-freundlich, direkte Ansprache der SuS mit "du"/"ihr".

6. **Am Ende anbieten:** Export-Hinweis, Musterlösung, Bewertungsraster.
