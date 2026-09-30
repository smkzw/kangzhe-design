"""Mechanical preflight for KZ sidecar, NOT visual quality certification."""
from pathlib import Path
import argparse,json,re,hashlib
from PIL import Image
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def intersects(a,b):
 return min(a[0]+a[2],b[0]+b[2])>max(a[0],b[0]) and min(a[1]+a[3],b[1]+b[3])>max(a[1],b[1])
def in_bounds(rect,w,h):
 return rect[2]>0 and rect[3]>0 and rect[0]>=0 and rect[1]>=0 and rect[0]+rect[2]<=w and rect[1]+rect[3]<=h
def validate(plan,manifest=None,asset_root=None):
 findings=[]
 def add(code,where,message,level='error'):findings.append(dict(code=code,where=where,message=message,level=level))
 schema=json.loads((ROOT/'schemas/page-plan.schema.json').read_text());tokens=json.loads((ROOT/'tokens/tokens.json').read_text())
 errs=list(Draft202012Validator(schema).iter_errors(plan))
 for e in errs:add('SCHEMA','/'.join(map(str,e.absolute_path)),e.message)
 if errs:return findings
 seen=set();w,h=plan['canvas']
 targets={tuple(v) for v in plan['target_viewports']}
 if plan['track']=='site' and not {tuple(v) for v in tokens['site_viewports']}.issubset(targets):add('VIEWPORT-COVERAGE','project','站点缺少规定的桌面宽屏验收视口')
 if plan['track'] in ['htmlppt','site','stream'] and not any(vw/vh>2 for vw,vh in targets):add('VIEWPORT-ULTRAWIDE','project','HTML交付计划缺少超宽视口，不能只测16:9')
 for p in plan['pages']:
  pid=p['id']
  if pid in seen:add('ID',pid,'重复页面 id')
  seen.add(pid)
  if re.search(r'[：:—–]|\s-\s',p['title']):add('TITLE',pid,'页面标题不应有冒号或破折号')
  if len(p['title'])>24:add('TITLE-REVIEW',pid,'长标题需要语言审阅；不是自动截短', 'review')
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
   for r in expected:
    if r not in actual:add('HERO-ROLE',pid,'缺少固定角色 '+r)
   if p['kind']=='toc':
    labels=[e for e in p['elements'] if e['role']=='toc_label'];n=len(labels)
    if not 1<=n<=6:add('HERO-CAPACITY',pid,'目录每页1至6项，超过必须拆页')
    else:
     from hero_layout import layout
     _,blocks,_=layout('toc',{'title':'目录','items':[{'title':'项','description':'说明'}]*n})
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
   if role in ['cover_title','hero_subtitle','hero_meta','toc_title','toc_number','toc_label','toc_description','section_number','section_title','ending_title'] and abs(font-tokens['type_px'][role])>.01:add('HERO-TYPE',pid+'/'+el['id'],'非正文页必须使用固定角色字号，不允许缩字')
   if plan['track'] in ['pptx','htmlppt'] and role in ['cover_title','hero_subtitle','hero_meta','toc_title','toc_number','toc_label','toc_description','section_number','section_title','ending_title'] and abs(el['line_height']-1.25)>.001:add('HERO-LINEHEIGHT',pid+'/'+el['id'],'固定行高必须为1.25')
   hero=tokens.get('hero_layouts',{}).get(p['kind'])
   anchor={'cover_title':'title','toc_title':'title','section_number':'number','section_title':'title','ending_title':'title','hero_subtitle':'subtitle','hero_meta':'meta'}.get(role)
   if plan['track'] in ['pptx','htmlppt'] and hero and anchor:
    expected_rect=hero.get(anchor)
    if expected_rect and (not el.get('rect') or any(abs(a-b)>2 for a,b in zip(el['rect'],expected_rect))):add('HERO-GEOMETRY',pid+'/'+el['id'],'固定文字框位置/尺寸与版式 token 不符')
   if role=='body':
    expected=tokens['type_px']['body_compact' if p['body_profile']=='compact' else 'body']
    if abs(font-expected)>.01:add('BODY-PROFILE',pid+'/'+el['id'],'正文未使用整页统一 profile')
  for role,styles in byrole.items():
   if role in ['body','card_title','chart_label'] and len(styles)>1:add('TYPE-UNIFORM',pid+'/'+role,'同页同角色字号或行距不一致')
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
  if image['mode']=='global_procedural_optical_field':
   if plan['track'] not in ['site','stream']:add('IMAGE-REQUIRED',pid,'PPTX/HTML-PPT 无程序化光场免生图豁免')
   if not image.get('procedural_evidence'):add('IMAGE-EXEMPTION',pid,'光场豁免缺少实现证据')
  elif not image.get('asset_id'):add('IMAGE-MAP',pid,'缺少生成图资产映射')
  for a in image.get('subject_rects',[]):
   if not in_bounds(a,w,h):add('IMAGE-BOUNDS',pid,'图像主体区域越界')
   for region in p['protected_regions']:
    b=region['rect'];m=max(tokens['image']['safety_pad_px'],region.get('motion_margin',0));b=[b[0]-m,b[1]-m,b[2]+2*m,b[3]+2*m]
    if intersects(a,b):add('IMAGE-COLLISION',pid+'/'+region['id'],'预期图像主体侵入保护区')
  if p.get('takeaway') and p['takeaway']['font_px']<tokens['type_px']['takeaway']:add('TAKEAWAY',pid,'强调句字号过小')
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
        rect=region['rect'];pad=max(tokens['image']['safety_pad_px'],region.get('motion_margin',0))*unit
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
      except (OSError,ValueError):add('ASSET-DECODE',p['id'],'图像不可解码')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('plan',type=Path);ap.add_argument('--manifest',type=Path);ap.add_argument('--asset-root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
 try:
  f=validate(json.loads(a.plan.read_text()),json.loads(a.manifest.read_text()) if a.manifest else None,a.asset_root);result={'scope':'mechanical preflight only','findings':f,'errors':sum(x['level']=='error' for x in f),'visual_review':'NOT_PERFORMED'};text=json.dumps(result,ensure_ascii=False,indent=2);print(text)
  if a.out:a.out.write_text(text,encoding='utf-8')
  raise SystemExit(1 if result['errors'] else 0)
 except (OSError,ValueError) as e:raise SystemExit(str(e))
