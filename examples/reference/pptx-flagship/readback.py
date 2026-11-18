"""OOXML read-back of the flagship deck: per-slide pictures, text frames, entrance timing, native charts and card shadows."""
import json
import re
import sys
import zipfile

z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
EMU = 9525
slides = sorted([n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)], key=lambda s: int(re.findall(r'\d+', s)[0]))
out = {}
for i, s in enumerate(slides, 1):
    x = z.read(s).decode('utf8')
    rels = z.read(s.replace('slides/', 'slides/_rels/') + '.rels').decode('utf8')
    frames = []
    for sp in re.findall(r'<p:sp>.*?</p:sp>', x, re.S):
        off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)" ?/>\s*<a:ext cx="(\d+)" cy="(\d+)"', sp)
        text = ''.join(re.findall(r'<a:t>([^<]*)</a:t>', sp))
        if off and text:
            frames.append({'rect': [round(int(v) / EMU, 1) for v in off.groups()], 'text': text[:40],
                           'sizes': sorted({int(v) / 100 for v in re.findall(r'sz="(\d+)"', sp)})})
    t = x[x.find('<p:timing'):] if '<p:timing' in x else ''
    out[i] = {
        'pictures': re.findall(r'<p:pic>.*?<p:cNvPr id="\d+" name="([^"]*)"', x, re.S),
        'media': sorted(set(re.findall(r'Target="\.\./media/([^"]+)"', rels))),
        'frames': frames,
        'timing': [{'preset': p, 'subtype': st, 'node': nt} for p, st, nt in
                   re.findall(r'presetID="(\d+)" presetClass="entr" presetSubtype="(\d+)"[^>]*nodeType="(\w+)"', t)],
        'clicks': t.count('nodeType="clickEffect"'),
        'charts': len(re.findall(r'<c:chart ', x)),
        'shadow_alpha': sorted({int(a) / 1000 for a in re.findall(r'<a:outerShdw[^>]*>.*?<a:alpha val="(\d+)"', x, re.S)}),
    }
for c in [n for n in names if re.fullmatch(r'ppt/charts/chart\d+\.xml', n)]:
    cx = z.read(c).decode('utf8')
    out['chart:' + c] = {'type': re.findall(r'<c:(barChart|lineChart|areaChart)>', cx),
                         'series': re.findall(r'<c:tx>.*?<c:v>([^<]*)</c:v>', cx, re.S),
                         'values': [re.findall(r'<c:v>([^<]*)</c:v>', v) for v in re.findall(r'<c:val>(.*?)</c:val>', cx, re.S)],
                         'colors': re.findall(r'<c:spPr><a:solidFill><a:srgbClr val="([0-9A-F]{6})"', cx)[:4]}
print(json.dumps(out, ensure_ascii=False, indent=1))
