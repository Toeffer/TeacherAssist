"""Regression coverage for optimistic whole-state persistence."""

from __future__ import annotations

import os

import pytest

from teacherassist_core.storage import EncryptedStateStore, StateConflict


def test_whole_state_save_requires_current_revision(tmp_path):
    store = EncryptedStateStore(tmp_path / "state.enc", os.urandom(32))
    initial = store.get_state()
    assert initial["stateRevision"] == 0

    first = store.replace_state({"name": "A"}, [], expected_revision=0)
    assert first["stateRevision"] == 1

    with pytest.raises(StateConflict) as conflict:
        store.replace_state({"name": "B"}, [], expected_revision=0)
    assert conflict.value.actual_revision == 1
    assert store.get_state()["profile"] == {"name": "A"}


def test_all_state_mutations_advance_revision(tmp_path):
    store = EncryptedStateStore(tmp_path / "state.enc", os.urandom(32))
    chat = store.create_chat()
    after_chat = store.get_state()["stateRevision"]
    store.set_profile({"name": "Lehrkraft"})
    assert store.get_state()["stateRevision"] == after_chat + 1
    store.delete_chat(chat["id"])
    assert store.get_state()["stateRevision"] == after_chat + 2
