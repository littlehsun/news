#!/usr/bin/env python3
"""Check Taiwanese Traditional Chinese in public text and Chinese UI strings.

Use --fix only for an explicitly requested language correction. URLs and ASCII
identifiers are preserved. This is an editorial check, NOT a fact checker.
"""
from __future__ import annotations
import argparse
import difflib
from pathlib import Path
import re
import sys
from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
CONVERTER = OpenCC('s2twp')
HAN = re.compile(r'[\u3400-\u9fff]+')
URL = re.compile(r'https?://[^\s<>\]\)\"\x27]+')
# Keys use escapes so rule definitions themselves contain no simplified text.
TERMS = {
    '\u751f\u547d\u5468\u671f': '生命週期',
    '\u5468\u671f': '週期',
    '\u670d\u52d9\u5668': '伺服器',
    '\u6578\u64da\u4e2d\u5fc3': '資料中心',
    '\u6578\u64da\u5eab': '資料庫',
    '\u4fe1\u606f': '資訊',
    '\u9ed8\u8a8d': '預設',
    '\u8abf\u7528': '呼叫',
    '\u5b57\u7b26\u4e32': '字串',
    '\u8b8a\u91cf': '變數',
    '\u63a5\u53e3': '介面',
    '\u5b58\u5132': '儲存',
    '\u8996\u983b': '影片',
    '\u97f3\u983b': '音訊',
    '\u5167\u5b58': '記憶體',
    '\u7de9\u5b58': '快取',
    '\u7db2\u7d61': '網路',
    '\u4ee3\u78bc': '程式碼',
    '\u914d\u7f6e\u6587\u4ef6': '設定檔',
    '\u914d\u7f6e\u6a94': '設定檔',
    '\u8cec\u865f': '帳號',
    '\u6578\u64da\u8cea\u91cf': '資料品質',
    '\u670d\u52d9\u8cea\u91cf': '服務品質',
    '\u7a0b\u5f0f\u78bc\u8cea\u91cf': '程式碼品質',
}
TERM_RE = re.compile('|'.join(map(re.escape, sorted(TERMS, key=len, reverse=True))))
# Preserve legitimate domain wording rather than blindly replacing shared words.
PROTECTED = ('物理質量', '原子質量', '粒子質量', '電子質量', '分子質量', '質量守恆', '資產配置')


def convert_run(match: re.Match) -> str:
    text = match.group()
    saved = {}
    for index, phrase in enumerate(PROTECTED):
        if phrase in text:
            key = f'__ZHTW_KEEP_{index}__'
            saved[key] = phrase
            text = text.replace(phrase, key)
    text = CONVERTER.convert(text).replace('臺灣', '台灣')
    text = re.sub(r'(?<!演)算法', '演算法', text)
    text = TERM_RE.sub(lambda m: TERMS[m.group()], text)
    for key, phrase in saved.items():
        text = text.replace(key, phrase)
    return text


def normalize(text: str) -> str:
    result, start = [], 0
    for url in URL.finditer(text):
        result.append(HAN.sub(convert_run, text[start:url.start()]))
        result.append(url.group())
        start = url.end()
    result.append(HAN.sub(convert_run, text[start:]))
    return ''.join(result)


def paths(root: Path):
    for name in ('README.md', 'AGENTS.md', 'PUBLISHING.md', 'index.html'):
        path = root / name
        if path.exists():
            yield path
    for directory in ('content', 'templates', 'assets'):
        for path in sorted((root / directory).rglob('*')):
            if path.is_file() and path.suffix in ('.md', '.json', '.js', '.html', '.css', '.svg'):
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fix', action='store_true', help='Apply language corrections only')
    args = parser.parse_args()
    changed, checked = [], 0
    for path in paths(ROOT):
        checked += 1
        before = path.read_text(encoding='utf-8')
        after = normalize(before)
        if before == after:
            continue
        name = str(path.relative_to(ROOT))
        changed.append(name)
        if args.fix:
            path.write_text(after, encoding='utf-8')
            print(f'Corrected: {name}')
        else:
            print(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name, tofile=f'{name} (zh-TW)')), file=sys.stderr)
    if changed and not args.fix:
        print(f'Locale check FAILED: {len(changed)} file(s). Use Taiwanese Traditional Chinese.', file=sys.stderr)
        return 1
    print(f'Locale check OK: {checked} files checked; {len(changed)} corrected.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
