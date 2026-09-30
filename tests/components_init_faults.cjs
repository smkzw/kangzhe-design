/* Node VM fault injection of the actual runtime modules (kz-charts/kz-gantt/kz-motion).
   document/window/ECharts/ResizeObserver below are component stubs standing in for the
   browser and ECharts APIs — this is not a browser, an LLM, or a rendered output claim.
   Faults are reachable caller callbacks (opts.onProgress) and stubbed native throws. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ROOT=process.argv[2]||'.';
const source=name=>fs.readFileSync(ROOT+'/'+name,'utf8');
const SOURCES={charts:source('runtime/kz-charts.js'),gantt:source('runtime/kz-gantt.js'),motion:source('runtime/kz-motion.js')};
const TOKENS={colors:{brand:'#0a6b58',body:'#33414a',ink:'#111111'},departments:{operations:{color:'#1779a8'},statistics:{color:'#a87617'},pv:{color:'#7a3fa0'}},fonts:{fallback_css:'sans-serif'},motion:{chart_ms:900},wide:{htmlppt_reference_height:720}};
function tracker(){const live=new Map();const drop=(t,cb)=>live.get(t)?.delete(cb);return{
 addEventListener(t,cb,options){if(!live.has(t))live.set(t,new Set());live.get(t).add(cb);const signal=options?.signal;if(signal){if(signal.aborted)drop(t,cb);else signal.addEventListener('abort',()=>drop(t,cb),{once:true});}},
 removeEventListener(t,cb){drop(t,cb)},count(t){return live.get(t)?.size??0},total(){let n=0;for(const s of live.values())n+=s.size;return n}}}
function element(tag){const el={tagName:tag,className:'',children:[],dataset:{},style:{},attrs:{},textContent:'',type:'',hidden:false,disabled:false,value:'',tabIndex:0,classes:new Set(),
 get childNodes(){return [...el.children]},
 get classList(){return{add:(...c)=>c.forEach(x=>el.classes.add(x)),remove:(...c)=>c.forEach(x=>el.classes.delete(x)),contains:c=>el.classes.has(c)}},
 setAttribute(k,v){el.attrs[k]=v},getAttribute(k){return el.attrs[k]},append(...n){el.children.push(...n)},replaceChildren(...n){el.children=[...n]},
 addEventListener(){},removeEventListener(){},focus(){},setPointerCapture(){},releasePointerCapture(){},hasPointerCapture(){return false},
 getBoundingClientRect(){return{left:0,top:0,width:640,height:320}},closest(){return null},querySelector(){return null},querySelectorAll(){return[]}};return el;}
const CHART_DATA={kind:'bar',categories:['Q1','Q2'],series:[{id:'s1',name:'系列一',values:[3,5]}],unit:'份'};
const GANTT_DATA={min:2024*4,max:2024*4+4,tasks:[{id:'t1',label:'设计',start:2024*4,end:2024*4+2},{id:'t2',label:'评审',start:2024*4+2,end:2024*4+4}]};
function observerStub(observers){return class{constructor(cb){this.cb=cb;this.live=false;observers.push(this)}observe(){this.live=true}disconnect(){this.live=false}}}
function chartsEnv(faults={}){
 const observers=[];
 const chart={disposed:false,calls:0,getWidth:()=>1280,getOption:()=>null,resize(){},on(){},
  setOption(){if(faults.setOption)throw Error('setOption fault');chart.calls++;},
  dispose(){chart.disposed=true;if(faults.chartDispose)throw Error('chart dispose fault');}};
 const doc=tracker(),win=tracker(),mq=tracker();doc.hidden=false;mq.matches=false;
 const echarts={init(){if(faults.init)throw Error('init fault');return chart},graphic:{LinearGradient:function(){}}};
 const context={window:win,document:doc,matchMedia:()=>mq,ResizeObserver:observerStub(observers),echarts,KZ_TOKENS:TOKENS,requestAnimationFrame:()=>1,cancelAnimationFrame:()=>{},innerHeight:720};
 win.echarts=echarts;
 vm.runInNewContext(SOURCES.charts,context);
 return {chart,doc,win,mq,context,liveObservers:()=>observers.filter(o=>o.live).length};
}
function ganttEnv(faults={}){
 const observers=[],aborts=[];
 const chart={disposed:false,calls:0,getWidth:()=>900,resize(){},convertFromPixel(){return 0},convertToPixel(){return[0,0]},
  setOption(){if(faults.setOption)throw Error('setOption fault');chart.calls++;},
  dispose(){chart.disposed=true;if(faults.chartDispose)throw Error('chart dispose fault');}};
 const doc=tracker();doc.hidden=false;doc.createElement=tag=>element(tag);
 const mq=tracker();mq.matches=false;
 const win=tracker();win.echarts={init:()=>chart};
 const context={window:win,document:doc,matchMedia:()=>mq,ResizeObserver:observerStub(observers),
  AbortController:class extends AbortController{constructor(){super();aborts.push(this)}},
  echarts:win.echarts,KZ_TOKENS:TOKENS,requestAnimationFrame:()=>1,cancelAnimationFrame:()=>{},innerHeight:720};
 vm.runInNewContext(SOURCES.gantt,context);
 const root=element('div');root.classList.add('orig');root.dataset.kzGantt='1';root.dataset.keep='x';
 const original=element('span');root.children.push(original);
 return {chart,doc,win,mq,root,original,context,aborts,liveObservers:()=>observers.filter(o=>o.live).length};
}
function motionEnv(faults={}){
 const doc=tracker(),win=tracker(),mq=tracker();doc.hidden=false;mq.matches=false;let mediaCalls=0,thrown=false;
 const context={window:win,document:doc,
  matchMedia:()=>{mediaCalls++;if(faults.mediaSecond&&mediaCalls===2)throw Error('media fault');return mq},
  ResizeObserver:class{observe(){}disconnect(){}},IntersectionObserver:class{observe(){}disconnect(){}},
  AbortController,HTMLElement:function Element(){},requestAnimationFrame:()=>1,cancelAnimationFrame:()=>{},KZ_TOKENS:TOKENS};
 const raw=win.addEventListener;win.addEventListener=(t,cb)=>{if(faults.winThrow===t&&!thrown){thrown=true;throw Error(t+' fault')}raw(t,cb)};
 vm.runInNewContext(SOURCES.motion,context);
 const root=element('div');
 return {context,root,doc,win,mq};
}
const checks=[];
function check(name,fn){try{fn();checks.push({name,pass:true})}catch(error){checks.push({name,pass:false,error:String(error)})}}
const attempt=fn=>{try{fn();return null}catch(error){return error}};
check('charts rollback releases chart/observer/media/visibility/print when user onProgress throws',()=>{
 const x=chartsEnv();
 const error=attempt(()=>x.win.KZCharts.mount({closest:()=>null},CHART_DATA,{onProgress(){throw Error('user onProgress fault')}}));
 assert.equal(error?.message,'user onProgress fault');
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.equal(x.doc.count('visibilitychange'),0);
 assert.equal(x.win.count('beforeprint'),0);
 assert.equal(x.mq.count('change'),0);
});
check('charts rollback releases the same handles when chart.setOption throws',()=>{
 const x=chartsEnv({setOption:true});
 const error=attempt(()=>x.win.KZCharts.mount({closest:()=>null},CHART_DATA,{}));
 assert.equal(error?.message,'setOption fault');
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.equal(x.doc.count('visibilitychange'),0);
 assert.equal(x.win.count('beforeprint'),0);
 assert.equal(x.mq.count('change'),0);
});
check('charts does not guess handles when echarts.init itself throws',()=>{
 const x=chartsEnv({init:true});
 const error=attempt(()=>x.win.KZCharts.mount({closest:()=>null},CHART_DATA,{}));
 assert.equal(error?.message,'init fault');
 assert.equal(x.doc.total()+x.win.total()+x.mq.total(),0);
 assert.equal(x.liveObservers(),0);
});
check('charts successful mount keeps public handle behavior',()=>{
 const x=chartsEnv();let last=null;
 const handle=x.win.KZCharts.mount({closest:()=>null},CHART_DATA,{onProgress(p){last=p}});
 handle.renderProgress(.4);
 assert.equal(last,.4);
 handle.dispose();
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.equal(x.mq.count('change'),0);
});
check('gantt rollback removes editor DOM and releases chart/observer/abort on user onProgress throw',()=>{
 const x=ganttEnv();
 const error=attempt(()=>x.win.KZGantt.mount(x.root,GANTT_DATA,{onProgress(){throw Error('user onProgress fault')}}));
 assert.equal(error?.message,'user onProgress fault');
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.equal(x.aborts.length,1);
 assert.equal(x.aborts[0].signal.aborted,true);
 assert.deepEqual(x.root.children,[x.original]);
 assert.equal(x.root.classes.has('kz-gantt'),false);
 assert.equal(x.root.classes.has('kz-interactive'),false);
 assert.equal(x.root.classes.has('orig'),true);
 assert.equal(x.root.dataset.kzEditing,undefined);
 assert.equal(x.root.dataset.kzGantt,'1');
 assert.equal(x.root.dataset.keep,'x');
});
check('gantt rollback releases the same handles when chart.setOption throws',()=>{
 const x=ganttEnv({setOption:true});
 const error=attempt(()=>x.win.KZGantt.mount(x.root,GANTT_DATA,{}));
 assert.equal(error?.message,'setOption fault');
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.equal(x.aborts[0].signal.aborted,true);
 assert.deepEqual(x.root.children,[x.original]);
 assert.equal(x.root.dataset.kzEditing,undefined);
});
check('gantt rollback keeps the reason and still releases the rest when cleanup also fails',()=>{
 const x=ganttEnv({chartDispose:true});
 const error=attempt(()=>x.win.KZGantt.mount(x.root,GANTT_DATA,{onProgress(){throw Error('user onProgress fault')}}));
 assert.equal(error?.name,'AggregateError');
 assert.equal(error.errors[0].message,'user onProgress fault');
 assert.equal(error.errors[1].message,'chart dispose fault');
 assert.equal(x.aborts[0].signal.aborted,true);
 assert.deepEqual(x.root.children,[x.original]);
 assert.equal(x.root.classes.has('kz-gantt'),false);
 assert.equal(x.root.dataset.kzEditing,undefined);
});
check('gantt successful mount then dispose restores the original root',()=>{
 const x=ganttEnv();
 const handle=x.win.KZGantt.mount(x.root,GANTT_DATA,{});
 assert.deepEqual(x.root.children.length,3);
 handle.dispose();
 assert.equal(x.chart.disposed,true);
 assert.equal(x.liveObservers(),0);
 assert.deepEqual(x.root.children,[x.original]);
 assert.equal(x.root.classes.has('kz-gantt'),false);
 assert.equal(x.root.classes.has('orig'),true);
 assert.equal(x.root.dataset.kzEditing,undefined);
 assert.equal(x.root.dataset.kzGantt,'1');
});
check('mountPage releases tilt and page listeners when a later listener attach throws',()=>{
 const x=motionEnv({winThrow:'beforeprint'});
 const error=attempt(()=>x.context.window.KZMotion.mountPage(x.root));
 assert.equal(error?.message,'beforeprint fault');
 assert.equal(x.doc.count('visibilitychange'),0);
 assert.equal(x.win.total(),0);
 assert.equal(x.mq.count('change'),0);
 assert.equal(x.root.dataset.kzMotionMounted,undefined);
 assert.equal(x.root.dataset.kzMotionActive,undefined);
 const life=x.context.window.KZMotion.mountPage(x.root);
 assert.equal(typeof life.dispose,'function');
 life.dispose();
});
check('mountPage releases an acquired tilt when the environment fails before listeners attach',()=>{
 const x=motionEnv({mediaSecond:true});
 const error=attempt(()=>x.context.window.KZMotion.mountPage(x.root));
 assert.equal(error?.message,'media fault');
 assert.equal(x.mq.count('change'),0);
 assert.equal(x.root.dataset.kzMotionMounted,undefined);
 const life=x.context.window.KZMotion.mountPage(x.root);
 life.dispose();
 assert.equal(x.root.dataset.kzMotionMounted,undefined);
});
console.log(JSON.stringify({scope:'Node VM fault injection of actual runtime modules with labeled component stubs; not a browser, model, or rendered-output claim',checks},null,2));
process.exitCode=checks.every(x=>x.pass)?0:1;
