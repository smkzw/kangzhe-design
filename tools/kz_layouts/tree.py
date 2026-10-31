"""Layout tree for template pages (13 BODY-02): one description, two renderers.

A template turns page data into a tree of nodes. For PPTX the tree is solved here with measured text (text.py):
every node reports its natural height for a width, a vertical stack hands spare height out evenly between its groups
(capped, the rest split above and below, so text never piles up at the top of a card — 03 TYPE-02), and the result is
a list of primitives that svg.py writes as ppt-master SVG. For HTML-PPT the same tree prints CSS grid/flex markup
(html.py) and the browser does the measuring.
"""
from html import escape
import json
from pathlib import Path
from . import text as T

R = Path(__file__).resolve().parents[2]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
C = TOK['colors']
L = TOK['layout']['templates']
INK, BODY, MUTED, RISK, BRAND = C['ink'], C['body'], C['muted'], C['risk'], C['brand']

# role → (size px on the 1280 canvas, leading, colour, bold); sizes are the 03 TYPE-01 contract
ROLES = {
    'body': (TOK['type_px']['body'], 1.5, BODY, False),
    'secondary': (TOK['type_px']['secondary'], 1.45, BODY, False),
    'label': (TOK['type_px']['secondary'], 1.35, MUTED, False),
    'card_title': (TOK['type_px']['card_title'], 1.3, INK, True),
    'item_title': (TOK['type_px']['body'], 1.35, INK, True),
    'takeaway': (TOK['type_px']['takeaway'], 1.4, INK, True),
    'kpi': (TOK['type_px']['kpi_value'], 1.1, INK, True),
    'kpi_small': (TOK['type_px']['kpi_value_min'], 1.1, INK, True),
}
CSS_ROLE = {'body': 'body', 'secondary': 'secondary', 'label': 'secondary', 'card_title': 'card-title', 'item_title': 'body',
            'takeaway': 'takeaway', 'kpi': 'kpi-value', 'kpi_small': 'kpi-value'}

ICONS = json.loads((R / 'assets/icons/icons.json').read_text(encoding='utf-8'))['icons']

def u(n):
    return f'calc({n:g} * var(--kz-u))'

def icon_svg(name):
    if name not in ICONS: raise KeyError(f'未知图标：{name}')
    return (f'<svg class="kz-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true"><path d="{ICONS[name]["d"]}"/></svg>')

def runs_html(markup):
    out = []
    for t, st in T.parse(markup):
        h = escape(t)
        if 'highlight' in st: h = f'<mark class="kzl-mark">{h}</mark>'
        if 'underline' in st: h = f'<u>{h}</u>'
        if 'risk' in st: h = f'<b class="kz-risk">{h}</b>'
        elif 'bold' in st: h = f'<b>{h}</b>'
        out.append(h)
    return ''.join(out)

class Node:
    flex = 0           # share of spare height inside a Stack (charts and diagrams grow)
    unit = False       # True: becomes one top-level ppt-master group (one editable, animatable unit)
    def measure(self, w): raise NotImplementedError
    def place(self, x, y, w, h, out): raise NotImplementedError
    def html(self): raise NotImplementedError

class Text(Node):
    def __init__(self, markup, role='body', align='start', color=None, bold=None, size=None, nowrap=False):
        self.markup, self.role, self.align, self.nowrap = markup, role, align, nowrap
        s, lead, col, b = ROLES[role]
        self.size, self.lead, self.color, self.bold = size or s, lead, color or col, b if bold is None else bold
    def lines(self, w):
        return T.wrap(self.markup, 1e9 if self.nowrap else w, self.size, self.bold)
    def measure(self, w):
        return len(self.lines(w)) * self.size * self.lead
    def place(self, x, y, w, h, out):
        out.append({'k': 'text', 'x': x, 'y': y, 'w': w, 'lines': self.lines(w), 'size': self.size, 'lead': self.lead,
                    'color': self.color, 'bold': self.bold, 'align': self.align})
    def html(self):
        tag = 'h3' if self.role == 'card_title' else 'p'
        cls = f'kzl-t kzl-{CSS_ROLE[self.role]}' + (f' is-{self.role}' if self.role in ('label', 'item_title') else '')
        css = ([f'text-align:{"center" if self.align == "middle" else "right"}'] if self.align != 'start' else []) + \
              ([f'color:{self.color}'] if self.color != ROLES[self.role][2] else [])
        st = f' style="{";".join(css)}"' if css else ''
        return f'<{tag} class="{cls}"{st}>{runs_html(self.markup)}</{tag}>'

class Spacer(Node):
    def __init__(self, h=0, flex=1): self.h, self.flex = h, flex
    def measure(self, w): return self.h
    def place(self, x, y, w, h, out): pass
    def html(self): return f'<div class="kzl-spacer" style="flex:{self.flex} 1 {u(self.h)}"></div>'

class Stack(Node):
    """Vertical group. justify: 'distribute' (spare height evenly between and around children, gaps capped),
    'center', 'start', 'end', 'fill' (spare height to flex children)."""
    def __init__(self, children, gap=L['gap'], justify='distribute', unit=False, id=None, flex=None):
        self.children, self.gap, self.justify, self.unit, self.id = [c for c in children if c], gap, justify, unit, id
        self.flex = max([c.flex for c in self.children] + [0]) if flex is None else flex
    def measure(self, w):
        return sum(c.measure(w) for c in self.children) + self.gap * max(0, len(self.children) - 1)
    def place(self, x, y, w, h, out):
        hs = [c.measure(w) for c in self.children]
        spare = h - sum(hs) - self.gap * max(0, len(hs) - 1)
        flexes = [c.flex for c in self.children]
        gaps = [self.gap] * max(0, len(hs) - 1)
        top = 0
        if spare > 0 and sum(flexes) and self.justify in ('distribute', 'fill', 'center', 'start', 'end'):
            hs = [hh + spare * f / sum(flexes) for hh, f in zip(hs, flexes)]; spare = 0
        if spare > 0:
            if self.justify == 'distribute' and len(hs) > 1:
                # space-evenly, each gap at most group_gap_max; whatever is left goes half above, half below
                extra = min(spare / (len(hs) + 1), L['group_gap_max'] - self.gap)
                gaps = [g + extra for g in gaps]; top = (spare - extra * (len(hs) - 1)) / 2
            elif self.justify in ('distribute', 'center'): top = spare / 2
            elif self.justify == 'end': top = spare
        cy = y + top
        for i, (c, hh) in enumerate(zip(self.children, hs)):
            c.place(x, cy, w, hh, out); cy += hh + (gaps[i] if i < len(gaps) else 0)
    def html(self, grow=None):
        j = {'distribute': 'space-evenly', 'center': 'center', 'start': 'flex-start', 'end': 'flex-end', 'fill': 'stretch'}[self.justify]
        return f'<div class="kzl-stack" style="justify-content:{j};gap:{u(self.gap)};flex-grow:{self.flex if grow is None else grow:g}">' + ''.join(c.html() for c in self.children) + '</div>'

class Row(Node):
    """Horizontal group; children share the row height (cards in a row are equally tall)."""
    def __init__(self, children, gap=L['gap'], weights=None, align='stretch', flex=None):
        self.children = [c for c in children if c is not None]
        self.weights = weights or [1] * len(self.children)
        self.gap, self.align = gap, align
        self.flex = max([c.flex for c in self.children] + [0]) if flex is None else flex
    def widths(self, w):
        avail = w - self.gap * (len(self.children) - 1)
        return [avail * k / sum(self.weights) for k in self.weights]
    def measure(self, w):
        return max(c.measure(cw) for c, cw in zip(self.children, self.widths(w)))
    def place(self, x, y, w, h, out):
        cx = x
        for c, cw in zip(self.children, self.widths(w)):
            ch = h if self.align == 'stretch' else c.measure(cw)
            cy = y + (h - ch) / 2 if self.align == 'center' else y
            c.place(cx, cy, cw, ch, out); cx += cw + self.gap
    def html(self):
        cols = ' '.join(f'minmax(0,{k:g}fr)' for k in self.weights)
        ai = {'stretch': 'stretch', 'center': 'center', 'start': 'start'}[self.align]
        return f'<div class="kzl-row" style="grid-template-columns:{cols};gap:{u(self.gap)};align-items:{ai};flex-grow:{self.flex:g}">' + ''.join(c.html() for c in self.children) + '</div>'

class Card(Node):
    """Glass card (02 LG-01): one top-level unit. Content is a Stack laid out inside the padding."""
    unit = True
    def __init__(self, children, title=None, icon=None, variant='glass', justify='distribute', pad=None, id=None, gap=None, flex=None):
        head = (IconLead(icon, Text(title, 'card_title')) if icon else Text(title, 'card_title')) if title else None
        self.body = Stack(([head] if head else []) + list(children), gap=L['gap_tight'] if gap is None else gap, justify=justify)
        self.variant, self.pad, self.id = variant, pad or L['card_pad'], id
        self.flex = self.body.flex if flex is None else flex
    def measure(self, w):
        return self.body.measure(w - 2 * self.pad[0]) + 2 * self.pad[1]
    def place(self, x, y, w, h, out):
        out.append({'k': 'card', 'x': x, 'y': y, 'w': w, 'h': h, 'variant': self.variant, 'id': self.id})
        self.body.place(x + self.pad[0], y + self.pad[1], w - 2 * self.pad[0], h - 2 * self.pad[1], out)
        out.append({'k': 'end_unit'})
    def html(self):
        v = '' if self.variant == 'glass' else f' is-{self.variant}'
        return f'<article class="kz-card kzl-card{v}" data-kz-no-tilt style="flex-grow:{self.flex:g}">' + self.body.html(grow=1) + '</article>'

class Icon(Node):
    def __init__(self, name, size=32, tone='focus', disc=False):
        self.name, self.size, self.tone, self.disc = name, size, tone, disc
    def measure(self, w): return self.size
    def place(self, x, y, w, h, out):
        out.append({'k': 'icon', 'name': self.name, 'x': x, 'y': y + (h - self.size) / 2, 'size': self.size, 'tone': self.tone, 'disc': self.disc})
    def html(self):
        return f'<span class="kzl-icon{" is-disc" if self.disc else ""} is-{self.tone}" style="--s:{self.size:g}">{icon_svg(self.name)}</span>'

class IconLead(Node):
    """An icon (or a lettered/numbered badge) in front of a block (title, item): it sits at the block's first line."""
    def __init__(self, icon, block, size=36, tone='focus', gap=14, badge=None):
        self.icon, self.block, self.size, self.tone, self.gap, self.badge = icon, block, size, tone, gap, badge
    def measure(self, w): return max(self.size, self.block.measure(w - self.size - self.gap))
    def place(self, x, y, w, h, out):
        bh = self.block.measure(w - self.size - self.gap)
        iy = y + max(0, (min(bh, self.size * 1.2) - self.size) / 2)
        if self.badge is not None:
            out.append({'k': 'badge', 'text': str(self.badge), 'x': x, 'y': iy, 'size': self.size, 'tone': self.tone})
        else:
            out.append({'k': 'icon', 'name': self.icon, 'x': x, 'y': iy, 'size': self.size, 'tone': self.tone, 'disc': True})
        self.block.place(x + self.size + self.gap, y + max(0, (self.size - bh) / 2) if bh < self.size else y, w - self.size - self.gap, bh, out)
    def html(self):
        mark = (f'<span class="kzl-badge is-{self.tone}" style="--s:{self.size:g}">{escape(str(self.badge))}</span>' if self.badge is not None
                else f'<span class="kzl-icon is-disc is-{self.tone}" style="--s:{self.size:g}">{icon_svg(self.icon)}</span>')
        return f'<div class="kzl-lead" style="--s:{self.size:g};gap:{u(self.gap)}">{mark}<div>{self.block.html()}</div></div>'

def Band(markup, tone='tint'):
    """The page's conclusion line in a tinted strip (the reference decks close most body pages with one)."""
    return Card([Text(markup, 'item_title', align='middle')], variant=tone, justify='center', pad=[24, 12])

def KpiTile(value, label, tone='brand'):
    return Card([Kpi(value, label, tone=tone, role='kpi_small', align='middle')], justify='center', pad=[16, 10])

class Items(Node):
    """List with drawn markers: 'dot', 'number' (orange disc with the item number, numbering continues across
    pages through `start`), 'check', 'cross', or an icon name per item. One paragraph per item; continuation lines
    hang under the text, not under the marker. An item {'level': 1} is a sub-item: it hangs under its parent's text
    with a dot ('marker': 'none' when its text carries its own label such as （1）). align='spread' spaces the items
    over the card's spare height; align='top' keeps them at item_gap from the top (rule text read down a column)."""
    def __init__(self, items, marker='dot', start=1, role='body', gap=None, columns=1, col_gap=None, tone='brand', align='spread'):
        self.items, self.marker, self.start, self.role, self.columns, self.tone = list(items), marker, start, role, columns, tone
        self.align = align
        self.flex = 1  # a list takes the spare height of its card (and, when spread, spaces its items over it)
        s = ROLES[role][0]
        self.gap = L['item_gap'] if gap is None else gap
        self.col_gap = col_gap or L['gap']
        self.mw = {'dot': s * 0.9, 'number': max(s * 1.55, max(22, s * 1.15) + 7), 'check': s * 1.25, 'cross': s * 1.25}.get(marker, s * 1.5)
        self.sw = s * 0.9  # sub-item dot column
    def _ind(self, it):
        """Left offset of an item's text: the marker column, plus the sub-item dot column for a sub-item."""
        return self.mw + (self.sw if isinstance(it, dict) and it.get('level') else 0)
    def _cols(self, hs=None):
        """Column-major split into consecutive runs with balanced heights (hs: measured item heights; text length
        when no width is known, as in html()). Numbering reads down one column, then the next."""
        from .paginate import partition, chunks
        n = len(self.items); k = max(1, min(self.columns, n))
        hs = hs or [len(T.plain(it if isinstance(it, str) else it['text'])) + 8 for it in self.items]
        return [list(range(a, b)) for a, b in chunks(n, partition(hs, [1] * k, self.gap))]
    def _texts(self):
        return [Text(it if isinstance(it, str) else it['text'], self.role) for it in self.items]
    def measure(self, w):
        cw = (w - self.col_gap * (self.columns - 1)) / self.columns
        ts = self._texts(); hs = [t.measure(cw - self._ind(it)) for t, it in zip(ts, self.items)]
        return max(sum(hs[i] for i in col) + self.gap * (len(col) - 1) for col in self._cols(hs))
    def place(self, x, y, w, h, out):
        cw = (w - self.col_gap * (self.columns - 1)) / self.columns
        ts = self._texts(); s, lead = ts[0].size, ts[0].lead if ts else (20, 1.5)
        tw = [cw - self._ind(it) for it in self.items]
        for ci, col in enumerate(self._cols([t.measure(w_) for t, w_ in zip(ts, tw)])):
            cx, cy = x + ci * (cw + self.col_gap), y
            used = sum(ts[i].measure(tw[i]) for i in col) + self.gap * (len(col) - 1)
            gap = self.gap
            if self.align == 'spread':
                gap += max(0, h - used) / max(1, len(col) - 1) if len(col) > 1 and h - used > 0 else 0
                gap = min(gap, self.gap + L['item_gap_stretch_max'])
                cy += max(0, h - used - (gap - self.gap) * (len(col) - 1)) / 2  # what the capped gaps leave is split above and below
            for i in col:
                it = self.items[i]; th = ts[i].measure(tw[i]); sub = isinstance(it, dict) and it.get('level')
                mk = it.get('marker') if isinstance(it, dict) else None
                out.append({'k': 'marker', 'kind': mk or ('dot' if sub else self.marker), 'n': (it.get('n') if isinstance(it, dict) else None) or self.start + i,
                            'x': cx + (self.mw if sub else 0), 'y': cy, 'size': s, 'lead': lead, 'tone': (it.get('tone') if isinstance(it, dict) else None) or self.tone})
                ts[i].place(cx + self._ind(it), cy, tw[i], th, out)
                cy += th + gap
    def html(self):
        tag = 'ol' if self.marker == 'number' else 'ul'
        start = f' start="{self.start}"' if self.marker == 'number' and self.start != 1 else ''
        lis = []
        for i, it in enumerate(self.items):
            t = it if isinstance(it, str) else it['text']; mk = (it.get('marker') if isinstance(it, dict) else None) or self.marker
            tone = (it.get('tone') if isinstance(it, dict) else None) or self.tone
            num = (it.get('n') if isinstance(it, dict) else None) or self.start + i
            sub = isinstance(it, dict) and it.get('level')
            if sub and not (isinstance(it, dict) and it.get('marker')): mk = 'dot'
            sym = (f'<span class="kzl-mk is-number">{num}</span>' if mk == 'number' else '<span class="kzl-mk is-none"></span>' if mk == 'none' else '<span class="kzl-mk is-dot"></span>' if mk == 'dot'
                   else f'<span class="kzl-mk is-icon">{icon_svg("check" if mk == "check" else "cross" if mk == "cross" else mk)}</span>')
            lis.append(f'<li class="is-{tone}{" is-sub" if sub else ""}">{sym}<span class="kzl-li">{runs_html(t)}</span></li>')
        cls = f'kzl-items kzl-{CSS_ROLE[self.role]}' + (' is-top' if self.align == 'top' else '')
        if self.columns > 1:
            lists = ''.join(f'<{tag} class="{cls}" style="--gap:{self.gap:g}">' + ''.join(lis[i] for i in col) + f'</{tag}>' for col in self._cols())
            return f'<div class="kzl-cols" style="--cols:{len(self._cols())};column-gap:{u(self.col_gap)}">{lists}</div>'
        return f'<{tag} class="{cls}"{start} style="--gap:{self.gap:g}">' + ''.join(lis) + f'</{tag}>'

class Kpi(Node):
    def __init__(self, value, label, tone='ink', role='kpi', align='start'):
        self.value, self.label, self.tone, self.role, self.align = value, label, tone, role, align
    def _v(self): return Text(self.value, self.role, color=RISK if self.tone == 'risk' else C['focus'] if self.tone == 'brand' else INK, align=self.align, nowrap=True)
    def _l(self): return Text(self.label, 'label', align=self.align)
    def measure(self, w): return self._v().measure(w) + 4 + self._l().measure(w)
    def place(self, x, y, w, h, out):
        v, l = self._v(), self._l(); vh = v.measure(w); lh = l.measure(w); top = y + max(0, (h - vh - 4 - lh) / 2)
        v.place(x, top, w, vh, out); l.place(x, top + vh + 4, w, lh, out)
    def html(self):
        return f'<div class="kzl-kpi is-{self.tone}" style="text-align:{"center" if self.align == "middle" else "left"}"><b class="kzl-{CSS_ROLE[self.role]}">{runs_html(self.value)}</b><span class="kzl-secondary">{runs_html(self.label)}</span></div>'

class Figure(Node):
    """A drawing that fills the space it is given: chart, table or diagram (see figures.py). `min_h` is its
    natural height; `flex` lets it take the spare height of its stack."""
    unit = True
    def __init__(self, kind, spec, min_h=200, flex=1, id=None, aspect=None):
        self.kind, self.spec, self.min_h, self.flex, self.id, self.aspect = kind, spec, min_h, flex, id, aspect
    def measure(self, w):
        if self.kind == 'table':  # a table is as tall as its rows; spare height then grows the rows (figures.table_layout)
            from .figures import table_layout
            return table_layout(self.spec, [0, 0, w, 0], grow=False)['need']
        from .diagrams import MEASURE
        if self.kind in MEASURE: return max(self.min_h if self.flex else 0, MEASURE[self.kind](self.spec, w))
        return max(self.min_h, w / self.aspect) if self.aspect else self.min_h
    def place(self, x, y, w, h, out):
        self.box = [x, y, w, h]
        out.append({'k': 'figure', 'kind': self.kind, 'spec': self.spec, 'x': x, 'y': y, 'w': w, 'h': h, 'id': self.id})
    def html(self):
        from . import figures
        box = getattr(self, 'box', None)  # a fixed-height diagram (flex 0) keeps its measured height in HTML too
        from .diagrams import DRAW
        # a drawn diagram keeps the height the PPTX solver gave it, so its viewBox renders at scale 1 (16 px text stays 16 px)
        mh = box[3] if box and (self.kind in DRAW or not self.flex) else self.min_h
        return figures.html(self.kind, self.spec, self.id or 'fig', mh, box)

def solve(root, box=None):
    """Place the tree in the body box (tokens.chrome.body). Returns (primitives, overflow_px)."""
    x, y, w, h = box or TOK['chrome']['body']
    need = root.measure(w)
    out = []
    root.place(x, y, w, max(h, need) if need > h else h, out)
    return out, max(0.0, need - h)
