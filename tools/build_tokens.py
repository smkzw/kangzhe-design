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
    w = math.log(1000) / zeta
    wd = w * math.sqrt(1 - zeta * zeta)
    def x(t):
        return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + zeta / math.sqrt(1 - zeta * zeta) * math.sin(wd * t))
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
            f'  --kz-measure: {t["wide"]["reading_measure_ch"]}ch;',
            f'  --kz-gutter: {t["wide"]["outer_gutter_vw"]}vw;',
            f'  --kz-fold-header: {fold["header_max_px"]}px;',
            f'  --kz-fold-gap: clamp({fold["gap_px"][0]}px,1.1vw,{fold["gap_px"][1]}px);',
            f'  --kz-reference-height: {t["wide"]["htmlppt_reference_height"]};',
            f'  --kz-dialog-width: {t["wide"]["dialog_width_vw"]}vw;',
            f'  --kz-dialog-max-height: {t["wide"]["dialog_height_vh"]}vh;', '}']
    # Pointer-lit recipes read --kz-lx/--kz-ly/--kz-lift where they are declared, so they must be
    # declared on the lit element itself, not inherited from :root (custom properties substitute var() at declaration).
    css += ['.kz-card,.kz-lit {',
            f'  --kz-rim: linear-gradient(calc({rim["angle_deg"]}deg + var(--kz-lx,0) * {rim["angle_swing_deg"]}deg),{stops(rim["stops"])});',
            f'  --kz-shadow-dynamic: {shadow_dynamic(e["levels"]["rest"], e["levels"]["raised"], e["light_offset_px"], srgb)};', '}']
    (R/'runtime/kz-tokens.css').write_text('/* Generated by tools/build_tokens.py; do not edit. */\n'+'\n'.join(css)+'\n')
    (R/'runtime/kz-tokens.js').write_text('/* Generated. Numeric authority: tokens/tokens.json */\nwindow.KZ_TOKENS = '+json.dumps(t,ensure_ascii=False,separators=(',',':'))+';\n')
if __name__ == '__main__': build()
