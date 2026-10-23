# PPT Master 适配合同

核对基线：hugohe3/ppt-master `523e5bd972f9`（2026-10-23，`git describe` 为 `v6.7.3-2-g523e5bd`，即 v6.7.3 之后的两个往返修复提交），转换器级回读见 `examples/reference/pptx/README.md`。安装位置由宿主决定，执行前按上游 `SKILL.md` 的“paths before commands”取得 `SKILL_DIR`，先跑 `attribution_guard.py`。升级时重读 routing、svg-contract、native-data、animations 与 transitions 文档，再改本页。

## 插入点
| 上游步骤 | 本包提供 | 不干预 |
|---|---|---|
| 路由与资料接收 | 四轨意图、品牌限定、引用策略 | 不把所有任务强制成同一路由 |
| Strategist（Default）/ Quick 决策 | tokens、page-plan、短标题、可选观点句、保护区、图像需求、构图预设 | 不替用户通过 BLOCKING 门；Quick 不塞 spec_lock |
| 图像阶段 | 04 的图像计划、保护区、审阅 | 沿用上游 manifest 与 `image_gen.py`；外部生图结果导入同一 manifest |
| Executor SVG | 原生文字与数据、渐变 alpha、合法阴影、已批准图片 | 不写 backdrop-filter、任意 SVG 滤镜或整页截图 |
| 原生图表 | 05 的同一数据、native 标记与元数据 | 不把 ECharts option 当上游 JSON |
| 动效侧车 | 06 MOTION-07 的 `animations.json` | 不用 auto/mixed/random |
| checker / export | 康哲质量门另做，保留两份报告 | 不绕过上游 checker 与导出顺序 |

## SVG 写法要点（6.7.3 已核）
- 每个内容单元一个顶层 `<g id>` 并声明 `data-pptx-bounds="x y w h"`；顶层组在两轴重叠 >1px 即失败（结构角色组、Morph 暂存组除外）。页标题自成一组。
- 背景图、横线、Logo、页脚用 `data-pptx-role`（`background / decoration / logo / footer`）；**带角色的原始元素必须有稳定 id**（`brand_fragments` 已加）。不要给卡片、正文、图表加结构角色。
- 根 `<svg lang="zh-CN">` 声明演示语言；`font-family="Microsoft YaHei, Arial"` 导出为主题字体 latin Arial / ea Microsoft YaHei。
- `• ` 开头的分行文字导出为原生项目符号 `a:buChar` 加悬挂缩进。
- 渐变停点的 `stop-opacity` 原生保留；线性渐变转角度，径向渐变只保留焦点。

## 阴影
- 每个对象只转换一个效果；可挂滤镜的只有 rect、circle、polygon、image、path、text 及少数特例组，普通 `<g>` 上的滤镜被拒绝。
- `feDropShadow` 偏移非零 → 一个外阴影；`dx=dy=0` → glow。`blurRad = stdDeviation × 2 × 9525`，`dist = hypot(dx,dy) × 9525`，导出 alpha ≈ 作者 alpha × 0.75（`tokens.elevation.pptx.export_alpha_factor`）。
- inner shadow、soft edge、背景模糊、mask 须预先栅格化，玻璃卡不用。
- 康哲配方见 02 LG-PPTX：作者值 `elevation.pptx.rest`（dy 6、σ 8、α 0.12，导出约 0.09）。实测：blurRad 152400、dist 57150、dir 90°、alpha 9%。

## 原生数据
- 图表：可见 fallback + `data-pptx-replace-with="chart"` 的 JSON 元数据，`stamp_native_fallbacks.py --write` 同步，`verify-charts` 阶段，导出加 `--native-charts-and-tables`。
- 折线 + 面积：combo 中 area 与 line 两个 plot 共享数据。
- 值轴：`{"axes":{"value":{"minimum":0,"maximum":8,"major_unit":2}}}`（封闭对象）；扁平 `axes.minimum` 会被拒绝。
- 甘特：不在原生 chart 类型中（上游明确 fail fast），用可编辑形状与日期表，不写 `type:gantt`。

## 动效与 Morph
- 侧车 `animations.json` 放在项目根，`animation_config.py validate <project>` 校验，导出加 `--animation-config animations.json`（路径相对项目）。
- 字段：`defaults.transition`、`slides.<页>.animation.trigger`、`groups.<顶层组 id>.{effect,duration,delay,order,decelerate}`、`slides.<页>.transition.{effect:"morph",effect_options:{"morph_by":"object"},duration}`、`morph.{from, pairs.<key>.{from,to}}`。
- 时序：同一拍内的 `with-previous` 行，delay 都从这一拍的起点算，不累加（上游：delay 是“加在已解析起点上的行偏移”）；`after-previous` 行从上一行结束后再加 delay。康哲的错峰用 with-previous，第 n 组写 n × 70ms；实测导出的 `p:cond delay` 为 0 / 70 / 140 / 410。
- 实测导出：Fade 为 presetID 10、`nodeType="withEffect"`、`decel="70000"`；Morph 两端写成同名 `!!<key>`，目的页 `p159:morph option="byObject"`。
- 限制：Morph 只用于相邻页，两端同种容器；原生图表、表格、带结构角色的根原语不能配对；只出现在第二页的文字用淡入（可用 `data-pptx-morph-staging="true"` 放画布外）。没有小位移入场预设；不支持段落级逐条出现、自定义路径、按系列出现。

## 品牌绑定（导出之后）
```bash
python tools/bind_header_mark_pptx.py upstream.pptx marked.pptx bindings.json --receipt mark-binding.json
python tools/bind_hero_pptx.py upstream.pptx branded.pptx hero-page-plan.json --receipt frame-binding.json
python3 ${SKILL_DIR}/scripts/pptx_delivery_check.py marked.pptx
```
- 双菱形：`bindings.json` 形如 `{"pages":[{"slide":2,"replace_shape_ids":[3,4,5,6]}]}`，ID 从当次导出的 slide XML 中按名称（`kz-facet-0…3`）查得，不假设各页一致。工具要求 1280×720 画布、对象无正文文字、位于标记边界内，否则直接失败；输出另存，保留上游原件。实测绑定后 `p:timing` 与 Morph 名称完好、交付检查 0 错误。
- hero 文字框：6.7.0 起普通文本框按字体度量定位首行基线。先不绑定导出，按 11 HERO-04 回读框位置，误差都 ≤2 逻辑像素就不绑定；需要时页面 id 前缀为真实页码，只绑定四类 hero 文字的原生框、内边距、固定行高与禁止自动缩字。
- Edit Native PPTX 的 round-trip 会保留不支持的效果载荷；如果从参考 PPTX 出发能原生保留双菱形，可不再绑定（待用户提供参考文件后验证）。

## 待做（需用户在场）
- 用 Create Template 建康哲 Brand/Style workspace 并注册（上游有确认门）。
- Default 全流程正例与 PowerPoint 实机编辑保存回读。
