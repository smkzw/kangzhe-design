# 公开装配接口

此页描述当前实现的可调用接口，不新增设计阈值，不代替规则所有者。先完成阶段计划和资产保护审阅，再按实际页型挂载。数据格式仍以对应 schema / 05 / 08 为准。上游拥有活动页、导航、hash、演讲者和导出；这里没有第二套演示引擎。

## 页面微交互

`KZMotion.mountPage(root)` 从 root 内收集 `[data-kz-reveal]`、`[data-kz-tilt]`、`[data-kz-light]`，返回 `{enter,leave,finish,dispose}`。它已拥有 reveal 和 tilt，不对同一 root/目标再调用 mountTilt 或 reveal。root 不能与另一个挂载范围重叠。布局外壳、reveal 层、tilt 玻璃层分别拥有 transform；阅读内容放在玻璃层内。`[data-kz-light]` 仅光源，数据面不倾斜。

卡片外层默认不加 preserve-3d；须真实鼠标驻留核验，避免变换后 hit-test 触发 leave 即复位。层级和反例由 06 管理，接口挂载成功不证明实际 hover 稳定。

独立使用时：`KZMotion.mountTilt(root)` 返回 `{dispose}`；`KZMotion.reveal(root,{exit:false})` 返回 `{finished,cancel}`，退出使用 `exit:true`。退出序列在 finished 后仍保留 forwards 与目标所有权；必须保留返回句柄，在复入/换驱动者前调用 cancel()。这些是另一种装配选择，不与 mountPage 重复挂载。微浮动由 kz-glass.css 的 `.kz-float` 及活动/冻结状态控制，不存在 mountFloat()。

这些CSS浮动不是Film的RAF，也不由mountPage.finish自动静止。调用方以唯一owner将真实document.hidden同步到`.kz`宿主的`kz-background-paused`类，首次挂载即同步，visibilitychange使用本项目AbortSignal并在dispose释放；恢复显示只解除这一原因。实际inactive页的data-kz-motion-active=false、RM、capture/preview/print各自继续冻结。float/reveal/tilt必须由分层或独立属性承载，文字随同一阅读层浮动；记录真正6.4秒轨迹，而不是仅验证hover。

## HTML-PPT 生命周期

`KZHTMLPPT.bind(deck,factory)` 位于 adapters/html-ppt-bridge.js。factory 接收上游 deck 的每个直接子 slide，返回 `{enter,leave,dispose}`；桥返回 `{sync,dispose}`。概览克隆不挂载。初始 bind 抛错会清理已返回的生命周期并断开观察器；factory 在返回前自行创建的资源须自行回滚。enter/leave 成功后才提交桥内活动状态，异常不记成功，修复后可显式 sync；项目 QC 必须记录异常为失败。dispose 即使某个生命周期抛错也释放其余组件，最后报告聚合错误。调用片段（依赖已经由正式脚手架生成的 deck 与所需脚本，不是独立成品）：

```js
const bridge = KZHTMLPPT.bind(document.querySelector('.deck'), slide => {
  const page = KZMotion.mountPage(slide);
  return {
    enter() { page.enter(); },
    leave() { page.leave(); },
    dispose() { page.dispose(); }
  };
});
// 工程自己的销毁入口调用 bridge.dispose()。
```

图表/甘特/电影另加入同一 factory 的生命周期。捕获/preview 分支由项目装配层完成全部数据终态，不能假设组件有 freezeForPreview() 或桥自动实现它；具体静态副本路径见 adapter。正式观众源保持自动动效。加载顺序见 adapter，不修改上游 runtime。

## ECharts 数值图

先加载随包 ECharts 与 kz-tokens.js，再加载 kz-charts.js。调用 `KZCharts.mount(el,data,options)`；data 为 `{kind:'line'|'bar'|'column',categories:[...],series:[{id,name,values:[number|null]}],unit,...}`，可选 axis:{min,max,interval}、decimals、area、description。各系列长度等于类别数；null 保持缺失，绝不写成零。

options 可提供 `onProgress(progress,currentData)` 和 `onDataClick(echartsParams,currentData)`。返回 chart、play(durationMs)、finish()、renderProgress(p)、getData()、getProgress()、setData(next)、resize()、pause()、resume()、dispose()。pause() 实际完成到真值；resume() 无重播行为，重新进入时显式调用 play()。普通态 play() 同步从0开始，再按单一RAF时钟递增到1；RM/打印与pause/finish仍显示完整真值1，不先跳满再归零。使用 onProgress 将数字与图形绑定；项目负责离页完成、静态完整和最终 dispose。KZCharts.option(data,options) 是低级 option 工厂，通常不需使用。

显式axis可只给一端，另一端由完整数据的自动范围决定；合并后必须min<max，否则validate在初始化ECharts之前拒绝。显式科学端点未给interval时，由ECharts按该范围决定步长，不强制改成自动1/2/5范围。自动范围在增长动画中固定。onProgress收到当前数据的独立拷贝；20万点工厂探针只验证不触发参数展开栈溢出，不表示20万点动画性能或可读性已通过。

## 可编辑季度甘特

`KZGantt.mount(root,data,options)`；数据为 `{min,max,tasks:[{id,label,start,end,...}]}`，整数季度来自 KZGantt.qindex(year,quarter)。区间是 **[start,end)**；展示“含结束季度”须把结束季度 index 加 1，不能再额外加一整年。root 由组件创建 plot/editor，项目提供尺寸。支持 onProgress(progress,currentData)，单一数据对象驱动图形与读数。

返回 chart、root、plot、select(id)、play(durationMs)、finish()、getProgress()、getData()、getSelected()、getDirty()、commit(start,end)、undo()、reset()、serialize()、geometry(id)、importJSON(text)、pause()、resume()、dispose()。commit 修改当前选中任务；importJSON 只支持相同轴和同序任务 ID。普通态play同步从0开始，再自然增长到1；RM及pause/finish显示真值1。销毁后不再play/finish/draw，不创建新RAF或调用已释放图表。编辑自动结束入场，避免动画覆盖修改；表单/拖移/两端延展/键盘仍须真实测试。没有 exportExcel 或原生 Excel 接口。

绘图区的max是半开区间边界，末端刻度不标成下一年的业务时期；当前工厂省略该边界标签，范围标题和编辑器继续显示真实含结束季度。不移动条形、不减一季度、不把max改为含端点。

## 宽幅多层下钻

`new KZDrilldown.Drilldown({host,onOpen,onClose})`；host 必须在 `.kz` 作用域。`push({id,title,render},trigger)` 的 render 接收 (section,drill)，用 DOM/textContent 写真实内容并返回可选 `{pause,resume,dispose}`。下级 push 使用新的层 ID；父层隐藏/暂停而不是销毁。方法为 push、pop、close、snapshot、dispose，snapshot 仅报告状态，不验证内容完整。

多层数据/电影仍由项目装配，父层返回时恢复焦点/滚动。onOpen/onClose 可暂停/恢复原页面的相应后台原因；不要清除其他暂停原因。组件捕获 renderer 抛错会显示“明细未能加载”，项目 QC 必须把这个错误视为未通过，不能因为弹窗打开就判成功。

首次打开时组件给弹窗祖先路径以外的互斥背景根挂载内部类`.kz-drill-background`：只模糊后方页面并暂停其CSS动画，不模糊弹窗或改写背景内联filter。close/dispose引用计数释放该类与body滚动锁，保留外部已有class、overflow值和priority；返回上层仍保持隔离。背景JS电影仍由onOpen/onClose管理相应暂停原因，弹窗内当前层电影继续正常自动播放；此内部类不是全站背景主题。

## 连续电影

`new KZMotion.Film(root,options)` 要求 root 内已有 `.kz-film-stage` 与同一 `.kz-film-carrier`，并提供 options.frames、duration。帧结构为 `{t,x,y,w,h,r,tint:[r,g,b,a],label,caption}`，首尾回接按 06。可选 managedText:false 由项目业务时钟写文本；onRender(frame,progress,film) 的 frame.index 来自同一几何采样，供同步业务状态。另有 staticProgress、minCarrierWidth 参数；数值从实际计划/token 取，不在此页复制设计默认值。

这些几何值是相对于实际舞台的归一化值，不能把 x/y 当作载体中心坐标。当前 `validateFrames` 要求至少四帧，t 严格递增且端点为0和1；每帧 x/y 非负、w/h 为正、x+w 与 y+h 均不超过1（当前实现仅容许1e-5浮点误差），r 在0–0.5之间。tint为四项RGBA数组，RGB为0–255、alpha为0–1；首尾几何、材质和文字满足同一合同。业务状态数量不等于帧数量：N个业务状态还须追加一个t=1的回接帧，复制第一状态的几何、材质和文字。四个状态仅映射到0/.25/.5/.75会被拒绝，不能把启动失败误认为静态阅读态。譬如 w=.70 时，x=.48会被构造器拒绝，而不是自动裁切为合法运动。最小宽度在后续render中的调整不能救非法输入帧。

构造成功后当前实现设置 root.dataset.kzReady='true'，render更新 root.dataset.kzProgress；返回实例的snapshot也提供进度、同节点及暂停原因。dispose清除这两项root状态属性，carrierId保持节点身份。这些是当前组件的实际接口，不要求其他项目时钟冒用同名属性。普通态须实际确认初始化成功、有限进度、自动变化和完整回接。异常、未挂载、缺失/NaN进度或EMPTY不算动画通过；静态副本可能不创建Film，须另测普通观众源。电影初始化错误还可能阻断同一enter中的图表play，图表真值与联动须另作断言。

舞台尺寸来自真实 `.kz-film-stage` 的clientWidth/clientHeight。当前共享CSS同时设 `height:440px; min-height:320px`；嵌入较矮的PPT正文卡时，项目只覆盖height不会取消min-height，实际舞台仍可能撑破卡片。项目须在自己的作用域一并设定合理height/min-height，并实测正文卡、标题、说明、图表、页脚的联合容量；不能裁字或缩字遮溢出。内层叙事载体置于玻璃阅读卡时保持同族，但不得再叠加第二层backdrop采样；02负责材质硬门。

隐藏容器可先挂载，初始stage可能为零尺寸；ready只证明初始化，不证明可见布局。实际活动页必须等待舞台宽高为正及ResizeObserver重新render，再测effective几何/字形/保护区；零尺寸snapshot不算可见状态通过。

离页若项目调用 `film.pause('engine-inactive')`，复入必须调用 `film.resume('engine-inactive')`；IO或resume其他原因不会清除它。保留其他hidden/modal/RM原因，并实际测离开后返回，不用初次自动播放推定复入正确。

Film 自动开始，返回 pause(reason)、resume(reason)、seek(progress)、snapshot()、dispose()；没有 play/reset/static_summary 方法。pause/resume 按原因集合管理；seek 仅后台 QC/捕获，不呈现播放器。Film 已管理 RM/可见性/打印/自身 resize；项目自己的 observer/listener/timer 仍须释放。静态总览是项目内容合同，不是某个 Film 方法。能力边界与语义电影验收见 06 与 runtime/README。

## 计划和证据

`tools/qc_plan.py PLAN --manifest MANIFEST --asset-root ROOT --out REPORT` 是现有语义预检：不只 schema，还检查图像映射、真实 hash/像素、每视口裁切、品牌字号、卡片动效清单等。它输出 pending/review/warning；不是视觉、动态或指定引擎放行证书。项目页数/源事实清单与实际 DOM 仍须逐项对账。没有 plan init、plan validate --stage 这类 CLI，不要猜测调用。

### 从业务状态构造完整回接帧的最小示例
下面只装配当前Film的参数，非另一引擎。`states`至少三项，每项已经提供合法x/y/w/h/r/tint/label/caption。更复杂片段按真实阅读停留设计t，不强制均分。

```js
function loopFrames(states) {
  if (states.length < 3) throw new Error('至少三个业务状态');
  const frames = states.map((state, i) => ({...state, t: i / states.length}));
  frames.push({...frames[0], tint: [...frames[0].tint], t: 1});
  KZMotion.validateFrames(frames);
  return frames;
}
```

构造器前先验证实际frames，再验证普通页面的ready、有限进度和自然增长；不能仅检查film-plan中的端点。项目onRender使用frame.index时，将回接帧索引按业务状态数归回第一状态，避免多出不存在的业务阶段。四状态示例的五帧必须保留所有四个业务状态，不能复制第一状态来删掉最后一段。
