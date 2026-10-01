"""Native-safe candidate SVG primitive for ppt-master authoring, not a PPTX engine.
Must still pass the installed upstream checker and target PowerPoint review.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
def card(x=80,y=120,w=540,h=420,title='材料参考'):
 t=json.loads((ROOT/'tokens/tokens.json').read_text());g=t['glass'];r=g['radius'];ink=t['colors']['ink']
 stops=''.join(f'<stop offset="{v["offset"]}" stop-color="{v["color"]}" stop-opacity="{v["alpha"]}"/>' for v in g['face_gradient'])
 return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
 <defs><linearGradient id="face" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient><filter id="shadow"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="{ink}" flood-opacity=".10"/></filter><linearGradient id="glint" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".95"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient></defs>
 <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#face)" stroke="{g['border_color']}" stroke-opacity="{g['border_alpha']}" stroke-width="1" filter="url(#shadow)"/>
 <path d="M{x+2} {y+r} Q{x+2} {y+2} {x+r} {y+2} L{x+w*.28} {y+2}" fill="none" stroke="url(#glint)" stroke-width="1.5"/>
 <text x="{x+24}" y="{y+52}" font-family="Microsoft YaHei" font-size="24" font-weight="700" fill="{ink}">{escape(title)}</text>
 </svg>'''
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();a.out.write_text(card(),encoding='utf-8')
