/* Additive wiring only: the upstream runtime owns all page navigation. */
(function(g){'use strict';
function ready(fn){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',fn):fn();}
ready(()=>{
 const deck=document.querySelector('.deck'),slides=[...deck.querySelectorAll(':scope > .slide')];
 const staticMode=document.body.dataset.preview==='1',mq=matchMedia('(prefers-reduced-motion: reduce)');
 const chart=KZCharts.mount(deck.querySelector('[data-kz-chart]'),KZ_DECK_DATA.chart);
 const gantt=KZGantt.mount(deck.querySelector('[data-kz-gantt]'),KZ_DECK_DATA.gantt);
 const pages=new Map();let printing=false;
 function freeze(){const frozen=printing||staticMode||mq.matches;document.body.dataset.kzFrozen=String(frozen);if(frozen){for(const m of pages.values())m.finish();chart.finish();gantt.finish();}}
 const bridge=KZHTMLPPT.bind(deck,slide=>{
  const motion=KZMotion.mountPage(slide);pages.set(slide,motion);
  return {enter(){deck.dataset.chrome=slide.dataset.chrome||'body';freeze();motion.enter();const n=slides.indexOf(slide)+1;
   if(staticMode){const c=deck.querySelector(':scope > .deck-footer .slide-number');c?.setAttribute('data-current',n);c?.setAttribute('data-total',slides.length);}
   if(slide.querySelector('[data-kz-chart]')){document.body.dataset.kzFrozen==='true'?chart.finish():chart.play();}
   if(slide.querySelector('[data-kz-gantt]')){gantt.resume();document.body.dataset.kzFrozen==='true'?gantt.finish():gantt.play();}
  },leave(){motion.leave();if(slide.querySelector('[data-kz-chart]'))chart.pause();if(slide.querySelector('[data-kz-gantt]'))gantt.pause();},dispose(){motion.dispose();pages.delete(slide);}};
 });
 mq.addEventListener('change',freeze);
 addEventListener('beforeprint',()=>{printing=true;freeze();});addEventListener('afterprint',()=>{printing=false;freeze();});
 document.addEventListener('visibilitychange',()=>{document.body.classList.toggle('kz-background-paused',document.hidden);if(document.hidden){chart.pause();gantt.pause();}});
 freeze();g.__kzInstances={chart,gantt};g.__kzMotionPages=pages;g.__kzBridge=bridge;
});})(window);
