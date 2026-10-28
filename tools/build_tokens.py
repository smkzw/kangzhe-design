#!/usr/bin/env python3
"""Generate runtime tokens. The JSON is the single numeric/color authority."""
from pathlib import Path
import json, math
R = Path(__file__).resolve().parents[1]

def rgb(hex_color):
    c = hex_color.lstrip('#')
    return ','.join(str(int(c[i:i+2], 16)) for i in (0, 2, 4))

def stops(items):
    return ','.join(f'rgba({rgb(s["color"])},{s["alpha"]}) {s["offset"]*100:g}%' for s in items)

def bezier(v):
    return 'cubic-bezier(' + ','.join(f'{x:g}' for x in v) + ')'

def spring_linear(zeta, samples=28):
    """Step response of a damped spring, normalized so it settles (0.1%) at t=1, as CSS linear()."""
    if zeta < 1:
        w = math.log(1000) / zeta
        wd = w * math.sqrt(1 - zeta * zeta)
        def x(t):
            return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + zeta / math.sqrt(1 - zeta * zeta) * math.sin(wd * t))
    else:
        # Critically damped or overdamped: no oscillation; pick the natural frequency that leaves 0.1% at t=1.
        def step(w, t):
            if zeta == 1:
                return 1 - (1 + w * t) * math.exp(-w * t)
            wd = w * math.sqrt(zeta * zeta - 1)
            return 1 - math.exp(-zeta * w * t) * (math.cosh(wd * t) + zeta / math.sqrt(zeta * zeta - 1) * math.sinh(wd * t))
        lo, hi = 1.0, 500.0
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if 1 - step(mid, 1) > 1e-3 else (lo, mid)
        def x(t, w=hi):
            return step(w, t)
    pts = [f'{x(i / samples):.4f}' for i in range(samples)] + ['1']
    pts[0] = '0'
    return 'linear(' + ','.join(pts) + ')'

def shadow_static(layers, srgb):
    return ','.join(f'{x}px {y}px {b}px {s}px rgba({srgb},{a})' for x, y, b, s, a in layers)

def shadow_dynamic(rest, raised, offsets, srgb):
    """Interpolate rest→raised by --kz-lift; key/ambient layers move away from the pointer light (--kz-lx/--kz-ly)."""
    out = []
    for (r, h, (ox, oy)) in zip(rest, raised, offsets):
        def mix(i, unit='px'):
            a, b = r[i], h[i]
            return f'calc({a}{unit} + var(--kz-lift,0) * {b - a:g}{unit})' if a != b else f'{a}{unit}'
        x = f'calc({mix(0)} - var(--kz-lx,0) * {ox}px)' if ox else mix(0)
        y = f'calc({mix(1)} - var(--kz-ly,0) * {oy}px)' if oy else mix(1)
        alpha = f'calc({r[4]} + var(--kz-lift,0) * {h[4] - r[4]:.3f})'
        out.append(f'{x} {y} {mix(2)} {mix(3)} rgba({srgb},{alpha})')
    return ','.join(out)

def build():
    t = json.loads((R/'tokens/tokens.json').read_text())
    g, m, e = t['glass'], t['motion'], t['elevation']
    css = [':root {']
    for key, value in t['colors'].items(): css.append(f'  --kz-{key.replace("_","-")}: {value};')
    for key, value in t['type_px'].items(): css.append(f'  --kz-type-{key.replace("_","-")}: {value}px;')
    for key, value in t['departments'].items():
        css += [f'  --kz-{key}: {value["color"]};', f'  --kz-{key}-tint: {value["tint"]};']
    for label, stop in zip(['top','mid','bottom'], g['face_gradient']):
        css += [f'  --kz-face-{label}-rgb: {rgb(stop["color"])};', f'  --kz-face-{label}-alpha: {stop["alpha"]};', f'  --kz-face-{label}-offset: {stop["offset"]*100:g}%;']
    css += [f'  --kz-face-border-rgb: {rgb(g["border_color"])};', f'  --kz-face-border-alpha: {g["border_alpha"]};']
    rim = g['rim']
    css += [f'  --kz-thin-face: linear-gradient(145deg,{stops(g["thin"]["face_gradient"])});',
            f'  --kz-thin-border-alpha: {g["thin"]["border_alpha"]};',
            f'  --kz-carrier-face: linear-gradient(145deg,{stops(g["carrier_face_gradient"])});',
            f'  --kz-specular-radius: {g["specular"]["radius_pct"]}%;',
            f'  --kz-specular-alpha: {g["specular"]["alpha"]};',
            f'  --kz-specular-rest: {g["specular"]["rest_opacity"]};',
            f'  --kz-highlight-extent: {g["highlight_extent_max"]*100:g}%;',
            f'  --kz-saturate: {g["saturate_pct"]}%;']
    srgb = ','.join(map(str, e['shadow_rgb']))
    css.append(f'  --kz-shadow-rgb: {srgb};')
    for name, layers in e['levels'].items(): css.append(f'  --kz-elev-{name}: {shadow_static(layers, srgb)};')
    css.append(f'  --kz-elev-inset: inset {shadow_static([e["inset"]], srgb)};')
    css.append(f'  --kz-lift-px: {e["lift_px"]}px;')
    for name, v in m['easing'].items(): css.append(f'  --kz-ease-{name}: {bezier(v)};')
    css.append(f'  --kz-ease-spring: {spring_linear(m["spring"]["css_damping_ratio"])};')
    css.append(f'  --kz-dur-spring: {m["spring"]["css_duration_ms"]}ms;')
    for name, v in m['duration_ms'].items(): css.append(f'  --kz-dur-{name.replace("_","-")}: {v}ms;')
    for name, v in m['distance_px'].items(): css.append(f'  --kz-dist-{name}: {v}px;')
    css += [f'  --kz-perspective: {m["tilt"]["perspective_px"]}px;',
            f'  --kz-float-amplitude: {m["float"]["hero_px"]}px;',
            f'  --kz-float-period: {m["float"]["period_ms"]}ms;',
            f'  --kz-float-phase: {m["float"]["phase_step_ms"]}ms;',
            f'  --kz-mark-float-amplitude: {m["header_mark_float"]["px"]}px;',
            f'  --kz-mark-float-period: {m["header_mark_float"]["period_ms"]}ms;',
            f'  --kz-parallax-max: {m["parallax"]["field_max_px"]}px;']
    fold = t['layout']['fold']
    css += [f'  --kz-font: {t["fonts"]["fallback_css"]};',
            f'  --kz-radius: {g["radius"]}px;',
            f'  --kz-radius-compact: {g["radius_compact"]}px;',
            f'  --kz-radius-dialog: {g["radius_dialog"]}px;',
            f'  --kz-blur: {g["blur_px"]}px;',
            f'  --kz-gap: {t["rhythm"]["gap"]}px;',
            f'  --kz-gap-floor: {t["rhythm"]["gap_floor"]}px;',
            f'  --kz-pad: {t["rhythm"]["card_padding"]}px;',
            f'  --kz-pad-compact: {t["rhythm"]["card_padding_compact"]}px;',
            f'  --kz-line-body: {t["rhythm"]["line_height_body"]};',
            f'  --kz-line-title: {t["rhythm"]["line_height_title"]};',
            f'  --kz-measure: {t["wide"]["reading_measure_em"]}em;',
            f'  --kz-gutter: {t["wide"]["outer_gutter_vw"]}vw;',
            f'  --kz-fold-header: {fold["header_max_px"]}px;',
            f'  --kz-fold-gap: clamp({fold["gap_px"][0]}px,1.1vw,{fold["gap_px"][1]}px);',
            f'  --kz-reference-height: {t["wide"]["htmlppt_reference_height"]};',
            f'  --kz-dialog-width: {t["wide"]["dialog_width_vw"]}vw;',
            f'  --kz-dialog-max-height: {t["wide"]["dialog_height_vh"]}vh;',
            f'  --kz-lede-max: {fold["lede_max_em"]}em;']
    dense = t['layout']['dense']
    css += [f'  --kz-dense-head-max: {dense["head_max_vh"] * 100:g}vh;',
            f'  --kz-dense-stage-max: {dense["stage_max_vh"] * 100:g}vh;',
            f'  --kz-dense-gap: {dense["section_gap_px"]}px;',
            f'  --kz-chart-aspect: {dense["chart_aspect"]};']
    # Body-page chrome in canvas units (unitless): HTML-PPT multiplies by --kz-u, so the deck CSS holds no geometry.
    c, (cw, ch) = t['chrome'], t['units']['canvas_px']
    named = {'title': c['title'], 'logo': c['logo'], 'body': c['body'], 'mark': c['header_mark']['placement_htmlppt_u']}
    css += [f'  --kz-canvas-w: {cw};', f'  --kz-canvas-h: {ch};']
    for name, (x, y, w, h) in named.items():
        css += [f'  --kz-chrome-{name}-{k}: {v:g};' for k, v in zip('xywh', (x, y, w, h))]
    x1, y1, x2, _, stroke = c['rule']
    css += [f'  --kz-chrome-rule-x1: {x1:g};', f'  --kz-chrome-rule-y: {y1:g};', f'  --kz-chrome-rule-x2: {x2:g};', f'  --kz-chrome-rule-stroke: {stroke:g};']
    css += [f'  --kz-chrome-foot-{k}: {c["footer"][k]:g};' for k in ('left', 'right', 'bottom')]
    # Flagship route (14): type in logical px (deck CSS multiplies by --kz-un), geometry unitless (×--kz-u), motion in ms.
    f = t['flagship']
    css += [f'  --kzf-type-{k.replace("_","-")}: {v}px;' for k, v in f['type_px'].items()]
    css += [f'  --kzf-canvas: {f["canvas"]};', f'  --kzf-rule: {f["rule"]};', f'  --kzf-numeral-weight: {f["numeral_weight"]};',
            f'  --kzf-glass-face: linear-gradient(155deg,{stops(f["glass"]["face"])});',
            f'  --kzf-glass-face-clear: linear-gradient(155deg,{stops(f["glass"]["face_clear"])});',
            f'  --kzf-glass-rim-width: {f["glass"]["rim_width"]:g};', f'  --kzf-glass-rim-warm-rgb: {rgb(f["glass"]["rim_warm"])};',
            f'  --kzf-glass-caustic-alpha: {f["glass"]["caustic_alpha"]};', f'  --kzf-glass-spec-alpha: {f["glass"]["spec_alpha"]};',
            f'  --kzf-glass-shadow-rgb: {",".join(map(str, f["glass"]["shadow_rgb"]))};', f'  --kzf-glass-radius: {f["glass"]["radius"]:g};',
            f'  --kzf-paper-face: {f["paper"]["face"]};', f'  --kzf-paper-hairline: {f["paper"]["hairline"]};', f'  --kzf-paper-radius: {f["paper"]["radius"]:g};',
            '  --kzf-paper-shadow: {}px {}px {}px {}px rgba({},{});'.format(*f['paper']['shadow'][:4], ','.join(map(str, f['glass']['shadow_rgb'])), f['paper']['shadow'][4]),
            f'  --kzf-identity-logo-h: {f["identity"]["logo_height"]:g};', f'  --kzf-lens-fallback-blur: {f["lens"]["fallback_blur_px"]}px;',
            f'  --kzf-accent-ink: {f["accent_ink"]};', f'  --kzf-identity-gap: {f["identity"]["gap"]:g};',
            f'  --kzf-identity-mx: {f["identity"]["margin"][0]:g};', f'  --kzf-identity-my: {f["identity"]["margin"][1]:g};']
    css += [f'  --kzf-identity-pad-{side}: {v:g};' for side, v in zip('trbl', f['identity']['pad'])]
    css += [f'  --kzf-trans-{k[:-3].replace("_","-")}: {v}ms;' for k, v in f['transition'].items() if k.endswith('_ms')]
    en = f['entrance']
    css += [f'  --kzf-text-ms: {en["text_ms"]}ms;', f'  --kzf-glass-ms: {en["glass_ms"]}ms;', f'  --kzf-text-rise: {en["text_rise"]:g};',
            f'  --kzf-text-blur: {en["text_blur"]:g};', f'  --kzf-glass-rise: {en["glass_rise"]:g};', f'  --kzf-glass-scale-from: {en["glass_scale_from"]};']
    css.append('}')
    # Pointer-lit recipes read --kz-lx/--kz-ly/--kz-lift where they are declared, so they must be
    # declared on the lit element itself, not inherited from :root (custom properties substitute var() at declaration).
    css += ['.kz-card,.kz-lit {',
            f'  --kz-rim: linear-gradient(calc({rim["angle_deg"]}deg + var(--kz-lx,0) * {rim["angle_swing_deg"]}deg),{stops(rim["stops"])});',
            f'  --kz-shadow-dynamic: {shadow_dynamic(e["levels"]["rest"], e["levels"]["raised"], e["light_offset_px"], srgb)};', '}']
    (R/'runtime/kz-tokens.css').write_text('/* Generated by tools/build_tokens.py; do not edit. */\n'+'\n'.join(css)+'\n')
    (R/'runtime/kz-tokens.js').write_text('/* Generated. Numeric authority: tokens/tokens.json */\nwindow.KZ_TOKENS = '+json.dumps(t,ensure_ascii=False,separators=(',',':'))+';\n')
if __name__ == '__main__': build()
