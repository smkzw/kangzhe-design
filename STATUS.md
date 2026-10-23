# 当前验证状态 · 2026-10-24（7.0.0 / KZ7-1024-B03）

整体 **PARTIAL**：规范、runtime 与四轨正例已重构并在本机实测；PPTX 已按 ppt-master Default 全流程做出正例并经 PowerPoint 实机检查。Windows Office、Safari、上游 headless 截帧尚未覆盖。状态词见 `design_specs/10-quality-gates.md` QA-STATUS。

| 证据层 | 状态 | 已完成（本机实测） | 未完成 / 边界 |
|---|---|---|---|
| 单元测试 | PASS | 仓库 `tests/test_*.py` 12 个文件全部通过（维护者回归，不随包发布） | Python 3.10+ |
| 组件（ego lite / Chromium 154） | PASS | 组件实验室真实指针/键盘/滚动检查 20/20：入场分层、弹簧倾斜、电影交叉淡入与 seek、下钻展开/折回/中途关闭/按键隔离/焦点、段落入场、光场视差、图表揭示、减少动态 | Playwright 版检查已按 7.0 更新但未在本机运行 |
| 站点 / 流式正例 | PASS | 3 页 × 6 视口（`tokens.viewports` 五档 + 1920×900），电影初始态与静态帧各测 `inspectFold`，全部 PASS；无孤字 | 1920×940 初始态覆盖率贴近阈值 0.45；Safari、跨文档 view transition（需 HTTP 同源）未测 |
| HTML-PPT 正例 | PASS | html-ppt-skill 脚手架起步；8 页 × 5 视口与 1280×610、1366×640 无越界/孤字/卡片告警；入场时序与 PPTX 一致；深链接、方向键、O、`?preview`、减少动态 | `render.sh`（headless）未跑，替代截帧见 adapter；S 演讲者窗口、打印未测；总览缩略图中的图表为空（上游限制） |
| PPTX（ppt-master Default 全流程） | PASS | `examples/reference/pptx-default/`：两次确认页、Design Spec/lock、手写 SVG、最终检查 0 错误、verify-charts、备注、动效、原生图表导出、双菱形与 hero 绑定、交付检查 0 错误、OOXML 回读 | 见下一行的 PowerPoint 实机 |
| PowerPoint 实机（macOS 16.114） | PENDING | 文件打开无修复提示，6 页、讲者备注、图表与玻璃卡正常显示 | 编辑保存回读与播放观感：自动化授权完成后补测 |
| 生图 | WARN | 正例复用历史真实生成图并登记来源哈希 | hero 长边 1672 < 2560；正文安静背景下部可见玻璃弧线，需真实重生成；缺超宽正文背景 |

历史与逐轮细节在仓库 `review/CURRENT_STATUS.md` 与 `CHANGELOG.md`。
