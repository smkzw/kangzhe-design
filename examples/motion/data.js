/* Synthetic brief shared with the reference decks (研究资料完整性核对，合成示例). Each form gets the facts it shows;
   every number on stage is computed by runtime/kz-demo.js from these inputs (15 DEMO-04). */
(function () {
  const Q = (year, quarter) => year * 4 + quarter - 1; // KZGantt.qindex
  const groups = [{ name: '方案与修订', due: 2, received: 2 }, { name: '中心记录', due: 12, received: 9 }, { name: '实验室数据', due: 6, received: 6 }, { name: '安全性报告', due: 4, received: 3 }];
  window.KZ_MOTION_DATA = {
    units: { unit: '份', owner: '医学部', deadline: '2027Q1', note: '合成示例', groups },
    calc: { unit: '份', aLabel: '应收', bLabel: '已收', diffLabel: '缺口', note: '合成示例', rows: groups.map(g => ({ name: g.name, a: g.due, b: g.received })) },
    story: { unit: '份', aLabel: '应收', bLabel: '已收', gapLabel: '缺口', note: '合成示例', takeaway: '缺口集中在中心记录与安全性报告，共 4 份', groups: groups.map(g => ({ name: g.name, a: g.due, b: g.received })) },
    timeline: { note: '合成示例', min: Q(2026, 4), max: Q(2027, 3), milestone: { at: Q(2027, 1), label: '2027Q1：缺失资料补收与版本差异确认在本季度内完成' }, tasks: [
      { id: 'collect', label: '缺失资料补收', start: Q(2026, 4), end: Q(2027, 2), department: 'medical' },
      { id: 'confirm', label: '版本差异确认', start: Q(2027, 1), end: Q(2027, 2), department: 'medical' },
      { id: 'recheck', label: '完整性复核', start: Q(2027, 1), end: Q(2027, 3), department: 'statistics' },
      { id: 'safety', label: '安全性报告核对', start: Q(2027, 1), end: Q(2027, 3), department: 'pv' },
      { id: 'opinion', label: '审阅意见形成', start: Q(2027, 2), end: Q(2027, 3), department: 'medical' }] },
    decision: { note: '合成示例', intro: '每份资料都按同一条路径判定', summary: '缺失不按零处理；差异确认之前不做组间比较',
      nodes: [{ id: 'in', label: '资料登记', x: .01, y: .42, w: .14, kind: 'in' }, { id: 'got', label: '收到了吗？', x: .19, y: .42, w: .17 },
        { id: 'miss', label: '保留空值·补收', x: .45, y: .12, w: .26, kind: 'out' }, { id: 'conf', label: '差异已确认？', x: .45, y: .6, w: .2 },
        { id: 'cmp', label: '进入组间比较', x: .77, y: .38, w: .22, kind: 'out' }, { id: 'wait', label: '暂不比较', x: .77, y: .74, w: .22, kind: 'out' }],
      edges: [{ from: 'in', to: 'got' }, { from: 'got', to: 'miss', label: '未收到' }, { from: 'got', to: 'conf', label: '已收到' }, { from: 'conf', to: 'cmp', label: '已确认' }, { from: 'conf', to: 'wait', label: '未确认' }],
      cases: [{ id: 'a', label: '示例 A', detail: '已收，差异已确认', path: ['in', 'got', 'conf', 'cmp'] }, { id: 'b', label: '示例 B', detail: '中心记录缺失', path: ['in', 'got', 'miss'] }, { id: 'c', label: '示例 C', detail: '已收，差异待确认', path: ['in', 'got', 'conf', 'wait'] }] },
    compare: { note: '合成示例', left: '方案 V2.1', right: '方案 V2.3', leftTag: 'V2.1', rightTag: 'V2.3', tray: '转交确认',
      // rightOrder: where each row sits in the right version before alignment (its own section order)
      rows: [{ label: '研究对象', left: '成人 2 型糖尿病', right: '成人 2 型糖尿病' }, { label: '评价时间窗', left: '±3 天', right: '±3 天' },
        { label: '筛选窗口', left: '28 天', right: '42 天' }, { label: '终点评价时间点', left: '第 24 周', right: '第 26 周' }], rightOrder: [1, 0, 3, 2] },
  };
})();
