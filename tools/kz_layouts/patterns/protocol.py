"""Protocol discussion templates (研究方案讨论会): the page kinds of a protocol review deck, one data shape each.
Modelled on the page kinds of a reviewed protocol-discussion deck: basic information, PICOS, numbered rationale,
rule tables, endpoints, concomitant medication, discussion questions. Every page may close with a conclusion band."""
from .. import pattern
from ..tree import Card, Items, Row, Stack, Text, Figure, IconLead, Band, KpiTile, Spacer
from ..paginate import split_rows

def _close(body, d, gap=14):
    """The body, then the page's conclusion band and source note when given."""
    tail = ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack([body] + tail, justify='fill', gap=gap)

CAT = ['cat1', 'cat2', 'cat3', 'cat4', 'cat5', 'ink']  # badge tones in the fixed categorical order (never department colours)

# ---------------------------------------------------------------- 研究基本信息
@pattern('kv-table', scene='方案讨论', title='研究基本信息（键值表）', density='高', split=lambda d, fits: split_rows(d, fits),
         use='方案要素逐项列出（药物、适应症、题目、分期、编号、版本、组长单位、剂型、途径、用法用量）；rows=[[项目, 内容]]')
def kv_table(d):
    spec = {'header': False, 'rows': d['rows'], 'widths': d.get('widths', [1, 4.2]), 'first_fill': True}
    return _close(Figure('table', spec, flex=1), d)

# ---------------------------------------------------------------- PICOS(N)
@pattern('picos', scene='方案讨论', title='PICOS 研究框架（字母行 + 指标列）', density='高',
         use='研究人群、干预、对照、终点、设计、样本量逐行一字母；行内可带一条判定注记；右侧 3–5 个关键数字')
def picos(d):
    rows = []
    for i, r in enumerate(d['rows']):
        block = Stack([Text(r['title'], 'item_title'), Text(r['text'], 'secondary')], gap=2, justify='start')
        if r.get('note'):
            block = Row([block, Card([Text(r['note'], 'label')], variant='tint', pad=[12, 6], justify='center')], weights=[2, 1], gap=12)
        rows.append(Card([IconLead(None, block, size=36, badge=r['badge'], tone=r.get('tone', CAT[i % len(CAT)]))], justify='center', pad=[18, 8], flex=1))
    left = Stack(rows, gap=8, justify='fill')
    if not d.get('kpis'): return _close(left, d)
    right = Stack([KpiTile(k['value'], k['label'], k.get('tone', 'brand')) for k in d['kpis']], gap=8, justify='fill')
    for c in right.children: c.flex = 1
    return _close(Row([left, right], weights=[3.3, 1], gap=20, flex=1), d)

# ---------------------------------------------------------------- 编号依据卡
@pattern('numbered-cards', scene='通用', title='编号要点卡（含卡底指标）', density='中高',
         use='3–6 条并列依据或要点（剂量依据、选择理由、风险来源）；每卡：编号、标题、两三句说明、卡底一条关键指标；layout 3x2 | 2x3 | 2x2 | 4x1')
def numbered_cards(d):
    cs = d['cards']; cols = {'3x2': 3, '2x3': 2, '2x2': 2, '4x1': 4, '3x1': 3}.get(d.get('layout'), 3 if len(cs) in (3, 6) else 2)
    def card(n, c):
        parts = [IconLead(None, Text(c['title'], 'item_title'), size=30, badge=n), Text(c['text'], 'secondary')]
        if c.get('foot'): parts += [Spacer(0, flex=1), Text(c['foot'], 'item_title', align='middle', color='#B85C00')]
        return Card(parts, justify='start', gap=10, flex=1)
    rows = [cs[i:i + cols] for i in range(0, len(cs), cols)]
    grid = Stack([Row([card(i * cols + j + 1, c) for j, c in enumerate(r)] + [Stack([])] * (cols - len(r)), flex=1) for i, r in enumerate(rows)],
                 justify='fill', gap=16, flex=1)
    return _close(grid, d)

# ---------------------------------------------------------------- 规则表 + 结论
@pattern('table-band', scene='通用', title='规则表（含结论带）', density='高', split=lambda d, fits: split_rows(d, fits),
         use='逐行规则或对照：药物类别与洗脱期、禁用药与例外、竞品口径对比；原文不压缩，行多按行分页')
def table_band(d):
    spec = {k: d[k] for k in ('columns', 'groups', 'rows', 'widths', 'numeric', 'center', 'first_bold', 'first_fill') if k in d}
    head = [Card([Text(d['lead'], 'item_title')], variant='tint', pad=[18, 8], justify='center')] if d.get('lead') else []
    return _close(Stack(head + [Figure('table', spec, flex=1)], gap=10, justify='fill', flex=1), d)

# ---------------------------------------------------------------- 研究终点
@pattern('endpoints', scene='方案讨论', title='研究终点（主要终点横幅 + 分类卡）', density='高',
         use='主要终点一句话横幅；次要、探索、安全性、PK/PD 等分类各一卡，条目照方案原文')
def endpoints(d):
    p = d['primary']
    banner = Card([Row([Text(p.get('label', '主要终点'), 'item_title', color='#B85C00'), Text(p['text'], 'item_title')], weights=[1, 5.5], gap=16)],
                  variant='tint', pad=[20, 12], justify='center')
    gs = d['groups']; cols = d.get('columns', 3 if len(gs) in (3, 5, 6) else 2)
    def card(g): return Card([Items(g['items'], role='secondary', gap=6)], title=g['title'], icon=g.get('icon'), justify='start', gap=10, flex=1)
    rows = [gs[i:i + cols] for i in range(0, len(gs), cols)]
    grid = Stack([Row([card(g) for g in r] + [Stack([])] * (cols - len(r)), flex=1) for r in rows], justify='fill', gap=14, flex=1)
    return _close(Stack([banner, grid], gap=14, justify='fill', flex=1), d)

# ---------------------------------------------------------------- 允许 / 禁用
@pattern('allow-deny', scene='方案讨论', title='允许与禁用（伴随用药、操作规定）', density='高',
         use='背景治疗横幅；允许与禁用两栏逐条原文（✓ / ✕）；补救或例外规则用标签行')
def allow_deny(d):
    parts = []
    if d.get('banner'):
        b = d['banner']
        parts.append(Card([Row([Text(b['label'], 'item_title', color='#B85C00'), Text(b['text'], 'secondary')], weights=[1, 6], gap=16)],
                          variant='tint', pad=[20, 10], justify='center'))
    cols = Row([Card([Items(d['allowed'], marker='check', role='secondary', gap=6)], title=d.get('allowed_title', '允许使用'), icon='circle-check', justify='start', gap=10),
                Card([Items(d['prohibited'], marker='cross', role='secondary', gap=6)], title=d.get('prohibited_title', '禁止使用'), icon='circle-x', justify='start', gap=10)],
               flex=1)
    parts.append(cols)
    for r in d.get('rules', []):
        parts.append(Card([Row([Text(r['tag'], 'item_title', color='#B85C00'), Text(r['text'], 'secondary')], weights=[1, 6], gap=16)],
                          variant='plain', pad=[20, 8], justify='center'))
    return _close(Stack(parts, gap=12, justify='fill', flex=1), d)

# ---------------------------------------------------------------- 讨论题
@pattern('discussion', scene='方案讨论', title='讨论题（现状 + 多方视角 + 开放问题）', density='高',
         use='先写现状与争议点（可配示意图），再并列本方案、指南、竞品等视角（2–4 栏），最后一句开放问题')
def discussion(d):
    iss = d['issue']
    top = [Text(iss['title'], 'item_title')]
    if iss.get('figure'): top.append(Figure(iss['figure']['kind'], iss['figure'], min_h=iss['figure'].get('min_h', 150), flex=0))
    if iss.get('items'): top.append(Items(iss['items'], role='secondary', gap=4))
    head = Card(top, justify='start', gap=8)
    views = Row([Card([Items(v['items'], role='secondary', gap=6)], title=v['title'], icon=v.get('icon'), justify='start', gap=10) for v in d['views']], flex=1)
    q = Band(d['question'], tone='tint') if d.get('question') else None
    return Stack([head, views] + ([q] if q else []) + ([Text(d['note'], 'label')] if d.get('note') else []), gap=12, justify='fill')

# ---------------------------------------------------------------- 研究设计总览
@pattern('study-schema', scene='方案讨论', title='研究设计总览（分期 · 访视 · 分组 + 指标条）', density='高',
         use='整体流程：分期带、访视轴（访视号/周次）、随机与主要终点节点、各组给药条、背景治疗；底部 3–4 个关键数字')
def study_schema(d):
    fig = Card([Figure('schema', d['schema'], min_h=300, flex=1)], justify='fill', pad=[20, 14], flex=1)
    kp = Row([KpiTile(k['value'], k['label'], k.get('tone', 'brand')) for k in d.get('kpis', [])], gap=14) if d.get('kpis') else None
    return _close(Stack([fig] + ([kp] if kp else []), gap=14, justify='fill', flex=1), d)

# ---------------------------------------------------------------- 时间窗口 / 收集时限
@pattern('windows', scene='方案讨论', title='时间窗口与规则卡（AE 收集时限、访视窗口、报告时限）', density='高',
         use='时间轴上的关键节点与区间（如 ICF → 首次给药 → 研究结束），下接 2–4 张规则卡（SAE 定义、AESI、妊娠等）')
def windows(d):
    tl = Figure('timeline', d['timeline'], min_h=d['timeline'].get('min_h', 170), flex=1)
    fig = Card(([Text(d['timeline_title'], 'item_title')] if d.get('timeline_title') else []) + [tl], justify='start', gap=6, pad=[20, 12])
    cards = Row([Card([Items(c['items'], role='secondary', gap=5)], title=c['title'], icon=c.get('icon'), justify='start', gap=8) for c in d['cards']], flex=1)
    return _close(Stack([fig, cards], gap=12, justify='fill', flex=1), d)
