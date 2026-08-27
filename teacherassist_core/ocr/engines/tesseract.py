"""Tesseract-Engine: Druckschrift-OCR ueber pytesseract (Stufe 2).

Schwere Importe (pytesseract, PIL) bleiben ausschliesslich innerhalb von
Methoden -- siehe engines/__init__.py fuer den Lazy-Import-Vertrag dieses
Pakets. is_available()/status() pruefen nur ueber importlib.util.find_spec
bzw. teacherassist_core.tesseract_setup (Stufe 0, selbst ohne schwere
Top-Level-Importe), nie ueber einen echten Import.
"""

from __future__ import annotations

import importlib.util
import logging
from typing import Any, Mapping

from ... import tesseract_setup
from ...tesseract_setup import configure_pytesseract, tesseract_binary
from ..types import OCRCandidate, RegionType
from .base import EngineError, EngineKind, EngineStatus

logger = logging.getLogger(__name__)

_SUPPORTED_TYPES = frozenset(
    {RegionType.TEXT_LINE, RegionType.PARAGRAPH, RegionType.HEADER, RegionType.TABLE}
)


def _region_suffix(region_id: str | None) -> str:
    """`region_id` ist rein advisory (siehe base.OCREngine.recognize) --
    diese Engine hat sonst keine Verwendung dafuer, haengt es aber an
    Fehlermeldung und Log an, damit ein Fehlschlag sagt, welche Region
    betroffen war."""
    return f":region={region_id}" if region_id else ""


def _deps_available() -> bool:
    # Wie runtime.capability_status()'s available()-Helfer: find_spec() kann
    # in seltenen Faellen (z.B. der sys.meta_path-Blocker in
    # tests/test_ocr_engines.py::test_engines_import_without_heavy_deps)
    # werfen statt None zurueckzugeben -- das darf is_available()/status()
    # nie hochreissen, sondern muss als "nicht verfuegbar" gelten.
    try:
        return (
            importlib.util.find_spec("pytesseract") is not None
            and importlib.util.find_spec("PIL") is not None
        )
    except Exception:
        return False


class TesseractEngine:
    name = "tesseract"
    kind: EngineKind = "print"
    capabilities: Mapping[str, bool] = {
        "cpu": True,
        "cuda": False,
        "vulkan": False,
        "xpu": False,
        "rocm": False,
    }

    def is_available(self) -> bool:
        return _deps_available()

    def status(self) -> EngineStatus:
        if not _deps_available():
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason="not_installed:pytesseract|PIL",
                model_id=self.name,
                capabilities=self.capabilities,
            )
        if tesseract_setup.tesseract_binary() is None:
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason="binary_not_found:tesseract",
                model_id=self.name,
                capabilities=self.capabilities,
            )
        return EngineStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            reason="",
            model_id=self.name,
            capabilities=self.capabilities,
        )

    def supports(self, region_type: RegionType) -> bool:
        return region_type in _SUPPORTED_TYPES

    def recognize(
        self,
        image: Any,
        *,
        region_type: RegionType,
        language: str = "deu",
        region_id: str | None = None,
    ) -> OCRCandidate:
        if not _deps_available():
            reason = f"not_installed:pytesseract|PIL{_region_suffix(region_id)}"
            logger.warning("Tesseract-Abhaengigkeiten fehlen (Region %s)", region_id or "?")
            raise EngineError(self.name, reason)
        if not tesseract_setup.configure_pytesseract():
            reason = f"binary_not_found:tesseract{_region_suffix(region_id)}"
            logger.warning("Tesseract-Binary nicht gefunden (Region %s)", region_id or "?")
            raise EngineError(self.name, reason)

        try:
            import pytesseract
            from pytesseract import Output

            start = _now_ms()
            data = pytesseract.image_to_data(image, lang=language, output_type=Output.DICT)
            duration_ms = _now_ms() - start
        except Exception as exc:  # pragma: no cover - defensive, exercised via fail_with-style tests
            logger.warning("Tesseract-Erkennung fehlgeschlagen (Region %s): %s", region_id or "?", exc)
            raise EngineError(self.name, f"recognize_failed:{exc}{_region_suffix(region_id)}") from exc

        tokens: list[str] = []
        token_confidences: list[float] = []
        for text, conf in zip(data.get("text", ()), data.get("conf", ())):
            word = text.strip()
            if not word:
                continue
            try:
                conf_value = float(conf)
            except (TypeError, ValueError):
                continue
            if conf_value < 0:
                continue
            tokens.append(word)
            token_confidences.append(conf_value / 100.0)

        overall_confidence = (
            sum(token_confidences) / len(token_confidences) if token_confidences else 0.0
        )
        raw_text = " ".join(tokens)

        return OCRCandidate(
            engine=self.name,
            text=raw_text,
            raw_text=raw_text,
            confidence=overall_confidence,
            tokens=tuple(tokens),
            token_confidences=tuple(token_confidences),
            duration_ms=duration_ms,
            markers=(),
        )

    def warmup(self) -> None:
        tesseract_setup.configure_pytesseract()


def _now_ms() -> int:
    import time

    return int(time.monotonic() * 1000)


__all__ = ["TesseractEngine", "tesseract_binary", "configure_pytesseract"]
