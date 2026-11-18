# 公开装配接口

本页描述当前实现的可调用接口，不新增设计阈值；数值在 tokens，规则在 design_specs。所有文件使用 `.kz` 作用域与 `window.KZ*` 名称。加载顺序：`kz-tokens.css` → `kz-glass.css`；脚本（HTML-PPT 先加载上游 `runtime.js`）→ `echarts.min.js`（用到图表或甘特时）→ `kz-tokens.js` → `kz-motion.js` → `kz-charts.js` /（用到甘特时）`kz-icons.js` → `kz-clinical.js` → `kz-gantt.js` → `kz-gantt-studio.js` / `kz-drilldown.js` →（临床交互图时）`kz-explore.js` →（HTML-PPT）`adapters/html-ppt-bridge.js` → 项目装配 → `kz-audience.js`。`kz-layout-qc.js` 只在验收时注入。

`kz-audience.js` 是观众端策略：移除残留的播放、暂停、重播、进度控件（含后续动态插入的），不接管导航。

## CSS
| 类 / 属性 | 作用 |
|---|---|
| `.kz-card` | 玻璃卡：三停面 + rim + 短高光 + 动态三层阴影（读 `--kz-lx/--kz-ly/--kz-lift/--kz-mx/--kz-my`） |
| `.kz-thin` | 卡内薄覆层（`--kz-elev-thin`）；表单字段内凹影用 `--kz-elev-inset` |
| `[data-kz-tilt]` / `[data-kz-light]` | 由 `mountTilt` 驱动：倾斜 + 光 / 只有光与抬升；`data-kz-tilt="6"` 指定上限（≤ hero 上限） |
| `[data-kz-no-tilt]`、`.kz-chart`、`.kz-gantt` | 测量面不倾斜 |
| `[data-kz-reveal]` | 入场目标；`data-kz-order` 指定顺序；内部 `h2/h3`（标题档）与 `li`、`tbody tr`、`[data-kz-reveal-item]`（条目档）级联；含 `.kz-takeaway-card` 或带 `data-kz-takeaway` 的目标最后出现 |
| `[data-kz-section]` | 首屏以下段落，`mountSections` 首次可见时入场 |
| `.kz-float`（`--kz-float-index` 错相）/ `.kz-mark-float` | hero 卡浮动 / 双菱形浮动 |
| `.kz-optical-field` | 程序化环境光场，`mountField` 驱动视差 |
| `.kz-fold` `.kz-fold-head` `.kz-fold-grid` `.kz-fold-lead` `.kz-fold-stage` `.kz-fold-stage-head` | Bento 首屏（13 FOLD-02） |
| `.kz-kpis` `.kz-kpi` `.kz-number` `.kz-unit` `.kz-kpi-label` `.kz-kpi-note` | KPI 卡 |
| `.kz-steps` `.kz-step[data-state=done|current|todo]` `.kz-step-mark` | 状态条 |
| `.kz-detail-tall` | 可视区高度 ≥ `layout.fold.tall_detail_min_height_px` 才显示的次要说明 |
| `.kz-site-head` `.kz-brand` `.kz-site-meta` | 站点与流式的固定玻璃页眉（13 WIDE-01）：Logo + 站点名或面包屑、导航、元信息一行 |
| `.kz-stream` `.kz-stream-rail` `.kz-rail-kicker` `.kz-stream-main` `.kz-stream-chapter` `.kz-stream-wide` | 流式两栏：目录轨 + 宽正文栏，没有右侧栏（13 FOLD-05）；`.kz-stream-wide` 并排图表与说明卡 |
| `[data-span-xl]` `[data-kz-xl-only]` | 视口 ≥ `wide.xl_min_vw` 时 24 栏网格中的块宽 / 只在超宽屏显示的块 |
| `--kz-sx` `--kz-gutter` `--kz-site-head-h` `--kz-logo-h` `--kz-stream-rail` `--kz-stream-measure` | 宽屏变量（tokens.wide 生成）；`--kz-sx` 是随宽度放大的 1px，写法 `calc(18 * var(--kz-sx))` |
| `.kz-film` `.kz-film-stage` `.kz-film-carrier` `.kz-film-carrier-label` `.kz-film-caption` `.kz-film-links` | 电影结构 |
| `[data-kz-layout=centered|distributed]` + `.kz-card-reading` | 卡内纵向模式 |
| `.kz[data-kz-frozen=true]`、`.kz-background-paused`、`[data-kz-motion-active=false]` | 冻结、后台、非活动页暂停浮动 |

## KZMotion
- `mountPage(root)` → `{enter, leave, finish, dispose}`：收集 root 内的 `[data-kz-reveal]` 与 `[data-kz-tilt],[data-kz-light]`；enter 按 06 MOTION-04 编排入场，leave 加速退出（forwards）。同一 root 或目标不能重复挂载；mountPage 已包含 root 内的指针倾斜，不要再对同一 root 调 `mountTilt`（会抛错）。
- `reveal(root, {exit})` → `{finished, cancel}`：不经 mountPage 的单次编排；退出后保留句柄，复入或换驱动者前调用 `cancel()`。
- `mountTilt(root)` → `{dispose}`：弹簧驱动指针光源、抬升与倾斜；鼠标以外的指针、选字、编辑、冻结、减少动态时复位。
- `mountSections(root=document, {selector, threshold})` → `{finish, dispose}`：首屏以下段落首次进入视口时 `reveal`；打印或切到减少动态时全部显示（打印样式另有 CSS 兜底）。单个段落入场出错时报告错误并显示该段，不影响同批其他段落。
- `mountField(root=document)` → `{dispose}`：环境光场随滚动位移（限幅）。
- `fitFold(fold)` → `{check, dispose}`：首屏容量守卫。`.kz-detail-tall` 在媒体查询允许时先显示，若首屏左栏或舞台的布局底边越出视口，按文档倒序逐个加 `data-kz-fit=overflow` 收起，直到放下；尺寸变化与字体加载后重算。按布局偏移测量，入场位移不算越出。
- `countUp(el, {to, from=0, decimals=0, duration})` → `{play, seek(p), finish, progress, dispose}`：终值写入 `aria-label`；减少动态或后台时直接终值。
- `storyboard(states, opts)` → `{frames, duration, holds, enterAt, closeAt, sceneAt, phaseAt(p), staticProgress}`：每个 state 为 `{label, caption, facts?, geometry:{x,y,w,h,r}, tint?}`；输出合法、首尾一致的 Film 关键帧与业务阶段映射。`opts` 默认取 `motion.film.storyboard`，另可传 `staticState`（静态帧所用状态的序号）。`phaseAt` 与 `sample` 用同一采样；把 `staticProgress` 传给 `new Film`，减少动态、打印与 `?preview` 才会停在停留段而不是移动途中。
- `drawLinks(svg, pairs)`：`pairs=[{id, from:Element, to:Element, progress}]`，按实时矩形画三次贝塞尔连线，`progress` 决定描绘长度；在 Film `onRender` 中调用即可随载体变形。
- `new Film(root, {frames, duration, onRender, managedText, staticProgress, minCarrierWidth, scenes})`：root 内须有 `.kz-film-stage` 与其中唯一的 `.kz-film-carrier`。帧 `{t,x,y,w,h,r,tint:[r,g,b,a],label,caption}`：至少四帧、t 严格递增且含 0 与 1、几何归一化且不越出舞台、r ∈ [0,0.5]、首尾几何/材质/文字一致。方法 `pause(reason)`、`resume(reason)`、`seek(p)`、`snapshot()`、`dispose()`；没有 play/reset。传 `scenes`（严格递增、落在 [0,1) 的停点，通常是 `storyboard().sceneAt`）时进入 HTML-PPT 的 scene 模式（06 MOTION-09）：从 `scenes[0]` 开始，不自动循环；另有 `scene`、`moving`、`toScene(i)`、`next()`、`prev()`、`playThrough()`，`next()`/`prev()` 返回 `true` 表示已消费。根节点 `data-kz-scene` 标出当前 scene。`onRender(frame, p, film)` 的 frame 带 `index` 与 `textAlpha`；默认模式下 runtime 写 label/caption 并设 `--kz-film-text`。构造成功设 `root.dataset.kzReady='true'`，`kzProgress` 随渲染更新。
- `sample(frames, p)`、`validateFrames(frames)`：低级函数。

## KZCharts
`mount(el, data, {onProgress, onDataClick})`；data 为 `{kind:'line'|'bar'|'column', categories, series:[{id, name, values:[number|null], color?, role?:'comparator', department?}], unit, axis?:{min,max,interval}, decimals?, area?, description?}`。返回 `chart, play(ms), finish, renderProgress(p), getData, getProgress, setData, resize, pause, resume, dispose`。折线揭示左→右描出（x 轴为 0…n−1 的数值轴，标签映射回类别）；柱形自基线错峰长出；类别色取 `tokens.charts.categorical`，按固定顺序分配给“占用类别色”的系列；自带 `color`、`role:'comparator'` 或声明了已知 `department` 的系列不占位。占用类别色的系列超过色序长度（5）时，`validate` 抛错并提示合并为“其他”或拆成小多图（7.0 起不再循环取色）。`option(data, opts)` 是低级 option 工厂。

## KZGantt
`mount(root, data, {onProgress, fill?})`，两种数据形式（08 GANTT-02）：
- **计划合同**（8.0）：`{from, to, today?, granularity?, phases?, lanes:[{key, name, note?, parent?, collapsed?, bars:[…], milestones:[…]}]}`，结构见 `schemas/program-plan.schema.json`，校验走 `KZClinical.program`（与静态模板同一规则）；时间写 `2026Q3` / `2026-08` / `2026-08-15`，修改按计划粒度写回文字。
- **7.x 季度形式**：`{min, max, tasks:[{id, label, start, end, color?, department?, row?}], rows?, milestones?, today?, legend?, taskColor?}`，整数季度序号（`KZGantt.qindex(year, quarter)`），格式见 `schemas/gantt.schema.json`；含 `start_known`/`end_known: false` 的任务直接报错。

根元素写 `data-kz-gantt="<gid>"` 且 `window.KZ_DECK_DATA[gid]` 存在时，每次修改写回该条目（翻页重挂、旗舰舞台与保存都读它），并更新同页 `[data-kz-bind]` 文字（GANTT-07）。`fill:true` 让绘图区铺满容器高度（编辑台预览用）。页内：点选、拖整条或两端（按粒度吸附，条内里程碑随动）、←/→、Shift+←/→、⌘/Ctrl+Z 与 ⇧⌘/Ctrl+Z；回车、空格或双击打开编辑台（加载了 `kz-gantt-studio.js` 时）。有修改时根元素内出现紧凑的 `.kz-dirty` 条（撤销 / 还原）与自动隐去的 `.kz-gantt-status` 提示；7.x 的内嵌表单编辑器已移除。端点命中区读 `tokens.gantt`。

返回 `chart, root, plot, gid, openEditor, renderProgress(p), select(id), play, finish, getProgress, getData, getDoc, getBaseline, isDoc, view, getSelected, getDirty, commit(start, end), undo, redo, canUndo, canRedo, reset, setDoc(doc, {message, record}), markSaved, serialize, importJSON, on(fn), geometry, pause, resume, dispose`。`view()` 是当前绘制视图 `{rows, tasks, ms, todayX, todayText, legend, gran}`；`on(fn)` 订阅 `change` 等事件，返回取消函数；`setDoc` 整体替换数据（经校验，`record:false` 不进撤销历史）；`markSaved` 把当前数据设为保存点；`openEditor(open)` 打开或关闭编辑台（未加载 `kz-gantt-studio.js` 时只给提示）。

静态工具：`validate(data)`、`fromLegacy(data)`（7.x → 计划合同）、`viewOf(data)`、`bindValue(expr, doc)`（`key`、`key.start`、`key.end`、`gap:a,b`）、`snap(x, gran)`、`step(x, gran, ±1)`、`qindex`、`fromIndex`、`qlabel`、`instances()`（当前挂载的实例）。

## KZGanttStudio（runtime/kz-gantt-studio.js，08 GANTT-01 / -05）
全页甘特编辑台。加载后在 window 上以捕获阶段监听 **T**（无修饰键、焦点不在输入框）：打开当前甘特（打开着的下钻层 → HTML-PPT 活动页 → 离视口中线最近的那个；只看在视口内的）。`open(inst, {focus})` 用某个 KZGantt 实例打开，`close()` 关闭，`isOpen()`，`state()` → `{doc, sel, message}`（测试与适配用），`noteChange(inst)` 由 KZGantt 在每次修改时调用（存草稿、刷新编辑台）。`replaceData(text, store, gid)` 是“保存到本文件”的纯函数：返回只替换了 `KZ_DECK_DATA` 数据块中改过的甘特条目的文件文本，文件不是当前页面的（无数据块、无法解析、缺当前 gid）时抛错；`pyjson(v)` 按构建器的单行 JSON 写法序列化。草稿键 `kz-gantt-draft:<路径>:<gid>`（localStorage）；文件句柄存 IndexedDB `kz-gantt`。需要 `kz-tokens.js`、`kz-icons.js`、`kz-clinical.js`、`kz-gantt.js` 先加载。

## KZDrilldown
`new Drilldown({host, onOpen, onClose})`；`push({id, title, render}, trigger)`，render 收到 `(section, drill)`，返回可选 `{pause, resume, dispose}`；`pop()`、`close()`、`snapshot()`、`dispose()`。trigger 位于 `.kz-card` 或 `[data-kz-drill-source]` 内时从该卡片展开，否则原地打开。`close()` 返回 promise：调用时状态即关闭（`snapshot().open=false`、背景隔离解除、`onClose`），折回动画结束、原生 close 并还焦点后兑现；展开中途关闭会反向折回。`snapshot().width` 用布局宽度（`offsetWidth`），不受展开动画的 transform 影响。`KZDrilldown.element(tag, cls, text)` 是用 textContent 建节点的小工具。

## KZScenes（runtime/kz-scenes.js，演示舞台 15）
`mount(root, {scenes, loop, staticScene, onScene})` → `Stage`。root 内的 `[data-kz-scene-canvas]`（没有则 root）是画布，其中每个 `[data-kz-obj="id"]` 是一个持久对象；可选 `[data-kz-scene-caption]`（说明句）与 `[data-kz-scene-rail]`（状态条，自动生成序号）。
- scene：`{id, caption, set: {objId: state}, order?: [objId…], hold?}`。状态是相对上一 scene 的增量：`x y w h`（画布比例）、`opacity scale rotate`、`fill color stroke`、`draw`（SVG 描绘 0–1）、`count` + `decimals unit`、`text`、`attr`（数值型 SVG 属性）、`cls`（类名开关）。`from` 是首次出现前的隐藏起点，`via: [[x,y]…]` 是本次运动的途经点。对象写入 `[data-kz-obj-text]` 子节点（若有）。
- 步进模式（`loop:false`，HTML-PPT）与循环模式（`loop:true`，站点）。方法同 Film 的 scene 接口：`pause resume seek scene moving toScene next prev playThrough snapshot dispose`，另有 `stops`（各 scene 的进度）、`audit()` → `{scenes, objects, transitions:[{scene, changed, entered, travel, grow, caption}]}` 与 `coverage({cols, rows})` → `{cells, figures, texts}`（当前 scene 可见对象触及的画布网格比例，连线按笔画计；图形对象与文字对象的个数；15 DEMO-03）。没有任何 scene 写到的对象保持标记里的样子、可见（例如只靠 clipPath 揭示的曲线）。时长读 `motion.scenes`。
- `KZScenes.layout`：`grid(n, {box, cols, gap, valign})`、`bars(values, {box, max, gap})`、`scale(domain, range)`、`rows(n, {box, gap})`、`cols(n, {box, gap})`，都返回画布比例的矩形。

## KZIcons（runtime/kz-icons.js，15 DEMO-08）
`svg(name, {title})` → 24×24 线性图标（`currentColor` 描边，状态类改色）；`path(name)` → 该图标的 SVG path 数据（ECharts 里画里程碑图标用）；`names` 列出全部图标（来源 `assets/icons/icons.json`，`tools/build_icons.py` 生成）。

## KZClinical（runtime/kz-clinical.js，8.0 临床场景族）
临床场景的数据合同，常规演示 `kz-demo-clinical.js` 与旗舰舞台 `kz-flagship-stages.js` 共用；规则与 `tools/kz_layouts/diagram_clinical.py`（静态模板）逐条相同，报错文字也相同（维护仓库的回归测试对拍）。`safety(data)` → `{arms, rows:[{…row, depth, pct[], diff}], ti, ci, flag, focus, unit, under(row)}`：2–4 组且各有正整数 N，3–10 行，每组一个例数且不超过 N，下级不大于上级，最多 3 级，第一行是顶层类别，需要对照组（`role: comparator`）或 `compare: [组, 参照组]`。`program(data, today?)` → `{from, to, today, today_w, granularity, phases, used, layers:{status, progress, baseline, levels}, lanes:[{…lane, depth, children, bars:[{…, s, e, pi}], milestones:[{…, kind, t, tw, bt?, btw?}], summary?, summary_ms?}], visible, focus, kinds}`：计划合同（08 GANTT-02，`schemas/program-plan.schema.json`），时间换成连续季度单位的 [起, 止)（与 KZGantt 同一模型），规则同上（泳道 1–24 且同时显示 ≤12、两级泳道、阶段不重叠、里程碑 ≤6、粒度、today 与 focus 有效）。另有 `tspan(s, what)` → `[起, 止, 单位]`、`ttext(v, gran)`、`qindex('2026Q3')`（只收季度）、`qtext(i)`、`dtext(diff)`、`npct(n, pct)`、`num(v, d)`、`PHASES`、`MS_KINDS`、`STATUSES`、`GRANS`。在 `kz-tokens.js` 之后、使用它的脚本之前加载。

## KZDemo（runtime/kz-demo.js + kz-demo-patterns.js + kz-demo-fine.js + kz-demo-clinical.js，15 DEMO-02）
`mount(root, kind, data, {loop, staticScene})` → `Stage`；所有数字与说明句由 data 计算。`forms` 列出已注册形式；`define(kind, fn)` 注册新形式，`fn(root, data, opt)` 返回 Stage；`renderFacts(el, stage)` 把形式算出的 `stage.facts`（`[{value, label, risk?}]`）渲染成事实条（`demo-stack` 预设）。
`kit` 是搭建工具：`frame(root, kind, note)` 建画布与底栏，`obj(cv, id, cls, text)` 建持久对象，`icon(cv, id, name, cls)` 图标对象，`lead(node, name)` 文字前加图标（文字移入 `[data-kz-obj-text]`），`glyph(node, name, fallback)` 只放一个图标，`links(cv)` → `{svg, path(id, d, cls)}` 画布级连线层（0–1000 坐标），`pts([[x,y]…])` 折线路径，另有 `S C MUTE SOFT sum fmt el`。
- `units`：`{unit, groups:[{name, due, received}], owner, deadline, note}`
- `calc`：`{unit, rows:[{name, a, b}], aLabel, bLabel, diffLabel, note}`
- `story`：`{unit, groups:[{name, a, b}], aLabel, bLabel, gapLabel, takeaway?, note}`
- `timeline`：`{min, max, tasks:[{id, label, start, end, department}], milestone?:{at, label, flag?}, note}`，季度同 KZGantt
- `decision`：`{nodes:[{id, label, x, y, w, h?, kind:'in'|'q'|'out'}], edges:[{from, to, label?}], cases:[{id, label, detail, path:[nodeId…]}], intro, summary?, note}`
- `compare`：`{left, right, leftTag?, rightTag?, rows:[{label, left, right}], rightOrder?, tray, note}`
- `decision` 的节点可带 `icon`（KZIcons 名称）。
- `flow`：`{stations:[{id, label, icon, rule}], cases:[{id, label, detail, steps:[{at, result:'pass'|'fail', back?}]}], bins?:{accept, rework, escalate}, intro?, summary?, note}`；带 `back` 的失败退回该环节返工，不带 `back` 的失败升级
- `gantt`：`{labels:[期名…], unit, tasks:[{id, label, start, end, department, deps?:[id…]}], milestone:{label, after:[id…]}, today, todayLabel?, slip:{task, by, reason}, recover?:{task, by, action}, note}`；`[start,end)` 以期计，按依赖前推排期
- `swimlane`：`{lanes:[{id, label, icon, department}], steps:[{lane, label, days, sla}], unit, limit, caseLabel, chunks?, note}`
- `consort`：`{unit, per, screened, excluded:[{reason, n}], arms:[{name, role:'treat'|'comparator', n, lost:[{reason, n}]}], note}`；各组合计须等于随机化人数
- `curve`：`{x:[标签…], unit, series:[{name, values:[数值|null], role?}], threshold?:{value, label}, window?:{from, to, label}, events?:[{at, label}], takeaway?, note}`；`unit` 为 `%` 时差值写“个百分点”
- `breakdown`：`{unit, total:{label}, parts:[{label, value, children?:[{label, value, flag?}]}], focus?, takeaway?, note}`
- `audit`：`{title, fields:[{label, value, ok, rule?}], groups?, note}`
- `matrix`：`{x:{label, levels}, y:{label, levels}, items:[{label, at:[xi, yi], after?:[xi, yi], action?}], high, note}`
- `network`：`{nodes:[{id, label, icon, x, y}], links:[{from, to}], packets:[{label, route:[id…], blocked?:[from, to], note?}], intro?, note}`；节点坐标是网络区的比例，右侧留给数据包台账
- `schedule`：`{unit, span:[d0, d1], visits:[{label, day, window:[-a, +b]}], subjects:[{label, actual:[日|null…]}], note}`
- `waffle`：`{unit, groups:[{name, due, received}], note}`；2–6 组整数，应收合计不超过 60 份，`received ≤ due`
- `funnel`：`{unit, stages:[{name, value}], note}`；3–6 级，每级不大于上一级，第一级大于 0
- `shift`：`{unit, from, to, items:[{name, before, after, good:'up'|'down', decimals?}], decimals?, note}`；2–6 项，每项按自己的较大值定刻度；`good` 说明哪个方向算改善
- `milestones`：`{now, nowLabel?, items:[{when, name, owner?}], note}`；3–7 个节点，`now` 是走到第几个节点（0 … n−1，可带小数）
- `pathway`：`{steps:[{name, note?, icon?, alert?}], caseLabel?, note}`；3–7 步，至多一步带 `alert`（个案停在这一步并退回补齐）
- `safety`：`{unit, set?, arms:[{name, n, role:'treat'|'comparator'}], rows:[{key, label, short?, values:[每组例数], parent?}], focus?, flag_pp?(5), compare?:[组, 参照组], note}`；2–4 组、3–10 行，子类例数不大于上级，第一行须是顶层类别；舞台画比较的两组（蝴蝶图），`short` 是舞台上的短名；与静态模板 `safety-overview`、旗舰舞台 `safety` 同一份数据
- `program`：临床开发计划合同 `{from:'2025Q1', to:'2029Q4', today?, phases?, focus?, lanes:[{key, name, note?, bars:[{key, phase, start, end, label?, risk?}], milestones?:[{key, at, label, kind?:'start'|'readout'|'submit'|'approve'|'other', risk?}]}], note}`；季度写成 2026Q3、首尾都含；1–8 条泳道，同一泳道的阶段前后相接不重叠，每条泳道 ≤6 个里程碑；`focus` 须是有阶段条的泳道（或其条、里程碑的 key），只有子泳道的上级泳道不能当 focus；与静态模板 `program-plan`、旗舰舞台 `program` 同一份数据
- `exposure`：暴露例数汇总合同 `{unit?, head?, bands:[{key, label}], groups:[{key, name, note?, values:[每档例数], py?}], targets?:{档 key: 目标例数}, target_label?, focus?, note}`；2–5 个累计时长档（长档是短档的子集，例数沿一行不升），1–8 组；合计、人年合计与是否达标由 `KZClinical.exposure` 算出；与静态模板 `exposure-summary`、旗舰舞台 `exposure`、旗舰 PPTX `flag-exposure` 同一份数据
- `trialflow`：试验流程合同 `{unit?, trunk?:[{label, from, to, kind?}], split:{at, label?, ratio?}, arms:[{key, name, n?, segs:[{from, to, label, kind?}], split?:{at, label?, ratio?, arms:[子分组 2–3]}}], after?:[{label, from, to, kind?}]（随机后各组共同的后续段，最多 2 段，数组）, endpoints?:[{at, label, primary?}], subs?:[{key, name, of:[分组 key], from, to, n?}], focus?, note}`；kind 取 titrate / maintain / placebo / open / off；段落前后相接，各分组同一周结束，子分组不再分；与静态模板 `trial-flow`、旗舰舞台 `trialflow`、旗舰 PPTX `flag-trialflow` 共用（`KZClinical.trialflow`）。
- `landscape`：竞争格局合同 `{stages?:[阶段名 2–7，缺省 临床前…上市], efficacy?:{label, unit?, better:'higher'|'lower', note?}, safety?:{…}, assets:[{key, name, company?, moa?, route?, stage, efficacy?, safety?, ours?}], focus?, note}`；2–10 个药物、ours 至多一个；指标值为数字或 null（无数据，不当 0、不参与排名）；排序按阶段再按有效性；与静态模板 `landscape`、旗舰舞台 `landscape`、旗舰 PPTX `flag-landscape` 共用（`KZClinical.landscape`）。竞品只用合成或经核实的公开数据。
- `efficacy`：有效性汇总合同 `{arms:[{key, name, n, role:'treat'|'comparator'}] 2–4 组且恰一个对照, rows:[{key, label, tier?, unit?, time?, type:'continuous'|'binary'|'tte'|'rate', effect?, better:'higher'|'lower'（效应值朝哪边有利：至应答 HR>1 有利写 higher，至复发写 lower）, values:[每组 数字 | [n, N] | {median?, events?, n?}（源材料没有的不推算） | 事件率 | null], vs:{治疗组 key:{diff, ci:[lo, hi], p?}}}] 1–10 个, focus?, note}`；二分类率差（百分点）须与 n/N 一致（±0.15）；CI 不跨 0 按 better 判有利/不利，跨 0 为 ns；一节一轴：均值差、率差各一条含 0 的轴，HR / OR / RR / 率比共用一条含 1 的对数轴（`KZClinical.efTicks`）；与静态模板 `efficacy-summary`、旗舰舞台 `efficacy`、旗舰 PPTX `flag-efficacy` 共用（`KZClinical.efficacy`）。
- `soa`：访视流程合同 `{visits:[{v, week, period?}] 2–30 个（v 不重复；week 写 W/D/M 数字时须递增）, rows:[{section} | {item, at:[每个访视 1 | 0 | null | 文字标记]}]（1 = 做；0 与 null 都是不做、画成空格；1–40 个项目，分组下至少一项，≤8 组）, footnotes?, focus?:某一个项目 item 的原文全名, note}`；分期须是连续的一段访视；文字标记（如 ×2、ᵃ）算作有；算出每组各访视项目数、每次访视评估数与最忙访视（`KZClinical.soa`）；与静态模板 `soa`（逐项明细、按访视分页）、旗舰舞台 `soa`、旗舰 PPTX `flag-soa` 共用。
数据自相矛盾时形式抛错（例如分组合计不等于随机化人数、阻断通道不在路径上）。示例数据：`examples/motion/data.js`。

## KZHTMLPPT（adapters/html-ppt-bridge.js）
维护 `--kz-un` 与 `--kz-u`（adapter「单位：一个比率」）。`bind(deck, factory)` → `{sync, dispose}`：factory 收到每个上游直接子 `.slide`，返回 `{enter(info), leave, dispose, next?, prev?}`；`info = {direction:'forward'|'backward', attended}`。桥接在捕获阶段把翻页键与滑动先交给活动页的 `next()`/`prev()`，返回 `true` 时不交上游（06 MOTION-09）；总览克隆不挂载；初始化失败会清理已返回的生命周期。

## KZFlagship（runtime/kz-flagship.js，旗舰路线 F1，14）
依赖：`kz-tokens.js`、`assets/vendor/gsap.min.js`（+ DrawSVGPlugin、MotionPathPlugin、CustomEase）、有 3D 场景时 `three.bundle.min.js`（three r187 + postprocessing + N8AO 的 IIFE 包，挂 `THREE` 与 `KZ3D`）、`kz-icons.js`、用到时 `kz-charts.js`/`kz-gantt.js`、`adapters/html-ppt-bridge.js`。CSS 用 `kz-flagship.css`，`body` 写 `class="kz kzf"`。

`mount(deck, {logo, title, data})` → `{lives, state(), finishAll(), dispose()}`。它给每页加 chrome（官方 Logo、内容页页眉与标签、目录/章节/内容页的进度段与页脚），把声明的动效标记编成每页一条 GSAP 时间线，挂载图表、甘特与组件，并经 `KZHTMLPPT.bind` 接管翻页键做分场推进；完成后写 `html[data-kzf-ready="true"]`。不改上游导航、hash 与 `.is-active`。

- 页面标记：`data-kzf-kind`（cover / toc / section / content / ending）；内容页 `data-kzf-icon`（KZIcons 名称，画进左上棱面图标块 `.kzf-mark`，默认用本章图标）、`data-kzf-kicker`（“02 资料完整性”，原样显示）、`data-title`、`data-kzf-chips="a|b"`；可选 `data-kzf-template`（14 FLAG-08 版式 id，供 QC 读取）。
- 元素标记：`data-kzf-fx="<fx>"` 与 `data-kzf-s="<场号>"`（fx 词汇见 14 FLAG-06，参数在 `tokens.flagship.motion.fx`）；`count` 从 0 计到元素文字；`[data-icon]:empty` 自动填图标；`.kzf-cycle` 的节点、弧线（`data-kzf-arc-s`）与脉冲（`data-kzf-pulse-s`）由 `layoutCycle()` 生成。
- 组件：`data-kzf-comp="<名>"`、`data-kzf-steps="a,b,c"`（每步一场）、`data-kzf-data='<JSON>'`。`component(name, make)` 注册，`make(host, data)` 返回 `{step(name, tl, at), layout?(), dispose()}`（`layout` 在每次重建时间线前调用，供 SVG 组件按当前尺寸重排）；`components()` 列出已注册组件。
- 舞台组件库 `runtime/kz-flagship-stages.js`（在 `kz-flagship.js` 之后加载，14 FLAG-06a）：`platforms`、`rings`、`morph`、`towers`、`stream`、`layers`、`runway`、`constellation`、`ghost`、`safety`（8.0 安全性场景族）、`program`（8.0 临床开发计划，宽舞台），后两者需要先加载 `kz-clinical.js`；全部是 three.js 舞台（共用一个离屏 WebGL 渲染器，逐帧复制到各自的 2D 画布；`view3d(host, pose)` 的 `pose.look`/`origin` 可用 GSAP 补间做机位运动，`pose.wide` 让横向展开的组件在宽舞台上收近镜头，系数读 `tokens.flagship.three.wide_fit`）。平面信息图逐场揭示的画法属于常规轨 KZDemo（15 DEMO-02）。组件名、步骤与数据字段只看 `tokens.flagship.stages.catalog`；未知步骤或非法数据直接抛错；舞台上的合计、占比、缺口、流失与升降都由组件从数据算出。图库：`examples/motion/flagship/index.html`。
- `state()`：活动页 `{index, scene, scenes, playing, time, duration}`；`finishAll()` 把所有页置于终态（打印前调用）。
- 放映（06 MOTION-09）：有人值守进入播第 0 场，`next()` 推进一场，播放中再按先放完当前场；无人值守进入播完全部场；`prev()` 退回上一场；从后一页退回显示终态。`playing` 是逻辑状态（有驱动且未到目标），不依赖首帧。
- 终态：减少动态、打印、上游 `?preview` 与 QC 参数 `?kzf-final` 直接显示终态；流体比例变化（`kz:fluidratio`）时重建活动页时间线并保持进度。

## KZLayoutQC（runtime/kz-layout-qc.js）
`inspectCard(card)`、`inspectTextBounds(zone, {tolerance, minOpacity})`、`inspectFold(fold, {content, cols, rows})`、`inspectOrphans(root, {selector})`、`inspectBodySpan(body)`、`inspectEdgeBars(root)`、`inspectEmphasis(root)`、`inspectSiblings(root)`、`inspectWidth(root, {content, container})`、`inspectScroll()`、`inspectOverlaps(root, {scope, minOpacity, min})`（默认查 `.kz-demo-canvas`：不同对象的可见文字行框互相压叠超过 `min` px 记 FAIL，逐 scene seek 后各跑一次）、`inspectTextFloor(root, {min})`（渲染字号：computed font-size × SVG 屏幕缩放，小于 `min`（默认 11 px）记 FAIL；canvas 图表不在内）、`inspect(root)`。返回状态与测量值，不是视觉判决（10）。

- `inspectCard` 的 `TEXT_OUTSIDE`：文字越过内边距（纵向容差 `layout.qc.text_overhang_em`，横向 `text_inner_tolerance_px`）或越过卡片外缘。
- `inspectFold` 只把带可见文字或已绘制图形的对象计入覆盖率，空卡与空舞台不计，数量见 `emptyBoxes`。
- `inspectOrphans` 按行带分行：字号较小的行内片段（单位、`<small>`）与所在行合并，不会被误判成单独的末行。
- `inspectOrphans` 同时返回 `splits`：换行落在中文词内部（`Intl.Segmenter` 分词，如“中心记｜录”）的元素与被拆的词；有孤字为 FAIL，只有拆词为 WARN。
- `inspectWidth` 量信息对象的横向跨度占视口宽的比例（13 WIDE-01），低于 `wide.content_width_min` 为 FAIL；页眉内的元素与宽度 ≥ 视口 `container`（默认 0.9）倍的容器不计，`containersSkipped` 给出跳过的数量。
- `inspectFold` 把首屏外的固定页眉 `.kz-site-head` 一并计入首屏（它和旧版首屏内页头一样在视口里）；`inspectScroll` 把吸顶块（如流式目录轨，页眉除外）画在它在每个窗口里实际停留的位置，不只算它的静态位置。
- `inspectBodySpan` 量 PPT 正文区直接子元素的纵向跨度占正文区高度的比例，低于 `layout.content_span_target` 下限为 WARN；撑满型预设（film、full、split）读作 1。

## 计划
`python tools/qc_plan.py PLAN [--manifest MANIFEST --asset-root ROOT --out REPORT]`：schema 与语义预检，输出 error/pending/review。

## KZExposure / KZLongitudinal / KZExplore（runtime/kz-explore.js，round 9）
- **`KZExposure.mount(el, data, opts)`**：`data` 是 `{kind:'exposure-plan', program, targets?, focus?, unit?, target_label?, ref?}`。
  - 返回 `chart, play, finish, renderProgress, getProgress, getData, model, gantt, openEditor, select(k), setData, resize, pause, resume, dispose`。
  - 离屏 KZGantt（`gantt`）持有计划，并接入计划总线（08 GANTT-08）。
  - `KZExposure.refreshTables(ref, program)` 重绘 `[data-kz-xp-plan=ref]` 的表。
- 参考范围与参考线（历时变化、小倍数）：`ref: {range: {lo, hi}, lines: [{label: 'ULN', value: 40}]}`，两项都可省；别的键报错。
- **`KZLongitudinal.mount(el, data, opts)`**：`data.kind` 是 `longitudinal`、`longitudinal-diff`、`lab-boxplot`、`lab-multiples` 或 `completeness`。表内改数写回 `KZ_DECK_DATA[<元素的 data-kz-chart>]`：两张图共用一份数据（如首屏概览与正文同一历时图）就写同一个 data-kz-chart 键，不要另起别名，否则改动写到新键，原数据条目不变。
  - 返回 `chart, play, finish, renderProgress, getProgress, getData, model, openDrill(g, arm, j), setData, resize, pause, resume, dispose`；`setData` 不合规时抛错。
  - 点数据点打开历时表，表可编辑（05 CHART-06）。
- **`KZCharts.mount`** 遇到上述 kind 时自动转交；deck、站点与流式的挂载代码不用改。
- **`KZExplore.scan(root)`**：给 SoA 表（`data-kz-explore`）加下钻热区（DRILL-08）。载荷在 `window.KZ_DECK_DATA[<data-kz-explore 的值>]`：`kz_layout.py render --track html` 写出的 charts.json 已按这个键给好（如 `soa1f1`），整份并进 `KZ_DECK_DATA`，不要改键名；键不对时下钻不报错，只是不出现。页面加载时自动执行一次；动态插入的表要手动再调用。
- **计划总线**：
  - `KZGantt.publish(doc, from)` 把计划分发给同 `id` 的订阅者并更新 `KZ_DECK_DATA`。
  - `KZGantt.subscribe(from, fn)` 返回取消函数。
  - `KZGantt.mount` 的新选项：`gid`、`field`（写回 `KZ_DECK_DATA[gid][field]`）、`anchor`（编辑台按该元素定位）、`bus:false`（不进总线）。甘特与累计暴露共用一份计划时，数据条目是包络（exposure-plan 的 charts.json 写成 `{program: …}`）：甘特挂 `KZGantt.mount(el, KZ_DECK_DATA[gid].program, {gid, field: 'program'})`，不另存一份计划，两张图经总线按 program id 同步。
- **KZClinical 新增**：
  - `longitudinal(spec)`、`LG_INTERVALS`；
  - `exposurePlan(spec)`、`exposureTables(model)`（返回 `{readiness, ledger}`，与 Python 表格一致）、`pyRound`；
  - `XP_BANDS`、`XP_LABEL`。
