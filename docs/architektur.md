# Architektur - LehrerAssistent

## Ein Prozess, ein Port

`tool_server.py` ist der einzige Server, auf Port `8789`. Er liefert sowohl das
gebaute Frontend (`web_dist/`, per `npm run build` erzeugt und committed) als auch
alle `/api/v1/*`-Endpunkte aus. Es gibt keinen zweiten Webserver und keinen
separaten Port für die UI.

## Kernbibliothek

Sicherheits- und Datenschutz-kritische Logik ist von der HTTP-Schicht getrennt in
`teacherassist_core/`:

- `security.py` – Session-/CSRF-Verwaltung, Host-/Origin-Validierung, SSRF-sichere
  URL-Prüfung für ausgehende Requests (Lehrplan-Download, Custom-Endpoint).
- `privacy.py` – Fail-closed-Klassifikation, ob ein Gespräch lokal verarbeitet
  werden muss (`decide_privacy`), plus Profil-Minimierung für Cloud-Requests.
- `runtime.py` – Laufzeitpfade (`RuntimePaths`), nicht-geheime Einstellungen
  (`SettingsStore`), Secrets über den Windows-Anmeldeinformationsspeicher
  (`CredentialStore`).
- `storage.py` – Fernet-verschlüsselter Chat-/Profil-State (`EncryptedStateStore`).
- `skills.py` – Validierte Skill-Registrierung (`SkillRegistry`), lädt
  `skills/*/skill.md` gemäss `skills_index.json`.
- `documents.py` – SSRF-sicherer PDF-Download und Textextraktion.

`tool_server.py` bleibt der dünne HTTP-Adapter darüber (Routing, Streaming,
Multipart-Parsing, ChromaDB-Zugriff).

## Datenverzeichnis

Alle veränderlichen Daten (Memory, Uploads, Exports, Logs, ChromaDB,
Einstellungen, verschlüsselter State) liegen unter
`%LOCALAPPDATA%\TeacherAssist\` (überschreibbar per `TEACHERASSIST_DATA_DIR`),
nicht im Repository. Details siehe `teacherassist_core/runtime.py` und
`CLAUDE.md` → Abschnitt *Laufzeit-Datenverzeichnis*.

## Frontend-Build

`src/main.jsx` ist der Vite-Entry-Point; er lädt `app.jsx`, `components.jsx` und
`tweaks-panel.jsx` (weiterhin der eigentliche Anwendungscode, window-global) per
dynamischem `import()`. `npm run build` erzeugt `web_dist/`, das der Server
gegenüber den Repo-Root-Quellen bevorzugt ausliefert. Endnutzer benötigen daher
kein Node.js — der Build ist Teil des Repositorys.

## LLM-Anbindung

`tool_server.py` ruft Provider serverseitig auf (nie direkt vom Browser):

```
tool_server.py ──HTTP──► OpenRouter (Cloud)         – wenn provider=openrouter und Cloud erlaubt
tool_server.py ──HTTP──► Ollama :11434 (lokal)      – wenn provider=ollama oder DSGVO-Pflicht
tool_server.py ──HTTP──► Custom-Endpoint (loopback  – wenn provider=custom
                          oder validierte HTTPS-URL)
```

Ob Cloud erlaubt ist, entscheidet ausschliesslich `decide_privacy()` in
`teacherassist_core/privacy.py` — siehe `CLAUDE.md` für die vollständige Logik.

## Mobile Clients

Frühere iOS- (Swift) und Flutter-Clients sprachen ein WebSocket-Protokoll zu
einem OpenClaw-Gateway auf Port 18789, das nie Teil dieser Architektur wurde.
Die Quellen sind entfernt und auf dem Branch `archive/mobile-clients` erhalten.
