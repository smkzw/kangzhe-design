"""Structural checks on the normative text: one owner per rule, no incident history, live references."""
from pathlib import Path
import json, re, unittest
R = Path(__file__).resolve().parents[1]
NORMATIVE = [R / 'SKILL.md', *sorted((R / 'design_specs').glob('*.md')), *sorted((R / 'adapters').glob('*.md')), R / 'runtime/API.md', R / 'runtime/README.md']
RULE = re.compile(r'\b(CORE|LG|ELEV|TYPE|COPY|IMG|CHART|MOTION|FILM|DRILL|GANTT|NOTES|HERO|FOLD|BODY)-(\d{2}|PPTX|PLAN)\b')
TOKENS = json.loads((R / 'tokens/tokens.json').read_text())

def text(p):
    return p.read_text(encoding='utf-8')

class SpecStructure(unittest.TestCase):
    def test_each_rule_has_exactly_one_owner_heading(self):
        owners = {}
        for f in sorted((R / 'design_specs').glob('*.md')):
            for line in text(f).splitlines():
                if line.startswith('#'):
                    for m in RULE.finditer(line):
                        owners.setdefault(m.group(0), []).append(f.name)
        dup = {k: v for k, v in owners.items() if len(v) > 1}
        self.assertEqual(dup, {}, 'rule defined in more than one heading')
        missing = set()
        for f in NORMATIVE:
            for m in RULE.finditer(text(f)):
                if m.group(0) not in owners:
                    missing.add((m.group(0), f.name))
        self.assertEqual(missing, set(), 'rule referenced but never defined')

    def test_no_incident_history_in_normative_text(self):
        banned = [r'\bA0\d\b', r'\bR\d{2}\b', r'KZ6-', 'Camofox', 'ARCO', 'gpt-image', 'Pi/Luna', 'CodeBuddy', 'Gemini', '本轮', 'A08 起']
        hits = []
        for f in NORMATIVE:
            for pat in banned:
                for m in re.finditer(pat, text(f)):
                    hits.append((f.name, m.group(0)))
        self.assertEqual(hits, [])

    def test_token_paths_named_in_text_exist(self):
        roots = {'glass', 'elevation', 'motion', 'layout', 'charts', 'viewports', 'wide', 'image', 'chrome', 'hero_layouts', 'type_px', 'type_pt', 'rhythm', 'colors', 'brand_budget', 'logo', 'departments'}
        bad = []
        for f in NORMATIVE:
            for m in re.finditer(r'`(tokens\.)?([a-z_]+(?:\.[a-z0-9_<>]+)+)', text(f)):
                path = m.group(2).split('.')
                # page-plan also has an `image` object; only an explicit tokens. prefix makes it a token path.
                if path[0] not in roots or (path[0] == 'image' and not m.group(1)):
                    continue
                node = TOKENS
                for key in path:
                    if key.startswith('<'):
                        break
                    if not isinstance(node, dict) or key not in node:
                        bad.append((f.name, m.group(2)))
                        break
                    node = node[key]
        self.assertEqual(bad, [])

    def test_files_named_in_skill_exist(self):
        for m in re.finditer(r'`((?:design_specs|adapters|runtime|tools|schemas|examples|assets|tokens|review)/[^`*\s]+)`', text(R / 'SKILL.md')):
            self.assertTrue((R / m.group(1)).exists(), m.group(1))

    def test_skill_entry_stays_short(self):
        self.assertLess(len(text(R / 'SKILL.md')), 6000)

    def test_versions_agree(self):
        v = (R / 'VERSION').read_text().strip()
        self.assertEqual(TOKENS['version'], v)
        self.assertIn(f'# Kangzhe Design {".".join(v.split(".")[:2])}', text(R / 'SKILL.md'))
        schema = json.loads((R / 'schemas/page-plan.schema.json').read_text())
        fixture = json.loads((R / 'agent/fixtures/page-plan.valid.json').read_text())
        self.assertEqual(schema['properties']['contract_revision']['const'], fixture['contract_revision'])

if __name__ == '__main__':
    unittest.main()
