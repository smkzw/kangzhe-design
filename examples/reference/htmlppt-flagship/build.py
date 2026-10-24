#!/usr/bin/env python3
"""Derive the flagship reference deck (14) from the html-ppt-skill scaffold (scaffold.html = raw new-deck.sh output).

Same synthetic brief and data as ../htmlppt and ../pptx-default, so the two routes can be compared page by page.
Kept from upstream: the <body>/.deck/.slide structure, base.css and runtime.js (vendored, byte-identical), notes.
Flagship layer: runtime/kz-flagship.{css,js} draws the light field, lenses and the identity capsule; pages declare
data-kzf-kind / data-kzf-focus, reading areas data-kzf-calm, the one focal lens data-kzf-pool.
Run:  python3 examples/reference/htmlppt-flagship/build.py
"""
from pathlib import Path
from html import escape
import json
HERE = Path(__file__).resolve().parent
RT = '../../../runtime/'
LOGO = '../../../assets/logo_bot.svg'
DATE = '2026年10月'

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

def slide(kind, title, focus, inner, notes, light=None):
    attrs = f' data-kzf-kind="{kind}" data-kzf-focus="{focus}" data-title="{escape(title)}"' + (f' data-kzf-light="{light}"' if light else '')
    return f'<section class="slide kzf-page kzf-page-{kind}"{attrs}>{inner}<aside class="notes">{escape(notes)}</aside></section>'

def section(n, title, lede, notes):
    return slide('section', title, '0.25,0.48',
                 f'<div class="kzf-section-num kzf-numeral" data-kzf-in="0">{n}</div>'
                 f'<div class="kzf-section-lens kzf-glass kzf-lens" data-kzf-lens="section" data-kzf-in="1"></div>'
                 f'<div class="kzf-section-text"><p class="kzf-kicker" data-kzf-in="2">第{"一二三"[int(n) - 1]}部分</p>'
                 f'<h2 data-kzf-in="3">{escape(title)}</h2><p class="kzf-lede" data-kzf-in="4">{escape(lede)}</p></div>', notes, light=240)

def content(title_html, title, body, notes, focus='0.80,0.40'):
    return slide('content', title, focus,
                 f'<div class="kzf-title" data-kzf-in="0" data-kzf-calm><h2>{title_html}</h2><div class="kzf-rule"></div></div>{body}', notes, light=170)

def lens_kpi(value, unit, label, cls='kzf-kpi'):
    return (f'<div class="{cls} kzf-glass kzf-lens" data-kzf-lens="kpi" data-kzf-pool data-kzf-in="2"><div>'
            f'<p class="kzf-kpi-num kzf-numeral">{escape(value)}<small>{escape(unit)}</small></p><p class="kzf-kpi-label">{escape(label)}</p></div></div>')

def note(title, html):
    return f'<div class="kzf-note" data-kzf-in="3" data-kzf-calm><h3>{escape(title)}</h3><p>{html}</p></div>'

def legend(depts):
    return '<span class="kzf-legend">' + ''.join(f'<span><i style="background:var(--kz-{d})"></i>{n}</span>' for d, n in depts) + '</span>'

slides = [
    slide('cover', '封面', '0.72,0.74',
          '<div class="kzf-cover-text"><p class="kzf-kicker" data-kzf-in>管理层季度汇报 · 合成示例</p>'
          '<h1 data-kzf-in>研究资料<br>完整性核对</h1><p class="kzf-lede" data-kzf-in>应收 24 份，已收 20 份；<b>缺口集中在两组资料</b></p></div>'
          '<div class="kzf-cover-bar kzf-glass kzf-lens" data-kzf-lens="bar" data-kzf-in="3">'
          '<div><span class="kzf-numeral">24</span><span>应收（份）</span></div><div><span class="kzf-numeral">20</span><span>已收（份）</span></div>'
          '<div><span class="kzf-numeral kzf-risk-num">4</span><span>缺口（份）</span></div></div>'
          f'<p class="kzf-cover-meta" data-kzf-in="4">{DATE}　管理层季度汇报</p>',
          '今天汇报一个研究资料包的完整性核对，数据是合成的。按计划应收 24 份，目前收到 20 份，还缺 4 份。希望会上把补收和确认的安排定下来。', light=205),
    slide('toc', '目录', '0.62,0.70',
          '<div class="kzf-toc-head"><p class="kzf-kicker" data-kzf-in="0">汇报章节</p><h2 data-kzf-in="0">三个问题，一个决定</h2></div>'
          '<div class="kzf-toc">'
          + ''.join(f'<div class="kzf-toc-card kzf-glass kzf-lens" data-kzf-lens="ask" data-kzf-in="{i + 1}"><span class="kzf-numeral">{n}</span><b>{t}</b><span>{d}</span></div>'
                    for i, (n, t, d) in enumerate([('01', '研究范围', '对象、时间窗与资料组'), ('02', '资料完整性', '应收与已收、缺口所在'), ('03', '核对计划', '补收、确认与复核')]))
          + '</div>',
          '分三部分：先说这次核对的范围，再看各组资料收齐了多少，最后是补收、确认和复核的季度安排。', light=215),
    section('01', '研究范围', '范围定下来，才知道哪些资料要进核对', '先看范围。范围定下来，才知道哪些资料要进核对。'),
    content('研究范围', '研究范围',
            '<div class="kzf-cards">'
            '<article class="kzf-paper kzf-card" data-kzf-in="1" data-kzf-calm><h3>研究对象与时间窗</h3>'
            '<p class="kzf-figure"><b>成人受试者</b><span>研究对象</span></p><p class="kzf-figure"><b>第 16 周</b><span>评价时间窗</span></p></article>'
            '<article class="kzf-paper kzf-card" data-kzf-in="2" data-kzf-calm><h3>纳入资料</h3><p class="kzf-figure"><b>4 组</b><span>纳入核对</span></p>'
            '<ul class="kzf-cols-2"><li>方案与修订</li><li>中心记录</li><li>实验室数据</li><li>安全性报告</li></ul></article></div>'
            + lens_kpi('2', '项', '待确认的方案差异')
            + note('方案 V2.1 与 V2.3', '差异在筛选窗口与终点评价时间点<br><b>确认之后，再做组间比较</b>'),
            '核对对象是成人受试者，评价时间窗是第 16 周。资料分 4 组：方案与修订、中心记录、实验室数据、安全性报告。方案有 V2.1 和 V2.3 两版，并排比下来有 2 处要确认：筛选窗口和终点评价时间点。这 2 项会影响后面的组间比较，所以确认之前先不比。'),
    section('02', '资料完整性', '缺口在哪里，会不会影响组间比较', '接下来看各组资料收齐了多少。'),
    content('缺口集中在<span class="kzf-risk">中心记录</span>与<span class="kzf-risk">安全性报告</span>', '资料完整性',
            '<article class="kzf-paper kzf-data" data-kzf-in="1" data-kzf-calm><div class="kzf-data-head"><h3>各资料组应收与已收</h3><span>合成示例数据｜单位：份</span></div>'
            '<div class="kz-chart kzf-chart" data-kz-chart="completeness" role="img" aria-label="应收与已收：方案与修订 2 与 2，中心记录 12 与 9，实验室数据 6 与 6，安全性报告 4 与 3"></div></article>'
            + lens_kpi('4', '份', '资料缺口 · 应收 24 / 已收 20')
            + note('缺失处理', '缺失记录保留为空值<br><b>不按零处理，也不插补</b>'),
            '方案与修订、实验室数据已经收齐，缺口在两组：中心记录缺 3 份，安全性报告缺 1 份。缺的记录在数据里留空，不按零处理，也不插补，这样后面比较时缺口一直看得见。'),
    section('03', '核对计划', '补收、确认与复核排进季度', '最后是补收、确认和复核的时间表。'),
    content('核对计划', '核对计划',
            '<article class="kzf-paper kzf-plan" data-kzf-in="1" data-kzf-calm><div class="kzf-data-head"><h3>季度安排</h3>' + legend([('medical', '医学部'), ('statistics', '数统'), ('pv', 'PV')]) + '</div>'
            '<div data-kz-gantt="gantt"></div><p class="kzf-plan-note">补收与版本差异确认<b>在 2027Q1 内完成</b>，复核、安全性报告核对与审阅意见在 2027Q2 内完成</p></article>',
            '关键节点是 2027 年一季度。缺的 4 份由医学部从今年四季度开始补收，一季度内补齐；两版方案的差异也在一季度内确认。数统的完整性复核和 PV 的安全性报告核对从一季度做到二季度，二季度由医学部形成审阅意见。',
            focus='0.50,0.90'),
    slide('ending', '结束', '0.50,0.66',
          '<div class="kzf-ending-head"><p class="kzf-kicker" data-kzf-in="0">会议决定事项</p><h2 data-kzf-in="1">请确认两件事</h2></div>'
          '<div class="kzf-asks">'
          '<div class="kzf-ask kzf-glass kzf-lens" data-kzf-lens="ask" data-kzf-in="2"><span class="kzf-numeral">01</span><p>4 份资料由医学部牵头<br><b>2027Q1 内补收</b></p></div>'
          '<div class="kzf-ask kzf-glass kzf-lens" data-kzf-lens="ask" data-kzf-in="3"><span class="kzf-numeral">02</span><p>版本差异<b>确认之后</b><br>再做组间比较</p></div></div>'
          f'<p class="kzf-ending-meta" data-kzf-in="4">{DATE}　管理层季度汇报</p>',
          '最后请大家确认两件事：一是缺的 4 份资料由医学部牵头，2027 年一季度内补收；二是 2 项版本差异确认之后，再做组间比较。没有不同意见的话，就按这个时间表推进。', light=225),
]

src = (HERE / 'scaffold.html').read_text(encoding='utf-8')
assert '<div class="deck">' in src and 'assets/runtime.js' in src, 'scaffold structure changed upstream; re-read new-deck.sh output'
head = ('<!DOCTYPE html>\n<!-- Derived from html-ppt-skill new-deck.sh output (scaffold.html) by build.py; do not edit by hand. -->\n'
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>研究资料完整性核对 · 康哲医学部 · 旗舰</title>\n<link rel="icon" href="data:,">\n'
        '<link rel="stylesheet" href="vendor/html-ppt/assets/base.css">\n'
        f'<link rel="stylesheet" href="{RT}kz-tokens.css">\n<link rel="stylesheet" href="{RT}kz-glass.css">\n<link rel="stylesheet" href="{RT}kz-flagship.css">\n'
        '<link rel="stylesheet" href="deck.css">\n</head>\n')
body_html = ('<body class="kz kzf" data-fit="fluid">\n<div class="deck">\n' + '\n'.join(slides) + '\n</div>\n'
             '<script src="vendor/html-ppt/assets/runtime.js"></script>\n'
             + ''.join(f'<script src="{RT}{m}"></script>\n' for m in ['../assets/vendor/echarts.min.js', 'kz-tokens.js', 'kz-motion.js', 'kz-charts.js', 'kz-gantt.js', 'kz-flagship.js'])
             + '<script src="../../../adapters/html-ppt-bridge.js"></script>\n'
             + f'<script>window.KZ_DECK_DATA = {json.dumps(DATA, ensure_ascii=False)};window.KZ_LOGO = {json.dumps(LOGO)};</script>\n<script src="deck.js"></script>\n'
             + f'<script src="{RT}kz-audience.js"></script>\n</body></html>\n')
(HERE / 'index.html').write_text(head + body_html, encoding='utf-8')
print('wrote', HERE / 'index.html', len(slides), 'slides')
