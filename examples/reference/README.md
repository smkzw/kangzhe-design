# 参考实现（7.0）

按当前规范制作的正例，用来照着做；`examples/validation/` 下的历史样本只作回溯，不再作为模板。内容全部是合成演示数据，不对应真实研究。

| 轨道 | 入口 | 说明 |
|---|---|---|
| 站点式 HTML | `site/index.html`、`site/chapter.html` | Bento 首屏（左 4 栏标题/KPI/要点，右 8 栏电影与状态条）；下方段落入场、宽幅下钻、图表与甘特 |
| 流式 HTML | `stream/index.html` | 同一首屏结构；正文阅读栏 34em + 侧注，章节目录随阅读位置高亮 |
| HTML-PPT | `htmlppt/index.html` | 由 html-ppt-skill `new-deck.sh` 生成（原始输出 `htmlppt/scaffold.html`），`htmlppt/build.py` 派生；上游 `base.css`/`runtime.js` 原样随包 |
| PPTX | `pptx/` | 经 ppt-master 流程导出，见该目录 README |

## 共同做法

- 阅读内容写在 HTML 里，脚本只负责行为（无 JS 时内容仍完整）。
- 电影用 `KZMotion.storyboard(states)` 生成关键帧：停留时长按字数计算，最后一段回到首状态；载体内的分项事实、右侧节点与连线、下方状态条都由同一个进度驱动。
- 首屏在 `tokens.viewports` 每一档内一屏放下；可视区高度 ≥1000px 时才显示 `.kz-detail-tall` 次要说明（这些内容在页面其他位置完整可得）。

## 生图资产

`assets/` 复用历史真实生图（原始回执见 `examples/validation/KZ6-0929-A01/asset-provenance.json`），只转码为 WebP，来源哈希见 `assets/provenance.json`。已知缺口：

- 封面类主视觉长边 1672px，低于 `tokens.image.hero_min_long_edge_px` 2560，清晰度 WARN。
- 没有合格的超宽正文背景：现有超宽图是封面式玻璃丝带，违反 IMG-05，未采用；宽屏下对 16:9 安静背景做 cover 裁切。正式交付须真实生成超宽正文背景。

## 本次验证（2026-10-24，ego lite 0.6.0.16 / Chromium 154，视口 1280×720、1536×730、1920×940、1920×1080、2560×1080，另测 1920×900）

- 站点/流式：`KZLayoutQC.inspectFold` 3 页 × 6 视口，在电影初始态与静态帧各测一次，全部 PASS（初始态覆盖率 0.45–0.53、最大空白 ≤0.13；静态帧 0.50–0.60）。复测前 1920×1080 首页的“资料分组”卡底边被视口切掉，旧口径只看文字没有发现；现在外框越出也报 `FOLD_OVERFLOW`，首屏挂载 `KZMotion.fitFold`。`inspectOrphans` 5 视口 × 4 页无孤字行。
- HTML-PPT：8 页 × 5 视口与 1280×610、1366×640 无越界文字、无孤字、无卡片告警（`inspectCard` 已改为按内边距判断越界）；正文页 chrome 几何改由 tokens 生成的变量驱动，3 视口 × 5 页 90 个矩形与改动前逐一相同；入场时序与 PPTX 一致（卡片 0/70/140ms，观点句 410ms），表格逐行入场。
- 组件实验室：`tests/ego/runtime_checks.mjs` 20/20（含展开中途关闭的反向折回）。
- 未验证：上游 `render.sh`（使用 headless Chrome，本机规则不允许；替代截帧路径见 adapters/html-ppt.md）、S 演讲者窗口、打印、Safari、跨文档 view transition（需要 HTTP 同源，本次只用 file://）。总览里的图表和甘特缩略图为空，原因是上游在组件挂载前就克隆了页面，这是已知限制。
