"""Bind native text frames after a real ppt-master export; never creates a deck.
Fails closed on unmatched/duplicate text. Preserves all non-hero slide parts.
"""
from pathlib import Path
import argparse,json,zipfile,xml.etree.ElementTree as E,hashlib
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
for k,v in NS.items():E.register_namespace(k,v)
def norm(s):return ''.join(s.split())
def bind(src,dst,plan):
    if src.resolve()==dst.resolve():raise ValueError('Use a separate output; retain upstream original')
    changed={};receipt=[]
    with zipfile.ZipFile(src) as z:
      for page in plan['pages']:
        if not page.get('hero_layout_id'):continue
        index=int(page['id'].split('_')[0]);name=f'ppt/slides/slide{index}.xml';r=E.fromstring(z.read(name));used=set()
        for el in page['elements']:
          want=norm(el.get('text',''))
          if not want:continue
          matches=[s for s in r.findall('.//p:sp',NS) if norm(''.join(t.text or '' for t in s.findall('.//a:t',NS)))==want]
          if len(matches)!=1:raise ValueError(f'{name}: expected one native shape for {want!r}, got {len(matches)}')
          s=matches[0]
          sizes={int(v.get('sz')) for v in s.findall('.//a:rPr',NS) if v.get('sz')}
          if sizes!={round(el['font_px']*.75*100)}:raise ValueError(f'{name}: native font size differs from plan: {sizes}')
          if id(s) in used:raise ValueError('Duplicate role binding')
          used.add(id(s));xf=s.find('p:spPr/a:xfrm',NS);off=xf.find('a:off',NS);ext=xf.find('a:ext',NS);x,y,w,h=el['rect'];before={**off.attrib,**ext.attrib};off.set('x',str(round(x*9525)));off.set('y',str(round(y*9525)));ext.set('cx',str(round(w*9525)));ext.set('cy',str(round(h*9525)))
          tx=s.find('p:txBody',NS);bp=tx.find('a:bodyPr',NS)
          for key,val in {'lIns':'0','rIns':'0','tIns':'0','bIns':'0','anchor':'t','wrap':'square'}.items():bp.set(key,val)
          for child in list(bp):
            if child.tag.rsplit('}',1)[-1] in ['normAutofit','spAutoFit','noAutofit']:bp.remove(child)
          E.SubElement(bp,'{'+NS['a']+'}noAutofit')
          for para in tx.findall('a:p',NS):
            pp=para.find('a:pPr',NS)
            if pp is None:pp=E.Element('{'+NS['a']+'}pPr');para.insert(0,pp)
            for c in list(pp):
              if c.tag.rsplit('}',1)[-1] in ['lnSpc','spcBef','spcAft']:pp.remove(c)
            pp.set('algn','l')
            ln=E.Element('{'+NS['a']+'}lnSpc');pp.insert(0,ln);E.SubElement(ln,'{'+NS['a']+'}spcPts',{'val':str(round(el['font_px']*.75*el['line_height']*100))})
            for at,k in enumerate(['spcBef','spcAft'],1):
              space=E.Element('{'+NS['a']+'}'+k);E.SubElement(space,'{'+NS['a']+'}spcPts',{'val':'0'});pp.insert(at,space)
          receipt.append({'slide':index,'role':el['role'],'text':el['text'],'before':before,'rect_px':el['rect'],'font_px':el['font_px']})
        changed[name]=E.tostring(r,encoding='utf-8',xml_declaration=True)
      with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():out.writestr(info,changed.get(info.filename,z.read(info.filename)))
    return {'scope':'brand hero text-frame binding after upstream export','input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changed_parts':list(changed),'bindings':receipt}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('plan',type=Path);ap.add_argument('--receipt',type=Path,required=True);a=ap.parse_args();a.receipt.write_text(json.dumps(bind(a.input,a.output,json.loads(a.plan.read_text())),ensure_ascii=False,indent=2)+'\n')
