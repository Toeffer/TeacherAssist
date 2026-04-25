"""
image_receiver.py
=================
OpenClaw Tool – empfängt Base64-kodierte Bilder vom iPhone (gleiches WLAN),
speichert sie temporär, gibt den Pfad für ocr_reader.py zurück.

Aufruf durch OpenClaw:
  python image_receiver.py '{"image_data": "<base64>", "format": "jpeg", "session_id": "uuid"}'

Ausgabe (JSON auf stdout):
  {"success": true, "filepath": "/tmp/openclaw_img_uuid.jpg", "session_id": "uuid"}
"""

import sys
import json
import base64
import os
import tempfile
import uuid
import time
from pathlib import Path


# Maximale Bildgröße: 10 MB (Base64-kodiert ~13 MB)
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# Erlaubte Formate
ALLOWED_FORMATS = {"jpeg", "jpg", "png", "webp", "heic"}

# Temp-Verzeichnis für Bilder (wird nach Auswertung gelöscht)
TEMP_DIR = Path(tempfile.gettempdir()) / "openclaw_images"


def receive_image(args: dict) -> dict:
    """
    Empfängt ein Base64-kodiertes Bild und speichert es temporär.

    Args:
        args (dict):
            image_data (str):   Base64-kodiertes Bild (ohne data:image-Prefix)
            format (str):       Bildformat: "jpeg", "png", "webp", "heic"
            session_id (str):   UUID der Übertragungssession (für Nachverfolgung)
            context (dict):     Optional: fach, klasse, aufgabe (wird mitgeloggt)

    Returns:
        dict:
            success (bool)
            filepath (str):     Absoluter Pfad zur temporären Bilddatei
            session_id (str)
            filesize_kb (int)
            error (str|None)
    """

    # --- Eingabe validieren ---
    image_b64 = args.get("image_data", "")
    image_format = args.get("format", "jpeg").lower().strip(".")
    session_id = args.get("session_id", str(uuid.uuid4()))

    if not image_b64:
        return _error("image_data fehlt oder leer", session_id)

    if image_format not in ALLOWED_FORMATS:
        return _error(
            f"Format '{image_format}' nicht unterstützt. Erlaubt: {ALLOWED_FORMATS}",
            session_id
        )

    # data:image/jpeg;base64,... Prefix entfernen falls vorhanden
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    # --- Base64 dekodieren ---
    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception as e:
        return _error(f"Base64-Dekodierung fehlgeschlagen: {e}", session_id)

    # --- Größe prüfen ---
    if len(image_bytes) > MAX_IMAGE_BYTES:
        size_mb = len(image_bytes) / (1024 * 1024)
        return _error(
            f"Bild zu groß: {size_mb:.1f} MB (Maximum: {MAX_IMAGE_BYTES // (1024*1024)} MB)",
            session_id
        )

    # --- Temp-Verzeichnis erstellen ---
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # --- Datei schreiben ---
    # Dateiname: session_id + Zeitstempel → verhindert Kollisionen
    timestamp = int(time.time())
    filename = f"openclaw_{session_id[:8]}_{timestamp}.{image_format}"
    filepath = TEMP_DIR / filename

    try:
        with open(filepath, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        return _error(f"Konnte Datei nicht schreiben: {e}", session_id)

    filesize_kb = len(image_bytes) // 1024

    return {
        "success": True,
        "filepath": str(filepath),
        "session_id": session_id,
        "filesize_kb": filesize_kb,
        "format": image_format,
        "error": None
    }


def cleanup_image(filepath: str) -> dict:
    """
    Löscht eine temporäre Bilddatei nach der Auswertung.
    DSGVO: Bilder dürfen nicht persistent gespeichert werden.

    Args:
        filepath (str): Absoluter Pfad zur zu löschenden Datei

    Returns:
        dict: {"success": bool, "error": str|None}
    """
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            return {"success": True, "error": None}
        else:
            return {"success": True, "error": None}  # Schon gelöscht = OK
    except Exception as e:
        return {"success": False, "error": str(e)}


def cleanup_old_images(max_age_minutes: int = 30) -> dict:
    """
    Löscht alle temporären Bilder die älter als max_age_minutes sind.
    Wird vom Heartbeat-Skill regelmäßig aufgerufen.
    """
    if not TEMP_DIR.exists():
        return {"success": True, "deleted": 0}

    now = time.time()
    deleted = 0
    errors = []

    for f in TEMP_DIR.glob("openclaw_*.jpg"):
        try:
            age_minutes = (now - f.stat().st_mtime) / 60
            if age_minutes > max_age_minutes:
                f.unlink()
                deleted += 1
        except Exception as e:
            errors.append(str(e))

    return {
        "success": len(errors) == 0,
        "deleted": deleted,
        "errors": errors if errors else None
    }


def _error(message: str, session_id: str = "") -> dict:
    return {
        "success": False,
        "filepath": None,
        "session_id": session_id,
        "filesize_kb": 0,
        "error": message
    }


# --- Einstiegspunkt (OpenClaw ruft als Subprozess auf) ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(_error("Kein Argument übergeben")))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps(_error(f"JSON-Fehler: {e}")))
        sys.exit(1)

    # Action-Routing
    action = args.get("action", "receive")

    if action == "receive":
        result = receive_image(args)
    elif action == "cleanup":
        result = cleanup_image(args.get("filepath", ""))
    elif action == "cleanup_old":
        result = cleanup_old_images(args.get("max_age_minutes", 30))
    else:
        result = _error(f"Unbekannte Action: {action}")

    print(json.dumps(result, ensure_ascii=False))
