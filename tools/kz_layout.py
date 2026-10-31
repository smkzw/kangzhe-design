#!/usr/bin/env python3
"""Kangzhe template pages (13 BODY-02) from the command line: list the catalogue, show a template's example data,
render pages for PPTX (ppt-master SVG) or HTML-PPT (slide body markup).

    python3 "$KZ_DIR/tools/kz_layout.py" list [--json]
    python3 "$KZ_DIR/tools/kz_layout.py" example criteria            # path of the example data (the data contract)
    python3 "$KZ_DIR/tools/kz_layout.py" render criteria data.json --track pptx --title 入选与排除标准 \
            --out <project>/kz_fragments --first 5 --total 18
    python3 "$KZ_DIR/tools/kz_layout.py" render criteria data.json --track html --title 入选与排除标准 --out frag/

PPTX writes full pages (康哲 chrome + template body) as page_NN.svg into --out, never into svg_output/: the
Executor reviews each page and places it into svg_output/ itself (ppt-master: page SVGs are the agent's). HTML writes
slide_NN.html (the .kz-body content for data-preset="kzl") and charts.json (KZCharts payloads keyed by chart id).
Every run appends to <out>/kz-layout-receipt.json: pages, overflow, page ranges and the verbatim check
(every source clause, row and cell must appear in the rendered pages; 03 COPY-09). tools/check_kz_project.py reads it.
Exit 1 when a page overflows or a source string is missing.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
import kz_layouts as K  # noqa: E402
from kz_layouts import text as T  # noqa: E402

EXAMPLES = R / 'examples/templates'
VERBATIM_KEYS = ('inclusion', 'exclusion', 'rows', 'items', 'allowed', 'prohibited', 'footnotes')

def example_files():
    sys.path.insert(0, str(EXAMPLES))
    from pages import PAGES
    out = {}
    for name, f, *_ in PAGES: out.setdefault(name, []).append(str(EXAMPLES / f))
    return out

def source_strings(data):
    """Leaf strings under the list keys whose text must survive unshortened (clauses, table rows, footnotes)."""
    out = []
    def walk(v, keep):
        if isinstance(v, str):
            if keep and len(T.plain(v).strip()) >= 2: out.append(T.plain(v))
        elif isinstance(v, dict):
            for k, x in v.items(): walk(x, keep or k in VERBATIM_KEYS) if k not in ('tone', 'icon', 'marker', 'align', 'mark') else None
        elif isinstance(v, list):
            for x in v: walk(x, keep)
    walk(data, False)
    return out

def squash(s):
    return re.sub(r'\s+', '', s)

def page_text(markup, track):
    if track == 'pptx':  # only what PowerPoint will show: <text> runs (metadata JSON and ids are not text)
        parts = re.findall(r'<text\b[^>]*>(.*?)</text>', markup, flags=re.S)
        return squash(''.join(re.sub(r'<[^>]+>', '', p) for p in parts))
    return squash(re.sub(r'<[^>]+>', '', markup))

def payload_text(v):
    """String leaves of a KZCharts payload, as the chart will print them (no JSON escaping)."""
    if isinstance(v, str): return v
    if isinstance(v, dict): return ''.join(payload_text(x) for x in v.values())
    if isinstance(v, list): return ''.join(payload_text(x) for x in v)
    return ''

def missing_strings(want, text):
    """A source string is present only if the pages show it at least as often as the source strings that contain
    it: a repeated clause (the same washout rule on three rows) must appear three times, not once."""
    sq = [squash(w) for w in want]; out = []
    for w, s in zip(want, sq):
        need = sum(1 for t in sq if s in t)
        if text.count(s) < need: out.append(w)
    return list(dict.fromkeys(out))

def ranges(cols):
    """Criteria flow columns → [[{key, first, last}]] (clause numbers per column, 1-based inclusive); an SoA visit
    range [a, b) → {'first_visit', 'last_visit'} (1-based inclusive), the same convention."""
    if cols and len(cols) == 2 and all(isinstance(c, int) for c in cols): return {'first_visit': cols[0] + 1, 'last_visit': cols[1]}
    if not cols or not isinstance(cols[0], list): return cols
    return [[{'key': s['key'], 'first': s['start'], 'last': s['start'] + len(s['items']) - 1} for s in col] for col in cols]

def unescape(s):
    import html
    return html.unescape(s)

def render_cmd(a):
    from kz_layouts.page import svg_page
    data = json.loads(Path(a.data).read_text(encoding='utf-8'))
    pages = K.render(a.pattern, data, 'pptx' if a.track == 'pptx' else 'html')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    total = a.total or (a.first + len(pages) - 1)
    files, texts, charts = [], [], {}
    for i, p in enumerate(pages):
        n = a.first + i
        if a.track == 'pptx':
            body = svg_page(a.title, p['svg'], n, total, background=a.background, logo=a.logo)
            f = out / f'page_{n:02d}.svg'
        else:
            body = p['html']; charts.update(p['charts']); f = out / f'slide_{n:02d}.html'
        f.write_text(body, encoding='utf-8'); files.append(f.name)
        # HTML charts draw their labels from the KZCharts payload, so the payload counts as page text
        texts.append(unescape(page_text(body, a.track)) + (squash(payload_text(p['charts'])) if a.track == 'html' else ''))
    if charts: (out / 'charts.json').write_text(json.dumps(charts, ensure_ascii=False, indent=1), encoding='utf-8')
    allt = ''.join(texts)
    missing = missing_strings(source_strings(data), allt)
    rec = {'pattern': a.pattern, 'title': a.title, 'track': a.track, 'data': str(Path(a.data).resolve()),
           'data_sha256': hashlib.sha256(Path(a.data).read_bytes()).hexdigest(),
           'pages': [{'n': a.first + i, 'file': f, 'overflow_px': p['overflow'], 'page_of': p['data'].get('page_of'),
                      'first_row': (p['data']['row_start'] + 1) if p['data'].get('row_start') is not None else None, 'rows': len(p['data']['rows']) if isinstance(p['data'].get('rows'), list) else None,
                      'cols': ranges(p['data'].get('cols'))} for i, (p, f) in enumerate(zip(pages, files))],
           'verbatim': {'checked': len(source_strings(data)), 'missing': missing}}
    rp = out / 'kz-layout-receipt.json'
    log = json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {'runs': []}
    # a new run replaces the pages it writes; an older run that loses some of its pages keeps the rest and records
    # which ones were overwritten (its source text is then no longer all on the deck: check_kz_project reports it)
    mine = {p['n'] for p in rec['pages']}; keep = []
    for r in log['runs']:
        if r['track'] == a.track and {p['n'] for p in r['pages']} & mine:
            lost = sorted({p['n'] for p in r['pages']} & mine)
            r = {**r, 'pages': [p for p in r['pages'] if p['n'] not in mine], 'overwritten_pages': sorted(set(r.get('overwritten_pages', [])) | set(lost))}
            if not r['pages']: continue  # fully replaced
        keep.append(r)
    log['runs'] = keep + [rec]
    rp.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding='utf-8')
    over = [p for p in rec['pages'] if p['overflow_px'] > 0.5]
    print(f'{a.pattern}: {len(pages)} page(s) → {out}  ' + ' '.join(files))
    for p in over: print(f'  page {p["n"]}: overflow {p["overflow_px"]} px — shorten nothing; split or choose another template', file=sys.stderr)
    for s in missing: print(f'  missing from the rendered pages: {s[:60]}', file=sys.stderr)
    return 1 if over or missing else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list'); l.add_argument('--json', action='store_true')
    e = sub.add_parser('example'); e.add_argument('pattern')
    r = sub.add_parser('render'); r.add_argument('pattern'); r.add_argument('data')
    r.add_argument('--track', choices=['pptx', 'html'], required=True); r.add_argument('--title', required=True)
    r.add_argument('--out', required=True); r.add_argument('--first', type=int, default=1); r.add_argument('--total', type=int)
    r.add_argument('--background', default='../images/body_quiet.jpg'); r.add_argument('--logo', default='../images/logo.png')
    a = ap.parse_args()
    if a.cmd == 'list':
        cat = K.catalog(); ex = example_files()
        for c in cat: c['examples'] = ex.get(c['name'], [])
        if a.json: print(json.dumps(cat, ensure_ascii=False, indent=1)); return 0
        for c in cat: print(f'{c["name"]:16} {c["scene"]:6} 密度{c["density"]:3} {c["title"]}\n{"":16} {c["use"]}')
        print(f'\n{len(cat)} templates')
        return 0
    if a.cmd == 'example':
        ex = example_files().get(a.pattern)
        if not ex: print(f'unknown template: {a.pattern}', file=sys.stderr); return 2
        print('\n'.join(ex)); return 0
    return render_cmd(a)

if __name__ == '__main__':
    sys.exit(main())
