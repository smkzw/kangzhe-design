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
 // DEMO-03 / TYPE-04: text of one object drawn over text of another (a demo stage squeezed below its capacity, a label on
 // a label). Objects are the direct children of each scope (default: demo canvases); line boxes of visible text
 // (effective opacity ≥ minOpacity) are compared pairwise across objects; an overlap counts when both sides exceed `min` px.
 function inspectOverlaps(root=document,{scope='.kz-demo-canvas',minOpacity=.5,min=3}={}){
  const out=[];let scopes=0;
  for(const sc of root.querySelectorAll(scope)){
   // a stage on a slide that is not showing (deck pages stay in the DOM) is not drawn
   if(!sc.getBoundingClientRect().height||!sc.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;scopes++;const lines=[];
   const walker=document.createTreeWalker(sc,NodeFilter.SHOW_TEXT);let node;
   while(node=walker.nextNode()){
    if(!node.textContent.trim())continue;let el=node.parentElement,obj=el,op=1,hidden=false;
    for(;el&&el!==sc;el=el.parentElement){const st=getComputedStyle(el);op*=Number(st.opacity);if(st.display==='none'||st.visibility==='hidden')hidden=true;obj=el;}
    if(hidden||op<minOpacity)continue;
    const r=document.createRange();r.selectNodeContents(node);
    for(const b of r.getClientRects())if(b.width>1&&b.height>1)lines.push({obj,text:node.textContent.trim().slice(0,24),b});
   }
   for(let i=0;i<lines.length;i++)for(let j=i+1;j<lines.length;j++){const A=lines[i],B=lines[j];if(A.obj===B.obj)continue;
    const w=Math.min(A.b.right,B.b.right)-Math.max(A.b.left,B.b.left),h=Math.min(A.b.bottom,B.b.bottom)-Math.max(A.b.top,B.b.top);
    if(w>min&&h>min)out.push({scope:sc.closest('[id]')?.id||scope,a:A.text,b:B.text,w:Math.round(w),h:Math.round(h)});}
  }
  return{status:!scopes?'EMPTY':out.length?'FAIL':'PASS',scopes,overlaps:out};
 }
 // Legibility floor as rendered: a template diagram (SVG, viewBox `meet`) squeezed into a narrow card draws its text
 // at a fraction of its font-size. Rendered size = computed font-size × the SVG's screen scale (HTML text: computed
 // font-size). `min` is a legibility floor in screen px, not the role contract (03 TYPE-01); canvas charts not covered.
 function inspectTextFloor(root=document.body,{min=11}={}){
  void document.documentElement.offsetHeight; // flush layout first: getScreenCTM can return the pre-resize scale
  const small=[];let n=0,low=Infinity;const seen=new Set();
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node;
  while(node=walker.nextNode()){const el=node.parentElement;if(!el||!node.textContent.trim()||seen.has(el)||el.closest('script,style,.notes,[hidden]'))continue;seen.add(el);
   if(!el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})||!el.getClientRects().length)continue;
   let px=parseFloat(getComputedStyle(el).fontSize);
   if(el.closest('svg')&&el.getScreenCTM){const m=el.getScreenCTM();if(m)px*=Math.hypot(m.a,m.b);}
   if(px<1)continue; // font-size 0 hides text on purpose (icon fonts, counters)
   n++;low=Math.min(low,px);if(px<min-.05)small.push({text:el.textContent.trim().slice(0,24),px:+px.toFixed(1),svg:!!el.closest('svg')});}
  return{status:!n?'EMPTY':small.length?'FAIL':'PASS',min,texts:n,smallest:n?+low.toFixed(1):null,small:small.slice(0,40),count:small.length};
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
  // The fixed site header (13 WIDE-01) sits outside .kz-fold but is part of the first screen, as the old in-fold head was.
  const head=document.querySelector('.kz-site-head'),roots=head&&!fold.contains(head)&&visible(head)?[fold,head]:[fold];
  for(const el of roots.flatMap(r=>[...r.querySelectorAll(content)])){
   if(!visible(el))continue;const r=el.getBoundingClientRect();if(!r.width||!r.height)continue;
   if(!informative(el)){skipped++;continue;}
   rects.push(r);
   // A card cut by the viewport edge is not "fully shown" even when its last text line still fits.
   if(r.bottom>H+1||r.right>W+1)overflow.push({text:'('+(el.className||el.tagName.toLowerCase())+')',rect:r.toJSON()});
  }
  for(const root of roots){const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node;
  while(node=walker.nextNode()){
   const p=node.parentElement;if(!node.textContent.trim()||!p||p.closest('script,style,.notes,[hidden]')||!visible(p))continue;
   const range=document.createRange();range.selectNodeContents(node);
   for(const q of range.getClientRects()){if(!q.width||!q.height)continue;rects.push(q);if(q.bottom>H+1||q.right>W+1)overflow.push({text:node.textContent.trim().slice(0,24),rect:q.toJSON()});}
  }}
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
    if(node.parentElement.closest('svg'))continue; // SVG <text> never wraps: its separate rows are not line breaks
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
  // a thin coloured box hugging one edge of the card, from inside or from outside, running along it → edge and share
  const along=(R,q,detail,kind,card)=>{const w=q.right-q.left,h=q.bottom-q.top;if(w<=0||h<=0)return;let side=null,run=0,len=0,edge=1;
   if(w<=thin&&h>w){if(Math.min(Math.abs(q.left-R.left),Math.abs(q.right-R.left))<=hug)side='left';else if(Math.min(Math.abs(R.right-q.right),Math.abs(R.right-q.left))<=hug)side='right';run=Math.min(q.bottom,R.bottom)-Math.max(q.top,R.top);len=h;edge=R.height;}
   else if(h<=thin&&w>h){if(Math.min(Math.abs(q.top-R.top),Math.abs(q.bottom-R.top))<=hug)side='top';else if(Math.min(Math.abs(R.bottom-q.bottom),Math.abs(R.bottom-q.top))<=hug)side='bottom';run=Math.min(q.right,R.right)-Math.max(q.left,R.left);len=w;edge=R.width;}
   if(!side||run<=0||run<.6*len)return;const ratio=run/edge,lv=level(ratio);if(lv)out.push({card:name(card),side,kind,detail,ratio:+ratio.toFixed(2),level:lv});};
  // background layers: a coloured gradient layer sized as a strip (background-size), or a gradient whose coloured
  // stops make a strip at one end ("linear-gradient(90deg,#f90 0 4px,transparent 4px)")
  const top=v=>{const out=[];let d=0,cur='';for(const ch of String(v)){if(ch==='(')d++;if(ch===')')d--;if(ch===','&&!d){out.push(cur);cur='';}else cur+=ch;}out.push(cur);return out;}; // split at top-level commas
  const layers=st=>{const imgs=top(st.backgroundImage),sizes=String(st.backgroundSize).split(','),pos=String(st.backgroundPosition).split(',');return imgs.map((im,i)=>({im:im.trim(),size:(sizes[i]||sizes[0]||'').trim(),pos:(pos[i]||pos[0]||'').trim()}));};
  const stripOf=(R,L)=>{if(!/gradient\(/.test(L.im)||!colours(L.im).some(coloured))return null;const [sw,sh]=L.size.split(/\s+/);const px=(v,full)=>v==null||v==='auto'?full:v.endsWith('%')?full*parseFloat(v)/100:parseFloat(v);
   const w=px(sw,R.width),h=px(sh==null?sw:sh,R.height);if(L.size&&L.size!=='auto'&&L.size!=='auto auto'&&(w<=thin||h<=thin)){const [px_,py_]=L.pos.split(/\s+/);const off=(v,full,sz)=>v==null?0:v.endsWith('%')?(full-sz)*parseFloat(v)/100:parseFloat(v)||0;const x=R.left+off(px_,R.width,w),y=R.top+off(py_,R.height,h);return{left:x,top:y,right:x+w,bottom:y+h};}
   const m=L.im.match(/linear-gradient\((?:(-?[\d.]+)deg|to (\w+))?/);const ang=m?.[1]!=null?((+m[1])%360+360)%360:{right:90,left:270,bottom:180,top:0}[m?.[2]]??180;if(ang%90)return null;
   const axis=ang===90||ang===270?R.width:R.height;const stops=[...L.im.matchAll(/(rgba?\([^)]+\))((?:\s+-?[\d.]+(?:px|%))*)/g)].map(x=>({c:rgba(x[1]),at:(x[2].trim().split(/\s+/).filter(Boolean)).map(v=>v.endsWith('%')?axis*parseFloat(v)/100:parseFloat(v))}));
   if(stops.length<2)return null;const first=stops.findIndex(z=>!coloured(z.c));if(first<=0)return null;const edgeAt=Math.max(...stops[first-1].at.concat(stops[first].at.slice(0,1)).filter(Number.isFinite));if(!(edgeAt>0&&edgeAt<=thin))return null;
   const fromStart=ang===90||ang===180;const t=edgeAt;return ang===90?{left:R.left,top:R.top,right:R.left+t,bottom:R.bottom}:ang===270?{left:R.right-t,top:R.top,right:R.right,bottom:R.bottom}:ang===180?{left:R.left,top:R.top,right:R.right,bottom:R.top+t}:fromStart?null:{left:R.left,top:R.bottom-t,right:R.right,bottom:R.bottom};};
  for(const card of root.querySelectorAll('*')){
   const st=getComputedStyle(card);if(!card.checkVisibility?.({checkOpacity:true,checkVisibilityCSS:true})||!boxy(card,st))continue;
   const R=card.getBoundingClientRect(),sides=['Top','Right','Bottom','Left'].map(s=>({s:s.toLowerCase(),w:parseFloat(st['border'+s+'Width'])||0,c:st['border'+s+'Color']}));
   for(const b of sides){if(b.w<1.5||!coloured(rgba(b.c)))continue;if(sides.every(o=>Math.abs(o.w-b.w)<.5&&o.c===b.c))continue; // an even frame is a state, not a bar
    out.push({card:name(card),side:b.s,kind:'border',detail:`${b.w}px ${b.c}`,ratio:1,level:'fail'});}
   if(st.borderImageSource&&st.borderImageSource!=='none'&&colours(st.borderImageSource).some(coloured)&&!sides.every(o=>Math.abs(o.w-sides[0].w)<.5))out.push({card:name(card),side:'uneven',kind:'border-image',detail:st.borderImageSource.slice(0,60),ratio:1,level:'fail'});
   for(const part of top(st.boxShadow)){const c=rgba(part),n=part.replace(/rgba?\([^)]+\)/,'').match(/-?[\d.]+px/g)?.map(parseFloat)||[];const[x=0,y=0,blur=0,spread=0]=n;
    if(!coloured(c)||!(x===0||y===0)||Math.max(Math.abs(x),Math.abs(y))<1.5)continue;
    if(/inset/.test(part)&&blur<=4&&spread<=0)out.push({card:name(card),side:x>0?'left':x<0?'right':y>0?'top':'bottom',kind:'inset-shadow',detail:part.trim(),ratio:1,level:'fail'});
    else if(!/inset/.test(part)&&blur<=2&&spread<=0)out.push({card:name(card),side:x<0?'left':x>0?'right':y<0?'top':'bottom',kind:'outer-shadow',detail:part.trim(),ratio:1,level:'fail'});}
   for(const L of layers(st)){const q=stripOf(R,L);if(q)along(R,q,L.im.slice(0,48),'gradient',card);}
   for(const pseudo of['::before','::after']){const p=getComputedStyle(card,pseudo);if(p.content==='none'||p.display==='none'||!paint(p))continue;
    const w=parseFloat(p.width),h=parseFloat(p.height);if(!Number.isFinite(w)||!Number.isFinite(h))continue;const px=v=>v==='auto'?null:parseFloat(v);
    const l=px(p.left),t=px(p.top),r=px(p.right),b=px(p.bottom),x0=l!=null?R.left+l:r!=null?R.right-r-w:R.left,y0=t!=null?R.top+t:b!=null?R.bottom-b-h:R.top;
    along(R,{left:x0,top:y0,right:x0+w,bottom:y0+h},pseudo,'pseudo',card);}
   // every descendant near an edge: painted boxes, and inline SVG rect/line/path/polygon (charts sit in their own
   // measurement surfaces and are skipped)
   const near=q=>q.left<=R.left+thin+hug||q.right>=R.right-thin-hug||q.top<=R.top+thin+hug||q.bottom>=R.bottom-thin-hug;
   for(const d of card.querySelectorAll('*')){const q=d.getBoundingClientRect();if(!q.width||!q.height||!near(q))continue;
    if(d.closest('.kz-chart,[data-kz-chart],canvas'))continue;
    if(d instanceof SVGElement){if(!/^(rect|line|path|polygon|polyline)$/.test(d.tagName))continue;const ds=getComputedStyle(d);
     const f=coloured(rgba(ds.fill))&&parseFloat(ds.fillOpacity||1)*parseFloat(ds.opacity||1)>=T.alpha_min,k=coloured(rgba(ds.stroke))&&parseFloat(ds.strokeWidth)*un<=thin*1.0;if(f||k)along(R,q,name(d),'svg',card);continue;}
    const cs=getComputedStyle(d);if(!paint(cs)||!d.checkVisibility?.({checkOpacity:true,checkVisibilityCSS:true}))continue;along(R,q,name(d),'child',card);}
  }
  return{status:out.some(o=>o.level==='fail')?'FAIL':out.length?'WARN':'PASS',bars:out};
 }
 // 13 FOLD-07: information density of every viewport-high window of a scrolling page. Only ink counts: text
 // lines, painted figures (charts, Gantt plots, images, SVG, demo objects) and tables; card boxes do not, so an
 // empty or half-empty card shows up as void. Layout boxes are used (entrance opacity is ignored), so the page
 // need not be scrolled. Windows step by the viewport height; the last one is aligned to the page bottom.
 // Sticky blocks other than the site header (the stream chapter rail) are drawn where they actually stick in each
 // window, within their parent; measured at their static position only, every later window would show their column
 // as empty although the reader sees the rail there.
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
  const sticky=[...root.querySelectorAll('*')].filter(e=>!e.closest('.kz-site-head')&&getComputedStyle(e).position==='sticky'&&e.checkVisibility()).map(e=>{
   const r=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect(),box={l:r.left,r:r.right,t:r.top+sy,b:r.bottom+sy};
   return{box,top:parseFloat(getComputedStyle(e).top)||0,end:p.bottom+sy,own:ink.filter(q=>q.l>=box.l-1&&q.r<=box.r+1&&q.t>=box.t-1&&q.b<=box.b+1)};});
  const inkAt=top=>{const out=[...ink];for(const k of sticky){const dy=Math.min(top+k.top,k.end-(k.box.b-k.box.t))-k.box.t;if(dy>0)for(const q of k.own)out.push({l:q.l,r:q.r,t:q.t+dy,b:q.b+dy});}return out;};
  const windows=[...new Set(tops)].map(top=>{
   const grid=[];let hit=0;const ink=inkAt(top);
   // a cell is ink when any ink box overlaps it (a centre sample misses text lines thinner than a cell)
   for(let r=0;r<rows;r++){const row=[];const y0=top+r*vh/rows,y1=y0+vh/rows;for(let c=0;c<cols;c++){const x0=c*W/cols,x1=x0+W/cols,on=ink.some(q=>q.l<x1&&q.r>x0&&q.t<y1&&q.b>y0);row.push(on);if(on)hit++;}grid.push(row);}
   const h=Array(cols).fill(0);let best=0;
   for(let r=0;r<rows;r++){for(let c=0;c<cols;c++)h[c]=grid[r][c]?0:h[c]+1;const st=[];for(let c=0;c<=cols;c++){const v=c<cols?h[c]:0;let s=c;while(st.length&&st.at(-1)[1]>=v){const[i,hv]=st.pop();best=Math.max(best,hv*(c-i));s=i;}st.push([s,v]);}}
   const w={top:Math.round(top),ink:+(hit/(cols*rows)).toFixed(3),void:+(best/(cols*rows)).toFixed(3)};
   w.flags=[...(w.ink<T.min_ink?['LOW_INK']:[]),...(w.void>T.max_void_ratio?['VOID']:[])];return w;});
  return{status:windows.some(w=>w.flags.length)?'WARN':'PASS',height:H,viewport:[W,vh],thresholds:{min_ink:T.min_ink,max_void_ratio:T.max_void_ratio},windows};
 }
 // 13 WIDE-01: how much of the viewport width the information uses (cards, KPIs, charts, headings, text blocks).
 // span = (rightmost − leftmost edge of visible information objects) / viewport width; ≥ tokens.wide.content_width_min.
 // 13 WIDE-01 width use: horizontal span of the information boxes (cards, KPIs, charts, tables, film carriers, steps,
 // stream rail and paragraphs) as a share of the viewport. Header chrome and boxes at least 90% of the viewport wide are
 // containers, not content, so they are skipped: a centred column inside a full-width wrapper must not read as full span.
 function inspectWidth(root=document.body,{content='.kz-card,.kz-kpi,.kz-chart,.kz-film-carrier,.kz-step,table,.kz-stream-rail,.kz-stream-main p,h1,h2,.kz-lede',container=.9}={}){
  const W=document.documentElement.clientWidth,min=(g.KZ_TOKENS?.wide?.content_width_min)??.85;let l=Infinity,r=-Infinity,n=0,skipped=0;
  for(const e of root.querySelectorAll(content)){if(e.closest('.kz-site-head,.kz-fold-head'))continue;const q=e.getBoundingClientRect();if(q.width<20||q.height<8||q.bottom<0)continue;
   if(q.width>=container*W){skipped++;continue;}n++;l=Math.min(l,q.left);r=Math.max(r,q.right);}
  const span=r>l?(r-l)/W:0;return{status:span>=min?'PASS':'FAIL',span:+span.toFixed(3),left:Math.round(l),right:Math.round(r),viewport:W,min,boxes:n,containersSkipped:skipped};
 }
 // 03 COPY-10 sibling balance: cards side by side in one row share a height, so their content spans should be close
 // (tokens.layout.balance; the PPTX solver reports the same as CARD-BALANCE in the template receipt).
 function inspectSiblings(root=document.body,{cards='.kz-card,.kzl-card',budget=(g.KZ_TOKENS||{}).layout?.balance}={}){
  const B=budget||{spread_max:.3,fill_min:.6},rows=new Map(),out=[];
  for(const c of root.querySelectorAll(cards)){if(!c.checkVisibility?.({checkOpacity:false,checkVisibilityCSS:true}))continue;const r=c.getBoundingClientRect();if(r.height<40)continue;
   const key=c.parentElement;if(!rows.has(key))rows.set(key,[]);rows.get(key).push({c,r});}
  for(const [parent,list] of rows){const byTop=new Map();for(const x of list){const k=Math.round(x.r.top/4);(byTop.get(k)||byTop.set(k,[]).get(k)).push(x);}
   for(const group of byTop.values()){if(group.length<2)continue;const spans=group.map(x=>{const m=inspectCard(x.c);return m.span??null;}).filter(v=>v!=null);
    if(spans.length<2)continue;const mx=Math.max(...spans),mn=Math.min(...spans);
    if(mx-mn>B.spread_max&&mn<B.fill_min)out.push({row:parent.id||parent.className.split(' ')[0],spans:spans.map(v=>+v.toFixed(2)),cards:group.map(x=>x.c.id||x.c.className.split(' ')[0])});}}
  return{status:out.length?'REVIEW':'PASS',rows:out};
 }
 // 03 COPY-04 inline emphasis per card and free paragraph, the same rules as tools/kz_layouts/emphasis.py.
 function inspectEmphasis(root=document.body,{units='.kz-card,.kzl-card,[data-kz-unit]',paragraphs='p,li',budget=(g.KZ_TOKENS||{}).emphasis?.budget}={}){
  const B=budget||{text_heavy_chars:40,unit_min:1,unit_max:3,item_max:1,paragraph_max:2,page_risk_max:2,page_highlight_max:1,page_underline_max:3,run_chars_max:16,run_share_max:.5,share_min_units:24,stack_max:2};
  const EMPH='b,strong,u,mark,.kz-risk',HEAD='h1,h2,h3,h4,.kz-card-title,.kzl-card-title,.kz-takeaway,.kzl-takeaway,.is-item_title';
  const n=s=>s.replace(/\s/g,'').length, w=s=>[...s.replace(/\s/g,'')].reduce((a,c)=>a+(/[\u1100-\u115F\u2E80-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6]/.test(c)?1:.5),0);
  const vis=e=>e.getBoundingClientRect().height>0&&e.checkVisibility({checkOpacity:false,checkVisibilityCSS:true});
  const marks=e=>{const s=new Set();for(let x=e;x&&x!==root;x=x.parentElement){const t=x.tagName;if(t==='B'||t==='STRONG')s.add('bold');if(t==='U')s.add('underline');if(t==='MARK')s.add('highlight');if(x.classList?.contains('kz-risk'))s.add('risk');}return s;};
  // groups: outermost emphasis elements, adjacent ones (nothing but whitespace between) merged
  const groupsIn=p=>{const out=[];let prev=null;const walker=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);for(let t=walker.nextNode();t;t=walker.nextNode()){const st=marks(t.parentElement);if(!t.textContent.trim()){continue;}if(st.size){if(prev&&prev.open)prev.text+=t.textContent,st.forEach(x=>prev.st.add(x));else{prev={text:t.textContent,st,open:true};out.push(prev);}}else if(prev)prev.open=false;}return out;};
  const found=[],page={risk:0,highlight:0,underline:0};
  const audit=(id,kind,paras,items)=>{let gu=0,chars=0;paras.forEach((p,i)=>{const plain=p.textContent,gs=groupsIn(p);chars+=n(plain);gu+=gs.length;
    if(items.has(i)&&gs.length>B.item_max)found.push({code:'EMPHASIS-DENSE',where:id,message:`一条要点 ${gs.length} 组强调：${plain.trim().slice(0,24)}`});
    gs.forEach(gr=>{const k=w(gr.text),whole=w(plain);if(k>B.run_chars_max||(whole>=B.share_min_units&&k>B.run_share_max*whole))found.push({code:'EMPHASIS-LONG',where:id,message:`“${gr.text.trim().slice(0,20)}” ${k} 字宽`});
      const m=new Set(gr.st);if(m.has('risk'))m.delete('bold');if(m.size>B.stack_max||(gr.st.has('risk')&&gr.st.has('highlight')))found.push({code:'EMPHASIS-STACK',where:id,message:[...m].join('+')});
      ['risk','highlight','underline'].forEach(k2=>{if(gr.st.has(k2))page[k2]++;});});});
   if(kind==='heading')return;
   const limit=kind==='card'?Math.max(B.unit_max,Math.ceil(items.size/2)):B.paragraph_max;
   if(gu>limit)found.push({code:'EMPHASIS-DENSE',where:id,message:`${gu} 组强调（上限 ${limit}）`});
   if(chars>=B.text_heavy_chars&&gu<B.unit_min&&!paras[0]?.closest('[data-kz-emphasis="not_applicable"]'))found.push({code:'EMPHASIS-MISSING',where:id,message:`${chars} 字没有强调`});};
  const cards=[...root.querySelectorAll(units)].filter(vis).filter(c=>!c.parentElement?.closest(units));
  const leafs=c=>[...c.querySelectorAll(paragraphs)].filter(vis).filter(p=>!p.closest(HEAD)&&!p.querySelector(paragraphs)&&n(p.textContent));
  const heads=[];
  cards.forEach((c,i)=>{const ps=leafs(c);const items=new Set(ps.map((p,j)=>p.tagName==='LI'?j:-1).filter(j=>j>=0));if(ps.length)audit(c.id||`${c.className.split(' ')[0]}#${i+1}`,'card',ps,items);heads.push(...c.querySelectorAll(HEAD));});
  [...root.querySelectorAll(paragraphs)].filter(vis).filter(p=>!p.closest(units)&&!p.closest(HEAD)&&!p.querySelector(paragraphs)&&n(p.textContent)).forEach((p,i)=>audit(`p#${i+1}`,'paragraph',[p],new Set()));
  heads.push(...[...root.querySelectorAll(HEAD)].filter(h=>!h.closest(units)));
  if(heads.length)audit('headings','heading',heads.filter(vis),new Set());
  [['risk','EMPHASIS-RED','page_risk_max'],['highlight','EMPHASIS-MARK','page_highlight_max'],['underline','EMPHASIS-ULINE','page_underline_max']].forEach(([k,code,cap])=>{if(page[k]>B[cap])found.push({code,where:'page',message:`${page[k]} 处（上限 ${B[cap]}）`});});
  return {findings:found,page};
 }
 g.KZLayoutQC={inspectCard,inspectTextBounds,inspectOverlaps,inspectTextFloor,inspectFold,inspectOrphans,inspectBodySpan,inspectEdgeBars,inspectScroll,inspectEmphasis,inspectSiblings,inspectWidth,inspect(root=document){return [...root.querySelectorAll('.kz-card')].filter(e=>e.getBoundingClientRect().height>0&&e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})).map(e=>inspectCard(e));}};
})(window);
