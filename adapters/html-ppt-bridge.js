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
