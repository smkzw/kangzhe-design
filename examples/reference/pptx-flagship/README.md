# PPTX 旗舰路线探针（14 FLAG-10）

与 HTML 旗舰正例同一素材，共 5 页：封面、目录、章节、资料完整性（原生柱图）、决定事项。由 `build_svg.py` 写入 ppt-master 项目，导出与检查都由 ppt-master 完成：

```
python3 examples/reference/pptx-flagship/build_svg.py <ppt-master 项目目录>
python3 <ppt-master>/scripts/stamp_native_fallbacks.py <项目>/svg_output/04_data.svg --write
python3 <ppt-master>/scripts/svg_quality_checker.py <项目> --canonical-authoring --stage final --quick-generate --json
python3 <ppt-master>/scripts/svg_to_pptx.py <项目> --quick-generate --no-notes --native-charts-and-tables --animation-config <项目>/animations.json -o kangzhe_flagship.pptx
```

## 做法

- **背景**：每页背景是 `tools/flagship_plate.py` 渲染的 2560×1440 光效图，与 HTML 光场共用同一套 tokens。参数见 `build_svg.py` 的 `PLATES`，SHA-256 登记在 `plates.json` 与 `page-plan.json`（`route: flagship`）。内容页渲染时传入标题、纸卡和说明三块阅读区以及聚光圆，所以图上阅读区本身就是安静的。
- **玻璃**：PowerPoint 不能模糊或折射形状背后的内容，所以每块玻璃分两层。下层是 `tools/flagship_plate.py` 的 `lens()` 从同页光效图烘焙的透镜图（`images/pNN-*-lens*.png`）：阅读区磨砂、降饱和、提亮，边缘环带折射，参数与 HTML 透镜滤镜相同。上层是原生玻璃壳：渐变面、白色细边和单个外阴影。两层都是原生对象，移动卡片时要一起移动。章节号透镜放在数字下层，用通透面。
- **数字字体**：超细数字改用常规字重的 Arial，因为 PowerPoint 没有可移植的细体中文或数字字体。
- **身份胶囊**：原生圆角矩形，内放官方 Logo PNG 与部门名，按页型放在四个角，代替正文页 chrome；不绑定双菱形。
- **动效**：淡入错峰 `pptx_card` 180ms，柱图自底部擦入，页面转场为淡入淡出（06 MOTION-07）。

## 本次验证（2026-10-24，7.1.1 磨砂玻璃）

| 项目 | 结果 |
|---|---|
| 计划预检 | `qc_plan.py page-plan.json --asset-root <项目>/images`：0 错误，光效图哈希一致 |
| ppt-master 检查与导出 | 检查器 0 错误；交付检查 0/0（`delivery-check.json`） |
| OOXML 回读 | `ooxml-readback.json`：封面 0/180/360/540/720/900；目录 0/180/360/540；章节 0/180/360；资料完整性 0、180、柱图擦入（presetSubtype 4）360、540、720；结尾 0/180/360 |
| PowerPoint（macOS 16.114） | 打开、另存 PDF 逐页查看：13 张透镜图都垫在玻璃壳下，阅读区为乳白磨砂，边缘可见折射厚边；版面正常。加文本框后保存、重开，图片对象、动效时序与原生柱图保持不变 |

## 未覆盖

- 实际放映的观感未看。
- Windows PowerPoint 未测。
- 讲稿未写入，因为探针用 `--no-notes` 导出；正式交付按 09 写讲稿。
