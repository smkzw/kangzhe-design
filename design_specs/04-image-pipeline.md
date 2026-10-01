# 04 主动生图与版式保护

## 生成是计划中的工序，不是可选灵感
IMG-01：PPTX 和 HTML-PPT 逐页记录 `asset_id`。封面、目录、章节、结束页各自要有主题相符的已生成主视觉；正文页要绑定安静的生成背景，可在同一章节复用。**不要求每页重画一张**，要求每页都有合格映射，不把图片任务无限放大。已批准的同任务缓存可以复用，记录原始调用回执与哈希。

站点及流式每个独立页面/章节首屏有生成主视觉，或使用全站统一的实际程序化光学场景。豁免必须在计划写 `global_procedural_optical_field`、列出运行文件与全站一致性证据。只有静态渐变/圆点/空光斑不构成完整替代；仍须有主题相关的连续信息电影。正文深层信息不强制每张卡生图。

## 能力发现与隐私
调用当前环境真实可用的生图工具/技能，由上游生图路由执行；不硬编码不存在的个人绝对路径或特定模型。PPT Master 已有生图 manifest/执行阶段时，在其阶段加入保护区和审阅合同，**不另起并行生图流程**。一项资产只有一个 owner。

用户指定仅使用某个技能的生图能力时，只读取其真实接口、认证方式和返回格式，不引入该技能其他风格、配色、文字或审批规则。本轮指定 `gpt-image-2-sci-draw` 的生成能力：在环境中发现其 SKILL.md、scripts/gen_image.py 及接口文档后调用，结果仍遵守本章 Liquid Glass、保护区及真实尺寸要求。包装脚本未暴露参数不等于服务不支持；继续核服务 API 文档、实际模型目录及该模型的上游参数文档。本轮 API-REF.md 明确支持 `customConfig`，以 `size:2560x1088, quality:high` 的真实请求取得相同原像素尺寸。此事实只绑定该次原回执及资产，不能推断其他请求或后台权重版本。将返回资产和原始回执回填既有引擎资产清单，继续原引擎导出，不以另一个生图后端替代 ppt-master 或 html-ppt-skill。只有核查这些接口仍无尺寸能力时才记录 null 与提示请求尺寸；不猜参数、不把业务路由编号当成已证实的模型版本。

传给外部图像服务的提示词仅含去识别的视觉概念、公开主题和品牌要求；未经授权不上传内部方案全文、患者资料或未公开研究数值。需要参考图时区分版权/隐私授权。输出里只保留必要回执摘要，不泄露访问密钥。工具不可用：任务为 blocked/pending，允许出布局草案但不能标正式完成；不得让几行 CSS 渐变获得“生图通过”。

## 先布局，再画保护区 IMG-02
每页先固定页型、字号、卡片与图表的真实几何。生成 `protected_regions`：页眉、Logo、标题、正文卡、图表绘图区、必要标签、观点、参考行、页脚。每个区域记录 rect、对象 id、用途、扩张 padding。静态默认外扩 16px；可能运动的元素使用扫掠包围盒并外扩 24px。不能只保护文字点位而忽略运行中卡片位移。

建立三种区域：
- `clear`：标题、Logo、页眉页脚、正文文字和数据面，不能出现语义主体或高对比边缘。
- `quiet`：卡片背后的局部光场，仅低频、低对比、柔和色散。
- `subject`：主视觉允许区，主题物象、玻璃构造与空间关系集中于此。

保护区是 **构图和遮罩合同**，不是要求整张背景在几何上与卡片零相交。允许低频背景在卡后透出；不允许复杂结构或亮斑穿过文字笔画。图像换比例、裁切、移动后必须重新验证映射，不能复用旧 pass。

## 提示词模板
### 正文页专用构图 IMG-05（PPTX / HTML-PPT）
正文背景与封面、目录、章节、结束页主视觉必须分开策划和登记。不得把 hero 的玻璃块、玻璃环、丝带或光束降透明度后当正文背景。正文默认采用 **近白阅读区＋极少量边缘光影**，Liquid Glass 的可感知材质主要由前景原生卡片和数据外壳提供。

先依据实际 protected_regions 确定可用边缘空槽；可见暖色光影只落在这些空槽，不横穿正文。边缘位置不自动豁免页眉、Logo 或页脚保护。没有空槽时，允许生成近白的极低频光学底图，不为证明“生过图”强塞物象。

- 中央正文、全部文字和图表坐标面保持近白、低频；不得出现可辨认的玻璃轮廓、斜向光带、折射亮线、大片橙黄色雾、硬阴影、环或丝带。玻璃轮廓即使很浅，仍须核对它是否穿过字形、曲线或刻度；不能只靠低透明度放行。
- 仅在可用边缘空槽放一处或两处很淡的局部光影。不得沿一整条边铺色、形成通长色带或用连续装饰框包围正文。业务主题通过整套主视觉和前景信息表达，正文背景不再重复画流程、数据或结构。
- 在中间阅读区优先减去背景结构，不靠增加玻璃层数补救。背景无冲突是前景卡片透明度选择的前提；仍有冲突则退回重新生成/构图，不提高模糊强度掩盖。

正文提示词从下面的专用模板出发；后面的通用 subject 模板主要用于 hero，不得无差别用于正文：

“Generate a quiet near-white optical background for a formal pharmaceutical medical presentation, [actual aspect ratio]. This is a CONTENT SLIDE, not a cover or hero illustration. The foreground will contain editable text, tables and charts. Keep every [actual protected rectangle] uniformly near-white and visually empty. No recognizable objects anywhere in the reading area: no glass panels, rings, ribbons, folds, diagonal rays, caustic lines or large orange/yellow clouds. Only one or two extremely faint warm refraction hints may sit in [actual unused edge slots], with no outline or hard edge. Keep header, logo and footer slots clean even at the edges. Liquid Glass depth is expressed by foreground cards, not by detailed background geometry. No text, logo, chart, border or letterboxing.”

提示词应包含：本页业务主题的非敏感概括；康哲浅色橙黄光学材料；主物象及它为何服务本页；精确 subject / quiet / clear 区位置；预期画幅和裁切；光向一致；不可出现的内容。示例（只作模板，不是已生成资产）：

“Create a refined light Liquid Glass environment for a formal medical research presentation. Main accent #FF9900, secondary #FFCC00, predominantly white. Theme: [specific non-confidential concept]. Place [subject] only inside [normalized rectangles]. Keep [protected rectangles] clear and low-frequency; no bright edges crossing those zones. One coherent soft light direction, translucent rounded forms, restrained optical depth. No rendered text, numbers, labels, charts, watermarks or imitation corporate logos. The image is decoration, not scientific evidence.”

禁止所有任务一律套同一玻璃球/山峰/环形图。不能为了有图而制造新的分子机制、人体解剖或研究流程。科学示意图需要独立专家审阅和真实依据；患者影像与证据图禁止生成替代。

## 生成后双重审阅 IMG-03
第一遍看 **裸图**：主题匹配、光向、品牌色、无乱码/假 Logo/不实机制；保护区内是否有亮边、轮廓和高频纹理。第二遍看 **实际合成页**：实际字体、图片裁切、卡片透明度、页眉页脚、hover/电影关键帧全部参与。只看裸图不算通过。

目录等hero须保护整个阅读卡壳及浮动扫掠区，不能只核标题文字框。封面通过的裁切位置不自动适用于目录、章节或尾页；允许按页型登记不同背景位置，把物象移入实际空槽，再逐交付视口复核。不得移动固定标题、缩小卡片文字或擦白主视觉来迁就背景。

机器检查：尺寸/MIME/哈希/本地可读取；布局区域坐标；遮罩和裁切是否登记；对比度的代表性最差样本；protected-region 内边缘密度和局部亮度波动可作筛查，不能当成语义审阅替代。VLM 先看完整页，再看问题局部；不要只给图像或只给很小 contact sheet。拒绝项标注 asset id、页号、区域、截图和修改建议。

正文合成审阅另须覆盖：文字最多的卡片页、无卡/有玻璃壳的图表页、表格或甘特页。检查背景与前景的主次、实际最小字号、浅灰刻度与网格线、强调红字、正文卡在未 hover 与 hover 时的可读性。复用一张正文图不代表三个阅读用途自动通过；任一用途出现背景轮廓与字形/数据混读，即该用途失败。先审原始图，再审每种实际裁切后的合成；截图须保留真实前景，不能仅给空白模板。

近白是正文阅读区的要求，不是“所有页全部看不见生图”的目标。已为正文生成并通过裸图审阅的低频背景，默认按登记裁切直接显示；不要再机械套低opacity、saturate或白scrim把唯一边缘光影擦掉。若需要局部遮罩，标出影响区域、理由及实际合成证据，不能用整页擦白替代重新策划保护区。无可用边缘空槽时近白源仍允许，必须在计划写具体几何原因；此时前景玻璃材质仍须通过02 LG-04，不能连卡片也退成白扁卡。封面/目录/章节/结束页的主题主视觉依其独立合同必须可见。

修复优先：重新安排 subject 区/重新生成 → 调整裁切 → 与设计一致的局部浅色遮罩。不得靠整页盖 94% 白色把所有生图都擦掉，也不得把文字移到固定页眉之外迁就图。达到重试预算后写阻塞，不偷换成假图通过。

## 编码与存储
根据实际用途选择透明 PNG 或高质量 WebP/JPEG；不硬锁某个编码质量数。主视觉长边建议至少 2560px，正文背景至少 1920px，检查实际渲染而非盲目追求 8K。大图可共享引用和内容寻址缓存；不再采用单 PNG 150KB、整套 800KB 这类不现实硬门。一般 hero 可先以 0.3–2MB 作为优化目标，清晰度优先，记录总载荷；单文件 HTML 的 base64 膨胀也计入预算。

模块化 HTML 采用随包相对路径，离线可用；单文件交付才内联，且由同源构建产生。PPTX 图像随官方 workspace 管理，不能引用个人临时目录或远程图片。不得在分享包中夹带提示词里的敏感业务数据。

## 资产回执
每条记录含 `asset_id / image_role / generation_required / origin / tool / model_if_returned / receipt / file / sha256 / pages / protected_regions / crop / preflight_status / composite_review_status`。`origin=generated` 必须有真实调用或已验证缓存回执；`origin=procedural` 仅站点/流式豁免；`origin=source_original` 仅原始证据，不代替 hero 生成要求。示例包没有执行过的生成不要写虚假 provider/model。

## IMG-04 画幅与实际像素
资产计划先按目标轨道列交付viewport族（16:9、21:9/实际ultrawide；仅合同明确要求移动阅读时加入移动端），每族给源图目标比例、protected_regions和裁切策略。站点式 HTML 不设手机/窄屏资产任务。HTML宽屏必须有真实超宽生成背景，不能只有16:9源图用contain后两侧空白。可复用同一超宽图的受检裁切用于16:9，但每种裁切重新做裸图映射与合成QC；不得把拉伸、CSS补边或放大重采样称为超宽生图成功。

回执区分requested_size、actual_size与有效显示尺寸；宽幅源图比例误差默认不超过tokens.image.aspect_tolerance。工具无尺寸参数时只把提示尺寸当请求，不当成功事实。正文长边与hero长边分别按tokens检查；超宽比例合格不代表分辨率合格。低分辨率可供开发检查，正式清晰度项保持WARN/BLOCKED。保护区域按实际裁切变换，不沿用旧16:9 mask。

A04 可机读清单以 schemas/asset-manifest.schema.json 为准。generated 资产必须记录 requested_size（接口未提供尺寸参数时为 null）、actual_size、renditions；每个 rendition 用源图像素 crop=[x,y,w,h]、viewport=[w,h]、fit=cover、裁切后显示像素坐标中的 protected_regions/subject_rects 和审阅证据。实际尺寸由文件解码核验，不能由提示词推断。预检只能确认几何/像素/回执字段存在，回执真实性及亮边与文字冲突仍由实际工具日志和图像审阅判定；无 asset_root 时不能取得图像实证通过。

页面计划的 target_viewports 必填，列出本次交付的实际视口；站点矩阵以 tokens.site_viewports 为准，HTML轨必须包含超宽视口。每页映射的生成资产必须覆盖这些视口的 rendition，不能只提交一张16:9合成图却宣称宽屏通过。计划画布和实际裁切后视口的保护区、主体框均须为正尺寸且不越界；透明背景空框不作为保护区证据。

### 按视口选择真实源图
同一页面使用不同画幅的真实资产时，`image.asset_id` 是默认源；可添加 `image.viewport_assets=[{"viewport":[2560,1080],"asset_id":"hero-ultrawide"}]` 对已列入 `target_viewports` 的精确视口覆盖。默认源与覆盖源分别在资产清单登记其真实文件/尺寸/调用回执及实际使用的renditions，不把两张图拼成一个假哈希，不将16:9源的crop冒称21:9生成。每个交付视口只有一个有效源；重复/合同外视口、缺失覆盖源、未审原图和错误像素仍失败。

这只是登记和预检接口，不接管HTML的responsive图片选择。项目可用同一主题的`picture/source`按画幅切换；在每个目标视口核对真实`currentSrc`、解码尺寸、对应asset SHA与crop，再看完整合成保护区。不能因默认图通过就放行替换图，静态导出与普通观众源都须绑定实际选择。一个生成源覆盖全部视口仍可只用asset_id，旧有效计划不必迁移。

默认回退源即使在列出的视口中未被选中，也须真实登记并通过裸图/合成、尺寸/哈希检查；它仍随产品交付，不得作为坏图后门。generated模式必须有非空asset_id。

有可辨认主体的非基准画幅须补 `image.viewport_regions=[{"viewport":[2560,1080],"protected_regions":[{"id":"page-title","role":"title","rect":[84,36,1378.5,66],"motion_margin":16}]}]`，其中rect为该视口实际显示像素，示例必须替换为本页真实DOM几何；列表覆盖基准保护区全部对象id，不猜fluid横坐标伸缩。基准视口直接核页面protected_regions，清单里删空保护区不能绕过。预检另核资产rendition声明的保护区并加安全外扩；PPT安全量按同一高度单位换算，站点/流式保持屏幕px，运动margin按规则登记。viewport_regions来自真实渲染，JSON本身无法证明作者登记值是真实DOM，仍须实际合成/轨迹复核。近白无可辨认主体的正文源无需人为制造subject框，但可见亮边/纹理冲突仍由IMG-05实物审阅拒绝。
