"""OOXML read-back of the delivered deck against the Kangzhe contract (hero frames, chart, motion, notes, glass)."""
import json
import re
import sys
import zipfile
from pathlib import Path

K = Path(__file__).resolve().parents[3]  # skill root (this file sits in examples/reference/pptx-default/)
T = json.loads((K / 'tokens/tokens.json').read_text())
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
EMU = 9525
slides = sorted([n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)], key=lambda s: int(re.findall(r'\d+', s)[0]))
out = {}


def frames(x):
    res = []
    for sp in re.findall(r'<p:sp>.*?</p:sp>', x, re.S):
        name = re.search(r'<p:cNvPr id="\d+" name="([^"]*)"', sp)
        off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)" ?/>\s*<a:ext cx="(\d+)" cy="(\d+)"', sp)
        texts = ''.join(re.findall(r'<a:t>([^<]*)</a:t>', sp))
        if off and texts:
            res.append({'name': name.group(1) if name else '', 'rect': [round(int(v) / EMU, 1) for v in off.groups()], 'text': texts[:40],
                        'sizes': sorted({int(s) / 100 for s in re.findall(r'sz="(\d+)"', sp)}),
                        'bullets': len(re.findall(r'<a:buChar', sp))})
    return res


hero = {1: ('cover', ['title', 'subtitle', 'meta']), 2: ('toc', ['title']), 6: ('ending', ['title', 'subtitle', 'meta'])}
for i, s in enumerate(slides, 1):
    x = z.read(s).decode('utf8')
    rec = {'frames': frames(x)}
    if i in hero:
        kind, keys = hero[i]
        lay = T['hero_layouts'][kind]
        checks = []
        for k in keys:
            want = lay[k]
            got = next((f for f in rec['frames'] if f['rect'][1] - 2 <= want[1] <= f['rect'][1] + f['rect'][3]), None)
            checks.append({'role': k, 'want': want, 'got': got and got['rect'], 'max_dev': got and max(abs(a - b) for a, b in zip(want, got['rect']))})
        rec['hero_frames'] = checks
    t = x[x.find('<p:timing'):] if '<p:timing' in x else ''
    rec['timing'] = [{'preset': p, 'subtype': st, 'delay': d} for p, st, d in
                     re.findall(r'presetID="(\d+)" presetClass="entr" presetSubtype="(\d+)"[^>]*>.*?<p:cond delay="(\d+)"', t, re.S)]
    rec['transition'] = re.findall(r'<p:transition[^>]*>.*?</p:transition>', x, re.S)[:1] and re.sub(r'\s+', ' ', re.findall(r'<p:transition[^>]*>.*?</p:transition>', x, re.S)[0])[:160]
    rec['charts'] = len(re.findall(r'<c:chart ', x))
    rec['shadow_alpha'] = sorted({int(a) / 1000 for a in re.findall(r'<a:outerShdw[^>]*>.*?<a:alpha val="(\d+)"', x, re.S)})
    rec['gradient_alpha'] = sorted({int(a) / 1000 for a in re.findall(r'<a:gs pos="\d+"><a:srgbClr val="FF[0-9A-F]{4}"><a:alpha val="(\d+)"', x)})
    rels = z.read(s.replace('slides/', 'slides/_rels/') + '.rels').decode('utf8')
    note = re.search(r'Target="\.\./notesSlides/(notesSlide\d+\.xml)"', rels)
    rec['notes_chars'] = len(''.join(re.findall(r'<a:t>([^<]*)</a:t>', z.read('ppt/notesSlides/' + note.group(1)).decode('utf8')))) if note else 0
    out[i] = rec
charts = [n for n in names if re.fullmatch(r'ppt/charts/chart\d+\.xml', n)]
for c in charts:
    cx = z.read(c).decode('utf8')
    out['chart:' + c] = {'type': re.findall(r'<c:(barChart|lineChart|areaChart)>', cx), 'barDir': re.findall(r'<c:barDir val="(\w+)"', cx),
                         'series': re.findall(r'<c:tx>.*?<c:v>([^<]*)</c:v>', cx, re.S), 'values': re.findall(r'<c:val>.*?</c:val>', cx, re.S) and
                         [re.findall(r'<c:v>([^<]*)</c:v>', v) for v in re.findall(r'<c:val>(.*?)</c:val>', cx, re.S)],
                         'colors': re.findall(r'<c:spPr><a:solidFill><a:srgbClr val="([0-9A-F]{6})"', cx)[:4], 'max': re.findall(r'<c:max val="([^"]+)"', cx), 'majorUnit': re.findall(r'<c:majorUnit val="([^"]+)"', cx)}
theme = z.read('ppt/theme/theme1.xml').decode('utf8')
out['fonts'] = {'latin': re.findall(r'<a:majorFont><a:latin typeface="([^"]*)"', theme), 'ea': re.findall(r'<a:majorFont>.*?<a:ea typeface="([^"]*)"', theme, re.S)}
print(json.dumps(out, ensure_ascii=False, indent=1))
