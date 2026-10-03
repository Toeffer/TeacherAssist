"""Fail-closed privacy classification and cloud-payload minimization."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Any, Iterable, Iterator
from urllib.parse import urlparse


SENSITIVE_SKILLS = {
    "schuelerarbeit_bewerten",
    "zeugnis_formulieren",
    "foerderplan_erstellen",
    "lerntagebuch_feedback",
    "klassenstatistik",
}

DOCUMENT_CLASSIFICATIONS = frozenset({"public_curriculum", "personal", "unknown", "student_submission"})
CLOUD_FORBIDDEN_CLASSIFICATIONS = frozenset({"student_submission"})


def cloud_allowed_for_classification(classification: str) -> bool:
    return classification == "public_curriculum"

PERSONAL_PATTERNS = (
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("phone", re.compile(r"(?:\+49|0049|0\d{2,5})[\s\-/]?\d[\d\s\-/]{4,}")),
    ("birth_date", re.compile(r"\b(?:geb\.?|geboren|geburtstag|geburtsdatum)\D{0,20}\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}\b", re.I)),
    ("student_context", re.compile(r"\b(?:schüler(?:in)?|schueler(?:in)?|lernende[rs]?|kind|sohn|tochter|sus|zeugnis|förderplan|foerderplan|nachteilsausgleich|lerntagebuch|benotung|korrektur)\b", re.I)),
    # The cue is case-insensitive ("Für Jonas", "Name: Max"), the name itself
    # must be capitalized. Matches go through person_name_matches(), never
    # through this pattern alone.
    ("person_name", re.compile(
        r"\b(?P<cue>(?i:von|für|fuer|heißt|heisst|namens|name:))\s+"
        r"(?P<first>[A-ZÄÖÜ][a-zäöüß]{2,})(?:\s+(?P<second>[A-ZÄÖÜ][a-zäöüß]{2,}))?"
    )),
    ("student_identifier", re.compile(r"\b(?:SuS|Schüler|Schueler)[-_ ]?\d{1,4}\b", re.I)),
)

# "für"/"von" are weak name cues: German capitalizes every noun, so without
# this list "Arbeitsblatt für Klasse 8" counted as a person's name and forced
# a local model for most ordinary planning prompts. Only words listed here
# (or compounds with the suffixes below) are skipped; every unknown
# capitalized word still counts as a name, so the check stays fail-closed.
# Words that are also first names (August, April, Mai, Juli, ...) are
# deliberately absent. The strong cues heißt/namens/Name: are never filtered.
_WEAK_NAME_CUES = frozenset({"von", "für", "fuer"})
_SCHOOL_NOUNS = frozenset(word.casefold() for word in (
    # subjects
    "Mathematik", "Mathe", "Deutsch", "Englisch", "Französisch", "Franzoesisch", "Latein",
    "Spanisch", "Russisch", "Italienisch", "Griechisch", "Chinesisch", "Türkisch", "Polnisch",
    "Biologie", "Bio", "Chemie", "Physik", "Geschichte", "Geografie", "Geographie", "Erdkunde",
    "Sozialkunde", "Gemeinschaftskunde", "Politik", "Wirtschaft", "Ethik", "Religion",
    "Philosophie", "Kunst", "Musik", "Sport", "Informatik", "Technik", "Sachunterricht",
    "Astronomie", "Naturwissenschaften", "Werken", "Psychologie", "Pädagogik", "Recht",
    # school structure and groups of people
    "Klasse", "Klassen", "Klassenstufe", "Jahrgang", "Jahrgangsstufe", "Stufe", "Oberstufe",
    "Unterstufe", "Mittelstufe", "Sekundarstufe", "Grundschule", "Gymnasium", "Regelschule",
    "Realschule", "Hauptschule", "Gesamtschule", "Gemeinschaftsschule", "Förderschule",
    "Berufsschule", "Schule", "Schulen", "Kurs", "Kurse", "Leistungskurs", "Grundkurs",
    "Gruppe", "Gruppen", "Lerngruppe", "Eltern", "Lehrkraft", "Lehrkräfte", "Lehrer",
    "Lehrerin", "Lehrerinnen", "Kollegen", "Kolleginnen", "Kollegium", "Referendare",
    "Anfänger", "Fortgeschrittene", "Jugendliche", "Erwachsene", "Alle",
    # lessons and material
    "Unterricht", "Stunde", "Stunden", "Doppelstunde", "Einzelstunde", "Vertretung",
    "Einstieg", "Sicherung", "Thema", "Themen", "Einheit", "Reihe", "Material",
    "Materialien", "Arbeitsblatt", "Arbeitsblätter", "Tafelbild", "Aufgabe", "Aufgaben",
    "Übung", "Übungen", "Test", "Tests", "Klassenarbeit", "Klausur", "Klausuren", "Prüfung",
    "Prüfungen", "Abitur", "Hausaufgaben", "Projekt", "Projekte", "Präsentation", "Referat",
    "Referate", "Quiz", "Wiederholung", "Beispiel", "Beispiele", "Ideen", "Methode",
    "Methoden", "Lehrplan", "Lehrpläne", "Kompetenz", "Kompetenzen", "Bewertung", "Noten",
    "Elternabend", "Elternbrief", "Wandertag", "Ausflug", "Exkursion", "Klassenfahrt",
    "Schulfest", "Ferien", "Weihnachten", "Ostern", "Pause", "Inklusion", "Förderung",
    # time
    "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag",
    "Januar", "Februar", "März", "Maerz", "Juni", "September", "Oktober", "November",
    "Dezember", "Woche", "Wochen", "Schuljahr", "Halbjahr", "Semester", "Quartal",
))
# Compound endings ("Gruppenarbeit", "Projektwoche", "Vertretungsstunde"),
# only for words of 8+ letters so short names ending the same way still count.
_SCHOOL_NOUN_SUFFIXES = tuple(suffix.casefold() for suffix in (
    "unterricht", "stunde", "stunden", "arbeit", "arbeiten", "klasse", "klassen", "gruppe",
    "gruppen", "thema", "themen", "blatt", "blätter", "material", "materialien", "aufgabe",
    "aufgaben", "übung", "übungen", "plan", "pläne", "projekt", "projekte", "test", "tests",
    "kurs", "kurse", "einheit", "einheiten", "reihe", "phase", "phasen", "methode", "methoden",
    "kontrolle", "prüfung", "prüfungen", "schule", "schulen", "stufe", "stufen", "woche",
    "wochen", "kunde", "wissenschaft", "wissenschaften", "lehre", "fahrt", "abend", "brief",
    "gespräch", "ung", "heit", "keit", "tion", "schaft",
))


def _is_school_noun(word: str) -> bool:
    folded = word.casefold()
    return folded in _SCHOOL_NOUNS or (len(folded) >= 8 and folded.endswith(_SCHOOL_NOUN_SUFFIXES))


def person_name_matches(text: str) -> Iterator[re.Match]:
    """Matches of the person_name cue that may name a person.

    A weak cue ("für", "von") followed only by known school nouns is skipped;
    everything else, including any unknown capitalized word, is reported."""
    for match in dict(PERSONAL_PATTERNS)["person_name"].finditer(text):
        words = [word for word in match.group("first", "second") if word]
        if match.group("cue").casefold() in _WEAK_NAME_CUES and all(_is_school_noun(word) for word in words):
            continue
        yield match


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
            if name == "person_name":
                if next(person_name_matches(text), None) is not None:
                    findings.add(name)
            elif pattern.search(text):
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
    if classifications & CLOUD_FORBIDDEN_CLASSIFICATIONS:
        reasons.add("student_submission")
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
