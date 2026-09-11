import { expect, test } from '@playwright/test';

const CHAT_ID = '11111111-1111-4111-8111-111111111111';

function bootstrapPayload({ messages = [] } = {}) {
  return {
    csrfToken: 'browser-test-csrf',
    settings: {
      provider: 'openrouter',
      model: 'deepseek/deepseek-chat',
      ollamaModel: 'gemma3:4b',
      customEndpoint: '',
      customModel: 'gpt-3.5-turbo',
      hasApiKey: true,
      hasCustomApiKey: false,
    },
    state: {
      stateRevision: 7,
      profile: { assistant_name: 'Mila', name: 'Alex' },
      chats: [{ id: CHAT_ID, title: 'Gespeicherter Chat', messages, ocrJobIds: [], privacyMode: 'auto' }],
    },
  };
}

async function setUpApp(page, { messages = [] } = {}) {
  const stateWrites = [];
  await page.addInitScript(() => localStorage.setItem('ta_onboarded', 'true'));
  await page.route('**/api/v1/bootstrap', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify(bootstrapPayload({ messages })),
  }));
  await page.route('**/api/v1/status', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      capabilities: { ollama: false },
      credentials: { hasApiKey: true, hasCustomApiKey: false },
    }),
  }));
  await page.route('**/api/v1/collections', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ chunks: 0 }),
  }));
  await page.route('**/api/v1/state', async route => {
    const body = route.request().postDataJSON();
    stateWrites.push(body);
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ state: { ...bootstrapPayload().state, stateRevision: body.expectedRevision + 1 } }),
    });
  });
  return stateWrites;
}

test('loads the saved chat before mounting and does not replace it during hydration', async ({ page }) => {
  const stateWrites = await setUpApp(page);

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.waitForTimeout(700);

  expect(stateWrites).toEqual([]);
});

test('uses the saved revision only after an actual edit', async ({ page }) => {
  const stateWrites = await setUpApp(page);

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Gespeicherter Chat')).toBeVisible();
  await page.getByRole('button', { name: 'Neuer Chat' }).evaluate(button => button.click());

  await expect.poll(() => stateWrites.length).toBe(1);
  expect(stateWrites[0].expectedRevision).toBe(7);
  expect(stateWrites[0].chats).toHaveLength(2);
  expect(stateWrites[0].chats[0].id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
});

test('shows a retryable error instead of mounting on a failed saved-state bootstrap', async ({ page }) => {
  await page.route('**/api/v1/bootstrap', route => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: JSON.stringify({ error: { code: 'PERSISTENCE_UNAVAILABLE' } }),
  }));

  await page.goto('/', { waitUntil: 'domcontentloaded' });

  await expect(page.getByRole('heading', { name: 'Gespeicherte Daten konnten nicht geladen werden' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Erneut versuchen' })).toBeVisible();
  await expect(page.getByText('Gespeicherter Chat')).toHaveCount(0);
});

test('downloads exports with authenticated fetch from both export UI entry points', async ({ page }) => {
  await setUpApp(page, { messages: [{ role: 'bot', text: 'Exportinhalt', ts: 1 }] });
  const exportRequests = [];
  await page.route('**/api/v1/export-file', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ url: '/api/v1/exports/browser-test.md', filename: 'browser-test.md' }),
  }));
  await page.route('**/api/v1/exports/browser-test.md', route => {
    exportRequests.push(route.request().headers());
    return route.fulfill({
      contentType: 'text/markdown',
      headers: { 'Content-Disposition': 'attachment; filename="browser-test.md"' },
      body: '# Export',
    });
  });

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Exportinhalt')).toBeVisible();
  await page.getByTitle('Exportieren / Drucken').click();
  const firstDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'MD' }).click();
  expect((await firstDownload).suggestedFilename()).toBe('browser-test.md');

  const secondDownload = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Datei herunterladen' }).click();
  expect((await secondDownload).suggestedFilename()).toBe('browser-test.md');

  expect(exportRequests).toHaveLength(2);
  expect(exportRequests.every(headers => headers['x-csrf-token'] === 'browser-test-csrf')).toBe(true);
});
