/* kz-explore.js — the interactive layer of the round-9 clinical figures in the HTML tracks (HTML-PPT, site, stream).

   KZExposure — cumulative exposure on the development plan (= Python diagram_scenes.exposure_plan_chart; the model is
   KZClinical.exposurePlan, the tables KZClinical.exposureTables). An ECharts step line of the drug-exposed patients
   counted study by study, a dot per study in its indication's colour, the ICH E1 total target, one numbered NDA vertical
   per indication, the count at each NDA ringed (met / short with the gap) and the first crossing.
     · hover a dot: the study's sample size, control share, exposure, when it counts and the running total;
     · drag a dot left / right: the study moves in the plan (its bar's start and end, whole units of the bar's own
       precision); up / down: its exposure (step 10; the sample size follows the control share, ≥26/≥52 weeks scale);
     · ← / → pick a study, Shift + ← / → move it one unit, Shift + ↑ / ↓ exposure ± 10, ⌘/Ctrl + Z undo;
     · T, Enter or double-click: the Gantt studio on the same plan (a bar's 暴露 block: n, control share, exposed,
       ≥26 / ≥52 weeks), Esc closes.
   The plan is held by an off-screen KZGantt (anchor = this figure), so every change rides the plan bus
   (KZGantt.publish): a Gantt or figure of the same program id on the page follows, KZ_DECK_DATA keeps the figure's
   data for 保存到本文件, and the readiness / ledger tables of that plan ([data-kz-xp-table]) re-render.
   Requires echarts, kz-tokens.js, kz-clinical.js, kz-gantt.js, kz-charts.js (kz-gantt-studio.js for T). */
(function(global){
  'use strict';
  const K=()=>global.KZClinical,G=()=>global.KZGantt,TK=()=>global.KZ_TOKENS;
  const clone=x=>JSON.parse(JSON.stringify(x)),n0=v=>Number(v).toLocaleString('en-US');
  const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const unitOf=s=>/Q/.test(s)?'quarter':String(s).length===7?'month':'day';
  const UNIT_LEN={quarter:1,month:1/3,day:1/91};
  function nice(v){const raw=v*1.08/5,mag=10**Math.floor(Math.log10(raw)),st=[1,2,2.5,5,10].map(k=>k*mag).find(s=>s>=raw-1e-9);return [Math.ceil(v*1.08/st-1e-9)*st,st];}

  // ---- tables of a plan: re-render every [data-kz-xp-table] that follows it (the Python table_html markup)
  function renderTable(fig,spec){
    const tb=fig.querySelector('tbody');if(!tb)return;const num=new Set(spec.numeric||[]),cen=new Set(spec.center||[]);
    tb.innerHTML=spec.rows.map(r=>'<tr>'+r.map((c,col)=>{c=typeof c==='object'&&c?c:{text:String(c)};
      const al=num.has(col)?'r':cen.has(col)?'c':'l',cls=[`is-${al}`].concat(c.tone?[`is-${c.tone}`]:[]);let body=esc(c.text??'');if(col===0)body=`<b>${body}</b>`;
      return `<td class="${cls.join(' ')}">${body}</td>`;}).join('')+'</tr>').join('');
  }
  // each table carries the figure's settings (targets, focus, unit, label: data-kz-xp-meta); the plan comes with the change
  function refreshTables(ref,program){
    if(typeof document==='undefined')return;const memo=new Map();
    for(const fig of document.querySelectorAll(`[data-kz-xp-plan="${CSS.escape(String(ref))}"]`)){
      const meta=fig.dataset.kzXpMeta||'{}';
      try{if(!memo.has(meta))memo.set(meta,K().exposureTables(K().exposurePlan({...JSON.parse(meta),program})));const t=memo.get(meta)[fig.dataset.kzXpTable];if(t)renderTable(fig,t);}
      catch(e){console.error(e);}
    }
  }

  function mount(el,data,opts={}){
    if(!global.echarts)throw Error('缺少随包 ECharts；不以 CSS 假图代替');
    if(!K()||!G())throw Error('累计暴露图需要 kz-clinical.js 与 kz-gantt.js');
    let spec=clone(data),m=K().exposurePlan(spec);const ref=data.ref||(spec.program&&spec.program.id)||'';
    const gid=el.dataset?.kzChart,store=()=>gid&&global.KZ_DECK_DATA&&Object.prototype.hasOwnProperty.call(global.KZ_DECK_DATA,gid)?global.KZ_DECK_DATA:null;
    let disposed=false,progress=1,raf=0,sel=0,drag=null,preview=null,hintTimer=0;
    const prior=[...el.childNodes],priorPos=el.style.position;if(getComputedStyle(el).position==='static')el.style.position='relative';   // the plot fills this element on any page
    const plot=document.createElement('div');plot.className='kz-xp-plot';plot.style.cssText='position:absolute;inset:0';plot.tabIndex=0;plot.setAttribute('role','application');
    plot.setAttribute('aria-label','累计暴露图（可编辑）：左右方向键（Home / End）选研究，Shift 加左右移动时间、Shift 加上下调整暴露例数；拖动圆点同样可调；回车、双击或 T 打开编辑台');
    const hint=document.createElement('p');hint.className='kz-gantt-status kz-xp-status';hint.setAttribute('aria-live','polite');
    const host=document.createElement('div');host.setAttribute('aria-hidden','true');host.inert=true;host.style.cssText='position:absolute;left:-20000px;top:0;width:1100px;height:560px;visibility:hidden;pointer-events:none';
    el.replaceChildren(plot,hint,host);
    const chart=echarts.init(plot,null,{renderer:'canvas'});
    // the plan lives in an off-screen Gantt standing at this figure: the studio (T) opens on it, the bus carries it
    const hg=G().mount(host,spec.program,{gid,field:'program',anchor:el,fill:true});
    const offHg=hg.on(type=>{if(type!=='change'||disposed)return;spec={...spec,program:hg.getDoc()};
      try{m=K().exposurePlan(spec);}catch(e){status(e.message);return;}
      const S=store();if(S)S[gid]={...S[gid],program:clone(spec.program)};
      {const k=m.studies.findIndex(x=>x.key===picked);sel=k>=0?k:Math.min(sel,m.studies.length-1);}   // the picked study stays picked when the order changes
      draw();refreshTables(ref,spec.program);opts.onChange?.(clone(spec));});
    function status(msg=''){hint.textContent=msg;clearTimeout(hintTimer);if(msg)hintTimer=setTimeout(()=>{if(!disposed)hint.textContent='';},2600);}
    const unit=()=>global.KZCharts?.fluidUnit?.(el)??1;
    const font=(px,bold)=>`${bold?'bold ':''}${px}px ${TK().fonts.fallback_css}`;
    let textW=(s,px)=>[...String(s)].reduce((a,c)=>a+(c.charCodeAt(0)<0x2000?.56:1),0)*px;
    try{const c=document.createElement('canvas').getContext('2d');if(c)textW=(s,px)=>{c.font=font(px,true);return c.measureText(String(s)).width;};}catch{}

    function geometry(mm){
      const u=unit(),W=chart.getWidth(),H=chart.getHeight(),pg=mm.plan,inds=mm.indications.filter(i=>i.nda);
      // while a dot is dragged the count axis holds still (unless the candidate outgrows it), so the dot stays under the pointer
      const x0=58*u,x1=W-150*u,X=t=>x0+(t-pg.from)/(pg.to-pg.from)*(x1-x0);
      // NDA chips (= Python xp_chips): centred on the vertical, inside the plot, on the lowest of ≤ 3 tiers that is free
      const chips=[];for(const [k,i] of inds.entries()){const lab=`${i.name} NDA ${i.nda.text}`,lw=textW(lab,14*u)+40*u,lx=Math.min(Math.max(X(i.nda.t)-lw/2,x0),x1+140*u-lw);
        let tier=[0,1,2].find(t=>chips.every(c=>c.tier!==t||lx>=c.lx+c.lw+6*u||lx+lw+6*u<=c.lx));if(tier==null)tier=2;chips.push({lx,lw,tier,lab,k});}
      const nt=Math.max(0,...chips.map(c=>c.tier)),y0=(46+22*nt)*u,y1=H-30*u,[top,st]=drag&&drag.g&&mm.max<=drag.g.top?[drag.g.top,drag.g.st]:nice(mm.max);
      return {u,W,H,pg,inds,chips,x0,x1,y0,y1,top,st,a:pg.from,b:pg.to,X,Y:v=>y1-v/top*(y1-y0)};
    }
    function option(mm,p){
      const g=geometry(mm),{u,X,Y,a,b,x0,x1,y0,y1,top,st,inds,chips}=g,T=TK(),cat=T.charts.categorical,treat=cat[0],risk=T.colors.risk,ink=T.colors.ink,muted=T.colors.muted||'#64676B';
      const accent=T.flagship?.accent_ink||'#9A4D00',icol={};mm.indications.forEach((i,k)=>{icol[i.key]=cat[k%cat.length];});
      const cut=a+p*(b-a),shown=mm.studies.filter(s=>s.t<=cut+1e-9),tgt=mm.targets.any;
      const pts=[[a,0],...shown.map(s=>[s.t,s.cum.any])];const last=shown.length?shown[shown.length-1].cum.any:0;pts.push([Math.max(cut,shown.length?shown[shown.length-1].t:a),last]);
      const gr=[],F=14*u;
      // NDA verticals with numbered chips, in one or two tiers so neighbours do not collide (as the static figure)
      inds.forEach((i,k)=>{const nx=X(i.nda.t),{lab,lw,lx,tier}=chips[k],ty=(12+tier*22)*u,on=i.nda.t<=cut+1e-9;
        gr.push({type:'line',z:1,silent:true,shape:{x1:nx,y1:ty+12*u,x2:nx,y2:y1},style:{stroke:'#8A949E',lineWidth:1.2,lineDash:[5,4],opacity:on?1:.25}});
        gr.push({type:'rect',z:3,silent:true,shape:{x:lx,y:ty-10*u,width:lw,height:20*u,r:10*u},style:{fill:i.key===mm.focus?'#FFF1DE':'#F3F4F6',opacity:on?1:.35}});
        gr.push({type:'circle',z:4,silent:true,shape:{cx:lx+11*u,cy:ty,r:8*u},style:{fill:icol[i.key],opacity:on?1:.35}});
        gr.push({type:'text',z:5,silent:true,x:lx+11*u,y:ty,style:{text:String(k+1),font:font(12*u,true),fill:'#fff',align:'center',verticalAlign:'middle',opacity:on?1:.35}});
        gr.push({type:'text',z:5,silent:true,x:lx+24*u,y:ty,style:{text:lab,font:font(F,true),fill:ink,verticalAlign:'middle',opacity:on?1:.35}});});
      if(tgt)gr.push({type:'text',z:5,silent:true,x:x1+8*u,y:Y(tgt)-9*u,style:{text:`${mm.target_label} ${n0(tgt)} ${mm.unit}`,font:font(F,true),fill:risk,verticalAlign:'middle'}});
      if(p>=1)gr.push({type:'text',z:5,silent:true,x:x1+8*u,y:Y(mm.totals.any)+10*u,style:{text:`累计 ${n0(mm.totals.any)} ${mm.unit}`,font:font(F,true),fill:ink,verticalAlign:'middle'}});
      // boxes already taken (flat steps of the line, the NDA value labels) so the first-reach label can avoid them (= the static figure)
      const taken=[];for(let j=1;j<pts.length;j++){const [p0,v0]=pts[j-1],[p1]=pts[j];taken.push([X(p0),Y(v0)-3*u,X(p1),Y(v0)+3*u]);}
      const ndaPts=inds.filter(i=>i.nda.t<=cut+1e-9).map(i=>{const ok=i.met.any??true,lab=n0(i.cum.any)+(ok?'':`（差 ${n0(i.gap.any)}）`),nx=X(i.nda.t),ly=Y(i.cum.any)-12*u,lw=textW(lab,F);
        // right of the ring unless the next study's riser would cut through the text; then left of it (= the static figure)
        const left=shown.some(s=>s.t>i.nda.t&&X(s.t)>nx+6*u&&X(s.t)<nx+14*u+lw),lx=left?nx-10*u:nx+10*u;
        gr.push({type:'text',z:6,silent:true,x:lx,y:ly,style:{text:lab,font:font(F,true),fill:ok?ink:risk,align:left?'right':'left',verticalAlign:'middle'}});taken.push(left?[lx-lw,ly-9*u,lx,ly+9*u]:[lx,ly-9*u,lx+lw,ly+9*u]);
        return {value:[i.nda.t,i.cum.any],ind:i.key,itemStyle:{color:'#fff',borderColor:ok?treat:risk,borderWidth:2*u}};});
      const fr=mm.first.any,frOn=tgt&&fr!=null&&fr<=cut+1e-9;
      if(frOn){const fl=`首次达到 ${K().ttext(fr+1e-7,mm.plan.granularity)}`,fw=textW(fl,F),fx=X(fr),ty=Y(tgt);
        // above-left of the diamond, else above-right, below-left, below-right: the first that clears the step line and the NDA labels
        const cands=[[fx-10*u,ty-11*u,'right'],[fx+10*u,ty-11*u,'left'],[fx-10*u,ty+13*u,'right'],[fx+10*u,ty+13*u,'left']];
        const box=c=>c[2]==='right'?[c[0]-fw,c[1]-9*u,c[0],c[1]+9*u]:[c[0],c[1]-9*u,c[0]+fw,c[1]+9*u];
        const hit=q=>taken.some(t=>q[0]<t[2]&&t[0]<q[2]&&q[1]<t[3]&&t[1]<q[3]),c=cands.find(c=>{const q=box(c);return !hit(q)&&q[0]>=x0&&q[2]<=x1+2*u;})||cands[0];
        gr.push({type:'text',z:6,silent:true,x:c[0],y:c[1],style:{text:fl,font:font(F,true),fill:accent,align:c[2],verticalAlign:'middle'}});}
      // years: a tick at each year start, the label in the middle of the year (as the static figure)
      const ticks=[],labs=[];for(let yr=Math.ceil(a/4);yr*4<=b;yr++){ticks.push(yr*4);if(yr*4+2<=b)labs.push(yr*4+2);}
      const yearOf=v=>String(K().ttext(v+1e-7,'quarter')).slice(0,4);
      return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:T.fonts.fallback_css,fontSize:16*u,color:T.colors.body},
        aria:{enabled:true,decal:{show:false},label:{description:data.description||'累计暴露阶梯图'}},
        grid:{left:x0,right:g.W-x1,top:y0,bottom:g.H-y1,outerBoundsMode:'none'},
        tooltip:{show:p===1&&!drag,trigger:'item',confine:true,textStyle:{fontSize:15*u},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3',formatter:tip},
        xAxis:{type:'value',min:a,max:b,splitLine:{show:false},axisLine:{lineStyle:{color:T.charts.axis,width:1.2}},axisTick:{show:true,customValues:ticks,length:5*u,lineStyle:{color:T.charts.axis}},
          axisLabel:{customValues:labs,formatter:v=>yearOf(v),fontSize:F,color:muted,margin:9*u}},
        yAxis:{type:'value',min:0,max:top,interval:st,splitLine:{lineStyle:{color:T.charts.grid}},axisLine:{show:false},axisTick:{show:false},axisLabel:{formatter:v=>n0(v),fontSize:F,color:muted,margin:8*u}},
        graphic:gr,
        series:[
          {id:'step',type:'line',step:'end',data:pts,symbol:'none',silent:true,z:2,lineStyle:{color:treat,width:2.6*u},
            markLine:tgt?{silent:true,symbol:'none',animation:false,lineStyle:{color:risk,type:'dashed',width:1.6},label:{show:false},data:[{yAxis:tgt}]}:undefined},
          {id:'studies',type:'scatter',z:4,data:shown.map((s,k)=>({value:[s.t,s.cum.any],k,itemStyle:{color:icol[s.ind],borderColor:k===sel&&(focused||drag)?ink:'#fff',borderWidth:(k===sel&&(focused||drag)?2.4:1.5)*u}})),
            symbolSize:11*u,cursor:'grab',emphasis:{scale:1.35}},
          {id:'nda',type:'scatter',z:5,data:ndaPts,symbolSize:14*u,cursor:'default'},
          {id:'first',type:'scatter',z:6,silent:true,symbol:'diamond',symbolSize:14*u,data:frOn?[[fr,tgt]]:[],itemStyle:{color:accent}}]};
    }
    function tip(p){
      if(p.seriesId==='studies'){const s=(preview||m).studies[p.data.k];if(!s)return '';
        const parts=[`<b>${esc(s.ind_name)}${s.lane===s.ind?'':' · '+esc(s.lane_name)} · ${esc(s.label)}</b>`,`样本量 ${n0(s.n)}${s.ctrl?` · 对照 ${K().pyRound(s.ctrl*100)}%`:''} · 暴露 ${n0(s.band.any)} 例`];
        if(s.band.w26!=null)parts.push(`≥26 周 ${n0(s.band.w26)}${s.band.w52!=null?` · ≥52 周 ${n0(s.band.w52)}`:''}`);
        parts.push(`计入 ${esc(s.at_text)} · 累计 ${n0(s.cum.any)} 例`,'<span style="color:#64676B">拖动调时间或例数 · T 编辑</span>');return parts.join('<br>');}
      if(p.seriesId==='nda'){const i=(preview||m).indications.find(x=>x.key===p.data.ind);if(!i)return '';
        return [`<b>${esc(i.name)} NDA ${esc(i.nda.text)}</b>`,...Object.keys(i.met).map(k=>`${K().XP_LABEL[k]} ${n0(i.cum[k])} / 目标 ${n0(m.targets[k])} ${i.met[k]?'✓':'· 差 '+n0(i.gap[k])}`)].join('<br>');}
      return '';
    }
    let focused=false,picked=null;
    function draw(p=progress){if(disposed)return;const s=m.studies[sel];if(s&&s.key!==picked){picked=s.key;try{hg.select(s.key);}catch{}}chart.setOption(option(preview||m,p),{notMerge:true});}
    function renderProgress(p){progress=Math.max(0,Math.min(1,p));draw();opts.onProgress?.(progress);}
    function finish(){cancelAnimationFrame(raf);raf=0;renderProgress(1);}
    function play(duration=TK().motion?.duration_ms?.data??1000){
      cancelAnimationFrame(raf);raf=0;if(disposed)return;if(matchMedia('(prefers-reduced-motion: reduce)').matches){finish();return;}
      let start=null;const tick=()=>{if(disposed)return;const now=performance.now();start??=now;const q=Math.min(1,(now-start)/duration);renderProgress(1-(1-q)**3);raf=q<1?requestAnimationFrame(tick):0;};
      renderProgress(0);raf=requestAnimationFrame(tick);
    }
    // ---- edits: a candidate plan from a study move; committed through the off-screen Gantt (undo, bus, studio)
    function barOf(doc,s){for(const l of doc.lanes)if(l.key===s.lane)for(const b of l.bars||[])if(b.key===s.key||(b.label||b.phase)===s.label&&!s.key)return b;return null;}
    function shiftText(t,du){if(!du)return t;const g=unitOf(t);let x=K().tspan(t,'时间')[0];for(let i=0;i<Math.abs(du);i++)x=G().step(x,g,Math.sign(du));return K().ttext(x+1e-7,g);}
    function moved(s,du,dex){
      const doc=clone(spec.program),b=barOf(doc,s);if(!b)return null;const x=b.exposure;
      if(du){b.start=shiftText(b.start,du);b.end=shiftText(b.end,du);if(x.at)x.at=shiftText(x.at,du);}
      if(dex){const ex0=s.band.any,ex=Math.max(0,ex0+dex),r=ex0?ex/ex0:1;
        if(x.exposed!=null){x.exposed=ex;x.n=Math.max(x.n,ex);}else x.n=Math.max(1,K().pyRound(ex/(1-(x.ctrl||0))));
        if(x.w26!=null)x.w26=Math.min(K().pyRound(x.w26*r),x.exposed??K().pyRound(x.n*(1-(x.ctrl||0))));if(x.w52!=null)x.w52=Math.min(K().pyRound(x.w52*r),x.w26??x.exposed??x.n);}
      try{const mm=K().exposurePlan({...spec,program:doc});return {doc,mm};}catch(e){return {error:e.message};}
    }
    const label=s=>`${s.ind_name} · ${s.label}`;
    function commit(c,msg){if(!c||c.error){status(c?.error||'这项研究不在计划里');return false;}hg.setDoc(c.doc,{message:msg});status(msg+' · ⌘Z 撤销');return true;}
    const pxUnit=(s,g)=>(g.x1-g.x0)/(g.b-g.a)*UNIT_LEN[unitOf(barOf(spec.program,s)?.end||'Q')];
    chart.on('mousedown',p=>{if(p.seriesId!=='studies'||progress<1)return;const ev=p.event?.event;if(!ev)return;sel=p.data.k;const r=plot.getBoundingClientRect();
      drag={k:sel,s:m.studies[sel],x:ev.clientX,y:ev.clientY,mode:null,cand:null,g:geometry(m),r};plot.style.cursor='grabbing';
      addEventListener('pointermove',onMove,true);addEventListener('pointerup',onUp,true);addEventListener('keydown',onEsc,true);});
    function onMove(e){if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(!drag.mode){if(Math.hypot(dx,dy)<6)return;drag.mode=Math.abs(dx)>=Math.abs(dy)?'time':'n';}
      let c;if(drag.mode==='time'){const du=Math.round(dx/pxUnit(drag.s,drag.g));c=du?moved(drag.s,du,0):null;if(c&&!c.error)c.msg=`${label(drag.s)}：${du>0?'推后':'提前'} ${Math.abs(du)} 个${{quarter:'季度',month:'月',day:'日'}[unitOf(barOf(spec.program,drag.s).end)]}`;}
      else{const dv=Math.round(-dy/(drag.g.y1-drag.g.y0)*drag.g.top/10)*10;c=dv?moved(drag.s,0,dv):null;if(c&&!c.error)c.msg=`${label(drag.s)}：暴露 ${n0(drag.s.band.any)} → ${n0(Math.max(0,drag.s.band.any+dv))} 例`;}
      if(c&&c.error){status(c.error);return;}drag.cand=c;preview=c?c.mm:null;if(c)status(c.msg);draw();}
    function endDrag(){removeEventListener('pointermove',onMove,true);removeEventListener('pointerup',onUp,true);removeEventListener('keydown',onEsc,true);plot.style.cursor='';}
    function onUp(){if(!drag)return;const c=drag.cand;endDrag();drag=null;preview=null;if(c)commit(c,c.msg);else draw();}
    function onEsc(e){if(e.key!=='Escape'||!drag)return;e.preventDefault();e.stopPropagation();endDrag();drag=null;preview=null;draw();status('已取消');}
    function openEditor(){const S=global.KZGanttStudio;if(!S){status('编辑台未加载（kz-gantt-studio.js）');return;}const s=m.studies[sel];S.open(hg,{focus:s?.key});}
    chart.on('dblclick',p=>{if(p.seriesId==='studies')sel=p.data.k;openEditor();});
    chart.on('click',p=>{if(p.seriesId==='studies'){sel=p.data.k;draw();}opts.onDataClick?.(p,clone(spec));});
    plot.addEventListener('focus',()=>{focused=true;draw();});plot.addEventListener('blur',()=>{focused=false;if(!disposed)draw();});
    plot.addEventListener('keydown',e=>{
      const s=m.studies[sel];
      if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'){e.preventDefault();e.stopPropagation();e.shiftKey?hg.redo():hg.undo();status(e.shiftKey?'已重做':'已撤销');return;}
      if(e.key==='Enter'){e.preventDefault();e.stopPropagation();openEditor();return;}
      if(e.key==='Home'||e.key==='End'){e.preventDefault();e.stopPropagation();sel=e.key==='Home'?0:m.studies.length-1;draw();return;}
      if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();e.stopPropagation();if(!s)return;
      const h=e.key==='ArrowLeft'||e.key==='ArrowRight',d=e.key==='ArrowRight'||e.key==='ArrowUp'?1:-1;
      if(!e.shiftKey){if(h){sel=(sel+d+m.studies.length)%m.studies.length;draw();const t=m.studies[sel];status(`${label(t)} · ${t.at_text} · 暴露 ${n0(t.band.any)} 例`);}return;}
      const c=h?moved(s,d,0):moved(s,0,10*d);if(c&&!c.error)commit(c,h?`${label(s)}：${d>0?'推后':'提前'}一个单位`:`${label(s)}：暴露 ${d>0?'+':'−'}10 例`);else status(c?.error||'');});
    // off-figure, the plan bus may change the plan (a Gantt of the same program id was edited): the hidden Gantt
    // follows it (KZGantt subscribes itself), which redraws here through offHg
    const ro=new ResizeObserver(()=>{if(disposed)return;chart.resize();draw();});ro.observe(plot);
    const onRatio=()=>draw();global.addEventListener('kz:fluidratio',onRatio);
    draw();
    const api={chart,play,finish,renderProgress,getProgress:()=>progress,getData:()=>clone(spec),model:()=>m,gantt:hg,openEditor,
      select(k){if(!m.studies[k])throw Error('没有这项研究');sel=k;draw();},
      setData(next){hg.setDoc(clone(next.program),{message:'已更新'});},resize:()=>chart.resize(),pause:finish,resume(){},
      dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);clearTimeout(hintTimer);if(drag)endDrag();const errors=[];
        for(const f of [()=>ro.disconnect(),()=>global.removeEventListener('kz:fluidratio',onRatio),()=>offHg(),()=>hg.dispose(),()=>chart.dispose(),()=>el.replaceChildren(...prior),()=>{el.style.position=priorPos;}])try{f();}catch(e){errors.push(e);}
        if(errors.length)throw new AggregateError(errors,'累计暴露图清理未完全释放');}};
    return api;
  }
  // ---- SoA drilldown (the static SoA table with data-kz-explore, payload {kind:'soa', cols:[a,b], soa}): a visit header
  // opens that visit — period, week and window, key events, the treatment periods it falls in, then every assessment done
  // at it by section (with the cell's note); an assessment (in the visit layer or the row name) opens its schedule across
  // all visits with the visit it came from marked and the primary endpoint visits tinted. Enter / Space open, Esc goes back.
  let drill=null;
  const E=(tag,cls,text)=>global.KZDrilldown?.element?global.KZDrilldown.element(tag,cls,text):Object.assign(document.createElement(tag),cls?{className:cls}:{},text!=null?{textContent:text}:{});
  function dd(fig){if(!drill&&global.KZDrilldown)drill=new global.KZDrilldown.Drilldown({host:fig.closest('.kz')||document.body});return drill;}
  const markText=v=>v===1||v===true?'●':typeof v==='string'?v:'';
  function soaModel(fig){const D=global.KZ_DECK_DATA||{},x=D[fig.dataset.kzExplore];if(!x||x.kind!=='soa')return null;if(!fig._kzSoa)fig._kzSoa={x,m:K().soa(x.soa)};return fig._kzSoa;}
  function visitLayer(fig,i){
    const {x,m}=soaModel(fig),v=x.soa.visits[i],rows=x.soa.rows;
    return {id:`soa-v${i}`,title:`${v.v} · ${v.week}`,render(sec,d){
      sec.classList.add('kz-xp-drill');
      const meta=E('p','kz-xp-meta',[v.period,v.window?`窗口 ${v.window}`:null].filter(Boolean).join(' · '));sec.append(meta);
      const chips=E('div','kz-xp-chips');
      if(m.primary.includes(i))chips.append(E('span','kz-xp-chip is-primary','主要终点访视'));
      for(const e of m.events.filter(e=>e.i===i&&!(e.kind==='primary'&&m.primary.includes(i))))chips.append(E('span','kz-xp-chip is-event',e.label));
      for(const b of m.bands.filter(b=>b.from<=i&&i<=b.to))chips.append(E('span',`kz-xp-chip is-${b.kind}`,b.label));
      if(chips.childNodes.length)sec.append(chips);
      for(const b of m.bands.filter(b=>b.from<=i&&i<=b.to&&b.text))sec.append(E('p','kz-xp-note',`${b.label}：${b.text}`));
      let section=null,list=null,n=0;
      for(const r of rows){
        if('section' in r){section=r.section;list=null;continue;}
        const mk=markText(r.at[i]);if(!mk)continue;
        if(!list){sec.append(E('h3','kz-xp-h',section||'评估'));list=E('ul','kz-xp-list');sec.append(list);}
        const li=E('li',r.item===m.focus?'is-focus':null),btn=E('button','kz-xp-item');btn.type='button';
        btn.append(E('span',null,r.item));if(mk!=='●')btn.append(E('small',null,mk));
        btn.addEventListener('click',()=>d.push(itemLayer(fig,r.item,i),btn));li.append(btn);list.append(li);n++;
      }
      if(!n)sec.append(E('p','kz-xp-note','这次访视没有安排评估。'));
      return {};
    }};
  }
  function itemLayer(fig,item,from){
    const {x,m}=soaModel(fig),r=x.soa.rows.find(r=>r.item===item),vs=x.soa.visits;
    return {id:`soa-i-${item}`,title:item,render(sec){
      sec.classList.add('kz-xp-drill');
      const sch=vs.map((v,j)=>markText(r.at[j])).filter(Boolean).length;
      sec.append(E('p','kz-xp-meta',`共 ${sch} 次访视安排${from!=null?` · 标出的是 ${vs[from].v}`:''}`));
      const wrap=E('div','kz-xp-scroll'),t=E('table','kz-xp-table'),hr=E('tr'),br=E('tr');
      vs.forEach((v,j)=>{const th=E('th',[m.primary.includes(j)?'is-primary':'',j===from?'is-hit':''].join(' ').trim()||null);th.append(E('b',null,v.v),E('small',null,v.week));hr.append(th);
        const td=E('td',[m.primary.includes(j)?'is-primary':'',j===from?'is-hit':''].join(' ').trim()||null,markText(r.at[j])||'·');if(!markText(r.at[j]))td.classList.add('is-empty');br.append(td);});
      const th=E('thead'),tb=E('tbody');th.append(hr);tb.append(br);t.append(th,tb);wrap.append(t);sec.append(wrap);
      const mk=f=>[...String(f)][0],fn=(x.soa.footnotes||[]).filter(f=>/[^\u0000-\u024f\u3000-\u9fff]/.test(mk(f))&&(item.includes(mk(f))||r.at.some(a=>typeof a==='string'&&a.includes(mk(f)))));   // footnotes whose marker (ᵃ ᵇ …) the row carriesif(fn.length)sec.append(E('p','kz-xp-note',fn.join('；')));
      return {};
    }};
  }
  function decorate(fig){
    if(fig.dataset.kzExploreReady)return;const S=soaModel(fig);if(!S)return;fig.dataset.kzExploreReady='true';
    const [a,b]=S.x.cols,head=[...fig.querySelectorAll('thead tr')].at(-1);if(!head)return;
    [...head.children].slice(1).forEach((th,j)=>{const i=a+j;if(i>=b)return;th.dataset.kzVisit=String(i);th.tabIndex=0;th.setAttribute('role','button');th.classList.add('kz-xp-hot');
      th.setAttribute('aria-label',`查看 ${S.x.soa.visits[i].v}（${S.x.soa.visits[i].week}）的评估`);});
    const names=new Set(S.x.soa.rows.filter(r=>!('section' in r)).map(r=>r.item));
    for(const tr of fig.querySelectorAll('tbody tr')){const td=tr.children[0];const t=td?.textContent.trim();if(td&&td.colSpan===1&&names.has(t)){td.dataset.kzItem=t;td.tabIndex=0;td.setAttribute('role','button');td.classList.add('kz-xp-hot');td.setAttribute('aria-label',`查看「${t}」在各访视的安排`);}}
  }
  function scan(root=document){for(const fig of root.querySelectorAll?.('[data-kz-explore]')||[])try{decorate(fig);}catch(e){console.error(e);}}
  function openFrom(el){
    const fig=el.closest('[data-kz-explore]');if(!fig)return false;const d=dd(fig);if(!d)return false;
    if(el.dataset.kzVisit!=null){d.push(visitLayer(fig,+el.dataset.kzVisit),el);return true;}
    if(el.dataset.kzItem!=null){d.push(itemLayer(fig,el.dataset.kzItem,null),el);return true;}
    return false;
  }
  if(typeof document!=='undefined'){
    const ready=()=>scan();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
    document.addEventListener('click',e=>{const el=e.target.closest?.('[data-kz-explore] [data-kz-visit],[data-kz-explore] [data-kz-item]');if(el&&openFrom(el)){e.preventDefault();e.stopPropagation();}},true);
    document.addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const el=e.target.closest?.('[data-kz-explore] [data-kz-visit],[data-kz-explore] [data-kz-item]');if(el&&openFrom(el)){e.preventDefault();e.stopPropagation();}},true);
  }
  // ---- KZLongitudinal: the longitudinal family in HTML (kinds longitudinal / longitudinal-diff / lab-boxplot / lab-multiples
  // / completeness; model KZClinical.longitudinal = Python diagram_long). ECharts on the true time axis, the primary visit
  // tinted, reference range and lines, n per visit under the axis; hover a point for its values; click a point: the
  // drilldown table (visits × arms, n, the difference rows) with the clicked cell marked; 编辑数据 turns the cells into
  // inputs (validated by the contract; the figure, KZ_DECK_DATA and the table follow), 复制数据 copies the JSON.
  const LONG_KINDS=['longitudinal','longitudinal-diff','lab-boxplot','lab-multiples','completeness'];
  const fmtv=(v,st)=>{const d=st>=1?0:Math.min(3,Math.max(1,-Math.floor(Math.log10(st)+1e-9)));const s=Number(v).toFixed(d);return /^-0(\.0+)?$/.test(s)?'0':s.replace('-','−');};
  function longMount(el,data,opts={}){
    if(!global.echarts)throw Error('缺少随包 ECharts；不以 CSS 假图代替');
    let spec=clone(data);const kind=data.kind,multi=kind==='lab-multiples';
    const models=()=>multi?(spec.panels||[]).map(p=>K().longitudinal({...Object.fromEntries(['visits','arms','blinded','time_unit','primary'].filter(k=>k in spec).map(k=>[k,spec[k]])),...p})):[K().longitudinal(spec)];
    let ms=models();if(multi&&!(ms.length>=2&&ms.length<=9))throw Error('小倍数需要 2–9 个指标 panels');
    const gid=el.dataset?.kzChart,store=()=>gid&&global.KZ_DECK_DATA&&Object.prototype.hasOwnProperty.call(global.KZ_DECK_DATA,gid)?global.KZ_DECK_DATA:null;
    const prior=[...el.childNodes],priorPos=el.style.position,plot=document.createElement('div');if(getComputedStyle(el).position==='static')el.style.position='relative';plot.style.cssText='position:absolute;inset:0';el.replaceChildren(plot);
    const chart=echarts.init(plot,null,{renderer:'canvas'});let progress=1,raf=0,disposed=false,hit=null;
    const T=TK(),u=()=>global.KZCharts?.fluidUnit?.(el)??1,F=T.fonts.fallback_css,muted=T.colors.muted||'#64676B',ink=T.colors.ink;
    function axisX(m,g){const t0=m.t[0],t1=m.t[m.t.length-1],sp=(t1-t0)||1,pad=sp*.04;
      return {type:'value',gridIndex:g,min:t0-pad,max:t1+pad,splitLine:{show:false},axisLine:{onZero:false,lineStyle:{color:T.charts.axis,width:1.2}},
        axisTick:{customValues:m.t},axisLabel:{customValues:m.t,formatter:v=>{const j=m.t.findIndex(t=>Math.abs(t-v)<1e-9);return j<0?'':m.labels[j];},fontSize:14*u(),color:muted,
          rich:{}}};}
    function axisY(m,g,dom){const [lo,hi,st]=dom;return {type:'value',gridIndex:g,min:lo,max:hi,interval:st,axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:T.charts.grid}},axisLabel:{formatter:v=>fmtv(v,st),fontSize:14*u(),color:muted}};}
    // series for one model on grid g: per arm a line (gaps at null) and the interval whiskers / boxes (custom), dodged in pixels
    function armSeries(m,g,cut,{diff=false,dodgePx=7}={}){
      const out=[],arms=diff?m.arms.filter(a=>a.key in m.diff):m.arms,na=arms.length,box=m.box&&!diff;
      // boxes side by side per visit: the slot per arm is capped by the narrowest visit gap (same rule as the PPTX figure)
      const minGap=Math.min(...m.t.slice(1).map((t,j)=>t-m.t[j]));
      arms.forEach((a,k)=>{const col=m.color[a.key],rows=diff?m.diff[a.key]:m.rows[a.key],dpx=box?(k-(na-1)/2)*(Math.max(8,Math.min(22,60/na))+4):(k-(na-1)/2)*dodgePx;
        const pts=rows.map((c,j)=>c&&m.t[j]<=cut+1e-9?{value:[m.t[j],c.est],j,arm:a.key}:{value:[m.t[j],null],j,arm:a.key});
        if(!box)out.push({id:`${g}-${a.key}-line`,name:a.name,type:'line',xAxisIndex:g,yAxisIndex:g,data:pts,connectNulls:false,symbol:'circle',symbolSize:(a.key===m.focus?9:8)*u(),
          lineStyle:{color:col,width:(a.key===m.focus?2.6:2)*u(),type:diff?'dashed':'solid'},itemStyle:{color:col,borderColor:'#fff',borderWidth:1.5},z:4,
          symbolOffset:[dpx*u(),0],emphasis:{scale:1.4},animation:false});
        out.push({id:`${g}-${a.key}-iv`,name:a.name,type:'custom',xAxisIndex:g,yAxisIndex:g,z:3,animation:false,itemStyle:{color:col},
          data:rows.map((c,j)=>c&&m.t[j]<=cut+1e-9?{value:[m.t[j],c.lo,c.hi,c.est,c.q1??c.lo,c.q3??c.hi],j,arm:a.key}:null).filter(Boolean),
          renderItem:(p,api)=>{const [x,ylo]=api.coord([api.value(0),api.value(1)]),[,yhi]=api.coord([api.value(0),api.value(2)]),[,ye]=api.coord([api.value(0),api.value(3)]);const cx=x+dpx*u(),cap=3*u(),ns=diff&&api.value(1)<=0&&api.value(2)>=0;
            if(box){const [,q1]=api.coord([api.value(0),api.value(4)]),[,q3]=api.coord([api.value(0),api.value(5)]),slot=Math.min((Math.max(8,Math.min(22,60/na))+4)*u(),minGap*api.size([1,0])[0]*.92/na),bw=Math.max(4*u(),slot-4*u()),cx=x+(k-(na-1)/2)*slot;
              return {type:'group',children:[{type:'line',shape:{x1:cx,y1:yhi,x2:cx,y2:ylo},style:{stroke:col,lineWidth:1.4}},{type:'rect',shape:{x:cx-bw/2,y:q3,width:bw,height:Math.max(1,q1-q3),r:2},style:{fill:'#fff',stroke:col,lineWidth:1.6}},{type:'line',shape:{x1:cx-bw/2,y1:ye,x2:cx+bw/2,y2:ye},style:{stroke:col,lineWidth:2.4}}]};}
            const c2=ns?'#9AA1A8':col;return {type:'group',children:[{type:'line',shape:{x1:cx,y1:yhi,x2:cx,y2:ylo},style:{stroke:c2,lineWidth:(diff?2.4:1.4)*u()}},
              ...(diff?[]:[{type:'line',shape:{x1:cx-cap,y1:yhi,x2:cx+cap,y2:yhi},style:{stroke:col,lineWidth:1.4}},{type:'line',shape:{x1:cx-cap,y1:ylo,x2:cx+cap,y2:ylo},style:{stroke:col,lineWidth:1.4}}])]};}});});
      return out;
    }
    function decor(m,g,{diff=false}={}){
      const ma=[],ml=[];
      // the band stops short of a reference line on its edge (ULN = range hi), so the line never reads as a coloured edge bar (02 LG-02)
      const ins=v=>m.lines.some(l=>Math.abs(l.value-v)<1e-9)?(m.domain[1]-m.domain[0])*.02:0;
      // labels sit over the widest gap between visits (same rule as the PPTX figure), never on a whisker at the plot's end
      let gk=0;for(let j=1;j<m.t.length-1;j++)if(m.t[j+1]-m.t[j]>m.t[gk+1]-m.t[gk])gk=j;const ga=m.t[gk],gb=m.t[gk+1];
      if(!diff&&m.range){const r=m.range,rl=r.lo!=null?r.lo+ins(r.lo):m.domain[0],rh=r.hi!=null?r.hi-ins(r.hi):m.domain[1];ma.push([{yAxis:rl,itemStyle:{color:'#E8F1E4'}},{yAxis:rh}]);if(r.label)ma.push([{xAxis:ga,yAxis:rh,itemStyle:{color:'transparent'},label:{position:'insideTop',formatter:r.label,color:'#3D6B1F',fontSize:14*u()}},{xAxis:gb,yAxis:rl}]);}
      if(m.primary!=null){const tp=m.t[m.primary],sp=(m.t[m.t.length-1]-m.t[0])||1;ma.push([{xAxis:tp-sp*.018,itemStyle:{color:'#FFF1DE'},label:{show:!multi,position:'insideTop',formatter:'主要终点',color:'#9A4D00',fontWeight:'bold',fontSize:14*u()}},{xAxis:tp+sp*.018}]);}
      if(!diff)for(const l of m.lines){ml.push({yAxis:l.value,lineStyle:{color:'#C00000',type:'dashed',width:1.2},label:{show:false}});ml.push([{coord:[ga,l.value],lineStyle:{color:'transparent',width:0},label:{formatter:l.label,position:'insideMiddleTop',color:'#C00000',fontWeight:'bold',fontSize:14*u()}},{coord:[gb,l.value]}]);}
      if(diff||(m.domain[0]<0&&m.domain[1]>0))ml.push({yAxis:0,lineStyle:{color:'#9AA1A8',type:'solid',width:1.2},label:{show:false}});
      return {id:`${g}-decor`,type:'line',xAxisIndex:g,yAxisIndex:g,data:[],silent:true,markArea:{silent:true,data:ma},markLine:{silent:true,symbol:'none',data:ml},z:1};
    }
    function option(p){
      const U=u(),cut=p>=1?Infinity:null;let g=[],xa=[],ya=[],series=[],graphic=[],titles=[];
      const m0=ms[0],cutT=m=>p>=1?Infinity:m.t[0]+p*(m.t[m.t.length-1]-m.t[0]);
      const legendArms=kind==='longitudinal-diff'?m0.arms.filter(a=>a.key in m0.diff):m0.arms;
      const capOf=(m,diff)=>{const it=diff?'95% CI':K().LG_INTERVALS[m.measure.interval],st=diff?'与对照之差':m.measure.stat||(m.box?'中位数':'均值');return (m.unit?`${st}（${m.unit}）· ${it}`:`${st} · ${it}`)+(m.blinded?' · 盲态汇总，仅限内部':'');};
      if(kind==='completeness'){
        const m=m0;if(!m.expected)throw Error('数据完整性需要 expected（各访视应到人数）');const n=m.t.length,have=m.labels.map((_,j)=>m.arms.reduce((s,a)=>s+((m.rows[a.key][j]||{}).n||0),0)),ins=m.labels.map((_,j)=>Math.max(have[j],(m.in_study||m.expected)[j]));
        const solid=m.blinded?'#5F6B76':T.charts.categorical[0],k=Math.min(n,Math.max(1,Math.round(p*n)));
        return {...baseOpt(U),graphic:m.blinded?[{type:'text',silent:true,right:4*U,top:4*U,style:{text:'盲态汇总，仅限内部',font:`${14*U}px ${F}`,fill:muted,align:'right'}}]:[],grid:[{left:56*U,right:12*U,top:40*U,bottom:30*U}],legend:{top:0,left:56*U,itemWidth:12*U,itemHeight:12*U,textStyle:{fontSize:14*U,color:T.colors.body},data:['应到','仍在研究',`有${m.measure.label}数据`]},
          tooltip:{trigger:'axis',confine:true,textStyle:{fontSize:15*U},formatter:ps=>{const j=ps[0].dataIndex;return `<b>${esc(m.labels[j])}</b><br>应到 ${n0(m.expected[j])} · 仍在研究 ${n0(ins[j])} · 有数据 ${n0(have[j])}（${m.expected[j]?Math.round(have[j]/m.expected[j]*100):0}%）`;}},
          xAxis:[{type:'category',data:m.labels,axisLabel:{fontSize:14*U,color:muted},axisLine:{lineStyle:{color:T.charts.axis}}}],yAxis:[{type:'value',axisLabel:{fontSize:14*U,color:muted,formatter:v=>n0(v)},splitLine:{lineStyle:{color:T.charts.grid}}}],
          series:[{id:'exp',name:'应到',type:'bar',barWidth:'56%',data:m.expected.map((v,j)=>j<k?v:null),itemStyle:{color:'#fff',borderColor:'#9AA1A8',borderWidth:1,borderRadius:3},z:1,
              label:{show:true,position:'top',fontSize:14*U,fontWeight:'bold',color:ink,formatter:q=>m.expected[q.dataIndex]?Math.round(have[q.dataIndex]/m.expected[q.dataIndex]*100)+'%':'—'}},
            {id:'ins',name:'仍在研究',type:'bar',barWidth:'48%',barGap:'-92%',data:ins.map((v,j)=>j<k?v:null),itemStyle:{color:'#E7EBEE',borderRadius:2},z:2},
            {id:'have',name:`有${m.measure.label}数据`,type:'bar',barWidth:'40%',barGap:'-90%',data:have.map((v,j)=>j<k?v:null),itemStyle:{color:solid,borderRadius:2},z:3}]};
      }
      if(multi){
        const n=ms.length,cols=n>4?3:2,rows=Math.ceil(n/cols),W=chart.getWidth(),H=chart.getHeight(),gap=18*U,pw=(W-gap*(cols-1))/cols,ph=(H-26*U-gap*(rows-1))/rows;
        ms.forEach((m,i)=>{const r=Math.floor(i/cols),c=i%cols,px=c*(pw+gap),py=26*U+r*(ph+gap);
          g.push({left:px+48*U,top:py+34*U,width:pw-60*U,height:ph-(r===rows-1?56:44)*U});const ax=axisX(m,i),keep=m.t.filter((t,j)=>j===0||j===m.t.length-1||j===m.primary);xa.push({...ax,axisTick:{customValues:m.t},axisLabel:{...ax.axisLabel,customValues:keep,show:r===rows-1}});ya.push({...axisY(m,i,m.domain),splitNumber:2,axisLabel:{fontSize:13*U,color:muted,formatter:v=>fmtv(v,m.domain[2])}});
          graphic.push({type:'rect',silent:true,z:-1,shape:{x:px,y:py,width:pw,height:ph,r:10*U},style:{fill:'#fff',stroke:'#E7EBEE'}},
            {type:'text',silent:true,x:px+12*U,y:py+16*U,style:{text:m.measure.label+(m.unit?`（${m.unit}）`:''),font:`bold ${16*U}px ${F}`,fill:ink,verticalAlign:'middle'}},
            {type:'text',silent:true,x:px+pw-10*U,y:py+16*U,style:{text:K().LG_INTERVALS[m.measure.interval],font:`${14*U}px ${F}`,fill:muted,align:'right',verticalAlign:'middle'}});
          series.push(decor(m,i),...armSeries(m,i,cutT(m),{dodgePx:4}));});
        return {...baseOpt(U),grid:g,xAxis:xa,yAxis:ya,series,graphic,legend:{top:0,left:0,itemWidth:10*U,itemHeight:10*U,icon:'circle',textStyle:{fontSize:14*U,color:ink,fontWeight:'bold'},data:legendArms.map(a=>a.name)},tooltip:tipOpt(U)};
      }
      const diffOnly=kind==='longitudinal-diff',m=m0,nt=diffOnly?0:m.arms.length,dom=diffOnly?m.ddomain:m.domain;
      if(diffOnly&&!m.ddomain)throw Error('组间差图需要 diff（各治疗组对 comparator 的差与 95% CI）');
      // the diff panel keeps the n-table left edge too, so the two stacked time axes line up
      const labW=Math.max(...m.arms.map(a=>textW(m.blinded?"n":a.name,14*U)))+20*U;
      g=[{left:Math.max(56*U,labW),right:16*U,top:36*U,bottom:(30+nt*22)*U}];xa=[axisX(m,0)];ya=[axisY(m,0,dom)];
      series=[decor(m,0,{diff:diffOnly}),...armSeries(m,0,cutT(m),{diff:diffOnly})];
      graphic.push({type:'text',silent:true,right:4*U,top:4*U,style:{text:capOf(m,diffOnly),font:`${14*U}px ${F}`,fill:muted,align:'right'}});
      return {...baseOpt(U),grid:g,xAxis:xa,yAxis:ya,series,graphic,legend:{top:0,left:Math.max(56*U,labW),itemWidth:10*U,itemHeight:10*U,icon:'circle',selectedMode:!m.blinded,textStyle:{fontSize:14*U,color:ink,fontWeight:'bold'},data:legendArms.map(a=>a.name)},tooltip:tipOpt(U)};
    }
    const baseOpt=U=>({backgroundColor:'transparent',animation:false,textStyle:{fontFamily:F,fontSize:16*U,color:T.colors.body},aria:{enabled:true,decal:{show:false},label:{description:data.description||'历时变化图'}}});
    let textW=(s,px)=>[...String(s)].reduce((a,c)=>a+(c.charCodeAt(0)<0x2000?.56:1),0)*px;
    try{const c=document.createElement('canvas').getContext('2d');if(c)textW=(s,px)=>{c.font=`bold ${px}px ${F}`;return c.measureText(String(s)).width;};}catch{}
    function tipOpt(U){return {trigger:'item',confine:true,textStyle:{fontSize:15*U},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3',formatter:q=>{
      const d=q.data;if(!d||d.j==null)return '';const g=q.seriesIndex!=null?+String(q.seriesId).split('-')[0]:0,m=ms[g]||ms[0],diff=kind==='longitudinal-diff';
      const c=(diff?m.diff[d.arm]:m.rows[d.arm])[d.j];if(!c)return '';const a=m.arms.find(x=>x.key===d.arm),st=m.domain[2]/10;
      return `<b>${esc(a.name)} · ${esc(m.labels[d.j])}</b>`+(multi?` · ${esc(m.measure.label)}`:'')+'<br>'+(m.box&&!diff?`中位数 ${fmtv(c.est,st)} · Q1–Q3 ${fmtv(c.q1,st)}–${fmtv(c.q3,st)}`:`${fmtv(c.est,st)}（${fmtv(c.lo,st)}, ${fmtv(c.hi,st)}）`)+(c.n!=null?` · n=${c.n}`:'')+'<br><span style="color:#64676B">点击看历时表</span>';}};}
    // n per visit under the axis (one row per arm), placed from the axis after each render
    function nTable(){
      if(multi||kind==='completeness'||kind==='longitudinal-diff')return [];const m=ms[0],U=u(),out=[],H=chart.getHeight();
      m.arms.forEach((a,r)=>{const y=H-(nt(m)-r)*22*U+2*U;const sp=(m.t[m.t.length-1]-m.t[0])||1;out.push({type:'text',silent:true,x:chart.convertToPixel({gridIndex:0},[m.t[0]-sp*.04,0])[0]-8*U,y,style:{text:m.blinded?'n':a.name,font:`bold ${14*U}px ${F}`,fill:a.role==='comparator'?T.colors.body:m.color[a.key],align:'right',verticalAlign:'middle'}});
        m.t.forEach((t,j)=>{const c=m.rows[a.key][j],x=chart.convertToPixel({gridIndex:0},[t,0])[0];out.push({type:'text',silent:true,x,y,style:{text:c?String(c.n):'—',font:`${14*U}px ${F}`,fill:c?T.colors.body:muted,align:'center',verticalAlign:'middle'}});});});
      return out;
    }
    const nt=m=>m.arms.length;
    function draw(){if(disposed)return;const o=option(progress);chart.setOption(o,{notMerge:true});const extra=nTable();if(extra.length)chart.setOption({graphic:[...(o.graphic||[]),...extra]});}
    function renderProgress(q){progress=Math.max(0,Math.min(1,q));draw();opts.onProgress?.(progress);}
    function finish(){cancelAnimationFrame(raf);raf=0;renderProgress(1);}
    function play(duration=T.motion?.duration_ms?.data??1000){cancelAnimationFrame(raf);raf=0;if(disposed)return;if(matchMedia('(prefers-reduced-motion: reduce)').matches){finish();return;}
      let start=null;const tick=()=>{if(disposed)return;const now=performance.now();start??=now;const q=Math.min(1,(now-start)/duration);renderProgress(1-(1-q)**3);raf=q<1?requestAnimationFrame(tick):0;};renderProgress(0);raf=requestAnimationFrame(tick);}
    // ---- drilldown: the history table of the clicked measure, the clicked cell marked; editable
    function setSpec(next,msg){
      try{const t=multi?next.panels.map(p=>K().longitudinal({...Object.fromEntries(['visits','arms','blinded','time_unit','primary'].filter(k=>k in next).map(k=>[k,next[k]])),...p})):[K().longitudinal(next)];spec=next;ms=t;}
      catch(e){return e.message;}
      const S=store();if(S)S[gid]={...clone(spec),kind};draw();opts.onChange?.(clone(spec));return null;
    }
    function drillLayer(g,arm,j){
      const m=ms[g],diff=kind==='longitudinal-diff';
      return {id:`lg-${gid}-${g}`,title:`${m.measure.label}${m.unit?`（${m.unit}）`:''} · 历时表`,render(sec){
        sec.classList.add('kz-xp-drill');let editing=false;
        const meta=E('p','kz-xp-meta',`${m.measure.stat||(m.box?'中位数':'均值')} · ${K().LG_INTERVALS[m.measure.interval]}${m.blinded?' · 盲态汇总，仅限内部':''}${arm!=null?` · 标出的是 ${(m.arms.find(a=>a.key===arm)||{}).name} ${m.labels[j]}`:''}`);
        const bar=E('div','kz-xp-chips'),edit=E('button','kz-button',editing?'完成编辑':'编辑数据'),copy=E('button','kz-button','复制数据'),msg=E('p','kz-xp-note');edit.type=copy.type='button';
        bar.append(edit,copy);const wrap=E('div','kz-xp-scroll');sec.append(meta,bar,wrap,msg);
        const st=m.domain[2]/10,cellTxt=c=>c?(m.box?`${fmtv(c.est,st)}（${fmtv(c.q1,st)}–${fmtv(c.q3,st)}）`:`${fmtv(c.est,st)}（${fmtv(c.lo,st)}, ${fmtv(c.hi,st)}）`):'—';
        function render(){
          const mm=ms[g],t=E('table','kz-xp-table'),hr=E('tr');hr.append(E('th',null,'组'));mm.labels.forEach((l,jj)=>{const th=E('th',[mm.primary===jj?'is-primary':'',jj===j?'is-hit':''].join(' ').trim()||null);th.append(E('b',null,l),E('small',null,`${mm.t[jj]} ${mm.time_unit}`));hr.append(th);});
          const th=E('thead'),tb=E('tbody');th.append(hr);t.append(th,tb);
          for(const a of mm.arms){const tr=E('tr'),h=E('th',null,a.name);h.style.color=a.role==='comparator'?'':mm.color[a.key];tr.append(h);
            mm.labels.forEach((_,jj)=>{const c=mm.rows[a.key][jj],td=E('td',[mm.primary===jj?'is-primary':'',a.key===arm&&jj===j?'is-hit':''].join(' ').trim()||null);
              if(editing){const keys=mm.box?['lo','q1','est','q3','hi','n']:['est','lo','hi','n'],names=mm.box?['下须','Q1','中位','Q3','上须','n']:['估计','下限','上限','n'];
                const box_=E('div','kz-xp-edit');keys.forEach((k,q)=>{const i=E('input');i.type='number';i.step='any';i.value=c?c[k]:'';i.placeholder=names[q];i.setAttribute('aria-label',`${a.name} ${mm.labels[jj]} ${names[q]}`);
                  i.addEventListener('change',()=>{const next=clone(spec),tgt=multi?next.panels[g]:next,key=mm.box?'boxes':'series',vals=[...box_.querySelectorAll('input')].map(x=>x.value.trim());
                    tgt[key]={...tgt[key]};tgt[key][a.key]=[...tgt[key][a.key]];tgt[key][a.key][jj]=vals.every(v=>v==='')?null:vals.map((v,qq)=>qq===vals.length-1?parseInt(v,10):parseFloat(v));
                    const err=setSpec(next);msg.textContent=err?'没有改：'+err:`已更新 ${a.name} ${mm.labels[jj]}`;msg.classList.toggle('is-error',!!err);if(!err)render();});box_.append(i);});
                td.append(box_);}
              else{td.textContent=cellTxt(c);if(!c)td.classList.add('is-empty');if(c&&c.n!=null){td.append(E('small',null,`n=${c.n}`));}}
              tr.append(td);});tb.append(tr);}
          for(const [k,r] of Object.entries(mm.diff||{})){const a=mm.arms.find(x=>x.key===k),tr=E('tr','is-diff'),h=E('th',null,`${a.name} − ${(mm.arms.find(x=>x.key===mm.comp)||{}).name}`);tr.append(h);
            r.forEach((c,jj)=>{const td=E('td',[mm.primary===jj?'is-primary':'',diff&&k===arm&&jj===j?'is-hit':''].join(' ').trim()||null,c?`${fmtv(c.est,st)}（${fmtv(c.lo,st)}, ${fmtv(c.hi,st)}）`:'—');tr.append(td);});tb.append(tr);}
          wrap.replaceChildren(t);
        }
        edit.addEventListener('click',()=>{editing=!editing;edit.textContent=editing?'完成编辑':'编辑数据';render();});
        copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(JSON.stringify(spec,null,1));msg.textContent='已复制数据（JSON）';}catch{msg.textContent='浏览器不允许写剪贴板';}});
        render();return {};}};
    }
    chart.on('click',q=>{const d=q.data;if(!d||d.j==null)return;const g=+String(q.seriesId).split('-')[0]||0,dd_=dd(el);if(!dd_)return;hit=[g,d.arm,d.j];dd_.push(drillLayer(g,d.arm,d.j),el);opts.onDataClick?.(q,clone(spec));});
    const ro=new ResizeObserver(()=>{if(disposed)return;chart.resize();draw();});ro.observe(plot);const onRatio=()=>draw();global.addEventListener('kz:fluidratio',onRatio);
    draw();
    return {chart,play,finish,renderProgress,getProgress:()=>progress,getData:()=>clone(spec),model:()=>ms,openDrill:(g=0,arm=null,j=null)=>dd(el)?.push(drillLayer(g,arm,j),el),
      setData(next){const e=setSpec(clone(next));if(e)throw Error(e);},resize:()=>chart.resize(),pause:finish,resume(){},
      dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);const errors=[];for(const f of [()=>ro.disconnect(),()=>global.removeEventListener('kz:fluidratio',onRatio),()=>chart.dispose(),()=>el.replaceChildren(...prior),()=>{el.style.position=priorPos;}])try{f();}catch(e){errors.push(e);}
        if(errors.length)throw new AggregateError(errors,'历时变化图清理未完全释放');}};
  }
  // a table of a plan with no figure on the page still follows the plan bus
  if(typeof document!=='undefined'&&global.KZGantt?.subscribe)global.KZGantt.subscribe(null,doc=>refreshTables(doc.id,doc));
  global.KZExposure={mount,refreshTables};
  global.KZExplore={scan,open:openFrom};
  global.KZLongitudinal={mount:longMount,KINDS:LONG_KINDS};
})(typeof window!=='undefined'?window:globalThis);
