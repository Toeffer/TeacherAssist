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
    bot: 'Wie darf ich dich nennen? Und wie soll ich heißen?\n\nSchreib z.B. "Ich bin Sabine, du bist Mila"\n– oder einfach nur deinen Namen.',
    field: 'name',
    placeholder: 'Dein Name oder "Ich bin …, du bist …"',
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
    optional: true,
  },
  {
    id: 'methoden',
    bot: 'Hast du Lieblingsmethoden oder Methoden, die du grundsätzlich vermeidest?\n(z.B. "Ich mache gerne Stationenarbeit" oder "kein reiner Frontalunterricht")\n\n(Optional – einfach überspringen)',
    field: 'methoden',
    placeholder: 'Optional – Enter zum Überspringen',
    phase: 2,
    optional: true,
  },
  {
    id: 'ollama_setup',
    bot: '🔒 **Datenschutz & lokale KI (Ollama)**\n\nFür Schülerarbeiten und personenbezogene Daten ist es wichtig, dass die Verarbeitung lokal auf deinem Rechner stattfindet.\n\nOllama ist ein kostenloses Tool, das KI-Modelle lokal ausführt – nichts verlässt deinen Computer.',
    field: 'ollama_choice',
    phase: 2,
    quickReplies: ['Ollama installieren', 'Ich hab Ollama bereits', 'Später einrichten'],
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

/* ---------- Zeitbasierte Begrüßung ---------- */
function getTimeBasedGreeting(teacherName, asstName) {
  const now = new Date();
  const hour = now.getHours();
  const day = now.getDay(); // 0=So, 1=Mo, ..., 5=Fr, 6=Sa
  const month = now.getMonth(); // 0=Jan, ..., 5=Jun, 6=Jul, 11=Dez
  const asst = asstName || 'Mila';
  const prefix = teacherName ? `${teacherName}, ` : '';

  let greeting = '';
  if (hour < 10) greeting = 'Guten Morgen';
  else if (hour < 14) greeting = 'Guten Tag';
  else if (hour < 18) greeting = 'Guten Nachmittag';
  else greeting = 'Guten Abend';

  let moodLine = '';

  // Wochentag
  if (day === 5) moodLine = 'Endlich Freitag!';
  else if (day === 1) moodLine = 'Auf in eine neue Woche!';

  // Ferien / besondere Zeiten
  if (month === 6 || month === 7) moodLine = moodLine || 'Nicht mehr lang bis zu den Sommerferien – du schaffst das!';
  else if (month === 11) moodLine = moodLine || 'Noch ein paar Wochen bis Weihnachten – durchhalten!';
  else if (month === 0) moodLine = moodLine || 'Frohes neues Jahr! Ich hoffe, du hattest schöne Ferien.';

  let msg = `${greeting}, ${prefix}ich bin ${asst} 👋\n\nSchön, dass du da bist.`;
  if (moodLine) msg += `\n\n${moodLine}`;
  msg += `\n\nLass uns dein Profil kurz einrichten – dann kann ich dir im Schulalltag richtig helfen.`;
  return msg;
}

/* ---------- Name-Parsing für "Ich bin X, du bist Y" ---------- */
function parseNameInput(raw) {
  if (!raw || !raw.trim()) return { name: '', assistant_name: '' };
  const text = raw.trim();

  // Muster: "Ich bin X, du bist Y"
  const m = text.match(/ich\s*(?:bin|heiße)\s+([a-zA-ZäöüÄÖÜß\-\s]+?)(?:\s*,?\s*(?:und\s+)?du\s*(?:bist|heißt)\s+([a-zA-ZäöüÄÖÜß\-]+))?\s*$/i);
  if (m) {
    return {
      name: m[1].trim(),
      assistant_name: m[2] ? m[2].trim() : '',
    };
  }

  // Muster: "X, und du bist Y" oder "X – du Y"
  const m2 = text.match(/^([a-zA-ZäöüÄÖÜß\-\s]+?)\s*[,–\-—]+\s*du\s*(?:bist|heißt)?\s*([a-zA-ZäöüÄÖÜß\-]+)\s*$/i);
  if (m2) {
    return {
      name: m2[1].trim(),
      assistant_name: m2[2].trim(),
    };
  }

  // Du-bist-Muster muss vor der "Nur ein Name"-Prüfung stehen
  const m3 = text.match(/^([a-zA-ZäöüÄÖÜß\-\s]+?)\s*,?\s*du\s*(?:bist|heißt)\s+([a-zA-ZäöüÄÖÜß\-]+)\s*$/i);
  if (m3) {
    return { name: m3[1].trim(), assistant_name: m3[2].trim() };
  }

  // Nur ein Name → nur Lehrkraft-Name, assistant_name bleibt bestehen
  if (text.length <= 40 && !/[\s]{3,}/.test(text) && !text.includes('?') && !/\bdu\s+(bist|heißt)\b/i.test(text)) {
    return { name: text, assistant_name: '' };
  }

  return { name: text, assistant_name: '' };
}

/* ---------- Onboarding: Frage-Erkennung & FAQ ---------- */
function isOnboardingQuestion(text) {
  if (text.includes('?')) return true;
  const lower = text.trim().toLowerCase();
  const starters = [
    'was ', 'wie ', 'wann ', 'warum ', 'wieso ', 'weshalb ', 'wer ', 'wo ', 'welche',
    'wofür ', 'wozu ', 'inwiefern ', 'in welch', 'an welch', 'auf welch', 'mit welch',
    'kann ', 'kannst ', 'könnte ', 'könnt ', 'darf ', 'gibt ', 'haben ', 'hast ',
    'muss ', 'musst ', 'sollte ', 'soll ',
    'meinst du', 'wie meinst', 'was meinst',
  ];
  if (starters.some(s => lower.startsWith(s))) return true;
  const markers = [
    'verstehe nicht', 'verstehe ich nicht', 'kapiere nicht',
    'weiß nicht', 'weiss nicht', 'keine ahnung',
    'hilfe', 'erklär',
  ];
  return markers.some(m => lower.includes(m));
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

// Findet alle Klassenstufen-Zahlen in einem Free-Form-Text wie
// "Mathe 7a, 8b – Deutsch 5a, 7a". Liefert Number[].
function extractKlassenStufen(text) {
  if (!text) return [];
  const out = [];
  const re = /\b(\d{1,2})\s*[a-zäöüß]?\b/gi;
  let m;
  while ((m = re.exec(text)) !== null) {
    const n = parseInt(m[1], 10);
    if (!Number.isNaN(n)) out.push(n);
  }
  return out;
}

/* ---------- LLM-Chat via Tool-Server (Proxy mit DSGVO-Filter + Skill-Router) ---------- */
async function callChatViaServer(messages, profile, onChunk, onMeta, customEndpoint = '', customApiKey = '', customModel = 'gpt-3.5-turbo', apiKey = '', providerOverride = '', modelOverride = '', ollamaModelOverride = '') {
  const response = await fetch('http://localhost:8789/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      profile,
      customEndpoint,
      customApiKey,
      customModel,
      apiKey,
      providerOverride,
      modelOverride,
      ollamaModelOverride,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || `Server-Fehler ${response.status}`);
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
      try {
        const parsed = JSON.parse(data);
        switch (parsed.type) {
          case 'chunk': onChunk(parsed.text); break;
          case 'usage': if (onMeta) onMeta('usage', parsed.usage); break;
          case 'dsgvo_warning': if (onMeta) onMeta('dsgvo', parsed); break;
          case 'skill': if (onMeta) onMeta('skill', parsed); break;
          case 'provider': if (onMeta) onMeta('provider', parsed); break;
          case 'error': throw new Error(parsed.message);
          case 'done': return;
        }
      } catch (e) {
        if (e.message && !e.message.startsWith('Server-')) throw e;
      }
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
    try {
      const saved = JSON.parse(localStorage.getItem('ta_profile')) || {};
      return { assistant_name: 'Mila', ...saved };
    } catch { return { assistant_name: 'Mila' }; }
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
  const [provider, setProvider] = useState(() => localStorage.getItem('ta_provider') || 'openrouter');
  const [ollamaModel, setOllamaModel] = useState(() => localStorage.getItem('ta_ollama_model') || 'gemma4:e4b');
  const [ollamaStatus, setOllamaStatus] = useState('unknown');
  const [ollamaModels, setOllamaModels] = useState([]);
  const [openrouterStatus, setOpenrouterStatus] = useState('unknown');
  const [sessionTokens, setSessionTokens] = useState(0);
  const [customEndpoint, setCustomEndpoint] = useState(() => localStorage.getItem('ta_custom_endpoint') || '');
  const [customApiKey, setCustomApiKey] = useState(() => localStorage.getItem('ta_custom_apikey') || '');
  const [customModel, setCustomModel] = useState(() => localStorage.getItem('ta_custom_model') || 'gpt-3.5-turbo');
  const [tailscaleStatus, setTailscaleStatus] = useState('unknown');
  const [showStylePopover, setShowStylePopover] = useState(false);
  const [dsgvoRoutingActive, setDsgvoRoutingActive] = useState(false);
  const [uploadPhase, setUploadPhase] = useState(null); // null | 'uploading' | 'indexing'
  const [batchQueue,  setBatchQueue]  = useState([]);   // [{file, status:'pending'|'active'|'done'|'error'}]
  const batchRunning = useRef(false);
  const chatContainerRef = useRef(null);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];

  const effectiveProvider = useMemo(() => {
    if (provider === 'openrouter' && openrouterStatus === 'offline' && ollamaStatus === 'online') return 'ollama';
    if (provider === 'ollama' && ollamaStatus === 'offline' && apiKey && openrouterStatus === 'online') return 'openrouter';
    return provider;
  }, [provider, openrouterStatus, ollamaStatus, apiKey]);
  const isFallbackActive = effectiveProvider !== provider;
  const isDsgvoRouting = dsgvoRoutingActive;

  useEffect(() => { localStorage.setItem('ta_dark', JSON.stringify(dark)); }, [dark]);
  useEffect(() => { localStorage.setItem('ta_profile', JSON.stringify(profile)); }, [profile]);
  useEffect(() => { localStorage.setItem('ta_chats', JSON.stringify(chats)); }, [chats]);
  useEffect(() => { localStorage.setItem('ta_onboarded', JSON.stringify(onboardingDone)); }, [onboardingDone]);
  useEffect(() => { localStorage.setItem('ta_api_key', apiKey); }, [apiKey]);
  useEffect(() => { localStorage.setItem('ta_model', model); }, [model]);
  useEffect(() => { localStorage.setItem('ta_provider', provider); }, [provider]);
  useEffect(() => { localStorage.setItem('ta_ollama_model', ollamaModel); }, [ollamaModel]);
  useEffect(() => { localStorage.setItem('ta_custom_endpoint', customEndpoint); }, [customEndpoint]);
  useEffect(() => { localStorage.setItem('ta_custom_apikey', customApiKey); }, [customApiKey]);
  useEffect(() => { localStorage.setItem('ta_custom_model', customModel); }, [customModel]);

  // Provider-Wahl, API-Key und Custom-Felder an Tool-Server senden
  useEffect(() => {
    if (toolStatus !== 'online') return;
    fetch('http://localhost:8789/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, ollamaModel, model, apiKey, customEndpoint, customApiKey, customModel }),
    }).catch(() => {});
  }, [toolStatus, provider, ollamaModel, model, apiKey, customEndpoint, customApiKey, customModel]);

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
      const greeting = getTimeBasedGreeting(profile.name, profile.assistant_name);
      addBotMessage(greeting, 400);
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

    // Leer-Enter im Onboarding: optionale Schritte überspringen
    if (!text && !isStreaming && !isTyping && !onboardingDone) {
      const step = ONBOARDING_STEPS[onboardingStep];
      if (step?.optional && step.field) {
        setInputValue('');
        setProfile(p => ({ ...p, [step.field]: '' }));
        const nextIdx = onboardingStep + 1;
        const nextStep = ONBOARDING_STEPS[nextIdx];
        if (nextStep) {
          setOnboardingStep(nextIdx);
          addBotMessage(nextStep.bot, 600);
          if (nextStep.id === 'done') setTimeout(() => setOnboardingDone(true), 1200);
        }
        return;
      }
    }

    if (!text || isStreaming || isTyping) return;
    setInputValue('');

    // DSGVO-Prüfung jetzt serverseitig (Tool-Server filtert automatisch)

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
            await callChatViaServer(
              [{ role: 'user', text }], {},
              chunk => { answer += chunk; },
              undefined,
              customEndpoint, customApiKey, customModel, apiKey,
              effectiveProvider, model, ollamaModel
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
      if (step?.field && step.field !== 'lehrplan_choice' && step.field !== 'ollama_choice') {
        const raw = text === 'nein' || text === '-' ? '' : text;
        if (step.field === 'faecher') {
          const ungueltige = [...new Set(extractKlassenStufen(raw).filter(n => n < 1 || n > 13))];
          if (ungueltige.length) {
            addBotMessage(
              `Hmm, du hast Klasse ${ungueltige.join(', ')} genannt – in deutschen Schulen gibt es nur die Stufen 1 bis 13. ` +
              `Magst du das nochmal eingeben? (Beispiel: "Mathe 7a, 8b – Deutsch 5a, 7a")`,
              600
            );
            return;
          }
          const items = raw.split(/[,\n]+/).map(s => normalizeFachname(s.trim())).filter(Boolean);
          setProfile(p => ({ ...p, faecher: items }));
        } else if (step.field === 'bundesland') {
          setProfile(p => ({ ...p, bundesland: normalizeBundesland(raw) }));
        } else if (step.field === 'schulform') {
          setProfile(p => ({ ...p, schulform: normalizeSchulform(raw) }));
        } else if (step.field === 'name') {
          const parsed = parseNameInput(raw);
          setProfile(p => ({
            ...p,
            name: parsed.name || raw,
            assistant_name: parsed.assistant_name || p.assistant_name || 'Mila',
          }));
        } else {
          setProfile(p => ({ ...p, [step.field]: raw }));
        }
      }

      // Ollama-Setup: Installationsanleitung oder Modell-Empfehlung
      if (step?.id === 'ollama_setup') {
        const choice = text.toLowerCase();
        if (choice.includes('installieren') || choice.includes('ollama installieren')) {
          addBotMessage(`Super! So installierst du Ollama:\n\n1. Gehe auf **ollama.com/download** und lade die Windows-Version herunter\n2. Installiere wie gewohnt – kein Admin-Passwort nötig\n3. Starte danach TeacherAssist neu\n\nIch erkenne Ollama beim nächsten Start automatisch und empfehle dir passende Modelle.\n\n**Warum Ollama?** 🔒\n• Alle Daten bleiben auf deinem Rechner\n• Keine Internetverbindung nötig für lokale Anfragen\n• Perfekt für Schülerarbeiten & personenbezogene Daten\n• DSGVO-konform\n\n📸 Für Handschrifterkennung empfehle ich zusätzlich ein VLM wie **qwen3-vl** – damit kann ich Fotos von Schülerarbeiten direkt lesen.`, 1000);
          setTimeout(() => {
            setOnboardingStep(onboardingStep + 1);
            addBotMessage(ONBOARDING_STEPS[onboardingStep + 1]?.bot || '', 600);
          }, 2000);
          return;
        } else if (choice.includes('bereits') || choice.includes('hab ollama')) {
          addBotMessage('Perfekt! Dann kann ich deine sensiblen Daten gleich lokal verarbeiten.\n\nIch empfehle diese Modelle für TeacherAssist:\n\n• **Basis (≈4 GB):** gemma4:e4b, llama3.2 – schnell, ideal für Planung & Korrektur\n• **Allround (≈6–7 GB):** qwen3:8b – starke deutsche Sprache, ausgewogen\n• **Qualität (≈9 GB):** phi4 – höchste Genauigkeit, etwas langsamer\n• **📸 Handschrift / Bilder:** qwen3-vl – liest Schüler-Handschrift\n\nDu kannst jederzeit mit `/pull <modell>` ein Modell herunterladen.', 1200);
        }
        // Always advance
        setTimeout(() => {
          setOnboardingStep(onboardingStep + 1);
          addBotMessage(ONBOARDING_STEPS[onboardingStep + 1]?.bot || '', 600);
        }, choice.includes('später') ? 400 : 2000);
        return;
      }

      // Lehrplan-Entscheidung: Wenn "angeben", auf Upload warten
      if (step?.id === 'lehrplan') {
        const lower = text.toLowerCase();
        if (lower.includes('angeben') || lower.includes('hochladen') || lower.includes('pdf')) {
          addBotMessage('📄 Super! Schick mir jetzt einfach das PDF über den 📎-Button im Eingabefeld.\n\nIch lese es automatisch ein und speichere es in der Wissensdatenbank. Wenn der Upload fertig ist, sag einfach "weiter" oder klicke eine Quick-Reply.', 400);
          return;
        }
        if (lower.includes('später') || lower.includes('nein') || lower.includes('nicht')) {
          const nextIdx = onboardingStep + 1;
          if (nextIdx < ONBOARDING_STEPS.length) {
            setOnboardingStep(nextIdx);
            const nextStep = ONBOARDING_STEPS[nextIdx];
            addBotMessage(nextStep.bot, 800);
            if (nextStep.id === 'done') {
              setTimeout(() => setOnboardingDone(true), 1200);
            }
          }
          return;
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

    // Slash-Befehle
    const pullMatch = text.match(/^\/pull\s+(.+)$/i);
    if (pullMatch) {
      const model = pullMatch[1].trim();
      addMessage(activeChatId, { role: 'bot', text: `⏳ Lade **${model}** über Ollama herunter… Das kann einige Minuten dauern.`, ts: Date.now() });
      try {
        const res = await fetch('http://localhost:8789/ollama-pull', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model }),
        });
        if (!res.ok) throw new Error(await res.text());
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let lastPct = -1;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === 'progress' && evt.percent !== lastPct) {
                lastPct = evt.percent;
                // Update last bot message in chat
                setChats(prev => prev.map(c => {
                  if (c.id !== activeChatId) return c;
                  const msgs = [...c.messages];
                  if (msgs.length > 0 && msgs[msgs.length - 1]?.role === 'bot') {
                    msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], text: `⏳ Lade **${model}**… ${lastPct}%\n\n${'█'.repeat(Math.floor(lastPct / 5))}${'░'.repeat(20 - Math.floor(lastPct / 5))}` };
                  }
                  return { ...c, messages: msgs };
                }));
              }
              if (evt.type === 'done' && evt.success) {
                addMessage(activeChatId, { role: 'bot', text: `✅ **${model}** wurde erfolgreich installiert!\n\nDu kannst jetzt unter Einstellungen zu Ollama wechseln und das Modell auswählen.`, ts: Date.now() });
                return;
              }
              if (evt.type === 'error') {
                addMessage(activeChatId, { role: 'bot', text: `⚠️ Fehler beim Download: ${evt.message}`, ts: Date.now() });
                return;
              }
            } catch {}
          }
        }
      } catch (err) {
        addMessage(activeChatId, { role: 'bot', text: `⚠️ Fehler: ${err.message}\n\nIst Ollama installiert? Versuche: ollama pull ${model}`, ts: Date.now() });
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

    let fullText = '';
    try {
      await callChatViaServer(currentMessages, profile, (chunk) => {
        fullText += chunk;
        setStreamingText(fullText);
      }, (type, data) => {
        if (type === 'usage') setSessionTokens(n => n + (data.total_tokens || 0));
        else if (type === 'dsgvo') {
          if (data.routing === 'dsgvo_local') {
            setDsgvoRoutingActive(true);
          }
          if (data.message) {
            addMessage(activeChatId, { role: 'bot', text: `🔒 ${data.message}`, ts: Date.now() });
          }
        }
      }, customEndpoint, customApiKey, customModel, apiKey, effectiveProvider, model, ollamaModel);
    } catch (err) {
      fullText = `⚠️ Fehler bei der Anfrage: ${err.message}\n\nBitte prüfe deine Verbindung und die Einstellungen.`;
    }

    setIsStreaming(false);
    setStreamingText('');
    addMessage(activeChatId, { role: 'bot', text: fullText || '(Keine Antwort erhalten)', ts: Date.now() });
  }, [inputValue, activeChatId, chats, onboardingDone, onboardingStep, profile, apiKey, model, isStreaming, isTyping, toolStatus, ragDocCount, addMessage, addBotMessage, provider, ollamaModel, ollamaStatus, openrouterStatus, effectiveProvider, customEndpoint, customApiKey, customModel]);

  const handleFileUpload = useCallback(async (file, track) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      addMessage(activeChatId, { role: 'bot', text: '⚠️ Bitte nur PDF-Dateien hochladen.', ts: Date.now() });
      return;
    }
    const sourceName = track ? `${track} – ${file.name}` : file.name;
    addMessage(activeChatId, { role: 'user', text: `📄 ${sourceName}`, ts: Date.now() });
    setUploadPhase('uploading');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const upRes = await fetch('http://localhost:8789/upload', { method: 'POST', body: formData });
      if (!upRes.ok) throw new Error('Upload fehlgeschlagen');
      const { saved } = await upRes.json();
      if (!saved?.length) throw new Error('Keine Datei gespeichert');

      setUploadPhase('indexing');
      const inRes = await fetch('http://localhost:8789/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: saved[0], source: sourceName }),
      });
      const data = await inRes.json();
      if (!inRes.ok || data.error) throw new Error(data.error || 'Verarbeitung fehlgeschlagen');

      setUploadPhase(null);
      setRagDocCount(n => n + data.chunks);
      addMessage(activeChatId, {
        role: 'bot',
        text: `✅ **${sourceName}** wurde eingelesen!\n\n${data.chunks} Abschnitte · ca. ${(data.words || 0).toLocaleString('de-DE')} Wörter\n\nDu kannst jetzt Fragen zu diesem Lehrplan stellen – ich finde automatisch den passenden Kontext.`,
        ts: Date.now(),
      });
    } catch (err) {
      setUploadPhase(null);
      addMessage(activeChatId, {
        role: 'bot',
        text: `⚠️ PDF-Verarbeitung fehlgeschlagen: ${err.message}\n\nIst der Tool-Server gestartet? (start.bat neu starten)`,
        ts: Date.now(),
      });
    }
  }, [activeChatId, addMessage]);

  const handleFilesUpload = useCallback(async (files) => {
    if (!files || files.length === 0) return;
    const items = files.map(f => ({ file: f, status: 'pending' }));
    setBatchQueue(prev => [...prev, ...items]);

    if (batchRunning.current) return; // already draining
    batchRunning.current = true;

    // drain queue sequentially
    const drainFrom = (startIdx) => {
      setBatchQueue(prev => {
        const pending = prev.findIndex((it, idx) => idx >= startIdx && it.status === 'pending');
        if (pending === -1) { batchRunning.current = false; return prev; }

        const updated = prev.map((it, idx) => idx === pending ? { ...it, status: 'active' } : it);

        // process this file async, then recurse
        const item = updated[pending];
        (async () => {
          try {
            const sourceName = item.file.name;
            const formData = new FormData();
            formData.append('file', item.file);
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

            setRagDocCount(n => n + (data.chunks || 0));
            setBatchQueue(prev => prev.map((it, idx) => idx === pending ? { ...it, status: 'done' } : it));
          } catch (err) {
            setBatchQueue(prev => prev.map((it, idx) => idx === pending ? { ...it, status: 'error', err: err.message } : it));
          }
          drainFrom(pending + 1);
        })();

        return updated;
      });
    };

    drainFrom(0);
  }, []);

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

  const handleExport = useCallback(async (text, format = 'pdf') => {
    const title = activeChat?.title && activeChat.title !== 'Neuer Chat' ? activeChat.title : 'TeacherAssist Export';
    if (format === 'pdf') {
      openPrintWindow(text, title);
      return;
    }

    try {
      const res = await fetch('/export-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content: text, format }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.error) throw new Error(data.error || 'Export fehlgeschlagen');

      const a = document.createElement('a');
      a.href = data.url;
      a.download = data.filename;
      a.click();

      addMessage(activeChatId, {
        role: 'bot',
        text: `✅ Export erstellt: **${data.filename}**\n\n[Datei herunterladen](${data.url})`,
        ts: Date.now(),
      });
    } catch (err) {
      addMessage(activeChatId, {
        role: 'bot',
        text: `⚠️ Export fehlgeschlagen: ${err.message}\n\nIst der Tool-Server gestartet?`,
        ts: Date.now(),
      });
    }
  }, [activeChat?.title, activeChatId, addMessage]);

  const handleBackup = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8789/backup');
      if (!res.ok) throw new Error('Backup fehlgeschlagen');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `teacherAssist_backup_${new Date().toISOString().slice(0, 10)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Backup fehlgeschlagen: ${err.message}\n\nIst der Tool-Server gestartet?`);
    }
  }, []);

  const handleRestore = useCallback(async (file) => {
    if (!file) return;
    if (!window.confirm(
      `Memory-Dateien aus "${file.name}" wiederherstellen?\n\n` +
      'Bestehende Dateien werden überschrieben. Danach bitte die Seite neu laden.'
    )) return;
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('http://localhost:8789/restore', { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || 'Restore fehlgeschlagen');
      alert(`✅ ${data.restored} Datei(en) wiederhergestellt.\n\nBitte lade die Seite neu (F5), damit alle Änderungen aktiv werden.`);
    } catch (err) {
      alert(`Restore fehlgeschlagen: ${err.message}`);
    }
  }, []);

  const handleNavigate = useCallback((view) => {
    setCurrentView(view);
    setSidebarOpen(false);
  }, []);

  const handleSessionSummary = useCallback(async () => {
    const msgs = chats.find(c => c.id === activeChatId)?.messages || [];
    if (msgs.filter(m => m.role === 'user').length < 2) {
      addMessage(activeChatId, { role: 'bot', text: 'Es gibt noch nicht genug Nachrichten zum Zusammenfassen. Stelle erst ein paar Fragen.', ts: Date.now() });
      return;
    }
    addMessage(activeChatId, { role: 'user', text: '📝 Sitzung zusammenfassen und speichern', ts: Date.now() });
    setIsTyping(true);
    try {
      const res = await fetch('http://localhost:8789/session-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: msgs,
          profile,
          apiKey,
          providerOverride: effectiveProvider,
          modelOverride: model,
          ollamaModelOverride: ollamaModel,
          customEndpoint,
          customApiKey,
          customModel,
        }),
      });
      const data = await res.json();
      setIsTyping(false);
      if (data.error) throw new Error(data.error);
      addMessage(activeChatId, {
        role: 'bot',
        text: `✅ Sitzung gespeichert!\n\n📝 **Zusammenfassung:**\n${data.summary}\n\n*(Im Memory-Editor unter "vergangene_stunden.md" einsehbar)*`,
        ts: Date.now(),
      });
    } catch (err) {
      setIsTyping(false);
      addMessage(activeChatId, { role: 'bot', text: `⚠️ Fehler beim Zusammenfassen: ${err.message}`, ts: Date.now() });
    }
  }, [activeChatId, chats, profile, apiKey, effectiveProvider, model, ollamaModel, customEndpoint, customApiKey, customModel, addMessage]);

  const handleTestModel = useCallback(async () => {
    let text = '';
    let usedProvider = provider;
    await callChatViaServer(
      [{ role: 'user', text: 'Antworte auf Deutsch mit genau einem kurzen Satz: Modelltest erfolgreich.' }],
      profile,
      (chunk) => { text += chunk; },
      (type, data) => {
        if (type === 'provider' && data?.provider) usedProvider = data.provider;
      },
      customEndpoint,
      customApiKey,
      customModel,
      apiKey,
      provider,
      model,
      ollamaModel
    );

    return {
      text: text.trim() || '(Keine Antwort erhalten)',
      provider: usedProvider,
      model: provider === 'ollama' ? ollamaModel : provider === 'custom' ? customModel : model,
    };
  }, [apiKey, customApiKey, customEndpoint, customModel, model, ollamaModel, profile, provider]);

  // Tastaturkürzel
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key === 'n') { e.preventDefault(); handleNewChat(); }
      if (e.ctrlKey && e.key === 'b') { e.preventDefault(); setSidebarOpen(s => !s); }
      if (e.ctrlKey && e.key === ',') { e.preventDefault(); setCurrentView(v => v === 'settings' ? 'chat' : 'settings'); }
      if (e.ctrlKey && e.key === 's') { e.preventDefault(); handleSessionSummary(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleNewChat, handleSessionSummary]);

  const handleShutdown = useCallback(() => {
    return fetch('http://localhost:8789/shutdown', { method: 'POST' }).catch(() => {});
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
        assistantName={profile.assistant_name || 'Mila'}
        onShutdown={handleShutdown}
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
        <div
          title="Klicken zum Anpassen des Antwortstils"
          style={{ position: 'relative', cursor: 'pointer' }}
          onClick={() => setShowStylePopover(!showStylePopover)}
          onMouseEnter={e => { e.currentTarget.querySelector('.avatar-badge')?.style.setProperty('opacity', '1'); }}
          onMouseLeave={e => { e.currentTarget.querySelector('.avatar-badge')?.style.setProperty('opacity', '0'); }}
        >
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <BotAvatar size={30} name={profile.assistant_name || 'Mila'} />
            <span className="avatar-badge" style={{
              position: 'absolute', bottom: -2, right: -2,
              width: 14, height: 14, borderRadius: '50%',
              background: 'var(--accent)', color: '#fff',
              fontSize: 9, display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '2px solid var(--surface)',
              opacity: 0, transition: 'opacity 0.2s',
            }}>⚙</span>
          </div>
          {showStylePopover && (
            <AssistantStylePopover
              profile={profile}
              onUpdate={setProfile}
              onClose={() => setShowStylePopover(false)}
            />
          )}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.2 }}>{profile.assistant_name || 'Mila'}</div>
          {(() => {
            const namePrefix = (profile.assistant_name || 'Mila');
            const isActive = isFallbackActive || (provider === 'ollama' ? ollamaStatus === 'online' : provider === 'custom' ? !!customEndpoint : !!apiKey);
            const label = isStreaming ? namePrefix + ' · antwortet…' : isTyping ? namePrefix + ' · schreibt…'
              : isDsgvoRouting
                ? '🔒 Lokales Modell (DSGVO)'
                : isFallbackActive
                  ? (provider === 'openrouter'
                      ? '⚠ OpenRouter offline · 🔒 Ollama Fallback'
                      : '⚠ Ollama offline · ☁️ OpenRouter Fallback')
                  : provider === 'ollama'
                    ? ollamaStatus === 'online' ? '🔒 Lokal · ' + namePrefix : '⚠ Ollama offline'
                    : provider === 'custom'
                      ? customEndpoint ? namePrefix + ' · Eigener Dienst' : '⚠ Custom-Endpoint fehlt'
                    : apiKey ? namePrefix + ' · Online' : '⚠ API-Key fehlt';
            const dsgvoColor = '#d97706';
            const color = isDsgvoRouting ? dsgvoColor
              : isStreaming || isTyping ? 'var(--text-tertiary)'
              : isFallbackActive ? '#d97706'
              : isActive ? (provider === 'ollama' ? '#2a9d5c' : provider === 'custom' ? '#7c3aed' : '#3b82f6') : 'var(--danger)';
            return <div style={{ fontSize: 12, color }}>{label}</div>;
          })()}
        </div>
        {sessionTokens > 0 && (
          <div title="Kosten dieser Sitzung" style={{
            fontSize: 11, color: 'var(--text-tertiary)',
            whiteSpace: 'nowrap', userSelect: 'none',
          }}>
            {(() => {
              const p = MODEL_PRICES[model];
              if (!p || !sessionTokens) return null;
              const cost = (p.in * 0.0003 + p.out * 0.0006) / 1.08;
              const eur = (sessionTokens / 900) * cost;
              if (eur < 0.0001) return '< 0,001 €';
              return '≈ ' + eur.toLocaleString('de-DE', { minimumFractionDigits: 3, maximumFractionDigits: 3 }) + ' €';
            })()}
          </div>
        )}
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

      {currentView === 'chat' ? (
        <>
          <div ref={chatContainerRef} style={{
            flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
            display: 'flex', flexDirection: 'column', gap: 14,
          }}>
            {activeChat.messages.map((msg, i) => (
              <ChatBubble key={i} message={msg.text} isBot={msg.role === 'bot'} onExport={msg.role === 'bot' ? handleExport : undefined} assistantName={profile.assistant_name || 'Mila'} />
            ))}
            {isStreaming && (
              <ChatBubble message={streamingText} isBot isTyping={!streamingText} assistantName={profile.assistant_name || 'Mila'} />
            )}
            {isTyping && !isStreaming && <ChatBubble isBot isTyping assistantName={profile.assistant_name || 'Mila'} />}
            {showQuickReplies && (
              <QuickReplies options={currentOnboardingStep.quickReplies} onSelect={handleQuickReply} />
            )}
            <div></div>
          </div>

          {uploadPhase && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 18px',
              background: 'var(--accent-soft)',
              borderTop: '1px solid var(--border)',
              fontSize: 13, color: 'var(--accent)', flexShrink: 0,
            }}>
              <div style={{
                width: 14, height: 14, flexShrink: 0,
                border: '2px solid var(--accent)', borderTopColor: 'transparent',
                borderRadius: '50%', animation: 'spin 0.7s linear infinite',
              }}></div>
              {uploadPhase === 'uploading'
                ? 'Schritt 1/2: PDF wird übertragen…'
                : 'Schritt 2/2: Wird eingelesen und indiziert… (kann etwas dauern)'}
            </div>
          )}
          <BatchQueuePanel
            queue={batchQueue}
            onDismiss={() => setBatchQueue([])}
          />
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={() => handleSend()}
            placeholder={currentOnboardingStep?.placeholder || 'Nachricht eingeben…'}
            disabled={isBusy || !!uploadPhase}
            onFileUpload={(onboardingDone || currentOnboardingStep?.id === 'lehrplan') ? handleFileUpload : null}
            onFilesUpload={(onboardingDone || currentOnboardingStep?.id === 'lehrplan') && toolStatus === 'online' ? handleFilesUpload : null}
            toolOnline={toolStatus === 'online'}
            showDsgvoHint={onboardingDone && effectiveProvider === 'openrouter'}
            showLocalHint={onboardingDone && effectiveProvider === 'ollama'}
            quickActions={onboardingDone && !isBusy && !uploadPhase ? [
              { label: '📋 Was war letzte Stunde?', onSelect: () => handleSend('Was war in meiner letzten geplanten Unterrichtsstunde? Bitte zeige mir eine kurze Zusammenfassung aus dem Verlaufsprotokoll (vergangene_stunden.md).') },
              { label: '⚡ Vorlagen', onSelect: () => handleNavigate('templates') },
            ] : []}
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
      ) : currentView === 'templates' ? (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <TemplateGalleryView onUseTemplate={(prompt) => { setInputValue(prompt); handleNavigate('chat'); }} />
        </div>
      ) : currentView === 'memory' ? (
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
          <MemoryEditorView toolStatus={toolStatus} />
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
            customEndpoint={customEndpoint} onCustomEndpointChange={setCustomEndpoint}
            customApiKey={customApiKey} onCustomApiKeyChange={setCustomApiKey}
            customModel={customModel} onCustomModelChange={setCustomModel}
            tailscaleStatus={tailscaleStatus}
            onBackup={handleBackup} onRestore={handleRestore}
            onTestModel={handleTestModel}
          />
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
