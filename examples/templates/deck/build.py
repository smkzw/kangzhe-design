#!/usr/bin/env python3
"""HTML-PPT template deck (13 BODY-02): every registered template page, rendered from examples/templates/*.json by
tools/kz_layouts, inside the reference chrome (examples/reference/htmlppt/build.py: body, write_deck; deck.css;
deck.js). The PPTX side of the same pages is examples/templates/pptx/build.py.
Run:  python examples/templates/deck/build.py
"""
from pathlib import Path
import importlib.util, json, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from kz_layouts import render  # noqa: E402
spec = importlib.util.spec_from_file_location('kz_ref_build', HERE.parents[1] / 'reference/htmlppt/build.py')
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
ref.A = '../../reference/assets/'
BASE = '../../reference/htmlppt/'
sys.path.insert(0, str(HERE.parent)); from pages import PAGES  # noqa: E402  (template, data file, title, notes)

def build():
    slides, charts = [], {}
    rendered = []
    for name, data_file, title, notes in PAGES:
        data = json.loads((HERE.parent / data_file).read_text(encoding='utf-8'))
        for p in render(name, data, 'html'): rendered.append((title, p, notes)); charts.update(p['charts'])
    for n, (title, p, notes) in enumerate(rendered, 1):
        slides.append(ref.body(n, len(rendered), title, 'kzl', p['html'], notes))
    ref.write_deck(slides, json.dumps(charts, ensure_ascii=False), HERE / 'index.html', '模板页组', base=BASE)

if __name__ == '__main__':
    build()
