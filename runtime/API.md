# 公开装配接口

本页描述当前实现的可调用接口，不新增设计阈值；数值在 tokens，规则在 design_specs。所有文件使用 `.kz` 作用域与 `window.KZ*` 名称。加载顺序：`kz-tokens.css` → `kz-glass.css`；脚本 `echarts.min.js` → `kz-tokens.js` → `kz-motion.js` → `kz-charts.js` / `kz-gantt.js` / `kz-drilldown.js` →（HTML-PPT）`adapters/html-ppt-bridge.js` → 项目装配 → `kz-audience.js`。

## CSS
| 类 / 属性 | 作用 |
|---|---|
| `.kz-card` | 玻璃卡：三停面 + rim + 短高光 + 动态三层阴影（读 `--kz-lx/--kz-ly/--kz-lift/--kz-mx/--kz-my`） |
| `.kz-thin` | 卡内薄覆层 |
| `[data-kz-tilt]` / `[data-kz-light]` | 由 `mountTilt` 驱动：倾斜 + 光 / 只有光与抬升；`data-kz-tilt="6"` 指定上限（≤ hero 上限） |
| `[data-kz-no-tilt]`、`.kz-chart`、`.kz-gantt` | 测量面不倾斜 |
| `[data-kz-reveal]` | 入场目标；`data-kz-order` 指定顺序；内部 `h2/h3/li/[data-kz-reveal-item]` 级联 |
| `[data-kz-section]` | 首屏以下段落，`mountSections` 首次可见时入场 |
| `.kz-float`（`--kz-float-index` 错相）/ `.kz-mark-float` | hero 卡浮动 / 双菱形浮动 |
| `.kz-optical-field` | 程序化环境光场，`mountField` 驱动视差 |
| `.kz-fold` `.kz-fold-head` `.kz-fold-grid` `.kz-fold-lead` `.kz-fold-stage` `.kz-fold-stage-head` | Bento 首屏（13 FOLD-02） |
| `.kz-kpis` `.kz-kpi` `.kz-number` `.kz-unit` `.kz-kpi-label` `.kz-kpi-note` | KPI 卡 |
| `.kz-steps` `.kz-step[data-state=done|current|todo]` `.kz-step-mark` | 状态条 |
| `.kz-detail-tall` | 可视区高度 ≥1000px 才显示的次要说明 |
| `.kz-film` `.kz-film-stage` `.kz-film-carrier` `.kz-film-carrier-label` `.kz-film-caption` `.kz-film-links` | 电影结构 |
| `[data-kz-layout=centered|distributed]` + `.kz-card-reading` | 卡内纵向模式 |
| `.kz[data-kz-frozen=true]`、`.kz-background-paused`、`[data-kz-motion-active=false]` | 冻结、后台、非活动页暂停浮动 |

## KZMotion
- `mountPage(root)` → `{enter, leave, finish, dispose}`：收集 root 内的 `[data-kz-reveal]` 与 `[data-kz-tilt],[data-kz-light]`；enter 按 06 MOTION-04 编排入场，leave 加速退出（forwards）。同一 root 或目标不能重复挂载。
- `reveal(root, {exit})` → `{finished, cancel}`：不经 mountPage 的单次编排；退出后保留句柄，复入或换驱动者前调用 `cancel()`。
- `mountTilt(root)` → `{dispose}`：弹簧驱动指针光源、抬升与倾斜；鼠标以外的指针、选字、编辑、冻结、减少动态时复位。
- `mountSections(root=document, {selector, threshold})` → `{finish, dispose}`：首屏以下段落首次进入视口时 `reveal`；打印或切到减少动态时全部显示。
- `mountField(root=document)` → `{dispose}`：环境光场随滚动位移（限幅）。
- `countUp(el, {to, from=0, decimals=0, duration})` → `{play, seek(p), finish, progress, dispose}`：终值写入 `aria-label`；减少动态或后台时直接终值。
- `storyboard(states, opts)` → `{frames, duration, holds, enterAt, closeAt, phaseAt(p)}`：每个 state 为 `{label, caption, facts?, geometry:{x,y,w,h,r}, tint?}`；输出合法、首尾一致的 Film 关键帧与业务阶段映射。
- `drawLinks(svg, pairs)`：`pairs=[{id, from:Element, to:Element, progress}]`，按实时矩形画三次贝塞尔连线，`progress` 决定描绘长度；在 Film `onRender` 中调用即可随载体变形。
- `new Film(root, {frames, duration, onRender, managedText, staticProgress, minCarrierWidth})`：root 内须有 `.kz-film-stage` 与其中唯一的 `.kz-film-carrier`。帧 `{t,x,y,w,h,r,tint:[r,g,b,a],label,caption}`：至少四帧、t 严格递增且含 0 与 1、几何归一化且不越出舞台、r ∈ [0,0.5]、首尾几何/材质/文字一致。方法 `pause(reason)`、`resume(reason)`、`seek(p)`、`snapshot()`、`dispose()`；没有 play/reset。`onRender(frame, p, film)` 的 frame 带 `index` 与 `textAlpha`；默认模式下 runtime 写 label/caption 并设 `--kz-film-text`。构造成功设 `root.dataset.kzReady='true'`，`kzProgress` 随渲染更新。
- `sample(frames, p)`、`validateFrames(frames)`：低级函数。

## KZCharts
`mount(el, data, {onProgress, onDataClick})`；data 为 `{kind:'line'|'bar'|'column', categories, series:[{id, name, values:[number|null], color?, role?:'comparator', department?}], unit, axis?:{min,max,interval}, decimals?, area?, description?}`。返回 `chart, play(ms), finish, renderProgress(p), getData, getProgress, setData, resize, pause, resume, dispose`。折线揭示左→右描出（x 轴为 0…n−1 的数值轴，标签映射回类别）；柱形自基线错峰长出；类别色取 `tokens.charts.categorical`，超过 5 个系列抛错。`option(data, opts)` 是低级 option 工厂。

## KZGantt
`mount(root, data, {onProgress})`；data `{min, max, tasks:[{id, label, start, end, color?, department?}], taskColor?}`，整数季度来自 `KZGantt.qindex(year, quarter)`，区间 [start, end)。返回 `chart, root, plot, select, play, finish, getProgress, getData, getSelected, getDirty, commit, undo, reset, serialize, geometry, importJSON, pause, resume, dispose`。

## KZDrilldown
`new Drilldown({host, onOpen, onClose})`；`push({id, title, render}, trigger)`，render 收到 `(section, drill)`，返回可选 `{pause, resume, dispose}`；`pop()`、`close()`、`snapshot()`、`dispose()`。打开时从 trigger 所在卡片展开，关闭时折回（状态立即关闭，动画后原生 close 并还焦点）。`KZDrilldown.element(tag, cls, text)` 是用 textContent 建节点的小工具。

## KZHTMLPPT（adapters/html-ppt-bridge.js）
维护 `--kz-un` 与 `--kz-u`（adapter「单位：一个比率」）。`bind(deck, factory)` → `{sync, dispose}`：factory 收到每个上游直接子 `.slide`，返回 `{enter, leave, dispose}`；总览克隆不挂载；初始化失败会清理已返回的生命周期。

## KZLayoutQC（runtime/kz-layout-qc.js）
`inspectCard(card)`、`inspectTextBounds(zone, {tolerance, minOpacity})`、`inspectFold(fold, {content, cols, rows})`、`inspectOrphans(root, {selector})`、`inspect(root)`。返回状态与测量值，不是视觉判决（10）。

## 计划
`python tools/qc_plan.py PLAN [--manifest MANIFEST --asset-root ROOT --out REPORT]`：schema 与语义预检，输出 error/pending/review。
