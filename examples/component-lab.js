/* Deliberately synthetic data; no source clinical data bundled. */
(function(){'use strict';
const frames=[{"t": 0, "x": 0.08, "y": 0.16, "w": 0.36, "h": 0.33, "r": 0.45, "tint": [255, 244, 220, 0.72], "label": "研究问题", "caption": "界定研究对象、评价范围和需要解决的问题。"}, {"t": 0.12, "x": 0.08, "y": 0.16, "w": 0.36, "h": 0.33, "r": 0.45, "tint": [255, 244, 220, 0.72], "label": "研究问题", "caption": "界定研究对象、评价范围和需要解决的问题。"}, {"t": 0.3, "x": 0.2, "y": 0.13, "w": 0.49, "h": 0.46, "r": 0.14, "tint": [255, 248, 233, 0.78], "label": "证据整理", "caption": "将资料、关键数据与限制条件汇集为可审阅的信息。"}, {"t": 0.42, "x": 0.2, "y": 0.13, "w": 0.49, "h": 0.46, "r": 0.14, "tint": [255, 248, 233, 0.78], "label": "证据整理", "caption": "将资料、关键数据与限制条件汇集为可审阅的信息。"}, {"t": 0.62, "x": 0.1, "y": 0.1, "w": 0.79, "h": 0.53, "r": 0.1, "tint": [247, 250, 252, 0.86], "label": "决策审阅", "caption": "比较证据和可选方案，形成明确的审阅意见。"}, {"t": 0.74, "x": 0.1, "y": 0.1, "w": 0.79, "h": 0.53, "r": 0.1, "tint": [247, 250, 252, 0.86], "label": "决策审阅", "caption": "比较证据和可选方案，形成明确的审阅意见。"}, {"t": 0.88, "x": 0.08, "y": 0.16, "w": 0.36, "h": 0.33, "r": 0.45, "tint": [255, 244, 220, 0.72], "label": "研究问题", "caption": "界定研究对象、评价范围和需要解决的问题。"}, {"t": 1, "x": 0.08, "y": 0.16, "w": 0.36, "h": 0.33, "r": 0.45, "tint": [255, 244, 220, 0.72], "label": "研究问题", "caption": "界定研究对象、评价范围和需要解决的问题。"}];
const lineData={"kind": "line", "unit": "项", "description": "虚构示例。各季度完成项目数，不代表实际业务数据。", "categories": ["第一季度", "第二季度", "第三季度", "第四季度"], "series": [{"id": "review", "name": "审阅完成", "values": [12, 18, 25, 31]}, {"id": "archive", "name": "资料归档", "values": [9, 14, 22, 28]}], "decimals": 0};
const ganttData={"min": 8104, "max": 8116, "tasks": [{"id": "design", "label": "设计确认", "start": 8104, "end": 8107}, {"id": "prepare", "label": "资料准备", "start": 8105, "end": 8109}, {"id": "review", "label": "集中审阅", "start": 8107, "end": 8111}, {"id": "follow", "label": "后续复核", "start": 8110, "end": 8115}]};
const q=s=>document.querySelector(s),el=KZDrilldown.element;
const film=new KZMotion.Film(q('#main-film'),{frames,duration:36000,onRender(f,p){document.querySelectorAll('#main-film [data-phase]').forEach((n,i)=>{const phase=f.label==='研究问题'?0:f.label==='证据整理'?1:2;n.style.background=phase===i?'rgba(255,241,211,.58)':'rgba(255,255,255,.35)';n.setAttribute('aria-current',phase===i?'step':'false');});}});
const tilt=KZMotion.mountTilt(document);KZMotion.reveal(q('#components'));
const line=KZCharts.mount(q('#line-chart'),lineData,{onProgress(p,d){q('#chart-value').textContent=String(Math.round(d.series[0].values.at(-1)*p));}});
const bar=KZCharts.mount(q('#bar-chart'),{kind:'column',unit:'项',decimals:0,categories:['设计确认','资料准备','集中审阅','后续复核'],series:[{id:'stages',name:'任务数',values:[12,18,25,31]}]});

const gantt=KZGantt.mount(q('#gantt'),ganttData);
const drill=new KZDrilldown.Drilldown({host:document.body,onOpen(){film.pause('dialog');},onClose(){film.resume('dialog');}});
function table(parent){const t=el('table','lab-table');for(const row of [['审阅维度','示例关注点'],['完整性','资料与关键字段是否齐备'],['一致性','数值、结论与展示口径是否一致'],['限制条件','缺失项与不确定性是否明确']]){const tr=el('tr');row.forEach((v,i)=>tr.append(el(i===0?'th':'td',null,v)));t.append(tr);}parent.append(t);}
function openL2(container){
 container.append(el('p','lab-section-intro','此层保存完整的示例审阅结构，并呈现独立的审阅过程。返回后，上一级图表与滚动位置保持不变。'));
 const grid=el('div','kz-grid kz-grid-two'),a=el('article','kz-card'),b=el('article','kz-card');a.append(el('h3',null,'审阅维度'));table(a);
 const fr=el('div','kz-film'),stage=el('div','kz-film-stage'),carrier=el('div','kz-film-carrier');carrier.append(el('strong','kz-film-carrier-label','研究问题'));stage.append(carrier);fr.append(stage,el('p','kz-film-caption'));
 b.append(el('h3',null,'审阅过程'),fr);grid.append(a,b);container.append(grid);
 const nested=new KZMotion.Film(fr,{frames,duration:36000});window.KZ_LAB.nested=nested;return {pause:()=>nested.pause('parent'),resume:()=>nested.resume('parent'),dispose:()=>nested.dispose()};
}
q('#open-details').addEventListener('click',event=>drill.push({id:'evidence',title:'证据明细',render(container,manager){
 container.append(el('p','lab-section-intro','详细层不是缩小的提示框。这里同时容纳数据图、审阅维度和进一步的方法说明。'));
 const grid=el('div','lab-details-grid'),a=el('article','kz-card'),b=el('article','kz-card'),ce=el('div','kz-chart');a.append(el('h3',null,'季度比较'),ce);b.append(el('h3',null,'核对要点'));table(b);const next=el('button','kz-button','查看审阅方法');next.type='button';next.id='open-method';next.style.marginTop='24px';next.addEventListener('click',()=>manager.push({id:'method',title:'审阅方法',render:openL2},next));b.append(next);grid.append(a,b);container.append(grid);
 container.append(el('p','lab-section-intro','每一项需要与资料核对的限制条件都应保留在对应明细中。缺少原始材料时，明确写明尚未提供，不以推测补齐。'));
 const c=KZCharts.mount(ce,lineData);return {pause:()=>c.pause(),resume:()=>c.resize(),dispose:()=>c.dispose()};
}},event.currentTarget));
window.KZ_LAB={film,line,bar,gantt,drill,frames,lineData,ganttData,tilt,dispose(){film.dispose();line.dispose();bar.dispose();gantt.dispose();drill.dispose();tilt.dispose?.();}};
document.documentElement.dataset.kzLabReady='true';
})();