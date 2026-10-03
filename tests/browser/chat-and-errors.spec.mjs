import { readFile } from 'node:fs/promises';

import { expect, test } from '@playwright/test';

import { setUpApp } from './fixtures.mjs';

function sse(...events) {
  return events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('');
}

test('keeps a partially streamed answer when the stream reports an error', async ({ page }) => {
  await setUpApp(page);
  await page.route('**/api/v1/chat', route => route.fulfill({
    contentType: 'text/event-stream',
    body: sse(
      { type: 'privacy', mode: 'cloud_allowed', reasons: [] },
      { type: 'chunk', text: 'Erster Teil der Antwort.' },
      { type: 'error', code: 'PROVIDER_ERROR', message: 'OpenRouter ist gerade gestört (HTTP 503).' },
      { type: 'done' },
    ),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const input = page.getByPlaceholder('Nachricht eingeben…');
  await input.fill('Ideen für einen Einstieg');
  await input.press('Enter');

  // The answer used to be replaced by "Fehler bei der Anfrage" entirely.
  await expect(page.getByText(/Die Antwort wurde unterbrochen: OpenRouter ist gerade gestört/)).toBeVisible();
  await expect(page.getByText('Erster Teil der Antwort.')).toBeVisible();
  await expect(page.getByText(/Fehler bei der Anfrage/)).toHaveCount(0);
});

test('the settings model test sends the configured provider and models', async ({ page }) => {
  await setUpApp(page);
  const chatRequests = [];
  await page.route('**/api/v1/chat', route => {
    chatRequests.push(route.request().postDataJSON());
    return route.fulfill({
      contentType: 'text/event-stream',
      body: sse({ type: 'chunk', text: 'Modelltest erfolgreich.' }, { type: 'done' }),
    });
  });

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.keyboard.press('Control+,');
  await page.getByRole('button', { name: 'Test senden' }).click();

  await expect(page.getByText('Modelltest erfolgreich.')).toBeVisible();
  expect(chatRequests).toHaveLength(1);
  // A missing customApiKey argument used to shift every later argument by
  // one, so the test sent the Ollama model name as the OpenRouter model.
  expect(chatRequests[0]).toMatchObject({
    providerOverride: 'openrouter',
    modelOverride: 'deepseek/deepseek-chat',
    ollamaModelOverride: 'gemma3:4b',
    customModel: 'gpt-3.5-turbo',
    customEndpoint: '',
  });
});

test('shows the message of a structured server error instead of [object Object]', async ({ page }) => {
  await setUpApp(page);
  await page.route('**/api/v1/download-url', route => route.fulfill({
    status: 400,
    contentType: 'application/json',
    body: JSON.stringify({ error: { code: 'DOWNLOAD_BLOCKED', message: 'Nur HTTPS-Adressen sind erlaubt.' } }),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.keyboard.press('Control+,');
  await page.getByText('Wissensdatenbank (Lehrpläne)').click();
  const urlInput = page.getByPlaceholder('https://…/lehrplan.pdf').first();
  await urlInput.fill('http://example.com/lehrplan.pdf');
  await urlInput.press('Enter');
  await page.keyboard.press('Control+,');

  await expect(page.getByText(/Download fehlgeschlagen: Nur HTTPS-Adressen sind erlaubt\./)).toBeVisible();
  await expect(page.getByText(/object Object/)).toHaveCount(0);
});

test('tells the teacher to start the server when nothing answers', async ({ page }) => {
  await page.route('**/api/v1/bootstrap', route => route.abort('connectionrefused'));

  await page.goto('/', { waitUntil: 'domcontentloaded' });

  await expect(page.getByRole('heading', { name: 'Der TeacherAssist-Server läuft nicht' })).toBeVisible();
  await expect(page.getByText(/start\.bat/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Erneut versuchen' })).toBeVisible();
});

test('the header shows a saved OpenRouter key as online', async ({ page }) => {
  // The key lives in the Credential Manager (hasApiKey); the header used to
  // check only the transient input field and showed "API-Key fehlt".
  await setUpApp(page);

  await page.goto('/', { waitUntil: 'domcontentloaded' });

  await expect(page.getByText('Mila · Online')).toBeVisible();
  await expect(page.getByText('⚠ API-Key fehlt')).toHaveCount(0);
});

test('Ollama running without a model asks for ollama pull, not ollama serve', async ({ page }) => {
  // An Ollama-only teacher: with a stored OpenRouter key the app would
  // (correctly) fall back to OpenRouter instead.
  await setUpApp(page, {
    settings: { provider: 'ollama', ollamaModel: 'gemma3:4b', hasApiKey: false },
    status: { ollamaRunning: true, ollamaModels: [], credentials: { hasApiKey: false, hasCustomApiKey: false } },
  });

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('⚠ Kein Ollama-Modell')).toBeVisible();
  const input = page.getByPlaceholder('Nachricht eingeben…');
  await input.fill('Ideen für einen Einstieg');
  await input.press('Enter');

  // The send path switches to the settings page and explains the fix there.
  await expect(page.getByText('Ollama läuft – noch kein Modell installiert')).toBeVisible();
  await expect(page.getByText('ollama pull gemma3:4b')).toBeVisible();
  await expect(page.getByText('ollama serve')).toHaveCount(0);
});

test('the Ollama model picker lists installed models and flags cloud ones', async ({ page }) => {
  await setUpApp(page, {
    settings: { provider: 'ollama', ollamaModel: 'llama3.2:3b' },
    status: {
      capabilities: { ollama: true },
      ollamaRunning: true,
      ollamaModels: [
        { name: 'gemma3:4b', cloud: false },
        { name: 'gpt-oss:120b-cloud', cloud: true },
      ],
    },
  });

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.keyboard.press('Control+,');

  // The list used to stay empty ("Kein Modell gefunden") even with models installed.
  const picker = page.locator('select').filter({ has: page.locator('option', { hasText: 'gemma3:4b' }) });
  await expect(picker.locator('option')).toHaveText([
    'llama3.2:3b (nicht installiert)',
    'gemma3:4b',
    'gpt-oss:120b-cloud (Cloud – nicht für Schülerdaten)',
  ]);
  await expect(picker).toHaveValue('llama3.2:3b');
  await expect(page.getByText('ollama pull llama3.2:3b')).toBeVisible();
  await expect(page.getByText('Kein Modell gefunden')).toHaveCount(0);
});

test('with a stored OpenRouter key, a model-less Ollama falls back and says why', async ({ page }) => {
  await setUpApp(page, {
    settings: { provider: 'ollama', ollamaModel: 'gemma3:4b' },
    status: { ollamaRunning: true, ollamaModels: [] },
  });

  await page.goto('/', { waitUntil: 'domcontentloaded' });

  await expect(page.getByText('⚠ Kein Ollama-Modell · ☁️ OpenRouter Fallback')).toBeVisible();
});

test.describe('calendar export', () => {
  test.use({ timezoneId: 'Europe/Berlin' });

  test('turns a dated exam in an answer into a local-time calendar entry', async ({ page }) => {
    await setUpApp(page, {
      messages: [{ role: 'bot', text: 'Die Klassenarbeit am 15.10.2026 umfasst Bruchrechnung. Viel Erfolg!', ts: 1 }],
    });

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await page.getByTitle('Exportieren / Drucken').click();
    await page.getByRole('button', { name: '📅 Termin' }).click();

    // Prefilled from the answer; the date's dots no longer cut the title.
    await expect(page.locator('input[type="date"]')).toHaveValue('2026-10-15');
    await expect(page.locator('label:text-is("Titel") + input')).toHaveValue('Klassenarbeit am 15.10.2026 umfasst Bruchrechnung');
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: /\.ics herunterladen/ }).click();
    const file = await download;
    const ics = await readFile(await file.path(), 'utf8');

    // 08:00 must stay 08:00: it used to be written as UTC without "Z" (06:00).
    expect(ics).toContain('DTSTART:20261015T080000\r\n');
    expect(ics).toContain('DTEND:20261015T084500\r\n');
    expect(ics).toMatch(/DTSTAMP:\d{8}T\d{6}Z/);
  });
});

test('a chat that went local says why and offers a new chat', async ({ page }) => {
  await setUpApp(page);
  await page.route('**/api/v1/chat', route => route.fulfill({
    contentType: 'text/event-stream',
    body: sse(
      { type: 'privacy', mode: 'local_required', reasons: ['personal_data:person_name', 'sensitive_skill:zeugnis_formulieren'] },
      { type: 'chunk', text: 'Lokale Antwort.' },
      { type: 'done' },
    ),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const input = page.getByPlaceholder('Nachricht eingeben…');
  await input.fill('Zeugnistext für Max');
  await input.press('Enter');

  const banner = page.getByTestId('local-mode-banner');
  await expect(banner).toContainText('Dieser Chat läuft nur lokal');
  await expect(banner).toContainText('möglicher Personenname');
  await expect(banner).toContainText('Datenschutz-Skill „Zeugnis formulieren“');

  await banner.getByRole('button', { name: 'Neuer Chat' }).click();
  await expect(page.getByTestId('local-mode-banner')).toHaveCount(0);
});

test('a refused local-only request names the reason', async ({ page }) => {
  await setUpApp(page);
  await page.route('**/api/v1/chat', route => route.fulfill({
    status: 409,
    contentType: 'application/json',
    body: JSON.stringify({ error: {
      code: 'LOCAL_MODEL_REQUIRED',
      message: 'Dieses Material braucht ein lokales Modell. Ollama ist nicht verfügbar.',
      reasons: ['personal_data:person_name'],
    } }),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const input = page.getByPlaceholder('Nachricht eingeben…');
  await input.fill('Feedback für Max');
  await input.press('Enter');

  await expect(page.getByText('Dieses Material braucht ein lokales Modell.', { exact: false })).toBeVisible();
  await expect(page.getByText(/Grund:.*möglicher Personenname/)).toBeVisible();
  await expect(page.getByText(/Fehler bei der Anfrage/)).toHaveCount(0);
});

test('a capped scanned curriculum PDF says how many pages were read', async ({ page }) => {
  await setUpApp(page);
  await page.route('**/api/v1/download-url', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ saved: ['/tmp/x.pdf'], filename: 'Lehrplan.pdf' }),
  }));
  await page.route('**/api/v1/ingest', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ success: true, chunks: 40, words: 9000, totalPages: 180, ocrPages: 50, ocrTruncated: true }),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.keyboard.press('Control+,');
  await page.getByText('Wissensdatenbank (Lehrpläne)').click();
  const urlInput = page.getByPlaceholder('https://…/lehrplan.pdf').first();
  await urlInput.fill('https://example.org/lehrplan.pdf');
  await urlInput.press('Enter');
  await page.keyboard.press('Control+,');

  await expect(page.getByText(/nur die ersten 50 von 180 Seiten eingelesen/)).toBeVisible();
});
