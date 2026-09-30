"""Track-scoped typography: preserve PPT profiles, permit declared web adaptation."""
from pathlib import Path
import json,sys,unittest,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from qc_plan import validate
class ResponsiveProfiles(unittest.TestCase):
 def plan(self,track='site',profile='responsive',size=18):
  p=json.loads((R/'agent/fixtures/page-plan.valid.json').read_text());p['track']=track
  if track=='site':p['target_viewports']=[[1280,720],[1440,900],[1920,1080],[2560,1080]]
  elif track!='pptx':p['target_viewports']=[[1280,720],[2560,1080]]
  page=p['pages'][0];page['body_profile']=profile
  for e in page['elements']:e['font_px']=size
  if track!='pptx':page['motion_objects']=[{'id':'a','role':'card','enter':'fade','exit':'fade','hover':'tilt','ambient':'none'}]
  return p
 def codes(self,p):return {x['code'] for x in validate(p) if x['level']=='error'}
 def test_site_explicit_responsive_18(self):self.assertEqual(self.codes(self.plan()),set())
 def test_stream_explicit_responsive_18(self):self.assertEqual(self.codes(self.plan('stream')),set())
 def test_pptx_responsive_forbidden(self):self.assertIn('SCHEMA',self.codes(self.plan('pptx')))
 def test_htmlppt_responsive_forbidden(self):self.assertIn('SCHEMA',self.codes(self.plan('htmlppt')))
 def test_site_standard_does_not_silently_mean_18(self):self.assertIn('BODY-PROFILE',self.codes(self.plan(profile='standard')))
 def test_responsive_cannot_drop_floor(self):self.assertIn('FONT-FLOOR',self.codes(self.plan(size=15)))
 def test_responsive_cannot_mix_body_sizes(self):
  p=self.plan();p['pages'][0]['elements'][1]['font_px']=20;self.assertIn('TYPE-UNIFORM',self.codes(p))
 def test_responsive_cannot_mix_line_heights(self):
  p=self.plan();p['pages'][0]['elements'][1]['line_height']=1.6;self.assertIn('TYPE-UNIFORM',self.codes(p))
if __name__=='__main__':unittest.main()
