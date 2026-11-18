#!/usr/bin/env python3
"""02 LG-02 for PPTX: find coloured edge bars on cards, in ppt-master SVG pages and in the exported PPTX.

    python3 tools/check_edge_bars.py <svg file or directory> [--json]
    python3 tools/check_edge_bars.py --pptx out.pptx [--json]

A card is any closed shape at least 40×24 that is not the full canvas: rect, path, polygon (SVG) or a preset or
custom shape (PPTX). Template card shells carry data-pptx-role="decoration" and are cards all the same. A bar is a
thin (≤ max_thickness_px) coloured shape or stroke — rect, line, path, polygon or polyline — that hugs one edge of a
card from inside or from outside (its near side within hug_px of the edge) and runs along it. Paint is resolved like
SVG does it: inline style over presentation attribute over <style> class/id/tag rules over the inherited value;
gradient fills count when any stop is coloured. translate, scale and matrix transforms without rotation are followed;
rotated or skewed subtrees are skipped. Page chrome is not a card or a bar: background, logo and footer roles, and
the header mark, title and page rule. Data graphics are not cards either (02 LG-02: Gantt bars, plot bars and bands
are data marks): a subtree marked data-kz-figure in SVG, and in PPTX the group a template figure exports to (named
<page prefix>f<n>, the id kz_layouts gives every Figure), is skipped. Thresholds come from tokens.glass.edge_bar. Exit 1 when any bar reaches
forbid_ratio of its edge; shorter hugging marks are WARN.
"""
from pathlib import Path
import argparse, colorsys, json, re, sys, zipfile
import xml.etree.ElementTree as E

R = Path(__file__).resolve().parents[1]
T = json.loads((R / 'tokens/tokens.json').read_text())['glass']['edge_bar']
NS = '{http://www.w3.org/2000/svg}'
CHROME_ROLES = ('background', 'logo', 'footer')
CHROME_IDS = ('header-mark', 'rule', 'title', 'footer', 'bg', 'logo')

def colour(v):
    """→ (r,g,b) 0–1 or None for none/transparent/unknown."""
    v = (v or '').strip()
    m = re.fullmatch(r'#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})', v)
    if m:
        h = m.group(1)
        h = ''.join(c * 2 for c in h) if len(h) == 3 else h
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    m = re.fullmatch(r'rgba?\(([^)]+)\)', v)
    if m:
        p = [float(x) for x in re.split(r'[,\s/]+', m.group(1).strip()) if x and not x.endswith('%')][:3]
        return tuple(x / 255 for x in p) if len(p) == 3 else None
    return {'white': (1, 1, 1), 'black': (0, 0, 0), 'red': (1, 0, 0), 'orange': (1, .65, 0)}.get(v.lower())

def alpha_of(v):
    """Alpha carried inside an rgba()/rgb(... / a) value, 1 otherwise."""
    m = re.fullmatch(r'rgba?\(([^)]+)\)', (v or '').strip())
    p = [x for x in re.split(r'[,\s/]+', m.group(1).strip()) if x] if m else []
    return (float(p[3][:-1]) / 100 if p[3].endswith('%') else float(p[3])) if len(p) > 3 else 1.0

def coloured(rgb, alpha):
    if rgb is None or alpha < T['alpha_min']:
        return False
    return colorsys.rgb_to_hsv(*rgb)[1] > T['neutral_saturation_max']

# ------------------------------------------------------------------ transforms: (a, b, c, d, e, f) as in SVG matrix()
def _mul(m, n):
    a, b, c, d, e, f = m; A, B, C, D, Ee, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * Ee + c * F + e, b * Ee + d * F + f)

def transform(t):
    """→ matrix for translate/scale/matrix (any chain), None when a rotate, skew or skewed matrix is present."""
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.split(r'[\s,]+', args.strip()) if x]
        if name == 'translate': n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale': n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'matrix' and len(v) == 6 and abs(v[1]) < 1e-9 and abs(v[2]) < 1e-9: n = tuple(v)
        elif name == 'rotate' and v and abs(v[0]) < 1e-9: n = (1, 0, 0, 1, 0, 0)
        else: return None
        m = _mul(m, n)
    return m

def apply(m, box):
    x, y, w, h = box; a, _, _, d, e, f = m
    x0, x1 = sorted((a * x + e, a * (x + w) + e)); y0, y1 = sorted((d * y + f, d * (y + h) + f))
    return (x0, y0, x1 - x0, y1 - y0)

# ------------------------------------------------------------------ shape boxes
def path_box(d):
    """Bounding box of a path from its end and control points (arcs by their end points); None for an empty path."""
    pts, cx, cy, sx, sy = [], 0.0, 0.0, 0.0, 0.0
    toks = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', d or '')
    i, cmd = 0, None
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.fullmatch(r'[A-Za-z]', toks[i]): cmd = toks[i]; i += 1
        if cmd is None: break
        rel = cmd.islower(); C = cmd.upper()
        if C == 'Z': cx, cy = sx, sy; pts.append((cx, cy)); cmd = None; continue
        try:
            if C in 'ML':
                x, y = num(), num(); cx, cy = (cx + x, cy + y) if rel else (x, y)
                if C == 'M': sx, sy = cx, cy; cmd = 'l' if rel else 'L'
                pts.append((cx, cy))
            elif C == 'H': x = num(); cx = cx + x if rel else x; pts.append((cx, cy))
            elif C == 'V': y = num(); cy = cy + y if rel else y; pts.append((cx, cy))
            elif C in 'CSQT':
                n = {'C': 3, 'S': 2, 'Q': 2, 'T': 1}[C]
                for _ in range(n):
                    x, y = num(), num(); px, py = (cx + x, cy + y) if rel else (x, y); pts.append((px, py))
                cx, cy = pts[-1]
            elif C == 'A':
                num(); num(); num(); num(); num(); x, y = num(), num(); cx, cy = (cx + x, cy + y) if rel else (x, y); pts.append((cx, cy))
            else: i += 1
        except (IndexError, ValueError):
            break
    if not pts: return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

def points_box(s):
    v = [float(x) for x in re.split(r'[\s,]+', (s or '').strip()) if x]
    if len(v) < 4: return None
    xs, ys = v[0::2], v[1::2]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

def axis_aligned(pts):
    """True when consecutive vertices share an x or a y (a strip, not an arrowhead or a wedge)."""
    pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    return len(pts) >= 2 and all(abs(a[0] - b[0]) < .01 or abs(a[1] - b[1]) < .01 for a, b in zip(pts, pts[1:]))

def path_points(d):
    """Vertices of a path made of straight segments only; None when it has curves or arcs (a rounded strip counts
    as a strip, so the caller then keeps it)."""
    if re.search(r'[CcSsQqTtAa]', d or ''): return None
    pts, cx, cy, sx, sy = [], 0.0, 0.0, 0.0, 0.0
    toks = re.findall(r'[MmLlHhVvZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', d or ''); i, cmd = 0, None
    while i < len(toks):
        if re.fullmatch(r'[A-Za-z]', toks[i]): cmd = toks[i]; i += 1
        if cmd is None: break
        rel, C = cmd.islower(), cmd.upper()
        try:
            if C == 'Z': cx, cy = sx, sy; pts.append((cx, cy)); cmd = None; continue
            if C in 'ML':
                x, y = float(toks[i]), float(toks[i + 1]); i += 2; cx, cy = (cx + x, cy + y) if rel else (x, y)
                if C == 'M': sx, sy = cx, cy; cmd = 'l' if rel else 'L'
            elif C == 'H': x = float(toks[i]); i += 1; cx = cx + x if rel else x
            elif C == 'V': y = float(toks[i]); i += 1; cy = cy + y if rel else y
            pts.append((cx, cy))
        except (IndexError, ValueError):
            break
    return pts

# ------------------------------------------------------------------ the shared geometry
def find_bars(cards, bars, file):
    """cards: [(x,y,w,h,id)], bars: [(x,y,w,h,id)] in one coordinate system → findings."""
    hug, out = T['hug_px'], []
    for bx, by, bw, bh, bid in bars:
        best = None
        for cx, cy, cw, ch, cid in cards:
            if (round(bx, 1), round(by, 1), round(bw, 1), round(bh, 1)) == (round(cx, 1), round(cy, 1), round(cw, 1), round(ch, 1)) or bw * bh >= cw * ch:
                continue
            if bh > bw:   # vertical: hugs the left or right edge, from inside or from outside
                side = 'left' if min(abs(bx - cx), abs(bx + bw - cx)) <= hug else 'right' if min(abs(bx + bw - cx - cw), abs(bx - cx - cw)) <= hug else None
                run = min(by + bh, cy + ch) - max(by, cy); length, edge = bh, ch
            else:
                side = 'top' if min(abs(by - cy), abs(by + bh - cy)) <= hug else 'bottom' if min(abs(by + bh - cy - ch), abs(by - cy - ch)) <= hug else None
                run = min(bx + bw, cx + cw) - max(bx, cx); length, edge = bw, cw
            if not side or run < 0.6 * length or run <= 0: continue
            ratio = run / edge
            level = 'fail' if ratio >= T['forbid_ratio'] else 'warn' if ratio >= T['warn_ratio'] else None
            if level and (best is None or ratio > best['ratio']):
                best = {'file': file, 'card': cid, 'bar': bid, 'side': side, 'ratio': round(ratio, 2), 'level': level}
        if best: out.append(best)
    return out

# ------------------------------------------------------------------ SVG
def _css_rules(root):
    """Simple <style> rules: .class, #id and tag selectors (comma lists) → {selector: {prop: value}}."""
    rules = {}
    for st in root.iter(NS + 'style'):
        for sels, body in re.findall(r'([^{}]+)\{([^}]*)\}', st.text or ''):
            props = {k.strip(): v.strip() for k, v in (kv.split(':', 1) for kv in body.split(';') if ':' in kv)}
            for sel in sels.split(','):
                sel = sel.strip()
                if re.fullmatch(r'[.#]?[\w-]+', sel): rules.setdefault(sel, {}).update(props)
    return rules

PAINT = ('fill', 'stroke', 'stroke-width', 'fill-opacity', 'stroke-opacity', 'opacity')

def scan(path):
    root = E.parse(path).getroot() if not str(path).lstrip().startswith('<') else E.fromstring(str(path))
    file = Path(path).name if not str(path).lstrip().startswith('<') else 'svg'
    vb = [float(x) for x in (root.get('viewBox') or '0 0 1280 720').split()]
    grads = {}
    for g in root.iter():
        if g.tag in (NS + 'linearGradient', NS + 'radialGradient') and g.get('id'):
            grads[g.get('id')] = [(colour(s.get('stop-color')), float(s.get('stop-opacity', 1))) for s in g.iter(NS + 'stop')]
    css = _css_rules(root)
    def style_of(el, inh):
        st = dict(inh); st['opacity'] = '1'          # opacity multiplies down the tree (handled through op below)
        for sel in [el.tag.replace(NS, '')] + ['.' + c for c in (el.get('class') or '').split()] + (['#' + el.get('id')] if el.get('id') else []):
            st.update({k: v for k, v in css.get(sel, {}).items() if k in PAINT})
        st.update({k: el.get(k) for k in PAINT if el.get(k) is not None})
        inline = {k.strip(): v.strip() for k, v in (kv.split(':', 1) for kv in (el.get('style') or '').split(';') if ':' in kv)}
        st.update({k: v for k, v in inline.items() if k in PAINT})
        return st
    def painted(st, attr, op):
        v = (st.get(attr) or ('#000' if attr == 'fill' else 'none')).strip()
        if v in ('none', 'transparent'): return False
        a = float(st.get(attr + '-opacity', 1)) * op
        m = re.fullmatch(r'url\(#([^)]+)\)', v)
        stops = grads.get(m.group(1), []) if m else [(colour(v), alpha_of(v))]
        return any(coloured(c, s * a) for c, s in stops)
    cards, bars = [], []
    def walk(el, M, inh, op, chrome):
        t = transform(el.get('transform'))
        if t is None: return
        M = _mul(M, t)
        tag = el.tag.replace(NS, '')
        if tag in ('defs', 'clipPath', 'mask', 'linearGradient', 'radialGradient', 'pattern', 'symbol', 'metadata', 'style', 'text'): return
        if el.get('data-kz-figure') is not None: return   # a data graphic: its bars are data marks, not card edges
        chrome = chrome or el.get('data-pptx-role') in CHROME_ROLES or el.get('id') in CHROME_IDS or (el.get('id') or '').startswith('kz-facet')
        st = style_of(el, inh); op = op * float(st.get('opacity') or 1)
        box = None
        if tag == 'rect': box = (float(el.get('x', 0)), float(el.get('y', 0)), float(el.get('width', 0)), float(el.get('height', 0)))
        elif tag == 'path':
            pp = path_points(el.get('d'))
            box = path_box(el.get('d')) if pp is None or axis_aligned(pp) else None
        elif tag in ('polygon', 'polyline'):
            v = [float(x) for x in re.split(r'[\s,]+', (el.get('points') or '').strip()) if x]
            box = points_box(el.get('points')) if axis_aligned(list(zip(v[0::2], v[1::2]))) else None
        elif tag == 'line':
            x1, y1, x2, y2 = (float(el.get(k, 0)) for k in ('x1', 'y1', 'x2', 'y2'))
            box = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        if box and not chrome:
            sw = float(re.sub(r'px$', '', str(st.get('stroke-width') or 1)) or 1)
            x, y, w, h = apply(M, box); k = abs(M[0]) if w >= h else abs(M[3]); sw *= k
            closed = tag in ('rect', 'polygon') or (tag == 'path' and re.search(r'[Zz]\s*$', el.get('d') or ''))
            if closed and w >= 40 and h >= 24 and not (w >= vb[2] * .98 and h >= vb[3] * .98):
                cards.append((x, y, w, h, el.get('id') or tag))
            if closed and min(w, h) <= T['max_thickness_px'] and painted(st, 'fill', op):
                bars.append((x, y, w, h, el.get('id') or tag))
            elif min(w, h) <= T['max_thickness_px'] and painted(st, 'stroke', op) and sw <= T['max_thickness_px'] and (w <= 1 or h <= 1 or not closed):
                # a stroke drawn along one axis: a line, an open path, a hairline rect
                if w >= h: bars.append((x, y + h / 2 - sw / 2, w, sw, el.get('id') or tag))
                else: bars.append((x + w / 2 - sw / 2, y, sw, h, el.get('id') or tag))
        for c in el: walk(c, M, st, op, chrome)
    walk(root, (1, 0, 0, 1, 0, 0), {}, 1.0, False)
    return find_bars(cards, bars, file)

# ------------------------------------------------------------------ PPTX (after export: native shapes)
_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
_P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU = 9525
FIGURE_GROUP = re.compile(r'[a-z][a-z0-9-]*\d*f\d+')   # kz_layouts Figure ids, e.g. programplan1f2

def _fill(el, alpha_mul=1.0):
    """Colour paint of an <a:solidFill>/<a:gradFill> (or None): [(rgb, alpha)]."""
    out = []
    for sf in el.findall(_A + 'solidFill') + [g for gf in el.findall(_A + 'gradFill') for g in gf.iter(_A + 'gs')]:
        clr = sf.find(_A + 'srgbClr')
        if clr is None: continue
        a = clr.find(_A + 'alpha')
        out.append((colour('#' + clr.get('val')), (int(a.get('val')) / 100000 if a is not None else 1.0) * alpha_mul))
    return out

def scan_pptx(pptx):
    found = []
    with zipfile.ZipFile(pptx) as z:
        names = sorted((n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)), key=lambda n: int(re.findall(r'\d+', n)[-1]))
        for name in names:
            root = E.fromstring(z.read(name)); cards, bars = [], []
            def xf(sppr):
                x = sppr.find(_A + 'xfrm') if sppr is not None else None
                if x is None or x.find(_A + 'off') is None: return None
                o, e = x.find(_A + 'off'), x.find(_A + 'ext')
                return [int(o.get('x')), int(o.get('y')), int(e.get('cx')), int(e.get('cy'))]
            def walk(node, M):
                for el in node:
                    tag = el.tag.replace(_P, '')
                    if tag == 'grpSp':
                        g = el.find(_P + 'grpSpPr/' + _A + 'xfrm')
                        gn = el.find(f'{_P}nvGrpSpPr/{_P}cNvPr')
                        if gn is not None and FIGURE_GROUP.fullmatch(gn.get('name') or ''): continue   # a template figure (data marks)
                        if g is None: walk(el, M); continue
                        if g.get('rot') not in (None, '0'): continue
                        o, e, co, ce = (g.find(_A + k) for k in ('off', 'ext', 'chOff', 'chExt'))
                        sx = int(e.get('cx')) / max(1, int(ce.get('cx'))); sy = int(e.get('cy')) / max(1, int(ce.get('cy')))
                        walk(el, _mul(M, (sx, 0, 0, sy, int(o.get('x')) - sx * int(co.get('x')), int(o.get('y')) - sy * int(co.get('y')))))
                    elif tag in ('sp', 'cxnSp'):
                        sppr = el.find(_P + 'spPr'); box = xf(sppr)
                        if box is None or (sppr.find(_A + 'xfrm').get('rot') not in (None, '0')): continue
                        x, y, w, h = (v / EMU for v in apply(M, box))
                        nm = (el.find(f'.//{_P}cNvPr').get('name') if el.find(f'.//{_P}cNvPr') is not None else tag)
                        if re.match(r'kz-facet|header-mark|rule|footer|logo', nm or ''): continue
                        geom = sppr.find(_A + 'prstGeom'); prst = geom.get('prst') if geom is not None else 'custom'
                        if tag == 'sp' and prst != 'line' and w >= 40 and h >= 24 and not (w >= 1250 and h >= 700): cards.append((x, y, w, h, nm))
                        paint = _fill(sppr)
                        if prst == 'custom':  # a freeform: a strip only when its straight segments run along the axes (not an arrowhead)
                            pts = [(int(pt.get('x')), int(pt.get('y'))) for pt in sppr.iter(_A + 'pt')]
                            curved = any(True for _ in sppr.iter(_A + 'cubicBezTo')) or any(True for _ in sppr.iter(_A + 'arcTo'))
                            if pts and not curved and not axis_aligned(pts): paint = []
                        if tag == 'sp' and prst != 'line' and min(w, h) <= T['max_thickness_px'] and any(coloured(c, a) for c, a in paint):
                            bars.append((x, y, w, h, nm))
                        ln = sppr.find(_A + 'ln')
                        if ln is not None and (prst == 'line' or tag == 'cxnSp' or min(w, h) < 1) and any(coloured(c, a) for c, a in _fill(ln)):
                            sw = int(ln.get('w', 12700)) / EMU
                            if sw <= T['max_thickness_px']:
                                bars.append((x, y + h / 2 - sw / 2, w, sw, nm) if w >= h else (x + w / 2 - sw / 2, y, sw, h, nm))
            tree = root.find(f'.//{_P}spTree')
            if tree is not None: walk(tree, (1, 0, 0, 1, 0, 0))
            found += find_bars(cards, bars, name.split('/')[-1])
    return found

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('target', type=Path, nargs='?'); ap.add_argument('--pptx', type=Path); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if a.pptx:
        files, found = [a.pptx], scan_pptx(a.pptx)
    else:
        files = sorted(a.target.glob('*.svg')) if a.target.is_dir() else [a.target]
        found = [b for f in files for b in scan(f)]
    if a.json:
        print(json.dumps({'files': len(files), 'bars': found}, ensure_ascii=False, indent=1))
    else:
        for b in found:
            print(f"{b['level'].upper():5} {b['file']}: {b['bar']} on {b['side']} edge of card {b['card'] or '(no id)'}, {b['ratio']:.0%} of the edge")
        print(f"{len(files)} file(s), {sum(b['level'] == 'fail' for b in found)} fail, {sum(b['level'] == 'warn' for b in found)} warn")
    sys.exit(1 if any(b['level'] == 'fail' for b in found) else 0)

if __name__ == '__main__':
    main()
