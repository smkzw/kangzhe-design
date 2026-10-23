# PPTX 正例：ppt-master Default 全流程（2026-10-24）

一份 6 页合成示例汇报（封面、目录、研究范围、资料完整性、核对计划、结束页），按 ppt-master 6.7.3 的 Default Generate 路由从头到尾执行：两次确认页（Stage 1 沟通合同与自由设计，Stage 2 方案与制作）都在浏览器确认页上由用户角色提交，没有跳过任何门。kangzhe-design 提供品牌、字号、材质、构图、动效与验收；ppt-master 负责规划产物、checker 与导出。

和同级 `../pptx/` 的转换器级探针不同，本目录是完整流程的产物与证据。

## 文件

| 文件 | 来源步骤 |
|---|---|
| `source-brief.md` | 用户提供的素材（合成数据） |
| `design_spec.md`、`spec_lock.md` | Step 4：确认结果写入的设计规范与执行锁（`project_manager.py validate` 通过） |
| `page-plan.json`、`asset-manifest.json` | 康哲 tracks-pptx 第 1 步：页面计划与资产清单（`qc_plan.py`；hero 文字框取自 `hero_layout.layout()`） |
| `svg_output/*.svg` | Step 6：主 agent 手写的页面（hero 页由 `hero_layout.svg_fragment` 片段改写，正文页 chrome 取 tokens，双菱形取 `brand_fragments.facets(native=True)`） |
| `animations.json` | 自定义动效阶段（用户要求自动入场） |
| `notes-total.md` | 讲者备注（康哲 09） |
| `header-mark-plan.json`、`header-mark-binding.json`、`hero-binding.json` | 导出后的品牌绑定计划与回执 |
| `delivery-check.json`、`ooxml-readback.json`、`readback.py` | 交付检查与 OOXML 回读 |
| `kangzhe_integrity_default.pptx` | 交付文件（只在仓库与 Release 附件中，不进安装包） |

页面引用的 `../images/*.png` 是用户提供的历史真实生成图（来源哈希见 `asset-manifest.json`），未随包附带；同一批图的 WebP 版在 `../assets/`。Logo PNG 取 `assets/logo_bot.png`。

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

## 结果

| 检查 | 结果 |
|---|---|
| `project_manager.py validate` | 通过 |
| `svg_quality_checker.py --stage final` | 6 页 0 错误、0 阻断（3 条紧凑写法建议） |
| verify-charts | 分组柱：纵向与计算器一致，横向按 PowerPoint 簇状槽位（柱宽 = 槽宽 ÷（系列数 + 1.5））更新；甘特：每季度 268 px，起止端一致 |
| 导出 postflight | `passed-with-warnings`（同上 3 条建议） |
| `pptx_delivery_check` | 绑定后 0 错误、0 建议 |
| hero 文字框 | 6.7 导出会把文字框收缩到内容大小（封面标题 538×86），偏差超过 HERO-04 的 2 px，因此绑定；绑定后与 tokens 偏差 0 |
| 原生图表 | `barChart` 簇状柱，两系列 2/12/6/4 与 2/9/6/3，色 #6E7B8C / #D46B08，值轴 0–15、主刻度 5 |
| 动效 `p:timing` | 目录与研究范围 Fade 0/70/140 ms；资料完整性 Wipe 自底部（presetSubtype 4）+ Fade 70/140 + 观点句 410 ms；核对计划 Wipe 自左（presetSubtype 8） |
| 讲者备注 | 6 页均有 |
| 字体 | 主题 latin Arial / ea Microsoft YaHei |

## 过程中的教训（已写回规范或工具）

- Stage 2 确认页会按正文基准重算标题、副标题、注释字号，候选里写的 `typography.sizes` 不会显示；康哲字号要在页面上手动固定，确认后核对 `result.json` 的 `typography.sizes`（adapters/ppt-master.md）。
- Logo PNG 要登记进 §VIII 与 `spec_lock.md images`，否则是计划外图片。
- `entrance_wipe` 的方向以预设表为准：自底部写 `direction: "down"`（subtype 4），自左写 `"left"`（subtype 8）；`pptx_animations.py --describe` 的注释说法相反。
- 康哲浅色玻璃 hero 有 84–91% 的高亮像素，旧的“亮像素比例 + 饱和度”过曝判据对它们全部误报，已改为亮度标准差判据（04 IMG-01）。

## 未验证

- PowerPoint 实机播放观感与编辑保存回读：见 `STATUS.md`。
- Windows PowerPoint。
