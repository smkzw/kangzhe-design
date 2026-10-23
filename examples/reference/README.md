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

## 本次验证（2026-10-23，ego lite / Chromium 154，视口 1280×720、1536×730、1920×940、2560×1080）

- 站点/流式：`KZLayoutQC.inspectFold` 3 页 × 4 视口均 PASS（覆盖率 0.45–0.51，最大空白矩形 ≤0.13）；电影载体文字 `inspectTextBounds` PASS；`inspectOrphans` 在 5 个电影进度点均无孤字行。
- HTML-PPT：8 页 × 4 视口无越界文字、无孤字；正文 20、卡标题 24 逻辑 px（computed ÷ `--kz-un`）；深链接、方向键、O 总览、`?preview` 静态、减少动态均实测。翻页时离开页在退出窗口内保持不透明，玻璃模糊不会在翻页时失效。
- 未验证：上游 `render.sh`（使用 headless Chrome，本机规则不允许）、S 演讲者窗口、打印、Safari。总览里的图表和甘特缩略图为空，原因是上游在组件挂载前就克隆了页面，这是已知限制。
