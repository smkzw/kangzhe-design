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

def flagship_css(f):
    """14 FLAG (F1): custom properties for runtime/kz-flagship.css, all from tokens.flagship."""
    grad = lambda st, ang: f'linear-gradient({ang}deg,' + ','.join(f'{c} {o*100:g}%' for c, o in st) + ')'
    u = lambda v: f'calc({v:g} * var(--kz-u,1px))' if v else '0'
    shadow = lambda layers: ','.join(f'{u(x)} {u(y)} {u(b)} {u(sp)} {c}' for x, y, b, sp, c in layers)
    cv, g, k = f['canvas'], f['geometry'], f['card']
    ss = lambda d: (lambda t: t * t * (3 - 2 * t))(max(0.0, min(1.0, 1 - d / .7)))  # same falloff as tools/flagship_canvas.py
    glows = ','.join(f'radial-gradient({w["size"][0]*100:g}vw {w["size"][1]*100:g}vh at {w["at"][0]*100:g}% {w["at"][1]*100:g}%,'
                     + ','.join(f'rgba({rgb(w["color"])},{w["alpha"] * ss(d):.3f}) {d*100:g}%' for d in (0, .14, .28, .42, .56, .7)) + ')' for w in cv['glows'])
    out = [f'  --kzf-type-{n.replace("_", "-")}: {v}px;' for n, v in f['type_px'].items()]
    out += [f'  --kzf-ink-{n}: {v};' for n, v in f['ink'].items() if not n.startswith('_')]
    out += [f'  --kzf-g-{n.replace("_", "-")}: {v:g};' for n, v in g.items() if not n.startswith('_') and not isinstance(v, list)]
    out += [f'  --kzf-g-card-pad-y: {g["card_pad"][0]:g};', f'  --kzf-g-card-pad-x: {g["card_pad"][1]:g};',
            f'  --kzf-canvas: {glows},linear-gradient(180deg,{cv["top"]},{cv["bottom"]});', f'  --kzf-canvas-flat: {cv["bottom"]};',
            f'  --kzf-card-face: {k["face"]};', f'  --kzf-card-border: {k["border"]};', f'  --kzf-card-radius: {k["radius"]:g};',
            f'  --kzf-card-shadow: {shadow(k["shadow"])};', f'  --kzf-card-shadow-raised: {shadow(k["shadow_raised"])};',
            f'  --kzf-head-face: {f["head"]["face"]};', f'  --kzf-head-border: {f["head"]["border"]};', f'  --kzf-head-radius: {f["head"]["radius"]:g};',
            f'  --kzf-head-num: {f["head"]["num"]};', f'  --kzf-tile: {grad(f["tile"]["stops"], 140)};',
            f'  --kzf-mark-w: {f["mark"]["w"]:g};', f'  --kzf-mark-h: {f["mark"]["h"]:g};',
            f'  --kzf-mark-icon-x: {f["mark"]["icon_at"][0] / f["mark"]["view"][0]:.4f};', f'  --kzf-mark-icon-y: {f["mark"]["icon_at"][1] / f["mark"]["view"][1]:.4f};',
            f'  --kzf-mark-icon: {f["mark"]["icon"] / f["mark"]["view"][0]:.4f};', f'  --kzf-mark-icon-ink: {f["mark"]["icon_ink"]};', f'  --kzf-mark-icon-stroke: {f["mark"]["icon_stroke"]:g};',
            '  --kzf-mark-shadow: {0}px {1}px {2}px {3};'.format(*f["mark"]["shadow"]),
            f'  --kzf-chip-face: {f["chip"]["face"]};', f'  --kzf-chip-border: {f["chip"]["border"]};', f'  --kzf-chip-ink: {f["chip"]["ink"]};',
            f'  --kzf-pill-face: {f["pill"]["face"]};', f'  --kzf-pill-border: {f["pill"]["border"]};', f'  --kzf-line: {f["line"]};',
            f'  --kzf-numeral: {grad(f["numeral"]["stops"], 165)};', f'  --kzf-numeral-weight: {f["numeral"]["weight"]};',
            f'  --kzf-numeral-pad: {f["numeral"]["pad_em"]:g}em;',
            '  --kzf-numeral-depth: ' + ' '.join('drop-shadow({0} {0} 0 {1})'.format(f'min({f["numeral"]["extrude_step_em"]:g}em, {f["numeral"]["extrude_step_max_px"]:g}px)', c) for c in f["numeral"]["extrude"])
            + ' drop-shadow({0}em {1:g}em {2:g}em {3})'.format(*f["numeral"]["ground"]) + ';',
            f'  --kzf-rule: {grad(f["rule"]["stops"], 90)};', f'  --kzf-rule-h: {f["rule"]["height"]:g};',
            f'  --kzf-prog-track: {f["progress"]["track"]};', f'  --kzf-prog-on: {grad(f["progress"]["on"], 90)};',
            f'  --kzf-prog-h: {f["progress"]["height"]:g};', f'  --kzf-prog-gap: {f["progress"]["gap"]:g};',
            f'  --kzf-accent-ink: {f["accent_ink"]};', f'  --kzf-exit-ms: {f["motion"]["page_exit_ms"]}ms;']
    out += [f'  --kzf-tag-{n}-bg: {bg};\n  --kzf-tag-{n}-ink: {fg};' for n, (bg, fg) in ((n, v) for n, v in f['tag'].items() if not n.startswith('_'))]
    return out

def wide_css(t):
    """13 WIDE-01: the site/stream widescreen variables. Breakpoints live here (media queries cannot read variables),
    generated from tokens.wide so CSS and tokens cannot drift."""
    w = t['wide']; ts = w['type_scale']
    k = (ts['to'] - 1) / (ts['to_vw'] - ts['from_vw'])            # scale per px of viewport width
    a = 1 - k * ts['from_vw']                                       # scale = a + k × 100vw
    # --kz-sx is one CSS px scaled with the width (a length, so it multiplies plain numbers: calc(18 * var(--kz-sx)))
    out = [':root {', f'  --kz-sx: clamp(1px, calc({a:.4f}px + {k * 100:.5f}vw), {ts["max"]}px);',
           f'  --kz-site-head-h: {w["header_px"][0][1]}px;', f'  --kz-logo-h: {w["logo_px"][0][1]}px;', '  --kz-sheet-cols: 12;',
           f'  --kz-stream-rail: clamp({w["stream_rail"][0]}px,{w["stream_rail"][1]}vw,{w["stream_rail"][2]}px);',
           f'  --kz-stream-measure: {w["stream_measure_em"]}em;', '}']
    steps = sorted({v for v, _ in w['header_px'] + w['logo_px'] if v} | {w['xl_min_vw']})
    for v in steps:
        decl = [f'--kz-site-head-h: {h}px;' for bp, h in w['header_px'] if bp == v] + [f'--kz-logo-h: {h}px;' for bp, h in w['logo_px'] if bp == v]
        if v == w['xl_min_vw']: decl.append(f'--kz-sheet-cols: {w["sheet_cols_xl"]};')
        out.append(f'@media (min-width:{v}px){{:root{{{"".join(decl)}}}}}')
    return out

def build():
    t = json.loads((R/'tokens/tokens.json').read_text())
    g, m, e = t['glass'], t['motion'], t['elevation']
    css = [':root {']
    for key, value in t['colors'].items(): css.append(f'  --kz-{key.replace("_","-")}: {value};')
    for key, value in t['type_px'].items(): css.append(f'  --kz-type-{key.replace("_","-")}: {value}px;')
    em = t['emphasis']  # 03 COPY-04: one look for the four inline marks on every track
    css += [f'  --kz-emph-bold: {em["bold"]["color"]};', f'  --kz-emph-bold-weight: {em["bold"]["weight"]};',
            f'  --kz-emph-in-bold: {em["bold"]["in_bold_color"]};', f'  --kz-emph-risk: {em["risk"]["color"]};',
            f'  --kz-emph-underline: {em["underline"]["color"]};', f'  --kz-emph-underline-thickness: {em["underline"]["thickness_em"]}em;',
            f'  --kz-emph-underline-offset: {em["underline"]["offset_em"]}em;', f'  --kz-emph-highlight: {em["highlight"]["fill"]};',
            f'  --kz-emph-highlight-pad: {em["highlight"]["pad_em"]}em;', f'  --kz-emph-highlight-radius: {em["highlight"]["radius_em"]}em;']
    for key, value in t['departments'].items():
        css += [f'  --kz-{key}: {value["color"]};', f'  --kz-{key}-tint: {value["tint"]};']
    gd = t['gantt']['today']  # 08 GANTT-06: the today line is a quiet grey dash on every track (KZGantt, static, demo)
    css += [f'  --kz-gantt-today: {gd["line"]};', f'  --kz-gantt-today-pill: {gd["pill"]};', f'  --kz-gantt-today-text: {gd["text"]};']
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
            f'  --kz-gutter: clamp({t["wide"]["gutter_px"][0]}px,{t["wide"]["outer_gutter_vw"]}vw,{t["wide"]["gutter_px"][1]}px);',
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
    # Flagship route F1 (14, 8.0): type in logical px (deck CSS multiplies by --kz-un), geometry unitless (×--kz-u).
    css += flagship_css(t['flagship'])
    css.append('}')
    # Pointer-lit recipes read --kz-lx/--kz-ly/--kz-lift where they are declared, so they must be
    # declared on the lit element itself, not inherited from :root (custom properties substitute var() at declaration).
    css += ['.kz-card,.kz-lit {',
            f'  --kz-rim: linear-gradient(calc({rim["angle_deg"]}deg + var(--kz-lx,0) * {rim["angle_swing_deg"]}deg),{stops(rim["stops"])});',
            f'  --kz-shadow-dynamic: {shadow_dynamic(e["levels"]["rest"], e["levels"]["raised"], e["light_offset_px"], srgb)};', '}']
    css += wide_css(t)
    (R/'runtime/kz-tokens.css').write_text('/* Generated by tools/build_tokens.py; do not edit. */\n'+'\n'.join(css)+'\n')
    (R/'runtime/kz-tokens.js').write_text('/* Generated. Numeric authority: tokens/tokens.json */\nwindow.KZ_TOKENS = '+json.dumps(t,ensure_ascii=False,separators=(',',':'))+';\n')
if __name__ == '__main__': build()
