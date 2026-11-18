#!/usr/bin/env python3
"""04 IMG-09: the warm-paper ground of background style A and the A2 composition (a generated glass subject laid
onto that ground), for any page size. Values live in tokens.image.backdrop.

    python3 "$KZ_DIR/tools/kz_backdrop.py" ground  --kind body  --size 2560x1440 --out body.jpg
    python3 "$KZ_DIR/tools/kz_backdrop.py" compose generated.png --kind cover --size 2560x1080 --out cover-wide.jpg \
            [--scale 1.12] [--dy 0.07] [--receipt r.json]

ground: a vertical paper gradient, warm corner glows (one set for hero pages, a quieter one for body pages) and
a fine grain. compose: the generated image is scaled to the page height × scale, anchored to the right edge and
moved down by dy × height and laid over the ground (the generated field is already the paper colour); when the page is wider than the image, its left edge
fades into the ground over feather_pct of the image width (the ground fills the extra width, so one 16:9 image
serves 16:9 and 21:9 pages), and when it is moved down its top fades in over top_fade_pct. Per page kind the scale
and dy default to tokens.image.backdrop.placement — chosen so the subject stays out of the hero text zones; check the
result with tools/quiet_plate.py --check (04 IMG-08) and by eye (04 IMG-03) before using it.
"""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))
B = TOK['image']['backdrop']

def _rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)

def ground(kind, W, H, seed=7):
    """→ float32 H×W×3 array (0–255)."""
    g = B['ground']['body' if kind == 'body' else 'hero']
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = _rgb(g['top']) * (1 - t) + _rgb(g['bottom']) * t
    img = np.broadcast_to(img, (H, W, 3)).copy()
    k = H / 1080.0  # glow sizes are given for a 1080-high page
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    for cx, cy, rx, ry, colour, alpha in reversed(g['glows']):  # the first glow is drawn on top, as in CSS
        d = np.sqrt(((xs - cx * W) / (rx * k)) ** 2 + ((ys - cy * H) / (ry * k)) ** 2)
        a = (alpha * np.clip(1 - d / B['ground']['glow_reach'], 0, 1))[..., None]
        img = img * (1 - a) + _rgb(colour) * a
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, (H, W)).astype(np.float32)[..., None]
    img = img * (1 + B['ground']['grain'] * 0.5 * np.tanh(noise))  # fine grain around 1, so it does not darken the page
    return np.clip(img, 0, 255)

def compose(gen, kind, W, H, scale=None, dy=None):
    """→ (PIL image, placement dict)."""
    p = B['placement'].get(kind, {'scale': 1, 'dy': 0})
    scale = p['scale'] if scale is None else scale; dy = p['dy'] if dy is None else dy
    base = ground(kind, W, H)
    src = gen.convert('RGB'); ih = round(H * scale); iw = round(ih * src.width / src.height)
    im = np.asarray(src.resize((iw, ih), Image.LANCZOS), dtype=np.float32)
    x0 = W - iw; y0 = round(H * dy)
    # crop the placed image to the page
    sx0, sy0 = max(0, -x0), max(0, -y0); dx0, dy0 = max(0, x0), max(0, y0)
    w = min(iw - sx0, W - dx0); h = min(ih - sy0, H - dy0)
    patch = im[sy0:sy0 + h, sx0:sx0 + w]
    m = np.ones((h, w), dtype=np.float32)
    if W > iw:  # left edge fades into the ground
        f = max(1, round(iw * B['feather_pct'] / 100)); ramp = np.clip((np.arange(w) + sx0) / f, 0, 1)
        m *= (ramp * ramp * (3 - 2 * ramp))[None, :]
    if y0 > 0:  # moved down: the top edge fades in
        f = max(1, round(ih * B['top_fade_pct'] / 100)); ramp = np.clip((np.arange(h) + sy0) / f, 0, 1)
        m *= (ramp * ramp * (3 - 2 * ramp))[:, None]
    region = base[dy0:dy0 + h, dx0:dx0 + w]
    base[dy0:dy0 + h, dx0:dx0 + w] = region * (1 - m[..., None]) + patch * m[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), {'scale': scale, 'dy': dy, 'image_box': [x0, y0, iw, ih]}

def _size(s):
    w, h = s.lower().split('x'); return int(w), int(h)

def _save(img, out):
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in ('.jpg', '.jpeg'): img.save(out, quality=B['jpeg_quality'], optimize=True, progressive=True)
    else: img.save(out)
    return hashlib.sha256(out.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('ground'); g.add_argument('--kind', required=True, choices=['cover', 'toc', 'section', 'ending', 'body'])
    g.add_argument('--size', required=True); g.add_argument('--out', required=True)
    c = sub.add_parser('compose'); c.add_argument('image'); c.add_argument('--kind', required=True, choices=['cover', 'toc', 'section', 'ending'])
    c.add_argument('--size', required=True); c.add_argument('--out', required=True)
    c.add_argument('--scale', type=float); c.add_argument('--dy', type=float); c.add_argument('--receipt')
    a = ap.parse_args()
    W, H = _size(a.size)
    if a.cmd == 'ground':
        sha = _save(Image.fromarray(ground(a.kind, W, H).astype(np.uint8)), a.out)
        print(json.dumps({'out': a.out, 'kind': a.kind, 'size': [W, H], 'sha256': sha}, ensure_ascii=False)); return 0
    src = Image.open(a.image)
    img, place = compose(src, a.kind, W, H, a.scale, a.dy)
    sha = _save(img, a.out)
    rec = {'source': a.image, 'source_sha256': hashlib.sha256(Path(a.image).read_bytes()).hexdigest(), 'source_size': list(src.size),
           'out': a.out, 'sha256': sha, 'kind': a.kind, 'size': [W, H], 'placement': place,
           'upscaled': src.height < H * place['scale']}
    if a.receipt: Path(a.receipt).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(rec, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
