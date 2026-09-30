/* Kangzhe 6.0 — component motion, not a page/slide navigation runtime. */
(function (global) {
  'use strict';
  const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
  const ease = x => x*x*x*(x*(x*6-15)+10); // zero first/second derivatives at endpoints
  const media = () => matchMedia('(prefers-reduced-motion: reduce)');
  const lerp = (a,b,p) => a+(b-a)*p;
  let serial=0;
  const activeFilms=new WeakMap(),activeCarriers=new WeakMap(),activePages=new WeakMap(),activePageTargets=new WeakMap(),activeTilts=new WeakMap(),activeTiltTargets=new WeakMap();
  function validateFrames(frames,{managedText=true}={}) {
    if (!Array.isArray(frames)||frames.length<4) throw Error('电影至少需要四个关键帧（含回接帧）');
    let prev=-1;
    for (const f of frames) {
      if (!Number.isFinite(f.t)||f.t<=prev||f.t<0||f.t>1) throw Error('关键帧时间须在 0–1 严格递增');
      prev=f.t;
      for (const k of ['x','y','w','h','r']) if(!Number.isFinite(f[k])) throw Error('关键帧缺少数值 '+k);
      if(f.x<0||f.y<0||f.w<=0||f.h<=0||f.x+f.w>1.00001||f.y+f.h>1.00001||f.r<0||f.r>.5) throw Error('载体关键帧超出舞台');
      if(!Array.isArray(f.tint)||f.tint.length!==4||f.tint.some((v,i)=>!Number.isFinite(v)||v<0||v>(i===3?1:255))) throw Error('颜色格式须为 RGBA 数组');
      if(managedText&&['label','caption'].some(k=>typeof f[k]!=='string'))throw Error('关键帧须显式提供标题和说明文字');
    }
    if(frames[0].t!==0||frames.at(-1).t!==1) throw Error('电影须有 0 与 1 端点');
    const a=frames[0],b=frames.at(-1);
    for(const k of ['x','y','w','h','r']) if(Math.abs(a[k]-b[k])>1e-4) throw Error('首尾几何不一致 '+k);
    if(a.tint.some((v,i)=>Math.abs(v-b.tint[i])>1e-4)||a.label!==b.label||a.caption!==b.caption) throw Error('首尾材料或文字不一致');
  }
  function sample(frames,p) {
    p=clamp(p);let i=0;
    while(i<frames.length-2&&p>frames[i+1].t)i++;
    const a=frames[i],b=frames[i+1],u=ease(clamp((p-a.t)/(b.t-a.t)));
    const f={};for(const k of ['x','y','w','h','r'])f[k]=lerp(a[k],b[k],u);
    f.tint=a.tint.map((v,j)=>lerp(v,b.tint[j],u));
    f.label=(u<.5?a:b).label||'';f.caption=(u<.5?a:b).caption||'';
    f.index=u<.5?i:i+1;return f;
  }
  class Film {
    constructor(root, options) {
      if(!(root instanceof HTMLElement))throw Error('电影根节点不存在');
      if(activeFilms.has(root))throw Error('电影根节点已由另一时钟挂载，请先dispose');
      validateFrames(options.frames,{managedText:options.managedText!==false});
      this.root=root;this.frames=options.frames;this.duration=options.duration||36000;
      if(!Number.isFinite(this.duration)||this.duration<1000)throw Error('电影时长无效');
      this.minCarrierWidth=options.minCarrierWidth??160;
      if(!Number.isFinite(this.minCarrierWidth)||this.minCarrierWidth<0)throw Error('载体最小宽度须为非负有限像素值');
      this.stage=root.querySelector('.kz-film-stage');
      this.carrier=root.querySelector('.kz-film-carrier');
      if(!this.stage||!this.carrier)throw Error('缺少持续存在的舞台/载体节点');
      if(activeCarriers.has(this.carrier))throw Error('电影载体已由另一时钟挂载，请先dispose');
      this.carrier.dataset.kzCarrierId=this.carrier.dataset.kzCarrierId||('kz-carrier-'+(++serial));
      this.identity=this.carrier;this.p=0;this.raf=0;this.last=0;this.disposed=false;
      this.reasons=new Set();this.abort=new AbortController();this.signal=this.abort.signal;
      this.onRender=options.onRender||(()=>{});this.staticProgress=options.staticProgress??.74;
      // A project business clock may own text; frame geometry remains managed here.
      this.managedText=options.managedText!==false;
      this.label=this.carrier.querySelector('.kz-film-carrier-label');
      this.caption=root.querySelector('.kz-film-caption');this.mq=media();
      this.mqChange=()=>{if(this.mq.matches){this.pause('reduced-motion');this.seek(this.staticProgress);}else this.resume('reduced-motion');};
      this.mq.addEventListener('change',this.mqChange);
      document.addEventListener('visibilitychange',()=>document.hidden?this.pause('hidden'):this.resume('hidden'),{signal:this.signal});
      root.addEventListener('keydown',e=>{if(e.target.closest('input,select,button,textarea,[contenteditable=true]'))e.stopPropagation();},{signal:this.signal});
      this.resize=new ResizeObserver(()=>this.render());this.resize.observe(this.stage);
      this.io=new IntersectionObserver(entries=>{for(const e of entries)e.isIntersecting?this.resume('offscreen'):this.pause('offscreen');},{threshold:.05});
      this.io.observe(root);this.before=()=>{this.savedCapture=this.p;this.pause('capture');this.seek(this.staticProgress);};
      this.after=()=>{this.seek(this.savedCapture??this.p);this.resume('capture');};
      global.addEventListener('beforeprint',this.before,{signal:this.signal});global.addEventListener('afterprint',this.after,{signal:this.signal});
      activeFilms.set(root,this);
      activeCarriers.set(this.carrier,this);
      try{this.render();}catch(error){this.dispose();throw error;}
      if(this.mq.matches)this.mqChange();else this.resume('init');
      if(document.hidden)this.pause('hidden');
      root.dataset.kzReady='true';
    }
    render() {
      if(this.disposed)return;
      const f=sample(this.frames,this.p),s=this.carrier.style;
      const requested={x:f.x,y:f.y,w:f.w,h:f.h};
      if(this.stage.clientWidth>0){f.w=Math.max(f.w,Math.min(.88,this.minCarrierWidth/this.stage.clientWidth));f.x=Math.min(f.x,1-f.w);}
      this.geometry={requested,effective:{x:f.x,y:f.y,w:f.w,h:f.h},stage:[this.stage.clientWidth,this.stage.clientHeight],minCarrierWidth:this.minCarrierWidth,adjusted:f.x!==requested.x||f.w!==requested.w};
      s.left=(f.x*100)+'%';s.top=(f.y*100)+'%';s.width=(f.w*100)+'%';s.height=(f.h*100)+'%';
      const radius=Math.min(this.stage.clientWidth*f.w,this.stage.clientHeight*f.h)*f.r;
      s.borderRadius=radius+'px';s.backgroundColor=`rgba(${f.tint[0]},${f.tint[1]},${f.tint[2]},${f.tint[3]})`;
      if(this.managedText&&this.label&&this.label.textContent!==f.label)this.label.textContent=f.label;
      if(this.managedText&&this.caption&&this.caption.textContent!==f.caption)this.caption.textContent=f.caption;
      this.onRender(f,this.p,this);
      this.root.dataset.kzProgress=this.p.toFixed(5);
    }
    tick(now) {
      this.raf=0;if(this.disposed||this.reasons.size)return;
      const dt=this.last?Math.min(now-this.last,100):0;this.last=now;
      this.p=(this.p+dt/this.duration)%1;this.render();this.raf=requestAnimationFrame(t=>this.tick(t));
    }
    pause(reason='user') {if(this.disposed)return;this.reasons.add(reason);cancelAnimationFrame(this.raf);this.raf=0;this.last=0;}
    resume(reason='user') {if(this.disposed)return;this.reasons.delete(reason);if(!this.reasons.size&&!this.raf){this.last=0;this.raf=requestAnimationFrame(t=>this.tick(t));}}
    seek(p) {if(this.disposed)return;if(!Number.isFinite(p))throw Error('进度不是有限数');this.p=clamp(p);this.last=0;this.render();}
    snapshot(){return {progress:this.p,geometry:this.geometry,carrierId:this.carrier.dataset.kzCarrierId,sameNode:this.carrier===this.identity,connected:this.carrier.isConnected,running:!!this.raf,reasons:[...this.reasons],style:{left:this.carrier.style.left,top:this.carrier.style.top,width:this.carrier.style.width,height:this.carrier.style.height,radius:this.carrier.style.borderRadius,color:this.carrier.style.backgroundColor},rect:this.carrier.getBoundingClientRect().toJSON()};}
    dispose(){if(this.disposed)return;this.pause('disposed');this.disposed=true;this.abort.abort();this.io.disconnect();this.resize.disconnect();this.mq.removeEventListener('change',this.mqChange);delete this.root.dataset.kzReady;activeFilms.delete(this.root);activeCarriers.delete(this.carrier);}
  }
  function mountTilt(root=document) {
    if(activeTilts.has(root))throw Error('光影根节点已有动态挂载，请先dispose');
    const abort=new AbortController(),mq=media(),els=[...root.querySelectorAll('[data-kz-tilt],[data-kz-light]')],ownedClass=new Set(els.filter(el=>!el.classList.contains('kz-tilt')));
    if(els.some(el=>activeTiltTargets.has(el)))throw Error('光影元素已有动态挂载，请先dispose');
    function reset(el){el.style.transform='';el.style.removeProperty('--kz-mx');el.style.removeProperty('--kz-my');}
    for(const el of els){
      el.classList.add('kz-tilt');
      el.addEventListener('pointermove',e=>{
        if(mq.matches||e.pointerType!=='mouse'||document.getSelection()?.toString()||el.closest('[data-kz-editing=true],[data-kz-frozen=true]')||e.target.closest('input,select,textarea,[contenteditable=true]')){reset(el);return;}
        const raw=el.dataset.kzTilt?.trim(),requested=raw?Number(raw):10;
        const r=el.getBoundingClientRect(),x=clamp((e.clientX-r.left)/r.width),y=clamp((e.clientY-r.top)/r.height),max=Math.min(Math.abs(Number.isFinite(requested)?requested:10),10);
        el.style.setProperty('--kz-mx',(x*100)+'%');el.style.setProperty('--kz-my',(y*100)+'%');
        if(el.hasAttribute('data-kz-tilt')&&!el.closest('.kz-chart,.kz-gantt,table,[data-kz-no-tilt]')&&!el.querySelector('.kz-chart,.kz-gantt,table,[data-kz-no-tilt]'))el.style.transform=`perspective(1100px) rotateX(${(0.5-y)*2*max}deg) rotateY(${(x-0.5)*2*max}deg)`;
      },{signal:abort.signal});
      el.addEventListener('pointerleave',()=>reset(el),{signal:abort.signal});
    }
    const change=()=>els.forEach(reset);mq.addEventListener('change',change);
    let disposed=false;
    const life={dispose(){if(disposed)return;disposed=true;abort.abort();mq.removeEventListener('change',change);activeTilts.delete(root);els.forEach(el=>{activeTiltTargets.delete(el);reset(el);if(ownedClass.has(el))el.classList.remove('kz-tilt');});}};
    activeTilts.set(root,life);els.forEach(el=>activeTiltTargets.set(el,life));return life;
  }
  function animateReveal(root,{exit=false}={}) {
    if(document.hidden||media().matches||root.closest('[data-kz-frozen=true]'))return {finished:Promise.resolve(),cancel(){}};
    const els=[...root.querySelectorAll('[data-kz-reveal]')];
    const animations=[];try{els.forEach((el,i)=>animations.push(el.animate(exit?[{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(-8px)'}]:[{opacity:0,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:exit?(global.KZ_TOKENS?.motion?.exit_ms??240):(global.KZ_TOKENS?.motion?.enter_ms??440),delay:exit?0:i*(global.KZ_TOKENS?.motion?.stagger_ms??70),easing:'cubic-bezier(.2,.7,.2,1)',fill:exit?'forwards':'backwards'})));}catch(error){animations.forEach(a=>a.cancel());throw error;}
    return {finished:Promise.all(animations.map(a=>a.finished.catch(()=>{}))),cancel(){animations.forEach(a=>a.cancel());}};
  }
  function reveal(root,{exit=false}={}) {
    const targets=[...root.querySelectorAll('[data-kz-reveal]')];
    if(targets.some(el=>activePageTargets.has(el)))throw Error('页面动画元素已有动态挂载，请先取消或dispose');
    let sequence=null,released=false;
    const owner={cancel(){sequence?.cancel();release();}};
    function release(){if(released)return;released=true;targets.forEach(el=>{if(activePageTargets.get(el)===owner)activePageTargets.delete(el);});}
    targets.forEach(el=>activePageTargets.set(el,owner));
    try{sequence=animateReveal(root,{exit});}catch(error){release();throw error;}
    const finished=sequence.finished.finally(()=>{if(!exit)release();});
    return{finished,cancel:owner.cancel};
  }
  function mountPage(root) {
    if(activePages.has(root))throw Error('页面根节点已有动态挂载，请先dispose');
    const targets=[...root.querySelectorAll('[data-kz-reveal]')];
    if(targets.some(el=>activePageTargets.has(el)))throw Error('页面动画元素已有动态挂载，请先dispose');
    const tilt=mountTilt(root),abort=new AbortController(),mq=media();let sequence=null,disposed=false;
    root.dataset.kzMotionMounted='true';root.dataset.kzMotionActive='false';
    function complete(){sequence?.cancel();sequence=null;}
    const settle=()=>{if(document.hidden||mq.matches)complete();};
    document.addEventListener('visibilitychange',settle,{signal:abort.signal});
    global.addEventListener('beforeprint',complete,{signal:abort.signal});
    mq.addEventListener('change',settle);
    const life={
      enter(){if(disposed)return;complete();root.dataset.kzMotionActive='true';sequence=animateReveal(root);},
      leave(){if(disposed)return;complete();root.dataset.kzMotionActive='false';sequence=animateReveal(root,{exit:true});},
      finish(){complete();},
      dispose(){if(disposed)return;disposed=true;complete();tilt.dispose();abort.abort();mq.removeEventListener('change',settle);activePages.delete(root);targets.forEach(el=>activePageTargets.delete(el));delete root.dataset.kzMotionMounted;delete root.dataset.kzMotionActive;}
    };
    activePages.set(root,life);targets.forEach(el=>activePageTargets.set(el,life));return life;
  }
  global.KZMotion={Film,mountTilt,reveal,mountPage,sample,validateFrames};
})(window);
