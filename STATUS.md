# 当前验证状态 · 2026-10-24（7.1.1 / KZ7-1024-B07）

整体 **PARTIAL**：规范、runtime 与四轨正例已重构并在本机实测；7.1 新增 PPTX 与 HTML-PPT 的旗舰路线（14）及开工前的选路阻断，7.1.1 把旗舰中承载文字的玻璃改为半透磨砂；PPTX 已按 ppt-master Default 全流程做出正例，并在 macOS PowerPoint 中完成编辑、保存、重开与回读。Windows Office、Safari、上游 headless 截帧尚未覆盖。状态词见 `design_specs/10-quality-gates.md` QA-STATUS。

| 证据层 | 状态 | 已完成（本机实测） | 未完成 / 边界 |
|---|---|---|---|
| 单元测试 | PASS | 仓库 `tests/test_*.py` 13 个文件 129 项全部通过（维护者回归，不随包发布） | Python 3.10+ |
| 组件（ego lite / Chromium 154） | WARN | 7.0.0 发布前组件实验室真实指针/键盘/滚动检查 20/20（ego lite 0.6.0.12）；升级到 0.6.0.20 后同一机器 15/20，重启浏览器后仍是 15/20。失败的 5 项（悬停弹簧抬升与回位、下钻收回/折回/焦点归还）都靠 requestAnimationFrame 推进，而这一版浏览器在页面跑过任何 rAF 动画后把帧率降到 1 fps（见 HTML-PPT 行），未改动的 7.0.0 同样失败。甘特按需展开、选中、拖动、撤销以真实输入复测通过。覆盖：入场分层、弹簧倾斜、电影交叉淡入与 seek、下钻展开/折回/中途关闭/按键隔离/焦点、段落入场、光场视差、图表揭示、减少动态 | 5 项要在正常帧率的 Chromium 上复测；Playwright 版检查已按 7.0 更新但未在本机运行 |
| 站点 / 流式正例 | PASS | 3 页 × 6 视口（`tokens.viewports` 五档 + 1920×900），电影初始态与静态帧各测 `inspectFold`，全部 PASS；无孤字 | 1920×940 初始态覆盖率贴近阈值 0.45；Safari、跨文档 view transition（需 HTTP 同源）未测 |
| HTML-PPT 正例 | PASS | html-ppt-skill 脚手架起步；与 PPTX Default 同一素材，10 页 × 5 视口无越界/卡片告警，10 页 × 4 视口无孤字与词内换行，正文页纵向跨度 ≥0.70；入场顺序与 PPTX 一致（HTML 卡片错峰 70ms 带位移与卡内级联，PPTX 纯淡入错峰 180ms）；7.0.2 甘特编辑器按需展开后 10 页 × 4 视口复测无孤字与断词；深链接、方向键、O、`?preview`、减少动态 | 在 ego lite 0.6.0.20 中翻页首帧约 0.5 s、卡片约 1.5 s 才出现。已用 5 行最小页面复现：任何页面只要跑过一段 requestAnimationFrame 动画（JS 位移、canvas、ECharts 入场均可），之后 rAF 一直停在 1 fps；从未动画的静态页是 120 fps，持续的 CSS 动画约 30 fps；重启浏览器无效。deck 的 ECharts 入场动画因此把整份 deck 拖到 1 fps。属浏览器问题，正常帧率的 Chromium 上的观感尚未复核；`render.sh`（headless）未跑；S 演讲者窗口、打印未测；总览缩略图中的图表为空（上游限制） |
| HTML-PPT 旗舰（14） | PASS | `examples/reference/htmlppt-flagship/`：html-ppt-skill 脚手架加 `runtime/kz-flagship.*`；承载文字的透镜为半透磨砂（边缘折射、阅读区磨砂提亮）；7.1.1 复测 9 页 × 4 视口无孤字、断词、越界，最小字号 16，身份胶囊不压内容；`tests/ego/flagship_checks.mjs` 19/19 通过，覆盖 WebGL 光场、Chromium 透镜、胶囊锚点、入场晚于光转场、透镜预算、连续快速翻页不重复整页光波、深链不播放转场、`?kzf-p` 从上一页起、减少动态下翻页重画且不叠页、打印（含减少动态）每页可见并保留胶囊、`?kzf-t` 定格可复现、内容页纸卡背后的光场近于画布色、减少动态、`?preview` 降级 | 正常帧率的 Chrome/Edge 中放映观感未复核（本机 ego lite 有 rAF 1 fps 问题）；非 Chromium 降级未实测；总览缩略图中的图表为空（上游限制） |
| PPTX 旗舰（14） | PASS | `examples/reference/pptx-flagship/`：`tools/flagship_plate.py` 静态光效图，每块玻璃下垫烘焙透镜图（`lens()`，阅读区磨砂、边缘折射）再加原生玻璃壳，身份胶囊与原生柱图，经 ppt-master 导出；`qc_plan`（route flagship）0 错误且光效图哈希一致，检查器 0 错误，交付检查 0/0，OOXML 回读时序与图表正确；PowerPoint 打开、另存 PDF、编辑保存重开回读一致 | 放映观感与 Windows 未测；探针不含讲稿 |
| PPTX（ppt-master Default 全流程） | PASS | `examples/reference/pptx-default/`：两次确认页、Design Spec/lock、手写 SVG、最终检查 0 错误、verify-charts、备注、动效、原生图表导出、双菱形与 hero 绑定、交付检查 0 错误、OOXML 回读 | 见下一行的 PowerPoint 实机 |
| PowerPoint 实机（macOS 16.114） | PASS | 7.0.2 的两份样例经 AppleScript 在 PowerPoint 中打开、编辑（解组后改标题文字、新增文本框、讲稿追加）、另存、关闭、重开，三处修改都读回；PowerPoint 另存的 PDF 逐页查看版面正常。保存后 OOXML 与导出时一致：动效时序（0/180/360/740 等）、原生柱图的系列/数值/颜色、主题字体、hero 框、阴影与渐变；探针的 Morph 转场与 `!!kz-carrier` 名称保存后仍在 | 放映观感（实际播放入场与 Morph）未看；Windows PowerPoint 未测 |
| 生图 | WARN | 正例复用历史真实生成图并登记来源哈希 | hero 长边 1672 < 2560；正文安静背景下部可见玻璃弧线，需真实重生成；缺超宽正文背景；章节页在 2560×1080 下主视觉压到标题，需要宽屏专用图（7.0.2 尝试用 gpt-image-2 生成 21:9 章节图，本机图像接口凭据被拒 401，BLOCKED） |

历史与逐轮细节在仓库 `review/CURRENT_STATUS.md` 与 `CHANGELOG.md`。
