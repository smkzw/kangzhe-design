# PPTX 轨道

入口：`ppt-master` 当前安装版的 SKILL 与 routing。不能用 python-pptx 或其他生成器偷偷取代用户指定链路。本包的 Python 工具只做计划、token 派生、审计/原生输出验证；它不直接写最终 PPTX。

新建康哲品牌/样式/布局 workspace 时按上游 Create Template 路由；已有已验证 workspace 可复用。需要直接改用户现有 PPTX 时走上游 Edit Native PPTX，不把原文件当普通 Generate 模板强套。选择 Default/Quick 由上游和用户意图决定；本包不强迫重复确认已确定的品牌和样式。

将 01 chrome/tokens 注入品牌与 layout；02 注入 style；03/04/05/09 注入策划、图像 manifest、SVG 和 notes。保留上游质量检查、原生图表元数据一致性、后处理与导出顺序。已发布设计锁不能被临时手改后不重新校验。

全文可编辑优先级高于逐像素模拟玻璃折射。正文/卡/图/表原生，光学背景独立图片。图表需要原生 data object 时使用官方 native interface；不支持的图型/甘特用有说明的可编辑原生形状，不说成 native chart。

每页内容区及 title/footer 原值，不把字体变化当空间补救。生成背景落在保护槽内；透明卡的局部光场不遮字。非正文页使用11-hero-layouts固定形态，不能“每页换一个金属/纸张/扁平主题”。

最终的最小测试不是导出成功：解包 OOXML 验证对象/文本/字体/alpha/图表数据；LibreOffice 逐页看结构；目标 Windows PowerPoint 或用户指定 Office 真实打开、编辑、保存、重开。后两种环境不能相互冒充。鼠标倾斜、弹窗下钻和日期联动不属于普通 PPTX 静态能力。

适配细节与已核对上游版本见 `adapters/ppt-master.md`。历史与当前的真实集成状态只读review/CURRENT_STATUS.md，不以本轨道说明代替运行证据。
