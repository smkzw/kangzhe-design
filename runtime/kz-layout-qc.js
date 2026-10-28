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
  const textRanges=ranges.slice();
  for(const el of card.querySelectorAll('.kz-chart,.kz-gantt-plot')){if(!el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;const painted=[...el.querySelectorAll('canvas,svg')].some(e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0);const r=el.getBoundingClientRect();if(!painted||!r.width||!r.height)continue;const chart=chartLibrary?.getInstanceByDom(el),series=chart?.getModel?.()?.getSeries?.();if(!series)return{id:card.id,status:'NOT_TESTED',reason:'painted chart requires reachable actual ECharts data instance',chart:el.id};if(series.some(v=>v.getData().count()>0))ranges.push(r);}
  if(!ranges.length)return{id:card.id,status:'EMPTY',rect:box.toJSON()};
  const top=Math.min(...ranges.map(r=>r.top)),bottom=Math.max(...ranges.map(r=>r.bottom));
  const sy=card.offsetHeight?box.height/card.offsetHeight:1;
  const pt=parseFloat(style.paddingTop)*sy,pb=parseFloat(style.paddingBottom)*sy,h=box.height-pt-pb;
  if(h<=0)return{id:card.id,status:'NOT_TESTED',reason:'no usable reading height'};
  const gapTop=top-box.top-pt,gapBottom=box.bottom-pb-bottom,span=(bottom-top)/h,balance=Math.abs(gapTop-gapBottom)/h;
  const thresholds=g.KZ_TOKENS?.layout||{card_span_warning:.45,vertical_imbalance_warning:.20},qc=thresholds.qc||{};
  // Text must stay inside the padding box. Glyph content areas overhang tight line boxes (line-height 1.25), so the
  // vertical allowance is a fraction of the card's font size; horizontally the allowance is a pixel (10 G5-LAYOUT).
  const sx=card.offsetWidth?box.width/card.offsetWidth:1,pl=parseFloat(style.paddingLeft)*sx,pr=parseFloat(style.paddingRight)*sx;
  const ty=(qc.text_overhang_em??.2)*parseFloat(style.fontSize)*sy,tx=qc.text_inner_tolerance_px??1;
  const outside=q=>q.top<box.top+pt-ty||q.bottom>box.bottom-pb+ty||q.left<box.left+pl-tx||q.right>box.right-pr+tx;
  const flags=[];if(top<box.top-.5||bottom>box.bottom+.5||textRanges.some(outside))flags.push('TEXT_OUTSIDE');
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
 // FOLD-01: the first screen fits the actual viewport and spends it on information, not empty stage.
 // Samples a grid over the viewport; a point is covered by information objects (cards, KPI tiles, steps,
 // film carrier/nodes, headings, visible text lines). Reports overflow below/right of the viewport,
 // coverage share and the largest empty axis-aligned rectangle (share of the viewport). A metric, not a verdict.
 function inspectFold(fold=document.querySelector('.kz-fold')||document.body,{content='.kz-card,.kz-kpi,.kz-step,.kz-film-carrier,[data-kz-node],[data-kz-info],h1,h2,.kz-lede,nav,.kz-chart,img:not([alt=""])',cols=64,rows=36}={}){
  const T=g.KZ_TOKENS?.layout?.fold||{},minCoverage=T.min_coverage??.45,maxVoid=T.max_void_ratio??.18,W=innerWidth,H=innerHeight;
  if(!fold||!fold.isConnected)return{status:'NOT_TESTED',reason:'missing fold root'};
  const visible=el=>el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
  // A box only counts when it actually carries information: visible text or a painted graphic. Empty cards and
  // placeholder stages do not raise coverage.
  const sized=el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0;};
  const informative=el=>el.matches('img,canvas,svg')||!!el.innerText?.trim()||[...el.querySelectorAll('img,canvas,svg')].some(x=>visible(x)&&sized(x));
  const rects=[],overflow=[];let skipped=0;
  for(const el of fold.querySelectorAll(content)){
   if(!visible(el))continue;const r=el.getBoundingClientRect();if(!r.width||!r.height)continue;
   if(!informative(el)){skipped++;continue;}
   rects.push(r);
   // A card cut by the viewport edge is not "fully shown" even when its last text line still fits.
   if(r.bottom>H+1||r.right>W+1)overflow.push({text:'('+(el.className||el.tagName.toLowerCase())+')',rect:r.toJSON()});
  }
  const walker=document.createTreeWalker(fold,NodeFilter.SHOW_TEXT);let node;
  while(node=walker.nextNode()){
   const p=node.parentElement;if(!node.textContent.trim()||!p||p.closest('script,style,.notes,[hidden]')||!visible(p))continue;
   const range=document.createRange();range.selectNodeContents(node);
   for(const q of range.getClientRects()){if(!q.width||!q.height)continue;rects.push(q);if(q.bottom>H+1||q.right>W+1)overflow.push({text:node.textContent.trim().slice(0,24),rect:q.toJSON()});}
  }
  const foldRect=fold.getBoundingClientRect();
  if(foldRect.bottom>H+1)overflow.unshift({text:'(fold root)',rect:foldRect.toJSON()});
  const grid=[];let covered=0;
  for(let j=0;j<rows;j++){const row=[];for(let i=0;i<cols;i++){const x=(i+.5)*W/cols,y=(j+.5)*H/rows,hit=rects.some(r=>x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom);row.push(hit);if(hit)covered++;}grid.push(row);}
  // Largest all-empty rectangle by the histogram method.
  const heights=new Array(cols).fill(0);let largest=0;
  for(let j=0;j<rows;j++){
   for(let i=0;i<cols;i++)heights[i]=grid[j][i]?0:heights[i]+1;
   const stack=[];for(let i=0;i<=cols;i++){const h=i<cols?heights[i]:0;while(stack.length&&heights[stack.at(-1)]>=h){const top=stack.pop(),width=stack.length?i-stack.at(-1)-1:i;largest=Math.max(largest,heights[top]*width);}stack.push(i);}
  }
  const coverage=covered/(cols*rows),voidRatio=largest/(cols*rows),flags=[];
  if(overflow.length)flags.push('FOLD_OVERFLOW');if(coverage<minCoverage)flags.push('LOW_COVERAGE');if(voidRatio>maxVoid)flags.push('LARGE_VOID');
  return{status:flags.length?'FAIL':'PASS',viewport:[W,H],coverage:+coverage.toFixed(3),voidRatio:+voidRatio.toFixed(3),thresholds:{minCoverage,maxVoid},flags,emptyBoxes:skipped,overflow:overflow.slice(0,12)};
 }
 // 03 孤字行：段落/列表项的末行只有一个汉字（可带标点）。按实际渲染行（Range 行框）判定，不按字符数估算。
 function inspectOrphans(root=document.body,{selector='p,li,h1,h2,h3,td,th,.kz-kpi-label,.kz-film-caption,[data-kz-role="body"]'}={}){
  const cjk=/[\u3400-\u9fff\uf900-\ufaff]/,punct=/[\s，。、；：！？）》」』”’…—·,.;:!?)\]]/;const found=[],splits=[];
  const words=typeof Intl.Segmenter==='function'?new Intl.Segmenter('zh-CN',{granularity:'word'}):null;
  for(const el of root.querySelectorAll(selector)){
   if(!el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})||el.querySelector(selector))continue;
   // A rendered line is a vertical band; a smaller inline run (unit, <small>) whose centre falls inside the band
   // belongs to the same line even though its glyph top differs. `at` is the line's first offset in the element text.
   // `full` is the element text with a newline at each <br> or block boundary, so segmentation never joins across them.
   const lines=[],walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);let node,full='',cut=false;
   while(node=walker.nextNode()){if(node.nodeType===1){if(node.tagName==='BR'||!getComputedStyle(node).display.startsWith('inline'))cut=true;continue;}
    if(cut&&full){full+='\n';}cut=false;const text=node.textContent,offset=full.length;full+=text;
    for(let i=0;i<text.length;i++){const r=document.createRange();r.setStart(node,i);r.setEnd(node,i+1);const q=r.getClientRects()[0];if(!q||!q.width)continue;const c=(q.top+q.bottom)/2;let line=lines.find(l=>c>=l.top&&c<=l.bottom);if(!line)lines.push(line={top:q.top,bottom:q.bottom,text:'',at:offset+i});line.text+=text[i];}}
   if(lines.length<2)continue;lines.sort((a,b)=>a.top-b.top);const last=lines.at(-1).text,core=[...last].filter(c=>!punct.test(c));
   if(core.length===1&&cjk.test(core[0]))found.push({text:el.textContent.trim().slice(0,40),lastLine:last,tag:el.tagName.toLowerCase()});
   // A wrap inside a Chinese word (中心记|录) reads as a broken term even when no line is a lone character.
   if(words)for(const s of words.segment(full)){if(!s.isWordLike||s.segment.length<2||!cjk.test(s.segment))continue;if(lines.slice(1).some(l=>l.at>s.index&&l.at<s.index+s.segment.length))splits.push({text:el.textContent.trim().slice(0,40),word:s.segment,tag:el.tagName.toLowerCase()});}
  }
  return{status:found.length?'FAIL':splits.length?'WARN':'PASS',orphans:found,splits};
 }
 // PPT body region (13 BODY-01): vertical span of its direct children over the region height against
 // layout.content_span_target. Below the floor the page floats in a band; full-height presets read 1.
 function inspectBodySpan(body=document.querySelector('.kz-body')){
  const target=g.KZ_TOKENS?.layout?.content_span_target||[.7,.92];if(!body)return{status:'N/A',span:null,target};
  const b=body.getBoundingClientRect(),rs=[...body.children].filter(c=>c.checkVisibility({checkVisibilityCSS:true})).map(c=>c.getBoundingClientRect()).filter(r=>r.height>0);
  if(!rs.length||!b.height)return{status:'N/A',span:null,target};
  const span=(Math.max(...rs.map(r=>r.bottom))-Math.min(...rs.map(r=>r.top)))/b.height;
  return{status:span<target[0]?'WARN':'PASS',span:+span.toFixed(3),target};
 }
 // 02 LG-02: a coloured, thin mark hugging one edge of a card-like box (anything with a fill, border or shadow).
 // Four ways to draw one: a single coloured border side, an edge pseudo-element, a sharp one-sided inset
 // shadow, or a child element along the edge. Lengths are compared with the edge; sizes in logical px.
 function inspectEdgeBars(root=document.body){
  const T=Object.assign({hug_px:4,max_thickness_px:12,neutral_saturation_max:.18,alpha_min:.3,warn_ratio:.2,forbid_ratio:.5},g.KZ_TOKENS?.glass?.edge_bar);
  const un=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--kz-un'))||1,hug=T.hug_px*un,thin=T.max_thickness_px*un;
  const rgba=s=>{const m=String(s).match(/rgba?\(([^)]+)\)/);if(!m)return null;const v=m[1].split(/[,\s/]+/).filter(Boolean).map(parseFloat);return[v[0],v[1],v[2],v.length>3?v[3]:1];};
  const colours=s=>[...String(s).matchAll(/rgba?\([^)]+\)/g)].map(m=>rgba(m[0]));
  const coloured=c=>{if(!c)return false;const mx=Math.max(c[0],c[1],c[2]),mn=Math.min(c[0],c[1],c[2]);return c[3]>=T.alpha_min&&mx>0&&(mx-mn)/mx>T.neutral_saturation_max;};
  const paint=st=>coloured(rgba(st.backgroundColor))||colours(st.backgroundImage).some(coloured);
  const boxy=(el,st)=>{const r=el.getBoundingClientRect();if(r.width<40||r.height<24||el===document.body||el===document.documentElement||el.matches('.slide,.deck,.kz-body,.kz-optical-field,.kz-fold,svg *'))return false;
   return el.matches('.kz-card,.kz-kpi,.kz-step,.kz-demo,.kz-dialog')||(rgba(st.backgroundColor)?.[3]>.05)||st.backgroundImage!=='none'||st.boxShadow!=='none'||['Top','Right','Bottom','Left'].some(s=>parseFloat(st['border'+s+'Width'])>0);};
  const out=[],level=r=>r>=T.forbid_ratio?'fail':r>=T.warn_ratio?'warn':null,name=el=>el.id?'#'+el.id:el.tagName.toLowerCase()+(el.classList.length?'.'+[...el.classList].slice(0,2).join('.'):'');
  // a thin coloured rect inside the card box, near one edge → which edge and how much of it
  const along=(R,q,detail,kind,card)=>{const w=q.right-q.left,h=q.bottom-q.top;if(w<=0||h<=0)return;let side=null,ratio=0;
   if(w<=thin&&h>w){if(Math.abs(q.left-R.left)<=hug)side='left';else if(Math.abs(R.right-q.right)<=hug)side='right';ratio=h/R.height;}
   else if(h<=thin&&w>h){if(Math.abs(q.top-R.top)<=hug)side='top';else if(Math.abs(R.bottom-q.bottom)<=hug)side='bottom';ratio=w/R.width;}
   const lv=side&&level(ratio);if(lv)out.push({card:name(card),side,kind,detail,ratio:+ratio.toFixed(2),level:lv});};
  for(const card of root.querySelectorAll('*')){
   const st=getComputedStyle(card);if(!card.checkVisibility?.({checkOpacity:true,checkVisibilityCSS:true})||!boxy(card,st))continue;
   const R=card.getBoundingClientRect(),sides=['Top','Right','Bottom','Left'].map(s=>({s:s.toLowerCase(),w:parseFloat(st['border'+s+'Width'])||0,c:st['border'+s+'Color']}));
   for(const b of sides){if(b.w<1.5||!coloured(rgba(b.c)))continue;if(sides.every(o=>Math.abs(o.w-b.w)<.5&&o.c===b.c))continue; // an even frame is a state, not a bar
    out.push({card:name(card),side:b.s,kind:'border',detail:`${b.w}px ${b.c}`,ratio:1,level:'fail'});}
   for(const part of String(st.boxShadow).split(/,(?![^(]*\))/)){if(!/inset/.test(part))continue;const c=rgba(part),n=part.replace(/rgba?\([^)]+\)/,'').match(/-?[\d.]+px/g)?.map(parseFloat)||[];const[x=0,y=0,blur=0,spread=0]=n;
    if(coloured(c)&&blur<=4&&spread<=0&&Math.max(Math.abs(x),Math.abs(y))>=1.5&&(x===0||y===0))out.push({card:name(card),side:x>0?'left':x<0?'right':y>0?'top':'bottom',kind:'inset-shadow',detail:part.trim(),ratio:1,level:'fail'});}
   for(const pseudo of['::before','::after']){const p=getComputedStyle(card,pseudo);if(p.content==='none'||p.display==='none'||!paint(p))continue;
    const w=parseFloat(p.width),h=parseFloat(p.height);if(!Number.isFinite(w)||!Number.isFinite(h))continue;const px=v=>v==='auto'?null:parseFloat(v);
    const l=px(p.left),t=px(p.top),r=px(p.right),b=px(p.bottom),x0=l!=null?R.left+l:r!=null?R.right-r-w:R.left,y0=t!=null?R.top+t:b!=null?R.bottom-b-h:R.top;
    along(R,{left:x0,top:y0,right:x0+w,bottom:y0+h},pseudo,'pseudo',card);}
   for(const child of card.children){const cs=getComputedStyle(child);if(child.closest('svg')||!paint(cs)||!child.checkVisibility?.({checkOpacity:true,checkVisibilityCSS:true}))continue;along(R,child.getBoundingClientRect(),name(child),'child',card);}
  }
  return{status:out.some(o=>o.level==='fail')?'FAIL':out.length?'WARN':'PASS',bars:out};
 }
 // 13 FOLD-07: information density of every viewport-high window of a scrolling page. Only ink counts: text
 // lines, painted figures (charts, Gantt plots, images, SVG, demo objects) and tables; card boxes do not, so an
 // empty or half-empty card shows up as void. Layout boxes are used (entrance opacity is ignored), so the page
 // need not be scrolled. Windows step by the viewport height; the last one is aligned to the page bottom.
 function inspectScroll(root=document.body,{from=0,cols=48,rows=27}={}){
  const T=Object.assign({min_ink:.2,max_void_ratio:.16},g.KZ_TOKENS?.layout?.dense),sy=scrollY,ink=[];
  const add=r=>{if(r.width>2&&r.height>2)ink.push({l:r.left,r:r.right,t:r.top+sy,b:r.bottom+sy});};
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){const p=n.parentElement;return n.textContent.trim()&&!p.closest('script,style,.notes,[hidden],[aria-hidden="true"],.kz-optical-field')&&p.checkVisibility({checkVisibilityCSS:true})?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;}});
  let n;while(n=walker.nextNode()){const r=document.createRange();r.selectNodeContents(n);for(const q of r.getClientRects())add(q);}
  for(const e of root.querySelectorAll('canvas,img,table,.kz-chart,.kz-gantt-plot,svg:not(.kz-optical-field svg),[data-kz-obj]'))if(e.checkVisibility({checkVisibilityCSS:true})&&!e.closest('[aria-hidden="true"]:not(.kz-film-links)'))add(e.getBoundingClientRect());
  // the measured page ends at the last content above the page footer (the footer strip is not reading content)
  const foot=[...root.querySelectorAll('footer')].map(f=>f.getBoundingClientRect().top+sy),end=foot.length?Math.min(...foot):Infinity;
  const H=Math.min(Math.max(document.documentElement.scrollHeight,root.scrollHeight),Math.max(...ink.filter(q=>q.t<end).map(q=>q.b),innerHeight)),W=innerWidth,vh=innerHeight,tops=[];
  for(let y=from;y<H-vh;y+=vh)tops.push(y);tops.push(Math.max(from,H-vh));
  const windows=[...new Set(tops)].map(top=>{
   const grid=[];let hit=0;
   // a cell is ink when any ink box overlaps it (a centre sample misses text lines thinner than a cell)
   for(let r=0;r<rows;r++){const row=[];const y0=top+r*vh/rows,y1=y0+vh/rows;for(let c=0;c<cols;c++){const x0=c*W/cols,x1=x0+W/cols,on=ink.some(q=>q.l<x1&&q.r>x0&&q.t<y1&&q.b>y0);row.push(on);if(on)hit++;}grid.push(row);}
   const h=Array(cols).fill(0);let best=0;
   for(let r=0;r<rows;r++){for(let c=0;c<cols;c++)h[c]=grid[r][c]?0:h[c]+1;const st=[];for(let c=0;c<=cols;c++){const v=c<cols?h[c]:0;let s=c;while(st.length&&st.at(-1)[1]>=v){const[i,hv]=st.pop();best=Math.max(best,hv*(c-i));s=i;}st.push([s,v]);}}
   const w={top:Math.round(top),ink:+(hit/(cols*rows)).toFixed(3),void:+(best/(cols*rows)).toFixed(3)};
   w.flags=[...(w.ink<T.min_ink?['LOW_INK']:[]),...(w.void>T.max_void_ratio?['VOID']:[])];return w;});
  return{status:windows.some(w=>w.flags.length)?'WARN':'PASS',height:H,viewport:[W,vh],thresholds:{min_ink:T.min_ink,max_void_ratio:T.max_void_ratio},windows};
 }
 g.KZLayoutQC={inspectCard,inspectTextBounds,inspectFold,inspectOrphans,inspectBodySpan,inspectEdgeBars,inspectScroll,inspect(root=document){return [...root.querySelectorAll('.kz-card')].filter(e=>e.getBoundingClientRect().height>0&&e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).map(e=>inspectCard(e));}};
})(window);
