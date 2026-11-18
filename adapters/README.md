# adapters：制作引擎适配

| 轨道 | 引擎 | 文件 |
|---|---|---|
| 可编辑 PPTX | hugohe3/ppt-master | `ppt-master.md`：在 Default / Quick 流程里插入康哲计划、字号、SVG 写法、原生图表与表格、动效，导出后的双菱形与 hero 绑定 |
| HTML-PPT | lewislulu/html-ppt-skill | `html-ppt.md` 与生命周期桥 `html-ppt-bridge.js`：脚手架起步，接管入场、scene 步进、按键隔离与字号换算，不另起翻页或缩放 |

站点式与流式不引入新框架：沿用项目现有结构，取用本包的 tokens、玻璃、电影、图表、下钻与甘特组件，避免双时钟与双导航。

两页都写明了核对过的上游版本。上游升级后先按页内列出的上游文件重新核对，再改适配；品牌与内容规则只在 `design_specs/` 修改。
