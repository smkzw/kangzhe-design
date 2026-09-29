"""Shared native-safe decorative fragments; ppt-master remains the exporter."""
from pathlib import Path
import json
T=json.loads((Path(__file__).resolve().parents[1]/'tokens/tokens.json').read_text())
def facets(prefix='kz',native=False):
 out=['<defs>']
 for name in ['orange','yellow']:
  colors=T['chrome']['facet_material'][name+'_stops'];out.append(f'<linearGradient id="{prefix}-{name}" x1="0" y1="0" x2="1" y2="1">'+''.join(f'<stop offset="{i/2}" stop-color="{c}" stop-opacity="{[.92,.86,.94][i]}"/>' for i,c in enumerate(colors))+'</linearGradient>')
 out.append(f'<filter id="{prefix}-shadow"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#67553D" flood-opacity=".12"/></filter></defs>')
 for i,name in enumerate(['yellow','orange']):
  pts=T['chrome']['facet_'+name];p=' '.join(f'{x},{y}' for x,y in pts);a,b,c,d=pts;depth=T['chrome']['facet_material']['depth_px']
  side=[b,c,[c[0]-depth,c[1]-depth],[b[0]-depth,b[1]+depth]]
  xs=[v[0] for v in pts];ys=[v[1] for v in pts]
  motion='' if native else f' class="kz-float" style="animation-delay:{-i*2.1}s"'
  out.append(f'<g id="{prefix}-{name}-group" data-pptx-role="decoration" data-pptx-bounds="{min(xs)} {min(ys)} {max(xs)-min(xs)} {max(ys)-min(ys)}" data-kz-facet="{name}"{motion}><polygon id="{prefix}-{name}-face" data-pptx-role="decoration" points="{p}" fill="url(#{prefix}-{name})" filter="url(#{prefix}-shadow)"/>')
  out.append(f'<polygon id="{prefix}-{name}-depth" data-pptx-role="decoration" points="'+ ' '.join(f'{x},{y}' for x,y in side)+'" fill="#A56D10" fill-opacity=".20"/>')
  out.append(f'<path id="{prefix}-{name}-glint" data-pptx-role="decoration" d="M{a[0]+1} {a[1]+1} L{b[0]-3} {b[1]+1} L{b[0]-6} {b[1]+7}" fill="none" stroke="#FFFFFF" stroke-opacity=".78" stroke-width="1"/></g>')
 return '\n'.join(out)
