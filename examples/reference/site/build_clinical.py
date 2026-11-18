"""Clinical reference pages for the site and stream tracks (round 9): the longitudinal family (HbA1c by arm with the
difference, safety labs as small multiples, ALT distribution, completeness) and the cumulative exposure on the development
plan together with its Gantt — one program id, so an edit in either (drag, T studio) moves the other and the readiness
table. Data are the synthetic template examples (examples/templates/*.json); charts mount through KZCharts (ECharts),
the exposure figure and the longitudinal kinds through runtime/kz-explore.js.

    python3 examples/reference/site/build_clinical.py      → site/clinical.html and stream/clinical.html
"""
import json, sys
from html import escape
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from kz_layouts import figures as FG
from kz_layouts.diagram_scenes import exposure_plan, exposure_readiness_table

def load(n): return json.loads((ROOT / 'examples/templates' / n).read_text(encoding='utf-8'))
HBA, BL, ALT, MUL, XP = load('longitudinal.json'), load('longitudinal-blinded.json'), load('lab-boxplot.json'), load('lab-multiples.json'), load('exposure-plan.json')
DATA = {'hba': {'kind': 'longitudinal', **HBA['longitudinal']}, 'hba-diff': {'kind': 'longitudinal-diff', **HBA['longitudinal']},
        'labs': {'kind': 'lab-multiples', **MUL['lab-multiples']}, 'alt': {'kind': 'lab-boxplot', **ALT['longitudinal']},
        'complete': {'kind': 'completeness', **BL['longitudinal']}, 'xp': {'kind': 'exposure-plan', **XP['exposure_plan']},
        'plan': XP['exposure_plan']['program']}
m = exposure_plan(XP['exposure_plan']); DATA['xp']['ref'] = m['ref']
table = '<div class="kzl-root" style="height:auto;margin-top:12px">' + FG.table_html(exposure_readiness_table(m), 'xp-ready') + '</div>'
FG.collect()   # table_html registers nothing we need here

def chart(id_, label, h=360): return f'<div class="kz-chart" data-kz-chart="{id_}" style="height:{h}px" role="img" aria-label="{escape(label)}"></div>'

CARDS = [  # (span, id, title, body)
    (12, 'hba', 'HbA1c 较基线变化（LS 均值与 95% CI，真实周数）', '<p class="kz-ref-intro">横轴按真实周数排；竖线是 95% CI，轴下是各访视有数据的人数；W30 为停药后随访。'
     '点任一数据点看历时表，所点格子标出，表里可以改数。</p>' + chart('hba', 'HbA1c 较基线变化，三组，W0 到 W30，W26 为主要终点', 380) + chart('hba-diff', '两个剂量组对安慰剂之差与 95% CI', 210)),
    (12, 'labs', '安全性检验与生命体征（均值与 95% CI，各自刻度）', chart('labs', '六项安全性检验与生命体征，两组，W0 到 W52', 460)),
    (6, 'alt', 'ALT 历时分布（箱线）', chart('alt', 'ALT 各访视两组的箱线图，ULN 40 U/L', 360)),
    (6, 'complete', '收缩压数据完整性（进行中，盲态）', chart('complete', '各访视应到、仍在研究、有收缩压数据的人数', 360)),
    (12, 'plan', '临床开发计划（与累计暴露同一份数据）', '<p class="kz-ref-intro">拖动阶段条或按 <b>T</b> 打开编辑台；研究条的“暴露”块改样本量与对照比例。下方累计暴露图、达标表随之更新。</p><div data-kz-gantt="plan"></div>'),
    (12, 'xp', '累计暴露与各适应症 NDA（ICH E1）', chart('xp', '按开发计划累计的研究药物暴露与各适应症 NDA 时点', 380) + table),
]
HEAD = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="../../../runtime/kz-tokens.css">
<link rel="stylesheet" href="../../../runtime/kz-glass.css">
<link rel="stylesheet" href="../../../runtime/kz-layouts.css">
<link rel="stylesheet" href="../site/ref.css">
</head>
<body class="kz">
<main class="kz-ref">
<div class="kz-optical-field" aria-hidden="true"></div>
<header class="kz-site-head"><a class="kz-brand" href="#"><img src="../../../assets/logo_bot.svg" alt="康哲药业"><i></i>{brand}</a>
  <nav aria-label="{nav_label}">{nav}</nav><span class="kz-site-meta">医学部 · 合成示例</span></header>
'''
KPIS = '''<div class="kz-kpis">
      <div data-kz-reveal><article class="kz-card kz-kpi" data-kz-tilt><div><span class="kz-number">−1.88</span><span class="kz-unit">%</span></div><div class="kz-kpi-label">HbA1c · W26</div></article></div>
      <div data-kz-reveal><article class="kz-card kz-kpi" data-kz-tilt><div><span class="kz-number">−1.58</span><span class="kz-unit">%</span></div><div class="kz-kpi-label">较安慰剂 · W26</div></article></div>
      <div data-kz-reveal><article class="kz-card kz-kpi" data-kz-tilt><div><span class="kz-number">2,131</span><span class="kz-unit">例</span></div><div class="kz-kpi-label">累计暴露 2031Q1</div></article></div>
      <div data-kz-reveal><article class="kz-card kz-kpi" data-kz-tilt><div><span class="kz-number kz-risk">369</span><span class="kz-unit">例</span></div><div class="kz-kpi-label">糖尿病 NDA 差额</div></article></div>
    </div>'''
SCRIPTS = ['../../../assets/vendor/echarts.min.js'] + [f'../../../runtime/{n}' for n in ('kz-tokens.js', 'kz-motion.js', 'kz-icons.js', 'kz-clinical.js', 'kz-charts.js', 'kz-gantt.js', 'kz-gantt-studio.js', 'kz-drilldown.js', 'kz-explore.js')]
MOUNT = '''<script>
(function () {
  'use strict';
  const D = window.KZ_DECK_DATA, life = [];
  // data reveals start once, when the figure first scrolls into view
  const whenVisible = (node, play) => { const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) { io.disconnect(); play(); } }, { threshold: .3 }); io.observe(node); life.push({ dispose: () => io.disconnect() }); };
  for (const el of document.querySelectorAll('[data-kz-gantt]')) life.push(KZGantt.mount(el, D[el.dataset.kzGantt]));
  for (const el of document.querySelectorAll('[data-kz-chart]')) { const c = KZCharts.mount(el, D[el.dataset.kzChart]); life.push(c); whenVisible(el, () => c.play()); }
  if (window.KZMotion && KZMotion.mountSections) life.push(KZMotion.mountSections(document));
  addEventListener('pagehide', () => life.forEach(x => { try { x.dispose(); } catch (e) { console.error(e); } }), { once: true });
  window.KZ_PAGE = { life };
  document.documentElement.dataset.kzPageReady = 'true';
})();
</script>'''

def page(track):
    site = track == 'site'
    nav = ('<a href="index.html">首页</a><a href="chapter.html">资料核对</a><a href="clinical.html" aria-current="page">临床数据</a><a href="../stream/clinical.html">流式阅读版</a>' if site
           else ''.join(f'<a href="#{c[1]}">{t}</a>' for c, t in zip([CARDS[0], CARDS[2], CARDS[5]], ['有效性历时', '安全性检验', '暴露与计划'])) + '<a href="../site/clinical.html">站点版本</a>')
    out = HEAD.format(title='临床数据｜历时变化与累计暴露' + ('' if site else '（流式阅读版）'), brand='证据组织 › 临床数据' if site else '临床数据 · 流式阅读版',
                      nav_label='站点导航' if site else '文档导航', nav=nav)
    lede = '<p class="kz-lede">有效性与安全性指标按真实时间看变化；累计暴露挂在开发计划上，改计划即改暴露。全部为合成示例。</p>'
    if site:
        out += f'<header class="kz-chapter" aria-label="章节概览"><div class="kz-chapter-title"><div><h1>临床数据</h1>{lede}</div>{KPIS}</div></header>\n<div class="kz-sheet">\n'
        for span, id_, title, body in CARDS:
            out += f'  <div data-span="{span}" data-kz-section id="{id_}"><article class="kz-card" data-kz-no-tilt><h3>{title}</h3>{body}</article></div>\n'
        out += '</div>\n'
    else:
        out += f'<section class="kz-fold" aria-label="文档概览"><div class="kz-fold-grid"><div class="kz-fold-lead"><div><h1>临床数据</h1>{lede}</div>{KPIS}</div></div></section>\n<div class="kz-stream">\n'
        for span, id_, title, body in CARDS:
            out += f'  <section data-kz-section id="{id_}"><article class="kz-card" data-kz-no-tilt><h3>{title}</h3>{body}</article></section>\n'
        out += '</div>\n'
    out += '<footer class="kz-ref-foot"><span>产品中心-医学部｜2026年10月</span><span>临床数据</span></footer>\n</main>\n'
    out += ''.join(f'<script src="{s}"></script>\n' for s in SCRIPTS)
    out += f'<script>window.KZ_DECK_DATA = {json.dumps(DATA, ensure_ascii=False)};</script>\n' + MOUNT + '\n</body>\n</html>\n'
    return out

(HERE / 'clinical.html').write_text(page('site'), encoding='utf-8')
(HERE.parent / 'stream' / 'clinical.html').write_text(page('stream'), encoding='utf-8')
print('wrote site/clinical.html stream/clinical.html')
