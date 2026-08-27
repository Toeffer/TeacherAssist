"""Testet scripts/capability_check.py.

Deckt Bug 1 ab (siehe Auftrag): der Report muss die ECHTE Konfiguration
(settings.json ueber RuntimePaths/SettingsStore, genau wie tool_server.py)
widerspiegeln, nicht stillschweigend DEFAULT_SETTINGS -- inklusive des
Neuinstallations-Falls (kein settings.json), der explizit als solcher
kenntlich gemacht werden muss statt mit dem konfigurierten Fall verwechselt
zu werden.

ALLE Tests hier laufen als Subprozess (echtes TEACHERASSIST_DATA_DIR ueber
die Umgebung, wie RuntimePaths.from_environment es liest) -- das ist der
Vertrag, den ein Supporter beim Ausfuehren dieses Skripts tatsaechlich
sieht, UND es haelt die Test-Suite sauber: capability_check.main() importiert
(fuer REQUIRED/OPTIONAL) echte schwere Abhaengigkeiten wie PIL/pytesseract
per importlib.import_module() -- ein In-Prozess-Aufruf wuerde diese
dauerhaft in sys.modules des Test-Prozesses hinterlassen und damit
tests/test_ocr_engines.py::test_engines_import_without_heavy_deps
(sys.meta_path-Blocker verlaesst sich darauf, dass diese Module NICHT
schon importiert sind) zum Scheitern bringen, je nach Ausfuehrungsreihenfolge.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capability_check.py"

sys.path.insert(0, str(ROOT))
from teacherassist_core.ocr.engines.ollama_vlm import DEFAULT_VISION_MODEL  # noqa: E402


def _run(tmp_path: Path, *, extra_code: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "TEACHERASSIST_DATA_DIR": str(tmp_path)}
    if not extra_code:
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    return subprocess.run(
        [sys.executable, "-c", extra_code],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_reads_real_settings_json(tmp_path):
    """Ein crafted settings.json muss den Report steuern -- nicht
    DEFAULT_SETTINGS (Bug 1)."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"ocrEngines": ["tesseract", "ollama_vlm"], "ocrVisionModel": "qwen3-vl:32b"}),
        encoding="utf-8",
    )

    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert report["settingsSource"] == str(settings_path)
    assert report["engines"]["ollama_vlm"]["modelId"] == "qwen3-vl:32b"
    assert report["engines"]["ollama_vlm"]["enabled"] is True
    assert report["engines"]["tesseract"]["enabled"] is True
    # htr ist nicht in ocrEngines/ocrVerifyEngines konfiguriert, muss aber
    # weiterhin im Bericht auftauchen (Vollstaendigkeit) -- nur als
    # "enabled": False markiert.
    assert report["engines"]["htr"]["enabled"] is False


def test_fresh_install_reports_defaults_and_says_so(tmp_path):
    """Kein settings.json (Neuinstallation) ist ein normaler Zustand: das
    Skript faellt auf DEFAULT_SETTINGS zurueck, MUSS das aber ausdruecklich
    kennzeichnen statt einen Pfad vorzutaeuschen."""
    assert not (tmp_path / "settings.json").exists()

    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert report["settingsSource"] == "defaults (keine settings.json gefunden)"
    assert report["engines"]["ollama_vlm"]["modelId"] == DEFAULT_VISION_MODEL


_MISSING_KEYRING_CODE = f"""
import sys
sys.path.insert(0, r{str(ROOT / "scripts")!r})
import capability_check as cc

real_import_module = cc.importlib.import_module

def fake_import_module(name, *args, **kwargs):
    if name == "keyring":
        raise ImportError("simulated missing dependency")
    return real_import_module(name, *args, **kwargs)

cc.importlib.import_module = fake_import_module
sys.exit(cc.main())
"""


def test_missing_required_capability_exits_1(tmp_path):
    """install.bat haengt an diesem Exit-Code -- muss trotz aller anderen
    Aenderungen exakt so bleiben. Simuliert eine fehlende REQUIRED-
    Abhaengigkeit (keyring) per gefaketem importlib.import_module in einem
    eigenen Subprozess, statt echt zu deinstallieren."""
    result = _run(tmp_path, extra_code=_MISSING_KEYRING_CODE)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "keyring" in result.stderr


def test_required_ok_exits_0(tmp_path):
    """Gegenprobe zu oben: sind alle REQUIRED-Abhaengigkeiten vorhanden
    (wie in dieser Test-Umgebung), bleibt der Exit-Code 0."""
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
