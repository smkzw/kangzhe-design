#!/usr/bin/env python3
"""02 LG-02 for PPTX: find coloured edge bars on cards in ppt-master SVG pages.

    python3 tools/check_edge_bars.py <svg file or directory> [--json]

A bar is a thin coloured rect or line hugging one edge of a card-like rect (a rect at least 40×24 that is not
the full canvas). Thresholds come from tokens.glass.edge_bar. Group and element translate() transforms are
followed; rotated or skewed groups are skipped. Elements with a data-pptx-role (background, decoration, logo,
footer: page chrome) are not cards or bars. Exit 1 when any bar reaches forbid_ratio of its edge.
"""
from pathlib import Path
import argparse, colorsys, json, re, sys
import xml.etree.ElementTree as E

R = Path(__file__).resolve().parents[1]
T = json.loads((R / 'tokens/tokens.json').read_text())['glass']['edge_bar']
NS = '{http://www.w3.org/2000/svg}'

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
        p = [float(x) for x in re.split(r'[,\s/]+', m.group(1).strip()) if x]
        return tuple(x / 255 for x in p[:3])
    return {'white': (1, 1, 1), 'black': (0, 0, 0)}.get(v.lower())

def alpha_of(v):
    """Alpha carried inside an rgba()/rgb(... / a) value, 1 otherwise."""
    m = re.fullmatch(r'rgba?\(([^)]+)\)', (v or '').strip())
    p = [x for x in re.split(r'[,\s/]+', m.group(1).strip()) if x] if m else []
    return (float(p[3][:-1]) / 100 if p[3].endswith('%') else float(p[3])) if len(p) > 3 else 1.0

def coloured(rgb, alpha):
    if rgb is None or alpha < T['alpha_min']:
        return False
    return colorsys.rgb_to_hsv(*rgb)[1] > T['neutral_saturation_max']

def translate(t):
    """(dx, dy) for translate(), None for any other transform."""
    if not t:
        return 0.0, 0.0
    m = re.fullmatch(r'\s*translate\(\s*([-\d.eE]+)(?:[\s,]+([-\d.eE]+))?\s*\)\s*', t)
    return (float(m.group(1)), float(m.group(2) or 0)) if m else None

def scan(path):
    root = E.parse(path).getroot()
    vb = [float(x) for x in (root.get('viewBox') or '0 0 1280 720').split()]
    grads = {}
    for g in root.iter():
        if g.tag in (NS + 'linearGradient', NS + 'radialGradient') and g.get('id'):
            grads[g.get('id')] = [(colour(s.get('stop-color')), float(s.get('stop-opacity', 1))) for s in g.iter(NS + 'stop')]
    def paints(el, attr):
        v = el.get(attr) or ''
        style = {k.strip(): x.strip() for k, x in (kv.split(':', 1) for kv in (el.get('style') or '').split(';') if ':' in kv)}
        v = style.get(attr, v).strip()
        op = float(el.get(attr + '-opacity', style.get(attr + '-opacity', 1))) * float(el.get('opacity', 1))
        m = re.fullmatch(r'url\(#([^)]+)\)', v)
        stops = grads.get(m.group(1), []) if m else [(colour(v), op * alpha_of(v))]
        return any(coloured(c, a * (op if m else 1)) for c, a in stops)
    cards, bars = [], []
    def walk(el, dx, dy, chrome):
        t = translate(el.get('transform'))
        if t is None:
            return
        dx, dy = dx + t[0], dy + t[1]
        chrome = chrome or el.get('data-pptx-role') is not None
        tag = el.tag.replace(NS, '')
        if tag == 'rect' and not chrome:
            x, y = dx + float(el.get('x', 0)), dy + float(el.get('y', 0))
            w, h = float(el.get('width', 0)), float(el.get('height', 0))
            if w >= 40 and h >= 24 and not (w >= vb[2] * .98 and h >= vb[3] * .98):
                cards.append((x, y, w, h, el.get('id') or ''))
            if min(w, h) <= T['max_thickness_px'] and paints(el, 'fill'):
                bars.append((x, y, w, h, el.get('id') or 'rect'))
        elif tag == 'line' and not chrome and paints(el, 'stroke'):
            x1, y1, x2, y2 = (float(el.get(k, 0)) for k in ('x1', 'y1', 'x2', 'y2'))
            sw = float(el.get('stroke-width', 1))
            if sw <= T['max_thickness_px'] and (x1 == x2 or y1 == y2):
                bars.append((dx + min(x1, x2) - (sw / 2 if x1 == x2 else 0), dy + min(y1, y2) - (sw / 2 if y1 == y2 else 0),
                             abs(x2 - x1) or sw, abs(y2 - y1) or sw, el.get('id') or 'line'))
        for c in el:
            walk(c, dx, dy, chrome)
    walk(root, 0.0, 0.0, False)
    hug, out = T['hug_px'], []
    for bx, by, bw, bh, bid in bars:
        for cx, cy, cw, ch, cid in cards:
            if (bx, by, bw, bh) == (cx, cy, cw, ch) or bw * bh >= cw * ch:
                continue
            inside = bx >= cx - hug and by >= cy - hug and bx + bw <= cx + cw + hug and by + bh <= cy + ch + hug
            if not inside:
                continue
            side = ratio = None
            if bh > bw:
                side = 'left' if abs(bx - cx) <= hug else 'right' if abs(cx + cw - bx - bw) <= hug else None
                ratio = bh / ch
            else:
                side = 'top' if abs(by - cy) <= hug else 'bottom' if abs(cy + ch - by - bh) <= hug else None
                ratio = bw / cw
            level = side and ('fail' if ratio >= T['forbid_ratio'] else 'warn' if ratio >= T['warn_ratio'] else None)
            if level:
                out.append({'file': Path(path).name, 'card': cid, 'bar': bid, 'side': side, 'ratio': round(ratio, 2), 'level': level})
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('target', type=Path); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    files = sorted(a.target.glob('*.svg')) if a.target.is_dir() else [a.target]
    found = [b for f in files for b in scan(f)]
    if a.json:
        print(json.dumps({'files': len(files), 'bars': found}, ensure_ascii=False, indent=1))
    else:
        for b in found:
            print(f"{b['level'].upper():5} {b['file']}: {b['bar']} on {b['side']} edge of card {b['card'] or '(no id)'}, {b['ratio']:.0%} of the edge")
        print(f"{len(files)} SVG, {sum(b['level'] == 'fail' for b in found)} fail, {sum(b['level'] == 'warn' for b in found)} warn")
    sys.exit(1 if any(b['level'] == 'fail' for b in found) else 0)

if __name__ == '__main__':
    main()
