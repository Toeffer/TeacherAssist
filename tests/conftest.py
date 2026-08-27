"""Suite-weite Fixtures/Hilfsfunktionen.

Zwei Dinge leben hier (siehe Auftrag Fix 2 -- "vier Tests machen echte
Netzwerkaufrufe an 127.0.0.1:11434"):

1. ``stub_ollama_vlm_factory()`` -- eine EINZIGE, gemeinsam genutzte
   Hilfsfunktion, die jede ``isolated_server``-Fixture (test_http_api.py,
   test_ocr_http.py, test_ocr_htr.py, test_student_grading_gate.py -- jede
   Datei definiert ihre EIGENE ``isolated_server``-Fixture, es gibt also
   keine einzelne Fixture zum zentral Patchen) am Ende ihres Setups
   aufruft, statt denselben Patch viermal zu kopieren. Sie ersetzt
   ``ENGINE_FACTORIES["ollama_vlm"]`` durch eine ``FakeEngine`` mit
   ``available=False``.

   Grund: ``/api/v1/bootstrap`` ruft ``ocr_capability_status()`` auf, das
   UNBEDINGT ``ENGINE_FACTORIES["ollama_vlm"]`` baut und dessen
   ``.status()`` aufruft -- das macht wiederum einen ECHTEN
   ``urllib.request.urlopen("http://127.0.0.1:11434/api/tags")``
   (engines/ollama_vlm.py). Das bereits vorhandene
   ``monkeypatch.setattr(tool_server, "check_ollama", lambda: False)``
   deckt das NICHT ab -- das ist ein separater Aufruf innerhalb von
   tool_server.py selbst, nicht der von ``ocr_capability_status()``
   unabhaengig angestossene. Gleiche Technik wie bereits in
   tests/test_ocr_htr.py::test_ocr_capability_status_reflects_real_htr_availability
   vorgemacht -- hier nur zentral fuer alle serverstartenden Fixtures
   verfuegbar gemacht.

   BEWUSST NICHT als autouse-Fixture: tests/test_ocr_engines.py::
   test_ocr_capability_status_vlm_reflects_stubbed_tags_probe testet
   GENAU den echten ``ENGINE_FACTORIES["ollama_vlm"]``-Verdrahtungspfad
   (mit gestubbtem ``urllib.request.urlopen`` statt gestubbter Fabrik) --
   ein globaler Ersatz der Fabrik fuer JEDEN Test wuerde diesen Test
   sinnlos machen.

2. ``_forbid_unstubbed_network_calls`` -- eine permanente, autouse
   Absicherung (siehe Auftrag: "make sure this class of bug cannot come
   back"): ersetzt ``urllib.request.urlopen`` FUER JEDEN Test durch eine
   Wache, die den Test sofort und lesbar scheitern laesst, wenn er
   tatsaechlich einen echten Netzwerkaufruf ausloest, statt ihn
   stillschweigend durchzulassen (und damit vom Ollama-Zustand DIESER
   Maschine abhaengig zu machen). Jeder Test, der ``urllib.request.urlopen``
   legitim braucht (tests/test_ocr_vlm.py, tests/test_ocr_engines.py),
   ersetzt es ohnehin selbst per eigenem ``monkeypatch.setattr(...)`` --
   das geschieht im Testkoerper, also NACH dieser Fixture, und ueberschreibt
   die Wache fuer die restliche Testdauer einfach wieder. Kein Konflikt,
   keine Sonderbehandlung noetig.
"""

from __future__ import annotations

import urllib.request

import pytest

from teacherassist_core.ocr.engines import ENGINE_FACTORIES
from teacherassist_core.ocr.engines.fake import FakeEngine


def stub_ollama_vlm_factory(monkeypatch) -> None:
    """Von jeder ``isolated_server``-Fixture aufzurufen, die einen echten
    ToolHandler/HTTP-Server startet und damit potenziell ``/api/v1/bootstrap``
    erreichbar macht (siehe Moduldocstring)."""
    monkeypatch.setitem(
        ENGINE_FACTORIES,
        "ollama_vlm",
        lambda settings: FakeEngine("ollama_vlm", "", available=False),
    )


@pytest.fixture(autouse=True)
def _forbid_unstubbed_network_calls(monkeypatch):
    """Laesst JEDEN Test sofort scheitern, der ``urllib.request.urlopen()``
    fuer einen ECHTEN Netzwerkaufruf erreicht, ohne ihn selbst gestubbt zu
    haben (siehe Moduldocstring Punkt 2)."""

    def _guarded_urlopen(request, *args, **kwargs):
        url = getattr(request, "full_url", None) or str(request)
        pytest.fail(
            "urllib.request.urlopen() wurde fuer einen ECHTEN Netzwerkaufruf an "
            f"{url!r} aufgerufen, ohne dass der Test ihn gestubbt haette -- siehe "
            "tests/conftest.py::_forbid_unstubbed_network_calls. Die Suite darf "
            "nicht vom Zustand eines echten Dienstes auf diesem Rechner (z.B. "
            "Ollama auf 127.0.0.1:11434) abhaengen.",
            pytrace=False,
        )

    monkeypatch.setattr(urllib.request, "urlopen", _guarded_urlopen)
