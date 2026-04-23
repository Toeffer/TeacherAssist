# Bewertungsraster-Verzeichnis

> Hier werden alle erstellten Bewertungsraster und Erwartungshorizonte gespeichert.
> Jede Datei entspricht einem Fach-Klassen-Thema-Kombination.

## Dateinamen-Konvention
```
{fach}_{klasse}_{thema}.md
```

Beispiele:
- `mathematik_7_bruchrechnung.md`
- `deutsch_10_gedichtanalyse.md`
- `englisch_8_present_perfect.md`

## Dateistruktur
Jede Bewertungsraster-Datei folgt diesem Template:

```markdown
# Bewertungsraster: {Thema}
## Fach: {Fach}
## Klasse: {Klasse}
## Erstellt am: {Datum}

## Lernziele
- [Lernziel 1]
- [Lernziel 2]
- [Lernziel 3]

## Bewertungskriterien

### Inhalt (max. {X} Punkte)
| Kriterium | Max. Punkte | Beschreibung |
|-----------|-------------|--------------|
| Kriterium 1 | {Punkte} | {Beschreibung} |
| Kriterium 2 | {Punkte} | {Beschreibung} |

### Form/Sprache (max. {Y} Punkte)
| Kriterium | Max. Punkte | Beschreibung |
|-----------|-------------|--------------|
| Rechtschreibung | {Punkte} | {Beschreibung} |
| Ausdruck | {Punkte} | {Beschreibung} |

## Notenschlüssel
| Prozent | Note | Beschreibung |
|---------|------|--------------|
| 95-100% | 1 | Sehr gut |
| 80-94%  | 2 | Gut |
| 65-79%  | 3 | Befriedigend |
| 50-64%  | 4 | Ausreichend |
| 25-49%  | 5 | Mangelhaft |
| 0-24%   | 6 | Ungenügend |

## AFB-Verteilung
- AFB I (Reproduktion): ~30%
- AFB II (Reorganisation): ~40%
- AFB III (Transfer): ~30%

## Zeitvorgabe
- Bearbeitungszeit: {X} Minuten
- Einstieg: max. 10 Minuten
- Sicherung: min. 5 Minuten

## Differenzierung
- **Einfach:** {Aufgaben für leistungsschwächere Schüler}
- **Erweitert:** {Aufgaben für leistungsstärkere Schüler}

## Materialien
- [Liste benötigter Materialien]

## Anmerkungen
[Hier können zusätzliche Hinweise stehen]
```

## Automatische Erstellung
Bewertungsraster werden automatisch erstellt durch:
1. Skill `bewertung_erstellen`
2. Skill `schuelerarbeit_bewerten` (bei Bedarf)

## Manuelle Bearbeitung
Alle Dateien können jederzeit manuell bearbeitet werden. Der Agent berücksichtigt Änderungen bei zukünftigen Bewertungen.