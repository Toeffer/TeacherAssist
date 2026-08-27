"""Freigabe-Gate fuer die Bewertung von Schuelerarbeiten.

``evaluate_grading_gate`` ist der Sicherheits-Choke-Point zwischen der
OCR-Pipeline und dem Bewertungs-Skill ``schuelerarbeit_bewerten``: er stellt
sicher, dass eine Lehrkraft jede referenzierte Transkription explizit
freigegeben hat (``OCRStatus.APPROVED``, siehe ocr/types.py), bevor eine
Bewertung auf ihr laufen darf, und blockiert zusaetzlich freigegebene
Dokumente mit verbliebener kritischer Unsicherheit (defence in depth).

WICHTIGER GRENZFALL -- BEWUSST SO GEWOLLT, KEIN BUG: Wird ein
Bewertungs-Skill ganz OHNE referenzierte OCR-Job-IDs aufgerufen (die
Lehrkraft hat die Schuelerantworten selbst per Hand eingetippt), ist das
Gate offen (``allowed=True``). Wir koennen und wollen nicht ueberpruefen, ob
handgetippter Text irgendwo "eigentlich" aus einem nicht freigegebenen Scan
stammt -- das ist die ehrliche Grenze dieses Mechanismus. Niemand sollte das
spaeter als Luecke missverstehen und "reparieren": das wuerde jede manuelle
Eingabe von Bewertungsgrundlagen unbenutzbar machen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .types import DocumentResult, OCRStatus

GRADING_SKILLS = frozenset({"schuelerarbeit_bewerten"})

_GATE_MESSAGE_DE = (
    "Die Transkription ist noch nicht freigegeben. Bitte prüfe die "
    "markierten Unsicherheiten und gib die Abschrift frei, bevor ich bewerte."
)


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...]
    message: str


def evaluate_grading_gate(
    *,
    skill_id: str | None,
    ocr_job_ids: Sequence[str],
    jobs: Mapping[str, DocumentResult],
) -> GateDecision:
    """Prueft, ob ein Bewertungs-Skill fuer die referenzierten OCR-Jobs
    freigegeben ist.

    - Nicht-Bewertungs-Skills sind immer erlaubt.
    - Fuer jede referenzierte Job-ID:
      - fehlt sie in ``jobs`` (unbekannte, client-gelieferte ID), wird
        fail-closed abgelehnt (``"unknown_job:{job_id}"``) -- eine ID, die
        wir nicht aufloesen koennen, ist niemals in Ordnung.
      - ist der Status nicht ``APPROVED``, wird abgelehnt
        (``"not_approved:{job_id}"``).
      - besteht trotz Freigabe noch kritische Unsicherheit, wird abgelehnt
        (``"critical_uncertainty:{job_id}"``, defence in depth).
    - Keine referenzierten Jobs bei einem Bewertungs-Skill: erlaubt (siehe
      Modul-Docstring -- das ist die manuelle Eingabe durch die Lehrkraft).
    """
    if skill_id not in GRADING_SKILLS:
        return GateDecision(allowed=True, reasons=(), message="")

    reasons: list[str] = []
    for job_id in ocr_job_ids:
        job = jobs.get(job_id)
        if job is None:
            reasons.append(f"unknown_job:{job_id}")
            continue
        if job.status is not OCRStatus.APPROVED:
            reasons.append(f"not_approved:{job_id}")
            continue
        if job.has_critical_uncertainty:
            reasons.append(f"critical_uncertainty:{job_id}")

    if reasons:
        return GateDecision(allowed=False, reasons=tuple(reasons), message=_GATE_MESSAGE_DE)
    return GateDecision(allowed=True, reasons=(), message="")
