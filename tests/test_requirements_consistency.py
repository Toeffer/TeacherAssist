"""install.bat installs tools/requirements*.txt, repair.bat reinstalls
tools/requirements.lock (pip freeze of a working venv). When the two drift,
a fresh install differs from the repaired one, and two requirement files
pinning different versions of one package (Pillow 11.1.0 vs 12.2.0 once)
cannot be installed together at all."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
PIN = re.compile(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?==([^\s;]+)")


def pins(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN.match(line.split("#", 1)[0].strip())
        if match:
            result[re.sub(r"[-_.]+", "-", match.group(1).lower())] = match.group(2)
    return result


LOCK = pins(TOOLS / "requirements.lock")


def test_every_base_requirement_is_locked_at_the_same_version():
    base = pins(TOOLS / "requirements.txt")

    assert base, "requirements.txt has no pins"
    assert {name: (version, LOCK.get(name)) for name, version in base.items() if LOCK.get(name) != version} == {}


@pytest.mark.parametrize("filename", sorted(path.name for path in TOOLS.glob("requirements-*.txt")))
def test_optional_requirements_agree_with_the_lock(filename):
    """Optional stacks may contain packages the lock lacks (paddle is kept
    out on purpose), but a package present in both must have one version."""
    optional = pins(TOOLS / filename)

    assert {
        name: (version, LOCK[name])
        for name, version in optional.items()
        if name in LOCK and LOCK[name] != version
    } == {}
