"""Actual Chromium failure rollback and retry; component boundary only."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--chromium',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=a.chromium);p=b.new_page()
 p.set_content('<main class="deck"><section id="a" class="slide is-active"></section><section id="b" class="slide"></section></main>')
 p.evaluate('''()=>{const Native=MutationObserver;window.obsLive=new Set();window.MutationObserver=class extends Native {observe(...a){super.observe(...a);obsLive.add(this)}disconnect(){super.disconnect();obsLive.delete(this)}}}''')
 p.add_script_tag(path=str(ROOT/'adapters/html-ppt-bridge.js'))
 initial=p.evaluate('''()=>{let disposed=[];const baseline=obsLive.size;try{KZHTMLPPT.bind(document.querySelector('.deck'),s=>{if(s.id==='b')throw Error('factory failure');return {enter(){},dispose(){disposed.push(s.id)}}})}catch(e){return {error:e.message,baseline,observers:obsLive.size,disposed}}}''')
 # New page isolates leaked observers in the red baseline from subsequent checks.
 p.close();p=b.new_page();p.set_content('<main class="deck"><section id="a" class="slide"></section></main>');p.add_script_tag(path=str(ROOT/'adapters/html-ppt-bridge.js'))
 retry=p.evaluate('''()=>{let enters=0;const d=document.querySelector('.deck'),s=d.firstElementChild;const bridge=KZHTMLPPT.bind(d,()=>({enter(){if(++enters===1)throw Error('enter failure')},dispose(){}}));s.classList.add('is-active');let error;try{bridge.sync()}catch(e){error=e.message};bridge.sync();const result={error,enters};bridge.dispose();return result}''')
 p.close();p=b.new_page();p.set_content('<main class="deck"><section id="a" class="slide"></section><section id="b" class="slide"></section></main>');p.add_script_tag(path=str(ROOT/'adapters/html-ppt-bridge.js'))
 cleanup=p.evaluate('''()=>{let disposed=[];const bridge=KZHTMLPPT.bind(document.querySelector('.deck'),s=>({dispose(){disposed.push(s.id);if(s.id==='a')throw Error('dispose failure')}}));let error;try{bridge.dispose()}catch(e){error=e.message};return {error,disposed}}''')
 p.close();p=b.new_page();p.set_content('<main class="deck"><section id="a" class="slide"></section><section id="b" class="slide"></section></main>');p.add_script_tag(path=str(ROOT/'adapters/html-ppt-bridge.js'))
 removed=p.evaluate('''()=>{let disposed=[];const d=document.querySelector('.deck'),bridge=KZHTMLPPT.bind(d,s=>({dispose(){disposed.push(s.id);if(s.id==='a')throw Error('remove dispose failure')}}));d.replaceChildren();let error;try{bridge.sync()}catch(e){error=e.message};const result={error,disposed:[...disposed]};bridge.dispose();return result}''')
 b.close()
checks={'failed_initialization_releases_observer_and_prior_components':initial['observers']==initial['baseline'] and initial['disposed']==['a'],'failed_enter_not_marked_active_and_can_retry':retry['enters']==2,'dispose_failure_does_not_leak_other_components':cleanup['disposed']==['a','b'],'removal_failure_still_releases_all_removed_components':removed['disposed']==['a','b']}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'scope':'owner real Chrome exceptional component boundary, not upstream/model acceptance','checks':checks,'initial':initial,'retry':retry,'cleanup':cleanup,'removed':removed},ensure_ascii=False,indent=2));print(json.dumps(checks));raise SystemExit(0 if all(checks.values()) else 1)
