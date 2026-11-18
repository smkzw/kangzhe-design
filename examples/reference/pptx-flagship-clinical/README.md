# 旗舰 PPTX 临床模板参考（14 FLAG-12，语言 L1「层叠纸板」）

九个旗舰 PPTX 正文模板各一页，框架（棱面页眉、Logo、胶囊、进度段、页脚）与 `../pptx-flagship/` 相同，正文由 `tools/kz_layouts/flagship_pptx.py` 生成，数据读临床场景族合同（`examples/templates/safety-overview.json`、`program-plan.json`、`exposure-summary.json`、`trial-flow.json`、`landscape.json`、`efficacy-summary.json`、`soa.json`），数字与静态模板、常规演示、旗舰舞台一致。

| 页 | template | 内容 |
|---|---|---|
| 1 | `flag-safety` | 蝶形纸条：治疗组向左、对照组向右，凹槽底轨；差值 ≥ 阈值标签；右侧三张洞察页签（立体图标 + 两组率） |
| 2 | `flag-program` | 开发计划：泳道卡 + 错位底纸，阶段为棱面箭头（当前线前实色、后浅色虚线），双色棱面宝石里程碑，当前线灰色虚线垫底；下方三张洞察页签 |
| 3 | `flag-safety-dumbbell` | 主张列（焦点差值大号渐变数字 + 编号要点）+ 画布上的哑铃点图与差值列 |
| 4 | `flag-program-strip` | 同一计划画成凹槽里的立体纸条 |
| 5 | `flag-exposure` | 暴露阶梯：每个适应症一条凹槽，累计时长档由浅到深叠成台阶，右列例数与人年、合计行；右侧 ICH E1 目标卡（合计大数字、目标刻度量尺、达到/差额标签）；下方三张洞察页签 |
| 6 | `flag-trialflow` | 研究流程：周轴分段线性与终点宝石；筛选、导入、随访是横跨各行的高纸板；随机化圆片分到各组，KZ-001 组 W36 再随机化为两个子分组；CGM 子研究虚线胶囊；下方三张洞察页签 |
| 7 | `flag-landscape` | 竞争格局：七个药物（竞品合成）按阶段排序，本品行着色；阶段棱面箭头；体重降幅与胃肠道不良事件两列凹槽纸条，最佳值深橙，无数据写“—”；下方三张洞察页签 |
| 8 | `flag-efficacy` | 有效性汇总：只放主要与关键次要终点（4 个）；两个剂量与安慰剂列，连续变量与二分类各一段差值轴（含 0）；每个治疗组一条从 0 伸出的纸条加 95% CI 须线，右列差值与 P；下方三张洞察页签 |
| 9 | `flag-soa` | 访视流程概览：分期棱面箭头覆盖访视列；四个分组 × 12 次访视的立体纸圆片（大小 = 项目数）；HbA1c 重点条；每次访视评估数纸条（V3 最忙 13 项）；下方三张洞察页签 |

```
PM=~/.claude/skills/ppt-master; PY=python3   # ppt-master 依赖所在的 Python
python3 examples/reference/pptx-flagship-clinical/build_svg.py <项目>
$PY $PM/scripts/svg_quality_checker.py <项目> --canonical-authoring --stage final --quick-generate --json
$PY $PM/scripts/svg_to_pptx.py <项目> --quick-generate --no-notes --animation-config <项目>/animations.json -o kangzhe_flagship_clinical.pptx
$PY $PM/scripts/pptx_delivery_check.py kangzhe_flagship_clinical.pptx
python3 examples/reference/pptx-flagship/readback.py kangzhe_flagship_clinical.pptx
python3 tools/qc_plan.py <项目>/page-plan.json
python3 tools/check_kz_project.py <项目> --plan <项目>/page-plan.json --pptx kangzhe_flagship_clinical.pptx
```
