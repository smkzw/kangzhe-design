"""Catch fixed PPT role drift without treating web typography as PPT."""
from pathlib import Path
import json,sys,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from qc_plan import validate
class PPTRoleSizes(unittest.TestCase):
 def codes(self,track,role,size):
  p=json.loads((R/'agent/fixtures/page-plan.valid.json').read_text());p['track']=track
  if track!='pptx':
   p['target_viewports']=[[1280,720],[2560,1080]]
   p['pages'][0]['motion_objects']=[{'id':'a','role':'card','enter':'fade','exit':'fade','hover':'tilt','ambient':'none'}]
  e=p['pages'][0]['elements'][0];e.update(role=role,font_px=size)
  return {f['code'] for f in validate(p) if f['level']=='error'}
 def test_card_title_20_cannot_pass_fixed_24(self):
  for track in ['pptx','htmlppt']:
   with self.subTest(track=track):self.assertIn('PPT-ROLE-TYPE',self.codes(track,'card_title',20))
 def test_body_page_title_30_cannot_pass_fixed_32(self):
  for track in ['pptx','htmlppt']:
   with self.subTest(track=track):self.assertIn('PPT-ROLE-TYPE',self.codes(track,'page_title',30))
 def test_footer_16_cannot_pass_fixed_18(self):
  for track in ['pptx','htmlppt']:
   with self.subTest(track=track):self.assertIn('PPT-ROLE-TYPE',self.codes(track,'footer',16))
 def test_token_roles_pass(self):
  for track in ['pptx','htmlppt']:
   for role,size in [('card_title',24),('page_title',32),('footer',18)]:
    with self.subTest(track=track,role=role):self.assertEqual(self.codes(track,role,size),set())
 def test_web_card_title_not_forced_to_ppt_24(self):
  for track in ['site','stream']:
   with self.subTest(track=track):self.assertNotIn('PPT-ROLE-TYPE',self.codes(track,'card_title',22))
 def test_legible_chart_labels_remain_minimum_not_exact(self):
  self.assertEqual(self.codes('pptx','chart_label',18),set())
if __name__=='__main__':unittest.main()
