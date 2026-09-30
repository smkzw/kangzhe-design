"""Real wall-clock page exit, remount and static lifecycle evidence."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--chrome',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();R=Path(__file__).resolve().parents[1];out={}
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=a.chrome);p=b.new_page();p.set_content('<div id=p><div id=t data-kz-reveal data-kz-tilt>普通页面完整可读</div></div>');p.add_script_tag(path=str(R/'runtime/kz-motion.js'))
 p.evaluate("window.life=KZMotion.mountPage(document.querySelector('#p'));window.duplicateRejected=false;try{KZMotion.mountPage(document.querySelector('#p'))}catch(e){duplicateRejected=/已有动态挂载/.test(e.message)};life.enter()");p.wait_for_timeout(480);out['entered']=p.evaluate("({opacity:getComputedStyle(document.querySelector('#t')).opacity,rejected:duplicateRejected})");assert out['entered']=={'opacity':'1','rejected':True},out
 p.evaluate('life.leave()');p.wait_for_timeout(330);out['exit']=p.evaluate("({opacity:getComputedStyle(document.querySelector('#t')).opacity,active:document.querySelector('#p').dataset.kzMotionActive})");assert out['exit']=={'opacity':'0','active':'false'},out
 p.evaluate('life.enter()');p.wait_for_timeout(480);out['reentry']=p.evaluate("getComputedStyle(document.querySelector('#t')).opacity");assert out['reentry']=='1',out
 p.evaluate('life.leave();life.enter()');p.wait_for_timeout(40);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(30);out['rm']=p.evaluate("({opacity:getComputedStyle(document.querySelector('#t')).opacity,animations:document.querySelector('#t').getAnimations().length})");assert out['rm']=={'opacity':'1','animations':0},out
 p.emulate_media(reduced_motion='no-preference');p.evaluate('life.enter()');p.wait_for_timeout(40);p.evaluate("dispatchEvent(new Event('beforeprint'))");out['print']=p.evaluate("({opacity:getComputedStyle(document.querySelector('#t')).opacity,animations:document.querySelector('#t').getAnimations().length})");assert out['print']=={'opacity':'1','animations':0},out
 out['remount']=p.evaluate("()=>{life.dispose();const n=KZMotion.mountPage(document.querySelector('#p'));const good=document.querySelector('#p').dataset.kzMotionMounted==='true';n.dispose();return good&&document.querySelector('#p').dataset.kzMotionMounted===undefined;}");assert out['remount'],out;b.close()
Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Actual wall-clock exit hold, reentry, RM/print settling and page ownership passed')
