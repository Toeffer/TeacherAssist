#!/usr/bin/env python3
"""
TeacherAssist Tool-Server  –  Port 8789
=========================================
Stellt lokale Endpunkte bereit:
  GET  /health               – Statuscheck
  GET  /collections          – Anzahl gespeicherter Abschnitte in ChromaDB
  GET  /search?q=...         – Semantische Lehrplan-Suche (RAG)
  GET  /settings             – Gespeicherte Einstellungen abrufen
  GET  /backup               – Memory-Verzeichnis als ZIP herunterladen
  GET  /list-raster          – Bewertungsraster auflisten
  GET  /memory-list          – Alle .md-Dateien unter memory/
  GET  /memory-read?file=... – Einzelne Memory-Datei lesen
  GET  /memory-versions?file=... – Backup-Versionen einer Datei

  POST /chat                 – LLM-Chat mit Streaming (NEU: Proxy + DSGVO-Filter + Skill-Router)
  POST /upload               – PDF-Datei speichern (multipart)
  POST /ingest               – PDF verarbeiten + in ChromaDB speichern
  POST /clear                – Gesamte Wissensdatenbank leeren
  POST /download-url         – Lehrplan per URL herunterladen
  POST /settings             – Einstellungen speichern
  POST /save-raster          – Bewertungsraster speichern
  POST /restore              – Backup wiederherstellen (ZIP)
  POST /memory-write         – Memory-Datei schreiben
  POST /memory-restore-version – Backup-Version wiederherstellen
  POST /ocr-image            – Bild per OCR in Text umwandeln
  POST /session-summary      – Chat-Verlauf zusammenfassen und in vergangene_stunden.md speichern

Sicherheit:
  - API-Key NUR serverseitig in settings.json
  - DSGVO-Filter prüft jede Nachricht VOR API-Versand
  - Schülerdaten → automatisch Ollama (lokal) statt Cloud-API
  - Skill-Router lädt passende skill.md ohne OpenClaw
"""

import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE_DIR      = Path(__file__).parent
UPLOAD_DIR    = BASE_DIR / "uploads"
CHROMA_DIR    = BASE_DIR / "tools" / "chroma_db"
SETTINGS_FILE = BASE_DIR / "settings.json"
SKILLS_DIR    = BASE_DIR / "skills"
MEMORY_DIR    = BASE_DIR / "memory"
SKILLS_INDEX  = BASE_DIR / "skills_index.json"

UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

ORIGIN = "http://localhost:8788"

# ---------------------------------------------------------------------------
# Konfiguration laden
# ---------------------------------------------------------------------------
def load_settings():
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text("utf-8"))
    except Exception:
        pass
    return {"provider": "openrouter", "ollamaModel": "gemma3:4b", "model": "deepseek/deepseek-chat"}

def get_api_key():
    """API-Key aus settings.json oder Umgebungsvariable."""
    try:
        s = load_settings()
        if s.get("apiKey"):
            return s["apiKey"]
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY", "")

# ---------------------------------------------------------------------------
# DSGVO-Filter (serverseitig – nicht umgehbar)
# ---------------------------------------------------------------------------
def detect_personal_data(text):
    findings = []
    if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text):
        findings.append({"type": "E-Mail-Adresse", "auto": True})
    if re.search(r'(\+49[\s\-]?|0049[\s\-]?|0\d{2,5}[\s\-\/])\d[\d\s\-\/]{4,}', text):
        findings.append({"type": "Telefonnummer", "auto": True})
    if re.search(r'(geb\b\.?|geboren|geburtstag|geburtsdatum)', text, re.I) and \
       re.search(r'\b\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4}\b', text):
        findings.append({"type": "Geburtsdatum", "auto": True})
    if re.search(r'(schüler[in]?|lernende[r]?|kind|elternteil?|sohn|tochter|sus)\s+(von\s+)?[A-ZÄÖÜ][a-zäöüß]{2,}(\s+[A-ZÄÖÜ][a-zäöüß]{2,})?', text, re.I):
        findings.append({"type": "Möglicher Personenname", "auto": False})
    if re.search(r'\b(heißt|namens|vorname|nachname|familienname|name:)\s+[A-ZÄÖÜ][a-zäöüß]{2,}', text, re.I):
        findings.append({"type": "Möglicher Personenname", "auto": False})
    return findings

def anonymize_text(text):
    r = text
    r = re.sub(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', '[E-Mail]', r)
    r = re.sub(r'(\+49[\s\-]?|0049[\s\-]?|0\d{2,5}[\s\-\/])\d[\d\s\-\/]{4,}', '[Telefon]', r)
    if re.search(r'(geb\b\.?|geboren|geburtstag|geburtsdatum)', r, re.I):
        r = re.sub(r'\b\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4}\b', '[Datum]', r)
    return r

# ---------------------------------------------------------------------------
# Skill-Router (lädt passende skill.md ohne OpenClaw)
# ---------------------------------------------------------------------------
_skill_index_cache = None

def load_skill_index():
    global _skill_index_cache
    if _skill_index_cache is not None:
        return _skill_index_cache
    try:
        if SKILLS_INDEX.exists():
            _skill_index_cache = json.loads(SKILLS_INDEX.read_text("utf-8"))
        else:
            _skill_index_cache = []
    except Exception:
        _skill_index_cache = []
    return _skill_index_cache

def find_matching_skill(user_text):
    """Findet den ersten Skill, dessen Trigger im Usertext vorkommt."""
    skills = load_skill_index()
    text_lower = user_text.lower()
    best = None
    best_len = 0
    for skill in skills:
        for trigger in skill.get("triggers", []):
            if trigger.lower() in text_lower:
                if len(trigger) > best_len:
                    best = skill
                    best_len = len(trigger)
    return best

def load_skill_content(folder_name):
    """Liest eine skill.md aus skills/<folder>/."""
    skill_path = SKILLS_DIR / folder_name / "skill.md"
    if skill_path.exists():
        return skill_path.read_text("utf-8")
    return ""

def load_memory_context():
    """Lädt lehrerprofil.md + begleiter_gedaechtnis.md als Kontext."""
    parts = []
    profil = MEMORY_DIR / "lehrerprofil.md"
    begleiter = MEMORY_DIR / "begleiter_gedaechtnis.md"
    if profil.exists():
        parts.append(profil.read_text("utf-8"))
    if begleiter.exists():
        parts.append(begleiter.read_text("utf-8"))
    return "\n\n".join(parts)

# ---------------------------------------------------------------------------
# System-Prompt
# ---------------------------------------------------------------------------
def build_system_prompt(profile):
    asst_name = (profile or {}).get("assistant_name") or "Mila"
    teacher_name = (profile or {}).get("name") or ""
    lines = [
        f"Du bist {asst_name}, eine persönliche und vertraute Begleitung im Schulalltag einer deutschen Lehrkraft{teacher_name and ' namens ' + teacher_name or ''}.",
        "Du hilfst professionell-kollegial bei Unterrichtsplanung, Bewertungserstellung, Schülerkorrektur und Lehrplanfragen.",
        "",
        "## Deine Persönlichkeit",
        "- Du bist warmherzig, wertschätzend und hast einen leisen Humor – wie eine vertraute Kollegin im Lehrerzimmer.",
        "- Du fragst ab und zu nach, wie eine zuvor geplante Stunde gelaufen ist (nicht jedes Mal, aber wenn es passt).",
        "- Du erkennst an, wenn viel zu tun ist (Zeugniszeit, Elternsprechtag, vor den Ferien).",
        "- Du feierst kleine Meilensteine (\"Das war schon die 10. Stunde, die wir zusammen geplant haben! 🎉\").",
        "- Du nutzt Emojis dezent und passend 📚🍎✨ – nicht inflationär.",
        "- Am Freitag, vor den Ferien oder am Montagmorgen passt du deinen Ton entsprechend an.",
        "- Du bleibst immer professionell, aber du darfst auch mal einen kleinen Scherz machen – wie unter Kolleginnen.",
        "",
        "## Grundprinzipien",
        "- Du machst Vorschläge – die Lehrkraft entscheidet immer selbst.",
        "- Bewertungen immer als \"Vorschlag\" kennzeichnen.",
        "- AFB-Verteilung bei Aufgaben: ~30% AFB I (Reproduktion) / ~40% AFB II (Reorganisation) / ~30% AFB III (Transfer).",
        "- Zeitangaben in Stundenentwürfen: Einstieg max. 10 Min., Sicherung min. 5 Min.",
        "- Lehrplanbezüge ohne eindeutige Quelle mit [*] markieren.",
        "- Keine Schülernamen verwenden (DSGVO) – bei Bedarf SuS-01, SuS-02 etc.",
        "- Alle Antworten auf Deutsch.",
        "- Antworte strukturiert mit Markdown (##, - Listen, **fett**) für bessere Lesbarkeit.",
    ]
    if profile and isinstance(profile, dict) and len(profile) > 0:
        lines.append("")
        lines.append("## Lehrerprofil")
        if profile.get("name"):
            lines.append(f"- Name: {profile['name']}")
        if profile.get("bundesland"):
            lines.append(f"- Bundesland: {profile['bundesland']}")
        if profile.get("schulform") == "Gemeinschaftsschule":
            lines.append("- Schulform: Gemeinschaftsschule (kombiniert Gymnasium-Zweig & Regelschul-Zweig)")
            lines.append("- Beim Planen und Bewerten immer beide Zweige berücksichtigen.")
        elif profile.get("schulform"):
            lines.append(f"- Schulform: {profile['schulform']}")
        if profile.get("faecher") and len(profile.get("faecher", [])) > 0:
            lines.append(f"- Fächer & Klassen: {', '.join(profile['faecher'])}")
        if profile.get("besonderheiten"):
            lines.append(f"- Klassenbesonderheiten: {profile['besonderheiten']}")
        if profile.get("methoden"):
            lines.append(f"- Bevorzugte Methoden: {profile['methoden']}")

        # ── Stil-Präferenzen vom Avatar-Popover ──
        style_lines = []
        formality = profile.get("style_formality", "")
        detail = profile.get("style_detail", "")

        if formality == "locker":
            style_lines.append("- Du sprichst im kollegialen Du-Ton, herzlich und locker – wie eine vertraute Kollegin im Lehrerzimmer.")
        elif formality == "formal":
            style_lines.append("- Du antwortest sachlich-neutral und distanziert, im professionellen Beratungsstil.")

        if detail == "knapp":
            style_lines.append("- Du antwortest extrem knapp: Stichworte, Bullet Points, keine ausschweifenden Erklärungen. Kein Satz länger als nötig.")
        elif detail == "ausführlich":
            style_lines.append("- Du antwortest ausführlich: mit Begründungen, Beispielen und didaktischen Erläuterungen. Ganze Sätze, Prosa-Stil.")

        if style_lines:
            lines.append("")
            lines.append("## Gewünschter Antwortstil")
            lines.extend(style_lines)

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Lazy-geladene Heavy-Imports
# ---------------------------------------------------------------------------
_col = None
_ef  = None

def get_collection():
    global _col, _ef
    if _col is not None:
        return _col, _ef
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    _ef  = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    _col   = client.get_or_create_collection("lehrplaene", embedding_function=_ef)
    return _col, _ef

# ---------------------------------------------------------------------------
# PDF-Hilfsfunktionen
# ---------------------------------------------------------------------------
def extract_pdf_text(path):
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(str(path))
        if text and text.strip():
            return text
    except Exception:
        pass
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(str(path))
        return "\n".join(pytesseract.image_to_string(img, lang="deu") for img in images)
    except Exception:
        return ""

def chunk_text(text, max_chars=900, overlap=150):
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            for sep in (".\n", ". ", "\n\n", "\n"):
                pos = text.rfind(sep, start + overlap, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        chunk = text[start:end].strip()
        if len(chunk) > 60:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def parse_multipart(body, boundary):
    files = []
    sep = ("--" + boundary).encode()
    for part in body.split(sep)[1:]:
        if not part.strip() or part.strip() == b"--":
            continue
        if b"\r\n\r\n" not in part:
            continue
        raw_headers, content = part.split(b"\r\n\r\n", 1)
        if content.endswith(b"\r\n"):
            content = content[:-2]
        headers = raw_headers.decode("utf-8", errors="replace")
        filename = None
        for line in headers.split("\r\n"):
            if "filename=" in line:
                for seg in line.split(";"):
                    seg = seg.strip()
                    if seg.lower().startswith("filename="):
                        filename = seg[9:].strip('"')
        if filename:
            files.append((os.path.basename(filename), content))
    return files

# ---------------------------------------------------------------------------
# RAG-Kontext
# ---------------------------------------------------------------------------
def search_rag(query, limit=4):
    try:
        col, _ = get_collection()
        n = col.count()
        if n == 0:
            return ""
        res = col.query(query_texts=[query], n_results=min(limit, n))
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        hits = [
            {"text": d, "source": m.get("source", ""), "distance": round(dist, 3)}
            for d, m, dist in zip(docs, metas, dists)
            if dist < 1.3
        ]
        if not hits:
            return ""
        blocks = [f"[Quelle: {h['source']}]\n{h['text']}" for h in hits]
        return "\n\n## Relevante Lehrplaninhalte (automatisch eingeblendet)\n" + "\n\n---\n\n".join(blocks)
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# Ollama-Status-Cache
# ---------------------------------------------------------------------------
_ollama_online = False
_ollama_last_check = 0

def check_ollama():
    global _ollama_online, _ollama_last_check
    now = time.time()
    if now - _ollama_last_check < 10:
        return _ollama_online
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            _ollama_online = bool(data.get("models"))
    except Exception:
        _ollama_online = False
    _ollama_last_check = now
    return _ollama_online

# ---------------------------------------------------------------------------
# DSGVO-Modell-Routing – Skill-basierte Erzwingung lokaler Modelle
# ---------------------------------------------------------------------------
DSGVO_PFLICHT_LOKAL = [
    "schuelerarbeit_bewerten",   # Schülerarbeiten enthalten ggf. Namen
    "zeugnis_formulieren",       # Schülerbezogene Bewertungen
    "foerderplan_erstellen",     # Individuelle Förderdaten
    "lerntagebuch_feedback",     # SuS-Reflexionen
    "klassenstatistik",          # Aggregierte Schülerdaten
]

def route_model(skill_name: str, user_preferred_model: str) -> str:
    """
    Gibt das tatsächlich zu verwendende Modell zurück.
    Bei DSGVO-pflichtigen Skills wird IMMER auf Ollama geroutet,
    unabhängig von der Nutzerpräferenz.
    """
    if skill_name and skill_name in DSGVO_PFLICHT_LOKAL:
        return "ollama"  # Lokales Modell erzwingen
    return user_preferred_model  # Nutzerwahl respektieren

# ---------------------------------------------------------------------------
# LLM-Call (Streaming) – serverseitiger Proxy
# ---------------------------------------------------------------------------
def stream_llm(messages, profile, settings, skill_content="", rag_context="", wfile=None, skill_name=None):
    """
    Ruft LLM an und streamt Antwort per SSE an wfile.
    Entscheidet Provider (openrouter/ollama) basierend auf DSGVO-Prüfung.
    """
    is_ollama = settings.get("provider") == "ollama"
    ollama_model = settings.get("ollamaModel") or "gemma3:4b"
    model = settings.get("model") or "deepseek/deepseek-chat"
    api_key = settings.get("apiKey") or get_api_key()

    # DSGVO-Skill-basiertes Routing (VOR content-basierter Prüfung)
    routed_provider = route_model(skill_name, "ollama" if is_ollama else "openrouter")
    dsgvo_routing_active = False
    if routed_provider == "ollama" and not is_ollama:
        # DSGVO-Skill: lokales Modell erzwungen
        dsgvo_routing_active = True
        if check_ollama():
            is_ollama = True
            _send_sse(wfile, {"type": "dsgvo_warning", "message": "🔒 Lokales Modell (DSGVO): Dieser Skill erfordert lokale Verarbeitung – verwende Ollama.", "routing": "dsgvo_local"})
        else:
            # Ollama offline + DSGVO-Skill → KEIN Cloud-Fallback
            _send_sse(wfile, {"type": "error", "message": "🔒 DSGVO-Pflicht: Dieser Skill (Klasse: " + skill_name + ") muss lokal verarbeitet werden. Ollama ist nicht verfügbar. Bitte starte Ollama und versuche es erneut."})
            _send_sse(wfile, {"type": "done"})
            return

    # DSGVO-Prüfung: Letzte User-Nachricht prüfen (nur wenn nicht bereits durch Skill geroutet)
    if not dsgvo_routing_active:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("text", m.get("content", ""))
                break

        findings = detect_personal_data(last_user_msg)
        has_auto_detectable = any(f["auto"] for f in findings)
        has_any_findings = len(findings) > 0

        # DSGVO-Modus: erzwinge lokal wenn personenbezogene Daten erkannt wurden
        force_local = False
        if has_auto_detectable:
            force_local = True
            if not check_ollama():
                # Kein Ollama verfügbar → Daten schwärzen, dann Cloud
                anon_text = anonymize_text(last_user_msg)
                for m in messages:
                    if m.get("role") == "user" and m.get("text"):
                        m["text"] = anon_text
                force_local = False
                _send_sse(wfile, {"type": "dsgvo_warning", "message": "Personenbezogene Daten erkannt und automatisch geschwärzt. Bitte überprüfen.", "findings": findings})
            else:
                _send_sse(wfile, {"type": "dsgvo_warning", "message": "Personenbezogene Daten erkannt – verwende lokales Modell (DSGVO-konform).", "findings": findings})
        elif has_any_findings:
            _send_sse(wfile, {"type": "dsgvo_warning", "message": "Mögliche personenbezogene Daten erkannt. Bitte prüfen und ggf. durch SuS-01 etc. ersetzen.", "findings": findings})

        # Provider erzwingen falls nötig
        if force_local:
            is_ollama = True

    # System-Prompt bauen
    system_content = build_system_prompt(profile)
    if skill_content:
        system_content += "\n\n## Aktiver Skill\n" + skill_content
    if rag_context:
        system_content += rag_context

    api_messages = [{"role": "system", "content": system_content}]
    for m in messages:
        role = "assistant" if m.get("role") == "bot" else "user"
        content = m.get("text", m.get("content", ""))
        if content and content.strip():
            api_messages.append({"role": role, "content": content})

    # Provider-Endpunkt
    if is_ollama:
        endpoint = "http://localhost:11434/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        body = {"model": ollama_model, "messages": api_messages, "stream": True}
        _send_sse(wfile, {"type": "provider", "provider": "ollama"})
    elif settings.get("provider") == "custom":
        custom_endpoint = settings.get("customEndpoint", "").strip()
        custom_apikey = settings.get("customApiKey", "").strip()
        custom_model = settings.get("customModel", "gpt-3.5-turbo").strip()
        if not custom_endpoint:
            _send_sse(wfile, {"type": "error", "message": "Custom-Endpoint nicht konfiguriert. Bitte in den Einstellungen eintragen."})
            _send_sse(wfile, {"type": "done"})
            return
        endpoint = custom_endpoint
        headers = {"Content-Type": "application/json"}
        if custom_apikey:
            headers["Authorization"] = f"Bearer {custom_apikey}"
        body = {"model": custom_model, "messages": api_messages, "stream": True}
        _send_sse(wfile, {"type": "provider", "provider": "custom"})
    else:
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8788",
            "X-Title": "TeacherAssist",
        }
        body = {"model": model, "messages": api_messages, "stream": True}
        _send_sse(wfile, {"type": "provider", "provider": "openrouter"})

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            buffer = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        _send_sse(wfile, {"type": "done"})
                        return
                    try:
                        parsed = json.loads(data)
                        content = parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            _send_sse(wfile, {"type": "chunk", "text": content})
                        if parsed.get("usage"):
                            _send_sse(wfile, {"type": "usage", "usage": parsed["usage"]})
                    except Exception:
                        pass
    except Exception as e:
        _send_sse(wfile, {"type": "error", "message": str(e)})
    finally:
        _send_sse(wfile, {"type": "done"})

def _send_sse(wfile, data):
    """Sendet ein SSE-Event an den Client."""
    if wfile is None:
        return
    try:
        line = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        wfile.write(line.encode("utf-8"))
        wfile.flush()
    except Exception:
        pass

# ---------------------------------------------------------------------------
# HTTP-Handler
# ---------------------------------------------------------------------------
class ToolHandler(http.server.BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    # ---- GET ----------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == "/health":
            self._json({"status": "ok", "version": "1.1", "ollama": check_ollama()})

        elif path == "/settings":
            self._json(load_settings())

        elif path == "/collections":
            try:
                col, _ = get_collection()
                self._json({"chunks": col.count()})
            except Exception as e:
                self._json({"chunks": 0, "error": str(e)})

        elif path == "/backup":        self._backup()
        elif path == "/list-raster":   self._list_raster()
        elif path == "/memory-list":   self._list_memory()
        elif path == "/memory-read":
            file_param = parse_qs(parsed.query).get("file", [""])[0]
            self._read_memory_file(file_param)
        elif path == "/memory-versions":
            file_param = parse_qs(parsed.query).get("file", [""])[0]
            self._list_versions(file_param)

        elif path == "/search":
            params = parse_qs(parsed.query)
            query  = params.get("q", [""])[0].strip()
            limit  = min(int(params.get("limit", ["4"])[0]), 8)
            if not query:
                self._json({"results": []})
                return
            try:
                col, _ = get_collection()
                n = col.count()
                if n == 0:
                    self._json({"results": []})
                    return
                res = col.query(query_texts=[query], n_results=min(limit, n))
                docs  = res["documents"][0]  if res["documents"]  else []
                metas = res["metadatas"][0]  if res["metadatas"]  else []
                dists = res["distances"][0]  if res["distances"]  else []
                hits  = [
                    {"text": d, "source": m.get("source", ""), "distance": round(dist, 3)}
                    for d, m, dist in zip(docs, metas, dists)
                    if dist < 1.3
                ]
                self._json({"results": hits})
            except Exception as e:
                self._json({"results": [], "error": str(e)})
        else:
            self.send_error(404)

    # ---- POST ---------------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if   path == "/chat":            self._chat()
        elif path == "/upload":          self._upload()
        elif path == "/ingest":          self._ingest()
        elif path == "/clear":           self._clear()
        elif path == "/download-url":    self._download_url()
        elif path == "/settings":        self._save_settings()
        elif path == "/save-raster":     self._save_raster()
        elif path == "/restore":         self._restore()
        elif path == "/memory-write":    self._write_memory_file()
        elif path == "/memory-restore-version": self._restore_version()
        elif path == "/ollama-pull":     self._ollama_pull()
        elif path == "/shutdown":       self._shutdown()
        elif path == "/ocr-image":       self._ocr_image()
        elif path == "/session-summary": self._session_summary()
        else: self.send_error(404)

    # ---- NEU: /chat (LLM-Proxy mit DSGVO-Filter + Skill-Router) ------------
    def _chat(self):
        try:
            data = json.loads(self._body().decode("utf-8"))
        except Exception:
            self._json({"error": "Ungültiges JSON"}, 400)
            return

        messages = data.get("messages", [])
        profile  = data.get("profile", {})
        settings = load_settings()
        # API-Key aus Request-Body überschreibt gespeicherten Key (kein Race-Condition)
        if data.get("apiKey"):
            settings["apiKey"] = data["apiKey"]

        # Skill-Router: passenden Skill finden
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("text", m.get("content", ""))
                break

        skill = find_matching_skill(last_user)
        skill_content = ""
        if skill:
            skill_content = load_skill_content(skill["folder"])
            if not skill_content:
                # Fallback: alle Memory-Dateien
                skill_content = load_memory_context()

        # RAG-Kontext
        rag_context = search_rag(last_user)

        # SSE-Streaming-Antwort
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        if skill:
            _send_sse(self.wfile, {"type": "skill", "name": skill["name"]})

        stream_llm(
            messages=messages,
            profile=profile,
            settings=settings,
            skill_content=skill_content,
            rag_context=rag_context,
            wfile=self.wfile,
            skill_name=skill["name"] if skill else None,
        )

    # ---- Bestehende Endpunkte (unverändert) ---------------------------------
    def _upload(self):
        ct = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ct:
            self._json({"error": "multipart/form-data erwartet"}, 400)
            return
        boundary = ""
        for seg in ct.split(";"):
            seg = seg.strip()
            if seg.startswith("boundary="):
                boundary = seg[9:].strip('"')
        body  = self._body()
        files = parse_multipart(body, boundary)
        saved = []
        for name, content in files:
            dest = UPLOAD_DIR / name
            dest.write_bytes(content)
            saved.append(str(dest))
        self._json({"saved": saved})

    def _ingest(self):
        data   = json.loads(self._body().decode("utf-8"))
        path   = data.get("path", "")
        source = data.get("source", Path(path).name if path else "unbekannt")
        if not path or not os.path.isfile(path):
            self._json({"error": f"Datei nicht gefunden: {path}"}, 400)
            return
        try:
            text = extract_pdf_text(Path(path))
            if not text.strip():
                self._json({"error": "Kein Text aus PDF extrahierbar"}, 400)
                return
            chunks = chunk_text(text)
            if not chunks:
                self._json({"error": "Text zu kurz zum Indexieren"}, 400)
                return
            col, _ = get_collection()
            old = col.get(where={"source": source})
            if old["ids"]:
                col.delete(ids=old["ids"])
            ids       = [f"{source}::{i}" for i in range(len(chunks))]
            metadatas = [{"source": source, "chunk": i} for i in range(len(chunks))]
            col.add(documents=chunks, ids=ids, metadatas=metadatas)
            self._json({
                "success": True,
                "source":  source,
                "chunks":  len(chunks),
                "words":   len(text.split()),
            })
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _download_url(self):
        data   = json.loads(self._body().decode("utf-8"))
        url    = data.get("url", "").strip()
        source = data.get("source", "").strip()
        if not url:
            self._json({"error": "Keine URL angegeben"}, 400)
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            self._json({"error": "Nur HTTP/HTTPS-URLs erlaubt"}, 400)
            return
        try:
            filename = source or url.split("/")[-1].split("?")[0] or "lehrplan.pdf"
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            dest = UPLOAD_DIR / filename
            req  = urllib.request.Request(url, headers={"User-Agent": "TeacherAssist/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            self._json({"saved": [str(dest)], "filename": filename})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _save_settings(self):
        try:
            data = json.loads(self._body().decode("utf-8"))
            # Erlaube apiKey im Server zu speichern (kommt vom Frontend-Settings)
            allowed = {}
            for k in ("provider", "ollamaModel", "model", "apiKey", "customEndpoint", "customApiKey", "customModel"):
                if k in data:
                    allowed[k] = data[k]
            SETTINGS_FILE.write_text(json.dumps(allowed, ensure_ascii=False), "utf-8")
            self._json({"success": True})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _clear(self):
        try:
            col, _ = get_collection()
            ids = col.get()["ids"]
            if ids:
                col.delete(ids=ids)
            self._json({"success": True, "deleted": len(ids)})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _list_raster(self):
        raster_dir = BASE_DIR / "memory" / "bewertungsraster"
        rasters = []
        if raster_dir.exists():
            for f in sorted(raster_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
                if f.name == "README.md":
                    continue
                stat = f.stat()
                label = f.stem.replace("_", " ").title()
                rasters.append({
                    "filename": f.name,
                    "stem":     f.stem,
                    "label":    label,
                    "modified": stat.st_mtime,
                    "size_bytes": stat.st_size,
                })
        self._json({"rasters": rasters})

    def _save_raster(self):
        data   = json.loads(self._body().decode("utf-8"))
        content = data.get("content", "").strip()
        fach    = data.get("fach", "").strip()
        klasse  = data.get("klasse", "").strip()
        thema   = data.get("thema", "").strip()
        if not (fach and klasse and thema):
            self._json({"error": "fach, klasse und thema erforderlich"}, 400)
            return
        slug = f"{fach}_{klasse}_{thema}".lower()
        slug = re.sub(r"[^\w]", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        raster_dir = BASE_DIR / "memory" / "bewertungsraster"
        raster_dir.mkdir(parents=True, exist_ok=True)
        filepath = raster_dir / f"{slug}.md"
        self._rotate_backups(filepath)
        filepath.write_text(content, encoding="utf-8")
        self._json({"success": True, "filename": f"{slug}.md"})

    def _backup(self):
        if not MEMORY_DIR.exists():
            self._json({"error": "memory/-Verzeichnis nicht gefunden"}, 404)
            return
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(MEMORY_DIR.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(BASE_DIR))
            data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="teacherAssist_memory_backup.zip"')
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _restore(self):
        ct = self.headers.get("Content-Type", "")
        body = self._body()
        try:
            if "multipart/form-data" in ct:
                boundary = ""
                for seg in ct.split(";"):
                    seg = seg.strip()
                    if seg.startswith("boundary="):
                        boundary = seg[9:].strip('"')
                files = parse_multipart(body, boundary)
                if not files:
                    self._json({"error": "Keine Datei übermittelt"}, 400)
                    return
                _, zip_data = files[0]
            else:
                zip_data = body

            buf = io.BytesIO(zip_data)
            if not zipfile.is_zipfile(buf):
                self._json({"error": "Datei ist kein gültiges ZIP-Archiv"}, 400)
                return

            restored = []
            with zipfile.ZipFile(buf, "r") as zf:
                for name in zf.namelist():
                    norm = name.replace("\\", "/")
                    if not (norm.startswith("memory/") or norm.startswith("./memory/")):
                        continue
                    dest = BASE_DIR / norm
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(zf.read(name))
                    restored.append(norm)
            self._json({"success": True, "restored": len(restored), "files": restored})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _list_memory(self):
        files = []
        if MEMORY_DIR.exists():
            for f in sorted(MEMORY_DIR.rglob("*.md"), key=lambda p: str(p)):
                rel = str(f.relative_to(MEMORY_DIR)).replace("\\", "/")
                files.append({
                    "path": rel,
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                })
        self._json({"files": files})

    def _read_memory_file(self, file_path):
        try:
            target = (MEMORY_DIR / file_path).resolve()
            if not str(target).startswith(str(MEMORY_DIR.resolve())):
                self._json({"error": "Zugriff verweigert"}, 403)
                return
            if not target.exists():
                self._json({"error": "Datei nicht gefunden"}, 404)
                return
            self._json({"content": target.read_text(encoding="utf-8"), "path": file_path})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _write_memory_file(self):
        try:
            data = json.loads(self._body().decode("utf-8"))
            file_path = data.get("path", "").strip()
            content   = data.get("content", "")
            if not file_path.endswith(".md"):
                self._json({"error": "Nur .md-Dateien erlaubt"}, 400)
                return
            target = (MEMORY_DIR / file_path).resolve()
            if not str(target).startswith(str(MEMORY_DIR.resolve())):
                self._json({"error": "Zugriff verweigert"}, 403)
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            self._rotate_backups(target)
            target.write_text(content, encoding="utf-8")
            self._json({"success": True, "path": file_path})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    @staticmethod
    def _rotate_backups(filepath):
        if not filepath.exists():
            return
        bak3 = Path(str(filepath) + '.bak3')
        bak2 = Path(str(filepath) + '.bak2')
        bak1 = Path(str(filepath) + '.bak1')
        if bak2.exists(): shutil.copy2(str(bak2), str(bak3))
        if bak1.exists(): shutil.copy2(str(bak1), str(bak2))
        shutil.copy2(str(filepath), str(bak1))

    def _list_versions(self, file_path):
        import datetime
        try:
            target = (MEMORY_DIR / file_path).resolve()
            if not str(target).startswith(str(MEMORY_DIR.resolve())):
                self._json({"error": "Zugriff verweigert"}, 403)
                return
            versions = []
            for i in range(1, 4):
                bak = Path(str(target) + f'.bak{i}')
                if bak.exists():
                    stat = bak.stat()
                    versions.append({
                        "version": i,
                        "modified": stat.st_mtime,
                        "label": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                        "size": stat.st_size,
                    })
            self._json({"versions": versions})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _restore_version(self):
        try:
            data = json.loads(self._body().decode("utf-8"))
            file_path = data.get("path", "").strip()
            version = int(data.get("version", 0))
            if not file_path.endswith(".md") or version not in (1, 2, 3):
                self._json({"error": "Ungültige Anfrage"}, 400)
                return
            target = (MEMORY_DIR / file_path).resolve()
            if not str(target).startswith(str(MEMORY_DIR.resolve())):
                self._json({"error": "Zugriff verweigert"}, 403)
                return
            bak = Path(str(target) + f'.bak{version}')
            if not bak.exists():
                self._json({"error": "Version nicht gefunden"}, 404)
                return
            self._rotate_backups(target)
            shutil.copy2(str(bak), str(target))
            self._json({"success": True, "content": target.read_text(encoding="utf-8")})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _ocr_image(self):
        ct  = self.headers.get("Content-Type", "")
        body = self._body()
        try:
            if "multipart/form-data" in ct:
                boundary = ""
                for seg in ct.split(";"):
                    seg = seg.strip()
                    if seg.startswith("boundary="):
                        boundary = seg[9:].strip('"')
                files = parse_multipart(body, boundary)
                if not files:
                    self._json({"error": "Kein Bild übermittelt"}, 400)
                    return
                name, content = files[0]
            else:
                name, content = "image.jpg", body

            suffix = '.jpg' if name.lower().endswith(('.jpg', '.jpeg')) else '.png'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(content)
                tmp_path = f.name

            # ── VLM-Pfad: Versuche Ollama Vision-Modell für Handschrift ──
            if check_ollama():
                try:
                    import base64
                    with open(tmp_path, "rb") as bf:
                        b64 = base64.b64encode(bf.read()).decode("ascii")
                    # Nutze das erste verfügbare VLM oder das aktuelle Ollama-Modell
                    settings = load_settings()
                    vision_model = ""
                    # Prüfe ob ein Vision-Modell verfügbar ist
                    req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        tags_data = json.loads(resp.read())
                        models = [m.get("name", "") for m in tags_data.get("models", [])]
                        for vm in ["granite3.2-vision", "minicpm-v", "gemma3:12b", "llava", "bakllava"]:
                            if any(m.startswith(vm) for m in models):
                                vision_model = next(m for m in models if m.startswith(vm))
                                break
                    if not vision_model:
                        vision_model = settings.get("ollamaModel", "gemma3:4b")

                    vlm_body = {
                        "model": vision_model,
                        "prompt": "Lies den Text auf diesem Bild. Gib nur den erkannten Text zurück, keine zusätzlichen Erklärungen. Wenn es sich um handgeschriebenen Text handelt, gib ihn so genau wie möglich wieder. Erwähne nichts über das Bild selbst.",
                        "images": [b64],
                        "stream": False,
                    }
                    vlm_req = urllib.request.Request(
                        "http://localhost:11434/api/generate",
                        data=json.dumps(vlm_body).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(vlm_req, timeout=60) as vlm_resp:
                        vlm_text = ""
                        for line in vlm_resp:
                            try:
                                p = json.loads(line)
                                vlm_text += p.get("response", "")
                            except Exception:
                                pass
                        vlm_text = vlm_text.strip()
                        if vlm_text and len(vlm_text) > 5:
                            try: os.unlink(tmp_path)
                            except: pass
                            self._json({"text": vlm_text, "method": "ollama", "model": vision_model})
                            return
                except Exception:
                    pass  # VLM fehlgeschlagen → Fallback zu Tesseract

            # ── Tesseract-Fallback ──
            try:
                import pytesseract
                from PIL import Image
            except Exception:
                try: os.unlink(tmp_path)
                except: pass
                self._json({"error": "OCR nicht verfügbar – bitte Tesseract installieren oder Ollama mit VLM starten."}, 500)
                return

            try:
                img  = Image.open(tmp_path)
                text = pytesseract.image_to_string(img, lang="deu")
                os.unlink(tmp_path)
            except Exception:
                try: os.unlink(tmp_path)
                except: pass
                raise
            if not text.strip():
                self._json({"error": "Kein Text erkannt. Bitte ein deutlicheres Foto machen."})
                return
            self._json({"text": text.strip()})
        except Exception as e:
            self._json({"error": f"OCR fehlgeschlagen: {str(e)}"}, 500)

    def _ollama_pull(self):
        """Lädt ein Ollama-Modell herunter und streamt den Fortschritt per SSE."""
        try:
            data = json.loads(self._body().decode("utf-8"))
        except Exception:
            self._json({"error": "Ungültiges JSON"}, 400)
            return
        model = data.get("model", "").strip()
        if not model:
            self._json({"error": "Kein Modellname angegeben"}, 400)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        try:
            proc = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                    if "completed" in parsed and "total" in parsed:
                        pct = int(parsed["completed"] / max(parsed["total"], 1) * 100)
                        _send_sse(self.wfile, {"type": "progress", "percent": pct, "status": parsed.get("status", "downloading")})
                    elif "status" in parsed:
                        _send_sse(self.wfile, {"type": "status", "message": parsed["status"]})
                except json.JSONDecodeError:
                    _send_sse(self.wfile, {"type": "status", "message": line})

            proc.wait()
            if proc.returncode == 0:
                _send_sse(self.wfile, {"type": "done", "success": True, "model": model})
            else:
                _send_sse(self.wfile, {"type": "error", "message": f"ollama pull fehlgeschlagen (code {proc.returncode})"})
        except FileNotFoundError:
            _send_sse(self.wfile, {"type": "error", "message": "Ollama ist nicht installiert. Bitte von ollama.com/download herunterladen."})
        except Exception as e:
            _send_sse(self.wfile, {"type": "error", "message": str(e)})

    def _shutdown(self):
        """Beendet den Tool-Server und den Web-Server."""
        self._json({"success": True, "message": "TeacherAssist wird beendet."})
        # Web-Server auf Port 8788 beenden
        try:
            subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq TeacherAssist Web*"], capture_output=True)
        except Exception:
            pass
        # Browser-Fenster, die diesen Server referenzieren, bleiben offen – nur Server sterben
        import threading
        def _exit():
            time.sleep(0.5)
            os._exit(0)
        threading.Thread(target=_exit, daemon=True).start()

    def _session_summary(self):
        """Fasst den Chat-Verlauf zusammen und speichert ihn in vergangene_stunden.md."""
        try:
            data = json.loads(self._body().decode("utf-8"))
        except Exception:
            self._json({"error": "Ungültiges JSON"}, 400)
            return

        messages = data.get("messages", [])
        profile  = data.get("profile", {})
        settings = load_settings()
        if data.get("apiKey"):
            settings["apiKey"] = data["apiKey"]

        # Nur User-Nachrichten extrahieren (ohne System/Bot)
        user_texts = []
        for m in messages:
            if m.get("role") == "user":
                text = m.get("text", m.get("content", "")).strip()
                if text:
                    user_texts.append(text)

        if not user_texts:
            self._json({"error": "Keine User-Nachrichten zum Zusammenfassen"}, 400)
            return

        # Zusammenfassung per LLM generieren
        summary_prompt = (
            "Fasse den folgenden Chat-Verlauf einer Lehrkraft mit ihrem KI-Assistenten "
            "in 3-5 Sätzen zusammen. Was war das Thema? Welche Fächer/Klassen wurden besprochen? "
            "Welche Ergebnisse/Pläne wurden erarbeitet? "
            "Schreibe im Stil eines Verlaufsprotokolls für die Lehrkraft.\n\n"
            + "\n".join(f"- {t}" for t in user_texts[-20:])  # max 20 Nachrichten
        )

        summary = ""
        try:
            is_ollama = settings.get("provider") == "ollama"
            ollama_model = settings.get("ollamaModel") or "gemma3:4b"
            model = settings.get("model") or "deepseek/deepseek-chat"
            api_key = settings.get("apiKey") or get_api_key()

            if is_ollama:
                endpoint = "http://localhost:11434/v1/chat/completions"
                headers = {"Content-Type": "application/json"}
                body = {"model": ollama_model, "messages": [{"role": "user", "content": summary_prompt}], "stream": False}
            else:
                endpoint = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:8788",
                    "X-Title": "TeacherAssist",
                }
                body = {"model": model, "messages": [{"role": "user", "content": summary_prompt}], "stream": False}

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            summary = f"Chat-Sitzung: {user_texts[0][:100]}…"

        if not summary.strip():
            summary = f"Chat-Sitzung: {user_texts[0][:100]}…"

        # In vergangene_stunden.md speichern
        now = time.strftime("%d.%m.%Y %H:%M")
        entry = f"\n\n## {now}\n{summary.strip()}\n"

        vergangene = MEMORY_DIR / "vergangene_stunden.md"
        if vergangene.exists():
            existing = vergangene.read_text("utf-8").strip()
            lines = existing.split("\n")
            if len(lines) > 300:
                existing = "\n".join(lines[-300:])
            vergangene.write_text(existing + entry, encoding="utf-8")
        else:
            vergangene.parent.mkdir(parents=True, exist_ok=True)
            vergangene.write_text(f"# Vergangene Stunden – Verlaufsprotokoll\n\nErstellt am {now}\n{entry}", encoding="utf-8")

        self._json({"success": True, "summary": summary.strip()})

    def log_message(self, *_):
        pass

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port   = 8789
    server = http.server.ThreadingHTTPServer(("", port), ToolHandler)
    print(f"TeacherAssist Tool-Server -> http://localhost:{port}", flush=True)
    server.serve_forever()