"""Mechanical preflight for KZ sidecar, NOT visual quality certification."""
from pathlib import Path
import argparse,json,re,hashlib
from PIL import Image,ImageStat
from jsonschema import Draft202012Validator
import sys;sys.path.insert(0,str(Path(__file__).resolve().parent))
from kz_titles import title_findings
ROOT=Path(__file__).resolve().parents[1]
def intersects(a,b):
 return min(a[0]+a[2],b[0]+b[2])>max(a[0],b[0]) and min(a[1]+a[3],b[1]+b[3])>max(a[1],b[1])
def in_bounds(rect,w,h):
 return rect[2]>0 and rect[3]>0 and rect[0]>=0 and rect[1]>=0 and rect[0]+rect[2]<=w and rect[1]+rect[3]<=h
def pad_for(region,tokens):
 # 04 IMG-02: static regions pad safety_pad_px; regions that move (declared motion_margin) pad at least motion_safety_pad_px.
 m=region.get('motion_margin',0)
 return max(tokens['image']['safety_pad_px'],m,tokens['image']['motion_safety_pad_px'] if m else 0)
# 14 FLAG-08: the flagship content-page layout library
FLAG_TEMPLATES=['flag-cols','flag-flow','flag-stage','flag-chart','flag-gantt','flag-cycle','flag-safety','flag-safety-dumbbell','flag-program','flag-program-strip','flag-exposure','flag-exposure-plan','flag-trialflow','flag-landscape','flag-efficacy','flag-soa']
FLAG_PPTX_ONLY=['flag-safety','flag-safety-dumbbell','flag-program','flag-program-strip','flag-exposure','flag-exposure-plan','flag-trialflow','flag-landscape','flag-efficacy','flag-soa']   # 14 FLAG-12: PPTX language L1; HTML uses the safety/program stages

def flagship_set():
    """14 FLAG-03: id -> asset of assets/backgrounds/flagship/default-set.json."""
    f=ROOT/'assets/backgrounds/flagship/default-set.json'
    return {a['id']:a for a in json.loads(f.read_text(encoding='utf-8'))['assets']} if f.is_file() else {}

def default_set():
 # 04 IMG-07: the shipped fallback backgrounds; every hash of the same picture (shipped JPEG, original PNG, WebP
 # transcodes) identifies it, so a deck cannot pass the fallback set off as a generated image.
 d=json.loads((ROOT/'assets/backgrounds/default-set.json').read_text())
 # 8.0: every style, both renditions (16:9, 21:9), and the generated source of an A2 picture
 hs=lambda a:[a['sha256'],a.get('source_sha256'),(a.get('provenance') or {}).get('source_sha256'),(a.get('provenance') or {}).get('capture_sha256'),
              *[x['sha256'] for x in a.get('aliases',[])+a.get('renditions',[])]]
 return {a['id']:a for a in d['assets']},{h for a in d['assets'] for h in hs(a) if h}
def warm_share(im,style):
 # 04 IMG-07: share of the coloured pixels whose hue is in the Kangzhe orange-yellow band (None: almost no colour)
 small=im.convert('HSV');small.thumbnail((style['sample_px'],style['sample_px']))
 px=list(small.getdata());lo,hi=style['warm_hue_deg']
 col=[h*360/255 for h,s,v in px if s/255>style['saturation_min'] and v/255>style['value_min']]
 if len(col)<style['colored_share_min']*len(px):return None
 return sum(lo<=h<=hi for h in col)/len(col)
def validate(plan,manifest=None,asset_root=None):
 findings=[]
 def add(code,where,message,level='error'):findings.append(dict(code=code,where=where,message=message,level=level))
 schema=json.loads((ROOT/'schemas/page-plan.schema.json').read_text());tokens=json.loads((ROOT/'tokens/tokens.json').read_text())
 errs=list(Draft202012Validator(schema).iter_errors(plan))
 for e in errs:add('SCHEMA','/'.join(map(str,e.absolute_path)),e.message)
 if errs:return findings
 seen=set();w,h=plan['canvas']
 # 14: the flagship route keeps the floors and the language rules but has its own type contract, hero forms and light field.
 flagship=plan.get('route','regular')=='flagship';FT=tokens['flagship']['type_px']
 FLAG_ROLE={'cover_title':'cover_title','hero_subtitle':'cover_lede','hero_meta':'cover_meta','toc_title':'toc_title','toc_number':'toc_numeral','toc_label':'toc_card_title','toc_description':'toc_card_desc','section_number':'section_numeral','section_title':'section_title','ending_title':'ending_title','page_title':'page_title','card_title':'card_title','footer':'foot'}
 FLAG_SET=flagship_set()
 if flagship and plan['track'] not in ['pptx','htmlppt']:add('ROUTE-TRACK','project','旗舰路线只用于 PPTX 与 HTML-PPT')
 # 04 IMG-07: regular PPTX/HTML-PPT decks pass the image-capability gate (detect, then ask the user) before assets.
 cap=plan.get('image_capability');DEFAULT,DEFAULT_HASHES=default_set()
 if not flagship and plan['track'] in ['pptx','htmlppt'] and not cap:add('IMAGE-CAPABILITY','project','PPTX/HTML-PPT 常规路线须先过生图能力闸门：检测生图能力并询问用户（04 IMG-07）')
 if cap and (flagship or plan['track'] not in ['pptx','htmlppt']):add('IMAGE-CAPABILITY','project','生图能力闸门只用于 PPTX/HTML-PPT 常规路线','warning')
 targets={tuple(v) for v in plan['target_viewports']}
 required=tokens['viewports'].get(plan['track'])
 if required and not {tuple(v) for v in required}.issubset(targets):add('VIEWPORT-COVERAGE','project','缺少本轨规定的浏览器可视区验收视口：'+', '.join(f'{a}×{b}' for a,b in required))
 if plan['track'] in ['htmlppt','site','stream'] and not any(vw/vh>2 for vw,vh in targets):add('VIEWPORT-ULTRAWIDE','project','HTML交付计划缺少超宽视口，不能只测16:9')
 for p in plan['pages']:
  pid=p['id']
  if pid in seen:add('ID',pid,'重复页面 id')
  seen.add(pid)
  for lv,code,msg in title_findings(p['title'],p.get('kind')):add(code,pid,msg,'error' if lv=='error' else 'review')
  byrole={}
  if plan['track'] in ['htmlppt','site','stream']:
   motion=p['motion_objects']; ids=[m['id'] for m in motion]
   if len(ids)!=len(set(ids)):add('MOTION-ID',pid,'动态对象 id 重复')
   for c in p['cards']:
    if c['id'] not in ids:add('MOTION-MAP',pid+'/'+c['id'],'卡片未列入逐对象动态清单')
   add('MOTION-RUNTIME-PENDING',pid,'计划只验证清单；还须交付DOM对象、挂载和真实轨迹逐项对账','pending')
  if plan['track'] in ['pptx','htmlppt'] and p['kind'] in ['cover','toc','section','ending']:
   expected={'cover':['cover_title'],'toc':['toc_title','toc_label'],'section':['section_number','section_title'],'ending':['ending_title']}[p['kind']]
   actual={e['role'] for e in p['elements']}
   # 14 FLAG-04: flagship toc and section pages carry the page-progress footer; covers and endings never do
   if (not flagship or p['kind'] in ['cover','ending']) and ('footer' in actual or any(r['role'] in ['header','footer'] for r in p['protected_regions'])):add('HERO-CHROME',pid,'旗舰封面与尾页不带页脚和进度段（14 FLAG-04）' if flagship else '封面、目录、章节和尾页不得显示正文页眉页脚或页码')
   for r in expected:
    if r not in actual:add('HERO-ROLE',pid,'缺少固定角色 '+r)
   if p['kind']=='ending':
    for e in p['elements']:
     if e['role']=='ending_title' and 'text' in e and e['text'].strip()!=tokens['hero_layouts']['ending']['text']:add('ENDING-TEXT',pid,f'尾页结束语固定为“{tokens["hero_layouts"]["ending"]["text"]}”（11 HERO-01）；决定事项、待办与结论放在最后一张正文页')
   if p['kind']=='toc' and flagship:
    if not 2<=len([e for e in p['elements'] if e['role']=='toc_label'])<=tokens['flagship']['max_toc']:add('FLAG-CAPACITY',pid,f'旗舰目录每页 2 至 {tokens["flagship"]["max_toc"]} 章（14 FLAG-07）')
   elif p['kind']=='toc':
    labels=[e for e in p['elements'] if e['role']=='toc_label'];n=len(labels)
    lid=p.get('hero_layout_id') if p.get('hero_layout_id','').startswith('toc-') else 'toc-01'
    tcap=tokens['hero_layouts']['variants'][lid]['max_items'] if lid in tokens['hero_layouts']['variants'] else 6
    if not 1<=n<=tcap:add('HERO-CAPACITY',pid,f'{lid} 每页 1 至 {tcap} 项，超过必须拆页或换版式')
    else:
     from hero_layout import layout
     _,blocks,_=layout('toc',{'title':'目录','items':[{'title':'项','description':'说明'}]*n,'layout':lid})
     for role in ['toc_number','toc_label','toc_description']:
      els=[e for e in p['elements'] if e['role']==role];want=[b for b in blocks if b['role']==role]
      if role=='toc_description':
       # Descriptions are optional per card; actual slots must still be unique.
       occupied=set()
       for e in els:
        matches=[i for i,b in enumerate(want) if e.get('rect') and all(abs(a-c)<=2 for a,c in zip(e['rect'],b['rect']))]
        if not matches:add('HERO-GEOMETRY',pid,'目录固定网格位置不符 '+role)
        elif matches[0] in occupied:add('HERO-ROLE',pid,'目录说明槽重复')
        else:occupied.add(matches[0])
      elif len(els)!=len(want):add('HERO-ROLE',pid,'目录角色数量不一致 '+role)
      elif any(not e.get('rect') or any(abs(a-b)>2 for a,b in zip(e['rect'],b['rect'])) for e,b in zip(els,want)):add('HERO-GEOMETRY',pid,'目录固定网格位置不符 '+role)
  for el in p['elements']:
   role=el['role'];font=el['font_px'];byrole.setdefault(role,set()).add((round(font,3),round(el['line_height'],3)))
   floor=tokens['type_px']['reference'] if role=='reference' else tokens['type_px']['body_floor']
   if font<floor-.01:add('FONT-FLOOR',pid+'/'+el['id'],'字号低于该角色最低值')
   if role=='secondary' and abs(font-tokens['type_px']['secondary'])>.01:add('SECONDARY-TYPE',pid+'/'+el['id'],'辅助文字固定用 type_px.secondary（03 TYPE-01）')
   if flagship:
    if role in FLAG_ROLE and abs(font-FT[FLAG_ROLE[role]])>.01:add('FLAG-TYPE',pid+'/'+el['id'],'旗舰角色字号须取 tokens.flagship.type_px（14 FLAG-07）')
   elif role in ['cover_title','hero_subtitle','hero_meta','toc_title','toc_number','toc_label','toc_description','section_number','section_title','ending_title'] and abs(font-tokens['type_px'][role])>.01:add('HERO-TYPE',pid+'/'+el['id'],'非正文页必须使用固定角色字号，不允许缩字')
   if not flagship and plan['track'] in ['pptx','htmlppt'] and role in ['cover_title','hero_subtitle','hero_meta','toc_title','toc_number','toc_label','toc_description','section_number','section_title','ending_title'] and abs(el['line_height']-1.25)>.001:add('HERO-LINEHEIGHT',pid+'/'+el['id'],'固定行高必须为1.25')
   hero=tokens.get('hero_layouts',{}).get(p['kind'])
   anchor={'cover_title':'title','toc_title':'title','section_number':'number','section_title':'title','ending_title':'title','hero_subtitle':'subtitle','hero_meta':'meta'}.get(role)
   if not flagship and plan['track'] in ['pptx','htmlppt'] and hero and anchor:
    expected_rect=hero.get(anchor)
    if expected_rect and (not el.get('rect') or any(abs(a-b)>2 for a,b in zip(el['rect'],expected_rect))):add('HERO-GEOMETRY',pid+'/'+el['id'],'固定文字框位置/尺寸与版式 token 不符')
   if not flagship and plan['track'] in ['pptx','htmlppt'] and role in ['page_title','card_title','footer'] and abs(font-tokens['type_px'][role])>.01:add('PPT-ROLE-TYPE',pid+'/'+el['id'],'正文页标题、卡标题和页脚必须使用固定角色字号')
   if role=='body' and p['body_profile']!='responsive':
    expected=FT['body'] if flagship else tokens['type_px']['body_compact' if p['body_profile']=='compact' else 'body']
    if abs(font-expected)>.01:add('BODY-PROFILE',pid+'/'+el['id'],'正文未使用整页统一 profile')
  # 14 FLAG-05: flagship cards are white paper cards; the regular route keeps the glass family (02 LG-01)
  for c in p['cards']:
   if flagship!=(c['material']=='flagship_paper'):add('FLAG-CARD',pid+'/'+c['id'],'旗舰卡片 material 写 flagship_paper（14 FLAG-05）' if flagship else 'flagship_paper 只用于旗舰路线')
  for role,styles in byrole.items():
   if role in ['body','card_title','chart_label','secondary'] and len(styles)>1:add('TYPE-UNIFORM',pid+'/'+role,'同页同角色字号或行距不一致')
  for source in p['sources']:
   if source['visible'] and source['kind'] not in ['scientific_paper','guideline','consensus','guidance']:add('CITATION',pid+'/'+source['id'],'该资料类型不添加观众可见来源脚注')
  for region in p['protected_regions']:
   if not in_bounds(region['rect'],w,h):add('PROTECTION-BOUNDS',pid+'/'+region['id'],'保护区尺寸须为正且位于画布内')
  image=p['image']
  bindings=set()
  if image.get('viewport_assets') and image['mode']!='generated':add('IMAGE-VIEWPORT-MODE',pid,'按视口资产选择只用于真实生成图，不用于光场豁免')
  for binding in image.get('viewport_assets',[]):
   viewport=tuple(binding['viewport'])
   if viewport not in targets:add('IMAGE-VIEWPORT-UNKNOWN',pid,'资产选择视口未列入交付合同')
   if viewport in bindings:add('IMAGE-VIEWPORT-DUPLICATE',pid,'同一视口不得选择多个资产')
   bindings.add(viewport)
  region_viewports=set()
  for mapping in image.get('viewport_regions',[]):
   viewport=tuple(mapping['viewport'])
   if viewport not in targets:add('IMAGE-VIEWPORT-UNKNOWN',pid,'保护区映射视口未列入交付合同')
   if viewport in region_viewports:add('IMAGE-PROTECTION-DUPLICATE',pid,'视口保护区映射重复')
   region_viewports.add(viewport)
   ids=[region['id'] for region in mapping['protected_regions']]
   if len(ids)!=len(set(ids)):add('IMAGE-PROTECTION-DUPLICATE',pid,'实际保护区id重复')
   if not {region['id'] for region in p['protected_regions']}.issubset(ids):add('IMAGE-PROTECTION-COVERAGE',pid,'实际视口保护区漏掉页面对象')
   for region in mapping['protected_regions']:
    if not in_bounds(region['rect'],*viewport):add('IMAGE-RENDITION-BOUNDS',pid+'/'+region['id'],'实际视口保护区越界或尺寸非正')
  if cap and image['mode'] in ['generated','default_set'] and image['mode']!=cap['decision']:add('IMAGE-STRATEGY',pid,'页面图像方式与生图能力闸门的结论不一致（04 IMG-07）')
  if image['mode']=='default_set':
   a=DEFAULT.get(image.get('asset_id'))
   if flagship or plan['track'] not in ['pptx','htmlppt']:add('IMAGE-DEFAULT-SET',pid,'缺省背景套只用于 PPTX/HTML-PPT 常规路线')
   elif not a:add('IMAGE-DEFAULT-SET',pid,'asset_id 不在缺省背景套 assets/backgrounds/default-set.json 中')
   elif p['kind'] not in a['page_kinds']:add('IMAGE-DEFAULT-SET',pid,f'缺省背景套的 {a["id"]} 用于 {"/".join(a["page_kinds"])} 页，不用于 {p["kind"]} 页')
  # 14 FLAG-03: flagship pages use the F1 set (cover visual / warm canvas) or, for a theme cover, a generated image
  if flagship and image['mode'] not in ['flagship_set','generated']:add('FLAG-IMAGE',pid,'旗舰背景用旗舰背景套 flagship_set（封面可另生，写 generated）（14 FLAG-03）')
  if flagship and image['mode']=='generated' and p['kind']!='cover':add('FLAG-IMAGE',pid,'旗舰只有封面可以另生主视觉，其余页用 flagship-canvas（14 FLAG-03）')
  if image['mode']=='flagship_set':
   a=FLAG_SET.get(image.get('asset_id'))
   if not flagship:add('FLAG-IMAGE-ROUTE',pid,'旗舰背景套只用于旗舰路线')
   elif not a:add('FLAG-IMAGE',pid,'asset_id 不在 assets/backgrounds/flagship/default-set.json 中')
   elif p['kind'] not in a['page_kinds'] and not (p['kind']=='body' and 'content' in a['page_kinds']):add('FLAG-IMAGE',pid,f'{a["id"]} 用于 {"/".join(a["page_kinds"])} 页，不用于 {p["kind"]} 页')
  if image['mode']=='global_procedural_optical_field':
   if plan['track'] not in ['site','stream']:add('IMAGE-REQUIRED',pid,'PPTX/HTML-PPT 无程序化光场免生图豁免')
   if not image.get('procedural_evidence'):add('IMAGE-EXEMPTION',pid,'光场豁免缺少实现证据')
  elif image['mode']=='generated' and not image.get('asset_id'):add('IMAGE-MAP',pid,'缺少生成图资产映射')
  for a in image.get('subject_rects',[]):
   if not in_bounds(a,w,h):add('IMAGE-BOUNDS',pid,'图像主体区域越界')
   for region in p['protected_regions']:
    b=region['rect'];m=pad_for(region,tokens);b=[b[0]-m,b[1]-m,b[2]+2*m,b[3]+2*m]
    if intersects(a,b):add('IMAGE-COLLISION',pid+'/'+region['id'],'预期图像主体侵入保护区')
  if p.get('takeaway') and p['takeaway']['font_px']<tokens['type_px']['takeaway']:add('TAKEAWAY',pid,'观点句字号过小')
 # 15 DEMO-05/09: demo pages use a demo preset, adjacent demo pages rotate it, process demos show right and wrong cases
 # 15 DEMO-02: adjacent demo pages use different forms; three or more demo pages use at least three forms
 if plan['track']=='htmlppt':
  prev=None;prevk=None;kinds=[]
  for p in plan['pages']:
   d=p.get('demo') or {};pre=p.get('preset','')
   if 'kind' not in d:prev=None;prevk=None;continue
   if d['kind']!='custom':
    kinds.append(d['kind'])
    if d['kind']==prevk:add('DEMO-KIND-REPEAT',p['id'],f'与上一演示页同为 {prevk}；相邻演示页换用同一任务下的另一种形式（15 DEMO-02）')
   prevk=d['kind']
   if not pre.startswith('demo'):add('DEMO-PRESET',p['id'],'演示页须用 demo / demo-mirror / demo-wide / demo-stack 预设之一（15 DEMO-05）')
   elif pre==prev:add('DEMO-PRESET-REPEAT',p['id'],f'与上一演示页重复预设 {pre}；相邻演示页轮换构图（15 DEMO-05）')
   if d['kind'] in ['flow','decision','audit'] and not {'positive','negative','complex_negative'}<=set(d.get('cases',[])):add('DEMO-CASES',p['id'],'流程、判定、核查类演示须含正例、简单反例与复杂反例（15 DEMO-09）')
   prev=pre if pre.startswith('demo') else None
  if len(kinds)>=3 and len(set(kinds))<3:add('DEMO-KIND-MIX','deck',f'{len(kinds)} 个演示页只用了 {len(set(kinds))} 种形式；三页以上至少三种（15 DEMO-02）')
 # 13 BODY-03: neighbouring body pages do not repeat a look; a deck mixes looks; a body page names its template and
 # density so the storyboard (SKILL 开工流程) can show it and offer the other variants of the same family
 if plan['track'] in ['pptx','htmlppt']:
  body=[p for p in plan['pages'] if p['kind'] in ['body','flow_section'] and not p.get('demo',{}).get('kind')]
  if flagship:
   for p in body:
    if p.get('template') and p['template'] not in FLAG_TEMPLATES:add('FLAG-TEMPLATE',p['id'],'旗舰正文页 template 取 14 FLAG-08 的 '+'/'.join(FLAG_TEMPLATES))
    elif p.get('template') in FLAG_PPTX_ONLY and plan['track']!='pptx':add('FLAG-TEMPLATE',p['id'],f'{p["template"]} 是旗舰 PPTX 模板（14 FLAG-12）；HTML-PPT 旗舰用舞台 safety / program / exposure / trialflow / landscape / efficacy / soa（FLAG-06a）')
  # 14 FLAG-06a: stage components come from the catalog, rotate between neighbouring stage pages and mix within a deck
  if flagship:
   cat=tokens['flagship']['stages']['catalog']; stages=[]
   for p in plan['pages']:
    st=p.get('stage')
    if p.get('template')=='flag-stage' and plan['track']=='htmlppt' and not st:add('FLAG-STAGE',p['id'],'flag-stage 版式要写 stage: {component, job}（14 FLAG-06a）')
    if not st:continue
    if plan['track']!='htmlppt':add('FLAG-STAGE',p['id'],'舞台组件只用于 HTML-PPT；PPTX 旗舰用原生图表、形状与卡片组合（14 FLAG-10）');continue
    c=cat.get(st['component'])
    if not c:add('FLAG-STAGE',p['id'],f'舞台组件 {st["component"]} 不在 tokens.flagship.stages.catalog（{"/".join(cat)}）');continue
    if st['job'] not in c['job']:add('FLAG-STAGE',p['id'],f'{st["component"]} 适用 {"/".join(c["job"])}，不用于 {st["job"]}（14 FLAG-06a）')
    stages.append(p)
   for a,b in zip(stages,stages[1:]):
    if a['stage']['component']==b['stage']['component'] and not b.get('continues'):add('FLAG-STAGE-ADJACENT',b['id'],f'与上一张舞台页同用 {b["stage"]["component"]}：换同类内容的另一组件（14 FLAG-06a）')
   if len(stages)>=3 and len({p['stage']['component'] for p in stages})<3:add('FLAG-STAGE-VARIETY','project',f'{len(stages)} 张舞台页只用了 {len({p["stage"]["component"] for p in stages})} 种组件；3 张及以上至少 3 种（14 FLAG-06a）')
   if plan['track']=='htmlppt' and len(body)>=4:
    carriers=[p for p in body if p.get('stage') or p.get('template') in ('flag-chart','flag-gantt','flag-cycle')+tuple(FLAG_PPTX_ONLY)]
    if len(carriers)*3<len(body):add('FLAG-STAGE-MISSING','project',f'{len(body)} 张内容页只有 {len(carriers)} 张舞台或图表页；每 3 张内容页至少 1 张（14 FLAG-06a）','warn')
  elif any(p.get('stage') for p in plan['pages']):add('FLAG-STAGE','project','舞台组件 stage 只用于旗舰路线（14 FLAG-06a）')
  run,prev=0,None
  for p in body:
   t=p.get('template')
   if not t:add('TEMPLATE-MISSING',p['id'],'正文页没有写 template（13 BODY-02/03）：从模板库选版式并写进 page-plan，故事板才能展示和换版式','warn');run,prev=0,None;continue
   same=t==prev and not p.get('continues')
   run=run+1 if same else (run if p.get('continues') and t==prev else 1)
   if same and run>=3:add('TEMPLATE-REPEAT',p['id'],f'{t} 连续用了 {run} 页（上限 2；同一列表分页续排写 continues: true，不计）')
   elif same:add('TEMPLATE-ADJACENT',p['id'],f'与上一页同一版式 {t}：相邻正文页换同族的另一变体（13 BODY-03）','warn')
   prev=t
  used={p.get('template') for p in body if p.get('template')}
  if len(body)>=6 and len(used)<3:add('TEMPLATE-VARIETY','deck',f'{len(body)} 张正文页只用了 {len(used)} 种版式（至少 3 种）')
 if manifest is not None:
  ms=json.loads((ROOT/'schemas/asset-manifest.schema.json').read_text())
  me=list(Draft202012Validator(ms).iter_errors(manifest))
  for e in me:add('ASSET-SCHEMA','/'.join(map(str,e.absolute_path)),e.message)
  if not me:
   assets={a['id']:a for a in manifest['assets']}
   if len(assets)!=len(manifest['assets']):add('ASSET-ID','assets','资产 id 重复')
   for p in plan['pages']:
    if p['image']['mode']!='generated':continue
    choices={tuple(b['viewport']):b['asset_id'] for b in p['image'].get('viewport_assets',[])}
    # The fallback image is shipped even when all target viewports have overrides.
    required={p['image'].get('asset_id'):set()}
    for viewport in targets:required.setdefault(choices.get(viewport,p['image'].get('asset_id')),set()).add(viewport)
    for asset_id,asset_targets in required.items():
     _validate_asset(p,assets.get(asset_id),asset_targets,asset_root,tokens,add,plan['canvas'],plan['track'])
     if assets.get(asset_id,{}).get('sha256') in DEFAULT_HASHES:add('IMAGE-DEFAULT-AS-GENERATED',p['id'],'登记为生成图的资产是缺省背景套；没有生图时 image.mode 写 default_set（04 IMG-07）')
 else:add('ASSET-NOT-CHECKED','project','仅完成生成前计划检查；未验证实际生成与合成审阅','pending')
 return findings

def _validate_asset(p,a,targets,asset_root,tokens,add,canvas,track):
    if not a:add('ASSET-MISSING',p['id'],'资产映射不存在');return
    if a['origin']!='generated' or not a.get('tool_receipt'):add('GEN-RECEIPT',p['id'],'需要真实生成工具回执；占位声明不算生成')
    if a['review']['bare']!='pass' or a['review']['composite']!='pass' or not a['review']['evidence']:add('IMAGE-QC',p['id'],'裸图和合成图均须有审阅证据')
    if a['origin']!='generated':return
    size=a['actual_size']; tol=tokens['image']['aspect_tolerance']
    floor=tokens['image']['hero_min_long_edge_px' if p['kind'] in ['cover','toc','section','ending','hero'] else 'body_min_long_edge_px']
    if max(size)<floor:add('IMAGE-RESOLUTION',p['id'],'源图实际长边不足；不得把重采样算真实生成','warning')
    covered={tuple(r['viewport']) for r in a['renditions']}
    if not targets.issubset(covered):add('IMAGE-RENDITION-MISSING',p['id'],'资产缺少交付视口的裁切/保护区/合成审阅映射')
    if len(covered)!=len(a['renditions']):add('IMAGE-RENDITION-DUPLICATE',p['id'],'同一资产视口映射重复')
    for r in a['renditions']:
     vw,vh=r['viewport'];x,y,cw,ch=r['crop']
     unit=vh/canvas[1] if track in ['pptx','htmlppt'] else 1
     if x<0 or y<0 or cw<=0 or ch<=0 or x+cw>size[0] or y+ch>size[1]:add('IMAGE-CROP',p['id'],'裁切超出源图实际像素')
     elif abs(cw/ch/(vw/vh)-1)>tol:add('IMAGE-STRETCH',p['id'],'裁切与显示比例不符，不允许拉伸或补边')
     if vw/vh>2 and abs(size[0]/size[1]/(vw/vh)-1)>tol:add('IMAGE-ULTRAWIDE',p['id'],'超宽显示缺少比例匹配的真实源图')
     for role in ['protected_regions','subject_rects']:
      for rect in r[role]:
       if not in_bounds(rect,vw,vh):add('IMAGE-RENDITION-BOUNDS',p['id']+'/'+role,'显示坐标区域尺寸须为正且位于视口内')
     for subject in r['subject_rects']:
      for protected in r['protected_regions']:
       pad=tokens['image']['safety_pad_px']*unit
       expanded=[protected[0]-pad,protected[1]-pad,protected[2]+2*pad,protected[3]+2*pad]
       if intersects(subject,expanded):add('IMAGE-RENDITION-COLLISION',p['id'],'实际裁切映射后主体侵入保护区含安全外扩')
     if r['subject_rects'] and tuple(r['viewport']) in targets:
      mapped=next((m['protected_regions'] for m in p['image'].get('viewport_regions',[]) if m['viewport']==r['viewport']),None)
      regions=p['protected_regions'] if r['viewport']==canvas else mapped
      if regions is None:add('IMAGE-PROTECTION-MAP',p['id'],'非基准视口有主体时必须登记实际保护区，不猜测fluid坐标')
      else:
       for region in regions:
        rect=region['rect'];pad=pad_for(region,tokens)*unit
        expanded=[rect[0]-pad,rect[1]-pad,rect[2]+2*pad,rect[3]+2*pad]
        if any(intersects(subject,expanded) for subject in r['subject_rects']):add('IMAGE-RENDITION-COLLISION',p['id']+'/'+region['id'],'主体侵入页面实际保护区含运动安全外扩')
    if not asset_root:add('ASSET-PIXELS-PENDING',p['id'],'没有资产根目录，未从图像文件核验真实像素','pending')
    if asset_root:
     root=Path(asset_root).resolve();file=(root/a['file']).resolve()
     if not file.is_relative_to(root) or not file.is_file():add('ASSET-FILE',p['id'],'资产文件不存在或越界')
     else:
      if hashlib.sha256(file.read_bytes()).hexdigest()!=a['sha256']:add('ASSET-HASH',p['id'],'资产哈希不一致')
      try:
       with Image.open(file) as im:
        if list(im.size)!=size:add('ASSET-PIXELS',p['id'],'实际文件尺寸与清单不一致')
        wash=tokens['image'].get('washout')
        if wash and p['kind'] in ['cover','toc','section','ending','hero']:
         # 04 IMG-01: a washed-out hero has almost no tonal structure. The Kangzhe near-white glass look is mostly
         # bright pixels by design, so brightness share is not the signal; the luminance spread is.
         small=im.convert('L');small.thumbnail((wash['sample_px'],wash['sample_px']));std=ImageStat.Stat(small).stddev[0]
         if std<wash['luminance_std_min']:add('IMAGE-WASHOUT',p['id'],f'主视觉灰度标准差 {std:.1f} 低于 {wash["luminance_std_min"]}，主体不可辨')
        style=tokens['image'].get('style');share=style and warm_share(im,style)
        if share is not None and share<style['warm_share_min']:add('IMAGE-STYLE',p['id'],f'有色像素中暖色（橙黄）只占 {share:.0%}，低于 {style["warm_share_min"]:.0%}，偏离康哲浅色橙黄 liquid glass 风格（04 IMG-07）','warning')
      except (OSError,ValueError):add('ASSET-DECODE',p['id'],'图像不可解码')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('plan',type=Path);ap.add_argument('--manifest',type=Path);ap.add_argument('--asset-root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
 try:
  f=validate(json.loads(a.plan.read_text()),json.loads(a.manifest.read_text()) if a.manifest else None,a.asset_root);result={'scope':'mechanical preflight only','findings':f,'errors':sum(x['level']=='error' for x in f),'visual_review':'NOT_PERFORMED'};text=json.dumps(result,ensure_ascii=False,indent=2);print(text)
  if a.out:a.out.write_text(text,encoding='utf-8')
  raise SystemExit(1 if result['errors'] else 0)
 except (OSError,ValueError) as e:raise SystemExit(str(e))
