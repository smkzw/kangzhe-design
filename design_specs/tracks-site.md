# 站点式 HTML 轨道

按真实信息结构分为首页、章节页、明细页，路由与面包屑可见。不引入新框架：沿用项目现有 HTML/CSS/JS 或 React 结构，取用本包 tokens、玻璃、电影、图表、下钻、甘特组件，避免双时钟、双导航。

## 步骤
1. **计划**：事实清单 → 页面结构（首页、章节、明细）→ page-plan（`track: site`，`body_profile: responsive`，`target_viewports` 取 `tokens.viewports.site`）→ 每个首屏舞台写 film-plan（06 FILM-PLAN），材料不够电影时写 `fold_stage` 与理由 → `tools/qc_plan.py` 预检。
2. **资产**：首页与章节首屏用生成主视觉或全站程序化光场（04 IMG-01），登记资产清单。
3. **页面**：Bento 首屏（13 FOLD-02）、下方段落（FOLD-05）、宽幅下钻（07）。组件接入 `KZMotion.fitFold` 与 `mountPage`（首屏）、`mountSections`（段落）、`mountField`（光场）、`storyboard` + `Film`（电影，传入 `staticProgress`）、`KZCharts`、`KZDrilldown`；接线方式见 `examples/reference/site/site.js`。
4. **验收**：10 的 G5-FOLD（每档视口在电影初始态与静态帧各跑一次 `inspectFold`）、G5-ORPHAN、G7（入场、电影完整周期、减少动态、打印）、G8（下钻按键、滚轮、焦点）；交付说明附 G0–G9 门表。

## 结构
- 首页与每个独立章节页：13 FOLD-01/02 的 Bento 首屏（一屏放下，左导读、右电影与状态条）。
- 首屏以下：13 FOLD-05 的段落（标题 + 说明 + 卡组/图表/表格），段落首次可见时入场。
- 明细：07 的宽幅下钻（L0→L1→L2），或独立长文页并有返回来源。进入明细暂停父电影，返回恢复。
- 页间跳转用跨文档转场（06 MOTION-05），站点头部不动。

允许“单页章节锚 + 模态明细”变体：一个长页承载全部章节（锚点导航），每章首区块有章节电影，明细用下钻。任务书选用时须写明；此时每章主层至少独立完成一个真实信息任务，导航与滚动恢复由框架层单一实现，区块背景随段高（不固定 100vh 造成接缝）。

## 视觉
- 不使用 PPT 固定画布、页眉页脚或双菱形。全宽场景、外围窄边距（`--kz-gutter`），阅读正文单独限行长（`--kz-measure`），不以 `max-width:1100px` 锁死全站。
- 首屏用生成主视觉，或全站统一、实际运行的程序化光场（`.kz-optical-field` + `mountField` 视差），逐页确认存在。光场不是大面积橙色渐变，不干扰正文。
- 正文字号默认 `type_px.site_body`，下限 16px（03 TYPE-01 responsive 档）。

## 范围
面向桌面宽屏，验收视口为 `tokens.viewports.site`（1280×720 至 2560×1080 的五档浏览器可视区，见 13 FOLD-04），不做手机或窄屏适配，不加汉堡菜单或触控版。桌面窗口在此范围内改变尺寸时，电影几何、图表与下钻须正确重算。减少动态、键盘、焦点、浏览器缩放、打印继续保留。无 JS 时内容仍完整可读。

本轨不强制讲稿；G7-NOTES 在门表写“N/A：本轨无讲稿容器”。

参考实现：`examples/reference/site/`。
