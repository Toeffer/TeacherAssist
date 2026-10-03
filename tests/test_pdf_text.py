"""Curriculum PDF text extraction (documents.read_pdf_text): scanned PDFs are
OCR'd inside the ingest request, so the number of OCR pages is capped and
reported instead of blocking for minutes on a long scan."""

from __future__ import annotations

import pytest
from PIL import Image

from teacherassist_core import documents

pytesseract = pytest.importorskip("pytesseract")


def scanned_pdf(path, pages):
    """An image-only PDF: no text layer, like a scanned document."""
    images = [Image.new("RGB", (200, 280), "white") for _ in range(pages)]
    images[0].save(path, "PDF", save_all=True, append_images=images[1:])
    return path


@pytest.fixture
def fake_ocr(monkeypatch):
    calls = []

    def image_to_string(image, lang=None):
        calls.append(lang)
        return f"Erkannter Lehrplantext Seite {len(calls)}"

    monkeypatch.setattr(pytesseract, "image_to_string", image_to_string)
    return calls


def test_long_scans_are_ocr_capped_and_reported(tmp_path, fake_ocr):
    result = documents.read_pdf_text(scanned_pdf(tmp_path / "scan.pdf", 5), max_ocr_pages=3)

    assert len(fake_ocr) == 3
    assert (result.total_pages, result.ocr_pages, result.ocr_truncated) == (5, 3, True)
    assert "Seite 3" in result.text and "Seite 4" not in result.text


def test_short_scans_are_read_completely(tmp_path, fake_ocr):
    result = documents.read_pdf_text(scanned_pdf(tmp_path / "scan.pdf", 2), max_ocr_pages=3)

    assert fake_ocr == ["deu", "deu"]
    assert (result.total_pages, result.ocr_pages, result.ocr_truncated) == (2, 2, False)


def test_pdfs_with_a_text_layer_are_not_ocrd(tmp_path, fake_ocr):
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    path = tmp_path / "text.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, "Kompetenzerwartungen Mathematik Klasse 7: Bruchrechnung, " * 3)
    pdf.save()

    result = documents.read_pdf_text(path)

    assert fake_ocr == []
    assert result.ocr_pages == 0 and not result.ocr_truncated
    assert "Bruchrechnung" in result.text
    assert documents.extract_pdf_text(path) == result.text
