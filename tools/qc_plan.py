"""Mechanical preflight for KZ sidecar, NOT visual quality certification."""
from pathlib import Path
import argparse,json,re,hashlib
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def intersects(a,b):
 return min(a[0]+a[2],b[0]+b[2])>max(a[0],b[0]) and min(a[1]+a[3],b[1]+b[3])>max(a[1],b[1])
def validate(plan,manifest=None,asset_root=None):
 findings=[]
 def add(code,where,message,level='error'):findings.append(dict(code=code,where=where,message=message,level=level))
 schema=json.loads((ROOT/'schemas/page-plan.schema.json').read_text());tokens=json.loads((ROOT/'tokens/tokens.json').read_text())
 errs=list(Draft202012Validator(schema).iter_errors(plan))
 for e in errs:add('SCHEMA','/'.join(map(str,e.absolute_path)),e.message)
 if errs:return findings
 seen=set();w,h=plan['canvas']
 for p in plan['pages']:
  pid=p['id']
  if pid in seen:add('ID',pid,'重复页面 id')
  seen.add(pid)
  if re.search(r'[：:—–]|\s-\s',p['title']):add('TITLE',pid,'页面标题不应有冒号或破折号')
  if len(p['title'])>24:add('TITLE-REVIEW',pid,'长标题需要语言审阅；不是自动截短', 'review')
  byrole={}
  for el in p['elements']:
   role=el['role'];font=el['font_px'];byrole.setdefault(role,set()).add((round(font,3),round(el['line_height'],3)))
   floor=tokens['type_px']['reference'] if role=='reference' else tokens['type_px']['body_floor']
   if font<floor-.01:add('FONT-FLOOR',pid+'/'+el['id'],'字号低于该角色最低值')
   if role=='body':
    expected=tokens['type_px']['body_compact' if p['body_profile']=='compact' else 'body']
    if abs(font-expected)>.01:add('BODY-PROFILE',pid+'/'+el['id'],'正文未使用整页统一 profile')
  for role,styles in byrole.items():
   if role in ['body','card_title','chart_label'] and len(styles)>1:add('TYPE-UNIFORM',pid+'/'+role,'同页同角色字号或行距不一致')
  for source in p['sources']:
   if source['visible'] and source['kind'] not in ['scientific_paper','guideline','consensus','guidance']:add('CITATION',pid+'/'+source['id'],'该资料类型不添加观众可见来源脚注')
  image=p['image']
  if image['mode']=='global_procedural_optical_field':
   if plan['track'] not in ['site','stream']:add('IMAGE-REQUIRED',pid,'PPTX/HTML-PPT 无程序化光场免生图豁免')
   if not image.get('procedural_evidence'):add('IMAGE-EXEMPTION',pid,'光场豁免缺少实现证据')
  elif not image.get('asset_id'):add('IMAGE-MAP',pid,'缺少生成图资产映射')
  for a in image.get('subject_rects',[]):
   if a[2]<=0 or a[3]<=0 or a[0]<0 or a[1]<0 or a[0]+a[2]>w or a[1]+a[3]>h:add('IMAGE-BOUNDS',pid,'图像主体区域越界')
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
    a=assets.get(p['image'].get('asset_id'))
    if not a:add('ASSET-MISSING',p['id'],'资产映射不存在');continue
    if a['origin']!='generated' or not a.get('tool_receipt'):add('GEN-RECEIPT',p['id'],'需要真实生成工具回执；占位声明不算生成')
    if a['review']['bare']!='pass' or a['review']['composite']!='pass' or not a['review']['evidence']:add('IMAGE-QC',p['id'],'裸图和合成图均须有审阅证据')
    if asset_root:
     root=Path(asset_root).resolve();file=(root/a['file']).resolve()
     if not file.is_relative_to(root) or not file.is_file():add('ASSET-FILE',p['id'],'资产文件不存在或越界')
     elif hashlib.sha256(file.read_bytes()).hexdigest()!=a['sha256']:add('ASSET-HASH',p['id'],'资产哈希不一致')
 else:add('ASSET-NOT-CHECKED','project','仅完成生成前计划检查；未验证实际生成与合成审阅','pending')
 return findings
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('plan',type=Path);ap.add_argument('--manifest',type=Path);ap.add_argument('--asset-root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
 try:
  f=validate(json.loads(a.plan.read_text()),json.loads(a.manifest.read_text()) if a.manifest else None,a.asset_root);result={'scope':'mechanical preflight only','findings':f,'errors':sum(x['level']=='error' for x in f),'visual_review':'NOT_PERFORMED'};text=json.dumps(result,ensure_ascii=False,indent=2);print(text)
  if a.out:a.out.write_text(text,encoding='utf-8')
  raise SystemExit(1 if result['errors'] else 0)
 except (OSError,ValueError) as e:raise SystemExit(str(e))
