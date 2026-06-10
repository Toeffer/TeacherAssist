#!/usr/bin/env python3
"""
OCR Reader Tool für LehrerAgent

Liest Text aus gescannten PDFs und Bilddateien (Fotos von Schülerarbeiten).
Verwendet Tesseract OCR für Texterkennung.
"""

import sys
import json
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional


def setup_tesseract():
    """Versucht, Tesseract zu konfigurieren mit Plattform-spezifischen Pfaden."""
    try:
        import pytesseract
        
        # Plattform-spezifische Tesseract-Pfade
        if os.name == 'nt':  # Windows
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.join(os.environ.get('ProgramFiles', ''), "Tesseract-OCR", "tesseract.exe"),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), "Tesseract-OCR", "tesseract.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        # Unix/Mac: Standardpfad sollte funktionieren
        return pytesseract
    except ImportError:
        raise ImportError("pytesseract nicht installiert. Bitte installieren: pip install pytesseract")


def extract_text_from_image(image_path: Path, language: str = "deu") -> Tuple[str, float]:
    """Extrahiert Text aus einem Bild mit Tesseract OCR."""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow nicht installiert. Bitte installieren: pip install Pillow")
    
    pytesseract = setup_tesseract()
    
    # Bild öffnen
    try:
        img = Image.open(image_path)
    except Exception as e:
        raise ValueError(f"Kann Bild nicht öffnen: {e}")
    
    # OCR durchführen
    try:
        # Konfiguration für bessere Genauigkeit
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(img, lang=language, config=custom_config)
        
        # Zusätzliche Daten für Konfidenz (falls verfügbar)
        try:
            data = pytesseract.image_to_data(img, lang=language, config=custom_config, output_type=pytesseract.Output.DICT)
            confidences = [float(c) for c in data['conf'] if int(c) != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        except:
            avg_confidence = 0.0
        
        return text.strip(), avg_confidence
    except Exception as e:
        raise RuntimeError(f"OCR-Fehler: {e}")


def extract_text_from_pdf(pdf_path: Path, language: str = "deu") -> Tuple[str, float]:
    """Extrahiert Text aus einer gescannten PDF (konvertiert jede Seite zu Bildern)."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("pdf2image nicht installiert. Bitte installieren: pip install pdf2image")
    
    # Temporäres Verzeichnis für Konvertierung
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # PDF in Bilder konvertieren
            images = convert_from_path(
                pdf_path,
                dpi=300,  # Hohe DPI für bessere OCR
                output_folder=temp_dir,
                fmt='png',
                thread_count=2
            )
        except Exception as e:
            raise ValueError(f"PDF-Konvertierung fehlgeschlagen: {e}")
        
        if not images:
            return "", 0.0
        
        # OCR auf jedem Bild durchführen
        all_texts = []
        all_confidences = []
        
        for i, image in enumerate(images):
            # Temporäres Bild speichern
            temp_image_path = Path(temp_dir) / f"page_{i+1}.png"
            image.save(temp_image_path, 'PNG')
            
            # OCR auf dieser Seite
            try:
                text, confidence = extract_text_from_image(temp_image_path, language)
                if text:
                    all_texts.append(f"--- Seite {i+1} ---\n{text}")
                    all_confidences.append(confidence)
            except Exception as e:
                # Seite überspringen, aber Warnung protokollieren
                all_texts.append(f"--- Seite {i+1} (OCR fehlgeschlagen: {e}) ---")
                all_confidences.append(0.0)
        
        # Durchschnittliche Konfidenz berechnen
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        full_text = "\n\n".join(all_texts)
        
        return full_text, avg_confidence


def get_file_type(filepath: Path) -> str:
    """Bestimmt den Dateityp anhand der Endung."""
    ext = filepath.suffix.lower()
    if ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']:
        return 'image'
    else:
        raise ValueError(f"Nicht unterstützter Dateityp: {ext}")


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
        
        language = args.get("language", "deu")
        
        # Pfad validieren
        filepath = Path(filepath_str)
        if not filepath.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")
        
        if not filepath.is_file():
            raise ValueError(f"Pfad ist keine Datei: {filepath}")
        
        # Dateityp bestimmen und entsprechend verarbeiten
        file_type = get_file_type(filepath)
        
        if file_type == 'pdf':
            text, confidence = extract_text_from_pdf(filepath, language)
        else:  # image
            text, confidence = extract_text_from_image(filepath, language)
        
        # Warnung bei niedriger Konfidenz (Handschrift)
        warning = None
        if confidence < 60:
            warning = f"Warnung: OCR-Konfidenz ist niedrig ({confidence:.1f}%). Handschriftliche Schülerarbeiten haben oft niedrige Konfidenzwerte. Bitte Ergebnisse überprüfen."
        
        # Output
        output = {
            "success": True,
            "text": text,
            "confidence": round(confidence, 2),
            "warning": warning,
            "error": None
        }
        
    except Exception as e:
        output = {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "warning": None,
            "error": str(e)
        }
    
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()