"""Real native browser keyboard events, shared Gantt component only."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--chrome',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();R=Path(__file__).resolve().parents[1];out={}
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=a.chrome);p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.set_content('<style>.kz-gantt-plot{width:800px;height:400px}</style><div class=kz><div id=gantt></div></div><div id=outside tabindex=0>正常演示</div>')
 for name in ['assets/vendor/echarts.min.js','runtime/kz-tokens.js','runtime/kz-gantt.js']:p.add_script_tag(path=str(R/name))
 p.evaluate("window.g=KZGantt.mount(document.querySelector('#gantt'),{min:8104,max:8116,tasks:[{id:'t1',label:'资料整理',start:8105,end:8108}]});window.nav=0;window.clicks=0;document.addEventListener('keydown',e=>{if(['ArrowRight','Enter',' '].includes(e.key))nav++});document.querySelector('button').addEventListener('click',()=>clicks++);window.selectEvents=[];document.querySelector('#gantt').addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')selectEvents.push({key:e.key,defaultPrevented:e.defaultPrevented});});")
 p.get_by_role('button',name='应用时间',exact=True).focus();p.keyboard.press('Enter');p.wait_for_timeout(60);out['enter']=p.evaluate('({nav,clicks})');assert out['enter']=={'nav':0,'clicks':1},out
 p.keyboard.press('Space');p.wait_for_timeout(60);out['space']=p.evaluate('({nav,clicks})');assert out['space']=={'nav':0,'clicks':2},out
 p.get_by_label('开始季度',exact=True).focus();old=p.get_by_label('开始季度',exact=True).input_value();p.keyboard.press('ArrowDown');p.keyboard.press('ArrowDown');p.keyboard.press('Enter');out['select']=dict(before=old,after=p.get_by_label('开始季度',exact=True).input_value(),nav=p.evaluate('nav'),events=p.evaluate('selectEvents'));assert out['select']['nav']==0 and out['select']['events'] and all(not e['defaultPrevented'] for e in out['select']['events']),out
 p.locator('.kz-gantt-plot').focus();p.keyboard.press('ArrowRight');out['plot']=p.evaluate('({nav,data:g.getData()})');assert out['plot']['nav']==0 and out['plot']['data']['tasks'][0]['start']==8106,out
 p.locator('#outside').focus();p.keyboard.press('ArrowRight');out['outside']=p.evaluate('nav');assert out['outside']==1,out
 out['pageerrors']=errors;assert not errors,errors;b.close()
Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Real Enter/Space preserve native button activation; editor and plot isolate keys; outside navigation preserved')
