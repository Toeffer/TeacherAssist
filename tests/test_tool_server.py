import io
import json
import urllib.error

import pytest

import tool_server
from teacherassist_core.privacy import PrivacyDecision, anonymize_text, decide_privacy

try:
    import chromadb  # noqa: F401

    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


def test_apply_request_overrides_uses_resolved_provider_and_models():
    settings = {"provider": "openrouter", "model": "cloud", "ollamaModel": "local"}
    data = {
        "providerOverride": "ollama",
        "modelOverride": "cloud-2",
        "ollamaModelOverride": "local-2",
        "apiKey": "sk-test",  # apiKey is intentionally NOT forwarded (security fix)
    }

    result = tool_server.apply_request_overrides(settings, data)

    assert result["provider"] == "ollama"
    assert result["model"] == "cloud-2"
    assert result["ollamaModel"] == "local-2"
    assert "apiKey" not in result  # apiKey must never be accepted per-request


def test_apply_request_overrides_rejects_unknown_provider():
    settings = {"provider": "openrouter"}

    result = tool_server.apply_request_overrides(settings, {"providerOverride": "surprise"})

    assert result["provider"] == "openrouter"


def test_personal_data_detection_and_anonymization():
    text = "Kontakt: max@example.de, Tel. 030 1234567, geboren am 01.02.2010"

    findings = tool_server.detect_personal_data(text)
    anonymized = anonymize_text(text)

    assert {item["type"] for item in findings} >= {"E-Mail-Adresse", "Telefonnummer", "Geburtsdatum"}
    assert "max@example.de" not in anonymized
    assert "030 1234567" not in anonymized
    assert "01.02.2010" not in anonymized


def test_memory_zip_destination_accepts_only_memory_paths():
    safe = tool_server.memory_zip_destination("./memory/lehrerprofil.md")

    assert safe is not None
    dest, norm = safe
    assert norm == "memory/lehrerprofil.md"
    assert dest.name == "lehrerprofil.md"
    assert dest.parent == tool_server.MEMORY_DIR.resolve()
    assert tool_server.memory_zip_destination("other/file.md") is None


def test_memory_zip_destination_rejects_traversal():
    with pytest.raises(ValueError):
        tool_server.memory_zip_destination("memory/../app.jsx")


# ---------------------------------------------------------------------------
# search_rag() <-> decide_privacy(): the classification must round-trip through
# ChromaDB metadata, not silently fall back to a hardcoded value that would
# force every RAG-hit chat into local-only mode regardless of the real
# document classification.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not HAS_CHROMADB,
    reason="chromadb is not installed in tools/.venv; skipping the search_rag() classification round-trip",
)
def test_search_rag_round_trips_document_classification(tmp_path, monkeypatch):
    monkeypatch.setattr(tool_server, "_col", None)
    monkeypatch.setattr(tool_server, "_ef", None)
    monkeypatch.setattr(tool_server, "CHROMA_DIR", tmp_path / "chroma")

    collection, _ = tool_server.get_collection()
    collection.add(
        documents=["Im Lehrplan Klasse 6 wird die Bruchrechnung eingefuehrt."],
        ids=["test-doc-public:0"],
        metadatas=[{
            "source": "test",
            "classification": "public_curriculum",
            "chunk": 0,
            "document_id": "test-doc-public",
        }],
    )
    _, public_classifications = tool_server.search_rag("Bruchrechnung Klasse 6")
    assert "public_curriculum" in public_classifications
    assert "unknown" not in public_classifications

    collection.add(
        documents=["Persoenliche Foerdernotiz fuer einen einzelnen Schueler."],
        ids=["test-doc-personal:0"],
        metadatas=[{
            "source": "test",
            "classification": "personal",
            "chunk": 0,
            "document_id": "test-doc-personal",
        }],
    )
    _, personal_classifications = tool_server.search_rag("Persoenliche Foerdernotiz Schueler")
    assert "personal" in personal_classifications


def test_decide_privacy_allows_cloud_for_public_curriculum_documents():
    decision = decide_privacy(
        messages=[{"role": "user", "text": "Was steht im Lehrplan zur Bruchrechnung?"}],
        skill_id=None,
        document_classifications=["public_curriculum"],
    )

    assert decision.local_required is False


def test_decide_privacy_forces_local_for_non_public_documents():
    decision = decide_privacy(
        messages=[{"role": "user", "text": "Was steht im Lehrplan zur Bruchrechnung?"}],
        skill_id=None,
        document_classifications=["personal"],
    )

    assert decision.local_required is True
    assert "document_not_public" in decision.reasons


class _FakeStreamResponse:
    """Minimal stand-in for the urlopen() context manager used by stream_llm."""

    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self, size=-1):
        return self._stream.read(size)


def _run_cloud_stream(monkeypatch, upstream=None, raises=None):
    def fake_urlopen(request, *args, **kwargs):
        if raises is not None:
            raise raises
        return _FakeStreamResponse(upstream)

    monkeypatch.setattr(tool_server.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(tool_server.CREDENTIALS, "get", lambda name: "sk-test")
    out = io.BytesIO()
    text = tool_server.stream_llm(
        [{"role": "user", "text": "Hallo"}],
        {},
        {"provider": "openrouter", "model": "some/model"},
        wfile=out,
        privacy_decision=PrivacyDecision("cloud_allowed", ()),
    )
    events = [
        json.loads(block[len("data: "):])
        for block in out.getvalue().decode("utf-8").split("\n\n")
        if block.startswith("data: ")
    ]
    return text, events


def test_stream_tolerates_chunks_without_choices(monkeypatch):
    """OpenRouter ends a stream with a usage-only chunk whose "choices" list
    is empty, and Azure starts one with a prompt-filter chunk shaped the same
    way. Indexing choices[0] used to raise IndexError, which replaced a
    complete answer with a PROVIDER_ERROR in the UI."""
    upstream = (
        b'data: {"choices":[],"prompt_filter_results":[]}\n\n'
        b'data:{"choices":[{"delta":{"content":"Hallo"}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":" Welt"}}]}\n\n'
        b'data: {"choices":[],"usage":{"total_tokens":5}}\n\n'
        b"data: [DONE]\n\n"
    )

    text, events = _run_cloud_stream(monkeypatch, upstream)

    assert text == "Hallo Welt"
    types = [event["type"] for event in events]
    assert "error" not in types
    assert types[-1] == "done"
    assert {"type": "usage", "usage": {"total_tokens": 5}} in events


def test_stream_surfaces_mid_stream_provider_error(monkeypatch):
    upstream = (
        b'data: {"choices":[{"delta":{"content":"Teil"}}]}\n\n'
        b'data: {"error":{"code":502,"message":"upstream overloaded"},"choices":[]}\n\n'
    )

    text, events = _run_cloud_stream(monkeypatch, upstream)

    assert text == "Teil"
    errors = [event for event in events if event["type"] == "error"]
    assert len(errors) == 1
    assert "upstream overloaded" in errors[0]["message"]
    assert events[-1]["type"] == "done"


@pytest.mark.parametrize(
    "status, expected",
    [
        (401, "API-Key"),
        (402, "Guthaben"),
        (404, "„some/model“"),
        (429, "zu viele Anfragen"),
        (503, "HTTP 503"),
    ],
)
def test_stream_maps_http_errors_to_actionable_messages(monkeypatch, status, expected):
    error = urllib.error.HTTPError("https://openrouter.ai", status, "error", {}, None)

    text, events = _run_cloud_stream(monkeypatch, raises=error)

    assert text == ""
    errors = [event for event in events if event["type"] == "error"]
    assert len(errors) == 1
    assert expected in errors[0]["message"]


@pytest.mark.parametrize(
    "filename, ascii_fallback",
    [
        ("20261003_120000_übung_brüche.md", "20261003_120000_uebung_brueche.md"),
        ("20261003_120000_arbeitsblatt_ελληνικά.md", "20261003_120000_arbeitsblatt_.md"),
        ("20261003_120000_wortschatz_日本語.html", "20261003_120000_wortschatz_.html"),
    ],
)
def test_content_disposition_is_latin1_safe_and_keeps_the_utf8_name(filename, ascii_fallback):
    """http.server encodes headers as Latin-1; a Greek or Japanese export
    title used to raise inside send_header() after the 200 status line."""
    from urllib.parse import unquote

    header = tool_server.content_disposition(filename)

    header.encode("latin-1")  # must not raise
    assert f'filename="{ascii_fallback}"' in header
    assert unquote(header.split("filename*=UTF-8''", 1)[1]) == filename


@pytest.mark.parametrize("name", ["gemma3:4b", "qwen3-vl:8b", "fhswf/TrOCR_german_handwritten", "hf.co/org/model@main"])
def test_model_name_pattern_accepts_real_model_ids(name):
    assert tool_server.MODEL_NAME_RE.fullmatch(name)


@pytest.mark.parametrize("name", ["--insecure", "-h", "../etc", "", "a b", "x;rm -rf", "a" * 101])
def test_model_name_pattern_rejects_option_like_and_unsafe_values(name):
    """These values reach `ollama pull <name>` as a subprocess argument; a
    leading "-" would be parsed as a command-line option."""
    assert not tool_server.MODEL_NAME_RE.fullmatch(name)


@pytest.mark.parametrize(
    "file_path",
    ["../settings.json", "../../outside.md", "/etc/passwd.md", "students/index.md", "Students/index.md", "notes.txt", "", None, 42],
)
def test_memory_markdown_path_rejects_anything_but_markdown_inside_memory(file_path):
    assert tool_server.memory_markdown_path(file_path) is None


def test_memory_markdown_path_accepts_nested_markdown():
    target = tool_server.memory_markdown_path(" bewertungsraster/mathe_7_brueche.md ")

    assert target == (tool_server.MEMORY_DIR / "bewertungsraster" / "mathe_7_brueche.md").resolve()


@pytest.mark.parametrize("key", ["privacy_mode", "privacyMode"])
def test_both_privacy_mode_spellings_are_honoured(key):
    """/chats/{id}/messages read only privacy_mode while the streaming code
    read both, so privacyMode applied to one answer without marking the chat
    local for the next message."""
    assert tool_server.requested_privacy_mode({key: "local_required"}) == "local_required"
    assert tool_server.requested_privacy_mode({}) == "auto"
