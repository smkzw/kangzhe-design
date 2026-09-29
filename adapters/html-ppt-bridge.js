/* Additive lifecycle bridge: never changes navigation, hashes or .is-active. */
(function(g){'use strict';
function bind(deck,factory){
 if(!deck||typeof factory!=='function')throw Error('需要现有 deck 与组件工厂');
 const states=new Map();let disposed=false;
 function sync(){if(disposed)return;
  // Upstream overview thumbnails clone .slide below an overview wrapper.
  // Only direct deck children own a live component lifecycle.
  for(const slide of deck.querySelectorAll(':scope > .slide')){
   let rec=states.get(slide);if(!rec){rec={life:factory(slide)||{},active:false};states.set(slide,rec);}
   const active=slide.classList.contains('is-active');
   if(active!==rec.active){rec.active=active;active?rec.life.enter?.():rec.life.leave?.();}
  }
  for(const [el,rec]of states)if(!el.isConnected||el.parentElement!==deck){rec.life.dispose?.();states.delete(el);}
 }
 const mo=new MutationObserver(sync);mo.observe(deck,{attributes:true,attributeFilter:['class'],subtree:true,childList:true});sync();
 return {sync,dispose(){disposed=true;mo.disconnect();for(const r of states.values())r.life.dispose?.();states.clear();}};
}
g.KZHTMLPPT={bind};
})(window);
