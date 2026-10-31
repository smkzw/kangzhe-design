"""Text for template pages (03 TYPE-01/04, COPY-04): inline emphasis markup, measured widths, CJK line breaking.

Markup (one level, no nesting): **加粗**  !!深红加粗!!  __下划线__  ==高亮==  — a backslash escapes a marker.
Widths come from Microsoft YaHei when its font file is on this machine (the face PowerPoint renders the deck
with); otherwise from a per-class approximation that errs wide, so a fitted line never overflows in PowerPoint.
"""
from pathlib import Path
import re, unicodedata
from functools import lru_cache

MARKS = (('!!', 'risk'), ('**', 'bold'), ('__', 'underline'), ('==', 'highlight'))
_FONT_DIRS = [Path('/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts'), Path('/Library/Fonts/Microsoft'),
              Path('/Library/Fonts'), Path.home() / 'Library/Fonts', Path('C:/Windows/Fonts')]

def parse(s):
    """'普通**重点**' → [('普通', frozenset()), ('重点', {'bold'})]; adjacent runs with equal style merge."""
    runs, buf, style, i = [], '', None, 0
    def flush(st):
        nonlocal buf
        if buf:
            if runs and runs[-1][1] == st: runs[-1] = (runs[-1][0] + buf, st)
            else: runs.append((buf, st))
        buf = ''
    s = str(s)
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s): buf += s[i + 1]; i += 2; continue
        hit = next(((m, k) for m, k in MARKS if s.startswith(m, i)), None)
        if hit:
            m, k = hit
            if style is None: flush(frozenset()); style = k
            elif style == k: flush(frozenset({k} | ({'bold'} if k == 'risk' else set()))); style = None
            else: buf += m
            i += len(m); continue
        buf += s[i]; i += 1
    if style is not None: buf = MARKS[[k for _, k in MARKS].index(style)][0] + buf  # unclosed marker stays literal
    flush(frozenset())
    return runs

def plain(s):
    return ''.join(t for t, _ in parse(s))

def emphasis_count(s):
    return sum(1 for t, st in parse(s) if st and t.strip())

@lru_cache(maxsize=None)
def _font(bold):
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    for d in _FONT_DIRS:
        for name in (['msyhbd.ttc', 'msyhbd.ttf'] if bold else ['msyh.ttc', 'msyh.ttf']):
            if (d / name).exists():
                try: return ImageFont.truetype(str(d / name), 100, index=0)
                except OSError: pass
    return None

def metrics_source():
    return 'Microsoft YaHei' if _font(False) else 'approximation'

@lru_cache(maxsize=65536)
def _w100(ch, bold):
    f = _font(bold)
    if f: return f.getlength(ch)
    if unicodedata.east_asian_width(ch) in 'WF': return 100.0
    if ch == ' ': return 32.0
    return 62.0 if bold else 58.0

def width(text, size, bold=False):
    return sum(_w100(c, bold) for c in text) * size / 100.0

def runs_width(runs, size, bold=False):
    return sum(width(t, size, bold or 'bold' in st or 'risk' in st) for t, st in runs)

# ---------- line breaking ----------
_NO_START = set('，。、；：？！）》」』】〕”’%‰,.;:?!)]}·…—/')
_NO_END = set('（《「『【〔“‘([{/')
_UNITS = set('周天日月年岁例份次项人组个页条mgkgmlLμ%')

# a number keeps its comparator and a following Latin unit (≥160/100 mmHg, 7.0 mmol/L, 27 kg/m²)
_UNIT_RE = r'(?:mmHg|mmol/L|mg/dL|μmol/L|mmol/mol|g/L|mg/L|U/L|IU/L|kg/m²|kg/m2|mg|kg|mL|ml|IU|μg|ng/mL|min|h|%)'
_TOKEN = re.compile(r'[≥≤<>±~～−-]?\d[\d.,/:–\-]*(?:\s?' + _UNIT_RE + r'(?![A-Za-z]))?|[A-Za-z][A-Za-z0-9.+\-−–/]*|[^\S\n]+|.')

def _tokens(runs):
    """Break opportunities: each CJK char is a token; Latin words, numbers (with a following unit) stay whole;
    closing punctuation sticks to the token before it, opening punctuation to the token after it."""
    out = []  # list of [(text, style), ...] per token
    for text, st in runs:
        for m in re.finditer(_TOKEN, text):
            out.append([(m.group(0), st)])
    merged = []
    for tok in out:
        t = tok[0][0]
        if merged and (t[0] in _NO_START or (t[0] in _UNITS and re.search(r'[0-9]$', merged[-1][-1][0]))):
            merged[-1] += tok; continue
        if merged and merged[-1][-1][0] and merged[-1][-1][0][-1] in _NO_END:
            merged[-1] += tok; continue
        merged.append(tok)
    return merged

def _join(tokens):
    runs = []
    for tok in tokens:
        for t, st in tok:
            if runs and runs[-1][1] == st: runs[-1] = (runs[-1][0] + t, st)
            else: runs.append((t, st))
    return runs

def _is_orphan(line):
    s = ''.join(t for t, _ in line).strip()
    core = ''.join(c for c in s if c not in _NO_START)
    return len(core) == 1 and unicodedata.east_asian_width(core) in 'WF'

HEADROOM = __import__('json').loads((Path(__file__).resolve().parents[2] / 'tokens/tokens.json').read_text())['layout']['templates']['measure_headroom']

def wrap(markup, max_w, size, bold=False, keep_space=False):
    """→ list of lines, each a list of (text, style) runs; trailing spaces trimmed; no single-character last line.
    Lines are filled to max_w / HEADROOM: PowerPoint's text layout and ppt-master's checker run a few per cent wider
    than the font metrics measured here."""
    max_w = max_w / HEADROOM
    toks = _tokens(parse(markup))
    lines, cur, cur_w = [], [], 0.0
    for tok in toks:
        tw = runs_width(tok, size, bold)
        if cur and cur_w + tw > max_w and ''.join(t for t, _ in tok).strip():
            lines.append(cur); cur, cur_w = [], 0.0
            if not ''.join(t for t, _ in tok).strip(): continue
        if not cur and not ''.join(t for t, _ in tok).strip(): continue
        cur.append(tok); cur_w += tw
    if cur: lines.append(cur)
    # orphan: pull the last token of the previous line down until the last line holds a word group
    while len(lines) > 1 and _is_orphan(_join(lines[-1])) and len(lines[-2]) > 1:
        lines[-1].insert(0, lines[-2].pop())
    out = []
    for ln in lines:
        r = _join(ln)
        if r and not keep_space: r[-1] = (r[-1][0].rstrip(), r[-1][1])
        if r: r[0] = (r[0][0].lstrip(), r[0][1])
        out.append([x for x in r if x[0]])
    return out or [[]]
