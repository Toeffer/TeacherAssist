"""Testet die PaddleOCR-VL-Engine (Stufe 8 des OCR-Refactors).

Deckt teacherassist_core/ocr/engines/paddleocr_vl.py (PaddleOcrVlEngine)
sowie die Registrierung in engines/__init__.py (ENGINE_FACTORIES,
DEFAULT_ENGINES) ab.

Diese Engine ist gebaut, registriert und ABSICHTLICH DEAKTIVIERT (siehe
paddleocr_vl.py Moduldoc) -- keine der beiden konkurrierenden
Abhaengigkeiten (paddlepaddle/paddleocr[doc-parser], transformers>=5) ist in
diesem venv installiert. KEIN Test hier installiert etwas, laedt ein
Modell oder fasst ein Netzwerk an: is_available()/status() werden ueber
gestubbte Versions-/Import-Proben getestet (wie test_ocr_engines.py fuer
htr/tesseract), und die Backend-Aufrufe selbst werden fuer den
Erkennungstest durch einen In-Prozess-Stub ersetzt (wie test_ocr_vlm.py
fuer ollama_vlm).
"""

from __future__ import annotations

import importlib
import sys

import pytest

from teacherassist_core.ocr.engines import DEFAULT_ENGINES, ENGINE_FACTORIES
from teacherassist_core.ocr.engines.base import EngineError, EngineStatus

# importlib.import_module() statt "import ... as paddleocr_vl_module": ein
# DOTTED-ATTRIBUTE-Import wird ueber Attributzugriff auf die Elternpakete
# aufgeloest, nicht ueber sys.modules -- siehe test_ocr_htr.py fuer die
# ausfuehrliche Begruendung. Wichtig hier, weil dieses Testmodul selbst
# teacherassist_core.ocr.engines.paddleocr_vl purgt/neu importiert (siehe
# test_import_without_paddle_or_transformers).
paddleocr_vl_module = importlib.import_module("teacherassist_core.ocr.engines.paddleocr_vl")
from teacherassist_core.ocr.engines.paddleocr_vl import (
    BACKEND_AUTO,
    BACKEND_PADDLE,
    BACKEND_TRANSFORMERS,
    DEFAULT_PADDLE_MODEL,
    FALLBACK_CONFIDENCE,
    PaddleOcrVlEngine,
    _resolve_backend,
)
from teacherassist_core.ocr.privacy_guard import CloudBlocked
from teacherassist_core.ocr.types import RegionType

from _ocr_module_reload_helpers import restore_purged_modules


# ---------------------------------------------------------------------------
# status() -- Versionsproben gestubbt, kein echter Import
# ---------------------------------------------------------------------------
def test_status_reports_transformers_too_old(monkeypatch):
    """Backend "transformers": Paddle ist irrelevant, nur die installierte
    transformers-Version zaehlt. Gestubbt auf "4.57.6" (die tatsaechlich in
    diesem venv installierte Version, siehe requirements-ocr.txt) -- die
    Version wird zur LAUFZEIT gelesen, nie hartkodiert erwartet."""
    monkeypatch.setattr(
        paddleocr_vl_module, "_transformers_installed_version", lambda: "4.57.6"
    )
    engine = PaddleOcrVlEngine(backend=BACKEND_TRANSFORMERS)

    status = engine.status()

    assert status.available is False
    assert status.reason == "transformers_too_old:4.57.6<5.0.0"
    assert status.name == "paddleocr_vl"
    assert status.kind == "layout"
    assert engine.is_available() is False


def test_status_reports_paddle_not_installed(monkeypatch):
    """Backend "paddleocr": transformers ist irrelevant, nur ob
    paddle/paddleocr importierbar sind zaehlt."""
    monkeypatch.setattr(paddleocr_vl_module, "_paddle_deps_available", lambda: False)
    engine = PaddleOcrVlEngine(backend=BACKEND_PADDLE)

    status = engine.status()

    assert status.available is False
    assert status.reason == "not_installed:paddlepaddle"
    assert engine.is_available() is False


def test_auto_backend_selection_order(monkeypatch):
    """"auto" waehlt paddleocr, falls importierbar, sonst transformers,
    falls dessen Version ausreicht, sonst gar keines -- mit dem
    aussagekraeftigsten verfuegbaren Grund (siehe _resolve_backend)."""
    # paddle verfuegbar -> gewinnt, unabhaengig von transformers.
    monkeypatch.setattr(paddleocr_vl_module, "_paddle_deps_available", lambda: True)
    monkeypatch.setattr(
        paddleocr_vl_module, "_transformers_installed_version", lambda: "5.1.0"
    )
    backend, reason = _resolve_backend(BACKEND_AUTO)
    assert backend == BACKEND_PADDLE
    assert reason == ""

    # paddle fehlt, transformers ausreichend -> transformers.
    monkeypatch.setattr(paddleocr_vl_module, "_paddle_deps_available", lambda: False)
    monkeypatch.setattr(
        paddleocr_vl_module, "_transformers_installed_version", lambda: "5.1.0"
    )
    backend, reason = _resolve_backend(BACKEND_AUTO)
    assert backend == BACKEND_TRANSFORMERS
    assert reason == ""

    # paddle fehlt, transformers installiert aber zu alt -> nicht verfuegbar,
    # Grund nennt die zu alte Version (nicht "not_installed").
    monkeypatch.setattr(
        paddleocr_vl_module, "_transformers_installed_version", lambda: "4.57.6"
    )
    backend, reason = _resolve_backend(BACKEND_AUTO)
    assert backend is None
    assert reason == "transformers_too_old:4.57.6<5.0.0"

    # weder paddle noch transformers vorhanden -> "not_installed:paddlepaddle".
    monkeypatch.setattr(paddleocr_vl_module, "_transformers_installed_version", lambda: None)
    backend, reason = _resolve_backend(BACKEND_AUTO)
    assert backend is None
    assert reason == "not_installed:paddlepaddle"


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------
def test_refuses_non_loopback_before_any_call(monkeypatch):
    """assert_local_only() ist die ALLERERSTE Anweisung von recognize() --
    ein (hier gestubbter) nicht-lokaler Modell-Endpunkt-Marker muss
    CloudBlocked werfen, BEVOR auch nur der Ladepfad des Backends beruehrt
    wird. Der Stub laesst den Test scheitern, falls er ueberhaupt
    aufgerufen wird."""
    monkeypatch.setattr(
        paddleocr_vl_module, "_LOCAL_MODEL_ENDPOINT", "https://evil.example/paddleocr-vl"
    )

    def _forbidden(self):
        pytest.fail("Modell-Ladepfad wurde aufgerufen, bevor assert_local_only greifen konnte")

    monkeypatch.setattr(PaddleOcrVlEngine, "_load_transformers_model", _forbidden)
    monkeypatch.setattr(PaddleOcrVlEngine, "_load_paddleocr_pipeline", _forbidden)

    engine = PaddleOcrVlEngine(classification="student_submission")
    with pytest.raises(CloudBlocked):
        engine.recognize(object(), region_type=RegionType.PARAGRAPH)


def test_cloud_blocked_not_converted_to_engine_error(monkeypatch):
    """CloudBlocked darf NIE in einen EngineError umgewandelt werden (siehe
    privacy_guard.py Modul-Docstring und paddleocr_vl.py Moduldoc
    "PRIVACY")."""
    monkeypatch.setattr(
        paddleocr_vl_module, "_LOCAL_MODEL_ENDPOINT", "https://evil.example/paddleocr-vl"
    )
    engine = PaddleOcrVlEngine(classification="student_submission")
    try:
        engine.recognize(object(), region_type=RegionType.PARAGRAPH)
        pytest.fail("recognize() haette CloudBlocked werfen muessen")
    except CloudBlocked:
        pass
    except EngineError:
        pytest.fail("CloudBlocked wurde faelschlich in EngineError umgewandelt")


# ---------------------------------------------------------------------------
# status() loest NIE einen Download aus
# ---------------------------------------------------------------------------
def test_never_downloads_from_status(monkeypatch):
    """status() darf unter keiner Kombination von Backend-Verfuegbarkeit je
    den Modell-Ladepfad (from_pretrained/paddleocr-Pipeline-Aufbau)
    beruehren -- nur find_spec()/importlib.metadata.version()/
    try_to_load_from_cache(), nie einen echten Import oder Download."""

    def _forbidden(self):
        pytest.fail("status() hat den Modell-Ladepfad beruehrt")

    monkeypatch.setattr(PaddleOcrVlEngine, "_load_transformers_model", _forbidden)
    monkeypatch.setattr(PaddleOcrVlEngine, "_load_paddleocr_pipeline", _forbidden)

    for backend in (BACKEND_AUTO, BACKEND_PADDLE, BACKEND_TRANSFORMERS):
        engine = PaddleOcrVlEngine(backend=backend)
        status = engine.status()
        assert status.available is False
        assert status.reason


# ---------------------------------------------------------------------------
# Registrierung
# ---------------------------------------------------------------------------
def test_registered_but_not_default():
    assert "paddleocr_vl" in ENGINE_FACTORIES
    assert "paddleocr_vl" not in DEFAULT_ENGINES

    engine = ENGINE_FACTORIES["paddleocr_vl"](
        {"ocrPaddleModel": "custom/model-id", "ocrPaddleBackend": BACKEND_TRANSFORMERS}
    )
    assert isinstance(engine, PaddleOcrVlEngine)
    assert engine.model_id == "custom/model-id"
    assert engine.backend == BACKEND_TRANSFORMERS

    default_engine = ENGINE_FACTORIES["paddleocr_vl"]({})
    assert default_engine.model_id == DEFAULT_PADDLE_MODEL
    assert default_engine.backend == BACKEND_AUTO
    assert default_engine.classification == "student_submission"


# ---------------------------------------------------------------------------
# Lazy-Import-Vertrag: import ohne paddle/paddleocr/transformers/torch/PIL
# ---------------------------------------------------------------------------
BLOCKED_ROOTS = frozenset({"paddle", "paddleocr", "transformers", "torch", "PIL"})


class _BlockingFinder:
    """Wie test_ocr_engines.py:_BlockingFinder -- macht BLOCKED_ROOTS fuer
    die Dauer des Tests unauffindbar, unabhaengig davon, ob sie auf dieser
    Maschine tatsaechlich installiert sind."""

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".", 1)[0]
        if root in BLOCKED_ROOTS:
            raise ModuleNotFoundError(f"blocked for test: {fullname}")
        return None


def _purge_engines_modules() -> dict:
    removed = {}
    for name in list(sys.modules):
        if name == "teacherassist_core.ocr.engines" or name.startswith(
            "teacherassist_core.ocr.engines."
        ):
            removed[name] = sys.modules.pop(name)
    return removed


def test_import_without_paddle_or_transformers():
    """import teacherassist_core.ocr.engines.paddleocr_vl darf mit allen
    fuenf schweren Abhaengigkeiten vom sys.meta_path blockiert trotzdem
    gelingen (siehe engines/__init__.py "LAZY-IMPORT-VERTRAG"), und
    status()/is_available() muessen available=False mit einem befuellten
    reason-String liefern -- NIE einen ImportError durchschlagen lassen."""
    finder = _BlockingFinder()
    sys.meta_path.insert(0, finder)
    saved_modules = _purge_engines_modules()
    try:
        module = importlib.import_module("teacherassist_core.ocr.engines.paddleocr_vl")
        engine = module.PaddleOcrVlEngine()
        status = engine.status()
        available = engine.is_available()
    finally:
        sys.meta_path.remove(finder)
        _purge_engines_modules()
        restore_purged_modules(saved_modules)

    assert available is False
    assert status.available is False
    assert status.reason  # nicht-leerer, maschinenlesbarer Grund


# ---------------------------------------------------------------------------
# supports()
# ---------------------------------------------------------------------------
def test_supports_document_region_types():
    """Dokumenten-Layout-Parser: Text, Absaetze, Tabellen, Formeln,
    Ueberschriften -- KEINE Abbildungen (FIGURE ist kein OCR-Fall)."""
    engine = PaddleOcrVlEngine()

    for region_type in (
        RegionType.TEXT_LINE,
        RegionType.PARAGRAPH,
        RegionType.TABLE,
        RegionType.FORMULA,
        RegionType.HEADER,
    ):
        assert engine.supports(region_type) is True

    assert engine.supports(RegionType.FIGURE) is False


# ---------------------------------------------------------------------------
# recognize() gegen ein gestubbtes Backend
# ---------------------------------------------------------------------------
def test_recognize_builds_candidate_from_stubbed_backend(monkeypatch):
    """recognize() selbst fuehrt kein Backend aus -- _run_backend() ist der
    Test-Seam (siehe paddleocr_vl.py Moduldoc). Deckt ab: status()-Gate
    umgangen (gestubbt auf verfuegbar), Markup wird wie bei jeder anderen
    Engine aufgeloest, und die vom Stub gelieferte Konfidenz landet
    unveraendert im Kandidaten."""
    engine = PaddleOcrVlEngine()
    monkeypatch.setattr(
        engine,
        "status",
        lambda: EngineStatus(
            name=engine.name,
            kind=engine.kind,
            available=True,
            reason="",
            model_id=engine.model_id,
            capabilities=engine.capabilities,
        ),
    )
    raw = "Die Kraft <uncertain>ist|ist nicht</uncertain> konstant."
    monkeypatch.setattr(
        PaddleOcrVlEngine,
        "_run_backend",
        lambda self, backend, image, prompt: (raw, 0.91),
    )

    candidate = engine.recognize(object(), region_type=RegionType.PARAGRAPH, region_id="p1-r1")

    assert candidate.engine == "paddleocr_vl"
    assert candidate.raw_text == raw
    assert "ist nicht" not in candidate.text
    assert "ist" in candidate.text
    assert "uncertain" in candidate.markers
    assert candidate.confidence == 0.91


def test_recognize_rejects_unsupported_region_type(monkeypatch):
    """FIGURE wird von supports() abgelehnt -- recognize() muss vorher
    scheitern, ohne je das Backend zu erreichen."""
    engine = PaddleOcrVlEngine()

    def _forbidden(self, backend, image, prompt):
        pytest.fail("_run_backend wurde trotz nicht unterstuetztem RegionType aufgerufen")

    monkeypatch.setattr(PaddleOcrVlEngine, "_run_backend", _forbidden)

    with pytest.raises(EngineError) as excinfo:
        engine.recognize(object(), region_type=RegionType.FIGURE, region_id="p2-r3")

    assert "unsupported_region_type" in excinfo.value.reason
    assert "p2-r3" in excinfo.value.reason


def test_recognize_raises_engine_error_when_unavailable():
    """Ohne installierte Abhaengigkeit (der reale Zustand dieses venv)
    muss recognize() eine EngineError mit dem status()-Grund werfen --
    nie einen leeren/geratenen Kandidaten liefern (siehe base.EngineError
    Docstring)."""
    engine = PaddleOcrVlEngine()
    assert engine.status().available is False  # echter Zustand dieses venv

    with pytest.raises(EngineError) as excinfo:
        engine.recognize(object(), region_type=RegionType.PARAGRAPH, region_id="p4-r1")

    assert excinfo.value.engine == "paddleocr_vl"
    assert "p4-r1" in excinfo.value.reason


def test_fallback_confidence_below_min_confidence_default():
    """Wie ollama_vlm.py:VLM_CONFIDENCE -- die dokumentierte Konstante muss
    unterhalb von consensus.decide_status()'s min_confidence-Default (0.75)
    liegen, sonst koennte sie allein Auto-Clean/APPROVED beeinflussen."""
    assert FALLBACK_CONFIDENCE < 0.75
