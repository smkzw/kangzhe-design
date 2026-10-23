#!/usr/bin/env python3
"""Build the installable skill directory (dist/kangzhe-design) and its PACKAGE_MANIFEST.json.

Maintenance and history material stays in the repository only: review/, agent/, docs/history/, tests/,
examples/validation/. Install the produced directory as one skill (INSTALL.md).
"""
from pathlib import Path
import argparse, hashlib, json, shutil
R = Path(__file__).resolve().parents[1]
EXCLUDE = ('.git/', 'dist/', 'review/', 'agent/', 'docs/history/', 'tests/', 'examples/validation/')
EXCLUDE_NAMES = {'.DS_Store', '__pycache__'}

def included(rel):
    return not rel.startswith(EXCLUDE) and not (set(Path(rel).parts) & EXCLUDE_NAMES) and not rel.endswith('.pyc')

def build(out):
    files = sorted(p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and included(p.relative_to(R).as_posix()))
    target = out / 'kangzhe-design'
    if target.exists():
        shutil.rmtree(target)
    entries = []
    for rel in files:
        if rel == 'PACKAGE_MANIFEST.json':
            continue
        dst = target / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(R / rel, dst)
        data = (R / rel).read_bytes()
        entries.append({'path': rel, 'bytes': len(data), 'sha256': 'sha256:' + hashlib.sha256(data).hexdigest()})
    manifest = {'version': (R / 'VERSION').read_text().strip(), 'revision': (R / 'REVISION').read_text().strip(),
                'scope': 'installable skill content; maintenance material (review/, agent/, docs/history/, tests/, examples/validation/) excluded',
                'files': entries}
    text = json.dumps(manifest, ensure_ascii=False, indent=1) + '\n'
    (target / 'PACKAGE_MANIFEST.json').write_text(text)
    (R / 'PACKAGE_MANIFEST.json').write_text(text)
    return target, len(entries)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=R / 'dist'); a = ap.parse_args()
    target, n = build(a.out.resolve())
    print(f'{target} ({n} files)')
