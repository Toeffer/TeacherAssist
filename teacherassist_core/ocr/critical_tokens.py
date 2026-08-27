"""Erkennung bedeutungsveraendernder ("kritischer") OCR-Abweichungen.

Eine Abweichung zwischen zwei OCR-Engines ist nur dann "kritisch" (muss also
zwingend von einer Lehrkraft geprueft werden), wenn sie den fachlichen Inhalt
aendern koennte -- ein anderes Wort mit gleicher Bedeutung ("Auto" vs.
"Autos") ist es nicht, eine Negation ("nicht"), eine Zahl, Einheit oder ein
mathematisches Symbol dagegen schon.

Bewusst NICHT implementiert: praefixbasierte Negationserkennung (un-, in-)
-- ohne echtes Lexikon feuert das auf Woertern wie "Uniform" vs. "Form" und
erzeugt mehr Rauschen als Nutzen. Stattdessen wird nur die explizite
Wortliste CRITICAL_WORDS verwendet.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

from .markup import UNCLEAR_SENTINEL

CRITICAL_WORDS: frozenset[str] = frozenset(
    {
        # Negation / Quantifizierung
        "nicht",
        "kein",
        "keine",
        "keiner",
        "keinen",
        "keinem",
        "keines",
        "keinerlei",
        "nichts",
        "nie",
        "niemals",
        "niemand",
        "ohne",
        "weder",
        "noch",
        "außer",
        "ausser",
        "nur",
        "kaum",
        # Polaritaet / Vergleich
        "mehr",
        "weniger",
        "größer",
        "groesser",
        "kleiner",
        "gleich",
        "ungleich",
        "zunimmt",
        "abnimmt",
        "steigt",
        "sinkt",
        "wächst",
        "waechst",
        "schrumpft",
        "konstant",
        "positiv",
        "negativ",
        "richtig",
        "falsch",
        "wahr",
        "unwahr",
        "ja",
        "nein",
        # Modalitaet
        "muss",
        "kann",
        "darf",
        "soll",
        "möglich",
        "moeglich",
        "unmöglich",
        "unmoeglich",
        "immer",
        "alle",
        "jeder",
        "manche",
        "einige",
        "höchstens",
        "hoechstens",
        "mindestens",
    }
)

CRITICAL_SYMBOLS: frozenset[str] = frozenset(
    "+-−±×÷/*=≠<>≤≥≈^√%°‰·∙∑∏∫∂ΔΩπµ→←↔⇌∈∉⊂⊆∪∩∧∨¬"
    "‐‑‒–—―−"
)

# SI- und Schul-Einheiten. Der Vergleich erfolgt casefolded (siehe
# unit_tokens), die Rohschreibweise bleibt fuer die SI-Praefix-Erkennung
# erhalten (siehe classify_span / _si_prefix_confusion).
UNIT_TOKENS: frozenset[str] = frozenset(
    {
        "m", "cm", "mm", "km", "µm", "nm",
        "g", "kg", "mg", "t",
        "s", "ms", "min", "h",
        "N", "J", "kJ",
        "W", "kW",
        "V", "mV", "kV",
        "A", "mA",
        "Ω", "ohm",
        "C", "K",
        "Pa", "hPa", "bar",
        "mol", "l", "ml",
        "Hz", "kHz", "MHz",
        "eV", "dB", "%",
        "°C",
        "m/s", "km/h", "m/s²", "g/mol", "mol/l",
    }
)

# Praefix-Paare, die historisch besonders haeufig durch OCR verwechselt
# werden (visuell aehnliche Kleinbuchstaben) und daher explizit als kritisch
# gelten muessen, selbst wenn beide Seiten formal "eine Einheit" sind.
SI_PREFIX_CONFUSIONS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"m", "k"}),
        frozenset({"m", "µ"}),
        frozenset({"c", "m"}),
        frozenset({"h", "k"}),
    }
)

SUBJECT_TOKENS: dict[str, frozenset[str]] = {
    "physik": frozenset(
        {
            "kraft", "masse", "beschleunigung", "geschwindigkeit", "energie",
            "leistung", "spannung", "stromstärke", "stromstaerke", "widerstand",
            "ladung", "feld", "frequenz", "wellenlänge", "wellenlaenge",
            "impuls", "drehmoment", "reibung", "gravitation", "magnetfeld",
            "induktion",
        }
    ),
    "chemie": frozenset(
        {
            "säure", "saeure", "base", "salz", "molekül", "molekuel", "atom",
            "ion", "reaktion", "oxidation", "reduktion", "katalysator",
            "lösung", "loesung", "konzentration", "molar", "bindung",
            "elektron", "proton", "neutron", "isotop", "niederschlag",
        }
    ),
    "mathematik": frozenset(
        {
            "funktion", "ableitung", "integral", "grenzwert", "gleichung",
            "ungleichung", "variable", "konstante", "summe", "produkt",
            "matrix", "vektor", "winkel", "fläche", "flaeche", "volumen",
            "wahrscheinlichkeit", "menge", "polynom", "extremum",
        }
    ),
}

_SI_PREFIX_CHARS = frozenset("mkµcndhMGpTP")

_WORD_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# Erfasst Zahl-Läufe inkl. deutscher Tausenderpunkte/Dezimalkomma sowie
# vereinzelter englischer Dezimalpunkte (siehe _parse_german_number).
_NUMBER_RUN_RE = re.compile(r"[+-]?\d[\d.,]*\d|[+-]?\d")


@dataclass(frozen=True)
class CriticalTokenConfig:
    words: frozenset[str] = CRITICAL_WORDS
    symbols: frozenset[str] = CRITICAL_SYMBOLS
    units: frozenset[str] = UNIT_TOKENS
    subject: str | None = None
    extra_words: frozenset[str] = frozenset()

    @classmethod
    def for_subject(
        cls,
        subject: str | None,
        overrides: dict | None = None,
    ) -> "CriticalTokenConfig":
        """Baut eine Konfiguration fuer `subject` und mischt optionale
        Overrides (Form siehe load_overrides) flach ueber die Defaults.
        `overrides["subjects"][subject]` erweitert die kritischen Woerter
        nur fuer dieses Fach (extra_words); `overrides["words"]` /
        `["symbols"]` erweitern die globalen Mengen fuer alle Faecher."""
        words = CRITICAL_WORDS
        symbols = CRITICAL_SYMBOLS
        units = UNIT_TOKENS
        extra_words: frozenset[str] = frozenset()
        if overrides:
            if "words" in overrides:
                words = words | frozenset(overrides["words"])
            if "symbols" in overrides:
                symbols = symbols | frozenset(overrides["symbols"])
            if "units" in overrides:
                units = units | frozenset(overrides["units"])
            if subject and subject in overrides.get("subjects", {}):
                extra_words = frozenset(overrides["subjects"][subject])
        return cls(words=words, symbols=symbols, units=units, subject=subject, extra_words=extra_words)


def load_overrides(path: str | Path) -> dict:
    """Laedt eine Overrides-Datei: {"words": [...], "symbols": "...",
    "subjects": {"physik": [...]}}. Wird bewusst NIE beim Modulimport
    aufgerufen, sondern nur lazy vom Aufrufer."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _parse_german_number(raw: str) -> Decimal:
    sign = ""
    body = raw
    if body and body[0] in "+-":
        sign = "-" if body[0] == "-" else ""
        body = body[1:]

    if "," in body:
        # Deutsches Format: "." gruppiert Tausender, "," ist das Dezimaltrennzeichen.
        integer_part, _, frac_part = body.rpartition(",")
        integer_part = integer_part.replace(".", "") or "0"
        normalized = f"{sign}{integer_part}.{frac_part}"
    elif body.count(".") == 1:
        # Mehrdeutig: koennte deutsche Tausendergruppierung ("1.234") oder ein
        # durch OCR eingefuegter englischer Dezimalpunkt ("3.5") sein. Wir
        # behandeln einen einzelnen Punkt als Dezimaltrennzeichen -- das ist
        # unabdingbar dafuer, dass "3,5" und "3.5" als GLEICHER Wert gelten
        # (siehe Testfall: 3,5 vs. 3.5 ist NICHT kritisch), da Komma/Punkt
        # eine der haeufigsten OCR-Verwechslungen ueberhaupt ist.
        normalized = f"{sign}{body}"
    elif "." in body:
        # Mehrere Punkte: eindeutig deutsche Tausendergruppierung (z.B. "1.234.567").
        normalized = f"{sign}{body.replace('.', '')}"
    else:
        normalized = f"{sign}{body}"

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return Decimal(0)


def numeric_values(text: str) -> tuple[Decimal, ...]:
    """Extrahiert jeden Zahl-Lauf aus `text` und normalisiert deutsche
    Formatierung. Jede Differenz -- Wert, Anzahl oder Reihenfolge -- macht
    die zurueckgegebenen Tupel ungleich."""
    return tuple(_parse_german_number(raw) for raw in _NUMBER_RUN_RE.findall(text))


def _raw_unit_tokens(text: str, units: frozenset[str]) -> tuple[str, ...]:
    """Wie unit_tokens, behaelt aber die urspruengliche Gross-/Kleinschreibung
    bei -- benoetigt fuer die SI-Praefix-Verwechslungserkennung, bei der genau
    diese Schreibung (z.B. "mV" vs. "MV") den Unterschied ausmacht."""
    casefolded_lookup = {u.casefold() for u in units}
    found: list[str] = []
    for word in text.split():
        candidate = word.strip(",.;:()[]{}")
        if not candidate:
            continue
        stripped = re.sub(r"^[+-]?\d+([.,]\d+)?", "", candidate)
        for form in (candidate, stripped):
            if form and form.casefold() in casefolded_lookup:
                found.append(form)
                break
    return tuple(found)


def unit_tokens(text: str, units: frozenset[str] = UNIT_TOKENS) -> tuple[str, ...]:
    """Gibt die casefolded Einheiten-Teilstrings aus `text` zurueck, die eine
    bekannte Einheit treffen, in Erscheinungsreihenfolge."""
    return tuple(token.casefold() for token in _raw_unit_tokens(text, units))


def _split_prefix(unit: str) -> tuple[str, str]:
    if len(unit) >= 2 and unit[0] in _SI_PREFIX_CHARS:
        return unit[0], unit[1:]
    return "", unit


def _si_prefix_confusion(text_a: str, text_b: str, units: frozenset[str]) -> bool:
    """Erkennt Faelle, in denen dieselbe Basiseinheit mit unterschiedlichem
    SI-Praefix vorkommt (z.B. "mV" vs. "MV"), auch wenn der einfache
    casefolded Vergleich in unit_tokens() das uebersieht, weil beide
    Praefixe auf denselben Kleinbuchstaben casefolden."""
    for raw_a in _raw_unit_tokens(text_a, units):
        prefix_a, base_a = _split_prefix(raw_a)
        for raw_b in _raw_unit_tokens(text_b, units):
            prefix_b, base_b = _split_prefix(raw_b)
            if base_a.casefold() != base_b.casefold():
                continue
            if raw_a == raw_b:
                continue
            if not prefix_a and not prefix_b:
                continue
            if prefix_a == prefix_b:
                continue
            # Praefixe unterscheiden sich auf derselben Basiseinheit: das
            # aendert immer die physikalische Groessenordnung. SI_PREFIX_
            # CONFUSIONS dokumentiert zusaetzlich, welche Paare historisch
            # die haeufigsten OCR-Verwechslungen sind (fuer Tests/Doku).
            return True
    return False


def _canonical_word(word: str) -> str:
    """Vereinheitlicht Umlaut-Schreibweisen (ö/oe, ü/ue, ä/ae, ß/ss) neben
    Gross-/Kleinschreibung. CRITICAL_WORDS enthaelt bewusst beide
    Schreibweisen mancher Woerter (z.B. "größer" UND "groesser"), weil OCR
    ueber beide stolpern kann; str.casefold() allein loest ß->ss aber NICHT
    ö->oe auf, wuerde also "größer" nicht auf "groesser" abbilden.

    NFKC-normalisiert VOR dem Falten (siehe Auftrag: konsistent mit
    ``consensus.normalize_token``) -- ein NFC- und ein NFD-kodiertes
    "größer" (vorkomponiertes ö vs. o + kombinierendes Trema) sollen
    identisch abgebildet werden, statt als kritische Diskrepanz
    aufzufallen. Zwei unterschiedliche Normalisierungsregeln in derselben
    Pipeline wuerden sonst frueher oder spaeter auseinanderlaufen."""
    text = unicodedata.normalize("NFKC", word)
    text = text.casefold().replace("ß", "ss")
    return text.replace("ö", "oe").replace("ü", "ue").replace("ä", "ae")


def _critical_word_set(text: str, words: frozenset[str]) -> frozenset[str]:
    # NFKC VOR der Tokenisierung (nicht erst in _canonical_word): _WORD_TOKEN_RE
    # stuetzt sich auf \w, das kombinierende Zeichen (Unicode-Kategorie Mn)
    # ausschliesst. In NFD-kodiertem Text (z.B. macOS-Zwischenablage) ist z.B.
    # "möglich" als "o" + kombinierendes Trema (U+0308) kodiert und wuerde
    # schon HIER, beim Tokenisieren, in zwei Tokens zerrissen ("mo"/"glich") --
    # _canonical_word() normalisiert zwar auch NFKC, bekommt die Fragmente aber
    # erst NACH diesem Bruch zu sehen und kann ihn nicht mehr heilen.
    text = unicodedata.normalize("NFKC", text)
    canonical_words = {_canonical_word(w) for w in words}
    found = set()
    for match in _WORD_TOKEN_RE.finditer(text):
        canonical = _canonical_word(match.group(0))
        if canonical in canonical_words:
            found.add(canonical)
    return frozenset(found)


# Zeichen, die beim "de-spacing" (siehe _critical_word_sequence) neben
# Leerraum ebenfalls entfernt werden, damit ein abgetrenntes Negationspraefix
# wie "un-" bzw. "un" wieder an sein Grundwort andocken kann. Bewusst
# dieselbe Zeichenmenge wie der neu ergaenzte Bindestrich-Block in
# CRITICAL_SYMBOLS (siehe Modul-Docstring, Stufe: kritische
# Bindestrich-Glyphen) plus der ASCII-Bindestrich.
_DASH_CHARS: frozenset[str] = frozenset("-‐‑‒–—―−")


# Fragmente, die selbst gebraeuchliche, kurze deutsche Funktionswoerter sind,
# duerfen NIE mit einem Nachbarn verschmolzen werden (siehe
# _critical_word_sequence, Abschnitte (b) und (c)) -- sonst bildet z.B.
# "je"+"der" das Quantorwort "jeder" und meldet eine voellig unabhaengige,
# unkritische Textabweichung ("je" vs. "wie"/"so" o.ae.) faelschlich als
# kritisch. "un" ist bewusst NICHT in dieser Liste: es ist selbst kein
# eigenstaendiges deutsches Wort, sondern ausschliesslich ein gebundenes
# Negationspraefix -- taucht es isoliert als Variante auf, ist das (fast)
# immer ein OCR-Trennartefakt und niemals ein eigenstaendiger Lesefund, der
# geschuetzt werden muesste. Bewusst DISJUNKT von CRITICAL_WORDS gehalten:
# diese Liste beschreibt reine Funktionswoerter (Artikel, Pronomen,
# Praepositionen, Konjunktionen, Hilfsverbformen), keine bedeutungstragenden
# Inhaltswoerter -- ein kritisches Wort wird ueber CRITICAL_WORDS ohnehin
# schon direkt erkannt (Schritt 1), unabhaengig von jeder Verschmelzung, und
# gehoert konzeptionell nicht hierher. Kuratiert als Positivliste (kein
# Lexikon): lieber ein Eintrag zu viel als zu wenig -- jeder Eintrag
# verhindert nur eine Verschmelzungsmoeglichkeit (Kosten: eine ohnehin sehr
# schmale Sonderpruefung greift in einem weiteren Fall nicht), waehrend ein
# fehlender Eintrag eine Lehrkraft einen falschen kritischen Alarm klicken
# laesst.
MERGE_BLOCKED_FRAGMENTS: frozenset[str] = frozenset(
    {
        # Artikel / Determinierer
        "der", "die", "das", "den", "dem", "des",
        "ein", "eine", "einen", "einem", "einer", "eines",
        "jener", "jene", "jenes", "dieser", "diese", "dieses",
        # Pronomen
        "ich", "du", "er", "sie", "es", "wir", "ihr", "man",
        "wer", "was", "mich", "dich", "ihn", "ihm", "uns", "euch", "ihnen",
        "mein", "dein", "sein", "unser", "euer",
        # Praepositionen
        "in", "an", "am", "im", "um", "zu", "zur", "zum", "ab",
        "auf", "aus", "bei", "mit", "von", "vom", "vor", "fuer", "fur",
        "nach", "bis", "durch", "gegen", "unter", "ueber", "neben",
        "zwischen", "waehrend", "seit", "trotz",
        # Konjunktionen / Partikeln
        "und", "oder", "aber", "denn", "weil", "wenn", "als", "wie", "dass",
        "ob", "so", "da", "doch", "auch", "schon", "sehr", "jetzt", "heute",
        "hier", "dort", "dann", "zwar", "sowie", "je", "eben", "mal", "wohl",
        "etwa", "ganz", "recht", "gar",
        # kurze Hilfsverbformen
        "ist", "war", "sind", "wird", "waren", "bin", "bist", "seid",
        "hat", "habe", "haben", "hatte", "wurde", "werden", "sei",
    }
)


def _is_blocked_fragment(tokens: Sequence[str]) -> bool:
    """True, wenn irgendeines der (rohen) `tokens` -- kanonisiert -- selbst
    ein gebraeuchliches Funktionswort aus MERGE_BLOCKED_FRAGMENTS ist. Wird
    ausschliesslich auf die Fragment-Seite angewendet (das Variantentext
    selbst bzw. die innerhalb EINER Spanne zu verschmelzenden Tokens),
    NIEMALS auf die Nachbar-Seite (left_context/right_context) -- der
    Nachbar stammt per Konstruktion immer aus echtem, unstrittigem
    Fliesstext und WAERE daher so gut wie immer selbst ein echtes Wort;
    ihn ebenfalls zu pruefen wuerde praktisch jede Verschmelzung blockieren."""
    canonical_blocked = {_canonical_word(w) for w in MERGE_BLOCKED_FRAGMENTS}
    return any(_canonical_word(t) in canonical_blocked for t in tokens)


def _critical_word_sequence(
    text: str,
    words: frozenset[str],
    *,
    left_context: str = "",
    right_context: str = "",
) -> tuple[str, ...]:
    """Wie _critical_word_set, aber (a) ORDNUNG-erhaltend (ein Tupel in
    Erscheinungsreihenfolge statt eines Sets), (b) ergaenzt um Treffer aus
    der "de-spaced/de-hyphenated" Form des Textes, und (c) ergaenzt um
    Treffer aus derselben Form, zusaetzlich mit den Nachbar-Referenztokens
    verschmolzen.

    (a) ist noetig, weil ein Set blind fuer Transposition ist:
    {"steigt","nicht"} == {"nicht","steigt"}, obwohl genau diese benachbarte
    Vertauschung die Form ist, die ein unsicheres HTR-Modell auf eng
    geschriebener Handschrift bevorzugt produziert.

    (b) ist noetig, weil ein abgetrenntes Negationspraefix ("un moeglich",
    "un-moeglich") pro Wort-Token identisch zum reinen Grundwort
    ("moeglich") tokenisiert -- das Praefix verschwindet spurlos. Wir
    entfernen daher zusaetzlich Leerraum UND Bindestrich-Glyphen aus dem
    Text und tokenisieren erneut; nur wenn dadurch tatsaechlich Tokens
    verschmelzen (d.h. sich die Tokenliste aendert), wird die verschmolzene
    Form zusaetzlich gegen die Wortliste geprueft. Ohne diese Bedingung
    wuerde z.B. das einzelne Wort "moeglich" (keine Leerzeichen/Bindestriche
    zum Entfernen) sich selbst ein zweites Mal beisteuern und Vergleiche
    verfaelschen. Das Ergebnis matcht bewusst NUR gegen die explizite
    CRITICAL_WORDS-Liste (kein generisches Praefix-Stripping) -- "Uniform"
    verschmilzt zu nichts und trifft daher nie "Form".

    (c) faengt den Fall, in dem das abgetrennte Praefix nicht im selben
    Diskrepanz-Bereich (`text`) steht, sondern in einem angrenzenden,
    zwischen allen Varianten UNSTRITTIGEN Referenztoken -- z.B. wenn
    collect_disagreements (consensus.py) einer Engine nur "un" als
    Diskrepanz zuweist, weil "moeglich" bei ihr identisch zur Referenz
    ausfaellt und daher als "equal"-Op ausserhalb der Spanne landet. Da
    `left_context`/`right_context` fuer ALLE Varianten einer Spanne
    identisch sind (siehe collect_disagreements), koennen kritische
    Woerter, die vollstaendig INNERHALB des Kontexts liegen (also nicht ueber
    die Kontext/Variante-Grenze verschmelzen), niemals einen Unterschied
    zwischen Varianten erzeugen -- sie tauchen bei jeder Variante identisch
    auf und heben sich beim Tupel-Vergleich in classify_span gegenseitig
    auf. Nur eine Verschmelzung, die tatsaechlich ueber die Grenze
    Kontext<->Variante hinweg ein neues, in der Wortliste stehendes Wort
    bildet, kann also je eine Diskrepanz ausloesen -- exakt wie bei (b)
    matcht auch das nur die GESAMTE verschmolzene Zeichenkette gegen die
    Liste, nie eine Teilzeichenkette.

    Wichtig: linker und rechter Nachbar werden EINZELN mit `text`
    verschmolzen (`left_context+text` und `text+right_context`), NIE beide
    gleichzeitig zu einer einzigen Dreier-Kette. Ein echtes Wort links vom
    abgetrennten Praefix (z.B. "ist" in "Das ist un moeglich") ist selbst
    kein Teil des Verbunds -- wuerde man es MIT anverschmelzen, entstuende
    "istunmoeglich", das (korrekterweise) auf keiner Liste steht, und die
    tatsaechlich relevante Verschmelzung "un"+"moeglich" -> "unmoeglich"
    ginge unter, weil beide Nachbarn in eine einzige, dadurch nicht mehr
    treffende Zeichenkette gepresst wuerden. Getrennt geprueft, feuert
    stattdessen zuverlaessig genau die Seite, auf der die Trennung
    tatsaechlich lag.

    NFKC-normalisiert `text`/`left_context`/`right_context` VOR jeder
    Tokenisierung (nicht erst in _canonical_word): _WORD_TOKEN_RE stuetzt sich
    auf \\w, das kombinierende Zeichen (Unicode-Kategorie Mn) ausschliesst. In
    NFD-kodiertem Text (z.B. macOS-Zwischenablage, per PATCH .../regions/{rid}
    eingereicht) ist z.B. "möglich" als "o" + kombinierendes Trema (U+0308)
    kodiert und wuerde schon HIER, beim ersten Tokenisieren, in zwei Tokens
    zerrissen ("mo"/"glich") -- keines davon steht in CRITICAL_WORDS, das Wort
    waere unsichtbar. _canonical_word() normalisiert zwar ebenfalls NFKC,
    bekommt die Fragmente aber erst NACH diesem Bruch zu sehen."""
    text = unicodedata.normalize("NFKC", text)
    left_context = unicodedata.normalize("NFKC", left_context)
    right_context = unicodedata.normalize("NFKC", right_context)
    canonical_words = {_canonical_word(w) for w in words}

    plain_tokens = [match.group(0) for match in _WORD_TOKEN_RE.finditer(text)]
    sequence = [
        canonical
        for canonical in (_canonical_word(t) for t in plain_tokens)
        if canonical in canonical_words
    ]

    def _merged_tokens_of(candidate: str) -> list[str]:
        # `candidate` ist hier stets aus bereits NFKC-normalisierten Teilen
        # verkettet (text/left_context/right_context, siehe oben) -- ein
        # erneutes normalize() ist daher im Regelfall ein no-op (NFKC ist
        # idempotent), sichert aber zusaetzlich den (theoretischen) Fall ab,
        # dass die Verkettung selbst an der Nahtstelle ein neues, noch nicht
        # normalisiertes Zeichen entstehen liesse.
        candidate = unicodedata.normalize("NFKC", candidate)
        stripped = "".join(
            ch for ch in candidate if ch not in _DASH_CHARS and not ch.isspace()
        )
        return [match.group(0) for match in _WORD_TOKEN_RE.finditer(stripped)]

    merged_tokens = _merged_tokens_of(text)
    # _is_blocked_fragment(plain_tokens): dieselbe Absicherung wie unten bei
    # der Kontext-Verschmelzung, hier auf die INNERHALB derselben Spanne zu
    # verschmelzenden Tokens angewendet -- ohne sie wuerde z.B. eine Spanne
    # mit dem Variantentext "je der" (zwei eigenstaendige, gebraeuchliche
    # Woerter) zu "jeder" verschmelzen und JEDE unabhaengige Abweichung an
    # dieser Stelle (z.B. "je der" vs. "wie der") faelschlich als kritisch
    # melden. "un" (in "un moeglich"/"un-moeglich") ist nicht in
    # MERGE_BLOCKED_FRAGMENTS und bleibt daher unangetastet erlaubt.
    if merged_tokens != plain_tokens and not _is_blocked_fragment(plain_tokens):
        sequence.extend(
            canonical
            for canonical in (_canonical_word(t) for t in merged_tokens)
            if canonical in canonical_words
        )

    context_matches: list[str] = []
    seen_context_matches: set[str] = set()
    # Nur versuchen, wenn `text` selbst mindestens ein Wort-Token beisteuert
    # (plain_tokens nicht leer) UND dieses Token selbst kein gebraeuchliches
    # Funktionswort ist (_is_blocked_fragment) -- sonst wuerde z.B. "je" (ein
    # eigenstaendiges Wort) mit einem rechten Nachbarn "der" zu "jeder"
    # verschmelzen und eine voellig unabhaengige Abweichung ("je" vs.
    # "wie"/"so") faelschlich als kritisch melden. Nur die Fragment-Seite
    # (`text`) wird so geprueft, NIE die Nachbar-Seite (left_context/
    # right_context) -- der Nachbar stammt immer aus echtem, unstrittigem
    # Fliesstext und waere so gut wie immer selbst ein echtes Wort; ihn zu
    # pruefen wuerde praktisch jede Verschmelzung blockieren (siehe
    # _is_blocked_fragment Docstring). Ohne die plain_tokens-Bedingung
    # wuerde z.B. eine reine Insertion (text == "") jeden bereits fuer sich
    # genommen kritischen Nachbarn (links ODER rechts) unveraendert
    # durchreichen -- "" + "ist konstant"[Nachbar]"konstant" wuerde dann
    # "konstant" *selbst* als vermeintlichen Verschmelzungstreffer zaehlen,
    # obwohl `text` gar nichts beigetragen hat. Das erzeugte einen echten
    # Regressionsfall: bei "Die Kraft ist nicht konstant." vs. "Die Kraft
    # ist konstant." kippte der gemeldete Grund von "critical_word:nicht"
    # auf "critical_word:konstant", weil die leere Variante den rechten
    # Nachbarn "konstant" unveraendert als eigenen Treffer einsammelte.
    if plain_tokens and not _is_blocked_fragment(plain_tokens):
        for candidate in (
            f"{left_context}{text}" if left_context else "",
            f"{text}{right_context}" if right_context else "",
        ):
            if not candidate:
                continue
            candidate_tokens = _merged_tokens_of(candidate)
            if candidate_tokens == plain_tokens:
                continue
            for canonical in (_canonical_word(t) for t in candidate_tokens):
                if canonical in canonical_words and canonical not in seen_context_matches:
                    seen_context_matches.add(canonical)
                    context_matches.append(canonical)
    sequence.extend(context_matches)

    return tuple(sequence)


def _first_sequence_diff(a: tuple[str, ...], b: tuple[str, ...]) -> str:
    """Findet die erste Position, an der sich zwei geordnete
    Kritisch-Wort-Sequenzen unterscheiden, und benennt eines der dort
    beteiligten Woerter (deterministisch alphabetisch gewaehlt, falls an
    dieser Position beide Seiten ein Wort haben -- z.B. bei einer
    Transposition wie "steigt"/"nicht")."""
    for word_a, word_b in zip(a, b):
        if word_a != word_b:
            return sorted((word_a, word_b))[0]
    if len(a) != len(b):
        longer = a if len(a) > len(b) else b
        return longer[min(len(a), len(b))]
    return ""


def classify_span(
    variants: Sequence[tuple[str, tuple[str, ...]]],
    config: CriticalTokenConfig,
    *,
    left_context: str = "",
    right_context: str = "",
) -> tuple[bool, str]:
    """Klassifiziert eine Menge konkurrierender Lesarten einer Textspanne.
    Gibt (True, Grund) zurueck, sobald IRGENDEIN Paar von Varianten sich
    bedeutungsveraendernd unterscheidet. Prioritaet (erster Treffer
    gewinnt): unclear > Zahlen > Einheiten > Symbole > kritische Woerter >
    chemische Gross-/Kleinschreibung > Fachvokabular.

    `left_context`/`right_context` sind die (unstrittigen) Referenztokens
    unmittelbar vor bzw. nach der Spanne -- je hoechstens eines, das reicht
    fuer den Anlagerungsfall, den sie abdecken (siehe
    _critical_word_sequence, Abschnitt (c)): ein per Leerzeichen
    abgetrenntes Negationspraefix landet als eigene, einzeltoken-kleine
    Diskrepanzspanne, deren einziger Nachbar auf der betroffenen Seite exakt
    ein Token entfernt liegt. Sie beeinflussen NUR die Kritikalitaets-
    beurteilung kritischer Woerter (Schritt 4) -- weder Zahlen, Einheiten,
    Symbole noch Fachvokabular werten sie aus."""
    texts = [text for text, _engines in variants]
    if not texts:
        return False, ""

    if any(UNCLEAR_SENTINEL in text for text in texts):
        return True, "unclear"

    base_text = texts[0]

    # 1. Zahlen
    base_numbers = numeric_values(base_text)
    for other in texts[1:]:
        if numeric_values(other) != base_numbers:
            return True, "number"

    # 2. Einheiten (inkl. SI-Praefix-Verwechslung, siehe _si_prefix_confusion)
    base_units = unit_tokens(base_text, config.units)
    for other in texts[1:]:
        if unit_tokens(other, config.units) != base_units:
            return True, "unit"
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if _si_prefix_confusion(texts[i], texts[j], config.units):
                return True, "unit"

    # 3. Symbole (Multimenge pro Variante)
    base_symbols: dict[str, int] = {}
    for ch in base_text:
        if ch in config.symbols:
            base_symbols[ch] = base_symbols.get(ch, 0) + 1
    for other in texts[1:]:
        other_symbols: dict[str, int] = {}
        for ch in other:
            if ch in config.symbols:
                other_symbols[ch] = other_symbols.get(ch, 0) + 1
        if other_symbols != base_symbols:
            differing = {
                ch
                for ch in set(base_symbols) | set(other_symbols)
                if base_symbols.get(ch, 0) != other_symbols.get(ch, 0)
            }
            symbol = sorted(differing)[0] if differing else ""
            return True, f"symbol:{symbol}"

    # 4. kritische Woerter (ordnungs- und anlagerungssensitiv, siehe
    # _critical_word_sequence)
    all_words = config.words | config.extra_words
    base_sequence = _critical_word_sequence(
        base_text, all_words, left_context=left_context, right_context=right_context
    )
    for other in texts[1:]:
        other_sequence = _critical_word_sequence(
            other, all_words, left_context=left_context, right_context=right_context
        )
        if other_sequence != base_sequence:
            return True, f"critical_word:{_first_sequence_diff(base_sequence, other_sequence)}"

    # 5. chemische Gross-/Kleinschreibung (z.B. "Co" vs. "CO")
    if config.subject == "chemie":
        casefolded = {text.casefold() for text in texts}
        if len(casefolded) == 1 and len(set(texts)) > 1:
            return True, "chemical_case"

    # 6. Fachvokabular
    if config.subject:
        subject_words = SUBJECT_TOKENS.get(config.subject, frozenset())
        base_subject = _critical_word_set(base_text, subject_words)
        for other in texts[1:]:
            if _critical_word_set(other, subject_words) != base_subject:
                return True, f"subject:{config.subject}"

    return False, ""
