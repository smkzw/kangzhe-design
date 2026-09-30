# 测试入口

`test_contracts.py`、`test_hero.py` 与 `test_a04_gates.py` 覆盖字号、固定版式、引用、图像及计划绕过等确定性合同；以实际测试输出计数，不以文档数字作为证据。`browser_smoke.py` 使用真实Chromium、真实ECharts和真实pointer/keyboard事件，不用mock；采用本地依赖内联harness，以便受管理策略限制的环境复现。`film_cycle.py`约40秒观察正常36秒时钟，不是独立视觉审片。

先用宿主已有环境。缺依赖时按该环境安全安装 `jsonschema Pillow playwright`；Chromium路径通过 `--chromium` 指定，不猜每个平台路径。运行命令见根README。

模型/harness评价不是这些单元测试的替代，反之亦然。本测试集目前不执行图像生成、ppt-master、html-ppt-skill或Office，后续增加专门E2E测试时须继续明确环境与真调用。

R10：test_context_routing.py核最终owner不丢、旧入口兼容与hash变更重读。bridge_failure_browser.py使用真实Chrome验证初始化回滚、失败入场重试与销毁异常；bridge_regression.py保留正常DOM边界。tilt_pointer_browser.py接受实际观众URL，真实鼠标进入后驻留并检查±10°和光源、离开复位，不用dispatchEvent瞬时结果放行。它们均不是指定引擎/模型或四轨验收。

R10最终组件检查：桥四项异常路径及五项正常生命周期在真实Chrome通过；51合同通过。新增真实pointer驻留门不代表失败作者实物已修好。流式owner最新R9 runtime六场景×两档12个自然完整周期，1948样本、0可见文字越界、同carrier与双层返回焦点通过，仍非指定模型制作终态或最终四轨轮。
