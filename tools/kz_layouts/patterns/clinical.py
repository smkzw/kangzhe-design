"""Clinical-trial templates: dense criteria, study design, schedule of assessments, endpoints, subject flow,
efficacy chart with interpretation, forest plot, safety table, time-to-event curve, dense Gantt."""
from .. import pattern
from ..tree import Card, Items, Row, Stack, Text, Figure, Kpi, IconLead, L

# ---------------------------------------------------------------- 入选 / 排除标准（原文，按编号分页）
_CRIT = (('inclusion', 'inclusion_title', '入选标准', 'user-check', 'brand'),
         ('exclusion', 'exclusion_title', '排除标准', 'user-x', 'risk'))

def _criteria_split(data, fits):
    """One page: inclusion and exclusion side by side. More than one page: the lists flow through two columns per
    page, inclusion first, exclusion straight after (dense first, then split; 03 COPY-03). A list that carries on in
    the next column or page keeps its plain card title and its numbering; there is no 'continued' label."""
    from ..paginate import partition
    from ..text import plain
    lists = {k: list(data.get(k, [])) for k, *_ in _CRIT}
    vol = [max(1, sum(len(plain(t)) for t in lists[k])) for k, *_ in _CRIT]
    w = data.get('weights') or [max(0.8, min(1.25, v / (sum(vol) / 2))) for v in vol]
    for role in ('body', 'secondary'):
        one = {**data, 'weights': w, 'role': role, 'layout': 'pair', 'start': {k: 1 for k in lists}}
        if fits(one): return [{**one, 'page_of': [1, 1]}]
    role = 'secondary'
    import re
    def fits_one(k, text):
        return fits({**data, 'role': role, 'layout': 'flow', 'cols': [[{'key': k, 'start': 1, 'items': [text]}]]})
    def pieces(k, n, t):
        """A criterion taller than a column is broken at its own clause ends (；。) and carries on in the next column
        without a number and without a 'continued' label; the words are not touched (03 COPY-09)."""
        if fits_one(k, t): return [t]
        out, cur = [], ''
        for c in re.findall(r'[^；。]+[；。]?', t):
            if not cur or fits_one(k, cur + c): cur += c; continue
            out.append(cur); cur = c
        out.append(cur)
        bad = [x for x in out if not fits_one(k, x)]
        if bad: raise ValueError(f'{k} 第 {n + 1} 条有一句单独一栏也放不下，请检查原文：{bad[0][:30]}')
        return out
    units = {k: [] for k in lists}  # each unit is a whole criterion or one piece of it; 'n' keeps the source number
    for k in lists:
        for n, t in enumerate(lists[k]):
            for i, x in enumerate(pieces(k, n, t)): units[k].append({'text': x, 'n': n + 1, **({'marker': 'none'} if i else {})})
    flow = [(k, i) for k, *_ in _CRIT for i in range(len(units[k]))]
    def segs(run):  # consecutive flow positions → [{'key', 'start', 'items'}] per list
        out = []
        for k, i in run:
            u = units[k][i]
            if out and out[-1]['key'] == k: out[-1]['items'].append(u)
            else: out.append({'key': k, 'start': u['n'], 'items': [u]})
        return out
    def page(cols): return {**data, 'role': role, 'layout': 'flow', 'cols': [segs(c) for c in cols]}
    pages, cols, cur = [], [], []
    for pos in flow:
        if fits(page(cols + [cur + [pos]])): cur.append(pos); continue
        if not cur: raise ValueError(f'{pos[0]} 第 {units[pos[0]][pos[1]]["n"]} 条单独一栏也放不下，请检查原文')
        cols.append(cur); cur = [pos]
        if len(cols) == 2: pages.append(cols); cols = []
    cols.append(cur); pages.append(cols)
    # widow balance: a last page under half full shares the last two pages' columns evenly (earlier pages stay full)
    hs = lambda run: [len(plain(units[k][i]['text'])) + 12 for k, i in run]
    tail = [pos for c in pages[-1] for pos in c]
    if len(pages) > 1 and sum(hs(tail)) < 0.5 * sum(hs([pos for c in pages[-2] for pos in c])):
        run = [pos for c in pages[-2] + pages[-1] for pos in c]; ends = partition(hs(run), [1] * 4); a = 0; cols = []
        for b in ends: cols.append(run[a:b]); a = b
        if len(cols) == 4 and all(fits(page(cols[i:i + 2])) for i in (0, 2)): pages[-2:] = [cols[:2], cols[2:]]
    elif len(tail) > 1:  # otherwise the last page's own two columns are evened out
        cut = partition(hs(tail), [1, 1])[0]
        if fits(page([tail[:cut], tail[cut:]])): pages[-1] = [tail[:cut], tail[cut:]]
    out = [page(c) for c in pages]
    for n, p in enumerate(out, 1): p['page_of'] = [n, len(out)]
    return out

@pattern('criteria', scene='临床试验', title='入选与排除标准（原文密排）', density='高',
         use='方案的入选、排除标准原文：编号、阈值、时间窗、例外原样保留；一页放不下按编号接着排到下一页', split=_criteria_split)
def criteria(d):
    role = d.get('role', 'body'); meta = {k: (d.get(tk, title), icon, tone) for k, tk, title, icon, tone in _CRIT}
    def card(key, items, start):
        title, icon, tone = meta[key]
        return Card([Items(items, marker='number', start=start, role=role, tone=tone)], title=title, icon=icon, justify='start', gap=12)
    if d.get('layout') == 'flow':
        body = Row([Stack([card(s['key'], s['items'], s['start']) for s in col], justify='fill', gap=L['gap'], flex=1) if col else Stack([])
                    for col in d['cols']] + [Stack([])] * (2 - len(d['cols'])), flex=1)
    else:
        present = [k for k in meta if d.get(k)]
        body = Row([card(k, d[k], d.get('start', {}).get(k, 1)) for k in present],
                   weights=(d.get('weights') or [1, 1]) if len(present) == 2 else [1], flex=1)
    return Stack([body] + ([Text(d['note'], 'label')] if d.get('note') else []), justify='fill', gap=12)

# ---------------------------------------------------------------- 访视流程表 SoA（按访视列分页）
def _soa_split(d, fits):
    """Visit columns are paged first (each page repeats the item column and the footnotes), then rows when a page is
    still too tall. Columns split evenly: 18 visits at 15 per page become 9 + 9, not 15 + 3."""
    from ..paginate import split_rows
    n = len(d['visits'])
    if not n: raise ValueError('SoA 缺少访视（visits 为空）')
    cap = d.get('per_page') or max(4, int((1168 - d.get('item_px', 250)) // d.get('min_col', 60)))
    pages = -(-n // cap); per = -(-n // pages); out = []
    for a in range(0, n, per):
        chunk = split_rows({**d, 'cols': [a, min(n, a + per)]}, fits)
        for i in range(len(chunk) - 1):  # a section heading never ends a page: it moves down to the rows it heads
            while chunk[i]['rows'] and 'section' in chunk[i]['rows'][-1] and len(chunk[i]['rows']) > 1:
                moved = {**chunk[i + 1], 'rows': [chunk[i]['rows'][-1]] + chunk[i + 1]['rows'], 'row_start': chunk[i + 1]['row_start'] - 1}
                if not fits(moved): break
                chunk[i] = {**chunk[i], 'rows': chunk[i]['rows'][:-1]}; chunk[i + 1] = moved
        out += chunk
    for k, p in enumerate(out, 1): p['page_of'] = [k, len(out)]
    return out

def soa_table(d):
    a, b = d.get('cols', [0, len(d['visits'])]); vis = d['visits'][a:b]; k = len(vis)
    groups = [{'text': ''}]
    for v in vis:
        if groups[-1].get('text') == v.get('period') and len(groups) > 1: groups[-1]['span'] += 1
        else: groups.append({'text': v.get('period', ''), 'span': 1})
    cols = ['评估项目'] + [f"{v['v']} {v['week']}" for v in vis]
    def cell(x):
        if x in (1, True, '●'): return {'mark': 'dot'}
        return {'text': '' if x in (0, None, False) else str(x)}
    rows = []
    for r in d['rows']:
        if 'section' in r: rows.append([{'text': r['section'], 'span': k + 1, 'tone': 'tint', 'bold': True}])
        else: rows.append([r['item']] + [cell(x) for x in r['at'][a:b]])
    item_w = d.get('item_px', 250); vis_w = (1168 - item_w) / max(1, k)
    return {'groups': groups, 'columns': cols, 'rows': rows, 'widths': [item_w / vis_w] + [1] * k, 'center': list(range(1, k + 1))}

@pattern('soa', scene='临床试验', title='访视流程表 SoA（圆点矩阵 · 按访视分页 · 脚注）', density='高', split=_soa_split,
         use='评估项目 × 访视的圆点矩阵，按分期分组表头；访视多时按列分页，每页重复项目列与脚注；rows=[{section}|{item, at=[1/0/文字]}]')
def soa(d):
    parts = [Figure('table', soa_table(d), flex=1)]
    if d.get('footnotes'):
        fn = d['footnotes']; half = (len(fn) + 1) // 2
        parts.append(Row([Stack([Text(t, 'label') for t in fn[:half]], gap=8, justify='start'),
                          Stack([Text(t, 'label') for t in fn[half:]], gap=8, justify='start')], gap=24))  # 8: text frames carry 0.2·size padding
    return Stack(parts, justify='fill', gap=10)

# ---------------------------------------------------------------- 森林图 + 解读
def _close(body, d, gap=14):
    from ..tree import Band
    tail = ([Band(d['band'])] if d.get('band') else []) + ([Text(d['note'], 'label')] if d.get('note') else [])
    return Stack([body] + tail, justify='fill', gap=gap)

def _insights(d, key='insights'):
    return [Card([IconLead(i.get('icon', 'bulb'), Stack([Text(i['title'], 'item_title')] + ([Text(i['text'], 'secondary')] if i.get('text') else []), gap=4, justify='start'), size=32,
                           tone=i.get('tone', 'focus'))], justify='center', pad=[18, 12], flex=1) for i in d.get(key, [])]

@pattern('forest', scene='临床试验', title='亚组森林图 + 解读', density='高',
         use='亚组 HR/OR/差值及 95% CI（对数轴、参考线、倾向方向），右侧 2–3 条解读；PPTX 原生形状，HTML 用 ECharts')
def forest(d):
    fig = Card([Figure('forest', d['forest'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d)
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [2.2, 1]), gap=18, flex=1) if side else fig, d)

@pattern('km', scene='临床试验', title='生存曲线 KM + 风险人数 + 关键指标', density='高',
         use='两到三组 Kaplan–Meier 阶梯曲线（删失刻度、风险人数表与时间轴对齐），右侧中位时间、HR 等指标与解读')
def km(d):
    from ..tree import KpiTile
    fig = Card([Figure('km', d['km'], min_h=320, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = [KpiTile(k['value'], k['label'], k.get('tone', 'brand')) for k in d.get('kpis', [])] + _insights(d)
    for c in side: c.flex = 1
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [2.3, 1]), gap=18, flex=1) if side else fig, d)

@pattern('consort', scene='临床试验', title='受试者流程 CONSORT + 说明', density='中高',
         use='筛选、排除（原因分列）、随机、各组分配、脱落（原因）、分析集；右侧 2–3 张说明卡')
def consort(d):
    fig = Card([Figure('consort', d['consort'], min_h=0, flex=1)], justify='center', pad=[20, 14], flex=1)
    side = _insights(d, 'notes')
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [2.3, 1]), gap=18, flex=1) if side else fig, d)
