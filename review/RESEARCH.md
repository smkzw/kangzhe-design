# 公开参考与上游边界

检索/核对日期：2026-09-29。以下为技术与视觉参考，不是将这些来源当成未来业务页脚的文献。

## 官方与原始资料

| 来源 | 实际读取范围 | 采用/不采用 |
|---|---|---|
| Apple WWDC25 Meet Liquid Glass | 官方介绍与文字稿，特别是动态、可读性、材料与层级 | 采用连续形变、局部光学、内容优先；不照搬系统控件结构，不声称报告卡片=官方HIG规定 |
| Apache ECharts Area Chart | 官方 `areaStyle` 例子 | HTML默认浅面积折线；特殊统计意义需取消/另用置信带，不能混同 |
| Apache ECharts Drag | 官方坐标转换/拖动交互示例 | 按像素/数据双向转换实现季度编辑，resize/父缩放实测；不是声称ECharts自带完整可编辑Gantt |
| W3C WCAG 2.2.2 | 官方解释自动动态暂停/停止要求 | 自动电影提供持久暂停与静态信息；hover停止不够 |
| ppt-master | README、AGENTS、native-data-interface、SVG effects等；指定SHA | 原生数据fallback与metadata同步、alpha/效果边界；Gantt并非该版本原生chart类型 |
| html-ppt-skill | SKILL、runtime主要接口等；指定SHA | 官方画布/导航/演讲者唯一；主题与生命周期增量适配 |

- https://developer.apple.com/videos/play/wwdc2025/219/
- https://echarts.apache.org/handbook/en/how-to/chart-types/line/area-line/
- https://echarts.apache.org/handbook/en/how-to/interaction/drag/
- https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html
- https://github.com/hugohe3/ppt-master/tree/680de11f1bef4628b68d5daad9dffec569fbd51f
- https://github.com/lewislulu/html-ppt-skill/tree/fd1629067909ff55b36b905476de4e5f26062a1f

## 用户给定动态合集

https://motionsites.ai/ ：读取公开目录与预览介绍；没有取得收费prompt/源码，也未对所有预览运行浏览器。因此Biotech、Features、金融信息图等只用于构图方向候选，不虚构其具体动画API或直接复制不可见实现。

https://miaai-lab.github.io/Claude-Opus-5.5-100-HTML-Files/ ：读取索引与部分候选说明/页面材料，不代表逐一实测100例。

| 候选类型 | 康哲可吸收 | 康哲不直接吸收 |
|---|---|---|
| Aurora / Glass交互 | 指针局部高光、轻倾斜、背景材料联系 | 深色/极光多色、过强发光 |
| Raster / FLIP构图 | 同一元素在网格变化中的空间连续 | 海报化红黑版式、为运动而打乱阅读顺序 |
| Lighthouse式长文 | 阅读栏与宽幅视觉并存、层级清晰 | 全站锁死一个窄中心栏 |
| Mercury类变形 | 可追踪单载体的尺寸/圆角/色彩变化 | 多球分裂后替换主体、文字穿插、金属霓虹 |
| Nimbus类场景数据 | 状态变化与数据解释关联 | 把原例SVG统计图搬来取代ECharts，或用crossfade冒充连续主体 |
| Loader / 微交互 | 等待→完成的一个控件连续变形、轻呼吸 | 将loading控件放大当整部医学电影、全屏循环干扰 |
| 共享元素明细展示 | 大卡展开/关闭的空间关系、返回状态 | 截图式过渡被误称同DOM；只有三行的窄抽屉 |

所有采纳都需重配康哲橙黄/部门色、文字语气、字体、光学强度、语义与可访问性。案例美观不能覆盖数据真实性。动画名不是验收条件，实际连续与信息理解才是。
