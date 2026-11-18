# PPTX 常规正例：ppt-master Default 全流程

一份 6 页合成示例汇报（封面、目录、研究范围、资料完整性、核对计划、结束页），按 ppt-master 的 Default Generate 路由从头到尾制作：两次确认页（Stage 1 沟通合同与自由设计，Stage 2 方案与制作）都由用户在浏览器确认页上提交。康哲提供品牌、字号、材质、构图、动效与验收；ppt-master 负责规划产物、检查器与导出。同级 `../pptx/` 是转换器级探针，本目录是完整流程。

## 文件

| 文件 | 来源步骤 |
|---|---|
| `source-brief.md` | 用户提供的素材（合成数据） |
| `design_spec.md`、`spec_lock.md` | Step 4：确认结果写入的设计规范与执行锁 |
| `page-plan.json`、`asset-manifest.json` | 康哲 tracks-pptx 第 1 步：页面计划与资产清单（hero 文字框取自 `hero_layout.layout()`） |
| `svg_output/*.svg` | Step 6：逐页手写的页面（hero 页由 `hero_layout.svg_fragment` 片段改写，正文页 chrome 取 tokens，双菱形取 `brand_fragments.facets(native=True)`） |
| `animations.json` | 自动入场动效 |
| `notes-total.md` | 讲者备注（09） |
| `header-mark-plan.json` | 导出后双菱形绑定计划 |
| `readback.py` | 导出后对照康哲合同做 OOXML 回读：hero 文字框、图表、动效、讲稿、玻璃 |

页面引用的 `../images/*.png` 是历史真实生成图，未随包附带；同一批图的 WebP 版在 `../assets/`。Logo PNG 取 `assets/logo_bot.png`。

## 命令顺序

`${PM}` 指 ppt-master 的 `SKILL_DIR`，`${KZ}` 指本技能目录，Python 3.10+。

```bash
python3 ${PM}/scripts/attribution_guard.py
python3 ${PM}/scripts/project_manager.py init kangzhe_integrity --format ppt169 --dir <工作目录>/projects
python3 ${PM}/scripts/project_manager.py import-sources <project> <brief.md> <images...>
python3 ${PM}/scripts/analyze_images.py <project>/images
# Stage 1：写 confirm_ui/recommendations.stage1.json → server.py <project>（确认页）→ 用户提交 → --wait-only --wait-stage stage1
# Stage 2：写 recommendations.stage2.json（康哲字号写进 typography.sizes，并在确认页上核对）→ 用户提交 → 读一次 result.json → --shutdown
python3 ${PM}/scripts/visualization_recall.py validate chart/grouped_bar_chart chart/gantt_chart
# 写 design_spec.md、spec_lock.md
python3 ${PM}/scripts/project_manager.py validate <project>
python3 ${KZ}/tools/qc_plan.py page-plan.json --manifest asset-manifest.json --asset-root <project>/images
python3 ${PM}/scripts/text_measure.py calibrate <project> --outline
python3 ${PM}/scripts/svg_editor/server.py <project> --live          # 实时预览
# 手写 svg_output/*.svg
python3 ${PM}/scripts/stamp_native_fallbacks.py <project>/svg_output/04_资料完整性.svg --write
python3 ${PM}/scripts/svg_quality_checker.py <project> --canonical-authoring --stage final --json
python3 ${PM}/scripts/svg_position_calculator.py calc bar ...         # verify-charts
# 写 notes/total.md、animations.json
python3 ${PM}/scripts/animation_config.py validate <project>
python3 ${PM}/scripts/total_md_split.py <project>
python3 ${PM}/scripts/finalize_svg.py <project>
python3 ${PM}/scripts/svg_to_pptx.py <project> --native-charts-and-tables
python3 ${KZ}/tools/bind_header_mark_pptx.py <exported>.pptx marked.pptx header-mark-plan.json --receipt header-mark-binding.json
python3 ${KZ}/tools/bind_hero_pptx.py marked.pptx deck.pptx page-plan.json --receipt hero-binding.json
python3 ${PM}/scripts/pptx_delivery_check.py deck.pptx
```

## 成品要点

- 资料完整性页是原生簇状柱图（应收 slate、已收 orange），可在 PowerPoint 里编辑；核对计划页的甘特按季度模型 [start,end) 画成原生形状。
- 入场：组间错峰 `stagger_ms.pptx_card`（180 ms），观点句再隔 `takeaway_gap`；图表自底部擦入，甘特区自左擦入。卡壳是静态装饰，卡头、图表、图例、观点句各自成动画单元。
- 封面一行标题贴框底；hero 文字框导出后用 `bind_hero_pptx.py` 固定到 tokens 位置（导出会把文字框收缩到内容大小）。
- 主题字体 latin Arial、ea Microsoft YaHei；6 页均有讲者备注。

## 制作要点

- ppt-master 要求页面根模块的 `data-pptx-bounds` 互不重叠：需要“卡壳静止、内容逐个入场”时，卡壳写成 `data-pptx-role="decoration"` 的根级图元，卡头、图表、图例、观点句各自成根组。
- Stage 2 确认页会按正文基准重算标题、副标题、注释字号，康哲字号要在页面上手动固定，确认后核对 `result.json` 的 `typography.sizes`（adapters/ppt-master.md）。
- Logo PNG 要登记进 §VIII 与 `spec_lock.md images`，否则是计划外图片。
- `entrance_wipe` 的方向以预设表为准：自底部写 `direction: "down"`（subtype 4），自左写 `"left"`（subtype 8）。
- 动效与 Morph 的观感只在 PowerPoint 中验收（10 G9）。
