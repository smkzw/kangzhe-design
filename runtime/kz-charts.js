/* ECharts is the only quantitative-chart renderer for the three HTML tracks. */
(function(global){
  'use strict';
  const copy=x=>JSON.parse(JSON.stringify(x));
  const palettes=()=>[KZ_TOKENS.colors.brand,KZ_TOKENS.departments.operations.color,KZ_TOKENS.departments.statistics.color,KZ_TOKENS.departments.pv.color];
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
    const category={type:'category',data:data.categories,boundaryGap:!line,axisTick:{show:false},axisLine:{lineStyle:{color:'#CED3D8'}},axisLabel:{color:KZ_TOKENS.colors.body,fontSize:16*unit,interval:0,width:width<480?32:undefined,overflow:'break',lineHeight:20*unit}};
    const [lo,hi]=extent(data);
    const axis=readableAxis(lo,hi);
    const explicitExtent=data.axis?.min!==undefined||data.axis?.max!==undefined;
    const value={type:'value',min:data.axis?.min??axis.min,max:data.axis?.max??axis.max,interval:data.axis?.interval??(explicitExtent?undefined:axis.interval),name:data.unit,nameTextStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},axisLabel:{color:KZ_TOKENS.colors.body,fontSize:16*unit},splitLine:{lineStyle:{color:'#E7EBEE'}},axisLine:{show:false}};
    return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16*unit,color:KZ_TOKENS.colors.body},
      aria:{enabled:true,decal:{show:false},label:{description:data.description||('图表；单位：'+data.unit)}},
      color:palettes(),grid:{left:(horizontal?120:60)*unit,right:28*unit,top:56*unit,bottom:(width<480?56:42)*unit,containLabel:false},
      legend:{show:data.series.length>1,top:0,textStyle:{color:KZ_TOKENS.colors.body,fontSize:16*unit},icon:'roundRect',itemWidth:20,itemHeight:8},
      tooltip:{show:progress===1,trigger:'axis',confine:true,valueFormatter:numberFormat,textStyle:{fontSize:16*unit},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3'},
      xAxis:horizontal?value:category,yAxis:horizontal?category:value,
      series:data.series.map((s,i)=>{
        const color=s.color||palettes()[i%4],vals=s.values.map(v=>v===null?null:v*progress);
        const common={id:s.id,name:s.name||s.id,type:line?'line':'bar',data:vals,animation:false,itemStyle:{color},emphasis:{focus:'series'},silent:progress!==1};
        if(line)return {...common,smooth:false,connectNulls:false,symbol:'circle',symbolSize:7,lineStyle:{color,width:3},areaStyle:data.area===false?undefined:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:rgba(color,.14)},{offset:1,color:rgba(color,.025)}])}};
        return {...common,barMaxWidth:42,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,horizontal?1:0,horizontal?0:1,[{offset:0,color:rgba(color,.68)},{offset:1,color}]),borderRadius:horizontal?[0,6,6,0]:[6,6,0,0]},label:{show:true,position:horizontal?'right':'top',fontSize:16*unit,color:KZ_TOKENS.colors.body,formatter:p=>numberFormat(p.value)}};
      })};
  }
  function mount(el,data,opts={}){
    if(!global.echarts)throw Error('缺少随包 ECharts；不以 CSS 假图代替');
    validate(data);let current=copy(data),disposed=false,raf=0,lastProgress=1;
    const chart=echarts.init(el,null,{renderer:'canvas'}),mq=matchMedia('(prefers-reduced-motion: reduce)');
    let selected={};chart.on('legendselectchanged',e=>{selected={...e.selected};});
    const ro=new ResizeObserver(()=>{chart.resize();renderProgress(lastProgress);});ro.observe(el);
    function renderProgress(p){
      if(disposed)return;p=Math.max(0,Math.min(1,p));lastProgress=p;
      const previous=chart.getOption();selected={...selected,...(previous?.legend?.[0]?.selected||{})};
      const unit=el.closest('.deck')&&document.body.dataset.fit==='fluid'?Math.max(1,innerHeight/KZ_TOKENS.wide.htmlppt_reference_height):1;
      const next=option(current,{progress:p,width:chart.getWidth(),unit});next.legend.selected={...selected};
      chart.setOption(next,{notMerge:true});
      opts.onProgress?.(p,copy(current));
    }
    function finish(){cancelAnimationFrame(raf);raf=0;renderProgress(1);}
    function play(duration=KZ_TOKENS.motion.chart_ms){
      finish();if(mq.matches||disposed)return;
      let start=null;
      function tick(now){if(disposed)return;start??=now;const p=Math.min(1,(now-start)/duration);renderProgress(1-Math.pow(1-p,3));if(p<1)raf=requestAnimationFrame(tick);else raf=0;}
      raf=requestAnimationFrame(tick);
    }
    const changed=()=>{if(mq.matches)finish();};mq.addEventListener('change',changed);
    const beforePrint=()=>finish();global.addEventListener('beforeprint',beforePrint);
    const visibility=()=>{if(document.hidden)finish();};document.addEventListener('visibilitychange',visibility);
    chart.on('click',params=>opts.onDataClick?.(params,copy(current)));
    renderProgress(1);
    return {chart,play,finish,renderProgress,getData:()=>copy(current),getProgress:()=>lastProgress,
      setData(next){validate(next);current=copy(next);finish();},resize:()=>chart.resize(),pause:finish,resume(){},
      dispose(){if(disposed)return;cancelAnimationFrame(raf);disposed=true;ro.disconnect();mq.removeEventListener('change',changed);document.removeEventListener('visibilitychange',visibility);global.removeEventListener('beforeprint',beforePrint);chart.dispose();}};
  }
  global.KZCharts={mount,option,validate,rgba};
})(window);
