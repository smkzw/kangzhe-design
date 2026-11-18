"""Clinical-report diagram kinds (8.0 scenario families): safety overview. Same conventions as diagram_kinds.py —
labels 16 px (12 pt), scale marks 14 px; native shapes and text in PPTX, the same geometry inline in HTML. Every number is
computed from the data contract (counts and N), never typed: percentages, differences, depth of a category."""
from .diagrams import kind, f, icon
from .tree import TOK, INK, BODY, MUTED, RISK
from . import text as T
from .diagram_kinds import R, Ln, Tx, S, SMALL, TINT, EDGE

CAT, COMP = TOK['charts']['categorical'], TOK['charts']['comparator']

def W(s, size=S, bold=False): return T.width(T.plain(s), size, bold)

# ---------------------------------------------------------------- safety overview
def safety_model(spec):
    """Validate the safety contract and compute everything drawn: per row depth, n, %, difference (first treat − first
    comparator, percentage points). Shared by the template, the regular demo form and the flagship stage (same rules).
    spec: {unit, set?, arms: [{name, n, role: treat|comparator}], rows: [{key, label, short?, values: [n per arm], parent?}],
           focus?: key, flag_pp?: 5, compare?: [arm, reference], layout?: butterfly|grouped}"""
    arms, rows = spec.get('arms') or [], spec.get('rows') or []
    if not 2 <= len(arms) <= 4: raise ValueError('安全性总览需要 2–4 个组 arms：[{name, n, role}]')
    for a in arms:
        if not (isinstance(a.get('n'), int) and a['n'] > 0): raise ValueError(f'组「{a.get("name")}」的 n 须为正整数')
    if not 3 <= len(rows) <= 10: raise ValueError('安全性总览需要 3–10 行 rows')
    keys = {r['key']: r for r in rows}
    if len(keys) != len(rows): raise ValueError('rows 的 key 不能重复')
    out = []
    for r in rows:
        v = r.get('values') or []
        if len(v) != len(arms) or not all(isinstance(x, int) and 0 <= x for x in v): raise ValueError(f'「{r["label"]}」的 values 须是每组一个非负整数')
        for x, a in zip(v, arms):
            if x > a['n']: raise ValueError(f'「{r["label"]}」在「{a["name"]}」的例数 {x} 超过该组 N={a["n"]}')
        depth, p = 0, r.get('parent')
        while p:
            if p not in keys: raise ValueError(f'「{r["label"]}」的 parent「{p}」不存在')
            if any(c > q for c, q in zip(v, keys[p]['values'])): raise ValueError(f'「{r["label"]}」的例数不能大于上级「{keys[p]["label"]}」')
            depth += 1; p = keys[p].get('parent')
            if depth > 3: raise ValueError('rows 的层级最多 3 级（或 parent 成环）')
        pc = [x / a['n'] * 100 for x, a in zip(v, arms)]
        out.append({**r, 'depth': depth, 'pct': pc})
    ti = next((i for i, a in enumerate(arms) if a.get('role') == 'treat'), 0)
    ci = next((i for i, a in enumerate(arms) if a.get('role') == 'comparator'), None)
    if spec.get('compare'):  # [arm, reference] for the difference column, e.g. the highest dose against placebo
        ti, ci = spec['compare']
        if not (0 <= ti < len(arms) and 0 <= ci < len(arms) and ti != ci): raise ValueError('compare 须是两个不同组的序号 [组, 参照组]')
    if ci is None: raise ValueError('安全性总览需要一个对照组（role: comparator）或 compare')
    for r in out: r['diff'] = r['pct'][ti] - r['pct'][ci]
    if spec.get('focus') and spec['focus'] not in keys: raise ValueError(f'focus「{spec["focus"]}」不在 rows 里')
    if out[0]['depth']: raise ValueError('rows 第一行须是顶层类别（例如任何 TEAE）')
    return {'arms': arms, 'rows': out, 'treat': ti, 'comp': ci, 'flag': spec.get('flag_pp', 5), 'focus': spec.get('focus'),
            'unit': spec.get('unit', '例'), 'max': max(max(r['pct']) for r in out)}

def arm_colors(arms):
    out, slot = [], 0
    for a in arms:
        if a.get('role') == 'comparator': out.append(COMP)
        else: out.append(CAT[slot % len(CAT)]); slot += 1
    return out

def _nice(v):
    # scale tops whose half is a whole percentage (the half tick is labelled)
    for m in (10, 20, 30, 40, 50, 60, 80, 100):
        if v <= m: return m
    return 100

def npct(n, p):
    return f'{n} ({p:.1f}%)'

def dtext(d):
    return '—' if d is None else ('±0.0' if abs(d) < .05 else f'{"+" if d > 0 else "−"}{abs(d):.1f}')

def _safety_measure(spec, w):
    n = len(spec['rows']); grouped = (spec.get('layout') == 'grouped') or len(spec['arms']) > 2
    rh = 20 + 15 * (len(spec["arms"]) - 1) if grouped else 34
    return 56 + n * rh + 34

@kind('safety', measure=_safety_measure)
def safety(spec, box, gid, mode):
    """Safety overview: one row per event category (TEAE, TRAE, ≥3 级, TESAE, TRSAE, AESI, 停药, 死亡 …), child rows
    indented under their parent, n (%) per arm, bars on one shared % scale and the difference column (pp).
    layout 'butterfly' (two arms: treatment wing left of the spine, comparator right) or 'grouped' (2–4 arms)."""
    m = safety_model(spec); x, y, w, h = box; arms, rows = m['arms'], m['rows']; col = arm_colors(arms)
    grouped = spec.get('layout') == 'grouped' or len(arms) > 2
    top_scale = _nice(m['max'])
    lab = min(w * 0.3, max(W(r['label'], S, r['depth'] == 0) + 16 * r['depth'] for r in rows) + 18)
    has_d = m['comp'] is not None
    dw = (W('差值 (pp)', S, True) + 12) if has_d else 0
    head = 56; axis = 34
    n = len(rows)
    out = []
    if not grouped:
        vw = max(W(npct(a['n'], 100.0), S) for a in arms) + 12
        x0 = x + lab; x1 = x + w - dw
        wing = (x1 - x0 - 2 * vw - 12) / 2; spine = x0 + vw + wing + 6
        rh = max(30, min(46, (h - head - axis) / n)); y0 = y + head + max(0, (h - head - axis - rh * n) / 2) * .5
        L = lambda p: spine - 3 - p / top_scale * wing
        Rr = lambda p: spine + 3 + p / top_scale * wing
        # header: arm names with N, centred over each wing + value column
        for i, (cx, a) in enumerate(((x0 + (vw + wing) / 2, arms[m['treat']]), (spine + 6 + (wing + vw) / 2, arms[m['comp'] if has_d else 1]))):
            out.append(Tx(cx, y + 16, a['name'], S, INK, True, 'middle'))
            out.append(Tx(cx, y + 36, f'N = {a["n"]}', SMALL, MUTED, False, 'middle'))
        out.append(Tx(x, y + 26, spec.get('head', '事件类别'), S, INK, True))
        if has_d: out.append(Tx(x + w, y + 26, '差值 (pp)', S, INK, True, 'end'))
        out.append(Ln(x, y + head - 6, x + w, y + head - 6, '#D5DADF', 1))
        idx = (m['treat'], m['comp'] if has_d else 1)
        for k, r in enumerate(rows):
            cy = y0 + k * rh + rh / 2; top = r['depth'] == 0; foc = r['key'] == m['focus']
            if foc: out.append(R(x - 6, y0 + k * rh + 2, w + 12, rh - 4, TINT['brand'], EDGE['brand'], 8))
            elif k % 2 == 0: out.append(R(x0, y0 + k * rh + 2, x1 - x0, rh - 4, '#F7F8F9', None, 4))
            out.append(Tx(x + 16 * r['depth'], cy, r['label'], S, INK if top or foc else BODY, top or foc, 'start', lab - 16 * r['depth'] - 8))
            bh = rh * (.46 if top else .34)
            pl, pr = r['pct'][idx[0]], r['pct'][idx[1]]
            out.append(R(L(pl), cy - bh / 2, max(.5, L(0) - L(pl)), bh, col[idx[0]], None, 3))
            out.append(R(Rr(0), cy - bh / 2, max(.5, Rr(pr) - Rr(0)), bh, col[idx[1]], None, 3))
            out.append(Tx(x0 + vw - 6, cy, npct(r['values'][idx[0]], pl), S, INK if top else BODY, top, 'end'))
            out.append(Tx(spine + 6 + wing + 6 + 6, cy, npct(r['values'][idx[1]], pr), S, INK if top else BODY, top, 'start'))
            if has_d:
                d = r['diff']; hot = d is not None and d >= m['flag']
                out.append(Tx(x + w, cy, dtext(d), S, RISK if hot else (INK if top else BODY), hot or top, 'end'))
        yb = y0 + n * rh + 4
        out.append(Ln(spine, y0 - 4, spine, yb, '#5F6B76', 1.2))
        out.append(Ln(L(top_scale), yb, Rr(top_scale), yb, '#CED3D8', 1))
        for t in (0, top_scale / 2, top_scale):
            for X in ((L(t),) if t == 0 else (L(t), Rr(t))):
                out.append(Ln(X, yb, X, yb + 4, '#CED3D8', 1)); out.append(Tx(X, yb + 14, f'{t:g}%', SMALL, MUTED, False, 'middle'))
    else:
        # grouped: one thin bar per arm inside each row, n (%) at the bar end; legend in the header
        x0 = x + lab; x1 = x + w - dw - 8; vw = max(W(npct(a['n'], 100.0), S) for a in arms) + 10
        span = x1 - x0 - vw; na = len(arms)
        rh = max(20 + 15 * (na - 1), min(28 + 20 * (na - 1), (h - head - axis) / n)); y0 = y + head
        X = lambda p: x0 + p / top_scale * span
        lx = x
        for i, a in enumerate(arms):
            out.append(R(lx, y + 4, 14, 14, col[i], None, 3)); out.append(Tx(lx + 20, y + 11, f'{a["name"]}（N = {a["n"]}）', S, INK, True))
            lx += 20 + W(f'{a["name"]}（N = {a["n"]}）', S, True) + 24
        out.append(Tx(x, y + 38, spec.get('head', '事件类别'), S, INK, True))
        if has_d: out.append(Tx(x + w, y + 38, '差值 (pp)', S, INK, True, 'end'))
        out.append(Ln(x, y + head - 6, x + w, y + head - 6, '#D5DADF', 1))
        for k, r in enumerate(rows):
            ry = y0 + k * rh; top = r['depth'] == 0; foc = r['key'] == m['focus']
            if foc: out.append(R(x - 6, ry + 2, w + 12, rh - 4, TINT['brand'], EDGE['brand'], 8))
            elif k % 2 == 0: out.append(R(x0, ry + 2, x1 - x0, rh - 4, '#F7F8F9', None, 4))
            out.append(Tx(x + 16 * r['depth'], ry + rh / 2, r['label'], S, INK if top or foc else BODY, top or foc, 'start', lab - 16 * r['depth'] - 8))
            bh = min(12, (rh - 10) / na - 4)
            for i in range(na):
                by = ry + 5 + (rh - 10) * (i + .5) / na
                out.append(R(x0, by - bh / 2, max(.5, X(r['pct'][i]) - x0), bh, col[i], None, 3))
                out.append(Tx(X(r['pct'][i]) + 6, by, npct(r['values'][i], r['pct'][i]), SMALL, BODY, False))
            if has_d:
                d = r['diff']; hot = d is not None and d >= m['flag']
                out.append(Tx(x + w, ry + rh / 2, dtext(d), S, RISK if hot else (INK if top else BODY), hot or top, 'end'))
        yb = y0 + n * rh + 4
        out.append(Ln(x0, yb, x0 + span, yb, '#CED3D8', 1))
        for t in (0, top_scale / 2, top_scale):
            out.append(Ln(X(t), yb, X(t), yb + 4, '#CED3D8', 1)); out.append(Tx(X(t), yb + 14, f'{t:g}%', SMALL, MUTED, False, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- clinical development plan (program Gantt)
import re as _re, datetime as _dt, json as _json
from pathlib import Path
PHASES = ['I 期', 'II 期', 'III 期', '注册', '上市后']
MS_KINDS = {'start': '首例入组', 'readout': '结果读出', 'submit': '递交', 'approve': '获批', 'other': '里程碑'}
STATUSES = {'planned': '计划', 'active': '进行中', 'done': '已完成', 'delayed': '延迟', 'risk': '风险'}
GRANS = ('quarter', 'month', 'day')
PHASE_COL = TOK['charts']['phases']
ICONS = set(_json.loads((Path(__file__).resolve().parents[2] / 'assets/icons/icons.json').read_text(encoding='utf-8'))['icons'])
_Q = _re.compile(r'^(\d{4})Q([1-4])$')
_M = _re.compile(r'^(\d{4})-(0[1-9]|1[0-2])$')
_D = _re.compile(r'^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')

def tspan(s, what):
    """A time value as [start, end) in continuous quarter units (year × 4 + quarter − 1, days as a fraction of their
    quarter) plus its unit: '2026Q3' → one quarter, '2026-08' → one month (a third), '2026-08-15' → one day.
    The same arithmetic, in the same order, as runtime/kz-clinical.js (so both products agree to the last bit)."""
    v = str(s if s is not None else '')
    m = _Q.match(v)
    if m:
        i = int(m[1]) * 4 + int(m[2]) - 1; return i, i + 1, 'quarter'
    m = _M.match(v)
    if m:
        y, mo = int(m[1]), int(m[2]); i = y * 4 + (mo - 1) // 3; k = (mo - 1) % 3
        return i + k / 3, i + (k + 1) / 3, 'month'
    m = _D.match(v)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
        try: day = _dt.date(y, mo, d)
        except ValueError: raise ValueError(f'{what}「{s}」不是有效日期')
        q0 = _dt.date(y, (mo - 1) // 3 * 3 + 1, 1); q1 = _dt.date(y + 1, 1, 1) if mo > 9 else _dt.date(y, (mo - 1) // 3 * 3 + 4, 1)
        n, off, i = (q1 - q0).days, (day - q0).days, y * 4 + (mo - 1) // 3
        return i + off / n, i + (off + 1) / n, 'day'
    raise ValueError(f'{what}「{s}」须写成季度、月份或日期，例如 2026Q3、2026-08、2026-08-15')

def qindex(s, what):
    """Whole quarters only (axis ends written as quarters, the KZGantt legacy model)."""
    a, _, u = tspan(s, what)
    if u != 'quarter': raise ValueError(f'{what}「{s}」须写成年份加季度，例如 2026Q3')
    return a

def qtext(i):
    i = int(i); return f'{i // 4}Q{i % 4 + 1}'

def ttext(v, gran):
    """A quarter-unit position as text at a granularity: 2026Q3 · 2026-08 · 2026-08-15."""
    i = int(v // 1); y, q = i // 4, i % 4
    if gran == 'quarter': return f'{y}Q{q + 1}'
    if gran == 'month': return f'{y}-{q * 3 + min(2, int((v - i) * 3 + 1e-9)) + 1:02d}'
    q0 = _dt.date(y, q * 3 + 1, 1); q1 = _dt.date(y + 1, 1, 1) if q == 3 else _dt.date(y, q * 3 + 4, 1)
    return (q0 + _dt.timedelta(days=int((v - i) * (q1 - q0).days + 1e-9))).isoformat()

def _finer(u, gran):
    return GRANS.index(u) > GRANS.index(gran)

def program_model(spec, today=None):
    """Validate the clinical-development-plan contract and compute the time geometry. Times are written as quarters
    ('2026Q3'), months ('2026-08') or days ('2026-08-15'); bar ends are inclusive in their unit. Internally everything is
    continuous quarter units (year × 4 + quarter − 1; [start, end)), the same model as KZGantt (08 GANTT-02).
    spec: {from, to, today?: time | 'auto', granularity?: quarter|month|day, phases?, focus?,
           lanes: [{key, name, note?, parent?, collapsed?,
                    bars: [{key, phase, start, end, label?, color?, status?, progress?, baseline?: {start, end}}],
                    milestones?: [{key, at, label, kind?, icon?, risk?, major?, baseline?}]}]}
    granularity (default: the finest unit any bar is written in) is the bars' precision; milestones may be days at any
    granularity. A lane with `parent` (the lane right above it, or a sibling under it) is a child: two levels at most; a
    `collapsed` parent shows its children summed up (phases merged; only `major` milestones, else submit/approve).
    status / progress / baseline / icon are optional layers: absent data draws nothing. Past = before today."""
    a = tspan(spec.get('from'), 'from')[0]; b = tspan(spec.get('to'), 'to')[1]
    a, b = int(a // 1), -int(-b // 1)                       # the axis runs on whole quarters
    if not 2 <= b - a <= 40: raise ValueError('时间轴 from–to 须覆盖 2–40 个季度（含首尾）')
    gran = spec.get('granularity')
    if gran is not None and gran not in GRANS: raise ValueError('granularity 须是 quarter、month、day 之一')
    phases = spec.get('phases') or PHASES
    if not 1 <= len(phases) <= len(PHASE_COL): raise ValueError(f'phases 须是 1–{len(PHASE_COL)} 个阶段名')
    lanes = spec.get('lanes') or []
    if not 1 <= len(lanes) <= 24: raise ValueError('临床开发计划需要 1–24 条泳道 lanes')
    keys, units = set(), []
    def uniq(k):
        if not k or k in keys: raise ValueError(f'key「{k}」缺失或重复')
        keys.add(k)
    def inside(s0, e0, what):
        if not a <= s0 < e0 <= b: raise ValueError(f'{what}须在 from–to 之内，且结束不早于开始')
    out, kids = [], {}
    for idx, ln in enumerate(lanes):
        uniq(ln.get('key'))
        if not str(ln.get('name') or '').strip(): raise ValueError('泳道 name 不能为空')
        par = ln.get('parent')
        if par is not None:
            prev = out[-1] if out else None
            top = prev and (prev['key'] if prev.get('parent') is None else prev['parent'])
            if par != top: raise ValueError(f'泳道「{ln["name"]}」的 parent 须是紧挨在它上面的上级泳道（只有两级）')
            kids.setdefault(par, []).append(ln['key'])
        bars = []
        for br in ln.get('bars') or []:
            uniq(br.get('key'))
            if br.get('phase') not in phases: raise ValueError(f'「{ln["name"]}」的阶段「{br.get("phase")}」不在 phases 里')
            what = f'「{ln["name"]} · {br["phase"]}」'
            s0, _, u0 = tspan(br.get('start'), what + '的开始'); _, e0, u1 = tspan(br.get('end'), what + '的结束')
            inside(s0, e0, what); units += [u0, u1]
            o = {**br, 's': s0, 'e': e0, 'pi': phases.index(br['phase'])}
            if br.get('color') is not None and not _re.match(r'^#[0-9A-Fa-f]{6}$', str(br['color'])): raise ValueError(f'{what}的 color 须是 #RRGGBB')
            if br.get('status') is not None and br['status'] not in STATUSES: raise ValueError(f'{what}的 status 须是 {"、".join(STATUSES)} 之一')
            if br.get('progress') is not None and not (isinstance(br['progress'], (int, float)) and not isinstance(br['progress'], bool) and 0 <= br['progress'] <= 100):
                raise ValueError(f'{what}的 progress 须是 0–100 的数')
            if br.get('baseline') is not None:
                bl = br['baseline']
                if not isinstance(bl, dict): raise ValueError(f'{what}的 baseline 须写成 {{start, end}}')
                bs, _, v0 = tspan(bl.get('start'), what + '的原计划开始'); _, be, v1 = tspan(bl.get('end'), what + '的原计划结束')
                inside(bs, be, what + '的原计划'); units += [v0, v1]; o['bs'], o['be'] = bs, be
            bars.append(o)
        bars.sort(key=lambda r: r['s'])
        for p, q in zip(bars, bars[1:]):
            if q['s'] < p['e']: raise ValueError(f'「{ln["name"]}」的「{p["phase"]}」与「{q["phase"]}」时间重叠；源材料的日期照原样写，不要为消除重叠改日期：同一泳道的阶段须前后相接，交叠或并行的研究（如 II 期未结束时 III 期已启动）拆成子泳道（parent 指向上级泳道）')
        ms = []
        for m in ln.get('milestones') or []:
            uniq(m.get('key'))
            if not str(m.get('label') or '').strip(): raise ValueError(f'「{ln["name"]}」有里程碑缺 label')
            k = m.get('kind', 'other')
            if k not in MS_KINDS: raise ValueError(f'里程碑「{m["label"]}」的 kind 须是 {"、".join(MS_KINDS)} 之一')
            ic = m.get('icon')
            if ic is not None and ic not in MS_KINDS and ic not in ICONS: raise ValueError(f'里程碑「{m["label"]}」的 icon「{ic}」不是里程碑图形或图标库里的名字')
            t0, t1, _ = tspan(m.get('at'), f'里程碑「{m["label"]}」的时间')
            if not a <= t0 < b: raise ValueError(f'里程碑「{m["label"]}」不在 from–to 之内')
            o = {**m, 'kind': k, 't': t0, 'tw': t1 - t0}
            if m.get('baseline') is not None:
                u0, u1, _ = tspan(m['baseline'], f'里程碑「{m["label"]}」的原计划时间')
                if not a <= u0 < b: raise ValueError(f'里程碑「{m["label"]}」的原计划时间不在 from–to 之内')
                o['bt'], o['btw'] = u0, u1 - u0
            ms.append(o)
        if len(ms) > 6: raise ValueError(f'「{ln["name"]}」的里程碑超过 6 个；多适应症总图只放关键性里程碑，细化节点放单适应症页')
        out.append({**ln, 'bars': bars, 'milestones': sorted(ms, key=lambda m: m['t']), 'depth': 1 if par is not None else 0})
    for ln in out:
        ln['children'] = kids.get(ln['key'], [])
        if ln.get('collapsed') and not ln['children']: raise ValueError(f'泳道「{ln["name"]}」没有下级泳道，不能 collapsed')
        if not ln['bars'] and not ln['children']: raise ValueError(f'泳道「{ln["name"]}」至少要有一个阶段 bars')
    fin = max((GRANS.index(u) for u in units), default=0)
    if gran is None: gran = GRANS[fin]
    elif fin > GRANS.index(gran): raise ValueError(f'阶段的起止写得比 granularity「{gran}」更细；改 granularity，或把起止写成{"季度" if gran == "quarter" else "月份"}')
    # collapsed parents: their own bars if any, else the children's bars merged per phase; milestones flagged major
    # (else submit / approve) climb up. Children of a collapsed parent are hidden.
    by = {ln['key']: ln for ln in out}
    for ln in out:
        if not (ln.get('collapsed') and ln['children']): continue
        ch = [by[k] for k in ln['children']]
        if not ln['bars']:
            seg = []
            for pi in sorted({br['pi'] for c in ch for br in c['bars']}):
                iv = sorted((br['s'], br['e']) for c in ch for br in c['bars'] if br['pi'] == pi)
                cur = list(iv[0])
                for s0, e0 in iv[1:]:
                    if s0 <= cur[1]: cur[1] = max(cur[1], e0)
                    else: seg.append({'key': f'{ln["key"]}~{pi}~{len(seg)}', 'phase': phases[pi], 'pi': pi, 's': cur[0], 'e': cur[1], 'summary': True}); cur = [s0, e0]
                seg.append({'key': f'{ln["key"]}~{pi}~{len(seg)}', 'phase': phases[pi], 'pi': pi, 's': cur[0], 'e': cur[1], 'summary': True})
            ln['summary'] = sorted(seg, key=lambda r: (r['s'], r['pi']))
        up = [m for c in ch for m in c['milestones'] if m.get('major')] or [m for c in ch for m in c['milestones'] if m['kind'] in ('submit', 'approve')]
        ln['summary_ms'] = sorted(up, key=lambda m: m['t'])[:6]
    hidden = {k for ln in out if ln.get('collapsed') for k in ln['children']}
    visible = [ln for ln in out if ln['key'] not in hidden]
    if len(visible) > 12: raise ValueError('同时显示的泳道超过 12 条；收起一些上级泳道（collapsed），或拆成两页')
    tv = spec.get('today')
    if tv == 'auto':
        d = today or _dt.date.today(); tv = d.isoformat()
    now = tw = None
    if tv:
        now, t1, _ = tspan(tv, 'today'); tw = t1 - now
        if not a <= now < b: raise ValueError('today 不在 from–to 之内')
    if spec.get('focus') and spec['focus'] not in keys: raise ValueError(f'focus「{spec["focus"]}」不是任何泳道、阶段或里程碑的 key')
    used = sorted({br['pi'] for ln in visible for br in (ln['bars'] or ln.get('summary') or [])})
    allm = [m for ln in visible for m in (ln['milestones'] + ln.get('summary_ms', []))]
    layers = {'status': any(br.get('status') for ln in visible for br in ln['bars']),
              'progress': any(br.get('progress') is not None for ln in visible for br in ln['bars']),
              'baseline': any('bs' in br for ln in visible for br in ln['bars']) or any('bt' in m for m in allm),
              'levels': any(ln['children'] for ln in out)}
    return {'from': a, 'to': b, 'today': now, 'today_w': tw, 'granularity': gran, 'phases': phases, 'used': used,
            'lanes': out, 'visible': visible, 'focus': spec.get('focus'), 'layers': layers,
            'kinds': [k for k in MS_KINDS if any(m['kind'] == k for m in allm)]}

def _lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def on_color(bg):
    """Ink or white, whichever contrasts more with the bar colour."""
    l = _lum(bg); return INK if (l + .05) / (_lum(INK) + .05) >= 1.05 / (l + .05) else '#FFFFFF'

def _mix(hexc, t=.55):
    c = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(v + (255 - v) * t):02X}' for v in c)

def glyph(kind, cx, cy, r, fill, stroke=None, sw=1.8):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    if kind == 'start': return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r * .82)}" fill="{fill}"{st}/>'
    if kind == 'submit': pts = [(cx, cy - r), (cx + r * .95, cy + r * .72), (cx - r * .95, cy + r * .72)]
    elif kind == 'approve':
        import math
        pts = [(cx + (r * 1.15 if i % 2 == 0 else r * .5) * math.sin(i * math.pi / 5), cy - (r * 1.15 if i % 2 == 0 else r * .5) * math.cos(i * math.pi / 5)) for i in range(10)]
    elif kind == 'other':   # a hexagon: an axis-aligned square on a bar edge would read as an edge strip (02 LG-02 checker)
        import math
        pts = [(cx + r * .92 * math.cos(math.pi / 6 + i * math.pi / 3), cy + r * .92 * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]
    else: pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    return f'<polygon points="{" ".join(f"{f(px)},{f(py)}" for px, py in pts)}" fill="{fill}"{st}/>'

LINE, BAR, PIN = 19, 29, 6.5   # label line, bar height, milestone glyph radius (the glyph is pinned on the bar's top edge)
# compact plan (many lanes on one page): thinner bars and label lines, used only when the full size does not fit the box;
# the measure reports the compact height, so a plan that fits compact never overflows into a lane being dropped
COMPACT = {'LINE': 16, 'BAR': 22}

class _compact:
    def __enter__(self):
        g = globals(); self.old = {k: g[k] for k in COMPACT}; g.update(COMPACT)
    def __exit__(self, *a):
        globals().update(self.old)
GHOST = 7                        # the baseline strip under a bar (原计划), when the plan carries baselines
GT = TOK['gantt']                # 08 GANTT-06 layer tokens: today line and pill, progress track
OK_INK = '#3F7A1F'               # earlier than planned (the brand has no green token; text only, never a fill)
STATUS_ICON = {'done': 'circle-check', 'active': 'progress-check', 'delayed': 'clock', 'risk': 'alert-circle'}
UNIT = {'quarter': ('季度', 1), 'month': ('个月', 3), 'day': ('天', None)}

def lane_items(ln):
    """What a visible lane draws: its own bars (or, collapsed, the children merged per phase) and milestones."""
    bars = ln['bars'] or (ln.get('summary') or [] if ln.get('collapsed') else [])
    ms = ln['milestones'] + (ln.get('summary_ms') or [] if ln.get('collapsed') else [])
    return bars, sorted(ms, key=lambda m: m['t'])

def slip(d, gran, at):
    """A signed shift in quarter units as text at the plan's granularity: +1 季度 · −2 个月 · +15 天."""
    if abs(d) < 1e-9: return ''
    word, k = UNIT[gran]
    if k is None:
        import datetime as _d
        a0, a1 = _d.date.fromisoformat(ttext(at - d, 'day')), _d.date.fromisoformat(ttext(at, 'day')); n = (a1 - a0).days
    else: n = round(d * k)
    return '' if n == 0 else f'{"+" if n > 0 else "−"}{abs(n)} {word}'

def _program_layout(spec, w):
    m = program_model(spec)
    def head(ln): return (16 if ln['depth'] else 0) + (14 if ln['children'] else 0)
    lab = min(w * .26, max(max(W(ln['name'], S, True), W(ln.get('note', ''), SMALL)) + head(ln) for ln in m['visible']) + 22)
    x0, x1 = lab, w - 10; qw = (x1 - x0) / (m['to'] - m['from'])
    X = lambda q: x0 + (q - m['from']) * qw
    lanes, tx = [], (X(m['today'] + m['today_w'] / 2) if m['today'] is not None else None)
    for ln in m['visible']:
        bars, mss = lane_items(ln)
        taken, place = [], []
        for ms in mss:
            cx = X(ms['t'] + ms['tw'] / 2); lw = W(ms['label'], S) + 10
            free = lambda k, sp: not any(r == k and not (sp[1] <= p or sp[0] >= q) for r, p, q in taken)
            # per line: centred on the glyph, starting at it, ending at it, then left or right of it; a label that would cross the
            # today line takes the next candidate on the same line, and only if every candidate is taken one line up
            clear = lambda sp: tx is None or not (sp[0] - 2 < tx < sp[1] + 2)
            for k in range(3):
                spans = [(lo, lo + lw) for lo in (min(max(lo, x0), x1 - lw) for lo in (cx - lw / 2, cx - 8, cx + 8 - lw, cx - PIN - 6 - lw, cx + PIN + 6))]
                hit = next((sp for sp in spans if free(k, sp) and clear(sp)), None) or next((sp for sp in spans if free(k, sp)), None)
                if hit: break
            else: raise ValueError(f'「{ln["name"]}」的里程碑标签太挤（同一时段超过 3 层）：缩短标签或拆成单适应症细化页')
            taken.append((k, *hit)); place.append((ms, cx, (hit[0] + hit[1]) / 2, k))
        lines = 1 + max((k for *_, k in place), default=-1)
        hh = 36 if not bars and not place else max(BAR + 17, 4 + lines * LINE + 6 + BAR + 6 + _lane_ghost(bars))
        lanes.append((ln, bars, place, hh))
    return m, lab, x0, x1, X, lanes, 1

def _lane_ghost(bars):
    # room for the baseline strip only on lanes that draw one (a bar whose 原计划 differs from the plan)
    return GHOST + 3 if any('bs' in b and (abs(b['bs'] - b['s']) > 1e-9 or abs(b['be'] - b['e']) > 1e-9) for b in bars) else 0

def _legend_items(m):
    items = [('phase', i, m['phases'][i]) for i in m['used']] + [('ms', k, MS_KINDS[k]) for k in m['kinds']]
    used = {br.get('status') for ln in m['visible'] for br in ln['bars']} if m['layers']['status'] else set()
    # the phase swatches are the solid (done) look; 计划 explains the light dashed part after today (as KZGantt's legend)
    if m['today'] is not None and any(br['e'] > m['today'] + m['today_w'] / 2 for ln in m['visible'] for br in (ln['bars'] or ln.get('summary') or [])):
        items.append(('plan', None, '计划'))
    if m['layers']['baseline']: items.append(('ghost', None, '原计划'))
    if m['layers']['progress']: items.append(('progress', None, '进度'))
    items += [('status', k, STATUSES[k]) for k in STATUS_ICON if k in used]
    return items

def _program_need(spec, w):
    m, lab, x0, x1, X, lanes, _ = _program_layout(spec, w)
    lw = sum(W(t, SMALL) + 30 for *_, t in _legend_items(m))
    return (26 if lw <= w else 50) + 6 + 40 + sum(h for *_, h in lanes) + (30 if m['today'] is not None else 6)

def _program_measure(spec, w):
    with _compact(): return _program_need(spec, w)

def _caret(x, y, open_):
    pts = [(x, y - 4), (x + 8, y - 4), (x + 4, y + 3)] if open_ else [(x + 1, y - 5), (x + 1, y + 4), (x + 8, y - .5)]
    return f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in pts)}" fill="{MUTED}"/>'

@kind('program', measure=_program_measure)
def program(spec, box, gid, mode):
    """Clinical development plan on a time axis (quarters, with months when the plan is written in months or days): one
    lane per indication (key milestones) or per study (detailed milestones), two levels when lanes carry `parent`; phase
    bars on one sequential ramp (I 期 → 上市后), the part after the today line drawn as plan (light, dashed); milestone
    glyphs by kind (首例入组 ● / 结果读出 ◆ / 递交 ▲ / 获批 ★ / 其他 ⬢) or a chosen icon, filled when past, hollow when
    ahead. Optional layers, drawn only when the data has them: status marks, progress, the baseline (原计划) strip with
    the slip."""
    x, y, w, h = box
    if _program_need(spec, w) > h + .5:
        with _compact(): return _program_draw(spec, box, gid, mode)
    return _program_draw(spec, box, gid, mode)

def _program_draw(spec, box, gid, mode):
    x, y, w, h = box
    m, lab, x0, x1, X, lanes, _ = _program_layout(spec, w)
    x0 += x; x1 += x; X0 = X; X = lambda q: X0(q) + x
    gran = m['granularity']
    items = _legend_items(m); lw = sum(W(t, SMALL) + 30 for *_, t in items)
    leg_h = 26 if lw <= w else 50
    nat = _program_measure(spec, w); extra = max(0, h - nat); grow = min(24, extra / max(1, len(lanes)))
    now = m['today']; tx = X(now + m['today_w'] / 2) if now is not None else None
    out = []
    # legend
    lx, ly = x, y + 9
    for typ, i, t in items:
        tw = W(t, SMALL) + 30
        if lx + tw > x + w: lx, ly = x, ly + 24
        if typ == 'phase': out.append(R(lx, ly - 7, 16, 14, PHASE_COL[i], None, 3))
        elif typ == 'ms': out.append(glyph(i, lx + 8, ly, 7, INK))
        elif typ == 'progress':
            out += [R(lx, ly - 7, 16, 14, PHASE_COL[2], None, 3), R(lx + 2, ly + 1, 12, 3, GT['progress']['track'], None, 1.5), R(lx + 2, ly + 1, 7, 3, GT['progress']['fill'], None, 1.5)]
        elif typ == 'ghost': out.append(R(lx, ly - 3, 16, GHOST, 'none', MUTED, 2, True, 1.1))
        elif typ == 'status': out.append(icon(STATUS_ICON[i], lx, ly - 8, 16, RISK if i == 'risk' else INK, mode))
        else: out.append(R(lx, ly - 7, 16, 14, _mix(PHASE_COL[2]), PHASE_COL[2], 3, True, 1.2))
        out.append(Tx(lx + 22, ly, t, SMALL, BODY)); lx += tw
    # axis: years over quarters (or months when the plan is written finer than quarters and there is room)
    ay = y + leg_h + 6; top = ay + 40
    body_h = sum(hh + grow for *_, hh in lanes); bot = top + body_h
    qw = X(m['from'] + 1) - X(m['from']); months = gran != 'quarter' and qw / 3 >= 22
    out.append(R(x0, ay, x1 - x0, 40, '#FFF6EA', None, 6))
    for q in range(m['from'], m['to']):
        if q == m['from'] or q % 4 == 0:
            ye = min(m['to'], (q // 4 + 1) * 4)
            # a partial year at the axis start: '2024 年', else '2024', else nothing — never a bare '24'
            yw = X(ye) - X(q); yl = next((t for t in (f'{q // 4} 年', str(q // 4)) if yw >= W(t, SMALL, True) + 8), '')
            if yl: out.append(Tx((X(q) + X(ye)) / 2, ay + 11, yl, SMALL, INK, True, 'middle'))
            if q != m['from']: out.append(Ln(X(q), ay + 4, X(q), bot, '#E1E5E9', 1))
        elif qw >= 22: out.append(Ln(X(q), ay + 22, X(q), bot, '#F1F3F5', 1))
        if months:
            for k in range(3):
                mx = X(q + k / 3)
                if k: out.append(Ln(mx, ay + 26, mx, ay + 40, '#F1F3F5', 1))
                out.append(Tx(mx + qw / 6, ay + 30, f'{q % 4 * 3 + k + 1}', SMALL, MUTED, False, 'middle'))
        elif qw >= 28: out.append(Tx(X(q) + qw / 2, ay + 30, f'Q{q % 4 + 1}', SMALL, MUTED, False, 'middle'))
    out.append(Tx(x, ay + 20, spec.get('head', '适应症 / 研究'), S, INK, True))
    # lanes: stripes first, then the today line, then bars, glyphs and labels above it
    bg, cy0, head_n = [], top, len(out)
    for k, (ln, bars, place, hh) in enumerate(lanes):
        hh += grow; foc_lane = ln['key'] == m['focus']
        if foc_lane: bg.append(R(x - 6, cy0 + 2, w + 12, hh - 4, TINT['brand'], EDGE['brand'], 8))
        elif k % 2: bg.append(R(x0, cy0 + 1, x1 - x0, hh - 2, '#F8F9FA', None, 4))
        by = cy0 + hh - 6 - _lane_ghost(bars) - BAR / 2
        nx = x + (16 if ln['depth'] else 0)
        if ln['children']: out.append(_caret(nx, by if not ln.get('note') else by - 9, not ln.get('collapsed'))); nx += 14
        nw = lab - 12 - (nx - x)
        if ln.get('note'):
            out.append(Tx(nx, by - 9, ln['name'], S, INK, True, 'start', nw)); out.append(Tx(nx, by + 11, ln['note'], SMALL, MUTED, False, 'start', nw))
        else: out.append(Tx(nx, by, ln['name'], S, INK if not ln['depth'] else BODY, not ln['depth'], 'start', nw))
        if not bars and ln['children']:     # an open parent without bars of its own: a light span over its children
            ch = [c for c in m['lanes'] if c.get('parent') == ln['key']]
            s0 = min(br['s'] for c in ch for br in c['bars']); e0 = max(br['e'] for c in ch for br in c['bars'])
            out.append(R(X(s0), by - 3, X(e0) - X(s0), 6, '#E9E2D8', None, 3))
        stops = [X(ms['t'] + ms['tw'] / 2) for ms, *_ in place] + ([tx] if tx is not None else [])
        for br in bars:
            col = PHASE_COL[br['pi']]; b0, b1 = X(br['s']) + 1.5, X(br['e']) - 1.5; foc = br['key'] == m['focus']
            st = br.get('status'); stroke = RISK if (br.get('risk') or st == 'risk') else (INK if foc else None)
            if 'bs' in br and (abs(br['bs'] - br['s']) > 1e-9 or abs(br['be'] - br['e']) > 1e-9):
                g0, g1 = X(br['bs']) + 1.5, X(br['be']) - 1.5
                out.append(R(g0, by + BAR / 2 + 3, g1 - g0, GHOST, 'none', MUTED, 2, True, 1.1))
                d = slip(br['e'] - br['be'], gran, br['e'])
                if d: out.append(Tx(max(b1, g1) + 6, by + BAR / 2 + 3 + GHOST / 2, d, SMALL, RISK if br['e'] > br['be'] else OK_INK, True))
            if tx is not None and tx < b1:
                out.append(R(max(b0, tx), by - BAR / 2, b1 - max(b0, tx), BAR, _mix(col), col, 5, True, 1.2))
                if tx > b0: out.append(R(b0, by - BAR / 2, tx - b0, BAR, col, None, 5))
            else: out.append(R(b0, by - BAR / 2, b1 - b0, BAR, col, None, 5))
            if br.get('progress') is not None:
                # a thin in-bar track (white) with the done part in deep orange, as KZGantt — a progress bar, not a rule
                pg = GT['progress']; tw0, ph = b1 - b0 - 10, pg['height']; pw = tw0 * br['progress'] / 100; py = by + BAR / 2 - ph - 3
                out.append(R(b0 + 5, py, tw0, ph, _mix(col, pg['track_opacity']), None, ph / 2))
                if pw > .5: out.append(R(b0 + 5, py, max(ph, pw), ph, pg['fill'], None, ph / 2))
            if stroke: out.append(R(b0 - 1, by - BAR / 2 - 1, b1 - b0 + 2, BAR + 2, 'none', stroke, 6, False, 2))
            icon_w = icon_l = 0
            if st in STATUS_ICON and b1 - b0 >= 26:
                # at the end of the bar, else at its start when a milestone glyph sits there; no room at either end → no icon
                # (the same rule as KZGantt)
                gl = [X(ms['t'] + ms['tw'] / 2) for ms, *_ in place]
                ix = next((v for v in (b1 - 19, b0 + 3) if all(g < v - 10 or g > v + 26 for g in gl)), None)
                if ix is not None:
                    out.append(icon(STATUS_ICON[st], ix, by - 8, 16, RISK if st == 'risk' else on_color(col if (tx is None or ix + 8 < tx) else _mix(col)), mode))
                    if ix > (b0 + b1) / 2: icon_w = 20
                    else: icon_l = 20
            text = br.get('label') or br['phase']
            if br.get('progress') is not None: text = f'{text} · {br["progress"]:g}%'
            tw = W(text, SMALL, True)
            if tw + 14 + icon_w + icon_l <= b1 - b0:
                # keep the label clear of the pinned glyphs and the today line: centred, else at either end of the bar
                fits = lambda c: all(abs(c - sx) > tw / 2 + PIN + 3 for sx in stops)
                cx = next((c for c in ((b0 + icon_l + b1 - icon_w) / 2, b0 + icon_l + 7 + tw / 2, b1 - 7 - icon_w - tw / 2) if fits(c)), (b0 + icon_l + b1 - icon_w) / 2)
                out.append(Tx(cx, by, text, SMALL, on_color(col if (tx is None or cx < tx) else _mix(col)), True, 'middle'))
            elif br.get('label') and not br.get('summary'):
                raise ValueError(f'阶段条「{text}」太短放不下标签：缩短 label、加宽时间轴或拆页')
        for ms, cx, lx_, lv in place:
            cx += x; lx_ += x
            past = now is not None and ms['t'] < now; foc = ms['key'] == m['focus']
            ink = RISK if ms.get('risk') else INK
            gy = by - BAR / 2 - 1; ly_ = gy - PIN - 4 - LINE / 2 - lv * LINE
            if 'bt' in ms and abs(ms['bt'] - ms['t']) > 1e-9:      # the planned date: a hollow grey glyph, a dotted lead to now
                bx = X(ms['bt'] + ms['btw'] / 2)
                out.append(Ln(bx, gy, cx, gy, MUTED, 1, True))
                out.append(glyph(ms['kind'], bx, gy, PIN - 1, '#FFFFFF', MUTED, 1.2))
            if lv: out.append(Ln(cx, ly_ + 9, cx, gy - PIN - 2, '#B9C0C7', 1, True))
            out.append(Tx(lx_, ly_, ms['label'], S, ink if (foc or ms.get('risk')) else BODY, foc or bool(ms.get('risk')), 'middle'))
            if foc: out.append(f'<circle cx="{f(cx)}" cy="{f(gy)}" r="{f(PIN + 5.5)}" fill="{TINT["brand"]}" stroke="{EDGE["brand"]}" stroke-width="1.5"/>')
            out.append(f'<circle cx="{f(cx)}" cy="{f(gy)}" r="{f(PIN + 1.8)}" fill="#FFFFFF"/>')
            ic = ms.get('icon')
            if ic and ic not in MS_KINDS:
                out.append(f'<circle cx="{f(cx)}" cy="{f(gy)}" r="{f(PIN + 1.5)}" fill="{ink if past or now is None else "#FFFFFF"}" stroke="{ink}" stroke-width="1.4"/>')
                out.append(icon(ic, cx - PIN + .5, gy - PIN + .5, 2 * PIN - 1, '#FFFFFF' if past or now is None else ink, mode))
            else:
                out.append(glyph(ic or ms['kind'], cx, gy, PIN, ink if past or now is None else '#FFFFFF', None if past or now is None else ink, 1.6))
        bg.append(Ln(x, cy0 + hh, x1, cy0 + hh, '#EEF0F2', 1)); cy0 += hh
    out = out[:head_n] + bg + ([Ln(tx, ay + 22, tx, bot + 4, GT['today']['line'], GT['today']['width'], True)] if tx is not None else []) + out[head_n:]
    if tx is not None:
        tv = spec.get('today'); tu = gran if tv in (None, 'auto') else tspan(tv, 'today')[2]
        t = f'当前 {ttext(now, tu if GRANS.index(tu) < GRANS.index(gran) else gran)}'; tw = W(t, SMALL, True) + 14
        out.append(R(min(max(tx - tw / 2, x0), x1 - tw), bot + 5, tw, 20, GT['today']['pill'], None, 10))
        out.append(Tx(min(max(tx - tw / 2, x0), x1 - tw) + tw / 2, bot + 15, t, SMALL, GT['today']['text'], True, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- texts bound to the plan (08 GANTT-07)
_TOK = _re.compile(r'\{([A-Za-z0-9_\-]+(?:\.(?:start|end))?|gap:[A-Za-z0-9_\-]+(?:\.(?:start|end))?,[A-Za-z0-9_\-]+(?:\.(?:start|end))?)\}')
BIND_OPEN, BIND_MID, BIND_CLOSE = '\ue000', '\ue001', '\ue002'   # private-use marks, never in content

def _cn(v):
    """A time value as prose: 2028Q1 · 2028 年 3 月 · 2028 年 3 月 15 日 (the same in runtime/kz-gantt.js)."""
    u = tspan(v, '时间')[2]
    if u == 'quarter': return v
    if u == 'month': return f'{v[:4]} 年 {int(v[5:7])} 月'
    return f'{v[:4]} 年 {int(v[5:7])} 月 {int(v[8:10])} 日'

def bind_value(expr, spec):
    """{key} → a milestone's date, or a phase's start–end; {key.start} / {key.end}; {gap:a,b} → b − a in the plan's
    granularity (个季度 / 个月 / 天), points being a milestone's date or a phase's start (or .end)."""
    items = {}
    for ln in spec['lanes']:
        for b in ln.get('bars') or []: items[b['key']] = ('bar', b)
        for m in ln.get('milestones') or []: items[m['key']] = ('ms', m)
    def raw(ref):
        key, _, part = ref.partition('.')
        if key not in items: raise ValueError(f'绑定文字里的「{key}」不是任何阶段或里程碑的 key')
        kind, o = items[key]
        if kind == 'ms':
            if part: raise ValueError(f'里程碑「{key}」没有 .{part}')
            return o['at'], None
        return (o['start'], 'start') if part == 'start' else (o['end'], 'end') if part == 'end' else (o['start'], o['end'])
    if expr.startswith('gap:'):
        a, b = expr[4:].split(',')
        def point(ref):
            v, w = raw(ref); s0, e0, _ = tspan(v, '时间'); return e0 if w == 'end' else s0
        d, g = point(b) - point(a), program_model(spec)['granularity']
        if g == 'day':
            n = abs((_dt.date.fromisoformat(ttext(point(b) + 1e-7, 'day')) - _dt.date.fromisoformat(ttext(point(a) + 1e-7, 'day'))).days); return f'{n} 天'
        return f'{abs(round(d * (3 if g == "month" else 1)))} {"个月" if g == "month" else "个季度"}'
    v, w = raw(expr)
    if w is None or w in ('start', 'end'): return _cn(v)
    return f'{_cn(v)}–{_cn(w)}'

def bind_text(template, spec, marked=False):
    """Replace {…} tokens with values; marked=True wraps each value as exprvalue for the HTML Text,
    which turns it into <span data-kz-bind="expr"> so the live Gantt can update it."""
    return _TOK.sub(lambda m: (f'{BIND_OPEN}{m[1]}{BIND_MID}{bind_value(m[1], spec)}{BIND_CLOSE}' if marked else bind_value(m[1], spec)), template)
