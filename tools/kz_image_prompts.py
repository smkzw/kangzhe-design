#!/usr/bin/env python3
"""04 IMG-07/08: one prompt per background asset of a page-plan, in the Kangzhe composition contract.

    python3 "$KZ_DIR/tools/kz_image_prompts.py" page-plan.json --topic "2 型糖尿病周制剂 III 期方案讨论" [-o prompts.json]

Every prompt starts with the same style anchor (identical across the deck), then the page-kind contract: near-white
base; body backgrounds carry light only along the canvas edges and corners; cover, TOC, section and ending may carry
a pattern or object, but only outside the text zones, which are named by position. The topic must be a de-identified
visual concept (no protocol text, patient data or unpublished numbers; IMG-06). After generation run
tools/quiet_plate.py on each result (the `then` line) and use its output, not the raw image.
"""
from pathlib import Path
import argparse, json, sys
R = Path(__file__).resolve().parents[1]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))

ANCHOR = ('Style anchor (identical for every image in this deck): Kangzhe light liquid-glass optical material on a near-white '
          'field; translucent warm-white glass with soft refraction, thin bright rims and short highlights; colour only as faint '
          'refracted light in brand orange #FF9900 and secondary yellow #FFCC00; one soft light source from the upper left; calm, '
          'airy, formal medical style. No dark background, no neon, no saturated blue, green or purple, no text, numbers, logos or watermarks.')

def where(rect):
    """A 1280×720 rect as words the image model can follow."""
    x, y, w, h = rect; cx, cy = (x + w / 2) / 1280, (y + h / 2) / 720
    col = 'left' if cx < 0.38 else 'right' if cx > 0.62 else 'centre'; row = 'top' if cy < 0.36 else 'bottom' if cy > 0.64 else 'middle'
    return f'{row}-{col} band ({round(w / 12.8)}% of the width, {round(h / 7.2)}% of the height)'

BODY = ('CONTENT SLIDE background, {aspect}. The whole reading area, the central {body_w}% × {body_h}% of the canvas, is '
        'uniformly near-white and empty: no glass panels, rings, ribbons, folds, diagonal rays, caustic lines or orange/yellow clouds. '
        'Decoration lives only along the outer edges and corners, within about {band}% of the width from each edge: one or two faint '
        'warm refraction hints or a thin glass edge, fading to white toward the centre with no hard border. Keep the top-left '
        '(page mark), top-right (logo) and bottom strip (footer) clean. Theme hint, kept abstract: {topic}.')
HERO = ('{kind_name} background, {aspect}. Near-white base. A liquid-glass pattern or object that stands for "{topic}" may sit '
        'in the {subject}; keep it light and airy. Keep these text zones uniformly near-white and free of edges or highlights: '
        '{zones}. Nothing crosses the text zones; the composition reads as white space with decoration around it, not a full-bleed picture.')
KIND_NAME = {'cover': 'COVER', 'toc': 'TABLE OF CONTENTS', 'section': 'SECTION DIVIDER', 'ending': 'CLOSING'}

def text_zones(kind):
    lay = TOK['hero_layouts'][kind]
    return [lay[k] for k in ('title', 'subtitle', 'meta', 'grid', 'number') if k in lay]

def subject_of(kind):
    zs = text_zones(kind); bottom = max(y + h for x, y, w, h in zs); right = max(x + w for x, y, w, h in zs)
    if bottom < 470: return 'lower third and the right edge'
    if right < 900: return 'right third'
    return 'outer edges and corners'

def prompts(plan, topic, aspect='16:9'):
    out, seen = [], {}
    b = TOK['chrome']['body']; band = round(TOK['image']['quiet']['band_px'] / 12.8)
    for p in plan['pages']:
        img = p.get('image') or {}
        aid = img.get('asset_id') or f'{p["id"]}-bg'; kind = p['kind'] if p['kind'] in KIND_NAME else 'body'
        if aid in seen: seen[aid]['pages'].append(p['id']); continue
        if kind == 'body':
            text = BODY.format(aspect=aspect, body_w=round(b[2] / 12.8), body_h=round(b[3] / 7.2), band=band, topic=topic)
        else:
            text = HERO.format(kind_name=KIND_NAME[kind], aspect=aspect, topic=topic, subject=subject_of(kind),
                               zones='; '.join(where(z) for z in text_zones(kind)))
        rec = {'asset_id': aid, 'kind': kind, 'pages': [p['id']], 'prompt': ANCHOR + '\n\n' + text,
               'then': f'python3 "$KZ_DIR/tools/quiet_plate.py" <generated> images/{aid}.jpg --kind {kind} --receipt receipts/{aid}.quiet.json'}
        seen[aid] = rec; out.append(rec)
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('plan'); ap.add_argument('--topic', required=True, help='de-identified visual concept of the deck')
    ap.add_argument('--aspect', default='16:9'); ap.add_argument('-o', '--out')
    a = ap.parse_args()
    res = prompts(json.loads(Path(a.plan).read_text(encoding='utf-8')), a.topic, a.aspect)
    s = json.dumps(res, ensure_ascii=False, indent=1)
    Path(a.out).write_text(s, encoding='utf-8') if a.out else print(s)
    return 0

if __name__ == '__main__':
    sys.exit(main())
