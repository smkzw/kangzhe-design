"""8.0 clinical-report scenario families (static page templates). One data contract per scenario feeds four products:
this template (PPTX + HTML-PPT regular), the regular demo form (KZDemo), the flagship three.js stage and the flagship PPTX
page. The contract and its checks live in the diagram kind (diagram_clinical.safety_model …), so all products agree."""
from .. import pattern
from ..tree import Card, Row, Stack, Text, Figure
from .clinical import _insights, _close

# ---------------------------------------------------------------- 安全性总览
@pattern('safety-overview', scene='临床试验', title='安全性总览（TEAE / TRAE / ≥3 级 / TESAE / TRSAE / AESI / 停药 / 死亡）', density='高',
         family='data', tiers=('standard', 'dense'),
         use='安全性分析集各组的不良事件类别：每类一行，子类缩进在上级之下，n (%) 由例数与 N 算出，共用 % 刻度的条形与差值列（pp）；'
             'layout: butterfly（两组，治疗组左翼、对照组右翼）| grouped（2–4 组）；右侧 2–3 条解读；数据合同与常规演示 safety、旗舰舞台 safety 共用')
def safety_overview(d):
    spec = {**d['safety'], 'layout': d.get('layout', d['safety'].get('layout', 'butterfly'))}
    fig = Card([Figure('safety', spec, min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d)
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [2.4, 1]), gap=18, flex=1) if side else fig, d)

# ---------------------------------------------------------------- 临床开发计划（甘特 + 里程碑）
@pattern('program-plan', scene='临床试验', title='临床开发计划甘特（多适应症 · 关键里程碑 / 单适应症 · 细化节点）', density='高',
         family='plan', tiers=('standard', 'dense'),
         use='季度轴上的泳道：多适应症总图一条泳道一个适应症、阶段前后相接、只放关键性里程碑（顶线、递交、获批）；单适应症细化页一条泳道一项研究，'
             '放首例入组、末例入组、锁库、顶线等节点。阶段色由浅到深（I 期 → 上市后），当前线之后画成计划（浅色虚线），过去的里程碑实心、未来空心；'
             '阶段交叠（II 期未完 III 期已启动）时拆子泳道（parent），源日期照写不改；'
             '两种版式：默认不写 insights，整页只放甘特，宽度全给时间轴，要点写进讲稿；只有计划页单独成篇、讲稿不承载解读时才在右侧放 2–3 条解读；数据合同与常规演示 program、旗舰舞台 program、可编辑甘特共用')
def program_plan(d):
    from ..diagram_clinical import bind_text
    fig = Card([Figure('program', d['program'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d, bind=lambda s, marked: bind_text(s, d['program'], marked))
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [3.1, 1]), gap=18, flex=1) if side else fig, d)

# ---------------------------------------------------------------- 多适应症暴露例数汇总
@pattern('exposure-summary', scene='临床试验', title='暴露例数汇总（多适应症 · 按暴露时长档 · 人年 · 对照目标）', density='高',
         family='data', tiers=('standard', 'dense'),
         use='各适应症或研究的暴露人数按累计时长档（任何暴露、≥26 周、≥52 周 …，长档是短档的子集）逐行列出，嵌套条由浅到深，'
             '右侧是每档例数与人年；底部合计对照暴露目标（如 ICH E1），达到为绿、未达为红并写差额；右侧 2–3 条解读；'
             '数据合同与常规演示 exposure、旗舰舞台 exposure、旗舰 PPTX flag-exposure 共用')
def exposure_summary(d):
    fig = Card([Figure('exposure', d['exposure'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d)
    return _close(Row([fig, Stack(side, gap=12, justify='fill')], weights=d.get('weights', [2.6, 1]), gap=18, flex=1) if side else fig, d)

# ---------------------------------------------------------------- 累计暴露与 NDA（挂在临床开发计划上，round 9）
@pattern('exposure-plan', scene='临床试验', title='累计暴露与各适应症 NDA（按开发计划累计 · ICH E1 · 达标表）', density='高',
         family='data', tiers=('standard', 'dense'),
         use='领导层快速看：按临床开发计划逐个研究累计研究药物暴露（暴露 = 样本量 × (1 − 对照比例)，计入时点为研究结束），阶梯图上画 ICH E1 目标线、'
             '各适应症 NDA 竖线与 NDA 时的累计（达到 / 差额）、首次达到时点；下方原生表逐适应症列 NDA 时任何暴露、≥26 周、≥52 周是否达标；'
             '不带解读卡（写进讲稿）；数据挂在开发计划合同（program，研究条带 exposure）上，与甘特同一份数据，HTML 按 T 改样本量、对照比例与时间。'
             '源表给了暴露例数就照抄进 exposed（如 2:1 随机写成“33%”时 180 例的暴露是 120，不是 180 × 0.67 = 121），工具算出的合计与源材料不一致时先查 exposed，不改源材料的数字')
def exposure_plan_page(d):
    from ..diagram_scenes import exposure_plan, exposure_readiness_table
    m = exposure_plan(d['exposure_plan'])
    fig = Card([Figure('exposure-plan', d['exposure_plan'], min_h=240, flex=1), Figure('table', exposure_readiness_table(m))],
               title=d.get('title'), justify='fill', gap=10, pad=[20, 14], flex=1)
    return _close(fig, d)

@pattern('exposure-ledger', scene='临床试验', title='暴露规划台账（逐研究 · 累计 · NDA 行 · 首次达到）', density='高',
         family='data', tiers=('standard', 'dense'),
         use='逐研究列样本量、对照比例、暴露例数、计入时点与累计暴露，按计入时点排序，各适应症 NDA 单独成行写当时累计与差额，首次达到 ICH E1 总量的一行标出；'
             '与 exposure-plan 同一份开发计划数据；不带解读卡')
def exposure_ledger(d):
    from ..diagram_scenes import exposure_plan, exposure_ledger_table
    m = exposure_plan(d['exposure_plan'])
    return _close(Card([Figure('table', exposure_ledger_table(m), flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1), d)

# ---------------------------------------------------------------- 试验流程（含子流程）
@pattern('trial-flow', scene='临床试验', title='试验流程（共同阶段 → 随机化 → 各组段落 → 再随机化子流程 → 随访）', density='高',
         family='process', tiers=('standard', 'dense'),
         use='一项研究从筛选到随访的流程：筛选、导入等共同阶段画在全部分组的中线上，随机化节点（R + 比例）分出各组，每组是前后相接的段落'
             '（递增、维持、安慰剂、开放标签、非治疗）；某组再随机化时分出 2–3 个子分组；各组同一周结束后汇入共同随访；终点在时间轴上，'
             '子研究画成虚线条。时间轴分段线性，短的筛选期不被压扁；下方 2–3 条解读；数据合同与常规演示 trialflow、旗舰舞台 trialflow、旗舰 PPTX flag-trialflow 共用')
def trial_flow(d):
    fig = Card([Figure('trialflow', d['trialflow'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d)
    return _close(Stack([fig, Row(side, gap=18)], gap=18, justify='fill', flex=1) if side else fig, d)

# ---------------------------------------------------------------- 竞争格局（研发进度 · 有效性 · 安全性）
@pattern('landscape', scene='临床试验', title='竞争格局（研发阶段 · 有效性 · 安全性，本品与竞品同表）', density='高',
         family='compare', tiers=('standard', 'dense'),
         use='本品与竞品逐行列出：名称、公司、机制与给药方式；研发阶段画成到当前阶段为止的色块轨；一个有效性指标、一个安全性指标各自一列条形，'
             '表头写指标名、单位与“越高 / 越低越好”，每列最佳值深橙加粗，无数据写“—”（不当 0）；本品行着色；按阶段再按有效性排序；'
             '≤4 个药物时下方 2–3 条解读，5–8 个不带卡（要点进讲稿），>8 个改用 landscape-pipeline / -efficacy / -safety 三页；竞品一律合成或经核实的公开数据（跨研究比较写明局限）；数据合同与常规演示 landscape、旗舰舞台 landscape、旗舰 PPTX flag-landscape 共用')
def landscape(d):
    # round 9 tiers: ≤ 4 assets keep the insight cards; 5–8 drop them (the points go into the notes); > 8 split into
    # landscape-pipeline / landscape-efficacy / landscape-safety
    n = len(d['landscape'].get('assets') or [])
    if n > 8: raise ValueError(f'竞争格局 {n} 个药物：超过 8 个时分三页——landscape-pipeline（研发格局）、landscape-efficacy（有效性）、landscape-safety（安全性）')
    fig = Card([Figure('landscape', d['landscape'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d) if n <= 4 else []
    return _close(Stack([fig, Row(side, gap=18)], gap=18, justify='fill', flex=1) if side else fig, d)

# ---------------------------------------------------------------- 竞争格局（竞品多，分三页，round 9）
_LS_MANY_USE = '同一份竞争格局合同（assets ≤30，另加每个药物 trial:{name, weeks, n}、detail:{安全性指标 key: 值}，以及 safety_detail:[{key, label, unit, better}]）分三页：'

@pattern('landscape-pipeline', scene='临床试验', title='竞品研发格局（机制 × 研发阶段看板，竞品多时第 1 页）', density='高',
         family='compare', tiers=('standard', 'dense'),
         use=_LS_MANY_USE + '这一页按机制分行、研发阶段分列，每个药物一枚胶囊（名称 + 公司），本品实心品牌色、重点描边；每个药物只出现一次；不带解读卡')
def landscape_pipeline(d):
    return _close(Card([Figure('landscape-pipeline', d['landscape'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1), d)

@pattern('landscape-efficacy', scene='临床试验', title='竞品有效性对比（按疗效排序 · 研究出处 · 竞品多时第 2 页）', density='高',
         family='compare', tiers=('standard', 'dense'),
         use=_LS_MANY_USE + '这一页只列有疗效数据的药物，按疗效从好到差排序：名称与公司、阶段、研究出处（研究名 · 周数 · 例数）、同一尺度的条形与数值（最佳深橙），'
             '无数据的药物在图下点名（不当 0）；跨研究比较的局限写进脚注；不带解读卡')
def landscape_efficacy(d):
    return _close(Card([Figure('landscape-efficacy', d['landscape'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1), d)

@pattern('landscape-safety', scene='临床试验', title='竞品安全性对比（多指标矩阵 · 竞品多时第 3 页）', density='高',
         family='compare', tiers=('standard', 'dense'),
         use=_LS_MANY_USE + '这一页一行一个药物、一列一个安全性指标（safety_detail，缺省用 safety），格子按本列好坏由浅到深着色，每列最佳深橙加粗，无数据写“—”；不带解读卡')
def landscape_safety(d):
    return _close(Card([Figure('landscape-safety', d['landscape'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1), d)

# ---------------------------------------------------------------- 有效性汇总（连续 / 二分类 / 多组对比）
@pattern('efficacy-summary', scene='临床试验', title='有效性汇总（各类终点 · 各治疗组对对照 · 带解读或整页）', density='高',
         family='data', tiers=('standard', 'dense'),
         use='主要与次要终点逐行列出各组数值（均值变化；比例与 n/N；时间事件写中位时间，源材料给了事件数才写 events/n，不推算；事件率），'
             'better 指效应值（差值或比值）朝哪边有利：降低为好的量写 lower，至应答等有利事件 HR > 1 有利写 higher，至复发、死亡等不利事件写 lower；'
             '治疗组按剂量由低到高列（颜色由浅到深，高剂量最深）；每个治疗组对对照的效应与 95% CI 画成小森林图：'
             '一节一轴——均值差、率差（百分点）各一条含 0 的轴，HR / OR / RR / 率比共用一条含 1 的对数轴；节标题只写效应量与单位，不写数据类型；'
             'CI 不跨参考值且方向有利为实心、跨参考值为空心、方向不利为红；估计值（比值前写 HR 等）与 P 值列在右侧；率差必须与 n/N 一致（校验）；'
             '两种版式：下方 2–3 条解读（终点 ≤6），或不写 insights 整页（终点多、画面密时用，要点写进讲稿）；'
             '数据合同与常规演示 efficacy、旗舰舞台 efficacy、旗舰 PPTX flag-efficacy 共用')
def efficacy_summary(d):
    fig = Card([Figure('efficacy', d['efficacy'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=8, pad=[20, 14], flex=1)
    side = _insights(d)
    return _close(Stack([fig, Row(side, gap=18)], gap=18, justify='fill', flex=1) if side else fig, d)


# ---------------------------------------------------------------- 历时变化（round 9：有效性与安全性客观指标）
_LONG_USE = ('合同 longitudinal（diagram_long.py = KZClinical.longitudinal）：visits 带真实研究时间 t（不等距照实排，不按访视序号），每组每访视 [估计, 下限, 上限, n]，'
             'measure.interval 写明 95% CI / SE / SD / IQR；null 是缺失（断线，不当 0）；盲态写 blinded: true，只有一条全体序列、不分组、不做组间差，标“仅限内部”；')

@pattern('longitudinal', scene='临床试验', title='历时变化（各组或盲态全体 · 真实时间轴 · 各访视 n）', density='高', family='data', tiers=('standard', 'dense'),
         use=_LONG_USE + '各组估计 ± 区间按访视画在真实时间轴上，同一访视各组轻微错开，主要终点访视淡底，参考线 / 参考范围，轴下逐组列 n；'
             'with_diff 时下方加组间差（各治疗组对对照之差与 95% CI，参考 0）；HTML 点数据点下钻出历时表并高亮该格，可在表里改数；不带解读卡')
def longitudinal_page(d):
    spec = d['longitudinal']; kids = [Figure('longitudinal', spec, min_h=0, flex=1.6 if d.get('with_diff') else 1)]
    if d.get('with_diff'): kids.append(Figure('longitudinal-diff', spec, min_h=0, flex=1))
    return _close(Card(kids, title=d.get('title'), justify='fill', gap=10, pad=[20, 14], flex=1), d)

@pattern('lab-boxplot', scene='临床试验', title='检验指标历时分布（箱线 · 各组 · ULN 与参考范围）', density='高', family='data', tiers=('standard', 'dense'),
         use=_LONG_USE + '实验室指标偏态、关注尾部：每访视每组一个箱（须、Q1–Q3、中位数），ULN 参考线与参考范围绿带，轴下各访视 n；measure.interval 写 box、数据写 boxes')
def lab_boxplot_page(d):
    return _close(Card([Figure('lab-boxplot', d['longitudinal'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=10, pad=[20, 14], flex=1), d)

@pattern('lab-multiples', scene='临床试验', title='安全性检验与生命体征小倍数（多指标 · 各自刻度 · 参考范围）', density='高', family='data', tiers=('standard', 'dense'),
         use=_LONG_USE + '2–9 个指标各占一格（共用访视与组，各自刻度与参考范围），一行图例；适合安全性检验与生命体征总览；单个指标要细看时下钻或改用 longitudinal')
def lab_multiples_page(d):
    return _close(Card([Figure('lab-multiples', d['lab-multiples'], min_h=0, flex=1)], title=d.get('title'), justify='fill', gap=10, pad=[20, 14], flex=1), d)

@pattern('completeness', scene='临床试验', title='各访视数据完整性（应到 · 仍在研究 · 有数据，盲态可用）', density='中', family='data', tiers=('standard',),
         use=_LONG_USE + '每个访视三层柱：应到人数（框）、仍在研究（浅）、有该指标数据（实），柱顶写有数据比例；盲态与揭盲都可用（FDA STF-IG 图 11）；需要 expected 与 in_study；卡标题取 completeness_title（缺省用 title），同一份数据可同时做历时页与本页')
def completeness_page(d):
    title = d.get('completeness_title') or d.get('title')   # one data file can feed the change page and this page under its own title
    return _close(Card([Figure('completeness', d['longitudinal'], min_h=0, flex=1)], title=title, justify='fill', gap=10, pad=[20, 14], flex=1), d)
