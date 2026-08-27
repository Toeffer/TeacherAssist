"""Cloud-Zugriffssperre fuer die OCR-Pipeline.

JEDE OCR-ENGINE, DIE EINEN NETZWERK-SOCKET OEFFNET (Cloud-API, HTTP-Client
etc.), MUSS ``assert_local_only()`` ALS ALLERERSTE ANWEISUNG AUFRUFEN --
NOCH VOR DEM AUFBAU DER VERBINDUNG. Es gibt keine Ausnahme von dieser Regel.

``CloudBlocked`` DARF INNERHALB DER PIPELINE (pipeline.py: process_page/
process_document) NIEMALS ABGEFANGEN werden -- innerhalb dieser Funktionen
gilt weiterhin uneingeschraenkt: kein stiller Fallback auf eine andere
Engine, kein "catch and continue". Das wuerde genau die Klasse von Bug
reproduzieren, derentwegen dieser gesamte Refactor existiert: eine
Schuelerarbeit, die unbemerkt an einen Cloud-Anbieter geschickt wird.

Was danach mit der Exception passiert, haengt vom Aufrufpfad ab, und die
beiden Faelle sind NICHT gleich:

- SYNCHRONER Pfad (process_single_image_sync() o.ae., direkt aus einem
  HTTP-Request-Handler aufgerufen): hier MUSS ``CloudBlocked`` bis in die
  HTTP-Schicht durchschlagen, wo sie dem Nutzer als Fehler angezeigt wird
  -- es gibt einen lebenden Call-Stack, der sie tragen kann.
- ASYNCHRONER Pfad (OCRJobStore._run_job() auf dem Hintergrund-Worker,
  siehe store.py): "durchschlagen bis in die HTTP-Schicht" ist hier
  UNMOEGLICH -- die HTTP-Antwort (202 processing) wurde laengst
  zurueckgegeben, es gibt keinen lebenden Call-Stack mehr. store.py faengt
  ``CloudBlocked`` deshalb an der Executor-Grenze ab und terminiert den Job
  als FAILED mit einem eigenen, maschinenlesbaren Marker
  (``store.CLOUD_BLOCKED_ERROR_CODE``) -- das ist die einzige Stelle, an
  der ein Abfangen zulaessig ist, UND NUR, um es als das zu markieren, was
  es ist: NICHT als gewoehnlicher ``engine_failure``, der ``needs_review``
  ergibt.
"""

from __future__ import annotations

from ..privacy import cloud_allowed_for_classification, is_trusted_loopback_endpoint


class CloudBlocked(PermissionError):
    """Wird ausgeloest, wenn eine Klassifikation Cloud-Zugriff verbietet und
    der Ziel-Endpunkt kein vertrauenswuerdiger Loopback-Endpunkt ist.

    ``engine`` benennt (falls bekannt) die Engine, die den Verstoss ausgeloest
    hat -- optional, damit bestehende Aufrufstellen nicht brechen. Wird sie
    hier nicht mitgegeben (z.B. weil ``assert_local_only`` selbst sie nicht
    kennt), setzt pipeline.py sie an der Stelle nach, an der bekannt ist,
    welche Engine gerade aufgerufen wurde (siehe process_page), bevor die
    Exception weitergereicht wird -- so muss store.py's Sicherheits-Logzeile
    nicht mehr auf "eine der konfigurierten Engines" approximieren.

    ``__str__`` baut die Meldung ABSICHTLICH bei jedem Aufruf frisch aus dem
    AKTUELLEN Wert von ``self.engine`` (statt sie einmalig in ``__init__``
    einzufrieren): pipeline.py setzt ``exc.engine`` typischerweise erst NACH
    der Konstruktion (siehe oben) nach, bevor sie weiterwirft -- ``str(exc)``
    (das store.py fuer ``DocumentResult.error`` verwendet) muss diesen
    nachtraeglich gesetzten Namen trotzdem noch sehen."""

    def __init__(self, classification: str, endpoint: str, engine: str | None = None) -> None:
        self.classification = classification
        self.endpoint = endpoint
        self.engine = engine
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        message = (
            f"Cloud-Zugriff fuer Klassifikation '{self.classification}' auf Endpunkt "
            f"'{self.endpoint}' ist nicht erlaubt (nur lokale/Loopback-Endpunkte)."
        )
        if self.engine is not None:
            message += f" (Engine: {self.engine})"
        return message

    def __str__(self) -> str:
        return self._build_message()


def assert_local_only(classification: str, endpoint_url: str, engine: str | None = None) -> None:
    """Erzwingt lokale Verarbeitung, wenn die Klassifikation Cloud verbietet.

    Erlaubt den Aufruf nur, wenn entweder die Klassifikation Cloud-Zugriff
    zulaesst (``cloud_allowed_for_classification``) oder der Endpunkt ein
    vertrauenswuerdiger Loopback-Endpunkt ist (``is_trusted_loopback_endpoint``).
    Andernfalls wird ``CloudBlocked`` ausgeloest.

    ``engine`` ist optional und wird 1:1 an ``CloudBlocked`` durchgereicht:
    ruft eine Engine dies als allerersten Schritt mit ihrem eigenen Namen auf,
    ist die Exception bereits am Entstehungsort identifiziert (siehe
    ``CloudBlocked``-Docstring).
    """
    if cloud_allowed_for_classification(classification):
        return
    if is_trusted_loopback_endpoint(endpoint_url):
        return
    raise CloudBlocked(classification, endpoint_url, engine=engine)
