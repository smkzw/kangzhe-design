/* Kangzhe 7.1 — ten more demonstrative forms (15 DEMO-02) built on KZDemo.kit. Each turns the page's own data into
   a schematic: icons, lanes, dots, bars and SVG links carry the content, text labels it (15 DEMO-08). Every number
   and every caption is computed from the data passed in (15 DEMO-04); a form throws when the data contradict
   themselves (for example arm totals that do not add up to the randomised count).
     flow       process with a positive case, a simple negative (rework) and a complex negative (repeated failure → escalation)
     gantt      Gantt advance: dependencies, today line, a slip and its cascade, the critical path, a recovery
     swimlane   hand-offs across departments with elapsed time against the limit
     consort    subject flow: screened → excluded → randomised → lost → analysed (one dot = `per` subjects)
     curve      line chart read scene by scene: series, threshold, window difference, events
     breakdown  whole → parts → one part's children, with shares of the whole
     audit      a document checked field by field; failures copied to a findings list with their rule
     matrix     risk matrix: items placed, high zone counted, mitigations move them
     network    data flow between parties; one packet blocked on a broken link
     schedule   visit windows: subjects' actual visits against target day ± window
   Requires kz-scenes.js, kz-demo.js and kz-icons.js. Styles: kz-glass.css "Demo stages". */
(function (global) {
  'use strict';
  const K = () => global.KZDemo.kit, def = (kind, fn) => global.KZDemo.define(kind, fn);
  const asp = cv => (cv.clientWidth && cv.clientHeight ? cv.clientWidth / cv.clientHeight : 1.9);
  const pct = (a, b) => (b ? Math.round(a / b * 100) : 0);
  const need = (ok, msg) => { if (!ok) throw Error(msg); };
  const chunk = (list, parts) => { const size = Math.max(1, Math.ceil(list.length / parts)), out = []; for (let i = 0; i < list.length; i += size) out.push(list.slice(i, i + size)); return out; };
  // a square object (icon, dot) centred on (cx, cy): its height in canvas fractions follows the canvas aspect
  const sq = (cx, cy, w, A) => ({ x: cx - w / 2, y: cy - w * A / 2, w });
  const mount = (root, scenes, opt, staticScene, facts) => { const s = K().S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? staticScene }); s.facts = facts; return s; };

  /* ---------- flow ----------
     data: { stations: [{id, label, icon, rule}], cases: [{id, label, detail, steps: [{at, result:'pass'|'fail', back?}]}],
             bins: {accept, rework, escalate}, intro, summary } — a fail with `back` sends the case through rework to
             that station; a fail without it escalates. A case ending with a pass at the last station is accepted. */
  def('flow', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'flow', d.note), A = asp(cv), st = d.stations, n = st.length, at = id => st.findIndex(s => s.id === id);
    need(n >= 2 && d.cases?.length, 'flow 需要至少两个环节和一个示例');
    const bins = { accept: '通过', rework: '返工', escalate: '升级处理', ...d.bins };
    const sp = .62 / (n - 1), sx = i => .1 + i * sp, gx = i => sx(i) + sp / 2, sy = .3, iw = .066, ih = iw * A, ty = sy - ih / 2 - .09, lane = .7, cw = .14, bx = .8, lw = Math.min(.15, sp - .01);
    const L = k.links(cv);
    L.path('rail', k.pts([[sx(0), sy], [bx - .01, sy]]), 'is-rail');
    L.path('lane', k.pts([[sx(0), lane], [sx(n - 1), lane]]), 'is-lane');
    st.forEach((s, i) => { k.icon(cv, 'st' + i, s.icon || 'doc'); k.obj(cv, 'sl' + i, 'kz-demo-label', s.label); k.obj(cv, 'sb' + i, 'kz-demo-badge'); if (s.rule) k.obj(cv, 'sr' + i, 'kz-demo-note', s.rule); });
    k.obj(cv, 'bA', 'kz-demo-bin is-ok', bins.accept); k.obj(cv, 'bE', 'kz-demo-bin is-risk', bins.escalate);
    k.obj(cv, 'cA', 'kz-demo-count'); k.obj(cv, 'cE', 'kz-demo-count is-risk'); k.obj(cv, 'lr', 'kz-demo-note is-risk'); k.icon(cv, 'li', 'rework', 'is-risk');
    const base = { rail: { stroke: k.MUTE }, lane: { stroke: 'rgba(192,0,0,.35)' }, bA: { x: bx, y: .12, w: .19, h: .32 }, bE: { x: bx, y: .56, w: .19, h: .32 },
      cA: { x: bx, y: .19, w: .19, count: 0, unit: ' 例' }, cE: { x: bx, y: .63, w: .19, count: 0, unit: ' 例' }, li: sq(sx(0) - .035, lane, .03, A), lr: { x: sx(0) - .015, y: lane + .03, w: .3, text: `${bins.rework} 0 次` } };
    st.forEach((s, i) => Object.assign(base, { ['st' + i]: sq(sx(i), sy, iw, A), ['sl' + i]: { x: sx(i) - lw / 2, y: sy + ih / 2 + .015, w: lw },
      ['sb' + i]: { x: sx(i) + iw / 2 - .012, y: sy - ih / 2 - .035, w: .03, count: 0, opacity: 0 }, ...(s.rule ? { ['sr' + i]: { x: sx(i) - lw / 2, y: sy + ih / 2 + .075, w: lw } } : {}) }));
    const scenes = [{ id: 'rules', caption: d.intro || `${n} 个环节逐一核对，不合格的返工或升级`, set: base }];
    const fails = st.map(() => 0); let accepted = 0, escalated = 0, reworks = 0;
    // where each case ends, known up front, so a bin spaces its chips by how many it will hold
    const ends = d.cases.map(c => { const last = c.steps[c.steps.length - 1]; return last.result === 'pass' && at(last.at) === n - 1 ? 'accept' : 'escalate'; });
    const gap = kind => Math.min(.085, .17 / Math.max(1, ends.filter(e => e === kind).length - 1));
    d.cases.forEach((c, ci) => {
      k.obj(cv, 'c' + ci, 'kz-demo-case', c.label);
      const tr = L.path('t' + ci, 'M0 0', 'is-trace');
      // rework runs down the gap after the failing station and back up the gap before the station it returns to,
      // so no trace crosses a station's label
      const pts = [[sx(0) - .05, ty]]; let end = null, rw = 0;
      c.steps.forEach((s, j) => {
        const i = at(s.at); need(i >= 0, `flow 示例 ${c.label} 的环节 ${s.at} 不存在`);
        pts.push([sx(i), ty]);
        if (s.result === 'fail') { fails[i]++; if (s.back) { const b = at(s.back); need(b >= 0, `flow 示例 ${c.label} 的退回环节 ${s.back} 不存在`); rw++; const up = b ? gx(b - 1) : sx(0) - .05; pts.push([gx(i), ty], [gx(i), lane - .04], [up, lane - .04], [up, ty]); } else end = 'escalate'; }
        else if (j === c.steps.length - 1) end = i === n - 1 ? 'accept' : 'escalate';
      });
      reworks += rw; end === 'accept' ? accepted++ : escalated++;
      const slot = end === 'accept' ? accepted - 1 : escalated - 1, box = end === 'accept' ? [bx, .12] : [bx, .56];
      const park = [box[0] + (.19 - cw) / 2, box[1] + .14 + slot * gap(end)];
      // enter the bin from its left side, below its title and count
      pts.push([bx - .012, ty], [bx - .012, park[1]], [park[0] + cw / 2, park[1]]);
      tr.setAttribute('d', k.pts(pts));
      const set = { ['c' + ci]: { from: { x: pts[0][0] - cw / 2, y: pts[0][1], w: cw, opacity: 0 }, x: park[0], y: park[1], w: cw, via: pts.slice(1, -1).map(([x, y]) => [x - cw / 2, y]) },
        ['t' + ci]: { opacity: 1, stroke: end === 'accept' ? k.C('brand') : k.C('risk') }, cA: { count: accepted }, cE: { count: escalated }, lr: { text: `${bins.rework} ${reworks} 次` } };
      d.cases.forEach((_, p) => { if (p < ci) set['t' + p] = { opacity: .16 }; });
      st.forEach((_, i) => { const hit = c.steps.some(s => s.at === st[i].id && s.result === 'fail'); set['st' + i] = { cls: { 'is-fail': hit, 'is-hot': fails[i] > 0 && !hit } }; if (fails[i]) set['sb' + i] = { count: fails[i], opacity: 1 }; });
      const word = end === 'accept' ? bins.accept : bins.escalate;
      scenes.push({ id: c.id, caption: `${c.label}：${c.detail} → ${word}${rw ? `（返工 ${rw} 次）` : ''}`, order: ['c' + ci], set });
    });
    // the station with most failures is named only when one station has strictly the most
    const top = Math.max(...fails), worst = top > 0 && fails.filter(f => f === top).length === 1 ? fails.indexOf(top) : -1;
    scenes.push({ id: 'summary', caption: d.summary || `${bins.accept} ${accepted} 例、返工 ${reworks} 次、${bins.escalate} ${escalated} 例${worst >= 0 ? `；问题集中在「${st[worst].label}」` : ''}`,
      set: Object.fromEntries([...d.cases.map((_, p) => ['t' + p, { opacity: .5 }]), ...st.map((_, i) => ['st' + i, { cls: { 'is-fail': false, 'is-hot': fails[i] > 0 } }])]) });
    return mount(root, scenes, opt, scenes.length - 1, [{ value: String(accepted), label: bins.accept }, { value: String(reworks), label: `${bins.rework}次数` }, { value: String(escalated), label: bins.escalate, risk: escalated > 0 }, ...(worst >= 0 ? [{ value: st[worst].label, label: '问题最多的环节' }] : [])]);
  });

  /* ---------- gantt ----------
     data: { labels: ['1月', …] (periods), unit: '个月', tasks: [{id, label, start, end, department, deps: [ids]}] ([start,end) in periods),
             milestone: {label, after: [ids]}, today, slip: {task, by, reason}, recover?: {task, by, action} } */
  def('gantt', (root, d, opt) => {
    const k = K(), L = k.S().layout, cv = k.frame(root, 'gantt', d.note), T = d.tasks, N = d.labels.length, unit = d.unit || '期';
    const X = L.scale([0, N], [.2, .96]), rows = L.rows(T.length, { box: [0, .14, 1, .62], gap: .36 }), byId = Object.fromEntries(T.map(t => [t.id, t]));
    // forward pass: a task starts when its plan says and after all its dependencies end
    const plan = (adj = {}) => { const s = {}; let changed = true, guard = 0;
      while (changed && guard++ < 50) { changed = false; for (const t of T) { const dur = t.end - t.start + (adj[t.id] || 0), st0 = Math.max(t.start, ...(t.deps || []).map(id => s[id]?.end ?? -Infinity)), v = { start: st0, end: st0 + dur };
        if (!s[t.id] || s[t.id].start !== v.start || s[t.id].end !== v.end) { s[t.id] = v; changed = true; } } }
      return s; };
    const msEnd = s => Math.max(...d.milestone.after.map(id => s[id].end));
    const critical = s => { const out = []; let cur = d.milestone.after.reduce((a, b) => (s[b].end > s[a].end ? b : a));
      while (cur) { out.unshift(cur); cur = (byId[cur].deps || []).find(id => s[id].end === s[cur].start) || null; } return out; };
    const adj2 = { [d.slip.task]: d.slip.by }; if (d.recover) adj2[d.recover.task] = (adj2[d.recover.task] || 0) - d.recover.by;
    const S0 = plan(), S1 = plan({ [d.slip.task]: d.slip.by }), S2 = d.recover ? plan(adj2) : null;
    const m0 = msEnd(S0), m1 = msEnd(S1), m2 = S2 && msEnd(S2), lab = e => d.labels[e - 1];
    need(Math.max(m0, m1, m2 || 0) <= N, `gantt：labels 只有 ${N} 期，延误后的${d.milestone.label}落在第 ${Math.max(m0, m1, m2 || 0)} 期，需加长时间轴`);
    d.labels.forEach((t, j) => k.obj(cv, 'ax' + j, 'kz-demo-tick', t));
    T.forEach((t, i) => { k.obj(cv, 'gl' + i, 'kz-demo-label is-left', t.label); k.obj(cv, 'gb' + i, 'kz-demo-bar is-ghost'); k.obj(cv, 'gt' + i, 'kz-demo-bar is-' + (t.department || 'medical')); k.obj(cv, 'gp' + i, 'kz-demo-bar is-done'); });
    const deps = T.flatMap((t, i) => (t.deps || []).map(id => [T.findIndex(x => x.id === id), i]));
    deps.forEach((_, j) => { k.obj(cv, 'dv' + j, 'kz-demo-dep'); k.obj(cv, 'dh' + j, 'kz-demo-dep'); });
    k.obj(cv, 'td', 'kz-demo-playhead'); k.obj(cv, 'tdl', 'kz-demo-note is-risk is-start'); k.icon(cv, 'ms', 'flag', 'is-on'); k.obj(cv, 'msl', 'kz-demo-label'); k.obj(cv, 'msd', 'kz-demo-count is-risk');
    const A = asp(cv), bar = (s, i) => ({ x: X(s.start), y: rows[i].y, w: X(s.end) - X(s.start), h: rows[i].h });
    const conn = (s, [a, b]) => { const x = X(s[T[a].id].end), y1 = rows[a].y + rows[a].h / 2, y2 = rows[b].y + rows[b].h / 2;
      return [{ x: x - .0015, y: Math.min(y1, y2), w: .003, h: Math.abs(y2 - y1) }, { x, y: y2 - .003, w: Math.max(.003, X(s[T[b].id].start) - x), h: .006 }]; };
    const geo = s => { const o = {}; T.forEach((t, i) => { o['gt' + i] = bar(s[t.id], i); }); deps.forEach((p, j) => { const [v, h] = conn(s, p); o['dv' + j] = v; o['dh' + j] = h; }); return o; };
    const msAt = e => ({ ms: sq(X(e), .85, .028, A), msl: { x: Math.min(.78, X(e) - .1), y: .9, w: .2, text: `${d.milestone.label}：${lab(e)}` } });
    const base = { ...geo(S0), ...msAt(m0), td: { x: X(d.today), y: .1, w: .004, h: .7, opacity: 0 }, tdl: { x: X(d.today) + .008, y: .76, w: .2, text: d.todayLabel || '当前', opacity: 0 }, msd: { x: X(m0) + .02, y: .82, w: .14, text: '', opacity: 0 } };
    d.labels.forEach((t, j) => { base['ax' + j] = { x: X(j), y: .05, w: X(j + 1) - X(j) }; });
    T.forEach((t, i) => Object.assign(base, { ['gl' + i]: { x: .01, y: rows[i].y, w: .18 }, ['gb' + i]: bar(S0[t.id], i), ['gp' + i]: { ...bar(S0[t.id], i), w: 0, opacity: 0 } }));
    const done = T.filter(t => S0[t.id].end <= d.today), going = T.filter(t => S0[t.id].start < d.today && S0[t.id].end > d.today);
    const moved = T.filter(t => S1[t.id].start !== S0[t.id].start || S1[t.id].end !== S0[t.id].end), slipT = byId[d.slip.task];
    const crit = critical(S1), crit2 = S2 && critical(S2);
    const scenes = [
      { id: 'plan', caption: `计划 ${T.length} 项任务，「${d.milestone.label}」在 ${lab(m0)}`, set: base },
      { id: 'today', caption: `进行到 ${d.labels[Math.min(N - 1, d.today)]}：已完成 ${done.length} 项，进行中 ${going.length} 项`, order: ['td', 'tdl', ...T.map((_, i) => 'gp' + i)],
        set: { td: { opacity: 1 }, tdl: { opacity: 1 }, ...Object.fromEntries(T.map((t, i) => { const s = S0[t.id], e = Math.min(s.end, d.today); return ['gp' + i, e > s.start ? { w: X(e) - X(s.start), opacity: 1 } : {}]; })) } },
      { id: 'slip', caption: `${slipT.label}延误 ${d.slip.by} ${unit}（${d.slip.reason}）→ ${moved.length - 1} 项后续顺延，${d.milestone.label}推迟 ${m1 - m0} ${unit}`, order: moved.map(t => 'gt' + T.indexOf(t)),
        set: { ...geo(S1), ...msAt(m1), msd: { x: X(m1) > .8 ? X(m1) - .18 : X(m1) + .02, opacity: 1, text: `+${m1 - m0} ${unit}` }, ...Object.fromEntries(moved.map(t => ['gt' + T.indexOf(t), { ...bar(S1[t.id], T.indexOf(t)), cls: { 'is-slip': t.id === d.slip.task, 'is-moved': t.id !== d.slip.task } }])) } },
      { id: 'critical', caption: `关键路径：${crit.map(id => byId[id].label).join(' → ')}；其中任何一项再延误，都会推迟${d.milestone.label}`,
        set: Object.fromEntries(T.flatMap((t, i) => crit.includes(t.id) ? [['gt' + i, { cls: { 'is-crit': true } }], ['gl' + i, { cls: { 'is-on': true } }]] : [['gt' + i, { opacity: .35 }], ['gb' + i, { opacity: .35 }]])) },
    ];
    if (S2) {
      const rt = byId[d.recover.task], off = m2 - m0;
      scenes.push({ id: 'recover', caption: `${rt.label}压缩 ${d.recover.by} ${unit}（${d.recover.action}）→ ${d.milestone.label}${off > 0 ? `仍推迟 ${off} ${unit}` : '回到原计划'}`,
        set: { ...geo(S2), ...msAt(m2), msd: { x: X(m2) > .8 ? X(m2) - .18 : X(m2) + .02, text: off > 0 ? `+${off} ${unit}` : '按计划', cls: { 'is-risk': off > 0 } },
          ...Object.fromEntries(T.flatMap((t, i) => [['gt' + i, { ...bar(S2[t.id], i), opacity: 1, cls: { 'is-crit': crit2.includes(t.id), 'is-recover': t.id === d.recover.task } }], ['gb' + i, { opacity: 1 }], ['gl' + i, { cls: { 'is-on': crit2.includes(t.id) } }]])) } });
    }
    return mount(root, scenes, opt, scenes.length - 1, [{ value: `+${m1 - m0}`, label: `${d.milestone.label}推迟（${unit}）`, risk: m1 > m0 }, { value: String(moved.length), label: '受影响任务' }, { value: String(crit.length), label: '关键路径任务' }, ...(S2 ? [{ value: m2 - m0 > 0 ? `+${m2 - m0}` : '0', label: `追赶后推迟（${unit}）`, risk: m2 > m0 }] : [])]);
  });

  /* ---------- swimlane ----------
     data: { lanes: [{id, label, icon, department}], steps: [{lane, label, days, sla}], unit, limit, caseLabel, chunks? } */
  def('swimlane', (root, d, opt) => {
    const k = K(), L = k.S().layout, cv = k.frame(root, 'swimlane', d.note), A = asp(cv), ln = d.lanes, sp = d.steps, unit = d.unit || '天';
    const rows = L.rows(ln.length, { box: [0, .03, 1, .86], gap: .1 }), li = id => ln.findIndex(l => l.id === id);
    const sx = i => .27 + i * (.66 / Math.max(1, sp.length - 1)), cy = s => rows[li(s.lane)].y + rows[li(s.lane)].h / 2, nw = .118;
    const Lk = k.links(cv);
    ln.forEach((l, j) => { k.obj(cv, 'lb' + j, 'kz-demo-lane'); k.icon(cv, 'lc' + j, l.icon || 'people'); k.obj(cv, 'll' + j, 'kz-demo-label is-left', l.label); k.obj(cv, 'ld' + j, 'kz-demo-dot is-' + (l.department || 'medical')); });
    sp.forEach((s, i) => { k.obj(cv, 'sn' + i, 'kz-demo-node is-small', s.label); k.obj(cv, 'sd' + i, 'kz-demo-note', `${s.days} ${unit}`);
      if (i) Lk.path('sc' + i, k.pts([[sx(i - 1) + nw / 2, cy(sp[i - 1])], [(sx(i - 1) + sx(i)) / 2, cy(sp[i - 1])], [(sx(i - 1) + sx(i)) / 2, cy(s)], [sx(i) - nw / 2, cy(s)]])); });
    k.obj(cv, 'tk', 'kz-demo-case', d.caseLabel || '示例'); k.icon(cv, 'ck', 'clock'); k.obj(cv, 'cv', 'kz-demo-count');
    const base = { ck: sq(.81, .945, .028, A), cv: { x: .83, y: .92, w: .16, count: 0, unit: ` / ${d.limit} ${unit}` }, tk: { x: sx(0) - .07, y: cy(sp[0]) - .11, w: .14, opacity: 0 } };
    ln.forEach((l, j) => Object.assign(base, { ['lb' + j]: { x: .005, y: rows[j].y, w: .99, h: rows[j].h }, ['lc' + j]: sq(.03, rows[j].y + rows[j].h / 2, .026, A), ['ll' + j]: { x: .058, y: rows[j].y + rows[j].h / 2 - .03, w: .13 }, ['ld' + j]: sq(.049, rows[j].y + rows[j].h / 2, .008, A) }));
    sp.forEach((s, i) => Object.assign(base, { ['sn' + i]: { x: sx(i) - nw / 2, y: cy(s) - .035, w: nw, h: .07 }, ['sd' + i]: { x: sx(i) - nw / 2, y: cy(s) + .04, w: nw }, ...(i ? { ['sc' + i]: { stroke: k.MUTE } } : {}) }));
    const scenes = [{ id: 'lanes', caption: `${ln.length} 个部门、${sp.length} 个环节，时限 ${d.limit} ${unit}`, set: base }];
    const groups = d.chunks ? d.chunks.map(g => g.map(i => sp[i])) : chunk(sp, 3); let elapsed = 0, last = -1;
    groups.forEach((g, gi) => {
      const set = {}, overs = [];
      for (const s of g) { const i = sp.indexOf(s); elapsed += s.days; set['sn' + i] = { cls: { 'is-on': true, 'is-fail': s.sla != null && s.days > s.sla } }; if (i) set['sc' + i] = { stroke: k.C('brand') };
        if (s.sla != null && s.days > s.sla) { overs.push(s); set['sd' + i] = { text: `${s.days} ${unit}，超时 +${s.days - s.sla}`, cls: { 'is-risk': true } }; } last = i; }
      const end = sp[last]; set.tk = { x: sx(last) - .07, y: cy(end) - .11, opacity: 1, via: g.slice(0, -1).map(s => [sx(sp.indexOf(s)) - .07, cy(s) - .11]) }; set.cv = { count: elapsed, cls: { 'is-risk': elapsed > d.limit } };
      const lanes = [...new Set(g.map(s => ln[li(s.lane)].label))].join('、');
      scenes.push({ id: 'g' + gi, caption: `${lanes}：${g.map(s => s.label).join('、')}，累计 ${elapsed} ${unit}${overs.length ? `；${overs.map(s => `${s.label}超时 ${s.days - s.sla} ${unit}`).join('，')}` : ''}`, order: ['tk', ...g.map(s => 'sn' + sp.indexOf(s))], set });
    });
    const slow = sp.reduce((a, b) => (b.days > a.days ? b : a)), over = elapsed - d.limit;
    scenes.push({ id: 'summary', caption: `合计 ${elapsed} ${unit}，${over > 0 ? `超出时限 ${over} ${unit}` : '在时限内'}；最慢的是「${slow.label}」（${slow.days} ${unit}）`, set: { tk: { opacity: .35 }, ...Object.fromEntries(sp.map((s, i) => ['sn' + i, s === slow ? { cls: { 'is-crit': true } } : { opacity: .5 }])) } });
    return mount(root, scenes, opt, scenes.length - 1, [{ value: `${elapsed}`, label: `合计（${unit}）`, risk: over > 0 }, { value: `${d.limit}`, label: `时限（${unit}）` }, { value: slow.label, label: '最慢环节' }, { value: String(sp.filter(s => s.sla != null && s.days > s.sla).length), label: '超时环节', risk: sp.some(s => s.sla != null && s.days > s.sla) }]);
  });

  /* ---------- consort ----------
     data: { unit, per (subjects per dot), screened, excluded: [{reason, n}], arms: [{name, role:'treat'|'comparator', n, lost: [{reason, n}]}] } */
  def('consort', (root, d, opt) => {
    const k = K(), L = k.S().layout, per = d.per || 10, cv = k.frame(root, 'consort', d.note || `合成示例 · 每点 ${per} 例`), A = asp(cv), u = d.unit || '例';
    const E = k.sum(d.excluded.map(x => x.n)), R = d.screened - E, arms = d.arms.map(a => ({ ...a, lost: a.lost || [] }));
    arms.forEach(a => need(k.sum(a.lost.map(x => x.n)) <= a.n, `consort：${a.name}的脱落合计大于该组人数`));
    need(k.sum(arms.map(a => a.n)) === R, `consort：各组合计 ${k.sum(arms.map(a => a.n))} 与随机化人数 ${R} 不符`);
    const dots = n => Math.max(n > 0 ? 1 : 0, Math.round(n / per));
    // each dot belongs to one final group: an exclusion reason, an arm's loss reason, or an arm's analysed set
    const groups = [...d.excluded.map((x, j) => ({ kind: 'ex', j, n: x.n })), ...arms.flatMap((a, j) => [...a.lost.map((x, q) => ({ kind: 'lost', j, q, n: x.n })), { kind: 'an', j, n: a.n - k.sum(a.lost.map(x => x.n)) }])];
    const marks = groups.flatMap(g => Array.from({ length: dots(g.n) }, () => ({ ...g }))); marks.forEach((m, i) => k.obj(cv, 'm' + i, 'kz-demo-dot'));
    const pool = L.grid(marks.length, { box: [.22, .14, .46, .5], stageAspect: A });
    k.obj(cv, 'top', 'kz-demo-figure'); k.obj(cv, 'xb', 'kz-demo-bin is-muted', '排除'); d.excluded.forEach((x, j) => k.obj(cv, 'xr' + j, 'kz-demo-note', `${x.reason} ${x.n} ${u}`));
    const col = L.cols(arms.length, { box: [.02, .2, .7, .76], gap: .16 });
    arms.forEach((a, j) => { k.obj(cv, 'ah' + j, 'kz-demo-label is-strong'); k.obj(cv, 'al' + j, 'kz-demo-note is-risk'); k.obj(cv, 'an' + j, 'kz-demo-count'); });
    const exMarks = marks.filter(m => m.kind === 'ex'), exPos = L.grid(exMarks.length, { box: [.78, .21 + d.excluded.length * .09, .19, Math.max(.1, .47 - d.excluded.length * .09)], stageAspect: A, cols: 6 });
    const armPos = arms.map((a, j) => { const ms = marks.filter(m => m.kind !== 'ex' && m.j === j); return { ms, pos: L.grid(ms.length, { box: [col[j].x, col[j].y + .06, col[j].w, .34], stageAspect: A }) }; });
    const lostPos = arms.map((a, j) => { const ms = marks.filter(m => m.kind === 'lost' && m.j === j); return { ms, pos: L.grid(ms.length, { box: [col[j].x, .7, col[j].w * .6, .08], stageAspect: A, cols: 8 }) }; });
    const base = { top: { x: .2, y: .03, w: .5, text: `筛选 ${k.fmt(d.screened)} ${u}` }, xb: { x: .76, y: .12, w: .22, h: .56, opacity: 0 } };
    marks.forEach((m, i) => { base['m' + i] = { ...pool[i], fill: k.MUTE }; });
    d.excluded.forEach((x, j) => { base['xr' + j] = { x: .77, y: .21 + j * .09, w: .21, opacity: 0 }; });
    arms.forEach((a, j) => Object.assign(base, { ['ah' + j]: { x: col[j].x, y: col[j].y, w: col[j].w, opacity: 0, text: `${a.name} ${k.fmt(a.n)} ${u}` }, ['al' + j]: { x: col[j].x, y: .8, w: col[j].w, opacity: 0 }, ['an' + j]: { x: col[j].x, y: .62, w: col[j].w, opacity: 0, count: 0, unit: ` ${u}` } }));
    const fill = a => (a.role === 'comparator' ? '#6E7B8C' : k.C('brand'));
    const scenes = [
      { id: 'screen', caption: `筛选 ${k.fmt(d.screened)} ${u}，每个点代表 ${per} ${u}`, set: base },
      { id: 'exclude', caption: `排除 ${k.fmt(E)} ${u}：${d.excluded.map(x => `${x.reason} ${x.n}`).join('，')}`, order: exMarks.map(m => 'm' + marks.indexOf(m)),
        set: { xb: { opacity: 1 }, ...Object.fromEntries(d.excluded.map((_, j) => ['xr' + j, { opacity: 1 }])), ...Object.fromEntries(exMarks.map((m, q) => ['m' + marks.indexOf(m), { ...exPos[q], fill: '#C9CFD6' }])), top: { text: `筛选 ${k.fmt(d.screened)} → 随机化 ${k.fmt(R)} ${u}` } } },
      { id: 'randomise', caption: `随机化 ${k.fmt(R)} ${u}：${arms.map(a => `${a.name} ${a.n}`).join('，')}`, order: armPos.flatMap(p => p.ms.map(m => 'm' + marks.indexOf(m))),
        set: { ...Object.fromEntries(arms.flatMap((a, j) => [['ah' + j, { opacity: 1 }], ...armPos[j].ms.map((m, q) => ['m' + marks.indexOf(m), { ...armPos[j].pos[q], fill: fill(a) }])])) } },
      { id: 'lost', caption: `脱落：${arms.map(a => `${a.name} ${k.sum(a.lost.map(x => x.n))} ${u}`).join('，')}；原因列在各组下方`, order: lostPos.flatMap(p => p.ms.map(m => 'm' + marks.indexOf(m))),
        set: { ...Object.fromEntries(arms.flatMap((a, j) => [['al' + j, { opacity: 1, text: `脱落 ${k.sum(a.lost.map(x => x.n))} ${u}${a.lost.length ? `：${a.lost.map(x => `${x.reason} ${x.n}`).join('、')}` : ''}` }], ...lostPos[j].ms.map((m, q) => ['m' + marks.indexOf(m), { ...lostPos[j].pos[q], fill: 'rgba(255,255,255,0)', cls: { 'is-hollow': true } }])])) } },
      { id: 'analysed', caption: `进入分析：${arms.map(a => { const an = a.n - k.sum(a.lost.map(x => x.n)); return `${a.name} ${an} ${u}（${pct(an, a.n)}%）`; }).join('，')}`,
        set: Object.fromEntries(arms.map((a, j) => ['an' + j, { opacity: 1, count: a.n - k.sum(a.lost.map(x => x.n)), unit: ` ${u} 进入分析` }])) },
    ];
    return mount(root, scenes, opt, scenes.length - 1, [{ value: k.fmt(d.screened), label: `筛选（${u}）` }, { value: k.fmt(R), label: `随机化（${u}）` }, ...arms.map(a => ({ value: k.fmt(a.n - k.sum(a.lost.map(x => x.n))), label: `${a.name}分析（${u}）` }))]);
  });

  /* ---------- curve ----------
     data: { x: [labels], unit, series: [{name, values: [number|null], role?}], threshold?: {value, label}, window?: {from, to, label}, events?: [{at, label}], takeaway? } */
  def('curve', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'curve', d.note), A = asp(cv), xs = d.x, n = xs.length, u = d.unit || '';
    // a difference between two percentages is in percentage points
    const du = u === '%' ? ' 个百分点' : u;
    const all = d.series.flatMap(s => s.values).filter(Number.isFinite).concat(d.threshold ? [d.threshold.value] : []);
    const lo = Math.min(0, ...all), step = 10 ** Math.floor(Math.log10(Math.max(...all) - lo || 1)), hi = Math.ceil(Math.max(...all) / step) * step;
    const box = [.1, .08, .66, .76], X = i => box[0] + i / (n - 1) * box[2], Y = v => box[1] + box[3] - (v - lo) / (hi - lo) * box[3];
    const Lk = k.links(cv), defs = document.createElementNS(Lk.svg.namespaceURI, 'defs'); Lk.svg.prepend(defs);
    const uid = 'kzc' + Math.random().toString(36).slice(2, 8);
    k.obj(cv, 'axx', 'kz-demo-axis'); k.obj(cv, 'axy', 'kz-demo-axis');
    for (let j = 0; j <= 4; j++) k.obj(cv, 'yt' + j, 'kz-demo-tick is-y', k.fmt(lo + (hi - lo) * j / 4));
    xs.forEach((x, i) => k.obj(cv, 'xt' + i, 'kz-demo-tick is-x', x));
    d.series.forEach((s, si) => {
      const cp = document.createElementNS(Lk.svg.namespaceURI, 'clipPath'); cp.id = `${uid}-${si}`; const r = document.createElementNS(Lk.svg.namespaceURI, 'rect');
      r.setAttribute('x', '0'); r.setAttribute('y', '0'); r.setAttribute('height', '1000'); r.setAttribute('width', '0'); r.dataset.kzObj = 'cr' + si; cp.append(r); defs.append(cp);
      let dpath = '', pen = false; s.values.forEach((v, i) => { if (!Number.isFinite(v)) { pen = false; return; } dpath += `${pen ? 'L' : 'M'}${(X(i) * 1000).toFixed(1)} ${(Y(v) * 1000).toFixed(1)} `; pen = true; });
      const p = Lk.path('p' + si, dpath.trim(), 'is-series' + (s.role === 'comparator' ? ' is-comparator' : '')); p.setAttribute('clip-path', `url(#${cp.id})`);
      s.values.forEach((v, i) => { if (Number.isFinite(v)) k.obj(cv, `d${si}_${i}`, 'kz-demo-dot' + (s.role === 'comparator' ? ' is-comparator' : ' is-treat')); });
      k.obj(cv, 'el' + si, 'kz-demo-label is-left' + (s.role === 'comparator' ? '' : ' is-strong'));
    });
    if (d.threshold) { k.obj(cv, 'th', 'kz-demo-threshold'); k.obj(cv, 'thl', 'kz-demo-note is-risk', d.threshold.label); }
    if (d.window) { k.obj(cv, 'wb', 'kz-demo-band'); k.obj(cv, 'wl', 'kz-demo-dep is-risk'); k.obj(cv, 'wd', 'kz-demo-callout is-risk'); }
    (d.events || []).forEach((e, j) => { k.icon(cv, 'ev' + j, 'flag', 'is-on'); k.obj(cv, 'evl' + j, 'kz-demo-note', e.label); });
    const firstOf = s => s.values.findIndex(Number.isFinite);
    const lastOf = s => { for (let i = s.values.length - 1; i >= 0; i--) if (Number.isFinite(s.values[i])) return i; return -1; };
    const base = { axx: { x: box[0], y: box[1] + box[3], w: box[2], h: .004 }, axy: { x: box[0], y: box[1], w: .003, h: box[3] } };
    for (let j = 0; j <= 4; j++) base['yt' + j] = { x: 0, y: Y(lo + (hi - lo) * j / 4) - .025, w: .055 };
    xs.forEach((x, i) => { base['xt' + i] = { x: X(i) - .04, y: box[1] + box[3] + .015, w: .08 }; });
    const show = si => { const s = d.series[si], o = { ['cr' + si]: { attr: { width: 1000 } } }; s.values.forEach((v, i) => { if (Number.isFinite(v)) o[`d${si}_${i}`] = { ...sq(X(i), Y(v), .012, A), opacity: 1 }; });
      const li = lastOf(s); o['el' + si] = { x: X(li) + .02, y: Y(s.values[li]) - .025, w: .2, opacity: 1, text: `${s.name} ${k.fmt(s.values[li])}${u}` }; return o; };
    d.series.forEach((s, si) => { base['cr' + si] = { attr: { width: 0 } }; s.values.forEach((v, i) => { if (Number.isFinite(v)) base[`d${si}_${i}`] = { ...sq(X(i), Y(v), .012, A), opacity: 0 }; }); base['el' + si] = { x: X(lastOf(s)) + .02, y: Y(s.values[lastOf(s)]) - .025, w: .2, opacity: 0, text: '' }; });
    if (d.threshold) Object.assign(base, { th: { x: box[0], y: Y(d.threshold.value), w: box[2], h: .004, opacity: 0 }, thl: { x: box[0] + .01, y: Y(d.threshold.value) - .06, w: .2, opacity: 0, cls: { 'is-start': true } } });
    if (d.window) Object.assign(base, { wb: { x: X(d.window.from), y: box[1], w: .002, h: box[3], opacity: 0 }, wl: { x: X(d.window.to), y: box[1], w: .004, h: 0, opacity: 0 }, wd: { x: X(d.window.to) - .26, y: box[1] + .02, w: .25, opacity: 0, text: '' } });
    (d.events || []).forEach((e, j) => Object.assign(base, { ['ev' + j]: { ...sq(X(e.at), box[1] + box[3] - .05, .022, A), opacity: 0 }, ['evl' + j]: { x: X(e.at) - .1, y: box[1] + box[3] - .14 - (j % 2) * .06, w: .2, opacity: 0 } }));
    const [s0, s1] = d.series, scenes = [{ id: s0.name, caption: `${s0.name}：${xs[firstOf(s0)]} 到 ${xs[lastOf(s0)]}，${k.fmt(s0.values.find(Number.isFinite))} → ${k.fmt(s0.values[lastOf(s0)])}${u}`, set: { ...base, ...show(0) } }];
    // the other series join on the same scale in one scene
    if (s1) scenes.push({ id: s1.name, caption: `${d.series.slice(1).map(s => `${s.name}`).join('、')}同一刻度：${d.series.slice(1).map(s => `${k.fmt(s.values.find(Number.isFinite))} → ${k.fmt(s.values[lastOf(s)])}${u}`).join('；')}`, set: Object.assign({}, ...d.series.slice(1).map((_, q) => show(q + 1))) });
    if (d.threshold) { const over = d.series.map(s => s.values.filter(v => Number.isFinite(v) && v >= d.threshold.value).length);
      scenes.push({ id: 'threshold', caption: `${d.threshold.label.includes(k.fmt(d.threshold.value)) ? d.threshold.label : `${d.threshold.label}（${k.fmt(d.threshold.value)}${u}）`}：${d.series.map((s, si) => `${s.name} ${over[si]} 个时点达到`).join('，')}`, set: { th: { opacity: 1 }, thl: { opacity: 1 },
        ...Object.fromEntries(d.series.flatMap((s, si) => s.values.map((v, i) => [`d${si}_${i}`, Number.isFinite(v) ? { cls: { 'is-over': v >= d.threshold.value } } : null]).filter(e => e[1]))) } }); }
    if (d.window && s1) { const a = s0.values[d.window.to], b = s1.values[d.window.to], diff = a - b;
      need(Number.isFinite(a) && Number.isFinite(b), `curve：窗口终点 ${xs[d.window.to]} 需两条曲线都有值`);
      scenes.push({ id: 'window', caption: `${d.window.label}：${xs[d.window.to]}时两者相差 ${k.fmt(Math.abs(diff))}${du}`, set: { wb: { w: X(d.window.to) - X(d.window.from), opacity: 1 }, wl: { y: Y(Math.max(a, b)), h: Math.abs(Y(a) - Y(b)), opacity: 1 }, wd: { opacity: 1, text: `差值 ${diff > 0 ? '+' : ''}${k.fmt(diff)}${du}` } } }); }
    if (d.events?.length) scenes.push({ id: 'events', caption: d.takeaway || d.events.map(e => `${xs[e.at]}：${e.label}`).join('；'), set: Object.fromEntries(d.events.flatMap((e, j) => [['ev' + j, { opacity: 1 }], ['evl' + j, { opacity: 1 }]])) });
    return mount(root, scenes, opt, scenes.length - 1, d.series.map(s => ({ value: `${k.fmt(s.values[lastOf(s)])}${u}`, label: `${s.name}（${xs[lastOf(s)]}）` })));
  });

  /* ---------- breakdown ----------
     data: { unit, total: {label}, parts: [{label, value, children?: [{label, value, flag?}]}], focus?, takeaway? } */
  def('breakdown', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'breakdown', d.note), u = d.unit || '', parts = [...d.parts].sort((a, b) => b.value - a.value), T = k.sum(parts.map(p => p.value));
    const f = parts.find(p => p.label === d.focus) || parts.find(p => p.children?.length) || parts[0], ch = f.children || [], flag = ch.find(c => c.flag) || ch[0];
    need(!ch.length || Math.abs(k.sum(ch.map(c => c.value)) - f.value) <= 1e-9 * Math.max(1, Math.abs(f.value)), `breakdown：「${f.label}」的子项合计与其数值不符`);
    const box = [.03, .06, .62, .86], fi = parts.indexOf(f);
    k.obj(cv, 'tot', 'kz-demo-block is-total'); k.obj(cv, 'tv', 'kz-demo-figure');
    parts.forEach((p, i) => { k.obj(cv, 'pb' + i, 'kz-demo-block is-p' + (i % 4)); k.obj(cv, 'pl' + i, 'kz-demo-label is-strong is-start'); k.obj(cv, 'pv' + i, 'kz-demo-note is-start'); });
    ch.forEach((c, j) => { k.obj(cv, 'cb' + j, 'kz-demo-block is-child'); k.obj(cv, 'cl' + j, 'kz-demo-label is-left'); k.obj(cv, 'rr' + j, 'kz-demo-row'); });
    k.obj(cv, 'rh', 'kz-demo-label is-left is-strong');
    // slice-and-dice: parts left to right by value; the focus part's children top to bottom
    const w0 = box[2] * parts[0].value / T, rest = T - parts[0].value; let yy0 = box[1];
    const slices = parts.map((p, i) => { if (!i) return { x: box[0], y: box[1], w: w0 - .006, h: box[3] }; const h = box[3] * p.value / rest, r = { x: box[0] + w0, y: yy0, w: box[2] - w0, h: Math.max(.004, h - .008) }; yy0 += h; return r; });
    const lab = (r, i) => ({ ['pl' + i]: { x: r.x + .012, y: r.y + .015, w: Math.max(.06, r.w - .024) }, ['pv' + i]: { x: r.x + .012, y: r.y + .07, w: Math.max(.06, r.w - .024) } });
    const fbox = { x: box[0] + .1, y: box[1], w: box[2] - .1, h: box[3] };
    let y = fbox.y; const kids = ch.map(c => { const h = fbox.h * c.value / f.value, r = { x: fbox.x + .01, y: y + .004, w: fbox.w - .02, h: Math.max(.004, h - .008) }; y += h; return r; });
    const base = { tot: { x: box[0], y: box[1], w: box[2], h: box[3] }, tv: { x: box[0], y: box[1] + box[3] / 2 - .05, w: box[2], count: T, unit: ` ${u}` }, rh: { x: .68, y: .06, w: .3, opacity: 0, text: `${f.label}的构成` } };
    parts.forEach((p, i) => Object.assign(base, { ['pb' + i]: { ...slices[i], opacity: 0 }, ...lab(slices[i], i), ['pl' + i]: { ...lab(slices[i], i)['pl' + i], opacity: 0, text: p.label }, ['pv' + i]: { ...lab(slices[i], i)['pv' + i], opacity: 0, text: `${k.fmt(p.value)} ${u} · ${pct(p.value, T)}%` } }));
    ch.forEach((c, j) => Object.assign(base, { ['cb' + j]: { ...kids[j], opacity: 0 }, ['cl' + j]: { x: kids[j].x + .01, y: kids[j].y + kids[j].h / 2 - .025, w: kids[j].w - .02, opacity: 0, text: `${c.label} ${k.fmt(c.value)} ${u}` }, ['rr' + j]: { x: .68, y: .13 + j * .12, w: .3, h: .1, opacity: 0, text: '' } }));
    ch.forEach((c, j) => { const r = cv.querySelector(`[data-kz-obj="rr${j}"]`), kk = k.el('span', 'kz-demo-row-k', c.label); kk.dataset.kzObjText = ''; r.append(kk, k.el('span', 'kz-demo-row-v', `${k.fmt(c.value)} ${u} · 占总量 ${pct(c.value, T)}%`)); base['rr' + j].text = c.label; });
    const strip = i => { const others = parts.filter(p => p !== f), q = others.indexOf(parts[i]), h = box[3] / others.length; return { x: box[0], y: box[1] + q * h, w: .085, h: h - .008 }; };
    const top2 = parts.slice(0, 2).map(p => `${p.label} ${pct(p.value, T)}%`).join('、');
    const scenes = [
      { id: 'total', caption: `${d.total.label} ${k.fmt(T)} ${u}`, set: base },
      { id: 'parts', caption: `分成 ${parts.length} 部分，最大的是 ${top2}`, order: parts.map((_, i) => 'pb' + i), set: { tot: { opacity: 0 }, tv: { opacity: 0 }, ...Object.fromEntries(parts.flatMap((_, i) => [['pb' + i, { opacity: 1, from: { ...base.tot, opacity: 0 } }], ['pl' + i, { opacity: 1 }], ['pv' + i, { opacity: 1 }]])) } },
      { id: 'focus', caption: `聚焦「${f.label}」：${k.fmt(f.value)} ${u}，占 ${pct(f.value, T)}%`, order: ['pb' + fi],
        set: Object.fromEntries(parts.flatMap((p, i) => i === fi ? [['pb' + i, { ...fbox, cls: { 'is-focus': true } }], ['pl' + i, { x: fbox.x + .01, y: fbox.y + .015, w: .3 }], ['pv' + i, { x: fbox.x + .01, y: fbox.y + .065, w: .3 }]]
          : [['pb' + i, { ...strip(i), opacity: .55 }], ['pl' + i, { opacity: 0 }], ['pv' + i, { opacity: 0 }]])) },
    ];
    if (ch.length) {
      scenes.push({ id: 'children', caption: `「${f.label}」里，${flag.label} ${k.fmt(flag.value)} ${u}，占总量 ${pct(flag.value, T)}%`, order: ch.flatMap((_, j) => ['cb' + j, 'rr' + j]),
        set: { rh: { opacity: 1 }, ['pl' + fi]: { opacity: 0 }, ['pv' + fi]: { opacity: 0 }, ...Object.fromEntries(ch.flatMap((c, j) => [['cb' + j, { opacity: 1, cls: { 'is-flag': c === flag } }], ['cl' + j, { opacity: 1 }], ['rr' + j, { opacity: 1, cls: { 'is-diff': c === flag } }]])) } });
      const fs = slices[fi]; let yy = fs.y; const back = ch.map(c => { const h = fs.h * c.value / f.value, r = { x: fs.x + .004, y: yy + .004, w: Math.max(.004, fs.w - .008), h: Math.max(.004, h - .008) }; yy += h; return r; });
      scenes.push({ id: 'context', caption: d.takeaway || `放回总量：${flag.label}是 ${k.fmt(T)} ${u} 中的 ${k.fmt(flag.value)} ${u}`,
        set: { ...Object.fromEntries(parts.flatMap((p, i) => [['pb' + i, { ...slices[i], opacity: 1, cls: { 'is-focus': false } }], ...Object.entries(lab(slices[i], i)).map(([id, v]) => [id, { ...v, opacity: 1 }])])),
          // the focus part keeps its name; inside it only the flagged child stays, labelled where it sits in the whole
          ...Object.fromEntries(ch.flatMap((c, j) => [['cb' + j, { ...back[j], opacity: c === flag ? 1 : 0 }], ['cl' + j, c === flag && back[j].h >= .07 ? { x: back[j].x + .01, y: back[j].y + back[j].h / 2 - .025, w: back[j].w - .02, opacity: 1 } : { opacity: 0 }]])) } });
    }
    return mount(root, scenes, opt, Math.max(2, scenes.length - 2), [{ value: `${k.fmt(T)}`, label: `${d.total.label}（${u}）` }, { value: `${pct(f.value, T)}%`, label: f.label }, ...(flag ? [{ value: `${pct(flag.value, T)}%`, label: flag.label, risk: !!flag.flag }] : [])]);
  });

  /* ---------- audit ----------
     data: { title, fields: [{label, value, ok, rule?}], groups? (number of scenes for the check) } */
  def('audit', (root, d, opt) => {
    const k = K(), L = k.S().layout, cv = k.frame(root, 'audit', d.note), A = asp(cv), F = d.fields, N = F.length, bad = F.filter(f => !f.ok);
    const rows = L.rows(N, { box: [.05, .15, .4, .78], gap: .22 });
    k.obj(cv, 'pg', 'kz-demo-paper'); k.icon(cv, 'pi', 'doc'); k.obj(cv, 'pt', 'kz-demo-label is-left is-strong', d.title);
    F.forEach((f, i) => { const r = k.obj(cv, 'f' + i, 'kz-demo-row'), kk = k.el('span', 'kz-demo-row-k', f.label); kk.dataset.kzObjText = ''; r.append(kk, k.el('span', 'kz-demo-row-v', f.value)); k.glyph(k.obj(cv, 'fm' + i, 'kz-demo-mark-sign'), f.ok ? 'check' : 'cross', f.ok ? '✓' : '✕'); });
    k.obj(cv, 'fp', 'kz-demo-bin is-list'); k.obj(cv, 'fh', 'kz-demo-label is-left is-strong'); k.obj(cv, 'sc', 'kz-demo-count'); k.icon(cv, 'mg', 'search', 'is-on');
    bad.forEach((f, j) => { k.obj(cv, 'fc' + j, 'kz-demo-finding'); });
    const panel = { x: .55, y: .04, w: .42, h: .92 }, fh2 = Math.min(.16, (panel.h - .2) / Math.max(1, bad.length) - .02), slot = j => ({ x: panel.x + .02, y: panel.y + .16 + j * (fh2 + .02), w: panel.w - .04, h: fh2 });
    const base = { pg: { x: .03, y: .04, w: .44, h: .92 }, pi: sq(.065, .09, .03, A), pt: { x: .09, y: .065, w: .36 }, fp: { ...panel }, fh: { x: panel.x + .02, y: panel.y + .03, w: .2, text: '核查发现 0 项' }, sc: { x: panel.x + .24, y: panel.y + .035, w: .16, text: `已核 0 / ${N}` }, mg: { ...sq(.47, .12, .045, A), opacity: 0 } };
    F.forEach((f, i) => Object.assign(base, { ['f' + i]: { ...rows[i] }, ['fm' + i]: { x: .455, y: rows[i].y + rows[i].h / 2 - .025, w: .04, opacity: 0, cls: { 'is-diff': !f.ok } } }));
    bad.forEach((f, j) => { const el = cv.querySelector(`[data-kz-obj="fc${j}"]`); el.append(k.el('b', null, `${f.label}：${f.value}`), k.el('span', null, f.rule || '与依据不符')); const i = F.indexOf(f); base['fc' + j] = { ...rows[i], opacity: 0 }; });
    const groups = chunk(F, d.groups || 3), scenes = [{ id: 'doc', caption: `${d.title}：${N} 个字段待核`, set: base }]; let seen = 0, found = 0;
    groups.forEach((g, gi) => {
      const set = {}, gf = g.filter(f => !f.ok);
      g.forEach(f => { const i = F.indexOf(f); set['fm' + i] = { opacity: 1 }; if (!f.ok) set['f' + i] = { cls: { 'is-diff': true } }; });
      gf.forEach(f => { const j = bad.indexOf(f), i = F.indexOf(f); set['fc' + j] = { ...slot(j), opacity: 1 }; });
      seen += g.length; found += gf.length; const last = F.indexOf(g[g.length - 1]);
      set.mg = { ...sq(.47, rows[last].y + rows[last].h / 2, .045, A), opacity: 1, via: g.slice(0, -1).map(f => { const r = rows[F.indexOf(f)]; const s = sq(.47, r.y + r.h / 2, .045, A); return [s.x, s.y]; }) };
      set.fh = { text: `核查发现 ${found} 项` }; set.sc = { text: `已核 ${seen} / ${N}` };
      scenes.push({ id: 'g' + gi, caption: `${g[0].label}至${g[g.length - 1].label}：${!gf.length ? '全部相符' : gf.length === 1 ? `${gf[0].label}不符（${gf[0].rule || '与依据不符'}）` : `${gf.map(f => f.label).join('、')}不符，规则见发现清单`}`, order: ['mg', ...gf.map(f => 'fc' + bad.indexOf(f))], set });
    });
    scenes.push({ id: 'summary', caption: `${N} 个字段中 ${N - bad.length} 个相符（${pct(N - bad.length, N)}%），${bad.length} 项转交更正`, set: { mg: { opacity: 0 }, sc: { text: `相符 ${N - bad.length} / ${N}`, cls: { 'is-risk': bad.length > 0 } } } });
    return mount(root, scenes, opt, scenes.length - 1, [{ value: `${N - bad.length}/${N}`, label: '相符字段' }, { value: String(bad.length), label: '核查发现', risk: bad.length > 0 }, { value: `${pct(N - bad.length, N)}%`, label: '相符率' }]);
  });

  /* ---------- matrix ----------
     data: { x: {label, levels: [...]}, y: {label, levels: [...]} (low → high), items: [{label, at: [xi, yi], after?: [xi, yi], action?}], high (score ≥ high is the high zone) } */
  def('matrix', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'matrix', d.note), A = asp(cv), nx = d.x.levels.length, ny = d.y.levels.length, I = d.items;
    const g = { x: .12, y: .1, w: .48, h: .7 }, cw = g.w / nx, chh = g.h / ny, score = ([a, b]) => (a + 1) * (b + 1), high = d.high ?? Math.ceil(nx * ny / 2);
    const cell = ([a, b]) => ({ x: g.x + a * cw, y: g.y + (ny - 1 - b) * chh, w: cw, h: chh });
    for (let a = 0; a < nx; a++) for (let b = 0; b < ny; b++) { const s = score([a, b]); k.obj(cv, `c${a}_${b}`, 'kz-demo-heat ' + (s >= high ? 'is-high' : s >= high / 2 ? 'is-mid' : 'is-low')); }
    d.x.levels.forEach((t, a) => k.obj(cv, 'xl' + a, 'kz-demo-tick is-x', t)); d.y.levels.forEach((t, b) => k.obj(cv, 'yl' + b, 'kz-demo-tick is-y', t));
    k.obj(cv, 'xt', 'kz-demo-head', d.x.label); k.obj(cv, 'yt', 'kz-demo-head', d.y.label);
    I.forEach((it, i) => { k.obj(cv, 'it' + i, 'kz-demo-dot is-num', String(i + 1)); k.obj(cv, 'lg' + i, 'kz-demo-row'); });
    k.obj(cv, 'hc', 'kz-demo-callout');
    // items sharing a cell sit side by side inside it
    const place = key => { const groups = {}; I.forEach((it, i) => { const c = it[key] || it.at, id = c.join(); (groups[id] ||= []).push(i); });
      const out = {}; for (const ids of Object.values(groups)) ids.forEach((i, q) => { const c = cell(I[i][key] || I[i].at), m = ids.length, cx = c.x + c.w * (q + 1) / (m + 1); out[i] = sq(cx, c.y + c.h / 2, .034, A); }); return out; };
    const P0 = place('at'), P1 = place('after'), list = i => ({ x: .66, y: g.y + i * Math.min(.16, g.h / I.length), w: .32, h: Math.min(.14, g.h / I.length - .02) });
    const base = { xt: { x: g.x, y: g.y + g.h + .065, w: g.w }, yt: { x: g.x, y: .02, w: g.w }, hc: { x: .62, y: g.y + g.h + .055, w: .36, opacity: 0, text: '' } };
    for (let a = 0; a < nx; a++) for (let b = 0; b < ny; b++) base[`c${a}_${b}`] = { ...cell([a, b]), w: cw - .004, h: chh - .006 };
    d.x.levels.forEach((t, a) => { base['xl' + a] = { x: g.x + a * cw, y: g.y + g.h + .01, w: cw }; }); d.y.levels.forEach((t, b) => { base['yl' + b] = { x: 0, y: cell([0, b]).y + chh / 2 - .025, w: .11 }; });
    I.forEach((it, i) => { const el = cv.querySelector(`[data-kz-obj="lg${i}"]`), kk = k.el('span', 'kz-demo-row-k', `${i + 1} ${it.label}`); kk.dataset.kzObjText = ''; el.append(kk, k.el('span', 'kz-demo-row-v', '')); base['it' + i] = { ...sq(.66, list(i).y + list(i).h / 2, .034, A), opacity: 0 }; base['lg' + i] = { ...list(i), opacity: .45, text: `${i + 1} ${it.label}` }; });
    const hi0 = I.filter(it => score(it.at) >= high), hi1 = I.filter(it => score(it.after || it.at) >= high), mov = I.filter(it => it.after);
    const scenes = [
      { id: 'grid', caption: `${d.y.label} ${ny} 档 × ${d.x.label} ${nx} 档；评分 ≥ ${high} 为高风险区`, set: base },
      { id: 'place', caption: `${I.length} 项风险按评估落位`, order: I.map((_, i) => 'it' + i), set: Object.fromEntries(I.flatMap((it, i) => [['it' + i, { ...P0[i], opacity: 1 }], ['lg' + i, { opacity: 1 }]])) },
      { id: 'high', caption: `高风险区 ${hi0.length} 项：${hi0.map(it => it.label).join('、') || '无'}`, set: { ...Object.fromEntries(I.map((it, i) => ['it' + i, { cls: { 'is-risk': score(it.at) >= high } }])), hc: { opacity: 1, text: `高风险 ${hi0.length} 项`, cls: { 'is-risk': true } } } },
      { id: 'mitigate', caption: `采取措施后 ${mov.length} 项移位：${mov.map(it => it.action).join('、')}`, order: mov.map(it => 'it' + I.indexOf(it)),
        set: Object.fromEntries(I.flatMap((it, i) => it.after ? [['it' + i, { ...P1[i], cls: { 'is-risk': score(it.after) >= high, 'is-moved': true } }], ['lg' + i, { text: `${i + 1} ${it.label}` }]] : [['it' + i, { ...P1[i] }]])) },
      { id: 'summary', caption: `高风险从 ${hi0.length} 项降到 ${hi1.length} 项${hi1.length ? `，${hi1.map(it => it.label).join('、')}仍需跟踪` : ''}`, set: { hc: { text: `高风险 ${hi0.length} → ${hi1.length} 项`, cls: { 'is-risk': hi1.length > 0 } }, ...Object.fromEntries(I.flatMap((it, i) => score(it.after || it.at) >= high ? [] : [['it' + i, { opacity: .55 }], ['lg' + i, { opacity: .55 }]])) } },
    ];
    mov.forEach(it => { const el = cv.querySelector(`[data-kz-obj="lg${I.indexOf(it)}"] .kz-demo-row-v`); el.textContent = it.action; el.style.opacity = '0'; el.dataset.reveal = '1'; });
    const st = mount(root, scenes, { ...opt, onScene: undefined }, 4, [{ value: String(hi0.length), label: '措施前高风险', risk: hi0.length > 0 }, { value: String(hi1.length), label: '措施后高风险', risk: hi1.length > 0 }, { value: String(mov.length), label: '有措施的风险项' }]);
    // the action text beside each moved item appears from the mitigation scene on
    st.spec.onScene = i => cv.querySelectorAll('[data-reveal] ').forEach(e => { e.style.opacity = i >= 3 ? '1' : '0'; });
    st.spec.onScene(st.scene);
    return st;
  });

  /* ---------- network ----------
     data: { nodes: [{id, label, icon, x, y}], links: [{from, to}], packets: [{label, route: [ids], blocked?: [from, to], note}], intro? } */
  def('network', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'network', d.note), A = asp(cv), N = d.nodes, ni = id => N.findIndex(n => n.id === id), Lk = k.links(cv), iw = .065;
    // node positions are fractions of the network area; the right column holds the packet log
    const c = id => [.04 + N[ni(id)].x * .64, .04 + N[ni(id)].y * .86], key = (a, b) => [a, b].sort().join('|'), linkIdx = (a, b) => d.links.findIndex(l => key(l.from, l.to) === key(a, b));
    d.links.forEach((l, i) => Lk.path('lk' + i, k.pts([c(l.from), c(l.to)]), 'is-rail'));
    N.forEach((n, i) => { k.icon(cv, 'n' + i, n.icon || 'building'); k.obj(cv, 'nl' + i, 'kz-demo-label', n.label); k.obj(cv, 'nc' + i, 'kz-demo-badge'); });
    // chips are as wide as their longest label (measured before the stage positions them), at least .11
    const chips = d.packets.map((p, j) => k.obj(cv, 'pk' + j, 'kz-demo-case', p.label)), pw = Math.max(.11, ...chips.map(c => (c.scrollWidth + 6) / (cv.clientWidth || 1e9))); k.icon(cv, 'bx', 'unlink', 'is-risk'); k.obj(cv, 'bxl', 'kz-demo-note is-risk');
    k.obj(cv, 'lgp', 'kz-demo-bin is-list'); k.obj(cv, 'lgh', 'kz-demo-label is-left is-strong');
    const fate = p => (p.blocked ? '受阻' : `送达${N[ni(p.route[p.route.length - 1])].label}`);
    d.packets.forEach((p, j) => { const r = k.obj(cv, 'lg' + j, 'kz-demo-row'), kk = k.el('span', 'kz-demo-row-k', p.label); kk.dataset.kzObjText = ''; r.append(kk, k.el('span', 'kz-demo-row-v', fate(p))); });
    const LP = { x: .74, y: .04, w: .24, h: .9 }, lgRow = j => ({ x: LP.x + .012, y: LP.y + .13 + j * .13, w: LP.w - .024, h: .1 });
    const base = { bx: { ...sq(.5, .5, .04, A), opacity: 0 }, bxl: { x: .4, y: .5, w: .2, opacity: 0, text: '' }, lgp: { ...LP }, lgh: { x: LP.x + .015, y: LP.y + .03, w: LP.w - .03, text: `数据包 0/${d.packets.length}` } };
    d.packets.forEach((p, j) => { base['lg' + j] = { ...lgRow(j), opacity: 0 }; });
    d.links.forEach((l, i) => { base['lk' + i] = { stroke: k.MUTE, cls: { 'is-broken': false } }; });
    N.forEach((n, i) => { const [x, y] = c(n.id); Object.assign(base, { ['n' + i]: sq(x, y, iw, A), ['nl' + i]: { x: x - .08, y: y + iw * A / 2 + .01, w: .16 }, ['nc' + i]: { x: x + iw / 2 - .01, y: y - iw * A / 2 - .03, w: .032, count: 0, opacity: 0 } }); });
    const scenes = [{ id: 'net', caption: d.intro || `${N.length} 方、${d.links.length} 条数据通道`, set: base }], got = N.map(() => 0), broken = new Set(); let blocked = 0;
    d.packets.forEach((p, j) => {
      const route = p.route, set = {}, pos = ([x, y]) => [x - pw / 2, y - iw * A / 2 - .07];
      let stop = route.length - 1;
      if (p.blocked) { const b = route.indexOf(p.blocked[0]); need(b >= 0 && route[b + 1] === p.blocked[1], `network：${p.label} 的阻断通道不在其路径上`); stop = b; }
      const pts = route.slice(0, stop + 1).map(id => pos(c(id)));
      if (p.blocked) { const [a, b] = p.blocked, m = [(c(a)[0] + c(b)[0]) / 2, (c(a)[1] + c(b)[1]) / 2], li = linkIdx(a, b); pts.push([m[0] + .015, m[1] - .045]); blocked++;
        set['lk' + li] = { stroke: k.C('risk'), cls: { 'is-broken': true } }; broken.add(li); set.bx = { ...sq(m[0], m[1], .04, A), opacity: 1 }; set.bxl = { x: m[0] - .08, y: m[1] + .04, w: .16, opacity: 1, text: p.note || '通道中断' }; }
      else { const last = ni(route[route.length - 1]), [nx, ny] = c(route[route.length - 1]); got[last]++; set['nc' + last] = { count: got[last], opacity: 1 }; pts.push([nx - pw / 2, Math.min(.9, ny + iw * A / 2 + .06 + (got[last] - 1) * .06)]); }
      d.links.forEach((_, li) => { if (!set['lk' + li] && !broken.has(li)) set['lk' + li] = { stroke: k.MUTE }; });
      route.slice(0, stop + 1).forEach((id, q) => { if (q) { const li = linkIdx(route[q - 1], id); if (!broken.has(li)) set['lk' + li] = { stroke: k.C('brand') }; } });
      d.packets.forEach((_, q) => { if (q < j) set['pk' + q] = { opacity: .35 }; });
      const [x, y] = pts[pts.length - 1];
      set['pk' + j] = { from: { x: pts[0][0], y: pts[0][1], w: pw, opacity: 0 }, x, y, w: pw, opacity: 1, via: pts.slice(1, -1) };
      set['lg' + j] = { opacity: 1, cls: { 'is-diff': !!p.blocked } }; set.lgh = { text: `数据包 ${j + 1}/${d.packets.length}` };
      scenes.push({ id: 'p' + j, caption: `${p.label}：${route.slice(0, stop + 1).map(id => N[ni(id)].label).join(' → ')}${p.blocked ? ` ✕ ${N[ni(p.blocked[1])].label}（${p.note || '通道中断'}）` : ' 送达'}`, order: ['pk' + j, 'lg' + j], set });
    });
    const delivered = d.packets.length - blocked;
    scenes.push({ id: 'summary', caption: `${d.packets.length} 份数据送达 ${delivered} 份、受阻 ${blocked} 份；${blocked ? '修复中断通道前，受阻数据不进入下游' : '全部按路径送达'}`, set: { lgh: { text: `送达 ${delivered} · 受阻 ${blocked}`, cls: { 'is-risk': blocked > 0 } }, ...Object.fromEntries(d.packets.map((_, q) => ['pk' + q, { opacity: 1 }])) } });
    return mount(root, scenes, opt, scenes.length - 1, [{ value: String(delivered), label: '送达' }, { value: String(blocked), label: '受阻', risk: blocked > 0 }, { value: String(d.links.length), label: '数据通道' }]);
  });

  /* ---------- schedule ----------
     data: { unit, span: [d0, d1], visits: [{label, day, window: [-a, +b]}], subjects: [{label, actual: [day|null per visit]}] } */
  def('schedule', (root, d, opt) => {
    const k = K(), L = k.S().layout, cv = k.frame(root, 'schedule', d.note), A = asp(cv), V = d.visits, Sb = d.subjects, u = d.unit || '天';
    const X = L.scale(d.span, [.16, .96]), rows = L.rows(Sb.length, { box: [0, .16, 1, .74], gap: .3 });
    V.forEach((v, j) => { k.obj(cv, 'vb' + j, 'kz-demo-band'); k.obj(cv, 'vt' + j, 'kz-demo-dep'); k.obj(cv, 'vl' + j, 'kz-demo-tick is-x', v.label); });
    Sb.forEach((s, i) => { k.obj(cv, 'sl' + i, 'kz-demo-label is-left', s.label); k.obj(cv, 'sr' + i, 'kz-demo-axis is-soft'); V.forEach((v, j) => { k.obj(cv, `m${i}_${j}`, 'kz-demo-dot'); k.obj(cv, `t${i}_${j}`, 'kz-demo-note is-risk'); }); });
    k.icon(cv, 'cal', 'calendar');
    const base = { cal: sq(.05, .07, .03, A) };
    V.forEach((v, j) => Object.assign(base, { ['vb' + j]: { x: X(v.day + v.window[0]), y: .12, w: X(v.day + v.window[1]) - X(v.day + v.window[0]), h: .8 }, ['vt' + j]: { x: X(v.day) - .001, y: .12, w: .002, h: .8 }, ['vl' + j]: { x: X(v.day) - .06, y: .04, w: .12, text: `${v.label} · 第 ${v.day} ${u}` } }));
    const judge = (v, a) => (a == null ? { kind: 'miss', text: '缺访' } : a < v.day + v.window[0] ? { kind: 'early', text: `${a - v.day - v.window[0]} ${u}` } : a > v.day + v.window[1] ? { kind: 'late', text: `+${a - v.day - v.window[1]} ${u}` } : { kind: 'ok', text: '' });
    Sb.forEach((s, i) => { const cy = rows[i].y + rows[i].h / 2; Object.assign(base, { ['sl' + i]: { x: .01, y: cy - .03, w: .14 }, ['sr' + i]: { x: .16, y: cy, w: .8, h: .003 } });
      V.forEach((v, j) => { base[`m${i}_${j}`] = { ...sq(.16, cy, .016, A), opacity: 0 }; base[`t${i}_${j}`] = { x: X(v.day) - .05, y: cy + .03, w: .1, opacity: 0 }; }); });
    const counts = { ok: 0, early: 0, late: 0, miss: 0 }, scenes = [{ id: 'windows', caption: `${V.length} 次访视，各有允许窗口（${V.map(v => `${v.label} ${v.window[0]}/+${v.window[1]}`).join('，')}）`, set: base }];
    Sb.forEach((s, i) => {
      const cy = rows[i].y + rows[i].h / 2, set = {}, dev = [];
      V.forEach((v, j) => { const a = s.actual[j], r = judge(v, a); counts[r.kind]++;
        set[`m${i}_${j}`] = { ...sq(X(a ?? v.day), cy, .016, A), opacity: 1, cls: { 'is-ok': r.kind === 'ok', 'is-risk': r.kind === 'early' || r.kind === 'late', 'is-hollow': r.kind === 'miss' } };
        if (r.kind !== 'ok') { set[`t${i}_${j}`] = { x: X(a ?? v.day) - .05, opacity: 1, text: r.text }; dev.push(`${v.label}${r.kind === 'miss' ? '缺访' : `${r.kind === 'late' ? '晚' : '早'} ${Math.abs(parseInt(r.text, 10))} ${u}`}`); } });
      scenes.push({ id: 's' + i, caption: `${s.label}：${dev.length ? dev.join('，') : `${V.length} 次访视都在窗口内`}`, order: V.map((_, j) => `m${i}_${j}`), set });
    });
    const tot = Sb.length * V.length;
    scenes.push({ id: 'summary', caption: `${tot} 次访视：窗口内 ${counts.ok}，超窗 ${counts.early + counts.late}，缺访 ${counts.miss}；超窗与缺访按方案偏离记录`,
      set: Object.fromEntries(Sb.flatMap((s, i) => V.map((v, j) => [`m${i}_${j}`, { opacity: judge(v, s.actual[j]).kind === 'ok' ? .4 : 1 }]))) });
    return mount(root, scenes, opt, scenes.length - 1, [{ value: `${counts.ok}/${tot}`, label: '窗口内访视' }, { value: String(counts.early + counts.late), label: '超窗', risk: counts.early + counts.late > 0 }, { value: String(counts.miss), label: '缺访', risk: counts.miss > 0 }]);
  });
})(window);
