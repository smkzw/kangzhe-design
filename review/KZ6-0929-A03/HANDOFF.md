# HANDOFF · KZ6-0929-A03

## 1. 状态

**PARTIAL**。规范6.0.0，唯一入口kangzhe-design；入口SHA256 `31d1e6684c8eb2bd4827512922312392f49ba62ea22dc0d070938b3bbc4d8b04`。当前源起点d5b31e49；最终提交、安装与public发布由publication/installation回执绑定，不能把发布算验收。

观众页面已去除播放器式控件；动画自动发生，保留正常翻页/业务详情/Gantt编辑。最新50项组件通过，EGO七页×三桌面尺寸21次观察无横向溢出/播放面板。

未完成前三项：①最终A03 PPTX原生Office编辑/重开BLOCKED，LO面积缺失值填充仍有renderer风险；②site/stream、复杂电影/宽L1/L2及H02–H04未全闭环；③异质模型×harness与第二VLM能力档未完成，第3审阅节点终态回执也缺失。

## 2. 执行事实

|目标|修改/产物|真实执行及证据|结果|
|---|---|---|---|
|完整审计与12例归因|PRECHANGE_REVIEW、DEEP_ANALYSIS、REQUIREMENTS_MATRIX|原A01原件+独立CB审计+仲裁|没有足够证据判MODEL_LIMIT|
|规范重构|01/02/03/04/06/10/11、tokens/schema、adapters|当前Git差异；26合同检查|规则已写，视觉不自动全过|
|无播放器且自动运行|kz-audience、component-lab、27工作预览、7页HTML|components-final、ego-film-no-player-r4、normal-film-cycle-r4|50项组件通过，实际无控件且时钟推进|
|宽屏、倾斜光影|fluid、mountPage、layout-qc|ego-motion、ego-7pages-3viewports-final；IAB截图|局部行为通过，非所有影片审片|
|原生可编辑结构|matched-seven-fixed.pptx|pptx-export-final、frame-binding-final、native-inspection-final|Default真实7页；原生图表/工作簿/形状存在|
|Office编辑回读|native-office-current-status|CUA加载未形成文档，最终文件未实际编辑|BLOCKED，LO不替代|
|真实生图|assets/body-wide-generated.png|imagegen真实工具receipt+prompt+hash|1931×814；未达2560目标|
|模型调用|model-runs/raw-native/receipts|8制作+3审阅实调用|分层PARTIAL/FAIL/INCOMPLETE|

手写代码、组件测试、上游实产、Office和跨模型分别列出；owner补改不是测试模型成功。上游安装无.git，使用A01 environment记录的真实tree hash（ppt-master65092fd6…，html-ppt154596a0…），不把remoteHEAD当安装SHA。

## 3. 模型运行

|case|模型与harness|spec入口hash|预算/实际秒|结果|
|---|---|---|---|---|
|cb-before|deepseek-v4.1-flash(max) / CodeBuddy CLI|48bf0991dc98|600 / 600.047|PARTIAL：2页HTML；旧宽屏/平菱形/底条失败；无终态交接|
|pi-before|openai-codex/gpt-6-luna(max) / Pi/OMP|48bf0991dc98|600 / 600.139|INCOMPLETE：仅引擎模板/素材，无任务终稿|
|cb-after|deepseek-v4.1-flash(max) / CodeBuddy CLI|da48ee4fd130|600 / 600.025|PARTIAL：2页改善宽屏/菱形/卡片；底条仍失败|
|pi-after|openai-codex/gpt-6-luna(max) / Pi/OMP|da48ee4fd130|600 / 600.013|PARTIAL：新版已有2页任务HTML；底条/QC未关闭|
|cb-holdout-pptx|deepseek-v4.1-flash(max) / CodeBuddy CLI|da48ee4fd130|600 / 257.315|PARTIAL：Default真实3页原生PPTX，未完成视觉/Office；不是超600秒|
|cb-site|deepseek-v4.1-flash(max) / CodeBuddy CLI|da48ee4fd130|600 / 334.464|FAIL：生成2页；40轮上限；site-common的line/el接口错配|
|pi-stream|openai-codex/gpt-6-luna(max) / Pi/OMP|da48ee4fd130|600 / 600.029|INCOMPLETE：18 read +5 todo，无目标文件|
|cb-r2|deepseek-v4.1-flash(max) / CodeBuddy CLI|31d1e6684c8e|600 / 251.213|PARTIAL：播放面板/底条已移除；40轮上限；站点仍有JS错误|

冻结spec整包manifest在baseline/candidate-r1/candidate-r2，不能只用入口hash代表全包不变。新调用不重启模型；冷启动/纯生成时间未被可靠拆分，记UNKNOWN。R2是从R1复制后的一个修复轮，不是从零生成。原始输出在raw-native，模型原件与后期工作预览用beforehash/zip区分。

独立CB归因审计268.639秒；Gemini第一轮115.364秒；最后一轮480.023秒有实质读图报告但缺终态runner回执。没有伪造额外VLM档。

## 4. 发现与归因

|完成事实|反思/建议|
|---|---|
|宽屏旧合同与上游fluid接口冲突已修|可执行默认与清晰适配比重复抽象形容词更有效|
|四项缺陷也存在owner样板|不能据此怪罪12例弱模型；先分规范与接线问题|
|Pi仍有预算内过度读取/未写入|可判断该route交付调度弱，无法分离模型与harness因果|
|CB新版视觉改善且R2去底条|整例QC/交接缺失及site JS错误仍不能算成功|
|owner清理器误删电影、测试器漏CSS已修|保留失败日志；必须同时检查无控件和动画仍存在|
|第三盲审发现章节对应错误并修复|规则增加目录/章节/正文同源映射门，仍不编造复审|

细化归因和原12例每一条证据见DEEP_ANALYSIS。

## 5. 修订理由与替代方案

沿用html-ppt-skill官方fluid退出固定fit，不建立第二套导航。页眉/页脚/官方Logo/颜色/字号不变；PPTX原生多面渐变近似玻璃，不整页光栅化。源图尺寸接口只接受prompt，2560目标未满足而非偷偷放宽；不放大冒称原生。最新用户要求取代旧可见播放控制规范；后台生命周期保留，未更改产品方向。

## 6. 验证覆盖

实际：26合同、50Chromium组件、5桥接、36秒正常时钟/同节点1圈；EGO1920×810指针/光源/RM；1280×720、1920×1080、2560×1080七页无溢出/播放器；IAB真实截图；Default导出与LO逐页补充。24声明文本框绑定及未声明ZIP部分检查，最终小改由receipt记录；原生结构检查不冒称编辑回读。

失败日志保留：components-no-player缺CSS、components-r3动画载体误删、ego旧文档未reload误判、native Office加载、LO缺失面积填充、两harness超时/工具上限。

没有完整验证：最终Mac/WindowsOffice编辑回读、Safari/presenter、复杂统计图、全部业务电影正常速度视觉审片、三模型能力档/两VLM能力档。计时器循环不是电影审美合格证。

## 7. 效率

预算按整项600/480秒含恢复强制终止；不再沿用旧pilot恢复追加预算。复用运行服务/已安装引擎/缓存真实生成图；本轮实际新增生图一次。纯推理/渲染时间无法可靠拆开，UNKNOWN；总耗时见回执，不采信模型自报。CB site/R2触及40轮分别334.464/251.213秒；H01实际257.315秒，撤回其自报超600秒。

## 8. 下一步

1. 在可连接的原生PowerPoint打开最终hash，编辑文字/图表/甘特、保存重开，确认缺失数据语义；保留环境BLOCKED直到实测。
2. 修复并冻结新site，补全stream；逐页/章完整电影及宽L1/L2，再做H02–H04，不用组件demo代替。
3. 获得后续预算后做同模型跨harness/不同能力VLM对照；保留本轮原始失败，不在后台无限重试。

无新增产品方向问题需要用户决定；下一阶段主要是验证能力与测试预算。
