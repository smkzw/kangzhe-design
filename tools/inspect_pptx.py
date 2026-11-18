"""Read-only structural audit. Explicit XML fonts are not resolved theme fonts."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import argparse,json,xml.etree.ElementTree as E,re
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def inspect(path):
 with ZipFile(path) as z:
  slides=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda s:int(re.search(r'slide(\d+)',s).group(1)))
  out=[]
  for n in slides:
   root=E.fromstring(z.read(n));sizes=Counter(x.get('sz') for x in root.findall('.//a:rPr',NS) if x.get('sz'))
   out.append({'slide':n,'native_shapes':len(root.findall('.//p:sp',NS)),'pictures':len(root.findall('.//p:pic',NS)),'graphic_frames':len(root.findall('.//p:graphicFrame',NS)),'explicit_sizes_hundredth_pt':dict(sizes),'alpha_nodes':len(root.findall('.//a:alpha',NS))})
  return {'slide_count':len(slides),'slides':out,'chart_parts':len([n for n in z.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml',n)]),'embedded_workbooks':len([n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]),'scope':'structure only; does not prove visual quality, native edit readback, or effective theme fonts'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('pptx',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();s=json.dumps(inspect(a.pptx),ensure_ascii=False,indent=2);print(s)
 if a.out:a.out.write_text(s,encoding='utf-8')
