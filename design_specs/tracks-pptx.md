# PPTX 轨道（经 ppt-master）

唯一制作引擎是安装的 hugohe3/ppt-master（当前核对 v6.7.3）。先读它的 `SKILL.md`、`workflows/routing.md`，按其路由执行；本包不另造 PPTX 导出器，也不用 python-pptx 等其他生成器绕过。接口细节见 `adapters/ppt-master.md`。

## 路由
- 新建康哲 Brand/Style/Layout workspace：上游 Create Template，建成后用其 `register_template.py` 注册，之后 Default 第一阶段可直接选用。
- 用已验证 workspace 生成：Default 完整流程（含上游 ⛔ BLOCKING 确认门，必须等用户确认）。Quick 只有用户明确要求时使用，且不计入 Default 验收。
- 改用户现有 PPTX：上游 Edit Native PPTX，不把原文件当 Generate 模板硬套。

## 步骤
1. **计划**：事实清单 → 页型与信息层级（03 COPY-01/06）→ 每页构图预设（13 BODY-01）→ hero 版式 ID（11）→ page-plan（`schemas/page-plan.schema.json`）与 `tools/qc_plan.py` 预检。
2. **注入上游设计阶段**：01 chrome 与 tokens 进品牌与版式；02 材质进样式（在 Style 的 Decoration 里写明玻璃配方是多手段叠加，避免 Executor 按上游“单一强调”默认简化掉）；03/04/05/09 进策划、图像 manifest、SVG 与 notes。
3. **图像**：在上游图像阶段按 04 加保护区与审阅；不另起并行生图流程。
4. **Executor SVG**：正文卡用 `tools/glass_svg.py` 原语（渐变 alpha + 一个 `feDropShadow`，参数取 `elevation.pptx`）；hero 用 `tools/hero_layout.svg_fragment`；双菱形先用 `brand_fragments.facets(native=True)` 预览；bullet 写 `• ` 前缀（导出为原生项目符号）。每个内容单元一个带 `data-pptx-bounds` 的顶层 `<g id>`；背景、横线、Logo、页脚用结构角色。
5. **数据**：原生图表按 05 CHART-05；甘特用原生形状（08）。
6. **动效**：需要时按 06 MOTION-07 写 `animations.json`（入场随上一项、错峰、Morph 承载载体）。
7. **检查与导出**：严格按上游 Step 7 的顺序：`svg_quality_checker.py`（最终门）→ 备注拆分 → `finalize_svg.py` → `svg_to_pptx.py`；需要原生图表时加 `--native-charts-and-tables`。
8. **品牌绑定**：导出后 `tools/bind_header_mark_pptx.py` 绑定原生双菱形；hero 文字框需要固定时用 `tools/bind_hero_pptx.py`（6.7 起上游按字体度量定位首行基线，先确认是否仍需要）。保留上游原件，再跑 `pptx_delivery_check.py`。
9. **验收**（10 G9）：解包 OOXML 核对对象、文本、字体、alpha、阴影、图表数据、`p:timing` 与 Morph 名称；在目标 PowerPoint 中打开、编辑、保存、重开。LibreOffice 渲染不冒充 PowerPoint 验收。

## 必验
- 全文可编辑优先于逐像素模拟玻璃：正文、卡、图、表原生；光学背景是独立图片。
- 每页内容区与标题/页脚取原值，不用改字号补救空间；正文背景按 04 IMG-05 单独生成。
- 指针倾斜、弹窗下钻、日期联动不属于 PPTX 能力。

参考实现与导出回读：`examples/reference/pptx/`（转换器级探针，非 Default 全流程）。
