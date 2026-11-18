# 13 首屏、页面构图与信息密度

页面空间优先放信息：不留大面积空舞台，同一信息不在多处重复，首屏一屏放下，不靠留白“显高级”。

## 验收视口 FOLD-04
视口是**浏览器可视区**（CSS 内容区），不是屏幕分辨率。矩阵在 `tokens.viewports`：

| 视口 | 对应环境 |
|---|---|
| 1920×940 | 1920×1080 屏、100% 缩放、浏览器最大化（无书签栏） |
| 1920×1080 | 同屏 F11 全屏或放映 |
| 1536×730 | 1920×1080 屏、Windows 125% 缩放（企业笔记本常见） |
| 2560×1080 | 超宽显示器 |
| 3440×1440 | 34 英寸超宽带鱼屏（站点式、流式） |
| 1280×720 | 下限 |

HTML-PPT 按前五档验收；站点式与流式另加 3440×1440，共六档（站点式不做手机适配）。浏览器开着书签栏时 1080 屏的可视区约 1920×910，介于 1920×940 与 1536×730 的高宽比之间，不单列。HTML-PPT 低于 720 高度时整页按同一比率等比缩小（adapter 的单一比率），文字不会比框大。

## 首屏一屏放下 FOLD-01（站点式、流式）
站点首页与流式文档首页的首屏，在每个验收视口内**不滚动就完整呈现**：主题、导航、关键事实和首屏电影都在视口内，不被切。

- 页头是固定玻璃页眉 `.kz-site-head`（WIDE-01），Logo、站点名或面包屑、导航在同一行，不各占一行；高度按 `wide.header_px` 分档（1920 档 64px，即 `layout.fold.header_max_px`；≥2200 宽 72px；≥3000 宽 80px）。首屏 `.kz-fold` 占页眉以下的整屏。
- 不在首屏下方重复电影里的同一组信息（以前的“静态总览”卡）；电影的节点、状态条与左栏要点合起来就是静态总览。
- 可视区高度 ≥ `layout.fold.tall_detail_min_height_px`（1000px）时，可以显示 `.kz-detail-tall` 次要说明（KPI 补充、短表），前提是同样内容在页面其他位置完整可得；矮视口不显示，不溢出。断点只是前提：内容量不同，同一高度未必放得下，所以挂载首屏时调用 `KZMotion.fitFold(fold)`，它按文档倒序逐个收起 `.kz-detail-tall`，直到首屏放下，并在尺寸变化时重算。
- 矮视口（≤ `layout.fold.kpi_single_row_max_height_px`，820px）四个 KPI 排成一行，避免把左栏挤出首屏。这两个断点写在 CSS 媒体查询里（媒体查询读不到变量），由单测核对与 tokens 一致。

## Bento 首屏 FOLD-02
12 栏网格，左 4 栏为导读，右 8 栏为电影舞台（`layout.fold.lead_columns / stage_columns`）。宽而矮的视口（宽高比 ≥ `layout.fold.wide_split.min_aspect` 且宽 ≥ `min_vw`（2200px，如 2560×1080、3440×1440））改为 5/7：这时舞台本来就比内容需要的宽，多出的一栏给左栏放信息（实测 3/9 让舞台更空，4/8 在 2560×1080 下左栏下方留出一整条空带）。间距 `--kz-fold-gap`，页边 `--kz-gutter`（WIDE-01）。

KPI 的形态按左栏**自身宽度**决定（容器查询 `kz-lead`，阈值 `layout.fold.lead_kpi`）：左栏 < 900px 时 2×2、数字在上；900–1200px 时仍 2×2，但数字与标签并排，每张卡矮约三分之一，把空间让给 `.kz-detail-tall`；≥1200px 时四张一行，补充说明只在顿号处断行。同一行的 KPI 卡等高。

左栏（自上而下）：
1. 页面标题（h1）与一句导语（`kz-lede`，行长 ≤ `layout.fold.lede_max_em`）；
2. 2–4 个 KPI 卡（数值 + 单位 + 标签，不放裸数字；风险数值按 03 COPY-04 用深红，同时有文字标签说明是风险）。材料没有可量化的关键事实时，改为一条“关键事实条”（2–4 个带标签的短事实），不编造数值；
3. 一张要点卡（3–4 条，含本页最关键的限定），可带进入明细的按钮。

右栏舞台（`.kz-fold-stage`）：
1. 舞台标题行（内容名称，可加“合成演示数据”等必要标注）；
2. 电影（载体在左、关联节点在右，连线表达关系；载体内放该状态的分项事实）；材料不足以构成电影时按 06 FILM-01 改放关系图或图表（page-plan `fold_stage`）；
3. 状态条 `.kz-steps`：已过/当前/未到三态，兼作静态总览与章节导航提示。

参考实现：`examples/reference/site/index.html`、`chapter.html`、`examples/reference/stream/index.html`、`examples/component-lab.html`。

## 密度指标 FOLD-03
`KZLayoutQC.inspectFold(fold)` 在视口上做网格采样（64×36），信息对象（卡片、KPI、状态条、电影载体与节点、标题、导语、导航、可见文字行、图表）覆盖的采样点比例为覆盖率；只有带可见文字或已绘制图形的对象计入，空卡和空舞台不计；全空采样点构成的最大矩形占视口的比例为最大空白。阈值在 `layout.fold`：

- 覆盖率 ≥ `min_coverage`（0.45）；
- 最大空白 ≤ `max_void_ratio`（0.18）；
- 首屏根、信息对象的外框与可见文字都不越出视口（`FOLD_OVERFLOW`）；卡片底边被视口切掉，即使最后一行字还在视口内，也算越出。

阈值是 2026-10-23 的校准起点，2026-10-24 按新口径（只计带信息的对象、外框越出也算）复测：

| 样本 | 覆盖率 | 最大空白 |
|---|---|---|
| 6.1.3 参考站点首页（不合格） | 0.19–0.33 | 0.28–0.37 |
| Bento 原型 | 0.53 | 0.06 |
| 7.0 参考实现，电影初始态（3 页 × 5 档视口） | 0.45–0.53 | 0.07–0.13 |
| 7.0 参考实现，静态帧 | 0.50–0.60 | 0.04–0.11 |

初始态是电影最小的状态，1920×940 下三页都贴近 0.45；静态帧普遍高出 0.05。提高阈值前，先让初始态的舞台携带更多信息（例如首状态就显示分项事实），不要靠放大空载体凑数。电影的初始态和静态帧（`staticProgress`）都要测；指标通过不代替视觉审阅。

## 下方阅读区 FOLD-05
首屏以下与非首页的全部内容放进密排网格 `.kz-sheet`（FOLD-06）；段落入场用 `data-kz-section`，首次进入视口时触发（06 MOTION-05）。

- **行长**：`--kz-measure`（34em，约 34 个汉字）只约束连续正文，不约束卡片、图表、表格的宽度。
- **流式文档**（用户 2026-11-17 定稿）：两栏，“左侧章节目录轨 `.kz-stream-rail` · 正文栏 `.kz-stream-main`”，**没有右侧栏**，也不放“要点数字和口径说明”一类的侧注。
  - 目录轨宽 `--kz-stream-rail`（`wide.stream_rail`），吸顶在页眉下方，随阅读位置高亮。
  - 正文栏占满其余宽度；段落行长上限 `--kz-stream-measure`（`wide.stream_measure_em`），图表、表格、卡片占满正文栏全宽。
  - 同一章节的图表与说明卡用 `.kz-stream-wide` 并排；并排的卡等高，说明卡要有和图表相当的信息量（短表、步骤），不用一句话配一张大图。
  - 正文栏 ≥1200px 时，整栏宽的两列键值表折成每行两对，短值不留大半张空卡。

## 非首页密排 FOLD-06（站点式、流式）
FOLD-01 的一屏 Bento 首屏只用于站点首页和流式文档首页。章节页、明细页和首页首屏以下的内容按密排组织，纵向空间用来放信息。

- **章节头 `.kz-chapter`**：
  - 页头行：Logo、面包屑、导航；
  - 标题行：左 5 栏放标题和一句导语，右 7 栏放 2–4 个 KPI，排成一行；
  - 整体高度不超过视口的 `layout.dense.head_max_vh`。
- **密排网格 `.kz-sheet`**：
  - 12 栏，`grid-auto-flow: row dense`，块与块之间的间距为 `layout.dense.section_gap_px`；
  - 块宽用 `data-span` 按内容决定：说明卡与表格 4–5 栏，图表、甘特图与演示舞台 7–8 栏或整行；同一行的块等高；
  - 段落标题用 `.kz-sheet-head`，标题和一句说明排在同一行。
- **舞台**：章节有自己的叙事时，电影或演示舞台（15 DEMO）作为网格里的一块，高度不超过 `layout.dense.stage_max_vh`，不再占满一整屏。
- **图表与甘特图按内容定高**：
  - 滚动页的图表按宽度取高，宽高比 `layout.dense.chart_aspect`，超宽屏再放宽 1.25 倍；
  - 甘特绘图区高度 = （`gantt_axis_px` + 任务数 × `gantt_row_px`）× 宽度比例（WIDE-01）；
  - HTML-PPT 仍用构图预设的固定高度。
- **禁止的做法**：
  - 每个段落独占一行，旁边留空；
  - 用固定高度的大卡装几行字；
  - 段落之间留大段空白；
  - 在章节页复制一个满屏的空舞台。

参考实现：`examples/reference/site/chapter.html`（章节头加密排网格）、`index.html` 首屏以下、`examples/reference/stream/index.html`。

## 逐屏密度 FOLD-07
`KZLayoutQC.inspectScroll()` 把页面按视口高度切成连续窗口（最后一个窗口与内容底部对齐，页尾 footer 不计），逐窗计算两个量：
- **墨迹占比**：只计文字行、图表与甘特绘图区、图片、SVG、表格和演示对象，不计卡片外框，所以空卡和半空卡会显出来；
- **最大空白**：没有墨迹的最大矩形占窗口的比例。

阈值在 `layout.dense`：墨迹占比 ≥ `min_ink`，最大空白 ≤ `max_void_ratio`。站点与流式的每个页面在 FOLD-04 的各档视口都要测；首屏窗口另外按 FOLD-03 测。演示舞台在 scene 0 与静态 scene 各测一次。指标通过不代替视觉审阅，标定过程见 token 说明。

## 宽屏 WIDE-01（站点式、流式）
宽屏多出的宽度用来**放更多信息、放大字号**，不让内容只占中间一列。数值在 `tokens.wide`，CSS 由 `tools/build_tokens.py` 生成。

- **页边**：`--kz-gutter` = clamp(`gutter_px[0]`, `outer_gutter_vw`, `gutter_px[1]`)。不用 `max-width` 把整站锁在中间；只有连续正文段落受行长约束。
- **字号与间距随宽度放大**：`--kz-sx` 是随视口宽度放大的 1px（`type_scale`：1920 → 1，2560 → 约 1.19，3440 → 约 1.46，上限 1.5）。站点与流式的字号、间距变量都写成 `calc(N * var(--kz-sx))`；ECharts 图表与甘特在这两条轨上用同一条线算字号（`kz-charts.js` / `kz-gantt.js` 的 `wideUnit`），所以图表文字和正文一起放大。HTML-PPT 仍用自己的 `--kz-un`，不受影响。
- **固定页眉**：`.kz-site-head` 吸顶，左侧 Logo（原件，高 `--kz-logo-h`：28/32/36px）+ 竖线 + 站点名或面包屑，中间导航（当前项高亮），右侧一行元信息（部门 · 合成示例等）。高度 `--kz-site-head-h` 按 `header_px` 分档。所有站点页和流式页用同一个页眉，不各写一套。
- **超宽网格**：视口 ≥ `xl_min_vw`（3000px）时 `.kz-sheet` 由 12 栏换 `sheet_cols_xl`（24）栏，块按 `data-span-xl` 取宽（不写时按 `data-span` 翻倍），一行可以多放一个模块；`data-kz-xl-only` 的块只在超宽屏出现，同样内容须在页面其他位置完整可得。
- **首屏**：FOLD-02 的 5/7 分栏与 KPI 形态。
- **流式**：FOLD-05 的目录轨 + 宽正文栏。
- **宽度验收**：`KZLayoutQC.inspectWidth(root)` 量信息对象（卡片、KPI、图表、表格、电影载体、状态条、目录轨、正文段落、标题、导语）的横向跨度占视口宽的比例，须 ≥ `content_width_min`（0.85）。页眉和宽度 ≥ 视口 90% 的容器不计，所以“全宽外壳里套一列居中窄栏”量出来仍是窄的。每页在 FOLD-04 的每档视口都要量。

参考实现：`examples/reference/site/`、`examples/reference/stream/`；2026-11-17 实测（三页 × 1920×1080 / 2560×1080 / 3440×1440）宽度跨度均为 0.936，首屏覆盖率 0.47–0.52。

## PPT 正文页构图 BODY-01（PPTX / HTML-PPT）
正文区 `tokens.chrome.body`（56/96/1168/564）。先按内容量选预设，再写内容：

| 预设 | 适用 | 要点 |
|---|---|---|
| `cards-3` / `cards-2` | 并列的 2–3 组事实 | 卡片取内容高度、同排等高，整组在正文区垂直居中；可加一行通栏观点句 |
| `split-7-5` | 图表 + 解读 | 左图（数据卡撑满高度），右侧观点句（centered）+ 数值表 |
| `film` | 流程、关系 | 舞台占满宽度，下方状态条 |
| `full` | 甘特、大表 | 单卡撑满正文区 |
| `demo` | 方法、规则、计算、数据、计划的示范（15 DEMO-05） | 左 4 栏阅读卡（内容高度、垂直居中）讲本页结论，右 7 栏演示舞台撑满高度、按 scene 步进 |
| `demo-mirror` | 同上，舞台需要先读（流程、网络、甘特从左读起） | 舞台在左 7 栏，阅读卡在右 4 栏 |
| `demo-wide` | 横向展开的舞台（甘特推进、曲线、泳道） | 上方一行观点句与 2–3 条要点，舞台通栏撑满余下高度 |
| `demo-stack` | 舞台本身信息量足、只需几个结论数字 | 舞台在上撑满，下方一条由舞台数据算出的事实条（`KZDemo.renderFacts`） |

相邻的演示页不重复同一个 demo 预设（15 DEMO-05，`tools/qc_plan.py` 检查）。不要把三条 bullet 放进撑满 564 高的卡里（03 TYPE-02 会判 SPARSE / TOP_HEAVY）；内容少时用 `centered` 或缩短卡高，内容多时拆页。正文区整体占用跨度目标 `layout.content_span_target`（10 G5-SPAN）：内容少的页换一个更合适的模板（BODY-02），或缩短卡高、改行列组合，不用撑满的空壳凑跨度，也不为凑高度给每张卡加一个大数字。参考实现：`examples/reference/htmlppt/`（deck.css 的 `data-preset`）、`examples/reference/pptx/build_svg.py`。

## 正文模板库 BODY-02（PPTX / HTML-PPT）
常规路线的文字、规则、数据、流程、计划类正文页从模板库取版式，不从空白画布手搭卡片。模板把页面数据排成布局树，PPTX 一侧用实测字宽求解几何并写出 ppt-master 合规 SVG（每张卡、每张图表或表格一个顶层组，纵向按 03 TYPE-02 分布），HTML-PPT 一侧输出同一结构的 grid/flex 标记；两轨共用同一份数据。

- 目录：`python3 "$KZ_DIR/tools/kz_layout.py" list`（50 套，按场景分：临床试验、方案讨论、项目汇报、AI 汇报、通用；每套标版式族与适用密度档，见 BODY-03）。每套的数据合同就是 `examples/templates/` 里的示例数据，`kz_layout.py example <模板>` 打印路径；两轨样张：`examples/templates/deck/index.html` 与 `examples/templates/pptx/build.py`。
- 高密度模板：入选/排除标准原文密排（criteria）、访视流程表（soa）、键值表与规则表（kv-table、table-band）、PICOS、终点、伴随用药、讨论题（含路径示意）、研究设计总览、时间窗口、流程 + 解析、高密度甘特、数据图 + 解读（小多图或侧解读）、森林图、KM 曲线、CONSORT、方案比较、KPI 看板、风险矩阵、分层架构。普通场景另有图标网格、编号要点卡、路线图、漏斗、中心辐射、二维象限、观点引述 + 证据，多数带 `layout` 选项（如 3x2 / 2x3 / 4x1、charts-top / chart-side）。
- 选型：先按内容类别选模板（规则原文 → criteria / table-band / kv-table；方法与流程 → process / study-schema / windows；数据 → chart-insight / forest / km / kpi-dashboard；安全性汇总 → safety-overview（两组蝴蝶式或 2–4 组分组，数字由例数与 N 算出）；计划 → gantt-plan / roadmap，临床开发计划 → program-plan（多适应症泳道或单适应症细化节点，各期阶段条 + 里程碑 + 当前线；两种版式：右侧 2–3 张解读卡，或不写 insights 整页只放甘特，泳道多、时间长时用；解读里的日期用 08 GANTT-07 绑定记号；HTML 输出可编辑的 KZGantt（T 键编辑台），PPTX 输出原生形状）；取舍 → options-compare / quadrant / risk-matrix），再看密度。数值图在 HTML 用 ECharts、PPTX 用原生图表；森林图、KM、甘特与示意图在 PPTX 用原生形状，HTML 的森林图与 KM 用 ECharts。
- 临床数据页（round 9）：
  - **不带解读卡**：SoA、研究流程、暴露、竞争格局（>4 个药物）、历时变化、有效性整页版（efficacy-summary 不写 insights，示例数据 efficacy-full.json）的小结与强调写进讲稿（09），页面只标记重点数据点。
  - **有效性**：节标题写效应量与单位，不写“二分类 / 连续变量”。时间事件（HR）、事件率（率比）、OR / RR 共用一条含 1 的对数轴。
  - **访视流程**（`soa`）：关键节点行（入组、随机、主要终点等）与研究药物、背景治疗时段，不写“每次访视评估数”；HTML 里访视表头和评估项可以下钻（07）。
  - **研究流程**（`trial-flow`）：分组之外标关键事件，并画研究药物与背景治疗时段。
  - **暴露**：`exposure-summary` 是分档汇总。领导层看各适应症 NDA 能否满足 ICH E1 时用 `exposure-plan`（累计阶梯图 + NDA 达标表）与 `exposure-ledger`（逐研究台账）。数据挂在开发计划合同的研究条带 `exposure` 上，与甘特同一份（08 GANTT-08）。
  - **竞争格局**分档：≤4 个药物用 `landscape` 带卡；5–8 个用 `landscape` 不带卡；>8 个分三页：`landscape-pipeline`（机制 × 阶段看板）、`landscape-efficacy`（按疗效排序 + 研究出处）、`landscape-safety`（多指标矩阵）。
  - **历时变化**：`longitudinal`（可加组间差 `with_diff`）、`lab-boxplot`、`lab-multiples`、`completeness`，规则见 05 CHART-06。
- 轮换：见 BODY-03。每页至少有一种视觉载体：图标、编号、状态胶囊、图表、表格或示意图；纯文字页只在原文规则页出现。
- 原文条款不压缩（03 COPY-09）：模板先密排再拆页，拆页时编号接着排（第一页 1–6，第二页从 7 起），不写“续”；`kz_layout.py render` 的回执逐条核对源文字都在页上，缺一条即失败。
- 行内强调用模板标记：`**加粗**`、`!!深红!!`、`__下划线__`、`==高亮==`（03 COPY-04）。
- 制作：`kz_layout.py render <模板> data.json --track pptx|html --title … --out …` 生成页面；PPTX 的接入步骤见 `adapters/ppt-master.md`“模板页”，HTML 见 `adapters/html-ppt.md`“模板页”。导出前跑 `tools/check_kz_project.py`（10 G-KZ）。


## 版式族、变体与密度档 BODY-03（PPTX / HTML-PPT）
同一种内容有多种呈现，相邻页不重复同一个样子；页面的样子跟着内容量走，不拿空壳撑满，也不把多内容塞进稀疏版式。

**版式族**（catalog 的 `family`）：并列要点 `points`、流程 `process`、对比 `compare`、数据 `data`、规则原文 `rules`、讨论 `discussion`、计划 `plan`。并列要点（最常用、最容易连续同形的一族）有这些变体：

| 变体 | 什么时候用 | 密度档 |
|---|---|---|
| `icon-grid` 图标要点网格 | 3–6 个短要点，每点一图标一句话 | 低、常规 |
| `numbered-cards` 编号要点卡 | 要点有先后或编号引用 | 常规 |
| `points-strips` 横条列表 | 说明较长（一两句）、带关键数或状态 | 常规、高 |
| `points-claim` 论点 + 支撑 | 有一句核心判断，2–4 条支撑 | 低、常规 |
| `points-numbers` 大数字 | 每个要点都由一个数字领起 | 低、常规 |
| `points-figure` 左图右文 | 有一张图或一个关键数字可以看 | 常规 |
| `hub-spoke` 中心辐射 | 一个中心与 4–8 个周边要点 | 低、常规 |
| `points-matrix` 对照矩阵 | 每条都要在同样几个维度上比较 | 常规、高 |
| `cards-dense` 高密度卡片网格 | 4–8 个对象各有不少内容（现状盘点） | 高 |
| `points-steps` 步骤箭头（流程族） | 有先后顺序的 3–5 步 | 常规 |
| `columns-flow` 分栏流程（流程族） | 4–5 个环节各有清单、键值、判定 | 高 |

**密度档**：`tools/kz_layout.py render` 按数据量算 `load`（可见字数 + 12 × 列表条目，`tokens.layout.density`），低于 240 为低密度，不低于 600 为高密度，之间为常规；回执写 `density.tier`。所选变体不支持该档时终端报 `DENSITY`：内容少就换低密度变体（大数字、论点 + 支撑、中心辐射），而不是把三句话放进六栏卡；内容多就换高密度变体（分栏流程、高密度卡片、矩阵）或拆页。图表、表格、计划类按数据定版式，不按字数判档。高密度版式对齐智研 METRIC 汇报的信息量：箭头表头、每栏 2–4 个块（键值行、状态胶囊、子项）、栏底一句提示、底部衔接带。

**选择与轮换**
1. 先按内容类别定族，再按密度档挑变体，再看前一页：相邻正文页不用同一个模板（`qc_plan` 报 `TEMPLATE-ADJACENT` 警告），连续三页同一模板失败（`TEMPLATE-REPEAT`）；同一列表或条款分页续排的后续页写 `continues: true`，不计。
2. 六页以上的 deck 至少用三种模板（`TEMPLATE-VARIETY`）。
3. page-plan 每张正文页写 `template` 与 `density`（`TEMPLATE-MISSING` 警告）：分页故事板（17 SB，`tools/storyboard.py`）据此显示缩略图，并列出同族其他变体供用户逐页替换。
4. 能用图、表、编号、状态胶囊表达的，不写成纯文字卡。
