"""Testet die HTR-Engine (Handschrifterkennung, Stufe 6 des OCR-Refactors).

Deckt teacherassist_core/ocr/engines/htr.py (HtrEngine) sowie die
Registrierung in engines/__init__.py (ENGINE_FACTORIES, DEFAULT_ENGINES,
ocr_capability_status) und den Download-Endpoint POST
/api/v1/ocr/models/download in tool_server.py ab.

KEIN Test hier laedt ein echtes Modell herunter, braucht eine GPU oder
fasst das Netzwerk an -- torch/transformers sind auf dieser Maschine zwar
echt installiert (siehe Umgebungsfakten der Aufgabe), aber die Modellgewichte
von fhswf/TrOCR_german_handwritten liegen nicht im HF-Cache; jeder Test, der
eine echte Erkennung braucht, stubbt Prozessor/Modell statt from_pretrained()
zu erreichen.
"""

from __future__ import annotations

import http.client
import importlib
import json
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

import pytest

from conftest import stub_ollama_vlm_factory
from teacherassist_core.ocr.engines import (
    DEFAULT_ENGINES,
    ENGINE_FACTORIES,
    ocr_capability_status,
)
from teacherassist_core.ocr.engines.base import EngineError
from teacherassist_core.ocr.engines.fake import FakeEngine
from teacherassist_core.ocr.engines.htr import DEFAULT_HTR_MODEL, HtrEngine
from teacherassist_core.ocr.types import RegionType

BLOCKED_ROOTS = frozenset({"torch", "transformers"})


# ---------------------------------------------------------------------------
# status() -- die drei Zustaende
# ---------------------------------------------------------------------------
def test_htr_status_without_model_reports_not_downloaded(monkeypatch):
    """status() unterscheidet drei Zustaende: fehlende Abhaengigkeiten,
    Abhaengigkeiten vorhanden aber Gewichte nicht im Cache, und bereit."""
    # importlib.import_module() statt "import ... as htr_module": Ein
    # DOTTED-ATTRIBUTE-Import wie "import teacherassist_core.ocr.engines.htr
    # as htr_module" wird ueber Attributzugriff auf die Elternpakete
    # aufgeloest (teacherassist_core -> .ocr -> .engines -> .htr), nicht
    # ueber sys.modules -- und teacherassist_core.ocr's .engines-Attribut
    # bleibt nach test_ocr_engines.py::test_engines_import_without_heavy_deps
    # (das engines.htr fuer die Dauer des Tests purgt/neu importiert)
    # inkonsistent stehen, selbst wenn sys.modules selbst korrekt
    # zurueckgesetzt wird. importlib.import_module() liest dagegen garantiert
    # aus sys.modules und liefert deshalb zuverlaessig dasselbe Modulobjekt,
    # dessen __dict__ auch HtrEngine.status tatsaechlich verwendet.
    htr_module = importlib.import_module("teacherassist_core.ocr.engines.htr")

    engine = HtrEngine()

    # Zustand 1: Abhaengigkeiten fehlen.
    monkeypatch.setattr(htr_module, "_deps_available", lambda: False)
    status = engine.status()
    assert status.available is False
    assert status.reason == "not_installed:torch|transformers"

    # Zustand 2: Abhaengigkeiten vorhanden, Gewichte nicht im Cache.
    monkeypatch.setattr(htr_module, "_deps_available", lambda: True)
    monkeypatch.setattr(htr_module, "_weights_cached", lambda model_id: False)
    status = engine.status()
    assert status.available is False
    assert status.reason == f"model_not_downloaded:{DEFAULT_HTR_MODEL}"

    # Zustand 3: bereit.
    monkeypatch.setattr(htr_module, "_weights_cached", lambda model_id: True)
    status = engine.status()
    assert status.available is True
    assert status.reason == ""
    assert status.name == "htr"
    assert status.kind == "htr"


def test_htr_never_downloads_from_status(monkeypatch):
    """status() darf unter keinen Umstaenden das Netzwerk anfassen -- weder
    snapshot_download noch from_pretrained() duerfen erreicht werden. Beide
    werden hier so gepatcht, dass sie den Test scheitern lassen, falls sie
    doch aufgerufen werden."""

    def _boom(*args, **kwargs):
        raise AssertionError("status() darf keinen Download/from_pretrained ausloesen")

    import huggingface_hub
    import transformers

    monkeypatch.setattr(huggingface_hub, "snapshot_download", _boom)
    monkeypatch.setattr(transformers.TrOCRProcessor, "from_pretrained", classmethod(_boom))
    monkeypatch.setattr(transformers.VisionEncoderDecoderModel, "from_pretrained", classmethod(_boom))

    engine = HtrEngine()
    status = engine.status()  # darf nicht raisen
    assert status.name == "htr"


def _purge_htr_module() -> dict:
    removed = {}
    for name in list(sys.modules):
        if name == "teacherassist_core.ocr.engines.htr":
            removed[name] = sys.modules.pop(name)
    return removed


def _purge_real_heavy_modules() -> dict:
    """Entfernt torch/transformers (und Untermodule) aus sys.modules, falls
    andere Tests (in dieser Datei oder frueher im Lauf) sie bereits echt
    importiert haben. Noetig, weil importlib.util.find_spec() ein bereits in
    sys.modules gecachtes Modul SOFORT zurueckliefert, OHNE die
    sys.meta_path-Finder zu befragen -- ein blockierender Finder waere sonst
    wirkungslos, sobald irgendein frueherer Test `import torch` ausgeloest
    hat (z.B. test_htr_never_downloads_from_status oben). Die Eintraege
    werden danach unveraendert zurueckgegeben (kein echter Re-Import noetig)."""
    removed = {}
    for name in list(sys.modules):
        root = name.split(".", 1)[0]
        if root in BLOCKED_ROOTS:
            removed[name] = sys.modules.pop(name)
    return removed


def test_htr_import_without_torch():
    """Wie test_ocr_engines.py::test_engines_import_without_heavy_deps, aber
    gezielt fuer htr.py: mit torch/transformers vom sys.meta_path blockiert
    muss der Modulimport trotzdem gelingen (kein Top-Level-Import) und
    status() muss available=False mit reason="not_installed:..." liefern,
    statt eine ImportError hochzureissen."""

    class _BlockingFinder:
        def find_spec(self, fullname, path=None, target=None):
            root = fullname.split(".", 1)[0]
            if root in BLOCKED_ROOTS:
                raise ModuleNotFoundError(f"blocked for test: {fullname}")
            return None

    saved_heavy = _purge_real_heavy_modules()
    finder = _BlockingFinder()
    sys.meta_path.insert(0, finder)
    saved_htr = _purge_htr_module()
    try:
        htr_module = importlib.import_module("teacherassist_core.ocr.engines.htr")
        engine = htr_module.HtrEngine()
        status = engine.status()
    finally:
        sys.meta_path.remove(finder)
        _purge_htr_module()
        sys.modules.update(saved_htr)
        sys.modules.update(saved_heavy)

    assert status.available is False
    assert status.reason == "not_installed:torch|transformers"


# ---------------------------------------------------------------------------
# supports() / region-type-Ablehnung
# ---------------------------------------------------------------------------
def test_htr_rejects_non_text_line_regions():
    """TrOCR ist ein Ein-Zeilen-Modell -- PARAGRAPH/FORMULA muessen sofort
    mit EngineError('unsupported_region_type...') abgelehnt werden, ohne
    dass ueberhaupt ein Modell geladen werden muss."""
    engine = HtrEngine()
    assert engine.supports(RegionType.TEXT_LINE) is True
    assert engine.supports(RegionType.PARAGRAPH) is False
    assert engine.supports(RegionType.FORMULA) is False

    for region_type in (RegionType.PARAGRAPH, RegionType.FORMULA):
        with pytest.raises(EngineError) as exc_info:
            engine.recognize(None, region_type=region_type)
        assert exc_info.value.reason.startswith("unsupported_region_type")


def test_htr_engine_error_carries_region_id():
    """Wie tesseract.py's region_id-Vertrag: ein Fehlschlag muss die
    betroffene Region im reason-String tragen."""
    engine = HtrEngine()
    with pytest.raises(EngineError) as exc_info:
        engine.recognize(None, region_type=RegionType.PARAGRAPH, region_id="p3-r7")
    assert "p3-r7" in exc_info.value.reason
    assert "p3-r7" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Registrierung
# ---------------------------------------------------------------------------
def test_htr_registered_in_factories_but_not_default():
    """htr ist registriert, aber NICHT in DEFAULT_ENGINES -- ein nicht
    heruntergeladenes Modell darf keinen Job standardmaessig degradieren
    (siehe engines/__init__.py-Kommentar)."""
    assert "htr" in ENGINE_FACTORIES
    assert "htr" not in DEFAULT_ENGINES

    engine = ENGINE_FACTORIES["htr"]({})
    assert isinstance(engine, HtrEngine)
    assert engine.model_id == DEFAULT_HTR_MODEL
    assert engine.device == "auto"

    custom = ENGINE_FACTORIES["htr"]({"ocrHtrModel": "some/other-model", "ocrDevice": "cpu"})
    assert custom.model_id == "some/other-model"
    assert custom.device == "cpu"


def test_htr_accepts_region_id():
    """Struktureller Signatur-Check (siehe test_ocr_engines.py::
    test_all_registered_engines_accept_region_id, das bereits ALLE
    ENGINE_FACTORIES-Eintraege abdeckt und damit htr automatisch mit
    prueft) -- hier zusaetzlich explizit fuer htr allein bestaetigt."""
    import inspect

    engine = HtrEngine()
    signature = inspect.signature(engine.recognize)
    assert "region_id" in signature.parameters
    assert signature.parameters["region_id"].default is None


def test_ocr_capability_status_reflects_real_htr_availability(monkeypatch):
    """ocr_capability_status()['ocrHtr'] muss den echten Status widerspiegeln
    (Abhaengigkeiten UND heruntergeladene Gewichte), nicht mehr fest False."""
    # ocr_capability_status() befragt seit Stufe 7 auch ENGINE_FACTORIES["ollama_vlm"],
    # dessen status() ueber OllamaVlmEngine einen echten Netzwerkaufruf macht
    # (GET http://127.0.0.1:11434/api/tags) -- unabhaengig davon, ob dieser
    # Test ungestubbt bestehen wuerde (siehe assert unten, der nur ocrHtr
    # prueft), macht das die Suite davon abhaengig, ob gerade ein
    # Ollama-Dienst laeuft. Gleiche Behebung wie
    # tests/test_ocr_engines.py::_patch_engine_availability, hier aber NUR
    # fuer die hier irrelevante VLM-Quelle -- HTR bleibt bewusst echt/ungestubbt,
    # das ist genau das, was dieser Test verifiziert.
    monkeypatch.setitem(
        ENGINE_FACTORIES, "ollama_vlm", lambda settings: FakeEngine("ollama_vlm", "x", available=False)
    )

    status = ocr_capability_status({})
    # Auf dieser Maschine sind torch/transformers zwar installiert, die
    # Gewichte aber nicht im HF-Cache -- daher hier deterministisch False,
    # OHNE das Netzwerk anzufassen (ocr_capability_status ruft nur status()).
    engine = HtrEngine()
    assert status["ocrHtr"] == engine.status().available


# ---------------------------------------------------------------------------
# Download-Endpoint (tool_server.py)
# ---------------------------------------------------------------------------
@pytest.fixture
def isolated_server(tmp_path, monkeypatch):
    """Wie tests/test_ocr_http.py::isolated_server -- ein echter
    ToolHandler/_QuietThreadingHTTPServer ueber Loopback, damit Routing UND
    _authorize() mitgetestet werden."""
    import tool_server

    monkeypatch.setenv("TEACHERASSIST_DATA_DIR", str(tmp_path))
    runtime_paths = tool_server.RuntimePaths.from_environment(tool_server.BASE_DIR)
    runtime_paths.ensure()

    monkeypatch.setattr(tool_server, "RUNTIME_PATHS", runtime_paths)
    monkeypatch.setattr(tool_server, "UPLOAD_DIR", runtime_paths.uploads)
    monkeypatch.setattr(tool_server, "CHROMA_DIR", runtime_paths.chroma)
    monkeypatch.setattr(tool_server, "EXPORT_DIR", runtime_paths.exports)
    monkeypatch.setattr(tool_server, "LOG_DIR", runtime_paths.logs)
    monkeypatch.setattr(tool_server, "SETTINGS_FILE", runtime_paths.settings)
    monkeypatch.setattr(tool_server, "MEMORY_DIR", runtime_paths.memory)
    monkeypatch.setattr(
        tool_server, "SETTINGS_STORE", tool_server.SettingsStore(runtime_paths.settings, tool_server.CREDENTIALS)
    )
    monkeypatch.setattr(
        tool_server, "STATE_STORE", tool_server.EncryptedStateStore(runtime_paths.encrypted_state, None)
    )
    ocr_store = tool_server.OCRJobStore(runtime_paths.ocr, max_workers=1)
    monkeypatch.setattr(tool_server, "OCR_JOBS", ocr_store)
    monkeypatch.setattr(tool_server, "check_ollama", lambda: False)
    # ocr_capability_status() (called from bootstrap) independently builds
    # ENGINE_FACTORIES["ollama_vlm"] and calls .status() on it -- a SEPARATE
    # real network call that the check_ollama stub above does not cover
    # (see tests/conftest.py::stub_ollama_vlm_factory).
    stub_ollama_vlm_factory(monkeypatch)

    original_handlers = list(tool_server.logger.handlers)
    for handler in original_handlers:
        tool_server.logger.removeHandler(handler)
    temp_handler = RotatingFileHandler(runtime_paths.logs / "tool_server.log", encoding="utf-8")
    temp_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    tool_server.logger.addHandler(temp_handler)

    server = tool_server._QuietThreadingHTTPServer(("127.0.0.1", 0), tool_server.ToolHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], tool_server
    finally:
        server.shutdown()
        server.server_close()
        ocr_store.shutdown()
        thread.join(timeout=5)
        tool_server.logger.removeHandler(temp_handler)
        temp_handler.close()
        for handler in original_handlers:
            tool_server.logger.addHandler(handler)


def _bootstrap(port):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": f"localhost:{port}"})
        response = conn.getresponse()
        body = json.loads(response.read())
        set_cookie = response.getheader("Set-Cookie").split(";", 1)[0]
        return body["csrfToken"], set_cookie
    finally:
        conn.close()


def _post_json(port, csrf, cookie, path, payload):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Host": f"localhost:{port}",
            "Cookie": cookie,
            "X-CSRF-Token": csrf,
            "Content-Type": "application/json",
        }
        conn.request("POST", path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = None
        return response.status, parsed
    finally:
        conn.close()


def test_model_download_endpoint_validates_engine_and_model_id(isolated_server, monkeypatch):
    """POST /api/v1/ocr/models/download muss die Engine gegen
    ENGINE_FACTORIES und die Modell-ID gegen die strenge Regex pruefen,
    BEVOR ueberhaupt ein Download versucht wird -- snapshot_download wird
    gepatcht, um den Test scheitern zu lassen, falls er doch erreicht wird."""
    port, tool_server = isolated_server

    def _boom(*args, **kwargs):
        raise AssertionError("snapshot_download darf bei ungueltiger Eingabe nicht erreicht werden")

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "snapshot_download", _boom)

    csrf, cookie = _bootstrap(port)

    # Unbekannte Engine.
    status, body = _post_json(port, csrf, cookie, "/api/v1/ocr/models/download", {"engine": "does-not-exist"})
    assert status == 400
    assert "error" in body

    # Bekannte Engine, aber deren Modell-ID (via Settings) verletzt die
    # strenge Regex-Pruefung.
    monkeypatch.setattr(
        tool_server, "load_settings", lambda: {"ocrHtrModel": "not a valid id!!", "ocrDevice": "cpu"}
    )
    status, body = _post_json(port, csrf, cookie, "/api/v1/ocr/models/download", {"engine": "htr"})
    assert status == 400
    assert "error" in body


# ---------------------------------------------------------------------------
# recognize() mit gestubbtem Prozessor/Modell
# ---------------------------------------------------------------------------
class _StubGenerateOutput:
    def __init__(self, sequences, scores):
        self.sequences = sequences
        self.scores = scores


class _StubModel:
    """Minimaler Ersatz fuer VisionEncoderDecoderModel: generate() liefert
    feste Sequenzen/Scores, compute_transition_scores() liefert bekannte
    Log-Wahrscheinlichkeiten, sodass die abgeleitete confidence exakt
    nachgerechnet werden kann (kein hartkodierter Wert im Produktcode)."""

    def generate(self, pixel_values, **kwargs):
        import torch

        sequences = torch.tensor([[0, 5, 6, 7, 8, 2]])
        # 4 generierte Tokens -> 4 Score-Verteilungen (Inhalt irrelevant,
        # da compute_transition_scores unten gestubbt ist).
        scores = tuple(torch.zeros(1, 16) for _ in range(4))
        return _StubGenerateOutput(sequences, scores)

    def compute_transition_scores(self, sequences, scores, normalize_logits=True):
        import torch

        # Bekannte Wahrscheinlichkeiten: 0.9, 0.8, 0.7, 0.6 -> Mittel 0.75.
        return torch.log(torch.tensor([[0.9, 0.8, 0.7, 0.6]]))


class _StubProcessorOutput:
    def __init__(self, pixel_values):
        self.pixel_values = pixel_values


class _StubProcessor:
    def __call__(self, images, return_tensors="pt"):
        import torch

        return _StubProcessorOutput(torch.zeros(1, 3, 4, 4))

    def batch_decode(self, sequences, skip_special_tokens=True):
        return ["Ich bin ein Testsatz"]


def test_htr_recognize_builds_candidate_from_stubbed_model(monkeypatch):
    """Stubbt Prozessor/Modell im Modul-Cache (statt from_pretrained/
    snapshot_download zu erreichen) und prueft, dass recognize() daraus
    einen korrekten OCRCandidate baut: tokens befuellt, confidence aus den
    (gestubbten) Generation-Scores abgeleitet statt hartkodiert, markers
    leer."""
    from PIL import Image

    # importlib.import_module() statt dotted-attribute-Import -- siehe
    # Kommentar in test_htr_status_without_model_reports_not_downloaded.
    htr_module = importlib.import_module("teacherassist_core.ocr.engines.htr")

    engine = HtrEngine()
    monkeypatch.setattr(engine, "status", lambda: htr_module.EngineStatus(
        name="htr", kind="htr", available=True, reason="", model_id=engine.model_id, capabilities=engine.capabilities,
    ))
    monkeypatch.setattr(engine, "_load", lambda: (_StubProcessor(), _StubModel(), "cpu"))

    image = Image.new("L", (20, 8), color=255)
    candidate = engine.recognize(image, region_type=RegionType.TEXT_LINE, region_id="p1-r1")

    assert candidate.engine == "htr"
    assert candidate.text == "Ich bin ein Testsatz"
    assert candidate.raw_text == "Ich bin ein Testsatz"
    assert candidate.tokens == ("Ich", "bin", "ein", "Testsatz")
    assert candidate.markers == ()
    # confidence = Mittel von exp(log([.9,.8,.7,.6])) = Mittel von [.9,.8,.7,.6]
    assert candidate.confidence == pytest.approx(0.75, abs=1e-6)
    # Kein hartkodierter Platzhalterwert wie 0.9.
    assert candidate.confidence != 0.9
