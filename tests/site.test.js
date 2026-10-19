import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { markdown, plain, parseEdition } from '../assets/markdown.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const index = JSON.parse(fs.readFileSync(path.join(root, 'content/index.json'), 'utf8'));

test('all indexed editions have exactly 20 stories, four groups, three highlights and tracking', () => {
  const seen = new Set();
  for (const meta of index.editions) {
    assert.ok(!seen.has(meta.id), `duplicate ${meta.id}`);
    seen.add(meta.id);
    const raw = fs.readFileSync(path.join(root, meta.path), 'utf8');
    const e = parseEdition(raw);
    assert.equal(e.stories.length, 20, `${meta.id}: expected 20 stories`);
    for (const cat of ['ai', 'tech', 'markets', 'business']) {
      assert.equal(e.stories.filter(s => s.category === cat).length, 5, `${meta.id}/${cat}`);
    }
    assert.equal(new Set(e.stories.map(s => s.id)).size, 20);
    assert.equal(e.highlights.length, 3, `${meta.id}: executive highlights`);
    assert.deepEqual(e.tracking.map(t => t.title), ['Today', 'This Week', 'Worth Tracking']);
    for (const s of e.stories) {
      assert.ok(s.title.length > 2);
      assert.ok(s.summary.length > 20, `${meta.id}/${s.id}: empty summary`);
      assert.ok(s.body.includes('**我的判讀｜**'), `${meta.id}/${s.id}: last field retained`);
      assert.ok(!s.summary.includes('為什麼重要｜'), `${meta.id}/${s.id}: summary boundary`);
    }
  }
});

test('October 3 has one disclosed edition and missing dates remain explicit', () => {
  const editions = index.editions.filter(e => e.date === '2026-10-03');
  assert.equal(editions.length, 1);
  assert.equal(editions[0].id, '2026-10-03');
  assert.equal(editions[0].status, 'unverified_archive');
  const raw = fs.readFileSync(path.join(root, editions[0].path), 'utf8');
  assert.ok(raw.includes('原第一版保留於'));
  assert.ok(raw.includes('版本整理：2026-10-19'));
  for (const date of index.missingDates) assert.ok(!index.editions.some(e => e.date === date));
});

test('renderer escapes raw HTML and does not permit javascript URLs', () => {
  const out = markdown('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[unsafe](javascript:alert)');
  assert.ok(!out.includes('<script'));
  assert.ok(!out.includes('<img'));
  assert.ok(!out.includes('href="javascript:'));
  assert.ok(out.includes('&lt;script&gt;'));
});

test('renderer supports safe links, emphasis and field labels', () => {
  const out = markdown('**摘要｜** [Source](https://example.org/a?b=1&c=2) **重要**');
  assert.match(out, /class="field"/);
  assert.match(out, /rel="noopener noreferrer"/);
  assert.match(out, /&amp;c=2/);
  assert.match(out, /<strong>重要<\/strong>/);
});

test('tables and code blocks render without executing markup', () => {
  const out = markdown('| A | B |\n| --- | --- |\n| x | y |\n\n```js\n<script>\n```');
  assert.match(out, /<table>/);
  assert.match(out, /<td>x<\/td>/);
  assert.match(out, /<pre><code>&lt;script&gt;/);
});

test('plain text extraction strips formatting and unresolved citation widgets', () => {
  assert.equal(plain('**Hello** [world](https://example.org) `code`'), 'Hello world code');
  assert.equal(plain('a citeturn1news0 b'), 'a b');
});

test('HTML uses subpath-safe assets and no external executable dependencies', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(html.includes('assets/app.js'));
  assert.ok(html.includes('Content-Security-Policy'));
  assert.ok(!/src="https?:/.test(html));
  assert.ok(!/href="\/assets\//.test(html));
  assert.ok(html.includes('lang="zh-Hant-TW"'));
  assert.ok(html.indexOf('assets/theme.js') < html.indexOf('assets/style.css'));
  for (const choice of ['light', 'dark', 'system']) {
    assert.ok(html.includes(`data-theme-choice="${choice}"`));
  }
});
