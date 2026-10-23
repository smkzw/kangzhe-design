/* Additive lifecycle bridge: never changes navigation, hashes or .is-active. */
(function(g){'use strict';
// 单一比率来源（7.0）：--kz-un = 布局视口高/参考高(720)，不钳制；--kz-u = 同一比率的长度（calc(var(--kz-un)*1px)）。
// 字号、几何、canvas 组件都乘同一个比率，矮视口（如 1080 屏 150% 缩放 ≈1280×610）整页等比缩小，文字不会比框大。
// 用 innerHeight（布局视口）而不是 visualViewport：捏合缩放应放大画面，而不是反向缩小字号。
// 打印期间是比率不变量：beforeprint 收回 1 并锁定，afterprint 解锁恢复。项目 CSS 不得另定义 --kz-u。
// 每次写入后广播 kz:fluidratio，canvas 组件（图表/甘特）据此重渲染，与 CSS 共用同一字号生命周期。
const doc=g.document;
let printing=false;
function fluidRef(){return (g.KZ_TOKENS&&g.KZ_TOKENS.wide&&g.KZ_TOKENS.wide.htmlppt_reference_height)||720;}
function writeRatio(v){const s=doc.documentElement.style;s.setProperty('--kz-un',String(v));s.setProperty('--kz-u',`calc(var(--kz-un) * 1px)`);g.dispatchEvent(new Event('kz:fluidratio'));}
// A hidden iframe or preview can report innerHeight 0: keep the variables defined (ratio 1) until a real resize.
function syncFluidRatio(){if(printing)return;const v=g.innerHeight/fluidRef();if(Number.isFinite(v)&&v>0)writeRatio(v);else if(!doc.documentElement.style.getPropertyValue('--kz-un'))writeRatio(1);}
function resetFluidRatio(){printing=true;writeRatio(1);}
function restoreFluidRatio(){printing=false;syncFluidRatio();}
syncFluidRatio();g.addEventListener('resize',syncFluidRatio);
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
