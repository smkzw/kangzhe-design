/* Rich drilldown: one modal, persistent layer stack, no untrusted innerHTML. */
(function(global){
  'use strict';let serial=0;
  const backgroundOwners=new WeakMap();
  const scrollOwners=new WeakMap();
  function lockScroll(){
    const body=document.body;let rec=scrollOwners.get(body);
    if(!rec){rec={count:0,value:body.style.getPropertyValue('overflow'),priority:body.style.getPropertyPriority('overflow')};scrollOwners.set(body,rec);body.style.setProperty('overflow','hidden',rec.priority);}
    rec.count++;
    return ()=>{if(--rec.count)return;scrollOwners.delete(body);if(body.style.getPropertyValue('overflow')==='hidden'&&body.style.getPropertyPriority('overflow')===rec.priority){if(rec.value)body.style.setProperty('overflow',rec.value,rec.priority);else body.style.removeProperty('overflow');}};
  }
  function isolateBackground(dialog){
    const roots=[];let path=dialog;
    // Disjoint siblings along the ancestor path: never blur the reading panel
    // or nest filters. Native ::backdrop blur can be advertised but not painted.
    while(path.parentElement){
      const parent=path.parentElement;
      for(const node of parent.children){
        if(node===path||['DIALOG','SCRIPT','STYLE','LINK','TEMPLATE','NOSCRIPT'].includes(node.tagName))continue;
        let rec=backgroundOwners.get(node);
        if(!rec){rec={count:0,added:!node.classList.contains('kz-drill-background')};backgroundOwners.set(node,rec);}
        rec.count++;node.classList.add('kz-drill-background');roots.push(node);
      }
      if(parent===document.body)break;path=parent;
    }
    return ()=>{for(const node of roots){const rec=backgroundOwners.get(node);if(!rec)continue;if(--rec.count===0){if(rec.added)node.classList.remove('kz-drill-background');backgroundOwners.delete(node);}}};
  }
  function element(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!=null)el.textContent=text;return el;}
  class Drilldown {
    constructor({host=document.body,onOpen=()=>{},onClose=()=>{}}={}){
      this.host=host;this.stack=[];this.onOpen=onOpen;this.onClose=onClose;this.abort=new AbortController();this.disposed=false;
      this.dialog=element('dialog','kz-dialog kz-interactive');this.dialog.dataset.kzDialogId=String(++serial);
      // Host is inside .kz (or itself .kz); one design scope, no global CSS collision.
      const frame=element('div','kz-dialog-frame'),head=element('header','kz-dialog-head');
      this.back=element('button','kz-button','返回');this.back.type='button';
      this.title=element('h2',null,'详细信息');this.title.id='kz-dialog-title-'+serial;this.title.tabIndex=-1;
      this.closeButton=element('button','kz-button','关闭');this.closeButton.type='button';
      head.append(this.back,this.title,this.closeButton);this.crumb=element('nav','kz-breadcrumb');this.crumb.setAttribute('aria-label','信息层级');
      this.body=element('div','kz-dialog-body');frame.append(head,this.crumb,this.body);this.dialog.append(frame);host.append(this.dialog);
      this.dialog.setAttribute('aria-labelledby',this.title.id);
      const signal=this.abort.signal;
      this.back.addEventListener('click',()=>this.pop(),{signal});this.closeButton.addEventListener('click',()=>this.close(),{signal});
      this.dialog.addEventListener('cancel',e=>{e.preventDefault();this.pop();},{signal});
      // DRILL-03/04 隔离：阻止冒泡不影响按钮原生 Enter/Space 激活（默认动作在目标自身，不依赖冒泡路径）。
      this.dialog.addEventListener('keydown',e=>{
        // 宿主快捷键（翻页、S/O/F/A 等单字母键）一律不出弹层；原生默认动作（Esc→cancel、按钮激活）不受影响。
        e.stopPropagation();
        if(e.key==='Tab'){
          // 候选集须是实际可聚焦节点：:disabled 覆盖禁用 fieldset 后代，排除 inert 子树与不可见节点
          const items=[...this.dialog.querySelectorAll('button,a[href],input,select,textarea,[tabindex]')].filter(el=>{
            if(el.matches(':disabled')||el.closest('[inert]')||el.tabIndex<0)return false;
            const s=getComputedStyle(el);
            return s.visibility!=='hidden'&&s.display!=='none'&&el.getClientRects().length>0;
          });
          if(!items.length)return;
          const first=items[0],last=items[items.length-1],active=document.activeElement;
          if(!this.dialog.contains(active)){e.preventDefault();first.focus();}
          else if(!items.includes(active)){e.preventDefault();(e.shiftKey?last:first).focus();}
          else if(e.shiftKey&&active===first){e.preventDefault();last.focus();}
          else if(!e.shiftKey&&active===last){e.preventDefault();first.focus();}
        }
      },{signal});
      // DRILL-04 冒泡阶段滚轮路由：Y 与 X 各自找指针之下、沿该方向仍可滚动的最近滚动体；
      // 横向命中不吞纵向增量（触控板单事件常带两个分量）；两端或滚动体外一律消费，
      // 不链滚背景、不触发翻页。触控走原生滚动，横向滚动壳的 overscroll-behavior 陷阱见 07 DRILL-04。
      this.dialog.addEventListener('wheel',e=>{
        // 子控件已取消默认动作时不再路由滚动，但事件仍不得出弹层（隔离不依赖宿主另查 defaultPrevented）。
        if(e.defaultPrevented){e.stopPropagation();return;}
        const origin=e.target instanceof Element?e.target:e.target&&e.target.parentElement;
        // 页模式按轴取分母：Y 用视口高、X 用视口宽。
        const modeY=e.deltaMode===1?16:e.deltaMode===2?global.innerHeight:1;
        const modeX=e.deltaMode===1?16:e.deltaMode===2?global.innerWidth:1;
        // 手动赋值须即时生效：CSS scroll-behavior:smooth 会让连续 += 读到动画中间值，增量丢失。
        const instant=(node,axis,delta)=>{const prev=node.style.scrollBehavior;node.style.scrollBehavior='auto';if(axis==='Y')node.scrollTop+=delta;else node.scrollLeft+=delta;node.style.scrollBehavior=prev;};
        for(const [axis,delta] of [['Y',e.deltaY*modeY],['X',e.deltaX*modeX]]){
          if(!delta)continue;
          let node=origin;
          while(node&&node!==this.dialog){
            const style=getComputedStyle(node);
            if(axis==='Y'&&/(auto|scroll)/.test(style.overflowY)&&((delta>0&&node.scrollTop+node.clientHeight<node.scrollHeight-1)||(delta<0&&node.scrollTop>0))){instant(node,'Y',delta);break;}
            if(axis==='X'&&/(auto|scroll)/.test(style.overflowX)&&((delta>0&&node.scrollLeft+node.clientWidth<node.scrollWidth-1)||(delta<0&&node.scrollLeft>0))){instant(node,'X',delta);break;}
            node=node.parentElement;
          }
        }
        e.preventDefault();e.stopPropagation();
      },{signal,passive:false});
      // DRILL-04 触控隔离：全程阻止冒泡使宿主翻页滑动手势不触发；不 preventDefault，弹层内原生滚动保留。
      // data-no-swipe 供上游引擎 interactive() 识别；stopPropagation 兜底其他宿主。
      this.dialog.setAttribute('data-no-swipe','');
      for(const type of ['touchstart','touchmove','touchend','touchcancel'])this.dialog.addEventListener(type,e=>{e.stopPropagation();},{signal,passive:true});
    }
    push({id,title,render},trigger=document.activeElement){
      if(this.disposed)throw Error('下钻组件已释放');if(!id||!title||typeof render!=='function')throw Error('下钻层缺少 id/title/render');
      if(this.stack.some(x=>x.id===id))throw Error('同一层重复入栈；应通过面包屑返回');
      const old=this.stack.at(-1);
      if(old){old.scroll=this.body.scrollTop;old.focus=trigger?.isConnected?trigger:document.activeElement;old.life.pause?.();old.section.hidden=true;}
      const section=element('section');section.dataset.kzLevel=id;section.setAttribute('aria-label',title);
      this.body.append(section);const rec={id,title,section,scroll:0,focus:null,life:{}};this.stack.push(rec);
      if(this.stack.length===1){this.finishClosing();this.opener=trigger;this.dialog.showModal();this.restoreScroll=lockScroll();this.restoreBackground=isolateBackground(this.dialog);this.onOpen();}
      else this.animateLevel(section,1);
      // A renderer only receives its own container. Strings must be rendered with textContent.
      try{rec.life=render(section,this)||{};}catch(err){section.replaceChildren(element('p','kz-error','明细未能加载：'+err.message));rec.life={};}
      this.sync();this.body.scrollTop=0;this.title.focus();
      if(this.stack.length===1)this.morph(trigger,false);
      requestAnimationFrame(()=>{if(!this.disposed&&this.stack.at(-1)===rec)rec.life.resume?.();});
    }
    sync(){
      const top=this.stack.at(-1);if(!top)return;
      this.title.textContent=top.title;this.back.hidden=this.stack.length<2;this.crumb.hidden=this.stack.length<2;this.crumb.replaceChildren();
      this.stack.forEach((rec,i)=>{
        if(i)this.crumb.append(element('span',null,'›'));
        const b=element('button',null,rec.title);b.type='button';if(i===this.stack.length-1)b.setAttribute('aria-current','page');
        b.addEventListener('click',()=>{while(this.stack.length>i+1)this.pop();});this.crumb.append(b);
      });
    }
    pop(){
      if(this.stack.length<=1){this.close();return;}
      const top=this.stack.pop();top.life.dispose?.();top.section.remove();
      const prev=this.stack.at(-1);prev.section.hidden=false;this.animateLevel(prev.section,-1);this.sync();this.body.scrollTop=prev.scroll;
      prev.life.resume?.();const f=prev.focus;if(f?.isConnected)f.focus({preventScroll:true});else this.title.focus({preventScroll:true});
    }
    // Returns a promise that settles once the native dialog has closed and focus is back on the opener.
    close(){
      if(!this.stack.length)return this.closing?.done??Promise.resolve();
      const opener=this.opener;
      // Fold back into the source card: reverse an unfinished opening, otherwise measure the settled panel.
      const animating=!this.disposed&&(this.reverseOpening()||this.morph(opener,true)),removed=[];
      while(this.stack.length){const rec=this.stack.pop();rec.life.dispose?.();if(animating)removed.push(rec.section);else rec.section.remove();}
      this.restoreBackground?.();this.restoreBackground=null;this.restoreScroll?.();this.restoreScroll=null;this.onClose();
      // Focus can only return once the modal has closed (the page behind a modal dialog is inert).
      if(animating){const c=Object.assign(this.closing,{sections:removed,opener});c.done=c.finished.then(()=>this.finishClosing(),()=>this.finishClosing());return c.done;}
      this.dialog.close();if(opener?.isConnected)opener.focus({preventScroll:true});return Promise.resolve();
    }
    reverseOpening(){
      const o=this.opening;this.opening=null;
      if(!o||o.box.playState!=='running')return false;
      for(const a of [o.box,o.text]){a.effect.updateTiming({fill:'backwards'});a.reverse();}
      this.dialog.style.pointerEvents='none';this.closing={finished:o.box.finished,cancel(){o.box.cancel();o.text.cancel();}};
      return true;
    }
    // Shared-element transition between the source card and the panel (FLIP on the dialog box only).
    morph(trigger,closing){
      const T=global.KZ_TOKENS?.motion||{},reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
      // Only a card (or a declared source) is a shared element; a bare button or <body> opens in place.
      const source=trigger?.closest?.('.kz-card,[data-kz-drill-source]');
      if(reduced||document.hidden||!source?.isConnected||!this.dialog.animate)return false;
      const from=source.getBoundingClientRect(),to=this.dialog.getBoundingClientRect();
      if(!from.width||!from.height||!to.width||!to.height)return false;
      const card=`translate(${from.left-to.left}px,${from.top-to.top}px) scale(${from.width/to.width},${from.height/to.height})`;
      const ease=a=>'cubic-bezier('+a.join(',')+')',frame=this.dialog.firstElementChild;
      const opt={duration:closing?(T.duration_ms?.exit??220):(T.duration_ms?.dialog??420),easing:closing?ease(T.easing?.exit??[.3,0,.8,.15]):ease(T.easing?.enter??[.05,.7,.1,1]),fill:closing?'forwards':'none'};
      this.dialog.style.transformOrigin='0 0';
      const box=this.dialog.animate(closing?[{transform:'none',opacity:1},{transform:card,opacity:.4}]:[{transform:card,opacity:.4},{transform:'none',opacity:1}],opt);
      const text=frame.animate(closing?[{opacity:1},{opacity:0,offset:.5},{opacity:0}]:[{opacity:0},{opacity:0,offset:.45},{opacity:1}],opt);
      if(closing){this.dialog.style.pointerEvents='none';this.closing={finished:box.finished,cancel(){box.cancel();text.cancel();}};}
      else{this.opening={box,text};box.finished.then(()=>{if(this.opening?.box===box)this.opening=null;},()=>{});}
      return true;
    }
    finishClosing(){
      if(!this.closing)return;const c=this.closing;this.closing=null;c.cancel();c.sections?.forEach(x=>x.remove());this.dialog.style.pointerEvents='';if(this.dialog.open&&!this.stack.length){this.dialog.close();if(c.opener?.isConnected)c.opener.focus({preventScroll:true});}
    }
    animateLevel(section,direction){
      const T=global.KZ_TOKENS?.motion||{};
      if(matchMedia('(prefers-reduced-motion: reduce)').matches||!section.animate)return;
      section.animate([{opacity:0,translate:`${24*direction}px 0`},{opacity:1,translate:'0 0'}],{duration:T.duration_ms?.item??360,easing:'cubic-bezier('+(T.easing?.enter??[.05,.7,.1,1]).join(',')+')'});
    }
    snapshot(){return {open:this.dialog.open&&!this.closing,depth:this.stack.length,path:this.stack.map(x=>x.id),width:this.dialog.open&&!this.closing?this.dialog.offsetWidth:0,viewport:innerWidth};}
    dispose(){if(this.disposed)return;this.close();this.finishClosing();this.disposed=true;this.abort.abort();this.dialog.remove();}
  }
  global.KZDrilldown={Drilldown,element};
})(window);
