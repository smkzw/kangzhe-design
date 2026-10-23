# 指定制作引擎的适配层

- PPTX → `ppt-master.md`（hugohe3/ppt-master）。
- HTML-PPT → `html-ppt.md` 与生命周期桥 `html-ppt-bridge.js`（lewislulu/html-ppt-skill）。

站点式与流式不强制新框架：沿用项目现有结构，取用本包 tokens、玻璃、电影、图表、下钻、甘特组件，避免双时钟、双导航。

上游接口变化在适配层解决；品牌与内容规则只由 design_specs 的各所有者修改。所有第三方命令以真实安装的版本为准，本页记录的是核对基线与实测结果，不代替实际运行证据。
