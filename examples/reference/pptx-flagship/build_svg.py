#!/usr/bin/env python3
"""Author the flagship F1 PPTX reference (14 FLAG-10) into an existing ppt-master project.

Same synthetic brief and numbers as the HTML flagship reference (../htmlppt-flagship). Backgrounds come from the
flagship set (cover visual, warm canvas); the header (facet mark with the chapter number, chapter name, title, logo, chips), the page progress and
the footer are native objects (14 FLAG-04); cards are white paper cards with one native outer shadow and the F1
components (14 FLAG-05); body pages use the flagship layout library (14 FLAG-08: flag-cols, flag-flow, flag-chart,
flag-gantt); the chart is a native chart, the Gantt native shapes; animations follow the HTML scene order, scene 0 on
entry and each later scene on a click (14 FLAG-06/10, 06 MOTION-07).

Executor-side authoring only; checking and export stay with ppt-master. Usage:
  python3 examples/reference/pptx-flagship/build_svg.py <ppt-master project dir>
Text is fitted with the Microsoft YaHei metrics of tools/kz_layouts/text.py; a line that does not fit raises instead
of shrinking (03 TYPE-03).
"""
from pathlib import Path
from html import escape
import argparse, json, re, shutil, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from kz_layouts import text as KT, svg as KS  # noqa: E402

T = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
F, C = T['flagship'], T['colors']
TY, G, INK = F['type_px'], F['geometry'], F['ink']
FONT = 'Microsoft YaHei, Arial'
DATE = '2026年11月'
TITLE = '研究资料完整性核对（合成示例）'
W, H = 1280, 720
MX = G['margin_x']; BODY_T = G['body_top']; BODY_B = H - G['body_bottom']; GAP = G['gap']
PADY, PADX = G['card_pad']
NUM_INK = F['numeral']['stops'][-1][0]          # solid numerals (KPI): the deep end of the numeral ramp
MK, NU = F['mark'], F['numeral']
DEPT = {k: v['color'] for k, v in T['departments'].items()}

def rgba(s):
    """'rgba(r,g,b,a)' or '#RRGGBB' → (hex, alpha)."""
    m = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', s)
    return (f'#{int(m[1]):02X}{int(m[2]):02X}{int(m[3]):02X}', float(m[4])) if m else (s, 1.0)

def f(n):
    return f'{n:.1f}'.rstrip('0').rstrip('.')

# ---------- primitives ----------
def defs():
    sh = F['card']['pptx_shadow']; k = 4 / 3   # pt → px
    stops = lambda name, ss: f'<linearGradient id="{name}" x1="0" y1="0" x2="1" y2="1">' + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in ss) + '</linearGradient>'
    rule = ''.join(f'<stop offset="{o}" stop-color="{rgba(c)[0]}" stop-opacity="{rgba(c)[1]}"/>' for c, o in F['rule']['stops'])
    mark = ''.join(stops(f'kzf-mark-{k}', [(c, o) for c, o in ss]) for k, ss in enumerate(MK['fills']))
    gloss = f'<linearGradient id="kzf-mark-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="{MK["gloss"]}"/><stop offset="0.45" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
    mx, my, mb, mc = MK['shadow']; mc, ma = rgba(mc)
    # numerals (FLAG-07): gradient face + one hard shadow for depth (PowerPoint text takes a single effect)
    num = '<linearGradient id="kzf-numeral" x1="0" y1="0" x2="0.35" y2="1">' + ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in NU['stops']) + '</linearGradient>'
    depth = ''.join(f'<filter id="kzf-depth-{k}"><feDropShadow dx="{f(d)}" dy="{f(d)}" stdDeviation="0.5" flood-color="{NU["extrude"][len(NU["extrude"]) // 2]}" flood-opacity="1"/></filter>'
                    for k, d in (('toc', depth_px(TY['toc_numeral'])), ('section', depth_px(TY['section_numeral']))))
    return ('<defs>' + stops('kzf-tile', F['tile']['stops']) + mark + gloss + num + depth
            + f'<filter id="kzf-mark-shadow"><feDropShadow dx="{mx}" dy="{my}" stdDeviation="{f(mb / 2)}" flood-color="{mc}" flood-opacity="{ma}"/></filter>'
            + f'<linearGradient id="kzf-rule" x1="0" y1="0" x2="1" y2="0">{rule}</linearGradient>'
            # one native outer shadow per object (ppt-master: one effect per object)
            + f'<filter id="kzf-card"><feDropShadow dx="0" dy="{f(sh["dist_pt"] * k)}" stdDeviation="{f(sh["blur_pt"] * k / 2)}" flood-color="{sh["color"]}" flood-opacity="{sh["alpha"]}"/></filter>'
            + '</defs>')

def para(x, y, w, markup, size, color=None, bold=False, align='start', lead=1.35, max_lines=1):
    """One native paragraph fitted to width w; returns (svg, height). Raises when it needs more than max_lines."""
    lines = KT.wrap(markup, w, size, bold)
    if len(lines) > max_lines:
        raise ValueError(f'放不下（{len(lines)} 行 > {max_lines}）：{KT.plain(markup)}')
    return KS.text_svg({'lines': lines, 'size': size, 'lead': lead, 'align': align, 'x': x, 'w': w, 'y': y,
                        'color': color or INK['body'], 'bold': bold}), len(lines) * size * lead

def text(*a, **k):
    return para(*a, **k)[0]

def depth_px(size):
    return min(NU['pptx_depth_em'] * size, NU['pptx_depth_max_px'])

def numeral(x, y, w, s, size, lead, kind):
    # gradient run fill + the page's hard depth shadow on the text shape
    return text(x, y, w, s, size, 'url(#kzf-numeral)', True, lead=lead).replace('<text ', f'<text filter="url(#kzf-depth-{kind})" ', 1)

def mark_paths(x, y, k):
    # the H2 tile facets (tokens.flagship.mark.paths: absolute M/H/L commands in the view box) baked into slide coordinates
    sx, sy = MK['w'] / MK['view'][0], MK['h'] / MK['view'][1]
    pts, cur = [], [0.0, 0.0]
    for cmd, args in re.findall(r'([MLHVZ])([^MLHVZ]*)', MK['paths'][k]):
        v = [float(a) for a in args.replace(',', ' ').split()]
        if cmd in 'ML': cur = v[:2]
        elif cmd == 'H': cur = [v[0], cur[1]]
        elif cmd == 'V': cur = [cur[0], v[0]]
        else: continue
        pts.append(f'{"M" if not pts else "L"} {f(x + cur[0] * sx)} {f(y + cur[1] * sy)}')
    return ' '.join(pts) + ' Z'

def tw(s, size, bold=False):
    return KT.width(KT.plain(s), size, bold)

def card_rect(x, y, w, h, face=None, r=None):
    bc, ba = rgba(F['card']['border'])
    return (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{r or F["card"]["radius"]}" fill="{face or F["card"]["face"]}" '
            f'stroke="{bc}" stroke-opacity="{ba}" stroke-width="1" filter="url(#kzf-card)"/>')

def icon(name, x, y, size, color):
    return f'<use data-icon="kangzhe/{name}" x="{f(x)}" y="{f(y)}" width="{f(size)}" height="{f(size)}" fill="{color}"/>'

def tag(x_right, cy, label, kind):
    bg, ink = F['tag'][kind]; w = tw(label, TY["label"], True) + 14; h = 26
    return (f'<rect x="{f(x_right - w)}" y="{f(cy - h / 2)}" width="{f(w)}" height="{h}" rx="7" fill="{bg}"/>'
            + text(x_right - w, cy - h / 2, w, label, TY['label'], ink, True, 'middle', lead=h / TY['label'])), w

def hline(x, y, w):
    return f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + w)}" y2="{f(y)}" stroke="{F["line"]}" stroke-width="1"/>'

# ---------- registry: groups per page (scene, effect) for animations.json, roles for the page-plan ----------
class Page:
    def __init__(self, pid, kind, title, template=None):
        self.pid, self.kind, self.title, self.template = pid, kind, title, template
        self.groups, self.els, self.cards = [], [], []
    def role(self, role, size, txt, lh=1.25):
        self.els.append({'id': f'{self.pid}-{role}-{len(self.els)}', 'role': role, 'font_px': size, 'line_height': lh, 'text': KT.plain(txt)})
    def group(self, gid, x, y, w, h, inner, scene=0, effect='entrance_fade', card=False, figure=False, **opt):
        self.groups.append((gid, scene, effect, opt))
        if card: self.cards.append(gid)
        waive = ' data-kz-emphasis="not_applicable"' if figure else ''   # axis and task labels, no running text (03 COPY-04)
        return f'<g id="{gid}" data-pptx-bounds="{f(x)} {f(y)} {f(w)} {f(h)}"{waive}>{inner}</g>'

def svg_page(role, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" lang="zh-CN" font-family="{FONT}" data-pptx-page-role="{role}">'
            + defs() + inner + '</svg>\n')

def bg(name):
    return f'<image id="bg" data-pptx-role="background" href="../images/{name}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'

LOGO_RATIO = 1210 / 250
def logo(hero):
    h = 34 if hero else G['logo_h']; w = h * LOGO_RATIO
    x, y = (MX, 46) if hero else (W - MX - w, G['head_top'] + 2)
    return f'<image id="logo" data-pptx-role="logo" href="../images/logo.png" x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" preserveAspectRatio="xMidYMid meet"/>'

def header(pg, kicker, chips):
    # FLAG-06 H2 tile: the chapter icon in the orange facet; the kicker keeps "02 资料完整性" whole
    x0, y0 = MX, G['head_top']; mw, mh = MK['w'], MK['h']; my0 = y0 + 21 - mh / 2
    ic = CHAPTERS[int(kicker.split()[0]) - 1][0]
    pg.role('page_title', TY['page_title'], pg.title)
    mark = (f'<path d="{mark_paths(x0, my0, 0)}" fill="url(#kzf-mark-0)" filter="url(#kzf-mark-shadow)"/>'
            + f'<path d="{mark_paths(x0, my0, 0)}" fill="url(#kzf-mark-g)"/>'
            + f'<path d="{mark_paths(x0, my0, 1)}" fill="url(#kzf-mark-1)"/>')
    s = MK['icon'] * mw / MK['view'][0]
    mark += icon(ic, x0 + MK['icon_at'][0] * mw / MK['view'][0] - s / 2, my0 + MK['icon_at'][1] * mh / MK['view'][1] - s / 2, s, MK['icon_ink'])
    tx = x0 + mw + 8
    k = text(tx, y0 - 3, 600, kicker, TY['kicker'], INK['kicker'], True, lead=1.3)
    ttl = text(tx, y0 + 15, 760, pg.title, TY['page_title'], INK['title'], True, lead=1.25)
    out = f'<g id="header" data-pptx-role="header" data-pptx-bounds="{x0} {f(my0)} 860 {f(y0 + 68 - my0)}">{mark}{k}{ttl}</g>'
    if chips:
        cf, ca = rgba(F['chip']['face']); bc, ba = rgba(F['chip']['border'])
        x, items = W - MX, ''
        for c in reversed(chips):
            w = tw(c, TY['chip'], True) + 26; x -= w
            items += (f'<rect x="{f(x)}" y="{G["chip_top"]}" width="{f(w)}" height="28" rx="14" fill="{cf}" fill-opacity="{ca}" stroke="{bc}" stroke-opacity="{ba}"/>'
                      + text(x, G['chip_top'], w, c, TY['chip'], F['chip']['ink'], True, 'middle', lead=28 / TY['chip']))
            x -= 8
        out += f'<g id="chips" data-pptx-role="header" data-pptx-bounds="{f(x)} {G["chip_top"]} {f(W - MX - x)} 28">{items}</g>'
    return out

def chrome_foot(pg, i, n):
    pr = F['progress']; seg = (W - 2 * MX - (n - 1) * pr['gap']) / n; y = H - G['progress_bottom']
    tc, ta = rgba(pr['track'])
    segs = ''.join(f'<rect x="{f(MX + k * (seg + pr["gap"]))}" y="{y}" width="{f(seg)}" height="{pr["height"]}" rx="1" '
                   + (f'fill="{pr["on"][-1][0]}"' if k <= i else f'fill="{tc}" fill-opacity="{ta}"') + '/>' for k in range(n))
    fy = H - G['foot_bottom'] - 24
    pg.role('footer', TY['foot'], F['identity']['name'])
    left = text(MX, fy, 700, f'{F["identity"]["name"]}　｜　{TITLE}', TY['foot'], INK['foot'], lead=1.5)
    num = text(W - MX - 120, fy, 120, f'{i + 1:02d} / {n:02d}', TY['foot'], INK['foot'], True, 'end', lead=1.5)
    return (f'<g id="progress" data-pptx-role="decoration" data-pptx-bounds="{MX} {y} {W - 2 * MX} {pr["height"]}">{segs}</g>'
            f'<g id="footer" data-pptx-role="footer" data-pptx-bounds="{MX} {fy} 700 24">{left}</g>'
            f'<g id="page-number" data-pptx-role="page-number" data-pptx-bounds="{W - MX - 120} {fy} 120 24">{num}</g>')

# ---------- card components (14 FLAG-05) ----------
def rows_block(x, y, w, h, items, kind):
    """Rows that share the spare height (capped), so equal-height sibling cards stay balanced (03 COPY-10)."""
    n = len(items); gap = 9 if kind == 'pill' else 0
    natural = {'pill': 40, 'row': 40, 'row2': 52, 'check': 34, 'step': 32}[kind]
    rh = max(natural, min(62, (h - gap * (n - 1)) / n)); out = ''
    for k, it in enumerate(items):
        ry = y + k * (rh + gap); cy = ry + rh / 2
        if kind == 'pill':
            label, value = it
            out += f'<rect x="{f(x)}" y="{f(ry)}" width="{f(w)}" height="{f(rh)}" rx="9" fill="{F["pill"]["face"]}" stroke="{F["pill"]["border"]}"/>'
            out += text(x + 12, cy - 11, w * .6, label, TY['body'], INK['body'], lead=22 / TY['body'])
            vw = tw(value, TY['label'], True) + 20
            out += f'<rect x="{f(x + w - 10 - vw)}" y="{f(cy - 12)}" width="{f(vw)}" height="24" rx="12" fill="#FFFFFF" stroke="{F["pill"]["border"]}"/>'
            out += text(x + w - 10 - vw, cy - 12, vw, value, TY['label'], INK['title'], True, 'middle', lead=24 / TY['label'])
        elif kind in ('row', 'row2'):
            label, sub, tkind, tlabel = it
            g, tw_ = tag(x + w, cy, tlabel, tkind)
            if sub:
                out += text(x, cy - 22, w - tw_ - 10, label, TY['body'], INK['title'], lead=1.4)
                out += text(x, cy, w - tw_ - 10, sub, TY['label'], INK['muted'], lead=1.4)
            else:
                out += text(x, cy - 11, w - tw_ - 10, label, TY['body'], INK['title'], lead=22 / TY['body'])
            out += g + hline(x, ry + rh - .5, w)
        elif kind == 'check':
            out += text(x, cy - 11, w - 30, it, TY['body'], INK['body'], lead=22 / TY['body'])
            out += icon('check', x + w - 20, cy - 10, 20, F['tag']['ok'][1])
        elif kind == 'step':
            hf = F['head']
            out += f'<rect x="{f(x)}" y="{f(cy - 10)}" width="20" height="20" rx="6" fill="{hf["face"]}" stroke="{hf["border"]}"/>'
            out += text(x, cy - 10, 20, str(k + 1), TY['label'], hf['num'], True, 'middle', lead=20 / TY['label'])
            out += text(x + 30, cy - 11, w - 30, it, TY['body'], INK['body'], lead=22 / TY['body'])
    return out, n * rh + gap * (n - 1)

def note(x, y_bottom, w, markup):
    s, h = para(x, y_bottom - 30, w, markup, TY['note'], INK['body'], True, lead=1.4)
    return hline(x, y_bottom - 36, w) + s

def kpi(pg, gid, x, y, w, h, value, unit, label, desc, scene, risk=False):
    vw = tw(value, TY['kpi_numeral'], True)
    inner = (card_rect(x, y, w, h)
             + text(x + PADX, y + 18, vw + 8, value, TY['kpi_numeral'], C['risk'] if risk else NUM_INK, True, lead=1.15)
             + (text(x + PADX + vw + 6, y + 18 + TY['kpi_numeral'] * 1.15 - 30, 60, unit, TY['kpi_unit'], INK['muted'], True, lead=1.4) if unit else '')
             + text(x + PADX, y + 18 + TY['kpi_numeral'] * 1.15 + 6, w - 2 * PADX, label, TY['kpi_label'], INK['title'], True, lead=1.3)
             + text(x + PADX, y + 18 + TY['kpi_numeral'] * 1.15 + 34, w - 2 * PADX, desc, TY['label'], INK['muted'], lead=1.4))
    pg.role('body', TY['label'], desc, 1.4)
    return pg.group(gid, x, y, w, h, inner, scene, 'entrance_zoom' if risk else 'entrance_fade', card=True)

def band(pg, gid, y, h, lead_title, lead_sub, segs, scene):
    x, w = MX, W - 2 * MX
    inner = card_rect(x, y, w, h)
    inner += text(x + 22, y + h / 2 - 26, 200, lead_title, TY['card_title'], INK['title'], True, lead=1.3)
    inner += text(x + 22, y + h / 2 + 2, 200, lead_sub, TY['label'], INK['muted'], lead=1.4)
    sx = x + 240; sw = (x + w - 14 - sx - 3 * 14) / 4
    for k, (a, b) in enumerate(segs):
        bx = sx + k * (sw + 14)
        inner += f'<rect x="{f(bx)}" y="{f(y + 12)}" width="{f(sw)}" height="{f(h - 24)}" rx="9" fill="{F["pill"]["face"]}"/>'
        inner += text(bx + 16, y + h / 2 - 25, sw - 32, a, TY['label'], INK['muted'], lead=1.45)
        inner += text(bx + 16, y + h / 2 + 1, sw - 32, b, TY['body'], INK['title'], True, lead=1.45)
    pg.role('card_title', TY['card_title'], lead_title, 1.3)
    return pg.group(gid, x, y, w, h, inner, scene, 'entrance_wipe', effect_options={'direction': 'left'})

def column_card(pg, gid, x, y, w, h, title, items, kind, note_md, scene, lede=None):
    inner = card_rect(x, y, w, h); cy = y + PADY
    if title:
        s, th = para(x + PADX, cy, w - 2 * PADX, title, TY['card_title'], INK['title'], True, lead=1.3)
        inner += s; cy += th + 10; pg.role('card_title', TY['card_title'], title, 1.3)
    if lede:
        s, lh = para(x + PADX, cy, w - 2 * PADX, lede, TY['label'], INK['muted'], lead=1.4, max_lines=2)
        inner += s; cy += lh + 10; pg.role('body', TY['label'], lede, 1.4)
    bottom = y + h - PADY - (44 if note_md else 0)
    rows, _ = rows_block(x + PADX, cy, w - 2 * PADX, bottom - cy - 8, items, kind)
    inner += rows
    if note_md:
        inner += note(x + PADX, y + h - PADY + 4, w - 2 * PADX, note_md); pg.role('body', TY['note'], note_md, 1.4)
    return pg.group(gid, x, y, w, h, inner, scene, 'entrance_rise_up', card=True)

# ---------- pages ----------
CHAPTERS = [('doc', '研究范围', '对象、时间窗与四组资料'), ('clipboard-check', '资料完整性', '应收与已收、缺口所在'),
            ('git-compare', '差异处理', '版本差异的判定与关闭'), ('calendar-stats', '核对计划', '补收、确认与复核排期')]

def cover(pg):
    x = MX; inner = bg('flagship-cover.jpg') + logo(True)
    kick = text(x, 178, 700, '医学部 · 管理层季度汇报', TY['cover_kicker'], INK['kicker'], True, lead=1.3)
    lines =[[('研究资料', frozenset())], [('完整性核对', frozenset())]]
    title = KS.text_svg({'lines': lines, 'size': TY['cover_title'], 'lead': 1.12, 'align': 'start', 'x': x, 'w': 700, 'y': 206, 'color': INK['title'], 'bold': True})
    rule = f'<rect id="cover-rule" data-pptx-role="decoration" x="{x}" y="{206 + 2 * 80 * 1.12 + 22}" width="467" height="{F["rule"]["height"]}" rx="1.5" fill="url(#kzf-rule)"/>'
    ly = 206 + 2 * 80 * 1.12 + 44
    lede = text(x, ly, 760, '应收 24 份、已收 20 份；缺口集中在**中心记录与安全性报告**', TY['cover_lede'], INK['body'], lead=1.4)
    cf, ca = rgba(F['chip']['face']); bc, ba = rgba(F['chip']['border']); cx, chips = x, ''
    for i, (_, t, _) in enumerate(CHAPTERS):
        lab = f'{i + 1:02d} {t}'; w = tw(lab, TY['cover_chip'], True) + 30
        chips += (f'<rect x="{f(cx)}" y="{f(ly + 54)}" width="{f(w)}" height="34" rx="17" fill="{cf}" fill-opacity="{ca}" stroke="{bc}" stroke-opacity="{ba}"/>'
                  + KS.text_svg({'lines': [[(f'{i + 1:02d} ', frozenset()), (t, frozenset())]], 'size': TY['cover_chip'], 'lead': 34 / TY['cover_chip'], 'align': 'middle',
                                 'x': cx, 'w': w, 'y': ly + 54, 'color': INK['title'], 'bold': True}))
        cx += w + 10
    meta = text(x, H - 62, 600, f'{F["identity"]["name"]} · {DATE}', TY['cover_meta'], INK['body'], True, lead=1.4)
    pg.role('cover_title', TY['cover_title'], '研究资料完整性核对', 1.12)
    pg.role('hero_subtitle', TY['cover_lede'], '应收 24 份、已收 20 份；缺口集中在中心记录与安全性报告', 1.4)
    pg.role('hero_meta', TY['cover_meta'], f'{F["identity"]["name"]} · {DATE}', 1.4)
    inner += rule
    inner += pg.group('cover-title', x, 170, 760, 240, kick + title, 0, 'entrance_rise_up')
    inner += pg.group('cover-lede', x, ly - 4, 760, 40, lede, 0, 'entrance_fade')
    inner += pg.group('cover-chips', x, ly + 54, cx - x, 34, chips, 0, 'entrance_fade')
    inner += pg.group('cover-meta', x, H - 62, 600, 26, meta, 0, 'entrance_fade')
    return svg_page('cover', inner)

def toc(pg, i, n):
    inner = bg('flagship-canvas.jpg') + logo(True)
    inner += pg.group('toc-title', MX, 120, 700, 120,
                      text(MX, 124, 400, 'CONTENTS', TY['toc_kicker'], INK['kicker'], True, lead=1.3)
                      + text(MX, 146, 700, '汇报章节', TY['toc_title'], INK['title'], True, lead=1.25), 0, 'entrance_rise_up')
    pg.role('toc_title', TY['toc_title'], '汇报章节')
    cw = (W - 2 * MX - 3 * 24) / 4; y, h = 290, 272
    for k, (ic, t, d) in enumerate(CHAPTERS):
        x = MX + k * (cw + 24); hf = F['head']
        c = (card_rect(x, y, cw, h)
             + f'<rect x="{f(x + 22)}" y="{y + 24}" width="40" height="40" rx="11" fill="{hf["face"]}"/>' + icon(ic, x + 31, y + 33, 22, F['accent_ink'])
             + numeral(x + 22, y + 82, cw - 44, f'{k + 1:02d}', TY['toc_numeral'], 1.1, 'toc')
             + text(x + 22, y + h - 92, cw - 44, t, TY['toc_card_title'], INK['title'], True, lead=1.3)
             + text(x + 22, y + h - 50, cw - 44, d, TY['toc_card_desc'], INK['muted'], lead=1.45))
        inner += pg.group(f'toc-{k + 1}', x, y, cw, h, c, 0, 'entrance_rise_up', card=True)
        pg.role('toc_number', TY['toc_numeral'], f'{k + 1:02d}', 1.1); pg.role('toc_label', TY['toc_card_title'], t, 1.3)
        pg.role('toc_description', TY['toc_card_desc'], d, 1.45)
    return svg_page('toc', inner + chrome_foot(pg, i, n))

def section(pg, i, n, ch):
    icon_name, title, lede = CHAPTERS[ch - 1]
    inner = bg('flagship-canvas.jpg') + logo(True)
    inner += pg.group('section-number', MX - 8, 190, 380, 362,
                      numeral(MX - 8, 196, 380, f'{ch:02d}', TY['section_numeral'], 1.0, 'section'), 0, 'entrance_zoom')
    tx = 466
    inner += pg.group('section-text', tx, 250, 420, 170,
                      text(tx, 258, 400, f'第{"一二三四"[ch - 1]}部分', TY['section_kicker'], INK['kicker'], True, lead=1.3)
                      + text(tx, 290, 420, title, TY['section_title'], INK['title'], True, lead=1.25)
                      + text(tx, 378, 420, lede, TY['section_lede'], INK['body'], lead=1.4), 0, 'entrance_fade')
    lx, ly, items = 936, 200, ''
    for k, (_, t, _) in enumerate(CHAPTERS):
        yy = ly + k * 53
        if k == ch - 1:
            items += card_rect(lx, yy, W - MX - lx, 48, r=10)
        items += KS.text_svg({'lines': [[(f'{k + 1:02d}', frozenset())]], 'size': TY['section_toc'], 'lead': 48 / TY['section_toc'], 'align': 'start',
                              'x': lx + 16, 'w': 40, 'y': yy, 'color': F['accent_ink'] if k == ch - 1 else INK['title'], 'bold': False})
        items += text(lx + 52, yy, 200, t, TY['section_toc'], INK['title'] if k == ch - 1 else INK['muted'], k == ch - 1, lead=48 / TY['section_toc'])
    inner += pg.group('section-toc', lx, ly, W - MX - lx, 4 * 53, items, 0, 'entrance_fade')
    pg.role('section_number', TY['section_numeral'], f'{ch:02d}', 1.0); pg.role('section_title', TY['section_title'], title)
    return svg_page('section', inner + chrome_foot(pg, i, n))

def scope(pg, i, n):
    inner = bg('flagship-canvas.jpg') + logo(False) + header(pg, '01 研究范围', ['合成示例数据', '牵头：医学部'])
    bh = 92; ch = BODY_B - BODY_T - GAP - bh; cw = (W - 2 * MX - 2 * GAP) / 3
    cols = [
        ('研究对象与时间窗', [('研究对象', '成人受试者'), ('筛选期', '4 周'), ('评价时间窗', '第 16 周'), ('参与中心', '12 家')], 'pill', '范围外的资料**只作背景**，不进核对表'),
        ('纳入资料（4 组）', [('方案与修订', '2 份'), ('中心记录', '12 份'), ('实验室数据', '6 份'), ('安全性报告', '4 份')], 'pill', '应收合计 **24 份**'),
        ('方案版本比对', [('版本号', 'V2.1 / V2.3', 'ok', '已登记'), ('入组标准', '两版一致', 'ok', '一致'), ('筛选窗口', '**28 天 / 35 天**', 'wait', '待确认'), ('终点时间点', '**第 16 / 24 周**', 'wait', '待确认')], 'row', '!!2 项!!确认之前，先不做组间比较'),
    ]
    for k, (t, items, kind, nt) in enumerate(cols):
        inner += column_card(pg, f'scope-{k + 1}', MX + k * (cw + GAP), BODY_T, cw, ch, t, items, kind, nt, 0)
    inner += band(pg, 'scope-band', BODY_B - bh, bh, '范围怎么用', '规则与档案同源',
                  [('写入核对规则', '对象与时间窗'), ('决定应收清单', '4 组 24 份'), ('标记版本差异', '2 项待确认'), ('转入统计', '空值随数据集传递')], 1)
    return svg_page('content', inner + chrome_foot(pg, i, n))

FLOW = [
    ('2.1', '资料清单', '按方案版本列出四组应收资料', [('方案与修订', '2'), ('中心记录', '12'), ('实验室数据', '6'), ('安全性报告', '4')], 'pill', '应收合计 **24 份**'),
    ('2.2', '上传识别', '中心上传后自动识别资料类型', ['检验报告', '影像报告', '门诊病历', '知情同意书'], 'check', '上传即**脱敏归类**'),
    ('2.3', '逐项比对', '对照方案逐项核对四个要素', [('版本号', '', 'ok', 'V2.3 符合'), ('签署日期', '', 'ok', '已签署'), ('访视窗', '', 'wait', '偏差 2 天'), ('页码', '', 'risk', '缺第 4 页')], 'row', '原文**定位到页**'),
    ('2.4', '差异判定', '四类结果按同一规则处理', [('未收到', '', 'risk', '空值'), ('版本不符', '', 'wait', '先确认'), ('页码缺失', '', 'wait', '补收'), ('一致', '', 'ok', '比较')], 'row', '空值**不按零**处理'),
    ('2.5', '补收跟进', '缺口由医学经理牵头补收', ['医学经理确认', 'CRA 联系中心', '中心补传', '重新比对'], 'step', '补收后**自动重新比对**'),
    ('2.6', '复核签署', '四项复核全部通过后签署', ['资料清单', '版本差异', '缺口处理', '签署人与日期'], 'check', '签署前**再核关键条目**'),
]

def flow(pg, i, n):
    inner = bg('flagship-canvas.jpg') + logo(False) + header(pg, '02 资料完整性', ['合成示例数据', '牵头：医学部 · 临床运营'])
    m = len(FLOW); cw = (W - 2 * MX - (m - 1) * GAP) / m; hh = 44; bh = 92
    cy = BODY_T + hh + 12; ch = BODY_B - bh - GAP - cy; hf = F['head']; heads = ''
    for k, (num, name, *_rest) in enumerate(FLOW):
        x = MX + k * (cw + GAP)
        heads += (f'<rect x="{f(x)}" y="{BODY_T}" width="{f(cw)}" height="{hh}" rx="{hf["radius"]}" fill="{hf["face"]}" stroke="{hf["border"]}"/>'
                  + KS.text_svg({'lines': [[(num + '  ', frozenset())]], 'size': TY['head_num'], 'lead': hh / TY['head_num'], 'align': 'start', 'x': x + 14, 'w': 40, 'y': BODY_T, 'color': hf['num'], 'bold': False})
                  + text(x + 50, BODY_T, cw - 60, name, TY['head'], INK['title'], True, lead=hh / TY['head']))
        if k < m - 1:
            heads += f'<circle cx="{f(x + cw + GAP / 2)}" cy="{BODY_T + hh / 2}" r="4" fill="{F["tile"]["stops"][1][0]}"/>'
    inner += pg.group('flow-heads', MX, BODY_T, W - 2 * MX, hh, heads, 0, 'entrance_wipe', effect_options={'direction': 'left'})
    for k, (num, name, lede, items, kind, nt) in enumerate(FLOW):
        inner += column_card(pg, f'flow-{k + 1}', MX + k * (cw + GAP), cy, cw, ch, None, items, kind, nt, 1, lede=lede)
    inner += band(pg, 'flow-band', BODY_B - bh, bh, '模块衔接', '规则 · 档案同源',
                  [('取自研究规则库', '核对要点与规则一致'), ('写入资料档案', '结论与缺口原因'), ('转入统计分析', '空值标记随数据集'), ('转入安全性复核', '安全性报告补收进度')], 2)
    return svg_page('content', inner + chrome_foot(pg, i, n))

CHART = {"name": "completeness-bars", "type": "column", "grouping": "clustered",
         "categories": ["方案与修订", "中心记录", "实验室数据", "安全性报告"],
         "series": [{"name": "应收", "values": [2, 12, 6, 4]}, {"name": "已收", "values": [2, 9, 6, 3]}],
         "axes": {"value": {"minimum": 0, "maximum": 15, "major_unit": 5}}, "data_labels": {"show_value": True}}

def chart(x, y, w, h):
    """Native column chart (ppt-master --native-charts-and-tables) with a drawn fallback the checker can read."""
    recv = T['charts']['categorical'][0]; px, py, pw, ph = x + 36, y + 14, w - 36, h - 62
    meta = dict(CHART, x=x, y=y, width=w, height=h, plot_area={"x": px, "y": py, "width": pw, "height": ph},
                style={"colors": [T['charts']['comparator'], recv], "axis_color": T['charts']['axis'], "grid_color": T['charts']['grid'], "text_color": INK['body'], "font_family": "Microsoft YaHei"})
    base = py + ph; scale = ph / 15; slot = pw / 4; bw = slot * 0.29
    grid = ''.join(f'<line x1="{f(px)}" y1="{base - v * scale:.2f}" x2="{f(px + pw)}" y2="{base - v * scale:.2f}"/>' for v in (5, 10, 15))
    ticks = ''.join(f'<text x="{f(px - 8)}" y="{base - v * scale + 5:.2f}">{v}</text>' for v in (0, 5, 10, 15))
    bars, labels = ['', ''], ''
    for i in range(4):
        for j, s in enumerate(CHART['series']):
            val = s['values'][i]; bx = px + slot * i + slot * 0.21 + j * bw; bh = val * scale
            bars[j] += f'<rect x="{bx:.2f}" y="{base - bh:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="4"/>'
            labels += f'<text x="{bx + bw / 2:.2f}" y="{base - bh - 8:.2f}">{val}</text>'
        labels += f'<text x="{px + slot * i + slot / 2:.2f}" y="{base + 26:.2f}">{CHART["categories"][i]}</text>'
    return (f'<g id="completeness-bars" data-pptx-bounds="{f(x)} {f(y)} {f(w)} {f(h)}" data-pptx-replace-with="chart">'
            f'<metadata type="application/json">{json.dumps(meta, ensure_ascii=False)}</metadata>'
            f'<g id="completeness-bars-chartArea"><g id="completeness-grid" stroke="{T["charts"]["grid"]}" stroke-width="1">{grid}</g>'
            f'<g font-size="16" fill="{INK["body"]}" text-anchor="end">{ticks}</g>'
            f'<line id="completeness-axis" x1="{f(px)}" y1="{f(base)}" x2="{f(px + pw)}" y2="{f(base)}" stroke="{T["charts"]["axis"]}" stroke-width="2"/>'
            f'<!-- chart-plot-area: object=completeness-bars | {f(px)},{f(py)},{f(px + pw)},{f(base)} -->'
            f'<g fill="{T["charts"]["comparator"]}">{bars[0]}</g><g fill="{recv}">{bars[1]}</g>'
            f'<g font-size="16" fill="{INK["body"]}" text-anchor="middle">{labels}</g></g></g>')

def side_list(pg, gid, x, y, w, h, title, items, note_md, scene):
    return column_card(pg, gid, x, y, w, h, title, items, 'row2' if any(it[1] for it in items) else 'row', note_md, scene)

def gaps(pg, i, n):
    inner = bg('flagship-canvas.jpg') + logo(False) + header(pg, '02 资料完整性', ['合成示例数据', '单位：份'])
    side = 360; cx, cw = MX, W - 2 * MX - side - GAP; sx = cx + cw + GAP; bh = BODY_B - BODY_T
    recv = T['charts']['categorical'][0]
    shell = card_rect(cx, BODY_T, cw, bh).replace('<rect ', '<rect id="chart-card" data-pptx-role="decoration" ', 1)
    head = (''
            + text(cx + PADX, BODY_T + PADY, 300, '应收与已收', TY['card_title'], INK['title'], True, lead=1.3)
            + text(cx + cw - PADX - 306, BODY_T + PADY + 2, 300, '缺口 = 应收 − 已收', TY['label'], INK['muted'], align='end', lead=1.4)
            + f'<rect x="{f(cx + PADX)}" y="{BODY_T + 56}" width="12" height="12" rx="3" fill="{T["charts"]["comparator"]}"/>'
            + text(cx + PADX + 24, BODY_T + 51, 60, '应收', TY['label'], INK['body'], lead=1.4)
            + f'<rect x="{f(cx + PADX + 76)}" y="{BODY_T + 56}" width="12" height="12" rx="3" fill="{recv}"/>'
            + text(cx + PADX + 94, BODY_T + 51, 60, '已收', TY['label'], INK['body'], lead=1.4))
    pg.role('card_title', TY['card_title'], '应收与已收', 1.3); pg.role('chart_label', 16, '份', 1.4)
    pg.cards.append('chart-card')
    inner += shell + pg.group('chart-head', cx + 1, BODY_T + 1, cw - 2, 80, head, 0, 'entrance_fade')
    inner += chart(cx + PADX, BODY_T + 84, cw - 2 * PADX, bh - 84 - PADY)
    pg.groups.append(('completeness-bars', 1, 'entrance_wipe', {'effect_options': {'direction': 'down'}}))
    kh = 150
    inner += kpi(pg, 'gap-kpi', sx, BODY_T, side, kh, '4', '份', '资料缺口', '中心记录 3 · 安全性报告 1', 2, risk=True)
    inner += side_list(pg, 'gap-list', sx, BODY_T + kh + GAP, side, bh - kh - GAP, '补收清单',
                       [('C-03 中心 A · 访视后未上传', '', 'wait', '补收中'), ('C-07 中心 B · 扫描件缺页', '', 'wait', '补收中'),
                        ('C-11 中心 B · 待确认', '', 'risk', '待确认'), ('S-02 PV · 安全性报告', '', 'wait', '补收中')],
                       '缺的记录**保留为空值**，不按零处理', 2)
    return svg_page('content', inner + chrome_foot(pg, i, n))

GANTT = {'min': (2026, 4), 'quarters': ['2026Q4', '2027Q1', '2027Q2'], 'tasks': [
    ('缺失资料补收', 0, 2, 'medical'), ('版本差异确认', 1, 2, 'medical'), ('完整性复核', 1, 3, 'statistics'),
    ('安全性报告核对', 1, 3, 'pv'), ('审阅意见形成', 2, 3, 'medical')]}

def gantt(x, y, w, h):
    """Quarter Gantt as native shapes (08): one model [start, end), department colours, quarter grid and labels."""
    lab = 140; px, pw = x + lab, w - lab; q = len(GANTT['quarters']); qw = pw / q; ah = 34
    rows = len(GANTT['tasks']); rh = (h - ah) / rows; out = ''
    for k in range(q + 1):
        out += f'<line x1="{f(px + k * qw)}" y1="{f(y)}" x2="{f(px + k * qw)}" y2="{f(y + h - ah)}" stroke="{T["charts"]["grid"]}" stroke-width="1"/>'
    for k, ql in enumerate(GANTT['quarters']):
        out += text(px + k * qw, y + h - ah + 6, qw, ql, TY['label'], INK['body'], align='middle', lead=1.4)
    for r, (name, s, e, dept) in enumerate(GANTT['tasks']):
        ry = y + r * rh
        out += text(x, ry + rh / 2 - 11, lab - 12, name, TY['label'], INK['body'], align='end', lead=22 / TY['label'])
        out += f'<rect x="{f(px + s * qw + 3)}" y="{f(ry + rh * .26)}" width="{f((e - s) * qw - 6)}" height="{f(rh * .48)}" rx="7" fill="{DEPT[dept]}" fill-opacity="0.82"/>'
    return out

def plan(pg, i, n):
    inner = bg('flagship-canvas.jpg') + logo(False) + header(pg, '04 核对计划', ['医学部 · 数统 · PV', '2026Q4 – 2027Q2'])
    side = 330; cx, cw = MX, W - 2 * MX - side - GAP; sx = cx + cw + GAP; bh = BODY_B - BODY_T
    shell = card_rect(cx, BODY_T, cw, bh).replace('<rect ', '<rect id="gantt-card" data-pptx-role="decoration" ', 1)
    card = (''
            + text(cx + PADX, BODY_T + PADY, 300, '季度安排', TY['card_title'], INK['title'], True, lead=1.3)
            + text(cx + cw - PADX - 306, BODY_T + PADY + 2, 300, '区间 [起, 止)', TY['label'], INK['muted'], align='end', lead=1.4))
    pg.role('card_title', TY['card_title'], '季度安排', 1.3)
    pg.cards.append('gantt-card')
    inner += shell + pg.group('gantt-head', cx + 1, BODY_T + 1, cw - 2, 60, card, 0, 'entrance_fade')
    gx, gy, gw, gh = cx + PADX, BODY_T + 70, cw - 2 * PADX, bh - 70 - PADY
    inner += pg.group('gantt', gx, gy, gw, gh, gantt(gx, gy, gw, gh), 1, 'entrance_wipe', figure=True, effect_options={'direction': 'left'})
    kh = 150
    inner += kpi(pg, 'plan-kpi', sx, BODY_T, side, kh, '2027Q1', '', '关键节点', '缺失资料补收与版本差异确认完成', 2)
    inner += side_list(pg, 'plan-list', sx, BODY_T + kh + GAP, side, bh - kh - GAP, '里程碑',
                       [('**4 份补收** · 2 项版本确认', '医学部', 'info', '2027Q1'), ('完整性复核', '数统', 'info', '2027Q2'),
                        ('安全性报告核对', 'PV', 'info', '2027Q2'), ('形成审阅意见', '医学部', 'info', '2027Q3 初')], None, 2)
    return svg_page('content', inner + chrome_foot(pg, i, n))

def ending(pg):
    inner = bg('flagship-canvas.jpg') + logo(True)
    t = F['ending']['text']
    inner += pg.group('ending-title', 340, 220, 600, 172, text(340, 224, 600, t, TY['ending_title'], INK['title'], True, 'middle', lead=1.2), 0, 'entrance_zoom')
    inner += f'<rect id="ending-rule" data-pptx-role="decoration" x="480" y="420" width="320" height="{F["rule"]["height"]}" rx="1.5" fill="url(#kzf-rule)"/>'
    inner += pg.group('ending-sub', 290, 440, 700, 40, text(290, 442, 700, TITLE, TY['ending_lede'], INK['body'], align='middle', lead=1.4), 0, 'entrance_fade')
    inner += pg.group('ending-meta', 390, H - 64, 500, 28, text(390, H - 62, 500, f'{F["identity"]["name"]} · {DATE}', TY['ending_meta'], INK['foot'], True, 'middle', lead=1.4), 0, 'entrance_fade')
    pg.role('ending_title', TY['ending_title'], t, 1.2)
    return svg_page('ending', inner)

# ---------- assemble ----------
PAGES = [('01_cover', 'cover', '研究资料完整性核对', None), ('02_toc', 'toc', '汇报章节', None), ('03_section', 'section', '研究范围', None),
         ('04_scope', 'body', '核对范围与资料分组', 'flag-cols'), ('05_flow', 'body', '资料核对六步', 'flag-flow'),
         ('06_gaps', 'body', '各资料组应收与已收', 'flag-chart'), ('07_plan', 'body', '核对计划', 'flag-gantt'), ('08_ending', 'ending', '谢谢', None)]

def build(project):
    svg_dir, img_dir, ico = project / 'svg_output', project / 'images', project / 'icons/kangzhe'
    for d in (svg_dir, img_dir, ico): d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / T['logo']['png_path'], img_dir / 'logo.png')
    for name, src in (('flagship-cover.jpg', 'cover.jpg'), ('flagship-canvas.jpg', 'canvas.jpg')):
        shutil.copy2(ROOT / 'assets/backgrounds/flagship' / src, img_dir / name)
    for fsvg in (ROOT / 'assets/icons/kangzhe').glob('*.svg'): shutil.copy2(fsvg, ico / fsvg.name)
    n = len(PAGES); pages, plan_pages = {}, []
    for i, (name, kind, title, tpl) in enumerate(PAGES):
        pg = Page(f'p{i + 1:02d}', kind, title, tpl)
        svg = {'01_cover': lambda: cover(pg), '02_toc': lambda: toc(pg, i, n), '03_section': lambda: section(pg, i, n, 1),
               '04_scope': lambda: scope(pg, i, n), '05_flow': lambda: flow(pg, i, n), '06_gaps': lambda: gaps(pg, i, n),
               '07_plan': lambda: plan(pg, i, n), '08_ending': lambda: ending(pg)}[name]()
        (svg_dir / f'{name}.svg').write_text(svg, encoding='utf-8'); pages[name] = pg
        page = {'id': pg.pid, 'kind': kind, 'title': title, 'body_profile': 'standard', 'elements': pg.els, 'protected_regions': [],
                'cards': [{'id': c, 'material': 'flagship_paper', 'edge_decoration': 'none', 'layout_mode': 'distributed',
                           'detail': 'not_needed', 'detail_reason': '合成示例页，卡内已给全量信息'} for c in pg.cards],
                'image': {'mode': 'flagship_set', 'asset_id': 'flagship-cover' if kind == 'cover' else 'flagship-canvas'},
                'sources': [{'id': 'brief', 'kind': 'internal', 'visible': False}]}
        if kind in ('cover', 'toc', 'section', 'ending'): page['hero_layout_id'] = f'flagship-{kind}'
        if tpl: page['template'] = tpl
        plan_pages.append(page)
    # animations: scene 0 runs on slide entry; each later scene starts on a click (14 FLAG-06/10)
    enter = T['motion']['duration_ms']['card'] / 1000; step = T['motion']['stagger_ms']['pptx_card'] / 1000
    slides = {}
    for name, pg in pages.items():
        groups, order, last_scene, k_in_scene = {}, 0, None, 0
        for gid, scene, effect, opt in sorted(pg.groups, key=lambda g: g[1]):
            order += 1
            k_in_scene = 0 if scene != last_scene else k_in_scene + 1
            trig = 'with-previous' if scene == 0 or k_in_scene else 'on-click'
            row = {'effect': effect, 'duration': T['motion']['duration_ms']['data'] / 1000 if 'wipe' in effect else enter,
                   'delay': round(k_in_scene * step, 3), 'trigger': trig, 'order': order}
            if effect in ('entrance_fade', 'entrance_wipe', 'entrance_zoom'): row['decelerate'] = 0.7
            row.update(opt); groups[gid] = row; last_scene = scene
        slides[name] = {'groups': groups}
    anim = {'defaults': {'transition': {'effect': 'fade', 'duration': 0.4}, 'animation': {'effect': 'none'}}, 'slides': slides}
    (project / 'animations.json').write_text(json.dumps(anim, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    plan_doc = {'schema_version': '6.1', 'contract_revision': '7.0', 'track': 'pptx', 'route': 'flagship', 'canvas': [W, H],
            'target_viewports': T['viewports'].get('pptx', [[W, H]]), 'pages': plan_pages}
    (project / 'page-plan.json').write_text(json.dumps(plan_doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return sorted(pages)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', type=Path); a = ap.parse_args()
    print(json.dumps({'pages': build(a.project.resolve())}, ensure_ascii=False))
