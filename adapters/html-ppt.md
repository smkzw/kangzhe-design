# HTML-PPT正式适配合同

## 已核查接口
本机runtime.js的initCanvasFit在初始化时把data-w/data-h读为常量，后续resize只更新scale；运行时改data-w不能可靠改变逻辑宽度。它与base.css均明确支持body[data-fit="fluid"]退出固定fit，由主题负责全视口排版。这是宽屏最小适配点，不改上游源码、不增加新引擎。远端基线fd1629067909ff55b36b905476de4e5f26062a1f与本机tree hash分别记录，不冒充相同。

## A03默认：全视口主题
从new-deck.sh创建。body设置data-fit="fluid"；deck保持上游class和导航；CSS覆盖其默认padding，用一套品牌主题单位 `--kz-u = viewport_height / 720`，在16:9桌面与1280×720基准相同。主题使用正常CSS长度/网格，不再给deck或文字transform:scale。桌面正文区域left=56u、right=56u、top=96u、bottom=60u，卡群真实跨该宽度；左页眉锚定，右Logo/页码右锚定，固定分隔线向右延伸。文字/Logo/菱形不横向拉伸。对短内容限制文本行长，不限制整个网格/主视觉的宽度。

共享组件在 `body.kz[data-fit="fluid"]` 下通过 `--kz-component-u=--kz-u` 换算其按钮、甘特编辑标签/字段/状态、面包屑和图表状态等文字；其他HTML轨保持屏幕单位，不继承PPT换算。项目CSS后加载时仍须检查最终computed字号/u，控件和下钻中的必要文字同样不得低于16逻辑px，不准只检查卡片正文。不要把已换算的component变量再乘一次u；此补充不替代项目网格、行高、内边距与字号角色的完整主题适配。

### 材料资源须一起接入（A04 R22）
新版材质的共享kz-glass.css、kz-tokens.css和kz-tokens.js须来自同一冻结包。新增face stop/border tokens不是另一套主题；不能只复制新glass CSS却留旧tokens而让background声明失效。项目覆盖只调整实际布局，不用纯白rgba替换完整材料配方或消去高光/阴影。body图默认保留真实颜色/opacity1；若需要局部遮罩或降色，按04记录范围与合成QC。实际检查未hover/自然电影/冻结和数据面，不能只给鼠标光影样例。

### 文字卡与列表的实际字号（A04 R20）
03 COPY-06适用于每个普通文字卡及业务阅读组。必须检查真正显示的 `h3`、每个 `li`、正文及重点run，不以 `ul` 或外壳的computed值代替后代。A04真实试验在1280×720得到body20逻辑px，在2560×1080却只有13.333：原因是**本包**旧 `kz-glass.css` 对 `.kz-card li` 直接设置未换算的20px，覆盖了项目对 `ul` 设置的30px继承值；不是上游引擎缺陷，也不是单凭此证实模型能力低。

当前共享CSS在 `h3`、`p`、`li` 与 `[data-kz-role="body"]` 的实际节点上通过 `--kz-component-u` 换算字号；站点/流式仍为1。角色tokens保持未经乘u的基准px，不能再将 `--kz-type-body`、`--kz-type-card-title` 全局改成乘u后的值而让组件二次换算；历史快照及其自带旧vendor保留，不混用新CSS与旧的length型u/token方案。项目自身的角色覆盖同样应在实际节点落实正确u，并保留字号、行高、bullet标记和悬挂缩进。普通20逻辑px文字卡不得借compact密度变成16。

HTML必须用真实标题及ul/ol/li、按完整意义分条；已有模板的p标题/整段p不能当作新版验收依据。第一张样卡写完后先验1280与2560的实际后代computed字号/u、全文字形与重点样式，再扩展卡群、L1/L2和全部状态；最终仍执行完整上游及动态门，不因小样通过豁免其余页面。

`tokens.chrome.rule` 是端点数组 `[x1,y1,x2,y2,stroke_width]`，不是矩形 `[x,y,width,height]`。当前右端点1257对应1280基准右距23；HTML用 `left:x1*u; right:(1280-x2)*u; top:y1*u; height:stroke_width*u`，不要把x2当长度相加或得到负右距。PPTX/SVG用原端点和描边宽度，不改固定页眉。

主交付覆盖16:9、2:1、21:9及更宽桌面；狭窄竖屏使用明确的阅读布局或提示横屏，不能把正常中文降到低于16屏幕px来假装适配。若任务要求固定16:9文件，以显式fixed-export配置使用上游fit；它不代表宽屏观看验收。打印恢复1280×720与完整终态，退出打印恢复观众模式。

非16:9桌面（例如1440×900）仍按同一u保留角色字号与左锚，但文字框不能机械套用整套基准宽度。对固定文字角色，从tokens读取基准x、w，基准右留距为 `reference_width - x - w`；实际宽度取 `min(w*u, viewport_width - x*u - right_margin*u)`。这只约束文字阅读框，背景与正文网格仍铺满全视口；右锚Logo另按现有右锚规则。16:9基准框不变，宽屏不借加宽重拼标题；若实际字形仍放不下，按11精简展示名称或按既有行数自然断句，不缩角色字号、不隐藏裁切。分别检查文字框和每行实际字形，不能以“字暂时没出屏”豁免越界框。

四类hero的基准坐标来自tokens：左文字/Logo锚保留；右Logo锚随宽度；目录三等列展开；背景用实际宽幅生成资产按经审阅crop铺满。页眉页脚位置以同一u换算，只有x的右锚随宽度变化。PPTX保持固定画布，无须模拟浏览器resize。

## 禁止上游默认页底进度条
上游runtime自动在body下注入`.progress-bar > span`，它不一定出现在作者HTML中，也不在`.deck`内。必须加载`runtime/kz-glass.css`的`.kz .progress-bar{display:none!important}`；仅正文页保留规定物理页码；封面、目录、章节、尾页不显示页码。不改上游runtime。不准只删除源HTML标签或只在hero页关闭。到最后一页检查computed display、全视口底部截图和实际span边界；蓝/橙全宽线均失败，页眉固定橙线仍保留。

## 可移植资源与普通态启动
new-deck.sh 创建时生成的路径可能仍指向安装目录。交付前把实际使用的官方 base.css/runtime.js 原件及其需要的资源复制到项目资源目录，记录上游与复制件SHA；相对引用只在交付目录内解析，不改上游内容，也不依赖用户机器的隐藏技能目录。分别通过 file:// 和当前HTTP预览实际打开，核对所有必需资源无404、七页正常导航及G7-INIT。scaffold成功不等于可移植交付；先完成这一步，再投入长周期和视觉审阅。

Film 的签名是 `new KZMotion.Film(root, options)`。root 是包含 `.kz-film-stage` 和该舞台内唯一 `.kz-film-carrier` 的外层容器；构造器在 root 的后代中自行查找两者，不接收 carrier 参数。先取得并断言这三个 DOM 节点的嵌套关系，再调用构造器；不要把 stage 本身作为 root，也不把整张含固定 chrome 的 slide 当作几何舞台。专用外层容器或该页唯一拥有的包含范围可以作为 root。不得使用未声明的 carrier 变量。DOM 根节点与 Film 实例句柄分开持有；四业务阶段和首尾同形接续仍按06处理。代码异常必须修复，不能用删除电影、只留静态图或吞掉异常代替。

## 生命周期和真实挂载
顺序：上游base/theme → kz-tokens → kz-glass → 品牌布局；上游runtime → kz-motion/其他所需组件 → html-ppt-bridge →项目装配 → kz-audience。`kz-audience.js`清除兼容旧示例的播放器UI，不接管动画时钟/翻页；新页面从源头不生成这些控件。
`KZHTMLPPT.bind(deck,factory)`只观察上游直接子slide，排除overview克隆。factory必须返回enter/leave/dispose并接入每张卡的reveal、合法tilt/光源和float；图表/甘特/film按需调用播放、暂停、resize。不要只写chart.play便称整页动效通过。动画对象与最终清单一一对应，缺一项就记录失败。

退出卡片可借上游现有500ms淡出窗口执行240ms退出；不拦截翻页、不改hash。输入与dialog内部阻止对应方向键冒泡，保留输入默认行为。观众界面不加任何播放/暂停/重播/进度按钮。活动页自动进入动效，后台暂停原因互不覆盖；preview静态，打印全部数据，不留隐藏页RAF。

## 当前上游旧康哲指引的替换
本机html-ppt/SKILL.md的Hybrid条目仍提旧design_specs/assets/htmlppt/gx_fx.css、gx_fx.js及htmlppt_fx.md；它们属于停用包，不得寻找或加载。A03对应能力来自本包runtime/kz-motion.js、kz-glass.css与实际组件装配。其150–320字备注和ribbon资产不是康哲6.0约束，分别由09与11管理。其删除runtime主题处理代码的建议不采用：不声明data-themes，保留原runtime，品牌样式后加载。不修改上游来掩盖这些差异。

## 上游验收
必须保存真实scaffold命令和版本；实际深链接/箭头/overview/S双窗同步、preview、print和离线资源检查。fluid模式下presenter预览是独立viewport，不保证天然复制观众的超宽比例：要测试，必要时向预览传递演示比例或把其边界列为未通过，不声称完全同画。当前真实覆盖以review/CURRENT_STATUS为准。

### 正式静态截帧兼容路径
先读当前上游 `scripts/render.sh` 的实际接口。本次已测版本仅接收 `<HTML文件> [页号|all] [输出目录]`，用 `file://实际文件#/页号`，固定1920×1080、virtual-time-budget=4000，无 query 或就绪等待参数。普通源页可能在上游500ms透明度过渡中被截帧；延长 virtual-time 并不能证明能等到真实 compositor 终态。不得把低透明度 PNG 当完整导出，也不为导出取消观众动画。

确有该问题时，从当前观众源自动派生同目录的 `capture-only.html`，资源路径和官方 runtime/hash 导航不变；仅此副本链接静态 CSS，取消过渡/浮动，并确保活动页 opacity=1、其他页仍由上游控制。项目装配还必须识别**只属于副本**的冻结标志，将图表/甘特和电影置于已验证完整静态态；单独禁用 CSS 不能让未出现的数据自动完整。

捕获标志由项目装配层识别，不能猜测存在 `freezeForPreview()`。当前实测七页工程以 `body[data-capture-only]` 或 `body[data-preview]` 选择静态分支：page.finish()、chart.finish()、gantt.finish()呈现完整终态；不启动普通Film，另以静态文字展示完整阶段与限制。其他工程可按自己已核实的公开接口装配静态态，不能复制一个没有定义的方法名。不可猜测把 URL query 写进文件名，也不修改官方 renderer/runtime。观众 `index.html` 不引用捕获 CSS 或冻结标志；改源后重新派生捕获副本，不保留过时正文。

最后必须实际调用原 `render.sh capture-only.html all 输出目录`，逐页检查真实 PNG/尺寸、活动页 computed opacity=1、完整文字/数据、字号和品牌 chrome；另验观众源普通自动播放与进出。正式脚本1920截图不代替2560宽屏运行检查。记录观众源与上游源码前后hash、副本diff和真实返回码，明确“官方工具＋静态副本”，不宣称普通源未经适配已正常截帧。

## 固定双菱形
调用 `tools/brand_fragments.py` 的 `facets(prefix=页面唯一前缀)`，插入原页眉 SVG，保留 1280×720 基准坐标。若独立 SVG，使用 viewBox="0 0 100 90"，宽高各为 100u/90u，左上锚定 0/0，禁止随页面宽度横向拉伸。不要把静态 SVG 作为 img 后误以为内层 class 能被宿主 CSS 动画控制：采用 inline SVG，加载 kz-glass.css 并保留 `.kz-float` 整组。标记内部四形状不再单独施加动效。普通播放自动微浮动；冻结/减少动态/打印恢复基准，无播放器 UI。

## Responsive图片登记
使用picture/source切换标准与超宽真实源时，按04的image.viewport_assets记录精确目标视口有效asset_id；媒体条件是项目实现，不是第二个fit引擎。逐视口检查currentSrc及源SHA/裁切，正式capture-only仍从同观众源派生，不默默换回未经登记图片。

### 静态布局与观众布局绑定
静态分支不创建 Film 时，不能依赖它平时写入的 inline 几何来覆盖通用组件 CSS。项目静态样式必须显式采用已审阅总览帧的有效几何、内容宽度和内边距；核对最终 computed 值与完整文字 Range，而非只检查 opacity。共享 carrier 的默认位置、尺寸或 align-items 不得使静态副本退回小载体、窄内容列或顶端拥挤。静态分支可选择合法完整总览，不要求复制动态帧，但字号、事实、完整数据及品牌锚不得改变。preview、RM、capture、print 分别在其真实宿主环境验证，不把一种模式通过推广到其他模式。
