# 用户要求逐项映射

| 编号 | 要求 | 归属 | 当前状态 |
|---|---|---|---|
| G1 | 全轨Liquid Glass | 02-liquid-glass / tokens | 规范+参考实现；PPT原生表现待上游验证 |
| G2 | 主动生图 | 04-image-pipeline | 规范/schema/QC；真实图片调用待验证 |
| G3 | 背景与文字固定元素不冲突 | 04 / 06 / qc_plan / mask | 生成前机械门已测；合成VLM待验证 |
| G4 | 统一ECharts语言和浅面积折线 | 05-charts / kz-charts | HTML基础图已测；PPT原生组合待验证 |
| G5 | 仅科学论文/权威指南类可见文献 | 03 / qc_plan | 分类规则及反例测试已测 |
| G6 | 绝对禁止通长彩色边缘装饰 | 02 / page-plan schema | 旧代码未携带；schema拒绝；所有渲染CSS/VLM仍要验 |
| P1 | 统一最小字号/同页同类间距 | 03 / tokens | 18项合同测试覆盖相关规则；目标Office待测 |
| P2 | PPTX玻璃一致与半透明 | 02 / adapter / glass_svg | 规范+原语；未声称导出已通过 |
| P3 | 强调句可选、大字居中且有意义 | 03 / page-plan | 规范；语义评审需实样 |
| P4 | title短章节名，无结论/冒号/破折号 | 03 / qc_plan | 机器部分已测；语义模型待测 |
| P5 | 正式原生中文 | 03 / 09 | 正反例与角色区分；模型评估待测 |
| P6 | 纵向有效利用 | 03 / 10 | 诊断与修复顺序，未用填充凑高度 |
| P7 | 与指定两个skill有机结合 | adapters | 源码核对+生命周期桥；E2E待测 |
| P8a | 卡片入出/hover光影/±10° | kz-motion / kz-glass | 参考实现；更多轨道实样待测 |
| P8b | 流程按语义顺序出现 | 06 / reveal | 底座实现；复杂关系电影待测 |
| P8c | 图表/甘特增长与数字联动 | kz-charts / kz-gantt | 组件进度和真值测试 |
| P8d | 首尾相接自动电影 | 06 / Film | 同载体/端点/普通36秒循环实测；叙事审片待测 |
| P8e | 双菱形/英雄卡浮动 | 06 / float CSS | 参数与参考CSS；正式chrome接入待测 |
| P8f | 适宜的Dribbble动效 | 06 / RESEARCH | 候选采纳/禁用边界；非全量案例验证 |
| P9 | 可拖可伸可表单编辑的甘特 | 08 / kz-gantt | 真实指针/缩放/表单/撤销等已测；上游待测 |
| P10 | 多层级丰富下钻 | 07 / kz-drilldown | 宽L1/L2、图表+表格+子电影已测 |
| P11 | 批判地借鉴PPTX和讲稿 | 09 / RECONSTRUCTION_REVIEW | 已审阅19页/备注/结构；未校验临床事实 |
| W1 | 用满宽屏但不拉长阅读行 | tracks-site / tracks-stream / 06 | 参考页4宽度无水平溢出；生产布局待测 |
| W2 | 每页/一级章节首屏电影 | 06 / tracks-site / tracks-stream | 详细合同；真正完整多页样板由P3完成 |
| W3 | 宽弹层及嵌套复杂下钻 | 07 / Drilldown | 82vw×88vh、状态生命周期参考已测 |
| N1 | 修改前完整结构审阅 | review / input_inventory | 归档全清单、文档代码冲突、19页PPT和11页站点预览 |
| N2 | 整体重构非补丁 | 00 / new directory | 新目录构建；未复制旧CSS/旧规范 |
| N3 | 单一6.0与Agent循环包 | README / agent | 单包与独立执行包；真实多模型运行待Agent |

“已写规范”与“已测”不同；任何未覆盖平台不能据此标为通过。详细实际证据看LOCAL_VALIDATION.json。
