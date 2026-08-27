"""Testet die Mehr-Engine-OCR-Konsenspipeline.

Deckt teacherassist_core/ocr/consensus.py ab: pick_reference (Zeile 72),
align (Zeile 98, insbesondere die autojunk=False-Regression), collect_
disagreements (Zeile 162), render_consensus (Zeile 286), build_region
(Zeile 312) und decide_status (Zeile 356) -- sowie den Sicherheits-Vertrag
von DocumentResult.to_dict in teacherassist_core/ocr/types.py.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from teacherassist_core.ocr import types
from teacherassist_core.ocr.consensus import (
    build_region,
    decide_status,
    pick_reference,
    render_consensus,
)
from teacherassist_core.ocr.critical_tokens import CriticalTokenConfig
from teacherassist_core.ocr.markup import parse_markup
from teacherassist_core.ocr.types import (
    Disagreement,
    DocumentResult,
    ImageQuality,
    OCRCandidate,
    OCRStatus,
    PageResult,
    RegionType,
)


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


DEFAULT_CONFIG = CriticalTokenConfig()


def _build_page(
    region,
    *,
    classification: str,
    quality: ImageQuality | None = None,
    auto_approve: bool = False,
):
    quality = quality or ImageQuality.unknown(100, 100)
    status, auto_clean, reasons = decide_status(
        [region],
        quality=quality,
        engine_failures=(),
        require_engines=(),
        config=DEFAULT_CONFIG,
        classification=classification,
        auto_approve=auto_approve,
    )
    page = PageResult(
        index=0,
        width=100,
        height=100,
        quality=quality,
        regions=(region,),
        status=status,
        auto_clean=auto_clean,
        engine_failures=(),
        status_reasons=reasons,
    )
    return page, status, auto_clean, reasons


@pytest.mark.parametrize(
    "htr_text, tesseract_text",
    [
        ("Die Kraft ist nicht konstant.", "Die Kraft ist konstant."),
        ("Die Kraft ist konstant.", "Die Kraft ist nicht konstant."),
    ],
    ids=["htr_has_negation", "tesseract_has_negation"],
)
def test_negation_detected_regardless_of_engine_order(htr_text, tesseract_text):
    """Regression test for the critical false-negative bug: collect_disagreements
    (consensus.py:162) used to silently drop a negation whenever it came
    ONLY from the non-reference engine. Root cause: reconstructing a
    zero-width (insertion) reference span via two INDEPENDENT
    _map_position() boundary lookups always collapses both lookups to the
    SAME shared boundary value (op.other_end of the preceding op always
    equals op.other_start of the following op, by construction of
    SequenceMatcher.get_opcodes()) -- so the "other" text for an insertion
    was always reconstructed as empty, regardless of which engine actually
    inserted the word. See _engine_range_for_ref_span's docstring
    (consensus.py) for the full proof and the fix (look up the op that is
    ITSELF zero-width at that exact position, and use its full range,
    instead of two independent boundary lookups).

    Since ENGINE_PRIORITY (consensus.py:22) puts "htr" first, the bug fired
    precisely when the handwriting engine MISSED a negation another engine
    caught -- the single most likely real-world case, and the one this
    whole architecture exists to catch. Both engine orders (parametrized
    here) must now produce exactly one critical disagreement, an
    "[<...>nicht?]" bracket in consensus_text, agreement < 1.0, and a page
    status that withholds the text -- regardless of which engine happens to
    be picked as reference."""
    candidates = [
        _candidate("htr", htr_text),
        _candidate("tesseract", tesseract_text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )

    assert len(region.disagreements) == 1
    disagreement = region.disagreements[0]
    assert disagreement.critical is True
    assert disagreement.reason == "critical_word:nicht"
    assert re.search(r"\[\+?nicht\?\]", region.consensus_text)
    assert region.has_critical_uncertainty is True
    assert region.agreement < 1.0

    page, status, auto_clean, _reasons = _build_page(region, classification="student_submission")
    assert status is OCRStatus.NEEDS_REVIEW
    assert auto_clean is False
    assert page.has_critical_uncertainty is True

    doc = DocumentResult(
        job_id="job-1", source_name="probe.pdf", classification="student_submission",
        created_at=time.time(), pages=[page], status=status,
    )
    assert doc.to_dict()["pages"][0]["text"] is None


@pytest.mark.parametrize(
    "text_a, text_b",
    [
        ("Ergebnis: -3,5 m", "Ergebnis: 3,5 m"),
        ("Spannung: +5 V", "Spannung: -5 V"),
    ],
    ids=["sign_on_value", "sign_on_voltage"],
)
@pytest.mark.parametrize("swap_order", [False, True], ids=["htr_first", "tesseract_first"])
def test_sign_disagreement_is_critical_regardless_of_engine_order(text_a, text_b, swap_order):
    """Vorzeichen- und Wertfehler ("-3,5" vs. "3,5", "+5" vs. "-5") sind
    immer kritisch (Grund "number", classify_span-Prioritaet Schritt 1 vor
    Symbolen/Woertern) -- und zwar unabhaengig davon, welche Engine welchen
    Text liefert (siehe test_negation_detected_regardless_of_engine_order
    fuer die allgemeine Lehre aus dem Falsch-Negativ-Bug: jede Eigenschaft,
    die gelten soll, muss in beiden Reihenfolgen gelten)."""
    htr_text, tesseract_text = (text_b, text_a) if swap_order else (text_a, text_b)
    candidates = [_candidate("htr", htr_text), _candidate("tesseract", tesseract_text, confidence=0.9)]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert region.has_critical_uncertainty is True
    assert any(d.reason == "number" for d in region.disagreements)


def test_identical_text_yields_no_disagreements():
    """Drei Engines mit identischem Text: keine Disagreements, agreement ==
    1.0, auto_clean True, kein "[" im Konsenstext -- aber der Seitenstatus
    bleibt NEEDS_REVIEW, weil Schuelerarbeiten IMMER eine Lehrkraft brauchen
    (decide_status, consensus.py:356, classification == "student_submission"
    darf NIE automatisch freigeben, egal wie sauber der Konsens ist)."""
    text = "Die Kraft ist konstant."
    candidates = [
        _candidate("htr", text),
        _candidate("paddleocr_vl", text, confidence=0.93),
        _candidate("tesseract", text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )

    assert region.disagreements == ()
    assert region.agreement == 1.0
    assert "[" not in region.consensus_text

    page, status, auto_clean, _reasons = _build_page(region, classification="student_submission")
    assert auto_clean is True
    assert status is OCRStatus.NEEDS_REVIEW


@pytest.mark.parametrize(
    "swap_order",
    [False, True],
    ids=["htr_has_full_text", "tesseract_has_full_text"],
)
def test_autojunk_disabled_on_long_pages(swap_order):
    """Regressionswaechter fuer consensus.py:98 align(): SequenceMatchers
    Standard-autojunk=True markiert jedes Token, das in >1% einer laengeren
    als 200 Elemente umfassenden Sequenz vorkommt, als "populaer" und
    verwendet es nicht mehr als Ankerpunkt fuers Alignment. Auf einer
    langen, repetitiven Seite verschluckt das genau die Woerter, deretwegen
    dieses Modul existiert.

    Manuell verifiziert (siehe Kommentar in align()): mit autojunk=True
    zerfaellt das Alignment nach der geloeschten Stelle in einen einzigen
    riesigen replace-Block ueber hunderte Tokens; mit autojunk=False (der
    tatsaechliche Code) bleibt es ein praeziser 1-Token-delete an genau der
    richtigen Stelle. Dieser Test baut absichtlich eine ~600-Token-Seite mit
    120 Wiederholungen von "nicht" (>>1% Haeufigkeit), damit er bei einer
    versehentlich entfernten autojunk=False-Angabe tatsaechlich fehlschlaegt.

    Parametrisiert ueber beide Engine-Reihenfolgen: wenn tesseract (nicht
    htr) die vollstaendige Fassung liefert, ist die Referenz (htr, hoechste
    ENGINE_PRIORITY) die KUERZERE Fassung -- das ist eine Insertion aus
    Referenzsicht, also genau der nullbreite Fall aus dem
    Falsch-Negativ-Bug, hier aber bei realistischer Groesse."""
    words: list[str] = []
    for _ in range(120):
        words += ["die", "kraft", "ist", "nicht", "konstant"]
    full_text = " ".join(words)

    short_words = list(words)
    deleted_index = 60 * 5 + 3
    assert short_words[deleted_index] == "nicht"
    del short_words[deleted_index]
    short_text = " ".join(short_words)

    htr_text, tesseract_text = (short_text, full_text) if swap_order else (full_text, short_text)
    candidates = [_candidate("htr", htr_text), _candidate("tesseract", tesseract_text, confidence=0.9)]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 10, 10), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )

    assert region.has_critical_uncertainty is True
    assert len(region.disagreements) == 1
    disagreement = region.disagreements[0]
    # Ein praeziser, kleiner Bereich beweist, dass autojunk=False das
    # Alignment verankert hielt -- mit autojunk=True waere dies stattdessen
    # ein Bereich ueber hunderte Tokens (siehe Docstring oben).
    assert disagreement.end - disagreement.start <= 3
    assert disagreement.critical is True
    assert disagreement.reason == "critical_word:nicht"


def test_render_consensus_bracket_formats():
    """Table-driven ueber die vier Klammer-Faelle aus der Spezifikation
    (render_consensus, consensus.py:286), plus die Invariante, dass die
    Anzahl der "[...?]"-Treffer immer len(disagreements) entspricht."""
    cases = [
        # (ref_tokens, disagreement, erwarteter_ausschnitt)
        (
            ["a", "nicht", "b"],
            Disagreement(start=1, end=2, variants=(("nicht", ("htr",)), ("", ("tesseract",))), critical=True, reason="critical_word:nicht"),
            "a [nicht?] b",
        ),
        (
            ["a", "b"],
            Disagreement(start=1, end=1, variants=(("", ("htr",)), ("nicht", ("tesseract",))), critical=True, reason="critical_word:nicht"),
            "a [+nicht?] b",
        ),
        (
            ["Ergebnis:", "3,5", "m"],
            Disagreement(start=1, end=2, variants=(("3,5", ("htr",)), ("8,5", ("tesseract",))), critical=True, reason="number"),
            "Ergebnis: [3,5|8,5?] m",
        ),
        (
            ["Formel:", "Co"],
            Disagreement(
                start=1, end=2,
                variants=(("Co", ("htr",)), ("CO", ("tesseract",)), ("C0", ("paddleocr_vl",))),
                critical=True, reason="chemical_case",
            ),
            "Formel: [Co|CO|C0?]",
        ),
    ]
    for ref_tokens, disagreement, expected in cases:
        rendered = render_consensus(ref_tokens, [disagreement])
        assert rendered == expected
        assert len(re.findall(r"\[[^\]]*\?\]", rendered)) == 1


def test_reference_selection_prefers_htr():
    """pick_reference (consensus.py:72) waehlt den ENGINE_PRIORITY-Rang vor
    Konfidenz und Tokenanzahl -- htr gewinnt hier trotz niedrigerer
    Konfidenz und weniger Tokens gegen tesseract."""
    weak_htr = _candidate("htr", "a", confidence=0.5, tokens=("a",))
    strong_tesseract = _candidate("tesseract", "a b c d", confidence=0.99, tokens=("a", "b", "c", "d"))
    chosen = pick_reference([strong_tesseract, weak_htr])
    assert chosen.engine == "htr"


@pytest.mark.parametrize("swap_order", [False, True], ids=["htr_first", "tesseract_first"])
def test_merge_gap_joins_adjacent_spans(swap_order):
    """Zwei Abweichungsstellen, die nur durch ein einziges (<=MERGE_GAP)
    uebereinstimmendes Referenz-Token getrennt sind, muessen zu EINER
    Disagreement verschmolzen werden (_merge_ranges, consensus.py:138) --
    unabhaengig davon, welche Engine Referenz ist."""
    text_a, text_b = "eins zwei drei", "einsX zwei dreiY"
    htr_text, tesseract_text = (text_b, text_a) if swap_order else (text_a, text_b)
    candidates = [
        _candidate("htr", htr_text),
        _candidate("tesseract", tesseract_text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 10, 10), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert len(region.disagreements) == 1
    disagreement = region.disagreements[0]
    assert (disagreement.start, disagreement.end) == (0, 3)


def test_insertion_produces_disagreement_end_to_end():
    """End-to-end coverage for the insertion path: two real candidate texts
    (not a hand-built Disagreement, unlike test_render_consensus_bracket_
    formats) go through build_region -> collect_disagreements, asserting
    the resulting consensus_text actually contains a "[+...?]" bracket.
    This is exactly the gap the false-negative bug hid in: the RENDERER
    (render_consensus) had end-to-end coverage via hand-constructed
    Disagreement objects, but the DETECTOR (collect_disagreements)
    producing that same shape from real OCR candidates never did."""
    candidates = [
        _candidate("htr", "Die Kraft ist konstant."),
        _candidate("tesseract", "Die Kraft ist nicht konstant.", confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert re.search(r"\[\+nicht\?\]", region.consensus_text)
    assert len(region.disagreements) == 1
    disagreement = region.disagreements[0]
    assert disagreement.start == disagreement.end  # nullbreite Insertion


@pytest.mark.parametrize(
    "htr_text, tesseract_text",
    [
        ("Kraft ist konstant.", "Die Kraft ist konstant."),
        ("Die Kraft ist", "Die Kraft ist konstant"),
    ],
    ids=["insertion_at_start", "insertion_at_end"],
)
def test_insertion_at_start_and_end_of_line(htr_text, tesseract_text):
    """Insertionen ganz am Anfang oder ganz am Ende der Referenz sind genau
    dort, wo ein Off-by-one an einer Randbedingung sich am ehesten
    versteckt (siehe Bug-Report des Koordinators). _engine_range_for_ref_span
    (consensus.py) sucht direkt nach einem an genau dieser Position
    nullbreiten Op, statt sich auf eine Randabbildung zwischen benachbarten
    Ops zu verlassen -- die Position innerhalb der Sequenz (Anfang, Mitte,
    Ende) darf also keine Rolle spielen."""
    candidates = [
        _candidate("htr", htr_text),
        _candidate("tesseract", tesseract_text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert len(region.disagreements) == 1
    disagreement = region.disagreements[0]
    assert disagreement.start == disagreement.end
    assert "[+" in region.consensus_text


def test_zero_width_span_lowers_agreement():
    """Eine nullbreite (reine Insertions-)Disagreement darf fuer `agreement`
    nicht unsichtbar sein: build_region (consensus.py) zaehlt eine
    nullbreite Spanne jetzt als mindestens 1 abweichendes Token, sonst
    wuerde die min_agreement-Schranke in decide_status() eine kritische
    Diskrepanz durchwinken, weil sie faelschlich mit einem perfekten 1.0
    bewertet wuerde."""
    candidates = [
        _candidate("htr", "Die Kraft ist konstant."),
        _candidate("tesseract", "Die Kraft ist nicht konstant.", confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert len(region.disagreements) == 1
    assert region.disagreements[0].start == region.disagreements[0].end
    assert region.agreement < 1.0


def test_uncertain_marker_self_escalates():
    """Eine EINZELNE Engine, die <uncertain>ist|ist nicht</uncertain>
    liefert, muss aus sich selbst heraus eine kritische Disagreement
    erzeugen (collect_disagreements' synthetische Markup-Varianten,
    consensus.py:162) -- ganz ohne eine zweite Engine zum Vergleich."""
    raw = "Die Kraft <uncertain>ist|ist nicht</uncertain> konstant."
    parsed = parse_markup(raw)
    candidate = _candidate("htr", parsed.text, raw_text=raw)

    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), [candidate],
        config=DEFAULT_CONFIG, classification="student_submission",
    )

    assert region.has_critical_uncertainty is True
    assert any(d.critical and d.reason == "critical_word:nicht" for d in region.disagreements)


def test_deleted_text_excluded_from_text():
    """Durchgestrichener Schuelertext (<deleted>...</deleted>, markup.py)
    darf niemals in ParsedMarkup.text landen -- er wuerde sonst versehentlich
    zur Bewertung herangezogen."""
    parsed = parse_markup("Die Aussage ist <deleted>falsch</deleted> richtig.")
    assert "falsch" not in parsed.text
    assert parsed.deleted == ("falsch",)
    # Restlicher sichtbarer Text bleibt erhalten (Whitespace-Details rund um
    # die entfernte Stelle sind hier nicht Testgegenstand).
    assert " ".join(parsed.text.split()) == "Die Aussage ist richtig."


def test_document_result_withholds_text_until_approved():
    """types.DocumentResult.to_dict() darf vollen Text erst nach
    mark_approved() herausgeben -- vorher muessen "text"/"selectedText"
    None sein, waehrend "consensusText" (mit [...]-Markierungen) immer
    sichtbar bleibt, da die Review-UI sie braucht."""
    candidates = [_candidate("htr", "konstant"), _candidate("tesseract", "konstant", confidence=0.9)]
    region = build_region(
        "p1-r1", RegionType.TEXT_LINE, (0, 0, 10, 10), candidates,
        config=DEFAULT_CONFIG, classification="reference_material",
    )
    page, status, _auto_clean, _reasons = _build_page(region, classification="reference_material")
    doc = DocumentResult(
        job_id="job-2", source_name="probe.pdf", classification="reference_material",
        created_at=time.time(), pages=[page], status=status,
    )

    before = doc.to_dict()
    assert before["pages"][0]["text"] is None
    assert before["pages"][0]["regions"][0]["selectedText"] is None
    assert before["pages"][0]["regions"][0]["consensusText"] is not None

    doc.mark_approved()
    after = doc.to_dict()
    assert after["status"] == "approved"
    assert isinstance(after["pages"][0]["text"], str)
    assert isinstance(after["pages"][0]["regions"][0]["selectedText"], str)


def test_student_submission_never_auto_approves_even_with_auto_approve_flag():
    """The most important guard from the auto_approve fix (consensus.py:367
    decide_status): classification == "student_submission" must stay
    NEEDS_REVIEW even when the caller passes auto_approve=True on a fully
    clean page -- the belt-and-braces check at consensus.py:418 exists
    precisely so a caller mistake here can never leak a student's OCR text
    without a teacher's eyes on it. PROCESSING must never come back either
    (it would mean "still running" for a page that is actually finished)."""
    text = "Die Kraft ist konstant."
    candidates = [
        _candidate("htr", text),
        _candidate("tesseract", text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="student_submission",
    )
    assert region.disagreements == ()  # fully clean input

    page, status, auto_clean, _reasons = _build_page(
        region, classification="student_submission", auto_approve=True,
    )
    assert auto_clean is True  # the consensus itself really was clean...
    assert status is OCRStatus.NEEDS_REVIEW  # ...but that must not matter here
    assert status is not OCRStatus.APPROVED
    assert status is not OCRStatus.PROCESSING

    doc = DocumentResult(
        job_id="job-3", source_name="klausur.pdf", classification="student_submission",
        created_at=time.time(), pages=[page], status=status,
    )
    # And because status stayed NEEDS_REVIEW, the text must still be withheld.
    assert doc.to_dict()["pages"][0]["text"] is None


def test_non_student_material_auto_approves_when_flag_set_and_clean():
    """Non-student material (e.g. classification="public_curriculum") with
    an explicitly set auto_approve=True and a fully clean consensus reaches
    APPROVED directly from decide_status (consensus.py:430) -- the one place
    outside DocumentResult.mark_approved that this module may set APPROVED,
    and only under this exact, caller-opted-in policy. Once APPROVED,
    DocumentResult.to_dict() must carry the text (types.py include_text)."""
    text = "Photosynthese wandelt Lichtenergie in chemische Energie um."
    candidates = [
        _candidate("htr", text),
        _candidate("tesseract", text, confidence=0.9),
    ]
    region = build_region(
        "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
        config=DEFAULT_CONFIG, classification="public_curriculum",
    )
    assert region.disagreements == ()

    page, status, auto_clean, _reasons = _build_page(
        region, classification="public_curriculum", auto_approve=True,
    )
    assert auto_clean is True
    assert status is OCRStatus.APPROVED

    doc = DocumentResult(
        job_id="job-4", source_name="arbeitsblatt.pdf", classification="public_curriculum",
        created_at=time.time(), pages=[page], status=status,
    )
    result = doc.to_dict()
    assert result["status"] == "approved"
    assert isinstance(result["pages"][0]["text"], str)
    assert isinstance(result["pages"][0]["regions"][0]["selectedText"], str)


def test_auto_approve_default_false_stays_needs_review_regardless_of_classification():
    """With auto_approve left at its default (False, matching the settings
    key ocrAutoApproveNonStudent's default), a clean page must stay
    NEEDS_REVIEW no matter the classification -- auto-approval is strictly
    opt-in, never the default behaviour."""
    text = "Die Kraft ist konstant."
    for classification in ("student_submission", "public_curriculum", "reference_material"):
        candidates = [
            _candidate("htr", text),
            _candidate("tesseract", text, confidence=0.9),
        ]
        region = build_region(
            "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
            config=DEFAULT_CONFIG, classification=classification,
        )
        _page, status, auto_clean, _reasons = _build_page(region, classification=classification)
        assert auto_clean is True
        assert status is OCRStatus.NEEDS_REVIEW


def test_decide_status_never_returns_processing():
    """Invariant: decide_status is only ever called once a page's OCR run
    has actually finished, so PROCESSING (a job "still running") must never
    be among its possible return values -- for any combination of clean/
    dirty input, classification, and auto_approve (consensus.py:367)."""
    clean_text = "Die Kraft ist konstant."
    dirty_candidates = [
        _candidate("htr", "Die Kraft ist nicht konstant."),
        _candidate("tesseract", "Die Kraft ist konstant.", confidence=0.9),
    ]
    clean_candidates = [
        _candidate("htr", clean_text),
        _candidate("tesseract", clean_text, confidence=0.9),
    ]

    for candidates in (clean_candidates, dirty_candidates):
        for classification in ("student_submission", "public_curriculum", "reference_material"):
            region = build_region(
                "p1-r1", RegionType.PARAGRAPH, (0, 0, 100, 20), candidates,
                config=DEFAULT_CONFIG, classification=classification,
            )
            for auto_approve in (True, False):
                status, _auto_clean, _reasons = decide_status(
                    [region],
                    quality=ImageQuality.unknown(100, 100),
                    engine_failures=(),
                    require_engines=(),
                    config=DEFAULT_CONFIG,
                    classification=classification,
                    auto_approve=auto_approve,
                )
                assert status is not OCRStatus.PROCESSING

    # The no-candidates / FAILED path (no regions at all) must not return
    # PROCESSING either.
    status, _auto_clean, _reasons = decide_status(
        [],
        quality=ImageQuality.unknown(100, 100),
        engine_failures=(("htr", "timeout"),),
        require_engines=("htr",),
        config=DEFAULT_CONFIG,
        classification="reference_material",
    )
    assert status is OCRStatus.FAILED
    assert status is not OCRStatus.PROCESSING


def test_document_result_to_dict_source_contract_derives_include_text_from_status():
    """Quelltext-Vertragstest (Idiom siehe tests/test_http_api.py:155):
    DocumentResult.to_dict() darf `include_text` NIEMALS als Parameter
    entgegennehmen, sondern MUSS es intern aus self.status ableiten -- das
    ist der Sicherheits-Dreh-und-Angelpunkt aus types.py's Modul-Docstring.
    Ein Regression hier waere ein unautorisierter Volltext-Leak vor
    Lehrkraft-Freigabe."""
    source = Path(types.__file__).read_text(encoding="utf-8")
    class_start = source.index("class DocumentResult:")
    class_source = source[class_start:]
    method_start = class_source.index("def to_dict(self)")
    signature_line = class_source[method_start : class_source.index("\n", method_start)]
    assert "include_text" not in signature_line
    method_body = class_source[method_start:]
    assert "include_text = self.status is OCRStatus.APPROVED" in method_body
