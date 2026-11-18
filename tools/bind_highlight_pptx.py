#!/usr/bin/env python3
"""Bind inline emphasis in an exported PPTX (03 COPY-04, tokens.emphasis):
- ==highlight==: ppt-master has no highlight run, so pages write highlighted runs in the sentinel colour
  emphasis.highlight.marker; each such run becomes ink text with a native <a:highlight> fill (emphasis.highlight.fill).
- __underline__: exported as u="sng" in the text colour; each underlined run gets the token underline colour
  (<a:uFill>, emphasis.underline.color), as the HTML tracks draw it.
Slides, layouts and masters are scanned.

    python tools/bind_highlight_pptx.py in.pptx out.pptx [--receipt highlight-binding.json]
"""
from pathlib import Path
import argparse, json, re, sys, zipfile

ROOT = Path(__file__).resolve().parents[1]
TOK = json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))
MARK = TOK['emphasis']['highlight']['marker'].lstrip('#').upper()
FILL = TOK['emphasis']['highlight']['fill'].lstrip('#').upper()
INK = TOK['colors']['ink'].lstrip('#').upper()
ULINE = TOK['emphasis']['underline']['color'].lstrip('#').upper()
_AFTER_UFILL = ('a:latin', 'a:ea', 'a:cs', 'a:sym', 'a:hlinkClick', 'a:hlinkMouseOver', 'a:rtl', 'a:extLst')
# CT_TextCharacterProperties child order: ln, fill, effect, highlight, uLnTx|uLn, uFillTx|uFill, latin, ea, cs, sym, hlink…
_AFTER_HIGHLIGHT = ('a:uLnTx', 'a:uLn', 'a:uFillTx', 'a:uFill', 'a:latin', 'a:ea', 'a:cs', 'a:sym', 'a:hlinkClick', 'a:hlinkMouseOver', 'a:rtl', 'a:extLst')
_RPR = re.compile(r'<a:(rPr|endParaRPr|defRPr)\b([^>]*?)(/>|>(.*?)</a:\1>)', re.S)

def bind_xml(xml):
    """→ (xml, highlighted runs, underline colours set)."""
    n = u = 0
    def fix(m):
        nonlocal n, u
        tag, attrs, close, inner = m.group(1), m.group(2), m.group(3), m.group(4)
        hl = inner is not None and re.search(r'<a:solidFill>\s*<a:srgbClr val="' + MARK + r'"', inner, re.I)
        ul = re.search(r'\bu="(?!none)[a-zA-Z]+"', attrs) and tag == 'rPr' and not (inner and '<a:uFill' in inner)
        if not hl and not ul: return m.group(0)
        inner = inner or ''
        if hl:
            inner = re.sub(r'(<a:solidFill>\s*<a:srgbClr val=")' + MARK + '"', r'\g<1>' + INK + '"', inner, count=1, flags=re.I)
            inner = re.sub(r'<a:highlight>.*?</a:highlight>', '', inner, flags=re.S)
            cut = min([i for i in (inner.find('<' + t) for t in _AFTER_HIGHLIGHT) if i >= 0] + [len(inner)])
            inner = inner[:cut] + f'<a:highlight><a:srgbClr val="{FILL}"/></a:highlight>' + inner[cut:]; n += 1
        if ul:
            cut = min([i for i in (inner.find('<' + t) for t in _AFTER_UFILL) if i >= 0] + [len(inner)])
            inner = inner[:cut] + f'<a:uFill><a:solidFill><a:srgbClr val="{ULINE}"/></a:solidFill></a:uFill>' + inner[cut:]; u += 1
        return f'<a:{tag}{attrs}>{inner}</a:{tag}>'
    return _RPR.sub(fix, xml), n, u

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--receipt')
    a = ap.parse_args()
    data, receipt, ureceipt = {}, {}, {}
    with zipfile.ZipFile(a.src) as z:
        infos = z.infolist()
        for i in infos: data[i.filename] = z.read(i.filename)
    for name, raw in data.items():
        if re.match(r'ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml$', name):
            xml, n, u = bind_xml(raw.decode('utf-8'))
            if n or u: data[name] = xml.encode('utf-8')
            if n: receipt[name] = n
            if u: ureceipt[name] = u
    tmp = Path(a.dst).with_suffix('.tmp.pptx')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for i in infos: z.writestr(i, data[i.filename])
    tmp.replace(a.dst)
    left = sum(len(re.findall(r'<a:srgbClr val="' + MARK + '"', d.decode('utf-8', 'ignore'), re.I)) for k, d in data.items() if k.startswith('ppt/slides/'))
    out = {'source': a.src, 'output': a.dst, 'bound_runs': receipt, 'total': sum(receipt.values()), 'underline_colour_runs': ureceipt, 'sentinel_left_on_slides': left}
    if a.receipt: Path(a.receipt).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))
    return 1 if left else 0

if __name__ == '__main__':
    sys.exit(main())
