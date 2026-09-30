"""Real pointer dwell in an audience artifact; no synthetic event-only PASS."""
import argparse,json,hashlib,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--chromium',required=True);ap.add_argument('--url',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
report={'scope':'actual pointer dwell in given audience URL, not whole engine or model acceptance','url':a.url,'runs':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=a.chromium)
 for w,h in [(1280,720),(2560,1080)]:
  p=b.new_page(viewport={'width':w,'height':h});errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(a.url);p.wait_for_timeout(1200)
  targets=p.locator('.deck > .slide.is-active [data-kz-tilt]');rows=[]
  for i in range(targets.count()):
   el=targets.nth(i);r=el.bounding_box()
   if not r or not r['width'] or not r['height']:continue
   p.mouse.move(1,h-1);p.mouse.move(r['x']+r['width']*.5,r['y']+r['height']*.5);p.wait_for_timeout(80);p.mouse.move(r['x']+r['width']*.7,r['y']+r['height']*.4,steps=4)
   samples=[]
   for _ in range(6):
    p.wait_for_timeout(80);samples.append(el.evaluate('(e)=>({transform:e.style.transform,lightX:e.style.getPropertyValue("--kz-mx"),lightY:e.style.getPropertyValue("--kz-my")})'))
   p.mouse.move(1,h-1);p.wait_for_timeout(300);reset=el.evaluate('(e)=>({transform:e.style.transform,lightX:e.style.getPropertyValue("--kz-mx")})')
   angles=[float(x) for s in samples for x in re.findall(r'rotate[XY]\((-?[\d.]+)deg\)',s['transform'])]
   rows.append({'target':i,'samples':samples,'reset':reset,'held':all(s['lightX'] and s['lightY'] and 'perspective' in s['transform'] for s in samples),'angle_range_valid':bool(angles) and all(abs(v)<=10.00001 for v in angles),'reset_ok':not reset['transform'] and not reset['lightX']})
  report['runs'].append({'viewport':[w,h],'targets':rows,'errors':errors,'pass':bool(rows) and all(x['held'] and x['angle_range_valid'] and x['reset_ok'] for x in rows) and not errors});p.close()
 b.close()
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps([{'viewport':r['viewport'],'targets':len(r['targets']),'pass':r['pass']} for r in report['runs']]));raise SystemExit(0 if all(r['pass'] for r in report['runs']) else 1)
