"""Normal-duration timer/identity observation; not a perceptual video review."""
from pathlib import Path
import json,sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inline_preview import inline_html
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--chromium',default='/usr/bin/chromium');a=ap.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=a.chromium,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(inline_html(ROOT/'examples/component-lab.html'));page.wait_for_function('!!window.KZ_LAB');page.wait_for_timeout(100)
  page.evaluate("""()=>{let f=KZ_LAB.film;f.seek(0);let old=f.onRender;window.cycleObservation={loops:0,frames:0,identity:true,previous:0,start:performance.now(),duration:f.duration};f.onRender=(state,p,ref)=>{let o=cycleObservation;o.frames++;o.identity=o.identity&&(ref.carrier===ref.identity)&&ref.carrier.isConnected;if(p<o.previous-.5)o.loops++;o.previous=p;old(state,p,ref);};f.resume('user');}""")
  page.wait_for_timeout(38000);res=page.evaluate('({...cycleObservation,elapsed:performance.now()-cycleObservation.start,snapshot:KZ_LAB.film.snapshot()})');res.update(errors=errors,scope='normal 36-second reference film timer and node identity; no independent video/perceptual review');a.out.write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps(res,ensure_ascii=False));b.close()
  sys.exit(0 if res['loops']>=1 and res['identity'] and not errors else 1)
