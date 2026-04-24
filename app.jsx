/* ============================================
   TeacherAssist – Main App
   ============================================ */

const { useState, useEffect, useRef, useCallback } = React;

/* ---------- Onboarding Script ---------- */
const ONBOARDING_STEPS = [
  {
    id: 'welcome',
    bot: '👋 Hallo! Ich bin dein persönlicher LehrerAssistent.\n\nIch helfe dir bei:\n📚 Unterrichtsplanung & Lehrplankonformität\n📝 Erwartungshorizonte & Bewertungsraster\n✅ Schülerarbeiten anhand klarer Kriterien bewerten\n📖 Lehrpläne einlesen und abrufen\n\nDamit ich dir wirklich helfen kann, richte ich dein Profil erst einmalig ein.\nDas dauert etwa 2 Minuten. Du kannst alles später jederzeit anpassen.\n\nBereit? Dann fangen wir an! 🚀',
    quickReplies: ['Ja, los geht\'s!', 'Erzähl mir mehr'],
    field: null,
    phase: 1,
  },
  {
    id: 'name',
    bot: 'Wie darf ich dich nennen? (Optional – du kannst auch einfach Enter drücken)',
    field: 'name',
    placeholder: 'Dein Name…',
    phase: 2,
  },
  {
    id: 'bundesland',
    bot: 'In welchem Bundesland unterrichtest du?\n(z.B. Bayern, NRW, Berlin, Baden-Württemberg…)',
    field: 'bundesland',
    placeholder: 'Bundesland eingeben…',
    phase: 2,
    quickReplies: ['Bayern', 'NRW', 'Baden-Württemberg', 'Berlin', 'Hessen', 'Niedersachsen'],
  },
  {
    id: 'schulform',
    bot: 'An welcher Schulform unterrichtest du?\n(z.B. Gymnasium, Gesamtschule, Realschule, Grundschule, Mittelschule…)',
    field: 'schulform',
    placeholder: 'Schulform eingeben…',
    phase: 2,
    quickReplies: ['Gymnasium', 'Realschule', 'Gesamtschule', 'Grundschule', 'Mittelschule'],
  },
  {
    id: 'faecher',
    bot: 'Welche Fächer unterrichtest du, und in welchen Klassen?\n\nBitte so eingeben (eine Zeile pro Fach):\nMathematik – 7a, 8b, 9c\nDeutsch – 5a, 7a\n\nDu kannst auch einfach schreiben: "Mathe 7 und 8, Deutsch 5"\n– ich sortiere das dann für dich.',
    field: 'faecher',
    placeholder: 'z.B. Mathe 7a, 8b – Deutsch 5a, 7a',
    phase: 2,
  },
  {
    id: 'besonderheiten',
    bot: 'Gibt es Besonderheiten in deinen Klassen, die ich kennen sollte?\n(z.B. Inklusionsklassen, DaZ-Schüler, sehr leistungsstarke Gruppen, besondere Förderbedarfe…)\n\n(Optional – einfach mit "nein" oder leer überspringen)',
    field: 'besonderheiten',
    placeholder: 'Optional – Enter zum Überspringen',
    phase: 2,
  },
  {
    id: 'methoden',
    bot: 'Hast du Lieblingsmethoden oder Methoden, die du grundsätzlich vermeidest?\n(z.B. "Ich mache gerne Stationenarbeit" oder "kein reiner Frontalunterricht")\n\n(Optional – einfach überspringen)',
    field: 'methoden',
    placeholder: 'Optional – Enter zum Überspringen',
    phase: 2,
  },
  {
    id: 'lehrplan',
    bot: 'Möchtest du direkt einen Lehrplan einrichten?\n\nDas geht so:\n• Schick mir einfach ein Lehrplan-PDF – ich lese es automatisch ein.\n• Oder sag mir Fach + Klasse, ich trage einen Standardeintrag ein.\n• Oder überspringe das jetzt – du kannst das jederzeit nachholen.',
    quickReplies: ['Später einrichten', 'Ich möchte einen Lehrplan angeben'],
    field: 'lehrplan_choice',
    phase: 2,
  },
  {
    id: 'done',
    bot: '✅ Super, dein Profil ist eingerichtet!\n\nIch habe alles gespeichert. Du kannst deine Angaben jederzeit unter "Mein Profil" anpassen.\n\nWie kann ich dir jetzt helfen? Hier ein paar Ideen:\n\n📚 Unterricht planen – Sag mir Fach, Klasse und Thema\n📝 Bewertung erstellen – Ich erstelle Erwartungshorizonte\n✅ Schülerarbeit bewerten – Schick mir eine Arbeit zum Bewerten\n📖 Lehrplan abrufen – Frag mich zu deinem Lehrplan',
    field: null,
    phase: 3,
  },
];

/* ---------- Simulated Bot Responses ---------- */
const BOT_RESPONSES = [
  { match: /unterricht|plan|stunde/i, response: '📚 Klar! Sag mir bitte:\n\n1. Welches Fach?\n2. Welche Klasse?\n3. Welches Thema?\n\nDann erstelle ich dir einen Unterrichtsentwurf.' },
  { match: /bewert|note|korrektur|arbeit/i, response: '📝 Gerne helfe ich beim Bewerten!\n\nSchick mir die Aufgabenstellung und die Schülerarbeit – ich erstelle einen Erwartungshorizont und bewerte die Arbeit anhand klarer Kriterien.' },
  { match: /lehrplan|curriculum/i, response: '📖 Zum Lehrplan kann ich dir helfen!\n\nSag mir einfach Fach und Klassenstufe, dann zeige ich dir die relevanten Kompetenzerwartungen und Inhalte.' },
  { match: /hilfe|help|was kannst/i, response: 'Ich kann dir bei Folgendem helfen:\n\n📚 Unterricht planen – Stundenplanung nach Lehrplan\n📝 Bewertungen erstellen – Erwartungshorizonte & Raster\n✅ Schülerarbeiten bewerten – KI-gestützte Korrektur\n📖 Lehrpläne – Inhalte nachschlagen & verwalten\n\nEinfach loslegen – ich führe dich durch!' },
];

function getSimulatedResponse(text) {
  for (const r of BOT_RESPONSES) {
    if (r.match.test(text)) return r.response;
  }
  return 'Danke für deine Nachricht! Ich helfe dir gerne weiter. Sag mir einfach, was du planst – z.B. "Plane eine Stunde zu Bruchrechnung für die 7a" oder "Erstelle einen Erwartungshorizont für einen Aufsatz".';
}

/* ---------- Main App ---------- */
function App() {
  const [dark, setDark] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ta_dark')) || false; } catch { return false; }
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState('chat'); // chat | profile | settings
  const [onboardingDone, setOnboardingDone] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ta_onboarded')) || false; } catch { return false; }
  });
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [profile, setProfile] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ta_profile')) || {}; } catch { return {}; }
  });
  const [chats, setChats] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('ta_chats'));
      if (saved && saved.length) return saved;
    } catch {}
    return [{ id: 'c1', title: 'Onboarding', messages: [] }];
  });
  const [activeChatId, setActiveChatId] = useState(() => chats[0]?.id || 'c1');
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];

  // Persist
  useEffect(() => { localStorage.setItem('ta_dark', JSON.stringify(dark)); }, [dark]);
  useEffect(() => { localStorage.setItem('ta_profile', JSON.stringify(profile)); }, [profile]);
  useEffect(() => { localStorage.setItem('ta_chats', JSON.stringify(chats)); }, [chats]);
  useEffect(() => { localStorage.setItem('ta_onboarded', JSON.stringify(onboardingDone)); }, [onboardingDone]);

  // Auto-scroll
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [activeChat?.messages, isTyping]);

  // Send onboarding welcome
  useEffect(() => {
    if (!onboardingDone && activeChat.messages.length === 0) {
      addBotMessage(ONBOARDING_STEPS[0].bot);
    }
  }, [activeChatId]);

  // Reset onboarding if chat has stale state
  useEffect(() => {
    if (!onboardingDone && onboardingStep > 0 && activeChat.messages.length === 0) {
      setOnboardingStep(0);
    }
  }, [activeChatId]);

  const addMessage = useCallback((chatId, msg) => {
    setChats(prev => prev.map(c => c.id === chatId ? { ...c, messages: [...c.messages, msg] } : c));
  }, []);

  const addBotMessage = useCallback((text, delay = 600) => {
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      addMessage(activeChatId, { role: 'bot', text, ts: Date.now() });
    }, delay);
  }, [activeChatId, addMessage]);

  const handleSend = useCallback((overrideText) => {
    const text = (overrideText || inputValue).trim();
    if (!text) return;
    setInputValue('');

    addMessage(activeChatId, { role: 'user', text, ts: Date.now() });

    if (!onboardingDone) {
      // Onboarding flow
      const step = ONBOARDING_STEPS[onboardingStep];
      if (step?.field && step.field !== 'lehrplan_choice') {
        const val = text === 'nein' || text === '-' ? '' : text;
        if (step.field === 'faecher') {
          setProfile(p => ({ ...p, faecher: val.split(/[,\n]+/).map(s => s.trim()).filter(Boolean) }));
        } else {
          setProfile(p => ({ ...p, [step.field]: val }));
        }
      }

      const nextIdx = onboardingStep + 1;
      if (nextIdx < ONBOARDING_STEPS.length) {
        setOnboardingStep(nextIdx);
        const nextStep = ONBOARDING_STEPS[nextIdx];
        addBotMessage(nextStep.bot, 800);
        if (nextStep.id === 'done') {
          setTimeout(() => setOnboardingDone(true), 1200);
        }
      }
    } else {
      // Normal chat – show welcome suggestions if first message
      const resp = getSimulatedResponse(text);
      addBotMessage(resp, 900);
      // Update chat title from first user message
      setChats(prev => prev.map(c => {
        if (c.id === activeChatId && (c.title === 'Neuer Chat' || c.title === 'Onboarding')) {
          return { ...c, title: text.slice(0, 35) + (text.length > 35 ? '…' : '') };
        }
        return c;
      }));
    }
  }, [inputValue, activeChatId, onboardingDone, onboardingStep, addMessage, addBotMessage]);

  const handleQuickReply = useCallback((text) => {
    handleSend(text);
  }, [handleSend]);

  const handleNewChat = useCallback(() => {
    const id = 'c' + Date.now();
    setChats(prev => [{ id, title: 'Neuer Chat', messages: [] }, ...prev]);
    setActiveChatId(id);
    setCurrentView('chat');
    setSidebarOpen(false);
  }, []);

  const handleDeleteChat = useCallback((id) => {
    setChats(prev => {
      const filtered = prev.filter(c => c.id !== id);
      if (!filtered.length) filtered.push({ id: 'c' + Date.now(), title: 'Neuer Chat', messages: [] });
      if (activeChatId === id) setActiveChatId(filtered[0].id);
      return filtered;
    });
  }, [activeChatId]);

  const handleNavigate = useCallback((view) => {
    setCurrentView(view);
    setSidebarOpen(false);
  }, []);

  const currentOnboardingStep = !onboardingDone ? ONBOARDING_STEPS[onboardingStep] : null;
  const showQuickReplies = currentOnboardingStep?.quickReplies && !isTyping &&
    activeChat.messages.length > 0 && activeChat.messages[activeChat.messages.length - 1]?.role === 'bot';

  const onboardingTotal = 7; // visible steps (excluding welcome & done)
  const onboardingCurrent = Math.min(Math.max(onboardingStep, 1), onboardingTotal);

  return (
    <div className={dark ? 'dark' : 'light'} style={{
      height: '100dvh', display: 'flex', flexDirection: 'column',
      background: 'var(--bg)', color: 'var(--text-primary)',
      fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif",
      overflow: 'hidden',
    }}>
      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen} onClose={() => setSidebarOpen(false)}
        chats={chats} activeChatId={activeChatId}
        onSelectChat={id => { setActiveChatId(id); setSidebarOpen(false); }}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onNavigate={handleNavigate}
        currentView={currentView}
        dark={dark} onToggleDark={() => setDark(d => !d)}
      />

      {/* Top bar */}
      <header style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 16px', borderBottom: '1px solid var(--border)',
        background: 'var(--surface)', flexShrink: 0, zIndex: 10,
        minHeight: 52,
      }}>
        <button onClick={() => setSidebarOpen(true)} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-secondary)', padding: 4, display: 'flex',
        }}>
          {Icons.menu}
        </button>
        <BotAvatar size={30} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.2 }}>TeacherAssist</div>
          <div style={{ fontSize: 12, color: 'var(--accent)' }}>
            {isTyping ? 'schreibt…' : 'Online'}
          </div>
        </div>
        <button onClick={() => setDark(d => !d)} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-secondary)', padding: 4, display: 'flex',
        }}>
          {dark ? Icons.sun : Icons.moon}
        </button>
      </header>

      {/* Onboarding Progress */}
      {!onboardingDone && onboardingStep > 0 && (
        <OnboardingProgress step={onboardingCurrent} total={onboardingTotal} />
      )}

      {/* Main Content */}
      {currentView === 'chat' ? (
        <>
          {/* Messages */}
          <div ref={chatContainerRef} style={{
            flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
            display: 'flex', flexDirection: 'column', gap: 14,
          }}>
            {activeChat.messages.map((msg, i) => (
              <ChatBubble key={i} message={msg.text} isBot={msg.role === 'bot'} />
            ))}
            {isTyping && <ChatBubble isBot isTyping />}
            {showQuickReplies && (
              <QuickReplies options={currentOnboardingStep.quickReplies} onSelect={handleQuickReply} />
            )}
            <div ref={messagesEndRef}></div>
          </div>

          {/* Input */}
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={() => handleSend()}
            placeholder={currentOnboardingStep?.placeholder || 'Nachricht eingeben…'}
            disabled={isTyping}
          />
        </>
      ) : currentView === 'profile' ? (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <ProfileView profile={profile} onUpdate={setProfile} />
        </div>
      ) : (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <SettingsView dark={dark} onToggleDark={() => setDark(d => !d)} />
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
