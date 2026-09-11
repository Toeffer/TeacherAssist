(function () {
  'use strict';

  const rawFetch = window.fetch.bind(window);
  let bootstrapPromise = null;
  let csrfToken = '';
  let bootstrapData = null;

  const aliases = new Map([
    ['/health', '/api/v1/health'],
    ['/settings', '/api/v1/settings'],
    ['/collections', '/api/v1/collections'],
    ['/backup', '/api/v1/backup'],
    ['/list-raster', '/api/v1/rasters'],
    ['/memory-list', '/api/v1/memory-list'],
    ['/memory-read', '/api/v1/memory-read'],
    ['/memory-versions', '/api/v1/memory-versions'],
    ['/search', '/api/v1/search'],
    ['/chat', '/api/v1/chat'],
    ['/upload', '/api/v1/upload'],
    ['/ingest', '/api/v1/ingest'],
    ['/clear', '/api/v1/clear'],
    ['/download-url', '/api/v1/download-url'],
    ['/export-file', '/api/v1/export-file'],
    ['/save-raster', '/api/v1/save-raster'],
    ['/restore', '/api/v1/restore'],
    ['/memory-write', '/api/v1/memory-write'],
    ['/memory-restore-version', '/api/v1/memory-restore-version'],
    ['/ollama-pull', '/api/v1/ollama-pull'],
    ['/shutdown', '/api/v1/shutdown'],
    ['/ocr-image', '/api/v1/ocr-image'],
    ['/session-summary', '/api/v1/session-summary'],
  ]);

  function normalize(input) {
    if (typeof input !== 'string') return input;
    let url = input;
    try {
      const parsed = new URL(input, window.location.origin);
      if (parsed.hostname === 'localhost' && parsed.port === '8789') {
        url = parsed.pathname + parsed.search;
      }
    } catch {}
    const queryAt = url.indexOf('?');
    const path = queryAt >= 0 ? url.slice(0, queryAt) : url;
    const query = queryAt >= 0 ? url.slice(queryAt) : '';
    return (aliases.get(path) || path) + query;
  }

  async function bootstrap(force = false) {
    if (force) bootstrapPromise = null;
    if (!bootstrapPromise) {
      bootstrapPromise = rawFetch('/api/v1/bootstrap', {
        credentials: 'same-origin',
        cache: 'no-store',
      }).then(async response => {
        if (!response.ok) throw new Error('TeacherAssist-Sitzung konnte nicht gestartet werden.');
        bootstrapData = await response.json();
        csrfToken = bootstrapData.csrfToken || '';
        window.dispatchEvent(new CustomEvent('teacherassist:bootstrap', { detail: bootstrapData }));
        await migrateLegacySecrets();
        return bootstrapData;
      }).catch(error => {
        bootstrapPromise = null;
        throw error;
      });
    }
    return bootstrapPromise;
  }

  async function migrateLegacySecrets() {
    const legacyApiKey = localStorage.getItem('ta_api_key') || '';
    const legacyCustomKey = localStorage.getItem('ta_custom_apikey') || '';
    if (!legacyApiKey && !legacyCustomKey) return;
    const patch = {};
    if (legacyApiKey) patch.apiKey = legacyApiKey;
    if (legacyCustomKey) patch.customApiKey = legacyCustomKey;
    const response = await rawFetch('/api/v1/settings', {
      method: 'PATCH',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(patch),
    });
    if (!response.ok) return;
    const result = await response.json();
    const settings = result.settings || {};
    if (!legacyApiKey || settings.hasApiKey) localStorage.removeItem('ta_api_key');
    if (!legacyCustomKey || settings.hasCustomApiKey) localStorage.removeItem('ta_custom_apikey');
    bootstrapData.settings = settings;
    window.dispatchEvent(new CustomEvent('teacherassist:credentials', { detail: settings }));
  }

  async function apiFetch(input, options = {}) {
    const normalized = normalize(input);
    if (typeof normalized !== 'string' || !normalized.startsWith('/api/v1/')) {
      return rawFetch(input, options);
    }
    if (normalized === '/api/v1/health' || normalized === '/api/v1/bootstrap') {
      return rawFetch(normalized, { ...options, credentials: 'same-origin' });
    }
    await bootstrap();
    const request = () => {
      const headers = new Headers(options.headers || {});
      headers.set('X-CSRF-Token', csrfToken);
      return rawFetch(normalized, {
        ...options,
        headers,
        credentials: 'same-origin',
        cache: options.cache || 'no-store',
      });
    };
    let response = await request();
    // A second tab can outlive a purged session.  Refresh once only when the
    // server explicitly identifies authentication as the failure; streams
    // that have already started are never retried.
    const retryableBody = !(typeof ReadableStream !== 'undefined' && options.body instanceof ReadableStream);
    if (response.status === 403 && retryableBody) {
      let code = '';
      try { code = (await response.clone().json())?.error?.code || ''; } catch {}
      if (code === 'AUTH_REQUIRED') {
        await bootstrap(true);
        response = await request();
      }
    }
    return response;
  }

  window.taApi = {
    bootstrap,
    fetch: apiFetch,
    getBootstrap: () => bootstrapData,
    errorMessage: payload => payload?.error?.message || payload?.error || 'Unbekannter Fehler',
  };
  window.taFetch = apiFetch;
})();
