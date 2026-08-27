"""Pseudonymisierung von Schuelernamen fuer Bewertungs-Workflows.

Speichert eine Zuordnung "echter Name" <-> "Alias" (``SuS-01``, ``SuS-02``,
...), Fernet-verschluesselt auf der Platte -- exakt dasselbe Muster wie
``EncryptedStateStore`` in teacherassist_core/storage.py und der
``CredentialStore`` in teacherassist_core/runtime.py: mit ``raw_key=None``
(kein Windows-Credential-Manager verfuegbar) laeuft die Zuordnung rein im
Arbeitsspeicher weiter und WIRD NIEMALS AUF DIE PLATTE GESCHRIEBEN -- weder
verschluesselt noch (erst recht nicht) im Klartext. Kein Schreibversuch,
keine Ausnahme dabei: der Aufrufer merkt den degradierten Modus daran, dass
die Datei nach einem Prozessende schlicht nicht existiert.

``pseudonymize()`` ersetzt ABSICHTLICH NUR die Namen, die explizit uebergeben
wurden -- niemals automatisch alle von ``detect()`` vorgeschlagenen
Kandidaten. ``detect()`` liefert lediglich Vorschlaege fuer die Lehrkraft-UI;
eine automatische Ersetzung waere unzuverlaessig (Nachnamen, die mit
Fachvokabular kollidieren, OCR-Fehler mitten im Namen selbst) und eine
falsche Ersetzung wuerde die Abschrift, auf der die Bewertung anschliessend
laeuft, still korrumpieren. Die Lehrkraft bestaetigt jeden Namen einzeln in
der UI, bevor er ersetzt wird.

``restore()`` ist ausschliesslich fuer die lokale Ausgabe lehrkraft-seitigen
Feedbacks gedacht (Text wieder mit echten Namen anzeigen). Das Ergebnis darf
NIEMALS an einen Cloud-Anbieter gehen -- es enthaelt per Definition wieder
die echten, pseudonymisierten Namen.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .. import privacy
from ..storage import PersistenceUnavailable

logger = logging.getLogger(__name__)

NAME_FIELD_RE = re.compile(
    r"(?im)^\s*(?:name|namen|vorname|nachname|schüler(?:in)?|schueler(?:in)?)\s*[:\-–]\s*(.{2,60})$"
)

_ALIAS_RE = re.compile(r"SuS-\d{2}")
_PERSON_NAME_TRIGGER_RE = re.compile(
    r"^(?:von|für|fuer|heißt|heisst|namens|name:)\s+", re.I
)
_WORD_CHAR_RE = re.compile(r"\w", re.UNICODE)


def _boundary_pattern(name: str) -> re.Pattern[str]:
    """Baut ein Ersetzungsmuster fuer ``name``, das nur an Wortgrenzen
    ("\\b") greift -- so rewritet ein bestaetigtes "Tim" nicht "Timo" oder
    "Timur", und ein bestaetigtes "Berg" nicht "Bergbau".

    Python-``\\b`` ist bei ``str``-Mustern Unicode-bewusst, daher zaehlen
    ae/oe/ue/ss als Wortzeichen. Faengt ein Name mit einem Nicht-Wortzeichen
    an oder hoert damit auf (z.B. ein alleinstehendes "Dr." mit
    abschliessendem Punkt), wuerde ein starres ``\\b`` an dieser Seite nie
    matchen, weil beide Seiten der Grenze dann Nicht-Wortzeichen waeren --
    deshalb wird die jeweilige Grenze nur angewendet, wenn das erste bzw.
    letzte Zeichen des Namens selbst ein Wortzeichen ist."""
    escaped = re.escape(name)
    leading = r"\b" if _WORD_CHAR_RE.match(name[0]) else ""
    trailing = r"\b" if _WORD_CHAR_RE.match(name[-1]) else ""
    return re.compile(f"{leading}{escaped}{trailing}")


@dataclass(frozen=True)
class Pseudonym:
    real: str
    alias: str
    first_seen: float


class PseudonymMap:
    """Fernet-verschluesselte Alias-Zuordnung mit degradiertem In-Memory-Modus.

    Im degradierten Modus (``raw_key=None``) bleibt die Zuordnung fuer die
    Lebensdauer des Prozesses funktionsfaehig, geht aber beim Neustart
    verloren -- ``restore()`` kann dann spaeter keine Aliase mehr auf echte
    Namen zurueckfuehren. Aufrufer, die Pseudonyme oder Aliase in der UI
    anzeigen, SOLLTEN ``persistent`` pruefen und diesen Zustand der Lehrkraft
    sichtbar machen (z.B. ein Hinweis-Icon), statt den degradierten Modus
    still zu lassen."""

    def __init__(self, path: Path, raw_key: bytes | None) -> None:
        self.path = path
        self.raw_key = raw_key
        self._lock = threading.RLock()
        self._data = self._load()
        if not raw_key:
            logger.warning(
                "PseudonymMap laeuft ohne Verschluesselungsschluessel im "
                "In-Memory-Modus (%s): Zuordnung geht beim Neustart verloren.",
                path,
            )

    @property
    def persistent(self) -> bool:
        """True, wenn diese Zuordnung tatsaechlich verschluesselt auf die
        Platte geschrieben wird. False im degradierten In-Memory-Modus."""
        return bool(self.raw_key)

    # -- Persistenz (mirrors EncryptedStateStore in storage.py) --------

    def _fernet(self):
        if not self.raw_key:
            raise PersistenceUnavailable("Encrypted persistence requires Windows Credential Manager")
        from cryptography.fernet import Fernet

        return Fernet(base64.urlsafe_b64encode(self.raw_key))

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"schemaVersion": 1, "nextIndex": 1, "entries": []}

    def _load(self) -> dict[str, Any]:
        if not self.raw_key or not self.path.exists():
            return self._empty()
        try:
            plaintext = self._fernet().decrypt(self.path.read_bytes())
            data = json.loads(plaintext.decode("utf-8"))
            return data if isinstance(data, dict) else self._empty()
        except Exception:
            return self._empty()

    def _save(self) -> None:
        # Degradierter Modus: kein Schluessel -> nie auf die Platte schreiben,
        # weder verschluesselt noch im Klartext. Kein Fehler, kein Hinweis --
        # die Zuordnung bleibt einfach nur im Prozessspeicher gueltig.
        if not self.raw_key:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ciphertext = self._fernet().encrypt(json.dumps(self._data, ensure_ascii=False).encode("utf-8"))
        fd, temp_name = tempfile.mkstemp(prefix="pseudonyms-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(ciphertext)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    # -- Alias-Zuordnung --------------------------------------------------

    def alias_for(self, name: str) -> str:
        """Liefert den stabilen Alias fuer ``name`` (z.B. ``"SuS-01"``).

        Derselbe Name bekommt immer denselben Alias; ein neuer Name bekommt
        den naechsten freien, monotonen Index."""
        normalized = name.strip()
        with self._lock:
            for entry in self._data["entries"]:
                if entry["real"] == normalized:
                    return entry["alias"]
            index = self._data["nextIndex"]
            alias = f"SuS-{index:02d}"
            self._data["entries"].append({
                "real": normalized,
                "alias": alias,
                "firstSeen": time.time(),
            })
            self._data["nextIndex"] = index + 1
            self._save()
            return alias

    def real_for(self, alias: str) -> str | None:
        with self._lock:
            for entry in self._data["entries"]:
                if entry["alias"] == alias:
                    return entry["real"]
        return None

    def detect(self, text: str) -> tuple[str, ...]:
        """Schlaegt Namenskandidaten vor -- ersetzt NICHTS.

        Quellen: Treffer von ``NAME_FIELD_RE``, die erste nicht-leere Zeile
        des Texts, sowie Treffer von ``privacy.PERSONAL_PATTERNS``' Muster
        ``person_name``. Reihenfolge und Duplikate werden dedupliziert,
        Reihenfolge des ersten Auftretens bleibt erhalten."""
        candidates: list[str] = []
        seen: set[str] = set()

        def add(candidate: str) -> None:
            candidate = candidate.strip()
            if candidate and candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)

        for match in NAME_FIELD_RE.finditer(text):
            add(match.group(1))

        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                add(stripped)
                break

        person_name_pattern = dict(privacy.PERSONAL_PATTERNS)["person_name"]
        for match in person_name_pattern.finditer(text):
            add(_PERSON_NAME_TRIGGER_RE.sub("", match.group(0)))

        return tuple(candidates)

    def pseudonymize(self, text: str, names: Sequence[str]) -> tuple[str, tuple[Pseudonym, ...]]:
        """Ersetzt NUR die explizit uebergebenen ``names`` durch ihren Alias.

        ``detect()`` liefert lediglich Vorschlaege; hier werden ausschliesslich
        die von der Lehrkraft bestaetigten Namen tatsaechlich ersetzt (siehe
        Modul-Docstring).

        Die Ersetzung selbst greift NUR an Wortgrenzen (``_boundary_pattern``)
        -- ein einfaches ``str.replace`` wuerde auch innerhalb anderer Woerter
        treffen (bestaetigtes "Tim" wuerde "Timo" zu "SuS-01o" verstuemmeln)
        und wuerde damit still die Abschrift korrumpieren, auf der die
        Bewertung anschliessend laeuft. Namen werden dabei absteigend nach
        Laenge ersetzt, damit ein laengerer bestaetigter Name (z.B.
        "Anna Meier") konsumiert wird, bevor ein separat bestaetigtes
        Praefix davon (z.B. "Anna") greifen kann."""
        normalized_names = [name.strip() for name in names if name.strip()]

        applied: list[Pseudonym] = []
        aliases: dict[str, str] = {}
        for normalized in normalized_names:
            alias = self.alias_for(normalized)
            aliases[normalized] = alias
            with self._lock:
                first_seen_ts = next(
                    (entry["firstSeen"] for entry in self._data["entries"] if entry["alias"] == alias),
                    time.time(),
                )
            applied.append(Pseudonym(real=normalized, alias=alias, first_seen=first_seen_ts))

        result = text
        for normalized in sorted(set(normalized_names), key=len, reverse=True):
            result = _boundary_pattern(normalized).sub(aliases[normalized], result)

        return result, tuple(applied)

    def restore(self, text: str) -> str:
        """Ersetzt Aliase durch die echten Namen -- NUR fuer lokale,
        lehrkraft-seitige Ausgabe. Das Ergebnis darf niemals an einen
        Cloud-Anbieter weitergereicht werden."""

        def _replace(match: re.Match[str]) -> str:
            real = self.real_for(match.group(0))
            return real if real is not None else match.group(0)

        return _ALIAS_RE.sub(_replace, text)
