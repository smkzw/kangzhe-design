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
/* Scene stepping (06 MOTION-09): the presenter's next/previous inputs first go to the active slide's
   life.next()/prev(); only when that returns false (no scene left) do they reach upstream navigation.
   Upstream binds →/Space/PageDown/Enter, ←/PageUp/Backspace and horizontal swipes. ↑/↓ and vertical swipes
   are not bound upstream, so when no scene is left they are handed to it as →/←. Listeners sit in the window
   capture phase, ahead of upstream. Text fields, dialogs, the active slide's Gantt and upstream overlays keep their
   keys; a focused button or link keeps only Space and Enter (upstream pages on any target, so arrows still step). */
const NEXT=new Set(['ArrowRight','ArrowDown',' ','PageDown','Enter']),PREV=new Set(['ArrowLeft','ArrowUp','PageUp','Backspace']);
const UNBOUND={ArrowDown:'ArrowRight',ArrowUp:'ArrowLeft'};
const OWN='input,select,textarea,[contenteditable=""],[contenteditable="true"],dialog,[role="dialog"],.overview,.notes-overlay,[data-no-swipe]';
function sceneToken(k,d){const v=g.KZ_TOKENS&&g.KZ_TOKENS.motion&&g.KZ_TOKENS.motion.film&&g.KZ_TOKENS.motion.film.scene;return v&&Number.isFinite(v[k])?v[k]:d;}
function bind(deck,factory){
 if(!deck||typeof factory!=='function')throw Error('需要现有 deck 与组件工厂');
 const states=new Map();let disposed=false,activeIndex=-1,lastInput=-Infinity,forwarding=false;
 const abort=new AbortController(),on=(type,fn)=>g.addEventListener(type,fn,{capture:true,passive:type.startsWith('touch'),signal:abort.signal});
 function sync(){if(disposed)return;
  // Upstream overview thumbnails clone .slide below an overview wrapper.
  // Only direct deck children own a live component lifecycle.
  const slides=[...deck.querySelectorAll(':scope > .slide')];
  const cur=slides.findIndex(s=>s.classList.contains('is-active'));
  // Entering from a later slide shows the slide complete; an entry without a recent local input (presenter
  // window, deep link, first load) is unattended, so its scenes play through once (06 MOTION-09).
  const info={direction:cur<activeIndex?'backward':'forward',attended:performance.now()-lastInput<sceneToken('attended_window_ms',1200)};
  slides.forEach((slide,i)=>{
   let rec=states.get(slide);if(!rec){rec={life:factory(slide)||{},active:false};states.set(slide,rec);}
   const active=i===cur;
   if(active!==rec.active){active?rec.life.enter?.(info):rec.life.leave?.();rec.active=active;}
  });
  if(cur>=0)activeIndex=cur;
  const errors=[];
  for(const [el,rec]of states)if(!el.isConnected||el.parentElement!==deck){states.delete(el);try{rec.life.dispose?.();}catch(error){errors.push(error);}}
  if(errors.length)throw new AggregateError(errors,'移除组件销毁失败');
 }
 function step(dir){const rec=[...states.values()].find(r=>r.active),f=rec&&(dir>0?rec.life.next:rec.life.prev);return typeof f==='function'&&f.call(rec.life)===true;}
 function hand(key){forwarding=true;try{doc.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true}));}finally{forwarding=false;}}
 const owned=(t,key)=>t instanceof Element&&(!!t.closest(OWN)||!!(t.closest('.kz-gantt')&&t.closest('.slide.is-active'))||((key===' '||key==='Enter')&&!!t.closest('button,a[href]')));
 const blocked=()=>!!doc.querySelector('dialog[open],[aria-modal="true"],.overview.open');
 on('keydown',e=>{
  if(forwarding||e.defaultPrevented||e.isComposing||e.metaKey||e.ctrlKey||e.altKey)return;
  const dir=NEXT.has(e.key)?1:PREV.has(e.key)?-1:0;
  if(!dir)return;
  lastInput=performance.now();
  if(owned(e.target,e.key)||blocked())return;
  if(step(dir)){e.preventDefault();e.stopImmediatePropagation();return;}
  if(UNBOUND[e.key]){e.preventDefault();e.stopImmediatePropagation();hand(UNBOUND[e.key]);}
 });
 // Same gesture thresholds as upstream initTouchNav, plus the vertical axis.
 let touch=null;
 on('touchstart',e=>{touch=e.touches.length===1&&!owned(e.target)?{x:e.touches[0].clientX,y:e.touches[0].clientY,t:Date.now()}:null;});
 on('touchmove',e=>{if(e.touches.length>1)touch=null;});
 on('touchcancel',()=>{touch=null;});
 on('touchend',e=>{
  const s=touch,c=e.changedTouches&&e.changedTouches[0];touch=null;
  if(!s||!c||Date.now()-s.t>sceneToken('swipe_max_ms',800)||blocked())return;
  const dx=c.clientX-s.x,dy=c.clientY-s.y,min=sceneToken('swipe_min_px',50),ratio=sceneToken('swipe_ratio',1.5);
  const across=Math.abs(dx)>=min&&Math.abs(dx)>=Math.abs(dy)*ratio,down=Math.abs(dy)>=min&&Math.abs(dy)>=Math.abs(dx)*ratio;
  if(!across&&!down)return;
  const dir=(across?dx:dy)<0?1:-1;lastInput=performance.now();
  if(step(dir)){e.stopImmediatePropagation();return;}
  if(down)hand(dir>0?'ArrowRight':'ArrowLeft');
 });
 // Overview thumbnails and other clicks that navigate are local, attended inputs.
 on('click',()=>{lastInput=performance.now();});
 const mo=new MutationObserver(sync);
 function dispose(){
  if(disposed)return;disposed=true;mo.disconnect();abort.abort();
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
