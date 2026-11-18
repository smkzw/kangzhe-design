/* Kangzhe 8.0 — clinical-report scenario forms (15 DEMO-02) on KZDemo.kit. Each scenario family has one data contract
   shared by its static page template (tools/kz_layouts …/scenarios.py), this regular demo form and the flagship stage
   (kz-flagship-stages.js); the checks below mirror tools/kz_layouts/diagram_clinical.py so every product rejects the
   same contradictions. Every number and caption is computed from the data (DEMO-04).
     safety   safety overview: the analysis set (N per arm) → the overall TEAE row → TEAE splits into its sub-categories
              (the child bars peel out of the parent bar) → the remaining categories → differences (pp) to the ledger,
              the flagged ones lit → the focus category
     exposure exposure summary: groups on empty tracks → the first band grows → longer bands fill in deeper → totals against
              the targets → the focus group
     efficacy efficacy summary: endpoints with each arm's value → the continuous section's differences and 95% CIs → the binary
              section → the endpoints whose CI crosses 0 → the focus endpoint
     soa      schedule of assessments: visit columns under their periods → per section a dot per visit sized by its item count
              → the load per visit → the focus item's visits
     program  clinical development plan (Gantt + milestones): lanes on the quarter axis → phases laid out → the today line
              turns what is ahead into plan → milestones pin onto the bars → the focus
   Requires kz-clinical.js (the shared contracts), kz-scenes.js, kz-demo.js and kz-icons.js. Styles: kz-glass.css "Demo stages". */
(function (global) {
  'use strict';
  const K = () => global.KZDemo.kit, def = (kind, fn) => global.KZDemo.define(kind, fn);
  const need = (ok, msg) => { if (!ok) throw Error(msg); };
  const num = (v, d = 0) => Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const over = (base, ch) => { const o = { ...base }; for (const k in ch) o[k] = { ...base[k], ...ch[k] }; return o; };
  const mount = (root, scenes, opt, staticScene, facts) => { const s = K().S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? staticScene }); s.facts = facts; return s; };
  // capacity guard (15 DEMO-03): `check(H)` returns how many places do not fit at stage height H px (0 = fits). The stage is
  // often laid out after mount (a deck page entering), so it runs whenever the canvas gets a size; a misfit logs one
  // console error with the remedy and marks the canvas data-kz-fit="overflow"
  const fitGuard = (cv, stage, check, msg) => { let said = '';
    const run = () => { const H = cv.getBoundingClientRect().height; if (!(H > 0)) return; const bad = check(H);
      if (!bad) { delete cv.dataset.kzFit; return; } cv.dataset.kzFit = 'overflow'; const m = msg(H, bad); if (m !== said) { said = m; console.error(m); } };
    if (global.ResizeObserver) { const ro = new ResizeObserver(() => requestAnimationFrame(run)); ro.observe(cv); const d0 = stage.dispose?.bind(stage); if (d0) stage.dispose = (...a) => { ro.disconnect(); return d0(...a); }; }
    run(); return stage; };
  // text line boxes of different objects that intersect (more than 2 px both ways)
  const textClash = els => { const L = []; els.forEach((el, k) => { if (!el) return; const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const r = document.createRange(); r.selectNodeContents(n); for (const b of r.getClientRects()) if (b.width > 1) L.push([k, b]); } });
    let c = 0; for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) { const [ka, A] = L[i], [kb, B] = L[j];
      if (ka !== kb && Math.min(A.right, B.right) - Math.max(A.left, B.left) > 2 && Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top) > 2) c++; } return c; };

  const C = () => { if (!global.KZClinical) throw Error('kz-demo-clinical.js 要在 kz-clinical.js 之后加载'); return global.KZClinical; };
  const safetyModel = d => C().safety(d), dtext = v => C().dtext(v), npct = (n, p) => C().npct(n, p);

  /* ---------- safety ----------
     data: { unit, set?, arms: [{name, n, role}], rows: [{key, label, short?, values, parent?}], focus?, flag_pp?, compare?, note }
     short is the stage name of a category (TRAE, TESAE …); the static template prints the full label
     the stage draws the two compared arms as a butterfly (treatment wing left of the spine, comparator right) */
  def('safety', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'safety', d.note), M = safetyModel(d), rows = M.rows, n = rows.length;
    const A = M.arms[M.ti], B = M.arms[M.ci], scale = [10, 20, 30, 40, 50, 60, 80, 100].find(s => s >= Math.max(...rows.flatMap(r => [r.pct[M.ti], r.pct[M.ci]]))) || 100;
    const spine = .565, wing = .16, y0 = .15, rowH = .8 / n, top = r => r.depth === 0;
    const Y = i => y0 + i * rowH, bh = r => rowH * (top(r) ? .5 : .34);
    const wl = p => Math.max(.003, p / scale * wing);
    k.obj(cv, 'hd', 'kz-demo-head', `${d.set || '安全性分析集'} · 差值 = ${A.name} − ${B.name}（百分点）`);
    k.obj(cv, 'aA', 'kz-demo-label is-strong'); k.obj(cv, 'aB', 'kz-demo-label is-strong');
    k.obj(cv, 'band', 'kz-demo-band');
    const L = k.links(cv); L.path('spine', k.pts([[spine, y0 - .02], [spine, Y(n) + .01]]), 'is-rail');
    rows.forEach((r, i) => {
      k.obj(cv, 'l' + i, 'kz-demo-label is-left' + (top(r) ? ' is-strong' : ''), r.short || r.label);
      k.obj(cv, 'bt' + i, 'kz-demo-bar'); k.obj(cv, 'bc' + i, 'kz-demo-bar is-comparator');
      k.obj(cv, 'vt' + i, 'kz-demo-count'); k.obj(cv, 'vc' + i, 'kz-demo-count'); k.obj(cv, 'd' + i, 'kz-demo-count');
    });
    const geo = (r, i) => ({ t: { x: spine - .004 - wl(r.pct[M.ti]), y: Y(i) + (rowH - bh(r)) / 2, w: wl(r.pct[M.ti]), h: bh(r) },
      c: { x: spine + .004, y: Y(i) + (rowH - bh(r)) / 2, w: wl(r.pct[M.ci]), h: bh(r) } });
    const base = { hd: { x: .01, y: .015, w: .9 }, aA: { x: .245, y: .07, w: .3, text: `${A.name}（N = ${A.n}）`, opacity: 0 },
      aB: { x: .58, y: .07, w: .3, text: `${B.name}（N = ${B.n}）`, opacity: 0 }, band: { x: .005, y: y0, w: .99, h: rowH, opacity: 0 }, spine: { draw: 0 } };
    rows.forEach((r, i) => {
      const cy = Y(i) + rowH / 2 - .028;
      Object.assign(base, {
        ['l' + i]: { x: .01 + .018 * r.depth, y: cy, w: .215 - .018 * r.depth, opacity: .3 },
        ['bt' + i]: { x: spine - .004, y: Y(i) + (rowH - bh(r)) / 2, w: .003, h: bh(r), opacity: 0 },
        ['bc' + i]: { x: spine + .004, y: Y(i) + (rowH - bh(r)) / 2, w: .003, h: bh(r), opacity: 0 },
        ['vt' + i]: { x: .25, y: cy, w: .14, opacity: 0, text: npct(r.values[M.ti], r.pct[M.ti]) },
        ['vc' + i]: { x: .73, y: cy, w: .14, opacity: 0, text: npct(r.values[M.ci], r.pct[M.ci]) },
        ['d' + i]: { x: .73, y: cy, w: .14, opacity: 0, text: dtext(r.diff) } });
    });
    const show = (i, from) => { const g = geo(rows[i], i);
      return [['bt' + i, { ...(from ? { from: { ...from.t, opacity: 1 } } : {}), ...g.t, opacity: 1 }], ['bc' + i, { ...(from ? { from: { ...from.c, opacity: 1 } } : {}), ...g.c, opacity: 1 }],
        ['vt' + i, { opacity: 1 }], ['vc' + i, { opacity: 1 }], ['l' + i, { opacity: 1 }]]; };
    const cas = rows.map((r, i) => i).filter(i => i > 0 && M.under(rows[i])), rest = rows.map((r, i) => i).filter(i => i > 0 && !M.under(rows[i]));
    const g0 = geo(rows[0], 0), flagged = rows.map((r, i) => i).filter(i => rows[i].diff >= M.flag);
    const big = rows.map((r, i) => i).sort((a, b) => rows[b].diff - rows[a].diff)[0], fi = M.focus ? rows.findIndex(r => r.key === M.focus) : big;
    const nm = i => rows[i].short || rows[i].label;
    const lst = ids => ids.map(i => `${nm(i)} ${num(rows[i].pct[M.ti], 1)}% 对 ${num(rows[i].pct[M.ci], 1)}%`).join('；');
    const scenes = [
      { id: 'set', caption: `${d.set || '安全性分析集'}：${A.name} ${A.n} ${M.unit}、${B.name} ${B.n} ${M.unit}，按事件类别逐行比较`,
        set: over(base, { aA: { opacity: 1, text: `${A.name}（N = ${A.n}）` }, aB: { opacity: 1 }, spine: { draw: 1 } }) },
      { id: 'overall', caption: `${rows[0].label}：${num(rows[0].pct[M.ti], 1)}% 对 ${num(rows[0].pct[M.ci], 1)}%`, set: Object.fromEntries(show(0)) },
      { id: 'cascade', caption: cas.length ? `${rows[0].label}拆开：${lst(cas.filter(i => rows[i].depth === 1))}` : `${rows[0].label}没有下级类别`,
        order: cas.flatMap(i => ['bt' + i, 'bc' + i]),
        set: { ...Object.fromEntries(cas.flatMap(i => show(i, g0))), ['bt0']: { opacity: .55 }, ['bc0']: { opacity: .55 } } },
      { id: 'rest', caption: rest.length ? `其余类别：${lst(rest.filter(i => rows[i].depth === 0))}` : '没有其余类别', order: rest.flatMap(i => ['bt' + i, 'bc' + i]),
        set: { ...Object.fromEntries(rest.flatMap(i => show(i))), ['bt0']: { opacity: 1 }, ['bc0']: { opacity: 1 } } },
      { id: 'diff', caption: flagged.length ? `差值 ≥ ${M.flag} 个百分点的 ${flagged.length} 项标红，最大是 ${nm(big)} ${dtext(rows[big].diff)}` : `各类别差值都在 ${M.flag} 个百分点以内`,
        order: rows.map((_, i) => 'd' + i),
        set: Object.fromEntries(rows.map((r, i) => ['d' + i, { x: .89, w: .1, opacity: 1, cls: { 'is-risk': r.diff >= M.flag }, scale: r.diff >= M.flag ? 1.08 : 1 }])) },
      { id: 'focus', caption: `重点看${rows[fi].label}：${num(rows[fi].pct[M.ti], 1)}% 对 ${num(rows[fi].pct[M.ci], 1)}%，差 ${num(Math.abs(rows[fi].diff), 1)} 个百分点`,
        set: { band: { opacity: 1, y: Y(fi) }, ...Object.fromEntries(rows.flatMap((r, i) => i === fi ? [['l' + i, { cls: { 'is-strong': true } }], ['vt' + i, { scale: 1.06 }], ['vc' + i, { scale: 1.06 }]]
          : [['bt' + i, { opacity: .35 }], ['bc' + i, { opacity: .35 }], ['vt' + i, { opacity: .45 }], ['vc' + i, { opacity: .45 }], ['d' + i, { opacity: .45 }], ['l' + i, { opacity: .55 }]])) } },
    ];
    return mount(root, scenes, opt, 5, [
      { value: `${num(rows[0].pct[M.ti], 1)}%`, label: `${rows[0].label}（${A.name}）` }, { value: `${num(rows[0].pct[M.ci], 1)}%`, label: `${rows[0].label}（${B.name}）` },
      { value: dtext(rows[fi].diff), label: `${rows[fi].label}差值（pp）`, risk: rows[fi].diff >= M.flag }]);
  });
  /* ---------- exposure ----------
     data: the exposure-summary contract (KZClinical.exposure): { unit?, head?, bands: [{key, label}], groups: [{key, name, note?,
     values, py?}], targets?: {band: n}, target_label?, focus?, note }
     scenes: the groups on empty tracks → everyone exposed (the first band grows) → each longer band fills in from the
     left, deeper colour (a subset of the band before) → the totals add up and meet (or miss) their targets → the focus */
  def('exposure', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'exposure', d.note), M = C().exposure(d), B = M.bands, G = M.groups, n = G.length, nb = B.length;
    const ramp = (global.KZ_TOKENS?.charts?.phases) || ['#FFEAA8', '#FFD02A', '#FFA916', '#F98500', '#D96500'];
    const col = B.map((_, i) => ramp[Math.min(ramp.length - 1, 1 + Math.round(i * (ramp.length - 2) / Math.max(1, nb - 1)))]);
    const x0 = .2, x1 = .6, c0 = .62, cw = (.985 - c0) / nb, y0 = .15, rowH = .62 / n, bh = Math.min(.07, rowH * .5);
    const Y = i => y0 + i * rowH, BY = i => Y(i) + (rowH - bh) / 2, X = v => (v / M.max) * (x1 - x0), u = M.unit;
    const fmt = v => num(v), fi = M.focus ? G.findIndex(g => g.key === M.focus) : G.reduce((a, g, i) => (g.values[nb - 1] > G[a].values[nb - 1] ? i : a), 0);
    k.obj(cv, 'hd', 'kz-demo-head', `${d.head || '适应症 / 研究'} · 累计暴露时长档（长档是短档的子集）`); k.obj(cv, 'band', 'kz-demo-band');
    const base = { hd: { x: .01, y: .015, w: .6 }, band: { x: .005, y: y0, w: .99, h: rowH, opacity: 0 } };
    B.forEach((b, j) => { const g = k.obj(cv, 'bh' + j, 'kz-demo-legend', b.label); g.style.setProperty('--sw', col[j]); base['bh' + j] = { x: c0 + j * cw, y: .08, w: cw, opacity: 0 }; });
    G.forEach((g, i) => {
      const l = k.obj(cv, 'gn' + i, 'kz-demo-lane-name'); l.innerHTML = ''; const b = document.createElement('b'); b.textContent = g.name; l.append(b);
      if (g.note) { const sm = document.createElement('small'); sm.textContent = g.note; l.append(sm); }
      base['gn' + i] = { x: .01, y: Y(i) + rowH / 2 - .045, w: .18, h: .09, opacity: 0 };
      k.obj(cv, 'tr' + i, 'kz-demo-bar is-track'); base['tr' + i] = { x: x0, y: BY(i), w: x1 - x0, h: bh, opacity: 0 };
      B.forEach((_, j) => {
        k.obj(cv, `e${i}_${j}`, 'kz-demo-bar is-phase'); base[`e${i}_${j}`] = { x: x0, y: BY(i), w: .002, h: bh, opacity: 0, fill: col[j] };
        k.obj(cv, `v${i}_${j}`, 'kz-demo-count'); base[`v${i}_${j}`] = { x: c0 + j * cw, y: Y(i) + rowH / 2 - .028, w: cw - .01, opacity: 0, text: fmt(g.values[j]) };
      });
    });
    const ty = Y(n) + .03;
    k.obj(cv, 'tl', 'kz-demo-label is-left is-strong', `合计（${u}）`); base.tl = { x: .01, y: ty, w: .18, opacity: 0 };
    k.obj(cv, 'trule', 'kz-demo-grid'); base.trule = { x: .01, y: ty - .012, w: .975, h: .002, opacity: 0 };
    B.forEach((_, j) => {
      k.obj(cv, 'tt' + j, 'kz-demo-count'); base['tt' + j] = { x: c0 + j * cw, y: ty, w: cw - .01, opacity: 0, text: fmt(M.totals[j]) };
      if (M.targets[j] != null) { k.obj(cv, 'tg' + j, 'kz-demo-note'); base['tg' + j] = { x: c0 + j * cw, y: ty + .07, w: cw - .01, opacity: 0, text: `目标 ≥${fmt(M.targets[j])}` }; }
    });
    const grow = j => Object.fromEntries(G.flatMap((g, i) => [[`e${i}_${j}`, { w: Math.max(.002, X(g.values[j])), opacity: g.values[j] ? 1 : 0 }], [`v${i}_${j}`, { opacity: 1 }]]));
    const zero = j => G.filter(g => !g.values[j]).map(g => g.name);
    const miss = B.map((b, j) => (M.met[j] === false ? `${b.label}差 ${fmt(M.targets[j] - M.totals[j])}` : null)).filter(Boolean);
    const hasT = M.targets.some(t => t != null), F0 = G[fi];
    const scenes = [
      { id: 'groups', caption: `${n} 个${d.head ? d.head.split(' ')[0] : '组'}，按 ${nb} 个累计暴露时长档统计（${B.map(b => b.label).join('、')}）`,
        set: over(base, { hd: { opacity: 1 }, ...Object.fromEntries(Object.keys(base).filter(id => /^(gn|tr|bh)/.test(id)).map(id => [id, { opacity: 1 }])) }) },
      { id: 'any', caption: `${B[0].label}共 ${fmt(M.totals[0])} ${u}，最多：${G.reduce((a, g) => (g.values[0] > a.values[0] ? g : a)).name} ${fmt(Math.max(...G.map(g => g.values[0])))} ${u}`,
        order: G.map((_, i) => `e${i}_0`), set: grow(0) },
      ...B.slice(1).map((b, j0) => { const j = j0 + 1, z = zero(j);
        return { id: 'band' + j, caption: `${b.label} ${fmt(M.totals[j])} ${u}（占${B[0].label}的 ${num(M.totals[j] / Math.max(1, M.totals[0]) * 100, 0)}%）` + (z.length ? `；${z.join('、')}还没有` : ''),
          order: G.map((_, i) => `e${i}_${j}`), set: grow(j) }; }),
      { id: 'total', caption: hasT ? (miss.length ? `合计对照 ${d.target_label || '目标'}：${miss.join('；')}` : `合计 ${M.totals.map((t, j) => `${B[j].label} ${fmt(t)}`).join('、')}，都达到 ${d.target_label || '目标'}`)
        : `合计 ${M.totals.map((t, j) => `${B[j].label} ${fmt(t)}`).join('、')}` + (M.py != null ? `，${fmt(Math.round(M.py))} 人年` : ''),
        order: ['trule', 'tl', ...B.map((_, j) => 'tt' + j)],
        set: { trule: { opacity: 1 }, tl: { opacity: 1 }, ...Object.fromEntries(B.flatMap((_, j) => [['tt' + j, { opacity: 1, scale: 1.06, cls: { 'is-risk': M.met[j] === false, 'is-ok': M.met[j] === true } }],
          ...(M.targets[j] != null ? [['tg' + j, { opacity: 1 }]] : [])])) } },
      { id: 'focus', caption: `重点：${F0.name}，${B.map((b, j) => `${b.label} ${fmt(F0.values[j])}`).join('、')}` + (F0.py != null ? `，${fmt(Math.round(F0.py))} 人年` : ''),
        set: { band: { opacity: 1, y: Y(fi) }, ...Object.fromEntries(G.flatMap((g, i) => i === fi ? B.map((_, j) => [`v${i}_${j}`, { scale: 1.08 }])
          : [...B.map((_, j) => [`e${i}_${j}`, { opacity: g.values[j] ? .35 : 0 }]), ...B.map((_, j) => [`v${i}_${j}`, { opacity: .45 }]), ['gn' + i, { opacity: .55 }]])) } },
    ];
    return mount(root, scenes, opt, scenes.length - 1, [
      { value: fmt(M.totals[0]), label: `${B[0].label}（${u}）` }, { value: fmt(M.totals[nb - 1]), label: `${B[nb - 1].label}（${u}）`, risk: M.met[nb - 1] === false },
      ...(M.py != null ? [{ value: fmt(Math.round(M.py)), label: '人年' }] : [])]);
  });
  /* ---------- landscape ----------
     data: the competitive-landscape contract (KZClinical.landscape): { stages?, efficacy?: {label, unit?, better, note?}, safety?: {…},
     assets: [{key, name, company?, moa?, route?, stage, efficacy?, safety?, ours?}], focus?, note }
     scenes: the assets in stage order → the stage tracks fill → efficacy bars grow and the rows re-sort by efficacy →
     safety bars grow → the focus asset (ours by default) */
  def('landscape', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'landscape', d.note), M = C().landscape(d), S0 = M.stages, ns = S0.length, AS = M.assets, n = AS.length;
    const wf = wfAt(cv);
    const PH = (global.KZ_TOKENS?.charts?.phases) || ['#FFEAA8', '#FFD02A', '#FFA916', '#F98500', '#D96500'], TREAT = global.KZ_TOKENS?.charts?.categorical?.[0] || '#D46B08';
    const COMP = global.KZ_TOKENS?.charts?.comparator || '#6E7B8C', sc = S0.map((_, i) => PH[Math.min(PH.length - 1, Math.round(i * (PH.length - 1) / Math.max(1, ns - 1)))]);
    const y0 = .17, rowH = Math.min(.105, .76 / n), bh = Math.min(.05, rowH * .42), Y = r => y0 + r * rowH, mets = Object.keys(M.metrics);
    // name column: name over company · MoA; rows too short for two lines (9–10 assets) put both on one line. The column
    // grows to the longest label (0.20–0.34 of the stage) and the stage tracks and metric bars share what is left
    const subOf = a => [a.company, a.moa].filter(Boolean).join(' · '), nmOf = a => a.name + (a.ours ? '（本品）' : '');
    const inline = rowH < .088, nh = inline ? rowH : .09;
    const lw = Math.min(.34, Math.max(.2, ...AS.map(a => (inline ? wf(nmOf(a)) + (subOf(a) ? wf(subOf(a)) * .875 : 0) : Math.max(wf(nmOf(a)), wf(subOf(a)) * .875)) + .01)));
    const sx = lw + .02, sw = .23, cw = sw / ns, m0 = sx + sw + .03, per = (.985 - m0) / Math.max(1, mets.length);
    const MX = mets.map((_, j) => m0 + j * per), MW = Math.min(.3, per - .09), byKey = Object.fromEntries(AS.map(a => [a.key, a]));
    const pos = order => Object.fromEntries(order.map((key, r) => [key, r])), base = {};
    const add = (id, cls, text, geo) => { const el = k.obj(cv, id, cls, text); base[id] = { opacity: 0, ...geo }; return el; };
    add('hd', 'kz-demo-head', `${n} 个药物 · 研发阶段 · ${mets.map(mk => M.metrics[mk].label).join(' · ')}`, { x: .01, y: .015, w: .7 });
    add('band', 'kz-demo-band', null, { x: .005, y: y0, w: .99, h: rowH });
    S0.forEach((t, i) => add('sh' + i, 'kz-demo-tick is-x', t, { x: sx + i * cw, y: .1, w: cw }));
    mets.forEach((mk, j) => { const mt = M.metrics[mk]; add('mh' + j, 'kz-demo-label is-start is-strong', `${mt.label}${mt.unit ? `（${mt.unit}）` : ''} · ${mt.better === 'higher' ? '越高越好' : '越低越好'}`, { x: MX[j], y: .1, w: per - .01 }); });
    const P0 = pos(M.order);
    AS.forEach((a, i) => {
      const r = P0[a.key], cy = Y(r) + rowH / 2, l = add('n' + i, 'kz-demo-lane-name' + (inline ? ' is-inline' : ''), null, { x: .01, y: cy - nh / 2, w: lw, h: nh }); l.innerHTML = '';
      const b = document.createElement('b'); b.textContent = nmOf(a); l.append(b);
      const sub = subOf(a); if (sub) { const sm = document.createElement('small'); sm.textContent = sub; l.append(sm); }
      S0.forEach((_, q) => add(`c${i}_${q}`, 'kz-demo-bar', null, { x: sx + q * cw + .003, y: cy - bh * .32, w: cw - .006, h: bh * .64, fill: '#EEF0F2' }));
      mets.forEach((mk, j) => {
        const v = a[mk];
        if (v == null) { add(`v${j}_${i}`, 'kz-demo-note is-start', '— 暂无数据', { x: MX[j], y: cy - .02, w: .2 }); return; }
        add(`b${j}_${i}`, 'kz-demo-bar', null, { x: MX[j], y: cy - bh / 2, w: .002, h: bh, fill: a.ours ? TREAT : COMP });
        add(`v${j}_${i}`, 'kz-demo-label is-start' + (M.best[mk] === a.key ? ' is-on' : ''), String(v), { x: MX[j] + Math.abs(v) / M.max[mk] * MW + .008, y: cy - .02, w: .06 });
      });
    });
    // moving a row moves every object of that asset to the row's y
    const move = order => { const P = pos(order); return Object.fromEntries(AS.flatMap((a, i) => { const cy = Y(P[a.key]) + rowH / 2;
      return [['n' + i, { y: cy - nh / 2 }], ...S0.map((_, q) => [`c${i}_${q}`, { y: cy - bh * .32 }]),
        ...mets.flatMap((mk, j) => [[`b${j}_${i}`, { y: cy - bh / 2 }], [`v${j}_${i}`, { y: cy - .02 }]]).filter(([id]) => base[id])]; })); };
    const merge = (...xs) => { const o = {}; for (const x of xs) for (const id in x) o[id] = { ...(o[id] || {}), ...x[id] }; return o; };
    const effOrder = mets.includes('efficacy') ? [...M.rank.efficacy, ...M.order.filter(key => !M.rank.efficacy.includes(key))] : M.order;
    const byStage = S0.map((t, q) => [t, AS.filter(a => a.si === q).map(a => a.name)]).filter(([, xs]) => xs.length).reverse();
    const grow = j => Object.fromEntries(AS.flatMap((a, i) => base[`b${j}_${i}`] ? [[`b${j}_${i}`, { w: Math.max(.004, Math.abs(a[mets[j]]) / M.max[mets[j]] * MW), opacity: 1 }], [`v${j}_${i}`, { opacity: 1 }]] : [[`v${j}_${i}`, { opacity: 1 }]]));
    const nm = key => byKey[key].name, num1 = v => (Math.round(v * 10) / 10).toString();
    const capM = j => { const mk = mets[j], mt = M.metrics[mk], r = M.rank[mk], o = M.ours, oi = o ? r.indexOf(o) : -1, u = mt.unit || '';
      return `${mt.label}：${nm(r[0])} ${num1(byKey[r[0]][mk])}${u} ${mt.better === 'higher' ? '最高' : '最低'}` + (o && oi > 0 ? `，${nm(o)} ${num1(byKey[o][mk])}${u} 排第 ${oi + 1}` : '') +
        (n - r.length ? `；${n - r.length} 个暂无数据` : ''); };
    const fa = byKey[M.focus] || AS[0], fi = AS.indexOf(fa);
    const scenes = [
      { id: 'assets', caption: `${n} 个药物按研发阶段排开：${byStage.map(([t, xs]) => `${t} ${xs.length} 个`).join('、')}`,
        set: over(base, { hd: { opacity: 1 }, ...Object.fromEntries(Object.keys(base).filter(id => /^(n|sh|mh|c)\d/.test(id) || /^(sh|mh)/.test(id)).map(id => [id, { opacity: 1 }])) }) },
      { id: 'stage', caption: byStage.map(([t, xs]) => `${t}：${xs.join('、')}`).join('；'), order: AS.map((_, i) => `c${i}_0`),
        set: Object.fromEntries(AS.flatMap((a, i) => S0.map((_, q) => [`c${i}_${q}`, q <= a.si ? { fill: sc[q], h: bh * .64 } : {}]))) },
      ...mets.map((mk, j) => j === 0 && mk === 'efficacy'
        ? { id: 'efficacy', caption: capM(j) + '，按疗效重新排序', order: AS.map((_, i) => `b0_${i}`), set: merge(grow(0), move(effOrder)) }
        : { id: mk, caption: capM(j), order: AS.map((_, i) => `b${j}_${i}`), set: grow(j) }),
      { id: 'focus', caption: `重点：${fa.name}，${fa.stage}` + mets.map(mk => fa[mk] == null ? '' : `，${M.metrics[mk].label} ${num1(fa[mk])}${M.metrics[mk].unit || ''}（第 ${M.rank[mk].indexOf(fa.key) + 1}/${M.rank[mk].length}）`).join(''),
        set: merge({ band: { opacity: 1, y: Y(effOrder.indexOf(fa.key)) } }, Object.fromEntries(AS.flatMap((a, i) => i === fi ? [] : [['n' + i, { opacity: .5 }],
          ...mets.flatMap((_, j) => [[`b${j}_${i}`, { opacity: .35 }], [`v${j}_${i}`, { opacity: .45 }]]).filter(([id]) => base[id])]))) },
    ];
    return mount(root, scenes, opt, scenes.length - 1, [
      { value: String(n), label: '药物' }, { value: String(AS.filter(a => a.si === ns - 1).length), label: `已${S0[ns - 1]}` },
      ...(M.ours && mets.length ? [{ value: `${M.rank[mets[0]].indexOf(M.ours) + 1}/${M.rank[mets[0]].length}`, label: `本品${M.metrics[mets[0]].label}排名` }] : [])]);
  });
  /* ---------- trialflow ----------
     data: the trial-flow contract (KZClinical.trialflow): { trunk?, split: {at, label?, ratio?}, arms: [{key, name, n?, segs, split?: {at, ratio?,
     arms}}], after?, endpoints?, subs?, focus?, note }
     scenes: the shared periods → the randomisation node fans out to the arms → each arm's segments run along the week axis →
     a re-randomised arm splits into its sub-arms → endpoints and the shared follow-up → sub-studies → the focus arm */
  const wk = v => `W${v < 0 ? '−' : ''}${Math.abs(v)}`;
  def('trialflow', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'trialflow', d.note), M = C().trialflow(d), L = M.leaves, A = M.arms, nl = L.length;
    const wf = wfAt(cv);
    const FL = (global.KZ_TOKENS?.charts?.flow) || { titrate: '#FFC04D', maintain: '#F98500', placebo: '#6E7B8C', open: '#008F8A', off: '#ECEEF1', off_edge: '#B9C0C7' };
    const INKW = { placebo: '#FFFFFF', open: '#FFFFFF' }, nested = A.some(a => a.sub);
    // the name columns fit the longest arm / sub-arm name on one line (an arm name never wraps into its n= line)
    const ca = Math.min(.2, Math.max(.11, ...A.map(a => wf(a.name) + .01))), cb = nested ? Math.min(.18, Math.max(.11, ...L.filter(l => l.parent).map(l => wf(l.name) + .016))) : 0;
    const ns = M.subs.length, y0 = .21, rowH = Math.min(.17, (.68 - ns * .08) / nl), bh = Math.min(.064, rowH * .5);
    const X = C().flowScale(M, ca + cb + .03, .985, .075), CY = r => y0 + r * rowH + rowH / 2, mid = (CY(0) + CY(nl - 1)) / 2;
    const acy = Object.fromEntries(A.map(a => [a.key, (CY(a.rows[0]) + CY(a.rows[a.rows.length - 1])) / 2])), u = M.unit;
    const base = {}, add = (id, cls, text, geo) => { const el = k.obj(cv, id, cls, text); base[id] = { opacity: 0, ...geo }; return el; };
    add('hd', 'kz-demo-head', `${M.trunk.map(g => g.label).join(' → ')}${M.trunk.length ? ' → ' : ''}${M.split.label || '随机化'} → ${A.length} 组`, { x: .01, y: .015, w: .7 });
    add('band', 'kz-demo-band', null, { x: .005, y: y0, w: .99, h: rowH });
    add('ax', 'kz-demo-grid', null, { x: X(M.start), y: .125, w: X(M.final) - X(M.start), h: .002 });
    M.ticks.forEach((t, i) => add('tk' + i, 'kz-demo-tick is-x', wk(t), { x: Math.min(X(t) - .025, .994 - .05), y: .135, w: .05 }));
    // a segment: a bar (tall for the shared periods) and its label inside, or under it when it does not fit
    // li / ri: room kept clear at the bar's ends for a split node sitting on them
    const seg = (id, g, yc, h, li = 0, ri = 0) => {
      const kd = g.kind || 'maintain', x0 = X(g.from) + .002, w = X(g.to) - X(g.from) - .004, el = add(id, 'kz-demo-bar', null, { x: x0, y: yc - h / 2, w: .002, h, fill: FL[kd] });
      if (kd === 'off') el.style.boxShadow = `inset 0 0 0 1px ${FL.off_edge}`;
      const lw = w - li - ri, fits = wf(g.label || '') < lw, lb = add(id + 'l', 'kz-demo-label is-strong', g.label || '', { x: fits ? x0 + li : x0 + w / 2 - wf(g.label || '') / 2, y: fits ? yc - .022 : yc + h / 2 + .006, w: fits ? lw : wf(g.label || '') });
      lb.style.color = fits ? (INKW[kd] || 'var(--kz-ink)') : 'var(--kz-muted)'; lb.style.zIndex = 4; return { id, w };
    };
    const tall = CY(nl - 1) - CY(0) + bh, shared = [...M.trunk.map((g, i) => seg('tb' + i, g, mid, tall)), ...M.after.map((g, i) => seg('fb' + i, g, mid, tall))];
    const nameEl = (id, nm, n, geo) => { const l = add(id, 'kz-demo-lane-name', null, geo); l.innerHTML = ''; const b = document.createElement('b'); b.textContent = nm; l.append(b);
      if (n != null) { const sm = document.createElement('small'); sm.textContent = `n=${num(n)}`; l.append(sm); } };
    const node = (id, nx, ny, ys, label) => {
      add(id + 's', 'kz-demo-dep is-link', null, { x: nx - .0008, y: Math.min(...ys), w: .0016, h: Math.max(...ys) - Math.min(...ys) + .001 });
      add(id, 'kz-demo-node is-small', 'R', { x: nx - .016, y: ny - .028, w: .032, h: .056, scale: .2 }).style.zIndex = 5;
      add(id + 'l', 'kz-demo-label is-ms is-on', label, { x: nx + .012, y: Math.min(...ys) - bh / 2 - .05, w: wf(label) });
    };
    const ratio = (sp, r) => (sp.label || '随机化') + (r ? ` ${r.join(':')}` : '');
    node('rn', X(M.at), mid, Object.values(acy), ratio(M.split, M.ratio));
    const armSegs = [], subSegs = [];
    A.forEach((a, ai) => {
      nameEl('an' + ai, a.name, a.n, { x: .01, y: acy[a.key] - .045, w: ca - .01, h: .09 });
      a.segs.forEach((g, j) => armSegs.push(seg(`a${ai}_${j}`, g, acy[a.key], bh, g.from === M.at ? .016 : 0, a.sub && j === a.segs.length - 1 ? .018 : 0)));
      if (a.sub) {
        const kids = L.filter(l => l.parent === a.key), ys = kids.map(l => CY(l.row)), raw = d.arms[ai].split;
        node('sn' + ai, X(a.sub.at), acy[a.key], ys, ratio({ label: a.sub.label }, a.sub.ratio));
        add('br' + ai, 'kz-demo-dep is-link', null, { x: ca + .004, y: ys[0] - bh / 2, w: .0016, h: ys[ys.length - 1] - ys[0] + bh });
        kids.forEach((l, j) => { nameEl(`ln${ai}_${j}`, l.name, l.n, { x: ca + .014, y: CY(l.row) - .045, w: cb - .016, h: .09 });
          l.segs.forEach((g, q) => subSegs.push({ ...seg(`s${ai}_${j}_${q}`, g, CY(l.row), bh), ai, j })); });
      }
    });
    if (M.after.length) add('mg', 'kz-demo-dep is-link', null, { x: X(M.end) - .0008, y: CY(0), w: .0016, h: CY(nl - 1) - CY(0) + .001 });
    const GL = '<polygon points="10,2.5 17.5,10 10,17.5 2.5,10"/>';
    // endpoint labels left to right: one that would run into the previous one moves up a row
    const epEnd = [-1, -1], epUp = new Map();
    for (const e of M.endpoints.map(p => ({ p, x: X(p.at) - wf(p.label) / 2, w: wf(p.label) })).sort((a, b) => a.x - b.x)) {
      const row = e.x >= epEnd[0] + .008 || e.x < epEnd[1] + .008 ? 0 : 1; epEnd[row] = e.x + e.w; epUp.set(e.p, row);
    }
    M.endpoints.forEach((p, i) => {
      const g = add('ep' + i, 'kz-demo-ms' + (p.primary ? '' : ' is-ahead'), null, { x: X(p.at) - .014, y: .105, w: .028, h: .04, scale: .2 });
      g.innerHTML = `<svg viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${GL}</svg>`;
      add('epl' + i, 'kz-demo-label is-ms' + (p.primary ? ' is-on' : ''), p.label, { x: Math.max(.005, Math.min(.995 - wf(p.label), X(p.at) - wf(p.label) / 2)), y: epUp.get(p) ? .022 : .06, w: wf(p.label) });
      add('epg' + i, 'kz-demo-dep is-link', null, { x: X(p.at) - .0006, y: .16, w: .0012, h: y0 + nl * rowH - .16 });
    });
    const names = Object.fromEntries([...A, ...L].map(x => [x.key, x.name]));
    M.subs.forEach((x, i) => {
      const yy = y0 + nl * rowH + .03 + i * .08, el = add('ss' + i, 'kz-demo-bar', null, { x: X(x.from) + .002, y: yy, w: .002, h: .05, fill: '#FFFFFF' });
      el.style.boxShadow = `inset 0 0 0 1.4px ${global.KZ_TOKENS?.flagship?.accent_ink || '#9A4D00'}`;
      add('ssl' + i, 'kz-demo-label is-start is-strong', `${x.name}${x.n != null ? ` n=${num(x.n)}` : ''} · ${x.of.map(q => names[q]).join('、')}`, { x: X(x.from) + .014, y: yy + .004, w: X(x.to) - X(x.from) - .02 }).style.zIndex = 4;
    });
    const on = ids => Object.fromEntries(ids.filter(id => base[id]).map(id => [id, { opacity: 1 }]));
    const grow = list => Object.fromEntries(list.flatMap(s => [[s.id, { w: s.w, opacity: 1 }], [s.id + 'l', { opacity: 1 }]]));
    const fa = A.find(a => a.key === M.focus) || A[0], fi = A.indexOf(fa), sub = A.find(a => a.sub);
    const pathText = a => a.segs.map(g => g.label).join(' → ');
    const scenes = [
      { id: 'shared', caption: M.trunk.length ? `所有受试者先经过${M.trunk.map(g => `${g.label}（${wk(g.from)}–${wk(g.to)}）`).join('、')}` : `${wk(M.at)} 起直接随机化`,
        order: shared.filter(s => s.id.startsWith('tb')).map(s => s.id),
        set: over(base, { hd: { opacity: 1 }, ax: { opacity: 1 }, ...on(M.ticks.map((_, i) => 'tk' + i)), ...grow(shared.filter(s => s.id.startsWith('tb'))) }) },
      { id: 'random', caption: `${wk(M.at)} ${ratio(M.split, M.ratio)}：${A.map(a => `${a.name}${a.n != null ? ` ${num(a.n)} 例` : ''}`).join('、')}`,
        order: ['rns', 'rn', 'rnl', ...A.map((_, i) => 'an' + i)], set: { rns: { opacity: 1 }, rn: { opacity: 1, scale: 1 }, rnl: { opacity: 1 }, ...on(A.map((_, i) => 'an' + i)) } },
      { id: 'arms', caption: A.map(a => `${a.name}：${pathText(a)}`).join('；'), order: armSegs.map(s => s.id), set: grow(armSegs) },
      ...(sub ? [{ id: 'sub', caption: `${wk(sub.sub.at)} ${sub.name} ${ratio({ label: sub.sub.label }, sub.sub.ratio)}：${L.filter(l => l.parent === sub.key).map(l => `${l.name}${l.n != null ? ` ${num(l.n)} 例` : ''}`).join('、')}`,
        order: subSegs.map(s => s.id),
        set: { ...Object.fromEntries(A.flatMap((a, ai) => a.sub ? [['sn' + ai + 's', { opacity: 1 }], ['sn' + ai, { opacity: 1, scale: 1 }], ['sn' + ai + 'l', { opacity: 1 }], ['br' + ai, { opacity: 1 }],
          ...L.filter(l => l.parent === a.key).map((l, j) => [`ln${ai}_${j}`, { opacity: 1 }])] : [])), ...grow(subSegs) } }] : []),
      { id: 'end', caption: [...M.endpoints.map(p => p.label), ...(M.after.length ? [`${wk(M.end)} 后${M.after.map(g => g.label).join('、')} ${M.final - M.end} ${u}`] : [])].join('；') || `各组 ${wk(M.end)} 结束`,
        order: [...M.endpoints.map((_, i) => 'ep' + i), 'mg', ...shared.filter(s => s.id.startsWith('fb')).map(s => s.id)],
        set: { ...Object.fromEntries(M.endpoints.flatMap((_, i) => [['ep' + i, { opacity: 1, scale: 1 }], ['epl' + i, { opacity: 1 }], ['epg' + i, { opacity: 1 }]])),
          ...on(['mg']), ...grow(shared.filter(s => s.id.startsWith('fb'))) } },
      ...(ns ? [{ id: 'subs', caption: M.subs.map(x => `${x.name}${x.n != null ? ` ${num(x.n)} 例` : ''}，${wk(x.from)}–${wk(x.to)}，来自${x.of.map(q => names[q]).join('、')}`).join('；'),
        order: M.subs.map((_, i) => 'ss' + i), set: Object.fromEntries(M.subs.flatMap((x, i) => [['ss' + i, { w: X(x.to) - X(x.from) - .004, opacity: 1 }], ['ssl' + i, { opacity: 1 }]])) }] : []),
      { id: 'focus', caption: `重点：${fa.name}${fa.n != null ? ` ${num(fa.n)} 例` : ''}，${pathText(fa)}` + (fa.sub ? `，${wk(fa.sub.at)} 再分为${L.filter(l => l.parent === fa.key).map(l => l.name).join('与')}` : ''),
        set: { band: { opacity: 1, y: y0 + fa.rows[0] * rowH, h: fa.rows.length * rowH },
          ...Object.fromEntries(A.flatMap((a, ai) => ai === fi ? [] : [['an' + ai, { opacity: .5 }], ...a.segs.flatMap((_, j) => [[`a${ai}_${j}`, { opacity: .35 }], [`a${ai}_${j}l`, { opacity: .45 }]])])) } },
    ];
    return mount(root, scenes, opt, scenes.length - 1, [
      ...(M.n != null ? [{ value: num(M.n), label: '随机化（例）' }] : []), { value: String(nl), label: '治疗分支' },
      { value: `${M.final - M.start}`, label: `总时长（${u}）` }]);
  });
  /* ---------- efficacy ----------
     data: the efficacy-summary contract (KZClinical.efficacy): { arms: [{key, name, n, role: treat|comparator}], rows: [{key, label,
     tier?, unit?, type: continuous|binary, better, values, vs: {treat key: {diff, ci, p?}}}], focus?, note }
     scenes: the endpoints with each arm's value → per endpoint type, the difference and 95% CI of every treat arm against the
     comparator on that section's axis (filled when the CI excludes 0 the good way, hollow when it crosses 0) → the endpoints
     whose CI crosses 0 → the focus endpoint */
  def('efficacy', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'efficacy', d.note), M = C().efficacy(d), A = M.arms, R = M.rows, n = R.length, TY = M.axes;
    const wf = wfAt(cv);
    const TREAT = global.KZ_TOKENS?.charts?.categorical?.[0] || '#D46B08', COMP = global.KZ_TOKENS?.charts?.comparator || '#6E7B8C';
    const RISK = global.KZ_TOKENS?.color?.risk || '#C00000', NS = '#9AA1A8', nt = M.treat.length;
    const tc = Object.fromEntries(M.treat.map((i, q) => [i, nt > 1 ? mix(TREAT, .3 * (1 - q / (nt - 1))) : TREAT]));
    const vx = .25, vw = .085, fx0 = vx + vw * A.length + .025, fx1 = .75, dx = .765, sh = .06;
    const y0 = .2, rowH = Math.min(.1, (.78 - TY.length * sh) / n), base = {};
    const add = (id, cls, text, geo) => { const el = k.obj(cv, id, cls, text); base[id] = { opacity: 0, ...geo }; return el; };
    const f = (v, dp) => num(v, dp).replace('-', '−');
    // lines that belong together are one object (a column of <b>/<small> lines), so they can never overlap each other
    const stack = (id, lines, geo, center) => { const el = add(id, 'kz-demo-lane-name', null, geo); el.innerHTML = '';
      if (center) { el.style.alignItems = 'center'; el.style.textAlign = 'center'; }
      lines.forEach(([t, tag, st]) => { const e = document.createElement(tag); if (Array.isArray(t)) e.append(...t); else e.textContent = t; Object.assign(e.style, st || {}); el.append(e); }); return el; };
    const tiers = [...new Set(R.map(r => r.tier).filter(Boolean))];
    add('hd', 'kz-demo-head', `${n} 个终点 · ${A.map(a => a.name).join(' / ')} · 各治疗组对${A[M.comp].name}`, { x: .01, y: .015, w: .75 });
    add('band', 'kz-demo-band', null, { x: .005, y: y0, w: .99, h: rowH });
    A.forEach((a, i) => {
      // the name breaks at the space nearest its middle (KZ-001 / 0.5 mg) instead of wherever the column ends
      const sp = [...a.name].map((ch, q) => (ch === ' ' ? q : -1)).filter(q => q >= 0), cut = sp.length ? sp.reduce((p, q) => (Math.abs(q - a.name.length / 2) < Math.abs(p - a.name.length / 2) ? q : p)) : -1;
      const nm = cut < 0 || wf(a.name) < vw ? [a.name] : [a.name.slice(0, cut), a.name.slice(cut + 1)], dot = document.createElement('span');
      dot.textContent = '● '; dot.style.color = tc[i] || COMP;
      stack('ah' + i, [[[dot, nm[0]], 'b'], ...nm.slice(1).map(t => [t, 'b']), [`n=${num(a.n)}`, 'small']], { x: vx + i * vw, y: .055, w: vw, h: .125 }, true);
    });
    let y = y0; const rowY = {}, secY = {}, X = {};
    TY.forEach(t => {
      secY[t] = y; y += sh; const dom = M.domain[t];
      X[t] = v => fx0 + C().efPos(dom, v) * (fx1 - fx0); const ref = t === 'ratio' ? 1 : 0;
      add('sh_' + t, 'kz-demo-label is-ms is-start', C().EF_HEAD[t], { x: .01, y: secY[t] + .015, w: fx0 - .03 });
      C().efTicks(dom).forEach((v, q) => add(`tk_${t}${q}`, 'kz-demo-tick is-x' + (v === ref ? ' is-on' : ''), String(v).replace('-', '−'), { x: X[t](v) - .02, y: secY[t] + .015, w: .04 }));
      const rows = R.filter(r => r.axis === t);
      add('z_' + t, 'kz-demo-dep is-link', null, { x: X[t](ref) - .0008, y, w: .0016, h: rows.length * rowH });
      rows.forEach(r => { rowY[r.key] = y; y += rowH; });
    });
    const cmpIds = {};
    R.forEach((r, ri) => {
      const cy = rowY[r.key] + rowH / 2, nm = add('rn' + ri, 'kz-demo-lane-name', null, { x: .01, y: cy - Math.min(.045, rowH / 2 - .003), w: vx - .02, h: Math.min(.09, rowH - .006) });
      nm.innerHTML = ''; const b = document.createElement('b'); b.textContent = r.label; nm.append(b);
      const sub = [r.tier, r.unit, r.time].filter(Boolean).join(' · '); if (sub) { const sm = document.createElement('small'); sm.textContent = sub; nm.append(sm); }
      A.forEach((a, i) => {
        const v = r.values[i], cls = 'kz-demo-label' + (i in tc ? ' is-strong' : '');
        const [main, small] = C().efValue(r, i);
        if (!small) { add(`v${ri}_${i}`, cls, main, { x: vx + i * vw, y: cy - .02, w: vw }); return; }
        stack(`v${ri}_${i}`, [[main, 'b', i in tc ? {} : { fontWeight: 400, color: 'var(--kz-body)' }], [small, 'small']], { x: vx + i * vw, y: cy - rowH / 2 + .003, w: vw, h: rowH - .006 }, true);
      });
      const ks = Object.keys(r.cmp), dy = Math.min(.036, rowH * .36); cmpIds[r.key] = [];
      ks.forEach((key, j) => {
        const c = r.cmp[key], i = A.findIndex(a => a.key === key), yy = cy + (j - (ks.length - 1) / 2) * dy, Xt = X[r.axis];
        const col = c.verdict === 'worse' ? RISK : c.verdict === 'better' ? tc[i] : NS, id = `c${ri}_${j}`;
        add(id + 'l', 'kz-demo-bar', null, { x: Xt(r.ref), y: yy - .002, w: .002, h: .004, fill: col });
        const sq = add(id + 's', 'kz-demo-ms' + (c.verdict === 'ns' ? ' is-ahead' : ''), null, { x: Xt(c.diff) - .012, y: yy - .018, w: .024, h: .036, scale: .2 });
        sq.innerHTML = '<svg viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><rect x="4" y="4" width="12" height="12" rx="2"/></svg>'; sq.style.color = col;
        cmpIds[r.key].push({ id, t: 'd' + ri, c, col, x: Xt(c.ci[0]), w: Xt(c.ci[1]) - Xt(c.ci[0]) });
      });
      const fo = r.key === M.focus;
      stack('d' + ri, cmpIds[r.key].map(o => { const dot = document.createElement('span'); dot.textContent = '● '; dot.style.color = o.col;
        return [[dot, `${C().efDiff(o.c, r.dp, r.measure)}${o.c.p != null ? `  P ${o.c.p}` : ''}`], 'b',
          { fontWeight: fo && o.c.verdict === 'better' ? 700 : 500, color: o.c.verdict === 'worse' ? RISK : o.c.verdict === 'ns' ? 'var(--kz-muted)' : 'var(--kz-ink)', whiteSpace: 'nowrap' }]; }),
        { x: dx, y: rowY[r.key] + .003, w: .99 - dx, h: rowH - .006 });
    });
    const show = ids => Object.fromEntries(ids.filter(id => base[id]).map(id => [id, { opacity: 1 }]));
    const forest = rs => Object.fromEntries(rs.flatMap(r => cmpIds[r.key].flatMap(o => [[o.id + 'l', { x: o.x, w: o.w, opacity: 1 }], [o.id + 's', { opacity: 1, scale: 1 }], [o.t, { opacity: 1 }]])));
    const ns = R.filter(r => Object.values(r.cmp).some(c => c.verdict !== 'better'));
    // captions name the measure, never the data type (round 9)
    const capT = t => { const rs = R.filter(r => r.axis === t), all = rs.flatMap(r => Object.values(r.cmp)), win = all.filter(c => c.verdict === 'better').length, ref = t === 'ratio' ? 1 : 0;
      const top = rs.find(r => r.key === M.focus) || rs[0], size = c => Math.abs(t === 'ratio' ? Math.log(c.diff) : c.diff), best = Object.entries(top.cmp).sort((a, b) => size(b[1]) - size(a[1]))[0];
      return `${{ md: '均值差', rd: '率差', ratio: '比值' }[t]} ${rs.length} 项：${win}/${all.length} 个比较 CI 不跨 ${ref} 且方向有利；${top.label} ${A.find(a => a.key === best[0]).name} ${C().efDiff(best[1], top.dp, top.measure).split(' (')[0]}${t === 'rd' ? ' 个百分点' : t === 'md' ? (top.unit || '') : ''}`; };
    const fr = R.find(r => r.key === M.focus) || R[0], fri = R.indexOf(fr);
    const scenes = [
      { id: 'endpoints', caption: `${n} 个终点` + (tiers.length ? `（${tiers.map(t => `${t} ${R.filter(r => r.tier === t).length}`).join('、')}）` : '') + `，${A.map(a => `${a.name} ${num(a.n)} 例`).join('、')}`,
        set: over(base, { hd: { opacity: 1 }, ...show(Object.keys(base).filter(id => /^(ah|rn|v)\d/.test(id))) }) },
      ...TY.map(t => ({ id: t, caption: capT(t), order: R.filter(r => r.axis === t).flatMap(r => cmpIds[r.key].map(o => o.id + 'l')),
        set: { ...show(['sh_' + t, 'z_' + t, ...Object.keys(base).filter(id => id.startsWith('tk_' + t))]), ...forest(R.filter(r => r.axis === t)) } })),
      ...(ns.length ? [{ id: 'ns', caption: ns.map(r => `${r.label}：${Object.entries(r.cmp).filter(([, c]) => c.verdict !== 'better').map(([key, c]) => `${A.find(a => a.key === key).name} ${c.verdict === 'worse' ? '方向不利' : `95% CI 跨 ${r.ref}`}`).join('、')}`).join('；'),
        set: Object.fromEntries(R.flatMap((r, ri) => ns.includes(r) ? [] : [['rn' + ri, { opacity: .5 }], ...cmpIds[r.key].flatMap(o => [[o.id + 'l', { opacity: .3 }], [o.id + 's', { opacity: .3 }], [o.t, { opacity: .4 }]])])) }] : []),
      { id: 'focus', caption: `重点：${fr.label}，` + Object.entries(fr.cmp).map(([key, c]) => `${A.find(a => a.key === key).name} ${C().efDiff(c, fr.dp, fr.measure)}`).join('，'),
        set: { band: { opacity: 1, y: rowY[fr.key] }, ...Object.fromEntries(R.flatMap((r, ri) => ri === fri ? [['rn' + ri, { opacity: 1 }], ...cmpIds[r.key].flatMap(o => [[o.id + 'l', { opacity: 1 }], [o.id + 's', { opacity: 1, scale: 1.3 }], [o.t, { opacity: 1 }]])]
          : [['rn' + ri, { opacity: .5 }], ...A.flatMap((_, i) => [[`v${ri}_${i}`, { opacity: .45 }], [`w${ri}_${i}`, { opacity: .45 }]]).filter(([id]) => base[id]),
            ...cmpIds[r.key].flatMap(o => [[o.id + 'l', { opacity: .3 }], [o.id + 's', { opacity: .3 }], [o.t, { opacity: .4 }]])])) } },
    ];
    const stage = mount(root, scenes, opt, scenes.length - 1, [
      { value: String(n), label: '终点' }, { value: `${M.wins}/${M.tests}`, label: 'CI 不跨参考线且有利' },
      ...(fr.cmp ? [{ value: Object.values(fr.cmp).every(c => c.verdict === 'better') ? '达到' : '未全达到', label: `${fr.label}`, risk: !Object.values(fr.cmp).every(c => c.verdict === 'better') }] : [])]);
    // an endpoint row holds its name over tier · unit and one difference line per treated arm
    return fitGuard(cv, stage, () => [...cv.querySelectorAll('[data-kz-obj]')].filter(e => /^(rn|d)\d+$/.test(e.dataset.kzObj) && e.scrollHeight > e.clientHeight + 2).length,
      (H, bad) => `有效性演示放不下：${n} 个终点、${nt} 个治疗组在 ${Math.round(H)} px 高的舞台里每行只有 ${Math.round(rowH * H)} px，${bad} 处文字超出行高；`
        + '把终点拆到两个舞台（主要终点一个、次要终点一个），或改用静态模板 efficacy-summary（15 DEMO-03）');
  });
  /* ---------- soa ----------
     data: the SoA contract (KZClinical.soa): { visits: [{v, week, period?, window?}], events?: [{at, label, kind}],
     bands?: [{label, from, to, kind, text?}], rows: [{section} | {item, at: [1 | 0 | null | text]}], footnotes?, focus?: item, note }
     scenes (round 9): the visit columns under their periods → the treatment periods (study drug, background, rescue…) →
     the key events (randomisation, primary endpoint…) → per section, its assessments item by item → the focus item at the
     primary-endpoint visits. No per-visit load: what matters is when, and which assessment where. */
  const SOA_FILL = { drug: '#F2B467', background: '#DDE2E7', rescue: '#FBE3C2', washout: '#EEF0F2', other: '#EEF0F2' };
  def('soa', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'soa', d.note), M = C().soa(d), V = M.visits, nv = V.length, SC = M.sections.filter(q => q.items.length), B = M.bands;
    const CAT = global.KZ_TOKENS?.charts?.categorical || ['#D46B08', '#407AAA', '#587B3B', '#A85F34', '#7A5C99'], ACC = global.KZ_TOKENS?.flagship?.accent_ink || '#9A4D00';
    const named = SC.some(q => q.name), sx = named ? .085 : .01, cx0 = .235, cw = (.985 - cx0) / nv, X = i => cx0 + i * cw + cw / 2, prim = new Set(M.primary);
    const ey = .212, eh = M.events.length ? .075 : 0, by = ey + eh + .006, bh = .05, iy0 = by + B.length * bh + .01;
    const rows = SC.flatMap(q => q.items), rh = Math.min(.06, (.985 - iy0) / rows.length);
    const base_ = {}, add = (id, cls, text, geo) => { const el = k.obj(cv, id, cls, text); base_[id] = { opacity: 0, ...geo }; return el; };
    const lane = (id, b, sm, geo) => { const l = add(id, 'kz-demo-lane-name', null, geo); l.innerHTML = ''; const e = document.createElement('b'); e.textContent = b; l.append(e);
      if (sm) { const x = document.createElement('small'); x.textContent = sm; l.append(x); } return l; };
    const glyph = (id, svg, color, geo, cls = '') => { const g = add(id, 'kz-demo-ms' + cls, null, { scale: .2, ...geo }); g.innerHTML = `<svg viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${svg}</svg>`; g.style.color = color; return g; };
    const DIA = '<polygon points="10,2.5 17.5,10 10,17.5 2.5,10"/>', DOT = '<circle cx="10" cy="10" r="7"/>';
    add('hd', 'kz-demo-head', `${nv} 个访视 · ${M.events.length} 个关键节点 · ${B.length} 段给药 / 治疗 · ${M.items.length} 个评估项目`, { x: .01, y: .015, w: .8 });
    M.primary.forEach(i => add('pc' + i, 'kz-demo-band', null, { x: X(i) - cw / 2 + .002, y: .118, w: cw - .004, h: .985 - .118 }));
    M.periods.forEach((p, q) => {
      if (!p.name) return; const x = cx0 + p.from * cw, w = (p.to - p.from) * cw;
      add('pl' + q, 'kz-demo-tick is-x is-on', p.name, { x: x + .003, y: .066, w: w - .006 });
      add('pr' + q, 'kz-demo-grid', null, { x: x + .004, y: .106, w: w - .008, h: .003 });
    });
    V.forEach((v, i) => { const l = lane('vv' + i, v.v, v.week || '', { x: X(i) - cw / 2, y: .118, w: cw, h: .085 }); l.style.alignItems = 'center'; l.style.textAlign = 'center'; });
    // key events: a diamond (primary in accent, randomisation in the treat hue) or a dot, with its label under it
    const at = {}; M.events.forEach(e => { (at[e.i] ||= []).push(e); });
    if (M.events.length) add('el', 'kz-demo-label is-start is-strong', '关键节点', { x: .01, y: ey + .012, w: cx0 - .02 });
    Object.entries(at).forEach(([i, es]) => { i = +i; const kinds = es.map(e => e.kind), kk = kinds.includes('primary') ? 'primary' : kinds.includes('random') ? 'random' : kinds[0];
      glyph('eg' + i, kk === 'primary' || kk === 'random' ? DIA : DOT, kk === 'primary' ? ACC : kk === 'random' ? CAT[0] : '#9AA1A8', { x: X(i) - .012, y: ey, w: .024, h: .03 });
      const l = lane('et' + i, es.map(e => e.label).join('、'), '', { x: X(i) - cw / 2, y: ey + .03, w: cw, h: eh - .032 }); l.style.alignItems = 'center'; l.style.textAlign = 'center';
      if (kk !== 'primary') l.querySelector('b').style.fontWeight = 500; });
    // treatment periods: the label on the left, a flat strip from the first to the last visit with its text
    B.forEach((b, q) => { const y = by + q * bh, x = cx0 + b.from * cw + .004, w = (b.to - b.from + 1) * cw - .008;
      add('bl' + q, 'kz-demo-label is-start is-strong', b.label, { x: .01, y: y + .006, w: cx0 - .02 });
      add('bb' + q, 'kz-demo-bar', null, { x, y: y + .006, w: .002, h: bh - .012, fill: SOA_FILL[b.kind] });
      add('bt' + q, 'kz-demo-label', b.text || b.label, { x: x + .006, y: y + .006, w: w - .012 }).style.zIndex = 4; });   // above the strip (kz-demo-bar is z 2)
    // assessments item by item; the section name in its own column beside its rows
    let y = iy0; const itemY = {};
    SC.forEach((q, si) => { const col = CAT[si % CAT.length], y0 = y;
      q.items.forEach(ii => { const it = M.items[ii], cy = y + rh / 2; itemY[ii] = y;
        add('in' + ii, 'kz-demo-label is-start' + (it.item === M.focus ? ' is-strong' : ''), it.item, { x: sx, y: cy - .018, w: cx0 - sx - .01 });
        it.marks.forEach(i => glyph(`m${ii}_${i}`, DOT, col, { x: X(i) - .009, y: cy - .011, w: .018, h: .022 }));
        y += rh; });
      if (named) add('sn' + si, 'kz-demo-label is-start', q.name, { x: .01, y: y0 + (y - y0) / 2 - .018, w: sx - .015 });
      add('sg' + si, 'kz-demo-grid', null, { x: .01, y, w: .975, h: .002 }); });
    const fi = M.items.findIndex(x => x.item === M.focus), F_ = fi >= 0 ? M.items[fi] : null;
    add('band', 'kz-demo-band', null, { x: .005, y: F_ ? itemY[fi] : iy0, w: .99, h: rh });
    if (F_) F_.marks.filter(i => prim.has(i)).forEach(i => glyph('fm' + i, DIA, ACC, { x: X(i) - .014, y: itemY[fi] + rh / 2 - .018, w: .028, h: .036 }));
    const show = ids => Object.fromEntries(ids.filter(id => base_[id]).map(id => [id, { opacity: 1 }]));
    const vlab = i => `${V[i].v}${V[i].week ? ` ${V[i].week}` : ''}`, span = p => (p.to - p.from > 1 ? `${V[p.from].v}–${V[p.to - 1].v}` : V[p.from].v);
    const scenes = [
      { id: 'visits', caption: `${nv} 个访视` + (M.periods.some(p => p.name) ? `：${M.periods.filter(p => p.name).map(p => `${p.name} ${span(p)}`).join('、')}` : ''),
        set: over(base_, { hd: { opacity: 1 }, ...show(Object.keys(base_).filter(id => /^(pl|pr|vv)\d/.test(id))) }) },
      ...(B.length ? [{ id: 'treatment', caption: B.map(b => `${b.label} ${V[b.from].v}–${V[b.to].v}`).join('；'), order: B.map((_, q) => 'bb' + q),
        set: Object.fromEntries(B.flatMap((b, q) => [['bl' + q, { opacity: 1 }], ['bb' + q, { opacity: 1, w: (b.to - b.from + 1) * cw - .008 }], ['bt' + q, { opacity: 1 }]])) }] : []),
      ...(M.events.length ? [{ id: 'events', caption: M.events.map(e => `${e.label} ${vlab(e.i)}`).join('、'),
        set: { ...show(['el', ...Object.keys(at).flatMap(i => ['eg' + i, 'et' + i]), ...M.primary.map(i => 'pc' + i)]), ...Object.fromEntries(Object.keys(at).map(i => ['eg' + i, { opacity: 1, scale: 1 }])) } }] : []),
      ...SC.map((q, si) => ({ id: 'sec' + si, caption: `${q.name || '评估'}：` + q.items.map(ii => `${M.items[ii].item} ${M.items[ii].count} 次`).join('、'),
        order: q.items.map(ii => 'in' + ii),
        set: { ['sn' + si]: { opacity: 1 }, ['sg' + si]: { opacity: 1 }, ...Object.fromEntries(q.items.flatMap(ii => [['in' + ii, { opacity: 1 }], ...M.items[ii].marks.map(i => [`m${ii}_${i}`, { opacity: 1, scale: 1 }])])) } })),
      ...(F_ ? [{ id: 'focus', caption: `重点：${F_.item}，${F_.marks.map(vlab).join('、')} 共 ${F_.count} 次` + (M.primary.length ? `；主要终点在 ${M.primary.map(vlab).join('、')}` : ''),
        order: F_.marks.filter(i => prim.has(i)).map(i => 'fm' + i),
        set: { band: { opacity: 1 }, ...Object.fromEntries(F_.marks.filter(i => prim.has(i)).map(i => ['fm' + i, { opacity: 1, scale: 1 }])),
          ...Object.fromEntries(M.items.flatMap((it, ii) => ii === fi ? [] : [['in' + ii, { opacity: .45 }], ...it.marks.map(i => [`m${ii}_${i}`, { opacity: .35 }])])) } }] : []),
    ];
    const stage = mount(root, scenes, opt, scenes.length - 1, [
      { value: String(nv), label: '访视' }, { value: String(M.items.length), label: '评估项目' },
      ...(M.primary.length ? [{ value: M.primary.map(i => V[i].v).join('、'), label: '主要终点访视' }] : [])]);
    // the header (title line, period names, visit · week) sits in fixed shares of the stage height: on a short stage they overprint
    const obj = id => cv.querySelector(`[data-kz-obj="${id}"]`);
    return fitGuard(cv, stage, () => textClash(['hd', ...M.periods.map((_, q) => 'pl' + q), ...V.map((_, i) => 'vv' + i)].map(obj)),
      (H, bad) => `SoA 演示放不下：${Math.round(H)} px 高的舞台里表头 ${bad} 处文字相压（标题、分期名、访视号 · 周次）；放整行舞台并给足高度（约 520 px 以上），访视多时改用静态模板 soa（15 DEMO-03）`);
  });
  /* ---------- program ----------
     data: the clinical-development-plan contract (KZClinical.program): { from, to, today?, phases?, focus?, lanes: [{key, name,
     note?, bars: [{key, phase, start, end, label?}], milestones?: [{key, at, label, kind?, risk?}]}], note }
     scenes: the lanes on the quarter axis → the phases laid out lane by lane → the today line walks in and turns what is
     ahead into plan (light, dashed) → milestones pin onto the bars (past filled, ahead hollow) → the focus */
  const GLYPH = { start: '<circle cx="10" cy="10" r="6"/>', readout: '<polygon points="10,2.5 17.5,10 10,17.5 2.5,10"/>',
    submit: '<polygon points="10,2.5 17.5,16 2.5,16"/>', approve: '<polygon points="10,1.5 12.3,7.2 18.5,7.6 13.7,11.5 15.3,17.6 10,14.3 4.7,17.6 6.3,11.5 1.5,7.6 7.7,7.2"/>',
    other: '<polygon points="16.1,13.5 10,17 3.9,13.5 3.9,6.5 10,3 16.1,6.5"/>' };
  const mix = (hex, t = .55) => '#' + [1, 3, 5].map(i => Math.round(parseInt(hex.slice(i, i + 2), 16) * (1 - t) + 255 * t).toString(16).padStart(2, '0')).join('');
  // label width as a canvas fraction, measured against a 1000 px canvas (narrower than any stage), so the estimate errs wide
  const wf = s => [...s].reduce((a, c) => a + (c.charCodeAt(0) < 0x2000 ? .56 : 1), 0) * 16 / 1000 + .014;
  // the same estimate against this stage's own width when it is narrower than 1000 logical px (a stage beside a card is
  // about 700): text is sized by the deck unit, not by the stage, so a narrow stage needs a larger fraction
  const wfAt = cv => { let k = 1; try { const w = cv.getBoundingClientRect().width, u = parseFloat(getComputedStyle(cv).getPropertyValue('--kz-component-u')) || 1;
    if (w > 0) k = Math.max(1, 1000 * u / w); } catch (e) { /* detached: keep the 1000 px estimate */ } return s => (wf(s) - .014) * k + .014; };
  def('program', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'program', d.note), M = C().program(d), G = M.granularity, q = v => C().ttext(v, G), qe = v => C().ttext(v - 1e-6, G);
    const wf = wfAt(cv);
    // the visible lanes (children of a collapsed parent hidden) with what each draws: own bars or the merged summary
    const lanes = M.visible.map(ln => ({ ...ln, bars: ln.bars.length ? ln.bars : (ln.collapsed ? ln.summary || [] : []), milestones: [...ln.milestones, ...(ln.collapsed ? ln.summary_ms || [] : [])].sort((a, b) => a.t - b.t) })), n = lanes.length;
    const UNIT = { quarter: ['个季度', 1], month: ['个月', 3], day: ['天', 0] }[G], gap = dt => UNIT[1] ? `${Math.round(dt * UNIT[1])} ${UNIT[0]}` : `${Math.round((new Date(C().ttext(dt + M.today, 'day')) - new Date(C().ttext(M.today, 'day'))) / 864e5)} 天`;
    const col = (global.KZ_TOKENS?.charts?.phases) || ['#FFEAA8', '#FFD02A', '#FFA916', '#F98500', '#D96500'];
    const X = t => .21 + (t - M.from) / (M.to - M.from) * .775, y0 = .17, rowH = .7 / n, bh = Math.min(.058, rowH * .3), LH = .046;
    const Y = i => y0 + i * rowH, BY = i => Y(i) + rowH / 2 - bh / 2, now = M.today, tx = now == null ? null : X(now + M.today_w / 2);
    k.obj(cv, 'hd', 'kz-demo-head', `${{ quarter: '季度', month: '月', day: '日' }[G]}轴 ${C().qtext(M.from)}–${C().qtext(M.to - 1)}` + (now == null ? '' : ` · 当前 ${q(now)}`));
    k.obj(cv, 'band', 'kz-demo-band');
    const base = { hd: { x: .01, y: .015, w: .5 }, band: { x: .005, y: y0, w: .99, h: rowH, opacity: 0 } };
    // phase legend, right-aligned on the head line (the bars carry colour only)
    let lx = .99; M.used.slice().reverse().forEach(pi => { const w = wf(M.phases[pi]) + .02; lx -= w;
      const g = k.obj(cv, 'lg' + pi, 'kz-demo-legend', M.phases[pi]); g.style.setProperty('--sw', col[pi]); base['lg' + pi] = { x: lx, y: .015, w, opacity: 0 }; });
    // axis: one label per year, quarter ticks where they fit, a grid line at each year start
    for (let t = M.from, j = 0; t < M.to; t++) {
      if (t === M.from || t % 4 === 0) {
        const e = Math.min(M.to, (Math.floor(t / 4) + 1) * 4);
        k.obj(cv, 'yr' + j, 'kz-demo-head is-num', `${Math.floor(t / 4)}`); base['yr' + j] = { x: X(t), y: .075, w: X(e) - X(t), opacity: 0 };
        k.obj(cv, 'gl' + j, 'kz-demo-grid'); base['gl' + j] = { x: X(t), y: .075, w: .001, h: .8, opacity: 0 }; j++;
      }
    }
    lanes.forEach((ln, i) => {
      const l = k.obj(cv, 'ln' + i, 'kz-demo-lane-name'); l.innerHTML = ''; const b = document.createElement('b'); b.textContent = ln.name; l.append(b);
      if (ln.note) { const s = document.createElement('small'); s.textContent = ln.note; l.append(s); }
      base['ln' + i] = { x: .01 + (ln.depth ? .014 : 0), y: Y(i) + rowH / 2 - .045, w: .19 - (ln.depth ? .014 : 0), h: .09, opacity: 0 };
      ln.bars.forEach((br, j) => {
        const id = `b${i}_${j}`, x0 = X(br.s) + .002, x1 = X(br.e) - .002, cut = tx != null && tx < x1 ? Math.max(x0, tx) : x1;
        k.obj(cv, id, 'kz-demo-bar is-phase'); base[id] = { x: x0, y: BY(i), w: 0, h: bh, opacity: 0, fill: col[br.pi] };
        if (cut < x1) { k.obj(cv, id + 'p', 'kz-demo-bar is-plan'); base[id + 'p'] = { x: cut, y: BY(i), w: 0, h: bh, opacity: 0, fill: col[br.pi] }; }
        br.geo = { x0, x1, cut };
      });
      // milestone labels: above the bar, else below it; centred, starting at, ending at, then beside the glyph
      const taken = [];
      ln.milestones.forEach((m, j) => {
        const cx = X(m.t + m.tw / 2), w = wf(m.label), clear = sp => tx == null || !(sp[0] - .003 < tx && tx < sp[1] + .003);
        const free = (side, sp) => !taken.some(([s, a, b]) => s === side && !(sp[1] <= a || sp[0] >= b));
        const spans = [cx - w / 2, cx - .01, cx + .01 - w, cx - .016 - w, cx + .016].map(lo => Math.min(Math.max(lo, .21), .985 - w)).map(lo => [lo, lo + w]);
        let pick = null;
        for (const side of ['up', 'down']) { pick = (spans.find(sp => free(side, sp) && clear(sp)) || spans.find(sp => free(side, sp))); if (pick) { pick = [side, ...pick]; break; } }
        pick = pick || ['up', ...spans[0]]; taken.push(pick); m.geo = { cx, side: pick[0], lo: pick[1], w };
        const g = k.obj(cv, `m${i}_${j}`, 'kz-demo-ms is-' + m.kind + (m.risk ? ' is-risk' : ''));
        g.innerHTML = `<svg viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${GLYPH[m.kind]}</svg>`;
        base[`m${i}_${j}`] = { x: cx - .016, y: BY(i) - .028, w: .032, h: .04, opacity: 0, scale: .2 };
        k.obj(cv, `ml${i}_${j}`, 'kz-demo-label is-ms' + (m.risk ? ' is-risk' : ''), m.label);
        base[`ml${i}_${j}`] = { x: pick[1], y: pick[0] === 'up' ? BY(i) - .012 - LH - .02 : BY(i) + bh + .008, w, opacity: 0 };
      });
    });
    if (tx != null) {
      k.obj(cv, 'now', 'kz-demo-now'); base.now = { x: X(M.from), y: .13, w: .0025, h: y0 + .7 - .13, opacity: 0 };
      k.obj(cv, 'nowL', 'kz-demo-now-label', `当前 ${q(now)}`); base.nowL = { x: Math.min(Math.max(tx - .05, .21), .885), y: y0 + .705, w: .1, opacity: 0 };
    }
    const all = lanes.flatMap((ln, i) => ln.bars.map((br, j) => [ln, br, `b${i}_${j}`])), ms = lanes.flatMap((ln, i) => ln.milestones.map((m, j) => [ln, m, i, j]));
    const done = all.filter(([, br]) => now != null && br.e <= now).length, live = all.filter(([, br]) => now != null && br.s <= now && now < br.e).length;
    const past = ms.filter(([, m]) => now != null && m.t < now), ahead = ms.filter(([, m]) => now == null || m.t >= now);
    const keyMs = ms.find(([, m]) => m.key === M.focus) || ms.find(([, m]) => m.kind === 'submit') || ms.find(([, m]) => m.kind === 'approve') || ms[0];
    const fLane = M.focus ? lanes.findIndex(l => l.key === M.focus || l.bars.some(b => b.key === M.focus) || l.milestones.some(m => m.key === M.focus)) : (keyMs ? keyMs[2] : 0);
    const firstSub = ms.filter(([, m]) => m.kind === 'submit').sort((a, b) => a[1].t - b[1].t)[0];
    const phaseCount = M.used.map(pi => `${M.phases[pi]} ${all.filter(([, br]) => br.pi === pi).length} 段`).join('、');
    const msOn = ([ln, m, i, j]) => [[`m${i}_${j}`, { opacity: 1, scale: 1, cls: { 'is-ahead': now != null && m.t >= now } }], [`ml${i}_${j}`, { opacity: 1 }]];
    const focusCap = () => {
      const fm = ms.find(([, m]) => m.key === M.focus), fb = all.find(([, br]) => br.key === M.focus);
      if (fm) return `重点：${fm[0].name} ${fm[1].label}，${q(fm[1].t)}` + (now != null ? (fm[1].t >= now ? `，距当前 ${gap(fm[1].t - now)}` : '，已完成') : '');
      if (fb) return `重点：${fb[0].name} ${fb[1].phase} ${q(fb[1].s)}–${qe(fb[1].e)}`;
      const L = lanes[fLane]; return `重点：${L.name}，${L.bars.map(b => b.phase).join(' → ')}，到 ${qe(L.bars[L.bars.length - 1].e)}`;
    };
    const fms = ms.find(([, m]) => m.key === M.focus);
    const scenes = [
      { id: 'axis', caption: `${n} 条泳道，${C().qtext(M.from)} 到 ${C().qtext(M.to - 1)}，按${{ quarter: '季度', month: '月', day: '日' }[G]}排开`,
        set: over(base, { hd: { opacity: 1 }, ...Object.fromEntries(Object.keys(base).filter(id => /^(yr|gl|ln|lg)/.test(id)).map(id => [id, { opacity: 1 }])) }) },
      { id: 'phases', caption: `${all.length} 个阶段按时间铺开：${phaseCount}`, order: all.map(([, , id]) => id),
        set: Object.fromEntries(all.flatMap(([, br, id]) => [[id, { w: br.geo.x1 - br.geo.x0, opacity: 1 }], ...(base[id + 'p'] ? [[id + 'p', { opacity: 0 }]] : [])])) },
      { id: 'today', caption: now == null ? '没有标当前时点：全部按计划显示' : `当前 ${q(now)}：${done} 个阶段已完成、${live} 个进行中，当前线之后转为计划`,
        order: ['now', ...all.map(([, , id]) => id + 'p')],
        set: now == null ? {} : { now: { x: tx - .00125, opacity: 1 }, nowL: { opacity: 1 },
          ...Object.fromEntries(all.flatMap(([, br, id]) => base[id + 'p'] ? [[id, { w: Math.max(0, br.geo.cut - br.geo.x0), opacity: br.geo.cut > br.geo.x0 ? 1 : 0 }],
            [id + 'p', { w: br.geo.x1 - br.geo.cut, opacity: 1, fill: mix(col[br.pi]) }]] : [])) } },
      { id: 'milestones', caption: ms.length ? `${ms.length} 个里程碑：` + (now == null ? `最早 ${ms.slice().sort((a, b) => a[1].t - b[1].t)[0][1].label}` : `已过 ${past.length} 个，接下来是${ahead.length ? ` ${ahead.sort((a, b) => a[1].t - b[1].t)[0][0].name} ${ahead[0][1].label}（${q(ahead[0][1].t)}）` : '：无'}`) : '没有里程碑',
        order: ms.map(([, , i, j]) => `m${i}_${j}`), set: Object.fromEntries(ms.flatMap(msOn)) },
      { id: 'focus', caption: focusCap(),
        set: { band: { opacity: 1, y: Y(fLane) }, ...(fms ? { [`m${fms[2]}_${fms[3]}`]: { scale: 1.35 }, [`ml${fms[2]}_${fms[3]}`]: { cls: { 'is-on': true } } } : {}),
          ...Object.fromEntries(lanes.flatMap((ln, i) => i === fLane ? [] : [['ln' + i, { opacity: .5 }], ...ln.bars.map((_, j) => [`b${i}_${j}`, { opacity: .35 }]),
            ...ln.bars.filter((_, j) => base[`b${i}_${j}p`]).map(br => [`b${i}_${ln.bars.indexOf(br)}p`, { opacity: .35 }]),
            ...ln.milestones.flatMap((_, j) => [[`m${i}_${j}`, { opacity: .35 }], [`ml${i}_${j}`, { opacity: .45 }]])])) } },
    ];
    return mount(root, scenes, opt, 4, [
      { value: String(n), label: '适应症 / 研究' },
      ...(firstSub ? [{ value: q(firstSub[1].t), label: `首个递交（${firstSub[0].name}）` }] : [{ value: qe(M.to), label: '计划截止' }]),
      ...(now != null ? [{ value: `${past.length} / ${ms.length}`, label: '已过里程碑' }] : [])]);
  });
})(window);
