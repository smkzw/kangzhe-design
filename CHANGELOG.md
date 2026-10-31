# 7.2.4 · 2026-11-01

## KZ7-1101-B14 · 入排标准的方案编号与子项层级（OMP + DeepSeek 7.2.3 重跑）
7.2.3 重跑的 PPTX（25 页）排除标准逐字 21/21，但编号与方案对不上：方案 Word 里排除标准是自动编号 1–19，其中 4 条是“引导语 + 子项”（如“筛选前使用下列治疗：”下 8 项、“传染病筛查指标符合以下标准：”下 4 项）。docx → txt/md 转换保留文字、丢掉自动编号和层级，模型只能按字面猜：第 1 条的 8 个子项被并成一段、引导语被删，传染病的 4 个子项又被提成第 10–13 条，幻灯的“第 n 条”不再是方案第 n 条。按分句比对的原文核对因此放过。根因是工具链与规范：文本里没有编号信息，规范没要求编号层级照方案，模板也不支持子项。
修订：
- 新增 `tools/protocol_lists.py`（标准库）：从 docx 的 `document.xml` 与 `numbering.xml` 读出列表的方案编号与上下级，按标题（排除标准 / 入选标准）定位，目录行与正文不算；输出 criteria 数据，带子项的条款写成 `{"text": 引导语, "items": [...]}`，手写的（1）（2）也算子项；`--outline` 打印编号大纲。
- `tools/kz_layout.py render --source` 接受 .docx：入排标准额外核对第 n 条是否方案第 n 条、子项是否一致（回执 `source_check.numbering`），不符退出 1。`check_kz_project.py`：不符为 RULE-SOURCE 错误；只用文本核对的入排标准为 RULE-NUMBERING 警告。
- criteria 模板：子项挂在引导语下、沿用方案编号；引导语不单独落在栏底；条款列表顶对齐（原来垂直居中并拉大间距，单条时悬在卡中间）。`Items` 新增 `align` 与子项 `level`。
- HTML：编号圆点居中在首行、只占一行高（`@property --kz-lh`），单行条目不再被撑高约 6 px，HTML 与求解器量高一致。
- 03 COPY-09“编号与层级取自 Word”，两个 adapter、SKILL 硬规则 11、10 工具表、`context_pack` 同步；`criteria-long` 示例加一条带子项的合成条款，模板样张两轨重建。
- 测试新增 `tests/test_protocol_lists.py`（合成 docx），共 200 项通过。

# 7.2.3 · 2026-10-31

## KZ7-1031-B13 · 条款原文核对、原文优先于篇幅、超长条款接排（OMP + DeepSeek 实测）
OMP 调用 DGX DeepSeek 按康哲 design 做了两轮方案讨论会 PPTX（7.2.1、7.2.2，均 25 页）。两轮都把排除标准做成“要点（概览）”，SoA 换成概览表；用方案原文逐条核对，入选标准 10/10 逐字，排除标准 0/9 与 0/15，用药与安全性规则大半改写。轨迹显示原因在规范与工具，不在模型能力：
- 用户给的页数（约 20–25 页）与原文条款冲突时，规范没写谁优先；03 COPY-03 的“概览页可标明是概览”被当成了替代原文的许可。
- 模板回执只核对“数据 → 页面”，不核对“原文 → 数据”，所以摘要喂进模板也能过检查。
- 排除标准第 1 条 700 多字，单栏放不下，criteria 模板无法拆开。
修订：
- 03 COPY-09：篇幅与原文冲突时原文优先，加页或放附录并在汇报中说明；概览只能另加，不能代替原文页；SoA 不合并评估行。COPY-03 同步。
- `tools/kz_layout.py render --source <方案文本>`：条款数据必须在原文里逐字找得到（忽略空格与全半角），否则退出 1；回执记 `source_check`。`check_kz_project.py` 新增 RULE-SOURCE（错误：入排与 SoA 未核对、或核对不符）、RULE-UNCHECKED、RULE-OVERVIEW（警告）。
- criteria 模板：超长单条在自己的分号、句号处接到下一栏，后段不带编号、不写“续”，字面不变。
- 09 / `check_notes.py`：章节页“先看……”“接着看……”“最后看……”“这一段要讲”也算报幕（run2 有 4 处）。
- SKILL 硬规则 11、两个 adapter 同步；测试 195 项通过。

# 7.2.2 · 2026-10-31

## KZ7-1031-B12 · 标题写章节名、讲稿规则、说明文字 10.5pt、色条绝对禁止
用户在评估参照稿后定了四条：
1. 正文不小于 12pt，辅助、说明类文字 10.5pt。`type_pt.reference` 8 → 10.5（`type_px` 10.67 → 14），03 TYPE-01 把这一档扩成“说明文字”（脚注、来源、图注、坐标刻度、图例、n=），是全局最小字号；表体、数据标签、示意图标签仍按 12pt。
2. 页标题承担“这一页讲的是哪一章、哪个主题”，不承担观点。03 COPY-01 重写；新增 `tools/kz_titles.py`（冒号、破折号、句读为错误，像结论或问句、超过 14 字为警告），`qc_plan.py` 与 `check_kz_project.py`（读渲染后的 `<g id="title">`）共用。旗舰参照稿的“三个问题，一个决定”“缺口集中在……”改为“汇报章节”“资料缺口分布”，重导出 PPTX。
3. 卡片边缘色条绝对禁止：`forbid_ratio` 0.5 → 0.1，更短的贴边色块也 WARN；02 LG-02 删掉“短色标”替代项。
4. 讲稿：新增 09 NOTES-04（封面、目录、章节、尾页一句话）与 NOTES-05（不报幕、非工程化、非翻译腔、短句、不轻飘，有重点）；新增 `tools/check_notes.py`，读 PPTX、`notes/total.md` 或 HTML-PPT 的 `aside.notes`，并接入 `check_kz_project.py`。模板样张 29 条讲稿按页面数据重写（原来是版面说明），PPTX 样张改为 `--with-notes` 嵌入；四套参照稿的 hero 讲稿压成一句，删去“接下来看”。示例数据里的“抓手”“口子”“落地”“跑通”“闭环”改成临床说法。
- 测试新增 `tests/test_notes_titles.py`，色条测试按新阈值改写，共 191 项通过。

# 7.2.1 · 2026-10-31

## KZ7-1031-B11 · PowerPoint 实机回读修复（原生表格行高、图表标签）
7.2.0 的 31 页模板样张在 Mac PowerPoint 16.114 打开、编辑、另存、导出 PDF 后逐页查看，发现两处只在 PowerPoint 出现的缺陷（SVG 预览、LibreOffice 与 ppt-master 检查器都看不出）：
- 原生表格：单元格没写边距，PowerPoint 用默认上下 0.05in，再按微软雅黑自身度量排中文单倍行（16px 约 1.68em），最小行高超过求解器分配的行高，13 行累计多出约 40px，SoA 末行压在脚注上。现在每个单元格写成一段并带 80% 行距、显式边距（`tokens.layout.templates.pptx_table`），复测行距 34.5px 与设计一致。
- 原生图表：负值柱图的类别标签默认画在零线上、压进柱子，改为 `axes.category.label_position: low`；环图的数值注释与 PowerPoint 的图例相撞，改为把数值并入图例（“恶心 42%”），不再另写注释。
- 回归测试 `tests/test_layouts.py` PowerPointReadback 2 项，全部 182 项通过。

# 7.2.0 · 2026-10-31

## KZ7-1031-B10 · 正文模板库（两轨共用 27 套）、原文保真、四种强调、白底合成、开工第一站
用户反馈七点：
1. 没有阻断式确认生图能力。
2. 生成图不受控：没把液态玻璃和康哲风格融合，画面繁杂、和卡片打架；应当白底、只在边缘装饰，封面和章节可以有图案。
3. 内容页单调，都是“大数字 + 文字卡”。
4. 没有 SVG、图标和示意图，信息密度低。
5. 抽取内容时过度压缩，规则和条款不能压缩。
6. 卡片文字都贴在卡顶，没有纵向分布；关键词和数据没有加粗、下划线、深红或高亮。
7. 深度思考，做出 Agent 可以直接调用的模板页；HTML-PPT 同样检查。

原因（已核实）
- 闸门只写在 SKILL 与 IMG-07 的文字里；ppt-master 的 Stage 2 确认页另有 `image_usage` 与 AI 路径，Agent 按上游确认页走就绕过了康哲的闸门，导出前也没有任何工具核对。
- 正文背景的规则（IMG-05）写对了，但只靠提示词约束，没有构图合同、没有合成兜底、没有安静度检测。
- 13 BODY-01 写着“内容少的页先给卡片主数字”，参考实现只有“卡片 + 条目”一种版式，正文预设只有 cards / split / full。
- ppt-master 有图标机制，康哲从未接入；没有流程、时间线、对比、条款、矩阵类版式。
- COPY-06 的“一般 2–4 条”被当成上限；原文条款保留编号与阈值的要求埋在 COPY-03；没有内容类别和保真等级。
- PPTX 没有布局求解，Agent 从卡顶往下堆；强调词汇只有加粗和深红。

正文模板库（13 BODY-02）
- `tools/kz_layouts/`：页面数据 → 布局树。PPTX 一侧按微软雅黑实测字宽求解几何（纵向按 03 TYPE-02 分布），写出 ppt-master 合规 SVG；HTML 一侧输出同一结构的 grid/flex 标记（`runtime/kz-layouts.css`）。
- 27 套模板：入选/排除标准原文密排、SoA 访视矩阵、键值表、PICOS、编号依据卡、规则表 + 结论带、终点、伴随用药、讨论题（含路径示意）、研究设计总览、时间窗口、流程 + 解析、高密度甘特、数据图 + 解读、森林图、KM + 风险人数、CONSORT、方案比较、KPI 看板、路线图、风险矩阵 + 登记表、分层架构、漏斗、中心辐射、二维象限、观点引述 + 证据、图标网格。
- 数据图：HTML 用 ECharts（新增 stacked、combo、doughnut、forest、km），PPTX 用原生图表；甘特、森林图、KM 与示意图在 PPTX 是原生形状；表格是 ppt-master semantic-table v2（逐边框线、多级表头、合并单元格）。
- 图标单一来源 `assets/icons/`（康哲自绘 + Tabler Icons 子集，MIT），生成 `runtime/kz-icons.js` 与 ppt-master `icons/kangzhe/*.svg`。
- CLI `tools/kz_layout.py`：list / example / render；render 的回执逐条核对源文字都已上页，溢出或缺字即退出 1。
- 两轨样张：`examples/templates/deck/index.html`（HTML-PPT，31 页）与 `examples/templates/pptx/build.py`（PPTX，31 页）。

原文保真与强调（03）
- 新增 COPY-09：材料分原文条款、数据、叙述三类；原文条款逐字保留，先密排再拆页，编号接续，不写“续”。
- COPY-04 强调词汇：加粗、深红、下划线、高亮四种，模板标记 `**`、`!!`、`__`、`==`；加粗文字里的加粗显示为强调色；PPTX 高亮导出后由 `tools/bind_highlight_pptx.py` 改成原生 `a:highlight`。
- TYPE-02：说明 PPTX 由模板求解纵向分布。

生图（04）
- SKILL：选路与生图能力在开工第一站一次问完；答案预填 ppt-master Stage 2 的 `image_usage` / AI 路径，确认页不再重新决定。
- 新增 IMG-08：生成图经 `tools/quiet_plate.py` 合成到白底（正文页只留边缘带，hero 页把文字区提白），量阅读区安静度，回执进 `receipts/`；`tools/kz_image_prompts.py` 按页型生成带风格锚与构图合同的提示词。

检查（10 G-KZ）
- `tools/check_kz_project.py`：闸门与白底回执、色条、字号下限、模板原文核对与溢出、模板轮换、强调、视觉载体、PPTX 高亮哨兵。

# 7.1.3 · 2026-10-29

## KZ7-1029-B09 · 卡片边缘色条闸、生图能力闸门、非首页密排、演示动画模板组
用户反馈四点：
1. 卡片边缘的全高或全宽装饰色条仍偶有出现，问规范是否没写清、是否覆盖所有轨道。
2. HTML-PPT 与 PPTX 似乎共用一套背景图。有生图能力时应积极生图，图要贴近讲稿主题并保持 liquid glass 风格；建议 PPTX 加闸门问用户有没有生图 skill 或接口，确认没有才用缺省背景套；HTML-PPT 规范若没有背景要求就不加。
3. 站点式与流式 HTML 的非首页纵向空间利用率低、信息密度不够，问是否规范写死。
4. HTML-PPT 的多 scene 演示调用不积极且写死：版式单一（都是左卡右动画）、密度低、元素单一（卡片加文字）。要求从规范层解决，并给出至少 10 套可复用、数据驱动的模板，含流程正反例（特别是复杂反例）与甘特推进。

原因（已核实）
- 色条：规则只在 02 LG-02 写过一句“大部分长度”，没有阈值；轨道与适配器都没有重复；上游 html-ppt 的 `.card-accent`（3px 彩色顶边）、竖条主题与 ppt-master 文档里的 accent bar 都会带进来；10 的门表写了检查，但没有任何实现。
- 背景：04 IMG-01/05 与 HTML-PPT 轨道第 4 步对两条 PPT 轨道都已要求生图，这不是新要求；缺的是“先确认有没有生图能力”这一步，以及一套正式登记、可校验的缺省背景，所以没有能力时各自拿参考图凑。闸门对 PPTX 与 HTML-PPT 两轨都加。旗舰路线用程序化光场，不适用。
- 密度：13 FOLD-01 让每个章节页都占一个 100svh 的 Bento 首屏；FOLD-05 只管行长，没有密度指标；卡高不随内容；流式正文 34em 夹在目录与侧注之间，右侧大片空白。改前参考页首屏以下 31 个窗口里 23 个最大空白超过 0.19。
- 演示：15 只列了六种形式和一个 `demo` 预设，没有空间与图形门槛，也没有正反例要求，图库与参考 deck 都是左卡右舞台、文字框为主。

卡片边缘色条（02 LG-02）
- 重写 LG-02：四条轨道、两条路线都适用；有填充、描边或阴影的框都算卡片；列出 CSS 与 PPTX/SVG 的各种画法（单边边框、边缘伪元素、单侧内阴影、边缘子元素、SVG 细长矩形），以及上游 `.card-accent`、竖条主题、ppt-master accent bar。
- 判定阈值 `glass.edge_bar`：贴边 ≤ `hug_px`、厚度 ≤ `max_thickness_px`、彩色（饱和度与不透明度）、长度占边 ≥ `warn_ratio` 为 WARN、≥ `forbid_ratio` 为不通过。
- 允许的替代：短色标、圆点、图标、不超过 `warn_ratio` 的短色块、部门色块；不算色条的情形：均匀的中性 rim、数据对象、页面框架的橙色规则线、表头行、无框文字的中性分隔线。
- 检查工具：HTML 用 `KZLayoutQC.inspectEdgeBars`；PPTX 用 `tools/check_edge_bars.py <svg 目录>`（跟随 translate，非零退出码表示有色条）。`kz-glass.css` 中和上游 `.card-accent`。
- 同步：四条轨道、两个适配器、SKILL 硬规则 4、10 G5-EDGE。

生图能力闸门（04 IMG-07）
- PPTX 与 HTML-PPT 常规路线在出图前：检测本机生图能力（skill、接口、环境变量）→ ⛔ 询问用户 → 在 page-plan 写 `image_capability`（`decision` generated/default_set、`provider`、`asked_user`、`detected`、`user_answer`）。
- 有能力：按讲稿主题逐页生图，提示词带 liquid glass 风格锚（英文锚句写在 IMG-07），`qc_plan` 对暖色占比做风格 WARN。
- 没有能力：用登记的缺省背景套 `assets/backgrounds/`（封面、目录、章节、尾页、安静正文五张，`default-set.json` 记录页型、哈希与原图哈希），`image.mode` 写 `default_set`。
- `qc_plan` 新增 IMAGE-CAPABILITY、IMAGE-STRATEGY、IMAGE-DEFAULT-SET（id 与页型须匹配）、IMAGE-DEFAULT-AS-GENERATED（缺省图不得冒充生成图）、IMAGE-STYLE。
- 参考 `pptx-default` 改为 `default_set`；SKILL 新增“生图能力闸门”一节与硬规则 8；PPTX 与 HTML-PPT 轨道配方同步。

非首页密排（13 FOLD-01/05/06/07）
- FOLD-01 的一屏 Bento 只管站点首页与流式文档首页。
- 新增 FOLD-06：章节页用紧凑章节头 `.kz-chapter`（标题与 KPI 一行，高度 ≤ `head_max_vh`），正文用 12 栏密排网格 `.kz-sheet`（`data-span` 3–9，段落标题行 `.kz-sheet-head`，舞台高度 ≤ `stage_max_vh`）。
- 新增 FOLD-07：逐屏密度 `KZLayoutQC.inspectScroll`，只计墨迹（文字行、图表与甘特绘图区、图片、SVG、表格、演示对象），不计卡片外框与页尾；每个视口高的窗口墨迹 ≥ `min_ink`、最大空白 ≤ `max_void_ratio`。格子与墨迹框有重叠即计墨迹（中心点采样会漏掉比格子薄的文字行）。阈值 0.35 / 0.17：7.1.3 参考页全部通过，7.1.2 参考页每页至少一档视口不过。
- 滚动页图表按宽高比定高（`chart_aspect` 3.2，超宽屏 ×1.25），甘特按任务数定高（`gantt_row_px`、`gantt_axis_px`）。
- 参考实现：章节页改为章节头 + 密排网格，首屏电影换成 compare 演示；首页首屏以下改为密排网格；流式改三栏，图表进第三栏。
- 同步：10 G5-FOLD / G5-DENSE、站点与流式轨道、06 FILM-01。

演示动画（15 DEMO）
- DEMO-01：方法、流程、规则、判定、计算、数据、计划、版本对比、风险、数据流转页 MUST 用演示舞台；每个讲方法或数据的章节 MUST 至少一页演示；page-plan 写 `demo: {kind, cases?}` 或 `demo: {none: 理由}`。
- DEMO-02：形式从 6 种增至 16 种。新增 `flow` 流程正反例、`gantt` 甘特推进、`swimlane` 跨部门泳道、`consort` 受试者流、`curve` 曲线解读、`breakdown` 构成拆解、`audit` 逐项核查、`matrix` 风险矩阵、`network` 数据流转、`schedule` 访视窗口。元素与文字全部来自数据，数据自相矛盾时抛错。
- DEMO-03：新增空间与图形门槛 `min_canvas_coverage`（最满 scene 的画布网格覆盖率，连线按笔画计）、`min_figures`（图标、点、条、块、连线）、`min_stage_share`（HTML-PPT 舞台占幻灯片面积），由新的 `Stage.coverage()` 出回执。
- DEMO-05：四个构图预设 `demo`、`demo-mirror`、`demo-wide`、`demo-stack`（舞台在上、下方事实条，`KZDemo.renderFacts`）；相邻演示页不重复预设，`qc_plan` 检查 DEMO-PRESET、DEMO-PRESET-REPEAT。
- 新增 DEMO-08 视觉词汇：图标与示意图为主、文字只做标注；状态用同一对象换样式表达；列出反模式。
- 新增 DEMO-09 正例与反例：流程、规则、核查类演示至少一个正例、一个简单反例、一个复杂反例，反例路径画在舞台上，汇总 scene 给出计数；`qc_plan` 检查 DEMO-CASES。
- 新增 runtime：
  - `runtime/kz-icons.js`（`KZIcons`）：28 个本包绘制的线性图标；
  - `runtime/kz-demo-patterns.js`：十种新形式，用 `KZDemo.kit` 搭建，也是写项目自定义形式的范例；
  - `KZDemo.define / forms / kit / renderFacts`；`kit.lead`、`kit.glyph` 给文字加图标；
  - `KZScenes.Stage.coverage()`；没有任何 scene 写到的对象保持标记里的样子、可见。
- 前六种形式升级：判定节点、版本对比的文档与结论带图标，核对勾叉改为图标，计算演示每行加同刻度条，数据动画图标出数值、堆叠后各段带名称。
- 示例：
  - `examples/motion/`：16 种形式，左右、通栏、上下四种排法；
  - 新增 `examples/motion/deck/`：HTML-PPT 模板组 12 页，十种新形式各一页，四个预设轮换，讲稿按 scene 分段，可复制一页改数据直接用；
  - 参考 deck 与模板组共用 `build.py` 的 `write_deck`。
- 同步：00 规则所有者表、13 BODY-01 四个预设、10 G7-DEMO、HTML-PPT 轨道（脚本顺序加 `kz-icons.js`、`kz-demo-patterns.js`）、`runtime/API.md`、SKILL 硬规则 11、page-plan schema（`preset` 枚举、`demo` 字段）。

验证
- 单元测试 161 项通过。新增 `tests/test_edge_bars.py`（9 项）、`tests/test_image_gate.py`（9 项）；`tests/test_demo_motion.py` 增至 14 项：16 种形式都有规范、API、数据与图库；模板组覆盖十种新形式、预设轮换、讲稿每页 5 个 scene 段；图标名都存在；page-plan 演示声明、预设轮换与正反例检查。
- ego lite 0.6.1.13（Chromium 156）：
  - `tests/ego/demo_checks.mjs` 20/20：16 种形式都达到密度、空间与图形门槛；每个 scene 在 1600×1000 与 1280×800 下无文字重叠、出界、溢出；scene 与到达路径无关；参考 deck 第 8、9 页步进；模板组十页在 1920×1080、1280×720、2560×1080 下舞台占比、版面与事实条全部通过，相邻不重复预设，→ 逐 scene 前进后翻页；减少动态；数据形态回归 14 项；无脚本错误；
  - `scene_checks.mjs` 15/15，`flagship_checks.mjs` 19/19；
  - `runtime_checks.mjs` 19/20：失败的一项是“下钻展开中途关闭时反向折回”，按 7.1.2 的代码（HEAD）重跑三次也失败两次，随 ego lite 的帧调度时好时坏，与本轮改动无关；7.1.2 记录的另外三项已知失败本轮通过。
  - 站点首页、章节页、流式页在 1920×940、1536×730、2560×1080、1280×720 下逐屏密度全部通过，`inspectEdgeBars` 0 处色条；参考 PPTX 的 6 张 SVG 经 `check_edge_bars.py` 0 处色条。
- 独立代码审查发现 12 处缺陷和 1 处轻微问题，均已修复，并在 `demo_checks.mjs` 的“数据形态回归”或 `test_edge_bars.py` 里补了检查：
  - 甘特：追赶的任务就是延误的那项时，两次调整互相覆盖，结论写成“回到原计划”；延误把里程碑推出时间轴时，标签和旗标出错（现在报错，要求加长时间轴）；
  - 曲线：窗口终点是空值时差值算错（现在报错）；首个值为空时起点标签错；第三条曲线不显示却计入文案；
  - 受试者流：没有脱落的组直接抛错；脱落超过该组人数不报错；省略 `per` 时说明写“每点 undefined 例”；
  - 流程：全部通过时仍点名“问题集中在第一站”；退回第一站时路径出画布；退回不存在的环节不报错；同一托盘个案多时溢出；
  - 构成拆解：小数子项合计用严格相等，误报不符；
  - 风险矩阵：非方阵时说明写错档数；
  - 时间轴：任务在轴外结束时，完成勾因“从未设置即可见”停在画布左上角；
  - 数据流：前面数据包点亮的通道一直亮着；连带发现舞台的 `stroke` 写成属性，被类样式盖住，通道高亮从未显示，现改为内联样式；
  - `coverage()` 漏算水平和竖直的直线；
  - `check_edge_bars.py` 读 style 时没去掉键名前的空格，`rgba()` 的透明度被忽略。
- 前六种形式也给出事实条数据，`demo-stack` 可以用在任何形式上。
- 未覆盖：
  - 真实生图接口的出图与风格审阅（本机无生图能力，参考例走缺省背景套）；
  - 正常帧率 Chrome/Edge 与 PowerPoint 的放映观感；
  - PPTX 的演示降级（DEMO-06）仍无参考实现。

# 7.1.2 · 2026-10-26

## KZ7-1026-B08 · HTML-PPT 按 scene 步进、12pt 辅助文字、演示性动画
用户反馈三点：
1. HTML-PPT 的动画没有按 scene 截断，默认以超慢速连续播放，演讲者无法手动控制。要求按 scene 区分，滑动或方向键后开启下一个 scene。
2. 最小字号放开到约 PowerPoint 的 12 号字。
3. 用本技能做的动画大多仍是卡片入场加卡片间连线。要求按页面内容做演示性、示例性的动画：形式多样，多 scene、高密度、大幅度，例如左右分栏，一边展示本页内容，一边用动画做示范，或做成基于数据的动画数据图；并把要求写进技能，提供可复用的示例与框架。

原因（已核实）
- 慢速：
  - 电影时钟每帧最多推进 100ms，帧率低时整部电影成倍变慢（1 fps 时慢 10 倍）；
  - 时钟取 rAF 回调的时间戳，而 ego lite 0.6.1 的时间戳慢于真实时间（实测 1495ms 内只走了 891ms）。
- 无法控制：HTML-PPT 照搬了站点的 36 秒连续循环，FILM-01 又把“自动推进”写成必备条件，放映时没有给演讲者留出节奏。

HTML-PPT scene 步进（06 MOTION-09）
- 每个电影状态就是一个 scene。入场只显示 scene 0。
- →、↓、空格、PageDown、左滑、上滑：各播放一个 scene 的运动后停住；已在最后一个 scene 时再按才翻页。
- ←、↑、右滑、下滑：瞬时退回上一个 scene，不倒带。
- 运动中再按一次：完成当前运动，不会跳过下一个 scene。
- 从后一页退回：显示最后一个 scene。
- 演讲者窗口、深链、首次加载等无人操作的入场：一次走完全部 scene。
- 减少动态：直接翻页。
- 实现：
  - `Film` 新增 `scenes` 选项与 `next/prev/toScene/playThrough`；`storyboard` 返回 `sceneAt`；
  - `html-ppt-bridge.js` 在捕获阶段先把按键与滑动交给活动页；上游没有绑定的 ↑/↓ 与纵向滑动转交为 →/←；
  - 阈值见 `motion.film.scene`。
- 时钟（FILM-05）：
  - 电影、图表、甘特、计数、弹簧一律读 `performance.now()`；
  - 单帧最大步长改为 `motion.film.max_frame_gap_ms`；弹簧按 1/60 秒定步长积分；
  - 帧率低时只掉帧，不再变慢。
- FILM-01/03/04 改为按轨道区分：站点与流式自动循环，HTML-PPT 按 scene 步进。讲稿按 scene 分段（09 NOTES-02）。

12pt 辅助文字（03 TYPE-01）
- 新增 `secondary` 角色：`type_pt.secondary` 12，`type_px.secondary` 16。
- 用于注释、图注、表体、图表轴与图例、卡内旁注、状态条与演示舞台标签。任何页都可以用，不必整页切换 compact。
- 正文仍为 15pt，标题不变；同页同角色仍只有一个字号。
- page-plan 的角色枚举加入 `secondary`，`qc_plan.py` 新增 SECONDARY-TYPE 检查。
- 页脚是固定的页面框架，保持 13.5pt。

演示性动画（新增 15 DEMO）
- DEMO-01 写明何时必须做：讲方法、规则、判定、计算、数据、计划、版本对比的页面要用演示舞台；只有卡片入场和连线不算演示。
- DEMO-02 形式目录：单位流动、计算演示、数据动画图、时间轴推演、判定走查、版本对比，另可自定义。
- DEMO-03 密度与幅度门槛：`motion.scenes.density`，由 `Stage.audit()` 出回执。
- DEMO-04 内容依据：数字与说明句由数据算出，合成示例要标明，并附 scene 台账。
- DEMO-05 分栏版式：HTML-PPT 用 `data-preset="demo"`，站点用 `.kz-demo-split`。
- DEMO-06 PPTX 降级：一个 scene 一页，用 Morph 配对。参考实现尚未覆盖。
- 新增 runtime：
  - `runtime/kz-scenes.js`（`KZScenes`）：通用演示舞台，支持持久对象、scene 增量、错峰、途经点、步进与循环、seek、`audit()`；
  - `runtime/kz-demo.js`（`KZDemo`）：六种形式；
  - `kz-glass.css` 新增 Demo stages 段。
- 示例：
  - 新增 `examples/motion/`：六种形式的站点式图库，左右分栏，舞台循环播放；
  - HTML-PPT 参考 deck 增至 12 页，第 8 页“缺口与补收”（单位流动）、第 9 页“缺失与差异的处理”（判定走查）按 scene 步进，讲稿按 scene 分段；
  - 参考 deck 的电影页改为 scene 模式。
- 同步更新：00 规则所有者表、13 BODY-01 加 `demo` 预设、10 G7-SCENE / G7-DEMO、HTML-PPT 与站点轨道、两个 adapter、`runtime/API.md`、SKILL.md 硬规则 5/10/11 与读取顺序；`context_pack.py` 对所有带动效的任务路由到 15。

验证
- 单元测试 137 项通过，新增 `tests/test_demo_motion.py`：
  - secondary 字号；
  - scene 与密度 token 都有使用方；
  - 时钟不取 rAF 时间戳；
  - 六种形式都有规范、API、数据与图库；
  - 参考 deck 的演示页与脚本顺序；
  - 路由。
- ego lite 0.6.1.11（Chromium 156）真实按键与触控：
  - `tests/ego/scene_checks.mjs` 15/15，多次运行均通过；
  - 新增 `tests/ego/demo_checks.mjs` 16/16：六种形式全部达到密度门槛；每个 scene 在 1600×1000 与 1280×800 下无文字重叠、出界、溢出；无论前进、后退还是循环回到某个 scene，画面都一致；deck 第 8、9 页逐 scene 步进、退回、翻页；焦点在按钮上时 → 仍进一个 scene；减少动态；无脚本错误；
  - `flagship_checks.mjs` 19/19；
  - `runtime_checks.mjs` 16/20：失败的 4 项（离开时弹簧回到静止、下钻收回与焦点归还）与 7.1.1 的已知失败相同（当时 15/20）。
- 独立代码审查发现 6 处缺陷，均已修复并补了回归检查：
  - 往回切 scene 或循环回到开头时，后面 scene 设的类名与文字不复原；
  - 数值与文字写同一槽位时，继承来的数值压过新文字（units 缺口 scene 显示“9 / 12 份”而不是“缺 3 份”）；
  - 焦点在按钮或链接上时，按键直接翻页并跳过本页 scene（上游不看事件目标）；
  - 预备状态带上了途经点，循环收尾时对象倒走；
  - 画满的连线仍带虚线，在大画布上可能画不到终点；
  - `site.js` 节点数多于状态时会出现 NaN。
- 两个 ego 脚本改为在文档加载前注入错误收集。此前 `scene_checks` 读取的错误列表没有任何代码写入，无论有无脚本错误都会通过。
- 未覆盖：
  - 正常帧率 Chrome/Edge 的放映观感；
  - S 演讲者窗口中逐 scene 同步的实际观感；
  - 平板真机滑动；
  - PPTX 的演示降级。

# 7.1.1 · 2026-10-24

## KZ7-1024-B07 · 旗舰玻璃改为半透磨砂
用户反馈：旗舰两份样例的玻璃质感满意，但卡片承载信息，玻璃太透；背后是明亮复杂的鎏金，几乎全透的卡片上再放文字，会和光冲突；PPTX 立体感更弱，问题更明显。要求改成半透玻璃或其他更自然的做法，不是简单关掉透明。

HTML
- 透镜滤镜分两区：边缘环带照旧折射加饱和；中间阅读区单独磨砂（`lens.roles` 第三项），再降饱和（`frost_saturate` 0.7）并把亮度压向白色（`frost_lift` [0.62, 0.38]），背后的鎏金只剩淡蜜色。环带到阅读区的过渡由 `rim_band` 控制。
- 玻璃面加厚到约一半白（`glass.face` 0.50/0.36/0.42）。章节号上的透镜不承载文字，改用 `glass.face_clear`，仍保持通透和数字弯折。

PPTX
- PowerPoint 不能模糊或折射形状背后的内容。新增 `tools/flagship_plate.py` 的 `lens()`：它是运行时透镜滤镜的 numpy 移植，从同页光效图裁出玻璃范围，在阅读区磨砂、降饱和、提亮，在边缘环带按同一距离场折射，形状外透明。
- `build_svg.py` 在每块玻璃壳下垫一张烘焙透镜图，共 13 张：身份胶囊、封面数据条、目录卡、章节透镜、关键数字透镜、决定事项卡。玻璃壳保留渐变面、白色细边和外阴影。章节透镜放在数字下层，壳用通透面。

规范与测试
- 14 FLAG-05 写明承载文字的透镜是半透磨砂；FLAG-10 写明 PPTX 的两层玻璃做法；FLAG-11 G5 加一条阅读区磨砂。`tracks-pptx.md` 与 SKILL.md 同步。
- 新增测试：透镜参数为三项、磨砂提亮保持白色、阅读面比通透面更不透明；烘焙透镜图结果确定、形状外透明、阅读区比背后光效图更淡更平而边缘保留颜色；PPTX 探针每块玻璃壳下都有透镜图，且透镜图在壳的前面绘制。

验证
- 单元测试 129 项通过。
- HTML：运行时检查 19/19；9 页 × 4 视口版面检查无问题，最小字号 16。
- PPTX：检查器 0 错误，交付检查 0/0，`qc_plan` 0 错误，OOXML 回读动效时序不变；PowerPoint 另存 PDF 逐页查看；加文本框后保存、重开，23 个图片对象（13 张透镜图）、动效时序与原生柱图都保持不变。
- 未覆盖：正常帧率 Chrome/Edge 的放映观感；非 Chromium 降级；Windows Office。

# 7.1.0 · 2026-10-24

## KZ7-1024-B06 · 旗舰路线与选路阻断
新增旗舰路线（`design_specs/14-flagship.md`），用于对外汇报和向公司顶层领导汇报。方向由用户在三套原型中选定：浅色画布，B（白昼棱镜）的排印与内容页，C（流光液态）的光与液态玻璃；深色舞台不采用。

选路
- PPTX 与 HTML-PPT 开工前一律阻断，请用户在“常规”和“旗舰”之间选择（SKILL.md、14 FLAG-01）。提问前 Agent 先根据材料与信息判定，给出推荐路线和理由；判据有听众、场合、材料性质、用户措辞、放映环境。站点式与流式不触发。`tools/context_pack.py --route flagship` 加入 14。

旗舰的视觉与动效
- 页面角色光量分三级：封面、目录、尾页全量；章节页光河从数字下方穿过；内容页的光退让。用户指出原型 C 的光在内容页太扎眼、和卡片抢视线，因此内容页里标了 `data-kzf-calm` 的阅读区以羽化矩形挡住光场，光只留在页边和底边地平线，并在唯一的聚光对象背后聚一池光。
- 光先转场：翻页时一道暖光波扫过全页，光停下后内容才入场，文字带轻微模糊上移，玻璃从微缩放落定。连续快速翻页时整页光波间隔不短于 700ms（WCAG 2.3.1）。
- 液态玻璃透镜：Chromium 上用 SVG 位移作 backdrop-filter，只在边缘折射，中心不变形；边缘高光随页面光向转动。每页最多 3 块，图表、表格和正文后面不放。非 Chromium 浏览器退回磨砂。
- 去掉固定页眉页脚，由一枚身份胶囊（官方 Logo 加“产品中心医学部”）锚定，翻页时滑到各页型的角落。
- 内容页的阅读面是白纸卡加发丝线；关键数字用超细大号字。

实现
- `runtime/kz-flagship.js/css`：在上游 html-ppt deck 下方铺一张共用的 WebGL 光场，透镜、胶囊和转场都只在品牌层叠加，导航、hash、总览、演讲者窗口与打印仍归上游。支持 `?kzf-t` / `?kzf-p` 定格；减少动态时只画一帧；`?preview` 与 WebGL 不可用时改用 CSS 渐变光场。
- `tokens.flagship` 加 `--kzf-*` CSS 变量；`tools/flagship_plate.py` 用 numpy 移植同一光场，供 PPTX 背景使用，结果确定。`requirements.txt` 加入 numpy。
- 正例：`examples/reference/htmlppt-flagship/`（9 页，同一素材）、`examples/reference/pptx-flagship/`（5 页，ppt-master 导出）。
- 测试：`tests/test_flagship.py`，覆盖 token 完整且都有使用方、光效图确定性与安静区、选路与路由、qc_plan 的旗舰检查、正例结构；`tests/ego/flagship_checks.mjs` 用真实按键检查运行时。

独立审阅后的修正
- 启动：上游初始化后第一次出现的 `.is-active` 当作起始页，深链和刷新不再先播一遍从封面过来的转场；`?kzf-p` 从上一页起。
- 减少动态：翻页后立即重画光场（原来内容页一直顶着 hero 光量），取消页面容器的过渡，新旧两页不再叠显；打印加减少动态时不再出现空白页。
- 转场：离场页与入场页的安全区、光池按进度交叉过渡；整页光波用独立时钟，被限频的翻页不会掐断正在进行的光波；中途打断时从当前混合状态起步；入场未完成就离开的页不再闪现。
- 对比度：引导语与编号改用 `flagship.accent_ink`（#9A4D00，在画布上为 5.96:1），封面与尾页的元信息改用正文色。原来用的 `colors.focus` 在画布上只有 4.47:1。
- 打印保留身份胶囊；处理 WebGL 上下文丢失与恢复；dispose 清理计时器、透镜与变量；胶囊内边距与间距改读 tokens；着色器里 edge0≥edge1 的 smoothstep 改为合法写法。
- 计划预检：page-plan 加 `route`，旗舰 hero 页写 `flagship-<kind>`，背景写 `flagship_light_field`（PPTX 附光效图回执）；`qc_plan.py` 据此改用旗舰字号与光场检查，并按 `--asset-root` 核对光效图哈希；FLAG-02 补上 03 TYPE-01 角色字号一行。PPTX 旗舰探针附 `page-plan.json`，0 错误。
- 选路：修改已有 deck 时沿用原路线，不再阻断。`context_pack` 的 assets 阶段按路线给出 14 与光场工具。

验证
- HTML 旗舰：9 页 × 4 视口版面检查全净；运行时检查 19/19 通过（含连续快速翻页、深链、减少动态与打印回归）。
- PPTX 旗舰：检查器 0 错误，交付检查 0/0，OOXML 回读正确；PowerPoint 另存 PDF 与编辑保存回读一致。
- 未覆盖：正常帧率 Chrome/Edge 中的放映观感；非 Chromium 降级；Windows Office。

# 7.0.2 · 2026-10-24

## KZ7-1024-B05 · 甘特编辑器按需展开、PPTX 错峰拉长、PowerPoint 实机回读
按用户要求：甘特编辑器点选任务条才展开；PPTX 入场间隔拉长；此前留给使用者的遗留项由维护者自己处理。

运行时
- 甘特编辑器按需出现（08 GANTT-01）：默认只显示图表并占满卡宽；点选任务条（松开后）、在图上按回车或方向键、或调用 `select()` 时，编辑器在右侧展开（约 1/4，淡入）；“完成”或 Esc 收起并把焦点还给图。根元素 `data-kz-editor` 为 `closed` / `open`，新增 `openEditor(open)`。拖动过程中不显示“已修改”条，避免图表区改变尺寸而打断拖动；有未撤销的修改时，收起状态下仍保留“已修改”与撤销、还原。指针点选不再给整个图表画键盘焦点框。

动效
- 新增 `motion.stagger_ms.pptx_card`（180ms）。PPTX 入场是纯淡入，没有 HTML 的位移和卡内级联，70ms 的间隔放映时看起来是同时出现；HTML 仍用 `card` 70ms。06 MOTION-07 与 adapters/ppt-master.md 改为 `n × pptx_card`，观点句 `组数 × pptx_card + takeaway_gap`。
- 两份 PPTX 样例重新导出：Default 封面/目录/结束页 0/180/360ms，研究范围 0/180/360 + 观点句 740，资料完整性 卡头 0、柱图擦入 180、KPI 360、缺失处理 540、观点句 920，核对计划 卡头 0、甘特擦入 180、图例 360、结论 740；探针 0/180/360/740。检查 0 错误，交付检查 0/0，OOXML 回读一致。

验证
- PowerPoint（macOS 16.114）编辑保存回读完成：两份样例经 AppleScript 打开、改标题文字、新增文本框、讲稿追加、另存、重开，三处修改都读回；保存后的动效时序、原生柱图、字体、hero 框、阴影与渐变与导出时一致，探针的 Morph 与 `!!kz-carrier` 保留。放映观感与 Windows 未测。
- 翻页卡顿查到根因：ego lite 0.6.0.20 中，任何页面跑过一段 requestAnimationFrame 动画后 rAF 一直停在 1 fps（5 行最小页面可复现，重启无效），ECharts 入场动画因此把整份 deck 拖慢；组件实验室 15/20 的 5 项失败都靠 rAF 推进，同属此因。属浏览器问题，未改代码。
- HTML-PPT 10 页 × 4 视口复测无孤字与断词，正文页纵向跨度 ≥0.70。
- 2560×1080 章节页宽屏专用图：本机 gpt-image-2 接口凭据被拒（401），未生成，仍为 WARN/BLOCKED。

# 7.0.1 · 2026-10-24

## KZ7-1024-B04 · 用户视角审美审阅修订
按观众和讲者的视角重审三份 PPT 样例（HTML-PPT、PPTX Default、PPTX 探针）：美观、断行、字号、重叠、是否遵循设计指令、文字重点与逻辑、讲稿语言、纵向空间、强调、动效卡顿与动画密度。本人截图审阅加两路独立只读审阅（视觉、文字与讲稿），确认的问题逐条修复并复测。

HTML-PPT 正例
- 改用与 PPTX Default 相同的素材（研究资料完整性核对），两轨讲同一个故事、同一组数据。原版目录承诺三章而只有一张章节页、同一流程在一页里有三种叫法、柱图只画完整份数而看不出缺口、结尾只有“谢谢”。
- 10 页：补 02、03 章节页；“核对流程”电影的右侧节点改为各步产出，状态条只留动作名；资料完整性改成应收/已收分组柱，数值表加缺失列与空值说明；甘特用 5 项真实任务、部门色与图例，底部一句结论；结尾改为“请确认两件事”。
- 研究范围页卡片加主数字（第 16 周 / 4 组 / 2 项），文字卡页加大卡内留白，正文区纵向跨度 0.61 → 0.70。
- 组件数据由 build.py 内联为 `window.KZ_DECK_DATA`，不再借用站点正例的 `site/data.js`。
- 讲稿全部重写成能直接说出口的中文：不描述画面与软件操作，数字用阿拉伯数字。
- 翻页时离场页的标题与页眉立即隐藏，正文页之间不再出现两个标题叠印（屏幕态；打印不变）。

运行时与工具
- 甘特：季度标签居中到季度带（原在分界线上，条形右端看起来落在下一季度）；空间够时一季度写成“2027Q1”而不是光秃的年份；进入页面时不再给第一条描深色边，点选、下拉选择或键盘聚焦后才描边。
- `KZLayoutQC.inspectOrphans` 增加 `splits`：用 `Intl.Segmenter` 找出落在中文词内部的换行（如“中心记｜录”），`<br>` 与块级子元素两侧不拼词；有孤字为 FAIL、只有拆词为 WARN（03 TYPE-04、10 G5-ORPHAN）。
- 新增 `KZLayoutQC.inspectBodySpan`：`layout.content_span_target` 原来没有任何工具读取，现在按正文区直接子元素的纵向跨度判 WARN（10 G5-SPAN，13 BODY-01）。
- 封面标题在两行预留框内贴底（`hero_layouts.cover.title_valign: bottom`；PPTX 绑定时 `anchor="b"`），一行标题与副标题不再隔开一整行。
- hero 图片框 y>0 时顶边叠画布色渐变（`hero_layouts.image_top_fade_px` 72），PPTX 目录页 y=90 处的接缝消失；HTML 图片按框的 y 下移，16:9 下与 PPTX 同位，章节页主体不再压标题。
- 电影未到节点的透明度下限 .42 → .65，投影时可读。

PPTX Default 正例（重新导出，检查 0 错误，交付检查 0/0，OOXML 回读一致）
- 封面、目录顶边接缝消除；研究范围页加观点句并把卡片拉高到正文区 0.73；资料完整性页删去与 KPI、观点句重复的逐组缺口条目，卡片改为“缺失处理”；核对计划页去掉没有标注的高亮季度带，结论句补全；结束页写明“医学部牵头”。
- 动效：封面与结束页标题、副标题、元信息 0/70/140ms 入场；柱图与甘特不再整卡擦入，卡头淡入、图表单独擦入、观点句最后（卡壳改为静态装饰，因为 ppt-master 要求根模块互不重叠）。
- 讲稿改为阿拉伯数字，删去“先说结论”与材料里没有的“整体可用”。
- `readback.py` 改为从仓库读 tokens（原来写死已安装路径）。

PPTX 探针
- 与 Default 同一素材；研究范围页卡组居中、卡内主数字与分栏让三张卡等高、带强调；Morph 页载体居中、卡高随内容，加步骤条；封面与第一张流程页补入场动效。

不变（需要时由使用者决定）
- 甘特编辑器在 HTML-PPT 里常显（08 GANTT-01：图 3/4、编辑器 1/4）；电影自动推进（06）；PPTX 入场错峰 70ms 与 HTML 一致。（7.0.2 已按用户要求改为编辑器按需展开、PPTX 错峰 180ms。）

# 7.0.0 · 2026-10-24

## KZ7-1024-B03 · 安装实测与 ppt-master Default 全流程正例
把三套技能装进 `~/.claude/skills`，以用户视角跑通 ppt-master 6.7.3 的 Default Generate 路由（两次确认页、Design Spec/lock、手写 SVG、最终检查、verify-charts、备注、动效、原生图表导出、品牌绑定、交付检查、OOXML 回读），并在 PowerPoint 中打开交付文件。流程中暴露的问题逐条修复。

安装包
- 新增 `requirements.txt`（jsonschema、Pillow）与随包的 `STATUS.md`（当前验证状态；`review/` 不随包发布，原指向失效）。
- SKILL.md 的命令改为 `python3 "$KZ_DIR/tools/…"`，不依赖当前目录（宿主常没有 `python` 命令）。
- 新增 `assets/logo_bot.png`：官方 SVG 原样渲染的 10× 透明 PNG，哈希登记在 `tokens.logo.png_sha256`；ppt-master 不做 SVG 图片映射，agent 不必各自栅格化（01 CORE-02）。
- INSTALL.md 改写为面向任意读 `SKILL.md` 目录的宿主，并列出两个引擎的安装与核对版本。
- 安装包不再包含 `.pptx` 样例成品（改作 Release 附件），包体 4.1MB → 2.2MB。

PPTX 轨
- 新增 `examples/reference/pptx-default/`：Default 全流程正例（素材、Design Spec、执行锁、page-plan、资产清单、6 页手写 SVG、动效、备注、绑定回执、交付检查与 OOXML 回读）；tracks-pptx 与 context_pack 指向它。
- `hero_layout.svg_fragment`：目录页 page role 写成 `toc`（原为 `content`）；每张目录卡的卡面与编号、标题、说明合为一个根组，成为一个编辑与动画单元。
- `bind_hero_pptx.py` 直接读 page-plan：页码取 `slide` 字段或页面 id 中的第一个整数（原只接受 `1_cover` 形式）。实测 6.7.3 导出会把 hero 文字框收缩到内容大小（封面标题 538×86），超出 HERO-04 容差，四类 hero 页因此需要绑定；绑定后偏差 0。
- 06 MOTION-07 / adapter：`entrance_wipe` 方向以预设表为准，自底部写 `"down"`（presetSubtype 4），自左 `"left"`（8）；`pptx_animations.py --describe` 的注释说法相反。Default 自动读取项目根 `animations.json`。
- adapter 新增“Default 路由里的康哲输入”：Stage 2 确认页会按正文基准重算角色字号，康哲字号要在页面上固定并核对 `result.json`；Logo PNG 与所有位图登记 §VIII 与执行锁；页面 SVG 由主 agent 手写；本机反向 DNS 慢时确认页与预览改用前台进程。

图像
- `IMAGE-WASHOUT` 改用亮度标准差（`image.washout.luminance_std_min` 7）：康哲浅色玻璃 hero 本来就有 84–91% 高亮像素，B02 的“亮像素比例 + 饱和度”判据对批准过的三张 hero 全部误报。标定：批准 hero 8.5–12.9，同图叠加 60% 白色后 3.4–5.2。

## KZ7-1024-B02 · 两路独立审阅后的修订
代码审阅（runtime 与工具）和规范审阅（自洽、可执行性、中文）各自只读完成，确认的问题逐条修复并复测。

运行时
- 下钻：`snapshot().width` 改用布局宽度，展开动画期间也是最终宽度；`close()` 返回原生关闭并还焦点后兑现的 promise；展开中途关闭时反向折回，不先跳回全尺寸；只有从卡片（`.kz-card` / `data-kz-drill-source`）触发才做共享元素展开，独立按钮或缺省触发时原地打开。
- 电影：`storyboard()` 返回 `staticProgress`（信息最多的状态停留段中点，可用 `staticState` 指定），参考接线传给 Film，静态帧不再落在移动段或文字淡出窗口里；`phaseAt` 改由同一采样器推导，状态条不会先于载体文字切换；停留时长参数进 `motion.film.storyboard`。
- 入场：观点句（`.kz-takeaway-card` / `data-kz-takeaway`）最后出现，多隔 `stagger_ms.takeaway_gap`，与 PPTX 回读的 0/70/140/410ms 一致；卡标题用 `distance_px.title` / `duration_ms.title`；表格逐行进入级联；站点章节转场用 `duration_ms.section`。
- `mountSections`：单个段落出错不再让同批段落永久隐藏；打印样式兜底显示待入场段落。
- 新增 `KZMotion.fitFold`：`.kz-detail-tall` 按文档倒序收起，直到首屏放得下。实测 1920×1080 首页“资料分组”卡此前底边被切掉。
- 图表：只有占用类别色的系列计入 5 色上限（自带色、对照组、部门系列不占位），超出时在 `validate` 阶段报错；7.0 起不再循环取色。
- 甘特：端点命中区读 `tokens.gantt`；`*_known:false` 的任务明确报错（schema 允许对应端点为 null）。
- html-ppt-bridge：可视区高度为 0（隐藏 iframe、预览）时也写入比率 1，`--kz-u` 不会缺失。
- KZLayoutQC：`inspectFold` 只把带可见文字或已绘制图形的对象计入覆盖率，卡片外框越出视口也报 `FOLD_OVERFLOW`，缺省阈值与 tokens 一致；`inspectCard` 的 `TEXT_OUTSIDE` 恢复按内边距判断（纵向容差 0.2em、横向 1px，进 `layout.qc`）；`inspectOrphans` 按行带分行，不再把行内小字号片段误判为孤字行。

tokens 与工具
- 删除无人读取的 token：`wide.desktop_scene_min_width_ratio`、`data_min_width_ratio`，`colors.ribbon_mid`、`table_header`，`rhythm.ink_inset_*`、`sibling_inset_tolerance`，`motion.max_blur_layers_per_region`、`duration_ms.text_swap`、`scale.dialog_from`。
- 规范里写死的数值登记进 tokens 并接入代码：首屏断点（单测核对 CSS 媒体查询）、导语行长、KPI 与首屏标题字号、弹窗最宽、弹层空白比例、QC 容差、主视觉过曝判据、电影状态变化阈值、PPTX 接触椭圆 alpha、甘特命中区。
- 阴影：新增 `thin`（玻璃内的嵌套薄覆层，电影节点改用它）与 `inset`（表单字段内凹）；PPTX `raised` 的 alpha 回到单层上限 0.15。
- 正文页 chrome 几何由 `build_tokens.py` 生成为 `--kz-chrome-*` 变量，deck CSS 不再写几何数值（3 视口 × 5 页 90 个矩形前后一致）。
- 验收矩阵加入 1920×1080（同屏 F11 全屏）。
- `qc_plan.py`：四类 hero 主视觉按 `image.washout` 计算过曝并报 `IMAGE-WASHOUT`。
- `build_tokens.py`：阻尼比 ≥1 时不再除零。`build_dist.py`：在 git 仓库中只打包受版本管理的文件（98 个）。
- `hero_layout.svg_fragment`：Logo 恢复 `meet`，主视觉保持 `slice`（复测导出不再有 `srcRect` 裁切）。
- `context_pack.py`：资产阶段补 02、11、13；PPTX 制作阶段补 `glass_svg.py` 与探针说明。

规范
- 状态词统一为 10 QA-STATUS 的 PASS / WARN / FAIL / BLOCKED / PENDING / N/A；00 的验证范围措辞与之分开。
- page-plan schema 补规范要求填写的字段：`preset`、`body_profile_reason`（compact 必填）、`fold_stage` 与理由、卡片 `emphasis` / `verbatim_quote`、保护区 `zone` 与 `reference` 角色；gantt schema 允许未知端点为 null。
- SKILL 硬规则 4 区分 HTML 三层动态阴影与 PPTX 单阴影；00 写明硬规则是摘要，与所有者冲突时以所有者为准。
- 首屏舞台材料不够电影时改放关系图或图表（`fold_stage`），KPI 不够时用关键事实条，不编造；电影状态下限统一为“三个阅读状态 + 收束帧”。
- PPTX 入场 delay 统一为“同一拍起点 + n × 70ms”，并与上游定义和回读对齐；ppt-master 基线写明为 `v6.7.3-2-g523e5bd`。
- HTML-PPT：宿主禁用 headless 时的替代截帧路径；脚手架安装定位与“不复制参考 index.html”；脚本顺序补 ECharts 与 kz-layout-qc。
- 10 的工具表区分安装包内工具与仓库维护者回归（`tests/` 不随包发布）。
- COPY-08 判定改正（原文两问的方向写反）；站点、流式补“步骤”；数据更新不补间；chrome 定义；术语统一为观点句、尾页、讲稿、所有者。

## KZ7-1024-B01 · 分层重构、动效与材质增强、首屏密度、四轨正例
规范结构
- 规范只写设计规则：SKILL.md 精简为四轨与引擎、13 条硬规则与读取顺序；验收方法、门表、工具清单集中到 10；事故叙述、轮次编号、具体模型与工具名、重复条款移出正文（原文见提交 `b487472`）。规则编号沿用，新增 ELEV-01/02、LG-PPTX、MOTION-03…08、CHART-01…05、FOLD-01…05、BODY-01、DRILL-05/06、NOTES-01…03、FILM-PLAN、TYPE-04、IMG-06、CORE-01…07。
- 新增 13「首屏、页面构图与信息密度」；12-reference-patterns 移入 docs/history（ARCO 证据不在公共包，不能作为规范引用）。
- 删除 test_a04_gates 的措辞锚点测试，改为 tests/test_spec_structure.py：每条规则只有一个所有者、引用的规则必须存在、规范正文无事故史标记、文中 token 路径存在、SKILL 引用的文件存在、版本一致。
- tools/build_dist.py：安装包排除 review/agent/docs/history/tests/examples/validation（4.1MB / 99 文件，仓库 58MB）。

材质与阴影
- tokens：`elevation`（rest/raised/overlay 三层暖色阴影、光源偏移、抬升、PPTX 作者值与 ×0.75 导出系数）、`glass.rim/specular/thin/carrier_face_gradient`、`colors.focus`；删除未被读取且与 ≤0.62 规则冲突的 `face_alpha*`。
- kz-glass.css：rim 渐变边、随指针转动；镜面光斑与顶边短高光随指针移动；阴影由 `--kz-lift/--kz-lx/--kz-ly` 插值；无 JS 时 `@property` 悬停抬升；`.kz-thin` 补齐同族材质；电影载体去掉 backdrop-filter（消除与 FILM-05 的冲突）。
- 指针光与阴影配方生成在 `.kz-card,.kz-lit` 上（自定义属性的 var() 在声明元素解析，放 :root 不会随卡片变化）。

动效
- tokens.motion 重构：四条缓动（enter/exit/standard/data）+ CSS linear() 弹簧、分层时长、位移、缩放、错峰、倾斜（正文 4° / hero 6°）、浮动（hero 6px 错相；双菱形 2px 同相，独立 `.kz-mark-float`）、视差、电影参数。
- 入场：reveal 层只用独立 translate/scale；opacity 写在玻璃本层——实测祖先 opacity<1 时 backdrop-filter 全程失效、结束时跳出。行列波浪错峰 + 卡内标题/条目级联；退出改加速曲线（原减速曲线可见时长约 80ms）。
- 新增 `mountSections`（段落首次可见入场）、`mountField`（环境光场视差）、`countUp`、`storyboard`（按 FILM-03 计时生成首尾无缝关键帧）、`drawLinks`（随载体变形的关系连线）；倾斜改共享临界阻尼弹簧，静止停 rAF。
- 电影文字在不同文案的状态间交叉淡入（`--kz-film-text`，可 seek），不再在插值中点硬切。
- 图表：折线自左向右描出（不再整条从零抬起）、柱形错峰长出；类别色序 `charts.categorical` 与部门色分离（已过 dataviz 校验），对照组保留中性色。
- 下钻：从卡片展开、关闭折回；对话框内全部按键不冒泡（含上游 S/O/F/A）。
- 站点跨文档章节转场；HTML-PPT 翻页改为容器瞬时切换、背景与卡片各自淡入、去掉 ±30px 横移；康哲 deck 不加载 html-ppt animations.css。
- PPTX：经 ppt-master `animations.json` 的入场（Fade、随上一项、70ms 错峰、decel 0.7）与 Morph 载体合同（06 MOTION-07）。

首屏与密度
- 验收视口改为浏览器可视区：1280×720、1536×730、1920×940、2560×1080（`tokens.viewports`，取代 `site_viewports`）；qc_plan 对 HTML 三轨都检查矩阵。
- Bento 首屏（12 栏，左 4 导读、右 8 电影与状态条）、KPI 卡、状态条、`.kz-detail-tall`；`KZLayoutQC.inspectFold`（覆盖率 ≥0.45、最大空白 ≤0.18，按实测校准）。
- `KZLayoutQC.inspectOrphans` 孤字检测；`text-wrap: pretty/balance`；中文阅读行宽改为 34em（46ch 只有约 25 字）；`inspectCard` 的 TEXT_OUTSIDE 改按卡边框判断（修正行高 1.25 下字形外溢的误报）。

HTML-PPT 单位
- html-ppt-bridge 只维护一个比率：`--kz-un = innerHeight/720`（不钳制）与 `--kz-u = calc(var(--kz-un)*1px)`；修正矮视口（1080@150%）文字比框大约 18%、捏合缩放反向缩字的问题。

一致性修复
- schema `contract_revision` A06 → 7.0（此前 SKILL 写 A08 而 schema 只接受 A06）；gantt schema 补 owner/department/status/dependencies/start_known/end_known/taskColor（runtime 已读取 department/taskColor）。
- hero 主视觉的 y 偏移登记为构图；宽屏 fluid 铺满、底对齐，不再出现顶带。HERO-05 目录右缘以自身对称边距为锚（原 1212 vs 1224 永远不满足）。
- hero_layout：`html_fluid_fragment`（--kz-u 几何 / --kz-un 字号 / 右锚 / 目录随宽展开 / 入场顺序）；`svg_fragment` 用 tokens 的玻璃渐变与阴影、cover 裁切、根 lang；glass_svg 的阴影与高光长度取 tokens。
- brand_fragments：带 `data-pptx-role` 的路径加稳定 id（ppt-master 6.7 checker 报错）；qc_plan 对运动区域使用 `motion_safety_pad_px`。
- context_pack：路由 13 章、film-plan schema 与参考实现；新增 `motion` 能力（PPTX 动效）。

正例
- examples/reference：站点首页与章节页、流式文档、HTML-PPT（new-deck.sh 原始输出 + build.py 派生，上游 base/runtime 原样随包）、PPTX 导出探针（ppt-master 523e5bd 实际 checker/validate/export/delivery_check，OOXML 回读记录）；组件实验室改用 Bento 首屏。
- examples/validation 下的 6.x 样本保留作回溯，不再作为模板。

# 6.1.3 · 2026-10-07

## A08 · R2 三方审阅回写（玻璃近白高透光、FILM-01 复合判据、门表法定化、计时口径）
- 来源：R2 构建产物（glm-5.3-flash 医学写作 HTML-PPT、gpt-6-luna 入组审核站点）经 codex/bunny/grok 三方独立审阅与我方源码裁决的发现汇总；证据存项目私有工作区 retro_r2 与各审阅文件。
- 新增：09「计时口径」——总耗时必备/单页可选/「双时钟」任务书必须定义对象与语义（闭合 R2-N01）。
- 修复：runtime/kz-glass.css 补 `.kz-dialog-body` 正文字号规则（R2-F11 参考实现缺口）。
- 修复：tokens.glass 卡面三停改近白高透光（alpha ≤0.62）+ `.kz-card::after` 局部短高光，消除 LG-04 与「不得米黄实色」的张力（R2-bunny#16 规范缺陷）。
- 修复：`.kz-dirty` 改 absolute 浮层合同 + GANTT-04 真实指针验收条款（R2-F05/bunny#2 规范缺陷）。
- 新增：06 FILM-01 复合判据（几何+新信息对象+退出三条件，纯载体膨胀不计独立状态）与主载体文字落矩形条款（R2-bunny FILM 专项规范缺陷）。
- 新增：11 HERO-05 宽屏展开机检判据（≤2px）、HERO-02 目录说明换行行宽。
- 新增：07 DRILL-04「无可溢出内容记不适用/未验证」口径。
- 新增：adapters/html-ppt 页码 `.slide-number` 耦合点（R2-F06）。
- 新增：03 COPY-08 语义层示例（「不代表/不构造/规格未定义」类）与业务规则句豁免（R2-codex F10）；范围扩弹层/抽屉层、字面禁语降为示例、两问式主判定与机械化代理指标（R2-bunny B2）。
- 新增：tracks-site 单页章节锚变体合同（R2-codex F12）与三条变体约束（主层信息任务/交互单一所有者/背景盒随段高，R2-bunny B5/C1/C5）；版本语义说明（包 VERSION/REVISION 为唯一权威，tokens/schema 版本独立，R2-codex F13）。
- 新增：06 动态 protected_region 按运动包络登记；SKILL.md 过程合同补 runtime 快照版本锁定记录（VERSION+REVISION+已用模块 sha256）。
- 新增：10 门表法定化（SELF_REPORT 必含 G0–G9 门表小节，逐门 PASS+证据/FAIL/PENDING/N/A+原因；G7-NOTES/G5-PROJ 必填行）；favicon 噪音口径。
- 新增：G5 空洞量化下限（卡/载体/弹层最大内部垂直空隙与尾空隙 >30% 即缺陷，07 落地、10 引用）；06 载体高度由内容导出；04 主视觉可见度自验数字与裁切锚点规则（R2-bunny A8/C2/C7/A11/B6/C4）。
- 新增：06 性能白名单（backdrop-filter 表面禁逐帧动画 width/height）；02 载体嵌套面板材质档位（.kz-thin）。
- 测试夹具：patch_smoke 横向表演 premise 修订——`.kz-dialog-body` 字号规则生效后表演内容换行使表格变为纵可滚，双轴增量被正确路由到表（最近可滚体），夹具补 `white-space:nowrap` 恢复「表仅横向可滚」前提；非 runtime 缺陷。
- 版本同步：VERSION 6.1.3、REVISION KZ6-1007-A08；tests/test_a04_gates.py 哨兵新增 A08 锚。

# 6.1.2 · 2026-10-07

## A07 · R2 构建实机回写（边界宣示禁令、hero 衬底合同、页缘溢出实测）
- 来源：R2 构建产物（glm-5.3-flash 医学写作 HTML-PPT）用户实机审阅四条问题 + 我方 DOM 级复测；证据存项目私有工作区 retro_r2。
- 03 新增 COPY-08 边界宣示禁令：受众为熟悉人机协同分工与证据边界的内部资深人员时，受众可见层禁止呈现「AI 不替代/不等于医学判断」「最终判断由人确认」「仅供参考」「必须人工确认」类边界声明（页标题/卡标题/强调行/bullet/注脚/讲稿一律删除）；源材料边界条款登记 fact-map 即可；判断标准为「删掉后业务信息无损即属宣示」。业务规则本身（知识库优先级、可回溯、不一致处置流向）不受限。事故：R2 产物整页以「使用边界」为标题，三卡底部分别缀「不直接替代医学撰写经理的最终判断」等宣示句。
- 11 HERO-03 新增文字区衬底与主视觉铺满合同：hero 页主视觉承载文字的区域必须 ①生成时策划为低频低对比构图 或 ②合成态加同层级虚化/渐变遮罩/暗化衬底；不允许清晰高对比主体直接置于标题笔画之下；验收以合成态文字笔画区取样对比为准，裸图通过不代替合成态可读性。主视觉未铺满产生的未覆盖带（顶部白条、侧缘缺口）须在 page-plan 登记几何与理由并过审，未登记空白带按缺陷处理。事故：R2 封面/目录/章节页文字直接压清晰亮图，封面顶部出现未登记白带。
- 10 「几何与文字」新增页缘溢出实测条款：每个交付视口逐页逐卡 getBoundingClientRect 底/右对页面边界求差，>2px 即失败；卡内叶级文字 Range 矩形不得越过卡片左右内边界 >1px；CSS 裁切使滚动不可见不等于无溢出；卡内容分布沿用 03 TYPE-02 T/B/H/R 阈值，无测量记录不得自述通过。事故：R2 产物 s5 卡超页面下缘 68px（1280 视口 118px）、甘特卡内 20 处文字横向溢出、边界页卡下空白 52%——03 TYPE-02 阈值与 03:15 容量处置原有条款已覆盖但未被构建者执行，本条把测量方法与「scroll 裁切不可见≠通过」显性化。
- 版本同步：VERSION 6.1.2、REVISION KZ6-1007-A07，README/INSTALL/00/10/CURRENT_STATUS/VALIDATION_STATUS/CURRENT_HANDOFF 同步；tests/test_a04_gates.py 哨兵锚定 COPY-08/边界宣示、文字区衬底/主视觉铺满合同、页缘溢出实测/getBoundingClientRect。pytest 93 绿。

# 6.1.1 · 2026-10-06

## A06 · R1 双轨盲审回写（字号换算类型缺陷、模态键/滚轮路由、品牌几何收编、状态增量量化）
- 来源：glm-5.3-flash（HTML-PPT 轨）与 gpt-6-luna（站点轨）R1 构建的四路独立审阅（space-bunny、gpt-6.1-sol×2、grok-4.7 简版）加我方实测复核；完整证据与归因存项目私有工作区。
- 修复包缺陷（P0）：`runtime/kz-glass.css` 的 `--kz-component-u:var(--kz-u,1)` 把长度赋给字号换算系数，`calc(px token × 长度)` 整条声明无效，fluid 下组件字号全部回落浏览器默认（实测 1920×1080 卡标题逻辑 10.67px，低于 TYPE-01 地板）。改为 `--kz-component-u:var(--kz-un,1)`；`adapters/html-ppt-bridge.js` 新增 `--kz-un` 无单位比率（视口高/tokens.wide.htmlppt_reference_height，resize 同步）维护。adapter 合同改为双变量显式类型：`--kz-u` 长度仅用于几何（`calc(99 * var(--kz-u))`），`--kz-un` 数字仅用于 px 换算，附非法写法示例；字号验收改为逐实际节点 computed÷u（1280 与 2560，含控件与下钻文字），不只查声明值或卡片正文。
- `runtime/kz-drilldown.js` 补齐 DRILL-03/04 参考机制：翻页键隔离扩至 Enter/Backspace（stopPropagation 不阻碍按钮原生激活）、Tab 焦点圈禁、冒泡阶段滚轮路由（增量交指针之下沿方向仍可滚动的最近滚动体；两端与滚动体外消费，恒 preventDefault+stopPropagation；子控件已 preventDefault 时尊重其取消、不再重复路由，但仍 stopPropagation 使事件不出弹层）。07 DRILL-04 补横向滚动壳 CSS 陷阱（`overflow-x:auto` 使 `overflow-y` 计算为 auto，配 `overscroll-behavior:contain` 形成整块滚轮/触控死区；应 `overscroll-behavior-x:contain` / `-y:auto`），验收须含指针落在溢出子区域的采样。
- 品牌几何收编：`tokens.chrome.header_mark` 新增 `placement_htmlppt_u=[0,0,100,90]`（适配合同原文数值）与 `placement_pptx=native_xml`；adapter 固定双菱形节改以 tokens 为唯一几何权威。事故：R1 构建方自行缩至 37×33.3u 并移至 54/22u。
- 06 FILM-01 量化状态增量：相邻主要状态几何逐项差 >1e-3 或可见节点/连接增减，纯文案替换不构成独立状态；relations 必须有可见 DOM 对应物；验收逐对相邻状态采样，计划声明不作为关系已发展的证据。
- 10 G5-PROJ 补级联：无实机记“投屏可读性未验证”时 G2/G5 门与 SELF_REPORT 结论段同步标注，不得写无条件 PASS。
- tracks-site 补 G7-NOTES 的 N/A 显式声明惯例（站点轨无讲稿容器时须写明原因，不得留空）。
- schemas/page-plan：cards 项新增必填 `detail`（available/not_available/not_needed）与 `detail_reason`，对齐 07 DRILL-01 逐卡规划义务（A05  schema 未开放该字段，计划无法如实登记）。
- 版本同步：VERSION 6.1.1、PACKAGE_MANIFEST（revision KZ6-0929-A06，302 条 sha256 全量重算）。
- chrome 对照合格参照件实测量产（用户提供 MG-K10 方案讨论会 HTML 与研究者会 PPTX）：双菱形四原生形状（橙[24,9,70,62] 黄[5,42,40,36]+candy 层）、标题区、橙色横线 [54,80,1257,1.5px]、Logo [1031,45,158,33]、页脚两槽与页码格式，与 tokens 登记逐项吻合，无需改数；唯页脚日期格式按参照件钉死为 `YYYY年M月`（01-core 与 tokens.chrome.footer.date_format）。

## A06 · 补丁复审回写（space-bunny / grok-4.7 复审，gpt-6.1-sol 复审中断后以合并清单为准）
- `kz-drilldown.js` 真缺陷修复：`deltaMode===2` 分支误用不存在的变量 `g`（IIFE 形参为 `global`），DOM_DELTA_PAGE 滚轮事件抛 ReferenceError 且 preventDefault 不执行；已改 `global.innerHeight`。滚轮路由改双轴独立行走：Y 与 X 各找指针之下沿该方向仍可滚动的最近滚动体，横向命中不再吞掉同一事件的纵向增量（触控板单事件常带两个分量）。触控隔离补 touchstart/touchmove/touchend 阻止冒泡（不 preventDefault，弹层内原生滚动保留）并加 `data-no-swipe` 供上游引擎 interactive() 识别。焦点圈禁补标题位：h2[tabIndex=-1] 不在 Tab 环内，焦点落于环外节点时按方向收拢到首/末可聚焦件。 wheel 处理器开头尊重 `e.defaultPrevented`。
- `html-ppt-bridge.js`：`--kz-un` 下限钳 1（窄高视口不缩字，容量处置走 03；与 kz-charts/kz-gantt 的 Math.max(1,…) 一致），beforeprint 收回 1、afterprint 恢复（内联样式压过作者样式表，打印态必须显式重置），并补 visualViewport resize 监听（Safari 工具栏/捏合缩放时 innerHeight 与 100vh 分叉）。
- `kz-glass.css` 组件内部间距随字号走：卡标题下距、列表项间距、按钮 min-height/padding/gap 乘 `--kz-component-u`（720 基准下不变；按钮 min-height 保留 44px 地板）。
- adapter 双变量合同消除歧义：`--kz-u = calc(100vh/720)` 明写为长度；自定义字号合法写法只有 `calc(24px * var(--kz-un))` 或几何量 `calc(24 * var(--kz-u))`；预缩放与 `--kz-un` 二选一，不得把已乘 `--kz-u` 的值再交给 `--kz-component-u`。A03 历史样本的预乘写法在 README 显式标注不得照抄（vendor 为冻结快照，不改写历史证据）。
- 权威链闭合：00-authority 明确双菱形 HTML-PPT 放置矩形以 `tokens.chrome.header_mark.placement_htmlppt_u` 为唯一权威（视图框坐标 [x,y,w,h]，tokens 增加 format 注记），PPTX 走 native_xml；tests/test_header_mark.py 新增 placement 字段断言。
- page-plan schema 破坏性变更正式升版：schema_version const 6.0→6.1、$id→urn:kangzhe:page-plan:6.1、contract_revision const A04→A06；两份夹具同步升版：A02 hero 示例（HTML-PPT 轨）补齐 detail/detail_reason/motion_objects/target_viewports/contract_revision；agent/fixtures 夹具为 PPTX 轨计划、无 motion_objects（可选字段），仅补 detail/detail_reason/target_viewports/contract_revision，A02 目录页网格 rect 按现行 hero_layout token 修正（此前被 SCHEMA 早退掩盖）；SKILL.md、test_hero.py 引用同步。pytest 91 项通过，qc_plan 对两份夹具零 error。
- 闸门措辞收敛：G5-PROJ 级联范围限定为 G2/G5/SELF_REPORT 结论段（SELF_REPORT 定义为交付随附验收自述的结论段），其余门按各自证据独立判定；G7-NOTES 在 10 章本体增加 N/A 分支，tracks-stream 同步（此前只在 tracks-site）。
- 06 FILM-01 补：归一化坐标分母写明（相对电影舞台宽高的 0–1 比例）；环回状态对归 FILM-04 接续比较（1e-4），不计入相邻状态增量采样。examples/film-plan.json 四对几何全等的相邻状态合并为 4 状态（环回保持）。
- 措辞勘误：DRILL-04 路由实际在冒泡阶段（无 capture:true），drilldown.js 注释、07、CHANGELOG 原「捕获阶段」表述统一改「冒泡阶段」；07 DRILL-04 补三类必验形态（双轴增量、触控滑动、实现取舍知情——手动 scrollTop 换确定性、丢平滑/惯性）。
- 版本串补齐：REVISION→KZ6-0929-A06；README、INSTALL、00-authority、10-quality-gates、CURRENT_STATUS、VALIDATION_STATUS、agent/CURRENT_HANDOFF 全部同步 6.1.1/A06（ECharts 6.1.0 为库版本号，不动）。
- 运行时冒烟扩展重跑（playwright-core + Chromium，1920×1080）：原 9 项基础上新增双轴滚轮（dx=120 且 dy=150 同时生效）、deltaMode=2 不抛错、触控三事件零冒泡+data-no-swipe、标题位 Tab/Shift+Tab 收拢，共 14 项全过。
- 已知边界（记录在案，不展开修复）：page 级背景图的逐图 detail 登记未开放（DRILL-01 目前只覆盖 cards）；数字输入与部分 select 的滚轮默认动作在弹层内被取消（路由确定性取舍，07 已注明）。
## A06 · 终审回写（gpt-6.1-sol / space-bunny 终审，修复已落地并实测）
- `kz-drilldown.js` 滚轮早退泄漏修复：子控件已 preventDefault 时原实现直接 return、不 stopPropagation，事件穿出弹层触发宿主翻页；改为 `defaultPrevented → stopPropagation 后 return`（事件不出弹层的隔离不变量对所有路径成立）。
- `kz-drilldown.js` 平滑滚动吞增量：宿主或 UA 样式 `scroll-behavior:smooth` 时手动 `scrollTop` 赋值被动画化、连续增量相互覆盖，路由丢失确定性；改为赋值前临时内联 `scrollBehavior='auto'`、赋值后恢复（instant 辅助函数）。deltaMode=2（整页滚动）时 X 轴分母改用 innerWidth（原为 innerHeight，宽屏横向页滚动距离失真）。
- `kz-drilldown.js` 焦点候选过滤补强：`:disabled` 用 `el.matches` 判定（字段集禁用继承）、排除 `[inert]` 子树、查 computed visibility/display（仅 offsetParent 会漏 `visibility:hidden`）。触控隔离补 `touchcancel`。
- `html-ppt-bridge.js` 打印不变量：新增 `printing` 标志——beforeprint 锁定 `--kz-un=1`、打印期间 resize 不改写、afterprint 恢复原值；抽出 `writeRatio()` 统一写入并广播 `kz:fluidratio` 事件供运行时组件重渲染。视口高取 `visualViewport.height||innerHeight`。
- `kz-charts.js` / `kz-gantt.js` 流体适配闭环：各自新增 `fluidUnit(el)`（fluid 模式读 :root `--kz-un`，弹层内经 `el.closest('.kz-dialog')` 正确解析，`document.body` 空防御）；监听 `kz:fluidratio` 重渲染（charts 纳入 releaseAll 释放清单，gantt 复用既有 AbortSignal）。修复前弹层内图表字号按视口而非弹层缩放。
- adapter html-ppt 字号合同收敛为单一规则：自定义字号只许 `calc(24px * var(--kz-un))`，`--kz-u`（长度变量）禁用于 font-size——矮视口下两种写法分叉且验收不可判定；验收分母统一为 `--kz-un` 使用值。
- 06 FILM-01 口径补全：归一化坐标分母（载体短边系数直接比）与 tint 比较口径（RGB 分量 ÷255、alpha 直接比）写明，消除「几何差>1e-3」在实现侧的解读空间。
- A02 目录三卡 ambient `none→float`：目录卡片为主要内容载体，HERO-05 要求 hero 页元素有环境动效登记，none 与示例其余页不一致。
- `kz-glass.css` 组件间距补乘 `--kz-component-u`（第二轮）：.kz-thin/.kz-marker/.kz-chart（高 350px）/.kz-chart-status/.kz-film-stage（440px）/按钮 radius 16px/dialog head/body padding；卡 padding 与 grid gap 保持项目域不动（版心尺度属项目决策，规范不预乘）。
- tokens 对齐实测：`dialog_height_vh` 88→94（对齐 kz-glass.css 实测值）；build_tokens.py 新增派生 `--kz-dialog-width`/`--kz-dialog-max-height`，kz-glass.css 改消费变量、不再硬编码。
- 闸门措辞唯一口径：tracks-site 与 tracks-stream 的 G7-NOTES 描述统一为「以 10-quality-gates 该门条文为唯一口径」，消除轨道文件与闸门本体的措辞漂移。
- tests/test_a04_gates.py 新增 `test_gate_wording_anchors`：哨兵串断言（投屏可读性未验证/SELF_REPORT/唯一口径/禁用于 font-size/kz:fluidratio/除以 255/FILM-04），防终审条款在后续编辑中静默丢失。
- tests/test_header_mark.py 新增 `test_placement_fields_registered_in_tokens` 与 `test_svg_asset_viewbox_matches_placement`：正则解析 SVG viewBox 与 tokens placement 对拍，品牌几何漂移由测试拦截。
- 冒烟扩至 17 项：新增 defaultPrevented 包容（子控件取消后事件不出弹层）、scroll-behavior:smooth 下 200ms 内增量不丢失、打印三段（beforeprint 锁 1 / 期间 resize 不改写 / afterprint 恢复）断言，全过。
- .gitignore 补 `.pytest_cache/`。
- 终审后措辞勘误（冻结后非阻断项，由 bunny R3 §3 提出）：10 章 G5-PROJ 与 03 章「除以主题 u」统一为「除以 `--kz-un` 使用值（含钳制与打印锁定）」，消除 `--kz-u`/`--kz-un` 双变量下的解读歧义；哨兵测试同步锚定两章 `--kz-un` 且禁「主题u」回退。终审结论（codex+bunny 双「可冻结」）：16 项修复核验全对、93 pytest 绿、manifest 302 条 0 不符、无新 P0；非阻断建议另两条留档（A02 实建件早于计划属冻结证据；bridge beforeprint 先于图表注册致打印重绘两次，终态正确仅冗余）。



## A05 · 阶段性汇报实战回写（电影中断安全、模态滚动、状态可辨、讲稿时钟）
- 来源：医学部阶段性汇报（HTML-PPT 与站点融合、逐页动画电影、多层级下钻、S 键讲者窗）十余轮返工中已定位的真实失败模式；条款只收不变量与验收法，事故细节留在本条目。三方会商（gpt-6.1-sol / grok-4.7 / space-bunny）记录存项目私有工作区。
- 06 FILM-05 补中断安全：暂停/seek/再次进入/编辑打断只终止自有补间且限其正在写入的属性；禁止不区分属性的 kill/clear/overwrite 连带终止同时间轴未开始的补间；重开以整条时间轴为单位；锚点可见性须符合进度。事故：GSAP killTweensOf 未限定属性，误杀未开始的 autoAlpha tween，主令牌永久 opacity 0；静态截图与录屏均不可见，由播放中段 computed 断言发现。
- 06 新增第 16 节状态可辨识性：状态差不得只由细描边或低于 TYPE-01 地板的标注承载；流程需要区分三态时，已过态须保留不依赖动画的完成标记；手段不规定数量，示例移 12；减少动态与静态总览下区分仍成立。§15 审阅样本补中断-恢复帧与“主要叙事状态须有新增解释价值”的观看判定。
- FILM-03 补：并行车道/并列分支同时建立（优先于 70ms 间隔默认值）；关键解释第一圈即完整可读；连续多页不追求统一片长、避免同一开场结构。
- 07 新增 DRILL-04 模态期间内部滚动优先：模态打开期间页面翻页暂停；滚动增量交给指针下仍可滚动的最近滚动体；到边缘或滚动体外消费事件，不链式滚背景、不翻页。事故：全局 wheel 捕获无条件拦截，弹窗 267px 溢出内容完全不可达。
- 10：G7 最小证据补登记锚元素中断-恢复后可见性断言（G7-ANCHOR，锚清单登记于 QC 旁注，不改 film-plan schema，个数不设上限）；G8 补可滚动层真实滚轮双向放行与边缘吞没；G5 方法补投屏可读性（最大交付视口 100% 渲染加实际观看条件判定；截图缩小不是等价代理；无实机记“投屏可读性未验证”）。
- 09 新增校准锚（只提问、不设字数区间、不以句数触发诊断）与“讲稿与电影共用同一业务时钟”（讲稿不得指向尚未出现或已消失的状态；静态摘要持续保有，不要求逐帧完整）。
- 03 新增 COPY-07 卡内嵌装饰图构图：图固定一侧、向文字侧渐隐至近白、文字落近白侧；证据图/图表/影像除外；不催生新图；PPTX 文字不栅格进图。
- 00 补：融合形态不是第五轨，须声明导航/缩放/讲者窗口/chrome 的轨道归属。
- 会商否决未入条款：投屏截图 50% 缩放代理（只是降采样，不构成观看距离等价）、状态变化“至少两项属性”计数（不可定位失败）、讲稿 100–150 字通用区间（数字即成硬门）。
- 第二轮复审（同三家）后修订：FILM-05 锚点登记位置与 G7-ANCHOR 对齐（schema 未开放时登记于 QC 旁注）；09 双时钟节消除 static_summary 逐帧误读、删去与 FILM-03 重复的第二圈句；校准锚删句数触发；第 16 节术语对齐（当前对象/状态进入前中后/target_viewports）；新增 G7-NOTES 验收段；G5-PROJ 补 PPTX 画幅口径。
- 版本同步：PACKAGE_MANIFEST（version 6.1.0 / revision KZ6-0929-A05，全部 302 条 sha256 重算）、README、INSTALL、CURRENT_STATUS 头、VALIDATION_STATUS 头、CURRENT_HANDOFF 头。review/LOCAL_VALIDATION.json 保留 6.0.0 历史验证快照不改写；各历史轮次记录（R12–R23）保留原文。

# A04 R23 · 用户指定快速收尾
- 修下钻背景文字重影、背景CSS动画争用与多实例滚动恢复；弹窗正文与电影不模糊、不降低动画速度。
- 补有界词组、统一否定重点、真实浏览器换行与目录整卡运动保护；修实际H08行首标点，源事实保留。
- 生图能力发现纠正：实际服务customConfig原生2560×1088已验证，脚本缺参数不再等同服务缺能力。
- 90项合同及真实Chrome下钻组件通过；H08受影响56层级/事实检查通过；两上游/Office/跨模型证据保持各自范围。
- 按用户要求不再派新测试；发布安装与完整四轨两轮验收分开，未完成项/STOP不改绿。

# A04 R17 · 静态布局、退出顺序与循环数据验收
- 固定hero文字框由tokens计算右留距，保持角色字号与左锚；正文和背景仍占满宽屏。
- 静态布局绑定实际总览几何，分别验证preview/RM/capture/print；普通动画保留。
- 原速验证业务阅读真实显露、子信息先退出再收缩、第二圈图数同步及隐藏恢复；无越界不替代这些门。
- 自动记忆隔离以配置与真实工具轨迹核验；盲审区分实际硬规则、条件、诊断与审美建议。
- 新fresh独立Gemini规范差异审正常154.867秒，四文档0硬问题；这是规范审，不是四轨验收。
- 实际DS配额、EGO工具/空间、真实生图像素接口仍阻塞；不降低生图、字号、可编辑和指定引擎要求。

# A04 R15 · 非正文页码门与可移植启动
- 增加HERO-CHROME，补adapter页码仅正文的明确边界。
- 明确复制实际上游原件、file/HTTP正常启动和Film外层root接口。
- 手换行保护中文语义单元；不改字号、条件与正常全角标点。
- 90组件通过；独立审阅发现的新接口歧义已修并取得fresh复审。整体验收仍未完成。

# A04 R14 修订
- 站点/流式responsive档显式记录实际字号，同角色一致/16px地板不变；PPT固定角色检查补齐。
- Charts/Gantt/mountPage初始化回滚、宿主唯一全局与CSS后台owner清理；普通图表入场不先跳到满值。
- 历史A03仅同步当前JS以测生命周期，现行视觉按tokens/design_specs；89合同和真实分层检查见R14状态。
- 保留未完成门、原始失败与真实像素WARN。不是最终验收版本声明。

# 6.0.0 · 2026-09-29

## 2026-10-01 A04 R12 候选（安装/发布以实际回执为准）
- R11已发布并安装；以下早期“候选/未冻结”段落是保留的开发历史，不是当前安装状态。R11正式目录采用同一阅读基线，早期有/无说明变体已被取代。
- 真实普通HTML-PPT报“载体关键帧超出舞台”；API补明当前构造器的归一化边界与初始化状态，质量门分开普通态、静态导出和数据联动。
- 真实流式全周期机械通过后，独立盲审仍发现首页短文子卡巨高空白；新增嵌套阅读组纵向核对，不把父载体内容跨度当子卡通过。居中短卡与卡外留白按实际测量裁决。
- 本候选修复已证实的接口、校验器与共享组件缺口；作者实物修复和四轨最终验收仍在执行，不记为全包完成。
- 修复qc_plan对合法目录说明的误拒：说明可按实际槽位缺省，但出现时必须在固定槽且不重复；补混合/全有/全无说明及错位/重复回归。
- Film dispose清除根的ready/progress运行态，保留载体身份；真实Chrome销毁/重建检查通过。
- Gantt编辑区键盘事件不冒泡至HTML-PPT翻页器，保留按钮原生Enter/Space激活、select默认事件与图上键盘编辑；实际组件Chrome及Luna执行的两档28项上游交互通过。select默认事件未阻止不等于特定操作系统一定改变选项。
- 真实Default制作补核原生数据对象阅读底板与上游静态decoration接口。PPTX七页原生放映、新鲜独立VLM静态零确认缺陷、隔离副本中文/表格/形状编辑保存重开已完成；生图像素和四轨最终两轮/保留集仍未关闭。

- 图表轴由完整真值固定并生成1/2/5整齐刻度，保留科学显式尺度；有限极值/下溢回退与单端科学范围冲突早拒，长数组不做无界参数展开。季度起点非Q1仍显示年季，半开末界不伪作新年份任务。真实Chrome15探针通过，动画性能未据option测试声称。
- 普通与静态HTML导出状态按真实引擎分开，不再要求不存在的freezeForPreview通用接口；孤字行优先统一段落/共同宽度，禁止逐卡缩字或补造事实。

- 修复单一asset_id无法表达responsive双真实源的合同缺口：可选viewport_assets按精确交付视口覆盖；每源仍逐一核生成、真实像素/哈希、crop、保护区和审阅，不降IMG-04。RED七失败后GREEN全67合同，synthetic夹具不当生图。

- 新鲜审阅找到默认回退源漏检和rendition自声明保护区绕过，修复generated schema/默认源实物核验，新增有主体非基准viewport_regions与运动安全外扩；全71合同GREEN，后续新审和实物接入继续。

## A04 R11 未冻结候选
真实原创七页暴露目录无说明时底空白与页眉线端点误读；固定目录阅读变体（按说明有无选用）、HTML卡与文字共父层，并显式标注线端点格式。外框/字号/引擎不变；候选尚未安装或宣称完整产品通过。在途测试继续使用不可变R10。

- 合并4.5.7与5.2.7为一个技能；不继承旧版平面开关、并存说明、遗留色条兼容或旧CSS优先权。
- 建立主题所有者和单一token，四轨共用材料/字体/图表语义；交互降为通用能力而不是第五轨。
- 重写生图规则及生成前/生成后保护门；正文背景可复用但须映射真实批准生成资产。
- 统一15pt/20px正文与整页12pt/16px紧凑下限；取消10.5pt和13.5px等正文/辅助槽混用豁免。
- 主题标题与可选居中观点句分离；正式中文、受众脚注与私有来源分离；讲稿取消逐页定额。
- 全面禁止卡片边缘通长彩条；统一高光/透明/层级，特殊可访问态不成为旧扁平模式回流路径。
- 新写连续电影、同载体身份、首尾接续、暂停原因、静态详情、宽屏和多层下钻合同。
- 提供独立 ECharts / 季度甘特 / 宽下钻 / Film 参考实现与实际组件测试；新增指定上游适配合同。
- 附异质模型+harness评估、归因、修订循环和证据型HANDOFF。未实际完成的集成与生图不记为完成。

## A04 候选修订
- 强制页面布局/逐对象动态、真实资产像素裁切与实际Film接口，明确四轨各自多轮验收。
- 站点只验收桌面宽屏，移除手机/窄屏适配要求；流式与HTML-PPT范围独立。
- 将ARCO业务电影、宽幅多层明细转为有取舍的机制参考，保留同载体、自然滚动、可读性与状态恢复要求。
- 用户指定sci-draw时只调用生图能力，不导入其他视觉规则；实际尺寸与请求分开记录。
- 本修订仍为候选，原A03发布历史保留，未宣布最终放行。

- A04桌面范围QC：页面计划必填target_viewports；站点只要求四档桌面宽屏，生成资产裁切覆盖逐视口核对，保护区/主体框正尺寸与边界检查；42项合同回归通过。视觉盲审误判与制作缺陷分开记录，不将彩色语义表头自动等同装饰色条。

- A04真实轨迹修订：按工序读取与样页落盘门，PPTX排除HTML实现阅读；明确用户指定生图导入原manifest；补充字段/条目口径对账、文字退出先于收小及滚动测试基准。

## A04 固定标记修订
- 用户指定的原生双菱形成为唯一资产；PPTX 导出后直接复用，HTML 同源几何与整组竖直微浮动。删除旧额外折面/白高光/异相位移要求。

## 2026-09-30 A04 品牌装饰适用范围
双菱形仅用于 PPTX 与 HTML-PPT；站点式和流式 HTML 不挂载、不留空占位。固定 PPT 原生资产与 HTML-PPT 微浮动不变。此项已做实际浏览器局部验证，不代表四轨完成验收。

## 2026-09-30 A04 正文背景范围修订
新增 IMG-05 与 G4-BODY：PPTX/HTML-PPT 正文采用近白阅读区、极少量边缘光影；前景同族玻璃壳负责分隔，不给每个元素叠卡。主视觉页仍按自己的保护区构图。本次为规则范围修订，不纳入在途共享运行时代码，不代表四轨验收完成。

## 2026-09-30 A04 共享组件与验收证据修订
修复动画目标所有权、几何回执、默认文字约束及真实布局测量；补入七套真实浏览器反例回归。明确不调用原生Excel，保留PPTX原生对象与PowerPoint编辑回读。HTML-PPT正式静态截帧以官方renderer加派生副本，不取消观众自动动效。四轨整体仍在验收循环，组件通过不等于整包无缺陷。

## A04 下钻容量 R9
- 真实双家族盲审发现宽幅下钻固定高度与表格偏左；桌面保持82vw但按内容 fit-content、限制94vh、长内容单独滚动；单层不重复面包屑，多层完整返回路径。
- 固定列阅读遮罩允许同族不透明浅底，保留外壳玻璃；新增容量/遮挡验收。实际短/长内容、滚动、焦点与层栈Chrome回归、53组件和47合同通过。
- Luna/max现成SVG的Default完整引擎重放正常完成，单列为引擎证据。CodeBuddy429至2026-09-30 22:28:20，不能计中断制作通过。四轨最终两轮/保留集仍未完成。

## 2026-09-30 A04 R10 工序与真实交互核查
- context_pack新增bootstrap/plan/assets/author/verify，owner hash及同会话已读声明；默认旧read_files兼容，终审保留完整规则。
- runtime/API.md列实际接口、上游责任与standalone exit取消句柄；没有新增演示引擎或第二套计划validator。
- 独立Sol真实审阅发现桥异常状态/初始化泄漏；Chrome复现后修复事务初始化、成功后提交活动状态、全量销毁后聚合错误。3异常与5正常浏览器检查通过。
- 真实HTML-PPT鼠标驻留发现reveal祖先preserve-3d造成hover立即复位，06加入实际合成指导及真实pointer驻留测试；当前测试者实物仍待修复，规范文字不是成功证明。
- 51合同通过；整包仍持续验证，不计最终两轮或holdout。

R10最终组件检查：桥四项异常路径及五项正常生命周期在真实Chrome通过；51合同通过。新增真实pointer驻留门不代表失败作者实物已修好。流式owner最新R9 runtime六场景×两档12个自然完整周期，1948样本、0可见文字越界、同carrier与双层返回焦点通过，仍非指定模型制作终态或最终四轨轮。

R11候选另由真实Chrome确认fluid u=1.5共享控件仍16屏幕px（10.67逻辑）违反TYPE-01；加入仅fluid组件文字单位换算，站点/流式保持屏幕值。待实际接入与独立复审，不记为指定tester成功。

## 2026-09-30 A04 R11 候选
- 目录改为一套共同号码/标题基线，有真实说明放下方槽，不造空块；显式卡身份、转义和粗筛/实际字形边界分开。
- HTML-PPT fluid共享UI字体按同一u换算，其余HTML保持屏幕字号；57合同及真实Chrome目标组件通过，独立v4冻结源/帧复审无确认产品缺陷。
- 接口提示舞台height与min-height、离页暂停原因须成对恢复；匿名新七页仍有真实撞字，保留失败继续修。
- 站点真实串行8首页/章节自然周期及L2-A30秒已有129项检查0失败，未测B/C完整周期、真实hidden/EGO仍不关闭。整体仍PARTIAL。
