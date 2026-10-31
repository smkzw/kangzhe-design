"""Figures inside template pages: native tables and charts, and drawn diagrams (diagrams.py).

PPTX: tables and charts are ppt-master native replacement objects — a visible SVG fallback drawn from the same data
plus the JSON payload (upstream native-data-interface §2, SVG-first). Run upstream stamp_native_fallbacks.py --write
before the final checker. HTML-PPT: tables are <table>, charts mount through KZCharts (ECharts, 05 CHART-01) from
`collect()`'d data, diagrams are inline SVG drawn by the same code as the PPTX shapes.
"""
from html import escape
import json, math
from . import text as T
from .tree import TOK, C, INK, BODY, runs_html, u

CH = TOK['charts']
FONT = 'Microsoft YaHei'
_COLLECT = {}

def collect():
    """Chart data printed by html() since the last call (for window.KZ_DECK_DATA)."""
    out = dict(_COLLECT); _COLLECT.clear(); return out

def f(n):
    return f'{n:.2f}'.rstrip('0').rstrip('.')

def palette(series):
    cat = list(CH['categorical']); out = []; slot = 0
    for s in series:
        if s.get('color'): out.append(s['color'])
        elif s.get('role') == 'comparator': out.append(CH['comparator'])
        elif s.get('department'): out.append(TOK['departments'][s['department']]['color'])
        else: out.append(cat[slot % len(cat)]); slot += 1
    return out

# ---------------------------------------------------------------- tables
# spec: columns (leaf header cells), optional groups (an upper header row of {'text', 'span'}), rows; a cell is a
# string or {'text', 'span', 'tone': 'brand'|'risk'|'tint'|'muted', 'align': 'l'|'c'|'r', 'mark': 'dot'|'key'}.
# widths (relative), numeric (right-aligned column indexes), center (centred column indexes), first_bold (default
# True), first_fill (tint the first column: key–value tables), size (px; default the secondary role).
TONE_FILL = {'brand': '#FFF1DE', 'risk': '#FCEDEC', 'tint': '#FFF8EE', 'muted': '#F3F4F6'}
HEAD_FILL = '#FFF4E2'; RULE = '#E1E5E9'; MARK = {'dot': '●', 'key': '●'}

def _cell(c):
    return dict(c) if isinstance(c, dict) else {'text': '' if c is None else str(c)}

def _grid_row(cells, ncol):
    """→ [(col, span, cell)] anchors of one row."""
    out, col = [], 0
    for c in cells:
        c = _cell(c); span = max(1, int(c.get('span', 1)))
        if col >= ncol or span > ncol - col:
            raise ValueError(f'表格行比列数（{ncol}）多出单元格，会丢字：{[_cell(x).get("text", "") for x in cells]}')
        out.append((col, span, c)); col += span
    return out

def table_layout(spec, box, grow=True):
    x, y, w, h = box
    ncol = len(spec.get('columns') or spec['rows'][0])
    size = spec.get('size', TOK['type_px']['secondary']); lead = 1.35; pad_x, pad_y = 10, 6
    weights = spec.get('widths') or [1] * ncol
    cw = [w * k / sum(weights) for k in weights]
    num, center = set(spec.get('numeric', [])), set(spec.get('center', []))
    def align(col, c):
        return c.get('align') or ('r' if col in num else 'c' if col in center else 'l')
    def lines(c, col, span, bold):
        if c.get('mark'): return [[(MARK[c['mark']], frozenset())]]
        width = sum(cw[col:col + span]) - 2 * pad_x
        return T.wrap(c.get('text', ''), width, size, bold, keep_space=True)
    head_rows = [] if spec.get('header') is False else ([_grid_row(spec['groups'], ncol)] if spec.get('groups') else []) + [_grid_row(spec['columns'], ncol)]
    body_rows = [_grid_row(r, ncol) for r in spec['rows']]
    fb = spec.get('first_bold', True)
    def lay(row, header):
        cells = [(col, span, c, lines(c, col, span, header or (col == 0 and fb) or c.get('bold', False)), align(col, c)) for col, span, c in row]
        return cells, max([len(l) for *_, l, _ in cells] + [1]) * size * lead + 2 * pad_y
    head = [lay(r, True) for r in head_rows]; body = [lay(r, False) for r in body_rows]
    hh = [hgt for _, hgt in head]; rh = [hgt for _, hgt in body]
    need = sum(hh) + sum(rh)
    if grow and need < h and rh:  # fill the box: rows grow evenly, at most 1.7× (03 TYPE-02: nothing pinned to the top)
        k = min(1.7, (h - sum(hh)) / sum(rh)); rh = [r * k for r in rh]
    return {'x': x, 'y': y, 'w': w, 'cw': cw, 'size': size, 'lead': lead, 'pad': (pad_x, pad_y), 'head': [c for c, _ in head],
            'body': [c for c, _ in body], 'hh': hh, 'rh': rh, 'need': need, 'ncol': ncol, 'first_fill': spec.get('first_fill', False), 'fb': fb}

def _line_svg(x, y, lines, size, lead, color, bold=False, anchor='start'):
    from .svg import run_svg
    if not lines or not lines[0]: return ''
    a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
    b = ' font-weight="bold"' if bold else ''
    out = f'<text x="{f(x)}" y="{f(y)}" font-size="{f(size)}" fill="{color}"{b}{a}>' + ''.join(run_svg(t, st, color, bold) for t, st in lines[0])
    for ln in lines[1:]:
        out += f'<tspan x="{f(x)}" dy="{f(size * lead)}">' + ''.join(run_svg(t, st, color, bold) for t, st in ln) + '</tspan>'
    return out + '</text>'

PT = TOK['layout']['templates']['pptx_table']

def _payload_cell(c, bold=False, align='l', color=None, fill=None, span=1, header=False):
    """Every cell is one paragraph with an explicit line spacing (tokens.layout.templates.pptx_table): PowerPoint's
    single CJK line is taller than the solver's, and the row would grow past the drawn one."""
    ls = PT['line_spacing_percent']
    if c.get('mark'):
        out = {'paragraphs': [{'text': MARK[c['mark']], 'line_spacing_percent': ls}], 'color': BRAND_HEX if c['mark'] == 'dot' else C['risk']}
    else:
        text = c.get('text', '')
        runs = [{'text': t, **({'bold': True} if (bold or 'bold' in st or 'risk' in st) else {}), **({'color': C['risk']} if 'risk' in st else {}),
                 **({'underline': True} if 'underline' in st else {})} for t, st in T.parse(text) if t]
        rich = len(runs) > 1 or any('underline' in r or ('color' in r) for r in runs)
        out = {'paragraphs': [{'runs': runs, 'line_spacing_percent': ls} if rich else {'text': T.plain(text), 'line_spacing_percent': ls}]}
        if bold and not rich: out['bold'] = True
        if color and not rich: out['color'] = color
    out['align'] = {'l': 'l', 'c': 'ctr', 'r': 'r'}[align]
    if fill: out['fill'] = fill
    if span > 1: out['col_span'] = span
    return out

BRAND_HEX = C['brand']

def _cell_fill(t, col, c, header):
    if header: return None
    if c.get('tone'): return TONE_FILL[c['tone']]
    if col == 0 and t['first_fill']: return TONE_FILL['tint']
    return None

def table_svg(spec, box, gid):
    from .svg import baseline
    t = table_layout(spec, box); x, y = t['x'], t['y']; size, lead = t['size'], t['lead']; px, py = t['pad']
    parts = [f'<rect id="{gid}-header" x="{f(x)}" y="{f(y)}" width="{f(t["w"])}" height="{f(sum(t["hh"]))}" fill="{HEAD_FILL}"/>'] if t['hh'] else []
    xs = [x]
    for v in t['cw']: xs.append(xs[-1] + v)
    def draw_row(cells, top, hgt, header):
        for col, span, c, ln, al in cells:
            cx0, cx1 = xs[col], xs[col + span]
            fill = _cell_fill(t, col, c, header)
            if fill: parts.append(f'<rect x="{f(cx0)}" y="{f(top)}" width="{f(cx1 - cx0)}" height="{f(hgt)}" fill="{fill}"/>')
            th = len(ln) * size * lead; ty = top + (hgt - th) / 2
            tx = {'l': cx0 + px, 'c': (cx0 + cx1) / 2, 'r': cx1 - px}[al]
            mark = c.get('mark')
            color = (BRAND_HEX if mark == 'dot' else C['risk']) if mark else INK if (header or col == 0) else BODY
            bold = header or (col == 0 and t['fb']) or bool(c.get('bold'))
            parts.append(_line_svg(tx, baseline(ty, size, lead), ln, size, lead, color, bold and not mark, {'l': 'start', 'c': 'middle', 'r': 'end'}[al]))
    cy = y
    for i, (cells, hgt) in enumerate(zip(t['head'], t['hh'])):
        draw_row(cells, cy, hgt, True); cy += hgt
        if i < len(t['hh']) - 1:
            for col, span, *_ in cells:  # a group header rules only under itself
                parts.append(f'<line x1="{f(xs[col] + 4)}" y1="{f(cy)}" x2="{f(xs[col + span] - 4)}" y2="{f(cy)}" stroke="#F2C98A" stroke-width="1"/>')
    for cells, hgt in zip(t['body'], t['rh']):
        parts.append(f'<line x1="{f(x)}" y1="{f(cy)}" x2="{f(x + t["w"])}" y2="{f(cy)}" stroke="{RULE}" stroke-width="1"/>')
        draw_row(cells, cy, hgt, False); cy += hgt
    parts.append(f'<line x1="{f(x)}" y1="{f(cy)}" x2="{f(x + t["w"])}" y2="{f(cy)}" stroke="{RULE}" stroke-width="1"/>')
    total = cy - y
    NONE, SOLID = {'style': 'none'}, {'style': 'solid', 'color': RULE, 'width': 1}
    GROUP = {'style': 'solid', 'color': '#F2C98A', 'width': 1}
    def prow(cells, header, last_head=False):
        out = []
        for col, span, c, ln, al in cells:
            bold = header or (col == 0 and t['fb']) or bool(c.get('bold'))
            cell = _payload_cell(c, bold, al, INK if (header or col == 0) else None, _cell_fill(t, col, c, header), span, header)
            if header:  # the fallback rules only under a header row: body rule (last header row) or the group rule
                cell['borders'] = {'left': NONE, 'right': NONE, 'top': NONE, 'bottom': SOLID if last_head else GROUP}
            out.append(cell); out += [{'merge_continuation': True}] * (span - 1)
        return out
    hrows = [prow(c, True, i == len(t['head']) - 1) for i, c in enumerate(t['head'])]; brows = [prow(c, False) for c in t['body']]
    payload = {'schema': 'ppt-master.semantic-table.v2', 'name': gid, 'x': round(x, 2), 'y': round(y, 2), 'width': round(t['w'], 2), 'height': round(total, 2),
               **({'columns': hrows[0]} if hrows else {}), 'rows': hrows[1:] + brows,
               'column_widths': [round(v, 2) for v in t['cw']], 'row_heights': [round(v, 2) for v in t['hh'] + t['rh']],
               'style': {'font_family': FONT, 'font_size': size, **({'header_fill': HEAD_FILL, 'header_text': INK} if hrows else {}), 'body_text': BODY, 'band_row': False,
                         'valign': 'middle', 'border_color': RULE, 'border_width': 1,
                         'padding': {'left': PT['pad_x'], 'right': PT['pad_x'], 'top': PT['pad_y'], 'bottom': PT['pad_y']}}}
    payload['defaults'] = {'cell': {'borders': {'left': NONE, 'right': NONE, 'top': SOLID, 'bottom': SOLID}}}  # horizontal rules only, as drawn
    if len(hrows) > 1: payload['header_rows'] = len(hrows)
    return (f'<g id="{gid}" data-pptx-bounds="{f(x)} {f(y)} {f(t["w"])} {f(total)}" data-pptx-replace-with="table">'
            f'<metadata type="application/json">{escape(json.dumps(payload, ensure_ascii=False), quote=False)}</metadata>' + ''.join(parts) + '</g>')

def table_html(spec, gid):
    ncol = len(spec.get('columns') or spec['rows'][0]); num, center = set(spec.get('numeric', [])), set(spec.get('center', [])); fb = spec.get('first_bold', True)
    ff = spec.get('first_fill', False); weights = spec.get('widths') or [1] * ncol
    def cell(tag, col, span, c, header):
        al = c.get('align') or ('r' if col in num else 'c' if col in center else 'l')
        cls = [f'is-{al}'] + ([f'is-{c["tone"]}'] if c.get('tone') else []) + (['is-key'] if col == 0 and ff and not header else [])
        if c.get('mark'): body = f'<span class="kzl-dot is-{c["mark"]}" aria-label="是">●</span>'
        else:
            body = runs_html(c.get('text', ''))
            if not header and col == 0 and fb: body = f'<b>{body}</b>'
        return f'<{tag} class="{" ".join(cls)}"' + (f' colspan="{span}"' if span > 1 else '') + f'>{body}</{tag}>'
    heads = [] if spec.get('header') is False else ([_grid_row(spec['groups'], ncol)] if spec.get('groups') else []) + [_grid_row(spec['columns'], ncol)]
    thead = ''.join('<tr>' + ''.join(cell('th', col, span, c, True) for col, span, c in r) + '</tr>' for r in heads)
    tbody = ''.join('<tr>' + ''.join(cell('td', col, span, c, False) for col, span, c in _grid_row(r, ncol)) + '</tr>' for r in spec['rows'])
    cols = ''.join(f'<col style="width:{100 * k / sum(weights):.2f}%">' for k in weights)
    return (f'<div class="kzl-figure is-table"><table class="kzl-table kzl-secondary" id="{gid}"><colgroup>{cols}</colgroup>'
            + (f'<thead>{thead}</thead>' if thead else '') + f'<tbody>{tbody}</tbody></table></div>')

# ---------------------------------------------------------------- charts
def nice_axis(lo, hi, ticks=5):
    lo, hi = min(0, lo), max(0, hi); span = (hi - lo) or 1
    raw = span * 1.1 / ticks; mag = 10 ** math.floor(math.log10(raw)); fr = raw / mag
    step = (1 if fr <= 1 else 2 if fr <= 2 else 5 if fr <= 5 else 10) * mag
    mn = math.floor(lo * (1.08 if lo < 0 else 1) / step) * step; mx = math.ceil(hi * 1.08 / step) * step
    return mn, mx, step

def fmt(v, dec=None):
    if v is None: return ''
    if dec is None: dec = 0 if float(v).is_integer() else 1
    return f'{v:.{dec}f}'

def tick(v):
    """An axis tick as PowerPoint prints it: no trailing zeros (0.50 → 0.5, 1.0 → 1)."""
    t = f'{v:.6f}'.rstrip('0').rstrip('.')
    return '0' if t in ('-0', '') else t

def chart_svg(spec, box, gid):
    kind = spec['kind']
    if kind == 'doughnut': return doughnut_svg(spec, box, gid)
    x, y, w, h = box; size = TOK['type_px']['chart_label']
    cats = spec['categories']; series = spec['series']; cols = palette(series)
    horizontal = kind == 'bar'; stacked = spec.get('stacked', False)
    vals = [v for s in series for v in s['values'] if v is not None]
    if stacked: vals += [sum(s['values'][i] or 0 for s in series) for i in range(len(cats))]
    mn, mx, step = spec.get('axis', {}).get('min'), spec.get('axis', {}).get('max'), spec.get('axis', {}).get('step')
    a, b, c = nice_axis(min(vals), max(vals))
    explicit = mn is not None or mx is not None
    mn = a if mn is None else mn; mx = b if mx is None else mx
    if step is None and explicit:  # an explicit range gets its own tidy step (70–100 → 5 or 10), not the 0-based one
        raw = (mx - mn) / 5; mag = 10 ** math.floor(math.log10(raw)); fr = raw / mag
        c = (1 if fr <= 1 else 2 if fr <= 2 else 5 if fr <= 5 else 10) * mag
    step = c if step is None else step
    dec = spec.get('decimals')
    # plot area: left room for value ticks (or category labels on a bar chart), bottom for category labels
    if horizontal:
        lab_w = max(T.width(cc, size) for cc in cats) + 14
        pa = [x + lab_w, y + 8, w - lab_w - 44, h - 8 - size * 1.8]
    else:
        tick_w = max(T.width(tick(mn + i * step), size) for i in range(int(round((mx - mn) / step)) + 1)) * 1.1 + 14
        cat_h = size * 1.45 * max(len(T.wrap(cc, (w - tick_w) / len(cats) - 8, size)) for cc in cats) + 10
        pa = [x + tick_w, y + size * 1.6, w - tick_w - 8, h - size * 1.6 - cat_h]
    px, py, pw, ph = pa
    V = (lambda v: px + (v - mn) / (mx - mn) * pw) if horizontal else (lambda v: py + ph - (v - mn) / (mx - mn) * ph)
    out = [f'<g id="{gid}-chartArea">', f'<g id="{gid}-grid" stroke="{CH["grid"]}" stroke-width="1">']
    nt = int(round((mx - mn) / step))
    for i in range(nt + 1):
        v = mn + i * step
        if horizontal: out.append(f'<line x1="{f(V(v))}" y1="{f(py)}" x2="{f(V(v))}" y2="{f(py + ph)}"/>')
        elif i: out.append(f'<line x1="{f(px)}" y1="{f(V(v))}" x2="{f(px + pw)}" y2="{f(V(v))}"/>')
    out.append('</g>')
    out.append(f'<g font-size="{size}" fill="{CH["label"]}"' + (' text-anchor="middle"' if horizontal else ' text-anchor="end"') + '>')
    for i in range(nt + 1):
        v = mn + i * step
        if horizontal: out.append(f'<text x="{f(V(v))}" y="{f(py + ph + size * 1.4)}">{tick(v)}</text>')
        else: out.append(f'<text x="{f(px - 8)}" y="{f(V(v) + size * 0.35)}">{tick(v)}</text>')
    out.append('</g>')
    z = V(min(max(0, mn), mx))  # the category axis sits on the zero line (bars of negative values grow away from it), or the range floor
    axis = (f'<line id="{gid}-axis" x1="{f(z)}" y1="{f(py)}" x2="{f(z)}" y2="{f(py + ph)}" stroke="{CH["axis"]}" stroke-width="2"/>' if horizontal
            else f'<line id="{gid}-axis" x1="{f(px)}" y1="{f(z)}" x2="{f(px + pw)}" y2="{f(z)}" stroke="{CH["axis"]}" stroke-width="2"/>')
    out.append(axis)
    out.append(f'<!-- chart-plot-area: object={gid} | {f(px)},{f(py)},{f(px + pw)},{f(py + ph)} -->')
    n = len(cats); slot = (ph if horizontal else pw) / n
    bar_series = [i for i, s in enumerate(series) if s.get('type', 'line' if kind == 'line' else 'column') != 'line']
    line_series = [i for i, s in enumerate(series) if s.get('type', 'line' if kind == 'line' else 'column') == 'line']
    nb = 1 if stacked else max(1, len(bar_series))
    bw = min(slot * 0.62 / nb, 46)
    labels = []
    for j in range(n):
        base_c = (py if horizontal else px) + slot * j + slot / 2
        acc = 0
        for k, si in enumerate(bar_series):
            v = series[si]['values'][j]
            if v is None: continue
            off = 0 if stacked else (k - (nb - 1) / 2) * bw
            v0, v1 = (acc, acc + v) if stacked else (0, v)
            neg = v < 0
            if horizontal:
                bx, by, bwid, bh = min(V(v0), V(v1)), base_c + off - bw / 2, abs(V(v1) - V(v0)), bw
                labels.append(((V(v1) - 6 if neg else V(v1) + 6), by + bw / 2 + size * 0.35, fmt(v, dec), 'end' if neg else 'start') if not stacked
                              else (bx + bwid / 2, by + bw / 2 + size * 0.35, fmt(v, dec), 'middle'))
            else:
                bx, by, bwid, bh = base_c + off - bw / 2, min(V(v0), V(v1)), bw, abs(V(v0) - V(v1))
                labels.append((bx + bw / 2, (by + bh + size * 1.1 if neg else by - 6) if not stacked else by + bh / 2 + size * 0.35, fmt(v, dec), 'middle'))
            out.append(f'<rect x="{f(bx)}" y="{f(by)}" width="{f(max(0.5, bwid))}" height="{f(max(0.5, bh))}" rx="{3 if not stacked else 0}" fill="{cols[si]}"/>')
            acc += v if stacked else 0
    for si in line_series:
        pts = [(px + slot * j + slot / 2, V(v)) if v is not None else None for j, v in enumerate(series[si]['values'])]
        seg = []
        for p in pts + [None]:
            if p: seg.append(p)
            elif seg:
                out.append(f'<polyline points="{" ".join(f"{f(a)},{f(b)}" for a, b in seg)}" fill="none" stroke="{cols[si]}" stroke-width="3"/>'); seg = []
        for j, p in enumerate(pts):
            if p:
                out.append(f'<circle cx="{f(p[0])}" cy="{f(p[1])}" r="4.5" fill="{cols[si]}"/>')
                labels.append((p[0], p[1] - 10, fmt(series[si]['values'][j], dec), 'middle'))
    if spec.get('labels', True):
        out.append(f'<g font-size="{size}" fill="{CH["label"]}">' + ''.join(f'<text x="{f(a)}" y="{f(b)}"' + (f' text-anchor="{an}"' if an != 'start' else '') + f'>{escape(t)}</text>' for a, b, t, an in labels) + '</g>')
    out.append(f'<g font-size="{size}" fill="{CH["label"]}"' + ('' if horizontal else ' text-anchor="middle"') + '>')
    for j, cc in enumerate(cats):
        cpos = (py if horizontal else px) + slot * j + slot / 2
        if horizontal: out.append(f'<text x="{f(px - 10)}" y="{f(cpos + size * 0.35)}" text-anchor="end">{escape(cc)}</text>')
        else:
            ln = T.wrap(cc, slot - 8, size)
            out.append(_line_svg(cpos, py + ph + size * 1.35, ln, size, 1.45, CH['label'], anchor='middle'))
    out.append('</g></g>')
    ntype = 'combo' if line_series and bar_series else ('line' if kind == 'line' else 'bar' if horizontal else 'column')
    payload = {'name': gid, 'x': round(x, 2), 'y': round(y, 2), 'width': round(w, 2), 'height': round(h, 2),
               'plot_area': {'x': round(px, 2), 'y': round(py, 2), 'width': round(pw, 2), 'height': round(ph, 2)}, 'type': ntype,
               # category labels at the low end, as drawn: with negative values PowerPoint's default (next_to) puts them on the zero line, inside the bars
               'categories': cats, 'axes': {'category': {'label_position': 'low'}, 'value': {'minimum': mn, 'maximum': mx, 'major_unit': step}},
               'style': {'colors': cols, 'axis_color': CH['axis'], 'grid_color': CH['grid'], 'text_color': CH['label'], 'font_family': FONT}}
    if ntype == 'combo':
        payload['series'] = [{'name': s['name'], 'values': s['values'], 'type': 'line' if i in line_series else 'column'} for i, s in enumerate(series)]
    else:
        payload['series'] = [{'name': s['name'], 'values': s['values']} for s in series]
        payload['grouping'] = 'stacked' if stacked else ('standard' if kind == 'line' else 'clustered')
    if kind == 'line': payload['line_style'] = 'lineMarker'
    if spec.get('labels', True) and ntype != 'combo':
        payload['data_labels'] = {'show_value': True, **({'number_format': '0.' + '0' * dec} if dec else {})}
    return (f'<g id="{gid}" data-pptx-bounds="{f(x)} {f(y)} {f(w)} {f(h)}" data-pptx-replace-with="chart">'
            f'<metadata type="application/json">{escape(json.dumps(payload, ensure_ascii=False), quote=False)}</metadata>' + ''.join(out) + '</g>')

def doughnut_svg(spec, box, gid):
    x, y, w, h = box; size = TOK['type_px']['chart_label']
    s = spec['series'][0]; vals = s['values']; cats = spec['categories']; tot = sum(v for v in vals if v)
    cols = spec.get('colors') or palette([{} for _ in vals])
    dec = spec.get('decimals'); unit = spec.get('unit', '')
    # the legend carries the values ("恶心 42%"): pie-family native charts take no data labels, and a companion note
    # under the ring collides with PowerPoint's legend, which it centres on the whole chart frame
    cats = [f'{c} {fmt(v, dec)}{unit if unit == "%" else ""}' for c, v in zip(cats, vals)]
    leg_w = max(T.width(c, size) for c in cats) * 1.1 + 30
    ring_w, ring_h = w - leg_w - 16, h
    r = min(ring_w, ring_h) / 2 - 4; cx, cy = x + ring_w / 2, y + ring_h / 2; ri = r * 0.62
    out = [f'<g id="{gid}-chartArea">']; a0 = -math.pi / 2
    for v, col in zip(vals, cols):
        a1 = a0 + 2 * math.pi * v / tot; large = 1 if a1 - a0 > math.pi else 0
        p = lambda rr, a: (cx + rr * math.cos(a), cy + rr * math.sin(a))
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p(r, a0), p(r, a1), p(ri, a1), p(ri, a0)
        out.append(f'<path d="M{f(x0)} {f(y0)} A{f(r)} {f(r)} 0 {large} 1 {f(x1)} {f(y1)} L{f(x2)} {f(y2)} A{f(ri)} {f(ri)} 0 {large} 0 {f(x3)} {f(y3)} Z" fill="{col}"/>')
        a0 = a1
    # legend at the right (category names, as the native legend prints them); values as a companion note below
    lh = size * 1.6; ly = cy - lh * len(cats) / 2; lx = x + w - leg_w
    out.append(f'<g id="{gid}-legend" font-size="{size}" fill="{CH["label"]}">')
    for i, (c, col) in enumerate(zip(cats, cols)):
        yy = ly + i * lh
        out.append(f'<rect x="{f(lx)}" y="{f(yy + lh / 2 - 6)}" width="12" height="12" rx="3" fill="{col}"/><text x="{f(lx + 20)}" y="{f(yy + lh / 2 + size * 0.35)}">{escape(c)}</text>')
    out.append('</g></g>')
    payload = {'name': gid, 'x': round(x, 2), 'y': round(y, 2), 'width': round(w, 2), 'height': round(h, 2), 'type': 'doughnut', 'hole_size': 62,
               'plot_area': {'x': round(cx - r, 2), 'y': round(cy - r, 2), 'width': round(2 * r, 2), 'height': round(2 * r, 2)},
               'show_legend': True, 'legend_position': 'r',
               'categories': cats, 'series': [{'name': s['name'], 'values': vals, 'point_colors': cols}], 'style': {'colors': cols, 'font_family': FONT}}
    return (f'<g id="{gid}" data-pptx-bounds="{f(x)} {f(y)} {f(w)} {f(h)}" data-pptx-replace-with="chart">'
            f'<metadata type="application/json">{escape(json.dumps(payload, ensure_ascii=False), quote=False)}</metadata>' + ''.join(out) + '</g>')

def chart_html(spec, gid, min_h):
    data = {'kind': spec['kind'],
            'unit': spec.get('unit', ''), 'categories': spec['categories'], 'decimals': spec.get('decimals'),
            'series': [{'id': s.get('id', f's{i}'), 'name': s['name'], 'values': s['values'], **{k: s[k] for k in ('role', 'department', 'color', 'type') if k in s}} for i, s in enumerate(spec['series'])],
            'description': spec.get('description', '')}
    if spec.get('stacked'): data['kind'] = 'stacked'; data['horizontal'] = spec['kind'] == 'bar'
    if any(s.get('type') == 'line' for s in spec['series']) and spec['kind'] != 'line': data['kind'] = 'combo'
    if spec.get('axis'): data['axis'] = {k2: v for k2, v in (('min', spec['axis'].get('min')), ('max', spec['axis'].get('max')), ('interval', spec['axis'].get('step'))) if v is not None}
    _COLLECT[gid] = data
    return f'<div class="kzl-figure" style="--min-h:{min_h:g}"><div class="kz-chart" data-kz-chart="{gid}" role="img" aria-label="{escape(spec.get("description", "图表"))}"></div></div>'

# ---------------------------------------------------------------- dispatch
def svg(kind, spec, box, gid):
    if kind == 'table': return table_svg(spec, box, gid)
    if kind == 'chart': return chart_svg(spec, box, gid)
    from . import diagrams
    body = diagrams.draw(kind, spec, box, gid, mode='pptx')
    x, y, w, h = box
    return f'<g id="{gid}" data-pptx-bounds="{f(x)} {f(y)} {f(w)} {f(h)}">{body}</g>'

ECHARTS_DIAGRAMS = ('forest', 'km')  # quantitative diagrams: native shapes in PPTX, ECharts in HTML (05 CHART-01)

def clinical_chart_html(kind, spec, gid, min_h):
    data = {'kind': kind, **{k: v for k, v in spec.items() if k not in ('kind', 'min_h')}}
    if kind == 'km': data['series'] = [{'id': s.get('id', f's{i}'), **s} for i, s in enumerate(spec['series'])]
    _COLLECT[gid] = data
    return f'<div class="kzl-figure" style="--min-h:{min_h:g}"><div class="kz-chart" data-kz-chart="{gid}" role="img" aria-label="{escape(spec.get("description", "图表"))}"></div></div>'

def html(kind, spec, gid, min_h, box=None):
    if kind == 'table': return table_html(spec, gid)
    if kind == 'chart': return chart_html(spec, gid, min_h)
    if kind in ECHARTS_DIAGRAMS: return clinical_chart_html(kind, spec, gid, min_h)
    from . import diagrams
    w, h = (box[2], box[3]) if box else (1168, min_h)
    body = diagrams.draw(kind, spec, [0, 0, w, h], gid, mode='html')
    return (f'<div class="kzl-figure" style="--min-h:{min_h:g}"><svg viewBox="0 0 {f(w)} {f(h)}" preserveAspectRatio="xMidYMid meet" '
            f'font-family="var(--kz-font)" role="img" aria-label="{escape(spec.get("description", ""))}">{body}</svg></div>')
