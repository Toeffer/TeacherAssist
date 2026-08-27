"""Parser fuer die Transkriptions-Markup-Sprache aus prompts.VERBATIM_PROMPT_DE.

Das Modell markiert unsichere/gestrichene/unleserliche Stellen mit einer
kleinen Menge von Pseudo-Tags: ``<uncertain>a|b</uncertain>``,
``<deleted>...</deleted>``, ``<unclear/>``. ``parse_markup`` loest diese Tags
in Klartext auf und liefert daneben strukturierte Informationen, damit
consensus.py daraus synthetische Diskrepanzen bauen kann.

Fail closed: jede nicht eindeutig interpretierbare Markup-Struktur (nicht
geschlossene Tags, verschachtelte Tags, mehr als drei Alternativen) wird
woertlich aus dem Text entfernt und als "malformed" markiert, statt geraten
zu werden -- Aufrufer erzwingen dann needs_review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# U+2423 (OPEN BOX) umschliesst das Fragezeichen, damit die Sentinel-Sequenz
# nicht mit echtem Freitext verwechselt werden kann.
UNCLEAR_SENTINEL = "␣?␣"

_OPEN_TAG_RE = re.compile(r"<(uncertain|deleted|unclear)(\s*/)?>")
_CLOSE_TAG_RE = re.compile(r"</(uncertain|deleted|unclear)>")


@dataclass(frozen=True)
class ParsedMarkup:
    text: str
    alternatives: tuple[tuple[int, tuple[str, ...]], ...]  # (Token-Index, Varianten)
    deleted: tuple[str, ...]
    unclear_count: int
    markers: tuple[str, ...]


def _count_tokens(chunk: str) -> int:
    """Zaehlt Tokens nach derselben Regel wie consensus.tokenize: auf
    Leerzeichen aufgeteilt, wobei ein abschliessendes satzendendes
    .!?: als eigenes Token zaehlt."""
    count = 0
    for word in chunk.split():
        if len(word) > 1 and word[-1] in ".!?:":
            count += 2
        else:
            count += 1
    return count


def parse_markup(raw: str) -> ParsedMarkup:
    text_parts: list[str] = []
    deleted: list[str] = []
    alternatives: list[tuple[int, tuple[str, ...]]] = []
    markers: set[str] = set()
    unclear_count = 0
    token_count = 0

    pos = 0
    length = len(raw)

    while pos < length:
        open_match = _OPEN_TAG_RE.match(raw, pos)
        if open_match:
            tag = open_match.group(1)
            self_closing = bool(open_match.group(2))

            if tag == "unclear" and self_closing:
                text_parts.append(UNCLEAR_SENTINEL)
                token_count += 1
                unclear_count += 1
                pos = open_match.end()
                continue

            close_match = re.compile(rf"</{tag}>").search(raw, open_match.end())
            if close_match is None:
                # Kein schliessendes Tag im gesamten Rest des Textes: nicht
                # geschlossenes Tag, woertlich entfernen, fail closed.
                markers.add("malformed")
                pos = open_match.end()
                continue

            inner = raw[open_match.end() : close_match.start()]
            if _OPEN_TAG_RE.search(inner) or _CLOSE_TAG_RE.search(inner):
                # Verschachteltes Tag innerhalb dieser Spanne -- nicht
                # interpretieren, Tags woertlich entfernen und markieren.
                markers.add("malformed")
                inner_clean = _CLOSE_TAG_RE.sub("", _OPEN_TAG_RE.sub("", inner))
                text_parts.append(inner_clean)
                token_count += _count_tokens(inner_clean)
                pos = close_match.end()
                continue

            if tag == "uncertain":
                variants = inner.split("|")
                if len(variants) < 2 or len(variants) > 3:
                    markers.add("malformed")
                    text_parts.append(inner)
                    token_count += _count_tokens(inner)
                else:
                    preferred = variants[0]
                    text_parts.append(preferred)
                    alternatives.append((token_count, tuple(variants)))
                    token_count += _count_tokens(preferred)
                    markers.add("uncertain")
            elif tag == "deleted":
                # Durchgestrichener Schuelertext darf nie zur Bewertung
                # gelangen -- daher NICHT in text_parts, nur in .deleted.
                deleted.append(inner)
            else:  # tag == "unclear" (offen+geschlossen, z.B. <unclear></unclear>)
                text_parts.append(UNCLEAR_SENTINEL)
                token_count += 1
                unclear_count += 1

            pos = close_match.end()
            continue

        close_match = _CLOSE_TAG_RE.match(raw, pos)
        if close_match:
            # Verwaistes schliessendes Tag ohne passenden Opener.
            markers.add("malformed")
            pos = close_match.end()
            continue

        next_open = _OPEN_TAG_RE.search(raw, pos)
        next_close = _CLOSE_TAG_RE.search(raw, pos)
        candidates = [m for m in (next_open, next_close) if m is not None]
        end = min((m.start() for m in candidates), default=length)

        chunk = raw[pos:end]
        if chunk:
            text_parts.append(chunk)
            token_count += _count_tokens(chunk)
        pos = end if candidates else length

    return ParsedMarkup(
        text="".join(text_parts),
        alternatives=tuple(alternatives),
        deleted=tuple(deleted),
        unclear_count=unclear_count,
        markers=tuple(sorted(markers)),
    )
