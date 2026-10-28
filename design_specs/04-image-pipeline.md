# 04 主动生图与版式保护

## 生成是计划中的工序 IMG-01
PPTX 与 HTML-PPT 逐页登记 `asset_id`：封面、目录、章节、尾页各有主题相符的生成主视觉；正文页绑定安静的生成背景，可在章节内复用。开工前先过 IMG-07 的生图能力闸门；用户确认没有生图能力时，改用缺省背景套。不要求每页重画，要求每页有合格映射；同任务已批准的缓存可复用，记录原始回执与哈希。

站点与流式的首页和章节首屏要么有生成主视觉，要么使用全站统一、实际运行的程序化光场（计划写 `global_procedural_optical_field` 并列出运行文件）。普通 CSS 渐变不构成替代。正文深层信息不强制每卡生图。

主视觉交付时把亮度分布写进资产清单的 `review.evidence`。康哲的浅色玻璃画面本来就以高亮像素为主，亮像素比例不能说明主体是否可辨；判据看明暗结构：缩到 `image.washout.sample_px` 长边后的灰度标准差低于 `luminance_std_min`（7），按“主体不可辨”重新构图或调整裁切。`tools/qc_plan.py --asset-root` 对四类 hero 页自动计算并报 `IMAGE-WASHOUT`（2026-10-24 标定：批准的 hero 8.5–12.9，同图叠加 60% 白色后 3.4–5.2）。多画幅裁切以主体为锚，不一律中心裁切。

## 能力发现与隐私 IMG-06
调用当前环境真实可用的生图能力；PPT Master 已有生图 manifest 阶段时，在其阶段加入保护区与审阅合同，不另起并行流程。一项资产只有一个负责环节。

用户指定某个技能或服务生图时，只使用它的生成接口：先读该技能/服务的接口文档与参数说明，再发真实请求；包装脚本没有暴露的参数不等于服务不支持。回执区分请求尺寸与实际尺寸，实际尺寸以解码文件为准。不引入该技能的其他风格或审批规则，生成结果仍守本章与 02。

提示词只含去识别的视觉概念、公开主题和品牌要求；不上传内部方案全文、患者资料或未公开数值。回执只保留必要摘要，不泄露密钥。闸门（IMG-07）选定生图后，接口在制作中途不可用时记 BLOCKED（10 QA-STATUS），可出布局草案但不能标完成；要换成缺省背景套，须告诉用户并改写闸门结论，不得静默换图。CSS 渐变不能顶替“生图通过”。

## 生图能力闸门与缺省背景套 IMG-07（PPTX / HTML-PPT 常规路线）
两条轨道都要求按讲稿主题生成背景（IMG-01、IMG-05）。能不能生图取决于当前环境，所以在开工时确认，不默认沿用参考实现的图。旗舰路线用程序化光效图（14），不过这道闸门；站点与流式可以用程序化光场，也不过。

1. **先检测**，不先提问。逐项核对并记下证据：
   - 宿主技能列表里的生图 skill；
   - 可用的生图类 MCP 工具；
   - ppt-master `image_gen.py` 的后端是否已配置（只看配置项是否存在，不读出、不打印密钥）；
   - 用户在本次任务里点名的服务。
2. **⛔ 询问用户**（阻断，得到回答前不进入资产工序）。把检测结果和推荐写在问题里，选项为：
   - 用检测到的某个 skill 或接口生图（检测到时推荐这一项）；
   - 用户另行指定 skill 或接口；
   - 没有生图能力，用缺省背景套。

   开工时若同时要选路（14 FLAG-01），先选路；选了旗舰就不再问本项。修改已有 deck 时沿用它原来的结论。
3. **登记**：page-plan 写 `image_capability`（`decision`、`provider`、`asked_user: true`、`detected`、可选 `user_answer`）。全套 deck 用同一种方式：
   - `generated` 时各页 `image.mode` 写 `generated`；
   - `default_set` 时各页写 `default_set`。

**选生图时**：
- 照 IMG-01 至 IMG-05 生成与审阅。
- 每条提示词都以同一段风格锚开头，同一套 deck 的光向一致：

  > Style anchor (identical for every image in this deck): Kangzhe light liquid-glass optical material on a near-white field; translucent warm-white glass with soft refraction, thin bright rims and short highlights; colour only as faint refracted light in brand orange #FF9900 and secondary yellow #FFCC00; one soft light source from the upper left; calm, airy, formal medical style. No dark background, no neon, no saturated blue, green or purple, no text, numbers, logos or watermarks.

- 接口支持参考图时，把缺省背景套里同类页面的图作为风格参考传入。IMG-03 第一遍审裸图时，把它和该参考图放在一起比较。
- 检查：
  - `tools/qc_plan.py --asset-root` 计算有色像素中暖色的比例，低于 `image.style.warm_share_min` 报 `IMAGE-STYLE`（WARN）；
  - 登记成生成图的资产若哈希属于缺省背景套，报 `IMAGE-DEFAULT-AS-GENERATED`（失败）。

**用缺省背景套时**：
- 清单在 `assets/backgrounds/default-set.json`：封面、目录、章节、尾页主视觉，加一张正文安静背景。JPEG 格式，PPTX 与 HTML 都能直接用。
- 各页 `image.asset_id` 写清单里的 id，按页型对应：`qc_plan.py` 核对 id 与页型，用错页型报 `IMAGE-DEFAULT-SET`。
- 已知限制照实写进交付说明：
  - 长边 1672，hero 清晰度 WARN；
  - 没有超宽正文背景；
  - 背景与讲稿主题无关。
- 裸图已审过，合成审阅（IMG-03 第二遍、G4-BODY）照做。

## 先布局，再画保护区 IMG-02
先固定页型、字号、卡片与图表的真实几何，再生成 `protected_regions`：页眉、Logo、标题、正文卡、图表绘图区、必要标签、观点、参考行、页脚。每个区域记录 rect、对象 id、用途和外扩：静态外扩 `tokens.image.safety_pad_px`，会运动的对象按扫掠包络外扩 `tokens.image.motion_safety_pad_px`。

三类区域：`clear`（文字、数据、chrome，不能出现主体或高对比边缘）、`quiet`（卡片后的低频柔光）、`subject`（主视觉允许区）。保护区是构图与遮罩合同，不要求背景与卡片零相交；允许低频背景在卡后透出，不允许复杂结构或亮斑穿过笔画。换比例、裁切、移动后重新验证，不复用旧结论。

## 正文背景 IMG-05（PPTX / HTML-PPT）
正文背景与四类 hero 主视觉分开策划和登记。不得把 hero 的玻璃块、环、丝带降透明度后当正文背景。默认是近白阅读区加极少量边缘光影；玻璃的可感知性主要由前景卡与数据外壳提供。

- 中央正文与坐标面保持近白、低频：无可辨认的玻璃轮廓、斜向光带、折射亮线、大片橙黄雾、硬阴影、环或丝带。
- 只在实际可用的边缘空槽放一两处很淡的光影；不沿整条边铺色，不用连续装饰框包围正文。边缘不豁免页眉、Logo、页脚。
- 没有空槽时允许近白的极低频底图，不为“生过图”强塞物象。
- 已通过裸图审阅的正文背景按登记裁切直接显示，不再机械套低 opacity、saturate 或整页白色蒙版；需要局部遮罩时标出区域与理由。

正文提示词模板：

> Generate a quiet near-white optical background for a formal pharmaceutical medical presentation, [actual aspect ratio]. This is a CONTENT SLIDE, not a cover or hero illustration. The foreground will contain editable text, tables and charts. Keep every [actual protected rectangle] uniformly near-white and visually empty. No recognizable objects anywhere in the reading area: no glass panels, rings, ribbons, folds, diagonal rays, caustic lines or large orange/yellow clouds. Only one or two extremely faint warm refraction hints may sit in [actual unused edge slots], with no outline or hard edge. Keep header, logo and footer slots clean even at the edges. No text, logo, chart, border or letterboxing.

hero 提示词要素：本页业务主题的非敏感概括；康哲浅色橙黄光学材料（主色 `colors.brand`、辅色 `colors.secondary`，以白为主）；主物象及其为何服务本页；subject / quiet / clear 区的精确位置；画幅与裁切；一致的光向；不出现文字、数字、图表、水印、仿冒 Logo。不要所有任务都套同一玻璃球、山峰或环形图；不为有图而画新的分子机制、人体解剖或研究流程；患者影像与证据图禁止生成替代。

## 生成后双重审阅 IMG-03
第一遍看裸图：主题、光向、品牌色、无乱码/假 Logo/虚构机制，保护区内无亮边和高频纹理。第二遍看实际合成页：真实字体、裁切、卡片透明度、chrome、悬停和电影关键帧全部参与。只看裸图不算通过。正文背景至少审三种合成：文字最多的卡片页、图表页、表格或甘特页（G4-BODY）。

修复优先级：重新安排 subject 区或重新生成 → 调整裁切 → 与设计一致的局部浅色遮罩。不整页盖白，不把文字移出固定区迁就图。达到重试预算仍不合格就记 BLOCKED。

## 画幅与像素 IMG-04
资产计划按交付视口族列源图比例、保护区和裁切策略（视口矩阵见 13 FOLD-04）。HTML 宽屏应有真实超宽生成背景；可以把一张超宽图的受检裁切用于 16:9，但把 16:9 源图放大裁切到超宽只能记 WARN，不能称为“超宽生图通过”。拉伸、CSS 补边、contain 留白都不合格。

回执记录 `requested_size`（接口无尺寸参数时为 null）、`actual_size` 与每个 rendition 的 `crop=[x,y,w,h]`、`viewport`、`fit=cover`、显示坐标中的 `protected_regions` / `subject_rects`；源图比例误差不超过 `tokens.image.aspect_tolerance`，hero 与正文长边分别不低于 `tokens.image.hero_min_long_edge_px` / `body_min_long_edge_px`，不足时清晰度 WARN 或 BLOCKED。可机读清单以 `schemas/asset-manifest.schema.json` 为准。

同一页面按视口换源图时，用 `image.viewport_assets=[{"viewport":[w,h],"asset_id":…}]` 覆盖列入 `target_viewports` 的精确视口；默认源与覆盖源分别登记、分别审阅。非基准画幅有可辨认主体时补 `image.viewport_regions`，rect 取该视口的真实 DOM 几何。HTML 项目可用 `picture/source` 切换，但须在每个视口核对实际 `currentSrc`、解码尺寸与 SHA。

## 编码与存储
按用途选透明 PNG 或高质量 WebP/JPEG（PPTX 用 PNG/JPEG）。主视觉长边建议 ≥2560px，正文背景 ≥1920px；一般 hero 以 0.3–2MB 为优化目标，单文件 HTML 的 base64 膨胀计入预算。模块化 HTML 用随包相对路径离线可用；PPTX 图片随 ppt-master 项目管理。分享包不夹带含敏感业务数据的提示词。

## 资产回执
每条记录含 `id / origin / file / sha256 / tool_receipt / requested_size / actual_size / renditions / review`（`schemas/asset-manifest.schema.json`）；`origin=generated` 必须有真实调用或已验证缓存回执，`approved_logo` 只用于官方标识，`evidence_original` 只用于原始证据图（不代替 hero 生成要求）。示例包没有执行过的生成不写虚构的 provider 或模型。
