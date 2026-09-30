/* Fault injection checks the example host, not a model or browser result. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
function setup(faults={}){
 const calls=[],host=new EventTarget(),doc=new EventTarget(),mq=new EventTarget();
 const classes=new Set(['kz-background-paused']);
 const deck={dataset:{chrome:'body'},querySelectorAll:()=>[],querySelector:()=>({})};
 doc.readyState='complete';doc.hidden=true;doc.querySelector=()=>deck;
 doc.body={dataset:{},classList:{toggle(n,v){v?classes.add(n):classes.delete(n)},remove(n){classes.delete(n)}}};
 if(faults.initialFrozen!==undefined)doc.body.dataset.kzFrozen=faults.initialFrozen;
 mq.matches=false;
 const mounted=n=>{if(faults.mount===n)throw Error(n+' mount');return {finish(){},pause(){},dispose(){calls.push(n);if(faults.dispose?.includes(n))throw Error(n+' dispose')}}};
 const win={addEventListener:host.addEventListener.bind(host),document:doc};
 if(faults.seed)Object.assign(win,faults.seed);
 const context={window:win,document:doc,AbortController,AggregateError,matchMedia:()=>mq,addEventListener:host.addEventListener.bind(host),KZ_DECK_DATA:{chart:{},gantt:{}},KZCharts:{mount:()=>mounted('chart')},KZGantt:{mount:()=>mounted('gantt')},KZMotion:{mountPage(){return {dispose(){throw Error('motion dispose')}}}},KZHTMLPPT:{bind(_deck,factory){if(faults.bind)throw Error('bind');if(faults.motionDispose){const life=factory({});return {dispose(){life.dispose()}}}return mounted('bridge')}}};
 let error;try{vm.runInNewContext(source,context)}catch(e){error=e}
 return {win,doc,mq,calls,classes,error};
}
const checks=[];
function check(name,fn){try{fn();checks.push({name,pass:true})}catch(error){checks.push({name,pass:false,error:String(error)})}}
check('initial bind failure releases both returned components',()=>{const x=setup({bind:true});assert.deepEqual(x.calls,['chart','gantt']);assert.equal(x.error.message,'bind');assert.equal(x.classes.size,0)});
check('second mount failure releases first component',()=>{const x=setup({mount:'gantt'});assert.deepEqual(x.calls,['chart']);assert.equal(x.error.message,'gantt mount')});
check('initial error and cleanup error are both preserved',()=>{const x=setup({bind:true,dispose:['chart']});assert.equal(x.error.name,'AggregateError');assert.equal(x.error.errors[0].message,'bind');assert.equal(x.error.errors[1].errors[0].message,'chart dispose');assert.deepEqual(x.calls,['chart','gantt'])});
check('all disposal errors collected after releasing every resource',()=>{const x=setup({dispose:['bridge','chart','gantt']});const dispose=x.win.__kzDispose;assert.equal(typeof dispose,'function');let e;try{dispose()}catch(error){e=error}assert.equal(e.name,'AggregateError');assert.deepEqual([...e.errors].map(x=>x.message),['bridge dispose','chart dispose','gantt dispose']);assert.deepEqual(x.calls,['bridge','chart','gantt']);assert.equal(x.classes.size,0)});
check('dispose is idempotent and aborts ambient listeners',()=>{const x=setup();const dispose=x.win.__kzDispose;assert.equal(x.classes.has('kz-background-paused'),true);dispose();x.doc.dispatchEvent(new Event('visibilitychange'));dispose();assert.equal(x.classes.size,0);assert.deepEqual(x.calls,['bridge','chart','gantt'])});
check('throwing motion disposal still removes host page references',()=>{const x=setup({motionDispose:true});const pages=x.win.__kzMotionPages,dispose=x.win.__kzDispose;assert.equal(pages.size,1);try{dispose()}catch{}assert.equal(pages.size,0);assert.deepEqual(x.calls,['chart','gantt']);assert.equal(x.classes.size,0)});
check('dispose removes only host-created frozen attribute',()=>{const x=setup();assert.equal(x.doc.body.dataset.kzFrozen,'false');x.win.__kzDispose();assert.equal(x.doc.body.dataset.kzFrozen,undefined)});
check('dispose preserves preexisting frozen attribute',()=>{const x=setup({initialFrozen:'true'});x.win.__kzDispose();assert.equal(x.doc.body.dataset.kzFrozen,'true')});
check('dispose clears only its own published globals and keeps the saved handle callable',()=>{const x=setup();const dispose=x.win.__kzDispose;assert.equal(typeof dispose,'function');dispose();assert.equal(x.win.__kzInstances,undefined);assert.equal(x.win.__kzMotionPages,undefined);assert.equal(x.win.__kzBridge,undefined);assert.equal(x.win.__kzDispose,undefined);dispose();assert.deepEqual(x.calls,['bridge','chart','gantt'])});
check('dispose restores prior globals and preserves later foreign replacements',()=>{const priorBridge={legacy:true},priorDispose=()=>{};const x=setup({seed:{__kzBridge:priorBridge,__kzDispose:priorDispose}});const foreign={mine:true};x.win.__kzInstances=foreign;x.win.__kzDispose();assert.equal(x.win.__kzBridge,priorBridge);assert.equal(x.win.__kzDispose,priorDispose);assert.equal(x.win.__kzInstances,foreign);assert.equal(x.win.__kzMotionPages,undefined)});
console.log(JSON.stringify({scope:'Node fault injection of actual example with component stubs',checks},null,2));
process.exitCode=checks.every(x=>x.pass)?0:1;
