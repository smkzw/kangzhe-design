"""03 COPY-09: criteria keep the protocol's Word numbering and sub-item levels (OMP run2, 7.2.3: a docx → txt export
dropped both; the deck merged one stem's sub-items, promoted another's, and its numbers no longer matched the protocol).
The docx here is synthetic and built in the test."""
from pathlib import Path
import json, subprocess, sys, tempfile, unittest, zipfile
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
import protocol_lists as PL
import kz_layouts as K
from kz_layout import numbering_findings

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

def para(text, num=None, ilvl=0):
    pr = f'<w:pPr><w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num}"/></w:numPr></w:pPr>' if num else ''
    return f'<w:p>{pr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'

NUMBERING = (f'<w:numbering {NS}>'
             '<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl></w:abstractNum>'
             '<w:abstractNum w:abstractNumId="2"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/></w:lvl></w:abstractNum>'
             '<w:num w:numId="5"><w:abstractNumId w:val="1"/></w:num><w:num w:numId="6"><w:abstractNumId w:val="2"/></w:num>'
             '<w:num w:numId="7"><w:abstractNumId w:val="1"/></w:num></w:numbering>')

BODY = [para('3.2 排除标准 ........ 12'),  # a table-of-contents line is not the heading
        para('入选标准：'), para('年龄 18–75 岁；', 7), para('同时存在下述症状：', 7), para('（1）鼻塞；'), para('（2）嗅觉减退；'),
        para('签署知情同意书。', 7),
        para('排除标准：'), para('试验参与者符合以下任一标准，则不能入组：'),
        para('筛选前使用下列治疗：', 5), para('基线前 3 个月内使用生物制剂；', 6), para('基线前 4 周内使用免疫抑制剂；', 6),
        para('急性感染者；', 5), para('传染病筛查符合以下标准：', 5), para('乙肝表面抗原阳性；', 6), para('HIV 抗体阳性；', 6),
        para('妊娠或哺乳期女性。', 5), para('重新筛选'), para('筛选失败者可重新筛选一次。')]

def make_docx(d):
    f = Path(d) / 'protocol.docx'
    with zipfile.ZipFile(f, 'w') as z:
        z.writestr('word/document.xml', f'<w:document {NS}><w:body>' + ''.join(BODY) + '</w:body></w:document>')
        z.writestr('word/numbering.xml', NUMBERING)
    return f

class ProtocolLists(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.docx = make_docx(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_reads_numbers_stems_and_sub_items(self):
        b = PL.find_blocks(self.docx, '排除标准')[0]
        self.assertEqual([it['label'] for it in b['items']], ['1.', '2.', '3.', '4.'])
        self.assertEqual(PL.data_items(b), [
            {'text': '筛选前使用下列治疗：', 'items': ['基线前 3 个月内使用生物制剂；', '基线前 4 周内使用免疫抑制剂；']},
            '急性感染者；', {'text': '传染病筛查符合以下标准：', 'items': ['乙肝表面抗原阳性；', 'HIV 抗体阳性；']}, '妊娠或哺乳期女性。'])
        inc = PL.data_items(PL.find_blocks(self.docx, '入选标准')[0])  # hand-numbered （1）（2） are sub-items too
        self.assertEqual(inc[1], {'text': '同时存在下述症状：', 'items': ['（1）鼻塞；', '（2）嗅觉减退；']})
        self.assertEqual(len(inc), 3)
        self.assertIn('1. 筛选前使用下列治疗：', PL.docx_text(self.docx))

    def test_numbering_check_catches_merged_promoted_and_dropped_stems(self):
        good = {'exclusion': PL.data_items(PL.find_blocks(self.docx, '排除标准')[0])}
        self.assertEqual(numbering_findings(good, self.docx), [])
        merged = {'exclusion': ['基线前 3 个月内使用生物制剂；基线前 4 周内使用免疫抑制剂；', '急性感染者；']}  # stem dropped, sub-items merged
        self.assertEqual(numbering_findings(merged, self.docx)[0]['n'], 1)
        promoted = {'exclusion': [good['exclusion'][0], '急性感染者；', '乙肝表面抗原阳性；', 'HIV 抗体阳性；', '妊娠或哺乳期女性。']}
        self.assertEqual(numbering_findings(promoted, self.docx)[0]['n'], 3)
        short = {'exclusion': good['exclusion'][:3]}
        self.assertIn('4 条', numbering_findings(short, self.docx)[0]['problem'])

    def test_cli_writes_the_criteria_contract_and_render_records_the_check(self):
        out = Path(self.tmp.name)
        r = subprocess.run([sys.executable, str(R / 'tools/protocol_lists.py'), str(self.docx), '--from', '排除标准', '--key', 'exclusion'],
                           capture_output=True, text=True, check=True)
        (out / 'excl.json').write_text(r.stdout, encoding='utf-8')
        r = subprocess.run([sys.executable, str(R / 'tools/kz_layout.py'), 'render', 'criteria', str(out / 'excl.json'), '--track', 'pptx',
                            '--title', '排除标准', '--out', str(out / 'frag'), '--source', str(self.docx)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        sc = json.loads((out / 'frag/kz-layout-receipt.json').read_text(encoding='utf-8'))['runs'][-1]['source_check']
        self.assertEqual(sc['numbering'], {'checked': True, 'mismatch': []}); self.assertEqual(sc['not_in_source'], [])

class CriteriaLayout(unittest.TestCase):
    def test_sub_items_hang_under_their_stem_and_keep_its_number(self):
        d = {'exclusion': [{'text': '筛选前使用下列治疗：', 'items': ['甲药；', '乙药；']}, '急性感染者；']}
        p = K.render('criteria', d, 'pptx')[0]
        html = K.render('criteria', d, 'html')[0]['html']
        self.assertIn('is-sub', html); self.assertIn('is-top', html)
        self.assertEqual(html.count('kzl-mk is-number'), 2)  # 1 and 2; the sub-items take dots
        self.assertIn('>2<', p['svg'])

    def test_a_stem_never_ends_a_column_without_its_first_sub_item(self):
        short = '妊娠或哺乳期女性，或计划在研究期间妊娠的女性；'
        long = '基线前三个月内接受过任何全身性单克隆抗体或生物制剂治疗，或研究者评估其他可能影响疗效评价的治疗；' * 2
        d = {'exclusion': [short] * 9 + [{'text': '合并哮喘者满足以下任一条件：', 'items': [long, long]}] + [short] * 3}
        cols = [[(u['n'], u.get('level', 0)) for s in col for u in s['items']] for p in K.render('criteria', d, 'pptx') for col in p['data']['cols']]
        self.assertFalse(any(len(c) > 1 and c[-1] == (10, 0) for c in cols), cols)
        self.assertTrue(any(c[0] == (10, 0) for c in cols), cols)  # carried over with its sub-items

if __name__ == '__main__':
    unittest.main()
