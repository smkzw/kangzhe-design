/* KZ6-0929-A01 · P1B · 唯一语义数据源
 * 与 ../source-ledger.json 的 chart_series_main / gantt.json 一一对应。
 * 不在此处派生第二份数：图表与甘特都从本对象构造。
 * 全部为合成演示值，非真实研究结果。
 */
window.KZ_DECK_DATA = {
  schema: 'kz-deck-data-1',
  chart: {
    id: 'chart_series_main',
    kind: 'line',
    description: '示例计数随访视时间点的变化；第 2 个时间点缺失，保留缺口。单位为例，数值为合成演示值。',
    categories: ['T1', 'T2', 'T3', 'T4'],
    unit: '例（合成）',
    decimals: 0,
    area: true,
    series: [
      { id: 'series_example_count', name: '示例计数', values: [2, null, 5, 7] }
    ],
    meta: {
      missingIndex: 1,
      missingPolicy: 'preserve_gap',
      estimand: null,
      analysisPopulation: '合成演示人群（不对应任何真实分析集）',
      limitations: '数值为演示占位值，不支持任何趋势或疗效解读。'
    }
  },
  gantt: {
    min: 8104,
    max: 8116,
    /* 任务条统一使用品牌橙，不按行号轮转部门色。
       01-core.md:5 规定部门色「仅表达已知部门身份」；本例六条任务没有部门归属，
       若沿用组件默认的 departments 轮转调色板，会暗示不存在的部门归属。
       color 属表现层绑定，故只写在此处；gantt.json 仍是无颜色字段的纯时间模型。 */
    taskColor: '#FF9900',
    tasks: [
      { id: 't1_protocol', label: '方案定稿与伦理递交', start: 8104, end: 8105 },
      { id: 't2_site', label: '中心筛选与启动', start: 8105, end: 8106 },
      { id: 't3_enroll', label: '受试者入组', start: 8106, end: 8108 },
      { id: 't4_followup', label: '随访与数据采集', start: 8107, end: 8111 },
      { id: 't5_lock', label: '数据清理与锁库', start: 8111, end: 8112 },
      { id: 't6_report', label: '统计分析与总结报告', start: 8112, end: 8116 }
    ],
    meta: {
      quarterIndexFormula: 'index = year * 4 + quarter - 1',
      interval: 'half_open_[start,end)',
      axisLabel: '2026Q1–2028Q4',
      nature: 'synthetic_placeholder_schedule'
    }
  }
};
