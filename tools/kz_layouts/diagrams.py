"""Drawn diagrams for template pages: one drawing function per kind, used by both tracks.

mode='pptx' writes ppt-master shapes (icons as <use data-icon="kangzhe/…">); mode='html' writes the same geometry as
inline SVG (icons as paths). Text inside a diagram is native text in PPTX and SVG text in HTML; sizes follow 03.
"""
from html import escape
import math
from . import text as T
from .tree import TOK, C, L, INK, BODY, MUTED, RISK, BRAND, ICONS

DRAW, MEASURE = {}, {}

def kind(name, measure=None):
    """Register a diagram; `measure(spec, w)` gives its natural height when the drawing should not stretch."""
    def deco(fn):
        DRAW[name] = fn
        if measure: MEASURE[name] = measure
        return fn
    return deco

def draw(name, spec, box, gid, mode='pptx'):
    return DRAW[name](spec, box, gid, mode)

def f(n):
    return f'{n:.1f}'.rstrip('0').rstrip('.')

def icon(name, x, y, size, color, mode, disc=False):
    if name not in ICONS: raise KeyError(f'未知图标：{name}（见 assets/icons/icons.json）')
    out = ''
    if disc:
        out += f'<circle cx="{f(x + size / 2)}" cy="{f(y + size / 2)}" r="{f(size / 2)}" fill="{L["icon_tint"]}"/>'
        inner = size * 0.6; x, y, size = x + (size - inner) / 2, y + (size - inner) / 2, inner
    if mode == 'pptx':
        return out + f'<use data-icon="kangzhe/{name}" x="{f(x)}" y="{f(y)}" width="{f(size)}" height="{f(size)}" fill="{color}"/>'
    k = size / 24
    return out + (f'<g transform="translate({f(x)} {f(y)}) scale({k:.4f})" fill="none" stroke="{color}" stroke-width="1.8" '
                  f'stroke-linecap="round" stroke-linejoin="round"><path d="{ICONS[name]["d"]}"/></g>')

def text(x, y_top, markup, size, color=INK, bold=False, anchor='start', width=None, lead=1.35):
    """Native paragraph: wrapped to `width` when given. Returns (svg, height)."""
    from .svg import baseline, run_svg
    lines = T.wrap(markup, width or 1e9, size, bold)
    a = f' text-anchor="{anchor}"' if anchor != 'start' else ''
    b = ' font-weight="bold"' if bold else ''
    y0 = baseline(y_top, size, lead)
    out = f'<text x="{f(x)}" y="{f(y0)}" font-size="{f(size)}" fill="{color}"{b}{a}>' + ''.join(run_svg(t, st, color, bold) for t, st in lines[0])
    for ln in lines[1:]:
        out += f'<tspan x="{f(x)}" dy="{f(size * lead)}">' + ''.join(run_svg(t, st, color, bold) for t, st in ln) + '</tspan>'
    return out + '</text>', len(lines) * size * lead

from . import diagram_kinds, diagram_more  # noqa: E402,F401  (registers the kinds)
