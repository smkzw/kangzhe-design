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

def pattern(name, *, scene, title, use, density, split=None):
    """Register a template. `split(data, fits)` returns the data of each page (for paged lists)."""
    def deco(fn):
        PATTERNS[name] = {'name': name, 'scene': scene, 'title': title, 'use': use, 'density': density, 'build': fn, 'split': split}
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
        pre = prefix or f'{name.replace("-", "")}{n}'
        root = p['build'](d); _ids(root, pre, [0])
        prims, over = solve(root, box)
        page = {'data': d, 'overflow': round(over, 1)}
        if track == 'pptx':
            page['svg'], page['units'] = _svg.render(prims, prefix=pre + 'u')
        else:
            figures.collect()
            page['html'] = '<div class="kzl-root" data-kz-pattern="' + name + '">' + root.html() + '</div>'
            page['charts'] = figures.collect()
        out.append(page)
    return out
