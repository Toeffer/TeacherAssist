import React from 'react';
import * as ReactDOM from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import '../api-client.js';

window.React = React;
window.ReactDOM = ReactDOM;

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
          <a {...props} href={safeHref(href)} rel="noopener noreferrer" target="_blank">
            {linkChildren}
          </a>
        ),
      }}
    >
      {String(children || '')}
    </ReactMarkdown>
  );
};

await import('../tweaks-panel.jsx');
await import('../components.jsx');
await import('../app.jsx');
