"""Testet die OCR-Engine-Abstraktion (Stufe 2 des OCR-Refactors).

Deckt teacherassist_core/ocr/engines/base.py (EngineStatus, EngineError,
OCREngine-Protocol), engines/fake.py (FakeEngine, Zeile 20) und
engines/tesseract.py (TesseractEngine, Zeile 32) ab, sowie die Registry in
engines/__init__.py: build_engines (Zeile 36), available_engines
(Zeile 56) und ocr_capability_status (Zeile 62).

Der wichtigste Vertrag dieses gesamten Moduls ist der Lazy-Import: siehe
engines/__init__.py:1-15 fuer den Wortlaut. test_engines_import_without_
heavy_deps erzwingt das mit einem sys.meta_path-Blocker, der torch,
transformers, pytesseract, PIL, paddle und numpy fuer die Dauer des Tests
so behandelt, als seien sie nicht installiert -- unabhaengig davon, ob sie
im tools/.venv dieser Maschine tatsaechlich installiert sind.
"""

from __future__ import annotations

import importlib
import inspect
import json
import logging
import sys
import urllib.request

import pytest

import teacherassist_core.ocr.engines as engines_module
import teacherassist_core.ocr.engines.ollama_vlm as ollama_vlm_module
from teacherassist_core.ocr.engines import (
    DEFAULT_VISION_MODEL,
    ENGINE_FACTORIES,
    FakeEngine,
    build_engines,
    ocr_capability_status,
)
from teacherassist_core.ocr.engines.base import EngineError
from teacherassist_core.ocr.engines.tesseract import TesseractEngine
from teacherassist_core.ocr.types import RegionType
from teacherassist_core.tesseract_setup import tesseract_binary

from _ocr_module_reload_helpers import restore_purged_modules

BLOCKED_ROOTS = frozenset({"torch", "transformers", "pytesseract", "PIL", "paddle", "numpy"})


class _BlockingFinder:
    """sys.meta_path-Finder, der BLOCKED_ROOTS unauffindbar macht.

    find_spec() muss den Import ablehnen, BEVOR der reguläre PathFinder
    (der die echten, in tools/.venv installierten Pakete faende) an die
    Reihe kommt -- ein Finder, der None zurueckgibt, wuerde die Suche nur
    an den naechsten Finder weiterreichen, nicht blockieren. Raising ist
    hier die korrekte Technik; genau deshalb muss jeder is_available()/
    status()-Aufruf in engines/tesseract.py find_spec() gegen Exceptions
    absichern (siehe tesseract.py:_deps_available), statt sich auf ein
    sauberes None bei "nicht installiert" zu verlassen."""

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".", 1)[0]
        if root in BLOCKED_ROOTS:
            raise ModuleNotFoundError(f"blocked for test: {fullname}")
        return None


def _purge_engines_modules() -> dict:
    removed = {}
    for name in list(sys.modules):
        if name == "teacherassist_core.ocr.engines" or name.startswith("teacherassist_core.ocr.engines."):
            removed[name] = sys.modules.pop(name)
    return removed


def test_engines_import_without_heavy_deps():
    """engines/__init__.py und seine Untermodule (base.py, fake.py,
    tesseract.py) duerfen beim reinen Import keine der schweren
    Abhaengigkeiten anfassen (siehe engines/__init__.py:1-15,
    'LAZY-IMPORT-VERTRAG'). Mit allen fuenf Bibliotheken vom sys.meta_path
    blockiert muss ein frischer Import trotzdem gelingen, und
    available_engines({}) muss eine Statusliste mit available=False und
    einem befuellten reason-String liefern (DEFAULT_ENGINES=("tesseract",),
    also genau ein Eintrag mit reason="not_installed:pytesseract|PIL")."""
    finder = _BlockingFinder()
    sys.meta_path.insert(0, finder)
    saved_modules = _purge_engines_modules()
    try:
        engines_module = importlib.import_module("teacherassist_core.ocr.engines")
        statuses = engines_module.available_engines({})
    finally:
        sys.meta_path.remove(finder)
        _purge_engines_modules()
        restore_purged_modules(saved_modules)

    assert statuses, "available_engines({}) sollte mind. den Default 'tesseract' liefern"
    for status in statuses:
        assert status.available is False
        assert status.reason  # nicht-leerer, maschinenlesbarer Grund


def test_fake_engine_deterministic_and_keyed():
    """FakeEngine (engines/fake.py:20) unterstuetzt drei Formen von `texts`:
    str (immer derselbe Text), Mapping (nachgeschlagen ueber `region_id` --
    dem im OCREngine-Protocol selbst festgeschriebenen Parameter, base.py,
    keine FakeEngine-spezifische Erweiterung) und Sequence (der Reihe nach
    ueber aufeinanderfolgende recognize()-Aufrufe konsumiert, mit
    Wraparound). Alle Aufrufe hier verwenden daher die normale
    Protocol-Signatur -- der Pipeline-Code (Stufe 4/5) ruft jede Engine
    genauso auf, ohne auf FakeEngine vs. echte Engine unterscheiden zu
    muessen. call_count zaehlt jeden Aufruf, unabhaengig von der Form."""
    str_engine = FakeEngine("str-engine", "Hallo Welt")
    c1 = str_engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p1-r1")
    c2 = str_engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p1-r2")
    assert c1.text == c2.text == "Hallo Welt"
    assert str_engine.call_count == 2

    mapping_engine = FakeEngine(
        "map-engine", {"p1-r1": "Erste Zeile", "p1-r2": "Zweite Zeile"}
    )
    m1 = mapping_engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p1-r1")
    m2 = mapping_engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p1-r2")
    assert m1.text == "Erste Zeile"
    assert m2.text == "Zweite Zeile"
    # Wiederholter, identischer Aufruf -> wertgleicher Kandidat (OCRCandidate
    # ist ein frozen dataclass, siehe types.py:41, also Wertgleichheit).
    m1_again = mapping_engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p1-r1")
    assert m1_again == m1
    assert mapping_engine.call_count == 3

    seq_engine = FakeEngine("seq-engine", ["Eins", "Zwei", "Drei"])
    s1 = seq_engine.recognize(None, region_type=RegionType.TEXT_LINE)
    s2 = seq_engine.recognize(None, region_type=RegionType.TEXT_LINE)
    s3 = seq_engine.recognize(None, region_type=RegionType.TEXT_LINE)
    assert (s1.text, s2.text, s3.text) == ("Eins", "Zwei", "Drei")
    assert seq_engine.call_count == 3
    # Wraparound: der vierte Aufruf liefert wieder "Eins".
    s4 = seq_engine.recognize(None, region_type=RegionType.TEXT_LINE)
    assert s4.text == "Eins"


def test_fake_engine_fail_with_raises_engine_error():
    """fail_with (engines/fake.py:38) macht recognize() eine EngineError
    werfen, statt einen leeren/geratenen Kandidaten zurueckzugeben -- der
    Mechanismus, der die Pipeline-Regel testbar macht, dass eine
    fehlgeschlagene HTR-Engine NIE still auf Tesseract zurueckfaellt."""
    engine = FakeEngine("broken", "wird nie verwendet", fail_with="model_not_downloaded:htr-de-v1")

    with pytest.raises(EngineError) as exc_info:
        engine.recognize(None, region_type=RegionType.PARAGRAPH)

    assert exc_info.value.engine == "broken"
    assert exc_info.value.reason == "model_not_downloaded:htr-de-v1"
    assert str(exc_info.value) == "broken: model_not_downloaded:htr-de-v1"
    # Der Aufruf zaehlt trotz Fehlschlag -- "wurde die Engine ueberhaupt
    # aufgerufen" muss unabhaengig vom Ausgang beobachtbar sein.
    assert engine.call_count == 1


def test_fake_engine_parses_markup():
    """FakeEngine.recognize() schickt den Rohtext durch markup.parse_markup
    (engines/fake.py:97), genau wie eine echte Engine: <uncertain>-Varianten
    landen im markers-Feld, <deleted>-Inhalt bleibt in raw_text erhalten
    (Verbatim-Vertrag), fehlt aber im aufgeloesten text-Feld."""
    raw = (
        "Die Kraft <uncertain>ist|ist nicht</uncertain> konstant. "
        "Das ist <deleted>falsch</deleted> richtig."
    )
    engine = FakeEngine("markup-engine", raw)
    candidate = engine.recognize(None, region_type=RegionType.PARAGRAPH)

    assert candidate.raw_text == raw
    assert "uncertain" in candidate.markers
    assert "falsch" not in candidate.text
    assert "ist" in candidate.text  # bevorzugte (erste) Alternative bleibt im Text


def test_tesseract_status_reports_binary_not_found():
    """TesseractEngine.status() (engines/tesseract.py:46) muss zwischen
    "Abhaengigkeiten fehlen" und "Binary nicht gefunden" unterscheiden.
    Statt das Testergebnis an den Zustand DIESER Maschine zu ketten,
    verzweigt der Test ueber tesseract_binary() (tesseract_setup.py:32),
    sodass er sowohl hier (Binary fehlt) als auch auf einer Maschine mit
    installiertem Tesseract gruen bleibt."""
    engine = TesseractEngine()
    status = engine.status()

    if tesseract_binary() is None:
        assert status.available is False
        assert status.reason == "binary_not_found:tesseract"
    else:
        assert status.available is True
        assert status.reason == ""
    assert status.name == "tesseract"
    assert status.kind == "print"


def test_tesseract_accepts_and_ignores_region_id():
    """TesseractEngine.recognize() (engines/tesseract.py:85) muss den
    protocol-weiten `region_id`-Parameter (base.OCREngine.recognize)
    annehmen, obwohl Tesseract selbst keine fachliche Verwendung dafuer
    hat -- die Pipeline (Stufe 4/5) uebergibt ihn an JEDE Engine ohne
    Sonderfaelle. Statt ihn zu ignorieren, haengt tesseract.py ihn an
    Fehlermeldung und Log an (_region_suffix), damit ein Fehlschlag sagt,
    welche Region betroffen war. Auf dieser Maschine ist kein
    Tesseract-Binary vorhanden (siehe
    test_tesseract_status_reports_binary_not_found), daher schlaegt
    recognize() zuverlaessig fehl -- der Test prueft deshalb den
    Fehlerpfad (region_id im Fehlertext), statt eine erfolgreiche
    Erkennung vorauszusetzen, und ueberspringt sich selbst auf einer
    Maschine, auf der Tesseract tatsaechlich verfuegbar ist."""
    engine = TesseractEngine()
    if engine.status().available:
        pytest.skip("Tesseract ist auf dieser Maschine verfuegbar -- kein Fehlschlagpfad zu testen")

    with pytest.raises(EngineError) as exc_info:
        engine.recognize(None, region_type=RegionType.TEXT_LINE, region_id="p3-r7")

    assert "p3-r7" in exc_info.value.reason
    assert "p3-r7" in str(exc_info.value)


def test_all_registered_engines_accept_region_id():
    """Struktureller Signatur-Check statt eines aufrufbasierten Tests, damit
    er auch die drei weiteren Engines abdeckt, die in Stufe 6-8 von anderen
    Agents zu ENGINE_FACTORIES (engines/__init__.py:28) hinzugefuegt
    werden: jede registrierte Engine muss recognize() mit einem
    region_id-Schluesselwortparameter (Default None, siehe
    base.OCREngine.recognize) anbieten, sonst kann die Pipeline sie nicht
    einheitlich ueber das Protocol aufrufen."""
    for name, factory in ENGINE_FACTORIES.items():
        engine = factory({})
        signature = inspect.signature(engine.recognize)
        assert "region_id" in signature.parameters, f"{name}.recognize() fehlt region_id"
        assert signature.parameters["region_id"].default is None


def test_build_engines_returns_unavailable_engines_too(monkeypatch):
    """build_engines() (engines/__init__.py:36) filtert NICHT nach
    Verfuegbarkeit -- die Pipeline muss eine nicht verfuegbare Engine sehen
    koennen, um einen engine_failure-Eintrag zu erzeugen (siehe
    types.PageResult.engine_failures). Registriert dafuer eine garantiert
    nicht verfuegbare FakeEngine unter einem eigenen Namen, statt sich auf
    den (maschinenabhaengigen) Tesseract-Binary-Zustand zu verlassen."""
    monkeypatch.setitem(
        ENGINE_FACTORIES,
        "always-unavailable",
        lambda settings: FakeEngine("always-unavailable", "text", available=False),
    )

    built = build_engines({}, names=["always-unavailable"])

    assert len(built) == 1
    assert built[0].is_available() is False


def _patch_engine_availability(monkeypatch, *, tesseract: bool, htr: bool, vlm: bool) -> None:
    """Ersetzt alle drei von ocr_capability_status() befragten Engine-Quellen
    durch FakeEngine-Instanzen mit fest vorgegebener Verfuegbarkeit --
    deterministisch, ohne echtes Tesseract-Binary, HTR-Modell oder
    Ollama-Netzwerk. TesseractEngine wird als Klassenname im
    engines-Modul selbst ersetzt, weil ocr_capability_status() sie DIREKT
    aufruft (`TesseractEngine()`), nicht ueber ENGINE_FACTORIES; htr und
    ollama_vlm laufen ausschliesslich ueber ENGINE_FACTORIES (das
    ocr_capability_status() tatsaechlich befragt), daher genuegt dort
    monkeypatch.setitem."""
    monkeypatch.setattr(
        engines_module, "TesseractEngine",
        lambda: FakeEngine("tesseract", "x", available=tesseract),
    )
    monkeypatch.setitem(
        ENGINE_FACTORIES, "htr", lambda settings: FakeEngine("htr", "x", available=htr)
    )
    monkeypatch.setitem(
        ENGINE_FACTORIES, "ollama_vlm", lambda settings: FakeEngine("ollama_vlm", "x", available=vlm)
    )


@pytest.mark.parametrize(
    "tesseract, htr, vlm, expected_consensus",
    [
        (True, False, False, False),  # nur 1 verfuegbar -> ocrConsensus False
        (True, True, False, True),  # genau 2 verfuegbar -> ocrConsensus True
        (False, False, False, False),  # keine verfuegbar
        (True, True, True, True),  # alle drei verfuegbar
    ],
    ids=["one_available", "two_available", "none_available", "all_available"],
)
def test_ocr_capability_status_shape_and_contract(monkeypatch, tesseract, htr, vlm, expected_consensus):
    """ocr_capability_status() (engines/__init__.py:62) muss alle fuenf
    vertraglich zugesicherten Schluessel liefern, jeweils als bool, und
    ocrConsensus muss exakt "mindestens zwei der drei befragten Engines
    verfuegbar" widerspiegeln.

    Bewusst NICHT gegen den tatsaechlichen Verfuegbarkeitszustand DIESER
    Maschine getestet (kein Tesseract-Binary noetig, kein Ollama-Dienst
    noetig) -- seit Stufe 7 macht ocrVlm einen echten Netzwerkaufruf
    (OllamaVlmEngine.status() -> /api/tags), sodass ein Test, der
    ungestubbt `ocr_capability_status({})` aufruft, je nachdem, ob auf der
    Entwicklermaschine ein Ollama-Dienst mit gepulltem Modell laeuft oder
    nicht, unterschiedliche Ergebnisse liefert -- genau die Art Test, die
    als "flaky" endet. _patch_engine_availability ersetzt alle drei
    Engine-Quellen durch FakeEngine, wodurch dieser Test auf jeder Maschine
    (mit oder ohne laufendes Ollama) identisch bleibt und ausserdem beide
    Zweige von ocrConsensus (< 2 bzw. >= 2 verfuegbar) deterministisch
    durchlaeuft. Der reale Netzwerkpfad selbst wird separat in
    test_ocr_capability_status_vlm_reflects_stubbed_tags_probe abgedeckt."""
    _patch_engine_availability(monkeypatch, tesseract=tesseract, htr=htr, vlm=vlm)

    status = ocr_capability_status({})

    assert set(status.keys()) == {"ocrTesseract", "ocrHtr", "ocrVlm", "ocrPaddle", "ocrConsensus"}
    assert all(isinstance(value, bool) for value in status.values())
    assert status["ocrTesseract"] is tesseract
    assert status["ocrHtr"] is htr
    assert status["ocrVlm"] is vlm
    assert status["ocrPaddle"] is False
    assert status["ocrConsensus"] is expected_consensus


class _FakeTagsResponse:
    """Minimaler Stand-in fuer das von urllib.request.urlopen() als
    Context-Manager zurueckgegebene Response-Objekt -- identisches Muster
    wie tests/test_ocr_vlm.py::_FakeResponse, hier lokal dupliziert, damit
    dieses Testmodul nicht von test_ocr_vlm.py importiert (keine
    Kopplung zwischen Testdateien)."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeTagsResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def test_ocr_capability_status_vlm_reflects_stubbed_tags_probe(monkeypatch):
    """Deckt den ECHTEN Verdrahtungspfad ab (bewusst KEIN FakeEngine-Ersatz
    hier): ocr_capability_status() ruft die echte
    ENGINE_FACTORIES["ollama_vlm"]-Fabrik und die echte
    OllamaVlmEngine.status()-Kette auf, aber urllib.request.urlopen wird
    In-Prozess gestubbt -- identisches Muster wie
    tests/test_ocr_vlm.py::_StubTransport. Kein Socket, keine Abhaengigkeit
    vom lokalen Ollama-Zustand dieser Maschine. Deckt beide Antworten ab
    (Ollama nicht erreichbar -> ocrVlm False; Ollama antwortet mit dem
    konfigurierten Modell bereits gepullt -> ocrVlm True), damit die Suite
    auf einer Maschine MIT laufendem Ollama (z.B. qwen3-vl gepullt) exakt
    dasselbe Ergebnis liefert wie auf einer Maschine ganz ohne Ollama.
    _tags_cache wird vor und nach jedem Teilschritt geleert (10s-TTL-Cache,
    modul-global, siehe ollama_vlm.py-Docstring) -- sonst wuerde der zweite
    Teilschritt die Antwort des ersten "erben"."""
    ollama_vlm_module._tags_cache.clear()

    def _offline(request, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _offline)
    try:
        status_offline = ocr_capability_status({})
    finally:
        ollama_vlm_module._tags_cache.clear()
    assert status_offline["ocrVlm"] is False

    def _online(request, timeout=None):
        payload = json.dumps({"models": [{"name": DEFAULT_VISION_MODEL}]}).encode("utf-8")
        return _FakeTagsResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", _online)
    try:
        status_online = ocr_capability_status({})
    finally:
        ollama_vlm_module._tags_cache.clear()
    assert status_online["ocrVlm"] is True


def test_unknown_engine_name_is_skipped_not_fatal(caplog):
    """Ein unbekannter Name in settings['ocrEngines'] darf build_engines()
    (engines/__init__.py:36) nie zum Absturz bringen -- er wird geloggt und
    uebersprungen, waehrend bekannte Namen in derselben Liste normal
    gebaut werden."""
    with caplog.at_level(logging.WARNING, logger="teacherassist_core.ocr.engines"):
        built = build_engines({}, names=["tesseract", "nonexistent_engine"])

    assert len(built) == 1
    assert built[0].name == "tesseract"
    assert any("nonexistent_engine" in record.message for record in caplog.records)
