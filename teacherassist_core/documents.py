"""PDF extraction and hardened remote PDF downloads."""

from __future__ import annotations

import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

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
