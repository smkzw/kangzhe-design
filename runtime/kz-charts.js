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
  const finiteOrNull=x=>x===null||Number.isFinite(x);
  function extent(data){let lo=0,hi=0;for(const series of data.series)for(const v of series.values)if(Number.isFinite(v)){lo=Math.min(lo,v);hi=Math.max(hi,v);}return [lo,hi];}
  function validate(data){
    if(!data||!['line','bar','column'].includes(data.kind))throw Error('基础图表只支持 line/bar/column');
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
  function option(data,{progress=1,reduced=false,width=1280,unit=1}={}){
    validate(data);const line=data.kind==='line',horizontal=data.kind==='bar';
    const numberFormat=v=>v===null?'未提供':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:data.decimals??2,minimumFractionDigits:data.decimals??0});
    const n=data.categories.length,labelStyle={color:chartTone('label',KZ_TOKENS.colors.body),fontSize:16*unit,width:width<480?32:undefined,overflow:'break',lineHeight:20*unit};
    const category=line
      ?{type:'value',min:0,max:Math.max(1,n-1),interval:n<=48?1:undefined,axisTick:{show:false},splitLine:{show:false},axisLine:{show:true,lineStyle:{color:chartTone('axis','#CED3D8')}},axisLabel:{...labelStyle,formatter:v=>Number.isInteger(v)&&v<n?String(data.categories[v]):''},axisPointer:{snap:true,label:{formatter:({value})=>String(data.categories[Math.round(value)]??'')}}}
      :{type:'category',data:data.categories,boundaryGap:true,axisTick:{show:false},axisLine:{lineStyle:{color:chartTone('axis','#CED3D8')}},axisLabel:{...labelStyle,interval:0}};
    const [lo,hi]=extent(data);
    const axis=readableAxis(lo,hi);
    const explicitExtent=data.axis?.min!==undefined||data.axis?.max!==undefined;
    const value={type:'value',min:data.axis?.min??axis.min,max:data.axis?.max??axis.max,interval:data.axis?.interval??(explicitExtent?undefined:axis.interval),name:data.unit,nameTextStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},axisLabel:{color:chartTone('label',KZ_TOKENS.colors.body),fontSize:16*unit},splitLine:{lineStyle:{color:chartTone('grid','#E7EBEE')}},axisLine:{show:false}};
    return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit,color:KZ_TOKENS.colors.body},
      aria:{enabled:true,decal:{show:false},label:{description:data.description||('图表；单位：'+data.unit)}},
      color:palettes(),grid:{left:(horizontal?120:60)*unit,right:28*unit,top:56*unit,bottom:(width<480?56:42)*unit,containLabel:false},
      legend:{show:data.series.length>1,top:0,textStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},icon:'roundRect',itemWidth:20,itemHeight:8},
      tooltip:{show:progress===1,trigger:'axis',confine:true,valueFormatter:numberFormat,textStyle:{fontSize:16*unit},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3'},
      xAxis:horizontal?value:category,yAxis:horizontal?category:value,
      series:data.series.map((s,i)=>{
        const color=seriesColor(s,data.series.slice(0,i).filter(takesSlot).length),vals=line?lineData(s.values,progress):s.values.map((v,j)=>barValue(v,j,n,progress));
        const common={id:s.id,name:s.name||s.id,type:line?'line':'bar',data:vals,animation:false,itemStyle:{color},emphasis:{focus:'series'},silent:progress!==1};
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
