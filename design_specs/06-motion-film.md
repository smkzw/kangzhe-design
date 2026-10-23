# 06 动作、编排与电影

本章拥有动作词汇（token）、编排、电影，以及 HTML-PPT 与 PPTX 的动效接入；数据揭示的语义归 05 CHART-04，指针光与倾斜归 02 ELEV-02，下钻展开归 07 DRILL-05，它们都使用本章的 token 与编排。HTML-PPT 保留上游翻页控制，站点与流式保留自然滚动。动画在观众端自然自动发生，不出现播放、暂停、重播、进度条、时间码或“开始播放下一页”等控件（包括悬停唤出的）；后台暂停与 QC seek 接口保留，不属于观众界面。

## 动作词汇 MOTION-03
全部取自 `tokens.motion`，runtime 生成为 `--kz-ease-*`、`--kz-dur-*`、`--kz-dist-*` 变量，JS 通过 `KZ_TOKENS.motion` 读取。

| 类别 | token | 用途 |
|---|---|---|
| 缓动 | `easing.enter` (.05,.7,.1,1) | 入场、展开：快出慢停 |
| | `easing.exit` (.3,0,.8,.15) | 退出：慢起快走（退出不能沿用减速曲线，否则可见时长只剩三分之一） |
| | `easing.standard` (.2,0,0,1) | 状态变化、悬停、阴影 |
| | `easing.data` (.33,1,.68,1) | 数据揭示与计数 |
| | `spring` | 指针光源与倾斜：JS 临界阻尼；CSS 用 `--kz-ease-spring`（linear() 采样，超调约 1%） |
| 时长 | `duration_ms.*` | hover 150、title 360、item 360、card 520、exit 220、dialog 420、page 480、section 640、data 1000、count 900 |
| 位移 | `distance_px.*` | 卡片 18、标题 10、条目 6、退出 8、段落 28；HTML-PPT 乘 `--kz-un` |
| 缩放 | `scale.*` | 卡片自 0.985 入场，退出至 0.99，弹窗自卡片尺寸展开 |
| 错峰 | `stagger_ms.*` | 卡片 70、条目 45、组 90、观点句另隔 200（`takeaway_gap`），单页总错峰上限 560 |
| 倾斜 | `tilt.*` | 正文卡 4°、hero 6°、透视 1400px（02 ELEV-02） |
| 浮动 | `float.*` | hero/目录卡 6px / 7.2s，每张错相 1.3s；双菱形另用 `header_mark_float` 2px / 6.4s 同相 |
| 视差 | `parallax.*` | 仅环境光场：滚动位移 × 0.06，上限 48px |

同类动作在全站速度一致。超出阅读能力时减少同时变化的对象，不把动画调快。

## 编排 MOTION-04
一页内容按阅读顺序分层出现：

1. **卡片外壳**：reveal 元素用独立的 `translate` / `scale` 属性做位移与缩放（不占用 `transform`，倾斜和浮动在别的层）；透明度写在**玻璃元素本身**——祖先 opacity<1 会让玻璃的 backdrop-filter 失效（02 LG-04）。
2. **错峰**：按阅读顺序的行列波浪（行号 + 列号）× `stagger_ms.card`，`data-kz-order` 可显式指定；并行车道或并列分支同时出现，不逐个排队。观点句（`.kz-takeaway-card` 或 `data-kz-takeaway`）排在其余内容之后，再隔 `stagger_ms.takeaway_gap` 出现，与 PPTX 相同。
3. **卡内级联**：外壳开始落定后（+`stagger_ms.group`），卡标题上移 `distance_px.title`（`duration_ms.title`），每条 bullet 与表格的每一行上移 `distance_px.item`（`duration_ms.item`），依次淡入，条目错峰 `stagger_ms.item`。单元格、图表和电影舞台内部不单独运动。
4. **数据**：图表与 KPI 在其页或段落首次可见时开始揭示（05 CHART-04）。
5. **退出**：220ms 加速曲线，上移 8px 并略缩，不错峰。

`KZMotion.mountPage(root)` 实现以上全部（enter / leave / finish / dispose）；独立组件可用 `reveal(root)`。结构为：布局外壳 → reveal 层 → 浮动层（如有）→ 倾斜玻璃层 → 阅读内容；每个属性只有一个写入方，文字始终在卡内随卡运动。卡片的布局/reveal 祖先不加 `transform-style: preserve-3d`。

## 环境与微交互 MOTION-05
- **指针光源与倾斜**：02 ELEV-02。
- **浮动**：HTML 各轨的目录、章节、首尾玻璃卡 `.kz-float`（错相）；HTML-PPT 正文双菱形 `.kz-mark-float`。大号标题与 Logo 保持静止。后台、非活动页、减少动态、冻结态暂停。
- **环境光场视差**：`KZMotion.mountField` 让 `.kz-optical-field` 随自然滚动小幅位移；只作用于环境层，文字、数据、电影舞台不参与；不改变任何电影时钟。
- **段落入场**：`KZMotion.mountSections` 让首屏以下的 `[data-kz-section]` 在首次进入视口时按 MOTION-04 入场；没有 JS 或减少动态时内容直接可见；不做滚动绑定的进度动画，不拦截滚动。
- **章节转场**（站点式）：同源多页启用跨文档 view transition（kz-glass.css），旧页按 `duration_ms.exit` 加速淡出，新页按 `duration_ms.section` 上移 `distance_px.section` 淡入，站点头部保持不动；不支持的浏览器直接跳转。不同文档不声称共享同一个 DOM 元素。
- **下钻展开**：弹窗从触发卡片的位置与尺寸展开（07），层级前进/返回横向滑入，关闭时折回卡片。
- **KPI 计数**：`KZMotion.countUp`，终值即真值。
- **状态条**：当前/已过/未到三态切换使用 `duration_ms.item` 过渡；已过态有不依赖动画的完成标记（FILM 状态可辨）。

## 禁止 MOTION-06
正式医学内容中禁止：闪烁、故障字、霓虹、扫光文字、纸屑、烟花、爆炸数字、随机飞字、剧烈弹簧（超调 >2%）、音效提示、整页 3D 翻转、跑马灯、Ken Burns（会改变已审阅的裁切）、打字机效果（减少动态下会丢字）。

html-ppt-skill 自带的 `animations.css`（data-anim）与 `fx-runtime` 不在康哲 deck 中加载：其中多数属于上面的禁止项，且不处理减少动态、不可 seek。不加载之后，上游的 A 键也不再注入动画。需要的有方向入场（fade-up/left/right）、依次出现、连线描绘等语义，由 MOTION-04 与 `KZMotion.drawLinks` 实现，每种动作只有一个实现。

## HTML-PPT 动效 MOTION-08
- 生命周期只用 `KZHTMLPPT.bind(deck, factory)`：每个上游直接子 `.slide` 一个生命周期，enter 时 `mountPage.enter()`、图表 play、电影 `resume('engine-inactive')`；leave 时反向；overview 克隆不挂载。
- 翻页：上游给 `.slide` 0.5s 透明度渐变和 ±30px 横移。康哲 deck 在品牌层改为“容器瞬时切换、离开页在退出窗口（`duration_ms.exit`）内保持可见、背景图与卡片各自淡入”，去掉横移；理由是容器透明度渐变会让整页玻璃失效再跳回（02 LG-04），横移会让同一张背景错位重影。减少动态下全部取消过渡。参考实现 `examples/reference/htmlppt/deck.css`。
- 不改写上游导航、hash 或 `.is-active`；dialog 内所有按键不冒泡到上游（07 DRILL-04）。

## PPTX 动效 MOTION-07（经 ppt-master）
动效写在 ppt-master 项目的 `animations.json` 侧车，由上游 `animation_config.py validate` 校验、`svg_to_pptx.py --animation-config animations.json` 导出。

- **默认**：页面转场 `fade` 0.4s；对象动画默认关闭，只有用户要求动效或交付计划写明时才开启。不用 `auto / mixed / random` 模式。
- **入场**：正文内容组用 `entrance_fade`，`trigger: with-previous`（进入页面即自动发生，不增加点击），时长 `duration_ms.card`/1000，`decelerate: 0.7` 近似 `easing.enter`。
  - 同一页的 with-previous 行属于同一拍，每行的 delay 都从这一拍的起点算，不累加：第 n 组（n 从 0 起）`delay = n × stagger_ms.card / 1000`。
  - 观点句在最后一组之后再隔 `stagger_ms.takeaway_gap`：`delay = (组数 × stagger_ms.card + takeaway_gap) / 1000`。参考实现三组卡片加观点句，导出回读为 0 / 70 / 140 / 410ms。PPTX 没有 18px 小位移预设（`entrance_ascend` 移动约 10% 画高），小位移不映射，明写降级为纯淡入。
- **图表**：整个图表对象用 `entrance_wipe`，方向为自底部，时长 `duration_ms.data`/1000；不承诺按系列生长。上游两份文档对 `direction` 的含义说法相反，导出后以 `p:timing` 回读为准：自底部应为 `presetSubtype="4"`。
- **退出**：换页本身完成退出，不写 exit 动画。
- **叙事载体（一形不切）**：用 Morph 承载。相邻两页的载体组用同一个 `morph.pairs.<key>`，导出为同名 `!!<key>`；目的页 `transition: morph, morph_by: object`，0.8s。载体必须是普通内容 `<g>`（原生图表、表格、带结构角色的组不能配对），两端结构同构；只出现在第二页的文字用淡入。Morph 只能在 PowerPoint 中验收，LibreOffice 不算；不支持 Morph 的客户端回退为淡入淡出。
- 页眉双菱形、页脚、Logo、背景保持静态（结构角色会被自动排除）。
- 导出后用双菱形绑定工具时，再跑 `pptx_delivery_check.py`，核对 `p:timing` 与 `!!` 名称完好。

## 动画电影
### 什么才算电影 FILM-01
同时具备：有材料依据的叙事问题；至少三个有关联的阅读状态（film-plan 的 `states` 另含一个回到首状态的收束帧，所以至少 4 项）；一个可识别并持续存在的主载体；建立、解释、关系变化、收束的顺序；自动推进；首尾无跳切地接续；静态完整信息随时可读。

相邻主要状态必须同时满足：(a) 主载体几何（x/y/w/h/r，归一化到舞台；tint 按通道 ÷255）至少一项变化超过 `motion.film.state_delta_min`；(b) 至少一个新的可见信息对象（文本、节点、连线）进入，或既有对象的可读内容实质增加。收束段还须先让上一状态的内部信息退出或归位，再收小载体。只换标题、几何相同、或载体膨胀而里面没有新信息，都不算独立状态，应合并并缩短总时长。`relations` 必须有可见的 DOM 对应物（节点、连线或高亮），只写在说明文字里的关系不算。

不算电影：背景粒子、几张卡轮流淡入、滚轮不动就不推进、录制的视频、截图之间交叉淡入。

**站点首页、每个独立章节页和流式文档首页的首屏舞台默认放电影。** 材料达不到本条（没有三个有依据的关联状态）时，舞台改放有依据的关系图或 ECharts 图表，page-plan 写 `fold_stage` 与理由，不为凑电影编造状态。流式一级章节入口用章节电影或章节首区块。不要求每个小标题都循环。HTML-PPT 的流程、关系、章节页优先用电影，密集原文表与统计明细页用稳定的分组入场即可。

### 先写电影设计书 FILM-PLAN
每部电影一份 `film-plan.json`（`schemas/film-plan.schema.json`）：`id / page_id / question / audience_message`、`source_claim_ids`（合成示例标 synthetic）、`carrier_id`、`protected_regions`（运动对象按扫掠包络）、`states`（几何、材质、文案、数据、解释任务）、`relations`（谁、何时、为什么，无依据的因果不画成因果箭头）、`timing`、`loop_contract / static_summary`（写明由哪些已有 DOM 承担静态总览：电影节点、状态条、左栏要点；不另建总览卡，见 13 FOLD-01）` / lifecycle_api / audience_playback_ui=false / reduced_motion / cleanup`。含数量的电影旁附数据对账表：画面对象 → 源字段 → 单位 → 计算 → 受众标签，条目数与字段数、单版本与两版本比较分别核对。

先回答“观众此刻看懂了什么、这个状态为何由上一状态发展而来”，再写动画代码。

### 一形不切 FILM-02
主载体保持同一个 DOM 节点（或同一条可追踪的 SVG path），只改它的位置、尺寸、圆角、色彩和光学参数。禁止：载体透明后换物体；时间边界上 destroy/create；React 换 key 导致重新挂载；从 SVG 切到 DOM 复制品；分裂成多个后任取一个当原载体。允许：持续存在的载体展开后露出它本来容纳的子信息；预先存在的对象按顺序进入；用连线表达关系；文案在稳定的文字槽里换。

### 叙事语法
- 研究流程：信息片 → 展宽为阶段容器 → 步骤与角色依次连接 → 聚合 → 收回。步骤来自材料，节点形成后有足够停留。
- 证据组织：研究卡 → 展开为人群/方法/结果 → 结果图随共用进度显露 → 有依据的解释 → 收束。研究结果不从随机数字长到最终值来暗示时间变化。
- 部门协同：同一任务载体；部门以固定身份色出现；责任连接依序显露；不画材料未支持的“自动批准”。
- 信息结构：同一容器从概览展开成分类面板，再收拢；细节放下方与下钻。
- 阶段计划：稳定时间轴上任务条依序延伸；用户点击条即暂停电影进入编辑，动画不覆盖修改。

### 时间 FILM-03
参考时长约 36 秒（`motion.film.default_ms`），通常 3–6 个阅读状态；停留由信息量决定：中文约 5–7 字/秒加起读时间，关键说明至少 2 秒。文字稳定后才开始计停留；关键观点和限制必须在第一圈就完整呈现并可读。`KZMotion.storyboard(states)` 按这一规则从状态列表生成关键帧，参数在 `motion.film.storyboard`：

停留 = max(`min_hold_ms`, 字数 ÷ `chars_per_second` + `read_start_ms`)；状态间移动 `move_ms`；最后用 `close_ms` 收回首状态。

它同时返回 `phaseAt(p)`、`enterAt[]` 和 `staticProgress`。标题、编号、节点、连线和数值都由 `phaseAt(p)` 取当前状态，不各自维护阈值表；`phaseAt` 与载体用同一个采样器，状态条不会先于载体文字切换。

### 首尾接续 FILM-04
起点与终点是同一叙事语境：最后一段把载体带回首状态，x/y/w/h/r/tint/文字逐项相同（容差 `motion.film.seek_tolerance`），速度在接缝处趋近零；不黑帧、不白闪、不瞬移、不在接缝偷偷隐藏载体。业务上不适合回圈时设计“回到总览”的尾段，不用无语义的倒带。

### 控制与生命周期 FILM-05
- 暂停原因是集合：`hidden / offscreen / editing / modal / dialog / reduced-motion / engine-inactive / capture / qc`；只有对应原因解除才恢复，解除一个不清除其他。离屏或幻灯片不活动时停 RAF；恢复不因累计后台时间跳段。
- `seek(p)` 直接得到完整一致的状态（几何、文字、交叉淡入、节点、连线、数值都由 p 决定），不依赖播放路径；QC 可冻结指定进度。
- 挂载、卸载、再进入不重复注册监听，不重复初始化 ECharts，不留定时器；组件拥有 pause/resume/seek/dispose；同一属性只有一个动画写入方，重复挂载在改属性之前拒绝。
- 中断路径只终止本次清理拥有的补间及其写入的属性，不对同一目标做不分属性的 kill/clear。
- 性能：承载 backdrop-filter 的表面不逐帧动画 width/height/x/y。runtime 的电影载体因此不带 backdrop-filter，改用高散射面加 overlay 阴影。
- 不劫持滚轮，不强制滚完才能见内容，自然滚动不改变电影时钟，不向观众暴露进度拖动。

### 图层与文字保护 FILM-06
主载体从最小到最大的扫掠区域不撞标题、Logo、导航、关键解释或图表；每个关键帧与中间插值都检查。载体最小宽度 `motion.film.min_carrier_width_px`（可设 0）可能使载体扩张并左移，保护区检查用 `snapshot().geometry` 的实际值。

- 内部文字只在面板足够大之后显露，收回前先退出；不把大面板的文字缩进小圆点里。
- 文字切换：runtime 在两个不同文案的状态之间按 `film.text_crossfade_window` 交叉淡出淡入（`--kz-film-text`），在中点完全透明时换字，不硬切。
- 项目用业务状态表驱动文字时设 `managedText:false`，由 `onRender` 作为唯一文字写入者；不要让关键帧与业务回调同时覆写同一文字。
- 数据绘图区保持平面，光斑在其外围。卡片外层负责布局、内层负责倾斜、再内层负责进入位移，不让多个来源同时写同一个 `transform`。clip 用于物体外形，不裁文字。

### 宽屏构图
电影舞台利用宽度，阅读行长不随之拉长；横向信息按真实关系分区（版本列、并列组、输入/处理/结果区），不把短标签逐行拉到全宽，也不把一张小卡放大成空箱。信息不足以支撑当前尺寸时缩小载体、用有依据的关联实体组成舞台，不凭空补内容。站点/流式首屏电影的位置与尺寸由 13 FOLD-02 决定（Bento 右 8 栏，高度 = 可视区剩余），不按视口高度反推载体几何。展开面板中的子卡同样守 03 TYPE-02。

### 下钻中的电影
L1/L2 可有自己的电影，只在当前层可见时运行；父电影暂停，返回后恢复原进度，不重开片头。关闭时清理子电影与图表。

### 状态可辨
当前、已过、未到三态在最小交付视口下可区分；仅靠细描边或低于正文下限的标注不算。已过态保留不依赖动画的完成标记（如 `.kz-step[data-state=done]` 的勾）；光环、投影、环境光不能单独承担状态差，减少动态与静态总览下仍须成立。可选手段：命中对象抬升并加深填充、标记加大并带指向、阶段表头与主动态进入同一状态、字幕条与对象身份签。

## 对象动态清单 MOTION-01
每个非静态 HTML 页在 page-plan 为每个可见内容对象登记 `id / role / enter / exit / hover / ambient / data_progress / film_id`（或静态原因）。库存在、函数名能 grep 到、组件实验室能跑，都不等于交付页已经接入；以实际 DOM 与轨迹对账（10 G7-OBJECT）。

## 无障碍与静态态
- `prefers-reduced-motion`：不自动播放、不倾斜、不视差、不浮动、无入场与段落入场；电影停在 `staticProgress` 的总览帧（用 storyboard 时传入它返回的 `staticProgress`：信息最多的状态的停留段中点，可用 `staticState` 指定；不能落在移动段或文字交叉淡入窗口里）；全部必要事实直接可读；仍可下钻、编辑甘特。
- 打印、导出、截图不因脚本停在第一帧而丢内容：用 `static_summary` 或规定的总览帧；退出打印恢复原暂停原因与进度。
- 屏幕阅读器不逐帧播数字：提供稳定终值与图表说明（`aria-label`）。

## 实现选择
默认参考实现是 DOM/CSS + Web Animations + 一个时间轴采样器（`runtime/kz-motion.js`）。复杂路径可用 GSAP 或 Motion，但每部电影只有一个叙事时钟，不强制安装新框架；已有站点用 GSAP 的继续沿用，不把 Film 塞进去重复驱动。参考实现覆盖同节点几何与色彩插值、文字交叉淡入、关系连线、首尾检查、暂停原因、seek、减少动态与清理；关联多节点图、真实医学机制图、各视口构图仍由项目实现并验收。
