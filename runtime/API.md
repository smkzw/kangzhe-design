# 公开装配接口

本页描述当前实现的可调用接口，不新增设计阈值；数值在 tokens，规则在 design_specs。所有文件使用 `.kz` 作用域与 `window.KZ*` 名称。加载顺序：`kz-tokens.css` → `kz-glass.css`；脚本（HTML-PPT 先加载上游 `runtime.js`）→ `echarts.min.js`（用到图表或甘特时）→ `kz-tokens.js` → `kz-motion.js` → `kz-charts.js` / `kz-gantt.js` / `kz-drilldown.js` →（HTML-PPT）`adapters/html-ppt-bridge.js` → 项目装配 → `kz-audience.js`。`kz-layout-qc.js` 只在验收时注入。

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
| `.kz-film` `.kz-film-stage` `.kz-film-carrier` `.kz-film-carrier-label` `.kz-film-caption` `.kz-film-links` | 电影结构 |
| `[data-kz-layout=centered|distributed]` + `.kz-card-reading` | 卡内纵向模式 |
| `.kz[data-kz-frozen=true]`、`.kz-background-paused`、`[data-kz-motion-active=false]` | 冻结、后台、非活动页暂停浮动 |

## KZMotion
- `mountPage(root)` → `{enter, leave, finish, dispose}`：收集 root 内的 `[data-kz-reveal]` 与 `[data-kz-tilt],[data-kz-light]`；enter 按 06 MOTION-04 编排入场，leave 加速退出（forwards）。同一 root 或目标不能重复挂载。
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
`mount(root, data, {onProgress})`；data `{min, max, tasks:[{id, label, start, end, color?, department?}], taskColor?}`，整数季度来自 `KZGantt.qindex(year, quarter)`，区间 [start, end)。端点命中区读 `tokens.gantt`；含 `start_known`/`end_known: false` 的任务直接报错（参考组件不渲染未知端点）。编辑器按需展开：根元素 `data-kz-editor` 为 `closed`（只显示图）或 `open`；点选条形、回车或方向键、`select(id)` 打开，“完成”或 Esc 收起，`openEditor(open)` 可直接控制。返回 `chart, root, plot, openEditor, select, play, finish, getProgress, getData, getSelected, getDirty, commit, undo, reset, serialize, geometry, importJSON, pause, resume, dispose`。

## KZDrilldown
`new Drilldown({host, onOpen, onClose})`；`push({id, title, render}, trigger)`，render 收到 `(section, drill)`，返回可选 `{pause, resume, dispose}`；`pop()`、`close()`、`snapshot()`、`dispose()`。trigger 位于 `.kz-card` 或 `[data-kz-drill-source]` 内时从该卡片展开，否则原地打开。`close()` 返回 promise：调用时状态即关闭（`snapshot().open=false`、背景隔离解除、`onClose`），折回动画结束、原生 close 并还焦点后兑现；展开中途关闭会反向折回。`snapshot().width` 用布局宽度（`offsetWidth`），不受展开动画的 transform 影响。`KZDrilldown.element(tag, cls, text)` 是用 textContent 建节点的小工具。

## KZScenes（runtime/kz-scenes.js，演示舞台 15）
`mount(root, {scenes, loop, staticScene, onScene})` → `Stage`。root 内的 `[data-kz-scene-canvas]`（没有则 root）是画布，其中每个 `[data-kz-obj="id"]` 是一个持久对象；可选 `[data-kz-scene-caption]`（说明句）与 `[data-kz-scene-rail]`（状态条，自动生成序号）。
- scene：`{id, caption, set: {objId: state}, order?: [objId…], hold?}`。状态是相对上一 scene 的增量：`x y w h`（画布比例）、`opacity scale rotate`、`fill color stroke`、`draw`（SVG 描绘 0–1）、`count` + `decimals unit`、`text`、`attr`（数值型 SVG 属性）、`cls`（类名开关）。`from` 是首次出现前的隐藏起点，`via: [[x,y]…]` 是本次运动的途经点。对象写入 `[data-kz-obj-text]` 子节点（若有）。
- 步进模式（`loop:false`，HTML-PPT）与循环模式（`loop:true`，站点）。方法同 Film 的 scene 接口：`pause resume seek scene moving toScene next prev playThrough snapshot dispose`，另有 `stops`（各 scene 的进度）与 `audit()` → `{scenes, objects, transitions:[{scene, changed, entered, travel, grow, caption}]}`（15 DEMO-03）。时长读 `motion.scenes`。
- `KZScenes.layout`：`grid(n, {box, cols, gap, valign})`、`bars(values, {box, max, gap})`、`scale(domain, range)`、`rows(n, {box, gap})`、`cols(n, {box, gap})`，都返回画布比例的矩形。

## KZDemo（runtime/kz-demo.js，15 DEMO-02）
`mount(root, kind, data, {loop, staticScene})` → `Stage`；所有数字与说明句由 data 计算。
- `units`：`{unit, groups:[{name, due, received}], owner, deadline, note}`
- `calc`：`{unit, rows:[{name, a, b}], aLabel, bLabel, diffLabel, note}`
- `story`：`{unit, groups:[{name, a, b}], aLabel, bLabel, gapLabel, takeaway?, note}`
- `timeline`：`{min, max, tasks:[{id, label, start, end, department}], milestone?:{at, label, flag?}, note}`，季度同 KZGantt
- `decision`：`{nodes:[{id, label, x, y, w, h?, kind:'in'|'q'|'out'}], edges:[{from, to, label?}], cases:[{id, label, detail, path:[nodeId…]}], intro, summary?, note}`
- `compare`：`{left, right, leftTag?, rightTag?, rows:[{label, left, right}], rightOrder?, tray, note}`
示例数据：`examples/motion/data.js`。

## KZHTMLPPT（adapters/html-ppt-bridge.js）
维护 `--kz-un` 与 `--kz-u`（adapter「单位：一个比率」）。`bind(deck, factory)` → `{sync, dispose}`：factory 收到每个上游直接子 `.slide`，返回 `{enter(info), leave, dispose, next?, prev?}`；`info = {direction:'forward'|'backward', attended}`。桥接在捕获阶段把翻页键与滑动先交给活动页的 `next()`/`prev()`，返回 `true` 时不交上游（06 MOTION-09）；总览克隆不挂载；初始化失败会清理已返回的生命周期。

## KZFlagship（runtime/kz-flagship.js，旗舰路线 14）
`mount(deck, {logo})` → `{ready, frozen, transition, measure, rebuildLenses, dispose}`（`transition` 供 QC 读取当前转场与是否播放了整页光波）。加载顺序在 kz-tokens.js 之后、项目装配之前，CSS 用 `kz-flagship.css`，`body` 加类 `kzf`。它在 deck 下方建一张全屏光场 canvas，在顶层建身份胶囊（`logo` 为官方 Logo 原件的相对路径），给 `.kzf-lens` 生成位移透镜，并监听上游 `.is-active` 变化来驱动光转场；不改导航、hash 与 `.is-active`。

- 页面标记：`data-kzf-kind`（cover / toc / section / content / ending）、`data-kzf-focus="x,y"`（视口比例）、可选 `data-kzf-light`（边缘高光角度）与 `data-kzf-river="a,b"`。
- 元素标记：`data-kzf-in[="序号"]` 入场（光停下后错峰），`data-kzf-calm` 内容页安静区，`data-kzf-pool` 唯一聚光对象，`.kzf-lens[data-kzf-lens=identity|kpi|bar|section|ask]` 透镜，`.kzf-glass` 玻璃面，`.kzf-paper` 纸卡。
- `ready`：字体就绪、透镜与胶囊就位后兑现，同时写 `html[data-kzf-ready]`。`frozen`：减少动态、上游 `?preview` 或 QC 定格时为真，项目装配据此把图表与甘特置于终态。
- QC：`?kzf-t=秒` 定格时钟（入场按该时刻 seek），`?kzf-p=0..1` 定格在从上一页过来的转场中途（未给 `kzf-t` 时时钟取 `flagship.plate.time_s`）。上游初始化后第一次出现的 `.is-active` 当作起始页，深链和刷新不播放转场。`measure()` 在项目改动页面几何后重算光场遮罩。
- 降级：WebGL2 不可用或 `?preview` 时改用 CSS 渐变光场；非 Chromium 的透镜改为磨砂（`.kzf-lens-fallback`）。

## KZLayoutQC（runtime/kz-layout-qc.js）
`inspectCard(card)`、`inspectTextBounds(zone, {tolerance, minOpacity})`、`inspectFold(fold, {content, cols, rows})`、`inspectOrphans(root, {selector})`、`inspectBodySpan(body)`、`inspect(root)`。返回状态与测量值，不是视觉判决（10）。

- `inspectCard` 的 `TEXT_OUTSIDE`：文字越过内边距（纵向容差 `layout.qc.text_overhang_em`，横向 `text_inner_tolerance_px`）或越过卡片外缘。
- `inspectFold` 只把带可见文字或已绘制图形的对象计入覆盖率，空卡与空舞台不计，数量见 `emptyBoxes`。
- `inspectOrphans` 按行带分行：字号较小的行内片段（单位、`<small>`）与所在行合并，不会被误判成单独的末行。
- `inspectOrphans` 同时返回 `splits`：换行落在中文词内部（`Intl.Segmenter` 分词，如“中心记｜录”）的元素与被拆的词；有孤字为 FAIL，只有拆词为 WARN。
- `inspectBodySpan` 量 PPT 正文区直接子元素的纵向跨度占正文区高度的比例，低于 `layout.content_span_target` 下限为 WARN；撑满型预设（film、full、split）读作 1。

## 计划
`python tools/qc_plan.py PLAN [--manifest MANIFEST --asset-root ROOT --out REPORT]`：schema 与语义预检，输出 error/pending/review。
