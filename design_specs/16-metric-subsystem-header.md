# 16 · 智研 METRIC 子系统页头（统一规范）

用户 2026-11-11 定：各子系统（医学监查、临床监查、入排审核、方案设计与撰写、竞品调研等）的网页页头统一为
**「智研 METRIC 主标｜子系统横版」**，页头**不放康哲标志**。资源一律取自本仓库 `assets/metric/`，不另存改名副本。

## 1. 资源（assets/metric/）

| 用途 | 文件 | 说明 |
| --- | --- | --- |
| 页头·平台主标 | `lockup-3x1-header.svg` | 智研 METRIC 横版；去四周留白版，宽高比约 4.98 |
| 页头·子系统横版 | `sub-X-lockup-header.svg` | X＝子系统字母（见下表）；去留白版，宽高比 5.1–6.4 |
| 浏览器图标 favicon | `sub-X.svg` | 子系统方形图标（100×100） |
| 原件 | `lockup-3x1.svg`、`sub-X-lockup.svg`、`mark.svg`、`icon.svg` | 官方原件逐字节保留（汇报、海报等留白版式用） |

`-header` 版只改了 `viewBox/width/height`（去掉四周留白），图形路径与原件逐字节相同；来源与 md5 见 `provenance.json`。
禁止重画、改色、改字、拉伸，禁止用位图替代。

| 字母 | 子系统 | 子系统色 |
| --- | --- | --- |
| T | 试验数据与知识中枢 | `#4A5568` |
| R | 中心遴选与启动评估 | `#2A9D8F` |
| E | 入排资料智能审核 | `#FF9900` |
| M | 数字化医学监查 | `#E8590C` |
| C | 数字化临床监查 | `#407AAA` |
| I | 安全性监测 | `#A85F34` |
| P | 方案设计与撰写 | `#6D4AA8` |
| L | 竞品调研与设计先例 | `#B8406A` |

## 2. 页头结构与尺寸

```
[智研 METRIC 主标 30px 高] ─ 14px ─ │ 1px×28px ─ 14px ─ [子系统横版 32px 高] ─ 28px ─ 导航/面包屑 …… 右侧元素
```

- 高度 56px，`position: sticky; top: 0`；左右内边距 20px。
- 背景 `rgba(255,255,255,.88)` + `backdrop-filter: blur(12px)`；底边 `1px solid rgba(190,178,161,.35)`；不加阴影、不加色条。
- 分隔线 `1px × 28px`，色 `rgba(190,178,161,.6)`。
- 主标点击回平台首页（若有）；子系统横版点击回本子系统首页。`alt` 分别写「智研 METRIC」「<子系统中文名>」。
- 同一子系统内的首页、列表页、详情页共用同一页头；子系统**内部**的不同空间（如医学监查与临床监查同属一套看板）
  按当前空间切换横版字母（M ↔ C），主标不变。
- 页头里不再用 HTML 文字重复子系统名（横版已含中文名与 METRIC · X · 英文名）。
- 窄屏（< 900px）：子系统横版改用 `sub-X.svg` 方形图标 28px。

## 3. 浏览器标题与图标

- `<title>`：`<页面名> · [项目代号 · ]<子系统中文名> · 智研 METRIC`（「智研」与「METRIC」之间有空格；项目内页面带项目代号，便于多标签页区分）；子系统首页可省略页面名。
- `<link rel="icon" type="image/svg+xml" href="…/sub-X.svg">`。

## 4. 代码片段

见 `assets/metric/header-snippet.html`（纯 HTML/CSS，无框架依赖；React/Vue 按同一结构与类名移植）。

## 5. 接入检查（各子系统自查）

1. 页头只有主标与子系统横版两枚标志，无康哲标志、无其他图标或文字标题重复。
2. 两个文件均来自 `assets/metric/`，md5 与 `provenance.json` 一致（不另存改名副本）。
3. 高度 56px、分隔线、底边、背景按第 2 节。
4. favicon 为本子系统 `sub-X.svg`；`<title>` 按第 3 节。
5. 首页与内页一致；截图核对标志清晰、不变形、不裁切。

## 6. 各子系统现状与接入要点（2026-11-11 盘点）

| 子系统 | 现状 | 接入要点 |
| --- | --- | --- |
| M/C 医学监查·临床监查（看板＋工作台首页） | 已按本规范改完（medical-monitoring-report 3459afd 起；工作台首页同步） | — |
| E 入排资料智能审核（enrollment-review-app frontend） | 已是「主标＋E 横版」，文件改名为 metric.svg / eligibility*.svg，横版靠 overflow 裁切留白；页头 52px；title「入排资料智能审核 · 智研METRIC」 | 改用 `lockup-3x1-header.svg`、`sub-E-lockup-header.svg`、`sub-E.svg`（不再裁切）；页头 56px、分隔与底边按第 2 节；title 改为「… · 入排资料智能审核 · 智研 METRIC」 |
| P 方案设计与撰写（protocol-v3-workbench mw.html / StudioApp） | 康哲 logo＋P 方形图标＋HTML 文字「方案设计与撰写 / METRIC·P」；没有主标；title「方案设计与撰写 · METRIC」；老入口 index.html、mw-runs.html 各不相同 | 去掉康哲 logo 与 HTML 文字，改为主标＋`sub-P-lockup-header.svg`；三个入口统一同一页头；title「… · 方案设计与撰写 · 智研 METRIC」 |
| L 竞品调研与设计先例（competitive-intelligence-workflow 报告站 base.html） | 只有 L 方形图标（ciw-mark.svg）＋文字「竞品调研」；无主标；title「报告名 · 适应症」 | 改为主标＋`sub-L-lockup-header.svg`，去掉文字「竞品调研」；title「报告名 · 适应症 · 竞品调研与设计先例 · 智研 METRIC」；被嵌入时隐藏页头的现有逻辑保留 |

各子系统也不再使用橙色丝带或其他页头色条；设计令牌统一引用本仓库 `tokens/`（当前各子系统分别停在 7.1.1、7.1.3 与自定义变量）。
