"""02 LG-02: the PPTX edge-bar checker finds full-height and full-width bars and leaves allowed marks alone."""
from pathlib import Path
import json, sys, tempfile, unittest
R = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / 'tools'))
from check_edge_bars import scan

CARD = '<rect id="card" x="100" y="100" width="400" height="200" rx="18" fill="url(#face)"/>'
DEFS = '<defs><linearGradient id="face"><stop stop-color="#FFFDFB" stop-opacity=".6"/></linearGradient></defs>'

def svg(body):
    f = tempfile.NamedTemporaryFile('w', suffix='.svg', delete=False)
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">{DEFS}{body}</svg>'); f.close()
    return f.name

class EdgeBars(unittest.TestCase):
    def levels(self, body):
        return [(b['side'], b['level']) for b in scan(svg(body))]

    def test_full_height_left_bar_fails(self):
        self.assertEqual(self.levels(CARD + '<rect id="bar" x="100" y="100" width="6" height="200" fill="#FF9900"/>'), [('left', 'fail')])

    def test_style_with_spaces_is_read(self):
        # style="stroke:none; fill:#FF9900": the key after "; " is " fill"
        self.assertEqual(self.levels(CARD + '<rect x="100" y="100" width="6" height="200" style="stroke:none; fill:#FF9900"/>'), [('left', 'fail')])

    def test_faint_rgba_bar_is_not_a_bar(self):
        self.assertEqual(self.levels(CARD + '<rect x="100" y="100" width="6" height="200" fill="rgba(255,153,0,.1)"/>'), [])

    def test_full_width_top_bar_fails_inside_translated_group(self):
        body = '<g transform="translate(40,20)">' + CARD + '<rect x="100" y="100" width="400" height="4" fill="#407AAA"/></g>'
        self.assertEqual(self.levels(body), [('top', 'fail')])

    def test_coloured_line_on_right_edge_fails(self):
        self.assertEqual(self.levels(CARD + '<line x1="498" y1="110" x2="498" y2="290" stroke="#C00000" stroke-width="4"/>'), [('right', 'fail')])

    def test_short_mark_and_neutral_hairline_pass(self):
        body = CARD + '<rect x="100" y="120" width="6" height="24" fill="#FF9900"/><rect x="100" y="299" width="400" height="1" fill="#E5E1DA"/>'
        self.assertEqual(self.levels(body), [])

    def test_page_chrome_rule_is_not_a_card_bar(self):
        body = '<g data-pptx-role="decoration"><rect x="56" y="88" width="1168" height="2" fill="#FF9900"/></g>' + CARD
        self.assertEqual(self.levels(body), [])

    def test_mid_length_mark_warns(self):
        self.assertEqual(self.levels(CARD + '<rect x="100" y="100" width="6" height="70" fill="#FF9900"/>'), [('left', 'warn')])

    def test_thresholds_come_from_tokens(self):
        t = json.loads((R / 'tokens/tokens.json').read_text())['glass']['edge_bar']
        self.assertLess(t['warn_ratio'], t['forbid_ratio'])
        src = (R / 'runtime/kz-layout-qc.js').read_text()
        for k in t:
            if not k.startswith('_'):
                self.assertIn(k, src)

if __name__ == '__main__':
    unittest.main()
