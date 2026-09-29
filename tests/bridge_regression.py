"""Real Chromium DOM lifecycle checks; component coverage, not LLM evaluation."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def run(executable, output):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=executable)
        page = browser.new_page()
        page.set_content('<main class="deck"><section id="s1" class="slide is-active"></section><section id="s2" class="slide"></section><aside class="overview"><section id="clone" class="slide is-active"></section></aside></main><aside id="outside"></aside>')
        page.add_script_tag(content=(ROOT / 'adapters/html-ppt-bridge.js').read_text())
        page.evaluate('''() => {
          window.events=[];
          window.bridge=KZHTMLPPT.bind(document.querySelector('.deck'), slide=>{
            events.push(['create',slide.id]);
            return Object.fromEntries(['enter','leave','dispose'].map(kind=>[kind,()=>events.push([kind,slide.id])]));
          });
        }''')
        initial = page.evaluate('events.slice()')
        page.evaluate("document.querySelector('#s1').classList.remove('is-active'); document.querySelector('#s2').classList.add('is-active')")
        page.wait_for_function("events.some(x=>x[0]==='enter'&&x[1]==='s2')")
        page.evaluate("document.querySelector('#outside').append(document.querySelector('#s2')); bridge.sync()")
        moved = page.evaluate('events.slice()')
        page.evaluate('bridge.dispose()')
        final = page.evaluate('events.slice()')
        checks = {
            'overview_clone_never_created': not any(x[1]=='clone' for x in initial),
            'only_active_real_slide_enters': [x for x in initial if x[0]=='enter']==[['enter','s1']],
            'real_slide_transition': ['leave','s1'] in moved and ['enter','s2'] in moved,
            'connected_slide_moved_out_disposed': ['dispose','s2'] in moved,
            'each_real_component_disposed_once': all(final.count(['dispose',s])==1 for s in ['s1','s2']),
        }
        browser.close()
    result = {'scope':'real Chromium component DOM; no upstream engine or model claims','checks':checks,'initial':initial,'moved':moved,'final':final}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2))
    print(json.dumps(checks))
    return all(checks.values())

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--chromium',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raise SystemExit(0 if run(a.chromium,a.out) else 1)
