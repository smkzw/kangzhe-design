"""8.0 clinical scenario families, batch 2 (static diagram kinds). Same conventions as diagram_clinical.py — labels 16 px,
scale marks 14 px, native shapes and text in PPTX, the same geometry inline in HTML; every number is computed from the
data contract. Each *_model mirrors runtime/kz-clinical.js (same rules, order and messages; the maintainers'
regression tests run both on the same cases), so a scenario file is accepted or rejected the same way by the static template, the regular
demo form, the flagship stage and the flagship PPTX page.

  exposure   multi-indication exposure summary: subjects exposed per indication / study by cumulative duration band
             (any, ≥26 weeks, ≥52 weeks …), patient-years, totals against the exposure targets (e.g. ICH E1)
  trialflow  trial flow with subflows: shared periods (screening, run-in) → randomisation → arms of contiguous segments
             (titration, maintenance, placebo …) → an optional re-randomisation of one arm into 2–3 sub-arms → shared
             follow-up; endpoints on the time axis and sub-studies across arms
  landscape  competitive landscape: assets (ours + synthetic competitors) by development stage, one efficacy and one
             safety metric (each with its own better direction; null = no data, never 0), ranks and the best per metric
  efficacy   efficacy summary: continuous (LS mean change) and binary (n/N → %) endpoints per arm, each treat arm against
             the one comparator with the reported difference and 95% CI; verdict per comparison from the CI and the
             endpoint's better direction; one difference scale per endpoint type
  soa        schedule of assessments: visits (week labels, periods as contiguous runs) × assessment items grouped in
             sections; per-visit load, section × visit counts, the busiest visits (the full item table is the 7.x soa
             pattern, which now validates through soa_model)
"""
from .diagrams import kind
from .tree import TOK, INK, BODY, MUTED, RISK
from . import text as T
import json
import math
import re
from .diagram_kinds import R, Ln, Tx, S, SMALL, TINT, EDGE, Diamond, Dot
from . import diagram_clinical as DC   # attribute access at call time: diagram_clinical imports diagrams, which imports this module

PH = TOK['charts']['phases']; OK_INK = TOK['flagship']['tag']['ok'][1]

def W(s, size=S, bold=False): return T.width(T.plain(s), size, bold)
def n0(v): return f'{v:,}'

def _int(v): return isinstance(v, int) and not isinstance(v, bool)

# ---------------------------------------------------------------- exposure summary
def band_colors(n):
    """Cumulative duration bands are ordered: one hue light → deep (the phase ramp, skipping its pale first step)."""
    return [PH[min(len(PH) - 1, 1 + round(k * (len(PH) - 2) / max(1, n - 1)))] for k in range(n)]

def exposure_model(spec):
    """Validate the exposure contract and compute totals.
    spec: {unit?: '例', head?: '适应症 / 研究', bands: [{key, label}] (2–5, cumulative: each band a subset of the one before),
           groups: [{key, name, note?, values: [n per band], py?: patient-years}] (1–8), targets?: {band key: n}, focus?: group key}"""
    bands, groups = spec.get('bands') or [], spec.get('groups') or []
    if not 2 <= len(bands) <= 5: raise ValueError('暴露汇总需要 2–5 个暴露时长档 bands：[{key, label}]')
    bk = [b.get('key') for b in bands]
    if len(set(bk)) != len(bk): raise ValueError('bands 的 key 不能重复')
    if not 1 <= len(groups) <= 8: raise ValueError('暴露汇总需要 1–8 个组 groups（适应症或研究）')
    gk = [g.get('key') for g in groups]
    if len(set(gk)) != len(gk): raise ValueError('groups 的 key 不能重复')
    out = []
    for g in groups:
        v = g.get('values') or []
        if len(v) != len(bands) or not all(_int(x) and x >= 0 for x in v): raise ValueError(f'「{g["name"]}」的 values 须是每个时长档一个非负整数')
        if any(v[i + 1] > v[i] for i in range(len(v) - 1)): raise ValueError(f'「{g["name"]}」的暴露例数须随时长档递减或持平（长档是短档的子集）')
        py = g.get('py')
        if py is not None and (isinstance(py, bool) or not isinstance(py, (int, float)) or py < 0): raise ValueError(f'「{g["name"]}」的 py（人年）须是非负数')
        out.append(dict(g))
    tg = spec.get('targets') or {}
    for k, t in tg.items():
        if k not in bk: raise ValueError(f'targets 的「{k}」不是 bands 的 key')
        if not _int(t) or t <= 0: raise ValueError('targets 的值须是正整数')
    if spec.get('focus') is not None and spec['focus'] not in gk: raise ValueError(f'focus「{spec["focus"]}」不在 groups 里')
    totals = [sum(g['values'][i] for g in out) for i in range(len(bands))]
    py = sum(g['py'] for g in out) if all(g.get('py') is not None for g in out) else None
    targets = [tg.get(k) for k in bk]
    return {'bands': bands, 'groups': out, 'totals': totals, 'py': py, 'targets': targets,
            'met': [None if t is None else totals[i] >= t for i, t in enumerate(targets)],
            'focus': spec.get('focus'), 'unit': spec.get('unit', '例'), 'max': max(g['values'][0] for g in out) or 1}

def _exposure_measure(spec, w):
    n = len(spec.get('groups') or []); has_t = bool(spec.get('targets'))
    return 40 + n * 36 + 40 + (34 if has_t else 0)

@kind('exposure', measure=_exposure_measure)
def exposure(spec, box, gid, mode):
    """Exposure summary: one row per indication / study; a nested bar per row (the cumulative bands overlaid light → deep,
    each band a subset of the one before), the counts per band and patient-years in columns, the totals and the targets
    underneath (a total that reaches its target in green, one that falls short in red with the gap)."""
    m = exposure_model(spec); x, y, w, h = box; bands, groups = m['bands'], m['groups']; col = band_colors(len(bands))
    has_py = m['py'] is not None; has_t = any(t is not None for t in m['targets'])
    lab = min(w * .24, max(max(W(g['name'], S, True), W(g.get('note', ''), SMALL)) for g in groups) + 18)
    cws = [max(W(b['label'], SMALL, True) + 36, W(n0(max(m['totals'])), S, True) + 18) for b in bands]
    pyw = (max(W('人年', SMALL, True), W(f'{m["py"]:,.0f}', S, True)) + 22) if has_py else 0
    cols_w = sum(cws) + pyw; bx0 = x + lab; bx1 = x + w - cols_w - 16; bw = bx1 - bx0
    head = 40; foot = 40 + (34 if has_t else 0); n = len(groups)
    rh = max(30, min(64, (h - head - foot) / n)); y0 = y + head
    out = [Tx(x, y + 20, spec.get('head', '适应症 / 研究'), S, INK, True)]
    cx = x + w - cols_w
    for b, c, cw in zip(bands, col, cws):
        out.append(R(cx + cw - 8 - W(b['label'], SMALL, True) - 18, y + 14, 12, 12, c, None, 3))
        out.append(Tx(cx + cw - 8, y + 20, b['label'], SMALL, INK, True, 'end')); cx += cw
    if has_py: out.append(Tx(x + w - 8, y + 20, '人年', SMALL, INK, True, 'end'))
    out.append(Ln(x, y + head - 6, x + w, y + head - 6, '#D5DADF', 1))
    for k, g in enumerate(groups):
        ry = y0 + k * rh; cy = ry + rh / 2; foc = g['key'] == m['focus']
        if foc: out.append(R(x - 6, ry + 2, w + 12, rh - 4, TINT['brand'], EDGE['brand'], 8))
        elif k % 2 == 0: out.append(R(bx0, ry + 2, bw, rh - 4, '#F7F8F9', None, 4))
        if g.get('note') and rh >= 40:
            out.append(Tx(x, cy - 9, g['name'], S, INK, True, 'start', lab - 10)); out.append(Tx(x, cy + 10, g['note'], SMALL, MUTED, False, 'start', lab - 10))
        else: out.append(Tx(x, cy, g['name'], S, INK, True, 'start', lab - 10))
        bh = min(26, rh * .5)
        for i, (v, c) in enumerate(zip(g['values'], col)):
            if v: out.append(R(bx0, cy - bh / 2, max(1, v / m['max'] * bw), bh, c, None, 3))
        cx = x + w - cols_w
        for v, cw in zip(g['values'], cws):
            out.append(Tx(cx + cw - 8, cy, n0(v), S, INK if foc else BODY, foc, 'end')); cx += cw
        if has_py: out.append(Tx(x + w - 8, cy, f'{g["py"]:,.0f}', S, BODY, False, 'end'))
    ty = y0 + n * rh + 4
    out.append(Ln(x, ty, x + w, ty, '#5F6B76', 1.2))
    out.append(Tx(x, ty + 20, f'合计（{m["unit"]}）', S, INK, True))
    cx = x + w - cols_w
    for i, (v, cw) in enumerate(zip(m['totals'], cws)):
        met = m['met'][i]; c = INK if met is None else (OK_INK if met else RISK)
        out.append(Tx(cx + cw - 8, ty + 20, n0(v), S, c, True, 'end')); cx += cw
    if has_py: out.append(Tx(x + w - 8, ty + 20, f'{m["py"]:,.0f}', S, INK, True, 'end'))
    if has_t:
        out.append(Tx(x, ty + 54, spec.get('target_label', '目标'), S, MUTED, True))
        cx = x + w - cols_w; gaps = []
        for i, (t, cw) in enumerate(zip(m['targets'], cws)):
            if t is not None:
                out.append(Tx(cx + cw - 8, ty + 54, f'≥{n0(t)}', S, MUTED, False, 'end'))
                if not m['met'][i]: gaps.append(f'{bands[i]["label"]}差 {n0(t - m["totals"][i])}')
            cx += cw
        msg = '；'.join(gaps) if gaps else '各时长档均已达到目标'
        out.append(Tx(bx0, ty + 54, msg, SMALL, RISK if gaps else OK_INK, True, 'start', bw))
    return ''.join(out)

# ---------------------------------------------------------------- trial flow with subflows
FLOW_KINDS = ('titrate', 'maintain', 'placebo', 'open', 'off')

def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)

def _segs(segs, start, who):
    """Contiguous segments from `start`; returns the end week."""
    if not segs: raise ValueError(f'「{who}」需要至少一段 segs：[{{from, to, label, kind}}]')
    t = start
    for g in segs:
        lab = g.get('label') or who
        if not (_num(g.get('from')) and _num(g.get('to'))) or g['from'] >= g['to']: raise ValueError(f'「{lab}」的 from 须小于 to')
        if g['from'] != t: raise ValueError(f'「{lab}」须接上前一段（from = {t}）')
        if g.get('kind', 'maintain') not in FLOW_KINDS: raise ValueError(f'「{lab}」的 kind 须是 titrate / maintain / placebo / open / off')
        t = g['to']
    return t

def _ratio(r, n, who):
    if r is None: return None
    parts = str(r).split(':')
    if len(parts) != n or not all(re.fullmatch(r'\d+', x) and int(x) > 0 for x in parts): raise ValueError(f'{who}的 ratio「{r}」须是与组数相同的正整数比，如 2:1')
    return [int(x) for x in parts]

def _n(x):
    v = x.get('n')
    if v is not None and not (_int(v) and v >= 0): raise ValueError(f'「{x.get("name")}」的 n 须是非负整数')

def trialflow_model(spec):
    """Validate the trial-flow contract and lay out its rows.
    spec: {unit?: '周', trunk?: [{label, from, to, kind?}] (≤3, contiguous), split: {at, label?, ratio?: '2:1'},
           arms: [{key, name, n?, segs: [{from, to, label, kind?}], split?: {at, label?, ratio?, arms: [sub-arm, 2–3]}}] (2–5),
           after?: [{label, from, to, kind?}] (≤2), endpoints?: [{at, label, primary?}], subs?: [{key, name, of: [arm keys], from, to, n?}] (≤3),
           events?: [{at, label, kind: interim|dmc|unblind|lock|eot|rescue|other}] (≤6),
           bands?: [{label, from, to, kind: drug|background|rescue|washout|other, text?, of?: [arm keys]}] (≤4), focus?: arm key}.
    kind ∈ titrate / maintain / placebo / open / off (arm segments default maintain; trunk and after default off — screening,
    run-in without drug and follow-up are not treatment). Every leaf ends at the same week."""
    trunk, split, arms = spec.get('trunk') or [], spec.get('split') or {}, spec.get('arms') or []
    if len(trunk) > 3: raise ValueError('共同阶段 trunk 最多 3 段（筛选、导入…）')
    if not _num(split.get('at')): raise ValueError('试验流程需要 split：{at, label?, ratio?}（随机化所在周）')
    if trunk and _segs(trunk, trunk[0].get('from'), '共同阶段') != split['at']: raise ValueError('split.at 须等于共同阶段 trunk 的结束周')
    if not 2 <= len(arms) <= 5: raise ValueError('试验流程需要 2–5 个组 arms')
    ratio = _ratio(split.get('ratio'), len(arms), '随机化')
    keys, leaves, ends, out = [], [], [], []
    for a in arms:
        keys.append(a.get('key')); _n(a)
        e = _segs(a.get('segs'), split['at'], a.get('name')); sp = a.get('split'); r0 = len(leaves); sub = None
        if sp:
            kids = sp.get('arms') or []
            if sp.get('at') != e: raise ValueError(f'「{a.get("name")}」的 split.at 须等于该组最后一段的结束周')
            if not 2 <= len(kids) <= 3: raise ValueError(f'「{a.get("name")}」的子分组需要 2–3 个')
            sub = {'at': e, 'label': sp.get('label', '再随机化'), 'ratio': _ratio(sp.get('ratio'), len(kids), f'「{a.get("name")}」再随机化')}
            for b in kids:
                keys.append(b.get('key')); _n(b)
                if b.get('split'): raise ValueError('子分组不能再分（最多两层）')
                ends.append(_segs(b.get('segs'), e, b.get('name')))
                leaves.append({**b, 'parent': a.get('key'), 'row': len(leaves), 'path': list(a['segs']) + list(b['segs'])})
            if a.get('n') is not None and all(b.get('n') is not None for b in kids) and sum(b['n'] for b in kids) > a['n']:
                raise ValueError(f'「{a.get("name")}」的子分组例数之和不能超过该组 n')
        else:
            ends.append(e); leaves.append({**a, 'parent': None, 'row': len(leaves), 'path': list(a['segs'])})
        out.append({**a, 'rows': list(range(r0, len(leaves))), 'sub': sub})
    if len(set(keys)) != len(keys): raise ValueError('arms 的 key 不能重复（含子分组）')
    if len(set(ends)) != 1: raise ValueError('各分组的治疗期须在同一周结束')
    end = ends[0]; after = spec.get('after') or []
    if len(after) > 2: raise ValueError('结束后阶段 after 最多 2 段（随访…）')
    final = _segs(after, end, '结束后阶段') if after else end
    start = trunk[0]['from'] if trunk else split['at']
    for p in spec.get('endpoints') or []:
        if not _num(p.get('at')) or not start <= p['at'] <= final: raise ValueError(f'终点「{p.get("label")}」的 at 不在试验时间范围内')
    subs = spec.get('subs') or []
    if len(subs) > 3: raise ValueError('子研究 subs 最多 3 个')
    for x in subs:
        if not x.get('of'): raise ValueError(f'子研究「{x.get("name")}」需要 of（所在分组）')
        for k in x['of']:
            if k not in keys: raise ValueError(f'子研究「{x.get("name")}」的 of 含未知分组「{k}」')
        if not (_num(x.get('from')) and _num(x.get('to'))) or x['from'] >= x['to'] or x['from'] < start or x['to'] > final:
            raise ValueError(f'子研究「{x.get("name")}」的 from–to 须在试验时间范围内且 from < to')
        _n(x)
    if spec.get('focus') is not None and spec['focus'] not in keys: raise ValueError(f'focus「{spec["focus"]}」不是分组 key')
    events = []
    for e in spec.get('events') or []:
        if not isinstance(e.get('label'), str) or not e['label'].strip(): raise ValueError('关键事件 events 须有 label')
        if not _num(e.get('at')) or not start <= e['at'] <= final: raise ValueError(f'事件「{e["label"]}」的 at 不在试验时间范围内')
        if e.get('kind') not in TF_EVENTS: raise ValueError(f'事件「{e["label"]}」的 kind 须是 {"、".join(TF_EVENTS)} 之一')
        events.append({'at': e['at'], 'label': e['label'], 'kind': e['kind']})
    if len(events) > 6: raise ValueError('关键事件 events 最多 6 个')
    bands = []
    for b in spec.get('bands') or []:
        lab = b.get('label')
        if not isinstance(lab, str) or not lab.strip(): raise ValueError('给药 / 治疗时段 bands 须有 label')
        if b.get('kind') not in TF_BANDS: raise ValueError(f'时段「{lab}」的 kind 须是 {"、".join(TF_BANDS)} 之一')
        if not (_num(b.get('from')) and _num(b.get('to'))) or b['from'] >= b['to'] or b['from'] < start or b['to'] > final:
            raise ValueError(f'时段「{lab}」的 from–to 须在试验时间范围内且 from < to')
        for k in b.get('of') or []:
            if k not in keys: raise ValueError(f'时段「{lab}」的 of 含未知分组「{k}」')
        bands.append({'label': lab, 'kind': b['kind'], 'text': b.get('text') or '', 'from': b['from'], 'to': b['to'], 'of': list(b.get('of') or [])})
    if len(bands) > 4: raise ValueError('给药 / 治疗时段 bands 最多 4 条')
    segs = trunk + after + [g for a in arms for g in a['segs']] + [g for l in leaves if l['parent'] for g in l['segs']]
    ticks = sorted({v for g in segs for v in (g['from'], g['to'])})
    n = sum(a['n'] for a in arms) if all(a.get('n') is not None for a in arms) else None
    # shared periods before randomisation and after treatment are not treatment unless the source says so: kind defaults to off
    trunk = [{**g, 'kind': g.get('kind', 'off')} for g in trunk]; after = [{**g, 'kind': g.get('kind', 'off')} for g in after]
    return {'start': start, 'at': split['at'], 'end': end, 'final': final, 'trunk': trunk, 'after': after, 'split': split, 'ratio': ratio,
            'arms': out, 'leaves': leaves, 'endpoints': spec.get('endpoints') or [], 'subs': subs, 'focus': spec.get('focus'),
            'unit': spec.get('unit', '周'), 'n': n, 'ticks': ticks, 'events': events, 'bands': bands}

# key events on the week axis besides the splits and the endpoints, and the treatment periods under the arms (round 9)
TF_EVENTS = ('interim', 'dmc', 'unblind', 'lock', 'eot', 'rescue', 'other')
TF_BANDS = ('drug', 'background', 'rescue', 'washout', 'other')

FLOW = TOK['charts']['flow']; ACCENT = TOK['flagship']['accent_ink']; CAT_TREAT = TOK['charts']['categorical'][0]

def wk(v, unit='周'):
    """Week label: W−3, W0, W36 (the axis and the endpoint labels)."""
    return f'W{"−" if v < 0 else ""}{abs(v):g}'

def flow_scale(m, x0, x1, minw):
    """Piecewise-linear time scale over every boundary (segments, endpoints, sub-studies): an interval never gets less
    than `minw` px, so a 2-week screening period stays readable next to a 52-week treatment period."""
    pts = sorted(set(m['ticks']) | {p['at'] for p in m['endpoints']} | {v for x in m['subs'] for v in (x['from'], x['to'])}
                 | {e['at'] for e in m.get('events', [])} | {v for b in m.get('bands', []) for v in (b['from'], b['to'])})
    span = x1 - x0; d = [b - a for a, b in zip(pts, pts[1:])]; fixed = set()
    for _ in range(len(d)):
        free = sum(v for i, v in enumerate(d) if i not in fixed); room = span - minw * len(fixed)
        k = room / free if free else 0; small = [i for i, v in enumerate(d) if i not in fixed and v * k < minw]
        if not small: break
        fixed |= set(small)
    ws = [minw if i in fixed else v * k for i, v in enumerate(d)]; xs = [x0]
    for w in ws: xs.append(xs[-1] + w)
    def X(t):
        for i in range(len(d)):
            if t <= pts[i + 1] or i == len(d) - 1: return xs[i] + (t - pts[i]) / d[i] * ws[i]
    return X

def _flow_measure(spec, w):
    n = sum(len((a.get('split') or {}).get('arms') or [0]) for a in spec.get('arms') or [])
    return 84 + n * 52 + len(spec.get('subs') or []) * 40 + len(spec.get('bands') or []) * 32 + 10

# treatment-period strips (trial flow and SoA): fill, ink, dashed outline
BAND_STYLE = {'drug': ('#FBD9A8', '#5C3A00', False), 'background': ('#E6E9ED', '#3D4651', False), 'rescue': ('#FFFFFF', ACCENT, True),
              'washout': ('#F1F3F5', '#6B7480', True), 'other': ('#F1F3F5', '#3D4651', False)}

@kind('trialflow', measure=_flow_measure)
def trialflow(spec, box, gid, mode):
    """Trial flow with subflows: endpoints, key events and week ticks on the axis; shared periods on one bar at the centre of all
    rows; a randomisation node with a spine fanning out to the arms; an arm re-randomised into sub-arms gets its own node;
    every leaf runs to the same end, where a merge spine leads into the shared follow-up; sub-studies are dashed bars
    underneath, then one strip per treatment period (study drug, background, rescue). Arms in the label column (sub-arms
    in a second column behind a bracket), n under each name."""
    m = trialflow_model(spec); x, y, w, h = box; leaves, arms = m['leaves'], m['arms']; nested = any(a['sub'] for a in arms)
    name_w = lambda xs: max([W(v['name'], S, True) for v in xs] + [W(f'n={v["n"]}', SMALL) for v in xs if v.get('n') is not None] + [0])
    ca = min(w * .16, name_w(arms) + 16); cb = min(w * .14, name_w([l for l in leaves if l['parent']]) + 24) if nested else 0
    x0 = x + ca + cb + 16; x1 = x + w - 8; X = flow_scale(m, x0, x1, 84)
    ax = y + 50; ry0 = y + 84; ns = len(m['subs']); nb = len(m['bands']); rh = max(40, min(64, (h - 84 - ns * 40 - nb * 32 - 10) / len(leaves))); bh = min(28, rh * .56)
    cy = lambda r: ry0 + r * rh + rh / 2; mid = (cy(0) + cy(len(leaves) - 1)) / 2
    out = []
    focus = next((a for a in arms if a['key'] == m['focus']), None)
    if focus: out.append(R(x - 6, ry0 + focus['rows'][0] * rh + 2, w + 12, len(focus['rows']) * rh - 4, TINT['brand'], None, 8))
    # axis: ticks, endpoints (diamond + label above, light guide through the rows)
    out.append(Ln(x0, ax, x1, ax, TOK['charts']['axis'], 1.2))
    for t in m['ticks']:
        out.append(Ln(X(t), ax - 4, X(t), ax + 4, TOK['charts']['axis'], 1.2)); out.append(Tx(X(t), ax + 16, wk(t), SMALL, MUTED, False, 'middle'))
    for p in m['endpoints']:
        c = ACCENT if p.get('primary') else MUTED; px = X(p['at'])
        out.append(Ln(px, ax + 26, px, ry0 + len(leaves) * rh, TOK['charts']['grid'], 1.2, True))
        out.append(Diamond(px, ax, 7 if p.get('primary') else 6, c)); out.append(Tx(px, ax - 22, p['label'], SMALL, c, True, 'middle'))
    # key events (round 9): a ringed dot on the axis, the label above it — one line higher when an endpoint label is near
    taken = [(X(p['at']), W(p['label'], SMALL, True)) for p in m['endpoints']]
    for e in m['events']:
        ex_ = X(e['at']); lw = W(e['label'], SMALL); hi = any(abs(ex_ - tx) < (lw + tw_) / 2 + 8 for tx, tw_ in taken)
        out.append(Ln(ex_, ax + 26, ex_, ry0 + len(leaves) * rh, TOK['charts']['grid'], 1, True))
        out.append(Dot(ex_, ax, 5, '#FFFFFF', '#6B7480')); out.append(Tx(min(ex_, x1 - lw / 2), ax - (40 if hi else 22), e['label'], SMALL, BODY, False, 'middle'))
        if e['at'] not in m['ticks']: out.append(Tx(ex_, ax + 16, wk(e['at']), SMALL, MUTED, False, 'middle'))
        taken.append((ex_, lw))
    def bar(g, yc, x_a, x_b, hh=None):
        k = g.get('kind', 'maintain'); col = FLOW[k]; off = k == 'off'; hh = hh or bh
        o = [R(x_a + 1, yc - hh / 2, x_b - x_a - 2, hh, col, FLOW['off_edge'] if off else None, min(hh, bh) / 2 if off else 5, off)]
        lab = g.get('label', ''); fits = W(lab, SMALL, True) + 14 < x_b - x_a
        if fits: o.append(Tx((x_a + x_b) / 2, yc, lab, SMALL, INK if off else DC.on_color(col), True, 'middle'))
        else: o.append(Tx((x_a + x_b) / 2, yc + bh / 2 + 12, lab, SMALL, MUTED, False, 'middle'))
        return o
    # shared periods are tall blocks over every row: they read as common to all arms, not as part of the middle row
    tall = cy(len(leaves) - 1) - cy(0) + bh
    for g in m['trunk'] + m['after']: out += bar(g, mid, X(g['from']), X(g['to']), tall)
    acy = {a['key']: (cy(a['rows'][0]) + cy(a['rows'][-1])) / 2 for a in arms}
    def node(nx, ny, ys, label):
        o = [Ln(nx, min(ys), nx, max(ys), '#8A949E', 1.6)] + [Ln(nx, yy, nx + 6, yy, '#8A949E', 1.6) for yy in ys]
        o += [Dot(nx, ny, 12, '#FFFFFF', ACCENT), Tx(nx, ny, 'R', SMALL, ACCENT, True, 'middle')]
        # label above the top end of the spine, right of it: left of a node sits a shared block or the parent bar
        o.append(Tx(nx + 10, min(ys) - bh / 2 - 11, label, SMALL, INK, True, 'start'))
        return o
    # randomisation nodes go on top of the arm bars (drawn after them): a bar starting at the node would hide its R
    sp = m['split']; late = node(X(m['at']), mid, list(acy.values()), sp.get('label', '随机化') + (f' {sp["ratio"]}' if sp.get('ratio') else ''))
    for a in arms:
        yc = acy[a['key']]; fo = a['key'] == m['focus']
        for g in a['segs']: out += bar(g, yc, X(g['from']), X(g['to']))
        nm = [Tx(x, yc - (9 if a.get('n') is not None else 0), a['name'], S, INK, True, 'start', ca - 8)]
        if a.get('n') is not None: nm.append(Tx(x, yc + 11, f'n={a["n"]}', SMALL, MUTED))
        out += nm
        if a['sub']:
            ys = [cy(r) for r in a['rows']]; sub = a['sub']; kids = [l for l in leaves if l['parent'] == a['key']]
            raw = next(x_ for x_ in spec['arms'] if x_.get('key') == a['key'])['split']
            late += node(X(sub['at']), yc, ys, sub['label'] + (f' {raw["ratio"]}' if raw.get('ratio') else ''))
            bx = x + ca + 2; out.append(Ln(bx, ys[0] - bh / 2, bx, ys[-1] + bh / 2, EDGE['brand' if fo else 'muted'], 2))
            for l, yy in zip(kids, ys):
                for g in l['segs']: out += bar(g, yy, X(g['from']), X(g['to']))
                out.append(Tx(bx + 10, yy - (9 if l.get('n') is not None else 0), l['name'], S, INK, False, 'start', cb - 12))
                if l.get('n') is not None: out.append(Tx(bx + 10, yy + 11, f'n={l["n"]}', SMALL, MUTED))
    out += late
    ex = X(m['end'])
    if m['after']: out += [Ln(ex, cy(0), ex, cy(len(leaves) - 1), '#8A949E', 1.6)]
    sy = ry0 + len(leaves) * rh + 8
    names = {a['key']: a['name'] for a in arms} | {l['key']: l['name'] for l in leaves}
    for k, sb in enumerate(m['subs']):
        yy = sy + k * 40 + 16; xa, xb = X(sb['from']), X(sb['to'])
        out.append(R(xa + 1, yy - 13, xb - xa - 2, 26, '#FFFFFF', ACCENT, 13, True, 1.4))
        lab = sb['name'] + (f' n={sb["n"]}' if sb.get('n') is not None else '') + ' · ' + '、'.join(names[q] for q in sb['of'])
        out.append(Tx(xa + 14, yy, lab, SMALL, INK, True, 'start', xb - xa - 24))
    if ns: out.append(Tx(x, sy + 16, '子研究', S, MUTED, True, 'start', ca + cb))
    # treatment periods (study drug, background, rescue…): one strip each under the arms, named in the label column
    by_ = sy + ns * 40
    for k, bd in enumerate(m['bands']):
        yy = by_ + k * 32 + 16; xa, xb = X(bd['from']), X(bd['to']); fill, ink, dash = BAND_STYLE[bd['kind']]
        out.append(R(xa + 1, yy - 10, xb - xa - 2, 20, fill, ink if dash else None, 10, dash, 1.2))
        lab = bd['text'] or bd['label']
        if bd['of']: lab += ' · ' + '、'.join(names[q] for q in bd['of'])
        out.append(Tx(xa + 12, yy, lab, SMALL, ink, False, 'start', xb - xa - 20))
        out.append(Tx(x, yy, bd['label'], S, INK, True, 'start', ca + cb))
    return ''.join(out)

# ---------------------------------------------------------------- competitive landscape
LS_STAGES = ['临床前', 'I 期', 'II 期', 'III 期', '申报', '上市']
LS_METRICS = ('efficacy', 'safety')

def landscape_model(spec, cap=10):
    """Validate the competitive-landscape contract, order the assets and rank them per metric.
    spec: {stages?: [names] (2–7, default 临床前…上市), efficacy?: {label, unit?, better: higher|lower, note?},
           safety?: {label, unit?, better: higher|lower}, assets: [{key, name, company?, moa?, route?, stage, efficacy?, safety?,
           ours?}] (2–10, at most one ours), focus?: asset key}. A metric value is a number or null (no data — drawn as —)."""
    stages = spec.get('stages') or LS_STAGES; assets = spec.get('assets') or []
    if not 2 <= len(stages) <= 7: raise ValueError('竞争格局需要 2–7 个研发阶段 stages')
    if len(set(stages)) != len(stages): raise ValueError('stages 不能重复')
    if not 2 <= len(assets) <= cap: raise ValueError(f'竞争格局需要 2–{cap} 个药物 assets' + ('（更多时分页：landscape-pipeline / -efficacy / -safety）' if cap == 10 else ''))
    keys = [a.get('key') for a in assets]
    if len(set(keys)) != len(keys): raise ValueError('assets 的 key 不能重复')
    if sum(1 for a in assets if a.get('ours')) > 1: raise ValueError('ours 最多标一个（本公司药物）')
    metrics = {}
    for mk in LS_METRICS:
        mt = spec.get(mk)
        if mt is None: continue
        if not mt.get('label'): raise ValueError(f'{mk} 需要 label（指标名）')
        if mt.get('better') not in ('higher', 'lower'): raise ValueError(f'{mk}.better 须是 higher 或 lower')
        metrics[mk] = mt
    out = []
    for i, a in enumerate(assets):
        if a.get('stage') not in stages: raise ValueError(f'「{a.get("name")}」的 stage 须是 stages 之一')
        for mk in LS_METRICS:
            v = a.get(mk)
            if v is None: continue
            if mk not in metrics: raise ValueError(f'「{a.get("name")}」写了 {mk}，但没有定义 {mk} 指标')
            if not _num(v): raise ValueError(f'「{a.get("name")}」的 {mk} 须是数字或 null（无数据）')
        out.append({**a, 'idx': i, 'si': stages.index(a['stage'])})
    if spec.get('focus') is not None and spec['focus'] not in keys: raise ValueError(f'focus「{spec["focus"]}」不在 assets 里')
    def mkey(a, mk):
        v = a.get(mk); hi = metrics.get(mk, {}).get('better') == 'higher'
        return 1e9 if v is None else (-v if hi else v)
    order = [a['key'] for a in sorted(out, key=lambda a: (-a['si'], mkey(a, 'efficacy'), a['idx']))]
    rank = {mk: [a['key'] for a in sorted([a for a in out if a.get(mk) is not None], key=lambda a: (mkey(a, mk), a['idx']))] for mk in metrics}
    best = {mk: (r[0] if r else None) for mk, r in rank.items()}
    mx = {mk: max([abs(a[mk]) for a in out if a.get(mk) is not None] + [0]) or 1 for mk in metrics}
    ours = next((a['key'] for a in out if a.get('ours')), None)
    return {'stages': stages, 'assets': out, 'order': order, 'rank': rank, 'best': best, 'max': mx, 'metrics': metrics,
            'ours': ours, 'focus': spec.get('focus', ours)}


def stage_colors(n):
    """Development stages read along the phase ramp (pale first step skipped when there are fewer stages than steps)."""
    return [PH[min(len(PH) - 1, round(k * (len(PH) - 1) / max(1, n - 1)))] for k in range(n)]

def _ls_measure(spec, w):
    return 52 + len(spec.get('assets') or []) * 40 + 8

@kind('landscape', measure=_ls_measure)
def landscape(spec, box, gid, mode):
    """Competitive landscape table: one row per asset (ours tinted), the development stage as a track of stage cells filled
    up to the current one (phase ramp), then one bar column per metric on its own scale with the value (the best per
    metric in bold accent; null drawn as — , never as 0); the header names each metric with its better direction."""
    m = landscape_model(spec); x, y, w, h = box; st = m['stages']; A = {a['key']: a for a in m['assets']}; mets = list(m['metrics'])
    nw = min(w * .3, max(max(W(a['name'], S, True), W(' · '.join(v for v in (a.get('company'), a.get('moa'), a.get('route')) if v), SMALL)) for a in A.values()) * T.HEADROOM + 16)
    sw = min(w * .3, max(W(t, SMALL, True) for t in st) * len(st) + 8 * len(st)); mw = (w - nw - sw - 24 * len(mets)) / max(1, len(mets))
    head = 52; rh = max(36, min(56, (h - head - 8) / len(A))); out = []; sc = stage_colors(len(st))
    sx = x + nw; cwid = sw / len(st)
    out.append(Tx(x, y + 18, '药物 · 公司 · 机制', SMALL, MUTED, True))
    out.append(Tx(sx, y + 18, '研发阶段', SMALL, MUTED, True))
    for k, t in enumerate(st): out.append(Tx(sx + k * cwid + cwid / 2, y + 38, t, SMALL, INK, True, 'middle', cwid))
    mx0 = [sx + sw + 24 + j * (mw + 24) for j in range(len(mets))]
    for j, mk in enumerate(mets):
        mt = m['metrics'][mk]; arrow = '越高越好' if mt['better'] == 'higher' else '越低越好'
        out.append(Tx(mx0[j], y + 18, f'{mt["label"]}' + (f'（{mt["unit"]}）' if mt.get('unit') else ''), SMALL, INK, True, 'start', mw))
        out.append(Tx(mx0[j], y + 38, arrow + (f' · {mt["note"]}' if mt.get('note') else ''), SMALL, MUTED, False, 'start', mw))
    out.append(Ln(x, y + head - 2, x + w, y + head - 2, '#D5DADF', 1))
    for r, key in enumerate(m['order']):
        a = A[key]; ry = y + head + r * rh; cy = ry + rh / 2; ours = a.get('ours'); fo = key == m['focus']
        if ours or fo: out.append(R(x - 6, ry + 2, w + 12, rh - 4, TINT['brand'], EDGE['brand'] if fo else None, 8))
        elif r % 2: out.append(R(x - 6, ry + 2, w + 12, rh - 4, '#F7F8F9', None, 6))
        sub = ' · '.join(v for v in (a.get('company'), a.get('moa'), a.get('route')) if v)
        if sub and rh >= 40:
            out.append(Tx(x, cy - 9, a['name'], S, INK, True, 'start', nw - 10)); out.append(Tx(x, cy + 10, sub, SMALL, MUTED, False, 'start', nw - 10))
        else: out.append(Tx(x, cy, a['name'], S, INK, True, 'start', nw - 10))
        for k in range(len(st)):
            on = k <= a['si']; cx0 = sx + k * cwid + 2
            out.append(R(cx0, cy - 7, cwid - 4, 14, sc[k] if on else '#EEF0F2', None, 7))
        for j, mk in enumerate(mets):
            v = a.get(mk); bx = mx0[j]; vw = W('00.0', S, True) + 10; bw = mw - vw
            if v is None: out.append(Tx(bx, cy, '—  暂无数据', SMALL, MUTED, False)); continue
            col = CAT_TREAT if ours else TOK['charts']['comparator']; best = m['best'][mk] == key
            out.append(R(bx, cy - 8, max(2, abs(v) / m['max'][mk] * bw), 16, col, None, 4))
            out.append(Tx(bx + abs(v) / m['max'][mk] * bw + 8, cy, f'{v:g}', S, ACCENT if best else (INK if ours else BODY), best or ours, 'start'))
    return ''.join(out)

# ---------------------------------------------------------------- competitive landscape, many assets (round 9)
# ≤ 4 assets: the landscape page with insight cards; 5–8: the same page without cards (points in the notes); > 8: three
# pages from one contract — pipeline (mechanism × stage board), efficacy (ranked, with the trial behind each number) and
# safety (a matrix of safety measures). The contract is the landscape one with up to 30 assets, plus per asset
# trial: {name?, weeks?, n?} and detail: {key: number | null}, and safety_detail: [{key, label, unit?, better}] (1–6).
LS_MANY = 30

def landscape_many(spec):
    """Validate the many-assets landscape contract (see above) → the landscape model plus classes (mechanisms in
    stage order, or spec.classes), per-asset trial text, the safety-detail metrics with per-column ranks."""
    m = landscape_model(spec, cap=LS_MANY)
    det = spec.get('safety_detail') or []
    if len(det) > 6: raise ValueError('safety_detail 最多 6 个安全性指标')
    dk = [d.get('key') for d in det]
    if len(set(dk)) != len(dk) or not all(dk): raise ValueError('safety_detail 每项需要不重复的 key')
    for d in det:
        if not d.get('label'): raise ValueError(f'safety_detail「{d.get("key")}」需要 label')
        if d.get('better') not in ('higher', 'lower'): raise ValueError(f'safety_detail「{d["key"]}」的 better 须是 higher 或 lower')
    for a in m['assets']:
        for k, v in (a.get('detail') or {}).items():
            if k not in dk: raise ValueError(f'「{a["name"]}」的 detail 写了 {k}，但 safety_detail 里没有')
            if v is not None and not _num(v): raise ValueError(f'「{a["name"]}」的 detail.{k} 须是数字或 null')
        t = a.get('trial') or {}
        if t and not isinstance(t, dict): raise ValueError(f'「{a["name"]}」的 trial 须是 {{name?, weeks?, n?}}')
        a['trial_text'] = ' · '.join(x for x in (t.get('name'), f'{t["weeks"]} 周' if t.get('weeks') else None, f'n={t["n"]:,}' if isinstance(t.get('n'), int) else None) if x)
    drank = {}
    for d in det:
        have = [a for a in m['assets'] if (a.get('detail') or {}).get(d['key']) is not None]
        sgn = -1 if d['better'] == 'higher' else 1
        drank[d['key']] = [a['key'] for a in sorted(have, key=lambda a: (sgn * a['detail'][d['key']], a['idx']))]
    seen = []
    for a in sorted(m['assets'], key=lambda a: (-a['si'], a['idx'])):
        c = a.get('moa') or '其他'
        if c not in seen: seen.append(c)
    classes = spec.get('classes') or seen
    if set(classes) != set(seen): raise ValueError('classes 须恰好列出 assets 里出现的全部机制（moa）')
    return {**m, 'classes': classes, 'detail': det, 'detail_rank': drank}

def _col_dec(vals):
    """Decimals shared by a column: the most any value carries (≤ 2), so 6 and 6.2 print as 6.0 and 6.2."""
    return min(2, max([len(f'{v:g}'.split('.')[1]) if '.' in f'{v:g}' else 0 for v in vals if v is not None] + [0]))

def _chip_w(a): return W(a['name'], SMALL, True) + (W(a['company'], SMALL) + 8 if a.get('company') else 0) + 20

def _lp_layout(m, w):
    """Rows (mechanisms) × stage columns: each cell a wrap of chips; → (label width, column width, per class the lines per cell)."""
    lab = min(w * .22, max(W(c, S, True) for c in m['classes']) + 20); cw = (w - lab) / len(m['stages'])
    A = m['assets']; rows = []
    for c in m['classes']:
        cells = []
        for k in range(len(m['stages'])):
            chips = [a for a in A if (a.get('moa') or '其他') == c and a['si'] == k]; lines, x = (1 if chips else 0), 0
            for a in chips:
                cwid = min(_chip_w(a), cw - 8)
                if x and x + cwid > cw - 8: lines += 1; x = 0
                x += cwid + 6
            cells.append((chips, lines))
        rows.append((c, cells, max([l for _, l in cells] + [1])))
    return lab, cw, rows

def _lp_measure(spec, w):
    m = landscape_many(spec); _, _, rows = _lp_layout(m, w)
    return 40 + sum(12 + n * 30 for _, _, n in rows) + 4

@kind('landscape-pipeline', measure=_lp_measure)
def landscape_pipeline(spec, box, gid, mode):
    """Pipeline board for many assets: mechanisms as rows (in stage order, or spec.classes), development stages as
    columns (the phase ramp in the header), one chip per asset in its cell — name bold, company muted; ours brand-filled,
    the focus ringed; marketed column tinted. Every asset of the contract appears exactly once."""
    m = landscape_many(spec); x, y, w, h = box; lab, cw, rows = _lp_layout(m, w); st = m['stages']; sc = stage_colors(len(st)); out = []
    out.append(Tx(x, y + 16, '机制', SMALL, MUTED, True))
    for k, t in enumerate(st):
        cx = x + lab + k * cw
        out.append(R(cx + 2, y + 4, cw - 4, 24, sc[k], None, 12)); out.append(Tx(cx + cw / 2, y + 16, t, SMALL, INK, True, 'middle', cw - 8))
    yy = y + 40; need = sum(12 + n * 30 for _, _, n in rows); grow = max(1, min(1.6, (h - 44) / need))   # rows share the spare height
    for r, (c, cells, n) in enumerate(rows):
        rh = (12 + n * 30) * grow
        if r % 2: out.append(R(x - 6, yy, w + 12, rh, '#F7F8F9', None, 8))
        out.append(Tx(x, yy + rh / 2, c, S, INK, True, 'start', lab - 12))
        for k, (chips, _) in enumerate(cells):
            cx = x + lab + k * cw + 4; px, py = cx, yy + (rh - n * 30 + 6) / 2
            for a in chips:
                cwid = min(_chip_w(a), cw - 8)
                if px > cx and px + cwid > cx + cw - 8: px, py = cx, py + 30
                ours, fo = a.get('ours'), a['key'] == m['focus']
                out.append(R(px, py, cwid, 24, CAT_TREAT if ours else '#FFFFFF', EDGE['brand'] if fo else '#D5DADF', 12))
                out.append(Tx(px + 10, py + 12, a['name'], SMALL, '#FFFFFF' if ours else INK, True, 'start', cwid - 14))
                if a.get('company') and cwid >= _chip_w(a) - 1:
                    out.append(Tx(px + 14 + W(a['name'], SMALL, True), py + 12, a['company'], SMALL, '#FFFFFF' if ours else MUTED, False, 'start'))
                px += cwid + 6
        yy += rh
    out.append(Ln(x, y + 34, x + w, y + 34, '#D5DADF', 1))
    return ''.join(out)

def _le_rows(m): return [m_ for m_ in m['rank'].get('efficacy', [])]

def _le_measure(spec, w):
    m = landscape_many(spec); return 52 + len(_le_rows(m)) * 32 + 8

@kind('landscape-efficacy', measure=_le_measure)
def landscape_efficacy(spec, box, gid, mode):
    """Efficacy across many assets: assets with data ranked best first, one row each — name and company, stage pill,
    the trial behind the number (study · weeks · n), and the value as a bar on one scale with the label (ours in the
    treat hue, the best in accent); assets without data are named under the chart, never drawn as 0."""
    m = landscape_many(spec); x, y, w, h = box; A = {a['key']: a for a in m['assets']}; mt = m['metrics'].get('efficacy')
    if not mt: raise ValueError('竞争格局有效性页需要 efficacy 指标')
    keys = _le_rows(m); st = m['stages']; sc = stage_colors(len(st)); out = []
    nw = min(w * .26, max(W(A[k]['name'], S, True) + (W(A[k].get('company') or '', SMALL) + 12) for k in keys) + 16)
    pw = max(W(t, SMALL, True) for t in st) + 20; TH = '研究 · 时长 · 例数'; trials = any(A[k]['trial_text'] for k in keys)
    # the trial column only when the source names the trials, and never narrower than its own header
    tw_ = min(w * .3, max([W(A[k]['trial_text'], SMALL) for k in keys] + [W(TH, SMALL, True)]) + 20) if trials else 0
    bx = x + nw + pw + tw_ + 12; bw = x + w - bx - 70; rh = max(26, min(36, (h - 52 - 8 - (24 if len(keys) < len(A) else 0)) / max(1, len(keys))))
    out.append(Tx(x, y + 18, '药物 · 公司', SMALL, MUTED, True)); out.append(Tx(x + nw, y + 18, '阶段', SMALL, MUTED, True))
    if trials: out.append(Tx(x + nw + pw, y + 18, TH, SMALL, MUTED, True))
    out.append(Tx(bx, y + 18, mt['label'] + (f'（{mt["unit"]}）' if mt.get('unit') else ''), SMALL, INK, True))
    out.append(Tx(bx, y + 38, ('越高越好' if mt['better'] == 'higher' else '越低越好') + (f' · {mt["note"]}' if mt.get('note') else ''), SMALL, MUTED, False, 'start', bw + 60))
    out.append(Ln(x, y + 50, x + w, y + 50, '#D5DADF', 1))
    for r, k in enumerate(keys):
        a = A[k]; cy = y + 52 + r * rh + rh / 2; ours, fo = a.get('ours'), k == m['focus']
        if ours or fo: out.append(R(x - 6, cy - rh / 2 + 1, w + 12, rh - 2, TINT['brand'], EDGE['brand'] if fo else None, 8))
        elif r % 2: out.append(R(x - 6, cy - rh / 2 + 1, w + 12, rh - 2, '#F7F8F9', None, 6))
        out.append(Tx(x, cy, a['name'], S, INK, True, 'start'))
        if a.get('company'): out.append(Tx(x + W(a['name'], S, True) + 8, cy, a['company'], SMALL, MUTED, False, 'start'))
        out.append(R(x + nw, cy - 10, pw - 10, 20, sc[a['si']], None, 10)); out.append(Tx(x + nw + (pw - 10) / 2, cy, a['stage'], SMALL, INK, True, 'middle'))
        if a['trial_text']: out.append(Tx(x + nw + pw, cy, a['trial_text'], SMALL, BODY, False, 'start', tw_ - 10))
        v = a['efficacy']; best = m['best']['efficacy'] == k; L = abs(v) / m['max']['efficacy'] * bw; dp = _col_dec([A[q]['efficacy'] for q in keys])
        out.append(R(bx, cy - 7, max(2, L), 14, CAT_TREAT if ours else TOK['charts']['comparator'], None, 4))
        out.append(Tx(bx + L + 8, cy, f'{v:.{dp}f}', S, ACCENT if best else (INK if ours else BODY), best or ours, 'start'))
    miss = [a['name'] for a in m['assets'] if a.get('efficacy') is None]
    if miss: out.append(Tx(x, y + 52 + len(keys) * rh + 14, '暂无公开数据：' + '、'.join(miss), SMALL, MUTED, False, 'start', w))
    return ''.join(out)

def _lsf_measure(spec, w):
    m = landscape_many(spec); return 60 + len(m["assets"]) * 27 + 6

@kind('landscape-safety', measure=_lsf_measure)
def landscape_safety(spec, box, gid, mode):
    """Safety across many assets: a matrix — one row per asset (stage order), one column per safety measure
    (safety_detail, else the landscape safety metric); each cell the value on a light-to-deep shade of its column
    (deeper = worse, by the column's better direction), the best per column in bold accent, — for no data; ours tinted."""
    m = landscape_many(spec); x, y, w, h = box; A = {a['key']: a for a in m['assets']}; out = []
    cols = m['detail'] or ([{'key': '_s', 'label': m['metrics']['safety']['label'], 'unit': m['metrics']['safety'].get('unit'), 'better': m['metrics']['safety']['better']}] if 'safety' in m['metrics'] else [])
    if not cols: raise ValueError('竞争格局安全性页需要 safety_detail 或 safety 指标')
    val = lambda a, c: a.get('safety') if c['key'] == '_s' else (a.get('detail') or {}).get(c['key'])
    keys = m['order']; nw = min(w * .3, max(W(A[k]['name'], S, True) + (W(A[k].get('company') or '', SMALL) + 12) for k in keys) + 16)
    cw = (w - nw) / len(cols); rh = max(26, min(36, (h - 60 - 8) / len(keys)))
    shade = ['#FBF3EA', '#F6E2CC', '#EFC9A3', '#E4A774']   # light → deep warm (sequential, one hue); text stays ink
    out.append(Tx(x, y + 18, '药物 · 公司', SMALL, MUTED, True))
    for j, c in enumerate(cols):
        cx = x + nw + j * cw
        out.append(Tx(cx + cw / 2, y + 18, c['label'] + (f'（{c["unit"]}）' if c.get('unit') else ''), SMALL, INK, True, 'middle', cw - 8))
        out.append(Tx(cx + cw / 2, y + 40, '越高越好' if c['better'] == 'higher' else '越低越好', SMALL, MUTED, False, 'middle', cw - 8))
    out.append(Ln(x, y + 56, x + w, y + 56, '#D5DADF', 1))
    rng = {}
    for c in cols:
        vs = [val(A[k], c) for k in keys if val(A[k], c) is not None]; rng[c['key']] = (min(vs), max(vs)) if vs else (0, 1)
    for r, k in enumerate(keys):
        a = A[k]; cy = y + 60 + r * rh + rh / 2; ours, fo = a.get('ours'), k == m['focus']
        if ours or fo: out.append(R(x - 6, cy - rh / 2 + 1, nw, rh - 2, TINT['brand'], EDGE['brand'] if fo else None, 8))
        out.append(Tx(x, cy, a['name'], S, INK, True, 'start'))
        if a.get('company'): out.append(Tx(x + W(a['name'], S, True) + 8, cy, a['company'], SMALL, MUTED, False, 'start'))
        for j, c in enumerate(cols):
            v = val(a, c); cx = x + nw + j * cw
            if v is None: out.append(Tx(cx + cw / 2, cy, '—', S, MUTED, False, 'middle')); continue
            lo, hi = rng[c['key']]; q = 0 if hi == lo else (v - lo) / (hi - lo)
            bad = q if c['better'] == 'lower' else 1 - q; best = (m['detail_rank'].get(c['key']) or m['rank'].get('safety') or [None])[0] == k
            out.append(R(cx + 4, cy - rh / 2 + 3, cw - 8, rh - 6, shade[min(3, int(bad * 3.999))], EDGE['brand'] if ours else None, 6))
            dp = _col_dec([val(A[q], c) for q in keys]); out.append(Tx(cx + cw / 2, cy, f'{v:.{dp}f}', S, ACCENT if best else INK, best or ours, 'middle'))
    return ''.join(out)

# ---------------------------------------------------------------- efficacy summary
EF_TYPES = ('continuous', 'binary', 'tte', 'rate')
EF_EFFECTS = {'continuous': ('md',), 'binary': ('rd', 'or', 'rr'), 'tte': ('hr',), 'rate': ('rr',)}
EF_RATIO = ('hr', 'or', 'rr')
# section heads name the effect measure and its unit, never the data type (round 9)
EF_HEAD = {'md': '均值差（95% CI）', 'rd': '率差（百分点，95% CI）', 'ratio': '比值（95% CI，对数轴）'}

def ef_measure(r):
    """The label printed before a ratio estimate: HR, OR, RR, or 率比 for an event-rate ratio; '' for differences."""
    e = r['effect']
    return '' if e in ('md', 'rd') else '率比' if r['type'] == 'rate' else e.upper()

EF_GOOD_EVENT = re.compile(r'应答|缓解|改善|达到|治愈|response|remission', re.I)

def efficacy_model(spec):
    """Validate the efficacy-summary contract and derive rates, verdicts and scales.
    spec: {arms: [{key, name, n, role: treat|comparator}] (2–4, exactly one comparator),
           rows: [{key, label, tier?, unit?, time?, type: continuous|binary|tte|rate, effect?, better: higher|lower,
                   values: [per arm, by type — continuous: number; binary: [n, N]; tte: {events, n, median?: number | 'NR'};
                            rate: number ≥ 0; null when missing],
                   vs: {treat key: {diff, ci: [lo, hi], p?}}}] (1–10), focus?: row key}.
    better: the direction of the effect estimate (diff / ratio) that favours treatment — a reduction that is good → lower;
    time to a beneficial event (response) → higher (HR > 1 favours), time to a harmful one (relapse, death) → lower.
    effect: continuous → md (mean difference); binary → rd (default, percentage points, must match the n/N rates ±0.15),
    or, rr; tte → hr; rate → rr (rate ratio). `diff` is the estimate on that scale (a ratio for hr/or/rr, > 0).
    Rows are grouped by axis: md, rd, and one log axis for every ratio (reference 1). Verdict: better / worse when the CI
    excludes the reference (0, or 1 for ratios) in / against the row's better direction, ns otherwise."""
    arms, rows = spec.get('arms') or [], spec.get('rows') or []
    if not 2 <= len(arms) <= 4: raise ValueError('有效性汇总需要 2–4 个组 arms：[{key, name, n, role}]')
    ak = [a.get('key') for a in arms]
    if len(set(ak)) != len(ak): raise ValueError('arms 的 key 不能重复')
    for a in arms:
        if not (_int(a.get('n')) and a['n'] > 0): raise ValueError(f'组「{a.get("name")}」的 n 须为正整数')
    comp = [i for i, a in enumerate(arms) if a.get('role') == 'comparator']
    if len(comp) != 1: raise ValueError('arms 须有且只有一个 role: comparator（对照组）')
    ci_ = comp[0]; treat = [i for i in range(len(arms)) if i != ci_]
    if not 1 <= len(rows) <= 10: raise ValueError('有效性汇总需要 1–10 行 rows（终点）')
    rk = [r.get('key') for r in rows]
    if len(set(rk)) != len(rk): raise ValueError('rows 的 key 不能重复')
    out, types, axes = [], [], []
    for r in rows:
        lab = r.get('label'); ty = r.get('type')
        if ty not in EF_TYPES: raise ValueError(f'「{lab}」的 type 须是 continuous、binary、tte 或 rate')
        eff = r.get('effect') or EF_EFFECTS[ty][0]
        if eff not in EF_EFFECTS[ty]: raise ValueError(f'「{lab}」的 effect 须是 {"、".join(EF_EFFECTS[ty])} 之一')
        if r.get('better') not in ('higher', 'lower'): raise ValueError(f'「{lab}」的 better 须是 higher 或 lower')
        v = r.get('values') or []
        if len(v) != len(arms): raise ValueError(f'「{lab}」的 values 须每组一个（无数据写 null）')
        pct = []
        for i, x in enumerate(v):
            if x is None: pct.append(None); continue
            if ty == 'continuous':
                if not _num(x): raise ValueError(f'「{lab}」的 values 须是数字或 null')
                pct.append(None)
            elif ty == 'rate':
                if not (_num(x) and x >= 0): raise ValueError(f'「{lab}」的 values 须是 ≥0 的事件率或 null')
                pct.append(None)
            elif ty == 'tte':
                # events / n are optional (a source may give only the median and the HR); never derive them (03 COPY-09)
                ok = isinstance(x, dict); md = x.get('median') if ok else None; ev = ('events' in x or 'n' in x) if ok else False
                if not (ok and (md is None or md == 'NR' or (_num(md) and md > 0)) and (md is not None or ev)
                        and (not ev or (_int(x.get('events')) and _int(x.get('n')) and 0 <= x['events'] <= x['n'] and x['n'] > 0))):
                    raise ValueError(f'「{lab}」的 values 须是 {{median?, events?, n?}}（至少给 median 或 events/n；events 与 n 同时给且 0 ≤ events ≤ n；median 为正数或 "NR"；源材料没有的不要推算）或 null')
                pct.append(x['events'] / x['n'] * 100 if ev else None)
            else:
                if not (isinstance(x, list) and len(x) == 2 and _int(x[0]) and _int(x[1]) and 0 <= x[0] <= x[1] and x[1] > 0):
                    raise ValueError(f'「{lab}」的 values 须是 [n, N]（0 ≤ n ≤ N）或 null')
                pct.append(x[0] / x[1] * 100)
        ratio = eff in EF_RATIO; ref = 1 if ratio else 0; ax = 'ratio' if ratio else eff
        vs = r.get('vs') or {}; cmp_ = {}
        for k, c in vs.items():
            if k not in ak or ak.index(k) == ci_: raise ValueError(f'「{lab}」的 vs「{k}」不是治疗组 key')
            ci = c.get('ci') or []
            if not (_num(c.get('diff')) and len(ci) == 2 and _num(ci[0]) and _num(ci[1]) and ci[0] <= c['diff'] <= ci[1] and ci[0] < ci[1]):
                raise ValueError(f'「{lab}」对「{k}」须给 diff 与 ci: [lo, hi]，且 lo ≤ diff ≤ hi')
            if ratio and ci[0] <= 0: raise ValueError(f'「{lab}」对「{k}」的 {eff.upper()} 及其 CI 须大于 0')
            i = ak.index(k)
            if eff == 'rd' and pct[i] is not None and pct[ci_] is not None and abs(pct[i] - pct[ci_] - c['diff']) > .15:
                raise ValueError(f'「{lab}」对「{k}」的率差 {c["diff"]:g} 与 n/N 算出的 {pct[i] - pct[ci_]:.1f} 不一致')
            sig = ci[0] > ref or ci[1] < ref; good = (c['diff'] < ref) == (r['better'] == 'lower')
            cmp_[k] = {**c, 'verdict': ('better' if good else 'worse') if sig else 'ns'}
        if ty not in types: types.append(ty)
        if ax not in axes: axes.append(ax)
        out.append({**r, 'effect': eff, 'axis': ax, 'ref': ref, 'pct': pct, 'cmp': cmp_})
    # time-to-event rows: two mistakes seen in real runs (round 9 E2E) — the better direction of a beneficial event,
    # and event counts copied from a binary row when the source gives only the median
    for r in out:
        if r['type'] != 'tte': continue
        if r['better'] == 'lower' and EF_GOOD_EVENT.search(r.get('label') or ''):
            raise ValueError(f'「{r["label"]}」是至应答类有利事件：HR > 1 表示更快达到，better 须写 higher（至复发、死亡等不利事件才写 lower）')
        ev = [[v['events'], v['n']] if isinstance(v, dict) and 'events' in v else None for v in r['values']]
        for q in out:
            if q['type'] == 'binary' and any(ev) and all(e is None or e == list(b or []) for e, b in zip(ev, q['values'])):
                raise ValueError(f'「{r["label"]}」的 events/n 与「{q["label"]}」的 n/N 完全相同，疑似抄错；源材料没有事件数就只写 median')
    if spec.get('focus') is not None and spec['focus'] not in rk: raise ValueError(f'focus「{spec["focus"]}」不在 rows 里')
    for r in out:
        nums = [b for c in r['cmp'].values() for b in (c['diff'], *c['ci'])] + ([v for v in r['values'] if v is not None] if r['type'] == 'continuous' else [])
        # ratios keep the source's precision (HR 12.4 stays 12.4, 0.85 stays 0.85), 1–2 decimals (03 COPY-09)
        r['dp'] = min(2, max([1] + [_dec(v) for v in nums])) if r['axis'] == 'ratio' else 1 if r['axis'] == 'rd' else min(2, max([_dec(v) for v in nums] + [0]))
        r['measure'] = ef_measure(r)
    bounds = lambda a: [b for r in out if r['axis'] == a for c in r['cmp'].values() for b in c['ci']]
    domain = {a: ef_log_domain(bounds(a)) if a == 'ratio' else ef_domain(bounds(a)) for a in axes}
    return {'arms': arms, 'comp': ci_, 'treat': treat, 'rows': out, 'types': types, 'axes': axes, 'domain': domain, 'focus': spec.get('focus'),
            'wins': sum(1 for r in out for c in r['cmp'].values() if c['verdict'] == 'better'), 'tests': sum(len(r['cmp']) for r in out)}


def _dec(v):
    return len(f'{abs(v):.6f}'.rstrip('0').split('.')[1])

def _r6(v):
    return math.floor(v * 1e6 + .5) / 1e6

def ef_domain(bounds):
    """Difference axis that always holds 0: [lo, hi] padded by 8 % of the span, and a 1-2-5 tick step near span / 5."""
    lo, hi = min(bounds + [0]), max(bounds + [0]); span = (hi - lo) or 1; pad = span * .08
    raw = span / 5; mag = 10 ** math.floor(math.log10(raw)); step = next(k * mag for k in (1, 2, 5, 10) if k * mag >= raw * .999)
    return [_r6(lo - pad), _r6(hi + pad), _r6(step)]

def ef_log_domain(bounds):
    """Ratio axis (log) that always holds 1: [lo, hi] padded by 8 % of the log span; step 0 marks the axis as log."""
    lo, hi = min(bounds + [1]), max(bounds + [1]); span = (math.log(hi) - math.log(lo)) or math.log(2); pad = span * .08
    return [_r6(lo * math.exp(-pad)), _r6(hi * math.exp(pad)), 0]

EF_LOG_TICKS = ([0.1, 0.2, 0.5, 1, 2, 5, 10], [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4], [0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.25, 1.5])

def ef_ticks(dom):
    lo, hi, st = dom
    if st == 0:
        for cand in EF_LOG_TICKS:
            t = [v for v in cand if lo <= v <= hi]
            if len(t) >= 3: return t
        return [v for v in EF_LOG_TICKS[2] if lo <= v <= hi] or [1]
    k = math.ceil(lo / st - 1e-9); out = []
    while k * st <= hi + 1e-9: out.append(_r6(k * st)); k += 1
    return out

def ef_pos(dom, v):
    """0..1 along the axis (linear, or log when the step is 0)."""
    lo, hi, st = dom
    if st == 0: return (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return (v - lo) / (hi - lo)


def treat_colors(t):
    """Treat arms light → deep in the treat hue in the listed order (list doses low → high, so the highest dose is deepest);
    the lightest is 30 % toward white so its forest square still reads on white. The comparator keeps the comparator slate."""
    return [DC._mix(CAT_TREAT, .3 * (1 - k / max(1, t - 1))) if t > 1 else CAT_TREAT for k in range(t)]

def ef_value(r, i):
    v = r['values'][i]
    if v is None: return '—', ''
    if r['type'] == 'continuous': return f'{v:+.{r["dp"]}f}'.replace('-', '−'), ''
    if r['type'] == 'rate': return f'{v:.2f}', ''
    if r['type'] == 'tte':
        md = v.get('median'); return ('未达到' if md == 'NR' else f'{md:g}' if md is not None else '—'), (f'{v["events"]}/{v["n"]}' if 'events' in v else '')
    return f'{r["pct"][i]:.1f}%', f'{v[0]}/{v[1]}'

def ef_diff(c, dp=1, measure=''):
    g = lambda v: f'{v:.{dp}f}'.replace('-', '−')
    return f'{measure + " " if measure else ""}{g(c["diff"])} ({g(c["ci"][0])}, {g(c["ci"][1])})'

def _ef_measure(spec, w):
    rows = spec.get('rows') or []; axes = []
    for r in rows:
        eff = r.get('effect') or (EF_EFFECTS.get(r.get('type')) or ('?',))[0]; a = 'ratio' if eff in EF_RATIO else eff
        if a not in axes: axes.append(a)
    return 38 + len(axes) * 30 + len(rows) * 40 + 4

@kind('efficacy', measure=_ef_measure)
def efficacy(spec, box, gid, mode):
    """Efficacy summary: arm header (name, n); per axis (mean difference, rate difference, ratios on a log axis) a section
    headed by the measure; one row per endpoint — tier tag, label with unit and time, each arm's value (binary: % with n/N
    under it; time-to-event: median with events/N; rate: events per patient-year), a mini forest per treat
    arm (filled square when the CI excludes 0 in the good direction, hollow when not, red when it excludes 0 the wrong way),
    the difference with its 95% CI and p beside it."""
    m = efficacy_model(spec); x, y, w, h = box; arms = m['arms']; tr = m['treat']; tc = dict(zip(tr, treat_colors(len(tr))))
    tagw = lambda r: W(r['tier'], SMALL, True) + 20 if r.get('tier') else 0
    lw = min(w * .3, max(tagw(r) + W(r['label'], S, True) * T.HEADROOM for r in m['rows']) + 12)
    vw = max(92, max(W(a['name'], SMALL, True) for a in arms) * T.HEADROOM + 14)
    dw = max(W(ef_diff(c, r['dp'], r['measure']), SMALL) for r in m['rows'] for c in r['cmp'].values()) * T.HEADROOM + 26; pw = W('<0.001', SMALL) + 16
    fw = min(300, w - lw - vw * len(arms) - 36 - dw - pw)
    if fw < 160:
        longest = max(m['rows'], key=lambda r: W(r['label'], S, True))['label']
        raise ValueError(f'有效性汇总放不下：森林图只剩 {fw:.0f} px（至少 160）。终点名写短名（约 10 字内，如“PASI 90 应答”），'
                         f'单位和时点放 unit / time 字段，不写进 label（当前最长：“{longest}”）；组名用短名；仍放不下再减组或拆页')
    xv = x + lw; xf = xv + vw * len(arms) + 18; xd = xf + fw + 18; xp = x + w - pw
    out = []
    for i, a in enumerate(arms):
        cx = xv + i * vw + vw / 2; col = tc.get(i, TOK['charts']['comparator']); nt = f'n={a["n"]}'
        out.append(Tx(cx, y + 11, a['name'], SMALL, INK, True, 'middle'))
        out.append(Dot(cx - W(nt, SMALL) / 2 - 10, y + 28, 5, col)); out.append(Tx(cx + 2, y + 28, nt, SMALL, MUTED, False, 'middle'))
    out.append(Tx(xd, y + 11, f'{"效应值" if "ratio" in m["axes"] else "差值"}（vs {arms[m["comp"]]["name"]}）', SMALL, INK, True)); out.append(Tx(xp + pw - 4, y + 11, 'P', SMALL, INK, True, 'end'))
    cy0 = y + 38; ns = len(m['axes']); rh = max(38, min(60, (h - 38 - ns * 30 - 4) / len(m['rows'])))
    for t in m['axes']:
        dom = m['domain'][t]; X = lambda v: xf + ef_pos(dom, v) * fw; ref = 1 if t == 'ratio' else 0
        out.append(Ln(x, cy0, x + w, cy0, '#D5DADF', 1)); out.append(Tx(x, cy0 + 15, EF_HEAD[t], SMALL, MUTED, True, 'start', xf - x - 10))
        for v in ef_ticks(dom): out.append(Tx(X(v), cy0 + 15, f'{v:g}'.replace('-', '−'), SMALL, INK if v == ref else MUTED, v == ref, 'middle'))
        rows = [r for r in m['rows'] if r['axis'] == t]; ry0 = cy0 + 30
        out.append(Ln(X(ref), ry0, X(ref), ry0 + len(rows) * rh, '#9AA1A8', 1.2))
        for k, r in enumerate(rows):
            ry = ry0 + k * rh; cy = ry + rh / 2; fo = r['key'] == m['focus']
            if fo: out.append(R(x - 6, ry + 1, w + 12, rh - 2, TINT['brand'], EDGE['brand'], 8))
            elif k % 2: out.append(R(x - 6, ry + 1, w + 12, rh - 2, '#F7F8F9', None, 6))
            tier = r.get('tier'); tx = x
            if tier:
                tw_ = W(tier, SMALL, True) + 12; pri = tier == '主要'
                out.append(R(x, cy - 11, tw_, 22, TINT['brand'] if pri else '#EEF0F2', None, 11)); out.append(Tx(x + tw_ / 2, cy, tier, SMALL, ACCENT if pri else BODY, True, 'middle'))
                tx = x + tw_ + 8
            sub = ' · '.join(v for v in (r.get('unit'), r.get('time')) if v)
            if sub and rh >= 38: out += [Tx(tx, cy - 9, r['label'], S, INK, True, 'start', lw - (tx - x) - 8), Tx(tx, cy + 11, sub, SMALL, MUTED, False, 'start', lw - (tx - x) - 8)]
            else: out.append(Tx(tx, cy, r['label'], S, INK, True, 'start', lw - (tx - x) - 8))
            for i in range(len(arms)):
                main, small = ef_value(r, i); cx = xv + i * vw + vw / 2
                if small and rh >= 38: out += [Tx(cx, cy - 9, main, S, INK if i in tr else BODY, i in tr, 'middle'), Tx(cx, cy + 11, small, SMALL, MUTED, False, 'middle')]
                else: out.append(Tx(cx, cy, main, S, INK if i in tr else BODY, i in tr and main != '—', 'middle'))
            n = len(r['cmp']); sp = min(16, (rh - 14) / max(1, n - 1))
            for j, (key, c) in enumerate(r['cmp'].items()):
                i = [a['key'] for a in arms].index(key); col = tc[i]; yy = cy + (j - (n - 1) / 2) * sp
                vcol = RISK if c['verdict'] == 'worse' else (col if c['verdict'] == 'better' else '#9AA1A8')
                out.append(Ln(X(c['ci'][0]), yy, X(c['ci'][1]), yy, vcol, 2))
                out.append(R(X(c['diff']) - 5, yy - 5, 10, 10, vcol if c['verdict'] != 'ns' else '#FFFFFF', vcol, 2, False, 1.6))
                out.append(R(xd, yy - 4, 8, 8, col, None, 2))
                out.append(Tx(xd + 14, yy, ef_diff(c, r['dp'], r['measure']), SMALL, INK if c['verdict'] != 'ns' else MUTED, c['verdict'] == 'better' and fo, 'start'))
                if c.get('p') is not None: out.append(Tx(xp + pw - 4, yy, str(c['p']), SMALL, INK if c['verdict'] != 'ns' else MUTED, False, 'end'))
        cy0 = ry0 + len(rows) * rh + 4
    return ''.join(out)


# ---------------------------------------------------------------- schedule of assessments (SoA)
_WK = re.compile(r'^\s*([WDM])\s*([-−]?\d+(?:\.\d+)?)\s*$')
# key events on the visit axis and the treatment periods drawn under the visit header (round 9)
SOA_EVENTS = ('consent', 'random', 'dose', 'interim', 'primary', 'secondary', 'eot', 'eos', 'other')
SOA_BANDS = ('drug', 'background', 'rescue', 'washout', 'other')

def soa_week(label):
    """'W−4' → -4, 'D1' → 1/7 week, 'M3' → 13 weeks; None when the label is not a plain W/D/M number."""
    m = _WK.match(label or '') if isinstance(label, str) else None
    if not m: return None
    v = float(m[2].replace('−', '-')); return v if m[1] == 'W' else v / 7 if m[1] == 'D' else v * 52 / 12

def soa_model(spec):
    """Validate the SoA contract and derive the per-visit load, the section × visit counts and the period spans.
    spec: {visits: [{v, week, period?}] (2–30, v unique, week W/D/M labels strictly increasing when all parse),
           rows: [{section} | {item, at: [per visit 1 | 0 | null | text]}] (1–40 items, a section heads ≥1 item),
           events?: [{at: v, label, kind: consent|random|dose|interim|primary|secondary|eot|eos|other}] (≤12),
           bands?: [{label, from: v, to: v, kind: drug|background|rescue|washout|other, text?}] (≤6),
           footnotes?, focus?: item}. Visits may carry a window ('±3 天'). A period occupies one contiguous run of visits.
    A text cell counts as done (e.g. '×2', 'ᵃ'); 0, null and '' do not. `primary` lists the primary-endpoint visits."""
    vis, rows = spec.get('visits') or [], spec.get('rows') or []
    if not 2 <= len(vis) <= 30: raise ValueError('SoA 需要 2–30 个访视 visits：[{v, week, period?}]')
    vk = [x.get('v') for x in vis]
    if any(not isinstance(v, str) or not v.strip() for v in vk): raise ValueError('每个访视须有名称 v（如 V1、EOS）')
    if len(set(vk)) != len(vk): raise ValueError('访视名称 v 不能重复')
    t = [soa_week(x.get('week')) for x in vis]
    if all(v is not None for v in t):
        for i in range(1, len(t)):
            if t[i] <= t[i - 1]: raise ValueError(f'访视时间须递增：{vis[i - 1]["week"]} → {vis[i]["week"]}')
    else: t = None
    periods = []
    for i, x in enumerate(vis):
        pn = x.get('period') or ''
        if periods and periods[-1]['name'] == pn: periods[-1]['to'] = i + 1; continue
        if pn and any(q['name'] == pn for q in periods): raise ValueError(f'分期「{pn}」的访视不连续')
        periods.append({'name': pn, 'from': i, 'to': i + 1})
    items, sections, cur = [], [], None
    for r in rows:
        if 'section' in r:
            if not isinstance(r['section'], str) or not r['section'].strip(): raise ValueError('section 须是非空文字')
            if cur is not None and not cur['items']: raise ValueError(f'分组「{cur["name"]}」下没有评估项目')
            cur = {'name': r['section'], 'items': [], 'counts': [0] * len(vis)}; sections.append(cur); continue
        name = r.get('item')
        if not isinstance(name, str) or not name.strip(): raise ValueError('每行须有 item（评估项目）或 section（分组）')
        at = r.get('at') or []
        if len(at) != len(vis): raise ValueError(f'「{name}」的 at 须每个访视一个（共 {len(vis)} 个）')
        marks = []
        for i, c in enumerate(at):
            if c is None or c is False or c == 0 or c == '': continue
            if c is True or c == 1 or (isinstance(c, str) and c.strip()): marks.append(i); continue
            raise ValueError(f'「{name}」的 at 只能写 1、0、null 或文字标记')
        if not marks: raise ValueError(f'「{name}」在所有访视都没有标记')
        if cur is None: cur = {'name': '', 'items': [], 'counts': [0] * len(vis)}; sections.append(cur)
        it = {'item': name, 'section': len(sections) - 1, 'marks': marks, 'count': len(marks)}; items.append(it); cur['items'].append(len(items) - 1)
        for i in marks: cur['counts'][i] += 1
    if cur is not None and not cur['items']: raise ValueError(f'分组「{cur["name"]}」下没有评估项目')
    if not 1 <= len(items) <= 40: raise ValueError('SoA 需要 1–40 个评估项目')
    if len([q for q in sections if q['name']]) > 8: raise ValueError('SoA 最多 8 个分组 section')
    names = [x['item'] for x in items]
    if len(set(names)) != len(names): raise ValueError('评估项目 item 不能重复')
    if spec.get('focus') is not None and spec['focus'] not in names: raise ValueError(f'focus「{spec["focus"]}」不是评估项目：写某一个评估项目 item 的原文全名（如「{names[0]}」），不是缩写或几项合写')
    vi = {v: i for i, v in enumerate(vk)}
    events = []
    for e in spec.get('events') or []:
        if e.get('at') not in vi: raise ValueError(f'关键节点「{e.get("label")}」的 at 须是访视名称 v')
        if e.get('kind') not in SOA_EVENTS: raise ValueError(f'关键节点「{e.get("label")}」的 kind 须是 {"、".join(SOA_EVENTS)} 之一')
        if not isinstance(e.get('label'), str) or not e['label'].strip(): raise ValueError('关键节点须有 label')
        events.append({'i': vi[e['at']], 'v': e['at'], 'label': e['label'], 'kind': e['kind']})
    if len(events) > 12: raise ValueError('关键节点 events 最多 12 个')
    bands = []
    for b in spec.get('bands') or []:
        lab = b.get('label')
        if not isinstance(lab, str) or not lab.strip(): raise ValueError('给药 / 治疗时段须有 label')
        if b.get('from') not in vi or b.get('to') not in vi: raise ValueError(f'时段「{lab}」的 from / to 须是访视名称 v')
        if vi[b['from']] > vi[b['to']]: raise ValueError(f'时段「{lab}」的 from 在 to 之后')
        if b.get('kind') not in SOA_BANDS: raise ValueError(f'时段「{lab}」的 kind 须是 {"、".join(SOA_BANDS)} 之一')
        bands.append({'label': lab, 'kind': b['kind'], 'text': b.get('text') or '', 'from': vi[b['from']], 'to': vi[b['to']]})
    if len(bands) > 6: raise ValueError('给药 / 治疗时段 bands 最多 6 条')
    primary = sorted({e['i'] for e in events if e['kind'] == 'primary'})
    load = [sum(q['counts'][i] for q in sections) for i in range(len(vis))]; mx = max(load)
    return {'visits': vis, 't': t, 'periods': periods, 'items': items, 'sections': sections, 'load': load, 'max': mx,
            'busiest': [i for i, v in enumerate(load) if v == mx], 'total': sum(load), 'focus': spec.get('focus'),
            'events': events, 'bands': bands, 'primary': primary}


# ---------------------------------------------------------------- cumulative exposure on the development plan (round 9)
XP_BANDS = ('any', 'w26', 'w52')
XP_LABEL = {'any': '任何暴露', 'w26': '≥26 周', 'w52': '≥52 周'}

def exposure_plan(spec):
    """Cumulative study-drug exposure along the clinical development plan, against the ICH E1 targets at each NDA.
    spec: {program: <clinical-development-plan contract>, targets?: {any?: 1500, w26?, w52?}, target_label?, unit?, focus?: lane key}.
    A bar of the plan counts when it carries exposure: {n (sample size), ctrl? (control share 0–<1, default 0),
    exposed? (drug-exposed patients, default round(n × (1 − ctrl))), w26?, w52? (of them, exposed ≥26 / ≥52 weeks),
    at? (when the data count, default the bar's end value)}. Counts are cumulated in time order; each top-level lane is
    an indication and its first `submit` milestone is its NDA: the exposure counted by then (same unit included) is
    compared with the targets. The plan is the same object the Gantt and its studio edit (one data base)."""
    pg = DC.program_model(spec.get('program') or {}); lanes = pg['lanes']; gran = pg['granularity']
    tg = spec.get('targets') or {'any': 1500}
    for k, v in tg.items():
        if k not in XP_BANDS: raise ValueError(f'targets 的键须是 {"、".join(XP_BANDS)} 之一')
        if not (_int(v) and v > 0): raise ValueError(f'targets.{k} 须为正整数')
    top = {}
    for ln in lanes:
        top[ln['key']] = ln['key'] if ln.get('parent') is None else top[ln['parent']]
    name = {ln['key']: ln['name'] for ln in lanes}
    studies = []
    for li, ln in enumerate(lanes):
        for br in ln['bars']:
            x = br.get('exposure')
            if x is None: continue
            what = f'「{ln["name"]} · {br.get("label") or br["phase"]}」的 exposure'
            if not isinstance(x, dict) or not (_int(x.get('n')) and x['n'] > 0): raise ValueError(f'{what}须给样本量 n（正整数）')
            ctrl = x.get('ctrl', 0)
            if not (_num(ctrl) and 0 <= ctrl < 1): raise ValueError(f'{what}的对照比例 ctrl 须在 0 到 1 之间（不含 1）')
            ex = x.get('exposed', round(x['n'] * (1 - ctrl)))
            if not (_int(ex) and 0 <= ex <= x['n']): raise ValueError(f'{what}的 exposed 须是 0 到 n 之间的整数')
            band = {'any': ex}
            for k, up in (('w26', 'any'), ('w52', 'w26')):
                if x.get(k) is not None:
                    if not (_int(x[k]) and 0 <= x[k] <= band.get(up, ex)): raise ValueError(f'{what}的 {k} 须是不超过{XP_LABEL[up]}例数的整数')
                    band[k] = x[k]
            t = DC.tspan(x['at'], what + '的 at')[0] if x.get('at') is not None else DC.tspan(br['end'], what + '的结束')[0]
            if not pg['from'] <= t < pg['to']: raise ValueError(f'{what}的计入时点不在 from–to 之内')
            studies.append({'lane': ln['key'], 'lane_name': ln['name'], 'ind': top[ln['key']], 'ind_name': name[top[ln['key']]], 'key': br['key'],
                            'label': br.get('label') or br['phase'], 'phase': br['phase'], 'n': x['n'], 'ctrl': ctrl, 'band': band, 't': t,
                            'at_text': DC.ttext(t, gran), 'order': li})
    if not studies: raise ValueError('暴露累计需要至少一个研究条带 exposure：{n, ctrl?, exposed?, at?}')
    bands = [k for k in XP_BANDS if k == 'any' or any(k in s['band'] for s in studies) or k in tg]
    studies.sort(key=lambda s: (s['t'], s['order']))
    run = {k: 0 for k in bands}; first = {k: None for k in bands}
    for s in studies:
        for k in bands: run[k] += s['band'].get(k, 0)
        s['cum'] = dict(run)
        for k in bands:
            if first[k] is None and k in tg and run[k] >= tg[k]: first[k] = s['t']
    inds = []
    for ln in lanes:
        if ln.get('parent') is not None: continue
        fam = [l for l in lanes if top[l['key']] == ln['key']]
        sub = sorted((m for l in fam for m in l['milestones'] if m['kind'] == 'submit'), key=lambda m: m['t'])
        has = any(s['ind'] == ln['key'] for s in studies)
        if not sub and not has: continue
        nda = sub[0] if sub else None; cum = {k: 0 for k in bands}
        if nda:
            for s in studies:
                if s['t'] <= nda['t']:
                    for k in bands: cum[k] += s['band'].get(k, 0)
        inds.append({'key': ln['key'], 'name': ln['name'], 'nda': nda and {'t': nda['t'], 'label': nda['label'], 'text': DC.ttext(nda['t'], gran), 'key': nda['key']},
                     'cum': cum, 'met': {k: cum[k] >= tg[k] for k in tg if k in cum} if nda else {}, 'gap': {k: max(0, tg[k] - cum[k]) for k in tg if k in cum} if nda else {}})
    if spec.get('focus') is not None and spec['focus'] not in [i['key'] for i in inds]: raise ValueError(f'focus「{spec["focus"]}」不是有暴露或递交里程碑的适应症泳道')
    return {'plan': pg, 'studies': studies, 'indications': inds, 'bands': bands, 'targets': tg, 'first': first,
            'totals': dict(run), 'unit': spec.get('unit', '例'), 'target_label': spec.get('target_label', 'ICH E1'), 'focus': spec.get('focus'),
            'max': max([run['any']] + list(tg.values())), 'ref': xp_ref(spec),
            'meta': {k: spec[k] for k in ('targets', 'focus', 'unit', 'target_label') if k in spec}}


def xp_ref(spec):
    """The plan a figure and its tables follow in HTML (data-kz-xp-plan): the program id, else a digest of the program."""
    import hashlib
    pr = spec.get('program') or {}
    return str(pr['id']) if pr.get('id') is not None else 'xp-' + hashlib.sha1(json.dumps(pr, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]


def _xp_measure(spec, w):
    return 250

def xp_nice(v):
    """Axis top and step for a count axis: 1-2-2.5-5 steps, 4–6 ticks, top ≥ 1.08 × v."""
    raw = v * 1.08 / 5; mag = 10 ** math.floor(math.log10(raw)); st = next(k * mag for k in (1, 2, 2.5, 5, 10) if k * mag >= raw)
    return math.ceil(v * 1.08 / st) * st, st

def n0(v):
    return f'{v:,}'

@kind('exposure-plan', measure=_xp_measure)
def exposure_plan_chart(spec, box, gid, mode):
    """Cumulative exposure (exposure_plan): a step line of the drug-exposed patients counted study by study on the plan's
    time axis (a dot per study in its indication's colour), the ICH E1 total target as a dashed red line, one dashed
    vertical per indication NDA with its number chip and name, the cumulative count at that NDA ringed (met / short) and
    the first crossing of the target named. The readiness table under it is a separate (native) table."""
    m = exposure_plan(spec); x, y, w, h = box; pg = m['plan']; a, b = pg['from'], pg['to']
    tgt = m['targets'].get('any'); top, st = xp_nice(m['max'])
    inds = [i for i in m['indications'] if i['nda']]; cat = TOK['charts']['categorical']
    icol = {i['key']: cat[k % len(cat)] for k, i in enumerate(m['indications'])}
    x0 = x + 58; x1 = x + w - 132; X = lambda t: x0 + (t - a) / (b - a) * (x1 - x0)
    chips = xp_chips(inds, X, x0, x1 + 120, lambda s_: W(s_, SMALL, True))
    y0 = y + 46 + 22 * (max([c[2] for c in chips] + [0])); y1 = y + h - 30; Y = lambda v: y1 - v / top * (y1 - y0)
    out = []
    v = 0
    while v <= top + 1e-9:
        out.append(Ln(x0, Y(v), x1, Y(v), TOK['charts']['grid'], 1)); out.append(Tx(x0 - 8, Y(v), n0(int(v)), SMALL, MUTED, False, 'end')); v += st
    yr = int(a // 4) + (0 if a % 4 == 0 else 1)
    while yr * 4 <= b:
        tx = X(yr * 4)
        if x0 - 1 <= tx <= x1 + 1:   # a tick at each year start, the year in the middle of its year (none for a year past the axis)
            out.append(Ln(tx, y1, tx, y1 + 5, TOK['charts']['axis'], 1))
            if yr * 4 + 2 <= b: out.append(Tx(X(yr * 4 + 2), y1 + 17, str(yr), SMALL, MUTED, False, 'middle'))
        yr += 1
    out.append(Ln(x0, y1, x1, y1, TOK['charts']['axis'], 1.2))
    # NDA verticals (behind the step), numbered chips on the tiers found above
    for k, (i, (lx, lw, tier, lab)) in enumerate(zip(inds, chips)):
        nx = X(i['nda']['t']); ty = y + 12 + tier * 22
        out.append(Ln(nx, ty + 12, nx, y1, '#8A949E', 1.2, True))
        out.append(R(lx, ty - 10, lw, 20, TINT['brand'] if i['key'] == m['focus'] else '#F3F4F6', None, 10))
        out.append(Dot(lx + 11, ty, 8, icol[i['key']])); out.append(Tx(lx + 11, ty, str(k + 1), SMALL, '#FFFFFF', True, 'middle'))
        out.append(Tx(lx + 24, ty, lab, SMALL, INK, True, 'start'))
    # target line
    if tgt:
        out.append(Ln(x0, Y(tgt), x1, Y(tgt), RISK, 1.6, True)); out.append(Tx(x1 + 8, Y(tgt) - 9, f'{m["target_label"]} {n0(tgt)} {m["unit"]}', SMALL, RISK, True, 'start'))
    # the step line and a dot per study
    px, py = X(a), Y(0); path = []
    for s in m['studies']:
        nx = X(s['t']); path += [(px, py, nx, py), (nx, py, nx, Y(s['cum']['any']))]; px, py = nx, Y(s['cum']['any'])
    path.append((px, py, x1, py))
    out += [Ln(*seg, CAT_TREAT, 2.6) for seg in path]
    taken = [(min(p_[0], p_[2]), p_[1] - 3, max(p_[0], p_[2]), p_[1] + 3) for p_ in path if p_[1] == p_[3]]   # flat steps, for label placement
    for s in m['studies']: out.append(Dot(X(s['t']), Y(s['cum']['any']), 5, icol[s['ind']], '#FFFFFF'))
    out.append(Tx(x1 + 8, py + 10, f'累计 {n0(m["totals"]["any"])} {m["unit"]}', SMALL, INK, True, 'start'))
    # cumulative at each NDA, ringed: met in the treat hue, short in risk with the gap
    for i in inds:
        nx, ny = X(i['nda']['t']), Y(i['cum']['any']); ok = i['met'].get('any', True)
        out.append(Dot(nx, ny, 7, '#FFFFFF', CAT_TREAT if ok else RISK))
        lab = f'{n0(i["cum"]["any"])}' + ('' if ok else f'（差 {n0(i["gap"]["any"])}）'); lw_ = W(lab, SMALL, True)
        # right of the ring unless the next study's riser would cut through the text; then left of it
        left = any(nx + 6 < X(s['t']) < nx + 14 + lw_ and s['t'] > i['nda']['t'] for s in m['studies'])
        out.append(Tx(nx - 10 if left else nx + 10, ny - 12, lab, SMALL, INK if ok else RISK, True, 'end' if left else 'start'))
        taken.append((nx - 10 - lw_, ny - 21, nx - 10, ny - 3) if left else (nx + 10, ny - 21, nx + 10 + lw_, ny - 3))
    if tgt and m['first']['any'] is not None:
        fx = X(m['first']['any']); out.append(Diamond(fx, Y(tgt), 7, ACCENT))
        # first-reach label: above-left of the diamond unless an NDA label or the step line is there; then above-right,
        # below-left, below-right (an NDA shortly before the first reach puts its gap label on the same band)
        fl = f'首次达到 {DC.ttext(m["first"]["any"], pg["granularity"])}'; fw = W(fl, SMALL, True); ty_ = Y(tgt)
        hit = lambda b_: any(b_[0] < q[2] and q[0] < b_[2] and b_[1] < q[3] and q[1] < b_[3] for q in taken)
        cands = [(fx - 10, ty_ - 11, 'end'), (fx + 10, ty_ - 11, 'start'), (fx - 10, ty_ + 13, 'end'), (fx + 10, ty_ + 13, 'start')]
        box = lambda c: (c[0] - fw, c[1] - 9, c[0], c[1] + 9) if c[2] == 'end' else (c[0], c[1] - 9, c[0] + fw, c[1] + 9)
        cx_, cy_, an = next((c for c in cands if not hit(box(c)) and x0 <= box(c)[0] and box(c)[2] <= x1 + 2), cands[0])
        out.append(Tx(cx_, cy_, fl, SMALL, ACCENT, True, an))
    return ''.join(out)


def xp_chips(inds, X, lo, hi, width, gap=6, max_tiers=3):
    """NDA chips of the exposure figure (= runtime/kz-explore.js): each centred on its NDA vertical and kept inside
    [lo, hi], on the lowest tier (≤ 3) where it clears the chips already there. → [(left, width, tier, label)]."""
    out = []
    for k, i in enumerate(inds):
        lab = f'{i["name"]} NDA {i["nda"]["text"]}'; lw = width(lab) + 36; nx = X(i['nda']['t'])
        lx = min(max(nx - lw / 2, lo), hi - lw)
        tier = next((t for t in range(max_tiers) if all(c[2] != t or lx >= c[0] + c[1] + gap or lx + lw + gap <= c[0] for c in out)), None)
        if tier is None: raise ValueError(f'NDA 标签放不下（{len(inds)} 个适应症挤在一起）：拆页或缩短适应症名称')
        out.append((lx, lw, tier, lab))
    return out


def exposure_readiness_table(m):
    """NDA readiness, one row per indication with an NDA: the cumulative count by then per band, ✓ or the gap."""
    tg = m['targets']; bands = [k for k in m['bands'] if k in tg]
    cols = ['适应症', 'NDA'] + [f'{XP_LABEL[k]}（目标 {n0(tg[k])}）' for k in bands]
    rows = []
    for i in m['indications']:
        if not i['nda']: continue
        cells = [i['name'], i['nda']['text']]
        for k in bands:
            ok = i['met'][k]; cells.append({'text': f'{n0(i["cum"][k])} ✓' if ok else f'{n0(i["cum"][k])} · 差 {n0(i["gap"][k])}', 'tone': None if ok else 'risk', 'bold': not ok})
        rows.append([({'text': c, 'tone': 'brand'} if j == 0 and i['key'] == m['focus'] else c) if not isinstance(c, dict) else {k_: v for k_, v in c.items() if v is not None}
                     for j, c in enumerate(cells)])
    return {'columns': cols, 'rows': rows, 'widths': [1.4, 1] + [1.6] * len(bands), 'center': list(range(1, len(cols))), 'live': {'xp': 'readiness', 'plan': m['ref'], 'meta': m['meta']}}


def exposure_ledger_table(m):
    """The study ledger (D017-style): indication, study, n, control share, drug-exposed, when it counts, cumulative —
    in count order with each NDA as its own tinted row (studies of the same unit come first) and the first crossing of
    the total target flagged."""
    tgt = m['targets'].get('any'); cross = next((k for k, s in enumerate(m['studies']) if tgt and s['cum']['any'] >= tgt), None)
    seq = [(s['t'], 0, k, s) for k, s in enumerate(m['studies'])] + [(i['nda']['t'], 1, k, i) for k, i in enumerate(m['indications']) if i['nda']]
    cols = ['适应症', '研究', '样本量', '对照比例', '暴露例数', '计入时点', '累计暴露']; rows = []
    for t, kind_, k, o in sorted(seq, key=lambda e: (e[0], e[1], e[2])):
        if kind_ == 0:
            s = o; flag = f' · 首次达到 {n0(tgt)}' if k == cross else ''
            rows.append([s['ind_name'] if s['lane'] == s['ind'] else f'{s["ind_name"]} · {s["lane_name"]}', s['label'], n0(s['n']),
                         f'{s["ctrl"] * 100:.0f}%' if s['ctrl'] else '—', n0(s['band']['any']), s['at_text'],
                         {'text': n0(s['cum']['any']) + flag, 'tone': 'brand', 'bold': True} if flag else n0(s['cum']['any'])])
        else:
            i = o; ok = i['met'].get('any', True); tint = lambda x, **kw: {'text': x, 'tone': 'tint', **kw}
            rows.append([tint(f'{i["name"]} NDA', bold=True), tint(i['nda']['label']), tint(''), tint(''), tint(''), tint(i['nda']['text']),
                         {'text': f'{n0(i["cum"]["any"])} ' + ('✓' if ok else f'· 差 {n0(i["gap"]["any"])}'), 'tone': 'tint' if ok else 'risk', 'bold': True}])
    return {'columns': cols, 'rows': rows, 'widths': [1.5, 2, .8, .8, .9, 1, 1.6], 'numeric': [2, 4, 6], 'center': [3, 5], 'live': {'xp': 'ledger', 'plan': m['ref'], 'meta': m['meta']}}
