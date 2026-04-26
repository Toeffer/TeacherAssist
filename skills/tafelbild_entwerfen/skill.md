---
name: tafelbild_entwerfen
version: 1.0.0
author: LehrerAgent
description: Entwirft ein strukturiertes Tafelbild oder Whiteboard-Layout für eine Unterrichtsstunde – als ASCII-Skizze mit Erläuterung und didaktischen Hinweisen.
category: bildung
language: de
priority: 13

triggers:
  - "tafelbild"
  - "tafelskizze"
  - "whiteboard"
  - "tafelanschrieb"
  - "was schreibe ich an die tafel"
  - "visualisierung für die stunde"
  - "tafelbild entwerfen"
  - "tafelplan"
  - "tafelanschrift"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - thema
  optional:
    - fach
    - klasse
    - stundenziel
    - tafellayout
    - farben_verfuegbar
    - digital
---

# Skill: Tafelbild entwerfen

## Zweck

Dieser Skill erstellt einen konkreten Entwurf für ein Tafelbild oder Whiteboard-Layout.
Output: ASCII-Skizze der Tafelaufteilung + Farb-/Symbolhinweise + Schrittweise Aufbauanleitung.
Geeignet für analoge Tafel, Whiteboard und digitale Präsentationsflächen (Smartboard).

**Grundprinzip:** Ein gutes Tafelbild entsteht im Unterricht – es wird nicht einfach
aufgedeckt, sondern Schritt für Schritt gemeinsam entwickelt.

---

## Schritt-für-Schritt-Anweisung für den Brain

### Schritt 1 – Kontext erfassen

Frage falls nicht angegeben:
- Was ist das Thema / die Kernaussage der Stunde?
- Welches Fach und welche Klasse?
- Steht eine analoge Tafel oder ein digitales Whiteboard zur Verfügung?
- Welche Farben/Marker sind vorhanden? (Standard: Weiß + 1–2 Farben)

### Schritt 2 – Struktur wählen

Wähle die passende Grundstruktur:
- **Zentral:** Ein Hauptbegriff in der Mitte, Äste nach außen (geeignet für Begriffsnetze)
- **Zweispaltig:** Links Ausgangsproblem, rechts Lösung/Ergebnis
- **Dreispaltig:** These – Argument – Beispiel / Vorher – Prozess – Nachher
- **Zeitstrahl:** horizontal für chronologische Themen
- **Tabelle:** für Vergleiche, Gegenüberstellungen
- **Fluss:** Prozessdarstellung mit Pfeilen (geeignet für naturwiss. Abläufe)

### Schritt 3 – Tafelbild entwerfen

Erstelle eine ASCII-Skizze der gesamten Tafeloberfläche.
Verwende Kästchen, Pfeile und Symbole zur Verdeutlichung.
Nummeriere die Reihenfolge, in der Inhalte erscheinen.

### Schritt 4 – Aufbauanleitung schreiben

Erkläre Schritt für Schritt, wann was an die Tafel kommt.

---

## Ausgabeformat

---

### 🖊️ Tafelbild-Entwurf

**Thema:** {thema}
**Fach / Klasse:** {fach} / {klasse}
**Stundenziel:** {stundenziel}
**Format:** {analog Tafel / Whiteboard / Smartboard}
**Farben:** {verfuegbare_farben}

---

### 📐 Tafelaufteilung (Skizze)

*(Legende: ① ② ③ ... = Reihenfolge des Aufbaus | 🔴 = rot | 🔵 = blau | ⬛ = schwarz/weiß)*

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ①  {linke_spalte_titel}     │  ③  {rechte_spalte_titel}   │
│  ─────────────────────       │  ──────────────────────      │
│                              │                              │
│  {linker_inhalt_1}           │  {rechter_inhalt_1}          │
│                              │                              │
│  {linker_inhalt_2}      ②    │  {rechter_inhalt_2}          │
│  → {schlüsselbegriff}        │                              │
│                              │  ④  {ergebnis_bereich}       │
│                              │                              │
│                              │  {schlussformel_oder_fazit}  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

*(alternative Skizze je nach gewähltem Layout)*

---

### 🎨 Farb- und Symbolkonzept

| Element | Farbe / Symbol | Bedeutung |
|---------|---------------|-----------|
| Überschriften | {farbe_1} (z. B. rot) | Struktur / Orientierung |
| Schlüsselbegriffe | {farbe_2} (z. B. blau) | Merken! |
| SuS-Beiträge | weiß / schwarz | Unterricht entwickelt sich |
| Pfeile | weiß / schwarz | Zusammenhänge |
| Kästen | gelb eingerahmt | Definition / Merksatz |

---

### 📋 Aufbau-Anleitung (Schritt für Schritt)

**Schritt ① – Vor der Stunde:**
{was bereits an der Tafel steht wenn SuS reinkommen – z. B. nur die Überschrift}

**Schritt ② – Einstieg ({zeitpunkt}):**
{was während des Einstiegs an die Tafel kommt – welche Fragen/Impulse werden hingeschrieben}

**Schritt ③ – Erarbeitung ({zeitpunkt}):**
{was gemeinsam erarbeitet und festgehalten wird}
> Tipp: SuS kommen selbst an die Tafel / diktieren den Anschrieb

**Schritt ④ – Sicherung ({zeitpunkt}):**
{fertige Merksätze, Definitionen, Zusammenfassungen}

---

### 📸 Abschreibe-Hinweis für SuS

{falls Tafelbild abgeschrieben werden soll: klarer Hinweis wann}
> „Bitte schreibt jetzt Schritt ④ in euer Heft ab."

{alternative: Foto erlaubt statt Abschreiben}

---

### 💡 Tipps für dieses Tafelbild

- {tipp_1 – z. B. Platz für spontane SuS-Beiträge lassen}
- {tipp_2 – z. B. Hauptbegriff schon zu Beginn eintragen, Rest leer lassen}
- {tipp_3 – z. B. Tafelbild fotografieren für vergangene_stunden.md}

---

## Verhaltensregeln

1. **Tafelbild wächst** – niemals komplett vorschreiben; Platz für Unterrichtsentwicklung lassen.
2. **Lesbarkeit** – max. 30–40 Wörter auf der gesamten Tafel; lieber weniger.
3. **Kein Fließtext** – Stichworte, Strukturen, Pfeile.
4. **Keine Fehler** – was an der Tafel steht, gilt als korrekt und wird so gelernt.
5. **Am Ende fragen:**
   "Soll ich auch einen Stundenentwurf oder ein Arbeitsblatt erstellen,
   das zum Tafelbild passt?"
