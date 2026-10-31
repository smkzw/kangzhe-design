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

Rule pages (03 COPY-09: criteria, permitted and prohibited medication, visit windows, dosing and stopping rules,
endpoint, SAE and AESI definitions, SoA) also take --source <protocol text>: every clause, row and cell of the data
must then be found word for word in the protocol (spaces and full/half-width forms ignored), so a summary cannot pass
as the original. The receipt records the result; tools/check_kz_project.py reports rule pages without it.

    python3 "$KZ_DIR/tools/protocol_lists.py" protocol.docx --from 排除标准 --key exclusion > excl.json
    python3 "$KZ_DIR/tools/kz_layout.py" render criteria excl.json --track pptx --title 排除标准 \
            --out <project>/kz_fragments --source protocol.docx

Criteria come from the protocol .docx through tools/protocol_lists.py, not from a text export: Word keeps the
criterion numbers and the sub-item levels in its numbering, which a txt/md conversion drops. With a .docx --source the
receipt also records whether item n is protocol item n with the same sub-items.
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
        if text.count(s) >= need: continue
        # a long criterion may be broken at its clause ends across columns (patterns/clinical.py): its clauses must
        # then all appear, in order
        parts = [c for c in re.findall(r'[^；。]+[；。]?', s) if c]
        if need == 1 and len(parts) > 1:
            at = 0
            for c in parts:
                at = text.find(c, at)
                if at < 0: break
                at += len(c)
            if at >= 0: continue
        out.append(w)
    return list(dict.fromkeys(out))

def ranges(cols):
    """Criteria flow columns → [[{key, first, last}]] (clause numbers per column, 1-based inclusive); an SoA visit
    range [a, b) → {'first_visit', 'last_visit'} (1-based inclusive), the same convention."""
    if cols and len(cols) == 2 and all(isinstance(c, int) for c in cols): return {'first_visit': cols[0] + 1, 'last_visit': cols[1]}
    if not cols or not isinstance(cols[0], list): return cols
    def last(s):
        it = s['items'][-1]
        return it['n'] if isinstance(it, dict) and 'n' in it else s['start'] + len(s['items']) - 1
    return [[{'key': s['key'], 'first': s['start'], 'last': last(s)} for s in col] for col in cols]

RULE_PATTERNS = ('criteria', 'soa')  # always original clauses

def normal(s):
    """Comparison form for source fidelity: NFKC (full/half width), no whitespace."""
    import unicodedata
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))

def not_in_source(want, source_text):
    """Data strings that do not occur word for word in the source (a line of the protocol may hold several, and a
    long criterion may be split by the data author at its own clause ends, which still matches clause by clause)."""
    src = normal(source_text); out = []
    for w in want:
        n = normal(w)
        if len(n) < 4 or n in src: continue
        parts = [c for c in re.findall(r'[^；;。]+[；;。]?', n) if len(c.strip('；;。')) >= 4]
        if len(parts) > 1 and all(c.rstrip('；;。') in src for c in parts): continue
        out.append(w)
    return out

def numbering_findings(data, docx):
    """Criteria data against the protocol's numbered lists (tools/protocol_lists.py): item n must be protocol item n,
    a stem keeps its sub-items as sub-items, nothing merged, promoted, dropped or renumbered (03 COPY-09)."""
    import protocol_lists as PL
    _, blocks = PL.lists(docx); out = []
    trim = lambda t: normal(T.plain(t)).rstrip('；;。.，,')
    for key in ('inclusion', 'exclusion'):
        items = data.get(key)
        if not items: continue
        want = [(it if isinstance(it, str) else it['text'], [] if isinstance(it, str) else it.get('items', [])) for it in items]
        b = next((b for b in blocks if b['items'] and trim(b['items'][0]['text']) == trim(want[0][0])), None)
        if b is None:
            out.append({'key': key, 'n': 1, 'problem': '第 1 条不是方案里任何一个编号列表的第 1 条（引导语被删、子项被并入或顺序改动）'}); continue
        src = [(it['text'], [c['text'] for c in it['items']]) for it in b['items']]
        for n, ((t, kids), s_) in enumerate(zip(want, src), 1):
            st, skids = s_
            if trim(t) != trim(st): out.append({'key': key, 'n': n, 'problem': f'与方案第 {n} 条不同：方案为“{st[:24]}”'}); break
            if [trim(k) for k in kids] != [trim(k) for k in skids]:
                out.append({'key': key, 'n': n, 'problem': f'子项与方案不同：方案有 {len(skids)} 个子项，数据有 {len(kids)} 个'}); break
        else:
            if len(want) != len(src): out.append({'key': key, 'n': min(len(want), len(src)) + 1, 'problem': f'方案该列表有 {len(src)} 条，数据有 {len(want)} 条'})
    return out

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
    numbering = []
    if a.source:
        sp = Path(a.source); want = source_strings(data); docx = sp.suffix.lower() == '.docx'
        if docx:
            import protocol_lists as PL
            stext = PL.docx_text(sp)
        else: stext = sp.read_text(encoding='utf-8')
        bad = not_in_source(want, stext)
        rec['source_check'] = {'source': str(sp.resolve()), 'source_sha256': hashlib.sha256(sp.read_bytes()).hexdigest(),
                               'checked': len(want), 'not_in_source': bad}
        if a.pattern == 'criteria':
            # numbers and levels exist only in the Word file; a text export keeps the words and loses both
            numbering = numbering_findings(data, sp) if docx else []
            rec['source_check']['numbering'] = {'checked': docx, 'mismatch': numbering}
    rec['rule'] = a.pattern in RULE_PATTERNS or bool(a.source)
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
    bad = rec.get('source_check', {}).get('not_in_source', [])
    for s in bad: print(f'  not word for word in the source (03 COPY-09: rule text is not summarised): {s[:60]}', file=sys.stderr)
    for m in numbering: print(f'  {m["key"]} 第 {m["n"]} 条编号或层级与方案不符：{m["problem"]}；用 tools/protocol_lists.py 从 docx 取数据', file=sys.stderr)
    if a.pattern == 'criteria' and a.source and not rec['source_check']['numbering']['checked']:
        print('  note: numbering not checked — pass the protocol .docx as --source (a text export drops Word numbering and sub-item levels)', file=sys.stderr)
    return 1 if over or missing or bad or numbering else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list'); l.add_argument('--json', action='store_true')
    e = sub.add_parser('example'); e.add_argument('pattern')
    r = sub.add_parser('render'); r.add_argument('pattern'); r.add_argument('data')
    r.add_argument('--track', choices=['pptx', 'html'], required=True); r.add_argument('--title', required=True)
    r.add_argument('--out', required=True); r.add_argument('--first', type=int, default=1); r.add_argument('--total', type=int)
    r.add_argument('--background', default='../images/body_quiet.jpg'); r.add_argument('--logo', default='../images/logo.png')
    r.add_argument('--source', help='protocol .docx (preferred: numbering and sub-item levels are checked too) or text: rule data must occur in it word for word (03 COPY-09)')
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
