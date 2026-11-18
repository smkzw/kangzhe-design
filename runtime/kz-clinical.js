/* Kangzhe 8.0 — clinical scenario data contracts (shared by the regular demo forms in kz-demo-clinical.js and the flagship
   stages in kz-flagship-stages.js). The rules mirror tools/kz_layouts/diagram_clinical.py, which checks the same data
   for the static page templates, so one scenario file is accepted or rejected the same way by every product.
     KZClinical.safety(data) → {arms, rows:[{…row, depth, pct[], diff}], ti, ci, flag, focus, unit, under(row)}
     KZClinical.exposure(data) → {bands, groups, totals[], py, targets[], met[], focus, unit, max}
     KZClinical.efficacy(data) → {arms, comp, treat[], rows:[{…, pct[], cmp:{treat key: {diff, ci, p, verdict}}}], types, scale, focus, wins, tests}
     KZClinical.landscape(data) → {stages, assets:[{…, idx, si}], order, rank:{metric: keys}, best, max, metrics, ours, focus}
     KZClinical.flowScale(model, x0, x1, minw) → t ↦ x (piecewise week scale of a trial flow, diagram_scenes.flow_scale)
     KZClinical.trialflow(data) → {start, at, end, final, trunk, after, split, ratio, arms:[{…, rows, sub}], leaves:[{…, parent, row, path}], endpoints, subs, focus, unit, n, ticks}
     KZClinical.program(data) → {from, to, today, phases, used, lanes:[{…lane, bars:[{…, s, e, pi}], milestones:[{…, kind, t}]}], focus, kinds}
   Load after kz-tokens.js; no other dependency. */
(function (global) {
  'use strict';
  const need = (ok, msg) => { if (!ok) throw Error(msg); };
  const num = (v, d = 0) => Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
  /* safety contract (same rules as diagram_clinical.safety_model): arms 2–4 with N, rows 3–10 with one count per arm,
     a child never above its parent, depth ≤ 3; difference = compare[0] − compare[1] (default first treat − first comparator) */
  function safetyModel(d) {
    const arms = d.arms || [], rows = d.rows || [];
    need(arms.length >= 2 && arms.length <= 4, '安全性总览需要 2–4 个组 arms：[{name, n, role}]');
    arms.forEach(a => need(Number.isInteger(a.n) && a.n > 0, `组「${a.name}」的 n 须为正整数`));
    need(rows.length >= 3 && rows.length <= 10, '安全性总览需要 3–10 行 rows');
    const keys = new Map(rows.map(r => [r.key, r])); need(keys.size === rows.length, 'rows 的 key 不能重复');
    const out = rows.map(r => {
      const v = r.values || [];
      need(v.length === arms.length && v.every(x => Number.isInteger(x) && x >= 0), `「${r.label}」的 values 须是每组一个非负整数`);
      v.forEach((x, i) => need(x <= arms[i].n, `「${r.label}」在「${arms[i].name}」的例数 ${x} 超过该组 N=${arms[i].n}`));
      let depth = 0, p = r.parent;
      while (p) {
        need(keys.has(p), `「${r.label}」的 parent「${p}」不存在`);
        need(v.every((x, i) => x <= keys.get(p).values[i]), `「${r.label}」的例数不能大于上级「${keys.get(p).label}」`);
        depth++; p = keys.get(p).parent; need(depth <= 3, 'rows 的层级最多 3 级（或 parent 成环）');
      }
      return { ...r, depth, pct: v.map((x, i) => x / arms[i].n * 100) };
    });
    let ti = arms.findIndex(a => a.role === 'treat'), ci = arms.findIndex(a => a.role === 'comparator');
    if (ti < 0) ti = 0;
    if (d.compare) { [ti, ci] = d.compare; need(ti >= 0 && ci >= 0 && ti < arms.length && ci < arms.length && ti !== ci, 'compare 须是两个不同组的序号 [组, 参照组]'); }
    need(ci >= 0, '安全性总览需要一个对照组（role: comparator）或 compare');
    out.forEach(r => { r.diff = r.pct[ti] - r.pct[ci]; });
    need(!d.focus || keys.has(d.focus), `focus「${d.focus}」不在 rows 里`);
    const root = out[0]; need(root.depth === 0, 'rows 第一行须是顶层类别（例如任何 TEAE）');
    const under = r => { let p = r.parent; while (p) { if (p === root.key) return true; p = keys.get(p).parent; } return false; };
    return { arms, rows: out, ti, ci, flag: d.flag_pp ?? 5, focus: d.focus, unit: d.unit || '例', under };
  }
  const dtext = v => (Math.abs(v) < .05 ? '±0.0' : `${v > 0 ? '+' : '−'}${num(Math.abs(v), 1)}`);
  const npct = (n, p) => `${n} (${num(p, 1)}%)`;
  /* clinical development plan (same rules, order and messages as diagram_clinical.program_model): times written as
     quarters '2026Q3', months '2026-08' or days '2026-08-15' (bar ends inclusive in their unit); internally continuous
     quarter units [start, end) (year × 4 + quarter − 1, days as a fraction of their quarter — the KZGantt model);
     granularity quarter|month|day (default: the finest unit a bar is written in); two-level lanes (parent / collapsed);
     optional layers status / progress / baseline / icon (absent data draws nothing); past = before today */
  const PHASES = ['I 期', 'II 期', 'III 期', '注册', '上市后'];
  const MS_KINDS = { start: '首例入组', readout: '结果读出', submit: '递交', approve: '获批', other: '里程碑' };
  const STATUSES = { planned: '计划', active: '进行中', done: '已完成', delayed: '延迟', risk: '风险' };
  const GRANS = ['quarter', 'month', 'day'];
  const DAY = 86400000, utc = (y, m, d) => Date.UTC(y, m - 1, d);
  function tspan(s, what) {
    const v = String(s ?? ''); let m;
    if ((m = /^(\d{4})Q([1-4])$/.exec(v))) { const i = +m[1] * 4 + +m[2] - 1; return [i, i + 1, 'quarter']; }
    if ((m = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(v))) { const y = +m[1], mo = +m[2], i = y * 4 + Math.floor((mo - 1) / 3), k = (mo - 1) % 3; return [i + k / 3, i + (k + 1) / 3, 'month']; }
    if ((m = /^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.exec(v))) {
      const y = +m[1], mo = +m[2], d = +m[3], t = new Date(utc(y, mo, d));
      need(t.getUTCMonth() === mo - 1 && t.getUTCDate() === d, `${what}「${s}」不是有效日期`);
      const q0 = utc(y, Math.floor((mo - 1) / 3) * 3 + 1, 1), q1 = mo > 9 ? utc(y + 1, 1, 1) : utc(y, Math.floor((mo - 1) / 3) * 3 + 4, 1);
      const n = Math.round((q1 - q0) / DAY), off = Math.round((t - q0) / DAY), i = y * 4 + Math.floor((mo - 1) / 3);
      return [i + off / n, i + (off + 1) / n, 'day'];
    }
    need(false, `${what}「${s ?? 'None'}」须写成季度、月份或日期，例如 2026Q3、2026-08、2026-08-15`);
  }
  const qindex = (s, what) => { const [a, , u] = tspan(s, what); need(u === 'quarter', `${what}「${s ?? 'None'}」须写成年份加季度，例如 2026Q3`); return a; };
  const qtext = i => { i = Math.floor(i); return `${Math.floor(i / 4)}Q${(i % 4 + 4) % 4 + 1}`; };
  function ttext(v, gran) {
    const i = Math.floor(v), y = Math.floor(i / 4), q = (i % 4 + 4) % 4;
    if (gran === 'quarter') return `${y}Q${q + 1}`;
    if (gran === 'month') return `${y}-${String(q * 3 + Math.min(2, Math.floor((v - i) * 3 + 1e-9)) + 1).padStart(2, '0')}`;
    const q0 = utc(y, q * 3 + 1, 1), q1 = q === 3 ? utc(y + 1, 1, 1) : utc(y, q * 3 + 4, 1);
    return new Date(q0 + Math.floor((v - i) * Math.round((q1 - q0) / DAY) + 1e-9) * DAY).toISOString().slice(0, 10);
  }
  const isNum = x => typeof x === 'number' && Number.isFinite(x);
  function programModel(d, today) {
    let a = tspan(d.from, 'from')[0], b = tspan(d.to, 'to')[1];
    a = Math.floor(a); b = Math.ceil(b);
    need(b - a >= 2 && b - a <= 40, '时间轴 from–to 须覆盖 2–40 个季度（含首尾）');
    let gran = d.granularity ?? null;
    need(gran === null || GRANS.includes(gran), 'granularity 须是 quarter、month、day 之一');
    const phases = d.phases && d.phases.length ? d.phases : PHASES, ncol = (global.KZ_TOKENS?.charts?.phases || PHASES).length;
    need(phases.length >= 1 && phases.length <= ncol, `phases 须是 1–${ncol} 个阶段名`);
    const lanes = d.lanes || [];
    need(lanes.length >= 1 && lanes.length <= 24, '临床开发计划需要 1–24 条泳道 lanes');
    const icons = new Set(global.KZIcons?.names || []);
    const keys = new Set(), units = [], uniq = k => { need(k && !keys.has(k), `key「${k ?? 'None'}」缺失或重复`); keys.add(k); };
    const inside = (s0, e0, what) => need(a <= s0 && s0 < e0 && e0 <= b, `${what}须在 from–to 之内，且结束不早于开始`);
    const out = [], kids = {};
    for (const ln of lanes) {
      uniq(ln.key); need(String(ln.name ?? '').trim(), '泳道 name 不能为空');
      const par = ln.parent ?? null;
      if (par !== null) {
        const prev = out[out.length - 1], top = prev && (prev.parent == null ? prev.key : prev.parent);
        need(par === top, `泳道「${ln.name}」的 parent 须是紧挨在它上面的上级泳道（只有两级）`);
        (kids[par] = kids[par] || []).push(ln.key);
      }
      const bars = (ln.bars || []).map(br => {
        uniq(br.key); need(phases.includes(br.phase), `「${ln.name}」的阶段「${br.phase ?? 'None'}」不在 phases 里`);
        const what = `「${ln.name} · ${br.phase}」`;
        const [s0, , u0] = tspan(br.start, what + '的开始'), [, e0, u1] = tspan(br.end, what + '的结束');
        inside(s0, e0, what); units.push(u0, u1);
        const o = { ...br, s: s0, e: e0, pi: phases.indexOf(br.phase) };
        if (br.color != null) need(/^#[0-9A-Fa-f]{6}$/.test(String(br.color)), `${what}的 color 须是 #RRGGBB`);
        if (br.status != null) need(br.status in STATUSES, `${what}的 status 须是 ${Object.keys(STATUSES).join('、')} 之一`);
        if (br.progress != null) need(isNum(br.progress) && br.progress >= 0 && br.progress <= 100, `${what}的 progress 须是 0–100 的数`);
        if (br.baseline != null) {
          const bl = br.baseline; need(typeof bl === 'object' && !Array.isArray(bl), `${what}的 baseline 须写成 {start, end}`);
          const [bs, , v0] = tspan(bl.start, what + '的原计划开始'), [, be, v1] = tspan(bl.end, what + '的原计划结束');
          inside(bs, be, what + '的原计划'); units.push(v0, v1); o.bs = bs; o.be = be;
        }
        return o;
      });
      bars.sort((p, q) => p.s - q.s);
      bars.slice(1).forEach((q, i) => need(q.s >= bars[i].e, `「${ln.name}」的「${bars[i].phase}」与「${q.phase}」时间重叠；源材料的日期照原样写，不要为消除重叠改日期：同一泳道的阶段须前后相接，交叠或并行的研究（如 II 期未结束时 III 期已启动）拆成子泳道（parent 指向上级泳道）`));
      const ms = (ln.milestones || []).map(m => {
        uniq(m.key); need(String(m.label ?? '').trim(), `「${ln.name}」有里程碑缺 label`);
        const kind = 'kind' in m ? m.kind : 'other'; need(kind in MS_KINDS, `里程碑「${m.label}」的 kind 须是 ${Object.keys(MS_KINDS).join('、')} 之一`);
        const ic = m.icon ?? null; need(ic === null || ic in MS_KINDS || icons.has(ic), `里程碑「${m.label}」的 icon「${ic}」不是里程碑图形或图标库里的名字`);
        const [t0, t1] = tspan(m.at, `里程碑「${m.label}」的时间`); need(a <= t0 && t0 < b, `里程碑「${m.label}」不在 from–to 之内`);
        const o = { ...m, kind, t: t0, tw: t1 - t0 };
        if (m.baseline != null) {
          const [u0, u1] = tspan(m.baseline, `里程碑「${m.label}」的原计划时间`);
          need(a <= u0 && u0 < b, `里程碑「${m.label}」的原计划时间不在 from–to 之内`); o.bt = u0; o.btw = u1 - u0;
        }
        return o;
      });
      need(ms.length <= 6, `「${ln.name}」的里程碑超过 6 个；多适应症总图只放关键性里程碑，细化节点放单适应症页`);
      out.push({ ...ln, bars, milestones: ms.sort((p, q) => p.t - q.t), depth: par !== null ? 1 : 0 });
    }
    for (const ln of out) {
      ln.children = kids[ln.key] || [];
      need(!(ln.collapsed && !ln.children.length), `泳道「${ln.name}」没有下级泳道，不能 collapsed`);
      need(ln.bars.length || ln.children.length, `泳道「${ln.name}」至少要有一个阶段 bars`);
    }
    const fin = units.reduce((x, u) => Math.max(x, GRANS.indexOf(u)), 0);
    if (gran === null) gran = GRANS[fin];
    else need(fin <= GRANS.indexOf(gran), `阶段的起止写得比 granularity「${gran}」更细；改 granularity，或把起止写成${gran === 'quarter' ? '季度' : '月份'}`);
    const by = Object.fromEntries(out.map(l => [l.key, l]));
    for (const ln of out) {
      if (!(ln.collapsed && ln.children.length)) continue;
      const ch = ln.children.map(k => by[k]);
      if (!ln.bars.length) {
        const seg = [], mk = (pi, c) => ({ key: `${ln.key}~${pi}~${seg.length}`, phase: phases[pi], pi, s: c[0], e: c[1], summary: true });
        for (const pi of [...new Set(ch.flatMap(c => c.bars.map(r => r.pi)))].sort((p, q) => p - q)) {
          const iv = ch.flatMap(c => c.bars.filter(r => r.pi === pi).map(r => [r.s, r.e])).sort((p, q) => p[0] - q[0] || p[1] - q[1]);
          let cur = [...iv[0]];
          for (const [s0, e0] of iv.slice(1)) { if (s0 <= cur[1]) cur[1] = Math.max(cur[1], e0); else { seg.push(mk(pi, cur)); cur = [s0, e0]; } }
          seg.push(mk(pi, cur));
        }
        ln.summary = seg.sort((p, q) => p.s - q.s || p.pi - q.pi);
      }
      const major = ch.flatMap(c => c.milestones.filter(m => m.major)), up = major.length ? major : ch.flatMap(c => c.milestones.filter(m => m.kind === 'submit' || m.kind === 'approve'));
      ln.summary_ms = up.sort((p, q) => p.t - q.t).slice(0, 6);
    }
    const hidden = new Set(out.filter(l => l.collapsed).flatMap(l => l.children)), visible = out.filter(l => !hidden.has(l.key));
    need(visible.length <= 12, '同时显示的泳道超过 12 条；收起一些上级泳道（collapsed），或拆成两页');
    let tv = d.today;
    if (tv === 'auto') { const t = today || new Date(); tv = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`; }
    let now = null, tw = null;
    if (tv) { const [t0, t1] = tspan(tv, 'today'); now = t0; tw = t1 - t0; need(a <= now && now < b, 'today 不在 from–to 之内'); }
    need(!d.focus || keys.has(d.focus), `focus「${d.focus}」不是任何泳道、阶段或里程碑的 key`);
    const used = [...new Set(visible.flatMap(l => (l.bars.length ? l.bars : l.summary || []).map(r => r.pi)))].sort((p, q) => p - q);
    const allm = visible.flatMap(l => [...l.milestones, ...(l.summary_ms || [])]);
    const layers = { status: visible.some(l => l.bars.some(r => r.status)), progress: visible.some(l => l.bars.some(r => r.progress != null)),
      baseline: visible.some(l => l.bars.some(r => 'bs' in r)) || allm.some(m => 'bt' in m), levels: out.some(l => l.children.length) };
    const kinds = Object.keys(MS_KINDS).filter(k => allm.some(m => m.kind === k));
    return { from: a, to: b, today: now, today_w: tw, granularity: gran, phases, used, lanes: out, visible, focus: d.focus || null, layers, kinds };
  }
  /* exposure summary (same rules, order and messages as diagram_scenes.exposure_model): cumulative duration bands 2–5
     (each band a subset of the one before, so counts never rise along a row), groups 1–8, optional patient-years,
     targets per band (e.g. ICH E1); totals and target status are computed */
  const isInt = v => Number.isInteger(v);
  function exposureModel(d) {
    const bands = d.bands || [], groups = d.groups || [];
    need(bands.length >= 2 && bands.length <= 5, '暴露汇总需要 2–5 个暴露时长档 bands：[{key, label}]');
    const bk = bands.map(b => b.key); need(new Set(bk).size === bk.length, 'bands 的 key 不能重复');
    need(groups.length >= 1 && groups.length <= 8, '暴露汇总需要 1–8 个组 groups（适应症或研究）');
    const gk = groups.map(g => g.key); need(new Set(gk).size === gk.length, 'groups 的 key 不能重复');
    const out = groups.map(g => {
      const v = g.values || [];
      need(v.length === bands.length && v.every(x => isInt(x) && x >= 0), `「${g.name}」的 values 须是每个时长档一个非负整数`);
      need(v.every((x, i) => i === 0 || x <= v[i - 1]), `「${g.name}」的暴露例数须随时长档递减或持平（长档是短档的子集）`);
      need(g.py == null || (typeof g.py === 'number' && g.py >= 0), `「${g.name}」的 py（人年）须是非负数`);
      return { ...g };
    });
    const tg = d.targets || {};
    for (const [k, t] of Object.entries(tg)) { need(bk.includes(k), `targets 的「${k}」不是 bands 的 key`); need(isInt(t) && t > 0, 'targets 的值须是正整数'); }
    need(d.focus == null || gk.includes(d.focus), `focus「${d.focus}」不在 groups 里`);
    const totals = bands.map((_, i) => out.reduce((a, g) => a + g.values[i], 0));
    const py = out.every(g => g.py != null) ? out.reduce((a, g) => a + g.py, 0) : null, targets = bk.map(k => tg[k] ?? null);
    return { bands, groups: out, totals, py, targets, met: targets.map((t, i) => (t == null ? null : totals[i] >= t)), focus: d.focus ?? null,
      unit: d.unit || '例', max: Math.max(...out.map(g => g.values[0])) || 1 };
  }
  /* trial flow with subflows (same rules as diagram_scenes.trialflow_model) */
  const FLOW_KINDS = ['titrate', 'maintain', 'placebo', 'open', 'off'];
  function flowSegs(segs, start, who) {
    need(segs && segs.length, `「${who}」需要至少一段 segs：[{from, to, label, kind}]`);
    let t = start;
    for (const g of segs) {
      const lab = g.label || who;
      need(isNum(g.from) && isNum(g.to) && g.from < g.to, `「${lab}」的 from 须小于 to`);
      need(g.from === t, `「${lab}」须接上前一段（from = ${t}）`);
      need(FLOW_KINDS.includes(g.kind ?? 'maintain'), `「${lab}」的 kind 须是 titrate / maintain / placebo / open / off`);
      t = g.to;
    }
    return t;
  }
  function flowRatio(r, n, who) {
    if (r == null) return null;
    const parts = String(r).split(':');
    need(parts.length === n && parts.every(x => /^\d+$/.test(x) && +x > 0), `${who}的 ratio「${r}」须是与组数相同的正整数比，如 2:1`);
    return parts.map(Number);
  }
  const flowN = x => need(x.n == null || (isInt(x.n) && x.n >= 0), `「${x.name}」的 n 须是非负整数`);
  function trialflowModel(d) {
    const trunk = d.trunk || [], split = d.split || {}, arms = d.arms || [];
    need(trunk.length <= 3, '共同阶段 trunk 最多 3 段（筛选、导入…）');
    need(isNum(split.at), '试验流程需要 split：{at, label?, ratio?}（随机化所在周）');
    if (trunk.length) need(flowSegs(trunk, trunk[0].from, '共同阶段') === split.at, 'split.at 须等于共同阶段 trunk 的结束周');
    need(arms.length >= 2 && arms.length <= 5, '试验流程需要 2–5 个组 arms');
    const ratio = flowRatio(split.ratio, arms.length, '随机化');
    const keys = [], leaves = [], ends = [], out = [];
    for (const a of arms) {
      keys.push(a.key); flowN(a);
      const e = flowSegs(a.segs, split.at, a.name), sp = a.split, r0 = leaves.length; let sub = null;
      if (sp) {
        const kids = sp.arms || [];
        need(sp.at === e, `「${a.name}」的 split.at 须等于该组最后一段的结束周`);
        need(kids.length >= 2 && kids.length <= 3, `「${a.name}」的子分组需要 2–3 个`);
        sub = { at: e, label: sp.label ?? '再随机化', ratio: flowRatio(sp.ratio, kids.length, `「${a.name}」再随机化`) };
        for (const b of kids) {
          keys.push(b.key); flowN(b);
          need(!b.split, '子分组不能再分（最多两层）');
          ends.push(flowSegs(b.segs, e, b.name));
          leaves.push({ ...b, parent: a.key, row: leaves.length, path: [...a.segs, ...b.segs] });
        }
        need(!(a.n != null && kids.every(b => b.n != null) && kids.reduce((s, b) => s + b.n, 0) > a.n), `「${a.name}」的子分组例数之和不能超过该组 n`);
      } else { ends.push(e); leaves.push({ ...a, parent: null, row: leaves.length, path: [...a.segs] }); }
      out.push({ ...a, rows: leaves.slice(r0).map(l => l.row), sub });
    }
    need(new Set(keys).size === keys.length, 'arms 的 key 不能重复（含子分组）');
    need(new Set(ends).size === 1, '各分组的治疗期须在同一周结束');
    const end = ends[0], after = d.after || [];
    need(after.length <= 2, '结束后阶段 after 最多 2 段（随访…）');
    const final = after.length ? flowSegs(after, end, '结束后阶段') : end, start = trunk.length ? trunk[0].from : split.at;
    for (const p of d.endpoints || []) need(isNum(p.at) && start <= p.at && p.at <= final, `终点「${p.label}」的 at 不在试验时间范围内`);
    const subs = d.subs || [];
    need(subs.length <= 3, '子研究 subs 最多 3 个');
    for (const x of subs) {
      need(x.of && x.of.length, `子研究「${x.name}」需要 of（所在分组）`);
      for (const k of x.of) need(keys.includes(k), `子研究「${x.name}」的 of 含未知分组「${k}」`);
      need(isNum(x.from) && isNum(x.to) && x.from < x.to && x.from >= start && x.to <= final, `子研究「${x.name}」的 from–to 须在试验时间范围内且 from < to`);
      flowN(x);
    }
    need(d.focus == null || keys.includes(d.focus), `focus「${d.focus}」不是分组 key`);
    const events = (d.events || []).map(e => {
      need(typeof e.label === 'string' && e.label.trim(), '关键事件 events 须有 label');
      need(isNum(e.at) && start <= e.at && e.at <= final, `事件「${e.label}」的 at 不在试验时间范围内`);
      need(TF_EVENTS.includes(e.kind), `事件「${e.label}」的 kind 须是 ${TF_EVENTS.join('、')} 之一`);
      return { at: e.at, label: e.label, kind: e.kind };
    });
    need(events.length <= 6, '关键事件 events 最多 6 个');
    const bands = (d.bands || []).map(b => {
      const lab = b.label;
      need(typeof lab === 'string' && lab.trim(), '给药 / 治疗时段 bands 须有 label');
      need(TF_BANDS.includes(b.kind), `时段「${lab}」的 kind 须是 ${TF_BANDS.join('、')} 之一`);
      need(isNum(b.from) && isNum(b.to) && b.from < b.to && b.from >= start && b.to <= final, `时段「${lab}」的 from–to 须在试验时间范围内且 from < to`);
      for (const k of b.of || []) need(keys.includes(k), `时段「${lab}」的 of 含未知分组「${k}」`);
      return { label: lab, kind: b.kind, text: b.text || '', from: b.from, to: b.to, of: [...(b.of || [])] };
    });
    need(bands.length <= 4, '给药 / 治疗时段 bands 最多 4 条');
    const segs = [...trunk, ...after, ...arms.flatMap(a => a.segs), ...leaves.filter(l => l.parent).flatMap(l => l.segs)];
    const ticks = [...new Set(segs.flatMap(g => [g.from, g.to]))].sort((a, b) => a - b);
    const n = arms.every(a => a.n != null) ? arms.reduce((s, a) => s + a.n, 0) : null;
    // shared periods before randomisation and after treatment default to off (not treatment) unless the source gives a kind
    return { start, at: split.at, end, final, trunk: trunk.map(g => ({ ...g, kind: g.kind ?? 'off' })), after: after.map(g => ({ ...g, kind: g.kind ?? 'off' })), split, ratio, arms: out, leaves, endpoints: d.endpoints || [], subs, focus: d.focus ?? null,
      unit: d.unit || '周', n, ticks, events, bands };
  }
  const TF_EVENTS = ['interim', 'dmc', 'unblind', 'lock', 'eot', 'rescue', 'other'], TF_BANDS = ['drug', 'background', 'rescue', 'washout', 'other'];
  // piecewise-linear week scale (same rule as diagram_scenes.flow_scale): no interval narrower than minw
  function flowScale(M, x0, x1, minw) {
    const pts = [...new Set([...M.ticks, ...M.endpoints.map(p => p.at), ...M.subs.flatMap(x => [x.from, x.to]), ...(M.events || []).map(e => e.at), ...(M.bands || []).flatMap(b => [b.from, b.to])])].sort((a, b) => a - b);
    const d = pts.slice(1).map((b, i) => b - pts[i]), fixed = new Set(); let k = 0;
    for (let it = 0; it < d.length; it++) {
      const free = d.reduce((a, v, i) => a + (fixed.has(i) ? 0 : v), 0), room = (x1 - x0) - minw * fixed.size;
      k = free ? room / free : 0; const small = d.map((v, i) => i).filter(i => !fixed.has(i) && d[i] * k < minw);
      if (!small.length) break; small.forEach(i => fixed.add(i));
    }
    const ws = d.map((v, i) => fixed.has(i) ? minw : v * k), xs = [x0]; ws.forEach(w => xs.push(xs[xs.length - 1] + w));
    return t => { for (let i = 0; i < d.length; i++) if (t <= pts[i + 1] || i === d.length - 1) return xs[i] + (t - pts[i]) / d[i] * ws[i]; return x0; };
  }
  /* cumulative exposure on the development plan (= Python diagram_scenes.exposure_plan, round 9) */
  const XP_BANDS = ['any', 'w26', 'w52'], XP_LABEL = { any: '任何暴露', w26: '≥26 周', w52: '≥52 周' };
  function exposurePlan(d) {
    const pg = programModel(d.program || {}), lanes = pg.lanes, gran = pg.granularity, tg = d.targets || { any: 1500 };
    for (const [k, v] of Object.entries(tg)) { need(XP_BANDS.includes(k), `targets 的键须是 ${XP_BANDS.join('、')} 之一`); need(isInt(v) && v > 0, `targets.${k} 须为正整数`); }
    const top = {}, name = {};
    lanes.forEach(ln => { top[ln.key] = ln.parent == null ? ln.key : top[ln.parent]; name[ln.key] = ln.name; });
    const studies = [];
    lanes.forEach((ln, li) => ln.bars.forEach(br => {
      const x = br.exposure; if (x == null) return;
      const what = `「${ln.name} · ${br.label || br.phase}」的 exposure`;
      need(x && typeof x === 'object' && isInt(x.n) && x.n > 0, `${what}须给样本量 n（正整数）`);
      const ctrl = x.ctrl ?? 0; need(isNum(ctrl) && ctrl >= 0 && ctrl < 1, `${what}的对照比例 ctrl 须在 0 到 1 之间（不含 1）`);
      const ex = x.exposed ?? pyRound(x.n * (1 - ctrl)); need(isInt(ex) && ex >= 0 && ex <= x.n, `${what}的 exposed 须是 0 到 n 之间的整数`);
      const band = { any: ex };
      for (const [k, up] of [['w26', 'any'], ['w52', 'w26']]) if (x[k] != null) { need(isInt(x[k]) && x[k] >= 0 && x[k] <= (band[up] ?? ex), `${what}的 ${k} 须是不超过${XP_LABEL[up]}例数的整数`); band[k] = x[k]; }
      const t = x.at != null ? tspan(x.at, what + '的 at')[0] : tspan(br.end, what + '的结束')[0];
      need(pg.from <= t && t < pg.to, `${what}的计入时点不在 from–to 之内`);
      studies.push({ lane: ln.key, lane_name: ln.name, ind: top[ln.key], ind_name: name[top[ln.key]], key: br.key, label: br.label || br.phase, phase: br.phase,
        n: x.n, ctrl, band, t, at_text: ttext(t, gran), order: li });
    }));
    need(studies.length, '暴露累计需要至少一个研究条带 exposure：{n, ctrl?, exposed?, at?}');
    const bands = XP_BANDS.filter(k => k === 'any' || studies.some(s => k in s.band) || k in tg);
    studies.sort((a, b) => a.t - b.t || a.order - b.order);
    const run = Object.fromEntries(bands.map(k => [k, 0])), first = Object.fromEntries(bands.map(k => [k, null]));
    for (const s of studies) {
      bands.forEach(k => { run[k] += s.band[k] || 0; }); s.cum = { ...run };
      bands.forEach(k => { if (first[k] == null && k in tg && run[k] >= tg[k]) first[k] = s.t; });
    }
    const inds = [];
    for (const ln of lanes) {
      if (ln.parent != null) continue;
      const fam = lanes.filter(l => top[l.key] === ln.key), sub = fam.flatMap(l => l.milestones).filter(m => m.kind === 'submit').sort((a, b) => a.t - b.t);
      if (!sub.length && !studies.some(s => s.ind === ln.key)) continue;
      const nda = sub[0] || null, cum = Object.fromEntries(bands.map(k => [k, 0]));
      if (nda) studies.forEach(s => { if (s.t <= nda.t) bands.forEach(k => { cum[k] += s.band[k] || 0; }); });
      const tk = Object.keys(tg).filter(k => k in cum);
      inds.push({ key: ln.key, name: ln.name, nda: nda && { t: nda.t, label: nda.label, text: ttext(nda.t, gran), key: nda.key }, cum,
        met: nda ? Object.fromEntries(tk.map(k => [k, cum[k] >= tg[k]])) : {}, gap: nda ? Object.fromEntries(tk.map(k => [k, Math.max(0, tg[k] - cum[k])])) : {} });
    }
    need(d.focus == null || inds.some(i => i.key === d.focus), `focus「${d.focus}」不是有暴露或递交里程碑的适应症泳道`);
    return { plan: pg, studies, indications: inds, bands, targets: tg, first, totals: { ...run }, unit: d.unit || '例', target_label: d.target_label || 'ICH E1',
      focus: d.focus ?? null, max: Math.max(run.any, ...Object.values(tg)) };
  }
  // Python round(): half to even (so n × (1 − ctrl) gives the same count on both sides)
  /* longitudinal (= Python diagram_long.longitudinal_model, round 9): change over visits on a true time axis; blinded
     data carry one overall series only (no arms, no differences) */
  const LG_INTERVALS = { ci95: '95% CI', se: '± SE', sd: '± SD', iqr: 'IQR', box: '中位数与四分位' }, LG_OVERALL = '#5F6B76';
  const fin = v => typeof v === 'number' && Number.isFinite(v);
  function lgNice(lo, hi, n = 5) {
    if (hi === lo) { hi += 1; lo -= 1; }
    // non-negative data never get an axis below 0 (= Python nice)
    const pad = (hi - lo) * .06; lo = lo >= 0 ? Math.max(0, lo - pad) : lo - pad; hi += pad; const raw = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(raw));
    const st = [1, 2, 2.5, 5, 10].map(k => k * mag).find(x => x >= raw - 1e-12);
    return [Math.floor(lo / st + 1e-9) * st, Math.ceil(hi / st - 1e-9) * st, st];
  }
  function longitudinalModel(spec) {
    const me = spec.measure || {}, vis = spec.visits || [], blind = !!spec.blinded;
    need(me.label, '历时变化需要 measure.label（指标名）');
    need(me.interval in LG_INTERVALS, `measure.interval 须是 ${Object.keys(LG_INTERVALS).join('、')} 之一（误差范围必须写明是什么）`);
    need(me.better == null || me.better === 'higher' || me.better === 'lower', 'measure.better 须是 higher、lower 或不写');
    need(vis.length >= 2 && vis.length <= 16, '历时变化需要 2–16 个访视 visits：[{label, t}]');
    const ts = [];
    for (const v of vis) { need(v.label && fin(v.t), '每个访视需要 label 与数值时间 t（研究时间，不是访视序号）'); need(!ts.length || v.t > ts[ts.length - 1], `访视时间 t 须递增：${v.label}`); ts.push(v.t); }
    const labels = vis.map(v => v.label); need(new Set(labels).size === labels.length, '访视 label 不能重复');
    const prim = spec.primary; need(prim == null || labels.includes(prim), `primary「${prim}」不是访视之一`);
    let arms = spec.arms || [];
    if (blind) { need(!arms.length && !spec.diff, '盲态数据只能有一条全体合并的序列：不写 arms、不写 diff（编码分组视同揭盲）'); arms = [{ key: 'all', name: '全体（盲态）', role: 'overall' }]; }
    else {
      need(arms.length >= 1 && arms.length <= 4, '历时变化需要 1–4 个组 arms（盲态数据写 blinded: true）');
      const keys = arms.map(a => a.key); need(new Set(keys).size === keys.length && keys.every(Boolean) && !keys.includes('all'), 'arms 的 key 须不重复、非空，且不能用 all');
      for (const a of arms) { need(a.name, `组「${a.key}」需要 name`); need(['treat', 'comparator'].includes(a.role ?? 'treat'), `组「${a.key}」的 role 须是 treat 或 comparator`); }
      need(arms.filter(a => a.role === 'comparator').length <= 1, 'comparator 最多一个');
    }
    const ak = arms.map(a => a.key), n = vis.length, box = me.interval === 'box', data = spec[box ? 'boxes' : 'series'] || {};
    need(Object.keys(data).length === ak.length && ak.every(k => k in data), `${box ? 'boxes' : 'series'} 须给每个组一行：${ak.join('、')}`);
    const rows = {};
    for (const k of ak) {
      const r = data[k]; need(Array.isArray(r) && r.length === n, `「${k}」须给 ${n} 个访视的值（无数据写 null）`);
      rows[k] = r.map((c, j) => {
        if (c == null) return null; const where = `「${k}」${labels[j]}`;
        if (box) { need(Array.isArray(c) && c.length === 6 && c.slice(0, 5).every(fin) && isInt(c[5]) && c[5] >= 0, `${where} 须是 [下须, Q1, 中位数, Q3, 上须, n]`);
          need(c[0] <= c[1] && c[1] <= c[2] && c[2] <= c[3] && c[3] <= c[4], `${where} 须满足 下须 ≤ Q1 ≤ 中位数 ≤ Q3 ≤ 上须`); return { lo: c[0], q1: c[1], est: c[2], q3: c[3], hi: c[4], n: c[5] }; }
        need(Array.isArray(c) && c.length === 4 && c.slice(0, 3).every(fin) && isInt(c[3]) && c[3] >= 0, `${where} 须是 [估计, 下限, 上限, n]`);
        need(c[1] <= c[0] && c[0] <= c[2], `${where} 须满足 下限 ≤ 估计 ≤ 上限`); return { est: c[0], lo: c[1], hi: c[2], n: c[3] };
      });
    }
    const comp = (arms.find(a => a.role === 'comparator') || {}).key ?? null, diff = {};
    for (const [k, r] of Object.entries(spec.diff || {})) {
      need(comp != null, 'diff 需要一个 comparator 组'); need(ak.includes(k) && k !== comp, `diff 的「${k}」须是治疗组`); need(Array.isArray(r) && r.length === n, `diff「${k}」须给 ${n} 个访视的值`);
      diff[k] = r.map((c, j) => { if (c == null) return null; need(Array.isArray(c) && c.length === 3 && c.every(fin) && c[1] <= c[0] && c[0] <= c[2], `diff「${k}」${labels[j]} 须是 [估计, 下限, 上限]，下限 ≤ 估计 ≤ 上限`); return { est: c[0], lo: c[1], hi: c[2] }; });
    }
    const exp = spec.expected ?? null; need(exp == null || (Array.isArray(exp) && exp.length === n && exp.every(x => isInt(x) && x >= 0)), `expected 须是 ${n} 个访视的应到人数`);
    const ins = spec.in_study ?? null; need(ins == null || (exp && Array.isArray(ins) && ins.length === n && ins.every((v, i) => isInt(v) && v >= 0 && v <= exp[i])), 'in_study 须是各访视仍在研究的人数（不超过 expected）');
    const ref = spec.ref || {}, lines = ref.lines || [], rng = ref.range ?? null;
    const extra = Object.keys(ref).filter(k => k !== 'lines' && k !== 'range');
    need(!extra.length, `ref 只认 range（{lo, hi}）与 lines（[{label, value}]），不认「${extra.join('、')}」：参考线写成 lines: [{label: 'ULN', value: 40}]`);
    need(Array.isArray(lines), 'ref.lines 须是数组 [{label, value}]');
    for (const l of lines) need(l.label && fin(l.value), '参考线需要 label 与数值 value');
    need(rng == null || (['lo', 'hi'].some(k => fin(rng[k])) && ['lo', 'hi'].every(k => rng[k] == null || fin(rng[k]))), '参考范围 range 需要数值 lo 和/或 hi');
    need(spec.focus == null || ak.includes(spec.focus), `focus「${spec.focus}」不是组之一`);
    const vals = [...Object.values(rows).flatMap(r => r.filter(Boolean).flatMap(c => [c.lo, c.hi])), ...lines.map(l => l.value), ...(rng ? ['lo', 'hi'].filter(k => rng[k] != null).map(k => rng[k]) : [])];
    const dvals = [...Object.values(diff).flatMap(r => r.filter(Boolean).flatMap(c => [c.lo, c.hi])), ...(Object.keys(diff).length ? [0] : [])];
    const cat = (global.KZ_TOKENS && global.KZ_TOKENS.charts && global.KZ_TOKENS.charts.categorical) || ['#D46B08', '#008F8A', '#7B5CC7', '#B38A00', '#C4457C'];
    const cmpc = (global.KZ_TOKENS && global.KZ_TOKENS.charts && global.KZ_TOKENS.charts.comparator) || '#6E7B8C';
    const color = {}; let ti = 0;
    for (const a of arms) color[a.key] = a.role === 'overall' ? LG_OVERALL : a.role === 'comparator' ? cmpc : cat[ti++ % cat.length];
    return { measure: me, visits: vis, t: ts, labels, primary: prim != null ? labels.indexOf(prim) : null, blinded: blind, arms: arms.map(a => ({ role: 'treat', ...a })), rows, diff, comp,
      expected: exp, in_study: ins, lines, range: rng, box, color, focus: spec.focus ?? null, unit: me.unit || '', time_unit: spec.time_unit || '周',
      domain: vals.length ? lgNice(Math.min(...vals), Math.max(...vals)) : [0, 1, .2], ddomain: dvals.length ? lgNice(Math.min(...dvals), Math.max(...dvals)) : null };
  }
  // the readiness and ledger tables of the same model (= Python exposure_readiness_table / exposure_ledger_table):
  // cells are text or {text, tone, bold}; the HTML figure re-renders them after every plan change
  const n0 = v => Number(v).toLocaleString('en-US');
  function exposureTables(m) {
    const tg = m.targets, bands = m.bands.filter(k => k in tg), rows = [];
    for (const i of m.indications) {
      if (!i.nda) continue;
      const cells = [i.key === m.focus ? { text: i.name, tone: 'brand' } : i.name, i.nda.text];
      for (const k of bands) { const ok = i.met[k]; cells.push(ok ? { text: `${n0(i.cum[k])} ✓`, bold: false } : { text: `${n0(i.cum[k])} · 差 ${n0(i.gap[k])}`, tone: 'risk', bold: true }); }
      rows.push(cells);
    }
    const readiness = { columns: ['适应症', 'NDA', ...bands.map(k => `${XP_LABEL[k]}（目标 ${n0(tg[k])}）`)], rows, widths: [1.4, 1, ...bands.map(() => 1.6)], center: Array.from({ length: bands.length + 1 }, (_, j) => j + 1) };
    const tgt = tg.any, cross = tgt ? m.studies.findIndex(s => s.cum.any >= tgt) : -1;
    const seq = [...m.studies.map((s, k) => [s.t, 0, k, s]), ...m.indications.map((i, k) => [i.nda && i.nda.t, 1, k, i]).filter(e => e[3].nda)]
      .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
    const lrows = [], tint = (x, kw = {}) => ({ text: x, tone: 'tint', ...kw });
    for (const [, kind, k, o] of seq) {
      if (kind === 0) {
        const flag = k === cross ? ` · 首次达到 ${n0(tgt)}` : '';
        lrows.push([o.lane === o.ind ? o.ind_name : `${o.ind_name} · ${o.lane_name}`, o.label, n0(o.n), o.ctrl ? `${pyRound(o.ctrl * 100)}%` : '—', n0(o.band.any), o.at_text,
          flag ? { text: n0(o.cum.any) + flag, tone: 'brand', bold: true } : n0(o.cum.any)]);
      } else {
        const ok = o.met.any ?? true;
        lrows.push([tint(`${o.name} NDA`, { bold: true }), tint(o.nda.label), tint(''), tint(''), tint(''), tint(o.nda.text),
          { text: `${n0(o.cum.any)} ` + (ok ? '✓' : `· 差 ${n0(o.gap.any)}`), tone: ok ? 'tint' : 'risk', bold: true }]);
      }
    }
    const ledger = { columns: ['适应症', '研究', '样本量', '对照比例', '暴露例数', '计入时点', '累计暴露'], rows: lrows, widths: [1.5, 2, .8, .8, .9, 1, 1.6], numeric: [2, 4, 6], center: [3, 5] };
    return { readiness, ledger };
  }
  function pyRound(v) { const f = Math.floor(v), r = v - f; return r > .5 + 1e-9 ? f + 1 : r < .5 - 1e-9 ? f : (f % 2 === 0 ? f : f + 1); }
  /* competitive landscape (same rules as diagram_scenes.landscape_model) */
  const LS_STAGES = ['临床前', 'I 期', 'II 期', 'III 期', '申报', '上市'], LS_METRICS = ['efficacy', 'safety'];
  function landscapeModel(d) {
    const stages = d.stages || LS_STAGES, assets = d.assets || [];
    need(stages.length >= 2 && stages.length <= 7, '竞争格局需要 2–7 个研发阶段 stages');
    need(new Set(stages).size === stages.length, 'stages 不能重复');
    need(assets.length >= 2 && assets.length <= 10, '竞争格局需要 2–10 个药物 assets（更多时分页：landscape-pipeline / -efficacy / -safety）');
    const keys = assets.map(a => a.key); need(new Set(keys).size === keys.length, 'assets 的 key 不能重复');
    need(assets.filter(a => a.ours).length <= 1, 'ours 最多标一个（本公司药物）');
    const metrics = {};
    for (const mk of LS_METRICS) {
      const mt = d[mk]; if (mt == null) continue;
      need(mt.label, `${mk} 需要 label（指标名）`); need(['higher', 'lower'].includes(mt.better), `${mk}.better 须是 higher 或 lower`);
      metrics[mk] = mt;
    }
    const out = assets.map((a, i) => {
      need(stages.includes(a.stage), `「${a.name}」的 stage 须是 stages 之一`);
      for (const mk of LS_METRICS) {
        const v = a[mk]; if (v == null) continue;
        need(metrics[mk], `「${a.name}」写了 ${mk}，但没有定义 ${mk} 指标`); need(isNum(v), `「${a.name}」的 ${mk} 须是数字或 null（无数据）`);
      }
      return { ...a, idx: i, si: stages.indexOf(a.stage) };
    });
    need(d.focus == null || keys.includes(d.focus), `focus「${d.focus}」不在 assets 里`);
    const mkey = (a, mk) => { const v = a[mk], hi = (metrics[mk] || {}).better === 'higher'; return v == null ? 1e9 : (hi ? -v : v); };
    const order = out.slice().sort((a, b) => (b.si - a.si) || (mkey(a, 'efficacy') - mkey(b, 'efficacy')) || (a.idx - b.idx)).map(a => a.key);
    const rank = Object.fromEntries(Object.keys(metrics).map(mk => [mk, out.filter(a => a[mk] != null).sort((a, b) => (mkey(a, mk) - mkey(b, mk)) || (a.idx - b.idx)).map(a => a.key)]));
    const best = Object.fromEntries(Object.entries(rank).map(([mk, r]) => [mk, r.length ? r[0] : null]));
    const max = Object.fromEntries(Object.keys(metrics).map(mk => [mk, Math.max(0, ...out.filter(a => a[mk] != null).map(a => Math.abs(a[mk]))) || 1]));
    const ours = (out.find(a => a.ours) || {}).key ?? null;
    return { stages, assets: out, order, rank, best, max, metrics, ours, focus: d.focus !== undefined ? d.focus : ours };
  }
  /* efficacy summary (same rules as diagram_scenes.efficacy_model) */
  const EF_TYPES = ['continuous', 'binary', 'tte', 'rate'];
  const EF_EFFECTS = { continuous: ['md'], binary: ['rd', 'or', 'rr'], tte: ['hr'], rate: ['rr'] };
  const EF_RATIO = ['hr', 'or', 'rr'];
  const EF_HEAD = { md: '均值差（95% CI）', rd: '率差（百分点，95% CI）', ratio: '比值（95% CI，对数轴）' };
  const efDec = v => (Math.abs(v).toFixed(6).replace(/0+$/, '').split('.')[1] || '').length;
  const r6 = v => Math.floor(v * 1e6 + .5) / 1e6;
  // Difference axis that always holds 0: [lo, hi] padded by 8 % of the span, and a 1-2-5 tick step near span / 5 (= Python ef_domain).
  function efDomain(bounds) {
    const lo = Math.min(0, ...bounds), hi = Math.max(0, ...bounds), span = (hi - lo) || 1, pad = span * .08;
    const raw = span / 5, mag = 10 ** Math.floor(Math.log10(raw)), step = [1, 2, 5, 10].map(k => k * mag).find(v => v >= raw * .999);
    return [r6(lo - pad), r6(hi + pad), r6(step)];
  }
  // Ratio axis (log) that always holds 1; step 0 marks it as log (= Python ef_log_domain).
  function efLogDomain(bounds) {
    const lo = Math.min(1, ...bounds), hi = Math.max(1, ...bounds), span = (Math.log(hi) - Math.log(lo)) || Math.log(2), pad = span * .08;
    return [r6(lo * Math.exp(-pad)), r6(hi * Math.exp(pad)), 0];
  }
  const EF_LOG_TICKS = [[0.1, 0.2, 0.5, 1, 2, 5, 10], [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4], [0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.25, 1.5]];
  function efTicks(dom) {
    const [lo, hi, st] = dom, out = [];
    if (st === 0) {
      for (const cand of EF_LOG_TICKS) { const t = cand.filter(v => lo <= v && v <= hi); if (t.length >= 3) return t; }
      const t = EF_LOG_TICKS[2].filter(v => lo <= v && v <= hi); return t.length ? t : [1];
    }
    for (let k = Math.ceil(lo / st - 1e-9); k * st <= hi + 1e-9; k++) out.push(r6(k * st));
    return out;
  }
  // 0..1 along the axis, linear or log (= Python ef_pos)
  const efPos = (dom, v) => (dom[2] === 0 ? (Math.log(v) - Math.log(dom[0])) / (Math.log(dom[1]) - Math.log(dom[0])) : (v - dom[0]) / (dom[1] - dom[0]));
  const efMeasure = r => (['md', 'rd'].includes(r.effect) ? '' : r.type === 'rate' ? '率比' : r.effect.toUpperCase());
  const EF_GOOD_EVENT = /应答|缓解|改善|达到|治愈|response|remission/i;
  function efficacyModel(d) {
    const arms = d.arms || [], rows = d.rows || [];
    need(arms.length >= 2 && arms.length <= 4, '有效性汇总需要 2–4 个组 arms：[{key, name, n, role}]');
    const ak = arms.map(a => a.key); need(new Set(ak).size === ak.length, 'arms 的 key 不能重复');
    arms.forEach(a => need(isInt(a.n) && a.n > 0, `组「${a.name}」的 n 须为正整数`));
    const comp = arms.map((a, i) => (a.role === 'comparator' ? i : -1)).filter(i => i >= 0);
    need(comp.length === 1, 'arms 须有且只有一个 role: comparator（对照组）');
    const ci_ = comp[0], treat = arms.map((_, i) => i).filter(i => i !== ci_);
    need(rows.length >= 1 && rows.length <= 10, '有效性汇总需要 1–10 行 rows（终点）');
    const rk = rows.map(r => r.key); need(new Set(rk).size === rk.length, 'rows 的 key 不能重复');
    const types = [], axes = [];
    const out = rows.map(r => {
      const lab = r.label, ty = r.type;
      need(EF_TYPES.includes(ty), `「${lab}」的 type 须是 continuous、binary、tte 或 rate`);
      const eff = r.effect || EF_EFFECTS[ty][0];
      need(EF_EFFECTS[ty].includes(eff), `「${lab}」的 effect 须是 ${EF_EFFECTS[ty].join('、')} 之一`);
      need(['higher', 'lower'].includes(r.better), `「${lab}」的 better 须是 higher 或 lower`);
      const v = r.values || []; need(v.length === arms.length, `「${lab}」的 values 须每组一个（无数据写 null）`);
      const pct = v.map(x => {
        if (x == null) return null;
        if (ty === 'continuous') { need(isNum(x), `「${lab}」的 values 须是数字或 null`); return null; }
        if (ty === 'rate') { need(isNum(x) && x >= 0, `「${lab}」的 values 须是 ≥0 的事件率或 null`); return null; }
        if (ty === 'tte') {
          // events / n are optional (a source may give only the median and the HR); never derive them (03 COPY-09)
          const ok = x && typeof x === 'object' && !Array.isArray(x), md = ok ? x.median : undefined, ev = ok && ('events' in x || 'n' in x);
          need(ok && (md == null || md === 'NR' || (isNum(md) && md > 0)) && (md != null || ev) && (!ev || (isInt(x.events) && isInt(x.n) && x.events >= 0 && x.events <= x.n && x.n > 0)),
            `「${lab}」的 values 须是 {median?, events?, n?}（至少给 median 或 events/n；events 与 n 同时给且 0 ≤ events ≤ n；median 为正数或 "NR"；源材料没有的不要推算）或 null`);
          return ev ? x.events / x.n * 100 : null;
        }
        need(Array.isArray(x) && x.length === 2 && isInt(x[0]) && isInt(x[1]) && x[0] >= 0 && x[0] <= x[1] && x[1] > 0, `「${lab}」的 values 须是 [n, N]（0 ≤ n ≤ N）或 null`);
        return x[0] / x[1] * 100;
      });
      const ratio = EF_RATIO.includes(eff), ref = ratio ? 1 : 0, ax = ratio ? 'ratio' : eff;
      const cmp = {};
      for (const [k, c] of Object.entries(r.vs || {})) {
        need(ak.includes(k) && ak.indexOf(k) !== ci_, `「${lab}」的 vs「${k}」不是治疗组 key`);
        const ci = c.ci || [];
        need(isNum(c.diff) && ci.length === 2 && isNum(ci[0]) && isNum(ci[1]) && ci[0] <= c.diff && c.diff <= ci[1] && ci[0] < ci[1], `「${lab}」对「${k}」须给 diff 与 ci: [lo, hi]，且 lo ≤ diff ≤ hi`);
        if (ratio) need(ci[0] > 0, `「${lab}」对「${k}」的 ${eff.toUpperCase()} 及其 CI 须大于 0`);
        const i = ak.indexOf(k);
        if (eff === 'rd' && pct[i] != null && pct[ci_] != null) need(Math.abs(pct[i] - pct[ci_] - c.diff) <= .15, `「${lab}」对「${k}」的率差 ${c.diff} 与 n/N 算出的 ${(pct[i] - pct[ci_]).toFixed(1)} 不一致`);
        const sig = ci[0] > ref || ci[1] < ref, good = (c.diff < ref) === (r.better === 'lower');
        cmp[k] = { ...c, verdict: sig ? (good ? 'better' : 'worse') : 'ns' };
      }
      if (!types.includes(ty)) types.push(ty);
      if (!axes.includes(ax)) axes.push(ax);
      return { ...r, effect: eff, axis: ax, ref, pct, cmp };
    });
    // time-to-event rows: the better direction of a beneficial event, and event counts copied from a binary row (= Python)
    for (const r of out) {
      if (r.type !== 'tte') continue;
      need(!(r.better === 'lower' && EF_GOOD_EVENT.test(r.label || '')), `「${r.label}」是至应答类有利事件：HR > 1 表示更快达到，better 须写 higher（至复发、死亡等不利事件才写 lower）`);
      const ev = r.values.map(v => v && typeof v === 'object' && 'events' in v ? [v.events, v.n] : null);
      for (const q of out) if (q.type === 'binary' && ev.some(Boolean) && ev.every((e, i) => e == null || (Array.isArray(q.values[i]) && e[0] === q.values[i][0] && e[1] === q.values[i][1])))
        need(false, `「${r.label}」的 events/n 与「${q.label}」的 n/N 完全相同，疑似抄错；源材料没有事件数就只写 median`);
    }
    need(d.focus == null || rk.includes(d.focus), `focus「${d.focus}」不在 rows 里`);
    out.forEach(r => {
      const nums = Object.values(r.cmp).flatMap(c => [c.diff, ...c.ci]).concat(r.type === 'continuous' ? r.values.filter(v => v != null) : []);
      r.dp = r.axis === 'ratio' ? Math.min(2, Math.max(1, ...nums.map(efDec))) : r.axis === 'rd' ? 1 : Math.min(2, Math.max(0, ...nums.map(efDec)));
      r.measure = efMeasure(r);
    });
    const bounds = a => out.filter(r => r.axis === a).flatMap(r => Object.values(r.cmp).flatMap(c => c.ci));
    const domain = Object.fromEntries(axes.map(a => [a, a === 'ratio' ? efLogDomain(bounds(a)) : efDomain(bounds(a))]));
    return { arms, comp: ci_, treat, rows: out, types, axes, domain, focus: d.focus ?? null,
      wins: out.reduce((a, r) => a + Object.values(r.cmp).filter(c => c.verdict === 'better').length, 0), tests: out.reduce((a, r) => a + Object.keys(r.cmp).length, 0) };
  }
  // display helpers (= Python ef_value / ef_diff)
  function efValue(r, i) {
    const v = r.values[i];
    if (v == null) return ['—', ''];
    if (r.type === 'continuous') return [(v >= 0 ? '+' : '−') + Math.abs(v).toFixed(r.dp), ''];
    if (r.type === 'rate') return [v.toFixed(2), ''];
    if (r.type === 'tte') { const md = v.median; return [md === 'NR' ? '未达到' : md != null ? String(md) : '—', 'events' in v ? `${v.events}/${v.n}` : '']; }
    return [r.pct[i].toFixed(1) + '%', `${v[0]}/${v[1]}`];
  }
  const efDiff = (c, dp = 1, measure = '') => { const g = v => v.toFixed(dp).replace('-', '−'); return `${measure ? measure + ' ' : ''}${g(c.diff)} (${g(c.ci[0])}, ${g(c.ci[1])})`; };
  const SOA_EVENTS = ['consent', 'random', 'dose', 'interim', 'primary', 'secondary', 'eot', 'eos', 'other'];
  const SOA_BANDS = ['drug', 'background', 'rescue', 'washout', 'other'];
  // schedule of assessments (= Python soa_model): visits × items in sections; per-visit load, section × visit counts, periods
  const soaWeek = label => { const m = typeof label === 'string' ? /^\s*([WDM])\s*([-−]?\d+(?:\.\d+)?)\s*$/.exec(label) : null;
    if (!m) return null; const v = parseFloat(m[2].replace('−', '-')); return m[1] === 'W' ? v : m[1] === 'D' ? v / 7 : v * 52 / 12; };
  function soaModel(d) {
    const vis = d.visits || [], rows = d.rows || [];
    need(vis.length >= 2 && vis.length <= 30, 'SoA 需要 2–30 个访视 visits：[{v, week, period?}]');
    const vk = vis.map(x => x.v);
    need(vk.every(v => typeof v === 'string' && v.trim()), '每个访视须有名称 v（如 V1、EOS）');
    need(new Set(vk).size === vk.length, '访视名称 v 不能重复');
    let t = vis.map(x => soaWeek(x.week));
    if (t.every(v => v != null)) { for (let i = 1; i < t.length; i++) need(t[i] > t[i - 1], `访视时间须递增：${vis[i - 1].week} → ${vis[i].week}`); }
    else t = null;
    const periods = [];
    vis.forEach((x, i) => {
      const pn = x.period || '';
      if (periods.length && periods[periods.length - 1].name === pn) { periods[periods.length - 1].to = i + 1; return; }
      need(!(pn && periods.some(q => q.name === pn)), `分期「${pn}」的访视不连续`);
      periods.push({ name: pn, from: i, to: i + 1 });
    });
    const items = [], sections = []; let cur = null;
    for (const r of rows) {
      if ('section' in r) {
        need(typeof r.section === 'string' && r.section.trim(), 'section 须是非空文字');
        need(!(cur && !cur.items.length), `分组「${cur && cur.name}」下没有评估项目`);
        cur = { name: r.section, items: [], counts: vis.map(() => 0) }; sections.push(cur); continue;
      }
      const name = r.item;
      need(typeof name === 'string' && name.trim(), '每行须有 item（评估项目）或 section（分组）');
      const at = r.at || []; need(at.length === vis.length, `「${name}」的 at 须每个访视一个（共 ${vis.length} 个）`);
      const marks = [];
      at.forEach((c, i) => {
        if (c == null || c === false || c === 0 || c === '') return;
        if (c === true || c === 1 || (typeof c === 'string' && c.trim())) { marks.push(i); return; }
        need(false, `「${name}」的 at 只能写 1、0、null 或文字标记`);
      });
      need(marks.length, `「${name}」在所有访视都没有标记`);
      if (!cur) { cur = { name: '', items: [], counts: vis.map(() => 0) }; sections.push(cur); }
      items.push({ item: name, section: sections.length - 1, marks, count: marks.length }); cur.items.push(items.length - 1);
      marks.forEach(i => { cur.counts[i] += 1; });
    }
    need(!(cur && !cur.items.length), `分组「${cur && cur.name}」下没有评估项目`);
    need(items.length >= 1 && items.length <= 40, 'SoA 需要 1–40 个评估项目');
    need(sections.filter(q => q.name).length <= 8, 'SoA 最多 8 个分组 section');
    const names = items.map(x => x.item); need(new Set(names).size === names.length, '评估项目 item 不能重复');
    need(d.focus == null || names.includes(d.focus), `focus「${d.focus}」不是评估项目：写某一个评估项目 item 的原文全名（如「${names[0]}」），不是缩写或几项合写`);
    const vi = Object.fromEntries(vk.map((v, i) => [v, i])), has = v => Object.prototype.hasOwnProperty.call(vi, v);
    const events = (d.events || []).map(e => {
      need(has(e.at), `关键节点「${e.label}」的 at 须是访视名称 v`);
      need(SOA_EVENTS.includes(e.kind), `关键节点「${e.label}」的 kind 须是 ${SOA_EVENTS.join('、')} 之一`);
      need(typeof e.label === 'string' && e.label.trim(), '关键节点须有 label');
      return { i: vi[e.at], v: e.at, label: e.label, kind: e.kind };
    });
    need(events.length <= 12, '关键节点 events 最多 12 个');
    const bands = (d.bands || []).map(b => {
      const lab = b.label;
      need(typeof lab === 'string' && lab.trim(), '给药 / 治疗时段须有 label');
      need(has(b.from) && has(b.to), `时段「${lab}」的 from / to 须是访视名称 v`);
      need(vi[b.from] <= vi[b.to], `时段「${lab}」的 from 在 to 之后`);
      need(SOA_BANDS.includes(b.kind), `时段「${lab}」的 kind 须是 ${SOA_BANDS.join('、')} 之一`);
      return { label: lab, kind: b.kind, text: b.text || '', from: vi[b.from], to: vi[b.to] };
    });
    need(bands.length <= 6, '给药 / 治疗时段 bands 最多 6 条');
    const primary = [...new Set(events.filter(e => e.kind === 'primary').map(e => e.i))].sort((a, b) => a - b);
    const load = vis.map((_, i) => sections.reduce((a, q) => a + q.counts[i], 0)), mx = Math.max(...load);
    return { visits: vis, t, periods, items, sections, load, max: mx, busiest: load.map((v, i) => (v === mx ? i : -1)).filter(i => i >= 0),
      total: load.reduce((a, b) => a + b, 0), focus: d.focus ?? null, events, bands, primary };
  }
  global.KZClinical = { safety: safetyModel, program: programModel, exposure: exposureModel, exposurePlan, exposureTables, pyRound, longitudinal: longitudinalModel, LG_INTERVALS, XP_BANDS, XP_LABEL, trialflow: trialflowModel, flowScale, landscape: landscapeModel, efficacy: efficacyModel, efTicks, efPos, efValue, efDiff, EF_HEAD, soa: soaModel, soaWeek, SOA_EVENTS, SOA_BANDS, FLOW_KINDS, dtext, npct, num, tspan, qindex, qtext, ttext, PHASES, MS_KINDS, STATUSES, GRANS };
})(window);
