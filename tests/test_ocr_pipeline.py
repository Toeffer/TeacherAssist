"""Testet die OCR-Pipeline (Stufe 4b des OCR-Refactors).

Deckt teacherassist_core/ocr/pipeline.py ab: process_page (Zeile ~118,
insbesondere die "blocking quality -> keine Engine wird aufgerufen"-Regel
und den "CloudBlocked wird niemals abgefangen"-Vertrag), process_document
(Zeile ~316, insbesondere den Lazy-Konsum-Vertrag) und _document_status
(Zeile ~296).

Alle Tests laufen ausschliesslich gegen FakeEngine (engines/fake.py) --
keine Modelle, keine GPU, kein Netzwerk, kein Tesseract-Binary. Um die
Tests unabhaengig von den (bereits andernorts getesteten) Heuristiken in
image_quality.assess()/segmentation.segment_page() zu machen, werden diese
beiden Funktionen ueber das pipeline-Modul selbst (``pipeline.image_quality``/
``pipeline.segmentation``, dieselben Modulobjekte wie ueberall sonst)
gezielt monkeygepatcht -- jeder Test bekommt so eine deterministische,
nicht-blockierende Bildqualitaet und eine feste Regionsliste, ohne echte
Bildheuristiken nachbilden zu muessen. preprocess.prepare() wird ebenfalls
durch die Identitaetsfunktion ersetzt, da dessen eigenes Verhalten in
tests/test_ocr_preprocess.py abgedeckt ist (falls vorhanden) bzw. nicht
Gegenstand dieser Stufe ist.
"""

from __future__ import annotations

import importlib
import sys

import pytest

from teacherassist_core.ocr import pipeline
from teacherassist_core.ocr.engines import FakeEngine
from teacherassist_core.ocr.engines.base import EngineError, EngineStatus
from teacherassist_core.ocr.page_render import PageImage
from teacherassist_core.ocr.pipeline import PipelineConfig, process_document, process_page
from teacherassist_core.ocr.privacy_guard import CloudBlocked
from teacherassist_core.ocr.types import ImageQuality, OCRStatus, RegionType

from _ocr_module_reload_helpers import restore_purged_modules

BLOCKED_ROOTS = frozenset({"torch", "transformers", "pytesseract", "PIL", "numpy", "paddle"})


def _blank_image():
    from PIL import Image

    return Image.new("RGB", (400, 300), color="white")


def _page(index: int = 0) -> PageImage:
    return PageImage(index=index, image=_blank_image(), dpi=350, width=400, height=300)


def _benign_quality(**overrides) -> ImageQuality:
    """Eine nicht-blockierende ImageQuality mit unauffaelligen Werten --
    steht stellvertretend fuer "eine gute Aufnahme", ohne echte
    Bildheuristiken (image_quality.assess()) nachbilden zu muessen."""
    base = dict(
        width=400,
        height=300,
        estimated_dpi=350.0,
        blur_score=500.0,
        contrast=0.5,
        brightness=0.5,
        skew_degrees=0.0,
        glare_ratio=0.0,
        issues=(),
        blocking=False,
        score=0.95,
    )
    base.update(overrides)
    return ImageQuality(**base)


def _patch_page_flow(monkeypatch, *, quality: ImageQuality, regions: list) -> None:
    """Monkeypatcht image_quality.assess/segmentation.segment_page/
    preprocess.prepare ueber die vom pipeline-Modul selbst gehaltenen
    Modulreferenzen (``from . import image_quality, preprocess,
    segmentation`` in pipeline.py) -- patcht also dieselben Modulobjekte,
    die pipeline.py tatsaechlich zur Laufzeit aufruft."""
    monkeypatch.setattr(pipeline.image_quality, "assess", lambda image, **kwargs: quality)
    monkeypatch.setattr(
        pipeline.segmentation, "segment_page", lambda image, *, page_index=0: regions
    )
    monkeypatch.setattr(
        pipeline.preprocess, "prepare", lambda image, *, region_type, target_dpi: image
    )


class _CloudBlockedEngine:
    """Minimale, handgeschriebene OCREngine-Attrappe, die IMMER CloudBlocked
    wirft -- FakeEngine.fail_with kann nur EngineError werfen (siehe
    engines/fake.py:88), daher die eigene Klasse hier."""

    name = "cloud-vlm"
    kind = "vlm"
    capabilities: dict = {}

    def is_available(self) -> bool:
        return True

    def status(self) -> EngineStatus:
        return EngineStatus(name=self.name, kind="vlm", available=True, reason="", model_id=self.name)

    def supports(self, region_type: RegionType) -> bool:
        return True

    def recognize(self, image, *, region_type, language="deu", region_id=None):
        raise CloudBlocked("student_submission", "https://example.invalid/ocr")

    def warmup(self) -> None:
        return None


class _ExplodingEngine:
    """Wirft eine ValueError statt einer EngineError -- steht fuer eine
    Engine mit einem echten, unerwarteten Bug (nicht "Modell fehlt"), gegen
    die process_page() sich trotzdem absichern muss (siehe Auftrag: "Catch
    Exception too, so one broken engine cannot kill a whole batch")."""

    name = "exploding"
    kind = "fake"
    capabilities: dict = {}

    def is_available(self) -> bool:
        return True

    def status(self) -> EngineStatus:
        return EngineStatus(name=self.name, kind="fake", available=True, reason="", model_id=self.name)

    def supports(self, region_type: RegionType) -> bool:
        return True

    def recognize(self, image, *, region_type, language="deu", region_id=None):
        raise ValueError("boom")

    def warmup(self) -> None:
        return None


def test_htr_engine_failure_does_not_silently_fall_back_to_tesseract(monkeypatch):
    """process_page() (pipeline.py) darf einen HTR-Fehlschlag NIE dadurch
    verstecken, dass Tesseract stillschweigend zum vollwertigen Ersatz
    wird: der Fehlschlag muss sichtbar in engine_failures UND in
    status_reasons ("engine_unavailable:htr") auftauchen, der Status muss
    NEEDS_REVIEW bleiben (auto_clean=False) -- auch wenn Tesseract selbst
    anstandslos einen Kandidaten liefert. DocumentResult.to_dict()'s
    Sicherheits-Choke-Point (types.py:247) muss den Volltext trotzdem
    weiterhin sperren (status ist nicht APPROVED), waehrend
    engineFailures fuer die Review-UI sichtbar bleibt (siehe
    PageResult.to_dict, types.py:202)."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    htr = FakeEngine("htr", "wird nie verwendet", fail_with="model_not_downloaded")
    tesseract = FakeEngine("tesseract", "Tesseract-Text")
    config = PipelineConfig(require_engines=("htr",))

    doc = process_document(
        [_page()], job_id="job-htr-fail", source_name="scan.png", config=config,
        engines=[htr, tesseract],
    )
    page_result = doc.pages[0]

    assert ("htr", "model_not_downloaded") in page_result.engine_failures
    assert page_result.auto_clean is False
    assert page_result.status is OCRStatus.NEEDS_REVIEW
    assert "engine_unavailable:htr" in page_result.status_reasons

    region = page_result.regions[0]
    assert any(c.engine == "tesseract" and c.text == "Tesseract-Text" for c in region.candidates)

    data = doc.to_dict()
    assert data["pages"][0]["text"] is None
    assert data["pages"][0]["engineFailures"]


def test_blocking_quality_short_circuits(monkeypatch):
    """process_page() (pipeline.py) darf bei quality.blocking=True KEINE
    Engine aufrufen -- ein grosses Modell, das ein unbrauchbares Foto
    "rettet", ist genau der Fehlerfall, den dieser gesamte Refactor
    verhindern soll (siehe Modul-Docstring)."""
    blocking_quality = _benign_quality(blocking=True, issues=("too_blurry",), blur_score=1.0)
    monkeypatch.setattr(pipeline.image_quality, "assess", lambda image, **kwargs: blocking_quality)

    htr = FakeEngine("htr", "text")
    tesseract = FakeEngine("tesseract", "text")

    result = process_page(_page(), config=PipelineConfig(), engines=[htr, tesseract])

    assert result.status is OCRStatus.NEEDS_REVIEW
    assert result.regions == ()
    assert htr.call_count == 0
    assert tesseract.call_count == 0


def test_single_engine_never_auto_clean(monkeypatch):
    """Mit nur einer erfolgreichen Engine kann build_region() nie eine
    Uebereinstimmung von 1.0 erreichen (consensus.py: "eine einzelne Engine
    ... kann nie eine Uebereinstimmung von 1.0 erreichen") -- decide_status()
    muss das ueber den "single_engine"-Grund sichtbar machen und darf nie
    auto_clean=True liefern."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    engine = FakeEngine("tesseract", "Alleiniger Text")
    config = PipelineConfig(require_engines=())

    result = process_page(_page(), config=config, engines=[engine])

    assert result.auto_clean is False
    assert "single_engine" in result.status_reasons


def test_cloud_blocked_propagates_out_of_pipeline(monkeypatch):
    """CloudBlocked (privacy_guard.py) darf innerhalb der Pipeline NIEMALS
    abgefangen werden -- weder von process_page() noch von
    process_document(). Ein stiller Fallback wuerde genau die Klasse Bug
    reproduzieren, derentwegen privacy_guard.py existiert (siehe dessen
    Modul-Docstring)."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    with pytest.raises(CloudBlocked):
        process_page(
            _page(),
            config=PipelineConfig(require_engines=()),
            engines=[_CloudBlockedEngine()],
        )


def test_unexpected_engine_exception_becomes_engine_failure(monkeypatch):
    """Eine ValueError (oder jede andere nicht-EngineError-Exception) aus
    einer Engine darf process_page() nicht abstuerzen lassen -- sie wird
    als ("<engine>", "unexpected:ValueError") in engine_failures
    aufgenommen, waehrend die uebrigen Engines normal weiterlaufen (siehe
    Auftrag: "one broken engine cannot kill a whole batch")."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Text")
    result = process_page(
        _page(),
        config=PipelineConfig(require_engines=()),
        engines=[_ExplodingEngine(), tesseract],
    )

    assert ("exploding", "unexpected:ValueError") in result.engine_failures
    assert result.regions[0].candidates  # tesseract lieferte trotzdem einen Kandidaten
    assert result.status is not OCRStatus.FAILED


def test_process_document_consumes_pages_lazily(monkeypatch):
    """process_document() (pipeline.py) muss Seiten lazy konsumieren: die
    Quellen-Iterable wird instrumentiert (jede Seite traegt sich beim
    Rendern in `rendered` ein), und on_page() erfasst jeweils, wie viele
    Seiten zu diesem Zeitpunkt bereits gerendert wurden. Waere die Quelle
    vorab vollstaendig durchlaufen (`list(...)`), stuende beim ersten
    on_page()-Aufruf bereits `len(rendered) == 3`, nicht 1 -- das genau
    unterscheidet dieser Test."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    rendered: list[int] = []

    def _instrumented_pages():
        for i in range(3):
            rendered.append(i)
            yield _page(i)

    seen_at_callback: list[int] = []

    def _on_page(index, page_result):
        seen_at_callback.append(len(rendered))

    engine = FakeEngine("tesseract", "Text")
    process_document(
        _instrumented_pages(),
        job_id="job-lazy",
        source_name="doc.pdf",
        config=PipelineConfig(require_engines=()),
        engines=[engine],
        on_page=_on_page,
    )

    assert seen_at_callback == [1, 2, 3]


def test_region_with_no_candidates_is_kept(monkeypatch):
    """Liefert JEDE Engine fuer eine Region keinen Kandidaten (hier: die
    FakeEngine-Mapping-Form kennt nur "p0-r0", nicht "p0-r1" -- siehe
    engines/fake.py:_resolve_text, "no_text_for_region"), darf diese Region
    nicht aus dem Ergebnis verschwinden. Sie muss als Region MIT LEEREN
    Kandidaten erhalten bleiben (siehe Auftrag: "do not silently drop
    it")."""
    regions = [
        ("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20)),
        ("p0-r1", RegionType.TEXT_LINE, (0, 30, 50, 50)),
    ]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    engine = FakeEngine("tesseract", {"p0-r0": "Erste Zeile"})
    result = process_page(_page(), config=PipelineConfig(require_engines=()), engines=[engine])

    assert len(result.regions) == 2
    empty_region = result.regions[1]
    assert empty_region.id == "p0-r1"
    assert empty_region.candidates == ()
    assert any(name == "tesseract" for name, _reason in result.engine_failures)


def test_verify_engine_not_called_when_bulk_engines_agree(monkeypatch):
    """Zwei Bulk-Engines, die wortgleich uebereinstimmen, sind kein Fall
    fuer einen zweiten (teuren) Blick -- die Verifikations-Engine
    (config.verify_engines) darf gar nicht erst aufgerufen werden (siehe
    Auftrag "selective second reading": "a region where two independent
    bulk engines agree character-for-character does not need a third
    opinion")."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Der Hund läuft schnell.")
    htr = FakeEngine("htr", "Der Hund läuft schnell.")
    verify = FakeEngine("verify_vlm", "Der Hund läuft schnell.", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",))

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert verify.call_count == 0
    assert result.regions[0].disagreements == ()


def test_verify_engine_called_on_disagreement(monkeypatch):
    """Widersprechen sich zwei Bulk-Engines, muss die konfigurierte
    Verifikations-Engine aufgerufen werden UND ihr Kandidat muss in der
    final aufgebauten Region auftauchen (siehe Auftrag Schritt 4: "Re-run
    consensus for those regions with the extra candidate included")."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Die Kraft ist konstant.")
    htr = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    verify = FakeEngine("verify_vlm", "Die Kraft ist nicht konstant.", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",))

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert verify.call_count == 1
    region = result.regions[0]
    assert any(c.engine == "verify_vlm" for c in region.candidates)


def test_verify_engine_called_on_low_confidence(monkeypatch):
    """Stimmen zwei Bulk-Engines wortgleich ueberein, aber ihre mittlere
    Konfidenz liegt unter config.min_confidence, ist das trotzdem ein Fall
    fuer den zweiten Blick -- Uebereinstimmung allein sagt nichts darueber,
    wie sicher sich beide Engines waren."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Text unsicher.", confidence=0.4)
    htr = FakeEngine("htr", "Text unsicher.", confidence=0.4)
    verify = FakeEngine("verify_vlm", "Text unsicher.", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",), min_confidence=0.75)

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert verify.call_count == 1


def test_verify_engine_called_on_single_bulk_engine(monkeypatch):
    """Liefert nur eine Bulk-Engine ueberhaupt einen Kandidaten fuer eine
    Region (nichts, womit man vergleichen koennte), ist das ebenfalls ein
    Fall fuer den zweiten Blick (siehe Auftrag: "only one bulk engine
    produced a candidate")."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Alleiniger Text.")
    verify = FakeEngine("verify_vlm", "Alleiniger Text.", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",))

    result = process_page(_page(), config=config, engines=[tesseract, verify])

    assert verify.call_count == 1
    region = result.regions[0]
    assert region.agreement == 1.0


def test_verify_budget_prioritises_critical_regions(monkeypatch):
    """Mehr verdaechtige Regionen als das Budget erlaubt: eine kritische
    Region (Negation "nicht") wird bedient, eine nur "leise" verdaechtige
    (nicht-kritische Wortabweichung "läuft"/"rennt") muss dagegen leer
    ausgehen (siehe PipelineConfig.max_verify_regions_per_page /
    _verify_priority_key: "prioritise regions with critical
    disagreements first")."""
    regions = [
        ("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20)),
        ("p0-r1", RegionType.TEXT_LINE, (0, 30, 50, 50)),
    ]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    # p0-r0: kritische Diskrepanz (Negation "nicht").
    # p0-r1: nicht-kritische Wortabweichung ("läuft" vs. "rennt").
    tesseract = FakeEngine(
        "tesseract",
        {"p0-r0": "Die Kraft ist konstant.", "p0-r1": "Der Hund läuft schnell."},
    )
    htr = FakeEngine(
        "htr",
        {"p0-r0": "Die Kraft ist nicht konstant.", "p0-r1": "Der Hund rennt schnell."},
    )
    verify = FakeEngine("verify_vlm", "GEPRUEFT", kind="vlm")
    config = PipelineConfig(
        require_engines=(), verify_engines=("verify_vlm",), max_verify_regions_per_page=1,
    )

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert verify.call_count == 1
    critical_region = next(r for r in result.regions if r.id == "p0-r0")
    quiet_region = next(r for r in result.regions if r.id == "p0-r1")
    assert any(c.engine == "verify_vlm" for c in critical_region.candidates)
    assert not any(c.engine == "verify_vlm" for c in quiet_region.candidates)


def test_verify_budget_exhausted_is_recorded(monkeypatch):
    """Reicht das Verifikationsbudget nicht fuer alle verdaechtigen
    Regionen, muss die Seite das explizit vermerken (status_reasons
    "verify_budget_exhausted") -- eine Lehrkraft darf nie stillschweigend
    annehmen, dass ohnehin jede schwache Region gegengeprueft wurde (siehe
    Auftrag: "record status_reasons += (\"verify_budget_exhausted\",)")."""
    regions = [
        ("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20)),
        ("p0-r1", RegionType.TEXT_LINE, (0, 30, 50, 50)),
    ]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine(
        "tesseract",
        {"p0-r0": "Die Kraft ist konstant.", "p0-r1": "Der Hund läuft schnell."},
    )
    htr = FakeEngine(
        "htr",
        {"p0-r0": "Die Kraft ist nicht konstant.", "p0-r1": "Der Hund rennt schnell."},
    )
    verify = FakeEngine("verify_vlm", "GEPRUEFT", kind="vlm")
    config = PipelineConfig(
        require_engines=(), verify_engines=("verify_vlm",), max_verify_regions_per_page=1,
    )

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert "verify_budget_exhausted" in result.status_reasons


def test_consensus_recomputed_after_verification(monkeypatch):
    """Der Verifikations-Kandidat wird nicht nur angehaengt, sondern der
    Konsens der Region wird komplett neu aufgebaut (consensus.build_region).
    Vergleicht denselben Bulk-Zustand mit (verified) und ohne (baseline)
    Verifikation:
    (a) p0-r0 hat nur eine Bulk-Engine (nichts zum Vergleichen, agreement
        0.0); bestaetigt die Verifikations-Engine deren Lesart woertlich,
        steigt agreement auf 1.0.
    (b) p0-r1 hat zwei (niedrig-konfidente, aber wortgleiche) Bulk-Engines
        ohne jede Diskrepanz; widerspricht die Verifikations-Engine kritisch
        (fuegt die Negation "nicht" ein), muss die Region danach eine
        kritische Diskrepanz tragen, die vorher nicht da war."""
    regions = [
        ("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20)),
        ("p0-r1", RegionType.TEXT_LINE, (0, 30, 50, 50)),
    ]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    def _bulk_engines() -> list:
        solo = FakeEngine("solo", {"p0-r0": "Alleiniger Text."})
        engine_a = FakeEngine("engine_a", {"p0-r1": "Der Wert ist konstant."}, confidence=0.4)
        engine_b = FakeEngine("engine_b", {"p0-r1": "Der Wert ist konstant."}, confidence=0.4)
        return [solo, engine_a, engine_b]

    baseline = process_page(
        _page(), config=PipelineConfig(require_engines=(), verify_engines=()), engines=_bulk_engines()
    )
    assert baseline.regions[0].agreement == 0.0
    assert baseline.regions[1].disagreements == ()
    assert baseline.regions[1].has_critical_uncertainty is False

    verify = FakeEngine(
        "verify_vlm",
        {"p0-r0": "Alleiniger Text.", "p0-r1": "Der Wert ist nicht konstant."},
        kind="vlm",
    )
    verified = process_page(
        _page(),
        config=PipelineConfig(require_engines=(), verify_engines=("verify_vlm",)),
        engines=[*_bulk_engines(), verify],
    )

    assert verified.regions[0].agreement == 1.0
    assert verified.regions[1].has_critical_uncertainty is True
    assert verified.regions[1].agreement < 1.0


def test_verify_engine_failure_is_recorded_not_fatal(monkeypatch):
    """Schlaegt die Verifikations-Engine selbst fehl (z.B. Ollama nicht
    erreichbar), darf das weder die Seite zum Scheitern bringen noch den
    bereits vorhandenen Bulk-Konsens verwerfen -- der Fehlschlag wird wie
    jeder andere Engine-Fehlschlag in engine_failures vermerkt (siehe
    _recognize_all, gemeinsam fuer Bulk- und Verifikationslauf).

    Zusaetzlich (siehe Auftrag Fix 4): schlagen ALLE fuer eine ausgewaehlte
    Region vorgesehenen Verifikations-Engines fehl, muss die Region das
    selbst tragen (``verify_failed=True``, in ``to_dict()`` als
    ``verifyFailed``) -- sonst ist "verifiziert, sauber befunden" von
    "Verifikation versucht und fehlgeschlagen" nicht mehr unterscheidbar:
    engine_failures ist Seiten-, nicht Regionen-bezogen, eine Lehrkraft
    koennte also nicht erkennen, DASS gerade diese Region keinen
    tatsaechlichen zweiten Blick bekommen hat."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Die Kraft ist konstant.")
    htr = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    verify = FakeEngine("verify_vlm", "wird nie verwendet", fail_with="ollama_offline", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",))

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    assert ("verify_vlm", "ollama_offline") in result.engine_failures
    assert result.status is not OCRStatus.FAILED
    region = result.regions[0]
    assert not any(c.engine == "verify_vlm" for c in region.candidates)
    # Der urspruengliche Bulk-Konsens (die Diskrepanz) bleibt erhalten.
    assert region.disagreements
    assert region.verify_failed is True
    assert region.to_dict(include_text=True)["verifyFailed"] is True


def test_verify_succeeded_region_is_not_marked_verify_failed(monkeypatch):
    """Gegenprobe zu test_verify_engine_failure_is_recorded_not_fatal:
    liefert die Verifikations-Engine tatsaechlich einen Kandidaten, bleibt
    verify_failed False -- der Marker darf nicht generell fuer jede
    ausgewaehlte Region gesetzt werden, sondern NUR, wenn wirklich JEDE
    Verifikations-Engine fehlgeschlagen ist."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Die Kraft ist konstant.")
    htr = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    verify = FakeEngine("verify_vlm", "Die Kraft ist nicht konstant.", kind="vlm")
    config = PipelineConfig(require_engines=(), verify_engines=("verify_vlm",))

    result = process_page(_page(), config=config, engines=[tesseract, htr, verify])

    region = result.regions[0]
    assert any(c.engine == "verify_vlm" for c in region.candidates)
    assert region.verify_failed is False
    assert region.to_dict(include_text=True)["verifyFailed"] is False


def test_verify_engine_cloud_blocked_propagates(monkeypatch):
    """CloudBlocked aus einer Verifikations-Engine darf ebenso wenig
    abgefangen werden wie aus einer Bulk-Engine (siehe
    test_cloud_blocked_propagates_out_of_pipeline) -- der selektive Pfad
    darf den privacy_guard-Vertrag nicht unterlaufen."""
    regions = [("p0-r0", RegionType.TEXT_LINE, (0, 0, 50, 20))]
    _patch_page_flow(monkeypatch, quality=_benign_quality(), regions=regions)

    tesseract = FakeEngine("tesseract", "Die Kraft ist konstant.")
    htr = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    cloud_verify = _CloudBlockedEngine()
    config = PipelineConfig(require_engines=(), verify_engines=(cloud_verify.name,))

    with pytest.raises(CloudBlocked):
        process_page(_page(), config=config, engines=[tesseract, htr, cloud_verify])


class _BlockingFinder:
    """sys.meta_path-Finder, der BLOCKED_ROOTS unauffindbar macht -- muss
    den Import ablehnen (raise), bevor der reguläre PathFinder die echten,
    in tools/.venv installierten Pakete faende (siehe
    tests/test_ocr_engines.py::_BlockingFinder, identisches Muster)."""

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".", 1)[0]
        if root in BLOCKED_ROOTS:
            raise ModuleNotFoundError(f"blocked for test: {fullname}")
        return None


def _purge_ocr_modules() -> dict:
    removed = {}
    for name in list(sys.modules):
        if name == "teacherassist_core.ocr" or name.startswith("teacherassist_core.ocr."):
            removed[name] = sys.modules.pop(name)
    return removed


def test_pipeline_imports_without_torch():
    """import teacherassist_core.ocr (das jetzt pipeline.py/store.py
    reexportiert) muss auch dann gelingen, wenn torch/transformers/
    pytesseract/PIL/numpy/paddle fuer die Dauer des Tests unauffindbar sind
    -- siehe Auftrag: "No top-level import of heavy deps in pipeline.py or
    store.py. import teacherassist_core.ocr must stay cheap." Spiegelt
    tests/test_ocr_engines.py::test_engines_import_without_heavy_deps."""
    finder = _BlockingFinder()
    sys.meta_path.insert(0, finder)
    saved = _purge_ocr_modules()
    try:
        importlib.import_module("teacherassist_core.ocr")
    finally:
        sys.meta_path.remove(finder)
        _purge_ocr_modules()
        restore_purged_modules(saved)
