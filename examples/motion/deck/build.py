#!/usr/bin/env python3
"""HTML-PPT demo template deck (15 DEMO-07): one slide per demonstrative form, the four demo presets in rotation.

Reuses the reference deck's scaffold, chrome and wiring (examples/reference/htmlppt/build.py: hero, body, demo_page,
write_deck; deck.css; deck.js) and the gallery's data (../data.js, window.KZ_MOTION_DATA), so a slide here is the
gallery form at slide size. To reuse one: copy its body(...) call into your deck, put your data under the same key
in KZ_DECK_DATA.demos, and rewrite the reading side and the notes; the stage computes every number from the data.
Run:  python examples/motion/deck/build.py
"""
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('kz_ref_build', HERE.parents[1] / 'reference/htmlppt/build.py')
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
ref.A = '../../reference/assets/'   # backgrounds of the reference decks, seen from this folder
BASE = '../../reference/htmlppt/'   # shared vendor scaffold, deck.css and deck.js

# (kind, preset, title, reading side, notes with one 【n】 per scene)
PAGES = [
    ('flow', 'demo-mirror', '资料核查流程', ['5 个环节逐一核对，规则写在环节下方', '不合格<b>退回返工</b>；反复不合格<b>升级医学审核</b>', '每个环节累计问题数，找出最常出错的一环'],
     '【1】每份资料依次过 5 个环节，每个环节下面写着核对规则。【2】资料 A 是正例，各环节一次通过，直接入库。'
     '【3】资料 B 缺研究者签字，退回签字核对，补签后再往下走，最后入库，返工一次。'
     '【4】资料 C 是复杂反例：补签之后，原始记录比对又两次不一致，这时不再无限返工，升级医学审核。'
     '【5】合计入库 2 份、返工 3 次、升级 1 份，问题集中在签字核对。'),
    ('gantt', 'demo-wide', '核对计划推进', ['依赖关系决定排期', '一项延误怎样传导到里程碑', '追赶方案能挽回多少'],
     '【1】这是 12 个月的核对计划，6 项任务，带依赖关系，数据锁定原定 9 月。【2】现在是 3 月，补收资料和版本确认都在进行中。'
     '【3】补收资料因为两家中心延迟回传，要晚 2 个月，后面 4 项顺延，数据锁定推到 11 月。'
     '【4】关键路径是补收资料、安全性核对、审阅意见、数据锁定，这条线上任何一项再晚，锁定都会再推迟。'
     '【5】PV 增派一人，安全性核对压缩 1 个月，数据锁定回到 10 月，仍比原计划晚 1 个月。'),
    ('swimlane', 'demo-stack', '问题单跨部门流转', [],
     '【1】一张问题单要经过研究中心、医学部、PV、数统四个部门。【2】研究中心提交、医学部初审，前两段用了 3 天。'
     '【3】PV 安全性评估用了 4 天，超出时限 2 天；数统核对 1 天，累计 8 天。'
     '【4】医学部答复、研究中心关闭，总共 10 天。【5】比时限多 2 天，最慢的一段是安全性评估。'),
    ('matrix', 'demo', '核对风险评估', ['影响程度 × 发生可能性，各 3 档', '评分 ≥ 6 为<b>高风险</b>', '措施落实后重新落位'],
     '【1】风险矩阵按影响程度和发生可能性各分三档，评分 6 分以上为高风险。【2】5 项风险按评估落位。'
     '【3】高风险 3 项：中心资料延迟回传、版本口径不一致、签字缺失。【4】采取措施后，各项重新落位：每周催收、双人比对、交叉核对 PV 库、入库前核查。'
     '【5】高风险从 3 项降到 1 项，中心资料延迟回传仍需跟踪。'),
    ('curve', 'demo-wide', '核对清单实施后的完整率', ['同一刻度比较两类中心', '目标线与达标时点', '缺失时点不连线'],
     '【1】先看新流程中心，完整率从基线 62% 升到第 24 周 95%。【2】原流程中心同一刻度，从 60% 到 75%。'
     '【3】目标是 90%，新流程中心有 2 个时点达到，原流程中心没有达到。【4】第 16 到 24 周，第 24 周两者相差 20 个百分点。'
     '【5】第 8 周启用了核对清单；第 20 周新流程的数据缺失，图上不连线，不按零处理。'),
    ('breakdown', 'demo-mirror', '应收资料的构成', ['240 份应收资料分 4 部分', '中心记录占一半，<b>拆开看缺口</b>', '缺签字的记录放回总量看占比'],
     '【1】应收资料 240 份。【2】分成 4 部分，中心记录最大，占一半，其次是实验室数据。'
     '【3】聚焦中心记录，120 份。【4】中心记录里完整的 90 份，缺研究者签字 18 份，缺页 12 份。'
     '【5】放回总量看，缺签字的 18 份占全部应收资料的 8%。'),
    ('consort', 'demo-stack', '受试者流向', [],
     '【1】筛选 420 例，屏幕上一个点代表 10 例。【2】排除 90 例：不符合入选标准 60 例、撤回知情同意 20 例、其他原因 10 例。'
     '【3】随机化 330 例，试验组 166 例，对照组 164 例。【4】试验组脱落 14 例，对照组脱落 13 例，原因分别列出。'
     '【5】进入分析：试验组 152 例，对照组 151 例，都是 92%。'),
    ('audit', 'demo', '中心记录逐项核查', ['9 个字段分组核对', '不符项连同规则<b>复制到发现清单</b>', '最后给出相符率，转交中心更正'],
     '【1】这是一份中心记录核查表，9 个字段待核。【2】前三个字段里，研究者签字缺失，记入发现清单，规则是须签字并注明日期。'
     '【3】入组日期到第 4 周访视，全部相符。【4】合并用药没有记录剂量，实验室报告缺第 8 周，两项记入发现清单。'
     '【5】9 个字段 6 个相符，相符率 67%，3 项转交中心更正。'),
    ('network', 'demo-mirror', '数据流转与中断', ['研究中心经 EDC 与 CRO 流向数统和 PV', '数据包逐份沿路径送达', '一条通道中断，<b>受阻数据不进下游</b>'],
     '【1】研究数据从中心出发，经 EDC 和 CRO 流向数统和 PV 库。【2】访视数据沿研究中心、EDC、CRO 到数统，送达。'
     '【3】实验室结果从中心实验室传 EDC 时，接口字段不匹配，卡在这条通道上。'
     '【4】SAE 报告经 EDC、CRO 送达 PV 库。【5】3 份数据送达 2 份、受阻 1 份；通道修好之前，受阻的数据不进入下游。'),
    ('schedule', 'demo-wide', '访视窗口依从', ['4 次访视各有允许窗口', '逐个受试者落点', '超窗与缺访按方案偏离记录'],
     '【1】4 次访视，各有允许窗口：V1 是 0 到加 2 天，V4 是正负 7 天。【2】受试者 01 的 4 次访视都在窗口内。'
     '【3】受试者 02 的 V3 晚了 2 天。【4】受试者 03 的 V2 晚 4 天，V3 缺访，V4 晚 2 天。'
     '【5】12 次访视里窗口内 8 次、超窗 3 次、缺访 1 次，超窗和缺访都按方案偏离记录。'),
]

TOTAL = len(PAGES) + 2
FOOT = ref.FOOT
slides = [ref.hero('cover', {'title': '演示动画模板组', 'subtitle': '合成示例｜十种数据驱动的演示形式', 'meta': FOOT, 'title_short': '封面'}, 'cover.webp',
                   '这组演示页模板用合成数据，每页舞台随翻页键逐步推进，数字都由数据算出。')]
for n, (kind, preset, title, items, notes) in enumerate(PAGES, start=2):
    slides.append(ref.body(n, TOTAL, title, preset, ref.demo_page(kind, title, items, preset=preset), notes))
slides.append(ref.hero('ending', {'title': '换上自己的数据', 'subtitle': '复制一页、替换数据与讲稿，舞台自动重新计算', 'meta': FOOT, 'title_short': '结束'}, 'ending.webp',
                       '复制需要的页和它的数据，换成自己的内容，舞台上的数字和说明会按新数据重新计算。'))

if __name__ == '__main__':
    ref.write_deck(slides, '{"demos": window.KZ_MOTION_DATA}', HERE / 'index.html', '演示动画模板组', base=BASE, data_scripts=['../data.js'])
