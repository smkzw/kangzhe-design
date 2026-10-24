/* Flagship route (14): one full-viewport light field under the upstream deck, page-role light levels,
   liquid-glass lenses and the identity capsule. Additive only: the upstream runtime keeps navigation, hash,
   overview, presenter and print; this module reacts to .is-active changes on direct .slide children.
   QC: ?kzf-t=<s> freezes the clock (entrances are seeked, not skipped); ?kzf-p=<0..1> freezes mid-transition
   from the previous page (the clock then defaults to flagship.plate.time_s). Numbers come from KZ_TOKENS.flagship only. */
(function (g) {
  'use strict';
  const doc = g.document;
  const F = () => (g.KZ_TOKENS && g.KZ_TOKENS.flagship) || {};
  const hex = h => { const c = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(c.slice(i, i + 2), 16) / 255); };

  const COMMON = `#version 300 es
precision highp float;
uniform vec2 uRes; uniform float uTime; uniform vec2 uFocus; uniform vec2 uFocusFrom; uniform float uP; uniform float uWaveP;
uniform float uLevelFrom; uniform float uLevelTo; uniform vec4 uRiver;
uniform vec4 uRectsA[8]; uniform int uRectNA; uniform vec4 uPoolA; uniform vec4 uRectsB[8]; uniform int uRectNB; uniform vec4 uPoolB;
uniform vec3 uCanvas; uniform vec3 uHoney; uniform vec3 uDeep; uniform vec3 uRiverEdge; uniform vec3 uRiverCore; uniform vec3 uCore; uniform vec3 uWave; uniform vec3 uBoost;
uniform vec4 uField; uniform vec4 uField2; uniform vec4 uField3; uniform vec4 uField4; uniform vec4 uLevels; uniform vec4 uLevels2;
out vec4 o;
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 5; i++){ v += a * noise(p); p = m * p; a *= 0.5; } return v; }
`;
  // uField  = scale, speed, warp1, warp2 · uField2 = near falloff, body lo, body hi, deep lo · uField3 = deep hi, river width, river core width, river jitter
  // uField4 = ribbon sharpness, quiet mix · uLevels = hero gain, section gain, content margin gain, card calm · uLevels2 = feather, pool gain, wave gain, ribbon bands
  // uP = page transition progress (focus, river, level, masks); uWaveP = progress of the last whole-page wave (its own clock).
  const FIELD = `
vec3 field(vec2 uv, vec2 f, float t, float pulse, float e){
  float asp = uRes.x / uRes.y; vec2 p = vec2(uv.x * asp, uv.y) * uField.x;
  float s = t * uField.y;
  vec2 q = vec2(fbm(p + vec2(0.0, s)), fbm(p + vec2(5.2, 1.3) - s));
  vec2 r = vec2(fbm(p + uField.z * q + vec2(1.7, 9.2) + s * 0.6), fbm(p + uField.z * q + vec2(8.3, 2.8) - s * 0.4));
  float v = fbm(p + uField.w * r);
  vec2 fd = (uv - f) * vec2(asp, 1.0);
  float near = exp(-dot(fd, fd) * uField2.x);
  float gl = smoothstep(uField2.y, uField2.z, v);
  vec3 lightCol = mix(uHoney, uDeep, smoothstep(uField2.w, uField3.x, v));
  vec3 col = mix(uCanvas, lightCol, clamp(gl * (0.30 + 1.30 * near), 0.0, 0.95));
  col += pow(gl, 3.0) * near * uBoost;
  float band = abs(fract(v * uLevels2.w - s * 0.6) - 0.5);
  float ribbon = exp(-band * band * uField4.x);
  col += ribbon * uCore * (0.12 + 0.60 * near);
  vec2 rv = mix(uRiver.xy, uRiver.zw, e);
  float flow = uv.y - (rv.x - rv.y * uv.x) + (v - 0.5) * uField3.w + 0.045 * sin(uv.x * 4.0 + s * 2.6);
  float river = exp(-flow * flow * uField3.y);
  col = mix(col, mix(uRiverEdge, uRiverCore, river), river * 0.78 * (0.55 + 0.7 * near));
  col += exp(-flow * flow * uField3.z) * uCore * 0.55;
  float quiet = (1.0 - smoothstep(0.05, 0.60, uv.x)) * smoothstep(0.05, 0.45, 1.0 - abs(uv.y - 0.40) * 1.7);
  col = mix(col, uCanvas, quiet * uField4.y);
  float front = uWaveP * 1.5 - 0.25;
  float wave = exp(-pow((uv.x + (uv.y - 0.5) * 0.25 - front) * 5.0, 2.0)) * pulse;
  col = mix(col, uWave, wave * 0.6);
  col += wave * ribbon * 0.25;
  return col;
}
float calmOf(vec2 uv, float asp, vec4 rects[8], int n){
  float calm = 0.0;
  for (int i = 0; i < 8; i++) { if (i >= n) break; vec4 rc = rects[i];
    vec2 q = max(max(rc.xy - uv, uv - rc.zw), 0.0); calm = max(calm, 1.0 - smoothstep(0.0, uLevels2.x, length(q * vec2(asp, 1.0)))); }
  return calm;
}
float poolOf(vec2 uv, float asp, vec4 pool){
  if (pool.z <= 0.0) return 0.0; vec2 pd = (uv - pool.xy) * vec2(asp, 1.0); return exp(-dot(pd, pd) / (pool.z * pool.z));
}
void main(){ vec2 uv = gl_FragCoord.xy / uRes; uv.y = 1.0 - uv.y;
  float e = uP * uP * (3.0 - 2.0 * uP); vec2 f = mix(uFocusFrom, uFocus, e);
  float pulse = uWaveP < 1.0 ? sin(3.14159265 * uWaveP) : 0.0;
  vec3 c = field(uv, f, uTime, pulse, e);
  // 14 FLAG-03: level 3 hero, 2 section, 1 content. Content pages keep the light out of their calm rects and pool it
  // behind the focal lens; the outgoing page's masks fade out while the incoming page's fade in, so nothing jumps.
  float asp = uRes.x / uRes.y, lvl = mix(uLevelFrom, uLevelTo, e);
  float gain = lvl >= 2.0 ? mix(uLevels.y, uLevels.x, lvl - 2.0) : mix(uLevels.z, uLevels.y, lvl - 1.0);
  float calm = mix(calmOf(uv, asp, uRectsA, uRectNA) * clamp(2.0 - uLevelFrom, 0.0, 1.0), calmOf(uv, asp, uRectsB, uRectNB) * clamp(2.0 - uLevelTo, 0.0, 1.0), e);
  gain *= 1.0 - calm * uLevels.w;
  gain = max(gain, max(poolOf(uv, asp, uPoolA) * (1.0 - e), poolOf(uv, asp, uPoolB) * e) * uLevels2.y);
  gain = max(gain, pulse * uLevels2.z);
  c = uCanvas + (c - uCanvas) * gain;
  c += (hash(gl_FragCoord.xy + fract(uTime * 7.0)) - 0.5) / 255.0;
  o = vec4(clamp(c, 0.0, 1.0), 1.0); }`;

  function lensMap(w, h, rad, bevel, k) {
    const W = Math.max(8, Math.round(w * k)), H = Math.max(8, Math.round(h * k)), R = rad * k, B = Math.max(2, bevel * k);
    const c = doc.createElement('canvas'); c.width = W; c.height = H;
    const x = c.getContext('2d'), img = x.createImageData(W, H), d = img.data, hw = W / 2, hh = H / 2;
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
      const px = i + 0.5 - hw, py = j + 0.5 - hh, qx = Math.abs(px) - (hw - R), qy = Math.abs(py) - (hh - R);
      const sd = Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - R, depth = -sd;
      let nx = 0, ny = 0, m = 0;
      if (depth >= 0 && depth < B) {
        if (qx > 0 && qy > 0) { const l = Math.hypot(qx, qy) || 1; nx = qx / l * Math.sign(px); ny = qy / l * Math.sign(py); }
        else if (qx > qy) nx = Math.sign(px); else ny = Math.sign(py);
        m = Math.pow(1 - depth / B, 2.2); // convex rim: strongest bend at the edge, zero on the flat top
      }
      const o = (j * W + i) * 4; d[o] = 128 + nx * m * 127; d[o + 1] = 128 + ny * m * 127; d[o + 2] = 128; d[o + 3] = 255;
    }
    x.putImageData(img, 0, 0); return c.toDataURL();
  }

  // Layout rect relative to the viewport, ignoring CSS transforms (entrances translate/scale their targets).
  function layoutRect(el) {
    let x = 0, y = 0, n = el;
    while (n && n !== doc.body) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { left: x, top: y, width: el.offsetWidth, height: el.offsetHeight };
  }

  function mount(deck, options = {}) {
    if (!deck) throw Error('需要现有 deck');
    const T = F(), Q = new URLSearchParams(g.location.search);
    const P_FIX = Q.has('kzf-p') ? Math.min(1, Math.max(0, +Q.get('kzf-p'))) : null;
    const FREEZE = Q.has('kzf-t') ? +Q.get('kzf-t') : P_FIX !== null ? T.plate.time_s : null;
    const mq = g.matchMedia('(prefers-reduced-motion: reduce)');
    const preview = () => doc.body.dataset.preview === '1' || Q.has('preview');
    const still = () => mq.matches || preview() || FREEZE !== null;
    const root = doc.documentElement, slides = () => [...deck.querySelectorAll(':scope > .slide')];
    const kindOf = s => s.dataset.kzfKind || 'content';
    const chromium = !!(g.navigator.userAgentData?.brands || []).some(b => /Chromium/.test(b.brand));
    const u = () => (parseFloat(getComputedStyle(root).getPropertyValue('--kz-un')) || g.innerHeight / 720);
    const TR = T.transition, timers = new Set();
    const later = (fn, ms) => { const id = setTimeout(() => { timers.delete(id); fn(); }, ms); timers.add(id); return id; };
    doc.body.classList.add('kzf');
    if (FREEZE !== null) root.classList.add('kzf-frozen');
    let disposed = false;

    // 14 FLAG-05 lens budget: authoring error, reported (QC reads console), never silently trimmed
    slides().forEach((s, i) => { const n = s.querySelectorAll('.kzf-lens').length; if (n > T.lens.max_per_page) console.warn(`[kzf] 第 ${i + 1} 页有 ${n} 个透镜，超过 lens.max_per_page=${T.lens.max_per_page}`); });
    // index entrance order once: explicit data-kzf-in="<n>" or DOM order
    for (const s of slides()) [...s.querySelectorAll('[data-kzf-in]')].forEach((el, i) => el.style.setProperty('--kzf-i', el.dataset.kzfIn === '' ? i : el.dataset.kzfIn));

    /* ---------- shared layers: svg defs, field, identity capsule ---------- */
    const svg = doc.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('class', 'kzf-defs'); svg.setAttribute('aria-hidden', 'true');
    const defs = doc.createElementNS('http://www.w3.org/2000/svg', 'defs'); svg.append(defs); doc.body.prepend(svg);
    let canvas = doc.createElement('canvas'); canvas.className = 'kzf-field'; canvas.setAttribute('aria-hidden', 'true'); doc.body.prepend(canvas);
    const idEl = doc.createElement('div'); idEl.className = 'kzf-identity kzf-glass kzf-lens'; idEl.dataset.kzfLens = 'identity';
    const logo = doc.createElement('img'); logo.alt = '康哲药业'; logo.src = options.logo || 'logo_bot.svg';
    const name = doc.createElement('span'); name.className = 'kzf-identity-name'; name.textContent = T.identity?.name || '';
    idEl.append(logo, name); doc.body.append(idEl);

    /* ---------- lenses ---------- */
    let seq = 0;
    function buildLens(el) {
      const W = el.offsetWidth, H = el.offsetHeight; if (W < 4 || H < 4) return;
      const role = T.lens.roles[el.dataset.kzfLens] || T.lens.roles.kpi, k = u();
      const id = el.dataset.kzfLensId || (el.dataset.kzfLensId = 'kzf-lens-' + (++seq));
      defs.querySelector('#' + id)?.remove();
      if (!chromium || preview()) { el.style.backdropFilter = ''; el.classList.add('kzf-lens-fallback'); return; }
      el.classList.remove('kzf-lens-fallback');
      const rad = Math.min(parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0, W / 2, H / 2);
      const f = doc.createElementNS('http://www.w3.org/2000/svg', 'filter');
      for (const [a, v] of Object.entries({ id, x: 0, y: 0, width: W, height: H, filterUnits: 'userSpaceOnUse', primitiveUnits: 'userSpaceOnUse', 'color-interpolation-filters': 'sRGB' })) f.setAttribute(a, v);
      f.innerHTML = `<feGaussianBlur in="SourceGraphic" stdDeviation="${T.lens.frost_px}" result="b"/>`
        + `<feImage href="${lensMap(W, H, rad, role[0] * k, T.lens.map_scale)}" x="0" y="0" width="${W}" height="${H}" preserveAspectRatio="none" result="m"/>`
        + `<feDisplacementMap in="b" in2="m" scale="${role[1] * k}" xChannelSelector="R" yChannelSelector="G" result="d"/>`
        + `<feColorMatrix in="d" type="saturate" values="${T.lens.saturate}"/>`;
      defs.append(f); el.style.backdropFilter = `url(#${id})`;
    }
    const lenses = () => [idEl, ...deck.querySelectorAll(':scope > .slide .kzf-lens')];

    /* ---------- per-slide light geometry (viewport uv), measured without transforms ---------- */
    let geo = [];
    function measure() {
      const W = g.innerWidth, H = g.innerHeight, L = T.levels;
      const uvRect = r => [r.left / W, r.top / H, (r.left + r.width) / W, (r.top + r.height) / H];
      geo = slides().map(s => {
        const kind = kindOf(s), pool = s.querySelector('[data-kzf-pool]'), pr = pool && layoutRect(pool);
        return {
          kind, level: L.by_kind[kind] ?? 1,
          focus: (s.dataset.kzfFocus || '0.5,0.5').split(',').map(Number),
          river: (s.dataset.kzfRiver ? s.dataset.kzfRiver.split(',').map(Number) : T.river[kind] || T.river.content),
          rects: [...s.querySelectorAll('[data-kzf-calm]')].slice(0, L.max_calm_rects).map(e => uvRect(layoutRect(e))),
          pool: pr ? [(pr.left + pr.width / 2) / W, (pr.top + pr.height / 2) / H, Math.max(pr.width, pr.height) / H * L.pool_radius_factor] : [0, 0, 0]
        };
      });
    }

    /* ---------- identity capsule anchor ---------- */
    function placeId(kind) {
      const [corner, scale] = T.identity.anchors[kind] || T.identity.anchors.content, [mx, my] = T.identity.margin.map(v => v * u());
      const w = idEl.offsetWidth * scale, h = idEl.offsetHeight * scale;
      const x = corner[1] === 'l' ? mx : g.innerWidth - mx - w, y = corner[0] === 't' ? my : g.innerHeight - my - h;
      idEl.style.setProperty('--kzf-idx', x.toFixed(1) + 'px'); idEl.style.setProperty('--kzf-idy', y.toFixed(1) + 'px'); idEl.style.setProperty('--kzf-ids', scale);
    }
    // rim highlights of every lens turn with the page light (data-kzf-light, degrees)
    const lightAngle = s => root.style.setProperty('--kzf-la', (+s.dataset.kzfLight || T.glass.rim_angle_deg) + 'deg');

    /* ---------- clock, boot and transitions ---------- */
    const clock = () => FREEZE !== null ? FREEZE * 1000 : g.performance.now();
    const activeIndex = () => slides().findIndex(s => s.classList.contains('is-active'));
    const progress = (now = clock()) => P_FIX !== null ? P_FIX : still() ? 1 : Math.min(1, (now - trans.t0) / TR.duration_ms);
    let cur = -1, trans = null, waveT0 = -1e9, activeSince = 0, booted = false, resolveBoot;
    const bootDone = new Promise(r => { resolveBoot = r; });
    function show(n) { const s = slides()[n]; root.dataset.kzfKind = kindOf(s); placeId(kindOf(s)); lightAngle(s); s.classList.remove('kzf-skip'); activeSince = clock(); }
    // The first .is-active the upstream runtime sets (often after this module mounts) is the starting page, not a transition.
    function boot(n) {
      booted = true; cur = n;
      if (P_FIX !== null && n > 0) { trans = { from: n - 1, to: n, t0: 0, snap: null }; waveT0 = 0; slides()[n - 1].classList.add('kzf-leaving'); }
      else trans = { from: n, to: n, t0: -1e9, snap: null };
      show(n); resolveBoot();
    }
    // Scalars of the light as currently blended, so an interrupted transition starts from where the light is.
    function blended() {
      const A = trans.snap || geo[trans.from], B = geo[trans.to], p = progress(), e = p * p * (3 - 2 * p), mix = (a, b) => a.map((v, i) => v + (b[i] - v) * e);
      return { level: A.level + (B.level - A.level) * e, focus: mix(A.focus, B.focus), river: mix(A.river, B.river), rects: B.rects, pool: B.pool };
    }
    function onActive(n) {
      if (n < 0 || disposed) return;
      if (!booted) { boot(n); render(); return; }
      if (n === cur) return;
      const list = slides(), from = cur, now = clock();
      const snap = progress(now) < 1 ? blended() : null;
      // Whole-page waves stay at least min_interval apart (WCAG 2.3.1); a page turned sooner still moves focus, river
      // and level over the full duration, and a wave already under way finishes on its own clock.
      if (now - waveT0 >= TR.min_interval_ms) waveT0 = now;
      trans = { from, to: n, t0: now, snap }; cur = n;
      const prev = list[from];
      if (prev && !still()) {
        // A page left before its entrance finished skips the exit fade (no flash of half-entered text).
        if (now - activeSince < TR.content_delay_ms + T.entrance.text_ms) prev.classList.add('kzf-skip');
        else { prev.classList.add('kzf-leaving'); later(() => prev.classList.remove('kzf-leaving'), TR.exit_ms); }
      }
      show(n);
      still() ? render() : wake();
    }
    const mo = new MutationObserver(() => onActive(activeIndex()));
    mo.observe(deck, { attributes: true, attributeFilter: ['class'], subtree: true });

    /* ---------- WebGL ---------- */
    let gl = null, prog = null, U = {};
    function compile() {
      gl = canvas.getContext('webgl2', { antialias: false, premultipliedAlpha: false, preserveDrawingBuffer: true });
      if (!gl) throw Error('WebGL2 不可用');
      const sh = (type, s) => { const x = gl.createShader(type); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(x)); return x; };
      prog = gl.createProgram();
      gl.attachShader(prog, sh(gl.VERTEX_SHADER, '#version 300 es\nin vec2 a; void main(){ gl_Position = vec4(a, 0.0, 1.0); }'));
      gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, COMMON + FIELD)); gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(prog));
      gl.useProgram(prog);
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(prog, 'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      for (const n of ['uRes', 'uTime', 'uFocus', 'uFocusFrom', 'uP', 'uWaveP', 'uLevelFrom', 'uLevelTo', 'uRiver', 'uRectNA', 'uPoolA', 'uRectNB', 'uPoolB', 'uCanvas',
        'uHoney', 'uDeep', 'uRiverEdge', 'uRiverCore', 'uCore', 'uWave', 'uBoost', 'uField', 'uField2', 'uField3', 'uField4', 'uLevels', 'uLevels2']) U[n] = gl.getUniformLocation(prog, n);
      U.uRectsA = gl.getUniformLocation(prog, 'uRectsA[0]'); U.uRectsB = gl.getUniformLocation(prog, 'uRectsB[0]');
      const C = T.light, fd = T.field, L = T.levels;
      gl.uniform3f(U.uCanvas, ...hex(T.canvas));
      for (const [u_, k] of [['uHoney', 'honey'], ['uDeep', 'deep'], ['uRiverEdge', 'river_edge'], ['uRiverCore', 'river_core'], ['uCore', 'core_line'], ['uWave', 'wave'], ['uBoost', 'body_boost']]) gl.uniform3f(U[u_], ...hex(C[k]));
      gl.uniform4f(U.uField, fd.scale, fd.speed, fd.warp[0], fd.warp[1]);
      gl.uniform4f(U.uField2, fd.near_falloff, fd.body_threshold[0], fd.body_threshold[1], fd.deep_threshold[0]);
      gl.uniform4f(U.uField3, fd.deep_threshold[1], fd.river_width, fd.river_core_width, fd.river_jitter);
      gl.uniform4f(U.uField4, fd.ribbon_sharpness, fd.quiet_mix, 0, 0);
      gl.uniform4f(U.uLevels, L.gain.hero, L.gain.section, L.gain.content_margin, L.card_calm);
      gl.uniform4f(U.uLevels2, L.mask_feather_uv, L.pool_gain, L.wave_gain, fd.ribbon_bands);
    }
    function size() {
      if (!gl) return; const k = T.field.render_scale, dpr = Math.min(g.devicePixelRatio || 1, T.field.dpr_max);
      canvas.width = Math.max(2, Math.round(g.innerWidth * dpr * k)); canvas.height = Math.max(2, Math.round(g.innerHeight * dpr * k)); gl.viewport(0, 0, canvas.width, canvas.height);
    }
    function render() {
      if (!prog || disposed || !trans || gl.isContextLost()) return;
      const now = clock(), p = progress(now), A = trans.snap || geo[trans.from] || {}, B = geo[trans.to] || {}, rA = (geo[trans.from] || {}).rects || [], rB = B.rects || [];
      const waveP = P_FIX !== null ? P_FIX : still() ? 1 : Math.min(1, Math.max(0, (now - waveT0) / TR.duration_ms));
      gl.uniform2f(U.uRes, canvas.width, canvas.height); gl.uniform1f(U.uTime, mq.matches ? 0 : now / 1000);
      gl.uniform2f(U.uFocusFrom, ...(A.focus || [0.5, 0.5])); gl.uniform2f(U.uFocus, ...(B.focus || [0.5, 0.5]));
      gl.uniform1f(U.uP, p); gl.uniform1f(U.uWaveP, waveP);
      gl.uniform1f(U.uLevelFrom, A.level ?? 3); gl.uniform1f(U.uLevelTo, B.level ?? 3);
      gl.uniform4f(U.uRiver, ...(A.river || T.river.cover), ...(B.river || T.river.cover));
      gl.uniform1i(U.uRectNA, rA.length); if (rA.length) gl.uniform4fv(U.uRectsA, new Float32Array(rA.flat()));
      gl.uniform1i(U.uRectNB, rB.length); if (rB.length) gl.uniform4fv(U.uRectsB, new Float32Array(rB.flat()));
      gl.uniform4f(U.uPoolA, ...((geo[trans.from] || {}).pool || [0, 0, 0]), 0); gl.uniform4f(U.uPoolB, ...(B.pool || [0, 0, 0]), 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    let raf = 0;
    const loop = () => { raf = 0; render(); if (!still() && !doc.hidden && !disposed) raf = g.requestAnimationFrame(loop); };
    const wake = () => { if (!raf && !disposed && !still()) raf = g.requestAnimationFrame(loop); };
    const onVisible = () => { if (!doc.hidden) wake(); };
    doc.addEventListener('visibilitychange', onVisible);
    const onMotion = () => { render(); wake(); };
    mq.addEventListener('change', onMotion);
    function fallbackField() {
      const d = doc.createElement('div'); d.className = 'kzf-field kzf-field-fallback'; d.setAttribute('aria-hidden', 'true');
      canvas.replaceWith(d); canvas = d; gl = null; prog = null;
    }
    // Context loss (GPU reset, driver update): show the CSS field at once, rebuild when the browser restores the context.
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); prog = null; root.dataset.kzfField = 'lost'; });
    canvas.addEventListener('webglcontextrestored', () => { try { compile(); size(); delete root.dataset.kzfField; render(); wake(); } catch (err) { console.warn('[kzf] 光场恢复失败：', err.message); fallbackField(); } });

    function seekEntrances() {
      const Tms = P_FIX !== null ? P_FIX * TR.duration_ms : FREEZE * 1000;
      for (const a of doc.getAnimations()) if (a.effect?.target?.closest?.('.slide, .kzf-identity')) { a.pause(); a.currentTime = Math.min(Tms, a.effect.getComputedTiming().endTime); }
    }
    let resizeTimer = 0;
    function onResize() { size(); measure(); if (cur >= 0) placeId(kindOf(slides()[cur])); clearTimeout(resizeTimer); resizeTimer = setTimeout(() => lenses().forEach(buildLens), 80); render(); }
    g.addEventListener('resize', onResize);

    // boot: geometry before anything moves, then the field; lenses and the capsule once fonts and the first page are known
    measure();
    if (preview()) fallbackField();
    else { try { compile(); size(); } catch (err) { console.warn('[kzf] 光场降级为 CSS 渐变：', err.message); fallbackField(); } }
    if (activeIndex() >= 0) boot(activeIndex());
    const ready = Promise.all([doc.fonts?.ready || Promise.resolve(), bootDone]).then(() => {
      if (disposed) return;
      measure(); placeId(kindOf(slides()[cur])); lenses().forEach(buildLens);
      if (FREEZE !== null) seekEntrances();
      render(); wake(); root.dataset.kzfReady = 'true';
    });

    return {
      ready, get frozen() { return still(); },
      get transition() { return trans && { from: trans.from, to: trans.to, t0: trans.t0, wave: trans.t0 === waveT0 }; },   // QC: whether this turn played the whole-page wave
      measure() { measure(); render(); },
      rebuildLenses() { lenses().forEach(buildLens); },
      dispose() {
        if (disposed) return; disposed = true; mo.disconnect(); if (raf) g.cancelAnimationFrame(raf);
        clearTimeout(resizeTimer); timers.forEach(clearTimeout); timers.clear();
        g.removeEventListener('resize', onResize); doc.removeEventListener('visibilitychange', onVisible); mq.removeEventListener('change', onMotion);
        for (const el of lenses()) { el.style.backdropFilter = ''; el.classList.remove('kzf-lens-fallback'); delete el.dataset.kzfLensId; }
        for (const s of slides()) s.classList.remove('kzf-leaving', 'kzf-skip');
        canvas.remove(); svg.remove(); idEl.remove(); doc.body.classList.remove('kzf'); root.classList.remove('kzf-frozen'); root.style.removeProperty('--kzf-la');
        delete root.dataset.kzfReady; delete root.dataset.kzfKind; delete root.dataset.kzfField;
      }
    };
  }
  g.KZFlagship = { mount };
})(window);
