"""Kangzhe template pages (13 BODY-02): page data → layout tree → PPTX (ppt-master SVG) or HTML-PPT markup.

    from kz_layouts import render, catalog
    pages = render('criteria', data, track='pptx')   # → [{'svg': body_svg, 'units': [...], 'data': page_data}, ...]
    pages = render('criteria', data, track='html')   # → [{'html': body_html, 'charts': {...}, 'data': page_data}, ...]

A template that holds rules or lists verbatim (03 COPY-09) never shortens them: it pages them, and numbering continues
on the next page (items 1–6 on the first page, 7… on the second; no “continued” label).
"""
from . import tree, svg as _svg, figures
from .tree import solve

PATTERNS = {}

# 13 BODY-03: every template belongs to one family (what kind of content it carries) and serves one or more density
# tiers (how much content: tokens.layout.density). Templates written before 8.0 get theirs here.
FAMILIES = ('points', 'process', 'compare', 'data', 'rules', 'discussion', 'plan')
LEGACY = {
    'criteria': ('rules', ('standard', 'dense')), 'soa': ('rules', ('dense',)), 'forest': ('data', ('standard', 'dense')),
    'km': ('data', ('standard', 'dense')), 'consort': ('data', ('standard', 'dense')), 'icon-grid': ('points', ('sparse', 'standard')),
    'chart-insight': ('data', ('standard', 'dense')), 'process': ('process', ('standard',)), 'funnel': ('data', ('sparse', 'standard')),
    'hub-spoke': ('points', ('sparse', 'standard')), 'quadrant': ('compare', ('standard',)), 'quote-evidence': ('discussion', ('sparse', 'standard')),
    'gantt-plan': ('plan', ('dense',)), 'options-compare': ('compare', ('standard', 'dense')), 'kpi-dashboard': ('data', ('standard', 'dense')),
    'roadmap': ('plan', ('standard',)), 'risk-matrix': ('compare', ('dense',)), 'architecture': ('process', ('standard',)),
    'kv-table': ('rules', ('standard', 'dense')), 'picos': ('rules', ('standard',)), 'numbered-cards': ('points', ('standard',)),
    'table-band': ('rules', ('dense',)), 'endpoints': ('rules', ('standard',)), 'allow-deny': ('rules', ('standard', 'dense')),
    'discussion': ('discussion', ('standard',)), 'study-schema': ('process', ('standard', 'dense')), 'windows': ('process', ('standard',)),
}

def pattern(name, *, scene, title, use, density, split=None, family=None, tiers=None):
    """Register a template. `split(data, fits)` returns the data of each page (for paged lists)."""
    def deco(fn):
        fam, tr = (family, tiers) if family else LEGACY[name]
        assert fam in FAMILIES, (name, fam)
        PATTERNS[name] = {'name': name, 'scene': scene, 'title': title, 'use': use, 'density': density, 'family': fam, 'tiers': list(tr),
                          'build': fn, 'split': split}
        return fn
    return deco

def catalog():
    from . import patterns  # noqa: F401  (registers)
    return [{k: v for k, v in p.items() if k not in ('build', 'split')} for p in PATTERNS.values()]

def _ids(node, prefix, counter):
    if isinstance(node, tree.Figure) and not node.id:
        counter[0] += 1; node.id = f'{prefix}f{counter[0]}'
    if isinstance(node, tree.Card) and not node.id:
        counter[0] += 1; node.id = f'{prefix}c{counter[0]}'
    for k in ('children',):
        for c in getattr(node, k, []) or []: _ids(c, prefix, counter)
    for k in ('body', 'block'):
        if hasattr(node, k) and isinstance(getattr(node, k), tree.Node): _ids(getattr(node, k), prefix, counter)

def balance(root):
    """03 TYPE-02 / COPY-10: sibling cards in one row share a height; when their content differs a lot one of them
    shows a void. → [{'row': n, 'fill': [natural/allotted per card], 'cards': [...]}] for rows whose fill spread exceeds
    tokens.layout.balance.spread_max while the emptiest card is under fill_min."""
    from .tokens_view import BAL
    out = []
    def walk(node, depth=0):
        if isinstance(node, tree.Row):
            cards = [c for c in node.children if isinstance(c, tree.Card)]
            got = getattr(node, '_placed', None)
            if len(cards) >= 2 and got:
                fills = []
                for c, (cw, ch) in zip(node.children, got):
                    if isinstance(c, tree.Card): fills.append(round(c.measure(cw) / ch, 2) if ch else 1)
                if fills and max(fills) - min(fills) > BAL['spread_max'] and min(fills) < BAL['fill_min']:
                    out.append({'fill': fills, 'cards': [c.id for c in cards]})
        for c in getattr(node, 'children', []) or []: walk(c, depth + 1)
        for k in ('body', 'block'):
            if isinstance(getattr(node, k, None), tree.Node): walk(getattr(node, k), depth + 1)
    walk(root)
    return out

def fits(name, data, box=None):
    from . import patterns  # noqa: F401
    root = PATTERNS[name]['build'](data)
    _, over = solve(root, box)
    return over <= 0.5

def render(name, data, track='pptx', box=None, prefix=None):
    from . import patterns  # noqa: F401
    p = PATTERNS[name]
    chunks = p['split'](data, lambda d: fits(name, d, box)) if p['split'] else [data]
    out = []
    for n, d in enumerate(chunks, 1):
        pre = f'{prefix or name.replace("-", "")}{n}'   # prefix: one per render call when a deck holds two renders of one template
        root = p['build'](d); _ids(root, pre, [0])
        prims, over = solve(root, box)
        from .emphasis import audit, tree_units
        found, stats = audit(tree_units(root))
        from .density import judge
        page = {'data': d, 'overflow': round(over, 1), 'emphasis': {'findings': [{'code': c, 'where': w, 'message': m} for c, w, m in found], 'page': stats},
                'density': judge(p['family'], p['tiers'], d), 'family': p['family'], 'balance': balance(root)}
        if track == 'pptx':
            page['svg'], page['units'] = _svg.render(prims, prefix=pre + 'u')
        else:
            figures.collect()
            page['html'] = '<div class="kzl-root" data-kz-pattern="' + name + '">' + root.html() + '</div>'
            page['charts'] = figures.collect()
        out.append(page)
    return out
