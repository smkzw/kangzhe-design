"""Diagram kinds (registered into diagrams.DRAW). Each takes (spec, box, gid, mode) and returns SVG: native shapes and
text for PPTX (one group), the same geometry inline for HTML. Main labels use the secondary role (16 px = 12 pt);
axis ticks and scale marks may use 14 px (03 TYPE-01 exceptions)."""
from html import escape
from .diagrams import kind, text, icon, f
from .tree import TOK, C, L, INK, BODY, MUTED, RISK, BRAND
from . import text as T

S = TOK['type_px']['secondary']; SMALL = 14
CAT = TOK['charts']['categorical']
TINT = {'brand': '#FFF1DE', 'risk': '#FCEDEC', 'muted': '#F1F3F5', 'ok': '#E8F1E4', 'blue': '#E4EDF6', 'soft': '#FFF8EE'}
EDGE = {'brand': '#F2B65C', 'risk': '#E8A3A0', 'muted': '#D5DADF', 'ok': '#A9C79A', 'blue': '#A9C2DA', 'soft': '#F5D7A8'}
SOLID = {'brand': BRAND, 'risk': RISK, 'muted': '#9AA1A8', 'ok': TOK['departments']['statistics']['color'], 'blue': TOK['departments']['operations']['color'],
         'soft': '#E9A23B', **{f'cat{i + 1}': c for i, c in enumerate(CAT)}}

def R(x, y, w, h, fill='#FFFFFF', stroke=None, rx=6, dash=False, sw=1):
    st = f' stroke="{stroke}" stroke-width="{sw}"' + (' stroke-dasharray="5 4"' if dash else '') if stroke else ''
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(max(0.5, w))}" height="{f(max(0.5, h))}" rx="{f(rx)}" fill="{fill}"{st}/>'

def Ln(x1, y1, x2, y2, stroke='#C9CED4', sw=1.5, dash=False):
    return f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{stroke}" stroke-width="{sw}"' + (' stroke-dasharray="5 4"' if dash else '') + '/>'

def Arrow(x1, y1, x2, y2, color='#9AA1A8', sw=1.8, head=8):
    import math
    a = math.atan2(y2 - y1, x2 - x1); bx, by = x2 - head * math.cos(a), y2 - head * math.sin(a)
    px, py = head * 0.55 * math.sin(a), -head * 0.55 * math.cos(a)
    return Ln(x1, y1, bx, by, color, sw) + f'<polygon points="{f(x2)},{f(y2)} {f(bx + px)},{f(by + py)} {f(bx - px)},{f(by - py)}" fill="{color}"/>'

def Diamond(cx, cy, r, fill):
    return f'<polygon points="{f(cx)},{f(cy - r)} {f(cx + r)},{f(cy)} {f(cx)},{f(cy + r)} {f(cx - r)},{f(cy)}" fill="{fill}"/>'

def Dot(cx, cy, r, fill, stroke=None):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="1.5"' if stroke else '') + '/>'

def Tx(x, y, s, size=S, color=BODY, bold=False, anchor='start', width=None, lead=1.3):
    """Text whose first line is centred on y (diagram labels sit on a row's centre line)."""
    lines = len(T.wrap(s, width or 1e9, size, bold))
    svg, h = text(x, y - lines * size * lead / 2, s, size, color, bold, anchor, width, lead)
    return svg

def lines_h(s, width, size=S, bold=False, lead=1.3):
    return len(T.wrap(s, width, size, bold)) * size * lead

# ---------------------------------------------------------------- study schema
@kind('schema')
def schema(spec, box, gid, mode):
    """Study design: period band, visit axis (visit above, week below), markers, one bar row per arm, background bar.
    spec: periods [{label, from, to, tone}], visits [{v, week, key, tag}], markers [{week, label, kind: random|primary}],
    arms [{label, bars: [{from, to, text, tone, dashed}]}], background {from, to, text}; weeks are numbers."""
    x, y, w, h = box
    lab_w = max([T.width(a['label'], S, True) for a in spec.get('arms', [])] + [0]) + 20
    weeks = [v['week'] for v in spec['visits']] + [p[k] for p in spec.get('periods', []) for k in ('from', 'to')]
    w0, w1 = min(weeks), max(weeks); x0, x1 = x + lab_w, x + w - 24
    X = lambda wk: x0 + (wk - w0) / ((w1 - w0) or 1) * (x1 - x0)
    rows = {'period': 30, 'gap1': 26, 'axis': 58, 'marker': 40}
    arm_h = 34; n_arm = len(spec.get('arms', [])); bg = spec.get('background')
    need = rows['period'] + rows['gap1'] + rows['axis'] + rows['marker'] + n_arm * (arm_h + 8) + (34 if bg else 0)
    pad = max(0, (h - need) / 6); cy = y + pad
    out = []
    for p in spec.get('periods', []):  # period band
        t = p.get('tone', 'soft')
        out.append(R(X(p['from']) + 1, cy, X(p['to']) - X(p['from']) - 2, rows['period'], TINT.get(t, t), EDGE.get(t), 5))
        out.append(Tx((X(p['from']) + X(p['to'])) / 2, cy + rows['period'] / 2, p['label'], S, '#8A5300', True, 'middle', X(p['to']) - X(p['from']) - 8))
    cy += rows['period'] + rows['gap1'] + pad
    ay = cy + 24  # visit axis
    out.append(Arrow(x0 - 16, ay, x1 + 16, ay, '#5F6B76', 2, 9))
    for v in spec['visits']:
        vx = X(v['week']); key = v.get('key')
        if v.get('tag'): out.append(Tx(vx, ay - 40, v['tag'], SMALL, '#B85C00', True, 'middle'))
        out.append(Tx(vx, ay - 20, v['v'], S, INK, True, 'middle'))
        out.append(Dot(vx, ay, 6 if key else 5, BRAND if key else '#FFFFFF', None if key else '#8A949E'))
        out.append(Tx(vx, ay + 20, v.get('label', f'W{v["week"]}'), SMALL, MUTED, False, 'middle'))
    cy += rows['axis'] + pad
    for m in spec.get('markers', []):
        mx = X(m['week']); col = RISK if m.get('kind') == 'primary' else BRAND
        out.append(Diamond(mx, cy + 6, 9, col)); out.append(Tx(mx, cy + 28, m['label'], S, col, True, 'middle'))
    cy += rows['marker'] + pad
    for a in spec.get('arms', []):
        out.append(Tx(x, cy + arm_h / 2, a['label'], S, INK, True))
        for b in a['bars']:
            t = b.get('tone', 'brand'); solid = not b.get('dashed') and t in ('brand', 'muted', 'blue', 'ok', 'risk')
            fill = SOLID[t] if solid and b.get('strong', True) else TINT.get(t, t)
            out.append(R(X(b['from']), cy, X(b['to']) - X(b['from']), arm_h, fill, EDGE.get(t) if not solid else None, 6, b.get('dashed', False), 1.5))
            out.append(Tx((X(b['from']) + X(b['to'])) / 2, cy + arm_h / 2, b['text'], S, '#FFFFFF' if solid and t != 'muted' else INK if solid else '#8A5300', True, 'middle', X(b['to']) - X(b['from']) - 10))
        cy += arm_h + 8
    if bg:
        cy += pad / 2
        out.append(R(X(bg['from']), cy, X(bg['to']) - X(bg['from']), 28, TINT['ok'], EDGE['ok'], 5))
        out.append(Tx((X(bg['from']) + X(bg['to'])) / 2, cy + 14, bg['text'], S, '#3D5A2A', True, 'middle', X(bg['to']) - X(bg['from']) - 10))
    return ''.join(out)

# ---------------------------------------------------------------- timeline with spans (AE windows, milestones)
@kind('timeline')
def timeline(spec, box, gid, mode):
    """Events on a horizontal axis with spans below it. spec: events [{label, sub, key}], spans [{from, to, label,
    detail, tone}] where from/to are event indexes (floats allowed)."""
    x, y, w, h = box; ev = spec['events']; n = len(ev)
    x0, x1 = x + 70, x + w - 70
    X = lambda i: x0 + i / max(1, n - 1) * (x1 - x0)
    spans = spec.get('spans', [])
    span_h = [max(30, 12 + lines_h(s['label'], X(s['to']) - X(s['from']) - 16, S, True) + (lines_h(s['detail'], X(s['to']) - X(s['from']) - 16, S) if s.get('detail') else 0)) for s in spans]
    need = 58 + sum(span_h) + 10 * len(spans)
    ay = y + max(28, (h - need) / 2 + 28)
    out = [Arrow(x + 20, ay, x + w - 10, ay, '#5F6B76', 2, 9)]
    for i, e in enumerate(ev):
        ex = X(i); key = e.get('key')
        out.append(Dot(ex, ay, 7 if key else 6, BRAND if key else '#FFFFFF', None if key else '#8A949E'))
        out.append(Tx(ex, ay - 20, e['label'], S, INK, True, 'middle', (x1 - x0) / max(1, n - 1) + 40))
        if e.get('sub'): out.append(Tx(ex, ay + 22, e['sub'], SMALL, MUTED, False, 'middle', (x1 - x0) / max(1, n - 1) + 40))
    cy = ay + 44
    for s, sh in zip(spans, span_h):
        t = s.get('tone', 'brand'); sx0, sx1 = X(s['from']), X(s['to'])
        out.append(R(sx0, cy, sx1 - sx0, sh, TINT.get(t, t), EDGE.get(t), 6))
        lh = lines_h(s['label'], sx1 - sx0 - 16, S, True)
        svg, _ = text(sx0 + 8, cy + 6, s['label'], S, '#8A5300' if t != 'risk' else RISK, True, 'start', sx1 - sx0 - 16, 1.3)
        out.append(svg)
        if s.get('detail'):
            svg, _ = text(sx0 + 8, cy + 6 + lh, s['detail'], S, BODY, False, 'start', sx1 - sx0 - 16, 1.3); out.append(svg)
        cy += sh + 10
    return ''.join(out)

# ---------------------------------------------------------------- process flow (steps, optional return branch)
def _flow_size(spec, w):
    st = spec['steps']; n = len(st); gap = 34; bw = (w - gap * (n - 1)) / n
    th = max(lines_h(s.get('text', ''), bw - 20, S) for s in st)
    return bw, gap, 44 + 12 + th + 14, (46 if spec.get('back') else 0)

def _flow_measure(spec, w):
    _, _, bh, back = _flow_size(spec, w); return bh + back + 8

@kind('flow', measure=_flow_measure)
def flow(spec, box, gid, mode):
    """Horizontal steps joined by arrows; each step a tinted box with an icon or number, a title and a short rule.
    spec: steps [{title, text, icon, tone}], back {from, to, label} (a return loop drawn under the steps)."""
    x, y, w, h = box; st = spec['steps']; n = len(st)
    bw, gap, bh, back = _flow_size(spec, w)
    bh = max(bh, min(h - back - 8, bh * 1.35))  # a little taller when there is room, never a tall empty box
    by = y + max(0, (h - bh - back) / 2)
    out = []
    for i, s in enumerate(st):
        bx = x + i * (bw + gap); t = s.get('tone', 'brand')
        out.append(R(bx, by, bw, bh, '#FFFFFF', EDGE.get(t, '#F2B65C'), 10, False, 1.5))
        out.append(R(bx, by, bw, 44, TINT.get(t, t), None, 10))
        out.append(R(bx, by + 30, bw, 14, TINT.get(t, t), None, 0))
        if s.get('icon'): out.append(icon(s['icon'], bx + 12, by + 8, 28, SOLID.get(t, BRAND), mode))
        else: out.append(Dot(bx + 26, by + 22, 13, SOLID.get(t, BRAND)) + Tx(bx + 26, by + 22, str(i + 1), SMALL, '#FFFFFF', True, 'middle'))
        out.append(Tx(bx + 48, by + 22, s['title'], S, INK, True, 'start', bw - 56))
        if s.get('text'):
            svg, _ = text(bx + 10, by + 56, s['text'], S, BODY, False, 'start', bw - 20, 1.3); out.append(svg)
        if i < n - 1: out.append(Arrow(bx + bw + 4, by + bh / 2, bx + bw + gap - 4, by + bh / 2, '#B85C00', 2, 9))
    if spec.get('back'):
        b = spec['back']; fx = x + b['from'] * (bw + gap) + bw / 2; tx = x + b['to'] * (bw + gap) + bw / 2; ly = by + bh + 26
        out.append(Ln(fx, by + bh, fx, ly, RISK, 1.8, True) + Ln(fx, ly, tx, ly, RISK, 1.8, True) + Arrow(tx, ly, tx, by + bh + 2, RISK, 1.8, 8))
        out.append(f'<rect x="{f((fx + tx) / 2 - T.width(b["label"], S) / 2 - 8)}" y="{f(ly - 11)}" width="{f(T.width(b["label"], S) + 16)}" height="22" rx="11" fill="#FFFFFF"/>')
        out.append(Tx((fx + tx) / 2, ly, b['label'], S, RISK, True, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- dense Gantt
@kind('gantt')
def gantt(spec, box, gid, mode):
    """Dense Gantt on a month grid: grouped tasks, bars [from, to) in month units, milestones, a status line.
    spec: months [labels], tasks [{group, label, from, to, tone, done (0–1), owner}], milestones [{at, label}], today."""
    x, y, w, h = box; months = spec['months']; tasks = spec['tasks']; nm = len(months)
    lab_w = min(w * 0.3, max(T.width(t['label'], S) for t in tasks) + 30)
    groups = []
    for t in tasks:
        if not groups or groups[-1][0] != t.get('group'): groups.append((t.get('group'), []))
        groups[-1][1].append(t)
    head = 30; ms_h = (30 + 20 * (len(spec.get('milestones', [])) - 1)) if spec.get('milestones') else 0
    rows = len(tasks) + sum(1 for g, _ in groups if g)
    rh = max(24, min(36, (h - head - ms_h - 6) / max(1, rows)))
    x0, x1 = x + lab_w, x + w; mw = (x1 - x0) / nm
    X = lambda m: x0 + m * mw
    out = [R(x0, y, x1 - x0, head, '#FFF4E2', None, 4)]
    for i, m in enumerate(months):
        out.append(Tx(X(i) + mw / 2, y + head / 2, m, SMALL, INK, True, 'middle'))
        if i: out.append(Ln(X(i), y + head, X(i), y + head + rows * rh + ms_h, '#EEF0F2', 1))
    cy = y + head
    for g, ts in groups:
        if g:
            out.append(Tx(x + 4, cy + rh / 2, g, S, '#8A5300', True)); out.append(Ln(x, cy + rh - 1, x1, cy + rh - 1, '#F2C98A', 1)); cy += rh
        for t in ts:
            tone = t.get('tone', 'brand'); col = SOLID.get(tone, tone); bx0, bx1 = X(t['from']), X(t['to'])
            out.append(Tx(x + 16, cy + rh / 2, t['label'], S, BODY, False, 'start', lab_w - 20))
            out.append(R(bx0 + 1, cy + rh * 0.2, bx1 - bx0 - 2, rh * 0.6, TINT.get(tone, '#FFF1DE'), None, rh * 0.3))
            done = t.get('done', 0)
            if done: out.append(R(bx0 + 1, cy + rh * 0.2, (bx1 - bx0 - 2) * done, rh * 0.6, col, None, rh * 0.3))
            if t.get('owner'): out.append(Tx(bx1 + 6, cy + rh / 2, t['owner'], SMALL, MUTED)) if bx1 + 60 < x1 else None
            out.append(Ln(x, cy + rh, x1, cy + rh, '#F1F3F5', 1)); cy += rh
    taken = []  # label extents per line: a label that would overlap an earlier one drops to the next line
    for m in spec.get('milestones', []):
        mx = X(m['at']); lw = T.width(m['label'], S, True); right = mx + 12 + lw > x1
        span = (mx - 12 - lw, mx + 7) if right else (mx - 7, mx + 12 + lw)
        row = 0
        while any(r == row and not (span[1] < a or span[0] > b) for r, a, b in taken): row += 1
        taken.append((row, *span)); my = cy + 12 + row * 20
        out.append(Ln(mx, y + head, mx, my, RISK, 1.2, True))
        out.append(Diamond(mx, my, 7, RISK)); out.append(Tx(mx - 12 if right else mx + 12, my, m['label'], S, RISK, True, 'end' if right else 'start'))
    if spec.get('today') is not None:
        tx = X(spec['today']); out.append(Ln(tx, y + head, tx, cy + 4, '#0F1115', 1.6))
        out.append(R(tx - T.width(spec.get('today_label', '当前'), SMALL, True) / 2 - 6, cy + 4, T.width(spec.get('today_label', '当前'), SMALL, True) + 12, 20, '#0F1115', None, 10))
        out.append(Tx(tx, cy + 14, spec.get('today_label', '当前'), SMALL, '#FFFFFF', True, 'middle'))
    return ''.join(o for o in out if o)

# ---------------------------------------------------------------- converging paths (discussion issue)
def _paths_parts(spec, w):
    sw_ = min(300, w * 0.3); gap = 10
    shs = [max(32, lines_h(c['text'], sw_ - 16, S, True) + 12) for c in spec['sources']]
    top = [c for c in spec.get('callouts', []) if c.get('near') == 'top']; bot = [c for c in spec.get('callouts', []) if c.get('near') != 'top']
    cws = [min(w - 20, T.width(c['text'], S, True) * 1.05 + 28) for c in bot]
    chs = [lines_h(c['text'], cw - 24, S, True) + 10 for c, cw in zip(bot, cws)]
    return top, bot, cws, chs, sum(shs) + (len(shs) - 1) * gap, (34 if top else 0), sum(10 + ch for ch in chs), shs

def _paths_measure(spec, w):
    *_, block, top_h, bot_h, _ = _paths_parts(spec, w); return top_h + block + bot_h + 4

@kind('paths', measure=_paths_measure)
def paths(spec, box, gid, mode):
    """Several entry routes converging on one condition, then the next step; dashed callouts mark what is unclear.
    spec: sources [{text, hl}], target {text, sub}, end {text}, callouts [{text, near: 'top'|'bottom'}]."""
    x, y, w, h = box; src = spec['sources']
    sw_ = min(300, w * 0.3); gap = 10
    top, bot, cws, chs, block, top_h, bot_h, shs = _paths_parts(spec, w)
    ty = y + top_h + max(0, (h - top_h - bot_h - block) / 2)
    out = []
    tx0 = x + sw_ + 110; tw = min(300, w * 0.3); tgt_h = 56; tgy = ty + block / 2 - tgt_h / 2
    sy = ty - gap
    for s, sh in zip(src, shs):
        sy += gap; hl = s.get('hl')
        out.append(R(x, sy, sw_, sh, BRAND if hl else '#F3F4F6', None if hl else '#D5DADF', 8))
        out.append(Tx(x + sw_ / 2, sy + sh / 2, s['text'], S, '#FFFFFF' if hl else INK, True, 'middle', sw_ - 16))
        out.append(Ln(x + sw_, sy + sh / 2, tx0, tgy + tgt_h / 2, BRAND if hl else '#B8BFC6', 2 if hl else 1.5))
        sy += sh
    out.append(R(tx0, tgy, tw, tgt_h, '#FCE9D6', '#F2B65C', 10, False, 1.5))
    out.append(Tx(tx0 + tw / 2, tgy + (18 if spec['target'].get('sub') else tgt_h / 2), spec['target']['text'], S, '#8A5300', True, 'middle', tw - 16))
    if spec['target'].get('sub'): out.append(Tx(tx0 + tw / 2, tgy + 40, spec['target']['sub'], S, '#8A5300', False, 'middle', tw - 16))
    if spec.get('end'):
        ex = tx0 + tw + 110; out.append(Arrow(tx0 + tw, tgy + tgt_h / 2, ex, tgy + tgt_h / 2, '#0F1115', 2, 10))
        out.append(Dot(ex + 14, tgy + tgt_h / 2, 7, BRAND)); out.append(Tx(ex + 14, tgy + tgt_h / 2 - 22, spec['end']['text'], S, INK, True, 'middle'))
    for c in top:
        cw = T.width(c['text'], S, True) + 24
        out.append(R(x + sw_ + 30, y, cw, 28, '#FFF6F5', RISK, 6, True)); out.append(Tx(x + sw_ + 42, y + 14, c['text'], S, RISK, True))
    by = ty + block
    for c, cw, ch in zip(bot, cws, chs):
        by += 10
        out.append(R(x, by, cw, ch, '#FFF6F5', RISK, 6, True)); out.append(Tx(x + 12, by + ch / 2, c['text'], S, RISK, True, 'start', cw - 24))
        by += ch
    return ''.join(out)
