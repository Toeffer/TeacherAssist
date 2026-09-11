"""Reine, abhaengigkeitsfreie OCR-Konsens-Kernlogik (Stufe 1 des OCR-Refactors).

Dieses Paket darf NUR aus der Standardbibliothek importieren (siehe die
einzelnen Module). `import teacherassist_core.ocr` muss in wenigen
Millisekunden abgeschlossen sein -- daher hier bewusst nur billige
Re-Exports, keine weitere Logik.
"""

from __future__ import annotations

from .consensus import (
    ENGINE_PRIORITY,
    MERGE_GAP,
    AlignmentOp,
    align,
    build_region,
    collect_disagreements,
    decide_status,
    normalize_token,
    pick_reference,
    render_consensus,
    render_consensus_with_offsets,
    tokenize,
)
from .engines import (
    DEFAULT_ENGINES,
    DEFAULT_HTR_MODEL,
    ENGINE_FACTORIES,
    EngineError,
    EngineStatus,
    FakeEngine,
    HtrEngine,
    OCREngine,
    TesseractEngine,
    available_engines,
    build_engines,
    ocr_capability_status,
)
from .critical_tokens import (
    CRITICAL_SYMBOLS,
    CRITICAL_WORDS,
    SI_PREFIX_CONFUSIONS,
    SUBJECT_TOKENS,
    UNIT_TOKENS,
    CriticalTokenConfig,
    classify_span,
    load_overrides,
    numeric_values,
    unit_tokens,
)
from .gate import GRADING_SKILLS, GateDecision, evaluate_grading_gate
from .markup import UNCLEAR_SENTINEL, ParsedMarkup, parse_markup
from .pipeline import (
    OCRBusy,
    PipelineConfig,
    process_document,
    process_page,
    process_pages,
    process_single_image_sync,
    process_student_pdf,
)
from .privacy_guard import CloudBlocked, assert_local_only
from .prompts import FORMULA_PROMPT_DE, VERBATIM_PROMPT_DE, VERBATIM_PROMPT_VERSION
from .pseudonyms import Pseudonym, PseudonymMap
from .store import (
    ApprovalNotReady,
    ApprovalRefused,
    CLOUD_BLOCKED_ERROR_CODE,
    DeletionCleanupFailed,
    EmptyPatchError,
    OCRJobStore,
)
from .types import (
    DocumentResult,
    Disagreement,
    ImageQuality,
    OCRCandidate,
    OCRStatus,
    PageResult,
    Region,
    RegionType,
)

__all__ = [
    "DEFAULT_ENGINES",
    "DEFAULT_HTR_MODEL",
    "ENGINE_FACTORIES",
    "EngineError",
    "EngineStatus",
    "FakeEngine",
    "HtrEngine",
    "OCREngine",
    "TesseractEngine",
    "available_engines",
    "build_engines",
    "ocr_capability_status",
    "ENGINE_PRIORITY",
    "MERGE_GAP",
    "AlignmentOp",
    "align",
    "build_region",
    "collect_disagreements",
    "decide_status",
    "normalize_token",
    "pick_reference",
    "render_consensus",
    "render_consensus_with_offsets",
    "tokenize",
    "CRITICAL_SYMBOLS",
    "CRITICAL_WORDS",
    "SI_PREFIX_CONFUSIONS",
    "SUBJECT_TOKENS",
    "UNIT_TOKENS",
    "CriticalTokenConfig",
    "classify_span",
    "load_overrides",
    "numeric_values",
    "unit_tokens",
    "UNCLEAR_SENTINEL",
    "ParsedMarkup",
    "parse_markup",
    "FORMULA_PROMPT_DE",
    "VERBATIM_PROMPT_DE",
    "VERBATIM_PROMPT_VERSION",
    "GRADING_SKILLS",
    "GateDecision",
    "evaluate_grading_gate",
    "PipelineConfig",
    "OCRBusy",
    "process_document",
    "process_page",
    "process_pages",
    "process_single_image_sync",
    "process_student_pdf",
    "CloudBlocked",
    "assert_local_only",
    "Pseudonym",
    "PseudonymMap",
    "ApprovalNotReady",
    "ApprovalRefused",
    "CLOUD_BLOCKED_ERROR_CODE",
    "DeletionCleanupFailed",
    "EmptyPatchError",
    "OCRJobStore",
    "DocumentResult",
    "Disagreement",
    "ImageQuality",
    "OCRCandidate",
    "OCRStatus",
    "PageResult",
    "Region",
    "RegionType",
]
