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
def choose_theme(page, choice):
    root = page.locator('html')
    switch = page.locator('[data-theme-toggle]')
    if choice == 'system':
        reset = page.locator('[data-theme-choice="system"]')
        if reset.is_visible():
            reset.click()
    else:
        if root.get_attribute('data-theme') == choice and root.get_attribute('data-theme-preference') != choice:
            switch.click()
        if root.get_attribute('data-theme') != choice:
            switch.click()

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
        expect(page.locator('[data-theme-choice="system"]')).to_be_visible()
        expect(page.locator('[data-theme-choice="system"]')).to_have_attribute('aria-pressed', 'true')
        for choice in ('light', 'dark', 'system'):
            bounds = page.locator('#theme').bounding_box()
            choose_theme(page, choice)
            expect(page.locator('[data-theme-choice="system"]')).to_be_visible()
            expect(page.locator('[data-theme-choice="system"]')).to_have_attribute('aria-pressed', str(choice == 'system').lower())
            assert page.locator('#theme').bounding_box() == bounds
            expect(page.locator('html')).to_have_attribute('data-theme-preference', choice)
            expect(page.locator('[data-theme-toggle]')).to_have_attribute('aria-checked', str(page.locator('html').get_attribute('data-theme') == 'dark').lower())
            page.reload(wait_until='networkidle')
            expect(page.locator('html')).to_have_attribute('data-theme-preference', choice)
        page.emulate_media(color_scheme='light')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.screenshot(path=str(OUTPUT / 'theme-light.png'))
        page.emulate_media(color_scheme='dark')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        page.screenshot(path=str(OUTPUT / 'theme-system-dark.png'))
        choose_theme(page, 'light')
        page.emulate_media(color_scheme='dark')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        page.locator('[data-theme-toggle]').focus()
        page.keyboard.press('Enter')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        checks.append('sun/moon switch, system reset, reload persistence, live system changes and keyboard access')
        page2 = context.new_page()
        page2.goto(BASE, wait_until='networkidle')
        choose_theme(page2, 'light')
        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        checks.append('theme selection synchronizes across browser tabs')
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, color_scheme='dark')
        mobile = mobile_context.new_page()
        mobile.on('pageerror', lambda error: errors.append(str(error)))
        mobile.goto(BASE, wait_until='networkidle')
        mobile.locator('#menu').click()
        choose_theme(mobile, 'light')
        expect(mobile.locator('html')).to_have_attribute('data-theme', 'light')
        choose_theme(mobile, 'system')
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
        choose_theme(restricted, 'light')
        expect(restricted.locator('html')).to_have_attribute('data-theme', 'light')
        checks.append('disabled localStorage does not break page or theme switching')
        assert not errors, errors
        result = {'passed': True, 'checks': checks, 'page_errors': errors}
        (OUTPUT / 'theme-report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()
finally:
    server.shutdown()
