#!/usr/bin/env python3
"""Author Kangzhe pages into an existing ppt-master project (svg_output/ + animations.json) for native export.

This is the Executor-side authoring a ppt-master run performs; it is not an exporter. Export, checking and
packaging stay with ppt-master (svg_quality_checker.py, svg_to_pptx.py). Usage:
  python examples/reference/pptx/build_svg.py <ppt-master project dir> --images <dir with cover.png body-quiet.png logo.png>
"""
from pathlib import Path
from html import escape
import argparse, json, shutil, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from hero_layout import svg_fragment  # noqa: E402
from brand_fragments import facets  # noqa: E402
T = json.loads((ROOT / 'tokens/tokens.json').read_text())
G, C, E = T['glass'], T['colors'], T['elevation']['pptx']
FONT = 'Microsoft YaHei, Arial'
FOOT = '产品中心-医学部｜2026年10月'

def defs():
    stops = ''.join(f'<stop offset="{s["offset"]}" stop-color="{s["color"]}" stop-opacity="{s["alpha"]}"/>' for s in G['face_gradient'])
    sh = E['rest']
    return ('<defs>'
            f'<linearGradient id="kz-face" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient>'
            '<linearGradient id="kz-glint" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".95"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
            # One native outer shadow per card (ppt-master: one effect per object; exported alpha ≈ author × 0.75).
            f'<filter id="kz-shadow"><feDropShadow dx="{sh["dx"]}" dy="{sh["dy"]}" stdDeviation="{sh["std_deviation"]}" flood-color="{E["color"]}" flood-opacity="{sh["alpha"]}"/></filter>'
            '</defs>')

def chrome(title):
    t = T['chrome']
    x1, y1, x2, _, sw = t['rule']; lx, ly, lw, lh = t['logo']; tx, ty, tw, th = t['title']
    mark = facets(prefix='kz', native=True)
    return (f'<image id="bg" data-pptx-role="background" href="../images/body-quiet.png" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>'
            f'<g id="header-mark" data-pptx-role="decoration" data-pptx-bounds="0 0 100 90">{mark}</g>'
            f'<g id="title" data-pptx-bounds="{tx} {ty} {tw} {th}"><text x="{tx}" y="{ty + 32}" font-size="{T["type_px"]["page_title"]}" font-weight="bold" fill="{C["ink"]}">{escape(title)}</text></g>'
            f'<line id="rule" data-pptx-role="decoration" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y1}" stroke="{C["brand"]}" stroke-width="{sw}"/>'
            f'<image id="logo" data-pptx-role="logo" href="../images/logo.png" x="{lx}" y="{ly}" width="{lw}" height="{lh}" preserveAspectRatio="xMidYMid meet"/>')

def footer(n, total):
    f = T['chrome']['footer']; y = 720 - f['bottom'] - 4
    return (f'<g id="footer" data-pptx-role="footer" data-pptx-bounds="{f["left"]} {y - 20} {1280 - f["left"] - f["right"]} 26">'
            f'<text x="{f["left"]}" y="{y}" font-size="{T["type_px"]["footer"]}" fill="{C["footer"]}">{escape(FOOT)}</text>'
            f'<text x="{1280 - f["right"]}" y="{y}" font-size="{T["type_px"]["footer"]}" fill="{C["footer"]}" text-anchor="end">{n} / {total}</text></g>')

def runs(item):
    """A bullet as text or [(text, style)] runs; style 'b' = bold, 'r' = bold deep red (03 COPY-04)."""
    if isinstance(item, str):
        return escape(item)
    style = {None: '', 'b': ' font-weight="bold" fill="' + C['ink'] + '"', 'r': ' font-weight="bold" fill="' + C['risk'] + '"'}
    return ''.join(f'<tspan{style[k]}>{escape(t)}</tspan>' if k else escape(t) for t, k in item)

def card(id_, x, y, w, h, title, items, figures=(), cols=1):
    r, pad = G['radius'], T['rhythm']['card_padding']; body = T['type_px']['body']; lh = body * T['rhythm']['line_height_body']
    out = [f'<g id="{id_}" data-pptx-bounds="{x} {y} {w} {h}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>',
           f'<rect x="{x + pad}" y="{y + 1}" width="{w * G["highlight_extent_max"]:.1f}" height="1.5" fill="url(#kz-glint)"/>']
    cy = y + pad
    out.append(f'<text x="{x + pad}" y="{cy + 24}" font-size="{T["type_px"]["card_title"]}" font-weight="bold" fill="{C["ink"]}">{escape(title)}</text>')
    cy += 24 * 1.25 + 16
    # Lead figures: (value, label[, 'risk']) — the number the card is about, label in muted body-floor beside it.
    kv = T['type_px']['kpi_value']
    for f in figures:
        out.append(f'<text x="{x + pad}" y="{cy + kv * 0.9:g}" font-size="{kv}" font-weight="bold" fill="{C["risk"] if len(f) > 2 else C["ink"]}">{escape(f[0])}'
                   f'<tspan font-size="{T["type_px"]["body_floor"]}" font-weight="normal" fill="{C["muted"]}">  {escape(f[1])}</tspan></text>')
        cy += kv * 1.25 + 12
    # One text frame per bullet column: native text with a bullet glyph and hanging indent (03 COPY-06 allows this form).
    colw = (w - 2 * pad) / cols
    for c in range(cols):
        part = items[c::cols]
        if not part:
            continue
        out.append(f'<text x="{x + pad + c * colw:g}" y="{cy + body}" font-size="{body}" fill="{C["body"]}">')
        for i, item in enumerate(part):
            dy = 0 if i == 0 else lh + 10
            out.append(f'<tspan x="{x + pad + c * colw:g}" dy="{dy}">• {runs(item)}</tspan>')
        out.append('</text>')
    out.append('</g>')
    return ''.join(out)

def page(role, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" font-family="{FONT}" data-pptx-page-role="{role}">'
            + defs() + inner + '</svg>\n')

def carrier(x, y, w, h, label, caption, facts):
    out = [f'<g id="carrier" data-pptx-bounds="{x} {y} {w} {h}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>',
           f'<text x="{x + 40}" y="{y + 60}" font-size="{T["type_px"]["card_title"]}" font-weight="bold" fill="{C["ink"]}">{escape(label)}</text>',
           f'<text x="{x + 40}" y="{y + 96}" font-size="{T["type_px"]["body_floor"]}" fill="{C["muted"]}">{escape(caption)}</text>',
           f'<text x="{x + 40}" y="{y + 146}" font-size="{T["type_px"]["body"]}" fill="{C["body"]}">']
    for i, f in enumerate(facts):
        out.append(f'<tspan x="{x + 40}" dy="{0 if i == 0 else 42}">• {runs(f)}</tspan>')
    out.append('</text></g>')
    return ''.join(out)

STEPS = ['界定范围', '清点资料', '比较版本', '排定计划']

def steps(current):
    """Step rail under the stage, as in the HTML-PPT film page; the current step is filled."""
    b = T['chrome']['body']; gap = 16; w = (b[2] - 3 * gap) / 4; y = 588
    out = [f'<g id="steps" data-pptx-bounds="{b[0]} {y} {b[2]} 48">']
    for i, label in enumerate(STEPS):
        x = b[0] + i * (w + gap); on = i == current
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="48" rx="16" fill="{C["brand"] if on else "#FFFFFF"}" fill-opacity="{0.16 if on else 0.6}" stroke="{G["border_color"]}" stroke-opacity="0.3" stroke-width="1"/>'
                   f'<text x="{x + 20:.1f}" y="{y + 31}" font-size="{T["type_px"]["body_floor"]}" font-weight="bold" fill="{C["ink"] if on else C["body"]}">{i + 1}  {label}</text>')
    out.append('</g>')
    return ''.join(out)

def build(project, images):
    svg_dir = project / 'svg_output'; svg_dir.mkdir(exist_ok=True)
    for name in ['cover.png', 'body-quiet.png', 'logo.png']:
        shutil.copy2(images / name, project / 'images' / name)
    total = 4
    (svg_dir / '01_cover.svg').write_text(svg_fragment('cover', {'title': '研究资料完整性核对', 'subtitle': '合成示例｜应收 24 份，已收 20 份', 'meta': FOOT}, '../images/cover.png', '../images/logo.png') + '\n', encoding='utf-8')
    # Scope: cards + takeaway centred in the body region; cards keep content height (03 TYPE-02); span about 0.61, below layout.content_span_target — a converter probe, not padded (10 G5-SPAN).
    b = T['chrome']['body']; gap = 24; w = (b[2] - 2 * gap) / 3; ch, th = 236, 84; top = b[1] + (b[3] - (ch + gap + th)) / 2
    cards = ''.join(card(f'card-{i + 1}', round(b[0] + i * (w + gap), 2), round(top), round(w, 1), ch, t, items, figs, cols) for i, (t, items, figs, cols) in enumerate([
        ('研究对象与时间窗', [], [('成人受试者', '研究对象'), ('第 16 周', '评价时间窗')], 1),
        ('纳入资料', ['方案与修订', '中心记录', '实验室数据', '安全性报告'], [('4 组', '纳入核对')], 2),
        ('方案版本', ['V2.1 与 V2.3 并排比较', '筛选窗口、终点评价时间点'], [('2 项', '待确认差异', 'risk')], 1)]))
    ty = round(top + ch + gap)
    takeaway = (f'<g id="takeaway" data-pptx-bounds="{b[0]} {ty} {b[2]} {th}"><rect x="{b[0]}" y="{ty}" width="{b[2]}" height="{th}" rx="{G["radius"]}" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>'
                f'<text x="640" y="{ty + 54}" font-size="{T["type_px"]["takeaway"]}" font-weight="bold" fill="{C["ink"]}" text-anchor="middle">版本差异<tspan fill="{C["risk"]}">确认之后</tspan>，再做组间比较</text></g>')
    (svg_dir / '02_scope.svg').write_text(page('content', chrome('研究范围') + cards + takeaway + footer(2, total)), encoding='utf-8')
    # Morph pair: the same carrier key on two adjacent slides; geometry and content change, identity stays.
    (svg_dir / '03_flow_a.svg').write_text(page('content', chrome('核对流程') + carrier(360, 212, 560, 260, '界定范围', '先定对象、时间窗和纳入的资料。', ['研究对象：成人受试者', [('评价时间窗：', None), ('第 16 周', 'b')], '纳入资料：4 组']) + steps(0) + footer(3, total)), encoding='utf-8')
    (svg_dir / '04_flow_b.svg').write_text(page('content', chrome('核对流程') + carrier(96, 192, 1088, 300, '清点资料', '逐组登记应收与已收，缺失照原样保留。', [[('应收 24 份，已收 20 份，', None), ('缺 4 份', 'r')], '中心记录缺 3 份，安全性报告缺 1 份', [('缺失记录保留为空值，', None), ('不按零处理', 'b')]]) + steps(1) + footer(4, total)), encoding='utf-8')
    motion = T['motion']
    enter = motion['duration_ms']['card'] / 1000; step = motion['stagger_ms']['card'] / 1000
    anim = {
        'defaults': {'transition': {'effect': 'fade', 'duration': 0.4}, 'animation': {'effect': 'none'}},
        'slides': {
            '01_cover': {'animation': {'trigger': 'with-previous'}, 'groups': {
                g: {'effect': 'entrance_fade', 'duration': enter, 'delay': round(i * step, 3), 'decelerate': 0.7, 'order': i + 1} for i, g in enumerate(['hero-cover-title', 'hero-hero-subtitle', 'hero-hero-meta'])}},
            '03_flow_a': {'animation': {'trigger': 'with-previous'}, 'groups': {
                'carrier': {'effect': 'entrance_fade', 'duration': enter, 'delay': 0, 'decelerate': 0.7, 'order': 1},
                'steps': {'effect': 'entrance_fade', 'duration': enter, 'delay': step, 'decelerate': 0.7, 'order': 2}}},
            '02_scope': {'animation': {'trigger': 'with-previous'}, 'groups': {
                **{f'card-{i + 1}': {'effect': 'entrance_fade', 'duration': enter, 'delay': round(i * step, 3), 'decelerate': 0.7, 'order': i + 1} for i in range(3)},
                'takeaway': {'effect': 'entrance_fade', 'duration': enter, 'delay': round(3 * step + motion['stagger_ms']['takeaway_gap'] / 1000, 3), 'decelerate': 0.7, 'order': 4}}},
            '04_flow_b': {'transition': {'effect': 'morph', 'effect_options': {'morph_by': 'object'}, 'duration': 0.8},
                          'morph': {'from': '03_flow_a', 'pairs': {'kz-carrier': {'from': 'carrier', 'to': 'carrier'}}}}
        }
    }
    (project / 'animations.json').write_text(json.dumps(anim, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return sorted(p.name for p in svg_dir.glob('*.svg'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', type=Path); ap.add_argument('--images', type=Path, required=True); a = ap.parse_args()
    print(build(a.project.resolve(), a.images.resolve()))
