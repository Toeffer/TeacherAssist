import zipfile

import pytest

from tools import document_export


def _sample_student() -> dict:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "identity": {
            "vorname": "Anna",
            "nachname": "Müller",
            "pronomen": "sie",
            "alias": "SuS-01",
        },
        "klasse": "7a",
        "competencies": {
            "Deutsch": {
                "Leseverstehen": {"rating": 3, "scale": "1-4", "last_update": "2026-05-12", "note": ""},
                "Schreiben":     {"rating": 2, "scale": "1-4", "last_update": "2026-05-12", "note": "ausbaufähig"},
            },
            "Mathematik": {
                "Bruchrechnung": {"rating": 4, "scale": "1-4", "last_update": "2026-05-12", "note": ""},
            },
        },
        "observations": [],
    }


def test_name_reinsertion_sie():
    text = "{NAME} zeigt im Unterricht, dass {er/sie} aufmerksam ist. {Sein/Ihr} Lesetempo ist gut."
    out = document_export._name_reinsertion(text, {"vorname": "Anna", "pronomen": "sie"})
    assert out == "Anna zeigt im Unterricht, dass sie aufmerksam ist. Ihr Lesetempo ist gut."


def test_name_reinsertion_er():
    text = "{NAME} arbeitet konzentriert. {Er/sie} bringt {sein/ihr} Material immer mit."
    out = document_export._name_reinsertion(text, {"vorname": "Ben", "pronomen": "er"})
    assert out == "Ben arbeitet konzentriert. Er bringt sein Material immer mit."


def test_name_reinsertion_falls_back_to_alias_when_no_vorname():
    text = "{NAME} arbeitet gut."
    out = document_export._name_reinsertion(text, {"alias": "SuS-01", "pronomen": "sie"})
    assert out == "SuS-01 arbeitet gut."


def test_schuljahr_aus_datum():
    from datetime import datetime as dt
    assert document_export._schuljahr_aus_datum(dt(2026, 5, 15)) == "2025/26"
    assert document_export._schuljahr_aus_datum(dt(2026, 9, 1)) == "2026/27"
    assert document_export._schuljahr_aus_datum(dt(2026, 8, 1)) == "2026/27"
    assert document_export._schuljahr_aus_datum(dt(2026, 7, 31)) == "2025/26"


def test_format_rating_with_scale():
    assert document_export._format_rating({"rating": 3, "scale": "1-4"}) == "3 / 4"
    assert document_export._format_rating({"rating": 2}) == "2"
    assert document_export._format_rating({"scale": "1-4"}) == ""


def test_generate_docx_writes_valid_file(tmp_path):
    out = tmp_path / "wortgutachten.docx"
    narrative = "{NAME} arbeitet zuverlässig. {Sein/Ihr} Verständnis von Bruchrechnung wächst stetig."
    document_export.generate_wortgutachten_docx(
        _sample_student(), narrative, out, schuljahr="2025/26", datum="2026-05-15"
    )
    assert out.exists()
    assert out.stat().st_size > 1000
    # DOCX = ZIP. Document.xml soll Klarname enthalten.
    with zipfile.ZipFile(out) as z:
        with z.open("word/document.xml") as f:
            xml_bytes = f.read()
    assert "Anna" in xml_bytes.decode("utf-8")
    assert "Bruchrechnung" in xml_bytes.decode("utf-8")
    assert "Verbale Einschätzung" in xml_bytes.decode("utf-8")
    # Platzhalter darf NICHT im Output erscheinen
    assert "{NAME}" not in xml_bytes.decode("utf-8")
    assert "{Sein/Ihr}" not in xml_bytes.decode("utf-8")


def test_generate_pdf_via_reportlab_directly(tmp_path):
    """Erzwingt den Fallback-Pfad ohne MS Word."""
    out = tmp_path / "wortgutachten.pdf"
    narrative = "{NAME} arbeitet zuverlässig. {Sein/Ihr} Lesetempo ist altersgerecht."
    document_export._pdf_via_reportlab(
        _sample_student(), narrative, out, schuljahr="2025/26", datum="2026-05-15"
    )
    assert out.exists()
    head = out.read_bytes()[:4]
    assert head == b"%PDF"


def test_generate_pdf_uses_fallback_when_docx2pdf_fails(tmp_path, monkeypatch):
    """Wenn docx2pdf wirft, soll der reportlab-Fallback einspringen."""
    def _broken(*a, **kw):
        raise RuntimeError("simulated: word not installed")
    monkeypatch.setattr(document_export, "_pdf_via_docx2pdf", _broken)

    out = tmp_path / "wortgutachten.pdf"
    document_export.generate_wortgutachten_pdf(
        _sample_student(), "{NAME} arbeitet gut.", out, datum="2026-05-15"
    )
    assert out.exists()
    assert out.read_bytes()[:4] == b"%PDF"
