# HTML-PPT正式适配合同

## 已核查接口
本机runtime.js的initCanvasFit在初始化时把data-w/data-h读为常量，后续resize只更新scale；运行时改data-w不能可靠改变逻辑宽度。它与base.css均明确支持body[data-fit="fluid"]退出固定fit，由主题负责全视口排版。这是宽屏最小适配点，不改上游源码、不增加新引擎。远端基线fd1629067909ff55b36b905476de4e5f26062a1f与本机tree hash分别记录，不冒充相同。

## A03默认：全视口主题
从new-deck.sh创建。body设置data-fit="fluid"；deck保持上游class和导航；CSS覆盖其默认padding，用一套品牌主题单位 `--kz-u = viewport_height / 720`，在16:9桌面与1280×720基准相同。主题使用正常CSS长度/网格，不再给deck或文字transform:scale。桌面正文区域left=56u、right=56u、top=96u、bottom=60u，卡群真实跨该宽度；左页眉锚定，右Logo/页码右锚定，固定分隔线向右延伸。文字/Logo/菱形不横向拉伸。对短内容限制文本行长，不限制整个网格/主视觉的宽度。

主交付覆盖16:9、2:1、21:9及更宽桌面；狭窄竖屏使用明确的阅读布局或提示横屏，不能把正常中文降到低于16屏幕px来假装适配。若任务要求固定16:9文件，以显式fixed-export配置使用上游fit；它不代表宽屏观看验收。打印恢复1280×720与完整终态，退出打印恢复观众模式。

四类hero的基准坐标来自tokens：左文字/Logo锚保留；右Logo锚随宽度；目录三等列展开；背景用实际宽幅生成资产按经审阅crop铺满。页眉页脚位置以同一u换算，只有x的右锚随宽度变化。PPTX保持固定画布，无须模拟浏览器resize。

## 禁止上游默认页底进度条
上游runtime自动在body下注入`.progress-bar > span`，它不一定出现在作者HTML中，也不在`.deck`内。必须加载`runtime/kz-glass.css`的`.kz .progress-bar{display:none!important}`；保留原生页码，不改上游runtime。不准只删除源HTML标签或只在hero页关闭。到最后一页检查computed display、全视口底部截图和实际span边界；蓝/橙全宽线均失败，页眉固定橙线仍保留。

## 生命周期和真实挂载
顺序：上游base/theme → kz-tokens → kz-glass → 品牌布局；上游runtime → kz-motion/其他所需组件 → html-ppt-bridge →项目装配 → kz-audience。`kz-audience.js`清除兼容旧示例的播放器UI，不接管动画时钟/翻页；新页面从源头不生成这些控件。
`KZHTMLPPT.bind(deck,factory)`只观察上游直接子slide，排除overview克隆。factory必须返回enter/leave/dispose并接入每张卡的reveal、合法tilt/光源和float；图表/甘特/film按需调用播放、暂停、resize。不要只写chart.play便称整页动效通过。动画对象与最终清单一一对应，缺一项就记录失败。

退出卡片可借上游现有500ms淡出窗口执行240ms退出；不拦截翻页、不改hash。输入与dialog内部阻止对应方向键冒泡，保留输入默认行为。观众界面不加任何播放/暂停/重播/进度按钮。活动页自动进入动效，后台暂停原因互不覆盖；preview静态，打印全部数据，不留隐藏页RAF。

## 当前上游旧康哲指引的替换
本机html-ppt/SKILL.md的Hybrid条目仍提旧design_specs/assets/htmlppt/gx_fx.css、gx_fx.js及htmlppt_fx.md；它们属于停用包，不得寻找或加载。A03对应能力来自本包runtime/kz-motion.js、kz-glass.css与实际组件装配。其150–320字备注和ribbon资产不是康哲6.0约束，分别由09与11管理。其删除runtime主题处理代码的建议不采用：不声明data-themes，保留原runtime，品牌样式后加载。不修改上游来掩盖这些差异。

## 上游验收
必须保存真实scaffold命令和版本；实际深链接/箭头/overview/S双窗同步、preview、print和离线资源检查。fluid模式下presenter预览是独立viewport，不保证天然复制观众的超宽比例：要测试，必要时向预览传递演示比例或把其边界列为未通过，不声称完全同画。当前真实覆盖以review/CURRENT_STATUS为准。
