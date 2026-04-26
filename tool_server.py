#!/usr/bin/env python3
"""
TeacherAssist Tool-Server  –  Port 8789
Stellt lokale Endpunkte bereit:
  GET  /health           – Statuscheck
  GET  /collections      – Anzahl gespeicherter Abschnitte
  GET  /search?q=...     – Semantische Lehrplan-Suche (RAG)
  POST /upload           – PDF-Datei speichern (multipart)
  POST /ingest           – PDF verarbeiten + in ChromaDB speichern
  POST /clear            – Gesamte Wissensdatenbank leeren
Wird mit dem venv-Python aus start.bat gestartet.
"""
import http.server
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE_DIR      = Path(__file__).parent
UPLOAD_DIR    = BASE_DIR / "uploads"
CHROMA_DIR    = BASE_DIR / "tools" / "chroma_db"
SETTINGS_FILE = BASE_DIR / "settings.json"
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

ORIGIN = "http://localhost:8788"

# ---------------------------------------------------------------------------
# Lazy-geladene Heavy-Imports (damit der Server sofort startet)
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
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def extract_pdf_text(path: Path) -> str:
    """Text aus PDF extrahieren; bei Scan-PDFs Tesseract als Fallback."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(str(path))
        if text and text.strip():
            return text
    except Exception:
        pass
    # Fallback: OCR
    from pdf2image import convert_from_path
    import pytesseract
    images = convert_from_path(str(path))
    return "\n".join(pytesseract.image_to_string(img, lang="deu") for img in images)

def chunk_text(text: str, max_chars=900, overlap=150) -> list[str]:
    """Text in überlappende Abschnitte aufteilen."""
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

def parse_multipart(body: bytes, boundary: str) -> list[tuple[str, bytes]]:
    """Minimaler Multipart-Parser; gibt [(filename, content), ...] zurück."""
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
# HTTP-Handler
# ---------------------------------------------------------------------------
class ToolHandler(http.server.BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  ORIGIN)
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
            self._json({"status": "ok", "version": "1.0"})

        elif path == "/settings":
            try:
                if SETTINGS_FILE.exists():
                    self._json(json.loads(SETTINGS_FILE.read_text("utf-8")))
                else:
                    self._json({"provider": "openrouter", "ollamaModel": "gemma3:4b"})
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif path == "/collections":
            try:
                col, _ = get_collection()
                self._json({"chunks": col.count()})
            except Exception as e:
                self._json({"chunks": 0, "error": str(e)})

        elif path == "/backup":        self._backup()
        elif path == "/list-raster":   self._list_raster()

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
                res  = col.query(query_texts=[query], n_results=min(limit, n))
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
        if   self.path == "/upload":       self._upload()
        elif self.path == "/ingest":       self._ingest()
        elif self.path == "/clear":        self._clear()
        elif self.path == "/download-url": self._download_url()
        elif self.path == "/settings":     self._save_settings()
        elif self.path == "/save-raster":  self._save_raster()
        elif self.path == "/restore":      self._restore()
        else: self.send_error(404)

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
                self._json({"error": "Kein Text aus PDF extrahierbar (leeres Dokument?)"}, 400)
                return
            chunks = chunk_text(text)
            if not chunks:
                self._json({"error": "Text zu kurz zum Indexieren"}, 400)
                return
            col, _ = get_collection()
            # Alte Einträge dieser Quelle löschen
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
            import urllib.request
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
            allowed = {k: v for k, v in data.items() if k in ("provider", "ollamaModel", "model")}
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
        """Alle Bewertungsraster aus memory/bewertungsraster/ auflisten."""
        raster_dir = BASE_DIR / "memory" / "bewertungsraster"
        rasters = []
        if raster_dir.exists():
            for f in sorted(raster_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
                if f.name == "README.md":
                    continue
                stat = f.stat()
                # Dateinamen-Parsing: fach_klasse_thema.md
                parts = f.stem.split("_", 2)
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
        """Bewertungsraster in memory/bewertungsraster/ speichern."""
        import re
        data     = json.loads(self._body().decode("utf-8"))
        content  = data.get("content", "").strip()
        fach     = data.get("fach", "").strip()
        klasse   = data.get("klasse", "").strip()
        thema    = data.get("thema", "").strip()
        if not (fach and klasse and thema):
            self._json({"error": "fach, klasse und thema erforderlich"}, 400)
            return
        slug = f"{fach}_{klasse}_{thema}".lower()
        slug = re.sub(r"[^\w]", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        raster_dir = BASE_DIR / "memory" / "bewertungsraster"
        raster_dir.mkdir(parents=True, exist_ok=True)
        filepath = raster_dir / f"{slug}.md"
        filepath.write_text(content, encoding="utf-8")
        self._json({"success": True, "filename": f"{slug}.md", "filepath": str(filepath)})

    def _backup(self):
        """Gesamtes memory/-Verzeichnis als ZIP zum Download anbieten."""
        memory_dir = BASE_DIR / "memory"
        if not memory_dir.exists():
            self._json({"error": "memory/-Verzeichnis nicht gefunden"}, 404)
            return
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(memory_dir.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(BASE_DIR))
            data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition",
                             'attachment; filename="teacherAssist_memory_backup.zip"')
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _restore(self):
        """ZIP-Datei hochladen und memory/-Verzeichnis wiederherstellen."""
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
                    # Sicherheit: nur Dateien unter memory/ erlaubt
                    if not (norm.startswith("memory/") or norm.startswith("./memory/")):
                        continue
                    dest = BASE_DIR / norm
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(zf.read(name))
                    restored.append(norm)

            self._json({"success": True, "restored": len(restored), "files": restored})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def log_message(self, *_):
        pass  # Kein Log-Spam

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port   = 8789
    server = http.server.ThreadingHTTPServer(("", port), ToolHandler)
    print(f"TeacherAssist Tool-Server -> http://localhost:{port}", flush=True)
    server.serve_forever()
