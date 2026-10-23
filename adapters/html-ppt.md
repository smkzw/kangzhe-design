# HTML-PPT 适配合同（html-ppt-skill）

核对基线：lewislulu/html-ppt-skill `fd1629067909`（2026-09-14）。升级上游后先重读 `runtime.js` 的 fit、活动页、键盘与演讲者部分，再改本页；不反过来放宽品牌要求。

## 上游事实
- `body[data-fit="fluid"]` 时 `initCanvasFit` 直接返回，`.deck` 为 100vw×100vh；这是宽屏的唯一扩展点，不再叠缩放。
- 翻页切换 `.is-active / .is-prev`；base.css 给 `.slide` 0.5s 透明度渐变与 ±30px 横移，且没有减少动态规则。
- `data-anim`（animations.css，27 种）与 `data-fx`（fx-runtime，20 种）由上游在翻页时重加；A 键会给当前页循环套上入场动画。大多数不处理减少动态。
- 页码：runtime 只更新文档中第一个 `.slide-number` 的 `data-current/data-total`，base.css 用 `::before/::after` 显示。
- O 总览在初始化时克隆一次页面（早于项目组件挂载，克隆中的图表/甘特为空）；S 演讲者窗口的两个 iframe 固定 1920×1080 再缩放，与 fluid 观众窗不同画；`?preview` 只显示一页并设 `body[data-preview]`。
- 打印样式隐藏 deck 级 `.deck-header/.deck-footer`。
- `scripts/render.sh <html> [N|all] [out]` 用 headless Chrome、1920×1080、`file://…#/N`、virtual-time-budget 4000，没有就绪等待参数。

## 康哲的做法
### 脚手架与资源
`new-deck.sh` 生成后，把实际使用的 `base.css`、`runtime.js` 复制进交付目录并记录上游与副本 SHA；不加载主题链接、`data-themes`、远程字体（fonts.css）和 `animations.css`。分别用 `file://` 与 HTTP 打开，确认无 404。

### 单位：一个比率
`html-ppt-bridge.js` 维护 `:root` 上的 `--kz-un = innerHeight / 720`（不钳制）和 `--kz-u = calc(var(--kz-un) * 1px)`。几何写 `calc(N * var(--kz-u))`，字号写 `calc(Npx * var(--kz-un))`，共享组件在 `.kz[data-fit="fluid"]` 下以 `--kz-component-u: var(--kz-un)` 自动换算；canvas 组件（图表、甘特）读同一比率并在 `kz:fluidratio` 事件时重绘。项目 CSS 不另定义 `--kz-u`。

这样字号与几何永远同比例：1080 屏 150% 缩放（约 1280×610）时整页等比缩小，文字不会比框大；捏合缩放不改变比率（用布局视口而非 visualViewport）；打印期间比率锁定为 1。浏览器 Ctrl± 缩放被高度归一化抵消，这是放映的正常行为。核对字号时用 computed ÷ `--kz-un` 使用值。

不要写 `calc(24px * var(--kz-u))`（长度×长度，整条声明无效）或 `calc(24 * var(--kz-un))`（无单位，非法字号）。

### 页面结构
- 正文页 chrome 放在每张正文页内（打印也保留）：`brand_fragments.facets(prefix)` 生成的内联 SVG 双菱形，放置矩形 `tokens.chrome.header_mark.placement_htmlppt_u`；`tokens.chrome.rule` 是端点数组 `[x1,y1,x2,y2,stroke]`，HTML 写 `left:x1·u; right:(1280−x2)·u; top:y1·u; height:stroke·u`；Logo 右锚；页脚两槽，页码可静态写入。
- 非 16:9 视口的固定文字框宽度取 `min(w·u, 视口宽 − x·u − 右留距·u)`，背景与正文网格仍铺满。
- hero 页用 `hero_layout.html_fluid_fragment`。
- 上游注入的 `.progress-bar` 由 kz-glass.css 隐藏。

### 翻页与动效
品牌层覆盖上游翻页（06 MOTION-08）：`.kz .slide{transform:none; transition: opacity 0s linear var(--kz-dur-exit)}`、`.is-active` 去掉延迟、背景图与 hero 主视觉各自淡入、减少动态取消过渡。生命周期用 `KZHTMLPPT.bind`：

```js
const bridge = KZHTMLPPT.bind(document.querySelector('.deck'), slide => {
  const page = KZMotion.mountPage(slide);
  return { enter() { page.enter(); }, leave() { page.leave(); }, dispose() { page.dispose(); } };
});
```

图表、甘特、Film 加入同一个 factory：enter 时 play / `resume('engine-inactive')`，leave 时 pause。`?preview`、打印、减少动态走静态终态（`page.finish()`、`chart.finish()`、`film.seek(film.staticProgress)`）。完整示例：`examples/reference/htmlppt/deck.js`。

### 已知限制
- O 总览中的图表/甘特缩略图为空（上游先克隆后挂载）；需要时在组件挂载后重建总览，或在交付说明中列为限制。
- 演讲者窗口预览与 fluid 观众窗比例不同；需要同画时向预览传递观众比例，否则列为限制。

## 正式静态截帧
`render.sh` 可能在上游 0.5s 过渡中截帧。确有该问题时，从观众源派生同目录 `capture-only.html`：资源与 hash 导航不变，仅此副本加 `body[data-capture-only]`，项目装配识别后把图表、甘特、电影置于完整终态；观众源不引用捕获样式。改源后重新派生。然后调用原 `render.sh capture-only.html all <out>`，逐页核对 PNG 尺寸、活动页 opacity=1、完整文字与数据。1920 截帧不代替 2560 宽屏运行检查；记录上游与副本 hash 和真实返回码。
