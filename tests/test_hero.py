from pathlib import Path
import sys,json,copy,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from qc_plan import validate
from hero_layout import layout,html_fragment
class HeroContracts(unittest.TestCase):
 def page(self):
  t=json.loads((R/'tokens/tokens.json').read_text());rect=t['hero_layouts']['cover']['title']
  return {'schema_version':'6.0','contract_revision':'A04','track':'pptx','canvas':[1280,720],'target_viewports':[[1280,720]],'pages':[{'id':'p1','kind':'cover','title':'汇报示例','hero_layout_id':'cover-01','body_profile':'standard','elements':[{'id':'title','role':'cover_title','font_px':56,'line_height':1.25,'rect':rect}],'protected_regions':[],'image':{'mode':'generated','asset_id':'real'},'sources':[],'cards':[]}]}
 def errors(self,p):return {x['code'] for x in validate(p) if x['level']=='error'}
 def test_valid(self):self.assertEqual(self.errors(self.page()),set())
 def test_small_generic_title_rejected(self):
  p=self.page();p['pages'][0]['elements'][0].update(role='page_title',font_px=32);self.assertIn('HERO-ROLE',self.errors(p))
 def test_shrink_rejected(self):
  p=self.page();p['pages'][0]['elements'][0]['font_px']=32;self.assertIn('HERO-TYPE',self.errors(p))
 def test_position_drift_rejected(self):
  p=self.page();p['pages'][0]['elements'][0]['rect'][0]+=40;self.assertIn('HERO-GEOMETRY',self.errors(p))
 def test_wrong_layout_rejected(self):
  p=self.page();p['pages'][0]['hero_layout_id']='ending-01';self.assertIn('SCHEMA',self.errors(p))
 def test_lineheight_drift_rejected(self):
  p=self.page();p['pages'][0]['elements'][0]['line_height']=1.1;self.assertIn('HERO-LINEHEIGHT',self.errors(p))
 def test_toc_seven_requires_split(self):
  with self.assertRaises(ValueError):layout('toc',{'title':'目录','items':[{'title':'章节'}]*7})
 def toc_plan(self,items):
  p=self.page();q=p['pages'][0];q.update(kind='toc',title='目录',hero_layout_id='toc-01')
  _,blocks,_=layout('toc',{'title':'目录','items':items})
  q['elements']=[dict(id=str(i),role=b['role'],font_px=b['font_px'],line_height=b['line_height'],rect=b['rect']) for i,b in enumerate(blocks)]
  return p
 def test_optional_description_slots_validate_for_mixed_and_full_toc(self):
  for descriptions in [[],[1],[0,2],[0,1,2]]:
   items=[dict(title='章节',**({'description':'真实说明'} if i in descriptions else {})) for i in range(3)]
   with self.subTest(descriptions=descriptions):self.assertEqual(self.errors(self.toc_plan(items)),set())
 def test_description_drift_and_duplicate_rejected(self):
  p=self.toc_plan([{'title':'章节','description':'说明'},{'title':'结果'}])
  e=next(e for e in p['pages'][0]['elements'] if e['role']=='toc_description')
  duplicate=copy.deepcopy(e);duplicate['id']='duplicate';p['pages'][0]['elements'].append(duplicate)
  self.assertIn('HERO-ROLE',self.errors(p))
  p['pages'][0]['elements'].pop();e['rect'][1]+=20
  self.assertIn('HERO-GEOMETRY',self.errors(p))
 def test_empty_description_reading_is_balanced_inside_fixed_card(self):
  _,blocks,cards=layout('toc',{'title':'目录','items':[{'title':'核对','description':None},{'title':'结果','description':'  '}]})
  reading=[b for b in blocks if b['role'] in ['toc_number','toc_label','toc_description']]
  self.assertNotIn('toc_description',{b['role'] for b in reading})
  for x,y,w,h in cards:
   bs=[b['rect'] for b in reading if x<=b['rect'][0]<x+w]
   self.assertEqual(len(bs),2)
   top=min(b[1] for b in bs)-y;bottom=y+h-max(b[1]+b[3] for b in bs)
   self.assertLessEqual(abs(top-bottom)/h,.20)
   self.assertTrue(all(b[0]+b[2]<=x+w and b[1]+b[3]<=y+h for b in bs))
 def test_toc_mixed_description_keeps_common_baseline(self):
  _,blocks,cards=layout('toc',{'title':'目录','items':[{'title':'核对','description':'材料范围'},{'title':'结果'},{'title':'计划'},{'title':'下一章'}]})
  labels=[b for b in blocks if b['role']=='toc_label']
  offsets=[b['rect'][1]-c[1] for b,c in zip(labels,cards)]
  self.assertEqual(offsets[1],offsets[0])
  self.assertEqual(offsets[1],offsets[2])
  self.assertEqual(offsets[3],offsets[1])
  self.assertEqual(sum(b['role']=='toc_description' for b in blocks),1)
 def test_long_chinese_line_rejected_before_fragment_generation(self):
  with self.assertRaises(ValueError):html_fragment('toc',{'title':'目录','items':[{'title':'材料'*40}]},'image.png','logo.svg')
 def test_optional_empty_blocks_omitted_required_title_rejected(self):
  _,blocks,_=layout('cover',{'title':'资料汇报','subtitle':None,'meta':''})
  self.assertEqual([b['role'] for b in blocks],['cover_title'])
  with self.assertRaises(ValueError):layout('cover',{'title':''})
 def test_explicit_card_identity_no_missing_or_duplicate_roles(self):
  _,blocks,cards=layout('toc',{'title':'目录','items':[{'title':'核对','description':'材料'},{'title':'结果'},{'title':'计划'}]})
  self.assertEqual([sum(b.get('card_index')==i for b in blocks) for i in range(len(cards))],[3,2,2])
 def test_html_toc_text_belongs_to_moving_card(self):
  from html.parser import HTMLParser
  class Tree(HTMLParser):
   def __init__(self):super().__init__();self.stack=[];self.reading=[]
   def handle_starttag(self,tag,attrs):
    attrs=dict(attrs)
    if attrs.get('data-hero-role') in ['toc_number','toc_label','toc_description']:self.reading.append(list(self.stack))
    if tag not in ['img','br']:self.stack.append(attrs)
   def handle_endtag(self,tag):
    if self.stack:self.stack.pop()
  tree=Tree();tree.feed(html_fragment('toc',{'title':'目录','items':[{'title':'A&B'}]},'image.png','logo.svg'))
  self.assertEqual(len(tree.reading),2)
  for chain in tree.reading:
   self.assertTrue(any('kz-card' in x.get('class','').split() for x in chain))
   self.assertTrue(any('kz-float' in x.get('class','').split() for x in chain))
   self.assertTrue(any('data-kz-reveal' in x for x in chain))
 def test_nonbody_footer_or_header_chrome_rejected(self):
  for track in ['pptx','htmlppt']:
   for kind in ['cover','toc','section','ending']:
    for role in ['footer','header']:
     p=self.page();p['track']=track;q=p['pages'][0];q.update(kind=kind,hero_layout_id=kind+'-01')
     data={'title':'资料汇报','number':'01','items':[{'title':'材料'}]}
     _,blocks,_=layout(kind,data)
     q['elements']=[dict(id=str(i),role=b['role'],font_px=b['font_px'],line_height=b['line_height'],rect=b['rect'])for i,b in enumerate(blocks)]
     if track=='htmlppt':p['target_viewports']=[[1280,720],[2560,1080]];q['motion_objects']=[dict(id='logo',role='brand-logo',enter='static',exit='static',hover='none',ambient='none')]
     if role=='footer':q['elements'].append(dict(id='page-number',role='footer',font_px=18,line_height=1.25,text='1 / 7'))
     else:q['protected_regions'].append(dict(id='header',role='header',rect=[0,0,100,90],motion_margin=0))
     with self.subTest(track=track,kind=kind,role=role):self.assertIn('HERO-CHROME',self.errors(p))
 def test_site_not_forced_to_slide_master(self):
  p=self.page();p['track']='site';p['target_viewports']=[[1280,720],[1440,900],[1920,1080],[2560,1080]];p['pages'][0].pop('hero_layout_id');p['pages'][0]['elements']=[];p['pages'][0]['motion_objects']=[{'id':'scene','role':'film','enter':'fade','exit':'fade','hover':'none','ambient':'film'}];self.assertEqual(self.errors(p),set())
if __name__=='__main__':unittest.main()
