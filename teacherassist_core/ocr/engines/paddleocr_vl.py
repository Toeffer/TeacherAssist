"""PaddleOCR-VL Layout-/Dokument-Engine (Stufe 8 des OCR-Refactors).

PaddleOCR-VL ist ein DOKUMENTEN-Parsing-Modell (Layout, Tabellen, Formeln,
Lesereihenfolge) -- KEIN Handschrift-Spezialist. Fuer handschriftliche
Schuelerarbeiten ist es die schwaechste hier verfuegbare Engine; sein Wert
liegt bei gedruckten Arbeitsblaettern, Tabellen und Formelregionen.

STATUS DIESER STUFE: Modul gebaut, registriert, ABSICHTLICH DEAKTIVIERT --
nicht in DEFAULT_ENGINES (siehe engines/__init__.py), keine Abhaengigkeit
installiert (siehe tools/requirements-ocr-paddle.txt). Zwei konkurrierende
Installationspfade, BEIDE mit echtem Konflikt zum bestehenden venv:

  - "transformers"-Backend (AutoModelForImageTextToText, der offizielle
    huggingface-native Weg fuer PaddleOCR-VL) braucht transformers>=5.0.0.
    Dieses venv haelt transformers==4.57.6, festgenagelt von
    sentence-transformers==3.4.1 ("transformers<5.0.0" in dessen eigener
    Dependency-Spec) -- dem RAG-Embedding-Pfad. Ein Upgrade wuerde ChromaDB
    brechen, um einen Dokument-Parser zu gewinnen.
  - "paddleocr"-Backend (paddlepaddle + paddleocr[doc-parser]) ist auf
    Windows/cp312 installierbar, zieht aber opencv, shapely und pyclipper
    sowie eine eigene numpy-Anforderung neben ChromaDBs mit.

Deshalb: Modul bauen, registrieren, NICHTS installieren, Engine per Default
AUS lassen. Eine Lehrkraft, die requirements-ocr-paddle.txt bewusst
installiert, schaltet die Engine ueber die Settings-UI frei (ocrEngines).

Schwere Importe (paddle, paddleocr, transformers, torch, PIL) bleiben
ausschliesslich innerhalb von Methoden -- siehe engines/__init__.py fuer den
Lazy-Import-Vertrag dieses Pakets. is_available()/status() pruefen nur ueber
importlib.util.find_spec() (Abhaengigkeiten), importlib.metadata.version()
(installierte transformers-Version, NIE hartkodiert) bzw.
huggingface_hub.try_to_load_from_cache() (Gewichte im HF-Cache) -- nie ueber
einen echten Import oder gar from_pretrained()/einen Backend-Aufruf.

BACKENDS: zwei Implementierungen, zur LAUFZEIT gewaehlt (nie beim Import
oder im Konstruktor, siehe _resolve_backend):
  - "transformers": AutoModelForImageTextToText.from_pretrained(...), lokal
    wie engines/htr.py (local_files_only=True als zweite Absicherung gegen
    einen impliziten Download, siehe dortigen Moduldoc).
  - "paddleocr": paddleocr[doc-parser]s eigene PaddleOCR-VL-Pipeline.
  - "auto": paddleocr, falls importierbar, sonst transformers, falls dessen
    Version ausreicht, sonst nicht verfuegbar.

TODO(verify) -- WEDER Backend wurde in dieser Stufe tatsaechlich ausgefuehrt
(keine der beiden Abhaengigkeiten ist in diesem venv installiert). Konkret
ungeprueft, bevor eine dieser beiden Methoden fuer echt gehalten werden darf:
  - Modell-ID/Revision: ob "PaddlePaddle/PaddleOCR-VL-1.6" exakt der
    Hub-Bezeichner ist, den AutoModelForImageTextToText.from_pretrained()
    bzw. paddleocr's eigener Lader erwartet.
  - Aufruf-Form des transformers-Backends (_recognize_with_transformers):
    Prompt-/Chat-Template-Format (ob VERBATIM_PROMPT_DE/FORMULA_PROMPT_DE
    unveraendert als Chat-Message funktionieren oder ein
    Processor-spezifisches Template noetig ist), und ob
    model.generate(..., output_scores=True) +
    model.compute_transition_scores(...) (wie
    engines/htr.py:_mean_token_probability) fuer dieses Modell ueberhaupt
    ein sinnvolles Konfidenzsignal liefert.
  - Aufruf-Form des paddleocr-Backends (_recognize_with_paddleocr): exakte
    Klasse/Methode (PaddleOCRVL().predict() ist eine Vermutung, kein
    verifizierter Aufruf), ob region-weise Bilder oder nur ganze Seiten
    entgegengenommen werden, und vor allem die Form der Rueckgabe --
    _extract_text_from_paddle_result() wirft deshalb bewusst einen
    EngineError statt eine geratene Struktur (z.B. bestimmte dict-Schluessel)
    anzunehmen.
  - Post-Processing: ob die Rohausgabe beider Backends bereits reiner Text
    ist oder erst aus einer strukturierten Layout-/Markdown-Antwort
    extrahiert werden muss, bevor markup.parse_markup() sinnvoll darauf
    angewendet werden kann.

Modell-ID und Backend sind Settings-getrieben (ocrPaddleModel/
ocrPaddleBackend, siehe engines/__init__.py-Factory) -- eine spaetere
Korrektur der obigen Punkte aendert also einen Settings-Wert oder eine der
beiden duennen _recognize_with_*-Methoden, nie recognize() selbst.

PRIVACY: Wie engines/ollama_vlm.py ruft recognize() als ALLERERSTE
Anweisung assert_local_only() auf -- CloudBlocked wird hier NIE abgefangen
und NIE in einen EngineError umgewandelt (siehe privacy_guard.py
Modul-Docstring). Anders als ollama_vlm hat diese Engine aber keinen
echten, nutzerkonfigurierbaren Netzwerk-Endpunkt: beide Backends fuehren
Inferenz vollstaendig im eigenen Prozess aus. Der hier uebergebene Endpunkt
(_LOCAL_MODEL_ENDPOINT) ist deshalb ein Loopback-Sentinel, kein echter
Ziel-Host -- er haelt den Aufruf-Ort bereits fest, an dem ein spaeterer
echter Remote-/Cloud-Backend-Modus (falls je hinzugefuegt) den
tatsaechlichen Ziel-Host uebergeben MUESSTE, macht den Aufruf fuer die
heutige, rein lokale Ausfuehrung aber unschaedlich.
"""

from __future__ import annotations

import importlib.util
import logging
import threading
from typing import Any, Mapping

from ..consensus import tokenize
from ..markup import parse_markup
from ..privacy_guard import assert_local_only
from ..prompts import FORMULA_PROMPT_DE, VERBATIM_PROMPT_DE
from ..types import OCRCandidate, RegionType
from .base import EngineError, EngineKind, EngineStatus

logger = logging.getLogger(__name__)

DEFAULT_PADDLE_MODEL = "PaddlePaddle/PaddleOCR-VL-1.6"

BACKEND_AUTO = "auto"
BACKEND_PADDLE = "paddleocr"
BACKEND_TRANSFORMERS = "transformers"
KNOWN_BACKENDS = (BACKEND_AUTO, BACKEND_PADDLE, BACKEND_TRANSFORMERS)

# Harte Untergrenze der transformers-nativen Route (siehe Moduldoc) -- NICHT
# die installierte Version (die wird zur Laufzeit gelesen, siehe
# _transformers_installed_version).
_MIN_TRANSFORMERS_MAJOR = 5
_MIN_TRANSFORMERS_VERSION_STR = "5.0.0"

# Siehe Moduldoc "PRIVACY".
_LOCAL_MODEL_ENDPOINT = "http://127.0.0.1/paddleocr-vl-local-model"

# Ganze Absaetze/Tabellen statt einer Einzelzeile (vgl. htr.py:_MAX_NEW_TOKENS),
# aber wie dort v.a. ein Deckel gegen einen haengenden Wiederholungs-Loop.
_MAX_NEW_TOKENS = 512

# Wie engines/ollama_vlm.py:VLM_CONFIDENCE -- dokumentierte, konservative
# Konstante UNTERHALB von consensus.decide_status()'s min_confidence-Default
# (0.75), NIE erfunden als Ersatz fuer ein echtes Signal. Greift fuer das
# paddleocr-Backend (dessen Ausgabeform, inkl. eventueller Konfidenzwerte
# pro Block, nicht verifiziert ist, siehe Moduldoc TODO(verify)) sowie als
# Rueckfallwert, falls das transformers-Backend kein auswertbares
# Score-Signal liefert.
FALLBACK_CONFIDENCE = 0.5

# Modell-/Pipeline-Cache ueber alle PaddleOcrVlEngine-Instanzen hinweg (wie
# htr.py:_MODEL_CACHE), geschuetzt durch _MODEL_LOCK.
_MODEL_CACHE: dict[tuple[str, str, str], Any] = {}
_MODEL_LOCK = threading.Lock()


def _region_suffix(region_id: str | None) -> str:
    """Wie tesseract.py/htr.py/ollama_vlm.py:_region_suffix."""
    return f":region={region_id}" if region_id else ""


def _paddle_deps_available() -> bool:
    # Wie tesseract.py/htr.py:_deps_available -- find_spec() kann in
    # seltenen Faellen (sys.meta_path-Blocker in Tests) werfen statt None
    # zurueckzugeben; das darf is_available()/status() nie hochreissen.
    try:
        return (
            importlib.util.find_spec("paddle") is not None
            and importlib.util.find_spec("paddleocr") is not None
        )
    except Exception:
        return False


def _transformers_installed_version() -> str | None:
    """Liest die installierte transformers-Version zur LAUFZEIT -- NIE
    hartkodiert (siehe Moduldoc). None, wenn transformers nicht
    importierbar ist oder die Version nicht ermittelt werden kann."""
    try:
        if importlib.util.find_spec("transformers") is None:
            return None
    except Exception:
        return None
    try:
        import importlib.metadata as metadata

        return metadata.version("transformers")
    except Exception:
        return None


def _transformers_version_sufficient(version: str | None) -> bool:
    if not version:
        return False
    try:
        major = int(version.split(".")[0])
    except (ValueError, IndexError):
        return False
    return major >= _MIN_TRANSFORMERS_MAJOR


def _resolve_backend(requested: str) -> tuple[str | None, str]:
    """Waehlt das zu verwendende Backend zur LAUFZEIT (nie beim Import/im
    Konstruktor, siehe Moduldoc). Liefert (Backend-Name, "") bei Erfolg,
    sonst (None, maschinenlesbarer Grund) -- NIE eine Exception fuer einen
    schlicht nicht verfuegbaren Zustand (siehe base.EngineStatus.reason)."""
    if requested == BACKEND_PADDLE:
        if _paddle_deps_available():
            return BACKEND_PADDLE, ""
        return None, "not_installed:paddlepaddle"

    if requested == BACKEND_TRANSFORMERS:
        version = _transformers_installed_version()
        if version is None:
            return None, "not_installed:transformers"
        if not _transformers_version_sufficient(version):
            return None, f"transformers_too_old:{version}<{_MIN_TRANSFORMERS_VERSION_STR}"
        return BACKEND_TRANSFORMERS, ""

    if requested == BACKEND_AUTO:
        # Reihenfolge: paddleocr zuerst (falls importierbar), sonst
        # transformers, falls dessen Version ausreicht, sonst nicht
        # verfuegbar (siehe Moduldoc "BACKENDS").
        if _paddle_deps_available():
            return BACKEND_PADDLE, ""
        version = _transformers_installed_version()
        if version is not None and _transformers_version_sufficient(version):
            return BACKEND_TRANSFORMERS, ""
        if version is not None:
            return None, f"transformers_too_old:{version}<{_MIN_TRANSFORMERS_VERSION_STR}"
        return None, "not_installed:paddlepaddle"

    return None, f"unknown_backend:{requested}"


def _weights_cached(model_id: str) -> bool:
    """Rein lokale Pruefung (kein Netzwerk) ueber den HF-Cache -- wie
    htr.py:_weights_cached. TODO(verify): fuer das paddleocr-Backend nicht
    verifiziert, ob dessen eigener Modell-Cache (vermutlich ein
    PaddleX-spezifisches Verzeichnis, nicht der HF-Cache) hierueber
    ueberhaupt sichtbar ist -- bis das geprueft ist, liefert diese Funktion
    im Zweifel False (nie faelschlich True)."""
    try:
        from huggingface_hub import try_to_load_from_cache

        for filename in (
            "model.safetensors",
            "model.safetensors.index.json",
            "pytorch_model.bin",
        ):
            if isinstance(try_to_load_from_cache(model_id, filename), str):
                return True
        return False
    except Exception:
        return False


def _resolve_device(device: str) -> str:
    """Wie htr.py:_resolve_device -- loest "auto" erst hier auf (nie beim
    Import/Konstruktor)."""
    if device == "cpu":
        return "cpu"
    if device == "cuda":
        return "cuda"
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _now_ms() -> int:
    import time

    return int(time.monotonic() * 1000)


class PaddleOcrVlEngine:
    name = "paddleocr_vl"
    kind: EngineKind = "layout"
    capabilities: Mapping[str, bool] = {
        "cpu": True,
        "cuda": True,
        "vulkan": False,
        "xpu": False,
        "rocm": False,
    }

    def __init__(
        self,
        model_id: str = DEFAULT_PADDLE_MODEL,
        backend: str = BACKEND_AUTO,
        device: str = "auto",
        classification: str = "student_submission",
    ) -> None:
        self.model_id = model_id
        self.backend = backend
        self.device = device
        self.classification = classification

    def is_available(self) -> bool:
        backend, _ = _resolve_backend(self.backend)
        return backend is not None

    def status(self) -> EngineStatus:
        backend, reason = _resolve_backend(self.backend)
        if backend is None:
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason=reason,
                model_id=self.model_id,
                capabilities=self.capabilities,
            )
        if not _weights_cached(self.model_id):
            return EngineStatus(
                name=self.name,
                kind=self.kind,
                available=False,
                reason=f"model_not_downloaded:{self.model_id}",
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
        # Dokumenten-Layout-Parser: Text, Absaetze, Tabellen, Formeln,
        # Ueberschriften -- KEINE Abbildungen (FIGURE, kein OCR-Fall).
        return region_type in (
            RegionType.TEXT_LINE,
            RegionType.PARAGRAPH,
            RegionType.TABLE,
            RegionType.FORMULA,
            RegionType.HEADER,
        )

    def recognize(
        self,
        image: Any,
        *,
        region_type: RegionType,
        language: str = "deu",
        region_id: str | None = None,
    ) -> OCRCandidate:
        # ALLERERSTE Anweisung -- siehe Moduldoc "PRIVACY" und
        # privacy_guard.py Modul-Docstring. CloudBlocked wird HIER NIE
        # abgefangen.
        assert_local_only(self.classification, _LOCAL_MODEL_ENDPOINT, engine=self.name)

        if not self.supports(region_type):
            reason = f"unsupported_region_type:{region_type.value}{_region_suffix(region_id)}"
            logger.warning(
                "PaddleOCR-VL unterstuetzt RegionType %s nicht (Region %s)",
                region_type.value, region_id or "?",
            )
            raise EngineError(self.name, reason)

        status = self.status()
        if not status.available:
            reason = f"{status.reason}{_region_suffix(region_id)}"
            logger.warning(
                "PaddleOCR-VL nicht verfuegbar (%s, Region %s)", status.reason, region_id or "?"
            )
            raise EngineError(self.name, reason)

        backend, _ = _resolve_backend(self.backend)
        prompt = FORMULA_PROMPT_DE if region_type is RegionType.FORMULA else VERBATIM_PROMPT_DE

        try:
            start = _now_ms()
            raw_text, confidence = self._run_backend(backend, image, prompt)
            duration_ms = _now_ms() - start
        except Exception as exc:
            reason = f"recognize_failed:{exc}{_region_suffix(region_id)}"
            logger.warning(
                "PaddleOCR-VL-Erkennung fehlgeschlagen (Region %s): %s", region_id or "?", exc
            )
            raise EngineError(self.name, reason) from exc

        # Wie bei jeder anderen Engine: Markup ((<uncertain>...</uncertain>)
        # etc.) wird aufgeloest.
        parsed = parse_markup(raw_text)
        tokens, _ = tokenize(parsed.text)

        return OCRCandidate(
            engine=self.name,
            text=parsed.text,
            raw_text=raw_text,
            confidence=confidence,
            tokens=tokens,
            token_confidences=(),
            duration_ms=duration_ms,
            markers=parsed.markers,
        )

    def _run_backend(self, backend: str | None, image: Any, prompt: str) -> tuple[str, float]:
        """Dispatch auf das gewaehlte Backend. Duenn gehalten (kein Zustand,
        keine Verzweigungslogik ausser der Auswahl), damit eine Korrektur an
        der Aufruf-Form (siehe Moduldoc TODO(verify)) nur eine der beiden
        _recognize_with_*-Methoden anfasst, nie recognize() selbst. Auch der
        Test-Seam fuer eine gestubbte Erkennung (siehe test_ocr_paddle.py)."""
        if backend == BACKEND_TRANSFORMERS:
            return self._recognize_with_transformers(image, prompt)
        return self._recognize_with_paddleocr(image, prompt)

    def _recognize_with_transformers(self, image: Any, prompt: str) -> tuple[str, float]:
        """TODO(verify): Aufruf-Form gegen ein echtes transformers>=5-
        Environment NICHT verifiziert (siehe Moduldoc). Modelliert nach
        AutoModelForImageTextToText + dem Chat-Message-Muster, das
        transformers fuer Vision-Sprachmodelle dokumentiert -- ob
        PaddleOCR-VL-1.6 exakt dieses Prompt-/Processor-Format erwartet
        (statt eines eigenen Task-Tokens), ist ungeprueft."""
        processor, model, device = self._load_transformers_model()

        import torch
        from PIL import Image

        pil_image = image if isinstance(image, Image.Image) else Image.open(image)
        pil_image = pil_image.convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(device)

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=_MAX_NEW_TOKENS,
                output_scores=True,
                return_dict_in_generate=True,
            )

        generated = outputs.sequences[:, inputs["input_ids"].shape[-1]:]
        text = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        confidence = self._transformers_confidence(model, outputs)
        return text, confidence

    def _transformers_confidence(self, model: Any, outputs: Any) -> float:
        """Wie htr.py:_mean_token_probability. TODO(verify): ob
        AutoModelForImageTextToText.compute_transition_scores fuer dieses
        Modell dasselbe Verhalten wie VisionEncoderDecoderModel zeigt.
        Faellt bei jedem Fehler auf FALLBACK_CONFIDENCE zurueck, statt einen
        Wert zu erfinden oder recognize() abstuerzen zu lassen."""
        try:
            import torch

            scores = getattr(outputs, "scores", None)
            if not scores:
                return FALLBACK_CONFIDENCE
            transition_scores = model.compute_transition_scores(
                outputs.sequences, scores, normalize_logits=True
            )
            finite_mask = torch.isfinite(transition_scores)
            if not bool(finite_mask.any()):
                return FALLBACK_CONFIDENCE
            probs = transition_scores[finite_mask].exp()
            return float(probs.mean().item())
        except Exception:
            return FALLBACK_CONFIDENCE

    def _load_transformers_model(self) -> tuple[Any, Any, str]:
        device = _resolve_device(self.device)
        cache_key = (BACKEND_TRANSFORMERS, self.model_id, device)
        with _MODEL_LOCK:
            cached = _MODEL_CACHE.get(cache_key)
            if cached is not None:
                processor, model = cached
                return processor, model, device

            # TODO(verify): Klassenname/Import-Pfad gegen ein echtes
            # transformers>=5-Environment nicht verifiziert (siehe Moduldoc).
            from transformers import AutoModelForImageTextToText, AutoProcessor

            # local_files_only=True ist die zweite Absicherung gegen einen
            # impliziten Download (die erste ist die status()-Pruefung oben
            # in recognize()) -- wie htr.py:_load.
            processor = AutoProcessor.from_pretrained(self.model_id, local_files_only=True)
            model = AutoModelForImageTextToText.from_pretrained(
                self.model_id, local_files_only=True
            )
            model.eval()
            model.to(device)
            _MODEL_CACHE[cache_key] = (processor, model)
            return processor, model, device

    def _recognize_with_paddleocr(self, image: Any, prompt: str) -> tuple[str, float]:
        """TODO(verify): paddleocr[doc-parser]s tatsaechliche Python-API fuer
        PaddleOCR-VL NICHT verifiziert (siehe Moduldoc) -- weder Klassen-
        noch Methodenname, noch ob eine einzelne Region (statt einer ganzen
        Seite) entgegengenommen wird. `prompt` wird aktuell nicht verwendet,
        weil ungeklaert ist, ob/wie das paddleocr-Backend ein
        Prompt-Argument uebernimmt (ggf. steuert es Formel- vs.
        Text-Erkennung stattdessen ueber region_type/einen eigenen
        Task-Parameter) -- absichtlich keine geratene Verwendung."""
        pipeline = self._load_paddleocr_pipeline()

        from PIL import Image

        pil_image = image if isinstance(image, Image.Image) else Image.open(image)
        pil_image = pil_image.convert("RGB")

        result = pipeline.predict(pil_image)
        text = self._extract_text_from_paddle_result(result)
        return text, FALLBACK_CONFIDENCE

    def _extract_text_from_paddle_result(self, result: Any) -> str:
        """TODO(verify): Form der paddleocr-Rueckgabe ungeprueft -- wirft
        deshalb bewusst EngineError statt eine geratene dict-/Objektstruktur
        anzunehmen, sobald das tatsaechliche Format bekannt ist (siehe
        Moduldoc TODO(verify))."""
        raise EngineError(self.name, "paddleocr_backend_output_shape_unverified")

    def _load_paddleocr_pipeline(self) -> Any:
        cache_key = (BACKEND_PADDLE, self.model_id, "")
        with _MODEL_LOCK:
            cached = _MODEL_CACHE.get(cache_key)
            if cached is not None:
                return cached

            # TODO(verify): Klassenname/Import-Pfad ungeprueft (siehe
            # Moduldoc) -- ob PaddleOCRVL lokale Gewichte respektiert, ohne
            # selbst einen Download auszuloesen, ist NICHT verifiziert.
            from paddleocr import PaddleOCRVL

            pipeline = PaddleOCRVL(model_name=self.model_id)
            _MODEL_CACHE[cache_key] = pipeline
            return pipeline

    def warmup(self) -> None:
        # Wie htr.py:warmup -- laedt NUR, wenn status() bereits verfuegbar
        # meldet (Gewichte gecacht), loest nie einen Download aus.
        if not self.status().available:
            return
        backend, _ = _resolve_backend(self.backend)
        try:
            if backend == BACKEND_TRANSFORMERS:
                self._load_transformers_model()
            else:
                self._load_paddleocr_pipeline()
        except Exception:
            logger.warning("PaddleOCR-VL-Warmup fehlgeschlagen (Modell %s)", self.model_id)


__all__ = [
    "PaddleOcrVlEngine",
    "DEFAULT_PADDLE_MODEL",
    "BACKEND_AUTO",
    "BACKEND_PADDLE",
    "BACKEND_TRANSFORMERS",
    "FALLBACK_CONFIDENCE",
]
