"""Runtime paths, non-secret settings, credentials, and capability checks."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import secrets
import shutil
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SETTINGS_KEYS = {
    "schemaVersion",
    "provider",
    "ollamaModel",
    "model",
    "customEndpoint",
    "customModel",
    "chatPersistence",
}
DEFAULT_SETTINGS = {
    "schemaVersion": 2,
    "provider": "openrouter",
    "ollamaModel": "gemma3:4b",
    "model": "deepseek/deepseek-chat",
    "customEndpoint": "",
    "customModel": "gpt-3.5-turbo",
    "chatPersistence": True,
}


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    memory: Path
    uploads: Path
    exports: Path
    logs: Path
    chroma: Path
    settings: Path
    encrypted_state: Path
    migration_manifest: Path

    @classmethod
    def from_environment(cls, repo_root: Path) -> "RuntimePaths":
        override = os.environ.get("TEACHERASSIST_DATA_DIR", "").strip()
        if override:
            root = Path(override).expanduser().resolve()
        else:
            local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
            if local_app_data:
                root = (Path(local_app_data) / "TeacherAssist").resolve()
            else:
                root = (Path.home() / ".teacherassist").resolve()
        return cls(
            root=root,
            memory=root / "memory",
            uploads=root / "uploads",
            exports=root / "exports",
            logs=root / "logs",
            chroma=root / "chroma_db",
            settings=root / "settings.json",
            encrypted_state=root / "state.enc",
            migration_manifest=root / "migration-v2.json",
        )

    def ensure(self, template_memory: Path | None = None) -> None:
        for directory in (self.root, self.memory, self.uploads, self.exports, self.logs, self.chroma):
            directory.mkdir(parents=True, exist_ok=True)
        if template_memory and template_memory.is_dir():
            for source in template_memory.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(template_memory)
                destination = self.memory / relative
                if not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)


class CredentialStore:
    """Credential Manager wrapper with an in-memory, non-persistent fallback."""

    SERVICE = "TeacherAssist"
    OPENROUTER = "openrouter-api-key"
    CUSTOM = "custom-api-key"
    DATA_KEY = "runtime-data-key"

    def __init__(self) -> None:
        self._session: dict[str, str] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _environment_value(name: str) -> str:
        env_names = {
            CredentialStore.OPENROUTER: "OPENROUTER_API_KEY",
            CredentialStore.CUSTOM: "TEACHERASSIST_CUSTOM_API_KEY",
        }
        return os.environ.get(env_names.get(name, ""), "").strip()

    @staticmethod
    def _keyring():
        try:
            import keyring

            return keyring
        except Exception:
            return None

    def get(self, name: str) -> str:
        env_value = self._environment_value(name)
        if env_value:
            return env_value
        with self._lock:
            if name in self._session:
                return self._session[name]
        keyring = self._keyring()
        if keyring is None:
            return ""
        try:
            return (keyring.get_password(self.SERVICE, name) or "").strip()
        except Exception:
            return ""

    def set(self, name: str, value: str, *, require_persistence: bool = False) -> bool:
        value = (value or "").strip()
        if not value:
            raise ValueError("Credential value must not be empty")
        keyring = self._keyring()
        if keyring is not None:
            try:
                keyring.set_password(self.SERVICE, name, value)
                with self._lock:
                    self._session.pop(name, None)
                return True
            except Exception:
                if require_persistence:
                    raise RuntimeError("Windows Credential Manager is unavailable")
        if require_persistence:
            raise RuntimeError("The keyring package or credential backend is unavailable")
        with self._lock:
            self._session[name] = value
        return False

    def delete(self, name: str) -> None:
        with self._lock:
            self._session.pop(name, None)
        keyring = self._keyring()
        if keyring is not None:
            try:
                keyring.delete_password(self.SERVICE, name)
            except Exception:
                pass

    def get_or_create_data_key(self) -> bytes | None:
        encoded = self.get(self.DATA_KEY)
        if encoded:
            try:
                raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
                return raw if len(raw) == 32 else None
            except Exception:
                return None
        raw = secrets.token_bytes(32)
        encoded = base64.urlsafe_b64encode(raw).decode("ascii")
        try:
            if self.set(self.DATA_KEY, encoded, require_persistence=True):
                return raw
        except RuntimeError:
            return None
        return None

    def status(self) -> dict[str, bool]:
        return {
            "hasApiKey": bool(self.get(self.OPENROUTER)),
            "hasCustomApiKey": bool(self.get(self.CUSTOM)),
            "credentialPersistence": self._keyring() is not None,
        }


class SettingsStore:
    def __init__(self, path: Path, credentials: CredentialStore) -> None:
        self.path = path
        self.credentials = credentials
        self._lock = threading.RLock()

    def load(self) -> dict[str, Any]:
        result = dict(DEFAULT_SETTINGS)
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                result.update({key: value for key, value in raw.items() if key in SETTINGS_KEYS})
        except (FileNotFoundError, OSError, ValueError, TypeError):
            pass
        if result.get("provider") not in {"openrouter", "ollama", "custom"}:
            result["provider"] = DEFAULT_SETTINGS["provider"]
        result["schemaVersion"] = 2
        return result

    def public(self) -> dict[str, Any]:
        return {**self.load(), **self.credentials.status()}

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(patch, dict):
            raise ValueError("Settings patch must be an object")
        with self._lock:
            current = self.load()
            for key in SETTINGS_KEYS:
                if key in patch:
                    current[key] = patch[key]
            if current.get("provider") not in {"openrouter", "ollama", "custom"}:
                raise ValueError("Unsupported provider")

            if isinstance(patch.get("apiKey"), str) and patch["apiKey"].strip():
                self.credentials.set(CredentialStore.OPENROUTER, patch["apiKey"])
            if patch.get("clearApiKey") is True:
                self.credentials.delete(CredentialStore.OPENROUTER)
            if isinstance(patch.get("customApiKey"), str) and patch["customApiKey"].strip():
                self.credentials.set(CredentialStore.CUSTOM, patch["customApiKey"])
            if patch.get("clearCustomApiKey") is True:
                self.credentials.delete(CredentialStore.CUSTOM)

            self._write(current)
            return self.public()

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        sanitized = {key: data[key] for key in SETTINGS_KEYS if key in data}
        sanitized["schemaVersion"] = 2
        fd, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(sanitized, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def migrate_legacy(self, legacy_path: Path) -> dict[str, Any]:
        """Copy legacy settings and remove plaintext secrets only after keyring success."""
        if self.path.exists() or not legacy_path.exists():
            return {"migrated": False}
        try:
            legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        except Exception:
            return {"migrated": False, "error": "legacy_settings_unreadable"}
        if not isinstance(legacy, dict):
            return {"migrated": False, "error": "legacy_settings_invalid"}

        secrets_migrated = True
        for field, credential_name in (
            ("apiKey", CredentialStore.OPENROUTER),
            ("customApiKey", CredentialStore.CUSTOM),
        ):
            value = legacy.get(field)
            if isinstance(value, str) and value.strip():
                try:
                    self.credentials.set(credential_name, value, require_persistence=True)
                except RuntimeError:
                    secrets_migrated = False

        sanitized = {key: value for key, value in legacy.items() if key in SETTINGS_KEYS}
        self._write({**DEFAULT_SETTINGS, **sanitized})
        if secrets_migrated and any(key in legacy for key in ("apiKey", "customApiKey")):
            legacy_path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"migrated": True, "secretsMigrated": secrets_migrated}


def capability_status() -> dict[str, bool]:
    def available(module: str) -> bool:
        try:
            return importlib.util.find_spec(module) is not None
        except Exception:
            return False

    return {
        "pdfText": available("pypdf"),
        "pdfOcr": available("pypdfium2") and available("pytesseract") and available("PIL"),
        "rag": available("chromadb") and available("sentence_transformers"),
        "credentialStore": available("keyring"),
        "encryptedStorage": available("cryptography"),
    }
