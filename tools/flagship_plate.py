#!/usr/bin/env python3
"""Render a flagship light plate (14 FLAG-10): the HTML light field, frozen, as a PNG for PPTX backgrounds and
static fallbacks. Same field and page-role light levels as runtime/kz-flagship.js, every number from
tokens.flagship; deterministic for the same arguments (no clock, no randomness).

    python3 tools/flagship_plate.py --kind content --focus 0.80,0.40 \
        --calm 0.078,0.27,0.65,0.91 --pool 0.88,0.42,0.30 --out p05.png --receipt p05.json

Coordinates are page fractions with the origin at the top left: --focus x,y; --calm x0,y0,x1,y1 (repeatable, the
reading areas of a content page); --pool cx,cy,r (r in page-height units, the one focal object). The receipt records
the arguments, size and SHA-256 for the asset manifest. lens() bakes the glass of one PPTX lens from a plate.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]

def _tokens():
    return json.loads((ROOT / 'tokens/tokens.json').read_text(encoding='utf-8'))['flagship']

def _rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)

def _fract(x):
    return x - np.floor(x)

def _hash(px, py):
    px, py = _fract(px * np.float32(123.34)), _fract(py * np.float32(456.21))
    d = px * (px + np.float32(45.32)) + py * (py + np.float32(45.32))
    return _fract((px + d) * (py + d))

def _noise(px, py):
    ix, iy = np.floor(px), np.floor(py); fx, fy = px - ix, py - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _hash(ix, iy), _hash(ix + 1, iy), _hash(ix, iy + 1), _hash(ix + 1, iy + 1)
    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uy

def _fbm(px, py):
    v = np.zeros_like(px); a = np.float32(0.5)
    for _ in range(5):
        v += a * _noise(px, py)
        px, py = np.float32(1.6) * px - np.float32(1.2) * py, np.float32(1.2) * px + np.float32(1.6) * py  # GLSL mat2(1.6,1.2,-1.2,1.6) * p
        a *= np.float32(0.5)
    return v

def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def render(kind, focus, calm=(), pool=None, river=None, size=None, time_s=None):
    """Return a PIL RGB image of the settled light field for one page (transition progress 1)."""
    T = _tokens(); fd, L, C = T['field'], T['levels'], T['light']
    W, H = size or T['plate']['size_px']; k = T['plate']['render_scale']
    w, h = max(16, round(W * k)), max(16, round(H * k))
    t = np.float32(T['plate']['time_s'] if time_s is None else time_s)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = (xs + 0.5) / w, (ys + 0.5) / h                       # uv, origin top left (as the shader after its flip)
    asp = np.float32(W / H)
    px, py = u * asp * fd['scale'], v * fd['scale']
    s = t * np.float32(fd['speed'])
    qx, qy = _fbm(px, py + s), _fbm(px + 5.2 - s, py + 1.3 - s)
    rx = _fbm(px + fd['warp'][0] * qx + 1.7 + s * 0.6, py + fd['warp'][0] * qy + 9.2 + s * 0.6)
    ry = _fbm(px + fd['warp'][0] * qx + 8.3 - s * 0.4, py + fd['warp'][0] * qy + 2.8 - s * 0.4)
    val = _fbm(px + fd['warp'][1] * rx, py + fd['warp'][1] * ry)
    fx, fy = (u - focus[0]) * asp, v - focus[1]
    near = np.exp(-(fx * fx + fy * fy) * fd['near_falloff'])
    canvas = _rgb(T['canvas'])
    gl = _smooth(*fd['body_threshold'], val)
    deep = _smooth(fd['deep_threshold'][0], fd['deep_threshold'][1], val)[..., None]
    light = _rgb(C['honey']) * (1 - deep) + _rgb(C['deep']) * deep
    amt = np.clip(gl * (0.30 + 1.30 * near), 0, 0.95)[..., None]
    col = canvas * (1 - amt) + light * amt
    col += (gl ** 3 * near)[..., None] * _rgb(C['body_boost'])
    band = np.abs(_fract(val * fd['ribbon_bands'] - s * 0.6) - 0.5)
    ribbon = np.exp(-band * band * fd['ribbon_sharpness'])
    col += (ribbon * (0.12 + 0.60 * near))[..., None] * _rgb(C['core_line'])
    ra, rb = river or T['river'].get(kind, T['river']['content'])
    flow = v - (ra - rb * u) + (val - 0.5) * fd['river_jitter'] + 0.045 * np.sin(u * 4.0 + s * 2.6)
    rv = np.exp(-flow * flow * fd['river_width'])[..., None]
    rcol = _rgb(C['river_edge']) * (1 - rv) + _rgb(C['river_core']) * rv
    ramt = rv * 0.78 * (0.55 + 0.7 * near)[..., None]
    col = col * (1 - ramt) + rcol * ramt
    col += np.exp(-flow * flow * fd['river_core_width'])[..., None] * _rgb(C['core_line']) * 0.55
    quiet = (_smooth(0.60, 0.05, u) * _smooth(0.05, 0.45, 1.0 - np.abs(v - 0.40) * 1.7))[..., None] * fd['quiet_mix']
    col = col * (1 - quiet) + canvas * quiet
    # page-role level (14 FLAG-03), settled state (e = 1, no transition wave)
    lvl = L['by_kind'].get(kind, 1); G = L['gain']
    gain = np.full((h, w), (G['section'] + (G['hero'] - G['section']) * (lvl - 2)) if lvl >= 2 else (G['content_margin'] + (G['section'] - G['content_margin']) * (lvl - 1)), dtype=np.float32)
    if lvl < 2 and calm:
        calm_m = np.zeros((h, w), dtype=np.float32)
        for x0, y0, x1, y1 in calm[:L['max_calm_rects']]:
            dx, dy = np.maximum(np.maximum(x0 - u, u - x1), 0) * asp, np.maximum(np.maximum(y0 - v, v - y1), 0)
            calm_m = np.maximum(calm_m, 1 - _smooth(0.0, L['mask_feather_uv'], np.sqrt(dx * dx + dy * dy)))
        gain *= 1 - calm_m * min(1.0, 2.0 - lvl) * L['card_calm']
    if pool:
        pdx, pdy = (u - pool[0]) * asp, v - pool[1]
        gain = np.maximum(gain, np.exp(-(pdx * pdx + pdy * pdy) / (pool[2] * pool[2])) * L['pool_gain'])
    col = canvas + (col - canvas) * gain[..., None]
    img = Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
    if (w, h) != (W, H):
        img = img.resize((W, H), Image.BICUBIC)
    # ordered dither after upscaling keeps the low-frequency gradients free of banding, deterministically
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16 - 0.5
    arr = np.asarray(img, dtype=np.float32) + np.tile(bayer, (H // 4 + 1, W // 4 + 1))[:H, :W, None]
    return Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8), 'RGB')

def _saturate(a, s):
    g = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    return g + (a - g) * s

def lens(plate, box, rad, role):
    """Bake one lens for PowerPoint (14 FLAG-10), which cannot filter what lies behind a shape. Port of the runtime's
    SVG lens filter (kz-flagship.js lensMap + filter): the plate under the shape is refracted and saturated in the rim
    band and frosted, desaturated and lifted in the reading area, with the same tokens.flagship.lens values. box
    (x, y, w, h) and rad are in 1280×720 page units; returns RGBA at plate resolution, transparent outside the shape."""
    L = _tokens()['lens']; bevel, refract, frost = L['roles'][role]
    s = plate.width / 1280
    X, Y, W, H = (round(v * s) for v in box); R, B, D = rad * s, max(2.0, bevel * s), refract * s
    pad = int(max(D, 3 * frost * s)) + 2
    src = np.pad(np.asarray(plate.convert('RGB')), ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    region = Image.fromarray(src[Y:Y + H + 2 * pad, X:X + W + 2 * pad])
    blur = lambda r: np.asarray(region.filter(ImageFilter.GaussianBlur(r)) if r > 0 else region, dtype=np.float32)
    centre = _saturate(blur(frost * s)[pad:pad + H, pad:pad + W], L['frost_saturate']) * L['frost_lift'][0] + 255 * L['frost_lift'][1]
    # signed distance to the rounded rectangle, normal and convex rim profile, as lensMap
    j, i = np.mgrid[0:H, 0:W].astype(np.float32)
    px, py = i + 0.5 - W / 2, j + 0.5 - H / 2
    qx, qy = np.abs(px) - (W / 2 - R), np.abs(py) - (H / 2 - R)
    depth = -(np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - R)
    l = np.maximum(np.hypot(qx, qy), 1e-6); corner = (qx > 0) & (qy > 0)
    nx = np.where(corner, qx / l * np.sign(px), np.where(qx > qy, np.sign(px), 0))
    ny = np.where(corner, qy / l * np.sign(py), np.where(qx > qy, 0, np.sign(py)))
    m = np.where((depth >= 0) & (depth < B), (1 - np.clip(depth / B, 0, 1)) ** 2.2, 0)
    # feDisplacementMap: P'(x, y) = P(x + scale·(R − ½), y + scale·(G − ½)), map channel = 128 + n·m·127
    sx = np.clip(np.rint(i + pad + D * nx * m * 127 / 255), 0, W + 2 * pad - 1).astype(int)
    sy = np.clip(np.rint(j + pad + D * ny * m * 127 / 255), 0, H + 2 * pad - 1).astype(int)
    rim_rgb = _saturate(blur(L['frost_px'] * s)[sy, sx], L['saturate'])
    t = depth / B; b0, b1 = L['rim_band']
    rim = np.where(depth < 0, 0, np.clip(1 - (t - b0) / (b1 - b0), 0, 1)); rim = (rim * rim * (3 - 2 * rim))[..., None]
    rgb = np.clip(centre * (1 - rim) + rim_rgb * rim, 0, 255)
    alpha = np.clip(depth + 0.5, 0, 1) * 255
    return Image.fromarray(np.concatenate([rgb, alpha[..., None]], -1).round().astype(np.uint8), 'RGBA')

def save(img, path):
    """PNG, or JPEG (quality 92, no chroma subsampling) for .jpg/.jpeg — the plates are smooth gradients, JPEG keeps decks small."""
    path = Path(path)
    if path.suffix.lower() in ('.jpg', '.jpeg'): img.save(path, quality=92, subsampling=0, optimize=True)
    else: img.save(path, optimize=True)

def _pair(s, n):
    vals = [float(x) for x in s.split(',')]
    if len(vals) != n: raise argparse.ArgumentTypeError(f'需要 {n} 个逗号分隔的数')
    return vals

def main(argv=None):
    T = _tokens()
    ap = argparse.ArgumentParser(description='Render a flagship light plate (14 FLAG-10).')
    ap.add_argument('--kind', required=True, choices=sorted(T['levels']['by_kind']))
    ap.add_argument('--focus', required=True, type=lambda s: _pair(s, 2))
    ap.add_argument('--calm', action='append', default=[], type=lambda s: _pair(s, 4), help='reading area x0,y0,x1,y1 (repeatable)')
    ap.add_argument('--pool', type=lambda s: _pair(s, 3), help='focal object cx,cy,r')
    ap.add_argument('--river', type=lambda s: _pair(s, 2), help='override river a,b (y = a - b*x)')
    ap.add_argument('--size', type=lambda s: [int(x) for x in s.lower().split('x')], help='WxH, default tokens.flagship.plate.size_px')
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--receipt', type=Path)
    a = ap.parse_args(argv)
    img = render(a.kind, a.focus, a.calm, a.pool, a.river, a.size)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    save(img, a.out)
    rec = {'tool': 'tools/flagship_plate.py', 'kind': a.kind, 'focus': a.focus, 'calm': a.calm, 'pool': a.pool, 'river': a.river,
           'size_px': list(img.size), 'time_s': T['plate']['time_s'], 'file': a.out.name, 'sha256': hashlib.sha256(a.out.read_bytes()).hexdigest()}
    if a.receipt: a.receipt.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(rec, ensure_ascii=False))

if __name__ == '__main__':
    main()
