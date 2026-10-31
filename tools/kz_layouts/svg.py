"""Primitives → ppt-master SVG (adapters/ppt-master.md, upstream shared-standards-core §4.2–4.3).

- One <text> per paragraph; later lines are positioned <tspan x dy>; emphasis is a non-positional <tspan> run
  (font-weight, fill, text-decoration) so it stays inside the same editable text frame.
- Highlight runs carry the sentinel colour layout.templates.highlight_marker; tools/bind_highlight_pptx.py turns
  them into ink text with a native highlight after export.
- Every card, figure and loose block is one top-level <g id> with data-pptx-bounds; card shells and glints are
  root primitives with data-pptx-role="decoration" (they overlap their own content group, which the contract allows).
- Icons are <use data-icon="kangzhe/<name>">; copy assets/icons/kangzhe/ to <project>/icons/kangzhe/ first.
"""
from html import escape
from . import text as T
from .tree import TOK, C, L, INK

G = TOK['glass']; SH = TOK['elevation']['pptx']['rest']; SH_COLOR = TOK['elevation']['pptx']['color']
_ASC = None

def _ascent_ratio():
    global _ASC
    if _ASC is None:
        f = T._font(False)
        if f:
            a, d = f.getmetrics(); _ASC = (a / 100.0, d / 100.0)
        else:
            _ASC = (1.06, 0.26)
    return _ASC

def baseline(top, size, lead):
    a, d = _ascent_ratio()
    return top + (lead * size - (a + d) * size) / 2 + a * size

def defs():
    stops = ''.join(f'<stop offset="{v["offset"]}" stop-color="{v["color"]}" stop-opacity="{v["alpha"]}"/>' for v in G['face_gradient'])
    return (f'<linearGradient id="kz-face" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient>'
            '<linearGradient id="kz-glint" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
            '<stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.95"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
            f'<filter id="kz-shadow"><feDropShadow dx="{SH["dx"]}" dy="{SH["dy"]}" stdDeviation="{SH["std_deviation"]}" flood-color="{SH_COLOR}" flood-opacity="{SH["alpha"]}"/></filter>')

def f(n):
    return f'{n:.1f}'.rstrip('0').rstrip('.')

def run_svg(t, st, color, bold=False):
    """One inline run; `bold` is the paragraph's own weight (a bold run inside bold text adds nothing)."""
    attrs = []
    if 'risk' in st: attrs.append(f'fill="{C["risk"]}"')
    elif 'highlight' in st: attrs.append(f'fill="{L["highlight_marker"]}"')
    elif 'bold' in st and bold: attrs.append(f'fill="{C["focus"]}"')  # bold inside bold text (bands, titles) shows as the focus colour
    if ('bold' in st or 'risk' in st) and not bold: attrs.append('font-weight="bold"')
    if 'underline' in st: attrs.append('text-decoration="underline"')
    return f'<tspan {" ".join(attrs)}>{escape(t)}</tspan>' if attrs else escape(t)

def text_svg(p):
    lines, size, lead = p['lines'], p['size'], p['lead']
    anchor = {'start': 'start', 'middle': 'middle', 'end': 'end'}[p['align']]
    x = p['x'] + (p['w'] / 2 if anchor == 'middle' else p['w'] if anchor == 'end' else 0)
    y0 = baseline(p['y'], size, lead)
    attrs = f'x="{f(x)}" y="{f(y0)}" font-size="{f(size)}" fill="{p["color"]}"' + (' font-weight="bold"' if p['bold'] else '') + (f' text-anchor="{anchor}"' if anchor != 'start' else '')
    body = ''.join(run_svg(t, st, p['color'], p['bold']) for t, st in lines[0])
    for ln in lines[1:]:
        body += f'<tspan x="{f(x)}" dy="{f(size * lead)}">' + ''.join(run_svg(t, st, p['color'], p['bold']) for t, st in ln) + '</tspan>'
    return f'<text {attrs}>{body}</text>'

def text_box(p):
    size, lead = p['size'], p['lead']
    ws = [T.runs_width(ln, size, p['bold']) for ln in p['lines']] or [0]
    w = max(ws); x = p['x'] + {'start': 0, 'middle': (p['w'] - w) / 2, 'end': p['w'] - w}[p['align']]
    pad = 0.2 * size  # ppt-master's checker boxes a line from baseline - 0.85em to baseline + 0.35em
    return [x, p['y'] - pad, w, len(p['lines']) * size * lead + 2 * pad]

def icon_svg(name, x, y, size, tone='focus', disc=False):
    from .tree import ICONS
    if name not in ICONS: raise KeyError(f'未知图标：{name}（见 assets/icons/icons.json）')
    col = L['icon_tone'] if tone == 'focus' else C.get(tone, tone) if not str(tone).startswith('#') else tone
    out = ''
    if disc:
        out += f'<circle cx="{f(x + size / 2)}" cy="{f(y + size / 2)}" r="{f(size / 2)}" fill="{L["icon_tint"]}"/>'
        inner = size * 0.6; x, y, size = x + (size - inner) / 2, y + (size - inner) / 2, inner
    return out + f'<use data-icon="kangzhe/{name}" x="{f(x)}" y="{f(y)}" width="{f(size)}" height="{f(size)}" fill="{col}"/>'

TONES = {'brand': C['brand'], 'risk': C['risk'], 'ok': TOK['departments']['statistics']['color'], 'muted': '#9AA1A8', 'ink': INK,
         'medical': TOK['departments']['medical']['color'], 'operations': TOK['departments']['operations']['color'],
         'statistics': TOK['departments']['statistics']['color'], 'pv': TOK['departments']['pv']['color'],
         **{f'cat{i + 1}': c for i, c in enumerate(TOK['charts']['categorical'])}}

def marker_svg(p):
    s, lead = p['size'], p['lead']; cy = p['y'] + lead * s / 2; tone = TONES.get(p['tone'], C['brand'])
    if p['kind'] == 'dot':
        r = s * 0.16
        return f'<circle cx="{f(p["x"] + r + 1)}" cy="{f(cy)}" r="{f(r)}" fill="{tone}"/>', [p['x'], cy - r, 2 * r + 1, 2 * r]
    if p['kind'] == 'number':
        d = max(22, s * 1.15); n = str(p['n']); fs = max(14, s * 0.62) if len(n) < 3 else max(12, s * 0.5)  # numerals stay ≥ 10.5 pt
        circ = f'<circle cx="{f(p["x"] + d / 2)}" cy="{f(cy)}" r="{f(d / 2)}" fill="{tone}"/>'
        num = f'<text x="{f(p["x"] + d / 2)}" y="{f(cy + fs * 0.36)}" font-size="{f(fs)}" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{n}</text>'
        return circ + num, [p['x'], cy - d / 2, d, d]
    name = {'check': 'check', 'cross': 'cross'}.get(p['kind'], p['kind'])
    col = TONES['ok'] if p['kind'] == 'check' else TONES['risk'] if p['kind'] == 'cross' else tone
    sz = s * 1.0
    return icon_svg(name, p['x'], cy - sz / 2, sz, col), [p['x'], cy - sz / 2, sz, sz]

def badge_svg(p):
    """A lettered or numbered disc (PICOS rows, numbered cards): tone fill, white bold text."""
    s = p['size']; cx, cy = p['x'] + s / 2, p['y'] + s / 2; tone = TONES.get(p['tone'], C['brand'] if p['tone'] == 'focus' else p['tone'])
    fs = max(16, s * 0.5) if len(p['text']) < 2 else max(14, s * 0.4) if len(p['text']) < 3 else s * 0.32
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(s / 2)}" fill="{tone}"/>'
            f'<text x="{f(cx)}" y="{f(cy + fs * 0.36)}" font-size="{f(fs)}" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{escape(p["text"])}</text>'), [p['x'], p['y'], s, s]

def card_shell(p, gid):
    r = G['radius'] if p['h'] > 140 else G['radius_compact']
    fill = {'glass': 'url(#kz-face)', 'tint': '#FFF6E8', 'risk': '#FCEDEC', 'plain': '#FFFFFF'}[p['variant']]
    shell = (f'<rect id="{gid}-shell" data-pptx-role="decoration" x="{f(p["x"])}" y="{f(p["y"])}" width="{f(p["w"])}" height="{f(p["h"])}" rx="{r}" '
             f'fill="{fill}" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>')
    glint = f'<rect id="{gid}-glint" data-pptx-role="decoration" x="{f(p["x"] + r)}" y="{f(p["y"] + 1)}" width="{f(min(200, p["w"] * G["highlight_extent_max"]))}" height="1.5" fill="url(#kz-glint)"/>'
    return shell + glint

def union(boxes):
    boxes = [b for b in boxes if b]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
    return [x0, y0, x1 - x0, y1 - y0]

def _overlap(a, b):
    return min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > 1 and min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > 1

def render(prims, prefix='u'):
    """→ (root_svg, unit_ids). Each card's content is one top-level group bounded by what it draws; a chart, table or
    diagram is its own top-level group (a native replacement object), so a card holding one splits its content into
    the groups above and below it. Loose text and icons become their own small groups."""
    from . import figures
    root, units, n, cur, depth = [], [], 0, None, 0
    def gid(name=None):
        nonlocal n
        n += 1
        return name or f'{prefix}{n}'
    def emit(g, parts, frame=None):
        box = union([b for _, b in parts] + ([frame] if frame else []))
        root.append(f'<g id="{g}" data-pptx-bounds="{" ".join(f(v) for v in box)}">' + ''.join(s for s, _ in parts) + '</g>'); units.append(g)
    for p in prims:
        k = p['k']
        if k == 'card':
            g = gid(p.get('id')); root.append(card_shell(p, g))
            if cur is not None: depth += 1; continue  # a card inside a card: its shell is decoration, its text joins the outer unit
            cur = {'id': g, 'parts': [], 'figs': [], 'rect': [p['x'], p['y'], p['w'], p['h']]}; continue
        if k == 'end_unit' and depth:
            depth -= 1; continue
        if k == 'end_unit':
            groups, run = [], []
            for part in sorted(cur['parts'], key=lambda x: x[1][1]):
                if run and any(_overlap(union([b for _, b in run] + [part[1]]), fb) for fb in cur['figs']):
                    groups.append(run); run = []
                run.append(part)
            if run: groups.append(run)
            # a card's text frame is the card itself (it is the space the text may use); split groups keep their own extent
            for j, grp in enumerate(groups):
                r = cur['rect']; top = min(b[1] for _, b in grp)
                emit(cur['id'] if j == 0 else f'{cur["id"]}-{j + 1}', grp, r if len(groups) == 1 and not cur['figs'] else [r[0], top, r[2], 0])
            cur = None; continue
        if k == 'figure':
            g = gid(p.get('id')); box = [p['x'], p['y'], p['w'], p['h']]
            root.append(figures.svg(p['kind'], p['spec'], box, g)); units.append(g)
            if cur is not None: cur['figs'].append(box)
            continue
        if k == 'text': part = (text_svg(p), text_box(p))
        elif k == 'icon': part = (icon_svg(p['name'], p['x'], p['y'], p['size'], p['tone'], p['disc']), [p['x'], p['y'], p['size'], p['size']])
        elif k == 'marker':
            if p['kind'] == 'none': continue  # continuation of a criterion broken across columns: no number
            part = marker_svg(p)
        elif k == 'badge': part = badge_svg(p)
        else: raise ValueError(k)
        if cur is not None: cur['parts'].append(part)
        else: emit(gid(), [part], [p['x'], p['y'], p.get('w', 0), 0] if k == 'text' else None)
    return ''.join(root), units
