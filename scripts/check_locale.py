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
# Character/variant conversion only. Use reviewed, idempotent wording below;
# blindly applying s2twp to already-Taiwanese prose can duplicate characters.
CONVERTER = OpenCC('s2tw')
HAN = re.compile(r'[\u3400-\u9fff]+')
URL = re.compile(r'https?://[^\s<>\]\)\"\x27]+')
# Keys use escapes so rule definitions themselves contain no simplified text.
TERMS = {
    '\u751f\u547d\u5468\u671f': '生命週期',
    '\u5468\u671f': '週期',
    '\u8edf\u4ef6': '軟體',
    '\u786c\u4ef6': '硬體',
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
    '\u64cd\u4f5c\u7cfb\u7d71': '作業系統',
    '\u9f20\u6a19': '滑鼠',
    '\u6253\u5370': '列印',
    '\u5c4f\u5e55': '螢幕',
    '\u96c6\u7fa4': '叢集',
    '\u512a\u5316': '最佳化',
    '\u904b\u884c': '執行',
    '\u93c8\u63a5': '連結',
    '\u7528\u6236': '使用者',
    '\u82af\u7247': '晶片',
    '\u6a21\u584a': '模組',
    '\u6fc0\u5149': '雷射',
    '\u5e36\u5bec': '頻寬',
    '\u56fa\u4ef6': '韌體',
    '\u4e92\u806f\u7db2': '網際網路',
    '\u6a21\u578b\u652f\u6301': '模型支援',
    '\u9589\u74b0': '閉迴路',
    '\u53ef\u80fd\u5148\u843d\u5730': '可能率先應用',
    '\u98a8\u96aa\u4e0a\u5831': '風險通報',
    '\u63aa\u65bd\u843d\u5730': '措施實施',
    '\u914d\u7f6e\u6587\u4ef6': '設定檔',
    '\u914d\u7f6e\u6a94': '設定檔',
    '\u8cec\u865f': '帳號',
    '\u6578\u64da\u8cea\u91cf': '資料品質',
    '\u670d\u52d9\u8cea\u91cf': '服務品質',
    '\u7a0b\u5f0f\u78bc\u8cea\u91cf': '程式碼品質',
}
TERM_RE = re.compile('|'.join(map(re.escape, sorted(TERMS, key=len, reverse=True))))
# Protect ambiguous characters in already-correct Traditional Chinese context.
PROTECTED = (
    '物理質量', '原子質量', '粒子質量', '電子質量', '分子質量', '質量守恆',
    '資產配置', '股票代碼', '交易代碼', '證券代碼',
    '干擾', '干涉', '干預', '若干', '干係', '相干', '不相干',
    '皇后', '王后', '太后', '后羿', '公里', '里程', '里長', '里民', '阿里巴巴',
    '只以', '只看', '只是', '只要', '只會', '只有', '只用', '只能', '不只',
    '發布', '公布', '宣布', '分布', '散布', '遍布', '布局', '回流',
)


def convert_run(match: re.Match) -> str:
    text = match.group()
    saved = {}
    for index, phrase in enumerate(sorted(PROTECTED, key=len, reverse=True)):
        if phrase in text:
            key = f'__ZHTW_KEEP_{index}__'
            saved[key] = phrase
            text = text.replace(phrase, key)
    text = CONVERTER.convert(text).replace('臺', '台')
    for old, new in (('隻以', '只以'), ('隻看', '只看'), ('迴流', '回流'),
                     ('發佈', '發布'), ('公佈', '公布'), ('宣佈', '宣布'),
                     ('分佈', '分布'), ('散佈', '散布'), ('遍佈', '遍布'), ('佈局', '布局')):
        text = text.replace(old, new)
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
