"""OCR-Pipeline: verbindet Bildqualitaet, Segmentierung, Engines und Konsens
zu einem End-zu-Ende-Ablauf ueber ganze Dokumente (Stufe 4b des OCR-Refactors).

Dieses Modul ist der Zusammenbau der in den Stufen 0-3 einzeln gebauten
Teile (image_quality, segmentation, preprocess, engines, consensus) -- es
selbst enthaelt keine neue fachliche Logik zu Bildqualitaet, Segmentierung
oder Konsens, sondern nur die Reihenfolge, in der diese Teile fuer eine
Seite bzw. ein ganzes Dokument aufgerufen werden.

WICHTIGE SICHERHEITSREGEL (siehe process_page): Ist eine Seite laut
image_quality.assess() "blocking" (zu unscharf/zu klein), werden die Engines
NIE aufgerufen. Ein grosses Modell, das ein unbrauchbares Foto "rettet",
ist genau der Fehlerfall, den dieses gesamte Projekt verhindern soll -- ein
schlechtes Foto verdient eine erneute Aufnahme, keine geratene Abschrift.

Import-Vertrag (siehe Auftrag): dieses Modul importiert KEINE schweren
Abhaengigkeiten auf Modulebene. image_quality/preprocess/segmentation/
engines.base importieren PIL/numpy selbst ausschliesslich innerhalb von
Funktionen (siehe deren Modul-Docstrings) -- dieses Modul importiert nur
diese (bereits lazy-sicheren) Module, nie torch/transformers/pytesseract/
PIL/numpy/paddle direkt.
"""

from __future__ import annotations

import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from . import image_quality, preprocess, segmentation
from .consensus import build_region, decide_status
from .critical_tokens import CriticalTokenConfig
from .engines.base import EngineError, OCREngine
from .page_render import PageImage, load_pages
from .privacy_guard import CloudBlocked
from .types import DocumentResult, OCRCandidate, OCRStatus, PageResult, Region

OnPage = Callable[[int, PageResult], None]
OnProgress = Callable[[float, str], None]


class OCRBusy(RuntimeError):
    """The legacy synchronous OCR slot is still occupied by a timed-out job."""


_sync_ocr_slot = threading.Lock()


@dataclass(frozen=True)
class PipelineConfig:
    """Alle Stellschrauben eines einzelnen OCR-Laufs an einem Ort.

    `require_engines` steuert, welche Engines fuer decide_status() als
    zwingend gelten (siehe consensus.decide_status): fehlt eine davon (z.B.
    weil das HTR-Modell noch nicht heruntergeladen ist), wird die Seite nie
    auto_clean, egal wie sauber der Konsens der uebrigen Engines ist.
    `classification` entscheidet zusammen mit `auto_approve`, ob
    decide_status() ueberhaupt APPROVED vergeben darf -- fuer
    "student_submission" NIE (siehe consensus.py-Kommentare).

    `verify_engines` benennt die Engines (per `OCREngine.name`), die NICHT
    ueber jede Region der Seite laufen, sondern nur als zweiter, gezielter
    Blick auf bereits verdaechtige Regionen (siehe process_page: "selective
    second reading" -- ein Ollama-VLM ist auf langsamer Hardware zu
    langsam fuer flaechendeckenden Einsatz, siehe engines/ollama_vlm.py
    Moduldoc fuer die gemessenen Zeiten). Default `()`: leer heisst keine
    Verhaltensaenderung gegenueber der Vor-Feature-Pipeline -- jede in
    `engines` uebergebene Engine laeuft weiterhin auf jeder Region.
    `max_verify_regions_per_page` deckelt, wie viele Regionen pro Seite
    hoechstens diesen zweiten Blick bekommen (Kostenobergrenze); wird sie
    ueberschritten, werden kritische Regionen zuerst bedient, dann die mit
    der niedrigsten Uebereinstimmung, und der Rest bekommt den Grund
    "verify_budget_exhausted" im Seitenergebnis vermerkt (siehe
    process_page), statt stillschweigend als ungeprueft zu gelten.
    """

    classification: str = "student_submission"
    subject: str | None = None
    language: str = "deu"
    target_dpi: int = 350
    min_agreement: float = 0.98
    min_confidence: float = 0.75
    auto_approve: bool = False
    require_engines: tuple[str, ...] = ("htr",)
    max_pages: int = 40
    verify_engines: tuple[str, ...] = ()
    max_verify_regions_per_page: int = 12

    @classmethod
    def from_settings(cls, settings: Mapping[str, Any], *, classification: str) -> "PipelineConfig":
        """Baut eine Config aus den (camelCase) Einstellungen des Nutzers.

        `classification` wird bewusst NICHT aus `settings` gelesen, sondern
        immer explizit vom Aufrufer uebergeben -- sie beschreibt die
        konkrete Anfrage (z.B. "student_submission" fuer einen hochgeladenen
        Schueler-Scan), nicht eine globale Einstellung, und ist damit der
        eine Parameter, den `decide_status()` niemals aus einer
        veraenderlichen Einstellung ableiten darf (siehe consensus.py:
        "classification == 'student_submission' gibt NIE automatisch
        frei")."""
        require_engines = settings.get("ocrRequireEngines")
        if not require_engines:
            require_engines = cls.require_engines
        # ocrVerifyEngines defaultet bewusst auf [] (siehe runtime.py
        # DEFAULT_SETTINGS) -- solange eine Lehrkraft es nicht ausdruecklich
        # setzt, aendert dieses Feature nichts am bisherigen Verhalten.
        verify_engines = settings.get("ocrVerifyEngines") or ()
        return cls(
            classification=classification,
            subject=(settings.get("ocrSubject") or None),
            language=str(settings.get("ocrLanguage") or "deu"),
            target_dpi=int(settings.get("ocrTargetDpi") or 350),
            min_agreement=float(settings.get("ocrMinAgreement") or 0.98),
            min_confidence=float(settings.get("ocrMinConfidence") or 0.75),
            auto_approve=bool(settings.get("ocrAutoApproveNonStudent", False)),
            require_engines=tuple(require_engines),
            max_pages=int(settings.get("ocrMaxPages") or 40),
            verify_engines=tuple(verify_engines),
            max_verify_regions_per_page=int(settings.get("ocrMaxVerifyRegions") or 12),
        )


def _empty_region(region_id: str, region_type, bbox: tuple[int, int, int, int]) -> Region:
    """Baut eine Region OHNE Kandidaten (jede Engine ist fuer sie
    fehlgeschlagen). build_region() selbst verlangt mindestens einen
    Kandidaten (siehe consensus.py: "build_region benoetigt mindestens
    einen Kandidaten") -- diese Region wird deshalb direkt konstruiert,
    nicht ueber build_region(). Sie MUSS trotzdem im Ergebnis auftauchen
    (siehe Auftrag: "do not silently drop it"), damit die Review-UI zeigen
    kann, dass an dieser Stelle der Seite gar nichts erkannt werden
    konnte."""
    return Region(
        id=region_id,
        type=region_type,
        bbox=bbox,
        candidates=(),
        reference_engine="",
        consensus_text="",
        selected_text="",
        disagreements=(),
        agreement=0.0,
        status=OCRStatus.NEEDS_REVIEW,
    )


def _recognize_all(
    engines: Sequence[OCREngine],
    prepared: Any,
    *,
    region_type,
    language: str,
    region_id: str,
    engine_failures: list[tuple[str, str]],
) -> list[OCRCandidate]:
    """Ruft jede Engine in `engines` auf einer bereits zugeschnittenen und
    vorbereiteten Region auf und sammelt die ueberlebenden Kandidaten.

    Gemeinsamer Kern fuer den Massenlauf (jede Bulk-Engine auf jeder Region,
    siehe process_page Schritt 3) UND fuer den gezielten Verifikationslauf
    (nur eine Handvoll Regionen, siehe process_page Schritt 4): EngineError
    wird abgefangen und als (engine, reason) an `engine_failures`
    angehaengt, der Rest der Engines laeuft trotzdem weiter. CloudBlocked
    wird NICHT abgefangen (siehe privacy_guard.py: darf niemals innerhalb
    der Pipeline verschluckt werden -- das gilt fuer eine Verifikations-
    Engine genauso wie fuer eine Bulk-Engine). Jede andere Exception wird
    ebenfalls aufgefangen (reason=f"unexpected:{{type}}"), damit eine
    einzelne kaputte Engine nicht die ganze Seite mitreisst."""
    candidates: list[OCRCandidate] = []
    for engine in engines:
        try:
            candidate = engine.recognize(
                prepared,
                region_type=region_type,
                language=language,
                region_id=region_id,
            )
        except EngineError as exc:
            engine_failures.append((engine.name, exc.reason))
            continue
        except CloudBlocked as exc:
            # NIEMALS abfangen (im Sinne von verschlucken) -- muss bis in
            # die HTTP-Schicht durchschlagen (siehe privacy_guard.py
            # Modul-Docstring). Hier aber, VOR dem Weiterreichen, die
            # ausloesende Engine nachtragen, falls sie noch nicht gesetzt
            # ist (z.B. weil assert_local_only() ohne engine=-Argument
            # aufgerufen wurde) -- diese Schleife ist die einzige Stelle,
            # die zuverlaessig weiss, welche Engine gerade lief (siehe
            # store.py's Log-Zeile, die exc.engine dafuer braucht).
            if exc.engine is None:
                exc.engine = engine.name
            raise
        except Exception as exc:  # noqa: BLE001 -- bewusst weit gefasst, siehe Docstring
            engine_failures.append((engine.name, f"unexpected:{type(exc).__name__}"))
            continue
        candidates.append(candidate)
    return candidates


def _region_needs_verification(
    region: Region,
    bulk_candidates: Sequence[OCRCandidate],
    failed_engines: set[str],
    *,
    config: PipelineConfig,
) -> bool:
    """Entscheidet, ob eine bereits aus den Bulk-Engines gebaute Region einen
    zusaetzlichen, gezielten zweiten Blick verdient (siehe Auftrag "selective
    second reading"). Eine Region gilt als verdaechtig, wenn mindestens EINE
    der folgenden Bedingungen zutrifft:
      - sie traegt bereits eine oder mehrere Diskrepanzen (kritisch oder
        nicht -- beide verdienen einen Blick, siehe consensus._region_status);
      - ihre Uebereinstimmung liegt unter config.min_agreement;
      - die mittlere Konfidenz ihrer Bulk-Kandidaten liegt unter
        config.min_confidence;
      - weniger als zwei Bulk-Engines lieferten ueberhaupt einen Kandidaten
        (nichts oder nur eine Stimme, mit der man vergleichen koennte);
      - eine der als `require_engines` konfigurierten Engines ist fuer genau
        diese Region fehlgeschlagen.
    Eine Region, in der sich zwei unabhaengige Bulk-Engines wortgleich
    einig sind, braucht keine dritte Meinung -- eine, in der sie sich
    widersprechen oder gar nichts liefern, braucht sie am meisten."""
    if len(bulk_candidates) < 2:
        return True
    if region.disagreements:
        return True
    if region.agreement < config.min_agreement:
        return True
    mean_confidence = sum(c.confidence for c in bulk_candidates) / len(bulk_candidates)
    if mean_confidence < config.min_confidence:
        return True
    if failed_engines & set(config.require_engines):
        return True
    return False


def _verify_priority_key(region: Region) -> tuple[int, float]:
    """Sortierschluessel fuer die Budgetierung (siehe
    PipelineConfig.max_verify_regions_per_page): kritische Regionen zuerst
    (0 vor 1), danach aufsteigend nach Uebereinstimmung (am wenigsten einige
    Regionen zuerst)."""
    return (0 if region.has_critical_uncertainty else 1, region.agreement)


def process_page(
    page: PageImage,
    *,
    config: PipelineConfig,
    engines: Sequence[OCREngine],
    on_progress: OnProgress | None = None,
) -> PageResult:
    """Verarbeitet eine einzelne, bereits gerenderte Seite.

    Ablauf (siehe Auftrag, exakte Reihenfolge):
    1. image_quality.assess() -- ist das Ergebnis "blocking", wird SOFORT
       mit status=NEEDS_REVIEW, ohne Regionen und OHNE JEDEN Engine-Aufruf
       zurueckgegeben (siehe Modul-Docstring oben).
    2. segmentation.segment_page() zerlegt die Seite in Regionen.
    3. Pro Region: zuschneiden, EINMAL preprocess.prepare() (nicht pro
       Engine neu), dann JEDE Bulk-Engine aufrufen (`engines`, ausser den in
       `config.verify_engines` benannten -- siehe _recognize_all) und
       consensus.build_region() darueber. Liefert keine Bulk-Engine einen
       Kandidaten, wird trotzdem eine Region MIT LEEREN Kandidaten
       aufgenommen (siehe _empty_region).
    4. Selektive Verifikation (siehe Auftrag "selective second reading" und
       PipelineConfig.verify_engines-Docstring): ueber alle Regionen der
       Seite werden die verdaechtigen ermittelt (_region_needs_verification),
       nach Prioritaet sortiert (_verify_priority_key: kritische zuerst,
       dann niedrigste Uebereinstimmung) und bis zu
       `config.max_verify_regions_per_page` davon bekommen zusaetzlich JEDE
       in `config.verify_engines` benannte Engine zu sehen. Reicht das
       Budget nicht fuer alle verdaechtigen Regionen, wird das NICHT
       stillschweigend hingenommen: die Seite traegt danach den Grund
       "verify_budget_exhausted", damit eine Lehrkraft weiss, dass manche
       schwachen Regionen keinen zweiten Blick bekamen, statt anzunehmen,
       es sei ohnehin alles gegengeprueft worden. Fuer jede so ausgewaehlte
       Region wird die Region mit den kombinierten (Bulk- + Verifikations-)
       Kandidaten neu ueber consensus.build_region() aufgebaut.
    5. consensus.decide_status() ueber alle (ggf. neu aufgebauten) Regionen
       der Seite.
    """
    quality = image_quality.assess(page.image, target_dpi=config.target_dpi)

    if quality.blocking:
        if on_progress:
            on_progress(1.0, f"Seite {page.index + 1}: Bildqualität reicht nicht -- Aufnahme wiederholen")
        return PageResult(
            index=page.index,
            width=page.width,
            height=page.height,
            quality=quality,
            regions=(),
            status=OCRStatus.NEEDS_REVIEW,
            auto_clean=False,
            engine_failures=(),
            status_reasons=("image_quality",),
        )

    region_specs = segmentation.segment_page(page.image, page_index=page.index)
    critical_config = CriticalTokenConfig.for_subject(config.subject)

    bulk_engines = [engine for engine in engines if engine.name not in config.verify_engines]
    verify_engines = [engine for engine in engines if engine.name in config.verify_engines]

    engine_failures: list[tuple[str, str]] = []
    regions: list[Region] = []
    region_meta: list[dict[str, Any]] = []
    total_regions = len(region_specs)

    for region_index, (region_id, region_type, bbox) in enumerate(region_specs):
        if on_progress:
            fraction = region_index / total_regions if total_regions else 0.0
            on_progress(fraction, f"Region {region_index + 1}/{total_regions} wird gelesen …")

        crop = page.image.crop(bbox)
        prepared = preprocess.prepare(crop, region_type=region_type, target_dpi=config.target_dpi)

        failures_before = len(engine_failures)
        candidates = _recognize_all(
            bulk_engines,
            prepared,
            region_type=region_type,
            language=config.language,
            region_id=region_id,
            engine_failures=engine_failures,
        )
        failed_engines = {name for name, _reason in engine_failures[failures_before:]}

        if candidates:
            region = build_region(
                region_id,
                region_type,
                bbox,
                candidates,
                config=critical_config,
                classification=config.classification,
            )
        else:
            region = _empty_region(region_id, region_type, bbox)
        regions.append(region)
        region_meta.append(
            {
                "prepared": prepared,
                "region_id": region_id,
                "region_type": region_type,
                "bbox": bbox,
                "bulk_candidates": candidates,
                "failed_engines": failed_engines,
            }
        )

    verify_budget_exhausted = False
    if verify_engines:
        suspicious_indices = [
            index
            for index, (region, meta) in enumerate(zip(regions, region_meta))
            if _region_needs_verification(
                region, meta["bulk_candidates"], meta["failed_engines"], config=config
            )
        ]
        ranked_indices = sorted(suspicious_indices, key=lambda index: _verify_priority_key(regions[index]))
        selected_indices = ranked_indices[: config.max_verify_regions_per_page]
        verify_budget_exhausted = len(ranked_indices) > len(selected_indices)

        for index in selected_indices:
            meta = region_meta[index]
            verify_candidates = _recognize_all(
                verify_engines,
                meta["prepared"],
                region_type=meta["region_type"],
                language=config.language,
                region_id=meta["region_id"],
                engine_failures=engine_failures,
            )
            if not verify_candidates:
                # Region wurde fuer die selektive zweite Lesung ausgewaehlt,
                # aber JEDE Verifikations-Engine ist mit EngineError
                # gescheitert (siehe engine_failures oben) -- die Region
                # bleibt beim reinen Bulk-Ergebnis. Ohne diesen Marker waere
                # das von "verifiziert, sauber befunden" nicht unterscheidbar
                # (siehe Auftrag/Region.verify_failed-Docstring).
                regions[index].verify_failed = True
                continue

            combined_candidates = [*meta["bulk_candidates"], *verify_candidates]
            regions[index] = build_region(
                meta["region_id"],
                meta["region_type"],
                meta["bbox"],
                combined_candidates,
                config=critical_config,
                classification=config.classification,
            )

    status, auto_clean, reasons = decide_status(
        regions,
        quality=quality,
        engine_failures=tuple(engine_failures),
        require_engines=config.require_engines,
        config=critical_config,
        classification=config.classification,
        min_agreement=config.min_agreement,
        min_confidence=config.min_confidence,
        auto_approve=config.auto_approve,
    )

    if verify_budget_exhausted:
        # Angehaengt statt an decide_status() uebergeben: consensus.py bleibt
        # unveraendert (siehe Auftrag-Scope), und jede Bedingung, die eine
        # Region ueberhaupt verdaechtig macht (kritische Diskrepanz, geringe
        # Uebereinstimmung, geringe Konfidenz, fehlende Pflicht-Engine),
        # erzeugt bereits ihren eigenen decide_status()-Grund -- reasons ist
        # in diesem Fall also nie leer, auto_clean bleibt konsistent False.
        reasons = reasons + ("verify_budget_exhausted",)

    if on_progress:
        on_progress(1.0, f"Seite {page.index + 1}: ausgewertet")

    return PageResult(
        index=page.index,
        width=page.width,
        height=page.height,
        quality=quality,
        regions=tuple(regions),
        status=status,
        auto_clean=auto_clean,
        engine_failures=tuple(engine_failures),
        status_reasons=reasons,
    )


def process_pages(
    pages: Iterable[PageImage],
    *,
    config: PipelineConfig,
    engines: Sequence[OCREngine],
    on_page: OnPage | None = None,
    on_progress: OnProgress | None = None,
) -> list[PageResult]:
    """Verarbeitet mehrere bereits gerenderte Seiten der Reihe nach.

    Iteriert `pages` als Iterator (nicht `list(pages)`), sodass eine
    generatorische Quelle weiterhin nur eine Seite gleichzeitig im Speicher
    haelt -- siehe process_document()-Docstring zur Speicherbegruendung.
    `total` fuer die Fortschrittsanzeige ist nur bekannt, wenn `pages`
    `__len__` unterstuetzt (z.B. eine bereits materialisierte Liste); bei
    einer echten generatorischen Quelle bleibt der Seitenanteil des Labels
    ohne "/Gesamt"."""
    total = len(pages) if hasattr(pages, "__len__") else None  # type: ignore[arg-type]
    results: list[PageResult] = []

    for page in pages:
        inner_on_progress = _wrap_page_progress(page.index, total, config.max_pages, on_progress)
        result = process_page(page, config=config, engines=engines, on_progress=inner_on_progress)
        results.append(result)
        if on_page:
            on_page(page.index, result)

    return results


def _wrap_page_progress(
    page_index: int,
    total_pages: int | None,
    max_pages: int,
    on_progress: OnProgress | None,
) -> OnProgress | None:
    """Baut den `on_progress`-Callback fuer eine einzelne Seite innerhalb
    eines mehrseitigen Laufs: haengt "Seite N[/Gesamt] · " vor das von
    process_page() gelieferte Label und rechnet dessen 0..1-Seitenanteil in
    einen Gesamt-Fortschritt um. Ist die Gesamtseitenzahl nicht im Voraus
    bekannt (echte generatorische Quelle, siehe process_document), wird
    `max_pages` als konservativer Naeherungsnenner verwendet -- das ist eine
    Schaetzung, kein exakter Fortschritt, da process_document() bewusst
    nicht vorab durchzaehlt (das wuerde die Lazy-Garantie brechen)."""
    if on_progress is None:
        return None

    denominator = total_pages if total_pages else max(max_pages, 1)
    page_label = f"Seite {page_index + 1}/{total_pages}" if total_pages else f"Seite {page_index + 1}"

    def _inner(fraction: float, label: str) -> None:
        overall = min(1.0, (page_index + fraction) / denominator)
        on_progress(overall, f"{page_label} · {label}")

    return _inner


def _document_status(page_results: Sequence[PageResult]) -> OCRStatus:
    """Leitet den Dokumentstatus aus den Seitenstatus ab (siehe Auftrag):
    FAILED nur, wenn ALLE Seiten fehlgeschlagen sind; sonst NEEDS_REVIEW,
    wenn mindestens eine Seite NEEDS_REVIEW ist; APPROVED nur, wenn
    AUSNAHMSLOS jede Seite APPROVED ist (das kann laut consensus.decide_status
    ohnehin nur nicht-schuelerbezogenes Material mit explizitem
    auto_approve=True erreichen). Jede andere Mischung (z.B. FAILED neben
    APPROVED, aber keine NEEDS_REVIEW-Seite) faellt sicherheitshalber auf
    NEEDS_REVIEW zurueck -- eine fehlgeschlagene Seite verdient immer einen
    Blick, auch wenn andere Seiten sauber durchliefen."""
    if not page_results:
        return OCRStatus.NEEDS_REVIEW
    if all(p.status is OCRStatus.FAILED for p in page_results):
        return OCRStatus.FAILED
    if any(p.status is OCRStatus.NEEDS_REVIEW for p in page_results):
        return OCRStatus.NEEDS_REVIEW
    if all(p.status is OCRStatus.APPROVED for p in page_results):
        return OCRStatus.APPROVED
    return OCRStatus.NEEDS_REVIEW


def process_document(
    source: Path | bytes | Iterable[PageImage],
    *,
    job_id: str,
    source_name: str,
    config: PipelineConfig,
    engines: Sequence[OCREngine],
    on_page: OnPage | None = None,
    on_progress: OnProgress | None = None,
) -> DocumentResult:
    """Verarbeitet ein ganzes Dokument (PDF-Pfad, Bild-Bytes oder eine
    bereits vorbereitete Iterable[PageImage] -- z.B. in Tests).

    MUSS Seiten lazy konsumieren: fuer `Path`/`bytes` wird
    `page_render.load_pages()` (ein Generator) verwendet und per einfacher
    `for`-Schleife durchlaufen, NIE per `list(load_pages(...))`. Nach jeder
    verarbeiteten Seite wird `on_page(index, page_result)` aufgerufen und
    danach die lokale `page`-Bindung explizit mit `del page` entfernt, BEVOR
    die Schleife die naechste Seite vom Generator anfordert -- so ist das
    Bild der vorigen Seite garantiert freigegeben, bevor das der naechsten
    gerendert wird (siehe Auftrag: eine 350-dpi-A4-Seite ist ~35 MB, 40
    Seiten eager waeren ~1.4 GB)."""
    if isinstance(source, Path):
        pages_source: Iterable[PageImage] = load_pages(
            source, target_dpi=config.target_dpi, max_pages=config.max_pages
        )
    elif isinstance(source, (bytes, bytearray)):
        pages_source = load_pages(
            bytes(source), target_dpi=config.target_dpi, max_pages=config.max_pages
        )
    else:
        pages_source = source

    page_results: list[PageResult] = []
    for page in pages_source:
        inner_on_progress = _wrap_page_progress(page.index, None, config.max_pages, on_progress)
        result = process_page(page, config=config, engines=engines, on_progress=inner_on_progress)
        page_results.append(result)
        if on_page:
            on_page(page.index, result)
        # Referenz auf das PIL-Bild dieser Seite entfernen, BEVOR die
        # Schleife die naechste Seite vom Generator anfordert (siehe
        # Docstring oben) -- nicht erst am Ende der Funktion.
        del page

    return DocumentResult(
        job_id=job_id,
        source_name=source_name,
        classification=config.classification,
        created_at=time.time(),
        pages=page_results,
        status=_document_status(page_results),
    )


def process_student_pdf(
    path: Path,
    *,
    config: PipelineConfig | None = None,
    engines: Sequence[OCREngine] | None = None,
    on_page: OnPage | None = None,
    on_progress: OnProgress | None = None,
) -> DocumentResult:
    """Bequemlichkeits-Wrapper um process_document() fuer den Standardfall
    "Schuelerarbeit als PDF hochgeladen": `config` defaultet auf
    `PipelineConfig()` (classification="student_submission"), `engines` auf
    `build_engines({})` (also DEFAULT_ENGINES). `job_id` wird hier selbst
    erzeugt (kein Job-Store beteiligt, siehe store.py fuer die
    Store-integrierte Variante) -- rein informativ als Kontext, nicht als
    stabile, wiederverwendbare ID gedacht."""
    from .engines import build_engines

    resolved_config = config or PipelineConfig()
    resolved_engines = engines if engines is not None else build_engines({})

    return process_document(
        path,
        job_id=f"adhoc-{uuid.uuid4().hex[:12]}",
        source_name=path.name,
        config=resolved_config,
        engines=resolved_engines,
        on_page=on_page,
        on_progress=on_progress,
    )


def process_single_image_sync(
    image_bytes: bytes,
    *,
    config: PipelineConfig,
    engines: Sequence[OCREngine],
    timeout_s: int = 90,
) -> DocumentResult:
    """Verarbeitet ein einzelnes Bild synchron, mit harter Zeitbegrenzung.

    Da die Pipeline selbst rein synchron ist (kein async, kein Cancel-Punkt
    innerhalb einer Engine), laeuft process_document() in einem eigenen
    Worker-Thread; ueberschreitet er `timeout_s`, wird sofort ein
    FAILED-Ergebnis zurueckgegeben. EINSCHRAENKUNG: Python-Threads lassen
    sich nicht hart abbrechen -- der Worker-Thread laeuft im Hintergrund
    weiter, bis die Engine selbst zurueckkehrt; nur der Aufrufer wartet
    nicht laenger darauf. Das ist fuer den vorgesehenen Anwendungsfall
    (ein einzelnes Foto, HTTP-Anfrage mit Timeout) akzeptabel."""
    job_id = f"sync-{uuid.uuid4().hex[:12]}"
    if not _sync_ocr_slot.acquire(blocking=False):
        raise OCRBusy("Eine frühere OCR-Anfrage wird noch beendet.")
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        process_document,
        image_bytes,
        job_id=job_id,
        source_name="single_image",
        config=config,
        engines=engines,
    )

    def release_slot(_future):
        _sync_ocr_slot.release()
        executor.shutdown(wait=False)

    future.add_done_callback(release_slot)
    try:
        return future.result(timeout=timeout_s)
    except FutureTimeoutError:
        # The worker cannot be forcibly stopped in Python.  The callback keeps
        # the one request slot occupied until it exits, while this HTTP request
        # returns immediately.
        return DocumentResult(
            job_id=job_id,
            source_name="single_image",
            classification=config.classification,
            created_at=time.time(),
            pages=[],
            status=OCRStatus.FAILED,
            error=f"Zeitüberschreitung nach {timeout_s}s",
        )
