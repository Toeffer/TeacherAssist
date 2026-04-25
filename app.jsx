/* ============================================
   TeacherAssist – Main App
   ============================================ */

const { useState, useEffect, useRef, useCallback, useMemo } = React;

/* ---------- Onboarding Script ---------- */
const ONBOARDING_STEPS = [
  {
    id: 'welcome',
    bot: '👋 Hallo! Ich bin dein persönlicher LehrerAssistent.\n\nIch helfe dir bei:\n📚 Unterrichtsplanung & Lehrplankonformität\n📝 Erwartungshorizonte & Bewertungsraster\n✅ Schülerarbeiten anhand klarer Kriterien bewerten\n📖 Lehrpläne einlesen und abrufen\n\nDamit ich dir wirklich helfen kann, richte ich dein Profil erst einmalig ein.\nDas dauert etwa 2 Minuten. Du kannst alles später jederzeit anpassen.\n\nBereit? Dann fangen wir an! 🚀',
    quickReplies: ["Ja, los geht's!", 'Erzähl mir mehr'],
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
    quickReplies: ['Gymnasium', 'Realschule', 'Gesamtschule', 'Grundschule', 'Mittelschule', 'Gemeinschaftsschule'],
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

/* ---------- Onboarding: Frage-Erkennung & FAQ ---------- */
function isOnboardingQuestion(text) {
  if (text.includes('?')) return true;
  const lower = text.trim().toLowerCase();
  const starters = ['was ', 'wie ', 'wann ', 'warum ', 'wieso ', 'weshalb ', 'wer ', 'wo ', 'welche', 'kann ', 'kannst ', 'darf ', 'gibt ', 'haben ', 'hast ', 'muss ', 'musst '];
  return starters.some(s => lower.startsWith(s));
}

const ONBOARDING_FAQ = [
  {
    keys: ['kostet', 'kosten', 'preis', 'euro', 'geld', 'günstig', 'teuer', 'bezahl'],
    answer: 'TeacherAssist selbst ist kostenlos. Du bezahlst nur direkt bei OpenRouter für KI-Anfragen – meist wenige Cent pro Unterrichtsstunde. Günstige Modelle wie DeepSeek V3 oder V4 Flash kosten unter 1 € pro 1.000 Anfragen.',
  },
  {
    keys: ['datenschutz', 'dsgvo', 'daten', 'schüler', 'sicher', 'privat'],
    answer: 'Keine Schülerdaten verlassen deinen Computer. Chats und Profil werden nur lokal im Browser gespeichert. An die KI wird nur dein Fragetext geschickt – keine Klassen- oder Schülerdaten.',
  },
  {
    keys: ['openrouter', 'api', 'key', 'schlüssel', 'anmeld', 'konto', 'registr'],
    answer: 'OpenRouter ist ein Dienst, der Zugang zu vielen KI-Modellen bündelt. Du erstellst ein kostenloses Konto auf openrouter.ai und erhältst einen API-Key (beginnt mit sk-or-v1-). Diesen trägst du nach dem Einrichten in den Einstellungen ein.',
  },
  {
    keys: ['lehrplan', 'pdf', 'hochladen', 'einlesen', 'dokument'],
    answer: 'Nach dem Einrichten kannst du Lehrplan-PDFs hochladen – per 📎-Button im Chat oder unter Einstellungen → Wissensdatenbank. Sie werden lokal per OCR eingelesen, sodass ich bei jeder Anfrage automatisch passende Abschnitte einblende.',
  },
  {
    keys: ['wie funktioniert', 'was macht', 'wozu', 'wofür', 'hilft', 'kann es', 'features', 'funktion'],
    answer: 'Ich helfe bei Unterrichtsplanung, Bewertungsrastern, Schülerkorrektur und Lehrplanfragen – immer passend zu deiner Schule und deinen Fächern. Einfach auf Deutsch schreiben, was du brauchst.',
  },
];

function onboardingFaqAnswer(text) {
  const lower = text.toLowerCase();
  for (const entry of ONBOARDING_FAQ) {
    if (entry.keys.some(k => lower.includes(k))) return entry.answer;
  }
  return null;
}

/* ---------- Eingabe-Normalisierung (Rechtschreibtoleranz) ---------- */
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => i === 0 ? j : j === 0 ? i : 0)
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
  return dp[m][n];
}

const BUNDESLAENDER = [
  'Baden-Württemberg','Bayern','Berlin','Brandenburg','Bremen',
  'Hamburg','Hessen','Mecklenburg-Vorpommern','Niedersachsen',
  'Nordrhein-Westfalen','Rheinland-Pfalz','Saarland','Sachsen',
  'Sachsen-Anhalt','Schleswig-Holstein','Thüringen',
];
const BL_ALIASES = {
  'nrw':'Nordrhein-Westfalen','bw':'Baden-Württemberg','bawü':'Baden-Württemberg',
  'meck-pomm':'Mecklenburg-Vorpommern','meckpomm':'Mecklenburg-Vorpommern',
  'rp':'Rheinland-Pfalz','sh':'Schleswig-Holstein',
  'sachsen-anhalt':'Sachsen-Anhalt','thüringen':'Thüringen',
};

function normalizeBundesland(input) {
  if (!input.trim()) return input;
  const lower = input.trim().toLowerCase();
  if (BL_ALIASES[lower]) return BL_ALIASES[lower];
  const exact = BUNDESLAENDER.find(bl => bl.toLowerCase() === lower);
  if (exact) return exact;
  let best = input, bestDist = Infinity;
  for (const bl of BUNDESLAENDER) {
    const d = levenshtein(lower, bl.toLowerCase());
    if (d < bestDist) { bestDist = d; best = bl; }
  }
  return bestDist <= 3 ? best : input;
}

const SCHULFORMEN = [
  'Gymnasium','Realschule','Gesamtschule','Grundschule','Mittelschule',
  'Hauptschule','Oberschule','Berufsschule','Berufsgymnasium','Förderschule',
  'IGS','KGS','FOS','BOS','Werkrealschule','Gemeinschaftsschule',
];

function normalizeSchulform(input) {
  if (!input.trim()) return input;
  const lower = input.trim().toLowerCase();
  const exact = SCHULFORMEN.find(s => s.toLowerCase() === lower);
  if (exact) return exact;
  let best = input, bestDist = Infinity;
  for (const s of SCHULFORMEN) {
    const d = levenshtein(lower, s.toLowerCase());
    if (d < bestDist) { bestDist = d; best = s; }
  }
  return bestDist <= 2 ? best : input;
}

const FACH_MAP = {
  'mathe':'Mathematik','math':'Mathematik','mathemathik':'Mathematik',
  'deutsch':'Deutsch','englisch':'Englisch','english':'Englisch',
  'bio':'Biologie','biologie':'Biologie',
  'physik':'Physik','chemie':'Chemie',
  'geo':'Geografie','geographie':'Geografie','erdkunde':'Erdkunde',
  'geschichte':'Geschichte','musik':'Musik','sport':'Sport',
  'kunst':'Kunst','religion':'Religion','ethik':'Ethik',
  'informatik':'Informatik','sozialkunde':'Sozialkunde',
  'politik':'Politik','wirtschaft':'Wirtschaft',
  'französisch':'Französisch','franzoesisch':'Französisch',
  'latein':'Latein','spanisch':'Spanisch','russisch':'Russisch',
  'gemeinschaftskunde':'Gemeinschaftskunde','nwt':'NWT',
};

function normalizeFachname(entry) {
  if (!entry) return '';
  const m = entry.match(/^([a-zA-ZäöüÄÖÜß]+)([\s\-–].+)?$/);
  if (!m) return entry;
  const key = m[1].toLowerCase();
  const rest = m[2] || '';
  const mapped = FACH_MAP[key];
  if (mapped) return mapped + rest;
  return m[1].charAt(0).toUpperCase() + m[1].slice(1) + rest;
}

/* ---------- DSGVO: Personenbezogene Daten erkennen & anonymisieren ---------- */
function detectPersonalData(text) {
  const findings = [];
  // E-Mail-Adressen
  if (/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/.test(text))
    findings.push({ type: 'E-Mail-Adresse', auto: true });
  // Telefonnummern (deutsche Formate)
  if (/(\+49[\s\-]?|0049[\s\-]?|0\d{2,5}[\s\-\/])\d[\d\s\-\/]{4,}/.test(text))
    findings.push({ type: 'Telefonnummer', auto: true });
  // Geburtsdatum (nur wenn im Kontext von "geboren" / "Geburtstag" / "geb.")
  if (/(geb\b\.?|geboren|geburtstag|geburtsdatum)/i.test(text) &&
      /\b\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4}\b/.test(text))
    findings.push({ type: 'Geburtsdatum', auto: true });
  // Möglicher Personenname nach typischen Schlüsselwörtern
  if (/(schüler[in]?|lernende[r]?|kind|elternteil?|sohn|tochter|sus)\s+(von\s+)?[A-ZÄÖÜ][a-zäöüß]{2,}(\s+[A-ZÄÖÜ][a-zäöüß]{2,})?/i.test(text) ||
      /\b(heißt|namens|vorname|nachname|familienname|name:)\s+[A-ZÄÖÜ][a-zäöüß]{2,}/i.test(text))
    findings.push({ type: 'Möglicher Personenname', auto: false });
  return findings;
}

function anonymizeText(text) {
  let r = text;
  r = r.replace(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g, '[E-Mail]');
  r = r.replace(/(\+49[\s\-]?|0049[\s\-]?|0\d{2,5}[\s\-\/])\d[\d\s\-\/]{4,}/g, '[Telefon]');
  if (/(geb\b\.?|geboren|geburtstag|geburtsdatum)/i.test(r))
    r = r.replace(/\b\d{1,2}[.\-]\d{1,2}[.\-]\d{2,4}\b/g, '[Datum]');
  return r;
}

/* ---------- System Prompt ---------- */
function buildSystemPrompt(profile) {
  const lines = [
    'Du bist TeacherAssist, ein KI-Assistent speziell für deutsche Lehrkräfte.',
    'Du hilfst professionell-kollegial bei Unterrichtsplanung, Bewertungserstellung, Schülerkorrektur und Lehrplanfragen.',
    '',
    '## Grundprinzipien',
    '- Du machst Vorschläge – die Lehrkraft entscheidet immer selbst.',
    '- Ton: professionell-kollegial, wie ein erfahrener Kollege.',
    '- Bewertungen immer als "Vorschlag" kennzeichnen.',
    '- AFB-Verteilung bei Aufgaben: ~30% AFB I (Reproduktion) / ~40% AFB II (Reorganisation) / ~30% AFB III (Transfer).',
    '- Zeitangaben in Stundenentwürfen: Einstieg max. 10 Min., Sicherung min. 5 Min.',
    '- Lehrplanbezüge ohne eindeutige Quelle mit [*] markieren.',
    '- Keine Schülernamen verwenden (DSGVO) – bei Bedarf SuS-01, SuS-02 etc.',
    '- Alle Antworten auf Deutsch.',
    '- Antworte strukturiert mit Markdown (##, - Listen, **fett**) für bessere Lesbarkeit.',
  ];

  if (profile && Object.keys(profile).length > 0) {
    lines.push('', '## Lehrerprofil');
    if (profile.name) lines.push(`- Name: ${profile.name}`);
    if (profile.bundesland) lines.push(`- Bundesland: ${profile.bundesland}`);
    if (profile.schulform === 'Gemeinschaftsschule') {
      lines.push('- Schulform: Gemeinschaftsschule (kombiniert Gymnasium-Zweig & Regelschul-Zweig)');
      lines.push('- Beim Planen und Bewerten immer beide Zweige berücksichtigen, sofern kein konkreter Zweig genannt wird.');
      lines.push('  Lehrplaninhalte sind in der Wissensdatenbank mit dem Präfix "Gymnasium –" bzw. "Regelschule –" gespeichert; diese Kennzeichnung ist in den RAG-Ergebnissen sichtbar.');
    } else if (profile.schulform) {
      lines.push(`- Schulform: ${profile.schulform}`);
    }
    if (profile.faecher?.length) lines.push(`- Fächer & Klassen: ${profile.faecher.join(', ')}`);
    if (profile.besonderheiten) lines.push(`- Klassenbesonderheiten: ${profile.besonderheiten}`);
    if (profile.methoden) lines.push(`- Bevorzugte Methoden: ${profile.methoden}`);
  }

  return lines.join('\n');
}

/* ---------- RAG-Kontext aus Tool-Server ---------- */
async function fetchRagContext(query) {
  try {
    const res = await fetch(
      `http://localhost:8789/search?q=${encodeURIComponent(query)}&limit=4`,
      { signal: AbortSignal.timeout(3000) }
    );
    if (!res.ok) return '';
    const { results } = await res.json();
    if (!results?.length) return '';
    const blocks = results.map(r => `[Quelle: ${r.source}]\n${r.text}`).join('\n\n---\n\n');
    return `\n\n## Relevante Lehrplaninhalte (automatisch eingeblendet)\n${blocks}`;
  } catch {
    return '';
  }
}

/* ---------- LLM API (OpenRouter & Ollama) ---------- */
async function callLLM(chatMessages, profile, apiKey, model, onChunk, ragContext = '', provider = 'openrouter', ollamaModel = 'gemma3:4b') {
  const isOllama = provider === 'ollama';
  const endpoint = isOllama
    ? 'http://localhost:11434/v1/chat/completions'
    : 'https://openrouter.ai/api/v1/chat/completions';
  const activeModel = isOllama ? ollamaModel : model;

  const apiMessages = [
    { role: 'system', content: buildSystemPrompt(profile) + ragContext },
    ...chatMessages
      .filter(m => m.text && m.text.trim())
      .map(m => ({ role: m.role === 'bot' ? 'assistant' : 'user', content: m.text })),
  ];

  const headers = { 'Content-Type': 'application/json' };
  if (!isOllama) {
    headers['Authorization'] = `Bearer ${apiKey}`;
    headers['HTTP-Referer'] = 'http://localhost:8788';
    headers['X-Title'] = 'TeacherAssist';
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify({ model: activeModel, messages: apiMessages, stream: true }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error?.message || `HTTP-Fehler ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6).trim();
      if (data === '[DONE]') return;
      try {
        const parsed = JSON.parse(data);
        const content = parsed.choices?.[0]?.delta?.content;
        if (content) onChunk(content);
      } catch {}
    }
  }
}

/* ---------- Main App ---------- */
function App() {
  const [dark, setDark] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ta_dark')) || false; } catch { return false; }
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentView, setCurrentView] = useState('chat');
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
  const [activeChatId, setActiveChatId] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('ta_chats'));
      return saved?.[0]?.id || 'c1';
    } catch { return 'c1'; }
  });
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('ta_api_key') || '');
  const [model, setModel] = useState(() => localStorage.getItem('ta_model') || 'deepseek/deepseek-chat');
  const [apiKeyModalDismissed, setApiKeyModalDismissed] = useState(false);
  const [toolStatus, setToolStatus] = useState('unknown');
  const [ragDocCount, setRagDocCount] = useState(0);
  const [dsgvoCheck, setDsgvoCheck] = useState(null);
  const [provider, setProvider] = useState(() => localStorage.getItem('ta_provider') || 'openrouter');
  const [ollamaModel, setOllamaModel] = useState(() => localStorage.getItem('ta_ollama_model') || 'gemma3:4b');
  const [ollamaStatus, setOllamaStatus] = useState('unknown');
  const [ollamaModels, setOllamaModels] = useState([]);
  const [openrouterStatus, setOpenrouterStatus] = useState('unknown');
  const chatContainerRef = useRef(null);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];

  useEffect(() => { localStorage.setItem('ta_dark', JSON.stringify(dark)); }, [dark]);
  useEffect(() => { localStorage.setItem('ta_profile', JSON.stringify(profile)); }, [profile]);
  useEffect(() => { localStorage.setItem('ta_chats', JSON.stringify(chats)); }, [chats]);
  useEffect(() => { localStorage.setItem('ta_onboarded', JSON.stringify(onboardingDone)); }, [onboardingDone]);
  useEffect(() => { localStorage.setItem('ta_api_key', apiKey); }, [apiKey]);
  useEffect(() => { localStorage.setItem('ta_model', model); }, [model]);
  useEffect(() => { localStorage.setItem('ta_provider', provider); }, [provider]);
  useEffect(() => { localStorage.setItem('ta_ollama_model', ollamaModel); }, [ollamaModel]);

  // Provider-Wahl auf Disk speichern, damit start.bat OpenClaw korrekt startet
  useEffect(() => {
    fetch('http://localhost:8789/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, ollamaModel, model }),
    }).catch(() => {});
  }, [provider, ollamaModel, model]);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      // Tool-Server
      try {
        const res = await fetch('http://localhost:8789/health', { signal: AbortSignal.timeout(2000) });
        if (cancelled) return;
        if (res.ok) {
          setToolStatus('online');
          const col = await fetch('http://localhost:8789/collections').then(r => r.json()).catch(() => ({}));
          if (!cancelled) setRagDocCount(col.chunks || 0);
        } else {
          if (!cancelled) setToolStatus('offline');
        }
      } catch {
        if (!cancelled) setToolStatus('offline');
      }
      // Ollama
      try {
        const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) });
        if (cancelled) return;
        if (res.ok) {
          const data = await res.json();
          const models = (data.models || []).map(m => m.name);
          if (!cancelled) {
            setOllamaModels(models);
            setOllamaStatus('online');
            setOllamaModel(prev => models.includes(prev) ? prev : (models[0] || prev));
          }
        } else {
          if (!cancelled) setOllamaStatus('offline');
        }
      } catch {
        if (!cancelled) setOllamaStatus('offline');
      }
      // OpenRouter-Erreichbarkeit (reiner Netzwerk-Check, kein API-Call)
      try {
        await fetch('https://openrouter.ai', { method: 'HEAD', mode: 'no-cors', signal: AbortSignal.timeout(4000) });
        if (!cancelled) setOpenrouterStatus('online');
      } catch {
        if (!cancelled) setOpenrouterStatus('offline');
      }
    };
    check();
    const id = setInterval(check, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [activeChat?.messages, isTyping, streamingText]);

  useEffect(() => {
    if (!onboardingDone && activeChat.messages.length === 0) {
      addBotMessage(ONBOARDING_STEPS[0].bot);
    }
  }, [activeChatId]);

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

  const handleSend = useCallback(async (overrideText, skipDsgvo = false) => {
    const text = (overrideText || inputValue).trim();
    if (!text || isStreaming || isTyping) return;
    setInputValue('');

    // DSGVO-Sperre: nur prüfen wenn Daten tatsächlich die Cloud erreichen würden
    if (!skipDsgvo && onboardingDone && effectiveProvider === 'openrouter' && apiKey) {
      const findings = detectPersonalData(text);
      if (findings.length > 0) {
        setDsgvoCheck({ text, findings });
        return;
      }
    }

    const userMsg = { role: 'user', text, ts: Date.now() };
    addMessage(activeChatId, userMsg);

    if (!onboardingDone) {
      const step = ONBOARDING_STEPS[onboardingStep];

      // Rückfragen während eines Feld-Schritts erkennen und beantworten
      if (step?.field && step.field !== 'lehrplan_choice' && isOnboardingQuestion(text)) {
        const faqAnswer = onboardingFaqAnswer(text);
        if (faqAnswer) {
          addBotMessage(faqAnswer, 700);
          setTimeout(() => addBotMessage(`Zurück zur Einrichtung:\n${step.bot}`, 1500), 1800);
        } else if (provider === 'ollama' ? ollamaStatus === 'online' : !!apiKey) {
          setIsTyping(true);
          let answer = '';
          try {
            await callLLM(
              [{ role: 'user', text }], {},
              apiKey, model,
              chunk => { answer += chunk; },
              '\n\nHinweis: Beantworte die Rückfrage kurz und hilfreich; weise dann darauf hin, dass das Profil noch fertig eingerichtet werden muss.',
              provider, ollamaModel
            );
          } catch { answer = 'Das beantworte ich gerne – lass uns aber erst das Profil abschließen!'; }
          setIsTyping(false);
          addMessage(activeChatId, { role: 'bot', text: answer || 'Gerne! Lass uns aber erst das Profil fertig einrichten.', ts: Date.now() });
          setTimeout(() => addBotMessage(`Zurück zur Einrichtung:\n${step.bot}`, 600), 900);
        } else {
          addBotMessage(`Gute Frage! Das erkläre ich dir gerne – lass uns aber kurz das Profil abschließen.\n\n${step.bot}`, 800);
        }
        return;
      }

      // Feldwert normalisiert speichern
      if (step?.field && step.field !== 'lehrplan_choice') {
        const raw = text === 'nein' || text === '-' ? '' : text;
        if (step.field === 'faecher') {
          const items = raw.split(/[,\n]+/).map(s => normalizeFachname(s.trim())).filter(Boolean);
          setProfile(p => ({ ...p, faecher: items }));
        } else if (step.field === 'bundesland') {
          setProfile(p => ({ ...p, bundesland: normalizeBundesland(raw) }));
        } else if (step.field === 'schulform') {
          setProfile(p => ({ ...p, schulform: normalizeSchulform(raw) }));
        } else {
          setProfile(p => ({ ...p, [step.field]: raw }));
        }
      }

      const nextIdx = onboardingStep + 1;
      if (nextIdx < ONBOARDING_STEPS.length) {
        setOnboardingStep(nextIdx);
        const nextStep = ONBOARDING_STEPS[nextIdx];
        let botMsg = nextStep.bot;
        if (nextStep.id === 'lehrplan' && profile.schulform === 'Gemeinschaftsschule') {
          botMsg = 'Da du an einer **Gemeinschaftsschule** unterrichtest, kannst du nach dem Einrichten zwei getrennte Lehrpläne hinterlegen:\n\n🎓 **Gymnasium-Zweig** – Lehrplan für den gymnasialen Zweig\n📘 **Regelschule-Zweig** – Lehrplan für den Regelschulzweig\n\nBeides geht unter **Einstellungen → Wissensdatenbank**, jeweils mit Zweig-Kennzeichnung. Ich berücksichtige dann bei jeder Anfrage automatisch beide Zweige.';
        }
        addBotMessage(botMsg, 800);
        if (nextStep.id === 'done') {
          setTimeout(() => setOnboardingDone(true), 1200);
        }
      }
      return;
    }

    if (provider === 'openrouter' && !apiKey && effectiveProvider !== 'ollama') {
      setTimeout(() => {
        addMessage(activeChatId, {
          role: 'bot',
          text: '⚠️ Kein API-Key konfiguriert.\n\nBitte trage deinen OpenRouter-Schlüssel unter Einstellungen ein.\nDen Key bekommst du kostenlos auf openrouter.ai',
          ts: Date.now(),
        });
        setCurrentView('settings');
      }, 300);
      return;
    }
    if (provider === 'ollama' && ollamaStatus !== 'online' && effectiveProvider !== 'openrouter') {
      setTimeout(() => {
        addMessage(activeChatId, {
          role: 'bot',
          text: '⚠️ Ollama ist nicht erreichbar.\n\nStelle sicher, dass Ollama läuft – suche das Ollama-Symbol in der Taskleiste oder starte in der Eingabeaufforderung:\n`ollama serve`',
          ts: Date.now(),
        });
        setCurrentView('settings');
      }, 300);
      return;
    }

    setChats(prev => prev.map(c => {
      if (c.id === activeChatId && (c.title === 'Neuer Chat' || c.title === 'Onboarding')) {
        return { ...c, title: text.slice(0, 35) + (text.length > 35 ? '…' : '') };
      }
      return c;
    }));

    const historySnapshot = chats.find(c => c.id === activeChatId)?.messages || [];
    const currentMessages = [...historySnapshot, userMsg];

    setIsStreaming(true);
    setStreamingText('');

    const ragContext = toolStatus === 'online' && ragDocCount > 0 ? await fetchRagContext(text) : '';

    let fullText = '';
    try {
      await callLLM(currentMessages, profile, apiKey, model, (chunk) => {
        fullText += chunk;
        setStreamingText(fullText);
      }, ragContext, effectiveProvider, ollamaModel);
    } catch (err) {
      fullText = effectiveProvider === 'ollama'
        ? `⚠️ Ollama-Fehler: ${err.message}\n\nLäuft Ollama noch? Prüfe die Einstellungen.`
        : `⚠️ Fehler bei der API-Anfrage: ${err.message}\n\nBitte prüfe deinen API-Key in den Einstellungen.`;
    }

    setIsStreaming(false);
    setStreamingText('');
    addMessage(activeChatId, { role: 'bot', text: fullText || '(Keine Antwort erhalten)', ts: Date.now() });
  }, [inputValue, activeChatId, chats, onboardingDone, onboardingStep, profile, apiKey, model, isStreaming, isTyping, toolStatus, ragDocCount, addMessage, addBotMessage, provider, ollamaModel, ollamaStatus, openrouterStatus, effectiveProvider]);

  const handleFileUpload = useCallback(async (file, track) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      addMessage(activeChatId, { role: 'bot', text: '⚠️ Bitte nur PDF-Dateien hochladen.', ts: Date.now() });
      return;
    }
    const sourceName = track ? `${track} – ${file.name}` : file.name;
    addMessage(activeChatId, { role: 'user', text: `📄 ${sourceName} wird hochgeladen…`, ts: Date.now() });
    setIsTyping(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const upRes = await fetch('http://localhost:8789/upload', { method: 'POST', body: formData });
      if (!upRes.ok) throw new Error('Upload fehlgeschlagen');
      const { saved } = await upRes.json();
      if (!saved?.length) throw new Error('Keine Datei gespeichert');

      const inRes = await fetch('http://localhost:8789/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: saved[0], source: sourceName }),
      });
      const data = await inRes.json();
      if (!inRes.ok || data.error) throw new Error(data.error || 'Verarbeitung fehlgeschlagen');

      setIsTyping(false);
      setRagDocCount(n => n + data.chunks);
      addMessage(activeChatId, {
        role: 'bot',
        text: `✅ **${sourceName}** wurde eingelesen!\n\n${data.chunks} Abschnitte · ca. ${(data.words || 0).toLocaleString('de-DE')} Wörter\n\nDu kannst jetzt Fragen zu diesem Lehrplan stellen – ich finde automatisch den passenden Kontext.`,
        ts: Date.now(),
      });
    } catch (err) {
      setIsTyping(false);
      addMessage(activeChatId, {
        role: 'bot',
        text: `⚠️ PDF-Verarbeitung fehlgeschlagen: ${err.message}\n\nIst der Tool-Server gestartet? (start.bat neu starten)`,
        ts: Date.now(),
      });
    }
  }, [activeChatId, addMessage]);

  const handleClearKnowledge = useCallback(async () => {
    if (!confirm('Gesamte Wissensdatenbank leeren?')) return;
    try {
      await fetch('http://localhost:8789/clear', { method: 'POST' });
      setRagDocCount(0);
    } catch (err) {
      addMessage(activeChatId, { role: 'bot', text: `⚠️ Löschen fehlgeschlagen: ${err.message}`, ts: Date.now() });
    }
  }, [activeChatId, addMessage]);

  const handleUrlDownload = useCallback(async (url, track) => {
    const baseFilename = url.split('/').pop().split('?')[0] || 'lehrplan.pdf';
    const sourceName = track ? `${track} – ${baseFilename}` : baseFilename;
    addMessage(activeChatId, { role: 'user', text: `🔗 PDF herunterladen${track ? ` [${track}-Zweig]` : ''}: ${url}`, ts: Date.now() });
    setIsTyping(true);
    try {
      const dlRes = await fetch('http://localhost:8789/download-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, source: sourceName }),
      });
      const dlData = await dlRes.json();
      if (!dlRes.ok || dlData.error) throw new Error(dlData.error || 'Download fehlgeschlagen');

      const inRes = await fetch('http://localhost:8789/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: dlData.saved[0], source: dlData.filename }),
      });
      const data = await inRes.json();
      if (!inRes.ok || data.error) throw new Error(data.error || 'Verarbeitung fehlgeschlagen');

      setIsTyping(false);
      setRagDocCount(n => n + data.chunks);
      addMessage(activeChatId, {
        role: 'bot',
        text: `✅ **${dlData.filename}** heruntergeladen und eingelesen!\n\n${data.chunks} Abschnitte · ca. ${(data.words || 0).toLocaleString('de-DE')} Wörter\n\nDu kannst jetzt Fragen zu diesem Lehrplan stellen.`,
        ts: Date.now(),
      });
    } catch (err) {
      setIsTyping(false);
      addMessage(activeChatId, {
        role: 'bot',
        text: `⚠️ Download fehlgeschlagen: ${err.message}\n\nHinweis: Nur direkte PDF-Links funktionieren (die URL muss direkt auf eine .pdf-Datei zeigen).`,
        ts: Date.now(),
      });
    }
  }, [activeChatId, addMessage]);

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

  const handleResetOnboarding = useCallback(() => {
    if (!confirm('Profil wirklich zurücksetzen? Das Onboarding startet neu.')) return;
    localStorage.removeItem('ta_onboarded');
    localStorage.removeItem('ta_profile');
    localStorage.removeItem('ta_chats');
    setOnboardingDone(false);
    setOnboardingStep(0);
    setProfile({});
    const newId = 'c' + Date.now();
    setChats([{ id: newId, title: 'Onboarding', messages: [] }]);
    setActiveChatId(newId);
    setCurrentView('chat');
    setSidebarOpen(false);
  }, []);

  // Effektiv verwendeter Provider (berücksichtigt Fallback bei Nichterreichbarkeit)
  const effectiveProvider = useMemo(() => {
    if (provider === 'openrouter' && openrouterStatus === 'offline' && ollamaStatus === 'online') return 'ollama';
    if (provider === 'ollama' && ollamaStatus === 'offline' && apiKey && openrouterStatus === 'online') return 'openrouter';
    return provider;
  }, [provider, openrouterStatus, ollamaStatus, apiKey]);
  const isFallbackActive = effectiveProvider !== provider;

  const showApiKeyModal = onboardingDone && provider === 'openrouter' && !apiKey && !apiKeyModalDismissed;

  const currentOnboardingStep = !onboardingDone ? ONBOARDING_STEPS[onboardingStep] : null;
  const isBusy = isTyping || isStreaming;
  const showQuickReplies = currentOnboardingStep?.quickReplies && !isBusy &&
    activeChat.messages.length > 0 && activeChat.messages[activeChat.messages.length - 1]?.role === 'bot';

  const onboardingTotal = 7;
  const onboardingCurrent = Math.min(Math.max(onboardingStep, 1), onboardingTotal);

  return (
    <div className={dark ? 'dark' : 'light'} style={{
      height: '100dvh', display: 'flex', flexDirection: 'column',
      background: 'var(--bg)', color: 'var(--text-primary)',
      fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif",
      overflow: 'hidden',
    }}>
      <Sidebar
        open={sidebarOpen} onClose={() => setSidebarOpen(false)}
        chats={chats} activeChatId={activeChatId}
        onSelectChat={id => { setActiveChatId(id); setSidebarOpen(false); setCurrentView('chat'); }}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onNavigate={handleNavigate}
        currentView={currentView}
        dark={dark} onToggleDark={() => setDark(d => !d)}
      />

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
          {(() => {
            const isActive = isFallbackActive || (provider === 'ollama' ? ollamaStatus === 'online' : !!apiKey);
            const label = isStreaming ? 'antwortet…' : isTyping ? 'schreibt…'
              : isFallbackActive
                ? (provider === 'openrouter'
                    ? '⚠ OpenRouter offline · 🔒 Ollama Fallback'
                    : '⚠ Ollama offline · ☁️ OpenRouter Fallback')
                : provider === 'ollama'
                  ? ollamaStatus === 'online' ? '🔒 Lokal · Ollama' : '⚠ Ollama offline'
                  : apiKey ? 'Online' : '⚠ API-Key fehlt';
            const color = isStreaming || isTyping ? 'var(--text-tertiary)'
              : isFallbackActive ? '#d97706'
              : isActive ? (provider === 'ollama' ? '#2a9d5c' : 'var(--accent)') : 'var(--danger)';
            return <div style={{ fontSize: 12, color }}>{label}</div>;
          })()}
        </div>
        <button onClick={() => setDark(d => !d)} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-secondary)', padding: 4, display: 'flex',
        }}>
          {dark ? Icons.sun : Icons.moon}
        </button>
      </header>

      {!onboardingDone && onboardingStep > 0 && (
        <OnboardingProgress step={onboardingCurrent} total={onboardingTotal} />
      )}

      {showApiKeyModal && (
        <ApiKeyModal
          onSave={(key) => { setApiKey(key); setApiKeyModalDismissed(false); }}
          onDismiss={() => setApiKeyModalDismissed(true)}
        />
      )}

      {dsgvoCheck && (
        <DsgvoWarningModal
          findings={dsgvoCheck.findings}
          onAnonymize={() => {
            const safe = anonymizeText(dsgvoCheck.text);
            setDsgvoCheck(null);
            handleSend(safe, true);
          }}
          onProceed={() => {
            const txt = dsgvoCheck.text;
            setDsgvoCheck(null);
            handleSend(txt, true);
          }}
          onCancel={() => {
            setInputValue(dsgvoCheck.text);
            setDsgvoCheck(null);
          }}
        />
      )}

      {currentView === 'chat' ? (
        <>
          <div ref={chatContainerRef} style={{
            flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
            display: 'flex', flexDirection: 'column', gap: 14,
          }}>
            {activeChat.messages.map((msg, i) => (
              <ChatBubble key={i} message={msg.text} isBot={msg.role === 'bot'} />
            ))}
            {isStreaming && (
              <ChatBubble message={streamingText} isBot isTyping={!streamingText} />
            )}
            {isTyping && !isStreaming && <ChatBubble isBot isTyping />}
            {showQuickReplies && (
              <QuickReplies options={currentOnboardingStep.quickReplies} onSelect={handleQuickReply} />
            )}
            <div></div>
          </div>

          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={() => handleSend()}
            placeholder={currentOnboardingStep?.placeholder || 'Nachricht eingeben…'}
            disabled={isBusy}
            onFileUpload={onboardingDone ? handleFileUpload : null}
            toolOnline={toolStatus === 'online'}
            showDsgvoHint={onboardingDone && effectiveProvider === 'openrouter'}
            showLocalHint={onboardingDone && effectiveProvider === 'ollama'}
          />
        </>
      ) : currentView === 'profile' ? (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <ProfileView profile={profile} onUpdate={setProfile} />
        </div>
      ) : currentView === 'raster' ? (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <RasterEditorView toolStatus={toolStatus} />
        </div>
      ) : (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <SettingsView
            dark={dark} onToggleDark={() => setDark(d => !d)}
            apiKey={apiKey} onApiKeyChange={setApiKey}
            model={model} onModelChange={setModel}
            onResetOnboarding={handleResetOnboarding}
            toolStatus={toolStatus}
            ragDocCount={ragDocCount}
            onFileUpload={handleFileUpload}
            onClearKnowledge={handleClearKnowledge}
            onUrlDownload={handleUrlDownload}
            profile={profile}
            provider={provider} onProviderChange={setProvider}
            ollamaModel={ollamaModel} onOllamaModelChange={setOllamaModel}
            ollamaStatus={ollamaStatus} ollamaModels={ollamaModels}
            openrouterStatus={openrouterStatus}
            isFallbackActive={isFallbackActive} effectiveProvider={effectiveProvider}
          />
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
