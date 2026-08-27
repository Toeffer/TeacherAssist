"""Findet das Tesseract-OCR-Binary und konfiguriert pytesseract, falls vorhanden.

Spiegelt die Suchpfade aus install.bat:68-103 (winget-Installation von
UB-Mannheim.TesseractOCR landet dort, ohne notwendigerweise im PATH zu sein).
Absichtlich ein eigenständiges Modul ohne teure Top-Level-Importe, damit
teacherassist_core/runtime.py und ein späteres ocr/engines/tesseract.py es
günstig importieren können.
"""

from __future__ import annotations

import importlib.util
import os
import shutil

TESSERACT_SEARCH_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)

_cached_binary: str | None = None
_cache_populated = False


def _local_app_data_path() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        return ""
    return os.path.join(local_app_data, "Programs", "Tesseract-OCR", "tesseract.exe")


def tesseract_binary() -> str | None:
    """Findet den Pfad zum tesseract-Binary, falls vorhanden. Ergebnis wird gecacht."""
    global _cached_binary, _cache_populated
    if _cache_populated:
        return _cached_binary

    found = shutil.which("tesseract")
    if not found:
        candidates = list(TESSERACT_SEARCH_PATHS)
        local_app_data_candidate = _local_app_data_path()
        if local_app_data_candidate:
            candidates.append(local_app_data_candidate)
        for candidate in candidates:
            if os.path.isfile(candidate):
                found = candidate
                break

    _cached_binary = found
    _cache_populated = True
    return _cached_binary


def configure_pytesseract() -> bool:
    """Setzt pytesseract.pytesseract.tesseract_cmd auf das gefundene Binary.

    Gibt True zurück, wenn pytesseract importierbar ist UND ein Binary gefunden wurde.
    Wirft nie, auch wenn pytesseract fehlt.
    """
    if importlib.util.find_spec("pytesseract") is None:
        return False

    binary = tesseract_binary()
    if not binary:
        return False

    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = binary
        return True
    except Exception:
        return False
