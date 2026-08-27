"""In-Prozess-Testengine ohne echtes Modell (Stufe 2 des OCR-Refactors).

Anders als tests/-Hilfscode lebt diese Klasse im Produktbaum und wird in
``ENGINE_FACTORIES`` (engines/__init__.py) registriert: sie ist das, womit
die gesamte Konsens-Pipeline (Stufen 4/5) end-to-end smoke-getestet werden
kann, ganz ohne Torch/Tesseract/Ollama. Jeder Test dort haengt an dieser
Datei -- Verhalten hier aendern heisst, Stufen 4/5 mitdenken.
"""

from __future__ import annotations

from typing import Any, Collection, Mapping, Sequence

from ..consensus import tokenize
from ..markup import parse_markup
from ..types import OCRCandidate, RegionType
from .base import EngineError, EngineKind, EngineStatus


class FakeEngine:
    """Deterministische Attrappen-Engine fuer Tests und Smoke-Runs.

    `texts` bestimmt, was recognize() liefert:
      - ``str``: immer genau dieser Text, unabhaengig von Region/Aufrufzahl.
      - ``Mapping[str, str]``: Text wird ueber ``region_id`` (Teil des
        OCREngine-Protocol selbst, siehe base.py -- keine FakeEngine-
        spezifische Erweiterung) nachgeschlagen (Schluessel = Region-ID).
      - ``Sequence[str]``: wird der Reihe nach ueber aufeinanderfolgende
        recognize()-Aufrufe konsumiert (via call_count, mit Wraparound).
    """

    def __init__(
        self,
        name: str,
        texts: Mapping[str, str] | Sequence[str] | str,
        *,
        confidence: float = 0.9,
        available: bool = True,
        fail_with: str | None = None,
        kind: EngineKind = "fake",
        latency_ms: int = 0,
        supported_types: Collection[RegionType] | None = None,
    ) -> None:
        self.name = name
        self.kind: EngineKind = kind
        self.capabilities: Mapping[str, bool] = {
            "cpu": True,
            "cuda": False,
            "vulkan": False,
            "xpu": False,
            "rocm": False,
        }
        self._texts = texts
        self.confidence = confidence
        self._available = available
        self.fail_with = fail_with
        self.latency_ms = latency_ms
        self._supported_types = set(supported_types) if supported_types is not None else None
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    def status(self) -> EngineStatus:
        return EngineStatus(
            name=self.name,
            kind=self.kind,
            available=self._available,
            reason="" if self._available else "fake_unavailable",
            model_id=self.name,
            capabilities=self.capabilities,
        )

    def supports(self, region_type: RegionType) -> bool:
        if self._supported_types is None:
            return True
        return region_type in self._supported_types

    def recognize(
        self,
        image: Any,
        *,
        region_type: RegionType,
        language: str = "deu",
        region_id: str | None = None,
    ) -> OCRCandidate:
        self.call_count += 1
        if self.fail_with:
            # Genau der Mechanismus, der eine "HTR-Engine ist fehlgeschlagen,
            # darf NICHT still auf Tesseract zurueckfallen"-Pipeline-Regel
            # testbar macht -- niemals einen leeren/geratenen Kandidaten.
            raise EngineError(self.name, self.fail_with)

        raw_text = self._resolve_text(region_id)
        # Wie eine echte Engine: Markup ((<uncertain>...</uncertain>) etc.)
        # wird aufgeloest, damit dieselben Konsens-Tests gegen FakeEngine
        # laufen koennen wie gegen ein echtes Modell.
        parsed = parse_markup(raw_text)
        tokens, _ = tokenize(parsed.text)

        return OCRCandidate(
            engine=self.name,
            text=parsed.text,
            raw_text=raw_text,
            confidence=self.confidence,
            tokens=tokens,
            token_confidences=tuple(self.confidence for _ in tokens),
            duration_ms=self.latency_ms,
            markers=parsed.markers,
        )

    def warmup(self) -> None:
        return None

    def _resolve_text(self, region_id: str | None) -> str:
        texts = self._texts
        if isinstance(texts, str):
            return texts
        if isinstance(texts, Mapping):
            if region_id is None or region_id not in texts:
                raise EngineError(self.name, f"no_text_for_region:{region_id}")
            return texts[region_id]
        # Sequenz-Form: der Reihe nach ueber aufeinanderfolgende Aufrufe
        # konsumiert. call_count wurde bereits inkrementiert (1-basiert),
        # daher -1; Wraparound haelt wiederholte Aufrufe deterministisch
        # statt mit IndexError abzubrechen.
        sequence = texts
        if not sequence:
            raise EngineError(self.name, "no_texts_configured")
        index = (self.call_count - 1) % len(sequence)
        return sequence[index]
