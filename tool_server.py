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
import hashlib
import html
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import zipfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

from teacherassist_core.documents import download_pdf as secure_download_pdf
from teacherassist_core.documents import extract_pdf_text as secure_extract_pdf_text
from teacherassist_core.privacy import (
    SENSITIVE_SKILLS,
    anonymize_text,
    decide_privacy,
    findings_for,
    is_trusted_loopback_endpoint,
    minimize_cloud_profile,
)
from teacherassist_core.runtime import (
    CredentialStore,
    RuntimePaths,
    SettingsStore,
    capability_status,
)
from teacherassist_core.security import (
    PUBLIC_PATHS,
    SessionManager,
    valid_browser_source,
    valid_host,
    validate_remote_url,
)
from teacherassist_core.skills import SkillRegistry
from teacherassist_core.storage import EncryptedStateStore, PersistenceUnavailable

# Hardened runtime services are kept separate from the HTTP adapter.

BASE_DIR      = Path(__file__).parent.resolve()
RUNTIME_PATHS = RuntimePaths.from_environment(BASE_DIR)
RUNTIME_PATHS.ensure(BASE_DIR / "memory")
UPLOAD_DIR    = RUNTIME_PATHS.uploads
CHROMA_DIR    = RUNTIME_PATHS.chroma
EXPORT_DIR    = RUNTIME_PATHS.exports
LOG_DIR       = RUNTIME_PATHS.logs
SETTINGS_FILE = RUNTIME_PATHS.settings
LEGACY_SETTINGS_FILE = BASE_DIR / "settings.json"
SKILLS_DIR    = BASE_DIR / "skills"
MEMORY_DIR    = RUNTIME_PATHS.memory
SKILLS_INDEX  = BASE_DIR / "skills_index.json"
VALID_PROVIDERS = {"openrouter", "ollama", "custom"}
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_CHAT_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_RESTORE_BYTES = 100 * 1024 * 1024
MAX_RESTORE_EXPANDED_BYTES = 250 * 1024 * 1024
MAX_RESTORE_FILES = 1000

CREDENTIALS = CredentialStore()
SETTINGS_STORE = SettingsStore(SETTINGS_FILE, CREDENTIALS)
SESSIONS = SessionManager()
SKILL_REGISTRY = SkillRegistry(SKILLS_DIR, SKILLS_INDEX)
STATE_STORE = EncryptedStateStore(RUNTIME_PATHS.encrypted_state, CREDENTIALS.get_or_create_data_key())

logger = logging.getLogger("tool_server")
if not logger.handlers:
    _h = RotatingFileHandler(LOG_DIR / "tool_server.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

def apply_request_overrides(settings, data):
    """Apply non-persistent per-request provider/model overrides from the UI."""
    provider = data.get("providerOverride")
    if provider in VALID_PROVIDERS:
        settings["provider"] = provider

    for request_key, settings_key in (
        ("modelOverride", "model"),
        ("ollamaModelOverride", "ollamaModel"),
        ("customEndpoint", "customEndpoint"),
        ("customModel", "customModel"),
    ):
        value = data.get(request_key)
        if isinstance(value, str) and value.strip():
            settings[settings_key] = value.strip()

    return settings

def memory_zip_destination(name):
    """Return a safe restore destination below memory/, or None for ignored entries."""
    norm = name.replace("\\", "/").lstrip("/")
    if norm.startswith("./"):
        norm = norm[2:]
    if not norm.startswith("memory/") or norm.endswith("/"):
        return None

    rel = norm[len("memory/"):]
    if not rel:
        return None

    dest = (MEMORY_DIR / rel).resolve()
    memory_root = MEMORY_DIR.resolve()
    try:
        dest.relative_to(memory_root)
    except ValueError:
        raise ValueError(f"Unsicherer ZIP-Pfad: {name}")
    return dest, "memory/" + rel

def safe_export_name(title, fmt):
    base = (title or "teacherassist-export").strip().lower()
    base = re.sub(r"[^\wäöüÄÖÜß-]+", "_", base, flags=re.I)
    base = re.sub(r"_+", "_", base).strip("_")[:60] or "teacherassist-export"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{base}.{fmt}"

def markdown_to_export_html(content, title="TeacherAssist Export"):
    text = html.escape(content or "")
    text = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", text, flags=re.M)
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.M)
    text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.M)
    text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    paragraphs = []
    for block in re.split(r"\n{2,}", text):
        block = block.strip()
        if not block:
            continue
        if block.startswith(("<h1", "<h2", "<h3", "<h4")):
            paragraphs.append(block)
        else:
            paragraphs.append(f"<p>{block.replace(chr(10), '<br>')}</p>")
    body = "\n".join(paragraphs)
    safe_title = html.escape(title or "TeacherAssist Export")
    today = time.strftime("%d.%m.%Y")
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{safe_title}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;max-width:820px;margin:0 auto;padding:28px;color:#222;font-size:15px;line-height:1.65}}
h1{{font-size:1.55em;border-bottom:2px solid #333;padding-bottom:6px}}
h2{{font-size:1.25em;border-bottom:1px solid #eee;padding-bottom:4px;margin-top:1.5em}}
p{{margin:.75em 0}}
.footer{{margin-top:2em;font-size:12px;color:#777;border-top:1px solid #eee;padding-top:8px}}
</style>
</head>
<body>
{body}
<div class="footer">Erstellt mit TeacherAssist · Exportiert am {today}</div>
</body>
</html>"""

STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.jsx": "app.jsx",
    "/api-client.js": "api-client.js",
    "/components.jsx": "components.jsx",
    "/tweaks-panel.jsx": "tweaks-panel.jsx",
    "/manifest.json": "manifest.json",
    "/service-worker.js": "service-worker.js",
    "/teacherassist.ico": "teacherassist.ico",
    "/favicon.ico": "favicon.ico",
}
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".jsx": "text/javascript; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".ico": "image/x-icon",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}

# ---------------------------------------------------------------------------
# Konfiguration laden
# ---------------------------------------------------------------------------
def load_settings():
    settings = SETTINGS_STORE.load()
    settings["apiKey"] = CREDENTIALS.get(CredentialStore.OPENROUTER)
    settings["customApiKey"] = CREDENTIALS.get(CredentialStore.CUSTOM)
    return settings

def get_api_key():
    """Read the OpenRouter key without exposing it through the HTTP API."""
    return CREDENTIALS.get(CredentialStore.OPENROUTER)

# ---------------------------------------------------------------------------
# DSGVO-Filter (serverseitig – nicht umgehbar)
# ---------------------------------------------------------------------------
def detect_personal_data(text):
    labels = {
        "email": "E-Mail-Adresse",
        "phone": "Telefonnummer",
        "birth_date": "Geburtsdatum",
        "student_context": "Schülerbezogener Kontext",
        "person_name": "Personenname",
        "student_identifier": "Schülerkennung",
    }
    return [{"type": labels.get(name, name), "auto": True} for name in sorted(findings_for(text))]

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
    """Return a legacy-shaped record from the validated registry."""
    skill = SKILL_REGISTRY.match(user_text)
    return {"name": skill.skill_id, "folder": skill.folder} if skill else None

def load_skill_content(folder_name):
    skill = SKILL_REGISTRY.get(folder_name)
    return skill.content if skill else ""

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
    return secure_extract_pdf_text(Path(path))

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
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
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
            return ("", [])
        res = col.query(query_texts=[query], n_results=min(limit, n))
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        hits = [
            {
                "text": d,
                "source": m.get("source", ""),
                "distance": round(dist, 3),
                "classification": m.get("classification", "unknown"),
            }
            for d, m, dist in zip(docs, metas, dists)
            if dist < 1.3
        ]
        if not hits:
            return ("", [])
        blocks = [f"[Quelle: {h['source']}]\n{h['text']}" for h in hits]
        context = "\n\n## Relevante Lehrplaninhalte (automatisch eingeblendet)\n" + "\n\n---\n\n".join(blocks)
        classifications = [h["classification"] for h in hits]
        return (context, classifications)
    except Exception:
        return ("", [])

# ---------------------------------------------------------------------------
# Ollama-Status-Cache
# ---------------------------------------------------------------------------
_ollama_lock = threading.Lock()
_ollama_online = False
_ollama_last_check = 0

def check_ollama():
    global _ollama_online, _ollama_last_check
    now = time.time()
    with _ollama_lock:
        if now - _ollama_last_check < 10:
            return _ollama_online
    online = False
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            online = bool(data.get("models"))
    except Exception:
        online = False
    with _ollama_lock:
        _ollama_online = online
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
def stream_llm(
    messages,
    profile,
    settings,
    skill_content="",
    rag_context="",
    wfile=None,
    skill_name=None,
    privacy_decision=None,
):
    """Stream one request while enforcing the complete-payload privacy decision."""
    decision = privacy_decision or decide_privacy(
        messages=messages,
        profile=profile,
        skill_id=skill_name,
        rag_context=rag_context,
    )
    provider = settings.get("provider") or "openrouter"
    custom_endpoint = (settings.get("customEndpoint") or "").strip()

    if decision.local_required:
        if provider == "custom" and is_trusted_loopback_endpoint(custom_endpoint):
            effective_provider = "custom"
        elif check_ollama():
            effective_provider = "ollama"
        else:
            _send_sse(wfile, {
                "type": "privacy",
                "mode": decision.mode,
                "reasons": list(decision.reasons),
            })
            _send_sse(wfile, {
                "type": "error",
                "code": "LOCAL_MODEL_REQUIRED",
                "message": "Diese Unterhaltung muss lokal verarbeitet werden. Bitte starte Ollama.",
            })
            _send_sse(wfile, {"type": "done"})
            return ""
    else:
        effective_provider = provider

    _send_sse(wfile, {
        "type": "privacy",
        "mode": decision.mode,
        "reasons": list(decision.reasons),
    })

    prompt_profile = profile if decision.local_required else minimize_cloud_profile(profile)
    system_content = build_system_prompt(prompt_profile)
    if decision.local_required:
        companion = SKILL_REGISTRY.companion_prompt()
        if companion:
            system_content += "\n\n## Persönliche Begleitung\n" + companion
        private_memory = load_memory_context()
        if private_memory:
            system_content += "\n\n## Lokaler Memory-Kontext\n" + private_memory
    if skill_content:
        system_content += "\n\n## Aktiver Skill\n" + skill_content
    if rag_context:
        system_content += rag_context

    api_messages = [{"role": "system", "content": system_content}]
    for message in messages:
        role = "assistant" if message.get("role") in {"bot", "assistant"} else "user"
        content = message.get("text", message.get("content", ""))
        if isinstance(content, str) and content.strip():
            api_messages.append({"role": role, "content": content})

    if effective_provider == "ollama":
        endpoint = "http://127.0.0.1:11434/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        body = {
            "model": settings.get("ollamaModel") or "gemma3:4b",
            "messages": api_messages,
            "stream": True,
        }
    elif effective_provider == "custom":
        if not custom_endpoint:
            _send_sse(wfile, {"type": "error", "code": "CUSTOM_ENDPOINT_MISSING", "message": "Custom-Endpoint fehlt."})
            _send_sse(wfile, {"type": "done"})
            return ""
        if not is_trusted_loopback_endpoint(custom_endpoint):
            try:
                validate_remote_url(custom_endpoint)
            except ValueError:
                _send_sse(wfile, {"type": "error", "code": "CUSTOM_ENDPOINT_BLOCKED", "message": "Der Custom-Endpoint ist nicht zulässig."})
                _send_sse(wfile, {"type": "done"})
                return ""
        headers = {"Content-Type": "application/json"}
        custom_key = CREDENTIALS.get(CredentialStore.CUSTOM)
        if custom_key:
            headers["Authorization"] = f"Bearer {custom_key}"
        endpoint = custom_endpoint
        body = {
            "model": settings.get("customModel") or "gpt-3.5-turbo",
            "messages": api_messages,
            "stream": True,
        }
    else:
        api_key = CREDENTIALS.get(CredentialStore.OPENROUTER)
        if not api_key:
            _send_sse(wfile, {"type": "error", "code": "API_KEY_MISSING", "message": "OpenRouter-API-Key fehlt."})
            _send_sse(wfile, {"type": "done"})
            return ""
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8789",
            "X-Title": "TeacherAssist",
        }
        body = {
            "model": settings.get("model") or "deepseek/deepseek-chat",
            "messages": api_messages,
            "stream": True,
        }

    _send_sse(wfile, {"type": "provider", "provider": effective_provider})
    full_text = []
    done_sent = False
    try:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            buffer = b""
            while True:
                chunk = response.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        _send_sse(wfile, {"type": "done"})
                        done_sent = True
                        return "".join(full_text)
                    try:
                        parsed = json.loads(raw)
                    except ValueError:
                        continue
                    content = parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        full_text.append(content)
                        _send_sse(wfile, {"type": "chunk", "text": content})
                    if parsed.get("usage"):
                        _send_sse(wfile, {"type": "usage", "usage": parsed["usage"]})
    except Exception:
        logger.exception("Provider request failed provider=%s", effective_provider)
        _send_sse(wfile, {"type": "error", "code": "PROVIDER_ERROR", "message": "Der Modellaufruf ist fehlgeschlagen."})
    finally:
        if not done_sent:
            _send_sse(wfile, {"type": "done"})
    return "".join(full_text)


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
class RequestTooLarge(ValueError):
    pass


class ToolHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TeacherAssist/2.0"

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; connect-src 'self'; font-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def _authorize(self, path):
        if not valid_host(self.headers.get("Host", "")):
            self._error("INVALID_HOST", "Ungültiger Host.", 421)
            return False
        if not valid_browser_source(self.headers.get("Origin", ""), self.headers.get("Sec-Fetch-Site", "")):
            self._error("CROSS_SITE_BLOCKED", "Cross-Site-Anfrage blockiert.", 403)
            return False
        if path.startswith("/api/v1/") and path not in PUBLIC_PATHS:
            if not SESSIONS.validate(self.headers.get("Cookie", ""), self.headers.get("X-CSRF-Token", "")):
                self._error("AUTH_REQUIRED", "Ungültige oder abgelaufene Sitzung.", 403)
                return False
        return True

    def do_OPTIONS(self):
        self._error("CORS_DISABLED", "Cross-Origin-Anfragen werden nicht unterstützt.", 405)

    def _json(self, data, status=200, extra_headers=None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, message, status=400):
        self._json({"error": {"code": code, "message": message}}, status)

    def _body(self, max_bytes=MAX_JSON_BYTES):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length < 0:
            raise ValueError("Invalid Content-Length")
        if length > max_bytes:
            raise RequestTooLarge(f"Request exceeds {max_bytes} bytes")
        return self.rfile.read(length)

    def _read_json(self, max_bytes=MAX_JSON_BYTES):
        try:
            data = json.loads(self._body(max_bytes).decode("utf-8"))
        except RequestTooLarge:
            raise
        except Exception as exc:
            raise ValueError("Invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _static(self, filename):
        dist_root = (BASE_DIR / "web_dist").resolve()
        source_root = BASE_DIR
        if dist_root.is_dir():
            candidate = dist_root / filename
            if candidate.is_file():
                source_root = dist_root
        path = (source_root / filename).resolve()
        try:
            path.relative_to(source_root)
        except ValueError:
            self.send_error(404)
            return
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        content_type = STATIC_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        if not self._authorize(route):
            return
        if route in STATIC_FILES:
            self._static(STATIC_FILES[route])
        elif route.startswith("/assets/"):
            self._static(route.lstrip("/"))
        elif route == "/api/v1/health":
            self._json({"status": "ok", "version": "2.0"})
        elif route == "/api/v1/bootstrap":
            session_id, csrf = SESSIONS.create()
            try:
                encrypted_state = STATE_STORE.get_state()
            except (PersistenceUnavailable, RuntimeError):
                encrypted_state = {"profile": {}, "chats": []}
            self._json({
                "csrfToken": csrf,
                "settings": SETTINGS_STORE.public(),
                "capabilities": {**capability_status(), "ollama": check_ollama()},
                "skills": SKILL_REGISTRY.public_index(),
                "state": encrypted_state,
                "dataSchemaVersion": 2,
            }, extra_headers={
                "Set-Cookie": f"{SESSIONS.COOKIE_NAME}={session_id}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSIONS.MAX_AGE_SECONDS}",
            })
        elif route == "/api/v1/settings":
            self._json(SETTINGS_STORE.public())
        elif route == "/api/v1/collections":
            try:
                collection, _ = get_collection()
                self._json({"chunks": collection.count()})
            except Exception:
                self._json({"chunks": 0, "available": False})
        elif route == "/api/v1/backup":
            self._backup()
        elif route == "/api/v1/rasters":
            self._list_raster()
        elif route == "/api/v1/memory-list":
            self._list_memory()
        elif route == "/api/v1/memory-read":
            self._read_memory_file(parse_qs(parsed.query).get("file", [""])[0])
        elif route == "/api/v1/memory-versions":
            self._list_versions(parse_qs(parsed.query).get("file", [""])[0])
        elif route == "/api/v1/search":
            self._search(parsed)
        elif route == "/api/v1/chats":
            self._list_chats()
        elif route == "/api/v1/profile":
            self._get_profile()
        elif route.startswith("/api/v1/chats/"):
            self._get_chat(route.rsplit("/", 1)[-1])
        elif route.startswith("/api/v1/exports/"):
            self._download_export(unquote(route[len("/api/v1/exports/"):]))
        else:
            self.send_error(404)

    def _search(self, parsed):
        params = parse_qs(parsed.query)
        query = params.get("q", [""])[0].strip()
        try:
            limit = min(max(int(params.get("limit", ["4"])[0]), 1), 8)
        except ValueError:
            limit = 4
        if not query:
            self._json({"results": []})
            return
        try:
            collection, _ = get_collection()
            count = collection.count()
            if count == 0:
                self._json({"results": []})
                return
            result = collection.query(query_texts=[query], n_results=min(limit, count))
            documents = result.get("documents", [[]])[0]
            metadata = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            hits = [
                {"text": text, "source": meta.get("source", ""), "distance": round(distance, 3)}
                for text, meta, distance in zip(documents, metadata, distances)
                if distance < 1.3
            ]
            self._json({"results": hits})
        except Exception:
            self._json({"results": [], "available": False})

    def do_POST(self):
        route = urlparse(self.path).path
        if not self._authorize(route):
            return
        routes = {
            "/api/v1/chat": self._chat,
            "/api/v1/upload": self._upload,
            "/api/v1/ingest": self._ingest,
            "/api/v1/clear": self._clear,
            "/api/v1/download-url": self._download_url,
            "/api/v1/settings": self._save_settings,
            "/api/v1/export-file": self._export_file,
            "/api/v1/save-raster": self._save_raster,
            "/api/v1/restore": self._restore,
            "/api/v1/memory-write": self._write_memory_file,
            "/api/v1/memory-restore-version": self._restore_version,
            "/api/v1/ollama-pull": self._ollama_pull,
            "/api/v1/shutdown": self._shutdown,
            "/api/v1/ocr-image": self._ocr_image,
            "/api/v1/session-summary": self._session_summary,
            "/api/v1/chats": self._create_chat,
            "/api/v1/profile": self._set_profile,
            "/api/v1/migration/browser-state": self._import_browser_state,
        }
        handler = routes.get(route)
        if handler:
            handler()
            return
        if route.startswith("/api/v1/chats/") and route.endswith("/messages"):
            self._chat_message(route.split("/")[-2])
            return
        if route.startswith("/api/v1/chats/") and route.endswith("/summary"):
            self._chat_summary(route.split("/")[-2])
            return
        self.send_error(404)

    def do_PATCH(self):
        route = urlparse(self.path).path
        if not self._authorize(route):
            return
        if route == "/api/v1/settings":
            self._save_settings()
        elif route == "/api/v1/profile":
            self._set_profile()
        elif route == "/api/v1/state":
            self._replace_state()
        else:
            self.send_error(404)

    def do_DELETE(self):
        route = urlparse(self.path).path
        if not self._authorize(route):
            return
        if route.startswith("/api/v1/chats/"):
            self._delete_chat(route.rsplit("/", 1)[-1])
        else:
            self.send_error(404)

    def _chat(self):
        try:
            data = self._read_json(MAX_CHAT_BYTES)
        except RequestTooLarge:
            self._error("REQUEST_TOO_LARGE", "Chat-Anfrage ist zu groß.", 413)
            return
        except ValueError:
            self._error("INVALID_JSON", "Ungültiges JSON.", 400)
            return
        self._stream_chat_payload(data)

    def _stream_chat_payload(self, data, persisted_chat=None):
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            self._error("INVALID_MESSAGES", "messages muss eine Liste sein.", 400)
            return ""
        profile = data.get("profile", {})
        settings = apply_request_overrides(load_settings(), data)
        last_user = next((message.get("text", message.get("content", "")) for message in reversed(messages) if message.get("role") == "user"), "")
        requested_skill = data.get("skill_id") or data.get("force_skill") or data.get("forceSkill")
        skill_record = SKILL_REGISTRY.get(requested_skill) if isinstance(requested_skill, str) else None
        if skill_record is None:
            skill_record = SKILL_REGISTRY.match(last_user)
        skill_id = skill_record.skill_id if skill_record else None
        skill_content = skill_record.content if skill_record else ""
        rag_context, rag_classifications = search_rag(last_user)
        decision = decide_privacy(
            messages=messages,
            profile=profile,
            skill_id=skill_id,
            requested_mode=data.get("privacy_mode", data.get("privacyMode", "auto")),
            sticky_mode=(persisted_chat or {}).get("privacyMode", data.get("stickyPrivacyMode", "auto")),
            document_classifications=rag_classifications,
            rag_context=rag_context,
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        if skill_id:
            _send_sse(self.wfile, {"type": "skill", "name": skill_id})
        return stream_llm(
            messages=messages,
            profile=profile,
            settings=settings,
            skill_content=skill_content,
            rag_context=rag_context,
            wfile=self.wfile,
            skill_name=skill_id,
            privacy_decision=decision,
        )

    def _storage_error(self, action):
        try:
            return action()
        except PersistenceUnavailable:
            self._error("PERSISTENCE_UNAVAILABLE", "Verschlüsselte Speicherung ist auf diesem System nicht verfügbar.", 503)
        except RuntimeError:
            logger.exception("Encrypted state operation failed")
            self._error("PERSISTENCE_ERROR", "Verschlüsselte Speicherung ist fehlgeschlagen.", 500)
        return None

    def _replace_state(self):
        try:
            data = self._read_json(MAX_CHAT_BYTES)
        except (ValueError, RequestTooLarge):
            self._error("INVALID_STATE", "Ungültiger Speicherstand.", 400)
            return
        result = self._storage_error(lambda: STATE_STORE.replace_state(data.get("profile", {}), data.get("chats", [])))
        if result is not None:
            self._json({"state": result})

    def _import_browser_state(self):
        try:
            data = self._read_json(MAX_CHAT_BYTES)
        except (ValueError, RequestTooLarge):
            self._error("INVALID_MIGRATION", "Ungültige Migrationsdaten.", 400)
            return
        result = self._storage_error(lambda: STATE_STORE.import_browser_state(data.get("profile", {}), data.get("chats", [])))
        if result is not None:
            self._json(result)

    def _list_chats(self):
        result = self._storage_error(STATE_STORE.list_chats)
        if result is not None:
            self._json({"chats": result})

    def _create_chat(self):
        try:
            data = self._read_json()
        except ValueError:
            data = {}
        result = self._storage_error(lambda: STATE_STORE.create_chat(data.get("title", "Neuer Chat"), data.get("messages")))
        if result is not None:
            self._json(result, 201)

    def _get_chat(self, chat_id):
        result = self._storage_error(lambda: STATE_STORE.get_chat(chat_id))
        if result is None:
            return
        self._json(result) if result else self._error("NOT_FOUND", "Chat nicht gefunden.", 404)

    def _delete_chat(self, chat_id):
        result = self._storage_error(lambda: STATE_STORE.delete_chat(chat_id))
        if result is not None:
            self._json({"success": bool(result)})

    def _chat_message(self, chat_id):
        try:
            data = self._read_json(MAX_CHAT_BYTES)
        except (ValueError, RequestTooLarge):
            self._error("INVALID_REQUEST", "Ungültige Chat-Anfrage.", 400)
            return
        chat = self._storage_error(lambda: STATE_STORE.get_chat(chat_id))
        if not chat:
            if chat is not None:
                self._error("NOT_FOUND", "Chat nicht gefunden.", 404)
            return
        content = data.get("content", "")
        if not isinstance(content, str) or not content.strip():
            self._error("EMPTY_MESSAGE", "Nachricht fehlt.", 400)
            return
        chat.setdefault("messages", []).append({"role": "user", "text": content.strip(), "ts": int(time.time() * 1000)})
        payload = {**data, "messages": chat["messages"], "stickyPrivacyMode": chat.get("privacyMode", "auto")}
        decision = decide_privacy(
            messages=chat["messages"],
            profile=STATE_STORE.get_profile(),
            skill_id=data.get("skill_id"),
            requested_mode=data.get("privacy_mode", "auto"),
            sticky_mode=chat.get("privacyMode", "auto"),
        )
        if decision.local_required:
            chat["privacyMode"] = "local_required"
        self._storage_error(lambda: STATE_STORE.save_chat(chat))
        answer = self._stream_chat_payload({**payload, "profile": STATE_STORE.get_profile()}, chat)
        if answer:
            chat["messages"].append({"role": "bot", "text": answer, "ts": int(time.time() * 1000)})
            self._storage_error(lambda: STATE_STORE.save_chat(chat))

    def _get_profile(self):
        result = self._storage_error(STATE_STORE.get_profile)
        if result is not None:
            self._json({"profile": result})

    def _set_profile(self):
        try:
            data = self._read_json()
            profile = data.get("profile", data)
        except ValueError:
            self._error("INVALID_JSON", "Ungültiges Profil.", 400)
            return
        result = self._storage_error(lambda: STATE_STORE.set_profile(profile))
        if result is not None:
            self._json({"profile": result})

    def _chat_summary(self, chat_id):
        chat = self._storage_error(lambda: STATE_STORE.get_chat(chat_id))
        if chat:
            self._summarize_messages(chat.get("messages", []), chat.get("privacyMode", "auto"))

    # ---- Bestehende Endpunkte (unverändert) ---------------------------------
    def _upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._error("INVALID_CONTENT_TYPE", "multipart/form-data erwartet.", 400)
            return
        try:
            body = self._body(MAX_UPLOAD_BYTES + 1024 * 1024)
        except RequestTooLarge:
            self._error("PDF_TOO_LARGE", "PDF ist größer als 50 MB.", 413)
            return
        boundary = next((segment.strip()[9:].strip('"') for segment in content_type.split(";") if segment.strip().startswith("boundary=")), "")
        if not boundary:
            self._error("INVALID_MULTIPART", "Multipart-Grenze fehlt.", 400)
            return
        files = parse_multipart(body, boundary)
        saved = []
        for original_name, content in files:
            if not original_name.lower().endswith(".pdf") or not content.startswith(b"%PDF"):
                continue
            destination = UPLOAD_DIR / f"upload-{uuid.uuid4().hex}.pdf"
            destination.write_bytes(content)
            saved.append(str(destination))
        if not saved:
            self._error("INVALID_PDF", "Keine gültige PDF-Datei gefunden.", 400)
            return
        self._json({"saved": saved})

    def _ingest(self):
        try:
            data = self._read_json()
        except (ValueError, RequestTooLarge):
            self._error("INVALID_JSON", "Ungültige Anfrage.", 400)
            return
        raw_path = data.get("path", "")
        source = str(data.get("source") or "Lehrplan")[:200]
        classification = data.get("classification", "unknown")
        if classification not in {"public_curriculum", "personal", "unknown"}:
            self._error("INVALID_CLASSIFICATION", "Ungültige Dokumentklassifikation.", 400)
            return
        try:
            path_obj = Path(raw_path).resolve()
            path_obj.relative_to(UPLOAD_DIR.resolve())
        except (ValueError, TypeError):
            self._error("PATH_BLOCKED", "Zugriff verweigert.", 403)
            return
        if not path_obj.is_file():
            self._error("NOT_FOUND", "Upload wurde nicht gefunden.", 404)
            return
        try:
            text = extract_pdf_text(path_obj)
            if not text.strip():
                self._error("PDF_TEXT_EMPTY", "Aus der PDF konnte kein Text extrahiert werden.", 422)
                return
            chunks = chunk_text(text)
            if not chunks:
                self._error("PDF_TEXT_TOO_SHORT", "Der extrahierte Text ist zu kurz.", 422)
                return
            collection, _ = get_collection()
            document_id = uuid.uuid4().hex
            ids = [f"{document_id}:{index}" for index in range(len(chunks))]
            metadata = [
                {"source": source, "chunk": index, "classification": classification, "document_id": document_id}
                for index in range(len(chunks))
            ]
            collection.add(documents=chunks, ids=ids, metadatas=metadata)
            self._json({
                "success": True,
                "documentId": document_id,
                "source": source,
                "classification": classification,
                "chunks": len(chunks),
                "words": len(text.split()),
            })
        except Exception:
            logger.exception("Document ingestion failed")
            self._error("INGEST_FAILED", "PDF-Verarbeitung ist fehlgeschlagen.", 500)
        finally:
            try:
                path_obj.unlink(missing_ok=True)
            except OSError:
                logger.warning("Temporary upload cleanup failed")

    def _download_url(self):
        try:
            data = self._read_json()
        except (ValueError, RequestTooLarge):
            self._error("INVALID_JSON", "Ungültige Anfrage.", 400)
            return
        url = str(data.get("url") or "").strip()
        display_name = str(data.get("source") or "Lehrplan.pdf")[:200]
        if not url:
            self._error("URL_REQUIRED", "URL fehlt.", 400)
            return
        try:
            destination = secure_download_pdf(url, UPLOAD_DIR)
            self._json({"saved": [str(destination)], "filename": display_name})
        except ValueError as exc:
            self._error("DOWNLOAD_BLOCKED", str(exc), 400)
        except Exception:
            logger.exception("Remote PDF download failed")
            self._error("DOWNLOAD_FAILED", "PDF-Download ist fehlgeschlagen.", 502)

    def _save_settings(self):
        try:
            data = self._read_json()
            settings = SETTINGS_STORE.update(data)
            self._json({"success": True, "settings": settings})
        except RequestTooLarge:
            self._error("REQUEST_TOO_LARGE", "Einstellungen sind zu groß.", 413)
        except ValueError as exc:
            self._error("INVALID_SETTINGS", str(exc), 400)
        except Exception:
            logger.exception("Settings update failed")
            self._error("SETTINGS_FAILED", "Einstellungen konnten nicht gespeichert werden.", 500)

    def _export_file(self):
        try:
            data = self._read_json()
        except RequestTooLarge:
            self._error("REQUEST_TOO_LARGE", "Anfrage ist zu groß.", 413)
            return
        except ValueError:
            self._error("INVALID_JSON", "Ungültiges JSON.", 400)
            return

        fmt = (data.get("format") or "").strip().lower()
        if fmt not in {"md", "txt", "html"}:
            self._json({"error": "Format muss md, txt oder html sein"}, 400)
            return

        content = (data.get("content") or "").strip()
        if not content:
            self._json({"error": "Kein Inhalt zum Exportieren"}, 400)
            return

        title = (data.get("title") or "TeacherAssist Export").strip()
        filename = safe_export_name(title, fmt)
        path = EXPORT_DIR / filename

        if fmt == "html":
            body = markdown_to_export_html(content, title)
        else:
            body = content

        try:
            path.write_text(body, encoding="utf-8")
        except Exception as e:
            self._json({"error": str(e)}, 500)
            return

        self._json({"success": True, "filename": filename, "url": f"/api/v1/exports/{filename}"})

    def _download_export(self, filename):
        if not filename or "/" in filename or "\\" in filename:
            self.send_error(404)
            return
        path = (EXPORT_DIR / filename).resolve()
        try:
            path.relative_to(EXPORT_DIR.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not path.is_file():
            self.send_error(404)
            return

        data = path.read_bytes()
        content_type = STATIC_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.end_headers()
        self.wfile.write(data)

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
        raster_dir = MEMORY_DIR / "bewertungsraster"
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
        try:
            data = self._read_json()
        except RequestTooLarge:
            self._error("REQUEST_TOO_LARGE", "Anfrage ist zu groß.", 413)
            return
        except ValueError:
            self._error("INVALID_JSON", "Ungültiges JSON.", 400)
            return
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
        if not slug:
            self._error("INVALID_NAME", "Fach/Klasse/Thema ergeben keinen gültigen Dateinamen.", 400)
            return
        raster_dir = MEMORY_DIR / "bewertungsraster"
        raster_dir.mkdir(parents=True, exist_ok=True)
        filepath = raster_dir / f"{slug}.md"
        self._rotate_backups(filepath)
        filepath.write_text(content, encoding="utf-8")
        self._json({"success": True, "filename": f"{slug}.md"})

    def _backup(self):
        try:
            files = []
            for item in sorted(MEMORY_DIR.rglob("*")):
                if not item.is_file() or "students" in item.relative_to(MEMORY_DIR).parts:
                    continue
                relative = item.relative_to(MEMORY_DIR)
                if item.suffix.lower() != ".md" and not any(item.name.endswith(suffix) for suffix in (".bak1", ".bak2", ".bak3")):
                    continue
                payload = item.read_bytes()
                files.append({
                    "path": "memory/" + relative.as_posix(),
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "payload": payload,
                })
            manifest = {
                "format": "teacherassist-memory-backup",
                "version": 2,
                "createdAt": int(time.time()),
                "files": [{key: row[key] for key in ("path", "size", "sha256")} for row in files],
            }
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                for row in files:
                    archive.writestr(row["path"], row["payload"])
            payload = buffer.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="teacherassist-memory-v2.zip"')
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        except Exception:
            logger.exception("Backup creation failed")
            self._error("BACKUP_FAILED", "Backup konnte nicht erstellt werden.", 500)

    def _restore(self):
        content_type = self.headers.get("Content-Type", "")
        try:
            body = self._body(MAX_RESTORE_BYTES)
        except RequestTooLarge:
            self._error("BACKUP_TOO_LARGE", "Backup ist größer als 100 MB.", 413)
            return
        try:
            if "multipart/form-data" in content_type:
                boundary = next((segment.strip()[9:].strip('"') for segment in content_type.split(";") if segment.strip().startswith("boundary=")), "")
                files = parse_multipart(body, boundary)
                if not files:
                    raise ValueError("Keine Backup-Datei übermittelt")
                zip_data = files[0][1]
            else:
                zip_data = body
            buffer = io.BytesIO(zip_data)
            if not zipfile.is_zipfile(buffer):
                raise ValueError("Datei ist kein ZIP-Archiv")
            with zipfile.ZipFile(buffer, "r") as archive:
                entries = [entry for entry in archive.infolist() if not entry.is_dir()]
                if len(entries) > MAX_RESTORE_FILES:
                    raise ValueError("Backup enthält zu viele Dateien")
                if sum(entry.file_size for entry in entries) > MAX_RESTORE_EXPANDED_BYTES:
                    raise ValueError("Entpacktes Backup ist zu groß")
                for entry in entries:
                    if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("Symlinks sind nicht erlaubt")
                try:
                    manifest = json.loads(archive.read("manifest.json"))
                except Exception as exc:
                    raise ValueError("Backup-Manifest fehlt oder ist ungültig") from exc
                if manifest.get("format") != "teacherassist-memory-backup" or manifest.get("version") != 2:
                    raise ValueError("Backup-Version wird nicht unterstützt")
                declared = {row.get("path"): row for row in manifest.get("files", []) if isinstance(row, dict)}
                prepared = []
                for name, row in declared.items():
                    safe = memory_zip_destination(name or "")
                    if safe is None or name not in archive.namelist():
                        raise ValueError("Unsicherer oder fehlender Backup-Pfad")
                    destination, normalized = safe
                    payload = archive.read(name)
                    if len(payload) != row.get("size") or hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                        raise ValueError("Backup-Prüfsumme stimmt nicht")
                    prepared.append((destination, normalized, payload))
            restored = []
            for destination, normalized, payload in prepared:
                destination.parent.mkdir(parents=True, exist_ok=True)
                self._rotate_backups(destination)
                temporary = destination.with_name(destination.name + ".restore.tmp")
                temporary.write_bytes(payload)
                os.replace(temporary, destination)
                restored.append(normalized)
            self._json({"success": True, "restored": len(restored), "files": restored})
        except ValueError as exc:
            self._error("INVALID_BACKUP", str(exc), 400)
        except Exception:
            logger.exception("Backup restore failed")
            self._error("RESTORE_FAILED", "Backup konnte nicht wiederhergestellt werden.", 500)

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
            try:
                target.relative_to(MEMORY_DIR.resolve())
            except ValueError:
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
            try:
                target.relative_to(MEMORY_DIR.resolve())
            except ValueError:
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
            try:
                target.relative_to(MEMORY_DIR.resolve())
            except ValueError:
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
            try:
                target.relative_to(MEMORY_DIR.resolve())
            except ValueError:
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
        try:
            body = self._body(MAX_IMAGE_BYTES + 1024 * 1024)
        except RequestTooLarge:
            self._error("IMAGE_TOO_LARGE", "Bild ist größer als 10 MB.", 413)
            return
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
                        for vm in ["qwen3-vl", "granite3.2-vision", "minicpm-v", "llava", "bakllava"]:
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
        if not re.match(r'^[a-zA-Z0-9_./:@-]{1,100}$', model):
            self._json({"error": "Ungültiger Modellname"}, 400)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            proc = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
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
        self._json({"success": True, "message": "TeacherAssist wird beendet."})
        def exit_later():
            time.sleep(0.5)
            os._exit(0)
        threading.Thread(target=exit_later, daemon=True).start()

    def _session_summary(self):
        try:
            data = self._read_json(MAX_CHAT_BYTES)
        except RequestTooLarge:
            self._error("REQUEST_TOO_LARGE", "Chat-Verlauf ist zu groß.", 413)
            return
        except ValueError:
            self._error("INVALID_JSON", "Ungültiger Chat-Verlauf.", 400)
            return
        self._summarize_messages(data.get("messages", []), data.get("stickyPrivacyMode", "auto"), data)

    def _summarize_messages(self, messages, sticky_mode="auto", request_data=None):
        request_data = request_data or {}
        user_texts = [
            message.get("text", message.get("content", "")).strip()
            for message in messages if message.get("role") == "user"
            and isinstance(message.get("text", message.get("content", "")), str)
            and message.get("text", message.get("content", "")).strip()
        ]
        if not user_texts:
            self._error("NO_MESSAGES", "Keine User-Nachrichten vorhanden.", 400)
            return
        decision = decide_privacy(
            messages=messages,
            profile=request_data.get("profile", {}),
            requested_mode=request_data.get("privacy_mode", "auto"),
            sticky_mode=sticky_mode,
        )
        settings = apply_request_overrides(load_settings(), request_data)
        if decision.local_required:
            if not check_ollama():
                self._error("LOCAL_MODEL_REQUIRED", "Diese Zusammenfassung muss lokal erstellt werden. Bitte starte Ollama.", 409)
                return
            endpoint = "http://127.0.0.1:11434/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            model = settings.get("ollamaModel") or "gemma3:4b"
        elif settings.get("provider") == "custom":
            endpoint = (settings.get("customEndpoint") or "").strip()
            if not endpoint:
                self._error("CUSTOM_ENDPOINT_MISSING", "Custom-Endpoint fehlt.", 400)
                return
            if not is_trusted_loopback_endpoint(endpoint):
                try:
                    validate_remote_url(endpoint)
                except ValueError:
                    self._error("CUSTOM_ENDPOINT_BLOCKED", "Custom-Endpoint ist nicht zulässig.", 400)
                    return
            headers = {"Content-Type": "application/json"}
            custom_key = CREDENTIALS.get(CredentialStore.CUSTOM)
            if custom_key:
                headers["Authorization"] = f"Bearer {custom_key}"
            model = settings.get("customModel") or "gpt-3.5-turbo"
        elif settings.get("provider") == "ollama":
            if not check_ollama():
                self._error("OLLAMA_OFFLINE", "Ollama ist nicht verfügbar.", 409)
                return
            endpoint = "http://127.0.0.1:11434/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            model = settings.get("ollamaModel") or "gemma3:4b"
        else:
            api_key = CREDENTIALS.get(CredentialStore.OPENROUTER)
            if not api_key:
                self._error("API_KEY_MISSING", "OpenRouter-API-Key fehlt.", 400)
                return
            endpoint = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}", "X-Title": "TeacherAssist"}
            model = settings.get("model") or "deepseek/deepseek-chat"
        prompt = (
            "Fasse den folgenden Chat einer Lehrkraft in 3-5 Sätzen als Verlaufsprotokoll zusammen. "
            "Nenne Thema und erarbeitete Ergebnisse, aber keine erfundenen Angaben.\n\n"
            + "\n".join(f"- {text}" for text in user_texts[-20:])
        )
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
        try:
            request = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read())
            summary = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not summary:
                raise ValueError("empty summary")
        except Exception:
            logger.exception("Session summary provider request failed")
            self._error("SUMMARY_FAILED", "Zusammenfassung konnte nicht erstellt werden.", 502)
            return
        timestamp = time.strftime("%d.%m.%Y %H:%M")
        target = MEMORY_DIR / "vergangene_stunden.md"
        existing = target.read_text("utf-8").strip() if target.exists() else "# Vergangene Stunden – Verlaufsprotokoll"
        lines = existing.splitlines()
        if len(lines) > 300:
            existing = "\n".join(lines[-300:])
        self._rotate_backups(target)
        target.write_text(existing + f"\n\n## {timestamp}\n{summary}\n", encoding="utf-8")
        self._json({"success": True, "summary": summary, "privacyMode": decision.mode})

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

class _QuietThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Unterdrueckt das laute stderr-Traceback bei harmlosen Client-Disconnects
    (WinError 10053 / 10054 / Broken Pipe). Browser, der das Tab schliesst
    waehrend Server gerade /health beantwortet, ist kein Server-Fehler."""
    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            logger.debug("Client disconnected mid-response: %s %s", client_address, exc)
            return
        logger.exception("Unhandled server error from %s", client_address)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    expected_venv = (BASE_DIR / "tools" / ".venv" / "Scripts" / "python.exe").resolve()
    if Path(sys.executable).resolve() != expected_venv:
        msg = f"WARN: Python ist nicht das erwartete venv. running={sys.executable} erwartet={expected_venv}"
        print(msg, flush=True)
        logger.warning(msg)

    port = 8789
    migration = SETTINGS_STORE.migrate_legacy(LEGACY_SETTINGS_FILE)
    logger.info("Starting Tool-Server port=%d python=%s settings_migrated=%s", port, sys.executable, migration.get("migrated", False))
    try:
        server = _QuietThreadingHTTPServer(("127.0.0.1", port), ToolHandler)
    except OSError as e:
        msg = f"Bind fehlgeschlagen auf Port {port}: {e}"
        print(msg, flush=True)
        logger.error(msg)
        sys.exit(1)
    print(f"TeacherAssist Tool-Server -> http://localhost:{port}", flush=True)
    logger.info("Tool-Server bereit auf :%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Tool-Server beendet (KeyboardInterrupt)")
