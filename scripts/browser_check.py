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
manifest = json.loads((ROOT / 'content/index.json').read_text())
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
        for theme in ('light', 'dark'):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            styles = page.locator('.highlight').evaluate_all('(els) => els.map(el => {const s = getComputedStyle(el); return [s.backgroundColor, s.color, el.getBoundingClientRect().width]})')
            assert styles[0][:2] == styles[1][:2] == styles[2][:2], styles
            assert max(s[2] for s in styles) - min(s[2] for s in styles) < 1, styles
        page.locator('[data-theme-choice="light"]').click()
        checks.append('20 stories, 3 highlights with equal color and width in both themes')
        expect(page.locator('.avatar')).to_have_js_property('naturalWidth', 160)
        expect(page.locator('.brand-icon, .masthead-mark')).to_have_count(0)
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
        expect(page.locator('.archive-card')).to_have_count(sum(e['date'].startswith(manifest['editions'][0]['date'][:7]) for e in manifest['editions']))
        expect(page.locator('.calendar-day.missing')).to_have_count(len(manifest['missingDates']))
        expect(page.locator('.archive-calendar th')).to_have_count(7)
        # October 2026 begins on Thursday: Monday-first calendars need 3 leading cells.
        assert page.locator('.calendar-day').nth(3).locator('time').get_attribute('datetime') == '2026-10-01'
        expect(page.locator('[data-edition="2026-10-03"]')).to_have_count(1)
        expect(page.locator('#month-prev')).to_be_disabled()
        expect(page.locator('#month-next')).to_be_disabled()
        page.locator('#archive-zoom').focus()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#archive-zoom-value')).to_have_text('120%')
        page.locator('#archive-zoom').press('End')
        expect(page.locator('#archive-zoom-value')).to_have_text('140%')
        assert page.locator('.calendar-day').first.evaluate('(el) => el.getBoundingClientRect().height') >= 266
        assert page.evaluate('innerWidth === document.documentElement.scrollWidth')
        page.locator('#archive-zoom').press('Home')
        page.keyboard.press('ArrowRight')
        page.screenshot(path=str(OUTPUT / 'archive.png'))
        page.locator('[data-theme-choice="dark"]').click()
        page.screenshot(path=str(OUTPUT / 'archive-dark.png'))
        page.locator('[data-theme-choice="light"]').click()
        page.locator('[data-edition="2026-10-03"]').click()
        expect(page.locator('#edition-select')).to_have_value('2026-10-03')
        expect(page.locator('.story')).to_have_count(20)
        checks.append('calendar weekday alignment, keyboard zoom, no overflow, October 3 opens once')
        checks.append('archive matches current manifest, including missing dates')
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
        page.goto(BASE + '?edition=2026-10-03-v2&story=ai-1', wait_until='networkidle')
        expect(page.locator('#edition-select')).to_have_value('2026-10-03')
        expect(page.locator('#reader-title')).to_contain_text('Claude Frontier Academy')
        page.locator('#close').click()
        page.goto(BASE + '?edition=2026-10-03-v1&story=ai-1', wait_until='networkidle')
        expect(page.locator('#reader')).not_to_be_visible()
        expect(page.locator('#edition-select')).to_have_value('2026-10-03')
        checks.append('old second-edition links still work; archived first-edition stories are not silently substituted')
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
        mobile.locator('#menu').click()
        mobile.locator('[data-view="archive"]').click()
        expect(mobile.locator('.archive-calendar')).to_be_visible()
        assert mobile.evaluate('innerWidth === document.documentElement.scrollWidth')
        mobile.screenshot(path=str(OUTPUT / 'archive-mobile.png'))
        mobile.locator('#archive-zoom').focus()
        mobile.locator('#archive-zoom').press('End')
        assert mobile.evaluate('innerWidth === document.documentElement.scrollWidth')
        mobile.locator('[data-edition="2026-10-03"]').click()
        expect(mobile.locator('#edition-select')).to_have_value('2026-10-03')
        checks.append('390px calendar, zoom and edition selection without page overflow')
        for width, height in [(375, 812), (768, 1024), (1024, 768), (1440, 1000), (812, 375)]:
            mobile.set_viewport_size({'width': width, 'height': height})
            assert mobile.evaluate('innerWidth === document.documentElement.scrollWidth'), (width, height)
        checks.append('375 / 768 / 1024 / 1440px and landscape without overflow')
        assert not errors, errors
        report = {'passed': True, 'checks': checks, 'page_errors': errors}
        (OUTPUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        browser.close()
finally:
    server.shutdown()
