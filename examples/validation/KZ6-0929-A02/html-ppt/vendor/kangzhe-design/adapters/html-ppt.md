# HTML-PPT 适配合同

核对基线：`lewislulu/html-ppt-skill@fd1629067909ff55b36b905476de4e5f26062a1f`。本次为源码适配设计及独立组件实现，**未运行该上游整套演示者流程**。

## 唯一运行时

上游负责 scaffold、`.deck/.slide/.is-active`、设计画布缩放、键盘翻页、hash、overview、presenter、notes、打印基础能力。本包只提供 theme、内容骨架、图表/动效/下钻/编辑组件；禁止再建立一套 SlideEngine 或 `window.onkeydown` 全局翻页。

用上游 scaffold 创建项目，不手工猜 `../` 深度。选择已有模板布局再注入康哲材料与受保护槽位。讲稿进入该版本的 `.notes`，不照搬其通用“每页 150–300 字”作为本品牌定额。

## 画布和 CSS

默认康哲逻辑坐标为 1280×720，因此给上游 `.deck` 明确 `data-w="1280" data-h="720"`；不同时使用 1920 模板像素和康哲 1280 像素。由上游 `initCanvasFit` 唯一负责缩放，不设第二层 fit。若选另一真实画布，则统一换算所有坐标与字体，不单缩个别卡片。

依赖顺序：上游 base/theme → `kz-tokens.css` → `kz-glass.css` → 项目级有限布局。给项目作用域 `.kz`；官方 logo 按上游声明式机制一次挂载，按标题页规则处理 `data-no-logo`。固定页眉页脚复用上游槽位并以 tokens 定位，不能追加第二套 logo、页码或 footer。

**骨架说明：**本包没有覆盖上游 CSS 的全自动 patch，因为尚未完成其 presenter/print E2E。`html-ppt-bridge.js` 仅观察上游 `.is-active` 调用组件生命周期。固定 chrome 的正式适配由 Agent P1 完成，不能把组件实验室当成已合格的 HTML-PPT 主题。

## 生命周期与输入

每页组件由 `KZHTMLPPT.bind(deck,factory)` 注册。factory 返回 `{enter,leave,dispose}`，入场可触发 `KZMotion.reveal`、`chart.play`、电影恢复；离开必须暂停，隐藏容器的图表在进入后 resize。桥接不修改 `.is-active`，也不监听/写入 hash。

电影、下钻、表单、甘特的方向键在组件内部阻止冒泡；原生输入行为保留。不在整个 document 屏蔽上游快捷键。退出编辑/对话框后，上游翻页应立即恢复。上游如果使用 capture-phase 导航，必须在其扩展点处理；不能谎称 bubble 拦截已解决所有情况。

Presenter preview iframe 是独立实例，须设置 snapshot/reduced-motion 模式，不让预览与观众页各自漂移。导出截图必须 seek 到获批关键帧并显示完整内容。原生 upstream 预览、双窗口同步、打印分页和窄屏等为 P1 的实际验证项。
