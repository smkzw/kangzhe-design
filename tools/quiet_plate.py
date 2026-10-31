#!/usr/bin/env python3
"""04 IMG-08: put a generated background onto a white base by page kind, then measure the reading zone.

    python3 "$KZ_DIR/tools/quiet_plate.py" generated.png out.jpg --kind body  [--receipt r.json] [--zones zones.json]
    python3 "$KZ_DIR/tools/quiet_plate.py" generated.png out.jpg --kind cover [--receipt r.json]
    python3 "$KZ_DIR/tools/quiet_plate.py" --check out.jpg --kind body           # measure only

body: only an edge band survives (strongest in the corners, fading to white within tokens.image.quiet.band_px
of each edge); cover / toc / section / ending: the image stays, and the text zones (tokens.hero_layouts, or
--zones [[x,y,w,h], …] on the 1280×720 canvas) are lifted to white with a feathered edge. The reading zone (body:
tokens.chrome.body; hero: the text zones) is then measured: luminance standard deviation, mean lightness and the
coloured-pixel share must stay inside tokens.image.quiet. Exit 1 when the plate fails; regenerate, or fall back to
the default background set through the IMG-07 gate (tell the user).
"""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
from PIL import Image, ImageFilter
R = Path(__file__).resolve().parents[1]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
Q = TOK['image']['quiet']
HERO = TOK['hero_layouts']

def zones(kind, extra=None):
    if extra: return extra
    if kind == 'body': return [TOK['chrome']['body']]
    lay = HERO[kind]
    return [lay[k] for k in ('title', 'subtitle', 'meta', 'grid', 'number') if k in lay]

def view(size):
    """Pages draw the plate with preserveAspectRatio xMidYMid slice (cover): one scale, centred, overflow cropped.
    → (scale, offset x, offset y) mapping canvas coordinates to image pixels."""
    W, H = size; k = max(W / 1280, H / 720)
    return k, (W - 1280 * k) / 2, (H - 720 * k) / 2

def rect_mask(size, rects, feather):
    k, ox, oy = view(size)
    m = Image.new('L', size, 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(m)
    pad = Q['zone_pad_px']
    for x, y, w, h in rects:
        d.rectangle([ox + (x - pad) * k, oy + (y - pad) * k, ox + (x + w + pad) * k, oy + (y + h + pad) * k], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather * k)) if feather else m

def edge_mask(size):
    """1 at the canvas edge, 0 beyond band_px inside; corners keep the most (product of the two axes' falloff)."""
    W, H = size; k, ox, oy = view(size); band = Q['band_px']
    x = (np.arange(W)[None, :] - ox) / k; y = (np.arange(H)[:, None] - oy) / k  # canvas coordinates of each pixel
    dx = np.maximum(np.minimum(x, 1280 - x), 0) / band; dy = np.maximum(np.minimum(y, 720 - y), 0) / band
    fx = np.clip(1 - dx, 0, 1); fy = np.clip(1 - dy, 0, 1)
    m = np.maximum(fx, fy) * Q['edge_keep'] + fx * fy * (1 - Q['edge_keep'])
    m = np.clip(m, 0, 1) ** Q['falloff_gamma']
    return m * m * (3 - 2 * m)  # smoothstep: no visible inner rim where the band ends

def flat(img):
    """RGB on white: transparent pixels of an RGBA/LA/P image become white, not black."""
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        rgba = img.convert('RGBA'); bg = Image.new('RGBA', rgba.size, (255, 255, 255, 255)); bg.alpha_composite(rgba)
        return bg.convert('RGB')
    return img.convert('RGB')

def compose(img, kind, extra=None):
    im = flat(img); a = np.asarray(im, dtype=np.float32)
    white = np.full_like(a, 255.0)
    if kind == 'body':
        keep = edge_mask(im.size)
    else:
        keep = np.ones(a.shape[:2], dtype=np.float32)
    if kind != 'body' or extra:  # hero text zones (or zones given explicitly) are lifted to white
        lift = np.asarray(rect_mask(im.size, zones(kind, extra), Q['feather_px']), dtype=np.float32) / 255
        keep = keep * (1 - lift)
    out = white * (1 - keep[..., None]) + a * keep[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def measure(img, kind, extra=None):
    im = flat(img); k, ox, oy = view(im.size)
    res = []
    for x, y, w, h in zones(kind, extra):
        crop = im.crop((int(ox + x * k), int(oy + y * k), int(ox + (x + w) * k), int(oy + (y + h) * k)))
        crop.thumbnail((Q['sample_px'], Q['sample_px']))
        L = np.asarray(crop.convert('L'), dtype=np.float32)
        hsv = np.asarray(crop.convert('HSV'), dtype=np.float32) / 255
        colored = float(((hsv[..., 1] > TOK['image']['style']['saturation_min']) & (hsv[..., 2] > TOK['image']['style']['value_min'])).mean())
        res.append({'zone': [x, y, w, h], 'luminance_std': round(float(L.std()), 2), 'mean_lightness': round(float(L.mean()), 1), 'colored_share': round(colored, 4)})
    lim = Q['body'] if kind == 'body' else Q['hero']
    fails = [f'{r["zone"]}: {k}' for r in res for k, ok in (('luminance_std', r['luminance_std'] <= lim['luminance_std_max']),
                                                             ('mean_lightness', r['mean_lightness'] >= lim['mean_lightness_min']),
                                                             ('colored_share', r['colored_share'] <= lim['colored_share_max'])) if not ok]
    return res, fails

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst', nargs='?')
    ap.add_argument('--kind', required=True, choices=['body', 'cover', 'toc', 'section', 'ending'])
    ap.add_argument('--zones', help='JSON file: [[x,y,w,h], …] on the 1280×720 canvas (default: from tokens)')
    ap.add_argument('--check', action='store_true', help='measure src only')
    ap.add_argument('--receipt')
    a = ap.parse_args()
    extra = json.loads(Path(a.zones).read_text()) if a.zones else None
    src = Image.open(a.src)
    if a.check: out, dst = src, a.src
    else:
        if not a.dst: ap.error('dst is required unless --check')
        out = compose(src, a.kind, extra); dst = a.dst
        out.save(dst, quality=92) if dst.lower().endswith(('.jpg', '.jpeg')) else out.save(dst)
    res, fails = measure(out, a.kind, extra)
    rec = {'tool': 'quiet_plate', 'kind': a.kind, 'source': a.src, 'source_sha256': hashlib.sha256(Path(a.src).read_bytes()).hexdigest(),
           'output': dst, 'output_sha256': hashlib.sha256(Path(dst).read_bytes()).hexdigest(), 'size': list(out.size),
           'zones': res, 'limits': Q['body'] if a.kind == 'body' else Q['hero'], 'passed': not fails, 'failures': fails}
    if a.receipt: Path(a.receipt).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: rec[k] for k in ('kind', 'output', 'passed', 'failures')}, ensure_ascii=False))
    for r in res: print('  zone', r['zone'], 'std', r['luminance_std'], 'L', r['mean_lightness'], 'colored', r['colored_share'])
    return 0 if not fails else 1

if __name__ == '__main__':
    sys.exit(main())
