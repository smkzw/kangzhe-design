#!/usr/bin/env python3
"""Flagship stage gallery (14 FLAG-06a): one page per cinematic three.js stage of runtime/kz-flagship-stages.js, grouped by
content job, so authors can compare the alternatives for the same content (the completeness pages draw one data set three ways).
Synthetic numbers only. The side column is read from tokens.flagship.stages.catalog, so the gallery cannot drift from
the register. Run:  python3 examples/motion/flagship/build.py   → index.html
"""
from pathlib import Path
from html import escape
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RT, AS, UP = '../../../runtime/', '../../../assets/', '../../reference/htmlppt-flagship/vendor/html-ppt/assets/'
TOK = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
CAT, JOBS = TOK['flagship']['stages']['catalog'], TOK['flagship']['stages']['jobs']
TITLE = '旗舰舞台组件库'
DATE = '2026年11月'

GROUPS = [{'name': '方案与修订', 'due': 2, 'got': 2}, {'name': '中心记录', 'due': 12, 'got': 9},
          {'name': '实验室数据', 'due': 6, 'got': 6}, {'name': '安全性报告', 'due': 4, 'got': 3}]
STEP_DOC = {
    'platforms': {'rise': '平台升起', 'fill': '每份资料落位', 'miss': '缺口闪红', 'orbit': '镜头环绕'},
    'rings': {'rise': '圆环展开', 'fill': '各环按完成度扫满', 'focus': '最低一环转红', 'orbit': '圆环倾转'},
    'morph': {'pile': '全部方块堆成总量', 'split': '飞向各组立成柱', 'gaps': '缺口飞入缺口盘', 'orbit': '镜头绕到侧面读数'},
    'towers': {'rise': '底座与柱基', 'grow': '柱高长到数值', 'focus': '重点柱留亮', 'orbit': '镜头环绕'},
    'stream': {'build': '通道与闸门', 'flow': '粒子流过、各级流失下落', 'focus': '最大流失一级标红', 'travel': '镜头沿通道推进'},
    'layers': {'stack': '各层叠起', 'explode': '分层展开并标名', 'fill': '各层内容落位', 'focus': '重点层抬起'},
    'runway': {'track': '轨道从起点铺开', 'flags': '里程碑立起，镜头拉远', 'run': '走到当前，镜头跟随', 'focus': '下一节点提示'},
    'constellation': {'hub': '中心点亮', 'nodes': '各方展开', 'links': '连线长出', 'pulse': '脉冲送达'},
    'ghost': {'before': '前值立成玻璃虚影', 'after': '后值实体长出', 'delta': '升降按好坏着色', 'orbit': '镜头环绕'},
    'safety': {'set': '台面、中脊与两组 N', 'overall': '任何 TEAE 两翼伸出', 'cascade': '下级类别从 TEAE 条里分出、滑到各自行', 'rest': '其余类别伸出',
               'diff': '差值入列、超阈值标红', 'focus': '镜头沿台面推到重点行，该行抬起'},
    'exposure': {'set': '玻璃台面与各适应症行', 'any': '任何暴露的长板伸出', 'longer': '更长时长档逐级叠成台阶（越长越高越深）', 'total': '合计长成塔柱、目标面出现（达到为绿）',
                 'focus': '镜头转向重点行，该行抬起'},
    'landscape': {'set': '玻璃台面与疗效 × 安全性场地', 'stage': '各药物立成玻璃筹码，越接近上市越高，按阶段沿前沿排开', 'map': '筹码滑到疗效（右）× 安全性（前）的位置，无数据的进左侧托盘',
                  'ideal': '理想区（疗效更好、耐受更好）亮起', 'focus': '镜头落到重点药物（默认本品），其余退后'},
    'trialflow': {'set': '玻璃台面、各治疗分支轨道与周刻度', 'shared': '共同阶段立成横跨各轨的厚板', 'random': '随机化圆台落下、玻璃杆分到各组',
                  'arms': '各组段落沿轨道长出（递增低而浅、维持高而深、安慰剂石墨色）', 'sub': '再随机化圆台与子分组段落', 'end': '终点标针落到前沿、共同随访与子研究色带', 'focus': '镜头转向重点组，其余退后'},
    'efficacy': {'set': '玻璃台面与各终点轨道（一节一轴：均值差、率差、比值，从后到前）', 'effects': '各节依次立起参考值玻璃墙，各治疗组效应条朝有利方向（右）长出、95% CI 细轨在上',
                 'ns': 'CI 跨参考值的终点抬起，其余退后', 'focus': '镜头转向重点终点，该行加高'},
    'soa': {'set': '玻璃台面、各分组轨道与访视列（访视名与周次）', 'periods': '各分期色板滑到所属访视下', 'treatment': '前沿长出给药与治疗时段条，主要终点访视立起淡色玻璃柱，其他关键节点在前沿标名',
            'sections': '各分组在每次访视叠起硬币（一枚 = 一个评估项目）', 'focus': '重点项目的访视落下标针，其余分组退后'},
    'program': {'rails': '玻璃台面与泳道、年份', 'phases': '各阶段按时间长出，阶段越后越高', 'today': '当前面扫到当前季度，之后的部分磨砂成计划',
                'milestones': '里程碑落到阶段条上（已过深色、未来白色）', 'focus': '镜头转向重点泳道，其余退后'},
}

PAGES = [
    ('platforms', '四组资料到位全景', {'groups': GROUPS},
     '四组资料：方案与修订 2 份全到，中心记录 12 份到 9 份，实验室数据 6 份全到，安全性报告 4 份到 3 份'),
    ('rings', '四组资料完成度', {'items': [{'name': g['name'], 'done': g['got'], 'total': g['due']} for g in GROUPS], 'center': '整体完成'},
     '四组资料完成度：方案与修订 100%，中心记录 75%，实验室数据 100%，安全性报告 75%，整体 83%'),
    ('morph', '应收资料去了哪里', {'unit': '份', 'groups': GROUPS},
     '应收 24 份按组立柱，已收 20 份，缺口 4 份：中心记录 3 份、安全性报告 1 份'),
    ('towers', '各中心入组人数', {'unit': '例', 'items': [{'name': '中心 A', 'value': 46}, {'name': '中心 B', 'value': 38}, {'name': '中心 C', 'value': 61, 'focus': True},
                                                                       {'name': '中心 D', 'value': 27}, {'name': '中心 E', 'value': 33}]},
     '五家中心入组：A 46 例、B 38 例、C 61 例、D 27 例、E 33 例，C 最多'),
    ('stream', '筛选到完成的逐级人数', {'unit': '例', 'stages': [{'name': '筛选', 'value': 320}, {'name': '符合入选', 'value': 248}, {'name': '随机', 'value': 205},
                                                                         {'name': '完成治疗', 'value': 181}, {'name': '完成随访', 'value': 172}]},
     '筛选 320 例，符合入选 248 例，随机 205 例，完成治疗 181 例，完成随访 172 例；筛选到入选流失最多'),
    ('layers', '资料核对的三层结构', {'focus': 1, 'layers': [
        {'name': '规则层', 'note': '方案版本与核对口径', 'items': ['方案 V2.3', '入排标准', '时间窗']},
        {'name': '资料层', 'note': '四组应收资料', 'items': ['方案修订', '中心记录', '实验室', '安全性']},
        {'name': '系统层', 'note': '归档与传递', 'items': ['eTMF', 'EDC', '安全库']}]},
     '资料核对分规则层、资料层、系统层；资料层是本次重点'),
    ('runway', '核对计划里程碑', {'now': 1.4, 'nowLabel': '当前', 'items': [
        {'when': '2026Q4', 'name': '启动核对', 'owner': '医学部'}, {'when': '2027Q1', 'name': '缺失资料补收'},
        {'when': '2027Q1', 'name': '版本差异确认'}, {'when': '2027Q2', 'name': '完整性复核', 'owner': '数统'},
        {'when': '2027Q3', 'name': '形成审阅意见'}]},
     '核对计划五个里程碑，当前在缺失资料补收与版本差异确认之间，下一节点是版本差异确认'),
    ('constellation', '资料核对的协作方', {'hub': {'name': '医学部'}, 'nodes': [
        {'name': '临床运营', 'weight': 3}, {'name': '数统', 'weight': 2}, {'name': 'PV', 'weight': 2}, {'name': '研究中心', 'weight': 3},
        {'name': '注册', 'weight': 1}, {'name': 'CRO', 'weight': 2}]},
     '医学部牵头，协作方为临床运营、数统、PV、研究中心、注册与 CRO'),
    ('ghost', '两个季度的核对指标', {'unit': '', 'from': '2026Q2', 'to': '2026Q4', 'items': [
        {'name': '已收资料（份）', 'before': 14, 'after': 20, 'good': 'up'}, {'name': '缺口（份）', 'before': 10, 'after': 4, 'good': 'down'},
        {'name': '版本差异（项）', 'before': 5, 'after': 2, 'good': 'down'}, {'name': '平均关闭天数', 'before': 9, 'after': 6, 'good': 'down'}]},
     '2026Q2 到 2026Q4：已收资料 14 到 20 份，缺口 10 到 4 份，版本差异 5 到 2 项，平均关闭天数 9 到 6 天'),
    # 8.0 scenario family: the stage reads the same contract as the static template and the regular demo form
    ('safety', '治疗期不良事件总览', json.loads((ROOT / 'examples/templates/safety-overview.json').read_text(encoding='utf-8'))['safety'],
     '安全性分析集：KZ-001 1.0 mg 200 例、安慰剂 100 例；任何 TEAE 71.0% 对 61.0%，TRAE 48.0% 对 30.0%，TESAE 6.0% 对 5.0%，无导致死亡的 TEAE'),
    ('exposure', 'KZ-001 暴露例数汇总', json.loads((ROOT / 'examples/templates/exposure-summary.json').read_text(encoding='utf-8'))['exposure'],
     '安全性分析集共 1,830 例用过 KZ-001：≥26 周 1,232 例、≥52 周 635 例，三档都达到 ICH E1 目标；长期暴露来自 2 型糖尿病与肥胖'),
    ('landscape', 'GLP-1 类减重药物竞争格局', json.loads((ROOT / 'examples/templates/landscape.json').read_text(encoding='utf-8'))['landscape'],
     '七个药物（竞品为合成示例）：A、B 已上市，KZ-001 与 C 在 III 期；体重降幅 KZ-001 18.6% 排第 2，胃肠道不良事件 34.0% 最低'),
    ('trialflow', 'KZ-001 III 期研究流程', json.loads((ROOT / 'examples/templates/trial-flow.json').read_text(encoding='utf-8'))['trialflow'],
     '600 例按 2:1 随机：KZ-001 先 16 周递增、再维持到 W36 主要终点，之后 360 例 1:1 再随机化继续或转安慰剂；安慰剂组全程 52 周；前 36 周 120 例参加 CGM 子研究'),
    ('efficacy', 'KZ-001 III 期有效性汇总', json.loads((ROOT / 'examples/templates/efficacy-summary.json').read_text(encoding='utf-8'))['efficacy'],
     'W26 FAS：HbA1c 较安慰剂再降 1.3% 与 1.7%，体重多降 4.6% 与 7.2%，两剂量 12 个比较里 10 个 95% CI 不跨 0 且有利；收缩压两组 CI 跨 0'),
    ('soa', 'KZ-001 III 期访视流程', {k: v for k, v in json.loads((ROOT / 'examples/templates/soa.json').read_text(encoding='utf-8')).items() if k in ('visits', 'events', 'bands', 'rows', 'focus')},
     '12 次访视分 4 个分期、16 个评估项目：V3（W0 随机化）最忙 13 项，V1 筛选 10 项；HbA1c 在 V1、V3、V7、V10、EOS 共 5 次'),
    ('program', 'KZ-001 临床开发计划', json.loads((ROOT / 'examples/templates/program-plan.json').read_text(encoding='utf-8'))['program'],
     'KZ-001 五个适应症的开发计划：2 型糖尿病 2028Q1 递交 NDA、2028Q4 获批；肥胖 2028Q3 递交；MASH 2027Q2 组织学结果后启动 III 期；慢性肾病与射血分数保留的心衰在 II 期'),
]

def fx(kind, s=0):
    return f' data-kzf-fx="{kind}"' + (f' data-kzf-s="{s}"' if s else '')

def slide(kind, title, inner, notes, **attrs):
    a = ''.join(f' data-kzf-{k}="{escape(str(v))}"' for k, v in attrs.items())
    return f'<section class="slide" data-kzf-kind="{kind}" data-title="{escape(title)}"{a}>{inner}<aside class="notes">{escape(notes)}</aside></section>'

def stage_page(i, comp, title, data, label):
    spec = CAT[comp]; steps = spec['steps']; jobs = ' · '.join(JOBS[j] for j in spec['job'])
    alts = [k for k, v in CAT.items() if k != comp and set(v['job']) & set(spec['job'])]
    stage = (f'<div class="kzf-stage" data-kzf-comp="{comp}" data-kzf-steps="{",".join(steps)}" data-kzf-data=\'{escape(json.dumps(data, ensure_ascii=False), quote=False)}\''
             f' role="img" aria-label="{escape(label)}"><canvas></canvas></div>')
    side = (f'<div class="kzf-stack"><article class="kzf-card"{fx("right")}><div class="kzf-card-head"><h3>{comp}</h3>'
            '<span class="kzf-tag wait">three.js</span></div>'
            f'<p>适用：<b>{escape(jobs)}</b></p>'
            + (f'<p class="kzf-lede">同类可换：{" / ".join(alts)}</p>' if alts else '') + '</article>'
            f'<article class="kzf-card"{fx("right")}><h3>分场</h3><ol class="kzf-steps">'
            + ''.join(f'<li{fx("item")}><i>{k + 1}</i><span><b>{s}</b> {escape(STEP_DOC[comp][s])}</span></li>' for k, s in enumerate(steps))
            + f'</ol><p class="kzf-note">数据：{escape(spec["data"])}</p></article></div>')
    # a wide stage (catalog wide: true — long time axes) takes the whole body; its scene list stays in the notes
    body = f'<div class="kzf-body">{stage}</div>' if spec.get('wide') else f'<div class="kzf-body kzf-split" style="--side:330">{stage}{side}</div>'
    return slide('content', title, body,
                 f'{title}：{label}。', kicker=f'{i:02d} {JOBS[spec["job"][0]]}', chips=f'{comp}|{len(steps)} 场', template='flag-stage')

cover = slide('cover', '封面',
    f'<picture class="kzf-cover-img"><source media="(min-aspect-ratio: 2/1)" srcset="{AS}backgrounds/flagship/cover-wide.jpg">'
    f'<img src="{AS}backgrounds/flagship/cover.jpg" alt=""{fx("fade")}></picture><div class="kzf-sweep"{fx("sweep", 1)}></div>'
    '<div class="kzf-cover">'
    f'<p class="kzf-cover-kick"{fx("rise")}>康哲 Design 8.0 · 旗舰路线</p>'
    f'<h1{fx("rise")}>旗舰舞台<br>组件库</h1><div class="kzf-rule"{fx("grow-x")}></div>'
    f'<p class="kzf-cover-lede"{fx("rise")}>{len(CAT)} 个组件，按内容选用；同一类内容至少两种画法，相邻页不重复</p>'
    '<div class="kzf-chips">' + ''.join(f'<span class="kzf-chip"{fx("item")}>{escape(v)}</span>' for v in JOBS.values()) + '</div></div>'
    f'<p class="kzf-cover-meta"{fx("fade")}>产品中心-医学部 · {DATE}</p>', '旗舰舞台组件库：按内容选组件，同类内容有多种画法。')
ending = slide('ending', '结束',
    f'<div class="kzf-end"><h2{fx("blur")}>谢谢</h2><div class="kzf-rule"{fx("grow-x")}></div><p{fx("rise")}>{TITLE}（合成示例）</p></div>'
    f'<p class="kzf-end-meta"{fx("fade")}>产品中心-医学部 · {DATE}</p>', '谢谢。')
slides = [cover] + [stage_page(i + 1, *p) for i, p in enumerate(PAGES)] + [ending]
assert sorted(p[0] for p in PAGES) == sorted(CAT), 'every catalog component has a gallery page'

VENDOR = ['gsap.min.js', 'DrawSVGPlugin.min.js', 'MotionPathPlugin.min.js', 'CustomEase.min.js', 'three.bundle.min.js']
html = ('<!DOCTYPE html>\n<!-- Built by build.py from tokens.flagship.stages; do not edit by hand. -->\n<html lang="zh-CN">\n<head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{TITLE} · 康哲医学部 · 旗舰</title>\n<link rel="icon" href="data:,">\n<link rel="stylesheet" href="{UP}base.css">\n'
        + ''.join(f'<link rel="stylesheet" href="{RT}{c}">\n' for c in ['kz-tokens.css', 'kz-glass.css', 'kz-flagship.css'])
        + f'</head>\n<body class="kz kzf" data-fit="fluid" data-kzf-title="{TITLE}（合成示例）">\n<div class="deck">\n' + '\n'.join(slides) + '\n</div>\n'
        f'<script src="{UP}runtime.js"></script>\n' + ''.join(f'<script src="{AS}vendor/{m}"></script>\n' for m in VENDOR)
        + ''.join(f'<script src="{RT}{m}"></script>\n' for m in ['kz-tokens.js', 'kz-icons.js', 'kz-clinical.js', 'kz-flagship.js', 'kz-flagship-stages.js'])
        + '<script src="../../../adapters/html-ppt-bridge.js"></script>\n'
        + "<script>(function(){const fx=KZFlagship.mount(document.querySelector('.deck'),{logo:'" + AS + "logo_bot.svg'});"
          "addEventListener('pagehide',()=>fx.dispose(),{once:true});window.KZ_DECK={fx};document.documentElement.dataset.kzDeckReady='true';})();</script>\n"
        + f'<script src="{RT}kz-audience.js"></script>\n</body></html>\n')
(HERE / 'index.html').write_text(html, encoding='utf-8')
print('wrote', HERE / 'index.html', len(slides), 'slides')
