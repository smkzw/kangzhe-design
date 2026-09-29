from pathlib import Path
import sys,json,copy,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from qc_plan import validate
from hero_layout import layout
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
 def test_site_not_forced_to_slide_master(self):
  p=self.page();p['track']='site';p['target_viewports']=[[1280,720],[1440,900],[1920,1080],[2560,1080]];p['pages'][0].pop('hero_layout_id');p['pages'][0]['elements']=[];p['pages'][0]['motion_objects']=[{'id':'scene','role':'film','enter':'fade','exit':'fade','hover':'none','ambient':'film'}];self.assertEqual(self.errors(p),set())
if __name__=='__main__':unittest.main()
