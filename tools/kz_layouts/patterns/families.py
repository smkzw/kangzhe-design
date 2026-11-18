"""8.0 variant families (13 BODY-03): the same kind of content in several looks, so neighbouring pages do not repeat
one form, and three density tiers so a page's look follows how much it has to say.

Parallel points come in nine looks (icon-grid and numbered-cards live in general.py / clinical.py): strips, claim +
support, steps, big numbers, matrix, figure + points, dense cards, column flow and the hub. Every card keeps its
content as one group distributed over its height (03 TYPE-02), sibling cards follow one copy budget, and status is
always a word on a tag (01 CORE-01), never colour alone.
"""
from .. import pattern
from ..tree import (Card, Items, Row, Stack, Text, IconLead, Kpi, Band, Figure, Icon, Tag, Chips, KeyRow, Chevron, Numeral,
                    Spacer, C)

from ..tree import TOK
CLAIM_PX = TOK['type_px']['takeaway'] * 1.5   # the one judgement of a claim page reads as a headline (36 px)

def _close(body, d, gap=14):
    tail = ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack([body] + tail, justify='fill', gap=gap)

def _list(items, role='secondary'):
    """A list that keeps its natural height: the card centres its content as one group instead of spreading the
    items over spare height (03 TYPE-02)."""
    it = Items(items, role=role, gap=6); it.flex = 0
    return it

def _extras(p, role='secondary'):
    """Optional parts shared by the point looks: a list, data rows, chips."""
    out = []
    if p.get('items'): out.append(_list(p['items'], role))
    if p.get('rows'): out.append(Stack([KeyRow(r['label'], r.get('value'), r.get('tag')) for r in p['rows']], gap=6, justify='start'))
    if p.get('chips'): out.append(Chips(p['chips']))
    return out

def _tag(p, align='start'):
    return Tag(p['tag']['text'], p['tag'].get('tone', 'info'), align=align) if p.get('tag') else None

# ---------------------------------------------------------------- strips
@pattern('points-strips', scene='通用', title='横条列表（序号 · 标题与说明 · 关键数 · 状态）', density='中高', family='points', tiers=('standard', 'dense'),
         use='3–6 条并列要点，说明较长（一两句）或带状态；每条一行：序号或图标、标题与说明（可带 2–3 条子项）、右侧关键数与状态')
def points_strips(d):
    rows = []
    for i, r in enumerate(d['rows']):
        lead = IconLead(r.get('icon'), Stack([Text(r['title'], 'item_title'), Text(r['text'], 'body')] + _extras(r), gap=6, justify='start'),
                        size=40, badge=None if r.get('icon') else i + 1 + d.get('start', 0))
        right = []
        if r.get('value') is not None: right.append(Kpi(r['value'], r.get('label', ''), tone=r.get('tone', 'brand'), role='kpi_small', align='end'))
        if r.get('tag'): right.append(_tag(r, 'end'))
        parts = [lead] + ([Stack(right, gap=8, justify='center')] if right else [])
        rows.append(Card([Row(parts, weights=[3.4, 1] if right else [1], gap=24, align='center')], justify='center', pad=[26, 10]))
    return _close(Stack(rows, gap=10, justify='distribute', flex=1), d)

# ---------------------------------------------------------------- claim + support
@pattern('points-claim', scene='通用', title='论点 + 支撑（一句核心判断 · 2–4 张支撑卡）', density='中', family='points', tiers=('sparse', 'standard'),
         use='有一句核心判断时：左侧论点卡（引导语、判断句、一两句说明），右侧 2–4 张紧凑支撑卡（图标、标题、一句说明，可带子项或状态）')
def points_claim(d):
    c = d['claim']
    left = Card(([Text(c['kicker'], 'label', color=C['focus'], bold=True)] if c.get('kicker') else []) + [Text(c['text'], 'takeaway', size=CLAIM_PX)]
                + ([Text(c['note'], 'body')] if c.get('note') else []) + ([Chips(c['chips'])] if c.get('chips') else []),
                variant='tint', justify='center', gap=18, pad=[34, 28], flex=1)
    from ..icon_pick import pick
    side = []
    for p, ic in zip(d['points'], pick(d['points'])):
        head = [Text(p['title'], 'item_title'), Text(p['text'], 'secondary')] + _extras(p)
        body = IconLead(ic, Stack(head, gap=6, justify='start'), size=40)
        side.append(Card([Row([body, _tag(p, 'end')], weights=[4, 1], gap=12, align='center') if p.get('tag') else body], justify='center', pad=[22, 14], flex=1))
    return _close(Row([left, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [1, 1.45]), gap=20, flex=1), d)

# ---------------------------------------------------------------- steps
@pattern('points-steps', scene='通用', title='步骤箭头（有先后的 3–5 步 · 每步说明与关键数）', density='中', family='process', tiers=('standard',),
         use='有先后顺序的 3–5 步：上方箭头条写步名，下方每步一张卡（一句说明、2–3 条子项、关键数或状态）；没有顺序的并列要点不用它')
def points_steps(d):
    n = len(d['steps'])
    heads = Row([Chevron(s['title'], s.get('number', f'{i + 1:02d}'), i, n) for i, s in enumerate(d['steps'])], gap=10, flex=0)
    cards = []
    for s in d['steps']:
        parts = ([Text(s['text'], 'body')] if s.get('text') else []) + _extras(s)
        if s.get('value') is not None: parts.append(Kpi(s['value'], s.get('label', ''), tone=s.get('tone', 'brand'), role='kpi_small'))
        if s.get('tag'): parts.append(_tag(s))
        cards.append(Card(parts, justify='distribute', gap=12, pad=[22, 18], flex=1))
    return _close(Stack([heads, Row(cards, gap=10, flex=1)], gap=12, justify='fill', flex=1), d)

# ---------------------------------------------------------------- big numbers
@pattern('points-numbers', scene='通用', title='大数字（2–4 个数字领起的要点）', density='低', family='data', tiers=('sparse', 'standard'),
         use='每个要点都由一个数字领起时：2–4 张卡，大数字与单位、数字标签、标题、一两句说明；数字必须来自材料')
def points_numbers(d):
    cards = []
    for p in d['numbers']:
        parts = [Numeral(p['value'], p.get('unit', ''), tone=p.get('tone', 'brand')), Text(p['label'], 'label')]
        parts += [Spacer(4, 0), Text(p['title'], 'item_title')] + ([Text(p['text'], 'body')] if p.get('text') else []) + _extras(p)
        cards.append(Card(parts, justify='center', gap=8, pad=[30, 24], flex=1))
    return _close(Row(cards, gap=20, flex=1), d)

# ---------------------------------------------------------------- matrix
@pattern('points-matrix', scene='通用', title='对照矩阵（条目 × 做法 × 影响 × 状态）', density='中高', family='compare', tiers=('standard', 'dense'),
         use='每条要点要在同样的几个维度上比较时：表头一行，每条一行（图标与标题、2–3 个维度的说明、状态胶囊）')
def points_matrix(d):
    cols = d['columns']; w = d.get('weights') or [1.2] + [1.6] * (len(cols) - 2) + [0.7]
    head = Row([Text(c, 'label', bold=True) for c in cols], weights=w, gap=20, flex=0)
    rows = []
    for r in d['rows']:
        first = IconLead(r.get('icon', 'dot'), Text(r['title'], 'item_title'), size=36) if r.get('icon') else Text(r['title'], 'item_title')
        cells = [first] + [Text(c, 'secondary') for c in r['cells']] + [_tag(r) or Text('', 'secondary')]
        rows.append(Card([Row(cells, weights=w, gap=20, align='center')], justify='center', pad=[24, 14]))
    return _close(Stack([Card([head], variant='plain', justify='center', pad=[24, 10], flex=0)] + rows, gap=10, justify='distribute', flex=1), d)

# ---------------------------------------------------------------- figure + points
@pattern('points-figure', scene='通用', title='左图右文（一张图 · 编号要点）', density='中', family='points', tiers=('standard',),
         use='有一个可视化对象（数据图、示意图或一个关键数字）时：左侧图卡，右侧 3–4 条编号要点（标题与说明）')
def points_figure(d):
    f = d['figure']
    if f.get('kind'): left = Card([Figure(f['kind'], f['spec'], min_h=f.get('min_h', 260), flex=1)] + ([Text(f['caption'], 'label', align='middle')] if f.get('caption') else []),
                                  title=f.get('title'), justify='fill', gap=10, pad=[24, 18], flex=1)
    else:
        left = Card([Icon(f.get('icon', 'doc'), 88, 'focus', True), Numeral(f['value'], f.get('unit', ''), align='middle') if f.get('value') is not None else None,
                     Text(f.get('label', ''), 'label', align='middle') if f.get('label') else None, Text(f['caption'], 'body', align='middle') if f.get('caption') else None],
                    variant='tint', justify='center', gap=12, pad=[30, 24], flex=1)
    pts = [Card([IconLead(None, Stack([Text(p['title'], 'item_title'), Text(p['text'], 'body')] + _extras(p), gap=6, justify='start'), size=40, badge=i + 1)],
                justify='center', pad=[24, 14], flex=1) for i, p in enumerate(d['points'])]
    return _close(Row([left, Stack(pts, gap=12, justify='fill')], weights=d.get('weights', [1, 1.5]), gap=20, flex=1), d)

# ---------------------------------------------------------------- dense cards (METRIC density)
@pattern('cards-dense', scene='通用', title='高密度卡片网格（图标标题 · 状态 · 子项 · 数据行）', density='高', family='points', tiers=('dense',),
         use='4–8 个对象都有不少内容时（汇报到管理层的现状盘点）：每卡图标与标题、状态胶囊、2–4 条子项、一两条键值行；layout 4x2 | 3x2 | 4x1')
def cards_dense(d):
    cs = d['cards']; cols = {'4x2': 4, '3x2': 3, '4x1': 4, '2x2': 2}.get(d.get('layout'), 4 if len(cs) in (4, 8) else 3)
    def card(c):
        head = IconLead(c.get('icon', 'doc'), Text(c['title'], 'item_title'), size=36)
        top = Row([head, _tag(c, 'end')], weights=[3, 1.3], gap=8, align='center') if c.get('tag') else head
        parts = [top] + ([Text(c['text'], 'secondary')] if c.get('text') else []) + _extras(c)
        return Card(parts, justify='distribute', gap=10, pad=[20, 16], flex=1)
    rows = [cs[i:i + cols] for i in range(0, len(cs), cols)]
    grid = Stack([Row([card(c) for c in r] + [Stack([])] * (cols - len(r)), gap=14, flex=1) for r in rows], gap=14, justify='fill', flex=1)
    return _close(grid, d)

# ---------------------------------------------------------------- column flow (METRIC p07)
@pattern('columns-flow', scene='通用', title='分栏流程（4–5 栏 · 箭头表头 · 栏内多块 · 衔接带）', density='高', family='process', tiers=('dense',),
         use='一个流程的 4–5 个环节各有不少内容（清单、键值、子项、判定）：箭头表头写环节名，每栏一张卡放 2–4 个块，栏底一句提示；底部可加一条衔接带说明与上下游模块的关系。PPTX 画布上一栏不窄于 220 px，所以最多 5 栏')
def columns_flow(d):
    cols = d['columns']; n = len(cols)
    if n > 5: raise ValueError('columns-flow 最多 5 栏（1280 宽画布上每栏至少 220 px）；环节更多时拆成两页或改用 process')
    heads = Row([Chevron(c['title'], c.get('number', f'{i + 1}'), i, n, h=52) for i, c in enumerate(cols)], gap=8, flex=0)
    def block(b):
        if 'label' in b and len(b) == 1: return [Text(b['label'], 'label', bold=True)]
        if b.get('rows'): return [Stack([KeyRow(r['label'], r.get('value'), r.get('tag')) for r in b['rows']], gap=6, justify='start')]  # one block, one group
        if b.get('items'): return [_list(b['items'])]
        if b.get('chips'): return [Chips(b['chips'])]
        if b.get('text'): return [Text(b['text'], 'secondary')]
        return []
    cards = []
    for c in cols:
        parts = [x for b in c['blocks'] for x in block(b)]
        if c.get('foot'): parts.append(Text(c['foot'], 'label', align='middle'))
        cards.append(Card(parts, justify='distribute', gap=10, pad=[14, 16], flex=1))
    body = [heads, Row(cards, gap=8, flex=1)]
    if d.get('link'):
        lk = d['link']
        segs = [Stack([Text(lk['title'], 'item_title')] + ([Text(lk['text'], 'label')] if lk.get('text') else []), gap=2, justify='center')]
        segs += [Stack([Text(s['label'], 'label'), Text(s['text'], 'secondary', bold=True)], gap=2, justify='center') for s in lk['segments']]
        body.append(Card([Row(segs, weights=[0.8] + [1] * len(lk['segments']), gap=18, align='center')], variant='tint', justify='center', pad=[24, 12], flex=0))
    return _close(Stack(body, gap=10, justify='fill', flex=1), d)
