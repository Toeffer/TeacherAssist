"""Precision of the regex-based personal-data check in decide_privacy().

German capitalizes every noun, so the "für/von + capitalized word" name cue
used to treat "Arbeitsblatt für Klasse 8" as a person's name and force a
local model for most ordinary planning prompts. The cue now skips known
school nouns, while every unknown capitalized word still counts as a name
(fail-closed).
"""

from __future__ import annotations

import pytest

from teacherassist_core.ocr.pseudonyms import PseudonymMap
from teacherassist_core.privacy import decide_privacy, findings_for


def _decision(text):
    return decide_privacy(messages=[{"role": "user", "text": text}])


@pytest.mark.parametrize(
    "prompt",
    [
        "Plane eine Stunde für Mathematik in Klasse 7 zum Thema Bruchrechnung",
        "Erstelle ein Arbeitsblatt zur Photosynthese für Klasse 8",
        "Ich brauche ein Tafelbild für Geschichte: Die Weimarer Republik",
        "Für Deutsch in der Oberstufe: Ideen für eine Doppelstunde zu Kafka",
        "Eine Vertretungsstunde für Englisch, 45 Minuten",
        "Material für Gruppenarbeit und Ideen für Montag",
        "Ein Quiz von Biologie bis Chemie für die Projektwoche",
        "Hausaufgaben für Anfänger und Fortgeschrittene",
        "Elternbrief für den Wandertag im September",
        "Erwartungshorizont für Klausuren im Leistungskurs Physik",
    ],
)
def test_ordinary_planning_prompts_stay_cloud_eligible(prompt):
    decision = _decision(prompt)

    assert "personal_data:person_name" not in decision.reasons, decision.reasons
    assert decision.local_required is False, decision.reasons


@pytest.mark.parametrize(
    "prompt",
    [
        "Schreib ein Feedback für Max zu seinem Referat",
        "Der Aufsatz von Lena Müller braucht eine Rückmeldung",
        "Für Jonas brauche ich eine Rückmeldung",       # cue at sentence start
        "VON Emma kam heute eine Frage",                 # upper-case cue
        "Eine kurze Notiz für Mathea",                   # name that starts like "Mathe"
        "Eine Rückmeldung für August",                   # month and first name
        "Eine Rückmeldung für Mai",                      # month and first name
        "Lob für Mathematik Ben",                        # one known noun, one name
        "Das Kind heißt Mathematik",                     # strong cues are never filtered
        "Name: Klasse Gruppe",
    ],
)
def test_real_names_are_still_detected(prompt):
    assert "person_name" in findings_for(prompt)
    assert _decision(prompt).local_required is True


def test_other_personal_data_rules_are_unchanged():
    reasons = _decision(
        "Kontakt max@example.de, Tel. 030 1234567, geboren am 01.02.2010, SuS-04"
    ).reasons

    for finding in ("email", "phone", "birth_date", "student_identifier"):
        assert f"personal_data:{finding}" in reasons


def test_ocr_name_suggestions_skip_school_nouns(tmp_path):
    """The OCR pseudonymizer reuses the same cue to suggest names to the
    teacher; "Mathematik" or "Klasse" are not names worth suggesting."""
    store = PseudonymMap(tmp_path / "unused.enc", raw_key=None)
    text = "Arbeit für Mathematik in Klasse 7\nDie Lösung stammt von Erika Musterfrau."

    candidates = store.detect(text)

    assert "Erika Musterfrau" in candidates
    assert "Mathematik" not in candidates
