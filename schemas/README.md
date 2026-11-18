# schemas：数据合同

这些 JSON Schema 是康哲侧的 sidecar 合同，不是 ppt-master 的 spec_lock、原生图表元数据或 html-ppt 的内部协议；交给上游时显式转换。

| 文件 | 合同 |
|---|---|
| `page-plan.schema.json` | 逐页计划：页型、路线、视口、构图与字号、载体与模板、演示、动效对象、保护区、生图任务（`contract_revision` 为 `7.0`）；`tools/qc_plan.py` 预检 |
| `asset-manifest.schema.json` | 资产清单：每张图的来源、尺寸、哈希、用途与审阅 |
| `film-plan.schema.json` | 电影状态；`states` 用 0–1 归一化舞台坐标，保护区同样归一化，交给按像素执行的 QC 前要换算 |
| `program-plan.schema.json` | 甘特与临床开发计划（08 GANTT-02）：时间写季度、月份或日期；结构由本 schema 核对，语义（先后、重叠、粒度、可见泳道数）由 `program_model` / `KZClinical.program` 判定 |
| `gantt.schema.json` | 7.x 的季度甘特：季度整数、半开区间 [start,end)；编辑台第一次修改时转成 `program-plan` |

Schema 只证明结构，不证明图像真实生成、引用可靠或视觉合格；这些按 `design_specs/10-quality-gates.md` 的门逐项验收。
