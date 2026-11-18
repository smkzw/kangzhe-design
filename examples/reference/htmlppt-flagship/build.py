#!/usr/bin/env python3
"""Derive the flagship F1 reference deck (14, 8.0) from the html-ppt-skill scaffold (scaffold.html = raw new-deck.sh output).

Same synthetic brief and numbers as ../htmlppt and ../pptx-default (research-material completeness check), so the two
routes compare page by page. Kept from upstream: <body>/.deck/.slide, base.css and runtime.js (vendored, byte-identical),
notes. Flagship layer: runtime/kz-flagship.{css,js} adds the header, logo, progress and footer, and turns the declared
data-kzf-fx / data-kzf-s marks into scene timelines (GSAP); the stages (`platforms`, `ghost`) come from the component
library in runtime/kz-flagship-stages.js (14 FLAG-06a).
Run:  python3 examples/reference/htmlppt-flagship/build.py
"""
from pathlib import Path
from html import escape
import json
HERE = Path(__file__).resolve().parent
RT, AS = '../../../runtime/', '../../../assets/'
LOGO = AS + 'logo_bot.svg'
DATE = '2026年11月'
TITLE = '研究资料完整性核对（合成示例）'

Q = lambda year, quarter: year * 4 + quarter - 1  # KZGantt.qindex
DATA = {
    'completeness': {'kind': 'column', 'unit': '份', 'decimals': 0, 'description': '合成示例：各资料组应收与已收份数',
                     'categories': ['方案与修订', '中心记录', '实验室数据', '安全性报告'],
                     'series': [{'id': 'due', 'name': '应收', 'values': [2, 12, 6, 4], 'role': 'comparator'},
                                {'id': 'received', 'name': '已收', 'values': [2, 9, 6, 3]}]},
    'gantt': {'min': Q(2026, 4), 'max': Q(2027, 3), 'tasks': [
        {'id': 'collect', 'label': '缺失资料补收', 'start': Q(2026, 4), 'end': Q(2027, 2), 'department': 'medical'},
        {'id': 'confirm', 'label': '版本差异确认', 'start': Q(2027, 1), 'end': Q(2027, 2), 'department': 'medical'},
        {'id': 'recheck', 'label': '完整性复核', 'start': Q(2027, 1), 'end': Q(2027, 3), 'department': 'statistics'},
        {'id': 'safety', 'label': '安全性报告核对', 'start': Q(2027, 1), 'end': Q(2027, 3), 'department': 'pv'},
        {'id': 'opinion', 'label': '审阅意见形成', 'start': Q(2027, 2), 'end': Q(2027, 3), 'department': 'medical'}]},
}
CHAPTERS = [('doc', '研究范围', '对象、时间窗与四组资料'), ('clipboard-check', '资料完整性', '应收与已收、缺口所在'),
            ('git-compare', '差异处理', '版本差异的判定与关闭'), ('calendar-stats', '核对计划', '补收、确认与复核排期')]

def fx(kind, s=0):
    return f' data-kzf-fx="{kind}"' + (f' data-kzf-s="{s}"' if s else '')

def slide(kind, title, inner, notes, **attrs):
    a = ''.join(f' data-kzf-{k}="{escape(str(v))}"' for k, v in attrs.items())
    return f'<section class="slide" data-kzf-kind="{kind}" data-title="{escape(title)}"{a}>{inner}<aside class="notes">{escape(notes)}</aside></section>'

def content(title, kicker, chips, body, notes, layout, style='', template=''):
    # template: 14 FLAG-08 layout id, carried to the page-plan (qc_plan BODY-03 rotation) and to QC as data-kzf-template
    # header tile icon (14 FLAG-06 H2): the chapter's icon unless the page names its own
    icon = CHAPTERS[int(kicker.split()[0]) - 1][0]
    return slide('content', title, f'<div class="kzf-body {layout}"{style}>{body}</div>', notes, icon=icon, kicker=kicker, chips='|'.join(chips), template=template)

def section(n, notes):
    icon, title, lede = CHAPTERS[n - 1]
    toc = ''.join(f'<li class="{"on" if i == n - 1 else ""}"{fx("right")}><b>{i + 1:02d}</b>{escape(t)}</li>' for i, (_, t, _) in enumerate(CHAPTERS))
    return slide('section', title,
                 f'<div class="kzf-sec-num"{fx("blur")}>{n:02d}</div>'
                 f'<div class="kzf-sec-text"><p{fx("left")}>第{"一二三四"[n - 1]}部分</p><h2{fx("left")}>{escape(title)}</h2><p{fx("left")}>{escape(lede)}</p></div>'
                 f'<ol class="kzf-sec-toc">{toc}</ol>', notes)

def kpi(v, unit, k, d, s=0, risk=False):
    return (f'<div class="kzf-kpi{" risk" if risk else ""}"{fx("right", s)}><div class="v"><span{fx("count", s)}>{v}</span><small>{unit}</small></div>'
            f'<div class="k">{k}</div><div class="d">{d}</div></div>')

# ---------- pages ----------
cover = slide('cover', '封面',
    '<picture class="kzf-cover-img"><source media="(min-aspect-ratio: 2/1)" srcset="' + AS + 'backgrounds/flagship/cover-wide.jpg">'
    f'<img src="{AS}backgrounds/flagship/cover.jpg" alt=""{fx("fade")}></picture><div class="kzf-sweep"{fx("sweep", 1)}></div>'
    '<div class="kzf-cover">'
    f'<p class="kzf-cover-kick"{fx("rise")}>医学部 · 管理层季度汇报</p>'
    f'<h1{fx("rise")}>研究资料<br>完整性核对</h1><div class="kzf-rule"{fx("grow-x")}></div>'
    f'<p class="kzf-cover-lede"{fx("rise")}>应收 24 份、已收 20 份；缺口集中在中心记录与安全性报告</p>'
    '<div class="kzf-chips">' + ''.join(f'<span class="kzf-chip"{fx("item")}><b>{i + 1:02d}</b>{t}</span>' for i, (_, t, _) in enumerate(CHAPTERS)) + '</div></div>'
    f'<p class="kzf-cover-meta"{fx("fade")}>产品中心-医学部 · {DATE}</p>',
    '今天汇报研究资料包的完整性核对：应收 24 份、已收 20 份，缺口在中心记录和安全性报告两组。')

toc = slide('toc', '目录',
    f'<div class="kzf-toc-head"><p{fx("rise")}>CONTENTS</p><h2{fx("rise")}>汇报章节</h2></div>'
    '<div class="kzf-toc" style="--n:4">' + ''.join(
        f'<div class="kzf-card"{fx("flip")}><div class="ic" data-icon="{ic}"></div><div class="n">{i + 1:02d}</div><h3>{t}</h3><p>{d}</p></div>'
        for i, (ic, t, d) in enumerate(CHAPTERS)) + '</div>',
    '汇报分四部分：核对范围、各组资料的到位情况、版本差异怎么处理、补收与复核的季度安排。')

scope = content('核对范围与资料分组', '01 研究范围', ['合成示例数据', '牵头：医学部'],
    '<article class="kzf-card"' + fx('card') + '><h3>研究对象与时间窗</h3>'
    f'<div class="kzf-pill"{fx("item")}>研究对象<em>成人受试者</em></div><div class="kzf-pill"{fx("item")}>筛选期<em>4 周</em></div>'
    f'<div class="kzf-pill"{fx("item")}>评价时间窗<em>第 16 周</em></div><div class="kzf-pill"{fx("item")}>参与中心<em class="num">12 家</em></div>'
    '<p class="kzf-note">范围外的资料<b>只作背景</b>，不进核对表</p></article>'
    '<article class="kzf-card"' + fx('card') + '><h3>纳入资料（4 组）</h3>'
    + ''.join(f'<div class="kzf-pill"{fx("item")}>{a}<em class="num">{b} 份</em></div>' for a, b in [('方案与修订', 2), ('中心记录', 12), ('实验室数据', 6), ('安全性报告', 4)])
    + '<p class="kzf-note">应收合计 <span class="num">24</span> 份</p></article>'
    '<article class="kzf-card"' + fx('card') + '><h3>方案版本比对</h3>'
    + ''.join(f'<div class="kzf-row"{fx("item")}><div>{a}<small>{b}</small></div><span class="kzf-tag {c}"{fx("stamp", 1)}>{d}</span></div>'
              for a, b, c, d in [('版本号', 'V2.1 / V2.3', 'ok', '已登记'), ('入组标准', '两版一致', 'ok', '一致'), ('筛选窗口', '28 天 / 35 天', 'wait', '待确认'), ('终点时间点', '第 16 / 24 周', 'wait', '待确认')])
    + '<p class="kzf-note"><b class="kzf-risk">2 项</b>确认之前，先不做组间比较</p></article>'
    '<div class="kzf-band"' + fx('card', 2) + '><div class="kzf-seg lead"><strong>范围怎么用</strong><span>规则与档案同源</span></div>'
    + ''.join(f'<div class="kzf-seg"{fx("left", 2)}><span>{a}</span><strong>{b}</strong></div>' for a, b in
              [('写入核对规则', '对象与时间窗'), ('决定应收清单', '4 组 24 份'), ('标记版本差异', '2 项待确认'), ('转入统计', '空值随数据集传递')]) + '</div>',
    '核对对象是成人受试者，筛选期 4 周，评价时间窗是第 16 周。资料分 4 组共 24 份。方案有 V2.1 和 V2.3 两版，筛选窗口和终点时间点两处不同，确认之前先不做组间比较。',
    'kzf-cols kzf-rows2', ' style="--n:3"', template='flag-cols')

COLS = [
 ('2.1', '资料清单', ''.join(f'<div class="kzf-pill"{fx("item", 1)}>{a}<em class="num">{b}</em></div>' for a, b in [('方案与修订', 2), ('中心记录', 12), ('实验室数据', 6), ('安全性报告', 4)]), '应收合计 <span class="num">24</span> 份'),
 ('2.2', '上传识别', ''.join(f'<div class="kzf-check"{fx("item", 1)}><span>{t}</span><span{fx("tick", 2)}>✓</span></div>' for t in ['检验报告', '影像报告', '门诊病历', '知情同意书']), '上传即<b>脱敏归类</b>'),
 ('2.3', '逐项比对', ''.join(f'<div class="kzf-row"{fx("item", 1)}><div>{a}</div><span class="kzf-tag {c}"{fx("stamp", 2)}>{d}</span></div>'
                           for a, c, d in [('版本号', 'ok', 'V2.3 符合'), ('签署日期', 'ok', '已签署'), ('访视窗', 'wait', '偏差 2 天'), ('页码', 'risk', '缺第 4 页')]), '原文<b>定位到页</b>'),
 ('2.4', '差异判定', ''.join(f'<div class="kzf-row"{fx("item", 1)}><div>{a}</div><span class="kzf-tag {c}"{fx("stamp", 2)}>{b}</span></div>' for a, b, c in [('未收到', '空值', 'risk'), ('版本不符', '先确认', 'wait'), ('页码缺失', '补收', 'wait'), ('一致', '比较', 'ok')]), '空值<b>不按零</b>处理'),
 ('2.5', '补收跟进', '<ol class="kzf-steps">' + ''.join(f'<li{fx("item", 1)}><i>{i + 1}</i>{t}</li>' for i, t in enumerate(['医学经理确认', 'CRA 联系中心', '中心补传', '重新比对'])) + '</ol>', '补收后<b>自动重新比对</b>'),
 ('2.6', '复核签署', ''.join(f'<div class="kzf-check"{fx("item", 1)}><span>{t}</span><span{fx("tick", 2)}>✓</span></div>' for t in ['资料清单', '版本差异', '缺口处理', '签署人与日期']), '签署前<b>再核关键条目</b>'),
]
LEDE = {'2.1': '按方案版本列出四组应收资料', '2.2': '中心上传后自动识别资料类型', '2.3': '对照方案逐项核对四个要素',
        '2.4': '四类结果按同一规则处理', '2.5': '缺口由医学经理牵头补收', '2.6': '四项复核全部通过后签署'}
flow = content('资料核对六步', '02 资料完整性', ['合成示例数据', '牵头：医学部 · 临床运营'],
    ''.join(f'<div class="kzf-hd"{fx("drop")}><b>{n}</b>{t}</div>' for n, t, _, _ in COLS)
    + ''.join(f'<article class="kzf-card"{fx("card", 1)}><p class="kzf-lede">{LEDE[n]}</p>{body}<p class="kzf-note">{note}</p></article>' for n, _, body, note in COLS)
    + '<div class="kzf-band"' + fx('card', 3) + '><div class="kzf-seg lead"><strong>模块衔接</strong><span>规则 · 档案同源</span></div>'
    + ''.join(f'<div class="kzf-seg"{fx("left", 3)}><span>{a}</span><strong>{b}</strong></div>' for a, b in
              [('取自研究规则库', '核对要点与规则一致'), ('写入资料档案', '结论与缺口原因'), ('转入统计分析', '空值标记随数据集'), ('转入安全性复核', '安全性报告补收进度')]) + '</div>',
    '核对分六步：先列应收清单，资料上传后统一识别分类，逐项比对版本、日期、访视窗和页码，按同一规则判定差异，缺的资料补收后重新比对，最后复核签署。每一步的结论都写回资料档案，统计和安全性复核直接取用。',
    'kzf-flow', template='flag-flow')

platforms = content('四组资料到位全景', '02 资料完整性', ['每块 = 1 份资料', '虚框 = 缺口'],
    '<div class="kzf-stage" data-kzf-comp="platforms" data-kzf-steps="rise,fill,miss,orbit" data-kzf-data=\''
    + json.dumps({'groups': [{'name': '方案与修订', 'due': 2, 'got': 2}, {'name': '中心记录', 'due': 12, 'got': 9}, {'name': '实验室数据', 'due': 6, 'got': 6}, {'name': '安全性报告', 'due': 4, 'got': 3}]}, ensure_ascii=False)
    + '\' role="img" aria-label="四组资料：方案与修订 2 份全到，中心记录 12 份到 9 份，实验室数据 6 份全到，安全性报告 4 份到 3 份"><canvas></canvas></div>'
    '<div class="kzf-kpis">' + kpi('24', '份', '应收资料', '四组合计', 2) + kpi('20', '份', '已收资料', '方案与实验室已齐', 2) + kpi('4', '份', '资料缺口', '中心记录 3 · 安全性 1', 2, risk=True) + '</div>',
    '每一块是一份资料，虚框是还没收到的。方案与修订、实验室数据已经齐了；中心记录缺 3 份，安全性报告缺 1 份，合计缺 4 份。',
    'kzf-split', template='flag-stage')

gaps = content('各资料组应收与已收', '02 资料完整性', ['合成示例数据', '单位：份'],
    '<article class="kzf-card kzf-chart-card"' + fx('card') + '><div class="kzf-card-head"><h3>应收与已收</h3><span>缺口 = 应收 − 已收</span></div>'
    '<div class="kz-chart" data-kz-chart="completeness"' + fx('chart', 1) + ' role="img" aria-label="应收与已收：方案与修订 2 与 2，中心记录 12 与 9，实验室数据 6 与 6，安全性报告 4 与 3"></div></article>'
    '<div class="kzf-stack">' + kpi('4', '份', '资料缺口', '中心记录 3 · 安全性报告 1', 2, risk=True) +
    '<article class="kzf-card"' + fx('right', 2) + '><h3>补收清单</h3>'
    + ''.join(f'<div class="kzf-row"{fx("item", 2)}><div><b>{a}</b> {b}</div><span class="kzf-tag {c}">{d}</span></div>' for a, b, c, d in
              [('C-03', '中心 A · 访视后未上传', 'wait', '补收中'), ('C-07', '中心 B · 扫描件缺页', 'wait', '补收中'), ('C-11', '中心 B · 是否存在待确认', 'risk', '待确认'), ('S-02', 'PV · 安全性报告', 'wait', '补收中')])
    + '<p class="kzf-note">缺的记录<b>保留为空值</b>，不按零处理，也不插补</p></article></div>',
    '方案与修订、实验室数据已经收齐，缺口在两组：中心记录缺 3 份，安全性报告缺 1 份。缺的记录留空，不按零处理，也不插补，后面比较时缺口一直看得见。',
    'kzf-split', ' style="--side:360"', template='flag-chart')

# phrase breaks are authored (<br>): CJK wraps anywhere, so a narrow node otherwise splits a word (03 TYPE-04)
NODES = [('发现差异', '比对时标出<br>版本、日期、页码不符'), ('定位原文', '每条差异<br>回到原文的页与行'), ('医学判定', '按同一规则<br>判定是否影响比较'),
         ('补收或说明', '缺失的补收<br>不可补的写明原因'), ('复核关闭', '复核后关闭<br>结论写入资料档案')]
cycle = content('差异处理闭环', '03 差异处理', ['5 个环节', '平均 6.5 天关闭'],
    '<div class="kzf-cycle" data-kzf-arc-s="2" data-kzf-pulse-s="3">'
    + kpi('38', '条', '本季度差异', '已关闭 31 · 进行中 7').replace('data-kzf-fx="right"', 'data-kzf-fx="pop"')
    + ''.join(f'<div class="kzf-node"{fx("pop", 1)}><h4><i>{i + 1}</i>{a}</h4><p>{b}</p></div>' for i, (a, b) in enumerate(NODES))
    + '</div>',
    '本季度登记差异 38 条，已关闭 31 条，7 条在处理。每条差异走同一个闭环：发现、定位原文、医学判定、补收或写明原因、复核关闭，平均 6.5 天关闭。',
    '', template='flag-cycle')

change = content('两个季度的差异处理', '03 差异处理', ['2026Q2 → 2026Q4', '合成示例数据'],
    '<div class="kzf-stage" data-kzf-comp="ghost" data-kzf-steps="before,after,delta,orbit" data-kzf-data=\''
    + json.dumps({'unit': '', 'from': '2026Q2', 'to': '2026Q4', 'items': [
        {'name': '登记差异（条）', 'before': 26, 'after': 38, 'good': 'up'}, {'name': '已关闭（条）', 'before': 15, 'after': 31, 'good': 'up'},
        {'name': '在处理（条）', 'before': 11, 'after': 7, 'good': 'down'}, {'name': '平均关闭天数', 'before': 9.2, 'after': 6.5, 'good': 'down', 'decimals': 1}]}, ensure_ascii=False)
    + '\' role="img" aria-label="2026Q2 到 2026Q4：登记差异 26 到 38 条，已关闭 15 到 31 条，在处理 11 到 7 条，平均关闭天数 9.2 到 6.5 天"><canvas></canvas></div>'
    '<div class="kzf-stack">' + kpi('82', '%', '关闭率', '2026Q4：31 / 38 条', 3)
    + '<article class="kzf-card"' + fx('right', 3) + '><h3>变化从哪里来</h3>'
    + ''.join(f'<div class="kzf-row"{fx("item", 3)}><div>{a}<small>{b}</small></div><span class="kzf-tag {c}">{d}</span></div>' for a, b, c, d in
              [('<b>原文定位到页</b>', '判定前不再来回查找', 'ok', '提速'), ('统一判定规则', '同类差异一次判完', 'ok', '提速'), ('版本差异 2 项', '等医学部确认', 'wait', '在处理')])
    + '<p class="kzf-note">登记变多是比对更细，<b>关闭天数</b>在下降</p></article></div>',
    '两个季度比，登记的差异从 26 条增加到 38 条，这是比对做得更细；已关闭从 15 条到 31 条，在处理的从 11 条降到 7 条，平均关闭天数从 9.2 天降到 6.5 天。',
    'kzf-split', ' style="--side:340"', template='flag-stage')

plan = content('核对计划', '04 核对计划', ['医学部 · 数统 · PV', '2026Q4 – 2027Q2'],
    '<article class="kzf-card kzf-chart-card"' + fx('card') + '><div class="kzf-card-head"><h3>季度安排</h3><span>区间 [起, 止)</span></div>'
    '<div data-kz-gantt="gantt"' + fx('gantt', 1) + ' style="flex:1;min-height:0"></div></article>'
    '<div class="kzf-stack">' + kpi('2027Q1', '', '关键节点', '缺失资料补收与版本差异确认完成', 2).replace('data-kzf-fx="count"', 'data-kzf-fx="fade"')
    + '<article class="kzf-card"' + fx('right', 2) + '><h3>里程碑</h3>'
    + ''.join(f'<div class="kzf-row"{fx("item", 2)}><div>{a}<small>{b}</small></div><span class="kzf-tag info">{q}</span></div>' for q, a, b in
              [('2027Q1', '<b>4 份补收</b> · 2 项版本确认', '医学部'), ('2027Q2', '完整性复核', '数统'), ('2027Q2', '安全性报告核对', 'PV'), ('2027Q3 初', '形成审阅意见', '医学部')])
    + '</article></div>',
    '关键节点是 2027 年一季度：缺的 4 份由医学部补收，两版方案的差异也在一季度确认。数统复核和 PV 核对做到二季度，三季度初形成审阅意见。',
    'kzf-split', ' style="--side:330"', template='flag-gantt')

ending = slide('ending', '结束',
    f'<div class="kzf-end"><h2{fx("blur")}>谢谢</h2><div class="kzf-rule"{fx("grow-x")}></div><p{fx("rise")}>{escape(TITLE)}</p></div>'
    f'<p class="kzf-end-meta"{fx("fade")}>产品中心-医学部 · {DATE}</p>', '谢谢大家。')

slides = [cover, toc, section(1, '第一部分，先说核对范围。'), scope, section(2, '第二部分，资料完整性。'), flow, platforms, gaps,
          section(3, '第三部分，版本差异怎么处理。'), cycle, change, section(4, '第四部分，核对计划。'), plan, ending]

src = (HERE / 'scaffold.html').read_text(encoding='utf-8')
assert '<div class="deck">' in src and 'assets/runtime.js' in src, 'scaffold structure changed upstream; re-read new-deck.sh output'
head = ('<!DOCTYPE html>\n<!-- Derived from html-ppt-skill new-deck.sh output (scaffold.html) by build.py; do not edit by hand. -->\n'
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{escape(TITLE)} · 康哲医学部 · 旗舰</title>\n<link rel="icon" href="data:,">\n'
        '<link rel="stylesheet" href="vendor/html-ppt/assets/base.css">\n'
        f'<link rel="stylesheet" href="{RT}kz-tokens.css">\n<link rel="stylesheet" href="{RT}kz-glass.css">\n<link rel="stylesheet" href="{RT}kz-flagship.css">\n'
        '<link rel="stylesheet" href="deck.css">\n</head>\n')
VENDOR = ['echarts.min.js', 'gsap.min.js', 'DrawSVGPlugin.min.js', 'MotionPathPlugin.min.js', 'CustomEase.min.js', 'three.bundle.min.js']
body_html = (f'<body class="kz kzf" data-fit="fluid" data-kzf-title="{escape(TITLE)}">\n<div class="deck">\n' + '\n'.join(slides) + '\n</div>\n'
             '<script src="vendor/html-ppt/assets/runtime.js"></script>\n'
             + ''.join(f'<script src="{AS}vendor/{m}"></script>\n' for m in VENDOR)
             + ''.join(f'<script src="{RT}{m}"></script>\n' for m in ['kz-tokens.js', 'kz-icons.js', 'kz-charts.js', 'kz-gantt.js', 'kz-clinical.js', 'kz-gantt-studio.js', 'kz-explore.js', 'kz-flagship.js', 'kz-flagship-stages.js'])
             + '<script src="../../../adapters/html-ppt-bridge.js"></script>\n'
             + f'<script>window.KZ_DECK_DATA = {json.dumps(DATA, ensure_ascii=False)};window.KZ_LOGO = {json.dumps(LOGO)};</script>\n<script src="deck.js"></script>\n'
             + f'<script src="{RT}kz-audience.js"></script>\n</body></html>\n')
(HERE / 'index.html').write_text(head + body_html, encoding='utf-8')
print('wrote', HERE / 'index.html', len(slides), 'slides')

# ---------- page-plan (14 FLAG-11 G2: tools/qc_plan.py runs on it) ----------
from html.parser import HTMLParser
TOK = json.loads((HERE.parents[2] / 'tokens/tokens.json').read_text(encoding='utf-8'))
FT = TOK['flagship']['type_px']
ROLE_PX = {'page_title': FT['page_title'], 'card_title': FT['card_title'], 'body': FT['body'], 'footer': FT['foot'], 'cover_title': FT['cover_title'],
           'hero_subtitle': FT['cover_lede'], 'hero_meta': FT['cover_meta'], 'toc_title': FT['toc_title'], 'toc_number': FT['toc_numeral'],
           'toc_label': FT['toc_card_title'], 'toc_description': FT['toc_card_desc'], 'section_number': FT['section_numeral'],
           'section_title': FT['section_title'], 'ending_title': FT['ending_title']}

class Page(HTMLParser):
    """Collects text roles, cards and their entrance fx from one slide's HTML."""
    CARD = ('kzf-card', 'kzf-kpi', 'kzf-node', 'kzf-band')
    def __init__(self, kind):
        super().__init__(); self.kind, self.stack, self.texts, self.cards = kind, [], [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = (a.get('class') or '').split()
        self.stack.append((tag, cls))
        if tag in ('article', 'div') and any(c in cls for c in self.CARD) and 'kzf-cycle' not in cls:
            self.cards.append({'cls': next(c for c in self.CARD if c in cls), 'fx': a.get('data-kzf-fx', 'fade'), 's': a.get('data-kzf-s', '0')})
        if tag == 'aside': self.stack[-1] = (tag, ['notes'])
    def handle_endtag(self, tag):
        while self.stack:
            if self.stack.pop()[0] == tag: break
    def handle_data(self, data):
        t = data.strip()
        if not t or any('notes' in c for _, c in self.stack): return
        tags = [x for x, _ in self.stack]; classes = {c for _, cs in self.stack for c in cs}
        k = self.kind
        if k == 'cover': role = 'cover_title' if 'h1' in tags else 'hero_subtitle' if 'kzf-cover-lede' in classes else 'hero_meta' if 'kzf-cover-meta' in classes else None
        elif k == 'toc': role = 'toc_title' if 'h2' in tags else 'toc_number' if 'n' in classes else 'toc_label' if 'h3' in tags else 'toc_description' if 'kzf-toc' in classes and 'p' in tags else None
        elif k == 'section': role = 'section_number' if 'kzf-sec-num' in classes else 'section_title' if 'h2' in tags else None
        elif k == 'ending': role = 'ending_title' if 'h2' in tags else None
        else: role = 'card_title' if 'h3' in tags else 'body'
        if role: self.texts.append((role, t))

def plan_page(i, html):
    import re
    kind = re.search(r'data-kzf-kind="(\w+)"', html).group(1); title = re.search(r'data-title="([^"]*)"', html).group(1)
    tpl = re.search(r'data-kzf-template="([^"]*)"', html)
    pp = Page(kind); pp.feed(html)
    pid = f's{i + 1:02d}'; els, seen = [], {}
    if kind == 'content': els.append({'id': f'{pid}-page_title', 'role': 'page_title', 'font_px': ROLE_PX['page_title'], 'line_height': 1.25, 'text': title})
    for role, t in pp.texts:
        n = seen[role] = seen.get(role, -1) + 1
        if role == 'body' and n >= 6: continue  # a sample of body runs is enough for type checks
        els.append({'id': f'{pid}-{role}-{n}', 'role': role, 'font_px': ROLE_PX[role], 'line_height': 1.25 if role != 'body' else 1.5, 'text': t})
    if kind in ('toc', 'section', 'content'): els.append({'id': f'{pid}-footer', 'role': 'footer', 'font_px': ROLE_PX['footer'], 'line_height': 1.4})
    cards = [{'id': f'{pid}-c{k + 1}', 'material': 'flagship_paper', 'edge_decoration': 'none', 'layout_mode': 'distributed',
              'detail': 'not_needed', 'detail_reason': '合成示例页，卡内已给全量信息'} for k, _ in enumerate(pp.cards)]
    motion = [{'id': c['id'], 'role': pc['cls'], 'enter': f'{pc["fx"]}@s{pc["s"]}', 'exit': 'page', 'hover': 'spot' if pc['cls'] != 'kzf-band' else 'none', 'ambient': 'none'}
              for c, pc in zip(cards, pp.cards)]
    # hero pages without cards: the title block is the motion object
    motion = motion or [{'id': f'{pid}-title', 'role': 'title', 'enter': 'blur@s0' if kind in ('section', 'ending') else 'rise@s0', 'exit': 'page', 'hover': 'none', 'ambient': 'none'}]
    page = {'id': pid, 'kind': 'body' if kind == 'content' else kind, 'title': title, 'body_profile': 'standard', 'elements': els,
            'protected_regions': [], 'cards': cards, 'motion_objects': motion,
            'image': {'mode': 'flagship_set', 'asset_id': 'flagship-cover' if kind == 'cover' else 'flagship-canvas'},
            'sources': [{'id': 'brief', 'kind': 'internal', 'visible': False}]}
    if kind in ('cover', 'toc', 'section', 'ending'): page['hero_layout_id'] = f'flagship-{kind}'
    if tpl and tpl.group(1): page['template'] = tpl.group(1)
    comp = re.search(r'data-kzf-comp="([^"]+)"', html)
    if comp:  # 14 FLAG-06a: the stage component and its content job, for qc_plan FLAG-STAGE*
        job = re.search(r'data-kzf-job="([^"]+)"', html)
        page['stage'] = {'component': comp.group(1), 'job': job.group(1) if job else TOK['flagship']['stages']['catalog'][comp.group(1)]['job'][0]}
    return page

plan = {'schema_version': '6.1', 'contract_revision': '7.0', 'track': 'htmlppt', 'route': 'flagship', 'canvas': [1280, 720],
        'target_viewports': TOK['viewports']['htmlppt'], 'pages': [plan_page(i, h) for i, h in enumerate(slides)]}
(HERE / 'page-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('wrote', HERE / 'page-plan.json')
