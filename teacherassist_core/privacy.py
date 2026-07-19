"""Fail-closed privacy classification and cloud-payload minimization."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse


SENSITIVE_SKILLS = {
    "schuelerarbeit_bewerten",
    "zeugnis_formulieren",
    "foerderplan_erstellen",
    "lerntagebuch_feedback",
    "klassenstatistik",
}

PERSONAL_PATTERNS = (
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("phone", re.compile(r"(?:\+49|0049|0\d{2,5})[\s\-/]?\d[\d\s\-/]{4,}")),
    ("birth_date", re.compile(r"\b(?:geb\.?|geboren|geburtstag|geburtsdatum)\D{0,20}\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}\b", re.I)),
    ("student_context", re.compile(r"\b(?:schüler(?:in)?|schueler(?:in)?|lernende[rs]?|kind|sohn|tochter|sus|zeugnis|förderplan|foerderplan|nachteilsausgleich|lerntagebuch|benotung|korrektur)\b", re.I)),
    ("person_name", re.compile(r"\b(?:von|für|fuer|heißt|heisst|namens|name:)\s+[A-ZÄÖÜ][a-zäöüß]{2,}(?:\s+[A-ZÄÖÜ][a-zäöüß]{2,})?")),
    ("student_identifier", re.compile(r"\b(?:SuS|Schüler|Schueler)[-_ ]?\d{1,4}\b", re.I)),
)


@dataclass(frozen=True)
class PrivacyDecision:
    mode: str
    reasons: tuple[str, ...]

    @property
    def local_required(self) -> bool:
        return self.mode == "local_required"


def _string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _string_values(item)


def findings_for(value: Any) -> set[str]:
    findings: set[str] = set()
    for text in _string_values(value):
        for name, pattern in PERSONAL_PATTERNS:
            if pattern.search(text):
                findings.add(name)
    return findings


def anonymize_text(text: str) -> str:
    patterns = dict(PERSONAL_PATTERNS)
    result = patterns["email"].sub("[E-Mail]", text)
    result = patterns["phone"].sub("[Telefon]", result)
    if re.search(r"(geb\b\.?|geboren|geburtstag|geburtsdatum)", result, re.I):
        result = re.sub(r"\b\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4}\b", "[Datum]", result)
    return result


def decide_privacy(
    *,
    messages: Any,
    profile: Any = None,
    skill_id: str | None = None,
    requested_mode: str = "auto",
    sticky_mode: str = "auto",
    document_classifications: Iterable[str] = (),
    rag_context: Any = None,
) -> PrivacyDecision:
    reasons: set[str] = set()
    if requested_mode == "local_required":
        reasons.add("user_requested_local")
    if sticky_mode == "local_required":
        reasons.add("chat_already_local")
    if skill_id in SENSITIVE_SKILLS:
        reasons.add(f"sensitive_skill:{skill_id}")
    classifications = set(document_classifications)
    if any(item != "public_curriculum" for item in classifications):
        reasons.add("document_not_public")
    for finding in findings_for({"messages": messages, "profile": profile, "rag": rag_context}):
        reasons.add(f"personal_data:{finding}")
    mode = "local_required" if reasons else "cloud_allowed"
    return PrivacyDecision(mode=mode, reasons=tuple(sorted(reasons)))


def minimize_cloud_profile(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    allowed = ("bundesland", "schulform", "faecher", "style_formality", "style_detail")
    return {key: profile[key] for key in allowed if key in profile}


def is_trusted_loopback_endpoint(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower().rstrip(".")
        if host == "localhost":
            return True
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False
