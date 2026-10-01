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
      this.dialog.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Escape'].includes(e.key))e.stopPropagation();},{signal});
    }
    push({id,title,render},trigger=document.activeElement){
      if(this.disposed)throw Error('下钻组件已释放');if(!id||!title||typeof render!=='function')throw Error('下钻层缺少 id/title/render');
      if(this.stack.some(x=>x.id===id))throw Error('同一层重复入栈；应通过面包屑返回');
      const old=this.stack.at(-1);
      if(old){old.scroll=this.body.scrollTop;old.focus=trigger?.isConnected?trigger:document.activeElement;old.life.pause?.();old.section.hidden=true;}
      const section=element('section');section.dataset.kzLevel=id;section.setAttribute('aria-label',title);
      this.body.append(section);const rec={id,title,section,scroll:0,focus:null,life:{}};this.stack.push(rec);
      if(this.stack.length===1){this.opener=trigger;this.dialog.showModal();this.restoreScroll=lockScroll();this.restoreBackground=isolateBackground(this.dialog);this.onOpen();}
      // A renderer only receives its own container. Strings must be rendered with textContent.
      try{rec.life=render(section,this)||{};}catch(err){section.replaceChildren(element('p','kz-error','明细未能加载：'+err.message));rec.life={};}
      this.sync();this.body.scrollTop=0;this.title.focus();
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
      const prev=this.stack.at(-1);prev.section.hidden=false;this.sync();this.body.scrollTop=prev.scroll;
      prev.life.resume?.();const f=prev.focus;if(f?.isConnected)f.focus({preventScroll:true});else this.title.focus({preventScroll:true});
    }
    close(){
      if(!this.stack.length)return;
      while(this.stack.length){const rec=this.stack.pop();rec.life.dispose?.();rec.section.remove();}
      this.dialog.close();this.restoreBackground?.();this.restoreBackground=null;this.restoreScroll?.();this.restoreScroll=null;this.onClose();
      if(this.opener?.isConnected)this.opener.focus();
    }
    snapshot(){return {open:this.dialog.open,depth:this.stack.length,path:this.stack.map(x=>x.id),width:this.dialog.open?this.dialog.getBoundingClientRect().width:0,viewport:innerWidth};}
    dispose(){if(this.disposed)return;this.close();this.disposed=true;this.abort.abort();this.dialog.remove();}
  }
  global.KZDrilldown={Drilldown,element};
})(window);
