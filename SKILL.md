---
name: kangzhe-design
description: 康哲药业医学部正式汇报与医学网页的统一 Liquid Glass 设计系统。用于康哲 design、康哲 design 3D、康哲风格、可编辑 PPTX、HTML PPT、站点式 HTML、流式 HTML。PPTX 配合 ppt-master；HTML-PPT 配合 html-ppt-skill。只安装本技能，不再安装旧扁平版或 3D 版。
---
# Kangzhe Design 6.0

## 先确定责任边界
这是品牌、内容表达、视觉与验收层，不是另一套 PPT 制作引擎。四轨只有一个设计语言，没有 flat 开关、legacy 卡片或第二套配色。数值常量只读 `tokens/tokens.json`；规则归属见 `design_specs/00-authority.md`。禁止加载旧包补缺。

## 最短读取路径
1. 必读 `design_specs/00-authority.md`、`01-core.md`、`03-typography-language.md`、`04-image-pipeline.md`；按需读取其中指向的唯一规则所有者，不要求把全包塞进上下文。
2. 四选一：PPTX → `tracks-pptx.md`；HTML-PPT → `tracks-htmlppt.md`；站点 → `tracks-site.md`；流式 → `tracks-stream.md`。交互是能力，不是第五轨。
PPTX/HTML-PPT 含封面、目录、章节或尾页时，必须读取 `11-hero-layouts.md`，选固定版式 ID；这些页不能套正文页标题字号。
3. 所有轨读取 `02-liquid-glass.md`。有数据图读取 `05-charts.md`；所有HTML轨必须读取 `06-motion-film.md`（包括普通卡片微交互，不仅电影）；有下钻读取 `07-drilldown.md`；有甘特读取 `08-gantt.md`；有讲稿读取 `09-speaker-notes.md`。
4. 制作前锁定 `page-plan.json`（当前 `contract_revision=A04`，卡片布局模式和HTML逐对象动态清单必填），再生图。终审读 `10-quality-gates.md`。可用 `tools/context_pack.py --track <track>` 生成当前轨最小索引；它不会代替读取所选规则。

## 不可绕过的制作顺序
源材料与事实清单 → 页型/信息层级/可选观点句 → 字号和版式 → 保护区与生图任务 → **实际生图**与资产审阅 → 经指定引擎制作 → 静态、动态、交互、数据与可编辑性复核 → 修复 → 交付。

- PPTX/HTML-PPT 每页都要有已批准生成资产的映射；正文页可以复用经批准的低干扰背景，不要求逐页重新调用生图。四类非正文页的主视觉不得以普通渐变占位交付。
- 站点及流式每个页面/章节首屏都要有连续自动叙事；只有全站统一、实际运行的程序化光学场景可免生图。普通 CSS 背景渐变不是免责证据。
- 标题写内容名称，不写结论，不带冒号或破折号。观点句可为空；存在时居中、字号更大、解释意义而非抄数字。
- 同页同角色正文同字号、同行距、同内边距；不能逐卡缩小。放不下先重排/拆页，不得裁字。
- 卡片统一玻璃材质。任何全宽或全高的彩色边缘装饰条均禁止，包括旧组件、伪元素、inset shadow 和渐变伪装。
- 数据与文字保持真实、可编辑；生成图不承载唯一医学信息。HTML 数值图用 ECharts；PPTX 使用原生数据图或明确声明的原生形状等价物，不把 ECharts 截图冒充原生图。
- 受众页仅对外部科学论文、权威指南/共识/指导原则作参考文献式标注。内部来源保留在私有工作记录，不写上页面。

## 引擎协作
PPTX 必须进入安装的 `ppt-master` 路由。HTML-PPT 必须从 `html-ppt-skill` 模板脚手架进入，保留它的唯一导航/演讲者运行时，并通过其正式fluid扩展点实现宽屏主题。康哲只注入品牌、页面计划、图像保护、图表及交互组件和 QC，不另写同类引擎，不擅改上游源码。参考 `adapters/README.md`。

## 能力缺失与交付措辞
工具不可用、源材料不足、上游不支持的效果：写明具体阻塞、影响页、已完成部分和所需能力，不伪造调用回执或把占位标为通过。静态近似不叫动态折射；组件测试不叫引擎端到端测试；LibreOffice 渲染不叫 Windows PowerPoint 验收。

本包重构与后续验证任务在 `agent/START_HERE.md`；本包已经做过什么，只以 `review/CURRENT_STATUS.md` 的实际记录为准。

## 观众播放界面（A03用户修订）
所有轨道的动画自然自动发生。不得呈现播放/暂停/重播/进度滑杆/“开始播放下一页”等播放器UI，包括浮动工具条和hover后出现的控件。保留正常翻页、业务导航、详情、Gantt编辑；后台RM/离屏/编辑暂停与QC seek API继续保留。
