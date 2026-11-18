# PPTX 导出探针（ppt-master）

转换器级探针，不是 Default 全流程正例（全流程见 `../pptx-default/`）。它只回答一个问题：康哲的 SVG 写法经 ppt-master 真实导出器后，是否落成预期的原生 OOXML。Default 流程有必须由用户在场确认的门，探针绕开规划阶段，直接从 SVG 导出。

## 复现

```bash
PM=<ppt-master>/skills/ppt-master
python3 $PM/scripts/project_manager.py init kangzhe_probe --format ppt169
python3 examples/reference/pptx/build_svg.py <project> --images <含 cover.png、body-quiet.png、logo.png 的目录>
python3 $PM/scripts/svg_quality_checker.py <project> --canonical-authoring --stage final --quick-generate --json
python3 $PM/scripts/animation_config.py validate <project>
python3 $PM/scripts/svg_to_pptx.py <project> --quick-generate --no-notes --animation-config animations.json -o <project>/exports/kangzhe_probe.pptx
python3 tools/bind_header_mark_pptx.py <exported>.pptx kangzhe_probe.pptx header-mark-plan.json --receipt header-mark-binding.json
python3 $PM/scripts/pptx_delivery_check.py kangzhe_probe.pptx
```

`logo.png` 由 `assets/logo_bot.svg` 原样渲染为透明 PNG（10×，不重绘），因为导出器不做内容级 SVG 图片映射。核对的上游版本见 `adapters/ppt-master.md`。

## 康哲写法落到 OOXML 的结果

| 写法 | 导出后 |
|---|---|
| 玻璃卡三停渐变 | 原生渐变，三停 alpha 保留 |
| 卡片阴影 | 单个原生外阴影（blur、距离、方向、透明度来自 tokens） |
| 文字 | 主题字体 latin Arial / ea Microsoft YaHei；`• ` 前缀转成原生项目符号与悬挂缩进 |
| 入场 | Fade（presetID 10），随上一项，按 `stagger_ms.pptx_card` 错峰，观点句再隔 `takeaway_gap` |
| hero Logo | `preserveAspectRatio="xMidYMid meet"`，不产生裁切 |
| Morph | 第 3→4 页同名 `!!kz-carrier`，按对象 Morph |
| 双菱形 | 导出后用批准的原生形状替换；替换后动画与 Morph 名称不变 |
