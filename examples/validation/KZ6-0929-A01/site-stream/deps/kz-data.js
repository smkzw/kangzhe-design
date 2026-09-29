/* KZ6-0929-A01 P3 — canonical synthetic data object.
   Single source for chart + relations + all page text. Derived only from D03 of the
   read-only fixture. Nothing here is real clinical data. */
(function (global) {
  'use strict';

  var SYNTHETIC_NOTE = '合成演示数据，不表示任何临床结果。';

  var DATA = {
    classification: 'synthetic_fixture_only',
    synthetic_note: SYNTHETIC_NOTE,
    doc_title: '证据组织',
    footer: '产品中心-医学部｜2026年9月',

    chart: {
      chart_id: 'chart.archive.count',
      name: '资料归档',
      kind: 'column',
      description: '资料归档数量的合成示例，按四个阶段分组，第二阶段缺失。单位：份。',
      categories: ['第一阶段', '第二阶段', '第三阶段', '第四阶段'],
      series: [{ id: 'archive-count', name: '资料归档', values: [2, null, 5, 7] }],
      unit: '份',
      decimals: 0,
      null_category: '第二阶段',
      null_meaning: '资料缺失，不等于零，不插补',
      method: '按资料形成时间逐项核对；缺失记为 null，禁止按其他阶段推算。',
      limitations: [
        '数量仅为合成示例，不表示任何临床结果。',
        '阶段二资料缺失，不能按零或相邻值解读。',
        '本图不用于比较治疗效果。'
      ]
    },

    /* Four relation segments, identical across the four first screens in wording,
       each film states which predicates it activates. */
    relations: [
      {
        id: 'r0', predicate: '限定', label: '界定范围',
        relation: '研究问题限定资料范围',
        detail: '先明确需要解决的问题与纳入资料的边界。'
      },
      {
        id: 'r1', predicate: '对应', label: '整理证据',
        relation: '资料分组对应问题',
        detail: '将资料按主题与形成时间组织，保留缺失信息。'
      },
      {
        id: 'r2', predicate: '连接', label: '审阅差异',
        relation: '组间差异连接待确认事项',
        detail: '比较各组资料并识别仍需补足的限制。'
      },
      {
        id: 'r3', predicate: '回收', label: '回到问题',
        relation: '审阅结果回到初始范围',
        detail: '回到原有问题，确认现有资料是否足以支持理解。'
      }
    ],

    home_cards: [
      { title: '研究范围', body: '本示例用于核对视觉规范与资料呈现方式。' },
      { title: '资料核对', body: '按既定阶段整理记录，保留缺失状态。确认资料的形成时间、内容范围与对应阶段；无法确定的信息不作推断。' },
      { title: '审阅安排', body: '先核对完整性，再检查各阶段记录的一致性。问题登记应区分资料缺失、内容不一致与待确认事项；必要限定直接写在主页面。完成复核后保留原始记录，确保后续调整可以追溯。' }
    ],

    stream_paragraphs: [
      { heading: '范围', body: '本示例用于核对视觉规范与资料呈现方式。页面先给出需要解决的问题与纳入资料的边界，再展开具体记录；边界之外的材料不进入本次核对。' },
      { heading: '分组', body: '资料按主题与形成时间组织为四个阶段。形成时间无法确定的记录单独标注，不并入任何阶段，也不按相邻阶段推算。分组结果保留缺失状态，缺失本身是需要登记的信息。' },
      { heading: '核对', body: '按资料形成时间逐项核对；缺失记为 null，禁止按其他阶段推算。逐项核对完成后，再检查各阶段记录的一致性：同一资料在不同阶段出现时，以形成时间更早的记录为准，并在问题登记中说明差异。' },
      { heading: '限制', body: '数量仅为合成示例，不表示任何临床结果。阶段二资料缺失，不能按零或相邻值解读。本图不用于比较治疗效果。上述限定写在主页面，不折叠进交互层。' },
      { heading: '记录', body: '问题登记区分资料缺失、内容不一致与待确认事项。完成复核后保留原始记录，后续调整可以追溯到具体条目与形成时间。' }
    ],

    /* L2 process steps for the independent drilldown film. */
    process_steps: [
      { predicate: '顺序', label: '逐项核对', detail: '以形成时间顺序逐项核对，不跳项、不合并。' },
      { predicate: '缺席', label: '记录缺失', detail: '阶段二缺失记为 null，禁止按其他阶段推算，也不按零读取。' },
      { predicate: '登记', label: '组间比较', detail: '比较各组资料并识别仍需补足的限制，登记为待确认事项。' },
      { predicate: '回收', label: '回到范围', detail: '回到原有问题，确认现有资料是否足以支持理解。' }
    ]
  };

  /* Derived view of the same canonical object — never a second hand-typed copy. */
  DATA.chartOptionData = function () {
    return {
      kind: 'column',
      categories: DATA.chart.categories.slice(),
      series: DATA.chart.series.map(function (s) {
        return { id: s.id, name: s.name, values: s.values.slice() };
      }),
      unit: DATA.chart.unit,
      decimals: DATA.chart.decimals,
      description: DATA.chart.description
    };
  };

  /* Plain-text value formatting shared by table + chart labels. */
  DATA.formatValue = function (v) {
    return v === null ? '未提供' : Number(v).toLocaleString('zh-CN');
  };

  global.KZ_DATA = DATA;
})(window);
