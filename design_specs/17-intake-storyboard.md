# 17 开工卡与分页故事板

开工分两站：第 1 站开工卡一次问完所有会改变做法的选择，第 2 站分页故事板在生成之前把整份 deck 摊开给用户确认。两站之后，上游引擎（ppt-master、html-ppt-skill）的确认页只核对，不再重新提问。2026-11-17 第 1 轮用户认可这两站流程，8.0 起落成工具。

## INTAKE-01 问什么
开工卡的题目是数据（`tools/intake.py` 的 `questions()`），不在对话里临时编：

| 键 | 题目 | 何时问 | 依据 |
|---|---|---|---|
| `track` | 交付形式：可编辑 PPTX / HTML-PPT / 站点式 / 流式 | 总是 | 四轨与引擎（SKILL） |
| `route` | 路线：常规 / 旗舰 | PPTX 与 HTML-PPT，**阻断项** | 14 FLAG-01 |
| `image` | 生图能力：用检测到的能力 / 另指定 / 缺省背景套 | PPTX 与 HTML-PPT，**阻断项** | 04 IMG-07 |
| `background` | 背景风格（`tokens.image.backdrop.styles`，缺省 A2） | 常规路线 | 04 IMG-09 |
| `audience` | 受众与场合 | 总是 | 03 COPY、14 FLAG-01 判据 |
| `motion` | 入场 + 分步演示 / 只做入场 / 静态 | 总是 | 06、15 |
| `scenes` | 包含的临床场景（多选，可留空） | 总是（提问工具降级时不问，按材料判断） | 场景族合同 |
| `pages`、`note` | 页数或时长、备注 | 总是（文字） | — |

表中是题意；答案文件里的取值是 `tools/intake.py` 的 `questions()` 给出的枚举（如 image 写 `generate` / `other` / `default_set`，audience 写 `mgmt` / `dept` / `ext` / `read`），以工具输出为准。信息密度不问：按内容算档（13 BODY-03）。生图能力的题目里写明检测结果（生图 skill、MCP、ppt-master 后端、用户点名的服务）。

## INTAKE-02 怎么问
- 能开浏览器：`intake.py html` 生成选择页，用 ego lite 打开；用户点「确认」后页面显示并下载 `kz-intake.json`。选择页按已选的交付形式与路线隐藏不适用的题目。
- 不能开浏览器：`intake.py ask` 输出提问工具的批次，每批不超过 4 问、每问不超过 4 项，推荐项排第一并标「（推荐）」；已知交付形式时去掉不适用的题，未知时题面写明「仅 PPTX / HTML-PPT 回答」。
- 用户在请求里已经说清的项写进 `--prefill`，选择页预选、提问批次不再出现；修改已有 deck 时沿用它原来的结论，只问改动的部分。
- 两项阻断题必须在同一次停顿里问到；得到明确答复之前不做计划、不生图、不搭脚手架。

## INTAKE-03 答案去哪里
`intake.py apply kz-intake.json` 先校验（取值必须在选项里；PPTX / HTML-PPT 必须有 `route` 与 `image`；`image=other` 时备注写明方式），再给出：
- page-plan 字段 `track`、`route`、`image_capability`；
- 本次要读的 `context_pack.py` 命令（按轨道、路线与场景推出 features）；
- ppt-master 预填：Stage 2 的 `image_usage` / `image_ai_path`（04 IMG-07）、是否带 `animations.json`；确认页只核对康哲字号与这两项（`adapters/ppt-master.md`）；
- html-ppt 预填：不出现主题、配色、字体、动画的询问，主题与配色由 tokens 固定（`adapters/html-ppt.md`）；
- 所选临床场景的四种产物：静态模板、常规演示形式、旗舰舞台、旗舰 PPTX 模板，以及按本次轨道与路线该用哪一个。

## SB-01 分页故事板的内容
page-plan 写好并经 `qc_plan.py` 预检之后、生图与引擎之前，`storyboard.py html page-plan.json` 生成故事板：每页一张卡，一行 3 张（窄于 960px 时一行 1 张，缩略图要看得清），写页码、页型、密度（正文页）、标题、载体与观点句：
- 常规正文页：模板名与用途、该模板示例页的缩略图（`examples/templates` 的示例数据，标注“版式示意”），以及同族可换的其他模板（13 BODY-03）；
- 旗舰正文页：旗舰版式（`flag-*`）或 three.js 舞台与它的步骤（`tokens.flagship.stages.catalog`）；
- 演示页：演示形式；hero 页：hero 版式 id；
- 该页的预检结果（错误红色，提示与待核灰色），整份 deck 的结果列在最上面。
正文页缺 `template` / `stage` / `demo` 时卡片写“未指定”，同时有 `TEMPLATE-MISSING` 提示。

## SB-02 确认与回写
用户逐页点「通过」或「要改」并写备注，「确认」后得到 `kz-storyboard.json`（`pages: [{id, ok, note}]`）。对话里没有浏览器时用 `storyboard.py text` 的 Markdown 表，请用户按页回复。按备注改完 page-plan，重跑预检，有改动的页再给用户看一次，然后才开始生成。故事板不代替视觉放行（10）。
