/* Resolve the preference before styles load, without depending on the news app. */
(() => {
  'use strict';
  const KEY = 'brief-theme';
  const choices = new Set(['light', 'dark', 'system']);
  const root = document.documentElement;
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = value => choices.has(value) ? value : 'system';
  let preference = 'system';
  try { preference = valid(localStorage.getItem(KEY)); } catch { /* Storage is optional. */ }

  function render() {
    const theme = preference === 'system' ? (media.matches ? 'dark' : 'light') : preference;
    root.dataset.theme = theme;
    root.dataset.themePreference = preference;
    const color = document.querySelector('meta[name="theme-color"]');
    if (color) color.content = theme === 'dark' ? '#171b25' : '#f8f7f4';
    const toggle = document.querySelector('[data-theme-toggle]');
    if (toggle) {
      toggle.setAttribute('aria-checked', String(theme === 'dark'));
      toggle.title = `${preference === 'system' ? '跟隨系統顏色' : '手動設定'}；切換至${theme === 'dark' ? '淺色' : '深色'}模式`;
    }
    const reset = document.querySelector('[data-theme-choice="system"]');
    if (reset) reset.setAttribute('aria-pressed', String(preference === 'system'));
  }

  function select(value) {
    preference = valid(value);
    try { localStorage.setItem(KEY, preference); } catch { /* Keep working for this visit. */ }
    render();
  }

  render();
  document.addEventListener('DOMContentLoaded', render, { once: true });
  document.addEventListener('click', event => {
    if (event.target.closest('[data-theme-toggle]')) {
      select(root.dataset.theme === 'dark' ? 'light' : 'dark');
      return;
    }
    const button = event.target.closest('[data-theme-choice]');
    if (button) select(button.dataset.themeChoice);
  });
  const onSystemChange = () => { if (preference === 'system') render(); };
  if (media.addEventListener) media.addEventListener('change', onSystemChange);
  else if (media.addListener) media.addListener(onSystemChange);
  window.addEventListener('storage', event => {
    if (event.key === KEY || event.key === null) {
      preference = valid(event.newValue);
      render();
    }
  });
})();
