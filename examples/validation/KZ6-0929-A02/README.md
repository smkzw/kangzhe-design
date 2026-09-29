# A02 同内容七页样板

- `html-ppt/index.html`：实际html-ppt-skill运行时。
- `matched-seven.pptx`：实际ppt-master默认导出，再绑定18个hero原生文字框。
- `hero-page-plan.json`、`content.json`：四类固定形态与合成文案。
- `frame-binding.json`、`binding-regression.json`：原件/输出hash及只改四页文字框的证据。

固定合同见根目录design_specs/11-hero-layouts.md。HTML源像素与PPTX单位转换为96px/in→72pt/in。大标题不自动缩字，超容量精简或拆页。

范围：三个HTML视口21状态；MacPowerPoint四类hero渲染；封面标题实际修改保存重开，42pt及框尺寸保持。原生图表与甘特的编辑回读另在A01副本验证，不扩大到本文件每个对象。

限制：源图1672×941未达建议分辨率；字体栅格/玻璃阴影有轻微跨渲染器差异；正文两轨图表值相同但轴范围不同。Windows未测；整个skill未生产验收。用户提供的临床原件不在公开仓库内。
