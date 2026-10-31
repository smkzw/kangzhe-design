"""More diagram kinds: forest plot, Kaplan–Meier curve, CONSORT flow, risk heat grid, architecture layers, funnel,
hub and spokes, 2×2 quadrant. Same conventions as diagram_kinds.py: content text 16 px (12 pt), axis ticks and scale
marks 14 px; geometry is native shapes in PPTX and inline SVG in HTML (forest and KM use ECharts in HTML)."""
import math
from .diagrams import kind, text, icon, f
from .tree import TOK, INK, BODY, MUTED, RISK, BRAND
from . import text as T
from .diagram_kinds import R, Ln, Arrow, Diamond, Dot, Tx, lines_h, S, SMALL, TINT, EDGE, SOLID, CAT

GRID, AXIS = '#E7EBEE', '#9AA1A8'
COMP = TOK['charts']['comparator']

def W(s, size=S, bold=False): return T.width(T.plain(s), size, bold)

def P(points, stroke, sw=2, dash=False, fill='none'):
    d = 'M' + ' L'.join(f'{f(px)} {f(py)}' for px, py in points)
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"' + (' stroke-dasharray="5 4"' if dash else '') + ' stroke-linejoin="round"/>'

def series_colors(series):
    out, slot = [], 0
    for s in series:
        if s.get('role') == 'comparator': out.append(COMP)
        else: out.append(s.get('color') or CAT[slot % len(CAT)]); slot += 1
    return out

# ---------------------------------------------------------------- forest plot
def _forest_cols(spec, w):
    lab = min(w * 0.34, max(W(r['label'], S, r.get('header') or r.get('overall')) + (0 if r.get('header') else 18) for r in spec['rows']) + 16)
    nw = 64 if any('n' in r for r in spec['rows']) else 0
    vw = max(W(_ci(r), S) for r in spec['rows'] if 'est' in r) + 20
    return lab, nw, vw

def _ci(r):
    if 'est' not in r: return ''
    return r.get('text') or f'{r["est"]:.2f} ({r["lo"]:.2f}–{r["hi"]:.2f})'

def _forest_rows(spec, w):
    """Label lines per row decide its height: a long subgroup name wraps inside the label column and its row grows."""
    lab, *_ = _forest_cols(spec, w)
    return [lines_h(r['label'], lab - (8 if r.get('header') or r.get('overall') else 26), S, bool(r.get('header') or r.get('overall'))) + 8 for r in spec['rows']]

def _forest_measure(spec, w):
    return 30 + sum(max(30, n) for n in _forest_rows(spec, w)) + 58

@kind('forest', measure=_forest_measure)
def forest(spec, box, gid, mode):
    """Subgroup forest plot. spec: rows [{label, n, est, lo, hi, text, header, overall}], ref (1), log (true),
    ticks, favours [left, right], heads [subgroup, n, estimate]. The squares are one colour; the overall row is a diamond."""
    x, y, w, h = box; rows = spec['rows']; ref = spec.get('ref', 1); log = spec.get('log', True)
    lab, nw, vw = _forest_cols(spec, w)
    px0, px1 = x + lab + nw + 16, x + w - vw - 16
    vals = [v for r in rows if 'est' in r for v in (r['lo'], r['est'], r['hi'])] + [ref]
    if log and min(vals) <= 0: raise ValueError('森林图对数轴要求估计值与区间都 > 0；差值类指标请设 "log": false')
    ticks = spec.get('ticks') or ([0.25, 0.5, 1, 2, 4] if log else None)
    if ticks is None:
        lo, hi = min(vals), max(vals); step = (hi - lo) / 4 or 1; ticks = [round(lo + i * step, 2) for i in range(5)]
    lo, hi = min(ticks + vals), max(ticks + vals)
    tf = (lambda v: math.log(v)) if log else (lambda v: v)
    X = lambda v: px0 + (tf(v) - tf(lo)) / ((tf(hi) - tf(lo)) or 1) * (px1 - px0)
    head = 30; axis_h = 58
    need = _forest_rows(spec, w)
    rh = max(24, min(36, (h - head - axis_h - sum(max(0, n - 30) for n in need)) / max(1, len(rows))))
    hs = [max(rh, n) for n in need]; ys = [sum(hs[:i]) for i in range(len(hs))]
    top = y + max(0, (h - head - axis_h - sum(hs)) / 2)
    heads = spec.get('heads', ['亚组', 'n', spec.get('measure', 'HR (95% CI)')])
    out = [Tx(x, top + 14, heads[0], S, INK, True)]
    if nw: out.append(Tx(x + lab + nw - 6, top + 14, heads[1], S, INK, True, 'end'))
    out.append(Tx(x + w, top + 14, heads[2], S, INK, True, 'end'))
    out.append(Ln(x, top + head - 2, x + w, top + head - 2, '#D5DADF', 1))
    y0 = top + head; y1 = y0 + sum(hs)
    for i in range(len(rows)):
        if i % 2 == 0: out.append(R(px0, y0 + ys[i], px1 - px0, hs[i], '#F7F8F9', None, 0))
    out.append(Ln(X(ref), y0 - 4, X(ref), y1 + 4, '#5F6B76', 1.5, True))
    color = spec.get('color', BRAND)
    for i, r in enumerate(rows):
        cy = y0 + ys[i] + hs[i] / 2; hd, ov = r.get('header'), r.get('overall')
        out.append(Tx(x + (0 if hd or ov else 18), cy, r['label'], S, INK if hd or ov else BODY, bool(hd or ov), 'start', lab - (8 if hd or ov else 26)))
        if nw and 'n' in r: out.append(Tx(x + lab + nw - 6, cy, str(r['n']), S, BODY, False, 'end'))
        if 'est' not in r: continue
        out.append(Ln(X(r['lo']), cy, X(r['hi']), cy, INK if ov else '#3D4650', 1.6))
        if ov: out.append(Diamond(X(r['est']), cy, 9, RISK if r.get('tone') == 'risk' else '#B85C00'))
        else:
            s = 9; out.append(R(X(r['est']) - s / 2, cy - s / 2, s, s, color, None, 1))
        out.append(Tx(x + w, cy, _ci(r), S, INK if ov else BODY, bool(ov), 'end'))
    ay = y1 + 8; out.append(Ln(px0, ay, px1, ay, AXIS, 1))
    for t in ticks:
        out.append(Ln(X(t), ay, X(t), ay + 5, AXIS, 1)); out.append(Tx(X(t), ay + 16, (f'{t:g}'), SMALL, MUTED, False, 'middle'))
    fav = spec.get('favours')
    if fav:
        out.append(Tx(X(ref) - 10, ay + 40, '← ' + fav[0], SMALL, MUTED, False, 'end'))
        out.append(Tx(X(ref) + 10, ay + 40, fav[1] + ' →', SMALL, MUTED, False, 'start'))
    return ''.join(out)

# ---------------------------------------------------------------- Kaplan–Meier
def _km_risk_h(spec): return (26 + 24 * len(spec['series'])) if spec.get('at_risk') else 0

@kind('km')
def km(spec, box, gid, mode):
    """Kaplan–Meier step curves with censor ticks and an at-risk table aligned to the time axis.
    spec: series [{name, points [[t, s%]], censor [t], role}], xmax, xstep, xlabel, ylabel ('%'), ymin (0),
    at_risk {times [t], rows [[n…] per series]}, median (draws the 50 % guide)."""
    x, y, w, h = box; ser = spec['series']; cols = series_colors(ser)
    lab_w = max(W(s['name'], S) for s in ser) + 24 if spec.get('at_risk') else 56
    risk_h = _km_risk_h(spec); legend_h = 30
    px0, px1 = x + max(56, lab_w), x + w - 16
    py0, py1 = y + legend_h + 8, y + h - risk_h - 44
    xmax = spec['xmax']; xstep = spec.get('xstep', max(1, int(xmax / 6 + 0.5))); ymin = spec.get('ymin', 0)  # = JS Math.round
    X = lambda t: px0 + t / xmax * (px1 - px0)
    Y = lambda s: py1 - (s - ymin) / (100 - ymin) * (py1 - py0)
    out = []
    for v in range(int(ymin), 101, 20 if 100 - ymin > 50 else 10):
        out.append(Ln(px0, Y(v), px1, Y(v), GRID, 1)); out.append(Tx(px0 - 8, Y(v), f'{v}', SMALL, MUTED, False, 'end'))
    out.append(Ln(px0, py1, px1, py1, AXIS, 1.2))
    t = 0
    while t <= xmax + 1e-9:
        out.append(Ln(X(t), py1, X(t), py1 + 5, AXIS, 1)); out.append(Tx(X(t), py1 + 16, f'{t:g}', SMALL, MUTED, False, 'middle')); t += xstep
    out.append(Tx((px0 + px1) / 2, py1 + 36, spec.get('xlabel', '时间（月）'), SMALL, MUTED, False, 'middle'))
    out.append(Tx(px0 - 8, py0 - 14, spec.get('ylabel', '%'), SMALL, MUTED, False, 'end'))
    if spec.get('median'): out.append(Ln(px0, Y(50), px1, Y(50), '#B8BFC6', 1, True))
    lx = px1
    for s, c in reversed(list(zip(ser, cols))):  # legend, right-aligned on the top line
        tw = W(s['name'], S); lx -= tw + 30
        out.append(Ln(lx, y + 14, lx + 20, y + 14, c, 3)); out.append(Tx(lx + 26, y + 14, s['name'], S, INK, False))
        lx -= 18
    for s, c in zip(ser, cols):
        pts, prev = [], None
        for tt, sv in s['points']:
            if prev is not None: pts.append((X(tt), Y(prev)))
            pts.append((X(tt), Y(sv))); prev = sv
        out.append(P(pts, c, 2.4))
        for ct in s.get('censor', []):  # a censor tick sits on the step that is current at that time
            sv = ([v for tt, v in s['points'] if tt <= ct] or [s['points'][0][1]])[-1]
            out.append(Ln(X(ct), Y(sv) - 5, X(ct), Y(sv) + 5, c, 1.6))
    ar = spec.get('at_risk')
    if ar:
        ty = py1 + 54; out.append(Tx(x, ty, '风险人数', SMALL, MUTED, True))
        for k, (s, c) in enumerate(zip(ser, cols)):
            ry = ty + 24 * (k + 1)
            out.append(Ln(x, ry, x + 14, ry, c, 3)); out.append(Tx(x + 20, ry, s['name'], SMALL, INK, False, 'start', lab_w - 24))
            for tt, n in zip(ar['times'], ar['rows'][k]): out.append(Tx(X(tt), ry, str(n), SMALL, BODY, False, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- CONSORT subject flow
def _box_h(lines_txt, bw):
    return sum(lines_h(t, bw - 20, S, b) for t, b in lines_txt) + 16

def _consort_lines(b):
    out = [(b['text'] + (f'（n={b["n"]}）' if 'n' in b else ''), True)]
    if b.get('inline') and b.get('items'): return out + [('；'.join(b['items']), False)]  # reasons on one line
    return out + [('· ' + it, False) for it in b.get('items', [])]

def _consort_geo(spec, w):
    arms = spec['arms']; na = len(arms); gap = 28
    aw = min(360, (w - gap * (na - 1)) / na); cw = min(380, w * 0.42)
    cx = max(cw / 2, w * 0.36) if spec.get('excluded') else w / 2  # the main column sits left of centre to leave the side box room
    sw_ = min(440, w - cx - 30)
    top = [spec['enrolled'], spec['randomized']]
    th = [_box_h(_consort_lines(b), cw) for b in top]
    ex = spec.get('excluded'); eh = _box_h(_consort_lines(ex), sw_) if ex else 0
    steps = max(len(a['steps']) for a in arms)
    sh = [max(_box_h(_consort_lines(a['steps'][i]), aw) if i < len(a['steps']) else 0 for a in arms) for i in range(steps)]
    mid = max(30, eh + 16)
    return aw, cw, sw_, gap, th, eh, sh, mid, cx

def _consort_measure(spec, w):
    aw, cw, sw_, gap, th, eh, sh, mid, _ = _consort_geo(spec, w)
    return th[0] + mid + th[1] + 34 + sum(sh) + 22 * (len(sh) - 1) + 4

@kind('consort', measure=_consort_measure)
def consort(spec, box, gid, mode):
    """Subject flow: enrolled → (excluded, on the side) → randomised → one column per arm with its steps (allocated,
    discontinued, analysed). spec: enrolled, excluded, randomized {text, n, items}, arms [{steps [{text, n, items, tone}]}]."""
    x, y, w, h = box; arms = spec['arms']; na = len(arms)
    aw, cw, sw_, gap, th, eh, sh, mid, cx = _consort_geo(spec, w)
    need = _consort_measure(spec, w); cy = y + max(0, (h - need) / 2); cx += x
    out = []
    def box_(bx, by, bw, b, bh, tone='muted'):
        out.append(R(bx, by, bw, bh, '#FFFFFF' if tone == 'muted' else TINT.get(tone, tone), EDGE.get(tone, '#D5DADF'), 8, False, 1.3))
        ty = by + 8
        for t_, bold in _consort_lines(b):
            svg, hh = text(bx + 10, ty, t_, S, INK if bold else BODY, bold, 'start', bw - 20, 1.3); out.append(svg); ty += hh
    box_(cx - cw / 2, cy, cw, spec['enrolled'], th[0], 'brand')
    y_r = cy + th[0] + mid
    out.append(Arrow(cx, cy + th[0], cx, y_r - 2, '#5F6B76', 1.6, 8))
    if spec.get('excluded'):
        ey = cy + th[0] + (mid - eh) / 2; ex0 = cx + 30
        out.append(Arrow(cx, ey + eh / 2, ex0 - 2, ey + eh / 2, '#5F6B76', 1.4, 7))
        box_(ex0, ey, sw_, spec['excluded'], eh, 'risk')
    box_(cx - cw / 2, y_r, cw, spec['randomized'], th[1], 'brand')
    total = na * aw + (na - 1) * gap; ax0 = x + (w - total) / 2
    by = y_r + th[1] + 14
    centers = [ax0 + i * (aw + gap) + aw / 2 for i in range(na)]
    out.append(Ln(cx, y_r + th[1], cx, by, '#5F6B76', 1.6)); out.append(Ln(centers[0], by, centers[-1], by, '#5F6B76', 1.6))
    sy = by + 20
    for i, a in enumerate(arms):
        out.append(Arrow(centers[i], by, centers[i], sy - 2, '#5F6B76', 1.6, 8))
    for k, hh in enumerate(sh):
        for i, a in enumerate(arms):
            if k >= len(a['steps']): continue
            st = a['steps'][k]
            box_(ax0 + i * (aw + gap), sy, aw, st, hh, st.get('tone', 'muted'))
            if k < len(sh) - 1 and k + 1 < len(a['steps']): out.append(Arrow(centers[i], sy + hh, centers[i], sy + hh + 20, '#5F6B76', 1.4, 7))
        sy += hh + 22
    return ''.join(out)

# ---------------------------------------------------------------- risk heat grid
@kind('riskgrid')
def riskgrid(spec, box, gid, mode):
    """Likelihood × impact grid (3×3 or 5×5) tinted by score, risks as numbered discs.
    spec: x_ticks, y_ticks (low → high), x_label, y_label, risks [{id, x, y}] (1-based cells)."""
    x, y, w, h = box; xt, yt = spec['x_ticks'], spec['y_ticks']; nx, ny = len(xt), len(yt)
    lw = max(W(t, SMALL) for t in yt) + 34; bh = 46
    gx0, gy0 = x + lw, y + 6; side = min((w - lw - 6) / nx, (h - bh - 6) / ny)
    gx0 += max(0, (w - lw - side * nx) / 2) * 0; gw, gh = side * nx, side * ny
    out = []
    for i in range(nx):
        for j in range(ny):
            score = (i + 1) / nx * (j + 1) / ny
            fill = '#FCEDEC' if score >= 0.5 else '#FFF1DE' if score >= 0.2 else '#E8F1E4'
            out.append(R(gx0 + i * side + 2, gy0 + (ny - 1 - j) * side + 2, side - 4, side - 4, fill, None, 8))
    for j, t in enumerate(yt): out.append(Tx(gx0 - 10, gy0 + (ny - 1 - j) * side + side / 2, t, SMALL, MUTED, False, 'end'))
    for i, t in enumerate(xt): out.append(Tx(gx0 + i * side + side / 2, gy0 + gh + 16, t, SMALL, MUTED, False, 'middle'))
    out.append(Tx(gx0 + gw / 2, gy0 + gh + 38, spec.get('x_label', '影响程度'), S, INK, True, 'middle'))
    out.append(Tx(x, gy0 - 0 + 10, spec.get('y_label', '发生可能'), SMALL, INK, True, 'start'))
    cells = {}
    for r in spec['risks']: cells.setdefault((r['x'], r['y']), []).append(r)
    for (cx_, cy_), rs in cells.items():
        for k, r in enumerate(rs):
            off = (k - (len(rs) - 1) / 2) * 30
            px = gx0 + (cx_ - 1) * side + side / 2 + off; py = gy0 + (ny - cy_) * side + side / 2
            score = cx_ / nx * cy_ / ny
            out.append(Dot(px, py, 13, RISK if score >= 0.5 else '#B85C00' if score >= 0.2 else SOLID['ok']))
            out.append(Tx(px, py, r['id'], SMALL, '#FFFFFF', True, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- architecture layers
def _chip_rows(items, w):
    rows, cur, used = [], [], 0
    for it in items:
        cwid = W(it, S) + 28
        if cur and used + cwid + 10 > w: rows.append(cur); cur, used = [], 0
        cur.append((it, cwid)); used += cwid + 10
    if cur: rows.append(cur)
    return rows

def _layers_geo(spec, w):
    side = spec.get('side'); sw_ = 150 if side else 0
    lw = max(W(l['name'], S, True) for l in spec['layers']) + 36
    cw = w - lw - (sw_ + 14 if side else 0) - 24
    hs = [max(56, len(_chip_rows(l['items'], cw)) * 44 + 12) for l in spec['layers']]
    return sw_, lw, cw, hs

def _layers_measure(spec, w):
    _, _, _, hs = _layers_geo(spec, w); return sum(hs) + 10 * (len(hs) - 1)

@kind('layers', measure=_layers_measure)
def layers(spec, box, gid, mode):
    """Layered architecture: one band per layer (name on the left, module chips on the right), an optional vertical
    cross-cutting bar. spec: layers [{name, sub, items, tone}] top → bottom, side {name, items}."""
    x, y, w, h = box; side = spec.get('side')
    sw_, lw, cw, hs = _layers_geo(spec, w)
    extra = max(0, h - sum(hs) - 10 * (len(hs) - 1)); hs = [hh + extra / len(hs) for hh in hs]
    out = []; cy = y
    for i, (l, hh) in enumerate(zip(spec['layers'], hs)):
        t = l.get('tone', ['brand', 'soft', 'blue', 'ok', 'muted'][i % 5])
        out.append(R(x, cy, w - (sw_ + 14 if side else 0), hh, TINT.get(t, t), EDGE.get(t), 10, False, 1.2))
        out.append(R(x, cy, lw, hh, SOLID.get(t, BRAND), None, 10))
        out.append(Tx(x + lw / 2, cy + hh / 2 - (10 if l.get('sub') else 0), l['name'], S, '#FFFFFF', True, 'middle', lw - 12))
        if l.get('sub'): out.append(Tx(x + lw / 2, cy + hh / 2 + 12, l['sub'], S, '#FFFFFF', False, 'middle', lw - 12))
        rows = _chip_rows(l['items'], cw); ry = cy + (hh - len(rows) * 44 + 8) / 2
        for row in rows:
            rx = x + lw + 14
            for it, cwid in row:
                out.append(R(rx, ry, cwid, 36, '#FFFFFF', EDGE.get(t), 8, False, 1)); out.append(Tx(rx + cwid / 2, ry + 18, it, S, INK, False, 'middle'))
                rx += cwid + 10
            ry += 44
        cy += hh + 10
    if side:
        sx = x + w - sw_; th = cy - 10 - y
        out.append(R(sx, y, sw_, th, '#F3F4F6', '#D5DADF', 10, False, 1.2))
        out.append(Tx(sx + sw_ / 2, y + 26, side['name'], S, INK, True, 'middle', sw_ - 16))
        iy = y + 56
        for it in side.get('items', []):
            svg, hh = text(sx + 12, iy, it, S, BODY, False, 'start', sw_ - 24, 1.3); out.append(svg); iy += hh + 10
    return ''.join(out)

# ---------------------------------------------------------------- funnel
@kind('funnel')
def funnel(spec, box, gid, mode):
    """Stages narrowing top → bottom, value in the band, step conversion on the right.
    spec: stages [{label, value, text}], unit."""
    x, y, w, h = box; st = spec['stages']; n = len(st); unit = spec.get('unit', '')
    conv_w = 120; fw = w - conv_w; gap = 6; bh = (h - gap * (n - 1)) / n
    top_w, bot_w = fw, fw * 0.36
    out = []
    for i, s in enumerate(st):
        w0 = top_w - (top_w - bot_w) * i / n; w1 = top_w - (top_w - bot_w) * (i + 1) / n
        cx = x + fw / 2; by = y + i * (bh + gap)
        col = [BRAND, '#F2A33A', '#E9B262', '#EFC48A', '#F4D5AC', '#F8E3C8'][min(i, 5)]
        pts = [(cx - w0 / 2, by), (cx + w0 / 2, by), (cx + w1 / 2, by + bh), (cx - w1 / 2, by + bh)]
        out.append(f'<path d="M{" L".join(f"{f(a)} {f(b)}" for a, b in pts)} Z" fill="{col}"/>')
        dark = i < 2
        label = f'{s["label"]}  {s["value"]:,}{unit}'
        out.append(Tx(cx, by + bh / 2 - (10 if s.get('text') else 0), label, S, '#FFFFFF' if dark else INK, True, 'middle', w1 - 16))
        if s.get('text'): out.append(Tx(cx, by + bh / 2 + 13, s['text'], S, '#FFFFFF' if dark else BODY, False, 'middle', w1 - 16))
        if i:
            pct = s['value'] / st[i - 1]['value'] * 100 if st[i - 1]['value'] else 0
            out.append(Tx(x + fw + 12, by - gap / 2, f'↓ {pct:.0f}%', S, RISK if pct < 50 else INK, True, 'start'))
    return ''.join(out)

# ---------------------------------------------------------------- hub and spokes
def _hub_geo(spec, w):
    nodes = spec['nodes']; left = nodes[: (len(nodes) + 1) // 2]; right = nodes[(len(nodes) + 1) // 2:]
    bw = min(340, (w - 300) / 2)
    nh = [lines_h(n_['title'], bw - 62, S, True) + (lines_h(n_['text'], bw - 62, S) if n_.get('text') else 0) + 20 for n_ in nodes]
    return left, right, bw, nh

def _hub_measure(spec, w):
    left, right, bw, nh = _hub_geo(spec, w)
    return max(sum(nh[:len(left)]) + 14 * (len(left) - 1), sum(nh[len(left):]) + 14 * (len(right) - 1), 220)

@kind('hub', measure=_hub_measure)
def hub(spec, box, gid, mode):
    """One centre (platform, goal, molecule) with 4–8 satellites split left and right, joined by connectors.
    spec: center {title, sub}, nodes [{title, text, icon}]."""
    x, y, w, h = box; left, right, bw, nh = _hub_geo(spec, w)
    cx, cy = x + w / 2, y + h / 2; r = min(100, h / 2 - 10)
    out = [Dot(cx, cy, r + 10, '#FFF1DE'), Dot(cx, cy, r, BRAND)]
    c = spec['center']
    out.append(Tx(cx, cy - (12 if c.get('sub') else 0), c['title'], S, '#FFFFFF', True, 'middle', 2 * r - 20))
    if c.get('sub'): out.append(Tx(cx, cy + 16, c['sub'], S, '#FFFFFF', False, 'middle', 2 * r - 20))
    def column(items, hs, bx, side):
        tot = sum(hs) + 14 * (len(hs) - 1); by = y + (h - tot) / 2; spare = (h - tot) / max(1, len(hs) + 1)
        by = y + spare; step_gap = spare if len(hs) > 1 else 0
        for n_, hh in zip(items, hs):
            ny = by + hh / 2
            ax = bx + bw if side == 'l' else bx
            out.append(P([(ax, ny), ((ax + cx) / 2, ny), (cx + (-r if side == 'l' else r) * 0.8, cy + (ny - cy) * 0.35)], '#E9B262', 1.6))
            out.append(R(bx, by, bw, hh, '#FFFFFF', '#F2B65C', 10, False, 1.2))
            out.append(icon(n_.get('icon', 'circle-check'), bx + 12, by + 10, 34, BRAND, mode, disc=True))
            svg, th = text(bx + 54, by + 10, n_['title'], S, INK, True, 'start', bw - 62, 1.3); out.append(svg)
            if n_.get('text'):
                svg, _ = text(bx + 54, by + 10 + th, n_['text'], S, BODY, False, 'start', bw - 62, 1.3); out.append(svg)
            by += hh + max(14, step_gap)
    column(left, nh[:len(left)], x, 'l'); column(right, nh[len(left):], x + w - bw, 'r')
    return ''.join(out)

# ---------------------------------------------------------------- 2×2 quadrant
@kind('quadrant')
def quadrant(spec, box, gid, mode):
    """Two axes, four tinted quadrants with names, items placed as labelled dots (x, y in 0–1).
    spec: x_label, y_label, x_ends [low, high], y_ends, names [top-left, top-right, bottom-left, bottom-right],
    points [{label, x, y, tone}]."""
    x, y, w, h = box; lw = 28
    gx0, gy0, gw, gh = x + lw, y + 4, w - lw - 4, h - 52
    mx, my = gx0 + gw / 2, gy0 + gh / 2
    fills = ['#FFF8EE', '#FFF1DE', '#F7F8F9', '#FFF8EE']  # top-right (high, high) is the warm one
    out = [R(qx + 2, qy + 2, gw / 2 - 4, gh / 2 - 4, fl, None, 8) for (qx, qy), fl in zip([(gx0, gy0), (mx, gy0), (gx0, my), (mx, my)], fills)]
    names = spec.get('names', [])
    for k, nm in enumerate(names):
        qx = gx0 + (k % 2) * gw / 2; qy = gy0 + (k // 2) * gh / 2
        out.append(Tx(qx + (gw / 2 - 14 if k % 2 else 14), qy + 22, nm, S, '#8A5300' if k == 1 else MUTED, True, 'end' if k % 2 else 'start'))
    out.append(Arrow(gx0, gy0 + gh, gx0 + gw, gy0 + gh, '#5F6B76', 1.6, 8)); out.append(Arrow(gx0, gy0 + gh, gx0, gy0, '#5F6B76', 1.6, 8))
    xe, ye = spec.get('x_ends', ['低', '高']), spec.get('y_ends', ['低', '高'])
    out.append(Tx(gx0, gy0 + gh + 16, xe[0], SMALL, MUTED, False, 'start')); out.append(Tx(gx0 + gw - 12, gy0 + gh + 16, xe[1], SMALL, MUTED, False, 'end'))
    out.append(Tx(gx0 + gw / 2, gy0 + gh + 38, spec.get('x_label', ''), S, INK, True, 'middle'))
    out.append(Tx(x + 2, gy0 + gh - 10, ye[0], SMALL, MUTED, False, 'start')); out.append(Tx(x + 2, gy0 + 16, ye[1], SMALL, MUTED, False, 'start'))
    out.append(Tx(x + 2, my, spec.get('y_label', ''), SMALL, INK, True, 'start', 24))
    for p in spec['points']:
        px, py = gx0 + p['x'] * gw, gy0 + (1 - p['y']) * gh; t = p.get('tone', 'brand')
        out.append(Dot(px, py, 8, SOLID.get(t, BRAND), '#FFFFFF'))
        right = p['x'] < 0.75
        out.append(Tx(px + (14 if right else -14), py, p['label'], S, INK, False, 'start' if right else 'end'))
    return ''.join(out)
