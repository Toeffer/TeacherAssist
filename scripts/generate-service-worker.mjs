import { createHash } from 'node:crypto';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, relative, resolve, sep } from 'node:path';

const root = resolve('web_dist');

async function files(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) result.push(...await files(path));
    else if (entry.name !== 'service-worker.js') result.push(path);
  }
  return result;
}

const assets = (await files(root)).map(path => `/${relative(root, path).split(sep).join('/')}`);
const digest = createHash('sha256').update(assets.join('\n')).digest('hex').slice(0, 12);
const template = await readFile('service-worker.js', 'utf8');
const output = template
  .replace("const CACHE = 'teacherassist-v3';", `const CACHE = 'teacherassist-${digest}';`)
  .replace("self.__TEACHERASSIST_ASSETS__ || ['/', '/index.html', '/manifest.json']", JSON.stringify(['/'].concat(assets)));
await writeFile(join(root, 'service-worker.js'), output, 'utf8');
