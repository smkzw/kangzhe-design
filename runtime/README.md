# runtime：HTML 组件

三种 HTML 交付（HTML-PPT、站点式、流式）共用的组件。它们不是新的 PPT 引擎：不翻页、不缩放、不联网，不做数据持久化或外部模型调用。接口与参数见 [API.md](API.md)。

| 文件 | 作用 |
|---|---|
| `kz-tokens.css` / `.js` | 由 `tools/build_tokens.py` 从 `tokens/tokens.json` 生成，不手改 |
| `kz-glass.css` | 玻璃材质、阴影层级、Bento 首屏、KPI、电影结构、下钻、甘特外观、减少动态与打印 |
| `kz-layouts.css` | 正文模板片段的版式；站点与流式里按卡宽缩放字号 |
| `kz-motion.js` | 分层入场、弹簧倾斜与指针光、段落入场、KPI 计数、分镜生成、载体形变、seek 与暂停原因 |
| `kz-scenes.js` | 按 scene 步进的演示舞台（`Stage`、`audit()`、`coverage()`） |
| `kz-demo.js`、`kz-demo-patterns.js`、`kz-demo-fine.js`、`kz-demo-clinical.js` | 演示动画形式（15 DEMO），临床形式带容量检查 |
| `kz-clinical.js` | 临床场景族的数据合同 `KZClinical`，规则与报错和 `tools/kz_layouts` 的 Python 实现逐字相同 |
| `kz-charts.js` | ECharts 折线、柱 / 条、固定轴与类别色序，null 不当 0 |
| `kz-gantt.js`、`kz-gantt-studio.js` | 甘特（季度模型 [start,end)、拖动、键盘、撤销）与按 T 打开的全页编辑台 |
| `kz-explore.js` | 临床图的交互层：累计暴露阶梯（`KZExposure`，与甘特联动）、历时图与 SoA 的点击下钻与表内改数 |
| `kz-drilldown.js` | 宽对话框多层栈、焦点圈禁、按键与滚轮隔离 |
| `kz-flagship.css` / `.js`、`kz-flagship-stages.js` | 旗舰路线的页眉、进度、页脚、多场 GSAP 动效与 three.js 舞台 |
| `kz-icons.js` | 线性图标，由 `tools/build_icons.py` 从 `assets/icons/icons.json` 生成 |
| `kz-layout-qc.js` | `KZLayoutQC`：卡内分布、越界、首屏覆盖率、孤字行、色条、文字压叠、渲染字号 |
| `kz-audience.js` | 清理旧产物里残留的播放器控件（兼容层；新页面从源头不生成这些控件） |

加载顺序与依赖（ECharts、GSAP、three.js 取自 `assets/vendor/`）见各轨道配方 `design_specs/tracks-*.md`。电影只换标签不算合格（06 FILM-01）。
