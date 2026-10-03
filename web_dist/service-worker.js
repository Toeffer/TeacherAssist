// Generated production service worker. API traffic is always network-only.
const CACHE = 'teacherassist-4452885b199c';
const PRE_CACHE = ["/","/assets/app-CG3MVZe_.js","/assets/components-Cdh7hYuU.js","/assets/index-eSN_3Bbz.js","/assets/manifest-C3jgv1Ik.json","/assets/ocr-ui-B_0jzriF.js","/assets/teacherassist-BuGrGrqB.ico","/assets/tweaks-panel-BrblVsvK.js","/index.html"];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRE_CACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))));
  self.clients.claim();
});

function fetchAndStore(request) {
  return fetch(request).then(response => {
    if (response.ok) {
      // Clone synchronously: once the page starts reading the body,
      // clone() throws.
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put(request, copy));
    }
    return response;
  });
}

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/assets/')) {
    // Vite content-hashes every asset name, so a cached URL is never stale.
    event.respondWith(caches.match(event.request).then(cached => cached || fetchAndStore(event.request)));
    return;
  }
  // Pages and unhashed files: network first, so an update is visible on the
  // next load. The cache only answers while the local server is stopped.
  event.respondWith(fetchAndStore(event.request).catch(() =>
    caches.match(event.request).then(cached => cached || Response.error())));
});
