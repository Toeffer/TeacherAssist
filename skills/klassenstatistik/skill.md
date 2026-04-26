---
name: klassenstatistik
version: 1.0.0
author: LehrerAgent
description: >
  Wertet Klassenleistungen statistisch aus: Durchschnitt, Notenverteilung,
  Vergleich Stärken/Schwächen pro Aufgabe – für Klassenarbeiten, Tests und
  Noten. Erstellt übersichtliche Auswertungstabellen und pädagogische Hinweise.
category: bildung
language: de
priority: 8

triggers:
  - "klassenstatistik"
  - "notenverteilung"
  - "klassendurchschnitt"
  - "auswertung klassenarbeit"
  - "ergebnisse auswerten"
  - "wie hat die klasse abgeschnitten"
  - "notenspiegel"
  - "leistungsübersicht"
  - "ergebnisanalyse"
  - "punkte auswerten"
  - "statistik klasse"
  - "klassenarbeit auswerten"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - daten               # Punktzahlen oder Noten der Klasse (als Liste)
  optional:
    - fach
    - klasse
    - thema               # Name der Prüfung / Klassenarbeit
    - gesamtpunkte        # Maximalpunktzahl (für Prozent-Berechnung)
    - notenschluessel     # standard | mild | verschaerft (Standard: standard)
    - aufgaben_punkte     # Punkte pro Aufgabe (für Aufgaben-Analyse)
    - datum               # Datum der Prüfung
    - vergleich_vorher    # frühere Durchschnittsnote zum Vergleich
---

# Skill: Klassenstatistik / Notenauswertung

## Zweck

Dieser Skill nimmt die Ergebnisse einer Klasse entgegen (Punkte oder Noten)
und erstellt eine vollständige statistische Auswertung mit Notenspiegel,
Durchschnitt, Streuung und pädagogischen Handlungsempfehlungen.

**DSGVO:** Keine Schülernamen in der Auswertung – nur anonyme Punktelisten.
Die Lehrkraft gibt die Zahlen ein; der Agent rechnet und visualisiert.

---

## Ablauf

### Schritt 1 – Kontext laden

Lade `lehrerprofil.md` für Schulform und bevorzugten Notenschlüssel.

### Schritt 2 – Daten entgegennehmen

Falls noch keine Daten vorliegen:
```
Gib mir die Punktzahlen (oder Noten) der Klasse – einfach als Liste,
z. B.: 38, 42, 17, 29, 45, 31, 22, 48, 35, 40, 27, 33, 19, 44, 36

Oder wenn du Noten hast: 2, 3, 4, 1, 3, 2, 5, 2, 3, 4
```

Falls `gesamtpunkte` fehlt aber Punktzahlen eingegeben wurden:
```
Wie viele Punkte waren maximal erreichbar?
```

Falls `aufgaben_punkte` vorhanden (z. B. "Aufg. 1: 8P, Aufg. 2: 12P, Aufg. 3: 15P, Aufg. 4: 15P"):
Berechne zusätzlich die aufgabenspezifische Lösungsquote.

### Schritt 3 – Statistik berechnen

Berechne folgende Kennzahlen:

**Grundstatistik:**
- Anzahl SuS (n)
- Minimum / Maximum
- Spannweite (Max – Min)
- Arithmetischer Mittelwert (Durchschnitt)
- Median (mittlerer Wert nach Sortierung)
- Standardabweichung (σ) – vereinfacht: zeige ob Klasse homogen oder heterogen

**Notenverteilung:**
Rechne jeden Punktwert in eine Note um (nach gewähltem Notenschlüssel).
Zähle: wie viele SuS haben Note 1, 2, 3, 4, 5, 6?

**Bestandsquote:**
Wie viele SuS haben bestanden (Note 1–4)? Prozentsatz angeben.

**Aufgaben-Analyse** (nur wenn `aufgaben_punkte` vorliegt):
Für jede Aufgabe: Summe der erreichten Punkte ÷ (n × max_punkte_aufgabe) = Lösungsquote
→ Zeigt, welche Aufgaben zu schwer / zu leicht waren.

### Schritt 4 – Auswertung erstellen

Erstelle die vollständige Auswertung im Ausgabeformat (siehe unten).

### Schritt 5 – Pädagogische Einordnung

Basierend auf den Ergebnissen:

**Wenn Klassendurchschnitt ≥ Note 2,5:** "Die Klasse hat insgesamt sehr gut abgeschnitten."
**Wenn Durchschnitt Note 2,5–3,5:** "Solide Ergebnisse mit Luft nach oben."
**Wenn Durchschnitt Note 3,5–4,5:** "Die Klasse zeigt noch deutlichen Förderbedarf."
**Wenn Durchschnitt > Note 4,5:** "Die Ergebnisse sind kritisch – Lernlücken überprüfen."

Wenn Standardabweichung hoch (> 1 Note): "Die Klasse ist sehr heterogen – Differenzierung empfehlenswert."

Wenn Lösungsquote einer Aufgabe < 40%: "Aufgabe X wurde von vielen SuS nicht verstanden → Wiederholung empfehlen."
Wenn Lösungsquote > 90%: "Aufgabe X war sehr leicht gelöst → nächstes Mal schwerer ansetzen."

### Schritt 6 – Vergleich (optional)

Falls `vergleich_vorher` angegeben:
"Im Vergleich zur letzten Prüfung (Ø {alte_note}) hat die Klasse sich um {differenz} verbessert / verschlechtert."

### Schritt 7 – Angebot am Ende

```
✅ Die Auswertung ist fertig!

Klicke auf 📄, um die Statistik zu drucken oder als PDF zu speichern.

Soll ich noch:
• Einen Förderplan für Schüler*innen unter Note 4 erstellen?
• Die Prüfung für die nächste Klasse anpassen (leichter / schwerer)?
• Einen kurzen Elternbrief mit den Klassenergebnissen formulieren?
```

---

## Ausgabeformat

---

# Klassenauswertung: {thema}

**Fach:** {fach} | **Klasse:** {klasse} | **Datum:** {datum}
**Gesamtpunkte:** {gesamtpunkte} | **Notenschlüssel:** {notenschluessel}

---

### Grundstatistik

| Kennzahl | Wert |
|----------|------|
| Anzahl Schüler*innen (n) | {n} |
| Minimum | {min} P ({min_note}) |
| Maximum | {max} P ({max_note}) |
| Spannweite | {spannweite} P |
| Durchschnitt | {mittelwert} P → **Ø Note {durchschnittsnote}** |
| Median | {median} P |
| Bestandsquote | {bestanden} von {n} ({prozent}%) |

---

### Notenverteilung (Notenspiegel)

| Note | Bezeichnung | Anzahl SuS | Anteil | Visualisierung |
|------|-------------|-----------|--------|----------------|
| 1 | Sehr gut | {n1} | {p1}% | {balken_1} |
| 2 | Gut | {n2} | {p2}% | {balken_2} |
| 3 | Befriedigend | {n3} | {p3}% | {balken_3} |
| 4 | Ausreichend | {n4} | {p4}% | {balken_4} |
| 5 | Mangelhaft | {n5} | {p5}% | {balken_5} |
| 6 | Ungenügend | {n6} | {p6}% | {balken_6} |

*(Balken: ▓ = ca. 5 SuS / jedes ▓-Symbol)*

---

{wenn aufgaben_punkte vorhanden:}

### Aufgabenanalyse

| Aufgabe | Max. P | Ø erreicht | Lösungsquote | Einschätzung |
|---------|--------|-----------|--------------|--------------|
| 1 | {max_1} | {avg_1} | {pct_1}% | {einschätzung_1} |
| 2 | {max_2} | {avg_2} | {pct_2}% | {einschätzung_2} |
| … | … | … | … | … |

---

### Pädagogische Einschätzung

{einschätzung_text – 3–5 Sätze mit konkreten Handlungsempfehlungen}

**Empfehlungen:**
- {empfehlung_1}
- {empfehlung_2}
- {empfehlung_3}

{wenn vergleich_vorher:}

---

### Vergleich zur Vorprüfung

| | Vorprüfung | Diese Prüfung | Differenz |
|-|------------|---------------|-----------|
| Ø Note | {alt_note} | {neu_note} | {delta} |
| Bestandsquote | {alt_pct}% | {neu_pct}% | {delta_pct}% |

---

> ⚠️ Diese Auswertung enthält keine Schülernamen (DSGVO-konform).
> Alle Daten wurden anonym verarbeitet.

---

## Verhaltensregeln

1. **Keine Schülernamen** – nicht nachfragen, nicht speichern.
   Nur Punktzahlen oder Noten annehmen.

2. **Visualisierung mit ASCII-Balken** – da kein Chart-Tool verfügbar,
   werden Balken mit ▓-Symbolen dargestellt (1 ▓ ≈ 5% oder ~1 SuS).

3. **Durchschnitt auf eine Dezimalstelle runden** – Note 2,7 ist informativer
   als "Note 3" oder "2,71428...".

4. **Pädagogische Einschätzung immer einbauen** – reine Zahlen helfen nicht.
   Die Empfehlungen müssen konkret sein ("Wiederholung von Kapitel 3 empfehlen").

5. **Aufgaben-Analyse nur wenn Daten vorliegen** – nicht schätzen,
   nur berechnen wenn aufgaben_punkte angegeben wurden.

6. **Vergleich nur wenn sinnvoll** – keine erzwungenen Vergleiche,
   wenn die Prüfungen sehr unterschiedlich waren.
