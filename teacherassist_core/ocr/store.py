"""Hintergrund-Job-Store fuer die OCR-Pipeline (Stufe 4b des OCR-Refactors).

``OCRJobStore`` ist die Bruecke zwischen der rein funktionalen Pipeline
(pipeline.py: process_document() usw., synchron, blockierend) und einer
Lehrkraft, die ein Dokument hochlaedt und danach weiterarbeiten will,
waehrend die Erkennung im Hintergrund laeuft: ``create()`` liefert sofort
ein PROCESSING-Ergebnis, ein einzelner Hintergrund-Worker erledigt die
eigentliche Arbeit, ``get()`` wird gepollt, bis der Job fertig ist.

EIN EINZIGER Hintergrund-Worker (``max_workers=1``) ist bewusst so gewaehlt,
nicht nur ein Default: zwei gleichzeitig laufende Torch-/VLM-Modelle wuerden
den Arbeitsspeicher eines Lehrer-Laptops sprengen. Jobs werden also
serialisiert, nie parallel verarbeitet.

Auf der Platte liegt unter ``root/<job_id>/``:
  - ``job.json`` -- das vollstaendige, JSON-serialisierte DocumentResult
    (siehe _serialize_document/_deserialize_document), PLUS die
    Engine-/Prompt-Version zur Reproduzierbarkeit/Auditierbarkeit
    (``prompts.VERBATIM_PROMPT_VERSION``, Engine-Namen/Modell-IDs) und ein
    Snapshot der verwendeten PipelineConfig.
  - ``source.upload`` -- die Original-Bytes der hochgeladenen PDF/des
    Bildes, damit ``page_png()`` spaeter verlangte Seiten/Regionen aus DER
    URSPRUENGLICHEN Quelle nachrendern kann (die Pipeline selbst haelt keine
    PIL-Bilder nach der Verarbeitung -- genau das macht sie speicherarm,
    siehe pipeline.py:process_document). Nur vorhanden, wenn ``create()``
    mit einem Path oder bytes aufgerufen wurde; bei einer bereits
    vorbereiteten ``Iterable[PageImage]`` (z.B. in Tests) gibt es nichts zu
    persistieren, und ``page_png()`` liefert dann ``None``.
  - ``page-{n}.png`` / ``region-{rid}.png`` -- verlangte Seiten-/Regionsbilder,
    lazy beim ersten ``page_png()``-Aufruf erzeugt und danach auf der Platte
    zwischengespeichert (5-35 MB je Seite -- viel zu gross fuer den
    verschluesselten Settings-Blob oder fuer ein dauerhaftes In-Memory-Cache).

``self._cache`` ist ein Write-Through-In-Memory-Cache (``dict[str,
DocumentResult]``): jede Aenderung wird ERST vollstaendig auf die Platte
geschrieben und ERST DANACH im Cache sichtbar (siehe
``OCRJobStore._persist_locked`` fuer die Invariante "der Cache eilt der
Platte nie voraus"), so dass ein neuer ``OCRJobStore`` auf demselben
``root`` (z.B. nach einem Neustart mitten in einem Batch) alle Jobs exakt
so wiederfindet, wie sie zuletzt im Cache sichtbar waren.

PFADTRAVERSAL-SCHUTZ (siehe Auftrag, spiegelt ``tool_server.py``'s
``_download_export`` bei Zeile ~1239): jede Methode, die eine ``job_id``
entgegennimmt, validiert sie ZUERST gegen ``JOB_ID_RE`` (dasselbe Alphabet
wie ``secrets.token_urlsafe`` erzeugt) und prueft ZUSAETZLICH
``job_dir.resolve().relative_to(self.root.resolve())`` -- doppelt gesichert,
nicht nur eine der beiden Pruefungen.

Import-Vertrag (siehe Auftrag): kein Modulebenen-Import schwerer
Abhaengigkeiten. PIL wird ausschliesslich innerhalb von Funktionen
importiert (siehe _downscale_and_encode/_encode_png/_render_source_page).
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Sequence

from .engines.base import OCREngine
from .pipeline import PipelineConfig, process_document
from .privacy_guard import CloudBlocked
from .prompts import VERBATIM_PROMPT_VERSION
from .types import (
    Disagreement,
    DocumentResult,
    ImageQuality,
    OCRCandidate,
    OCRStatus,
    PageResult,
    Region,
    RegionType,
)

logger = logging.getLogger(__name__)

# Dasselbe Alphabet, das secrets.token_urlsafe() erzeugt (A-Z a-z 0-9 - _).
JOB_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
REGION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Windows-reservierte Geraetenamen: bestehen JOB_ID_RE (rein alphanumerisch)
# UND loesen unter Windows auf echte Pfade auf (NUL existiert dort immer),
# muessen also zusaetzlich zur Zeichenklasse abgelehnt werden (siehe
# _resolve_job_dir). secrets.token_urlsafe() kann niemals eine dieser IDs
# erzeugen, die Ablehnung kann also nie eine legitime ID treffen.
_RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)

_REGION_CROP_PADDING_PX = 8
_PAGE_MAX_LONG_SIDE_PX = 1600
_SOURCE_FILENAME = "source.upload"

# Maschinenlesbarer Marker fuer DocumentResult.error_code, wenn ein
# Hintergrund-Job an CloudBlocked gescheitert ist (siehe _run_job): ein
# Sicherheitsereignis (Engine versuchte, Schuelerdaten an einen
# Nicht-Loopback-Endpunkt zu senden), das Ops-Tooling/UI unterscheiden
# koennen muessen, ohne die deutsche Fehlermeldung zu parsen.
CLOUD_BLOCKED_ERROR_CODE = "cloud_blocked"


def _is_reserved_device_name(job_id: str) -> bool:
    """True fuer CON/PRN/AUX/NUL/COM1-9/LPT1-9, case-insensitiv, auch mit
    Dateiendung (z.B. ``NUL.txt``) -- siehe _RESERVED_DEVICE_NAMES."""
    base = job_id.split(".", 1)[0]
    return base.upper() in _RESERVED_DEVICE_NAMES


class ApprovalRefused(Exception):
    """Wird von ``OCRJobStore.approve()`` geworfen, wenn mindestens eine
    Region noch eine ungeklaerte kritische Diskrepanz hat (siehe
    ``OCRJobStore.approve``-Docstring fuer die Design-Entscheidung
    "Exception statt stillem needs_review-Ergebnis"). Traegt die
    betroffenen Region-IDs, damit die HTTP-Schicht (Stufe 5) sie in eine
    409-Antwort mit Detailinformationen uebersetzen kann."""

    def __init__(self, region_ids: Sequence[str]) -> None:
        self.region_ids = tuple(region_ids)
        super().__init__(
            "Freigabe abgelehnt: ungeklärte kritische Unsicherheiten in Region(en) "
            + ", ".join(self.region_ids)
        )


class ApprovalNotReady(Exception):
    """Wird von ``OCRJobStore.approve()`` geworfen, wenn der Job noch nicht
    im Status ``NEEDS_REVIEW`` ist (z.B. noch ``PROCESSING`` oder bereits
    ``FAILED``).

    Ohne diese Pruefung waere die kritische-Diskrepanz-Pruefung in
    ``approve()`` vacuous: ein Job mit Status PROCESSING/FAILED hat eine
    LEERE ``pages``-Liste, hat also per Definition keine ungeklaerten
    kritischen Regionen -- die Freigabe wuerde still durchgehen und ein
    APPROVED-DocumentResult OHNE JEDEN Inhalt erzeugen, das das
    Bewertungs-Gate freischaltet.

    Bewusst getrennt von ``ApprovalRefused`` (siehe dort): "Job noch nicht
    bereit" und "Job hat ungeklaerte kritische Diskrepanzen" sind fuer die
    Lehrkraft unterschiedliche Probleme mit unterschiedlicher Anleitung,
    und die HTTP-Schicht (Stufe 5) bildet sie auf unterschiedliche
    409-Fehlercodes ab (OCR_NOT_READY vs. OCR_CRITICAL_UNRESOLVED)."""

    def __init__(self, status: OCRStatus) -> None:
        self.status = status
        super().__init__(
            "Freigabe abgelehnt: Job ist nicht im Status 'needs_review' "
            f"(aktueller Status: '{status.value}')."
        )


class EmptyPatchError(ValueError):
    """Wird von ``OCRJobStore.patch_region()`` geworfen, wenn weder ``text``
    noch ``candidate_engine`` angegeben ist.

    Ein solcher Aufruf veraendert nichts, wuerde aber unveraendert die
    Region zurueckliefern -- und ueber diese Region liesse sich, ohne
    jede Freigabe-Pruefung, ``selected_text``/Kandidatentexte auslesen
    (siehe Auftrag: der PATCH-Endpunkt war der EINZIGE Ort, an dem
    ``include_text`` hartkodiert statt vom Dokumentstatus abgeleitet
    wurde). Ein Patch, der nichts patcht, ist ein Client-Fehler, keine
    Leseoperation -- daher hier ein hartes Ablehnen statt eines stillen
    No-op-Erfolgs. Erbt bewusst von ``ValueError`` (wie die bestehende
    "unbekannte Engine"-Ablehnung), damit bestehender ``except
    ValueError``-Code weiterhin greift; die HTTP-Schicht unterscheidet
    trotzdem per ``isinstance`` fuer einen eigenen Fehlercode."""

    def __init__(self) -> None:
        super().__init__(
            "Patch muss mindestens 'text' oder 'candidateEngine' angeben."
        )


def _find_region(doc: DocumentResult, region_id: str) -> Region | None:
    for page in doc.pages:
        for region in page.regions:
            if region.id == region_id:
                return region
    return None


# -- Serialisierung: volle Wiedergabetreue, UNABHAENGIG vom Freigabestatus --
# (anders als DocumentResult.to_dict(), das text/selectedText erst nach
# APPROVED ausliefert -- job.json ist interner Speicher dieses Stores
# selbst, kein an einen Client ausgeliefertes Objekt, und muss beim
# Neuladen exakt denselben Zustand rekonstruieren koennen, egal welchen
# Freigabestatus der Job gerade hat.)


def _serialize_candidate(candidate: OCRCandidate) -> dict:
    return {
        "engine": candidate.engine,
        "text": candidate.text,
        "rawText": candidate.raw_text,
        "confidence": candidate.confidence,
        "tokens": list(candidate.tokens),
        "tokenConfidences": list(candidate.token_confidences),
        "durationMs": candidate.duration_ms,
        "markers": list(candidate.markers),
    }


def _deserialize_candidate(data: dict) -> OCRCandidate:
    return OCRCandidate(
        engine=data["engine"],
        text=data["text"],
        raw_text=data["rawText"],
        confidence=data["confidence"],
        tokens=tuple(data["tokens"]),
        token_confidences=tuple(data.get("tokenConfidences", ())),
        duration_ms=data.get("durationMs", 0),
        markers=tuple(data.get("markers", ())),
    )


def _serialize_disagreement(disagreement: Disagreement) -> dict:
    return {
        "start": disagreement.start,
        "end": disagreement.end,
        "variants": [[text, list(engine_names)] for text, engine_names in disagreement.variants],
        "critical": disagreement.critical,
        "reason": disagreement.reason,
        "charStart": disagreement.char_start,
        "charEnd": disagreement.char_end,
    }


def _deserialize_disagreement(data: dict) -> Disagreement:
    return Disagreement(
        start=data["start"],
        end=data["end"],
        variants=tuple((text, tuple(engine_names)) for text, engine_names in data["variants"]),
        critical=data["critical"],
        reason=data["reason"],
        # .get() mit -1-Default statt data[...]: ein job.json, das VOR
        # dieser Aenderung geschrieben wurde (z.B. noch im Cache dieser
        # Sitzung), traegt diese Felder noch nicht -- ein KeyError hier
        # wuerde beim Neuladen den GANZEN Job mitreissen (siehe
        # _load_existing). -1/-1 ist exakt der Disagreement-Docstring-
        # Default fuer "noch nicht gerendert".
        char_start=data.get("charStart", -1),
        char_end=data.get("charEnd", -1),
    )


def _serialize_region(region: Region) -> dict:
    return {
        "id": region.id,
        "type": region.type.value,
        "bbox": list(region.bbox),
        "candidates": [_serialize_candidate(c) for c in region.candidates],
        "referenceEngine": region.reference_engine,
        "consensusText": region.consensus_text,
        "selectedText": region.selected_text,
        "disagreements": [_serialize_disagreement(d) for d in region.disagreements],
        "agreement": region.agreement,
        "status": region.status.value,
        "editedByTeacher": region.edited_by_teacher,
        "verifyFailed": region.verify_failed,
    }


def _deserialize_region(data: dict) -> Region:
    return Region(
        id=data["id"],
        type=RegionType(data["type"]),
        bbox=tuple(data["bbox"]),
        candidates=tuple(_deserialize_candidate(c) for c in data["candidates"]),
        reference_engine=data["referenceEngine"],
        consensus_text=data["consensusText"],
        selected_text=data["selectedText"],
        disagreements=tuple(_deserialize_disagreement(d) for d in data["disagreements"]),
        agreement=data["agreement"],
        status=OCRStatus(data["status"]),
        edited_by_teacher=data.get("editedByTeacher", False),
        verify_failed=data.get("verifyFailed", False),
    )


def _deserialize_quality(data: dict) -> ImageQuality:
    return ImageQuality(
        width=data["width"],
        height=data["height"],
        estimated_dpi=data.get("estimatedDpi"),
        blur_score=data["blurScore"],
        contrast=data["contrast"],
        brightness=data["brightness"],
        skew_degrees=data["skewDegrees"],
        glare_ratio=data["glareRatio"],
        issues=tuple(data.get("issues", ())),
        blocking=data["blocking"],
        score=data["score"],
    )


def _serialize_page(page: PageResult) -> dict:
    return {
        "index": page.index,
        "width": page.width,
        "height": page.height,
        "quality": page.quality.to_dict(),
        "regions": [_serialize_region(r) for r in page.regions],
        "status": page.status.value,
        "autoClean": page.auto_clean,
        "engineFailures": [[engine, reason] for engine, reason in page.engine_failures],
        "statusReasons": list(page.status_reasons),
    }


def _deserialize_page(data: dict) -> PageResult:
    return PageResult(
        index=data["index"],
        width=data["width"],
        height=data["height"],
        quality=_deserialize_quality(data["quality"]),
        regions=tuple(_deserialize_region(r) for r in data["regions"]),
        status=OCRStatus(data["status"]),
        auto_clean=data["autoClean"],
        engine_failures=tuple((engine, reason) for engine, reason in data["engineFailures"]),
        status_reasons=tuple(data.get("statusReasons", ())),
    )


def _serialize_document(doc: DocumentResult) -> dict:
    return {
        "jobId": doc.job_id,
        "sourceName": doc.source_name,
        "classification": doc.classification,
        "createdAt": doc.created_at,
        "pages": [_serialize_page(p) for p in doc.pages],
        "status": doc.status.value,
        "approvedAt": doc.approved_at,
        "error": doc.error,
        # error_code ist ein echtes Feld von DocumentResult (types.py), das
        # dieser Store setzt (siehe CLOUD_BLOCKED_ERROR_CODE/_run_job) --
        # hier persistiert, damit es einen Neustart mitten in einem Batch
        # ueberlebt (siehe Modul-Docstring).
        "errorCode": doc.error_code,
    }


def _deserialize_document(data: dict) -> DocumentResult:
    doc = DocumentResult(
        job_id=data["jobId"],
        source_name=data["sourceName"],
        classification=data["classification"],
        created_at=data["createdAt"],
        pages=[_deserialize_page(p) for p in data["pages"]],
        status=OCRStatus(data["status"]),
        approved_at=data.get("approvedAt"),
        error=data.get("error"),
        error_code=data.get("errorCode"),
    )
    return doc


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="job-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        # os.replace() kann unter Windows transient mit PermissionError
        # ([WinError 5]) fehlschlagen, wenn die Zieldatei im selben Moment
        # kurzzeitig von einem anderen Handle geoeffnet ist (z.B. ein
        # Virenscanner oder ein gleichzeitiger Lesezugriff auf job.json) --
        # kein Datenverlust, nur ein zu frueher Versuch. Ein kurzer Retry
        # mit Backoff behebt DAS, und NUR das: er ist eine Verteidigung
        # gegen einen transienten Lock-Konflikt auf Windows, NICHT gegen
        # das Scheduling-Ordnungsproblem "Cache eilt der Platte voraus"
        # (siehe OCRJobStore._persist_locked) -- die beiden Probleme haben
        # unterschiedliche Ursachen, und dieser Retry behebt nur seines.
        _replace_attempts = 20
        for attempt in range(_replace_attempts):
            try:
                os.replace(temp_name, path)
                break
            except PermissionError:
                if attempt == _replace_attempts - 1:
                    raise
                time.sleep(0.05)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _engine_model_id(engine: OCREngine) -> str:
    try:
        return engine.status().model_id
    except Exception:  # noqa: BLE001 -- reine Bestpractice-Metadaten, nie kritisch
        return getattr(engine, "name", "")


def _downscale_and_encode(image: Any, *, max_long_side: int) -> bytes:
    """Skaliert `image` (PIL.Image.Image) so herunter, dass die laengere
    Seite hoechstens `max_long_side` Pixel misst, und kodiert als PNG-Bytes.
    PIL wird bewusst erst hier importiert (siehe Modul-Docstring)."""
    import io

    from PIL import Image

    width, height = image.size
    long_side = max(width, height)
    if long_side > max_long_side:
        scale = max_long_side / long_side
        new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        image = image.resize(new_size, Image.Resampling.BICUBIC)

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def _encode_png(image: Any) -> bytes:
    import io

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


class OCRJobStore:
    """Hintergrund-Job-Store: ``create()`` startet einen Job asynchron auf
    einem einzelnen Hintergrund-Worker (siehe Modul-Docstring zur
    ``max_workers=1``-Begruendung) und liefert sofort ein
    PROCESSING-Ergebnis; ``get()`` wird gepollt, bis der Job fertig ist."""

    def __init__(self, root: Path, *, max_workers: int = 1) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        self._cache: dict[str, DocumentResult] = {}
        self._load_existing()

    # -- Start/Wiederherstellung -----------------------------------------

    def _load_existing(self) -> None:
        """Laedt beim Start jeden auf der Platte gefundenen Job in den
        In-Memory-Cache (siehe Modul-Docstring: "survives a restart mid-
        batch"). Ein defektes/unlesbares job.json wird geloggt und
        uebersprungen, bricht den Store-Start aber nicht ab."""
        if not self.root.exists():
            return
        for job_dir in self.root.iterdir():
            if not job_dir.is_dir():
                continue
            job_json = job_dir / "job.json"
            if not job_json.exists():
                continue
            try:
                payload = json.loads(job_json.read_text(encoding="utf-8"))
                doc = _deserialize_document(payload["document"])
            except Exception:
                logger.warning("OCR-Job konnte beim Start nicht geladen werden: %s", job_dir)
                continue
            self._cache[doc.job_id] = doc

    # -- Pfadtraversal-Schutz ----------------------------------------------

    def _resolve_job_dir(self, job_id: str) -> Path | None:
        """Doppelt gesicherte Validierung (siehe Modul-Docstring): erst das
        erlaubte Zeichenalphabet, DANN die Ablehnung Windows-reservierter
        Geraetenamen (CON/NUL/COM1/... -- bestehen das Zeichenalphabet,
        loesen unter Windows aber auf echte, immer existierende Pfade auf,
        siehe _RESERVED_DEVICE_NAMES), dann zusaetzlich, dass der
        aufgeloeste Pfad tatsaechlich unterhalb von ``self.root`` liegt.
        Jede Verletzung liefert ``None`` -- kein Raise, damit Aufrufer
        einheitlich mit ``None``/``False`` reagieren koennen, ohne den
        Fehlerfall extra zu
        behandeln."""
        if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id):
            return None
        if _is_reserved_device_name(job_id):
            return None
        candidate = (self.root / job_id).resolve()
        try:
            candidate.relative_to(self.root.resolve())
        except ValueError:
            return None
        return candidate

    # -- Erzeugen/Ausfuehren ------------------------------------------------

    def _generate_job_id(self) -> str:
        while True:
            candidate = secrets.token_urlsafe(24)
            if JOB_ID_RE.match(candidate) and candidate not in self._cache:
                return candidate

    def create(
        self,
        *,
        source: Any,
        source_name: str,
        config: PipelineConfig,
        engines: Sequence[OCREngine],
    ) -> DocumentResult:
        """Legt einen neuen Job an und startet ihn im Hintergrund. Liefert
        SOFORT ein PROCESSING-DocumentResult (der Aufrufer bekommt nie den
        blockierenden process_document()-Aufruf direkt zu sehen)."""
        job_id = self._generate_job_id()
        job_dir = self.root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        self._persist_source(job_dir, source)

        stub = DocumentResult(
            job_id=job_id,
            source_name=source_name,
            classification=config.classification,
            created_at=time.time(),
            pages=[],
            status=OCRStatus.PROCESSING,
        )
        with self._lock:
            self._persist_locked(job_id, stub, config=config, engines=engines)

        self._executor.submit(self._run_job, job_id, source, source_name, config, engines)
        return stub

    def _persist_source(self, job_dir: Path, source: Any) -> None:
        """Sichert die Original-Bytes fuer spaeteres Nachrendern
        (``page_png``). Bei einer bereits vorbereiteten
        ``Iterable[PageImage]`` (kein Path/bytes) gibt es nichts zu
        sichern -- ``page_png`` liefert dann spaeter ``None``."""
        try:
            if isinstance(source, Path):
                data = source.read_bytes()
            elif isinstance(source, (bytes, bytearray)):
                data = bytes(source)
            else:
                return
            (job_dir / _SOURCE_FILENAME).write_bytes(data)
        except OSError:
            logger.warning("Quelle für OCR-Job konnte nicht gesichert werden: %s", job_dir)

    def _run_job(
        self,
        job_id: str,
        source: Any,
        source_name: str,
        config: PipelineConfig,
        engines: Sequence[OCREngine],
    ) -> None:
        """Laeuft auf dem Hintergrund-Worker. Jede Exception -- auch
        CloudBlocked, das process_document() bewusst NICHT abfaengt (siehe
        pipeline.py) -- wird HIER, an der Executor-Grenze, aufgefangen:
        "Never let a worker exception kill the executor" (siehe Auftrag).
        Ein zweiter Job muss nach einem ersten, abgestuerzten Job weiterhin
        normal fertig werden koennen.

        CloudBlocked wird VOR dem allgemeinen except-Zweig separat
        abgefangen (siehe privacy_guard.py Modul-Docstring: das gilt nur
        fuer den SYNCHRONEN Pfad als "muss durchschlagen" -- hier, im
        asynchronen Hintergrund-Worker, ist die HTTP-Antwort (202
        processing) laengst zurueckgegeben, es gibt also keinen lebenden
        Call-Stack mehr, in den die Exception "durchschlagen" koennte. Der
        Job wird stattdessen FAILED mit einem eigenen, maschinenlesbaren
        Marker (CLOUD_BLOCKED_ERROR_CODE) -- NICHT als gewoehnlicher
        engine_failure/needs_review behandelt, damit ein Privacy-Verstoss
        (eine Engine versuchte, Schuelerdaten an einen Nicht-Loopback-
        Endpunkt zu senden) fuer Ops-Tooling/UI von einem gewoehnlichen
        Absturz (kaputtes PDF, OOM) unterscheidbar bleibt, ohne die
        deutsche Fehlermeldung parsen zu muessen."""
        try:
            result = process_document(
                source,
                job_id=job_id,
                source_name=source_name,
                config=config,
                engines=engines,
            )
        except CloudBlocked as exc:
            # exc.engine ist gesetzt, sobald pipeline.py sie an der Stelle
            # nachtragen konnte, an der bekannt ist, welche Engine gerade
            # aufgerufen wurde (siehe pipeline.py: process_page). Nur wenn
            # sie -- aus welchem Grund auch immer -- None geblieben ist,
            # faellt der Log auf die alte Approximation "eine der
            # konfigurierten Engines" zurueck.
            if exc.engine is not None:
                engine_desc = exc.engine
            else:
                engine_desc = (
                    "unbekannt (konfiguriert: "
                    + (", ".join(sorted({getattr(e, "name", "?") for e in engines})) or "-")
                    + ")"
                )
            logger.error(
                "OCR-Job %s: Cloud-Zugriff blockiert (Klassifikation=%s, Endpunkt=%s, Engine=%s)",
                job_id,
                exc.classification,
                exc.endpoint,
                engine_desc,
            )
            with self._lock:
                existing = self._cache.get(job_id)
                if existing is None:
                    existing = DocumentResult(
                        job_id=job_id,
                        source_name=source_name,
                        classification=config.classification,
                        created_at=time.time(),
                        pages=[],
                        status=OCRStatus.FAILED,
                        error=str(exc),
                    )
                else:
                    existing.status = OCRStatus.FAILED
                    existing.error = str(exc)
                existing.error_code = CLOUD_BLOCKED_ERROR_CODE
                self._persist_locked(job_id, existing, config=config, engines=engines)
            return
        except Exception as exc:  # noqa: BLE001 -- siehe Docstring
            logger.exception("OCR-Job %s ist fehlgeschlagen", job_id)
            with self._lock:
                existing = self._cache.get(job_id)
                if existing is None:
                    existing = DocumentResult(
                        job_id=job_id,
                        source_name=source_name,
                        classification=config.classification,
                        created_at=time.time(),
                        pages=[],
                        status=OCRStatus.FAILED,
                        error=str(exc),
                    )
                else:
                    existing.status = OCRStatus.FAILED
                    existing.error = str(exc)
                existing.error_code = None
                self._persist_locked(job_id, existing, config=config, engines=engines)
            return

        with self._lock:
            result.error_code = None
            self._persist_locked(job_id, result, config=config, engines=engines)

    # -- Persistenz ----------------------------------------------------------

    def _persist(
        self,
        job_id: str,
        *,
        config: PipelineConfig | None = None,
        engines: Sequence[OCREngine] | None = None,
    ) -> None:
        """Oeffentlicher Einstiegspunkt: liest den aktuellen Cache-Zustand
        fuer `job_id` und delegiert an `_persist_locked` -- unter
        `self._lock` fuer die GESAMTE Dauer (Lesen des Cache UND
        Schreiben auf die Platte), damit kein anderer Thread zwischen
        beiden einen inkonsistenten Zwischenzustand sehen kann. `config`/
        `engines` werden nur bei Aufrufen mitgegeben, die sie zur Hand
        haben (create/_run_job) -- ohne sie werden vorhandene Werte aus
        der bestehenden Datei uebernommen (patch_region/approve kennen
        die urspruengliche Config nicht mehr, sollen sie aber auch nicht
        loeschen).

        Aufrufer, die `doc` bereits selbst haben und unter dem Lock
        mutieren (siehe `create`/`_run_job`/`patch_region`/`approve`),
        rufen stattdessen DIREKT `_persist_locked` innerhalb ihres
        eigenen `with self._lock:`-Blocks auf -- dieser Wrapper existiert
        fuer Aufrufer (Tests, siehe test_ocr_store.py), die nur die
        `job_id` kennen."""
        with self._lock:
            doc = self._cache.get(job_id)
            if doc is None:
                return
            self._persist_locked(job_id, doc, config=config, engines=engines)

    def _persist_locked(
        self,
        job_id: str,
        doc: DocumentResult,
        *,
        config: PipelineConfig | None = None,
        engines: Sequence[OCREngine] | None = None,
    ) -> None:
        """Schreibt `doc` vollstaendig nach job.json und veroeffentlicht es
        ERST DANACH im In-Memory-Cache. MUSS unter `self._lock` aufgerufen
        werden (RLock -- daher auch reentrant aus `_persist()` heraus
        aufrufbar); der Aufruf ist Teil des GLEICHEN Lock-Griffs, in dem
        der Aufrufer `doc` zuvor angelegt/mutiert hat.

        INVARIANTE: der Cache eilt der Platte nie voraus ("the cache
        never leads the disk"). Jeder Aufrufer haelt `self._lock` ueber
        die gesamte Zustandsaenderung (mutieren + persistieren), nicht
        nur ueber die Cache-Zuweisung -- ein anderer Thread, der ueber
        `get()`/`list()`/`snapshot()` denselben Lock nimmt, kann den
        neuen Zustand also erst sehen, NACHDEM `_atomic_write_json()`
        bereits vollstaendig durchgelaufen ist (das `os.replace()` darin
        ist atomar, es gibt also nie einen halb geschriebenen
        Plattenstand). Das schliesst genau das Szenario, das den
        fruehreren Bug ausloeste: ein Aufrufer pollt `store.get(job_id)`,
        bis der Job einen Endzustand verlaesst, und oeffnet DANACH einen
        zweiten `OCRJobStore` auf demselben `root` (siehe Modul-
        Docstring: "survives a restart mid-batch") -- dieser zweite Store
        liest NUR von der Platte (`_load_existing`), hat also keinerlei
        Sicht auf den Cache des ersten. Vorher wurde der Cache VOR dem
        Abschluss des Plattenschreibvorgangs aktualisiert, sodass das
        Polling bereits den neuen Status meldete, waehrend job.json noch
        den alten Stand zeigte. Jetzt ist die Reihenfolge innerhalb EINES
        Lock-Griffs fest verdrahtet: erst schreiben, dann
        veroeffentlichen -- kein Beobachter (dieser Prozess ueber den
        Lock, oder ein neuer Store ueber die Platte) kann je den neuen
        Cache-Stand vor dem entsprechenden Plattenstand sehen."""
        job_dir = self.root / job_id
        job_json_path = job_dir / "job.json"
        payload: dict[str, Any] = {"schemaVersion": 1}
        if job_json_path.exists():
            try:
                payload = json.loads(job_json_path.read_text(encoding="utf-8"))
            except Exception:
                payload = {"schemaVersion": 1}

        payload["document"] = _serialize_document(doc)
        payload["promptVersion"] = VERBATIM_PROMPT_VERSION

        if config is not None:
            payload["config"] = {
                "classification": config.classification,
                "subject": config.subject,
                "language": config.language,
                "targetDpi": config.target_dpi,
                "minAgreement": config.min_agreement,
                "minConfidence": config.min_confidence,
                "autoApprove": config.auto_approve,
                "requireEngines": list(config.require_engines),
                "maxPages": config.max_pages,
            }
        if engines is not None:
            payload["engines"] = [
                {"name": getattr(engine, "name", ""), "modelId": _engine_model_id(engine)}
                for engine in engines
            ]

        _atomic_write_json(job_json_path, payload)
        # Erst JETZT, nachdem der Plattenschreibvorgang vollstaendig
        # abgeschlossen ist, wird der Cache aktualisiert -- siehe
        # INVARIANTE oben.
        self._cache[job_id] = doc

    def _read_job_config(self, job_dir: Path) -> dict | None:
        job_json = job_dir / "job.json"
        if not job_json.exists():
            return None
        try:
            payload = json.loads(job_json.read_text(encoding="utf-8"))
        except Exception:
            return None
        return payload.get("config")

    # -- Abfragen --------------------------------------------------------------

    def get(self, job_id: str) -> DocumentResult | None:
        if self._resolve_job_dir(job_id) is None:
            return None
        with self._lock:
            return self._cache.get(job_id)

    def list(self) -> list[dict]:
        """Knappe Zusammenfassung aller Jobs (neueste zuerst) -- KEIN
        Volltext, das bleibt DocumentResult.to_dict()'s Freigabe-Choke-Point
        vorbehalten (siehe types.py)."""
        with self._lock:
            docs = list(self._cache.values())
        docs.sort(key=lambda d: d.created_at, reverse=True)
        return [
            {
                "jobId": doc.job_id,
                "sourceName": doc.source_name,
                "classification": doc.classification,
                "status": doc.status.value,
                "createdAt": doc.created_at,
                "pageCount": len(doc.pages),
            }
            for doc in docs
        ]

    def snapshot(self) -> dict[str, DocumentResult]:
        """Kopie des aktuellen Cache-Zustands fuer
        ``gate.evaluate_grading_gate(jobs=...)``."""
        with self._lock:
            return dict(self._cache)

    # -- Seiten-/Regionsbilder ---------------------------------------------

    def _render_source_page(self, job_dir: Path, page_index: int) -> Any | None:
        """Rendert Seite `page_index` frisch aus der gesicherten
        Original-Quelle (``source.upload``) -- die Pipeline haelt nach der
        Verarbeitung keine PIL-Bilder mehr vor (siehe Modul-Docstring)."""
        source_path = job_dir / _SOURCE_FILENAME
        if not source_path.exists():
            return None

        from .page_render import load_pages

        job_config = self._read_job_config(job_dir)
        target_dpi = int(job_config.get("targetDpi", 350)) if job_config else 350
        data = source_path.read_bytes()

        for page in load_pages(data, target_dpi=target_dpi, max_pages=page_index + 1):
            if page.index == page_index:
                return page.image
        return None

    def page_png(self, job_id: str, page: int, *, region_id: str | None = None) -> bytes | None:
        """Liefert PNG-Bytes fuer Seite `page` (voll, auf max. 1600 px
        lange Kante herunterskaliert) oder, mit `region_id`, einen
        Regionsausschnitt (8 px Rand, aus der vollaufgeloesten Seite
        geschnitten). Wird lazy erzeugt und danach auf der Platte
        zwischengespeichert (siehe Modul-Docstring)."""
        if region_id is not None and not REGION_ID_RE.match(region_id):
            return None
        job_dir = self._resolve_job_dir(job_id)
        if job_dir is None:
            return None

        doc = self.get(job_id)
        if doc is None or page < 0 or page >= len(doc.pages):
            return None

        if region_id is None:
            cache_path = job_dir / f"page-{page}.png"
            if cache_path.exists():
                return cache_path.read_bytes()
            image = self._render_source_page(job_dir, page)
            if image is None:
                return None
            png_bytes = _downscale_and_encode(image, max_long_side=_PAGE_MAX_LONG_SIDE_PX)
            cache_path.write_bytes(png_bytes)
            return png_bytes

        cache_path = job_dir / f"region-{region_id}.png"
        if cache_path.exists():
            return cache_path.read_bytes()

        region = _find_region(doc, region_id)
        if region is None or region.bbox is None:
            return None
        image = self._render_source_page(job_dir, page)
        if image is None:
            return None

        x0, y0, x1, y1 = region.bbox
        pad = _REGION_CROP_PADDING_PX
        box = (
            max(0, x0 - pad),
            max(0, y0 - pad),
            min(image.width, x1 + pad),
            min(image.height, y1 + pad),
        )
        crop = image.crop(box)
        png_bytes = _encode_png(crop)
        cache_path.write_bytes(png_bytes)
        return png_bytes

    # -- Lehrkraft-Aktionen ---------------------------------------------------

    def patch_region(
        self,
        job_id: str,
        region_id: str,
        *,
        text: str | None = None,
        candidate_engine: str | None = None,
    ) -> Region | None:
        """`text=` setzt `selected_text` direkt und markiert die Region als
        `edited_by_teacher`. `candidate_engine=` uebernimmt den Text DIESES
        Kandidaten in `selected_text` -- und markiert die Region ebenfalls
        als `edited_by_teacher`: Region kennt kein separates
        "expliziter Kandidat gewaehlt"-Feld, `edited_by_teacher` ist die
        EINZIGE im Datenmodell verfuegbare Markierung fuer "eine Lehrkraft
        hat sich hier aktiv entschieden" (siehe `approve()`-Docstring, das
        genau darauf aufbaut). Ein unbekannter Enginename wird abgelehnt
        (ValueError), statt die Region unveraendert zu lassen.

        Sind BEIDE Parameter `None`, wird `EmptyPatchError` geworfen --
        ein solcher Aufruf veraendert nichts und darf nicht still die
        (moeglicherweise noch nicht freigegebene) Region unveraendert
        zurueckliefern (siehe Auftrag / `EmptyPatchError`-Docstring).
        Diese Pruefung steht bewusst VOR jeder Job-/Region-Aufloesung:
        sie ist reine Argumentvalidierung, unabhaengig davon, ob der Job
        ueberhaupt existiert."""
        if text is None and candidate_engine is None:
            raise EmptyPatchError()
        if self._resolve_job_dir(job_id) is None:
            return None
        with self._lock:
            doc = self._cache.get(job_id)
            if doc is None:
                return None
            region = _find_region(doc, region_id)
            if region is None:
                return None

            if candidate_engine is not None:
                candidate = next(
                    (c for c in region.candidates if c.engine == candidate_engine), None
                )
                if candidate is None:
                    raise ValueError(f"Unbekannte Engine für diese Region: {candidate_engine}")
                region.selected_text = candidate.text
                region.edited_by_teacher = True

            if text is not None:
                region.selected_text = text
                region.edited_by_teacher = True

            self._persist_locked(job_id, doc)
        return region

    def approve(self, job_id: str, pages: Sequence[int] | None = None) -> DocumentResult | None:
        """Setzt `DocumentResult.mark_approved()`, nachdem sichergestellt
        ist, dass (a) der Job ueberhaupt in einem freigebbaren Zustand ist
        und (b) keine betroffene Region noch eine ungeklaerte kritische
        Diskrepanz hat.

        (a) ZUERST: der Job muss Status `NEEDS_REVIEW` haben. Ohne diese
        Pruefung waere (b) vacuous -- ein Job mit Status PROCESSING/FAILED
        hat eine LEERE `pages`-Liste, hat also per Definition keine
        ungeklaerten kritischen Regionen, und die Freigabe wuerde still
        durchgehen und ein APPROVED-Ergebnis OHNE JEDEN Inhalt erzeugen
        (siehe `ApprovalNotReady`-Docstring). Verletzung wirft
        `ApprovalNotReady`.

        DESIGN-ENTSCHEIDUNG (siehe Auftrag: "Pick one, document it"): bei
        einer Verletzung von (a) ODER (b) wird eine Exception GEWORFEN
        (statt still ein weiterhin needs_review-Ergebnis zurueckzugeben) --
        das macht den Ablehnungsgrund explizit fuer den Aufrufer sichtbar
        und laesst sich in der HTTP-Schicht (Stufe 5) 1:1 auf einen
        409-Statuscode mit Detail-Payload abbilden, ohne den Erfolgsfall
        (DocumentResult) und den Ablehnungsfall ueber dasselbe
        Rueckgabeobjekt unterscheiden zu muessen. ZWEI unterschiedliche
        Exceptions (`ApprovalNotReady` vs. `ApprovalRefused`), weil "Job
        noch nicht bereit" und "Job hat ungeklaerte kritische
        Diskrepanzen" fuer die Lehrkraft unterschiedliche Probleme mit
        unterschiedlicher Anleitung sind.

        Eine Region gilt als "geklaert", wenn `edited_by_teacher` True ist
        (siehe `patch_region()`-Docstring: das ist der einzige verfuegbare
        Marker, sowohl fuer freien Text als auch fuer eine explizite
        Kandidatenauswahl). `pages=None` prueft/gibt das gesamte Dokument
        frei; eine `pages`-Liste beschraenkt die Pruefung (und NUR die
        Pruefung -- der Dokumentstatus selbst ist immer ein Ganzes) auf die
        genannten Seitenindizes."""
        if self._resolve_job_dir(job_id) is None:
            return None
        with self._lock:
            doc = self._cache.get(job_id)
            if doc is None:
                return None

            if doc.status is not OCRStatus.NEEDS_REVIEW:
                raise ApprovalNotReady(doc.status)

            target_pages = doc.pages if pages is None else [p for p in doc.pages if p.index in pages]
            unresolved = [
                region.id
                for page in target_pages
                for region in page.regions
                if region.has_critical_uncertainty and not region.edited_by_teacher
            ]
            if unresolved:
                raise ApprovalRefused(unresolved)

            doc.mark_approved()
            self._persist_locked(job_id, doc)
        return doc

    def delete(self, job_id: str) -> bool:
        """Liefert `True` nur, wenn `job_id` tatsaechlich ein im Store
        bekannter Job war (Cache-Mitgliedschaft, NICHT nur
        `job_dir.exists()` -- ein reservierter Geraetename wie `NUL` wuerde
        unter Windows sonst als existierender Pfad durchgehen, obwohl er
        nie ein echter Job war; siehe `_is_reserved_device_name`, das ihn
        bereits in `_resolve_job_dir` ausschliesst, hier zusaetzlich
        abgesichert)."""
        job_dir = self._resolve_job_dir(job_id)
        if job_dir is None:
            return False
        with self._lock:
            existed_in_store = self._cache.pop(job_id, None) is not None
        if not existed_in_store:
            return False
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        return True

    def purge_expired(self, retention_days: int) -> int:
        """Loescht (per `shutil.rmtree`) jeden Job-Ordner, dessen
        `created_at` aelter als `retention_days` Tage ist. Gibt die Anzahl
        entfernter Jobs zurueck.

        Sweept ZUSAETZLICH verwaiste Ordner direkt unter `self.root`, die in
        KEINEM Cache-Eintrag stecken (typischerweise: ein `job.json`, das
        `_load_existing()` beim Start als kaputt/unlesbar uebersprungen hat
        -- siehe `_load_existing`-Docstring). Ohne diesen zweiten Sweep kann
        so ein Ordner NIE entfernt werden: er ist in keinem Cache, also nie
        Teil von `expired_ids` oben, und `delete()` ist bewusst cache-only
        (siehe dessen Docstring). Auf einer Maschine, die ganze Klassensaetze
        verarbeitet, sind das 5-35 MB PNGs pro Seite -- genau die Daten, fuer
        die die Aufbewahrungsfrist existiert.

        Pop-aus-Cache UND `shutil.rmtree` laufen fuer jeden Job UNTER
        DEMSELBEN `self._lock`-Griff (siehe Auftrag Fix 5): jede Mutation
        (`patch_region`/`approve`/`_persist_locked`) haelt denselben Lock
        ueber ihre GESAMTE kritische Sektion (Lesen aus dem Cache bis zum
        abgeschlossenen Plattenschreibvorgang). Wuerde hier NACH dem Pop
        der Lock freigegeben und ERST DANACH `rmtree` aufgerufen (wie
        zuvor), koennte ein Job, der GENAU an seiner Aufbewahrungsgrenze
        liegt und den eine Lehrkraft gerade aktiv patcht/freigibt, seinen
        Ordner waehrend eines gleichzeitigen Schreibvorgangs verlieren.
        Mit dem Lock ueber Pop+rmtree kann eine laufende Mutation (die den
        Lock haelt) niemals von der Loeschung ueberholt werden: entweder
        ist der Job zum Zeitpunkt des Pops noch unveraendert im Cache
        (dann wird sauber geloescht) oder eine Mutation ist zuerst fertig
        und vollstaendig persistiert (dann wird DANACH geloescht) -- nie
        ein halb geschriebener Zwischenzustand."""
        cutoff = time.time() - retention_days * 86400
        with self._lock:
            expired_ids = [job_id for job_id, doc in self._cache.items() if doc.created_at < cutoff]

        removed = 0
        for job_id in expired_ids:
            with self._lock:
                if job_id not in self._cache:
                    continue
                self._cache.pop(job_id, None)
                job_dir = self._resolve_job_dir(job_id)
                if job_dir is not None and job_dir.exists():
                    shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1

        removed += self._purge_orphaned_directories(cutoff)
        return removed

    def _read_created_at(self, job_dir: Path) -> float | None:
        """Bestes bekanntes `created_at` fuer einen Ordner ausserhalb des
        Caches, aus seinem eigenen `job.json` gelesen -- `None`, wenn die
        Datei fehlt oder nicht lesbar/parsebar ist (dann faellt
        `_purge_orphaned_directories` auf die Verzeichnis-mtime zurueck)."""
        job_json = job_dir / "job.json"
        if not job_json.exists():
            return None
        try:
            payload = json.loads(job_json.read_text(encoding="utf-8"))
            return float(payload["document"]["createdAt"])
        except Exception:
            return None

    def _purge_orphaned_directories(self, cutoff: float) -> int:
        """Sweept Eintraege direkt unter `self.root`, die NICHT im Cache
        stecken (siehe `purge_expired`-Docstring). Konservativ: nur Namen,
        die `JOB_ID_RE` bestehen UND durch `_resolve_job_dir` (Pfadtraversal-
        Schutz, siehe Modul-Docstring) aufgeloest werden koennen, werden
        ueberhaupt betrachtet -- niemals ein blankes `rmtree` auf irgendetwas
        Gefundenes. `created_at` kommt, wenn moeglich, aus dem eigenen
        `job.json` des Ordners; ist das unlesbar, wird die Verzeichnis-mtime
        als Naeherung verwendet."""
        if not self.root.exists():
            return 0
        with self._lock:
            known_ids = set(self._cache.keys())

        removed = 0
        for entry in self.root.iterdir():
            if not entry.is_dir() or entry.name in known_ids:
                continue
            job_dir = self._resolve_job_dir(entry.name)
            if job_dir is None:
                continue

            created_at = self._read_created_at(job_dir)
            if created_at is None:
                try:
                    created_at = job_dir.stat().st_mtime
                except OSError:
                    continue
            if created_at >= cutoff:
                continue

            age_days = (time.time() - created_at) / 86400
            logger.warning(
                "Verwaister OCR-Job-Ordner entfernt (job.json fehlt/unlesbar, Alter: "
                "%.1f Tage): %s",
                age_days,
                job_dir,
            )
            shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1
        return removed

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)
