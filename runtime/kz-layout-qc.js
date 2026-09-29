/* Observes actual text ranges, never empty layout boxes. Not a visual judge. */
(function(g){'use strict';
 function inspectCard(card){
  const box=card.getBoundingClientRect(),style=getComputedStyle(card),ranges=[];
  const walker=document.createTreeWalker(card,NodeFilter.SHOW_TEXT,{acceptNode(n){const p=n.parentElement;if(!n.textContent.trim()||p.closest('script,style,.notes,[hidden]')||!p.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))return NodeFilter.FILTER_REJECT;return NodeFilter.FILTER_ACCEPT;}});
  let node;while(node=walker.nextNode()){const r=document.createRange();r.selectNodeContents(node);for(const q of r.getClientRects())if(q.width&&q.height)ranges.push(q);}
  for(const el of card.querySelectorAll('.kz-chart,.kz-gantt-plot')){const r=el.getBoundingClientRect();if(r.width&&r.height)ranges.push(r);}
  if(!ranges.length)return{id:card.id,status:'EMPTY',rect:box.toJSON()};
  const top=Math.min(...ranges.map(r=>r.top)),bottom=Math.max(...ranges.map(r=>r.bottom));
  const pt=parseFloat(style.paddingTop),pb=parseFloat(style.paddingBottom),h=box.height-pt-pb;
  const gapTop=top-box.top-pt,gapBottom=box.bottom-pb-bottom,span=(bottom-top)/h,balance=Math.abs(gapTop-gapBottom)/h;
  const thresholds=g.KZ_TOKENS?.layout||{card_span_warning:.45,vertical_imbalance_warning:.20};
  const flags=[];if(gapTop<-.5||gapBottom<-.5)flags.push('TEXT_OUTSIDE');
  if(gapBottom>gapTop&&balance>thresholds.vertical_imbalance_warning)flags.push('TOP_HEAVY');
  if(span<thresholds.card_span_warning)flags.push('SPARSE_CONTENT');
  return{id:card.id,layout:card.dataset.kzLayout||'UNDECLARED',rect:box.toJSON(),content:{top,bottom},gapTop,gapBottom,span,balance,flags,status:flags.length?'REVIEW':'MEASURED'};
 }
 g.KZLayoutQC={inspectCard,inspect(root=document){return [...root.querySelectorAll('.kz-card')].filter(e=>e.getBoundingClientRect().height>0&&e.checkVisibility({checkOpacity:true})).map(inspectCard);}};
})(window);
