/* ECharts is the only quantitative-chart renderer for the three HTML tracks. */
(function(global){
  'use strict';
  const copy=x=>JSON.parse(JSON.stringify(x));
  // 字号比率与 bridge 同一生命周期：fluid 下读 :root 的 --kz-un（含钳制与打印锁定），无 bridge 时退回自算。
  function fluidUnit(el){
    if(!document.body||document.body.dataset.fit!=='fluid')return 1;
    if(!(el.closest('.deck')||el.closest('.kz-dialog')))return 1; // 下钻弹层挂在 body 上，同属 fluid 页面
    const v=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--kz-un'));
    if(Number.isFinite(v)&&v>0)return v;
    return innerHeight/KZ_TOKENS.wide.htmlppt_reference_height;
  }
  // Fixed categorical order (never cycled through department colours). Department colours apply only when a
  // series declares the department it represents; `role:'comparator'` takes the reserved neutral.
  const palettes=()=>KZ_TOKENS.charts?.categorical||[KZ_TOKENS.colors.brand,KZ_TOKENS.departments.operations.color,KZ_TOKENS.departments.statistics.color,KZ_TOKENS.departments.pv.color];
  const chartTone=(k,f)=>KZ_TOKENS.charts?.[k]||f;
  // Only series without their own colour, comparator role or known department take a categorical slot.
  const takesSlot=s=>!s.color&&s.role!=='comparator'&&!(s.department&&KZ_TOKENS.departments?.[s.department]);
  function seriesColor(s,slot){
    if(s.color)return s.color;
    if(s.role==='comparator')return chartTone('comparator','#6E7B8C');
    if(s.department&&KZ_TOKENS.departments?.[s.department])return KZ_TOKENS.departments[s.department].color;
    return palettes()[slot];
  }
  const easeData=()=>{const b=KZ_TOKENS.motion?.easing?.data||[.33,1,.68,1];return x=>{let lo=0,hi=1;for(let i=0;i<20;i++){const t=(lo+hi)/2,bx=3*(1-t)**2*t*b[0]+3*(1-t)*t*t*b[2]+t**3;bx<x?lo=t:hi=t;}const t=(lo+hi)/2;return 3*(1-t)**2*t*b[1]+3*(1-t)*t*t*b[3]+t**3;};};
  // Line reveal draws left→right: points up to the progress position keep their true values; the last
  // segment is interpolated to the progress position. Values are never scaled toward zero.
  function lineData(values,progress){
    const n=values.length,edge=progress*(n-1),out=[];
    for(let i=0;i<n;i++){
      if(i<=edge+1e-9){out.push([i,values[i]]);continue;}
      const a=values[i-1],b=values[i],f=edge-(i-1);
      if(f>0&&a!==null&&b!==null)out.push({value:[edge,a+(b-a)*f],symbol:'none'});
      break;
    }
    return out;
  }
  // Bars grow from the baseline with a small left→right offset inside the same progress.
  function barValue(v,i,n,progress){
    if(v===null)return null;const s=n>1?Math.min(.06,.4/(n-1)):0,local=Math.max(0,Math.min(1,(progress-i*s)/(1-(n-1)*s)));return v*local;
  }
  // 7.2: stacked (column, or bar with horizontal:true), combo (bars plus line series on the same value axis; never a
  // second axis) and doughnut join line/bar/column for template pages (13 BODY-02).
  const KINDS=['line','bar','column','stacked','combo','doughnut','forest','km'];
  const finiteOrNull=x=>x===null||Number.isFinite(x);
  function extent(data){
    let lo=0,hi=0;
    if(data.kind==='stacked'){data.categories.forEach((_,j)=>{let pos=0,neg=0;for(const s of data.series){const v=s.values[j];if(Number.isFinite(v))v>=0?pos+=v:neg+=v;}lo=Math.min(lo,neg);hi=Math.max(hi,pos);});return [lo,hi];}
    for(const series of data.series)for(const v of series.values)if(Number.isFinite(v)){lo=Math.min(lo,v);hi=Math.max(hi,v);}return [lo,hi];
  }
  // forest (subgroup estimates with CIs) and km (Kaplan–Meier steps with an at-risk table) carry their own shapes
  function validateClinical(data){
    if(data.kind==='forest'){
      if(!Array.isArray(data.rows)||!data.rows.length)throw Error('森林图缺少行');
      for(const r of data.rows){if(r.est===undefined)continue;if(![r.est,r.lo,r.hi].every(Number.isFinite)||!(r.lo<=r.est&&r.est<=r.hi))throw Error('森林图估计值或置信区间无效：'+r.label);if(data.log!==false&&r.lo<=0)throw Error('对数轴的区间下限必须大于 0：'+r.label);}
    }else{
      if(!Array.isArray(data.series)||!data.series.length)throw Error('KM 图缺少系列');
      for(const s of data.series){if(!s.id||!Array.isArray(s.points)||!s.points.length)throw Error('KM 系列缺少 id 或点');for(const [t,v] of s.points)if(!Number.isFinite(t)||!Number.isFinite(v)||v<0||v>100)throw Error('KM 点必须是 [时间, 0–100%]');}
      if(!Number.isFinite(data.xmax)||data.xmax<=0)throw Error('KM 图缺少 xmax');
      if(data.at_risk&&data.at_risk.rows.length!==data.series.length)throw Error('风险人数行数与系列数不一致');
    }
    return true;
  }
  function validate(data){
    if(!data||!KINDS.includes(data.kind))throw Error('图表类型只支持 '+KINDS.join('/'));
    if(data.kind==='forest'||data.kind==='km')return validateClinical(data);
    if(data.kind==='doughnut'&&data.series.length!==1)throw Error('环形图只能有一个系列');
    if(!Array.isArray(data.categories)||!data.categories.length)throw Error('缺少类别');
    if(!Array.isArray(data.series)||!data.series.length)throw Error('缺少系列');
    const ids=new Set();
    for(const s of data.series){
      if(!s.id||ids.has(s.id))throw Error('系列 id 缺失或重复');ids.add(s.id);
      if(!Array.isArray(s.values)||s.values.length!==data.categories.length||!s.values.every(finiteOrNull))throw Error('数值长度不一致或存在非有限数');
    }
    if(typeof data.unit!=='string'||!data.unit.trim())throw Error('图表必须声明单位');
    if(data.series.filter(takesSlot).length>palettes().length)throw Error('类别系列超过固定色序（'+palettes().length+' 色）；请合并为“其他”或拆成小多图');
    if(data.axis){
      for(const k of ['min','max','interval'])if(data.axis[k]!==undefined&&!Number.isFinite(data.axis[k]))throw Error('坐标范围必须为有限数');
      if(data.axis.min!==undefined&&data.axis.max!==undefined&&data.axis.min>=data.axis.max)throw Error('坐标上限必须大于下限');
      if(data.axis.interval!==undefined&&data.axis.interval<=0)throw Error('坐标间隔必须为正数');
      if(data.axis.min!==undefined||data.axis.max!==undefined){
        const automatic=readableAxis(...extent(data));
        if((data.axis.min??automatic.min)>=(data.axis.max??automatic.max))throw Error('显式坐标端点与自动范围冲突；请提供有效的 min/max');
      }
    }
    return true;
  }
  function rgba(hex,alpha){const h=hex.replace('#','');return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${alpha})`;}
  function readableAxis(lo,hi){
    const span=hi-lo||1,lower=lo<0?lo-span*.08:0,upper=hi>0?hi+span*.12:(lo===0?1:0);
    const raw=(upper-lower)/5,magnitude=10**Math.floor(Math.log10(raw)),fraction=raw/magnitude;
    const step=(fraction<=1?1:fraction<=2?2:fraction<=5?5:10)*magnitude;
    // IEEE-754 endpoints can leave no representable room for rounded padding.
    if(!Number.isFinite(raw)||!Number.isFinite(step)||step<=0)return {min:lo,max:hi||1,interval:undefined};
    const tidy=n=>Number(n.toPrecision(12));
    return {min:tidy(Math.floor(lower/step)*step),max:tidy(Math.ceil(upper/step)*step),interval:tidy(step)};
  }
  function doughnutOption(data,{progress=1,unit=1}){
    const s=data.series[0],total=s.values.reduce((a,v)=>a+(Number.isFinite(v)?v:0),0),pal=palettes();
    const numberFormat=v=>Number(v).toLocaleString('zh-CN',{maximumFractionDigits:data.decimals??1});
    const slices=data.categories.map((c,i)=>({name:c,value:s.values[i],itemStyle:{color:pal[i%pal.length],borderColor:'#FFFFFF',borderWidth:2}}));
    if(progress<1)slices.push({name:'',value:total*(1-progress)/Math.max(progress,1e-3),itemStyle:{color:'rgba(0,0,0,0)'},label:{show:false},labelLine:{show:false},tooltip:{show:false},silent:true});
    return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit,color:KZ_TOKENS.colors.body},
      aria:{enabled:true,decal:{show:false},label:{description:data.description||('环形图；单位：'+data.unit)}},
      legend:{show:false},tooltip:{show:progress===1,trigger:'item',confine:true,valueFormatter:numberFormat,textStyle:{fontSize:16*unit}},
      series:[{type:'pie',radius:['50%','74%'],center:['50%','52%'],startAngle:90,data:slices,animation:false,silent:progress!==1,
        label:{show:progress===1,color:KZ_TOKENS.colors.body,fontSize:16*unit,lineHeight:20*unit,formatter:p=>p.name+'\n'+numberFormat(p.value)+(data.unit==='%'?'%':data.unit?' '+data.unit:'')},
        labelLine:{length:10*unit,length2:12*unit,lineStyle:{color:'#C9CED4'}}}]};
  }
  const base=(unit,description)=>({backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit,color:KZ_TOKENS.colors.body},aria:{enabled:true,decal:{show:false},label:{description}}});
  const fmtTick=v=>String(Number(v.toFixed(4)));
  function forestOption(data,{progress=1,unit=1,width=1280}){
    const rows=data.rows,log=data.log!==false,ref=data.ref??1,tf=v=>log?Math.log(v):v,inv=v=>log?Math.exp(v):v;
    const vals0=rows.filter(r=>r.est!==undefined).flatMap(r=>[r.lo,r.hi]).concat(ref),vals=vals0,ticks=data.ticks||(log?[0.25,0.5,1,2,4]:(()=>{const a=Math.min(...vals0),b=Math.max(...vals0),st=(b-a)/4||1;return [0,1,2,3,4].map(i=>Math.round((a+i*st)*100)/100);})());
    const lo=Math.min(...vals,...ticks),hi=Math.max(...vals,...ticks),brand=data.color||KZ_TOKENS.colors.brand,ink=KZ_TOKENS.colors.ink,risk=KZ_TOKENS.colors.risk;
    const em=t=>[...String(t)].reduce((a,c)=>a+(/[\u0000-\u024f]/.test(c)?.58:1),0)*16*unit;
    const labW=Math.min(width*.34,Math.max(...rows.map(r=>em(r.label)+(r.header||r.overall?0:18*unit)))+12*unit),nW=rows.some(r=>r.n!==undefined)?60*unit:0;
    const ci=r=>r.est===undefined?'':(r.text||`${r.est.toFixed(2)} (${r.lo.toFixed(2)}–${r.hi.toFixed(2)})`);
    const ciW=Math.max(...rows.map(r=>em(ci(r))))+16*unit,heads=data.heads||['亚组','n',data.measure||'HR (95% CI)'];
    const cats=rows.map((_,i)=>String(i));
    const lab={rich:{h:{fontWeight:'bold',color:ink,fontSize:16*unit,width:labW,align:'left',overflow:'break'},b:{color:KZ_TOKENS.colors.body,fontSize:16*unit,width:labW-18*unit,align:'left',padding:[0,0,0,18*unit],overflow:'break'},n:{width:nW,align:'right',fontSize:16*unit,color:KZ_TOKENS.colors.body}}};
    const grid={left:labW+nW+20*unit,right:ciW+12*unit,top:34*unit,bottom:64*unit,outerBoundsMode:'none'};  // ECharts 6 would otherwise shrink the plot to contain the label columns
    const refX=grid.left+(tf(ref)-tf(lo))/((tf(hi)-tf(lo))||1)*(width-grid.left-grid.right),favFont=`${14*unit}px ${KZ_TOKENS.fonts.fallback_css}`;
    const muted=chartTone('label',KZ_TOKENS.colors.muted||'#6B7480');
    return {...base(unit,data.description||'森林图'),
      grid,legend:{show:false},tooltip:{show:progress===1,trigger:'item',confine:true,formatter:p=>{const r=rows[p.dataIndex];return r.est===undefined?r.label:`${r.label}${r.n!==undefined?'（n='+r.n+'）':''}<br>${ci(r)}`;},textStyle:{fontSize:16*unit}},
      graphic:[{type:'text',left:0,top:4*unit,style:{text:heads[0],font:`bold ${16*unit}px ${KZ_TOKENS.fonts.fallback_css}`,fill:ink}},
        ...(nW?[{type:'text',left:labW+nW-30*unit,top:4*unit,style:{text:heads[1],font:`bold ${16*unit}px ${KZ_TOKENS.fonts.fallback_css}`,fill:ink}}]:[]),
        {type:'text',right:0,top:4*unit,style:{text:heads[2],font:`bold ${16*unit}px ${KZ_TOKENS.fonts.fallback_css}`,fill:ink,align:'right'}},
        ...(data.favours?[{type:'text',right:width-refX+10*unit,bottom:8*unit,style:{text:'← '+data.favours[0],font:favFont,fill:muted}},{type:'text',left:refX+10*unit,bottom:8*unit,style:{text:data.favours[1]+' →',font:favFont,fill:muted}}]:[])],
      xAxis:{type:'value',min:tf(lo),max:tf(hi),splitLine:{show:false},axisLine:{show:true,lineStyle:{color:'#9AA1A8'}},axisTick:{show:true,customValues:ticks.map(tf)},
        axisLabel:{customValues:ticks.map(tf),formatter:v=>fmtTick(inv(v)),fontSize:14*unit,color:muted}},
      yAxis:[{type:'category',data:cats,inverse:true,axisLine:{show:false},axisTick:{show:false},splitArea:{show:true,areaStyle:{color:['#F7F8F9','rgba(0,0,0,0)']}},
          axisLabel:{margin:labW+nW+20*unit,align:'left',formatter:(v,i)=>{const r=rows[i];return (r.header||r.overall?`{h|${r.label}}`:`{b|${r.label}}`)+(nW?`{n|${r.n??''}}`:'');},rich:lab.rich}},
        {type:'category',data:cats,inverse:true,position:'right',axisLine:{show:false},axisTick:{show:false},axisLabel:{margin:10*unit,align:'left',formatter:(v,i)=>rows[i].overall?`{h|${ci(rows[i])}}`:ci(rows[i]),fontSize:16*unit,color:KZ_TOKENS.colors.body,rich:{h:{fontWeight:'bold',color:ink,fontSize:16*unit}}}}],
      series:[{type:'custom',animation:false,silent:progress!==1,data:rows.map((r,i)=>r.est===undefined?null:[tf(r.est),i,tf(r.lo),tf(r.hi),r.overall?1:0]),
        renderItem:(params,api)=>{const e=api.value(0),i=api.value(1),a=api.value(2),b=api.value(3),ov=api.value(4);const k=Math.max(0,Math.min(1,progress));
          const [cx,cy]=api.coord([e,i]),[ax]=api.coord([e-(e-a)*k,i]),[bx]=api.coord([e+(b-e)*k,i]),s=9*unit;
          const shape=ov?{type:'polygon',shape:{points:[[cx,cy-s],[cx+s,cy],[cx,cy+s],[cx-s,cy]]},style:{fill:'#B85C00'}}:{type:'rect',shape:{x:cx-s/2,y:cy-s/2,width:s,height:s,r:1},style:{fill:brand}};
          return {type:'group',children:[{type:'line',shape:{x1:ax,y1:cy,x2:bx,y2:cy},style:{stroke:ov?ink:'#3D4650',lineWidth:1.6}},shape]};},
        markLine:{silent:true,symbol:'none',lineStyle:{color:'#5F6B76',type:'dashed',width:1.5},
          data:[{xAxis:tf(ref),label:{show:false}}]}}]};
  }
  function kmOption(data,{progress=1,unit=1}){
    const ser=data.series,ymin=data.ymin??0,xmax=data.xmax,xstep=data.xstep??Math.max(1,Math.round(xmax/6)),ar=data.at_risk,edge=progress*xmax;
    const cols=ser.map((s,i)=>seriesColor(s,ser.slice(0,i).filter(takesSlot).length)),muted=chartTone('label',KZ_TOKENS.colors.muted||'#6B7480');
    const riskH=ar?(30+24*ser.length)*unit:0,labW=ar?Math.max(...ser.map(s=>[...s.name].reduce((a,c)=>a+(/[\u0000-\u024f]/.test(c)?.58:1),0)*14*unit))+56*unit:56*unit;
    const left=Math.max(56*unit,labW);
    const clip=pts=>{const out=[];for(const [t,v] of pts){if(t<=edge){out.push([t,v]);continue;}if(out.length)out.push([edge,out[out.length-1][1]]);break;}return out;};
    const grids=[{left,right:16*unit,top:40*unit,bottom:riskH+52*unit,outerBoundsMode:'none'}];
    const xAxes=[{type:'value',min:0,max:xmax,interval:xstep,gridIndex:0,name:data.xlabel||'时间（月）',nameLocation:'middle',nameGap:30*unit,nameTextStyle:{fontSize:14*unit,color:muted},splitLine:{show:false},axisLine:{show:true,lineStyle:{color:'#9AA1A8'}},axisTick:{show:true},axisLabel:{fontSize:14*unit,color:muted}}];
    const yAxes=[{type:'value',min:ymin,max:100,interval:(100-ymin)>50?20:10,gridIndex:0,name:data.ylabel||'%',nameTextStyle:{fontSize:14*unit,color:muted},axisLabel:{fontSize:14*unit,color:muted},splitLine:{lineStyle:{color:'#E7EBEE'}},axisLine:{show:false}}];
    const series=ser.map((s,i)=>({id:s.id,name:s.name,type:'line',step:'end',xAxisIndex:0,yAxisIndex:0,data:clip(s.points),symbol:'none',lineStyle:{color:cols[i],width:2.4},itemStyle:{color:cols[i]},animation:false,silent:progress!==1,
      markLine:data.median&&i===0?{silent:true,symbol:'none',label:{show:false},lineStyle:{color:'#B8BFC6',type:'dashed',width:1},data:[{yAxis:50}]}:undefined}));
    ser.forEach((s,i)=>{if(s.censor?.length)series.push({name:s.name,type:'scatter',xAxisIndex:0,yAxisIndex:0,symbol:'rect',symbolSize:[2*unit,10*unit],itemStyle:{color:cols[i]},silent:true,animation:false,tooltip:{show:false},
      data:s.censor.filter(t=>t<=edge).map(t=>[t,([...s.points].filter(p=>p[0]<=t).pop()||s.points[0])[1]])});});
    if(ar){
      grids.push({left,right:16*unit,bottom:6*unit,height:24*unit*ser.length,outerBoundsMode:'none'});
      xAxes.push({type:'value',min:0,max:xmax,interval:xstep,gridIndex:1,show:false});
      yAxes.push({type:'category',gridIndex:1,data:ser.map(s=>s.name),inverse:true,axisLine:{show:false},axisTick:{show:false},
        axisLabel:{margin:26*unit,fontSize:14*unit,color:KZ_TOKENS.colors.ink,formatter:(v,i)=>`{m${i}|━} ${v}`,rich:Object.fromEntries(cols.map((c,i)=>['m'+i,{color:c,fontSize:14*unit}]))}});
      series.push({type:'scatter',xAxisIndex:1,yAxisIndex:1,symbolSize:0,silent:true,animation:false,tooltip:{show:false},label:{show:true,position:'inside',fontSize:14*unit,color:KZ_TOKENS.colors.body,formatter:p=>String(p.value[2])},
        data:ser.flatMap((s,k)=>ar.times.map((t,j)=>[t,k,ar.rows[k][j]]))});
    }
    return {...base(unit,data.description||'Kaplan–Meier 曲线'),grid:grids,xAxis:xAxes,yAxis:yAxes,series,
      graphic:ar?[{type:'text',left:0,bottom:24*unit*ser.length+10*unit,style:{text:'风险人数',font:`bold ${14*unit}px ${KZ_TOKENS.fonts.fallback_css}`,fill:muted}}]:[],
      legend:{show:true,top:0,right:16*unit,data:ser.map(s=>s.name),textStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},icon:'roundRect',itemWidth:20,itemHeight:4},
      tooltip:{show:progress===1,trigger:'axis',confine:true,textStyle:{fontSize:16*unit},valueFormatter:v=>Number(v).toFixed(1)+'%'}};
  }
  function option(data,{progress=1,reduced=false,width=1280,unit=1}={}){
    validate(data);if(data.kind==='doughnut')return doughnutOption(data,{progress,unit});
    if(data.kind==='forest')return forestOption(data,{progress,unit,width});
    if(data.kind==='km')return kmOption(data,{progress,unit});
    const line=data.kind==='line',horizontal=data.kind==='bar'||(data.kind==='stacked'&&!!data.horizontal),stacked=data.kind==='stacked';
    const numberFormat=v=>v===null?'未提供':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:data.decimals??2,minimumFractionDigits:data.decimals??0});
    // category labels: on a column chart they wrap only inside their own slot; on a bar chart the grid makes room for
    // the longest one (estimated: CJK 1em, Latin .58em) so they never wrap mid-word
    const n=data.categories.length,em=t=>[...String(t)].reduce((a,c)=>a+(/[\u0000-\u024f]/.test(c)?.58:1),0)*16*unit;
    const gridL=horizontal?Math.min(width*.4,Math.max(...data.categories.map(em))+18*unit):60*unit,gridR=(horizontal?56:28)*unit;
    const labelStyle={color:chartTone('label',KZ_TOKENS.colors.body),fontSize:16*unit,width:horizontal?undefined:Math.max(36*unit,(width-gridL-gridR)/n-8*unit),overflow:'break',lineHeight:20*unit};
    const category=line
      ?{type:'value',min:0,max:Math.max(1,n-1),interval:n<=48?1:undefined,axisTick:{show:false},splitLine:{show:false},axisLine:{show:true,lineStyle:{color:chartTone('axis','#CED3D8')}},axisLabel:{...labelStyle,formatter:v=>Number.isInteger(v)&&v<n?String(data.categories[v]):''},axisPointer:{snap:true,label:{formatter:({value})=>String(data.categories[Math.round(value)]??'')}}}
      :{type:'category',data:data.categories,boundaryGap:true,inverse:horizontal,axisTick:{show:false},axisLine:{onZero:true,lineStyle:{color:chartTone('axis','#CED3D8')}},axisLabel:{...labelStyle,interval:0}};
    const [lo,hi]=extent(data);
    const axis=readableAxis(lo,hi);
    const explicitExtent=data.axis?.min!==undefined||data.axis?.max!==undefined;
    const value={type:'value',min:data.axis?.min??axis.min,max:data.axis?.max??axis.max,interval:data.axis?.interval??(explicitExtent?undefined:axis.interval),name:data.unit,nameTextStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},axisLabel:{color:chartTone('label',KZ_TOKENS.colors.body),fontSize:16*unit},splitLine:{lineStyle:{color:chartTone('grid','#E7EBEE')}},axisLine:{show:false}};
    return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit,color:KZ_TOKENS.colors.body},
      aria:{enabled:true,decal:{show:false},label:{description:data.description||('图表；单位：'+data.unit)}},
      color:palettes(),grid:{left:gridL,right:gridR,top:56*unit,bottom:(width<480?56:42)*unit,containLabel:false},
      legend:{show:data.series.length>1,top:0,textStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},icon:'roundRect',itemWidth:20,itemHeight:8},
      tooltip:{show:progress===1,trigger:'axis',confine:true,valueFormatter:numberFormat,textStyle:{fontSize:16*unit},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3'},
      xAxis:horizontal?value:category,yAxis:horizontal?category:value,
      series:data.series.map((s,i)=>{
        const color=seriesColor(s,data.series.slice(0,i).filter(takesSlot).length);
        const comboLine=data.kind==='combo'&&s.type==='line';
        // a combo line rides the category axis: points appear left→right with the bars' progress, never scaled
        const negPos=horizontal?'left':'bottom';
        const vals=line?lineData(s.values,progress):comboLine?s.values.map((v,j)=>j<=progress*(n-1)+1e-9?v:null)
          :s.values.map((v,j)=>{const b=barValue(v,j,n,progress);return v!==null&&v<0&&!stacked?{value:b,label:{position:negPos},itemStyle:{borderRadius:horizontal?[6,0,0,6]:[0,0,6,6]}}:b;});
        const common={id:s.id,name:s.name||s.id,type:line||comboLine?'line':'bar',data:vals,animation:false,itemStyle:{color},emphasis:{focus:'series'},silent:progress!==1};
        if(comboLine)return {...common,smooth:false,connectNulls:false,symbol:'circle',symbolSize:8,z:3,lineStyle:{color,width:3},label:{show:true,position:'top',fontSize:16*unit,color:KZ_TOKENS.colors.body,formatter:p=>p.value===null?'':numberFormat(p.value)}};
        if(stacked){const last=i===data.series.length-1;return {...common,stack:'total',barMaxWidth:46,itemStyle:{color,borderColor:'#FFFFFF',borderWidth:1,borderRadius:last?(horizontal?[0,6,6,0]:[6,6,0,0]):0},
          label:{show:true,position:'inside',fontSize:14*unit,color:KZ_TOKENS.colors.ink,formatter:p=>p.value?numberFormat(p.value):''}};}
        if(line)return {...common,smooth:false,connectNulls:false,symbol:'circle',symbolSize:7,lineStyle:{color,width:3},areaStyle:data.area===false?undefined:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:rgba(color,.14)},{offset:1,color:rgba(color,.025)}])}};
        return {...common,barMaxWidth:42,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,horizontal?1:0,horizontal?0:1,[{offset:0,color:rgba(color,.68)},{offset:1,color}]),borderRadius:horizontal?[0,6,6,0]:[6,6,0,0]},label:{show:true,position:horizontal?'right':'top',fontSize:16*unit,color:KZ_TOKENS.colors.body,formatter:p=>numberFormat(p.value)}};
      })};
  }
  function mount(el,data,opts={}){
    if(!global.echarts)throw Error('缺少随包 ECharts；不以 CSS 假图代替');
    validate(data);let current=copy(data),disposed=false,raf=0,lastProgress=1;
    let chart=null,mq=null,ro=null,selected={};
    let changed=()=>{},beforePrint=()=>{},visibility=()=>{},ratioChanged=()=>{};
    const releaseAll=()=>{const errors=[];for(const release of [()=>{cancelAnimationFrame(raf);raf=0;},()=>ro?.disconnect(),()=>mq?.removeEventListener('change',changed),()=>document.removeEventListener('visibilitychange',visibility),()=>global.removeEventListener('beforeprint',beforePrint),()=>global.removeEventListener('kz:fluidratio',ratioChanged),()=>chart?.dispose()]){try{release();}catch(error){errors.push(error);}}return errors;};
    function renderProgress(p){
      if(disposed)return;p=Math.max(0,Math.min(1,p));lastProgress=p;
      const previous=chart.getOption();selected={...selected,...(previous?.legend?.[0]?.selected||{})};
      const unit=fluidUnit(el);const next=option(current,{progress:p,width:chart.getWidth(),unit});next.legend.selected={...selected};
      chart.setOption(next,{notMerge:true});
      opts.onProgress?.(p,copy(current));
    }
    function finish(){if(disposed)return;cancelAnimationFrame(raf);raf=0;renderProgress(1);}
    function play(duration=KZ_TOKENS.motion?.duration_ms?.data??KZ_TOKENS.motion?.chart_ms??1000){
      cancelAnimationFrame(raf);raf=0;
      if(disposed)return;
      if(mq.matches){finish();return;}
      renderProgress(0);
      let start=null;
      const curve=easeData();
      function tick(){if(disposed)return;const now=performance.now();start??=now;const p=Math.min(1,(now-start)/duration);renderProgress(curve(p));if(p<1)raf=requestAnimationFrame(tick);else raf=0;}
      raf=requestAnimationFrame(tick);
    }
    try{
      chart=echarts.init(el,null,{renderer:'canvas'});
      mq=matchMedia('(prefers-reduced-motion: reduce)');
      chart.on('legendselectchanged',e=>{selected={...e.selected};});
      ro=new ResizeObserver(()=>{chart.resize();renderProgress(lastProgress);});ro.observe(el);
      changed=()=>{if(mq.matches)finish();};mq.addEventListener('change',changed);
      beforePrint=()=>finish();global.addEventListener('beforeprint',beforePrint);
      ratioChanged=()=>renderProgress(lastProgress);global.addEventListener('kz:fluidratio',ratioChanged);
      visibility=()=>{if(document.hidden)finish();};document.addEventListener('visibilitychange',visibility);
      chart.on('click',params=>opts.onDataClick?.(params,copy(current)));
      renderProgress(1);
      return {chart,play,finish,renderProgress,getData:()=>copy(current),getProgress:()=>lastProgress,
        setData(next){validate(next);current=copy(next);finish();},resize:()=>chart.resize(),pause:finish,resume(){},
        dispose(){if(disposed)return;disposed=true;const errors=releaseAll();if(errors.length)throw new AggregateError(errors,'图表清理未完全释放');}};
    }catch(error){
      disposed=true;
      const errors=releaseAll();
      if(errors.length)throw new AggregateError([error,...errors],'图表挂载失败且未完全释放');
      throw error;
    }
  }
  global.KZCharts={mount,option,validate,rgba};
})(window);
