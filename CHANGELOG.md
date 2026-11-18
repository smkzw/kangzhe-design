# 8.0.0 · 2026-11-19

8.0 是一次大改版，按主题列出。8.0 之前的版本不再维护，升级方法见 [INSTALL.md](INSTALL.md)。

## 开工两站（新规范 17）
- **开工卡** `tools/intake.py`：一次问完交付形式、路线与生图能力（两项阻断题同一次问到）、背景风格、受众、动效、临床场景与页数。有浏览器时出选择页，确认后得到 `kz-intake.json`；没有浏览器时输出提问批次。`apply` 校验答案（取 `questions()` 的枚举），预填 page-plan、`context_pack` 命令、ppt-master 与 html-ppt 的参数。
- **分页故事板** `tools/storyboard.py`：page-plan 预检后、生成前，每页显示页型、标题、载体（模板缩略图与同族可换模板、旗舰版式、舞台步骤、演示形式）与预检结果，用户逐页通过或提出修改（`kz-storyboard.json`），一行 3 页。

## 常规路线
- **背景**（04 IMG-09）：四种风格登记在 `tokens.image.backdrop.styles`。缺省 A2 是暖纸底加生成的玻璃丝带（`tools/kz_backdrop.py compose` 合成），另有 A1 程序化绸带、B 光学线稿、C 柔焦光晕；缺省背景套覆盖 4 种风格 × 5 种页型 × 16:9 与 21:9。尾页固定“谢谢”。
- **强调**（03 COPY-04）：加粗、深红、下划线、高亮四种标记，四轨外观相同，每卡、每条、每页有预算；`tools/kz_layouts/emphasis.py` 审计，`check_kz_project.py` 报 EMPHASIS-*。脚注与来源这类松散标签不计入强调要求。
- **色条禁令**（02 LG-02）：检查覆盖装饰卡壳、path / polygon、继承与 class 填色、矩阵变换、卡外贴边、导出后的原生形状，以及 HTML 的深层后代、内联 SVG、渐变色带、border-image、单侧阴影。图内的甘特条与刻度不算色条。
- **模板库**（13 BODY-02/03）：共 50 套，均有 family 与密度档。密度按内容算（sparse / standard / dense）；同排卡片的填充差有检查（CARD-BALANCE）。模板文字里出现 HTML 标签时报错。
- **站点与流式宽屏**（13 WIDE-01）：12 / 16 / 24 栏，页边 3.2vw，固定玻璃页眉与三档 Logo；流式两栏无右栏；宽高比 ≥2:1 时首屏 5/7 分栏。嵌入的模板片段按卡宽缩放（`kz-layouts.css` 的容器查询），字号同比，高度随内容，一行放一个模板。

## 旗舰路线 F1（14）
- **画布与编号**：暖白画布、白纸卡；内容页页眉为斜切橙棱面加白色章节图标和小黄棱面，目录与章节编号做立体挤出；尾页“谢谢”。
- **HTML-PPT**：声明式多场动效（有人值守 / 无人值守）。three.js 舞台升级到 r187 + postprocessing + N8AO（`assets/vendor/three.bundle.min.js`），共 16 个电影化舞台：platforms、rings、morph、towers、stream、layers、runway、constellation、ghost，以及临床的 safety、program、exposure、landscape、trialflow、efficacy、soa。
- **PPTX「层叠纸板」**（14 FLAG-12，`tools/kz_layouts/flagship_pptx.py`）：凹槽底轨、渐变纸条加单个原生投影、错位底纸、双色棱面宝石，甘特用棱面箭头条。九个模板：flag-safety、flag-safety-dumbbell、flag-program、flag-program-strip、flag-exposure、flag-trialflow、flag-landscape、flag-efficacy、flag-soa。放不下时报错，不缩字。

## 临床汇报场景族
每族一份数据合同，Python（`tools/kz_layouts/diagram_clinical.py`、`diagram_scenes.py`、`diagram_long.py`）与 JS（`runtime/kz-clinical.js` 的 `KZClinical`）规则与报错逐字相同。同一份数据产出静态模板（PPTX 与 HTML 共用）、常规演示形式、旗舰舞台与旗舰 PPTX 模板。
- **安全性总览** safety：TEAE / TRAE / ≥3 级 / TESAE / TRSAE / AESI 层级与组间差。
- **临床开发计划** program：多适应症泳道与关键里程碑，季度 / 月 / 日精度，两级泳道，原计划、状态与进度为可选层。同泳道阶段重叠时报错并要求改用子泳道，不改源日期；放不下时先用紧凑尺寸，提示先去掉 insights、kpis、band 再拆页，不删泳道。
- **累计暴露** exposure（08 GANTT-08）：挂在开发计划的研究条上，阶梯图、ICH E1 线、各适应症 NDA 时的达标与差额表和台账；源表给了暴露例数就照抄，不按四舍五入后的比例重算。HTML 里与甘特经计划总线（`KZGantt.publish/subscribe`）共享数据。
- **试验流程** trialflow / study-schema：共同阶段、随机化比例、剂量递增与维持、再随机化子流程、共同随访、子研究，分段线性周轴，关键事件与给药 / 背景治疗时段带；相邻标签相撞时自动错层。
- **竞争格局** landscape：研发阶段加一个有效性、一个安全性指标，null 不当 0；≤4 个带卡、5–8 个不带卡、>8 个分为研发格局、有效性、安全性三页；源材料没有研究出处时不画出处列。
- **有效性汇总** efficacy：连续变量、二分类、时间事件（HR，对数轴参考 1）与率比；率差须与 n/N 一致，每型一条含 0 的差值轴，CI 判定有利 / 不利 / 跨 0；疑似抄错（tte 事件数与某个二分类 n/N 相同）与方向写反时报错。
- **访视流程** soa：访视 × 分组的评估负担与最忙访视，关键节点（入组、随机、主要终点）、给药与背景治疗时段、逐项评估；访视表头为“访视号 / 周次”两行；HTML 有访视与评估项两层下钻（07 DRILL-08）。
- **历时变化**（05 CHART-06）：5 个 kind（longitudinal、longitudinal-diff、lab-boxplot、lab-multiples、completeness）、4 个模板；真实时间轴、CI / SE / SD / 箱线、盲态只画一条全体序列、参考线与正常范围（`ref` 只认 `range` 与 `lines`）、各访视 n；HTML 用 ECharts，可点开历时表并在表内改数。

## 演示动画（15）
- 演示形式由 16 种增至 28 种（新增 waffle、funnel、shift、milestones、pathway 与七个临床形式）。HTML-PPT 中按 scene 随翻页键推进；演示页写 `demo` 与页级 `preset`。
- 舞台容量检查 `fitGuard`：有效性查行高、SoA 查表头相压，放不下时控制台报错并标 `data-kz-fit="overflow"`；15 DEMO-03 写明哪些形式要整行舞台。

## 甘特编辑台（08）
HTML 四轨按 T 打开全页编辑台：精度日 / 月 / 季度、日期点选、里程碑图标、两级泳道、原计划与现计划、状态与进度、文字绑定（`{key}`、`{key.start}`、`{gap:a,b}`）。保存为草稿、写回本 HTML 的数据块，或导出 JSON。图层顺序见 GANTT-06（当前线为灰色虚线，垫在最底层）。

## 检查与文档
- `KZLayoutQC` 新增 `inspectOverlaps`（舞台内不同对象的文字压叠）与 `inspectTextFloor`（按屏幕缩放折算的渲染字号，下限 11 px）；10 增 G5-OVERLAP、G5-LEGIBLE。
- `kz_layout.py render --date` 写页脚月份；回执每页列出 `groups`（animations.json 的键）；模板图形组带 `data-kz-figure`。
- PPTX 原生表格：多行单元格的后续行行距 110%，SoA 按求解后的行逐段写入，PowerPoint 里不叠字、不留孤字。
- 适配与 API：ppt-master 模板页不填 `page_visualizations`；html-ppt 整份采用参考 `deck.css`，`charts.json` 顶层平铺并入 `KZ_DECK_DATA`，交付目录自带 ECharts；`runtime/API.md` 补 KZExplore 载荷、KZGantt 包络、trialflow `after`、SoA `at` 与 `focus`、`ref` 写法。
