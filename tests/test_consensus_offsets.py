"""Testet char_start/char_end auf Disagreement (types.py) und deren
Herkunft aus consensus.render_consensus_with_offsets().

Hintergrund (siehe Auftrag): die Review-UI fand Diskrepanz-Klammern bisher
per Regex-Scan im gerenderten consensus_text und paarte den i-ten Treffer
mit disagreements[i]. Das ist aus zwei Gruenden unreparierbar
client-seitig: (1) eine Mehrwort-Spanne rendert eine einzige Klammer ueber
mehrere Whitespace-Tokens hinweg, sodass Tokenzaehlen nicht funktioniert;
(2) eine synthetisierte Klammer ist byte-identisch zu gedrucktem Text im
Originaldokument (z.B. einem Mehrfachauswahlfeld "[ja|nein?]" auf einem
Pruefungsbogen) -- nichts unterscheidet sie im Text selbst. Die Reparatur:
render_consensus_with_offsets() kennt beim Aufbau des Strings Stueck fuer
Stueck den exakten Zeichenbereich jeder Klammer und traegt ihn auf das
jeweilige Disagreement-Objekt (char_start/char_end); consensus_text selbst
bleibt dabei byte-identisch zu vorher (siehe test_ocr_consensus.py::
test_render_consensus_bracket_formats, hier NICHT editiert).

Diese Datei ist bewusst getrennt von test_ocr_consensus.py (Kollisionsrisiko
mit einem parallel arbeitenden Agenten, siehe Auftrag).
"""

from __future__ import annotations

import pytest

from teacherassist_core.ocr.consensus import (
    build_region,
    render_consensus,
    render_consensus_with_offsets,
)
from teacherassist_core.ocr.critical_tokens import CriticalTokenConfig
from teacherassist_core.ocr.types import Disagreement, OCRCandidate, RegionType

DEFAULT_CONFIG = CriticalTokenConfig()


def _candidate(
    engine: str,
    text: str,
    *,
    raw_text: str | None = None,
    confidence: float = 0.95,
    tokens: tuple[str, ...] = (),
) -> OCRCandidate:
    return OCRCandidate(
        engine=engine,
        text=text,
        raw_text=raw_text if raw_text is not None else text,
        confidence=confidence,
        tokens=tokens,
    )


def test_offset_bracket_shapes():
    """char_start/char_end muss fuer jede Klammerform -- Loeschung,
    Einfuegung, Zweiweg, Dreiweg, eine Mehrwort-Spanne (die client-seitig
    per Whitespace in zwei Tokens zerfaellt), eine Klammer an Position 0
    und eine am Stringende -- exakt den tatsaechlich gerenderten
    Klammerausschnitt liefern: consensus_text[char_start:char_end] ==
    Klammer. Deckt zugleich ab, dass render_consensus() (der duenne
    String-Wrapper) weiterhin denselben Text liefert wie
    render_consensus_with_offsets()."""
    cases = [
        # (ref_tokens, disagreement, erwarteter_text, erwartete_klammer)
        (
            ["a", "nicht", "b"],
            Disagreement(
                start=1, end=2,
                variants=(("nicht", ("htr",)), ("", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            "a [nicht?] b",
            "[nicht?]",
        ),
        (
            ["a", "b"],
            Disagreement(
                start=1, end=1,
                variants=(("", ("htr",)), ("nicht", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            "a [+nicht?] b",
            "[+nicht?]",
        ),
        (
            ["Ergebnis:", "3,5", "m"],
            Disagreement(
                start=1, end=2,
                variants=(("3,5", ("htr",)), ("8,5", ("tesseract",))),
                critical=True, reason="number",
            ),
            "Ergebnis: [3,5|8,5?] m",
            "[3,5|8,5?]",
        ),
        (
            ["Formel:", "Co"],
            Disagreement(
                start=1, end=2,
                variants=(("Co", ("htr",)), ("CO", ("tesseract",)), ("C0", ("paddleocr_vl",))),
                critical=True, reason="chemical_case",
            ),
            "Formel: [Co|CO|C0?]",
            "[Co|CO|C0?]",
        ),
        (
            # Mehrwort-Spanne: EINE Diskrepanz, deren Klammer bei naivem
            # Whitespace-Tokenisieren in ZWEI Tokens zerfaellt ("[nicht" /
            # "wirklich|kaum?]") -- genau der Fall, an dem Tokenzaehlen
            # scheitert (siehe Auftrag, Grund 1).
            ["Das", "ist", "nicht", "wirklich", "klar"],
            Disagreement(
                start=2, end=4,
                variants=(("nicht wirklich", ("htr",)), ("kaum", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            "Das ist [nicht wirklich|kaum?] klar",
            "[nicht wirklich|kaum?]",
        ),
        (
            # Klammer an Position 0.
            ["nicht", "klar"],
            Disagreement(
                start=0, end=1,
                variants=(("nicht", ("htr",)), ("", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            "[nicht?] klar",
            "[nicht?]",
        ),
        (
            # Klammer am Stringende.
            ["klar", "nicht"],
            Disagreement(
                start=1, end=2,
                variants=(("nicht", ("htr",)), ("", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            "klar [nicht?]",
            "[nicht?]",
        ),
    ]
    for ref_tokens, disagreement, expected_text, expected_bracket in cases:
        text, offsets = render_consensus_with_offsets(ref_tokens, [disagreement])
        assert text == expected_text
        assert render_consensus(ref_tokens, [disagreement]) == expected_text
        assert len(offsets) == 1
        d = offsets[0]
        assert text[d.char_start:d.char_end] == expected_bracket


@pytest.mark.parametrize(
    "htr_text, tesseract_text",
    [
        (
            "Ist Newton II anwendbar? [ja|nein?] Die Kraft ist konstant.",
            "Ist Newton II anwendbar? [ja|nein?] Die Kraft ist nicht konstant.",
        ),
        (
            "Ist Newton II anwendbar? [ja|nein?] Die Kraft ist nicht konstant.",
            "Ist Newton II anwendbar? [ja|nein?] Die Kraft ist konstant.",
        ),
    ],
    ids=["htr_has_negation", "tesseract_has_negation"],
)
def test_reproduction_printed_bracket_is_not_the_real_disagreement(htr_text, tesseract_text):
    """Der Reproduktionsfall aus dem Auftrag: der Referenztext enthaelt
    bereits woertlich eine gedruckte "[ja|nein?]"-Klammer (z.B. ein
    Mehrfachauswahlfeld auf einem Pruefungsbogen) UND es gibt eine echte
    kritische Diskrepanz ("nicht"). Ein Regex-Scan kann die gedruckte
    Klammer nicht von einer synthetisierten unterscheiden (Auftrag, Grund
    2) -- char_start/char_end koennen es, weil sie beim Rendern gesetzt
    werden, nicht nachtraeglich im Text gesucht. Parametrisiert ueber
    beide Engine-Reihenfolgen: welche Engine Referenz wird, darf das
    Ergebnis nicht aendern (vgl. test_ocr_consensus.py::
    test_negation_detected_regardless_of_engine_order)."""
    candidates = [
        _candidate("htr", htr_text),
        _candidate("tesseract", tesseract_text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )

    assert len(region.disagreements) == 1
    d = region.disagreements[0]
    assert d.critical is True
    assert d.reason == "critical_word:nicht"

    printed_bracket = "[ja|nein?]"
    printed_start = region.consensus_text.index(printed_bracket)
    printed_end = printed_start + len(printed_bracket)

    # Die echte Diskrepanz darf weder auf die gedruckte Klammer zeigen
    # noch sich mit ihr ueberlappen ...
    assert (d.char_start, d.char_end) != (printed_start, printed_end)
    assert not (d.char_start < printed_end and printed_start < d.char_end)

    # ... sondern auf die tatsaechlich gerenderte "nicht"-Klammer.
    real_bracket = region.consensus_text[d.char_start:d.char_end]
    assert "nicht" in real_bracket
    assert real_bracket != printed_bracket


GENERATED_CASES = [
    (
        ["a", "x", "b", "c", "y", "d"],
        [
            Disagreement(start=1, end=2, variants=(("x", ("htr",)), ("", ("tesseract",))), critical=True, reason="unclear"),
            Disagreement(start=4, end=5, variants=(("y", ("htr",)), ("", ("tesseract",))), critical=False, reason="unclear"),
        ],
    ),
    (
        ["p", "q"],
        [
            Disagreement(start=0, end=0, variants=(("", ("htr",)), ("pre", ("tesseract",))), critical=False, reason="unclear"),
            Disagreement(start=2, end=2, variants=(("", ("htr",)), ("post", ("tesseract",))), critical=False, reason="unclear"),
        ],
    ),
    (
        ["Start", "mitte", "ende"],
        [
            Disagreement(start=0, end=1, variants=(("Start", ("htr",)), ("", ("tesseract",))), critical=True, reason="unclear"),
            Disagreement(
                start=2, end=3,
                variants=(("ende", ("htr",)), ("Ende", ("tesseract",)), ("ENDE", ("paddleocr_vl",))),
                critical=True, reason="unclear",
            ),
        ],
    ),
    (
        ["a", "nicht", "wirklich", "b", "c"],
        [
            Disagreement(
                start=1, end=3,
                variants=(("nicht wirklich", ("htr",)), ("kaum", ("tesseract",))),
                critical=True, reason="critical_word:nicht",
            ),
            Disagreement(start=4, end=5, variants=(("c", ("htr",)), ("C", ("tesseract",))), critical=False, reason="unclear"),
        ],
    ),
]


@pytest.mark.parametrize("ref_tokens, disagreements", GENERATED_CASES)
def test_offsets_invariant_non_overlapping_ascending_in_bounds(ref_tokens, disagreements):
    """Ueber mehrere generierte Faelle mit je mehreren Disagreements
    (Loeschungen, Einfuegungen, Mehrwort-Spannen, Dreiweg-Varianten,
    Randpositionen): die zurueckgegebenen char_start/char_end muessen
    aufsteigend sortiert, ueberlappungsfrei und innerhalb der
    Textgrenzen liegen."""
    text, offsets = render_consensus_with_offsets(ref_tokens, disagreements)
    assert len(offsets) == len(disagreements)
    previous_end = 0
    for d in sorted(offsets, key=lambda item: item.char_start):
        assert 0 <= d.char_start < d.char_end <= len(text)
        assert d.char_start >= previous_end
        previous_end = d.char_end
