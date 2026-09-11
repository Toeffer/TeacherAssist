import React from 'react';
import * as ReactDOM from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import '../api-client.js';

window.React = React;
window.ReactDOM = ReactDOM;

function filenameFromDisposition(value) {
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

async function start() {
  try {
    await window.taApi.bootstrap();
  } catch (error) {
    const root = document.getElementById('root');
    root.innerHTML = '<main style="font-family:system-ui;max-width:38rem;margin:12vh auto;padding:2rem"><h1>Gespeicherte Daten konnten nicht geladen werden</h1><p>TeacherAssist wurde nicht geöffnet, damit keine Daten überschrieben werden.</p><button id="retry-bootstrap">Erneut versuchen</button></main>';
    document.getElementById('retry-bootstrap').addEventListener('click', () => window.location.reload());
    return;
  }
  await import('../tweaks-panel.jsx');
  await import('../ocr-ui.jsx');
  await import('../components.jsx');
  await import('../app.jsx');
}

void start();
