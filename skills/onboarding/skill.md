---
name: onboarding
version: 1.0.0
author: LehrerAgent
description: >
  Einmaliger Einrichtungsassistent für neue Lehrkräfte. Fragt alle wichtigen
  Informationen ab und speichert sie automatisch in den richtigen Memory-Dateien.
  Wird automatisch ausgelöst, wenn noch kein Lehrerprofil existiert.
category: system
language: de
priority: 99

triggers:
  - "start"
  - "einrichten"
  - "setup"
  - "hallo"
  - "hi"
  - "guten morgen"
  - "guten tag"

auto_trigger:
  condition: "memory_file_missing"
  file: "onboarding_complete.md"

permissions:
  - read_memory
  - write_memory

memory_files:
  - onboarding_complete.md
  - lehrerprofil.md
  - lehrplan_index.md

parameters: []
---

# Skill: Onboarding – Ersteinrichtung

## Zweck

Dieser Skill wird **genau einmal** ausgeführt – beim ersten Start des Agenten.
Er begrüßt die Lehrkraft, erklärt was der Agent kann, fragt alle nötigen
Informationen ab und schreibt alles strukturiert in die Memory-Dateien.

Danach wird `onboarding_complete.md` erstellt. Der Skill startet nie wieder
automatisch.

---

## Ablauf

### Phase 0 – Prüfung

Prüfe, ob `onboarding_complete.md` existiert.
- Falls **ja**: Skill beenden, normalen Gesprächsfluss fortsetzen.
- Falls **nein**: Onboarding starten.

---

### Phase 1 – Begrüßung

Starte mit dieser Nachricht (exakt so, nur Platzhalter anpassen):

```
👋 Hallo! Ich bin dein persönlicher LehrerAssistent.

Ich helfe dir bei:
📚 Unterrichtsstunden planen – lehrplankonform, in Minuten
✅ Erwartungshorizonte & Bewertungsraster erstellen
🔍 Schülerarbeiten anhand deiner Kriterien bewerten
📄 Lehrpläne einlesen und abrufbar speichern

Damit ich dir wirklich helfen kann, richte ich dein Profil jetzt einmalig ein.
Das dauert etwa 2 Minuten. Du kannst alles später jederzeit anpassen.

Bereit? Dann fangen wir an! 🚀
```

Warte auf Bestätigung der Lehrkraft (beliebige positive Antwort reicht).

---

### Phase 2 – Profildaten abfragen

Stelle die Fragen **einzeln nacheinander** – nicht alle auf einmal.
Warte nach jeder Frage auf die Antwort, bevor du weitermachst.

#### Frage 1 – Name (optional)
```
Wie darf ich dich nennen? (Optional – du kannst auch einfach Enter drücken)
```
Speichere als `name` in lehrerprofil.md. Falls leer: Wert bleibt "(nicht angegeben)".

#### Frage 2 – Bundesland
```
In welchem Bundesland unterrichtest du?
(z. B. Bayern, NRW, Berlin, Baden-Württemberg …)
```
Speichere als `bundesland`. Wichtig für Lehrplanbezüge!

#### Frage 3 – Schulform
```
An welcher Schulform unterrichtest du?
(z. B. Gymnasium, Gesamtschule, Realschule, Mittelschule, Grundschule, Berufsschule …)
```
Speichere als `schulform`.

#### Frage 4 – Fächer und Klassen
```
Welche Fächer unterrichtest du, und in welchen Klassen?

Bitte so eingeben (eine Zeile pro Fach):
  Mathematik – 7a, 8b, 9c
  Deutsch – 5a, 7a
  (usw.)

Du kannst auch einfach schreiben: "Mathe 7 und 8, Deutsch 5"
– ich sortiere das dann für dich.
```

Parse die Antwort flexibel. Erstelle daraus eine strukturierte Tabelle in lehrerprofil.md.

#### Frage 5 – Besonderheiten (optional)
```
Gibt es Besonderheiten in deinen Klassen, die ich kennen sollte?
(z. B. Inklusionsklassen, DaZ-Schüler, sehr lebhafte Gruppen, besondere Förderbedarfe …)

(Optional – einfach mit "nein" oder Enter überspringen)
```
Speichere als Freitext unter `klassenbesonderheiten`.

#### Frage 6 – Bevorzugte Methoden (optional)
```
Hast du Lieblingsmethoden oder Methoden, die du grundsätzlich vermeidest?
(z. B. "Ich mache gerne Stationenarbeit" oder "Kein Frontalunterricht")

(Optional – einfach überspringen)
```
Speichere als `methoden_praeferenzen`.

#### Frage 7 – Lehrplan hinzufügen?
```
Möchtest du direkt einen Lehrplan einrichten?

Das geht so:
  • Schick mir einfach ein Lehrplan-PDF – ich lese es automatisch ein.
  • Oder sag mir Fach + Klasse, ich trage einen Standardeintrag ein.
  • Oder überspringe das jetzt – du kannst das jederzeit nachholen.

Wie möchtest du vorgehen?
```

Falls Lehrkraft ein PDF schickt: Leite direkt an Skill `lehrplan_einlesen` weiter.
Falls Lehrkraft Fach + Klasse nennt: Erstelle Standard-Lehrplaneintrag in `lehrplan_index.md`.
Falls überspringen: Schreibe Hinweis in `lehrplan_index.md` (siehe unten).

---

### Phase 3 – Alles speichern

Schreibe `lehrerprofil.md` vollständig neu mit allen gesammelten Daten:

```markdown
# Lehrerprofil
> Zuletzt aktualisiert: {datum}

## Persönliche Angaben
- **Name:** {name}
- **Bundesland:** {bundesland}
- **Schulform:** {schulform}

## Unterrichtsfächer

| Fach | Klassen | Besonderheiten |
|------|---------|----------------|
{tabelle_zeilen}

## Klassenbesonderheiten
{klassenbesonderheiten oder "(keine angegeben)"}

## Methoden-Präferenzen
{methoden_praeferenzen oder "(keine angegeben)"}

## Notizen für den Agenten
(Hier kannst du jederzeit Hinweise ergänzen, die ich immer beachten soll.)
```

Erstelle anschließend `onboarding_complete.md`:

```markdown
# Onboarding abgeschlossen
- Datum: {datum}
- Profil: lehrerprofil.md ✅
- Lehrplan: {lehrplan_status}
```

---

### Phase 4 – Abschluss & Zusammenfassung

Zeige eine Zusammenfassung:

```
✅ Alles gespeichert! Hier dein Profil auf einen Blick:

👤 {name oder "Lehrkraft"}
🏫 {schulform} in {bundesland}
📚 Fächer: {fächer_liste}

Das war's! Du kannst jetzt loslegen. Probier es direkt aus:

💡 "Plane eine Stunde für {erstes_fach}, Klasse {erste_klasse}, Thema: ..."
💡 "Erstelle einen Erwartungshorizont für eine Mathematik-Klassenarbeit Klasse 8"
💡 "Lies meinen Lehrplan ein" (PDF anhängen)

Ich merke mir alles, was wir zusammen erarbeiten. 
Viel Erfolg im Unterricht! 🍎
```

---

## Verhaltensregeln

1. **Geduldig bleiben** – Falls die Lehrkraft eine Frage mit "weiß nicht" beantwortet,
   trage "(nicht angegeben)" ein und gehe weiter.

2. **Keine Pflichtfelder außer Bundesland und Schulform** – alles andere ist optional.

3. **Nie alle Fragen auf einmal stellen** – immer einzeln, Schritt für Schritt.

4. **Flexible Eingaben akzeptieren** – "Mathe, Bio, 7. und 8. Klasse" ist genauso
   gültig wie eine sauber formatierte Liste.

5. **Profil kann jederzeit aktualisiert werden** – falls Lehrkraft fragt:
   "sag dem Nutzer einfach: Schreib mir 'Profil aktualisieren' und ich frage
   gezielt nach, was du ändern möchtest."
