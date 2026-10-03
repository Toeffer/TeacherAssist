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
