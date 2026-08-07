// Generated production service worker. API traffic is always network-only.
const CACHE = 'teacherassist-287e4cd43e94';
const PRE_CACHE = ["/","/assets/app-C7WUNHl0.js","/assets/components-CGlARzrP.js","/assets/index-B8GOZRCi.js","/assets/jsx-runtime-CdvZGgm7.js","/assets/manifest-DJFCjNqP.json","/assets/teacherassist-BuGrGrqB.ico","/assets/tweaks-panel-C5jvxMYF.js","/index.html"];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRE_CACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (event.request.method !== 'GET') return;
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (response.ok) caches.open(CACHE).then(cache => cache.put(event.request, response.clone()));
    return response;
  })));
});
