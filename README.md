# Kangzhe Design 7.1

康哲药业医学部的单一 Liquid Glass 设计技能，覆盖可编辑 PPTX、HTML-PPT、站点式 HTML、流式 HTML。PPTX 始终经 hugohe3/ppt-master 制作，HTML-PPT 始终从 lewislulu/html-ppt-skill 脚手架起步；本包负责品牌与内容表达、图像保护、材质、动效与组件、验收，不替代上游的路由、缩放、导航与导出。

7.1 为 PPTX 与 HTML-PPT 增加旗舰路线（`design_specs/14-flagship.md`，用于对外与顶层汇报：浅色画布上的全屏光场、液态玻璃透镜与身份胶囊），开工前先请用户在常规与旗舰之间选路。

7.0 是一次分层重构：规范只写设计规则，验收方法集中在 `design_specs/10-quality-gates.md`，事故史移出正文；新增阴影层级与指针光源、token 化的动作词汇与编排、Bento 首屏与密度指标、按浏览器可视区的验收视口，以及四轨的正例。变化逐条见 [CHANGELOG](CHANGELOG.md)，验证状态见 [STATUS.md](STATUS.md)。

## 目录
| 目录 | 内容 |
|---|---|
| `SKILL.md` | 入口：四轨与引擎、硬规则、读取顺序 |
| `design_specs/` | 规则所有者（00–11、13、14 旗舰路线）与四个轨道配方 |
| `tokens/` | 唯一数值源；`tools/build_tokens.py` 生成 `runtime/kz-tokens.*` |
| `runtime/` | 玻璃 CSS、动效、图表、甘特、下钻、布局 QC；接口见 `runtime/API.md` |
| `adapters/` | ppt-master 与 html-ppt-skill 的插入点、实测事实、HTML-PPT 生命周期桥 |
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
for t in tests/test_*.py; do python3 "$t"; done
python3 tools/build_dist.py            # 生成 dist/kangzhe-design 与 PACKAGE_MANIFEST.json
```

需要 Python 3.10+ 与 `requirements.txt`（`jsonschema`、`Pillow`）；安装方法见 [INSTALL.md](INSTALL.md)，当前验证状态见 [STATUS.md](STATUS.md)；浏览器检查需要能发真实指针事件的浏览器驱动（`tests/ego/` 用 ego-browser，`tests/*_browser.py` 用 Playwright）。

打开 `examples/reference/site/index.html` 看站点首屏，`examples/reference/htmlppt/index.html` 看 HTML-PPT（方向键翻页），`examples/component-lab.html` 看组件。内容均为合成示例，不对应真实研究。
