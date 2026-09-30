# PPT Master 适配合同

## 事实基线与边界

原包核对上游提交 `680de11f1bef4628b68d5daad9dffec569fbd51f`（2026-09-27）。KZ6-0929-A01 已实际执行本机 ppt-master 6.6.0 默认与 Quick 导出；本机安装目录无 Git 元数据，不能将远端提交当作安装 SHA。实际文件树 hash、命令和分项结果见本轮交接。本包没有修改上游；真实导出不等于整套集成验收通过。

唯一 PPTX 制作引擎：`hugohe3/ppt-master`。先读其 `AGENTS.md`、`skills/ppt-master/SKILL.md` 和该版本路由文件。路径、CLI 参数、工作区结构由它负责；本包不另造 PPTX 导出器。

## 插入点

| 上游步骤 | 本包提供 | 不得干预 |
|---|---|---|
| 路由与资料接收 | 四轨意图、品牌限定、引用展示策略 | 不把所有任务强制为同一路由 |
| Strategist / 显式 Quick 的设计决策 | tokens、页面计划、短标题、可选强调句、排版保护区、图片需求 | Quick 不强塞独立确认、spec_lock |
| 图片准备 | `04-image-pipeline.md` 的图像计划、保护区、主题和 QC 记录 | 沿用图片 manifest 和资产阶段；默认使用其 `image_gen.py`。用户指定外部生图能力时，将真实资产/回执导入该 manifest，不另造导出路线、不臆造 provider 参数 |
| Executor SVG | 原生文字/数据、透明填充、合法高光/阴影、已批准图片 | 不写 CSS backdrop-filter、任意 SVG 滤镜或整页截图 |
| native-ready 图表 | `05-charts.md` 的同一数据；逐对象选择 native 标记及元数据 | 不把 ECharts option 当成上游 native JSON |
| 上游 final checker / export | 补做康哲质量门，保留两份报告 | 不绕过其 checker、原生字段校验、快照同步要求 |
| 成品视觉复核 | 全页截图、文本/卡片/图片冲突、真正编辑后回读 | SVG 预览不代替 PowerPoint 检查 |

## 原生玻璃

采用背景图 + 可编辑低饱和半透明卡片 + 局部高光 + 合法外阴影。`tools/glass_svg.py` 仅生成**供上游 Executor 参考的 SVG 原语**，不是另一条 PPTX 制作路线。对象组内文字独立、颜色在通道 alpha 上，不给整体文字降透明度。

上游已核实的边界：`fill-opacity` / `stroke-opacity` / `stop-opacity`；对象直接引用的 `feDropShadow` 会近似为 DrawingML 效果；普通组上的任意滤镜、真实 backdrop blur 不在此合同内。最终原生表现必须实测。

### 数据对象下的阅读底板（A04 R12 实测）
原生图表、表格或甘特需要阅读底板时，底板与局部高光应先于数据对象绘制，最终位于数据对象下方，保持为独立、可编辑的静态页面框架原语。当前上游 checker 支持 root 原语的稳定 `id` 与 `data-pptx-role="decoration"`；其 `_carrier_page_frame_role` 与 `_check_animation_group_ids` 明确识别这类页面框架。不要为满足动画分组提示，将底板与原生图表/表格替换标记合并成一个内容组；替换器处理的边界可能包含底板。

只有确属无业务文字、无数据语义的底板/高光可声明为 decoration。正文、图表、表格、任务条和承载内容的卡片仍保持真实内容身份；不得借这个角色隐藏内容重叠。KZ6-0929-A04 R12 在本机 6.6.0 经真实 Default checker、native export 与 PowerPoint 显示验证该组合，仍保留非阻断样式提示。升级时重新读取该版本静态框架与替换标记接口，不复制样页坐标或猜测对象 ID。

## 原生数据与 ECharts 一致

对支持的图表，同时编写可见 fallback 与 `data-pptx-replace-with="chart"` 下的 JSON metadata；SVG-first 基线由上游脚本同步后再检查。原生激活使用该版本支持的 `--native-charts-and-tables`。面积与折线组合必须包含 area + line 两个 plot，共享源数据；不把可见面积删掉后声称一致。

值轴元数据使用 `axes.value.minimum`、`axes.value.maximum`、`axes.value.major_unit`，例如 `{"axes":{"value":{"minimum":0,"maximum":8,"major_unit":2}}}`。不能使用扁平的 `axes.minimum`：A01 对当前上游 `native_objects/chart_data.py::_chart_axes` 的真实调用会拒绝这些未知轴角色。它们也不等同于 ECharts `min/max/interval`，不得直接透传。

Gantt 不在该版本的原生 chart 类型中：输出可编辑任务形状/文本和日期表，不伪造 `type:gantt`。PPTX 放映环境不承诺 HTML 的拖动和编辑框；编辑模式可调整任务形状，数据驱动重新计算由作者工具执行。

## 参考 PPTX 的使用

上传参考仅作为风格和内容组织参考。若需提炼 Brand/Style/Layout/Deck 工作区，走上游 Create Template；原 PPTX 加新资料的保留式编辑，走 Edit Native PPTX。不要把裸 PPTX 假装成可直接使用的 Generate 模板，不要直接覆盖用户原件。

## 升级探针

记录上游 SHA；读取当次真实 route/接口；检查 image manifest、effect grammar、native-data、模板和导出命令；先跑两页小样再批量。任何接口变化先修适配层并记录，不反过来放宽康哲字体、禁色条、可编辑要求。详见 Agent P1。

## 固定 hero 文字框适配（A02）
上游 `scripts/docs/svg-contract.md` 的 `data-pptx-bounds` 是质量检查提示，不执行裁切或文字重排。实际导出会以文字度量收紧框，无法据此保证固定宽度。完成原引擎 checker 与真实导出后，再运行品牌适配：

```bash
python tools/qc_plan.py hero-page-plan.json
python tools/bind_hero_pptx.py upstream.pptx branded.pptx hero-page-plan.json --receipt frame-binding.json
```

页面 id 前缀必须为真实页码，如 `01_cover`；文字与上游原生对象须唯一精确对应，字号不符或重名直接失败。只绑定四类 hero 文字对象的原生框、内边距、固定行高与禁止自动缩字；图表、工作簿、图片、正文和导航不改动。保留上游原件并对输出重新做原生显示与编辑回读。该步骤不能创建 PPTX，不能绕过上游导出。空辅助文字不创建绑定；长标题精简或拆页，不能自动缩小。

## 固定双菱形原生绑定（A04 用户指定）
`assets/header-mark/source-native.xml` 是经用户确认的原始品牌形状，不是另一个制片引擎。SVG 预览可调用 `brand_fragments.facets(native=True)`；SVG 转换不能保证原始渐变、softEdge 等字段逐项保真，所以最终必须在 ppt-master 实际导出之后复用原生对象：

```bash
python tools/bind_header_mark_pptx.py upstream.pptx marked.pptx header-mark-bindings.json --receipt mark-binding.json
```

绑定 JSON 为 `{"pages":[{"slide":4,"replace_shape_ids":[3,4,5,6,7,8]}]}`；这里只是语法示例，实际 ID 必须从当次导出 XML 检查后填写，不猜测所有页一致。仅列入需要正文 chrome 的页面。工具要求原固定画布、精确对象 ID、对象无正文文字且位于左上标记边界内；不匹配直接失败。保留上游原件，四对象顺序不变，仅为避免碰撞重分配 ID。再次运行上游交付检查，并检查最终截图和 Office 原生编辑。不能把绑定工具当成 PPTX 制作/上游验证的替代品。
