#!/usr/bin/env python3
"""10 G-KZ: Kangzhe checks on a ppt-master project before export (and on the exported PPTX after it).

    python3 "$KZ_DIR/tools/check_kz_project.py" <project> [--plan page-plan.json] [--receipts <dir>] [--pptx out.pptx] [--json]

Reads <project>/svg_output/*.svg, the template receipts (tools/kz_layout.py writes kz-layout-receipt.json; default
<project>/kz_fragments) and, when given, the page-plan and the exported PPTX. Errors (exit 1):
  PLAN            tools/qc_plan.py errors, including the IMG-07 image-capability gate
  PLATE           a generated background without a passing tools/quiet_plate.py receipt (04 IMG-08)
  EDGE-BAR        coloured edge bars on cards (02 LG-02, tools/check_edge_bars.py)
  FONT-FLOOR      text below tokens.type_px.reference (03 TYPE-01)
  VERBATIM        a template page that dropped source text, or overflowed (03 COPY-09)
  HIGHLIGHT       sentinel-coloured runs left in the PPTX (run tools/bind_highlight_pptx.py)
Warnings:
  SMALL-TEXT      more than 15 % of a page's characters under the 12 pt content floor (only axes, legends, sources, n= may be small)
  ROTATION        the same template used more than twice in a row (one list paged across pages is one use),
                  or a deck of six or more template pages using fewer than three templates (13 BODY-02)
  EMPHASIS        a text-heavy page with no bold, dark-red, underline or highlight run (03 COPY-04/06)
  PLAIN-TEXT      a text-heavy page with no icon, chart, table or drawn diagram (13 BODY-02)
"""
from pathlib import Path
import argparse, json, re, sys, zipfile
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
FLOOR = TOK['type_px']['reference'] - 0.05; CONTENT = TOK['type_px']['secondary'] - 0.05
MARK = TOK['layout']['templates']['highlight_marker'].lstrip('#').upper()
RISK = TOK['colors']['risk'].upper().lstrip('#'); FOCUS = TOK['colors']['focus'].upper().lstrip('#')

def _style(el):
    return {k.strip(): v.strip() for k, v in (kv.split(':', 1) for kv in (el.get('style') or '').split(';') if ':' in kv)}

def _attr(el, name):
    """Presentation attribute or inline style (inline style wins, as in SVG)."""
    return _style(el).get(name, el.get(name))

def _px(v, inherited):
    if v is None: return inherited
    m = re.match(r'\s*([\d.]+)\s*(px|pt)?\s*$', str(v))
    if not m: return inherited
    return float(m.group(1)) * (4 / 3 if m.group(2) == 'pt' else 1)

def _bold(v, inherited):
    if v is None: return inherited
    return v == 'bold' or v == 'bolder' or (v.isdigit() and int(v) >= 600)

def texts(svg):
    """→ [(font_size, bold, chars, emphasis)] per run of characters: a <text> and each <tspan> inside it carry their own
    size and weight (attribute or inline style, inherited from ancestors); emphasis is per <text> and sits on its first run."""
    import xml.etree.ElementTree as E
    root = E.fromstring(svg); out = []
    def runs(el, size, bold, acc):
        size = _px(_attr(el, 'font-size'), size); bold = _bold(_attr(el, 'font-weight'), bold)
        n = len(re.sub(r'\s', '', el.text or ''))
        if n: acc.append([size, bold, n])
        for c in el:
            runs(c, size, bold, acc)
            t = len(re.sub(r'\s', '', c.tail or ''))
            if t: acc.append([size, bold, t])
    def walk(el, size, bold):
        tag = el.tag.split('}')[-1]
        if tag in ('metadata', 'defs'): return
        if tag == 'text':
            acc = []; runs(el, size, bold, acc)
            base_bold = _bold(_attr(el, 'font-weight'), bold)
            fills = ('#' + RISK, '#' + MARK, '#' + FOCUS)
            emph = any((_bold(_attr(c, 'font-weight'), base_bold) and not base_bold) or (_attr(c, 'fill') or '').upper() in fills
                       or 'underline' in (_attr(c, 'text-decoration') or '') for c in el.iter() if c is not el)
            emph = emph or (_attr(el, 'fill') or '').upper() == '#' + RISK
            for i, (sz, bd, n) in enumerate(acc): out.append((sz, bd, n, emph and i == 0))
            return
        size = _px(_attr(el, 'font-size'), size); bold = _bold(_attr(el, 'font-weight'), bold)
        for c in el: walk(c, size, bold)
    walk(root, 16, False)
    return out

def page_checks(name, svg, add):
    ts = texts(svg); total = sum(c for *_, c, _ in ts) or 1
    tiny = [s for s, b, c, e in ts if s < FLOOR and c]
    if tiny: add('error', 'FONT-FLOOR', name, f'{len(tiny)} text object(s) below {FLOOR + 0.05:g} px (smallest {min(tiny):g} px)')
    small = sum(c for s, b, c, e in ts if s < CONTENT)
    if small / total > 0.15: add('warn', 'SMALL-TEXT', name, f'{small / total:.0%} of the characters under {CONTENT + 0.05:g} px (12 pt)')
    body_chars = sum(c for s, b, c, e in ts if not b)
    data_page = 'data-pptx-replace-with' in svg  # tables and charts follow their own role contract (03 COPY-06)
    if body_chars >= 150 and not data_page and not any(e for *_, e in ts):
        add('warn', 'EMPHASIS', name, f'{body_chars} body characters and no emphasis run')
    visual = 'data-icon=' in svg or 'data-pptx-replace-with' in svg or len(re.findall(r'<(path|polygon|circle)\b', svg)) >= 6
    if body_chars >= 200 and not visual: add('warn', 'PLAIN-TEXT', name, 'text only: no icon, chart, table or diagram')

def receipt_checks(runs, add):
    """Per track: overflow and missing source text are errors, and so are pages a later render overwrote (that run's
    text is no longer all on the deck). ROTATION counts separate uses of a template in a row: one list paged across
    several pages is one use, so criteria pages 1–3 followed by kv-table never warn, but three different tables in
    a row do."""
    for track in sorted({r['track'] for r in runs}):
        rs = [r for r in runs if r['track'] == track]; seq = []
        for k, r in enumerate(rs):
            for p in r['pages']:
                if p['overflow_px'] > 0.5: add('error', 'VERBATIM', f'{track}:{p["file"]}', f'{r["pattern"]} overflows by {p["overflow_px"]} px')
                seq.append((p['n'], r['pattern'], k))
            for s in r['verbatim']['missing']: add('error', 'VERBATIM', f'{track}:{r["pattern"]}', f'source text not on any page: {s[:50]}')
            if r.get('overwritten_pages'):
                add('error', 'VERBATIM', f'{track}:{r["pattern"]}', f'pages {r["overwritten_pages"]} of this list were overwritten by a later render; render the list again')
        seq.sort(); streaks = []
        for n, pat, k in seq:  # maximal runs of consecutive pages with the same template
            if streaks and streaks[-1][-1][1] == pat and streaks[-1][-1][0] == n - 1: streaks[-1].append((n, pat, k))
            else: streaks.append([(n, pat, k)])
        for st in streaks:
            uses = len({k for *_, k in st})
            if uses > 2: add('warn', 'ROTATION', f'{track}:p{st[0][0]}–p{st[-1][0]}', f'{st[0][1]} used {uses} times in a row')
        if len(seq) >= 6 and len({p for _, p, _ in seq}) < 3: add('warn', 'ROTATION', f'{track}:deck', f'{len(seq)} template pages use only {sorted({p for _, p, _ in seq})}')

HERO_KINDS = ('cover', 'toc', 'section', 'ending')

def plate_checks(plan, project, add):
    """Every background of a generated deck needs a passing quiet_plate receipt of the right page kind, and the image
    in the project must be the plate that receipt measured (same SHA-256). Asset ids default as in kz_image_prompts."""
    import hashlib
    cap = (plan.get('image_capability') or {}).get('decision')
    if cap != 'generated': return
    rec = {}
    for f in sorted((project / 'receipts').glob('*.quiet.json')) if (project / 'receipts').exists() else []:
        d = json.loads(f.read_text(encoding='utf-8')); rec[Path(d['output']).stem] = d
    for p in plan['pages']:
        aid = (p.get('image') or {}).get('asset_id') or f'{p["id"]}-bg'
        kind = p['kind'] if p['kind'] in HERO_KINDS else 'body'
        d = rec.get(aid)
        if not d: add('error', 'PLATE', p['id'], f'generated background {aid} has no quiet_plate receipt (receipts/{aid}.quiet.json)'); continue
        if d['kind'] != kind: add('error', 'PLATE', p['id'], f'{aid} was plated as {d["kind"]} but the page is {kind}')
        if not d['passed']: add('error', 'PLATE', p['id'], f'{aid} failed the reading-zone check: {d["failures"]}')
        imgs = [f for f in (project / 'images').glob(aid + '.*')] if (project / 'images').exists() else []
        if not imgs: add('error', 'PLATE', p['id'], f'images/{aid}.* not found in the project')
        elif all(hashlib.sha256(f.read_bytes()).hexdigest() != d['output_sha256'] for f in imgs):
            add('error', 'PLATE', p['id'], f'images/{aid} is not the plate its receipt measured (SHA-256 differs)')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project', type=Path); ap.add_argument('--plan', type=Path); ap.add_argument('--receipts', type=Path)
    ap.add_argument('--pptx', type=Path); ap.add_argument('--json', action='store_true')
    a = ap.parse_args(); found = []
    def add(level, code, where, msg): found.append({'level': level, 'code': code, 'where': where, 'message': msg})
    svgs = sorted((a.project / 'svg_output').glob('*.svg'))
    if not svgs: add('error', 'PROJECT', str(a.project), 'no svg_output/*.svg')
    for f in svgs: page_checks(f.name, f.read_text(encoding='utf-8'), add)
    from check_edge_bars import scan
    for b in (b for f in svgs for b in scan(f)):
        add('error' if b['level'] == 'fail' else 'warn', 'EDGE-BAR', b['file'], f'{b["bar"]} on the {b["side"]} edge of {b["card"]} ({b["ratio"]:.0%})')
    rp = (a.receipts or a.project / 'kz_fragments') / 'kz-layout-receipt.json'
    if rp.exists(): receipt_checks(json.loads(rp.read_text(encoding='utf-8'))['runs'], add)
    if a.plan:
        plan = json.loads(a.plan.read_text(encoding='utf-8'))
        from qc_plan import validate
        for f in validate(plan):
            if f['level'] == 'error': add('error', 'PLAN', f['where'], f'{f["code"]}: {f["message"]}')
        plate_checks(plan, a.project, add)
    if a.pptx:
        z = zipfile.ZipFile(a.pptx)
        for n in sorted(z.namelist()):
            if re.match(r'ppt/slides/slide\d+\.xml$', n) and f'val="{MARK}"' in z.read(n).decode('utf-8'):
                add('error', 'HIGHLIGHT', n, 'highlight sentinel colour left; run tools/bind_highlight_pptx.py')
    errs = [x for x in found if x['level'] == 'error']
    if a.json: print(json.dumps({'pages': len(svgs), 'receipt': str(rp) if rp.exists() else None, 'findings': found}, ensure_ascii=False, indent=1))
    else:
        for x in found: print(f'{x["level"].upper():5} {x["code"]:11} {x["where"]}: {x["message"]}')
        print(f'{len(svgs)} pages, {len(errs)} error(s), {len(found) - len(errs)} warning(s); receipt: {rp if rp.exists() else "none"}')
    return 1 if errs else 0

if __name__ == '__main__':
    sys.exit(main())
