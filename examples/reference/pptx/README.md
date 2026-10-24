# PPTX 导出探针（ppt-master 6.7.3）

**这是转换器级探针，不是 Default 全流程正例。** Default 流程含 ⛔ BLOCKING 用户确认门（Stage 1 沟通合同与模板选择），必须有用户在场；本探针只验证康哲的 SVG 写法经上游真实导出器后，是否落成预期的原生 OOXML。

## 复现

```bash
python3 <ppt-master>/skills/ppt-master/scripts/project_manager.py init kangzhe_probe --format ppt169
python examples/reference/pptx/build_svg.py <project> --images <含 cover.png body-quiet.png logo.png 的目录>
python3 <ppt-master>/skills/ppt-master/scripts/svg_quality_checker.py <project> --canonical-authoring --stage final --quick-generate --json
python3 <ppt-master>/skills/ppt-master/scripts/animation_config.py validate <project>
python3 <ppt-master>/skills/ppt-master/scripts/svg_to_pptx.py <project> --quick-generate --no-notes --animation-config animations.json -o <project>/exports/kangzhe_probe.pptx
python tools/bind_header_mark_pptx.py <exported>.pptx kangzhe_probe.pptx header-mark-plan.json --receipt header-mark-binding.json
python3 <ppt-master>/skills/ppt-master/scripts/pptx_delivery_check.py kangzhe_probe.pptx
```

上游版本：hugohe3/ppt-master `523e5bd972f94c3cac8742fec0d54d43824a17bb`（`v6.7.3-2-g523e5bd`，v6.7.3 之后两个往返修复提交）。`logo.png` 由 `assets/logo_bot.svg` 原样渲染为透明 PNG（10×，未重绘），因为导出器不做内容级 SVG 图片映射。

## 实测结果（2026-10-23 首测，2026-10-24 复测）

| 检查 | 结果 |
|---|---|
| `svg_quality_checker` | 4 页 0 阻断（仅格式规范化与文字框 ≤5% 的告警）；首轮发现 `brand_fragments` 的路径缺稳定 id，已修 |
| 玻璃卡 | 渐变三停 alpha 62/55/50% 原生保留；外阴影 blur 152400、dist 57150、dir 90°、alpha 9%（作者值 0.12 × 0.75） |
| 文字 | 主题字体 latin Arial / ea Microsoft YaHei；`• ` 前缀转为原生 `a:buChar` 加悬挂缩进 |
| 入场 | 研究范围 4 组 Fade（presetID 10），随上一项，delay 0/70/140/410 ms（三组卡片 n × 70，观点句 3 × 70 + `takeaway_gap` 200），时长 520 ms，decel 70%；7.0.1 起封面三行 0/70/140、第一张流程页载体 0 与步骤条 70 |
| hero Logo | 2026-10-24 复测：Logo 改用 `meet` 后不再有 `srcRect` 裁切（首测为左右各 0.413%） |
| Morph | 第 3→4 页同名 `!!kz-carrier`，`p159:morph byObject`，0.8 s |
| 双菱形 | 导出后用批准的原生对象替换 3 页 × 4 形状；替换后动画与 Morph 名称完好 |
| `pptx_delivery_check` | 绑定前后均 0 errors / 0 advisories |

## 未验证

- PowerPoint 实机渲染、Morph 观感、编辑保存回读：本次 AppleScript 驱动 PowerPoint 时 AppleEvent 超时，系统可能在等待自动化授权，需要用户在场处理。
- Windows PowerPoint、LibreOffice。
- 原生图表/表格（本探针没有数据对象）。
