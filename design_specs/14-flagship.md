# 14 旗舰路线（对外与顶层汇报）

HTML-PPT 与 PPTX 各有两条路线：**常规**（01–13 的现行规范）和**旗舰**（本章）。旗舰用于对外汇报和向公司顶层领导汇报。8.0 起旗舰采用 **F1**：暖白画布、白纸卡与三层暖影、统一的页眉与页脚、密排的卡片组合；HTML-PPT 靠多场（scene）编排的入场、连线描出、计数、印章、轨道脉冲和 three.js 场景出效果，PPTX 靠图标、卡片组合、页面组合、背景与文字层级出效果。数值只在 `tokens.flagship`。

## FLAG-01 选路阻断与判定（MUST）
用户要求做 HTML-PPT 或 PPTX 时，Agent 必须停下，请用户在“常规”和“旗舰”之间选一条路线。得到明确答复之前，不做计划、不生图、不搭脚手架、不导出，即使用户已经上传了全部材料。

提问之前，先根据用户上传的材料和提供的信息做出判定，给出推荐路线和两三条具体理由，再请用户确认或改选。判据如下：

| 信号 | 指向旗舰 | 指向常规 |
|---|---|---|
| 听众 | 外部：合作方、KOL、投资者、会议听众；公司顶层领导、管理层、董事会 | 部门内部、跨部门例会、项目组 |
| 场合 | 大会、发布、战略或年度、季度管理层汇报、重要拜访 | 周会、进度同步、培训、工作记录 |
| 材料 | 结论导向，少数几个关键数字承担论点，适合用图示和动效讲 | 页数多、表格密集、以过程和明细为主 |
| 用户措辞 | “对外”“给老板”“高规格”“惊艳”“高大上”“发布” | “日常”“内部”“简单”“快速”“照模板” |
| 放映与分发 | 现场放映讲述 | 主要打印或以文件分发阅读 |

两边信号都有时，以听众和场合为准。

这一问放在 SKILL“开工两站”第 1 站的开工卡里（17 INTAKE），和生图能力（04 IMG-07）、轨道、页数一起问；宿主有提问工具时用提问工具，没有时输出问题并停在这一步。旗舰也要问生图能力：有生图能力时可以按主题另生封面主视觉（FLAG-03），没有时用旗舰缺省封面。

用户在本次请求里已经明确指定了路线（如“用旗舰版做”），视为已经选择：复述一句并继续。修改已有 deck 时沿用原路线（HTML 看 `body.kzf`，page-plan 看 `route`）；用户要求换路线时才重新选。站点式或流式 HTML 不触发本阻断。

## FLAG-02 与常规规范的关系
旗舰沿用以下规范，不另起一套：品牌色、部门色与官方 Logo（01 CORE-01/02/05）、字号下限、强调与中文表达（03，含 COPY-04 强调与 COPY-10 纵向平衡）、禁止通长边条（02 LG-02）、数据真实可编辑与图表规则（05）、讲稿（09）、下钻与甘特（07、08）、门表（10）、验收视口（13 FOLD-04）、尾页固定“谢谢”（11 HERO-02）、相邻正文页换版式（13 BODY-03）。

以下条文在旗舰中由本章替代：

| 常规条文 | 旗舰的做法 |
|---|---|
| 01 CORE-04 正文页 chrome（双菱形、标题横线、页脚两槽） | F1 页眉（棱面图标块 + kicker + 页标题 + 右上 Logo 与标签）、页码进度段与页脚（FLAG-04）；双菱形的配色与斜切语言做成图标块，不画标题横线 |
| 02 LG-01 同族玻璃卡、ELEV-01 | 白纸卡：纯白面、暖色细边、三层暖影（HTML）或单个原生外阴影（PPTX）（FLAG-05） |
| 04 IMG-01/05 每页映射真实生成图 | 封面用旗舰背景套的生成主视觉（或按主题另生），其余页用程序化暖白画布（FLAG-03） |
| 06 MOTION-04/08 卡片波浪入场 | 分场编排与旗舰 fx 词汇（FLAG-06）；06 MOTION-06 的禁止项照样有效 |
| 11 hero 固定版式 | 旗舰 hero 构图（FLAG-07） |
| 03 TYPE-01 角色字号 | `flagship.type_px`；03 的字号下限、同页同角色同字号与孤字规则照常 |
| 13 BODY-02 正文模板库 | 旗舰版式库（FLAG-08） |
| 10 G2 的 `qc_plan.py` 证据 | page-plan 写 `"route": "flagship"`，hero 页 `hero_layout_id` 为 `flagship-<kind>`，背景 `image.mode` 为 `flagship_set`，正文页 `template` 取旗舰版式 id |

## FLAG-03 画布与背景
- **画布**：`flagship.canvas`——上下两色的暖白渐变，加两团柔和暖光（`glows`，平滑衰减，不出硬边）。HTML 用 CSS 变量 `--kzf-canvas` 绘制；PPTX 与静态回退用 `tools/flagship_canvas.py` 渲染同一组数值（带有序抖动，避免色带）。不做深色舞台。
- **背景套**：`assets/backgrounds/flagship/default-set.json`，两个资产，各有 16:9 与 21:9 两种画幅：
  - `flagship-cover`：封面主视觉（生成的暖色玻璃丝带，主体在右下，左侧标题区安静）。
  - `flagship-canvas`：目录、章节、内容、尾页的画布。
- **封面主视觉**：有生图能力时可以按主题另生（04 IMG-02/07 照常：生图回执、裸图与合成审阅、主体不压标题区）；画面里不放大块图标、器物或第二个视觉中心，标题区（左侧约 60% 宽）保持安静。没有生图能力时用 `flagship-cover`。
- page-plan 写 `image.mode: "flagship_set"` 与 `asset_id`；另生的封面写 `generated` 并登记资产清单。

## FLAG-04 页面 chrome
- **页眉**（内容页）：左上是棱面图标块（`flagship.mark`，8.0 第 4 轮选定 H2）：斜切的橙色大棱面里放白色线性图标，左下伴一块小黄棱面；两块棱面用常规轨双菱形的 candy 渐变（逐字取自 `assets/header-mark/header-mark.svg`），斜切语言与常规轨一脉相承。图标写在 `data-kzf-icon`（KZIcons 名称，PPTX 用同名 `assets/icons/kangzhe` 资产），默认用本章图标，同章各页一致；缺图标时运行时告警、只画棱面。右侧上下两行：完整 kicker（`data-kzf-kicker="02 资料完整性"`，`ink.kicker`）和页标题（`type_px.page_title`）。右上是官方 Logo（`geometry.logo_h`），Logo 下面是 0–2 个标签（chip），写本页的口径、单位、牵头部门或图例，不写结论。
- **页脚**（目录、章节、内容页）：上方一排页码进度段（每页一段，已到的点亮），下方左侧是部门名（`identity.name`）与汇报标题，右侧是页码“07 / 13”。封面与尾页不带进度段和页脚。
- 封面、目录、章节和尾页的 Logo 在左上，比内容页的大一档（高 34 逻辑像素），压在背景图之上。
- 页眉、页脚和进度段由 runtime（HTML）或构建器（PPTX）统一生成，作者只写数据属性或 page-plan，不手画。

## FLAG-05 卡片与组件
- **纸卡**（`.kzf-card`）：纯白面（`card.face`）、暖色 1px 细边、圆角 `card.radius`、三层暖影（`card.shadow`）；指针或“聚光”时浮起（`shadow_raised`）。PPTX 用单个原生外阴影（`card.pptx_shadow`）。不加任何单侧色边、通长色条或色块条（02 LG-02）。
- **卡内组件**（同一套间距与字号，作者直接组合）：
  - 卡标题 `h3`；一行导语 `p.kzf-lede`（灰字，描述这张卡在做什么）。
  - 胶囊行 `.kzf-pill`（名称 + 右侧数值）；分隔行 `.kzf-row`（名称/小字 + 右侧状态标签）；勾选行 `.kzf-check`；编号步骤 `.kzf-steps`。
  - 状态标签 `.kzf-tag.ok / risk / wait / info`（`flagship.tag`），文字必须写出状态，不只靠颜色。
  - 卡底结论 `.kzf-note`：一句话，以粗体写出要点，固定在卡底。
  - KPI 卡 `.kzf-kpi`：渐变大数字（`numeral`）+ 单位 + 名称 + 一行说明；风险数字用 `.risk`（深红）。
  - 横带 `.kzf-band`：一张横贯的卡，左侧引导块加 3–4 个分段，写“怎么用”“衔接到哪里”。
  - 流程头 `.kzf-hd`：编号 + 步骤名，相邻两头之间自动加连接点。
- **纵向平衡**（03 COPY-10 的旗舰做法）：同一排等高的卡，行项目自动分摊多余高度（上限约 62 逻辑像素一行），卡底结论贴底；行数先在文案上拉齐（同排卡行数相差不超过 1），一张卡内容明显少时补一条有信息量的行或改版式，不靠拉大行距凑高度。放不下时先删减或拆页，不缩字。
- **强调**：沿用 03 COPY-04；旗舰里常用的是加粗（`b`）、风险深红（`.kzf-risk`）、KPI 大数字和状态标签。每张内容页至少有一处有依据的强调。

## FLAG-06 动效：分场编排
- **分场**：一页的动效分成若干场（scene）。元素写 `data-kzf-fx="<fx>"` 与 `data-kzf-s="<场号>"`（默认 0），runtime 据此生成一条 GSAP 时间线；组件（three.js 场景等）写 `data-kzf-comp` 与 `data-kzf-steps`，每一步占一场。
- **编排**：同一场里，页眉各件每隔 `flagship.motion.wave.chrome_step` 秒依次出现，正文首波在 `chrome_lead` 秒后开始；正文按 fx 合并成波（同 fx 的元素一起错峰，总错峰不超过 `flagship.motion.stagger_max`），后一波在前一波时长 × `wave.share`（最多 `step_max` 秒）后开始。一场通常 1.2–2 秒；只有轨道脉冲这类贯穿动作可以更长。
- **fx 词汇**（参数在 `flagship.motion.fx`）：`rise`、`drop`、`left`、`right`、`item`、`card`、`pop`、`stamp`（印章）、`tick`（打勾）、`flip`（3D 翻牌）、`blur`、`fade`、`grow-x`、`grow-y`、`draw`（SVG 描线）、`count`（数字从 0 计到元素里写的终值；非数字如“2027Q1”改用 `fade`）、`spot`（聚光浮起）、`orbit`（沿路径的脉冲）、`sweep`（封面光扫）、`chart`（ECharts 按进度生长）、`gantt`（甘特按进度生长）、`three`（3D 场景步骤）。舞台组件不写 fx，写 `data-kzf-comp` 与步骤（FLAG-06a）。
- **放映**（06 MOTION-09，经 `KZHTMLPPT.bind`）：
  - 有人值守（按键或点击翻到本页）：先播第 0 场；每按一次 → 播下一场；播放中再按 → 先把当前场放完；最后一场之后 → 翻页。
  - 无人值守（深链、首次打开、自动放映）：各场依次播完一遍并停在终态。
  - ← 在本页退回上一场；从后一页退回时直接显示终态。
- **静止与终态**：系统“减少动态”、打印、上游 `?preview` 与 QC 参数 `?kzf-final` 直接显示终态；时间线只在播放时运行，three.js 只在时间线更新时渲染，没有空转循环。
- **库**：GSAP 3.15（`assets/vendor/gsap.min.js` 及 DrawSVG、MotionPath、CustomEase 插件，GSAP Standard License，免费可商用；不得用于与 Webflow 竞争的无代码可视化动画工具）；three.js r187 + pmndrs postprocessing + N8AO，打成一个本地 IIFE 包 `three.bundle.min.js`（MIT / Zlib / CC0；维护者用 `tools/vendor3d` 构建）。许可与来源见 `assets/vendor/*-NOTICE.txt`。

### FLAG-06a 舞台组件库（MUST）
舞台组件是一页的视觉主角，按场推进，全部是电影化 three.js 舞台。它和常规轨演示形式（15 DEMO-02，KZDemo 平面信息图逐场揭示）的分界由下面三条判定，每个旗舰组件三条都要满足；只是平面图形加逐场揭示的画法归常规轨，不进旗舰库：
1. **景深与光影**：真实的三维体量、材质（玻璃、虚影、发光）、投影，不是平面图形加阴影。
2. **跨场持续的载体**：同一批对象从第一场走到最后一场，在场与场之间变形、移位、分组，不是每场换一张图。
3. **机位运动**：至少一场有推、拉、环绕或跟随镜头。

全部在 `runtime/kz-flagship-stages.js`，登记在 `tokens.flagship.stages.catalog`（组件名、适用内容 job、分场步骤、数据字段），运行时与 `qc_plan.py` 只认这一处；图库 `examples/motion/flagship/index.html` 每个组件一页，可逐场播放。

| 组件 | 适用内容 | 分场步骤 | 数据（`data-kzf-data`） | 载体与镜头 |
|---|---|---|---|---|
| `platforms` | 到位与完成度 | rise · fill · miss · orbit | `groups: [{name, due, got}]` | 每组一块平台、每份一块砖，缺口为红色线框；环绕 |
| `rings` | 到位与完成度 | rise · fill · focus · orbit | `items: [{name, done, total}]`，`center?` | 同心圆环按完成度扫满；倾转 |
| `morph` | 到位与完成度、数量对比 | pile · split · gaps · orbit | `unit, groups: [{name, due, got}]`，due 合计 ≤160 | 一份一块方块：堆成总量 → 飞向各组立成柱 → 缺口飞入缺口盘；拉远再绕到侧面 |
| `towers` | 数量对比 | rise · grow · focus · orbit | `unit, items: [{name, value, focus?}]` | 圆角柱长到数值，重点柱留亮；环绕 |
| `stream` | 逐级转化与流失、流程与路径 | build · flow · focus · travel | `unit, stages: [{name, value}]`，逐级不增 | 粒子穿过各级闸门，流失的在闸门前落成计数堆；沿通道跟拍 |
| `layers` | 关系与汇聚、流程与路径 | stack · explode · fill · focus | `focus?, layers: [{name, note?, items?}]`，3–5 层、每层 ≤4 个短词 | 玻璃层叠起后分层展开，内容落位，重点层抬起；侧移 |
| `runway` | 时间与里程碑 | track · flags · run · focus | `now, nowLabel?, items: [{when, name, owner?}]` | 轨道从起点铺开，进度条与光标走到当前；镜头从起点拉远、再跟随 |
| `constellation` | 关系与汇聚 | hub · nodes · links · pulse | `hub: {name}, nodes: [{name, weight?}]` | 中心与各方，连线长出、脉冲送达；环绕 |
| `ghost` | 前后变化 | before · after · delta · orbit | `unit, from, to, items: [{name, before, after, good: up\|down}]` | 前值是玻璃虚影，后值实体长在里面，箭头与升降按好坏着色；每项各自刻度（分开的底座）；环绕 |
| `safety` | 安全性汇总 | set · overall · cascade · rest · diff · focus | 安全性场景族合同（同 `safety-overview` 模板，需要 `runtime/kz-clinical.js`）：`arms: [{name, n, role}], rows: [{key, label, short?, values, parent?}], focus?, flag_pp?` | 玻璃台面上两组的三维蝴蝶条，下级类别从 TEAE 条里分出并滑到各自行，差值列超阈值标红；镜头倾向重点行、该行抬起 |
| `program` | 时间与里程碑 | rails · phases · today · milestones · focus | 临床开发计划合同（同 `program-plan` 模板，需要 `runtime/kz-clinical.js`）：`from, to, today?, lanes: [{key, name, note?, bars: [{key, phase, start, end}], milestones?: [{key, at, label, kind?}]}], focus?` | 宽舞台（catalog `wide: true`，占满正文）：玻璃台面上一条泳道一条轨，阶段块按时间长出、阶段越后越高；当前面扫到当前季度、镜头跟随，之后的部分磨砂成计划；里程碑钉落到阶段块上（已过深色、未来暖色）；镜头平移向重点泳道 |
| `landscape` | 竞争格局 | set · stage · map · ideal · focus | 竞争格局合同（同 `landscape` 模板，需要 `runtime/kz-clinical.js`）：`stages?, efficacy?, safety?, assets, focus?` | 每个药物是一枚玻璃筹码、越接近上市越高（本品品牌橙、竞品 comparator）；先按阶段沿前沿排开，再滑到疗效（右）× 安全性（前）场地，无数据的进左侧托盘；理想区亮起；镜头落到重点药物 |
| `efficacy` | 有效性汇总 | set · effects · ns · focus | 有效性汇总合同（同 `efficacy-summary` 模板，需要 `runtime/kz-clinical.js`）：`arms: [{key, name, n, role}], rows: [{key, label, tier?, unit?, type: continuous\|binary\|tte\|rate, effect?, better, values, vs}], focus?` | 宽舞台，一个终点一条轨道，一节一轴（均值差、率差、比值）从后到前；所有效应转成“有利方向朝右”（比值取对数）：每节一面参考值玻璃墙（0 或 1），各治疗组效应条从墙上长出（CI 不跨参考值且有利为治疗色、方向不利为红、跨参考值为磨砂玻璃），95% CI 是条上方的细轨，右列写真实估计值（比值前写 HR / OR / RR / 率比）；effects 一场里各节依次展开；CI 跨参考值的终点抬起；镜头转向重点终点 |
| `soa` | 访视流程 | set · periods · treatment · sections · focus | 访视流程合同（同 `soa` 模板，需要 `runtime/kz-clinical.js`）：`visits: [{v, week, period?, window?}], events?: [{at, label, kind}], bands?: [{label, from, to, kind, text?}], rows: [{section} \| {item, at}], focus?` | 宽舞台，一个访视一列、一个分组一条轨道：分期色板滑到所属访视下；前沿长出给药与治疗时段条（研究药物、背景治疗、补救…），主要终点访视立起一根淡色玻璃柱穿过各轨道，其他关键节点在前沿标名；各分组在每次访视叠起硬币（一枚 = 一个评估项目）；重点项目的访视落下标针，镜头转向该分组；不画每次访视评估数 |
| `trialflow` | 研究设计与流程 | set · shared · random · arms · sub · end · focus | 试验流程合同（同 `trial-flow` 模板，需要 `runtime/kz-clinical.js`）：`trunk?, split: {at, label?, ratio?}, arms: [{key, name, n?, segs, split?}], after?, endpoints?, subs?, focus?` | 宽舞台，一个治疗分支一条轨道、周数分段线性：共同阶段立成横跨各轨的厚板；随机化圆台落下、玻璃杆分到各组；各组段落沿轨道长出（递增低而浅、维持高而深、安慰剂石墨色）；再随机化的组有自己的圆台与子分组；终点标针落到前沿、共同随访与子研究色带；镜头转向重点组 |
| `exposure` | 暴露与样本量 | set · any · longer · total · focus | 暴露例数汇总合同（同 `exposure-summary` 模板，需要 `runtime/kz-clinical.js`）：`bands: [{key, label}], groups: [{key, name, note?, values, py?}], targets?, focus?` | 玻璃台面上一个适应症一行：任何暴露是长而低的板，更长的时长档逐级叠成更短、更高、更深色的台阶（长档是短档的子集）；合计在台面旁长成塔柱、目标面出现（达到为绿、未达为红）；镜头转向重点行、该行抬起 |

- **按内容选**：先定这一页要说的是哪类内容（job），再在同 job 的组件与版式里选；同一类内容至少有两种画法可换：研究设计与流程（`trialflow` / `flag-flow`；PPTX 用 `flag-trialflow`）、竞争格局（`landscape` / `flag-chart`；PPTX 用 `flag-landscape`）、有效性汇总（`efficacy` / `flag-chart`；PPTX 用 `flag-efficacy`）、访视流程（`soa` / 静态 `soa` 表；PPTX 用 `flag-soa`）、暴露与样本量（`exposure` / `flag-chart` 合计柱图）、到位与完成度（`platforms` / `rings` / `morph` / `flag-chart`）、数量对比（`towers` / `morph` / `flag-chart`）、流程（`stream` / `layers` / `flag-flow`）、时间（`runway` / `program` / `flag-gantt`；临床开发计划用 `program`）、关系（`constellation` / `layers` / `flag-cycle`）、前后变化（`ghost` / `flag-chart`）、逐级流失（`stream` / `flag-chart`）、安全性汇总（`safety` / `flag-chart`）。
- **轮换**：相邻两张舞台页不用同一组件（续排写 `continues: true` 除外）；一份 deck 有 3 张及以上舞台页时至少用 3 种组件；内容页 ≥4 张时，每 3 张内容页至少 1 张舞台页或图表页，不让整份 deck 只有卡片。page-plan 每张舞台页写 `stage: {component, job}`，`qc_plan.py` 查 FLAG-STAGE、FLAG-STAGE-ADJACENT、FLAG-STAGE-VARIETY 与 FLAG-STAGE-MISSING。
- **数据真实**：舞台上的数字（合计、占比、缺口、流失、升降）由组件从 `data-kzf-data` 算出，不在页面里另写；同一组数字在侧栏 KPI 里出现时取同一份数据。舞台写 `role="img"` 与完整的 `aria-label`（把数据说成一句话），屏幕阅读与打印都能得到全部信息。
- **宽舞台**：catalog 写 `wide: true` 的组件（长时间轴，如 `program`）单独占满正文，不与 KPI 或清单卡分栏；需要的说明放讲稿或下一页。
- **步骤**：`data-kzf-steps` 只取该组件 catalog 里的步骤，按需删减（至少保留第一步与数据成形的那一步），顺序不变；每步占一场，`data-kzf-s` 写第一步所在的场。未知步骤与非法数据在运行时直接报错。
- **画面**：所有组件共用一个 WebGL 渲染器与后期链，逐帧复制到各自的画布，所以一份 deck 可以放任意多个舞台；只在时间线推进时重绘。质感来自 `flagship.three`：透明底叠在页面画布色上（背景不过色调映射）、暖色柔光箱环境贴图给反射、带清漆的物理材质、N8AO 环境光遮蔽与接触阴影、SMAA 抗锯齿、Khronos PBR Neutral 色调映射（保住品牌橙）。运动中画运动档；停下 `refine_ms` 后，可见的舞台按 `refine_frames` 帧固定次序的亚像素抖动累积重渲一帧精修档（同一时刻结果相同，完成后标 `data-kzf-refined`），截图与 QC 等这个标记。缺口、待定一类“空”的部分用磨砂亚克力加描边表达，不用透射玻璃（透明底下透射玻璃后面没有可折射的东西，看起来是空白）。舞台里的文字是朝向镜头的标签，忽略深度、画在玻璃之上，不被前面的物体挡住。舞台直接放在画布上，不再套卡片。
- **新增组件**：先对照上面三条判定它属于旗舰还是常规（只满足平面揭示的，加到 15 DEMO-02）；属于旗舰的在 `stages.catalog` 登记，再在 `kz-flagship-stages.js` 用 `define(name, make)` 实现（步骤与 catalog 一致、数据校验、终态可 seek、不靠回调显隐、`dispose` 释放资源），图库加一页，维护仓库的回归测试核对三处一致。

## FLAG-07 hero 构图
- **封面**：背景是封面主视觉（FLAG-03）。左上依次是场合引导（`cover_kicker`）、两行标题（`cover_title`）、渐变短横线（`rule`）、一句引言（`cover_lede`，写主结论，数字来自材料）、章节标签（`cover_chip`，01–0N），左下是部门与日期。右侧只留给主视觉，不放大图标块或数据卡。
- **目录**：左上 Logo，“CONTENTS”与标题，下方一排章节卡（2–`max_toc` 张）：图标、立体大编号、章节名、一行说明。
- **章节**：左侧是立体巨号章节数字（`section_numeral`），右侧是章节引导、章节名、一句引导和本章要点列表（当前章加亮）。
- **立体编号**（目录与章节共用，`flagship.numeral`）：渐变正面 + `extrude` 五层逐层加深的硬投影（每层 `extrude_step_em`，上限 `extrude_step_max_px`，巨号也不出台阶）+ `ground` 落地软影。HTML 由 `kz-flagship.js` 把数字包进 `.kzf-num-face`，深度滤镜挂在内层，入场的模糊滤镜只动外层；内层右侧留 `pad_em` 并以负外边距抵消，字形右缘不被渐变裁掉（字距不得为负）。PPTX 文字只允许一个效果：原生渐变填充 + 一层近硬投影（`pptx_depth_em`，上限 `pptx_depth_max_px`），数字保持可编辑文字。
- **尾页**：居中大字“谢谢”（`ending.text`，固定，不放决定事项或待确认事项），下面一条渐变短横线、汇报标题和部门日期。

## FLAG-08 内容页版式库
正文区在页眉与页脚之间（`geometry.body_top`、`body_bottom`），宽屏时横向铺满。page-plan 的 `template` 取下列 id；相邻内容页不重复同一版式，连续三页同一版式是错误（13 BODY-03，`qc_plan.py` 检查）；每页至少一种视觉载体（图标、编号、状态标签、图表、表格、示意图或 3D 场景），不做纯文字页。

| template | 结构（HTML 类名） | 适合 | 动效编排参考 |
|---|---|---|---|
| `flag-cols` | 2–4 张并列卡 + 底部横带（`.kzf-cols.kzf-rows2`，`--n`） | 范围、分组、对比 | 场 0 卡与行，场 1 状态印章，场 2 横带 |
| `flag-flow` | 4–6 个流程头 + 每步一张卡 + 横带（`.kzf-flow`） | 步骤、流程、方法 | 场 0 流程头与连接点，场 1 卡与行，场 2 勾与印章，场 3 横带 |
| `flag-stage` | 左侧舞台组件 + 右侧 KPI 或清单卡列（`.kzf-split` + `.kzf-stage`，FLAG-06a） | 按组件的适用内容：到位、对比、流程、关系、变化 | 每个组件步骤一场，侧栏随后 |
| `flag-chart` | 左侧图表卡 + 右侧 KPI 与清单（`.kzf-split` + `.kzf-chart-card` + `.kzf-stack`） | 数据对比、趋势 | 场 0 卡，场 1 图表生长，场 2 KPI 与清单 |
| `flag-gantt` | 左侧甘特卡 + 右侧关键节点与里程碑（同上，甘特） | 计划、排期 | 同上 |
| `flag-cycle` | 中心 KPI + 环形节点 + 弧线与脉冲（`.kzf-cycle`） | 闭环、循环机制 | 场 0 中心，场 1 节点，场 2 弧线描出，场 3 脉冲环绕 |
| `flag-safety` | **仅 PPTX**（FLAG-12）：蝶形纸条卡 + 右侧洞察页签 | 安全性总览（治疗组对对照组） | 场 0 卡头，场 1 纸条擦入，场 2 页签 |
| `flag-safety-dumbbell` | **仅 PPTX**：主张列 + 画布上的哑铃点图 | 安全性组间差、需要一个主张数字时 | 场 0 主张与图头，场 1 点图，场 2 要点 |
| `flag-program` | **仅 PPTX**：泳道卡（棱面箭头阶段条、棱面宝石里程碑）+ 洞察页签 | 多适应症开发计划 | 场 0 轴与当前线，场 1 泳道逐条擦入，场 2 页签 |
| `flag-program-strip` | **仅 PPTX**：同上，阶段画成凹槽里的立体纸条 | 同上（换形，避免与相邻甘特同形） | 同上 |
| `flag-exposure` | **仅 PPTX**：适应症行卡（凹槽里按时长档叠起的阶梯纸条 + 例数与人年列 + 合计行）+ 右侧目标卡（每档合计大数字、带目标刻度的凹槽量尺、达到 / 差额标签）+ 洞察页签 | 暴露例数汇总、对照 ICH E1 等暴露目标 | 场 0 卡头与列头，场 1 行擦入，场 2 目标卡，场 3 页签 |
| `flag-exposure-plan` | **仅 PPTX**：累计暴露阶梯图卡（按开发计划逐个研究累计，ICH E1 目标线、编号的各适应症 NDA 竖线、NDA 时累计圈出、首次达到）+ 右侧 NDA 达标卡（每个适应症编号、名称、NDA 时间，每个目标档一行：例数与“达到 / 差 N”标签）；不带页签，小结写进讲稿 | 领导层看各适应症 NDA 时能否满足 ICH E1；数据与开发计划甘特同一份（program 的研究条带 `exposure`） | 场 0 卡头，场 1 阶梯图擦入，场 2 达标卡 |
| `flag-trialflow` | **仅 PPTX**：研究流程卡（周轴分段线性 + 终点宝石；共同阶段是横跨各行的高纸板；随机化圆片 R + 比例与分叉脊线；各组段落是凹槽里的立体纸条；再随机化的组有自己的圆片与子分组；子研究虚线胶囊）+ 洞察页签 | 研究设计、随机化与再随机化、随机撤药、剂量递增 | 场 0 卡头与周轴，场 1 共同阶段、随机化与各组，场 2 随访与子研究，场 3 页签 |
| `flag-landscape` | **仅 PPTX**：竞争格局卡（每个药物一行，本品着色；研发阶段是填到当前阶段的棱面箭头；有效性与安全性各一列凹槽纸条，最佳值深橙，无数据写“—”）+ 洞察页签 | 竞品格局、研发进度与疗效/耐受性对比 | 场 0 卡头与表头，场 1 各行擦入，场 2 页签 |
| `flag-efficacy` | **仅 PPTX**：有效性汇总卡（各组列头含 n；连续变量与二分类各一段、各自一条含 0 的差值轴；每个终点一行：层级标签、名称与单位、各组数值（二分类写 % 与 n/N）、每个治疗组一条从 0 伸到差值的凹槽纸条与 95% CI 须线，CI 跨 0 为白色虚线纸条、方向不利为深红；右列差值（95% CI）与 P）+ 洞察页签 | 主要与关键次要终点、剂量间比较 | 场 0 卡头与列头，场 1 各行擦入，场 2 页签 |
| `flag-soa` | **仅 PPTX**：访视流程卡（分期是覆盖其访视列的棱面箭头，访视名与周次；主要终点访视整列淡底；关键节点行——主要终点为强调宝石、随机为宝石、其余为小圆点，各带名称；每个给药 / 治疗时段一根扁平条，从起始访视到结束访视并写说明；评估项目逐项列出，分组名在左侧单列，每次访视一个扁平圆点，重点项目行着色、其主要终点访视的点为宝石）；不带洞察页签，要点写进讲稿 | 何时入组随机、何时评估主要终点、给药期与背景治疗覆盖哪些访视、哪个访视做哪些评估；`sections` / `items` 选本页内容（带关键节点与三段时段时约 9 项），逐项全表用静态 `soa` 表 | 场 0 卡头、分期与访视，场 1 关键节点与时段，场 2 评估项目擦入 |

- **密度**：对齐 METRIC 的信息密度：一张内容页通常 3–6 张卡、12–30 个行项目或一张图加 6–10 个行项目；材料确实少时选卡少的版式（如 `flag-cols` 用 2 张卡、`flag-cycle`），不要用撑满的空卡凑版面。
- **侧栏**：`.kzf-split` 的侧栏宽度写 `--side`（逻辑像素，默认 330–360）；侧栏用 `.kzf-stack` 时，最后一张卡分摊剩余高度。
- **新版式**：需要表中没有的结构时，用同一套卡与组件组合，并在交付说明里写明；需要新的舞台画法时按 FLAG-06a 的“新增组件”登记。

## FLAG-09 HTML-PPT 旗舰
- **起点**：仍从 html-ppt-skill 脚手架起步，接入方式同 `adapters/html-ppt.md`：单位、生命周期，不另做放映器。`body` 写 `class="kz kzf"`、`data-fit="fluid"`、`data-kzf-title="<汇报标题>"`。
- **加载顺序**：上游 runtime.js → `assets/vendor/` 的 echarts、gsap、DrawSVGPlugin、MotionPathPlugin、CustomEase（有 3D 场景时加 three.bundle.min.js）→ `kz-tokens.js`、`kz-icons.js`、`kz-charts.js`、`kz-gantt.js`、`kz-clinical.js`（临床场景族的数据合同，与静态模板同规则）、`kz-flagship.js`、`kz-flagship-stages.js`（舞台组件，FLAG-06a）→ `adapters/html-ppt-bridge.js` → 数据与 Logo → `KZFlagship.mount(deck, {logo, data})`。样式加载 `runtime/kz-flagship.css`。
- **页面标记**：页型写 `data-kzf-kind`（cover / toc / section / content / ending）；内容页页眉写 `data-kzf-kicker`（“02 资料完整性”，数字进徽章）、`data-title`、`data-kzf-chips="a|b"`；正文放在 `.kzf-body` 里并加版式类。
- 接口见 runtime/API.md 的 KZFlagship 一节；参考实现：`examples/reference/htmlppt-flagship/`（`build.py` 生成 13 页）。

## FLAG-10 PPTX 旗舰配套
- **路线**：仍经 ppt-master（`tracks-pptx.md` 与 `adapters/ppt-master.md`）。
- **背景**：封面用 `flagship-cover`，其余页用 `flagship-canvas`（或同参数的 `tools/flagship_canvas.py` 渲染图），作为整页背景图。
- **chrome**：页眉、Logo、标签、进度段与页脚按 FLAG-04 用原生对象绘制（棱面图标块为两块原生自定义形状 + 高光层 + 白色图标，橙色棱面带单个外阴影）。
- **卡片**：原生圆角矩形，白面、暖色细边、单个原生外阴影（`card.pptx_shadow`）；卡内组件按 FLAG-05 的样式用原生形状与文本框绘制；图表与甘特用原生图表与形状（05、08）。3D 场景在 PPTX 中用一张同数据渲染的静态图（登记来源），或改用 `flag-chart` 版式。
- **动效**：沿用 06 MOTION-07（淡入、错峰、图表擦入）；按 FLAG-06 的场序分组点击触发，页面转场用淡入淡出。
- **验收**：同常规 PPTX，包括检查器、交付检查、OOXML 回读，以及 PowerPoint 编辑保存回读。参考实现：`examples/reference/pptx-flagship/`；临床模板见 `examples/reference/pptx-flagship-clinical/`（FLAG-12）。

## FLAG-11 验收增补
在 10 的门表中按下列内容填写：
- **G0**：写明所选路线和 FLAG-01 的判定理由。
- **G1**：每页官方 Logo 哈希一致；内容页页眉、进度段、页脚齐全且页码正确；封面与尾页没有页脚；尾页为“谢谢”。
- **G2**：`qc_plan.py` 在 `route: flagship` 的 page-plan 上无错误。
- **G5**：三档视口（1280×720、1920×1080、2560×1080 或更宽）下卡内文字不溢出、无孤字行、无通长边条；同排卡纵向平衡；宽屏铺满；每张内容页有强调。
- **G7**：无人值守进入时各场播完并停在终态；有人值守时逐场推进、播放中按键先放完当前场、← 退回上一场、从后一页退回显示终态；减少动态与打印显示终态；连续翻页无脚本错误；每个舞台组件画出内容、步骤数与 catalog 一致、全部 3D 舞台只占一个 WebGL 上下文。证据：在正例与组件图库上逐项检查。
- **G9**：在 Edge 或 Chrome 中逐页放映；PPTX 在 PowerPoint 中回读。

## FLAG-12 旗舰 PPTX 正文语言 L1「层叠纸板」
旗舰 PPTX 不模仿 three.js 舞台，按 PowerPoint 原生能力单独立一套正文语言（用户 2026-11-18 在三套样张 L1 层叠纸板、L2 棱面几何、L3 编辑版式中选定 L1；开发计划的阶段条取 L2 的棱面箭头；L3 的安全性哑铃图保留为备选模板）。参数在 `tokens.flagship.pptx_l1`，组件在 `tools/kz_layouts/flagship_pptx.py`。

- **数据是立起来的纸条**：凹槽底轨（`groove`）+ 上浅下深的渐变条面（`strip_top`）+ 一个原生投影（`strip_shadow`）。数值、标签都是可编辑原生文本。
- **卡片下衬错位底纸**（`sheet`、`sheet_offset`）：主卡一张，其余卡只用 FLAG-05 的白纸卡与单个外阴影，不层层叠纸。
- **里程碑是双色棱面宝石**（`gem`、`gem_r`）：已发生左浅右深实心，计划中空心描边，风险用风险色，焦点里程碑加浅色光圈。
- **开发计划的阶段条是页眉棱面的箭头**（`plan_bar_h`）：同泳道相接的后一段左端内凹；当前线前实色，之后同色浅化加虚线描边；当前线是最底层的灰色虚线（`tokens.gantt.today`，08 GANTT-06）。
- **洞察页签**：白纸卡 + 立体圆形图标（渐变 `tile`、`lift_shadow`），标题取 `type_px.card_title`；洞察写了 `row` 时页签底部给出两组率的大号数字。
- **十个模板**（只用于 PPTX；HTML-PPT 旗舰用舞台 `safety` / `program` / `exposure` / `trialflow` / `landscape` / `efficacy` / `soa`，`qc_plan.py` 报 FLAG-TEMPLATE）：`flag-safety`（默认）与 `flag-safety-dumbbell`、`flag-program`（默认）与 `flag-program-strip`、`flag-exposure`、`flag-exposure-plan`、`flag-trialflow`、`flag-landscape`、`flag-efficacy`、`flag-soa`。同一族两种画法用于防止相邻页同形；数据合同与静态模板相同（`safety_model`、`program_model`、`exposure_model`、`trialflow_model`、`landscape_model`、`efficacy_model`、`soa_model`）。
- **暴露阶梯**（`flag-exposure`）：累计时长档从浅到深叠在同一凹槽里（长档是短档的子集，所以越深越短，形成台阶）；列头色块与条面同渐变；合计达到目标用绿色、未达用风险色；目标卡每档一行，量尺刻度是目标值，标签写“达到”或“差 N”。
- **研究流程**（`flag-trialflow`）：周轴分段线性（每段至少 92 px，短的筛选期不被压扁），段落色取 `tokens.charts.flow`（递增浅橙、维持深橙、安慰剂 comparator、开放标签类别色第 2 位、非治疗浅灰虚线）；段名必须放进纸条内，放不下报错；随机化标签压到时间轴时报错。
- **竞争格局**（`flag-landscape`）：本品纸条用 treat 渐变、竞品用 comparator 渐变；表头写指标名、单位与 ↑/↓（放得下时加“越高/越低越好”）；竞品只用合成或经核实的公开数据，页面胶囊写明“跨研究比较”。
- **有效性汇总**（`flag-efficacy`）：旗舰页只放主要与关键次要终点（一页约 4 个，带洞察页签时），完整终点列表留给静态模板 `efficacy-summary` 或附表；差值轴每段各自含 0，治疗组纸条用 treat 由浅到深（剂量顺序），P 值照数据原样写（名义值在脚注说明）。
- **访视流程**（`flag-soa`）：页面回答“何时入组随机、何时评估主要终点、给药与背景治疗覆盖哪些访视、哪个访视做哪些评估”，不画每次访视的评估数；关键节点（`events`）与给药 / 治疗时段（`bands`）来自 SoA 合同；需要强调的数据点只做标记（主要终点列淡底、重点项目的宝石），汇总与解读写进讲稿；逐项全表交给静态模板 `soa`（按访视分页、每页重复关键节点、时段、项目列与脚注）；分期色取阶段色带，分组色取类别色序。
- **容量**：放不下时报错而不缩字——`flag-safety` 行高 <36、`flag-safety-dumbbell` 行高 <34、计划泳道高 <50、`flag-exposure` 组行高 <40 或目标卡每档 <76、`flag-trialflow` 分支行高 <44、`flag-landscape` 行高 <34、`flag-efficacy` 终点行高 <44 或差值图宽 <200、`flag-soa` 访视列宽 <56 或评估项目行高 <24 时要求拆页、收起上级泳道或换模板；全为 0 的行不画条，自动写进脚注（“无导致死亡的 TEAE”）。
- **字号**：正文 ≥16 px（12 pt）；轴刻度、图例、里程碑与差值标签 14 px，只在图内（组标 `data-kz-emphasis="not_applicable"`）。
- **装配**：根层网格、当前线、底纸与面板是带 id 的 decoration 图元；模块组互不重叠（泳道按带分区，轴与当前线标签各自成组）。参考实现：`examples/reference/pptx-flagship-clinical/`（九个模板各一页）。
