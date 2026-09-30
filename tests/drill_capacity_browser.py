"""Real dialog geometry: short content, long overflow, path and focus return."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
a=argparse.ArgumentParser();a.add_argument('--chrome',required=True);a.add_argument('--output',required=True);o=a.parse_args()
R=Path(__file__).resolve().parents[1];out={}
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=o.chrome);p=b.new_page(viewport={'width':2560,'height':1080});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.set_content('<main class=kz><button id=open>查看明细</button></main>')
    for n in ['kz-tokens.css','kz-glass.css']:p.add_style_tag(path=str(R/'runtime'/n))
    p.add_script_tag(path=str(R/'runtime/kz-drilldown.js'))
    out['short']=p.evaluate('''()=>{window.d=new KZDrilldown.Drilldown({host:document.querySelector('main')});const t=document.querySelector('#open');t.focus();d.push({id:'a',title:'章节明细',render:c=>{const n=document.createElement('p');n.textContent='保留源件标识与核对位置。';c.append(n)}},t);const r=d.dialog.getBoundingClientRect(),f=d.dialog.firstChild.getBoundingClientRect();return {width:r.width,height:r.height,frame:f.height,crumb:getComputedStyle(d.crumb).display};}''')
    s=out['short'];assert s['width']>=2560*.8 and s['height']<300 and abs(s['height']-s['frame'])<=3 and s['crumb']=='none',s
    out['long']=p.evaluate('''()=>{d.push({id:'b',title:'记录列表',render:c=>{for(let i=0;i<90;i++){const p=document.createElement('p');p.textContent='记录'+i+' 源件标识、核对位置及待确认项。';c.append(p)}}});const r=d.dialog.getBoundingClientRect(),h=d.title.getBoundingClientRect();d.body.scrollTop=1000;return {height:r.height,scroll:d.body.scrollTop,overflow:d.body.scrollHeight>d.body.clientHeight,headStable:d.title.getBoundingClientRect().top===h.top,crumb:getComputedStyle(d.crumb).display};}''')
    l=out['long'];assert l['height']<=1080*.94+2 and l['scroll']>0 and l['overflow'] and l['headStable'] and l['crumb']!='none',l
    out['return']=p.evaluate('''()=>{d.pop();const hidden=getComputedStyle(d.crumb).display==='none';d.close();return {hidden,focus:document.activeElement.id,overflow:document.body.style.overflow};}''')
    assert out['return']=={'hidden':True,'focus':'open','overflow':''},out
    out['errors']=errors;assert not errors,errors;b.close()
Path(o.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print('actual short/long dialog, scroll, path and focus passed')
