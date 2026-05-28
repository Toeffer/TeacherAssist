import json
import time
from pathlib import Path

import pytest

from tools import student_store


@pytest.fixture(autouse=True)
def vault_in_tmpdir(tmp_path):
    """Lenkt den Vault auf einen temporären Pfad um und säubert die Session."""
    student_store.set_root_override(tmp_path)
    student_store.lock()
    yield tmp_path
    student_store.lock()
    student_store.set_root_override(None)


def test_setup_and_unlock_roundtrip(vault_in_tmpdir):
    assert not student_store.is_setup()
    student_store.setup_master("supersecret-123")
    assert student_store.is_setup()
    assert student_store.is_unlocked()
    student_store.lock()
    assert not student_store.is_unlocked()
    assert student_store.unlock("supersecret-123") is True


def test_unlock_rejects_wrong_password(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    student_store.lock()
    assert student_store.unlock("nope-nope") is False
    assert not student_store.is_unlocked()


def test_short_password_rejected(vault_in_tmpdir):
    with pytest.raises(ValueError):
        student_store.setup_master("short")


def test_setup_twice_rejected(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    with pytest.raises(RuntimeError):
        student_store.setup_master("anothersecret-456")


def test_add_student_creates_encrypted_files(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student(
        {"vorname": "Anna", "nachname": "Müller", "pronomen": "sie"},
        klasse="7a",
    )
    record_path = vault_in_tmpdir / "records" / f"{sid}.enc"
    index_path = vault_in_tmpdir / "index.enc"
    assert record_path.exists()
    assert index_path.exists()
    raw = record_path.read_bytes()
    assert b"Anna" not in raw
    assert b"M\xc3\xbcller" not in raw


def test_list_students_filters_by_class(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")
    student_store.add_student({"vorname": "Ben", "nachname": "Schmidt", "pronomen": "er"}, klasse="7a")
    student_store.add_student({"vorname": "Clara", "nachname": "Weber"}, klasse="8b")

    seven_a = student_store.list_students("7a")
    assert {s["vorname"] for s in seven_a} == {"Anna", "Ben"}
    assert student_store.list_students("9c") == []
    assert len(student_store.list_students()) == 3
    aliases = {s["alias"] for s in student_store.list_students()}
    assert aliases == {"SuS-01", "SuS-02", "SuS-03"}


def test_observations_and_competencies_persist(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")

    student_store.add_observation(sid, "2026-05-12", "Deutsch", "Aktive Mitarbeit beim Lesekreis.", tags=["mitarbeit"])
    student_store.add_observation(sid, "2026-05-13", "Mathematik", "Sicher bei Bruchrechnung.", tags=["stark"])
    student_store.set_competency(sid, "Deutsch", "Leseverstehen", rating=3)
    student_store.set_competency(sid, "Deutsch", "Schreiben", rating=2, note="braucht mehr Übung")

    rec = student_store.get_student(sid)
    assert len(rec["observations"]) == 2
    assert rec["observations"][0]["subject"] == "Deutsch"
    assert rec["observations"][0]["tags"] == ["mitarbeit"]
    assert rec["competencies"]["Deutsch"]["Leseverstehen"]["rating"] == 3
    assert rec["competencies"]["Deutsch"]["Schreiben"]["note"] == "braucht mehr Übung"


def test_update_student_syncs_index(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")
    student_store.update_student(sid, {"klasse": "8a", "identity": {"nachname": "Müller-Meier"}})
    listed = student_store.list_students()[0]
    assert listed["klasse"] == "8a"
    assert listed["nachname"] == "Müller-Meier"


def test_delete_student_removes_record_and_backups(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")
    student_store.add_observation(sid, "2026-05-12", "Deutsch", "Notiz 1.")
    student_store.add_observation(sid, "2026-05-13", "Deutsch", "Notiz 2.")
    record_path = vault_in_tmpdir / "records" / f"{sid}.enc"
    assert record_path.exists()
    assert (vault_in_tmpdir / "records" / f"{sid}.enc.bak1").exists()

    student_store.delete_student(sid)
    assert not record_path.exists()
    assert not (vault_in_tmpdir / "records" / f"{sid}.enc.bak1").exists()
    assert student_store.list_students() == []


def test_export_student_json_returns_full_record(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")
    student_store.add_observation(sid, "2026-05-12", "Deutsch", "Notiz.")
    export = student_store.export_student_json(sid)
    assert export["identity"]["vorname"] == "Anna"
    assert export["observations"][0]["text"] == "Notiz."
    # GDPR Art. 15: muss serialisierbar sein
    json.dumps(export)


def test_import_class_csv(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    csv_text = "vorname;nachname;pronomen\nAnna;Müller;sie\nBen;Schmidt;er\n"
    count = student_store.import_class_csv(csv_text, klasse="7a")
    assert count == 2
    students = student_store.list_students()
    assert {s["vorname"] for s in students} == {"Anna", "Ben"}


def test_idle_timeout_locks_vault(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    student_store.set_idle_timeout(60)  # min erlaubt
    # last_touch künstlich in die Vergangenheit setzen
    student_store._session["last_touch"] = time.time() - 120
    assert not student_store.is_unlocked()


def test_locked_vault_blocks_operations(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    student_store.lock()
    with pytest.raises(RuntimeError, match="gesperrt"):
        student_store.list_students()


def test_relock_persists_data(vault_in_tmpdir):
    student_store.setup_master("supersecret-123")
    sid = student_store.add_student({"vorname": "Anna", "nachname": "Müller"}, klasse="7a")
    student_store.add_observation(sid, "2026-05-12", "Deutsch", "Notiz.")
    student_store.lock()

    assert student_store.unlock("supersecret-123")
    rec = student_store.get_student(sid)
    assert rec["identity"]["vorname"] == "Anna"
    assert rec["observations"][0]["text"] == "Notiz."
