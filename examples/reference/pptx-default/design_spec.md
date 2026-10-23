<!-- ppt-master-schema: design-spec/v1 -->
# 研究资料完整性核对（合成示例） - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | kangzhe_integrity_ppt169_20261024 |
| Canvas Format | ppt169 (1280×720) |
| Page Count | 6 |
| Primary Language | zh-CN |
| Target Audience | 产品中心医学部内部例会的同事，熟悉研究资料审阅流程，关心资料是否齐全、缺口由谁补、何时能进入比较 |
| Communication Intent | 先报告资料完整性核对结果并说明缺口与处理口径，再就补收与版本确认的分工和时间达成一致 |
| Desired Audience Outcome | 与会者知道 24 份应收资料中缺 4 份及其所在资料组，接受“缺失保留为空值、差异确认后再比较”的口径，并认可 2027Q1 前完成补收与确认的安排 |
| Core Message / Ask / Action | 资料整体可用，但中心记录与安全性报告共缺 4 份、两版方案有 2 项差异；补收与确认在 2027Q1 内完成后再做组间比较 |
| Delivery Context | 主要为有主讲人的约 10 分钟内部例会投屏；次要为会后存档查阅 |
| Artifact Afterlife | 作为核对进度记录，供后续复核与审阅意见引用 |
| Reading Mode | balanced |
| Content Strategy | balanced default（content_divergence 留空） |
| Design Style | 结论先行的核对汇报（custom mode）+ 康哲 Liquid Glass（custom visual style，品牌固定） |
| AI Image Acquisition Path | not applicable（image_usage = provided） |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | enabled — explicit user instruction（“需要自动入场动效”，对象级入场）+ final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-10-24 |

- **Brand authority**: the user named the installed `kangzhe-design` skill as the brand and visual authority. Its tokens fix palette, typography, page chrome, hero layouts (cover-01 / toc-01 / ending-01) and the glass recipe; ppt-master supplies the engine, checker and export.
- **Typography correction (user, after Stage 2)**: the confirm page re-derived role sizes from the 20 px body (title 36, subtitle 28). The user then stated in chat that page titles follow the Kangzhe 24 pt rule: title 32 px, subtitle (card title) 24 px, annotation 16 px. This explicit later instruction supersedes the page values; body 20 px is unchanged.

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | body pages: Kangzhe chrome — title band y 24–68, rule y 80, footer y 682–708; hero pages: tokens.hero_layouts |
| Content Area | body pages x 56–1224, y 96–660 (tokens.chrome.body 56/96/1168/564) |

## III. Visual Theme

### Theme Style

- **Mode**: custom
- **Mode Behavior**: 封面即给出核对结论（应收 24、已收 20）；目录按“范围—结果—计划”三步；正文页标题写内容名称，页内先放关键事实再放解释；资料完整性页用原生分组柱图配一句观点句；核对计划页用原生形状甘特；结束页落到会上需要确认的两件事。
- **Visual style**: custom
- **Visual Style Behavior**: 康哲 Liquid Glass。近白浅底；正文页固定 chrome（左上原生双菱形、单行页标题、橙色横线、右上官方 Logo、两槽页脚）；内容放在同族玻璃卡里，三种手段叠加：三停近白半透明渐变面、中性细折光边与顶边短高光、一个暖褐柔和外阴影（elevation.pptx.rest）。卡标题加粗墨色，正文分条，普通重点加粗、关键缺口用深红；不用任何通长彩色边条；数据面平直，不透视、不倾斜。
- **Theme**: 康哲药业医学部正式汇报；浅白光场 + 少量橙黄折射 + 同族玻璃卡 + 稳定深色文字。
- **Tone**: 专业、克制、可核对。
- **Motif**: 正文页的双菱形 + 橙色横线是唯一跨页品牌母题；hero 页（封面、目录、结束页）使用同族光学玻璃背景图与目录玻璃卡。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FBFCFD | 页面浅底（tokens.colors.canvas） |
| Secondary background | #FFFFFF | 玻璃卡面高光停点、表格底 |
| Primary | #FF9900 | 品牌橙：正文页横线、目录序号、图表“已收”以外的品牌识别（不作小字号正文色） |
| Accent | #FFCC00 | 辅黄：双菱形小形与光学点缀 |
| Secondary accent | #C00000 | 深红：只用于关键缺口、风险与待确认（03 COPY-04） |
| Body text | #404040 | 正文灰 |
| Secondary text | #64676B | 注释、图例说明、页脚以外的弱化文字 |
| Divider | #CED3D8 | 图表轴线、表格细线 |

- **Ink**: #0F1115 for page titles, card titles and hero titles (tokens.colors.ink).
- **Footer**: #808080 (tokens.colors.footer).
- **Chart roles**: comparator #6E7B8C（“应收”参照量）, categorical[0] #D46B08（“已收”）, grid #E7EBEE, axis #CED3D8, label #404040 (tokens.charts).
- **Department roles (gantt only)**: 医学部 #FF9900, 数统 #587B3B, PV #A85F34 (tokens.departments).

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | 中性无衬线、加粗、墨色 | Microsoft YaHei | Arial | sans-serif |
| Body | 中性无衬线 | Microsoft YaHei | Arial | sans-serif |

- **Title stack**: Microsoft YaHei, Arial, sans-serif
- **Body stack**: Microsoft YaHei, Arial, sans-serif

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 20 |
| Title | 32 |
| Subtitle | 24 |
| Annotation | 16 |
| Card title | 24 |
| Takeaway | 24 |
| Footer | 18 |
| Cover title | 56 |
| Hero subtitle | 28 |
| Hero meta | 20 |
| TOC title | 48 |
| TOC number | 40 |
| TOC label | 32 |
| Ending title | 104 |

- **Role rationale**: card title, takeaway, footer and the hero roles are Kangzhe fixed roles (tokens.type_px); they share the Title/Body families and add no extra font.

## V. Layout Principles

### Deck-wide Direction

- **Hierarchy direction**: 页标题 → 卡标题 → 分条正文 → 观点句（最后出现）；数据页先图后解读。
- **Composition tendency**: 正文页按康哲 BODY-01 预设：研究范围用 cards-3（卡片取内容高度、整组垂直居中）；资料完整性用 split-7-5（左数据卡、右观点句与缺口卡）；核对计划用 full（单卡甘特）。hero 页用 11 的固定形态。
- **Cross-page continuity**: 正文页 chrome 完全一致；hero 页共享光学玻璃背景族。
- **Spacing posture**: variable by page rhythm — cards take content height; no full-height shells around three bullets.
- **Spacing anchors**: page margin 56 px · block gap 24 px · column gutter 24 px · corner radius 24 px (compact 18) · body leading 1.4

## VI. Icon Usage Specification

- **Primary bundled library**: none

| Icon Path | Suitable Scenarios |
| --- | --- |

## VII. Visualization Reference List

| Page | Family | Template | Usage |
| --- | --- | --- | --- |
| P04 | chart | grouped_bar_chart | 四个资料组的应收与已收份数并列比较，显出缺口所在 |
| P05 | chart | gantt_chart | 五项核对任务按季度排布，标出负责部门 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cover_hero.png | 1672×941 | 1.78 | 封面主视觉 | Background | 全幅背景，主体在画面下部，左上标题区为低频浅色 | adaptive | user | Existing | 历史真实生成图（康哲 A03 批次，sha256 aa4f7119…），用户提供 | none | hero_page |
| toc_hero.png | 1672×941 | 1.78 | 目录主视觉 | Background | 全幅背景，目录玻璃卡浮于其上，上部留给“汇报章节”标题 | adaptive | user | Existing | 历史真实生成图（sha256 566c6ad9…），用户提供 | none | hero_page |
| ending_hero.png | 1672×941 | 1.78 | 结束页主视觉 | Background | 全幅背景，左侧结束语区为浅色低频 | adaptive | user | Existing | 历史真实生成图（sha256 33680aee…），用户提供 | none | hero_page |
| body_quiet.png | 1672×941 | 1.78 | 正文页安静背景 | Background | 全幅近白背景，只在边缘有极淡光影，三张正文页复用 | adaptive | user | Existing | 历史真实生成正文背景（sha256 ce197776…），用户提供 | none | local |
| logo.png | 1210×250 | 4.84 | 官方 Logo（hero 页与正文页右上） | Logo | 按 kangzhe tokens 的 Logo 框原样放置，保持比例 | no-crop | user | Existing | 由 kangzhe-design assets/logo_bot.svg（sha256 8d16d3ae…）原样渲染的透明 PNG，10×，未重绘 | none | local |

## IX. Content Outline

### Part 1: 开场

#### Slide 01 - 封面

- **Audience move**: 不知道核对结论 → 一眼知道资料大体齐全但有缺口
- **Relationships**: none
- **Composition**: 康哲 cover-01：左上官方 Logo，左对齐大标题，其下副标题承载核对结论，再下单位与日期；主视觉作背景
- **Title**: 研究资料完整性核对
- **Core message**: 应收 24 份，已收 20 份
- **Content**: 标题 研究资料完整性核对 · 副标题 合成示例｜应收 24 份，已收 20 份 · 元信息 产品中心-医学部｜2026年10月
- **Cover impact**: hook = “应收 24 份，已收 20 份”（binding）；composition is a Reference
- **Data class**: scenario（全部数值为合成示例）

#### Slide 02 - 目录

- **Audience move**: 知道结论 → 知道汇报按范围、结果、计划三步展开
- **Relationships**: order — 研究范围 → 资料完整性 → 核对计划
- **Composition**: 康哲 toc-01：左上“汇报章节”，右上 Logo，三张等宽玻璃卡一行
- **Title**: 汇报章节
- **Core message**: 范围、结果、计划三部分
- **Content**: 01 研究范围 / 对象、时间窗与资料组 · 02 资料完整性 / 应收与已收、缺口所在 · 03 核对计划 / 补收、确认与复核

### Part 2: 范围与结果

#### Slide 03 - 研究范围

- **Audience move**: 不清楚核对边界 → 知道核对针对哪些人群、时间窗、资料组与方案版本
- **Relationships**: membership — 四个资料组属于纳入资料；contrast — V2.1 与 V2.3 两个方案版本
- **Composition**: cards-3：三张并列文字卡，取内容高度、整组垂直居中
- **Title**: 研究范围
- **Core message**: 核对覆盖成人受试者第 16 周的四组资料，并比较两个方案版本
- **Content**:
  - 卡 1 研究人群与时间窗：研究对象 成人受试者 · 评价时间窗 第 16 周
  - 卡 2 纳入资料：方案与修订 · 中心记录 · 实验室数据 · 安全性报告（共四组）
  - 卡 3 方案版本：V2.1 与 V2.3 并排比较 · **2 项差异待确认**：筛选窗口、终点评价时间点
- **Motion suggestion**: 三张卡按阅读顺序依次淡入
- **Data class**: scenario

#### Slide 04 - 资料完整性

- **Audience move**: 只知道总数 → 知道缺口在哪两组、缺几份，以及缺失如何处理
- **Relationships**: contrast — 各资料组应收 vs 已收；membership — 4 份缺口分属中心记录（3）与安全性报告（1）
- **Composition**: split-7-5：左侧数据卡撑满高度放分组柱图；右侧上为观点句卡，下为缺口与口径卡
- **Title**: 资料完整性
- **Core message**: 24 份应收资料已收 20 份，缺口集中在中心记录与安全性报告
- **Content**:
  - 图：四个资料组的应收与已收份数（方案与修订 2/2，中心记录 12/9，实验室数据 6/6，安全性报告 4/3），单位 份
  - 观点句：缺口集中在中心记录与安全性报告
  - 卡 缺口与口径：中心记录缺 **3 份** · 安全性报告缺 **1 份** · 缺失保留为空值，不按零处理，也不插补
- **Visualization**: completeness-bars — grouped bar, categories = 资料组, series = 应收（comparator）/ 已收, unit 份
- **Native-ready**: completeness-bars=yes
- **Motion suggestion**: 图表整体自底部擦入，随后缺口卡与观点句依次出现
- **Data class**: scenario

### Part 3: 计划与确认

#### Slide 05 - 核对计划

- **Audience move**: 知道缺口 → 知道谁在什么季度补收、确认与复核
- **Relationships**: order — 补收与差异确认在前，复核与审阅意见在后；membership — 任务归属医学部、数统、PV
- **Composition**: full：单张数据卡承载甘特，季度轴 2026Q4–2027Q2，条形按负责部门着色并带文字标签
- **Title**: 核对计划
- **Core message**: 补收与版本确认在 2027Q1 内完成，复核与审阅意见在 2027Q2
- **Content**:
  - 缺失资料补收｜医学部｜2026Q4–2027Q1
  - 版本差异确认｜医学部｜2027Q1
  - 完整性复核｜数统｜2027Q1–2027Q2
  - 安全性报告核对｜PV｜2027Q1–2027Q2
  - 审阅意见形成｜医学部｜2027Q2
- **Visualization**: check-plan-gantt — gantt, 5 tasks × quarters [2026Q4, 2027Q2], department colour + text label
- **Native-ready**: check-plan-gantt=no
- **Motion suggestion**: 甘特整体自左擦入
- **Data class**: scenario

#### Slide 06 - 结束页

- **Audience move**: 了解计划 → 在会上对两件事表态
- **Relationships**: membership — 两件待确认事项
- **Composition**: 康哲 ending-01：左上 Logo，左侧大号结束语，下接副标题与单位日期；主视觉作背景
- **Title**: 请确认两件事
- **Core message**: 4 份资料 2027Q1 内补收；2 项差异确认后再做组间比较
- **Content**: 结束语 请确认两件事 · 副标题 4 份资料 2027Q1 内补收，2 项差异确认后再比较 · 元信息 产品中心-医学部｜2026年10月
- **Closing impact**: takeaway = 两件待确认事项（binding）；composition is a Reference

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 现场能直接说出口的自然中文（kangzhe-design 09）：每页 0–3 个需要补充的解释点，不复读页面数字；合成示例数据，不引入材料以外的医学判断
- **Total duration**: 约 10 分钟
- **Notes style**: formal, conversational register for an internal meeting
- **Presentation purpose**: 先报告资料完整性核对结果并说明缺口与处理口径，再就补收与版本确认的分工和时间达成一致
