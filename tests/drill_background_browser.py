"""Actual modal isolation lifecycle; no simulated browser or model verdict."""
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright
a=argparse.ArgumentParser();a.add_argument('--output',required=True);o=a.parse_args()
R=Path(__file__).resolve().parents[1];out={}
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='chrome');p=b.new_page(viewport={'width':1728,'height':1031})
 p.set_content('<body class="kz"><header style="filter:brightness(.9)">保留样式</header><main><button id="open">查看明细</button><section id="source">后方密集信息</section><div id="host"></div></main><footer>后方页脚</footer></body>')
 for n in ['kz-tokens.css','kz-glass.css']:p.add_style_tag(path=str(R/'runtime'/n))
 p.add_style_tag(content='@keyframes source-drift{to{transform:translateX(1px)}}header{animation:source-drift 30s infinite alternate}')
 p.add_script_tag(path=str(R/'runtime/kz-drilldown.js'))
 out['nested']=p.evaluate('''()=>{window.d=new KZDrilldown.Drilldown({host:document.querySelector('#host')});openButton=document.querySelector('#open');openButton.focus();d.push({id:'one',title:'明细',render:c=>c.append(KZDrilldown.element('p',null,'弹窗正文保持清晰'))},openButton);const marked=[...document.querySelectorAll('.kz-drill-background')];return {roots:marked.map(x=>x.tagName+'#'+x.id),disjoint:marked.every(a=>marked.every(b=>a===b||!a.contains(b))),panelFilter:getComputedStyle(d.dialog).filter,insideMarked:!!d.dialog.closest('.kz-drill-background'),width:d.snapshot().width};}''')
 q=out['nested'];assert q['disjoint'] and not q['insideMarked'] and q['panelFilter']=='none' and q['width']>1728*.8,q
 out['backgroundAnimation']=p.evaluate('''()=>({play:getComputedStyle(document.querySelector('header')).animationPlayState,filter:getComputedStyle(document.querySelector('header')).filter,inline:document.querySelector('header').style.filter})''');assert out['backgroundAnimation']=={'play':'paused','filter':'blur(8px)','inline':'brightness(0.9)'},out
 out['layer']=p.evaluate('''()=>{const before=[...document.querySelectorAll('.kz-drill-background')];d.push({id:'two',title:'二级',render:c=>c.append(KZDrilldown.element('p',null,'二级正文'))});d.pop();return {same:before.every(x=>x.classList.contains('kz-drill-background')),depth:d.snapshot().depth};}''');assert out['layer']=={'same':True,'depth':1},out
 out['close']=p.evaluate('''()=>{d.close();return {remaining:document.querySelectorAll('.kz-drill-background').length,filter:document.querySelector('header').style.filter,focus:document.activeElement.id,overflow:document.body.style.overflow};}''');assert out['close']=={'remaining':0,'filter':'brightness(0.9)','focus':'open','overflow':''},out
 out['animationRestored']=p.evaluate('getComputedStyle(document.querySelector("header")).animationPlayState');assert out['animationRestored']=='running',out
 out['dispose']=p.evaluate('''()=>{d.push({id:'again',title:'明细',render:()=>{}});d.dispose();return {remaining:document.querySelectorAll('.kz-drill-background').length,dialog:document.querySelectorAll('dialog').length};}''');assert out['dispose']=={'remaining':0,'dialog':0},out
 out['ownership']=p.evaluate('''()=>{const h=document.querySelector('header');h.classList.add('kz-drill-background');const a=new KZDrilldown.Drilldown(),b=new KZDrilldown.Drilldown();a.push({id:'a',title:'甲',render:()=>{}});b.push({id:'b',title:'乙',render:()=>{}});a.close();const retained=document.querySelector('main').classList.contains('kz-drill-background');b.close();const released=!document.querySelector('main').classList.contains('kz-drill-background'),external=h.classList.contains('kz-drill-background');a.dispose();b.dispose();return {retained,released,external};}''');assert all(out['ownership'].values()),out
 out['scrollOwnership']=p.evaluate('''()=>{document.body.style.setProperty('overflow','scroll','important');const a=new KZDrilldown.Drilldown(),b=new KZDrilldown.Drilldown();a.push({id:'a',title:'甲',render:()=>{}});b.push({id:'b',title:'乙',render:()=>{}});a.close();const intermediate=document.body.style.overflow;b.close();const value=document.body.style.overflow,priority=document.body.style.getPropertyPriority('overflow');a.dispose();b.dispose();return {intermediate,value,priority};}''');assert out['scrollOwnership']=={'intermediate':'hidden','value':'scroll','priority':'important'},out
 b.close()
Path(o.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print('actual Chrome isolation/return/close/dispose/ownership passed')
