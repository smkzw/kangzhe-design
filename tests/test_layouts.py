"""13 BODY-02 template library, 03 COPY-09 verbatim paging, 04 IMG-08 white-base plates, 10 G-KZ project check."""
from pathlib import Path
import json, re, shutil, subprocess, sys, tempfile, unittest
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools')); sys.path.insert(0, str(R / 'examples/templates'))
import kz_layouts as K
from kz_layouts import text as T
from kz_layout import source_strings, page_text, squash
from pages import PAGES
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
EX = R / 'examples/templates'

def data(f): return json.loads((EX / f).read_text(encoding='utf-8'))

class Catalogue(unittest.TestCase):
    def test_twenty_to_thirty_templates_each_with_example_data(self):
        cat = K.catalog(); names = {c['name'] for c in cat}
        self.assertGreaterEqual(len(cat), 20); self.assertLessEqual(len(cat), 30)
        self.assertEqual(names, {p[0] for p in PAGES}, 'every template has a page in the sample deck and vice versa')
        for c in cat:
            for k in ('scene', 'title', 'use', 'density'): self.assertTrue(c[k], (c['name'], k))

    def test_every_example_renders_in_both_tracks_without_overflow_or_lost_text(self):
        for name, f, title, _ in PAGES:
            d = data(f); want = source_strings(d)
            for track in ('pptx', 'html'):
                with self.subTest(template=name, data=f, track=track):
                    pages = K.render(name, d, track)
                    self.assertTrue(pages)
                    for p in pages: self.assertLessEqual(p['overflow'], 0.5, f'page overflow {p["overflow"]}')
                    import html
                    got = ''.join(html.unescape(page_text(p['svg'] if track == 'pptx' else p['html'], track))
                                  + (squash(json.dumps(p['charts'], ensure_ascii=False)) if track == 'html' else '') for p in pages)
                    self.assertEqual([s for s in want if squash(s) not in got], [])

class Verbatim(unittest.TestCase):
    def test_long_criteria_page_with_continuous_numbers_and_no_continued_label(self):
        d = data('criteria-long.json'); pages = K.render('criteria', d, 'pptx')
        self.assertGreater(len(pages), 1)
        seen = {'inclusion': [], 'exclusion': []}
        for p in pages:
            for col in p['data']['cols']:
                for seg in col: seen[seg['key']] += list(range(seg['start'], seg['start'] + len(seg['items'])))
            self.assertIsNone(re.search(r'[（(]续[）)]|续表|（续', page_text(p['svg'], 'pptx')))
        for k in seen: self.assertEqual(seen[k], list(range(1, len(d[k]) + 1)), k)

    def test_dropped_clause_is_caught(self):
        d = data('criteria.json'); pages = K.render('criteria', d, 'pptx')
        got = ''.join(page_text(p['svg'], 'pptx') for p in pages)
        tampered = got.replace(squash(T.plain(d['exclusion'][-1]))[:12], '')
        self.assertIn(squash(T.plain(d['exclusion'][-1])), got)
        self.assertNotIn(squash(T.plain(d['exclusion'][-1])), tampered)

    def test_soa_pages_split_visit_columns_evenly_and_repeat_footnotes(self):
        d = data('soa.json'); d['per_page'] = 7; pages = K.render('soa', d, 'pptx')
        spans = sorted({tuple(p['data']['cols']) for p in pages})
        self.assertEqual([b - a for a, b in spans], [6, 6])
        for p in pages: self.assertIn(squash(d['footnotes'][0]), page_text(p['svg'], 'pptx'))

class Typography(unittest.TestCase):
    def test_no_text_below_the_reference_size_and_numerals_readable(self):
        floor = TOK['type_px']['reference']
        for name, f, *_ in PAGES:
            for p in K.render(name, data(f), 'pptx'):
                sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', p['svg'])]
                with self.subTest(template=name): self.assertGreaterEqual(min(sizes), 14 if floor <= 14 else floor)

    def test_highlight_sentinel_is_only_written_for_highlight_runs(self):
        mark = TOK['layout']['templates']['highlight_marker']
        for src in ('diagram_kinds.py', 'diagram_more.py', 'figures.py', 'tree.py'):
            self.assertNotIn(mark.lower(), (R / 'tools/kz_layouts' / src).read_text(encoding='utf-8').lower(), src)
        from kz_layouts.svg import run_svg
        self.assertIn(mark, run_svg('x', frozenset({'highlight'}), '#000'))
        self.assertNotIn(mark, run_svg('x', frozenset({'bold'}), '#000', bold=True))

    def test_bold_inside_bold_text_uses_the_focus_colour(self):
        from kz_layouts.svg import run_svg
        self.assertIn(TOK['colors']['focus'], run_svg('8%', frozenset({'bold'}), '#000', bold=True))

class Plates(unittest.TestCase):
    def test_hero_as_body_fails_raw_and_passes_after_compositing(self):
        from PIL import Image
        import quiet_plate as Q
        im = Image.open(R / 'assets/backgrounds/cover.jpg')
        self.assertTrue(Q.measure(im, 'body')[1], 'a cover image straight behind body text must fail')
        self.assertEqual(Q.measure(Q.compose(im, 'body'), 'body')[1], [])
        self.assertEqual(Q.measure(Image.open(R / 'assets/backgrounds/body-quiet.jpg'), 'body')[1], [], 'the approved quiet background passes')
        sec = Image.open(R / 'assets/backgrounds/section.jpg')
        self.assertEqual(Q.measure(Q.compose(sec, 'section'), 'section')[1], [])

    def test_prompts_share_one_anchor_and_name_the_composition(self):
        import kz_image_prompts as P
        plan = json.loads((R / 'examples/reference/pptx-default/page-plan.json').read_text(encoding='utf-8'))
        out = P.prompts(plan, 'clinical data review')
        self.assertEqual(len({o['asset_id'] for o in out}), len(out))
        for o in out:
            self.assertTrue(o['prompt'].startswith(P.ANCHOR))
            self.assertIn('near-white', o['prompt']); self.assertIn('quiet_plate.py', o['then'])
        self.assertTrue(any('edges and corners' in o['prompt'] for o in out if o['kind'] == 'body'))

class ProjectCheck(unittest.TestCase):
    def test_sample_project_passes_and_a_dropped_clause_or_small_text_fails(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            out = tmp / 'frag'
            src = tmp / 'protocol.txt'  # the synthetic protocol: the example's clauses, one per line
            src.write_text('\n'.join(source_strings(data('criteria-long.json'))), encoding='utf-8')
            r = subprocess.run([sys.executable, str(R / 'tools/kz_layout.py'), 'render', 'criteria', str(EX / 'criteria-long.json'), '--track', 'pptx',
                                '--title', '入选与排除标准', '--out', str(out), '--source', str(src)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            (tmp / 'svg_output').mkdir()
            for f in sorted(out.glob('page_*.svg')): shutil.copy(f, tmp / 'svg_output' / f.name)
            chk = [sys.executable, str(R / 'tools/check_kz_project.py'), str(tmp), '--receipts', str(out), '--json']
            r = subprocess.run(chk, capture_output=True, text=True); self.assertEqual(r.returncode, 0, r.stdout)
            rec = json.loads((out / 'kz-layout-receipt.json').read_text(encoding='utf-8'))
            rec['runs'][0]['verbatim']['missing'] = ['筛选前 3 个月内使用过 GLP-1 受体激动剂'];
            (out / 'kz-layout-receipt.json').write_text(json.dumps(rec, ensure_ascii=False), encoding='utf-8')
            f = sorted((tmp / 'svg_output').glob('*.svg'))[0]; f.write_text(f.read_text(encoding='utf-8').replace('font-size="16"', 'font-size="9"', 1), encoding='utf-8')
            r = subprocess.run(chk, capture_output=True, text=True); self.assertEqual(r.returncode, 1)
            codes = {x['code'] for x in json.loads(r.stdout)['findings'] if x['level'] == 'error'}
            self.assertEqual(codes, {'VERBATIM', 'FONT-FLOOR'})
        finally:
            shutil.rmtree(tmp)

class ReviewRegressions(unittest.TestCase):
    """Defects found in the 7.2.0 code review (2026-10-31)."""
    def test_repeated_source_text_must_appear_as_often(self):
        from kz_layout import missing_strings
        want = ['筛选前 3 个月内使用过者排除'] * 3
        self.assertEqual(missing_strings(want, squash(want[0]) * 2), want[:1])
        self.assertEqual(missing_strings(want, squash(want[0]) * 3), [])

    def test_table_row_wider_than_the_columns_is_an_error_not_a_silent_cut(self):
        from kz_layouts.figures import _grid_row
        with self.assertRaises(ValueError): _grid_row(['a', 'b', 'c'], 2)

    def test_checker_reads_inline_style_sizes_tspans_and_numeric_weights(self):
        from check_kz_project import texts
        svg = ('<svg xmlns="http://www.w3.org/2000/svg"><text style="font-size:8px">小字</text>'
               '<text font-size="16px">正常<tspan font-size="9">更小</tspan></text><text font-size="16" font-weight="700">粗</text></svg>')
        t = texts(svg)
        self.assertIn(8.0, [x[0] for x in t]); self.assertIn(9.0, [x[0] for x in t]); self.assertTrue(any(x[1] for x in t if x[2] == 1))

    def test_partly_overwritten_list_keeps_a_receipt_and_fails_the_check(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            out = tmp / 'frag'; run = lambda *a: subprocess.run([sys.executable, str(R / 'tools/kz_layout.py'), 'render', *a, '--track', 'pptx', '--title', 'T', '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(run('criteria', str(EX / 'criteria-long.json'), '--first', '5').returncode, 0)
            self.assertEqual(run('kv-table', str(EX / 'kv-table.json'), '--first', '6').returncode, 0)
            rec = json.loads((out / 'kz-layout-receipt.json').read_text(encoding='utf-8'))['runs']
            crit = [r for r in rec if r['pattern'] == 'criteria'][0]
            self.assertEqual([p['n'] for p in crit['pages']], [5]); self.assertEqual(crit['overwritten_pages'], [6])
            (tmp / 'svg_output').mkdir()
            for f in out.glob('page_*.svg'): shutil.copy(f, tmp / 'svg_output' / f.name)
            r = subprocess.run([sys.executable, str(R / 'tools/check_kz_project.py'), str(tmp), '--receipts', str(out), '--json'], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertTrue(any('overwritten' in x['message'] for x in json.loads(r.stdout)['findings']))
        finally:
            shutil.rmtree(tmp)

    def test_long_forest_labels_grow_their_rows(self):
        from kz_layouts.diagrams import MEASURE
        spec = data('forest.json')['forest']; base = MEASURE['forest'](spec, 700)
        long = json.loads(json.dumps(spec)); long['rows'][2]['label'] = '基线 HbA1c 低于 8.5% 且病程不超过 5 年的受试者亚组'
        self.assertGreater(MEASURE['forest'](long, 700), base)
        with self.assertRaises(ValueError):
            from kz_layouts.diagrams import draw
            bad = json.loads(json.dumps(spec)); bad['rows'][0].update(est=-0.3, lo=-0.6, hi=0.1); draw('forest', bad, [0, 0, 700, 400], 'f', 'pptx')

    def test_plate_follows_the_slice_crop_and_keeps_transparent_pixels_white(self):
        from PIL import Image
        import quiet_plate as Q
        self.assertEqual(Q.view((1280, 720)), (1.0, 0.0, 0.0))
        k, ox, oy = Q.view((1024, 1024))  # a square image is cropped left and right, as the page shows it
        self.assertAlmostEqual(k, 1024 / 720); self.assertAlmostEqual(ox, (1024 - 1280 * k) / 2); self.assertEqual(oy, 0.0)
        im = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        self.assertEqual(Q.compose(im, 'body').getpixel((5, 5)), (255, 255, 255))

    def test_rotation_counts_uses_once_per_streak(self):
        from check_kz_project import receipt_checks
        mk = lambda pat, ns: {'pattern': pat, 'track': 'pptx', 'pages': [{'n': n, 'file': f'p{n}', 'overflow_px': 0} for n in ns], 'verbatim': {'missing': []},
                              'source_check': {'checked': 1, 'not_in_source': []}}
        found = []; add = lambda *a: found.append(a)
        receipt_checks([mk('criteria', [1, 2, 3]), mk('kv-table', [4])], add); self.assertEqual(found, [])
        receipt_checks([mk('table-band', [1]), mk('table-band', [2]), mk('table-band', [3]), mk('table-band', [4])], add)
        self.assertEqual(len([f for f in found if f[1] == 'ROTATION' and 'in a row' in f[3]]), 1)

class Charts(unittest.TestCase):
    def test_echarts_runtime_knows_the_clinical_kinds(self):
        js = (R / 'runtime/kz-charts.js').read_text(encoding='utf-8')
        for k in ('forest', 'km'): self.assertIn(f"'{k}'", js.split('const KINDS=')[1].split(';')[0])
        self.assertIn("outerBoundsMode:'none'", js)

class LongCriterion(unittest.TestCase):
    """OMP run1 (2026-10-31): one exclusion criterion of 700+ characters did not fit a column, so the agent replaced
    the whole list with a summary. A criterion now breaks at its own clause ends and carries on unnumbered."""
    def test_overlong_criterion_flows_on_verbatim(self):
        from kz_layout import missing_strings
        clause = '筛选前 {n} 个月内发生过需要住院治疗的第 {n} 类合并疾病（研究者判断已稳定且不影响疗效评价者除外）；'
        long = ''.join(clause.format(n=i) for i in range(1, 19)).rstrip('；') + '。'
        d = {'inclusion': [f'入选条款 {i}：年龄 18–75 岁，签署知情同意书。' for i in range(1, 6)],
             'exclusion': [long] + [f'排除条款 {i}：筛选时 eGFR <45 mL/min/1.73 m²。' for i in range(2, 9)]}
        pages = K.render('criteria', d, 'pptx')
        self.assertGreater(len(pages), 1)
        self.assertTrue(all(p['overflow'] <= 0.5 for p in pages))
        units = [it for p in pages for col in p['data']['cols'] for seg in col for it in seg['items'] if seg['key'] == 'exclusion']
        first = [u for u in units if u['n'] == 1]
        self.assertGreater(len(first), 1)                       # criterion 1 was broken
        self.assertNotIn('marker', first[0]); self.assertTrue(all(u.get('marker') == 'none' for u in first[1:]))
        self.assertEqual(''.join(u['text'] for u in first), long)  # not a character changed
        self.assertEqual([u['n'] for u in units if 'marker' not in u], list(range(1, 9)))  # numbering intact
        import html; text = html.unescape(''.join(page_text(p['svg'], 'pptx') for p in pages))
        self.assertEqual(missing_strings(source_strings(d), text), [])
        self.assertNotIn('续', text)

class SourceFidelity(unittest.TestCase):
    """OMP run1: the agent fed its own summary of the exclusion criteria into a template; data → page was intact,
    protocol → data was not. --source checks the second link."""
    PROTOCOL = ('5.2 排除标准\n1. 筛选前 3 个月内使用过 GLP-1 受体激动剂、DPP-4 抑制剂或胰岛素（急性病住院期间短期使用 ≤14 天除外）。\n'
                '2. 筛选时 eGFR <45 mL/min/1.73 m²（CKD-EPI 公式）；或 ALT、AST >3×ULN。\n')
    def test_verbatim_passes_and_summary_fails(self):
        from kz_layout import not_in_source
        ok = ['筛选前 3 个月内使用过 GLP-1 受体激动剂、DPP-4 抑制剂或胰岛素（急性病住院期间短期使用 ≤14 天除外）。',
              '筛选时 eGFR <45 mL/min/1.73 m²（CKD-EPI 公式）；或 ALT、AST >3×ULN。',
              '筛选时 eGFR <45 mL/min/1.73 m²（CKD-EPI 公式）；']  # one clause of a longer criterion
        self.assertEqual(not_in_source(ok, self.PROTOCOL), [])
        self.assertEqual(not_in_source(['筛选时ｅＧＦＲ ＜45 mL/min/1.73 m²（CKD-EPI 公式）；'], self.PROTOCOL), [])  # width and spaces ignored
        summary = ['3 个月内用过 GLP-1、DPP-4 或胰岛素', 'eGFR <45 或肝酶 >3×ULN']
        self.assertEqual(not_in_source(summary, self.PROTOCOL), summary)

    def test_project_check_flags_unchecked_and_overview_rule_pages(self):
        from check_kz_project import receipt_checks
        found = []
        add = lambda lv, code, where, msg: found.append((lv, code))
        page = lambda n: {'n': n, 'file': f'page_{n:02d}.svg', 'overflow_px': 0}
        runs = [{'pattern': 'criteria', 'title': '入选标准', 'track': 'pptx', 'pages': [page(1)], 'verbatim': {'missing': []}},
                {'pattern': 'table-band', 'title': '排除标准要点', 'track': 'pptx', 'pages': [page(2)], 'verbatim': {'missing': []}},
                {'pattern': 'table-band', 'title': '禁用药物', 'track': 'pptx', 'pages': [page(3)], 'verbatim': {'missing': []},
                 'source_check': {'checked': 3, 'not_in_source': ['自写摘要']}}]
        receipt_checks(runs, add)
        self.assertIn(('error', 'RULE-SOURCE'), found)       # criteria without --source, and the failed check
        self.assertIn(('warn', 'RULE-UNCHECKED'), found)
        self.assertIn(('warn', 'RULE-OVERVIEW'), found)
        self.assertEqual(sum(1 for f in found if f == ('error', 'RULE-SOURCE')), 2)

class PowerPointReadback(unittest.TestCase):
    """Found in Mac PowerPoint 16.114 (PDF export of the template deck), invisible in the SVG preview and LibreOffice."""
    @staticmethod
    def payload(svg):
        import html
        return json.loads(html.unescape(re.search(r'<metadata type="application/json">(.*?)</metadata>', svg, re.S).group(1)))

    def test_table_cells_carry_padding_and_line_spacing(self):
        # PowerPoint's single CJK line (~1.68 em) plus default margins grew every SoA row and pushed the last row onto the footnotes
        from kz_layouts.figures import table_svg, PT
        p = self.payload(table_svg({'columns': ['项目', 'V1'], 'rows': [['知情同意', {'mark': 'dot'}], ['**HbA1c**', '!!≥7.0%!!']]}, (0, 0, 600, 300), 't'))
        self.assertEqual(p['style']['padding'], {'left': PT['pad_x'], 'right': PT['pad_x'], 'top': PT['pad_y'], 'bottom': PT['pad_y']})
        for row in [p['columns']] + p['rows']:
            for c in row:
                if c.get('merge_continuation'): continue
                self.assertNotIn('text', c)
                self.assertTrue(all(q['line_spacing_percent'] == PT['line_spacing_percent'] for q in c['paragraphs']))
        # the drawn row holds PowerPoint's line at that spacing plus both margins
        self.assertLessEqual(16 * 1.68 * PT['line_spacing_percent'] / 100 + 2 * PT['pad_y'], 16 * 1.35 + 12)

    def test_category_labels_sit_low_and_doughnut_values_live_in_the_legend(self):
        from kz_layouts.figures import chart_svg
        col = self.payload(chart_svg({'kind': 'column', 'categories': ['0.5 mg', '1.0 mg'], 'series': [{'name': 'Δ', 'values': [-1.1, -1.4]}]}, (0, 0, 400, 260), 'c'))
        self.assertEqual(col['axes']['category'], {'label_position': 'low'})  # not on the zero line, inside negative bars
        svg = chart_svg({'kind': 'doughnut', 'categories': ['恶心', '腹泻'], 'unit': '%', 'series': [{'name': 'AE', 'values': [42, 58]}]}, (0, 0, 400, 260), 'd')
        d = self.payload(svg)
        self.assertNotIn('note', d)  # a note under the ring collided with PowerPoint's legend
        self.assertEqual(d['categories'], ['恶心 42%', '腹泻 58%'])
        self.assertIn('恶心 42%', svg.split('</metadata>')[1])

if __name__ == '__main__':
    unittest.main()
