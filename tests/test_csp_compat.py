"""tool_server.py sends Content-Security-Policy "script-src 'self'", which
blocks every inline script and inline event handler. Two features were
silently dead because of it: the service-worker registration (an inline
<script> in index.html) and the print button of the PDF export window (an
inline onclick in HTML written with document.write). The browser tests run
against the Vite dev server, which sends no CSP, so this static check is
what keeps the pattern from coming back."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import tool_server

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_SOURCES = ["app.jsx", "components.jsx", "ocr-ui.jsx", "tweaks-panel.jsx", "api-client.js", "src/main.jsx"]


def test_server_csp_still_forbids_inline_scripts():
    """If this ever changes, the checks below can be revisited."""
    source = Path(tool_server.__file__).read_text(encoding="utf-8")
    csp = re.search(r'"Content-Security-Policy", "([^"]+)"', source).group(1)
    script_src = next(part for part in csp.split(";") if part.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in script_src


@pytest.mark.parametrize("page", ["index.html", "web_dist/index.html"])
def test_pages_have_no_inline_scripts(page):
    html = (ROOT / page).read_text(encoding="utf-8")
    inline = [tag for tag in re.findall(r"<script\b[^>]*>", html, re.I) if not re.search(r"\bsrc\s*=", tag, re.I)]
    assert inline == [], f"{page}: inline <script> is blocked by the CSP; move the code into src/main.jsx"


@pytest.mark.parametrize("source", FRONTEND_SOURCES)
def test_generated_html_has_no_inline_event_handlers(source):
    """JSX props are camelCase (onClick={...}) and fine; lower-case
    on...="..." attributes only appear in HTML strings, where the CSP
    blocks them."""
    text = (ROOT / source).read_text(encoding="utf-8")
    handlers = re.findall(r"""\son[a-z]+\s*=\s*["']""", text)
    assert handlers == [], f"{source}: inline event handler(s) {handlers} are blocked by the CSP"
