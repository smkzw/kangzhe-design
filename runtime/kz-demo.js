/* Kangzhe 7.1 — reusable demonstrative motion forms (15 DEMO-02) on KZScenes stages.
   Each form takes content data, builds its objects inside the stage root and returns a KZScenes.Stage.
   Every number on stage is computed here from the data passed in (15 DEMO-04): nothing is typed into a scene.
     KZDemo.mount(root, kind, data, { loop })   kind: units | calc | timeline | decision | story | compare
   Requires kz-scenes.js (and kz-tokens.js for timing). Styles: kz-glass.css “Demo stages”. */
(function (global) {
  'use strict';
  const S = () => global.KZScenes;
  const C = k => (global.KZ_TOKENS && global.KZ_TOKENS.colors && global.KZ_TOKENS.colors[k]) || { brand: '#FF9900', risk: '#C00000', ink: '#0F1115', muted: '#6B7280' }[k];
  const MUTE = '#D5DBE1', SOFT = '#EEF1F4';
  const sum = a => a.reduce((x, y) => x + (Number.isFinite(y) ? y : 0), 0);
  const fmt = n => Number(n).toLocaleString('zh-CN');
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function obj(canvas, id, cls, text) { const n = el('div', 'kz-demo-obj ' + (cls || ''), text); n.dataset.kzObj = id; canvas.append(n); return n; }
  // an icon in front of an object's text (15 DEMO-08); the text moves into a slot so scene text updates keep the icon
  // an icon standing alone in an object (a done tick, a verdict), with a text fallback when kz-icons.js is absent
  function glyph(n, name, fallback) { if (global.KZIcons) { n.append(global.KZIcons.svg(name)); n.classList.add('is-glyph'); } else n.textContent = fallback; return n; }
  // the facts a form computed, for the fact strip under a stacked stage (renderFacts, 15 DEMO-05)
  function facts(stage, list) { stage.facts = list.map(([value, label, risk]) => ({ value, label, risk: !!risk })); return stage; }
  function lead(n, name) { if (!name || !global.KZIcons) return n; const t = el('span', null, n.textContent); t.dataset.kzObjText = ''; n.replaceChildren(global.KZIcons.svg(name), t); n.classList.add('has-icon'); return n; }
  // Stage skeleton: canvas for the objects, then the caption band with the note tag and the scene rail
  // (state is readable, FILM 状态可辨). The tag sits in the band so it never covers the canvas corner.
  function frame(root, kind, note) {
    root.classList.add('kz-demo'); root.dataset.kzDemo = kind; root.replaceChildren();
    const canvas = el('div', 'kz-demo-canvas'); canvas.dataset.kzSceneCanvas = '';
    const foot = el('div', 'kz-demo-foot'), cap = el('p', 'kz-demo-caption'), rail = el('ol', 'kz-demo-rail');
    cap.dataset.kzSceneCaption = ''; cap.setAttribute('aria-live', 'polite'); rail.dataset.kzSceneRail = ''; rail.setAttribute('aria-label', '演示进度');
    foot.append(cap, ...(note ? [el('span', 'kz-demo-tag', note)] : []), rail); root.append(canvas, foot);
    return canvas;
  }

  /* ---------- units: one mark per record, regrouped scene by scene ----------
     data: { unit, groups: [{name, due, received}], owner, deadline, totalLabel, dueLabel, receivedLabel } */
  function units(root, d, opt) {
    const cv = frame(root, 'units', d.note), L = S().layout, g = d.groups, unit = d.unit || '份';
    const due = sum(g.map(x => x.due)), rec = sum(g.map(x => x.received)), miss = due - rec;
    const marks = []; g.forEach((x, gi) => { for (let k = 0; k < x.due; k++) marks.push({ gi, received: k < x.received, id: `m${marks.length}` }); });
    marks.forEach(m => obj(cv, m.id, 'kz-demo-mark'));
    const missing = marks.filter(m => !m.received);
    missing.forEach((m, i) => obj(cv, 'ghost' + i, 'kz-demo-mark is-ghost'));
    const total = obj(cv, 'total', 'kz-demo-figure'), tray = obj(cv, 'tray', 'kz-demo-tray');
    g.forEach((x, i) => { obj(cv, 'gl' + i, 'kz-demo-label'); obj(cv, 'gn' + i, 'kz-demo-count'); });
    const pool = L.grid(marks.length, { box: [.06, .2, .62, .62], cols: Math.ceil(marks.length / 3) });
    const colBox = L.cols(g.length, { box: [.02, .2, .7, .5], gap: .16 });
    const inCol = new Map(); g.forEach((x, gi) => L.grid(x.due, { box: [colBox[gi].x, colBox[gi].y, colBox[gi].w, colBox[gi].h], cols: 3, valign: 'bottom' }).forEach((r, k) => inCol.set(`${gi}:${k}`, r)));
    const pos = marks.map(m => inCol.get(`${m.gi}:${marks.filter(o => o.gi === m.gi).indexOf(m)}`));
    const trayBox = [.76, .26, .2, .5], trayPos = L.grid(missing.length, { box: [trayBox[0] + .03, trayBox[1] + .12, trayBox[2] - .06, trayBox[3] - .2], cols: 2 });
    const worst = g.map((x, i) => [x.due - x.received, i]).filter(([n]) => n > 0).sort((a, b) => b[0] - a[0]);
    const set = f => Object.fromEntries(marks.map((m, i) => [m.id, f(m, i)]));
    const lab = f => Object.fromEntries(g.flatMap((x, i) => [['gl' + i, f(x, i).l], ['gn' + i, f(x, i).n]]));
    const scenes = [
      { id: 'pool', caption: `${d.dueLabel || '应收'} ${due} ${unit}资料，一个方块是一${unit}`, set: { ...set((m, i) => ({ ...pool[i], fill: MUTE })), total: { x: .06, y: .04, w: .62, text: `${d.dueLabel || '应收'} ${due} ${unit}` } } },
      { id: 'group', caption: `按 ${g.length} 个资料组分开清点`, set: { ...set((m, i) => pos[i]), ...lab((x, i) => ({ l: { x: colBox[i].x - .01, y: .73, w: colBox[i].w + .02, text: x.name }, n: { x: colBox[i].x, y: .8, w: colBox[i].w, count: x.due, unit: ` ${unit}` } })) } },
      { id: 'fill', caption: `收到的变实心，缺的留空，缺失不按零处理`, set: { ...set(m => m.received ? { fill: C('brand') } : { fill: SOFT, cls: { 'is-missing': true } }), total: { text: `${d.receivedLabel || '已收'} ${rec} / ${d.dueLabel || '应收'} ${due} ${unit}` }, ...lab((x, i) => ({ n: { count: x.received, unit: ` / ${x.due} ${unit}` } })) } },
      { id: 'gap', caption: `缺口集中在${worst.map(([, i]) => g[i].name).join('与')}，共缺 ${miss} ${unit}`, order: [...missing.map(m => m.id)],
        set: { ...set((m, i) => m.received ? (g[m.gi].due > g[m.gi].received ? {} : { opacity: .35 }) : { fill: C('risk'), scale: 1.12 }), ...lab((x, i) => x.due > x.received ? { l: { cls: { 'is-risk': true } }, n: { text: `缺 ${x.due - x.received} ${unit}`, cls: { 'is-risk': true } } } : { l: { opacity: .45 }, n: { opacity: .45 } }), total: { text: `${d.missingLabel || '缺口'} ${miss} ${unit}`, cls: { 'is-risk': true } } } },
      { id: 'tray', caption: `${miss} ${unit}缺失进入补收清单，${d.owner || ''}牵头，${d.deadline || ''} 内完成`, order: missing.map(m => m.id),
        set: { ...Object.fromEntries(missing.map((m, i) => [m.id, { ...trayPos[i], scale: 1, via: [[.72, pos[marks.indexOf(m)].y - .08]] }])), ...Object.fromEntries(missing.map((m, i) => ['ghost' + i, { ...pos[marks.indexOf(m)] }])), tray: { from: { x: .92, y: trayBox[1], opacity: 0 }, x: trayBox[0], y: trayBox[1], w: trayBox[2], h: trayBox[3], text: `补收清单 · ${miss} ${unit}` } } },
    ];
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? 3 }), [[fmt(due), `应收（${unit}）`], [fmt(rec), `已收（${unit}）`], [fmt(miss), `缺口（${unit}）`, miss > 0]]);
  }

  /* ---------- calc: values fly out of the source table into the arithmetic ----------
     data: { unit, rows: [{name, a, b}], aLabel, bLabel, diffLabel } — result = Σa − Σb, checked row by row */
  function calc(root, d, opt) {
    const cv = frame(root, 'calc', d.note), r = d.rows, unit = d.unit || '', A = sum(r.map(x => x.a)), B = sum(r.map(x => x.b)), D = A - B;
    const rowY = i => .18 + i * (.62 / r.length), colX = { name: .03, a: .27, b: .36, d: .45 };
    const heads = [['hn', '资料组', colX.name, .23], ['ha', d.aLabel, colX.a, .08], ['hb', d.bLabel, colX.b, .08], ['hd', d.diffLabel, colX.d, .08]];
    heads.forEach(([id, text]) => obj(cv, id, 'kz-demo-head' + (id === 'hn' ? '' : ' is-num'), text));
    r.forEach((x, i) => { obj(cv, 'n' + i, 'kz-demo-cell'); obj(cv, 'a' + i, 'kz-demo-cell is-num'); obj(cv, 'b' + i, 'kz-demo-cell is-num'); obj(cv, 'd' + i, 'kz-demo-cell is-num'); obj(cv, 'fa' + i, 'kz-demo-token'); obj(cv, 'fb' + i, 'kz-demo-token is-b');
      obj(cv, 'ra' + i, 'kz-demo-bar is-ghost'); obj(cv, 'rb' + i, 'kz-demo-bar'); if (x.a > x.b) obj(cv, 'rg' + i, 'kz-demo-bar is-gap'); });
    for (let k = 0; k < r.length - 1; k++) { obj(cv, 'pa' + k, 'kz-demo-op', '+'); obj(cv, 'pb' + k, 'kz-demo-op', '+'); }
    ['sa', 'sb'].forEach(id => obj(cv, id, 'kz-demo-sum'));
    ['eA', 'eM', 'eB', 'eQ', 'eR'].forEach(id => obj(cv, id, 'kz-demo-eq'));
    obj(cv, 'check', 'kz-demo-check');
    const lineX = k => .55 + k * (.36 / r.length), cellW = .08;
    const base = Object.fromEntries(heads.map(([id, , x, w]) => [id, { x, y: .07, w }]));
    // each row carries a bar on one scale under its name: due as the outline, received filling it, the gap in red
    const maxA = Math.max(...r.map(x => x.a), 1), BW = .5, bar = (i, v, at = 0) => ({ x: colX.name + BW * at / maxA, y: rowY(i) + .075, w: BW * v / maxA, h: .03 });
    r.forEach((x, i) => Object.assign(base, { ['ra' + i]: bar(i, x.a), ['rb' + i]: { ...bar(i, x.b), w: 0, opacity: 0 }, ...(x.a > x.b ? { ['rg' + i]: { ...bar(i, x.a - x.b, x.b), opacity: 0 } } : {}) }));
    r.forEach((x, i) => Object.assign(base, { ['n' + i]: { x: colX.name, y: rowY(i), w: .23, text: x.name }, ['a' + i]: { x: colX.a, y: rowY(i), w: cellW, text: fmt(x.a) }, ['b' + i]: { x: colX.b, y: rowY(i), w: cellW, text: fmt(x.b) } }));
    const fly = (p, y, key) => Object.fromEntries(r.flatMap((x, i) => [[p + i, { from: { x: colX[key], y: rowY(i) }, x: lineX(i), y, w: .06, text: fmt(x[key]) }], ...(i < r.length - 1 ? [[(p === 'fa' ? 'pa' : 'pb') + i, { x: lineX(i) + .06, y, w: .03 }]] : [])]));
    const nz = r.map((x, i) => [x.a - x.b, i]).filter(([v]) => v !== 0);
    const scenes = [
      { id: 'table', caption: `${r.length} 组资料的${d.aLabel}与${d.bLabel}`, set: base },
      { id: 'sumA', caption: `${d.aLabel}逐组相加：${r.map(x => fmt(x.a)).join(' + ')} = ${fmt(A)}`, order: r.map((_, i) => 'fa' + i), set: { ...fly('fa', .2, 'a'), sa: { x: .55, y: .3, w: .4, count: A, unit: ` ${unit}`, from: { count: 0 } } } },
      { id: 'sumB', caption: `${d.bLabel}同样相加：${r.map(x => fmt(x.b)).join(' + ')} = ${fmt(B)}`, order: r.map((_, i) => 'fb' + i), set: { ...fly('fb', .44, 'b'), sb: { x: .55, y: .54, w: .4, count: B, unit: ` ${unit}`, from: { count: 0 } }, ...Object.fromEntries(r.map((x, i) => ['rb' + i, { ...bar(i, x.b), opacity: 1 }])) } },
      { id: 'diff', caption: `${fmt(A)} − ${fmt(B)} = ${fmt(D)}：${d.diffLabel} ${fmt(D)} ${unit}`,
        set: { ...Object.fromEntries(r.flatMap((_, i) => [['fa' + i, { opacity: 0, x: .6, y: .25, scale: .6 }], ['fb' + i, { opacity: 0, x: .7, y: .5, scale: .6 }]])), ...Object.fromEntries([...Array(r.length - 1).keys()].flatMap(k => [['pa' + k, { opacity: 0 }], ['pb' + k, { opacity: 0 }]])),
          sa: { opacity: 0, y: .2 }, sb: { opacity: 0, y: .44 },
          eA: { from: { x: .55, y: .3, scale: .6 }, x: .54, y: .34, w: .1, text: fmt(A) }, eM: { x: .645, y: .34, w: .05, text: '−' }, eB: { from: { x: .55, y: .54, scale: .6 }, x: .695, y: .34, w: .1, text: fmt(B) }, eQ: { x: .795, y: .34, w: .05, text: '=' }, eR: { x: .845, y: .34, w: .12, count: D, from: { count: 0 }, cls: { 'is-risk': D > 0 } } } },
      { id: 'rows', caption: `逐组核对：${nz.map(([v, i]) => `${r[i].name} ${fmt(v)}`).join('，')}，合计 ${fmt(sum(nz.map(([v]) => v)))} ${unit}`, order: r.map((_, i) => 'd' + i),
        set: { ...Object.fromEntries(r.map((x, i) => ['d' + i, { from: { x: colX.d + .04 }, x: colX.d, y: rowY(i), w: cellW, count: x.a - x.b, cls: { 'is-risk': x.a !== x.b } }])), ...Object.fromEntries(r.filter(x => x.a > x.b).map(x => ['rg' + r.indexOf(x), { opacity: 1 }])), ...Object.fromEntries(r.map((x, i) => x.a === x.b ? ['n' + i, { opacity: .45 }] : ['n' + i, { cls: { 'is-risk': true } }])),
          check: { from: { y: .66 }, x: .55, y: .6, w: .4, text: `${nz.map(([v]) => fmt(v)).join(' + ')} = ${fmt(sum(nz.map(([v]) => v)))} ✓ 与总数一致` } } },
    ];
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? 4 }), [[fmt(A), `${d.aLabel}（${unit}）`], [fmt(B), `${d.bLabel}（${unit}）`], [fmt(D), `${d.diffLabel}（${unit}）`, D > 0]]);
  }

  /* ---------- timeline: a playhead walks the quarters; bars grow as it passes; the milestone quarter is banded ----------
     data: { min, max (quarter indices, [min,max) as KZGantt), tasks: [{id,label,start,end,department}], milestone: {at, label} } */
  function timeline(root, d, opt) {
    const cv = frame(root, 'timeline', d.note), L = S().layout, t = d.tasks, ql = q => `${Math.floor(q / 4)}Q${q % 4 + 1}`;
    const cam = cv, x = L.scale([d.min, d.max], [.27, .94]), rows = L.rows(t.length, { box: [0, .2, 1, .62], gap: .3 });
    const qs = []; for (let q = d.min; q < d.max; q++) qs.push(q);
    qs.forEach((q, i) => { const n = obj(cam, 'q' + i, 'kz-demo-tick'); n.textContent = ql(q); });
    t.forEach((k, i) => { obj(cam, 'tl' + i, 'kz-demo-label is-left', k.label); obj(cam, 'tb' + i, 'kz-demo-bar is-' + (k.department || 'medical')); glyph(obj(cam, 'tc' + i, 'kz-demo-done'), 'check', '✓'); });
    obj(cam, 'band', 'kz-demo-band'); obj(cam, 'head', 'kz-demo-playhead'); obj(cam, 'flag', 'kz-demo-flag');
    const base = { head: { x: x(d.min), y: .14, w: .004, h: .72, opacity: 0 } };
    qs.forEach((q, i) => { base['q' + i] = { x: x(q), y: .08, w: x(q + 1) - x(q) }; });
    // ticks, band and flag wait hidden: a task ending after the axis never gets its tick, a plan without a milestone no band
    t.forEach((k, i) => { base['tl' + i] = { x: .01, y: rows[i].y, w: .25 }; base['tb' + i] = { x: x(k.start), y: rows[i].y, w: 0, h: rows[i].h, opacity: 0 }; base['tc' + i] = { opacity: 0 }; });
    base.band = { opacity: 0 }; base.flag = { opacity: 0 };
    const scenes = [{ id: 'plan', caption: `计划从 ${ql(d.min)} 到 ${ql(d.max - 1)}，共 ${t.length} 项任务`, set: base }];
    qs.forEach((q, qi) => {
      const started = t.filter(k => k.start === q).map(k => k.label), done = t.filter(k => k.end === q + 1).map(k => k.label), set = { head: { x: x(q + 1), opacity: 1 } };
      t.forEach((k, i) => { if (k.start <= q) { set['tb' + i] = { w: x(Math.min(q + 1, k.end)) - x(k.start), opacity: 1 }; if (k.end === q + 1) set['tc' + i] = { x: x(k.end) + .006, y: rows[i].y, w: .03, opacity: 1 }; } });
      // what finished is named; what started is counted, so the sentence stays one line
      const parts = [done.length && `完成${done.join('、')}`, started.length && (done.length ? `${started.length} 项开始` : `开始${started.join('、')}`)].filter(Boolean);
      scenes.push({ id: ql(q), caption: `${ql(q)}：${parts.join('；') || '各项继续推进'}`, set, order: ['head', ...t.map((_, i) => 'tb' + i)] });
    });
    if (d.milestone) {
      // the milestone quarter: a band sweeps open over its column, its axis label lights, the flag sits under the band
      const at = d.milestone.at, mt = t.map((k, i) => [k, i]).filter(([k]) => k.end === at + 1);
      scenes.push({ id: 'milestone', caption: d.milestone.label, order: ['band', 'head', 'flag'], set: { band: { from: { x: x(at), y: .14, w: 0, h: .72 }, x: x(at), y: .14, w: x(at + 1) - x(at), h: .72, opacity: 1 }, head: { opacity: 0 }, ['q' + qs.indexOf(at)]: { cls: { 'is-on': true } }, flag: { from: { x: x(at), y: .92, opacity: 0 }, x: x(at), y: .87, w: x(at + 1) - x(at), opacity: 1, text: `★ ${d.milestone.flag || '里程碑'}` },
        ...Object.fromEntries(t.map((k, i) => mt.some(([, j]) => j === i) ? ['tl' + i, { cls: { 'is-on': true } }] : ['tb' + i, { opacity: .4 }])) } });
    }
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? scenes.length - 1 }), [[String(t.length), '任务'], [`${ql(d.min)}–${ql(d.max - 1)}`, '计划区间'], ...(d.milestone ? [[ql(d.milestone.at), d.milestone.flag || '里程碑']] : [])]);
  }

  /* ---------- decision: example cases walk a rule path; outcomes count up ----------
     data: { nodes: [{id,label,x,y,w,h?,kind:'q'|'out'|'in'}], edges: [{from,to,label}], cases: [{id,label,detail,path:[nodeId…]}], intro, summary } */
  function decision(root, d, opt) {
    const cv = frame(root, 'decision', d.note), N = new Map(d.nodes.map(n => [n.id, n]));
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'kz-demo-links'); svg.setAttribute('viewBox', '0 0 1000 1000'); svg.setAttribute('preserveAspectRatio', 'none'); cv.append(svg);
    const H = n => n.h || .1, out = n => [n.x + n.w, n.y + H(n) / 2], inn = n => [n.x, n.y + H(n) / 2];
    d.edges.forEach((e, i) => { const p = document.createElementNS(svg.namespaceURI, 'path'); const a = out(N.get(e.from)), b = inn(N.get(e.to)), mx = (a[0] + b[0]) / 2;
      p.setAttribute('d', `M${a[0] * 1000} ${a[1] * 1000} C${mx * 1000} ${a[1] * 1000} ${mx * 1000} ${b[1] * 1000} ${b[0] * 1000} ${b[1] * 1000}`); p.setAttribute('vector-effect', 'non-scaling-stroke'); p.dataset.kzObj = 'e' + i; svg.append(p);
      if (e.label) obj(cv, 'el' + i, 'kz-demo-edge', e.label); });
    d.nodes.forEach(n => lead(obj(cv, 'n_' + n.id, 'kz-demo-node is-' + (n.kind || 'q'), n.label), n.icon));
    d.nodes.filter(n => n.kind === 'out').forEach(n => obj(cv, 'k_' + n.id, 'kz-demo-count'));
    d.cases.forEach((k, i) => obj(cv, 'c' + i, 'kz-demo-case', k.label));
    const base = {};
    d.nodes.forEach(n => { base['n_' + n.id] = { x: n.x, y: n.y, w: n.w, h: H(n) }; if (n.kind === 'out') base['k_' + n.id] = { x: n.x + n.w - .1, y: n.y - .075, w: .1, count: 0, unit: ' 例' }; });
    d.edges.forEach((e, i) => { base['e' + i] = { draw: 1, stroke: MUTE }; if (e.label) { const a = out(N.get(e.from)), b = inn(N.get(e.to)); base['el' + i] = { x: (a[0] + b[0]) / 2 - .04, y: (a[1] + b[1]) / 2 - .025, w: .08 }; } });
    const start = N.get(d.cases[0].path[0]), counts = {};
    const scenes = [{ id: 'rules', caption: d.intro || '先看判定路径', set: base }];
    d.cases.forEach((k, i) => {
      const end = N.get(k.path.at(-1)); counts[end.id] = (counts[end.id] || 0) + 1;
      const lit = {}; d.edges.forEach((e, j) => { const on = k.path.some((p, q) => p === e.from && k.path[q + 1] === e.to); lit['e' + j] = { stroke: on ? C('brand') : MUTE }; });
      // the token rides the rule path (via the questions) and parks under its outcome
      scenes.push({ id: k.id, caption: `${k.label}：${k.detail} → ${end.label}`, order: ['c' + i],
        set: { ...lit, ['c' + i]: { from: { x: start.x, y: start.y + H(start) + .02, opacity: 0 }, x: end.x + end.w - .12 - (counts[end.id] - 1) * .13, y: end.y + H(end) + .03, w: .12, via: k.path.slice(1, -1).map(p => [N.get(p).x, N.get(p).y + H(N.get(p)) + .02]) }, ['k_' + end.id]: { count: counts[end.id], cls: { 'is-on': true } }, ['n_' + end.id]: { cls: { 'is-on': true } } } });
    });
    if (d.summary) scenes.push({ id: 'summary', caption: d.summary, set: Object.fromEntries(d.edges.map((e, j) => ['e' + j, { stroke: MUTE }])) });
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? scenes.length - 1 }), d.nodes.filter(n => n.kind === 'out').map(n => [String(counts[n.id] || 0), n.label]));
  }

  /* ---------- story: one data set re-encoded scene by scene on a fixed scale ----------
     data: { unit, groups: [{name, a, b}], aLabel, bLabel, gapLabel, takeaway } — bars, gaps, sort, stack */
  function story(root, d, opt) {
    const cv = frame(root, 'story', d.note), L = S().layout, g = d.groups, unit = d.unit || '';
    const A = sum(g.map(x => x.a)), B = sum(g.map(x => x.b)), max = A, box = [.06, .1, .6, .74], n = g.length;
    obj(cv, 'axis', 'kz-demo-axis');
    g.forEach((x, i) => { obj(cv, 'ba' + i, 'kz-demo-bar is-comparator'); obj(cv, 'bb' + i, 'kz-demo-bar'); obj(cv, 'lb' + i, 'kz-demo-label'); obj(cv, 'va' + i, 'kz-demo-count'); if (x.a > x.b) { obj(cv, 'bg' + i, 'kz-demo-bar is-gap'); obj(cv, 'vg' + i, 'kz-demo-count is-risk'); } });
    obj(cv, 'note', 'kz-demo-callout'); obj(cv, 'tot', 'kz-demo-figure');
    const at = (order) => { const ra = L.bars(order.map(i => g[i].a), { box, max }), rb = L.bars(order.map(i => g[i].b), { box, max }); const m = {}; order.forEach((gi, k) => { m[gi] = { a: ra[k], b: rb[k] }; }); return m; };
    const idx = g.map((_, i) => i), P = at(idx), sorted = [...idx].sort((p, q) => (g[q].a - g[q].b) - (g[p].a - g[p].b) || p - q), Q = at(sorted);
    const lbl = (M, i) => ({ x: M[i].a.x - .02, y: box[1] + box[3] + .02, w: M[i].a.w + .04, text: g[i].name });
    const base = { axis: { x: box[0], y: box[1] + box[3], w: box[2], h: .004 } };
    g.forEach((x, i) => Object.assign(base, { ['ba' + i]: { ...P[i].a, from: { ...P[i].a, y: box[1] + box[3], h: 0 } }, ['lb' + i]: lbl(P, i), ['va' + i]: { x: P[i].a.x - .02, y: P[i].a.y - .065, w: P[i].a.w + .04, text: fmt(x.a) } }));
    const gapState = (M, i) => ({ x: M[i].a.x, y: M[i].a.y, w: M[i].a.w, h: M[i].b.y - M[i].a.y });
    const worst = sorted.filter(i => g[i].a > g[i].b), has = id => !!cv.querySelector(`[data-kz-obj="${id}"]`);
    const scenes = [
      { id: 'due', caption: `${d.aLabel}：${g.map(x => `${x.name} ${fmt(x.a)}`).join('，')}`, set: base },
      { id: 'recv', caption: `${d.bLabel}叠上去：同一刻度，${d.bLabel}合计 ${fmt(B)} ${unit}`, order: idx.map(i => 'bb' + i), set: Object.fromEntries(g.map((x, i) => ['bb' + i, { ...P[i].b, from: { ...P[i].b, y: box[1] + box[3], h: 0 } }])) },
      { id: 'gap', caption: `差额标红：${worst.map(i => `${g[i].name}缺 ${fmt(g[i].a - g[i].b)}`).join('，')}`, set: Object.fromEntries(g.flatMap((x, i) => x.a > x.b ? [['va' + i, { opacity: 0 }], ['bg' + i, gapState(P, i)], ['vg' + i, { x: P[i].a.x - .02, y: P[i].a.y - .07, w: P[i].a.w + .04, count: x.a - x.b }]] : [['ba' + i, { opacity: .5 }], ['bb' + i, { opacity: .5 }]])) },
      { id: 'sort', caption: `按缺口从大到小重排：${worst.map(i => g[i].name).join('、')}在前`, order: sorted.flatMap(i => ['ba' + i, 'bb' + i, 'bg' + i, 'lb' + i, 'vg' + i]).filter(has),
        set: Object.fromEntries(g.flatMap((x, i) => [['ba' + i, { x: Q[i].a.x }], ['bb' + i, { x: Q[i].b.x }], ['lb' + i, { x: Q[i].a.x - .02 }], ['va' + i, { x: Q[i].a.x - .02 }], ...(x.a > x.b ? [['bg' + i, { x: Q[i].a.x }], ['vg' + i, { x: Q[i].a.x - .02 }]] : [])])) },
      { id: 'stack', caption: d.takeaway || `${d.aLabel} ${fmt(A)}，${d.bLabel} ${fmt(B)}，${d.gapLabel} ${fmt(A - B)} ${unit}`, order: sorted.flatMap(i => ['ba' + i, 'bb' + i, 'bg' + i]).filter(has),
        set: (() => { const o = {}; let ya = box[1] + box[3], yb = ya; const W = .16, X = .66;
          // stacked totals on the same scale: each group's bar travels right and lands on the stack
          sorted.forEach(i => { const ha = box[3] * g[i].a / max, hb = box[3] * g[i].b / max; ya -= ha; yb -= hb;
            // each group's name travels with its bar and labels its segment of the stack
            o['ba' + i] = { x: X, y: ya, w: W, opacity: 1 }; o['bb' + i] = { x: X, y: yb, w: W, opacity: 1 }; o['va' + i] = { opacity: 0 }; o['lb' + i] = { x: X + W + .015, y: ya + ha / 2 - .022, w: .15, text: `${g[i].name} ${fmt(g[i].a)}`, cls: { 'is-start': true } };
            if (g[i].a > g[i].b) { o['bg' + i] = { opacity: 0 }; o['vg' + i] = { opacity: 0 }; } });
          o.tot = { from: { x: X - .06, y: box[1] - .1, opacity: 0 }, x: X - .06, y: box[1] - .1, w: W + .12, text: `${fmt(B)} / ${fmt(A)} ${unit}` };
          o.note = { from: { x: X - .2, opacity: 0 }, x: X - .3, y: box[1] + .1, w: .26, text: `${d.gapLabel} ${fmt(A - B)} ${unit}`, cls: { 'is-risk': true } }; return o; })() },
    ];
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? 2 }), [[fmt(A), `${d.aLabel}（${unit}）`], [fmt(B), `${d.bLabel}（${unit}）`], [fmt(A - B), `${d.gapLabel}（${unit}）`, A > B]]);
  }

  /* ---------- compare: two versions slide together, rows align, matching rows lock, differences go to a tray ----------
     data: { left, right, leftTag?, rightTag? (short names in the tray), rows: [{label, left, right}], rightOrder?: [row index → slot in the right version], tray }
     A row matches when its two values are identical; the verdicts and counts are computed from the values. */
  function compare(root, d, opt) {
    const cv = frame(root, 'compare', d.note), r = d.rows, L = S().layout, n = r.length;
    const row = (id, label, value) => { const e = obj(cv, id, 'kz-demo-row'), k = el('span', 'kz-demo-row-k', label); k.dataset.kzObjText = ''; e.append(k, el('span', 'kz-demo-row-v', value)); };
    ['L', 'R'].forEach(s => { obj(cv, 'doc' + s, 'kz-demo-doc'); lead(obj(cv, 'ttl' + s, 'kz-demo-head', s === 'L' ? d.left : d.right), 'doc'); });
    r.forEach((x, i) => { row('rl' + i, x.label, x.left); row('rr' + i, x.label, x.right); lead(obj(cv, 'mk' + i, 'kz-demo-mark-sign', x.left === x.right ? '一致' : '有差异'), x.left === x.right ? 'check' : 'cross'); });
    const diff = r.map((x, i) => [x, i]).filter(([x]) => x.left !== x.right);
    diff.forEach((_, k) => obj(cv, 'dk' + k, 'kz-demo-tray-k'));
    lead(obj(cv, 'tray', 'kz-demo-tray'), 'flag');
    // geometry: two documents and a verdict gutter between them; the destination list holds the right third from the
    // start (empty), so the stage reads as source → check → destination. The right version opens in its own order.
    const DW = .3, docY = .06, docH = .84, slot = L.rows(n, { box: [0, .19, 1, .67], gap: .2 }), at = d.rightOrder || r.map((_, i) => i);
    const doc = X => ({ x: X, y: docY, w: DW, h: docH }), cell = (X, k) => ({ x: X + .015, y: slot[k].y, w: DW - .03, h: slot[k].h });
    const Lx = .02, Rx = .4, gut = { x: Lx + DW, w: Rx - Lx - DW }, T = { x: .72, y: docY, w: .26, h: docH }, shuffled = at.some((v, i) => v !== i);
    const base = { docL: doc(Lx), docR: doc(Rx), ttlL: { x: Lx + .015, y: docY + .03, w: DW - .03 }, ttlR: { x: Rx + .015, y: docY + .03, w: DW - .03 }, tray: { ...T, text: `${d.tray} · 0 条` } };
    r.forEach((x, i) => { base['rl' + i] = cell(Lx, i); base['rr' + i] = cell(Rx, at[i]); });
    const near = {}; r.forEach((x, i) => { near['rr' + i] = cell(Rx, i); });
    const bh = Math.min(.29, (docH - .1) / Math.max(1, diff.length)), rh = (bh - .085) / 2;
    const scenes = [
      { id: 'two', caption: `${d.left} 与 ${d.right} 两版并排${shuffled ? `，${d.right} 的条目顺序不同` : ''}`, set: base },
      { id: 'align', caption: `按条目对齐，共 ${n} 条`, order: r.map((_, i) => 'rr' + i), set: near },
      { id: 'match', caption: `一致的 ${n - diff.length} 条锁定，${diff.length} 条取值不同`, set: Object.fromEntries(r.flatMap((x, i) => [['mk' + i, { x: gut.x, y: slot[i].y + slot[i].h / 2 - .025, w: gut.w, cls: { 'is-diff': x.left !== x.right } }],
        ...(x.left === x.right ? [['rl' + i, { opacity: .45 }], ['rr' + i, { opacity: .45 }]] : [['rl' + i, { cls: { 'is-diff': true } }], ['rr' + i, { cls: { 'is-diff': true } }]])])) },
      { id: 'pull', caption: `${diff.length} 条差异移入${d.tray}清单，两版取值并列`, order: ['tray', ...diff.flatMap(([, i], k) => ['dk' + k, 'rl' + i, 'rr' + i])],
        set: { tray: { text: `${d.tray} · ${diff.length} 条` },
          ...Object.fromEntries(diff.flatMap(([x, i], k) => { const y = T.y + .1 + k * bh;
            return [['dk' + k, { from: { x: T.x + .015, y, opacity: 0 }, x: T.x + .015, y, w: T.w - .03, text: x.label }],
              ['rl' + i, { x: T.x + .015, y: y + .065, w: T.w - .03, h: rh, text: d.leftTag || d.left }], ['rr' + i, { x: T.x + .015, y: y + .075 + rh, w: T.w - .03, h: rh, text: d.rightTag || d.right }], ['mk' + i, { opacity: 0 }]]; })) } },
    ];
    return facts(S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? scenes.length - 1 }), [[String(n), '对比条目'], [String(n - diff.length), '一致'], [String(diff.length), d.tray, diff.length > 0]]);
  }

  const FORMS = { units, calc, timeline, decision, story, compare };
  // Building blocks shared with further forms (kz-demo-patterns.js, project-specific forms): one frame, one object
  // model, icons (kz-icons.js) and a canvas-wide SVG layer for links in 0–1000 units (non-scaling strokes).
  const kit = {
    S, C, MUTE, SOFT, sum, fmt, el, obj, frame, lead, glyph,
    icon(cv, id, name, cls) { const n = obj(cv, id, 'kz-demo-icon ' + (cls || '')); n.append(global.KZIcons.svg(name)); return n; },
    links(cv) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'kz-demo-links'); svg.setAttribute('viewBox', '0 0 1000 1000'); svg.setAttribute('preserveAspectRatio', 'none'); cv.append(svg);
      return { svg, path(id, d, cls) { const p = document.createElementNS(svg.namespaceURI, 'path'); p.setAttribute('d', d); p.setAttribute('vector-effect', 'non-scaling-stroke'); if (cls) p.setAttribute('class', cls); if (id) p.dataset.kzObj = id; svg.append(p); return p; } };
    },
    pts: list => list.map(([x, y], i) => `${i ? 'L' : 'M'}${(x * 1000).toFixed(1)} ${(y * 1000).toFixed(1)}`).join(' ')
  };
  // Fact strip for the stacked layout (15 DEMO-05): facts a form computed from its data, as KPI chips.
  function renderFacts(container, stage) {
    if (!container || !stage || !stage.facts) return;
    container.replaceChildren(...stage.facts.map(f => { const d = el('div', 'kz-demo-fact' + (f.risk ? ' is-risk' : '')); d.append(el('b', null, f.value), el('span', null, f.label)); return d; }));
  }
  global.KZDemo = {
    mount(root, kind, data, opt = {}) { if (!FORMS[kind]) throw Error('未知演示形式：' + kind); return FORMS[kind](root, data, opt); },
    define(kind, fn) { if (FORMS[kind]) throw Error('演示形式已存在：' + kind); if (typeof fn !== 'function') throw Error('演示形式需要一个函数'); FORMS[kind] = fn; },
    get forms() { return Object.keys(FORMS); },
    kit, renderFacts
  };
})(window);
