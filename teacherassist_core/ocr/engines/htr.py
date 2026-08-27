"""HTR-Engine (Handschrifterkennung) ueber TrOCR/transformers (Stufe 6).

Schwere Importe (torch, transformers, PIL, huggingface_hub) bleiben
ausschliesslich innerhalb von Methoden -- siehe engines/__init__.py fuer den
Lazy-Import-Vertrag dieses Pakets. is_available()/status() pruefen nur ueber
importlib.util.find_spec (Abhaengigkeiten) bzw.
huggingface_hub.try_to_load_from_cache (Gewichte im HF-Cache) -- nie ueber
einen echten Import oder gar from_pretrained().

TrOCR ist ein Ein-Zeilen-Modell: unterstuetzt wird ausschliesslich
RegionType.TEXT_LINE. Ein ganzer Absatz oder eine Seite wuerde selbstbewussten
Unsinn statt eines erkennbaren Fehlers produzieren -- fuer dieses Projekt der
schlimmstmoegliche Fehlerfall (eine Lehrkraft koennte den Text fuer korrekt
erkannt halten).

Lizenzhinweis: Das Default-Modell fhswf/TrOCR_german_handwritten steht unter
AFL-3.0 (abweichend von der Lizenz des uebrigen Projekts). Gemeldete CER
liegt bei ca. 4.1% -- gut genug als zweiter Leser in der Konsens-Pipeline,
nicht gut genug, um allein vertraut zu werden. Genau diese Rolle gibt die
Architektur (consensus.py, Stufe 4) der Engine.

Der Modell-Download (~1.3 GB) wird NIEMALS implizit aus recognize()/warmup()
ausgeloest -- status() muss "verfuegbar" melden (Gewichte im Cache), bevor
_load() etwas anfasst; local_files_only=True in _load() ist die zweite
Absicherung. Der einzige Download-Trigger ist der explizite, von der
Lehrkraft gestartete Endpoint POST /api/v1/ocr/models/download in
tool_server.py.
"""

from __future__ import annotations

import importlib.util
import logging
import threading
from typing import Any, Mapping

from ..consensus import tokenize
from ..types import OCRCandidate, RegionType
from .base import EngineError, EngineKind, EngineStatus

logger = logging.getLogger(__name__)

DEFAULT_HTR_MODEL = "fhswf/TrOCR_german_handwritten"

# Deckelt die Generation, damit ein degenerierter Wiederholungs-Loop des
# Modells keinen Worker-Thread aufhaengen kann (eine einzelne Textzeile
# braucht in der Praxis weit weniger Tokens).
_MAX_NEW_TOKENS = 64

# Modell-Cache ueber alle HtrEngine-Instanzen hinweg (Schluessel: model_id +
# aufgeloestes Device), geschuetzt durch _MODEL_LOCK -- so laedt der erste
# recognize()/warmup()-Aufruf das Modell genau einmal, auch bei mehreren
# Instanzen mit identischer Konfiguration.
_MODEL_CACHE: dict[tuple[str, str], tuple[Any, Any]] = {}
_MODEL_LOCK = threading.Lock()


def _region_suffix(region_id: str | None) -> str:
    """Wie tesseract.py:_region_suffix -- region_id ist rein advisory
    (siehe base.OCREngine.recognize), wird aber an Fehlermeldung und Log
    angehaengt, damit ein Fehlschlag sagt, welche Region betroffen war."""
    return f":region={region_id}" if region_id else ""


def _deps_available() -> bool:
    # Wie tesseract.py:_deps_available -- find_spec() kann in seltenen
    # Faellen (sys.meta_path-Blocker in Tests) werfen statt None
    # zurueckzugeben; das darf is_available()/status() nie hochreissen.
    try:
        return (
            importlib.util.find_spec("torch") is not None
            and importlib.util.find_spec("transformers") is not None
        )
    except Exception:
        return False


def _weights_cached(model_id: str) -> bool:
    """Prueft rein lokal (kein Netzwerk), ob die Modellgewichte bereits im
    HF-Cache liegen. huggingface_hub selbst ist keine "schwere" Abhaengigkeit
    im Sinne des Lazy-Import-Vertrags (siehe engines/__init__.py) und bereits
    ueber sentence-transformers installiert -- der Import bleibt trotzdem
    innerhalb der Funktion, nie auf Modulebene."""
    try:
        from huggingface_hub import try_to_load_from_cache

        for filename in ("model.safetensors", "pytorch_model.bin"):
            if isinstance(try_to_load_from_cache(model_id, filename), str):
                return True
        return False
    except Exception:
        return False


def _resolve_device(device: str) -> str:
    """Loest "auto" erst hier auf (nie beim Import/Konstruktor) -- cuda,
    wenn torch.cuda.is_available(), sonst cpu. "cpu"/"cuda" erzwingen das
    jeweilige Device ohne Pruefung."""
    if device == "cpu":
        return "cpu"
    if device == "cuda":
        return "cuda"
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _mean_token_probability(model: Any, outputs: Any) -> float:
    """Mittlere Token-Wahrscheinlichkeit ueber die generierte Sequenz -- eine
    echte, aus den Generation-Scores abgeleitete Zahl, kein hartkodierter
    Wert. model.compute_transition_scores(..., normalize_logits=True)
    liefert Log-Softmax-Wahrscheinlichkeiten pro erzeugtem Token (nicht die
    Roh-Logits); Positionen nach dem EOS-Token sind nicht endlich (-inf) und
    werden vor der Mittelung ausmaskiert. Das ist kein kalibriertes
    Konfidenzmass (kein ECE-Fit o.ae.), sondern genau das: der geometrische
    Mittelwert der vom Modell selbst vergebenen Token-Wahrscheinlichkeiten."""
    import torch

    scores = getattr(outputs, "scores", None)
    if not scores:
        return 0.0
    transition_scores = model.compute_transition_scores(
        outputs.sequences, scores, normalize_logits=True
    )
    finite_mask = torch.isfinite(transition_scores)
    if not bool(finite_mask.any()):
        return 0.0
    probs = transition_scores[finite_mask].exp()
    return float(probs.mean().item())


class HtrEngine:
    name = "htr"
    kind: EngineKind = "htr"
    capabilities: Mapping[str, bool] = {
        "cpu": True,
        "cuda": True,
        "vulkan": False,
        "xpu": False,
        "rocm": False,
    }

    def __init__(self, model_id: str = DEFAULT_HTR_MODEL, device: str = "auto") -> None:
        self.model_id = model_id
        self.device = device

    def is_available(self) -> bool:
        return _deps_available()

    def status(self) -> EngineStatus:
        if not _deps_available():
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason="not_installed:torch|transformers",
                model_id=self.model_id,
                capabilities=self.capabilities,
            )
        if not _weights_cached(self.model_id):
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason=f"model_not_downloaded:{self.model_id}",
                model_id=self.model_id,
                capabilities=self.capabilities,
            )
        return EngineStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            reason="",
            model_id=self.model_id,
            capabilities=self.capabilities,
        )

    def supports(self, region_type: RegionType) -> bool:
        return region_type is RegionType.TEXT_LINE

    def recognize(
        self,
        image: Any,
        *,
        region_type: RegionType,
        language: str = "deu",
        region_id: str | None = None,
    ) -> OCRCandidate:
        if region_type is not RegionType.TEXT_LINE:
            reason = f"unsupported_region_type:{region_type.value}{_region_suffix(region_id)}"
            logger.warning(
                "HTR unterstuetzt nur TEXT_LINE, erhalten: %s (Region %s)",
                region_type.value, region_id or "?",
            )
            raise EngineError(self.name, reason)

        status = self.status()
        if not status.available:
            reason = f"{status.reason}{_region_suffix(region_id)}"
            logger.warning(
                "HTR nicht verfuegbar (%s, Region %s)", status.reason, region_id or "?"
            )
            raise EngineError(self.name, reason)

        try:
            processor, model, device = self._load()
        except Exception as exc:
            reason = f"model_load_failed:{exc}{_region_suffix(region_id)}"
            logger.warning(
                "HTR-Modell konnte nicht geladen werden (Region %s): %s", region_id or "?", exc
            )
            raise EngineError(self.name, reason) from exc

        try:
            import torch
            from PIL import Image

            start = _now_ms()
            pil_image = image if isinstance(image, Image.Image) else Image.open(image)
            pil_image = pil_image.convert("RGB")
            pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values.to(device)
            with torch.inference_mode():
                outputs = model.generate(
                    pixel_values,
                    max_new_tokens=_MAX_NEW_TOKENS,
                    output_scores=True,
                    return_dict_in_generate=True,
                )
            text = processor.batch_decode(outputs.sequences, skip_special_tokens=True)[0].strip()
            confidence = _mean_token_probability(model, outputs)
            duration_ms = _now_ms() - start
        except Exception as exc:
            reason = f"recognize_failed:{exc}{_region_suffix(region_id)}"
            logger.warning(
                "HTR-Erkennung fehlgeschlagen (Region %s): %s", region_id or "?", exc
            )
            raise EngineError(self.name, reason) from exc

        tokens, _ = tokenize(text)

        return OCRCandidate(
            engine=self.name,
            text=text,
            raw_text=text,
            confidence=confidence,
            tokens=tokens,
            # TrOCR erzeugt Subword-Tokens; die lassen sich nicht verlustfrei
            # auf die wortweisen tokenize()-Tokens abbilden. Statt eine
            # falsche Zuordnung zu erfinden, bleibt token_confidences leer --
            # `confidence` oben ist die einzige belastbare Zahl (siehe
            # _mean_token_probability).
            token_confidences=(),
            duration_ms=duration_ms,
            markers=(),
        )

    def warmup(self) -> None:
        # Warmup laedt NUR, wenn die Gewichte bereits im Cache liegen --
        # loest nie einen Download aus (siehe Moduldoc).
        if not self.status().available:
            return
        try:
            self._load()
        except Exception:
            logger.warning("HTR-Warmup fehlgeschlagen (Modell %s)", self.model_id)

    def _load(self) -> tuple[Any, Any, str]:
        device = _resolve_device(self.device)
        cache_key = (self.model_id, device)
        with _MODEL_LOCK:
            cached = _MODEL_CACHE.get(cache_key)
            if cached is not None:
                processor, model = cached
                return processor, model, device

            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            # local_files_only=True ist die zweite Absicherung gegen einen
            # impliziten Download (die erste ist die status()-Pruefung oben
            # in recognize()): selbst wenn dieser Codepfad je ohne
            # vorherige Pruefung erreicht wuerde, versucht from_pretrained()
            # keinen Netzwerkzugriff, sondern schlaegt lokal fehl.
            processor = TrOCRProcessor.from_pretrained(self.model_id, local_files_only=True)
            model = VisionEncoderDecoderModel.from_pretrained(self.model_id, local_files_only=True)
            model.eval()
            model.to(device)
            _MODEL_CACHE[cache_key] = (processor, model)
            return processor, model, device


def _now_ms() -> int:
    import time

    return int(time.monotonic() * 1000)


__all__ = ["HtrEngine", "DEFAULT_HTR_MODEL"]
