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

def card(id_, x, y, w, h, title, items, marker=None):
    r, pad = G['radius'], T['rhythm']['card_padding']; body = T['type_px']['body']; lh = body * T['rhythm']['line_height_body']
    out = [f'<g id="{id_}" data-pptx-bounds="{x} {y} {w} {h}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>',
           f'<rect x="{x + pad}" y="{y + 1}" width="{w * G["highlight_extent_max"]:.1f}" height="1.5" fill="url(#kz-glint)"/>']
    cy = y + pad
    if marker:
        out.append(f'<rect x="{x + pad}" y="{cy}" width="34" height="34" rx="12" fill="{C["brand"]}" fill-opacity="0.14"/>'
                   f'<text x="{x + pad + 17}" y="{cy + 23}" font-size="16" font-weight="bold" fill="{C["ink"]}" text-anchor="middle">{marker}</text>')
        cy += 48
    out.append(f'<text x="{x + pad}" y="{cy + 24}" font-size="{T["type_px"]["card_title"]}" font-weight="bold" fill="{C["ink"]}">{escape(title)}</text>')
    cy += 24 * 1.25 + 16
    # One text frame per bullet list: native text with a bullet glyph and hanging indent (03 COPY-06 allows this form).
    out.append(f'<text x="{x + pad}" y="{cy + body}" font-size="{body}" fill="{C["body"]}">')
    for i, item in enumerate(items):
        dy = 0 if i == 0 else lh + 10
        out.append(f'<tspan x="{x + pad}" dy="{dy}">• {escape(item)}</tspan>')
    out.append('</text></g>')
    return ''.join(out)

def page(role, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" font-family="{FONT}" data-pptx-page-role="{role}">'
            + defs() + inner + '</svg>\n')

def carrier(x, y, w, h, label, facts):
    out = [f'<g id="carrier" data-pptx-bounds="{x} {y} {w} {h}">',
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>',
           f'<text x="{x + w / 2}" y="{y + 56}" font-size="26" font-weight="bold" fill="{C["ink"]}" text-anchor="middle">{escape(label)}</text>',
           f'<text x="{x + 32}" y="{y + 110}" font-size="20" fill="{C["body"]}">']
    for i, f in enumerate(facts):
        out.append(f'<tspan x="{x + 32}" dy="{0 if i == 0 else 40}">• {escape(f)}</tspan>')
    out.append('</text></g>')
    return ''.join(out)

def build(project, images):
    svg_dir = project / 'svg_output'; svg_dir.mkdir(exist_ok=True)
    for name in ['cover.png', 'body-quiet.png', 'logo.png']:
        shutil.copy2(images / name, project / 'images' / name)
    total = 4
    (svg_dir / '01_cover.svg').write_text(svg_fragment('cover', {'title': '证据组织与资料核对', 'subtitle': '合成示例 · 研究资料审阅流程', 'meta': FOOT}, '../images/cover.png', '../images/logo.png') + '\n', encoding='utf-8')
    b = T['chrome']['body']; gap = 24; w = (b[2] - 2 * gap) / 3
    cards = ''.join(card(f'card-{i + 1}', b[0] + i * (w + gap), 160, round(w, 1), 236, t, items, f'0{i + 1}') for i, (t, items) in enumerate([
        ('研究人群', ['成人受试者，筛选期 4 周', '既往治疗失败或不耐受', '同期参加其他干预研究者排除']),
        ('主要终点', ['第 16 周较基线变化', '缺失值不按零处理', '分析人群与估计量分开说明']),
        ('安全性', ['治疗期间不良事件', '停药原因分开登记', '严重事件单列时间线'])]))
    takeaway = (f'<g id="takeaway" data-pptx-bounds="{b[0]} 420 {b[2]} 84"><rect x="{b[0]}" y="420" width="{b[2]}" height="84" rx="{G["radius"]}" fill="url(#kz-face)" stroke="{G["border_color"]}" stroke-opacity="{G["border_alpha"]}" stroke-width="1" filter="url(#kz-shadow)"/>'
                f'<text x="640" y="470" font-size="{T["type_px"]["takeaway"]}" font-weight="bold" fill="{C["ink"]}" text-anchor="middle">主要终点按第 16 周评价，缺失记录<tspan fill="{C["risk"]}">保留为空值</tspan></text></g>')
    (svg_dir / '02_scope.svg').write_text(page('content', chrome('研究范围') + cards + takeaway + footer(2, total)), encoding='utf-8')
    # Morph pair: the same carrier key on two adjacent slides; geometry and content change, identity stays.
    (svg_dir / '03_flow_a.svg').write_text(page('content', chrome('证据组织过程') + carrier(80, 150, 520, 300, '界定范围', ['研究对象：成人受试者', '评价时间窗：第 16 周', '纳入资料：方案、中心记录']) + footer(3, total)), encoding='utf-8')
    (svg_dir / '04_flow_b.svg').write_text(page('content', chrome('证据组织过程') + carrier(80, 120, 760, 470, '整理证据', ['方案与修订：V2.1 / V2.3', '中心记录：9 份完整，3 份缺失', '实验室数据：按访视窗口归组', '缺失记录保留为空值']) + footer(4, total)), encoding='utf-8')
    motion = T['motion']
    enter = motion['duration_ms']['card'] / 1000; step = motion['stagger_ms']['card'] / 1000
    anim = {
        'defaults': {'transition': {'effect': 'fade', 'duration': 0.4}, 'animation': {'effect': 'none'}},
        'slides': {
            '02_scope': {'animation': {'trigger': 'with-previous'}, 'groups': {
                **{f'card-{i + 1}': {'effect': 'entrance_fade', 'duration': enter, 'delay': round(i * step, 3), 'decelerate': 0.7, 'order': i + 1} for i in range(3)},
                'takeaway': {'effect': 'entrance_fade', 'duration': enter, 'delay': round(3 * step + 0.2, 3), 'decelerate': 0.7, 'order': 4}}},
            '04_flow_b': {'transition': {'effect': 'morph', 'effect_options': {'morph_by': 'object'}, 'duration': 0.8},
                          'morph': {'from': '03_flow_a', 'pairs': {'kz-carrier': {'from': 'carrier', 'to': 'carrier'}}}}
        }
    }
    (project / 'animations.json').write_text(json.dumps(anim, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return sorted(p.name for p in svg_dir.glob('*.svg'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', type=Path); ap.add_argument('--images', type=Path, required=True); a = ap.parse_args()
    print(build(a.project.resolve(), a.images.resolve()))
