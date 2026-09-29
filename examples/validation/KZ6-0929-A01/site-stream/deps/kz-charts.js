/* ECharts is the only quantitative-chart renderer for the three HTML tracks. */
(function(global){
  'use strict';
  const copy=x=>JSON.parse(JSON.stringify(x));
  const palettes=()=>[KZ_TOKENS.colors.brand,KZ_TOKENS.departments.operations.color,KZ_TOKENS.departments.statistics.color,KZ_TOKENS.departments.pv.color];
  const finiteOrNull=x=>x===null||Number.isFinite(x);
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
    return true;
  }
  function rgba(hex,alpha){const h=hex.replace('#','');return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${alpha})`;}
  function option(data,{progress=1,reduced=false,width=1280}={}){
    validate(data);const line=data.kind==='line',horizontal=data.kind==='bar';
    const numberFormat=v=>v===null?'未提供':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:data.decimals??2,minimumFractionDigits:data.decimals??0});
    const category={type:'category',data:data.categories,boundaryGap:!line,axisTick:{show:false},axisLine:{lineStyle:{color:'#CED3D8'}},axisLabel:{color:KZ_TOKENS.colors.body,fontSize:16,interval:0,width:width<480?32:undefined,overflow:'break',lineHeight:20}};
    const all=data.series.flatMap(s=>s.values).filter(Number.isFinite);
    const lo=Math.min(0,...all),hi=Math.max(0,...all),span=hi-lo||1;
    const value={type:'value',min:lo<0?lo-span*.08:0,max:hi>0?hi+span*.12:(lo===0?1:0),name:data.unit,nameTextStyle:{color:KZ_TOKENS.colors.body,fontSize:16},axisLabel:{color:KZ_TOKENS.colors.body,fontSize:16},splitLine:{lineStyle:{color:'#E7EBEE'}},axisLine:{show:false}};
    return {backgroundColor:'transparent',animation:false,textStyle:{fontFamily:KZ_TOKENS.fonts.fallback_css,fontSize:16,color:KZ_TOKENS.colors.body},
      aria:{enabled:true,decal:{show:false},label:{description:data.description||('图表；单位：'+data.unit)}},
      color:palettes(),grid:{left:horizontal?120:60,right:28,top:56,bottom:width<480?56:42,containLabel:false},
      legend:{show:data.series.length>1,top:0,textStyle:{color:KZ_TOKENS.colors.body,fontSize:16},icon:'roundRect',itemWidth:20,itemHeight:8},
      tooltip:{show:progress===1,trigger:'axis',confine:true,valueFormatter:numberFormat,textStyle:{fontSize:16},backgroundColor:'rgba(255,255,255,.96)',borderColor:'#D9DEE3'},
      xAxis:horizontal?value:category,yAxis:horizontal?category:value,
      series:data.series.map((s,i)=>{
        const color=s.color||palettes()[i%4],vals=s.values.map(v=>v===null?null:v*progress);
        const common={id:s.id,name:s.name||s.id,type:line?'line':'bar',data:vals,animation:false,itemStyle:{color},emphasis:{focus:'series'},silent:progress!==1};
        if(line)return {...common,smooth:false,connectNulls:false,symbol:'circle',symbolSize:7,lineStyle:{color,width:3},areaStyle:data.area===false?undefined:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:rgba(color,.14)},{offset:1,color:rgba(color,.025)}])}};
        return {...common,barMaxWidth:42,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,horizontal?1:0,horizontal?0:1,[{offset:0,color:rgba(color,.68)},{offset:1,color}]),borderRadius:horizontal?[0,6,6,0]:[6,6,0,0]},label:{show:true,position:horizontal?'right':'top',fontSize:16,color:KZ_TOKENS.colors.body,formatter:p=>numberFormat(p.value)}};
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
      const next=option(current,{progress:p,width:chart.getWidth()});next.legend.selected={...selected};
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
