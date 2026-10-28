"""04 IMG-07: the image-capability gate, the shipped default background set and the liquid-glass style check."""
from pathlib import Path
import copy, hashlib, json, sys, unittest
from PIL import Image
R = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / 'tools'))
from qc_plan import validate, default_set, warm_share
T = json.loads((R / 'tokens/tokens.json').read_text())
REF = json.loads((R / 'examples/reference/pptx-default/page-plan.json').read_text())
MANIFEST = json.loads((R / 'examples/reference/pptx-default/asset-manifest.json').read_text())

def codes(plan, manifest=None):
    return {f['code'] for f in validate(plan, manifest) if f['level'] == 'error'}

class Gate(unittest.TestCase):
    def test_regular_ppt_tracks_need_the_gate(self):
        for track in ('pptx', 'htmlppt'):
            p = json.loads((R / 'agent/fixtures/page-plan.valid.json').read_text()); p['track'] = track; del p['image_capability']
            if track == 'htmlppt':
                p['target_viewports'] = [[1280, 720], [1536, 730], [1920, 940], [1920, 1080], [2560, 1080]]
                p['pages'][0]['motion_objects'] = [{'id': 'a', 'role': 'card', 'enter': 'fade', 'exit': 'fade', 'hover': 'tilt', 'ambient': 'none'}]
            with self.subTest(track=track):
                self.assertIn('IMAGE-CAPABILITY', codes(p))

    def test_default_set_plan_passes_and_checks_ids_and_page_kinds(self):
        self.assertEqual(codes(REF), set())
        p = copy.deepcopy(REF); p['pages'][0]['image']['asset_id'] = 'my-cover'
        self.assertIn('IMAGE-DEFAULT-SET', codes(p))
        p = copy.deepcopy(REF); p['pages'][0]['image']['asset_id'] = 'body-quiet'   # page 0 is the cover
        self.assertIn('IMAGE-DEFAULT-SET', codes(p))

    def test_page_mode_must_follow_the_gate(self):
        p = copy.deepcopy(REF); p['image_capability'] = {'decision': 'generated', 'provider': 'x', 'asked_user': True, 'detected': ['x']}
        self.assertIn('IMAGE-STRATEGY', codes(p))

    def test_generated_route_needs_a_provider(self):
        p = copy.deepcopy(REF); p['image_capability'] = {'decision': 'generated', 'asked_user': True, 'detected': []}
        self.assertIn('SCHEMA', codes(p))

    def test_default_set_cannot_pass_as_generated(self):
        # the reference manifest registers the historical pictures (the same as the default set) as generated
        p = copy.deepcopy(REF); p['image_capability'] = {'decision': 'generated', 'provider': 'x', 'asked_user': True, 'detected': ['x']}
        back = {'cover': 'cover_hero', 'toc': 'toc_hero', 'body-quiet': 'body_quiet', 'ending': 'ending_hero'}
        for page in p['pages']:
            page['image'] = {**page['image'], 'mode': 'generated', 'asset_id': back[page['image']['asset_id']]}
        self.assertIn('IMAGE-DEFAULT-AS-GENERATED', codes(p, MANIFEST))

    def test_flagship_and_web_tracks_do_not_need_the_gate(self):
        flag = json.loads((R / 'examples/reference/pptx-flagship/page-plan.json').read_text())
        self.assertNotIn('IMAGE-CAPABILITY', codes(flag))

class DefaultSet(unittest.TestCase):
    def test_files_exist_and_hashes_match(self):
        assets, hashes = default_set()
        self.assertEqual(sorted(assets), ['body-quiet', 'cover', 'ending', 'section', 'toc'])
        for a in assets.values():
            f = R / a['file']
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), a['sha256'], a['id'])
            self.assertEqual(list(Image.open(f).size), a['actual_size'])
            self.assertTrue(f.suffix in ('.jpg', '.png'), 'PPTX takes PNG/JPEG')
            for alias in a['aliases']:
                self.assertEqual(hashlib.sha256((R / alias['file']).read_bytes()).hexdigest(), alias['sha256'])

    def test_default_set_is_in_the_kangzhe_palette(self):
        style = T['image']['style']
        for a in default_set()[0].values():
            share = warm_share(Image.open(R / a['file']), style)
            if share is not None:
                self.assertGreaterEqual(share, style['warm_share_min'], a['id'])

    def test_off_palette_picture_is_detected(self):
        style = T['image']['style']
        blue = Image.new('RGB', (200, 100), (250, 250, 252)); blue.paste((60, 110, 220), (0, 0, 120, 100))
        self.assertLess(warm_share(blue, style), style['warm_share_min'])
        warm = Image.new('RGB', (200, 100), (252, 250, 246)); warm.paste((255, 170, 40), (0, 0, 60, 100))
        self.assertGreaterEqual(warm_share(warm, style), style['warm_share_min'])

if __name__ == '__main__':
    unittest.main()
