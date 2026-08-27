"""Konservative Bildvorverarbeitung vor der OCR (Stufe 3 des OCR-Refactors).

Alle Funktionen hier sind bewusst zurueckhaltend: EXIF-Transponierung,
Graustufen-Konvertierung, optionales Geraderichten um den gemessenen Winkel
(image_quality.assess()), Hochskalieren kleiner Zeilen-Crops. KEINE
destruktive Binarisierung (Schwarz-Weiss-Threshold) -- ein VLM/HTR-Engine
liest Graustufen-Text erfahrungsgemaess besser als 1-Bit-Bilder, und eine
zu frueh binarisierte Zeile ist fuer keine der nachgelagerten Engines mehr
rueckgaengig zu machen.

Stufe-A-Regel dieses Repos gilt auch hier: das ORIGINAL wird nie
ueberschrieben. Jede Funktion in diesem Modul gibt ein NEUES Bild zurueck
und laesst das uebergebene Eingabebild unveraendert -- das gilt auch fuer
`prepare()`, das intern nur mit Kopien arbeitet.

Import-Vertrag: PIL wird ausschliesslich innerhalb von Funktionen
importiert, niemals auf Modulebene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import RegionType

if TYPE_CHECKING:
    import PIL.Image


# Tesseract liest Zeilen-Crops zuverlaessig erst ab einer x-Hoehe von rund
# 30-40 Pixeln (siehe Auftrag). Als Ziel-Minimalhoehe fuer eine ganze
# Zeilen-Bounding-Box (nicht nur die x-Hoehe der Buchstaben) wird hier
# grosszuegiger aufgerundet, weil eine Zeilenbox neben der reinen x-Hoehe
# auch Ober-/Unterlaengen enthaelt.
MIN_LINE_HEIGHT_PX = 60


def to_grayscale(image: "PIL.Image.Image") -> "PIL.Image.Image":
    """Gibt eine NEUE Graustufen-Kopie von `image` zurueck (Modus "L").
    `image` selbst bleibt unveraendert -- `Image.convert()` liefert bereits
    von sich aus immer ein neues Objekt, nie das Original."""
    return image.convert("L")


def deskew(image: "PIL.Image.Image", angle_degrees: float) -> "PIL.Image.Image":
    """Rotiert `image` um `angle_degrees` und gibt eine NEUE Bildinstanz
    zurueck. `image` bleibt unveraendert.

    VERTRAG (Vorzeichenkonvention, identisch zu image_quality.assess() /
    image_quality._estimate_skew_degrees -- siehe dortige Docstrings fuer die
    Gegenseite dieses Vertrags): `angle_degrees` ist bereits der fertige
    KORREKTURwinkel, so wie ihn `PIL.Image.rotate()` erwartet. Diese Funktion
    negiert ihn NICHT und interpretiert ihn nicht um -- sie reicht ihn
    unveraendert an `Image.rotate()` durch. Der von `image_quality.assess()`
    gelieferte `ImageQuality.skew_degrees`-Wert kann also direkt hier
    eingesetzt werden, um die gemessene Schiefe geradezuziehen:
    ``deskew(image, quality.skew_degrees)``. WICHTIG fuer Aufrufer: wer
    diesen Wert vor dem Aufruf selbst negiert ("um die Schiefe
    auszugleichen"), VERDOPPELT die Schiefe, statt sie zu entfernen -- und
    dieser Fehler sieht wie "das Deskewing funktioniert schlecht" aus, nicht
    wie ein offensichtlicher Bug. Also: nicht negieren, einfach durchreichen.

    `expand=True`, damit beim Rotieren keine Bildecken abgeschnitten werden;
    der dabei neu entstehende Rand wird mit Weiss (bzw. dem hellsten Wert des
    jeweiligen Modus) aufgefuellt, nicht mit Schwarz -- ein schwarzer Rand
    wuerde bei nachgelagerter Segmentierung/OCR leicht als Bildinhalt
    fehlinterpretiert."""
    from PIL import Image

    if angle_degrees == 0:
        return image.copy()

    if image.mode == "L":
        fill = 255
    elif image.mode == "RGB":
        fill = (255, 255, 255)
    elif image.mode == "RGBA":
        fill = (255, 255, 255, 255)
    else:
        # Unbekannter/exotischer Modus: ueber RGB rotieren und zurueck
        # konvertieren, damit fillcolor garantiert gueltig ist.
        rotated = image.convert("RGB").rotate(
            angle_degrees, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(255, 255, 255)
        )
        return rotated.convert(image.mode)

    return image.rotate(angle_degrees, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=fill)


# Alias, auf Modulebene zur Definitionszeit gebunden: prepare()'s eigener
# `deskew`-Parameter (bool) verdeckt sonst innerhalb dieser Funktion jeden
# Zugriff auf die gleichnamige Modulfunktion oben -- in Python schattet ein
# Parametername die GESAMTE Funktion, nicht nur ab seiner Zuweisung. Dieser
# Alias wird beim Modul-Import einmal gebunden (kein Import zur Laufzeit,
# keine Annahme ueber den Ladezustand des Moduls beim Aufruf) und macht die
# Namensschattierung an der einzigen Stelle sichtbar, an der ein:e Leser:in
# danach sucht.
_deskew_image = deskew


def upscale_to_min_height(image: "PIL.Image.Image", min_height: int) -> "PIL.Image.Image":
    """Skaliert `image` proportional hoch, falls seine Hoehe unter
    `min_height` liegt (typischerweise ein Tesseract-Zeilen-Crop unter
    MIN_LINE_HEIGHT_PX). Ist das Bild bereits hoch genug, wird eine
    unveraenderte KOPIE zurueckgegeben -- nie das Originalobjekt selbst, und
    es wird nie verkleinert (nur hoch-, nie runterskaliert)."""
    width, height = image.size
    if height >= min_height or height <= 0:
        return image.copy()

    factor = min_height / height
    new_size = (max(1, round(width * factor)), max(1, round(height * factor)))
    return image.resize(new_size, resample=_bicubic())


def _bicubic():
    from PIL import Image

    return Image.Resampling.BICUBIC


def prepare(
    image: "PIL.Image.Image",
    *,
    region_type: RegionType = RegionType.TEXT_LINE,
    deskew: bool = True,
    target_dpi: int = 350,
) -> "PIL.Image.Image":
    """Bereitet `image` fuer die OCR vor: EXIF-Transponierung, Graustufen,
    optionales Geraderichten, Hochskalieren zu kleiner Zeilen-Crops.

    Gibt IMMER ein neues Bildobjekt zurueck; `image` bleibt unveraendert
    (Stufe-A-Regel, siehe Modul-Docstring). `target_dpi` fliesst aktuell
    nicht in eine Skalierungsentscheidung ein (die einzige Skalierung hier
    ist das Hochskalieren zu kleiner Zeilen-Crops auf MIN_LINE_HEIGHT_PX,
    unabhaengig von der Ziel-DPI) -- der Parameter ist Teil der Signatur,
    damit spaetere DPI-bewusste Verfeinerungen ihn nutzen koennen, ohne
    Aufrufer anzupassen.

    `deskew` (der Parameter) und die Modulfunktion `deskew()` heissen
    bewusst gleich (wie im Auftrag spezifiziert). Der Parametername schattet
    innerhalb dieser Funktion die Modulfunktion vollstaendig -- aufgeloest
    ueber den Modulebenen-Alias `_deskew_image` (siehe dort), der beim Import
    des Moduls einmalig gebunden wird, nicht erst beim Aufruf von prepare().
    """
    from PIL import ImageOps

    prepared = ImageOps.exif_transpose(image) or image.copy()
    if prepared is image:
        prepared = prepared.copy()

    prepared = to_grayscale(prepared)

    if deskew:
        from .image_quality import assess as _assess_quality

        # Nutzt bewusst die oeffentliche assess()-Funktion (statt einer
        # privaten Helper-Funktion aus image_quality) fuer den gemessenen
        # Winkel -- das ist etwas mehr Arbeit (misst nebenbei auch Schaerfe,
        # Kontrast etc.), haelt preprocess.py aber unabhaengig von internen
        # Implementierungsdetails von image_quality. Der Winkel wird
        # UNVERAENDERT (nicht negiert) durchgereicht -- siehe Vorzeichen-
        # Vertrag im deskew()-Docstring oben.
        angle = _assess_quality(prepared).skew_degrees
        prepared = _deskew_image(prepared, angle)

    if region_type in (RegionType.TEXT_LINE, RegionType.PARAGRAPH):
        prepared = upscale_to_min_height(prepared, MIN_LINE_HEIGHT_PX)

    return prepared
