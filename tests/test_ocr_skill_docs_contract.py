"""Contract tests for Stufe 10 (the grading skill's transcription step, plus docs).

Two independent contracts are covered here:

1. ``skills/schuelerarbeit_bewerten/skill.md`` must contain the new Schritt 2a
   section with the four uncertainty-marker forms the model needs to
   recognize, and the skill must still load/validate through
   ``teacherassist_core.skills.SkillRegistry`` (source-text idiom established
   in tests/test_http_api.py, e.g. test_tool_server_still_defines_the_versioned_health_route:
   read the file as text, assert the literal substrings are present).
2. CLAUDE.md's HTTP-API-Referenz table must list every OCR route
   tool_server.py actually defines. The expected route set is derived
   directly from tool_server.py's own regex objects (OCR_JOB_RE/OCR_PAGE_RE/
   OCR_REGION_RE/OCR_APPROVE_RE) and its literal route-dict keys -- not from
   a second, hand-maintained list of OCR paths -- so the table cannot
   silently drift from the real routing code.
"""

from __future__ import annotations

import re
from pathlib import Path

import tool_server
from teacherassist_core.skills import SkillRegistry

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "skills" / "schuelerarbeit_bewerten" / "skill.md"


def test_skill_md_contains_schritt_2a_and_marker_forms():
    text = SKILL_MD.read_text(encoding="utf-8")

    assert "Schritt 2a" in text

    for marker in ("[wort?]", "[+wort?]", "[a|b?]", "␣?␣"):
        assert marker in text, f"Schritt 2a is missing the marker form {marker!r}"


def test_skill_md_still_loads_and_validates_through_skill_registry():
    registry = SkillRegistry(tool_server.SKILLS_DIR, tool_server.SKILLS_INDEX)

    skill = registry.get("schuelerarbeit_bewerten")

    assert skill is not None
    assert skill.folder == "schuelerarbeit_bewerten"
    assert "Schritt 2a" in skill.content


def _placeholder_path(pattern: str, names: list[str]) -> str:
    """Turn a compiled regex's ``.pattern`` into a readable route template by
    replacing each capture group, in order, with a ``{name}`` placeholder and
    stripping the ``^``/``$`` anchors."""
    path = pattern
    if path.startswith("^"):
        path = path[1:]
    if path.endswith("$"):
        path = path[:-1]
    for name in names:
        path = re.sub(r"\([^)]*\)", "{" + name + "}", path, count=1)
    return path


def _ocr_routes_from_source() -> set[str]:
    routes = {
        _placeholder_path(tool_server.OCR_JOB_RE.pattern, ["id"]),
        _placeholder_path(tool_server.OCR_PAGE_RE.pattern, ["id", "n"]),
        _placeholder_path(tool_server.OCR_REGION_RE.pattern, ["id", "regionId"]),
        _placeholder_path(tool_server.OCR_APPROVE_RE.pattern, ["id"]),
    }

    # Literal (non-regex) OCR routes: confirm they still exist as route-dict
    # keys / inline comparisons in tool_server.py's own source before adding
    # them to the expected set, so a rename here fails loudly instead of
    # silently checking for a route that no longer exists.
    source = Path(tool_server.__file__).read_text(encoding="utf-8")
    literals = ('/api/v1/ocr/jobs', '/api/v1/ocr/models/download', '/api/v1/ocr-image')
    for literal in literals:
        assert f'"{literal}"' in source, (
            f"{literal!r} is no longer a literal route in tool_server.py -- "
            "update this test's expectations alongside the CLAUDE.md table"
        )
    routes.update(literals)

    return routes


def test_claude_md_endpoint_table_lists_all_ocr_routes():
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    for route in _ocr_routes_from_source():
        assert route in claude_md, f"CLAUDE.md endpoint table is missing OCR route: {route}"
