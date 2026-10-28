/* Kangzhe 7.1 — multi-object scene stages for demonstrative motion (15 DEMO).
   A stage holds persistent objects ([data-kz-obj="id"]); each scene gives some of them a new state, the rest keep
   theirs (object constancy: an object is never destroyed and recreated between scenes). State at any instant is a
   pure function of the timeline position, so every scene is seekable, reversible and printable.
   Same control surface as KZMotion.Film in scene mode (next / prev / toScene / playThrough / pause / resume / seek),
   so the HTML-PPT bridge steps it by scene (06 MOTION-09); sites play it as a seamless loop.
   Timing, easing and density limits come from KZ_TOKENS.motion (scenes, film.storyboard, easing). */
(function (global) {
  'use strict';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  function tk(path, fallback) {
    let v = global.KZ_TOKENS && global.KZ_TOKENS.motion;
    for (const k of path.split('.')) v = v == null ? undefined : v[k];
    return v ?? fallback;
  }
  // cubic-bezier(x1,y1,x2,y2) as y(x), by bisection; the enter curve of MOTION-03
  function bezier([x1, y1, x2, y2]) {
    const bx = t => 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3, by = t => 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3;
    return x => { if (x <= 0) return 0; if (x >= 1) return 1; let lo = 0, hi = 1; for (let i = 0; i < 22; i++) { const m = (lo + hi) / 2; bx(m) < x ? lo = m : hi = m; } return by((lo + hi) / 2); };
  }
  // Colours: #RGB, #RRGGBB, rgb(), rgba() → [r,g,b,a]
  function rgba(c) {
    if (Array.isArray(c)) return c;
    const s = String(c).trim();
    if (s[0] === '#') { const h = s.length === 4 ? [...s.slice(1)].map(x => x + x).join('') : s.slice(1, 7); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)).concat(1); }
    const m = s.match(/rgba?\(([^)]+)\)/); if (m) { const v = m[1].split(',').map(Number); return [v[0], v[1], v[2], v[3] ?? 1]; }
    throw Error('无法解析颜色：' + c);
  }
  const css = v => `rgba(${v.slice(0, 3).map(Math.round).join(',')},${(+v[3]).toFixed(3)})`;
  const NUM = ['x', 'y', 'w', 'h', 'opacity', 'scale', 'rotate', 'draw', 'count'], COLOR = ['fill', 'color', 'stroke'];
  const DEFAULT = { opacity: 1, scale: 1, rotate: 0 };
  const media = () => matchMedia('(prefers-reduced-motion: reduce)');
  const mounted = new WeakSet();

  /* spec: {
       scenes: [{ id, caption, set: { objId: state }, order?: [objId…], hold? }],   state keys:
         x, y, w, h        stage fractions (0–1) of the object's top-left corner and size
         opacity, scale, rotate (deg), fill / color / stroke (colours), draw (0–1, SVG stroke reveal)
         count + {decimals, unit}  number tween written as text; text  string swapped at the move midpoint
         attr: {name: number}      numeric SVG attributes (cx, r, x2 …); cls: {className: bool} discrete toggles
       loop: true (site) | false (HTML-PPT steps), staticScene, onScene(i) } */
  class Stage {
    constructor(root, spec) {
      if (!(root instanceof HTMLElement)) throw Error('演示舞台根节点不存在');
      if (mounted.has(root)) throw Error('演示舞台已挂载，请先 dispose');
      if (!spec || !Array.isArray(spec.scenes) || spec.scenes.length < 2) throw Error('演示至少需要两个 scene');
      this.root = root; this.spec = spec; this.loop = !!spec.loop; this.disposed = false;
      // Object geometry is in fractions of the canvas ([data-kz-scene-canvas], else the root).
      this.canvas = root.querySelector('[data-kz-scene-canvas]') || root;
      this.objects = new Map([...this.canvas.querySelectorAll('[data-kz-obj]')].map(el => [el.dataset.kzObj, el]));
      for (const s of spec.scenes) for (const id of Object.keys(s.set || {})) if (!this.objects.has(id)) throw Error(`scene ${s.id} 引用了不存在的对象 ${id}`);
      this.caption = root.querySelector('[data-kz-scene-caption]');
      this.rail = root.querySelector('[data-kz-scene-rail]');
      this.ease = bezier(tk('easing.enter', [.05, .7, .1, 1]));
      this.text0 = new Map([...this.objects].map(([id, el]) => [id, (el.querySelector('[data-kz-obj-text]') || el).textContent]));
      this.resolve(); this.timeline();
      this.p = 0; this.target = 0; this.raf = 0; this.last = 0; this.reasons = new Set(); this.abort = new AbortController();
      this.staticProgress = this.stops[spec.staticScene ?? spec.scenes.length - 1];
      this.scenes = this.loop ? null : this.stops.slice();
      if (this.rail && !this.rail.children.length) this.rail.append(...spec.scenes.map((s, i) => { const li = document.createElement('li'); li.textContent = String(i + 1); li.title = s.caption || ''; return li; }));
      const signal = this.abort.signal; this.mq = media();
      this.mqChange = () => { if (this.mq.matches) { this.pause('reduced-motion'); this.seek(this.staticProgress); } else this.resume('reduced-motion'); };
      this.mq.addEventListener('change', this.mqChange);
      document.addEventListener('visibilitychange', () => document.hidden ? this.pause('hidden') : this.resume('hidden'), { signal });
      global.addEventListener('beforeprint', () => { this.saved = this.p; this.pause('capture'); this.seek(this.staticProgress); }, { signal });
      global.addEventListener('afterprint', () => { this.seek(this.saved ?? this.p); this.resume('capture'); }, { signal });
      this.ro = new ResizeObserver(() => this.render()); this.ro.observe(this.canvas);
      this.io = new IntersectionObserver(es => { for (const e of es) e.isIntersecting ? this.resume('offscreen') : this.pause('offscreen'); }, { threshold: .05 });
      this.io.observe(root);
      mounted.add(root);
      this.render();
      if (this.mq.matches) this.mqChange();
      if (document.hidden) this.pause('hidden');
      if (this.loop) this.run();
      root.dataset.kzReady = 'true';
    }
    // Every object's full state in every scene: a scene inherits whatever it does not set. An object first set in
    // a later scene waits hidden at that state (or at its `from` state, to travel in) and appears in that scene.
    // An object no scene mentions is static and visible as drawn (a path revealed only through its clip, a frame).
    resolve() {
      const scenes = this.spec.scenes, clean = o => { const { from, ...rest } = o; return rest; }, noVia = o => { const { via, ...rest } = o; return rest; };
      let prev = {};
      for (const id of this.objects.keys()) {
        const k = scenes.findIndex(s => s.set?.[id]), s0 = k < 0 ? {} : scenes[k].set[id];
        prev[id] = k <= 0 ? { ...DEFAULT, ...clean(s0) } : { ...DEFAULT, ...noVia(clean(s0)), ...(s0.from || {}), opacity: 0 };
      }
      const shown = new Set(scenes[0].set ? Object.keys(scenes[0].set) : []);
      this.states = scenes.map((s, i) => {
        const cur = {};
        for (const id of this.objects.keys()) {
          const set = s.set?.[id];
          if (!set || i === 0) { cur[id] = prev[id]; continue; }
          // First appearance: the scene's state on its own (the `from` pre-state is not inherited); later: a delta.
          cur[id] = shown.has(id) ? { ...noVia(prev[id]), ...clean(set), attr: { ...prev[id].attr, ...set.attr }, cls: { ...prev[id].cls, ...set.cls } } : { ...DEFAULT, ...clean(set) };
          // count and text write the same slot: the one this scene sets wins over the inherited other
          if (set.text != null && set.count == null) delete cur[id].count;
          if (set.count != null && set.text == null) delete cur[id].text;
          shown.add(id);
        }
        prev = cur; return cur;
      });
      // Every scene states every class and the text of every object, so stepping back or looping to an
      // earlier scene restores them: a class and the text default to the markup until a scene sets them.
      const clsKeys = new Map([...this.objects.keys()].map(id => [id, new Set(this.states.flatMap(st => Object.keys(st[id].cls || {})))]));
      const memo = new Map();
      this.states = this.states.map(st => Object.fromEntries(Object.entries(st).map(([id, o]) => {
        if (!memo.has(o)) { const off = Object.fromEntries([...clsKeys.get(id)].map(c => [c, this.objects.get(id).classList.contains(c)])); memo.set(o, { ...o, cls: { ...off, ...o.cls }, text: o.text ?? (o.count == null ? this.text0.get(id) : undefined) }); }
        return [id, memo.get(o)];
      })));
    }
    // Timeline: (hold, move) pairs. Step mode has no holds (the presenter holds); loop mode holds for reading time
    // and closes by moving back to scene 0, so the last frame equals the first (FILM-04).
    timeline() {
      const move = tk('scenes.move_ms', 1100), step = tk('scenes.stagger_ms', 60), cap = tk('scenes.stagger_max_ms', 480);
      const cps = tk('film.storyboard.chars_per_second', 6), read = tk('film.storyboard.read_start_ms', 1200), minHold = tk('film.storyboard.min_hold_ms', 2000);
      const n = this.spec.scenes.length;
      this.moves = []; this.stops = []; let t = 0;
      const order = s => s.order || Object.keys(s.set || {});
      const delays = s => { const m = new Map(); order(s).forEach((id, j) => m.set(id, Math.min(cap, j * step))); return m; };
      for (let i = 0; i < n; i++) {
        if (i > 0) { const d = delays(this.spec.scenes[i]); const len = move + Math.max(0, ...d.values()); this.moves.push({ from: i - 1, to: i, t0: t, len, delays: d, move }); t += len; }
        this.stops.push(t);
        if (this.loop) t += this.spec.scenes[i].hold ?? Math.max(minHold, (this.spec.scenes[i].caption || '').length / cps * 1000 + read);
      }
      if (this.loop) { const d = new Map([...this.objects.keys()].map(id => [id, 0])); this.moves.push({ from: n - 1, to: 0, t0: t, len: move, delays: d, move }); t += move; }
      this.total = Math.max(t, 1);
      this.stops = this.stops.map(x => x / this.total);
    }
    // Object state at timeline position p (0–1)
    sample(p) {
      const t = p * this.total;
      const mv = this.moves.find(m => t > m.t0 && t < m.t0 + m.len);
      if (!mv) { let i = 0; for (let k = 0; k < this.stops.length; k++) if (p >= this.stops[k] - 1e-9) i = k; return { scene: i, u: 1, get: id => this.states[i][id], mid: 1 }; }
      const local = t - mv.t0, A = this.states[mv.from], B = this.states[mv.to];
      return { scene: mv.from, to: mv.to, mid: local / mv.len, get: id => {
        const a = A[id], b = B[id]; if (a === b) return a;
        const u = this.ease(clamp((local - (mv.delays.get(id) ?? 0)) / mv.move)), o = {}, late = u >= .5 ? b : a;
        for (const k of NUM) if (a[k] != null || b[k] != null) o[k] = lerp(a[k] ?? b[k], b[k] ?? a[k], u);
        if ((a.count == null) !== (b.count == null)) o.count = late.count; // a count handing over to text (or back) switches with it
        // via: [[x,y],…] waypoints of this move; the object travels the polyline at constant speed
        if (b.via && b !== a) { const pts = [[a.x ?? 0, a.y ?? 0], ...b.via, [b.x ?? 0, b.y ?? 0]], seg = pts.slice(1).map((q, j) => Math.hypot(q[0] - pts[j][0], q[1] - pts[j][1])), L = seg.reduce((x, y) => x + y, 0) || 1;
          let d = u * L, j = 0; while (j < seg.length - 1 && d > seg[j]) { d -= seg[j]; j++; } const f = seg[j] ? d / seg[j] : 1; o.x = lerp(pts[j][0], pts[j + 1][0], f); o.y = lerp(pts[j][1], pts[j + 1][1], f); }
        for (const k of COLOR) if (a[k] != null || b[k] != null) o[k] = rgba(a[k] ?? b[k]).map((v, j) => lerp(v, rgba(b[k] ?? a[k])[j], u));
        o.attr = {}; for (const k of new Set([...Object.keys(a.attr || {}), ...Object.keys(b.attr || {})])) o.attr[k] = lerp(a.attr?.[k] ?? b.attr[k], b.attr?.[k] ?? a.attr[k], u);
        o.text = late.text; o.cls = late.cls; o.decimals = b.decimals ?? a.decimals; o.unit = b.unit ?? a.unit;
        return o;
      } };
    }
    render() {
      if (this.disposed) return;
      const W = this.canvas.clientWidth, H = this.canvas.clientHeight, S = this.sample(this.p);
      for (const [id, el] of this.objects) {
        const s = S.get(id), st = el.style;
        if (s.x != null || s.y != null) st.translate = `${((s.x ?? 0) * W).toFixed(1)}px ${((s.y ?? 0) * H).toFixed(1)}px`;
        if (s.w != null) st.width = (s.w * W).toFixed(1) + 'px';
        if (s.h != null) st.height = (s.h * H).toFixed(1) + 'px';
        st.opacity = clamp(s.opacity ?? 1).toFixed(3);
        st.scale = (s.scale ?? 1).toFixed(4); st.rotate = (s.rotate ?? 0).toFixed(2) + 'deg';
        st.visibility = (s.opacity ?? 1) <= .001 ? 'hidden' : ''; // '' inherits, so a hidden slide hides its stage
        if (s.fill) (el instanceof SVGElement ? el.setAttribute('fill', css(rgba(s.fill))) : st.backgroundColor = css(rgba(s.fill)));
        if (s.color) st.color = css(rgba(s.color));
        // inline, so a scene's stroke wins over a class default (a muted rail lights up when a route uses it)
        if (s.stroke) st.stroke = css(rgba(s.stroke));
        for (const [k, v] of Object.entries(s.attr || {})) el.setAttribute(k, (+v).toFixed(2));
        // a fully drawn line carries no dash (path length and a non-scaling stroke's dash units can differ)
        if (s.draw != null && el.getTotalLength) { if (s.draw >= .999) { st.strokeDasharray = ''; st.strokeDashoffset = ''; } else { const L = el.getTotalLength(); st.strokeDasharray = `${L} ${L}`; st.strokeDashoffset = String(L * (1 - clamp(s.draw))); } }
        const slot = el.querySelector('[data-kz-obj-text]') || el;
        if (s.count != null) { const t = Number(s.count).toLocaleString('zh-CN', { minimumFractionDigits: s.decimals || 0, maximumFractionDigits: s.decimals || 0 }) + (s.unit || ''); if (slot.textContent !== t) slot.textContent = t; }
        else if (s.text != null && slot.textContent !== s.text) slot.textContent = s.text;
        for (const [c, on] of Object.entries(s.cls || {})) el.classList.toggle(c, !!on);
      }
      // Caption: the arriving scene's sentence, swapped at the move midpoint while faded out.
      const idx = S.to != null && S.mid >= .5 ? S.to : S.scene, cap = this.spec.scenes[idx].caption || '';
      if (this.caption) { if (this.caption.textContent !== cap) this.caption.textContent = cap; this.caption.style.opacity = S.to != null ? clamp(Math.abs(S.mid - .5) / .25).toFixed(3) : '1'; }
      if (this.rail) [...this.rail.children].forEach((li, i) => { li.dataset.state = i < idx ? 'done' : i === idx ? 'current' : 'todo'; li.setAttribute('aria-current', i === idx ? 'step' : 'false'); });
      if (idx !== this.shown) { this.shown = idx; this.spec.onScene?.(idx, this); }
      this.root.dataset.kzScene = String(idx); this.root.dataset.kzProgress = this.p.toFixed(5);
    }
    tick() {
      this.raf = 0; if (this.disposed || this.reasons.size) return;
      const now = performance.now(), dt = this.last ? Math.min(now - this.last, tk('film.max_frame_gap_ms', 2000)) : 0; this.last = now;
      if (!this.loop) { this.p = Math.min(this.target, this.p + dt / this.total); this.render(); if (this.p < this.target) this.raf = requestAnimationFrame(() => this.tick()); return; }
      this.p = (this.p + dt / this.total) % 1; this.render(); this.raf = requestAnimationFrame(() => this.tick());
    }
    run() { if (!this.disposed && !this.reasons.size && !this.raf) { this.last = 0; this.raf = requestAnimationFrame(() => this.tick()); } }
    pause(reason = 'user') { if (this.disposed) return; this.reasons.add(reason); cancelAnimationFrame(this.raf); this.raf = 0; this.last = 0; }
    resume(reason = 'user') { if (this.disposed) return; this.reasons.delete(reason); this.run(); }
    seek(p) { if (this.disposed) return; if (!Number.isFinite(p)) throw Error('进度不是有限数'); this.p = clamp(p); this.target = this.p; this.last = 0; this.render(); }
    get scene() { let i = 0; for (let k = 0; k < this.stops.length; k++) if (this.p >= this.stops[k] - 1e-6) i = k; return i; }
    get moving() { return !this.loop && this.p < this.target - 1e-6; }
    toScene(i) { this.seek(this.stops[Math.max(0, Math.min(this.stops.length - 1, Math.trunc(i)))]); }
    next() {
      if (this.loop || this.disposed || this.reasons.has('reduced-motion')) return false;
      const stop = this.stops.find(t => t > this.p + 1e-6); if (stop === undefined) return false;
      if (this.moving || this.reasons.size) { this.seek(stop); return true; }
      this.target = stop; this.run(); return true;
    }
    prev() {
      if (this.loop || this.disposed || this.reasons.has('reduced-motion')) return false;
      const stop = [...this.stops].reverse().find(t => t < this.p - 1e-6); if (stop === undefined) return false;
      this.seek(stop); return true;
    }
    playThrough() { if (this.loop) return; this.target = 1; this.run(); }
    // Density receipt for QC (15 DEMO-03): what each scene changes, and how far things travel.
    audit() {
      const keys = ['x', 'y', 'w', 'h', 'opacity', 'scale', 'fill', 'stroke', 'count', 'text', 'draw', 'cls'];
      const per = this.states.slice(1).map((B, i) => {
        const A = this.states[i]; let changed = 0, travel = 0, grow = 1, entered = 0;
        for (const id of this.objects.keys()) {
          const a = A[id], b = B[id]; if (a === b) continue;
          if (keys.some(k => JSON.stringify(a[k]) !== JSON.stringify(b[k])) || JSON.stringify(a.attr) !== JSON.stringify(b.attr)) changed++;
          if ((a.opacity ?? 1) < .05 && (b.opacity ?? 1) > .5) entered++;
          if (a.x != null && b.x != null) travel = Math.max(travel, Math.hypot(b.x - a.x, (b.y ?? 0) - (a.y ?? 0)));
          if (a.w && b.w && a.h && b.h) grow = Math.max(grow, (b.w * b.h) / (a.w * a.h), (a.w * a.h) / (b.w * b.h));
        }
        return { scene: this.spec.scenes[i + 1].id, changed, entered, travel: +travel.toFixed(3), grow: +grow.toFixed(2), caption: this.spec.scenes[i + 1].caption || '' };
      });
      return { scenes: this.spec.scenes.length, objects: this.objects.size, transitions: per };
    }
    // Space receipt for QC (15 DEMO-03), measured in the DOM at the current scene: the share of canvas cells that
    // visible objects touch, and how many of them are figures (icons, marks, bars, links) rather than text.
    coverage({ cols, rows } = {}) {
      [cols, rows] = [cols || tk('scenes.density.coverage_grid', [24, 14])[0], rows || tk('scenes.density.coverage_grid', [24, 14])[1]];
      const C = this.canvas.getBoundingClientRect(), hit = new Set(); let figures = 0, texts = 0;
      if (!C.width || !C.height) return { cells: 0, figures: 0, texts: 0 };
      for (const el of this.canvas.querySelectorAll('[data-kz-obj]')) {
        const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity < .05 || el.closest('defs')) continue;
        // a straight horizontal or vertical link has a zero-height or zero-width box: only skip boxes empty both ways
        const r = el.getBoundingClientRect(); if (r.width < 1 && r.height < 1 || !(el instanceof SVGGeometryElement) && (r.width < 1 || r.height < 1)) continue;
        const figure = el instanceof SVGElement || !!el.querySelector('svg') || !el.textContent.trim();
        figure ? figures++ : texts++;
        const mark = (px, py) => { const x = Math.floor((px - C.left) / C.width * cols), y = Math.floor((py - C.top) / C.height * rows); if (x >= 0 && x < cols && y >= 0 && y < rows) hit.add(x + ',' + y); };
        // a link counts the cells its stroke passes through, not its bounding box
        if (el instanceof SVGGeometryElement) { const len = el.getTotalLength(), M = el.getScreenCTM(); for (let t = 0; t <= 80; t++) { const pt = el.getPointAtLength(len * t / 80), q = new DOMPoint(pt.x, pt.y).matrixTransform(M); mark(q.x, q.y); } continue; }
        const x0 = Math.max(0, Math.floor((r.left - C.left) / C.width * cols)), x1 = Math.min(cols - 1, Math.floor((r.right - C.left - .5) / C.width * cols));
        const y0 = Math.max(0, Math.floor((r.top - C.top) / C.height * rows)), y1 = Math.min(rows - 1, Math.floor((r.bottom - C.top - .5) / C.height * rows));
        for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) hit.add(x + ',' + y);
      }
      return { cells: +(hit.size / (cols * rows)).toFixed(3), figures, texts };
    }
    snapshot() { return { progress: this.p, scene: this.scene, moving: this.moving, reasons: [...this.reasons], loop: this.loop }; }
    dispose() {
      if (this.disposed) return; this.pause('disposed'); this.disposed = true; this.abort.abort(); this.ro.disconnect(); this.io.disconnect();
      this.mq.removeEventListener('change', this.mqChange); mounted.delete(this.root);
      delete this.root.dataset.kzReady; delete this.root.dataset.kzScene; delete this.root.dataset.kzProgress;
    }
  }

  /* ---------- Layout helpers: data → object states (stage fractions) ---------- */
  const layout = {
    // n unit marks in a grid inside box [x,y,w,h] (one mark = one record: a document, a subject, a visit)
    grid(n, { box = [0, 0, 1, 1], cols, gap = .25, aspect = 1, stageAspect = 16 / 9, valign = 'middle' } = {}) {
      const [bx, by, bw, bh] = box; cols = cols || Math.ceil(Math.sqrt(n * bw * stageAspect / bh));
      const rows = Math.ceil(n / cols), cw = bw / cols, ch = bh / rows;
      const s = Math.min(cw, ch * aspect / stageAspect) / (1 + gap);
      const w = s, h = s * stageAspect / aspect;
      // valign 'bottom': rows fill from the baseline up, so unit columns read like bars
      return Array.from({ length: n }, (_, i) => { const r = Math.floor(i / cols), y = valign === 'bottom' ? by + bh - (r + 1) * ch : by + r * ch; return { x: bx + (i % cols) * cw + (cw - w) / 2, y: y + (ch - h) / 2, w, h }; });
    },
    // bars on a fixed scale (05: the scale never changes between scenes); returns rects anchored on the baseline
    bars(values, { box = [0, 0, 1, 1], max, gap = .35, offset = 0, slots } = {}) {
      const [bx, by, bw, bh] = box, n = slots || values.length, slot = bw / n, w = slot * (1 - gap);
      max = max ?? Math.max(...values.filter(Number.isFinite));
      return values.map((v, i) => { const h = Number.isFinite(v) ? bh * v / max : 0; return { x: bx + slot * (i + offset) + (slot - w) / 2, y: by + bh - h, w, h }; });
    },
    // linear scale for timelines: domain → stage x inside box
    scale([d0, d1], [x0, x1]) { return v => x0 + (v - d0) / (d1 - d0) * (x1 - x0); },
    // even rows / columns of slots
    rows(n, { box = [0, 0, 1, 1], gap = .2 } = {}) { const [bx, by, bw, bh] = box, ch = bh / n; return Array.from({ length: n }, (_, i) => ({ x: bx, y: by + i * ch + ch * gap / 2, w: bw, h: ch * (1 - gap) })); },
    cols(n, { box = [0, 0, 1, 1], gap = .1 } = {}) { const [bx, by, bw, bh] = box, cw = bw / n; return Array.from({ length: n }, (_, i) => ({ x: bx + i * cw + cw * gap / 2, y: by, w: cw * (1 - gap), h: bh })); },
  };

  global.KZScenes = { Stage, mount: (root, spec) => new Stage(root, spec), layout, rgba };
})(window);
