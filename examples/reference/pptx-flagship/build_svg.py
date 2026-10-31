#!/usr/bin/env python3
"""Author the flagship PPTX probe (14 FLAG-10) into an existing ppt-master project: light plates rendered by
tools/flagship_plate.py as page backgrounds, baked lens pictures under native glass shells (frosted reading area,
refracted rim, as the HTML lens filter), the identity capsule instead of body chrome, a native column chart, and
animations.json (06 MOTION-07).

Executor-side authoring only; checking and export stay with ppt-master. Usage:
  python3 examples/reference/pptx-flagship/build_svg.py <ppt-master project dir>
"""
from pathlib import Path
from html import escape
import argparse, hashlib, json, shutil, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from flagship_plate import lens, render, save  # noqa: E402
T = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
F, C = T['flagship'], T['colors']
TY = F['type_px']
FONT = 'Microsoft YaHei, Arial'
NUM = 'Arial'                       # PowerPoint has no portable thin face: numerals use regular Arial (static approximation)
DATE = '2026年10月'
SR = '#' + ''.join(f'{c:02X}' for c in F['glass']['shadow_rgb'])
RECV = T['charts']['categorical'][0]   # the received series: first categorical hue (05)

def defs():
    stops = lambda face: ''.join(f'<stop offset="{s["offset"]}" stop-color="{s["color"]}" stop-opacity="{s["alpha"]}"/>' for s in F['glass'][face])
    sh = F['paper']['shadow']
    return ('<defs>'
            f'<linearGradient id="kzf-face" x1="0" y1="0" x2="1" y2="1">{stops("face")}</linearGradient>'
            f'<linearGradient id="kzf-face-clear" x1="0" y1="0" x2="1" y2="1">{stops("face_clear")}</linearGradient>'
            # one native outer shadow per object (ppt-master: one effect per object)
            f'<filter id="kzf-shadow"><feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="{SR}" flood-opacity="0.22"/></filter>'
            f'<filter id="kzf-paper-shadow"><feDropShadow dx="{sh[0]}" dy="{sh[1]}" stdDeviation="{sh[2] / 2:g}" flood-color="{SR}" flood-opacity="{sh[4]}"/></filter>'
            '</defs>')

def page(role, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" font-family="{FONT}" data-pptx-page-role="{role}">'
            + defs() + inner + '</svg>\n')

def bg(name):
    return f'<image id="bg" data-pptx-role="background" href="../images/{name}" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>'

LENSES = []   # (plate, picture file, box, radius, lens role), baked in build() once the plates exist
def lens_picture(id_, plate, x, y, w, h, r, role):
    """What PowerPoint cannot filter live: the plate under the glass, frosted and refracted ahead of time (14 FLAG-10)."""
    name = f'{plate[:4]}{id_}.png'
    LENSES.append((plate, name, (x, y, w, h), r, role))
    return f'<image id="{id_}" data-pptx-role="decoration" href="../images/{name}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" preserveAspectRatio="none"/>'

def glass(id_, x, y, w, h, r, plate, role):
    """Baked lens picture under a native shell: face gradient, white rim, one soft shadow."""
    return (lens_picture(id_.replace('shell', 'lens'), plate, x, y, w, h, r, role)
            + f'<rect id="{id_}" data-pptx-role="decoration" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#kzf-face)" '
            f'stroke="#FFFFFF" stroke-opacity="0.95" stroke-width="{F["glass"]["rim_width"]}" filter="url(#kzf-shadow)"/>')

PT, PR, PB, PL = F['identity']['pad']; GAP = F['identity']['gap']
LOGO_W = F['identity']['logo_height'] * 1210 / 250            # logo.png is 1210×250
NAME_W = len(F['identity']['name']) * TY['identity_name'] * 1.06  # bold CJK advance
IDW, IDH = PL + LOGO_W + GAP + NAME_W + PR, PT + F['identity']['logo_height'] + PB
def identity(kind, plate):
    corner, scale = F['identity']['anchors'][kind]; mx, my = F['identity']['margin']
    w, h = IDW * scale, IDH * scale
    x = mx if corner[1] == 'l' else 1280 - mx - w
    y = my if corner[0] == 't' else 720 - my - h
    lh = F['identity']['logo_height'] * scale; lw = LOGO_W * scale; pad = PL * scale; gap = GAP * scale
    return (lens_picture('identity-lens', plate, x, y, w, h, h / 2, 'identity')
            + f'<rect id="identity-shell" data-pptx-role="decoration" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{h / 2:g}" fill="url(#kzf-face)" stroke="#FFFFFF" stroke-opacity="0.95" stroke-width="1.3" filter="url(#kzf-shadow)"/>'
            f'<image id="logo" data-pptx-role="logo" href="../images/logo.png" x="{x + pad:g}" y="{y + (h - lh) / 2:g}" width="{lw:g}" height="{lh:g}" preserveAspectRatio="xMidYMid meet"/>'
            f'<g id="identity-name" data-pptx-bounds="{x + pad + lw + gap - 2:g} {y:g} {w - pad - lw - gap + 2:g} {h:g}"><text x="{x + pad + lw + gap:g}" y="{y + h / 2 + 5.5 * scale:g}" font-size="{TY["identity_name"]}" font-weight="bold" fill="{C["ink"]}">{escape(F["identity"]["name"])}</text></g>')

def kicker(id_, x, y, text, anchor='start'):
    tx = x + (48 if anchor == 'start' else 0)
    line = f'<rect x="{x}" y="{y - 6}" width="37" height="1" fill="{F["accent_ink"]}"/>' if anchor == 'start' else ''
    bx = x if anchor == 'start' else x - 260
    return f'<g id="{id_}" data-pptx-bounds="{bx} {y - 18} 520 24">{line}<text x="{tx}" y="{y}" font-size="{TY["kicker"]}" font-weight="bold" fill="{F["accent_ink"]}" letter-spacing="4.8" text-anchor="{anchor}">{escape(text)}</text></g>'

def frac(x, y, w, h):
    return [round(x / 1280, 4), round(y / 720, 4), round((x + w) / 1280, 4), round((y + h) / 720, 4)]

# ---------- pages (1280×720 logical, same geometry as the HTML flagship reference) ----------
def cover():
    bar = ''.join(f'<g id="bar-{i}" data-pptx-bounds="{100 + i * 360} 467 360 147">'
                  f'<text x="{100 + i * 360 + 150}" y="567" font-family="{NUM}" font-size="{TY["bar_numeral"]}" fill="{C["risk"] if i == 2 else C["ink"]}" text-anchor="end">{v}</text>'
                  f'<text x="{100 + i * 360 + 166}" y="566" font-size="{TY["bar_label"]}" fill="{C["body"]}">{l}</text></g>'
                  for i, (v, l) in enumerate([('24', '应收（份）'), ('20', '已收（份）'), ('4', '缺口（份）')]))
    seps = ''.join(f'<rect id="bar-sep-{i}" data-pptx-role="decoration" x="{100 + i * 360}" y="500" width="1" height="81" fill="#A0783C" fill-opacity="0.3"/>' for i in (1, 2))
    return page('cover', bg('p01-plate.png') + identity('cover', 'p01-plate.png')
                + kicker('kicker', 100, 166, '管理层季度汇报 · 合成示例')
                + f'<g id="title" data-pptx-bounds="100 180 900 205"><text font-size="{TY["cover_title"]}" font-weight="bold" fill="{C["ink"]}"><tspan x="100" y="262">研究资料</tspan><tspan x="100" y="350">完整性核对</tspan></text></g>'
                + f'<g id="lede" data-pptx-bounds="100 386 900 36"><text x="100" y="412" font-size="{TY["lede"]}" fill="{C["body"]}">应收 24 份，已收 20 份；<tspan font-weight="bold" fill="{C["ink"]}">缺口集中在两组资料</tspan></text></g>'
                + glass('bar-shell', 100, 467, 1080, 147, 73.5, 'p01-plate.png', 'bar') + seps + bar
                + f'<g id="meta" data-pptx-bounds="100 650 600 24"><text x="100" y="668" font-size="{TY["meta"]}" fill="{C["body"]}" letter-spacing="2">{DATE}　管理层季度汇报</text></g>')

def toc():
    cards = ''
    for i, (n, t, d) in enumerate([('01', '研究范围', '对象、时间窗与资料组'), ('02', '资料完整性', '应收与已收、缺口所在'), ('03', '核对计划', '补收、确认与复核')]):
        x = 100 + i * (344 + 24)
        cards += (glass(f'toc-shell-{i + 1}', x, 330, 344, 250, F['glass']['radius'], 'p02-plate.png', 'ask')
                  + f'<g id="toc-{i + 1}" data-pptx-bounds="{x} 330 344 250"><text x="{x + 30}" y="408" font-family="{NUM}" font-size="{TY["toc_numeral"]}" fill="{F["accent_ink"]}">{n}</text>'
                  f'<text x="{x + 30}" y="512" font-size="{TY["toc_label"]}" font-weight="bold" fill="{C["ink"]}">{t}</text>'
                  f'<text x="{x + 30}" y="548" font-size="{TY["toc_description"]}" fill="{C["body"]}">{d}</text></g>')
    return page('toc', bg('p02-plate.png') + identity('toc', 'p02-plate.png') + kicker('kicker', 100, 166, '目录')
                + f'<g id="title" data-pptx-bounds="100 180 900 80"><text x="100" y="240" font-size="{TY["toc_title"]}" font-weight="bold" fill="{C["ink"]}">汇报章节</text></g>' + cards)

def section():
    # the lens sits behind the numeral here: native text cannot be refracted, so the number shows through the clear face
    return page('section', bg('p03-plate.png') + identity('section', 'p03-plate.png')
                + lens_picture('section-lens-picture', 'p03-plate.png', 220, 220, 267, 267, 133.5, 'section')
                + f'<g id="section-number" data-pptx-bounds="70 100 480 490"><text x="80" y="440" font-family="{NUM}" font-size="{TY["section_numeral"]}" fill="{C["ink"]}">02</text></g>'
                + f'<circle id="section-lens" data-pptx-role="decoration" cx="353.5" cy="353.5" r="133.5" fill="url(#kzf-face-clear)" stroke="#FFFFFF" stroke-opacity="0.95" stroke-width="1.3" filter="url(#kzf-shadow)"/>'
                + kicker('kicker', 693, 300, '第二部分')
                + f'<g id="section-title" data-pptx-bounds="693 314 540 104"><text x="693" y="388" font-size="{TY["section_title"]}" font-weight="bold" fill="{C["ink"]}">资料完整性</text></g>'
                + f'<g id="section-lede" data-pptx-bounds="693 418 520 36"><text x="693" y="444" font-size="{TY["lede"]}" fill="{C["body"]}">缺口在哪里，会不会影响组间比较</text></g>')

CHART = {"name": "completeness-bars", "type": "column", "grouping": "clustered",
         "categories": ["方案与修订", "中心记录", "实验室数据", "安全性报告"],
         "series": [{"name": "应收", "values": [2, 12, 6, 4]}, {"name": "已收", "values": [2, 9, 6, 3]}],
         "axes": {"value": {"minimum": 0, "maximum": 15, "major_unit": 5}}, "data_labels": {"show_value": True}}

def chart(x, y, w, h):
    """Native column chart (ppt-master --native-charts-and-tables) with a drawn fallback the checker can read."""
    px, py, pw, ph = x + 36, y + 14, w - 36, h - 62
    meta = dict(CHART, x=x, y=y, width=w, height=h, plot_area={"x": px, "y": py, "width": pw, "height": ph},
                style={"colors": [T['charts']['comparator'], RECV], "axis_color": T['charts']['axis'], "grid_color": T['charts']['grid'], "text_color": C['body'], "font_family": "Microsoft YaHei"})
    base = py + ph; scale = ph / 15; slot = pw / 4; bw = slot * 0.29
    grid = ''.join(f'<line x1="{px}" y1="{base - v * scale:.2f}" x2="{px + pw}" y2="{base - v * scale:.2f}"/>' for v in (5, 10, 15))
    ticks = ''.join(f'<text x="{px - 8}" y="{base - v * scale + 5:.2f}">{v}</text>' for v in (0, 5, 10, 15))
    bars, labels = ['', ''], ''
    for i in range(4):
        for j, s in enumerate(CHART['series']):
            val = s['values'][i]; bx = px + slot * i + slot * 0.21 + j * bw; bh = val * scale
            bars[j] += f'<rect x="{bx:.2f}" y="{base - bh:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="4"/>'
            labels += f'<text x="{bx + bw / 2:.2f}" y="{base - bh - 8:.2f}">{val}</text>'
        labels += f'<text x="{px + slot * i + slot / 2:.2f}" y="{base + 26:.2f}">{CHART["categories"][i]}</text>'
    return (f'<g id="completeness-bars" data-pptx-bounds="{x} {y} {w} {h}" data-pptx-replace-with="chart">'
            f'<metadata type="application/json">{json.dumps(meta, ensure_ascii=False)}</metadata>'
            f'<g id="completeness-bars-chartArea"><g id="completeness-grid" stroke="{T["charts"]["grid"]}" stroke-width="1">{grid}</g>'
            f'<g font-size="16" fill="{C["body"]}" text-anchor="end">{ticks}</g>'
            f'<line id="completeness-axis" x1="{px}" y1="{base}" x2="{px + pw}" y2="{base}" stroke="{T["charts"]["axis"]}" stroke-width="2"/>'
            f'<!-- chart-plot-area: object=completeness-bars | {px},{py},{px + pw},{base} -->'
            f'<g fill="{T["charts"]["comparator"]}">{bars[0]}</g><g fill="{RECV}">{bars[1]}</g>'
            f'<g font-size="16" fill="{C["body"]}" text-anchor="middle">{labels}</g></g></g>')

def content():
    paper = (f'<rect id="paper-shell" data-pptx-role="decoration" x="100" y="196" width="733" height="460" rx="{F["paper"]["radius"]}" fill="{F["paper"]["face"]}" '
             f'stroke="{F["paper"]["hairline"]}" stroke-width="1" filter="url(#kzf-paper-shadow)"/>')
    return page('content', bg('p04-plate.png') + identity('content', 'p04-plate.png')
                + f'<g id="title" data-pptx-bounds="100 100 900 60"><text x="100" y="142" font-size="{TY["page_title"]}" font-weight="bold" fill="{C["ink"]}">资料缺口分布</text></g>'
                + f'<rect id="title-rule" data-pptx-role="decoration" x="100" y="168" width="1080" height="1" fill="{F["rule"]}"/>'
                + paper
                + f'<g id="paper-head" data-pptx-bounds="126 214 680 34"><text x="130" y="240" font-size="{TY["card_title"]}" font-weight="bold" fill="{C["ink"]}">各资料组应收与已收</text>'
                f'<text x="803" y="240" font-size="{TY["kpi_label"]}" fill="{C["muted"]}" text-anchor="end">合成示例数据｜单位：份</text></g>'
                + f'<g id="legend" data-pptx-bounds="130 254 300 24"><rect x="130" y="262" width="12" height="12" rx="3" fill="{T["charts"]["comparator"]}"/><text x="150" y="273" font-size="16" fill="{C["body"]}">应收</text>'
                f'<rect x="206" y="262" width="12" height="12" rx="3" fill="{RECV}"/><text x="226" y="273" font-size="16" fill="{C["body"]}">已收</text></g>'
                + chart(130, 290, 670, 346)
                + lens_picture('kpi-lens-picture', 'p04-plate.png', 873, 196, 307, 307, 153.5, 'kpi')
                + f'<circle id="kpi-lens" data-pptx-role="decoration" cx="1026.5" cy="349.5" r="153.5" fill="url(#kzf-face)" stroke="#FFFFFF" stroke-opacity="0.95" stroke-width="1.3" filter="url(#kzf-shadow)"/>'
                + f'<g id="kpi" data-pptx-bounds="900 250 253 200"><text x="1026.5" y="380" font-family="{NUM}" font-size="{TY["kpi_numeral"]}" fill="{C["risk"]}" text-anchor="middle">4<tspan font-size="31" fill="{C["body"]}"> 份</tspan></text>'
                f'<text x="1026.5" y="425" font-size="{TY["kpi_label"]}" fill="{C["body"]}" text-anchor="middle">资料缺口 · 应收 24 / 已收 20</text></g>'
                + f'<rect id="note-rule" data-pptx-role="decoration" x="873" y="527" width="307" height="2" fill="{C["ink"]}"/>'
                + f'<g id="note" data-pptx-bounds="873 535 307 110"><text font-size="{TY["note"]}" fill="{C["body"]}"><tspan x="873" y="562" font-weight="bold" fill="{C["ink"]}">缺失处理</tspan>'
                f'<tspan x="873" y="594">缺失记录保留为空值</tspan><tspan x="873" y="624" font-weight="bold" fill="{C["ink"]}">不按零处理，也不插补</tspan></text></g>')

def ending():
    asks = ''
    for i, (n, a, b) in enumerate([('01', '4 份资料由医学部牵头', '2027Q1 内补收'), ('02', '版本差异确认之后', '再做组间比较')]):
        x = 140 + i * (485 + 30)
        asks += (glass(f'ask-shell-{i + 1}', x, 373, 485, 118, 32, 'p05-plate.png', 'ask')
                 + f'<g id="ask-{i + 1}" data-pptx-bounds="{x} 373 485 118"><text x="{x + 32}" y="453" font-family="{NUM}" font-size="{TY["ask_numeral"]}" fill="{F["accent_ink"]}">{n}</text>'
                 f'<text font-size="{TY["ask"]}" fill="{C["ink"]}"><tspan x="{x + 128}" y="424">{a}</tspan><tspan x="{x + 128}" y="458" font-weight="bold">{b}</tspan></text></g>')
    return page('ending', bg('p05-plate.png') + identity('ending', 'p05-plate.png')
                + kicker('kicker', 640, 186, '会议决定事项', anchor='middle')
                + f'<g id="title" data-pptx-bounds="300 196 680 120"><text x="640" y="280" font-size="{TY["ending_title"]}" font-weight="bold" fill="{C["ink"]}" text-anchor="middle">请确认两件事</text></g>'
                + asks
                + f'<g id="meta" data-pptx-bounds="440 650 400 24"><text x="640" y="668" font-size="{TY["meta"]}" fill="{C["body"]}" text-anchor="middle" letter-spacing="2">{DATE}　管理层季度汇报</text></g>')

# Plates: kind, focus and (content page) the reading areas and focal pool, in page fractions from the geometry above.
PLATES = {
    'p01-plate.png': dict(kind='cover', focus=[0.72, 0.74]),
    'p02-plate.png': dict(kind='toc', focus=[0.62, 0.70]),
    'p03-plate.png': dict(kind='section', focus=[0.25, 0.48]),
    'p04-plate.png': dict(kind='content', focus=[0.80, 0.42], calm=[frac(100, 104, 1080, 66), frac(100, 196, 733, 460), frac(873, 527, 307, 120)],
                          pool=[1026.5 / 1280, 349.5 / 720, 307 / 720 * F['levels']['pool_radius_factor']]),
    'p05-plate.png': dict(kind='ending', focus=[0.50, 0.66]),
}

def page_plan(receipts):
    """The page-plan for qc_plan (route flagship): roles and sizes as authored above, plates bound by SHA-256."""
    def el(pid, i, role, size, text, lh=1.25):
        return {'id': f'{pid}-{role}-{i}', 'role': role, 'font_px': size, 'line_height': lh, 'text': text}
    ident = lambda pid, kind: {'id': f'{pid}-identity', 'rect': [0, 0, 1, 1], 'role': 'logo', 'zone': 'clear'}
    pages = [
        ('p01', 'cover', '研究资料完整性核对', [el('p01', 0, 'cover_title', TY['cover_title'], '研究资料完整性核对'), el('p01', 1, 'hero_subtitle', TY['lede'], '应收 24 份，已收 20 份；缺口集中在两组资料'), el('p01', 2, 'hero_meta', TY['meta'], DATE + '　管理层季度汇报')]),
        ('p02', 'toc', '汇报章节', [el('p02', 0, 'toc_title', TY['toc_title'], '汇报章节')] + [el('p02', i + 1, r, TY[k], t) for i, (r, k, t) in enumerate([('toc_number', 'toc_numeral', '01'), ('toc_label', 'toc_label', '研究范围'), ('toc_description', 'toc_description', '对象、时间窗与资料组'), ('toc_number', 'toc_numeral', '02'), ('toc_label', 'toc_label', '资料完整性'), ('toc_description', 'toc_description', '应收与已收、缺口所在'), ('toc_number', 'toc_numeral', '03'), ('toc_label', 'toc_label', '核对计划'), ('toc_description', 'toc_description', '补收、确认与复核')])]),
        ('p03', 'section', '资料完整性', [el('p03', 0, 'section_number', TY['section_numeral'], '02'), el('p03', 1, 'section_title', TY['section_title'], '资料完整性'), el('p03', 2, 'body', T['type_px']['body'], '缺口在哪里，会不会影响组间比较', 1.4)]),
        ('p04', 'body', '资料缺口分布', [el('p04', 0, 'page_title', TY['page_title'], '资料缺口分布'), el('p04', 1, 'card_title', TY['card_title'], '各资料组应收与已收'), el('p04', 2, 'chart_label', T['type_px']['chart_label'], '份', 1.4), el('p04', 3, 'body', T['type_px']['body'], '缺失记录保留为空值；不按零处理，也不插补', 1.4)]),
        ('p05', 'ending', '请确认两件事', [el('p05', 0, 'ending_title', TY['ending_title'], '请确认两件事'), el('p05', 1, 'body', T['type_px']['body'], '4 份资料由医学部牵头，2027Q1 内补收', 1.4), el('p05', 2, 'body', T['type_px']['body'], '版本差异确认之后，再做组间比较', 1.4)]),
    ]
    by_file = {r['file']: r for r in receipts}
    out = []
    for i, (pid, kind, title, els) in enumerate(pages):
        r = by_file[f'p0{i + 1}-plate.png']
        hero = {'hero_layout_id': 'flagship-' + kind} if kind in ('cover', 'toc', 'section', 'ending') else {}
        out.append({'id': pid, 'kind': kind, 'title': title, **hero, 'body_profile': 'standard', 'elements': els,
                    'protected_regions': [ident(pid, kind)], 'cards': [],
                    'image': {'mode': 'flagship_light_field', 'plate': {k: r[k] for k in ('file', 'sha256', 'kind', 'focus', 'calm', 'pool', 'size_px') if k in r}},
                    'sources': [{'id': 'brief', 'kind': 'internal', 'visible': False, 'locator': 'sources/资料完整性核对_brief.md'}]})
    return {'schema_version': '6.1', 'contract_revision': '7.0', 'track': 'pptx', 'route': 'flagship', 'canvas': [1280, 720], 'target_viewports': [[1280, 720]], 'pages': out}

def build(project):
    svg_dir, img_dir = project / 'svg_output', project / 'images'
    svg_dir.mkdir(exist_ok=True); img_dir.mkdir(exist_ok=True)
    shutil.copy2(ROOT / T['logo']['png_path'], img_dir / 'logo.png')
    receipts, plates = [], {}
    for name, args in PLATES.items():
        plates[name] = img = render(args['kind'], args['focus'], args.get('calm', ()), args.get('pool'), size=(2560, 1440))
        save(img, img_dir / name)
        receipts.append({'file': name, 'sha256': hashlib.sha256((img_dir / name).read_bytes()).hexdigest(), 'size_px': list(img.size), **args})
    LENSES.clear()
    pages = {'01_cover.svg': cover(), '02_toc.svg': toc(), '03_section.svg': section(), '04_data.svg': content(), '05_ending.svg': ending()}
    for name, svg in pages.items():
        (svg_dir / name).write_text(svg, encoding='utf-8')
    for plate, name, box, r, role in LENSES:
        save(lens(plates[plate], box, r, role), img_dir / name)
    enter = T['motion']['duration_ms']['card'] / 1000; step = T['motion']['stagger_ms']['pptx_card'] / 1000
    fade = lambda i: {'effect': 'entrance_fade', 'duration': enter, 'delay': round(i * step, 3), 'decelerate': 0.7, 'order': i + 1}
    anim = {'defaults': {'transition': {'effect': 'fade', 'duration': 0.4}, 'animation': {'effect': 'none'}},
            'slides': {
                '01_cover': {'animation': {'trigger': 'with-previous'}, 'groups': {g: fade(i) for i, g in enumerate(['kicker', 'title', 'lede', 'bar-0', 'bar-1', 'bar-2'])}},
                '02_toc': {'animation': {'trigger': 'with-previous'}, 'groups': {g: fade(i) for i, g in enumerate(['title', 'toc-1', 'toc-2', 'toc-3'])}},
                '03_section': {'animation': {'trigger': 'with-previous'}, 'groups': {g: fade(i) for i, g in enumerate(['section-number', 'section-title', 'section-lede'])}},
                '04_data': {'animation': {'trigger': 'with-previous'}, 'groups': {
                    'title': fade(0), 'paper-head': fade(1),
                    'completeness-bars': {'effect': 'entrance_wipe', 'effect_options': {'direction': 'down'}, 'duration': T['motion']['duration_ms']['data'] / 1000, 'delay': round(2 * step, 3), 'decelerate': 0.7, 'order': 3},
                    'kpi': fade(3), 'note': fade(4)}},
                '05_ending': {'animation': {'trigger': 'with-previous'}, 'groups': {g: fade(i) for i, g in enumerate(['title', 'ask-1', 'ask-2'])}},
            }}
    (project / 'animations.json').write_text(json.dumps(anim, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (project / 'page-plan.json').write_text(json.dumps(page_plan(receipts), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return sorted(pages), receipts

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', type=Path); a = ap.parse_args()
    pages, receipts = build(a.project.resolve())
    print(json.dumps({'pages': pages, 'plates': receipts}, ensure_ascii=False))
