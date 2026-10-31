"""09 NOTES-04/05 speaker notes and 03 COPY-01 titles (user rules of 2026-10-31)."""
from pathlib import Path
import json, re, subprocess, sys, tempfile, unittest
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from check_notes import check, sentences, from_md
from kz_titles import title_findings

def codes(notes, kinds=None):
    return sorted({(f['level'], f['code']) for f in check(notes, kinds)})

class Notes(unittest.TestCase):
    def test_hero_pages_take_one_sentence(self):
        two = [('封面', '今天汇报资料核对。希望会上定下补收安排。', None)]
        self.assertIn(('error', 'NOTES-HERO'), codes(two, ['cover']))
        one = [('封面', '今天汇报研究资料包的完整性核对，应收 24 份、已收 20 份，需要会上定下补收和确认的安排。', None)]
        self.assertEqual(codes(one, ['cover']), [])
        self.assertEqual(codes(two, ['content']), [])  # content pages may run longer

    def test_the_spec_bad_example_fails_and_the_good_one_passes(self):
        spec = (R / 'design_specs/09-speaker-notes.md').read_text(encoding='utf-8')
        good = re.search(r'合格：“(.+?)”\n', spec).group(1); bad = re.search(r'不合格：“(.+?)”', spec).group(1)
        self.assertEqual(codes([('入排', good, None)], ['content']), [])
        c = codes([('入排', bad, None)], ['content'])
        for want in (('error', 'NOTES-FILLER'), ('warn', 'NOTES-TRANSL'), ('warn', 'NOTES-LIGHT')): self.assertIn(want, c)

    def test_section_notes_that_only_announce_fail(self):
        # OMP run2 section pages: “先看疾病负担……”“接着看研究怎么设计……”“最后看入排……”
        for t in ('先看疾病负担和 MG-K10 的设计依据。', '接着看研究怎么设计、人群怎么选、药怎么给。', '最后看入排、访视和安全报告。'):
            self.assertIn(('error', 'NOTES-FILLER'), codes([('章节', t, None)], ['section']), t)
        self.assertEqual(codes([('章节', '排除标准有 41 条，筛选时最常卡住的是洗脱期和哮喘控制。', None)], ['section']), [])

    def test_jargon_and_long_sentences_warn(self):
        c = codes([('计划', '这一环节要形成闭环并与各中心对齐颗粒度。', None)], ['content'])
        self.assertIn(('warn', 'NOTES-JARGON'), c)
        long = '研究者需要在每次访视时根据受试者的实际情况和既往的用药记录以及中心实验室返回的检测结果综合判断是否继续给药并完整记录'
        self.assertIn(('warn', 'NOTES-SENTENCE'), codes([('给药', long + '。', None)], ['content']))

    def test_sentences_split_on_full_stops_and_semicolons(self):
        self.assertEqual(len(sentences('一是补收；二是确认。没有异议就推进。')), 3)

    def test_md_and_every_example_deck_pass(self):
        for f in ('examples/templates/deck/index.html', 'examples/reference/htmlppt/index.html',
                  'examples/reference/htmlppt-flagship/index.html', 'examples/motion/deck/index.html',
                  'examples/reference/pptx-default/notes-total.md'):
            r = subprocess.run([sys.executable, str(R / 'tools/check_notes.py'), str(R / f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f + '\n' + r.stdout)
        self.assertEqual(len(from_md(R / 'examples/reference/pptx-default/notes-total.md')), 6)

class Titles(unittest.TestCase):
    def test_titles_name_the_topic(self):
        self.assertEqual(title_findings('入选与排除标准'), [])
        self.assertEqual(title_findings('排除标准 既往治疗与洗脱'), [])
        for t in ('研究结果：疗效显著提升', '入排标准——精准识别人群', '二甲双胍稳定用药如何界定？'):
            self.assertIn('TITLE', [c for _, c, _ in title_findings(t)], t)
        self.assertIn('TITLE-CLAIM', [c for _, c, _ in title_findings('双主要终点支持注册')])
        self.assertIn('TITLE-LONG', [c for _, c, _ in title_findings('二甲双胍单药控制不佳人群的入排标准与洗脱要求')])
        self.assertEqual(title_findings('KZ-001 III 期研究：方案讨论会', 'cover'), [('error', 'TITLE', title_findings('a：b')[0][2])])

    def test_template_titles_comply(self):
        sys.path.insert(0, str(R / 'examples/templates'))
        from pages import PAGES
        for _, _, t, _ in PAGES: self.assertEqual(title_findings(t), [], t)

    def test_project_check_reads_rendered_titles(self):
        from check_kz_project import page_title
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><g id="title" data-pptx-bounds="0 0 1 1"><text>研究终点：双主要终点</text></g></svg>'
        self.assertEqual(page_title(svg), '研究终点：双主要终点')
        self.assertTrue(any(c == 'TITLE' for _, c, _ in title_findings(page_title(svg))))

class TypeFloor(unittest.TestCase):
    def test_explanatory_text_floor_is_10_5_pt(self):
        tok = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
        self.assertEqual(tok['type_pt']['reference'], 10.5); self.assertEqual(tok['type_px']['reference'], 14)
        self.assertEqual(tok['type_pt']['body_floor'], 12)

if __name__ == '__main__':
    unittest.main()
