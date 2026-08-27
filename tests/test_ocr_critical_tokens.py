"""Testet die Klassifikation bedeutungsveraendernder OCR-Abweichungen.

Deckt teacherassist_core/ocr/critical_tokens.py ab: classify_span
(Zeile 316), numeric_values (Zeile 241), unit_tokens (Zeile 266) und
CriticalTokenConfig.for_subject (Zeile 175). Die Reihenfolge, in der
classify_span seine Regeln prueft (Zahlen > Einheiten > Symbole > kritische
Woerter > chemische Gross-/Kleinschreibung > Fachvokabular), ist
absichtlich table-driven abgedeckt: jede CRITICAL_WORDS-Eintragung soll
"rundlaufen" (auftauchen -> als kritisch erkannt werden).
"""

from __future__ import annotations

import unicodedata
from decimal import Decimal

import pytest

from teacherassist_core.ocr.consensus import build_region, normalize_token
from teacherassist_core.ocr.critical_tokens import (
    CRITICAL_SYMBOLS,
    CRITICAL_WORDS,
    CriticalTokenConfig,
    _canonical_word,
    classify_span,
    numeric_values,
    unit_tokens,
)
from teacherassist_core.ocr.markup import UNCLEAR_SENTINEL
from teacherassist_core.ocr.types import OCRCandidate, RegionType


def _variants(*texts: str) -> list[tuple[str, tuple[str, ...]]]:
    """Baut eine variants-Liste wie sie classify_span erwartet, mit
    Platzhalter-Enginenamen A, B, C, ..."""
    engines = "ABCDEFGH"
    return [(text, (engines[i],)) for i, text in enumerate(texts)]


DEFAULT_CONFIG = CriticalTokenConfig()


@pytest.mark.parametrize("word", sorted(CRITICAL_WORDS))
def test_every_critical_word_round_trips(word):
    """Jedes Wort aus CRITICAL_WORDS (critical_tokens.py:26) muss, wenn es
    nur auf einer Seite auftaucht, als kritische Abweichung erkannt werden
    (classify_span, critical_tokens.py:316, Schritt 4). Der gemeldete Grund
    traegt die kanonisierte Schreibweise (_canonical_word,
    critical_tokens.py), da CRITICAL_WORDS bewusst sowohl Umlaut- als auch
    ASCII-Ersatzschreibweisen desselben Wortes enthaelt (z.B. "größer" und
    "groesser") und beide auf dieselbe kanonische Form abbilden."""
    variants = _variants(f"der wert ist {word}", "der wert ist anders")
    critical, reason = classify_span(variants, DEFAULT_CONFIG)
    assert critical is True
    assert reason == f"critical_word:{_canonical_word(word)}"


def test_canonical_word_and_normalize_token_agree_on_nfc_vs_nfd():
    """NFC ("größer", ein vorkomponiertes ö) und NFD (o + kombinierendes
    Trema U+0308) desselben Wortes sind byte-fuer-byte unterschiedlich,
    aber dasselbe Wort -- ein reiner Normalisierungsunterschied, keine
    inhaltliche Abweichung. Beide Ebenen der Pipeline muessen das
    identisch behandeln (siehe Auftrag Fix 3): consensus.normalize_token()
    normalisiert bereits seit jeher NFKC vor dem Falten; _canonical_word()
    (critical_tokens.py) tat das VOR diesem Fix nicht -- ohne NFKC-
    Normalisierung bildeten NFC- und NFD-"größer" auf unterschiedliche
    kanonische Formen ab und eine NFC/NFD-Diskrepanz waere als kritisch
    gemeldet worden (falsch-positiv). Zwei unterschiedliche
    Normalisierungsregeln in derselben Pipeline waeren sonst frueher oder
    spaeter auseinandergelaufen."""
    nfc = unicodedata.normalize("NFC", "größer")
    nfd = unicodedata.normalize("NFD", "größer")
    assert nfc != nfd, "Testaufbau erwartet tatsaechlich unterschiedliche Kodierungen"

    assert _canonical_word(nfc) == _canonical_word(nfd)
    assert normalize_token(nfc) == normalize_token(nfd)

    # HINWEIS (Historie): eine end-to-end classify_span()-Probe mit einer
    # NFD-kodierten Variante scheiterte NACH dem urspruenglichen Fix
    # (Faltreihenfolge in _canonical_word) weiterhin, aus einem damals
    # bewusst nicht angefassten Grund: _WORD_TOKEN_RE (r"[^\W\d_]+") zerlegte
    # ein NFD-"größer" schon BEIM Tokenisieren in zwei Tokens
    # ("gro"/"sser"), weil ein kombinierendes Trema (U+0308) kein
    # \w-Zeichen ist -- bevor _canonical_word() ueberhaupt zum Zug kam.
    # Dieser Luecke ist inzwischen (Folge-Runde) durch NFKC-Normalisierung
    # der Eingabe VOR jeder _WORD_TOKEN_RE-Anwendung geschlossen (siehe
    # _critical_word_set/_critical_word_sequence, critical_tokens.py) --
    # siehe test_nfd_input_no_longer_produces_false_negative_regression und
    # TestNfcNfdUmlautRoundTrip weiter unten fuer die end-to-end-Probe.


# --- Regressionstest: NFC- vs. NFD-kodierte Umlaut-/ß-Eingabe (dieser
# Auftrag) --------------------------------------------------------------
#
# Bestaetigter kritischer Falsch-Negativ: _WORD_TOKEN_RE (r"[^\W\d_]+")
# stuetzt sich auf \w, das kombinierende Zeichen (Unicode-Kategorie Mn)
# ausschliesst. In NFD-kodiertem Text (z.B. macOS-Zwischenablage, per PATCH
# .../regions/{rid} eingereicht) ist z.B. "größer" als "o" + kombinierendes
# Trema (U+0308) kodiert und zerfaellt BEIM Tokenisieren in zwei Tokens
# ("gro"/"ßer") -- bevor _canonical_word() ueberhaupt zum Zug kommt. Keines
# der Fragmente steht in CRITICAL_WORDS, das Wort wird unsichtbar. Fix:
# NFKC-Normalisierung der Eingabe VOR jeder _WORD_TOKEN_RE-Anwendung, in
# _critical_word_set und _critical_word_sequence (critical_tokens.py).


def test_nfd_word_token_re_split_reproduction():
    """Reproduziert die im Bericht dokumentierte Kernprobe woertlich."""
    import re
    import unicodedata as ud

    word_token_re = re.compile(r"[^\W\d_]+", re.UNICODE)
    assert word_token_re.findall("größer") == ["größer"]
    # Vor dem Fix zerfiel die NFD-Form in zwei Tokens; die Regex selbst ist
    # unveraendert (bewusst NICHT Teil dieses Fixes) -- die Eingabe wird
    # stattdessen VOR der Regex normalisiert (siehe critical_tokens.py).
    assert word_token_re.findall(ud.normalize("NFD", "größer")) == ["gro", "ßer"]


def test_nfd_input_no_longer_produces_false_negative_regression():
    """Exakte Reproduktion aus dem Bericht: eine NFD-kodierte Variante mit
    "möglich" muss GENAUSO kritisch erkannt werden wie die NFC-kodierte --
    vorher wurde dieselbe Diskrepanz bei NFD-Eingabe still schweigend
    unkritisch (False, "")."""
    nfc_variants = _variants("Das ist möglich", "Das ist denkbar")
    assert classify_span(nfc_variants, DEFAULT_CONFIG) == (True, "critical_word:moeglich")

    nfd_text = unicodedata.normalize("NFD", "Das ist möglich")
    assert nfd_text != "Das ist möglich"
    nfd_variants = _variants(nfd_text, "Das ist denkbar")
    assert classify_span(nfd_variants, DEFAULT_CONFIG) == (True, "critical_word:moeglich")


_UMLAUT_OR_ESZETT_CRITICAL_WORDS = tuple(
    sorted(w for w in CRITICAL_WORDS if any(ch in w for ch in "äöüÄÖÜß"))
)


class TestNfcNfdUmlautRoundTrip:
    """Jedes umlaut-/ß-tragende Wort aus CRITICAL_WORDS muss unter NFC- UND
    NFD-Kodierung des umgebenden Satzes dasselbe classify_span-Urteil (Wert
    UND Grund) liefern -- ein reiner Kodierungsunterschied darf niemals das
    Ergebnis aendern."""

    def test_setup_actually_covers_umlaut_words(self):
        # Absicherung gegen ein leeres Parametrize (z.B. durch eine
        # zukuenftige Aenderung an CRITICAL_WORDS), das den Test unten
        # unbemerkt zu einem No-Op machen wuerde.
        assert len(_UMLAUT_OR_ESZETT_CRITICAL_WORDS) >= 6

    @pytest.mark.parametrize("word", _UMLAUT_OR_ESZETT_CRITICAL_WORDS)
    def test_nfc_and_nfd_forms_yield_identical_verdict_and_reason(self, word):
        base_nfc = unicodedata.normalize("NFC", f"der wert ist {word}")
        base_nfd = unicodedata.normalize("NFD", f"der wert ist {word}")
        # ß (U+00DF) hat KEINE kanonische Zerlegung -- anders als oe/ae/ue
        # bleibt es unter NFD unveraendert. Nur bei Woertern mit einem
        # tatsaechlich zerlegbaren Umlaut MUESSEN sich NFC- und NFD-Form
        # ueberhaupt unterscheiden (Testaufbau-Absicherung); ein reines
        # ß-Wort wie "außer" ist unter beiden Formen bytegleich und bleibt
        # trotzdem im Parametrize, weil es genauso durch die neue
        # Normalisierung laufen und identisch urteilen muss.
        if any(ch in word for ch in "äöüÄÖÜ"):
            assert base_nfc != base_nfd, "Testaufbau erwartet tatsaechlich unterschiedliche Kodierungen"
        other = "der wert ist anders"

        critical_nfc, reason_nfc = classify_span(_variants(base_nfc, other), DEFAULT_CONFIG)
        critical_nfd, reason_nfd = classify_span(_variants(base_nfd, other), DEFAULT_CONFIG)

        assert critical_nfc is True
        assert (critical_nfc, reason_nfc) == (critical_nfd, reason_nfd)
        assert reason_nfc == f"critical_word:{_canonical_word(word)}"

    @pytest.mark.parametrize("word", _UMLAUT_OR_ESZETT_CRITICAL_WORDS)
    def test_mixed_nfc_nfd_same_word_is_not_critical(self, word):
        # Falsch-Positiv-Richtung: dieselbe Wortform, einmal NFC- einmal
        # NFD-kodiert, IST dasselbe Wort und darf NICHT als kritische
        # Diskrepanz gemeldet werden.
        nfc = f"der wert ist {word}"
        nfd = unicodedata.normalize("NFD", nfc)
        if any(ch in word for ch in "äöüÄÖÜ"):
            assert nfc != nfd, "Testaufbau erwartet tatsaechlich unterschiedliche Kodierungen"
        assert classify_span(_variants(nfc, nfd), DEFAULT_CONFIG) == (False, "")


def test_symbol_check_unaffected_by_nfkc_normalisation():
    """CRITICAL_SYMBOLS-Erkennung (Schritt 3) darf durch die NFKC-
    Normalisierung dieses Fixes NICHT veraendert werden: sie wird
    ausschliesslich in den Wort-Pfaden (_critical_word_set/
    _critical_word_sequence, Schritt 4/6) angewendet, niemals auf den
    rohen Text, den Schritt 3 zeichenweise gegen CRITICAL_SYMBOLS
    vergleicht. Besonders riskant waere µ (MICRO SIGN, U+00B5): NFKC
    normalisiert es auf das griechische Kleinbuchstaben-My (U+03BC), das
    NICHT in CRITICAL_SYMBOLS steht -- wuerde Schritt 3 (versehentlich) auf
    normalisiertem statt rohem Text arbeiten, wuerde ein µ-Symbol
    unsichtbar."""
    micro_sign = "µ"  # MICRO SIGN, NICHT das griechische My (U+03BC)
    assert unicodedata.normalize("NFKC", micro_sign) != micro_sign
    assert micro_sign in CRITICAL_SYMBOLS

    critical, reason = classify_span(_variants("F=µN", "F=N"), DEFAULT_CONFIG)
    assert critical is True
    assert reason == "symbol:µ"


@pytest.mark.parametrize(
    "text_a, text_b",
    [
        ("a+b", "a-b"),
        ("a<b", "a>b"),
        ("a≤b", "a<b"),
        ("a→b", "a⇌b"),
    ],
)
def test_symbol_flips_are_critical(text_a, text_b):
    """Symbol-Umkehrungen (critical_tokens.py:92 CRITICAL_SYMBOLS) muessen
    als kritisch mit reason.startswith("symbol:") erkannt werden (Schritt 3,
    vor kritischen Woertern aber nach Zahlen/Einheiten geprueft)."""
    critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
    assert critical is True
    assert reason.startswith("symbol:")


class TestNumericValues:
    """numeric_values (critical_tokens.py:241) normalisiert deutsche
    Zahlformate zu Decimal. Jede Differenz in Wert, Anzahl oder Reihenfolge
    ist bedeutungsveraendernd."""

    def test_german_comma_and_english_dot_are_the_same_value(self):
        # "3,5" (deutsches Dezimalkomma) und "3.5" (durch OCR haeufig
        # eingefuegter englischer Punkt) muessen auf denselben Decimal-Wert
        # normalisieren -- siehe critical_tokens.py:209 _parse_german_number.
        assert numeric_values("3,5") == numeric_values("3.5") == (Decimal("3.5"),)

    def test_comma_five_vs_thirty_five_is_a_different_value(self):
        assert numeric_values("3,5") != numeric_values("35")
        assert numeric_values("35") == (Decimal("35"),)

    def test_german_thousands_separator_parses_correctly(self):
        # "1.234,5" ist deutsche Tausendergruppierung + Dezimalkomma -> 1234.5.
        assert numeric_values("1.234,5") == (Decimal("1234.5"),)

    def test_negative_sign_changes_the_value(self):
        assert numeric_values("-4") == (Decimal("-4"),)
        assert numeric_values("4") == (Decimal("4"),)
        assert numeric_values("-4") != numeric_values("4")

    @pytest.mark.parametrize(
        "text_a, text_b",
        [
            ("3,5", "35"),
            ("-4", "4"),
            ("Ergebnis: -3,5 m", "Ergebnis: 3,5 m"),
            ("+5 V", "-5 V"),
        ],
    )
    def test_differing_numbers_are_critical(self, text_a, text_b):
        critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
        assert critical is True
        assert reason == "number"

    def test_same_value_different_spelling_is_not_critical_via_numbers(self):
        critical, reason = classify_span(_variants("3,5", "3.5"), DEFAULT_CONFIG)
        assert (critical, reason) == (False, "")


class TestUnitTokens:
    """unit_tokens (critical_tokens.py:266) erkennt bekannte Einheiten
    casefolded; SI-Praefix-Verwechslungen (z.B. mV vs. MV) werden zusaetzlich
    ueber _si_prefix_confusion (critical_tokens.py:278) gefangen, da der
    casefolded Vergleich allein "mv" == "mv" liefern wuerde."""

    @pytest.mark.parametrize(
        "text_a, text_b",
        [
            ("5 m", "5 km"),
            ("3 N", "3 J"),
            ("10 mV", "10 MV"),
        ],
    )
    def test_differing_units_are_critical(self, text_a, text_b):
        critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
        assert critical is True
        assert reason == "unit"

    def test_unit_tokens_extracts_known_units_casefolded(self):
        assert unit_tokens("5 m") == ("m",)
        assert unit_tokens("5 km") == ("km",)


def test_chemical_symbol_case_critical_only_for_chemistry_subject():
    """"Co" (Cobalt) vs. "CO" (Kohlenstoffmonoxid) ist nur bei
    subject="chemie" kritisch (classify_span Schritt 5, critical_tokens.py:
    ~355 chemical_case) -- ohne Fachkontext waere das sonst zu viele
    Falsch-Positive fuer andere Faecher."""
    variants = _variants("Co", "CO")

    critical_default, reason_default = classify_span(variants, DEFAULT_CONFIG)
    assert (critical_default, reason_default) == (False, "")

    chemie_config = CriticalTokenConfig(subject="chemie")
    critical_chemie, reason_chemie = classify_span(variants, chemie_config)
    assert critical_chemie is True
    assert reason_chemie == "chemical_case"


def test_unclear_sentinel_is_always_critical():
    """Der UNCLEAR_SENTINEL (markup.py) muss in jeder Konstellation Vorrang
    vor allen anderen Regeln haben (classify_span, allererste Pruefung)."""
    variants = _variants(f"das ist {UNCLEAR_SENTINEL} klar", "das ist ganz klar")
    critical, reason = classify_span(variants, DEFAULT_CONFIG)
    assert critical is True
    assert reason == "unclear"


@pytest.mark.parametrize(
    "text_a, text_b",
    [
        ("Auto", "Autos"),
        ("daher", "deshalb"),
    ],
)
def test_synonym_like_differences_are_not_critical(text_a, text_b):
    """Negativkontrolle: unterschiedliche, aber bedeutungsgleiche/-aehnliche
    Woerter duerfen NICHT als kritisch markiert werden, sonst waere jede
    OCR-Abweichung kritisch und die Review-Warteschlange nutzlos."""
    critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
    assert (critical, reason) == (False, "")


def test_config_overrides_merge_over_defaults():
    """CriticalTokenConfig.for_subject (critical_tokens.py:175) mischt eine
    Overrides-Struktur (Form wie load_overrides sie liefert, critical_tokens.py:
    201) flach ueber die Modul-Defaults: globale words/symbols erweitern alle
    Faecher, subjects[<fach>] landet nur in extra_words fuer dieses Fach."""
    overrides = {
        "words": ["fabelwort"],
        "symbols": "§",
        "subjects": {"physik": ["quantenpunkt"]},
    }

    config = CriticalTokenConfig.for_subject("physik", overrides)

    assert config.subject == "physik"
    assert CRITICAL_WORDS <= config.words
    assert "fabelwort" in config.words
    assert "§" in config.symbols
    assert "quantenpunkt" in config.extra_words
    # Ein anderes Fach bekommt die physik-spezifische Erweiterung NICHT.
    other_config = CriticalTokenConfig.for_subject("chemie", overrides)
    assert "quantenpunkt" not in other_config.extra_words
    assert "fabelwort" in other_config.words  # globale Overrides gelten ueberall


# --- Regressionstests: Negationsanlagerung / Transposition ------------------
#
# Zwei bestaetigte kritische Falsch-Negative in classify_span Schritt 4
# (kritische Woerter): der bisherige Set-Vergleich (_critical_word_set) war
# blind fuer (a) Reihenfolge -- {"steigt","nicht"} == {"nicht","steigt"} --
# und (b) Anlagerung -- "un moeglich" tokenisiert zu ("un","moeglich"), deren
# kritische Menge {"moeglich"} identisch zur reinen Grundform ist, das
# Negationspraefix verschwindet spurlos. Die Faelle unten reproduzieren
# beide Luecken und pinnen den Fix (_critical_word_sequence).

# Alle Trennzeichen, ueber die "un<sep>moeglich" zu "unmoeglich" verschmelzen
# soll: Leerzeichen sowie ASCII-Bindestrich + alle in CRITICAL_SYMBOLS neu
# ergaenzten Unicode-Bindestrich-Glyphen (critical_tokens.py CRITICAL_SYMBOLS).
_SEPARATORS = [
    " ",
    "-",       # U+002D ASCII-Bindestrich
    "‐",  # ‐ Hyphen
    "‑",  # ‑ Non-Breaking Hyphen
    "‒",  # ‒ Figure Dash
    "–",  # – En Dash
    "—",  # — Em Dash
    "―",  # ― Horizontal Bar
    "−",  # − Minus Sign
]


@pytest.mark.parametrize("sep", _SEPARATORS, ids=lambda s: f"U+{ord(s):04X}")
@pytest.mark.parametrize(
    "prefix, base",
    [
        ("un", "möglich"),
        ("un", "gleich"),
        ("un", "wahr"),
    ],
)
def test_split_negation_prefix_is_critical(prefix, base, sep):
    """Ein per Leerzeichen oder Bindestrich-Glyphe vom Grundwort getrenntes
    Negationspraefix ("un moeglich", "un-moeglich", "un—moeglich", ...) muss
    als kritisch erkannt werden, weil das Konkatenat (z.B. "unmoeglich")
    selbst in CRITICAL_WORDS steht. Ueberdeckt sowohl den Fall, in dem die
    Bindestrich-Glyphe zusaetzlich schon ueber Schritt 3 (Symbole) greift,
    als auch den reinen Leerzeichen-Fall, den nur Schritt 4 fangen kann."""
    split_text = f"{prefix}{sep}{base}"
    critical, reason = classify_span(_variants(split_text, base), DEFAULT_CONFIG)
    assert critical is True
    # Bei einer Bindestrich-Glyphe darf die Meldung bereits ueber Schritt 3
    # (Symbole) kommen (reason startswith "symbol:") -- das ist die schon
    # bestehende, nur zufaellig fuer ASCII "-" funktionierende Erkennung, die
    # jetzt fuer ALLE Bindestrich-Glyphen greift. Beim reinen Leerzeichen
    # bleibt nur Schritt 4 (kritische Woerter) uebrig.
    assert reason.startswith("symbol:") or reason.startswith("critical_word:")


def test_split_negation_prefix_via_space_names_merged_word_in_reason():
    """Ohne Bindestrich (reines Leerzeichen) kann nur Schritt 4 greifen; der
    Grund muss dann explizit das verschmolzene Negationswort benennen."""
    critical, reason = classify_span(_variants("un möglich", "möglich"), DEFAULT_CONFIG)
    assert critical is True
    assert reason == "critical_word:unmoeglich"


def test_jeder_still_in_critical_words():
    """"jeder" must stay in CRITICAL_WORDS even though it collides with the
    merge mechanism below ("je"+"der" -> "jeder", see
    MERGE_BLOCKED_FRAGMENTS): "jeder Schüler" vs. "der Schüler" -- every
    student versus THE student -- is grade-relevant and is the case "jeder"
    actually earns its place for. When a quantifier like "jeder" is swapped
    for a genuinely non-critical word, nothing else in classify_span would
    catch it; when it is swapped for another critical word, the ordered
    critical-word-sequence comparison (Schritt 4) already catches that
    regardless of whether "jeder" is on the list. A future reader who
    rediscovers the "je"+"der" collision should remove ITS CAUSE
    (MERGE_BLOCKED_FRAGMENTS is the fix) rather than remove this word."""
    assert "jeder" in CRITICAL_WORDS


def test_same_span_je_der_collision_no_longer_fires():
    """Pre-existing false positive (present on main before this round,
    independent of the neighbour-context feature): the de-spaced merge in
    _critical_word_sequence used to fuse a variant text that happened to
    contain "je" immediately followed by "der" -- both are common,
    independent, standalone German words -- into "jeder" and report a
    completely unrelated difference ("je" vs. "wie"/"so") as critical.
    MERGE_BLOCKED_FRAGMENTS now refuses the merge whenever the fragment
    (`text`) itself contains a common function word, so this no longer
    fires. "un" is deliberately NOT in that list -- it is never a
    standalone German word, only a bound negation prefix -- so
    "un moeglich"/"un gleich" stay caught (see tests above)."""
    assert classify_span(_variants("je der", "wie der"), DEFAULT_CONFIG) == (False, "")
    assert classify_span(_variants("je der", "so der"), DEFAULT_CONFIG) == (False, "")


class TestTransposedCriticalWords:
    """Schritt 4 vergleicht seit dem Fix geordnete Sequenzen statt Sets, damit
    eine Transposition benachbarter kritischer Woerter -- die typische Form,
    in der ein unsicheres HTR-Modell auf eng geschriebener Handschrift
    stolpert -- nicht mehr unsichtbar bleibt."""

    def test_two_word_transposition_is_critical(self):
        critical, reason = classify_span(
            _variants("steigt nicht", "nicht steigt"), DEFAULT_CONFIG
        )
        assert critical is True
        assert reason.startswith("critical_word:")

    def test_two_word_transposition_critical_regardless_of_engine_order(self):
        # Symmetrie-Kontrolle: welche Variante zuerst kommt, darf das
        # Ergebnis nicht aendern.
        critical_a, _ = classify_span(_variants("steigt nicht", "nicht steigt"), DEFAULT_CONFIG)
        critical_b, _ = classify_span(_variants("nicht steigt", "steigt nicht"), DEFAULT_CONFIG)
        assert critical_a is True
        assert critical_b is True

    def test_three_word_transposition_is_critical(self):
        critical, reason = classify_span(
            _variants("nicht mehr möglich", "möglich mehr nicht"), DEFAULT_CONFIG
        )
        assert critical is True
        assert reason.startswith("critical_word:")


@pytest.mark.parametrize(
    "text_a, text_b",
    [
        ("Uniform", "Form"),
        ("Unterricht", "Bericht"),
        ("integriert", "gefiltert"),
    ],
)
def test_uniform_vs_form_is_not_critical(text_a, text_b):
    """Ueber-Korrektur-Wache: der Fix darf NICHT zu generischem
    Praefix-Stripping werden. "Uniform" enthaelt zwar die Buchstabenfolge
    "un", verschmilzt aber zu nichts, das in CRITICAL_WORDS steht (anders als
    das explizite "un"+"moeglich" -> "unmoeglich"), muss also unkritisch
    bleiben. Ebenso fuer die weiteren Kontrollpaare."""
    critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
    assert (critical, reason) == (False, "")


def test_ist_konstant_vs_bleibt_konstant_is_not_critical():
    """Pinnt die bewusste Nicht-Korrektur aus der Spezifikation: "ist
    konstant" und "bleibt konstant" sind bedeutungsgleich, obwohl
    "konstant" auf der Polaritaets-Liste steht. Eine blindere Regel ("jede
    Token-Sequenz-Differenz, bei der irgendeine Variante ein kritisches Wort
    enthaelt, ist kritisch") wuerde hier faelschlich anschlagen."""
    critical, reason = classify_span(
        _variants("ist konstant", "bleibt konstant"), DEFAULT_CONFIG
    )
    assert (critical, reason) == (False, "")


# --- Re-Test aller bestehenden Negativkontrollen ----------------------------
# (identisch zu den Faellen weiter oben in dieser Datei -- hier noch einmal
# explizit gebuendelt, um zu belegen, dass der Fix ihre Falsch-Positiv-Rate
# nicht veraendert hat.)
@pytest.mark.parametrize(
    "text_a, text_b",
    [
        ("Auto", "Autos"),
        ("daher", "deshalb"),
    ],
)
def test_existing_synonym_negative_controls_still_hold_after_fix(text_a, text_b):
    critical, reason = classify_span(_variants(text_a, text_b), DEFAULT_CONFIG)
    assert (critical, reason) == (False, "")


class TestEndToEndBuildRegion:
    """Reproduziert die beiden bestaetigten Bugs end-to-end durch
    build_region (teacherassist_core/ocr/consensus.py), in beiden
    Engine-Reihenfolgen -- analog zu test_ocr_consensus.py::
    test_negation_detected_regardless_of_engine_order, das denselben
    Beweisstil fuer den urspruenglichen Insertion-Bug nutzt."""

    def _candidate(self, engine: str, text: str, *, confidence: float = 0.95) -> OCRCandidate:
        return OCRCandidate(
            engine=engine, text=text, raw_text=text, confidence=confidence, tokens=(),
        )

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("un möglich", "möglich"),
            ("möglich", "un möglich"),
        ],
        ids=["htr_has_split_negation", "vlm_has_split_negation"],
    )
    def test_pure_space_split_negation_prefix_is_critical_e2e(self, htr_text, vlm_text):
        """FORMERLY a known, documented gap (see git history /
        test_pure_space_split_negation_prefix_NOT_caught_e2e_known_gap):
        unlike the em-dash/hyphen and transposition cases below, the
        pure-space-separated split ("un moeglich" vs "moeglich") used to NOT
        reach has_critical_uncertainty=True through build_region, even after
        the classify_span de-spaced-merge fix. Root cause was one level up,
        in collect_disagreements (consensus.py): "un möglich" (2 reference
        tokens) vs "möglich" (1 token) aligns via difflib such that
        "möglich" itself matches as an "equal" op on both sides, so the
        disagreement span collect_disagreements handed to classify_span was
        ONLY "un" vs "" -- "möglich" never appeared in the span at all, so
        _critical_word_sequence's de-spaced merge (which needs the WHOLE
        phrase together) never got a chance to fire.

        Fixed by giving classify_span the adjacent, UNSTRITTIGEN reference
        tokens as left_context/right_context (see its docstring and
        collect_disagreements in consensus.py, which now looks up
        ref_raw[start-1]/ref_raw[end]): for the "un"-only span, the
        right_context is "möglich" (agreed by both engines, hence never
        part of the span), so classify_span can test "un"+"möglich" ==
        "unmöglich" -- in CRITICAL_WORDS -- against the word list, without
        the span itself ever growing wider. consensus_text and agreement
        are entirely unaffected; only the criticality judgement gains this
        context."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            (unicodedata.normalize("NFD", "Das ist möglich"), "Das ist denkbar"),
            ("Das ist denkbar", unicodedata.normalize("NFD", "Das ist möglich")),
        ],
        ids=["nfd_first", "nfd_second"],
    )
    def test_nfd_critical_word_is_detected_e2e_both_engine_orders(self, htr_text, vlm_text):
        """Dieser Auftrag: eine NFD-kodierte Variante (z.B. macOS-
        Zwischenablage) mit einem umlauttragenden CRITICAL_WORDS-Eintrag
        muss end-to-end genau wie die NFC-kodierte Form als kritisch
        erkannt werden, in BEIDEN Engine-Reihenfolgen."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("un gleich", "gleich"),
            ("gleich", "un gleich"),
        ],
        ids=["htr_has_split_negation", "vlm_has_split_negation"],
    )
    def test_pure_space_split_ungleich_negation_prefix_is_critical_e2e(self, htr_text, vlm_text):
        """Same mechanism as test_pure_space_split_negation_prefix_is_critical_e2e
        above, for a second word from CRITICAL_WORDS reachable through the
        merge path ("un" + "gleich" -> "ungleich"), proving the fix is not
        accidentally specific to "moeglich"."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("un möglich zu lösen", "möglich zu lösen"),
            ("möglich zu lösen", "un möglich zu lösen"),
        ],
        ids=["htr_has_split_negation", "vlm_has_split_negation"],
    )
    def test_split_negation_as_first_token_of_line_left_context_empty_e2e(
        self, htr_text, vlm_text
    ):
        """Boundary case: the split negation prefix ("un") is the very
        FIRST reference token of the line, so left_context is legitimately
        "" (collect_disagreements' `start > 0` guard), while right_context
        ("möglich") is populated -- proving classify_span's
        variant+right_context merge path fires correctly even when there is
        nothing at all on the other side."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("das ist un", "das ist un möglich"),
            ("das ist un möglich", "das ist un"),
        ],
        ids=["htr_missing_moeglich", "vlm_missing_moeglich"],
    )
    def test_split_negation_as_last_token_of_line_right_context_empty_e2e(
        self, htr_text, vlm_text
    ):
        """Boundary case: one engine's reading ends right after the split
        negation prefix ("un" is its very last token), so right_context is
        legitimately "" (collect_disagreements' `end < len(ref_raw)` guard)
        for the span both engines are compared over, while left_context
        ("un" itself, from the reading that has it) is populated on the
        OTHER side of the comparison -- proving classify_span's
        left_context+variant merge path fires correctly at this boundary
        too, symmetric to the first-token case above."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "text_a, text_b",
        [
            ("Er trägt heute eine Uniform zur Feier", "Er trägt heute eine Form zur Feier"),
            ("Der Unterricht beginnt um acht Uhr", "Der Bericht beginnt um acht Uhr"),
            ("Das Ergebnis ist integriert dargestellt", "Das Ergebnis ist gefiltert dargestellt"),
            ("Sie sagt daher nichts weiter dazu", "Sie sagt deshalb nichts weiter dazu"),
        ],
        ids=["uniform_vs_form", "unterricht_vs_bericht", "integriert_vs_gefiltert", "daher_vs_deshalb"],
    )
    def test_no_accidental_cross_boundary_formation_at_span_neighbours_e2e(
        self, text_a, text_b
    ):
        """Negative controls WITH real neighbouring context words on both
        sides of the differing token (unlike the bare-word versions of these
        pairs earlier in this file) -- proving that giving classify_span
        access to left_context/right_context does not turn ordinary,
        unrelated neighbouring words into accidental critical-word matches
        across the span boundary. Each pair differs by exactly one word,
        embedded in an otherwise identical sentence."""
        candidates = [
            self._candidate("htr", text_a),
            self._candidate("ollama_vlm", text_b, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is False

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("un—möglich", "möglich"),
            ("möglich", "un—möglich"),
        ],
        ids=["htr_has_em_dash_negation", "vlm_has_em_dash_negation"],
    )
    def test_em_dash_negation_prefix_is_critical_e2e(self, htr_text, vlm_text):
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("steigt nicht", "nicht steigt"),
            ("nicht steigt", "steigt nicht"),
        ],
        ids=["htr_transposed", "vlm_transposed"],
    )
    def test_transposed_negation_is_critical_e2e(self, htr_text, vlm_text):
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("Ich mag je der Klasse", "Ich mag wie der Klasse"),
            ("Ich mag wie der Klasse", "Ich mag je der Klasse"),
            ("Ich mag je der Klasse", "Ich mag so der Klasse"),
            ("Ich mag so der Klasse", "Ich mag je der Klasse"),
        ],
        ids=["je_vs_wie", "wie_vs_je", "je_vs_so", "so_vs_je"],
    )
    def test_jeder_collision_no_longer_fires_e2e(self, htr_text, vlm_text):
        """The false positive reported in the previous round: "je" (in
        collect_disagreements' single-token disagreement span) sits right
        next to the agreed-upon reference token "der", so the
        neighbour-context merge used to be able to form "jeder" -- a
        completely unrelated, non-critical difference ("je" vs. "wie"/"so")
        was reported as critical purely because of that adjacency.
        MERGE_BLOCKED_FRAGMENTS now refuses this because "je" (the fragment
        side, i.e. the variant text itself) is a common standalone German
        word, not a bound prefix like "un". Both engine orders and both
        substitute words are covered."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is False

    @pytest.mark.parametrize(
        "htr_text, vlm_text",
        [
            ("jeder Schüler", "der Schüler"),
            ("der Schüler", "jeder Schüler"),
        ],
        ids=["htr_has_jeder", "vlm_has_jeder"],
    )
    def test_jeder_quantifier_swap_stays_critical_e2e(self, htr_text, vlm_text):
        """"jeder" must stay caught when it is the actual, direct
        disagreement (not an accidental merge byproduct): "jeder Schüler"
        (every student) vs. "der Schüler" (the student) is grade-relevant
        and is exactly why "jeder" stays in CRITICAL_WORDS despite the
        "je"+"der" merge collision fixed above -- this is the ordinary
        direct-word-list match (Schritt 4, step 1), entirely unaffected by
        MERGE_BLOCKED_FRAGMENTS, which only ever suppresses the MERGE
        attempt, never a direct match of a whole token against the list."""
        candidates = [
            self._candidate("htr", htr_text),
            self._candidate("ollama_vlm", vlm_text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification="student_submission",
        )
        assert region.has_critical_uncertainty is True
