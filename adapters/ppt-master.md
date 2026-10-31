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
- 上游 Executor 文档建议用 accent bar 做分隔或强调，部分模板在卡片左边加细色条；康哲不用（02 LG-02），导出前对 `svg_output/` 跑 `tools/check_edge_bars.py`。
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
- 时序：同一拍内的 `with-previous` 行，delay 都从这一拍的起点算，不累加（上游：delay 是“加在已解析起点上的行偏移”）；`after-previous` 行从上一行结束后再加 delay。康哲的错峰用 with-previous，第 n 组写 n × `stagger_ms.pptx_card`（180ms）；实测导出的 `p:cond delay` 为 0 / 180 / 360 / 740。
- 实测导出：Fade 为 presetID 10、`nodeType="withEffect"`、`decel="70000"`；Wipe 为 presetID 22，`direction: "down"` → subtype 4（自底部）、`"left"` → 8（自左）、`"up"` → 1（自顶部）；Morph 两端写成同名 `!!<key>`，目的页 `p159:morph option="byObject"`。Default 路由下导出器自动读取项目根的 `animations.json`，不必加 `--animation-config`。
- 限制：Morph 只用于相邻页，两端同种容器；原生图表、表格、带结构角色的根原语不能配对；只出现在第二页的文字用淡入（可用 `data-pptx-morph-staging="true"` 放画布外）。没有小位移入场预设；不支持段落级逐条出现、自定义路径、按系列出现。

## Default 路由里的康哲输入
- Stage 1：画布 `ppt169`（康哲 PPTX 为 1280×720，初始化时可直接 `--format ppt169`），一般选自由设计；康哲不是 ppt-master 的模板工作区。
- Stage 2：三个方向的配色、字体、正文字号由 tokens 固定（`typography.fixed: true`，正文 20 px），方向之间只在叙事与构图上不同，并在方向说明里写明这一点。**确认页会按正文基准重算标题、副标题、注释字号**（候选里的 `typography.sizes` 只做兼容读入，不显示），所以交接说明里请用户在页面上把它们改成康哲值（标题 32、副标题 24、注释 16 px），确认后核对 `result.json` 的 `typography.sizes`；不一致时由用户在对话里明确更正，Design Spec §I 记下更正来源。注释、图注、表体、图表轴与图例、卡内旁注按 03 TYPE-01 的 secondary 角色写 12pt（SVG 16px），任何页都可用，不必把整页切成 compact；页脚仍按 chrome 的 13.5pt。
- Stage 2 的 `image_usage` 与 `image_ai_path` 由开工第一站的生图能力答案预填（04 IMG-07）：生图 → `["ai","provided"]` 加检测到的路径，三个方向的 `image_strategy` 写同一段康哲风格锚；缺省背景套 → `["provided"]`。确认后 `result.json` 与答案不一致时停下来问用户，不按确认页的默认值走。
- §VIII 与 `spec_lock.md images`：页面引用的每个位图都要登记，包括官方 Logo（复制 `assets/logo_bot.png` 到项目 `images/`，`source=user`、`crop=no-crop`）；漏登记的是计划外图片。
- Executor：ppt-master 要求页面 SVG 由主 agent 手写，脚本不直接写 `svg_output/`。`hero_layout.svg_fragment`、`brand_fragments.facets` 打印的是片段与参考页，由 agent 拼进页面。
- 本机若对 `127.0.0.1` 的反向 DNS 很慢（`socket.getfqdn` 秒级），确认页与实时预览的 `--daemon` 会在健康检查超时后被杀；改用不带 `--daemon` 的前台进程放到后台运行，再用浏览器打开。

## 模板页（13 BODY-02）
常规路线的正文页用模板库生成，Executor 审过再放进 `svg_output/`：

```bash
python3 "$KZ_DIR/tools/kz_layout.py" list                                   # 选模板；example <模板> 给数据合同
python3 "$KZ_DIR/tools/kz_layout.py" render criteria p05.json --track pptx --title 入选与排除标准 \
        --out <project>/kz_fragments --first 5 --total 18                   # 一份数据可拆成多页，页码接续
cp "$KZ_DIR"/assets/icons/kangzhe/*.svg <project>/icons/kangzhe/            # <use data-icon="kangzhe/…"> 在这里解析
# Executor 逐页审 kz_fragments/page_NN.svg，放进 svg_output/（可再改）；背景与 Logo 的相对路径默认 ../images/body_quiet.jpg、../images/logo.png
python3 "$SKILL_DIR/scripts/stamp_native_fallbacks.py" <project>/svg_output --write
python3 "$KZ_DIR/tools/check_kz_project.py" <project> --plan page-plan.json  # 10 G-KZ，导出前
python3 "$SKILL_DIR/scripts/svg_quality_checker.py" <project> --canonical-authoring --stage final --quick-generate --json
python3 "$KZ_DIR/tools/check_notes.py" <project>/notes/total.md --plan page-plan.json   # 09 讲稿，写完 notes/total.md 后
python3 "$SKILL_DIR/scripts/total_md_split.py" <project>
python3 "$SKILL_DIR/scripts/svg_to_pptx.py" <project> --quick-generate --with-notes --native-charts-and-tables -o out.pptx
python3 "$KZ_DIR/tools/bind_highlight_pptx.py" out.pptx out-hl.pptx --receipt highlight.json
python3 "$KZ_DIR/tools/check_kz_project.py" <project> --pptx out-hl.pptx     # 高亮哨兵已清
```

- 模板 SVG 已守本页的写法要点：每张卡、每个图表或表格一个顶层组并带 `data-pptx-bounds`，卡壳是 decoration，表格写 `semantic-table.v2`（逐边框线、`header_rows`、合并单元格），图表带原生 payload 与可见 fallback；甘特、森林图、KM、示意图是原生形状。
- 文字保持上游默认的 `preserve` 文本流（`wrap="none"` 加 `<a:br>`，行已在模板里按微软雅黑实测断好），不加 `--reflow-text`；`data-pptx-frame` 只由上游助手写，不手写。模板量宽时给 4%（`layout.templates.measure_headroom`）余量，抵消检查器偏宽的估算。
- `render` 的回执 `kz-layout-receipt.json` 记下每页的模板、溢出与原文核对；溢出或缺一条源文字时命令退出 1，按 COPY-09 换模板或拆页，不删字。
- Quick 路线同样适用；Default 路线在 Design Spec §IX 的 Composition 里写模板名。
- 讲稿按 09 写进 `notes/total.md`（`# NN_页标题`，页间 `---`）：封面、目录、章节、尾页一句话，正文页说重点和要决定的事，不报幕。ppt-master 的 executor-notes 只管格式与覆盖，用语以 09 为准。Quick 路线默认不嵌讲稿，要加 `--with-notes`。
- 页标题按 03 COPY-01 写章节或主题名；本页的观点放在模板的结论带（`band`）或观点句里。

## 品牌绑定（导出之后）
```bash
python3 "$KZ_DIR/tools/bind_header_mark_pptx.py" upstream.pptx marked.pptx bindings.json --receipt mark-binding.json
python3 "$KZ_DIR/tools/bind_hero_pptx.py" marked.pptx branded.pptx page-plan.json --receipt frame-binding.json
python3 "$SKILL_DIR/scripts/pptx_delivery_check.py" branded.pptx
```
- 双菱形：`bindings.json` 形如 `{"pages":[{"slide":2,"replace_shape_ids":[3,4,5,6]}]}`，ID 从当次导出的 slide XML 中按名称（`kz-facet-0…3`）查得，不假设各页一致。工具要求 1280×720 画布、对象无正文文字、位于标记边界内，否则直接失败；输出另存，保留上游原件。实测绑定后 `p:timing` 与 Morph 名称完好、交付检查 0 错误。
- hero 文字框：6.7.3 导出会把文字框收缩到内容大小（实测封面标题 1096×148 → 538×86，x/y 偏 2–3 px），所以四类 hero 页通常需要绑定。先按 11 HERO-04 回读，误差都 ≤2 逻辑像素才可不绑定。工具直接读 page-plan：页码取页面的 `slide` 字段，否则取页面 id 中的第一个整数（`p01`、`1_cover` 都可）；只绑定四类 hero 文字的原生框、内边距、固定行高与禁止自动缩字。绑定后回读偏差为 0。
- Edit Native PPTX 的 round-trip 会保留不支持的效果载荷；如果从参考 PPTX 出发能原生保留双菱形，可不再绑定（待用户提供参考文件后验证）。

## 待做（需用户在场）
- 用 Create Template 建康哲 Brand/Style workspace 并注册（上游有确认门）。
- Default 全流程正例与 PowerPoint 实机编辑保存回读。
