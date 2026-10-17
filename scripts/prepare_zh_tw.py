"""One-time editorial/theme migration on the isolated feature branch only."""
from pathlib import Path
import hashlib
import re
from check_locale import normalize, paths

ROOT = Path(__file__).resolve().parents[1]

def current(name, expected):
    path = ROOT / name
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != expected:
        raise RuntimeError(f'{name} changed; inspect it before applying this migration')
    return path, data.decode()

def replace(text, old, new):
    if old not in text:
        raise RuntimeError(f'Migration anchor not found: {old[:70]}')
    return text.replace(old, new)

path, text = current('assets/app.js', 'e6b378227651455c5853b5bb0f9e5200938c643e')
text = '\n'.join(line for line in text.split('\n') if not line.startswith("$('#theme').onclick="))
text = replace(text, "const state=", "const TRACK_LABEL={Today:'今天', 'This Week':'本週', 'Worth Tracking':'值得追蹤'};\nconst state=")
text = replace(text, '<h3>${escape(t.title)}</h3>', '<h3>${escape(TRACK_LABEL[t.title]||t.title)}</h3>')
text = replace(text, "openText(t.title,t.body,'KEEP THE THREAD')", "openText(TRACK_LABEL[t.title]||t.title,t.body,'持續追蹤')")
text = text.replace("'READING ROOM'", "'閱讀空間'").replace("'FULL EDITION'", "'完整簡報'").replace("'ABOUT THE ARCHIVE'", "'來源說明'")
text = text.replace(' DAYS / ${editions.length} EDITIONS', ' 個日期 · ${editions.length} 份簡報')
path.write_text(text, encoding='utf-8')

path, text = current('index.html', '3c18270116e995c5b2a3e92cb3ba04c5c624336d')
text = replace(text, 'lang="zh-Hant"', 'lang="zh-Hant-TW"')
text = replace(text, '<link rel="icon"', '<script src="assets/theme.js"></script>\n<link rel="icon"')
text = replace(text, '<script src="assets/theme.js"></script><script type="module"', '<link rel="stylesheet" href="assets/theme.css">\n<script type="module"')
text = replace(text, '<div><span>Asia / Taipei</span><button id="theme" class="icon-button" aria-label="切換深色模式" title="切換深色模式">◐</button></div>', '<div><span>台灣時間</span></div><fieldset id="theme" class="theme-picker"><legend>顯示主題</legend><div class="theme-options" role="group" aria-label="顯示主題"><button type="button" data-theme-choice="light" aria-pressed="false">淺色</button><button type="button" data-theme-choice="dark" aria-pressed="false">深色</button><button type="button" data-theme-choice="system" aria-pressed="true">跟隨系統</button></div></fieldset>')
labels = {'YOUR DAILY PERSPECTIVE':'每天一點新觀點', 'FOUR PERSPECTIVES':'四大主題', 'A LITTLE CONTEXT':'多一點脈絡', 'THE SIGNAL, NOT THE NOISE.':'讀重點，也讀懂脈絡。', 'DAILY TECH & MARKET BRIEF':'每日科技與市場簡報', 'THE BIG PICTURE':'掌握今日重點', 'GO A LITTLE DEEPER':'再多看一層', 'KEEP THE THREAD':'持續追蹤', 'BRIEF / DAILY':'每日精選', '歷史歸檔':'歷史簡報'}
for old, new in labels.items():
    text = replace(text, old, new)
path.write_text(text, encoding='utf-8')

path, text = current('scripts/browser_check.py', 'f602a0ed3e8f9d638e412392b3db124b46733717')
text = replace(text, "page.locator('#theme').click()", "page.locator('[data-theme-choice=\"dark\"]').click()")
path.write_text(text, encoding='utf-8')

path, text = current('.github/workflows/pages.yml', '4f07f9c90b4e0ef6baee8a4f73371c5e228a9bf2')
text = replace(text, '      - name: Validate archive structure and source links', '      - name: Install language checker\n        run: python3 -m pip install -r requirements-dev.txt\n      - name: Check Taiwanese Traditional Chinese\n        run: |\n          python3 scripts/check_locale.py\n          python3 scripts/test_locale.py\n      - name: Validate archive structure and source links')
text = replace(text, '        run: python3 scripts/browser_check.py', '        run: |\n          python3 scripts/browser_check.py\n          python3 scripts/theme_browser_check.py')
path.write_text(text, encoding='utf-8')

policy = '''\n## 台灣繁體中文規範\n\n網站介面、README、新聞全文、標題、索引及發稿範本一律使用繁體中文與台灣慣用詞。使用軟體、硬體、伺服器、網路、記憶體、快取、程式碼、資料庫、演算法、生命週期等用語；英文產品名稱、模型識別碼、程式碼與真實來源網址保持原樣。不能只轉換字形而忽略上下文；例如物理質量與資產配置應保留其原意。\n\n發布前執行 `python3 -m pip install -r requirements-dev.txt`、`python3 scripts/check_locale.py`、`python3 scripts/test_locale.py`，再執行原有內容與前端測試。CI 會阻擋未通過用語檢查的內容。自動檢查是輔助工具，仍需人工校閱，不是事實查核。歷史稿僅校正文字，不修改事件、數字或來源查核狀態。\n'''
for name in ('AGENTS.md', 'PUBLISHING.md'):
    path = ROOT / name
    path.write_text(path.read_text(encoding='utf-8') + policy, encoding='utf-8')
path = ROOT / 'templates/brief.md'
text = path.read_text(encoding='utf-8')
text = text.replace('\n\n', '\n\n用語規範：全文使用台灣繁體中文；產品名稱、模型識別碼與來源網址保留原樣。發布前須通過 `scripts/check_locale.py`。\n\n', 1)
path.write_text(text, encoding='utf-8')

changed = []
for path in paths(ROOT):
    before = path.read_text(encoding='utf-8')
    after = normalize(before)
    if after == before:
        continue
    assert re.findall(r'[\x00-\x7f]+', before) == re.findall(r'[\x00-\x7f]+', after), str(path)
    if path.suffix == '.md' and 'content/2026/10/' in path.as_posix():
        note = '> 用語校訂：2026-10-17 統一繁體中文與台灣用語；原有數字、事件說法與查核狀態維持不變。\n\n'
        title, rest = after.split('\n', 1)
        after = title + '\n\n' + normalize(note) + rest.lstrip('\n')
    path.write_text(after, encoding='utf-8')
    changed.append(str(path.relative_to(ROOT)))
print('Localized files:', len(changed), '\n' + '\n'.join(changed))
