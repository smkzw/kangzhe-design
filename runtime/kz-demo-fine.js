/* Kangzhe 8.0 — fine-grained demonstrative forms (15 DEMO-02) on KZDemo.kit: one content job each, small enough to sit
   beside cards, so neighbouring pages that carry the same kind of content can be drawn different ways (15 DEMO-10).
   They are the flat counterparts of the flagship's cinematic stages (14 FLAG-06a): the same jobs, drawn as schematic
   marks, bars, dots and links that move scene by scene. Every number and caption is computed from the data (DEMO-04).
     waffle      completeness: one cell per item in a row per group → received filled → gaps outlined → one share bar
     funnel      attrition: equal bars narrow to each stage → each stage's loss leaves for the loss ledger → the largest lit
     shift       change: each item on its own scale, earlier bar → later bar → signed change → tallied better / worse
     milestones  timeline: track → milestone flags → the "now" pointer walks, passed ones ticked → the next one lit
     pathway     process: steps along a path → a case token walks it → the flagged step stops it → the hand-off note
   Requires kz-scenes.js, kz-demo.js and kz-icons.js. Styles: kz-glass.css "Demo stages". */
(function (global) {
  'use strict';
  const K = () => global.KZDemo.kit, def = (kind, fn) => global.KZDemo.define(kind, fn);
  const need = (ok, msg) => { if (!ok) throw Error(msg); };
  const pct = (a, b) => (b ? Math.round(a / b * 100) : 0);
  const num = (v, d = 0) => Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const asp = cv => (cv.clientWidth && cv.clientHeight ? cv.clientWidth / cv.clientHeight : 1.9);
  // first scene = the layout with some objects changed (a plain spread would drop the changed objects' geometry)
  const over = (base, ch) => { const o = { ...base }; for (const k in ch) o[k] = { ...base[k], ...ch[k] }; return o; };
  const mount = (root, scenes, opt, staticScene, facts) => { const s = K().S().mount(root, { scenes, loop: !!opt.loop, staticScene: opt.staticScene ?? staticScene }); s.facts = facts; return s; };

  /* ---------- waffle ----------
     data: { unit, groups: [{name, due, received}], note } — at most 60 items in all */
  def('waffle', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'waffle', d.note), g = d.groups || [], unit = d.unit || '份', A = asp(cv);
    need(g.length >= 2 && g.length <= 6, 'waffle 需要 2–6 组 groups：[{name, due, received}]');
    g.forEach(x => need(Number.isInteger(x.due) && x.due > 0 && Number.isInteger(x.received) && x.received >= 0 && x.received <= x.due, `waffle 组「${x.name}」的 due/received 不合法`));
    const due = k.sum(g.map(x => x.due)), rec = k.sum(g.map(x => x.received)), lack = due - rec, maxDue = Math.max(...g.map(x => x.due));
    need(due <= 60, 'waffle 最多 60 格（due 合计），更多时用 units 或 story');
    const x0 = .22, span = .46, step = span / maxDue, cw = Math.min(.045, step * .82), rowH = .62 / g.length, ry = i => .1 + i * rowH + (rowH - cw * A) / 2;
    const bs = Math.min(.9 / due, .05), bw = bs * .84, bx = (1 - bs * due) / 2, by = .82;
    const cells = []; g.forEach((x, gi) => { for (let j = 0; j < x.due; j++) cells.push({ gi, j, got: j < x.received }); });
    cells.forEach((c, i) => k.obj(cv, 'c' + i, 'kz-demo-mark'));
    g.forEach((x, i) => { k.obj(cv, 'n' + i, 'kz-demo-label is-left', x.name); k.obj(cv, 'r' + i, 'kz-demo-count'); });
    k.obj(cv, 'total', 'kz-demo-figure');
    // the share bar keeps received first, then the gaps, so its length reads as the overall share
    const order = [...cells.filter(c => c.got), ...cells.filter(c => !c.got)];
    const at = c => ({ x: x0 + c.j * step, y: ry(c.gi), w: cw });
    const base = Object.fromEntries(cells.map((c, i) => ['c' + i, { ...at(c), fill: k.SOFT }]));
    g.forEach((x, i) => { base['n' + i] = { x: .02, y: ry(i) + cw * A / 2 - .03, w: .19 }; base['r' + i] = { x: .72, y: ry(i) + cw * A / 2 - .03, w: .24, opacity: 0 }; });
    base.total = { x: .2, y: .02, w: .6, text: `应收 ${due} ${unit}，一格一${unit}` };
    const worst = g.map((x, i) => [x.due - x.received, i]).filter(([n]) => n > 0).sort((a, b) => b[0] - a[0]).map(([, i]) => g[i].name);
    const scenes = [
      { id: 'grid', caption: `${g.length} 组资料共应收 ${due} ${unit}，每行一组、一格一${unit}`, set: base },
      { id: 'fill', caption: `已收的 ${rec} ${unit}填色，空着的就是还没收到的`, order: cells.map((_, i) => 'c' + i),
        set: { ...Object.fromEntries(cells.map((c, i) => ['c' + i, c.got ? { fill: k.C('brand') } : {}])),
          ...Object.fromEntries(g.map((x, i) => ['r' + i, { opacity: 1, count: x.received, unit: ` / ${x.due} ${unit}` }])), total: { text: `已收 ${rec} / ${due} ${unit}` } } },
      { id: 'miss', caption: lack ? `缺 ${lack} ${unit}，集中在${worst.join('、')}` : `${g.length} 组全部收齐`,
        set: { ...Object.fromEntries(cells.map((c, i) => ['c' + i, c.got ? {} : { fill: '#fff', cls: { 'is-missing': true }, scale: 1.12 }])),
          ...Object.fromEntries(g.map((x, i) => ['r' + i, x.received < x.due ? { text: `缺 ${x.due - x.received} ${unit}`, cls: { 'is-risk': true } } : { opacity: .45 }])),
          total: { text: `缺口 ${lack} ${unit}`, cls: { 'is-risk': lack > 0 } } } },
      { id: 'share', caption: `排成一条看整体：已收 ${rec} ${unit}，占 ${pct(rec, due)}%`, order: order.map(c => 'c' + cells.indexOf(c)),
        set: { ...Object.fromEntries(order.map((c, q) => ['c' + cells.indexOf(c), { x: bx + q * bs, y: by, w: bw, scale: 1 }])),
          ...Object.fromEntries(g.flatMap((x, i) => [['n' + i, { opacity: .4 }], ['r' + i, { opacity: .4 }]])),
          total: { x: .2, y: by - .14, w: .6, text: `已收 ${rec} / ${due} ${unit} · ${pct(rec, due)}%`, cls: { 'is-risk': false } } } },
    ];
    return mount(root, scenes, opt, 3, [{ value: num(due), label: `应收（${unit}）` }, { value: num(rec), label: `已收（${unit}）` }, { value: num(lack), label: `缺口（${unit}）`, risk: lack > 0 }]);
  });

  /* ---------- funnel ----------
     data: { unit, stages: [{name, value}], note } — 3–6 stages, each no larger than the one before */
  def('funnel', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'funnel', d.note), st = d.stages || [], unit = d.unit || '例', n = st.length;
    need(n >= 3 && n <= 6, 'funnel 需要 3–6 级 stages：[{name, value}]');
    st.forEach((x, i) => need(Number.isFinite(x.value) && x.value >= 0 && (i === 0 || x.value <= st[i - 1].value), `funnel 第 ${i + 1} 级「${x.name}」须为非负且不大于上一级`));
    need(st[0].value > 0, 'funnel 第一级须大于 0');
    const v0 = st[0].value, cx = .42, W = .5, rowH = .78 / n, bh = rowH * .62, y = i => .06 + i * rowH, w = v => W * v / v0;
    const drop = st.map((x, i) => (i ? st[i - 1].value - x.value : 0)), worst = drop.indexOf(Math.max(...drop));
    st.forEach((x, i) => { k.obj(cv, 'b' + i, 'kz-demo-bar'); k.obj(cv, 'n' + i, 'kz-demo-label is-left', x.name); k.obj(cv, 'v' + i, 'kz-demo-count'); if (i) { k.obj(cv, 'l' + i, 'kz-demo-bar is-gap'); k.obj(cv, 'd' + i, 'kz-demo-count is-risk'); } });
    k.obj(cv, 'ledger', 'kz-demo-tray', '流失');
    const base = { ledger: { x: .71, y: .04, w: .28, h: .9, opacity: 0 } };
    st.forEach((x, i) => {
      base['b' + i] = { x: cx - W / 2, y: y(i), w: W, h: bh, opacity: 0 };
      base['n' + i] = { x: .01, y: y(i) + bh / 2 - .03, w: .15 };
      base['v' + i] = { x: cx - .1, y: y(i) + bh / 2 - .03, w: .2, count: 0, unit: ` ${unit}`, opacity: 0 };
      if (i) { base['l' + i] = { x: cx - w(st[i - 1].value) / 2, y: y(i), w: Math.max(.004, (w(st[i - 1].value) - w(x.value)) / 2), h: bh, opacity: 0 };
        base['d' + i] = { x: .79, y: y(i) + bh / 2 - .03, w: .195, opacity: 0 }; }
    });
    const slot = i => ({ x: .725, y: y(i) + bh * .2, w: .055, h: bh * .6 });
    const scenes = [
      { id: 'start', caption: `${st[0].name} ${num(v0)} ${unit}，每一级都从这里出发`, set: over(base, { ...Object.fromEntries(st.map((x, i) => ['b' + i, { opacity: i ? .25 : 1 }])), v0: { opacity: 1, count: v0 } }) },
      { id: 'narrow', caption: `逐级收窄：${st.map(x => `${x.name} ${num(x.value)}`).join(' → ')}`, order: st.map((_, i) => 'b' + i),
        set: Object.fromEntries(st.flatMap((x, i) => [['b' + i, { x: cx - w(x.value) / 2, w: w(x.value), opacity: 1 }], ['v' + i, { opacity: 1, count: x.value }]])) },
      { id: 'drop', caption: `每级流失的人数移到右侧台账：合计流失 ${num(v0 - st[n - 1].value)} ${unit}`, order: st.slice(1).map((_, i) => 'l' + (i + 1)),
        set: { ledger: { opacity: 1 }, ...Object.fromEntries(st.slice(1).flatMap((x, j) => { const i = j + 1;
          return [['l' + i, { from: { ...base['l' + i], opacity: 0 }, ...slot(i), opacity: 1 }], ['d' + i, { opacity: 1, text: `−${num(drop[i])}（${pct(drop[i], st[i - 1].value)}%）` }]]; })) } },
      { id: 'focus', caption: `流失最多在「${st[worst - 1].name} → ${st[worst].name}」：${num(drop[worst])} ${unit}，占上一级 ${pct(drop[worst], st[worst - 1].value)}%`,
        set: Object.fromEntries(st.slice(1).flatMap((x, j) => { const i = j + 1, hot = i === worst;
          return [['l' + i, { opacity: hot ? 1 : .35, scale: hot ? 1.15 : 1 }], ['d' + i, { opacity: hot ? 1 : .45 }], ['b' + i, { opacity: hot || i === worst - 1 ? 1 : .55 }]]; })) },
    ];
    return mount(root, scenes, opt, 3, [{ value: num(v0), label: `${st[0].name}（${unit}）` }, { value: num(st[n - 1].value), label: `${st[n - 1].name}（${unit}）` }, { value: `${pct(st[n - 1].value, v0)}%`, label: '留存' }, { value: num(drop[worst]), label: '最大一级流失', risk: true }]);
  });

  /* ---------- shift ----------
     data: { unit, from, to, items: [{name, before, after, good: 'up'|'down', decimals?}], decimals?, note } — 2–6 items,
     each drawn on its own scale (its larger value fills the bar track) */
  def('shift', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'shift', d.note), it = d.items || [], n = it.length, unit = d.unit || '';
    need(n >= 2 && n <= 6, 'shift 需要 2–6 项 items：[{name, before, after, good}]');
    need(d.from && d.to, 'shift 需要 from 与 to（两个时点的名称）');
    it.forEach(x => need(Number.isFinite(x.before) && Number.isFinite(x.after) && x.before >= 0 && x.after >= 0 && ['up', 'down'].includes(x.good), `shift「${x.name}」需要非负 before/after 与 good: up|down`));
    const dec = x => (Number.isInteger(x.decimals) ? x.decimals : Number.isInteger(d.decimals) ? d.decimals : 0);
    const better = x => (x.good === 'up' ? x.after > x.before : x.after < x.before), worse = x => x.after !== x.before && !better(x);
    const rowH = .7 / n, y = i => .14 + i * rowH, bh = Math.min(.07, rowH * .42), X = .24, W = .36, w = (x, v) => W * v / (Math.max(x.before, x.after) || 1);
    k.obj(cv, 'hf', 'kz-demo-head', `灰 = ${d.from} · 橙 = ${d.to}（每项各自刻度）`);
    it.forEach((x, i) => { k.obj(cv, 'n' + i, 'kz-demo-label is-left', x.name); k.obj(cv, 'g' + i, 'kz-demo-bar is-comparator'); k.obj(cv, 'b' + i, 'kz-demo-bar'); k.obj(cv, 'v' + i, 'kz-demo-count'); k.obj(cv, 's' + i, 'kz-demo-mark-sign'); });
    const nb = it.filter(better).length, nw = it.filter(worse).length;
    k.obj(cv, 'binB', 'kz-demo-tray', `改善 ${nb} 项`); k.obj(cv, 'binW', 'kz-demo-tray', `变差 ${nw} 项`);
    const base = { hf: { x: .02, y: .02, w: .7 }, binB: { x: .8, y: .12, w: .18, h: .36, opacity: 0 }, binW: { x: .8, y: .54, w: .18, h: .36, opacity: 0 } };
    it.forEach((x, i) => Object.assign(base, {
      ['n' + i]: { x: .02, y: y(i) + bh / 2 - .03, w: .21 }, ['g' + i]: { x: X, y: y(i) + bh * .2, w: w(x, x.before), h: bh * .6, opacity: 0 },
      ['b' + i]: { x: X, y: y(i), w: w(x, x.before), h: bh, fill: '#B9C2CC' }, ['v' + i]: { x: X + W + .01, y: y(i) + bh / 2 - .03, w: .12, count: x.before, decimals: dec(x), unit },
      ['s' + i]: { x: X + W + .13, y: y(i) + bh / 2 - .03, w: .1, opacity: 0 } }));
    let qb = 0, qw = 0;
    const tally = Object.fromEntries(it.map((x, i) => { if (!worse(x) && !better(x)) return ['s' + i, { opacity: .4 }];
      const b = better(x), q = b ? qb++ : qw++; return ['s' + i, { x: .81, y: (b ? .2 : .62) + q * .06, w: .16 }]; }));
    const sign = x => { const v = x.after - x.before; return `${v > 0 ? '+' : v < 0 ? '−' : '±'}${num(Math.abs(v), dec(x))}${unit}`; };
    const scenes = [
      { id: 'before', caption: `${d.from}：${it.map(x => `${x.name} ${num(x.before, dec(x))}${unit}`).join('，')}`, set: base },
      { id: 'after', caption: `变到 ${d.to}：灰条留住 ${d.from} 的位置，橙条是现在`, order: it.map((_, i) => 'b' + i),
        set: Object.fromEntries(it.flatMap((x, i) => [['g' + i, { opacity: 1 }], ['b' + i, { w: w(x, x.after), fill: k.C('brand') }], ['v' + i, { count: x.after }]])) },
      { id: 'delta', caption: `升降按好坏着色：改善 ${nb} 项${nw ? `，变差 ${nw} 项` : ''}`,
        set: Object.fromEntries(it.map((x, i) => ['s' + i, { opacity: 1, text: sign(x), cls: { 'is-diff': worse(x) } }])) },
      { id: 'tally', caption: nw ? `${nb} 项改善、${nw} 项变差：变差的是${it.filter(worse).map(x => x.name).join('、')}` : `${nb} 项全部改善`, order: it.map((_, i) => 's' + i),
        set: { binB: { opacity: 1 }, binW: { opacity: nw ? 1 : .35 }, ...tally } },
    ];
    return mount(root, scenes, opt, 3, [{ value: String(nb), label: '改善（项）' }, { value: String(nw), label: '变差（项）', risk: nw > 0 }]);
  });

  /* ---------- milestones ----------
     data: { now, nowLabel?, items: [{when, name, owner?}], note } — now is how far along the list (0 … n−1, may be fractional) */
  def('milestones', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'milestones', d.note), it = d.items || [], n = it.length, now = Number(d.now), A = asp(cv);
    need(n >= 3 && n <= 7, 'milestones 需要 3–7 个 items：[{when, name, owner?}]');
    need(Number.isFinite(now) && now >= 0 && now <= n - 1, `milestones 的 now 须在 0 到 ${n - 1} 之间`);
    const ty = .64, X = i => .08 + i * (.84 / (n - 1)), nowX = .08 + now * (.84 / (n - 1)), next = Math.min(n - 1, Math.floor(now) + 1), passed = it.filter((_, i) => i <= now).length;
    const L = k.links(cv); L.path('rail', k.pts([[.04, ty], [.96, ty]]), 'is-rail'); L.path('prog', k.pts([[X(0), ty], [nowX, ty]]), 'is-trace');
    it.forEach((_, i) => L.path('k' + i, k.pts([[X(i), .31], [X(i), ty - .035]]), 'is-rail'));
    const fw = Math.min(.16, .84 / (n - 1) - .015), dw = .022;
    it.forEach((m, i) => { k.obj(cv, 'f' + i, 'kz-demo-flag', m.when); k.obj(cv, 'm' + i, 'kz-demo-note is-lines', m.name + (m.owner ? `\n${m.owner}` : '')); k.obj(cv, 'd' + i, 'kz-demo-dot'); });
    k.obj(cv, 'band', 'kz-demo-band'); k.obj(cv, 'ph', 'kz-demo-playhead'); k.obj(cv, 'pl', 'kz-demo-count is-risk', d.nowLabel || '当前');
    const base = { band: { x: X(0) - fw / 2, y: .17, w: .004, h: .66, opacity: 0 }, rail: { draw: 0 }, prog: { draw: 0, opacity: 0, stroke: k.C('brand') }, ph: { x: .04, y: ty - .2, w: .004, h: .26, opacity: 0 }, pl: { x: .01, y: ty - .27, w: .12, opacity: 0 } };
    it.forEach((m, i) => Object.assign(base, { ['d' + i]: { x: X(i) - dw / 2, y: ty - dw * A / 2, w: dw, opacity: 0 },
      ['k' + i]: { draw: 0, stroke: '#C9CFD6' }, ['f' + i]: { x: .02, y: .24, w: fw, opacity: 0 }, ['m' + i]: { x: X(i) - fw / 2, y: ty + .06, w: fw, opacity: 0 } }));
    const scenes = [
      { id: 'track', caption: `${it[0].when} 到 ${it[n - 1].when}，${n} 个节点`, set: over(base, { rail: { draw: 1 }, ...Object.fromEntries(it.map((_, i) => ['d' + i, { opacity: 1 }])) }) },
      { id: 'flags', caption: `节点依次是：${it.map(m => m.name).join('、')}`, order: it.flatMap((_, i) => ['f' + i, 'm' + i]),
        set: Object.fromEntries(it.flatMap((m, i) => [['f' + i, { x: X(i) - fw / 2, opacity: 1 }], ['k' + i, { draw: 1 }], ['m' + i, { opacity: 1 }]])) },
      { id: 'run', caption: `走到${d.nowLabel || '当前'}：已过 ${passed} 个节点`,
        set: { band: { opacity: 1, w: nowX - X(0) + fw / 2 }, prog: { opacity: 1, draw: 1 }, ph: { opacity: 1, x: nowX - .002 }, pl: { opacity: 1, x: nowX - .06 },
          ...Object.fromEntries(it.map((_, i) => ['d' + i, i <= now ? { cls: { 'is-ok': true }, scale: 1.25 } : {}])) } },
      { id: 'next', caption: `下一个节点：${it[next].when} ${it[next].name}${it[next].owner ? `（${it[next].owner}）` : ''}`,
        set: Object.fromEntries(it.flatMap((m, i) => i === next ? [['f' + i, { y: .18, scale: 1.12 }], ['k' + i, { stroke: k.C('risk') }], ['m' + i, { cls: { 'is-risk': true } }], ['d' + i, { cls: { 'is-risk': true }, scale: 1.4 }]]
          : [['f' + i, { opacity: .45 }], ['m' + i, { opacity: .45 }]])) },
    ];
    return mount(root, scenes, opt, 3, [{ value: `${passed} / ${n}`, label: '已过节点' }, { value: it[next].when, label: `下一节点：${it[next].name}` }]);
  });

  /* ---------- pathway ----------
     data: { steps: [{name, note?, icon?, alert?}], caseLabel?, note } — 3–7 steps; one step may be flagged (alert) */
  def('pathway', (root, d, opt) => {
    const k = K(), cv = k.frame(root, 'pathway', d.note), st = d.steps || [], n = st.length, A = asp(cv);
    need(n >= 3 && n <= 7, 'pathway 需要 3–7 步 steps：[{name, note?, icon?, alert?}]');
    const ai = st.findIndex(s => s.alert); need(st.filter(s => s.alert).length <= 1, 'pathway 最多一步带 alert');
    const X = i => .08 + i * (.84 / (n - 1)), Y = i => (i % 2 ? .48 : .2), iw = Math.min(.09, .8 / n), lw = Math.min(.17, .84 / (n - 1) - .01), lx = i => Math.min(.995 - lw, Math.max(.005, X(i) - lw / 2));
    const L = k.links(cv); L.path('path', k.pts(st.map((_, i) => [X(i), Y(i)])), 'is-rail'); L.path('walk', k.pts(st.slice(0, ai >= 0 ? ai + 1 : n).map((_, i) => [X(i), Y(i)])), 'is-trace');
    st.forEach((s, i) => { k.icon(cv, 'i' + i, s.icon || 'doc'); k.obj(cv, 'l' + i, 'kz-demo-label', s.name); if (s.note) k.obj(cv, 't' + i, 'kz-demo-note' + (s.alert ? ' is-risk' : ''), s.note); });
    const cw = .12; k.obj(cv, 'case', 'kz-demo-case', d.caseLabel || '示例资料');
    k.obj(cv, 'out', 'kz-demo-tray', ai >= 0 ? `退回补齐 · ${st[ai].name}` : '全部通过');
    const sq = i => ({ x: X(i) - iw / 2, y: Y(i) - iw * A / 2, w: iw });
    const base = { path: { draw: 0 }, walk: { draw: 0, opacity: 0, stroke: k.C('brand') }, case: { x: X(0) - cw / 2, y: Y(0) - iw * A / 2 - .09, w: cw, opacity: 0 }, out: { x: .2, y: .74, w: .6, h: .2, opacity: 0 } };
    st.forEach((s, i) => Object.assign(base, { ['i' + i]: { ...sq(i), opacity: 0 }, ['l' + i]: { x: lx(i), y: Y(i) + iw * A / 2 + .02, w: lw, opacity: 0 },
      ...(s.note ? { ['t' + i]: { x: lx(i), y: Y(i) + iw * A / 2 + .085, w: lw, opacity: 0 } } : {}) }));
    const end = ai >= 0 ? ai : n - 1, caseAt = i => ({ x: X(i) - cw / 2, y: Y(i) - iw * A / 2 - .09, w: cw });
    const scenes = [
      { id: 'path', caption: `${n} 步：${st.map(s => s.name).join(' → ')}`, order: st.flatMap((_, i) => ['i' + i, 'l' + i]),
        set: over(base, { path: { draw: 1 }, ...Object.fromEntries(st.flatMap((s, i) => [['i' + i, { opacity: 1 }], ['l' + i, { opacity: 1 }], ...(s.note ? [['t' + i, { opacity: 1 }]] : [])])) }) },
      { id: 'walk', caption: ai >= 0 ? `${d.caseLabel || '示例资料'}一步步走到「${st[ai].name}」` : `${d.caseLabel || '示例资料'}走完全部 ${n} 步`,
        set: { case: { opacity: 1, ...caseAt(end), via: st.slice(1, end).map((_, j) => [caseAt(j + 1).x, caseAt(j + 1).y]) }, walk: { opacity: 1, draw: 1 },
          ...Object.fromEntries(st.slice(0, end + 1).map((_, i) => ['i' + i, { cls: { 'is-on': true } }])) } },
      { id: 'stop', caption: ai >= 0 ? `在「${st[ai].name}」停下：${st[ai].note || '这一步不通过'}` : `最后一步「${st[n - 1].name}」完成`,
        set: ai >= 0 ? { ['i' + ai]: { cls: { 'is-on': false, 'is-fail': true }, scale: 1.18 }, ['l' + ai]: { cls: { 'is-risk': true } }, ...Object.fromEntries(st.map((_, i) => i > ai ? ['i' + i, { opacity: .35 }] : ['l' + i, {}])) }
          : Object.fromEntries(st.map((_, i) => ['i' + i, { cls: { 'is-ok': true } }])) },
      { id: 'out', caption: ai >= 0 ? `退回补齐后从「${st[ai].name}」重新进入，后续 ${n - ai - 1} 步等待` : `${n} 步全部通过，归档`, order: ['case', 'out'],
        set: { out: { opacity: 1 }, case: { x: .5 - cw / 2, y: .86, w: cw } } },
    ];
    return mount(root, scenes, opt, 3, [{ value: String(n), label: '步骤' }, ai >= 0 ? { value: st[ai].name, label: '卡在这一步', risk: true } : { value: '通过', label: '结果' }]);
  });
})(window);
