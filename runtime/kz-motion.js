/* Kangzhe 6.0 — component motion, not a page/slide navigation runtime. */
(function (global) {
  'use strict';
  const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
  const ease = x => x*x*x*(x*(x*6-15)+10); // zero first/second derivatives at endpoints
  const media = () => matchMedia('(prefers-reduced-motion: reduce)');
  const lerp = (a,b,p) => a+(b-a)*p;
  let serial=0;
  function validateFrames(frames) {
    if (!Array.isArray(frames)||frames.length<4) throw Error('电影至少需要四个关键帧（含回接帧）');
    let prev=-1;
    for (const f of frames) {
      if (!Number.isFinite(f.t)||f.t<=prev||f.t<0||f.t>1) throw Error('关键帧时间须在 0–1 严格递增');
      prev=f.t;
      for (const k of ['x','y','w','h','r']) if(!Number.isFinite(f[k])) throw Error('关键帧缺少数值 '+k);
      if(f.x<0||f.y<0||f.w<=0||f.h<=0||f.x+f.w>1.00001||f.y+f.h>1.00001||f.r<0||f.r>.5) throw Error('载体关键帧超出舞台');
      if(!Array.isArray(f.tint)||f.tint.length!==4||f.tint.some((v,i)=>!Number.isFinite(v)||v<0||v>(i===3?1:255))) throw Error('颜色格式须为 RGBA 数组');
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
      validateFrames(options.frames);
      this.root=root;this.frames=options.frames;this.duration=options.duration||36000;
      if(!Number.isFinite(this.duration)||this.duration<1000)throw Error('电影时长无效');
      this.minCarrierWidth=options.minCarrierWidth??160;
      this.stage=root.querySelector('.kz-film-stage');
      this.carrier=root.querySelector('.kz-film-carrier');
      if(!this.stage||!this.carrier)throw Error('缺少持续存在的舞台/载体节点');
      this.carrier.dataset.kzCarrierId=this.carrier.dataset.kzCarrierId||('kz-carrier-'+(++serial));
      this.identity=this.carrier;this.p=0;this.raf=0;this.last=0;this.disposed=false;
      this.reasons=new Set();this.abort=new AbortController();this.signal=this.abort.signal;
      this.onRender=options.onRender||(()=>{});this.staticProgress=options.staticProgress??.74;
      this.label=this.carrier.querySelector('.kz-film-carrier-label');
      this.caption=root.querySelector('.kz-film-caption');this.slider=root.querySelector('input[data-kz-progress]');
      this.progressText=root.querySelector('[data-kz-progress-text]');this.toggle=root.querySelector('[data-kz-pause]');
      const replay=root.querySelector('[data-kz-replay]');this.mq=media();
      this.mqChange=()=>{if(this.mq.matches){this.pause('reduced-motion');this.seek(this.staticProgress);}else this.resume('reduced-motion');};
      this.mq.addEventListener('change',this.mqChange);
      document.addEventListener('visibilitychange',()=>document.hidden?this.pause('hidden'):this.resume('hidden'),{signal:this.signal});
      this.toggle?.addEventListener('click',()=>this.reasons.has('user')?this.resume('user'):this.pause('user'),{signal:this.signal});
      replay?.addEventListener('click',()=>{this.seek(0);this.resume('user');},{signal:this.signal});
      this.slider?.addEventListener('input',()=>{this.pause('user');this.seek(Number(this.slider.value)/1000);},{signal:this.signal});
      root.addEventListener('keydown',e=>{if(e.target.closest('input,select,button,textarea,[contenteditable=true]'))e.stopPropagation();},{signal:this.signal});
      this.resize=new ResizeObserver(()=>this.render());this.resize.observe(this.stage);
      this.io=new IntersectionObserver(entries=>{for(const e of entries)e.isIntersecting?this.resume('offscreen'):this.pause('offscreen');},{threshold:.05});
      this.io.observe(root);this.before=()=>{this.savedCapture=this.p;this.pause('capture');this.seek(this.staticProgress);};
      this.after=()=>{this.seek(this.savedCapture??this.p);this.resume('capture');};
      global.addEventListener('beforeprint',this.before,{signal:this.signal});global.addEventListener('afterprint',this.after,{signal:this.signal});
      this.render();if(this.mq.matches)this.mqChange();else this.resume('init');
      if(document.hidden)this.pause('hidden');
      root.dataset.kzReady='true';
    }
    render() {
      if(this.disposed)return;
      const f=sample(this.frames,this.p),s=this.carrier.style;
      if(this.stage.clientWidth>0){f.w=Math.max(f.w,Math.min(.88,this.minCarrierWidth/this.stage.clientWidth));f.x=Math.min(f.x,1-f.w);}
      s.left=(f.x*100)+'%';s.top=(f.y*100)+'%';s.width=(f.w*100)+'%';s.height=(f.h*100)+'%';
      const radius=Math.min(this.stage.clientWidth*f.w,this.stage.clientHeight*f.h)*f.r;
      s.borderRadius=radius+'px';s.backgroundColor=`rgba(${f.tint[0]},${f.tint[1]},${f.tint[2]},${f.tint[3]})`;
      if(this.label&&this.label.textContent!==f.label)this.label.textContent=f.label;
      if(this.caption&&this.caption.textContent!==f.caption)this.caption.textContent=f.caption;
      if(this.slider)this.slider.value=String(Math.round(this.p*1000));
      if(this.progressText)this.progressText.textContent=Math.round(this.p*100)+'%';
      this.onRender(f,this.p,this);
      this.root.dataset.kzProgress=this.p.toFixed(5);
    }
    tick(now) {
      this.raf=0;if(this.disposed||this.reasons.size)return;
      const dt=this.last?Math.min(now-this.last,100):0;this.last=now;
      this.p=(this.p+dt/this.duration)%1;this.render();this.raf=requestAnimationFrame(t=>this.tick(t));
    }
    syncButton() {if(this.toggle){const stopped=this.reasons.has('user');this.toggle.textContent=stopped?'继续':'暂停';this.toggle.setAttribute('aria-pressed',String(stopped));}}
    pause(reason='user') {this.reasons.add(reason);cancelAnimationFrame(this.raf);this.raf=0;this.last=0;this.syncButton();}
    resume(reason='user') {this.reasons.delete(reason);this.syncButton();if(!this.disposed&&!this.reasons.size&&!this.raf){this.last=0;this.raf=requestAnimationFrame(t=>this.tick(t));}}
    seek(p) {if(!Number.isFinite(p))throw Error('进度不是有限数');this.p=clamp(p);this.last=0;this.render();}
    snapshot(){return {progress:this.p,carrierId:this.carrier.dataset.kzCarrierId,sameNode:this.carrier===this.identity,connected:this.carrier.isConnected,running:!!this.raf,reasons:[...this.reasons],style:{left:this.carrier.style.left,top:this.carrier.style.top,width:this.carrier.style.width,height:this.carrier.style.height,radius:this.carrier.style.borderRadius,color:this.carrier.style.backgroundColor},rect:this.carrier.getBoundingClientRect().toJSON()};}
    dispose(){if(this.disposed)return;this.pause('disposed');this.disposed=true;this.abort.abort();this.io.disconnect();this.resize.disconnect();this.mq.removeEventListener('change',this.mqChange);delete this.root.dataset.kzReady;}
  }
  function mountTilt(root=document) {
    const abort=new AbortController(),mq=media(),els=[...root.querySelectorAll('[data-kz-tilt]')];
    function reset(el){el.style.transform='';el.style.removeProperty('--kz-mx');el.style.removeProperty('--kz-my');}
    for(const el of els){
      el.classList.add('kz-tilt');
      el.addEventListener('pointermove',e=>{
        if(mq.matches||e.pointerType!=='mouse'||el.closest('[data-kz-editing=true],[data-kz-frozen=true]')||el.querySelector('.kz-chart,.kz-gantt')||e.target.closest('input,select,textarea,[contenteditable=true]')){reset(el);return;}
        const r=el.getBoundingClientRect(),x=clamp((e.clientX-r.left)/r.width),y=clamp((e.clientY-r.top)/r.height),max=Math.max(0,Math.min(Math.abs(Number(el.dataset.kzTilt)||10),10));
        el.style.setProperty('--kz-mx',(x*100)+'%');el.style.setProperty('--kz-my',(y*100)+'%');
        el.style.transform=`perspective(1100px) rotateX(${(0.5-y)*2*max}deg) rotateY(${(x-0.5)*2*max}deg)`;
      },{signal:abort.signal});
      el.addEventListener('pointerleave',()=>reset(el),{signal:abort.signal});
    }
    const change=()=>els.forEach(reset);mq.addEventListener('change',change);
    return {dispose(){abort.abort();mq.removeEventListener('change',change);els.forEach(reset);}};
  }
  function reveal(root,{exit=false}={}) {
    if(media().matches)return {finished:Promise.resolve(),cancel(){}};
    const els=[...root.querySelectorAll('[data-kz-reveal]')];
    const animations=els.map((el,i)=>el.animate(exit?[{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(-8px)'}]:[{opacity:0,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:exit?240:440,delay:exit?0:i*70,easing:'cubic-bezier(.2,.7,.2,1)',fill:exit?'none':'backwards'}));
    return {finished:Promise.all(animations.map(a=>a.finished.catch(()=>{}))),cancel(){animations.forEach(a=>a.cancel());}};
  }
  global.KZMotion={Film,mountTilt,reveal,sample,validateFrames};
})(window);
