"""Testet das Freigabe-Gate fuer Bewertungs-Skills.

Deckt teacherassist_core/ocr/gate.py ab: evaluate_grading_gate (Zeile 40)
und GateDecision (Zeile 33) -- der Sicherheits-Choke-Point zwischen der
OCR-Pipeline und ``schuelerarbeit_bewerten``. Baut DocumentResult-Instanzen
direkt aus teacherassist_core/ocr/types.py auf, ohne Engines, Bilder oder
Pipeline.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import threading
from logging.handlers import RotatingFileHandler

import pytest

import tool_server
from conftest import stub_ollama_vlm_factory
from teacherassist_core.ocr.gate import GRADING_SKILLS, evaluate_grading_gate
from teacherassist_core.ocr.types import (
    Disagreement,
    DocumentResult,
    ImageQuality,
    OCRCandidate,
    OCRStatus,
    PageResult,
    Region,
    RegionType,
)


def _candidate(text: str) -> OCRCandidate:
    return OCRCandidate(
        engine="fake",
        text=text,
        raw_text=text,
        confidence=0.9,
        tokens=tuple(text.split()),
    )


def _region(text: str, *, critical: bool = False, status: OCRStatus = OCRStatus.APPROVED) -> Region:
    disagreements = ()
    if critical:
        disagreements = (
            Disagreement(
                start=0,
                end=1,
                variants=(("nicht", ("fake",)),),
                critical=True,
                reason="critical_word:nicht",
            ),
        )
    return Region(
        id="p0-r0",
        type=RegionType.PARAGRAPH,
        bbox=(0, 0, 10, 10),
        candidates=(_candidate(text),),
        reference_engine="fake",
        consensus_text=text,
        selected_text=text,
        disagreements=disagreements,
        agreement=1.0,
        status=status,
    )


def _page(region: Region, *, status: OCRStatus) -> PageResult:
    return PageResult(
        index=0,
        width=100,
        height=100,
        quality=ImageQuality.unknown(100, 100),
        regions=(region,),
        status=status,
        auto_clean=False,
        engine_failures=(),
    )


def _document(job_id: str, *, status: OCRStatus, critical: bool = False) -> DocumentResult:
    region = _region("Antwort", critical=critical, status=status)
    page = _page(region, status=status)
    return DocumentResult(
        job_id=job_id,
        source_name="test.png",
        classification="student_submission",
        created_at=0.0,
        pages=[page],
        status=status,
    )


def test_gate_allows_non_grading_skills():
    """Ein Skill ausserhalb von GRADING_SKILLS (gate.py:23) wird nie geprueft,
    unabhaengig vom Status der referenzierten Jobs."""
    jobs = {"job-1": _document("job-1", status=OCRStatus.NEEDS_REVIEW)}

    decision = evaluate_grading_gate(skill_id="andere_aufgabe", ocr_job_ids=("job-1",), jobs=jobs)

    assert decision.allowed is True
    assert decision.reasons == ()


def test_gate_blocks_unapproved_job():
    """Ein referenzierter Job, dessen Status nicht APPROVED ist, blockiert
    das Gate mit dem Grund 'not_approved:{job_id}' (gate.py: Regel 2)."""
    jobs = {"job-1": _document("job-1", status=OCRStatus.NEEDS_REVIEW)}

    decision = evaluate_grading_gate(
        skill_id="schuelerarbeit_bewerten", ocr_job_ids=("job-1",), jobs=jobs
    )

    assert decision.allowed is False
    assert decision.reasons == ("not_approved:job-1",)


def test_gate_blocks_critical_uncertainty_even_when_approved():
    """Ein APPROVED-Job mit verbleibender kritischer Unsicherheit
    (has_critical_uncertainty, types.py:235) wird trotzdem blockiert --
    defence in depth (gate.py: Regel 3)."""
    jobs = {"job-1": _document("job-1", status=OCRStatus.APPROVED, critical=True)}

    decision = evaluate_grading_gate(
        skill_id="schuelerarbeit_bewerten", ocr_job_ids=("job-1",), jobs=jobs
    )

    assert decision.allowed is False
    assert decision.reasons == ("critical_uncertainty:job-1",)


def test_gate_blocks_unknown_job_id():
    """Eine vom Client gelieferte Job-ID, die sich nicht in ``jobs`` aufloesen
    laesst, wird fail-closed abgelehnt ('unknown_job:{job_id}') -- eine
    unbekannte ID ist niemals in Ordnung (gate.py: Regel 1)."""
    decision = evaluate_grading_gate(
        skill_id="schuelerarbeit_bewerten", ocr_job_ids=("does-not-exist",), jobs={}
    )

    assert decision.allowed is False
    assert decision.reasons == ("unknown_job:does-not-exist",)


def test_gate_allows_when_no_jobs_referenced():
    """Keine referenzierten OCR-Job-IDs bei einem Bewertungs-Skill ist
    erlaubt: die Lehrkraft hat die Antworten selbst per Hand eingetippt.
    Das ist die dokumentierte, ehrliche Grenze des Gates (gate.py
    Modul-Docstring) -- kein Loch, das "repariert" werden sollte."""
    decision = evaluate_grading_gate(
        skill_id="schuelerarbeit_bewerten", ocr_job_ids=(), jobs={}
    )

    assert decision.allowed is True
    assert decision.reasons == ()


def test_gate_message_is_german_and_actionable():
    """Bei einer Ablehnung ist ``message`` die feste deutsche,
    lehrkraft-gerichtete Meldung aus gate.py (_GATE_MESSAGE_DE)."""
    jobs = {"job-1": _document("job-1", status=OCRStatus.NEEDS_REVIEW)}

    decision = evaluate_grading_gate(
        skill_id="schuelerarbeit_bewerten", ocr_job_ids=("job-1",), jobs=jobs
    )

    assert decision.allowed is False
    assert "freigegeben" in decision.message
    assert "prüfe" in decision.message or "pruefe" in decision.message
    assert decision.message == (
        "Die Transkription ist noch nicht freigegeben. Bitte prüfe die "
        "markierten Unsicherheiten und gib die Abschrift frei, bevor ich bewerte."
    )


def test_grading_skills_contains_expected_skill():
    """GRADING_SKILLS (gate.py:16) enthaelt genau den Bewertungs-Skill."""
    assert GRADING_SKILLS == frozenset({"schuelerarbeit_bewerten"})


# ---------------------------------------------------------------------------
# HTTP-Wiring-Tests (Stufe 5): schliessen die Luecke zwischen der reinen
# gate.py-Logik oben und der tatsaechlichen Verdrahtung in
# tool_server.py::_stream_chat_payload. Fixture adaptiert von
# tests/test_http_api.py::isolated_server, siehe deren Docstring fuer die
# volle Begruendung des Monkeypatch-Tricks. Zusaetzlich hier: STATE_STORE
# bekommt einen ECHTEN Fernet-Schluessel (os.urandom(32) statt raw_key=None)
# -- diese Tests brauchen einen funktionierenden Chat-Store fuer
# /api/v1/chats + /api/v1/chats/{id}/messages, waehrend test_http_api.py's
# Variante das bewusst vermeidet, um Keyring/Fernet gar nicht erst
# anzufassen. OCR_JOBS wird ebenfalls auf einen tmp_path-Store umgehaengt,
# damit evaluate_grading_gate()'s OCR_JOBS.snapshot()-Aufruf nie das echte
# Produktions-Job-Verzeichnis liest.
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
        tool_server, "STATE_STORE", tool_server.EncryptedStateStore(runtime_paths.encrypted_state, os.urandom(32))
    )
    ocr_store = tool_server.OCRJobStore(runtime_paths.ocr, max_workers=1)
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
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        ocr_store.shutdown()
        thread.join(timeout=5)
        tool_server.logger.removeHandler(temp_handler)
        temp_handler.close()
        for handler in original_handlers:
            tool_server.logger.addHandler(handler)


def _bootstrap(port):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": f"localhost:{port}"})
        response = conn.getresponse()
        body = json.loads(response.read())
        set_cookie = response.getheader("Set-Cookie").split(";", 1)[0]
        return body["csrfToken"], set_cookie
    finally:
        conn.close()


def _authed_request(port, csrf, cookie, method, path, *, body=None):
    """Returns (status, response, parsed_json_or_None) -- keeps the raw
    `response` object around so callers can inspect headers (Content-Type
    in particular, see test_stream_chat_payload_returns_409_before_sse_headers)."""
    headers = {"Host": f"localhost:{port}", "Cookie": cookie, "X-CSRF-Token": csrf}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = None
        return response.status, response, parsed
    finally:
        conn.close()


def test_stream_chat_payload_returns_409_before_sse_headers(isolated_server):
    """SECURITY-CRITICAL: the evaluate_grading_gate() call in
    tool_server.py::_stream_chat_payload sits right before
    self.send_response(200)/the SSE headers, with a comment explaining that
    the ordering is load-bearing (see tool_server.py: "Sobald die SSE-Header
    einmal gesendet sind..."). This test is the one that catches a
    regression where somebody later moves the gate a few lines down: POSTing
    to /api/v1/chats/{id}/messages (the persisted-chat route, which layers
    STATE_STORE.save_chat() around _stream_chat_payload -- see
    tool_server.py:_chat_message) with skill_id="schuelerarbeit_bewerten"
    and an unresolvable ocrJobIds entry must answer a REGULAR HTTP 409 with
    Content-Type: application/json, never a 200 with
    text/event-stream (which is all that's still possible once the SSE
    headers have gone out)."""
    port = isolated_server
    csrf, cookie = _bootstrap(port)

    status, _response, chat = _authed_request(port, csrf, cookie, "POST", "/api/v1/chats", body={"title": "Testchat"})
    assert status == 201
    chat_id = chat["id"]

    status, response, payload = _authed_request(
        port, csrf, cookie, "POST", f"/api/v1/chats/{chat_id}/messages",
        body={
            "content": "Bitte bewerte die Arbeit von SuS-01.",
            "skill_id": "schuelerarbeit_bewerten",
            "ocrJobIds": ["does-not-exist"],
        },
    )

    assert status == 409
    content_type = response.getheader("Content-Type") or ""
    assert "application/json" in content_type
    assert "text/event-stream" not in content_type
    assert payload["error"]["code"] == "OCR_APPROVAL_REQUIRED"
    assert isinstance(payload["error"]["message"], str) and payload["error"]["message"]


def test_chat_without_ocr_jobs_is_unaffected(isolated_server):
    """Regression guard for the gate wiring itself: a normal chat message
    with no ocrJobIds (and no grading skill_id) must sail straight through
    to the SSE response -- evaluate_grading_gate() only blocks
    GRADING_SKILLS, and an empty ocr_job_ids list is explicitly allowed
    even for a grading skill (gate.py module docstring: manual teacher
    input). Only checks the transport-level outcome (status/Content-Type),
    not the LLM reply itself -- no provider is configured in this fixture."""
    port = isolated_server
    csrf, cookie = _bootstrap(port)

    status, _response, chat = _authed_request(port, csrf, cookie, "POST", "/api/v1/chats", body={"title": "Testchat"})
    assert status == 201
    chat_id = chat["id"]

    status, response, _payload = _authed_request(
        port, csrf, cookie, "POST", f"/api/v1/chats/{chat_id}/messages",
        body={"content": "Wie plane ich die nächste Stunde?"},
    )

    assert status == 200
    content_type = response.getheader("Content-Type") or ""
    assert "text/event-stream" in content_type
