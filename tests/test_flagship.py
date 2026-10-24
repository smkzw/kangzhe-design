"""Flagship route (14): tokens are complete and consumed, the light plate is deterministic and calm where asked,
routing and the stop gate are documented, and the reference deck follows FLAG-03/05/06."""
from pathlib import Path
import json, re, sys, unittest
R = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / 'tools'))
from context_pack import index  # noqa: E402

T = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
F = T['flagship']

class FlagshipTokens(unittest.TestCase):
    def test_type_respects_floor(self):
        for k, v in F['type_px'].items():
            self.assertGreaterEqual(v, T['type_px']['body_floor'], k)

    def test_identity_never_scaled_below_floor(self):
        for kind, (corner, scale) in F['identity']['anchors'].items():
            self.assertIn(corner, ('tl', 'tr', 'bl', 'br'), kind)
            self.assertGreaterEqual(scale, 1, kind)

    def test_every_page_kind_has_level_and_anchor(self):
        kinds = set(F['levels']['by_kind'])
        self.assertEqual(kinds, set(F['identity']['anchors']))
        self.assertTrue(kinds <= set(F['river']) | {'content'})

    def test_css_variables_generated(self):
        css = (R / 'runtime/kz-tokens.css').read_text(encoding='utf-8')
        for k in F['type_px']:
            self.assertIn(f'--kzf-type-{k.replace("_", "-")}:', css)
        for k in F['transition']:
            if k.endswith('_ms'):
                self.assertIn(f'--kzf-trans-{k[:-3].replace("_", "-")}:', css)

    def test_numeric_tokens_have_a_consumer(self):
        # A token nothing reads is inert (CLAUDE review rule): every field/level/light/lens key appears in a consumer.
        # Generated CSS variables count when kz-flagship.css actually uses them.
        consumers = ''.join((R / p).read_text(encoding='utf-8') for p in ['runtime/kz-flagship.js', 'runtime/kz-flagship.css', 'tools/flagship_plate.py', 'tools/build_tokens.py'])
        for group in ('field', 'levels', 'light', 'lens', 'transition', 'entrance', 'plate'):
            for key in F[group]:
                if key.startswith('_'):
                    continue
                names = [key] + ([f'var(--kzf-trans-{key[:-3].replace("_", "-")})'] if group == 'transition' and key.endswith('_ms') else [])
                self.assertTrue(any(n in consumers for n in names), f'flagship.{group}.{key}')

class FlagshipPlate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
        except ImportError:
            raise unittest.SkipTest('numpy not installed (requirements.txt)')
        from flagship_plate import render
        cls.render = staticmethod(render)

    def test_deterministic(self):
        a = self.render('cover', [0.72, 0.74], size=(320, 180)).tobytes()
        b = self.render('cover', [0.72, 0.74], size=(320, 180)).tobytes()
        self.assertEqual(a, b)

    def test_content_reading_area_is_calm(self):
        import numpy as np
        canvas = np.array([int(F['canvas'][i:i + 2], 16) for i in (1, 3, 5)])
        img = np.asarray(self.render('content', [0.8, 0.4], calm=[[0.08, 0.27, 0.65, 0.91]], size=(640, 360)), dtype=int)
        inside = img[int(0.35 * 360):int(0.85 * 360), int(0.15 * 640):int(0.58 * 640)]
        self.assertLessEqual(np.abs(inside - canvas).max(), 24)

    def test_hero_carries_more_light_than_content(self):
        import numpy as np
        warm = lambda im: (np.asarray(im, dtype=int)[..., 2] < 200).mean()
        self.assertGreater(warm(self.render('cover', [0.72, 0.74], size=(320, 180))), warm(self.render('content', [0.8, 0.4], size=(320, 180))) + 0.05)

class FlagshipRouting(unittest.TestCase):
    def test_context_pack_adds_owner(self):
        for track in ('pptx', 'htmlppt'):
            self.assertIn('design_specs/14-flagship.md', index(track, set(), 'bootstrap', route='flagship')['read_files'])
            self.assertNotIn('design_specs/14-flagship.md', index(track, set(), 'bootstrap')['read_files'])
        with self.assertRaises(ValueError):
            index('site', set(), 'all', route='flagship')

    def test_author_stage_files_exist(self):
        for track in ('pptx', 'htmlppt'):
            index(track, set(), 'author', route='flagship')   # raises FileNotFoundError on a dangling path

    def test_stop_gate_documented(self):
        skill = (R / 'SKILL.md').read_text(encoding='utf-8')
        spec = (R / 'design_specs/14-flagship.md').read_text(encoding='utf-8')
        self.assertIn('⛔ 选路阻断', skill)
        for word in ('PPTX', 'HTML-PPT', '推荐', '常规', '旗舰'):
            self.assertIn(word, skill.split('## ⛔ 选路阻断')[1].split('\n## ')[0])
        self.assertIn('## FLAG-01 选路阻断与判定（MUST）', spec)
        self.assertIn('14-flagship', (R / 'design_specs/00-authority.md').read_text(encoding='utf-8'))

class FlagshipPlanCheck(unittest.TestCase):
    """qc_plan with route flagship: the reference PPTX plan passes; regular sizes, a regular background or a flagship
    background on the regular route are errors (14 FLAG-02/11)."""
    @classmethod
    def setUpClass(cls):
        from qc_plan import validate
        cls.validate = staticmethod(validate)
        cls.plan = json.loads((R / 'examples/reference/pptx-flagship/page-plan.json').read_text(encoding='utf-8'))

    def errors(self, plan):
        return {f['code'] for f in self.validate(plan) if f['level'] == 'error'}

    def test_reference_plan_passes(self):
        self.assertEqual(self.errors(self.plan), set())

    def test_regular_type_rejected(self):
        import copy
        p = copy.deepcopy(self.plan); p['pages'][3]['elements'][0]['font_px'] = T['type_px']['page_title']
        self.assertIn('FLAG-TYPE', self.errors(p))

    def test_footer_rejected(self):
        import copy
        p = copy.deepcopy(self.plan); p['pages'][3]['elements'].append({'id': 'f', 'role': 'footer', 'font_px': 18, 'line_height': 1.4})
        self.assertIn('FLAG-CHROME', self.errors(p))

    def test_plate_required_and_route_bound(self):
        import copy
        p = copy.deepcopy(self.plan); del p['pages'][0]['image']['plate']
        self.assertIn('FLAG-PLATE', self.errors(p))
        q = copy.deepcopy(self.plan); del q['route']
        self.assertTrue({'SCHEMA', 'FLAG-IMAGE-ROUTE'} & self.errors(q))

class FlagshipReferenceDeck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (R / 'examples/reference/htmlppt-flagship/index.html').read_text(encoding='utf-8')
        cls.slides = re.findall(r'<section class="slide[^"]*"[^>]*>.*?</section>', cls.html, re.S)

    def test_every_slide_declares_kind_and_focus(self):
        self.assertGreaterEqual(len(self.slides), 5)
        for s in self.slides:
            self.assertRegex(s, r'data-kzf-kind="(cover|toc|section|content|ending)"')
            self.assertIn('data-kzf-focus=', s)

    def test_lens_budget_and_calm_content(self):
        for s in self.slides:
            self.assertLessEqual(len(re.findall(r'class="[^"]*\bkzf-lens\b', s)), F['lens']['max_per_page'])
            self.assertLessEqual(s.count('data-kzf-pool'), 1)
            if 'data-kzf-kind="content"' in s:
                self.assertGreaterEqual(s.count('data-kzf-calm'), 2)
                for role in re.findall(r'data-kzf-lens="(\w+)"', s):
                    self.assertIn(role, F['lens']['roles'])

    def test_no_fixed_chrome(self):
        for marker in ('kz-mark', 'kz-chrome', 'kz-foot', 'kz-page-number'):
            self.assertNotIn(marker, self.html)
        self.assertIn('kz-flagship.js', self.html)
        self.assertIn('kz-flagship.css', self.html)

if __name__ == '__main__':
    unittest.main()
