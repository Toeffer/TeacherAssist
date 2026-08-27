"""Gemeinsame Typen fuer OCR-Engines (Stufe 2 des OCR-Refactors).

Dieses Modul bleibt bewusst frei von schweren Abhaengigkeiten -- es
definiert nur das ``OCREngine``-Protocol sowie ``EngineStatus``/
``EngineError``, gegen die alle konkreten Engines (fake.py, tesseract.py,
spaeter htr.py/ollama_vlm.py/paddleocr_vl.py) implementieren. Siehe
teacherassist_core/ocr/engines/__init__.py fuer den Lazy-Import-Vertrag,
den diese Engines einhalten muessen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Mapping, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..types import OCRCandidate, RegionType

EngineKind = Literal["print", "htr", "vlm", "layout", "fake"]


@dataclass(frozen=True)
class EngineStatus:
    name: str
    kind: EngineKind
    available: bool
    # Leer, wenn available True ist; sonst maschinenlesbar, z.B.
    # "not_installed:torch|transformers", "binary_not_found:tesseract",
    # "model_not_downloaded:<id>", "model_not_pulled:<id>", "ollama_offline".
    reason: str
    model_id: str
    capabilities: Mapping[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "available": self.available,
            "reason": self.reason,
            "modelId": self.model_id,
            "capabilities": dict(self.capabilities),
        }


class EngineError(RuntimeError):
    """Wird von OCREngine.recognize() bei jedem Fehlschlag geworfen -- eine
    fehlgeschlagene Engine liefert NIE stillschweigend einen leeren oder
    geratenen Kandidaten zurueck (siehe engines/fake.py fail_with)."""

    def __init__(self, engine: str, reason: str) -> None:
        self.engine = engine
        self.reason = reason
        super().__init__(f"{engine}: {reason}")


@runtime_checkable
class OCREngine(Protocol):
    name: str
    kind: EngineKind
    capabilities: Mapping[str, bool]

    def is_available(self) -> bool:
        """Billige Pruefung, ob die noetigen Python-Abhaengigkeiten
        importierbar sind. Fuehrt keine Modell-/Netzwerk-Pruefung durch."""
        ...

    def status(self) -> EngineStatus:
        """Reichhaltigere Antwort als is_available(): unterscheidet u.a.
        "installiert, aber Modell noch nicht heruntergeladen" -- diese
        Unterscheidung treibt die Download-UX in Stufe 9."""
        ...

    def supports(self, region_type: "RegionType") -> bool:
        ...

    def recognize(
        self,
        image: Any,
        *,
        region_type: "RegionType",
        language: str = "deu",
        region_id: str | None = None,
    ) -> "OCRCandidate":
        """`region_id` (e.g. ``"p{page}-r{n}"`` from segmentation.segment_page)
        is advisory context, not a required input: the pipeline always passes
        it, but every engine must work correctly when it is None (e.g. called
        outside the full pipeline). Engines may use it for logging, caching,
        or per-region prompts -- FakeEngine uses it to key its mapping-form
        `texts`; TesseractEngine has no use for it beyond error/log context."""
        ...

    def warmup(self) -> None:
        """Optionales Vorwaermen (z.B. Modell laden). Default: no-op.

        Konkrete Engines koennen von diesem Protocol erben, um diese
        Default-Implementierung zu erhalten, statt sie selbst zu
        wiederholen (siehe engines/fake.py, engines/tesseract.py)."""
        return None
