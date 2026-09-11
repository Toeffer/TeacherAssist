"""Seitenweises Laden von Dokumentquellen (PDF oder Einzelbild) als PIL-Bilder
(Stufe 3 des grossen OCR-Refactors).

``PageImage`` ist hier statt in ``documents.py`` definiert: ``load_pages()``
muss fuer PDF-Quellen auf ``documents.iter_pdf_pages()`` dispatchen, und
``documents.py`` importiert im Gegenzug ``PageImage`` als Rueckgabetyp fuer
``iter_pdf_pages``/``render_pdf_pages``. Wuerde ``documents.py`` stattdessen
den Typ definieren und dieses Modul ihn importieren, entstuende beim
Top-Level-Import ein Zyklus (documents importiert page_render fuer den
Dispatch, page_render importiert documents fuer den Typ). Aufgeloest, indem
- ``documents.py`` ``PageImage`` von hier ganz normal auf Modulebene
  importiert (billig, dieses Modul importiert nichts Schweres auf
  Modulebene), und
- dieses Modul ``documents.iter_pdf_pages`` NICHT auf Modulebene importiert,
  sondern erst lokal innerhalb von ``load_pages()``, wenn tatsaechlich eine
  PDF-Quelle erkannt wurde.

Import-Vertrag: PIL/numpy/pypdfium2 werden ausschliesslich innerhalb von
Funktionen importiert, niemals auf Modulebene.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    import PIL.Image


# DIN-A4-Hoehe in Zoll -- Grundlage der (bewusst simplen) DPI-Schaetzung in
# estimate_dpi(): Sie geht von Hochformat aus und leitet die DPI allein aus
# der Pixelhoehe ab. Fuer querformatige oder nicht-A4-Vorlagen liefert das
# einen falschen Wert -- das ist als Einschraenkung akzeptiert, siehe
# estimate_dpi()-Docstring.
A4_HEIGHT_INCHES = 11.69


@dataclass(frozen=True)
class PageImage:
    """Eine einzelne gerenderte Seite. Die Aufruferin/der Aufrufer besitzt
    ``image`` (kein Cache, kein Wiederverwenden ueber mehrere PageImage-
    Instanzen hinweg) -- siehe iter_pdf_pages()-Docstring in documents.py."""

    index: int
    image: "PIL.Image.Image"
    dpi: int
    width: int
    height: int


def estimate_dpi(image: "PIL.Image.Image", *, assume_a4: bool = True) -> float | None:
    """Schaetzt die effektive Aufloesung aus der Pixelhoehe, unter der
    Annahme einer DIN-A4-Vorlage im Hochformat (11.69 Zoll hoch). Liefert
    ``None``, wenn ``assume_a4`` falsch ist -- ohne eine bekannte
    physische Seitengroesse laesst sich aus reinen Pixeln keine DPI ableiten.

    Bewusst simpel gehalten (keine Seitenverhaeltnis-Pruefung, kein
    Querformat-Fallback): fuer nicht-A4 oder querformatige Vorlagen ist der
    Rueckgabewert entsprechend ungenau -- die Aufruferin kennt in diesem Fall
    typischerweise ohnehin die echte DPI (z.B. aus target_dpi beim PDF-
    Rendering) und muss sich nicht auf diese Schaetzung verlassen."""
    if not assume_a4:
        return None
    _, height = image.size
    return height / A4_HEIGHT_INCHES


def load_pages(
    source: "Path | bytes",
    *,
    target_dpi: int = 350,
    max_pages: int = 40,
) -> Iterator[PageImage]:
    """Dispatcht anhand der Kopfbytes: ``%PDF`` -> ``documents.iter_pdf_pages``,
    sonst ein Einzelbild, mit PIL geoeffnet, EXIF-transponiert und nach RGB
    konvertiert.

    Muss ein Generator sein (siehe iter_pdf_pages()-Docstring in
    documents.py zur Speicher-Begruendung): Fuer PDF-Quellen wird das per
    ``yield from`` an den bereits generatorischen ``iter_pdf_pages``
    durchgereicht: PDF-Seiten werden also weiterhin einzeln beim Verbrauch
    gerendert, nicht vorab als Liste."""
    if isinstance(source, (bytes, bytearray)):
        header = bytes(source[:5])
        is_pdf = header.startswith(b"%PDF")
    else:
        source = Path(source)
        with open(source, "rb") as handle:
            header = handle.read(5)
        is_pdf = header.startswith(b"%PDF")

    if is_pdf:
        # Lokaler statt Modulebenen-Import -- siehe Modul-Docstring zur
        # Zyklus-Vermeidung.
        from ..documents import iter_pdf_pages

        yield from iter_pdf_pages(source, target_dpi=target_dpi, max_pages=max_pages)
        return

    import io

    from PIL import Image, ImageOps

    if isinstance(source, (bytes, bytearray)):
        image = Image.open(io.BytesIO(source))
    else:
        image = Image.open(source)
    image = ImageOps.exif_transpose(image) or image
    image = image.convert("RGB")
    width, height = image.size
    dpi = estimate_dpi(image, assume_a4=True)
    yield PageImage(
        index=0,
        image=image,
        dpi=int(dpi) if dpi else target_dpi,
        width=width,
        height=height,
    )
