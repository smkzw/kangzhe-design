/* KZGanttStudio — the full-page editing studio for KZGantt (08 GANTT-01 / -05). Press T (any track: HTML-PPT, site,
   stream, flagship), Enter on a selected bar or double-click it: the page becomes a studio — top bar (granularity
   日/月/季度, axis range, today, undo/redo/reset, save), the plan as a list on the left (lanes → phases and milestones;
   add, duplicate, move, nest, delete), a live preview in the middle (drag works there too), properties on the right with
   point-and-click date pickers (day / month / quarter) and a milestone icon picker. Esc or 完成 closes; the page shows the
   result at once (the Gantt on the slide and the page's data store follow every change).
   Saving (08 GANTT-05): a draft follows every change (localStorage, offered back when the studio next opens); 保存到本文件
   writes the data block of this HTML file in place (File System Access — the file is read first and only its data block
   is replaced; anything else is refused); 导出 / 导入 JSON and 复制数据 carry the plan to the Agent, who rebuilds the
   PPTX page from the same contract. Requires kz-tokens.js, kz-icons.js, kz-clinical.js, kz-gantt.js (in that order). */
(function(global){
  'use strict';
  const C=()=>global.KZClinical,G=()=>global.KZGantt;
  const clone=x=>JSON.parse(JSON.stringify(x));
  const T=()=>global.KZ_TOKENS||{colors:{},charts:{}};
  function h(tag,props,...kids){
    const el=document.createElement(tag);
    for(const [k,v] of Object.entries(props||{})){
      if(v==null||v===false)continue;
      if(k==='class')el.className=v;else if(k==='text')el.textContent=v;else if(k==='html')el.innerHTML=v;
      else if(k.startsWith('on')&&typeof v==='function')el.addEventListener(k.slice(2),v);
      else if(k==='style')el.style.cssText=v;else if(k==='dataset')Object.assign(el.dataset,v);
      else if(k in el&&typeof v!=='string')el[k]=v;else el.setAttribute(k,v===true?'':v);
    }
    for(const c of kids.flat(9))if(c!=null&&c!==false)el.append(c.nodeType?c:document.createTextNode(String(c)));
    return el;
  }
  const ico=(name,cls='')=>{const s=global.KZIcons?.svg?.(name);if(s){if(cls)s.classList.add(cls);return s;}return h('span');};
  const GRAN_TXT={quarter:'季度',month:'月',day:'日'};
  const KINDS={start:'首例入组',readout:'结果读出',submit:'递交',approve:'获批',other:'里程碑'};
  const STATUS=[['','无'],['planned','计划'],['active','进行中'],['done','已完成'],['delayed','延迟'],['risk','风险']];
  const STATUS_ICON={planned:'calendar',active:'progress-check',done:'circle-check',delayed:'clock',risk:'alert-circle'};
  const MS_ICONS=['flag','check','circle-check','doc-check','send','file-certificate','certificate','gavel','award','target','people','building-hospital','lab','pill','syringe','report-medical','database','lock','calendar-event','alert-circle'];
  function glyph(kind,filled=true){
    const r=6.4,pts=kind==='submit'?[[0,-r],[r*.95,r*.72],[-r*.95,r*.72]]:kind==='approve'?Array.from({length:10},(_,i)=>{const q=i%2?r*.5:r*1.15,a=i*Math.PI/5;return [Math.sin(a)*q,-Math.cos(a)*q];})
      :kind==='other'?Array.from({length:6},(_,i)=>{const a=Math.PI/6+i*Math.PI/3;return [Math.cos(a)*r*.92,Math.sin(a)*r*.92];}):[[0,-r],[r,0],[0,r],[-r,0]];
    const st=filled?'fill="currentColor"':'fill="#fff" stroke="currentColor" stroke-width="1.5"';
    const body=kind==='start'?`<circle cx="10" cy="10" r="${r*.82}" ${st}/>`:`<polygon points="${pts.map(([a,b])=>`${(10+a).toFixed(2)},${(10+b).toFixed(2)}`).join(' ')}" ${st}/>`;
    const s=h('span',{class:'kzs-glyph',html:`<svg viewBox="0 0 20 20" aria-hidden="true">${body}</svg>`});return s;
  }
  // ---- time helpers (quarter units; strings at the plan's granularity)
  const span=(v,w='时间')=>C().tspan(v,w);
  const txt=(x,g)=>C().ttext(x+1e-7,g),txtEnd=(x,g)=>C().ttext(x-1e-7,g);
  const conv=(v,g,edge)=>{const [a,b]=span(v);return edge==='end'?txtEnd(b,g):txt(a,g);};
  const unitOf=s=>/Q/.test(s)?'quarter':String(s).length===7?'month':'day';
  const pretty=(v)=>{if(!v)return '—';const u=unitOf(v);if(u==='quarter')return v.replace('Q',' Q');if(u==='month')return `${v.slice(0,4)}年${+v.slice(5)}月`;return `${v.slice(0,4)}年${+v.slice(5,7)}月${+v.slice(8)}日`;};
  const range=(b,g)=>`${pretty(b.start)} – ${pretty(b.end)}`;
  const pad=n=>String(n).padStart(2,'0');
  const todayStr=()=>{const d=new Date();return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;};
  const dur=g=>g==='quarter'?4:g==='month'?6:90;
  // ---- date picker: a field that opens a calendar popover (day), a month grid or a quarter grid
  let pop=null;
  function closePop(refocus=true){if(!pop)return;const f=pop.field;pop.el.remove();pop=null;if(refocus)f?.focus();}
  function picker({value,mode,onPick,label,clearable=false,placeholder='选择'}){
    const field=h('button',{type:'button',class:'kzs-date','aria-haspopup':'dialog','aria-label':label?`${label}：${pretty(value)}`:pretty(value)},
      h('span',{class:'kzs-date-v',text:value?pretty(value):placeholder}),ico('calendar','kzs-date-i'));
    field.addEventListener('click',()=>{if(pop&&pop.field===field){closePop();return;}openPop(field,{value,mode,onPick,clearable});});
    return field;
  }
  function openPop(field,{value,mode,onPick,clearable}){
    closePop(false);const host=S.root,box=field.getBoundingClientRect(),hb=host.getBoundingClientRect();
    let cur=value?span(value)[0]:(S.doc.today&&S.doc.today!=='auto'?span(S.doc.today)[0]:span(todayStr())[0]);
    let y=Math.floor(Math.floor(cur)/4),m=(Math.floor(cur)%4)*3+1;
    if(value&&unitOf(value)!=='quarter'){y=+value.slice(0,4);m=+value.slice(5,7);}
    let view=mode;   // day → month list → year list, by clicking the header
    const el=h('div',{class:'kzs-pop',role:'dialog','aria-label':'选择日期'});
    const pick=v=>{closePop();onPick(v);};
    const sel=value?span(value):null;
    const render=()=>{
      el.replaceChildren();const head=h('div',{class:'kzs-pop-head'});
      const step=d=>{if(view==='day'){m+=d;if(m<1){m=12;y--;}if(m>12){m=1;y++;}}else if(view==='years')y+=d*12;else y+=d;render();};
      const title=view==='day'?`${y} 年 ${m} 月`:view==='years'?`${y-5} – ${y+6}`:`${y} 年`;
      head.append(h('button',{type:'button',class:'kzs-pop-nav','aria-label':'上一页',onclick:()=>step(-1)},'‹'),
        h('button',{type:'button',class:'kzs-pop-title',onclick:()=>{view=view==='day'?'month-nav':view==='years'?view:'years';render();}},title),
        h('button',{type:'button',class:'kzs-pop-nav','aria-label':'下一页',onclick:()=>step(1)},'›'));
      el.append(head);
      let grid;
      if(view==='day'){
        grid=h('div',{class:'kzs-grid is-days',role:'grid'});for(const w of '一二三四五六日')grid.append(h('span',{class:'kzs-wd',text:w}));
        const first=new Date(Date.UTC(y,m-1,1)),lead=(first.getUTCDay()+6)%7,n=new Date(Date.UTC(y,m,0)).getUTCDate(),today=todayStr();
        for(let i=0;i<lead;i++)grid.append(h('span'));
        for(let d=1;d<=n;d++){const v=`${y}-${pad(m)}-${pad(d)}`,[a]=span(v),on=sel&&a>=sel[0]-1e-9&&a<sel[1]-1e-9&&unitOf(value)==='day';
          grid.append(h('button',{type:'button',class:'kzs-cell'+(on?' is-on':'')+(v===today?' is-today':''),'aria-label':pretty(v),'aria-pressed':on?'true':'false',onclick:()=>pick(v)},String(d)));}
      }else if(view==='month'||view==='month-nav'){
        grid=h('div',{class:'kzs-grid is-months',role:'grid'});
        for(let k=1;k<=12;k++){const v=`${y}-${pad(k)}`,[a]=span(v),on=view==='month'&&sel&&Math.abs(a-sel[0])<1e-6;
          grid.append(h('button',{type:'button',class:'kzs-cell'+(on?' is-on':''),'aria-pressed':on?'true':'false',onclick:()=>{if(view==='month')pick(v);else{m=k;view='day';render();}}},`${k} 月`));}
      }else if(view==='quarter'){
        grid=h('div',{class:'kzs-grid is-quarters',role:'grid'});
        for(let k=1;k<=4;k++){const v=`${y}Q${k}`,[a]=span(v),on=sel&&Math.abs(a-Math.floor(sel[0]+1e-9))<1e-6;
          grid.append(h('button',{type:'button',class:'kzs-cell'+(on?' is-on':''),'aria-pressed':on?'true':'false',onclick:()=>pick(v)},h('b',{text:`Q${k}`}),h('small',{text:`${k*3-2}–${k*3} 月`})));}
      }else{
        grid=h('div',{class:'kzs-grid is-years',role:'grid'});
        for(let k=y-5;k<=y+6;k++)grid.append(h('button',{type:'button',class:'kzs-cell'+(k===y?' is-on':''),onclick:()=>{y=k;view=mode==='day'?'month-nav':mode;render();}},String(k)));
      }
      el.append(grid);
      const foot=h('div',{class:'kzs-pop-foot'});
      if(mode==='day')foot.append(h('button',{type:'button',class:'kzs-link',onclick:()=>pick(todayStr())},'今天'));
      if(clearable)foot.append(h('button',{type:'button',class:'kzs-link',onclick:()=>pick(null)},'清除'));
      if(foot.childNodes.length)el.append(foot);
      // arrow keys walk the grid, Enter picks, Esc closes
      grid.addEventListener('keydown',e=>{const cells=[...grid.querySelectorAll('button')],i=cells.indexOf(document.activeElement);if(i<0)return;
        const cols=view==='day'?7:view==='quarter'?4:view==='years'?4:4,d={ArrowLeft:-1,ArrowRight:1,ArrowUp:-cols,ArrowDown:cols}[e.key];
        if(d){e.preventDefault();cells[Math.max(0,Math.min(cells.length-1,i+d))].focus();}});
      (grid.querySelector('.is-on')||grid.querySelector('.is-today')||grid.querySelector('button'))?.focus();
    };
    el.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();closePop();}});
    host.append(el);render();
    const su=S.su,w=el.offsetWidth,hgt=el.offsetHeight;let left=box.left-hb.left,top=box.bottom-hb.top+6*su;
    if(left+w>hb.width-8)left=hb.width-8-w;if(top+hgt>hb.height-8)top=box.top-hb.top-hgt-6*su;
    el.style.left=left+'px';el.style.top=Math.max(8,top)+'px';pop={el,field};
  }
  // ---- the studio
  let S=null,keyBound=false;
  const draftKey=inst=>`kz-gantt-draft:${location.pathname}:${inst.gid||'gantt'}`;
  function keysOf(doc){const s=new Set();for(const l of doc.lanes){s.add(l.key);for(const b of l.bars||[])s.add(b.key);for(const m of l.milestones||[])s.add(m.key);}return s;}
  function newKey(doc,prefix){const s=keysOf(doc);let i=1;while(s.has(`${prefix}${i}`))i++;return `${prefix}${i}`;}
  const findBar=(doc,key)=>{for(const l of doc.lanes)for(const b of l.bars||[])if(b.key===key)return [l,b];return [];};
  const findMs=(doc,key)=>{for(const l of doc.lanes)for(const m of l.milestones||[])if(m.key===key)return [l,m];return [];};
  const gran=doc=>C().program(doc).granularity;
  // widen the axis when an edit lands outside it (the studio never refuses a date just for the axis)
  function fitAxis(doc){
    let a=span(doc.from)[0],b=span(doc.to)[1];
    for(const l of doc.lanes){for(const x of l.bars||[]){a=Math.min(a,span(x.start)[0]);b=Math.max(b,span(x.end)[1]);if(x.baseline){a=Math.min(a,span(x.baseline.start)[0]);b=Math.max(b,span(x.baseline.end)[1]);}}
      for(const m of l.milestones||[]){a=Math.min(a,span(m.at)[0]);b=Math.max(b,span(m.at)[1]);if(m.baseline){a=Math.min(a,span(m.baseline)[0]);b=Math.max(b,span(m.baseline)[1]);}}}
    if(doc.today&&doc.today!=='auto'){a=Math.min(a,span(doc.today)[0]);b=Math.max(b,span(doc.today)[1]);}
    const f=C().qtext(Math.floor(a+1e-9)),t=C().qtext(Math.ceil(b-1e-9)-1);if(f!==doc.from&&span(f)[0]<span(doc.from)[0])doc.from=f;if(span(t)[1]>span(doc.to)[1])doc.to=t;
  }
  function apply(mut,message){
    const next=clone(S.doc);try{mut(next);fitAxis(next);C().program(next);}catch(e){say(e.message,true);return false;}
    if(S.pending){S.pending=false;S.banner.hidden=true;}
    S.doc=next;S.lock=true;try{S.inst.setDoc(next,{message});S.preview.setDoc(next,{message,record:false});}finally{S.lock=false;}
    say(message);renderAll();return true;
  }
  function say(msg,err=false){if(!S)return;S.msg.textContent=msg||'';S.msg.classList.toggle('is-error',!!err);}
  function select(sel){S.sel=sel;if(sel?.type==='bar'){try{S.preview.select(sel.key);}catch{}}renderList();renderProps();}
  function open(inst,{focus}={}){
    if(!C()||!G())throw Error('编辑台需要 kz-clinical.js 与 kz-gantt.js');
    if(S){if(S.inst===inst)return;close();}
    const doc=inst.getDoc(),root=h('div',{class:'kz kz-gantt-studio',role:'dialog','aria-modal':'true','aria-label':'编辑甘特',tabindex:'-1'});
    const fit=()=>{const su=Math.max(.72,Math.min(1.5,Math.min(innerWidth/1440,innerHeight/860)));root.style.setProperty('--su',su.toFixed(4));if(S)S.su=su;};
    S={inst,root,doc,sel:focus?{type:'bar',key:focus}:{type:'plan'},lock:false,su:1,legacy:!inst.isDoc()};fit();
    const title=inst.root.closest('.kzl-card,.kz-card,section,.slide')?.querySelector('h3,.kzl-card-title,h2')?.textContent?.trim()||'甘特图';
    // top bar
    const bar=h('header',{class:'kzs-top'},
      h('div',{class:'kzs-brand'},h('span',{class:'kzs-badge'},ico('timeline')),h('div',{},h('b',{text:'编辑甘特'}),h('small',{text:title}))),
      S.granBox=h('div',{class:'kzs-seg',role:'radiogroup','aria-label':'精度'}),
      S.rangeBox=h('div',{class:'kzs-field-inline'}),
      S.todayBox=h('div',{class:'kzs-field-inline'}),
      h('div',{class:'kzs-spacer'}),
      S.undoB=h('button',{type:'button',class:'kzs-btn',title:'撤销（⌘/Ctrl+Z）',onclick:()=>S.inst.undo()},'撤销'),
      S.redoB=h('button',{type:'button',class:'kzs-btn',title:'重做（⌘/Ctrl+Shift+Z）',onclick:()=>S.inst.redo()},'重做'),
      h('button',{type:'button',class:'kzs-btn',onclick:()=>{S.inst.reset();}},'还原'),
      S.saveB=h('div',{class:'kzs-menu'},h('button',{type:'button',class:'kzs-btn is-primary','aria-haspopup':'menu',onclick:()=>toggleMenu()},'保存',h('span',{class:'kzs-caret',text:'▾'}))),
      h('button',{type:'button',class:'kzs-btn',onclick:()=>close()},'完成'));
    S.list=h('nav',{class:'kzs-list','aria-label':'泳道、阶段与里程碑'});
    S.stage=h('div',{class:'kzs-stage'});const host=h('div',{class:'kzs-preview'});S.stage.append(host);
    S.props=h('aside',{class:'kzs-props','aria-label':'属性'});
    S.banner=h('div',{class:'kzs-banner',hidden:true});
    S.msg=h('p',{class:'kzs-msg','aria-live':'polite'});
    S.affect=h('div',{class:'kzs-affect'});
    root.append(bar,h('div',{class:'kzs-body'},h('div',{class:'kzs-col'},S.banner,S.list),S.stage,S.props),h('footer',{class:'kzs-foot'},S.msg,S.affect));
    document.body.append(root);
    // the rest of the page is inert while the studio is open (focus and pointer stay in it; deck keys never fire)
    S.inerted=[...document.body.children].filter(e=>e!==root&&!e.inert);S.inerted.forEach(e=>{e.inert=true;});
    S.preview=G().mount(host,doc,{fill:true,bus:false});
    S.offMain=inst.on((type)=>{if(!S||S.lock||type!=='change')return;S.doc=S.inst.getDoc();S.lock=true;try{S.preview.setDoc(S.doc,{record:false});}finally{S.lock=false;}renderAll();});
    S.offPrev=S.preview.on((type,d)=>{if(!S||S.lock)return;
      if(type==='select'){S.sel={type:'bar',key:d.id};renderList();renderProps();return;}
      if(type==='change'){const next=S.preview.getDoc();S.lock=true;try{S.inst.setDoc(next,{message:d.message});}finally{S.lock=false;}S.doc=next;renderAll();}});
    root.addEventListener('keydown',onKey);
    S.onWinKey=e=>{if(S&&!root.contains(e.target)){onKey(e);e.stopImmediatePropagation();}};addEventListener('keydown',S.onWinKey,true);
    S.onResize=()=>{fit();};addEventListener('resize',S.onResize);
    S.onDown=e=>{if(pop&&!pop.el.contains(e.target)&&!pop.field.contains(e.target))closePop(false);if(S.menu&&!S.saveB.contains(e.target))toggleMenu(false);};
    root.addEventListener('pointerdown',S.onDown,true);
    offerDraft();renderAll();
    if(S.legacy)say('这张甘特是 7.x 季度格式；第一次修改后按计划格式保存（可写日期、月份与更多字段）');
    inst.root.dataset.kzEditor='open';
    requestAnimationFrame(()=>root.querySelector('.kzs-list .is-on,.kzs-list button')?.focus());
  }
  function close(){
    if(!S)return;closePop(false);const {root,inst}=S;
    S.offMain?.();S.offPrev?.();try{S.preview.dispose();}catch{}removeEventListener('resize',S.onResize);removeEventListener('keydown',S.onWinKey,true);
    S.inerted.forEach(e=>{e.inert=false;});root.remove();inst.root.dataset.kzEditor='closed';S=null;
    // back to where T was pressed: the Gantt's plot, or the figure the off-screen Gantt stands for (inst.anchor)
    try{const back=inst.anchor?.querySelector?.('[tabindex="0"]');if(back)back.focus({preventScroll:true});else{inst.plot.dataset.kzPointer='true';inst.plot.focus({preventScroll:true});}}catch{}
  }
  function onKey(e){
    e.stopPropagation();   // nothing reaches the deck (page turns, scenes) while the studio is open
    const typing=e.target.closest?.('input,textarea,select,[contenteditable=true]');
    if(e.key==='Escape'){e.preventDefault();if(pop){closePop();return;}if(S.menu){toggleMenu(false);return;}close();return;}
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'&&!typing){e.preventDefault();e.shiftKey?S.inst.redo():S.inst.undo();return;}
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='y'&&!typing){e.preventDefault();S.inst.redo();return;}
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveToFile();return;}
    if((e.key==='Delete'||e.key==='Backspace')&&!typing&&S.sel&&S.sel.type!=='plan'){e.preventDefault();removeSel();}
  }
  function renderAll(){if(!S)return;renderTop();renderList();renderProps();renderAffect();S.undoB.disabled=!S.inst.canUndo();S.redoB.disabled=!S.inst.canRedo();saveDraft();keepFocus();}
  // a re-render replaces the controls; focus that fell out goes back to the selected item, else the studio itself
  function keepFocus(){if(!S||S.root.contains(document.activeElement)&&document.activeElement!==document.body)return;(S.list.querySelector('.is-on')||S.root).focus({preventScroll:true});}
  function renderTop(){
    const g=gran(S.doc);
    S.granBox.replaceChildren(h('span',{class:'kzs-label',text:'精度'}),...['day','month','quarter'].map(k=>h('button',{type:'button',role:'radio','aria-checked':g===k?'true':'false',class:'kzs-seg-b'+(g===k?' is-on':''),onclick:()=>setGran(k)},GRAN_TXT[k])));
    S.rangeBox.replaceChildren(h('span',{class:'kzs-label',text:'范围'}),picker({value:S.doc.from,mode:'quarter',label:'起',onPick:v=>apply(d=>{d.from=v;},'时间轴起点已更新')}),h('span',{class:'kzs-dash',text:'→'}),
      picker({value:S.doc.to,mode:'quarter',label:'止',onPick:v=>apply(d=>{d.to=v;},'时间轴终点已更新')}),
      h('button',{type:'button',class:'kzs-link',title:'按数据收紧时间轴',onclick:()=>apply(d=>{const M=C().program(d);let a=Infinity,b=-Infinity;for(const l of M.lanes){for(const x of l.bars){a=Math.min(a,x.s);b=Math.max(b,x.e);}for(const m of l.milestones){a=Math.min(a,m.t);b=Math.max(b,m.t+m.tw);}}
        d.from=C().qtext(Math.floor(a+1e-9));d.to=C().qtext(Math.ceil(b-1e-9)-1);if(span(d.to)[1]-span(d.from)[0]<2)d.to=C().qtext(span(d.from)[0]+1);},'时间轴已按数据收紧')},'贴合数据'));
    const tv=S.doc.today;
    S.todayBox.replaceChildren(h('span',{class:'kzs-label',text:'当前'}),
      h('div',{class:'kzs-seg is-small'},...[['none','无'],['auto','自动'],['fixed','指定']].map(([k,t])=>{const on=(k==='none'&&!tv)||(k==='auto'&&tv==='auto')||(k==='fixed'&&tv&&tv!=='auto');
        return h('button',{type:'button',class:'kzs-seg-b'+(on?' is-on':''),'aria-pressed':on?'true':'false',title:k==='auto'?'每次打开都取系统日期':'',onclick:()=>apply(d=>{if(k==='none')delete d.today;else if(k==='auto')d.today='auto';else d.today=tv&&tv!=='auto'?tv:todayStr();},'当前时点已更新')},t);})),
      ...(tv&&tv!=='auto'?[picker({value:tv,mode:'day',label:'当前',onPick:v=>apply(d=>{d.today=v;},'当前时点已更新')})]:[]));
  }
  function setGran(g){
    if(gran(S.doc)===g)return;
    apply(d=>{d.granularity=g;for(const l of d.lanes)for(const b of l.bars||[]){b.start=conv(b.start,g,'start');b.end=conv(b.end,g,'end');if(b.baseline){b.baseline={start:conv(b.baseline.start,g,'start'),end:conv(b.baseline.end,g,'end')};}}},
      `精度改为${GRAN_TXT[g]}：阶段起止已换算${g==='quarter'?'（取所在季度）':''}`);
  }
  // ---- left: the plan as a list
  function renderList(){
    const d=S.doc,g=gran(d),sel=S.sel||{},list=S.list;list.replaceChildren();
    const item=(cls,on,kids,onclick,extra={})=>h('button',{type:'button',class:`kzs-item ${cls}`+(on?' is-on':''),'aria-current':on?'true':null,onclick,...extra},...kids);
    list.append(item('is-plan',sel.type==='plan',[ico('settings'),h('span',{text:'计划设置'}),h('small',{text:`${GRAN_TXT[g]} · ${d.lanes.length} 条泳道`})],()=>select({type:'plan'})));
    const PH=T().charts.phases||[],phases=d.phases&&d.phases.length?d.phases:C().PHASES;
    for(const l of d.lanes){
      const grp=h('div',{class:'kzs-group'+(l.parent?' is-child':'')});
      const kids=d.lanes.filter(x=>x.parent===l.key).length;
      grp.append(item('is-lane',sel.type==='lane'&&sel.key===l.key,[kids?h('span',{class:'kzs-fold',text:l.collapsed?'▸':'▾'}):null,h('span',{class:'kzs-name',text:l.name}),l.note?h('small',{text:l.note}):null],()=>select({type:'lane',key:l.key})));
      for(const b of l.bars||[])grp.append(item('is-bar',sel.type==='bar'&&sel.key===b.key,[h('span',{class:'kzs-sw',style:`background:${b.color||PH[phases.indexOf(b.phase)]||'#ccc'}`}),h('span',{class:'kzs-name',text:b.label||b.phase}),h('small',{text:range(b,g)})],()=>select({type:'bar',key:b.key})));
      for(const m of l.milestones||[]){const gl=m.icon&&!(m.icon in KINDS)?h('span',{class:'kzs-glyph'},ico(m.icon)):glyph(m.icon||m.kind||'other');if(m.risk)gl.classList.add('is-risk');
        grp.append(item('is-ms',sel.type==='ms'&&sel.key===m.key,[gl,h('span',{class:'kzs-name',text:m.label}),h('small',{text:pretty(m.at)})],()=>select({type:'ms',key:m.key})));}
      grp.append(h('div',{class:'kzs-add'},h('button',{type:'button',class:'kzs-link',onclick:()=>addBar(l.key)},'＋ 阶段'),h('button',{type:'button',class:'kzs-link',onclick:()=>addMs(l.key)},'＋ 里程碑')));
      list.append(grp);
    }
    list.append(h('div',{class:'kzs-add is-root'},h('button',{type:'button',class:'kzs-btn is-ghost',onclick:()=>addLane()},'＋ 泳道')));
  }
  function defaultSpan(d,after){
    const g=gran(d),M=C().program(d);let a=after!=null?after:(M.today!=null?Math.floor(M.today*(g==='month'?3:1)+1e-9)/(g==='month'?3:1):M.from);
    a=G().snap(a,g);let e=a;for(let i=0;i<dur(g);i++)e=G().step(e,g,1);return [txt(a,g),txtEnd(e,g)];
  }
  function addLane(){
    const after=S.sel?.type==='lane'?S.sel.key:null;let key;
    apply(d=>{key=newKey(d,'lane-');const [s,e]=defaultSpan(d);const ph=(d.phases&&d.phases.length?d.phases:C().PHASES)[0];
      const lane={key,name:'新泳道',bars:[{key:newKey(d,'bar-'),phase:ph,start:s,end:e}],milestones:[]};
      let i=d.lanes.length;if(after){i=d.lanes.findIndex(l=>l.key===after)+1;while(i<d.lanes.length&&d.lanes[i].parent===after)i++;}
      const prev=d.lanes[i-1];if(prev&&(prev.parent)&&i<d.lanes.length&&d.lanes[i].parent===prev.parent)lane.parent=prev.parent;
      d.lanes.splice(i,0,lane);},'已加一条泳道')&&select({type:'lane',key});
  }
  function addBar(laneKey){
    let key;apply(d=>{const l=d.lanes.find(x=>x.key===laneKey);key=newKey(d,'bar-');const g=gran(d);
      const last=(l.bars||[]).map(b=>span(b.end)[1]).sort((a,b)=>b-a)[0];const [s,e]=defaultSpan(d,last);
      const phases=d.phases&&d.phases.length?d.phases:C().PHASES,lp=(l.bars||[]).map(b=>phases.indexOf(b.phase)).sort((a,b)=>b-a)[0]??-1;
      (l.bars=l.bars||[]).push({key,phase:phases[Math.min(phases.length-1,lp+1)],start:s,end:e});void g;},'已加一个阶段')&&select({type:'bar',key});
  }
  function addMs(laneKey){
    let key;apply(d=>{const l=d.lanes.find(x=>x.key===laneKey);key=newKey(d,'ms-');
      const last=(l.bars||[]).map(b=>span(b.end)[1]).sort((a,b)=>b-a)[0];const at=last!=null?txtEnd(last,'day'):todayStr();
      (l.milestones=l.milestones||[]).push({key,label:'新节点',at,kind:'other'});},'已加一个里程碑')&&select({type:'ms',key});
  }
  function removeSel(){
    const s=S.sel;if(!s)return;
    if(s.type==='lane')apply(d=>{const i=d.lanes.findIndex(l=>l.key===s.key);const l=d.lanes[i];d.lanes.splice(i,1);
      if(!l.parent)for(const x of d.lanes)if(x.parent===l.key)delete x.parent;},'已删除泳道（可撤销）')&&select({type:'plan'});
    if(s.type==='bar')apply(d=>{const [l]=findBar(d,s.key);l.bars=l.bars.filter(b=>b.key!==s.key);},'已删除阶段（可撤销）')&&select({type:'plan'});
    if(s.type==='ms')apply(d=>{const [l]=findMs(d,s.key);l.milestones=l.milestones.filter(m=>m.key!==s.key);},'已删除里程碑（可撤销）')&&select({type:'plan'});
  }
  function moveLane(key,dir){
    apply(d=>{const L=d.lanes,i=L.findIndex(l=>l.key===key),l=L[i];
      const block=k=>{const j=L.findIndex(x=>x.key===k);let e=j+1;if(!L[j].parent)while(e<L.length&&L[e].parent===k)e++;return [j,e];};
      if(l.parent){const sib=L.map((x,j)=>[x,j]).filter(([x])=>x.parent===l.parent).map(([,j])=>j),p=sib.indexOf(i),q=p+dir;if(q<0||q>=sib.length)throw Error('已经在最'+(dir<0?'上':'下')+'面');
        [L[i],L[sib[q]]]=[L[sib[q]],L[i]];return;}
      const tops=L.map((x,j)=>[x,j]).filter(([x])=>!x.parent).map(([x])=>x.key),p=tops.indexOf(key),q=p+dir;if(q<0||q>=tops.length)throw Error('已经在最'+(dir<0?'上':'下')+'面');
      const [a0,a1]=block(key),mine=L.slice(a0,a1);L.splice(a0,a1-a0);const [b0,b1]=block(tops[q]);L.splice(dir<0?b0:b1,0,...mine);},dir<0?'已上移':'已下移');
  }
  function nest(key,on){
    apply(d=>{const L=d.lanes,i=L.findIndex(l=>l.key===key),l=L[i];
      if(on){if(L.some(x=>x.parent===key))throw Error('这条泳道有下级，不能再设为下级（最多两级）');let j=i-1;while(j>=0&&L[j].parent)j--;if(j<0)throw Error('上面没有可作上级的泳道');l.parent=L[j].key;}
      else{const p=l.parent;delete l.parent;delete l.collapsed;L.splice(i,1);let e=L.findIndex(x=>x.key===p)+1;while(e<L.length&&L[e].parent===p)e++;L.splice(e,0,l);
        if(!L.some(x=>x.parent===p)){const P=L.find(x=>x.key===p);delete P.collapsed;}}},on?'已设为上一条泳道的下级':'已取消下级');
  }
  // ---- right: properties of the selection
  const row=(label,...ctl)=>h('label',{class:'kzs-row'},h('span',{class:'kzs-label',text:label}),...ctl);
  const block=(label,...ctl)=>h('div',{class:'kzs-row'},h('span',{class:'kzs-label',text:label}),...ctl);
  function textIn(value,onCommit,opt={}){const i=h('input',{type:'text',class:'kzs-input',value:value||'',placeholder:opt.placeholder||'',maxlength:opt.max||40});
    const go=()=>{const v=i.value.trim();if(v!==(value||''))onCommit(v);};i.addEventListener('change',go);i.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();go();}});return i;}
  function toggle(on,label,onChange){const b=h('button',{type:'button',role:'switch','aria-checked':on?'true':'false',class:'kzs-switch'+(on?' is-on':''),onclick:()=>onChange(!on)},h('span'),label);return b;}
  function renderProps(){
    const P=S.props,s=S.sel||{type:'plan'},d=S.doc,g=gran(d);P.replaceChildren();
    const head=(t,sub)=>P.append(h('div',{class:'kzs-props-head'},h('b',{text:t}),sub?h('small',{text:sub}):null));
    const phases=d.phases&&d.phases.length?d.phases:C().PHASES,PH=T().charts.phases||[];
    if(s.type==='plan'){
      head('计划设置','精度、阶段与显示');
      P.append(block('阶段',h('div',{class:'kzs-phases'},...phases.map((p,i)=>h('div',{class:'kzs-phase'},h('span',{class:'kzs-sw',style:`background:${PH[i]}`}),
        textIn(p,v=>{if(!v)return;apply(dd=>{const ps=[...(dd.phases&&dd.phases.length?dd.phases:C().PHASES)];const old=ps[i];ps[i]=v;dd.phases=ps;for(const l of dd.lanes)for(const b of l.bars||[])if(b.phase===old)b.phase=v;},'阶段名已更新');}),
        h('button',{type:'button',class:'kzs-icon-btn is-small','aria-label':'删除阶段',title:'删除（未被使用时）',onclick:()=>apply(dd=>{const ps=[...(dd.phases&&dd.phases.length?dd.phases:C().PHASES)];const used=dd.lanes.some(l=>(l.bars||[]).some(b=>b.phase===ps[i]));if(used)throw Error(`「${ps[i]}」还有阶段条在用，先改掉它们`);if(ps.length<2)throw Error('至少保留一个阶段');ps.splice(i,1);dd.phases=ps;},'已删除阶段')},'×'))),
        phases.length<PH.length?h('button',{type:'button',class:'kzs-link',onclick:()=>apply(dd=>{const ps=[...(dd.phases&&dd.phases.length?dd.phases:C().PHASES)];ps.push(`阶段 ${ps.length+1}`);dd.phases=ps;},'已加一个阶段名')},'＋ 阶段名'):null)));
      P.append(h('p',{class:'kzs-note',text:'阶段色按顺序取品牌黄 → 品牌橙五档（tokens.charts.phases），不单独调色。精度只管阶段条；里程碑总是可以精确到日。'}));
      const M=C().program(d);
      P.append(block('可选层',h('div',{class:'kzs-chips'},...[['status','状态'],['progress','进度'],['baseline','原计划'],['levels','两级泳道']].map(([k,t])=>h('span',{class:'kzs-chip'+(M.layers[k]?' is-on':''),text:t+(M.layers[k]?' · 有数据':' · 无数据不显示')})))));
      return;
    }
    if(s.type==='lane'){
      const i=d.lanes.findIndex(l=>l.key===s.key),l=d.lanes[i];if(!l){S.sel={type:'plan'};return renderProps();}
      const kids=d.lanes.filter(x=>x.parent===l.key).length;
      head('泳道',l.parent?'下级泳道':'');
      P.append(row('名称',textIn(l.name,v=>{if(!v)return say('泳道名称不能为空',true);apply(dd=>{dd.lanes[i].name=v;},'泳道名称已更新');})));
      P.append(row('备注',textIn(l.note,v=>apply(dd=>{if(v)dd.lanes[i].note=v;else delete dd.lanes[i].note;},'备注已更新'),{placeholder:'如研究编号、例数'})));
      P.append(block('层级',toggle(!!l.parent,'作为上一条泳道的下级',on=>nest(l.key,on)),kids?toggle(!!l.collapsed,`收起 ${kids} 条下级（合并显示）`,on=>apply(dd=>{if(on)dd.lanes[i].collapsed=true;else delete dd.lanes[i].collapsed;},on?'已收起':'已展开')):null));
      P.append(block('顺序',h('div',{class:'kzs-inline'},h('button',{type:'button',class:'kzs-btn is-small',onclick:()=>moveLane(l.key,-1)},'上移'),h('button',{type:'button',class:'kzs-btn is-small',onclick:()=>moveLane(l.key,1)},'下移'),
        h('button',{type:'button',class:'kzs-btn is-small',onclick:()=>dupLane(i)},'复制'))));
      P.append(h('div',{class:'kzs-danger'},h('button',{type:'button',class:'kzs-btn is-danger',onclick:removeSel},'删除泳道')));
      return;
    }
    if(s.type==='bar'){
      const [l,b]=findBar(d,s.key);if(!b){S.sel={type:'plan'};return renderProps();}
      const set=(fn,msg)=>apply(dd=>{const [,bb]=findBar(dd,s.key);fn(bb,dd);},msg);
      head('阶段',l.name);
      P.append(block('阶段',h('div',{class:'kzs-seg is-wrap'},...phases.map((p,k)=>h('button',{type:'button',class:'kzs-seg-b'+(b.phase===p?' is-on':''),'aria-pressed':b.phase===p?'true':'false',onclick:()=>set(bb=>{bb.phase=p;},'阶段已更新')},h('span',{class:'kzs-sw',style:`background:${PH[k]}`}),p)))));
      P.append(row('名称',textIn(b.label,v=>set(bb=>{if(v)bb.label=v;else delete bb.label;},'名称已更新'),{placeholder:`缺省显示「${b.phase}」`})));
      P.append(block(`起止（${GRAN_TXT[g]}）`,h('div',{class:'kzs-inline'},
        picker({value:b.start,mode:g,label:'开始',onPick:v=>set(bb=>{bb.start=v;if(span(bb.end)[1]<=span(v)[0])bb.end=conv(v,g,'end');},'开始时间已更新')}),h('span',{class:'kzs-dash',text:'→'}),
        picker({value:b.end,mode:g,label:'结束',onPick:v=>set(bb=>{bb.end=v;if(span(v)[1]<=span(bb.start)[0])bb.start=conv(v,g,'start');},'结束时间已更新')}))));
      P.append(block('状态',h('div',{class:'kzs-seg is-wrap'},...STATUS.map(([k,t])=>{const on=(b.status||'')===k;return h('button',{type:'button',class:'kzs-seg-b'+(on?' is-on':''),'aria-pressed':on?'true':'false',onclick:()=>set(bb=>{if(k)bb.status=k;else delete bb.status;},'状态已更新')},k?ico(STATUS_ICON[k]):null,t);}))));
      const hasP=b.progress!=null;
      P.append(block('进度',toggle(hasP,'显示完成百分比',on=>set(bb=>{if(on)bb.progress=bb.progress??0;else delete bb.progress;},on?'已显示进度':'已隐藏进度')),
        hasP?(()=>{const n=h('input',{type:'number',min:0,max:100,value:b.progress,class:'kzs-input is-num','aria-label':'完成百分比'}),
          r=h('input',{type:'range',min:0,max:100,step:5,value:b.progress,class:'kzs-range','aria-label':'完成百分比'});
          r.addEventListener('input',()=>{n.value=r.value;});r.addEventListener('change',()=>set(bb=>{bb.progress=+r.value;},'进度已更新'));
          n.addEventListener('change',()=>set(bb=>{bb.progress=Math.max(0,Math.min(100,+n.value||0));},'进度已更新'));
          return h('div',{class:'kzs-inline'},r,n,h('span',{text:'%'}));})():null));
      // exposure (round 9): what this study adds to the cumulative exposure figure of the same plan (ICH E1 check)
      const x=b.exposure;
      P.append(block('暴露（累计暴露图）',toggle(!!x,'计入研究药物累计暴露',on=>set(bb=>{if(on)bb.exposure={n:100};else delete bb.exposure;},on?'已计入累计暴露':'已不计入累计暴露')),
        x?(()=>{const num=(label,v,fn,{min=0,max,step=1,ph}={})=>{const n=h('input',{type:'number',min,max,step,value:v??'',placeholder:ph||'',class:'kzs-input is-num','aria-label':label});
            n.addEventListener('change',()=>{const raw=n.value.trim();set(bb=>{fn(bb.exposure,raw===''?null:+raw);fit(bb.exposure);},`${label}已更新`);});return h('label',{class:'kzs-xp-f'},h('span',{text:label}),n);};
          const exOf=o=>o.exposed??C().pyRound(o.n*(1-(o.ctrl||0))),ex=exOf(x);
          // the longer bands never exceed the shorter ones (a smaller study shrinks them with it)
          const fit=o=>{const e=exOf(o);if(o.w26!=null&&o.w26>e)o.w26=e;if(o.w52!=null&&o.w52>(o.w26??e))o.w52=o.w26??e;};
          const chk=(o,k,v,lim)=>{if(v==null){delete o[k];return;}if(!Number.isInteger(v)||v<0)throw Error('例数须是不小于 0 的整数');if(lim!=null&&v>lim)throw Error(`不能超过 ${lim} 例`);o[k]=v;};
          return h('div',{class:'kzs-xp'},
            num('样本量',x.n,(o,v)=>{if(!Number.isInteger(v)||v<1)throw Error('样本量须为正整数');o.n=v;if(o.exposed!=null&&o.exposed>v)o.exposed=v;}),
            num('对照比例 %',x.ctrl!=null?Math.round(x.ctrl*1000)/10:0,(o,v)=>{v=v??0;if(!(v>=0&&v<100))throw Error('对照比例须在 0–100% 之间（不含 100%）');if(v)o.ctrl=Math.round(v*10)/1000;else delete o.ctrl;},{max:99,step:.1}),
            num('暴露例数',x.exposed,(o,v)=>chk(o,'exposed',v,o.n),{ph:`按比例 ${ex}`}),
            num('≥26 周',x.w26,(o,v)=>chk(o,'w26',v,exOf(o)),{ph:'不填'}),
            num('≥52 周',x.w52,(o,v)=>chk(o,'w52',v,o.w26??exOf(o)),{ph:'不填'}),
            h('p',{class:'kzs-note',text:`暴露 = 样本量 × (1 − 对照比例)，暴露例数可覆盖（如延展只计安慰剂转入）；计入时点为研究结束 ${b.end}${x.at?`（已指定 ${x.at}）`:''}。`}),
            x.at?h('button',{type:'button',class:'kzs-link',onclick:()=>set(bb=>{delete bb.exposure.at;},'计入时点已改回研究结束')},'计入时点改回研究结束'):null);})():null));
      const bl=b.baseline;
      P.append(block('原计划',toggle(!!bl,'记录原计划，显示推迟或提前',on=>set(bb=>{if(on)bb.baseline={start:bb.start,end:bb.end};else delete bb.baseline;},on?'已把当前时间记为原计划':'已去掉原计划')),
        bl?h('div',{class:'kzs-inline'},picker({value:bl.start,mode:unitOf(bl.start),label:'原计划开始',onPick:v=>set(bb=>{bb.baseline.start=v;},'原计划已更新')}),h('span',{class:'kzs-dash',text:'→'}),
          picker({value:bl.end,mode:unitOf(bl.end),label:'原计划结束',onPick:v=>set(bb=>{bb.baseline.end=v;},'原计划已更新')})):null,
        bl?h('button',{type:'button',class:'kzs-link',onclick:()=>set(bb=>{bb.baseline={start:bb.start,end:bb.end};},'原计划已重置为当前时间')},'以当前时间为原计划'):null));
      if(b.color)P.append(block('颜色',h('div',{class:'kzs-inline'},h('span',{class:'kzs-sw is-big',style:`background:${b.color}`}),h('button',{type:'button',class:'kzs-link',onclick:()=>set(bb=>{delete bb.color;},'已恢复阶段色')},'恢复阶段色'))));
      P.append(h('div',{class:'kzs-danger'},h('button',{type:'button',class:'kzs-btn is-danger',onclick:removeSel},'删除阶段')));
      return;
    }
    if(s.type==='ms'){
      const [l,m]=findMs(d,s.key);if(!m){S.sel={type:'plan'};return renderProps();}
      const set=(fn,msg)=>apply(dd=>{const [,mm]=findMs(dd,s.key);fn(mm,dd);},msg);
      head('里程碑',l.name);
      P.append(row('名称',textIn(m.label,v=>{if(!v)return say('里程碑名称不能为空',true);set(mm=>{mm.label=v;},'名称已更新');})));
      P.append(block('日期',picker({value:m.at,mode:'day',label:'日期',onPick:v=>set(mm=>{mm.at=v;},'日期已更新')}),unitOf(m.at)!=='day'?h('small',{class:'kzs-note',text:`现写作${unitOf(m.at)==='quarter'?'季度':'月份'}，选一天即精确到日`}):null));
      P.append(block('类型',h('div',{class:'kzs-seg is-wrap'},...Object.entries(KINDS).map(([k,t])=>{const on=(m.kind||'other')===k&&!m.icon;return h('button',{type:'button',class:'kzs-seg-b'+(on?' is-on':''),'aria-pressed':on?'true':'false',onclick:()=>set(mm=>{mm.kind=k;delete mm.icon;},'类型已更新')},glyph(k),t);}))));
      P.append(block('图标',h('div',{class:'kzs-icons'},...MS_ICONS.filter(n=>global.KZIcons?.names?.includes(n)).map(n=>h('button',{type:'button',class:'kzs-icon-pick'+(m.icon===n?' is-on':''),'aria-label':n,'aria-pressed':m.icon===n?'true':'false',title:n,onclick:()=>set(mm=>{if(mm.icon===n)delete mm.icon;else mm.icon=n;},'图标已更新')},ico(n)))),
        h('small',{class:'kzs-note',text:'选图标后取代类型图形；再点一次恢复类型图形。'})));
      P.append(block('标记',h('div',{class:'kzs-stack'},toggle(!!m.risk,'风险（红色）',on=>set(mm=>{if(on)mm.risk=true;else delete mm.risk;},on?'已标为风险':'已取消风险')),
        l.parent?toggle(!!m.major,'上级收起时仍显示',on=>set(mm=>{if(on)mm.major=true;else delete mm.major;},'已更新')):null)));
      P.append(block('原计划',toggle(m.baseline!=null,'记录原计划日期',on=>set(mm=>{if(on)mm.baseline=mm.at;else delete mm.baseline;},on?'已把当前日期记为原计划':'已去掉原计划')),
        m.baseline!=null?picker({value:m.baseline,mode:'day',label:'原计划日期',onPick:v=>set(mm=>{mm.baseline=v;},'原计划已更新')}):null));
      P.append(block('所在泳道',(()=>{const sl=h('select',{class:'kzs-input','aria-label':'所在泳道'},...d.lanes.map(x=>h('option',{value:x.key,selected:x.key===l.key,text:(x.parent?'　':'')+x.name})));
        sl.addEventListener('change',()=>apply(dd=>{const [ol,mm]=findMs(dd,s.key);ol.milestones=ol.milestones.filter(x=>x.key!==s.key);const nl=dd.lanes.find(x=>x.key===sl.value);(nl.milestones=nl.milestones||[]).push(mm);},'已移到另一条泳道'));return sl;})()));
      P.append(h('div',{class:'kzs-danger'},h('button',{type:'button',class:'kzs-btn is-danger',onclick:removeSel},'删除里程碑')));
    }
  }
  function dupLane(i){
    let k2;apply(dd=>{const l=dd.lanes[i],c=clone(l),used=keysOf(dd),fresh=p=>{let n=1;while(used.has(p+n))n++;used.add(p+n);return p+n;};
      c.key=k2=fresh('lane-');c.name+=' 副本';c.bars=(c.bars||[]).map(b=>({...b,key:fresh('bar-')}));c.milestones=(c.milestones||[]).map(m=>({...m,key:fresh('ms-')}));delete c.collapsed;
      let e=i+1;if(!l.parent)while(e<dd.lanes.length&&dd.lanes[e].parent===l.key)e++;dd.lanes.splice(e,0,c);},'已复制泳道')&&select({type:'lane',key:k2});
  }
  // ---- saving
  function toggleMenu(force){
    const want=force??!S.menu;if(S.menu){const had=S.menu.contains(document.activeElement);S.menu.remove();S.menu=null;if(had)S.saveB.querySelector("button")?.focus();}if(!want)return;
    const fsOK=typeof global.showSaveFilePicker==='function',store=storeState();
    const it=(t,sub,fn,dis)=>h('button',{type:'button',role:'menuitem',class:'kzs-menu-item',disabled:!!dis,onclick:()=>{toggleMenu(false);fn();}},h('b',{text:t}),h('small',{text:sub}));
    S.menu=h('div',{class:'kzs-menu-pop',role:'menu'},
      it('保存到本文件',store?(fsOK?(S.handle?`写回 ${S.handle.name}（⌘/Ctrl+S）`:'选中当前这份 HTML 文件，只替换其中的数据'):'这个浏览器不能写文件：用「导出数据」'):'这个页面的数据不在 KZ_DECK_DATA 里：用「导出数据」',saveToFile,!store||!fsOK),
      it('导出数据（JSON）','交给 Agent 重建 PPTX 页或其他产物',exportJSON),
      it('复制数据','复制 JSON 到剪贴板',copyJSON),
      it('导入数据（JSON）','用一份计划替换当前（可撤销）',importJSON),
      it('丢弃草稿','删除这台电脑上保存的未保存修改',()=>{try{localStorage.removeItem(draftKey(S.inst));}catch{}say('草稿已丢弃');}));
    S.saveB.append(S.menu);S.menu.querySelector('button:not([disabled])')?.focus();
  }
  const storeState=()=>!!(S.inst.gid&&global.KZ_DECK_DATA&&Object.prototype.hasOwnProperty.call(global.KZ_DECK_DATA,S.inst.gid));
  const fileName=()=>decodeURIComponent(location.pathname.split('/').pop()||'index.html');
  // Python's json.dumps(ensure_ascii=False) layout (", " and ": "), so a saved file differs from a rebuilt one only in data
  function pyjson(v){if(Array.isArray(v))return '['+v.map(pyjson).join(', ')+']';if(v&&typeof v==='object')return '{'+Object.entries(v).map(([k,x])=>JSON.stringify(k)+': '+pyjson(x)).join(', ')+'}';return JSON.stringify(v);}
  const BLOCK=/(window\.KZ_DECK_DATA\s*=\s*)(\{[\s\S]*?\})(;\s*<\/script>)/;
  // top-level entries of a JSON object text: [{key, vs, ve}] (value spans), strings and nesting respected
  function entries(t){
    const out=[];let i=t.indexOf('{')+1,depth=1,key=null,vs=-1;
    const str=j=>{let k=j+1;while(t[k]!=='"'){if(t[k]==='\\')k++;k++;}return k;};
    while(i<t.length&&depth>0){const c=t[i];
      if(c==='"'){const e=str(i);if(depth===1&&key===null&&vs<0){key=JSON.parse(t.slice(i,e+1));}i=e+1;continue;}
      if(c===':'&&depth===1&&key!==null&&vs<0){vs=i+1;while(/\s/.test(t[vs]))vs++;}
      else if(c==='{'||c==='[')depth++;
      else if(c==='}'||c===']'){depth--;if(depth===0&&key!==null){out.push({key,vs,ve:i});}}
      else if(c===','&&depth===1){out.push({key,vs,ve:i});key=null;vs=-1;}
      i++;}
    return out.map(e=>({...e,ve:(()=>{let k=e.ve;while(/\s/.test(t[k-1]))k--;return k;})()}));
  }
  // the file's data block with the page's current Gantt data written in (every Gantt of the deck, so edits on other slides
  // are saved too). Only the entries that changed are replaced, as text, so the rest of the file stays byte for byte;
  // a file that is not this page's (no data block, unparsable, or without this Gantt's entry) is refused.
  function replaceData(text,store,gid){
    const m=BLOCK.exec(text);if(!m)throw Error('这个文件里没有 KZ_DECK_DATA 数据块；它不是当前页面的文件，没有写入');
    let data;try{data=JSON.parse(m[2]);}catch{throw Error('文件里的数据块无法解析；为安全起见没有写入');}
    if(!(gid in data))throw Error('这个文件里没有当前甘特的数据（'+gid+'）；它不是当前页面的文件，没有写入');
    let block=m[2];
    for(const e of entries(block).reverse()){const v=store[e.key];if(!(e.key in store)||!isPlanOrGantt(v)||JSON.stringify(v)===JSON.stringify(data[e.key]))continue;
      block=block.slice(0,e.vs)+pyjson(v)+block.slice(e.ve);}
    return text.slice(0,m.index)+m[1]+block+m[3]+text.slice(m.index+m[0].length);
  }
  const isPlanOrGantt=v=>!!v&&typeof v==='object'&&(Array.isArray(v.lanes)||(Array.isArray(v.tasks)&&Number.isInteger(v.min)));
  async function saveToFile(){
    if(!S||!storeState()||typeof global.showSaveFilePicker!=='function')return say('这个页面不能直接写回文件：请用「导出数据」',true);
    try{
      let handle=S.handle||await idbGet();
      if(handle&&(await handle.queryPermission?.({mode:'readwrite'}))!=='granted'&&(await handle.requestPermission?.({mode:'readwrite'}))!=='granted')handle=null;
      if(!handle)handle=await global.showSaveFilePicker({suggestedName:fileName(),types:[{description:'HTML',accept:{'text/html':['.html','.htm']}}]});
      if(handle.name!==fileName())throw Error(`选中的是「${handle.name}」，不是当前页面「${fileName()}」；没有写入`);
      const text=await (await handle.getFile()).text(),out=replaceData(text,global.KZ_DECK_DATA,S.inst.gid);
      const w=await handle.createWritable();await w.write(out);await w.close();
      S.handle=handle;idbPut(handle);S.inst.markSaved();try{localStorage.removeItem(draftKey(S.inst));}catch{}
      say(`已保存到 ${handle.name}（${new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}）`);
    }catch(e){if(e&&e.name==='AbortError')return say('已取消保存');say(e.message||String(e),true);}
  }
  function download(name,text,type){const a=h('a',{href:URL.createObjectURL(new Blob([text],{type})),download:name});document.body.append(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);}
  function exportJSON(){download(`${S.inst.gid||'gantt'}.json`,JSON.stringify(S.doc,null,1)+'\n','application/json');say('已导出计划数据（JSON）');}
  async function copyJSON(){try{await navigator.clipboard.writeText(JSON.stringify(S.doc,null,1));say('已复制计划数据');}catch{say('浏览器不允许写剪贴板：请用「导出数据」',true);}}
  function importJSON(){const i=h('input',{type:'file',accept:'.json,application/json'});i.addEventListener('change',async()=>{const f=i.files[0];if(!f)return;
    try{let d=JSON.parse(await f.text());if(d&&d.program&&Array.isArray(d.program.lanes))d=d.program;if(!Array.isArray(d.lanes))d=G().fromLegacy(d);C().program(d);S.lock=false;apply(x=>{for(const k of Object.keys(x))delete x[k];Object.assign(x,clone(d));},'已导入（可撤销）');}
    catch(e){say('导入失败：'+e.message,true);}});i.click();}
  // file handles persist across sessions in IndexedDB (the browser asks again for write permission)
  function idb(){return new Promise((res,rej)=>{const r=indexedDB.open('kz-gantt',1);r.onupgradeneeded=()=>r.result.createObjectStore('handles');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});}
  async function idbGet(){try{const db=await idb();return await new Promise(res=>{const q=db.transaction('handles').objectStore('handles').get(location.href);q.onsuccess=()=>res(q.result||null);q.onerror=()=>res(null);});}catch{return null;}}
  async function idbPut(hd){try{const db=await idb();db.transaction('handles','readwrite').objectStore('handles').put(hd,location.href);}catch{}}
  // drafts: every change (in the studio or in place) is kept on this computer until it is saved or discarded
  function saveDraft(inst=S?.inst){if(!inst||(S&&S.inst===inst&&S.pending))return;try{const dirty=inst.getDirty();if(!dirty){localStorage.removeItem(draftKey(inst));return;}localStorage.setItem(draftKey(inst),JSON.stringify({at:Date.now(),doc:inst.getDoc()}));}catch{}}
  function offerDraft(){
    let dr=null;try{dr=JSON.parse(localStorage.getItem(draftKey(S.inst))||'null');}catch{}
    if(!dr||!dr.doc||JSON.stringify(dr.doc)===JSON.stringify(S.doc)){S.banner.hidden=true;return;}
    S.pending=true;   // the draft stays on disk until 恢复 or 丢弃 (or the first edit, which supersedes it)
    const when=new Date(dr.at).toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
    S.banner.hidden=false;S.banner.replaceChildren(h('span',{text:`有 ${when} 未保存的修改`}),
      h('button',{type:'button',class:'kzs-btn is-small is-primary',onclick:()=>{try{C().program(dr.doc);S.pending=false;apply(x=>{for(const k of Object.keys(x))delete x[k];Object.assign(x,clone(dr.doc));},'已恢复草稿');}catch(e){say('草稿无法恢复：'+e.message,true);}S.banner.hidden=true;}},'恢复'),
      h('button',{type:'button',class:'kzs-btn is-small',onclick:()=>{S.pending=false;try{localStorage.removeItem(draftKey(S.inst));}catch{}S.banner.hidden=true;say('草稿已丢弃');}},'丢弃'));
  }
  function noteChange(inst){if(!inst.gid||(S&&(S.inst===inst||S.preview===inst)))return;saveDraft(inst);}
  // ---- texts on the page that mention what changed (bound texts update themselves, 08 GANTT-07)
  function renderAffect(){
    if(!S)return;const base=S.inst.getBaseline(),bd=Array.isArray(base.lanes)?base:G().fromLegacy(base),now=S.doc,changed=[];
    const flat=d=>{const m=new Map();for(const l of d.lanes){for(const b of l.bars||[])m.set(b.key,[l.name,b.label||b.phase,JSON.stringify(b)]);for(const x of l.milestones||[])m.set(x.key,[l.name,x.label,JSON.stringify(x)]);}return m;};
    const a=flat(now),b=flat(bd);for(const [k,v] of b){const w=a.get(k);if(!w||w[2]!==v[2])changed.push(v);}
    const page=S.inst.root.closest('.slide')||S.inst.root.closest('section,main')||document.body;
    const texts=[...page.querySelectorAll('.kzl-card p,.kzl-card li,.kz-card p,aside.notes')].filter(e=>!e.querySelector('[data-kz-bind]')&&!S.inst.root.contains(e));
    const hits=texts.filter(e=>changed.some(([ln,lab])=>e.textContent.includes(lab)||e.textContent.includes(ln)));
    S.affect.replaceChildren(...(hits.length?[h('span',{class:'kzs-label',text:`可能要改的文字 ${hits.length} 处：`}),...hits.slice(0,4).map(e=>h('span',{class:'kzs-quote',title:e.textContent,text:(e.matches('aside.notes')?'讲稿：':'')+e.textContent.trim().slice(0,26)+(e.textContent.trim().length>26?'…':'')}))]:[]));
  }
  // ---- T opens the studio for the Gantt in view (the active slide, an open drill-down, else the one nearest the centre)
  function current(){
    const all=G()?.instances?.()||[];if(!all.length)return null;
    // a Gantt kept off-screen for another figure (the cumulative exposure) stands at that figure (inst.anchor)
    const at=i=>i.anchor||i.root;
    const vis=all.filter(i=>{const r=at(i).getBoundingClientRect();return r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight;});
    const dlg=vis.find(i=>at(i).closest('dialog[open],.kz-dialog[open]'));if(dlg)return dlg;
    const act=vis.find(i=>at(i).closest('.slide.is-active'));if(act)return act;
    const mid=innerHeight/2;return vis.sort((p,q)=>{const a=at(p).getBoundingClientRect(),b=at(q).getBoundingClientRect();return Math.abs((a.top+a.bottom)/2-mid)-Math.abs((b.top+b.bottom)/2-mid);})[0]||null;
  }
  function bindKey(){
    if(keyBound)return;keyBound=true;
    global.addEventListener('keydown',e=>{
      if(S||e.metaKey||e.ctrlKey||e.altKey||(e.key!=='t'&&e.key!=='T'))return;
      if(e.target?.closest?.('input,textarea,select,[contenteditable=""],[contenteditable=true]'))return;
      const inst=current();if(!inst)return;
      e.preventDefault();e.stopImmediatePropagation();open(inst,{focus:inst.getSelected()});
    },true);
  }
  if(typeof document!=='undefined')bindKey();
  global.KZGanttStudio={open,close,noteChange,isOpen:()=>!!S,state:()=>S&&{doc:clone(S.doc),sel:S.sel,message:S.msg.textContent},replaceData,pyjson};
})(window);
