"""Testet die Cloud-Sperre und die Pseudonymisierung fuer Schuelerarbeiten.

Deckt teacherassist_core/ocr/privacy_guard.py (CloudBlocked, assert_local_only),
teacherassist_core/privacy.py (cloud_allowed_for_classification :nach Zeile 18,
decide_privacy :69 -- additive Erweiterung um den Grund "student_submission")
und teacherassist_core/ocr/pseudonyms.py (PseudonymMap, Pseudonym) ab.
"""

from __future__ import annotations

import os

import pytest

from teacherassist_core.ocr.privacy_guard import CloudBlocked, assert_local_only
from teacherassist_core.ocr.pseudonyms import PseudonymMap
from teacherassist_core.privacy import decide_privacy


# ---------------------------------------------------------------------------
# privacy_guard.py
# ---------------------------------------------------------------------------


def test_cloud_blocked_for_student_submission():
    """assert_local_only (privacy_guard.py) blockiert einen echten
    Cloud-Endpunkt fuer 'student_submission', laesst aber einen
    vertrauenswuerdigen Loopback-Endpunkt (privacy.is_trusted_loopback_endpoint,
    privacy.py:102) sowie eine Cloud-erlaubte Klassifikation durch."""
    with pytest.raises(CloudBlocked) as excinfo:
        assert_local_only("student_submission", "https://api.openrouter.ai/v1/chat")
    assert excinfo.value.classification == "student_submission"
    assert excinfo.value.endpoint == "https://api.openrouter.ai/v1/chat"

    assert_local_only("student_submission", "http://127.0.0.1:11434/api")  # darf nicht werfen

    assert_local_only("public_curriculum", "https://api.openrouter.ai/v1/chat")  # darf nicht werfen


def test_assert_local_only_passes_engine_through():
    """assert_local_only (privacy_guard.py) reicht ein optionales `engine=`
    1:1 an CloudBlocked durch (Fix B): `.engine` traegt den Namen, und
    str(exc) nennt ihn ebenfalls (CloudBlocked.__str__ baut die Meldung aus
    dem aktuellen `self.engine`). Ohne `engine=` bleibt `.engine` weiterhin
    None -- kein bestehender Aufrufer bricht."""
    with pytest.raises(CloudBlocked) as excinfo:
        assert_local_only(
            "student_submission", "https://api.openrouter.ai/v1/chat", engine="vlm-cloud"
        )
    assert excinfo.value.engine == "vlm-cloud"
    assert "vlm-cloud" in str(excinfo.value)

    with pytest.raises(CloudBlocked) as excinfo_no_engine:
        assert_local_only("student_submission", "https://api.openrouter.ai/v1/chat")
    assert excinfo_no_engine.value.engine is None


# ---------------------------------------------------------------------------
# privacy.py -- additive Erweiterung
# ---------------------------------------------------------------------------


def test_decide_privacy_forces_local_for_student_submission():
    """Spiegelt test_decide_privacy_forces_local_for_non_public_documents in
    tests/test_tool_server.py: fuer classification=student_submission ist
    local_required True und 'student_submission' steht unter den Gruenden
    (privacy.py: decide_privacy, additive Erweiterung um
    CLOUD_FORBIDDEN_CLASSIFICATIONS)."""
    decision = decide_privacy(
        messages=[{"role": "user", "text": "Bitte bewerte diese Klassenarbeit."}],
        skill_id=None,
        document_classifications=["student_submission"],
    )

    assert decision.local_required is True
    assert "student_submission" in decision.reasons
    assert "document_not_public" in decision.reasons


def test_decide_privacy_existing_behaviour_unchanged():
    """Regressions-Wächter: die vor Stufe 4a bestehenden Klassifikations-Faelle
    liefern identische PrivacyDecisions wie zuvor -- die Erweiterung in
    decide_privacy (privacy.py:96-97) ist rein additiv und darf bestehende
    Faelle nicht veraendern."""
    public = decide_privacy(
        messages=[{"role": "user", "text": "Was steht im Lehrplan zur Bruchrechnung?"}],
        skill_id=None,
        document_classifications=["public_curriculum"],
    )
    assert public.local_required is False
    assert public.reasons == ()

    personal = decide_privacy(
        messages=[{"role": "user", "text": "Was steht im Lehrplan zur Bruchrechnung?"}],
        skill_id=None,
        document_classifications=["personal"],
    )
    assert personal.local_required is True
    assert personal.reasons == ("document_not_public",)

    no_documents = decide_privacy(
        messages=[{"role": "user", "text": "Erklaere mir Photosynthese."}],
        skill_id=None,
        document_classifications=[],
    )
    assert no_documents.local_required is False
    assert no_documents.reasons == ()

    sensitive_skill = decide_privacy(
        messages=[{"role": "user", "text": "Bitte hilf mir dabei."}],
        skill_id="zeugnis_formulieren",
        document_classifications=[],
    )
    assert sensitive_skill.local_required is True
    assert sensitive_skill.reasons == ("sensitive_skill:zeugnis_formulieren",)


# ---------------------------------------------------------------------------
# pseudonyms.py
# ---------------------------------------------------------------------------


def test_pseudonym_map_round_trip_and_stability(tmp_path):
    """alias_for (pseudonyms.py) vergibt stabile, monotone Aliase: derselbe
    Name liefert zweimal denselben Alias, ein neuer Name den naechsten Index.
    restore() kehrt die Ersetzung um. Mit raw_key=None (degradierter Modus)
    wird niemals auf die Platte geschrieben -- die Datei existiert danach
    nicht (siehe Modul-Docstring, mirrors CredentialStore/EncryptedStateStore)."""
    key = os.urandom(32)
    path = tmp_path / "pseudonyms.enc"
    store = PseudonymMap(path, raw_key=key)

    alias1_a = store.alias_for("Max Mustermann")
    alias1_b = store.alias_for("Max Mustermann")
    alias2 = store.alias_for("Erika Musterfrau")

    assert alias1_a == "SuS-01"
    assert alias1_b == "SuS-01"
    assert alias2 == "SuS-02"

    text = "Max Mustermann hat die Aufgabe geloest."
    pseudonymized, applied = store.pseudonymize(text, ["Max Mustermann"])
    assert pseudonymized == "SuS-01 hat die Aufgabe geloest."
    assert len(applied) == 1
    assert applied[0].real == "Max Mustermann"
    assert applied[0].alias == "SuS-01"
    assert isinstance(applied[0].first_seen, float)

    restored = store.restore(pseudonymized)
    assert restored == text

    degraded_path = tmp_path / "degraded.enc"
    degraded_store = PseudonymMap(degraded_path, raw_key=None)
    degraded_store.alias_for("Max Mustermann")
    assert not degraded_path.exists()


def test_pseudonymize_only_replaces_confirmed_names(tmp_path):
    """detect() (pseudonyms.py) schlaegt mehrere Kandidaten vor, aber
    pseudonymize() ersetzt ausschliesslich den Namen, den die Lehrkraft
    explizit bestaetigt (uebergeben) hat -- niemals automatisch alle
    Vorschlaege (siehe Modul-Docstring)."""
    store = PseudonymMap(tmp_path / "unused.enc", raw_key=None)
    text = (
        "Name: Max Mustermann\n"
        "Die Antwort stammt von Erika Musterfrau und wurde korrigiert."
    )

    candidates = store.detect(text)
    assert "Max Mustermann" in candidates
    assert "Erika Musterfrau" in candidates
    assert len(candidates) >= 2

    pseudonymized, applied = store.pseudonymize(text, ["Max Mustermann"])

    assert "Erika Musterfrau" in pseudonymized
    assert "Max Mustermann" not in pseudonymized
    assert len(applied) == 1
    assert applied[0].real == "Max Mustermann"


def test_pseudonym_file_is_not_plaintext(tmp_path):
    """Mit einem echten Schluessel enthalten die auf der Platte liegenden
    Bytes nicht den Klartext-Namen (Fernet-Verschluesselung, mirrors
    EncryptedStateStore in storage.py)."""
    key = os.urandom(32)
    path = tmp_path / "pseudonyms.enc"
    store = PseudonymMap(path, raw_key=key)

    store.alias_for("Max Mustermann")

    raw_bytes = path.read_bytes()
    assert b"Max Mustermann" not in raw_bytes
    assert b"Max" not in raw_bytes


def test_pseudonymize_respects_word_boundaries(tmp_path):
    """pseudonymize() (pseudonyms.py: _boundary_pattern) ersetzt nur ganze
    Woerter. Ein bestaetigtes "Tim" darf "Timo" oder "Timur" nicht
    verstuemmeln -- ein einfaches str.replace wuerde genau das tun und damit
    still die Abschrift korrumpieren, auf der die Bewertung anschliessend
    laeuft."""
    store = PseudonymMap(tmp_path / "unused.enc", raw_key=None)
    text = "Timo und Timur waren da, aber Tim nicht."

    pseudonymized, applied = store.pseudonymize(text, ["Tim"])

    assert "Timo" in pseudonymized
    assert "Timur" in pseudonymized
    assert len(applied) == 1
    alias = applied[0].alias
    assert pseudonymized == f"Timo und Timur waren da, aber {alias} nicht."


def test_pseudonymize_handles_umlauts_and_punctuation(tmp_path):
    """_boundary_pattern (pseudonyms.py) ist Unicode-bewusst (ae/oe/ue/ss
    zaehlen als Wortzeichen) und escaped Namen mit Bindestrich oder Punkt
    korrekt via re.escape, statt an ihnen zu zerbrechen. Ein Name, der mit
    einem Nicht-Wortzeichen endet, wuerde mit einer starren, immer gesetzten
    Wortgrenze am Ende nie matchen (beide Seiten waeren dann
    Nicht-Wortzeichen) -- deshalb wird die Randbedingung je nach erstem/
    letztem Zeichen des Namens selbst gesetzt oder weggelassen."""
    store = PseudonymMap(tmp_path / "unused.enc", raw_key=None)

    umlaut_text = "Jürgen Groß hat die Aufgabe geloest."
    pseudonymized, applied = store.pseudonymize(umlaut_text, ["Jürgen Groß"])
    assert "Jürgen Groß" not in pseudonymized
    assert pseudonymized == f"{applied[0].alias} hat die Aufgabe geloest."

    hyphen_text = "Anna-Lena war im Unterricht."
    pseudonymized, applied = store.pseudonymize(hyphen_text, ["Anna-Lena"])
    assert "Anna-Lena" not in pseudonymized
    assert pseudonymized == f"{applied[0].alias} war im Unterricht."

    title_text = "Dr. Meier hat korrigiert."
    pseudonymized, applied = store.pseudonymize(title_text, ["Dr. Meier"])
    assert "Dr. Meier" not in pseudonymized
    assert pseudonymized == f"{applied[0].alias} hat korrigiert."


def test_pseudonymize_prefers_longest_name_first(tmp_path):
    """pseudonymize() (pseudonyms.py) ersetzt bestaetigte Namen absteigend
    nach Laenge: "Anna Meier" wird konsumiert, bevor das separat bestaetigte
    Praefix "Anna" greifen kann -- sonst wuerde "Anna Meier" durch den
    naiven "Anna"-Alias halb aufgefressen."""
    store = PseudonymMap(tmp_path / "unused.enc", raw_key=None)
    text = "Anna Meier antwortete zuerst. Spaeter meldete sich auch Anna."

    pseudonymized, applied = store.pseudonymize(text, ["Anna Meier", "Anna"])

    aliases = {p.real: p.alias for p in applied}
    assert aliases["Anna Meier"] != aliases["Anna"]
    assert pseudonymized == (
        f"{aliases['Anna Meier']} antwortete zuerst. "
        f"Spaeter meldete sich auch {aliases['Anna']}."
    )


def test_pseudonym_map_reports_non_persistent_without_key(tmp_path):
    """PseudonymMap.persistent (pseudonyms.py) macht den degradierten Modus
    sichtbar, statt ihn still zu lassen: False ohne Schluessel (Zuordnung
    geht beim Neustart verloren), True mit einem echten Schluessel."""
    degraded = PseudonymMap(tmp_path / "degraded.enc", raw_key=None)
    assert degraded.persistent is False

    persisted = PseudonymMap(tmp_path / "persisted.enc", raw_key=os.urandom(32))
    assert persisted.persistent is True
