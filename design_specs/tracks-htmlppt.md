# HTML-PPT轨道
必须实际调用已安装lewislulu/html-ppt-skill脚手架；上游拥有唯一deck、活动页、键盘、hash、S演讲者窗口、overview和notes。本包提供全视口品牌主题和组件，不创建第二个slideshow。

默认采用上游已公开的data-fit="fluid"扩展点，宽屏合同与精确接口见adapters/html-ppt.md。PPTX/HTML的16:9基准态保持固定品牌及四类hero形态，宽屏内容网格/背景扩展，字号不按卡单独调整。没有横向滚动条不等于用满宽屏。

必须加载06-motion-film，即使没有独立电影。每个实际交付页执行对象motion manifest：正文卡进出、hover光影/合规tilt、双菱形浮动、hero卡浮动；流程顺序、图表数字联动按对象启用。数据坐标面保持平直。上下游只保留一个导航/缩放owner。

四类非正文页使用11固定形态、真实生成背景和独立保护区；正文固定chrome，背景可在合格映射下复用。主动按材料设计宽L1/L2；甘特图3/4+编辑框1/4或上图下框。输入框、拖拽与dialog内部按键不能触发翻页。

preview、overview和print使用完整数据终态且不运行后台电影。观众普通打开仍有完整动态；实际测试深链接、箭头、S、O、打印、离线、宽屏resize、RM和重新进入。组件实验室不能代替上游E2E；当前状态见review/CURRENT_STATUS.md。
