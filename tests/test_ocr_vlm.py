"""Testet die Ollama-Vision-Engine (VLM, Stufe 7 des OCR-Refactors).

Deckt teacherassist_core/ocr/engines/ollama_vlm.py (OllamaVlmEngine) sowie
die Registrierung in engines/__init__.py (ENGINE_FACTORIES, DEFAULT_ENGINES,
ocr_capability_status) ab.

KEIN Test hier fasst ein echtes Netzwerk oder eine echte Ollama-Instanz an:
urllib.request.urlopen wird in jedem Test durch einen In-Prozess-Stub
ersetzt (siehe _StubTransport unten). Insbesondere fuer
test_never_falls_back_to_text_model und
test_refuses_non_loopback_endpoint_before_any_socket gilt: der Stub laesst
den Test bewusst fehlschlagen (pytest.fail), wenn er ueberhaupt/mit der
falschen URL erreicht wird -- "kein Generate-Aufruf" bzw. "kein Socket vor
CloudBlocked" ist damit KEIN Nebeneffekt, sondern eine gepruefte Aussage.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest

from teacherassist_core.ocr.engines import DEFAULT_ENGINES, ENGINE_FACTORIES
from teacherassist_core.ocr.engines.base import EngineError
import teacherassist_core.ocr.engines.ollama_vlm as ollama_vlm
from teacherassist_core.ocr.engines.ollama_vlm import (
    DEFAULT_VISION_MODEL,
    VISION_MODEL_PREFIXES,
    VLM_CONFIDENCE,
    OllamaVlmEngine,
)
from teacherassist_core.ocr.privacy_guard import CloudBlocked
from teacherassist_core.ocr.prompts import FORMULA_PROMPT_DE, VERBATIM_PROMPT_DE
from teacherassist_core.ocr.types import RegionType


@pytest.fixture(autouse=True)
def _clear_tags_cache():
    """_fetch_tags() cached ~10s ueber ALLE Instanzen desselben Endpunkts
    hinweg (siehe Moduldoc) -- ohne diesen Reset wuerde ein Test vom
    Ollama-Zustand eines vorherigen Tests "erben"."""
    ollama_vlm._tags_cache.clear()
    yield
    ollama_vlm._tags_cache.clear()


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class _StubTransport:
    """Ersetzt urllib.request.urlopen fuer die Dauer eines Tests.

    `forbid` ist eine Menge von URL-Teilstrings, die -- falls angefragt --
    den Test sofort per pytest.fail() scheitern lassen, statt einfach eine
    Fake-Antwort zu liefern. Das macht "diese Anfrage darf NIE passieren"
    zu einer echten Testaussage statt einer Hoffnung."""

    def __init__(
        self,
        *,
        tags: list[str] | None = None,
        offline: bool = False,
        chat_content: str = "",
        generate_content: str = "",
        forbid: tuple[str, ...] = (),
    ) -> None:
        self.tags = tags or []
        self.offline = offline
        self.chat_content = chat_content
        self.generate_content = generate_content
        self.forbid = forbid
        self.calls: list[str] = []
        self.bodies: list[dict] = []

    def __call__(self, request: urllib.request.Request, timeout: float | None = None):
        url = request.full_url
        self.calls.append(url)
        for marker in self.forbid:
            if marker in url:
                pytest.fail(f"unerwarteter Netzwerkaufruf erreichte verbotenen Endpunkt: {url}")

        if url.endswith("/api/tags"):
            if self.offline:
                raise OSError("connection refused")
            payload = json.dumps({"models": [{"name": name} for name in self.tags]}).encode("utf-8")
            return _FakeResponse(payload)

        if request.data:
            self.bodies.append(json.loads(request.data.decode("utf-8")))

        if url.endswith("/v1/chat/completions"):
            payload = json.dumps(
                {"choices": [{"message": {"content": self.chat_content}}]}
            ).encode("utf-8")
            return _FakeResponse(payload)

        if url.endswith("/api/generate"):
            payload = json.dumps({"response": self.generate_content}).encode("utf-8")
            return _FakeResponse(payload)

        pytest.fail(f"unerwartete URL angefragt: {url}")


def _make_image():
    from PIL import Image

    return Image.new("RGB", (20, 10), color="white")


# ---------------------------------------------------------------------------
# Bug 2: nie auf ein Text-Modell zurueckfallen
# ---------------------------------------------------------------------------
def test_never_falls_back_to_text_model(monkeypatch):
    """/api/tags liefert NUR gemma3:4b (ein Text-Modell) -- recognize() MUSS
    EngineError("model_not_pulled:...") werfen, und der Stub muss den Test
    scheitern lassen, falls je ein Generate-Aufruf versucht wird."""
    stub = _StubTransport(tags=["gemma3:4b"], forbid=("/v1/chat/completions", "/api/generate"))
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine(classification="public_curriculum")
    with pytest.raises(EngineError) as excinfo:
        engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)

    assert excinfo.value.reason.startswith(f"model_not_pulled:{engine.model_id}")
    assert stub.calls == ["http://127.0.0.1:11434/api/tags"]


def test_prefers_configured_model_then_prefix_order(monkeypatch):
    """Bevorzugt self.model_id, wenn es (a) in tags vorkommt und (b) ein
    bekanntes Vision-Praefix traegt; sonst faellt es auf den ERSTEN Treffer
    in VISION_MODEL_PREFIXES-Reihenfolge zurueck -- NICHT auf die
    Erscheinungsreihenfolge in tags."""
    engine_configured = OllamaVlmEngine(model_id="qwen2.5-vl:7b")
    chosen = engine_configured._resolve_vision_model(["qwen2.5-vl:7b", "moondream:latest"])
    assert chosen == "qwen2.5-vl:7b"

    # self.model_id (Default DEFAULT_VISION_MODEL == "qwen3-vl:8b") ist NICHT
    # in tags vorhanden -- "moondream" steht in tags VOR "qwen2.5-vl", aber
    # qwen2.5-vl steht in VISION_MODEL_PREFIXES vor moondream und muss daher
    # gewinnen.
    assert VISION_MODEL_PREFIXES.index("qwen2.5-vl") < VISION_MODEL_PREFIXES.index("moondream")
    engine_default = OllamaVlmEngine()
    chosen_fallback = engine_default._resolve_vision_model(["moondream:latest", "qwen2.5-vl:7b"])
    assert chosen_fallback == "qwen2.5-vl:7b"


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------
def test_refuses_non_loopback_endpoint_before_any_socket(monkeypatch):
    """Ein nicht-lokaler Endpunkt mit einer Cloud-verbietenden Klassifikation
    muss CloudBlocked werfen, BEVOR irgendein Socket geoeffnet wird -- der
    Stub laesst den Test scheitern, falls er ueberhaupt aufgerufen wird."""

    def _forbidden(*args, **kwargs):
        pytest.fail("urlopen wurde aufgerufen, bevor assert_local_only greifen konnte")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    engine = OllamaVlmEngine(endpoint="https://evil.example/api", classification="student_submission")
    with pytest.raises(CloudBlocked):
        engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)


def test_cloud_blocked_not_converted_to_engine_error(monkeypatch):
    """CloudBlocked darf NIE in einen EngineError umgewandelt werden (siehe
    privacy_guard.py Modul-Docstring) -- recognize() faengt sie nicht ab."""

    def _forbidden(*args, **kwargs):
        pytest.fail("urlopen wurde aufgerufen, bevor assert_local_only greifen konnte")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    engine = OllamaVlmEngine(endpoint="https://evil.example/api", classification="student_submission")
    try:
        engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)
        pytest.fail("recognize() haette CloudBlocked werfen muessen")
    except CloudBlocked:
        pass
    except EngineError:
        pytest.fail("CloudBlocked wurde faelschlich in EngineError umgewandelt")


# ---------------------------------------------------------------------------
# status()
# ---------------------------------------------------------------------------
def test_status_reports_ollama_offline(monkeypatch):
    stub = _StubTransport(offline=True)
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    status = engine.status()
    assert status.available is False
    assert status.reason == "ollama_offline"


def test_status_never_pulls_a_model(monkeypatch):
    """status() darf NUR /api/tags anfassen -- nie einen Pull/Generate-Call."""
    stub = _StubTransport(
        tags=["qwen3-vl:8b"],
        forbid=("/v1/chat/completions", "/api/generate", "pull"),
    )
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    status = engine.status()
    assert status.available is True
    assert stub.calls == ["http://127.0.0.1:11434/api/tags"]


# ---------------------------------------------------------------------------
# Prompt/Markup/Transport
# ---------------------------------------------------------------------------
def test_uses_verbatim_prompt_for_text_and_formula_prompt_for_formula(monkeypatch):
    stub = _StubTransport(tags=["qwen3-vl:8b"], chat_content="Text")
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)
    engine.recognize(_make_image(), region_type=RegionType.FORMULA)

    assert len(stub.bodies) == 2
    text_prompt = stub.bodies[0]["messages"][0]["content"][0]["text"]
    formula_prompt = stub.bodies[1]["messages"][0]["content"][0]["text"]
    assert text_prompt == VERBATIM_PROMPT_DE
    assert formula_prompt == FORMULA_PROMPT_DE


def test_markup_is_parsed(monkeypatch):
    stub = _StubTransport(
        tags=["qwen3-vl:8b"],
        chat_content="Das ist <uncertain>ist|ist nicht</uncertain> wahr.",
    )
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    candidate = engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)

    assert "uncertain" in candidate.markers
    assert "<uncertain>" not in candidate.text
    assert "ist nicht" not in candidate.text  # bevorzugte Lesart zuerst


def test_temperature_is_zero(monkeypatch):
    stub = _StubTransport(tags=["qwen3-vl:8b"], chat_content="Text")
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)

    assert stub.bodies[0]["temperature"] == 0


def test_confidence_is_not_fabricated(monkeypatch):
    """Pin auf die dokumentierte Konstante -- eine spaeter hartkodierte 0.9
    (oder jeder andere "erfundene" Wert) laesst diesen Test fehlschlagen."""
    stub = _StubTransport(tags=["qwen3-vl:8b"], chat_content="Text")
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    engine = OllamaVlmEngine()
    candidate = engine.recognize(_make_image(), region_type=RegionType.PARAGRAPH)

    assert VLM_CONFIDENCE < 0.75  # unterhalb consensus.decide_status' min_confidence-Default
    assert candidate.confidence == VLM_CONFIDENCE
    assert candidate.confidence == 0.5


# ---------------------------------------------------------------------------
# Registrierung
# ---------------------------------------------------------------------------
def test_registered_but_not_default():
    assert "ollama_vlm" in ENGINE_FACTORIES
    assert "ollama_vlm" not in DEFAULT_ENGINES

    engine = ENGINE_FACTORIES["ollama_vlm"]({"ocrVisionModel": "minicpm-v:8b"})
    assert isinstance(engine, OllamaVlmEngine)
    assert engine.model_id == "minicpm-v:8b"

    default_engine = ENGINE_FACTORIES["ollama_vlm"]({})
    assert default_engine.model_id == DEFAULT_VISION_MODEL


def test_factory_reads_classification_from_settings():
    """Die von tool_server.py in die settings-Mapping eingemischte
    "classification" (siehe engines/__init__.py-Kommentar) erreicht die
    Engine-Instanz -- ohne sie faellt das restriktivste Default
    ("student_submission")."""
    engine = ENGINE_FACTORIES["ollama_vlm"]({"classification": "public_curriculum"})
    assert engine.classification == "public_curriculum"

    default_engine = ENGINE_FACTORIES["ollama_vlm"]({})
    assert default_engine.classification == "student_submission"


# ---------------------------------------------------------------------------
# Quell-Vertrag: "gemma3:4b" darf in engines/ nirgends mehr vorkommen
# ---------------------------------------------------------------------------
def test_no_text_model_fallback_literal_in_engines_source():
    engines_dir = Path(ollama_vlm.__file__).resolve().parent
    offenders = []
    for path in engines_dir.glob("*.py"):
        if "gemma3:4b" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []
