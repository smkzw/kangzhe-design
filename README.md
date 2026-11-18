# Kangzhe Design 8.0

康哲药业医学部的统一设计技能（Agent Skill），用于正式汇报与医学网页。一个技能覆盖四种交付形式，共用一套 tokens、Liquid Glass 材质、字号与强调规则、动效词汇和验收门：

| 交付形式 | 制作引擎 | 本包提供 |
|---|---|---|
| 可编辑 PPTX | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)（必须） | 品牌与页型、原生玻璃卡、正文模板、原生图表与表格、入场动效、导出后的品牌绑定与检查 |
| HTML-PPT | [lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) 脚手架（必须） | 玻璃组件、电影与按 scene 步进的演示、ECharts 图表、甘特编辑台、下钻、版面检查 |
| 站点式 HTML | 项目现有结构 | 同上的 runtime，宽屏 Bento 首屏与密排网格 |
| 流式 HTML | 项目现有结构 | 同上的 runtime，章节目录与正文阅读栏 |

PPTX 与 HTML-PPT 各有两条路线：**常规**（内部汇报）与**旗舰**（对外与顶层汇报：暖白画布、立体编号、three.js 电影化舞台，PPTX 用「层叠纸板」语言）。开工时先选路线。

## 8.0 的内容

- **开工两站**：开工卡 `tools/intake.py` 一次问完交付形式、路线、生图能力、背景风格、受众、动效、临床场景与页数；分页故事板 `tools/storyboard.py` 在生成前逐页确认载体与预检结果（`design_specs/17-intake-storyboard.md`）。
- **正文模板库**：50 套模板（`tools/kz_layout.py list`），PPTX 与 HTML 共用一份数据，按内容分 sparse / standard / dense 三档密度；入排标准原文密排、SoA、流程、森林图、KM、CONSORT、KPI 看板、风险矩阵等。原文条款不压缩，放不下时报错并给出拆页办法，不缩字。
- **临床汇报场景族**：安全性、临床开发计划、暴露例数、试验流程、竞争格局、有效性、访视流程（SoA）、历时变化。每族一份数据合同，同时产出静态模板、常规演示动画、旗舰舞台与旗舰 PPTX 模板；数据不自洽时（率差与 n/N 不符、日期重叠、参考线键名写错等）直接报错。
- **甘特编辑台**：HTML 四轨按 T 打开全页编辑台，精度日 / 月 / 季度，两级泳道、里程碑、原计划与状态；累计暴露挂在开发计划上与甘特联动。
- **常规路线视觉**：四种背景风格（缺省 A2 暖纸底 + 玻璃丝带）与缺省背景套；加粗、深红、下划线、高亮四种强调四轨同一外观；卡片边缘色条一律禁止并有检查工具。
- **演示动画**：28 种演示形式（`examples/motion/index.html`），HTML-PPT 中随翻页键逐 scene 推进；舞台放不下时在控制台报错并标出。
- **检查工具**：计划预检 `tools/qc_plan.py`、项目检查 `tools/check_kz_project.py`、色条检查 `tools/check_edge_bars.py`、讲稿检查 `tools/check_notes.py`；浏览器端 `KZLayoutQC` 检查越界、孤字行、文字压叠与渲染字号。

完整变化见 [CHANGELOG.md](CHANGELOG.md)。

## 安装

从 [Releases](https://github.com/smkzw/kangzhe-design/releases) 下载 `kangzhe-design-8.0.0.zip`，解压后把 `kangzhe-design/` 目录放进宿主的技能目录（Claude Code 为 `~/.claude/skills/kangzhe-design/`），再安装 Python 依赖与两个制作引擎。步骤与自检见 [INSTALL.md](INSTALL.md)。

## 目录

| 目录 | 内容 |
|---|---|
| `SKILL.md` | 技能入口：四轨与引擎、硬规则、读取顺序、制作顺序 |
| `design_specs/` | 规则正文：00 权威与优先级、01 核心、02 玻璃材质、03 字号与文案、04 图像、05 图表、06 动效与电影、07 下钻、08 甘特、09 讲稿、10 验收门、11 hero 页、13 版面与密度、14 旗舰、15 演示动画、16 METRIC 页头、17 开工卡与故事板，以及四个轨道配方 `tracks-*.md` |
| `tokens/` | 唯一数值源 `tokens.json`；`tools/build_tokens.py` 生成 `runtime/kz-tokens.*` |
| `runtime/` | 玻璃 CSS、动效、图表、甘特与编辑台、下钻、临床合同、演示与旗舰舞台、版面检查；接口见 `runtime/API.md` |
| `adapters/` | ppt-master 与 html-ppt-skill 的插入点与核对基线、HTML-PPT 生命周期桥 |
| `tools/` | 开工卡、故事板、模板渲染、计划预检、hero 与双菱形片段、PPTX 绑定、项目检查、背景合成 |
| `schemas/` | page-plan、资产清单、电影、甘特、开发计划的数据合同 |
| `assets/` | 官方 Logo、双菱形原生形状、缺省背景套、图标、METRIC 标识、ECharts / GSAP / three.js |
| `examples/` | 四轨参考实现、模板样张、演示动画图库、组件实验室 |

## 快速开始

```bash
KZ=~/.claude/skills/kangzhe-design
python3 $KZ/tools/intake.py html --out intake.html --topic 主题          # 开工卡；无浏览器时用 intake.py ask
python3 $KZ/tools/context_pack.py --track pptx --stage bootstrap          # 当前工序要读的文件
python3 $KZ/tools/kz_layout.py list                                       # 正文模板目录
python3 $KZ/tools/storyboard.py html page-plan.json --out storyboard.html # 生成前逐页确认
python3 $KZ/tools/qc_plan.py page-plan.json                               # 计划预检
python3 $KZ/tools/check_kz_project.py <ppt-master 项目> --plan page-plan.json   # PPTX 导出前
```

离线打开 `examples/templates/deck/index.html` 看模板样张，`examples/reference/htmlppt/index.html` 看 HTML-PPT（方向键逐 scene 推进），`examples/reference/site/index.html` 看站点首页，`examples/motion/index.html` 看演示动画，`examples/component-lab.html` 看组件。

## 使用范围

- 官方康哲标识（`assets/logo_bot.*`）与双菱形品牌形状仅供有权使用康哲品牌的用户使用，不得改色、改字或重绘。
- 示例中的研究、药物、竞品与数字全部是合成数据，不对应真实研究。
- 第三方组件的许可证随包附带：`assets/vendor/`（ECharts、GSAP、three.js 等）、`assets/icons/NOTICE.md`（Tabler Icons）、`examples/reference/*/vendor/html-ppt/LICENSE`。
