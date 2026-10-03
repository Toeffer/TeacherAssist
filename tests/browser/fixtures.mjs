// Shared mocked-backend setup for the browser specs: every /api/v1 call the
// app makes on load is answered here, so no tool_server.py is needed.

export const CHAT_ID = '11111111-1111-4111-8111-111111111111';

export function bootstrapPayload({ messages = [], settings = {} } = {}) {
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
      ...settings,
    },
    state: {
      stateRevision: 7,
      profile: { assistant_name: 'Mila', name: 'Alex' },
      chats: [{ id: CHAT_ID, title: 'Gespeicherter Chat', messages, ocrJobIds: [], privacyMode: 'auto' }],
    },
  };
}

export async function setUpApp(page, { messages = [], settings = {}, status = {} } = {}) {
  const stateWrites = [];
  await page.addInitScript(() => localStorage.setItem('ta_onboarded', 'true'));
  await page.route('**/api/v1/bootstrap', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify(bootstrapPayload({ messages, settings })),
  }));
  await page.route('**/api/v1/status', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      capabilities: { ollama: false },
      credentials: { hasApiKey: true, hasCustomApiKey: false },
      ollamaRunning: false,
      ollamaModels: [],
      ...status,
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
