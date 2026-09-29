# 指定制作引擎的适配层

PPTX → `ppt-master.md`；HTML-PPT → `html-ppt.md` 与增量生命周期桥 `html-ppt-bridge.js`。这两个适配合同基于已读取源码，不代表端到端集成完成。

站点与流式无强制新增框架；沿用用户项目现有 HTML/CSS/JS 或 React 结构，选取本包的主题、Film/图表/下钻/甘特组件，避免双时钟、双导航。不同轨道共享设计 token 和业务数据，而非硬把 DOM 行为搬进 PPTX。

所有第三方命令都以真实安装版本为准。上游接口变化在适配层解决，品牌和内容规则只由 design_specs 各 owner 修改。
