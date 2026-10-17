#!/usr/bin/env python3
"""Validate the public archive structure. This is NOT a fact-checking engine."""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ['① AI / LLM / Agents / Developer Tools', '② Technology Products / Hardware / Networking', '③ Taiwan Stocks / U.S. Stocks / ETFs / Markets', '④ Major Global Technology / Business News']
FIELDS = ['摘要', '為什麼重要', '二階影響', '我的判讀']
ID_RE = re.compile(r'^\d{4}-\d{2}-\d{2}(?:-v[1-9]\d*)?$')
LINK_RE = re.compile(r'\[[^\]]+\]\((https?://[^\s)]+)\)')


def validate(root: Path = ROOT) -> dict:
    errors: list[str] = []
    try:
        manifest = json.loads((root / 'content/index.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read content/index.json: {exc}') from exc
    if manifest.get('timezone') != 'Asia/Taipei':
        errors.append('timezone must be Asia/Taipei')
    editions = manifest.get('editions', [])
    if not isinstance(editions, list) or not editions:
        raise ValueError('editions must be a non-empty list')
    ids: set[str] = set()
    dates: set[str] = set()
    paths: set[str] = set()
    count = 0
    for edition in editions:
        eid = edition.get('id', '')
        prefix = eid or '<missing id>'
        if not ID_RE.fullmatch(eid):
            errors.append(f'{prefix}: invalid edition id')
        if eid in ids:
            errors.append(f'{prefix}: duplicate id')
        ids.add(eid)
        date = edition.get('date', '')
        try:
            parsed_date = dt.date.fromisoformat(date)
        except (TypeError, ValueError):
            errors.append(f'{prefix}: invalid date')
            continue
        if not eid.startswith(date):
            errors.append(f'{prefix}: id/date mismatch')
        dates.add(date)
        expected = f'content/{parsed_date:%Y/%m}/{eid}.md'
        path = edition.get('path')
        if path != expected:
            errors.append(f'{prefix}: expected path {expected}')
            continue
        if path in paths:
            errors.append(f'{prefix}: duplicate content path')
        paths.add(path)
        if not edition.get('title') or not edition.get('edition'):
            errors.append(f'{prefix}: title and edition label are required')
        status = edition.get('status')
        if status not in ('unverified_archive', 'sourced'):
            errors.append(f'{prefix}: invalid source status')
        try:
            text = (root / path).read_text(encoding='utf-8')
        except OSError as exc:
            errors.append(f'{prefix}: missing content: {exc}')
            continue
        if '' in text or re.search(r'\bturn\d+(?:search|news|view|image)\d+\b', text):
            errors.append(f'{prefix}: unresolved ChatGPT citation/widget')
        sections: dict[str, str] = {}
        blocks = re.split(r'^## ', text, flags=re.M)
        for block in blocks[1:]:
            name, _, body = block.partition('\n')
            if name.strip() in sections:
                errors.append(f'{prefix}: duplicate section {name.strip()}')
            sections[name.strip()] = body
        required = ['今日最重要的 3 件事', *CATEGORIES, 'Today', 'This Week', 'Worth Tracking']
        for name in required:
            if not sections.get(name, '').strip():
                errors.append(f'{prefix}: missing/empty section {name}')
        highlights = re.findall(r'^### (\d+)\. ', sections.get(required[0], ''), flags=re.M)
        if highlights != ['1', '2', '3']:
            errors.append(f'{prefix}: executive summary must have items 1, 2, 3')
        for category in CATEGORIES:
            body = sections.get(category, '')
            stories = re.findall(r'^### (\d+)\. ([^\n]+)\n(.*?)(?=^### |\Z)', body, flags=re.M | re.S)
            if [s[0] for s in stories] != ['1', '2', '3', '4', '5']:
                errors.append(f'{prefix}: {category} must contain exactly 1–5')
            for number, title, content in stories:
                count += 1
                for field in FIELDS:
                    if f'**{field}｜**' not in content:
                        errors.append(f'{prefix}/{category[0]}-{number}: missing {field}')
                if status == 'sourced':
                    urls = LINK_RE.findall(content)
                    valid = [u for u in urls if urlparse(u).netloc and 'example.com' not in urlparse(u).netloc]
                    if not valid:
                        errors.append(f'{prefix}/{category[0]}-{number}: new stories require genuine source URL(s)')
        if status == 'unverified_archive' and '未重新查核' not in text and '尚未重新查核' not in text:
            errors.append(f'{prefix}: archive warning required')
    missing = manifest.get('missingDates', [])
    if len(missing) != len(set(missing)):
        errors.append('duplicate missingDates')
    for date in missing:
        try:
            dt.date.fromisoformat(date)
        except (TypeError, ValueError):
            errors.append(f'invalid missing date {date}')
        if date in dates:
            errors.append(f'{date}: cannot be both published and missing')
    if errors:
        raise ValueError('\n'.join(errors))
    return {'editions': len(editions), 'dates': len(dates), 'stories': count, 'missing': len(missing)}


if __name__ == '__main__':
    try:
        result = validate()
    except ValueError as exc:
        print(f'Archive validation FAILED:\n{exc}', file=sys.stderr)
        sys.exit(1)
    print('Archive validation OK: ' + ', '.join(f'{k}={v}' for k, v in result.items()))
    print('Structure/source-presence checks only; historical facts have NOT been independently verified.')
