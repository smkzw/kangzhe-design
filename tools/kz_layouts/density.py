"""13 BODY-03 content density: how much a page has to say, so its look can follow (tokens.layout.density).

load = visible characters (markup stripped, spaces dropped) + item_weight × list items. A page under sparse_max is
sparse (a few short points: big numbers, claim + support, hub), over dense_min is dense (column flow, dense cards,
rule tables), and standard between. Data-led families (charts, tables, plans) are not judged by text load.
"""
import json
from pathlib import Path
from . import text as T

TOK = json.loads((Path(__file__).resolve().parents[2] / 'tokens/tokens.json').read_text(encoding='utf-8'))
D = TOK['layout']['density']
SKIP = {'icon', 'tone', 'kind', 'layout', 'marker', 'align', 'mark', 'role', 'id', 'unit', 'type', 'department', 'color', 'weights'}

def load(data):
    chars = items = 0
    def walk(v, k=None):
        nonlocal chars, items
        if isinstance(v, str):
            if k not in SKIP: chars += len(T.plain(v).replace(' ', ''))
        elif isinstance(v, dict):
            for kk, x in v.items(): walk(x, kk)
        elif isinstance(v, list):
            if v and all(isinstance(x, (str, dict)) for x in v): items += len(v)
            for x in v: walk(x, k)
    walk(data)
    return chars + D['item_weight'] * items

def tier(n):
    return 'sparse' if n < D['sparse_max'] else 'dense' if n >= D['dense_min'] else 'standard'

def judge(family, tiers, data):
    n = load(data); t = tier(n)
    return {'load': n, 'tier': t, 'supported': list(tiers), 'judged': family in D['judged_families'],
            'mismatch': family in D['judged_families'] and t not in tiers}
