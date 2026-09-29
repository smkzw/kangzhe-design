# Kangzhe Design 6.0.0

康哲药业医学部的单一 Liquid Glass 设计技能。覆盖可编辑 PPTX、HTML-PPT、站点式 HTML、流式 HTML。替代原 `kangzhe-design 4.5.7` 与 `kangzhe-design-3d 5.2.7`，不保留 flat、3d 或 legacy 模式。

**版本说明：**6.0.0 是完成重构后的规范版本。已提供可运行参考组件和本地测试；真实生图、两个指定引擎端到端、原生 Office 编辑回读与多模型对照仍需后续验证。详见 `review/VALIDATION_STATUS.md`，不能把版本号当成所有能力已认证。

## 使用

安装只保留本目录的一个 SKILL.md。读取顺序见 `SKILL.md`；四轨共用 tokens 和主题所有者，条件读取图表、电影、下钻、甘特、讲稿规则。不把整个维护包无差别塞进模型上下文。

PPTX 始终通过 hugohe3/ppt-master；HTML-PPT 始终通过 lewislulu/html-ppt-skill。本包负责品牌与内容表达、图片保护、样式/组件和验收，不替代它们的 scaffold、路由、缩放、导航和导出。

## 目录

| 目录 | 用途 |
|---|---|
| design_specs | 核心品牌/玻璃/中文/生图/图表/电影/下钻/甘特/讲稿/QC；四轨入口 |
| tokens | 单一数值源；px/pt、颜色与部门、固定几何、字号和节奏 |
| assets | 原始官方 logo、随包 ECharts 6.1.0 及授权说明；没有字体文件 |
| runtime | 范围受控的玻璃、连续形变、图表、宽下钻、季度编辑参考 |
| adapters | 两个上游的职责/插入点与 HTML-PPT 增量生命周期桥 |
| schemas | 康哲侧页面/资产/电影/季度甘特合同，不冒充上游schema |
| tools / tests | 参数生成、计划预检、保护mask、PPTX只读审计、浏览器与单元测试 |
| examples | 可离线打开的独立组件实验室；虚构数据，不是正式上游PPT主题 |
| review | 输入审阅、重构依据、测试状态及实际证据 |
| agent | 后续执行计划、模型对照、提示、夹具和 handoff 模板 |

## 参考实现

打开 `examples/component-lab.html`。该页不需要构建和外网依赖，采用程序化光场，包含连续主载体、ECharts浅面积折线/柱图、两层宽下钻、可拖改季度甘特。它是参考组件，不是“已完成html-ppt-skill集成”的幻灯片。

此环境的本地URL导航受浏览器管理策略限制，实际测试通过把本地依赖内联到 Chromium set_content 完成；本地双击/HTTP、上游演讲者窗口、Safari 和 Office 仍需分别验证。不得在宣传中省略这一边界。

## 本地工具

使用当前已有 Python 3.10+、Node 与浏览器即可检查；Python检查依赖 `jsonschema`、`Pillow`，浏览器检查另需 `playwright` 和实际 Chromium。不要把安装依赖或启动模型作为每次修订的重复步骤。

```bash
python tools/context_pack.py --track htmlppt --features charts,film,gantt,drilldown,notes
python tools/build_tokens.py
python tests/test_contracts.py
python tests/browser_smoke.py --chromium /path/to/chromium --out /path/to/evidence
python tests/film_cycle.py --chromium /path/to/chromium --out /path/to/cycle.json
python tools/qc_plan.py agent/fixtures/page-plan.valid.json
```

preflight 没有资产 manifest 时返回 pending 的实际生图审阅项；不是生产放行。`tools/glass_svg.py` 只提供上游可参考的原语，未单独创建最终 PPTX。

## 下一阶段

将 `agent/prompts/EXECUTE.md` 交给开发 Agent，主包与 Agent执行包放在同一工作区。优先两条引擎真实集成和真实生图，再用不同能力模型×harness对照反复修改唯一规则所有者。没有工具/凭据时记录阻塞，不伪造通过。
