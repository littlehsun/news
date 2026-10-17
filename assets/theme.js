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
    if (color) color.content = theme === 'dark' ? '#121a17' : '#f7f8f4';
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      const selected = button.dataset.themeChoice === preference;
      button.setAttribute('aria-pressed', String(selected));
      button.classList.toggle('selected', selected);
    });
  }

  function select(value) {
    preference = valid(value);
    try { localStorage.setItem(KEY, preference); } catch { /* Keep working for this visit. */ }
    render();
  }

  render();
  document.addEventListener('DOMContentLoaded', render, { once: true });
  document.addEventListener('click', event => {
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
