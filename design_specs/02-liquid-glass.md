# 02 统一 Liquid Glass 材质

## 定位
康哲化的材料语言：透光、边缘折光、空间层次、柔和阴影和随指针变化的光。它不声称遵守 Apple 的界面规范，也不是全页高强度模糊。Apple 的原始设计面向控件与导航；本包按用户要求扩展到汇报卡片，靠高散射的阅读面承载高密度内容。

## 一种材料、三个用途 LG-01
| 用途 | 表现 | 底线 |
|---|---|---|
| 正文卡 | 近白高透光三停渐变面、rim 折光边、局部短高光、三层暖色阴影 | 全页同族；不能一半实色扁卡一半夸张玻璃 |
| 数据阅读面 | 同族外壳，内部近白、无移动反光 | 刻度与比较不折射、不透视、不变形；不再叠一层模糊 |
| 叙事载体 / 浮层 | 更高散射的面（`glass.carrier_face_gradient`）+ overlay 阴影 | 几何逐帧变化的载体不带 backdrop-filter（06 FILM-05） |

颜色、圆角、渐变停、rim、高光、阴影全部来自 tokens（`glass.*`、`elevation.*`），runtime 由 `tools/build_tokens.py` 生成的变量取用，项目 CSS 不另写一套配方。

一张正文卡至少包含：
1. 面：`glass.face_gradient` 三停（alpha ≤0.62），HTML 加 `backdrop-filter: blur(glass.blur_px) saturate(glass.saturate_pct)`；
2. rim：`glass.rim` 渐变描边，亮—暗—暗—亮，角度随指针在 `angle_swing_deg` 内转动；
3. 高光：顶边短高光，长度 ≤ `glass.highlight_extent_max`（30%）边长，随指针水平滑动；镜面光斑跟随指针位置；
4. 阴影：ELEV-01 的动态三层阴影。

嵌套在玻璃内的小字段、表格行和 chips 用 `.kz-thin` 同族薄覆层（渐变面 + 细边 + 轻阴影），不再模糊。禁止多层毛玻璃叠加、全页强 blur、或在原有卡片上再覆盖一张卡来压住复杂背景。

## 阴影层级 ELEV-01
阴影是三层叠加：接触影（紧、偏深）、主光影（中等模糊，随光源偏移）、环境影（大而淡）。阴影色用暖褐 `elevation.shadow_rgb`，不用纯黑。单层 alpha ≤ `elevation.alpha_max_per_layer`。

| 级别 | 用于 |
|---|---|
| `rest` | 静止的正文卡、数据外壳、Bento 首屏舞台 |
| `raised` | 悬停或键盘聚焦的卡（由 `--kz-lift` 从 rest 插值到 raised） |
| `overlay` | 下钻弹窗、电影载体、工具浮层 |

主光影与环境影按指针光源方向偏移（`elevation.light_offset_px`）：光在左上，影落右下。抬升时卡片同时上移 `elevation.lift_px`。禁止黑硬影、霓虹边和高饱和大光晕。

## 指针光源与倾斜 ELEV-02
桌面鼠标移动时，卡片的光源位置（`--kz-mx/--kz-my`）、rim 角度、高光位置、阴影偏移和抬升一起变化；倾斜由同一组变量合成。`KZMotion.mountTilt` 用临界阻尼弹簧驱动这些变量，静止后停止 rAF；只有被挂载的元素承载 transform。

- 倾斜上限：正文卡 `motion.tilt.body_max_deg`（4°），hero / 目录卡 `hero_max_deg`（6°），透视 `perspective_px`。
- 表格、图表测量面、甘特编辑面不倾斜，只保留光与抬升。
- 拖拽、选字、编辑、触屏、减少动态、冻结态关闭倾斜并复位。
- 没有挂载 JS 时，CSS 悬停仍会抬升卡片（`@property` 过渡）。

## 可感知材料 LG-04
“生过图”“fill 有 alpha”“CSS 有 blur”都只证明接口存在，不证明观众看见了玻璃。完整合成页在未悬停、动画中段和冻结态都必须能分辨：微暖透光面、连续折光边、短高光、柔和的空间影。卡面呈近不透明米黄色块，或静止时看不到任何高光，按不通过计。正文中间仍要安静，但不能把背景光影和卡面差异一起抹成纯白。

opacity 的写入位置会影响玻璃：祖先元素 opacity<1 时，Chromium 会把它当作 backdrop root，子元素的 backdrop-filter 只能采样到空白，模糊在淡入结束时突然出现。因此入场淡入写在玻璃元素自身（06 MOTION-04），HTML-PPT 的翻页不在 slide 容器上做透明度渐变（06 MOTION-08）。

## 下钻阅读隔离 LG-05
打开宽幅下钻时，后方页面的文字不得透到弹窗阅读面上。`kz-drilldown.js` 在弹窗之外互不嵌套的背景根节点上临时挂隔离类：模糊后方、暂停后方 CSS 动画；弹窗及其内容不加 filter。返回上层保持隔离，关闭或 dispose 后释放，并保留原有 class、style 与滚动锁（多实例引用计数）。只看 `CSS.supports` 或声明值不能证明隔离有效，须看实际画面。

## 色条禁令 LG-02
任何轨道、密度、卡型都不得用沿卡片一条边覆盖大部分长度的彩色条作装饰：border-left/top、独立矩形、伪元素、inset 阴影、渐变伪装、带色通长底边都算。可以用短编号、文字色、语义图标、局部光晕、短高光。卡片四周的中性细折光边、甘特条、统计柱、正文页固定橙线不属于色条。检测须结合对象角色与几何位置，不能简单禁止所有长矩形。

## 圆角与空间
正文卡、紧凑卡、对话框分别用 `glass.radius`、`radius_compact`、`radius_dialog`。外壳与内层圆角按内边距同心缩减。不把所有卡做成药丸形；自由形液态载体只出现在有语义的电影或 hero 中。

## PPTX 玻璃 LG-PPTX
PPTX 用原生可编辑的渐变填充（停点 alpha 保留）、描边和外阴影，必要时加独立的局部光学贴片；贴片不含文字或数据，不整卡栅格化。

- 阴影：ppt-master 每个对象只转换一个效果；`feDropShadow` 偏移非零才是外阴影，`dx=dy=0` 会变成 glow；导出 alpha ≈ 作者值 × `elevation.pptx.export_alpha_factor`（0.75）。用 `elevation.pptx.rest / raised` 的作者值。
- 三层阴影在 PPTX 里不叠：同级正文卡只用一个主阴影；hero 或抬升卡需要环境影时，在卡底外加一个径向渐变接触椭圆（中心 α≈0.06 渐到 0），不要在半透明卡面下垫深色底板（会透出来把卡面染灰）。
- inner shadow、soft edge、背景模糊、mask 在 ppt-master 中必须预先栅格化，玻璃卡不用它们。
- 指针光源、倾斜和动态折射不是 PPTX 的能力，不得宣称实现。
- `tools/glass_svg.py` 给出上游 Executor 可直接参考的原语；实际导出与回读证据见 `examples/reference/pptx/README.md`。

## 双菱形 LG-03（仅 PPTX 与 HTML-PPT）
唯一外观来自用户指定的原生对象 `assets/header-mark/source-native.xml`：橙色大形在后，黄色小形在左下前方；倒角、坐标、渐变、阴影、softEdge 和叠放顺序全部保留，不用普通四边形近似，不加侧折面、白色高光线、光晕，不随部门换色，通用玻璃规则不改造它。

- PPTX：ppt-master 导出后用 `tools/bind_header_mark_pptx.py` 按显式页码与对象 ID 替换为原生对象，保留上游原件，再跑上游 `pptx_delivery_check.py`。
- HTML-PPT：用 `tools/brand_fragments.py` 从同一资产生成内联 SVG，放置矩形由 `tokens.chrome.header_mark.placement_htmlppt_u` 唯一决定；整组 `.kz-mark-float` 竖直微浮动（`motion.header_mark_float`，2px / 6.4s，同相位），不左右漂移、不旋转、不缩放；减少动态、preview、打印、冻结态回到基准。
- 站点式与流式 HTML 不出现这组装饰，也不保留空占位。

## 反例与正例
不合格：纯白扁卡配左橙条；满屏橙色胶囊；玻璃外壳上再叠四层半透明卡；穿过笔画的高亮折线；黑底“高级感”；真实数据做成透视立体柱；只靠强 blur 掩盖背景冲突；所有卡的阴影都是同一张静态投影。

合格方向：浅白光场 + 少量橙黄折射 + 同族玻璃卡 + 稳定深色文字 + 平直准确的数据面；悬停时光与影跟着指针走，卡片轻轻抬起，离开后平稳落回。
