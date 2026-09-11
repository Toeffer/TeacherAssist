"""PDF page loading must keep bytes as bytes for PDFium."""

from __future__ import annotations

import sys
import types

from teacherassist_core.documents import iter_pdf_pages


def test_iter_pdf_pages_passes_pdf_bytes_directly_to_pdfium(monkeypatch):
    captured = []

    class Image:
        size = (100, 200)

    class Bitmap:
        def to_pil(self):
            return Image()

        def close(self):
            pass

    class Page:
        def render(self, scale):
            assert scale > 0
            return Bitmap()

        def close(self):
            pass

    class Document:
        def __init__(self, source):
            captured.append(source)

        def __len__(self):
            return 1

        def __getitem__(self, index):
            return Page()

        def close(self):
            pass

    monkeypatch.setitem(sys.modules, "pypdfium2", types.SimpleNamespace(PdfDocument=Document))
    pages = list(iter_pdf_pages(b"%PDF-test", target_dpi=200))
    assert len(pages) == 1
    assert captured == [b"%PDF-test"]
