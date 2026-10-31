"""7.1.2: secondary type role, scene/demo tokens wired to consumers, demo forms and their examples in place.
7.1.3: sixteen data-driven forms, icons, the four demo presets and their rotation, the HTML-PPT template deck."""
from pathlib import Path
import copy, json, re, sys, unittest
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

def all_forms():
    base = re.search(r"const FORMS = \{([^}]*)\}", read('runtime/kz-demo.js')).group(1).replace(' ', '').split(',')
    return base + re.findall(r"def\('(\w+)'", read('runtime/kz-demo-patterns.js'))

class DemoForms(unittest.TestCase):
    def test_each_form_is_documented_and_exemplified(self):
        forms = all_forms()
        spec, api, data = read('design_specs/15-demo-motion.md'), read('runtime/API.md'), read('examples/motion/data.js')
        gallery = read('examples/motion/index.html')
        self.assertEqual(len(forms), 16)
        self.assertEqual(len(set(forms)), 16)
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
        for s in ('kz-scenes.js', 'kz-icons.js', 'kz-demo.js', 'kz-demo-patterns.js'):
            self.assertLess(html.index(s), html.index('html-ppt-bridge.js'))

    def test_template_deck_covers_the_new_forms_and_rotates_presets(self):
        html = read('examples/motion/deck/index.html')
        kinds = re.findall(r'data-kz-demo-kind="(\w+)"', html)
        self.assertEqual(sorted(kinds), sorted(all_forms()[6:]))
        presets = re.findall(r'class="kz-body" data-preset="([\w-]+)"', html)
        self.assertEqual(len(presets), len(kinds))
        self.assertEqual(set(presets), {'demo', 'demo-mirror', 'demo-wide', 'demo-stack'})
        self.assertTrue(all(a != b for a, b in zip(presets, presets[1:])), presets)
        order = [html.index(f'runtime/{m}"') for m in ('kz-scenes.js', 'kz-icons.js', 'kz-demo.js', 'kz-demo-patterns.js')]
        self.assertEqual(order, sorted(order))
        # every demo slide has notes with one 【n】 per scene of its stage (five scenes each)
        notes = re.findall(r'<aside class="notes">([^<]*)</aside>', html)[1:-1]
        self.assertEqual([len(re.findall(r'【\d】', n)) for n in notes], [5] * len(kinds))

    def test_icons_used_exist(self):
        names = set(json.loads(read('assets/icons/icons.json'))['icons'])
        used = set(re.findall(r"icon: '([\w-]+)'", read('examples/motion/data.js')))
        # literal names in icon(cv, id, name) and lead/glyph(obj(…), name); unknown names also throw at mount
        for src in ('runtime/kz-demo.js', 'runtime/kz-demo-patterns.js'):
            used |= set(re.findall(r"icon\(cv, '\w+'(?: \+ \w+)?, '([\w-]+)'", read(src)))
            used |= set(re.findall(r"(?:lead|glyph)\(.*?\), '([\w-]+)'", read(src)))
        self.assertTrue(used, 'no icon references found')
        self.assertLessEqual(used, names, used - names)

class DemoPlan(unittest.TestCase):
    # 15 DEMO-01/05/09 in the page plan: demo pages declare kind and a demo preset, adjacent ones rotate it
    def plan(self, pages):
        p = json.loads(read('agent/fixtures/page-plan.valid.json')); p['track'] = 'htmlppt'
        p['target_viewports'] = [[1280, 720], [1536, 730], [1920, 940], [1920, 1080], [2560, 1080]]
        page = p['pages'][0]; page['motion_objects'] = [{'id': c['id'], 'role': 'card', 'enter': 'fade', 'exit': 'fade', 'hover': 'tilt', 'ambient': 'none'} for c in page['cards']] or [{'id': 'a', 'role': 'card', 'enter': 'fade', 'exit': 'fade', 'hover': 'tilt', 'ambient': 'none'}]
        out = []
        for i, (preset, demo) in enumerate(pages):
            q = copy.deepcopy(page); q['id'] = f'p{i:02d}'; q['preset'] = preset
            if demo is not None: q['demo'] = demo
            out.append(q)
        p['pages'] = out
        return {f['code'] for f in validate(p) if f['level'] == 'error'}

    def test_rotation_passes(self):
        cases = ['positive', 'negative', 'complex_negative']
        self.assertEqual(self.plan([('demo-mirror', {'kind': 'flow', 'cases': cases}), ('demo-wide', {'kind': 'gantt'}), ('cards-3', None), ('demo-mirror', {'kind': 'units'})]) & {'DEMO-PRESET', 'DEMO-PRESET-REPEAT', 'DEMO-CASES', 'SCHEMA'}, set())

    def test_adjacent_repeat_and_wrong_preset_fail(self):
        self.assertIn('DEMO-PRESET-REPEAT', self.plan([('demo', {'kind': 'units'}), ('demo', {'kind': 'calc'})]))
        self.assertIn('DEMO-PRESET', self.plan([('cards-3', {'kind': 'units'})]))

    def test_process_demos_need_both_cases(self):
        self.assertIn('DEMO-CASES', self.plan([('demo', {'kind': 'flow', 'cases': ['positive']})]))

    def test_no_demo_needs_a_reason(self):
        self.assertIn('SCHEMA', self.plan([('cards-3', {'none': ''})]))
        self.assertNotIn('SCHEMA', self.plan([('cards-3', {'none': '纯结论页'})]))

    def test_motion_routes_to_demo_owner(self):
        for track in ('htmlppt', 'site', 'stream'):
            self.assertIn('design_specs/15-demo-motion.md', files(track, set()))
        self.assertIn('design_specs/15-demo-motion.md', files('pptx', {'motion'}))
        self.assertNotIn('design_specs/15-demo-motion.md', files('pptx', set()))

if __name__ == '__main__':
    unittest.main()
