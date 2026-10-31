#!/usr/bin/env python3
"""Derive the Kangzhe reference deck from the html-ppt-skill scaffold (scaffold.html = raw new-deck.sh output).

Kept from upstream: the <body>/.deck/.slide structure, base.css and runtime.js (vendored, byte-identical),
speaker notes in .notes. Replaced: theme links, remote web fonts, animations.css and data-themes (Kangzhe owns
the look; the A key then has no animation CSS to apply), and the demo slides. Hero pages come from
tools/hero_layout.html_fluid_fragment, the header mark from tools/brand_fragments.facets.
Run:  python examples/reference/htmlppt/build.py
The helpers (hero, body, card, demo_page, write_deck) are reused by examples/motion/deck/build.py.
"""
from pathlib import Path
from html import escape
import json, re, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from hero_layout import html_fluid_fragment  # noqa: E402
from brand_fragments import facets  # noqa: E402

RT = '../../../runtime/'
A = '../assets/'
LOGO = '../../../assets/logo_bot.svg'
FOOT = '产品中心-医学部｜2026年10月'

def hero(kind, content, image, notes):
    return (f'<section class="slide kz-hero" data-chrome="hero" data-title="{escape(content.get("title_short", ""))}">'
            + html_fluid_fragment(kind, content, A + image, LOGO)
            + f'<aside class="notes">{escape(notes)}</aside></section>')

def body(n, total, title, preset, inner, notes):
    mark = f'<svg class="kz-mark" viewBox="0 0 100 90" aria-hidden="true">{facets(prefix=f"kz{n}")}</svg>'
    return (f'<section class="slide kz-body-page" data-chrome="body" data-title="{escape(title)}">'
            # Only the quiet body background passes IMG-05; the available wide asset is a hero-style ribbon. A real
            # ultrawide quiet body asset is still missing (IMG-04 WARN in README) — cover-crop until it is generated.
            f'<img class="kz-bg" src="{A}body-quiet.webp" alt="">'
            f'<div class="kz-chrome">{mark}<div class="kz-rule"></div><img class="kz-logo" src="{LOGO}" alt="康哲药业">'
            f'<div class="kz-foot"><span>{FOOT}</span><span class="kz-page-number">{n} / {total}</span></div></div>'
            f'<h2 class="kz-body-title">{escape(title)}</h2>'
            f'<div class="kz-body" data-preset="{preset}">{inner}</div>'
            f'<aside class="notes">{escape(notes)}</aside></section>')

def card(title, items, figures=(), cols=1, tilt=True):
    # figures = [(value, label[, 'risk'])]: the numbers the card is about, set above its bullets.
    fig = ''.join(f'<p class="kz-figure{" is-risk" if len(f) > 2 else ""}"><b>{escape(f[0])}</b><span>{escape(f[1])}</span></p>' for f in figures)
    lis = ''.join(f'<li>{i}</li>' for i in items)
    cls = ' class="kz-cols-2"' if cols == 2 else ''
    ul = f'<ul{cls}>{lis}</ul>' if items else ''
    return f'<div data-kz-reveal><article class="kz-card"{" data-kz-tilt" if tilt else " data-kz-no-tilt"}><h3>{escape(title)}</h3>{fig}{ul}</article></div>'

# Same synthetic brief as ../pptx-default/source-brief.md, so both PPT tracks tell one story with one data set.
# Component data is emitted into index.html (window.KZ_DECK_DATA) from here; deck.js mounts it.
Q = lambda year, quarter: year * 4 + quarter - 1  # KZGantt.qindex
DATA = {
    'film': {
        'title': '核对流程',
        'states': [
            {'label': '界定范围', 'caption': '先定对象、时间窗和纳入的资料。', 'facts': ['研究对象：成人受试者', '评价时间窗：第 16 周', '纳入资料：4 组']},
            {'label': '清点资料', 'caption': '逐组登记应收与已收，缺失照原样保留。', 'facts': ['应收 24 份，已收 20 份', '中心记录缺 3 份，安全性报告缺 1 份', '缺失记录保留为空值']},
            {'label': '比较版本', 'caption': '两版方案并排比较，差异转交确认。', 'facts': ['方案版本：V2.1 与 V2.3', '待确认差异：2 项', '筛选窗口、终点评价时间点']},
            {'label': '排定计划', 'caption': '把补收与确认排进季度计划。', 'facts': ['补收：医学部，2027Q1 内完成', '版本差异确认：2027Q1', '复核与审阅意见：2027Q2']},
        ],
        # What each step leaves behind; the step bar names the action, so the two lists do not repeat each other.
        'nodes': [
            {'title': '研究范围', 'text': '成人受试者，第 16 周'},
            {'title': '资料清单', 'text': '4 组，缺 4 份'},
            {'title': '待确认差异', 'text': '2 项，转交确认'},
            {'title': '核对计划', 'text': '2026Q4 至 2027Q2'},
        ],
    },
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

def film_page(f):
    s = f['states'][0]
    facts = ''.join(f'<li>{escape(x)}</li>' for x in s['facts'])
    nodes = ''.join(f'<li class="kz-deck-node" data-kz-node><b>{escape(n["title"])}</b><span>{escape(n["text"])}</span></li>' for n in f['nodes'])
    steps = ''.join(f'<li class="kz-step" data-phase="{i}" data-state="{"current" if i == 0 else "todo"}"><span class="kz-step-mark">{i + 1}</span><b>{escape(x["label"])}</b></li>' for i, x in enumerate(f['states']))
    return ('<div class="kz-film kz-deck-film" data-kz-film><div class="kz-film-stage"><svg class="kz-film-links" aria-hidden="true"></svg>'
            f'<div class="kz-film-carrier"><strong class="kz-film-carrier-label">{escape(s["label"])}</strong><p class="kz-film-carrier-sub kz-film-caption">{escape(s["caption"])}</p><ul class="kz-carrier-facts">{facts}</ul></div>'
            f'<ul class="kz-deck-nodes" aria-label="各步产出">{nodes}</ul></div></div>'
            f'<ol class="kz-steps" aria-label="步骤">{steps}</ol>')

DEMOS = {
    # 15 DEMO: the same synthetic brief, shown as worked demonstrations; every number on stage is computed by
    # runtime/kz-demo.js from these inputs.
    'units': {'unit': '份', 'owner': '医学部', 'deadline': '2027Q1', 'note': '合成示例',
              'groups': [{'name': '方案与修订', 'due': 2, 'received': 2}, {'name': '中心记录', 'due': 12, 'received': 9},
                         {'name': '实验室数据', 'due': 6, 'received': 6}, {'name': '安全性报告', 'due': 4, 'received': 3}]},
    'decision': {'note': '合成示例', 'intro': '每份资料都按同一条路径判定',
                 'nodes': [{'id': 'in', 'label': '资料登记', 'x': .01, 'y': .42, 'w': .14, 'kind': 'in'},
                           {'id': 'got', 'label': '收到了吗？', 'x': .19, 'y': .42, 'w': .17},
                           {'id': 'miss', 'label': '保留空值·补收', 'x': .45, 'y': .12, 'w': .26, 'kind': 'out'},
                           {'id': 'conf', 'label': '差异已确认？', 'x': .45, 'y': .6, 'w': .2},
                           {'id': 'cmp', 'label': '进入组间比较', 'x': .77, 'y': .38, 'w': .22, 'kind': 'out'},
                           {'id': 'wait', 'label': '暂不比较', 'x': .77, 'y': .74, 'w': .22, 'kind': 'out'}],
                 'edges': [{'from': 'in', 'to': 'got'}, {'from': 'got', 'to': 'miss', 'label': '未收到'}, {'from': 'got', 'to': 'conf', 'label': '已收到'},
                           {'from': 'conf', 'to': 'cmp', 'label': '已确认'}, {'from': 'conf', 'to': 'wait', 'label': '未确认'}],
                 'cases': [{'id': 'a', 'label': '示例 A', 'detail': '已收，差异已确认', 'path': ['in', 'got', 'conf', 'cmp']},
                           {'id': 'b', 'label': '示例 B', 'detail': '中心记录缺失', 'path': ['in', 'got', 'miss']},
                           {'id': 'c', 'label': '示例 C', 'detail': '已收，差异待确认', 'path': ['in', 'got', 'conf', 'wait']}],
                 'summary': '缺失不按零处理；差异确认之前不做组间比较'},
}

def stage(kind, title, key=None):
    return f'<div data-kz-reveal><div class="kz-deck-demo" data-kz-demo-kind="{kind}" data-kz-demo-data="{key or kind}" role="img" aria-label="{escape(title)}的演示"></div></div>'

def demo_page(kind, title, items, figures=(), preset='demo', key=None):
    # Reading side complete and still; the stage beside it steps scene by scene (15 DEMO-05, 06 MOTION-09).
    # demo / demo-mirror: a reading card beside the stage; demo-wide: one lead line over a full-width stage;
    # demo-stack: the stage over the facts its form computed (KZDemo.renderFacts fills the strip).
    if preset == 'demo-wide':
        lead = f'<div data-kz-reveal><div class="kz-demo-lead"><b>{escape(title)}</b>' + ''.join(f'<span>{i}</span>' for i in items) + '</div></div>'
        return lead + stage(kind, title, key)
    if preset == 'demo-stack':
        return f'<div data-kz-reveal><div class="kz-demo-facts" data-kz-demo-facts aria-label="{escape(title)}"></div></div>' + stage(kind, title, key)
    return card(title, items, figures, tilt=False) + stage(kind, title, key)

def legend(depts):
    return '<span class="kz-legend">' + ''.join(f'<span><i style="background:var(--kz-{d})"></i>{n}</span>' for d, n in depts) + '</span>'

def write_deck(slides, data, out, title, base='', data_scripts=()):
    """Write a deck page from the scaffold. base: path from out's folder to this folder (shared vendor, deck.css,
    deck.js); data_scripts: extra scripts that define data before window.KZ_DECK_DATA is set."""
    src = (HERE / 'scaffold.html').read_text(encoding='utf-8')
    head = ('<!DOCTYPE html>\n<!-- Derived from html-ppt-skill new-deck.sh output (scaffold.html) by build.py; do not edit by hand. -->\n'
            '<html lang="zh-CN">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{escape(title)} · 康哲医学部</title>\n<link rel="icon" href="data:,">\n'
            f'<link rel="stylesheet" href="{base}vendor/html-ppt/assets/base.css">\n'
            f'<link rel="stylesheet" href="{RT}kz-tokens.css">\n<link rel="stylesheet" href="{RT}kz-glass.css">\n<link rel="stylesheet" href="{RT}kz-layouts.css">\n<link rel="stylesheet" href="{base}deck.css">\n</head>\n')
    assert '<div class="deck">' in src and 'assets/runtime.js' in src, 'scaffold structure changed upstream; re-read new-deck.sh output'
    body_html = ('<body class="kz" data-fit="fluid">\n<div class="deck">\n' + '\n'.join(slides) + '\n</div>\n'
                 f'<script src="{base}vendor/html-ppt/assets/runtime.js"></script>\n'
                 + ''.join(f'<script src="{RT}{m}"></script>\n' for m in ['../assets/vendor/echarts.min.js', 'kz-tokens.js', 'kz-motion.js', 'kz-scenes.js', 'kz-icons.js', 'kz-demo.js', 'kz-demo-patterns.js', 'kz-charts.js', 'kz-gantt.js', 'kz-drilldown.js'])
                 + f'<script src="../../../adapters/html-ppt-bridge.js"></script>\n<script src="{base}../site/site.js"></script>\n'
                 + ''.join(f'<script src="{d}"></script>\n' for d in data_scripts)
                 + f'<script>window.KZ_DECK_DATA = {data};</script>\n<script src="{base}deck.js"></script>\n'
                 + f'<script src="{RT}kz-audience.js"></script>\n</body></html>\n')
    out.write_text(head + body_html, encoding='utf-8')
    print('wrote', out, len(slides), 'slides')

if __name__ == '__main__':
    TOTAL = 12
    slides = [
        hero('cover', {'title': '研究资料完整性核对', 'subtitle': '合成示例｜应收 24 份，已收 20 份', 'meta': FOOT, 'title_short': '封面'}, 'cover.webp',
             '今天汇报一个研究资料包的完整性核对，数据是合成的。按计划应收 24 份，目前收到 20 份，还缺 4 份。希望会上把补收和确认的安排定下来。'),
        hero('toc', {'title': '汇报章节', 'items': [{'title': '研究范围', 'description': '对象、时间窗与核对流程'}, {'title': '资料完整性', 'description': '应收与已收、缺口所在'}, {'title': '核对计划', 'description': '补收、确认与复核'}], 'title_short': '目录'}, 'toc.webp',
             '分三部分：先说这次核对的范围和做法，再看各组资料收齐了多少，最后是补收、确认和复核的季度安排。'),
        hero('section', {'number': '01', 'title': '研究范围', 'title_short': '研究范围'}, 'section.webp', '先看范围。范围定下来，才知道哪些资料要进核对。'),
        body(4, TOTAL, '研究范围', 'cards-3',
             card('研究对象与时间窗', [], [('成人受试者', '研究对象'), ('第 16 周', '评价时间窗')])
             + card('纳入资料', ['方案与修订', '中心记录', '实验室数据', '安全性报告'], [('4 组', '纳入核对')], cols=2)
             + card('方案版本', ['V2.1 与 V2.3 并排比较', '筛选窗口、终点评价时间点'], [('2 项', '待确认差异', 'risk')])
             + '<div class="kz-span-all" data-kz-reveal><article class="kz-card kz-takeaway-card" data-kz-no-tilt data-kz-layout="centered"><p>版本差异<span class="kz-risk">确认之后</span>，再做组间比较</p></article></div>',
             '核对对象是成人受试者，评价时间窗是第 16 周。资料分 4 组：方案与修订、中心记录、实验室数据、安全性报告。方案有 V2.1 和 V2.3 两版，并排比下来有 2 处要确认：筛选窗口和终点评价时间点。这 2 项会影响后面的组间比较，所以确认之前先不比。'),
        body(5, TOTAL, '核对流程', 'film', film_page(DATA['film']),
             '核对分四步。先定范围；再逐组清点应收和已收，缺的照原样记成空值；然后把两版方案并排比较，差异转交确认，我们不判断哪一版对；最后把补收和确认排进季度计划。'),
        hero('section', {'number': '02', 'title': '资料完整性', 'title_short': '资料完整性'}, 'section.webp', '接下来看各组资料收齐了多少。'),
        body(7, TOTAL, '资料完整性', 'split-7-5',
             '<div data-kz-reveal><article class="kz-card kz-data-card" data-kz-no-tilt><div class="kz-data-head"><h3>各资料组应收与已收</h3></div><div class="kz-chart" data-kz-chart="completeness" role="img" aria-label="应收与已收：方案与修订 2 与 2，中心记录 12 与 9，实验室数据 6 与 6，安全性报告 4 与 3"></div></article></div>'
             '<div class="kz-stack"><div data-kz-reveal><article class="kz-card kz-takeaway-card" data-kz-no-tilt data-kz-layout="centered"><p>缺口集中在<span class="kz-risk">中心记录与安全性报告</span></p></article></div>'
             '<div data-kz-reveal><article class="kz-card" data-kz-no-tilt><h3>应收、已收与缺失</h3><table class="kz-deck-table"><thead><tr><th>资料组</th><th>应收</th><th>已收</th><th>缺失</th></tr></thead><tbody>'
             '<tr><td>方案与修订</td><td>2</td><td>2</td><td>0</td></tr><tr><td>中心记录</td><td>12</td><td>9</td><td><span class="kz-risk">3</span></td></tr><tr><td>实验室数据</td><td>6</td><td>6</td><td>0</td></tr><tr><td>安全性报告</td><td>4</td><td>3</td><td><span class="kz-risk">1</span></td></tr></tbody></table>'
             '<p class="kz-table-note">缺失记录保留为空值，<b>不按零处理，也不插补</b></p></article></div></div>',
             '方案与修订、实验室数据已经收齐，缺口在两组：中心记录缺 3 份，安全性报告缺 1 份。缺的记录在数据里留空，不按零处理，也不插补，这样后面比较时缺口一直看得见。'),
        body(8, TOTAL, '缺口与补收', 'demo',
             demo_page('units', '清点结果', ['应收 24 份，已收 20 份', '中心记录缺 3 份，安全性报告缺 1 份', '缺失记录保留为空值，<b>不按零处理，也不插补</b>', '4 份由医学部牵头，<b>2027Q1 内补收</b>'], [('4 份', '缺口', 'risk')]),
             '【1】先看总量：应收 24 份，一个方块代表一份。【2】按四个资料组分开。【3】收到的变实心，缺的留空，不按零处理。'
             '【4】缺口集中在中心记录和安全性报告，一共 4 份。【5】这 4 份进入补收清单，由医学部牵头，2027 年一季度内补齐。'),
        body(9, TOTAL, '缺失与差异的处理', 'demo-mirror',
             demo_page('decision', '判定规则', ['资料未收到：保留空值，进入补收清单', '已收到：先看版本差异是否已确认', '差异确认之后，<b>才做组间比较</b>'], preset='demo-mirror'),
             '【1】每份资料走同一条判定路径。【2】示例 A 已收、差异已确认，进入组间比较。【3】示例 B 是缺失的中心记录，保留空值，进入补收清单。'
             '【4】示例 C 已收，但差异还没确认，先不比较。【5】两条规则：缺失不按零处理，差异确认之前不比较。'),
        hero('section', {'number': '03', 'title': '核对计划', 'title_short': '核对计划'}, 'section.webp', '最后是补收、确认和复核的时间表。'),
        body(11, TOTAL, '核对计划', 'full',
             '<div data-kz-reveal><article class="kz-card kz-data-card" data-kz-no-tilt><div class="kz-data-head"><h3>季度安排</h3>' + legend([('medical', '医学部'), ('statistics', '数统'), ('pv', 'PV')]) + '</div>'
             '<div data-kz-gantt="gantt"></div><p class="kz-gantt-note">补收与版本差异确认<b>在 2027Q1 内完成</b>，复核、安全性报告核对与审阅意见在 2027Q2 内完成</p></article></div>',
             '关键节点是 2027 年一季度。缺的 4 份由医学部从今年四季度开始补收，一季度内补齐；两版方案的差异也在一季度内确认。数统的完整性复核和 PV 的安全性报告核对从一季度做到二季度，二季度由医学部形成审阅意见。'),
        hero('ending', {'title': '请确认两件事', 'subtitle': '4 份资料由医学部牵头，2027Q1 内补收；版本差异确认后再做组间比较', 'meta': FOOT, 'title_short': '结束'}, 'ending.webp',
             '最后请大家确认两件事：一是缺的 4 份资料由医学部牵头，2027 年一季度内补收；二是 2 项版本差异确认之后，再做组间比较。没有不同意见的话，就按这个时间表推进。'),
    ]

    write_deck(slides, json.dumps({**DATA, "demos": DEMOS}, ensure_ascii=False), HERE / 'index.html', '研究资料完整性核对')
