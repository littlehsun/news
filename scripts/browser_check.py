#!/usr/bin/env python3
"""Real Chromium smoke tests; optional CI dependency: playwright==1.56.0."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'browser-preview'
OUTPUT.mkdir(exist_ok=True)
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT.parent))
server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
errors = []
checks = []

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until='networkidle')
        expect(page.locator('.story')).to_have_count(20)
        expect(page.locator('.highlight')).to_have_count(3)
        checks.append('latest edition: 20 stories, 3 executive highlights')
        page.screenshot(path=str(OUTPUT / 'desktop.png'))
        page.locator('[data-filter="ai"]').click()
        expect(page.locator('.story')).to_have_count(5)
        page.locator('[data-filter="all"]').click()
        expect(page.locator('.story')).to_have_count(20)
        checks.append('category filters')
        page.locator('.story-title').first.click()
        expect(page.locator('#reader')).to_be_visible()
        expect(page.locator('#reader-body')).to_contain_text('二階影響')
        expect(page.locator('#reader-body .field')).to_have_count(4)
        page.screenshot(path=str(OUTPUT / 'reader.png'))
        page.locator('#reader-save').click()
        expect(page.locator('#saved-count')).to_have_text('1')
        expect(page.locator('#reader-save')).to_have_attribute('aria-pressed', 'true')
        page.locator('#reader-next').click()
        expect(page.locator('#reader-position')).to_have_text('2 / 20')
        page.keyboard.press('Escape')
        expect(page.locator('#reader')).not_to_be_visible()
        checks.append('reader, four analysis fields, next story, Escape')
        page.reload(wait_until='networkidle')
        expect(page.locator('#saved-count')).to_have_text('1')
        page.locator('[data-view="saved"]').click()
        expect(page.locator('.story')).to_have_count(1)
        checks.append('bookmarks persist across reload')
        page.locator('[data-view="archive"]').click()
        expect(page.locator('.archive-card')).to_have_count(18)
        expect(page.locator('.archive-card.missing')).to_have_count(2)
        page.screenshot(path=str(OUTPUT / 'archive.png'))
        checks.append('16 editions + 2 explicit missing dates')
        page.locator('#search').fill('vLLM')
        expect(page.locator('#feed-title')).to_have_text('搜尋結果')
        expect(page.locator('.story').first).to_be_visible()
        assert page.locator('.story').count() > 5
        checks.append('full-text search across dates')
        page.goto(BASE + '?edition=2026-10-01&story=tech-5', wait_until='networkidle')
        expect(page.locator('#reader-title')).to_contain_text('TSMC')
        expect(page.locator('#reader-position')).to_have_text('10 / 20')
        page.locator('#reader-next').click()
        expect(page.locator('#reader-position')).to_have_text('11 / 20')
        assert 'story=markets-1' in page.url
        page.locator('#close').click()
        checks.append('GitHub Pages subpath + deep-link + reader navigation')
        page.locator('[data-theme-choice="dark"]').click()
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        page.screenshot(path=str(OUTPUT / 'dark.png'))
        page.reload(wait_until='networkidle')
        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
        checks.append('theme persistence')
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True, reduced_motion='reduce')
        mobile = mobile_context.new_page()
        mobile.on('pageerror', lambda e: errors.append(str(e)))
        mobile.goto(BASE, wait_until='networkidle')
        expect(mobile.locator('.story')).to_have_count(20)
        sizes = mobile.evaluate('({width:innerWidth, scroll:document.documentElement.scrollWidth})')
        assert sizes['width'] == sizes['scroll'], sizes
        mobile.screenshot(path=str(OUTPUT / 'mobile.png'))
        mobile.screenshot(path=str(OUTPUT / 'mobile-full.png'), full_page=True)
        mobile.locator('#menu').click()
        expect(mobile.locator('#menu')).to_have_attribute('aria-expanded', 'true')
        mobile.locator('[data-view="saved"]').click()
        expect(mobile.locator('#feed-title')).to_have_text('我的收藏')
        expect(mobile.locator('#menu')).to_have_attribute('aria-expanded', 'false')
        checks.append('390px mobile layout, no overflow, drawer navigation')
        assert not errors, errors
        report = {'passed': True, 'checks': checks, 'page_errors': errors}
        (OUTPUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        browser.close()
finally:
    server.shutdown()
