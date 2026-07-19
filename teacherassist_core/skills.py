"""Validated skill discovery and deterministic context orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .privacy import SENSITIVE_SKILLS


VALID_SKILL_ID = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class Skill:
    skill_id: str
    folder: str
    triggers: tuple[str, ...]
    content: str
    local_required: bool


class SkillRegistry:
    def __init__(self, skills_dir: Path, index_path: Path) -> None:
        self.skills_dir = skills_dir
        self.index_path = index_path
        self._skills = self._load()

    def _load(self) -> dict[str, Skill]:
        try:
            rows = json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            rows = []
        result: dict[str, Skill] = {}
        for row in rows if isinstance(rows, list) else []:
            skill_id = row.get("name", "") if isinstance(row, dict) else ""
            folder = row.get("folder", "") if isinstance(row, dict) else ""
            if not VALID_SKILL_ID.fullmatch(skill_id) or not VALID_SKILL_ID.fullmatch(folder):
                continue
            path = self.skills_dir / folder / "skill.md"
            if not path.is_file():
                continue
            result[skill_id] = Skill(
                skill_id=skill_id,
                folder=folder,
                triggers=tuple(str(item).lower() for item in row.get("triggers", []) if isinstance(item, str)),
                content=path.read_text(encoding="utf-8"),
                local_required=skill_id in SENSITIVE_SKILLS,
            )
        return result

    def get(self, skill_id: str | None) -> Skill | None:
        return self._skills.get(skill_id or "")

    def match(self, text: str) -> Skill | None:
        lowered = (text or "").lower()
        candidates = [
            (len(trigger), skill)
            for skill in self._skills.values()
            for trigger in skill.triggers
            if trigger and trigger in lowered
        ]
        return max(candidates, key=lambda item: item[0])[1] if candidates else None

    def companion_prompt(self) -> str:
        skill = self._skills.get("begleiter")
        return skill.content if skill else ""

    def public_index(self) -> list[dict[str, object]]:
        return [
            {
                "id": skill.skill_id,
                "triggers": list(skill.triggers),
                "localRequired": skill.local_required,
            }
            for skill in self._skills.values()
            if skill.skill_id != "begleiter"
        ]
