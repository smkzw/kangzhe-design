"""Project and AI-report templates: dense plan Gantt, roadmap, KPI dashboard, risk register, architecture."""
from .. import pattern
from ..tree import Card, Items, Row, Stack, Text, Figure, IconLead, Band, KpiTile

def _close(body, d, gap=14):
    tail = ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack([body] + tail, justify='fill', gap=gap)

@pattern('gantt-plan', scene='项目汇报', title='高密度甘特（分组任务 · 进度 · 里程碑 · 当前线）', density='高',
         use='10–20 项任务按工作流分组，月度刻度，条内显示完成进度，里程碑与当前时点；右侧可放 2–3 条风险或关键路径说明')
def gantt_plan(d):
    fig = Card([Figure('gantt', d['gantt'], min_h=300, flex=1)], justify='fill', pad=[18, 14], flex=1)
    if d.get('side'):
        side = Stack([Card([IconLead(s.get('icon', 'alert-circle'), Stack([Text(s['title'], 'item_title'), Text(s['text'], 'secondary')], gap=4, justify='start'), size=30,
                                     tone=s.get('tone', 'focus'))], justify='center', pad=[16, 12], flex=1) for s in d['side']], gap=12, justify='fill')
        fig = Row([fig, side], weights=[3.2, 1], gap=16, flex=1)
    return _close(fig, d)

def _note_cards(items, size=32):
    return [Card([IconLead(i.get('icon', 'bulb'), Stack([Text(i['title'], 'item_title')] + ([Text(i['text'], 'secondary')] if i.get('text') else [])
                                                        + ([Items(i['items'], role='secondary', gap=6)] if i.get('items') else []), gap=4, justify='start'),
                           size=size, tone=i.get('tone', 'focus'))], justify='center', pad=[18, 12], flex=1) for i in items]

# ---------------------------------------------------------------- 方案比较
@pattern('options-compare', scene='项目汇报', title='方案比较（选项卡 · 利弊 · 对比表 · 建议）', density='高',
         use='2–3 个备选方案并排：一句定位、优点（勾）、代价（叉）；推荐项浅暖底；下方可接逐项对比表，最后一条建议带')
def options_compare(d):
    from ..tree import C
    def card(o):
        parts = ([Text(o['tag'], 'label', color=C['focus'], bold=True)] if o.get('tag') else []) + ([Text(o['summary'], 'secondary')] if o.get('summary') else [])
        parts += [Items(o.get('pros', []), marker='check', role='secondary', gap=6)] if o.get('pros') else []
        parts += [Items(o.get('cons', []), marker='cross', role='secondary', gap=6)] if o.get('cons') else []
        return Card(parts, title=o['name'], variant='tint' if o.get('recommended') else 'glass', justify='start', gap=10, flex=1)
    rows = [Row([card(o) for o in d['options']], gap=18, flex=1)]
    if d.get('table'): rows.append(Figure('table', d['table'], flex=0))
    return _close(Stack(rows, gap=14, justify='fill', flex=1), d)

# ---------------------------------------------------------------- KPI 看板
@pattern('kpi-dashboard', scene='项目汇报', title='KPI 看板（指标条 · 两图 · 解读）', density='高',
         use='3–5 个关键指标一行，下面 1–2 张趋势或构成图，可配 1–3 条解读；适合月度运营、AI 项目效果汇报')
def kpi_dashboard(d):
    tiles = Row([KpiTile(k['value'], k['label'], k.get('tone', 'brand')) for k in d['kpis']], gap=14, flex=0)
    def chart_card(c):
        parts = [Figure('chart', c['chart'], min_h=c.get('min_h', 180), flex=1)] + ([Text(c['caption'], 'label', align='middle')] if c.get('caption') else [])
        return Card(parts, title=c.get('title'), justify='start', gap=8, flex=1)
    mid = [chart_card(c) for c in d.get('charts', [])]
    if d.get('insights'): mid.append(Stack(_note_cards(d['insights'], 30), gap=12, justify='fill'))
    return _close(Stack([tiles, Row(mid, weights=d.get('weights'), gap=16, flex=1)], gap=14, justify='fill', flex=1), d)

# ---------------------------------------------------------------- 路线图
@pattern('roadmap', scene='项目汇报', title='路线图（阶段列 · 交付卡）', density='中高',
         use='3–4 个阶段（时间窗）各列 2–4 项交付或里程碑；当前阶段浅暖底；适合 AI 能力建设、项目年度计划')
def roadmap(d):
    cols = []
    for ph in d['phases']:
        head = Card([Text(ph['name'], 'item_title', align='middle')] + ([Text(ph['time'], 'label', align='middle')] if ph.get('time') else []),
                    variant='tint' if ph.get('current') else 'plain', justify='center', gap=2, pad=[16, 10], flex=0)
        cols.append(Stack([head] + _note_cards(ph['items'], 30), gap=10, justify='fill'))
    return _close(Row(cols, gap=16, flex=1), d)

# ---------------------------------------------------------------- 风险矩阵 + 登记表
@pattern('risk-matrix', scene='项目汇报', title='风险矩阵 + 风险登记表', density='高',
         use='可能性 × 影响热力格（编号圆点）配风险登记表（编号、风险、责任人、应对与时限）；适合项目、试验运营、AI 上线评审')
def risk_matrix(d):
    grid = Card([Figure('riskgrid', d['grid'], min_h=280, flex=1)], title=d.get('grid_title', '风险分布'), justify='fill', gap=8, pad=[20, 14], flex=1)
    reg = Card([Figure('table', d['register'], flex=1)], title=d.get('register_title', '风险登记'), justify='fill', gap=8, pad=[20, 14], flex=1)
    return _close(Row([grid, reg], weights=d.get('weights', [1, 1.75]), gap=18, flex=1), d)

# ---------------------------------------------------------------- 分层架构
@pattern('architecture', scene='AI 汇报', title='分层架构（层带 · 模块块 · 贯穿能力）', density='中高',
         use='3–5 层（数据、模型、服务、应用、用户）各列模块，右侧一条贯穿能力（安全、合规、评测）；下接 2–3 条说明')
def architecture(d):
    fig = Card([Figure('layers', d['layers'], min_h=0, flex=1)], justify='center', pad=[20, 14], flex=1)
    parts = [fig] + ([Row(_note_cards(d['notes'], 30), gap=16, flex=0)] if d.get('notes') else [])
    return _close(Stack(parts, gap=14, justify='fill', flex=1), d)
