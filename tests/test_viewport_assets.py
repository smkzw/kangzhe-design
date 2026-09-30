"""Responsive real-source bindings; synthetic fixtures never claim generation."""
import copy,json,sys,tempfile,unittest,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from qc_plan import validate
class ViewportAssets(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.plan=json.loads((ROOT/'agent/fixtures/page-plan.valid.json').read_text());self.plan['target_viewports']=[[1280,720],[2560,1080]]
  self.assets=[]
  for name,size,viewport,crop in [('body-field-01',(2560,1440),(1280,720),(0,0,2560,1440)),('wide',(2560,1080),(2560,1080),(0,0,2560,1080))]:
   p=self.root/(name+'.png');Image.new('RGB',size,'white').save(p)
   self.assets.append(dict(id=name,origin='generated',file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),tool_receipt='synthetic deterministic fixture, not production generation',requested_size=None,actual_size=list(size),renditions=[dict(viewport=list(viewport),crop=list(crop),fit='cover',protected_regions=[],subject_rects=[],evidence=['synthetic'])],review=dict(bare='pass',composite='pass',reviewer='fixture',evidence=['synthetic'])))
  self.manifest={'schema_version':'6.0','assets':self.assets}
  self.image=self.plan['pages'][0]['image'];self.image['viewport_assets']=[{'viewport':[2560,1080],'asset_id':'wide'}]
 def codes(self):return {x['code'] for x in validate(self.plan,self.manifest,self.root) if x['level']=='error'}
 def test_valid_standard_and_ultrawide_real_sources(self):self.assertEqual(self.codes(),set())
 def test_all_targets_overridden_still_validate_default(self):
  self.image['viewport_assets'].insert(0,{'viewport':[1280,720],'asset_id':'body-field-01'})
  self.image['asset_id']='missing-fallback';self.assertIn('ASSET-MISSING',self.codes())
 def test_canonical_protection_cannot_be_removed_in_rendition(self):
  self.plan['pages'][0]['protected_regions']=[dict(id='header',role='header',rect=[0,0,1280,88],motion_margin=24)]
  self.assets[0]['renditions'][0]['subject_rects']=[[100,10,100,50]];self.assertIn('IMAGE-RENDITION-COLLISION',self.codes())
 def test_noncanonical_subject_requires_actual_viewport_protections(self):
  self.assets[1]['renditions'][0]['subject_rects']=[[100,10,100,50]];self.assertIn('IMAGE-PROTECTION-MAP',self.codes())
 def test_actual_viewport_protection_and_padding_cannot_be_omitted(self):
  self.plan['pages'][0]['protected_regions']=[dict(id='header',role='header',rect=[0,0,1280,88],motion_margin=24)]
  self.image['viewport_regions']=[dict(viewport=[2560,1080],protected_regions=[dict(id='header',role='header',rect=[0,0,2560,132],motion_margin=24)])]
  self.assets[1]['renditions'][0]['subject_rects']=[[100,140,100,10]];self.assertIn('IMAGE-RENDITION-COLLISION',self.codes())
  self.image['viewport_regions'][0]['protected_regions']=[];self.assertIn('IMAGE-PROTECTION-COVERAGE',self.codes())
 def test_stream_protection_pad_stays_screen_pixels(self):
  self.plan.update(track='stream',canvas=[2560,1080]);self.plan['pages'][0]['motion_objects']=[dict(id='a',role='card',enter='fade',exit='fade',hover='tilt',ambient='none')]
  self.plan['pages'][0]['protected_regions']=[dict(id='header',role='header',rect=[0,0,2560,88])]
  self.image['viewport_regions']=[dict(viewport=[1280,720],protected_regions=[dict(id='header',role='header',rect=[0,0,1280,88])])]
  self.assets[0]['renditions'][0]['subject_rects']=[[100,100,100,10]];self.assertIn('IMAGE-RENDITION-COLLISION',self.codes())
  self.assets[0]['renditions'][0]['subject_rects']=[[100,105,100,10]];self.assertNotIn('IMAGE-RENDITION-COLLISION',self.codes())
 def test_no_override_cannot_fake_wide_source(self):
  self.image.pop('viewport_assets');self.assertIn('IMAGE-RENDITION-MISSING',self.codes())
 def test_mapping_nonexistent_asset_rejected(self):
  self.image['viewport_assets'][0]['asset_id']='absent';self.assertIn('ASSET-MISSING',self.codes())
 def test_duplicate_or_undeclared_viewport_rejected(self):
  self.image['viewport_assets']*=2;self.assertIn('IMAGE-VIEWPORT-DUPLICATE',self.codes())
  self.image['viewport_assets']=[{'viewport':[390,844],'asset_id':'wide'}];self.assertIn('IMAGE-VIEWPORT-UNKNOWN',self.codes())
 def test_wide_mapping_still_checks_source_ratio_and_pixels(self):
  self.assets[1]['actual_size']=[2560,1440];self.assertIn('IMAGE-ULTRAWIDE',self.codes());self.assertIn('ASSET-PIXELS',self.codes())
 def test_selected_asset_still_requires_real_hash_and_composite(self):
  self.assets[1]['sha256']='0'*64;self.assets[1]['review']['composite']='pending';self.assertIn('ASSET-HASH',self.codes());self.assertIn('IMAGE-QC',self.codes())
 def test_selected_asset_cannot_hide_crop_collision(self):
  r=self.assets[1]['renditions'][0];r['protected_regions']=[[10,10,100,100]];r['subject_rects']=[[50,50,100,100]];self.assertIn('IMAGE-RENDITION-COLLISION',self.codes())
 def test_optical_exemption_cannot_carry_hidden_asset_overrides(self):
  self.plan['track']='site';self.plan['target_viewports']=[[1280,720],[1440,900],[1920,1080],[2560,1080]];self.plan['pages'][0]['motion_objects']=[dict(id='a',role='card',enter='fade',exit='fade',hover='tilt',ambient='none')]
  self.image.update(mode='global_procedural_optical_field',procedural_evidence='actual-field.js');self.assertIn('IMAGE-VIEWPORT-MODE',self.codes())
if __name__=='__main__':unittest.main()
