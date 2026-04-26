---
name: elternbrief_schreiben
version: 1.0.0
author: LehrerAgent
description: >
  Erstellt professionelle Elternbriefe für alle Anlässe – Informationen,
  Einladungen, Klassenfahrten, Verhaltenshinweise oder Datenschutzbelehrungen –
  klar formuliert, druckfertig und schulgerecht.
category: bildung
language: de
priority: 10

triggers:
  - "elternbrief"
  - "brief an eltern"
  - "elternschreiben"
  - "einladung eltern"
  - "elternabend einladen"
  - "schreibe einen brief"
  - "mitteilung an eltern"
  - "klassenfahrt ankündigen"
  - "elterninformation"
  - "brief schreiben"

permissions:
  - read_memory
  - write_memory

memory_files:
  - lehrerprofil.md

parameters:
  required:
    - anlass
  optional:
    - klasse
    - fach
    - datum_veranstaltung    # Datum des beschriebenen Ereignisses
    - rueckantwort_bis       # Stichtag für Rückantwort
    - ton                    # formell | freundlich | dringend (Standard: freundlich)
    - mit_abrisszettel       # ja | nein (Standard: je nach Anlass)
    - sprache                # de | de+tr | de+ar (für mehrsprachige Schulen)
---

# Skill: Elternbrief schreiben

## Zweck

Dieser Skill generiert professionelle, schulgerechte Elternbriefe für alle
typischen Anlässe im Schulalltag. Die Briefe sind sofort ausdruckbar und
berücksichtigen das Profil der Lehrkraft (Schule, Klasse, Ort).

---

## Ablauf

### Schritt 1 – Lehrerprofil laden

Lade `lehrerprofil.md` und entnehme:
- Name der Lehrkraft (Absender)
- Schule + Ort
- Klasse(n) → Empfänger-Anrede

### Schritt 2 – Anlass und Parameter klären

Falls `anlass` unklar, biete eine Auswahl an:
```
Für welchen Anlass soll ich den Elternbrief schreiben?
  1 – Elternabend (Einladung + Tagesordnung)
  2 – Klassenfahrt / Schulausflug (Infos + Kosten + Anmeldung)
  3 – Allgemeine Information (Thema, Änderung, Ankündigung)
  4 – Verhaltenshinweis / Ermahnung (sachlich, ohne Vorwurf)
  5 – Datenschutz / Einwilligung (Fotos, Ausflug, Digitale Tools)
  6 – Sonstiges (bitte kurz beschreiben)
```

Falls `klasse` fehlt und im Profil mehrere Klassen: frage gezielt.

Falls `datum_veranstaltung` relevant ist, aber fehlt:
```
Wann findet das statt? (Datum + Uhrzeit, falls bekannt)
```

Falls `rueckantwort_bis` relevant: frage nach dem Stichtag.

### Schritt 3 – Inhalt strukturieren

Gliedere den Brief je nach Anlass:

**Elternabend:** Begrüßung → Termin + Ort → Tagesordnungspunkte → Bitte um Teilnahme
**Klassenfahrt:** Ziel + Termin → Programm (kurz) → Kosten → Mitnahme-Liste → Anmeldung
**Information:** Thema erklären → Hintergrund → Konsequenzen / nächste Schritte
**Verhaltenshinweis:** sachlicher Ton ohne Schuldzuweisung → Beobachtung → gewünschtes Verhalten → Bitte um Gespräch
**Datenschutz:** was wird erhoben → warum → Rechtsgrundlage → Widerspruchsmöglichkeit
**Einwilligung:** klar beschreiben worum es geht → Abrisszettel mit Ja/Nein-Feld

### Schritt 4 – Brief erstellen

Erstelle den Brief im Ausgabeformat. Nutze den korrekten schulischen Ton:
- Elternabend/Klassenfahrt: freundlich, einladend
- Verhaltenshinweis: sachlich, nicht anklagend, Gesprächsangebot
- Datenschutz: klar, verständlich, kein Juristendeutsch

### Schritt 5 – Abrisszettel (wenn sinnvoll)

Bei Klassenfahrten, Einwilligungen und Terminen mit Rückmeldung:
Füge einen Abrisszettel mit Schere-Symbol und Unterschriftsfeld an.

### Schritt 6 – Angebot am Ende

```
✅ Der Elternbrief ist fertig!

Klicke auf den 📄-Button, um ihn druckfertig zu öffnen.

Soll ich noch:
• Eine Version auf Türkisch / Arabisch / Englisch erstellen?
• Den Brief kürzer / ausführlicher formulieren?
• Den Abrisszettel anpassen?
```

---

## Ausgabeformat

---

**{Schule}**
{Ort}, {datum_heute}

**An die Eltern und Erziehungsberechtigten**
**der Klasse {klasse}**

---

**Betreff: {betreff}**

Sehr geehrte Eltern und Erziehungsberechtigte,

{brieftext – 3–6 Absätze je nach Anlass, freundlich und klar formuliert}

{ggf. Aufzählung mit wichtigen Infos / Terminen / Kosten}

Für Rückfragen stehe ich Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen

{Name der Lehrkraft}
{Klassenleitung / Fachlehrkraft}

---

{wenn mit_abrisszettel: ja}

✂️ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

**Rückmeldung bis: {rueckantwort_bis}**

Name des Kindes: _____________________________ Klasse: _______

{je nach Anlass:}
☐ Ich nehme teil.  /  ☐ Ich nehme nicht teil.
– oder –
☐ Ich stimme zu.  /  ☐ Ich stimme nicht zu.
– oder –
☐ Ich werde zum Elternabend erscheinen.

Unterschrift Erziehungsberechtigte/r: _____________________________

---

## Verhaltensregeln

1. **Kein Schülerklarnamen im Elternbrief** – bei Verhaltenshinweisen immer
   an Eltern des betreffenden Kindes persönlich richten (nicht als Sammelbrief).

2. **Datenschutz** – Elternbriefe enthalten keine Listen mit Schülernamen.
   Anredeform: "Ihre Tochter / Ihr Sohn" oder "Ihr Kind".

3. **Ton sachlich halten** – bei Verhaltenshinweisen: Beobachtung schildern,
   nicht werten. Nie Diagnosen stellen. Immer Gesprächsangebot machen.

4. **Kosten immer transparent** – bei Klassenfahrten: Gesamtbetrag, Zahlungsweg,
   Stichtag und Hinweis auf Unterstützungsmöglichkeiten (Bildungs- und Teilhabepaket).

5. **Rechtssichere Einwilligungen** – bei Foto- oder Datenweitergabe:
   DSGVO-Konformität beachten, Widerrufsmöglichkeit erwähnen.

6. **Barrierefreie Sprache** – kurze Sätze, keine Schachtelsätze,
   Fremdwörter erklären oder vermeiden.
