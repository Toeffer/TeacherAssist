"""Mehr-Engine-OCR-Konsens: Ausrichtung, Diskrepanzerkennung, Statusentscheidung.

Kernidee: mehrere OCR-Engines lesen dieselbe Region, eine davon wird als
Referenz gewaehlt (pick_reference), die anderen werden gegen die Referenz
ausgerichtet (align, via difflib) und alle Nicht-Uebereinstimmungen werden zu
Disagreement-Objekten zusammengefasst (collect_disagreements). classify_span
(critical_tokens.py) entscheidet, ob eine Abweichung bedeutungsveraendernd
("kritisch") ist. decide_status leitet daraus den Seitenstatus ab.
"""

from __future__ import annotations

import difflib
import unicodedata
from dataclasses import dataclass, replace
from typing import Sequence

from .critical_tokens import CriticalTokenConfig, classify_span
from .markup import parse_markup
from .types import ImageQuality, OCRCandidate, OCRStatus, Region, RegionType, Disagreement

ENGINE_PRIORITY: tuple[str, ...] = ("htr", "paddleocr_vl", "ollama_vlm", "tesseract")
MERGE_GAP = 1

_DASH_CHARS = "‐‑‒–—―−"
_QUOTE_CHARS = "“”„‟‘’‚‛«»‹›\"'"
_DASH_TABLE = str.maketrans({ch: "-" for ch in _DASH_CHARS})
_QUOTE_TABLE = str.maketrans({ch: "'" for ch in _QUOTE_CHARS})
_STRIP_PUNCTUATION = " \t\n\r()[]{}<>«»‹›„“”‚‘’*_~"
_SENTENCE_FINAL = (".", "!", "?", ":")


def normalize_token(token: str) -> str:
    """Normalisiert ein Token fuer den ALIGNMENT-Vergleich (nicht fuer die
    Kritikalitaetspruefung -- die urteilt immer ueber die Originaltokens).

    Bewusst NICHT normalisiert: "," vs. "." (Dezimaltrennzeichen ist
    semantisch), "+"/"-", Ziffernfolgen, Gross-/Kleinschreibung innerhalb
    chemischer Formeln. Ein normalisiertes "-4" darf z.B. nicht zu "4"
    werden, sonst wuerde ein Vorzeichenfehler beim Alignment als
    Uebereinstimmung durchgehen und die Diskrepanz nie entdeckt."""
    text = unicodedata.normalize("NFKC", token)
    text = text.casefold()
    text = text.translate(_DASH_TABLE)
    text = text.translate(_QUOTE_TABLE)
    text = " ".join(text.split())
    return text.strip(_STRIP_PUNCTUATION)


def tokenize(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Teilt `text` auf Leerzeichen auf, behaelt Interpunktion an Tokens
    haengen -- ausser ein abschliessendes satzendendes .!?: wird als
    eigenes Token abgespalten. Gibt (Originaltokens, normalisierte Tokens)
    zurueck."""
    raw_tokens: list[str] = []
    for chunk in text.split():
        if len(chunk) > 1 and chunk[-1] in _SENTENCE_FINAL:
            raw_tokens.append(chunk[:-1])
            raw_tokens.append(chunk[-1])
        else:
            raw_tokens.append(chunk)
    normalized = tuple(normalize_token(t) for t in raw_tokens)
    return tuple(raw_tokens), normalized


def _token_count(candidate: OCRCandidate) -> int:
    if candidate.tokens:
        return len(candidate.tokens)
    return len(tokenize(candidate.text)[0])


def pick_reference(candidates: Sequence[OCRCandidate]) -> OCRCandidate:
    """Waehlt die Referenz-Engine: hoechster ENGINE_PRIORITY-Rang, bei
    Gleichstand hoehere mittlere Konfidenz, dann mehr Tokens, dann
    Enginename (aufsteigend) als deterministischer letzter Tie-Break."""
    if not candidates:
        raise ValueError("pick_reference benoetigt mindestens einen Kandidaten")

    def rank(candidate: OCRCandidate) -> tuple:
        try:
            priority = ENGINE_PRIORITY.index(candidate.engine)
        except ValueError:
            priority = len(ENGINE_PRIORITY)
        return (priority, -candidate.confidence, -_token_count(candidate), candidate.engine)

    return min(candidates, key=rank)


@dataclass(frozen=True)
class AlignmentOp:
    tag: str  # "equal" | "replace" | "delete" | "insert"
    ref_start: int
    ref_end: int
    other_start: int
    other_end: int


def align(reference: OCRCandidate, other: OCRCandidate) -> list[AlignmentOp]:
    _, ref_norm = tokenize(reference.text)
    _, other_norm = tokenize(other.text)
    # autojunk=False ist zwingend, nicht kosmetisch: SequenceMatchers
    # Standard-Heuristik behandelt jedes Token, das in >1% einer laengeren
    # als 200 Elemente umfassenden Sequenz vorkommt, als "Junk" und ignoriert
    # es beim Finden von Uebereinstimmungen. Auf einer 400-Token-Seite
    # verwirft das stillschweigend "der", "die", "ist" -- und "nicht", genau
    # das kritische Negationswort, wegen dessen dieses Modul existiert. Siehe
    # tests/test_ocr_consensus.py::test_autojunk_disabled_on_long_pages.
    matcher = difflib.SequenceMatcher(None, ref_norm, other_norm, autojunk=False)
    return [
        AlignmentOp(tag=tag, ref_start=i1, ref_end=i2, other_start=j1, other_end=j2)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
    ]


def _map_position(ops: Sequence[AlignmentOp], pos: int, *, source: str) -> int | None:
    """Bildet eine Randposition aus dem `source`-Tokenraum ("ref" oder
    "other") auf die entsprechende Position im jeweils anderen Tokenraum ab,
    unter Nutzung der Ops, die beide Sequenzen luecklos partitionieren."""
    for op in ops:
        if source == "ref":
            s_start, s_end, t_start, t_end = op.ref_start, op.ref_end, op.other_start, op.other_end
        else:
            s_start, s_end, t_start, t_end = op.other_start, op.other_end, op.ref_start, op.ref_end
        if s_start <= pos <= s_end:
            if s_end == s_start:
                if pos == s_start:
                    return t_start
                continue
            if op.tag == "equal":
                return t_start + (pos - s_start)
            if pos == s_start:
                return t_start
            if pos == s_end:
                return t_end
    return None


def _engine_range_for_ref_span(
    ops: Sequence[AlignmentOp], start: int, end: int
) -> tuple[int, int] | None:
    """Bildet einen Referenzbereich [start, end) auf den entsprechenden
    Bereich im 'other'-Tokenraum ab.

    Fuer NICHT-nullbreite Bereiche (start < end) sind zwei unabhaengige
    Randabbildungen ueber _map_position() korrekt: da die Ops beide
    Sequenzen lueckenlos und ueberlappungsfrei partitionieren, liefert der
    gemeinsame Rand zweier benachbarter Ops IMMER denselben Wert, egal
    welche der beiden Ops ihn aufloest (other_end des einen Ops ==
    other_start des naechsten, per Konstruktion von
    SequenceMatcher.get_opcodes()).

    Fuer NULLBREITE Bereiche (start == end -- eine reine Insertion in der
    Referenz, z.B. ein Wort, das nur eine Nicht-Referenz-Engine liefert)
    versagt genau diese Randabbildung strukturell: BEIDE unabhaengigen
    Aufrufe (fuer start und fuer end) landen zwangslaeufig auf demselben
    gemeinsamen Randwert (siehe Beweis oben), sodass jede Insertion als
    leerer Bereich rekonstruiert wuerde -- unabhaengig davon, welche Engine
    Referenz ist. DAS war die Ursache des kritischen Falsch-Negativ-Bugs:
    eine Negation, die nur eine Nicht-Referenz-Engine lieferte, verschwand
    spurlos aus dem Konsens (0 Disagreements statt 1 kritischer). Fuer
    diesen Fall wird deshalb gezielt nach einem Op gesucht, der SELBST in
    Referenz-Weite null ist (ref_start == ref_end == start) -- also einer
    echten Insertion an genau dieser Stelle -- und dessen VOLLER
    other-Bereich zurueckgegeben, statt ihn ueber zwei Randpunkte zu
    erschliessen, die sich rechnerisch zwangslaeufig zum selben Wert
    zusammenziehen. Existiert kein solcher Op (diese Engine hat an dieser
    Stelle nichts eingefuegt), faellt es auf die normale Randabbildung
    zurueck, die dann korrekt einen leeren Bereich an der richtigen Stelle
    liefert (die Engine stimmt der Referenz an dieser Stelle einfach zu)."""
    if start == end:
        for op in ops:
            if op.ref_start == start and op.ref_end == start:
                return (op.other_start, op.other_end)
        mapped = _map_position(ops, start, source="ref")
        if mapped is None:
            return None
        return (mapped, mapped)

    other_start = _map_position(ops, start, source="ref")
    other_end = _map_position(ops, end, source="ref")
    if other_start is None or other_end is None:
        return None
    return (other_start, other_end)


def _merge_ranges(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1] + MERGE_GAP:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def _ordered_variant_items(
    ref_text: str, variant_map: dict[str, set[str]]
) -> list[tuple[str, tuple[str, ...]]]:
    """Reference-Variante zuerst, danach alle uebrigen in stabiler
    Erscheinungsreihenfolge (Einfuegereihenfolge des dict)."""
    items = list(variant_map.items())
    items.sort(key=lambda item: 0 if item[0] == ref_text else 1)
    return [(text, tuple(sorted(engines))) for text, engines in items]


def collect_disagreements(
    reference: OCRCandidate,
    others: Sequence[OCRCandidate],
    *,
    config: CriticalTokenConfig,
) -> tuple[Disagreement, ...]:
    """Ermittelt alle Diskrepanzen zwischen `reference` und `others`.

    Ablauf: (1) jede andere Engine gegen die Referenz ausrichten und alle
    Nicht-equal-Ops als rohe Referenz-Bereiche sammeln; (2) synthetische
    Bereiche aus <uncertain>-Markup JEDES Kandidaten (inkl. der Referenz
    selbst) hinzufuegen, sodass eine einzelne Engine sich mit einem
    <uncertain>ist|ist nicht</uncertain> selbst eskalieren kann; (3)
    ueberlappende/durch <= MERGE_GAP Referenz-Tokens getrennte Bereiche
    zusammenfassen; (4) je Bereich die tatsaechlichen Varianten pro Engine
    rekonstruieren und via classify_span bewerten."""
    ref_raw, _ = tokenize(reference.text)
    all_candidates = (reference, *others)

    ops_by_engine: dict[str, list[AlignmentOp]] = {}
    other_raw_by_engine: dict[str, tuple[str, ...]] = {}
    raw_ranges: list[tuple[int, int]] = []

    for other in others:
        ops = align(reference, other)
        ops_by_engine[other.engine] = ops
        other_raw, _ = tokenize(other.text)
        other_raw_by_engine[other.engine] = other_raw
        for op in ops:
            if op.tag != "equal":
                raw_ranges.append((op.ref_start, op.ref_end))

    # Synthetische Spannen aus Markup-Alternativen (auch der Referenz selbst).
    synthetic_positions: list[tuple[int, OCRCandidate, tuple[str, ...]]] = []
    for candidate in all_candidates:
        parsed = parse_markup(candidate.raw_text)
        if not parsed.alternatives:
            continue
        cand_raw, _ = tokenize(candidate.text)
        for token_index, variant_texts in parsed.alternatives:
            if token_index >= len(cand_raw):
                continue
            if candidate is reference:
                ref_index = token_index
            else:
                ref_index = _map_position(ops_by_engine[candidate.engine], token_index, source="other")
            if ref_index is None:
                continue
            synthetic_positions.append((ref_index, candidate, variant_texts))
            raw_ranges.append((ref_index, ref_index + 1))

    if not raw_ranges:
        return ()

    merged = _merge_ranges(raw_ranges)
    disagreements: list[Disagreement] = []

    for start, end in merged:
        ref_text = " ".join(ref_raw[start:end])
        variant_map: dict[str, set[str]] = {ref_text: {reference.engine}}

        for other in others:
            ops = ops_by_engine[other.engine]
            # _engine_range_for_ref_span (nicht die zwei unabhaengigen
            # _map_position-Aufrufe direkt) -- siehe deren Docstring: fuer
            # nullbreite Bereiche (reine Insertionen in der Referenz)
            # wuerden zwei unabhaengige Randabbildungen IMMER auf denselben
            # Wert zusammenfallen und die Insertion als leeren Bereich
            # rekonstruieren, egal welche Engine Referenz ist.
            span = _engine_range_for_ref_span(ops, start, end)
            if span is None:
                continue
            other_start, other_end = span
            other_raw = other_raw_by_engine[other.engine]
            other_text = " ".join(other_raw[other_start:other_end])
            variant_map.setdefault(other_text, set()).add(other.engine)

        for ref_index, candidate, variant_texts in synthetic_positions:
            if not (start <= ref_index < end):
                continue
            for variant_text in variant_texts:
                variant_map.setdefault(variant_text, set()).add(candidate.engine)

        distinct_normalized = {normalize_token(text) for text in variant_map}
        if len(distinct_normalized) <= 1:
            continue

        variants_tuple = tuple(_ordered_variant_items(ref_text, variant_map))
        # Ein Nachbar-Referenztoken je Seite reicht: er gibt classify_span
        # genug Kontext, um ein per Leerzeichen abgetrenntes
        # Negationspraefix ("un moeglich") zu erkennen, dessen Grundwort
        # ("moeglich") als "equal"-Op ausserhalb DIESER Spanne liegt (siehe
        # critical_tokens.classify_span Docstring). Die Spanne selbst wird
        # dadurch NICHT veraendert -- consensus_text/agreement/Review-UI
        # sehen weiterhin exakt denselben Bereich; nur die
        # Kritikalitaetsbewertung bekommt zusaetzlichen Kontext.
        left_context = ref_raw[start - 1] if start > 0 else ""
        right_context = ref_raw[end] if end < len(ref_raw) else ""
        critical, reason = classify_span(
            variants_tuple, config, left_context=left_context, right_context=right_context
        )
        disagreements.append(
            Disagreement(start=start, end=end, variants=variants_tuple, critical=critical, reason=reason)
        )

    return tuple(disagreements)


_NO_SPACE_BEFORE = frozenset({".", "!", "?", ":"})


def _join_tokens(tokens: Sequence[str]) -> str:
    parts: list[str] = []
    for token in tokens:
        if parts and token not in _NO_SPACE_BEFORE:
            parts.append(" ")
        parts.append(token)
    return "".join(parts)


def _render_bracket(disagreement: Disagreement) -> str:
    texts = [text for text, _engines in disagreement.variants]
    ref_text = texts[0]
    others = texts[1:]

    if ref_text and not any(others):
        return f"[{ref_text}?]"

    if not ref_text:
        non_empty = [t for t in others if t]
        if len(non_empty) == 1:
            return f"[+{non_empty[0]}?]"
        if non_empty:
            return f"[+{'|'.join(non_empty)}?]"

    distinct: list[str] = []
    for text in texts:
        if text and text not in distinct:
            distinct.append(text)
    return f"[{'|'.join(distinct)}?]"


def render_consensus(ref_tokens: Sequence[str], disagreements: Sequence[Disagreement]) -> str:
    """Rendert den Konsenstext: Referenztokens mit [...]-Markierungen an
    jeder Diskrepanzstelle. Erfuellt die Invariante, dass
    re.findall(r"\\[[^\\]]*\\?\\]", ergebnis) genau len(disagreements)
    Treffer liefert.

    Duenner Wrapper um render_consensus_with_offsets(), der nur den Text
    zurueckgibt -- gibt es zusaetzlich zur Wrapper-Funktion, weil
    tests/test_ocr_consensus.py::test_render_consensus_bracket_formats
    render_consensus direkt mit hand-gebauten Disagreements aufruft und per
    Gleichheitspruefung einen reinen String erwartet (nicht editierbar,
    siehe Auftrag)."""
    text, _ = render_consensus_with_offsets(ref_tokens, disagreements)
    return text


def render_consensus_with_offsets(
    ref_tokens: Sequence[str], disagreements: Sequence[Disagreement]
) -> tuple[str, tuple[Disagreement, ...]]:
    """Wie render_consensus(), gibt zusaetzlich dieselben Disagreements
    zurueck, ergaenzt (via dataclasses.replace) um char_start/char_end --
    den Zeichenbereich ihrer gerenderten "[...]"-Klammer INNERHALB des
    zurueckgegebenen Texts. Das ist die einzige Stelle, die diese Position
    kennt: sie baut die Zeichenkette Stueck fuer Stueck auf und weiss daher
    exakt, wo jede Klammer beginnt/endet -- auch wenn eine Diskrepanz
    mehrere Referenztokens umfasst (z.B. "[nicht wirklich|kaum?]", das
    client-seitig per Whitespace in ZWEI Tokens zerfaellt, hier aber als
    EINE Klammer mit einem zusammenhaengenden Zeichenbereich gefuehrt wird).

    Die Positionsberechnung spiegelt _join_tokens() Token fuer Token: vor
    jedem Token (auch der Klammer als Ganzes) wird genau dann ein
    Leerzeichen eingerechnet, wenn schon mindestens ein Token ausgegeben
    wurde UND das Token nicht in _NO_SPACE_BEFORE liegt -- identisch zu
    _join_tokens()' eigener Regel. So bleibt der zurueckgegebene Text exakt
    identisch zu dem, was render_consensus() liefert, und die Offsets sind
    trotzdem fuer Klammern an Position 0 und am Stringende korrekt."""
    tokens_out: list[str] = []
    length = 0
    pos = 0
    with_offsets: list[Disagreement] = []
    for disagreement in sorted(disagreements, key=lambda d: d.start):
        while pos < disagreement.start:
            token = ref_tokens[pos]
            if tokens_out and token not in _NO_SPACE_BEFORE:
                length += 1
            length += len(token)
            tokens_out.append(token)
            pos += 1
        bracket = _render_bracket(disagreement)
        if tokens_out and bracket not in _NO_SPACE_BEFORE:
            length += 1
        char_start = length
        length += len(bracket)
        char_end = length
        tokens_out.append(bracket)
        with_offsets.append(replace(disagreement, char_start=char_start, char_end=char_end))
        pos = disagreement.end
    while pos < len(ref_tokens):
        token = ref_tokens[pos]
        if tokens_out and token not in _NO_SPACE_BEFORE:
            length += 1
        length += len(token)
        tokens_out.append(token)
        pos += 1
    return _join_tokens(tokens_out), tuple(with_offsets)


def _region_status() -> OCRStatus:
    # Eine frisch aus der Konsens-Pipeline gebaute Region ist IMMER
    # NEEDS_REVIEW, nie etwas anderes:
    #   - nie APPROVED: das ist ausschliesslich einer expliziten
    #     Lehrkraft-Aktion vorbehalten (types.OCRStatus.APPROVED:
    #     "consensus NEVER sets this"). decide_status darf das inzwischen
    #     auf SEITENebene fuer nicht-schuelerbezogenes Material mit
    #     explizitem auto_approve tun -- aber build_region kennt weder
    #     dieses Flag noch decide_status' min_agreement/min_confidence-
    #     Schwellen und kann diese Entscheidung also gar nicht vorwegnehmen.
    #   - nie PROCESSING: das wuerde "wird noch bearbeitet" bedeuten, obwohl
    #     die Region bereits fertig ausgewertet ist -- fuer eine per Poll
    #     abgefragte Region waere das irrefuehrend (Stufe 9 Review-UI).
    # Ob eine Diskrepanz kritisch ist oder nicht: beides zeigt die Review-UI
    # an (kritisch rot, unkritisch amber) und beides verdient einen Blick,
    # also wird hier nicht unterschieden. Der Seitenstatus (decide_status)
    # entscheidet allein ueber Freigabe/Review.
    return OCRStatus.NEEDS_REVIEW


def build_region(
    region_id: str,
    region_type: RegionType,
    bbox: tuple[int, int, int, int],
    candidates: Sequence[OCRCandidate],
    *,
    config: CriticalTokenConfig,
    classification: str,
) -> Region:
    if not candidates:
        raise ValueError("build_region benoetigt mindestens einen Kandidaten")

    # `classification` fliesst aktuell in keine Entscheidung hier ein (der
    # Regionsstatus ist immer NEEDS_REVIEW, siehe _region_status) -- sie
    # bleibt Teil der Signatur, weil nur decide_status auf Seitenebene genug
    # Kontext (auto_approve, min_agreement/min_confidence) hat, um ueber
    # APPROVED zu entscheiden. Wird hier als Parameter gehalten, damit
    # Aufrufer (und eine spaetere Region-spezifische Policy) sie nicht neu
    # durchreichen muessen.
    reference = pick_reference(candidates)
    others = [c for c in candidates if c is not reference]
    disagreements = collect_disagreements(reference, others, config=config)
    ref_raw, _ = tokenize(reference.text)
    # render_consensus_with_offsets() statt render_consensus(): die Region
    # muss die char_start/char_end-tragenden Disagreements weiterreichen
    # (siehe Disagreement.char_start docstring), nicht die rohen aus
    # collect_disagreements() ohne Zeichenposition.
    consensus_text, disagreements = render_consensus_with_offsets(ref_raw, disagreements)

    if not others:
        # Eine einzelne Engine stimmt mit niemandem ueberein -- sie kann nie
        # eine Uebereinstimmung von 1.0 erreichen, auch wenn es keine
        # Diskrepanzen gibt (siehe Spezifikation zu agreement).
        agreement = 0.0
    else:
        # max(1, ...) pro Disagreement: eine reine Insertion (start == end)
        # ist im Referenz-Tokenraum nullbreit und wuerde sonst 0 zum
        # Zaehler beitragen -- eine kritische Diskrepanz koennte so
        # agreement == 1.0 erreichen und die min_agreement-Schranke in
        # decide_status() unbemerkt passieren, obwohl es explizit eine
        # Diskrepanz gibt. Eine nullbreite Stelle zaehlt daher als
        # mindestens 1 abweichendes Token.
        disagreed_tokens = sum(max(1, d.end - d.start) for d in disagreements)
        agreement = 1.0 - disagreed_tokens / max(len(ref_raw), 1)
        agreement = max(0.0, min(1.0, agreement))

    return Region(
        id=region_id,
        type=region_type,
        bbox=bbox,
        candidates=tuple(candidates),
        reference_engine=reference.engine,
        consensus_text=consensus_text,
        selected_text=reference.text,
        disagreements=disagreements,
        agreement=agreement,
        status=_region_status(),
    )


def decide_status(
    regions: Sequence[Region],
    *,
    quality: ImageQuality,
    engine_failures: Sequence[tuple[str, str]],
    require_engines: Sequence[str],
    config: CriticalTokenConfig,
    classification: str,
    min_agreement: float = 0.98,
    min_confidence: float = 0.75,
    auto_approve: bool = False,
) -> tuple[OCRStatus, bool, tuple[str, ...]]:
    """Leitet den Seitenstatus aus den Regionen ab. `classification ==
    "student_submission"` gibt NIE automatisch frei, egal wie sauber der
    Konsens ist und egal, was `auto_approve` sagt -- Schuelerarbeiten
    brauchen immer den Blick einer Lehrkraft. Nicht-schuelerbezogenes
    Material erreicht APPROVED nur bei sauberem Konsens UND ausdruecklich
    gesetztem `auto_approve=True`; sonst (der Default) bleibt es
    NEEDS_REVIEW. PROCESSING wird von dieser Funktion nie zurueckgegeben --
    das waere fuer eine bereits fertig ausgewertete Seite irrefuehrend
    (siehe Stufe 5's Job-Polling). FAILED nur, wenn ueberhaupt keine Engine
    irgendwo einen Kandidaten geliefert hat."""
    reasons: list[str] = []

    failed_engine_names = {name for name, _reason in engine_failures}
    for name in require_engines:
        if name in failed_engine_names:
            reasons.append(f"engine_unavailable:{name}")

    if not any(region.candidates for region in regions):
        reasons.append("no_candidates")
        return OCRStatus.FAILED, False, tuple(reasons)

    if any(region.has_critical_uncertainty for region in regions):
        reasons.append("critical_uncertainty")
    if any(region.agreement < min_agreement for region in regions):
        reasons.append("low_agreement")

    mean_confidences = [
        sum(c.confidence for c in region.candidates) / len(region.candidates)
        for region in regions
        if region.candidates
    ]
    if mean_confidences and min(mean_confidences) < min_confidence:
        reasons.append("low_confidence")

    if quality.blocking:
        reasons.append("image_quality")

    engines_seen = {c.engine for region in regions for c in region.candidates}
    if len(engines_seen) < 2:
        reasons.append("single_engine")

    reasons_t = tuple(reasons)
    auto_clean = not reasons_t

    if classification == "student_submission":
        # Schuelerarbeiten werden NIE automatisch freigegeben, egal wie
        # sauber der Konsens ist und egal, was der Aufrufer bei auto_approve
        # uebergibt (Gueltigkeitspruefung mit Gurt UND Traeger: der Check
        # steht bewusst vor der auto_approve-Abfrage, nicht nur in der
        # classification-Vorbedingung dort).
        status = OCRStatus.NEEDS_REVIEW
    elif auto_clean and auto_approve and classification != "student_submission":
        # Anderes (nicht-schuelerbezogenes) Material darf APPROVED nur bei
        # ausdruecklich gesetztem auto_approve erreichen (Settings-Schluessel
        # ocrAutoApproveNonStudent, Default False) -- und nur dann. Das ist
        # die einzige Stelle in der gesamten Pipeline, an der die
        # Konsens-Logik APPROVED vergibt; sie tut das nur im Namen einer
        # expliziten, vom Aufrufer gesetzten Policy-Entscheidung, nie auf
        # eigene Initiative.
        status = OCRStatus.APPROVED
    else:
        status = OCRStatus.NEEDS_REVIEW

    return status, auto_clean, reasons_t
