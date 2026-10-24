# 当前验证状态 · 2026-10-24（7.0.1 / KZ7-1024-B04）

整体 **PARTIAL**：规范、runtime 与四轨正例已重构并在本机实测；PPTX 已按 ppt-master Default 全流程做出正例，PowerPoint 能直接打开；编辑保存回读尚未做。Windows Office、Safari、上游 headless 截帧尚未覆盖。状态词见 `design_specs/10-quality-gates.md` QA-STATUS。

| 证据层 | 状态 | 已完成（本机实测） | 未完成 / 边界 |
|---|---|---|---|
| 单元测试 | PASS | 仓库 `tests/test_*.py` 12 个文件 108 项全部通过（维护者回归，不随包发布） | Python 3.10+ |
| 组件（ego lite / Chromium 154） | PASS | 7.0.0 发布前组件实验室真实指针/键盘/滚动检查 20/20；7.0.1 复测时同一机器 15/20，失败的悬停弹簧与下钻收回 5 项在未改动的 7.0.0 上同样失败，归因于当时浏览器帧调度变慢（见 HTML-PPT 行），7.0.1 未改这两处代码；甘特选中、拖动、撤销另以真实输入复测通过。覆盖：入场分层、弹簧倾斜、电影交叉淡入与 seek、下钻展开/折回/中途关闭/按键隔离/焦点、段落入场、光场视差、图表揭示、减少动态 | Playwright 版检查已按 7.0 更新但未在本机运行 |
| 站点 / 流式正例 | PASS | 3 页 × 6 视口（`tokens.viewports` 五档 + 1920×900），电影初始态与静态帧各测 `inspectFold`，全部 PASS；无孤字 | 1920×940 初始态覆盖率贴近阈值 0.45；Safari、跨文档 view transition（需 HTTP 同源）未测 |
| HTML-PPT 正例 | PASS | html-ppt-skill 脚手架起步；与 PPTX Default 同一素材，10 页 × 5 视口无越界/卡片告警，10 页 × 4 视口无孤字与词内换行，正文页纵向跨度 ≥0.70；入场时序与 PPTX 一致；深链接、方向键、O、`?preview`、减少动态 | 本机远程会话中，从封面类页翻到正文页时首帧约 0.5 s、卡片约 1.5 s 才出现：主线程空闲、与像素量无关、未改动的上游脚手架也有空闲帧延迟，判断为浏览器/会话层现象，未在本地直连显示器复核；`render.sh`（headless）未跑；S 演讲者窗口、打印未测；总览缩略图中的图表为空（上游限制） |
| PPTX（ppt-master Default 全流程） | PASS | `examples/reference/pptx-default/`：两次确认页、Design Spec/lock、手写 SVG、最终检查 0 错误、verify-charts、备注、动效、原生图表导出、双菱形与 hero 绑定、交付检查 0 错误、OOXML 回读 | 见下一行的 PowerPoint 实机 |
| PowerPoint 实机（macOS 16.114） | PENDING | 7.0.0 的交付文件打开无修复提示；6 页缩略图、讲者备注、原生图表、玻璃卡与 Logo 正常显示（截图）。7.0.1 重新导出的文件只过了 ppt-master 交付检查与 OOXML 回读，未在 PowerPoint 中打开 | 编辑保存重开回读与放映观感未做：本轮跳过 PowerPoint 的 AppleScript 自动化授权；Windows PowerPoint 未测 |
| 生图 | WARN | 正例复用历史真实生成图并登记来源哈希 | hero 长边 1672 < 2560；正文安静背景下部可见玻璃弧线，需真实重生成；缺超宽正文背景；章节页在 2560×1080 下主视觉压到标题，需要宽屏专用图 |

历史与逐轮细节在仓库 `review/CURRENT_STATUS.md` 与 `CHANGELOG.md`。
