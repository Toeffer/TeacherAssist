"""Exercises the OCR HTTP endpoints added in Stufe 5 of the OCR refactor
(tool_server.py: OCR_JOB_RE/OCR_PAGE_RE/OCR_REGION_RE/OCR_APPROVE_RE and the
_list_ocr_jobs/_get_ocr_job/_ocr_job_page/_create_ocr_job/_patch_ocr_region/
_approve_ocr_job/_delete_ocr_job handlers).

Like tests/test_http_api.py, this drives the real ToolHandler/
_QuietThreadingHTTPServer over a loopback socket with stdlib http.client --
the only way to catch a route-regex or _authorize() regression. Unlike
test_http_api.py's isolated_server fixture, ours ALSO monkeypatches
tool_server.OCR_JOBS to a fresh OCRJobStore rooted under tmp_path: OCR_JOBS
is a module-level singleton built once at `import tool_server` time against
the real RUNTIME_PATHS.ocr (see tool_server.py near STATE_STORE), so without
this every OCR test here would read and write actual job folders under the
developer's real %LOCALAPPDATA%\\TeacherAssist\\ocr.

Most tests populate a job directly via OCR_JOBS.create() with FakeEngine
instances (teacherassist_core/ocr/engines/fake.py) constructed in-process --
mirroring tests/test_ocr_store.py's approach -- rather than through the
HTTP create route, because FakeEngine's per-region `texts` mapping can't be
expressed through the persisted settings JSON (there is no "fakeOcrTexts"
settings key, deliberately -- see runtime.py SETTINGS_KEYS). Only
test_create_job_returns_202_and_id exercises POST /api/v1/ocr/jobs itself,
using ocrEngines=["fake"] (a real, persistable settings key) with FakeEngine's
str-mode default of an empty string -- sufficient to prove the route/status
machinery without needing meaningful recognized text.
"""

from __future__ import annotations

import http.client
import io
import json
import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

import tool_server
from conftest import stub_ollama_vlm_factory
from teacherassist_core.ocr.engines import FakeEngine
from teacherassist_core.ocr.pipeline import PipelineConfig
from teacherassist_core.ocr.store import OCRJobStore
from teacherassist_core.ocr.types import OCRStatus

POLL_TIMEOUT_S = 10.0
POLL_INTERVAL_S = 0.05
BOUNDARY = "TeacherAssistOcrHttpTestBoundary"


# ---------------------------------------------------------------------------
# Fixture (adapted from tests/test_http_api.py::isolated_server, plus the
# OCR_JOBS swap described in the module docstring)
# ---------------------------------------------------------------------------
@pytest.fixture
def isolated_server(tmp_path, monkeypatch):
    monkeypatch.setenv("TEACHERASSIST_DATA_DIR", str(tmp_path))
    runtime_paths = tool_server.RuntimePaths.from_environment(tool_server.BASE_DIR)
    runtime_paths.ensure()

    monkeypatch.setattr(tool_server, "RUNTIME_PATHS", runtime_paths)
    monkeypatch.setattr(tool_server, "UPLOAD_DIR", runtime_paths.uploads)
    monkeypatch.setattr(tool_server, "CHROMA_DIR", runtime_paths.chroma)
    monkeypatch.setattr(tool_server, "EXPORT_DIR", runtime_paths.exports)
    monkeypatch.setattr(tool_server, "LOG_DIR", runtime_paths.logs)
    monkeypatch.setattr(tool_server, "SETTINGS_FILE", runtime_paths.settings)
    monkeypatch.setattr(tool_server, "MEMORY_DIR", runtime_paths.memory)
    monkeypatch.setattr(
        tool_server, "SETTINGS_STORE", tool_server.SettingsStore(runtime_paths.settings, tool_server.CREDENTIALS)
    )
    monkeypatch.setattr(
        tool_server, "STATE_STORE", tool_server.EncryptedStateStore(runtime_paths.encrypted_state, None)
    )
    ocr_store = OCRJobStore(runtime_paths.ocr, max_workers=1)
    monkeypatch.setattr(tool_server, "OCR_JOBS", ocr_store)
    monkeypatch.setattr(tool_server, "check_ollama", lambda: False)
    # ocr_capability_status() (called from bootstrap) independently builds
    # ENGINE_FACTORIES["ollama_vlm"] and calls .status() on it -- a SEPARATE
    # real network call that the check_ollama stub above does not cover
    # (see tests/conftest.py::stub_ollama_vlm_factory).
    stub_ollama_vlm_factory(monkeypatch)

    original_handlers = list(tool_server.logger.handlers)
    for handler in original_handlers:
        tool_server.logger.removeHandler(handler)
    temp_handler = RotatingFileHandler(runtime_paths.logs / "tool_server.log", encoding="utf-8")
    temp_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    tool_server.logger.addHandler(temp_handler)

    server = tool_server._QuietThreadingHTTPServer(("127.0.0.1", 0), tool_server.ToolHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], ocr_store, runtime_paths
    finally:
        server.shutdown()
        server.server_close()
        ocr_store.shutdown()
        thread.join(timeout=5)
        tool_server.logger.removeHandler(temp_handler)
        temp_handler.close()
        for handler in original_handlers:
            tool_server.logger.addHandler(handler)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def _bootstrap(port):
    """Returns (csrf_token, cookie_header_value) from the public bootstrap route."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": f"localhost:{port}"})
        response = conn.getresponse()
        body = json.loads(response.read())
        set_cookie = response.getheader("Set-Cookie").split(";", 1)[0]
        return body["csrfToken"], set_cookie
    finally:
        conn.close()


def _authed_request(port, csrf, cookie, method, path, *, body=None, extra_headers=None):
    """Sends an authenticated request. `body`: bytes -> sent as-is (caller sets
    Content-Type via extra_headers); dict -> JSON-encoded automatically.
    Returns (status, json_body_or_None, raw_bytes)."""
    headers = {"Host": f"localhost:{port}", "Cookie": cookie, "X-CSRF-Token": csrf}
    data = None
    if isinstance(body, dict):
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif body is not None:
        data = body
    if extra_headers:
        headers.update(extra_headers)

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = None
        return response.status, parsed, raw
    finally:
        conn.close()


def _multipart_body(parts, boundary=BOUNDARY):
    """Same construction as tests/test_multipart.py::_multipart_body."""
    chunks = []
    for part in parts:
        if "filename" in part:
            disposition = f'Content-Disposition: form-data; name="{part["name"]}"; filename="{part["filename"]}"'
            content_type = part.get("content_type", "application/octet-stream")
            head = ("--" + boundary + "\r\n" + disposition + "\r\n" + f"Content-Type: {content_type}" + "\r\n\r\n").encode()
            chunks.append(head + part["content"] + b"\r\n")
        else:
            disposition = f'Content-Disposition: form-data; name="{part["name"]}"'
            head = ("--" + boundary + "\r\n" + disposition + "\r\n\r\n").encode()
            value = part["value"]
            value_bytes = value if isinstance(value, bytes) else value.encode("utf-8")
            chunks.append(head + value_bytes + b"\r\n")
    chunks.append(("--" + boundary + "--\r\n").encode())
    return b"".join(chunks)


def _wait_until_left_processing(port, csrf, cookie, job_id, *, timeout=POLL_TIMEOUT_S):
    """Polls GET /api/v1/ocr/jobs/{job_id} until status leaves 'processing'.
    Fails the test (instead of hanging the suite) if the deadline passes."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status, payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
        assert status == 200
        if payload["status"] != "processing":
            return payload
        time.sleep(POLL_INTERVAL_S)
    pytest.fail(f"OCR-Job {job_id} hat 'processing' nicht innerhalb von {timeout}s verlassen")


# ---------------------------------------------------------------------------
# Test image builders (mirrors tests/test_ocr_store.py's helpers -- see
# there for the full rationale on why the image must not be blank/blurry)
# ---------------------------------------------------------------------------
def _make_image_bytes() -> bytes:
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
    """Exactly one text-line region (see test_ocr_store.py for why: multiple
    identical regions would make 'resolve exactly one region' ambiguous)."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (400, 300), color="white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 100, 360, 118], fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _wait_store_until_done(store, job_id, *, timeout=POLL_TIMEOUT_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        doc = store.get(job_id)
        assert doc is not None
        if doc.status is not OCRStatus.PROCESSING:
            return doc
        time.sleep(POLL_INTERVAL_S)
    pytest.fail(f"OCR-Job {job_id} hat PROCESSING nicht innerhalb von {timeout}s verlassen")


def _create_single_engine_job(store):
    """A job with exactly one engine -> no disagreements -> no critical
    uncertainty -> approve() succeeds without any patch_region() first."""
    engine = FakeEngine("tesseract", "Hallo Welt")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_single_line_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    doc = _wait_store_until_done(store, stub.job_id)
    assert doc.pages and doc.pages[0].regions, "Testaufbau erwartet mindestens eine Region"
    return doc.job_id


class _CloudBlockedEngine:
    """Minimal engine stand-in that raises CloudBlocked immediately --
    mirrors tests/test_ocr_store.py's `_CloudBlockedEngine` (FakeEngine
    cannot raise CloudBlocked, see engines/fake.py). Implements only what
    the OCREngine protocol (engines/base.py) and pipeline.py's
    process_page() actually need."""

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
        from teacherassist_core.ocr.privacy_guard import CloudBlocked

        raise CloudBlocked("student_submission", "https://example.invalid/ocr")

    def warmup(self) -> None:
        return None


def _create_critical_disagreement_job(store):
    """Two engines disagreeing on 'nicht' -> exactly one critical region
    (same construction as tests/test_ocr_store.py::_create_two_region_job).
    Returns (job_id, region_id)."""
    engine_a = FakeEngine("htr", "Die Kraft ist nicht konstant.")
    engine_b = FakeEngine("tesseract", "Die Kraft ist konstant.")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_single_line_image_bytes(), source_name="kritisch.png", config=config,
        engines=[engine_a, engine_b],
    )
    doc = _wait_store_until_done(store, stub.job_id)
    critical_regions = [r for p in doc.pages for r in p.regions if r.has_critical_uncertainty]
    assert critical_regions, "Testaufbau erwartet eine kritische Diskrepanz (nicht vs. leer)"
    return stub.job_id, critical_regions[0].id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_create_job_returns_202_and_id(isolated_server):
    """POST /api/v1/ocr/jobs (tool_server.py:_create_ocr_job) must answer
    202 with {jobId, status:'processing'} immediately (OCRJobStore.create()
    runs the pipeline on a background worker) -- polled via GET, the job
    must reach a terminal status within the timeout. Uses ocrEngines=["fake"]
    (a real, persistable settings key, see module docstring) so the whole
    round trip -- settings -> build_engines() -> OCR_JOBS.create() -- runs
    through production code, not a monkeypatch."""
    port, _store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    status, payload, _ = _authed_request(
        port, csrf, cookie, "POST", "/api/v1/settings", body={"ocrEngines": ["fake"]}
    )
    assert status == 200
    assert payload["settings"]["ocrEngines"] == ["fake"]

    body = _multipart_body([
        {"name": "classification", "value": "student_submission"},
        {"name": "scan", "filename": "scan.png", "content": _make_image_bytes(), "content_type": "image/png"},
    ])
    status, payload, _ = _authed_request(
        port, csrf, cookie, "POST", "/api/v1/ocr/jobs",
        body=body, extra_headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
    )
    assert status == 202
    assert isinstance(payload["jobId"], str) and payload["jobId"]
    assert payload["status"] == "processing"

    final = _wait_until_left_processing(port, csrf, cookie, payload["jobId"])
    assert final["status"] in ("needs_review", "approved", "failed")


def test_get_job_withholds_text_until_approved(isolated_server):
    """SECURITY-CRITICAL: GET /api/v1/ocr/jobs/{id} must deliver
    pages[*].text == None until the job is APPROVED (types.py's
    DocumentResult.to_dict() include_text choke point), and a real string
    afterwards. A single-engine job has no disagreements at all, so
    approve() succeeds without any patch_region() call first."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id = _create_single_engine_job(store)

    status, payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    assert payload["status"] != "approved"
    assert all(page["text"] is None for page in payload["pages"])

    status, payload, _ = _authed_request(port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{job_id}/approve")
    assert status == 200
    assert payload["status"] == "approved"
    assert all(isinstance(page["text"], str) for page in payload["pages"])

    status, payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    assert all(isinstance(page["text"], str) for page in payload["pages"])


def test_approve_rejects_while_critical_unresolved(isolated_server):
    """POST .../approve must answer 409 OCR_CRITICAL_UNRESOLVED (translated
    from store.py's ApprovalRefused) while a critical disagreement is
    unresolved, and must name the offending region id in the message."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    status, payload, _ = _authed_request(port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{job_id}/approve")
    assert status == 409
    assert payload["error"]["code"] == "OCR_CRITICAL_UNRESOLVED"
    assert region_id in payload["error"]["message"]

    # The job itself must remain un-approved after the refused attempt.
    status, payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    assert payload["status"] != "approved"


def test_approve_processing_job_returns_409_not_ready(isolated_server, monkeypatch):
    """POST .../approve on a job still PROCESSING must answer 409
    OCR_NOT_READY -- translated from store.py's ApprovalNotReady, which is
    now the ONLY guard for this rule (tool_server.py no longer duplicates
    a status pre-check of its own, see
    test_approve_handler_has_no_duplicate_status_precheck below)."""
    import teacherassist_core.ocr.store as store_module

    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    release = threading.Event()

    def _blocking_process_document(*args, **kwargs):
        release.wait(POLL_TIMEOUT_S)
        raise RuntimeError("should never actually run in this test")

    monkeypatch.setattr(store_module, "process_document", _blocking_process_document)

    engine = FakeEngine("tesseract", "Text")
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    assert stub.status is OCRStatus.PROCESSING

    try:
        status, payload, _ = _authed_request(
            port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{stub.job_id}/approve"
        )
        assert status == 409
        assert payload["error"]["code"] == "OCR_NOT_READY"
        assert "läuft noch" in payload["error"]["message"]
        assert "fehlgeschlagen" in payload["error"]["message"]
    finally:
        release.set()
        _wait_until_left_processing(port, csrf, cookie, stub.job_id)


def test_not_ready_and_unresolved_messages_differ(isolated_server):
    """The two 409 German messages must be genuinely different, and each
    must tell the teacher what to do next: OCR_NOT_READY says the
    recognition is still running or has failed (nothing to review yet),
    while OCR_CRITICAL_UNRESOLVED says to check the marked regions.

    Uses its OWN `monkeypatch.context()` (scoped to just the
    process_document patch below) rather than the `isolated_server`
    fixture's `monkeypatch` fixture -- calling `.undo()` on the SAME
    monkeypatch instance the fixture used would also revert the fixture's
    own patches (RUNTIME_PATHS/OCR_JOBS/etc.), pointing the HTTP server
    back at the real module-level OCR_JOBS singleton."""
    import pytest as _pytest

    import teacherassist_core.ocr.store as store_module

    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    release = threading.Event()

    def _blocking_process_document(*args, **kwargs):
        release.wait(POLL_TIMEOUT_S)
        raise RuntimeError("should never actually run in this test")

    with _pytest.MonkeyPatch.context() as scoped_patch:
        scoped_patch.setattr(store_module, "process_document", _blocking_process_document)
        engine = FakeEngine("tesseract", "Text")
        config = PipelineConfig(require_engines=())
        stub = store.create(
            source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
        )
        try:
            status, payload, _ = _authed_request(
                port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{stub.job_id}/approve"
            )
            assert status == 409
            not_ready_message = payload["error"]["message"]
        finally:
            release.set()
            _wait_until_left_processing(port, csrf, cookie, stub.job_id)

    job_id, _region_id = _create_critical_disagreement_job(store)
    status, payload, _ = _authed_request(port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{job_id}/approve")
    assert status == 409
    unresolved_message = payload["error"]["message"]

    assert not_ready_message != unresolved_message
    assert "läuft noch" in not_ready_message
    assert "prüfen" in unresolved_message
    assert "prüfen" not in not_ready_message
    assert "läuft noch" not in unresolved_message


def test_patch_region_with_candidate_engine_then_approve_succeeds(isolated_server):
    """PATCH .../regions/{rid} with {"candidateEngine": "tesseract"} must
    resolve the critical disagreement (store.py:patch_region sets
    edited_by_teacher=True), after which POST .../approve must succeed and
    the resolved text must appear in the response.

    The PATCH response itself withholds selectedText here: the parent
    document is still needs_review at this point, and include_text is
    derived from the document's real approval status, exactly like every
    other route (see tool_server.py:_patch_ocr_region and Auftrag Fix 1) --
    NOT from whether this particular edit was just made. See
    test_patch_response_withholds_text_for_unapproved_document for that
    rule in isolation."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    status, payload, _ = _authed_request(
        port, csrf, cookie, "PATCH", f"/api/v1/ocr/jobs/{job_id}/regions/{region_id}",
        body={"candidateEngine": "tesseract"},
    )
    assert status == 200
    assert payload["editedByTeacher"] is True
    assert payload["selectedText"] is None

    status, payload, _ = _authed_request(port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{job_id}/approve")
    assert status == 200
    assert payload["status"] == "approved"
    assert any("Die Kraft ist konstant." in (page["text"] or "") for page in payload["pages"])


def test_noop_patch_is_rejected(isolated_server):
    """PATCH with an empty body ({}) sets neither `text` nor
    `candidateEngine` -- store.patch_region() must reject that outright
    (EmptyPatchError -> 400 OCR_EMPTY_PATCH), instead of silently echoing
    the region back unchanged. Before this fix, that echo hardcoded
    include_text=True, so a pure no-op PATCH against a still-needs_review
    document with an unresolved critical disagreement handed back the
    reference engine's full selectedText, AND edited_by_teacher stayed
    False -- the one rule the whole OCR review flow rests on (no
    transcript text before teacher approval) had a hole (see Auftrag
    Fix 1)."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    status, payload, raw = _authed_request(
        port, csrf, cookie, "PATCH", f"/api/v1/ocr/jobs/{job_id}/regions/{region_id}",
        body={},
    )
    assert status == 400
    assert payload["error"]["code"] == "OCR_EMPTY_PATCH"

    raw_text = raw.decode("utf-8")
    assert "Die Kraft ist konstant." not in raw_text
    assert "Die Kraft ist nicht konstant." not in raw_text

    # And the no-op must not have mutated anything either: edited_by_teacher
    # stays False, the disagreement stays unresolved.
    status, doc_payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    region = next(
        r for page in doc_payload["pages"] for r in page["regions"] if r["id"] == region_id
    )
    assert region["editedByTeacher"] is False


def test_patch_response_withholds_text_for_unapproved_document(isolated_server):
    """After a legitimate `candidateEngine` patch on a still-needs_review
    document, the PATCH response's selectedText must be withheld (None) --
    include_text is derived from the parent document's real approval
    status (like every other route), never hardcoded. editedByTeacher,
    which is diagnostic metadata rather than transcript content, is still
    reported truthfully."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    status, payload, _ = _authed_request(
        port, csrf, cookie, "PATCH", f"/api/v1/ocr/jobs/{job_id}/regions/{region_id}",
        body={"candidateEngine": "tesseract"},
    )
    assert status == 200
    assert payload["editedByTeacher"] is True
    assert payload["selectedText"] is None
    # candidates[*].text bleiben bewusst IMMER sichtbar (siehe
    # types.py:OCRCandidate.to_dict -- die Review-UI braucht sie, um
    # Konsens-Abweichungen anzuzeigen, unabhaengig von der Freigabe). Nur
    # das aufgeloeste selectedText ist an die Freigabe gebunden.
    assert any(c["engine"] == "tesseract" for c in payload["candidates"])


def test_patch_cannot_be_used_to_read_candidates_before_approval(isolated_server):
    """The PATCH response must never become a side channel that disagrees
    with GET .../jobs/{id}: immediately after a legitimate edit, both must
    agree that selectedText/page text stay withheld while the document is
    not yet approved -- a teacher cannot use repeated PATCH calls as an
    oracle to read the resolved transcript before approving."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    status, patch_payload, _ = _authed_request(
        port, csrf, cookie, "PATCH", f"/api/v1/ocr/jobs/{job_id}/regions/{region_id}",
        body={"candidateEngine": "tesseract"},
    )
    assert status == 200
    assert patch_payload["selectedText"] is None

    status, doc_payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    assert doc_payload["status"] == "needs_review"
    for page in doc_payload["pages"]:
        assert page["text"] is None
        for region in page["regions"]:
            assert region["selectedText"] is None


def test_page_png_returns_image(isolated_server):
    """GET .../pages/{n} must answer image/png with Cache-Control: no-store
    and real PNG bytes (page_render via OCRJobStore.page_png)."""
    port, store, _paths = isolated_server
    job_id = _create_single_engine_job(store)
    csrf, cookie = _bootstrap(port)

    status, _payload, raw = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}/pages/0")
    assert status == 200
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"


def test_region_crop_differs_from_full_page(isolated_server):
    """GET .../pages/{n}?region={rid} must answer a smaller crop than the
    full page (OCRJobStore.page_png's region_id branch, 8px padding)."""
    port, store, _paths = isolated_server
    job_id, region_id = _create_critical_disagreement_job(store)
    csrf, cookie = _bootstrap(port)

    status, _payload, page_raw = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}/pages/0")
    assert status == 200
    status, _payload, region_raw = _authed_request(
        port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}/pages/0?region={region_id}"
    )
    assert status == 200
    assert region_raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(region_raw) < len(page_raw)


def test_delete_job_removes_directory(isolated_server):
    """DELETE /api/v1/ocr/jobs/{id} must answer {"deleted": true} and
    physically remove root/{job_id}/ (OCRJobStore.delete's shutil.rmtree);
    a subsequent GET must then answer 404 OCR_JOB_NOT_FOUND."""
    port, store, _paths = isolated_server
    job_id = _create_single_engine_job(store)
    csrf, cookie = _bootstrap(port)
    job_dir = store.root / job_id
    assert job_dir.exists()

    status, payload, _ = _authed_request(port, csrf, cookie, "DELETE", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 200
    assert payload == {"deleted": True}
    assert not job_dir.exists()

    status, payload, _ = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{job_id}")
    assert status == 404
    assert payload["error"]["code"] == "OCR_JOB_NOT_FOUND"


@pytest.mark.parametrize(
    "malicious_id",
    [
        "..%2f..%2fetc%2fpasswd",
        "..\\..\\windows",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "a" * 65,
    ],
)
def test_traversal_in_job_id_is_rejected(isolated_server, malicious_id):
    """A path-traversal-shaped job id must never reach OCRJobStore at all:
    OCR_JOB_RE's character class ([A-Za-z0-9_-]{1,64}) rejects it outright,
    so the route simply does not match and falls through to the generic
    404 -- nothing outside OCR_JOBS.root is ever touched (OCRJobStore adds
    its own independent check, see store.py's JOB_ID_RE/_resolve_job_dir)."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    status, _payload, _raw = _authed_request(port, csrf, cookie, "GET", f"/api/v1/ocr/jobs/{malicious_id}")
    assert status == 404

    # Nothing outside the isolated OCR root was created or read.
    assert not (store.root.parent / "passwd").exists()
    assert not (store.root.parent / "windows").exists()


def test_json_path_outside_uploads_is_rejected(isolated_server, tmp_path):
    """POST /api/v1/ocr/jobs with {"path": ...} pointing outside
    RUNTIME_PATHS.uploads must be rejected with 403 PATH_BLOCKED (mirrors
    _download_export's traversal defence, tool_server.py:~1327) -- a
    client-supplied path is never trusted."""
    port, _store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    outside_dir = tmp_path / "not-uploads"
    outside_dir.mkdir()
    outside_file = outside_dir / "sneaky.pdf"
    outside_file.write_bytes(b"%PDF-1.4 fake")

    status, payload, _ = _authed_request(
        port, csrf, cookie, "POST", "/api/v1/ocr/jobs",
        body={"path": str(outside_file), "classification": "unknown"},
    )
    assert status == 403
    assert payload["error"]["code"] == "PATH_BLOCKED"


def test_all_ocr_errors_use_structured_shape(isolated_server):
    """Every OCR error response must use self._error()'s {"error": {"code",
    "message"}} shape -- never the flat {"error": str} the old _ocr_image
    used (see tool_server.py's _error method and the Auftrag's explicit
    ban on the flat shape for OCR routes)."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)
    job_id, region_id = _create_critical_disagreement_job(store)

    responses = []
    status, payload, _ = _authed_request(port, csrf, cookie, "GET", "/api/v1/ocr/jobs/does-not-exist")
    responses.append((status, payload))
    status, payload, _ = _authed_request(port, csrf, cookie, "DELETE", "/api/v1/ocr/jobs/does-not-exist")
    responses.append((status, payload))
    status, payload, _ = _authed_request(
        port, csrf, cookie, "PATCH", "/api/v1/ocr/jobs/does-not-exist/regions/r0", body={"text": "x"}
    )
    responses.append((status, payload))
    status, payload, _ = _authed_request(port, csrf, cookie, "POST", "/api/v1/ocr/jobs/does-not-exist/approve")
    responses.append((status, payload))
    status, payload, _ = _authed_request(port, csrf, cookie, "POST", f"/api/v1/ocr/jobs/{job_id}/approve")
    responses.append((status, payload))
    status, payload, _ = _authed_request(
        port, csrf, cookie, "PATCH", f"/api/v1/ocr/jobs/{job_id}/regions/{region_id}",
        body={"candidateEngine": "does-not-exist"},
    )
    responses.append((status, payload))
    body = _multipart_body([{"name": "classification", "value": "student_submission"}])
    status, payload, _ = _authed_request(
        port, csrf, cookie, "POST", "/api/v1/ocr/jobs",
        body=body, extra_headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
    )
    responses.append((status, payload))

    assert len(responses) == 7
    for status, payload in responses:
        assert status >= 400
        assert isinstance(payload, dict) and "error" in payload
        assert isinstance(payload["error"], dict)
        assert isinstance(payload["error"].get("code"), str) and payload["error"]["code"]
        assert isinstance(payload["error"].get("message"), str) and payload["error"]["message"]


def test_cloud_blocked_job_exposes_error_code_over_http(isolated_server):
    """A job that failed because an engine tried to reach a non-loopback
    endpoint with student data must expose errorCode == 'cloud_blocked'
    over GET /api/v1/ocr/jobs/{id} (DocumentResult.to_dict() reaches the
    HTTP client unchanged, see tool_server.py:_get_ocr_job), while the
    transcript stays withheld: a CLOUD_BLOCKED job's `pages` list is
    always empty (store.py:_run_job never reaches page processing for
    this failure), so there is no page text to leak either -- diagnostics
    out, transcript withheld."""
    port, store, _paths = isolated_server
    csrf, cookie = _bootstrap(port)

    engine = _CloudBlockedEngine()
    config = PipelineConfig(require_engines=())
    stub = store.create(
        source=_make_image_bytes(), source_name="scan.png", config=config, engines=[engine]
    )
    final = _wait_until_left_processing(port, csrf, cookie, stub.job_id)

    assert final["status"] == "failed"
    assert final["errorCode"] == "cloud_blocked"
    assert final["pages"] == []
    assert all(page["text"] is None for page in final["pages"])


def test_approve_handler_has_no_duplicate_status_precheck():
    """_approve_ocr_job must not re-implement store.py's NEEDS_REVIEW-status
    guard itself: OCRJobStore.approve() is now the sole, authoritative
    choke point for that rule and raises ApprovalNotReady/ApprovalRefused
    for it -- a duplicated status check in tool_server.py would silently
    drift from store.py over time (see the Auftrag: "That was the whole
    point of moving the guard down."). Asserts against the handler's
    actual source rather than just its behaviour, so the duplication
    cannot quietly come back even if it happened to agree with store.py
    at the time it was re-added."""
    import inspect

    source = inspect.getsource(tool_server.ToolHandler._approve_ocr_job)
    assert "doc.status" not in source
    assert "OCRStatus.PROCESSING" not in source
    assert "OCRStatus.FAILED" not in source


def test_patch_ocr_region_never_hardcodes_include_text():
    """Quelltext-Vertragstest (siehe Auftrag Fix 1 und das analoge Idiom in
    tests/test_ocr_consensus.py::
    test_document_result_to_dict_source_contract_derives_include_text_from_status):
    `include_text=True` darf in tool_server.py NIRGENDS als Literal
    auftauchen. _patch_ocr_region war die EINZIGE Stelle, die das tat --
    jede andere Route leitet include_text aus dem Status des
    Elterndokuments ab (DocumentResult.to_dict()); ein hartkodiertes
    `include_text=True` an irgendeiner Stelle in tool_server.py waere
    also immer ein Freigabe-Bug, unabhaengig davon, welche Funktion es
    enthaelt."""
    source = Path(tool_server.__file__).read_text(encoding="utf-8")
    assert "include_text=True" not in source
