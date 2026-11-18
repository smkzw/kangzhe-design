"""Longitudinal family (round 9): change over visits on a true time axis, efficacy and safety measures alike.

One contract (longitudinal_model = runtime/kz-clinical.js KZClinical.longitudinal) for five kinds:
  longitudinal       per arm (or blinded overall) estimate ± interval at each visit, points dodged, lines not drawn across
                     missing visits, the primary visit tinted, reference lines / normal range, n per visit under the axis
  longitudinal-diff  each treat arm minus the comparator over time (estimate and CI, reference 0)
  lab-boxplot        the distribution per visit (whisker, Q1–Q3 box, median) per arm, normal range, n per visit
  lab-multiples      small multiples: several measures (labs, vital signs) each a mini panel with its own scale and range
  completeness       per visit: still in study and with data, against the expected count (works blinded)

Rules from /tmp/kz8/research-r9/charts.md (G3–G6, G9, §2–§3): the x axis is the visit's study time (t), never the
visit number; the interval type is always named (95% CI / SE / SD / IQR); null is no data (a gap, never 0); blinded data
carry one overall series only — no arms, no differences — and are marked for internal use.

spec: {measure: {label, unit?, stat?, interval: ci95|se|sd|iqr|box, better?: higher|lower},
       time_unit?: '周', visits: [{label, t}] (2–16, t increasing), primary?: visit label,
       blinded?: bool, arms?: [{key, name, role?: treat|comparator}] (1–4; omitted when blinded),
       series?: {arm: [[est, lo, hi, n] | null per visit]}, boxes?: {arm: [[lo, q1, med, q3, hi, n] | null]},
       diff?: {treat arm: [[est, lo, hi] | null]}, expected?: [n per visit], in_study?: [n per visit ≤ expected],
       ref?: {lines?: [{label, value}], range?: {lo?, hi?, label?}}, focus?: arm key, note?}
lab-multiples: {panels: [spec without arms, sharing the visits and arms of the page], visits, arms?, blinded?, time_unit?}.
"""
import math
from .diagrams import kind
from .diagram_kinds import R, Ln, Tx, Dot, S, SMALL, TINT
from .tree import TOK, INK, BODY, MUTED
from . import text as T

INTERVALS = {'ci95': '95% CI', 'se': '± SE', 'sd': '± SD', 'iqr': 'IQR', 'box': '中位数与四分位'}
BLIND_KEY = 'all'
OVERALL = '#5F6B76'   # one neutral hue for blinded overall data (no arm colours)

def W(s, size=S, bold=False): return T.width(T.plain(s), size, bold)
def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
def _int(v): return isinstance(v, int) and not isinstance(v, bool)

def longitudinal_model(spec):
    me = spec.get('measure') or {}; vis = spec.get('visits') or []; blind = bool(spec.get('blinded'))
    if not me.get('label'): raise ValueError('历时变化需要 measure.label（指标名）')
    if me.get('interval') not in INTERVALS: raise ValueError(f'measure.interval 须是 {"、".join(INTERVALS)} 之一（误差范围必须写明是什么）')
    if me.get('better') not in (None, 'higher', 'lower'): raise ValueError('measure.better 须是 higher、lower 或不写')
    if not 2 <= len(vis) <= 16: raise ValueError('历时变化需要 2–16 个访视 visits：[{label, t}]')
    ts = []
    for v in vis:
        if not v.get('label') or not _num(v.get('t')): raise ValueError('每个访视需要 label 与数值时间 t（研究时间，不是访视序号）')
        if ts and v['t'] <= ts[-1]: raise ValueError(f'访视时间 t 须递增：{v["label"]}')
        ts.append(v['t'])
    labels = [v['label'] for v in vis]
    if len(set(labels)) != len(labels): raise ValueError('访视 label 不能重复')
    prim = spec.get('primary')
    if prim is not None and prim not in labels: raise ValueError(f'primary「{prim}」不是访视之一')
    arms = spec.get('arms') or []
    if blind:
        if arms or spec.get('diff'): raise ValueError('盲态数据只能有一条全体合并的序列：不写 arms、不写 diff（编码分组视同揭盲）')
        arms = [{'key': BLIND_KEY, 'name': '全体（盲态）', 'role': 'overall'}]
    else:
        if not 1 <= len(arms) <= 4: raise ValueError('历时变化需要 1–4 个组 arms（盲态数据写 blinded: true）')
        keys = [a.get('key') for a in arms]
        if len(set(keys)) != len(keys) or not all(keys) or BLIND_KEY in keys: raise ValueError('arms 的 key 须不重复、非空，且不能用 all')
        for a in arms:
            if not a.get('name'): raise ValueError(f'组「{a["key"]}」需要 name')
            if a.get('role', 'treat') not in ('treat', 'comparator'): raise ValueError(f'组「{a["key"]}」的 role 须是 treat 或 comparator')
        if sum(1 for a in arms if a.get('role') == 'comparator') > 1: raise ValueError('comparator 最多一个')
    ak = [a['key'] for a in arms]; n = len(vis)
    box = me['interval'] == 'box'; data = spec.get('boxes' if box else 'series') or {}
    if set(data) != set(ak): raise ValueError(f'{"boxes" if box else "series"} 须给每个组一行：{"、".join(ak)}')
    rows = {}
    for k in ak:
        r = data[k]
        if not isinstance(r, list) or len(r) != n: raise ValueError(f'「{k}」须给 {n} 个访视的值（无数据写 null）')
        out = []
        for j, c in enumerate(r):
            if c is None: out.append(None); continue
            where = f'「{k}」{labels[j]}'
            if box:
                if not (isinstance(c, list) and len(c) == 6 and all(_num(x) for x in c[:5]) and _int(c[5]) and c[5] >= 0): raise ValueError(f'{where} 须是 [下须, Q1, 中位数, Q3, 上须, n]')
                if not c[0] <= c[1] <= c[2] <= c[3] <= c[4]: raise ValueError(f'{where} 须满足 下须 ≤ Q1 ≤ 中位数 ≤ Q3 ≤ 上须')
                out.append({'lo': c[0], 'q1': c[1], 'est': c[2], 'q3': c[3], 'hi': c[4], 'n': c[5]})
            else:
                if not (isinstance(c, list) and len(c) == 4 and all(_num(x) for x in c[:3]) and _int(c[3]) and c[3] >= 0): raise ValueError(f'{where} 须是 [估计, 下限, 上限, n]')
                if not c[1] <= c[0] <= c[2]: raise ValueError(f'{where} 须满足 下限 ≤ 估计 ≤ 上限')
                out.append({'est': c[0], 'lo': c[1], 'hi': c[2], 'n': c[3]})
        rows[k] = out
    comp = next((a['key'] for a in arms if a.get('role') == 'comparator'), None)
    diff = {}
    for k, r in (spec.get('diff') or {}).items():
        if comp is None: raise ValueError('diff 需要一个 comparator 组')
        if k not in ak or k == comp: raise ValueError(f'diff 的「{k}」须是治疗组')
        if not isinstance(r, list) or len(r) != n: raise ValueError(f'diff「{k}」须给 {n} 个访视的值')
        out = []
        for j, c in enumerate(r):
            if c is None: out.append(None); continue
            if not (isinstance(c, list) and len(c) == 3 and all(_num(x) for x in c) and c[1] <= c[0] <= c[2]): raise ValueError(f'diff「{k}」{labels[j]} 须是 [估计, 下限, 上限]，下限 ≤ 估计 ≤ 上限')
            out.append({'est': c[0], 'lo': c[1], 'hi': c[2]})
        diff[k] = out
    exp = spec.get('expected')
    if exp is not None and not (isinstance(exp, list) and len(exp) == n and all(_int(x) and x >= 0 for x in exp)): raise ValueError(f'expected 须是 {n} 个访视的应到人数')
    ins = spec.get('in_study')
    if ins is not None and not (exp and isinstance(ins, list) and len(ins) == n and all(_int(v) and 0 <= v <= e for v, e in zip(ins, exp))): raise ValueError('in_study 须是各访视仍在研究的人数（不超过 expected）')
    ref = spec.get('ref') or {}; lines = ref.get('lines') or []; rng = ref.get('range')
    extra = [k for k in ref if k not in ('lines', 'range')]
    if extra: raise ValueError('ref 只认 range（{lo, hi}）与 lines（[{label, value}]），不认「' + '、'.join(extra) + "」：参考线写成 lines: [{label: 'ULN', value: 40}]")
    if not isinstance(lines, list): raise ValueError('ref.lines 须是数组 [{label, value}]')
    for l in lines:
        if not l.get('label') or not _num(l.get('value')): raise ValueError('参考线需要 label 与数值 value')
    if rng is not None and not (any(_num(rng.get(k)) for k in ('lo', 'hi')) and all(rng.get(k) is None or _num(rng[k]) for k in ('lo', 'hi'))): raise ValueError('参考范围 range 需要数值 lo 和/或 hi')
    if spec.get('focus') is not None and spec['focus'] not in ak: raise ValueError(f'focus「{spec["focus"]}」不是组之一')
    vals = [x for r in rows.values() for c in r if c for x in (c['lo'], c['hi'])] + [l['value'] for l in lines] + [rng[k] for k in ('lo', 'hi') if rng and rng.get(k) is not None]
    dvals = [x for r in diff.values() for c in r if c for x in (c['lo'], c['hi'])] + ([0] if diff else [])
    cat = TOK['charts']['categorical']; color = {}; ti = 0
    for a in arms:
        if a.get('role') == 'overall': color[a['key']] = OVERALL
        elif a.get('role') == 'comparator': color[a['key']] = TOK['charts']['comparator']
        else: color[a['key']] = cat[ti % len(cat)]; ti += 1
    return {'measure': me, 'visits': vis, 't': ts, 'labels': labels, 'primary': labels.index(prim) if prim is not None else None, 'blinded': blind,
            'arms': [{'role': 'treat', **a} for a in arms], 'rows': rows, 'diff': diff, 'comp': comp, 'expected': exp, 'in_study': ins, 'lines': lines, 'range': rng,
            'box': box, 'color': color, 'focus': spec.get('focus'), 'unit': me.get('unit') or '', 'time_unit': spec.get('time_unit') or '周',
            'domain': nice(min(vals), max(vals)) if vals else (0, 1, .2), 'ddomain': nice(min(dvals), max(dvals)) if dvals else None}

def nice(lo, hi, n=5):
    """A tidy axis [lo, hi] with a 1-2-2.5-5 step around the data (4–6 ticks)."""
    if hi == lo: hi, lo = hi + 1, lo - 1
    # non-negative data (rates, counts, lab values) never get an axis below 0: a −20% tick under a response rate reads as data
    pad = (hi - lo) * .06; lo, hi = (max(0, lo - pad) if lo >= 0 else lo - pad), hi + pad; raw = (hi - lo) / n; mag = 10 ** math.floor(math.log10(raw))
    st = next(k * mag for k in (1, 2, 2.5, 5, 10) if k * mag >= raw - 1e-12)
    return math.floor(lo / st + 1e-9) * st, math.ceil(hi / st - 1e-9) * st, st

def fmt(v, st):
    d = 0 if st >= 1 else min(3, max(1, -math.floor(math.log10(st) + 1e-9)))
    s = f'{v:.{d}f}'; return '0' if s in ('-0', '-0.0', '-0.00') else s.replace('-', '−')

def _ticks(lo, hi, st):
    out, v = [], lo
    while v <= hi + st * 1e-6: out.append(round(v, 10)); v += st
    return out

# ---------------------------------------------------------------- shared frame: legend, axes, visits, n table
def _frame(m, box, ntable=True, diff=False, legend=True):
    x, y, w, h = box; arms = m['arms'] if not diff else [a for a in m['arms'] if a['key'] in m['diff']]
    lo, hi, st = m['ddomain'] if diff else m['domain']
    nrows = len(m['arms']) if ntable else 0
    lab_w = max([W(f'{a["name"]}', SMALL, True) for a in m['arms']] + [W('n', SMALL)]) + 16 if ntable or diff else 0   # the diff panel keeps the same left edge, so stacked time axes line up
    x0 = x + max(56, lab_w); x1 = x + w - 16; top = y + (30 if legend else 6); bot = y + h - 26 - nrows * 22
    t0, t1 = m['t'][0], m['t'][-1]; span = (t1 - t0) or 1; pad = span * .04
    X = lambda t: x0 + (t - t0 + pad) / (span + 2 * pad) * (x1 - x0); Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
    out = []
    if m['primary'] is not None:
        px = X(m['t'][m['primary']]); out.append(R(px - 16, top, 32, bot - top, TINT['brand'], None, 6))
        out.append(Tx(px, top - 10 if not legend else top + 10, '主要终点', SMALL, '#9A4D00', True, 'middle'))
    for v in _ticks(lo, hi, st):
        out.append(Ln(x0, Y(v), x1, Y(v), TOK['charts']['grid'], 1)); out.append(Tx(x0 - 8, Y(v), fmt(v, st), SMALL, MUTED, False, 'end'))
    if lo < 0 < hi or diff: out.append(Ln(x0, Y(0), x1, Y(0), '#9AA1A8', 1.2))
    out.append(Ln(x0, bot, x1, bot, TOK['charts']['axis'], 1.2))
    for j, (t, lab) in enumerate(zip(m['t'], m['labels'])):
        out.append(Ln(X(t), bot, X(t), bot + 4, TOK['charts']['axis'], 1)); out.append(Tx(X(t), bot + 14, lab, SMALL, INK if j == m['primary'] else MUTED, j == m['primary'], 'middle'))
    if ntable:
        for r, a in enumerate(m['arms']):
            ry = bot + 36 + r * 22; out.append(Tx(x0 - 8, ry, a['name'] if not m['blinded'] else 'n', SMALL, m['color'][a['key']] if a['role'] != 'comparator' else BODY, True, 'end'))
            for j, t in enumerate(m['t']):
                c = (m['rows'][a['key']] or [None] * len(m['t']))[j]; out.append(Tx(X(t), ry, str(c['n']) if c else '—', SMALL, BODY if c else MUTED, False, 'middle'))
    if legend:
        lx = x0
        for a in arms:
            out.append(Dot(lx + 6, y + 10, 5, m['color'][a['key']])); out.append(Tx(lx + 16, y + 10, a['name'], SMALL, INK, True, 'start')); lx += W(a['name'], SMALL, True) + 34
        it = INTERVALS[m['measure']['interval']] if not diff else '95% CI'
        stat = ('与对照之差' if diff else m['measure'].get('stat') or ('中位数' if m['box'] else '均值'))
        cap = f'{stat}（{m["unit"]}）· {it}' if m['unit'] else f'{stat} · {it}'
        out.append(Tx(x + w - 4, y + 10, cap + ('  · 盲态汇总，仅限内部' if m['blinded'] else ''), SMALL, MUTED, False, 'end'))
    return out, X, Y, top, bot

def _dodge(m, k, arms):
    na = len(arms); return (k - (na - 1) / 2) * 7

def _ref(m, X, Y, x0, x1, top, bot, out):
    # labels sit over the widest gap between visits, so they never cross a whisker or a box at the plot's end
    ts = m['t']; j = max(range(len(ts) - 1), key=lambda k: ts[k + 1] - ts[k]); gx = (X(ts[j]) + X(ts[j + 1])) / 2
    rng = m['range']
    if rng:
        lo = rng.get('lo'); hi = rng.get('hi'); ya = Y(hi) if hi is not None else top; yb = Y(lo) if lo is not None else bot
        ya, yb = max(top, min(bot, ya)), max(top, min(bot, yb))
        # a reference line on the band's edge (ULN = range hi) would read as a coloured edge bar (02 LG-02): the band stops short of it
        on = {round(Y(l['value']), 1) for l in m['lines']}
        if round(ya, 1) in on: ya += 6
        if round(yb, 1) in on: yb -= 6
        out.insert(0, R(x0, ya, x1 - x0, max(1, yb - ya), TINT['ok'], None, 0))
        if rng.get('label'): out.append(Tx(gx, ya + 10, rng['label'], SMALL, '#3D6B1F', False, 'middle'))
    for l in m['lines']:
        out.append(Ln(x0, Y(l['value']), x1, Y(l['value']), '#C00000', 1.2, True)); out.append(Tx(gx, Y(l['value']) - 9, l['label'], SMALL, '#C00000', True, 'middle'))

def _lm(spec, w):
    m = longitudinal_model(spec); return 220 + len(m['arms']) * 22

@kind('longitudinal', measure=_lm)
def longitudinal(spec, box, gid, mode):
    """Estimate ± interval per arm at each visit on the true time axis (see module doc)."""
    m = longitudinal_model(spec); x, y, w, h = box
    out, X, Y, top, bot = _frame(m, box); x0, x1 = X(m['t'][0]) - 20, x + w - 16
    _ref(m, X, Y, min(x0, X(m['t'][0]) - 10), x1, top, bot, out)
    for k, a in enumerate(m['arms']):
        col = m['color'][a['key']]; r = m['rows'][a['key']]; fo = a['key'] == m['focus']; prev = None
        # boxes side by side per visit: the slot per arm is capped by the narrowest visit gap, so W0 and W4 never overlap
        na = len(m['arms']); gap = min(X(b_) - X(a_) for a_, b_ in zip(m['t'], m['t'][1:]))
        slot = min(max(8, min(22, 60 / na)) + 4, gap * .92 / na); bw = max(4, slot - 4)
        dx = (k - (na - 1) / 2) * slot if m['box'] else _dodge(m, k, m['arms'])
        for j, c in enumerate(r):
            if c is None: prev = None; continue
            px, py = X(m['t'][j]) + dx, Y(c['est'])
            if m['box']:
                out.append(Ln(px, Y(c['hi']), px, Y(c['lo']), col, 1.4)); out.append(R(px - bw / 2, Y(c['q3']), bw, max(1, Y(c['q1']) - Y(c['q3'])), '#FFFFFF', col, 2, sw=1.6))
                out.append(Ln(px - bw / 2, py, px + bw / 2, py, col, 2.4))
            else:
                if prev: out.append(Ln(prev[0], prev[1], px, py, col, 2.6 if fo else 2))
                out.append(Ln(px, Y(c['hi']), px, Y(c['lo']), col, 1.4)); out.append(Ln(px - 3, Y(c['hi']), px + 3, Y(c['hi']), col, 1.4)); out.append(Ln(px - 3, Y(c['lo']), px + 3, Y(c['lo']), col, 1.4))
            prev = (px, py)
        if not m['box']:
            for j, c in enumerate(r):
                if c: out.append(Dot(X(m['t'][j]) + dx, Y(c['est']), 4.5 if fo else 4, col, '#FFFFFF'))
    return ''.join(out)

def _ldm(spec, w):
    longitudinal_model(spec); return 150

@kind('longitudinal-diff', measure=_ldm)
def longitudinal_diff(spec, box, gid, mode):
    """Each treat arm minus the comparator over time: estimate and 95% CI per visit, reference 0, the primary visit tinted."""
    m = longitudinal_model(spec)
    if not m['diff']: raise ValueError('组间差图需要 diff（各治疗组对 comparator 的差与 95% CI）')
    x, y, w, h = box; arms = [a for a in m['arms'] if a['key'] in m['diff']]
    out, X, Y, top, bot = _frame(m, box, ntable=False, diff=True)
    for k, a in enumerate(arms):
        col = m['color'][a['key']]; dx = _dodge(m, k, arms); prev = None
        for j, c in enumerate(m['diff'][a['key']]):
            if c is None: prev = None; continue
            px, py = X(m['t'][j]) + dx, Y(c['est']); ns = c['lo'] <= 0 <= c['hi']
            if prev: out.append(Ln(prev[0], prev[1], px, py, col, 1.6, True))
            out.append(Ln(px, Y(c['hi']), px, Y(c['lo']), col if not ns else '#9AA1A8', 2.4))
            out.append(Dot(px, py, 4.5, col if not ns else '#FFFFFF', '#FFFFFF' if not ns else '#9AA1A8')); prev = (px, py)
    return ''.join(out)

def _cm(spec, w):
    longitudinal_model(spec); return 230

@kind('completeness', measure=_cm)
def completeness(spec, box, gid, mode):
    """Data completeness per visit (FDA STF-IG fig. 11, also blinded): the expected count as an outline, still in study
    as a light bar, with data as the solid bar and its percentage of the expected."""
    m = longitudinal_model(spec)
    if not m['expected']: raise ValueError('数据完整性需要 expected（各访视应到人数）')
    x, y, w, h = box; n = len(m['t']); exp = m['expected']
    have = [sum((m['rows'][a['key']][j] or {}).get('n', 0) for a in m['arms']) for j in range(n)]
    insd = [max(have[j], (m['in_study'] or exp)[j]) for j in range(n)]
    top_v = max(exp) * 1.1; x0 = x + 56; x1 = x + w - 8; top = y + 30; bot = y + h - 26; bwid = (x1 - x0) / n * .56
    Y = lambda v: bot - v / top_v * (bot - top); out = []
    out.append(R(x0, y + 4, 12, 12, '#FFFFFF', '#9AA1A8', 3)); out.append(Tx(x0 + 18, y + 10, '应到', SMALL, BODY))
    out.append(R(x0 + 70, y + 4, 12, 12, '#E7EBEE', None, 3)); out.append(Tx(x0 + 88, y + 10, '仍在研究', SMALL, BODY))
    if m['blinded']: out.append(Tx(x + w - 4, y + 10, '盲态汇总，仅限内部', SMALL, MUTED, False, 'end'))
    out.append(R(x0 + 172, y + 4, 12, 12, OVERALL if m['blinded'] else TOK['charts']['categorical'][0], None, 3)); out.append(Tx(x0 + 190, y + 10, f'有{m["measure"]["label"]}数据', SMALL, BODY))
    lo, hi, st = 0, top_v, nice(0, max(exp))[2]
    for v in _ticks(0, max(exp), st): out.append(Ln(x0, Y(v), x1, Y(v), TOK['charts']['grid'], 1)); out.append(Tx(x0 - 8, Y(v), f'{v:,.0f}', SMALL, MUTED, False, 'end'))
    for j in range(n):
        cx = x0 + (j + .5) * (x1 - x0) / n
        out.append(R(cx - bwid / 2, Y(exp[j]), bwid, bot - Y(exp[j]), '#FFFFFF', '#9AA1A8', 3))
        out.append(R(cx - bwid / 2 + 3, Y(insd[j]), bwid - 6, bot - Y(insd[j]), '#E7EBEE', None, 2))
        out.append(R(cx - bwid / 2 + 7, Y(have[j]), bwid - 14, bot - Y(have[j]), OVERALL if m['blinded'] else TOK['charts']['categorical'][0], None, 2))
        out.append(Tx(cx, Y(exp[j]) - 10, f'{have[j] / exp[j] * 100:.0f}%' if exp[j] else '—', SMALL, INK, True, 'middle'))
        out.append(Tx(cx, bot + 14, m['labels'][j], SMALL, INK if j == m['primary'] else MUTED, j == m['primary'], 'middle'))
    out.append(Ln(x0, bot, x1, bot, TOK['charts']['axis'], 1.2))
    return ''.join(out)

def multiples_model(spec):
    ps = spec.get('panels') or []
    if not 2 <= len(ps) <= 9: raise ValueError('小倍数需要 2–9 个指标 panels')
    shared = {k: spec[k] for k in ('visits', 'arms', 'blinded', 'time_unit', 'primary') if k in spec}
    return [longitudinal_model({**shared, **p}) for p in ps]

def _mm(spec, w):
    ms = multiples_model(spec); cols = 3 if len(ms) > 4 else 2; return math.ceil(len(ms) / cols) * 170 + 26

@kind('lab-multiples', measure=_mm)
def lab_multiples(spec, box, gid, mode):
    """Small multiples (safety labs, vital signs): one mini panel per measure with its own scale — name and unit, normal
    range band, the estimate per arm per visit (median for boxes), the visit labels only on the bottom row; one legend."""
    ms = multiples_model(spec); x, y, w, h = box; n = len(ms); cols = 3 if n > 4 else 2; rows = math.ceil(n / cols)
    gap = 18; pw = (w - gap * (cols - 1)) / cols; ph = (h - 26 - gap * (rows - 1)) / rows; out = []
    m0 = ms[0]; lx = x
    for a in m0['arms']:
        out.append(Dot(lx + 6, y + 10, 5, m0['color'][a['key']])); out.append(Tx(lx + 16, y + 10, a['name'], SMALL, INK, True)); lx += W(a['name'], SMALL, True) + 34
    out.append(Tx(x + w, y + 10, ('盲态汇总，仅限内部 · ' if m0['blinded'] else '') + '各指标自有刻度；绿带为参考范围', SMALL, MUTED, False, 'end'))
    for i, m in enumerate(ms):
        r, c = divmod(i, cols); px, py = x + c * (pw + gap), y + 26 + r * (ph + gap)
        out.append(R(px, py, pw, ph, '#FFFFFF', '#E7EBEE', 10))
        it = INTERVALS[m['measure']['interval']]
        out.append(Tx(px + 12, py + 16, m['measure']['label'] + (f'（{m["unit"]}）' if m['unit'] else ''), S, INK, True))
        out.append(Tx(px + pw - 10, py + 16, it, SMALL, MUTED, False, 'end'))
        lo, hi, st = m['domain']; x0 = px + 48; x1 = px + pw - 12; top = py + 34; bot = py + ph - (22 if r == rows - 1 else 10)
        t0, t1 = m['t'][0], m['t'][-1]; sp = (t1 - t0) or 1; pad = sp * .05
        X = lambda t: x0 + (t - t0 + pad) / (sp + 2 * pad) * (x1 - x0); Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
        sub = []
        _ref({**m, 'lines': m['lines']}, X, Y, x0, x1, top, bot, sub)
        for v in (lo, hi): sub.append(Tx(x0 - 6, Y(v), fmt(v, st), SMALL, MUTED, False, 'end'))
        sub.append(Ln(x0, bot, x1, bot, TOK['charts']['axis'], 1))
        # the primary visit's tint goes over the range band (not under it), so it reads as one full-height column
        if m['primary'] is not None: sub.insert(1 if m['range'] else 0, R(X(m['t'][m['primary']]) - 10, top, 20, bot - top, TINT['brand'], None, 4))
        if r == rows - 1:
            for j, t in enumerate(m['t']):
                if j in (0, len(m['t']) - 1) or j == m['primary']: sub.append(Tx(X(t), bot + 11, m['labels'][j], SMALL, MUTED, False, 'middle'))
        for k, a in enumerate(m['arms']):
            col = m['color'][a['key']]; prev = None; dx = _dodge(m, k, m['arms']) * .6
            for j, cc in enumerate(m['rows'][a['key']]):
                if cc is None: prev = None; continue
                qx, qy = X(m['t'][j]) + dx, Y(cc['est'])
                if prev: sub.append(Ln(prev[0], prev[1], qx, qy, col, 1.8))
                sub.append(Ln(qx, Y(cc.get('q3', cc['hi'])), qx, Y(cc.get('q1', cc['lo'])), col, 1.2)); sub.append(Dot(qx, qy, 3, col)); prev = (qx, qy)
        out += sub
    return ''.join(out)

@kind('lab-boxplot', measure=_lm)
def lab_boxplot(spec, box, gid, mode):
    """Distribution over time per arm (laboratory values are skewed and the tail matters): whisker, Q1–Q3 box and median
    per visit, reference lines (ULN) and the normal range, n per visit under the axis."""
    if (spec.get('measure') or {}).get('interval') != 'box': raise ValueError('箱线图的 measure.interval 须是 box，数据写在 boxes')
    return longitudinal(spec, box, gid, mode)
