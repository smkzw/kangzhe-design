"""General templates with several layouts for everyday content."""
from .. import pattern
from ..tree import Card, Items, Row, Stack, Text, IconLead, Kpi

@pattern('icon-grid', scene='通用', title='图标要点网格', density='中',
         use='3–6 个并列要点，每点一个图标、一个小标题、一两句说明；layout: "3x2" | "2x3" | "4x1"')
def icon_grid(d):
    pts = d['points']; cols = {'3x2': 3, '2x3': 2, '4x1': 4, '3x1': 3, '2x2': 2}.get(d.get('layout'), 3 if len(pts) in (3, 6) else 2)
    rows = [pts[i:i + cols] for i in range(0, len(pts), cols)]
    def card(p):
        return Card([IconLead(p['icon'], Stack([Text(p['title'], 'item_title'), Text(p['text'], 'body')], gap=6, justify='start'), size=44)], justify='center')
    grid = Stack([Row([card(p) for p in r] + [Stack([])] * (cols - len(r)), flex=1) for r in rows], justify='fill', gap=24, flex=1)
    return Stack([grid] + ([Text(d['takeaway'], 'takeaway', align='middle')] if d.get('takeaway') else []), justify='fill', gap=20)

# ---------------------------------------------------------------- 数据图 + 解读
@pattern('chart-insight', scene='通用', title='数据图 + 解读（小多图 / 侧解读）', density='高',
         use='1–3 张数据图（柱、条、线、堆叠、组合、环形）各配标题与一句说明，再配 2–4 条解读；layout charts-top | chart-side')
def chart_insight(d):
    from ..tree import Figure, Band, Card
    def chart_card(c):
        parts = [Figure('chart', c['chart'], min_h=c.get('min_h', 200), flex=1)]
        if c.get('caption'): parts.append(Text(c['caption'], 'label', align='middle'))
        return Card(parts, title=c.get('title'), justify='start', gap=8, flex=1)
    def insight(i):
        return Card([IconLead(i.get('icon', 'bulb'), Stack([Text(i['title'], 'item_title')] + ([Text(i['text'], 'secondary')] if i.get('text') else [])
                                                           + ([Items(i['items'], role='secondary', gap=6)] if i.get('items') else []), gap=6, justify='start'), size=32)],
                    justify='center', pad=[18, 12], flex=1)
    charts = [chart_card(c) for c in d['charts']]; ins = [insight(i) for i in d.get('insights', [])]
    if d.get('layout') == 'chart-side':
        body = Row([Stack(charts, gap=14, justify='fill'), Stack(ins, gap=12, justify='fill')], weights=d.get('weights', [1.7, 1]), gap=20, flex=1)
    else:
        rows = [Row(charts, flex=3)] + ([Row(ins, flex=1)] if ins else [])
        body = Stack(rows, gap=14, justify='fill', flex=1)
    tail = [Band(d['band'])] if d.get('band') else []
    return Stack([body] + tail + ([Text(d['note'], 'label')] if d.get('note') else []), justify='fill', gap=14)

# ---------------------------------------------------------------- 流程 + 解析
@pattern('process', scene='通用', title='流程图 + 解析（步骤 · 退回分支 · 解析卡）', density='中高',
         use='3–6 个步骤的流程（每步标题与一句规则，可标出退回或升级分支），下接 2–4 张解析卡说明关键控制点')
def process(d):
    from ..tree import Figure, Band
    fig = Card([Figure('flow', d['flow'], min_h=0, flex=0)], justify='center', pad=[20, 14], flex=0)
    ins = Row([Card([IconLead(i.get('icon', 'bulb'), Stack([Text(i['title'], 'item_title')] + ([Text(i['text'], 'secondary')] if i.get('text') else [])
                                                           + ([Items(i['items'], role='secondary', gap=6)] if i.get('items') else []), gap=6, justify='start'), size=32)],
                    justify='center', pad=[18, 12]) for i in d.get('notes', [])], flex=1) if d.get('notes') else None
    parts = [fig] + ([ins] if ins else []) + ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack(parts, gap=14, justify='fill')

def _close(body, d, gap=14):
    from ..tree import Band
    tail = ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack([body] + tail, justify='fill', gap=gap)

def _notes(items, size=32):
    return [Card([IconLead(i.get('icon', 'bulb'), Stack([Text(i['title'], 'item_title')] + ([Text(i['text'], 'secondary')] if i.get('text') else []), gap=4, justify='start'),
                           size=size, tone=i.get('tone', 'focus'))], justify='center', pad=[18, 12], flex=1) for i in items]

def _fig_side(kind, spec, d, min_h=0, weights=(1.8, 1)):
    from ..tree import Figure
    fig = Card([Figure(kind, spec, min_h=min_h, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _notes(d.get('insights', []))
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=list(d.get('weights', weights)), gap=18, flex=1) if side else fig, d)

@pattern('funnel', scene='通用', title='漏斗 + 解读', density='中',
         use='3–6 个逐级收窄的阶段（筛选→入组→完成，线索→转化）带数值与环节转化率，右侧解读')
def funnel(d): return _fig_side('funnel', d['funnel'], d, 300)

@pattern('hub-spoke', scene='通用', title='中心辐射（平台 · 能力 · 场景）', density='中',
         use='一个中心（平台、目标、分子）与 4–8 个周边要点，每点图标、标题、一句说明')
def hub_spoke(d):
    from ..tree import Figure
    return _close(Card([Figure('hub', d['hub'], min_h=0, flex=1)], justify='center', pad=[20, 14], flex=1), d)

@pattern('quadrant', scene='通用', title='二维象限（优先级 · 定位）', density='中',
         use='两条维度、四个象限命名，条目按坐标落点；右侧给各象限的行动建议；适合优先级、竞品定位、AI 场景筛选')
def quadrant(d): return _fig_side('quadrant', d['quadrant'], d, 320, (1.5, 1))

@pattern('quote-evidence', scene='通用', title='观点引述 + 证据卡', density='中',
         use='一句核心观点或指南原文（注明出处），右侧 2–4 张证据卡：关键数字、说明与出处')
def quote_evidence(d):
    from ..tree import Icon
    q = d['quote']
    left = Card([Icon('quote', 40, 'focus', True), Text(q['text'], 'takeaway')] + ([Text(q['source'], 'label')] if q.get('source') else []),
                variant='tint', justify='center', gap=16, pad=[32, 24], flex=1)
    ev = [Card([Kpi(e['value'], e['label'], tone=e.get('tone', 'brand'), role='kpi_small'), Text(e['text'], 'secondary')] + ([Text(e['source'], 'label')] if e.get('source') else []),
               justify='center', gap=6, pad=[20, 12], flex=1) for e in d['evidence']]
    return _close(Row([left, Stack(ev, gap=12, justify='fill')], weights=d.get('weights', [1.15, 1]), gap=18, flex=1), d)
