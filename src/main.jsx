import React from 'react';
import * as ReactDOM from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import '../api-client.js';

window.React = React;
window.ReactDOM = ReactDOM;

function filenameFromDisposition(value) {
  // Prefer the RFC 6266 UTF-8 form; the plain filename is an ASCII fallback.
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(value || '');
  if (encoded) {
    try { return decodeURIComponent(encoded[1]); } catch {}
  }
  const match = /filename="?([^";]+)"?/i.exec(value || '');
  return match ? match[1] : 'teacherassist-export';
}

window.downloadTeacherAssistExport = async function downloadTeacherAssistExport(url, filename) {
  const response = await window.taFetch(url);
  if (!response.ok) {
    let message = 'Export konnte nicht heruntergeladen werden.';
    try { message = window.taApi.errorMessage(await response.json()); } catch {}
    throw new Error(message);
  }
  const blobUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = filename || filenameFromDisposition(response.headers.get('Content-Disposition'));
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(blobUrl);
};

function safeHref(href) {
  if (!href) return undefined;
  try {
    const url = new URL(href, window.location.origin);
    return ['http:', 'https:', 'mailto:'].includes(url.protocol) ? href : undefined;
  } catch {
    return undefined;
  }
}

window.SanitizedMarkdown = function SanitizedMarkdown({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeSanitize]}
      components={{
        a: ({ href, children: linkChildren, ...props }) => (
          <a {...props} href={safeHref(href)} rel="noopener noreferrer" target="_blank"
            onClick={event => {
              if (href?.startsWith('/api/v1/exports/')) {
                event.preventDefault();
                window.downloadTeacherAssistExport(href).catch(error => window.alert(error.message));
              }
            }}>
            {linkChildren}
          </a>
        ),
      }}
    >
      {String(children || '')}
    </ReactMarkdown>
  );
};

function registerServiceWorker() {
  // Registered here rather than by an inline <script>: the server's CSP
  // (script-src 'self') blocks inline scripts. Dev builds skip it so Vite's
  // module reloading and Playwright's request routing are never intercepted.
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('/service-worker.js', { updateViaCache: 'none' })
    .then(registration => registration.update())
    .catch(() => {}); // the offline cache is optional
}

async function start() {
  registerServiceWorker();
  try {
    await window.taApi.bootstrap();
  } catch (error) {
    // fetch() rejects with a TypeError when nothing answers on the port.
    const serverDown = error instanceof TypeError;
    const title = serverDown
      ? 'Der TeacherAssist-Server läuft nicht'
      : 'Gespeicherte Daten konnten nicht geladen werden';
    const detail = serverDown
      ? 'Bitte TeacherAssist über die Desktop-Verknüpfung bzw. start.bat starten und dann erneut versuchen.'
      : 'TeacherAssist wurde nicht geöffnet, damit keine Daten überschrieben werden.';
    const root = document.getElementById('root');
    // Light text: <body> is dark, and index.html resets every margin to 0.
    root.innerHTML = `<main style="font-family:system-ui;max-width:38rem;margin:12vh auto;padding:2rem;color:#f0ede6"><h1 style="margin-bottom:0.75rem">${title}</h1><p style="margin-bottom:1.5rem;line-height:1.5">${detail}</p><button id="retry-bootstrap" style="padding:0.6rem 1.2rem;border:none;border-radius:8px;background:#d97757;color:#fff;font-size:1rem;cursor:pointer">Erneut versuchen</button></main>`;
    document.getElementById('retry-bootstrap').addEventListener('click', () => window.location.reload());
    return;
  }
  await import('../tweaks-panel.jsx');
  await import('../ocr-ui.jsx');
  await import('../components.jsx');
  await import('../app.jsx');
}

void start();
