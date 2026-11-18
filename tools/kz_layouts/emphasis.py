"""03 COPY-04 inline-emphasis audit: one set of rules for template data, ppt-master SVG pages and (in
runtime/kz-layout-qc.js, KZLayoutQC.inspectEmphasis) HTML pages. Budgets are tokens.emphasis.budget.

A unit is a card (template Card, a top-level SVG group, an HTML card) or a free paragraph. Findings:
  EMPHASIS-MISSING  a unit with at least text_heavy_chars characters of running text and no emphasis group
  EMPHASIS-DENSE    a unit with more than unit_max groups (a list card: half its items if more; a free paragraph:
                    paragraph_max), or a bullet with more than item_max
  EMPHASIS-LONG     one group wider than run_chars_max (CJK 1, letters and digits 0.5), or over run_share_max of a
                    sentence of at least share_min_units (a whole sentence in bold or red is no emphasis at all)
  EMPHASIS-STACK    more than stack_max marks on one group, or dark red and highlight together
  EMPHASIS-RED / EMPHASIS-MARK / EMPHASIS-ULINE   a page over page_risk_max red groups, page_highlight_max
                    highlights or page_underline_max underlines
All are warnings: the reviewer decides, and a unit with no sensible emphasis is recorded as not_applicable.
"""
import json, re
from pathlib import Path
from . import text as T

R = Path(__file__).resolve().parents[2]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
E = TOK['emphasis']; B = E['budget']

def _n(s):
    return len(re.sub(r'\s', '', s))

def _w(s):
    """Width units: a CJK or full-width character is 1, a letter, digit or half-width sign 0.5."""
    import unicodedata
    return sum(1 if unicodedata.east_asian_width(c) in 'WF' else 0.5 for c in s if not c.isspace())

def audit(units):
    """units: [{'id', 'kind': 'card'|'paragraph', 'paras': [[(text, styles), …] per paragraph], 'items': [indices of
    paras that are bullets]}] → (findings [(code, where, message)], stats)."""
    out, page = [], {'risk': 0, 'highlight': 0, 'underline': 0, 'groups': 0}
    for u in units:
        groups_u, chars = 0, 0
        for pi, runs in enumerate(u['paras']):
            plain = ''.join(t for t, _ in runs); chars += _n(plain)
            gs = _groups(runs); groups_u += len(gs)
            if pi in u.get('items', ()) and len(gs) > B['item_max']:
                out.append(('EMPHASIS-DENSE', u['id'], f'一条要点里有 {len(gs)} 组强调（上限 {B["item_max"]}）：{plain[:24]}'))
            for t, st in gs:
                k, whole = _w(t), _w(plain)
                if k > B['run_chars_max'] or (whole >= B['share_min_units'] and k > B['run_share_max'] * whole):
                    out.append(('EMPHASIS-LONG', u['id'], f'强调“{t[:20]}”{k:g} 字宽，占句子 {k / max(1, whole):.0%}：只标关键词或关键数字'))
                marks = (st - ({'bold'} if 'risk' in st else set()))
                if len(marks) > B['stack_max'] or {'risk', 'highlight'} <= st:
                    out.append(('EMPHASIS-STACK', u['id'], f'“{t[:20]}”叠了 {"、".join(sorted(marks))}'))
                for k2 in ('risk', 'highlight', 'underline'):
                    if k2 in st: page[k2] += 1
        if u['kind'] == 'heading': continue   # bold lines (conclusion bands, item titles) count toward the page totals only
        page['groups'] += groups_u
        limit = max(B['unit_max'], -(-len(u.get('items', ())) // 2)) if u['kind'] == 'card' else B['paragraph_max']
        if groups_u > limit:
            out.append(('EMPHASIS-DENSE', u['id'], f'{groups_u} 组强调（上限 {limit}）：重点太多等于没有重点'))
        if chars >= B['text_heavy_chars'] and groups_u < B['unit_min'] and not u.get('not_applicable'):
            out.append(('EMPHASIS-MISSING', u['id'], f'{chars} 字的文字单元没有强调：给关键数字、关键词或结论词加粗'))
    for k2, code, cap in (('risk', 'EMPHASIS-RED', 'page_risk_max'), ('highlight', 'EMPHASIS-MARK', 'page_highlight_max'),
                          ('underline', 'EMPHASIS-ULINE', 'page_underline_max')):
        if page[k2] > B[cap]: out.append((code, 'page', f'{page[k2]} 处（上限 {B[cap]}）'))
    return out, page

def _groups(runs):
    out, prev = [], False
    for t, st in runs:
        if st and t.strip():
            if prev: out[-1] = (out[-1][0] + t, out[-1][1] | set(st))
            else: out.append((t, set(st)))
            prev = True
        elif not st: prev = False
    return out

# ------------------------------------------------------------------ template trees (tools/kz_layouts/tree.py)
TEXT_ROLES = ('body', 'secondary')          # running text; titles, labels and KPI values follow their own contract
HEAD_ROLES = ('item_title', 'takeaway')     # bold lines: only the page totals (red, highlight, underline) apply

def tree_units(root):
    """Units of a template tree: each Card, plus loose running text (a conclusion line) as paragraphs."""
    from . import tree as TR
    units, heads = [], []
    def collect(node, u):
        if isinstance(node, TR.Text):
            if node.role in TEXT_ROLES: u['paras'].append(T.parse(node.markup))
            elif node.role in HEAD_ROLES: heads.append(T.parse(node.markup))
            return
        if isinstance(node, TR.Items):
            for it in node.items:
                u['items'].add(len(u['paras'])); u['paras'].append(T.parse(it if isinstance(it, str) else it['text']))
            return
        if isinstance(node, TR.Kpi) or isinstance(node, TR.Figure): return
        for k in ('children',):
            for c in getattr(node, k, []) or []: collect(c, u)
        for k in ('body', 'block'):
            c = getattr(node, k, None)
            if isinstance(c, TR.Node): collect(c, u)
    def walk(node):
        if isinstance(node, TR.Card):
            u = {'id': node.id or 'card', 'kind': 'card', 'paras': [], 'items': set()}
            collect(node.body, u)
            if u['paras']: units.append(u)
            return
        if isinstance(node, TR.Text):
            if node.role in TEXT_ROLES: units.append({'id': 'text', 'kind': 'paragraph', 'paras': [T.parse(node.markup)], 'items': set()})
            elif node.role in HEAD_ROLES: heads.append(T.parse(node.markup))
            return
        if isinstance(node, TR.Items):
            u = {'id': 'list', 'kind': 'card', 'paras': [], 'items': set()}; collect(node, u); units.append(u); return
        for c in getattr(node, 'children', []) or []: walk(c)
        for k in ('body', 'block'):
            c = getattr(node, k, None)
            if isinstance(c, TR.Node): walk(c)
    walk(root)
    if heads: units.append({'id': 'headings', 'kind': 'heading', 'paras': heads, 'items': set()})
    return units

# ------------------------------------------------------------------ ppt-master SVG pages
def _style(el):
    return {k.strip(): v.strip() for k, v in (kv.split(':', 1) for kv in (el.get('style') or '').split(';') if ':' in kv)}

def _a(el, name):
    return _style(el).get(name, el.get(name))

def _bold(v):
    return v is not None and (v in ('bold', 'bolder') or (v.isdigit() and int(v) >= 600))

def svg_units(svg):
    """Units of a ppt-master SVG page: each top-level <g id> without a structural role (one card, one block); every
    <text> in it is a paragraph; data-kz-emphasis="not_applicable" on the group waives MISSING. Emphasis is read back from what tools/kz_layouts/svg.py and hand-written pages emit:
    a bold run in non-bold text, the risk, marker or in-bold fill, or text-decoration underline."""
    import xml.etree.ElementTree as X
    root = X.fromstring(svg if svg.lstrip().startswith('<svg') else f'<svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>')
    ns = lambda el: el.tag.split('}')[-1]
    risk, marker, inbold = E['risk']['color'].upper(), E['highlight']['marker'].upper(), E['bold']['in_bold_color'].upper()
    units, heads = [], []
    def text_runs(t):
        base_bold = _bold(_a(t, 'font-weight')); base_fill = (_a(t, 'fill') or '').upper(); runs = []
        def walk(el, st):
            if el is not t:
                st = set(st)
                f = (_a(el, 'fill') or '').upper(); w = _a(el, 'font-weight'); d = _a(el, 'text-decoration') or ''
                if f == risk and base_fill != risk: st |= {'risk', 'bold'}
                elif f == marker: st.add('highlight')
                elif f == inbold and base_bold: st.add('bold')
                if _bold(w) and not base_bold: st.add('bold')
                if 'underline' in d: st.add('underline')
            if el.text: runs.append((el.text, frozenset(st)))
            for c in el:
                walk(c, st)
                if c.tail: runs.append((c.tail, frozenset(st)))
        walk(t, set())
        return runs
    for g in root:
        if ns(g) != 'g' or g.get('data-pptx-role') or not g.get('id') or g.get('id') in ('title', 'footer', 'header-mark'): continue
        texts = [t for t in g.iter() if ns(t) == 'text' and _n(''.join(t.itertext()))]
        paras = [text_runs(t) for t in texts if not _bold(_a(t, 'font-weight'))]
        heads += [text_runs(t) for t in texts if _bold(_a(t, 'font-weight'))]
        if paras: units.append({'id': g.get('id'), 'kind': 'card' if len(paras) > 1 else 'paragraph', 'paras': paras, 'items': set(),
                                'not_applicable': g.get('data-kz-emphasis') == 'not_applicable'})
    if heads: units.append({'id': 'headings', 'kind': 'heading', 'paras': heads, 'items': set()})
    return units
