"""Fail-closed checks for Ollama models used with sensitive content."""

from __future__ import annotations

import json
import urllib.request


class LocalModelRequired(RuntimeError):
    pass


def _looks_remote(model: str) -> bool:
    normalized = (model or "").strip().lower()
    return normalized.endswith(":cloud") or normalized.endswith("-cloud")


_UPSTREAM_METADATA_KEYS = frozenset({
    "remote_model", "remotemodel", "remote_host", "remotehost",
    "upstream_model", "upstreammodel", "upstream_host", "upstreamhost",
    "cloud_model", "cloudmodel", "cloud_host", "cloudhost",
    "origin_model", "originmodel", "origin_host", "originhost",
})


def _identifies_upstream(value) -> bool:
    """Recognize current and future nested `/api/show` upstream fields."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _UPSTREAM_METADATA_KEYS and item:
                return True
            if _identifies_upstream(item):
                return True
    elif isinstance(value, list):
        return any(_identifies_upstream(item) for item in value)
    return False


def assert_local_ollama_model(model: str, *, endpoint: str = "http://127.0.0.1:11434") -> None:
    """Verify model metadata without including a user prompt in the request.

    Ollama can transparently proxy cloud models through its loopback API.  A
    model tag is rejected immediately, and ``/api/show`` rejects aliases that
    identify an upstream model or host.  Older/failed servers fail closed.
    """
    model = (model or "").strip()
    if not model:
        raise LocalModelRequired("Kein lokales Ollama-Modell ausgewählt.")
    if _looks_remote(model):
        raise LocalModelRequired(f"Das Modell „{model}“ ist ein Ollama-Cloud-Modell.")
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/show",
        data=json.dumps({"name": model}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            metadata = json.loads(response.read())
    except Exception as exc:
        raise LocalModelRequired(
            f"Das lokale Modell „{model}“ konnte nicht verifiziert werden."
        ) from exc
    if not isinstance(metadata, dict):
        raise LocalModelRequired(f"Das lokale Modell „{model}“ konnte nicht verifiziert werden.")
    if _identifies_upstream(metadata):
        raise LocalModelRequired(f"Model {model} is cloud-backed and cannot process sensitive material.")
    remote_model = str(metadata.get("remote_model") or metadata.get("remoteModel") or "")
    remote_host = str(metadata.get("remote_host") or "")
    if remote_model or remote_host or _looks_remote(remote_model):
        raise LocalModelRequired(f"Das Modell „{model}“ wird über Ollama Cloud ausgeführt.")
