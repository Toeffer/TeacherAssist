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
