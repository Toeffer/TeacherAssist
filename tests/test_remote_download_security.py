"""SSRF guard (security.validate_remote_url) and the hardened PDF download
(documents.download_pdf) behind POST /api/v1/download-url.

Both take injectable collaborators (a DNS resolver, a URL opener), so these
tests never touch the network: tests/conftest.py fails any test that reaches
a real urllib.request.urlopen().
"""

from __future__ import annotations

import io
import socket

import pytest

from teacherassist_core import documents
from teacherassist_core.documents import _ValidatingRedirectHandler, download_pdf
from teacherassist_core.security import validate_remote_url


def resolver_for(*ips):
    def resolve(host, port, type=socket.SOCK_STREAM):
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, type, 6, "", (ip, port)) for ip in ips]
    return resolve


PUBLIC = resolver_for("93.184.216.34")


def test_public_https_url_is_accepted():
    url = "https://www.example.org/lehrplan.pdf"
    assert validate_remote_url(url, resolver=PUBLIC) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://www.example.org/lehrplan.pdf",
        "ftp://www.example.org/lehrplan.pdf",
        "file:///C:/Windows/win.ini",
        "https://user:secret@www.example.org/lehrplan.pdf",
        "https://www.example.org:8443/lehrplan.pdf",
        "https:///lehrplan.pdf",
    ],
)
def test_unsafe_url_shapes_are_rejected(url):
    with pytest.raises(ValueError):
        validate_remote_url(url, resolver=PUBLIC)


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",          # loopback, e.g. this server or Ollama
        "10.0.0.5",           # school LAN
        "192.168.178.1",      # home router
        "169.254.169.254",    # cloud metadata endpoint
        "::1",
        "::ffff:127.0.0.1",   # IPv4-mapped loopback
        "fd00::1",            # unique local IPv6
    ],
)
def test_non_public_destinations_are_rejected(ip):
    with pytest.raises(ValueError, match="gesperrt"):
        validate_remote_url("https://lehrplan.example/", resolver=resolver_for(ip))


def test_one_private_address_among_public_ones_is_enough_to_reject():
    """DNS can return several records; every one must be public."""
    with pytest.raises(ValueError):
        validate_remote_url("https://lehrplan.example/", resolver=resolver_for("93.184.216.34", "10.0.0.5"))


def test_unresolvable_host_is_rejected_with_a_german_message():
    def failing(*args, **kwargs):
        raise socket.gaierror("no such host")

    with pytest.raises(ValueError, match="nicht gefunden"):
        validate_remote_url("https://does-not-exist.example/", resolver=failing)


def test_redirects_are_validated_before_they_are_followed():
    seen = []

    def validator(url):
        seen.append(url)
        raise ValueError("blocked")

    handler = _ValidatingRedirectHandler(validator)
    with pytest.raises(ValueError):
        handler.redirect_request(None, None, 302, "Found", {}, "https://127.0.0.1/admin")
    assert seen == ["https://127.0.0.1/admin"]


class _Response(io.BytesIO):
    def __init__(self, payload: bytes, content_type: str):
        super().__init__(payload)
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False


class _Opener:
    def __init__(self, payload: bytes, content_type: str = "application/pdf"):
        self.payload = payload
        self.content_type = content_type
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return _Response(self.payload, self.content_type)


def _no_dns(url):
    return url


def test_download_stores_a_valid_pdf(tmp_path):
    opener = _Opener(b"%PDF-1.7\n" + b"x" * 1000)

    path = download_pdf("https://lehrplan.example/a.pdf", tmp_path, validator=_no_dns, opener=opener)

    assert path.parent == tmp_path
    assert path.read_bytes().startswith(b"%PDF")
    assert [item.name for item in tmp_path.iterdir()] == [path.name]


def test_download_validates_the_url_before_opening_it(tmp_path):
    opener = _Opener(b"%PDF-1.7\n")

    def reject(url):
        raise ValueError("gesperrt")

    with pytest.raises(ValueError):
        download_pdf("https://127.0.0.1/a.pdf", tmp_path, validator=reject, opener=opener)
    assert opener.requests == []


@pytest.mark.parametrize(
    "payload, content_type, message",
    [
        (b"<html>Fehlerseite</html>", "text/html", "keine PDF-Datei"),
        (b"MZ\x90\x00 not a pdf", "application/octet-stream", "keine gültige PDF"),
    ],
)
def test_download_rejects_non_pdf_content_and_leaves_no_files(tmp_path, payload, content_type, message):
    opener = _Opener(payload, content_type)

    with pytest.raises(ValueError, match=message):
        download_pdf("https://lehrplan.example/a.pdf", tmp_path, validator=_no_dns, opener=opener)
    assert list(tmp_path.iterdir()) == []


def test_download_stops_at_the_size_limit_and_leaves_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "MAX_REMOTE_PDF_BYTES", 100 * 1024)
    opener = _Opener(b"%PDF-1.7\n" + b"x" * (200 * 1024))

    with pytest.raises(ValueError, match="50 MB"):
        download_pdf("https://lehrplan.example/a.pdf", tmp_path, validator=_no_dns, opener=opener)
    assert list(tmp_path.iterdir()) == []
