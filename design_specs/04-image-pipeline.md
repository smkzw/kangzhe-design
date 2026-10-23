# 04 主动生图与版式保护

## 生成是计划中的工序 IMG-01
PPTX 与 HTML-PPT 逐页登记 `asset_id`：封面、目录、章节、结束页各有主题相符的生成主视觉；正文页绑定安静的生成背景，可在章节内复用。不要求每页重画，要求每页有合格映射；同任务已批准的缓存可复用，记录原始回执与哈希。

站点与流式的首页和章节首屏要么有生成主视觉，要么使用全站统一、实际运行的程序化光场（计划写 `global_procedural_optical_field` 并列出运行文件）。普通 CSS 渐变不构成替代。正文深层信息不强制每卡生图。

主视觉交付时把平均饱和度与亮度分布写进资产清单的 `review.evidence`：超过 70% 像素落在最亮的 1/16 区间且平均饱和度 <5%，按“主体不可辨”重新构图或调整裁切。多画幅裁切以主体为锚，不一律中心裁切。

## 能力发现与隐私 IMG-06
调用当前环境真实可用的生图能力；PPT Master 已有生图 manifest 阶段时，在其阶段加入保护区与审阅合同，不另起并行流程。一项资产只有一个 owner。

用户指定某个技能或服务生图时，只使用它的生成接口：先读该技能/服务的接口文档与参数说明，再发真实请求；包装脚本没有暴露的参数不等于服务不支持。回执区分请求尺寸与实际尺寸，实际尺寸以解码文件为准。不引入该技能的其他风格或审批规则，生成结果仍守本章与 02。

提示词只含去识别的视觉概念、公开主题和品牌要求；不上传内部方案全文、患者资料或未公开数值。回执只保留必要摘要，不泄露密钥。工具不可用时任务为 blocked，可出布局草案但不能标完成，CSS 渐变不能顶替“生图通过”。

## 先布局，再画保护区 IMG-02
先固定页型、字号、卡片与图表的真实几何，再生成 `protected_regions`：页眉、Logo、标题、正文卡、图表绘图区、必要标签、观点、参考行、页脚。每个区域记录 rect、对象 id、用途和外扩：静态外扩 `tokens.image.safety_pad_px`，会运动的对象按扫掠包络外扩 `tokens.image.motion_safety_pad_px`。

三类区域：`clear`（文字、数据、chrome，不能出现主体或高对比边缘）、`quiet`（卡片后的低频柔光）、`subject`（主视觉允许区）。保护区是构图与遮罩合同，不要求背景与卡片零相交；允许低频背景在卡后透出，不允许复杂结构或亮斑穿过笔画。换比例、裁切、移动后重新验证，不复用旧结论。

## 正文背景 IMG-05（PPTX / HTML-PPT）
正文背景与四类 hero 主视觉分开策划和登记。不得把 hero 的玻璃块、环、丝带降透明度后当正文背景。默认是近白阅读区加极少量边缘光影；玻璃的可感知性主要由前景卡与数据外壳提供。

- 中央正文与坐标面保持近白、低频：无可辨认的玻璃轮廓、斜向光带、折射亮线、大片橙黄雾、硬阴影、环或丝带。
- 只在实际可用的边缘空槽放一两处很淡的光影；不沿整条边铺色，不用连续装饰框包围正文。边缘不豁免页眉、Logo、页脚。
- 没有空槽时允许近白的极低频底图，不为“生过图”强塞物象。
- 已通过裸图审阅的正文背景按登记裁切直接显示，不再机械套低 opacity、saturate 或整页白 scrim；需要局部遮罩时标出区域与理由。

正文提示词模板：

> Generate a quiet near-white optical background for a formal pharmaceutical medical presentation, [actual aspect ratio]. This is a CONTENT SLIDE, not a cover or hero illustration. The foreground will contain editable text, tables and charts. Keep every [actual protected rectangle] uniformly near-white and visually empty. No recognizable objects anywhere in the reading area: no glass panels, rings, ribbons, folds, diagonal rays, caustic lines or large orange/yellow clouds. Only one or two extremely faint warm refraction hints may sit in [actual unused edge slots], with no outline or hard edge. Keep header, logo and footer slots clean even at the edges. No text, logo, chart, border or letterboxing.

hero 提示词要素：本页业务主题的非敏感概括；康哲浅色橙黄光学材料（主色 `colors.brand`、辅色 `colors.secondary`，以白为主）；主物象及其为何服务本页；subject / quiet / clear 区的精确位置；画幅与裁切；一致的光向；不出现文字、数字、图表、水印、仿冒 Logo。不要所有任务都套同一玻璃球、山峰或环形图；不为有图而画新的分子机制、人体解剖或研究流程；患者影像与证据图禁止生成替代。

## 生成后双重审阅 IMG-03
第一遍看裸图：主题、光向、品牌色、无乱码/假 Logo/虚构机制，保护区内无亮边和高频纹理。第二遍看实际合成页：真实字体、裁切、卡片透明度、chrome、悬停和电影关键帧全部参与。只看裸图不算通过。正文背景至少审三种合成：文字最多的卡片页、图表页、表格或甘特页（G4-BODY）。

修复优先级：重新安排 subject 区或重新生成 → 调整裁切 → 与设计一致的局部浅色遮罩。不整页盖白，不把文字移出固定区迁就图。达到重试预算仍不合格就写 blocked。

## 画幅与像素 IMG-04
资产计划按交付视口族列源图比例、保护区和裁切策略（视口矩阵见 13 FOLD-04）。HTML 宽屏应有真实超宽生成背景；可以把一张超宽图的受检裁切用于 16:9，但把 16:9 源图放大裁切到超宽只能记 WARN，不能称为“超宽生图通过”。拉伸、CSS 补边、contain 留白都不合格。

回执记录 `requested_size`（接口无尺寸参数时为 null）、`actual_size` 与每个 rendition 的 `crop=[x,y,w,h]`、`viewport`、`fit=cover`、显示坐标中的 `protected_regions` / `subject_rects`；源图比例误差不超过 `tokens.image.aspect_tolerance`，hero 与正文长边分别不低于 `tokens.image.hero_min_long_edge_px` / `body_min_long_edge_px`，不足时清晰度 WARN 或 BLOCKED。可机读清单以 `schemas/asset-manifest.schema.json` 为准。

同一页面按视口换源图时，用 `image.viewport_assets=[{"viewport":[w,h],"asset_id":…}]` 覆盖列入 `target_viewports` 的精确视口；默认源与覆盖源分别登记、分别审阅。非基准画幅有可辨认主体时补 `image.viewport_regions`，rect 取该视口的真实 DOM 几何。HTML 项目可用 `picture/source` 切换，但须在每个视口核对实际 `currentSrc`、解码尺寸与 SHA。

## 编码与存储
按用途选透明 PNG 或高质量 WebP/JPEG（PPTX 用 PNG/JPEG）。主视觉长边建议 ≥2560px，正文背景 ≥1920px；一般 hero 以 0.3–2MB 为优化目标，单文件 HTML 的 base64 膨胀计入预算。模块化 HTML 用随包相对路径离线可用；PPTX 图片随 ppt-master 项目管理。分享包不夹带含敏感业务数据的提示词。

## 资产回执
每条记录含 `id / origin / file / sha256 / tool_receipt / requested_size / actual_size / renditions / review`（`schemas/asset-manifest.schema.json`）；`origin=generated` 必须有真实调用或已验证缓存回执，`approved_logo` 只用于官方标识，`evidence_original` 只用于原始证据图（不代替 hero 生成要求）。示例包没有执行过的生成不写虚构的 provider 或模型。
