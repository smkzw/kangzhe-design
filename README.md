# Kangzhe Design 6.0.0

康哲药业医学部的单一 Liquid Glass 设计技能。覆盖可编辑 PPTX、HTML-PPT、站点式 HTML、流式 HTML。替代原 `kangzhe-design 4.5.7` 与 `kangzhe-design-3d 5.2.7`，不保留 flat、3d 或 legacy 模式。

**版本说明：**6.0.0是规范版本；当前修订A04，四轨多轮验证继续中，尚未完整验收。新版候选包含桌面宽屏站点范围、ARCO机制取舍和指定生图能力边界。已完成的引擎、组件、原生Office与模型检查分别见[当前状态](review/CURRENT_STATUS.md)。

## 使用

安装只保留本目录的一个 SKILL.md。读取顺序见 `SKILL.md`；双菱形只用于 PPTX 与 HTML-PPT，站点式和流式 HTML 不使用。四轨共用 tokens 和主题所有者，条件读取图表、电影、下钻、甘特、讲稿规则。不把整个维护包无差别塞进模型上下文。

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

组件测试使用Chromium内联harness；A03另有EGO真实HTTP导航/交互与IAB补充截图。两类证据分开；A04新增了A03副本的Mac PowerPoint编辑回读及测试者HTML-PPT双窗口检查；这不代表Safari、Windows Office及全部最终产物已验证。

## 本地工具

使用当前已有 Python 3.10+、Node 与浏览器即可检查；Python检查依赖 `jsonschema`、`Pillow`，浏览器检查另需 `playwright` 和实际 Chromium。不要把安装依赖或启动模型作为每次修订的重复步骤。

```bash
python tools/context_pack.py --track htmlppt --stage bootstrap --features charts,film,gantt,drilldown,notes
# 后续逐阶段 plan/assets/author/verify；verify 保留全部适用硬门
python tools/build_tokens.py
python tests/test_contracts.py
python tests/browser_smoke.py --chromium /path/to/chromium --out /path/to/evidence
python tests/film_cycle.py --chromium /path/to/chromium --out /path/to/cycle.json
python tools/qc_plan.py agent/fixtures/page-plan.valid.json
```

preflight 没有资产 manifest 时返回 pending 的实际生图审阅项；不是生产放行。`tools/glass_svg.py` 只提供上游可参考的原语，未单独创建最终 PPTX。

## 后续本机验证

2026-09-29 的 KZ6-0929-A01 已完成迁移安装与 P0 本机复测；两条上游和跨模型验证继续中。分层结果见 [本机验证状态](review/KZ6-0929-A01/STATUS.md)。

## 下一阶段

将 `agent/prompts/EXECUTE.md` 交给开发 Agent，主包与 Agent执行包放在同一工作区。优先两条引擎真实集成和真实生图，再用不同能力模型×harness对照反复修改唯一规则所有者。没有工具/凭据时记录阻塞，不伪造通过。

## KZ6-0929-A02 固定首尾、目录与章节
四类页面共用版式 ID、逻辑坐标和专用字号，详见 [固定形态合同](design_specs/11-hero-layouts.md)。[本轮状态](review/KZ6-0929-A02/STATUS.md)分别报告规则代码、组件、两引擎、原生编辑与跨模型边界。公开示例均为合成内容，不包含用户提供的临床参考原件。

## A03 历史验证样本
[无播放器控件的HTML-PPT](examples/validation/KZ6-0929-A03/html-ppt/index.html) · [原生PPTX](examples/validation/KZ6-0929-A03/matched-seven.pptx)。均为owner制作的合成内容，不是测试模型成功样本，也不是当前批准的视觉模板。其资产、双菱形、布局和vendor保留当时版本供回溯；新产物遵循当前tokens与design_specs，不照抄历史样式。A04对该HTML样本的宿主生命周期另做修复与组件验证，不能由此宣称历史全部样式已重验。
