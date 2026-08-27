"""Ollama-Vision-Engine: zweiter, unabhaengiger Leser ueber ein lokales VLM
(Stufe 7 des OCR-Refactors).

Schwere Importe (PIL fuer die Bildkodierung) bleiben ausschliesslich
innerhalb von Methoden -- siehe engines/__init__.py fuer den Lazy-Import-
Vertrag dieses Pakets. urllib.request/json sind Standardbibliothek und
duerfen wie in htr.py/tesseract.py auf Modulebene stehen; is_available()
prueft nur ueber importlib.util.find_spec (PIL), status() nur ueber einen
GET auf /api/tags (kein echter Modell-Request, kein Pull).

BUG 2 (der gefaehrlichste im urspruenglichen Code): Die alte _ocr_image-
Implementierung liess bei fehlendem "vision_model"-Setting Folgendes zu:
``vision_model = settings.get("ollamaModel", <Default-Textmodell-Name>)``
-- derselbe Default-Modellname, der in tool_server.py als Fallback fuer
normale LLM-Chatanfragen dient (siehe stream_llm), ist dort bewusst NICHT
als Literal wiederholt, damit ein Quell-Vertrag-Test (test_ocr_vlm.py::
test_no_text_model_fallback_literal_in_engines_source) garantieren kann,
dass er in diesem Paket nirgends mehr als Fallback landet. Es ist ein
reines TEXT-Modell: mit ``images: [...]`` aufgerufen, ignoriert Ollama das
Bild stillschweigend und das Modell erfindet fluessige, plausible deutsche
Prosa -- die dann direkt in die Bewertung einer Schuelerarbeit floss. Eine
halluzinierte Antwort, die als Schuelerleistung bewertet wird, ist das
schlimmstmoegliche Ergebnis dieses Systems, UND sie scheitert lautlos (kein
Fehler, kein Log, nur falscher Text).

Deshalb gilt hier ausnahmslos: ``_resolve_vision_model()`` liefert NUR einen
Modellnamen, der nachweislich (a) in ``/api/tags`` vorhanden ist UND (b) zu
einem der bekannten Vision-Praefixe passt. Gibt es keinen solchen Namen,
wird ``EngineError(self.name, f"model_not_pulled:{self.model_id}")``
geworfen -- NIE ein Fallback auf irgendein anderes, in ``/api/tags``
vorhandenes Modell, das kein Vision-Praefix traegt. Wer hier je "der Job
soll doch nicht ganz scheitern, nimm irgendein Modell" als Fallback
einbaut, reproduziert exakt den oben beschriebenen Bug -- bitte nicht.

GEMESSENE LAUFZEIT (siehe Auftrag "measured constraint, not a preference"):
gegen eine laufende lokale Ollama-Instanz (``qwen3-vl:latest``, reine
CPU-Inferenz) gemessen:

  | Eingabe                        | Ausgabe    | Wandzeit                |
  |---------------------------------|-----------|--------------------------|
  | eine Zeile, 2800x360 px         | ~40 Zeichen | 90.6 s (korrekt, inkl.
  |                                 |             | Negation/Vorzeichen/Komma) |
  | 8 Zeilen, 3200x1560 px          | ~350 Zeichen | Timeout bei 540 s        |
  | dieselben 8 Zeilen, auf 1024 px | ~350 Zeichen | Timeout bei 420 s        |
  |   herunterskaliert              |             |                          |

Herunterskalieren half NICHT -- die Kosten haengen an der Laenge der
autoregressiv erzeugten Ausgabe, nicht an der Eingabe-Pixelzahl (diese
Ollama-Instanz rechnet auf CPU im Bereich von Sekunden pro Token). Daraus
folgt direkt zweierlei:
  1. Diese Engine ist als Massenleser ueber jede Region einer Seite
     unbrauchbar (20-30 Regionen x ~90 s waeren 30-45 Minuten pro Seite,
     ein 25-Arbeiten-Klassensatz waere unbedienbar) -- siehe pipeline.py's
     `verify_engines`/`_region_needs_verification`: diese Engine gehoert
     dorthin, nicht in die Bulk-Engine-Liste jeder Region.
  2. `timeout_s` MUSS deutlich ueber der Ein-Zeilen-Messung (90.6 s)
     liegen -- der alte Default von 120 s liess dafuer praktisch keine
     Marge. Der neue Default (siehe DEFAULT_TIMEOUT_S) ist bewusst
     grosszuegiger bemessen und ueber die Einstellung `ocrVlmTimeoutS`
     konfigurierbar (siehe runtime.py SETTINGS_KEYS/DEFAULT_SETTINGS).

PRIVACY: ``recognize()``s allererste Anweisung ist
``assert_local_only(self.classification, self.endpoint, engine=self.name)``
(siehe privacy_guard.py). ``CloudBlocked`` wird hier NIE abgefangen und NIE
in einen ``EngineError`` umgewandelt -- ein nicht-lokal konfigurierter
Endpunkt muss den Job stoppen, nicht ihn stillschweigend degradieren.

TRANSPORT: Dieses Modul sendet primaer ueber den OpenAI-kompatiblen Pfad
``POST {endpoint}/v1/chat/completions`` mit einer ``data:``-URI im
``image_url``-Feld -- das ist derselbe Transport, den tool_server.py fuer
JEDEN anderen Ollama-Aufruf bereits verwendet (siehe stream_llm ~:627 und
_summarize_messages ~:2036/2059: beide sprechen ausschliesslich
``/v1/chat/completions``, nie ``/api/generate``). Ollamas eigene
OpenAI-Kompatibilitaetsdokumentation (ollama/docs/openai.md, Abschnitt
"Vision") zeigt exakt dieses Muster (``image_url.url`` als
``data:image/...;base64,...``) als unterstuetzten Weg fuer Vision-Modelle.
DIES IST ABER NICHT gegen eine laufende Ollama-Instanz verifiziert worden
(siehe Bericht des implementierenden Agents) -- deshalb existiert
``_TRANSPORT_NATIVE_GENERATE`` als dokumentierter, ueber die
Modulkonstante ``_ACTIVE_TRANSPORT`` umschaltbarer Fallback auf
``POST {endpoint}/api/generate`` mit ``images: [b64]``, falls sich der
OpenAI-kompatible Pfad fuer ein konkretes Vision-Modell als unzuverlaessig
herausstellt.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import threading
import time
import urllib.request
from typing import Any, Mapping, Sequence

from ..consensus import tokenize
from ..markup import parse_markup
from ..privacy_guard import assert_local_only
from ..prompts import FORMULA_PROMPT_DE, VERBATIM_PROMPT_DE
from ..types import OCRCandidate, RegionType
from .base import EngineError, EngineKind, EngineStatus

logger = logging.getLogger(__name__)

VISION_MODEL_PREFIXES = (
    "qwen3-vl", "qwen2.5-vl", "granite3.2-vision",
    "minicpm-v", "llama3.2-vision", "llava", "bakllava", "moondream",
)
DEFAULT_VISION_MODEL = "qwen3-vl:8b"

# Siehe Moduldoc "GEMESSENE LAUFZEIT": eine einzelne Zeile brauchte 90.6 s
# auf gemessener CPU-Inferenz. Der alte Default von 120 s liess dafuer kaum
# Marge; 240 s geben einer Region in Zeilen-/Absatzgroesse auf vergleichbar
# langsamer Hardware realistischen Spielraum, ohne einen haengenden Worker
# unbegrenzt lange zu blockieren. Ueber die Einstellung `ocrVlmTimeoutS`
# konfigurierbar (siehe runtime.py).
DEFAULT_TIMEOUT_S = 240

# Deckelt die Generation, damit ein degenerierter Wiederholungs-Loop des
# Modells keinen Worker-Thread aufhaengen kann (wie htr.py:_MAX_NEW_TOKENS,
# nur grosszuegiger bemessen: diese Engine liest auch ganze Absaetze, nicht
# nur einzelne Zeilen).
_MAX_TOKENS = 2048

# Ollama liefert keinen kalibrierten Konfidenzwert (kein Logprob-Mittel wie
# bei HTR, siehe htr.py:_mean_token_probability -- die OpenAI-kompatible
# Chat-Completions-Antwort enthaelt hierfuer keine verwertbaren logprobs).
# Dieser Wert ist bewusst NICHT gemessen, sondern eine dokumentierte,
# konservative Konstante UNTERHALB von consensus.decide_status()'
# min_confidence-Default (0.75): "so vertrauenswuerdig wie ein Muenzwurf".
# Sie verhindert, dass diese Engine allein durch ihre Konfidenz zu
# auto_clean/APPROVED beitraegt (siehe decide_status: low_confidence-
# Schranke) -- eine spaeter "vereinfachte" 0.9 wuerde genau das aushebeln.
VLM_CONFIDENCE = 0.5

_TRANSPORT_OPENAI_CHAT = "openai_chat"
_TRANSPORT_NATIVE_GENERATE = "native_generate"
# Primaerer Transport -- siehe Moduldoc fuer die Begruendung und den
# ausdruecklichen Hinweis, dass dies NICHT gegen eine echte Ollama-Instanz
# verifiziert wurde. Auf _TRANSPORT_NATIVE_GENERATE umstellen, falls sich
# der OpenAI-kompatible Pfad fuer ein konkretes Modell als unzuverlaessig
# herausstellt.
_ACTIVE_TRANSPORT = _TRANSPORT_OPENAI_CHAT

# Wie tool_server.py:check_ollama -- haelt /api/v1/bootstrap (das status()
# ueber alle konfigurierten Engines aufruft) trotz Netzwerk-Roundtrip
# guenstig. Modul-globaler, nach Endpunkt geschluesselter Cache, damit
# mehrere OllamaVlmEngine-Instanzen mit demselben Endpunkt sich einen
# Tags-Request teilen.
_TAGS_CACHE_TTL_S = 10.0
_tags_lock = threading.Lock()
_tags_cache: dict[str, tuple[float, list[str] | None]] = {}


def _region_suffix(region_id: str | None) -> str:
    """Wie tesseract.py/htr.py:_region_suffix -- region_id ist rein advisory
    (siehe base.OCREngine.recognize), wird aber an Fehlermeldung und Log
    angehaengt, damit ein Fehlschlag sagt, welche Region betroffen war."""
    return f":region={region_id}" if region_id else ""


def _deps_available() -> bool:
    # Wie tesseract.py/htr.py:_deps_available -- find_spec() kann in
    # seltenen Faellen (sys.meta_path-Blocker in Tests) werfen statt None
    # zurueckzugeben; das darf is_available()/status() nie hochreissen.
    try:
        return importlib.util.find_spec("PIL") is not None
    except Exception:
        return False


def _probe_tags(endpoint: str) -> list[str] | None:
    """Reiner GET auf {endpoint}/api/tags -- NIE ein Pull, NIE ein
    Generate-Aufruf. Liefert die Liste der lokal vorhandenen Modellnamen
    oder None, wenn Ollama nicht erreichbar ist (jede Exception zaehlt als
    "nicht erreichbar", nie als harter Fehler)."""
    try:
        url = endpoint.rstrip("/") + "/api/tags"
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read())
        models = data.get("models") or []
        return [m.get("name", "") for m in models if isinstance(m, dict)]
    except Exception:
        return None


def _fetch_tags(endpoint: str) -> list[str] | None:
    """Gecachte (siehe _TAGS_CACHE_TTL_S) Sicht auf _probe_tags(). Wird von
    status() UND recognize() genutzt -- niemals von einer der beiden Stellen
    umgangen, damit "Modell erkannt" in status() und recognize() konsistent
    bleibt."""
    now = time.monotonic()
    with _tags_lock:
        cached = _tags_cache.get(endpoint)
        if cached is not None and now - cached[0] < _TAGS_CACHE_TTL_S:
            return cached[1]
    tags = _probe_tags(endpoint)
    with _tags_lock:
        _tags_cache[endpoint] = (now, tags)
    return tags


def _is_vision_model_name(name: str) -> bool:
    lowered = name.lower()
    return any(lowered.startswith(prefix.lower()) for prefix in VISION_MODEL_PREFIXES)


def _encode_image_to_base64(image: Any) -> str:
    """Kodiert `image` (typischerweise ein von preprocess.prepare() geliefertes
    PIL-Bild) als Base64-PNG. PIL wird bewusst erst hier importiert (siehe
    Lazy-Import-Vertrag in engines/__init__.py) -- wie in htr.py akzeptiert
    dies sowohl ein bereits offenes PIL.Image als auch einen Pfad/ein
    dateiaehnliches Objekt."""
    import base64
    import io

    from PIL import Image

    pil_image = image if isinstance(image, Image.Image) else Image.open(image)
    if pil_image.mode not in ("RGB", "L"):
        pil_image = pil_image.convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _call_openai_chat(endpoint: str, model: str, prompt: str, image_b64: str, *, timeout_s: int) -> str:
    """Primaerer Transport -- siehe Moduldoc fuer Begruendung/Evidenz."""
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
        # Transkription, keine Generierung: Sampling ist hier reiner Nachteil
        # (Bug-2-Klasse von Risiko in kleiner: ein Modell, das "kreativ" wird,
        # statt zu transkribieren).
        "temperature": 0,
        "max_tokens": _MAX_TOKENS,
        "stream": False,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data = json.loads(response.read())
    return data["choices"][0]["message"]["content"]


def _call_native_generate(endpoint: str, model: str, prompt: str, image_b64: str, *, timeout_s: int) -> str:
    """Dokumentierter Fallback-Transport (siehe Moduldoc) -- ``/api/generate``
    mit ``images: [b64]`` statt des OpenAI-kompatiblen Pfads. Wird nur
    verwendet, wenn ``_ACTIVE_TRANSPORT`` das erzwingt."""
    url = endpoint.rstrip("/") + "/api/generate"
    body = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0, "num_predict": _MAX_TOKENS},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data = json.loads(response.read())
    return data["response"]


class OllamaVlmEngine:
    name = "ollama_vlm"
    kind: EngineKind = "vlm"
    # Beschreibt die moeglichen Beschleuniger des Ollama-SERVER-Prozesses,
    # nicht dieses Python-Prozesses (die eigentliche Inferenz laeuft
    # ausserhalb dieses Codes) -- absichtlich dieselbe konservative Form wie
    # htr.py, da diese Engine selbst kein Device waehlt.
    capabilities: Mapping[str, bool] = {
        "cpu": True,
        "cuda": True,
        "vulkan": False,
        "xpu": False,
        "rocm": False,
    }

    def __init__(
        self,
        model_id: str = DEFAULT_VISION_MODEL,
        endpoint: str = "http://127.0.0.1:11434",
        classification: str = "student_submission",
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.model_id = model_id
        self.endpoint = endpoint
        self.classification = classification
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        return _deps_available()

    def status(self) -> EngineStatus:
        # NIE einen Pull ausloesen -- nur ein GET auf /api/tags (siehe
        # _probe_tags/_fetch_tags Docstrings).
        tags = _fetch_tags(self.endpoint)
        if tags is None:
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason="ollama_offline",
                model_id=self.model_id,
                capabilities=self.capabilities,
            )
        try:
            self._resolve_vision_model(tags)
        except EngineError as exc:
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason=exc.reason,
                model_id=self.model_id,
                capabilities=self.capabilities,
            )
        return EngineStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            reason="",
            model_id=self.model_id,
            capabilities=self.capabilities,
        )

    def supports(self, region_type: RegionType) -> bool:
        # Allzweck-Zweitleser: unterstuetzt auch RegionType.FORMULA (siehe
        # Moduldoc/FORMULA_PROMPT_DE) -- anders als HTR (nur TEXT_LINE).
        return True

    def _resolve_vision_model(self, tags: Sequence[str]) -> str:
        """Siehe Moduldoc "BUG 2": liefert NUR einen Namen, der (a) in `tags`
        vorkommt und (b) zu einem bekannten Vision-Praefix passt. Bevorzugt
        `self.model_id`, sonst der Reihe nach VISION_MODEL_PREFIXES. Sonst
        EngineError -- NIE ein Fallback auf ein Nicht-Vision-Modell."""
        tag_set = set(tags)
        if self.model_id in tag_set and _is_vision_model_name(self.model_id):
            return self.model_id
        for prefix in VISION_MODEL_PREFIXES:
            for tag in tags:
                if tag.lower().startswith(prefix.lower()):
                    return tag
        raise EngineError(self.name, f"model_not_pulled:{self.model_id}")

    def recognize(
        self,
        image: Any,
        *,
        region_type: RegionType,
        language: str = "deu",
        region_id: str | None = None,
    ) -> OCRCandidate:
        # ALLERERSTE Anweisung -- siehe privacy_guard.py Modul-Docstring und
        # Moduldoc "PRIVACY" oben. CloudBlocked wird HIER NIE abgefangen.
        assert_local_only(self.classification, self.endpoint, engine=self.name)

        tags = _fetch_tags(self.endpoint)
        if tags is None:
            reason = f"ollama_offline{_region_suffix(region_id)}"
            logger.warning("Ollama nicht erreichbar (Region %s)", region_id or "?")
            raise EngineError(self.name, reason)

        try:
            vision_model = self._resolve_vision_model(tags)
        except EngineError as exc:
            reason = f"{exc.reason}{_region_suffix(region_id)}"
            logger.warning(
                "Kein Vision-Modell verfuegbar (Region %s): %s", region_id or "?", exc.reason
            )
            raise EngineError(self.name, reason) from exc

        prompt = FORMULA_PROMPT_DE if region_type is RegionType.FORMULA else VERBATIM_PROMPT_DE

        try:
            image_b64 = _encode_image_to_base64(image)
        except Exception as exc:
            reason = f"image_encode_failed:{exc}{_region_suffix(region_id)}"
            logger.warning(
                "Bild konnte nicht kodiert werden (Region %s): %s", region_id or "?", exc
            )
            raise EngineError(self.name, reason) from exc

        try:
            start = _now_ms()
            raw_text = self._transcribe(vision_model, prompt, image_b64)
            duration_ms = _now_ms() - start
        except Exception as exc:
            reason = f"recognize_failed:{exc}{_region_suffix(region_id)}"
            logger.warning(
                "Ollama-VLM-Erkennung fehlgeschlagen (Region %s): %s", region_id or "?", exc
            )
            raise EngineError(self.name, reason) from exc

        # Wie bei jeder anderen Engine: Markup ((<uncertain>...</uncertain>)
        # etc.) wird aufgeloest, damit diese Engine sich selbst eskalieren
        # kann, auch wenn sie die einzige Engine im Job ist.
        parsed = parse_markup(raw_text)
        tokens, _ = tokenize(parsed.text)

        return OCRCandidate(
            engine=self.name,
            text=parsed.text,
            raw_text=raw_text,
            confidence=VLM_CONFIDENCE,
            tokens=tokens,
            # Kein Logprob-Signal aus der Chat-Completions-Antwort -- siehe
            # VLM_CONFIDENCE-Docstring. Eine erfundene Pro-Token-Aufteilung
            # waere schlimmer als gar keine.
            token_confidences=(),
            duration_ms=duration_ms,
            markers=parsed.markers,
        )

    def _transcribe(self, vision_model: str, prompt: str, image_b64: str) -> str:
        if _ACTIVE_TRANSPORT == _TRANSPORT_NATIVE_GENERATE:
            return _call_native_generate(
                self.endpoint, vision_model, prompt, image_b64, timeout_s=self.timeout_s
            )
        return _call_openai_chat(
            self.endpoint, vision_model, prompt, image_b64, timeout_s=self.timeout_s
        )

    def warmup(self) -> None:
        # Kein lokales Modell zum Vorladen -- Ollama laeuft als eigener
        # Prozess. No-op wie im Protocol-Default (siehe base.OCREngine).
        return None


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


__all__ = [
    "OllamaVlmEngine",
    "VISION_MODEL_PREFIXES",
    "DEFAULT_VISION_MODEL",
    "VLM_CONFIDENCE",
    "DEFAULT_TIMEOUT_S",
]
