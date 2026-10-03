"""web_dist/ is committed and served in preference to the sources, and end
users never build it themselves (see CLAUDE.md, "Frontend"). A change to
app.jsx without `npm run build` therefore ships a stale UI. The build writes
a fingerprint of its inputs (scripts/build-stamp.mjs); this test recomputes
it with the same rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "scripts" / "web-dist-inputs.json").read_text(encoding="utf-8"))
STAMP = ROOT / "web_dist" / "build-stamp.json"


def current_sources() -> list[str]:
    sources = list(CONFIG["files"])
    for directory in CONFIG["directories"]:
        sources.extend(
            path.relative_to(ROOT).as_posix() for path in (ROOT / directory).rglob("*") if path.is_file()
        )
    return sorted(sources)


def fingerprint(sources: list[str]) -> str:
    overall = hashlib.sha256()
    for source in sources:
        content = (ROOT / source).read_bytes()
        if (ROOT / source).suffix.lower() not in CONFIG["binaryExtensions"]:
            content = content.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
        overall.update(f"{source}\n{hashlib.sha256(content).hexdigest()}\n".encode("utf-8"))
    return overall.hexdigest()


def test_web_dist_was_built_from_the_current_sources():
    assert STAMP.is_file(), "web_dist/build-stamp.json fehlt: `npm run build` ausführen und web_dist/ committen."
    stamp = json.loads(STAMP.read_text(encoding="utf-8"))
    sources = current_sources()

    assert stamp["sources"] == sources, "Die Liste der Frontend-Quellen hat sich geändert: `npm run build` ausführen."
    assert stamp["fingerprint"] == fingerprint(sources), (
        "web_dist/ ist älter als die Frontend-Quellen: `npm run build` ausführen und web_dist/ committen."
    )


def test_every_frontend_source_is_fingerprinted():
    """A new top-level .jsx file the app loads must be added to
    scripts/web-dist-inputs.json, or changes to it would go unnoticed."""
    listed = set(CONFIG["files"])
    top_level = {path.name for path in ROOT.glob("*.jsx")}
    assert top_level <= listed
