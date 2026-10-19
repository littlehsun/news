import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../assets/theme.js', import.meta.url), 'utf8');
function setup({ stored = null, dark = false, blocked = false } = {}) {
  const events = {}, docEvents = {}, mediaEvents = {};
  const values = new Map(stored === null ? [] : [['brief-theme', stored]]);
  const root = { dataset: {} }, meta = {};
  const buttons = ['light', 'dark', 'system'].map(value => ({
    dataset: { themeChoice: value }, attributes: {},
    setAttribute(key, value) { this.attributes[key] = value; },
    classList: { toggle() {} },
    closest() { return this; }
  }));
  const media = { matches: dark, addEventListener(key, callback) { mediaEvents[key] = callback; } };
  const localStorage = {
    getItem(key) { if (blocked) throw new Error('blocked'); return values.get(key) ?? null; },
    setItem(key, value) { if (blocked) throw new Error('blocked'); values.set(key, value); }
  };
  const document = {
    documentElement: root, querySelector: () => meta, querySelectorAll: () => buttons,
    addEventListener(key, callback) { docEvents[key] = callback; }
  };
  const window = { matchMedia: () => media, addEventListener(key, callback) { events[key] = callback; } };
  vm.runInNewContext(source, { document, window, localStorage });
  return { root, meta, buttons, values,
    click(value) { docEvents.click({ target: buttons.find(b => b.dataset.themeChoice === value) }); },
    system(dark) { media.matches = dark; mediaEvents.change(); },
    storage(value, key = 'brief-theme') { events.storage({ key, newValue: value }); },
    ready() { docEvents.DOMContentLoaded(); }
  };
}

test('first visit follows the operating system before DOM ready', () => {
  for (const dark of [true, false]) {
    const app = setup({ dark });
    assert.equal(app.root.dataset.themePreference, 'system');
    assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light');
    app.ready();
    assert.equal(app.buttons[2].attributes['aria-pressed'], 'true');
    assert.equal(app.values.has('brief-theme'), false);
  }
});
test('explicit themes persist and are not overridden by system changes', () => {
  const app = setup({ dark: true });
  app.click('light'); app.system(true);
  assert.equal(app.root.dataset.theme, 'light');
  assert.equal(app.values.get('brief-theme'), 'light');
  app.click('dark'); app.system(false);
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.meta.content, '#171b25');
  assert.equal(app.buttons.filter(b => b.attributes['aria-pressed'] === 'true').length, 1);
});
test('system mode reacts immediately and remains system in storage', () => {
  const app = setup({ stored: 'dark' });
  app.click('system'); app.system(false);
  assert.equal(app.root.dataset.theme, 'light');
  app.system(true);
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.values.get('brief-theme'), 'system');
});
test('existing choices are restored and invalid storage falls back safely', () => {
  for (const stored of ['light', 'dark', 'system', 'invalid', '']) {
    const app = setup({ stored, dark: true });
    assert.equal(app.root.dataset.themePreference, ['light', 'dark'].includes(stored) ? stored : 'system');
    assert.equal(app.root.dataset.theme, stored === 'light' ? 'light' : 'dark');
  }
});
test('disabled storage does not stop theme controls', () => {
  const app = setup({ blocked: true });
  app.click('dark'); assert.equal(app.root.dataset.theme, 'dark');
  app.click('system'); app.system(false); assert.equal(app.root.dataset.theme, 'light');
});
test('cross-tab storage changes and clearing storage are applied', () => {
  const app = setup({ stored: 'light', dark: true });
  app.storage('dark'); assert.equal(app.root.dataset.themePreference, 'dark');
  app.storage('light', 'brief-saved'); assert.equal(app.root.dataset.theme, 'dark');
  app.storage(null, null); assert.equal(app.root.dataset.themePreference, 'system');
  assert.equal(app.root.dataset.theme, 'dark');
});
