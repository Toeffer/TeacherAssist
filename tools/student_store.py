#!/usr/bin/env python3
"""
Student Store für TeacherAssist – DSGVO-konformer, lokal verschlüsselter
Speicher für Schülerdaten.

Architektur:
    memory/students/
        .vault.json            Klartext: KDF-Params + Verifier-Ciphertext
        index.enc              Fernet-Blob: Liste {id, alias, klasse, vorname, nachname}
        records/<uuid>.enc     Fernet-Blob: voller Schülerdatensatz (JSON)
        records/<uuid>.enc.bak1/2/3

KDF: Argon2id (argon2-cffi) mit Fallback PBKDF2-SHA256/600k.
Cipher: Fernet (AES-128-CBC + HMAC-SHA256).
Schlüssel liegt nur im RAM (`_session`) und wird beim Lock per
bytearray-Überschreibung gelöscht. Idle-Timeout = 15 min (default).
"""

import base64
import csv
import io
import json
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    from argon2.low_level import Type as _Argon2Type, hash_secret_raw as _argon2_hash
    _HAS_ARGON2 = True
except ImportError:
    _HAS_ARGON2 = False


SCHEMA_VERSION = 1
DEFAULT_IDLE_S = 15 * 60

# Argon2id (OWASP empfohlen 2024+ für interaktive Auth)
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 64 * 1024
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32

# PBKDF2-Fallback
PBKDF2_ITERATIONS = 600_000
PBKDF2_HASH_LEN = 32

_VERIFIER_PLAINTEXT = b"TeacherAssist student vault v1"

_lock = threading.RLock()
_session = {
    "fernet": None,
    "key_buf": None,
    "last_touch": 0.0,
    "idle_s": DEFAULT_IDLE_S,
}

_root_override: Optional[Path] = None


def set_root_override(path: Optional[Path]) -> None:
    """Nur für Tests: lenkt den Vault auf ein anderes Verzeichnis um."""
    global _root_override
    _root_override = path


def _vault_root() -> Path:
    if _root_override is not None:
        root = _root_override
    else:
        root = Path(__file__).resolve().parents[1] / "memory" / "students"
    root.mkdir(parents=True, exist_ok=True)
    (root / "records").mkdir(parents=True, exist_ok=True)
    return root


def _vault_meta() -> Path:
    return _vault_root() / ".vault.json"


def _index_path() -> Path:
    return _vault_root() / "index.enc"


def _record_path(student_id: str) -> Path:
    return _vault_root() / "records" / f"{student_id}.enc"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _derive_key(password: str, salt: bytes, kdf: str, params: dict) -> bytes:
    """Leitet einen Fernet-Schlüssel ab (32 Byte raw → url-safe base64)."""
    if kdf == "argon2id":
        if not _HAS_ARGON2:
            raise RuntimeError("Vault wurde mit Argon2id erstellt, aber argon2-cffi ist nicht installiert.")
        raw = _argon2_hash(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=params["time_cost"],
            memory_cost=params["memory_cost"],
            parallelism=params["parallelism"],
            hash_len=params["hash_len"],
            type=_Argon2Type.ID,
        )
        return base64.urlsafe_b64encode(raw)
    if kdf == "pbkdf2-sha256":
        kdf_fn = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=params["hash_len"],
            salt=salt,
            iterations=params["iterations"],
        )
        return base64.urlsafe_b64encode(kdf_fn.derive(password.encode("utf-8")))
    raise ValueError(f"Unbekannte KDF: {kdf}")


# ---------------------------------------------------------------------------
# Setup / Unlock / Lock
# ---------------------------------------------------------------------------

def is_setup() -> bool:
    return _vault_meta().exists()


def setup_master(password: str) -> None:
    """Initiale Master-Passwort-Vergabe. Wirft Fehler, wenn Vault existiert."""
    if not password or len(password) < 8:
        raise ValueError("Passwort muss mindestens 8 Zeichen lang sein.")
    if is_setup():
        raise RuntimeError("Vault wurde bereits eingerichtet.")

    salt = os.urandom(16)
    if _HAS_ARGON2:
        kdf = "argon2id"
        params = {
            "time_cost": ARGON2_TIME_COST,
            "memory_cost": ARGON2_MEMORY_COST,
            "parallelism": ARGON2_PARALLELISM,
            "hash_len": ARGON2_HASH_LEN,
        }
    else:
        kdf = "pbkdf2-sha256"
        params = {"iterations": PBKDF2_ITERATIONS, "hash_len": PBKDF2_HASH_LEN}

    key = _derive_key(password, salt, kdf, params)
    fernet = Fernet(key)
    verifier_ct = fernet.encrypt(_VERIFIER_PLAINTEXT)

    meta = {
        "schema_version": SCHEMA_VERSION,
        "kdf": kdf,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "params": params,
        "verifier_b64": base64.b64encode(verifier_ct).decode("ascii"),
        "created_at": _now_iso(),
    }
    _vault_meta().write_text(json.dumps(meta, indent=2), encoding="utf-8")

    empty_index = {"students": [], "updated_at": _now_iso()}
    _write_encrypted(_index_path(), empty_index, fernet)

    with _lock:
        _wipe_key()
        _session["fernet"] = fernet
        _session["key_buf"] = bytearray(key)
        _session["last_touch"] = time.time()


def unlock(password: str) -> bool:
    """Entsperrt den Vault. Gibt True bei Erfolg zurück, False bei falschem Passwort."""
    if not is_setup():
        raise RuntimeError("Vault wurde noch nicht eingerichtet.")
    meta = json.loads(_vault_meta().read_text(encoding="utf-8"))
    salt = base64.b64decode(meta["salt_b64"])
    verifier_ct = base64.b64decode(meta["verifier_b64"])

    key = _derive_key(password, salt, meta["kdf"], meta["params"])
    fernet = Fernet(key)
    try:
        if fernet.decrypt(verifier_ct) != _VERIFIER_PLAINTEXT:
            return False
    except InvalidToken:
        return False

    with _lock:
        _wipe_key()
        _session["fernet"] = fernet
        _session["key_buf"] = bytearray(key)
        _session["last_touch"] = time.time()
    return True


def lock() -> None:
    with _lock:
        _wipe_key()


def _wipe_key() -> None:
    buf = _session.get("key_buf")
    if buf is not None:
        for i in range(len(buf)):
            buf[i] = 0
    _session["fernet"] = None
    _session["key_buf"] = None
    _session["last_touch"] = 0.0


def is_unlocked() -> bool:
    """True, wenn Tresor offen UND Idle-Timeout nicht überschritten ist."""
    with _lock:
        if _session.get("fernet") is None:
            return False
        if (time.time() - _session.get("last_touch", 0.0)) > _session.get("idle_s", DEFAULT_IDLE_S):
            _wipe_key()
            return False
        return True


def touch() -> None:
    with _lock:
        if _session.get("fernet") is not None:
            _session["last_touch"] = time.time()


def get_idle_remaining() -> int:
    with _lock:
        if _session.get("fernet") is None:
            return 0
        remaining = _session.get("idle_s", DEFAULT_IDLE_S) - (time.time() - _session.get("last_touch", 0.0))
        return max(0, int(remaining))


def set_idle_timeout(seconds: int) -> None:
    with _lock:
        _session["idle_s"] = max(60, int(seconds))


def _require_unlocked() -> Fernet:
    if not is_unlocked():
        raise RuntimeError("Vault ist gesperrt.")
    touch()
    return _session["fernet"]


# ---------------------------------------------------------------------------
# Verschlüsselte I/O
# ---------------------------------------------------------------------------

def _rotate_backups(filepath: Path) -> None:
    if not filepath.exists():
        return
    bak1 = Path(str(filepath) + ".bak1")
    bak2 = Path(str(filepath) + ".bak2")
    bak3 = Path(str(filepath) + ".bak3")
    if bak2.exists():
        shutil.copy2(str(bak2), str(bak3))
    if bak1.exists():
        shutil.copy2(str(bak1), str(bak2))
    shutil.copy2(str(filepath), str(bak1))


def _read_encrypted(filepath: Path, fernet: Fernet) -> dict:
    return json.loads(fernet.decrypt(filepath.read_bytes()).decode("utf-8"))


def _write_encrypted(filepath: Path, data: dict, fernet: Fernet) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if filepath.exists():
        _rotate_backups(filepath)
    ct = fernet.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    filepath.write_bytes(ct)


def _load_index(fernet: Fernet) -> dict:
    return _read_encrypted(_index_path(), fernet)


def _save_index(index: dict, fernet: Fernet) -> None:
    index["updated_at"] = _now_iso()
    _write_encrypted(_index_path(), index, fernet)


# ---------------------------------------------------------------------------
# Öffentliche API – Schüler:innen
# ---------------------------------------------------------------------------

def list_students(klasse: Optional[str] = None) -> list:
    """Listet Schüler:innen aus dem Index. Optional gefiltert nach Klasse."""
    fernet = _require_unlocked()
    with _lock:
        index = _load_index(fernet)
        return [s for s in index.get("students", []) if not klasse or s.get("klasse") == klasse]


def add_student(identity: dict, klasse: str) -> str:
    """Legt neue Schüler:in an. identity: {vorname, nachname, pronomen, [alias]}."""
    if not identity.get("vorname") or not identity.get("nachname"):
        raise ValueError("Vorname und Nachname sind erforderlich.")
    if not klasse:
        raise ValueError("Klasse ist erforderlich.")

    fernet = _require_unlocked()
    with _lock:
        index = _load_index(fernet)
        existing_aliases = {s.get("alias") for s in index.get("students", [])}
        alias = identity.get("alias")
        if not alias:
            n = len(index.get("students", [])) + 1
            while True:
                alias = f"SuS-{n:02d}"
                if alias not in existing_aliases:
                    break
                n += 1

        student_id = str(uuid.uuid4())
        now = _now_iso()
        record = {
            "id": student_id,
            "schema_version": SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "identity": {
                "vorname": identity["vorname"].strip(),
                "nachname": identity["nachname"].strip(),
                "pronomen": (identity.get("pronomen") or "sie").strip(),
                "alias": alias,
            },
            "klasse": klasse,
            "schulform": identity.get("schulform", ""),
            "competencies": {},
            "observations": [],
            "retention": {"created_at": now, "review_after": None},
        }
        _write_encrypted(_record_path(student_id), record, fernet)

        index.setdefault("students", []).append({
            "id": student_id,
            "alias": alias,
            "klasse": klasse,
            "vorname": record["identity"]["vorname"],
            "nachname": record["identity"]["nachname"],
        })
        _save_index(index, fernet)
        return student_id


def get_student(student_id: str) -> dict:
    fernet = _require_unlocked()
    path = _record_path(student_id)
    if not path.exists():
        raise KeyError(f"Schüler:in {student_id} nicht gefunden.")
    return _read_encrypted(path, fernet)


def update_student(student_id: str, patch: dict) -> dict:
    fernet = _require_unlocked()
    with _lock:
        record = get_student(student_id)
        if "identity" in patch:
            record["identity"].update(patch["identity"])
        if "klasse" in patch:
            record["klasse"] = patch["klasse"]
        if "schulform" in patch:
            record["schulform"] = patch["schulform"]
        record["updated_at"] = _now_iso()
        _write_encrypted(_record_path(student_id), record, fernet)

        index = _load_index(fernet)
        for entry in index.get("students", []):
            if entry["id"] == student_id:
                entry["alias"] = record["identity"]["alias"]
                entry["klasse"] = record["klasse"]
                entry["vorname"] = record["identity"]["vorname"]
                entry["nachname"] = record["identity"]["nachname"]
                break
        _save_index(index, fernet)
        return record


def delete_student(student_id: str) -> None:
    """GDPR Art. 17 – löscht Datensatz inkl. Backups und Index-Eintrag."""
    fernet = _require_unlocked()
    with _lock:
        path = _record_path(student_id)
        for suffix in ("", ".bak1", ".bak2", ".bak3"):
            f = Path(str(path) + suffix)
            if f.exists():
                f.unlink()
        index = _load_index(fernet)
        index["students"] = [s for s in index.get("students", []) if s["id"] != student_id]
        _save_index(index, fernet)


def add_observation(student_id: str, date: str, subject: str, text: str, tags: Optional[list] = None) -> str:
    fernet = _require_unlocked()
    with _lock:
        record = get_student(student_id)
        obs_id = str(uuid.uuid4())
        record.setdefault("observations", []).append({
            "id": obs_id,
            "date": date or _now_iso()[:10],
            "subject": subject,
            "text": text,
            "tags": tags or [],
        })
        record["updated_at"] = _now_iso()
        _write_encrypted(_record_path(student_id), record, fernet)
        return obs_id


def set_competency(student_id: str, subject: str, competency: str, rating, scale: str = "1-4", note: str = "") -> None:
    fernet = _require_unlocked()
    with _lock:
        record = get_student(student_id)
        record.setdefault("competencies", {}).setdefault(subject, {})[competency] = {
            "rating": rating,
            "scale": scale,
            "last_update": _now_iso(),
            "note": note,
        }
        record["updated_at"] = _now_iso()
        _write_encrypted(_record_path(student_id), record, fernet)


def export_student_json(student_id: str) -> dict:
    """GDPR Art. 15 – gibt den vollständigen entschlüsselten Datensatz zurück."""
    return get_student(student_id)


def import_class_csv(csv_text: str, klasse: str) -> int:
    """Importiert Klassenliste. Header (Semikolon-getrennt): vorname;nachname;pronomen."""
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    if not reader.fieldnames:
        raise ValueError("CSV ist leer oder hat keinen Header.")
    field_map = {f.lower().strip(): f for f in reader.fieldnames}
    if "vorname" not in field_map or "nachname" not in field_map:
        raise ValueError("CSV-Header muss 'vorname' und 'nachname' enthalten.")
    v_key = field_map["vorname"]
    n_key = field_map["nachname"]
    p_key = field_map.get("pronomen")

    count = 0
    for row in reader:
        vorname = (row.get(v_key) or "").strip()
        nachname = (row.get(n_key) or "").strip()
        if not vorname or not nachname:
            continue
        identity = {"vorname": vorname, "nachname": nachname}
        if p_key:
            identity["pronomen"] = (row.get(p_key) or "").strip()
        add_student(identity, klasse)
        count += 1
    return count
