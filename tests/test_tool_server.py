import pytest

import tool_server
from tools import lehrplan_indexer, lehrplan_searcher, memory_reader, memory_writer


def test_apply_request_overrides_uses_resolved_provider_and_models():
    settings = {"provider": "openrouter", "model": "cloud", "ollamaModel": "local"}
    data = {
        "providerOverride": "ollama",
        "modelOverride": "cloud-2",
        "ollamaModelOverride": "local-2",
        "apiKey": "sk-test",
    }

    result = tool_server.apply_request_overrides(settings, data)

    assert result["provider"] == "ollama"
    assert result["model"] == "cloud-2"
    assert result["ollamaModel"] == "local-2"
    assert result["apiKey"] == "sk-test"


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


def test_repo_local_memory_and_chroma_paths():
    repo_root = tool_server.BASE_DIR.resolve()

    assert memory_reader.get_memory_path("lehrerprofil.md").resolve() == repo_root / "memory" / "lehrerprofil.md"
    assert memory_writer.get_memory_path("vergangene_stunden.md").resolve() == repo_root / "memory" / "vergangene_stunden.md"
    assert lehrplan_indexer.get_chromadb_path().resolve() == repo_root / "tools" / "chroma_db"
    assert lehrplan_searcher.get_chromadb_path().resolve() == repo_root / "tools" / "chroma_db"
