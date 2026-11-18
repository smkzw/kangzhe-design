---
name: kangzhe-design
description: 康哲药业医学部正式汇报与医学网页的统一 Liquid Glass 设计系统。用于康哲 design、康哲 design 3D、康哲风格、可编辑 PPTX、HTML PPT、站点式 HTML、流式 HTML；PPTX 与 HTML-PPT 分常规与旗舰两条路线（旗舰用于对外与顶层汇报）。PPTX 配合 ppt-master；HTML-PPT 配合 html-ppt-skill。只安装本技能，不再安装旧扁平版或 3D 版。
---
# Kangzhe Design 8.0

品牌、内容表达、视觉、动效与验收层，不是另一套 PPT 引擎。四轨共用一套 tokens 与材质，没有 flat 开关或第二套配色。PPTX 与 HTML-PPT 各有两条路线：常规（日常与内部汇报）和旗舰（对外与顶层汇报，`design_specs/14-flagship.md`）。

## ⛔ 开工两站：开工卡 → 分页故事板（17 INTAKE / SB）
用户要求做 PPTX 或 HTML-PPT 时，必须先停下过开工卡（第 1 站），其中下面两项是阻断项，必须在同一次提问里问到；得到明确答复之前，不做计划、不生图、不搭脚手架、不导出，即使材料已经齐全。站点式与流式 HTML 不触发本阻断。

1. **路线**（14 FLAG-01）：常规或旗舰。先根据材料和用户信息（听众、场合、材料性质、用户措辞、放映环境，判据表见 14 FLAG-01）给出推荐和两三条具体理由，例如“推荐旗舰：这是给集团管理层的季度汇报，结论集中在 3 个数字上，并且会用 Edge 放映”。
   - 常规：01–13 的现行规范，正文页固定 chrome，同族玻璃卡承载内容，正文版式取自模板库（13 BODY-02）。
   - 旗舰（F1）：暖白画布、白纸卡与三层暖影、统一页眉（棱面图标块：斜切橙棱面里放白色章节图标、旁伴小黄棱面 + 完整 kicker + 标题，右上 Logo 与标签）、立体目录与章节编号与页码进度页脚；正文用旗舰版式库（14 FLAG-08）密排卡片，HTML-PPT 按场（scene）逐步编排入场、描线、计数、印章，并按内容从电影化 three.js 舞台组件库选组件（景深、跨场载体、机位运动；14 FLAG-06a，相邻页不重复），PPTX 用图标、卡片组合与原生动画表达。
2. **生图能力**（04 IMG-07；旗舰只决定是否按主题另生封面主视觉，14 FLAG-03）：先检测当前环境的生图能力（生图 skill、MCP 工具、ppt-master 已配置的后端、用户点名的服务），把检测结果写进问题，请用户选：用检测到的能力生图、另指定 skill 或接口、或没有生图能力而用缺省背景套 `assets/backgrounds/`。

**第 1 站 开工卡**：上面两项连同交付形式、背景风格、受众、动效、临床场景、页数一次问完，后面不再重复问；`tools/intake.py html` 出选择页，没有浏览器时 `intake.py ask` 出提问批次，答案 `intake.py apply` 后预填 page-plan 与上游。**第 2 站 分页故事板**：page-plan 预检后、生成前用 `tools/storyboard.py` 请用户逐页确认（17 INTAKE / SB）。

宿主有提问工具时用提问工具（两项阻断问题放在同一次调用里），没有时输出问题并停住等待。用户在本次请求中已经明确回答了某一项时，复述一句即可；修改已有 deck 时沿用它原来的结论。答案写进 page-plan（`route`、`image_capability`），并预填 ppt-master Stage 2 的 `image_usage` / AI 路径（04 IMG-07）；上游确认页不再重新决定生图。生成的图一律经 `tools/quiet_plate.py` 合成到白底并过安静度检查后才能上页（04 IMG-08）。

## 四轨与引擎
| 轨道 | 制作引擎 | 轨道配方 | 参考实现 |
|---|---|---|---|
| 可编辑 PPTX | ppt-master（必须） | `design_specs/tracks-pptx.md` · `adapters/ppt-master.md` | `examples/reference/pptx-default/` |
| HTML-PPT | html-ppt-skill 脚手架（必须） | `design_specs/tracks-htmlppt.md` · `adapters/html-ppt.md` | `examples/reference/htmlppt/` |
| 旗舰路线（PPTX / HTML-PPT） | 同上两行的引擎 | `design_specs/14-flagship.md`（叠加在所选轨道上） | `examples/reference/htmlppt-flagship/` · `examples/reference/pptx-flagship/` · `examples/reference/pptx-flagship-clinical/`（旗舰 PPTX 临床模板，FLAG-12） |
| 站点式 HTML | 项目现有结构 + 本包 runtime | `design_specs/tracks-site.md` | `examples/reference/site/` |
| 流式 HTML | 同上 | `design_specs/tracks-stream.md` | `examples/reference/stream/` |

本包只注入品牌、页面计划、图像保护、组件与 QC；不改上游源码，不另写同类引擎，不叠第二套缩放或翻页。上游真实能力达不到的效果，写明阻塞，不伪造。

## 硬规则（编号指向唯一所有者）
1. 数值只读 `tokens/tokens.json`；改值后运行 `tools/build_tokens.py`（00）。
2. 官方 Logo 只用 `assets/logo_bot.svg` 原件，校验哈希（01 CORE-02）。
3. 双菱形只用于常规路线的 PPTX 与 HTML-PPT 正文页，取自 `assets/header-mark` 原生资产；旗舰、站点与流式不用（02 LG-03、14 FLAG-02/04）。
4. 卡片是同族玻璃：三停渐变面、rim 折光边、短高光；HTML 轨用三层暖色阴影并随指针变化，PPTX 用单个原生外阴影（02 LG-01、ELEV-01、LG-PPTX）；卡片边缘色条绝对禁止，不论长短、不论参照稿或上游模板有没有（LG-02）。旗舰路线的正文用白纸卡与三层暖影，同样不加色条（14 FLAG-05）。
5. 字号守角色合同与下限：正文不小于 12pt；只有脚注、来源、图注、坐标刻度、图例这类说明文字可用 10.5pt（reference），这是全局最小字号；同页同角色同字号同行距；放不下先重排或拆页，不缩字、不裁字；无孤字行（03 TYPE-01/03/04）。
6. 页标题写这一页属于哪一章、讲哪个主题，不写观点，不带冒号、破折号或句读，参照稿用“主题：结论”也不沿用；文字卡有独立卡标题、语义分条与有依据的重点（03 COPY-01/06）。讲稿是讲者直接说的临床试验口语：封面、目录、章节、尾页只一句，不报幕，不用行话和翻译腔，短句（09 NOTES-04/05，`tools/check_notes.py`）。
7. 只为外部论文与权威指南标注来源；内部来源留在私有台账；不把边界声明当内容（03 COPY-05/08）。
8. PPTX/HTML-PPT 每页映射真实生成资产，没有生图能力时经闸门确认后用缺省背景套；正文背景安静、与 hero 主视觉分开策划（04 IMG-01/05/07）。旗舰路线封面用旗舰背景套的主视觉（或按主题另生），其余页用程序化暖白画布（14 FLAG-03）。
9. 数据真实可编辑：HTML 数值图用 ECharts，PPTX 用原生图表；null 不当 0；类别色序固定且独立于部门色（05）。
10. 站点与流式的动画自动发生；HTML-PPT 的电影与演示按 scene 随演讲者的翻页键与滑动推进，最后一个 scene 后才翻页；没有观众播放控件；时钟按真实时间；动作取自 token 化的词汇与编排；电影保持一个载体（06 MOTION-09、FILM-05）。
11. 常规路线的正文页从模板库取版式（`tools/kz_layout.py list`，13 BODY-02）：两轨共用同一份页面数据，同一模板连续不超过两页，每页至少一种视觉载体（图标、图表、表格、示意图）。原文条款（入排标准、用药规则、访视窗、定义、方案表格与脚注）逐字保留，入排标准用 `tools/protocol_lists.py` 从方案 Word 取数据，编号与子项层级照方案，渲染时加 `--source <方案.docx>` 核对原文；篇幅与原文冲突时加页，概览只能另加、不能代替原文；先密排再拆页，编号接续、不写“续”（03 COPY-09）；重点用加粗、深红、下划线、高亮四种标记（03 COPY-04）。导出前跑 `tools/check_kz_project.py`（10 G-KZ）。
12. 讲方法、流程、规则、计算、数据、计划的页面用演示舞台把内容做给观众看：从二十八种数据驱动形式选、相邻演示页换形式，图标与示意图为主、文字为辅，多 scene、高密度、大幅度，流程类演示正例与反例，相邻演示页轮换四种构图预设；只有卡片入场与连线不算演示（15 DEMO-01~09）。
13. 站点与流式的首屏在每个验收视口内一屏放下，采用 Bento 构图并通过密度指标；验收视口是浏览器可视区（13）。
14. 下钻是宽幅多层栈，按键与滚轮不泄漏到宿主（07）；甘特用一份计划合同（季度/月/日，连续时间 [start,end)），HTML 轨按 T 开全页编辑台、改动同步页面与数据（08）。
15. 交付按 10 的门表逐门给证据；组件测试不叫端到端，LibreOffice 不叫 PowerPoint 验收；不调用 Excel。

## 读取顺序
- 必读：`design_specs/00-authority.md`、`01-core.md`、`02-liquid-glass.md`、`03-typography-language.md`、`04-image-pipeline.md`、所选轨道文件；旗舰路线另读 `14-flagship.md`，它替代的常规条文以其 FLAG-02 表为准。
- PPTX / HTML-PPT 含封面、目录、章节、尾页时读 `11-hero-layouts.md`；正文页构图读 `13-layout-density.md` BODY-01 与 BODY-02（模板库），再读所选轨道适配合同里的“模板页”一节。
- 所有 HTML 轨读 `06-motion-film.md` 与 `15-demo-motion.md`；站点与流式读 `13-layout-density.md`；PPTX 需要动效时读 06 MOTION-07 与 15 DEMO-06。
- 智研 METRIC 各子系统的网页页头（医学监查、入排审核、方案撰写、竞品调研等）读 `16-metric-subsystem-header.md`，标志只取 `assets/metric/`。
- 按能力读：图表 05、下钻 07、甘特 08、讲稿 09；终审读 10。
- 本包的工具需要 Python 3.10+ 与 `requirements.txt`（jsonschema、Pillow、numpy）。把本文件所在目录记为 `KZ_DIR`，命令写成 `python3 "$KZ_DIR/tools/…"`，不依赖当前目录。
- `python3 "$KZ_DIR/tools/context_pack.py" --track <pptx|htmlppt|site|stream> [--route flagship] --stage <bootstrap|plan|assets|author|verify> --features charts,film,motion,demo,gantt,drilldown,notes` 输出当前工序要读的文件与哈希；它是索引，不代替阅读。
- 先照参考实现做出一页完整可验的样页，确认上游链路，再扩展全套。

## 制作顺序
源材料与事实清单 → 页型、信息层级、可选观点句 → 构图预设与字号 → 保护区与生图任务 → 实际生图与审阅 → 经指定引擎制作 → 静态、动态、交互、数据与可编辑性复核 → 修复 → 交付。page-plan 用 `schemas/page-plan.schema.json`（`contract_revision` 见 schema），`tools/qc_plan.py` 预检；预检通过不等于视觉放行。

## 观众界面与 Office 范围
不出现播放、暂停、重播、进度滑杆、“开始播放下一页”等控件；后台暂停、离屏、编辑、减少动态与 QC seek 接口保留。PPTX 要求原生可编辑的文字、表格、形状与图表，并做 PowerPoint 编辑保存回读；不调用、打开或修复 Excel，也不通过“编辑数据”启动 Excel。

## 维护资料
回归测试、验证记录与历史样本只在维护仓库，不进发布包；交付时按 10 的门表逐门给证据。
