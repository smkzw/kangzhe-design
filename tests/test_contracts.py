from pathlib import Path
import unittest,json,copy,sys,hashlib,xml.etree.ElementTree as E,tempfile
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from qc_plan import validate
from glass_svg import card
from make_safe_mask import make
from PIL import Image
class Contracts(unittest.TestCase):
 def setUp(self):self.p=json.loads((ROOT/'agent/fixtures/page-plan.valid.json').read_text())
 def errors(self,p):return [x['code'] for x in validate(p) if x['level']=='error']
 def test_valid_preflight_is_not_visual_pass(self):
  self.assertEqual(self.errors(self.p),[]);self.assertTrue(any(x['level']=='pending' for x in validate(self.p)))
 def test_title_colon(self):
  self.p['pages'][0]['title']='入排标准：关键要求';self.assertIn('TITLE',self.errors(self.p))
 def test_mixed_body_sizes(self):
  self.p['pages'][0]['elements'][1]['font_px']=18;self.assertIn('TYPE-UNIFORM',self.errors(self.p))
 def test_minimum(self):
  self.p['pages'][0]['elements'][0]['font_px']=15;self.assertIn('FONT-FLOOR',self.errors(self.p))
 def test_pagewide_compact(self):
  p=self.p['pages'][0];p['body_profile']='compact'
  for e in p['elements']:e['font_px']=16
  self.assertEqual(self.errors(self.p),[])
 def test_internal_citation_forbidden(self):
  self.p['pages'][0]['sources'][0]['visible']=True;self.assertIn('CITATION',self.errors(self.p))
 def test_external_science_allowed(self):
  self.p['pages'][0]['sources'][0].update(kind='scientific_paper',visible=True);self.assertEqual(self.errors(self.p),[])
 def test_card_edge_bars_rejected_by_schema(self):
  self.p['pages'][0]['cards'][0]['edge_decoration']='full_width_bar';self.assertIn('SCHEMA',self.errors(self.p))
 def test_image_subject_collision(self):
  self.p['pages'][0]['image']['subject_rects']=[[100,0,200,100]];self.assertIn('IMAGE-COLLISION',self.errors(self.p))
 def test_ppt_no_optical_exemption(self):
  self.p['pages'][0]['image']={'mode':'global_procedural_optical_field','procedural_evidence':'field.css'};self.assertIn('IMAGE-REQUIRED',self.errors(self.p))
 def test_site_optical_exemption_requires_evidence(self):
  self.p['track']='site';self.p['pages'][0]['image']={'mode':'global_procedural_optical_field'};self.assertIn('IMAGE-EXEMPTION',self.errors(self.p))
 def test_logo_byte_identity(self):
  t=json.loads((ROOT/'tokens/tokens.json').read_text());self.assertEqual(hashlib.sha256((ROOT/t['logo']['path']).read_bytes()).hexdigest(),t['logo']['sha256'])
 def test_px_pt_conversion(self):
  t=json.loads((ROOT/'tokens/tokens.json').read_text())
  for k in t['type_pt']:self.assertAlmostEqual(t['type_pt'][k]*4/3,t['type_px'][k],places=5)
 def test_mask_geometry(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'mask.png';make(self.p,0,p);im=Image.open(p);self.assertEqual(im.size,(1280,720));self.assertEqual(im.getpixel((120,20)),(255,255,255))
 def test_svg_primitive_parses_native_alpha(self):
  text=card(title='A&B');root=E.fromstring(text);self.assertIn('A&amp;B',text);self.assertIn('stop-opacity',text);self.assertNotIn('backdrop-filter',text)
 def test_film_schema(self):
  s=json.loads((ROOT/'schemas/film-plan.schema.json').read_text());d=json.loads((ROOT/'examples/film-plan.json').read_text());self.assertEqual(list(Draft202012Validator(s).iter_errors(d)),[])
 def test_gantt_schema(self):
  s=json.loads((ROOT/'schemas/gantt.schema.json').read_text());d=json.loads((ROOT/'examples/gantt-data.json').read_text());self.assertEqual(list(Draft202012Validator(s).iter_errors(d)),[])
 def test_legacy_missing_generation_asset_not_passed(self):
  findings=validate(self.p,{'schema_version':'6.0','assets':[]});self.assertIn('ASSET-MISSING',[x['code']for x in findings])
if __name__=='__main__':unittest.main(verbosity=2)
