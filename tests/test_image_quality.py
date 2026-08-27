"""Testet Bildqualitaetsmessung, Vorverarbeitung, Seitenrendering und
Segmentierung (Stufe 3 des OCR-Refactors: Bildhandhabung).

Deckt teacherassist_core/ocr/image_quality.py ab: assess (Zeile 266),
QualityThresholds (Zeile 44), _laplacian_variance (Zeile 110),
_estimate_skew_degrees (Zeile 157); teacherassist_core/ocr/preprocess.py:
prepare (Zeile 103), deskew (Zeile 45), upscale_to_min_height (Zeile 82);
teacherassist_core/ocr/page_render.py: PageImage (Zeile 41), estimate_dpi
(Zeile 53), load_pages (Zeile 70); teacherassist_core/ocr/segmentation.py:
segment_page (Zeile 168); sowie teacherassist_core/documents.py:
iter_pdf_pages (Zeile 52).

Alle Testbilder sind synthetisch (PIL.Image + ImageDraw, nur Rechtecke --
keine Schriftart-Abhaengigkeit) oder ein per reportlab erzeugtes Mini-PDF.
Kein Netzwerk, keine Fixture-Bilddateien, kein Tesseract-Binary.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

BLOCKED_ROOTS = frozenset({"PIL", "numpy", "pypdfium2"})


class _BlockingFinder:
    """sys.meta_path-Finder, der BLOCKED_ROOTS unauffindbar macht (siehe
    tests/test_ocr_engines.py::_BlockingFinder fuer denselben Kniff auf den
    Engine-Modulen). find_spec() muss den Import ablehnen, BEVOR der
    reguläre PathFinder die tatsaechlich installierten Pakete faende --
    daher ein Raise statt eines durchreichenden None."""

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".", 1)[0]
        if root in BLOCKED_ROOTS:
            raise ModuleNotFoundError(f"blocked for test: {fullname}")
        return None


def _purge_ocr_modules() -> dict:
    removed = {}
    for name in list(sys.modules):
        if name.startswith("teacherassist_core.ocr.image_quality") or name.startswith(
            "teacherassist_core.ocr.preprocess"
        ) or name.startswith("teacherassist_core.ocr.page_render") or name.startswith(
            "teacherassist_core.ocr.segmentation"
        ):
            removed[name] = sys.modules.pop(name)
    return removed


def test_stufe3_modules_import_without_heavy_deps():
    """Alle vier neuen Stufe-3-Module muessen importierbar bleiben, auch
    wenn PIL, numpy und pypdfium2 (per sys.meta_path) unauffindbar sind --
    der im Auftrag geforderte Lazy-Import-Vertrag: die schweren
    Abhaengigkeiten duerfen nur INNERHALB von Funktionen importiert werden,
    nie auf Modulebene."""
    import importlib

    finder = _BlockingFinder()
    sys.meta_path.insert(0, finder)
    saved = _purge_ocr_modules()
    try:
        importlib.import_module("teacherassist_core.ocr.image_quality")
        importlib.import_module("teacherassist_core.ocr.preprocess")
        importlib.import_module("teacherassist_core.ocr.page_render")
        importlib.import_module("teacherassist_core.ocr.segmentation")
    finally:
        sys.meta_path.remove(finder)
        _purge_ocr_modules()
        sys.modules.update(saved)


# ---------------------------------------------------------------------------
# image_quality.assess (Zeile 266)
# ---------------------------------------------------------------------------


def _striped_image(width: int = 800, height: int = 600, *, mode: str = "RGB"):
    """Baut ein synthetisches 'Textzeilen'-Bild: dunkle horizontale Balken
    auf hellem Grund, ohne jede Schriftart-Abhaengigkeit (nur
    ImageDraw.rectangle). Steht fuer scharfe, kontrastreiche Vorlagen."""
    from PIL import Image, ImageDraw

    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)
    for y in range(40, height - 40, 40):
        draw.rectangle([50, y, width - 50, y + 20], fill=0)
    return img.convert(mode)


def test_sharp_high_contrast_image_has_no_blur_issue_and_high_score():
    """assess() (image_quality.py:266) auf einem scharfen, kontrastreichen
    Bild: kein 'too_blurry', blocking ist False, und der Gesamtscore ist
    deutlich ueber der Mitte (siehe _score, image_quality.py:224)."""
    from teacherassist_core.ocr.image_quality import assess

    quality = assess(_striped_image())
    assert "too_blurry" not in quality.issues
    assert quality.blocking is False
    assert quality.score > 0.6


def test_blurred_image_flagged_too_blurry_and_blocking_with_lower_score():
    """Dasselbe Bild durch ImageFilter.GaussianBlur(radius=6): 'too_blurry'
    erscheint in issues, blocking wird True (image_quality.py:_estimate ->
    assess()'s blocking-Policy: NUR too_blurry/too_small blockieren, siehe
    Modul-Docstring), und blur_score ist STRIKT niedriger als im scharfen
    Original -- das ist die robuste, relative Assertion, keine absolute
    Magic Number (siehe Auftrag)."""
    from PIL import ImageFilter

    from teacherassist_core.ocr.image_quality import assess

    sharp = _striped_image()
    blurred = sharp.filter(ImageFilter.GaussianBlur(radius=6))

    sharp_quality = assess(sharp)
    blurred_quality = assess(blurred)

    assert "too_blurry" in blurred_quality.issues
    assert blurred_quality.blocking is True
    assert blurred_quality.blur_score < sharp_quality.blur_score


def test_dark_image_flagged_too_dark():
    """Pixelwerte mit Faktor 0.15 abgedunkelt -> 'too_dark' in issues
    (brightness_dark_max-Schwelle, image_quality.py:QualityThresholds)."""
    from PIL import Image

    from teacherassist_core.ocr.image_quality import assess

    base = _striped_image()
    dark = Image.eval(base, lambda p: int(p * 0.15))

    quality = assess(dark)
    assert "too_dark" in quality.issues


def test_washed_out_image_flagged_too_bright_or_low_contrast():
    """Ein Bild, dessen Werte stark Richtung Weiss gestaucht wurden
    (typisch fuer ueberbelichtete/washed-out Aufnahmen), loest 'too_bright'
    und/oder 'low_contrast' aus (beide Schwellen in QualityThresholds,
    image_quality.py:44)."""
    from PIL import Image

    from teacherassist_core.ocr.image_quality import assess

    base = _striped_image()
    washed_out = Image.eval(base, lambda p: min(255, int(p * 0.15 + 200)))

    quality = assess(washed_out)
    assert "too_bright" in quality.issues or "low_contrast" in quality.issues


def test_too_small_image_is_blocking():
    """Ein 200x150-Bild unterschreitet min_width/min_height
    (QualityThresholds, image_quality.py:44) -> 'too_small' und blocking
    True."""
    from teacherassist_core.ocr.image_quality import assess

    tiny = _striped_image(200, 150)

    quality = assess(tiny)
    assert "too_small" in quality.issues
    assert quality.blocking is True


def _text_line_image(width: int = 900, height: int = 700):
    """Mehrere duenne horizontale Balken (simulierte Textzeilen) fuer die
    Skew-Schaetzung -- braucht ausreichend viele Zeilen, damit das
    Projektionsprofil bei der richtigen Rotation deutlich peakiger wird als
    bei falschen Kandidatenwinkeln."""
    from PIL import Image, ImageDraw

    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)
    for y in range(40, height - 40, 30):
        draw.rectangle([40, y, width - 40, y + 12], fill=0)
    return img.convert("RGB")


@pytest.mark.parametrize("applied_angle", [7.0, -5.0])
def test_skew_degrees_recovers_known_rotation_within_tolerance(applied_angle):
    """_estimate_skew_degrees (image_quality.py:157), aufgerufen ueber
    assess(): ein per PIL.Image.rotate(applied_angle, expand=True) gedrehtes
    Textzeilenbild soll den KORREKTURwinkel -applied_angle zurueckliefern
    (Vorzeichenkonvention: assess()/deskew() teilen sich die Konvention,
    dass der von assess() gelieferte Winkel direkt an
    PIL.Image.rotate() durchgereicht werden kann, um wieder geradezuziehen
    -- siehe preprocess.py:45 deskew()-Docstring), mit einer Toleranz von
    +/-2 Grad. Oberhalb der 2-Grad-Schwelle erscheint zudem 'skewed' in
    issues (QualityThresholds.skew_warn_degrees)."""
    from teacherassist_core.ocr.image_quality import assess

    base = _text_line_image()
    rotated = base.rotate(applied_angle, expand=True, fillcolor=(255, 255, 255))

    quality = assess(rotated)
    expected_correction = -applied_angle
    assert abs(quality.skew_degrees - expected_correction) <= 2.0
    assert "skewed" in quality.issues


# ---------------------------------------------------------------------------
# page_render.estimate_dpi (Zeile 53)
# ---------------------------------------------------------------------------


def test_estimate_dpi_on_a4_proportioned_image():
    """estimate_dpi() (page_render.py:53) auf einem Bild mit exakten
    350-dpi-A4-Pixelmassen (2894x4093, siehe documents.py-Kalibrierung des
    pypdfium2-Skalierungsfaktors) liefert ungefaehr 350."""
    from PIL import Image

    from teacherassist_core.ocr.page_render import estimate_dpi

    a4_image = Image.new("RGB", (2894, 4093), (255, 255, 255))
    dpi = estimate_dpi(a4_image)
    assert dpi is not None
    assert abs(dpi - 350) < 5

    assert estimate_dpi(a4_image, assume_a4=False) is None


# ---------------------------------------------------------------------------
# preprocess.prepare (Zeile 103)
# ---------------------------------------------------------------------------


def test_prepare_returns_new_object_and_leaves_input_unmodified():
    """prepare() (preprocess.py:103) gibt IMMER ein NEUES Bildobjekt zurueck
    und laesst das Eingabebild unveraendert -- Stufe-A-Regel des Repos
    (siehe preprocess.py-Modul-Docstring). Geprueft ueber id() (kein
    dasselbe Objekt) UND Pixeldaten (tobytes() des Originals unveraendert)."""
    from teacherassist_core.ocr import preprocess
    from teacherassist_core.ocr.types import RegionType

    original = _text_line_image()
    original_bytes_before = original.tobytes()
    original_id = id(original)

    prepared = preprocess.prepare(original, region_type=RegionType.TEXT_LINE, deskew=True)

    assert id(prepared) != original_id
    assert prepared is not original
    assert original.tobytes() == original_bytes_before


def test_prepare_upscales_small_line_crop():
    """prepare() mit region_type=TEXT_LINE auf einem sehr niedrigen
    Zeilen-Crop (Hoehe 20px) skaliert per upscale_to_min_height()
    (preprocess.py:82) auf MIN_LINE_HEIGHT_PX hoch, damit Tesseract genug
    x-Hoehe zum Lesen hat."""
    from PIL import Image

    from teacherassist_core.ocr import preprocess
    from teacherassist_core.ocr.types import RegionType

    small_crop = Image.new("RGB", (400, 20), (255, 255, 255))
    prepared = preprocess.prepare(small_crop, region_type=RegionType.TEXT_LINE, deskew=False)
    assert prepared.height >= preprocess.MIN_LINE_HEIGHT_PX


# ---------------------------------------------------------------------------
# segmentation.segment_page (Zeile 168)
# ---------------------------------------------------------------------------


def test_segment_page_finds_three_separated_bars_in_order():
    """segment_page() (segmentation.py:168) auf einem synthetischen Bild mit
    drei klar getrennten horizontalen Balken (grosser Abstand > die
    PARAGRAPH_MERGE_GAP_ROWS-Zusammenfuehrungsschwelle) liefert drei
    Regionen mit sinnvollen, nicht ueberlappenden, korrekt (oben nach unten)
    geordneten Bounding-Boxen und IDs p0-r0, p0-r1, p0-r2."""
    from PIL import Image, ImageDraw

    from teacherassist_core.ocr.segmentation import segment_page

    img = Image.new("L", (400, 300), 255)
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 380, 60], fill=0)
    draw.rectangle([20, 130, 380, 170], fill=0)
    draw.rectangle([20, 240, 380, 280], fill=0)

    regions = segment_page(img, page_index=0)

    assert [r[0] for r in regions] == ["p0-r0", "p0-r1", "p0-r2"]
    ys = [bbox[1] for _id, _type, bbox in regions]
    assert ys == sorted(ys)
    for i in range(len(regions) - 1):
        _, _, bbox_a = regions[i]
        _, _, bbox_b = regions[i + 1]
        assert bbox_a[3] <= bbox_b[1]  # y1 der oberen Box <= y0 der unteren


# ---------------------------------------------------------------------------
# documents.iter_pdf_pages (Zeile 52)
# ---------------------------------------------------------------------------


def _build_pdf(path: Path, page_count: int) -> None:
    """Baut ein Mini-PDF mit `page_count` Seiten via reportlab (bereits im
    Projekt installiert, keine neue Abhaengigkeit)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(page_count):
        c.drawString(100, 700, f"Seite {i}")
        c.showPage()
    c.save()


def test_iter_pdf_pages_is_a_generator(tmp_path):
    """iter_pdf_pages() (documents.py:52) ist ein Generator, kein
    Listen-Aufbau (siehe Docstring dort zur Speicherbegruendung: 40 eager
    gerenderte 350-dpi-A4-Seiten waeren ~1.4 GB)."""
    from teacherassist_core.documents import iter_pdf_pages

    pdf_path = tmp_path / "mini.pdf"
    _build_pdf(pdf_path, 3)

    result = iter_pdf_pages(pdf_path, target_dpi=100)
    assert inspect.isgenerator(result)
    result.close()


def test_iter_pdf_pages_renders_lazily(tmp_path):
    """Nur die erste Seite konsumieren darf nicht dazu fuehren, dass alle
    Seiten gerendert werden: pypdfium2.PdfPage.render wird fuer die Dauer des
    Tests instrumentiert und die Anzahl der Aufrufe nach dem ersten next()
    geprueft (muss genau 1 sein, nicht page_count)."""
    import pypdfium2 as pdfium

    from teacherassist_core.documents import iter_pdf_pages

    pdf_path = tmp_path / "mini.pdf"
    _build_pdf(pdf_path, 5)

    render_calls = []
    original_render = pdfium.PdfPage.render

    def counting_render(self, *args, **kwargs):
        render_calls.append(1)
        return original_render(self, *args, **kwargs)

    pdfium.PdfPage.render = counting_render
    try:
        generator = iter_pdf_pages(pdf_path, target_dpi=100, max_pages=40)
        first_page = next(generator)
        assert len(render_calls) == 1
        assert first_page.index == 0
        generator.close()
    finally:
        pdfium.PdfPage.render = original_render


def test_iter_pdf_pages_honours_max_pages(tmp_path):
    """max_pages begrenzt die Anzahl gelieferter Seiten, auch wenn das PDF
    mehr Seiten enthaelt (documents.py:52)."""
    from teacherassist_core.documents import iter_pdf_pages

    pdf_path = tmp_path / "mini.pdf"
    _build_pdf(pdf_path, 5)

    pages = list(iter_pdf_pages(pdf_path, target_dpi=100, max_pages=2))
    assert len(pages) == 2
    assert [p.index for p in pages] == [0, 1]
