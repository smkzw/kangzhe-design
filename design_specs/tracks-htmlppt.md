# HTML-PPT 轨道（经 html-ppt-skill）

必须从安装的 lewislulu/html-ppt-skill 脚手架起步（`scripts/new-deck.sh`）。先按宿主的技能目录找到 html-ppt-skill 的安装位置（含 `SKILL.md`、`scripts/new-deck.sh`、`assets/runtime.js` 的目录），再运行其脚本；不要复制本包参考实现的 `index.html` 当起点，它只演示品牌层怎样接到脚手架上。上游拥有唯一的 deck、活动页、键盘、hash、S 演讲者窗口、O 总览和 notes；本包提供全视口品牌主题与组件，不创建第二个放映器，不改上游源码。接口细节见 `adapters/html-ppt.md`。

## 步骤
1. **计划**：同 PPTX 轨的事实清单、页型、构图预设（13 BODY-01）、hero 版式（11）、page-plan 与 `qc_plan.py`；`target_viewports` 用 `tokens.viewports.htmlppt`。
2. **脚手架**：`new-deck.sh <name> <dir>` 生成后保留原始输出（参考实现保存为 `scaffold.html`）；把实际使用的上游 `base.css`、`runtime.js` 复制进交付目录并记录 SHA；去掉主题链接、`data-themes`、远程字体和 `animations.css`。
3. **品牌层**：`body.kz[data-fit="fluid"]`；加载顺序 base.css → kz-tokens.css → kz-glass.css → 项目主题；脚本顺序：上游 runtime →（用到图表或甘特时）随包 `assets/vendor/echarts.min.js` → kz-tokens.js → kz-motion.js / kz-charts.js / kz-gantt.js / kz-drilldown.js /（有演示页时）kz-scenes.js → kz-demo.js → html-ppt-bridge.js → 项目装配 → kz-audience.js（清理观众页上残留的播放控件，见 runtime/API.md）。`kz-layout-qc.js` 只在验收时注入，不随观众页加载。
4. **页面**：hero 页用 `tools/hero_layout.html_fluid_fragment`；正文页每页内置 chrome（双菱形 `brand_fragments.facets` + 横线 + Logo + 页脚页码），正文放进 `.kz-body[data-preset]`；背景用安静的正文生图（04 IMG-05）。
5. **装配**：`KZHTMLPPT.bind(deck, factory)`，每页 `mountPage`、按需 Film / 演示舞台（15）/ 图表 / 甘特，非活动页暂停；电影与演示按 scene 步进（06 MOTION-09）；`?preview`、打印、减少动态走静态终态（06 MOTION-08）。
6. **讲稿**：上游 `aside.notes`（09），替换模板示例稿；scene 页按 scene 分段（09 NOTES-02）。
7. **验收**：10 G5（每档视口无越界、无孤字、卡片分布、宽屏贴边）、G7（入场分层、翻页不让玻璃失效、电影、scene 步进、演示、减少动态）、G9（深链接、方向键、O、S、`?preview`、打印、离线）；正式静态截帧按 adapter 的“正式静态截帧”一节：默认用上游 `render.sh` 处理捕获副本，宿主禁用 headless 时走同节的替代截帧并在门表注明方法。

## 必验
- 四类 hero 页用 11 的固定形态与真实生成背景；正文页固定 chrome，背景可复用。
- 宽屏不是“居中的 16:9 两边涂背景”：内容网格与背景铺满（G5-WIDE）。
- 输入框、拖拽与对话框里的按键不触发翻页。
- 讲方法、规则、计算、数据、计划的页面配演示舞台（15 DEMO-01），不只用卡片加连线。
- 组件实验室不能代替上游端到端。

参考实现：`examples/reference/htmlppt/`（`build.py` 从脚手架派生 `index.html`）。

旗舰路线（14）用同一脚手架与 adapter，另加 `runtime/kz-flagship.css/js`；步骤 4 的正文页 chrome 与背景生图由 14 FLAG-06/07/08 替代。参考实现：`examples/reference/htmlppt-flagship/`。
