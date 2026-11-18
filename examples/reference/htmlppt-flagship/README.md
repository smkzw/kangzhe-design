# HTML-PPT 旗舰参考实现（14，F1）

素材与 `../htmlppt/`、`../pptx-flagship/` 相同（研究资料完整性核对，合成数据），共 13 页：封面、目录、四张章节页、六张内容页、谢谢。六张内容页各用一个旗舰版式（FLAG-08），连续两页不重复：

| 页 | 版式 | 内容 |
|---|---|---|
| 核对范围与资料分组 | `flag-cols` | 三张并列卡＋底部衔接带 |
| 资料核对六步 | `flag-flow` | 六步表头＋逐列卡片 |
| 四组资料到位全景 | `flag-stage` | three.js 资料台（`platforms` 组件）＋侧栏 |
| 各资料组应收与已收 | `flag-chart` | ECharts 柱图＋KPI＋补收清单 |
| 差异处理闭环 | `flag-cycle` | 环形节点＋轨道脉冲 |
| 核对计划 | `flag-gantt` | 季度甘特＋关键节点＋里程碑 |

## 构建与放映

- **构建**：`python3 build.py` 从 `scaffold.html`（html-ppt-skill `new-deck.sh` 原始输出）派生 `index.html`，同时写出 `page-plan.json`。上游 `base.css` 与 `runtime.js` 原样随包（`vendor/html-ppt/assets/`）。
- **品牌层**：`runtime/kz-flagship.css/js`。页面只写内容和声明式动效标记（`data-kzf-fx` 动作、`data-kzf-s` 场次、`data-kzf-comp` 组件），运行时补上页眉（图标块、眉题、标题、Logo、信息胶囊）、进度段与页脚，并把标记编成每页的 GSAP 场景时间线（FLAG-04/06）。`deck.js` 只做装配；`deck.css` 没有规则，版式全部来自运行时。
- **背景**：只用旗舰背景组两张图：封面 `cover.jpg`，其余页 `canvas.jpg`（FLAG-03）。
- **放映**：用 Microsoft Edge 或 Chrome 打开 `index.html`。→ 在本页推进一场，本页最后一场之后再按 → 才翻页；← 退回上一场，退到上一页时直接显示该页最后一场。无人操作时各场依次自动播完。S 演讲者窗口、O 总览与上游一致。

## 已知限制

- O 总览的缩略图来自上游在初始化时克隆的页面，其中图表与甘特为空（常规路线相同）。
