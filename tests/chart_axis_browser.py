"""Real Chrome/ECharts axis checks, including animated values and explicit scales."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from inline_preview import inline_html
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--chromium',required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=a.chromium)
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(inline_html(ROOT/'examples/component-lab.html'));page.wait_for_function("document.documentElement.dataset.kzLabReady==='true'")
    result=page.evaluate('''()=>{
      const cases=[
        {name:'integer-gap',v:[2,null,5,7],expected:[0,8,2]},
        {name:'fractional',v:[.002,null,.005,.007],expected:[0,.008,.002]},
        {name:'negative',v:[-2,null,-5,-7],expected:[-8,0,2]},
        {name:'mixed',v:[-7,null,5,7],expected:[-10,10,5]},
        {name:'zero',v:[0,null,0,0],expected:[0,1,.2]},
        {name:'missing',v:[null,null,null,null],expected:[0,1,.2]},
        {name:'finite-extreme',v:[-1e308,null,5,1e308],expected:[-1e308,1e308,undefined]},
        {name:'finite-subnormal',v:[0,null,5e-324,1e-323],expected:[0,1e-323,undefined]},
        {name:'explicit',v:[2,null,5,7],axis:{min:0,max:7.84,interval:1.12},expected:[0,7.84,1.12]}
      ];
      const out=[];
      for(const c of cases){
        const d={kind:'line',categories:['准备','启动','执行','核查'],series:[{id:'axis-probe',values:c.v}],unit:'份',axis:c.axis};
        const options=KZCharts.option(d),axis=options.yAxis,got=[axis.min,axis.max,axis.interval];
        const element=document.createElement('div');element.style.cssText='width:800px;height:400px';document.body.append(element);
        const controller=KZCharts.mount(element,d);controller.renderProgress(.25);const first=controller.chart.getOption().yAxis[0];controller.finish();const final=controller.chart.getOption().yAxis[0];
        out.push({name:c.name,expected:c.expected,actual:got,pass:JSON.stringify(got)===JSON.stringify(c.expected)&&first.min===final.min&&first.max===final.max&&first.interval===final.interval&&JSON.stringify(final?controller.getData().series[0].values:[])===JSON.stringify(c.v),gapPreserved:options.series[0].data[1]===null,area:!!options.series[0].areaStyle});
        controller.dispose();element.remove();
      }
      const large={kind:'line',categories:Array.from({length:200000},(_,i)=>String(i)),series:[{id:'large',values:Array.from({length:200000},(_,i)=>i===1?null:i%8)}],unit:'份'};
      const largeOption=KZCharts.option(large);
      out.push({name:'200000-values-no-argument-spread',pass:largeOption.yAxis.max===8&&largeOption.series[0].data.length===200000,gapPreserved:largeOption.series[0].data[1]===null,area:!!largeOption.series[0].areaStyle});
      const element=document.createElement('div');element.style.cssText='width:320px;height:300px';document.body.append(element);
      const min=KZGantt.qindex(2024,3),max=KZGantt.qindex(2026,1),data={min,max,tasks:[{id:'quarter-probe',label:'季度核对',start:min,end:min+2}]};
      const g=KZGantt.mount(element,data),formatter=g.chart.getOption().xAxis[0].axisLabel.formatter;
      const gantt={first:formatter(min),exclusiveMax:formatter(max),unchanged:JSON.stringify(g.getData())===JSON.stringify(data)};
      gantt.pass=gantt.first==='2024Q3'&&gantt.exclusiveMax===''&&gantt.unchanged;
      g.dispose();element.remove();
      const single={kind:'line',categories:['甲','乙'],series:[{id:'single',values:[2,5]}],unit:'项'};
      const validation=[];
      for(const axis of [{min:10},{max:-1}]){
        let error='';try{KZCharts.validate({...single,axis});}catch(e){error=e.message;}
        validation.push({axis,error,pass:error.includes('自动范围冲突')});
      }
      for(const axis of [{min:1},{max:10}]){
        const o=KZCharts.option({...single,axis});validation.push({axis,actual:[o.yAxis.min,o.yAxis.max],pass:o.yAxis.min<o.yAxis.max&&o.yAxis.interval===undefined});
      }
      return {version:echarts.version,cases:out,gantt,validation};
    }''')
    browser.close()
result.update(scope='component real Chrome/ECharts, not upstream/Office/whole skill',errors=errors,runtime_sha256=hashlib.sha256((ROOT/'runtime/kz-charts.js').read_bytes()).hexdigest())
result['pass']=all(c['pass'] and c['gapPreserved'] and c['area'] for c in result['cases']) and result['gantt']['pass'] and all(x['pass'] for x in result['validation']) and not errors
(a.out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False));sys.exit(not result['pass'])
