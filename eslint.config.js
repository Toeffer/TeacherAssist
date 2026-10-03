import { readFileSync } from 'node:fs';

import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

// app.jsx, components.jsx, ocr-ui.jsx and tweaks-panel.jsx share code through
// window globals rather than imports: each file ends with
// Object.assign(window, { ... }). Reading those blocks keeps no-undef in step
// with what the files really export, without a hand-maintained list.
function windowExports(...files) {
  const names = {};
  for (const file of files) {
    const source = readFileSync(new URL(file, import.meta.url), 'utf8');
    for (const block of source.matchAll(/Object\.assign\(window,\s*\{([^}]*)\}\s*\)/g)) {
      for (const entry of block[1].split(',')) {
        const name = entry.split(':')[0].trim();
        if (name) names[name] = 'readonly';
      }
    }
  }
  return names;
}

const sharedAppGlobals = {
  ...windowExports('components.jsx', 'ocr-ui.jsx', 'tweaks-panel.jsx'),
  // set up by src/main.jsx and api-client.js before the app files load
  React: 'readonly',
  ReactDOM: 'readonly',
  SanitizedMarkdown: 'readonly',
  taFetch: 'readonly',
};

export default [
  { ignores: ['web_dist/**', 'node_modules/**', 'test-results/**', 'playwright-report/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,mjs}'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: { react, 'react-hooks': reactHooks },
    settings: { react: { version: '18.3' } },
    rules: {
      // `catch {}` is the deliberate "best effort" idiom throughout the app.
      'no-empty': ['error', { allowEmptyCatch: true }],
      // Mark components used in JSX as used / defined.
      'react/jsx-uses-vars': 'error',
      'react/jsx-no-undef': ['error', { allowGlobals: true }],
      'react/jsx-key': 'error',
      'react-hooks/rules-of-hooks': 'error',
      // Would have caught the stale hasApiKey in handleSend's dependencies.
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
  {
    files: ['app.jsx', 'components.jsx', 'ocr-ui.jsx', 'tweaks-panel.jsx', 'src/**/*.jsx', 'api-client.js'],
    languageOptions: { globals: { ...globals.browser, ...sharedAppGlobals } },
  },
  {
    files: ['service-worker.js'],
    languageOptions: { sourceType: 'script', globals: globals.serviceworker },
  },
  {
    files: ['scripts/**/*.mjs', '*.config.{js,mjs}', 'tests/browser/**/*.mjs'],
    languageOptions: { globals: globals.node },
  },
];
