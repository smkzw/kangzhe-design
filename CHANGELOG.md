# 7.0.0 · 2026-10-24

## KZ7-1024-B03 · 安装实测与 ppt-master Default 全流程正例
把三套技能装进 `~/.claude/skills`，以用户视角跑通 ppt-master 6.7.3 的 Default Generate 路由（两次确认页、Design Spec/lock、手写 SVG、最终检查、verify-charts、备注、动效、原生图表导出、品牌绑定、交付检查、OOXML 回读），并在 PowerPoint 中打开交付文件。流程中暴露的问题逐条修复。

安装包
- 新增 `requirements.txt`（jsonschema、Pillow）与随包的 `STATUS.md`（当前验证状态；`review/` 不随包发布，原指向失效）。
- SKILL.md 的命令改为 `python3 "$KZ_DIR/tools/…"`，不依赖当前目录（宿主常没有 `python` 命令）。
- 新增 `assets/logo_bot.png`：官方 SVG 原样渲染的 10× 透明 PNG，哈希登记在 `tokens.logo.png_sha256`；ppt-master 不做 SVG 图片映射，agent 不必各自栅格化（01 CORE-02）。
- INSTALL.md 改写为面向任意读 `SKILL.md` 目录的宿主，并列出两个引擎的安装与核对版本。
- 安装包不再包含 `.pptx` 样例成品（改作 Release 附件），包体 4.1MB → 2.2MB。

PPTX 轨
- 新增 `examples/reference/pptx-default/`：Default 全流程正例（素材、Design Spec、执行锁、page-plan、资产清单、6 页手写 SVG、动效、备注、绑定回执、交付检查与 OOXML 回读）；tracks-pptx 与 context_pack 指向它。
- `hero_layout.svg_fragment`：目录页 page role 写成 `toc`（原为 `content`）；每张目录卡的卡面与编号、标题、说明合为一个根组，成为一个编辑与动画单元。
- `bind_hero_pptx.py` 直接读 page-plan：页码取 `slide` 字段或页面 id 中的第一个整数（原只接受 `1_cover` 形式）。实测 6.7.3 导出会把 hero 文字框收缩到内容大小（封面标题 538×86），超出 HERO-04 容差，四类 hero 页因此需要绑定；绑定后偏差 0。
- 06 MOTION-07 / adapter：`entrance_wipe` 方向以预设表为准，自底部写 `"down"`（presetSubtype 4），自左 `"left"`（8）；`pptx_animations.py --describe` 的注释说法相反。Default 自动读取项目根 `animations.json`。
- adapter 新增“Default 路由里的康哲输入”：Stage 2 确认页会按正文基准重算角色字号，康哲字号要在页面上固定并核对 `result.json`；Logo PNG 与所有位图登记 §VIII 与执行锁；页面 SVG 由主 agent 手写；本机反向 DNS 慢时确认页与预览改用前台进程。

图像
- `IMAGE-WASHOUT` 改用亮度标准差（`image.washout.luminance_std_min` 7）：康哲浅色玻璃 hero 本来就有 84–91% 高亮像素，B02 的“亮像素比例 + 饱和度”判据对批准过的三张 hero 全部误报。标定：批准 hero 8.5–12.9，同图叠加 60% 白色后 3.4–5.2。

## KZ7-1024-B02 · 两路独立审阅后的修订
代码审阅（runtime 与工具）和规范审阅（自洽、可执行性、中文）各自只读完成，确认的问题逐条修复并复测。

运行时
- 下钻：`snapshot().width` 改用布局宽度，展开动画期间也是最终宽度；`close()` 返回原生关闭并还焦点后兑现的 promise；展开中途关闭时反向折回，不先跳回全尺寸；只有从卡片（`.kz-card` / `data-kz-drill-source`）触发才做共享元素展开，独立按钮或缺省触发时原地打开。
- 电影：`storyboard()` 返回 `staticProgress`（信息最多的状态停留段中点，可用 `staticState` 指定），参考接线传给 Film，静态帧不再落在移动段或文字淡出窗口里；`phaseAt` 改由同一采样器推导，状态条不会先于载体文字切换；停留时长参数进 `motion.film.storyboard`。
- 入场：观点句（`.kz-takeaway-card` / `data-kz-takeaway`）最后出现，多隔 `stagger_ms.takeaway_gap`，与 PPTX 回读的 0/70/140/410ms 一致；卡标题用 `distance_px.title` / `duration_ms.title`；表格逐行进入级联；站点章节转场用 `duration_ms.section`。
- `mountSections`：单个段落出错不再让同批段落永久隐藏；打印样式兜底显示待入场段落。
- 新增 `KZMotion.fitFold`：`.kz-detail-tall` 按文档倒序收起，直到首屏放得下。实测 1920×1080 首页“资料分组”卡此前底边被切掉。
- 图表：只有占用类别色的系列计入 5 色上限（自带色、对照组、部门系列不占位），超出时在 `validate` 阶段报错；7.0 起不再循环取色。
- 甘特：端点命中区读 `tokens.gantt`；`*_known:false` 的任务明确报错（schema 允许对应端点为 null）。
- html-ppt-bridge：可视区高度为 0（隐藏 iframe、预览）时也写入比率 1，`--kz-u` 不会缺失。
- KZLayoutQC：`inspectFold` 只把带可见文字或已绘制图形的对象计入覆盖率，卡片外框越出视口也报 `FOLD_OVERFLOW`，缺省阈值与 tokens 一致；`inspectCard` 的 `TEXT_OUTSIDE` 恢复按内边距判断（纵向容差 0.2em、横向 1px，进 `layout.qc`）；`inspectOrphans` 按行带分行，不再把行内小字号片段误判为孤字行。

tokens 与工具
- 删除无人读取的 token：`wide.desktop_scene_min_width_ratio`、`data_min_width_ratio`，`colors.ribbon_mid`、`table_header`，`rhythm.ink_inset_*`、`sibling_inset_tolerance`，`motion.max_blur_layers_per_region`、`duration_ms.text_swap`、`scale.dialog_from`。
- 规范里写死的数值登记进 tokens 并接入代码：首屏断点（单测核对 CSS 媒体查询）、导语行长、KPI 与首屏标题字号、弹窗最宽、弹层空白比例、QC 容差、主视觉过曝判据、电影状态变化阈值、PPTX 接触椭圆 alpha、甘特命中区。
- 阴影：新增 `thin`（玻璃内的嵌套薄覆层，电影节点改用它）与 `inset`（表单字段内凹）；PPTX `raised` 的 alpha 回到单层上限 0.15。
- 正文页 chrome 几何由 `build_tokens.py` 生成为 `--kz-chrome-*` 变量，deck CSS 不再写几何数值（3 视口 × 5 页 90 个矩形前后一致）。
- 验收矩阵加入 1920×1080（同屏 F11 全屏）。
- `qc_plan.py`：四类 hero 主视觉按 `image.washout` 计算过曝并报 `IMAGE-WASHOUT`。
- `build_tokens.py`：阻尼比 ≥1 时不再除零。`build_dist.py`：在 git 仓库中只打包受版本管理的文件（98 个）。
- `hero_layout.svg_fragment`：Logo 恢复 `meet`，主视觉保持 `slice`（复测导出不再有 `srcRect` 裁切）。
- `context_pack.py`：资产阶段补 02、11、13；PPTX 制作阶段补 `glass_svg.py` 与探针说明。

规范
- 状态词统一为 10 QA-STATUS 的 PASS / WARN / FAIL / BLOCKED / PENDING / N/A；00 的验证范围措辞与之分开。
- page-plan schema 补规范要求填写的字段：`preset`、`body_profile_reason`（compact 必填）、`fold_stage` 与理由、卡片 `emphasis` / `verbatim_quote`、保护区 `zone` 与 `reference` 角色；gantt schema 允许未知端点为 null。
- SKILL 硬规则 4 区分 HTML 三层动态阴影与 PPTX 单阴影；00 写明硬规则是摘要，与所有者冲突时以所有者为准。
- 首屏舞台材料不够电影时改放关系图或图表（`fold_stage`），KPI 不够时用关键事实条，不编造；电影状态下限统一为“三个阅读状态 + 收束帧”。
- PPTX 入场 delay 统一为“同一拍起点 + n × 70ms”，并与上游定义和回读对齐；ppt-master 基线写明为 `v6.7.3-2-g523e5bd`。
- HTML-PPT：宿主禁用 headless 时的替代截帧路径；脚手架安装定位与“不复制参考 index.html”；脚本顺序补 ECharts 与 kz-layout-qc。
- 10 的工具表区分安装包内工具与仓库维护者回归（`tests/` 不随包发布）。
- COPY-08 判定改正（原文两问的方向写反）；站点、流式补“步骤”；数据更新不补间；chrome 定义；术语统一为观点句、尾页、讲稿、所有者。

## KZ7-1024-B01 · 分层重构、动效与材质增强、首屏密度、四轨正例
规范结构
- 规范只写设计规则：SKILL.md 精简为四轨与引擎、13 条硬规则与读取顺序；验收方法、门表、工具清单集中到 10；事故叙述、轮次编号、具体模型与工具名、重复条款移出正文（原文见提交 `b487472`）。规则编号沿用，新增 ELEV-01/02、LG-PPTX、MOTION-03…08、CHART-01…05、FOLD-01…05、BODY-01、DRILL-05/06、NOTES-01…03、FILM-PLAN、TYPE-04、IMG-06、CORE-01…07。
- 新增 13「首屏、页面构图与信息密度」；12-reference-patterns 移入 docs/history（ARCO 证据不在公共包，不能作为规范引用）。
- 删除 test_a04_gates 的措辞锚点测试，改为 tests/test_spec_structure.py：每条规则只有一个所有者、引用的规则必须存在、规范正文无事故史标记、文中 token 路径存在、SKILL 引用的文件存在、版本一致。
- tools/build_dist.py：安装包排除 review/agent/docs/history/tests/examples/validation（4.1MB / 99 文件，仓库 58MB）。

材质与阴影
- tokens：`elevation`（rest/raised/overlay 三层暖色阴影、光源偏移、抬升、PPTX 作者值与 ×0.75 导出系数）、`glass.rim/specular/thin/carrier_face_gradient`、`colors.focus`；删除未被读取且与 ≤0.62 规则冲突的 `face_alpha*`。
- kz-glass.css：rim 渐变边、随指针转动；镜面光斑与顶边短高光随指针移动；阴影由 `--kz-lift/--kz-lx/--kz-ly` 插值；无 JS 时 `@property` 悬停抬升；`.kz-thin` 补齐同族材质；电影载体去掉 backdrop-filter（消除与 FILM-05 的冲突）。
- 指针光与阴影配方生成在 `.kz-card,.kz-lit` 上（自定义属性的 var() 在声明元素解析，放 :root 不会随卡片变化）。

动效
- tokens.motion 重构：四条缓动（enter/exit/standard/data）+ CSS linear() 弹簧、分层时长、位移、缩放、错峰、倾斜（正文 4° / hero 6°）、浮动（hero 6px 错相；双菱形 2px 同相，独立 `.kz-mark-float`）、视差、电影参数。
- 入场：reveal 层只用独立 translate/scale；opacity 写在玻璃本层——实测祖先 opacity<1 时 backdrop-filter 全程失效、结束时跳出。行列波浪错峰 + 卡内标题/条目级联；退出改加速曲线（原减速曲线可见时长约 80ms）。
- 新增 `mountSections`（段落首次可见入场）、`mountField`（环境光场视差）、`countUp`、`storyboard`（按 FILM-03 计时生成首尾无缝关键帧）、`drawLinks`（随载体变形的关系连线）；倾斜改共享临界阻尼弹簧，静止停 rAF。
- 电影文字在不同文案的状态间交叉淡入（`--kz-film-text`，可 seek），不再在插值中点硬切。
- 图表：折线自左向右描出（不再整条从零抬起）、柱形错峰长出；类别色序 `charts.categorical` 与部门色分离（已过 dataviz 校验），对照组保留中性色。
- 下钻：从卡片展开、关闭折回；对话框内全部按键不冒泡（含上游 S/O/F/A）。
- 站点跨文档章节转场；HTML-PPT 翻页改为容器瞬时切换、背景与卡片各自淡入、去掉 ±30px 横移；康哲 deck 不加载 html-ppt animations.css。
- PPTX：经 ppt-master `animations.json` 的入场（Fade、随上一项、70ms 错峰、decel 0.7）与 Morph 载体合同（06 MOTION-07）。

首屏与密度
- 验收视口改为浏览器可视区：1280×720、1536×730、1920×940、2560×1080（`tokens.viewports`，取代 `site_viewports`）；qc_plan 对 HTML 三轨都检查矩阵。
- Bento 首屏（12 栏，左 4 导读、右 8 电影与状态条）、KPI 卡、状态条、`.kz-detail-tall`；`KZLayoutQC.inspectFold`（覆盖率 ≥0.45、最大空白 ≤0.18，按实测校准）。
- `KZLayoutQC.inspectOrphans` 孤字检测；`text-wrap: pretty/balance`；中文阅读行宽改为 34em（46ch 只有约 25 字）；`inspectCard` 的 TEXT_OUTSIDE 改按卡边框判断（修正行高 1.25 下字形外溢的误报）。

HTML-PPT 单位
- html-ppt-bridge 只维护一个比率：`--kz-un = innerHeight/720`（不钳制）与 `--kz-u = calc(var(--kz-un)*1px)`；修正矮视口（1080@150%）文字比框大约 18%、捏合缩放反向缩字的问题。

一致性修复
- schema `contract_revision` A06 → 7.0（此前 SKILL 写 A08 而 schema 只接受 A06）；gantt schema 补 owner/department/status/dependencies/start_known/end_known/taskColor（runtime 已读取 department/taskColor）。
- hero 主视觉的 y 偏移登记为构图；宽屏 fluid 铺满、底对齐，不再出现顶带。HERO-05 目录右缘以自身对称边距为锚（原 1212 vs 1224 永远不满足）。
- hero_layout：`html_fluid_fragment`（--kz-u 几何 / --kz-un 字号 / 右锚 / 目录随宽展开 / 入场顺序）；`svg_fragment` 用 tokens 的玻璃渐变与阴影、cover 裁切、根 lang；glass_svg 的阴影与高光长度取 tokens。
- brand_fragments：带 `data-pptx-role` 的路径加稳定 id（ppt-master 6.7 checker 报错）；qc_plan 对运动区域使用 `motion_safety_pad_px`。
- context_pack：路由 13 章、film-plan schema 与参考实现；新增 `motion` 能力（PPTX 动效）。

正例
- examples/reference：站点首页与章节页、流式文档、HTML-PPT（new-deck.sh 原始输出 + build.py 派生，上游 base/runtime 原样随包）、PPTX 导出探针（ppt-master 523e5bd 实际 checker/validate/export/delivery_check，OOXML 回读记录）；组件实验室改用 Bento 首屏。
- examples/validation 下的 6.x 样本保留作回溯，不再作为模板。

# 6.1.3 · 2026-10-07

## A08 · R2 三方审阅回写（玻璃近白高透光、FILM-01 复合判据、门表法定化、计时口径）
- 来源：R2 构建产物（glm-5.3-flash 医学写作 HTML-PPT、gpt-6-luna 入组审核站点）经 codex/bunny/grok 三方独立审阅与我方源码裁决的发现汇总；证据存项目私有工作区 retro_r2 与各审阅文件。
- 新增：09「计时口径」——总耗时必备/单页可选/「双时钟」任务书必须定义对象与语义（闭合 R2-N01）。
- 修复：runtime/kz-glass.css 补 `.kz-dialog-body` 正文字号规则（R2-F11 参考实现缺口）。
- 修复：tokens.glass 卡面三停改近白高透光（alpha ≤0.62）+ `.kz-card::after` 局部短高光，消除 LG-04 与「不得米黄实色」的张力（R2-bunny#16 规范缺陷）。
- 修复：`.kz-dirty` 改 absolute 浮层合同 + GANTT-04 真实指针验收条款（R2-F05/bunny#2 规范缺陷）。
- 新增：06 FILM-01 复合判据（几何+新信息对象+退出三条件，纯载体膨胀不计独立状态）与主载体文字落矩形条款（R2-bunny FILM 专项规范缺陷）。
- 新增：11 HERO-05 宽屏展开机检判据（≤2px）、HERO-02 目录说明换行行宽。
- 新增：07 DRILL-04「无可溢出内容记不适用/未验证」口径。
- 新增：adapters/html-ppt 页码 `.slide-number` 耦合点（R2-F06）。
- 新增：03 COPY-08 语义层示例（「不代表/不构造/规格未定义」类）与业务规则句豁免（R2-codex F10）；范围扩弹层/抽屉层、字面禁语降为示例、两问式主判定与机械化代理指标（R2-bunny B2）。
- 新增：tracks-site 单页章节锚变体合同（R2-codex F12）与三条变体约束（主层信息任务/交互单一所有者/背景盒随段高，R2-bunny B5/C1/C5）；版本语义说明（包 VERSION/REVISION 为唯一权威，tokens/schema 版本独立，R2-codex F13）。
- 新增：06 动态 protected_region 按运动包络登记；SKILL.md 过程合同补 runtime 快照版本锁定记录（VERSION+REVISION+已用模块 sha256）。
- 新增：10 门表法定化（SELF_REPORT 必含 G0–G9 门表小节，逐门 PASS+证据/FAIL/PENDING/N/A+原因；G7-NOTES/G5-PROJ 必填行）；favicon 噪音口径。
- 新增：G5 空洞量化下限（卡/载体/弹层最大内部垂直空隙与尾空隙 >30% 即缺陷，07 落地、10 引用）；06 载体高度由内容导出；04 主视觉可见度自验数字与裁切锚点规则（R2-bunny A8/C2/C7/A11/B6/C4）。
- 新增：06 性能白名单（backdrop-filter 表面禁逐帧动画 width/height）；02 载体嵌套面板材质档位（.kz-thin）。
- 测试夹具：patch_smoke 横向表演 premise 修订——`.kz-dialog-body` 字号规则生效后表演内容换行使表格变为纵可滚，双轴增量被正确路由到表（最近可滚体），夹具补 `white-space:nowrap` 恢复「表仅横向可滚」前提；非 runtime 缺陷。
- 版本同步：VERSION 6.1.3、REVISION KZ6-1007-A08；tests/test_a04_gates.py 哨兵新增 A08 锚。

# 6.1.2 · 2026-10-07

## A07 · R2 构建实机回写（边界宣示禁令、hero 衬底合同、页缘溢出实测）
- 来源：R2 构建产物（glm-5.3-flash 医学写作 HTML-PPT）用户实机审阅四条问题 + 我方 DOM 级复测；证据存项目私有工作区 retro_r2。
- 03 新增 COPY-08 边界宣示禁令：受众为熟悉人机协同分工与证据边界的内部资深人员时，受众可见层禁止呈现「AI 不替代/不等于医学判断」「最终判断由人确认」「仅供参考」「必须人工确认」类边界声明（页标题/卡标题/强调行/bullet/注脚/讲稿一律删除）；源材料边界条款登记 fact-map 即可；判断标准为「删掉后业务信息无损即属宣示」。业务规则本身（知识库优先级、可回溯、不一致处置流向）不受限。事故：R2 产物整页以「使用边界」为标题，三卡底部分别缀「不直接替代医学撰写经理的最终判断」等宣示句。
- 11 HERO-03 新增文字区衬底与主视觉铺满合同：hero 页主视觉承载文字的区域必须 ①生成时策划为低频低对比构图 或 ②合成态加同层级虚化/渐变遮罩/暗化衬底；不允许清晰高对比主体直接置于标题笔画之下；验收以合成态文字笔画区取样对比为准，裸图通过不代替合成态可读性。主视觉未铺满产生的未覆盖带（顶部白条、侧缘缺口）须在 page-plan 登记几何与理由并过审，未登记空白带按缺陷处理。事故：R2 封面/目录/章节页文字直接压清晰亮图，封面顶部出现未登记白带。
- 10 「几何与文字」新增页缘溢出实测条款：每个交付视口逐页逐卡 getBoundingClientRect 底/右对页面边界求差，>2px 即失败；卡内叶级文字 Range 矩形不得越过卡片左右内边界 >1px；CSS 裁切使滚动不可见不等于无溢出；卡内容分布沿用 03 TYPE-02 T/B/H/R 阈值，无测量记录不得自述通过。事故：R2 产物 s5 卡超页面下缘 68px（1280 视口 118px）、甘特卡内 20 处文字横向溢出、边界页卡下空白 52%——03 TYPE-02 阈值与 03:15 容量处置原有条款已覆盖但未被构建者执行，本条把测量方法与「scroll 裁切不可见≠通过」显性化。
- 版本同步：VERSION 6.1.2、REVISION KZ6-1007-A07，README/INSTALL/00/10/CURRENT_STATUS/VALIDATION_STATUS/CURRENT_HANDOFF 同步；tests/test_a04_gates.py 哨兵锚定 COPY-08/边界宣示、文字区衬底/主视觉铺满合同、页缘溢出实测/getBoundingClientRect。pytest 93 绿。

# 6.1.1 · 2026-10-06

## A06 · R1 双轨盲审回写（字号换算类型缺陷、模态键/滚轮路由、品牌几何收编、状态增量量化）
- 来源：glm-5.3-flash（HTML-PPT 轨）与 gpt-6-luna（站点轨）R1 构建的四路独立审阅（space-bunny、gpt-6.1-sol×2、grok-4.7 简版）加我方实测复核；完整证据与归因存项目私有工作区。
- 修复包缺陷（P0）：`runtime/kz-glass.css` 的 `--kz-component-u:var(--kz-u,1)` 把长度赋给字号换算系数，`calc(px token × 长度)` 整条声明无效，fluid 下组件字号全部回落浏览器默认（实测 1920×1080 卡标题逻辑 10.67px，低于 TYPE-01 地板）。改为 `--kz-component-u:var(--kz-un,1)`；`adapters/html-ppt-bridge.js` 新增 `--kz-un` 无单位比率（视口高/tokens.wide.htmlppt_reference_height，resize 同步）维护。adapter 合同改为双变量显式类型：`--kz-u` 长度仅用于几何（`calc(99 * var(--kz-u))`），`--kz-un` 数字仅用于 px 换算，附非法写法示例；字号验收改为逐实际节点 computed÷u（1280 与 2560，含控件与下钻文字），不只查声明值或卡片正文。
- `runtime/kz-drilldown.js` 补齐 DRILL-03/04 参考机制：翻页键隔离扩至 Enter/Backspace（stopPropagation 不阻碍按钮原生激活）、Tab 焦点圈禁、冒泡阶段滚轮路由（增量交指针之下沿方向仍可滚动的最近滚动体；两端与滚动体外消费，恒 preventDefault+stopPropagation；子控件已 preventDefault 时尊重其取消、不再重复路由，但仍 stopPropagation 使事件不出弹层）。07 DRILL-04 补横向滚动壳 CSS 陷阱（`overflow-x:auto` 使 `overflow-y` 计算为 auto，配 `overscroll-behavior:contain` 形成整块滚轮/触控死区；应 `overscroll-behavior-x:contain` / `-y:auto`），验收须含指针落在溢出子区域的采样。
- 品牌几何收编：`tokens.chrome.header_mark` 新增 `placement_htmlppt_u=[0,0,100,90]`（适配合同原文数值）与 `placement_pptx=native_xml`；adapter 固定双菱形节改以 tokens 为唯一几何权威。事故：R1 构建方自行缩至 37×33.3u 并移至 54/22u。
- 06 FILM-01 量化状态增量：相邻主要状态几何逐项差 >1e-3 或可见节点/连接增减，纯文案替换不构成独立状态；relations 必须有可见 DOM 对应物；验收逐对相邻状态采样，计划声明不作为关系已发展的证据。
- 10 G5-PROJ 补级联：无实机记“投屏可读性未验证”时 G2/G5 门与 SELF_REPORT 结论段同步标注，不得写无条件 PASS。
- tracks-site 补 G7-NOTES 的 N/A 显式声明惯例（站点轨无讲稿容器时须写明原因，不得留空）。
- schemas/page-plan：cards 项新增必填 `detail`（available/not_available/not_needed）与 `detail_reason`，对齐 07 DRILL-01 逐卡规划义务（A05  schema 未开放该字段，计划无法如实登记）。
- 版本同步：VERSION 6.1.1、PACKAGE_MANIFEST（revision KZ6-0929-A06，302 条 sha256 全量重算）。
- chrome 对照合格参照件实测量产（用户提供 MG-K10 方案讨论会 HTML 与研究者会 PPTX）：双菱形四原生形状（橙[24,9,70,62] 黄[5,42,40,36]+candy 层）、标题区、橙色横线 [54,80,1257,1.5px]、Logo [1031,45,158,33]、页脚两槽与页码格式，与 tokens 登记逐项吻合，无需改数；唯页脚日期格式按参照件钉死为 `YYYY年M月`（01-core 与 tokens.chrome.footer.date_format）。

## A06 · 补丁复审回写（space-bunny / grok-4.7 复审，gpt-6.1-sol 复审中断后以合并清单为准）
- `kz-drilldown.js` 真缺陷修复：`deltaMode===2` 分支误用不存在的变量 `g`（IIFE 形参为 `global`），DOM_DELTA_PAGE 滚轮事件抛 ReferenceError 且 preventDefault 不执行；已改 `global.innerHeight`。滚轮路由改双轴独立行走：Y 与 X 各找指针之下沿该方向仍可滚动的最近滚动体，横向命中不再吞掉同一事件的纵向增量（触控板单事件常带两个分量）。触控隔离补 touchstart/touchmove/touchend 阻止冒泡（不 preventDefault，弹层内原生滚动保留）并加 `data-no-swipe` 供上游引擎 interactive() 识别。焦点圈禁补标题位：h2[tabIndex=-1] 不在 Tab 环内，焦点落于环外节点时按方向收拢到首/末可聚焦件。 wheel 处理器开头尊重 `e.defaultPrevented`。
- `html-ppt-bridge.js`：`--kz-un` 下限钳 1（窄高视口不缩字，容量处置走 03；与 kz-charts/kz-gantt 的 Math.max(1,…) 一致），beforeprint 收回 1、afterprint 恢复（内联样式压过作者样式表，打印态必须显式重置），并补 visualViewport resize 监听（Safari 工具栏/捏合缩放时 innerHeight 与 100vh 分叉）。
- `kz-glass.css` 组件内部间距随字号走：卡标题下距、列表项间距、按钮 min-height/padding/gap 乘 `--kz-component-u`（720 基准下不变；按钮 min-height 保留 44px 地板）。
- adapter 双变量合同消除歧义：`--kz-u = calc(100vh/720)` 明写为长度；自定义字号合法写法只有 `calc(24px * var(--kz-un))` 或几何量 `calc(24 * var(--kz-u))`；预缩放与 `--kz-un` 二选一，不得把已乘 `--kz-u` 的值再交给 `--kz-component-u`。A03 历史样本的预乘写法在 README 显式标注不得照抄（vendor 为冻结快照，不改写历史证据）。
- 权威链闭合：00-authority 明确双菱形 HTML-PPT 放置矩形以 `tokens.chrome.header_mark.placement_htmlppt_u` 为唯一权威（视图框坐标 [x,y,w,h]，tokens 增加 format 注记），PPTX 走 native_xml；tests/test_header_mark.py 新增 placement 字段断言。
- page-plan schema 破坏性变更正式升版：schema_version const 6.0→6.1、$id→urn:kangzhe:page-plan:6.1、contract_revision const A04→A06；两份夹具同步升版：A02 hero 示例（HTML-PPT 轨）补齐 detail/detail_reason/motion_objects/target_viewports/contract_revision；agent/fixtures 夹具为 PPTX 轨计划、无 motion_objects（可选字段），仅补 detail/detail_reason/target_viewports/contract_revision，A02 目录页网格 rect 按现行 hero_layout token 修正（此前被 SCHEMA 早退掩盖）；SKILL.md、test_hero.py 引用同步。pytest 91 项通过，qc_plan 对两份夹具零 error。
- 闸门措辞收敛：G5-PROJ 级联范围限定为 G2/G5/SELF_REPORT 结论段（SELF_REPORT 定义为交付随附验收自述的结论段），其余门按各自证据独立判定；G7-NOTES 在 10 章本体增加 N/A 分支，tracks-stream 同步（此前只在 tracks-site）。
- 06 FILM-01 补：归一化坐标分母写明（相对电影舞台宽高的 0–1 比例）；环回状态对归 FILM-04 接续比较（1e-4），不计入相邻状态增量采样。examples/film-plan.json 四对几何全等的相邻状态合并为 4 状态（环回保持）。
- 措辞勘误：DRILL-04 路由实际在冒泡阶段（无 capture:true），drilldown.js 注释、07、CHANGELOG 原「捕获阶段」表述统一改「冒泡阶段」；07 DRILL-04 补三类必验形态（双轴增量、触控滑动、实现取舍知情——手动 scrollTop 换确定性、丢平滑/惯性）。
- 版本串补齐：REVISION→KZ6-0929-A06；README、INSTALL、00-authority、10-quality-gates、CURRENT_STATUS、VALIDATION_STATUS、agent/CURRENT_HANDOFF 全部同步 6.1.1/A06（ECharts 6.1.0 为库版本号，不动）。
- 运行时冒烟扩展重跑（playwright-core + Chromium，1920×1080）：原 9 项基础上新增双轴滚轮（dx=120 且 dy=150 同时生效）、deltaMode=2 不抛错、触控三事件零冒泡+data-no-swipe、标题位 Tab/Shift+Tab 收拢，共 14 项全过。
- 已知边界（记录在案，不展开修复）：page 级背景图的逐图 detail 登记未开放（DRILL-01 目前只覆盖 cards）；数字输入与部分 select 的滚轮默认动作在弹层内被取消（路由确定性取舍，07 已注明）。
## A06 · 终审回写（gpt-6.1-sol / space-bunny 终审，修复已落地并实测）
- `kz-drilldown.js` 滚轮早退泄漏修复：子控件已 preventDefault 时原实现直接 return、不 stopPropagation，事件穿出弹层触发宿主翻页；改为 `defaultPrevented → stopPropagation 后 return`（事件不出弹层的隔离不变量对所有路径成立）。
- `kz-drilldown.js` 平滑滚动吞增量：宿主或 UA 样式 `scroll-behavior:smooth` 时手动 `scrollTop` 赋值被动画化、连续增量相互覆盖，路由丢失确定性；改为赋值前临时内联 `scrollBehavior='auto'`、赋值后恢复（instant 辅助函数）。deltaMode=2（整页滚动）时 X 轴分母改用 innerWidth（原为 innerHeight，宽屏横向页滚动距离失真）。
- `kz-drilldown.js` 焦点候选过滤补强：`:disabled` 用 `el.matches` 判定（字段集禁用继承）、排除 `[inert]` 子树、查 computed visibility/display（仅 offsetParent 会漏 `visibility:hidden`）。触控隔离补 `touchcancel`。
- `html-ppt-bridge.js` 打印不变量：新增 `printing` 标志——beforeprint 锁定 `--kz-un=1`、打印期间 resize 不改写、afterprint 恢复原值；抽出 `writeRatio()` 统一写入并广播 `kz:fluidratio` 事件供运行时组件重渲染。视口高取 `visualViewport.height||innerHeight`。
- `kz-charts.js` / `kz-gantt.js` 流体适配闭环：各自新增 `fluidUnit(el)`（fluid 模式读 :root `--kz-un`，弹层内经 `el.closest('.kz-dialog')` 正确解析，`document.body` 空防御）；监听 `kz:fluidratio` 重渲染（charts 纳入 releaseAll 释放清单，gantt 复用既有 AbortSignal）。修复前弹层内图表字号按视口而非弹层缩放。
- adapter html-ppt 字号合同收敛为单一规则：自定义字号只许 `calc(24px * var(--kz-un))`，`--kz-u`（长度变量）禁用于 font-size——矮视口下两种写法分叉且验收不可判定；验收分母统一为 `--kz-un` 使用值。
- 06 FILM-01 口径补全：归一化坐标分母（载体短边系数直接比）与 tint 比较口径（RGB 分量 ÷255、alpha 直接比）写明，消除「几何差>1e-3」在实现侧的解读空间。
- A02 目录三卡 ambient `none→float`：目录卡片为主要内容载体，HERO-05 要求 hero 页元素有环境动效登记，none 与示例其余页不一致。
- `kz-glass.css` 组件间距补乘 `--kz-component-u`（第二轮）：.kz-thin/.kz-marker/.kz-chart（高 350px）/.kz-chart-status/.kz-film-stage（440px）/按钮 radius 16px/dialog head/body padding；卡 padding 与 grid gap 保持项目域不动（版心尺度属项目决策，规范不预乘）。
- tokens 对齐实测：`dialog_height_vh` 88→94（对齐 kz-glass.css 实测值）；build_tokens.py 新增派生 `--kz-dialog-width`/`--kz-dialog-max-height`，kz-glass.css 改消费变量、不再硬编码。
- 闸门措辞唯一口径：tracks-site 与 tracks-stream 的 G7-NOTES 描述统一为「以 10-quality-gates 该门条文为唯一口径」，消除轨道文件与闸门本体的措辞漂移。
- tests/test_a04_gates.py 新增 `test_gate_wording_anchors`：哨兵串断言（投屏可读性未验证/SELF_REPORT/唯一口径/禁用于 font-size/kz:fluidratio/除以 255/FILM-04），防终审条款在后续编辑中静默丢失。
- tests/test_header_mark.py 新增 `test_placement_fields_registered_in_tokens` 与 `test_svg_asset_viewbox_matches_placement`：正则解析 SVG viewBox 与 tokens placement 对拍，品牌几何漂移由测试拦截。
- 冒烟扩至 17 项：新增 defaultPrevented 包容（子控件取消后事件不出弹层）、scroll-behavior:smooth 下 200ms 内增量不丢失、打印三段（beforeprint 锁 1 / 期间 resize 不改写 / afterprint 恢复）断言，全过。
- .gitignore 补 `.pytest_cache/`。
- 终审后措辞勘误（冻结后非阻断项，由 bunny R3 §3 提出）：10 章 G5-PROJ 与 03 章「除以主题 u」统一为「除以 `--kz-un` 使用值（含钳制与打印锁定）」，消除 `--kz-u`/`--kz-un` 双变量下的解读歧义；哨兵测试同步锚定两章 `--kz-un` 且禁「主题u」回退。终审结论（codex+bunny 双「可冻结」）：16 项修复核验全对、93 pytest 绿、manifest 302 条 0 不符、无新 P0；非阻断建议另两条留档（A02 实建件早于计划属冻结证据；bridge beforeprint 先于图表注册致打印重绘两次，终态正确仅冗余）。



## A05 · 阶段性汇报实战回写（电影中断安全、模态滚动、状态可辨、讲稿时钟）
- 来源：医学部阶段性汇报（HTML-PPT 与站点融合、逐页动画电影、多层级下钻、S 键讲者窗）十余轮返工中已定位的真实失败模式；条款只收不变量与验收法，事故细节留在本条目。三方会商（gpt-6.1-sol / grok-4.7 / space-bunny）记录存项目私有工作区。
- 06 FILM-05 补中断安全：暂停/seek/再次进入/编辑打断只终止自有补间且限其正在写入的属性；禁止不区分属性的 kill/clear/overwrite 连带终止同时间轴未开始的补间；重开以整条时间轴为单位；锚点可见性须符合进度。事故：GSAP killTweensOf 未限定属性，误杀未开始的 autoAlpha tween，主令牌永久 opacity 0；静态截图与录屏均不可见，由播放中段 computed 断言发现。
- 06 新增第 16 节状态可辨识性：状态差不得只由细描边或低于 TYPE-01 地板的标注承载；流程需要区分三态时，已过态须保留不依赖动画的完成标记；手段不规定数量，示例移 12；减少动态与静态总览下区分仍成立。§15 审阅样本补中断-恢复帧与“主要叙事状态须有新增解释价值”的观看判定。
- FILM-03 补：并行车道/并列分支同时建立（优先于 70ms 间隔默认值）；关键解释第一圈即完整可读；连续多页不追求统一片长、避免同一开场结构。
- 07 新增 DRILL-04 模态期间内部滚动优先：模态打开期间页面翻页暂停；滚动增量交给指针下仍可滚动的最近滚动体；到边缘或滚动体外消费事件，不链式滚背景、不翻页。事故：全局 wheel 捕获无条件拦截，弹窗 267px 溢出内容完全不可达。
- 10：G7 最小证据补登记锚元素中断-恢复后可见性断言（G7-ANCHOR，锚清单登记于 QC 旁注，不改 film-plan schema，个数不设上限）；G8 补可滚动层真实滚轮双向放行与边缘吞没；G5 方法补投屏可读性（最大交付视口 100% 渲染加实际观看条件判定；截图缩小不是等价代理；无实机记“投屏可读性未验证”）。
- 09 新增校准锚（只提问、不设字数区间、不以句数触发诊断）与“讲稿与电影共用同一业务时钟”（讲稿不得指向尚未出现或已消失的状态；静态摘要持续保有，不要求逐帧完整）。
- 03 新增 COPY-07 卡内嵌装饰图构图：图固定一侧、向文字侧渐隐至近白、文字落近白侧；证据图/图表/影像除外；不催生新图；PPTX 文字不栅格进图。
- 00 补：融合形态不是第五轨，须声明导航/缩放/讲者窗口/chrome 的轨道归属。
- 会商否决未入条款：投屏截图 50% 缩放代理（只是降采样，不构成观看距离等价）、状态变化“至少两项属性”计数（不可定位失败）、讲稿 100–150 字通用区间（数字即成硬门）。
- 第二轮复审（同三家）后修订：FILM-05 锚点登记位置与 G7-ANCHOR 对齐（schema 未开放时登记于 QC 旁注）；09 双时钟节消除 static_summary 逐帧误读、删去与 FILM-03 重复的第二圈句；校准锚删句数触发；第 16 节术语对齐（当前对象/状态进入前中后/target_viewports）；新增 G7-NOTES 验收段；G5-PROJ 补 PPTX 画幅口径。
- 版本同步：PACKAGE_MANIFEST（version 6.1.0 / revision KZ6-0929-A05，全部 302 条 sha256 重算）、README、INSTALL、CURRENT_STATUS 头、VALIDATION_STATUS 头、CURRENT_HANDOFF 头。review/LOCAL_VALIDATION.json 保留 6.0.0 历史验证快照不改写；各历史轮次记录（R12–R23）保留原文。

# A04 R23 · 用户指定快速收尾
- 修下钻背景文字重影、背景CSS动画争用与多实例滚动恢复；弹窗正文与电影不模糊、不降低动画速度。
- 补有界词组、统一否定重点、真实浏览器换行与目录整卡运动保护；修实际H08行首标点，源事实保留。
- 生图能力发现纠正：实际服务customConfig原生2560×1088已验证，脚本缺参数不再等同服务缺能力。
- 90项合同及真实Chrome下钻组件通过；H08受影响56层级/事实检查通过；两上游/Office/跨模型证据保持各自范围。
- 按用户要求不再派新测试；发布安装与完整四轨两轮验收分开，未完成项/STOP不改绿。

# A04 R17 · 静态布局、退出顺序与循环数据验收
- 固定hero文字框由tokens计算右留距，保持角色字号与左锚；正文和背景仍占满宽屏。
- 静态布局绑定实际总览几何，分别验证preview/RM/capture/print；普通动画保留。
- 原速验证业务阅读真实显露、子信息先退出再收缩、第二圈图数同步及隐藏恢复；无越界不替代这些门。
- 自动记忆隔离以配置与真实工具轨迹核验；盲审区分实际硬规则、条件、诊断与审美建议。
- 新fresh独立Gemini规范差异审正常154.867秒，四文档0硬问题；这是规范审，不是四轨验收。
- 实际DS配额、EGO工具/空间、真实生图像素接口仍阻塞；不降低生图、字号、可编辑和指定引擎要求。

# A04 R15 · 非正文页码门与可移植启动
- 增加HERO-CHROME，补adapter页码仅正文的明确边界。
- 明确复制实际上游原件、file/HTTP正常启动和Film外层root接口。
- 手换行保护中文语义单元；不改字号、条件与正常全角标点。
- 90组件通过；独立审阅发现的新接口歧义已修并取得fresh复审。整体验收仍未完成。

# A04 R14 修订
- 站点/流式responsive档显式记录实际字号，同角色一致/16px地板不变；PPT固定角色检查补齐。
- Charts/Gantt/mountPage初始化回滚、宿主唯一全局与CSS后台owner清理；普通图表入场不先跳到满值。
- 历史A03仅同步当前JS以测生命周期，现行视觉按tokens/design_specs；89合同和真实分层检查见R14状态。
- 保留未完成门、原始失败与真实像素WARN。不是最终验收版本声明。

# 6.0.0 · 2026-09-29

## 2026-10-01 A04 R12 候选（安装/发布以实际回执为准）
- R11已发布并安装；以下早期“候选/未冻结”段落是保留的开发历史，不是当前安装状态。R11正式目录采用同一阅读基线，早期有/无说明变体已被取代。
- 真实普通HTML-PPT报“载体关键帧超出舞台”；API补明当前构造器的归一化边界与初始化状态，质量门分开普通态、静态导出和数据联动。
- 真实流式全周期机械通过后，独立盲审仍发现首页短文子卡巨高空白；新增嵌套阅读组纵向核对，不把父载体内容跨度当子卡通过。居中短卡与卡外留白按实际测量裁决。
- 本候选修复已证实的接口、校验器与共享组件缺口；作者实物修复和四轨最终验收仍在执行，不记为全包完成。
- 修复qc_plan对合法目录说明的误拒：说明可按实际槽位缺省，但出现时必须在固定槽且不重复；补混合/全有/全无说明及错位/重复回归。
- Film dispose清除根的ready/progress运行态，保留载体身份；真实Chrome销毁/重建检查通过。
- Gantt编辑区键盘事件不冒泡至HTML-PPT翻页器，保留按钮原生Enter/Space激活、select默认事件与图上键盘编辑；实际组件Chrome及Luna执行的两档28项上游交互通过。select默认事件未阻止不等于特定操作系统一定改变选项。
- 真实Default制作补核原生数据对象阅读底板与上游静态decoration接口。PPTX七页原生放映、新鲜独立VLM静态零确认缺陷、隔离副本中文/表格/形状编辑保存重开已完成；生图像素和四轨最终两轮/保留集仍未关闭。

- 图表轴由完整真值固定并生成1/2/5整齐刻度，保留科学显式尺度；有限极值/下溢回退与单端科学范围冲突早拒，长数组不做无界参数展开。季度起点非Q1仍显示年季，半开末界不伪作新年份任务。真实Chrome15探针通过，动画性能未据option测试声称。
- 普通与静态HTML导出状态按真实引擎分开，不再要求不存在的freezeForPreview通用接口；孤字行优先统一段落/共同宽度，禁止逐卡缩字或补造事实。

- 修复单一asset_id无法表达responsive双真实源的合同缺口：可选viewport_assets按精确交付视口覆盖；每源仍逐一核生成、真实像素/哈希、crop、保护区和审阅，不降IMG-04。RED七失败后GREEN全67合同，synthetic夹具不当生图。

- 新鲜审阅找到默认回退源漏检和rendition自声明保护区绕过，修复generated schema/默认源实物核验，新增有主体非基准viewport_regions与运动安全外扩；全71合同GREEN，后续新审和实物接入继续。

## A04 R11 未冻结候选
真实原创七页暴露目录无说明时底空白与页眉线端点误读；固定目录阅读变体（按说明有无选用）、HTML卡与文字共父层，并显式标注线端点格式。外框/字号/引擎不变；候选尚未安装或宣称完整产品通过。在途测试继续使用不可变R10。

- 合并4.5.7与5.2.7为一个技能；不继承旧版平面开关、并存说明、遗留色条兼容或旧CSS优先权。
- 建立主题所有者和单一token，四轨共用材料/字体/图表语义；交互降为通用能力而不是第五轨。
- 重写生图规则及生成前/生成后保护门；正文背景可复用但须映射真实批准生成资产。
- 统一15pt/20px正文与整页12pt/16px紧凑下限；取消10.5pt和13.5px等正文/辅助槽混用豁免。
- 主题标题与可选居中观点句分离；正式中文、受众脚注与私有来源分离；讲稿取消逐页定额。
- 全面禁止卡片边缘通长彩条；统一高光/透明/层级，特殊可访问态不成为旧扁平模式回流路径。
- 新写连续电影、同载体身份、首尾接续、暂停原因、静态详情、宽屏和多层下钻合同。
- 提供独立 ECharts / 季度甘特 / 宽下钻 / Film 参考实现与实际组件测试；新增指定上游适配合同。
- 附异质模型+harness评估、归因、修订循环和证据型HANDOFF。未实际完成的集成与生图不记为完成。

## A04 候选修订
- 强制页面布局/逐对象动态、真实资产像素裁切与实际Film接口，明确四轨各自多轮验收。
- 站点只验收桌面宽屏，移除手机/窄屏适配要求；流式与HTML-PPT范围独立。
- 将ARCO业务电影、宽幅多层明细转为有取舍的机制参考，保留同载体、自然滚动、可读性与状态恢复要求。
- 用户指定sci-draw时只调用生图能力，不导入其他视觉规则；实际尺寸与请求分开记录。
- 本修订仍为候选，原A03发布历史保留，未宣布最终放行。

- A04桌面范围QC：页面计划必填target_viewports；站点只要求四档桌面宽屏，生成资产裁切覆盖逐视口核对，保护区/主体框正尺寸与边界检查；42项合同回归通过。视觉盲审误判与制作缺陷分开记录，不将彩色语义表头自动等同装饰色条。

- A04真实轨迹修订：按工序读取与样页落盘门，PPTX排除HTML实现阅读；明确用户指定生图导入原manifest；补充字段/条目口径对账、文字退出先于收小及滚动测试基准。

## A04 固定标记修订
- 用户指定的原生双菱形成为唯一资产；PPTX 导出后直接复用，HTML 同源几何与整组竖直微浮动。删除旧额外折面/白高光/异相位移要求。

## 2026-09-30 A04 品牌装饰适用范围
双菱形仅用于 PPTX 与 HTML-PPT；站点式和流式 HTML 不挂载、不留空占位。固定 PPT 原生资产与 HTML-PPT 微浮动不变。此项已做实际浏览器局部验证，不代表四轨完成验收。

## 2026-09-30 A04 正文背景范围修订
新增 IMG-05 与 G4-BODY：PPTX/HTML-PPT 正文采用近白阅读区、极少量边缘光影；前景同族玻璃壳负责分隔，不给每个元素叠卡。主视觉页仍按自己的保护区构图。本次为规则范围修订，不纳入在途共享运行时代码，不代表四轨验收完成。

## 2026-09-30 A04 共享组件与验收证据修订
修复动画目标所有权、几何回执、默认文字约束及真实布局测量；补入七套真实浏览器反例回归。明确不调用原生Excel，保留PPTX原生对象与PowerPoint编辑回读。HTML-PPT正式静态截帧以官方renderer加派生副本，不取消观众自动动效。四轨整体仍在验收循环，组件通过不等于整包无缺陷。

## A04 下钻容量 R9
- 真实双家族盲审发现宽幅下钻固定高度与表格偏左；桌面保持82vw但按内容 fit-content、限制94vh、长内容单独滚动；单层不重复面包屑，多层完整返回路径。
- 固定列阅读遮罩允许同族不透明浅底，保留外壳玻璃；新增容量/遮挡验收。实际短/长内容、滚动、焦点与层栈Chrome回归、53组件和47合同通过。
- Luna/max现成SVG的Default完整引擎重放正常完成，单列为引擎证据。CodeBuddy429至2026-09-30 22:28:20，不能计中断制作通过。四轨最终两轮/保留集仍未完成。

## 2026-09-30 A04 R10 工序与真实交互核查
- context_pack新增bootstrap/plan/assets/author/verify，owner hash及同会话已读声明；默认旧read_files兼容，终审保留完整规则。
- runtime/API.md列实际接口、上游责任与standalone exit取消句柄；没有新增演示引擎或第二套计划validator。
- 独立Sol真实审阅发现桥异常状态/初始化泄漏；Chrome复现后修复事务初始化、成功后提交活动状态、全量销毁后聚合错误。3异常与5正常浏览器检查通过。
- 真实HTML-PPT鼠标驻留发现reveal祖先preserve-3d造成hover立即复位，06加入实际合成指导及真实pointer驻留测试；当前测试者实物仍待修复，规范文字不是成功证明。
- 51合同通过；整包仍持续验证，不计最终两轮或holdout。

R10最终组件检查：桥四项异常路径及五项正常生命周期在真实Chrome通过；51合同通过。新增真实pointer驻留门不代表失败作者实物已修好。流式owner最新R9 runtime六场景×两档12个自然完整周期，1948样本、0可见文字越界、同carrier与双层返回焦点通过，仍非指定模型制作终态或最终四轨轮。

R11候选另由真实Chrome确认fluid u=1.5共享控件仍16屏幕px（10.67逻辑）违反TYPE-01；加入仅fluid组件文字单位换算，站点/流式保持屏幕值。待实际接入与独立复审，不记为指定tester成功。

## 2026-09-30 A04 R11 候选
- 目录改为一套共同号码/标题基线，有真实说明放下方槽，不造空块；显式卡身份、转义和粗筛/实际字形边界分开。
- HTML-PPT fluid共享UI字体按同一u换算，其余HTML保持屏幕字号；57合同及真实Chrome目标组件通过，独立v4冻结源/帧复审无确认产品缺陷。
- 接口提示舞台height与min-height、离页暂停原因须成对恢复；匿名新七页仍有真实撞字，保留失败继续修。
- 站点真实串行8首页/章节自然周期及L2-A30秒已有129项检查0失败，未测B/C完整周期、真实hidden/EGO仍不关闭。整体仍PARTIAL。
