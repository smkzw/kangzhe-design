/* Quarter Gantt: ECharts custom series, live editing, one canonical interval model. */
(function(global){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  const qindex=(year,q)=>{const y=Number(year),v=Number(q);if(!Number.isInteger(y)||y<1||!Number.isInteger(v)||v<1||v>4)throw Error('年份/季度无效');return y*4+v-1;};
  const fromIndex=i=>({year:Math.floor(i/4),quarter:(i%4+4)%4+1});
  const qlabel=i=>{const v=fromIndex(Math.round(i));return `${v.year} Q${v.quarter}`;};
  function validate(data){
    if(!data||!Number.isInteger(data.min)||!Number.isInteger(data.max)||data.max<=data.min)throw Error('甘特轴范围无效');
    if(!Array.isArray(data.tasks)||!data.tasks.length)throw Error('甘特缺少任务');
    const ids=new Set();
    for(const t of data.tasks){
      if(!t.id||ids.has(t.id))throw Error('任务 id 缺失或重复');ids.add(t.id);
      if(typeof t.label!=='string'||!t.label.trim())throw Error('任务标签为空');
      if(!Number.isInteger(t.start)||!Number.isInteger(t.end)||t.start>=t.end||t.start<data.min||t.end>data.max)throw Error('任务时间越界或区间无效');
    }
    return true;
  }
  function mount(root,input,options={}){
    if(!global.echarts)throw Error('缺少 ECharts');validate(input);
    const baseline=clone(input);let data=clone(input),selected=data.tasks[0].id,undo=[],drag=null,disposed=false;
    const abort=new AbortController(),signal=abort.signal;let progress=1,raf=0;
    const mq=matchMedia('(prefers-reduced-motion: reduce)');
    root.classList.add('kz-gantt','kz-interactive');root.dataset.kzEditing='true';
    const plot=document.createElement('div');plot.className='kz-gantt-plot';plot.tabIndex=0;plot.setAttribute('role','application');plot.setAttribute('aria-label','可编辑季度甘特图；左右方向键移动，Shift 加方向键调整结束季度');
    const editor=document.createElement('div');editor.className='kz-gantt-editor';
    const lab=(text)=>{const x=document.createElement('label');x.textContent=text;return x;};
    const select=document.createElement('select');select.setAttribute('aria-label','选择项目');
    const taskLabel=lab('选择项目');taskLabel.append(select);editor.append(taskLabel);
    const fields=document.createElement('div');fields.className='kz-gantt-fields';editor.append(fields);
    const inputs={};
    for(const [key,label] of [['sy','开始年份'],['sq','开始季度'],['ey','结束年份'],['eq','结束季度']]){
      const wrapper=lab(label),field=document.createElement('select');field.setAttribute('aria-label',label);field.dataset.kzField=key;inputs[key]=field;
      const minYear=fromIndex(data.min).year,maxYear=fromIndex(data.max-1).year;
      const values=key.endsWith('q')?[1,2,3,4]:Array.from({length:maxYear-minYear+1},(_,i)=>minYear+i);
      for(const value of values){const o=document.createElement('option');o.value=value;o.textContent=key.endsWith('q')?'Q'+value:String(value);field.append(o);}
      wrapper.append(field);fields.append(wrapper);
    }
    const apply=document.createElement('button');apply.type='button';apply.className='kz-button';apply.textContent='应用时间';apply.style.marginTop='16px';editor.append(apply);
    const hint=document.createElement('p');hint.className='kz-gantt-status';hint.setAttribute('aria-live','polite');editor.append(hint);
    const dirty=document.createElement('div');dirty.className='kz-dirty';dirty.hidden=true;
    const dirtyText=document.createElement('span');const undoB=document.createElement('button'),resetB=document.createElement('button');
    for(const [b,text] of [[undoB,'撤销'],[resetB,'还原全部']]){b.type='button';b.className='kz-button';b.textContent=text;}
    dirty.append(dirtyText,undoB,resetB);root.replaceChildren(plot,editor,dirty);
    for(const t of data.tasks){const o=document.createElement('option');o.value=t.id;o.textContent=t.label;select.append(o);}
    const chart=echarts.init(plot,null,{renderer:'canvas'});
    function task(){return data.tasks.find(t=>t.id===selected);}
    function countDirty(){return data.tasks.filter(t=>{const b=baseline.tasks.find(x=>x.id===t.id);return t.start!==b.start||t.end!==b.end;}).length;}
    function syncFields(){const t=task(),s=fromIndex(t.start),e=fromIndex(t.end-1);select.value=selected;inputs.sy.value=s.year;inputs.sq.value=s.quarter;inputs.ey.value=e.year;inputs.eq.value=e.quarter;}
    function status(message=''){hint.textContent=message;const n=countDirty();dirty.hidden=!n;dirtyText.textContent=`已修改 ${n} 项`;undoB.disabled=!undo.length;}
    function draw(){
      const unit=root.closest('.deck')&&document.body.dataset.fit==='fluid'?Math.max(1,innerHeight/KZ_TOKENS.wide.htmlppt_reference_height):1;
      chart.setOption({animation:false,grid:{left:(chart.getWidth()<480?96:126)*unit,right:24*unit,top:38*unit,bottom:44*unit},textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit},
        xAxis:{type:'value',min:data.min,max:data.max,interval:1,axisLabel:{fontSize:16*unit,color:KZ_TOKENS.colors.body,formatter:v=>{if(v>=data.max)return '';const q=fromIndex(v);if(v===data.min&&q.quarter!==1)return `${q.year}Q${q.quarter}`;return q.quarter===1?String(q.year):((chart.getWidth()-150*unit)/(data.max-data.min)>=30*unit?'Q'+q.quarter:'');}},axisTick:{show:false},splitLine:{lineStyle:{color:'#E3E7EC'}},axisLine:{lineStyle:{color:'#CDD3D9'}}},
        yAxis:{type:'category',inverse:true,data:data.tasks.map(t=>t.label),axisLabel:{fontSize:16*unit,color:KZ_TOKENS.colors.body,width:(chart.getWidth()<480?86:116)*unit,overflow:'break'},axisTick:{show:false},axisLine:{show:false}},
        tooltip:{show:false},series:[{type:'custom',coordinateSystem:'cartesian2d',id:'kz-gantt-tasks',silent:true,
          renderItem(params,api){const row=api.value(0),start=api.coord([api.value(1),row]),end=api.coord([api.value(2),row]),height=Math.min(36*unit,api.size([0,1])[1]*.56),t=data.tasks[row];
            const rect=echarts.graphic.clipRectByRect({x:start[0],y:start[1]-height/2,width:end[0]-start[0],height},{x:params.coordSys.x,y:params.coordSys.y,width:params.coordSys.width,height:params.coordSys.height});
            if(!rect)return null;const color=t.color||data.taskColor||KZ_TOKENS.departments[t.department]?.color||KZ_TOKENS.colors.brand;
            return {type:'rect',shape:{...rect,r:7*unit},style:{fill:color,opacity:.78,stroke:t.id===selected?KZ_TOKENS.colors.ink:'transparent',lineWidth:1.5}};},
          data:data.tasks.map((t,i)=>[i,t.start,t.start+(t.end-t.start)*progress]),encode:{x:[1,2],y:0}}]},{notMerge:true});
      status();options.onProgress?.(progress,clone(data));
    }
    function finish(){cancelAnimationFrame(raf);raf=0;progress=1;draw();}
    function play(duration=1000){finish();if(mq.matches)return;let start=null;
      const tick=now=>{if(disposed)return;start??=now;const p=Math.min(1,(now-start)/duration);progress=1-Math.pow(1-p,3);draw();if(p<1)raf=requestAnimationFrame(tick);else raf=0;};raf=requestAnimationFrame(tick);
    }
    mq.addEventListener('change',()=>{if(mq.matches)finish();},{signal});
    document.addEventListener('visibilitychange',()=>{if(document.hidden)finish();},{signal});
    global.addEventListener('beforeprint',finish,{signal});
    function local(event){const r=plot.getBoundingClientRect();return [(event.clientX-r.left)*(plot.clientWidth/r.width),(event.clientY-r.top)*(plot.clientHeight/r.height)];}
    function axisAt(event){return chart.convertFromPixel({xAxisIndex:0},local(event)[0]);}
    function rowGeometry(t){const i=data.tasks.findIndex(x=>x.id===t.id),a=chart.convertToPixel({xAxisIndex:0,yAxisIndex:0},[t.start,i]),b=chart.convertToPixel({xAxisIndex:0,yAxisIndex:0},[t.end,i]);return {x:a[0],y:a[1],w:b[0]-a[0],i};}
    function hit(event){const p=local(event);for(const t of data.tasks){const r=rowGeometry(t);if(p[0]>=r.x-3&&p[0]<=r.x+r.w+3&&Math.abs(p[1]-r.y)<23)return {t,r,p};}return null;}
    function commit(start,end,message='时间已更新'){
      if(progress!==1)finish();const t=task();if(!Number.isInteger(start)||!Number.isInteger(end)||start>=end||start<data.min||end>data.max){status('时间无效：结束须不早于开始，且在坐标轴范围内');return false;}
      if(start===t.start&&end===t.end){syncFields();return true;}
      undo.push(clone(data));t.start=start;t.end=end;draw();syncFields();status(message);return true;
    }
    function rollbackDrag(){if(!drag)return;data=drag.before;drag=null;draw();syncFields();status('本次拖动已取消');}
    plot.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;if(progress!==1)finish();const h=hit(event);if(!h)return;
      selected=h.t.id;syncFields();const edge=Math.min(14,h.r.w*.24);const mode=h.p[0]<h.r.x+edge?'start':h.p[0]>h.r.x+h.r.w-edge?'end':'move';
      drag={id:selected,mode,axis:axisAt(event),start:h.t.start,end:h.t.end,before:clone(data),clientX:event.clientX,moved:false,pointerId:event.pointerId};
      plot.setPointerCapture(event.pointerId);plot.focus();event.preventDefault();draw();
    },{signal});
    plot.addEventListener('pointermove',event=>{
      if(!drag){const h=hit(event);plot.style.cursor=h?(Math.min(Math.abs(h.p[0]-h.r.x),Math.abs(h.p[0]-h.r.x-h.r.w))<14?'ew-resize':'grab'):'default';return;}
      if(Math.abs(event.clientX-drag.clientX)<3&&!drag.moved)return;drag.moved=true;
      const dx=Math.round(axisAt(event)-drag.axis),t=task(),duration=drag.end-drag.start;
      if(drag.mode==='move'){t.start=Math.max(data.min,Math.min(data.max-duration,drag.start+dx));t.end=t.start+duration;}
      if(drag.mode==='start')t.start=Math.max(data.min,Math.min(drag.end-1,drag.start+dx));
      if(drag.mode==='end')t.end=Math.min(data.max,Math.max(drag.start+1,drag.end+dx));
      draw();syncFields();status('正在调整；松开以确认');
    },{signal});
    plot.addEventListener('pointerup',event=>{
      if(!drag)return;const before=drag.before,changed=JSON.stringify(before)!==JSON.stringify(data);drag=null;
      if(plot.hasPointerCapture(event.pointerId))plot.releasePointerCapture(event.pointerId);
      if(changed)undo.push(before);draw();syncFields();status(changed?'时间已更新':'项目已选择');
    },{signal});
    plot.addEventListener('pointercancel',rollbackDrag,{signal});
    plot.addEventListener('keydown',e=>{
      if(e.key==='Escape'&&drag){e.preventDefault();rollbackDrag();return;}
      if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();e.stopPropagation();const d=e.key==='ArrowRight'?1:-1,t=task();
      commit(t.start+(e.shiftKey?0:d),t.end+d);
    },{signal});
    root.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!e.target.closest('input,select,textarea')){e.preventDefault();e.stopPropagation();undoOne();return;}if(e.target.closest('input,select,textarea,button,[contenteditable=true]')||['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Enter','Escape'].includes(e.key))e.stopPropagation();},{signal});
    select.addEventListener('change',()=>{selected=select.value;syncFields();draw();},{signal});
    apply.addEventListener('click',()=>commit(qindex(inputs.sy.value,inputs.sq.value),qindex(inputs.ey.value,inputs.eq.value)+1),{signal});
    function undoOne(){finish();if(undo.length){data=undo.pop();draw();syncFields();status('已撤销');}}
    function reset(){cancelAnimationFrame(raf);progress=1;data=clone(baseline);undo=[];draw();syncFields();status('已还原');}
    undoB.addEventListener('click',undoOne,{signal});resetB.addEventListener('click',reset,{signal});
    const resize=new ResizeObserver(()=>{if(drag)rollbackDrag();chart.resize();draw();});resize.observe(plot);
    draw();syncFields();
    return {chart,root,plot,select(id){if(!data.tasks.some(t=>t.id===id))throw Error('未知任务');selected=id;syncFields();draw();},
      play,finish,getProgress:()=>progress,getData:()=>clone(data),getSelected:()=>selected,getDirty:countDirty,commit,undo:undoOne,reset,serialize:()=>JSON.stringify(data),
      geometry(id){const t=data.tasks.find(x=>x.id===id);if(!t)throw Error('未知任务');return rowGeometry(t);},
      importJSON(text){const next=JSON.parse(text);validate(next);if(next.min!==baseline.min||next.max!==baseline.max||next.tasks.length!==baseline.tasks.length||next.tasks.some((t,i)=>t.id!==baseline.tasks[i].id))throw Error('导入仅支持相同任务和时间轴');undo.push(clone(data));data=clone(next);draw();syncFields();},
      pause(){finish();if(drag)rollbackDrag();},resume(){chart.resize();},dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);abort.abort();resize.disconnect();chart.dispose();root.replaceChildren();}};
  }
  global.KZGantt={mount,validate,qindex,fromIndex,qlabel};
})(window);
