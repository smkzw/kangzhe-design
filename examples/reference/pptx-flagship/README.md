# PPTX 旗舰参考实现（14 FLAG-10，F1）

与 HTML 旗舰正例（`../htmlppt-flagship/`）同一份合成素材，共 8 页：封面、目录、章节、并列卡（flag-cols）、六步流程（flag-flow）、原生柱图（flag-chart）、甘特（flag-gantt）、谢谢。`build_svg.py` 把页面写入 ppt-master 项目，检查与导出都由 ppt-master 完成：

```
PM=~/.claude/skills/ppt-master
python3 examples/reference/pptx-flagship/build_svg.py <项目>
python3 $PM/scripts/stamp_native_fallbacks.py <项目>/svg_output/06_gaps.svg --write
python3 $PM/scripts/svg_quality_checker.py <项目> --canonical-authoring --stage final --quick-generate --json
python3 $PM/scripts/svg_to_pptx.py <项目> --quick-generate --no-notes --native-charts-and-tables --animation-config <项目>/animations.json -o kangzhe_flagship.pptx
python3 $PM/scripts/pptx_delivery_check.py kangzhe_flagship.pptx
python3 examples/reference/pptx-flagship/readback.py kangzhe_flagship.pptx
python3 tools/check_kz_project.py <项目> --plan <项目>/page-plan.json --pptx kangzhe_flagship.pptx
```

## 做法

- **背景**：只用旗舰背景组的两张图。封面用 `assets/backgrounds/flagship/cover.jpg`（右侧液态丝带，左侧留白放标题），其余页用 `canvas.jpg`（暖白底，角部淡光）。正文页背景不放主视觉，保证卡片和文字落在安静底上（FLAG-03）。
- **页面框架**（FLAG-04）：正文页左上是棱面图标块（斜切橙色棱面里放白色章节图标，旁伴小黄棱面）＋完整 kicker＋标题，右上是 Logo 与两枚信息胶囊，底部是分段进度条、页脚和页码，全部为原生对象；封面、目录、章节和谢谢页只在左上放 Logo，封面右侧不放大图标块。
- **卡片**（FLAG-05）：白色纸卡，单个原生外阴影（不透明度 22.5%），圆角来自 tokens；不画任何通长色条。并列卡内的行组共用行高，上限 62，卡内文字少时按行组撑开，不把文字堆在卡片上沿。
- **图表与甘特**：资料完整性页是原生柱图（应收 slate、已收 orange，可在 PowerPoint 里编辑）；核对计划页的甘特是原生形状，按季度模型 [start, end) 画，条形颜色按部门。
- **动效**（FLAG-06、06 MOTION-07）：场次与 HTML 旗舰一致。第 0 场随页面自动入场；之后每一场由一次单击开始，同场内按 `pptx_card` 间隔错峰。柱图自底部擦入，页面转场为 0.4 s 淡入淡出。
- **文字**：按 `tools/kz_layouts/text.py` 的微软雅黑字宽排行，放不下时直接报错，不缩字（03 TYPE-03）。
