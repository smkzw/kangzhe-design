"""Approved header mark, mechanically derived from the original native objects.

The native asset is authoritative. PPTX must use bind_header_mark_pptx after
ppt-master export: SVG conversion alone does not guarantee identical OOXML.
"""
from pathlib import Path
from html import escape
import hashlib,json,math,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1]
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}

def facets(prefix='kz',native=False):
    t=json.loads((R/'tokens/tokens.json').read_text())
    asset=R/t['chrome']['header_mark']['native_asset']
    if hashlib.sha256(asset.read_bytes()).hexdigest()!=t['chrome']['header_mark']['sha256']:
        raise ValueError('Approved mark asset hash mismatch')
    root=E.parse(asset).getroot();defs=[];parts=[];prefix=escape(prefix,quote=True)
    for i,s in enumerate(root.findall('p:sp',NS)):
        pr=s.find('p:spPr',NS); xf=pr.find('a:xfrm',NS)
        off=xf.find('a:off',NS); ext=xf.find('a:ext',NS)
        x,y=[int(off.get(k))/9525 for k in ('x','y')]; w,h=[int(ext.get(k))/9525 for k in ('cx','cy')]
        path=pr.find('a:custGeom/a:pathLst/a:path',NS);pw,ph=int(path.get('w')),int(path.get('h'));commands=[]
        for node in path:
            tag=node.tag.split('}')[-1]
            if tag=='close':commands.append('Z');continue
            if tag not in ('moveTo','lnTo'):raise ValueError('Unsupported approved path command')
            pt=node.find('a:pt',NS)
            commands.append(f'{"M" if tag=="moveTo" else "L"}{x+int(pt.get("x"))*w/pw:.7f},{y+int(pt.get("y"))*h/ph:.7f}')
        grad=pr.find('a:gradFill',NS);solid=pr.find('a:solidFill/a:srgbClr',NS);opacity=1
        if grad is not None:
            lin=grad.find('a:lin',NS)
            if lin.attrib!={'ang':'2700000','scaled':'1'}:raise ValueError('Unreviewed gradient direction')
            stops=[]
            for gs in grad.findall('a:gsLst/a:gs',NS):
                col=gs.find('a:srgbClr',NS);stops.append(f'<stop offset="{int(gs.get("pos"))/100000}" stop-color="#{col.get("val")}"/>')
            defs.append(f'<linearGradient id="{prefix}-gradient-{i}" x1="0" y1="0" x2="1" y2="1">'+''.join(stops)+'</linearGradient>')
            fill=f'url(#{prefix}-gradient-{i})'
        else:
            fill='#'+solid.get('val');alpha=solid.find('a:alpha',NS)
            if alpha is not None:opacity=int(alpha.get('val'))/100000
        effect='';shadow=pr.find('a:effectLst/a:outerShdw',NS)
        if shadow is not None:
            angle=int(shadow.get('dir'))/60000*math.pi/180;dist=int(shadow.get('dist'))/9525
            col=shadow.find('a:srgbClr',NS);alpha=int(col.find('a:alpha',NS).get('val'))/100000
            defs.append(f'<filter id="{prefix}-shadow-{i}" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB"><feDropShadow dx="{dist*math.cos(angle):.7f}" dy="{dist*math.sin(angle):.7f}" stdDeviation="{int(shadow.get("blurRad"))/9525/2:.7f}" flood-color="#{col.get("val")}" flood-opacity="{alpha}"/></filter>')
            effect=f' filter="url(#{prefix}-shadow-{i})"'
        parts.append(f'<path data-kz-source-shape="{s.find("p:nvSpPr/p:cNvPr",NS).get("name")}" data-pptx-role="decoration" d="{" ".join(commands)}" fill="{fill}" fill-opacity="{opacity}"{effect}/>')
    motion='' if native else ' class="kz-float"'
    return '<defs>'+''.join(defs)+'</defs>'+f'<g data-kz-header-mark="{t["chrome"]["header_mark"]["id"]}"{motion}>'+''.join(parts)+'</g>'

if __name__=='__main__':
    (R/'assets/header-mark/header-mark.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 90" aria-hidden="true">'+facets(native=True)+'</svg>\n')
