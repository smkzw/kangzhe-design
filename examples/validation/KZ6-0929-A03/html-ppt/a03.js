/* Additive wiring only: the upstream runtime owns all page navigation. */
(function(g){'use strict';
function ready(fn){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',fn):fn();}
ready(()=>{
 const ambientAbort=new AbortController(),ambientSignal=ambientAbort.signal;
 const deck=document.querySelector('.deck'),slides=[...deck.querySelectorAll(':scope > .slide')];
 const priorFrozen=document.body.dataset.kzFrozen,priorChrome=deck.dataset.chrome;
 const staticMode=document.body.dataset.preview==='1',mq=matchMedia('(prefers-reduced-motion: reduce)');
const pages=new Map();let chart,gantt,bridge,printing=false,disposed=false,published=null,priorGlobals=null;
function dispose(){
 if(disposed)return;disposed=true;const errors=[];
 const releases=[()=>ambientAbort.abort(),()=>bridge?.dispose(),()=>chart?.dispose(),()=>gantt?.dispose(),()=>document.body.classList.remove('kz-background-paused'),()=>{if(priorFrozen===undefined)delete document.body.dataset.kzFrozen;else document.body.dataset.kzFrozen=priorFrozen;},()=>{if(priorChrome===undefined)delete deck.dataset.chrome;else deck.dataset.chrome=priorChrome;}];
 if(published)for(const key of Object.keys(published))releases.push(()=>{const own=published[key];if(g[key]!==own)return;const prior=priorGlobals[key];if(prior===undefined)delete g[key];else g[key]=prior;});
 for(const release of releases){
  try{release();}catch(error){errors.push(error);}
 }
 if(errors.length)throw new AggregateError(errors,'演示组件清理失败');
}
 try{
 chart=KZCharts.mount(deck.querySelector('[data-kz-chart]'),KZ_DECK_DATA.chart);
 gantt=KZGantt.mount(deck.querySelector('[data-kz-gantt]'),KZ_DECK_DATA.gantt);
 function freeze(){const frozen=printing||staticMode||mq.matches;document.body.dataset.kzFrozen=String(frozen);if(frozen){for(const m of pages.values())m.finish();chart.finish();gantt.finish();}}
 bridge=KZHTMLPPT.bind(deck,slide=>{
  const motion=KZMotion.mountPage(slide);pages.set(slide,motion);
  return {enter(){deck.dataset.chrome=slide.dataset.chrome||'body';freeze();motion.enter();const n=slides.indexOf(slide)+1;
   if(staticMode){const c=deck.querySelector(':scope > .deck-footer .slide-number');c?.setAttribute('data-current',n);c?.setAttribute('data-total',slides.length);}
   if(slide.querySelector('[data-kz-chart]')){document.body.dataset.kzFrozen==='true'?chart.finish():chart.play();}
   if(slide.querySelector('[data-kz-gantt]')){gantt.resume();document.body.dataset.kzFrozen==='true'?gantt.finish():gantt.play();}
  },leave(){motion.leave();if(slide.querySelector('[data-kz-chart]'))chart.pause();if(slide.querySelector('[data-kz-gantt]'))gantt.pause();},dispose(){try{motion.dispose();}finally{pages.delete(slide);}}};
 });
 mq.addEventListener('change',freeze,{signal:ambientSignal});
 addEventListener('beforeprint',()=>{printing=true;freeze();},{signal:ambientSignal});addEventListener('afterprint',()=>{printing=false;freeze();},{signal:ambientSignal});
 function syncAmbient(){document.body.classList.toggle('kz-background-paused',document.hidden);if(document.hidden){chart.pause();gantt.pause();}}
 document.addEventListener('visibilitychange',syncAmbient,{signal:ambientSignal});syncAmbient();
 addEventListener('pagehide',dispose,{once:true,signal:ambientSignal});
 freeze();const instances={chart,gantt};
 priorGlobals={__kzInstances:g.__kzInstances,__kzMotionPages:g.__kzMotionPages,__kzBridge:g.__kzBridge,__kzDispose:g.__kzDispose};
 published={__kzInstances:instances,__kzMotionPages:pages,__kzBridge:bridge,__kzDispose:dispose};
 Object.assign(g,published);
 }catch(error){try{dispose();}catch(cleanup){throw new AggregateError([error,cleanup],'演示初始化及清理失败');}throw error;}
});})(window);
