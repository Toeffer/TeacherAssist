// Writes web_dist/build-stamp.json: a fingerprint of every input of the
// Vite build (scripts/web-dist-inputs.json). tests/test_web_dist_freshness.py
// recomputes it, so a source change committed without `npm run build`
// fails the test suite instead of shipping a stale web_dist/.
//
// Text files are hashed with CRLF normalized to LF, so a Windows checkout
// (core.autocrlf) and Linux CI produce the same fingerprint.
import { createHash } from 'node:crypto';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { extname, join, relative, sep } from 'node:path';

const config = JSON.parse(await readFile('scripts/web-dist-inputs.json', 'utf8'));

async function walk(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) result.push(...await walk(path));
    else result.push(relative('.', path).split(sep).join('/'));
  }
  return result;
}

const sources = [...config.files];
for (const directory of config.directories) sources.push(...await walk(directory));
sources.sort();

const overall = createHash('sha256');
for (const source of sources) {
  let content = await readFile(source);
  if (!config.binaryExtensions.includes(extname(source).toLowerCase())) {
    content = Buffer.from(content.toString('utf8').replace(/\r\n/g, '\n'), 'utf8');
  }
  overall.update(`${source}\n${createHash('sha256').update(content).digest('hex')}\n`);
}

await writeFile(
  'web_dist/build-stamp.json',
  JSON.stringify({ sources, fingerprint: overall.digest('hex') }, null, 2) + '\n',
  'utf8',
);
