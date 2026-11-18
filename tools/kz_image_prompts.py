#!/usr/bin/env python3
"""04 IMG-07/08/09: one prompt per background asset of a page-plan, in the Kangzhe composition contract (style A2).

    python3 "$KZ_DIR/tools/kz_image_prompts.py" page-plan.json --topic "2 型糖尿病周制剂 III 期方案讨论" [-o prompts.json]

Every prompt starts with the same style anchor (identical across the deck), then the page-kind contract: near-white
base; body backgrounds carry light only along the canvas edges and corners; cover, TOC, section and ending may carry
a pattern or object, but only outside the text zones, which are named by position. The topic must be a de-identified
visual concept (no protocol text, patient data or unpublished numbers; IMG-06). After generation run
tools/quiet_plate.py on each result (the `then` line) and use its output, not the raw image.

Two lessons from the 2026-11-17 generations are built in: every prompt begins with "Wide 16:9 landscape image" (left
out, the service returns other aspect ratios), and hero compositions name the empty region in plain proportions and
forbid the objects the model drifts to (a closing slide asked for a "loop" came back as a large glass bowl across the
message). Hero results are laid on the warm-paper ground with tools/kz_backdrop.py compose (one image serves 16:9 and
21:9) before the quiet check; always look at the composed page (04 IMG-03).
"""
from pathlib import Path
import argparse, json, sys
R = Path(__file__).resolve().parents[1]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))

ANCHOR = ('Wide 16:9 landscape image. Style anchor (identical for every image in this deck): Kangzhe light liquid-glass optical '
          'material on a near-white warm field (#FBF7F0); translucent warm-white glass with soft refraction, thin bright rims and short highlights; colour only as faint '
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
# style A2 hero compositions, as generated and approved on 2026-11-17 (provenance kept in the maintenance repository)
HERO = {
    'cover': ('COVER: one broad, soft, wide translucent glass-silk ribbon (about one fifth of the frame height wide) gracefully '
              'folding once, entering from the bottom edge at 62% width and leaving through the right edge near the top. The left 58% '
              'of the frame completely empty near-white for a title.'),
    'toc': ('TABLE OF CONTENTS: one long wide glass-silk ribbon lying low along the bottom-left edge of the frame, gently undulating, '
            'extending off the left edge, with a faint warm caustic below it. The upper 65% of the frame and the right 55% completely empty near-white.'),
    'section': ('SECTION DIVIDER: a single wide glass-silk ribbon curling softly in the lower right quarter of the frame, low and calm, '
                'with a faint warm caustic on the surface below. Everything above 45% height and left of 55% width completely empty near-white.'),
    'ending': ('CLOSING SLIDE: a single slim flat glass-silk ribbon lying horizontally along the very bottom edge of the frame, gently '
               'undulating from the lower left to the lower right, entirely inside the bottom 22% of the frame, low and flat like a ribbon '
               'resting on a table, soft warm caustic just beneath it. Absolutely nothing above the bottom quarter: the upper 78% of the '
               'frame is an empty, smooth, evenly lit near-white field. No bowl, no ring, no vessel.'),
}
HERO_TOPIC = (' The ribbon may echo "{topic}" only in its rhythm and shape; no literal objects, organs, molecules, devices or symbols. '
              'Keep these text zones uniformly near-white and free of edges or highlights: {zones}.')
KIND_NAME = {'cover': 'COVER', 'toc': 'TABLE OF CONTENTS', 'section': 'SECTION DIVIDER', 'ending': 'CLOSING'}

def text_zones(kind):
    lay = TOK['hero_layouts'][kind]
    return [lay[k] for k in ('title', 'subtitle', 'meta', 'grid', 'number') if k in lay]

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
            text = HERO[kind] + HERO_TOPIC.format(topic=topic, zones='; '.join(where(z) for z in text_zones(kind)))
        then = (f'python3 "$KZ_DIR/tools/quiet_plate.py" <generated> images/{aid}.jpg --kind {kind} --receipt receipts/{aid}.quiet.json' if kind == 'body' else
                f'python3 "$KZ_DIR/tools/kz_backdrop.py" compose <generated> --kind {kind} --size 2560x1440 --out images/{aid}.jpg --receipt receipts/{aid}.compose.json && '
                f'python3 "$KZ_DIR/tools/kz_backdrop.py" compose <generated> --kind {kind} --size 2560x1080 --out images/{aid}-wide.jpg && '
                f'python3 "$KZ_DIR/tools/quiet_plate.py" --check images/{aid}.jpg --kind {kind} --receipt receipts/{aid}.quiet.json')
        rec = {'asset_id': aid, 'kind': kind, 'pages': [p['id']], 'prompt': ANCHOR + '\n\n' + text, 'then': then}
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
