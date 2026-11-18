#!/usr/bin/env python3
"""Flagship PPTX clinical templates (14 FLAG-12, language L1 「层叠纸板」): one page per template.

flag-safety (butterfly) · flag-program (facet arrows) · flag-safety-dumbbell · flag-program-strip · flag-exposure · flag-trialflow · flag-landscape · flag-efficacy · flag-soa · flag-exposure-plan, on the F1 frame of
../pptx-flagship (header badge, logo, chips, progress, footer). Bodies come from tools/kz_layouts/flagship_pptx.py and
read the clinical contracts (safety_model, program_model, exposure_model, trialflow_model, landscape_model, efficacy_model, soa_model) of examples/templates/*.json, so the numbers match the
static templates, the regular demos and the flagship stages. Checking and export stay with ppt-master (README).
Usage: python3 examples/reference/pptx-flagship-clinical/build_svg.py <ppt-master project dir>
"""
from pathlib import Path
import argparse, importlib.util, json, shutil, sys
ROOT = Path(__file__).resolve().parents[3]; HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from kz_layouts import flagship_pptx as FP  # noqa: E402
spec = importlib.util.spec_from_file_location('kzf_ref', ROOT / 'examples/reference/pptx-flagship/build_svg.py')
BS = importlib.util.module_from_spec(spec); spec.loader.exec_module(BS)

T = BS.T; W, H, MX = BS.W, BS.H, BS.MX
BOX = (MX, BS.BODY_T, W - 2 * MX, BS.BODY_B - BS.BODY_T)
BS.CHAPTERS = [('shield', '安全性', '治疗期不良事件'), ('timeline', '临床开发计划', '多适应症泳道与关键里程碑'), ('people', '暴露与样本量', '各适应症暴露例数与 ICH E1 目标'), ('route', '研究设计', '随机化、再随机化与随访'), ('chart-dots', '竞争格局', '研发阶段、疗效与耐受性'), ('target', '有效性', '主要与次要终点'), ('calendar', '访视流程', '访视安排与评估负担')]
BS.TITLE = 'KZ-001 临床汇报（合成示例）'

def load(name):
    return json.loads((ROOT / 'examples/templates' / name).read_text(encoding='utf-8'))

SAFE = load('safety-overview.json')
for it, row in zip(SAFE['insights'], ('trae', 'tesae', 'disc')): it['row'] = row   # numeral pairs on the insight tabs
PROG = load('program-plan.json')
EXPO = load('exposure-summary.json')
XPLAN = load('exposure-plan.json')
FLOW = load('trial-flow.json')
LAND = load('landscape.json')
EFF = load('efficacy-summary.json')
# a flagship page carries the primary and key secondary endpoints (the full list stays on the static template / appendix)
EFF['efficacy']['rows'] = [r for r in EFF['efficacy']['rows'] if r.get('tier') in ('主要', '关键次要')]
_soa = load('soa.json')
# flag-soa (round 9): key events, treatment periods and the assessments item by item; two sections on this page (dosing is the study-drug period),
# no insight tabs — the summary is in the notes
SOA = {'title': 'III 期访视与评估安排（12 次访视）', 'soa': {k: _soa[k] for k in ('visits', 'events', 'bands', 'rows', 'focus')},
       'sections': ['有效性评估', '安全性评估']}
EFF['insights'] = EFF['insights'][:2] + [{'icon': 'award', 'title': '达标率为安慰剂的 3.4 倍', 'text': 'HbA1c <7.0%：1.0 mg 组 **71.0%** 对 21.0%，0.5 mg 组 59.0%'}]

PAGES = [  # (file, template, title, kicker, chips, data)
    ('01_safety', 'flag-safety', '治疗期不良事件总览', '01 安全性', ['安全性分析集', '合成示例'], SAFE),
    ('02_program', 'flag-program', 'KZ-001 临床开发计划', '02 临床开发计划', ['5 个适应症', '2025–2029'], PROG),
    ('03_safety_db', 'flag-safety-dumbbell', '治疗期不良事件的组间差', '01 安全性', ['安全性分析集', '合成示例'], SAFE),
    ('04_program_strip', 'flag-program-strip', '开发计划（纸条版）', '02 临床开发计划', ['5 个适应症', '2025–2029'], PROG),
    ('05_exposure', 'flag-exposure', '暴露例数汇总', '03 暴露与样本量', ['安全性分析集', '合成示例'], EXPO),
    ('06_trialflow', 'flag-trialflow', 'III 期研究流程', '04 研究设计', ['随机撤药设计', '合成示例'], FLOW),
    ('07_landscape', 'flag-landscape', '减重药物竞争格局', '05 竞争格局', ['竞品为合成示例', '跨研究比较'], LAND),
    ('08_efficacy', 'flag-efficacy', 'III 期有效性汇总', '06 有效性', ['W26 · FAS', '合成示例'], EFF),
    ('09_soa', 'flag-soa', '访视流程概览', '07 访视流程', ['12 次访视', '合成示例'], SOA),
    ('10_exposure_plan', 'flag-exposure-plan', '累计暴露与各适应症 NDA', '03 暴露与样本量', ['按开发计划累计', 'ICH E1', '合成示例'], XPLAN)]

# speaker notes, one block per page (09 NOTES; the summaries that used to sit in insight tabs live here)
_nl = [l for l in (HERE / 'notes.md').read_text(encoding='utf-8').splitlines() if l.strip()]   # page id line, then its notes line
NOTES = dict(zip(_nl[0::2], _nl[1::2]))

def build(project):
    svg_dir, img_dir, ico = project / 'svg_output', project / 'images', project / 'icons/kangzhe'
    for d in (svg_dir, img_dir, ico): d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / T['logo']['png_path'], img_dir / 'logo.png')
    shutil.copy2(ROOT / 'assets/backgrounds/flagship/canvas.jpg', img_dir / 'flagship-canvas.jpg')
    for fsvg in (ROOT / 'assets/icons/kangzhe').glob('*.svg'): shutil.copy2(fsvg, ico / fsvg.name)
    n = len(PAGES); slides, plan_pages = {}, []
    enter = T['motion']['duration_ms']['card'] / 1000; step = T['motion']['stagger_ms']['pptx_card'] / 1000
    for i, (name, tpl, title, kicker, chips, data) in enumerate(PAGES):
        pg = BS.Page(f'p{i + 1:02d}', 'body', title, tpl)
        inner = BS.bg('flagship-canvas.jpg') + BS.logo(False) + BS.header(pg, kicker, chips) + FP.RENDER[tpl](pg, data, BOX) + BS.chrome_foot(pg, i, n)
        svg = BS.svg_page('content', inner).replace('</defs>', FP.defs() + '</defs>', 1)
        (svg_dir / f'{name}.svg').write_text(svg, encoding='utf-8')
        groups, order, last, kin = {}, 0, None, 0
        for gid, scene, effect, opt in sorted(pg.groups, key=lambda g: g[1]):
            order += 1; kin = 0 if scene != last else kin + 1
            row = {'effect': effect, 'duration': T['motion']['duration_ms']['data'] / 1000 if 'wipe' in effect else enter,
                   'delay': round(kin * step, 3), 'trigger': 'with-previous' if scene == 0 or kin else 'on-click', 'order': order}
            if effect in ('entrance_fade', 'entrance_wipe', 'entrance_zoom'): row['decelerate'] = 0.7
            row.update(opt); groups[gid] = row; last = scene
        slides[name] = {'groups': groups}
        plan_pages.append({'id': pg.pid, 'kind': 'body', 'title': title, 'body_profile': 'standard', 'template': tpl, 'elements': pg.els,
                           'protected_regions': [], 'image': {'mode': 'flagship_set', 'asset_id': 'flagship-canvas'},
                           'cards': [{'id': c, 'material': 'flagship_paper', 'edge_decoration': 'none', 'layout_mode': 'distributed',
                                      'detail': 'not_needed', 'detail_reason': '合成示例页，卡内已给全量信息'} for c in pg.cards],
                           'sources': [{'id': 'brief', 'kind': 'internal', 'visible': False}]})
    anim = {'defaults': {'transition': {'effect': 'fade', 'duration': 0.4}, 'animation': {'effect': 'none'}}, 'slides': slides}
    (project / 'animations.json').write_text(json.dumps(anim, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    plan = {'schema_version': '6.1', 'contract_revision': '7.0', 'track': 'pptx', 'route': 'flagship', 'canvas': [W, H],
            'target_viewports': T['viewports'].get('pptx', [[W, H]]), 'pages': plan_pages}
    (project / 'page-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (project / 'notes').mkdir(exist_ok=True)
    (project / 'notes/total.md').write_text('\n\n---\n\n'.join(f'# {name}\n\n{NOTES[name].strip()}' for name, *_ in PAGES) + '\n', encoding='utf-8')
    return [p[0] for p in PAGES]

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', type=Path); a = ap.parse_args()
    print(json.dumps(build(a.project.resolve()), ensure_ascii=False))
