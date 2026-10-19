import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../assets/theme.js', import.meta.url), 'utf8');
function setup({ stored = null, dark = false, blocked = false } = {}) {
  const events = {}, docEvents = {}, mediaEvents = {};
  const values = new Map(stored === null ? [] : [['brief-theme', stored]]);
  const root = { dataset: {} }, meta = {};
  const button = selector => ({
    dataset: { themeChoice: 'system' }, attributes: {}, hidden: false,
    setAttribute(key, value) { this.attributes[key] = value; },
    closest(query) { return query === selector ? this : null; }
  });
  const toggle = button('[data-theme-toggle]'), reset = button('[data-theme-choice]');
  const media = { matches: dark, addEventListener(key, callback) { mediaEvents[key] = callback; } };
  const localStorage = {
    getItem(key) { if (blocked) throw new Error('blocked'); return values.get(key) ?? null; },
    setItem(key, value) { if (blocked) throw new Error('blocked'); values.set(key, value); }
  };
  const document = {
    documentElement: root,
    querySelector: selector => selector === '[data-theme-toggle]' ? toggle : selector === '[data-theme-choice="system"]' ? reset : meta,
    addEventListener(key, callback) { docEvents[key] = callback; }
  };
  const window = { matchMedia: () => media, addEventListener(key, callback) { events[key] = callback; } };
  vm.runInNewContext(source, { document, window, localStorage });
  return { root, meta, toggle, reset, values,
    click() { docEvents.click({ target: toggle }); },
    follow() { docEvents.click({ target: reset }); },
    system(dark) { media.matches = dark; mediaEvents.change(); },
    storage(value, key = 'brief-theme') { events.storage({ key, newValue: value }); },
    ready() { docEvents.DOMContentLoaded(); }
  };
}

test('first visit follows system and switch reflects actual color before DOM ready', () => {
  for (const dark of [true, false]) {
    const app = setup({ dark });
    assert.equal(app.root.dataset.themePreference, 'system');
    assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light');
    app.ready();
    assert.equal(app.toggle.attributes['aria-checked'], String(dark));
    assert.equal(app.reset.hidden, false);
    assert.equal(app.reset.attributes['aria-pressed'], 'true');
    assert.equal(app.values.has('brief-theme'), false);
  }
});
test('toggle chooses the opposite actual color and persists manual preference', () => {
  const app = setup({ dark: true });
  app.click(); app.system(true);
  assert.equal(app.root.dataset.theme, 'light');
  assert.equal(app.values.get('brief-theme'), 'light');
  assert.equal(app.reset.hidden, false);
  assert.equal(app.reset.attributes['aria-pressed'], 'false');
  app.click(); app.system(false);
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.values.get('brief-theme'), 'dark');
  assert.equal(app.meta.content, '#171b25');
  assert.equal(app.toggle.attributes['aria-checked'], 'true');
});
test('monitor stays visible and indicates when live system colors are selected', () => {
  const app = setup({ stored: 'dark' });
  app.follow(); app.system(false);
  assert.equal(app.root.dataset.theme, 'light');
  app.system(true);
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.toggle.attributes['aria-checked'], 'true');
  assert.equal(app.reset.hidden, false);
    assert.equal(app.reset.attributes['aria-pressed'], 'true');
  assert.equal(app.values.get('brief-theme'), 'system');
});
test('existing choices are restored and invalid storage falls back safely', () => {
  for (const stored of ['light', 'dark', 'system', 'invalid', '']) {
    const app = setup({ stored, dark: true });
    assert.equal(app.root.dataset.themePreference, ['light', 'dark'].includes(stored) ? stored : 'system');
    assert.equal(app.root.dataset.theme, stored === 'light' ? 'light' : 'dark');
  }
});
test('disabled storage does not stop the switch or system reset', () => {
  const app = setup({ blocked: true });
  app.click(); assert.equal(app.root.dataset.theme, 'dark');
  app.follow(); app.system(false); assert.equal(app.root.dataset.theme, 'light');
});
test('cross-tab storage changes and clearing storage update the switch', () => {
  const app = setup({ stored: 'light', dark: true });
  app.storage('dark'); assert.equal(app.root.dataset.themePreference, 'dark');
  assert.equal(app.toggle.attributes['aria-checked'], 'true');
  app.storage('light', 'brief-saved'); assert.equal(app.root.dataset.theme, 'dark');
  app.storage(null, null); assert.equal(app.root.dataset.themePreference, 'system');
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.reset.hidden, false);
    assert.equal(app.reset.attributes['aria-pressed'], 'true');
});
