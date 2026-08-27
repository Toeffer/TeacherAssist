"""Testet den OCR-Job-Store (Stufe 4b des OCR-Refactors).

Deckt teacherassist_core/ocr/store.py ab: OCRJobStore.create (Hintergrund-
Verarbeitung, Zeile ~ "def create"), get/list/snapshot, patch_region,
approve (inkl. ApprovalRefused), delete/purge_expired, den
Pfadtraversal-Schutz (_resolve_job_dir, spiegelt tool_server.py's
_download_export bei Zeile ~1239) und page_png.

Alle Tests laufen gegen FakeEngine (engines/fake.py) -- kein echtes Modell,
keine GPU, kein Tesseract-Binary. Jede Polling-Schleife hat ein Timeout,
damit eine Regression den Test scheitern laesst statt die gesamte
Test-Suite haengen zu lassen.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time

import pytest

from teacherassist_core.ocr.engines import FakeEngine
from teacherassist_core.ocr.pipeline import PipelineConfig, process_document
from teacherassist_core.ocr.privacy_guard import CloudBlocked
from teacherassist_core.ocr.store import (
    CLOUD_BLOCKED_ERROR_CODE,
    ApprovalNotReady,
    ApprovalRefused,
    EmptyPatchError,
    OCRJobStore,
)
from teacherassist_core.ocr.types import (
    DocumentResult,
    ImageQuality,
    OCRStatus,
    PageResult,
    Region,
    RegionType,
)

POLL_TIMEOUT_S = 5.0
POLL_INTERVAL_S = 0.02


def _wait_until_done(store: OCRJobStore, job_id: str, *, timeout: float = POLL_TIMEOUT_S):
    """Pollt store.get(job_id), bis der Status PROCESSING verlaesst.
    Bricht nach `timeout` Sekunden mit einer Testfehlermeldung ab, statt
    die Suite haengen zu lassen (siehe Auftrag: "Every polling loop has a
    timeout")."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        doc = store.get(job_id)
        assert doc is not None
        if doc.status is not OCRStatus.PROCESSING:
            return doc
        time.sleep(POLL_INTERVAL_S)
    pytest.fail(f"Job {job_id} hat PROCESSING nicht innerhalb von {timeout}s verlassen")


def _make_image_bytes() -> bytes:
    """Ein echtes PNG (kein PDF) als Quelle fuer create() -- mit
    schwarzen Balken auf weissem Grund, damit image_quality.assess() es
    NICHT als "blocking" (zu unscharf/zu klein) einstuft und
    segmentation.segment_page() tatsaechlich Zeilen-Regionen findet (ein
    komplett leeres weisses Bild waere zu unscharf: blur_score=0 -> die
    Seite wuerde blockieren, bevor ueberhaupt eine Engine aufgerufen wird).
    page_render.load_pages() erkennt den Nicht-PDF-Header und oeffnet es
    per PIL als Einzelbild."""
    import io

    from PIL import Image, ImageDraw

    image = Image.new("RGB", (400, 300), color="white")
    draw = ImageDraw.Draw(image)
    y = 40
    for _ in range(6):
        draw.rectangle([40, y, 360, y + 18], fill="black")
        y += 40

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _make_single_line_image_bytes() -> bytes:
    """Wie _make_image_bytes(), aber mit GENAU einem schwarzen Balken --
    segmentation.segment_page() findet dann genau eine Region, statt
    mehrerer. Die approve()-Tests brauchen das: FakeEngine im str-Modus
    liefert fuer JEDE Region denselben Text (siehe engines/fake.py), mit
    mehreren Regionen haette also jede dieselbe kritische Diskrepanz, und
    "nach Klaerung EINER Region freigeben" waere mit mehreren identischen
    Diskrepanzen nicht mehr eindeutig zu testen."""
    import io

    from PIL import Image, ImageDraw

    image = Image.new("RGB", (400, 300), color="white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 100, 360, 118], fill="black")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class _CloudBlockedEngine:
    """Minimal-Attrappe (nicht FakeEngine, siehe engines/fake.py --
    FakeEngine kann kein CloudBlocked werfen), die in recognize() sofort
    CloudBlocked wirft. Implementiert nur, was das OCREngine-Protocol
    (engines/base.py) und process_page() (pipeline.py) tatsaechlich
    brauchen, damit der Fehler exakt denselben Pfad wie eine echte
    Cloud-Engine nimmt (siehe pipeline.py:process_page, `except
    CloudBlocked: raise`)."""

    name = "cloud-fake"
    kind = "fake"
    capabilities = {"cpu": True, "cuda": False, "vulkan": False, "xpu": False, "rocm": False}

    def is_available(self) -> bool:
        return True

    def status(self):
        from teacherassist_core.ocr.engines.base import EngineStatus

        return EngineStatus(
            name=self.name,
            kind="fake",
            available=True,
            reason="",
            model_id=self.name,
            capabilities=self.capabilities,
        )

    def supports(self, region_type) -> bool:
        return True

    def recognize(self, image, *, region_type, language="deu", region_id=None):
        raise CloudBlocked("student_submission", "https://example.invalid/ocr")

    def warmup(self) -> None:
        return None


@pytest.fixture
def store(tmp_path):
    instance = OCRJobStore(tmp_path / "ocr-root", max_workers=1)
    yield instance
    instance.shutdown()


def test_create_returns_processing_then_completes(store):
    """OCRJobStore.create() muss SOFORT ein DocumentResult mit
    status=PROCESSING liefern (der Hintergrund-Worker laeuft asynchron) --
    gepollt ueber get() muss der Job innerhalb der Timeout-Frist einen
    Endstatus erreichen (siehe _wait_until_done)."""
    engine = FakeEngine("tesseract", "Hallo Welt")
    config = PipelineConfig(require_engines=())

    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    assert stub.status is OCRStatus.PROCESSING

    finished = _wait_until_done(store, stub.job_id)
    assert finished.status in (OCRStatus.NEEDS_REVIEW, OCRStatus.APPROVED, OCRStatus.FAILED)


def test_job_survives_reload_from_disk(tmp_path):
    """Ein zweiter OCRJobStore auf demselben `root` muss den bereits
    abgeschlossenen Job wiederfinden (Write-Through-Cache + job.json,
    siehe Modul-Docstring: "survives a restart mid-batch")."""
    root = tmp_path / "ocr-root"
    engine = FakeEngine("tesseract", "Hallo Welt")
    config = PipelineConfig(require_engines=())

    first_store = OCRJobStore(root, max_workers=1)
    try:
        stub = first_store.create(
            source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
        )
        _wait_until_done(first_store, stub.job_id)
    finally:
        first_store.shutdown()

    second_store = OCRJobStore(root, max_workers=1)
    try:
        reloaded = second_store.get(stub.job_id)
        assert reloaded is not None
        assert reloaded.job_id == stub.job_id
        assert reloaded.source_name == "scan.png"
    finally:
        second_store.shutdown()


def test_disagreement_char_offsets_survive_reload_from_disk(store):
    """Disagreement.char_start/char_end (die exakte Zeichenspanne der
    "[...]"-Klammer in Region.consensus_text, siehe render_consensus_with_offsets)
    muessen den Umweg ueber job.json unveraendert ueberstehen -- ohne
    _serialize_disagreement/_deserialize_disagreement wuerden sie beim
    Neuladen (Serverneustart, oder schlicht ein zweiter OCRJobStore auf
    demselben root) stillschweigend auf den -1/-1-Default zurueckfallen,
    und die Review-UI wuerde die komplette Hervorhebung verlieren, ohne
    jeden Hinweis darauf. Prueft nicht nur, dass die beiden Zahlen den
    Roundtrip ueberleben, sondern dass sie danach immer noch dasselbe
    BEDEUTEN: consensus_text[char_start:char_end] muss nach dem Reload
    exakt dieselbe gerenderte Klammer ergeben wie vorher."""
    job_id, region_id = _create_two_region_job(store)
    original_region = next(
        r for p in store.get(job_id).pages for r in p.regions if r.id == region_id
    )
    original_disagreement = original_region.disagreements[0]
    assert original_disagreement.char_start != -1
    assert original_disagreement.char_end != -1
    original_slice = original_region.consensus_text[
        original_disagreement.char_start : original_disagreement.char_end
    ]
    assert original_slice.startswith("[")
    assert original_slice.endswith("]")

    reloaded_store = OCRJobStore(store.root, max_workers=1)
    try:
        reloaded_doc = reloaded_store.get(job_id)
        assert reloaded_doc is not None
        reloaded_region = next(
            r for p in reloaded_doc.pages for r in p.regions if r.id == region_id
        )
        reloaded_disagreement = reloaded_region.disagreements[0]

        assert reloaded_disagreement.char_start == original_disagreement.char_start
        assert reloaded_disagreement.char_end == original_disagreement.char_end
        assert reloaded_region.consensus_text == original_region.consensus_text

        reloaded_slice = reloaded_region.consensus_text[
            reloaded_disagreement.char_start : reloaded_disagreement.char_end
        ]
        assert reloaded_slice == original_slice
    finally:
        reloaded_store.shutdown()


def test_disagreement_char_offsets_default_when_absent_from_job_json(store):
    """Ein `job.json`, das VOR der charStart/charEnd-Ergaenzung geschrieben
    wurde (oder aus einem anderen Grund keine dieser Schluessel traegt),
    darf beim Neuladen NICHT mit KeyError abstuerzen -- das wuerde den
    GANZEN Job mitreissen (siehe _load_existing). _deserialize_disagreement
    muss auf den dokumentierten -1/-1-Default zurueckfallen."""
    job_id, region_id = _create_two_region_job(store)

    job_json_path = store.root / job_id / "job.json"
    payload = json.loads(job_json_path.read_text(encoding="utf-8"))
    for page in payload["document"]["pages"]:
        for region in page["regions"]:
            for disagreement in region["disagreements"]:
                disagreement.pop("charStart", None)
                disagreement.pop("charEnd", None)
    job_json_path.write_text(json.dumps(payload), encoding="utf-8")

    reloaded_store = OCRJobStore(store.root, max_workers=1)
    try:
        reloaded_doc = reloaded_store.get(job_id)
        assert reloaded_doc is not None
        reloaded_region = next(
            r for p in reloaded_doc.pages for r in p.regions if r.id == region_id
        )
        reloaded_disagreement = reloaded_region.disagreements[0]
        assert reloaded_disagreement.char_start == -1
        assert reloaded_disagreement.char_end == -1
    finally:
        reloaded_store.shutdown()


@pytest.mark.parametrize(
    "malicious_id",
    [
        "../../etc/passwd",
        "..\\..\\windows",
        "/etc/passwd",
        "a" * 65,
    ],
)
def test_path_traversal_rejected(store, malicious_id):
    """Jede job_id-nehmende Methode muss eine boesartige ID ablehnen, OHNE
    ausserhalb von `root` etwas anzufassen (siehe Modul-Docstring:
    doppelte Pruefung -- Zeichenklasse UND job_dir.resolve().relative_to(
    self.root.resolve()), spiegelt tool_server.py:_download_export)."""
    assert store.get(malicious_id) is None
    assert store.delete(malicious_id) is False
    assert store.patch_region(malicious_id, "p0-r0", text="x") is None
    assert store.page_png(malicious_id, 0) is None
    # approve() darf fuer eine unbekannte/boesartige ID nicht ApprovalRefused
    # werfen (das waere fuer eine ID, die wir gar nicht auflösen koennen,
    # der falsche Fehlerkanal) -- es liefert None wie die anderen Methoden.
    assert store.approve(malicious_id) is None

    # Nichts ausserhalb des Stores darf beruehrt worden sein.
    assert not (store.root.parent / "passwd").exists()
    assert not (store.root.parent / "windows").exists()


def _create_two_region_job(store) -> tuple[str, str, str]:
    """Baut einen Job mit zwei Regionen, deren Konsens durch zwei
    widerspruechliche Engines eine kritische Diskrepanz ("nicht" vs. "")
    produziert -- die Grundlage fuer die approve()-Tests. Gibt
    (job_id, region_id_kritisch, region_id_unkritisch) zurueck."""
    # "nicht" muss im Text der REFERENZ-Engine stehen (htr hat hoehere
    # ENGINE_PRIORITY als tesseract, siehe consensus.py:22, wird also
    # Referenz): eine fehlende Referenz-Spanne (delete-Op) registriert
    # collect_disagreements zuverlaessig, waehrend eine reine Einfuegung
    # AUF Referenzseite (insert-Op, Nullbreite auf Referenzseite) an der
    # Segmentgrenze mit dem vorangehenden equal-Block kollabiert -- siehe
    # tests/test_ocr_consensus.py::test_negation_disagreement_is_critical,
    # das exakt demselben Muster folgt.
    engine_a = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    engine_b = FakeEngine("tesseract", "Die Kraft ist konstant.")
    config = PipelineConfig(require_engines=())

    stub = store.create(
        source=_make_single_line_image_bytes(), source_name="kritisch.png", config=config,
        engines=[engine_a, engine_b],
    )
    doc = _wait_until_done(store, stub.job_id)
    assert doc.pages, "Erwartet mindestens eine verarbeitete Seite"
    critical_regions = [r for p in doc.pages for r in p.regions if r.has_critical_uncertainty]
    assert critical_regions, "Testaufbau erwartet eine kritische Diskrepanz (nicht vs. leer)"
    return stub.job_id, critical_regions[0].id


def test_patch_region_sets_edited_by_teacher(store):
    """patch_region(text=...) (store.py) setzt selected_text UND markiert
    edited_by_teacher=True."""
    job_id, region_id = _create_two_region_job(store)

    patched = store.patch_region(job_id, region_id, text="Die Kraft ist konstant.")

    assert patched is not None
    assert patched.selected_text == "Die Kraft ist konstant."
    assert patched.edited_by_teacher is True

    # Persistenz: nach erneutem Laden aus dem Cache bleibt die Aenderung.
    reloaded_region = next(
        r for p in store.get(job_id).pages for r in p.regions if r.id == region_id
    )
    assert reloaded_region.selected_text == "Die Kraft ist konstant."
    assert reloaded_region.edited_by_teacher is True


def test_patch_region_with_candidate_engine(store):
    """patch_region(candidate_engine=...) uebernimmt den Text GENAU dieses
    Kandidaten in selected_text und markiert edited_by_teacher=True; ein
    unbekannter Enginename wird abgelehnt (ValueError), statt die Region
    unveraendert zu lassen (siehe store.py:patch_region-Docstring)."""
    job_id, region_id = _create_two_region_job(store)

    patched = store.patch_region(job_id, region_id, candidate_engine="tesseract")
    assert patched is not None
    assert patched.edited_by_teacher is True
    tesseract_candidate = next(c for c in patched.candidates if c.engine == "tesseract")
    assert patched.selected_text == tesseract_candidate.text

    with pytest.raises(ValueError):
        store.patch_region(job_id, region_id, candidate_engine="does-not-exist")


def test_patch_region_rejects_empty_patch(store):
    """patch_region() mit WEDER `text` NOCH `candidate_engine` muss
    EmptyPatchError werfen, statt die Region unveraendert zurueckzuliefern
    (siehe Auftrag Fix 1: ein solcher No-op-PATCH war zuvor ueber
    tool_server.py:_patch_ocr_region der EINZIGE Weg, unfreigegebenen
    Transkripttext auszulesen, weil dort include_text hartkodiert war).
    Die Region bleibt dabei unveraendert (edited_by_teacher weiterhin
    False) -- ein abgelehnter Patch ist keine (Teil-)Mutation."""
    job_id, region_id = _create_two_region_job(store)

    with pytest.raises(EmptyPatchError):
        store.patch_region(job_id, region_id)

    # EmptyPatchError ist auch ein ValueError (siehe Docstring), damit
    # bestehender `except ValueError`-Code weiterhin greift.
    with pytest.raises(ValueError):
        store.patch_region(job_id, region_id)

    reloaded_region = next(
        r for p in store.get(job_id).pages for r in p.regions if r.id == region_id
    )
    assert reloaded_region.edited_by_teacher is False


def test_approve_refused_while_critical_unresolved(store):
    """approve() muss ApprovalRefused werfen, solange irgendeine Region
    noch eine ungeklaerte kritische Diskrepanz hat (edited_by_teacher=False)
    -- siehe store.py:approve-Docstring fuer die Design-Entscheidung
    "Exception statt stillem needs_review-Ergebnis"."""
    job_id, region_id = _create_two_region_job(store)

    with pytest.raises(ApprovalRefused) as exc_info:
        store.approve(job_id)
    assert region_id in exc_info.value.region_ids

    # Der Job selbst bleibt unveraendert im needs_review-Zustand.
    assert store.get(job_id).status is not OCRStatus.APPROVED


def test_approve_succeeds_after_resolution(store):
    """Nachdem die kritische Region per patch_region() geklaert wurde,
    muss approve() durchgehen und der Volltext danach ueber to_dict()
    tatsaechlich sichtbar sein (types.py-Sicherheits-Choke-Point: erst nach
    APPROVED wird Text ausgeliefert)."""
    job_id, region_id = _create_two_region_job(store)

    store.patch_region(job_id, region_id, text="Geklärter Text.")
    approved = store.approve(job_id)

    assert approved is not None
    assert approved.status is OCRStatus.APPROVED
    data = approved.to_dict()
    assert data["pages"][0]["text"] is not None
    assert "Geklärter Text." in data["pages"][0]["text"]


def test_approve_refuses_processing_job(store, monkeypatch):
    """approve() muss ablehnen, solange der Job noch PROCESSING ist --
    sonst waere die kritische-Diskrepanz-Pruefung in approve() vacuous
    (PROCESSING-Jobs haben eine LEERE pages-Liste, also per Definition
    keine ungeklaerten kritischen Regionen) und die Freigabe ginge still
    durch, ohne dass irgendein Inhalt vorhanden ist."""
    import teacherassist_core.ocr.store as store_module

    release = threading.Event()

    def _blocking_process_document(*args, **kwargs):
        release.wait(POLL_TIMEOUT_S)
        raise RuntimeError("sollte in diesem Test nie tatsaechlich verarbeitet werden")

    monkeypatch.setattr(store_module, "process_document", _blocking_process_document)

    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    assert stub.status is OCRStatus.PROCESSING

    try:
        with pytest.raises(ApprovalNotReady) as exc_info:
            store.approve(stub.job_id)
        assert exc_info.value.status is OCRStatus.PROCESSING
        # Der Job selbst bleibt unveraendert im PROCESSING-Zustand.
        assert store.get(stub.job_id).status is OCRStatus.PROCESSING
    finally:
        release.set()
        _wait_until_done(store, stub.job_id)


def test_approve_refuses_failed_job(store, monkeypatch):
    """approve() muss ebenso ablehnen, wenn der Job bereits FAILED ist --
    auch hier waere die kritische-Diskrepanz-Pruefung sonst vacuous (leere
    pages-Liste)."""
    import teacherassist_core.ocr.store as store_module

    def _boom(*args, **kwargs):
        raise RuntimeError("Pipeline explodiert absichtlich für diesen Test")

    monkeypatch.setattr(store_module, "process_document", _boom)

    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="kaputt.png", config=config, engines=[engine]
    )
    failed = _wait_until_done(store, stub.job_id)
    assert failed.status is OCRStatus.FAILED

    with pytest.raises(ApprovalNotReady) as exc_info:
        store.approve(stub.job_id)
    assert exc_info.value.status is OCRStatus.FAILED

    # Der Job selbst bleibt unveraendert im FAILED-Zustand.
    assert store.get(stub.job_id).status is OCRStatus.FAILED


def test_approve_still_refuses_unresolved_critical(store):
    """Die bestehende Ablehnung wegen ungeklaerter kritischer Diskrepanz
    (ApprovalRefused) bleibt unveraendert bestehen und ist von der neuen
    ApprovalNotReady-Ablehnung (Job nicht im Status needs_review)
    unterscheidbar -- ein Job MIT Inhalt (needs_review, unresolved
    critical) darf niemals denselben Fehlerkanal nehmen wie ein Job OHNE
    Inhalt (processing/failed)."""
    job_id, region_id = _create_two_region_job(store)

    assert store.get(job_id).status is OCRStatus.NEEDS_REVIEW

    with pytest.raises(ApprovalRefused) as exc_info:
        store.approve(job_id)
    assert region_id in exc_info.value.region_ids

    # Der Job selbst bleibt unveraendert im needs_review-Zustand.
    assert store.get(job_id).status is OCRStatus.NEEDS_REVIEW


def test_purge_expired_removes_old_jobs_only(store):
    """purge_expired(retention_days) entfernt (per shutil.rmtree) nur
    Jobs, deren created_at aelter als die Aufbewahrungsfrist ist -- ein
    frischer Job bleibt unberuehrt."""
    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())

    old_stub = store.create(
        source=_make_image_bytes(), source_name="alt.png", config=config, engines=[engine]
    )
    _wait_until_done(store, old_stub.job_id)
    # created_at kuenstlich in die Vergangenheit versetzen, um Alter zu simulieren.
    with store._lock:
        store._cache[old_stub.job_id].created_at = time.time() - 100 * 86400
    store._persist(old_stub.job_id)

    fresh_stub = store.create(
        source=_make_image_bytes(), source_name="neu.png", config=config, engines=[engine]
    )
    _wait_until_done(store, fresh_stub.job_id)

    removed = store.purge_expired(retention_days=30)

    assert removed == 1
    assert store.get(old_stub.job_id) is None
    assert store.get(fresh_stub.job_id) is not None
    assert not (store.root / old_stub.job_id).exists()
    assert (store.root / fresh_stub.job_id).exists()


def test_purge_expired_does_not_race_with_concurrent_patch_region(store):
    """Ein Job an seiner Aufbewahrungsgrenze, den eine Lehrkraft gerade
    aktiv patcht, darf niemals halb geloescht werden (siehe Auftrag Fix 5):
    purge_expired()'s Pop-aus-Cache UND `shutil.rmtree` laufen jetzt unter
    DEMSELBEN Lock wie patch_region()'s Lesen+Mutieren+Persistieren, daher
    kann eine laufende Mutation nie von der Loeschung ueberholt werden.

    Treibt mehrere Threads an, die denselben Job unentwegt patchen,
    waehrend parallel wiederholt purge_expired() laeuft, und prueft nach
    jedem Durchlauf: der Job ist entweder VOLLSTAENDIG vorhanden
    (Verzeichnis UND job.json UND darin lesbar der zuletzt persistierte
    Regionstext) oder VOLLSTAENDIG verschwunden (weder Cache-Eintrag noch
    Verzeichnis) -- nie ein Zwischenzustand, und patch_region() wirft dabei
    nie eine unerwartete Exception (nur `None`, wenn der Job bereits
    entfernt wurde, ist ein legitimes Ergebnis)."""
    job_id, region_id = _create_two_region_job(store)
    with store._lock:
        store._cache[job_id].created_at = time.time() - 100 * 86400
    store._persist(job_id)

    errors: list[Exception] = []
    stop = threading.Event()

    def _patcher() -> None:
        i = 0
        while not stop.is_set():
            try:
                store.patch_region(job_id, region_id, text=f"Geklärter Text {i}.")
            except Exception as exc:  # noqa: BLE001 -- siehe Docstring: nur
                # `None` (Job schon entfernt) ist erwartet, jede echte
                # Exception hier waere die Korruption, die dieser Test
                # ausschliessen soll.
                errors.append(exc)
            i += 1

    threads = [threading.Thread(target=_patcher) for _ in range(4)]
    for t in threads:
        t.start()

    for _ in range(20):
        store.purge_expired(retention_days=30)

    stop.set()
    for t in threads:
        t.join(timeout=5)

    assert not errors

    job_dir = store.root / job_id
    doc = store.get(job_id)
    if doc is None:
        assert not job_dir.exists(), "Cache sagt geloescht, Verzeichnis existiert aber noch"
    else:
        assert job_dir.exists()
        assert (job_dir / "job.json").exists()
        reloaded_region = next(
            r for p in doc.pages for r in p.regions if r.id == region_id
        )
        assert isinstance(reloaded_region.selected_text, str)
        assert reloaded_region.selected_text.startswith("Geklärter Text")


def test_worker_exception_marks_job_failed_and_keeps_executor_alive(store, monkeypatch):
    """Wirft process_document() (bzw. hier: eine Engine innerhalb davon)
    eine unerwartete Exception, muss der betroffene Job status=FAILED mit
    gesetztem error-Text erreichen, OHNE den (einzigen) Hintergrund-Worker
    mitzureissen -- ein zweiter, danach eingereichter Job muss weiterhin
    normal fertig werden (siehe Auftrag: "Never let a worker exception
    kill the executor")."""
    import teacherassist_core.ocr.store as store_module

    def _boom(*args, **kwargs):
        raise RuntimeError("Pipeline explodiert absichtlich für diesen Test")

    monkeypatch.setattr(store_module, "process_document", _boom)

    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())

    failing_stub = store.create(
        source=_make_image_bytes(), source_name="kaputt.png", config=config, engines=[engine]
    )
    failed = _wait_until_done(store, failing_stub.job_id)
    assert failed.status is OCRStatus.FAILED
    assert failed.error and "explodiert absichtlich" in failed.error

    monkeypatch.undo()

    second_stub = store.create(
        source=_make_image_bytes(), source_name="ok.png", config=config, engines=[engine]
    )
    second_done = _wait_until_done(store, second_stub.job_id)
    assert second_done.status in (OCRStatus.NEEDS_REVIEW, OCRStatus.APPROVED)


def test_page_png_returns_bytes_and_region_crop_is_smaller(store):
    """page_png() liefert PNG-Bytes fuer die volle Seite (auf max. 1600 px
    lange Kante herunterskaliert) und, mit region_id, einen kleineren
    Regionsausschnitt (8 px Rand) -- lazy erzeugt und danach unter
    root/<job_id>/page-{n}.png bzw. region-{rid}.png zwischengespeichert
    (siehe store.py:page_png-Docstring)."""
    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())

    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    doc = _wait_until_done(store, stub.job_id)
    assert doc.pages and doc.pages[0].regions, "Testaufbau erwartet mindestens eine Region"
    region_id = doc.pages[0].regions[0].id

    page_bytes = store.page_png(stub.job_id, 0)
    assert page_bytes is not None
    assert page_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert (store.root / stub.job_id / "page-0.png").exists()

    region_bytes = store.page_png(stub.job_id, 0, region_id=region_id)
    assert region_bytes is not None
    assert region_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(region_bytes) < len(page_bytes)
    assert (store.root / stub.job_id / f"region-{region_id}.png").exists()


def test_cloud_blocked_marks_job_with_distinct_code(store):
    """Wirft eine Engine CloudBlocked (privacy_guard.py -- ein
    Sicherheitsereignis: ein Versuch, Schuelerdaten an einen
    Nicht-Loopback-Endpunkt zu senden), muss der betroffene Job FAILED
    werden, MIT einem eigenen maschinenlesbaren Marker
    (CLOUD_BLOCKED_ERROR_CODE), und Klassifikation/Endpunkt muessen in
    `error` erhalten bleiben -- OHNE als gewoehnlicher
    engine_failure/needs_review behandelt zu werden (siehe
    _run_job-Docstring)."""
    engine = _CloudBlockedEngine()
    config = PipelineConfig(require_engines=())

    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    finished = _wait_until_done(store, stub.job_id)

    assert finished.status is OCRStatus.FAILED
    assert getattr(finished, "error_code", None) == CLOUD_BLOCKED_ERROR_CODE
    assert finished.error is not None
    assert "student_submission" in finished.error
    assert "example.invalid" in finished.error

    # NICHT als gewoehnlicher engine_failure/needs_review-Fall behandelt:
    # ein FAILED-Job hat per _run_job() immer eine leere pages-Liste, kann
    # also gar nicht needs_review sein.
    assert finished.status is not OCRStatus.NEEDS_REVIEW
    assert finished.pages == []

    # Persistenz: nach Reload aus job.json bleibt der Marker erhalten.
    reloaded_store = OCRJobStore(store.root, max_workers=1)
    try:
        reloaded = reloaded_store.get(stub.job_id)
        assert reloaded is not None
        assert getattr(reloaded, "error_code", None) == CLOUD_BLOCKED_ERROR_CODE
    finally:
        reloaded_store.shutdown()


def test_ordinary_crash_is_not_marked_cloud_blocked(store, monkeypatch):
    """Negativ-Kontrolle: ein GEWOEHNLICHER Absturz (RuntimeError, keine
    CloudBlocked) darf NICHT mit CLOUD_BLOCKED_ERROR_CODE markiert werden
    -- sonst waere der Marker aus test_cloud_blocked_marks_job_with_distinct_code
    bedeutungslos."""
    import teacherassist_core.ocr.store as store_module

    def _boom(*args, **kwargs):
        raise RuntimeError("gewoehnlicher Absturz, keine Cloud-Sperre")

    monkeypatch.setattr(store_module, "process_document", _boom)

    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="kaputt.png", config=config, engines=[engine]
    )
    finished = _wait_until_done(store, stub.job_id)

    assert finished.status is OCRStatus.FAILED
    assert getattr(finished, "error_code", None) is None
    assert finished.error and "gewoehnlicher Absturz" in finished.error


@pytest.mark.parametrize(
    "reserved_id",
    ["CON", "NUL", "COM1", "LPT1", "nul", "NUL.txt"],
)
def test_reserved_device_names_rejected(store, reserved_id):
    """Windows-reservierte Geraetenamen (CON/NUL/COM1/LPT1, case-
    insensitiv, auch mit Dateiendung) bestehen JOB_ID_RE (rein
    alphanumerisch) und loesen unter Windows auf echte, immer
    existierende Pfade auf (NUL existiert dort immer) -- muessen also
    zusaetzlich abgelehnt werden. get()/delete()/page_png() muessen alle
    "nicht gefunden" melden, NIE stillschweigend Erfolg vortaeuschen."""
    assert store.get(reserved_id) is None
    assert store.delete(reserved_id) is False
    assert store.page_png(reserved_id, 0) is None


def test_delete_returns_false_for_unknown_job(store):
    """delete() muss False liefern, wenn `job_id` syntaktisch gueltig ist,
    aber nie ein tatsaechlicher, im Store bekannter Job war (siehe
    delete()-Docstring: Cache-Mitgliedschaft entscheidet, nicht nur, ob
    irgendein Pfad zufaellig existiert)."""
    import secrets

    unknown_job_id = secrets.token_urlsafe(24)
    assert store.get(unknown_job_id) is None
    assert store.delete(unknown_job_id) is False


# ---------------------------------------------------------------------------
# Fix A -- error_code als echtes DocumentResult-Feld (types.py)
# ---------------------------------------------------------------------------


def test_error_code_is_a_real_field_and_serialised(store):
    """error_code ist ein echtes Dataclass-Feld auf DocumentResult
    (types.py), kein dynamisch angehaengtes Attribut mehr -- und ueberlebt
    einen Store-Neustart (job.json-Roundtrip via
    _serialize_document/_deserialize_document, siehe store.py)."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(DocumentResult)}
    assert "error_code" in field_names

    engine = _CloudBlockedEngine()
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    finished = _wait_until_done(store, stub.job_id)
    assert finished.error_code == CLOUD_BLOCKED_ERROR_CODE

    # Kein zusaetzliches Warten auf die Platte noetig: _persist_locked()
    # (store.py) schreibt job.json VOR der Cache-Veroeffentlichung, unter
    # demselben Lock, den _wait_until_done() ueber get() ebenfalls nimmt --
    # sobald PROCESSING verlassen wurde, ist der Plattenstand also
    # garantiert schon aktuell (Invariante: der Cache eilt der Platte nie
    # voraus).
    reloaded_store = OCRJobStore(store.root, max_workers=1)
    try:
        reloaded = reloaded_store.get(stub.job_id)
        assert reloaded is not None
        assert reloaded.error_code == CLOUD_BLOCKED_ERROR_CODE
    finally:
        reloaded_store.shutdown()


def test_to_dict_exposes_error_code_without_approval():
    """Der wichtigste Test zu Fix A: errorCode ist in to_dict() SICHTBAR,
    auch wenn der Job NICHT freigegeben ist (FAILED statt APPROVED) --
    waehrend pages[*].text/regions[*].selectedText weiterhin None bleiben
    (include_text haengt AUSSCHLIESSLICH von status==APPROVED ab, siehe
    types.py-Sicherheits-Choke-Point). Diagnose raus, Transkript
    zurueckgehalten."""
    region = Region(
        id="p0-r0",
        type=RegionType.TEXT_LINE,
        bbox=(0, 0, 10, 10),
        candidates=(),
        reference_engine="",
        consensus_text="",
        selected_text="Geheimer Schuelertext",
        disagreements=(),
        agreement=1.0,
        status=OCRStatus.NEEDS_REVIEW,
    )
    page = PageResult(
        index=0,
        width=10,
        height=10,
        quality=ImageQuality.unknown(10, 10),
        regions=(region,),
        status=OCRStatus.NEEDS_REVIEW,
        auto_clean=False,
        engine_failures=(),
    )
    document = DocumentResult(
        job_id="job-cloud-blocked",
        source_name="scan.png",
        classification="student_submission",
        created_at=time.time(),
        pages=[page],
        status=OCRStatus.FAILED,
        error="Cloud-Zugriff blockiert",
        error_code=CLOUD_BLOCKED_ERROR_CODE,
    )

    data = document.to_dict()

    assert data["errorCode"] == CLOUD_BLOCKED_ERROR_CODE
    assert data["pages"][0]["text"] is None
    assert data["pages"][0]["regions"][0]["selectedText"] is None


def test_ordinary_failure_has_null_error_code():
    """Negativ-Kontrolle zu test_to_dict_exposes_error_code_without_approval:
    ein gewoehnlicher Fehlschlag (kein Cloud-Block) hat error_code=None per
    Default UND to_dict() liefert "errorCode": None -- der Marker ist
    ausschliesslich fuer Privacy-Blockierungen reserviert."""
    document = DocumentResult(
        job_id="job-ordinary",
        source_name="kaputt.pdf",
        classification="student_submission",
        created_at=time.time(),
        pages=[],
        status=OCRStatus.FAILED,
        error="Datei ist kein gueltiges PDF",
    )
    assert document.error_code is None
    assert document.to_dict()["errorCode"] is None


# ---------------------------------------------------------------------------
# Fix B -- CloudBlocked benennt die ausloesende Engine
# ---------------------------------------------------------------------------


def test_cloud_blocked_names_the_engine(store):
    """Eine Engine, die CloudBlocked OHNE eigenes engine=-Argument wirft
    (wie _CloudBlockedEngine), bekommt den Namen von pipeline.py automatisch
    nachgetragen (process_page: `except CloudBlocked as exc`), BEVOR die
    Exception weitergereicht wird. Das gilt sowohl direkt durch
    pipeline.process_document() als auch end-to-end durch den Store
    (_run_job faengt an der Executor-Grenze ab): der Engine-Name erreicht
    auch DocumentResult.error (str(exc), siehe privacy_guard.py), statt nur
    "eine der konfigurierten Engines" zu approximieren."""
    engine = _CloudBlockedEngine()
    other_engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())

    with pytest.raises(CloudBlocked) as excinfo:
        process_document(
            _make_image_bytes(),
            job_id="direct-test",
            source_name="scan.png",
            config=config,
            engines=[engine, other_engine],
        )
    assert excinfo.value.engine == _CloudBlockedEngine.name

    stub = store.create(
        source=_make_image_bytes(),
        source_name="scan.png",
        config=config,
        engines=[engine, other_engine],
    )
    finished = _wait_until_done(store, stub.job_id)

    assert finished.status is OCRStatus.FAILED
    assert finished.error_code == CLOUD_BLOCKED_ERROR_CODE
    assert finished.error is not None
    assert _CloudBlockedEngine.name in finished.error


# ---------------------------------------------------------------------------
# Fix C -- verwaiste Job-Ordner bleiben reklamierbar
# ---------------------------------------------------------------------------


def test_purge_expired_reclaims_orphaned_directory(store, caplog):
    """Ein Ordner direkt unter store.root, dessen job.json kaputt/unlesbar
    ist, steckt in KEINEM Cache-Eintrag (siehe _load_existing) -- ohne Fix C
    koennte er NIE entfernt werden (delete() ist bewusst cache-only).
    purge_expired() muss ihn trotzdem anhand seiner Verzeichnis-mtime
    reklamieren, ueber denselben _resolve_job_dir-Pfadtraversal-Schutz wie
    ueberall sonst, und den Vorgang mit seinem Alter loggen."""
    import secrets

    orphan_id = secrets.token_urlsafe(24)
    orphan_dir = store.root / orphan_id
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "job.json").write_text("{ nicht valides JSON", encoding="utf-8")

    old_time = time.time() - 100 * 86400
    os.utime(orphan_dir, (old_time, old_time))

    with caplog.at_level(logging.WARNING):
        removed = store.purge_expired(retention_days=30)

    assert removed == 1
    assert not orphan_dir.exists()
    assert any("Verwaister OCR-Job-Ordner" in record.message for record in caplog.records)


def test_purge_expired_leaves_recent_orphan_and_foreign_entries(store):
    """Ein FRISCHER verwaister Ordner (mtime innerhalb der
    Aufbewahrungsfrist) bleibt unangetastet, und ein Ordner, dessen Name
    NICHT JOB_ID_RE besteht, wird nie auch nur betrachtet -- konservativ:
    nur Namen, die den Pfadtraversal-Schutz bestehen, werden ueberhaupt in
    Erwaegung gezogen (siehe Fix C)."""
    import secrets

    recent_orphan_id = secrets.token_urlsafe(24)
    recent_orphan_dir = store.root / recent_orphan_id
    recent_orphan_dir.mkdir(parents=True)
    (recent_orphan_dir / "job.json").write_text("{ nicht valides JSON", encoding="utf-8")

    foreign_dir = store.root / "not a valid job id!"
    foreign_dir.mkdir(parents=True)
    (foreign_dir / "marker.txt").write_text("fremd", encoding="utf-8")
    old_time = time.time() - 100 * 86400
    os.utime(foreign_dir, (old_time, old_time))

    removed = store.purge_expired(retention_days=30)

    assert removed == 0
    assert recent_orphan_dir.exists()
    assert foreign_dir.exists()


# ---------------------------------------------------------------------------
# Persist-Ordering-Race -- der Cache eilt der Platte nie voraus
# ---------------------------------------------------------------------------


def _assert_reload_matches(store: OCRJobStore, job_id: str) -> None:
    """Oeffnet einen ZWEITEN OCRJobStore auf demselben `root` und
    vergleicht ihn mit dem, was der lebende `store` fuer denselben Job in
    GENAU diesem Moment im Cache haelt -- die beobachtbare Aussage der
    INVARIANTE in `OCRJobStore._persist_locked` (store.py): der Cache eilt
    der Platte nie voraus. Ein Reload direkt im Anschluss an eine
    Zustandsaenderung (die ueber `store.get()`/den Live-Zustand bereits
    sichtbar ist) muss deshalb IMMER exakt denselben Stand liefern -- kein
    Warten, kein Retry, kein `_persist()`-Nachtriggern noetig."""
    live = store.get(job_id)
    assert live is not None
    reloaded_store = OCRJobStore(store.root, max_workers=1)
    try:
        reloaded = reloaded_store.get(job_id)
        assert reloaded is not None
        assert reloaded.status == live.status
        assert reloaded.error == live.error
        assert reloaded.error_code == live.error_code
        assert len(reloaded.pages) == len(live.pages)
        for reloaded_page, live_page in zip(reloaded.pages, live.pages):
            assert len(reloaded_page.regions) == len(live_page.regions)
            for reloaded_region, live_region in zip(reloaded_page.regions, live_page.regions):
                assert reloaded_region.selected_text == live_region.selected_text
                assert reloaded_region.edited_by_teacher == live_region.edited_by_teacher
                assert reloaded_region.status == live_region.status
    finally:
        reloaded_store.shutdown()


def test_cache_never_leads_disk(store):
    """Kern-Regressionstest fuer die Persist-Ordering-Race (siehe Auftrag):
    nach JEDER Zustandsaenderung -- Job-Abschluss, patch_region, approve,
    UND ein echter Fehlschlag -- muss ein frisch konstruierter
    `OCRJobStore` auf demselben `root` GENAU das sehen, was der lebende
    Store in diesem Moment im Cache haelt. `OCRJobStore._persist_locked`
    schreibt job.json VOR der Cache-Veroeffentlichung, unter demselben
    Lock, den `get()` ebenfalls nimmt -- kein Beobachter (dieser Prozess
    ueber `get()`, oder ein neuer Store ueber die Platte) kann also je den
    neuen Cache-Stand sehen, bevor der entsprechende Plattenstand
    geschrieben ist.

    Treibt einen ECHTEN Job (zwei widerspruechliche FakeEngine-Instanzen,
    siehe `_create_two_region_job`) durch Abschluss, `patch_region()` UND
    `approve()`, plus einen zweiten, echt (nicht monkeypatched)
    fehlschlagenden Job (`_CloudBlockedEngine`) -- keine synthetische
    `DocumentResult`-Konstruktion, wie im Auftrag verlangt."""
    job_id, region_id = _create_two_region_job(store)

    # 1) Job-Abschluss (needs_review, mit ungeklaerter kritischer Region).
    assert store.get(job_id).status is OCRStatus.NEEDS_REVIEW
    _assert_reload_matches(store, job_id)

    # 2) patch_region.
    store.patch_region(job_id, region_id, text="Die Kraft ist konstant.")
    _assert_reload_matches(store, job_id)

    # 3) approve.
    store.approve(job_id)
    assert store.get(job_id).status is OCRStatus.APPROVED
    _assert_reload_matches(store, job_id)

    # 4) ein ECHT fehlschlagender zweiter Job (CloudBlocked ueber den
    # realen Hintergrund-Worker-Pfad, kein monkeypatchtes process_document).
    failing_engine = _CloudBlockedEngine()
    config = PipelineConfig(require_engines=())
    failing_stub = store.create(
        source=_make_image_bytes(),
        source_name="blockiert.png",
        config=config,
        engines=[failing_engine],
    )
    _wait_until_done(store, failing_stub.job_id)
    assert store.get(failing_stub.job_id).status is OCRStatus.FAILED
    _assert_reload_matches(store, failing_stub.job_id)
