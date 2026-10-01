# Agent 执行入口 · KZ6-0929

**当前R23策略：**用户要求快速收尾，不再派发新测试；先读CURRENT_HANDOFF.md、KNOWN_GAPS.md首表与review/CURRENT_STATUS.md。以下长期验证目标不触发当前自动续跑。

目标：在单一 `kangzhe-design` 6.0 上完成真实制作集成与异质模型验证，不再叠加旧包。不把本次已有参考组件重写一遍；先复测、定位差距，再最小范围完善。

## 先读

1. 根目录 `SKILL.md`、`README.md`、`review/RECONSTRUCTION_REVIEW.md` 和 `review/VALIDATION_STATUS.md`。
2. `PLAN.md`、`EVALUATION.md`、`HANDOFF_TEMPLATE.md`；实际制作时按轨道读取 design_specs，不把所有文档塞进每次模型上下文。
3. `KNOWN_GAPS.md`；不要把“有规范/有代码/机械测试通过”称为“生产验收通过”。

执行编号 `KZ6-0929-A01` 起，后续递增。新功能写入本包 owner 文件，删除被替代规则。不要建立 6.0补丁、6.0加强、6.0-3D 多个同名入口。

本包所附初测不是其他模型的能力评测。你必须实际探测可用 LLM/VLM/生图服务，记录模型准确标识、版本、harness、工具权限、预算、输入 hash、输出 hash、时间、失败与可回看的截图/录屏。没有凭据则标记 BLOCKED，不用伪模型或预制文件顶替生成测试。
