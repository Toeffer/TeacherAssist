"""HTTP session security and outbound URL validation."""

from __future__ import annotations

import http.cookies
import ipaddress
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse


PUBLIC_PATHS = {"/api/v1/health", "/api/v1/bootstrap"}
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


@dataclass
class Session:
    csrf: str
    touched_at: float


class SessionManager:
    COOKIE_NAME = "ta_session"
    MAX_AGE_SECONDS = 12 * 60 * 60

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    def create(self) -> tuple[str, str]:
        session_id = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        now = time.time()
        with self._lock:
            self._purge(now)
            self._sessions[session_id] = Session(csrf=csrf, touched_at=now)
        return session_id, csrf

    def validate(self, cookie_header: str, csrf_header: str) -> bool:
        cookies = http.cookies.SimpleCookie()
        try:
            cookies.load(cookie_header or "")
            morsel = cookies.get(self.COOKIE_NAME)
            session_id = morsel.value if morsel else ""
        except Exception:
            return False
        if not session_id or not csrf_header:
            return False
        now = time.time()
        with self._lock:
            self._purge(now)
            session = self._sessions.get(session_id)
            if session is None or not secrets.compare_digest(session.csrf, csrf_header):
                return False
            session.touched_at = now
            return True

    def _purge(self, now: float) -> None:
        expired = [sid for sid, session in self._sessions.items() if now - session.touched_at > self.MAX_AGE_SECONDS]
        for sid in expired:
            self._sessions.pop(sid, None)


def valid_host(host_header: str) -> bool:
    host = (host_header or "").strip().lower()
    if host.startswith("["):
        hostname = host.split("]", 1)[0] + "]"
    else:
        hostname = host.split(":", 1)[0]
    return hostname in ALLOWED_HOSTS


def valid_browser_source(origin: str, sec_fetch_site: str) -> bool:
    if (sec_fetch_site or "").lower() == "cross-site":
        return False
    if not origin:
        return True
    try:
        parsed = urlparse(origin)
        return parsed.scheme == "http" and (parsed.hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}
    except Exception:
        return False


def validate_remote_url(
    url: str,
    *,
    resolver: Callable[..., list] = socket.getaddrinfo,
    allow_http_for_tests: bool = False,
) -> str:
    parsed = urlparse(url)
    allowed_schemes = {"https"}
    if allow_http_for_tests:
        allowed_schemes.add("http")
    if parsed.scheme.lower() not in allowed_schemes or not parsed.hostname:
        raise ValueError("Only HTTPS URLs are permitted")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URLs are not permitted")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}:
        raise ValueError("Unsupported URL port")
    try:
        addresses = resolver(parsed.hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("URL host could not be resolved") from exc
    if not addresses:
        raise ValueError("URL host did not resolve")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private, loopback, link-local, and reserved destinations are blocked")
    return url
