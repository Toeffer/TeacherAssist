/* ============================================
   TeacherAssist – Shared Components
   ============================================ */

/* ---------- Icons (simple inline SVGs) ---------- */
const Icons = {
  send: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"></line>
      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
    </svg>
  ),
  menu: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  ),
  plus: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19"></line>
      <line x1="5" y1="12" x2="19" y2="12"></line>
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>
  ),
  user: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>
  ),
  book: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
    </svg>
  ),
  chat: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  ),
  sparkle: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z"></path>
    </svg>
  ),
  close: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  ),
  trash: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"></polyline>
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    </svg>
  ),
  moon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>
  ),
  sun: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>
  ),
  arrow: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12"></line>
      <polyline points="12 5 19 12 12 19"></polyline>
    </svg>
  ),
  paperclip: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
    </svg>
  ),
  database: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
    </svg>
  ),
  download: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="7 10 12 15 17 10"></polyline>
      <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>
  ),
  print: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 6 2 18 2 18 9"></polyline>
      <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
      <rect x="6" y="14" width="12" height="8"></rect>
    </svg>
  ),
  grid: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"></rect>
      <rect x="14" y="3" width="7" height="7"></rect>
      <rect x="3" y="14" width="7" height="7"></rect>
      <rect x="14" y="14" width="7" height="7"></rect>
    </svg>
  ),
  edit: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
    </svg>
  ),
  copy: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  ),
  mic: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="23"></line>
      <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
  ),
  micOff: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="1" y1="1" x2="23" y2="23"></line>
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path>
      <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path>
      <line x1="12" y1="19" x2="12" y2="23"></line>
      <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
  ),
  fileStack: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 2H8a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"></path>
      <path d="M4 6H2v16a2 2 0 0 0 2 2h14"></path>
    </svg>
  ),
  folder: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
    </svg>
  ),
  template: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="3" y1="9" x2="21" y2="9"></line>
      <line x1="9" y1="21" x2="9" y2="9"></line>
    </svg>
  ),
  upload: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16"></polyline>
      <line x1="12" y1="12" x2="12" y2="21"></line>
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>
    </svg>
  ),
  camera: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
      <circle cx="12" cy="13" r="4"></circle>
    </svg>
  ),
  calendar: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="16" y1="2" x2="16" y2="6"></line>
      <line x1="8" y1="2" x2="8" y2="6"></line>
      <line x1="3" y1="10" x2="21" y2="10"></line>
    </svg>
  ),
  history: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10"></polyline>
      <path d="M3.51 15a9 9 0 1 0 .49-4.05"></path>
    </svg>
  ),
};

/* ---------- Markdown → Druck-HTML ---------- */
function mdToHtml(md) {
  // Tabellen-Blöcke zuerst (vor Zeilen-Regex)
  let html = md.replace(/(\|.+\|\n\|[-| :]+\|\n(?:\|.+\|\n?)+)/g, (block) => {
    const lines = block.trim().split('\n');
    const ths = lines[0].split('|').filter(s => s.trim()).map(h => `<th>${h.trim()}</th>`).join('');
    const trs = lines.slice(2).map(row =>
      '<tr>' + row.split('|').filter(s => s.trim()).map(d => `<td>${d.trim()}</td>`).join('') + '</tr>'
    ).join('');
    return `<table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>\n`;
  });

  // Code-Blöcke (vor Inline-Ersetzungen)
  html = html.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) =>
    `<pre><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  );
  html = html.replace(/`([^`\n]+)`/g, (_, c) => `<code>${c.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</code>`);

  // Überschriften
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontale Linie
  html = html.replace(/^---+$/gm, '<hr>');

  // Fett / Kursiv
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Blockquotes
  html = html.replace(/(^> .+\n?)+/gm, block => {
    const inner = block.replace(/^> /gm, '').trim();
    return `<blockquote>${inner}</blockquote>\n`;
  });

  // Listen
  html = html.replace(/(^- .+\n?)+/gm, block => {
    const items = block.trim().split('\n').map(l => `<li>${l.replace(/^- /, '').trim()}</li>`).join('');
    return `<ul>${items}</ul>\n`;
  });
  html = html.replace(/(^\d+\. .+\n?)+/gm, block => {
    const items = block.trim().split('\n').map(l => `<li>${l.replace(/^\d+\. /, '').trim()}</li>`).join('');
    return `<ol>${items}</ol>\n`;
  });

  // Absätze (Doppel-Zeilenumbrüche)
  html = html.split(/\n{2,}/).map(para => {
    para = para.trim();
    if (!para) return '';
    if (/^<(h[1-6]|hr|ul|ol|table|pre|blockquote)/.test(para)) return para;
    return `<p>${para.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  return html;
}

function openPrintWindow(text, title) {
  const body = mdToHtml(text);
  const today = new Date().toLocaleDateString('de-DE');
  const win = window.open('', '_blank');
  if (!win) return;
  win.document.write(`<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>${title}</title>
<style>
  body{font-family:'Segoe UI',Arial,sans-serif;max-width:820px;margin:0 auto;padding:24px 28px;color:#222;font-size:15px;line-height:1.6}
  h1{font-size:1.5em;border-bottom:2px solid #333;padding-bottom:6px;margin-top:0}
  h2{font-size:1.25em;color:#333;margin-top:1.6em;border-bottom:1px solid #eee;padding-bottom:4px}
  h3{font-size:1.1em;color:#444;margin-top:1.4em}
  h4{font-size:1em;color:#555}
  table{width:100%;border-collapse:collapse;margin:1em 0;font-size:0.92em}
  th,td{border:1px solid #ccc;padding:7px 10px;text-align:left}
  th{background:#f2f2f2;font-weight:600}
  blockquote{border-left:3px solid #aaa;margin:1em 0;padding:6px 14px;color:#555;font-style:italic}
  hr{border:none;border-top:1px solid #ddd;margin:1.5em 0}
  code{background:#f4f4f4;padding:2px 5px;border-radius:3px;font-size:0.88em;font-family:monospace}
  pre{background:#f4f4f4;padding:12px;border-radius:6px;overflow:auto;font-size:0.88em}
  ul,ol{margin:.6em 0;padding-left:1.6em}
  li{margin:.25em 0}
  p{margin:.7em 0}
  .toolbar{background:#f0f7ff;border:1px solid #b6d4fe;border-radius:8px;padding:10px 16px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center}
  .toolbar span{font-size:13px;color:#1d4ed8}
  .btn-print{background:#2563eb;color:#fff;border:none;padding:8px 18px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600}
  .footer{margin-top:2em;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:8px}
  @media print{.toolbar{display:none}.footer{color:#bbb}}
</style>
</head>
<body>
<div class="toolbar">
  <span>📄 <strong>Export bereit</strong> – als PDF drucken oder speichern</span>
  <button class="btn-print" onclick="window.print()">🖨️ Drucken / Als PDF speichern</button>
</div>
${body}
<div class="footer">Erstellt mit TeacherAssist · ${today}</div>
</body>
</html>`);
  win.document.close();
}

/* ---------- Avatar ---------- */
function BotAvatar({ size = 32 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: 'var(--accent)', color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, fontSize: size * 0.45, fontWeight: 700,
    }}>
      TA
    </div>
  );
}

/* ---------- Typing indicator ---------- */
function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 4, padding: '8px 0' }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'var(--text-tertiary)',
          animation: `typingBounce 1.2s ease-in-out ${i * 0.15}s infinite`,
        }}></div>
      ))}
    </div>
  );
}

/* ---------- Chat Bubble ---------- */
function ChatBubble({ message, isBot, isTyping, onExport }) {
  const [hovered, setHovered] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const hasContent = isBot && !isTyping && message && message.length > 80;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const btnBase = {
    display: 'flex', alignItems: 'center', gap: 5,
    padding: '4px 10px', borderRadius: 8, fontSize: 12,
    background: 'var(--surface-elevated)',
    border: '1px solid var(--border)',
    color: 'var(--text-secondary)',
    cursor: 'pointer', fontFamily: 'inherit',
    transition: 'all 0.15s',
  };

  return (
    <div
      style={{
        display: 'flex', gap: 12, alignItems: 'flex-start',
        flexDirection: isBot ? 'row' : 'row-reverse',
        maxWidth: '100%',
        animation: 'fadeInUp 0.3s ease',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {isBot && <BotAvatar />}
      <div style={{ maxWidth: '75%', display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{
          background: isBot ? 'var(--bubble-bot)' : 'var(--bubble-user)',
          color: isBot ? 'var(--text-primary)' : 'var(--bubble-user-text)',
          padding: '10px 16px',
          borderRadius: isBot ? '4px 18px 18px 18px' : '18px 4px 18px 18px',
          fontSize: 15, lineHeight: 1.55,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {isTyping || !message ? <TypingDots /> : message}
        </div>
        {hasContent && (
          <div style={{
            display: 'flex', gap: 6,
            opacity: hovered ? 1 : 0,
            transition: 'opacity 0.2s',
          }}>
            <button
              onClick={handleCopy}
              title="Text kopieren (für Word / LibreOffice)"
              style={{ ...btnBase, ...(copied ? { background: '#2a9d5c', color: '#fff', borderColor: '#2a9d5c' } : {}) }}
              onMouseEnter={e => { if (!copied) { e.currentTarget.style.background = 'var(--accent)'; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'var(--accent)'; } }}
              onMouseLeave={e => { if (!copied) { e.currentTarget.style.background = 'var(--surface-elevated)'; e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.borderColor = 'var(--border)'; } }}
            >
              {copied ? Icons.check : Icons.copy} {copied ? 'Kopiert!' : 'Kopieren'}
            </button>
            <button
              onClick={() => onExport ? onExport(message) : openPrintWindow(message, 'TeacherAssist Export')}
              title="Drucken / Als PDF speichern"
              style={btnBase}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--accent)'; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface-elevated)'; e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
            >
              {Icons.print} Exportieren
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Quick Reply Buttons ---------- */
function QuickReplies({ options, onSelect }) {
  if (!options || options.length === 0) return null;
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: 8, paddingLeft: 44,
      animation: 'fadeInUp 0.3s ease',
    }}>
      {options.map((opt, i) => (
        <button key={i} onClick={() => onSelect(opt)} style={{
          background: 'var(--surface-elevated)',
          border: '1.5px solid var(--accent)',
          color: 'var(--accent)',
          padding: '8px 16px', borderRadius: 20,
          fontSize: 14, cursor: 'pointer', fontWeight: 500,
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={e => { e.target.style.background = 'var(--accent)'; e.target.style.color = '#fff'; }}
        onMouseLeave={e => { e.target.style.background = 'var(--surface-elevated)'; e.target.style.color = 'var(--accent)'; }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

/* ---------- Onboarding Progress ---------- */
function OnboardingProgress({ step, total }) {
  const pct = ((step) / total) * 100;
  return (
    <div style={{
      padding: '12px 20px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--surface)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
        <span>Einrichtung</span>
        <span>Schritt {step} von {total}</span>
      </div>
      <div style={{ height: 4, borderRadius: 2, background: 'var(--border)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 2,
          background: 'var(--accent)',
          width: `${pct}%`,
          transition: 'width 0.5s ease',
        }}></div>
      </div>
    </div>
  );
}

/* ---------- Sidebar ---------- */
function Sidebar({ open, onClose, chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, onNavigate, currentView, dark, onToggleDark }) {
  return (
    <>
      {open && <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)',
        zIndex: 998, display: window.innerWidth < 768 ? 'block' : 'none',
      }}></div>}
      <aside style={{
        position: 'fixed', top: 0, left: 0, bottom: 0,
        width: 280, background: 'var(--surface-sidebar)',
        borderRight: '1px solid var(--border)',
        transform: open ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.25s ease',
        zIndex: 999, display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 16px 12px', display: 'flex', alignItems: 'center', gap: 10,
          borderBottom: '1px solid var(--border)',
        }}>
          <BotAvatar size={36} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>TeacherAssist</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Dein Lehrerassistent</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 4 }}>
            {Icons.close}
          </button>
        </div>

        {/* New Chat */}
        <div style={{ padding: '12px 12px 4px' }}>
          <button onClick={() => { onNewChat(); }} style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 8,
            padding: '10px 14px', borderRadius: 10,
            background: 'var(--accent)', color: '#fff',
            border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600,
          }}>
            {Icons.plus} Neuer Chat
          </button>
        </div>

        {/* Chat list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, padding: '8px 4px 4px', marginBottom: 2 }}>Chats</div>
          {chats.map(c => (
            <div key={c.id}
              onClick={() => { onSelectChat(c.id); onNavigate('chat'); }}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '9px 10px', borderRadius: 8, cursor: 'pointer',
                background: currentView === 'chat' && activeChatId === c.id ? 'var(--accent-soft)' : 'transparent',
                color: currentView === 'chat' && activeChatId === c.id ? 'var(--accent)' : 'var(--text-primary)',
                fontSize: 14, transition: 'background 0.15s',
                marginBottom: 2,
              }}
            >
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.title}
              </span>
              {chats.length > 1 && (
                <span onClick={e => { e.stopPropagation(); onDeleteChat(c.id); }}
                  style={{ opacity: 0.4, cursor: 'pointer', flexShrink: 0 }}
                  onMouseEnter={e => e.currentTarget.style.opacity = 1}
                  onMouseLeave={e => e.currentTarget.style.opacity = 0.4}
                >{Icons.trash}</span>
              )}
            </div>
          ))}
        </div>

        {/* Bottom nav */}
        <div style={{ borderTop: '1px solid var(--border)', padding: '8px 12px' }}>
          <button onClick={() => onNavigate('profile')} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: currentView === 'profile' ? 'var(--accent-soft)' : 'transparent',
            color: currentView === 'profile' ? 'var(--accent)' : 'var(--text-primary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {Icons.user} Mein Profil
          </button>
          <button onClick={() => onNavigate('raster')} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: currentView === 'raster' ? 'var(--accent-soft)' : 'transparent',
            color: currentView === 'raster' ? 'var(--accent)' : 'var(--text-primary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {Icons.grid} Bewertungsraster
          </button>
          <button onClick={() => onNavigate('templates')} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: currentView === 'templates' ? 'var(--accent-soft)' : 'transparent',
            color: currentView === 'templates' ? 'var(--accent)' : 'var(--text-primary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {Icons.template} Vorlagen-Galerie
          </button>
          <button onClick={() => onNavigate('memory')} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: currentView === 'memory' ? 'var(--accent-soft)' : 'transparent',
            color: currentView === 'memory' ? 'var(--accent)' : 'var(--text-primary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {Icons.folder} Memory-Editor
          </button>
          <button onClick={() => onNavigate('settings')} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: currentView === 'settings' ? 'var(--accent-soft)' : 'transparent',
            color: currentView === 'settings' ? 'var(--accent)' : 'var(--text-primary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {Icons.settings} Einstellungen
          </button>
          <button onClick={onToggleDark} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '10px 10px', borderRadius: 8, border: 'none',
            background: 'transparent',
            color: 'var(--text-secondary)',
            cursor: 'pointer', fontSize: 14, textAlign: 'left',
          }}>
            {dark ? Icons.sun : Icons.moon} {dark ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </aside>
    </>
  );
}

/* ---------- Chat Input ---------- */
function ChatInput({ value, onChange, onSend, placeholder, disabled, onFileUpload, onFilesUpload, toolOnline, showDsgvoHint, showLocalHint, quickActions }) {
  const fileRef = React.useRef(null);
  const batchRef = React.useRef(null);
  const [isRecording, setIsRecording] = React.useState(false);
  const [recError, setRecError]       = React.useState('');
  const [showCamera, setShowCamera]   = React.useState(false);
  const recognitionRef = React.useRef(null);
  const cameraSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const dictateSupported = !!SpeechRec;

  const startDictation = () => {
    if (!SpeechRec || disabled) return;
    setRecError('');
    const rec = new SpeechRec();
    rec.lang = 'de-DE';
    rec.interimResults = true;
    rec.continuous = false;
    let baseText = value;
    rec.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
      const isFinal = e.results[e.results.length - 1].isFinal;
      const sep = baseText && !baseText.endsWith(' ') ? ' ' : '';
      onChange(baseText + sep + transcript);
      if (isFinal) { baseText = baseText + sep + transcript; }
    };
    rec.onerror = (e) => { setRecError(e.error === 'not-allowed' ? 'Mikrofon-Zugriff verweigert' : 'Diktat fehlgeschlagen'); setIsRecording(false); };
    rec.onend = () => setIsRecording(false);
    recognitionRef.current = rec;
    rec.start();
    setIsRecording(true);
  };

  const stopDictation = () => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); }
  };
  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (file && onFileUpload) onFileUpload(file);
    e.target.value = '';
  };
  const handleBatchFiles = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && onFilesUpload) onFilesUpload(files);
    e.target.value = '';
  };

  return (
    <div style={{ padding: '8px 16px 16px', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
      {showCamera && (
        <CameraModal
          onClose={() => setShowCamera(false)}
          onCapture={(text) => onChange(value ? value + '\n\n' + text : text)}
        />
      )}
      {quickActions?.length > 0 && !disabled && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
          {quickActions.map(a => (
            <button key={a.label} onClick={a.onSelect} style={{
              background: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              padding: '5px 12px', borderRadius: 14,
              fontSize: 12, cursor: 'pointer', fontFamily: 'inherit',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--accent-soft)'; e.currentTarget.style.color = 'var(--accent)'; e.currentTarget.style.borderColor = 'var(--accent)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface-elevated)'; e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 8,
        background: 'var(--surface-input)',
        borderRadius: 16, border: `1.5px solid ${isRecording ? 'var(--danger)' : 'var(--border)'}`,
        padding: '4px 4px 4px 8px',
        transition: 'border-color 0.2s',
      }}>
        {toolOnline && (
          <>
            <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFile} />
            <input ref={batchRef} type="file" accept=".pdf,image/*" multiple style={{ display: 'none' }} onChange={handleBatchFiles} />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={disabled}
              title="PDF-Lehrplan hochladen"
              style={{
                width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                background: 'none', border: 'none',
                color: 'var(--text-tertiary)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'color 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
            >
              {Icons.paperclip}
            </button>
            {onFilesUpload && (
              <button
                onClick={() => batchRef.current?.click()}
                disabled={disabled}
                title="Mehrere Schülerarbeiten auf einmal hochladen (Batch)"
                style={{
                  width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                  background: 'none', border: 'none',
                  color: 'var(--text-tertiary)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'color 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
              >
                {Icons.fileStack}
              </button>
            )}
          </>
        )}
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
          placeholder={isRecording ? '🎙 Diktat läuft… (sprechen)' : (placeholder || 'Nachricht eingeben…')}
          disabled={disabled}
          rows={1}
          style={{
            flex: 1, border: 'none', outline: 'none', resize: 'none',
            background: 'transparent', fontSize: 15, lineHeight: 1.5,
            color: 'var(--text-primary)', padding: '8px 0',
            fontFamily: 'inherit', maxHeight: 120,
          }}
          onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'; }}
        ></textarea>
        {dictateSupported && (
          <button
            onClick={isRecording ? stopDictation : startDictation}
            disabled={disabled}
            title={isRecording ? 'Diktat beenden' : 'Diktat starten (Spracheingabe)'}
            style={{
              width: 36, height: 36, borderRadius: 10, flexShrink: 0,
              background: isRecording ? 'rgba(220,38,38,0.12)' : 'none',
              border: 'none',
              color: isRecording ? 'var(--danger)' : 'var(--text-tertiary)',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
              animation: isRecording ? 'micPulse 1.2s ease-in-out infinite' : 'none',
            }}
            onMouseEnter={e => { if (!isRecording) e.currentTarget.style.color = 'var(--accent)'; }}
            onMouseLeave={e => { if (!isRecording) e.currentTarget.style.color = 'var(--text-tertiary)'; }}
          >
            {isRecording ? Icons.micOff : Icons.mic}
          </button>
        )}
        <button onClick={onSend} disabled={disabled || !value.trim()} style={{
          width: 40, height: 40, borderRadius: 12,
          background: value.trim() ? 'var(--accent)' : 'var(--border)',
          color: '#fff', border: 'none', cursor: value.trim() ? 'pointer' : 'default',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, transition: 'background 0.15s',
        }}>
          {Icons.send}
        </button>
      </div>
      {toolOnline && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 5, paddingLeft: 4 }}>
          📎 Lehrplan hochladen · {onFilesUpload ? '📚 Batch: mehrere Arbeiten auf einmal · ' : ''}
          {dictateSupported ? '🎙 Diktat per Mikrofon-Button' : ''}
        </div>
      )}
      {recError && (
        <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 3, paddingLeft: 4 }}>{recError}</div>
      )}
      {showDsgvoHint && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3, paddingLeft: 4 }}>
          🔒 DSGVO: Keine echten Schüler- oder Elternnamen eingeben – nutze z.B. SuS-01, SuS-02
        </div>
      )}
      {showLocalHint && (
        <div style={{ fontSize: 11, color: '#2a9d5c', marginTop: 3, paddingLeft: 4 }}>
          🔒 Lokal · Ollama: Daten verlassen nicht deinen Computer – DSGVO-konform für Schülerarbeiten
        </div>
      )}
    </div>
  );
}

/* ---------- Profile View ---------- */
function ProfileView({ profile, onUpdate }) {
  const fields = [
    { key: 'name', label: 'Name', placeholder: 'Dein Name' },
    { key: 'bundesland', label: 'Bundesland', placeholder: 'z.B. Bayern' },
    { key: 'schulform', label: 'Schulform', placeholder: 'z.B. Gymnasium' },
  ];
  return (
    <div style={{ padding: 24, maxWidth: 600, margin: '0 auto' }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Mein Profil</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
        Diese Daten helfen dem Assistenten, besser auf dich einzugehen.
      </p>
      {fields.map(f => (
        <div key={f.key} style={{ marginBottom: 18 }}>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>{f.label}</label>
          <input
            value={profile[f.key] || ''}
            onChange={e => onUpdate({ ...profile, [f.key]: e.target.value })}
            placeholder={f.placeholder}
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 10,
              border: '1.5px solid var(--border)', background: 'var(--surface-input)',
              color: 'var(--text-primary)', fontSize: 15, outline: 'none',
              fontFamily: 'inherit', boxSizing: 'border-box',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
        </div>
      ))}

      {/* Fächer */}
      <div style={{ marginBottom: 18 }}>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>Unterrichtsfächer &amp; Klassen</label>
        {(profile.faecher || []).length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            {profile.faecher.map((f, i) => (
              <span key={i} style={{
                background: 'var(--accent-soft)', color: 'var(--accent)',
                padding: '5px 12px', borderRadius: 16, fontSize: 13, fontWeight: 500,
              }}>{f}</span>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>Noch keine Fächer angegeben – starte den Onboarding-Chat!</p>
        )}
      </div>

      {/* Besonderheiten */}
      <div style={{ marginBottom: 18 }}>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>Klassenbesonderheiten</label>
        <textarea
          value={profile.besonderheiten || ''}
          onChange={e => onUpdate({ ...profile, besonderheiten: e.target.value })}
          placeholder="z.B. Inklusionsklassen, DaZ-Schüler…"
          rows={3}
          style={{
            width: '100%', padding: '10px 14px', borderRadius: 10,
            border: '1.5px solid var(--border)', background: 'var(--surface-input)',
            color: 'var(--text-primary)', fontSize: 15, outline: 'none',
            fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box',
          }}
        ></textarea>
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
          🔒 DSGVO: Keine Schüler- oder Elternnamen – Klassenbeschreibungen reichen aus
        </div>
      </div>

      {/* Methoden */}
      <div style={{ marginBottom: 18 }}>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>Bevorzugte Methoden</label>
        <textarea
          value={profile.methoden || ''}
          onChange={e => onUpdate({ ...profile, methoden: e.target.value })}
          placeholder="z.B. Stationenarbeit, kein reiner Frontalunterricht…"
          rows={2}
          style={{
            width: '100%', padding: '10px 14px', borderRadius: 10,
            border: '1.5px solid var(--border)', background: 'var(--surface-input)',
            color: 'var(--text-primary)', fontSize: 15, outline: 'none',
            fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box',
          }}
        ></textarea>
      </div>
    </div>
  );
}

/* ---------- URL Download Form (Wissensdatenbank) ---------- */
function UrlDownloadForm({ onDownload }) {
  const [url, setUrl] = React.useState('');
  const [busy, setBusy] = React.useState(false);

  const handleDownload = async () => {
    const trimmed = url.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    await onDownload(trimmed);
    setUrl('');
    setBusy(false);
  };

  return (
    <div style={{
      padding: '10px 14px', borderRadius: 8,
      background: 'var(--bg)', border: '1px dashed var(--border)',
    }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 6 }}>
        Lehrplan per URL herunterladen
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleDownload()}
          placeholder="https://…/lehrplan.pdf"
          disabled={busy}
          style={{
            flex: 1, padding: '8px 10px', borderRadius: 8, fontSize: 12,
            border: '1.5px solid var(--border)', background: 'var(--surface-input)',
            color: 'var(--text-primary)', outline: 'none', fontFamily: 'inherit',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--accent)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
        <button
          onClick={handleDownload}
          disabled={!url.trim() || busy}
          style={{
            padding: '8px 12px', borderRadius: 8, flexShrink: 0,
            background: url.trim() && !busy ? 'var(--accent)' : 'var(--border)',
            color: '#fff', border: 'none',
            cursor: url.trim() && !busy ? 'pointer' : 'default',
            fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          {Icons.download}{busy ? '…' : 'Laden'}
        </button>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 5 }}>
        Direkte PDF-URL erforderlich · Nur öffentlich zugängliche Dateien
      </div>
    </div>
  );
}

/* ---------- Gemeinschaftsschule – Zweig-Upload ---------- */
function TrackUploadSection({ trackLabel, onFileUpload, onUrlDownload }) {
  const [url, setUrl] = React.useState('');
  const [busy, setBusy] = React.useState(false);

  const handleDownload = async () => {
    const trimmed = url.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    await onUrlDownload(trimmed, trackLabel);
    setUrl('');
    setBusy(false);
  };

  return (
    <div style={{
      padding: '10px 14px', borderRadius: 8,
      background: 'var(--bg)', border: '1px solid var(--border)',
    }}>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 700, marginBottom: 8 }}>
        {trackLabel === 'Gymnasium' ? '🎓' : '📘'} {trackLabel}-Zweig
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <label style={{
          padding: '7px 12px', borderRadius: 8, cursor: 'pointer',
          background: 'var(--accent)', color: '#fff',
          fontSize: 12, fontWeight: 600, flexShrink: 0,
          display: 'inline-flex', alignItems: 'center', gap: 4,
        }}>
          📄 PDF hochladen
          <input type="file" accept=".pdf" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) onFileUpload(f, trackLabel); e.target.value = ''; }}
          />
        </label>
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleDownload()}
          placeholder="https://…/lehrplan.pdf"
          disabled={busy}
          style={{
            flex: 1, minWidth: 120, padding: '7px 10px', borderRadius: 8, fontSize: 12,
            border: '1.5px solid var(--border)', background: 'var(--surface-input)',
            color: 'var(--text-primary)', outline: 'none', fontFamily: 'inherit',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--accent)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
        <button
          onClick={handleDownload}
          disabled={!url.trim() || busy}
          style={{
            padding: '7px 10px', borderRadius: 8, flexShrink: 0,
            background: url.trim() && !busy ? 'var(--accent)' : 'var(--border)',
            color: '#fff', border: 'none',
            cursor: url.trim() && !busy ? 'pointer' : 'default',
            fontSize: 12, display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          {Icons.download}{busy ? '…' : 'URL'}
        </button>
      </div>
    </div>
  );
}

/* ---------- Settings View ---------- */
const MODEL_GROUPS = [
  {
    label: 'DeepSeek',
    models: [
      { value: 'deepseek/deepseek-v4-pro',   label: 'DeepSeek V4 Pro – Neuestes Flaggschiff, stärkstes Reasoning (Apr 2026)' },
      { value: 'deepseek/deepseek-v4-flash', label: 'DeepSeek V4 Flash – Neueste Generation, sehr schnell & günstig (Apr 2026)' },
      { value: 'deepseek/deepseek-chat',     label: 'DeepSeek V3 – Günstig & schnell, sehr gutes Deutsch (empfohlen)' },
      { value: 'deepseek/deepseek-r1',       label: 'DeepSeek R1 – Reasoning-Modell, ideal für komplexe Aufgaben' },
      { value: 'deepseek/deepseek-r1-0528',  label: 'DeepSeek R1 0528 – Aktuelleres R1 mit verbessertem Reasoning' },
    ],
  },
  {
    label: 'Google Gemini',
    models: [
      { value: 'google/gemini-2.0-flash-001',   label: 'Gemini 2.0 Flash – Sehr schnell & kosteneffizient' },
      { value: 'google/gemini-2.5-pro-preview', label: 'Gemini 2.5 Pro – Leistungsstark, langer Kontext (z.B. PDFs)' },
    ],
  },
  {
    label: 'OpenAI',
    models: [
      { value: 'openai/gpt-4o-mini', label: 'GPT-4o mini – Schnell & günstig von OpenAI' },
      { value: 'openai/gpt-4o',      label: 'GPT-4o – Sehr gute Deutschqualität, ausgewogen' },
    ],
  },
  {
    label: 'Anthropic Claude',
    models: [
      { value: 'anthropic/claude-haiku-4-5',  label: 'Claude Haiku 4.5 – Schnell & kosteneffizient' },
      { value: 'anthropic/claude-sonnet-4-6', label: 'Claude Sonnet 4.6 – Hohe Qualität, ausgewogene Geschwindigkeit' },
      { value: 'anthropic/claude-opus-4-7',   label: 'Claude Opus 4.7 – Höchste Qualität (langsamer, teurer)' },
    ],
  },
  {
    label: 'Open Source',
    models: [
      { value: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B – Open Source, sehr günstig auf OpenRouter' },
      { value: 'mistralai/mistral-large-2411',       label: 'Mistral Large – Europäisches Modell, datenschutznah' },
      { value: 'qwen/qwen-2.5-72b-instruct',         label: 'Qwen 2.5 72B – Stark bei Mehrsprachigkeit & Deutsch' },
    ],
  },
];

// Preise in USD pro 1 Million Token (Stand April 2026, OpenRouter – Änderungen möglich)
const MODEL_PRICES = {
  'deepseek/deepseek-v4-pro':           { in: 1.74,  out: 3.48  },
  'deepseek/deepseek-v4-flash':         { in: 0.14,  out: 0.28  },
  'deepseek/deepseek-chat':             { in: 0.32,  out: 0.89  },
  'deepseek/deepseek-r1':              { in: 0.70,  out: 2.50  },
  'deepseek/deepseek-r1-0528':         { in: 0.50,  out: 2.15  },
  'google/gemini-2.0-flash-001':       { in: 0.10,  out: 0.40  },
  'google/gemini-2.5-pro-preview':     { in: 1.25,  out: 10.00 },
  'openai/gpt-4o-mini':                { in: 0.15,  out: 0.60  },
  'openai/gpt-4o':                     { in: 2.50,  out: 10.00 },
  'anthropic/claude-haiku-4-5':        { in: 1.00,  out: 5.00  },
  'anthropic/claude-sonnet-4-6':       { in: 3.00,  out: 15.00 },
  'anthropic/claude-opus-4-7':         { in: 5.00,  out: 25.00 },
  'meta-llama/llama-3.3-70b-instruct': { in: 0.10,  out: 0.32  },
  'mistralai/mistral-large-2411':      { in: 2.00,  out: 6.00  },
  'qwen/qwen-2.5-72b-instruct':        { in: 0.12,  out: 0.39  },
};

// Typischer Austausch: ~300 Token Eingabe + ~600 Token Ausgabe = 900 Token
function calcMessagesPerEuro(prices) {
  if (!prices) return null;
  const costPerMsg = prices.in * 0.0003 + prices.out * 0.0006; // in USD
  const usdPerEuro = 1.08;
  return Math.round(1 * usdPerEuro / costPerMsg / 100) * 100; // gerundet auf 100
}

function SettingsView({ dark, onToggleDark, apiKey, onApiKeyChange, model, onModelChange, onResetOnboarding, toolStatus, ragDocCount, onFileUpload, onClearKnowledge, onUrlDownload, profile, provider, onProviderChange, ollamaModel, onOllamaModelChange, ollamaStatus, ollamaModels, openrouterStatus, isFallbackActive, effectiveProvider, onBackup, onRestore }) {
  const [showKey, setShowKey] = React.useState(false);
  const [keyInput, setKeyInput] = React.useState(apiKey || '');
  const [saved, setSaved] = React.useState(false);
  const restoreRef = React.useRef(null);

  const handleSaveKey = () => {
    onApiKeyChange(keyInput.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ padding: 24, maxWidth: 600, margin: '0 auto' }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Einstellungen</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
        Passe TeacherAssist an deine Bedürfnisse an.
      </p>

      {/* KI-Anbieter */}
      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 16,
      }}>
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', marginBottom: 3 }}>KI-Anbieter</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 12 }}>
            Cloud: leistungsstärker, erfordert API-Key · Lokal: kein Internet, DSGVO-konform für Schülerarbeiten
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => onProviderChange('openrouter')} style={{
              flex: 1, padding: '10px 8px', borderRadius: 10, cursor: 'pointer',
              fontWeight: 600, fontSize: 13, border: '2px solid',
              borderColor: provider === 'openrouter' ? 'var(--accent)' : 'var(--border)',
              background: provider === 'openrouter' ? 'var(--accent)' : 'var(--surface-input)',
              color: provider === 'openrouter' ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.15s',
            }}>☁️ OpenRouter</button>
            <button onClick={() => onProviderChange('ollama')} style={{
              flex: 1, padding: '10px 8px', borderRadius: 10, cursor: 'pointer',
              fontWeight: 600, fontSize: 13, border: '2px solid',
              borderColor: provider === 'ollama' ? 'var(--accent)' : 'var(--border)',
              background: provider === 'ollama' ? 'var(--accent)' : 'var(--surface-input)',
              color: provider === 'ollama' ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.15s',
            }}>🔒 Ollama (Lokal)</button>
          </div>
        </div>
      </div>

      {/* Fallback-Hinweis */}
      {isFallbackActive && (
        <div style={{
          padding: '12px 16px', borderRadius: 12, marginBottom: 16,
          background: dark ? '#451a03' : '#fef3c7',
          border: '1px solid #f59e0b',
          color: dark ? '#fcd34d' : '#92400e',
          fontSize: 13, lineHeight: 1.6,
        }}>
          <strong>⚠ {provider === 'openrouter' ? 'OpenRouter' : 'Ollama'} ist nicht erreichbar.</strong><br/>
          {effectiveProvider === 'ollama'
            ? '🔒 Ollama wird automatisch als Fallback verwendet – alle Daten bleiben lokal.'
            : '☁️ OpenRouter wird automatisch als Fallback verwendet.'}
        </div>
      )}

      {/* Ollama */}
      {provider === 'ollama' && (
      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 16,
      }}>
        <div style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
              background: ollamaStatus === 'online' ? '#2a9d5c' : ollamaStatus === 'offline' ? 'var(--danger)' : 'var(--text-tertiary)',
            }}></div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>
              {ollamaStatus === 'online' ? 'Ollama aktiv' : ollamaStatus === 'offline' ? 'Ollama nicht erreichbar' : 'Ollama wird geprüft…'}
            </div>
          </div>
          {ollamaStatus === 'offline' && (
            <div style={{
              padding: '10px 14px', borderRadius: 8, background: 'var(--bg)',
              fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.65,
            }}>
              Ollama läuft nicht. Starte es über das Taskleisten-Symbol oder führe in der Eingabeaufforderung aus:<br />
              <code style={{ fontFamily: 'monospace', fontSize: 12, display: 'inline-block', marginTop: 4 }}>ollama serve</code>
            </div>
          )}
          {ollamaStatus === 'online' && (
            <>
              <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 8 }}>Installiertes Modell</div>
              {ollamaModels.length > 0 ? (
                <select value={ollamaModel} onChange={e => onOllamaModelChange(e.target.value)} style={{
                  width: '100%', padding: '10px 14px', borderRadius: 10, marginBottom: 12,
                  border: '1.5px solid var(--border)', background: 'var(--surface-input)',
                  color: 'var(--text-primary)', fontSize: 14, outline: 'none',
                  fontFamily: 'inherit', cursor: 'pointer',
                }}>
                  {ollamaModels.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              ) : (
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 12 }}>
                  Kein Modell gefunden. Lade eines:<br />
                  <code style={{ fontFamily: 'monospace', fontSize: 12 }}>ollama pull gemma3:4b</code>
                </div>
              )}
            </>
          )}
          <div style={{
            padding: '10px 14px', borderRadius: 8,
            background: 'rgba(42,157,92,0.08)', border: '1px solid rgba(42,157,92,0.2)',
            fontSize: 12, color: '#2a9d5c', lineHeight: 1.65,
          }}>
            🔒 <strong>Lokal &amp; DSGVO-konform:</strong> Alle Anfragen laufen auf deinem Computer.
            Kein Internet erforderlich – Schülerarbeiten können bedenkenlos verarbeitet werden.
          </div>
        </div>
      </div>
      )}

      {/* API Key + Modell (OpenRouter) */}
      {provider === 'openrouter' && (
      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: apiKey ? '1px solid var(--border)' : '2px solid var(--accent)',
        overflow: 'hidden', marginBottom: 16,
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', marginBottom: 3, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>OpenRouter API-Key</span>
            {!apiKey && <span style={{ color: 'var(--accent)', fontWeight: 400, fontSize: 13 }}>– Pflichtfeld</span>}
            {openrouterStatus === 'offline' && (
              <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--danger)', display: 'inline-block' }}></span>
                nicht erreichbar
              </span>
            )}
            {openrouterStatus === 'online' && apiKey && (
              <span style={{ marginLeft: 'auto', fontSize: 12, color: '#2a9d5c', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#2a9d5c', display: 'inline-block' }}></span>
                erreichbar
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 12 }}>
            Kostenlos registrieren auf openrouter.ai · Key beginnt mit sk-or-v1-
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <input
              type={showKey ? 'text' : 'password'}
              value={keyInput}
              onChange={e => { setKeyInput(e.target.value); setSaved(false); }}
              onKeyDown={e => e.key === 'Enter' && handleSaveKey()}
              placeholder="sk-or-v1-..."
              style={{
                flex: 1, padding: '10px 14px', borderRadius: 10,
                border: '1.5px solid var(--border)', background: 'var(--surface-input)',
                color: 'var(--text-primary)', fontSize: 13, outline: 'none',
                fontFamily: 'monospace',
              }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
            <button onClick={() => setShowKey(s => !s)} style={{
              padding: '10px 12px', borderRadius: 10, whiteSpace: 'nowrap',
              border: '1.5px solid var(--border)', background: 'var(--surface-input)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13,
            }}>
              {showKey ? 'Verbergen' : 'Anzeigen'}
            </button>
          </div>
          <button
            onClick={handleSaveKey}
            disabled={!keyInput.trim()}
            style={{
              padding: '9px 20px', borderRadius: 10,
              background: saved ? '#2a9d5c' : 'var(--accent)',
              color: '#fff', border: 'none', cursor: keyInput.trim() ? 'pointer' : 'default',
              fontSize: 14, fontWeight: 600, opacity: keyInput.trim() ? 1 : 0.5,
              transition: 'background 0.2s',
            }}
          >
            {saved ? '✓ Gespeichert' : 'Speichern'}
          </button>
        </div>

        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', marginBottom: 3 }}>KI-Modell</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 10 }}>
            DeepSeek V3 ist optimal für Deutsch und sehr kostengünstig.
          </div>
          <select
            value={model}
            onChange={e => onModelChange(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', borderRadius: 10,
              border: '1.5px solid var(--border)', background: 'var(--surface-input)',
              color: 'var(--text-primary)', fontSize: 14, outline: 'none',
              fontFamily: 'inherit', cursor: 'pointer',
            }}
          >
            {MODEL_GROUPS.map(g => (
              <optgroup key={g.label} label={g.label}>
                {g.models.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </optgroup>
            ))}
          </select>

          {/* Preisanzeige für gewähltes Modell */}
          {(() => {
            const p = MODEL_PRICES[model];
            const msgsPerEuro = calcMessagesPerEuro(p);
            if (!p) return null;
            return (
              <div style={{
                marginTop: 10, padding: '10px 14px', borderRadius: 8,
                background: 'var(--bg)', fontSize: 12, color: 'var(--text-secondary)',
                lineHeight: 1.7,
              }}>
                {p.unknown ? (
                  <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
                    Neu veröffentlicht – Preis noch nicht bestätigt, bitte auf openrouter.ai prüfen
                  </span>
                ) : (
                  <>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 4 }}>
                      <span><strong>Eingabe:</strong> ca. {p.in.toLocaleString('de-DE', { minimumFractionDigits: 2 })} $ / 1M Token</span>
                      <span><strong>Ausgabe:</strong> ca. {p.out.toLocaleString('de-DE', { minimumFractionDigits: 2 })} $ / 1M Token</span>
                    </div>
                    {p.free
                      ? <span style={{ color: '#2a9d5c', fontWeight: 600 }}>Oft kostenlos auf OpenRouter verfügbar</span>
                      : msgsPerEuro && <span>&#8776; <strong>{msgsPerEuro.toLocaleString('de-DE')} Anfragen</strong> pro 1 €</span>
                    }
                  </>
                )}
              </div>
            );
          })()}

          {/* Was ist 1M Token? */}
          <div style={{
            marginTop: 10, padding: '10px 14px', borderRadius: 8,
            background: 'var(--bg)', fontSize: 12, color: 'var(--text-tertiary)',
            lineHeight: 1.65, borderLeft: '3px solid var(--border)',
          }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Was ist 1 Million Token?</strong>
            {' '}Ein Token entspricht ca. 0,6–0,7 deutschen Wörtern.
            1 Million Token ≈ <strong>650.000 Wörter</strong> ≈ <strong>ca. 1.300 DIN-A4-Seiten</strong> Text.
            In der Praxis: eine typische Lehreranfrage mit Antwort verbraucht ca. 800–1.200 Token.
            Preise können sich ändern – aktuell auf <em>openrouter.ai</em> prüfen.
          </div>
        </div>
      </div>
      )}

      {/* Wissensdatenbank */}
      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 16,
      }}>
        <div style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
            {Icons.database}
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Wissensdatenbank (Lehrpläne)</div>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 12, lineHeight: 1.6 }}>
            Lade PDF-Lehrpläne hoch – sie werden per OCR eingelesen und lokal gespeichert.
            Bei jeder Anfrage wird automatisch passender Kontext aus den Plänen eingeblendet.
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: toolStatus === 'online' ? '#2a9d5c' : toolStatus === 'offline' ? 'var(--danger)' : 'var(--text-tertiary)',
              flexShrink: 0,
            }}></div>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {toolStatus === 'online'
                ? `Tool-Server aktiv · ${ragDocCount.toLocaleString('de-DE')} Abschnitte gespeichert`
                : toolStatus === 'offline'
                ? 'Tool-Server offline – start.bat neu starten'
                : 'Tool-Server wird geprüft…'}
            </span>
          </div>

          {toolStatus === 'online' && (
            profile?.schulform === 'Gemeinschaftsschule' ? (
              <>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.5 }}>
                  Für die Gemeinschaftsschule kannst du Lehrpläne beider Schulzweige separat einlesen.
                  Ich berücksichtige bei jeder Anfrage automatisch beide Zweige.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
                  <TrackUploadSection trackLabel="Gymnasium" onFileUpload={onFileUpload} onUrlDownload={onUrlDownload} />
                  <TrackUploadSection trackLabel="Regelschule" onFileUpload={onFileUpload} onUrlDownload={onUrlDownload} />
                </div>
                {ragDocCount > 0 && (
                  <button onClick={onClearKnowledge} style={{
                    padding: '8px 16px', borderRadius: 8,
                    background: 'transparent', border: '1.5px solid var(--danger)',
                    color: 'var(--danger)', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                  }}>
                    Datenbank leeren
                  </button>
                )}
              </>
            ) : (
              <>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                  <label style={{
                    padding: '8px 16px', borderRadius: 8, cursor: 'pointer',
                    background: 'var(--accent)', color: '#fff',
                    fontSize: 13, fontWeight: 600,
                    display: 'inline-block',
                  }}>
                    PDF hochladen
                    <input type="file" accept=".pdf" style={{ display: 'none' }}
                      onChange={e => { const f = e.target.files?.[0]; if (f && onFileUpload) onFileUpload(f); e.target.value = ''; }}
                    />
                  </label>
                  {ragDocCount > 0 && (
                    <button onClick={onClearKnowledge} style={{
                      padding: '8px 16px', borderRadius: 8,
                      background: 'transparent', border: '1.5px solid var(--danger)',
                      color: 'var(--danger)', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                    }}>
                      Datenbank leeren
                    </button>
                  )}
                </div>
                <UrlDownloadForm onDownload={onUrlDownload} />
              </>
            )
          )}
        </div>
      </div>

      {/* Backup & Restore */}
      {toolStatus === 'online' && (
        <div style={{
          background: 'var(--surface-elevated)', borderRadius: 14,
          border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 16,
        }}>
          <div style={{ padding: '16px 20px' }}>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', marginBottom: 3 }}>
              Backup &amp; Restore
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 14, lineHeight: 1.6 }}>
              Sicher dein Profil, Lehrerprofil, Lehrplan-Index und Bewertungsraster als ZIP-Datei.
              Beim Restore werden bestehende Dateien überschrieben.
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={onBackup} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '9px 16px', borderRadius: 8,
                background: 'var(--accent)', color: '#fff',
                border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
              }}>
                {Icons.download} Backup herunterladen
              </button>
              <button onClick={() => restoreRef.current?.click()} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '9px 16px', borderRadius: 8,
                background: 'transparent', border: '1.5px solid var(--border)',
                color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13, fontWeight: 600,
              }}>
                {Icons.upload} Backup wiederherstellen
              </button>
              <input
                ref={restoreRef} type="file" accept=".zip"
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f && onRestore) onRestore(f); e.target.value = ''; }}
              />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 10 }}>
              🔒 Backup enthält keine Schülerdaten – nur dein Lehrerprofil und Unterrichtsunterlagen
            </div>
          </div>
        </div>
      )}

      {/* Erscheinungsbild + Reset + About */}
      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: '1px solid var(--border)', overflow: 'hidden',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Erscheinungsbild</div>
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>{dark ? 'Dark Mode aktiv' : 'Light Mode aktiv'}</div>
          </div>
          <button onClick={onToggleDark} style={{
            width: 52, height: 28, borderRadius: 14, border: 'none', cursor: 'pointer',
            background: dark ? 'var(--accent)' : 'var(--border)',
            position: 'relative', transition: 'background 0.2s',
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: '50%', background: '#fff',
              position: 'absolute', top: 3,
              left: dark ? 27 : 3,
              transition: 'left 0.2s ease',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
            }}></div>
          </button>
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Profil zurücksetzen</div>
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>Onboarding erneut durchlaufen</div>
          </div>
          <button onClick={onResetOnboarding} style={{
            padding: '8px 16px', borderRadius: 8,
            background: 'transparent', border: '1.5px solid var(--danger)',
            color: 'var(--danger)', cursor: 'pointer', fontSize: 13, fontWeight: 600,
          }}>
            Zurücksetzen
          </button>
        </div>

        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Über TeacherAssist</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Version 1.0 · {provider === 'ollama' ? `Ollama (Lokal) · ${ollamaModel}` : `OpenRouter · ${(model || '').split('/')[1] || model}`}
          </div>
          <div style={{
            marginTop: 12, padding: '10px 14px', borderRadius: 8,
            background: 'var(--bg)', fontSize: 12, color: 'var(--text-tertiary)',
            lineHeight: 1.6, borderLeft: '3px solid var(--border)',
          }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Hinweis gem. EU AI Act Art. 52:</strong> Diese Anwendung verwendet
            KI-Sprachmodelle über den Dienst <em>OpenRouter</em> (openrouter.ai).
            Antworten werden von einem KI-System generiert und stellen keine
            rechtsverbindliche Beratung dar. Inhalte immer auf fachliche
            Richtigkeit prüfen. Es werden keine personenbezogenen Schülerdaten
            an externe Server übermittelt.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- API Key Modal ---------- */
function ApiKeyModal({ onSave, onDismiss }) {
  const [keyInput, setKeyInput] = React.useState('');
  const [showKey, setShowKey] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleSave = () => {
    const trimmed = keyInput.trim();
    if (!trimmed) { setError('Bitte einen Key eingeben.'); return; }
    if (!trimmed.startsWith('sk-or-')) {
      setError('OpenRouter-Keys beginnen mit sk-or-v1-'); return;
    }
    onSave(trimmed);
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <div style={{
        background: 'var(--surface)', borderRadius: 20,
        padding: '32px 28px', maxWidth: 440, width: '100%',
        boxShadow: '0 24px 60px rgba(0,0,0,0.35)',
        animation: 'fadeInUp 0.3s ease',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <BotAvatar size={56} />
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 10, textAlign: 'center' }}>
          API-Key einrichten
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24, textAlign: 'center', lineHeight: 1.65 }}>
          TeacherAssist benötigt einen <strong>OpenRouter-Key</strong>, um auf die KI zuzugreifen.<br />
          Kostenlos registrieren auf <span style={{ color: 'var(--accent)', fontWeight: 600 }}>openrouter.ai</span> – der Key beginnt mit sk-or-v1-
        </p>

        <div style={{ display: 'flex', gap: 8, marginBottom: error ? 6 : 16 }}>
          <input
            type={showKey ? 'text' : 'password'}
            value={keyInput}
            onChange={e => { setKeyInput(e.target.value); setError(''); }}
            onKeyDown={e => e.key === 'Enter' && handleSave()}
            placeholder="sk-or-v1-..."
            autoFocus
            style={{
              flex: 1, padding: '11px 14px', borderRadius: 10,
              border: `1.5px solid ${error ? 'var(--danger)' : 'var(--border)'}`,
              background: 'var(--surface-input)',
              color: 'var(--text-primary)', fontSize: 13, outline: 'none',
              fontFamily: 'monospace',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => { if (!error) e.target.style.borderColor = 'var(--accent)'; }}
            onBlur={e => { e.target.style.borderColor = error ? 'var(--danger)' : 'var(--border)'; }}
          />
          <button onClick={() => setShowKey(s => !s)} style={{
            padding: '11px 12px', borderRadius: 10,
            border: '1.5px solid var(--border)', background: 'var(--surface-input)',
            color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13, whiteSpace: 'nowrap',
          }}>
            {showKey ? 'Verbergen' : 'Anzeigen'}
          </button>
        </div>

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</div>
        )}

        <button onClick={handleSave} style={{
          width: '100%', padding: '12px', borderRadius: 12,
          background: 'var(--accent)', color: '#fff',
          border: 'none', cursor: 'pointer', fontSize: 15, fontWeight: 600,
          marginBottom: 12, transition: 'opacity 0.15s',
        }}
          onMouseEnter={e => e.currentTarget.style.opacity = 0.88}
          onMouseLeave={e => e.currentTarget.style.opacity = 1}
        >
          Key speichern &amp; loslegen
        </button>

        {onDismiss && (
          <div style={{ textAlign: 'center' }}>
            <button onClick={onDismiss} style={{
              background: 'none', border: 'none', color: 'var(--text-tertiary)',
              fontSize: 13, cursor: 'pointer', textDecoration: 'underline',
            }}>
              Später einrichten
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- DSGVO-Warnmodal ---------- */
function DsgvoWarningModal({ findings, onAnonymize, onProceed, onCancel }) {
  const hasAuto = findings.some(f => f.auto);
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <div style={{
        background: 'var(--surface)', borderRadius: 20,
        padding: '28px 24px', maxWidth: 420, width: '100%',
        boxShadow: '0 24px 60px rgba(0,0,0,0.35)',
        animation: 'fadeInUp 0.3s ease',
      }}>
        <div style={{ fontSize: 32, textAlign: 'center', marginBottom: 10 }}>🔒</div>
        <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, textAlign: 'center' }}>
          Mögliche personenbezogene Daten
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14, lineHeight: 1.65, textAlign: 'center' }}>
          Gemäß DSGVO dürfen keine personenbezogenen Schüler- oder Elterndaten
          an externe KI-Dienste übermittelt werden.
        </p>

        <div style={{
          background: 'var(--bg)', borderRadius: 10,
          padding: '12px 14px', marginBottom: 18,
          border: '1px solid var(--border)',
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
            Erkannte Inhalte
          </div>
          {findings.map((f, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: i < findings.length - 1 ? 8 : 0 }}>
              <span style={{ fontSize: 14, flexShrink: 0 }}>{f.auto ? '🔴' : '🟡'}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{f.type}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 1 }}>
                  {f.auto
                    ? 'Wird automatisch geschwärzt'
                    : 'Bitte manuell ersetzen, z.B. durch SuS-01, SuS-02'}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {hasAuto && (
            <button onClick={onAnonymize} style={{
              padding: '12px', borderRadius: 12, border: 'none', cursor: 'pointer',
              background: 'var(--accent)', color: '#fff',
              fontSize: 14, fontWeight: 600, transition: 'opacity 0.15s',
            }}
              onMouseEnter={e => e.currentTarget.style.opacity = 0.88}
              onMouseLeave={e => e.currentTarget.style.opacity = 1}
            >
              🔒 Erkannte Daten schwärzen &amp; senden
            </button>
          )}
          <button onClick={onCancel} style={{
            padding: '12px', borderRadius: 12, cursor: 'pointer',
            background: 'var(--surface-elevated)',
            border: '1.5px solid var(--border)',
            color: 'var(--text-primary)',
            fontSize: 14, fontWeight: 600,
          }}>
            ✏️ Abbrechen &amp; Nachricht bearbeiten
          </button>
          <button onClick={onProceed} style={{
            padding: '8px', borderRadius: 10, cursor: 'pointer',
            background: 'transparent', border: 'none',
            color: 'var(--text-tertiary)', fontSize: 12,
          }}>
            Trotzdem senden (auf eigene Verantwortung)
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- Bewertungsraster-Editor ---------- */

const NOTENSCHLUESSEL_TYPEN = {
  standard:    [{ note:1,bez:'Sehr gut',pct:95 },{ note:2,bez:'Gut',pct:80 },{ note:3,bez:'Befriedigend',pct:65 },{ note:4,bez:'Ausreichend',pct:50 },{ note:5,bez:'Mangelhaft',pct:25 },{ note:6,bez:'Ungenügend',pct:0 }],
  mild:        [{ note:1,bez:'Sehr gut',pct:87 },{ note:2,bez:'Gut',pct:70 },{ note:3,bez:'Befriedigend',pct:55 },{ note:4,bez:'Ausreichend',pct:40 },{ note:5,bez:'Mangelhaft',pct:20 },{ note:6,bez:'Ungenügend',pct:0 }],
  verschaerft: [{ note:1,bez:'Sehr gut',pct:95 },{ note:2,bez:'Gut',pct:82 },{ note:3,bez:'Befriedigend',pct:70 },{ note:4,bez:'Ausreichend',pct:55 },{ note:5,bez:'Mangelhaft',pct:30 },{ note:6,bez:'Ungenügend',pct:0 }],
};

function genRasterMarkdown(form, nsTyp) {
  const today = new Date().toLocaleDateString('de-DE');
  const gesamtpunkte = form.kriterien.reduce((s, k) => s + (Number(k.punkte) || 0), 0);
  const ns = NOTENSCHLUESSEL_TYPEN[nsTyp] || NOTENSCHLUESSEL_TYPEN.standard;

  let md = `# Bewertungsraster: ${form.thema}\n\n`;
  md += `**Fach:** ${form.fach}  \n**Klasse:** ${form.klasse}  \n**Art:** ${form.art || 'Klassenarbeit'}  \n**Erstellt am:** ${today}  \n**Gesamtpunkte:** ${gesamtpunkte}\n\n`;
  md += `## Bewertungskriterien\n\n`;
  md += `| Kriterium | Max. Punkte | AFB | Beschreibung |\n`;
  md += `|-----------|-------------|-----|--------------|\n`;
  for (const k of form.kriterien) {
    md += `| ${k.name || '—'} | ${k.punkte || 0} | ${k.afb || 'II'} | ${k.beschreibung || '—'} |\n`;
  }
  md += `\n**Gesamtpunkte:** ${gesamtpunkte}\n\n`;
  md += `## Notenschlüssel\n\n`;
  md += `| Note | Bezeichnung | Mind. Punkte | Prozent |\n`;
  md += `|------|-------------|--------------|----------|\n`;
  for (let i = 0; i < ns.length; i++) {
    const n = ns[i];
    const minPkt = Math.round(gesamtpunkte * n.pct / 100 * 2) / 2;
    md += `| ${n.note} | ${n.bez} | ${minPkt} P | ≥ ${n.pct}% |\n`;
  }
  md += `\n> ⚠️ Dies ist ein Vorschlag. Du als Lehrkraft entscheidest abschließend über die Notengebung.\n`;
  return md;
}

function RasterEditorView({ toolStatus }) {
  const emptyForm = { fach:'', klasse:'', thema:'', art:'Klassenarbeit', kriterien:[
    { name:'Inhalt / Fachlichkeit', punkte:30, afb:'II', beschreibung:'' },
    { name:'Sprache / Ausdruck',    punkte:15, afb:'I',  beschreibung:'' },
    { name:'Form / Darstellung',    punkte:5,  afb:'I',  beschreibung:'' },
  ]};

  const [mode,     setMode]     = React.useState('list');
  const [rasters,  setRasters]  = React.useState([]);
  const [loading,  setLoading]  = React.useState(true);
  const [form,     setForm]     = React.useState(emptyForm);
  const [nsTyp,    setNsTyp]    = React.useState('standard');
  const [saving,   setSaving]   = React.useState(false);
  const [saved,    setSaved]    = React.useState(false);
  const [error,    setError]    = React.useState('');

  const TOOL = 'http://localhost:8789';

  React.useEffect(() => { loadRasters(); }, []);

  async function loadRasters() {
    setLoading(true);
    try {
      const r = await fetch(`${TOOL}/list-raster`);
      if (r.ok) setRasters((await r.json()).rasters || []);
    } catch {}
    setLoading(false);
  }

  function newRaster() {
    setForm(emptyForm);
    setNsTyp('standard');
    setError('');
    setSaved(false);
    setMode('edit');
  }

  async function loadRasterContent(filename) {
    try {
      // Read by requesting from server (we only have stem/label, re-derive form fields)
      const stem = filename.replace(/\.md$/, '');
      const parts = stem.split('_');
      setForm({ ...emptyForm,
        fach:   parts[0] ? parts[0].charAt(0).toUpperCase() + parts[0].slice(1) : '',
        klasse: parts[1] || '',
        thema:  parts.slice(2).join(' ') || stem,
      });
      setMode('edit');
    } catch {}
  }

  function updateKriterium(i, field, val) {
    setForm(f => {
      const k = [...f.kriterien];
      k[i] = { ...k[i], [field]: val };
      return { ...f, kriterien: k };
    });
  }
  function addKriterium() {
    setForm(f => ({ ...f, kriterien: [...f.kriterien, { name:'', punkte:10, afb:'II', beschreibung:'' }] }));
  }
  function removeKriterium(i) {
    setForm(f => ({ ...f, kriterien: f.kriterien.filter((_, j) => j !== i) }));
  }

  const gesamtpunkte = form.kriterien.reduce((s, k) => s + (Number(k.punkte) || 0), 0);

  async function handleSave() {
    if (!form.fach || !form.klasse || !form.thema) {
      setError('Bitte Fach, Klasse und Thema angeben.');
      return;
    }
    setSaving(true); setError('');
    try {
      const content = genRasterMarkdown(form, nsTyp);
      const r = await fetch(`${TOOL}/save-raster`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fach: form.fach, klasse: form.klasse, thema: form.thema, content }),
      });
      const data = await r.json();
      if (data.success) { setSaved(true); setTimeout(() => setSaved(false), 2000); loadRasters(); }
      else setError(data.error || 'Fehler beim Speichern.');
    } catch { setError('Tool-Server nicht erreichbar (start.bat läuft?).'); }
    setSaving(false);
  }

  function handleExportCurrent() {
    const md = genRasterMarkdown(form, nsTyp);
    openPrintWindow(md, `Bewertungsraster ${form.fach} ${form.klasse} – ${form.thema}`);
  }

  const inputStyle = {
    width: '100%', padding: '9px 13px', borderRadius: 10,
    border: '1.5px solid var(--border)', background: 'var(--surface-input)',
    color: 'var(--text-primary)', fontSize: 14, outline: 'none',
    fontFamily: 'inherit', boxSizing: 'border-box', transition: 'border-color 0.2s',
  };
  const labelStyle = { display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 5 };

  // ---- LIST VIEW ----
  if (mode === 'list') return (
    <div style={{ padding: 24, maxWidth: 650, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>Bewertungsraster</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, margin: 0 }}>
            Erstelle und verwalte Erwartungshorizonte für deine Klassen.
          </p>
        </div>
        <button onClick={newRaster} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '10px 18px', borderRadius: 10, border: 'none',
          background: 'var(--accent)', color: '#fff',
          cursor: 'pointer', fontSize: 14, fontWeight: 600,
        }}>
          {Icons.plus} Neu erstellen
        </button>
      </div>

      {toolStatus !== 'online' && (
        <div style={{ padding: '12px 16px', borderRadius: 10, background: 'var(--surface-elevated)', border: '1px solid var(--border)', marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
          ⚠ Tool-Server offline – Raster können nicht gespeichert werden. Starte <code>start.bat</code> neu.
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Lade…</div>
      ) : rasters.length === 0 ? (
        <div style={{
          padding: '36px 24px', borderRadius: 14, textAlign: 'center',
          border: '2px dashed var(--border)', color: 'var(--text-tertiary)',
        }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>Noch keine Raster vorhanden</div>
          <div style={{ fontSize: 13 }}>Erstelle dein erstes Bewertungsraster oder lasse den Agenten eines für dich erstellen.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {rasters.map(r => (
            <div key={r.filename} style={{
              padding: '14px 18px', borderRadius: 12,
              background: 'var(--surface-elevated)', border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: 12,
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', marginBottom: 2 }}>
                  {r.label}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                  {new Date(r.modified * 1000).toLocaleDateString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric' })}
                  {' · '}{r.filename}
                </div>
              </div>
              <button
                onClick={() => loadRasterContent(r.filename)}
                title="Bearbeiten"
                style={{ padding: '7px 13px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--surface-input)', color: 'var(--text-primary)', cursor: 'pointer', fontSize: 13, display: 'flex', alignItems: 'center', gap: 5 }}
              >
                {Icons.edit} Bearbeiten
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // ---- EDIT VIEW ----
  const ns = NOTENSCHLUESSEL_TYPEN[nsTyp];
  return (
    <div style={{ padding: 24, maxWidth: 700, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button onClick={() => setMode('list')} style={{ padding: '7px 13px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13 }}>
          ← Zurück
        </button>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          {form.fach && form.klasse ? `${form.fach} · ${form.klasse}` : 'Neues Bewertungsraster'}
        </h2>
      </div>

      {/* Metadaten */}
      <div style={{ background: 'var(--surface-elevated)', borderRadius: 14, border: '1px solid var(--border)', padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', marginBottom: 14 }}>Prüfungsdetails</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Fach *</label>
            <input value={form.fach} onChange={e => setForm(f => ({...f, fach: e.target.value}))}
              placeholder="z.B. Mathematik" style={inputStyle}
              onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
          </div>
          <div>
            <label style={labelStyle}>Klasse *</label>
            <input value={form.klasse} onChange={e => setForm(f => ({...f, klasse: e.target.value}))}
              placeholder="z.B. 7a" style={inputStyle}
              onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={labelStyle}>Thema / Prüfungsname *</label>
          <input value={form.thema} onChange={e => setForm(f => ({...f, thema: e.target.value}))}
            placeholder="z.B. Bruchrechnung Test 3" style={inputStyle}
            onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
        </div>
        <div>
          <label style={labelStyle}>Art der Prüfung</label>
          <select value={form.art} onChange={e => setForm(f => ({...f, art: e.target.value}))} style={{...inputStyle, cursor:'pointer'}}>
            {['Klassenarbeit','Kurztest','Hausaufgabe','Mündliche Prüfung','Präsentation','Projekt'].map(a => <option key={a}>{a}</option>)}
          </select>
        </div>
      </div>

      {/* Kriterien-Tabelle */}
      <div style={{ background: 'var(--surface-elevated)', borderRadius: 14, border: '1px solid var(--border)', padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
            Bewertungskriterien
            <span style={{ marginLeft: 10, fontSize: 13, fontWeight: 400, color: 'var(--text-tertiary)' }}>
              Gesamt: <strong style={{color:'var(--accent)'}}>{gesamtpunkte} Punkte</strong>
            </span>
          </div>
          <button onClick={addKriterium} style={{
            display:'flex',alignItems:'center',gap:5,padding:'6px 12px',borderRadius:8,
            border:'1.5px solid var(--accent)',background:'transparent',color:'var(--accent)',
            cursor:'pointer',fontSize:13,fontWeight:600,
          }}>
            {Icons.plus} Kriterium
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Header */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 72px 56px 1fr 32px', gap: 8, fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5, padding: '0 4px' }}>
            <span>Kriterium</span><span>Punkte</span><span>AFB</span><span>Beschreibung (optional)</span><span></span>
          </div>
          {form.kriterien.map((k, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 72px 56px 1fr 32px', gap: 8, alignItems: 'center' }}>
              <input value={k.name} onChange={e=>updateKriterium(i,'name',e.target.value)}
                placeholder="z.B. Inhalt" style={{...inputStyle, fontSize:13, padding:'7px 10px'}}
                onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
              <input type="number" min="0" max="999" value={k.punkte} onChange={e=>updateKriterium(i,'punkte',e.target.value)}
                style={{...inputStyle, fontSize:13, padding:'7px 10px', textAlign:'center'}}
                onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
              <select value={k.afb} onChange={e=>updateKriterium(i,'afb',e.target.value)}
                style={{...inputStyle, fontSize:13, padding:'7px 8px', cursor:'pointer'}}>
                <option>I</option><option>II</option><option>III</option>
              </select>
              <input value={k.beschreibung} onChange={e=>updateKriterium(i,'beschreibung',e.target.value)}
                placeholder="Optional…" style={{...inputStyle, fontSize:13, padding:'7px 10px'}}
                onFocus={e=>e.target.style.borderColor='var(--accent)'} onBlur={e=>e.target.style.borderColor='var(--border)'}/>
              {form.kriterien.length > 1 ? (
                <button onClick={()=>removeKriterium(i)} style={{ width:28,height:28,borderRadius:6,border:'none',background:'transparent',color:'var(--danger)',cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0 }}>
                  {Icons.trash}
                </button>
              ) : <div></div>}
            </div>
          ))}
        </div>
      </div>

      {/* Notenschlüssel */}
      <div style={{ background: 'var(--surface-elevated)', borderRadius: 14, border: '1px solid var(--border)', padding: '18px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>Notenschlüssel</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[['standard','Standard'],['mild','Mild (GS)'],['verschaerft','Verschärft']].map(([v,l]) => (
              <button key={v} onClick={()=>setNsTyp(v)} style={{
                padding:'5px 10px',borderRadius:7,fontSize:12,cursor:'pointer',fontWeight:600,
                border:'1.5px solid',
                borderColor: nsTyp===v ? 'var(--accent)' : 'var(--border)',
                background: nsTyp===v ? 'var(--accent)' : 'var(--surface-input)',
                color: nsTyp===v ? '#fff' : 'var(--text-secondary)',
                transition:'all 0.15s',
              }}>{l}</button>
            ))}
          </div>
        </div>
        <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
          <thead>
            <tr style={{ borderBottom:'1px solid var(--border)' }}>
              {['Note','Bezeichnung','Mind. Punkte','Prozent'].map(h => (
                <th key={h} style={{ textAlign:'left', padding:'6px 10px', color:'var(--text-tertiary)', fontWeight:600, fontSize:11, textTransform:'uppercase', letterSpacing:0.5 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ns.map((n, i) => {
              const minPkt = Math.round(gesamtpunkte * n.pct / 100 * 2) / 2;
              const maxPkt = i === 0 ? gesamtpunkte : Math.round(gesamtpunkte * ns[i-1].pct / 100 * 2) / 2 - 0.5;
              return (
                <tr key={n.note} style={{ borderBottom:'1px solid var(--border)' }}>
                  <td style={{ padding:'8px 10px', fontWeight:700, color:'var(--accent)', fontSize:16 }}>{n.note}</td>
                  <td style={{ padding:'8px 10px', color:'var(--text-primary)' }}>{n.bez}</td>
                  <td style={{ padding:'8px 10px', color:'var(--text-secondary)' }}>{minPkt}–{maxPkt} P</td>
                  <td style={{ padding:'8px 10px', color:'var(--text-tertiary)' }}>≥ {n.pct}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div style={{ marginTop:10, fontSize:12, color:'var(--text-tertiary)' }}>
          ⚠ Vorschlag – du entscheidest abschließend über die Notengebung.
        </div>
      </div>

      {/* Aktionen */}
      {error && <div style={{ marginBottom:12, padding:'10px 14px', borderRadius:8, background:'rgba(220,38,38,0.08)', color:'var(--danger)', fontSize:13 }}>{error}</div>}

      <div style={{ display:'flex', gap:10 }}>
        <button onClick={handleSave} disabled={saving || toolStatus !== 'online'} style={{
          flex:1, padding:'11px', borderRadius:10, border:'none', cursor: toolStatus==='online' ? 'pointer':'not-allowed',
          background: saved ? '#2a9d5c' : 'var(--accent)', color:'#fff',
          fontSize:14, fontWeight:600, transition:'background 0.2s',
          opacity: toolStatus !== 'online' ? 0.5 : 1,
        }}>
          {saving ? 'Speichert…' : saved ? '✓ Gespeichert' : '💾 Speichern'}
        </button>
        <button onClick={handleExportCurrent} style={{
          padding:'11px 20px', borderRadius:10, border:'1.5px solid var(--border)',
          background:'var(--surface-input)', color:'var(--text-primary)',
          cursor:'pointer', fontSize:14, fontWeight:600, display:'flex', alignItems:'center', gap:6,
        }}>
          {Icons.print} Drucken
        </button>
      </div>
      {toolStatus !== 'online' && (
        <div style={{ marginTop:8, fontSize:12, color:'var(--text-tertiary)' }}>
          Tool-Server offline – Speichern nicht möglich. Export funktioniert weiterhin.
        </div>
      )}
    </div>
  );
}

/* ---------- Memory-Editor ---------- */
function MemoryEditorView({ toolStatus }) {
  const [files,    setFiles]    = React.useState([]);
  const [loading,  setLoading]  = React.useState(true);
  const [selected, setSelected] = React.useState(null);
  const [content,  setContent]  = React.useState('');
  const [saving,   setSaving]   = React.useState(false);
  const [saved,    setSaved]    = React.useState(false);
  const [error,    setError]    = React.useState('');
  const TOOL = 'http://localhost:8789';

  React.useEffect(() => { loadList(); }, []);

  async function loadList() {
    setLoading(true);
    try {
      const r = await fetch(`${TOOL}/memory-list`);
      if (r.ok) setFiles((await r.json()).files || []);
    } catch {}
    setLoading(false);
  }

  async function openFile(path) {
    setError(''); setSaved(false);
    try {
      const r = await fetch(`${TOOL}/memory-read?file=${encodeURIComponent(path)}`);
      const d = await r.json();
      if (d.error) { setError(d.error); return; }
      setSelected(path);
      setContent(d.content || '');
    } catch (e) { setError(e.message); }
  }

  async function saveFile() {
    if (!selected) return;
    setSaving(true); setError('');
    try {
      const r = await fetch(`${TOOL}/memory-write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selected, content }),
      });
      const d = await r.json();
      if (d.success) { setSaved(true); setTimeout(() => setSaved(false), 2000); loadList(); }
      else setError(d.error || 'Fehler beim Speichern');
    } catch (e) { setError(e.message); }
    setSaving(false);
  }

  const labelStyle = {
    fontSize: 13, color: 'var(--text-primary)', cursor: 'pointer',
    padding: '10px 14px', borderRadius: 8, display: 'flex',
    alignItems: 'center', gap: 10, transition: 'background 0.15s',
    wordBreak: 'break-all',
  };

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* File list */}
      <div style={{
        width: 220, flexShrink: 0, borderRight: '1px solid var(--border)',
        overflowY: 'auto', padding: '16px 8px',
        background: 'var(--surface-sidebar)',
      }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', padding: '0 8px 12px' }}>
          Memory-Dateien
        </div>
        {toolStatus !== 'online' && (
          <div style={{ fontSize: 12, color: 'var(--danger)', padding: '8px', margin: '0 4px', borderRadius: 8, background: 'rgba(220,38,38,0.08)' }}>
            Tool-Server offline
          </div>
        )}
        {loading ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', padding: '8px 12px' }}>Lade…</div>
        ) : files.length === 0 ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', padding: '8px 12px' }}>Keine Dateien</div>
        ) : files.map(f => (
          <div
            key={f.path}
            onClick={() => openFile(f.path)}
            style={{
              ...labelStyle,
              background: selected === f.path ? 'var(--accent-soft)' : 'transparent',
              color: selected === f.path ? 'var(--accent)' : 'var(--text-primary)',
            }}
            onMouseEnter={e => { if (selected !== f.path) e.currentTarget.style.background = 'var(--surface-elevated)'; }}
            onMouseLeave={e => { if (selected !== f.path) e.currentTarget.style.background = 'transparent'; }}
          >
            <span style={{ fontSize: 16, flexShrink: 0 }}>
              {f.path.includes('/') ? '📂' : '📄'}
            </span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: selected === f.path ? 600 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
              {f.path.includes('/') && (
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.path.split('/').slice(0, -1).join('/')}</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Editor */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selected ? (
          <>
            <div style={{
              padding: '12px 20px', borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0,
              background: 'var(--surface)',
            }}>
              <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', flex: 1 }}>
                {selected}
              </span>
              <button onClick={saveFile} disabled={saving || toolStatus !== 'online'} style={{
                padding: '7px 18px', borderRadius: 9, border: 'none', cursor: 'pointer',
                background: saved ? '#2a9d5c' : 'var(--accent)', color: '#fff',
                fontSize: 13, fontWeight: 600, transition: 'background 0.2s',
                opacity: toolStatus !== 'online' ? 0.5 : 1,
              }}>
                {saving ? 'Speichert…' : saved ? '✓ Gespeichert' : '💾 Speichern'}
              </button>
              <button onClick={() => { setSelected(null); setContent(''); }} style={{
                padding: '7px 12px', borderRadius: 9, border: '1.5px solid var(--border)',
                background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13,
              }}>
                Schließen
              </button>
            </div>
            {error && (
              <div style={{ padding: '8px 20px', fontSize: 13, color: 'var(--danger)', background: 'rgba(220,38,38,0.06)', borderBottom: '1px solid var(--border)' }}>{error}</div>
            )}
            <textarea
              value={content}
              onChange={e => { setContent(e.target.value); setSaved(false); }}
              spellCheck={false}
              style={{
                flex: 1, resize: 'none', border: 'none', outline: 'none',
                padding: '20px 24px', fontFamily: "'Consolas','Courier New',monospace",
                fontSize: 13, lineHeight: 1.7, color: 'var(--text-primary)',
                background: 'var(--bg)', overflow: 'auto',
              }}
            />
            <div style={{ padding: '6px 20px', fontSize: 11, color: 'var(--text-tertiary)', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
              🔒 Nur .md-Dateien unter memory/ · Änderungen wirken beim nächsten Agent-Start
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', gap: 12 }}>
            <div style={{ fontSize: 40 }}>📁</div>
            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)' }}>Memory-Editor</div>
            <div style={{ fontSize: 13, textAlign: 'center', maxWidth: 320, lineHeight: 1.7 }}>
              Wähle links eine Datei aus um sie anzusehen und zu bearbeiten.<br/>
              Alle Änderungen werden sofort auf der Festplatte gespeichert.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Vorlagen-Galerie ---------- */
const TEMPLATE_CATEGORIES = [
  {
    label: 'Unterrichtsplanung',
    icon: '📋',
    templates: [
      { title: 'Stundenentwurf', prompt: 'Plane eine Unterrichtsstunde für Fach [FACH], Klasse [KLASSE] zum Thema [THEMA]. Zeitrahmen: 45 Minuten.' },
      { title: 'Reihenplanung (6 Std.)', prompt: 'Erstelle eine Unterrichtsreihe mit 6 Stunden für [FACH] Klasse [KLASSE] zum Thema [THEMA]. Zeige Stundenübersicht, Lernziele und Methodenvariation.' },
      { title: 'Jahresplanung', prompt: 'Erstelle eine Jahresplanung für [FACH] in Klasse [KLASSE] mit Stoffverteilungsplan, Klassenarbeitsterminen und Lehrplanbezügen.' },
      { title: 'Vertretungsstunde', prompt: 'Ich brauche sofort einen Crashplan für eine Vertretungsstunde in Klasse [KLASSE], Fach [FACH]. Kein spezielles Vorwissen nötig – in 2 Minuten einsetzbar.' },
    ],
  },
  {
    label: 'Bewertung & Korrektur',
    icon: '✅',
    templates: [
      { title: 'Bewertungsraster erstellen', prompt: 'Erstelle einen Erwartungshorizont für [ART DER PRÜFUNG] in [FACH] Klasse [KLASSE] zum Thema [THEMA]. Mit AFB-Verteilung, Punkteschlüssel und Notengrenzen.' },
      { title: 'Schülerarbeit bewerten', prompt: 'Bitte bewerte folgende Schülerarbeit anhand des gespeicherten Bewertungsrasters. [ARBEIT HIER EINFÜGEN]' },
      { title: 'Klassenstatistik auswerten', prompt: 'Ich habe folgende Noten in [FACH] Klasse [KLASSE] geschrieben: [NOTEN HIER]. Erstelle Notenspiegel, Durchschnitt und pädagogische Hinweise.' },
      { title: 'Zeugnisformulierungen', prompt: 'Formuliere Zeugniskommentare für [FACH] Klasse [KLASSE] in drei Varianten (gut, befriedigend, mit Förderempfehlung). Schulform: [SCHULFORM].' },
    ],
  },
  {
    label: 'Materialerstellung',
    icon: '📝',
    templates: [
      { title: 'Arbeitsblatt', prompt: 'Erstelle ein druckfertiges Arbeitsblatt für [FACH] Klasse [KLASSE] zum Thema [THEMA]. Mit Pflichtaufgaben und Zusatzaufgabe für schnellere Schüler.' },
      { title: 'Klassenarbeit / Klausur', prompt: 'Erstelle eine Klassenarbeit (45 Min.) für [FACH] Klasse [KLASSE] zum Thema [THEMA]. Mit Erwartungshorizont, AFB I–III und Notenschlüssel.' },
      { title: 'Lernzielkontrolle', prompt: 'Erstelle einen formativen Kurztest (10–15 Min.) für [FACH] Klasse [KLASSE] zu [THEMA]. Mit Musterlösung.' },
      { title: 'Tafelbild / Whiteboard', prompt: 'Entwirf ein strukturiertes Tafelbild für eine Stunde zu [THEMA] in [FACH] Klasse [KLASSE]. Als ASCII-Skizze mit Aufbauanleitung.' },
    ],
  },
  {
    label: 'Kommunikation',
    icon: '✉️',
    templates: [
      { title: 'Elternbrief', prompt: 'Schreibe einen Elternbrief für Klasse [KLASSE] zum Thema [ANLASS]. Freundlich, sachlich, mit Rückmeldebogen.' },
      { title: 'Förderplan', prompt: 'Erstelle einen individuellen Förderplan für einen Schüler in [FACH] Klasse [KLASSE] mit Schwäche bei [BEREICH]. Mit SMART-Zielen und konkreten Maßnahmen.' },
      { title: 'Lerntagebuch-Feedback', prompt: 'Formuliere konstruktives Feedback zu folgendem Lerntagebucheintrag eines Schülers: [EINTRAG HIER]' },
      { title: 'Klassenrat vorbereiten', prompt: 'Erstelle eine Tagesordnung und Protokollvorlage für den nächsten Klassenrat in Klasse [KLASSE] mit Themen: [THEMEN].' },
    ],
  },
];

function TemplateGalleryView({ onUseTemplate }) {
  const [activeCategory, setActiveCategory] = React.useState(0);
  const [search, setSearch] = React.useState('');

  const filtered = search.trim()
    ? TEMPLATE_CATEGORIES.map(cat => ({
        ...cat,
        templates: cat.templates.filter(t =>
          t.title.toLowerCase().includes(search.toLowerCase()) ||
          t.prompt.toLowerCase().includes(search.toLowerCase())
        ),
      })).filter(cat => cat.templates.length > 0)
    : [TEMPLATE_CATEGORIES[activeCategory]];

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: '0 auto' }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Vorlagen-Galerie</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
        Klicke auf eine Vorlage um sie direkt in den Chat zu übernehmen. Ersetze die [PLATZHALTER] mit deinen Angaben.
      </p>

      {/* Suche */}
      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Vorlage suchen…"
        style={{
          width: '100%', padding: '10px 14px', borderRadius: 10, marginBottom: 16,
          border: '1.5px solid var(--border)', background: 'var(--surface-input)',
          color: 'var(--text-primary)', fontSize: 14, outline: 'none', fontFamily: 'inherit',
          boxSizing: 'border-box',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />

      {/* Kategorie-Tabs */}
      {!search.trim() && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          {TEMPLATE_CATEGORIES.map((cat, i) => (
            <button key={i} onClick={() => setActiveCategory(i)} style={{
              padding: '8px 16px', borderRadius: 20, cursor: 'pointer', fontSize: 13, fontWeight: 600,
              border: '1.5px solid',
              borderColor: activeCategory === i ? 'var(--accent)' : 'var(--border)',
              background: activeCategory === i ? 'var(--accent)' : 'var(--surface-elevated)',
              color: activeCategory === i ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.15s',
            }}>
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>
      )}

      {/* Vorlagen */}
      {filtered.map((cat, ci) => (
        <div key={ci}>
          {search.trim() && (
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10, marginTop: ci > 0 ? 20 : 0 }}>
              {cat.icon} {cat.label}
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12, marginBottom: 8 }}>
            {cat.templates.map((t, ti) => (
              <div
                key={ti}
                onClick={() => onUseTemplate(t.prompt)}
                style={{
                  padding: '16px 18px', borderRadius: 12, cursor: 'pointer',
                  background: 'var(--surface-elevated)', border: '1.5px solid var(--border)',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.background = 'var(--accent-soft)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--surface-elevated)'; }}
              >
                <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', marginBottom: 6 }}>
                  {t.title}
                </div>
                <div style={{
                  fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.6,
                  overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
                }}>
                  {t.prompt}
                </div>
                <div style={{ marginTop: 10, fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>
                  Klicken zum Übernehmen →
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-tertiary)' }}>
          Keine Vorlagen gefunden für „{search}"
        </div>
      )}
    </div>
  );
}

/* ---------- Kamera-Modal (Foto-zu-Korrektur) ---------- */
function CameraModal({ onClose, onCapture }) {
  const videoRef   = React.useRef(null);
  const streamRef  = React.useRef(null);
  const [preview,    setPreview]    = React.useState(null);
  const [ocrText,    setOcrText]    = React.useState('');
  const [ocrLoading, setOcrLoading] = React.useState(false);
  const [errMsg,     setErrMsg]     = React.useState('');

  React.useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  async function startCamera() {
    setErrMsg('');
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } } });
      streamRef.current = s;
      if (videoRef.current) videoRef.current.srcObject = s;
    } catch (e) {
      setErrMsg('Kamera nicht zugänglich: ' + (e.message || e.name));
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  }

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    stopCamera();
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setPreview(dataUrl);
    canvas.toBlob(async (blob) => {
      setOcrLoading(true);
      try {
        const fd = new FormData();
        fd.append('image', blob, 'capture.jpg');
        const res  = await fetch('http://localhost:8789/ocr-image', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        setOcrText(data.text);
      } catch (e) {
        setErrMsg('OCR: ' + e.message);
      }
      setOcrLoading(false);
    }, 'image/jpeg', 0.92);
  }

  function retake() {
    setPreview(null); setOcrText(''); setErrMsg('');
    startCamera();
  }

  const inputStyle = {
    width: '100%', padding: '9px 13px', borderRadius: 10, boxSizing: 'border-box',
    border: '1.5px solid var(--border)', background: 'var(--surface-input)',
    color: 'var(--text-primary)', fontSize: 13, fontFamily: 'inherit',
    resize: 'vertical', minHeight: 100,
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 3000,
      background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: 'var(--surface)', borderRadius: 20, padding: 24,
        maxWidth: 480, width: '100%', maxHeight: '90vh', overflowY: 'auto',
        animation: 'fadeInUp 0.25s ease',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--text-primary)', margin: 0 }}>
            📸 Arbeit fotografieren
          </h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex' }}>
            {Icons.close}
          </button>
        </div>

        {!preview && (
          <>
            {errMsg ? (
              <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>
                ⚠️ {errMsg}
              </div>
            ) : (
              <video ref={videoRef} autoPlay playsInline muted style={{
                width: '100%', borderRadius: 12, background: '#000',
                maxHeight: 320, objectFit: 'cover', display: 'block', marginBottom: 12,
              }} />
            )}
            <button onClick={capture} disabled={!!errMsg} style={{
              width: '100%', padding: '12px', borderRadius: 12,
              background: errMsg ? 'var(--border)' : 'var(--accent)', color: '#fff',
              border: 'none', cursor: errMsg ? 'default' : 'pointer', fontSize: 15, fontWeight: 600,
            }}>
              📸 Foto aufnehmen
            </button>
          </>
        )}

        {preview && (
          <>
            <img src={preview} alt="Aufnahme" style={{ width: '100%', borderRadius: 12, marginBottom: 12, display: 'block' }} />
            {ocrLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-tertiary)', fontSize: 13, marginBottom: 12 }}>
                <div style={{ width: 14, height: 14, border: '2px solid var(--accent)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0 }}></div>
                Erkenne Text…
              </div>
            )}
            {errMsg && !ocrLoading && (
              <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(220,38,38,0.08)', color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>
                ⚠️ {errMsg}
              </div>
            )}
            {ocrText && (
              <>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 5 }}>
                  Erkannter Text (bearbeitbar):
                </div>
                <textarea
                  value={ocrText}
                  onChange={e => setOcrText(e.target.value)}
                  style={inputStyle}
                />
              </>
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button onClick={retake} style={{
                flex: 1, padding: '10px', borderRadius: 10, cursor: 'pointer',
                border: '1.5px solid var(--border)', background: 'var(--surface-elevated)',
                color: 'var(--text-secondary)', fontSize: 13,
              }}>
                ↩ Neu aufnehmen
              </button>
              {(ocrText || errMsg) && (
                <button
                  onClick={() => { onCapture(ocrText || ''); onClose(); }}
                  disabled={!ocrText}
                  style={{
                    flex: 2, padding: '10px', borderRadius: 10, cursor: ocrText ? 'pointer' : 'default',
                    background: ocrText ? 'var(--accent)' : 'var(--border)', color: '#fff',
                    border: 'none', fontSize: 13, fontWeight: 600,
                  }}
                >
                  In Chat einfügen →
                </button>
              )}
            </div>
          </>
        )}

        <div style={{ marginTop: 14, fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
          💡 Tipp: Auf hellem Untergrund fotografieren, Blatt gerade halten.
          Der erkannte Text wird in das Eingabefeld eingefügt.
        </div>
      </div>
    </div>
  );
}

/* ---------- iCal-Export-Modal ---------- */
function IcalExportModal({ text, onClose }) {
  const today = new Date().toISOString().slice(0, 10);

  const guessTitle = () => {
    const m = text.match(/(?:Klassenarbeit|Klausur|Test|Prüfung|Abgabe)[^\n.]{0,60}/i);
    return m ? m[0].trim() : 'Termin aus TeacherAssist';
  };
  const guessDate = () => {
    const m = text.match(/\b(\d{1,2})[./](\d{1,2})[./](20\d{2})\b/);
    if (m) {
      const [, d, mo, y] = m;
      return `${y}-${mo.padStart(2,'0')}-${d.padStart(2,'0')}`;
    }
    return today;
  };

  const [title,     setTitle]     = React.useState(guessTitle);
  const [date,      setDate]      = React.useState(guessDate);
  const [startTime, setStartTime] = React.useState('08:00');
  const [duration,  setDuration]  = React.useState('45');

  function download() {
    const dt    = new Date(`${date}T${startTime}:00`);
    const endDt = new Date(dt.getTime() + Math.max(5, parseInt(duration) || 45) * 60000);
    const fmt   = d => d.toISOString().replace(/[-:]/g, '').slice(0, 15);
    const uid   = `${Date.now()}@teacherAssist`;
    const ics   = [
      'BEGIN:VCALENDAR', 'VERSION:2.0',
      'PRODID:-//TeacherAssist//DE', 'CALSCALE:GREGORIAN',
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${fmt(new Date())}Z`,
      `DTSTART:${fmt(dt)}`,
      `DTEND:${fmt(endDt)}`,
      `SUMMARY:${title.replace(/[,;\\]/g, m => '\\' + m)}`,
      `DESCRIPTION:Erstellt mit TeacherAssist`,
      'END:VEVENT', 'END:VCALENDAR',
    ].join('\r\n');
    const blob = new Blob([ics], { type: 'text/calendar; charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = title.slice(0, 40).replace(/[^\wäöüÄÖÜß\s]/g, '').trim() + '.ics';
    a.click();
    URL.revokeObjectURL(url);
    onClose();
  }

  const is = {
    width: '100%', padding: '9px 13px', borderRadius: 10, boxSizing: 'border-box',
    border: '1.5px solid var(--border)', background: 'var(--surface-input)',
    color: 'var(--text-primary)', fontSize: 14, outline: 'none', fontFamily: 'inherit',
  };
  const ls = { display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 5 };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <div style={{
        background: 'var(--surface)', borderRadius: 20, padding: '28px 24px',
        maxWidth: 400, width: '100%', animation: 'fadeInUp 0.25s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--text-primary)', margin: 0 }}>
            📅 Als Kalender-Termin
          </h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex' }}>
            {Icons.close}
          </button>
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={ls}>Titel</label>
          <input value={title} onChange={e => setTitle(e.target.value)} style={is}
            onFocus={e => e.target.style.borderColor = 'var(--accent)'}
            onBlur={e  => e.target.style.borderColor = 'var(--border)'} />
        </div>

        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
          <div style={{ flex: 3 }}>
            <label style={ls}>Datum</label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} style={is}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e  => e.target.style.borderColor = 'var(--border)'} />
          </div>
          <div style={{ flex: 2 }}>
            <label style={ls}>Uhrzeit</label>
            <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} style={is}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e  => e.target.style.borderColor = 'var(--border)'} />
          </div>
          <div style={{ flex: 2 }}>
            <label style={ls}>Dauer (Min.)</label>
            <input type="number" value={duration} onChange={e => setDuration(e.target.value)}
              min="5" max="480" style={is}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e  => e.target.style.borderColor = 'var(--border)'} />
          </div>
        </div>

        <button onClick={download} style={{
          width: '100%', padding: '12px', borderRadius: 12, border: 'none',
          background: 'var(--accent)', color: '#fff', cursor: 'pointer',
          fontSize: 14, fontWeight: 600, transition: 'opacity 0.15s',
        }}
          onMouseEnter={e => e.currentTarget.style.opacity = 0.88}
          onMouseLeave={e => e.currentTarget.style.opacity = 1}
        >
          💾 .ics herunterladen
        </button>
        <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 12, textAlign: 'center', lineHeight: 1.6 }}>
          Öffne die Datei mit Outlook, Apple Kalender, Google Kalender etc.
        </p>
      </div>
    </div>
  );
}

/* ---------- Batch-Upload-Queue ---------- */
function BatchQueuePanel({ queue, onDismiss }) {
  if (!queue || queue.length === 0) return null;
  const done  = queue.filter(i => i.status === 'done').length;
  const total = queue.length;
  return (
    <div style={{
      padding: '10px 16px', borderTop: '1px solid var(--border)',
      background: 'var(--surface-elevated)', flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          Batch-Upload: {done}/{total} abgeschlossen
        </span>
        {done === total && (
          <button onClick={onDismiss} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 12 }}>
            Schließen
          </button>
        )}
      </div>
      {/* Fortschrittsbalken */}
      <div style={{ height: 4, borderRadius: 2, background: 'var(--border)', overflow: 'hidden', marginBottom: 8 }}>
        <div style={{
          height: '100%', borderRadius: 2,
          background: done === total ? '#2a9d5c' : 'var(--accent)',
          width: `${total > 0 ? (done / total) * 100 : 0}%`,
          transition: 'width 0.4s ease',
        }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 140, overflowY: 'auto' }}>
        {queue.map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <span style={{ flexShrink: 0, fontSize: 14 }}>
              {item.status === 'done'    ? '✅' :
               item.status === 'error'  ? '❌' :
               item.status === 'active' ? '⏳' : '⬜'}
            </span>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
              {item.file.name}
            </span>
            {item.status === 'error' && (
              <span style={{ color: 'var(--danger)', fontSize: 11, flexShrink: 0 }}>Fehler</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  Icons, BotAvatar, TypingDots, ChatBubble, QuickReplies,
  OnboardingProgress, Sidebar, ChatInput, ProfileView, SettingsView, ApiKeyModal,
  UrlDownloadForm, DsgvoWarningModal, MODEL_PRICES, MODEL_GROUPS,
  RasterEditorView, MemoryEditorView, TemplateGalleryView, BatchQueuePanel,
  TEMPLATE_CATEGORIES, openPrintWindow,
});
