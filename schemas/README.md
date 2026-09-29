# 数据合同

这些 JSON 是康哲侧的 **sidecar**，不是 ppt-master 的 spec_lock、native chart metadata 或 html-ppt 的内部协议。适配时显式转换，不要求上游识别本 schema。

`page-plan` 采用项目声明的逻辑画布；PPT 通常 1280×720。`film-plan.states` 使用 0–1 归一化舞台坐标，因此其 protected_regions 也使用归一化坐标；不要把它交给按像素执行的页面 QC 而不换算。`gantt` 使用季度整数和半开区间。[min,max] 定义时间轴边界，任务为 [start,end)。

Schema 检查只证明结构，不证明图像生成真实发生、引用可靠、视觉美观或电影合格。资产 manifest 的工具回执与图片审阅证据需人工/独立审阅者核实；文件 hash 只能证明对应文件。
