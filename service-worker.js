// LehrerAgent Service Worker – Offline-Cache & Installationsfähigkeit
const CACHE = 'lehreragent-v1';

// Assets, die beim Install vortäuschlich gecached werden
const PRE_CACHE = [
  '/',
  '/index.html',
  '/app.jsx',
  '/components.jsx',
  '/tweaks-panel.jsx',
  '/manifest.json',
];

// Install-Event: Pre-Cache statischer Assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => {
      return Promise.allSettled(
        PRE_CACHE.map((url) =>
          cache.add(url).catch(() => {
            // Ignoriere Fehler bei einzelnen Dateien (z.B. wenn Babel-CDN offline)
          })
        )
      );
    })
  );
  // Sofort aktivieren (kein Warten auf alte SW)
  self.skipWaiting();
});

// Activate-Event: Alte Caches löschen
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch-Event: Cache-First für statische Assets, Network-First für API
self.addEventListener('fetch', (event) => {
  const { url } = event.request;

  // Keine API-Calls cachen (Tool-Server, OpenRouter, Ollama)
  if (url.includes(':8789') || url.includes('openrouter.ai') || url.includes('ollama')) {
    return; // Lass den Browser normal fetchen
  }

  // Keine externen CDN-Scripts cachen (die kommen von unpkg)
  if (url.includes('unpkg.com') || url.includes('fonts.googleapis.com') || url.includes('fonts.gstatic.com')) {
    return;
  }

  // Statische Assets: Cache-First
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});