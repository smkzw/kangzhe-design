#!/usr/bin/env python3
"""PPTX template pages (13 BODY-02): the same pages as ../deck, written as ppt-master SVG into a project.

    python3 <ppt-master>/scripts/project_manager.py init kz_templates --format ppt169
    python examples/templates/pptx/build.py <project> [--preview <dir>]
    cp assets/icons/kangzhe/*.svg <project>/icons/kangzhe/      # <use data-icon="kangzhe/…"> resolves here
    cp assets/backgrounds/body-quiet.jpg <project>/images/body_quiet.jpg; cp assets/logo_bot.png <project>/images/logo.png
    python3 <ppt-master>/scripts/stamp_native_fallbacks.py <project> --write      # tables and charts
    python3 <ppt-master>/scripts/svg_quality_checker.py <project> --canonical-authoring --stage final --quick-generate --json
    python3 <ppt-master>/scripts/svg_to_pptx.py <project> --quick-generate --no-notes --native-charts-and-tables -o <out>.pptx
    python tools/bind_highlight_pptx.py <out>.pptx <out>.pptx          # ==highlight== runs → native highlight
--preview writes browser previews (icons inlined, absolute image paths) for screenshots.
"""
from pathlib import Path
import argparse, json, shutil, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(HERE.parent))
from kz_layouts import render  # noqa: E402
from kz_layouts.page import svg_page, inline_icons  # noqa: E402
from pages import PAGES  # noqa: E402

def build(project, preview=None):
    out = Path(project) / 'svg_output'; out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('*.svg'): f.unlink()
    (Path(project) / 'icons/kangzhe').mkdir(parents=True, exist_ok=True)
    for f in (ROOT / 'assets/icons/kangzhe').glob('*.svg'): shutil.copy(f, Path(project) / 'icons/kangzhe' / f.name)
    (Path(project) / 'images').mkdir(exist_ok=True)
    shutil.copy(ROOT / 'assets/backgrounds/body-quiet.jpg', Path(project) / 'images/body_quiet.jpg')
    shutil.copy(ROOT / 'assets/logo_bot.png', Path(project) / 'images/logo.png')
    pages = []
    for name, data_file, title, notes in PAGES:
        data = json.loads((HERE.parent / data_file).read_text(encoding='utf-8'))
        pages += [(title, p) for p in render(name, data, 'pptx')]
    for n, (title, p) in enumerate(pages, 1):
        s = svg_page(title, p['svg'], n, len(pages), background='../images/body_quiet.jpg')
        (out / f'slide_{n:02d}.svg').write_text(s, encoding='utf-8')
        if preview:
            Path(preview).mkdir(parents=True, exist_ok=True)
            img = str((Path(project) / 'images').resolve()) + '/'
            (Path(preview) / f'page_{n:02d}.svg').write_text(inline_icons(s).replace('../images/', img), encoding='utf-8')
        if p['overflow'] > 0.5: print(f'  page {n}: overflow {p["overflow"]} px', file=sys.stderr)
    print('wrote', len(pages), 'pages to', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--preview')
    a = ap.parse_args(); build(a.project, a.preview)
