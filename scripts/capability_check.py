from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from teacherassist_core import tesseract_setup  # noqa: E402
from teacherassist_core.ocr.engines import ENGINE_FACTORIES, build_engines  # noqa: E402
from teacherassist_core.runtime import CredentialStore, RuntimePaths, SettingsStore  # noqa: E402

REQUIRED = ("pypdf", "pypdfium2", "pytesseract", "PIL", "cryptography", "keyring")
OPTIONAL = ("chromadb", "sentence_transformers", "torch", "transformers")
OPTIONAL_BINARIES = ("tesseract",)


def main() -> int:
    status = {}
    for name in REQUIRED + OPTIONAL:
        try:
            importlib.import_module(name)
            status[name] = "ok"
        except Exception as exc:
            status[name] = f"missing: {type(exc).__name__}"

    binaries = {}
    for name in OPTIONAL_BINARIES:
        binaries[name] = "ok" if tesseract_setup.tesseract_binary() else "missing"
    status["binaries"] = binaries

    # Dieselben Bausteine wie tool_server.py (RuntimePaths.from_environment
    # -> SettingsStore(...).load()) statt einer leeren {} -- ein leeres
    # Mapping liess build_engines() bisher stillschweigend auf
    # DEFAULT_SETTINGS zurueckfallen, sodass dieser Report z.B. "qwen3-vl:8b"
    # zeigte, obwohl die Lehrkraft laengst "qwen3-vl:32b" konfiguriert hatte
    # (siehe Auftrag "Bug 1"). Ein fehlendes settings.json (Neuinstallation)
    # ist dabei ein normaler Zustand -- SettingsStore.load() faengt das
    # selbst ab und liefert DEFAULT_SETTINGS zurueck, OHNE das nach aussen
    # kenntlich zu machen; deshalb pruefen wir hier zusaetzlich, ob die Datei
    # tatsaechlich existiert, und tragen das explizit in den Report ein,
    # statt Default- und echte Werte fuer den Leser ununterscheidbar zu
    # machen.
    runtime_paths = RuntimePaths.from_environment(ROOT)
    settings_store = SettingsStore(runtime_paths.settings, CredentialStore())
    settings = settings_store.load()
    if runtime_paths.settings.exists():
        status["settingsSource"] = str(runtime_paths.settings)
    else:
        status["settingsSource"] = "defaults (keine settings.json gefunden)"

    # "enabled" = tatsaechlich in ocrEngines/ocrVerifyEngines konfiguriert
    # (siehe build_engines()/ENGINE_FACTORIES-Aufrufstellen in
    # tool_server.py) -- alle anderen registrierten Engines erscheinen
    # weiterhin (Engine-Status-Bericht wie zuvor, siehe untenstehender
    # Kommentar zu ENGINE_FACTORIES), aber ausdruecklich als nicht
    # eingeschaltet markiert, damit ein Bericht sowohl "was ist an" als auch
    # "was koennte an sein" zeigt.
    enabled_names = set(settings.get("ocrEngines") or []) | set(settings.get("ocrVerifyEngines") or [])

    # Engine-Status fuer ALLE registrierten Engines (nicht nur DEFAULT_ENGINES
    # -- htr ist bewusst nicht default, siehe engines/__init__.py), damit
    # torch/transformers-Verfuegbarkeit UND (fuer htr) ob die Modellgewichte
    # bereits im HF-Cache liegen sichtbar sind. "fake" ist keine echte
    # Capability und wird ausgeschlossen. Rein informativ -- geht NICHT in
    # den REQUIRED-Exit-Code ein (install.bat haengt nur an dem).
    engine_names = [name for name in ENGINE_FACTORIES if name != "fake"]
    status["engines"] = {
        engine.name: {**engine.status().to_dict(), "enabled": engine.name in enabled_names}
        for engine in build_engines(settings, names=engine_names)
    }

    print(json.dumps(status, indent=2))
    missing = [name for name in REQUIRED if status[name] != "ok"]
    if missing:
        print("Required capabilities missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
