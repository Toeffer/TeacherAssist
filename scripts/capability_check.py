from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = ("pypdf", "pypdfium2", "pytesseract", "PIL", "cryptography", "keyring")
OPTIONAL = ("chromadb", "sentence_transformers")


def main() -> int:
    status = {}
    for name in REQUIRED + OPTIONAL:
        try:
            importlib.import_module(name)
            status[name] = "ok"
        except Exception as exc:
            status[name] = f"missing: {type(exc).__name__}"
    print(json.dumps(status, indent=2))
    missing = [name for name in REQUIRED if status[name] != "ok"]
    if missing:
        print("Required capabilities missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
