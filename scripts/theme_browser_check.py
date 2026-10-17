#!/usr/bin/env python3
"""Chromium checks for theme preferences on desktop, mobile and restricted storage."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'browser-preview'
OUTPUT.mkdir(exist_ok=True)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT.parent)))
Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
errors, checks = [], []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='dark')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until='networkidle')
        expect(page.locator('.story')).to_have_count(20)
        expect(page.locator('html')).to_have_attribute('lang', 'zh-Hant-TW')
        expect(page.locator('html')).to_have_attribute('data-theme-preference', 'system')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        for choice in ('light', 'dark', 'system'):
            page.locator(f'[data-theme-choice="{choice}"]').click()
            expect(page.locator(f'[data-theme-choice="{choice}"]')).to_have_attribute('aria-pressed', 'true')
            page.reload(wait_until='networkidle')
            expect(page.locator('html')).to_have_attribute('data-theme-preference', choice)
        page.emulate_media(color_scheme='light')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.screenshot(path=str(OUTPUT / 'theme-light.png'))
        page.emulate_media(color_scheme='dark')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        page.screenshot(path=str(OUTPUT / 'theme-system-dark.png'))
        page.locator('[data-theme-choice="light"]').click()
        page.emulate_media(color_scheme='dark')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.locator('[data-theme-choice="dark"]').focus()
        page.keyboard.press('Enter')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        checks.append('three choices, reload persistence, live system changes and keyboard access')
        page2 = context.new_page()
        page2.goto(BASE, wait_until='networkidle')
        page2.locator('[data-theme-choice="light"]').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        checks.append('theme selection synchronizes across browser tabs')
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, color_scheme='dark')
        mobile = mobile_context.new_page()
        mobile.on('pageerror', lambda error: errors.append(str(error)))
        mobile.goto(BASE, wait_until='networkidle')
        mobile.locator('#menu').click()
        mobile.locator('[data-theme-choice="light"]').click()
        expect(mobile.locator('html')).to_have_attribute('data-theme', 'light')
        mobile.locator('[data-theme-choice="system"]').click()
        expect(mobile.locator('html')).to_have_attribute('data-theme', 'dark')
        assert mobile.evaluate('innerWidth === document.documentElement.scrollWidth')
        mobile.screenshot(path=str(OUTPUT / 'theme-mobile.png'))
        checks.append('mobile navigation theme controls and no horizontal overflow')
        blocked = browser.new_context(color_scheme='dark')
        blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new Error('Storage disabled');}})")
        restricted = blocked.new_page()
        restricted.on('pageerror', lambda error: errors.append(str(error)))
        restricted.goto(BASE, wait_until='networkidle')
        expect(restricted.locator('.story')).to_have_count(20)
        restricted.locator('[data-theme-choice="light"]').click()
        expect(restricted.locator('html')).to_have_attribute('data-theme', 'light')
        checks.append('disabled localStorage does not break page or theme switching')
        assert not errors, errors
        result = {'passed': True, 'checks': checks, 'page_errors': errors}
        (OUTPUT / 'theme-report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()
finally:
    server.shutdown()
