"""Flagship PPTX body language L1 「层叠纸板」(14 FLAG-12): clinical-family templates as native ppt-master SVG.

Data stands up like paper: strips with a lighter top face and one native shadow sit in recessed grooves, cards carry an
offset back sheet, milestones are two-facet gems. Plan bars use the facet arrows of the header badge (the L2 data bar the
user picked for Gantt pages). Every value comes from tokens.flagship.pptx_l1; the data contracts are the clinical ones
(safety_model, program_model, exposure_model, trialflow_model, landscape_model, efficacy_model, soa_model), so a page and its HTML/demo/stage siblings read the same numbers.

Templates (page-plan `template`, PPTX flagship only):
  flag-safety            butterfly strips (treat ← label → comparator) + insight tabs with numeral pairs   safety_butterfly
  flag-safety-dumbbell   claim column (hero difference, numbered notes) + dumbbell plot on the canvas        safety_dumbbell
  flag-program           lane card with facet arrows, gems, today line under everything + insight tabs     program_chevron
  flag-program-strip     the same plan as raised strips in grooves                                          program_strip
  flag-exposure          stepped strips per indication (cumulative bands light → deep) + count columns, a target card
                         per band (total numeral, groove gauge with the target tick, met / gap tag) + insight tabs    exposure_steps
  flag-exposure-plan     cumulative exposure on the development plan: the step chart (ICH E1 target, NDA verticals,
                         count at each NDA, first crossing) + a readiness card per indication × band       exposure_plan_board
  flag-trialflow         trial flow: shared periods as tall paper blocks, randomisation discs with spines, arm segments
                         as raised strips (sub-arms after a re-randomisation disc), endpoint gems on the week axis,
                         sub-studies as dashed pills + insight tabs                                                trialflow_board
  flag-landscape         competitive landscape: one row per asset (ours tinted), the stage as facet arrows up to the
                         current stage, efficacy and safety as raised strips in grooves (best in accent, null as —)   landscape_rows
  flag-efficacy          efficacy summary: per endpoint type a section with its own axis through 0; per row the arms'
                         values and per treat arm a raised strip from 0 to the difference with the CI whisker (dashed when
                         the CI crosses 0), difference and P in columns                                         efficacy_board
  flag-soa               SoA at item level: period facet arrows over the visit columns (primary visits tinted), a key-
                         events row, study-drug / background strips, one row per assessment (sections in a left
                         column) with a mark per visit                                                             soa_board

Each function takes `pg` (anything with group(gid, x, y, w, h, inner, scene, effect, card=, figure=, **opt), role(role,
size, text, lh) and a `cards` list — the Page of examples/reference/pptx-flagship/build_svg.py) and a body box
(x, y, w, h); it returns the SVG of the body. Root framing (grids, today line, back sheets, panels) is emitted as
decoration primitives with stable ids; module groups never overlap (ppt-master canonical authoring). Text that does
not fit raises instead of shrinking (03 TYPE-03). Body text is ≥16 px (12 pt); axis, legend and milestone labels 14 px.
"""
from html import escape  # noqa: F401  (kept for callers that build markup next to these blocks)
import re
from . import text as KT, svg as KS
from .tree import TOK
from . import diagram_clinical as DC, diagram_scenes as DS
from .icon_pick import pick

F = TOK['flagship']; L1 = F['pptx_l1']; TY, INK, C = F['type_px'], F['ink'], TOK['colors']
CH = TOK['charts']; PH = CH['phases']; FLW = CH['flow']; TREAT, COMP, RISK = CH['categorical'][0], CH['comparator'], C['risk']
GT = TOK['gantt']['today']; NUM_INK = F['numeral']['stops'][-1][0]
TEMPLATES = ('flag-safety', 'flag-safety-dumbbell', 'flag-program', 'flag-program-strip', 'flag-exposure', 'flag-exposure-plan', 'flag-trialflow', 'flag-landscape', 'flag-efficacy', 'flag-soa')
mix, on_color = DC._mix, DC.on_color

def f(n): return f'{n:.1f}'.rstrip('0').rstrip('.')

def rgba(s):
    m = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', s)
    return (f'#{int(m[1]):02X}{int(m[2]):02X}{int(m[3]):02X}', float(m[4])) if m else (s, 1.0)

def darker(c, t):
    return '#' + ''.join(f'{round(int(c[i:i + 2], 16) * (1 - t)):02X}' for i in (1, 3, 5))

# ---------- defs ----------
def _lin(id_, stops, vertical=True):
    xy = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    return f'<linearGradient id="{id_}" {xy}>' + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in stops) + '</linearGradient>'

def _shadow(id_, s):
    return f'<filter id="{id_}"><feDropShadow dx="0" dy="{s["dy"]}" stdDeviation="{s["blur"]}" flood-color="{s["color"]}" flood-opacity="{s["alpha"]}"/></filter>'

def defs():
    """Gradients and the two native shadows of the language; put inside the page <defs>."""
    top = L1['strip_top']
    return (_lin('l1-treat', [(mix(TREAT, top), 0), (TREAT, 1)]) + _lin('l1-comp', [(mix(COMP, top), 0), (COMP, 1)])
            + ''.join(_lin(f'l1-ph{k}', [(mix(c, top), 0), (c, 1)]) for k, c in enumerate(PH))
            + ''.join(_lin(f'l1-fl-{k}', [(mix(FLW[k], top), 0), (FLW[k], 1)]) for k in DS.FLOW_KINDS if k != 'off')
            + _lin('l1-treat-h', [(mix(TREAT, top), 0), (TREAT, 1)]) + _lin('l1-comp-h', [(mix(COMP, top), 0), (COMP, 1)])
            + _lin('l1-token', [(c, o) for c, o in F['tile']['stops']]) + _lin('l1-hero', [(c, o) for c, o in F['numeral']['stops']])
            + _shadow('l1-strip', L1['strip_shadow']) + _shadow('l1-lift', L1['lift_shadow'])
            + (lambda sh: f'<filter id="l1-card"><feDropShadow dx="0" dy="{f(sh["dist_pt"] * 4 / 3)}" stdDeviation="{f(sh["blur_pt"] * 2 / 3)}" '
               f'flood-color="{sh["color"]}" flood-opacity="{sh["alpha"]}"/></filter>')(F['card']['pptx_shadow']))

# ---------- primitives ----------
_DK = [0]
def _id(p):
    _DK[0] += 1; return f'{p}-{_DK[0]}'

def deco(frag):
    """Root framing primitives: stable id + decoration role (outside every module zone)."""
    return re.sub(r'<(line|rect|path|circle) (?!id=)', lambda m: f'<{m[1]} id="{_id("l1d")}" data-pptx-role="decoration" ', frag)

def para(x, y, w, markup, size, color=None, bold=False, align='start', lead=1.35, max_lines=1):
    lines = KT.wrap(markup, w, size, bold)
    if len(lines) > max_lines: raise ValueError(f'放不下（{len(lines)} 行 > {max_lines}）：{KT.plain(markup)}')
    return KS.text_svg({'lines': lines, 'size': size, 'lead': lead, 'align': align, 'x': x, 'w': w, 'y': y,
                        'color': color or INK['body'], 'bold': bold}), len(lines) * size * lead

def text(*a, **k): return para(*a, **k)[0]
def tw(s, size, bold=False): return KT.width(KT.plain(s), size, bold)

def card(x, y, w, h, id_=None):
    bc, ba = rgba(F['card']['border']); i = f'id="{id_}" data-pptx-role="decoration" ' if id_ else ''
    return (f'<rect {i}x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{F["card"]["radius"]}" fill="{F["card"]["face"]}" '
            f'stroke="{bc}" stroke-opacity="{ba}" stroke-width="1" filter="url(#l1-card)"/>')

def sheet(x, y, w, h):
    o = L1['sheet_offset']
    return f'<rect id="{_id("l1sheet")}" data-pptx-role="decoration" x="{f(x + o)}" y="{f(y + o)}" width="{f(w)}" height="{f(h)}" rx="{F["card"]["radius"]}" fill="{L1["sheet"]}"/>'

def icon(name, x, y, size, color):
    return f'<use data-icon="kangzhe/{name}" x="{f(x)}" y="{f(y)}" width="{f(size)}" height="{f(size)}" fill="{color}"/>'

def hline(x, y, w): return f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + w)}" y2="{f(y)}" stroke="{F["line"]}" stroke-width="1"/>'

def token(cx, cy, r, ic, risk=False):
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{RISK if risk else "url(#l1-token)"}" filter="url(#l1-lift)"/>'
            + icon(ic, cx - r * .55, cy - r * .55, r * 1.1, '#FFFFFF'))

def pct(v): return f'{v:.1f}%'
def pp(v): return ('+' if v > 0 else '−' if v < 0 else '±') + f'{abs(v):.1f}'

# ---------- safety ----------
def _safety(data):
    m = DC.safety_model(data['safety']); ti, ci = m['treat'], m['comp']
    shown = [r for r in m['rows'] if any(r['values'])]
    none = [r for r in m['rows'] if not any(r['values'])]
    for r in m['rows']: r['name'] = r.get('short') or r['label']; r['p0'], r['p1'] = r['pct'][ti], r['pct'][ci]
    return m, shown, none

def _note(data, m, none):
    """The footnote: denominators, the flag threshold and every all-zero row ('无导致死亡的 TEAE')."""
    s = f'差值 ≥{f(m["flag"])} 个百分点标出；百分比分母为各组{data["safety"].get("set", "分析集")}人数'
    return s + ''.join(f'；无{r["label"]}' for r in none)

def _pair(x, y, m, key, ink=None):
    r = next(r for r in m['rows'] if r['key'] == key); out = ''
    for j, (v, col) in enumerate(((r['p0'], TREAT), (r['p1'], COMP))):
        xx = x + j * 130
        out += f'<circle cx="{f(xx + 5)}" cy="{f(y + 22)}" r="5" fill="{col}"/>'
        out += text(xx + 16, y + 2, 112, pct(v), 26, ink or (NUM_INK if j == 0 else INK['muted']), True, lead=1.3)
    return out

def _arms_legend(x_right, y, m, pill=True):
    out, x = '', x_right
    for a, col in ((m['arms'][m['comp']], COMP), (m['arms'][m['treat']], TREAT)):
        lab = f'{a["name"]} n={a["n"]}'; w = tw(lab, 16, True) + 30; x -= w
        if pill: out += f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="28" rx="14" fill="{mix(col, .86)}"/>'
        out += f'<circle cx="{f(x + 13)}" cy="{f(y + 14)}" r="5" fill="{col}"/>' + text(x + 22, y, w - 20, lab, 16, INK['title'], True, lead=28 / 16)
        x -= 8
    return out, x

def safety_butterfly(pg, data, box, gid='fs'):
    """flag-safety: treat strips grow left, comparator right, from a centred label column; differences ≥ flag get a tag;
    insights are paper tabs with a raised icon token and, when an insight names a `row`, the two rates as numerals."""
    m, rows, none = _safety(data); x0, y0, W, H = box; side = L1['side_w']; o = L1['sheet_offset']
    cw = W - side - TOK['flagship']['geometry']['gap'] - o; ch = H - o
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    leg, lx = _arms_legend(x0 + cw - 20, y0 + 17, m)
    head = text(x0 + 20, y0 + 16, lx - x0 - 30, data['title'], TY['card_title'], INK['title'], True, lead=1.3) + leg
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, 56, head, 0, 'entrance_fade')
    lab_w = 150; avail = cw - 40 - 84; cx = x0 + 20 + avail / 2; half = (avail - lab_w) / 2 - 72
    ry0 = y0 + 70; rh = (ch - 70 - 58) / len(rows); scale = half / max(10, (int(m['max'] / 10) + 1) * 10)
    if rh < 36: raise ValueError(f'flag-safety 一页最多放 {int((ch - 128) / 36)} 行，当前 {len(rows)} 行；拆页或改 flag-safety-dumbbell')
    body = ''
    for k, r in enumerate(rows):
        cy = ry0 + k * rh + rh / 2; bh = min(18, rh * .5); foc = r['key'] == m['focus']
        if foc: body += f'<rect x="{f(x0 + 14)}" y="{f(cy - rh / 2 + 2)}" width="{f(cw - 28)}" height="{f(rh - 4)}" rx="10" fill="{L1["focus_row"]}"/>'
        lx, rx = cx - lab_w / 2, cx + lab_w / 2
        for sd, val, grad in ((-1, r['p0'], 'l1-treat'), (1, r['p1'], 'l1-comp')):
            g0 = lx - 10 - half if sd < 0 else rx + 10
            body += f'<rect x="{f(g0)}" y="{f(cy - bh / 2 - 1)}" width="{f(half)}" height="{f(bh + 2)}" rx="{f(bh / 2 + 1)}" fill="{L1["groove"]}"/>'
            bw = max(val * scale, 2); bx = lx - 10 - bw if sd < 0 else rx + 10
            body += f'<rect x="{f(bx)}" y="{f(cy - bh / 2)}" width="{f(bw)}" height="{f(bh)}" rx="{f(bh / 2)}" fill="url(#{grad})" filter="url(#l1-strip)"/>'
            body += text(bx - 68 if sd < 0 else bx + bw + 8, cy - 11, 60, pct(val), 16, INK['title'] if foc else INK['body'], foc, 'end' if sd < 0 else 'start', lead=22 / 16)
        body += text(lx, cy - 11, lab_w, r['name'], 16, INK['title'], True, 'middle', lead=22 / 16)
        if abs(r['diff']) >= m['flag']:
            dl = pp(r['diff']); dw = tw(dl, 14, True) + 14; bg, ink = F['tag']['wait']
            body += f'<rect x="{f(x0 + cw - 20 - dw)}" y="{f(cy - 11)}" width="{f(dw)}" height="22" rx="11" fill="{bg}"/>'
            body += text(x0 + cw - 20 - dw, cy - 11, dw, dl, 14, ink, True, 'middle', lead=22 / 14)
    nt = _note(data, m, none)
    body += hline(x0 + 20, y0 + ch - 46, cw - 40) + text(x0 + 20, y0 + ch - 38, cw - 40, nt, 16, INK['muted'], lead=1.4)
    pg.role('body', 16, nt, 1.4)
    out += pg.group(f'{gid}-bars', x0 + 14, ry0, cw - 28, ch - 70, body, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'up'})
    sx = x0 + cw + o + TOK['flagship']['geometry']['gap']; gap = TOK['flagship']['geometry']['gap']; n = len(data['insights']); ih = (H - (n - 1) * gap) / n
    icons = pick(data['insights'])
    for k, it in enumerate(data['insights']):
        y = y0 + k * (ih + gap); risk = it.get('tone') == 'risk'
        c = card(sx, y, side, ih) + token(sx + 34, y + 32, 17, icons[k], risk)
        c += text(sx + 62, y + 19, side - 78, it['title'], TY['card_title'], INK['title'], True, lead=1.3)
        c += para(sx + 20, y + 58, side - 40, it['text'], 16, INK['body'], lead=1.4, max_lines=2)[0]
        if it.get('row'): c += _pair(sx + 20, y + ih - 46, m, it['row'])
        pg.role('card_title', TY['card_title'], it['title'], 1.3); pg.role('body', 16, it['text'], 1.4)
        out += pg.group(f'{gid}-in{k}', sx, y, side, ih, c, 2, 'entrance_rise_up', card=True)
    return out

def safety_dumbbell(pg, data, box, gid='fd'):
    """flag-safety-dumbbell: the claim column (focus difference as a gradient hero numeral, numbered notes between
    hairlines) and a dumbbell plot straight on the canvas (comparator dot → treat dot, both rates, difference column)."""
    m, rows, none = _safety(data); x0, y0, W, H = box; lw = L1['claim_w']
    foc = next((r for r in m['rows'] if r['key'] == m['focus']), max(rows, key=lambda r: abs(r['diff'])))
    big = pp(foc['diff']); bw = tw(big, 96, True)
    hero = text(x0, y0 + 4, lw, f'{foc["label"]}的组间差', 18, INK['kicker'], True, lead=1.3)
    hero += text(x0, y0 + 34, bw + 12, big, 96, 'url(#l1-hero)', True, lead=1.1)
    hero += text(x0 + bw + 10, y0 + 34 + 96 * 1.1 - 40, lw - bw - 10, '个百分点', 20, INK['title'], True, lead=1.3)
    a0, a1 = m['arms'][m['treat']]['name'], m['arms'][m['comp']]['name']
    hero += text(x0, y0 + 152, lw, f'{a0} {pct(foc["p0"])}，{a1} {pct(foc["p1"])}', 18, INK['body'], lead=1.4)
    pg.role('takeaway', 96, big, 1.1)
    out = pg.group(f'{gid}-hero', x0, y0, lw, 186, hero, 0, 'entrance_rise_up')
    iy = y0 + 200; n = len(data['insights']); ih = (y0 + H - iy) / n
    for k, it in enumerate(data['insights']):
        y = iy + k * ih; risk = it.get('tone') == 'risk'
        c = hline(x0, y + 4, lw) + text(x0, y + 14, 40, f'{k + 1:02d}', 20, RISK if risk else F['accent_ink'], True, lead=1.3)
        c += text(x0 + 44, y + 12, lw - 44, it['title'], TY['card_title'], INK['title'], True, lead=1.3)
        c += para(x0 + 44, y + 42, lw - 56, it['text'], 16, INK['body'], lead=1.4, max_lines=2)[0]
        pg.role('card_title', TY['card_title'], it['title'], 1.3); pg.role('body', 16, it['text'], 1.4)
        out += pg.group(f'{gid}-in{k}', x0, y, lw, ih, c, 2, 'entrance_fade')
    px = x0 + lw + 56; pw = x0 + W - px; lab_w = 170; tx0 = px + lab_w; tw_ = pw - lab_w - 166
    top = max(10, (int(m['max'] / 20) + 1) * 20); scale = tw_ / top
    leg, hx = '', px + pw
    for a, col in ((m['arms'][m['comp']], COMP), (m['arms'][m['treat']], TREAT)):
        w = tw(a['name'], 15, True) + 10; hx -= w
        leg += f'<circle cx="{f(hx - 12)}" cy="{f(y0 + 16)}" r="6" fill="{col}"/>' + text(hx, y0 + 5, w, a['name'], 15, INK['body'], True, lead=22 / 15); hx -= 34
    head = text(px, y0 + 2, hx - px - 10, data['title'], TY['card_title'], INK['title'], True, lead=1.3) + leg
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', px, y0, pw, 30, head, 0, 'entrance_fade')
    ry0 = y0 + 62; rh = (y0 + H - 64 - ry0) / len(rows); grid, body = '', ''
    if rh < 34: raise ValueError(f'flag-safety-dumbbell 一页最多放 {int((H - 126) / 34)} 行，当前 {len(rows)} 行；请拆页')
    for v in range(0, top + 1, 20):
        x = tx0 + v * scale
        grid += f'<line x1="{f(x)}" y1="{f(ry0 - 6)}" x2="{f(x)}" y2="{f(ry0 + rh * len(rows))}" stroke="{CH["grid"]}" stroke-width="1"/>'
        body += text(x - 30, ry0 - 30, 60, f'{v}%', 14, INK['muted'], align='middle', lead=1.3)
    out += deco(grid)
    body += text(px + pw - 90, ry0 - 30, 90, '差值', 14, INK['muted'], True, 'end', lead=1.3)
    for k, r in enumerate(rows):
        cy = ry0 + k * rh + rh / 2; fo = r['key'] == m['focus']
        if fo: body += f'<rect x="{f(px - 10)}" y="{f(cy - rh / 2 + 2)}" width="{f(pw + 10)}" height="{f(rh - 4)}" rx="6" fill="{L1["focus_row"]}"/>'
        body += text(px, cy - 11, lab_w - 10, r['name'], 16, INK['title'] if fo else INK['body'], fo, lead=22 / 16)
        a, b = tx0 + r['p1'] * scale, tx0 + r['p0'] * scale
        body += f'<line x1="{f(a)}" y1="{f(cy)}" x2="{f(b)}" y2="{f(cy)}" stroke="{mix(TREAT, .55)}" stroke-width="4" stroke-linecap="round"/>'
        body += f'<circle cx="{f(a)}" cy="{f(cy)}" r="6" fill="{COMP}" stroke="#FFFFFF" stroke-width="2"/>'
        body += f'<circle cx="{f(b)}" cy="{f(cy)}" r="7" fill="{TREAT}" stroke="#FFFFFF" stroke-width="2"/>'
        # both rates beside the dots: treat in ink, comparator muted — colour, not bold, so eight rows do not become eight emphases
        t0 = pct(r['p0']); w0 = tw(t0, 14) + 4; vx = max(a, b) + 12
        body += text(vx, cy - 10, w0, t0, 14, INK['title'], lead=20 / 14) + text(vx + w0, cy - 10, 80, f'/ {pct(r["p1"])}', 14, INK['muted'], lead=20 / 14)
        flag = abs(r['diff']) >= m['flag']; sz = 18 if flag else 16
        body += text(px + pw - 90, cy - 12, 90, pp(r['diff']), sz, F['accent_ink'] if flag else INK['muted'], True, 'end', lead=24 / sz)
    nt = _note(data, m, none).replace('标出', '用深橙标出')
    body += hline(px, y0 + H - 44, pw) + text(px, y0 + H - 36, pw, nt, 16, INK['muted'], lead=1.4); pg.role('body', 16, nt, 1.4)
    out += pg.group(f'{gid}-plot', px - 10, ry0 - 30, pw + 10, y0 + H - ry0 + 30, body, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    return out

# ---------- program ----------
def _years(M, x0, w):
    X = lambda t: x0 + (t - M['from']) / (M['to'] - M['from']) * w
    return X, [(y, X(y * 4), X(y * 4 + 4)) for y in range(M['from'] // 4, (M['to'] - 1) // 4 + 1)]

def _ms_t(ln, mm):
    end = mm['t'] + mm['tw']
    if any(abs(b['e'] - end) < 1e-9 for b in ln['bars']): return end
    if any(abs(b['s'] - mm['t']) < 1e-9 for b in ln['bars']): return mm['t']
    return mm['t'] + mm['tw'] / 2

def _split(b, now):
    if now is None or b['e'] <= now: return [(b['s'], b['e'], False)]
    if b['s'] >= now: return [(b['s'], b['e'], True)]
    return [(b['s'], now, False), (now, b['e'], True)]

def _today(M, spec, X, y0, y1, ly, gid, pg):
    if M['today'] is None: return ''
    now = M['today'] + M['today_w'] / 2; x = X(now); gran = M['granularity']; tv = spec.get('today')
    tu = gran if tv in (None, 'auto') else DC.tspan(tv, 'today')[2]
    lab = '当前 ' + DC.ttext(M['today'], tu if DC.GRANS.index(tu) < DC.GRANS.index(gran) else gran)
    lw = tw(lab, 14, True) + 16
    line = deco(f'<line x1="{f(x)}" y1="{f(y0)}" x2="{f(x)}" y2="{f(y1)}" stroke="{GT["line"]}" stroke-width="{GT["width"]}" stroke-dasharray="{" ".join(str(v) for v in GT["dash"])}"/>')
    pill = (f'<rect x="{f(x - lw / 2)}" y="{f(ly)}" width="{f(lw)}" height="22" rx="11" fill="{GT["pill"]}"/>'
            + text(x - lw / 2, ly, lw, lab, 14, GT['text'], True, 'middle', lead=22 / 14))
    return line + pg.group(f'{gid}-now', x - lw / 2, ly, lw, 22, pill, 0, 'entrance_fade', figure=True)

def _label_slots(items):
    """Milestone labels in one row: shift right past an earlier label instead of overlapping it."""
    used, out = [], []
    for x, w in items:
        lx = x - w / 2
        for a, b in used:
            if lx < b + 6 and lx + w > a - 6: lx = b + 6
        used.append((lx, lx + w)); out.append(lx)
    return out

def gem(cx, cy, r, past, risk, focus):
    col = RISK if risk else L1['gem']
    lt, dk = (mix(col, .25), darker(col, .12)) if past else ('#FFFFFF', '#FFFFFF')
    out = f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r + 6)}" fill="{mix(col, .8)}"/>' if focus else ''
    return out + (f'<path d="M {f(cx)} {f(cy - r)} L {f(cx - r)} {f(cy)} L {f(cx)} {f(cy + r)} Z" fill="{lt}" stroke="{col}" stroke-width="1.5"/>'
                  f'<path d="M {f(cx)} {f(cy - r)} L {f(cx + r)} {f(cy)} L {f(cx)} {f(cy + r)} Z" fill="{dk}" stroke="{col}" stroke-width="1.5"/>')

def chevron(x0, x1, cy, h, fill, notch, point, stroke=None):
    k = h * .32
    pts = [(x0, cy - h / 2), (x1 - (k if point else 0), cy - h / 2)] + ([(x1, cy)] if point else [(x1, cy - h / 2), (x1, cy + h / 2)])
    pts += [(x1 - (k if point else 0), cy + h / 2), (x0, cy + h / 2)] + ([(x0 + k, cy)] if notch else [])
    st = f' stroke="{stroke}" stroke-width="1.2" stroke-dasharray="4 3"' if stroke else ''
    return f'<path d="M {" L ".join(f"{f(a)} {f(b)}" for a, b in pts)} Z" fill="{fill}"{st}/>'

def _program(pg, data, box, gid, style):
    M = DC.program_model(data['program']); spec = data['program']; x0, y0, W, H = box; o = L1['sheet_offset']; gap = F['geometry']['gap']
    lanes = M['visible']; cw = W - o; ins = data.get('insights') or []
    ch = H - o - (L1['insight_h'] + gap if ins else 0)
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    lab_w = 190; px0 = x0 + lab_w + 18; pw = x0 + cw - 22 - px0; ly0 = y0 + 54; rh = (ch - 54 - 46) / len(lanes)
    if rh < 50: raise ValueError(f'{"flag-program" if style == "chevron" else "flag-program-strip"} 一页最多放 {int((ch - 100) / 50)} 条泳道，当前 {len(lanes)} 条；收起上级泳道或拆页')
    X, yrs = _years(M, px0, pw); grid, axis = '', ''
    for yr, a, b in yrs:
        axis += text(a, y0 + 16, b - a, str(yr), 16, INK['title'], True, 'middle', lead=1.4)
        grid += f'<line x1="{f(a)}" y1="{f(ly0 - 6)}" x2="{f(a)}" y2="{f(ly0 + rh * len(lanes))}" stroke="{CH["grid"]}" stroke-width="1"/>'
    out += deco(grid) + _today(M, spec, X, ly0 - 6, ly0 + rh * len(lanes), ly0 + rh * len(lanes) + 8, gid, pg)
    out += pg.group(f'{gid}-axis', px0, y0 + 16, pw, 26, axis, 0, 'entrance_fade', figure=True)
    now = None if M['today'] is None else M['today'] + M['today_w'] / 2; bh = L1['plan_bar_h']
    for k, ln in enumerate(lanes):
        top = ly0 + k * rh; cy = top + rh * .66; mid = top + rh / 2; g = ''
        g += text(x0 + 20 + 14 * ln['depth'], mid - 22, lab_w - 14 * ln['depth'], ln['name'], 18, INK['title'], True, lead=1.3)
        if ln.get('note'): g += text(x0 + 20 + 14 * ln['depth'], mid + 1, lab_w, ln['note'], 14, INK['muted'], lead=1.4)
        bars = ln['bars'] or ln.get('summary') or []
        if style == 'strip': g += f'<rect x="{f(px0)}" y="{f(cy - bh / 2 - 3)}" width="{f(pw)}" height="{f(bh + 6)}" rx="{f(bh / 2 + 3)}" fill="{L1["groove_plan"]}"/>'
        for bi, b in enumerate(bars):
            col = b.get('color') or PH[b['pi']]; pieces = _split(b, now)
            for pj, (s, e, plan) in enumerate(pieces):
                a, z = X(s) + 1, X(e) - 1
                if style == 'chevron':
                    g += chevron(a, z, cy, bh, mix(col, .62) if plan else col, bi > 0 and pj == 0, pj == len(pieces) - 1, col if plan else None)
                elif plan:
                    g += f'<rect x="{f(a)}" y="{f(cy - bh / 2)}" width="{f(z - a)}" height="{f(bh)}" rx="{f(bh / 2)}" fill="{mix(col, .6)}" stroke="{col}" stroke-width="1.2" stroke-dasharray="4 3"/>'
                else:
                    g += f'<rect x="{f(a)}" y="{f(cy - bh / 2)}" width="{f(z - a)}" height="{f(bh)}" rx="{f(bh / 2)}" fill="url(#l1-ph{b["pi"]})" filter="url(#l1-strip)"/>'
            a, z = X(b['s']), X(b['e']); lab = b.get('label') or b['phase']
            if tw(lab, 15, True) + 30 < z - a: g += text(a + 14, cy - 10, z - a - 28, lab, 15, on_color(col), True, lead=20 / 15)
        ms = ln['milestones'] if ln['bars'] else ln.get('summary_ms', [])
        xs = [X(_ms_t(ln, mm)) for mm in ms]; lws = [tw(mm['label'], 14, mm['key'] == spec.get('focus')) + 12 for mm in ms]
        for mm, mx, lx, lw in zip(ms, xs, _label_slots(list(zip(xs, lws))), lws):
            fo = mm['key'] == spec.get('focus')
            g += gem(mx, cy, L1['gem_r'], now is not None and mm['t'] < now, mm.get('risk'), fo)
            g += text(lx, cy - 34, lw, mm['label'], 14, RISK if mm.get('risk') else INK['body'], fo, 'middle', lead=1.3)
        pg.role('chart_label', 18, ln['name'], 1.3)
        out += pg.group(f'{gid}-lane{k}', x0 + 14, top, cw - 28, rh, g, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    leg, lx, ly = '', x0 + 20, y0 + ch - 30
    for k in M['used']:
        nm = M['phases'][k]
        sw = (chevron(lx, lx + 22, ly + 10, 13, PH[k], False, True) if style == 'chevron' else f'<rect x="{f(lx)}" y="{f(ly + 4)}" width="22" height="12" rx="6" fill="url(#l1-ph{k})"/>')
        leg += sw + text(lx + 28, ly - 1, tw(nm, 14) + 8, nm, 14, INK['body'], lead=22 / 14); lx += tw(nm, 14) + 48
    if now is not None and any(b['e'] > now for ln in lanes for b in ln['bars']):
        leg += f'<rect x="{f(lx)}" y="{f(ly + 4)}" width="22" height="12" rx="6" fill="{mix(PH[2], .6)}" stroke="{PH[2]}" stroke-dasharray="4 3"/>' + text(lx + 28, ly - 1, 40, '计划', 14, INK['body'], lead=22 / 14); lx += 76
    out += pg.group(f'{gid}-legend', x0 + 20, ly - 2, lx - x0 - 20, 22, leg, 1, 'entrance_fade', figure=True)
    if ins:
        iy = y0 + ch + o + gap; ih = y0 + H - iy; iw = (W - (len(ins) - 1) * gap) / len(ins); icons = pick(ins)
        for k, it in enumerate(ins):
            x = x0 + k * (iw + gap); risk = it.get('tone') == 'risk'
            ttl, txt = DC.bind_text(it['title'], spec), DC.bind_text(it['text'], spec)
            c = card(x, iy, iw, ih) + token(x + 30, iy + 24, 15, icons[k], risk)
            c += text(x + 56, iy + 9, iw - 70, ttl, TY['card_title'], INK['title'], True, lead=1.3)
            c += para(x + 56, iy + 38, iw - 70, txt, 16, INK['body'], lead=1.35, max_lines=2)[0]
            pg.role('card_title', TY['card_title'], ttl, 1.3); pg.role('body', 16, txt, 1.35)
            out += pg.group(f'{gid}-in{k}', x, iy, iw, ih, c, 2, 'entrance_rise_up', card=True)
    return out

def program_chevron(pg, data, box, gid='fp'):
    """flag-program: lanes in one card on a back sheet; phases are facet arrows (solid before today, light dashed after);
    gems pinned on the bar; today line is the lowest grey dash; insight tabs underneath."""
    return _program(pg, data, box, gid, 'chevron')

def program_strip(pg, data, box, gid='fq'):
    """flag-program-strip: the same plan as raised gradient strips in recessed grooves."""
    return _program(pg, data, box, gid, 'strip')

# ---------- exposure ----------
def _insight_tabs(pg, ins, x0, iy, W, ih, gid, scene, bind=lambda t: t):
    gap = F['geometry']['gap']; iw = (W - (len(ins) - 1) * gap) / len(ins); out = ''; icons = pick(ins)
    for k, it in enumerate(ins):
        x = x0 + k * (iw + gap); risk = it.get('tone') == 'risk'; ttl, txt = bind(it['title']), bind(it['text'])
        c = card(x, iy, iw, ih) + token(x + 30, iy + 24, 15, icons[k], risk)
        c += text(x + 56, iy + 9, iw - 70, ttl, TY['card_title'], INK['title'], True, lead=1.3)
        c += para(x + 56, iy + 38, iw - 70, txt, 16, INK['body'], lead=1.35, max_lines=2)[0]
        pg.role('card_title', TY['card_title'], ttl, 1.3); pg.role('body', 16, txt, 1.35)
        out += pg.group(f'{gid}-in{k}', x, iy, iw, ih, c, scene, 'entrance_rise_up', card=True)
    return out

def exposure_steps(pg, data, box, gid='fe'):
    """flag-exposure: one card of indication rows — each a groove with the cumulative bands stacked as paper strips
    (any → ≥26 w → ≥52 w, light → deep, each a subset of the one before), counts and patient-years in columns, the totals
    underneath; beside it one target card (per band: total numeral, a groove gauge with the target tick, met / gap tag);
    insight tabs under both."""
    m = DS.exposure_model(data['exposure']); spec = data['exposure']; x0, y0, W, H = box
    o, gap, side = L1['sheet_offset'], F['geometry']['gap'], L1['side_w']; bands, groups = m['bands'], m['groups']
    ins = data.get('insights') or []; tg = [i for i, t in enumerate(m['targets']) if t is not None]
    cw = W - (side + gap if tg else 0) - o; ch = H - o - (L1['insight_h'] + gap if ins else 0)
    ci = [PH.index(c) for c in DS.band_colors(len(bands))]
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    has_py = m['py'] is not None
    # one width for every band column: the swatch then sits clearly nearer its own label than the previous one
    colw = [max(max(tw(b['label'], 14, True) for b in bands) + 40, tw(DS.n0(max(m['totals'])), 16, True) + 18)] * len(bands)
    pyw = max(tw('人年', 14, True), tw(f'{m["py"]:,.0f}', 16, True)) + 22 if has_py else 0
    cols = sum(colw) + pyw; lab_w = min(190, max(max(tw(g['name'], 16, True), tw(g.get('note', ''), 14)) for g in groups) + 20)
    px0 = x0 + 20 + lab_w; px1 = x0 + cw - 20 - cols - 18; pw = px1 - px0
    head = text(x0 + 20, y0 + 14, cw - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    cx = x0 + cw - 20 - cols
    for b, k, w in zip(bands, ci, colw):
        lw = tw(b['label'], 14, True)
        head += f'<rect x="{f(cx + w - 8 - lw - 18)}" y="{f(y0 + 59)}" width="12" height="12" rx="3" fill="url(#l1-ph{k})"/>'
        head += text(cx + w - 8 - lw - 2, y0 + 54, lw + 4, b['label'], 14, INK['title'], True, 'end', lead=22 / 14); cx += w
    head += text(x0 + 20, y0 + 54, lab_w, spec.get('head', '适应症 / 研究'), 14, INK['muted'], True, lead=22 / 14)
    if has_py: head += text(x0 + cw - 20 - pyw, y0 + 54, pyw - 8, '人年', 14, INK['title'], True, 'end', lead=22 / 14)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, 80, head, 0, 'entrance_fade')
    ry0 = y0 + 82; foot = 48; rh = (ch - 82 - foot) / len(groups)
    if rh < 40: raise ValueError(f'flag-exposure 一页最多放 {int((ch - 130) / 40)} 个组，当前 {len(groups)} 个；拆页或合并研究')
    bh = min(24, rh * .44); body = ''
    for r, g in enumerate(groups):
        cy = ry0 + r * rh + rh / 2; fo = g['key'] == m['focus']
        if fo: body += f'<rect x="{f(x0 + 14)}" y="{f(cy - rh / 2 + 2)}" width="{f(cw - 28)}" height="{f(rh - 4)}" rx="10" fill="{L1["focus_row"]}"/>'
        if g.get('note') and rh >= 48:
            body += text(x0 + 20, cy - 21, lab_w - 8, g['name'], 16, INK['title'], True, lead=22 / 16)
            body += text(x0 + 20, cy + 1, lab_w - 8, g['note'], 14, INK['muted'], lead=20 / 14)
        else: body += text(x0 + 20, cy - 11, lab_w - 8, g['name'], 16, INK['title'], True, lead=22 / 16)
        body += f'<rect x="{f(px0)}" y="{f(cy - bh / 2 - 3)}" width="{f(pw)}" height="{f(bh + 6)}" rx="{f(bh / 2 + 3)}" fill="{L1["groove"]}"/>'
        for v, k in zip(g['values'], ci):   # widest (any) first, each deeper band laid on top: a step per duration band
            if v: body += f'<rect x="{f(px0)}" y="{f(cy - bh / 2)}" width="{f(max(bh, v / m["max"] * pw))}" height="{f(bh)}" rx="{f(bh / 2)}" fill="url(#l1-ph{k})" filter="url(#l1-strip)"/>'
        cx = x0 + cw - 20 - cols
        for v, w in zip(g['values'], colw):
            body += text(cx, cy - 11, w - 8, DS.n0(v), 16, INK['title'] if fo else (INK['body'] if v else INK['muted']), fo, 'end', lead=22 / 16); cx += w
        if has_py: body += text(x0 + cw - 20 - pyw, cy - 11, pyw - 8, f'{g["py"]:,.0f}', 16, INK['body'], lead=22 / 16, align='end')
    ty = ry0 + len(groups) * rh
    body += f'<line x1="{f(x0 + 20)}" y1="{f(ty + 4)}" x2="{f(x0 + cw - 20)}" y2="{f(ty + 4)}" stroke="{INK["muted"]}" stroke-width="1.2"/>'
    body += text(x0 + 20, ty + 14, lab_w, f'合计（{m["unit"]}）', 16, INK['title'], True, lead=22 / 16)
    cx = x0 + cw - 20 - cols
    for i, (v, w) in enumerate(zip(m['totals'], colw)):
        met = m['met'][i]; c = INK['title'] if met is None else (F['tag']['ok'][1] if met else RISK)
        body += text(cx, ty + 14, w - 8, DS.n0(v), 16, c, True, 'end', lead=22 / 16); cx += w
    if has_py: body += text(x0 + cw - 20 - pyw, ty + 14, pyw - 8, f'{m["py"]:,.0f}', 16, INK['title'], True, 'end', lead=22 / 16)
    pg.role('chart_label', 16, groups[0]['name'], 22 / 16)
    out += pg.group(f'{gid}-rows', x0 + 14, ry0, cw - 28, ch - 82 - 8, body, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    if tg:
        sx = x0 + cw + o + gap; out += sheet(sx, y0, side, ch); c = card(sx, y0, side, ch)
        c += text(sx + 20, y0 + 14, side - 40, spec.get('target_label', '目标'), TY['card_title'], INK['title'], True, lead=1.3)
        th = (ch - 56 - 12) / len(tg)
        if th < 76: raise ValueError(f'flag-exposure 目标卡最多放 {int((ch - 68) / 76)} 个时长档目标，当前 {len(tg)} 个')
        for j, i in enumerate(tg):
            y = y0 + 56 + j * th; t, v, met = m['targets'][i], m['totals'][i], m['met'][i]
            if j: c += hline(sx + 20, y, side - 40)
            num = DS.n0(v); nw = tw(num, 30, True) + 6
            c += text(sx + 20, y + 10, side - 40, bands[i]['label'], 16, INK['body'], True, lead=22 / 16)
            c += text(sx + 20, y + 32, nw, num, 30, NUM_INK if met else RISK, True, lead=1.2)
            c += text(sx + 24 + nw, y + 44, side - 44 - nw - 80, f'目标 ≥{DS.n0(t)}', 16, INK['muted'], lead=22 / 16)
            tag = '达到' if met else f'差 {DS.n0(t - v)}'; bg, ink = F['tag']['ok'] if met else F['tag']['risk']; gw = tw(tag, 14, True) + 18
            c += f'<rect x="{f(sx + side - 20 - gw)}" y="{f(y + 44)}" width="{f(gw)}" height="22" rx="11" fill="{bg}"/>'
            c += text(sx + side - 20 - gw, y + 44, gw, tag, 14, ink, True, 'middle', lead=22 / 14)
            gy = y + th - 18; gx, gwid = sx + 20, side - 40; top = max(v, t) * 1.08
            c += f'<rect x="{f(gx)}" y="{f(gy - 5)}" width="{f(gwid)}" height="10" rx="5" fill="{L1["groove"]}"/>'
            c += f'<rect x="{f(gx)}" y="{f(gy - 4)}" width="{f(max(8, v / top * gwid))}" height="8" rx="4" fill="url(#l1-ph{ci[i]})" filter="url(#l1-strip)"/>'
            tx = gx + t / top * gwid
            c += f'<line x1="{f(tx)}" y1="{f(gy - 9)}" x2="{f(tx)}" y2="{f(gy + 9)}" stroke="{INK["title"]}" stroke-width="2" stroke-linecap="round"/>'
            pg.role('chart_label', 16, bands[i]['label'], 22 / 16)
        pg.role('card_title', TY['card_title'], spec.get('target_label', '目标'), 1.3); pg.role('takeaway', 30, DS.n0(m['totals'][tg[0]]), 1.2)
        out += pg.group(f'{gid}-target', sx, y0, side, ch, c, 2, 'entrance_rise_up', card=True)
    if ins: out += _insight_tabs(pg, ins, x0, y0 + ch + o + gap, W, H - ch - o - gap, gid, 3)
    return out

def exposure_plan_board(pg, data, box, gid='fx'):
    """flag-exposure-plan: cumulative exposure on the development plan, for a leadership read — one card with the step
    chart of the static template (diagram_scenes.exposure_plan_chart: a dot per study, ICH E1 target, numbered NDA
    verticals, the count at each NDA ringed, the first crossing), beside it one readiness card: per indication with an
    NDA its number disc, name and NDA date, then a row per target band (count at NDA, a met / gap tag). No insight
    tabs — the summary goes into the notes (round 9)."""
    spec = data['exposure_plan']; m = DS.exposure_plan(spec); x0, y0, W, H = box
    o, gap, side = L1['sheet_offset'], F['geometry']['gap'], L1['side_w'] + 40
    inds = [i for i in m['indications'] if i['nda']]; tg = m['targets']; bands = [k for k in m['bands'] if k in tg]
    cw = W - side - gap - o; ch = H - o
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    head = text(x0 + 20, y0 + 14, cw - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, 52, head, 0, 'entrance_fade')
    fig = DS.exposure_plan_chart(spec, [x0 + 16, y0 + 56, cw - 32, ch - 68], f'{gid}-plot', 'pptx')
    pg.role('chart_label', 16, m['target_label'], 22 / 16)
    out += pg.group(f'{gid}-plot', x0 + 14, y0 + 54, cw - 28, ch - 62, fig, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    if not inds: return out
    sx = x0 + cw + o + gap; c = sheet(sx, y0, side, ch) + card(sx, y0, side, ch)
    c += text(sx + 20, y0 + 14, side - 40, f'NDA 时对照 {m["target_label"]}', TY['card_title'], INK['title'], True, lead=1.3)
    pg.role('card_title', TY['card_title'], f'NDA 时对照 {m["target_label"]}', 1.3)
    bh = (ch - 60 - 8) / len(inds); need = 34 + 30 * len(bands)
    if bh < need: raise ValueError(f'flag-exposure-plan 达标卡一页最多放 {int((ch - 68) // need)} 个适应症，当前 {len(inds)} 个；拆页或只列关键适应症')
    cat = TOK['charts']['categorical']; icol = {i['key']: cat[k % len(cat)] for k, i in enumerate(m['indications'])}
    for j, i in enumerate(inds):
        y = y0 + 60 + j * bh; fo = i['key'] == m['focus']
        if j: c += hline(sx + 20, y - 6, side - 40)
        if fo: c += f'<rect x="{f(sx + 12)}" y="{f(y - 2)}" width="{f(side - 24)}" height="{f(bh - 8)}" rx="10" fill="{L1["focus_row"]}"/>'
        c += f'<circle cx="{f(sx + 31)}" cy="{f(y + 13)}" r="10" fill="{icol[i["key"]]}"/>'
        c += text(sx + 21, y + 2, 20, str(j + 1), 14, '#FFFFFF', True, 'middle', lead=22 / 14)
        c += text(sx + 48, y + 2, side - 200, i['name'], 16, INK['title'], True, lead=22 / 16)
        c += text(sx + side - 150, y + 2, 130, f'NDA {i["nda"]["text"]}', 16, INK['body'], False, 'end', lead=22 / 16)
        for r, k in enumerate(bands):
            ry = y + 34 + r * 30; ok = i['met'][k]
            c += text(sx + 48, ry, 110, KX_LABEL[k], 16, INK['body'], lead=22 / 16)
            c += text(sx + 150, ry, 80, DS.n0(i['cum'][k]), 16, NUM_INK if ok else RISK, True, 'end', lead=22 / 16)
            tag = '达到' if ok else f'差 {DS.n0(i["gap"][k])}'; bg, ink = F['tag']['ok'] if ok else F['tag']['risk']; gw = tw(tag, 14, True) + 18
            c += f'<rect x="{f(sx + side - 20 - gw)}" y="{f(ry)}" width="{f(gw)}" height="22" rx="11" fill="{bg}"/>'
            c += text(sx + side - 20 - gw, ry, gw, tag, 14, ink, True, 'middle', lead=22 / 14)
    pg.role('chart_label', 16, inds[0]['name'], 22 / 16)
    out += pg.group(f'{gid}-ready', sx, y0, side, ch, c, 2, 'entrance_rise_up', card=True)
    return out

KX_LABEL = {'any': '任何暴露', 'w26': '≥26 周', 'w52': '≥52 周'}

# ---------- trial flow ----------
def trialflow_board(pg, data, box, gid='ft'):
    """flag-trialflow: one card on a back sheet. Week axis on the piecewise scale with endpoint gems; shared periods
    (screening, run-in, follow-up) are tall paper blocks over every row; the randomisation disc (R + ratio) with its spine
    fans out to the arms; each arm's segments are raised strips in grooves (titration light, maintenance deep, placebo
    slate, off-treatment flat and dashed); a re-randomised arm gets its own disc and sub-arm strips; sub-studies are dashed
    pills under the rows; then one flat strip per treatment period (study drug, background, rescue); key events (interim,
    lock…) are ringed dots on the axis with their labels (one tier higher when an endpoint label is in the way); insight
    tabs underneath (optional — round 9 puts the summary in the notes)."""
    m = DS.trialflow_model(data['trialflow']); spec = data['trialflow']; x0, y0, W, H = box
    o, gap = L1['sheet_offset'], F['geometry']['gap']; ins = data.get('insights') or []
    arms, leaves = m['arms'], m['leaves']; nl, ns = len(leaves), len(m['subs']); nested = any(a['sub'] for a in arms)
    cw = W - o; ch = H - o - (L1['insight_h'] + gap if ins else 0)
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    nmw = lambda xs: max([tw(v['name'], 16, True) for v in xs] + [tw(f'n={v["n"]:,}', 14) for v in xs if v.get('n') is not None] + [0])
    ca = nmw(arms) + 22; cb = nmw([l for l in leaves if l['parent']]) + 30 if nested else 0
    tx0 = x0 + 20 + ca + cb + 14; tx1 = x0 + cw - 22; X = DS.flow_scale(m, tx0, tx1, 92)
    head = text(x0 + 20, y0 + 14, cw - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, 46, head, 0, 'entrance_fade')
    # event labels: same tier as the endpoint labels unless one is in the way, then one tier up (the axis moves down)
    span = lambda x_, w_: (x_ - w_ / 2, x_ + w_ / 2)
    taken = [span(X(p['at']), tw(p['label'], 14, bool(p.get('primary'))) + 8) for p in m['endpoints']]; tiers = []
    for e in m['events']:
        sp_ = span(min(X(e['at']), tx1 - (tw(e['label'], 14) + 8) / 2), tw(e['label'], 14) + 8)
        hit = any(sp_[0] < b_ + 6 and a_ < sp_[1] + 6 for a_, b_ in taken); tiers.append(1 if hit else 0); taken.append(sp_)
    up = 18 if any(tiers) else 0; nb = len(m['bands'])
    ay = y0 + 92 + up; ry0 = y0 + 128 + up; rh = (ch - 128 - up - 16 - ns * 36 - nb * 30) / nl
    if rh < 44: raise ValueError(f'flag-trialflow 一页最多放 {int((ch - 144 - up - ns * 36 - nb * 30) / 44)} 个治疗分支，当前 {nl} 个；拆页、去掉子研究或减少时段')
    rh = min(rh, 72); bh = min(26, rh * .42); cy = lambda r: ry0 + r * rh + rh / 2; mid = (cy(0) + cy(nl - 1)) / 2; rows_b = ry0 + nl * rh
    acy = {a['key']: (cy(a['rows'][0]) + cy(a['rows'][-1])) / 2 for a in arms}; NR = 13
    # root framing: focus tint, endpoint guides through the rows
    fa = next((a for a in arms if a['key'] == m['focus']), None); fr = ''
    if fa: fr += f'<rect x="{f(x0 + 14)}" y="{f(ry0 + fa["rows"][0] * rh + 2)}" width="{f(cw - 28)}" height="{f(len(fa["rows"]) * rh - 4)}" rx="10" fill="{L1["focus_row"]}"/>'
    for p in m['endpoints']:
        fr += f'<line x1="{f(X(p["at"]))}" y1="{f(ay + 10)}" x2="{f(X(p["at"]))}" y2="{f(rows_b)}" stroke="{CH["grid"]}" stroke-width="1.2" stroke-dasharray="4 4"/>'
    out += deco(fr)
    # axis: ticks, endpoint gems and labels
    ax = f'<line x1="{f(tx0)}" y1="{f(ay)}" x2="{f(tx1)}" y2="{f(ay)}" stroke="{CH["axis"]}" stroke-width="1.2"/>'
    for t in m['ticks']:
        ax += f'<line x1="{f(X(t))}" y1="{f(ay - 4)}" x2="{f(X(t))}" y2="{f(ay + 4)}" stroke="{CH["axis"]}" stroke-width="1.2"/>'
        lab = DS.wk(t); lw = tw(lab, 14) + 8; lx = min(max(X(t) - lw / 2, tx0 - 20), tx1 - lw)
        ax += text(lx, ay + 8, lw, lab, 14, INK['muted'], align='middle', lead=1.3)
    for p in m['endpoints']:
        px = X(p['at']); pr = bool(p.get('primary')); lw = tw(p['label'], 14, pr) + 8
        ax += gem(px, ay, 8, True, False, pr) if pr else gem(px, ay, 7, False, False, False)
        ax += text(min(px - lw / 2, tx1 - lw), ay - 36, lw, p['label'], 14, F['accent_ink'] if pr else INK['body'], pr, 'middle', lead=1.3)
    for e, tier in zip(m['events'], tiers):
        ex_ = X(e['at']); lw = tw(e['label'], 14) + 8
        ax += f'<circle cx="{f(ex_)}" cy="{f(ay)}" r="5" fill="#FFFFFF" stroke="{INK["muted"]}" stroke-width="1.6"/>'
        ax += text(min(ex_ - lw / 2, tx1 - lw), ay - 36 - 18 * tier, lw, e['label'], 14, INK['body'], False, 'middle', lead=1.3)
        if e['at'] not in m['ticks']:
            lab = DS.wk(e['at']); lw2 = tw(lab, 14) + 8; ax += text(ex_ - lw2 / 2, ay + 8, lw2, lab, 14, INK['muted'], align='middle', lead=1.3)
    out += pg.group(f'{gid}-axis', tx0 - 20, ay - 40 - up, tx1 - tx0 + 20, 66 + up, ax, 0, 'entrance_fade', figure=True)
    def strip(g, yc, a, b, hh=None):
        k = g.get('kind', 'maintain'); hh = hh or bh; r = min(hh, bh) / 2
        if k == 'off':
            sv = f'<rect x="{f(a)}" y="{f(yc - hh / 2)}" width="{f(b - a)}" height="{f(hh)}" rx="{f(r)}" fill="{FLW["off"]}" stroke="{FLW["off_edge"]}" stroke-width="1.2" stroke-dasharray="4 3"/>'
        else:
            sv = (f'<rect x="{f(a - 2)}" y="{f(yc - hh / 2 - 3)}" width="{f(b - a + 4)}" height="{f(hh + 6)}" rx="{f(r + 3)}" fill="{L1["groove"]}"/>'
                  f'<rect x="{f(a)}" y="{f(yc - hh / 2)}" width="{f(b - a)}" height="{f(hh)}" rx="{f(r)}" fill="url(#l1-fl-{k})" filter="url(#l1-strip)"/>')
        lab = g.get('label', ''); ink = INK['title'] if k == 'off' else on_color(FLW[k])
        if tw(lab, 14, True) + 16 < b - a: sv += text(a, yc - 10, b - a, lab, 14, ink, True, 'middle', lead=20 / 14)
        else: raise ValueError(f'flag-trialflow：段落「{lab}」放不下（{b - a:.0f}px）；缩短段名或拆页')
        return sv
    tall = cy(nl - 1) - cy(0) + bh + 12
    tr = ''.join(strip(g, mid, X(g['from']) + 2, X(g['to']) - (NR + 4 if g is m['trunk'][-1] else 2), tall) for g in m['trunk'])
    if tr: out += pg.group(f'{gid}-trunk', X(m['start']), mid - tall / 2 - 3, X(m['at']) - NR - 2 - X(m['start']), tall + 6, tr, 1, 'entrance_rise_up', figure=True)
    def disc(nx, ny, ys, label):
        sv = f'<line x1="{f(nx)}" y1="{f(min(ys))}" x2="{f(nx)}" y2="{f(max(ys))}" stroke="#8A949E" stroke-width="1.6"/>'
        sv += f'<circle cx="{f(nx)}" cy="{f(ny)}" r="{NR}" fill="#FFFFFF" stroke="{F["accent_ink"]}" stroke-width="2" filter="url(#l1-lift)"/>'
        return sv + text(nx - NR, ny - 10, 2 * NR, 'R', 14, F['accent_ink'], True, 'middle', lead=20 / 14)
    sp = m['split']; lab0 = sp.get('label', '随机化') + (f' {sp["ratio"]}' if sp.get('ratio') else '')
    ys0 = list(acy.values())
    out += pg.group(f'{gid}-rand', X(m['at']) - NR, min(ys0 + [mid]) - NR, 2 * NR, max(ys0 + [mid]) - min(ys0 + [mid]) + 2 * NR, disc(X(m['at']), mid, ys0, lab0), 1, 'entrance_zoom', figure=True)
    names = ''
    for k, a in enumerate(arms):
        yc = acy[a['key']]; g = ''; raw = next(x_ for x_ in spec['arms'] if x_.get('key') == a['key'])
        names += text(x0 + 20, yc - (21 if a.get('n') is not None else 11), ca - 6, a['name'], 16, INK['title'], True, lead=22 / 16)
        if a.get('n') is not None: names += text(x0 + 20, yc + 1, ca - 6, f'n={a["n"]:,}', 14, INK['muted'], lead=20 / 14)
        segs = a['segs']; sub = a['sub']
        for j, sg in enumerate(segs):
            g += strip(sg, yc, X(sg['from']) + (NR + 4 if j == 0 else 2), X(sg['to']) - (NR + 4 if sub and j == len(segs) - 1 else 2))
        ltop = r0 = ry0 + a['rows'][0] * rh
        if sub:
            ys = [cy(r) for r in a['rows']]; kids = [l for l in leaves if l['parent'] == a['key']]; sx = X(sub['at'])
            g += disc(sx, yc, ys, '')
            sl = sub['label'] + (f' {raw["split"]["ratio"]}' if raw['split'].get('ratio') else ''); lw = tw(sl, 14, True) + 6
            g += text(sx + NR + 6, ys[0] - bh / 2 - 22, lw, sl, 14, INK['title'], True, lead=20 / 14); ltop = min(ltop, ys[0] - bh / 2 - 23)
            bx = x0 + 20 + ca + 2
            names += f'<line x1="{f(bx)}" y1="{f(ys[0] - bh / 2)}" x2="{f(bx)}" y2="{f(ys[-1] + bh / 2)}" stroke="{F["accent_ink"] if fa is a else CH["axis"]}" stroke-width="2"/>'
            for l, yy in zip(kids, ys):
                for sg in l['segs']: g += strip(sg, yy, X(sg['from']) + (NR + 4 if sg is l['segs'][0] else 2), X(sg['to']) - 2)
                names += text(bx + 12, yy - (21 if l.get('n') is not None else 11), cb - 14, l['name'], 16, INK['title'], lead=22 / 16)
                if l.get('n') is not None: names += text(bx + 12, yy + 1, cb - 14, f'n={l["n"]:,}', 14, INK['muted'], lead=20 / 14)
        r1 = ry0 + (a['rows'][-1] + 1) * rh
        if k == 0: g += text(X(m['at']) + NR + 6, min(ys0) - bh / 2 - 22, tw(lab0, 14, True) + 6, lab0, 14, INK['title'], True, lead=20 / 14); ltop = min(ltop, min(ys0) - bh / 2 - 23)
        if ltop < ay + 27: raise ValueError('flag-trialflow：随机化标签压到时间轴；减少子研究或拆页')
        out += pg.group(f'{gid}-arm{k}', X(m['at']) + NR + 2, ltop, X(m['end']) - X(m['at']) - NR - 3, r1 - ltop, g, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    pg.role('chart_label', 16, arms[0]['name'], 22 / 16)
    out += pg.group(f'{gid}-names', x0 + 20, ry0, ca + cb, nl * rh, names, 1, 'entrance_fade', figure=True)
    if m['after']:
        af = f'<line x1="{f(X(m["end"]))}" y1="{f(cy(0))}" x2="{f(X(m["end"]))}" y2="{f(cy(nl - 1))}" stroke="#8A949E" stroke-width="1.6"/>'
        af += ''.join(strip(g, mid, X(g['from']) + 4, X(g['to']) - 2, tall) for g in m['after'])
        out += pg.group(f'{gid}-after', X(m['end']) - 1, mid - tall / 2 - 3, X(m['final']) - X(m['end']) + 1, tall + 6, af, 2, 'entrance_rise_up', figure=True)
    if ns:
        nm = {a['key']: a['name'] for a in arms} | {l['key']: l['name'] for l in leaves}; sv = ''
        sy = rows_b + 6
        sv += text(x0 + 20, sy + 6, ca + cb, '子研究', 16, INK['muted'], True, lead=22 / 16)
        for k, sb in enumerate(m['subs']):
            yy = sy + k * 36 + 17; a, b = X(sb['from']) + NR + 4, X(sb['to']) - 2
            sv += f'<rect x="{f(a)}" y="{f(yy - 13)}" width="{f(b - a)}" height="26" rx="13" fill="#FFFFFF" stroke="{F["accent_ink"]}" stroke-width="1.4" stroke-dasharray="5 4"/>'
            lab = sb['name'] + (f' n={sb["n"]:,}' if sb.get('n') is not None else '') + ' · ' + '、'.join(nm[q] for q in sb['of'])
            sv += text(a + 14, yy - 10, b - a - 24, lab, 14, INK['title'], True, lead=20 / 14)
        out += pg.group(f'{gid}-subs', x0 + 20, sy, cw - 40, ns * 36, sv, 2, 'entrance_fade', figure=True)
    if nb:   # treatment periods: name on the left, a flat strip over its weeks with its text
        bv = ''; by_ = rows_b + 6 + ns * 36 + (6 if ns else 0); nm2 = {a['key']: a['name'] for a in arms} | {l['key']: l['name'] for l in leaves}
        for k, b in enumerate(m['bands']):
            yy = by_ + k * 30 + 15; a_, z_ = X(b['from']) + 2, X(b['to']) - 2; fill, ink, dash = SOA_STRIP[b['kind']]
            bv += text(x0 + 20, yy - 11, ca + cb, b['label'], 16, INK['title'], True, lead=22 / 16)
            bv += f'<rect x="{f(a_)}" y="{f(yy - 9)}" width="{f(z_ - a_)}" height="18" rx="9" fill="{fill}"' + (f' stroke="{ink}" stroke-width="1.2" stroke-dasharray="4 3"' if dash else '') + '/>'
            lab = (b['text'] or b['label']) + (' · ' + '、'.join(nm2[q] for q in b['of']) if b['of'] else '')
            if tw(lab, 14) * KT.HEADROOM > z_ - a_ - 16: lab = b['label']
            bv += text(a_ + 10, yy - 9, z_ - a_ - 20, lab, 14, ink, False, lead=18 / 14)
        out += pg.group(f'{gid}-bands', x0 + 20, by_, cw - 40, nb * 30, bv, 2, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    if ins: out += _insight_tabs(pg, ins, x0, y0 + ch + o + gap, W, H - ch - o - gap, gid, 3)
    return out

# ---------- competitive landscape ----------
def landscape_rows(pg, data, box, gid='fl'):
    """flag-landscape: one card on a back sheet. A header with the stage names and each metric's label, unit and better
    direction; one row per asset in stage order (ours on the focus tint): name with company · mechanism · route, the
    stage as facet arrows filled up to the current stage (phase ramp), then a groove + raised strip per metric on its own
    scale with the value (the best per metric in accent ink; no data written as —, never drawn as 0); insight tabs."""
    m = DS.landscape_model(data['landscape']); x0, y0, W, H = box; o, gap = L1['sheet_offset'], F['geometry']['gap']
    st = m['stages']; A = {a['key']: a for a in m['assets']}; mets = list(m['metrics']); n = len(A)
    # round 9 tiers (as the static landscape): tabs only with ≤ 4 assets; > 8 go to the three split pages
    if n > 8: raise ValueError(f'flag-landscape {n} 个药物：超过 8 个时用常规的 landscape-pipeline / landscape-efficacy / landscape-safety 三页')
    ins = (data.get('insights') or []) if n <= 4 else []
    cw = W - o; ch = H - o - (L1['insight_h'] + gap if ins else 0)
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    sub = lambda a: ' · '.join(v for v in (a.get('company'), a.get('moa'), a.get('route')) if v)
    nw = max(max(tw(a['name'] + ('（本品）' if a.get('ours') else ''), 16, True), tw(sub(a), 14)) for a in A.values()) * KT.HEADROOM + 24
    sx = x0 + 20 + nw; cwid = max(64, max(tw(t, 14, True) for t in st) + 22); sw = cwid * len(st)
    mx = sx + sw + 28; mw = (x0 + cw - 20 - mx - 28 * (len(mets) - 1)) / max(1, len(mets))
    head = text(x0 + 20, y0 + 14, cw - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    hy = y0 + 54
    head += text(x0 + 20, hy, nw, '药物 · 公司 · 机制', 14, INK['muted'], True, lead=1.4)
    for k, t in enumerate(st): head += text(sx + k * cwid, hy, cwid, t, 14, INK['title'], True, 'middle', lead=1.4)
    for j, mk in enumerate(mets):
        mt = m['metrics'][mk]; up = mt['better'] == 'higher'; lab = mt['label'] + (f'（{mt["unit"]}）' if mt.get('unit') else '')
        full = lab + ('  ↑ 越高越好' if up else '  ↓ 越低越好'); lab = full if tw(full, 14, True) * KT.HEADROOM < mw else lab + (' ↑' if up else ' ↓')
        head += text(mx + j * (mw + 28), hy, mw, lab, 14, INK['title'], True, lead=1.4)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, 78, head, 0, 'entrance_fade')
    ry0 = y0 + 84; rh = (ch - 84 - 12) / n
    if rh < 34: raise ValueError(f'flag-landscape 一页最多放 {int((ch - 96) / 34)} 个药物，当前 {n} 个；拆页或去掉早期竞品')
    rh = min(rh, 60); two = rh >= 40; sc = DS.stage_colors(len(st)); body = ''; fr = ''
    for r, key in enumerate(m['order']):
        a = A[key]; cy = ry0 + r * rh + rh / 2; ours = a.get('ours'); fo = key == m['focus']
        if ours or fo: fr += f'<rect x="{f(x0 + 14)}" y="{f(cy - rh / 2 + 1)}" width="{f(cw - 28)}" height="{f(rh - 2)}" rx="10" fill="{L1["focus_row"]}"/>'
        nm = a['name'] + ('（本品）' if ours else '')
        if two and sub(a):
            body += text(x0 + 20, cy - 20, nw, nm, 16, F['accent_ink'] if ours else INK['title'], True, lead=22 / 16)
            body += text(x0 + 20, cy + 1, nw, sub(a), 14, INK['muted'], lead=20 / 14)
        else: body += text(x0 + 20, cy - 11, nw, nm, 16, F['accent_ink'] if ours else INK['title'], True, lead=22 / 16)
        for k in range(len(st)):
            on = k <= a['si']; xa = sx + k * cwid + 2; xb = xa + cwid - 4
            body += chevron(xa, xb, cy, 18, sc[k] if on else L1['groove'], k > 0, True)
        for j, mk in enumerate(mets):
            v = a.get(mk); bx = mx + j * (mw + 28); vw = tw('00.0', 16, True) + 12; bw = mw - vw
            body += f'<rect x="{f(bx)}" y="{f(cy - 9)}" width="{f(bw)}" height="18" rx="9" fill="{L1["groove"]}"/>'
            if v is None: body += text(bx + 10, cy - 10, bw, '—  暂无数据', 14, INK['muted'], lead=20 / 14); continue
            L = max(12, abs(v) / m['max'][mk] * bw); best = m['best'][mk] == key
            body += f'<rect x="{f(bx)}" y="{f(cy - 7)}" width="{f(L)}" height="14" rx="7" fill="url(#{"l1-treat-h" if ours else "l1-comp-h"})" filter="url(#l1-strip)"/>'
            body += text(bx + bw + 8, cy - 11, vw, f'{v:g}', 16, F['accent_ink'] if best else (INK['title'] if ours else INK['body']), best, lead=22 / 16)
    out += deco(fr)
    pg.role('chart_label', 16, A[m['order'][0]]['name'], 22 / 16)
    out += pg.group(f'{gid}-rows', x0 + 14, ry0, cw - 28, n * rh, body, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    if ins: out += _insight_tabs(pg, ins, x0, y0 + ch + o + gap, W, H - ch - o - gap, gid, 2)
    return out

def efficacy_board(pg, data, box, gid='fv'):
    """flag-efficacy: one card on a back sheet. A header with each arm (dot, name, n); per endpoint type a section with
    its own difference axis that always holds 0; one row per endpoint (focus on the tint): tier tag, label and unit, each
    arm's value (binary: % with n/N), then per treat arm a forest mark — the 95% CI as a soft line in the arm's colour and
    the estimate as a white-rimmed square (risk colour the wrong way, grey dashes and a hollow square when it crosses 0),
    the difference with its CI and P in the right columns; insight tabs underneath (optional)."""
    m = DS.efficacy_model(data['efficacy']); x0, y0, W, H = box; o, gap = L1['sheet_offset'], F['geometry']['gap']
    ins = data.get('insights') or []; arms, rows, tr = m['arms'], m['rows'], m['treat']; nt = len(tr); n = len(rows); ns = len(m['axes'])
    tc = dict(zip(tr, DS.treat_colors(nt)))
    cw = W - o; ch = H - o - (L1['insight_h'] + gap if ins else 0)
    out = sheet(x0, y0, cw, ch) + card(x0, y0, cw, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    tagw = lambda r: tw(r['tier'], 14, True) + 30 if r.get('tier') else 0
    lw = max(tagw(r) + tw(r['label'], 16, True) * KT.HEADROOM for r in rows) + 12
    # an arm name that does not fit its column breaks at the space nearest its middle (KZ-001 / 0.5 mg)
    def parts(nm):
        sp = [k for k, ch_ in enumerate(nm) if ch_ == ' ']
        if not sp: return [nm]
        k = min(sp, key=lambda q: abs(q - len(nm) / 2)); return [nm[:k], nm[k + 1:]]
    vals_w = max(tw(DS.ef_value(r, q)[0], 16, True) for r in rows for q in range(len(arms)))
    vw = max(84, vals_w * KT.HEADROOM + 30, max(tw(x, 16, True) for a in arms for x in parts(a['name'])) * KT.HEADROOM + 30)
    names = [[a['name']] if tw(a['name'], 16, True) * KT.HEADROOM <= vw - 22 else parts(a['name']) for a in arms]
    dw = max(tw(DS.ef_diff(c, r['dp'], r['measure']), 16, True) for r in rows for c in r['cmp'].values()) * KT.HEADROOM + 22
    pw = max([tw(str(c['p']), 16) for r in rows for c in r['cmp'].values() if c.get('p') is not None] + [0]) * KT.HEADROOM + 12
    xl = x0 + 20; xv = xl + lw; xf = xv + vw * len(arms) + 24; xp = x0 + cw - 20 - pw; xd = xp - dw; fw = xd - 20 - xf
    if fw < 200: raise ValueError(f'flag-efficacy 放不下：差值图只剩 {int(fw)} px（<200）；减少组数、缩短终点名或拆页')
    head = text(xl, y0 + 14, cw - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    hy = y0 + 48; nl_ = max(len(x) for x in names); hb = hy + nl_ * 20 + 18
    head += text(xl, hb - 20, lw - 8, '终点', 14, INK['muted'], True, lead=1.4)
    for i, a in enumerate(arms):
        cx = xv + i * vw; col = tc.get(i, COMP); top = hy + (nl_ - len(names[i])) * 20
        head += f'<circle cx="{f(cx + 9)}" cy="{f(top + 10)}" r="5" fill="{col}"/>'
        for k, x in enumerate(names[i]): head += text(cx + 20, top + k * 20, vw - 22, x, 16, INK['title'], True, lead=20 / 16)
        head += text(cx + 20, hb - 21, vw - 22, f'n={a["n"]:,}', 14, INK['muted'], lead=18 / 14)
    eff = '效应值' if 'ratio' in m['axes'] else '差值'
    head += text(xf, hb - 20, fw, f'{eff}与 95% CI（vs {arms[m["comp"]]["name"]}）', 14, INK['muted'], True, lead=1.4)
    head += text(xd, hb - 20, dw, f'{eff}（95% CI）', 14, INK['muted'], True, lead=1.4)
    if pw > 12: head += text(xp, hb - 20, pw, 'P', 14, INK['muted'], True, 'end', lead=1.4)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw, hb - y0, head, 0, 'entrance_fade')
    ry0 = hb + 4; SH = 28; rh = (y0 + ch - 10 - ry0 - ns * SH) / n
    if rh < 44: raise ValueError(f'flag-efficacy 一页最多放 {int((y0 + ch - 10 - ry0 - ns * SH) / 44)} 个终点，当前 {n} 个；拆页或把次要终点移到附表')
    rh = min(rh, 66); body = ''; fr = ''; y = ry0
    for t in m['axes']:
        dom = m['domain'][t]; X = lambda v, dom=dom: xf + DS.ef_pos(dom, v) * fw; ref = 1 if t == 'ratio' else 0
        body += text(xl, y + 4, xf - xl - 16, DS.EF_HEAD[t], 14, INK['muted'], True, lead=1.4)
        for v in DS.ef_ticks(dom):
            lab = f'{v:g}'.replace('-', '−'); body += text(X(v) - 30, y + 4, 60, lab, 14, INK['title'] if v == ref else INK['muted'], v == ref, 'middle', lead=1.4)
        y += SH; rs = [r for r in rows if r['axis'] == t]
        body += f'<line x1="{f(X(ref))}" y1="{f(y)}" x2="{f(X(ref))}" y2="{f(y + len(rs) * rh)}" stroke="{INK["muted"]}" stroke-width="1.2"/>'
        for r in rs:
            cy = y + rh / 2; fo = r['key'] == m['focus']
            if fo: fr += f'<rect x="{f(x0 + 14)}" y="{f(y + 2)}" width="{f(cw - 28)}" height="{f(rh - 4)}" rx="10" fill="{L1["focus_row"]}"/>'
            tx = xl
            if r.get('tier'):
                pw_ = tagw(r) - 8; pri = r['tier'] == '主要'
                body += f'<rect x="{f(xl)}" y="{f(cy - 13)}" width="{f(pw_)}" height="26" rx="13" fill="{mix(TREAT, .8) if pri else L1["groove"]}"/>'
                body += text(xl, cy - 10, pw_, r['tier'], 14, F['accent_ink'] if pri else INK['body'], True, 'middle', lead=20 / 14); tx = xl + pw_ + 8
            sub = ' · '.join(v for v in (r.get('unit'), r.get('time')) if v)
            if sub: body += text(tx, cy - 21, xv - tx - 8, r['label'], 16, INK['title'], True, lead=22 / 16) + text(tx, cy + 1, xv - tx - 8, sub, 14, INK['muted'], lead=20 / 14)
            else: body += text(tx, cy - 11, xv - tx - 8, r['label'], 16, INK['title'], True, lead=22 / 16)
            for i in range(len(arms)):
                main, small = DS.ef_value(r, i); cx = xv + i * vw + 20; ink = INK['title'] if i in tr else INK['body']
                if small: body += text(cx, cy - 21, vw - 22, main, 16, ink, i in tr, lead=22 / 16) + text(cx, cy + 1, vw - 22, small, 14, INK['muted'], lead=20 / 14)
                else: body += text(cx, cy - 11, vw - 22, main, 16, ink, i in tr and main != '—', lead=22 / 16)
            ks = list(r['cmp']); dy = min(20, (rh - 4) / max(1, len(ks)))
            for j, key in enumerate(ks):
                c = r['cmp'][key]; i = [a['key'] for a in arms].index(key); yy = cy + (j - (len(ks) - 1) / 2) * dy
                # forest marks (round 9: no groove, strip or black whisker): the CI as a round-capped line in the arm's own
                # colour, the estimate as a rounded square with a white rim; worse → risk colour, CI across 0 → grey dashes
                # and a hollow square
                col = RISK if c['verdict'] == 'worse' else (INK['muted'] if c['verdict'] == 'ns' else tc[i])
                dash = ' stroke-dasharray="4 3"' if c['verdict'] == 'ns' else ''
                body += f'<line x1="{f(X(c["ci"][0]))}" y1="{f(yy)}" x2="{f(X(c["ci"][1]))}" y2="{f(yy)}" stroke="{col}" stroke-opacity=".55" stroke-width="3" stroke-linecap="round"{dash}/>'
                q = 6 if fo else 5
                body += (f'<rect x="{f(X(c["diff"]) - q)}" y="{f(yy - q)}" width="{f(2 * q)}" height="{f(2 * q)}" rx="2.5" '
                         f'fill="{"#FFFFFF" if c["verdict"] == "ns" else col}" stroke="{col if c["verdict"] == "ns" else "#FFFFFF"}" stroke-width="1.5"/>')
                good = c['verdict'] == 'better'; ink = RISK if c['verdict'] == 'worse' else (INK['title'] if good else INK['muted'])
                body += f'<circle cx="{f(xd + 5)}" cy="{f(yy)}" r="4" fill="{tc[i]}"/>' + text(xd + 14, yy - 10, dw - 14, DS.ef_diff(c, r['dp'], r['measure']), 16, F['accent_ink'] if fo and good else ink, fo and good, lead=20 / 16)
                if c.get('p') is not None: body += text(xp, yy - 10, pw, str(c['p']), 16, ink, False, 'end', lead=20 / 16)
            y += rh
    out += deco(fr)
    pg.role('chart_label', 16, rows[0]['label'], 22 / 16)
    out += pg.group(f'{gid}-rows', x0 + 14, ry0, cw - 28, y - ry0, body, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    if ins: out += _insight_tabs(pg, ins, x0, y0 + ch + o + gap, W, H - ch - o - gap, gid, 2)
    return out

def soa_board(pg, data, box, gid='fa'):
    """flag-soa: one card on a back sheet (round 9). Periods as facet arrows over their visit columns, visit names with
    weeks; the primary-endpoint visit column on a pale tint from header to foot; a key-event row (primary endpoint as an
    accent gem, randomisation as a gem, the other events as small dots, each with its label); one flat strip per treatment
    period (study drug, background, rescue…) from its first to its last visit with its text; then the assessments item by
    item under their section names — a flat disc per visit, the focus item's row tinted and its primary-visit marks as
    gems. `sections` and / or `items` (optional) pick what this page shows (about 9 items fit with events and three
    periods; the full item table is the static soa template). No insight tabs: the summary goes to the notes."""
    m = DS.soa_model(data['soa']); x0, y0, W, H = box; o = L1['sheet_offset']
    V = m['visits']; nv = len(V); pick, only = data.get('sections'), data.get('items')
    secs = [q for q in m['sections'] if not pick or q['name'] in pick]
    if pick and len(secs) != len(pick): raise ValueError(f'flag-soa 的 sections 里有不存在的分组：{[s for s in pick if s not in [q["name"] for q in m["sections"]]]}')
    if only and any(n not in [x['item'] for x in m['items']] for n in only): raise ValueError(f'flag-soa 的 items 里有不存在的评估项目：{[n for n in only if n not in [x["item"] for x in m["items"]]]}')
    keep = lambda i: not only or m['items'][i]['item'] in only
    rows = [r for q in secs if any(keep(i) for i in q['items']) for r in ([('sec', q['name'])] if q['name'] else []) + [('item', m['items'][i]) for i in q['items'] if keep(i)]]
    cw_ = W - o; ch = H - o
    out = sheet(x0, y0, cw_, ch) + card(x0, y0, cw_, ch, f'{gid}-card'); pg.cards.append(f'{gid}-card')
    names = [r[1]['item'] for r in rows if r[0] == 'item'] + [b['label'] for b in m['bands']] + ['关键节点']
    secn = [r[1] for r in rows if r[0] == 'sec']
    sw = max(tw(t, 14, True) for t in secn) * KT.HEADROOM / 2 + 22 if secn else 0   # section names in their own column, two lines
    nw = sw + max(tw(t, 16, True) for t in names) * KT.HEADROOM + 16
    vx = x0 + 20 + nw; cw = (x0 + cw_ - 20 - vx) / nv
    if cw < 56: raise ValueError(f'flag-soa 一页最多放 {int((cw_ - 40 - nw) / 56)} 个访视，当前 {nv} 个；逐项明细用静态模板 soa（按访视分页）')
    X = lambda i: vx + cw * (i + .5); prim = set(m['primary'])
    head = text(x0 + 20, y0 + 14, cw_ - 40, data['title'], TY['card_title'], INK['title'], True, lead=1.3)
    named = [p for p in m['periods'] if p['name']]
    for k, p in enumerate(named):
        xa, xb = vx + p['from'] * cw + 2, vx + p['to'] * cw - 2; col = PH[min(len(PH) - 1, round(k * (len(PH) - 1) / max(1, len(named) - 1)))]
        head += chevron(xa, xb, y0 + 62, 22, col, k > 0, True)
        lab = p['name'] if tw(p['name'], 14, True) * KT.HEADROOM < xb - xa - 14 else p['name'][:max(1, int((xb - xa - 14) / 15))]
        head += text(xa + 6, y0 + 52, xb - xa - 14, lab, 14, on_color(col), True, 'middle', lead=20 / 14)
    for i, v in enumerate(V):
        head += text(X(i) - cw / 2, y0 + 80, cw, v['v'], 16, F['accent_ink'] if i in prim else INK['title'], True, 'middle', lead=20 / 16)
        if v.get('week'): head += text(X(i) - cw / 2, y0 + 100, cw, v['week'], 14, INK['muted'], False, 'middle', lead=18 / 14)
    pg.role('card_title', TY['card_title'], data['title'], 1.3)
    out += pg.group(f'{gid}-head', x0, y0, cw_, 120, head, 0, 'entrance_fade')
    # primary-endpoint columns: a pale tint behind everything below the header
    out += deco(''.join(f'<rect x="{f(vx + i * cw + 2)}" y="{f(y0 + 76)}" width="{f(cw - 4)}" height="{f(ch - 86)}" rx="10" fill="{L1["focus_row"]}"/>' for i in sorted(prim)))
    # key events
    ey = y0 + 122; ev = ''
    at = {}
    for e in m['events']: at.setdefault(e['i'], []).append(e)
    lines = max([len(KT.wrap('、'.join(e['label'] for e in es), cw - 4, 14, True)) for es in at.values()] + [1])
    if lines > 2: raise ValueError('flag-soa 关键节点名称放不下两行；缩短 label 或减少访视数')
    EH = (22 + lines * 18) if m['events'] else 0
    if m['events']:
        ev += text(x0 + 20, ey + EH / 2 - 11, nw - 8, '关键节点', 16, INK['title'], True, lead=22 / 16)
        for i, es in at.items():
            kinds = [e['kind'] for e in es]; k = 'primary' if 'primary' in kinds else 'random' if 'random' in kinds else kinds[0]
            ev += gem(X(i), ey + 9, 8, True, False, k == 'primary') if k in ('primary', 'random') else f'<circle cx="{f(X(i))}" cy="{f(ey + 9)}" r="4.5" fill="{INK["muted"]}"/>'
            lab = '、'.join(e['label'] for e in es)
            ev += para(X(i) - cw / 2 + 2, ey + 19, cw - 4, lab, 14, F['accent_ink'] if k == 'primary' else INK['body'], k == 'primary', 'middle', lead=18 / 14, max_lines=2)[0]
        out += pg.group(f'{gid}-events', x0 + 14, ey, cw_ - 28, EH, ev, 1, 'entrance_fade', figure=True)
    # treatment periods
    by = ey + EH + (4 if EH else 0); BH = 24; bd = ''
    for k, b in enumerate(m['bands']):
        cy = by + k * BH + BH / 2; a_, z_ = vx + b['from'] * cw + 4, vx + (b['to'] + 1) * cw - 4
        fill, ink, dash = SOA_STRIP[b['kind']]
        bd += text(x0 + 20, cy - 11, nw - 8, b['label'], 16, INK['title'], True, lead=22 / 16)
        bd += f'<rect x="{f(a_)}" y="{f(cy - 9)}" width="{f(z_ - a_)}" height="18" rx="9" fill="{fill}"' + (f' stroke="{ink}" stroke-width="1.2" stroke-dasharray="4 3"' if dash else '') + '/>'
        if b['text']:
            t_ = b['text'] if tw(b['text'], 14) * KT.HEADROOM <= z_ - a_ - 16 else b['label']
            bd += text(a_ + 8, cy - 9, z_ - a_ - 16, t_, 14, ink, False, 'middle', lead=18 / 14)
    if m['bands']:
        out += pg.group(f'{gid}-bands', x0 + 14, by, cw_ - 28, len(m['bands']) * BH, bd, 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    # assessments item by item
    ry0 = by + len(m['bands']) * BH + 6; nit = sum(1 for r in rows if r[0] == 'item')
    rh = (y0 + ch - 10 - ry0) / max(1, nit)
    if rh < 24: raise ValueError(f'flag-soa 放不下 {nit} 个评估项目（每行 <24 px）；用 sections / items 选择本页的内容，其余放下一页，逐项全表用静态 soa')
    rh = min(rh, 34); body = ''; fr = ''; y = ry0; si = -1; ix = x0 + 20 + sw
    for k, (kind, r) in enumerate(rows):
        if kind == 'sec':   # the section name, centred beside its rows, with a hairline bracket
            si += 1; nk = next((j for j in range(k + 1, len(rows)) if rows[j][0] == 'sec'), len(rows)) - k - 1; hh = nk * rh
            body += para(x0 + 20, y + hh / 2 - (19 if tw(r, 14, True) > sw - 22 else 10), sw - 14, r, 14, INK['muted'], True, lead=19 / 14, max_lines=2)[0]
            body += f'<line x1="{f(ix - 6)}" y1="{f(y + 4)}" x2="{f(ix - 6)}" y2="{f(y + hh - 4)}" stroke="{CH["categorical"][si % len(CH["categorical"])]}" stroke-width="2" stroke-linecap="round"/>'
            if k: body += hline(x0 + 20, y, cw_ - 40)
            continue
        cy = y + rh / 2; fo = r['item'] == m['focus']; col = CH['categorical'][max(0, si) % len(CH['categorical'])]
        if fo: fr += f'<rect x="{f(ix - 2)}" y="{f(y + 1)}" width="{f(x0 + cw_ - 14 - ix + 2)}" height="{f(rh - 2)}" rx="8" fill="{L1["focus_row"]}"/>'
        body += text(ix, cy - 11, nw - sw - 8, r['item'], 16, F['accent_ink'] if fo else INK['title'], fo, lead=22 / 16)
        for i in r['marks']:
            body += gem(X(i), cy, 8, True, False, True) if fo and i in prim else f'<circle cx="{f(X(i))}" cy="{f(cy)}" r="5" fill="{col}"/>'
        y += rh
    out += deco(fr)
    pg.role('chart_label', 16, rows[0][1] if rows[0][0] == 'sec' else rows[0][1]['item'], 22 / 16)
    out += pg.group(f'{gid}-rows', x0 + 14, ry0, cw_ - 28, y - ry0, body, 2, 'entrance_wipe', figure=True, effect_options={'direction': 'down'})
    return out

# treatment period strips: fill, ink, dashed outline
SOA_STRIP = {'drug': (mix(TREAT, .55), F['accent_ink'], False), 'background': ('#E9ECEF', INK['body'], False),
             'rescue': ('#FFFFFF', F['accent_ink'], True), 'washout': ('#F4F5F6', INK['muted'], True), 'other': ('#F4F5F6', INK['body'], False)}

RENDER = {'flag-safety': safety_butterfly, 'flag-safety-dumbbell': safety_dumbbell, 'flag-program': program_chevron, 'flag-program-strip': program_strip, 'flag-exposure': exposure_steps, 'flag-exposure-plan': exposure_plan_board, 'flag-trialflow': trialflow_board, 'flag-landscape': landscape_rows, 'flag-efficacy': efficacy_board, 'flag-soa': soa_board}
