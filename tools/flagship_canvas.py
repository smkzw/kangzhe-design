#!/usr/bin/env python3
"""Flagship F1 canvas (14 FLAG-03/10): the warm-white page ground of the flagship route as an image, for PPTX pages and
static fallbacks. Same values as the HTML canvas (--kzf-canvas, from tokens.flagship.canvas): a vertical two-colour
gradient with two soft warm glows. Deterministic; a light ordered dither keeps the gradient free of banding.

    python3 tools/flagship_canvas.py out.png [--size 2560x1440] [--json]

As a module: render(w, h) -> PIL.Image (RGB). The receipt (--json) carries the parameters and the SHA-256 for the asset
manifest (04 IMG-02).
"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]
TOK = json.loads((R / 'tokens/tokens.json').read_text(encoding='utf-8'))

def _rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)

def falloff(d):
    """Glow opacity factor at normalised distance d: 1 at the centre, smoothstep to 0 at 0.7."""
    t = np.clip(1 - np.asarray(d, dtype=np.float64) / .7, 0, 1)
    return t * t * (3 - 2 * t)

def render(w, h):
    c = TOK['flagship']['canvas']
    y = np.linspace(0, 1, h)[:, None, None]
    img = _rgb(c['top']) * (1 - y) + _rgb(c['bottom']) * y
    img = np.broadcast_to(img, (h, w, 3)).copy()
    xs, ys = np.meshgrid(np.arange(w) + .5, np.arange(h) + .5)
    for gl in c['glows']:
        # Smoothstep falloff to 0 at 70% of the radius; the CSS canvas samples the same curve as gradient stops.
        cx, cy = gl['at'][0] * w, gl['at'][1] * h
        rx, ry = gl['size'][0] * w, gl['size'][1] * h
        d = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
        a = falloff(d) * gl['alpha']
        img = img * (1 - a[..., None]) + _rgb(gl['color']) * a[..., None]
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - .5
    img = img + np.tile(bayer, (h // 4 + 1, w // 4 + 1))[:h, :w, None]
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8), 'RGB')

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out'); ap.add_argument('--size', default='2560x1440'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args(); w, h = map(int, a.size.lower().split('x'))
    out = Path(a.out); img = render(w, h)
    img.save(out, quality=TOK['image']['backdrop']['jpeg_quality'], optimize=True) if out.suffix.lower() in ('.jpg', '.jpeg') else img.save(out, optimize=True)
    receipt = {'tool': 'tools/flagship_canvas.py', 'size': [w, h], 'canvas': TOK['flagship']['canvas'], 'file': str(out),
               'sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'tokens_version': TOK['version']}
    print(json.dumps(receipt, ensure_ascii=False, indent=1) if a.json else f'{out}  {w}×{h}  sha256 {receipt["sha256"][:12]}…')

if __name__ == '__main__':
    main()
