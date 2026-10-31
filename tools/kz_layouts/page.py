"""Whole pages for previews and the template decks:康哲 chrome (01) around a template body.

PPTX: an SVG page in the ppt-master contract, same chrome as examples/reference/pptx-default (header mark, title,
rule, logo, footer, quiet background). HTML-PPT pages come from examples/reference/htmlppt/build.py body() with
data-preset="kzl".
"""
from html import escape
import sys
from .tree import TOK, R
from . import svg as S
sys.path.insert(0, str(R / 'tools'))
from brand_fragments import facets  # noqa: E402

def svg_page(title, body_svg, n, total, background='../images/body_quiet.png', logo='../images/logo.png', footer=None):
    ch = TOK['chrome']; tx, ty, tw, th = ch['title']; lx, ly, lw, lh = ch['logo']; x1, y1, x2, y2, sw = ch['rule']
    foot = footer or (ch['footer']['text_prefix'] + '2026年10月')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" font-family="Microsoft YaHei, Arial" data-pptx-page-role="content">'
            f'<defs>{S.defs()}</defs>'
            f'<image id="bg" data-pptx-role="background" href="{escape(background, quote=True)}" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>'
            f'<g id="header-mark" data-pptx-role="decoration" data-pptx-bounds="0 0 100 90">{facets(native=True)}</g>'
            f'<g id="title" data-pptx-bounds="{tx} {ty} {tw} {th}"><text x="{tx}" y="{ty + 32}" font-size="{TOK["type_px"]["page_title"]}" font-weight="bold" fill="{TOK["colors"]["ink"]}">{escape(title)}</text></g>'
            f'<line id="rule" data-pptx-role="decoration" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{TOK["colors"]["brand"]}" stroke-width="{sw}"/>'
            f'<image id="logo" data-pptx-role="logo" href="{escape(logo, quote=True)}" x="{lx}" y="{ly}" width="{lw}" height="{lh}" preserveAspectRatio="xMidYMid meet"/>'
            + body_svg
            + _footer(foot, n, total) + '</svg>')

def _footer(text, n, total):
    """Same geometry as examples/reference/pptx/build_svg.py footer()."""
    f = TOK['chrome']['footer']; y = 720 - f['bottom'] - 4; c = TOK['colors']['footer']; s = TOK['type_px']['footer']
    return (f'<g id="footer" data-pptx-role="footer" data-pptx-bounds="{f["left"]} {y - 20} {1280 - f["left"] - f["right"]} 26" font-size="{s}" fill="{c}">'
            f'<text x="{f["left"]}" y="{y}">{escape(text)}</text>'
            f'<text x="{1280 - f["right"]}" y="{y}" text-anchor="end">{n} / {total}</text></g>')

def inline_icons(svg_text):
    """Browser preview only: replace <use data-icon="kangzhe/…"> with the icon path (ppt-master's finalize step does
    the same for the export)."""
    import re
    from .tree import ICONS
    def sub(m):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(0)))
        name = a['data-icon'].split('/', 1)[1]; k = float(a['width']) / 24
        return (f'<g transform="translate({a["x"]} {a["y"]}) scale({k:.4f})" fill="none" stroke="{a.get("fill", "#000")}" stroke-width="1.8" '
                f'stroke-linecap="round" stroke-linejoin="round"><path d="{ICONS[name]["d"]}"/></g>')
    return re.sub(r'<use data-icon="kangzhe/[^"]+"[^>]*/>', sub, svg_text)
