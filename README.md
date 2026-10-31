# Kangzhe Design 7.2.2

康哲药业医学部的单一 Liquid Glass 设计技能，覆盖可编辑 PPTX、HTML-PPT、站点式 HTML、流式 HTML。PPTX 始终经 hugohe3/ppt-master 制作，HTML-PPT 始终从 lewislulu/html-ppt-skill 脚手架起步；本包负责品牌与内容表达、图像保护、材质、动效与组件、验收，不替代上游的路由、缩放、导航与导出。

7.1 为 PPTX 与 HTML-PPT 增加旗舰路线（`design_specs/14-flagship.md`，用于对外与顶层汇报：浅色画布上的全屏光场、液态玻璃透镜与身份胶囊），开工前先请用户在常规与旗舰之间选路。7.1.2 让 HTML-PPT 的电影与演示按 scene 随翻页键与滑动推进，新增 12pt 辅助文字角色，并新增演示性动画（`design_specs/15-demo-motion.md`）。7.1.3 禁止卡片边缘装饰色条并提供检查工具，PPT 两轨出图前先过生图能力闸门（没有生图能力时用登记的缺省背景套），站点与流式非首页改为章节头 + 密排网格并测逐屏密度，演示形式增至 16 种（图库 `examples/motion/index.html`，HTML-PPT 模板组 `examples/motion/deck/index.html`）。

7.2 给常规路线的正文页加了两轨共用的模板库（`design_specs/13-layout-density.md` BODY-02，27 套，`tools/kz_layout.py`）：入排标准原文密排与接续分页、SoA、讨论题、流程、高密度甘特、数据图 + 解读、森林图、KM、CONSORT、方案比较、KPI 看板、风险矩阵、分层架构等，HTML 图表用 ECharts、PPTX 用原生图表与形状；原文条款不压缩（03 COPY-09），强调用加粗、深红、下划线、高亮四种；选路与生图能力在开工第一站一次问完，生成图经 `tools/quiet_plate.py` 合成到白底并量安静度（04 IMG-08）；导出前跑 `tools/check_kz_project.py`。样张：`examples/templates/deck/index.html`。7.2.2 起页标题只写章节或主题名，讲稿按 09 写（hero 页一句、不报幕、临床口语，`tools/check_notes.py`），说明文字最小 10.5pt，卡片边缘色条绝对禁止。

7.0 是一次分层重构：规范只写设计规则，验收方法集中在 `design_specs/10-quality-gates.md`，事故史移出正文；新增阴影层级与指针光源、token 化的动作词汇与编排、Bento 首屏与密度指标、按浏览器可视区的验收视口，以及四轨的正例。变化逐条见 [CHANGELOG](CHANGELOG.md)，验证状态见 [STATUS.md](STATUS.md)。

## 目录
| 目录 | 内容 |
|---|---|
| `SKILL.md` | 入口：四轨与引擎、硬规则、读取顺序 |
| `design_specs/` | 规则所有者（00–11、13 密排、14 旗舰路线、15 演示动画）与四个轨道配方 |
| `assets/` | 官方 Logo、双菱形原生形状、缺省背景套（04 IMG-07，含哈希清单）、图标（`assets/icons/`）与 ECharts |
| `tokens/` | 唯一数值源；`tools/build_tokens.py` 生成 `runtime/kz-tokens.*` |
| `runtime/` | 玻璃 CSS、动效、图表、甘特、下钻、布局 QC；接口见 `runtime/API.md` |
| `adapters/` | ppt-master 与 html-ppt-skill 的插入点、实测事实、HTML-PPT 生命周期桥 |
| `examples/templates/` | 正文模板库的示例数据（即数据合同）与两轨样张（`deck/index.html`、`pptx/build.py`） |
| `examples/reference/` | 按当前规范做的正例：站点、流式、HTML-PPT、PPTX（ppt-master Default 全流程与导出探针） |
| `examples/component-lab.html` | 组件实验室（离线可开，虚构数据） |
| `schemas/`、`tools/` | 页面/资产/电影/甘特合同；计划预检、hero 与双菱形片段、PPTX 绑定、打包 |
| `tests/` | 单元测试；`tests/ego/` 真实输入的浏览器检查 |
| `review/`、`agent/`、`docs/history/`、`examples/validation/` | 维护与历史资料，不进安装包 |

## 使用
```bash
python3 tools/context_pack.py --track htmlppt --stage bootstrap --features charts,film,gantt,drilldown,notes
python3 tools/build_tokens.py          # 改 tokens 后
python3 tools/qc_plan.py examples/reference/pptx-default/page-plan.json
python3 tools/check_edge_bars.py examples/reference/pptx-default/svg_output   # 02 LG-02：有色条即非零退出
python3 tools/kz_layout.py list                                # 13 BODY-02 模板目录；render 生成页面与原文核对回执
python3 tools/check_kz_project.py <ppt-master 项目> --plan page-plan.json   # 10 G-KZ，导出前
for t in tests/test_*.py; do python3 "$t"; done
python3 tools/build_dist.py            # 生成 dist/kangzhe-design 与 PACKAGE_MANIFEST.json
```

需要 Python 3.10+ 与 `requirements.txt`（`jsonschema`、`Pillow`、`numpy`）；安装方法见 [INSTALL.md](INSTALL.md)，当前验证状态见 [STATUS.md](STATUS.md)；浏览器检查需要能发真实指针事件的浏览器驱动（`tests/ego/` 用 ego-browser，`tests/*_browser.py` 用 Playwright）。

打开 `examples/reference/site/index.html` 看站点首屏，`examples/reference/htmlppt/index.html` 看 HTML-PPT（方向键逐 scene 推进与翻页），`examples/motion/index.html` 看演示性动画，`examples/component-lab.html` 看组件。内容均为合成示例，不对应真实研究。
