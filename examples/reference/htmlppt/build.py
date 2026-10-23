#!/usr/bin/env python3
"""Derive the Kangzhe reference deck from the html-ppt-skill scaffold (scaffold.html = raw new-deck.sh output).

Kept from upstream: the <body>/.deck/.slide structure, base.css and runtime.js (vendored, byte-identical),
speaker notes in .notes. Replaced: theme links, remote web fonts, animations.css and data-themes (Kangzhe owns
the look; the A key then has no animation CSS to apply), and the demo slides. Hero pages come from
tools/hero_layout.html_fluid_fragment, the header mark from tools/brand_fragments.facets.
Run:  python examples/reference/htmlppt/build.py
"""
from pathlib import Path
from html import escape
import re, sys
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

def card(title, items, marker=None, tilt=True):
    m = f'<span class="kz-marker">{marker}</span>' if marker else ''
    lis = ''.join(f'<li>{i}</li>' for i in items)
    return f'<div data-kz-reveal><article class="kz-card"{" data-kz-tilt" if tilt else " data-kz-no-tilt"}>{m}<h3>{escape(title)}</h3><ul>{lis}</ul></article></div>'

TOTAL = 8
slides = [
    hero('cover', {'title': '证据组织与资料核对', 'subtitle': '合成示例 · 研究资料审阅流程', 'meta': FOOT, 'title_short': '封面'}, 'cover.webp',
         '今天用一个合成示例说明资料从界定范围到形成审阅意见的组织方式，内容不对应真实研究。'),
    hero('toc', {'title': '汇报章节', 'items': [{'title': '研究范围', 'description': '人群、终点与时间窗'}, {'title': '资料核对', 'description': '版本与缺失记录'}, {'title': '核对计划', 'description': '季度安排'}], 'title_short': '目录'}, 'toc.webp',
         '三部分依次展开：先界定范围，再看资料核对中的版本与缺失，最后是核对计划。'),
    hero('section', {'number': '01', 'title': '研究范围', 'title_short': '研究范围'}, 'section.webp', '先看研究范围，它决定哪些资料进入核对。'),
    body(4, TOTAL, '研究范围', 'cards-3',
         card('研究人群', ['成人受试者，<b>筛选期 4 周</b>', '既往治疗失败或不耐受', '同期参加其他干预研究者排除'], '01')
         + card('主要终点', ['第 16 周较基线变化', '<span class="kz-risk">缺失值不按零处理</span>', '分析人群与估计量分开说明'], '02')
         + card('安全性', ['治疗期间不良事件', '停药原因<b>分开登记</b>', '严重事件单列时间线'], '03')
         + '<div class="kz-span-all" data-kz-reveal><article class="kz-card kz-takeaway-card" data-kz-no-tilt data-kz-layout="centered"><p>主要终点按第 16 周评价，缺失记录<span class="kz-risk">保留为空值</span></p></article></div>',
         '三张卡分别对应人群、主要终点和安全性。主要终点这里请注意缺失值的处理：缺失保留为空值，不按零计算。'),
    body(5, TOTAL, '证据组织过程', 'film',
         '<div class="kz-film kz-deck-film" data-kz-film><div class="kz-film-stage"><svg class="kz-film-links" aria-hidden="true"></svg>'
         '<div class="kz-film-carrier"><strong class="kz-film-carrier-label">界定范围</strong><p class="kz-film-carrier-sub kz-film-caption">先明确问题与纳入资料的边界。</p><ul class="kz-carrier-facts"><li>研究对象：成人受试者</li><li>评价时间窗：第 16 周</li><li>纳入资料：方案、中心记录、实验室数据</li></ul></div>'
         '<ul class="kz-deck-nodes" aria-label="关系"><li class="kz-deck-node" data-kz-node><b>限定 · 研究问题</b><span>对象、范围与时间窗</span></li><li class="kz-deck-node" data-kz-node><b>对应 · 资料分组</b><span>4 组，各组字段不同</span></li><li class="kz-deck-node" data-kz-node><b>连接 · 待确认差异</b><span>2 项版本差异</span></li><li class="kz-deck-node" data-kz-node><b>回收 · 审阅意见</b><span>回到原问题复核</span></li></ul></div></div>'
         '<ol class="kz-steps" aria-label="阶段"><li class="kz-step" data-phase="0" data-state="current"><span class="kz-step-mark">1</span><b>界定范围</b><p>问题与纳入边界</p></li><li class="kz-step" data-phase="1" data-state="todo"><span class="kz-step-mark">2</span><b>整理证据</b><p>按主题和时间分组</p></li><li class="kz-step" data-phase="2" data-state="todo"><span class="kz-step-mark">3</span><b>审阅差异</b><p>识别待补足限制</p></li><li class="kz-step" data-phase="3" data-state="todo"><span class="kz-step-mark">4</span><b>回到问题</b><p>确认资料是否足够</p></li></ol>',
         '这一页的画面会自动推进四个阶段：先界定范围，再把资料按主题和时间分组，然后比较差异，最后回到原问题。讲到差异时可以指向右侧第三个节点。'),
    body(6, TOTAL, '资料完整性', 'split-7-5',
         '<div data-kz-reveal><article class="kz-card kz-data-card" data-kz-no-tilt><div class="kz-data-head"><h3>各组完整份数</h3><span>单位：份</span></div><div class="kz-chart" data-kz-chart="completeness" role="img" aria-label="方案与修订2份、中心记录9份、实验室数据6份、安全性报告4份"></div></article></div>'
         '<div class="kz-stack"><div data-kz-reveal><article class="kz-card kz-takeaway-card" data-kz-no-tilt data-kz-layout="centered"><p>中心记录的缺失需要先补足依据，再做组间比较</p></article></div>'
         '<div data-kz-reveal><article class="kz-card" data-kz-no-tilt><h3>分组数值</h3><table class="kz-deck-table"><thead><tr><th>分组</th><th>完整</th><th>缺失</th></tr></thead><tbody>'
         '<tr><td>方案与修订</td><td>2</td><td>0</td></tr><tr><td>中心记录</td><td>9</td><td><span class="kz-risk">3</span></td></tr><tr><td>实验室数据</td><td>6</td><td>0</td></tr><tr><td>安全性报告</td><td>4</td><td>0</td></tr></tbody></table></article></div></div>',
         '图中是各组完整份数。中心记录 12 份里有 3 份缺失，所以右侧的强调句建议先补足依据，再做比较。'),
    body(7, TOTAL, '核对计划', 'full',
         '<div data-kz-reveal><article class="kz-card kz-data-card" data-kz-no-tilt><div class="kz-data-head"><h3>季度安排</h3><span>可拖动条形或在右侧修改起止季度</span></div><div data-kz-gantt="plan"></div></article></div>',
         '四项工作按季度排开。现场如需调整，可以直接拖动条形，修改只保留在本次放映中。'),
    hero('ending', {'title': '谢谢', 'subtitle': '证据组织与资料核对', 'meta': FOOT, 'title_short': '结束'}, 'ending.webp', '以上是合成示例的完整流程，谢谢。'),
]

src = (HERE / 'scaffold.html').read_text(encoding='utf-8')
head_end = src.index('</head>')
head = ('<!DOCTYPE html>\n<!-- Derived from html-ppt-skill new-deck.sh output (scaffold.html) by build.py; do not edit by hand. -->\n'
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>证据组织与资料核对 · 康哲医学部</title>\n<link rel="icon" href="data:,">\n'
        '<link rel="stylesheet" href="vendor/html-ppt/assets/base.css">\n'
        f'<link rel="stylesheet" href="{RT}kz-tokens.css">\n<link rel="stylesheet" href="{RT}kz-glass.css">\n<link rel="stylesheet" href="deck.css">\n</head>\n')
assert '<div class="deck">' in src and 'assets/runtime.js' in src, 'scaffold structure changed upstream; re-read new-deck.sh output'
body_html = ('<body class="kz" data-fit="fluid">\n<div class="deck">\n' + '\n'.join(slides) + '\n</div>\n'
             '<script src="vendor/html-ppt/assets/runtime.js"></script>\n'
             + ''.join(f'<script src="{RT}{m}"></script>\n' for m in ['../assets/vendor/echarts.min.js', 'kz-tokens.js', 'kz-motion.js', 'kz-charts.js', 'kz-gantt.js', 'kz-drilldown.js'])
             + '<script src="../../../adapters/html-ppt-bridge.js"></script>\n<script src="../site/data.js"></script>\n<script src="../site/site.js"></script>\n<script src="deck.js"></script>\n'
             + f'<script src="{RT}kz-audience.js"></script>\n</body></html>\n')
(HERE / 'index.html').write_text(head + body_html, encoding='utf-8')
print('wrote', HERE / 'index.html', len(slides), 'slides')
