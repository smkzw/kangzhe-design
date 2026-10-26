"""7.1.2: secondary type role, scene/demo tokens wired to consumers, demo forms and their examples in place."""
from pathlib import Path
import json, re, sys, unittest
R = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / 'tools'))
from qc_plan import validate
from context_pack import files
T = json.loads((R / 'tokens/tokens.json').read_text())
read = lambda p: (R / p).read_text(encoding='utf-8')

class SecondaryRole(unittest.TestCase):
    def codes(self, track, size):
        p = json.loads(read('agent/fixtures/page-plan.valid.json')); p['track'] = track
        if track != 'pptx':
            p['target_viewports'] = [[1280, 720], [1536, 730], [1920, 940], [1920, 1080], [2560, 1080]]
            p['pages'][0]['motion_objects'] = [{'id': 'a', 'role': 'card', 'enter': 'fade', 'exit': 'fade', 'hover': 'tilt', 'ambient': 'none'}]
        p['pages'][0]['elements'][0].update(role='secondary', font_px=size)
        return {f['code'] for f in validate(p) if f['level'] == 'error'}

    def test_secondary_is_12pt(self):
        self.assertEqual(T['type_pt']['secondary'], 12)
        self.assertAlmostEqual(T['type_px']['secondary'], 12 * 4 / 3)
        self.assertIn('--kz-type-secondary:16px', read('runtime/kz-tokens.css').replace(' ', ''))

    def test_secondary_passes_at_its_size_on_any_page(self):
        for track in ('pptx', 'htmlppt'):
            with self.subTest(track=track):
                self.assertEqual(self.codes(track, T['type_px']['secondary']), set())

    def test_secondary_is_one_size(self):
        for track in ('pptx', 'htmlppt'):
            with self.subTest(track=track):
                self.assertIn('SECONDARY-TYPE', self.codes(track, 18))

class SceneTokens(unittest.TestCase):
    def test_scene_and_density_tokens_have_consumers(self):
        # A token nothing reads is inert: every scene, stepping and density key appears in a consumer.
        consumers = ''.join(read(p) for p in ['runtime/kz-scenes.js', 'runtime/kz-motion.js', 'adapters/html-ppt-bridge.js', 'tests/ego/demo_checks.mjs'])
        keys = [k for k in T['motion']['scenes'] if not k.startswith('_') and k != 'density']
        keys += [k for k in T['motion']['scenes']['density']] + [k for k in T['motion']['film']['scene'] if not k.startswith('_')] + ['max_frame_gap_ms']
        for k in keys:
            self.assertIn(k, consumers, k)

    def test_clocks_read_performance_now(self):
        # 06 FILM-05: no clock takes the rAF timestamp (it can run slower than the wall clock)
        for p in ['runtime/kz-motion.js', 'runtime/kz-scenes.js', 'runtime/kz-charts.js', 'runtime/kz-gantt.js']:
            src = read(p)
            with self.subTest(p=p):
                self.assertIn('performance.now()', src)
                self.assertNotRegex(src, r'requestAnimationFrame\(\s*(?:\(?\s*\w+\s*\)?\s*=>\s*this\.\w+\(\s*\w+\s*\)|this\.\w+\.bind)')

class DemoForms(unittest.TestCase):
    def test_each_form_is_documented_and_exemplified(self):
        forms = re.search(r"const FORMS = \{([^}]*)\}", read('runtime/kz-demo.js')).group(1).replace(' ', '').split(',')
        spec, api, data = read('design_specs/15-demo-motion.md'), read('runtime/API.md'), read('examples/motion/data.js')
        gallery = read('examples/motion/index.html')
        self.assertEqual(len(forms), 6)
        for f in forms:
            with self.subTest(form=f):
                self.assertIn(f'`{f}`', spec)
                self.assertIn(f'`{f}`', api)
                self.assertRegex(data, rf'\b{f}:')
                self.assertIn(f'data-demo="{f}"', gallery)

    def test_reference_deck_has_stepped_demo_pages(self):
        html = read('examples/reference/htmlppt/index.html')
        self.assertEqual(html.count('<section class="slide'), 12)
        self.assertEqual(sorted(set(re.findall(r'data-kz-demo-kind="(\w+)"', html))), ['decision', 'units'])
        for s in ('kz-scenes.js', 'kz-demo.js'):
            self.assertLess(html.index(s), html.index('html-ppt-bridge.js'))

    def test_motion_routes_to_demo_owner(self):
        for track in ('htmlppt', 'site', 'stream'):
            self.assertIn('design_specs/15-demo-motion.md', files(track, set()))
        self.assertIn('design_specs/15-demo-motion.md', files('pptx', {'motion'}))
        self.assertNotIn('design_specs/15-demo-motion.md', files('pptx', set()))

if __name__ == '__main__':
    unittest.main()
