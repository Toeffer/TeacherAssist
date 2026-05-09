# Architektur - LehrerAssistent

## Desktop-Web-App

- `index.html`, `app.jsx` und `components.jsx` laufen im Browser auf Port `8788`.
- `tool_server.py` ist der lokale Desktop-Tool-Server auf Port `8789`.
- Der Desktop-Tool-Server verwaltet Uploads, OCR, RAG, Memory, Bewertungsraster, Backup/Restore und den LLM-Proxy.
- Desktop-Memory und ChromaDB liegen repo-lokal unter `memory/` und `tools/chroma_db/`.

## Mobile App

- Flutter und iOS sprechen nicht direkt mit `tool_server.py`.
- Mobile Integration läuft über OpenClaw/Tailscale per WebSocket auf Port `18789`.
- `TAILSCALE_HOSTNAME` und `OPENCLAW_PORT` konfigurieren den mobilen OpenClaw-Endpunkt.

## Ports

- `8788`: Desktop-Webserver.
- `8789`: Desktop-Tool-Server.
- `18789`: OpenClaw/Tailscale WebSocket für mobile Clients.
