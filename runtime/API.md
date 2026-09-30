# 公开装配接口

此页描述当前实现的可调用接口，不新增设计阈值，不代替规则所有者。先完成阶段计划和资产保护审阅，再按实际页型挂载。数据格式仍以对应 schema / 05 / 08 为准。上游拥有活动页、导航、hash、演讲者和导出；这里没有第二套演示引擎。

## 页面微交互

`KZMotion.mountPage(root)` 从 root 内收集 `[data-kz-reveal]`、`[data-kz-tilt]`、`[data-kz-light]`，返回 `{enter,leave,finish,dispose}`。它已拥有 reveal 和 tilt，不对同一 root/目标再调用 mountTilt 或 reveal。root 不能与另一个挂载范围重叠。布局外壳、reveal 层、tilt 玻璃层分别拥有 transform；阅读内容放在玻璃层内。`[data-kz-light]` 仅光源，数据面不倾斜。

卡片外层默认不加 preserve-3d；须真实鼠标驻留核验，避免变换后 hit-test 触发 leave 即复位。层级和反例由 06 管理，接口挂载成功不证明实际 hover 稳定。

独立使用时：`KZMotion.mountTilt(root)` 返回 `{dispose}`；`KZMotion.reveal(root,{exit:false})` 返回 `{finished,cancel}`，退出使用 `exit:true`。退出序列在 finished 后仍保留 forwards 与目标所有权；必须保留返回句柄，在复入/换驱动者前调用 cancel()。这些是另一种装配选择，不与 mountPage 重复挂载。微浮动由 kz-glass.css 的 `.kz-float` 及活动/冻结状态控制，不存在 mountFloat()。

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

options 可提供 `onProgress(progress,currentData)` 和 `onDataClick(echartsParams,currentData)`。返回 chart、play(durationMs)、finish()、renderProgress(p)、getData()、getProgress()、setData(next)、resize()、pause()、resume()、dispose()。pause() 实际完成到真值；resume() 无重播行为，重新进入时显式调用 play()。使用 onProgress 将数字与图形绑定；项目负责离页完成、静态完整和最终 dispose。KZCharts.option(data,options) 是低级 option 工厂，通常不需使用。

## 可编辑季度甘特

`KZGantt.mount(root,data,options)`；数据为 `{min,max,tasks:[{id,label,start,end,...}]}`，整数季度来自 KZGantt.qindex(year,quarter)。区间是 **[start,end)**；展示“含结束季度”须把结束季度 index 加 1，不能再额外加一整年。root 由组件创建 plot/editor，项目提供尺寸。支持 onProgress(progress,currentData)，单一数据对象驱动图形与读数。

返回 chart、root、plot、select(id)、play(durationMs)、finish()、getProgress()、getData()、getSelected()、getDirty()、commit(start,end)、undo()、reset()、serialize()、geometry(id)、importJSON(text)、pause()、resume()、dispose()。commit 修改当前选中任务；importJSON 只支持相同轴和同序任务 ID。编辑自动结束入场，避免动画覆盖修改；表单/拖移/两端延展/键盘仍须真实测试。没有 exportExcel 或原生 Excel 接口。

## 宽幅多层下钻

`new KZDrilldown.Drilldown({host,onOpen,onClose})`；host 必须在 `.kz` 作用域。`push({id,title,render},trigger)` 的 render 接收 (section,drill)，用 DOM/textContent 写真实内容并返回可选 `{pause,resume,dispose}`。下级 push 使用新的层 ID；父层隐藏/暂停而不是销毁。方法为 push、pop、close、snapshot、dispose，snapshot 仅报告状态，不验证内容完整。

多层数据/电影仍由项目装配，父层返回时恢复焦点/滚动。onOpen/onClose 可暂停/恢复原页面的相应后台原因；不要清除其他暂停原因。组件捕获 renderer 抛错会显示“明细未能加载”，项目 QC 必须把这个错误视为未通过，不能因为弹窗打开就判成功。

## 连续电影

`new KZMotion.Film(root,options)` 要求 root 内已有 `.kz-film-stage` 与同一 `.kz-film-carrier`，并提供 options.frames、duration。帧结构为 `{t,x,y,w,h,r,tint:[r,g,b,a],label,caption}`，首尾回接按 06。可选 managedText:false 由项目业务时钟写文本；onRender(frame,progress,film) 的 frame.index 来自同一几何采样，供同步业务状态。另有 staticProgress、minCarrierWidth 参数；数值从实际计划/token 取，不在此页复制设计默认值。

舞台尺寸来自真实 `.kz-film-stage` 的clientWidth/clientHeight。当前共享CSS同时设 `height:440px; min-height:320px`；嵌入较矮的PPT正文卡时，项目只覆盖height不会取消min-height，实际舞台仍可能撑破卡片。项目须在自己的作用域一并设定合理height/min-height，并实测正文卡、标题、说明、图表、页脚的联合容量；不能裁字或缩字遮溢出。内层叙事载体置于玻璃阅读卡时保持同族，但不得再叠加第二层backdrop采样；02负责材质硬门。

离页若项目调用 `film.pause('engine-inactive')`，复入必须调用 `film.resume('engine-inactive')`；IO或resume其他原因不会清除它。保留其他hidden/modal/RM原因，并实际测离开后返回，不用初次自动播放推定复入正确。

Film 自动开始，返回 pause(reason)、resume(reason)、seek(progress)、snapshot()、dispose()；没有 play/reset/static_summary 方法。pause/resume 按原因集合管理；seek 仅后台 QC/捕获，不呈现播放器。Film 已管理 RM/可见性/打印/自身 resize；项目自己的 observer/listener/timer 仍须释放。静态总览是项目内容合同，不是某个 Film 方法。能力边界与语义电影验收见 06 与 runtime/README。

## 计划和证据

`tools/qc_plan.py PLAN --manifest MANIFEST --asset-root ROOT --out REPORT` 是现有语义预检：不只 schema，还检查图像映射、真实 hash/像素、每视口裁切、品牌字号、卡片动效清单等。它输出 pending/review/warning；不是视觉、动态或指定引擎放行证书。项目页数/源事实清单与实际 DOM 仍须逐项对账。没有 plan init、plan validate --stage 这类 CLI，不要猜测调用。
