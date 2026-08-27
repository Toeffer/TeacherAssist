"""Reine Datenstrukturen fuer die OCR-Konsenspipeline.

Dieses Modul ist bewusst frei von schweren Abhaengigkeiten (siehe
teacherassist_core/ocr/__init__.py). Es definiert nur Enums, Dataclasses
und deren JSON-Serialisierung.

``DocumentResult.to_dict()`` ist der Sicherheits-Dreh- und Angelpunkt der
gesamten OCR-Pipeline: ob der volltext ("text"/"selectedText") an den
Client geht, haengt AUSSCHLIESSLICH vom eigenen ``status`` des Dokuments ab
und wird niemals von aussen als Parameter hereingereicht. Solange eine
Schuelerarbeit nicht von einer Lehrkraft freigegeben wurde (APPROVED), darf
der rohe erkannte Text die Review-UI nicht verlassen -- nur die
Konsens-Markierungen ("[nicht?]" etc.) sind fuer die Review-Ansicht immer
sichtbar.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class OCRStatus(str, Enum):
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"  # entweder explizite Lehrkraft-Aktion (mark_approved) oder,
    # nur fuer nicht-schuelerbezogenes Material, consensus.decide_status() mit
    # ausdruecklich gesetztem auto_approve=True (Settings ocrAutoApproveNonStudent,
    # Default False). classification == "student_submission" gibt NIE automatisch frei.
    FAILED = "failed"


class RegionType(str, Enum):
    TEXT_LINE = "text_line"
    PARAGRAPH = "paragraph"
    FORMULA = "formula"
    TABLE = "table"
    FIGURE = "figure"
    HEADER = "header"


@dataclass(frozen=True)
class OCRCandidate:
    engine: str
    text: str
    raw_text: str
    confidence: float
    tokens: tuple[str, ...]
    token_confidences: tuple[float, ...] = ()
    duration_ms: int = 0
    markers: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        # Kandidatentexte werden IMMER vollstaendig ausgegeben (auch wenn das
        # Dokument insgesamt noch nicht freigegeben ist) -- die Review-UI
        # braucht sie, um Konsens-Abweichungen anzuzeigen und aufzuloesen.
        return {
            "engine": self.engine,
            "text": self.text,
            "rawText": self.raw_text,
            "confidence": self.confidence,
            "tokens": list(self.tokens),
            "tokenConfidences": list(self.token_confidences),
            "durationMs": self.duration_ms,
            "markers": list(self.markers),
        }


@dataclass(frozen=True)
class Disagreement:
    start: int  # halboffener Bereich in Referenz-Tokens
    end: int
    variants: tuple[tuple[str, tuple[str, ...]], ...]  # (Text, Engines, die dies sagten)
    critical: bool
    reason: str  # "critical_word:nicht" | "number" | "unit" | "symbol:+" | "unclear" | "subject:physik" | ""
    # Zeichenbereich (halboffen) der gerenderten "[...]"-Klammer dieser
    # Diskrepanz INNERHALB von Region.consensus_text -- von
    # consensus.render_consensus() (genauer: dessen offset-tragende
    # Hilfsfunktion) beim Bau des Konsenstexts gesetzt. -1/-1 bedeutet
    # "noch nicht gerendert" (z.B. bei einem frisch aus collect_disagreements
    # konstruierten Objekt, bevor render_consensus darueber gelaufen ist).
    # Existiert NUR, damit die Review-UI die Klammer client-seitig per
    # Substring statt per Regex-Scan findet -- ein Regex-Treffer kann nicht
    # zwischen einer synthetisierten Klammer und identisch aussehendem,
    # gedrucktem Text im Original (z.B. "[ja|nein?]" auf einem Pruefungsbogen)
    # unterscheiden. consensus_text selbst bleibt davon unveraendert.
    char_start: int = -1
    char_end: int = -1

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "variants": [
                {"text": text, "engines": list(engines)} for text, engines in self.variants
            ],
            "critical": self.critical,
            "reason": self.reason,
            "charStart": self.char_start,
            "charEnd": self.char_end,
        }


@dataclass
class Region:
    id: str  # "p{page}-r{n}"
    type: RegionType
    bbox: tuple[int, int, int, int]
    candidates: tuple[OCRCandidate, ...]
    reference_engine: str
    consensus_text: str  # mit [nicht?]-Klammern
    selected_text: str
    disagreements: tuple[Disagreement, ...]
    agreement: float
    status: OCRStatus
    edited_by_teacher: bool = False
    # True, wenn diese Region fuer die selektive zweite Lesung (siehe
    # pipeline.py: "selective second reading") ausgewaehlt wurde, aber JEDE
    # dafuer vorgesehene Verifikations-Engine mit EngineError fehlgeschlagen
    # ist -- die Region blieb dann beim reinen Bulk-Ergebnis. Ohne diesen
    # Marker ist "verifiziert, sauber befunden" nicht von "Verifikation
    # versucht und fehlgeschlagen" unterscheidbar (siehe Auftrag). IMMER
    # (unconditionally) ausgegeben, wie editedByTeacher -- Diagnose-Metadaten,
    # kein Transkriptinhalt.
    verify_failed: bool = False

    @property
    def has_critical_uncertainty(self) -> bool:
        return any(d.critical for d in self.disagreements)

    def to_dict(self, *, include_text: bool) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "bbox": list(self.bbox),
            "candidates": [c.to_dict() for c in self.candidates],
            "referenceEngine": self.reference_engine,
            # consensusText traegt nur die sichtbaren [...]-Markierungen,
            # niemals den vollen Rohtext -- daher immer sichtbar.
            "consensusText": self.consensus_text,
            "selectedText": self.selected_text if include_text else None,
            "disagreements": [d.to_dict() for d in self.disagreements],
            "agreement": self.agreement,
            "status": self.status.value,
            "editedByTeacher": self.edited_by_teacher,
            "verifyFailed": self.verify_failed,
        }


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    estimated_dpi: float | None
    blur_score: float
    contrast: float
    brightness: float
    skew_degrees: float
    glare_ratio: float
    issues: tuple[str, ...]  # too_blurry|too_dark|too_bright|low_contrast|skewed|glare|too_small
    blocking: bool
    score: float

    @classmethod
    def unknown(cls, width: int, height: int) -> "ImageQuality":
        """Neutrale, nicht-blockierende Instanz fuer Zeiten, in denen die
        eigentliche Bildqualitaetsmessung (Stufe 3) noch nicht existiert.
        So kann die Pipeline schon vorher gegen echte ImageQuality-Objekte
        getestet werden."""
        return cls(
            width=width,
            height=height,
            estimated_dpi=None,
            blur_score=0.0,
            contrast=0.0,
            brightness=0.0,
            skew_degrees=0.0,
            glare_ratio=0.0,
            issues=(),
            blocking=False,
            score=1.0,
        )

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "estimatedDpi": self.estimated_dpi,
            "blurScore": self.blur_score,
            "contrast": self.contrast,
            "brightness": self.brightness,
            "skewDegrees": self.skew_degrees,
            "glareRatio": self.glare_ratio,
            "issues": list(self.issues),
            "blocking": self.blocking,
            "score": self.score,
        }


@dataclass
class PageResult:
    index: int
    width: int
    height: int
    quality: ImageQuality
    regions: tuple[Region, ...]
    status: OCRStatus
    auto_clean: bool
    engine_failures: tuple[tuple[str, str], ...]  # (engine, reason)
    status_reasons: tuple[str, ...] = ()

    @property
    def has_critical_uncertainty(self) -> bool:
        return any(r.has_critical_uncertainty for r in self.regions)

    @property
    def text(self) -> str:
        """Zusammengefuegter, ausgewaehlter (ggf. lehrerkorrigierter) Text."""
        return "\n".join(r.selected_text for r in self.regions)

    @property
    def consensus_text(self) -> str:
        """Zusammengefuegter Konsenstext inkl. [...]-Markierungen."""
        return "\n".join(r.consensus_text for r in self.regions)

    def to_dict(self, *, include_text: bool) -> dict:
        return {
            "index": self.index,
            "width": self.width,
            "height": self.height,
            "quality": self.quality.to_dict(),
            "regions": [r.to_dict(include_text=include_text) for r in self.regions],
            "status": self.status.value,
            "autoClean": self.auto_clean,
            "engineFailures": [
                {"engine": engine, "reason": reason} for engine, reason in self.engine_failures
            ],
            "statusReasons": list(self.status_reasons),
            # "text" ist der ausgewaehlte Volltext und wird -- wie bei
            # Region.selectedText -- erst nach Freigabe ausgeliefert.
            "text": self.text if include_text else None,
            "consensusText": self.consensus_text,
            "hasCriticalUncertainty": self.has_critical_uncertainty,
        }


@dataclass
class DocumentResult:
    job_id: str
    source_name: str
    classification: str
    created_at: float
    pages: list[PageResult]
    status: OCRStatus
    approved_at: float | None = None
    error: str | None = None
    # Maschinenlesbarer Marker (z.B. store.CLOUD_BLOCKED_ERROR_CODE), der eine
    # Privacy-Blockierung von einem gewoehnlichen Absturz unterscheidet (siehe
    # store.py: _run_job). IMMER (unconditionally) in to_dict() ausgegeben,
    # genau wie `error` -- das ist Diagnose-Metadaten, kein Transkriptinhalt,
    # und darf NICHT von include_text/Freigabe abhaengen: ein an einer
    # Privacy-Blockierung gescheiterter Job muss diagnostizierbar sein, ohne
    # dass irgendjemand etwas freigegeben hat.
    error_code: str | None = None

    @property
    def has_critical_uncertainty(self) -> bool:
        return any(p.has_critical_uncertainty for p in self.pages)

    def mark_approved(self) -> None:
        """Die explizite Lehrkraft-Freigabe. Das ist NICHT die einzige Stelle,
        die OCRStatus.APPROVED setzen darf: consensus.decide_status() darf das
        ebenfalls, aber nur fuer nicht-schuelerbezogenes Material mit
        ausdruecklich gesetztem auto_approve=True -- niemals fuer
        classification == "student_submission" (siehe OCRStatus.APPROVED)."""
        self.status = OCRStatus.APPROVED
        self.approved_at = time.time()

    def to_dict(self) -> dict:
        # include_text wird IMMER aus dem eigenen Status abgeleitet -- niemals
        # als Parameter entgegengenommen. Das ist der Sicherheits-Choke-Point
        # dieses gesamten Refactors: solange status nicht APPROVED ist, darf
        # kein voller Text (weder hier noch in Page/Region) die Review-UI
        # verlassen.
        include_text = self.status is OCRStatus.APPROVED
        critical_count = sum(
            1 for page in self.pages for region in page.regions if region.has_critical_uncertainty
        )
        return {
            "jobId": self.job_id,
            "sourceName": self.source_name,
            "classification": self.classification,
            "createdAt": self.created_at,
            "status": self.status.value,
            "approvedAt": self.approved_at,
            "error": self.error,
            # errorCode wird -- wie error -- IMMER ausgegeben, unabhaengig von
            # include_text: siehe Feld-Docstring oben.
            "errorCode": self.error_code,
            "pageCount": len(self.pages),
            "criticalCount": critical_count,
            "hasCriticalUncertainty": self.has_critical_uncertainty,
            "pages": [p.to_dict(include_text=include_text) for p in self.pages],
        }
