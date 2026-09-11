"""PDF extraction and hardened remote PDF downloads."""

from __future__ import annotations

import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Iterator

from .ocr.page_render import PageImage
from .security import validate_remote_url


MAX_REMOTE_PDF_BYTES = 50 * 1024 * 1024


def extract_pdf_text(path: Path) -> str:
    """Extract text with pypdf and OCR sparse/scanned pages with PDFium."""
    text_parts: list[str] = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception:
        text_parts = []
    combined = "\n\n".join(part for part in text_parts if part).strip()
    if len(combined) >= 100:
        return combined

    try:
        import pypdfium2 as pdfium
        import pytesseract

        document = pdfium.PdfDocument(str(path))
        ocr_parts: list[str] = []
        for index in range(len(document)):
            page = document[index]
            bitmap = page.render(scale=2.0)
            image = bitmap.to_pil()
            ocr_parts.append(pytesseract.image_to_string(image, lang="deu").strip())
            image.close()
            page.close()
        document.close()
        ocr = "\n\n".join(part for part in ocr_parts if part).strip()
        return ocr or combined
    except Exception:
        return combined


def iter_pdf_pages(
    path: Path | bytes,
    *,
    target_dpi: int = 350,
    max_pages: int = 40,
) -> Iterator[PageImage]:
    """Rendert die Seiten von `path` als PIL-Bilder, EINE nach der anderen.

    MUSS ein Generator sein, kein Listen-Aufbau: Eine 350-dpi-A4-RGB-Seite
    ist 2894x4093 Pixel (siehe render_pdf_pages()-Kommentar zur genauen
    Herleitung des Skalierungsfaktors), das sind ~35 MB unkomprimiert. Bei 40
    Seiten waeren das eager ueber 1.4 GB Resident-Speicher fuer ein einziges
    Dokument -- inakzeptabel fuer einen Prozess, der mehrere Dokumente
    parallel verarbeiten koennte. Als Generator wird stattdessen jeweils nur
    die gerade konsumierte Seite im Speicher gehalten.

    pypdfium2s `scale`-Parameter ist relativ zu 72 dpi (gegen die
    installierte pypdfium2-Version verifiziert, nicht nur angenommen):
    ``scale = target_dpi / 72.0`` liefert bei einer A4-Seite und
    target_dpi=350 ein 2894x4093-Bild. Seite und Bitmap werden nach jedem
    Yield in einem `finally` geschlossen (die Aufruferin haelt zwischen zwei
    `next()`-Aufrufen jeweils nur eine PDFium-Seite offen), das Dokument am
    Ende in einem aeusseren `finally`.

    Eigentumsvertrag: die Aufruferin besitzt das per `yield` gelieferte
    PIL-Bild (`PageImage.image`) und ist fuer dessen Lebensdauer
    verantwortlich -- dieses Modul haelt danach keine Referenz mehr darauf.
    """
    import pypdfium2 as pdfium

    scale = target_dpi / 72.0
    document = pdfium.PdfDocument(path if isinstance(path, bytes) else str(path))
    try:
        page_count = min(len(document), max_pages)
        for index in range(page_count):
            page = document[index]
            try:
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil()
                finally:
                    bitmap.close()
                width, height = image.size
                yield PageImage(index=index, image=image, dpi=target_dpi, width=width, height=height)
            finally:
                page.close()
    finally:
        document.close()


def render_pdf_pages(
    path: Path,
    *,
    target_dpi: int = 350,
    max_pages: int = 8,
) -> list[PageImage]:
    """Eager-Variante von `iter_pdf_pages` fuer Aufrufer, die wirklich eine
    Liste brauchen (z.B. um mehrfach durch die Seiten zu iterieren).

    `max_pages` ist hier bewusst niedriger als bei `iter_pdf_pages`
    (8 statt 40): siehe `iter_pdf_pages`-Docstring zur Speicherrechnung --
    8 eager gehaltene 350-dpi-A4-RGB-Seiten sind bereits ~280 MB, was fuer
    einen bewussten "gib mir alle Seiten als Liste"-Aufruf akzeptabel ist,
    waehrend derselbe Default fuer ein 40-seitiges Dokument (~1.4 GB) es
    nicht waere. Wer wirklich mehr eager gerenderte Seiten braucht, kann
    `max_pages` explizit hochsetzen."""
    return list(iter_pdf_pages(path, target_dpi=target_dpi, max_pages=max_pages))


class _ValidatingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, validator: Callable[[str], str]) -> None:
        super().__init__()
        self.validator = validator

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.validator(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_pdf(
    url: str,
    destination_dir: Path,
    *,
    validator: Callable[[str], str] = validate_remote_url,
    opener=None,
) -> Path:
    validator(url)
    destination_dir.mkdir(parents=True, exist_ok=True)
    active_opener = opener or urllib.request.build_opener(_ValidatingRedirectHandler(validator))
    request = urllib.request.Request(url, headers={"User-Agent": "TeacherAssist/2.0"})
    fd, temp_name = tempfile.mkstemp(prefix="download-", suffix=".pdf.part", dir=destination_dir)
    total = 0
    first = b""
    try:
        with os.fdopen(fd, "wb") as target, active_opener.open(request, timeout=30) as response:
            content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            if content_type not in {"application/pdf", "application/octet-stream"}:
                raise ValueError("Remote resource is not a PDF")
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                if not first:
                    first = chunk[:8]
                total += len(chunk)
                if total > MAX_REMOTE_PDF_BYTES:
                    raise ValueError("Remote PDF exceeds 50 MB")
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if not first.startswith(b"%PDF"):
            raise ValueError("Remote resource has no PDF signature")
        destination = destination_dir / f"document-{os.urandom(12).hex()}.pdf"
        os.replace(temp_name, destination)
        return destination
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
