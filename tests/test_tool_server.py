from pathlib import Path

import pytest

import tool_server
from teacherassist_core.privacy import decide_privacy

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
    anonymized = tool_server.anonymize_text(text)

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


def test_memory_update_creates_an_undo_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(tool_server, "MEMORY_DIR", tmp_path)
    target = tmp_path / "begleiter_gedaechtnis.md"
    original = "# Gedächtnis\n> Zuletzt aktualisiert: alt\n\n## Laufende Themen\n(Automatisch aktualisiert)\n"
    target.write_text(original, encoding="utf-8")

    result = tool_server.apply_memory_updates(
        "begleiter_gedaechtnis.md",
        [("Laufende Themen", "- 07.08.2026 · Bruchrechnung · Mathematik · Klasse 7a", 15)],
    )

    assert result["Laufende Themen"]
    assert "Bruchrechnung" in target.read_text(encoding="utf-8")
    assert Path(str(target) + ".bak1").read_text(encoding="utf-8") == original


def test_memory_fact_extraction_rejects_personal_context():
    safe = tool_server.extract_memory_fact(
        "Plane zum Thema Bruchrechnung für Mathematik in Klasse 7a.",
        "unterricht_planen",
        {"faecher": ["Mathematik 7a"]},
    )
    personal = tool_server.extract_memory_fact(
        "Plane zum Thema Bruchrechnung für Schüler Max in Klasse 7a.",
        "unterricht_planen",
        {"faecher": ["Mathematik 7a"]},
    )

    assert safe == "Bruchrechnung · Mathematik · Klasse 7a"
    assert personal is None


def test_stream_emits_memory_event_before_done(monkeypatch):
    class FakeResponse:
        def __init__(self):
            self._chunks = [
                b'data: {"choices":[{"delta":{"content":"Hallo"}}]}\n\ndata: [DONE]\n\n',
                b"",
            ]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _size):
            return self._chunks.pop(0)

    events = []
    monkeypatch.setattr(tool_server.urllib.request, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    monkeypatch.setattr(tool_server, "_send_sse", lambda _wfile, event: events.append(event))

    answer = tool_server.stream_llm(
        messages=[{"role": "user", "text": "Hallo"}],
        profile={},
        settings={"provider": "ollama", "ollamaModel": "test"},
        wfile=object(),
        on_success=lambda: {"type": "memory_saved", "items": ["Test"]},
    )

    assert answer == "Hallo"
    assert [event["type"] for event in events][-3:] == ["chunk", "memory_saved", "done"]


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
