---
name: lehrplan_coverage
version: 1.0.0
author: LehrerAgent
description: >
  Analysiert den Unterrichtsfortschritt und zeigt, welche Lehrplaninhalte
  bereits behandelt wurden und welche noch ausstehen.
category: bildung
language: de

triggers:
  - "lehrplan coverage"
  - "lehrplan fortschritt"
  - "was haben wir schon gemacht"
  - "welche themen stehen noch aus"
  - "unterrichtsfortschritt"
  - "coverage tracker"
  - "was fehlt noch im lehrplan"
  - "lehrplan check"
  - "bin ich im zeitplan"

permissions:
  - read_memory

memory_files:
  - lehrerprofil.md
  - vergangene_stunden.md
---

# Skill: Lehrplan-Coverage-Tracker

## Zweck

Dieser Skill vergleicht die tatsächlich gehaltenen Unterrichtsstunden
(aus `memory/vergangene_stunden.md`) mit den erwarteten Lehrplaninhalten
(aus der RAG-Wissensdatenbank) und gibt eine übersichtliche
Coverage-Analyse zurück.

---

## Ablauf

### Schritt 1 – Verlaufsprotokoll laden

Lade `memory/vergangene_stunden.md` und extrahiere:
- Alle behandelten Themen mit Datum, Fach und Klasse
- Verwendete Methoden pro Stunde (falls vorhanden)

Falls die Datei leer oder nicht vorhanden ist:
```
Ich habe noch keine vergangenen Stunden im Verlaufsprotokoll.
Plane zuerst Unterrichtsstunden, damit ich den Lehrplanfortschritt
verfolgen kann.
```

### Schritt 2 – Lehrplaninhalte ermitteln

Nutze die RAG-Wissensdatenbank, um die erwarteten Themenblöcke für
das gewünschte Fach und die Klasse abzurufen.

Falls kein Lehrplan eingelesen wurde:
```
Kein Lehrplan für dieses Fach/diese Klasse gefunden.
Lade unter Einstellungen → Wissensdatenbank einen Lehrplan hoch,
damit ich den Abgleich vornehmen kann.
```

### Schritt 3 – Coverage berechnen

Vergleiche behandelte Themen mit Lehrplaninhalten (Schlagwort-
und Sinnabgleich, keine exakte Wortübereinstimmung nötig).

Markiere jeden Themenblock als:
- ✅ Behandelt – Inhalt ist klar im Verlaufsprotokoll vorhanden
- ⏳ Teilweise – Thema wurde begonnen, aber noch nicht abgeschlossen
- ❌ Ausstehend – Kein Eintrag im Verlaufsprotokoll gefunden

### Schritt 4 – Bericht ausgeben

---

## Ausgabeformat

---

### 📊 Lehrplan-Coverage: {Fach} Klasse {Klasse}

**Analysezeitraum:** {erstes Datum} – {letztes Datum}
**Gehaltene Stunden:** {anzahl}

---

#### ✅ Behandelte Themen ({anzahl})

| Thema | Datum | Stunden |
|-------|-------|---------|
| {Thema} | {Datum} | {n} |

---

#### ⏳ Teilweise behandelt ({anzahl})

{Kurze Beschreibung welcher Aspekt noch fehlt}

---

#### ❌ Noch ausstehend ({anzahl})

{Lehrplaninhalte, die bisher nicht behandelt wurden}

---

### 🗓️ Zeitplan-Einschätzung

**Status:** {Im Plan / Leicht verzögert / Deutlich verzögert}

{2-3 Sätze: Liegt der Kurs im Zeitplan? Welche Themen sollten
prioritär als nächstes dran kommen? Gibt es kritische Lücken,
die vor der nächsten Prüfung geschlossen werden müssen?}

**Empfehlung für die nächsten 2 Wochen:**
{Konkrete Vorschläge, welche Themen als nächstes behandelt werden sollten}

---

> 💡 Diese Analyse basiert auf den gespeicherten Verlaufsprotokollen
> und dem eingelesenen Lehrplan. Aktualisiere dein Verlaufsprotokoll
> regelmäßig für genaue Ergebnisse.
