"""OCR-Engine-Registry (Stufe 2 des OCR-Refactors).

LAZY-IMPORT-VERTRAG: Dieses Paket (und jedes Modul darin) darf beim reinen
`import teacherassist_core.ocr.engines` KEINE schweren Abhaengigkeiten
importieren -- namentlich nicht torch, transformers, pytesseract, PIL,
paddle oder numpy. `is_available()` prueft nur ueber
`importlib.util.find_spec(...)`, niemals per echtem Import. Jeder echte
Import einer schweren Bibliothek gehoert ausschliesslich in den Koerper von
`recognize()`/`warmup()` einer konkreten Engine, nie auf Modulebene. Wer
hier spaeter `import torch` o.ae. an den Dateikopf setzt, bricht sowohl den
schnellen Bootstrap-Pfad (tool_server.py importiert dieses Paket bei jedem
Serverstart) als auch tests/test_ocr_engines.py::
test_engines_import_without_heavy_deps, das genau das mit einem
sys.meta_path-Blocker erzwingt.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Sequence

from .base import EngineError, EngineKind, EngineStatus, OCREngine
from .fake import FakeEngine
from .htr import DEFAULT_HTR_MODEL, HtrEngine
from .ollama_vlm import DEFAULT_TIMEOUT_S, DEFAULT_VISION_MODEL, OllamaVlmEngine
from .paddleocr_vl import BACKEND_AUTO, DEFAULT_PADDLE_MODEL, PaddleOcrVlEngine
from .tesseract import TesseractEngine

logger = logging.getLogger(__name__)

ENGINE_FACTORIES: dict[str, Callable[[Mapping[str, Any]], OCREngine]] = {
    "tesseract": lambda settings: TesseractEngine(),
    "fake": lambda settings: FakeEngine("fake", settings.get("fakeOcrTexts", "")),
    "htr": lambda settings: HtrEngine(
        model_id=settings.get("ocrHtrModel") or DEFAULT_HTR_MODEL,
        device=settings.get("ocrDevice") or "auto",
    ),
    "ollama_vlm": lambda settings: OllamaVlmEngine(
        model_id=settings.get("ocrVisionModel") or DEFAULT_VISION_MODEL,
        # "classification" kommt nicht aus einer Nutzer-Einstellung, sondern
        # wird von den build_engines()-Aufrufstellen (tool_server.py) aus der
        # bereits fuer PipelineConfig aufgeloesten Klassifikation in die hier
        # uebergebene settings-Mapping eingemischt -- siehe deren Docstrings.
        # Default "student_submission" ist die restriktivste Klassifikation
        # (Cloud-Zugriff verboten), falls settings sie nicht mitbringt.
        classification=settings.get("classification") or "student_submission",
        timeout_s=int(settings.get("ocrVlmTimeoutS") or DEFAULT_TIMEOUT_S),
    ),
    "paddleocr_vl": lambda settings: PaddleOcrVlEngine(
        model_id=settings.get("ocrPaddleModel") or DEFAULT_PADDLE_MODEL,
        backend=settings.get("ocrPaddleBackend") or BACKEND_AUTO,
        device=settings.get("ocrDevice") or "auto",
        classification=settings.get("classification") or "student_submission",
    ),
}
# "htr"/"ollama_vlm"/"paddleocr_vl" sind absichtlich NICHT in DEFAULT_ENGINES:
# ein nicht heruntergeladenes/gepulltes Modell darf keinen Job
# standardmaessig degradieren (engine_failure-Eintrag fuer jede Region) --
# die Settings-UI (Stufe 9) schaltet sie bewusst frei. Fuer paddleocr_vl
# kommt hinzu, dass in dieser Stufe bewusst KEINE der beiden konkurrierenden
# Abhaengigkeiten (paddlepaddle/paddleocr[doc-parser] vs. transformers>=5)
# installiert wird -- siehe engines/paddleocr_vl.py Moduldoc und
# tools/requirements-ocr-paddle.txt.
DEFAULT_ENGINES: tuple[str, ...] = ("tesseract",)


def build_engines(settings: Mapping[str, Any], names: Sequence[str] | None = None) -> list[OCREngine]:
    """Baut Engine-Instanzen fuer `names` (Default: settings['ocrEngines']
    oder DEFAULT_ENGINES). Unbekannte Namen werden geloggt und uebersprungen,
    nie hart abgebrochen. Filtert NICHT nach Verfuegbarkeit -- die Pipeline
    muss eine nicht verfuegbare Engine sehen koennen, um einen
    engine_failure-Eintrag zu erzeugen (siehe types.PageResult.engine_failures)."""
    if names is None:
        configured = settings.get("ocrEngines")
        names = configured if configured else DEFAULT_ENGINES

    engines: list[OCREngine] = []
    for name in names:
        factory = ENGINE_FACTORIES.get(name)
        if factory is None:
            logger.warning("Unbekannter OCR-Engine-Name in Einstellungen ignoriert: %s", name)
            continue
        engines.append(factory(settings))
    return engines


def available_engines(settings: Mapping[str, Any]) -> list[EngineStatus]:
    """Reichhaltiger Statusbericht (mit `reason`) fuer die gemaess `settings`
    konfigurierten Engines -- die Grundlage fuer die Download-UX in Stufe 9."""
    return [engine.status() for engine in build_engines(settings)]


def ocr_capability_status(settings: Mapping[str, Any]) -> dict[str, bool]:
    """Flache bool-Map fuer /api/v1/bootstrap (siehe tool_server.py).

    `settings` ist bewusst Teil der Signatur: htr/vlm/paddle werten sie
    ueber ihre jeweilige ENGINE_FACTORIES-Fabrik aus. htr/vlm/paddle
    spiegeln den echten Status wider (Abhaengigkeiten UND
    heruntergeladenes/gepulltes Modell, siehe engines/htr.py:HtrEngine.status,
    engines/ollama_vlm.py:OllamaVlmEngine.status -- prueft nur /api/tags,
    loest nie einen Pull aus -- bzw.
    engines/paddleocr_vl.py:PaddleOcrVlEngine.status). paddle meldet in
    dieser Stufe zuverlaessig False, weil bewusst keine der beiden
    konkurrierenden Abhaengigkeiten installiert ist (siehe
    engines/paddleocr_vl.py Moduldoc) -- das ist der korrekte, nicht ein
    provisorischer Wert."""
    tesseract_available = TesseractEngine().status().available
    htr_available = ENGINE_FACTORIES["htr"](settings).status().available
    vlm_available = ENGINE_FACTORIES["ollama_vlm"](settings).status().available
    paddle_available = ENGINE_FACTORIES["paddleocr_vl"](settings).status().available

    flags: dict[str, bool] = {
        "ocrTesseract": tesseract_available,
        "ocrHtr": htr_available,
        "ocrVlm": vlm_available,
        "ocrPaddle": paddle_available,
    }
    flags["ocrConsensus"] = sum(1 for available in flags.values() if available) >= 2
    return flags


__all__ = [
    "EngineError",
    "EngineKind",
    "EngineStatus",
    "OCREngine",
    "FakeEngine",
    "TesseractEngine",
    "HtrEngine",
    "DEFAULT_HTR_MODEL",
    "OllamaVlmEngine",
    "DEFAULT_VISION_MODEL",
    "PaddleOcrVlEngine",
    "DEFAULT_PADDLE_MODEL",
    "ENGINE_FACTORIES",
    "DEFAULT_ENGINES",
    "build_engines",
    "available_engines",
    "ocr_capability_status",
]
