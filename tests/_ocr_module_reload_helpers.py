"""Gemeinsamer Helfer fuer Tests, die sys.modules-Eintraege temporaer
purgen (um einen Import unter simuliert fehlenden Abhaengigkeiten neu zu
erzwingen) und anschliessend wiederherstellen.

Verwendet von tests/test_ocr_pipeline.py und tests/test_ocr_engines.py.
Beide Tests folgen demselben Muster: sys.meta_path blockiert bestimmte
schwere Abhaengigkeiten, ein Satz teacherassist_core.ocr[.*]-Module wird aus
sys.modules entfernt, ein frischer Import erzwungen, und danach der
Ausgangszustand wiederhergestellt. Genau diese Wiederherstellung hat einen
nicht offensichtlichen zweiten Schritt, den restore_purged_modules() kapselt
(siehe Docstring dort) -- vormals in tests/test_ocr_pipeline.py als
_restore_ocr_modules() dupliziert, jetzt an einer Stelle.
"""

from __future__ import annotations

import sys


def restore_purged_modules(saved: dict) -> None:
    """Stellt `saved` in sys.modules wieder her UND repariert zusaetzlich
    die Elternpaket-Attribute (z.B. `teacherassist_core.ocr` als Attribut
    von `teacherassist_core`, `teacherassist_core.ocr.engines.htr` als
    Attribut von `teacherassist_core.ocr.engines`).

    `sys.modules.update(saved)` allein reicht NICHT: Pythons Import-System
    setzt das Eltern-Attribut nur beim tatsaechlichen (Neu-)Laden eines
    Submoduls -- ein reiner sys.modules-Cache-Hit tut das nicht (siehe
    importlib._bootstrap._find_and_load). Ohne diese Reparatur bleibt das
    Elternpaket-Attribut nach dem Test verwaist auf die temporaer
    importierte (und danach wieder verworfene) Kopie zeigen, waehrend
    sys.modules bereits wieder das Original enthaelt -- ein spaeteres
    `import teacherassist_core.ocr.engines.htr as m` (das ueber die
    Attributkette, nicht ueber sys.modules aufloest) wuerde dann die
    verwaiste Kopie statt des Originals liefern, wodurch z.B. ein
    monkeypatch.setattr(m, ...) in einem spaeter laufenden Test wirkungslos
    verpufft. Ganz konkret hat genau das
    tests/test_ocr_store.py::test_worker_exception_marks_job_failed_and_
    keeps_executor_alive zum Scheitern gebracht, wenn die gesamte Suite
    lief."""
    sys.modules.update(saved)
    for name, module in saved.items():
        if "." not in name:
            continue
        parent_name, _, child_name = name.rpartition(".")
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, child_name, module)
