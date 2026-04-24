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
        {isTyping ? <TypingDots /> : message}
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
function ChatInput({ value, onChange, onSend, placeholder, disabled }) {
  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };
  return (
    <div style={{
      padding: '12px 16px 16px',
      borderTop: '1px solid var(--border)',
      background: 'var(--surface)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 8,
        background: 'var(--surface-input)',
        borderRadius: 16, border: '1.5px solid var(--border)',
        padding: '4px 4px 4px 16px',
        transition: 'border-color 0.2s',
      }}>
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

/* ---------- Settings View ---------- */
function SettingsView({ dark, onToggleDark }) {
  return (
    <div style={{ padding: 24, maxWidth: 600, margin: '0 auto' }}>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Einstellungen</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
        Passe TeacherAssist an deine Bedürfnisse an.
      </p>

      <div style={{
        background: 'var(--surface-elevated)', borderRadius: 14,
        border: '1px solid var(--border)', overflow: 'hidden',
      }}>
        {/* Dark mode */}
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

        {/* Onboarding reset */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Profil zurücksetzen</div>
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>Onboarding erneut durchlaufen</div>
          </div>
          <button style={{
            padding: '8px 16px', borderRadius: 8,
            background: 'transparent', border: '1.5px solid var(--danger)',
            color: 'var(--danger)', cursor: 'pointer', fontSize: 13, fontWeight: 600,
          }}>
            Zurücksetzen
          </button>
        </div>

        {/* About */}
        <div style={{ padding: '16px 20px' }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Über TeacherAssist</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>Version 1.0 · Basiert auf OpenClaw</div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  Icons, BotAvatar, TypingDots, ChatBubble, QuickReplies,
  OnboardingProgress, Sidebar, ChatInput, ProfileView, SettingsView,
});
