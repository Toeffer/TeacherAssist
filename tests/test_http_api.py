"""Exercises the real HTTP server: bootstrap/CSRF flow and the health route.

These tests start the actual ToolHandler/_QuietThreadingHTTPServer from
tool_server.py on an OS-assigned loopback port and drive it with stdlib
http.client, instead of only calling helper functions in-process. That is
the only way to catch regressions in the session/CSRF gate itself (see
teacherassist_core/security.py: SessionManager, valid_host, valid_browser_source)
and in route-name drift between tool_server.py and start.bat's health probe.
"""

import http.client
import json
import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

import tool_server
from conftest import stub_ollama_vlm_factory

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def isolated_server(tmp_path, monkeypatch):
    """Start the real server against an isolated, temporary data directory.

    tool_server.py builds its module-level RUNTIME_PATHS/SETTINGS_STORE/STATE_STORE
    once at import time, reading TEACHERASSIST_DATA_DIR via RuntimePaths.from_environment
    (see tool_server.py lines ~85-96). Because pytest imports every test module during
    collection, `import tool_server` may already have happened (e.g. via
    tests/test_tool_server.py) before this fixture runs, so setting the env var here
    would be too late to influence that already-built module state. Instead we build a
    fresh RuntimePaths from tmp_path ourselves and monkeypatch the already-constructed
    module globals directly, which works regardless of import order.
    """
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
    # raw_key=None is fine here: the encrypted-state file does not exist yet in the
    # temp dir, so get_state() short-circuits to an empty default without touching
    # Fernet/keyring at all (see teacherassist_core/storage.py EncryptedStateStore._load).
    monkeypatch.setattr(
        tool_server, "STATE_STORE", tool_server.EncryptedStateStore(runtime_paths.encrypted_state, None)
    )
    # Avoid a real network round-trip to a possibly-absent local Ollama during bootstrap.
    monkeypatch.setattr(tool_server, "check_ollama", lambda: False)
    # ocr_capability_status() (called from bootstrap) independently builds
    # ENGINE_FACTORIES["ollama_vlm"] and calls .status() on it -- a SEPARATE
    # real network call that the check_ollama stub above does not cover
    # (see tests/conftest.py::stub_ollama_vlm_factory).
    stub_ollama_vlm_factory(monkeypatch)

    # tool_server.logger's RotatingFileHandler is bound to the real LOG_DIR at import
    # time, before this fixture ever runs, so monkeypatching LOG_DIR above does not
    # redirect it. Every request ToolHandler.log_message() logs would otherwise land
    # in the developer's real %LOCALAPPDATA%\TeacherAssist\logs\tool_server.log.
    # Swap in a handler pointed at the isolated tmp_path for the duration of the test.
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
        thread.join(timeout=5)
        tool_server.logger.removeHandler(temp_handler)
        temp_handler.close()
        for handler in original_handlers:
            tool_server.logger.addHandler(handler)


def test_bootstrap_issues_session_then_csrf_gate_blocks_and_allows_api_v1(isolated_server):
    port = isolated_server
    host_header = f"localhost:{port}"

    # GET /api/v1/bootstrap is public (see teacherassist_core/security.py PUBLIC_PATHS)
    # and must hand back a fresh CSRF token plus a session cookie.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host_header})
        response = conn.getresponse()
        body = response.read()
        assert response.status == 200

        payload = json.loads(body)
        csrf_token = payload.get("csrfToken")
        assert isinstance(csrf_token, str) and csrf_token

        set_cookie = response.getheader("Set-Cookie")
        assert set_cookie is not None
        assert tool_server.SESSIONS.COOKIE_NAME in set_cookie
        cookie_value = set_cookie.split(";", 1)[0]
    finally:
        conn.close()


    # A protected /api/v1/ route without cookie/CSRF must be rejected (403).
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/settings", headers={"Host": host_header})
        response = conn.getresponse()
        response.read()
        assert response.status == 403
    finally:
        conn.close()

    # The same route with the session cookie + matching X-CSRF-Token must succeed.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(
            "GET",
            "/api/v1/settings",
            headers={
                "Host": host_header,
                "Cookie": cookie_value,
                "X-CSRF-Token": csrf_token,
            },
        )
        response = conn.getresponse()
        body = response.read()
        assert response.status == 200
        settings_payload = json.loads(body)
        assert "provider" in settings_payload
    finally:
        conn.close()


def test_bootstrap_reuses_an_existing_tab_session(isolated_server):
    """A second bootstrap with the current cookie must not invalidate the
    first tab by replacing its session or CSRF token."""
    port = isolated_server
    host = f"localhost:{port}"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host})
        first = conn.getresponse()
        payload = json.loads(first.read())
        cookie = first.getheader("Set-Cookie").split(";", 1)[0]
    finally:
        conn.close()

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host, "Cookie": cookie})
        second = conn.getresponse()
        repeated = json.loads(second.read())
        assert second.status == 200
        assert repeated["csrfToken"] == payload["csrfToken"]
        assert second.getheader("Set-Cookie") is None
    finally:
        conn.close()


def test_camera_permission_is_granted_to_self(isolated_server):
    """Regression test for the bugfix in tool_server.py ToolHandler.end_headers
    (~line 693): the Permissions-Policy header used to ship `camera=()`, which
    disables the Camera API for this origin outright, so the app's own
    CameraModal (components.jsx:2792) could never call getUserMedia() and always
    got NotAllowedError regardless of OS/browser permission. Hits a real, public
    endpoint through the actual HTTP server and asserts the live response header
    grants the camera to 'self' and no longer carries the disabling `camera=()`."""
    port = isolated_server
    host_header = f"localhost:{port}"

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host_header})
        response = conn.getresponse()
        response.read()
        assert response.status == 200

        permissions_policy = response.getheader("Permissions-Policy")
        assert permissions_policy is not None
        assert "camera=(self)" in permissions_policy
        assert "camera=()" not in permissions_policy
    finally:
        conn.close()


def test_bootstrap_exposes_ocr_capabilities(isolated_server):
    """/api/v1/bootstrap (tool_server.py:~813) must merge
    ocr_capability_status() into "capabilities" and expose the richer
    per-engine list as a top-level "ocrEngines" sibling (Stufe 2 of the OCR
    refactor, teacherassist_core/ocr/engines/__init__.py:
    ocr_capability_status/available_engines). The flat bool map drives
    simple feature gating; ocrEngines carries the "reason" strings Stufe 9's
    settings UI needs to explain e.g. a missing Tesseract binary."""
    port = isolated_server
    host_header = f"localhost:{port}"

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host_header})
        response = conn.getresponse()
        body = response.read()
        assert response.status == 200
    finally:
        conn.close()

    payload = json.loads(body)
    capabilities = payload["capabilities"]
    for key in ("ocrTesseract", "ocrHtr", "ocrVlm", "ocrPaddle", "ocrConsensus"):
        assert key in capabilities
        assert isinstance(capabilities[key], bool)

    ocr_engines = payload["ocrEngines"]
    assert isinstance(ocr_engines, list) and ocr_engines
    for engine_status in ocr_engines:
        assert "name" in engine_status
        assert "available" in engine_status
        assert "reason" in engine_status
        assert "modelId" in engine_status


def test_start_bat_health_probe_matches_versioned_route():
    """Regression test: start.bat's health probe once silently drifted to a bare
    /health path while tool_server.py's real route is /api/v1/health, which broke
    the startup health check. Fail loudly if that divergence ever comes back."""
    start_bat = (REPO_ROOT / "start.bat").read_text(encoding="utf-8")

    assert "localhost:8789/health'" not in start_bat
    assert "localhost:8789/api/v1/health" in start_bat
    # Both probe occurrences (the "already running" check and the startup wait loop).
    assert start_bat.count("localhost:8789/api/v1/health") >= 2


def test_tool_server_still_defines_the_versioned_health_route():
    """Directly checks the server-side half of the start.bat<->tool_server.py
    contract, so a route rename shows up here even if start.bat isn't touched."""
    source = Path(tool_server.__file__).read_text(encoding="utf-8")
    assert 'route == "/api/v1/health"' in source


def test_ocr_image_no_longer_hardcodes_vlm_discovery():
    """Source-contract regression test for the Stufe-5 rewrite of _ocr_image
    (tool_server.py): the inline Ollama-VLM model-discovery list (which
    included the literal "granite3.2-vision") and the ollamaModel
    text-model fallback used AS AN IMAGE MODEL are both gone -- OCR now goes
    exclusively through teacherassist_core.ocr.pipeline.process_single_image_sync.

    "granite3.2-vision" had no other legitimate use in this file and must be
    gone entirely. "gemma3:4b" is different: it is ALSO the general Ollama
    chat-model default used by stream_llm()'s ollama branch and the
    session-summary helpers -- unrelated, pre-existing functionality this
    Stufe does not touch -- so this test only asserts it is gone from
    _ocr_image's own body, not from the whole file."""
    source = Path(tool_server.__file__).read_text(encoding="utf-8")
    assert "granite3.2-vision" not in source

    start = source.index("def _ocr_image(self):")
    end = source.index("\n    def ", start + 1)
    ocr_image_body = source[start:end]
    assert "gemma3:4b" not in ocr_image_body
    assert "qwen3-vl" not in ocr_image_body
    assert "minicpm-v" not in ocr_image_body


def test_new_ocr_settings_survive_round_trip(isolated_server):
    """Regression test for the SETTINGS_KEYS-allowlist trap called out in the
    Stufe-5 task (runtime.py: SettingsStore._write rebuilds its payload from
    SETTINGS_KEYS, so a key added only to DEFAULT_SETTINGS but not to
    SETTINGS_KEYS is silently discarded on the very next save). Saves every
    OCR settings key added in this Stufe with a non-default, valid value,
    then re-reads /api/v1/settings on a FRESH request/connection (simulating
    a reload) and asserts every value survived."""
    port = isolated_server
    host_header = f"localhost:{port}"

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/api/v1/bootstrap", headers={"Host": host_header})
        response = conn.getresponse()
        body = json.loads(response.read())
        csrf_token = body["csrfToken"]
        cookie_value = response.getheader("Set-Cookie").split(";", 1)[0]
    finally:
        conn.close()

    patch = {
        "ocrEngines": ["fake"],
        "ocrVisionModel": "custom-vision-model",
        "ocrHtrModel": "custom-htr-model",
        "ocrPaddleModel": "custom-paddle-model",
        "ocrPaddleBackend": "cpu",
        "ocrTargetDpi": 600,
        "ocrMinAgreement": 0.9,
        "ocrMinConfidence": 0.6,
        "ocrSubject": "Physik",
        "ocrLanguage": "eng",
        "ocrRetentionDays": 30,
        "ocrDeleteAfterApproval": True,
        "ocrAutoApproveNonStudent": True,
        "ocrDevice": "cpu",
        "ocrRequireEngines": ["fake"],
        "ocrMaxPages": 10,
    }

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(
            "POST", "/api/v1/settings",
            body=json.dumps(patch).encode("utf-8"),
            headers={
                "Host": host_header,
                "Cookie": cookie_value,
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json",
            },
        )
        response = conn.getresponse()
        assert response.status == 200
        saved = json.loads(response.read())["settings"]
        for key, value in patch.items():
            assert saved[key] == value, f"{key} did not round-trip through the save response"
    finally:
        conn.close()

    # Fresh connection/request -- proves it was actually persisted, not just
    # echoed back from the in-memory patch of the POST handler.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request(
            "GET", "/api/v1/settings",
            headers={"Host": host_header, "Cookie": cookie_value, "X-CSRF-Token": csrf_token},
        )
        response = conn.getresponse()
        assert response.status == 200
        reloaded = json.loads(response.read())
        for key, value in patch.items():
            assert reloaded[key] == value, f"{key} was dropped on reload (SETTINGS_KEYS allowlist trap)"
    finally:
        conn.close()


def test_static_files_serves_ocr_ui_and_camera_modal_moved_out_of_components():
    """Source-contract regression test for the Stufe-9 OCR review UI move.

    tool_server.py's STATIC_FILES map must serve the new ocr-ui.jsx (needed
    for the unbuilt dev-serving mode; _static() at :802 prefers web_dist/ if
    present, see its docstring/comment), and CameraModal must no longer be
    defined in components.jsx -- it now lives in ocr-ui.jsx and is exposed as
    window.CameraModal (see ocr-ui.jsx's trailing Object.assign(window, ...)).
    The call site in components.jsx (ChatInput) is intentionally unchanged:
    it references the bare identifier CameraModal, which resolves against the
    global object at render time once ocr-ui.jsx has run (src/main.jsx loads
    it before components.jsx)."""
    assert tool_server.STATIC_FILES.get("/ocr-ui.jsx") == "ocr-ui.jsx"

    components_source = (REPO_ROOT / "components.jsx").read_text(encoding="utf-8")
    assert "function CameraModal(" not in components_source
    # The call site must still be present and untouched.
    assert "<CameraModal" in components_source

    ocr_ui_source = (REPO_ROOT / "ocr-ui.jsx").read_text(encoding="utf-8")
    assert "function CameraModal(" in ocr_ui_source
    assert "CameraModal" in ocr_ui_source and "window" in ocr_ui_source
    assert "Object.assign(window" in ocr_ui_source
