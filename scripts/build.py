#!/usr/bin/env python3
"""Copy only public site assets and indexed articles into _site/."""
from pathlib import Path
import json
import shutil
from validate import validate

ROOT = Path(__file__).resolve().parents[1]


def build() -> None:
    stats = validate(ROOT)
    output = ROOT / '_site'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    for name in ('index.html', '.nojekyll'):
        shutil.copy2(ROOT / name, output / name)
    shutil.copytree(ROOT / 'assets', output / 'assets')
    (output / 'content').mkdir()
    shutil.copy2(ROOT / 'content/index.json', output / 'content/index.json')
    manifest = json.loads((ROOT / 'content/index.json').read_text(encoding='utf-8'))
    for edition in manifest['editions']:
        target = output / edition['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / edition['path'], target)
    print(f'Built _site with {stats["editions"]} editions and {stats["stories"]} stories.')


if __name__ == '__main__':
    build()
