"""Bildqualitaetsmessung fuer die OCR-Pipeline (Stufe 3 des grossen OCR-Refactors).

``assess()`` fuellt das bisher nur als Platzhalter existierende
``types.ImageQuality`` (siehe ``ImageQuality.unknown()``) mit tatsaechlich
gemessenen Werten, damit ``consensus.decide_status()`` (das bereits gegen
``quality.blocking`` entscheidet) echte Signale statt eines neutralen
Platzhalters bekommt.

Alle Berechnungen laufen auf numpy-Arrays; es wird bewusst KEIN scipy und
KEIN OpenCV verwendet (siehe Modul-Docstring-Vorgabe des Refactors) -- die
Laplace-Faltung fuer die Schaerfe-Metrik wird per verschobener numpy-Slices
von Hand berechnet, die Skew-Schaetzung per PIL-Rotation + Projektionsprofil.

WICHTIG -- unvalidierte Schwellenwerte: Alle Zahlen in
``QualityThresholds`` sind aktuell Schaetzwerte aus Plausibilitaetsueberlegung,
NICHT aus einem gemessenen Benchmark. Es gibt noch kein privates
OCR-Benchmark-Set, gegen das diese Werte kalibriert wurden. Sie sind bewusst
an einer einzigen Stelle gesammelt (dieses Dataclass), damit sie spaeter --
sobald ein solches Benchmark existiert -- ohne Aenderung der Messlogik
nachjustiert werden koennen. Bis dahin gilt: konservativ genug, um in
Reviews nicht staendig falsch-blockierende Verdikte zu produzieren (siehe
``blocking``-Policy unten), aber nicht validiert.

Import-Vertrag (siehe Repo-weite Vorgabe): dieses Modul importiert PIL und
numpy NUR innerhalb von Funktionen, niemals auf Modulebene, damit
``import teacherassist_core.ocr.image_quality`` auch dann funktioniert, wenn
diese Pakete (testweise) blockiert sind.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .page_render import estimate_dpi
from .types import ImageQuality

if TYPE_CHECKING:
    import numpy as np
    import PIL.Image


@dataclass(frozen=True)
class QualityThresholds:
    """Alle Stellschrauben der Bildqualitaetsmessung an einem Ort, damit sie
    spaeter -- ohne die Messlogik anzufassen -- gegen ein echtes Benchmark
    nachjustiert werden koennen. Siehe Modul-Docstring: aktuell UNVALIDIERTE
    Schaetzwerte, keine gemessenen Zahlen.
    """

    # -- Groesse --
    # Unterhalb dieser Pixelmasse gilt ein Bild als zu klein, um brauchbaren
    # Text zu enthalten -- typischerweise ein winziger Crop oder eine stark
    # verkleinerte Vorschau statt eines echten Fotos/Scans.
    min_width: int = 300
    min_height: int = 300

    # -- Schaerfe (Laplace-Varianz) --
    # Grober Richtwert: scharfe, texthaltige Fotos liegen typischerweise
    # deutlich ueber diesem Wert, stark weichgezeichnete (GaussianBlur-artige)
    # Aufnahmen deutlich darunter. Die Tests pruefen bewusst nur die relative
    # Reihenfolge (scharf > verwischt), nicht diese absolute Zahl.
    blur_variance_min: float = 80.0

    # -- Kontrast --
    # Normalisierte 5.-95.-Perzentil-Spannweite ueber 255. Gewaehlt statt
    # normalisierter Standardabweichung, weil Perzentile robuster gegen
    # einzelne sehr helle/dunkle Ausreisser (Glare, Schatten am Rand) sind.
    contrast_min: float = 0.20

    # -- Helligkeit (Mittelwert / 255) --
    brightness_dark_max: float = 0.25
    brightness_bright_min: float = 0.85

    # -- Schiefe (Skew) --
    # Suchbereich und Aufloesung der Winkelsuche (siehe _estimate_skew_degrees).
    skew_search_degrees: float = 8.0
    skew_search_step: float = 0.5
    skew_warn_degrees: float = 2.0

    # -- Glare (Blendlicht/Reflexion) --
    # Pixelwert, ab dem ein Pixel als (moeglicherweise) gesaettigt gilt.
    glare_pixel_threshold: int = 250
    # Anteil gesaettigter Nachbarn (inkl. sich selbst) in einer 3x3-Nachbar-
    # schaft, ab dem ein gesaettigtes Pixel als Teil einer zusammenhaengenden
    # Blendlicht-Flaeche zaehlt statt als isoliertes helles Pixel (z.B. ein
    # einzelnes ueberbelichtetes Pixel auf sonst legitim weissem Papier).
    # Das ist die im Auftrag geforderte Mindestflaechen-Gate: reines
    # "Anteil na-gesaettigter Pixel" wuerde weisses Papier systematisch
    # ueberzaehlen.
    glare_neighbor_fraction: float = 0.6
    # Anteil der Flaeche, der als zusammenhaengendes Glare gelten muss, damit
    # das issue "glare" gesetzt wird.
    glare_ratio_warn: float = 0.02
    # Obergrenze: liegt der zusammenhaengende gesaettigte Flaechenanteil
    # DARUEBER, wird er als normaler weisser Papierhintergrund gewertet,
    # nicht als Glare. Genau das ist die im Auftrag beschriebene Ueberzaehl-
    # Falle: ein legitim weisses Blatt Papier ist typischerweise die
    # DOMINANTE (zusammenhaengende) helle Flaeche im Bild, waehrend echtes
    # Blendlicht/Reflexion normalerweise nur einen begrenzten Hotspot bildet.
    # Ohne diese Obergrenze wuerde jedes Dokument mit grosszuegigem weissem
    # Rand faelschlich als "glare" markiert (siehe Kalibrierungs-Notizen im
    # Testmodul).
    glare_ratio_max: float = 0.45


DEFAULT_THRESHOLDS = QualityThresholds()


def _laplacian_variance(arr: "np.ndarray") -> float:
    """Varianz der Laplace-Faltung mit dem 3x3-Kernel
    ``[[0,1,0],[1,-4,1],[0,1,0]]``, per verschobener numpy-Slices berechnet
    (aequivalent zu einer 'valid'-Faltung, ohne scipy.signal). Hoehere Werte
    bedeuten mehr hochfrequente Kantenenergie, also ein schaerferes Bild."""
    if arr.shape[0] < 3 or arr.shape[1] < 3:
        return 0.0
    center = arr[1:-1, 1:-1]
    up = arr[:-2, 1:-1]
    down = arr[2:, 1:-1]
    left = arr[1:-1, :-2]
    right = arr[1:-1, 2:]
    laplacian = up + down + left + right - 4.0 * center
    return float(laplacian.var())


def _percentile_contrast(arr: "np.ndarray") -> float:
    """Normalisierte 5.-95.-Perzentil-Spannweite ueber 255 (siehe
    QualityThresholds.contrast_min-Kommentar zur Wahl gegenueber std-dev)."""
    import numpy as np

    p5, p95 = np.percentile(arr, [5, 95])
    return float((p95 - p5) / 255.0)


def _glare_ratio(arr: "np.ndarray", thresholds: QualityThresholds) -> float:
    """Anteil der Pixel, die (a) nahezu gesaettigt sind UND (b) von
    ueberwiegend ebenfalls gesaettigten Nachbarn umgeben sind -- also Teil
    einer zusammenhaengenden hellen Flaeche (Reflexion/Blendlicht) statt
    eines einzelnen isolierten weissen Pixels auf legitim weissem Papier."""
    import numpy as np

    saturated = arr >= thresholds.glare_pixel_threshold
    if not bool(saturated.any()):
        return 0.0

    padded = np.pad(saturated.astype(np.int32), 1)
    counts = np.zeros(arr.shape, dtype=np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            counts += padded[1 + dy : 1 + dy + arr.shape[0], 1 + dx : 1 + dx + arr.shape[1]]

    required = thresholds.glare_neighbor_fraction * 9
    glare_pixels = saturated & (counts >= required)
    return float(glare_pixels.sum() / saturated.size)


def _estimate_skew_degrees(grey: "PIL.Image.Image", thresholds: QualityThresholds) -> float:
    """Schaetzt den Korrekturwinkel per Projektionsprofil-Suche.

    Ablauf: Bild binarisieren (Pixel unterhalb des Mittelwerts = "Tinte"),
    dann fuer jeden Kandidatenwinkel im Bereich
    ``+/- thresholds.skew_search_degrees`` (Schrittweite
    ``thresholds.skew_search_step`` Grad, per Default also 33 Kandidaten
    zwischen -8 und +8 Grad) das binarisierte Bild um diesen Winkel rotieren
    und die Varianz des horizontalen Projektionsprofils (Zeilensummen)
    messen. Bei sauber ausgerichteten Textzeilen ist dieses Profil "peakig"
    (abwechselnd textreiche/-arme Zeilen), bei Schiefstellung dagegen flach.
    Der Winkel mit maximaler Varianz wird zurueckgegeben.

    Vorzeichenkonvention (wichtig fuer preprocess.deskew): Der zurueckgegebene
    Winkel ist direkt der Korrekturwinkel im Sinne von
    ``PIL.Image.rotate(angle, expand=True)`` -- ihn auf das Originalbild
    anzuwenden soll die Schiefe geradeziehen. ``assess()`` und
    ``preprocess.deskew()`` teilen sich diese Konvention bewusst, damit der
    von ``assess()`` gelieferte Wert ohne weitere Vorzeichen-Klimmzuege an
    ``deskew()`` durchgereicht werden kann.
    """
    import numpy as np
    from PIL import Image as PILImage

    # Auf eine handhabbare Groesse herunterskalieren -- die Winkelsuche
    # rotiert das Bild bis zu 33 Mal, das soll auch bei grossen Fotos schnell
    # bleiben. Die Genauigkeit der Skew-Schaetzung haengt nicht von der vollen
    # Aufloesung ab.
    max_dim = 500
    width, height = grey.size
    if max(width, height) > max_dim:
        scale = max_dim / max(width, height)
        grey = grey.resize((max(1, int(width * scale)), max(1, int(height * scale))))

    arr = np.asarray(grey, dtype=np.float64)
    if arr.size == 0 or float(arr.std()) < 1e-6:
        return 0.0

    ink = (arr < arr.mean()).astype("uint8") * 255
    if not bool(ink.any()):
        return 0.0
    ink_image = PILImage.fromarray(ink)

    angles = []
    angle = -thresholds.skew_search_degrees
    while angle <= thresholds.skew_search_degrees + 1e-9:
        angles.append(round(angle, 6))
        angle += thresholds.skew_search_step

    best_angle = 0.0
    best_variance = -1.0
    for candidate in angles:
        rotated = ink_image.rotate(
            candidate,
            expand=True,
            fillcolor=0,
            resample=PILImage.Resampling.NEAREST,
        )
        profile = np.asarray(rotated, dtype=np.float64).sum(axis=1)
        variance = float(profile.var())
        if variance > best_variance:
            best_variance = variance
            best_angle = float(candidate)

    return best_angle


def _score(
    *,
    blur_score: float,
    contrast: float,
    brightness: float,
    skew_degrees: float,
    glare_ratio: float,
    blocking: bool,
    thresholds: QualityThresholds,
) -> float:
    """Kombiniert die Einzelmetriken zu einem 0..1-Gesamtscore.

    Bewusst simple, dokumentierte Heuristik statt eines gelernten Modells:
    jede Metrik wird auf 0..1 normalisiert (1.0 = unauffaellig) und das
    arithmetische Mittel gebildet. Ein ``blocking``-Verdikt deckelt den Score
    zusaetzlich auf maximal 0.2, damit "blockiert, aber Score 0.9" nicht
    widerspruechlich wirkt."""
    blur_component = max(0.0, min(1.0, blur_score / (thresholds.blur_variance_min * 3.0)))
    contrast_component = max(
        0.0, min(1.0, contrast / max(thresholds.contrast_min * 2.0, 1e-6))
    )
    brightness_component = max(0.0, min(1.0, 1.0 - abs(brightness - 0.5) * 2.0))
    skew_component = max(
        0.0, min(1.0, 1.0 - abs(skew_degrees) / max(thresholds.skew_search_degrees, 1e-6))
    )
    glare_component = max(
        0.0, min(1.0, 1.0 - glare_ratio / max(thresholds.glare_ratio_warn * 5.0, 1e-6))
    )

    components = [
        blur_component,
        contrast_component,
        brightness_component,
        skew_component,
        glare_component,
    ]
    score = sum(components) / len(components)
    if blocking:
        score = min(score, 0.2)
    return max(0.0, min(1.0, score))


def assess(
    image: "PIL.Image.Image",
    *,
    target_dpi: int = 350,
    assume_a4: bool = True,
    thresholds: QualityThresholds = DEFAULT_THRESHOLDS,
) -> ImageQuality:
    """Misst die Bildqualitaet von `image` und liefert eine befuellte
    ``types.ImageQuality`` (siehe dort, insbesondere ``ImageQuality.unknown()``,
    dessen neutralen Platzhalter diese Funktion fuer echte Aufrufe ersetzt).

    `target_dpi` wird aktuell nicht in die Messung selbst einbezogen (die
    Metriken sind aufloesungsrelativ genug, um ohne Ziel-DPI auszukommen);
    er ist Teil der Signatur, damit spaetere Verfeinerungen (z.B.
    DPI-abhaengige Schaerfe-Schwellen) ihn nutzen koennen, ohne Aufrufer
    anzupassen.

    VERTRAG zum zurueckgegebenen ``ImageQuality.skew_degrees`` (Gegenseite
    dieses Vertrags: ``preprocess.deskew()``-Docstring): Der Wert ist bereits
    der fertige KORREKTURwinkel im Sinne von ``PIL.Image.rotate()`` -- ihn
    unveraendert an ``preprocess.deskew(image, quality.skew_degrees)``
    weiterzureichen zieht die gemessene Schiefe gerade. NICHT negieren: wer
    den Wert vorher selbst umdreht ("um die Schiefe auszugleichen"),
    VERDOPPELT sie, statt sie zu entfernen -- ein Fehler, der wie "das
    Deskewing wirkt kaum" aussieht, nicht wie ein offensichtlicher
    Vorzeichenfehler. Siehe auch ``_estimate_skew_degrees`` weiter unten fuer
    die Herleitung dieser Konvention.
    """
    import numpy as np

    width, height = image.size
    grey = image.convert("L")
    arr = np.asarray(grey, dtype=np.float64)

    issues: list[str] = []

    if width < thresholds.min_width or height < thresholds.min_height:
        issues.append("too_small")

    blur_score = _laplacian_variance(arr)
    if blur_score < thresholds.blur_variance_min:
        issues.append("too_blurry")

    contrast = _percentile_contrast(arr)
    brightness = float(arr.mean() / 255.0)
    if brightness < thresholds.brightness_dark_max:
        issues.append("too_dark")
    elif brightness > thresholds.brightness_bright_min:
        issues.append("too_bright")
    # low_contrast wird unabhaengig von zu dunkel/hell gemeldet -- ein Bild
    # kann z.B. mittelhell UND kontrastarm sein (verwaschener Scan).
    if contrast < thresholds.contrast_min:
        issues.append("low_contrast")

    glare_ratio = _glare_ratio(arr, thresholds)
    if thresholds.glare_ratio_warn < glare_ratio <= thresholds.glare_ratio_max:
        issues.append("glare")

    skew_degrees = _estimate_skew_degrees(grey, thresholds)
    if abs(skew_degrees) > thresholds.skew_warn_degrees:
        issues.append("skewed")

    # blocking: konservativ, siehe Modul-Docstring -- nur "too_blurry" und
    # "too_small" gelten als so unbrauchbar, dass eine erneute Aufnahme
    # erzwungen wird. "skewed"/"glare"/"low_contrast"/"too_dark"/"too_bright"
    # sind Warnungen, die die Review-UI anzeigt, aber die Pipeline nicht
    # hart stoppen: ein falsches "too_blurry" auf einem eigentlich lesbaren
    # Foto ist fuer eine Lehrkraft deutlich aergerlicher als eine zusaetzliche
    # Pruefung im Review.
    blocking = "too_blurry" in issues or "too_small" in issues

    score = _score(
        blur_score=blur_score,
        contrast=contrast,
        brightness=brightness,
        skew_degrees=skew_degrees,
        glare_ratio=glare_ratio,
        blocking=blocking,
        thresholds=thresholds,
    )

    return ImageQuality(
        width=width,
        height=height,
        estimated_dpi=estimate_dpi(image, assume_a4=assume_a4),
        blur_score=blur_score,
        contrast=contrast,
        brightness=brightness,
        skew_degrees=skew_degrees,
        glare_ratio=glare_ratio,
        issues=tuple(issues),
        blocking=blocking,
        score=score,
    )
