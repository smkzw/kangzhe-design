"""Regression cases for independently demonstrated preflight bypasses."""
from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
from PIL import Image
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from qc_plan import validate
class A04Gates(unittest.TestCase):
 def setUp(self):self.p=json.loads((R/'agent/fixtures/page-plan.valid.json').read_text())
 def codes(self,p=None,m=None,root=None):return {x['code'] for x in validate(p or self.p,m,root) if x['level']=='error'}
 def test_omitted_revision_cannot_bypass_layout(self):
  self.p.pop('contract_revision');self.p['pages'][0]['cards'][0].pop('layout_mode');self.assertIn('SCHEMA',self.codes())
 def test_obsolete_revision_requires_migration(self):
  self.p['contract_revision']='A03';self.assertIn('SCHEMA',self.codes())
 def test_html_missing_motion_rejected(self):
  self.p['track']='htmlppt';self.assertIn('SCHEMA',self.codes())
 def test_placeholder_does_not_cover_real_card(self):
  self.p['track']='htmlppt';self.p['pages'][0]['motion_objects']=[{'id':'placeholder','role':'card','enter':'fade','exit':'fade','hover':'tilt','ambient':'none'}];self.assertIn('MOTION-MAP',self.codes())
 def test_film_every_phase_needs_claim_and_explanation(self):
  s=json.loads((R/'schemas/film-plan.schema.json').read_text());p=json.loads((R/'examples/film-plan.json').read_text());p['states'][2].pop('source_claim_ids');self.assertTrue(list(Draft202012Validator(s).iter_errors(p)))
 def test_film_does_not_advertise_nonexistent_api(self):
  s=json.loads((R/'schemas/film-plan.schema.json').read_text());p=json.loads((R/'examples/film-plan.json').read_text());p['lifecycle_api']=['pause','resume','seek','replay','static_summary'];self.assertTrue(list(Draft202012Validator(s).iter_errors(p)))
 def asset(self,root):
  f=root/'bg.png';Image.new('RGB',(2560,1088),'white').save(f)
  return {'schema_version':'6.0','assets':[{'id':'body-field-01','origin':'generated','file':'bg.png','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'tool_receipt':'synthetic fixture; no production generation claim','requested_size':[2560,1088],'actual_size':[2560,1088],'renditions':[{'viewport':[2560,1080],'crop':[0,4,2560,1080],'fit':'cover','protected_regions':[],'subject_rects':[],'evidence':['synthetic fixture']}],'review':{'bare':'pass','composite':'pass','reviewer':'test fixture','evidence':['synthetic fixture']}}]}
 def test_actual_file_pixels_not_prompt_size(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);m=self.asset(root);m['assets'][0]['actual_size']=[3840,2160];self.assertIn('ASSET-PIXELS',self.codes(m=m,root=root))
 def test_16_9_source_is_not_ultrawide_generation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);m=self.asset(root);m['assets'][0]['actual_size']=[2560,1440];self.assertIn('IMAGE-ULTRAWIDE',self.codes(m=m))
 def test_stretched_rendition_fails(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);m=self.asset(root);m['assets'][0]['renditions'][0]['crop']=[0,0,1920,1080];self.assertIn('IMAGE-STRETCH',self.codes(m=m,root=root))
 def test_valid_geometric_asset_still_not_visual_certificate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.assertEqual(self.codes(m=self.asset(root),root=root),set())
if __name__=='__main__':unittest.main()
