"""Seitensegmentierung: eine Seite in einzelne Text-Regionen zerlegen (Stufe 3
des OCR-Refactors).

Primaeralgorithmus ist bewusst abhaengigkeitsarm: eine numpy-
Projektionsprofil-Analyse (kein Tesseract-Binary, kein OpenCV noetig). Der
optionale `word_boxes`-Parameter ist der spaeter vorgesehene Einstiegspunkt
fuer eine Tesseract-`image_to_data`-basierte Segmentierung -- dieses Modul
importiert das `engines`-Subpaket dabei bewusst NICHT (das gehoert gerade
einem anderen Agenten), sondern nimmt Wortboxen nur als bereits berechnete
Daten entgegen. So bleibt segment_page() ohne jedes Binary testbar.

TODO (spaetere Stufe, aussdruecklich nicht Teil dieser Stufe 3): eine
FORMULA/TABLE-Klassifikation. Aktuell wird jede gefundene Region entweder als
TEXT_LINE (eine einzelne Zeile) oder PARAGRAPH (mehrere zu nah beieinander
liegende Zeilen, siehe PARAGRAPH_MERGE_GAP_ROWS) eingestuft.

Import-Vertrag: PIL/numpy werden ausschliesslich innerhalb von Funktionen
importiert, niemals auf Modulebene.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence, TYPE_CHECKING

from .types import RegionType

if TYPE_CHECKING:
    import PIL.Image


# Eine Zeile besteht aus zusammenhaengenden Bildzeilen, in denen mindestens
# dieser Anteil der Breite "Tinte" (Pixel unter dem Schwellenwert) enthaelt --
# filtert einzelne verirrte Rauschpixel heraus, ohne echte duenne Textzeilen
# zu verpassen.
MIN_ROW_INK_FRACTION = 0.01
# Analog fuer die vertikale Projektion INNERHALB einer bereits gefundenen
# Zeilenbande, um deren linken/rechten Rand zu bestimmen.
MIN_COL_INK_FRACTION = 0.01
# Vertikaler Abstand (in Pixelzeilen) zwischen zwei Zeilenbanden, bis zu dem
# sie noch als Teil desselben Absatzes gelten (typischer Zeilenabstand
# innerhalb eines Absatzes) -- groessere Luecken trennen Regionen.
PARAGRAPH_MERGE_GAP_ROWS = 12
# Analoge Zusammenfuehrungsschwelle fuer den word_boxes-Pfad: zwei
# Wortboxen gelten als in derselben Zeile, wenn sich ihre vertikalen Spannen
# um mindestens diesen Anteil der kleineren Boxhoehe ueberlappen.
MIN_LINE_OVERLAP_FRACTION = 0.4


def _to_ink_mask(image: "PIL.Image.Image") -> "Any":
    """Binarisiert `image` (beliebiger Modus) zu einer bool-Maske: Pixel
    unter dem mittleren Grauwert gelten als "Tinte". Dieselbe simple
    Schwellenwahl wie in image_quality._estimate_skew_degrees -- fuer
    synthetische/gescannte Dokumente (dunkler Text auf hellem Grund)
    ausreichend, ohne ein echtes Otsu-Verfahren zu implementieren."""
    import numpy as np

    grey = image.convert("L")
    arr = np.asarray(grey, dtype=np.float64)
    return arr < arr.mean()


def _runs(mask: "Any") -> list[tuple[int, int]]:
    """Liefert die (start, end)-Bereiche (end exklusiv) zusammenhaengender
    True-Laeufe in einer 1D-bool-Sequenz."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(mask.tolist()):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def _line_bboxes_from_projection(ink: "Any") -> list[tuple[int, int, int, int]]:
    """Primaeralgorithmus: horizontale Projektion findet Zeilenbanden,
    vertikale Projektion INNERHALB jeder Bande trimmt deren linken/rechten
    Rand. Gibt (x0, y0, x1, y1)-Boxen zurueck, oben-nach-unten sortiert."""
    height, width = ink.shape
    row_counts = ink.sum(axis=1)
    row_has_text = row_counts >= max(1, int(width * MIN_ROW_INK_FRACTION))
    bands = _runs(row_has_text)

    line_bboxes: list[tuple[int, int, int, int]] = []
    for row_start, row_end in bands:
        band = ink[row_start:row_end, :]
        col_counts = band.sum(axis=0)
        col_has_text = col_counts >= max(1, int((row_end - row_start) * MIN_COL_INK_FRACTION))
        cols = col_has_text.nonzero()[0]
        if cols.size == 0:
            continue
        col_start, col_end = int(cols.min()), int(cols.max()) + 1
        line_bboxes.append((col_start, row_start, col_end, row_end))
    return line_bboxes


def _cluster_word_boxes_into_lines(
    boxes: Sequence[tuple[int, int, int, int]],
) -> list[tuple[int, int, int, int]]:
    """Alternativer Pfad fuer den `word_boxes`-Injection-Point: gruppiert
    einzelne Wortboxen (x0, y0, x1, y1) anhand vertikaler Ueberlappung zu
    Zeilenboxen. Wird nur verwendet, wenn eine `word_boxes`-Callable
    uebergeben wurde (z.B. spaeter aus Tesseracts `image_to_data`)."""
    if not boxes:
        return []

    ordered = sorted(boxes, key=lambda b: (b[1], b[0]))
    lines: list[list[tuple[int, int, int, int]]] = [[ordered[0]]]
    line_y0, line_y1 = ordered[0][1], ordered[0][3]

    for box in ordered[1:]:
        _, y0, _, y1 = box
        overlap = min(line_y1, y1) - max(line_y0, y0)
        min_height = min(line_y1 - line_y0, y1 - y0)
        if min_height > 0 and overlap >= MIN_LINE_OVERLAP_FRACTION * min_height:
            lines[-1].append(box)
            line_y0 = min(line_y0, y0)
            line_y1 = max(line_y1, y1)
        else:
            lines.append([box])
            line_y0, line_y1 = y0, y1

    line_bboxes = [
        (
            min(b[0] for b in line),
            min(b[1] for b in line),
            max(b[2] for b in line),
            max(b[3] for b in line),
        )
        for line in lines
    ]
    line_bboxes.sort(key=lambda b: b[1])
    return line_bboxes


def _merge_into_paragraphs(
    line_bboxes: Sequence[tuple[int, int, int, int]],
) -> list[tuple[tuple[int, int, int, int], int]]:
    """Fuehrt vertikal nah beieinander liegende Zeilenboxen (Abstand <=
    PARAGRAPH_MERGE_GAP_ROWS) zu Absatz-Boxen zusammen. Gibt pro Ergebnis-
    Region deren Bounding-Box UND die Anzahl urspruenglicher Zeilen zurueck
    (letzteres entscheidet TEXT_LINE vs. PARAGRAPH in segment_page)."""
    if not line_bboxes:
        return []

    groups: list[list[tuple[int, int, int, int]]] = [[line_bboxes[0]]]
    for bbox in line_bboxes[1:]:
        prev = groups[-1][-1]
        gap = bbox[1] - prev[3]
        if gap <= PARAGRAPH_MERGE_GAP_ROWS:
            groups[-1].append(bbox)
        else:
            groups.append([bbox])

    result: list[tuple[tuple[int, int, int, int], int]] = []
    for group in groups:
        x0 = min(b[0] for b in group)
        y0 = min(b[1] for b in group)
        x1 = max(b[2] for b in group)
        y1 = max(b[3] for b in group)
        result.append(((x0, y0, x1, y1), len(group)))
    return result


def segment_page(
    image: "PIL.Image.Image",
    *,
    page_index: int = 0,
    word_boxes: Callable[[Any], Sequence[tuple[int, int, int, int]]] | None = None,
) -> list[tuple[str, RegionType, tuple[int, int, int, int]]]:
    """Zerlegt `image` in Regionen und gibt sie als
    ``(region_id, region_type, bbox)``-Tripel zurueck, oben-nach-unten
    geordnet, mit IDs ``f"p{page_index}-r{n}"``.

    Standardpfad (``word_boxes=None``): numpy-Projektionsprofil (siehe
    `_line_bboxes_from_projection`). Wird eine `word_boxes`-Callable
    uebergeben, wird stattdessen deren Rueckgabe (Wort-Bounding-Boxen) zu
    Zeilen geclustert (siehe `_cluster_word_boxes_into_lines`) -- das ist der
    fuer eine spaetere Tesseract-`image_to_data`-Anbindung vorgesehene
    Einstiegspunkt.

    Anschliessend werden vertikal nahe Zeilen zu Absaetzen zusammengefuehrt
    (`_merge_into_paragraphs`): eine resultierende Region mit genau einer
    urspruenglichen Zeile wird als TEXT_LINE eingestuft, mit mehreren als
    PARAGRAPH. FORMULA/TABLE-Klassifikation ist nicht Teil dieser Stufe
    (siehe Modul-TODO)."""
    if word_boxes is not None:
        line_bboxes = _cluster_word_boxes_into_lines(word_boxes(image))
    else:
        ink = _to_ink_mask(image)
        line_bboxes = _line_bboxes_from_projection(ink)

    grouped = _merge_into_paragraphs(line_bboxes)

    regions: list[tuple[str, RegionType, tuple[int, int, int, int]]] = []
    for n, (bbox, line_count) in enumerate(grouped):
        region_type = RegionType.TEXT_LINE if line_count <= 1 else RegionType.PARAGRAPH
        regions.append((f"p{page_index}-r{n}", region_type, bbox))
    return regions
