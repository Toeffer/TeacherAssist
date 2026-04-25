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
};

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
function ChatBubble({ message, isBot, isTyping }) {
  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'flex-start',
      flexDirection: isBot ? 'row' : 'row-reverse',
      maxWidth: '100%',
      animation: 'fadeInUp 0.3s ease',
    }}>
      {isBot && <BotAvatar />}
      <div style={{
        background: isBot ? 'var(--bubble-bot)' : 'var(--bubble-user)',
        color: isBot ? 'var(--text-primary)' : 'var(--bubble-user-text)',
        padding: '10px 16px',
        borderRadius: isBot ? '4px 18px 18px 18px' : '18px 4px 18px 18px',
        maxWidth: '75%',
        fontSize: 15, lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {isTyping || !message ? <TypingDots /> : message}
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
function ChatInput({ value, onChange, onSend, placeholder, disabled, onFileUpload, toolOnline, showDsgvoHint, showLocalHint }) {
  const fileRef = React.useRef(null);
  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); }
  };
  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (file && onFileUpload) onFileUpload(file);
    e.target.value = '';
  };
  return (
    <div style={{ padding: '12px 16px 16px', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 8,
        background: 'var(--surface-input)',
        borderRadius: 16, border: '1.5px solid var(--border)',
        padding: '4px 4px 4px 8px',
        transition: 'border-color 0.2s',
      }}>
        {toolOnline && (
          <>
            <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFile} />
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
          </>
        )}
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder || 'Nachricht eingeben…'}
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
          📎 PDF-Lehrplan hochladen – wird automatisch in die Wissensdatenbank eingelesen
        </div>
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

function SettingsView({ dark, onToggleDark, apiKey, onApiKeyChange, model, onModelChange, onResetOnboarding, toolStatus, ragDocCount, onFileUpload, onClearKnowledge, onUrlDownload, profile, provider, onProviderChange, ollamaModel, onOllamaModelChange, ollamaStatus, ollamaModels, openrouterStatus, isFallbackActive, effectiveProvider }) {
  const [showKey, setShowKey] = React.useState(false);
  const [keyInput, setKeyInput] = React.useState(apiKey || '');
  const [saved, setSaved] = React.useState(false);

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

Object.assign(window, {
  Icons, BotAvatar, TypingDots, ChatBubble, QuickReplies,
  OnboardingProgress, Sidebar, ChatInput, ProfileView, SettingsView, ApiKeyModal,
  UrlDownloadForm, DsgvoWarningModal, MODEL_PRICES, MODEL_GROUPS,
});
