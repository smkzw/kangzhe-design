/* KZGantt — the live, editable Gantt (08 GANTT). ECharts custom series; one continuous time model in quarter units
   (year × 4 + quarter − 1; months are thirds, days a fraction of their quarter), intervals [start, end).
   Two data forms:
   · the plan contract (8.0, 08 GANTT-02): {from, to, granularity?, today?, phases?, lanes: [{key, name, note?, parent?,
     collapsed?, bars: [{key, phase, start, end, label?, color?, status?, progress?, baseline?}], milestones: [{key, at,
     label, kind?, icon?, risk?, major?, baseline?}]}]} — validated by runtime/kz-clinical.js (same rules as the static
     template), times written '2026Q3' / '2026-08' / '2026-08-15'. Edits write the times back as text at the plan's
     granularity, so the saved file stays readable and the PPTX template reads it unchanged.
   · the legacy quarter form (7.x): {min, max, tasks: [{id, label, start, end, color?, department?, row?}], rows?,
     milestones?, today?, legend?, taskColor?} — integer quarter indices; still mounted as before. The editing studio
     (kz-gantt-studio.js) turns it into the plan contract on its first edit.
   In place: select a bar, drag it or its ends (snapped to the granularity), ←/→ move by one unit, Shift+←/→ the end;
   Enter, double-click or T open the full-page studio. Optional layers (status, progress, baseline, two-level lanes) draw
   only when the data has them. */
(function(global){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  // 字号比率与 bridge 同一生命周期：fluid 下读 :root 的 --kz-un（含钳制与打印锁定），无 bridge 时退回自算。
  // 站点与流式页随宽度比例 --kz-sx 放大字号（13 WIDE-01），与 kz-charts 同一算法；固定舞台的 deck 保持 1。
  function wideUnit(el){
    const ts=KZ_TOKENS.wide&&KZ_TOKENS.wide.type_scale;
    if(!ts||el.closest?.('.deck,[data-fit]')||!(global.innerWidth>0))return 1;
    // Same line as --kz-sx in kz-tokens.css (tools/build_tokens.py): 1 at from_vw, `to` at to_vw, clamped to [1, max].
    return Math.min(ts.max,Math.max(1,1+(ts.to-1)*(global.innerWidth-ts.from_vw)/(ts.to_vw-ts.from_vw)));
  }
  function fluidUnit(el){
    // the editing studio sizes itself to the window (--su, kz-gantt-studio.js); its preview follows the studio, not the page
    const st=el.closest?.('.kz-gantt-studio');if(st){const v=parseFloat(st.style.getPropertyValue('--su'));return Number.isFinite(v)&&v>0?v:1;}
    if(!document.body||document.body.dataset.fit!=='fluid')return wideUnit(el);
    if(!(el.closest('.deck')||el.closest('.kz-dialog')))return 1; // 下钻弹层挂在 body 上，同属 fluid 页面
    const v=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--kz-un'));
    if(Number.isFinite(v)&&v>0)return v;
    return innerHeight/KZ_TOKENS.wide.htmlppt_reference_height;
  }
  const qindex=(year,q)=>{const y=Number(year),v=Number(q);if(!Number.isInteger(y)||y<1||!Number.isInteger(v)||v<1||v>4)throw Error('年份/季度无效');return y*4+v-1;};
  const fromIndex=i=>({year:Math.floor(i/4),quarter:(i%4+4)%4+1});
  const qlabel=i=>{const v=fromIndex(Math.round(i));return `${v.year} Q${v.quarter}`;};
  const qtext=i=>{const v=fromIndex(Math.floor(i));return `${v.year}Q${v.quarter}`;};
  // legacy quarter form (7.x) — unchanged rules
  function validate(data){
    if(isDoc(data)){K().program(data);return true;}
    if(!data||!Number.isInteger(data.min)||!Number.isInteger(data.max)||data.max<=data.min)throw Error('甘特轴范围无效');
    if(!Array.isArray(data.tasks)||!data.tasks.length)throw Error('甘特缺少任务');
    const ids=new Set();
    for(const t of data.tasks){
      if(!t.id||ids.has(t.id))throw Error('任务 id 缺失或重复');ids.add(t.id);
      if(typeof t.label!=='string'||!t.label.trim())throw Error('任务标签为空');
      if(t.start_known===false||t.end_known===false)throw Error('参考组件不渲染未知端点：任务 '+t.id+' 须由项目另行标示“待定”（08 GANTT-02）');
      if(!Number.isInteger(t.start)||!Number.isInteger(t.end)||t.start>=t.end||t.start<data.min||t.end>data.max)throw Error('任务时间越界或区间无效');
    }
    if(data.rows){
      const rids=new Set();
      for(const r of data.rows){if(!r.id||rids.has(r.id)||ids.has(r.id))throw Error('行 id 缺失或重复');if(typeof r.label!=='string'||!r.label.trim())throw Error('行标签为空');rids.add(r.id);}
      for(const t of data.tasks)if(!rids.has(t.row))throw Error('任务 '+t.id+' 的 row 不在 rows 里');
      for(const r of data.rows){const ts=data.tasks.filter(t=>t.row===r.id).sort((a,b)=>a.start-b.start);for(let i=1;i<ts.length;i++)if(ts[i].start<ts[i-1].end)throw Error('同一行的任务 '+ts[i-1].id+' 与 '+ts[i].id+' 时间重叠');}
    }
    for(const m of data.milestones||[]){
      if(!m.id||ids.has(m.id))throw Error('里程碑 id 缺失或重复');ids.add(m.id);
      if(typeof m.label!=='string'||!m.label.trim())throw Error('里程碑标签为空');
      if(m.task!==undefined){if(!data.tasks.some(t=>t.id===m.task)||!['start','end'].includes(m.edge))throw Error('里程碑 '+m.id+' 须绑定已有任务的 start 或 end');}
      else if(!Number.isInteger(m.at)||m.at<data.min||m.at>=data.max||(data.rows?!data.rows.some(r=>r.id===m.row):!data.tasks.some(t=>t.id===m.row)))throw Error('里程碑 '+m.id+' 须写 task+edge，或 row+at（at 在坐标轴内）');
    }
    if(data.today!==undefined&&data.today!==null&&(!Number.isInteger(data.today)||data.today<data.min||data.today>=data.max))throw Error('today 须是坐标轴内的季度序号');
    return true;
  }
  const isDoc=d=>!!d&&Array.isArray(d.lanes);
  const later=(fn,ms)=>typeof setTimeout==='function'?setTimeout(fn,ms):0,stopTimer=id=>{if(id&&typeof clearTimeout==='function')clearTimeout(id);};
  const K=()=>{if(!global.KZClinical)throw Error('计划数据需要 runtime/kz-clinical.js（在 kz-gantt.js 之前加载）');return global.KZClinical;};
  // ---- time arithmetic in quarter units (granularity quarter | month | day)
  const DAY=864e5,utc=(y,m,d)=>Date.UTC(y,m-1,d);
  const qdays=i=>{const y=Math.floor(i/4),q=(i%4+4)%4;return Math.round(((q===3?utc(y+1,1,1):utc(y,q*3+4,1))-utc(y,q*3+1,1))/DAY);};
  function snap(x,gran){if(gran==='quarter')return Math.round(x);if(gran==='month')return Math.round(x*3)/3;const i=Math.floor(x),n=qdays(i);return i+Math.round((x-i)*n)/n;}
  function step(x,gran,dir){
    if(gran==='quarter')return x+dir;if(gran==='month')return Math.round(x*3+dir)/3;
    const i=Math.floor(x+1e-9),n=qdays(i),k=Math.round((x-i)*n)+dir;
    if(k>=0&&k<=n)return k===n?i+1:i+k/n;const m=qdays(i-1);return i-1+(m-1)/m;
  }
  const unitOf=s=>/Q/.test(s)?'quarter':String(s).length===7?'month':'day',GR=['quarter','month','day'];
  const txt=(x,gran)=>K().ttext(x+1e-7,gran),txtEnd=(x,gran)=>K().ttext(x-1e-7,gran);
  // the 7.x quarter form as a plan contract (the studio edits plans; one lane per task unless rows were given)
  function fromLegacy(data){
    validate(data);const PH=KZ_TOKENS.charts?.phases||[];const lanes=!!data.rows,phased=data.tasks.every(t=>t.phase);
    const phases=phased?[...new Set(data.tasks.map(t=>t.phase))].slice(0,PH.length||5):['任务'];
    const colorOf=t=>t.color||data.taskColor||KZ_TOKENS.departments?.[t.department]?.color||KZ_TOKENS.colors.brand;
    const bar=t=>({key:t.id,phase:phased&&phases.includes(t.phase)?t.phase:phases[0],start:qtext(t.start),end:qtext(t.end-1),...(lanes||phased?{label:t.label}:{}),...(phased?{}:{color:colorOf(t)})});
    const msOf=rowId=>(data.milestones||[]).filter(m=>{const t=m.task!==undefined?data.tasks.find(x=>x.id===m.task):null;return t?(lanes?t.row:t.id)===rowId:m.row===rowId;})
      .map(m=>{const t=m.task!==undefined?data.tasks.find(x=>x.id===m.task):null;return {key:m.id,label:m.label,at:qtext(t?(m.edge==='start'?t.start:t.end-1):m.at),kind:m.kind||'other',...(m.risk?{risk:true}:{})};});
    const out={from:qtext(data.min),to:qtext(data.max-1),granularity:'quarter',phases,
      lanes:lanes?data.rows.map(r=>({key:r.id,name:r.label,...(r.note?{note:r.note}:{}),bars:data.tasks.filter(t=>t.row===r.id).map(bar),milestones:msOf(r.id)}))
        :data.tasks.map(t=>({key:'lane-'+t.id,name:t.label,bars:[bar(t)],milestones:msOf(t.id)}))};
    if(data.today!=null)out.today=qtext(data.today);
    return out;
  }
  // ---- the view both forms are drawn from: visible rows, bars and milestones with x positions in quarter units
  function viewOf(src){
    const PH=KZ_TOKENS.charts?.phases||[];
    if(isDoc(src)){
      const M=K().program(src),G=M.granularity,rows=[],tasks=[],ms=[];
      // one generic phase with colours of their own (a 7.x Gantt turned into a plan): no phase legend, no phase name in the bars
      const generic=M.phases.length===1&&M.lanes.every(l=>l.bars.every(b=>b.color));
      M.visible.forEach((ln,ri)=>{
        rows.push({id:ln.key,label:ln.name,note:ln.note,depth:ln.depth,parent:ln.children.length>0,collapsed:!!ln.collapsed});
        const bars=ln.bars.length?ln.bars:(ln.collapsed?ln.summary||[]:[]);
        for(const b of bars)tasks.push({id:b.key,row:ri,lane:ln.key,label:(b.label||(generic?'':b.phase))+(b.progress!=null?`${b.label||!generic?' · ':''}${+b.progress}%`:''),start:b.s,end:b.e,color:b.color||PH[b.pi],phase:b.phase,
          status:b.status,progress:b.progress,bs:b.bs,be:b.be,summary:!!b.summary,risk:!!b.risk});
        for(const m of [...ln.milestones,...(ln.collapsed?ln.summary_ms||[]:[])])ms.push({id:m.key,row:ri,label:m.label,kind:m.kind,icon:m.icon,risk:!!m.risk,x:m.t+m.tw/2,t:m.t,bx:m.bt!=null?m.bt+m.btw/2:null});
      });
      return {doc:true,M,gran:G,min:M.from,max:M.to,rows,tasks,ms,lanes:true,plain:false,today:M.today,todayX:M.today==null?null:M.today+M.today_w/2,
        todayText:M.today==null?'':`当前 ${K().ttext(M.today+1e-7,src.today&&src.today!=='auto'&&GR.indexOf(unitOf(src.today))<GR.indexOf(G)?unitOf(src.today):G)}`,legend:generic?[]:M.used.map(pi=>({label:M.phases[pi],color:PH[pi]})),layers:M.layers,focus:M.focus};
    }
    const lanes=!!src.rows,rows=lanes?src.rows.map(r=>({id:r.id,label:r.label,note:r.note,depth:0})):src.tasks.map(t=>({id:t.id,label:t.label,depth:0}));
    const rowOf=t=>lanes?src.rows.findIndex(r=>r.id===t.row):src.tasks.findIndex(x=>x.id===t.id);
    const tasks=src.tasks.map(t=>({id:t.id,row:rowOf(t),label:t.label,start:t.start,end:t.end,color:t.color||src.taskColor||KZ_TOKENS.departments?.[t.department]?.color||KZ_TOKENS.colors.brand}));
    const ms=(src.milestones||[]).map(m=>{if(m.task!==undefined){const t=src.tasks.find(x=>x.id===m.task);return {id:m.id,row:rowOf(t),label:m.label,kind:m.kind,risk:!!m.risk,x:m.edge==='start'?t.start+.5:t.end-.5,t:m.edge==='start'?t.start:t.end-1};}
      return {id:m.id,row:lanes?src.rows.findIndex(r=>r.id===m.row):src.tasks.findIndex(t=>t.id===m.row),label:m.label,kind:m.kind,risk:!!m.risk,x:m.at+.5,t:m.at};});
    return {doc:false,gran:'quarter',min:src.min,max:src.max,rows,tasks,ms,lanes,plain:!lanes,today:src.today??null,todayX:src.today!=null?src.today+.5:null,
      todayText:src.today!=null?`当前 ${qtext(src.today)}`:'',legend:src.legend||[],layers:{},focus:null};
  }
  // texts bound to the plan (08 GANTT-07): <span data-kz-bind="expr"> written by the template build
  // (diagram_clinical.bind_text, same rules): {key} a milestone's date or a phase's start–end, {key.start|end},
  // {gap:a,b} b − a in the plan's granularity
  const cn=v=>{const u=unitOf(v);return u==='quarter'?v:u==='month'?`${v.slice(0,4)} 年 ${+v.slice(5,7)} 月`:`${v.slice(0,4)} 年 ${+v.slice(5,7)} 月 ${+v.slice(8,10)} 日`;};
  function bindValue(expr,doc){
    const items=new Map();for(const l of doc.lanes){for(const b of l.bars||[])items.set(b.key,['bar',b]);for(const m of l.milestones||[])items.set(m.key,['ms',m]);}
    const raw=ref=>{const [key,part]=ref.split('.');const it=items.get(key);if(!it)return null;const [k,o]=it;if(k==='ms')return part?null:[o.at,null];
      return part==='start'?[o.start,'start']:part==='end'?[o.end,'end']:[o.start,o.end];};
    if(expr.startsWith('gap:')){const [a,b]=expr.slice(4).split(','),pt=ref=>{const r=raw(ref);if(!r)return null;const s=K().tspan(r[0],'时间');return r[1]==='end'?s[1]:s[0];};
      const pa=pt(a),pb=pt(b);if(pa==null||pb==null)return null;const g=K().program(doc).granularity;
      if(g==='day'){const n=Math.abs(Math.round((Date.parse(K().ttext(pb+1e-7,'day'))-Date.parse(K().ttext(pa+1e-7,'day')))/DAY));return `${n} 天`;}
      return `${Math.abs(Math.round((pb-pa)*(g==='month'?3:1)))} ${g==='month'?'个月':'个季度'}`;}
    const r=raw(expr);if(!r)return null;return r[1]===null||r[1]==='start'||r[1]==='end'?cn(r[0]):`${cn(r[0])}–${cn(r[1])}`;
  }
  const live=new Set();
  // the plan bus: every Gantt and exposure figure on the page that carries the same program id follows one change
  // (KZ_DECK_DATA entries of that id too: a plan, or a figure whose `program` is that plan), so a deck with the
  // development-plan Gantt and the cumulative exposure shares one data base. A plan without id stays local.
  const bus=new Set();let relaying=false;
  function publish(doc,from){
    if(relaying||!doc||doc.id==null||!Array.isArray(doc.lanes))return;relaying=true;
    try{const S=global.KZ_DECK_DATA;if(S)for(const [k,v] of Object.entries(S)){if(v&&v.id===doc.id&&Array.isArray(v.lanes))S[k]=clone(doc);else if(v&&v.program&&v.program.id===doc.id)S[k]={...v,program:clone(doc)};}
      for(const e of [...bus])if(e.from!==from){try{e.fn(clone(doc));}catch(error){console.error(error);}}}
    finally{relaying=false;}
  }
  function subscribe(from,fn){const e={from,fn};bus.add(e);return ()=>bus.delete(e);}
  function mount(root,input,options={}){
    if(!global.echarts)throw Error('缺少 ECharts');validate(input);
    let baseline=clone(input),src=clone(input),selected=null,marked=false,undo=[],redo=[],drag=null,disposed=false,levels=new Map(),V=viewOf(src);
    selected=V.tasks.find(t=>!t.summary)?.id??null;
    const abort=new AbortController(),signal=abort.signal;let progress=1,raf=0;const listeners=new Set();
    const mq=matchMedia('(prefers-reduced-motion: reduce)');
    const prior={children:[...root.childNodes],editing:root.dataset.kzEditing,editor:root.dataset.kzEditor,classes:['kz-gantt','kz-interactive'].filter(name=>!root.classList.contains(name))};
    let plot=null,chart=null,resize=null,api=null,hintTimer=0,offBus=null;
    const releaseAll=()=>{const errors=[];for(const release of [
      ()=>{if(raf){cancelAnimationFrame(raf);raf=0;}stopTimer(hintTimer);},
      ()=>abort.abort(),
      ()=>resize?.disconnect(),
      ()=>chart?.dispose(),
      ()=>{root.classList.remove(...prior.classes);for(const [key,value] of [['kzEditing',prior.editing],['kzEditor',prior.editor]]){if(value===undefined)delete root.dataset[key];else root.dataset[key]=value;}},
      ()=>root.replaceChildren(...prior.children),
      ()=>{if(api)live.delete(api);offBus?.();}
    ]){try{release();}catch(error){errors.push(error);}}return errors;};
    try{
    root.classList.add('kz-gantt','kz-interactive');root.dataset.kzEditing='true';root.dataset.kzEditor='closed';
    plot=document.createElement('div');plot.className='kz-gantt-plot';plot.tabIndex=0;plot.setAttribute('role','application');
    plot.setAttribute('aria-label','可编辑甘特图：点选阶段条，拖动整条或两端调整时间；左右方向键移动，Shift 加方向键调整结束；回车、双击或 T 打开编辑台');
    const hint=document.createElement('p');hint.className='kz-gantt-status';hint.setAttribute('aria-live','polite');
    const dirty=document.createElement('div');dirty.className='kz-dirty';dirty.hidden=true;
    const dirtyText=document.createElement('span');const undoB=document.createElement('button'),resetB=document.createElement('button');
    for(const [b,text] of [[undoB,'撤销'],[resetB,'还原全部']]){b.type='button';b.className='kz-button';b.textContent=text;}
    dirty.append(dirtyText,undoB,resetB);root.replaceChildren(plot,dirty,hint);
    // 13 FOLD-06: on scrolling pages the plot is as tall as its rows (scaled by --kz-sx, WIDE-01); HTML-PPT keeps the preset's fixed plot.
    const dense=KZ_TOKENS.layout&&KZ_TOKENS.layout.dense;
    const fitHeight=()=>{if(dense&&!root.closest('[data-fit="fluid"]')&&!options.fill)plot.style.height=Math.round((dense.gantt_axis_px+V.rows.length*dense.gantt_row_px*(V.ms.length?1.6:1))*wideUnit(root))+'px';};fitHeight();
    const ink=bg=>{const c=String(bg).replace('#','');if(c.length!==6)return KZ_TOKENS.colors.ink;const l=[0,2,4].map(i=>{const v=parseInt(c.slice(i,i+2),16)/255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4;});const L=.2126*l[0]+.7152*l[1]+.0722*l[2];return (L+.05)/.0565>=1.05/(L+.05)?(KZ_TOKENS.colors.ink||'#0F1115'):'#FFFFFF';};
    let measure=null;const textW=(s,px)=>{if(measure===null){const c=document.createElement('canvas');measure=c.getContext?c.getContext('2d'):false;}if(measure){measure.font=`${px}px ${KZ_TOKENS.fonts.fallback_css}`;return measure.measureText(s).width;}return [...s].reduce((a,ch)=>a+(ch.charCodeAt(0)<0x2000?.56:1),0)*px;};
    const iconPath=name=>global.KZIcons?.path?.(name)||null;
    // An icon path in a custom series: ECharts fits pathData into x/y/width/height only when the path is created, so an
    // update with the same pathData keeps the old place. Lay it out once in a fixed 24 box and move/scale the group.
    const iconEl=(d,x,y,size,style)=>({type:'group',x,y,scaleX:size/24,scaleY:size/24,children:[{type:'path',shape:{pathData:d,x:0,y:0,width:24,height:24},style:{...style,lineWidth:style.lineWidth*24/size}}]});
    const STATUS_ICON={done:'circle-check',active:'progress-check',delayed:'clock',risk:'alert-circle'};
    const GT=()=>({today:{line:'#A3A9B0',width:1.2,dash:[5,4],pill:'#EEF0F2',text:'#555A60',...KZ_TOKENS.gantt?.today},progress:{fill:'#B85C00',track:'#FFFFFF',track_opacity:.65,height:4,...KZ_TOKENS.gantt?.progress}});
    // the legend explains every layer that is drawn: phases, then plan (after today), 原计划, 进度 and the statuses in use
    function legendItems(){
      const out=V.legend.map(l=>({kind:'phase',label:l.label,color:l.color}));if(!V.doc)return out;
      const mid=(KZ_TOKENS.charts?.phases||[])[2]||'#FFA916',used=new Set(V.tasks.map(t=>t.status));
      if(V.todayX!=null&&V.tasks.some(t=>!t.summary&&t.end>V.todayX))out.push({kind:'plan',label:'计划',color:mid});
      if(V.layers?.baseline)out.push({kind:'ghost',label:'原计划'});
      if(V.layers?.progress)out.push({kind:'progress',label:'进度'});
      for(const [k,l] of [['done','已完成'],['active','进行中'],['delayed','延迟'],['risk','风险']])if(used.has(k))out.push({kind:'status',status:k,label:l});
      return out;
    }
    function swatch(l,x,y,unit){
      const P=GT().progress,muted=KZ_TOKENS.colors.muted||'#64676B';
      if(l.kind==='plan')return [{type:'rect',shape:{x,y:4*unit+y,width:14*unit,height:12*unit,r:3},style:{fill:l.color,opacity:.45,stroke:l.color,lineWidth:1.2,lineDash:[3,2]}}];
      if(l.kind==='ghost')return [{type:'rect',shape:{x,y:7*unit+y,width:14*unit,height:6*unit,r:2},style:{fill:'none',stroke:muted,lineWidth:1.1,lineDash:[3,2]}}];
      if(l.kind==='progress')return [{type:'rect',shape:{x,y:4*unit+y,width:14*unit,height:12*unit,r:3},style:{fill:(KZ_TOKENS.charts?.phases||[])[2]||'#FFA916'}},
        {type:'rect',shape:{x:x+2*unit,y:y+11*unit,width:10*unit,height:3*unit,r:1.5*unit},style:{fill:P.track,opacity:P.track_opacity}},{type:'rect',shape:{x:x+2*unit,y:y+11*unit,width:6*unit,height:3*unit,r:1.5*unit},style:{fill:P.fill}}];
      // the graphic component has no path element: the status icon goes in as a small SVG image
      if(l.kind==='status'){const ip=iconPath(STATUS_ICON[l.status]);if(!ip)return [];const col=l.status==='risk'?KZ_TOKENS.colors.risk:KZ_TOKENS.colors.ink;
        const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${ip}"/></svg>`;
        return [{type:'image',style:{image:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg),x:x-unit,y:y+unit,width:16*unit,height:16*unit}}];}
      return [{type:'rect',shape:{x,y:4*unit+y,width:14*unit,height:12*unit,r:3},style:{fill:l.color}}];
    }
    chart=echarts.init(plot,null,{renderer:'canvas'});
    const task=()=>V.tasks.find(t=>t.id===selected);
    const ghost=()=>!!V.layers.baseline,marks=()=>V.ms.length>0;
    const barBox=(unit,band)=>marks()||ghost()?{h:ghost()?Math.min(28*unit,band*.34):Math.min(34*unit,band*.42),dy:band*.2-(ghost()?5*unit:0)}:{h:Math.min(40*unit,band*.62),dy:0};
    function countDirty(){
      if(!isDoc(src)&&!isDoc(baseline))return src.tasks.filter(t=>{const b=baseline.tasks.find(x=>x.id===t.id);return !b||t.start!==b.start||t.end!==b.end;}).length;
      const flat=d=>{const m=new Map();const D=isDoc(d)?d:fromLegacy(d);for(const l of D.lanes){m.set(l.key,JSON.stringify({...l,bars:0,milestones:0}));for(const b of l.bars||[])m.set(b.key,JSON.stringify(b));for(const x of l.milestones||[])m.set(x.key,JSON.stringify(x));}return m;};
      const a=flat(src),b=flat(baseline);let n=0;for(const [k,v] of a)if(b.get(k)!==v)n++;for(const k of b.keys())if(!a.has(k))n++;return n;
    }
    // a short status line (bottom left, fades after a moment): what an edit did, or why it was refused
    function status(message=''){if(message!==hint.textContent){hint.textContent=message;stopTimer(hintTimer);if(message)hintTimer=later(()=>{if(!disposed)hint.textContent='';},2600);}const n=countDirty();dirty.hidden=!n||!!drag;dirtyText.textContent=`已修改 ${n} 项`;undoB.disabled=!undo.length;}
    // the page's data store (KZ_DECK_DATA[gid], as deck.js / kz-flagship.js mount from it) follows every change, so a
    // slide that remounts its Gantt on re-entry shows the edit; the studio saves the same object into the file
    // options.gid / options.field: a Gantt kept for another figure's plan (the exposure figure's T editing) writes
    // KZ_DECK_DATA[gid][field] instead of replacing the entry
    const gid=options.gid??root.dataset?.kzGantt,store=()=>gid&&global.KZ_DECK_DATA&&Object.prototype.hasOwnProperty.call(global.KZ_DECK_DATA,gid)?global.KZ_DECK_DATA:null;
    function bindTexts(){if(!isDoc(src))return;const scope=root.closest?.('.slide')||root.closest?.('section,main')||document;
      for(const el of scope.querySelectorAll?.('[data-kz-bind]')||[]){if(root.contains(el))continue;let v=null;try{v=bindValue(el.dataset.kzBind,src);}catch{}if(v!=null&&el.textContent!==v)el.textContent=v;}}
    const emit=(type,detail)=>{if(type==='change'){const S=store();if(S){if(options.field)S[gid]={...S[gid],[options.field]:clone(src)};else S[gid]=clone(src);}bindTexts();global.KZGanttStudio?.noteChange?.(api);if(options.bus!==false)publish(src,api);}for(const fn of listeners){try{fn(type,detail);}catch(error){console.error(error);}}};
    function draw(){
      if(disposed)return;
      const unit=fluidUnit(root),W=chart.getWidth(),H=chart.getHeight?.()??0,left=(W<480?96:V.lanes?190:126)*unit,band=(W-left-24*unit)/(V.max-V.min);
      // the legend wraps before the top-right corner, where the 已修改 / 撤销 / 还原 bar appears after an edit (so the
      // first edit does not reflow the chart)
      const legend=legendItems(),right=W-24*unit,nrows=V.rows.length,lw=it=>34*unit+textW(it.label,14*unit),room=Math.max(240*unit,right-left-(options.fill?0:300*unit));
      const lines=legend.length?legend.reduce((a,it)=>{const w=lw(it);if(a.x>0&&a.x+w>room){a.n++;a.x=0;}a.x+=w;return a;},{n:1,x:0}).n:0;
      const top=(legend.length?38+26*lines:38)*unit;
      // milestone labels per row: centred over the glyph, else nudged right or left, else starting or ending at it, else one
      // line up (≤3 lines), kept inside the plot and clear of the today pill. A label with no free place is left out (the
      // glyph stays): the static template proved the authored plan fits at full width, so this only happens when narrowed.
      levels=new Map();if(marks()){const byRow=new Map();for(const m of V.ms){if(!byRow.has(m.row))byRow.set(m.row,[]);byRow.get(m.row).push([m,left+(m.x-V.min)*band]);}
        const bandY=(H-top-44*unit)/nrows,bb=barBox(unit,bandY),tx=V.todayX!=null?left+(V.todayX-V.min)*band:null,
          pill=tx==null?null:(w=>[tx-w/2,tx+w/2])(textW(V.todayText,13*unit)+14*unit);
        for(const [row,list] of byRow){const taken=[],gy=top+(row+.5)*bandY+bb.dy-bb.h/2-1;list.sort((a,b)=>a[1]-b[1]);
          // the pill spans [top-22u, top-2u]: block it on the levels whose label box reaches into it; a level whose box
          // would climb past the bar of the row above (or into the legend line) is closed for the whole row
          const ceil=row?top+(row-.5)*bandY+bb.dy+bb.h/2+(ghost()?10*unit:0)+unit:top-26*unit;
          for(let lv=0;lv<3;lv++){const ty=gy-13*unit-lv*18*unit;if(ty-13*unit<ceil)taken.push([lv,-Infinity,Infinity]);else if(pill&&ty>top-22*unit&&ty-16*unit<top-2*unit)taken.push([lv,pill[0],pill[1]]);}
          for(const [m,cx] of list){const w=textW(m.label,14*unit)+8*unit;let pick=null;
            for(let lv=0;lv<3&&!pick;lv++)for(let dx of [0,w/2-8*unit,8*unit-w/2,w/2,-w/2]){dx+=Math.max(0,left-(cx+dx-w/2))-Math.max(0,cx+dx+w/2-right);const a=cx+dx-w/2,b=a+w;
              if(Math.abs(dx)<=w/2+2*unit&&!taken.some(([l,p,q])=>l===lv&&!(b<=p||a>=q))){pick={lv,dx,a,b};break;}}
            if(pick){taken.push([pick.lv,pick.a,pick.b]);levels.set(m.id,pick);}}}}
      // axis: quarters; months when the plan is written finer than quarters and a month is wide enough to label
      const months=V.gran!=='quarter'&&band/3>=22*unit,iv=months?1/3:1,F=KZ_TOKENS.fonts.fallback_css;
      const fmt=v=>{if(v>=V.max-1e-6)return '';const i=Math.floor(v+1e-6),q=fromIndex(i);
        if(months){const k=Math.round((v-i)*3),mo=(q.quarter-1)*3+k+1;return mo===1||(Math.abs(v-V.min)<1e-6&&mo!==1&&(13-mo)*band/3>=textW(`${q.year}.${mo}`,16*unit)/2+textW(String(q.year+1),16*unit)/2+10*unit)?(mo===1?String(q.year):`${q.year}.${mo}`):String(mo);}
        // an axis that opens mid-year names its first quarter, as long as it clears the next year label
        if(Math.abs(v-V.min)<1e-6&&q.quarter!==1){const gap=(5-q.quarter)*band,next=textW(String(q.year+1),16*unit)/2+10*unit;const s=`${q.year}Q${q.quarter}`;return gap>=textW(s,16*unit)/2+next?s:'';}
        // A bare year at Q1 reads as a year boundary, not a quarter; spell the quarter out when there is room.
        if(V.lanes)return q.quarter===1?String(q.year):(band>=44*unit?'Q'+q.quarter:'');
        return q.quarter===1?(band>=64*unit?`${q.year}Q1`:String(q.year)):(band>=30*unit?'Q'+q.quarter:'');};
      const rowLabel=(id)=>{const i=V.rows.findIndex(r=>r.id===id),r=V.rows[i];if(!r)return '';if(!V.lanes)return r.label;
        const caret=r.parent?`{c|${r.collapsed?'▸':'▾'}}`:'',pad=r.depth?'{i|}':'';return r.note?`${pad}${caret}{${r.depth?'k':'b'}|${r.label}}\n${pad}{s|${r.note}}`:`${pad}${caret}{${r.depth?'k':'b'}|${r.label}}`;};
      const gx0=(x,row,api)=>api.coord([x,row])[0];
      chart.setOption({animation:false,grid:{left,right:24*unit,top,bottom:44*unit},
        // phase legend on the top line; the today pill sits just above the plot, below it
        graphic:legend.length?[{type:'group',left:left,top:6*unit,children:legend.reduce((acc,l)=>{const w=lw(l);if(acc.x>0&&acc.x+w>room){acc.x=0;acc.y+=26*unit;}const x=acc.x,y=acc.y;acc.items.push(...swatch(l,x,y,unit),{type:'text',style:{text:l.label,x:x+20*unit,y:y+10*unit,verticalAlign:'middle',fontSize:14*unit,fill:KZ_TOKENS.colors.body,fontFamily:F}});acc.x+=w;return acc;},{x:0,y:0,items:[]}).items}]:[],textStyle:{fontFamily:F,fontSize:16*unit},
        xAxis:{type:'value',min:V.min,max:V.max,interval:iv,axisLabel:{fontSize:16*unit,color:KZ_TOKENS.colors.body,padding:[0,0,0,band*iv],formatter:fmt},axisTick:{show:false},
          splitLine:{lineStyle:{color:KZ_TOKENS.charts?.grid||'#E7EBEE',opacity:months?.6:1}},axisLine:{lineStyle:{color:KZ_TOKENS.charts?.axis||'#CED3D8'}}},
        yAxis:{type:'category',inverse:true,triggerEvent:true,data:V.rows.map(r=>r.id),axisLabel:{fontSize:16*unit,color:KZ_TOKENS.colors.body,formatter:rowLabel,
          // bars sit dy below the band centre when milestones ride above them; the lane name follows the bar (as the static figure)
          ...(barBox(unit,band).dy>0?{padding:[2*barBox(unit,band).dy,0,0,0]}:{}),...(V.lanes?{}:{width:(W<480?86:116)*unit,overflow:'break'}),
          ...(V.lanes?{rich:{b:{fontSize:16*unit,fontWeight:700,color:KZ_TOKENS.colors.ink,lineHeight:22*unit},k:{fontSize:15*unit,fontWeight:500,color:KZ_TOKENS.colors.body,lineHeight:22*unit},
            s:{fontSize:13*unit,color:KZ_TOKENS.colors.muted||'#6B7280',lineHeight:18*unit},c:{fontSize:13*unit,color:KZ_TOKENS.colors.muted||'#6B7280',padding:[0,6*unit,0,0]},i:{width:16*unit}}}:{})},axisTick:{show:false},axisLine:{show:false}},
        tooltip:{show:false},series:[{type:'custom',coordinateSystem:'cartesian2d',id:'kz-gantt-tasks',silent:true,
          renderItem(params,api){const row=api.value(0),t=V.tasks[api.value(3)],bandY=api.size([0,1])[1],bb=barBox(unit,bandY),start=api.coord([api.value(1),row]),end=api.coord([api.value(2),row]),height=bb.h;
            const cs={x:params.coordSys.x,y:params.coordSys.y,width:params.coordSys.width,height:params.coordSys.height};
            const rect=echarts.graphic.clipRectByRect({x:start[0],y:start[1]+bb.dy-height/2,width:end[0]-start[0],height},cs);
            if(!rect)return null;const color=t.color,sel=t.id===selected&&marked;
            if(V.plain)return {type:'rect',shape:{...rect,r:7*unit},style:{fill:color,opacity:.78,stroke:sel?KZ_TOKENS.colors.ink:'transparent',lineWidth:1.5}};
            const kids=[];
            // baseline (原计划): a dashed strip under the bar, and the slip at the later end
            if(t.bs!=null&&progress>=1&&(Math.abs(t.bs-t.start)>1e-9||Math.abs(t.be-t.end)>1e-9)){const g0=gx0(t.bs,row,api),g1=gx0(t.be,row,api),gy=rect.y+rect.height+3*unit;
              kids.push({type:'rect',shape:{x:g0+1,y:gy,width:Math.max(2,g1-g0-2),height:6*unit,r:2},style:{fill:'none',stroke:KZ_TOKENS.colors.muted||'#64676B',lineWidth:1.1,lineDash:[4,3]}});
              const d=slip(t.end-t.be,t.end);if(d)kids.push({type:'text',style:{text:d,x:Math.max(rect.x+rect.width,g1)+6*unit,y:gy+3*unit,verticalAlign:'middle',fontSize:13*unit,fontWeight:700,fill:t.end>t.be?KZ_TOKENS.colors.risk:'#3F7A1F',fontFamily:F}});}
            // the part after the today line is plan (light, dashed)
            const cut=V.todayX!=null?Math.max(rect.x,Math.min(rect.x+rect.width,gx0(V.todayX,row,api))):rect.x+rect.width;
            if(cut>rect.x)kids.push({type:'rect',shape:{x:rect.x,y:rect.y,width:cut-rect.x,height:rect.height,r:7*unit},style:{fill:color,opacity:t.summary?.85:.95}});
            if(cut<rect.x+rect.width)kids.push({type:'rect',shape:{x:cut,y:rect.y,width:rect.x+rect.width-cut,height:rect.height,r:7*unit},style:{fill:color,opacity:.45,stroke:color,lineWidth:1.2,lineDash:[5,4]}});
            if(t.progress!=null&&progress>=1){const P=GT().progress,tw0=rect.width-10*unit,ph=P.height*unit,ty=rect.y+rect.height-ph-3*unit,pw=tw0*t.progress/100;
              // progress: a thin in-bar track (white) with the done part in deep orange — read as a progress bar, not a rule
              kids.push({type:'rect',shape:{x:rect.x+5*unit,y:ty,width:tw0,height:ph,r:ph/2},style:{fill:P.track,opacity:P.track_opacity}});
              if(pw>.5)kids.push({type:'rect',shape:{x:rect.x+5*unit,y:ty,width:Math.max(ph,pw),height:ph,r:ph/2},style:{fill:P.fill}});}
            if(t.risk||t.status==='risk')kids.push({type:'rect',shape:{x:rect.x-1,y:rect.y-1,width:rect.width+2,height:rect.height+2,r:8*unit},style:{fill:'none',stroke:KZ_TOKENS.colors.risk,lineWidth:2}});
            if(sel)kids.push({type:'rect',shape:{...rect,r:7*unit},style:{fill:'none',stroke:KZ_TOKENS.colors.ink,lineWidth:1.8}});
            let iw=0,il=0;const ip=t.status&&STATUS_ICON[t.status]&&iconPath(STATUS_ICON[t.status]);
            if(ip&&rect.width>=30*unit&&progress>=1){const s=16*unit,mg=V.ms.filter(m=>m.row===row).map(m=>gx0(m.x,row,api)),free=x=>mg.every(g=>g<x-10*unit||g>x+s+10*unit);
              // at the end of the bar, else at its start when a milestone glyph sits there; no room at either end → no icon
              const ix=[rect.x+rect.width-s-4*unit,rect.x+4*unit].find(free);if(ix!==undefined){const onPlan=ix+s/2>cut;
              kids.push(iconEl(ip,ix,rect.y+rect.height/2-s/2,s,{fill:'none',stroke:t.status==='risk'?KZ_TOKENS.colors.risk:ink(onPlan?mixWhite(color):color),lineWidth:1.6,lineCap:'round',lineJoin:'round'}));if(ix>rect.x+rect.width/2)iw=s+4*unit;else il=s+4*unit;}}
            // centred, else in the widest free gap between the pinned milestone glyphs (as in the static template)
            const tw=textW(t.label,14*unit)+14*unit,gx=V.ms.filter(m=>m.row===row).map(m=>gx0(m.x,row,api)),gr=9.5*unit;
            const ink0=tw-14*unit,cuts=gx.map(g=>[g-gr,g+gr]).sort((a,b)=>a[0]-b[0]),gaps=[];let from=rect.x+7*unit+il;const to=rect.x+rect.width-7*unit-iw;
            for(const [a,b] of cuts){if(a>from)gaps.push([from,Math.min(a,to)]);from=Math.max(from,b);}if(to>from)gaps.push([from,to]);
            const mid=rect.x+il+(rect.width-iw-il)/2,fit=gaps.filter(([a,b])=>b-a>=ink0),home=fit.find(([a,b])=>a<=mid-ink0/2&&b>=mid+ink0/2);
            const cx=home?mid:fit.length?(([a,b])=>(a+b)/2)(fit.reduce((x,y)=>y[1]-y[0]>x[1]-x[0]?y:x)):undefined;
            if(cx!==undefined&&t.label)kids.push({type:'text',style:{text:t.label,x:cx,y:rect.y+rect.height/2,align:'center',verticalAlign:'middle',fontSize:14*unit,fontWeight:700,fill:cx<cut?ink(color):KZ_TOKENS.colors.ink,fontFamily:F}});
            return {type:'group',children:kids};},
          data:V.tasks.map((t,i,all)=>{const n=all.length,st=n>1?Math.min(.08,.4/(n-1)):0,local=Math.max(0,Math.min(1,(progress-i*st)/(1-(n-1)*st)));return [t.row,t.start,t.start+(t.end-t.start)*local,i];}),encode:{x:[1,2],y:0}},
          ...(marks()?[{type:'custom',coordinateSystem:'cartesian2d',id:'kz-gantt-milestones',silent:true,z:5,
            renderItem(params,api){const m=V.ms[api.value(2)],band=api.size([0,1])[1],bb=barBox(unit,band),p=api.coord([m.x,m.row]),gy=p[1]+bb.dy-bb.h/2-1,r=7*unit;
              const past=V.today!=null&&m.t<V.today,col=m.risk?KZ_TOKENS.colors.risk:KZ_TOKENS.colors.ink,filled=past||V.today==null,st={fill:filled?col:'#FFFFFF',stroke:col,lineWidth:1.6};
              const kids=[];
              if(m.bx!=null&&Math.abs(m.bx-m.x)>1e-9){const bx=api.coord([m.bx,m.row])[0];kids.push({type:'line',shape:{x1:bx,y1:gy,x2:p[0],y2:gy},style:{stroke:KZ_TOKENS.colors.muted||'#64676B',lineWidth:1,lineDash:[2,3]}},...glyphOf(m.kind,bx,gy,r*.8,{fill:'#FFFFFF',stroke:KZ_TOKENS.colors.muted||'#64676B',lineWidth:1.2}));}
              kids.push({type:'circle',shape:{cx:p[0],cy:gy,r:r+2.5*unit},style:{fill:'#FFFFFF'}});
              const ip=m.icon&&!(m.icon in GLYPHS)&&iconPath(m.icon);
              if(ip){kids.push({type:'circle',shape:{cx:p[0],cy:gy,r:r+1*unit},style:{fill:filled?col:'#FFFFFF',stroke:col,lineWidth:1.4}},
                iconEl(ip,p[0]-r*.78,gy-r*.78,r*1.56,{fill:'none',stroke:filled?'#FFFFFF':col,lineWidth:1.3,lineCap:'round',lineJoin:'round'}));}
              else kids.push(...glyphOf(m.icon||m.kind,p[0],gy,r,st));
              const lv=levels.get(m.id);
              // a thin surface halo keeps the label legible where it crosses the today line or a grid line
              if(lv)kids.push({type:'text',style:{text:m.label,x:p[0]+lv.dx,y:gy-r-6*unit-lv.lv*18*unit,align:'center',verticalAlign:'bottom',fontSize:14*unit,fontWeight:m.risk||m.id===V.focus?700:400,fill:m.risk?KZ_TOKENS.colors.risk:m.id===V.focus?KZ_TOKENS.colors.ink:KZ_TOKENS.colors.body,textBorderColor:'#FFFFFF',textBorderWidth:3*unit,fontFamily:F}});
              return {type:'group',children:kids};},
            data:progress>=1?V.ms.map((m,i)=>[m.x,m.row,i]):[],encode:{x:0,y:1}}]:[]),
          ...(V.todayX!=null?[{type:'custom',coordinateSystem:'cartesian2d',id:'kz-gantt-today',silent:true,z:0,
            renderItem(params,api){const x=api.coord([V.todayX,0])[0],cs=params.coordSys,t=V.todayText,w=textW(t,14*unit)+14*unit;
              const D=GT().today;return {type:'group',children:[{type:'line',shape:{x1:x,y1:cs.y,x2:x,y2:cs.y+cs.height},style:{stroke:D.line,lineWidth:D.width,lineDash:D.dash.map(v=>v*unit)}},
                {type:'rect',shape:{x:x-w/2,y:cs.y-22*unit,width:w,height:20*unit,r:10*unit},style:{fill:D.pill}},
                {type:'text',style:{text:t,x,y:cs.y-12*unit,align:'center',verticalAlign:'middle',fontSize:13*unit,fontWeight:600,fill:D.text,fontFamily:F}}]};},
            data:[[V.todayX,0]],encode:{x:0,y:1}}]:[])]},{notMerge:true});
      status(hint.textContent);options.onProgress?.(progress,clone(src));
    }
    // a signed shift (quarter units) at the plan's granularity: +1 季度 · −2 个月 · +15 天
    function slip(d,at){if(Math.abs(d)<1e-9)return '';if(V.gran==='day'){const a=new Date(K().ttext(at-d-1e-7,'day')),b=new Date(K().ttext(at-1e-7,'day')),n=Math.round((b-a)/DAY);return n?`${n>0?'+':'−'}${Math.abs(n)} 天`:'';}
      const n=Math.round(d*(V.gran==='month'?3:1));return n?`${n>0?'+':'−'}${Math.abs(n)} ${V.gran==='month'?'个月':'季度'}`:'';}
    function finish(){if(disposed)return;cancelAnimationFrame(raf);raf=0;progress=1;draw();}
    // Seekable reveal for timeline drivers (14 FLAG motion): p in [0,1], no own clock.
    function renderProgress(p){if(disposed)return;cancelAnimationFrame(raf);raf=0;progress=Math.max(0,Math.min(1,+p||0));draw();}
    function play(duration=KZ_TOKENS.motion?.duration_ms?.data??1000){cancelAnimationFrame(raf);raf=0;if(disposed)return;if(mq.matches){finish();return;}progress=0;draw();let start=null;
      // Same data easing as charts: tokens.motion.easing.data (cubic-bezier, solved by bisection).
      const b=KZ_TOKENS.motion?.easing?.data||[.33,1,.68,1],curve=x=>{let lo=0,hi=1;for(let i=0;i<20;i++){const t=(lo+hi)/2,bx=3*(1-t)**2*t*b[0]+3*(1-t)*t*t*b[2]+t**3;bx<x?lo=t:hi=t;}const t=(lo+hi)/2;return 3*(1-t)**2*t*b[1]+3*(1-t)*t*t*b[3]+t**3;};
      const tick=()=>{if(disposed)return;const now=performance.now();start??=now;const p=Math.min(1,(now-start)/duration);progress=curve(p);draw();if(p<1)raf=requestAnimationFrame(tick);else raf=0;};raf=requestAnimationFrame(tick);
    }
    mq.addEventListener('change',()=>{if(mq.matches)finish();},{signal});
    document.addEventListener('visibilitychange',()=>{if(document.hidden)finish();},{signal});
    global.addEventListener('beforeprint',finish,{signal});
    global.addEventListener('kz:fluidratio',()=>{if(!disposed)draw();},{signal});
    function local(event){const r=plot.getBoundingClientRect();return [(event.clientX-r.left)*(plot.clientWidth/r.width),(event.clientY-r.top)*(plot.clientHeight/r.height)];}
    function axisAt(event){return chart.convertFromPixel({xAxisIndex:0},local(event)[0]);}
    function rowGeometry(t){const a=chart.convertToPixel({xAxisIndex:0,yAxisIndex:0},[t.start,t.row]),b=chart.convertToPixel({xAxisIndex:0,yAxisIndex:0},[t.end,t.row]);
      const band=Math.abs(chart.convertToPixel({xAxisIndex:0,yAxisIndex:0},[t.start,t.row+1])?.[1]-a[1])||0,unit=fluidUnit(root),dy=barBox(unit,band).dy;return {x:a[0],y:a[1]+dy,w:b[0]-a[0],i:t.row};}
    function hit(event){const p=local(event);for(const t of V.tasks){if(t.summary)continue;const r=rowGeometry(t);if(p[0]>=r.x-3&&p[0]<=r.x+r.w+3&&Math.abs(p[1]-r.y)<23)return {t,r,p};}return null;}
    // the free interval of a bar in its lane (bars of a lane stay in sequence)
    function bounds(t){let lo=V.min,hi=V.max;for(const x of V.tasks)if(x.id!==t.id&&x.row===t.row&&!x.summary){if(x.end<=t.start+1e-9)lo=Math.max(lo,x.end);else if(x.start>=t.end-1e-9)hi=Math.min(hi,x.start);}return V.plain?[V.min,V.max]:[lo,hi];}
    const minLen=t=>V.gran==='quarter'?1:V.gran==='month'?1/3:1/qdays(Math.floor(t.start+1e-9));
    // write a bar's interval into the source: integers in the 7.x form; text at the granularity in a plan. Milestones ride
    // along as when they were bound to the bar: moving the whole bar carries every milestone inside it, dragging one end
    // carries those in the first or last unit of the bar (the start that opens it, the readout that closes it).
    const uw=(x,dir)=>V.gran==='quarter'?1:V.gran==='month'?1/3:1/qdays(Math.floor(dir<0?x-1e-9:x+1e-9));
    function writeBar(next,id,s,e){
      if(!isDoc(next)){const t=next.tasks.find(x=>x.id===id);t.start=s;t.end=e;return;}
      for(const l of next.lanes)for(const b of l.bars||[])if(b.key===id){
        const s0=K().tspan(b.start,'开始')[0],e0=K().tspan(b.end,'结束')[1],ds=s-s0,de=e-e0,move=Math.abs(ds-de)<1e-9;
        for(const m of l.milestones||[]){const t0=K().tspan(m.at,'时间')[0],u=unitOf(m.at);let d=0;
          if(move&&t0>=s0-1e-9&&t0<e0-1e-12)d=ds;
          else if(!move&&Math.abs(de)>1e-9&&t0>=e0-uw(e0,-1)-1e-9&&t0<e0-1e-12)d=de;
          else if(!move&&Math.abs(ds)>1e-9&&t0>=s0-1e-9&&t0<s0+uw(s0,1)-1e-12)d=ds;
          if(d)m.at=K().ttext(t0+d+1e-7,u);}
        b.start=txt(s,V.gran);b.end=txtEnd(e,V.gran);return;}
    }
    function setSource(next,message,{record=true,mark=true}={}){
      validate(next);if(record){undo.push(clone(src));redo=[];}src=next;V=viewOf(src);
      if(selected&&!V.tasks.some(t=>t.id===selected))selected=V.tasks.find(t=>!t.summary)?.id??null;
      fitHeight();draw();status(message);if(mark)emit('change',{data:clone(src),message});
    }
    function commit(start,end,message='时间已更新'){
      if(progress!==1)finish();const t=task();if(!t){status('先选一个阶段');return false;}
      const S=V.doc?snap(+start,V.gran):start,E=V.doc?snap(+end,V.gran):end;
      if(!Number.isFinite(S)||!Number.isFinite(E)||(!V.doc&&(!Number.isInteger(S)||!Number.isInteger(E)))||S>=E-1e-9||S<V.min-1e-9||E>V.max+1e-9){status('时间无效：结束须不早于开始，且在坐标轴范围内');return false;}
      const [lo,hi]=bounds(t);if(S<lo-1e-9||E>hi+1e-9){status('时间无效：与同一行的前后阶段重叠');return false;}
      if(Math.abs(S-t.start)<1e-9&&Math.abs(E-t.end)<1e-9)return true;
      const next=clone(src);writeBar(next,t.id,S,E);try{setSource(next,message);}catch(error){status(error.message);return false;}return true;
    }
    function rollbackDrag(){if(!drag)return;src=drag.before;V=viewOf(src);drag=null;draw();status('本次拖动已取消');}
    plot.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;if(progress!==1)finish();const h=hit(event);if(!h)return;
      selected=h.t.id;marked=true;const G=KZ_TOKENS.gantt||{},edge=Math.min(G.handle_px??14,h.r.w*(G.handle_short_ratio??.24));const mode=h.p[0]<h.r.x+edge?'start':h.p[0]>h.r.x+h.r.w-edge?'end':'move';
      drag={id:selected,mode,axis:axisAt(event),start:h.t.start,end:h.t.end,bounds:bounds(h.t),before:clone(src),clientX:event.clientX,moved:false,pointerId:event.pointerId};
      plot.dataset.kzPointer='true';plot.setPointerCapture(event.pointerId);plot.focus();event.preventDefault();draw();emit('select',{id:selected});
    },{signal});
    plot.addEventListener('pointermove',event=>{
      if(!drag){const h=hit(event);plot.style.cursor=h?(Math.min(Math.abs(h.p[0]-h.r.x),Math.abs(h.p[0]-h.r.x-h.r.w))<14?'ew-resize':'grab'):'default';return;}
      if(Math.abs(event.clientX-drag.clientX)<3&&!drag.moved)return;drag.moved=true;
      const dx=axisAt(event)-drag.axis,[lo,hi]=drag.bounds,t=task(),L=minLen(t);let s=drag.start,e=drag.end;
      const sn=x=>V.doc?snap(x,V.gran):Math.round(x);
      if(drag.mode==='move'){const len=drag.end-drag.start;s=Math.max(lo,Math.min(hi-len,sn(drag.start+dx)));e=V.doc?Math.min(hi,sn(s+len)):s+len;}
      if(drag.mode==='start')s=Math.max(lo,Math.min(drag.end-L,sn(drag.start+dx)));
      if(drag.mode==='end')e=Math.min(hi,Math.max(drag.start+L,sn(drag.end+dx)));
      const next=clone(drag.before);writeBar(next,drag.id,s,e);try{validate(next);src=next;V=viewOf(src);}catch{}
      draw();status('正在调整；松开以确认');
    },{signal});
    plot.addEventListener('pointerup',event=>{
      if(!drag)return;const before=drag.before,changed=JSON.stringify(before)!==JSON.stringify(src);drag=null;
      if(plot.hasPointerCapture(event.pointerId))plot.releasePointerCapture(event.pointerId);
      if(changed){undo.push(before);redo=[];emit('change',{data:clone(src),message:'时间已更新'});}draw();status(changed?'时间已更新':'已选中；回车或双击打开编辑台');
    },{signal});
    plot.addEventListener('pointercancel',rollbackDrag,{signal});
    plot.addEventListener('dblclick',event=>{const h=hit(event);if(h){selected=h.t.id;marked=true;draw();}openEditor(true);},{signal});
    plot.addEventListener('focus',()=>{if(!marked&&plot.matches(':focus-visible')){marked=true;draw();}},{signal});
    plot.addEventListener('keydown',e=>{
      delete plot.dataset.kzPointer;
      if(e.key==='Escape'&&drag){e.preventDefault();rollbackDrag();return;}
      if(e.key==='Enter'||e.key===' '){e.preventDefault();marked=true;draw();openEditor(true);return;}
      if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();e.stopPropagation();const d=e.key==='ArrowRight'?1:-1,t=task();if(!t)return;
      marked=true;const mv=x=>V.doc?step(x,V.gran,d):x+d;commit(e.shiftKey?t.start:mv(t.start),mv(t.end));
    },{signal});
    // the caret of a parent lane folds and unfolds its children (two-level plans)
    chart.on?.('click',params=>{if(params.componentType!=='yAxis'||!V.doc)return;const r=V.rows.find(x=>x.id===params.value);if(!r||!r.parent)return;
      const next=clone(src),l=next.lanes.find(x=>x.key===r.id);l.collapsed=!r.collapsed;if(!l.collapsed)delete l.collapsed;setSource(next,r.collapsed?'已展开':'已收起');});
    root.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!e.target.closest('input,select,textarea')){e.preventDefault();e.stopPropagation();e.shiftKey?redoOne():undoOne();return;}if(e.target.closest('input,select,textarea,button,[contenteditable=true]')||['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Enter','Escape'].includes(e.key))e.stopPropagation();},{signal});
    // the editing studio is a separate module (kz-gantt-studio.js); without it the Gantt stays editable in place
    function openEditor(open=true){
      const S=global.KZGanttStudio;if(!S){status(open?'编辑台未加载（kz-gantt-studio.js）':'');return;}
      if(open)S.open(api,{focus:selected});else S.close();
    }
    function undoOne(){finish();if(undo.length){redo.push(clone(src));src=undo.pop();V=viewOf(src);fitHeight();draw();status('已撤销');emit('change',{data:clone(src),message:'已撤销'});}}
    function redoOne(){finish();if(redo.length){undo.push(clone(src));src=redo.pop();V=viewOf(src);fitHeight();draw();status('已重做');emit('change',{data:clone(src),message:'已重做'});}}
    function reset(){cancelAnimationFrame(raf);progress=1;if(JSON.stringify(src)!==JSON.stringify(baseline))undo.push(clone(src));redo=[];src=clone(baseline);V=viewOf(src);fitHeight();draw();status('已还原');emit('change',{data:clone(src),message:'已还原'});}
    undoB.addEventListener('click',undoOne,{signal});resetB.addEventListener('click',reset,{signal});
    // resize on the next frame, so the redraw never feeds back into the same observer pass (no "ResizeObserver loop" error)
    let rz=0;resize=new ResizeObserver(()=>{cancelAnimationFrame(rz);rz=requestAnimationFrame(()=>{rz=0;if(disposed)return;if(drag)rollbackDrag();chart.resize();draw();});});resize.observe(plot);
    draw();bindTexts();
    api={chart,root,plot,openEditor,renderProgress,
      select(id){if(!V.tasks.some(t=>t.id===id))throw Error('未知任务');selected=id;marked=true;draw();emit('select',{id});},
      play,finish,getProgress:()=>progress,getData:()=>clone(src),getSelected:()=>selected,getDirty:countDirty,commit,undo:undoOne,redo:redoOne,reset,serialize:()=>JSON.stringify(src),
      canUndo:()=>undo.length>0,canRedo:()=>redo.length>0,
      // the plan contract (a 7.x quarter form is converted, unsaved, until the first edit replaces it)
      getDoc:()=>isDoc(src)?clone(src):fromLegacy(src),getBaseline:()=>clone(baseline),isDoc:()=>isDoc(src),
      setDoc(doc,{message='已更新',record=true}={}){setSource(clone(doc),message,{record});},
      // after a save the saved data is the new reference for "已修改"
      markSaved(){baseline=clone(src);status('已保存');emit('saved',{data:clone(src)});},
      view:()=>V,gid,anchor:options.anchor||null,
      on(fn){listeners.add(fn);return ()=>listeners.delete(fn);},
      geometry(id){const t=V.tasks.find(x=>x.id===id);if(!t)throw Error('未知任务');return rowGeometry(t);},
      importJSON(text){const next=JSON.parse(text);setSource(next,'已导入');},
      pause(){finish();if(drag)rollbackDrag();},resume(){chart.resize();},
      dispose(){if(disposed)return;disposed=true;const errors=releaseAll();if(errors.length)throw new AggregateError(errors,'甘特清理未完全释放');}};
    live.add(api);
    if(options.bus!==false)offBus=subscribe(api,doc=>{if(isDoc(src)&&src.id===doc.id&&JSON.stringify(src)!==JSON.stringify(doc))setSource(clone(doc),'已与同页图表同步',{record:false});});
    return api;
    }catch(error){
      disposed=true;
      const errors=releaseAll();
      if(errors.length)throw new AggregateError([error,...errors],'甘特挂载失败且未完全释放');
      throw error;
    }
  }
  const mixWhite=(c,t=.55)=>{const v=[1,3,5].map(i=>parseInt(String(c).slice(i,i+2),16));return '#'+v.map(x=>Math.round(x+(255-x)*t).toString(16).padStart(2,'0')).join('');};
  // milestone glyphs by kind (首例入组 ● / 结果读出 ◆ / 递交 ▲ / 获批 ★ / 其他 ⬢), the same shapes as the static template
  const GLYPHS={start:1,readout:1,submit:1,approve:1,other:1};
  function glyphOf(kind,cx,cy,r,style){
    if(kind==='start')return [{type:'circle',shape:{cx,cy,r:r*.82},style}];
    const pts=kind==='submit'?[[0,-r],[r*.95,r*.72],[-r*.95,r*.72]]:kind==='approve'?Array.from({length:10},(_,i)=>{const q=i%2?r*.5:r*1.15,a=i*Math.PI/5;return [Math.sin(a)*q,-Math.cos(a)*q];})
      :kind==='other'?Array.from({length:6},(_,i)=>{const a=Math.PI/6+i*Math.PI/3;return [Math.cos(a)*r*.92,Math.sin(a)*r*.92];}):[[0,-r],[r,0],[0,r],[-r,0]];
    return [{type:'polygon',shape:{points:pts.map(([a,b])=>[cx+a,cy+b])},style}];
  }
  global.KZGantt={mount,validate,fromLegacy,viewOf,bindValue,snap,step,qindex,fromIndex,qlabel,publish,subscribe,instances:()=>[...live]};
})(window);
