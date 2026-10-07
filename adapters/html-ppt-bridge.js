/* Additive lifecycle bridge: never changes navigation, hashes or .is-active. */
(function(g){'use strict';
// --kz-un：无单位流式比率（视口高/参考高720），供共享组件字号换算 calc(px * var(--kz-un))。
// --kz-u 是长度，仅用于几何 calc(99 * var(--kz-u))；px × --kz-u 为长度×长度，整条声明无效（6.1.1 修复）。
// 下限钳 1：窄高视口字号不缩（容量处置见 03），与 kz-charts/kz-gantt 一致；
// 打印期间是比率不变量：beforeprint 收回 1 并锁定，期间 resize/visualViewport 不再改写，afterprint 解锁恢复
// （内联样式压过作者样式表，不锁定则打印中一次 resize 即回到观看比率）。
// 每次写入后广播 kz:fluidratio，canvas 组件（图表/甘特）据此重渲染，与 CSS 共用同一字号生命周期。
const doc=g.document;
let printing=false;
function fluidRef(){return (g.KZ_TOKENS&&g.KZ_TOKENS.wide&&g.KZ_TOKENS.wide.htmlppt_reference_height)||720;}
function writeRatio(v){doc.documentElement.style.setProperty('--kz-un',String(v));g.dispatchEvent(new Event('kz:fluidratio'));}
function visibleHeight(){return (g.visualViewport&&g.visualViewport.height)||g.innerHeight;}
function syncFluidRatio(){if(printing)return;writeRatio(Math.max(1,visibleHeight()/fluidRef()));}
function resetFluidRatio(){printing=true;writeRatio(1);}
function restoreFluidRatio(){printing=false;syncFluidRatio();}
syncFluidRatio();g.addEventListener('resize',syncFluidRatio);
if(g.visualViewport)g.visualViewport.addEventListener('resize',syncFluidRatio);
g.addEventListener('beforeprint',resetFluidRatio);g.addEventListener('afterprint',restoreFluidRatio);
function bind(deck,factory){
 if(!deck||typeof factory!=='function')throw Error('需要现有 deck 与组件工厂');
 const states=new Map();let disposed=false;
 function sync(){if(disposed)return;
  // Upstream overview thumbnails clone .slide below an overview wrapper.
  // Only direct deck children own a live component lifecycle.
  for(const slide of deck.querySelectorAll(':scope > .slide')){
   let rec=states.get(slide);if(!rec){rec={life:factory(slide)||{},active:false};states.set(slide,rec);}
   const active=slide.classList.contains('is-active');
   if(active!==rec.active){active?rec.life.enter?.():rec.life.leave?.();rec.active=active;}
  }
  const errors=[];
  for(const [el,rec]of states)if(!el.isConnected||el.parentElement!==deck){states.delete(el);try{rec.life.dispose?.();}catch(error){errors.push(error);}}
  if(errors.length)throw new AggregateError(errors,'移除组件销毁失败');
 }
 const mo=new MutationObserver(sync);
 function dispose(){
  if(disposed)return;disposed=true;mo.disconnect();
  const records=[...states.values()],errors=[];states.clear();
  for(const r of records)try{r.life.dispose?.();}catch(error){errors.push(error);}
  if(errors.length)throw new AggregateError(errors,'组件销毁失败');
 }
 try{mo.observe(deck,{attributes:true,attributeFilter:['class'],subtree:true,childList:true});sync();}
 catch(error){try{dispose();}catch(cleanup){throw new AggregateError([error,cleanup],'页面初始化及清理失败');}throw error;}
 return {sync,dispose};
}
g.KZHTMLPPT={bind};
})(window);
