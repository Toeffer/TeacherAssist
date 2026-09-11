"""Encrypted local profile and chat persistence."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class PersistenceUnavailable(RuntimeError):
    pass


class StateConflict(RuntimeError):
    """Raised when a browser tries to replace an out-of-date saved state."""

    def __init__(self, expected_revision: int | None, actual_revision: int) -> None:
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision
        super().__init__("Saved state was changed in another browser tab")


class EncryptedStateStore:
    def __init__(self, path: Path, raw_key: bytes | None) -> None:
        self.path = path
        self.raw_key = raw_key
        self._lock = threading.RLock()

    def _fernet(self):
        if not self.raw_key:
            raise PersistenceUnavailable("Encrypted persistence requires Windows Credential Manager")
        from cryptography.fernet import Fernet

        return Fernet(base64.urlsafe_b64encode(self.raw_key))

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"schemaVersion": 2, "stateRevision": 0, "profile": {}, "chats": {}}

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            plaintext = self._fernet().decrypt(self.path.read_bytes())
            data = json.loads(plaintext.decode("utf-8"))
            if not isinstance(data, dict):
                return self._empty()
            # Existing encrypted files predate revisions.  Treat them as the
            # first version rather than forcing an unsafe browser overwrite.
            revision = data.get("stateRevision", 0)
            data["stateRevision"] = revision if isinstance(revision, int) and revision >= 0 else 0
            data["schemaVersion"] = 2
            return data
        except PersistenceUnavailable:
            raise
        except Exception as exc:
            raise RuntimeError("Encrypted state could not be read") from exc

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ciphertext = self._fernet().encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        fd, temp_name = tempfile.mkstemp(prefix="state-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(ciphertext)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _canonical_checksum(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            chats = list((data.get("chats") or {}).values())
            chats.sort(key=lambda item: item.get("updatedAt", 0), reverse=True)
            return {
                "stateRevision": data.get("stateRevision", 0),
                "profile": dict(data.get("profile") or {}),
                "chats": chats,
            }

    def replace_state(
        self,
        profile: dict[str, Any],
        chats: list[dict[str, Any]],
        *,
        expected_revision: int | None,
    ) -> dict[str, Any]:
        if not isinstance(profile, dict) or not isinstance(chats, list) or len(chats) > 500:
            raise ValueError("Invalid browser state")
        normalized = {}
        now = int(time.time() * 1000)
        for record in chats:
            if not isinstance(record, dict):
                continue
            chat = dict(record)
            chat_id = str(chat.get("id", ""))
            try:
                uuid.UUID(chat_id)
            except ValueError:
                chat_id = str(uuid.uuid4())
            messages = chat.get("messages")
            if not isinstance(messages, list) or len(messages) > 10000:
                messages = []
            chat.update({
                "id": chat_id,
                "title": str(chat.get("title") or "Neuer Chat")[:100],
                "messages": messages,
                "privacyMode": "local_required" if chat.get("privacyMode") == "local_required" else "auto",
                "createdAt": int(chat.get("createdAt") or now),
                "updatedAt": int(chat.get("updatedAt") or now),
            })
            normalized[chat_id] = chat
        with self._lock:
            data = self._load()
            actual_revision = data.get("stateRevision", 0)
            if expected_revision != actual_revision:
                raise StateConflict(expected_revision, actual_revision)
            data["profile"] = dict(profile)
            data["chats"] = normalized
            data["stateRevision"] = actual_revision + 1
            self._save(data)
        return self.get_state()

    def import_browser_state(
        self,
        profile: dict[str, Any],
        chats: list[dict[str, Any]],
        *,
        expected_revision: int | None,
    ) -> dict[str, Any]:
        source = {"profile": profile, "chats": chats}
        state = self.replace_state(profile, chats, expected_revision=expected_revision)
        return {
            "sourceChecksum": self._canonical_checksum(source),
            "profileImported": bool(profile),
            "chatCount": len(state["chats"]),
            "state": state,
        }

    def get_profile(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._load().get("profile") or {})

    def set_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(profile, dict):
            raise ValueError("Profile must be an object")
        with self._lock:
            data = self._load()
            data["profile"] = profile
            data["stateRevision"] = data.get("stateRevision", 0) + 1
            self._save(data)
        return profile

    def list_chats(self) -> list[dict[str, Any]]:
        with self._lock:
            chats = self._load().get("chats") or {}
            return [
                {
                    "id": chat["id"],
                    "title": chat.get("title", "Neuer Chat"),
                    "privacyMode": chat.get("privacyMode", "auto"),
                    "updatedAt": chat.get("updatedAt", 0),
                    "messageCount": len(chat.get("messages") or []),
                }
                for chat in sorted(chats.values(), key=lambda item: item.get("updatedAt", 0), reverse=True)
            ]

    def create_chat(self, title: str = "Neuer Chat", messages: list | None = None) -> dict[str, Any]:
        now = int(time.time() * 1000)
        chat = {
            "id": str(uuid.uuid4()),
            "title": (title or "Neuer Chat")[:100],
            "privacyMode": "auto",
            "messages": messages or [],
            "createdAt": now,
            "updatedAt": now,
        }
        with self._lock:
            data = self._load()
            data.setdefault("chats", {})[chat["id"]] = chat
            data["stateRevision"] = data.get("stateRevision", 0) + 1
            self._save(data)
        return chat

    def get_chat(self, chat_id: str) -> dict[str, Any] | None:
        with self._lock:
            chat = (self._load().get("chats") or {}).get(chat_id)
            return dict(chat) if chat else None

    def save_chat(self, chat: dict[str, Any]) -> dict[str, Any]:
        chat_id = str(chat.get("id", ""))
        try:
            uuid.UUID(chat_id)
        except ValueError as exc:
            raise ValueError("Invalid chat ID") from exc
        chat["updatedAt"] = int(time.time() * 1000)
        with self._lock:
            data = self._load()
            data.setdefault("chats", {})[chat_id] = chat
            data["stateRevision"] = data.get("stateRevision", 0) + 1
            self._save(data)
        return chat

    def delete_chat(self, chat_id: str) -> bool:
        with self._lock:
            data = self._load()
            removed = data.setdefault("chats", {}).pop(chat_id, None) is not None
            if removed:
                data["stateRevision"] = data.get("stateRevision", 0) + 1
                self._save(data)
            return removed
