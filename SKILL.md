---
name: kangzhe-design
description: 康哲药业医学部正式汇报与医学网页的统一 Liquid Glass 设计系统。用于康哲 design、康哲 design 3D、康哲风格、可编辑 PPTX、HTML PPT、站点式 HTML、流式 HTML；PPTX 与 HTML-PPT 分常规与旗舰两条路线（旗舰用于对外与顶层汇报）。PPTX 配合 ppt-master；HTML-PPT 配合 html-ppt-skill。只安装本技能，不再安装旧扁平版或 3D 版。
---
# Kangzhe Design 7.1

品牌、内容表达、视觉、动效与验收层，不是另一套 PPT 引擎。四轨共用一套 tokens 与材质，没有 flat 开关或第二套配色。PPTX 与 HTML-PPT 各有两条路线：常规（日常与内部汇报）和旗舰（对外与顶层汇报，`design_specs/14-flagship.md`）。

## ⛔ 选路阻断（PPTX 与 HTML-PPT，14 FLAG-01）
用户要求做 PPTX 或 HTML-PPT 时，必须先停下，请用户在“常规”和“旗舰”之间选一条路线；得到明确答复之前，不做计划、不生图、不搭脚手架、不导出，即使材料已经齐全。

提问前先判定：根据用户上传的材料和提供的信息（听众、场合、材料性质、用户措辞、放映环境，判据表见 14 FLAG-01）给出推荐路线和两三条具体理由，再请用户确认或改选，例如“推荐旗舰：这是给集团管理层的季度汇报，结论集中在 3 个数字上，并且会用 Edge 放映。请选择：常规 / 旗舰”。宿主有提问工具时用提问工具，没有时输出这个问题，停在这一步等待答复。用户在本次请求中已经明确指定路线时，复述一句即可继续；修改已有 deck 时沿用它原来的路线。站点式与流式 HTML 不触发本阻断。

- 常规：01–13 的现行规范，正文页固定 chrome，同族玻璃卡承载内容。
- 旗舰：浅色画布上的全屏光场、液态玻璃透镜与身份胶囊，光先转场、内容后入场，内容页光退到页边；不用固定页眉页脚，锚定“产品中心医学部”。HTML-PPT 需用 Edge 或 Chrome 放映；PPTX 用静态光效图，玻璃是烘焙透镜图加原生玻璃壳。

## 四轨与引擎
| 轨道 | 制作引擎 | 轨道配方 | 参考实现 |
|---|---|---|---|
| 可编辑 PPTX | ppt-master（必须） | `design_specs/tracks-pptx.md` · `adapters/ppt-master.md` | `examples/reference/pptx-default/` |
| HTML-PPT | html-ppt-skill 脚手架（必须） | `design_specs/tracks-htmlppt.md` · `adapters/html-ppt.md` | `examples/reference/htmlppt/` |
| 旗舰路线（PPTX / HTML-PPT） | 同上两行的引擎 | `design_specs/14-flagship.md`（叠加在所选轨道上） | `examples/reference/htmlppt-flagship/` · `examples/reference/pptx-flagship/` |
| 站点式 HTML | 项目现有结构 + 本包 runtime | `design_specs/tracks-site.md` | `examples/reference/site/` |
| 流式 HTML | 同上 | `design_specs/tracks-stream.md` | `examples/reference/stream/` |

本包只注入品牌、页面计划、图像保护、组件与 QC；不改上游源码，不另写同类引擎，不叠第二套缩放或翻页。上游真实能力达不到的效果，写明阻塞，不伪造。

## 硬规则（编号指向唯一所有者）
1. 数值只读 `tokens/tokens.json`；改值后运行 `tools/build_tokens.py`（00）。
2. 官方 Logo 只用 `assets/logo_bot.svg` 原件，校验哈希（01 CORE-02）。
3. 双菱形只用于常规路线的 PPTX 与 HTML-PPT 正文页，取自 `assets/header-mark` 原生资产；旗舰、站点与流式不用（02 LG-03、14 FLAG-06）。
4. 卡片是同族玻璃：三停渐变面、rim 折光边、短高光；HTML 轨用三层暖色阴影并随指针变化，PPTX 用单个原生外阴影（02 LG-01、ELEV-01、LG-PPTX）；禁止任何通长彩色边条（LG-02）。旗舰路线的正文放在纸卡上，液态玻璃透镜只用于框架元素（14 FLAG-05/08）。
5. 字号守角色合同与下限，辅助文字（注释、图注、表体、轴与图例）可用 12pt 的 secondary 角色；同页同角色同字号同行距；放不下先重排或拆页，不缩字、不裁字；无孤字行（03 TYPE-01/03/04）。
6. 标题写内容名称，不带冒号或破折号；文字卡有独立卡标题、语义分条与有依据的重点（03 COPY-01/06）。
7. 只为外部论文与权威指南标注来源；内部来源留在私有台账；不把边界声明当内容（03 COPY-05/08）。
8. PPTX/HTML-PPT 每页映射真实生成资产；正文背景安静、与 hero 主视觉分开策划（04 IMG-01/05）。旗舰路线的背景由品牌光场生成并登记参数与哈希（14 FLAG-02/10）。
9. 数据真实可编辑：HTML 数值图用 ECharts，PPTX 用原生图表；null 不当 0；类别色序固定且独立于部门色（05）。
10. 站点与流式的动画自动发生；HTML-PPT 的电影与演示按 scene 随演讲者的翻页键与滑动推进，最后一个 scene 后才翻页；没有观众播放控件；时钟按真实时间；动作取自 token 化的词汇与编排；电影保持一个载体（06 MOTION-09、FILM-05）。
11. 讲方法、规则、计算、数据、计划的页面用演示舞台把内容做给观众看，多 scene、高密度、大幅度，数字由数据算出；只有卡片入场与连线不算演示（15 DEMO-01/03/04）。
12. 站点与流式的首屏在每个验收视口内一屏放下，采用 Bento 构图并通过密度指标；验收视口是浏览器可视区（13）。
13. 下钻是宽幅多层栈，按键与滚轮不泄漏到宿主（07）；甘特用单一季度模型 [start,end)（08）。
14. 交付按 10 的门表逐门给证据；组件测试不叫端到端，LibreOffice 不叫 PowerPoint 验收；不调用 Excel。

## 读取顺序
- 必读：`design_specs/00-authority.md`、`01-core.md`、`02-liquid-glass.md`、`03-typography-language.md`、`04-image-pipeline.md`、所选轨道文件；旗舰路线另读 `14-flagship.md`，它替代的常规条文以其 FLAG-02 表为准。
- PPTX / HTML-PPT 含封面、目录、章节、尾页时读 `11-hero-layouts.md`；正文页构图读 `13-layout-density.md` BODY-01。
- 所有 HTML 轨读 `06-motion-film.md` 与 `15-demo-motion.md`；站点与流式读 `13-layout-density.md`；PPTX 需要动效时读 06 MOTION-07 与 15 DEMO-06。
- 按能力读：图表 05、下钻 07、甘特 08、讲稿 09；终审读 10。
- 本包的工具需要 Python 3.10+ 与 `requirements.txt`（jsonschema、Pillow、numpy）。把本文件所在目录记为 `KZ_DIR`，命令写成 `python3 "$KZ_DIR/tools/…"`，不依赖当前目录。
- `python3 "$KZ_DIR/tools/context_pack.py" --track <pptx|htmlppt|site|stream> [--route flagship] --stage <bootstrap|plan|assets|author|verify> --features charts,film,motion,demo,gantt,drilldown,notes` 输出当前工序要读的文件与哈希；它是索引，不代替阅读。
- 先照参考实现做出一页完整可验的样页，确认上游链路，再扩展全套。

## 制作顺序
源材料与事实清单 → 页型、信息层级、可选观点句 → 构图预设与字号 → 保护区与生图任务 → 实际生图与审阅 → 经指定引擎制作 → 静态、动态、交互、数据与可编辑性复核 → 修复 → 交付。page-plan 用 `schemas/page-plan.schema.json`（`contract_revision` 见 schema），`tools/qc_plan.py` 预检；预检通过不等于视觉放行。

## 观众界面与 Office 范围
不出现播放、暂停、重播、进度滑杆、“开始播放下一页”等控件；后台暂停、离屏、编辑、减少动态与 QC seek 接口保留。PPTX 要求原生可编辑的文字、表格、形状与图表，并做 PowerPoint 编辑保存回读；不调用、打开或修复 Excel，也不通过“编辑数据”启动 Excel。

## 维护资料
`review/`、`agent/`、`docs/history/`、`tests/`、`examples/validation/` 是维护与历史资料，不进安装包（`tools/build_dist.py`）。当前验证状态见 `STATUS.md`。
