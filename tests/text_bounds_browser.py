"""Real browser reading-zone regression; no model or visual acceptance claims."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--chrome',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
script=Path(__file__).resolve().parents[1]/'runtime/kz-layout-qc.js'
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=args.chrome);p=b.new_page()
    p.set_content('''<style>body{margin:0}#zone{position:relative;width:200px;height:100px;padding:10px;box-sizing:border-box;font:20px/24px sans-serif}#text{margin:0;position:relative}</style><div id="zone"><p id="text">可读的正文</p></div>''');p.add_script_tag(path=str(script));results=[]
    def check(name,expected):
        result=p.evaluate('KZLayoutQC.inspectTextBounds(document.querySelector("#zone"))');results.append({'name':name,'expected':expected,'observed':result});assert result['status']==expected,(name,result)
    check('contained Chinese','PASS')
    p.evaluate('document.querySelector("#text").style.left="180px"');check('horizontal spill','FAIL')
    p.evaluate('document.querySelector("#text").style.cssText="top:90px"');check('vertical spill','FAIL')
    p.evaluate('document.querySelector("#text").style.opacity="0.1";document.querySelector("#zone").style.opacity="0.01"');check('effective ancestor opacity','FAIL')
    p.evaluate('document.querySelector("#zone").style.opacity="0"');check('zero opacity placeholder','EMPTY')
    p.evaluate('document.querySelector("#zone").style.opacity="1"');check('visible transition still spills','FAIL')
    p.evaluate('document.querySelector("#text").hidden=true');check('hidden text','EMPTY')
    p.evaluate('document.querySelector("#text").hidden=false;document.querySelector("#text").style.cssText=""');check('restored readable state','PASS')
    results.append({'name':'missing zone','observed':p.evaluate('KZLayoutQC.inspectTextBounds(null)')});assert results[-1]['observed']['status']=='NOT_TESTED'
    p.set_content('<div id=zone style="width:320px;height:100px;padding:20px;box-sizing:border-box;font:20px/24px sans-serif"><div style="width:70px;overflow:hidden;white-space:nowrap">被裁切的整行文字必须识别</div></div>');p.add_script_tag(path=str(script));check('nested rectangular clipping','FAIL')
    p.set_content('<div id=empty class=kz-card style="width:300px;height:200px;padding:20px"><div class=kz-chart style="height:120px"></div></div>');p.add_script_tag(path=str(script));result=p.evaluate('KZLayoutQC.inspectCard(document.querySelector("#empty"))');assert result['status']=='EMPTY',result;results.append({'name':'empty chart shell','observed':result})
    p.set_content('<div id=scaled style="width:300px;height:200px;padding:20px;transform:scale(.5);transform-origin:top left;box-sizing:border-box"><p style="margin:0;font:20px/32px sans-serif">卡片中的正常文字</p></div>');p.add_script_tag(path=str(script));result=p.evaluate('KZLayoutQC.inspectCard(document.querySelector("#scaled"))');assert 'TEXT_OUTSIDE' not in result['flags'],result;results.append({'name':'scaled padding same coordinates','observed':result})
    p.set_content('<div id=zone style="position:relative;width:200px;height:100px;font:20px/32px sans-serif"><div style="visibility:hidden"><p style="visibility:visible;position:relative;left:180px;margin:0">可见溢出的正文</p></div></div>');p.add_script_tag(path=str(script));check('descendant visibility overrides hidden ancestor','FAIL')
    p.set_content('<div id=zone style="width:200px;height:100px"><div style="display:none"><p style="display:block;visibility:visible">仍不可见</p></div></div>');p.add_script_tag(path=str(script));check('display none cannot be overridden by descendants','EMPTY')
    rows=''.join('<tr><td>第'+str(i)+'行</td><td>完整表格数据</td></tr>' for i in range(12))
    p.set_content('<div id=card style="width:300px;height:200px;padding:20px;box-sizing:border-box"><div id=local style="height:100px;overflow:auto"><table>'+rows+'</table></div></div>');p.add_script_tag(path=str(script));result=p.evaluate('KZLayoutQC.inspectCard(document.querySelector("#card"))');assert result['status']=='NOT_TESTED' and result['scrollports'][0]['id']=='local',result;results.append({'name':'legal scrolling table needs separate reachability QC','observed':result})
    p.set_content('<div id=card style="width:300px;height:200px;padding:20px"><div id=chart class=kz-chart style="width:240px;height:120px"></div></div>');p.add_script_tag(path=str(script.parents[1]/'assets/vendor/echarts.min.js'));p.add_script_tag(path=str(script));p.evaluate("window.realChart=echarts.init(document.querySelector('#chart'));realChart.setOption({animation:false,xAxis:{type:'category',data:['甲','乙']},yAxis:{type:'value'},series:[{type:'bar',data:[1,2]}]})")
    for name,css,expected in [('actual ECharts visible','',False),('actual ECharts visibility hidden','visibility:hidden',True),('actual ECharts opacity zero','opacity:0',True)]:
        p.evaluate("css=>document.querySelector('#chart').style.cssText='width:240px;height:120px;'+css",css);result=p.evaluate('KZLayoutQC.inspectCard(document.querySelector("#card"))');assert (result['status']=='EMPTY')==expected,result;results.append({'name':name,'echarts':p.evaluate('echarts.version'),'observed':result})
    p.evaluate("document.querySelector('#chart').style.opacity='1';document.querySelector('#card').style.opacity='0'");result=p.evaluate('KZLayoutQC.inspectCard(document.querySelector("#card"))');assert result['status']=='EMPTY',result;results.append({'name':'actual ECharts ancestor opacity zero','observed':result});b.close()
Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2));print(str(len(results))+' real-browser layout checks passed')
