/* Observes actual text ranges, never empty layout boxes. Not a visual judge. */
(function(g){'use strict';
 function zeroLegacyClip(el){
  for(;el;el=el.parentElement){const st=getComputedStyle(el);if(!/^(absolute|fixed)$/.test(st.position))continue;const match=st.clip.match(/^rect\((.*)\)$/);if(!match)continue;const edges=match[1].split(/[,\s]+/).filter(Boolean).map(v=>/^[-+\d.]+px$/.test(v)?parseFloat(v):NaN);if(edges.length===4&&edges.every(Number.isFinite)&&(edges[1]<=edges[3]||edges[2]<=edges[0]))return true;}return false;
 }
 function inspectCard(card,{chartLibrary=g.echarts}={}){
  const box=card.getBoundingClientRect(),style=getComputedStyle(card),ranges=[];
  // Scrolling tables are verified against their visible scrollport and reachability,
  // not by comparing every offscreen row with the outer card's height.
  const scrollports=[card,...card.querySelectorAll('*')].filter(el=>{const st=getComputedStyle(el);return el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&((/^(auto|scroll)$/.test(st.overflowX)&&el.scrollWidth>el.clientWidth)||(/^(auto|scroll)$/.test(st.overflowY)&&el.scrollHeight>el.clientHeight));});
  if(scrollports.length)return{id:card.id,status:'NOT_TESTED',reason:'local scrollport requires separate visible-region and reachability QC',scrollports:scrollports.map(el=>({id:el.id,rect:el.getBoundingClientRect().toJSON(),client:[el.clientWidth,el.clientHeight],scroll:[el.scrollWidth,el.scrollHeight]}))};
  const walker=document.createTreeWalker(card,NodeFilter.SHOW_TEXT,{acceptNode(n){const p=n.parentElement;if(!n.textContent.trim()||p.closest('script,style,.notes,[hidden]')||zeroLegacyClip(p)||!p.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))return NodeFilter.FILTER_REJECT;return NodeFilter.FILTER_ACCEPT;}});
  let node;while(node=walker.nextNode()){const r=document.createRange();r.selectNodeContents(node);for(const q of r.getClientRects())if(q.width&&q.height)ranges.push(q);}
  for(const el of card.querySelectorAll('.kz-chart,.kz-gantt-plot')){if(!el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;const painted=[...el.querySelectorAll('canvas,svg')].some(e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0);const r=el.getBoundingClientRect();if(!painted||!r.width||!r.height)continue;const chart=chartLibrary?.getInstanceByDom(el),series=chart?.getModel?.()?.getSeries?.();if(!series)return{id:card.id,status:'NOT_TESTED',reason:'painted chart requires reachable actual ECharts data instance',chart:el.id};if(series.some(v=>v.getData().count()>0))ranges.push(r);}
  if(!ranges.length)return{id:card.id,status:'EMPTY',rect:box.toJSON()};
  const top=Math.min(...ranges.map(r=>r.top)),bottom=Math.max(...ranges.map(r=>r.bottom));
  const sy=card.offsetHeight?box.height/card.offsetHeight:1;
  const pt=parseFloat(style.paddingTop)*sy,pb=parseFloat(style.paddingBottom)*sy,h=box.height-pt-pb;
  if(h<=0)return{id:card.id,status:'NOT_TESTED',reason:'no usable reading height'};
  const gapTop=top-box.top-pt,gapBottom=box.bottom-pb-bottom,span=(bottom-top)/h,balance=Math.abs(gapTop-gapBottom)/h;
  const thresholds=g.KZ_TOKENS?.layout||{card_span_warning:.45,vertical_imbalance_warning:.20};
  const flags=[];if(gapTop<-.5||gapBottom<-.5)flags.push('TEXT_OUTSIDE');
  if(gapBottom>gapTop&&balance>thresholds.vertical_imbalance_warning)flags.push('TOP_HEAVY');
  if(span<thresholds.card_span_warning)flags.push('SPARSE_CONTENT');
  return{id:card.id,layout:card.dataset.kzLayout||'UNDECLARED',rect:box.toJSON(),content:{top,bottom},gapTop,gapBottom,span,balance,flags,status:flags.length?'REVIEW':'MEASURED'};
 }
 // Axis-aligned reading-zone check. Run from QC sampling, not a production RAF.
 function inspectTextBounds(root,{tolerance=1,minOpacity=0}={}){
  if(!root||!root.isConnected)return{status:'NOT_TESTED',reason:'missing reading zone'};
  const box=root.getBoundingClientRect(),failures=[];
  let textCount=0,suppressedVisible=0;
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  let node;while(node=walker.nextNode()){
   if(!node.textContent.trim()||node.parentElement.closest('script,style,.notes')||zeroLegacyClip(node.parentElement))continue;
   let opacity=1,visible=node.parentElement.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
   for(let el=node.parentElement;el;el=el.parentElement){const st=getComputedStyle(el);opacity*=Number(st.opacity);if(st.display==='none'){visible=false;break;}}
   if(!visible||opacity===0)continue;
   if(opacity<=minOpacity){suppressedVisible++;continue;}
   const range=document.createRange();range.selectNodeContents(node);
   for(const rect of range.getClientRects()){
    if(!rect.width||!rect.height)continue;textCount++;
    if(rect.left<box.left-tolerance||rect.right>box.right+tolerance||rect.top<box.top-tolerance||rect.bottom>box.bottom+tolerance)
     failures.push({text:node.textContent.trim(),opacity,rect:rect.toJSON(),reason:'reading-zone'});
    for(let el=node.parentElement;el&&el!==root;el=el.parentElement){const st=getComputedStyle(el),edge=el.getBoundingClientRect(),sx=el.offsetWidth?edge.width/el.offsetWidth:1,sy=el.offsetHeight?edge.height/el.offsetHeight:1,clip={left:edge.left+el.clientLeft*sx,top:edge.top+el.clientTop*sy};clip.right=clip.left+el.clientWidth*sx;clip.bottom=clip.top+el.clientHeight*sy;const x=/^(hidden|clip)$/.test(st.overflowX),y=/^(hidden|clip)$/.test(st.overflowY);if((x&&(rect.left<clip.left-tolerance||rect.right>clip.right+tolerance))||(y&&(rect.top<clip.top-tolerance||rect.bottom>clip.bottom+tolerance)))failures.push({text:node.textContent.trim(),opacity,rect:rect.toJSON(),reason:'ancestor-clip',ancestor:el.id||el.className});}
   }
  }
  return{id:root.id,status:failures.length?'FAIL':suppressedVisible?'REVIEW_OPACITY':textCount?'PASS':'EMPTY',rect:box.toJSON(),textCount,suppressedVisible,failures};
 }
 g.KZLayoutQC={inspectCard,inspectTextBounds,inspect(root=document){return [...root.querySelectorAll('.kz-card')].filter(e=>e.getBoundingClientRect().height>0&&e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).map(e=>inspectCard(e));}};
})(window);
