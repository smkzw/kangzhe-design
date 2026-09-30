/* Node VM playback-sequence check of the actual runtime modules (kz-charts/kz-gantt).
   document/window/ECharts/ResizeObserver/requestAnimationFrame below are component stubs
   standing in for the browser and ECharts APIs — this is not a browser, an LLM, or a
   rendered-output claim. The modules' own RAF scheduling runs on a manual clock, so the
   ordinary play() callback sequence is observable as data, not as pixels. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ROOT=process.argv[2]||'.';
const source=name=>fs.readFileSync(ROOT+'/'+name,'utf8');
const SOURCES={charts:source('runtime/kz-charts.js'),gantt:source('runtime/kz-gantt.js')};
const TOKENS={colors:{brand:'#0a6b58',body:'#33414a',ink:'#111111'},departments:{operations:{color:'#1779a8'},statistics:{color:'#a87617'},pv:{color:'#7a3fa0'}},fonts:{fallback_css:'sans-serif'},motion:{chart_ms:900},wide:{htmlppt_reference_height:720}};
function tracker(){const live=new Map();const drop=(t,cb)=>live.get(t)?.delete(cb);return{
 addEventListener(t,cb,options){if(!live.has(t))live.set(t,new Set());live.get(t).add(cb);const signal=options?.signal;if(signal){if(signal.aborted)drop(t,cb);else signal.addEventListener('abort',()=>drop(t,cb),{once:true});}},
 removeEventListener(t,cb){drop(t,cb)},count(t){return live.get(t)?.size??0}}}
function element(tag){const el={tagName:tag,className:'',children:[],dataset:{},style:{},attrs:{},textContent:'',type:'',hidden:false,disabled:false,value:'',tabIndex:0,classes:new Set(),
 get childNodes(){return [...el.children]},
 get classList(){return{add:(...c)=>c.forEach(x=>el.classes.add(x)),remove:(...c)=>c.forEach(x=>el.classes.delete(x)),contains:c=>el.classes.has(c)}},
 setAttribute(k,v){el.attrs[k]=v},getAttribute(k){return el.attrs[k]},append(...n){el.children.push(...n)},replaceChildren(...n){el.children=[...n]},
 addEventListener(){},removeEventListener(){},focus(){},setPointerCapture(){},releasePointerCapture(){},hasPointerCapture(){return false},
 getBoundingClientRect(){return{left:0,top:0,width:640,height:320}},closest(){return null},querySelector(){return null},querySelectorAll(){return[]}};return el;}
function clock(){let now=0,next=1;const queued=new Map();return{
 requestAnimationFrame(cb){const id=next++;queued.set(id,cb);return id;},
 cancelAnimationFrame(id){queued.delete(id);},
 pending(){return queued.size},
 step(dt){now+=dt;const cbs=[...queued.values()];queued.clear();for(const cb of cbs)cb(now);}}}
const drain=(c,dt)=>{for(let i=0;i<16&&c.pending();i++)c.step(dt);};
const CHART_DATA={kind:'bar',categories:['Q1','Q2','Q3','Q4'],series:[{id:'s1',name:'系列一',values:[3,null,5,7]}],unit:'份'};
const GANTT_DATA={min:2024*4,max:2024*4+4,tasks:[{id:'t1',label:'设计',start:2024*4,end:2024*4+2},{id:'t2',label:'评审',start:2024*4+2,end:2024*4+4}]};
function chartsEnv({matches=false}={}){
 const c=clock();
 const chart={disposed:false,calls:0,getWidth:()=>1280,getOption:()=>null,resize(){},on(){},
  setOption(){chart.calls++;},
  dispose(){chart.disposed=true;}};
 const doc=tracker(),win=tracker(),mq=tracker();doc.hidden=false;mq.matches=matches;
 const echarts={init:()=>chart,graphic:{LinearGradient:function(){}}};
 const context={window:win,document:doc,matchMedia:()=>mq,ResizeObserver:class{observe(){}disconnect(){}},echarts,KZ_TOKENS:TOKENS,
  requestAnimationFrame:c.requestAnimationFrame,cancelAnimationFrame:c.cancelAnimationFrame,innerHeight:720};
 win.echarts=echarts;
 vm.runInNewContext(SOURCES.charts,context);
 return {chart,doc,win,mq,clock:c,context};
}
function ganttEnv({matches=false}={}){
 const c=clock();
 const chart={disposed:false,calls:0,getWidth:()=>900,resize(){},convertFromPixel(){return 0},convertToPixel(){return[0,0]},
  setOption(){chart.calls++;},
  dispose(){chart.disposed=true;}};
 const doc=tracker();doc.hidden=false;doc.createElement=tag=>element(tag);
 const mq=tracker();mq.matches=matches;
 const win=tracker();win.echarts={init:()=>chart};
 const context={window:win,document:doc,matchMedia:()=>mq,ResizeObserver:class{observe(){}disconnect(){}},
  AbortController,echarts:win.echarts,KZ_TOKENS:TOKENS,requestAnimationFrame:c.requestAnimationFrame,cancelAnimationFrame:c.cancelAnimationFrame,innerHeight:720};
 vm.runInNewContext(SOURCES.gantt,context);
 const root=element('div');
 return {chart,doc,win,mq,clock:c,root,context};
}
const monotonic=values=>{for(let i=1;i<values.length;i++)assert.ok(values[i]>=values[i-1],`progress must not decrease: ${values.join(',')}`);};
const clone=x=>JSON.parse(JSON.stringify(x));
const checks=[];
function check(name,fn){try{fn();checks.push({name,pass:true})}catch(error){checks.push({name,pass:false,error:String(error)})}}
check('charts ordinary play renders 0 synchronously, then grows monotonically to the true 1',()=>{
 const x=chartsEnv();const seq=[];const input=clone(CHART_DATA);
 const handle=x.context.window.KZCharts.mount({closest:()=>null},input,{onProgress:p=>seq.push(p)});
 assert.deepEqual(seq,[1],'mount still renders the static complete value');
 const before=seq.length;handle.play(900);
 assert.deepEqual(seq.slice(before),[0],'ordinary play must render 0 synchronously instead of jumping to 1');
 assert.equal(handle.getProgress(),0);
 drain(x.clock,300);
 const frames=seq.slice(before);monotonic(frames);
 assert.equal(frames[frames.length-1],1);
 assert.equal(handle.getProgress(),1);
 assert.equal(x.clock.pending(),0);
 assert.equal(JSON.stringify(handle.getData()),JSON.stringify(input),'data model untouched by playback');
 assert.equal(JSON.stringify(handle.getData().series[0].values),'[3,null,5,7]','null preserved and values unscaled');
});
check('gantt ordinary play renders 0 synchronously, then grows monotonically to the true 1',()=>{
 const x=ganttEnv();const seq=[];const input=clone(GANTT_DATA);
 const handle=x.context.window.KZGantt.mount(x.root,input,{onProgress:p=>seq.push(p)});
 assert.deepEqual(seq,[1],'mount still renders the static complete value');
 const before=seq.length;handle.play(1000);
 assert.deepEqual(seq.slice(before),[0],'ordinary play must render 0 synchronously instead of jumping to 1');
 assert.equal(handle.getProgress(),0);
 drain(x.clock,250);
 const frames=seq.slice(before);monotonic(frames);
 assert.equal(frames[frames.length-1],1);
 assert.equal(handle.getProgress(),1);
 assert.equal(x.clock.pending(),0);
 assert.equal(JSON.stringify(handle.getData()),JSON.stringify(input),'quarter model untouched by playback');
 assert.ok(handle.getData().tasks.every(t=>Number.isInteger(t.start)&&Number.isInteger(t.end)),'quarters stay integers');
});
check('charts finish/pause and reduced motion still land on the true 1',()=>{
 const x=chartsEnv();let last=null;
 const handle=x.context.window.KZCharts.mount({closest:()=>null},clone(CHART_DATA),{onProgress:p=>{last=p}});
 handle.play(900);x.clock.step(300);assert.ok(last<1);
 handle.finish();assert.equal(last,1);assert.equal(handle.getProgress(),1);
 handle.play(900);x.clock.step(100);handle.pause();assert.equal(last,1);assert.equal(x.clock.pending(),0);
 const y=chartsEnv({matches:true});let rm=null;
 const h2=y.context.window.KZCharts.mount({closest:()=>null},clone(CHART_DATA),{onProgress:p=>{rm=p}});
 h2.play(900);assert.equal(rm,1);assert.equal(h2.getProgress(),1);assert.equal(y.clock.pending(),0);
});
check('gantt finish/pause and reduced motion still land on the true 1',()=>{
 const x=ganttEnv();let last=null;
 const handle=x.context.window.KZGantt.mount(x.root,clone(GANTT_DATA),{onProgress:p=>{last=p}});
 handle.play(1000);x.clock.step(250);assert.ok(last<1);
 handle.finish();assert.equal(last,1);assert.equal(handle.getProgress(),1);
 handle.play(1000);x.clock.step(100);handle.pause();assert.equal(last,1);assert.equal(x.clock.pending(),0);
 const y=ganttEnv({matches:true});let rm=null;
 const h2=y.context.window.KZGantt.mount(y.root,clone(GANTT_DATA),{onProgress:p=>{rm=p}});
 h2.play(1000);assert.equal(rm,1);assert.equal(h2.getProgress(),1);assert.equal(y.clock.pending(),0);
});
check('charts play/finish after dispose keep no side effects on the released chart',()=>{
 const x=chartsEnv();const seq=[];
 const handle=x.context.window.KZCharts.mount({closest:()=>null},clone(CHART_DATA),{onProgress:p=>seq.push(p)});
 handle.dispose();
 const calls=x.chart.calls,seen=seq.length;
 handle.finish();handle.play(900);handle.renderProgress(.5);
 x.clock.step(300);x.clock.step(300);
 assert.equal(x.chart.calls,calls,'no setOption on a released chart');
 assert.equal(seq.length,seen,'no onProgress after dispose');
 assert.equal(x.clock.pending(),0);
});
check('gantt play/finish after dispose keep no side effects on the released chart',()=>{
 const x=ganttEnv();const seq=[];
 const handle=x.context.window.KZGantt.mount(x.root,clone(GANTT_DATA),{onProgress:p=>seq.push(p)});
 handle.dispose();
 const calls=x.chart.calls,seen=seq.length,progress=handle.getProgress();
 handle.finish();handle.play(1000);
 x.clock.step(250);x.clock.step(250);
 assert.equal(x.chart.calls,calls,'no setOption on a released chart');
 assert.equal(seq.length,seen,'no onProgress after dispose');
 assert.equal(handle.getProgress(),progress);
 assert.equal(x.clock.pending(),0);
});
console.log(JSON.stringify({scope:'Node VM playback-sequence check of actual runtime modules with labeled component stubs and a manual RAF clock; not a browser, model, or rendered-output claim',checks},null,2));
process.exitCode=checks.every(x=>x.pass)?0:1;
