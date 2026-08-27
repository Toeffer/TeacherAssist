from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from teacherassist_core import tesseract_setup  # noqa: E402
from teacherassist_core.ocr.engines import ENGINE_FACTORIES, build_engines  # noqa: E402

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

    # Engine-Status fuer ALLE registrierten Engines (nicht nur DEFAULT_ENGINES
    # -- htr ist bewusst nicht default, siehe engines/__init__.py), damit
    # torch/transformers-Verfuegbarkeit UND (fuer htr) ob die Modellgewichte
    # bereits im HF-Cache liegen sichtbar sind. "fake" ist keine echte
    # Capability und wird ausgeschlossen. Rein informativ -- geht NICHT in
    # den REQUIRED-Exit-Code ein (install.bat haengt nur an dem).
    engine_names = [name for name in ENGINE_FACTORIES if name != "fake"]
    status["engines"] = {
        engine.name: engine.status().to_dict()
        for engine in build_engines({}, names=engine_names)
    }

    print(json.dumps(status, indent=2))
    missing = [name for name in REQUIRED if status[name] != "ok"]
    if missing:
        print("Required capabilities missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
