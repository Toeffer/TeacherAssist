"""The local Ollama endpoint is not sufficient proof of local inference."""

from __future__ import annotations

import io
import json

import pytest

from teacherassist_core.ollama_locality import LocalModelRequired, assert_local_ollama_model


class _Response:
    def __init__(self, payload):
        self._body = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self):
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_cloud_tag_is_rejected_without_a_metadata_probe(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: pytest.fail("must not probe"))
    with pytest.raises(LocalModelRequired):
        assert_local_ollama_model("qwen3:cloud")


def test_upstream_metadata_alias_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: _Response({"details": {"upstream_host": "ollama.com"}}),
    )
    with pytest.raises(LocalModelRequired):
        assert_local_ollama_model("friendly-local-alias")


def test_missing_metadata_probe_fails_closed(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")))
    with pytest.raises(LocalModelRequired):
        assert_local_ollama_model("qwen3:8b")
