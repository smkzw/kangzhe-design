# 站点式 HTML 轨道

按真实信息结构分为首页、章节页、明细页，路由与面包屑可见。不引入新框架：沿用项目现有 HTML/CSS/JS 或 React 结构，取用本包 tokens、玻璃、电影、图表、下钻、甘特组件，避免双时钟、双导航。

## 步骤
1. **计划**：事实清单 → 页面结构（首页、章节、明细）→ page-plan（`track: site`，`body_profile: responsive`，`target_viewports` 取 `tokens.viewports.site`）→ 每个首屏舞台写 film-plan（06 FILM-PLAN），材料不够电影时写 `fold_stage` 与理由 → `tools/qc_plan.py` 预检。
2. **资产**：首页与章节首屏用生成主视觉或全站程序化光场（04 IMG-01），登记资产清单。
3. **页面**：所有页面共用固定玻璃页眉 `.kz-site-head`（13 WIDE-01），首页 Bento 首屏（13 FOLD-02），章节页章节头（FOLD-06），首屏以下密排网格（FOLD-05/06），宽幅下钻（07）。组件接入 `KZMotion.fitFold` 与 `mountPage`（首屏）、`mountSections`（段落）、`mountField`（光场）、`storyboard` + `Film`（电影，传入 `staticProgress`）、`KZDemo`（讲方法与数据的段落，循环模式，`.kz-demo-split` 分栏，15 DEMO-05）、`KZCharts`、`KZDrilldown`；接线方式见 `examples/reference/site/site.js`。
4. **验收**：10 的 G5-FOLD（首页每档视口在电影初始态与静态帧各跑一次 `inspectFold`）、G5-DENSE（每页每档视口跑 `inspectScroll`，13 FOLD-07）、G5-WIDTH（每页每档视口跑 `inspectWidth`，13 WIDE-01）、G5-ORPHAN、G7（入场、电影完整周期、减少动态、打印）、G8（下钻按键、滚轮、焦点）；交付说明附 G0–G9 门表。

## 结构
- 首页：13 FOLD-01/02 的 Bento 首屏（一屏放下，左导读、右电影与状态条）。
- 章节页与明细页：13 FOLD-06 的章节头加密排网格，不再做满屏首屏；章节的电影或演示舞台是网格中的一块。
- 首屏以下：13 FOLD-05/06 的密排网格（段落标题行 + 并排的卡、图表、表格、演示舞台），段落首次可见时入场。讲方法与数据的段落优先用演示舞台（15 DEMO-01）。
- 明细：07 的宽幅下钻（L0→L1→L2），或独立长文页并有返回来源。进入明细暂停父电影，返回恢复。
- 页间跳转用跨文档转场（06 MOTION-05），站点头部不动。

允许“单页章节锚 + 模态明细”变体：一个长页承载全部章节（锚点导航），每章首区块有章节电影，明细用下钻。任务书选用时须写明；此时每章主层至少独立完成一个真实信息任务，导航与滚动恢复由框架层单一实现，区块背景随段高（不固定 100vh 造成接缝）。

## 视觉
- 不使用 PPT 固定画布、页眉页脚或双菱形。卡片、KPI、侧注、下钻面板都没有全高或全宽的边缘色条（02 LG-02），交付前跑 `KZLayoutQC.inspectEdgeBars`。全宽场景、外围窄边距（`--kz-gutter`），阅读正文单独限行长（`--kz-measure`），不以 `max-width:1100px` 锁死全站；宽屏字号、页眉与 Logo 尺寸、超宽网格按 13 WIDE-01。
- 首屏用生成主视觉，或全站统一、实际运行的程序化光场（`.kz-optical-field` + `mountField` 视差），逐页确认存在。光场不是大面积橙色渐变，不干扰正文。
- 正文字号默认 `type_px.site_body`，下限 16px（03 TYPE-01 responsive 档）。

## 范围
面向桌面宽屏，验收视口为 `tokens.viewports.site`（1280×720 至 3440×1440 的六档浏览器可视区，见 13 FOLD-04），不做手机或窄屏适配，不加汉堡菜单或触控版。桌面窗口在此范围内改变尺寸时，电影几何、图表与下钻须正确重算。减少动态、键盘、焦点、浏览器缩放、打印继续保留。无 JS 时内容仍完整可读。

本轨不强制讲稿；G7-NOTES 在门表写“N/A：本轨无讲稿容器”。

参考实现：`examples/reference/site/`。

甘特：加载 `kz-icons.js`、`kz-clinical.js`、`kz-gantt.js`、`kz-gantt-studio.js`（runtime/API.md），按 T 打开全页编辑台（08 GANTT-01）。要“保存到本文件”，甘特数据须放在页面的 `window.KZ_DECK_DATA[gid]` 数据块里并在根元素写 `data-kz-gantt="<gid>"`；否则保存菜单只给导出、复制、导入与草稿（08 GANTT-05）。

临床数据图（round 9）：
- **加载**：在 `kz-charts.js`、`kz-gantt.js`、`kz-clinical.js`、`kz-drilldown.js` 之后加载 `kz-explore.js`。KZCharts 遇到 `exposure-plan` 与历时变化各 kind 会转交给它（05 CHART-06，08 GANTT-08）。
- **共享计划**：甘特与累计暴露放在同一页时，用同一个 `program.id`，数据放在 `window.KZ_DECK_DATA`。
- **静态临床模板**：有效性汇总、SoA、试验流程、竞争格局三页（pipeline / efficacy / safety）、暴露汇总等在 HTML 里同样用模板库：`kz_layout.py render <模板> data.json --track html --out frag/` 写出卡片内标记与 frag/charts.json（并进 `KZ_DECK_DATA`，键名不改），放进整行卡（span 12），一行一个模板，不并排两张（并排时示意图按卡宽整体缩小，字小到读不出，`inspectTextFloor` 会报）。不要自己拼 ECharts 条形图代替竞争格局模板（药名要在轴上或行首，不只放在图例里）；演示舞台（kz-demo-clinical）只在需要逐 scene 讲解时用，放置宽度见 15 DEMO-03。用演示舞台时按 15 DEMO-07 的加载顺序引入整条链（kz-scenes → kz-icons → kz-demo → kz-demo-patterns → kz-demo-fine → kz-demo-clinical），缺一个就挂不上。模板片段的长度单位与字号在本轨由 kz-layouts.css 按卡宽给定（`--kz-u` = 卡宽 / 1168，字号同一比率），不要自己按 innerHeight/720 写比率或另加下限，也不加载 html-ppt-bridge。每个模板用各自的 `--out` 目录渲染（文件都叫 slide_NN.html，同目录会互相覆盖），再把各目录的 charts.json 并进同一个 `KZ_DECK_DATA`。
- **参考页**：`examples/reference/site/clinical.html` 与 `examples/reference/stream/clinical.html`，由 `examples/reference/site/build_clinical.py` 生成。
