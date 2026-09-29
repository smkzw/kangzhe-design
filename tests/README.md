# 测试入口

`test_contracts.py` 是18项确定性合同测试。`browser_smoke.py` 使用真实Chromium、真实ECharts和真实pointer/keyboard事件，不用mock；采用本地依赖内联harness，以便受管理策略限制的环境复现。`film_cycle.py`约40秒观察正常36秒时钟，不是独立视觉审片。

先用宿主已有环境。缺依赖时按该环境安全安装 `jsonschema Pillow playwright`；Chromium路径通过 `--chromium` 指定，不猜每个平台路径。运行命令见根README。

模型/harness评价不是这些单元测试的替代，反之亦然。本测试集目前不执行图像生成、ppt-master、html-ppt-skill或Office，后续增加专门E2E测试时须继续明确环境与真调用。
