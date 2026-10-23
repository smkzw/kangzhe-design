/* Kangzhe 7.0 — component motion, not a page/slide navigation runtime.
   Timing, easing, distances and tilt limits come from KZ_TOKENS.motion (tokens/tokens.json). */
(function (global) {
  'use strict';
  const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
  const ease = x => x*x*x*(x*(x*6-15)+10); // zero first/second derivatives at endpoints
  const media = () => matchMedia('(prefers-reduced-motion: reduce)');
  const lerp = (a,b,p) => a+(b-a)*p;
  // Token accessor with the shipped defaults, so partial token objects (tests, older hosts) still work.
  function tk(path, fallback) {
    let v = global.KZ_TOKENS && global.KZ_TOKENS.motion;
    for (const k of path.split('.')) v = v == null ? undefined : v[k];
    return v ?? fallback;
  }
  const bez = (name, fallback) => 'cubic-bezier(' + tk('easing.' + name, fallback).join(',') + ')';
  // HTML-PPT fluid decks scale motion distances with the same ratio as their type (--kz-un).
  function unitOf(el) {
    if (!document.body || document.body.dataset.fit !== 'fluid') return 1;
    const v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--kz-un'));
    return Number.isFinite(v) && v > 0 ? v : 1;
  }
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
  // Deterministic sampling: geometry, tint, text and the text cross-fade all derive from p alone (seekable).
  function sample(frames,p,window=tk('film.text_crossfade_window',.12)) {
    p=clamp(p);let i=0;
    while(i<frames.length-2&&p>frames[i+1].t)i++;
    const a=frames[i],b=frames[i+1],u=ease(clamp((p-a.t)/(b.t-a.t)));
    const f={};for(const k of ['x','y','w','h','r'])f[k]=lerp(a[k],b[k],u);
    f.tint=a.tint.map((v,j)=>lerp(v,b.tint[j],u));
    f.label=(u<.5?a:b).label||'';f.caption=(u<.5?a:b).caption||'';
    // Text changes are swapped at the segment midpoint while fully faded, never as a hard cut.
    const changes=a.label!==b.label||a.caption!==b.caption;
    f.textAlpha=changes&&window>0?clamp(Math.abs(u-.5)/window):1;
    f.index=u<.5?i:i+1;return f;
  }
  class Film {
    constructor(root, options) {
      if(!(root instanceof HTMLElement))throw Error('电影根节点不存在');
      if(activeFilms.has(root))throw Error('电影根节点已由另一时钟挂载，请先dispose');
      validateFrames(options.frames,{managedText:options.managedText!==false});
      this.root=root;this.frames=options.frames;this.duration=options.duration||tk('film.default_ms',36000);
      if(!Number.isFinite(this.duration)||this.duration<1000)throw Error('电影时长无效');
      this.minCarrierWidth=options.minCarrierWidth??tk('film.min_carrier_width_px',160);
      if(!Number.isFinite(this.minCarrierWidth)||this.minCarrierWidth<0)throw Error('载体最小宽度须为非负有限像素值');
      this.stage=root.querySelector('.kz-film-stage');
      this.carrier=root.querySelector('.kz-film-carrier');
      if(!this.stage||!this.carrier)throw Error('缺少持续存在的舞台/载体节点');
      if(activeCarriers.has(this.carrier))throw Error('电影载体已由另一时钟挂载，请先dispose');
      this.carrier.dataset.kzCarrierId=this.carrier.dataset.kzCarrierId||('kz-carrier-'+(++serial));
      this.identity=this.carrier;this.p=0;this.raf=0;this.last=0;this.disposed=false;
      this.reasons=new Set();this.abort=new AbortController();this.signal=this.abort.signal;
      this.onRender=options.onRender||(()=>{});this.staticProgress=options.staticProgress??tk('film.static_progress',.74);
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
      if(this.managedText){
        if(this.label&&this.label.textContent!==f.label)this.label.textContent=f.label;
        if(this.caption&&this.caption.textContent!==f.caption)this.caption.textContent=f.caption;
        this.root.style.setProperty('--kz-film-text',f.textAlpha.toFixed(3));
      }
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
    dispose(){if(this.disposed)return;this.pause('disposed');this.disposed=true;this.abort.abort();this.io.disconnect();this.resize.disconnect();this.mq.removeEventListener('change',this.mqChange);delete this.root.dataset.kzReady;delete this.root.dataset.kzProgress;this.root.style.removeProperty('--kz-film-text');activeFilms.delete(this.root);activeCarriers.delete(this.carrier);}
  }

  /* ---------- Pointer light + tilt: one shared critically damped spring loop ---------- */
  const springs=new Set();let loopRaf=0,loopLast=0;
  function stepSpring(s,dt){
    const k=tk('spring.stiffness',220),c=2*tk('spring.damping_ratio',1)*Math.sqrt(k);let moving=false;
    for(const key of ['lx','ly','lift']){
      const a=k*(s.target[key]-s.pos[key])-c*s.vel[key];s.vel[key]+=a*dt;s.pos[key]+=s.vel[key]*dt;
      if(Math.abs(s.target[key]-s.pos[key])>1e-3||Math.abs(s.vel[key])>1e-3)moving=true;else{s.pos[key]=s.target[key];s.vel[key]=0;}
    }
    const st=s.el.style;st.setProperty('--kz-lx',s.pos.lx.toFixed(4));st.setProperty('--kz-ly',s.pos.ly.toFixed(4));st.setProperty('--kz-lift',s.pos.lift.toFixed(4));
    return moving;
  }
  function loop(now){
    const dt=Math.min((now-(loopLast||now))/1000,1/30);loopLast=now;
    for(const s of springs)if(!stepSpring(s,dt))springs.delete(s);
    loopRaf=springs.size?requestAnimationFrame(loop):0;if(!loopRaf)loopLast=0;
  }
  const kick=s=>{springs.add(s);if(!loopRaf)loopRaf=requestAnimationFrame(loop);};
  function mountTilt(root=document) {
    if(activeTilts.has(root))throw Error('光影根节点已有动态挂载，请先dispose');
    const abort=new AbortController(),mq=media(),els=[...root.querySelectorAll('[data-kz-tilt],[data-kz-light]')],ownedClass=new Set(els.filter(el=>!el.classList.contains('kz-tilt')));
    if(els.some(el=>activeTiltTargets.has(el)))throw Error('光影元素已有动态挂载，请先dispose');
    const states=new Map();
    function reset(el,immediate){
      const s=states.get(el);if(!s)return;s.target={lx:0,ly:0,lift:0};
      if(immediate){springs.delete(s);s.pos={lx:0,ly:0,lift:0};s.vel={lx:0,ly:0,lift:0};for(const p of ['--kz-lx','--kz-ly','--kz-lift','--kz-mx','--kz-my'])el.style.removeProperty(p);}
      else kick(s);
    }
    const blocked=(el,e)=>mq.matches||e.pointerType!=='mouse'||document.getSelection()?.toString()||el.closest('[data-kz-editing=true],[data-kz-frozen=true]')||e.target.closest('input,select,textarea,[contenteditable=true]');
    for(const el of els){
      el.classList.add('kz-tilt');
      // Measurement surfaces keep their light and lift but never rotate.
      const data=el.closest('.kz-chart,.kz-gantt,table,[data-kz-no-tilt]')||el.querySelector('.kz-chart,.kz-gantt,table,[data-kz-no-tilt]');
      const raw=el.dataset.kzTilt?.trim(),requested=raw?Number(raw):tk('tilt.body_max_deg',4);
      const max=el.hasAttribute('data-kz-tilt')&&!data?Math.min(Math.abs(Number.isFinite(requested)?requested:tk('tilt.body_max_deg',4)),tk('tilt.hero_max_deg',6)):0;
      el.style.setProperty('--kz-tilt-max',max+'deg');
      states.set(el,{el,pos:{lx:0,ly:0,lift:0},vel:{lx:0,ly:0,lift:0},target:{lx:0,ly:0,lift:0}});
      el.addEventListener('pointermove',e=>{
        if(blocked(el,e)){reset(el);return;}
        const r=el.getBoundingClientRect(),x=clamp((e.clientX-r.left)/r.width),y=clamp((e.clientY-r.top)/r.height),s=states.get(el);
        el.style.setProperty('--kz-mx',(x*100).toFixed(1)+'%');el.style.setProperty('--kz-my',(y*100).toFixed(1)+'%');
        s.target={lx:x*2-1,ly:y*2-1,lift:1};kick(s);
      },{signal:abort.signal});
      el.addEventListener('pointerleave',()=>reset(el),{signal:abort.signal});
    }
    const change=()=>els.forEach(el=>reset(el,true));mq.addEventListener('change',change);
    let disposed=false;
    const life={dispose(){if(disposed)return;disposed=true;abort.abort();mq.removeEventListener('change',change);activeTilts.delete(root);els.forEach(el=>{activeTiltTargets.delete(el);reset(el,true);el.style.removeProperty('--kz-tilt-max');if(ownedClass.has(el))el.classList.remove('kz-tilt');});}};
    activeTilts.set(root,life);els.forEach(el=>activeTiltTargets.set(el,life));return life;
  }

  /* ---------- Choreographed reveal ----------
     The reveal element owns `translate`/`scale` (individual properties, so a tilt `transform` or a float
     `translate` on other layers is untouched). Opacity is written on the glass card itself: an ancestor with
     opacity<1 becomes a backdrop root and disables the card's backdrop-filter until the fade ends. */
  function glassTargets(el){
    if(el.matches('.kz-card,[data-kz-glass]'))return [el];
    // Outermost glass surfaces that belong to this reveal element (not to a nested reveal).
    const inner=[...el.querySelectorAll('.kz-card,[data-kz-glass]')].filter(c=>c.parentElement.closest('[data-kz-reveal]')===el);
    const top=inner.filter(c=>!inner.some(o=>o!==c&&o.contains(c)));
    return top.length?top:[el];
  }
  function waveDelays(els,step,max){
    // Reading order by rows (8px tolerance), then columns: delay grows along the diagonal wave.
    const boxes=els.map((el,i)=>({el,i,r:el.getBoundingClientRect()}));
    const rows=[];for(const b of [...boxes].sort((a,c)=>a.r.top-c.r.top||a.r.left-c.r.left)){let row=rows.find(x=>Math.abs(x.top-b.r.top)<=8);if(!row)rows.push(row={top:b.r.top,items:[]});row.items.push(b);}
    const delay=new Map();rows.forEach((row,ri)=>row.items.sort((a,c)=>a.r.left-c.r.left).forEach((b,ci)=>{const order=Number(b.el.dataset.kzOrder);delay.set(b.el,Math.min(max,(Number.isFinite(order)?order:ri+ci)*step));}));
    // The takeaway enters last, one beat plus takeaway_gap after the other content (same rule as PPTX MOTION-07).
    const late=el=>!('kzOrder' in el.dataset)&&(el.matches('[data-kz-takeaway]')||!!el.querySelector('.kz-takeaway-card,[data-kz-takeaway]'));
    const rest=els.filter(el=>!late(el)).map(el=>delay.get(el));
    if(rest.length<els.length){const at=Math.min(max,(rest.length?Math.max(...rest)+step:0)+tk('stagger_ms.takeaway_gap',200));els.filter(late).forEach(el=>delay.set(el,at));}
    return delay;
  }
  function animateReveal(root,{exit=false}={}) {
    if(document.hidden||media().matches||root.closest('[data-kz-frozen=true]'))return {finished:Promise.resolve(),cancel(){}};
    const els=[...root.querySelectorAll('[data-kz-reveal]')];
    const u=unitOf(root),animations=[];
    try{
      if(exit){
        const opt={duration:tk('duration_ms.exit',220),easing:bez('exit',[.3,0,.8,.15]),fill:'forwards'};
        for(const el of els){
          animations.push(el.animate([{translate:'0 0',scale:'1'},{translate:`0 ${-tk('distance_px.exit',8)*u}px`,scale:String(tk('scale.exit_to',.99))}],opt));
          for(const g of glassTargets(el))animations.push(g.animate([{opacity:1},{opacity:0}],opt));
        }
      }else{
        const delays=waveDelays(els,tk('stagger_ms.card',70),tk('stagger_ms.max_total',560));
        for(const el of els){
          const delay=delays.get(el)||0;
          animations.push(el.animate([{translate:`0 ${tk('distance_px.card',18)*u}px`,scale:String(tk('scale.card_from',.985))},{translate:'0 0',scale:'1'}],{duration:tk('duration_ms.card',520),delay,easing:bez('enter',[.05,.7,.1,1]),fill:'backwards'}));
          for(const g of glassTargets(el))animations.push(g.animate([{opacity:0},{opacity:1}],{duration:Math.round(tk('duration_ms.card',520)*.62),delay,easing:bez('standard',[.2,0,0,1]),fill:'backwards'}));
          // Inner cascade: title, then each bullet/item, after the shell has started to settle.
          // Table rows join the cascade (reading order, no deformation); cells and charts never move on their own.
          const items=[...el.querySelectorAll('h2,h3,li,tbody tr,[data-kz-reveal-item]')].filter(n=>!n.closest('.kz-chart,.kz-gantt,.kz-film-stage')&&(n.tagName==='TR'||!n.closest('table'))&&n.closest('[data-kz-reveal]')===el);
          items.forEach((n,j)=>{
            const title=/^H\d$/.test(n.tagName),dist=title?tk('distance_px.title',10):tk('distance_px.item',6);
            animations.push(n.animate([{opacity:0,translate:`0 ${dist*u}px`},{opacity:1,translate:'0 0'}],{duration:title?tk('duration_ms.title',360):tk('duration_ms.item',360),delay:delay+tk('stagger_ms.group',90)+Math.min(j*tk('stagger_ms.item',45),tk('stagger_ms.max_total',560)),easing:bez('enter',[.05,.7,.1,1]),fill:'backwards'}));
          });
        }
      }
    }catch(error){animations.forEach(a=>a.cancel());throw error;}
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
    const tilt=mountTilt(root),prior={mounted:root.dataset.kzMotionMounted,active:root.dataset.kzMotionActive};
    let abort,mq,sequence=null,disposed=false,settle=null;
    try{
      abort=new AbortController();mq=media();
      root.dataset.kzMotionMounted='true';root.dataset.kzMotionActive='false';
      function complete(){sequence?.cancel();sequence=null;}
      settle=()=>{if(document.hidden||mq.matches)complete();};
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
    }catch(error){
      const errors=[];
      for(const release of [()=>{if(settle&&mq)mq.removeEventListener('change',settle);},()=>abort?.abort(),()=>tilt.dispose(),
        ()=>{if(prior.mounted===undefined)delete root.dataset.kzMotionMounted;else root.dataset.kzMotionMounted=prior.mounted;},
        ()=>{if(prior.active===undefined)delete root.dataset.kzMotionActive;else root.dataset.kzMotionActive=prior.active;},
        ()=>activePages.delete(root),()=>targets.forEach(el=>activePageTargets.delete(el))]){
        try{release();}catch(failure){errors.push(failure);}
      }
      if(errors.length)throw new AggregateError([error,...errors],'页面挂载失败且未完全释放');
      throw error;
    }
  }

  /* ---------- Section entrances for long pages (stream chapters, site sections below the fold) ----------
     Each [data-kz-section] reveals once when it scrolls into view. Natural scrolling only triggers it;
     nothing is scroll-linked or hijacked. Without JS, or with reduced motion, content is simply visible. */
  function mountSections(root=document,{selector='[data-kz-section]',threshold=.15}={}) {
    const sections=[...root.querySelectorAll(selector)].filter(s=>!activePages.has(s));
    const mq=media(),abort=new AbortController(),pending=new Set(),running=new Map();
    function show(s){s.removeAttribute('data-kz-pending');pending.delete(s);}
    function play(s){if(!pending.has(s))return;try{const seq=reveal(s);show(s);running.set(s,seq);seq.finished.then(()=>running.delete(s));}catch(error){show(s);throw error;}}
    if(!mq.matches)for(const s of sections){const r=s.getBoundingClientRect();if(r.top>innerHeight*.9){s.setAttribute('data-kz-pending','');pending.add(s);}}
    // One failing section must not leave the rest of the batch hidden: report it and carry on.
    const io=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){io.unobserve(e.target);try{play(e.target);}catch(error){(global.reportError||console.error)(error);}}},{threshold});
    pending.forEach(s=>io.observe(s));
    const finishAll=()=>{[...pending].forEach(show);running.forEach(seq=>seq.cancel());running.clear();io.disconnect();};
    global.addEventListener('beforeprint',finishAll,{signal:abort.signal});
    mq.addEventListener('change',finishAll,{signal:abort.signal});
    return {finish:finishAll,dispose(){finishAll();abort.abort();}};
  }

  /* ---------- First-screen capacity guard (13 FOLD-01) ----------
     .kz-detail-tall blocks are optional extras: they show only while the whole first screen still fits the
     viewport. Measured on layout offsets, so entrance translate/scale never counts as overflow. */
  function fitFold(fold=document.querySelector('.kz-fold')){
    if(!(fold instanceof HTMLElement))throw Error('首屏根节点不存在');
    const extras=[...fold.querySelectorAll('.kz-detail-tall')];
    const top=el=>{let y=0;for(let n=el;n;n=n.offsetParent)y+=n.offsetTop;return y;};
    const overflows=()=>{const limit=top(fold)+innerHeight+1;return [...fold.querySelectorAll('.kz-fold-lead > *,.kz-fold-stage')].some(el=>top(el)+el.offsetHeight>limit);};
    // Drop extras from the last one in document order until the first screen fits again.
    function check(){
      extras.forEach(el=>el.removeAttribute('data-kz-fit'));
      for(const el of [...extras].reverse()){if(!overflows())break;el.setAttribute('data-kz-fit','overflow');}
    }
    const ro=new ResizeObserver(check);ro.observe(fold);check();document.fonts?.ready.then(()=>{if(fold.isConnected)check();});
    return {check,dispose(){ro.disconnect();extras.forEach(el=>el.removeAttribute('data-kz-fit'));}};
  }

  /* ---------- Ambient field parallax (environment layer only) ---------- */
  function mountField(root=document) {
    const fields=[...root.querySelectorAll('.kz-optical-field,[data-kz-field]')],mq=media(),abort=new AbortController();let raf=0;
    const ratio=tk('parallax.field_ratio',.06),max=tk('parallax.field_max_px',48);
    function write(){raf=0;const shift=mq.matches?0:clamp(-global.scrollY*ratio,-max,max);for(const f of fields)f.style.setProperty('--kz-field-shift',shift.toFixed(1));}
    const schedule=()=>{if(!raf)raf=requestAnimationFrame(write);};
    global.addEventListener('scroll',schedule,{passive:true,signal:abort.signal});mq.addEventListener('change',schedule,{signal:abort.signal});write();
    return {dispose(){abort.abort();cancelAnimationFrame(raf);for(const f of fields)f.style.removeProperty('--kz-field-shift');}};
  }

  /* ---------- Storyboard: states → seamless frames with FILM-03 reading time ----------
     Each state: {label, caption, facts?:[], geometry:{x,y,w,h,r}, tint?:[r,g,b,a]}. Hold time per state =
     max(min_hold, characters / chars_per_second + read_start). Moves between states, then a closing move
     back to state 0 so frame 1 equals frame 0 (FILM-04). phaseAt/enterAt share the same clock as the Film. */
  function storyboard(states,{charsPerSecond=tk('film.storyboard.chars_per_second',6),readStartMs=tk('film.storyboard.read_start_ms',1200),minHoldMs=tk('film.storyboard.min_hold_ms',2000),moveMs=tk('film.storyboard.move_ms',900),closeMs=tk('film.storyboard.close_ms',1200),tint=[255,250,240,.9],staticState}={}){
    if(!Array.isArray(states)||states.length<2)throw Error('分镜至少需要两个业务状态');
    const holds=states.map(s=>{const chars=[s.label,s.caption,...(s.facts||[])].join('').replace(/\s/g,'').length;return Math.max(minHoldMs,chars/charsPerSecond*1000+readStartMs);});
    const total=holds.reduce((a,b)=>a+b,0)+moveMs*(states.length-1)+closeMs;
    const frames=[],enterAt=[0];let t=0;
    const frame=(time,s)=>({t:Math.min(1,time/total),...s.geometry,tint:s.tint||tint,label:s.label,caption:s.caption||''});
    states.forEach((s,i)=>{
      if(!s.geometry)throw Error('分镜状态缺少 geometry：'+s.label);
      if(i>0){enterAt.push((t-moveMs/2)/total);}
      frames.push(frame(t,s));t+=holds[i];frames.push(frame(t,s));if(i<states.length-1)t+=moveMs;
    });
    const closeAt=(t+closeMs/2)/total;frames.push({...frame(total,states[0]),t:1});frames[0].t=0;
    // The phase comes from the same sampler as the carrier, so a state rail never runs ahead of the panel text.
    function phaseAt(p){const i=sample(frames,p).index;return i>=frames.length-1?0:i>>1;}
    // Static / print / reduced-motion frame: middle of the hold of the most informative state (ties → later).
    let rich=0;states.forEach((s,i)=>{if((s.facts||[]).length>=(states[rich].facts||[]).length)rich=i;});
    if(staticState!==undefined){if(!Number.isInteger(staticState)||staticState<0||staticState>=states.length)throw Error('staticState 超出状态范围');rich=staticState;}
    const staticProgress=(frames[2*rich].t+frames[2*rich+1].t)/2;
    return {frames,duration:Math.round(total),holds,enterAt,closeAt,phaseAt,staticProgress};
  }

  /* ---------- Relation links inside a film stage ----------
     Deterministic and seekable: called from Film onRender with each link's own reveal progress (0–1).
     Paths are recomputed from the live rects, so they follow the carrier as it changes shape. */
  const SVGNS='http://www.w3.org/2000/svg';
  function drawLinks(svg,pairs){
    if(!(svg instanceof SVGSVGElement))throw Error('关系连线需要舞台内的 svg 节点');
    const box=svg.getBoundingClientRect();if(!box.width||!box.height)return;
    svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
    for(const [i,pair] of pairs.entries()){
      let path=svg.querySelector(`path[data-kz-link="${pair.id||i}"]`);
      if(!path){path=document.createElementNS(SVGNS,'path');path.dataset.kzLink=pair.id||i;path.setAttribute('fill','none');svg.append(path);}
      const a=pair.from.getBoundingClientRect(),b=pair.to.getBoundingClientRect();
      const x1=a.right-box.left,y1=a.top+a.height/2-box.top,x2=b.left-box.left,y2=b.top+b.height/2-box.top,dx=Math.max(24,(x2-x1)/2);
      path.setAttribute('d',`M${x1.toFixed(1)} ${y1.toFixed(1)} C${(x1+dx).toFixed(1)} ${y1.toFixed(1)} ${(x2-dx).toFixed(1)} ${y2.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`);
      const len=path.getTotalLength(),q=clamp(pair.progress??1);
      path.style.strokeDasharray=`${len} ${len}`;path.style.strokeDashoffset=String(len*(1-q));path.style.opacity=q>0?'1':'0';
    }
  }

  /* ---------- Count-up for KPI numbers: deterministic, ends on the true value ---------- */
  function countUp(el,{to,from=0,decimals=0,duration=tk('duration_ms.count',900)}={}) {
    if(!(el instanceof HTMLElement))throw Error('计数元素不存在');
    if(!Number.isFinite(to)||!Number.isFinite(from))throw Error('计数目标须为有限数');
    const fmt=v=>Number(v).toLocaleString('zh-CN',{minimumFractionDigits:decimals,maximumFractionDigits:decimals});
    const [x1,y1,x2,y2]=tk('easing.data',[.33,1,.68,1]);
    // Cubic-bezier y(x) by bisection so the number follows the same curve as data reveals.
    const curve=x=>{let lo=0,hi=1;for(let i=0;i<24;i++){const t=(lo+hi)/2,bx=3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3;bx<x?lo=t:hi=t;}const t=(lo+hi)/2;return 3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3;};
    let raf=0,p=1,disposed=false;el.setAttribute('aria-label',fmt(to));
    const render=q=>{p=clamp(q);el.textContent=fmt(from+(to-from)*curve(p));};
    const finish=()=>{cancelAnimationFrame(raf);raf=0;render(1);};
    render(1);
    return {
      play(){if(disposed)return;cancelAnimationFrame(raf);if(media().matches||document.hidden){finish();return;}let start=null;render(0);
        const tick=now=>{start??=now;render((now-start)/duration);raf=p<1?requestAnimationFrame(tick):0;};raf=requestAnimationFrame(tick);},
      seek:render,finish,get progress(){return p;},
      dispose(){disposed=true;finish();}
    };
  }
  global.KZMotion={Film,mountTilt,reveal,mountPage,mountSections,mountField,fitFold,countUp,drawLinks,storyboard,sample,validateFrames};
})(window);
