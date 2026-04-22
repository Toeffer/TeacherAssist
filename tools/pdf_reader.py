#!/usr/bin/env python3
"""
PDF Reader Tool für LehrerAgent

Liest Text-PDFs ein (Lehrpläne, die nicht gescannt sind).
Verwendet pypdf für Text-Extraktion.
"""

import sys
import json
import os
from pathlib import Path


def read_pdf_text(filepath: Path, pages: list = None) -> tuple[str, int]:
    """
    Liest Text aus PDF und gibt (text, page_count) zurück.
    pages: Liste von 1-basierten Seitenzahlen, None für alle Seiten.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        # Fallback falls pypdf nicht installiert ist
        raise ImportError("pypdf nicht installiert. Bitte installieren: pip install pypdf")
    
    reader = PdfReader(filepath)
    page_count = len(reader.pages)
    
    if pages:
        # Filtere ungültige Seitenzahlen
        valid_pages = [p for p in pages if 1 <= p <= page_count]
        if not valid_pages:
            return "", page_count
        selected_pages = [reader.pages[p-1] for p in valid_pages]
    else:
        selected_pages = reader.pages
    
    texts = []
    for page in selected_pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    
    return "\n\n".join(texts), page_count


def main():
    try:
        # JSON Input parsen
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
        else:
            # Fallback: von stdin lesen
            args = json.load(sys.stdin)
        
        # Input validieren
        filepath_str = args.get("filepath")
        if not filepath_str:
            raise ValueError("'filepath' ist erforderlich")
        
        pages = args.get("pages")  # Kann None sein oder Liste
        
        # Pfad validieren
        filepath = Path(filepath_str)
        if not filepath.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")
        
        if not filepath.is_file():
            raise ValueError(f"Pfad ist keine Datei: {filepath}")
        
        # PDF lesen
        text, page_count = read_pdf_text(filepath, pages)
        
        # Prüfen ob Text zu kurz (möglicher Scan)
        text_length = len(text.strip())
        scan_warning = None
        if text_length < 100:
            scan_warning = f"Warnung: Extrahierter Text ist sehr kurz ({text_length} Zeichen). Möglicherweise ist die PDF ein Scan. Fallback auf OCR empfohlen."
        
        # Output
        output = {
            "success": True,
            "text": text,
            "page_count": page_count,
            "warning": scan_warning if text_length < 100 else None,
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "text": "",
            "page_count": 0,
            "warning": None,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()