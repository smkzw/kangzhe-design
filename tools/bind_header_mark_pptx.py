"""Copy approved native header objects after a real ppt-master export.
Explicit page/shape IDs only; no new deck, no replacement of clinical content.
"""
from pathlib import Path
from xml.dom import minidom as D
import argparse,hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
def nodes(n,ns,name):return n.getElementsByTagNameNS(ns,name)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def signature(node):
    n=node.cloneNode(True)
    for v in nodes(n,P,'cNvPr'):v.removeAttribute('id')
    def walk(v):
        if v.nodeType==v.ELEMENT_NODE:
            attrs=sorted((a.namespaceURI,a.localName,a.value) for a in v.attributes.values() if a.namespaceURI!='http://www.w3.org/2000/xmlns/')
            return [v.namespaceURI,v.localName,attrs,[walk(c) for c in v.childNodes if c.nodeType==c.ELEMENT_NODE or (c.nodeType==c.TEXT_NODE and c.data.strip())]]
        return v.data
    return hashlib.sha256(json.dumps(walk(n),sort_keys=True).encode()).hexdigest()
def bind(src,dst,plan):
    src,dst=Path(src),Path(dst)
    if src.resolve()==dst.resolve():raise ValueError('Retain the upstream original; use a separate output')
    token=json.loads((R/'tokens/tokens.json').read_text())['chrome']['header_mark'];asset=R/token['native_asset']
    if digest(asset)!=token['sha256']:raise ValueError('Approved asset hash mismatch')
    approved=list(nodes(D.parse(str(asset)),P,'sp'));changed={};records=[]
    if not plan.get('pages'):raise ValueError('Explicit page bindings required')
    with zipfile.ZipFile(src) as z:
        size=nodes(D.parseString(z.read('ppt/presentation.xml')),P,'sldSz')[0]
        if (size.getAttribute('cx'),size.getAttribute('cy'))!=('12192000','6858000'):raise ValueError('Requires the approved 1280 x 720 canvas')
        for page in plan['pages']:
            index=int(page['slide']);part=f'ppt/slides/slide{index}.xml'
            if part in changed:raise ValueError('Duplicate page binding')
            ids={str(v) for v in page['replace_shape_ids']}
            if not ids:raise ValueError('Explicit replacement shape IDs required')
            doc=D.parseString(z.read(part));tree=nodes(doc,P,'spTree')[0]
            chosen=[]
            for n in nodes(tree,P,'sp'):
                if nodes(n,P,'cNvPr')[0].getAttribute('id') not in ids:continue
                if any(t.firstChild and t.firstChild.data.strip() for t in nodes(n,A,'t')):raise ValueError('Refuse to replace text')
                if nodes(n,A,'hlinkClick'):raise ValueError('Refuse to replace linked objects')
                xf=nodes(n,A,'xfrm')[0];off=nodes(xf,A,'off')[0];ext=nodes(xf,A,'ext')[0]
                x,y=int(off.getAttribute('x')),int(off.getAttribute('y'));w,h=int(ext.getAttribute('cx')),int(ext.getAttribute('cy'))
                if min(x,y,w,h)<0 or x+w>100*9525 or y+h>90*9525:raise ValueError('Replacement outside approved header-mark bounds')
                chosen.append(n)
            if len(chosen)!=len(ids):raise ValueError('Missing, duplicated or non-shape replacement IDs')
            parent=chosen[0].parentNode
            if any(n.parentNode is not parent for n in chosen):raise ValueError('Replacement objects must share one parent')
            ancestor=parent
            while ancestor is not tree:
                if ancestor.namespaceURI!=P or ancestor.localName!='grpSp':raise ValueError('Unsupported parent')
                prop=next(c for c in ancestor.childNodes if c.nodeType==c.ELEMENT_NODE and c.localName=='grpSpPr')
                xforms=nodes(prop,A,'xfrm')
                if xforms:
                    xf=xforms[0]
                    if any(xf.getAttribute(k) not in ('','0','false') for k in ('rot','flipH','flipV')):raise ValueError('Transformed group would alter approved geometry')
                    for first,second,keys in [('off','chOff',('x','y')),('ext','chExt',('cx','cy'))]:
                        one=nodes(xf,A,first);two=nodes(xf,A,second)
                        if len(one)!=1 or len(two)!=1 or any(one[0].getAttribute(k)!=two[0].getAttribute(k) for k in keys):raise ValueError('Non-identity group would alter approved geometry')
                ancestor=ancestor.parentNode
            for element in doc.getElementsByTagName('*'):
                if element.getAttribute('spid') in ids or element.getAttribute('spId') in ids or (element.localName in ('stCxn','endCxn') and element.getAttribute('id') in ids):
                    raise ValueError('Replacement objects have animation/connector references; remove mark-only references explicitly upstream first')
            nextid=max(int(n.getAttribute('id')) for n in nodes(doc,P,'cNvPr'))+1
            new=[]
            for n in approved:
                copy=doc.importNode(n,True);nodes(copy,P,'cNvPr')[0].setAttribute('id',str(nextid));nextid+=1
                parent.insertBefore(copy,chosen[0]);new.append(copy)
            for n in chosen:parent.removeChild(n)
            if [signature(n) for n in new]!=[signature(n) for n in approved]:raise ValueError('Native copy verification failed')
            changed[part]=doc.toxml(encoding='UTF-8');records.append({'slide':index,'removed_ids':sorted(ids),'native_shape_ids':[nodes(n,P,'cNvPr')[0].getAttribute('id') for n in new],'native_signatures':[signature(n) for n in new]})
        with zipfile.ZipFile(dst,'w') as out:
            for info in z.infolist():out.writestr(info,changed.get(info.filename,z.read(info.filename)))
    return {'scope':'approved native brand objects copied after ppt-master export; not an exporter','input_sha256':digest(src),'output_sha256':digest(dst),'asset_sha256':digest(asset),'changed_parts':list(changed),'bindings':records}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('plan',type=Path);ap.add_argument('--receipt',type=Path,required=True);v=ap.parse_args();v.receipt.write_text(json.dumps(bind(v.input,v.output,json.loads(v.plan.read_text())),ensure_ascii=False,indent=2)+'\n')
