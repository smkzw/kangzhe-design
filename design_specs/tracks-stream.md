# 流式 HTML 轨道

按文档或电子书阅读组织章节，有固定目录与章节锚点，不是一串 16:9 幻灯片，也不使用双菱形。

## 步骤
1. **计划**：事实清单 → 章节树 → page-plan（`track: stream`，`body_profile: responsive`，`target_viewports` 取 `tokens.viewports.stream`）→ 首页与一级章节入口的 film-plan 或 `fold_stage` 理由 → `tools/qc_plan.py`。
2. **资产**：首页首屏用生成主视觉或程序化光场（04 IMG-01）。
3. **页面**：固定玻璃页眉（13 WIDE-01），首页 Bento 首屏，正文为“目录轨 · 宽正文栏”两栏（13 FOLD-05），章节 `data-kz-section` 入场，明细下钻；接线与站点式相同，用 runtime/API.md 的组件自己装配；参考实现 `examples/reference/stream/index.html` 借用了示例工程 `examples/reference/site/site.js` 的 `KZRefSite.mount('home')`，那是示例代码，不是 runtime 接口，项目里不必引入。
4. **验收**：同站点式，另验目录高亮随阅读位置变化、打印保留全文。

## 要点

- 文档首页：13 FOLD-01/02 的 Bento 首屏，电影建立全文结构概览；一级章节入口有章节电影或章节首区块。
- 正文：“左侧目录轨 · 正文栏”两栏（13 FOLD-05），没有右侧栏、不放要点数字或口径说明侧注；段落行长上限 `--kz-stream-measure`，图表、表格、卡片占满正文栏，图表与说明卡用 `.kz-stream-wide` 并排且等高；逐屏密度按 13 FOLD-07 验收；章节首次可见时入场；目录随阅读位置高亮。正文允许自然高度，不把所有段落包成等高卡。
- 下钻：一级卡是摘要，二级容器可有多卡、多图和原文，必要时三级；弹窗宽度与内容密度匹配。
- 电影离屏停帧，阅读下方段落时后台不持续耗资源。
- 侧注、正文卡与下钻面板没有全高或全宽的边缘色条（02 LG-02）；侧注靠位置与小标题区分，不靠左侧色条。
- 引用按 03 COPY-05；标题是内容名称，观点放在导语或结论段。
- 打印保留全文与关键明细，不让折叠后只剩标题。
- 验收视口 `tokens.viewports.stream`（含 3440×1440），每档视口跑 `inspectWidth`（13 WIDE-01）；没有人声讲解任务时不写讲稿，G7-NOTES 写 N/A 与原因。

参考实现：`examples/reference/stream/index.html`。

甘特：加载 `kz-icons.js`、`kz-clinical.js`、`kz-gantt.js`、`kz-gantt-studio.js`（runtime/API.md），按 T 打开全页编辑台（08 GANTT-01）。要“保存到本文件”，甘特数据须放在页面的 `window.KZ_DECK_DATA[gid]` 数据块里并在根元素写 `data-kz-gantt="<gid>"`；否则保存菜单只给导出、复制、导入与草稿（08 GANTT-05）。

临床数据图（round 9）：
- **加载**：在 `kz-charts.js`、`kz-gantt.js`、`kz-clinical.js`、`kz-drilldown.js` 之后加载 `kz-explore.js`。KZCharts 遇到 `exposure-plan` 与历时变化各 kind 会转交给它（05 CHART-06，08 GANTT-08）。
- **共享计划**：甘特与累计暴露放在同一页时，用同一个 `program.id`，数据放在 `window.KZ_DECK_DATA`。
- **静态临床模板**：有效性汇总、SoA、试验流程、竞争格局三页（pipeline / efficacy / safety）、暴露汇总等在 HTML 里同样用模板库：`kz_layout.py render <模板> data.json --track html --out frag/` 写出卡片内标记与 frag/charts.json（并进 `KZ_DECK_DATA`，键名不改），放进整行卡（流式：正文栏里的整宽卡，不用 `.kz-stream-wide` 并排），一行一个模板，不并排两张（并排时示意图按卡宽整体缩小，字小到读不出，`inspectTextFloor` 会报）。不要自己拼 ECharts 条形图代替竞争格局模板（药名要在轴上或行首，不只放在图例里）；演示舞台（kz-demo-clinical）只在需要逐 scene 讲解时用，放置宽度见 15 DEMO-03。用演示舞台时按 15 DEMO-07 的加载顺序引入整条链（kz-scenes → kz-icons → kz-demo → kz-demo-patterns → kz-demo-fine → kz-demo-clinical），缺一个就挂不上。模板片段的长度单位与字号在本轨由 kz-layouts.css 按卡宽给定（`--kz-u` = 卡宽 / 1168，字号同一比率），不要自己按 innerHeight/720 写比率或另加下限，也不加载 html-ppt-bridge。每个模板用各自的 `--out` 目录渲染（文件都叫 slide_NN.html，同目录会互相覆盖），再把各目录的 charts.json 并进同一个 `KZ_DECK_DATA`。
- **参考页**：`examples/reference/site/clinical.html` 与 `examples/reference/stream/clinical.html`，由 `examples/reference/site/build_clinical.py` 生成。
