#!/usr/bin/env python3
"""Numbered lists of a protocol .docx with their official numbers and levels (03 COPY-09).

Word numbering (1. 2. 3. …) and sub-items live in numbering.xml, not in the text: a docx → txt/md conversion keeps the
words and drops both, so criteria copied from the text end up renumbered, with stems dropped and sub-items merged into
one item or promoted to items of their own (OMP run2, 7.2.3: exclusion 1 swallowed its eight sub-items, the four
infection screens became items 10–13). This reader keeps the structure:

    python3 "$KZ_DIR/tools/protocol_lists.py" protocol.docx --from 排除标准 --key exclusion > excl.json
    python3 "$KZ_DIR/tools/protocol_lists.py" protocol.docx --from 入选标准 --outline

--from takes the numbered list under the heading with that text (the first one when the synopsis repeats it). Items are the list's top level
in protocol order (item n is protocol number n); a stem with sub-items becomes {"text": stem, "items": [...]}: the
sub-items are the protocol's second-level paragraphs, numbered or written by hand (（1）, ①, a)). The JSON is the
criteria data contract of tools/kz_layout.py; render it with --source protocol.docx, which checks numbers and levels
against the same reading. Standard library only."""
from pathlib import Path
import argparse, html, json, re, sys, zipfile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MANUAL = re.compile(r'^\s*(?:[（(]\s*\d+\s*[）)]|[①-⑳]|[a-zA-Z][.)）]|\d+[)）])')

def _text(p):
    """Visible text of one <w:p>: runs, tabs and breaks; deleted revisions (w:delText) and field codes are not text."""
    out = []
    for m in re.finditer(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:tab/>|<w:br/>|<w:sym [^>]*w:char="([0-9A-Fa-f]{4})"', p):
        if m.group(0).startswith('<w:tab') or m.group(0).startswith('<w:br'): out.append(' ')
        elif m.group(2): out.append(chr(int(m.group(2), 16)) if int(m.group(2), 16) < 0xF000 else '')
        else: out.append(html.unescape(m.group(1)))
    return ''.join(out).strip()

def _formats(z):
    """numId → {ilvl: (numFmt, lvlText, start)}."""
    try: x = z.read('word/numbering.xml').decode('utf-8')
    except KeyError: return {}
    abstract = {}
    for a in re.finditer(r'<w:abstractNum\b[^>]*w:abstractNumId="(\d+)"[^>]*>(.*?)</w:abstractNum>', x, re.S):
        lv = {}
        for l in re.finditer(r'<w:lvl\b[^>]*w:ilvl="(\d+)"[^>]*>(.*?)</w:lvl>', a.group(2), re.S):
            g = lambda tag, d: (re.search(rf'<w:{tag} w:val="([^"]*)"', l.group(2)) or [None, d])[1]
            lv[int(l.group(1))] = (g('numFmt', 'decimal'), g('lvlText', '%1.'), int(g('start', '1')))
        abstract[a.group(1)] = lv
    out = {}
    for n in re.finditer(r'<w:num\b[^>]*w:numId="(\d+)"[^>]*>(.*?)</w:num>', x, re.S):
        a = re.search(r'<w:abstractNumId w:val="(\d+)"', n.group(2))
        lv = dict(abstract.get(a.group(1), {})) if a else {}
        for o in re.finditer(r'<w:lvlOverride w:ilvl="(\d+)">(.*?)</w:lvlOverride>', n.group(2), re.S):
            s = re.search(r'<w:startOverride w:val="(\d+)"', o.group(2))
            if s and int(o.group(1)) in lv: f, t, _ = lv[int(o.group(1))]; lv[int(o.group(1))] = (f, t, int(s.group(1)))
        out[n.group(1)] = lv
    return out

def _label(fmt, text, n):
    if fmt == 'bullet' or fmt == 'none': return ''
    if fmt in ('lowerLetter', 'upperLetter'): v = chr(ord('a' if fmt == 'lowerLetter' else 'A') + (n - 1) % 26)
    elif fmt == 'decimalEnclosedCircle': v = chr(0x2460 + n - 1) if 1 <= n <= 20 else str(n)
    elif fmt in ('lowerRoman', 'upperRoman'): v = _roman(n) if fmt == 'upperRoman' else _roman(n).lower()
    else: v = str(n)
    return re.sub(r'%\d', v, text)

def _roman(n):
    out = ''
    for val, sym in ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                     (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')):
        while n >= val: out += sym; n -= val
    return out

def paragraphs(path):
    """→ [{'text', 'num': numId or None, 'ilvl', 'label'}] in document order (table cells included)."""
    z = zipfile.ZipFile(path); x = z.read('word/document.xml').decode('utf-8'); fm = _formats(z)
    count, out = {}, []
    for p in re.findall(r'<w:p[ >].*?</w:p>', x, re.S):
        ni = re.search(r'<w:numId w:val="(\d+)"', p); il = re.search(r'<w:ilvl w:val="(\d+)"', p)
        num = ni.group(1) if ni and ni.group(1) != '0' else None; ilvl = int(il.group(1)) if il else 0; label = ''
        if num:
            c = count.setdefault(num, {})
            for deeper in [k for k in c if k > ilvl]: del c[deeper]
            f, t, s = fm.get(num, {}).get(ilvl, ('decimal', f'%{ilvl + 1}.', 1))
            c[ilvl] = c.get(ilvl, s - 1) + 1; label = _label(f, t, c[ilvl])
        out.append({'text': _text(p), 'num': num, 'ilvl': ilvl, 'label': label})
    return out

def lists(path):
    """Numbered blocks: [{'start_at': paragraph index, 'items': [{'label', 'text', 'items': [{'label', 'text'}]}]}].
    The top level of a block is the numId and level of its first paragraph; other numbered paragraphs and hand-
    numbered paragraphs (（1） ① a)) under an item are its sub-items; any other text paragraph ends the block."""
    ps = paragraphs(path); blocks, cur, top = [], None, None
    for i, p in enumerate(ps):
        if not p['text']: continue
        if p['num'] and (cur is None):
            cur = {'start_at': i, 'items': []}; blocks.append(cur); top = (p['num'], p['ilvl'])
        if cur is None: continue
        if p['num'] and (p['num'], p['ilvl']) == top: cur['items'].append({'label': p['label'], 'text': p['text'], 'items': []})
        elif (p['num'] or MANUAL.match(p['text'])) and cur['items']: cur['items'][-1]['items'].append({'label': p['label'], 'text': p['text']})
        else: cur = None
    return ps, blocks

def data_items(block):
    """Block → criteria data: a plain item is its text, a stem with sub-items is {"text", "items"}."""
    return [it['text'] if not it['items'] else {'text': it['text'], 'items': [s['text'] for s in it['items']]} for it in block['items']]

def find_blocks(path, marker):
    """Every numbered list that starts within three text paragraphs after a short paragraph naming `marker` (a
    heading such as 排除标准 / 排除标准：; table-of-contents lines and running text do not count). A protocol usually
    has two: the synopsis and the body."""
    ps, blocks = lists(path); out = []
    for i, p in enumerate(ps):
        t = re.sub(r'^[\d.\s]+', '', p['text'])
        if not (t.startswith(marker) and len(t) <= len(marker) + 4 and not p['num']): continue
        near = [j for j in range(i + 1, len(ps)) if ps[j]['text']][:4]
        b = next((b for b in blocks if b['start_at'] in near), None)
        if b and b not in out: out.append(b)
    if not out: raise SystemExit(f'no numbered list follows a heading “{marker}” in {path}')
    return out

def docx_text(path):
    """Plain text of the document with list labels, one paragraph per line (the --source text for a .docx)."""
    return '\n'.join((p['label'] + ' ' if p['label'] else '') + p['text'] for p in paragraphs(path))

def outline(block):
    out = []
    for it in block['items']:
        out.append(f'{it["label"] or "•"} {it["text"]}')
        out += [f'    {s["label"] or "·"} {s["text"]}' for s in it['items']]
    return '\n'.join(out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('docx'); ap.add_argument('--from', dest='marker', required=True, help='text of the paragraph the list follows, e.g. 排除标准')
    ap.add_argument('--key', default='items', help='data key: inclusion / exclusion for the criteria template')
    ap.add_argument('--outline', action='store_true', help='print the numbered outline instead of JSON')
    a = ap.parse_args()
    found = find_blocks(a.docx, a.marker); b = found[0]
    if len(found) > 1:
        same = all(data_items(x) == data_items(b) for x in found[1:])
        print(f'note: {len(found)} lists follow “{a.marker}” (synopsis and body?): ' + ('identical' if same else
              'they differ — the first is used; check which one the protocol treats as binding'), file=sys.stderr)
    labels = [it['label'] for it in b['items']]
    if labels and labels != [f'{n}.' for n in range(1, len(labels) + 1)]:
        print(f'note: protocol numbers are {labels[:3]}…; the criteria template numbers from 1', file=sys.stderr)
    if a.outline: print(outline(b)); return 0
    print(json.dumps({a.key: data_items(b)}, ensure_ascii=False, indent=1))
    print(f'{a.key}: {len(b["items"])} items, {sum(1 for it in b["items"] if it["items"])} with sub-items', file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
