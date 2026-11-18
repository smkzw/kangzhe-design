/* Kangzhe Design flagship route F1 (14, 8.0) — chrome, declarative scene timelines and stage components.
   Load after kz-tokens.js, assets/vendor/gsap.min.js (+ DrawSVGPlugin, MotionPathPlugin, CustomEase), three.bundle.min.js when a
   page has a 3D stage, kz-icons.js, kz-charts.js / kz-gantt.js when used, and adapters/html-ppt-bridge.js; the stage
   components (platforms, towers, rings, …) live in kz-flagship-stages.js, loaded right after this file.

     KZFlagship.mount(deck, {logo, title, data}) → {lives, state(), finishAll(), dispose()}

   Pages are upstream html-ppt .slide elements with data-kzf-kind = cover | toc | section | content | ending.
   Content pages declare their header as attributes (data-kzf-icon = KZIcons name in the header tile, data-kzf-kicker "02 name", data-title, data-kzf-chips="a|b");
   the runtime adds the header, the logo, the page progress and the footer, so every page carries the same chrome.
   Motion is declared, not scripted: an element with data-kzf-fx="<fx>" and data-kzf-s="<scene>" joins the page timeline.
   Scenes advance with the presenter's keys through KZHTMLPPT.bind (06 MOTION-09): attended entry plays scene 0,
   unattended entry plays every scene once, going back shows the last scene. No idle loops: the timeline only runs while
   a scene plays, and stages repaint only from timeline updates. */
(function (g) {
  'use strict';
  const doc = document, Q = new URLSearchParams(location.search);
  const F = () => g.KZ_TOKENS.flagship, FX = () => F().motion.fx;
  const ratio = () => parseFloat(doc.documentElement.style.getPropertyValue('--kz-un')) || g.innerHeight / 720 || 1;
  const U = v => v * ratio();
  const mq = matchMedia('(prefers-reduced-motion: reduce)');
  const components = new Map();

  function ensureGsap() {
    if (!g.gsap) throw Error('旗舰路线需要 assets/vendor/gsap.min.js（14 FLAG-09）');
    const plugins = [g.DrawSVGPlugin, g.MotionPathPlugin, g.CustomEase].filter(Boolean);
    if (plugins.length) g.gsap.registerPlugin(...plugins);
    if (g.CustomEase && !g.CustomEase.get('kz')) g.CustomEase.create('kz', F().motion.ease.join(','));
  }
  const ease = () => (g.CustomEase ? 'kz' : 'power3.out');

  /* ---------- chrome ---------- */
  function el(tag, cls, html) { const e = doc.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function icon(name) {
    if (!name || !g.KZIcons) return '';
    try { return g.KZIcons.svg(name).outerHTML; } catch (e) { console.warn(e.message); return ''; }
  }
  function chrome(slide, i, total, opt) {
    const kind = slide.dataset.kzfKind || 'content';
    if (opt.logo && !slide.querySelector(':scope > .kzf-brand')) {
      const img = el('img', 'kzf-brand'); img.src = opt.logo; img.alt = '康哲药业'; slide.prepend(img);
    }
    if (kind === 'content' && !slide.querySelector(':scope > .kzf-head')) {
      const h = el('header', 'kzf-head');
      // H2 tile: the page icon in the orange facet; the kicker keeps "02 资料完整性" whole
      const mark = el('div', 'kzf-mark', markSvg()); mark.dataset.kzfFx = 'pop';
      const ic = icon(slide.dataset.kzfIcon);
      if (ic) mark.append(el('i', '', ic)); else console.warn('旗舰内容页缺 data-kzf-icon（14 FLAG-06）：' + (slide.dataset.title || ''));
      const kick = el('p', 'kzf-kick'); kick.textContent = slide.dataset.kzfKicker || ''; kick.dataset.kzfFx = 'rise';
      const title = el('h2', 'kzf-title'); title.textContent = slide.dataset.title || ''; title.dataset.kzfFx = 'rise';
      h.append(mark, kick, title); slide.prepend(h);
      const chips = (slide.dataset.kzfChips || '').split('|').map(s => s.trim()).filter(Boolean);
      if (chips.length) {
        const c = el('div', 'kzf-chips'); c.dataset.kzfFx = 'fade';
        for (const t of chips) { const s = el('span', 'kzf-chip'); s.textContent = t; c.append(s); }
        h.after(c);
      }
    }
    if (kind !== 'cover' && kind !== 'ending' && !slide.querySelector(':scope > .kzf-foot')) {
      const prog = el('div', 'kzf-prog'); prog.setAttribute('aria-hidden', 'true');
      for (let k = 0; k < total; k++) { const s = el('i', k <= i ? 'on' : ''); prog.append(s); }
      const foot = el('footer', 'kzf-foot');
      const pg = String(i + 1).padStart(2, '0') + ' / ' + String(total).padStart(2, '0');
      foot.innerHTML = `<span></span><span aria-hidden="true">｜</span><span></span><span class="pg">${pg}</span>`;
      foot.children[0].textContent = F().identity.name; foot.children[2].textContent = opt.title || doc.title;
      slide.append(prog, foot);
    }
    enhance(slide);
  }
  // H2 tile facets (tokens.flagship.mark): the regular track's candy ramps on the slanted tile geometry.
  let markSeq = 0;
  function markSvg() {
    const mk = F().mark, id = 'kzf-mark-' + (++markSeq);
    const ramp = (k, ss) => `<linearGradient id="${id}-${k}" x1="0" y1="0" x2="1" y2="1">${ss.map(([c, o]) => `<stop offset="${o}" stop-color="${c}"/>`).join('')}</linearGradient>`;
    return `<svg viewBox="0 0 ${mk.view[0]} ${mk.view[1]}" aria-hidden="true"><defs>${mk.fills.map((ss, k) => ramp(k, ss)).join('')}`
      + `<linearGradient id="${id}-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="${mk.gloss}"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>`
      + `<path d="${mk.paths[0]}" fill="url(#${id}-0)"/><path d="${mk.paths[0]}" fill="url(#${id}-g)"/><path d="${mk.paths[1]}" fill="url(#${id}-1)"/></svg>`;
  }
  // Template helpers that need real elements (so they can move): joints between flow heads, cycle geometry, numeral faces.
  function enhance(slide) {
    for (const e of slide.querySelectorAll('[data-icon]:empty')) e.innerHTML = icon(e.dataset.icon);
    for (const n of slide.querySelectorAll('.kzf-toc .n, .kzf-sec-num')) {
      if (n.querySelector('.kzf-num-face')) continue;
      const face = el('span', 'kzf-num-face'); face.textContent = n.textContent; n.replaceChildren(face);
    }
    for (const flow of slide.querySelectorAll('.kzf-flow')) {
      const heads = [...flow.querySelectorAll(':scope > .kzf-hd')];
      flow.style.setProperty('--n', heads.length);
      heads.slice(0, -1).forEach(h => { if (!h.querySelector('.kzf-joint')) { const j = el('i', 'kzf-joint'); j.dataset.kzfFx = 'tick'; j.dataset.kzfS = h.dataset.kzfS || '0'; h.append(j); } });
    }
  }

  /* ---------- cycle: nodes on an ellipse, arcs between them, an orbit path for the pulse ---------- */
  const SVGNS = 'http://www.w3.org/2000/svg';
  function layoutCycle(cyc) {
    const nodes = [...cyc.querySelectorAll(':scope > .kzf-node')], n = nodes.length;
    const W = cyc.clientWidth, H = cyc.clientHeight; if (!n || !W || !H) return;
    const cx = W / 2, cy = H / 2, ry = H / 2 - U(46), rx = Math.min(W / 2 - U(120), ry * 2.3); // capped: a very flat ring on ultrawide pages reads as two rows
    nodes.forEach((nd, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / n; nd.style.left = cx + Math.cos(a) * rx + 'px'; nd.style.top = cy + Math.sin(a) * ry + 'px'; });
    let svg = cyc.querySelector(':scope > svg');
    if (!svg) { svg = doc.createElementNS(SVGNS, 'svg'); svg.setAttribute('aria-hidden', 'true'); cyc.prepend(svg); }
    const s = cyc.dataset.kzfArcS || '2', ps = cyc.dataset.kzfPulseS || String(+s + 1);
    const ax = rx * .98, ay = ry * 1.02, gap = .3, p = a => [cx + Math.cos(a) * ax, cy + Math.sin(a) * ay];
    let h = `<defs><linearGradient id="kzf-arc" x1="0" x2="1"><stop offset="0" stop-color="#FFCC00"/><stop offset="1" stop-color="#FF8A00"/></linearGradient>
      <marker id="kzf-ah" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#FF9900"/></marker></defs>
      <ellipse cx="${cx}" cy="${cy}" rx="${ax}" ry="${ay}" fill="none" stroke="${F().line}" stroke-width="${U(1.4)}" stroke-dasharray="${U(2)} ${U(7)}"/>`;
    for (let i = 0; i < n; i++) {
      const [x0, y0] = p(-Math.PI / 2 + i * 2 * Math.PI / n + gap), [x1, y1] = p(-Math.PI / 2 + (i + 1) * 2 * Math.PI / n - gap);
      h += `<path data-kzf-fx="draw" data-kzf-s="${s}" d="M${x0} ${y0} A${ax} ${ay} 0 0 1 ${x1} ${y1}" fill="none" stroke="url(#kzf-arc)" stroke-width="${U(3.4)}" stroke-linecap="round" marker-end="url(#kzf-ah)"/>`;
    }
    const top = cy - ay;
    h += `<path class="kzf-orbit" d="M${cx} ${top} A${ax} ${ay} 0 1 1 ${cx - .1} ${top}" fill="none" stroke="none"/>
      <circle data-kzf-fx="orbit" data-kzf-s="${ps}" r="${U(7)}" fill="#FF9900"/><circle data-kzf-fx="orbit" data-kzf-s="${ps}" r="${U(15)}" fill="#FF9900" fill-opacity=".18"/>`;
    svg.innerHTML = h;
  }

  /* ---------- fx vocabulary → GSAP tweens ---------- */
  const back = v => `back.out(${v})`;
  function fromVars(fx, n) {
    const c = FX()[fx] || {}, e = ease();
    switch (fx) {
      case 'rise': return { y: U(c.y), opacity: 0, filter: `blur(${c.blur}px)`, ease: e };
      case 'drop': return { y: U(c.y), opacity: 0, ease: e };
      case 'left': case 'right': return { x: U(c.x), opacity: 0, ease: e };
      case 'item': case 'card': return { y: U(c.y), opacity: 0, ease: e };
      case 'pop': case 'stamp': case 'tick': return { scale: c.scale, opacity: 0, ease: back(c.back), transformOrigin: '50% 50%' };
      case 'flip': return { rotationY: i => (i - (n - 1) / 2) * -c.rotate_y, z: -U(c.z), y: U(c.y), opacity: 0, transformPerspective: U(1800), ease: e };
      case 'blur': return { y: U(c.y), scale: c.scale, opacity: 0, filter: `blur(${U(c.blur)}px)`, ease: e };
      case 'grow-x': return { scaleX: 0, transformOrigin: '0% 50%', ease: e };
      case 'grow-y': return { scaleY: 0, transformOrigin: '50% 100%', ease: e };
      case 'fade': return { opacity: 0, ease: 'none' };
      default: return null;
    }
  }
  function count(tl, node, at) {
    const txt = (node.dataset.kzfTo ??= node.textContent.trim()), target = parseFloat(txt.replace(/,/g, '')); if (!Number.isFinite(target)) return;
    const dec = (txt.split('.')[1] || '').length, o = { v: 0 };
    const put = () => { node.textContent = o.v.toFixed(dec); };
    tl.fromTo(o, { v: 0 }, { v: target, duration: FX().count.dur, ease: 'power1.out', onUpdate: put, onStart: put }, at);
  }
  function draw(tl, paths, at) {
    const c = FX().draw;
    if (g.DrawSVGPlugin) { tl.from(paths, { drawSVG: 0, duration: c.dur, stagger: c.stagger, ease: 'power1.inOut' }, at); return; }
    for (const p of paths) { const L = p.getTotalLength?.() || 0; p.style.strokeDasharray = L; }
    tl.from(paths, { strokeDashoffset: i => paths[i].getTotalLength?.() || 0, duration: c.dur, stagger: c.stagger, ease: 'power1.inOut' }, at);
  }
  function spot(tl, items, at) {
    const c = FX().spot;
    items.forEach((it, i) => tl.to(it, { '--kzf-spot': 1, duration: c.dur, ease: 'power2.out', yoyo: true, repeat: 1, repeatDelay: c.hold }, i ? `>-${c.dur}` : at));
  }
  function orbit(tl, items, at) {
    const c = FX().orbit;
    const L = label(tl, at);
    for (const it of items) {
      const host = it.closest('svg'), path = host && host.querySelector('.kzf-orbit');
      if (!path || !g.MotionPathPlugin) continue;
      tl.fromTo(it, { opacity: 0 }, { opacity: 1, duration: .3, immediateRender: true }, L)
        .to(it, { motionPath: { path, align: path, alignOrigin: [.5, .5] }, duration: c.dur, ease: 'none' }, L)
        .to(it, { opacity: 0, duration: .3 }, `${L}+=${c.dur - .3}`);
    }
  }
  function sweep(tl, items, at) {
    const c = FX().sweep;
    tl.fromTo(items, { xPercent: 0, opacity: 0 }, { xPercent: 260, opacity: 1, duration: c.dur, ease: 'power2.inOut' }, at).to(items, { opacity: 0, duration: .4 }, '>-.4');
  }

  let seq = 0; const label = (tl, at) => { const L = 'k' + (++seq); tl.addLabel(L, at); return L; };
  /* ---------- page timeline ---------- */
  function actors(slide) {
    const list = [];
    for (const e of slide.querySelectorAll('[data-kzf-fx]')) if (!e.closest('.notes')) list.push({ el: e, fx: e.dataset.kzfFx, s: +e.dataset.kzfS || 0 });
    for (const c of slide.querySelectorAll('[data-kzf-comp]')) {
      const steps = (c.dataset.kzfSteps || '').split(',').map(s => s.trim()).filter(Boolean), s0 = +c.dataset.kzfS || 0;
      steps.forEach((step, k) => list.push({ el: c, fx: 'comp', step, s: s0 + k }));
    }
    return list;
  }
  function build(life) {
    const { slide } = life, tl = g.gsap.timeline({ paused: true }), all = actors(slide), W = F().motion.wave;
    const n = Math.max(1, ...all.map(a => a.s + 1));
    const each = (c, len) => Math.min(c.stagger || 0, F().motion.stagger_max / Math.max(1, len - 1));
    for (let s = 0; s < n; s++) {
      tl.addLabel('s' + s); const base = tl.duration();
      // Page chrome (header, chips) arrives together at the start of scene 0 and the body follows after a short lead.
      const here = all.filter(a => a.s === s), chromeA = here.filter(a => a.el.closest('.kzf-head, .kzf-chips'));
      chromeA.forEach((a, i) => add(life, tl, { fx: a.fx, items: [a] }, base + i * W.chrome_step));
      // Body: one wave per fx in order of first appearance (the six flow cards rise as one staggered wave, their rows as the
      // next); waves start W.share of the previous wave's length apart, at most W.step_max, so a scene never chains for seconds.
      const groups = [], byKey = new Map();
      for (const a of here) {
        if (chromeA.includes(a)) continue;
        const key = a.fx === 'comp' ? null : a.fx;
        if (key && byKey.has(key)) { byKey.get(key).items.push(a); continue; }
        const gr = { fx: a.fx, items: [a] }; groups.push(gr); if (key) byKey.set(key, gr);
      }
      let at = base + (chromeA.length ? W.chrome_lead : 0);
      for (const gr of groups) {
        const c = FX()[gr.fx] || {}, len = gr.items.length;
        add(life, tl, gr, at);
        const span = gr.fx === 'comp' ? FX().three.dur : (c.dur || .8) + each(c, len) * (len - 1);
        at += Math.min(W.step_max, span * W.share);
      }
      tl.addLabel('e' + s);
    }
    return { tl, n };
  }
  function add(life, tl, gr, at) {
    const els = gr.items.map(a => a.el), c = FX()[gr.fx] || {}, len = els.length;
    const vars = fromVars(gr.fx, len);
    if (vars) { tl.from(els, { ...vars, duration: c.dur, stagger: { each: Math.min(c.stagger || 0, F().motion.stagger_max / Math.max(1, len - 1)) }, immediateRender: true }, at); return; }
    if (gr.fx === 'count') { els.forEach(e => count(tl, e, at)); return; }
    if (gr.fx === 'draw') return draw(tl, els, at);
    if (gr.fx === 'spot') return spot(tl, els, at);
    if (gr.fx === 'orbit') return orbit(tl, els, at);
    if (gr.fx === 'sweep') return sweep(tl, els, at);
    if (gr.fx === 'chart' || gr.fx === 'gantt') {
      for (const e of els) { const w = life.widgets.get(e); if (!w) continue; const o = { p: 0 };
        tl.fromTo(o, { p: 0 }, { p: 1, duration: FX().chart.dur, ease: 'none', onUpdate: () => w.renderProgress(o.p), immediateRender: false }, at);
        w.renderProgress(0); }
      return;
    }
    if (gr.fx === 'comp') { for (const a of gr.items) life.comps.get(a.el)?.step(a.step, tl, at); return; }
    console.warn('未知 data-kzf-fx：' + gr.fx);
  }

  /* ---------- page lifecycle (KZHTMLPPT.bind factory) ---------- */
  function lifeFor(slide, opt) {
    const life = { slide, widgets: new Map(), comps: new Map(), tl: null, n: 1, cur: -1 };
    for (const ce of slide.querySelectorAll('[data-kz-chart]')) { const d = opt.data?.[ce.dataset.kzChart]; if (d && g.KZCharts) life.widgets.set(ce, g.KZCharts.mount(ce, d)); }
    for (const ge of slide.querySelectorAll('[data-kz-gantt]')) { const d = opt.data?.[ge.dataset.kzGantt]; if (d && g.KZGantt) life.widgets.set(ge, g.KZGantt.mount(ge, d)); }
    for (const ce of slide.querySelectorAll('[data-kzf-comp]')) {
      const make = components.get(ce.dataset.kzfComp);
      if (!make) { console.warn('未注册的旗舰组件：' + ce.dataset.kzfComp); continue; }
      let data = null; try { data = JSON.parse(ce.dataset.kzfData || 'null'); } catch (e) { throw Error('data-kzf-data 不是合法 JSON：' + e.message); }
      life.comps.set(ce, make(ce, data));
    }
    const rebuild = () => {
      const t = life.tl ? life.tl.time() : 0, wasActive = busy();
      life.drv?.kill(); life.drv = null; life.tl?.kill(); slide.querySelectorAll('.kzf-cycle').forEach(layoutCycle);
      for (const c of life.comps.values()) c.layout?.();   // SVG stages redraw at the current size before the timeline is rebuilt
      g.gsap.set(slide.querySelectorAll('[data-kzf-fx]'), { clearProps: 'transform,opacity,filter,--kzf-spot' });
      const b = build(life); life.tl = b.tl; life.n = b.n; life.tl.seek(Math.min(t, life.tl.duration()), false); if (wasActive) { life.goal = life.tl.labels['e' + Math.max(0, life.cur)]; life.drv = life.tl.tweenTo(life.goal); }
    };
    const frozen = () => mq.matches || opt.frozen();
    const stop = () => { life.drv?.kill(); life.drv = null; life.tl?.pause(); };
    // "busy" is logical (a driver exists and the playhead has not reached its target), not GSAP isActive(): a tween is not
    // active until its first tick, so a second key press inside one frame would otherwise skip a scene.
    const target = to => (typeof to === "string" ? life.tl.labels[to] : to);
    const busy = () => !!(life.drv && life.tl && life.tl.time() < life.goal - 1e-3);
    life.busy = busy;
    const go = (from, to) => { stop(); life.tl.seek(from, false); life.goal = target(to); life.drv = life.tl.tweenTo(to); };
    const end = k => 'e' + Math.min(life.n - 1, Math.max(0, k));
    Object.assign(life, {
      rebuild,
      enter(info = {}) {
        rebuild();
        if (frozen() || info.direction === 'backward') { life.cur = life.n - 1; life.tl.seek(life.tl.duration(), false); return; }
        if (info.attended) { life.cur = 0; go(0, end(0)); return; }
        life.cur = life.n - 1; go(0, life.tl.duration());
      },
      leave() { stop(); },
      next() {
        if (!life.tl || frozen()) return false;
        if (busy()) { const t = life.goal; stop(); life.tl.seek(t, false); return true; }
        if (life.cur < life.n - 1) { life.cur += 1; go(end(life.cur - 1), end(life.cur)); return true; }
        return false;
      },
      prev() {
        if (!life.tl || frozen() || life.cur <= 0) return false;
        life.cur -= 1; stop(); life.tl.seek(end(life.cur), false); return true;
      },
      finish() { if (!life.tl) rebuild(); stop(); life.cur = life.n - 1; life.tl.seek(life.tl.duration(), false); },
      dispose() { stop(); life.tl?.kill(); for (const w of life.widgets.values()) w.dispose?.(); for (const c of life.comps.values()) c.dispose?.(); }
    });
    return life;
  }

  function mount(deck, opt = {}) {
    if (!deck) throw Error('需要 html-ppt 的 .deck');
    if (!g.KZHTMLPPT) throw Error('旗舰路线需要 adapters/html-ppt-bridge.js');
    ensureGsap();
    const slides = [...deck.querySelectorAll(':scope > .slide')];
    const printing = { on: false };
    const o = { logo: opt.logo, title: opt.title || doc.body.dataset.kzfTitle || doc.title, data: opt.data || g.KZ_DECK_DATA || {},
      frozen: () => printing.on || Q.has('preview') || Q.has('kzf-final') };
    slides.forEach((s, i) => chrome(s, i, slides.length, o));
    const lives = new Set();
    const bridge = g.KZHTMLPPT.bind(deck, slide => { const l = lifeFor(slide, o); lives.add(l); const d = l.dispose; l.dispose = () => { lives.delete(l); d(); }; return l; });
    const finishAll = () => lives.forEach(l => l.finish());
    const onMq = () => { if (mq.matches) finishAll(); };
    const onPrint = () => { printing.on = true; finishAll(); }, afterPrint = () => { printing.on = false; };
    let rt = 0; const onRatio = () => { clearTimeout(rt); rt = setTimeout(() => lives.forEach(l => { if (l.slide.classList.contains('is-active')) l.rebuild(); else if (l.tl) l.finish(); }), 60); };
    mq.addEventListener('change', onMq); g.addEventListener('beforeprint', onPrint); g.addEventListener('afterprint', afterPrint); g.addEventListener('kz:fluidratio', onRatio);
    doc.documentElement.dataset.kzfReady = 'true';
    const api = {
      lives,
      state() { const l = [...lives].find(x => x.slide.classList.contains('is-active')); return l ? { index: slides.indexOf(l.slide), scene: l.cur, scenes: l.n, playing: l.busy(), time: l.tl?.time() ?? 0, duration: l.tl?.duration() ?? 0 } : null; },
      finishAll,
      dispose() { mq.removeEventListener('change', onMq); g.removeEventListener('beforeprint', onPrint); g.removeEventListener('afterprint', afterPrint); g.removeEventListener('kz:fluidratio', onRatio); bridge.dispose(); }
    };
    return api;
  }

  g.KZFlagship = { mount, component(name, make) { components.set(name, make); }, components: () => [...components.keys()], layoutCycle };
})(window);
