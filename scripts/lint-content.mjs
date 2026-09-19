#!/usr/bin/env node
import { readdir, readFile } from 'node:fs/promises';
import { extname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../src', import.meta.url));
const EXTENSIONS = ['.md', '.mdx', '.astro'];

const FORBIDDEN = [
  'buy rating',
  'sell rating',
  'hold rating',
  'strong buy',
  'price target',
  'target price',
  'you should buy',
  'you should sell',
  'guaranteed',
  'risk-free',
  "can't lose",
  'sure thing',
  'to the moon',
];

const ALLOW_COMMENT = /lint-allow:/i;

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(full)));
    } else if (EXTENSIONS.includes(extname(entry.name))) {
      files.push(full);
    }
  }
  return files;
}

const files = await walk(ROOT);
const violations = [];

for (const file of files) {
  const text = await readFile(file, 'utf8');
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const lower = lines[i].toLowerCase();
    const hit = FORBIDDEN.find((phrase) => lower.includes(phrase));
    if (!hit) continue;
    if (ALLOW_COMMENT.test(lines[i - 1] ?? '')) continue;
    violations.push({ file, line: i + 1, phrase: hit });
  }
}

if (violations.length > 0) {
  console.error('Content lint failed:');
  for (const v of violations) {
    console.error(`  ${relative(process.cwd(), v.file)}:${v.line} — contains "${v.phrase}"`);
  }
  process.exit(1);
}

console.log(`Content lint passed (${files.length} files checked).`);
