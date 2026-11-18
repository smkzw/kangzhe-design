/* Kangzhe Design flagship stage components (14 FLAG-06a, 8.0): cinematic three.js stages that join a page's scene timeline —
   depth, a carrier that persists across scenes, and camera moves are what set them apart from the regular track's flat
   KZDemo forms (15 DEMO-02). Load after kz-flagship.js and assets/vendor/three.bundle.min.js. Each component is registered with
   KZFlagship.component and declared on a page as
     <div class="kzf-stage" data-kzf-comp="<name>" data-kzf-steps="a,b,c" data-kzf-data='{…}' role="img" aria-label="…">
   tokens.flagship.stages.catalog is the single register: content job, 2d/3d, step vocabulary and data fields.
   Every number drawn on a stage is computed here from data-kzf-data (totals, shares, gaps, deltas), never typed in.
   3D stages share one off-screen WebGL renderer and post-processing chain (N8AO → SMAA → PBR Neutral tone mapping) and copy
   each frame into their own 2D canvas, so a deck can hold any number of them (browsers cap live WebGL contexts) and printing
   keeps the last frame. Nothing runs between scenes: stages repaint only from timeline updates, at the moving tier while a
   tween runs and once more at the refined tier (jittered accumulation, deterministic) when it settles (tokens.flagship.three). */
(function (g) {
  'use strict';
  const K = g.KZFlagship;
  if (!K) throw Error('kz-flagship-stages.js 要在 kz-flagship.js 之后加载');
  const doc = document;
  const F = () => g.KZ_TOKENS.flagship, ST = () => F().stages, P3 = () => F().three, INK = () => F().ink;
  const RISK = () => g.KZ_TOKENS.colors.risk;
  const ease = () => (g.CustomEase && g.CustomEase.get('kz') ? 'kz' : 'power3.out');
  const back = v => `back.out(${v})`;
  const need = (ok, msg) => { if (!ok) throw Error(msg); };
  const fmt = (v, d = 0) => Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (a, b) => (b ? Math.round(a / b * 100) : 0);
  const each = (n, cap) => Math.min(cap, .8 / Math.max(1, n - 1));
  const hexMix = (a, b, t) => { const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)), x = p(a), y = p(b);
    return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join(''); };

  /* ---------- registration: catalog check, step check, one repaint per tick ---------- */
  function define(name, make) {
    K.component(name, (host, data) => {
      const spec = ST().catalog[name];
      need(spec, `${name} 不在 tokens.flagship.stages.catalog`);
      const api = make(host, data || {}, spec);
      return {
        step(s, tl, at) {
          need(spec.steps.includes(s) && api.steps[s], `${name} 没有这一步：${s}（可用：${spec.steps.join('、')}）`);
          api.steps[s](tl, at); api.dirty?.();
        },
        layout: api.layout, render: api.paint, dispose: api.dispose
      };
    });
  }

  /* ---------- shared 3D renderer + post chain ---------- */
  let RD = null, FXC = null, ENV = null;
  // warm studio for reflections (tokens.flagship.three.env): cream room, a big top softbox, warm side, soft fill, cool rim
  function studio(T, E) {
    const e = new T.Scene(), col = ([c, k]) => new T.Color(c).multiplyScalar(k);
    const room = new T.Mesh(new T.BoxGeometry(1, 1, 1), new T.MeshBasicMaterial({ color: col(E.room), side: T.BackSide }));
    room.scale.set(30, 16, 30); room.position.y = 6; e.add(room);
    const panel = (spec, w, h, pos, rot) => { const m = new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ color: col(spec), side: T.DoubleSide })); m.position.set(...pos); m.rotation.set(...rot); e.add(m); };
    panel(E.top, 14, 8, [0, 13.5, 0], [Math.PI / 2, 0, 0]); panel(E.warm, 6, 9, [-14, 6, 3], [0, Math.PI / 2, 0]);
    panel(E.fill, 3, 10, [12, 6, -6], [0, -Math.PI / 2.4, 0]); panel(E.rim, 18, 2, [0, 2, -14], [0, 0, 0]);
    return e;
  }
  function renderer() {
    const T = g.THREE, X = g.KZ3D; need(T && X, '3D 舞台需要 assets/vendor/three.bundle.min.js（14 FLAG-09）');
    if (!RD) {
      const P = P3(), A = P.ao;
      RD = new T.WebGLRenderer({ antialias: false, alpha: true, premultipliedAlpha: true, powerPreference: 'high-performance' });
      RD.outputColorSpace = T.SRGBColorSpace; RD.toneMapping = T.NoToneMapping; RD.shadowMap.enabled = true; RD.shadowMap.type = T.PCFShadowMap;
      RD.setPixelRatio(1); RD.setClearColor(0x000000, 0);
      const pm = new T.PMREMGenerator(RD), st = studio(T, P.env); ENV = pm.fromScene(st, .03).texture; pm.dispose();
      st.traverse(o => { o.geometry?.dispose(); o.material?.dispose?.(); });
      const cmp = new X.EffectComposer(RD, { frameBufferType: T.HalfFloatType, alpha: true }), s0 = new T.Scene(), c0 = new T.PerspectiveCamera();
      const ao = new X.N8AOPostPass(s0, c0, 4, 4);
      Object.assign(ao.configuration, { aoRadius: A.radius, distanceFalloff: A.falloff, intensity: A.intensity, color: new T.Color(A.color), halfRes: true, transparencyAware: false });
      ao.setQualityMode(A.quality);
      cmp.addPass(new X.RenderPass(s0, c0)); cmp.addPass(ao);
      cmp.addPass(new X.EffectPass(c0, new X.SMAAEffect(), new X.ToneMappingEffect({ mode: X.ToneMappingMode.NEUTRAL })));
      FXC = { cmp, ao };
    }
    return RD;
  }
  // one frame of a view through the chain at pw×ph (renderer pixel ratio stays 1; the 2D canvas carries the DPR)
  function frame(scene, cam, pw, ph) {
    const rd = renderer(), sz = rd.getSize(new g.THREE.Vector2());
    if (sz.x !== pw || sz.y !== ph) FXC.cmp.setSize(pw, ph, false);
    FXC.cmp.setMainScene(scene); FXC.cmp.setMainCamera(cam); FXC.ao.scene = scene; FXC.ao.camera = cam;
    FXC.cmp.render();
    return rd.domElement;
  }
  function rbox(T, w, h, d, r) {
    const s = new T.Shape(), x = -w / 2, y = -d / 2;
    s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + d - r); s.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
    s.lineTo(x + r, y + d); s.quadraticCurveTo(x, y + d, x, y + d - r); s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
    const geo = new T.ExtrudeGeometry(s, { depth: h, bevelEnabled: true, bevelThickness: .04, bevelSize: .04, bevelSegments: 4, curveSegments: 12 }); geo.rotateX(-Math.PI / 2); return geo;
  }
  function view3d(host, pose) {
    const T = g.THREE, P = P3(); renderer();
    const cv = host.querySelector(':scope > canvas') || host.appendChild(doc.createElement('canvas')), ctx = cv.getContext('2d');
    const scene = new T.Scene(), cam = new T.PerspectiveCamera(P.fov, 1, .1, 200);
    scene.environment = ENV; scene.environmentIntensity = P.env.intensity;
    scene.add(new T.HemisphereLight(P.hemi[0], P.hemi[1], P.hemi[2]));
    const sun = new T.DirectionalLight(P.sun[0], P.sun[1]); sun.position.set(...P.sun[2]); sun.castShadow = true;
    sun.shadow.mapSize.set(P.shadow_map, P.shadow_map); sun.shadow.radius = P.shadow_radius; sun.shadow.bias = -.0004; sun.shadow.normalBias = .02; scene.add(sun);
    const floor = new T.Mesh(new T.PlaneGeometry(80, 80), new T.ShadowMaterial({ opacity: P.floor_shadow, color: P.floor_ink }));
    floor.rotation.x = -Math.PI / 2; floor.position.y = -.05; floor.receiveShadow = true; scene.add(floor);
    const textures = [];
    let queued = false, settle = 0, refining = 0;
    const v = {
      T, scene, cam, sun, floor, pose: Object.assign({ ang: .9, dist: 18, yaw: 0, origin: [0, 0, 0], look: [0, 0, 0] }, pose),
      // look/origin become plain indexed objects: GSAP would read an array target as a list of targets
      extent(e) { Object.assign(sun.shadow.camera, { left: -e, right: e, top: e, bottom: -e }); sun.shadow.camera.updateProjectionMatrix(); },
      // moving tier: one frame at ≤ dpr_move, then a refined frame once nothing has moved for refine_ms
      paint() {
        queued = false; clearTimeout(settle); refining++; delete host.dataset.kzfRefined;
        const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return;
        const full = Math.min(P.dpr_max, g.devicePixelRatio || 1), cw = Math.round(w * full), ch = Math.round(h * full);
        if (cv.width !== cw || cv.height !== ch) { cv.width = cw; cv.height = ch; }
        const d = Math.min(P.dpr_move, full), pw = Math.round(w * d), ph = Math.round(h * d);
        v.aim(w, h); cam.clearViewOffset(); cam.updateProjectionMatrix();
        const src = frame(scene, cam, pw, ph); ctx.clearRect(0, 0, cw, ch); ctx.drawImage(src, 0, 0, pw, ph, 0, 0, cw, ch);
        settle = setTimeout(v.refine, P.refine_ms);
      },
      // refined tier: refine_frames renders with fixed sub-pixel offsets averaged off-screen, a few per animation frame;
      // a new paint cancels it. Same offsets every time, so a seek to the same moment gives the same pixels.
      refine() {
        const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return;
        // only a stage the audience can see is refined (hidden slides keep their moving-tier frame until shown)
        const r = host.getBoundingClientRect();
        const seen = host.checkVisibility ? host.checkVisibility({ opacityProperty: true, visibilityProperty: true }) : !!host.offsetParent;
        if (!seen || r.bottom <= 0 || r.right <= 0 || r.top >= g.innerHeight || r.left >= g.innerWidth) return;
        const run = ++refining, N = P.refine_frames, pw = cv.width, ph = cv.height;
        const acc = doc.createElement('canvas'); acc.width = pw; acc.height = ph; const ax = acc.getContext('2d');
        ax.globalCompositeOperation = 'lighter'; ax.globalAlpha = 1 / N;
        let i = 0;
        const chunk = () => {
          if (run !== refining) return;
          for (let k = 0; k < 3 && i < N; k++, i++) {
            const a = (i + .5) / N, r = Math.sqrt(a) * .5, th = i * 2.399963;
            v.aim(w, h); cam.setViewOffset(pw, ph, Math.cos(th) * r, Math.sin(th) * r, pw, ph); cam.updateProjectionMatrix();
            ax.drawImage(frame(scene, cam, pw, ph), 0, 0);
          }
          cam.clearViewOffset(); cam.updateProjectionMatrix();
          if (i < N) { g.requestAnimationFrame(chunk); return; }
          ctx.clearRect(0, 0, pw, ph); ctx.drawImage(acc, 0, 0); host.dataset.kzfRefined = '1';
        };
        chunk();
      },
      aim(w, h) {
        const p = v.pose, o = p.origin, wf = P.wide_fit, dist = p.dist * (p.wide ? Math.min(1, Math.max(wf[1], wf[0] / (w / h))) : 1);
        cam.aspect = w / h;
        cam.position.set(o[0] + Math.sin(p.yaw) * dist * Math.cos(p.ang), o[1] + Math.sin(p.ang) * dist, o[2] + Math.cos(p.yaw) * dist * Math.cos(p.ang));
        cam.lookAt(p.look[0], p.look[1], p.look[2]);
      },
      // one repaint per GSAP tick: tweens mark the view dirty, a microtask paints once after the tick (and right after a seek)
      dirty() { if (!queued) { queued = true; queueMicrotask(v.paint); } },
      upd() { return { onUpdate: v.dirty }; },
      // camera-facing text (a flat label on the floor is foreshortened to an unreadable size)
      label(text, o = {}) {
        const size = o.px || 64, weight = o.weight || 600, c = doc.createElement('canvas'), x = c.getContext('2d');
        const font = `${weight} ${size}px "PingFang SC","Microsoft YaHei",sans-serif`; x.font = font;
        const w = Math.ceil(x.measureText(text).width) + 16, hpx = Math.ceil(size * 1.35);
        const dot = o.dot ? Math.round(size * .9) : 0;
        c.width = w + dot; c.height = hpx; x.font = font; x.textBaseline = 'middle'; x.textAlign = 'left';
        if (dot) { x.fillStyle = o.dot; x.beginPath(); x.arc(8 + size * .32, hpx / 2, size * .3, 0, Math.PI * 2); x.fill(); }
        x.fillStyle = o.color || P.label || '#4a4038'; x.fillText(text, 8 + dot, hpx / 2);
        const tx = new T.CanvasTexture(c); tx.colorSpace = T.SRGBColorSpace; tx.anisotropy = 8; textures.push(tx);
        const sp = new T.Sprite(new T.SpriteMaterial({ map: tx, transparent: true, depthWrite: false, depthTest: o.depthTest !== false }));
        const hw = o.height || .5; sp.scale.set(hw * c.width / hpx, hw, 1); if (o.depthTest === false) sp.renderOrder = 10;
        sp.center.set(o.align === 'right' ? 1 : o.align === 'left' ? 0 : .5, .5);
        return sp;
      },
      dispose() { refining++; clearTimeout(settle); ro.disconnect(); textures.forEach(t => t.dispose()); scene.traverse(o => { o.geometry?.dispose(); o.material?.dispose?.(); }); }
    };
    v.pose.look = { ...v.pose.look }; v.pose.origin = { ...v.pose.origin };
    const ro = new ResizeObserver(() => v.paint()); ro.observe(host);
    return v;
  }
  const lin = (T, hex) => new T.Color(hex);   // r152+ colour management converts sRGB hex to linear
  // physical material with the token clearcoat (candy look under the studio environment)
  const pbr = (T, o) => new T.MeshPhysicalMaterial({ clearcoat: P3().clearcoat[0], clearcoatRoughness: P3().clearcoat[1], ...o });
  const mats = list => list.map(m => m.material).filter(Boolean);

  /* ======================= 3D stages ======================= */

  /* platforms — completeness: one rounded platform per group, one tile per item, missing items as outlined ghosts */
  define('platforms', (host, data) => {
    const P = P3(), groups = data.groups || [];
    need(groups.length, 'platforms 需要 groups：[{name, due, got}]');
    const maxDue = Math.max(...groups.map(x => x.due)), pitch = .68, width = Math.max(6, maxDue * pitch + 1.2);
    const fit = Math.max(1, (width + 3) / 11.4);
    const v = view3d(host, { ang: P.camera.angle, dist: P.camera.distance * fit, yaw: -.18, origin: [-1, 0, 0], look: P.camera.look_at, wide: true }), T = v.T;
    v.extent(Math.max(10, width / 2 + 3));
    const plats = [], tiles = [], miss = [];
    groups.forEach((gr, k) => {
      const z = (k - (groups.length - 1) / 2) * 1.9;
      const p = new T.Mesh(rbox(T, width, .22, 1.4, .35), pbr(T, { color: P.platform, roughness: .55, transparent: true }));
      p.position.set(0, 0, z); p.receiveShadow = p.castShadow = true; v.scene.add(p); plats.push(p);
      for (let i = 0; i < gr.due; i++) {
        const geo = rbox(T, .5, .5, .7, .12), x = -width / 2 + .6 + i * pitch;
        if (i < gr.got) {
          const m = new T.Mesh(geo, pbr(T, { color: lin(T, P.tiles[k % 2]), roughness: .35, metalness: .05, transparent: true }));
          m.position.set(x, .27, z); m.castShadow = true; v.scene.add(m); tiles.push(m); continue;
        }
        // a missing item: outline only (feature edges, not the bevel triangulation) over a faint ghost face
        const ghost = new T.LineSegments(new T.EdgesGeometry(geo, 30), new T.LineBasicMaterial({ color: new T.Color(P.missing), transparent: true }));
        ghost.add(new T.Mesh(geo, new T.MeshBasicMaterial({ color: new T.Color(P.missing), transparent: true, opacity: .16, depthWrite: false })));
        ghost.position.set(x, .27, z); v.scene.add(ghost); tiles.push(ghost); miss.push(ghost);
      }
      const lab = v.label(gr.name, { height: .64, align: 'right' }); lab.position.set(-width / 2 - .25, .35, z); v.scene.add(lab);
    });
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        rise(tl, at) { tl.from(plats.map(p => p.position), { y: -3, stagger: .12, duration: D, ease: ease(), ...u }, at).from(mats(plats), { opacity: 0, stagger: .12, duration: D * .8, ...u }, '<'); },
        fill(tl, at) {
          tl.from(tiles.map(m => m.position), { y: 4, stagger: .03, duration: .7, ease: 'bounce.out', ...u }, at).from(mats(tiles), { opacity: 0, stagger: .03, duration: .3, ...u }, '<')
            .from(miss.map(m => m.children[0].material), { opacity: 0, duration: .3, ...u }, '<');
        },
        miss(tl, at) {
          const alert = new T.Color(P.missing_alert);
          tl.to(miss.map(m => m.scale), { x: 1.25, y: 1.25, z: 1.25, yoyo: true, repeat: 1, duration: .4, stagger: .08, ...u }, at)
            .to(miss.map(m => m.material.color), { r: alert.r, g: alert.g, b: alert.b, duration: .4, ...u }, '<')
            .to(miss.map(m => m.children[0].material.color), { r: alert.r, g: alert.g, b: alert.b, duration: .4, ...u }, '<')
            .to(miss.map(m => m.children[0].material), { opacity: .3, duration: .4, ...u }, '<');
        },
        orbit(tl, at) { tl.to(v.pose, { ang: P.camera.angle_end, dist: P.camera.distance_end * fit, duration: 1.6, ease: 'power2.inOut', ...u }, at); }
      }
    };
  });

  /* towers — magnitude: one rounded column per category on a plinth; the focus (or largest) column stays lit */
  define('towers', (host, data) => {
    const items = data.items || [], unit = data.unit || '';
    need(items.length >= 2 && items.length <= 8, 'towers 需要 2–8 个 items：[{name, value}]');
    items.forEach(x => need(Number.isFinite(x.value) && x.value >= 0, `towers「${x.name}」的 value 不是非负数`));
    const P = P3(), C = ST().palette, n = items.length, max = Math.max(...items.map(x => x.value)) || 1, H = 4.4, pitch = 1.75;
    const fi = items.findIndex(x => x.focus) >= 0 ? items.findIndex(x => x.focus) : items.findIndex(x => x.value === max);
    const width = n * pitch;
    const v = view3d(host, { ang: .36, dist: Math.max(15, width * 1.18 + 6), yaw: .5, look: [0, H * .32, 0] }), T = v.T;
    v.extent(width / 2 + 4);
    const plinth = new T.Mesh(rbox(T, width + .9, .24, 2.4, .32), pbr(T, { color: P.platform, roughness: .55, transparent: true }));
    plinth.receiveShadow = plinth.castShadow = true; v.scene.add(plinth);
    const cols = [], vals = [], names = [], hs = items.map(it => Math.max(.06, it.value / max * H));
    items.forEach((it, i) => {
      const x = (i - (n - 1) / 2) * pitch, h = hs[i];
      const m = new T.Mesh(rbox(T, 1, 1, 1, .14), pbr(T, { color: lin(T, P.tiles[0]), roughness: .32, metalness: .04, transparent: true }));
      m.position.set(x, .24, 0); m.scale.y = h; m.castShadow = true; v.scene.add(m); cols.push(m);
      const vl = v.label(fmt(it.value) + unit, { height: .5, weight: 700, color: INK().title }); vl.position.set(x, .24 + h + .5, 0); v.scene.add(vl); vals.push(vl);
      const nl = v.label(it.name, { height: .42, color: INK().body, depthTest: false }); nl.position.set(x, .3, 1.95); v.scene.add(nl); names.push(nl);
    });
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        rise(tl, at) {
          tl.from(plinth.position, { y: -2.5, duration: D, ease: ease(), ...u }, at).from([plinth.material, ...mats(cols)], { opacity: 0, duration: D * .7, ...u }, '<')
            .from(mats(names), { opacity: 0, duration: .5, stagger: .06, ...u }, `<${D * .4}`);
        },
        // columns stand as stubs until this scene (fromTo renders its start state when the timeline is built)
        grow(tl, at) {
          cols.forEach((c, i) => tl.fromTo(c.scale, { y: .02 }, { y: hs[i], duration: 1.1, ease: 'power3.out', immediateRender: true, ...u }, at + i * each(n, .12)));
          tl.fromTo(mats(vals), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n, .12), immediateRender: true, ...u }, at + .7);
        },
        focus(tl, at) {
          const dim = lin(T, hexMix(C.soft, C.fill[0], .35)), hot = lin(T, C.fill[2]);
          tl.to(cols.filter((_, i) => i !== fi).map(c => c.material.color), { r: dim.r, g: dim.g, b: dim.b, duration: .5, ...u }, at)
            .to(cols[fi].material.color, { r: hot.r, g: hot.g, b: hot.b, duration: .5, ...u }, at)
            .to(vals[fi].scale, { x: vals[fi].scale.x * 1.25, y: vals[fi].scale.y * 1.25, duration: .5, ease: back(2), ...u }, at)
            .to(mats(vals.filter((_, i) => i !== fi)), { opacity: .55, duration: .5, ...u }, at);
        },
        orbit(tl, at) { tl.to(v.pose, { yaw: .12, ang: .28, duration: 1.6, ease: 'power2.inOut', ...u }, at); }
      }
    };
  });

  /* rings — completeness: one ring per item, the arc is done/total, the overall share sits in the middle */
  define('rings', (host, data) => {
    const items = data.items || [];
    need(items.length >= 2 && items.length <= 5, 'rings 需要 2–5 个 items：[{name, done, total}]');
    items.forEach(x => need(x.total > 0 && x.done >= 0 && x.done <= x.total, `rings「${x.name}」的 done/total 不合法`));
    const C = ST().palette, P = P3(), n = items.length;
    const v = view3d(host, { ang: .22, dist: 15 + n * .9, yaw: -.06, look: [-2.1, -.1, 0] }), T = v.T;
    v.extent(8); v.floor.visible = false;
    const grp = new T.Group(); grp.rotation.x = -.42; grp.position.y = .25; v.scene.add(grp);
    const R0 = 1.65, step = .78, tube = .27, RS = 14, arcs = [], caps = [], tracks = [], labs = [];
    const share = items.map(x => x.done / x.total), low = share.indexOf(Math.min(...share));
    items.forEach((it, k) => {
      const r = R0 + (n - 1 - k) * step, p = share[k], col = hexMix(C.fill[0], C.fill[2], n > 1 ? k / (n - 1) : 0);
      const tr = new T.Mesh(new T.TorusGeometry(r, tube * .92, 12, 140), pbr(T, { color: lin(T, C.track), roughness: .7, transparent: true }));
      grp.add(tr); tracks.push(tr);
      const arcCurve = new T.Curve(); arcCurve.getPoint = (t, out = new T.Vector3()) => { const a = Math.PI / 2 - t * 2 * Math.PI * Math.max(p, .001); return out.set(Math.cos(a) * r, Math.sin(a) * r, 0); };
      const segs = Math.max(8, Math.round(180 * p)), geo = new T.TubeGeometry(arcCurve, segs, tube, RS, false);
      const mat = pbr(T, { color: lin(T, col), roughness: .3, metalness: .05, emissive: lin(T, col), emissiveIntensity: .08 });
      const arc = new T.Mesh(geo, mat); arc.castShadow = true; grp.add(arc);
      const cap0 = new T.Mesh(new T.SphereGeometry(tube, 20, 14), mat), cap1 = new T.Mesh(new T.SphereGeometry(tube, 20, 14), mat);
      cap0.position.copy(arcCurve.getPoint(0)); cap1.position.copy(arcCurve.getPoint(1)); grp.add(cap0, cap1);
      arcs.push({ arc, geo, segs, curve: arcCurve, cap1, mat, p }); caps.push(cap1);
      const lab = v.label(`${it.name}  ${pct(it.done, it.total)}%`, { height: .44, align: 'left', color: k === low ? RISK() : INK().title, weight: 700, dot: col, depthTest: false });
      lab.position.set(-(R0 + (n - 1) * step) - 4.6, (n - 1) * .42 - k * .84 + .2, 0); v.scene.add(lab); labs.push(lab);
    });
    const done = items.reduce((a, x) => a + x.done, 0), total = items.reduce((a, x) => a + x.total, 0);
    const mid = v.label(`${pct(done, total)}%`, { height: .95, weight: 800, color: INK().title, depthTest: false }); mid.position.set(0, .12, .2); grp.add(mid);
    const midSub = v.label(data.center || '整体', { height: .34, color: INK().muted, depthTest: false }); midSub.position.set(0, -.62, .2); grp.add(midSub);
    const setP = (a, t) => { a.geo.setDrawRange(0, Math.round(t * a.segs) * RS * 6); a.cap1.position.copy(a.curve.getPoint(Math.max(t, .0005))); a.cap1.visible = t > .002; };
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        rise(tl, at) {
          tl.from(grp.scale, { x: .72, y: .72, z: .72, duration: D, ease: ease(), ...u }, at).from(grp.rotation, { z: -.5, duration: D, ease: ease(), ...u }, at)
            .from(mats(tracks), { opacity: 0, duration: .6, stagger: .08, ...u }, at);
        },
        // arcs and labels stay empty until this scene: set at build, swept by the tweens
        fill(tl, at) {
          arcs.forEach((a, k) => { setP(a, 0); const o = { t: 0 }; tl.fromTo(o, { t: 0 }, { t: 1, duration: 1.3, ease: 'power2.inOut', immediateRender: false, onUpdate: () => { setP(a, o.t); v.dirty(); } }, at + k * .14); });
          tl.fromTo(mats(labs), { opacity: 0 }, { opacity: 1, duration: .5, stagger: .14, immediateRender: true, ...u }, at + .3)
            .fromTo([mid.material, midSub.material], { opacity: 0 }, { opacity: 1, duration: .6, immediateRender: true, ...u }, at + .9);
        },
        focus(tl, at) {
          const a = arcs[low], hot = lin(T, C.alert);
          tl.to(a.mat.color, { r: hot.r, g: hot.g, b: hot.b, duration: .45, ...u }, at).to(a.mat.emissive, { r: hot.r, g: hot.g, b: hot.b, duration: .45, ...u }, at)
            .to(a.mat, { emissiveIntensity: .35, duration: .3, yoyo: true, repeat: 3, ...u }, at)
            .to(labs[low].scale, { x: labs[low].scale.x * 1.18, y: labs[low].scale.y * 1.18, duration: .45, ease: back(2), ...u }, at);
        },
        orbit(tl, at) { tl.to(grp.rotation, { x: -.62, y: .2, duration: 1.6, ease: 'power2.inOut', ...u }, at).to(v.pose, { ang: .3, duration: 1.6, ease: 'power2.inOut', ...u }, at); }
      }
    };
  });

  /* constellation — relation: a hub and the parties around it; links grow out and pulses travel to every node */
  define('constellation', (host, data) => {
    const nodes = data.nodes || [], hub = data.hub || {};
    need(hub.name && nodes.length >= 3 && nodes.length <= 10, 'constellation 需要 hub: {name} 与 3–10 个 nodes：[{name}]');
    const C = ST().palette, n = nodes.length;
    const v = view3d(host, { ang: .62, dist: 18.5, yaw: .12, look: [0, .1, -.9], wide: true }), T = v.T;
    v.extent(9); v.floor.material.opacity = P3().floor_shadow * .6;
    const hubMat = pbr(T, { color: lin(T, C.fill[1]), roughness: .3, metalness: .1, emissive: lin(T, C.fill[2]), emissiveIntensity: .18 });
    const hubM = new T.Mesh(new T.SphereGeometry(.95, 48, 32), hubMat); hubM.position.y = .9; hubM.castShadow = true; v.scene.add(hubM);
    const hubL = v.label(hub.name, { height: .56, weight: 700, color: INK().title, depthTest: false }); hubL.position.set(0, 2.25, 0); v.scene.add(hubL);
    const ws = nodes.map(x => x.weight || 1), wmax = Math.max(...ws);
    const nm = [], nl = [], links = [], pulses = [];
    nodes.forEach((nd, i) => {
      const a = -Math.PI / 2 + (i + .5) * 2 * Math.PI / n, pos = new T.Vector3(Math.cos(a) * 6.2, .55 + (i % 2 ? .7 : 0), Math.sin(a) * 2.7);
      const r = .34 + .22 * (ws[i] / wmax);
      const m = new T.Mesh(new T.SphereGeometry(r, 32, 24), pbr(T, { color: lin(T, C.soft), roughness: .35, emissive: lin(T, C.fill[0]), emissiveIntensity: .05, transparent: true }));
      m.position.copy(pos); m.castShadow = true; v.scene.add(m); nm.push(m);
      const l = v.label(nd.name, { height: .46, weight: 600, color: INK().title, depthTest: false }); l.position.set(pos.x, pos.y + r + .42, pos.z); v.scene.add(l); nl.push(l);
      const mid = new T.Vector3((pos.x) / 2, Math.max(pos.y, hubM.position.y) + 1.1, pos.z / 2);
      const curve = new T.QuadraticBezierCurve3(hubM.position.clone(), mid, pos.clone());
      const geo = new T.TubeGeometry(curve, 48, .04, 6, false);
      const ln = new T.Mesh(geo, pbr(T, { color: lin(T, C.link), roughness: .6 })); v.scene.add(ln);
      links.push({ geo, curve });
      const pu = new T.Mesh(new T.SphereGeometry(.13, 16, 12), new T.MeshBasicMaterial({ color: lin(T, C.fill[2]), transparent: true }));
      pu.visible = false; v.scene.add(pu); pulses.push(pu);
    });
    const setL = (L, t) => L.geo.setDrawRange(0, Math.round(t * 48) * 6 * 6);
    const D = F().motion.fx.three.dur, u = v.upd(), PD = ST().pulse.dur;
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        hub(tl, at) {
          tl.from(hubM.scale, { x: .01, y: .01, z: .01, duration: .8, ease: back(1.8), ...u }, at).from(hubL.material, { opacity: 0, duration: .5, ...u }, at + .3);
        },
        // nodes wait at the hub, hidden, until this scene
        nodes(tl, at) {
          nm.forEach((m, i) => {
            const s = at + i * each(n, .1);
            tl.fromTo(m.scale, { x: .01, y: .01, z: .01 }, { x: 1, y: 1, z: 1, duration: .7, ease: back(1.6), immediateRender: true, ...u }, s)
              .from(m.position, { x: 0, y: hubM.position.y, z: 0, duration: .8, ease: ease(), ...u }, s)
              .fromTo(nl[i].material, { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, s + .4);
          });
        },
        links(tl, at) { links.forEach((L, i) => { setL(L, 0); const o = { t: 0 }; tl.fromTo(o, { t: 0 }, { t: 1, duration: .8, ease: 'power1.inOut', immediateRender: false, onUpdate: () => { setL(L, o.t); v.dirty(); } }, at + i * each(n, .06)); }); },
        pulse(tl, at) {
          pulses.forEach((pu, i) => {
            const o = { t: 0 }, s = at + i * each(n, .1), L = links[i];
            tl.fromTo(o, { t: 0 }, { t: 1, duration: PD * .6, ease: 'power1.inOut', immediateRender: false,
              onUpdate: () => { pu.visible = o.t > 0 && o.t < 1; pu.position.copy(L.curve.getPoint(o.t)); v.dirty(); } }, s)
              .to(nm[i].scale, { x: 1.22, y: 1.22, z: 1.22, duration: .2, yoyo: true, repeat: 1, ...u }, s + PD * .6)
              .to(nm[i].material, { emissiveIntensity: .4, duration: .2, yoyo: true, repeat: 1, ...u }, s + PD * .6);
          });
          tl.to(v.pose, { yaw: -.12, ang: .56, duration: PD + .8, ease: 'power1.inOut', ...u }, at);
        }
      }
    };
  });

  /* morph — completeness / magnitude: one cube per item is the carrier through every scene — one block (the total),
     one column per group (received at the bottom, missing on top), the missing cubes fly to a gap tray, the camera
     swings round to read the columns */
  define('morph', (host, data) => {
    const gs = data.groups || [], unit = data.unit || '份', n = gs.length;
    need(n >= 2 && n <= 6, 'morph 需要 2–6 组 groups：[{name, due, got}]');
    gs.forEach(x => need(Number.isInteger(x.due) && x.due > 0 && Number.isInteger(x.got) && x.got >= 0 && x.got <= x.due, `morph 组「${x.name}」的 due/got 不合法`));
    const due = gs.reduce((a, x) => a + x.due, 0), got = gs.reduce((a, x) => a + x.got, 0), lack = due - got;
    need(due <= 160, 'morph 最多 160 块（due 合计），更多时换 rings 或 towers');
    const C = ST().palette, s = .5, pitch = s + .08;
    const pc = Math.ceil(Math.sqrt(due / 2)), pile = i => { const l = Math.floor(i / (pc * pc)), r = i % (pc * pc); return [(r % pc - (pc - 1) / 2) * pitch, s / 2 + l * pitch, (Math.floor(r / pc) - (pc - 1) / 2) * pitch]; };
    const cx = k => (k - (n - 1) / 2) * 2, col = (k, j) => { const l = Math.floor(j / 2); return [cx(k) + (j % 2 - .5) * pitch, s / 2 + l * pitch, 0]; };
    const tx0 = cx(n - 1) + 1.9, tray = m => { const l = Math.floor(m / 4), q = m % 4; return [tx0 + (q % 2) * pitch, s / 2 + l * pitch, (Math.floor(q / 2) - .5) * pitch]; };
    const span = tx0 + 1.6 - (cx(0) - 1);
    const v = view3d(host, { ang: .62, dist: 9 + pc * .9, yaw: .5, look: [0, .5, 0] }), T = v.T;
    v.extent(span / 2 + 3);
    const base = lin(T, C.fill[1]), geo = rbox(T, s, s, s, .07), tone = k => hexMix(C.fill[0], C.fill[2], n > 1 ? k / (n - 1) : 0);
    const recv = gs.map(() => pbr(T, { color: base.clone(), roughness: .34, metalness: .05 }));
    const miss = gs.map(() => pbr(T, { color: base.clone(), roughness: .34, metalness: .05 }));
    const cubes = []; let i = 0, m = 0;
    gs.forEach((gr, k) => {
      for (let j = 0; j < gr.due; j++, i++) {
        const lost = j >= gr.got, c = new T.Mesh(geo, lost ? miss[k] : recv[k]);
        c.position.set(...pile(i)); c.castShadow = true; v.scene.add(c);
        cubes.push({ c, p0: pile(i), p1: col(k, j), p2: lost ? tray(m++) : null });
      }
    });
    const layers = k => Math.ceil(gs[k].due / 2), top = (k, cnt) => s + Math.ceil(cnt / 2) * pitch;
    const total = v.label(`应收 ${fmt(due)} ${unit}`, { height: .62, weight: 700, color: INK().title, depthTest: false });
    total.position.set(0, s + Math.ceil(due / (pc * pc)) * pitch + .7, 0); v.scene.add(total);
    const names = gs.map((gr, k) => { const l = v.label(gr.name, { height: .42, color: INK().body, depthTest: false }); l.position.set(cx(k), .2, 1.5); v.scene.add(l); return l; });
    const dues = gs.map((gr, k) => { const l = v.label(`${gr.due} ${unit}`, { height: .4, weight: 600, color: INK().muted, depthTest: false }); l.position.set(cx(k), top(k, gr.due) + .35, 0); v.scene.add(l); return l; });
    const gots = gs.map((gr, k) => { const l = v.label(`${gr.got}/${gr.due}`, { height: .46, weight: 700, color: gr.got < gr.due ? RISK() : INK().title, depthTest: false }); l.position.set(cx(k), top(k, gr.got) + .4, 0); v.scene.add(l); return l; });
    const trayL = v.label(`缺口 ${fmt(lack)} ${unit}`, { height: .5, weight: 700, color: RISK(), depthTest: false });
    trayL.position.set(tx0 + pitch / 2, s + Math.ceil(lack / 4) * pitch + .55, 0); v.scene.add(trayL);
    const sum = v.label(`已收 ${fmt(got)}/${fmt(due)} ${unit} · ${pct(got, due)}%`, { height: .5, weight: 800, color: INK().title, depthTest: false });
    sum.position.set(0, -.75, 2.2); v.scene.add(sum);
    const D = F().motion.fx.three.dur, u = v.upd(), spread = each(cubes.length, .012);
    // one cube along a lifted arc between two slots, written from a proxy so the timeline can scrub it both ways
    const fly = (tl, c, a, b, at, dur, lift) => {
      const o = { t: 0 };
      tl.fromTo(o, { t: 0 }, { t: 1, duration: dur, ease: 'power2.inOut', immediateRender: false,
        onUpdate: () => { const t = o.t; c.position.set(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + Math.sin(Math.PI * t) * lift, a[2] + (b[2] - a[2]) * t); v.dirty(); } }, at);
    };
    const hide = (tl, list, at) => tl.fromTo(mats(list), { opacity: 0 }, { opacity: 1, duration: .45, stagger: .06, immediateRender: true, ...u }, at);
    for (const l of [...names, ...dues, ...gots, trayL, sum]) l.material.opacity = 0;
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        pile(tl, at) {
          tl.from(cubes.map(x => x.c.position), { y: '+=5', duration: .6, ease: 'bounce.out', stagger: spread, ...u }, at)
            .from(total.material, { opacity: 0, duration: .5, ...u }, at + .6);
        },
        split(tl, at) {
          cubes.forEach((x, q) => fly(tl, x.c, x.p0, x.p1, at + q * spread * .6, 1.1, 1.2));
          tl.to(total.material, { opacity: 0, duration: .3, ...u }, at);
          gs.forEach((_, k) => { const col = lin(T, tone(k)); tl.to([recv[k].color, miss[k].color], { r: col.r, g: col.g, b: col.b, duration: .6, ...u }, at + .4); });
          hide(tl, [...names, ...dues], at + 1);
          tl.to(v.pose, { ang: .34, dist: Math.max(13, span * 1.12), yaw: .16, duration: 1.4, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 1: Math.max(...gs.map((_, k) => layers(k))) * pitch * .42, duration: 1.4, ease: 'power2.inOut', ...u }, at);
        },
        gaps(tl, at) {
          const alert = lin(T, C.alert);
          tl.to(miss.map(x => x.color), { r: alert.r, g: alert.g, b: alert.b, duration: .4, ...u }, at);
          cubes.filter(x => x.p2).forEach((x, q) => fly(tl, x.c, x.p1, x.p2, at + .35 + q * each(lack, .05), 1, 1.6));
          tl.to(mats(dues), { opacity: 0, duration: .3, ...u }, at);
          hide(tl, [...gots, trayL], at + 1.1);
        },
        orbit(tl, at) {
          tl.to(v.pose, { yaw: -.32, ang: .3, duration: 1.8, ease: 'power2.inOut', ...u }, at);
          hide(tl, [sum], at + .6);
        }
      }
    };
  });

  /* stream — attrition / process: dots run down a glass channel and through one gate per stage; the dots a stage
     loses drop out in front of its gate into a counted pile; the largest loss is lit; the camera tracks the channel */
  define('stream', (host, data) => {
    const st = data.stages || [], unit = data.unit || '例', n = st.length;
    need(n >= 3 && n <= 6, 'stream 需要 3–6 级 stages：[{name, value}]');
    st.forEach((x, i) => need(Number.isFinite(x.value) && x.value >= 0 && (i === 0 || x.value <= st[i - 1].value), `stream 第 ${i + 1} 级「${x.name}」的 value 须为非负且不大于上一级`));
    need(st[0].value > 0, 'stream 第一级的 value 须大于 0');
    const C = ST().palette, N = 60, seg = 3, L = n * seg, x0 = -L / 2, sx = j => x0 + (j + .5) * seg, gx = j => x0 + j * seg;
    const kept = st.map(x => Math.round(x.value / st[0].value * N)), drop = st.map((x, j) => (j ? st[j - 1].value - x.value : 0));
    const worst = drop.indexOf(Math.max(...drop));
    const v = view3d(host, { ang: .5, dist: L * 1.05 + 6, yaw: .42, look: [.8, .5, .3], wide: true }), T = v.T;
    v.extent(L / 2 + 3);
    const glass = pbr(T, { color: 0xffffff, roughness: .3, transparent: true, opacity: .92 });
    const chan = new T.Mesh(rbox(T, L + 1.2, .2, 1.8, .3), glass); chan.receiveShadow = chan.castShadow = true; v.scene.add(chan);
    const gates = [], gmats = [];
    for (let j = 1; j < n; j++) {
      const mat = pbr(T, { color: lin(T, C.soft), roughness: .4, transparent: true }), grp = new T.Group();
      const post = () => new T.Mesh(rbox(T, .18, 1.5, .18, .06), mat);
      const a = post(), b = post(), bar = new T.Mesh(rbox(T, .18, .18, 2.2, .06), mat);
      a.position.set(0, .2, -1); b.position.set(0, .2, 1); bar.position.set(0, 1.62, 0);
      for (const q of [a, b, bar]) { q.castShadow = true; grp.add(q); }
      grp.position.x = gx(j); v.scene.add(grp); gates.push(grp); gmats.push(mat);
    }
    const nameL = st.map((x, j) => { const l = v.label(x.name, { height: .5, color: INK().body, depthTest: false }); l.position.set(sx(j), 2.25, -.4); v.scene.add(l); return l; });
    const valL = st.map((x, j) => { const l = v.label(`${fmt(x.value)} ${unit}`, { height: .6, weight: 800, color: INK().title, depthTest: false }); l.position.set(sx(j), 2.95, -.4); v.scene.add(l); return l; });
    const pileAt = (j, q) => [gx(j) + (q % 4 - 1.5) * .3, .13 + Math.floor(q / 12) * .26, 2 + (Math.floor(q / 4) % 3) * .3];
    const dropL = st.map((x, j) => {
      if (!j) return null;
      const l = v.label(`−${fmt(drop[j])}（${pct(drop[j], st[j - 1].value)}%）`, { height: .46, weight: 700, color: j === worst ? RISK() : INK().muted, depthTest: false });
      l.position.set(gx(j), 1 + Math.ceil((kept[j - 1] - kept[j]) / 12) * .26, 3.1); v.scene.add(l); return l;
    }).filter(Boolean);
    const endL = v.label(`留下 ${pct(st[n - 1].value, st[0].value)}%`, { height: .5, weight: 800, color: C.fill[2], depthTest: false });
    endL.position.set(L / 2 + .62, 1.75, 0); v.scene.add(endL);
    // each dot knows the gate it leaves at (or none) and its lane
    const dotMat = pbr(T, { color: lin(T, C.fill[1]), roughness: .3, emissive: lin(T, C.fill[2]), emissiveIntensity: .15 });
    const lostMat = pbr(T, { color: lin(T, C.fill[1]), roughness: .4 });
    const dots = [], dgeo = new T.SphereGeometry(.12, 16, 12), counts = st.map(() => 0);
    for (let q = 0; q < N; q++) {
      const leave = kept.findIndex(k => q >= k), lost = leave > 0, lane = ((q * 7) % 9 - 4) * .17;
      const d = new T.Mesh(dgeo, lost ? lostMat : dotMat); d.castShadow = true; d.visible = false; v.scene.add(d);
      const rest = lost ? pileAt(leave, counts[leave]++) : [L / 2 + .35 + (q % 3) * .27, .45 + Math.floor(q / 9) % 3 * .25, ((q / 3 | 0) % 3 - 1) * .27];
      dots.push({ d, lost, leave, lane, end: rest });
    }
    for (const l of [...nameL, ...valL, ...dropL, endL]) l.material.opacity = 0;
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        build(tl, at) {
          tl.from(chan.position, { y: -2, duration: D, ease: ease(), ...u }, at).from(glass, { opacity: 0, duration: D * .7, ...u }, at)
            .from(gates.map(q => q.scale), { y: .01, duration: .6, stagger: .1, ease: back(1.6), ...u }, at + .4)
            .fromTo(mats([...nameL, ...valL]), { opacity: 0 }, { opacity: 1, duration: .45, stagger: .05, immediateRender: true, ...u }, at + .6);
        },
        flow(tl, at) {
          dots.forEach((o, q) => {
            const p = { t: 0 }, xs = x0 - .4, xe = o.lost ? gx(o.leave) - .35 : o.end[0], dur = 1.6 + (xe - xs) / L * 1.2, y = .35;
            tl.fromTo(p, { t: 0 }, { t: 1, duration: dur, ease: 'none', immediateRender: false, onUpdate: () => {
              const t = p.t, run = o.lost ? .72 : .85; o.d.visible = t > 0;
              if (t <= run) { const k = t / run; o.d.position.set(xs + (xe - xs) * k, y, o.lane * (o.lost ? 1 : 1 - k * .4)); }
              else { const k = (t - run) / (1 - run), e = o.end, sxp = xe, szp = o.lost ? o.lane : o.lane * .6;
                o.d.position.set(sxp + (e[0] - sxp) * k, y + (e[1] - y) * k + (o.lost ? Math.sin(Math.PI * k) * .6 : 0), szp + (e[2] - szp) * k); }
              v.dirty(); } }, at + q * .03);
          });
          tl.fromTo(mats([...dropL, endL]), { opacity: 0 }, { opacity: 1, duration: .45, stagger: .15, immediateRender: true, ...u }, at + 2.1);
        },
        focus(tl, at) {
          const hot = lin(T, C.alert), j = worst;
          tl.to(gmats[j - 1].color, { r: hot.r, g: hot.g, b: hot.b, duration: .45, ...u }, at)
            .to(gates[j - 1].scale, { x: 1.25, y: 1.12, z: 1.12, duration: .5, ease: back(2), ...u }, at)
            .to(lostMat.color, { r: hot.r, g: hot.g, b: hot.b, duration: .45, ...u }, at)
            .to(mats(dropL.filter((_, k) => k + 1 !== j)), { opacity: .45, duration: .4, ...u }, at);
        },
        // a tracking shot down the channel, then back out to the whole run
        travel(tl, at) {
          tl.to(v.pose, { yaw: -.2, ang: .3, dist: L * .7 + 5, duration: 1.2, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 0: L * .18, duration: 1.2, ease: 'power2.inOut', ...u }, at)
            .to(v.pose, { yaw: .2, ang: .44, dist: L * 1.05 + 6, duration: 1.2, ease: 'power2.inOut', ...u }, at + 1.3)
            .to(v.pose.look, { 0: .8, duration: 1.2, ease: 'power2.inOut', ...u }, at + 1.3);
        }
      }
    };
  });

  /* runway — timeline: milestones stand along a glass track; the progress strip and a lit marker run to "now" while
     the camera rides along; the next milestone is lit */
  define('runway', (host, data) => {
    const it = data.items || [], n = it.length, now = Number(data.now);
    need(n >= 3 && n <= 7, 'runway 需要 3–7 个 items：[{when, name, owner?}]');
    need(Number.isFinite(now) && now >= 0 && now <= n - 1, `runway 的 now 须在 0 到 ${n - 1} 之间（第几项，可为小数）`);
    const C = ST().palette, gap = 3, L = (n - 1) * gap, x = i => -L / 2 + i * gap, nowX = -L / 2 + now * gap, next = Math.min(n - 1, Math.floor(now) + 1);
    const v = view3d(host, { ang: .3, dist: 9, yaw: -.85, origin: [x(0), 0, 0], look: [x(0) + 3, .8, 0], wide: true }), T = v.T;
    v.extent(L / 2 + 4);
    const track = new T.Mesh(rbox(T, L + 2.4, .18, 2, .3).translate(L / 2 + 1.2, 0, 0), pbr(T, { color: 0xffffff, roughness: .35, transparent: true }));
    track.position.x = -L / 2 - 1.2; track.receiveShadow = track.castShadow = true; v.scene.add(track);
    const strip = new T.Mesh(new T.BoxGeometry(1, .06, .36).translate(.5, 0, 0), pbr(T, { color: lin(T, C.fill[1]), roughness: .3, emissive: lin(T, C.fill[2]), emissiveIntensity: .12 }));
    strip.position.set(x(0), .21, .5); strip.scale.x = Math.max(.001, nowX - x(0)); v.scene.add(strip);
    const posts = [], flags = [], fmats = [], whenL = [], nameL = [];
    it.forEach((m, i) => {
      const mat = pbr(T, { color: lin(T, C.soft), roughness: .4 }), grp = new T.Group();
      const post = new T.Mesh(new T.CylinderGeometry(.06, .06, 1.6, 12), mat); post.position.y = .98;
      const flag = new T.Mesh(rbox(T, .9, .5, .12, .08), mat); flag.position.set(.45, 1.5, 0);
      for (const q of [post, flag]) { q.castShadow = true; grp.add(q); }
      grp.position.set(x(i), 0, -.35); v.scene.add(grp); posts.push(grp); fmats.push(mat);
      const w = v.label(m.when, { height: .52, weight: 800, color: INK().title, depthTest: false, align: 'left' }); w.position.set(x(i) - .05, 2.86, -.35); v.scene.add(w); whenL.push(w);
      const nm = v.label(m.name + (m.owner ? ` · ${m.owner}` : ''), { height: .4, color: INK().body, depthTest: false, align: 'left' }); nm.position.set(x(i) - .05, 2.36, -.35); v.scene.add(nm); nameL.push(nm);
    });
    const marker = new T.Mesh(new T.SphereGeometry(.24, 24, 16), pbr(T, { color: lin(T, C.fill[2]), emissive: lin(T, C.fill[1]), emissiveIntensity: .5, roughness: .25 }));
    marker.position.set(nowX, .45, .5); marker.castShadow = true; v.scene.add(marker);
    const nowL = v.label(data.nowLabel || '当前', { height: .4, weight: 700, color: C.fill[2], depthTest: false }); nowL.position.set(nowX, 1.05, .9); v.scene.add(nowL);
    for (const l of [...whenL, ...nameL, nowL]) l.material.opacity = 0;
    const D = F().motion.fx.three.dur, u = v.upd(), done = lin(T, C.fill[1]), wide = { ang: .48, dist: Math.max(16, L * 1.15 + 6), yaw: .16 };
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        track(tl, at) { tl.from(track.scale, { x: .01, duration: 1.2, ease: 'power3.out', ...u }, at).from(track.material, { opacity: 0, duration: .5, ...u }, at); },
        flags(tl, at) {
          posts.forEach((p, i) => tl.fromTo(p.scale, { y: .01 }, { y: 1, duration: .55, ease: back(1.8), immediateRender: true, ...u }, at + i * each(n, .14)));
          tl.fromTo(mats([...whenL, ...nameL]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n * 2, .07), immediateRender: true, ...u }, at + .3)
            .to(v.pose, { ...wide, duration: 1.4, ease: 'power2.inOut', ...u }, at).to(v.pose.origin, { 0: 0, duration: 1.4, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 0: 0, 1: .9, duration: 1.4, ease: 'power2.inOut', ...u }, at);
        },
        // the strip and the marker wait at the start until this scene; passed milestones turn orange as it reaches them
        run(tl, at) {
          const dur = 1.2 + now * .35;
          tl.fromTo(strip.scale, { x: .001 }, { x: Math.max(.001, nowX - x(0)), duration: dur, ease: 'power1.inOut', immediateRender: true, ...u }, at)
            .fromTo(marker.position, { x: x(0) }, { x: nowX, duration: dur, ease: 'power1.inOut', immediateRender: true, ...u }, at)
            .fromTo(nowL.position, { x: x(0) }, { x: nowX, duration: dur, ease: 'power1.inOut', immediateRender: true, ...u }, at)
            .fromTo(nowL.material, { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at);
          it.forEach((_, i) => { if (i <= now) tl.to(fmats[i].color, { r: done.r, g: done.g, b: done.b, duration: .35, ...u }, at + (now ? i / now : 0) * dur * .95); });
          tl.to(v.pose, { yaw: -.25, ang: .34, dist: Math.max(12, L * .8 + 5), duration: dur, ease: 'power1.inOut', ...u }, at)
            .to(v.pose.look, { 0: nowX * .6, duration: dur, ease: 'power1.inOut', ...u }, at);
        },
        focus(tl, at) {
          const hot = lin(T, C.fill[2]);
          tl.to(fmats[next].color, { r: hot.r, g: hot.g, b: hot.b, duration: .4, ...u }, at)
            .to(posts[next].scale, { x: 1.2, y: 1.2, z: 1.2, duration: .3, yoyo: true, repeat: 3, ...u }, at)
            .to(whenL[next].scale, { x: whenL[next].scale.x * 1.2, y: whenL[next].scale.y * 1.2, duration: .45, ease: back(2), ...u }, at)
            .to(v.pose, { ...wide, duration: 1.4, ease: 'power2.inOut', ...u }, at).to(v.pose.look, { 0: 0, duration: 1.4, ease: 'power2.inOut', ...u }, at);
        }
      }
    };
  });

  /* layers — relation / process: a stack of glass layers separates; each layer gets its name, its items land on it,
     one layer is lifted and lit while the others step back */
  define('layers', (host, data) => {
    const ls = data.layers || [], n = ls.length, fi = Number.isInteger(data.focus) ? data.focus : 0;
    need(n >= 3 && n <= 5, 'layers 需要 3–5 层 layers：[{name, note?, items?}]');
    need(fi >= 0 && fi < n, `layers 的 focus 须是 0–${n - 1} 的层号`);
    ls.forEach(x => need(!x.items || (Array.isArray(x.items) && x.items.length <= 4), `layers「${x.name}」最多 4 个 items`));
    const C = ST().palette, gapT = .32, gapE = 1.55, Wd = 6.4, Dp = 3;
    const yT = k => (n - 1 - k) * gapT, yE = k => (n - 1 - k) * gapE, off = k => (k - (n - 1) / 2) * -.35;
    const v = view3d(host, { ang: .5, dist: 17, yaw: .75, look: [0, n * gapT / 2, 0], wide: true }), T = v.T;
    v.extent(8);
    const slabs = [], smats = [], chips = [], chipL = [], nameL = [], noteL = [];
    ls.forEach((x, k) => {
      const col = hexMix(C.soft, C.fill[1], n > 1 ? k / (n - 1) * .7 : 0);
      const mat = pbr(T, { color: lin(T, col), roughness: .25, metalness: .02, transparent: true, opacity: .9, emissive: lin(T, C.fill[0]), emissiveIntensity: .04 });
      const sl = new T.Mesh(rbox(T, Wd, .2, Dp, .35), mat); sl.position.set(0, yT(k), 0); sl.receiveShadow = true; v.scene.add(sl); slabs.push(sl); smats.push(mat);
      const nl = v.label(x.name, { height: .52, weight: 700, color: INK().title, depthTest: false, align: 'left' }); nl.position.set(Wd / 2 + .5 + off(k), yE(k) + .42, 0); v.scene.add(nl); nameL.push(nl);
      if (x.note) { const tl2 = v.label(x.note, { height: .36, color: INK().muted, depthTest: false, align: 'left' }); tl2.position.set(Wd / 2 + .5 + off(k), yE(k) - .08, 0); v.scene.add(tl2); noteL.push(tl2); }
      (x.items || []).forEach((t, q, arr) => {
        const cw = (Wd - .8) / arr.length - .25, px = -Wd / 2 + .4 + (q + .5) * (cw + .25);
        const ch = new T.Mesh(rbox(T, cw, .18, .9, .1), pbr(T, { color: 0xffffff, roughness: .4 }));
        ch.position.set(px, .2, .2); sl.add(ch); chips.push(ch);
        const lb = v.label(t, { height: .32, weight: 600, color: INK().body, depthTest: false }); lb.position.set(px, .62, .2); sl.add(lb); chipL.push(lb);
      });
    });
    for (const l of [...nameL, ...noteL, ...chipL]) l.material.opacity = 0;
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        stack(tl, at) { tl.from(slabs.map(s => s.position), { y: '-=3', duration: D, stagger: .1, ease: ease(), ...u }, at).from(smats, { opacity: 0, duration: D * .7, stagger: .1, ...u }, at); },
        explode(tl, at) {
          slabs.forEach((s, k) => tl.fromTo(s.position, { y: yT(k), x: 0 }, { y: yE(k), x: off(k), duration: 1.2, ease: 'power3.inOut', immediateRender: false, ...u }, at + k * .06));
          tl.fromTo(mats([...nameL, ...noteL]), { opacity: 0 }, { opacity: 1, duration: .45, stagger: .08, immediateRender: true, ...u }, at + .8)
            .to(v.pose, { ang: .36, dist: 13 + n * 1.1, yaw: .42, duration: 1.4, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 0: 1.6, 1: (n - 1) * gapE / 2, duration: 1.4, ease: 'power2.inOut', ...u }, at);
        },
        fill(tl, at) {
          chips.forEach((c, q) => { const t0 = at + q * each(chips.length, .06);
            tl.fromTo(c.scale, { x: .01, y: .01, z: .01 }, { x: 1, y: 1, z: 1, duration: .25, immediateRender: true, ...u }, t0)
              .fromTo(c.position, { y: 2.4 }, { y: .2, duration: .55, ease: 'bounce.out', immediateRender: true, ...u }, t0); });
          tl.fromTo(mats(chipL), { opacity: 0 }, { opacity: 1, duration: .35, stagger: each(chipL.length, .06), immediateRender: true, ...u }, at + .45);
        },
        focus(tl, at) {
          const hot = lin(T, C.fill[1]);
          tl.to(slabs[fi].position, { y: `+=${gapE * .3}`, duration: .6, ease: back(1.6), ...u }, at)
            .to(smats[fi].color, { r: hot.r, g: hot.g, b: hot.b, duration: .5, ...u }, at).to(smats[fi], { emissiveIntensity: .25, duration: .5, ...u }, at)
            .to(smats.filter((_, k) => k !== fi), { opacity: .38, duration: .5, ...u }, at)
            .to(mats(nameL.filter((_, k) => k !== fi)), { opacity: .45, duration: .5, ...u }, at)
            .to(nameL[fi].scale, { x: nameL[fi].scale.x * 1.15, y: nameL[fi].scale.y * 1.15, duration: .45, ease: back(2), ...u }, at);
        }
      }
    };
  });

  /* ghost — change: on each item's own plinth the earlier value stands as a glass silhouette, the later value grows as
     a solid column inside it, the change is labelled and coloured by whether it is better; each item has its own scale */
  define('ghost', (host, data) => {
    const it = data.items || [], n = it.length, unit = data.unit || '';
    need(n >= 2 && n <= 5, 'ghost 需要 2–5 个 items：[{name, before, after, good: up|down}]');
    need(data.from && data.to, 'ghost 需要 from 与 to（两个时点的名称）');
    it.forEach(x => need(Number.isFinite(x.before) && Number.isFinite(x.after) && x.before >= 0 && x.after >= 0 && ['up', 'down'].includes(x.good), `ghost「${x.name}」需要非负 before/after 与 good: up|down`));
    const C = ST().palette, H = 3.6, pitch = 2.8, X = i => (i - (n - 1) / 2) * pitch;
    const dec = x => (Number.isInteger(x.decimals) ? x.decimals : Number.isInteger(data.decimals) ? data.decimals : 0);
    const better = x => (x.good === 'up' ? x.after > x.before : x.after < x.before);
    const v = view3d(host, { ang: .34, dist: Math.max(15, n * pitch * 1.2 + 6), yaw: .45, look: [0, H * .4, 0] }), T = v.T;
    v.extent(n * pitch / 2 + 3);
    const plinths = [], ghosts = [], solids = [], bL = [], aL = [], dL = [], nL = [], hs = [], arrows = [];
    it.forEach((x, i) => {
      const top = Math.max(x.before, x.after) || 1, hb = Math.max(.05, x.before / top * H), ha = Math.max(.05, x.after / top * H); hs.push([hb, ha]);
      const pl = new T.Mesh(rbox(T, 2, .2, 1.8, .3), pbr(T, { color: 0xffffff, roughness: .5, transparent: true }));
      pl.position.x = X(i); pl.castShadow = pl.receiveShadow = true; v.scene.add(pl); plinths.push(pl);
      const gg = rbox(T, 1.1, 1, 1.1, .12);
      const gh = new T.Mesh(gg, pbr(T, { color: lin(T, C.soft), roughness: .15, transparent: true, opacity: .5, depthWrite: false }));
      gh.add(new T.LineSegments(new T.EdgesGeometry(gg, 30), new T.LineBasicMaterial({ color: new T.Color(C.fill[0]), transparent: true })));
      gh.position.set(X(i), .2, 0); gh.scale.y = hb; v.scene.add(gh); ghosts.push(gh);
      const sm = pbr(T, { color: lin(T, C.fill[1]), roughness: .3, metalness: .04 });
      const so = new T.Mesh(rbox(T, .74, 1, .74, .1), sm); so.position.set(X(i), .2, 0); so.scale.y = ha; so.castShadow = true; v.scene.add(so); solids.push(so);
      const b = v.label(`${fmt(x.before, dec(x))}${unit}`, { height: .4, weight: 600, color: INK().muted, depthTest: false, align: 'left' }); b.position.set(X(i) + .66, .2 + hb, 0); v.scene.add(b); bL.push(b);
      const a = v.label(`${fmt(x.after, dec(x))}${unit}`, { height: .54, weight: 800, color: INK().title, depthTest: false }); a.position.set(X(i), .2 + Math.max(ha, hb) + .85, 0); v.scene.add(a); aL.push(a);
      const dv = x.after - x.before, sign = dv > 0 ? '+' : dv < 0 ? '−' : '±';
      const d = v.label(`${sign}${fmt(Math.abs(dv), dec(x))}${unit} ${dv > 0 ? '↑' : dv < 0 ? '↓' : ''}`.trim(), { height: .44, weight: 800, color: better(x) ? C.ok : dv ? RISK() : INK().muted, depthTest: false });
      d.position.set(X(i), .2 + Math.max(ha, hb) + 1.45, 0); v.scene.add(d); dL.push(d);
      const ar = new T.Mesh(new T.ConeGeometry(.22, .42, 24), pbr(T, { color: lin(T, better(x) ? C.ok : dv ? C.alert : C.track), roughness: .35 }));
      if (dv < 0) ar.rotation.z = Math.PI; ar.position.set(X(i) + .75, .2 + ha + (dv < 0 ? .35 : .3), 0); ar.visible = dv !== 0; v.scene.add(ar); arrows.push(ar);
      const nm = v.label(x.name, { height: .4, color: INK().body, depthTest: false }); nm.position.set(X(i), .25, 1.45); v.scene.add(nm); nL.push(nm);
    });
    const legend = v.label(`虚影 ${data.from} · 实体 ${data.to}（每项各自刻度）`, { height: .4, weight: 600, color: INK().muted, depthTest: false, align: 'left' });
    legend.position.set(0, -.75, 2); v.scene.add(legend);
    for (const l of [...bL, ...aL, ...dL, legend]) l.material.opacity = 0;
    const D = F().motion.fx.three.dur, u = v.upd();
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        before(tl, at) {
          tl.from(plinths.map(p => p.position), { y: -2, duration: D, stagger: .08, ease: ease(), ...u }, at).from(mats(plinths), { opacity: 0, duration: D * .7, ...u }, at)
            .fromTo(mats(nL), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .06, immediateRender: true, ...u }, at + .3);
          ghosts.forEach((gh, i) => tl.fromTo(gh.scale, { y: .02 }, { y: hs[i][0], duration: 1, ease: 'power3.out', immediateRender: true, ...u }, at + .3 + i * each(n, .1)));
          tl.fromTo(mats([...bL, legend]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .06, immediateRender: true, ...u }, at + .9);
        },
        // the solid columns stay flat until this scene
        after(tl, at) {
          solids.forEach((so, i) => tl.fromTo(so.scale, { y: .02 }, { y: hs[i][1], duration: 1.1, ease: 'power3.out', immediateRender: true, ...u }, at + i * each(n, .12)));
          tl.fromTo(mats(aL), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n, .12), immediateRender: true, ...u }, at + .8);
        },
        delta(tl, at) {
          arrows.forEach((ar, i) => tl.fromTo(ar.scale, { x: .01, y: .01, z: .01 }, { x: 1, y: 1, z: 1, duration: .5, ease: back(2.2), immediateRender: true, ...u }, at + i * .1));
          tl.fromTo(mats(dL), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .1, immediateRender: true, ...u }, at)
            .from(dL.map(d => d.position), { y: '-=.6', duration: .5, stagger: .1, ease: back(2), ...u }, at);
        },
        orbit(tl, at) { tl.to(v.pose, { yaw: -.2, ang: .26, duration: 1.8, ease: 'power2.inOut', ...u }, at); }
      }
    };
  });

  /* safety — safety overview (8.0 scenario family; the contract is KZClinical.safety, shared with the regular demo form and
     the static template): a glass ledger seen from above, one row per event category running toward the camera, the two
     compared arms as a 3D butterfly on either side of a glass spine. The child categories peel out of the TEAE bars and
     slide to their own rows (the same bars, re-scaled); the camera then dollies down the ledger to the focus row. */
  define('safety', (host, data) => {
    need(g.KZClinical, 'safety 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const M = g.KZClinical.safety(data), rows = M.rows, n = rows.length, C = ST().palette, A = M.arms[M.ti], B = M.arms[M.ci];
    const scale = [10, 20, 30, 40, 50, 60, 80, 100].find(s => s >= Math.max(...rows.flatMap(r => [r.pct[M.ti], r.pct[M.ci]]))) || 100;
    const W = 4.4, pitch = 1, depth = n * pitch, Z = i => -depth / 2 + pitch / 2 + i * pitch, len = p => Math.max(.02, p / scale * W);
    const top = r => r.depth === 0, nm = r => r.short || r.label, D = F().motion.fx.three.dur;
    // framed on the whole width: names (left of the treatment wing) to the difference column (right of the comparator)
    const v = view3d(host, { ang: 1.12, dist: 24 + n * .3, yaw: 0, look: [-.6, 0, .3] }), T = v.T;
    v.extent(W + 8);
    // the glass slab carries only the butterfly; names, values and differences float on the canvas beside it
    const plinth = new T.Mesh(rbox(T, 2 * W + 1.6, .2, depth + 1.2, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plinth.position.set(0, -.2, 0); plinth.receiveShadow = true; v.scene.add(plinth);
    const spine = new T.Mesh(rbox(T, .08, .5, depth + .4, .03), pbr(T, { color: lin(T, C.soft), roughness: .2, transparent: true, opacity: .85 }));
    spine.castShadow = true; v.scene.add(spine);
    const stripes = rows.map((r, i) => { if (i % 2) return null; const s = new T.Mesh(new T.BoxGeometry(2 * W + 1.2, .015, pitch * .92), pbr(T, { color: lin(T, '#F4EEE6'), roughness: .8, transparent: true }));
      s.position.set(0, .01, Z(i)); v.scene.add(s); return s; }).filter(Boolean);
    const barGeo = (h, dpt) => rbox(T, 1, h, dpt, Math.min(.08, h * .3)).translate(.5, 0, 0);
    const colT = lin(T, C.fill[1]), colC = lin(T, '#7C8796');
    const bars = rows.map((r, i) => {
      const h = top(r) ? .62 : .42, dpt = top(r) ? .6 : .42;
      const t = new T.Mesh(barGeo(h, dpt), pbr(T, { color: colT.clone(), roughness: .3, transparent: true }));
      const c = new T.Mesh(barGeo(h, dpt), pbr(T, { color: colC.clone(), roughness: .38, transparent: true }));
      t.rotation.y = Math.PI; t.position.set(-.06, .02, Z(i)); c.position.set(.06, .02, Z(i));
      t.scale.x = c.scale.x = .001; t.castShadow = c.castShadow = true; v.scene.add(t, c);
      return { t, c, lt: len(r.pct[M.ti]), lc: len(r.pct[M.ci]) };
    });
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; v.scene.add(l); return l; };
    const nameL = rows.map((r, i) => lab(nm(r), { height: top(r) ? .58 : .5, weight: top(r) ? 700 : 500, color: top(r) ? INK().title : INK().body, align: 'left' }, -W - 6.8 + .4 * r.depth, .1, Z(i)));
    const valT = rows.map((r, i) => lab(g.KZClinical.npct(r.values[M.ti], r.pct[M.ti]), { height: .5, weight: top(r) ? 700 : 500, color: INK().title, align: 'right' }, -W - 1.1, .1, Z(i)));
    const valC = rows.map((r, i) => lab(g.KZClinical.npct(r.values[M.ci], r.pct[M.ci]), { height: .5, weight: top(r) ? 700 : 500, color: INK().title, align: 'left' }, W + 1.1, .1, Z(i)));
    const difL = rows.map((r, i) => lab(g.KZClinical.dtext(r.diff), { height: .54, weight: 800, color: r.diff >= M.flag ? RISK() : INK().muted, align: 'left' }, W + 4.2, .1, Z(i)));
    const armA = lab(`${A.name}（N = ${A.n}）`, { height: .5, weight: 700, color: C.fill[2] }, -W / 2 - .3, .1, Z(0) - 1.35);
    const armB = lab(`${B.name}（N = ${B.n}）`, { height: .5, weight: 700, color: INK().body }, W / 2 + .3, .1, Z(0) - 1.35);
    const difH = lab('差值 (pp)', { height: .4, weight: 700, color: INK().muted, align: 'left' }, W + 4.2, .1, Z(0) - 1.35);
    const cas = rows.map((_, i) => i).filter(i => i > 0 && M.under(rows[i])), rest = rows.map((_, i) => i).filter(i => i > 0 && !M.under(rows[i]));
    const big = rows.map((_, i) => i).sort((a, b) => rows[b].diff - rows[a].diff)[0], fi = M.focus ? rows.findIndex(r => r.key === M.focus) : big;
    const u = v.upd(), op = list => list.map(l => l.material);
    const grow = (tl, i, at, from) => {
      const b = bars[i];
      if (from != null) {
        // peel: the child starts as a copy of the parent bar in the parent's row, then slides to its own row and length
        tl.fromTo([b.t.position, b.c.position], { z: Z(from) }, { z: Z(i), duration: 1.1, ease: ease(), immediateRender: true, ...u }, at)
          .fromTo(b.t.scale, { x: bars[from].lt }, { x: b.lt, duration: 1.1, ease: ease(), immediateRender: true, ...u }, at)
          .fromTo(b.c.scale, { x: bars[from].lc }, { x: b.lc, duration: 1.1, ease: ease(), immediateRender: true, ...u }, at);
      } else {
        tl.fromTo(b.t.scale, { x: .001 }, { x: b.lt, duration: 1, ease: 'power3.out', immediateRender: true, ...u }, at)
          .fromTo(b.c.scale, { x: .001 }, { x: b.lc, duration: 1, ease: 'power3.out', immediateRender: true, ...u }, at);
      }
      tl.fromTo(op([valT[i], valC[i]]), { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at + .6)
        .to(nameL[i].material, { opacity: 1, duration: .35, ...u }, at);
    };
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plinth.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plinth.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(spine.scale, { z: .02, duration: D, ease: ease(), ...u }, at + .2).from([...mats(stripes)], { opacity: 0, duration: .5, ...u }, at + .3)
            .fromTo(op(nameL), { opacity: 0 }, { opacity: .35, duration: .4, stagger: each(n, .05), immediateRender: true, ...u }, at + .4)
            .fromTo(op([armA, armB]), { opacity: 0 }, { opacity: 1, duration: .45, stagger: .12, immediateRender: true, ...u }, at + .5);
        },
        overall(tl, at) { grow(tl, 0, at); },
        cascade(tl, at) {
          cas.forEach((i, k) => grow(tl, i, at + k * each(cas.length, .1), 0));
          tl.to(mats([bars[0].t, bars[0].c]), { opacity: .55, duration: .4, ...u }, at);
        },
        rest(tl, at) {
          rest.forEach((i, k) => grow(tl, i, at + k * each(rest.length, .12)));
          tl.to(mats([bars[0].t, bars[0].c]), { opacity: 1, duration: .4, ...u }, at);
        },
        diff(tl, at) {
          tl.fromTo(op([difH, ...difL]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n + 1, .06), immediateRender: true, ...u }, at)
            .from(difL.map(l => l.position), { x: `-=${1.2}`, duration: .6, stagger: each(n, .06), ease: back(1.6), ...u }, at);
          rows.forEach((r, i) => { if (r.diff >= M.flag) tl.to(difL[i].scale, { x: difL[i].scale.x * 1.15, y: difL[i].scale.y * 1.15, duration: .4, ease: back(2), ...u }, at + .5); });
        },
        // the camera dollies down the ledger to the focus row; the row lifts, the others dim
        focus(tl, at) {
          const b = bars[fi], others = bars.filter((_, i) => i !== fi);
          // a small tilt toward the row only: the name column sits at the frame edge, so the camera must not dolly in
          tl.to(v.pose, { ang: 1.02, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 2: v.pose.look[2] + Z(fi) * .15, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to([b.t.position, b.c.position], { y: .38, duration: .7, ease: back(1.4), ...u }, at + .4)
            .to(mats(others.flatMap(o => [o.t, o.c])), { opacity: .45, duration: .6, ...u }, at + .3)
            .to(op([...valT, ...valC, ...nameL, ...difL].filter((_, k) => k % n !== fi)), { opacity: .4, duration: .6, ...u }, at + .3);
        }
      }
    };
  });

  /* exposure — exposure summary (8.0 scenario family; contract KZClinical.exposure, shared with the regular demo form, the
     static template and the flagship PPTX page): a glass ledger with one row per indication receding from the camera.
     Every row is a stepped ingot: the first band a long low slab, each longer band a shorter, taller, deeper-coloured
     step on top of it (a subset of the band below). The totals then rise as towers beside the ledger, one per band, each
     with a frosted target plane at its target height; the camera finally turns to the focus row. */
  define('exposure', (host, data) => {
    need(g.KZClinical, 'exposure 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const M = g.KZClinical.exposure(data), B = M.bands, G = M.groups, n = G.length, nb = B.length, C = ST().palette, D = F().motion.fx.three.dur;
    const ramp = g.KZ_TOKENS.charts.phases, col = B.map((_, i) => ramp[Math.min(ramp.length - 1, 1 + Math.round(i * (ramp.length - 2) / Math.max(1, nb - 1)))]);
    const L = 7.2, pitch = Math.min(1.5, 7.5 / n), depth = n * pitch, Z = i => -depth / 2 + pitch / 2 + i * pitch, len = v => Math.max(.02, v / M.max * L), x0 = -L / 2 - 1.2;
    const stepH = k => .22 + .2 * k, fmt = v => g.KZClinical.num(v);
    const tmax = Math.max(...M.totals, ...M.targets.filter(t => t != null)), TH = 4.2, tH = v => Math.max(.04, v / tmax * TH), tx = L / 2 + 1.4, TS = 1.7;
    // aim at the middle of names + deck + towers so neither the names nor the far plate edge touch the canvas
    const v = view3d(host, { ang: 1.06, dist: 23.5 + n * .45, yaw: -.08, look: [1.5, 0, .4] }), T = v.T;
    v.extent(L / 2 + 6);
    // the deck starts right of the name column: a label over the translucent glass is cut by it (same rule as safety)
    const px0 = x0 - .25, px1 = tx + (nb - 1) * TS + 1.5;
    const plate = new T.Mesh(rbox(T, px1 - px0, .2, depth + 1.4, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set((px0 + px1) / 2, -.2, 0); plate.receiveShadow = true; v.scene.add(plate);
    const rails = G.map((_, i) => { const r = new T.Mesh(new T.BoxGeometry(L + .4, .02, pitch * .66), pbr(T, { color: lin(T, i % 2 ? '#F4EEE6' : '#FBF7F1'), roughness: .8, transparent: true }));
      r.position.set(x0 + L / 2, .01, Z(i)); v.scene.add(r); return r; });
    const slab = (w, h, d) => rbox(T, 1, h, d, Math.min(.06, h * .3)).translate(.5, h / 2, 0);
    const steps = G.map((gr, i) => B.map((_, k) => {
      const m = new T.Mesh(slab(1, stepH(k), pitch * (.56 - .06 * k)), pbr(T, { color: lin(T, col[k]), roughness: .32, transparent: true }));
      m.position.set(x0, .02, Z(i)); m.scale.x = .001; m.castShadow = true; m.visible = gr.values[k] > 0; v.scene.add(m); return m; }));
    // labels draw after the glass (renderOrder) so a dimmed name is not cut by the translucent deck
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; l.renderOrder = 10; v.scene.add(l); return l; };
    const names = G.map((gr, i) => lab(gr.name, { height: .5, weight: 700, color: INK().title, align: 'right' }, x0 - .4, .1, Z(i)));
    const vals = G.map((gr, i) => B.map((_, k) => lab(fmt(gr.values[k]), { height: .42, weight: k === 0 ? 700 : 600, color: k === 0 ? INK().title : INK().body, align: 'left' }, x0 + len(gr.values[k]) + .25, stepH(k) + .25, Z(i) - .02 * k)));
    const towers = M.totals.map((t, k) => { const m = new T.Mesh(slab(1, 1, .9), pbr(T, { color: lin(T, col[k]), roughness: .28, transparent: true }));
      m.scale.set(.9, .001, 1); m.position.set(tx + k * TS, .02, depth / 2 - .8); m.castShadow = true; v.scene.add(m); return m; });
    const planes = M.targets.map((t, k) => { if (t == null) return null;
      const m = new T.Mesh(new T.BoxGeometry(1.15, .03, 1.15), pbr(T, { color: lin(T, M.met[k] ? '#9DBF7E' : '#E58A80'), roughness: .2, transparent: true, opacity: 0 }));
      m.position.set(tx + k * TS + .45, tH(t), depth / 2 - .8); v.scene.add(m); return m; });
    const tLab = M.totals.map((t, k) => lab(fmt(t), { height: .5, weight: 800, color: M.met[k] === false ? RISK() : INK().title }, tx + k * TS + .45, tH(t) + .45, depth / 2 - .8));
    const bLab = B.map((b, k) => lab(b.label, { height: .38, weight: 700, color: INK().muted }, tx + k * TS + .45, .1, depth / 2 + .1));
    const gLab = M.targets.map((t, k) => t == null ? null : lab(`目标 ${fmt(t)}`, { height: .34, weight: 600, color: INK().muted }, tx + k * TS + .45, tH(t) + .12, depth / 2 - .2));
    const fi = M.focus ? G.findIndex(gr => gr.key === M.focus) : 0, u = v.upd(), op = list => list.filter(Boolean).map(l => l.material);
    const grow = (tl, k, at) => G.forEach((gr, i) => { if (!gr.values[k]) return;
      tl.fromTo(steps[i][k].scale, { x: .001 }, { x: len(gr.values[k]), duration: 1, ease: 'power3.out', immediateRender: true, ...u }, at + i * each(n, .08))
        .fromTo(vals[i][k].material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .6 + i * each(n, .08)); });
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(mats(rails), { opacity: 0, duration: .5, stagger: each(n, .05), ...u }, at + .3)
            .fromTo(op(names), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n, .06), immediateRender: true, ...u }, at + .4);
        },
        any(tl, at) { grow(tl, 0, at); },
        longer(tl, at) { for (let k = 1; k < nb; k++) grow(tl, k, at + (k - 1) * .9); },
        total(tl, at) {
          towers.forEach((m, k) => tl.fromTo(m.scale, { y: .001 }, { y: tH(M.totals[k]), duration: 1.1, ease: 'power3.out', immediateRender: true, ...u }, at + k * .18));
          tl.fromTo(op([...tLab, ...bLab]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .08, immediateRender: true, ...u }, at + .7)
            .fromTo(planes.filter(Boolean).map(m => m.material), { opacity: 0 }, { opacity: .55, duration: .5, immediateRender: true, ...u }, at + 1)
            .fromTo(op(gLab), { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at + 1.1);
          M.met.forEach((ok, k) => { if (ok === false) tl.to(tLab[k].scale, { x: tLab[k].scale.x * 1.15, y: tLab[k].scale.y * 1.15, duration: .4, ease: back(2), ...u }, at + 1.3); });
        },
        focus(tl, at) {
          tl.to(v.pose, { ang: .98, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 2: v.pose.look[2] + Z(fi) * .2, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(steps[fi].map(m => m.position), { y: .3, duration: .7, ease: back(1.4), ...u }, at + .4)
            .to(mats(steps.filter((_, i) => i !== fi).flat()), { opacity: .4, duration: .6, ...u }, at + .3)
            .to(op([...names.filter((_, i) => i !== fi), ...vals.flatMap((r, i) => i === fi ? [] : r.filter((_, k) => G[i].values[k] > 0))]), { opacity: .4, duration: .6, ...u }, at + .3);
        }
      }
    };
  });

  /* landscape — competitive landscape (8.0 scenario family; contract KZClinical.landscape, shared with the regular demo form,
     the static template and the flagship PPTX page): every asset is a glass token whose height is its development stage.
     The tokens first line up by stage along the front edge, then glide onto an efficacy × safety field (better efficacy to
     the right, better safety to the front); assets without data wait in a tray on the left; the ideal corner lights up and
     the camera settles on the focus asset (ours by default). */
  define('landscape', (host, data) => {
    need(g.KZClinical, 'landscape 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const K = g.KZClinical, M = K.landscape(data), AS = M.assets, n = AS.length, S0 = M.stages, ns = S0.length, D = F().motion.fx.three.dur;
    const TREAT = g.KZ_TOKENS.charts.categorical[0], COMP = g.KZ_TOKENS.charts.comparator, ACC = F().accent_ink, ME = M.metrics;
    const L = 9, DZ = 5.6, hOf = si => .45 + si * .55, byKey = Object.fromEntries(AS.map(a => [a.key, a]));
    const ax = mk => { const vs = AS.map(a => a[mk]).filter(v => v != null); if (!vs.length) return null; const lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo || 1) * .15; return [lo - pad, hi + pad]; };
    const ex = ME.efficacy ? ax('efficacy') : null, ez = ME.safety ? ax('safety') : null;
    // efficacy along x (better to the right), safety along z (better to the front, towards the camera)
    const PX = v => { const t = (v - ex[0]) / (ex[1] - ex[0]); return -L / 2 + (ME.efficacy.better === 'higher' ? t : 1 - t) * L; };
    const PZ = v => { const t = (v - ez[0]) / (ez[1] - ez[0]); return -DZ / 2 + (ME.safety.better === 'lower' ? 1 - t : t) * DZ; };
    const onMap = a => ex && ez && a.efficacy != null && a.safety != null, tray = AS.filter(a => !onMap(a));
    const v = view3d(host, { ang: .92, dist: 21 + n * .15, yaw: -.1, origin: [-1.4, 0, 0], look: [-1.4, 0, .9] }), T = v.T;
    v.extent(L / 2 + 5);
    const plate = new T.Mesh(rbox(T, L + 6.2, .2, DZ + 3.4, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set(-1.4, -.2, .5); plate.receiveShadow = true; v.scene.add(plate);
    const field = new T.Mesh(new T.BoxGeometry(L + .6, .02, DZ + .6), pbr(T, { color: lin(T, '#FBF7F1'), roughness: .8, transparent: true }));
    field.position.set(0, .01, 0); v.scene.add(field);
    const ideal = new T.Mesh(new T.BoxGeometry(L / 2 + .3, .025, DZ / 2 + .3), pbr(T, { color: lin(T, '#FFC879'), roughness: .6, transparent: true, opacity: 0 }));
    ideal.position.set(L / 4 + .15, .02, DZ / 4 + .15); v.scene.add(ideal);
    const grid = []; for (let k = 1; k < 4; k++) { const gx = new T.Mesh(new T.BoxGeometry(.02, .03, DZ + .6), pbr(T, { color: lin(T, '#E3DACD'), roughness: .6, transparent: true }));
      gx.position.set(-L / 2 - .3 + k * (L + .6) / 4, .03, 0); v.scene.add(gx); grid.push(gx);
      const gz = new T.Mesh(new T.BoxGeometry(L + .6, .03, .02), pbr(T, { color: lin(T, '#E3DACD'), roughness: .6, transparent: true }));
      gz.position.set(0, .03, -DZ / 2 - .3 + k * (DZ + .6) / 4); v.scene.add(gz); grid.push(gz); }
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; l.renderOrder = 10; v.scene.add(l); return l; };
    const axL = [ME.efficacy && lab(`${ME.efficacy.label} ${ME.efficacy.better === 'higher' ? '越高越好' : '越低越好'} →`, { height: .46, weight: 700, color: INK().muted, align: 'left' }, -L / 2 - .3, .1, DZ / 2 + .75),
      ME.safety && lab(`↓ ${ME.safety.label} ${ME.safety.better === 'lower' ? '越低越好' : '越高越好'}`, { height: .42, weight: 700, color: INK().muted, align: 'left' }, L / 2 + .7, .1, -DZ / 2 + .2)].filter(Boolean);
    const idealL = lab('理想区：疗效更好、耐受更好', { height: .46, weight: 800, color: ACC, align: 'right' }, L / 2 + .3, .1, DZ / 2 + .75);
    const trayL = tray.length ? lab('暂无数据', { height: .44, weight: 700, color: INK().muted }, -L / 2 - 2.1, .1, -DZ / 2 + .9 + tray.length * 1.4 - .3) : null;
    // stage line-up along the front edge (stage order = M.order), then the map positions
    const lineX = r => -L / 2 + .6 + r * ((L - 1.2) / Math.max(1, n - 1)), order = M.order;
    const toks = AS.map(a => {
      const h = hOf(a.si), m = new T.Mesh(new T.CylinderGeometry(.55, .55, 1, 40).translate(0, .5, 0), pbr(T, { color: lin(T, a.ours ? TREAT : COMP), roughness: .3, transparent: true }));
      const r = order.indexOf(a.key), ti = tray.indexOf(a); m.scale.y = .001; m.castShadow = true;
      const P0 = [lineX(r), DZ / 2 + 2.2], P1 = onMap(a) ? [PX(a.efficacy), PZ(a.safety)] : [-L / 2 - 2.1, -DZ / 2 + .9 + ti * 1.4];
      m.position.set(P0[0], .02, P0[1]); v.scene.add(m);
      const nl = lab(a.name, { height: .56, weight: a.ours ? 800 : 700, color: a.ours ? ACC : INK().title }, P0[0], h + .5, P0[1]);
      const sl = lab(a.stage, { height: .4, weight: 600, color: INK().muted }, P0[0], h + .12, P0[1] + .5);
      // on the map one label per token: name · efficacy / safety (height already says the stage); a label is a texture, so swap it
      const vl = onMap(a) ? lab(`${a.name}  ${a.efficacy} / ${a.safety}`, { height: .46, weight: a.ours ? 800 : 700, color: a.ours ? ACC : INK().title }, P1[0], h + .45, P1[1]) : null;
      return { a, m, h, P0, P1, nl, sl, vl, lv: 0 };
    });
    // neighbours on the map stack their labels in levels instead of overlapping
    toks.slice().sort((p, q) => p.P1[0] - q.P1[0]).forEach((t, k, arr) => { while (arr.slice(0, k).some(o => o.vl && o.lv === t.lv && Math.abs(o.P1[0] - t.P1[0]) < 3.2 && Math.abs(o.P1[1] - t.P1[1]) < 1.8)) t.lv++;
      if (t.vl) t.vl.position.y += t.lv * .8; });
    const u = v.upd(), op = list => list.filter(Boolean).map(l => l.material), fa = byKey[M.focus] || AS[0], ft = toks.find(t => t.a === fa);
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(field.scale, { x: .01, duration: .9, ease: 'power3.out', ...u }, at + .2).from(mats(grid), { opacity: 0, duration: .5, ...u }, at + .4);
        },
        stage(tl, at) {
          toks.forEach((t, k) => tl.fromTo(t.m.scale, { y: .001 }, { y: t.h, duration: .8, ease: back(1.2), immediateRender: true, ...u }, at + order.indexOf(t.a.key) * each(n, .1)));
          tl.fromTo(op(toks.flatMap(t => [t.nl, t.sl])), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n * 2, .04), immediateRender: true, ...u }, at + .5);
        },
        map(tl, at) {
          toks.forEach((t, k) => { const go = { x: t.P1[0], z: t.P1[1], duration: 1.3, ease: 'power2.inOut', ...u };
            tl.to(t.m.position, go, at + k * .08).to(t.nl.position, go, at + k * .08).to(t.sl.position, { ...go, z: t.P1[1] + .5 }, at + k * .08); });
          tl.to(op(toks.filter(t => t.vl).flatMap(t => [t.sl, t.nl])), { opacity: 0, duration: .3, ...u }, at + 1)
            .fromTo(op([...axL, trayL, ...toks.map(t => t.vl)]), { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at + 1.2);
        },
        ideal(tl, at) {
          tl.fromTo(ideal.material, { opacity: 0 }, { opacity: .85, duration: .6, immediateRender: true, ...u }, at).fromTo(idealL.material, { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at + .3);
        },
        focus(tl, at) {
          tl.to(v.pose, { ang: .85, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 0: v.pose.look[0] + ft.P1[0] * .25, 2: v.pose.look[2] + ft.P1[1] * .25, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(mats(toks.filter(t => t !== ft).map(t => t.m)), { opacity: .45, duration: .6, ...u }, at + .3)
            .to(op(toks.filter(t => t !== ft).flatMap(t => t.vl ? [t.vl] : [t.nl, t.sl])), { opacity: .6, duration: .6, ...u }, at + .3)
            .to(ft.m.scale, { x: 1.25, z: 1.25, duration: .6, ease: back(2), ...u }, at + .5);
        }
      }
    };
  });

  /* trialflow — trial flow with subflows (8.0 scenario family; contract KZClinical.trialflow, shared with the regular demo form,
     the static template and the flagship PPTX page): a glass deck with one rail per treatment branch, weeks running left to
     right on the piecewise scale. The shared periods rise as wide slabs across every rail; the randomisation puck drops at
     W0 and glass rods fan out to the arms; each arm's segments grow along its rail (titration lower and lighter, maintenance
     higher and deeper, placebo graphite); a re-randomised arm gets its own puck and rods to its sub-arms; endpoint pins drop
     on the front edge with the follow-up slab; sub-studies run as a ribbon along the front; the camera turns to the focus arm. */
  define('trialflow', (host, data) => {
    need(g.KZClinical, 'trialflow 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const K = g.KZClinical, M = K.trialflow(data), A = M.arms, Lf = M.leaves, nl = Lf.length, D = F().motion.fx.three.dur, ACC = F().accent_ink;
    const FL = g.KZ_TOKENS.charts.flow, Lx = 15, X = K.flowScale(M, -Lx / 2, Lx / 2, 1.5), pitch = Math.min(1.9, 6.6 / nl), depth = nl * pitch;
    const Z = r => -depth / 2 + pitch / 2 + r * pitch, wk = t => `W${t < 0 ? '−' : ''}${Math.abs(t)}`;
    const az = Object.fromEntries(A.map(a => [a.key, (Z(a.rows[0]) + Z(a.rows[a.rows.length - 1])) / 2]));
    const HK = { off: .14, titrate: .32, maintain: .52, placebo: .3, open: .46 };
    // a wide stage framed on the deck plus the name columns (left of the deck)
    const v = view3d(host, { ang: .9, dist: (Lx / 2 + 3) * 2.0 + nl * .3, yaw: 0, origin: [-2.6, 0, 0], look: [-2.6, 0, .8] }), T = v.T;
    v.extent(Lx / 2 + 4);
    const plate = new T.Mesh(rbox(T, Lx + 1.4, .2, depth + 2.6, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set(0, -.2, .6); plate.receiveShadow = true; v.scene.add(plate);
    const rails = Lf.map((l, r) => { const m = new T.Mesh(new T.BoxGeometry(Lx + .4, .02, pitch * .6), pbr(T, { color: lin(T, r % 2 ? '#F4EEE6' : '#FBF7F1'), roughness: .8, transparent: true }));
      m.position.set(0, .01, Z(r)); m.receiveShadow = true; v.scene.add(m); return m; });
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; l.renderOrder = 10; v.scene.add(l); return l; };
    const ticks = M.ticks.map(t => lab(wk(t), { height: .42, weight: 600, color: INK().muted }, X(t), .1, depth / 2 + 1.75));
    // a segment block: grows from its left end (scale.x), height by kind; shared periods are slabs across every rail
    const block = (gg, z, d, lz = z) => { const h = HK[gg.kind || 'maintain'], x0 = X(gg.from) + .04, len = X(gg.to) - X(gg.from) - .08;
      const m = new T.Mesh(rbox(T, 1, h, d, Math.min(.1, h * .3)).translate(.5, h / 2, 0), pbr(T, { color: lin(T, FL[gg.kind || 'maintain']), roughness: .34, transparent: true }));
      m.position.set(x0, .02, z); m.scale.x = .001; m.castShadow = true; m.receiveShadow = true; m.userData.len = len; v.scene.add(m);
      const l = lab(gg.label || '', { height: .4, weight: 700, color: INK().title }, x0 + len / 2, h + .32, lz); return { m, l, len, x0 }; };
    // trunk labels sit at the front end of the slab, clear of the randomisation puck in the middle
    const slabD = depth - pitch * .3, trunk = M.trunk.map(gg => block(gg, 0, slabD, slabD / 2 - .45)), after = M.after.map(gg => block(gg, 0, slabD));
    // randomisation pucks and the glass rods that fan out from them
    const puck = (x, z, label) => { const grp = new T.Group(), m = new T.Mesh(new T.CylinderGeometry(.42, .42, .22, 40), pbr(T, { color: 0xffffff, roughness: .25, transparent: true, emissive: lin(T, ACC), emissiveIntensity: .08 }));
      const ring = new T.Mesh(new T.TorusGeometry(.42, .05, 12, 48).rotateX(Math.PI / 2), pbr(T, { color: lin(T, ACC), roughness: .3, transparent: true }));
      ring.position.y = .11; grp.add(m, ring); grp.position.set(x, .9, z); grp.scale.setScalar(.001); m.castShadow = true; v.scene.add(grp);
      // the ratio floats well above the puck: at puck height it collides with the slab and segment labels
      const r = lab('R', { height: .5, weight: 800, color: ACC }, x, 1.3, z), l = lab(label, { height: .46, weight: 700, color: INK().title }, x, 2.55, z); return { grp, r, l }; };
    const rod = (x, z0, z1) => { const m = new T.Mesh(new T.BoxGeometry(.06, .06, 1), pbr(T, { color: lin(T, '#B9BFC7'), roughness: .3, transparent: true }));
      m.position.set(x, .9, (z0 + z1) / 2); m.scale.z = .001; m.userData.len = Math.abs(z1 - z0) || .001; v.scene.add(m); return m; };
    const ratio = (lb, r) => (lb || '随机化') + (r ? ` ${r.join(':')}` : '');
    const P0 = puck(X(M.at), 0, ratio(M.split.label, M.ratio)), zs = Object.values(az), rods0 = [rod(X(M.at), Math.min(...zs, 0), Math.max(...zs, 0))];
    const nameX = -Lx / 2 - .8, subX = nameX, armX = A.some(a => a.sub) ? nameX - 2.7 : nameX;
    const armL = A.map(a => lab(a.name + (a.n != null ? `  n=${K.num(a.n)}` : ''), { height: .56, weight: 700, color: INK().title, align: 'right' }, armX, .2, az[a.key]));
    const armB = A.map(a => a.segs.map(gg => block(gg, az[a.key], pitch * .5)));
    const subs = A.map(a => { if (!a.sub) return null; const kids = Lf.filter(l => l.parent === a.key), ys = kids.map(l => Z(l.row));
      return { p: puck(X(a.sub.at), az[a.key], ratio(a.sub.label, a.sub.ratio)), rods: [rod(X(a.sub.at), Math.min(...ys), Math.max(...ys))],
        names: kids.map(l => lab(l.name + (l.n != null ? `  n=${K.num(l.n)}` : ''), { height: .5, weight: 600, color: INK().body, align: 'right' }, subX, .2, Z(l.row))),
        blocks: kids.map(l => l.segs.map(gg => block(gg, Z(l.row), pitch * .5))).flat() }; });
    // endpoints: pins at the front edge with a frosted plane through the deck for the primary one
    const pins = M.endpoints.map(p => { const x = X(p.at), grp = new T.Group();
      const post = new T.Mesh(new T.CylinderGeometry(.025, .025, 1.6, 8).translate(0, .8, 0), pbr(T, { color: lin(T, '#8C8378'), roughness: .5, transparent: true }));
      const hd = new T.Mesh(new T.OctahedronGeometry(.3), pbr(T, { color: lin(T, p.primary ? ACC : '#FFFFFF'), roughness: .3, transparent: true, emissive: lin(T, p.primary ? ACC : '#C9CED4'), emissiveIntensity: .15 }));
      hd.position.y = 1.9; hd.castShadow = true; grp.add(post, hd); grp.position.set(x, 4, depth / 2 + .7); v.scene.add(grp);
      const pl = p.primary ? new T.Mesh(rbox(T, .05, .9, depth + .4, .02), pbr(T, { color: 0xffffff, roughness: .15, transparent: true, opacity: 0 })) : null;
      if (pl) { pl.position.set(x, .45, 0); v.scene.add(pl); }
      return { grp, pl, l: lab(p.label, { height: .48, weight: p.primary ? 800 : 600, color: p.primary ? ACC : INK().body }, x, 2.65, depth / 2 + .7) }; });
    const names = Object.fromEntries([...A, ...Lf].map(x => [x.key, x.name]));
    const ribbons = M.subs.map((x, k) => { const len = X(x.to) - X(x.from) - .1, z = depth / 2 + 1.0 + k * .55;
      const m = new T.Mesh(rbox(T, 1, .06, .34, .03).translate(.5, 0, 0), pbr(T, { color: lin(T, '#FFFFFF'), roughness: .3, transparent: true, emissive: lin(T, ACC), emissiveIntensity: .12 }));
      m.position.set(X(x.from) + .05, .04, z); m.scale.x = .001; v.scene.add(m);
      return { m, len, l: lab(`${x.name}${x.n != null ? ` n=${K.num(x.n)}` : ''} · ${x.of.map(q => names[q]).join('、')}`, { height: .38, weight: 700, color: ACC, align: 'left' }, X(x.from) + .2, .3, z) }; });
    const u = v.upd(), op = list => list.filter(Boolean).map(l => l.material);
    const grow = (tl, list, at, gap = .12) => list.forEach((b, k) => tl.fromTo(b.m.scale, { x: .001 }, { x: b.len, duration: .9, ease: 'power3.out', immediateRender: true, ...u }, at + k * gap)
      .fromTo(b.l.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .5 + k * gap));
    const pop = (tl, P, at) => tl.fromTo(P.grp.scale, { x: .001, y: .001, z: .001 }, { x: 1, y: 1, z: 1, duration: .6, ease: back(1.8), immediateRender: true, ...u }, at)
      .fromTo(op([P.r, P.l]), { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .3);
    const fan = (tl, rods, at) => rods.forEach(m => tl.fromTo(m.scale, { z: .001 }, { z: m.userData.len, duration: .6, ease: 'power2.out', immediateRender: true, ...u }, at));
    const fa = A.find(a => a.key === M.focus) || A[0];
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(rails.map(r => r.scale), { x: .01, duration: .9, stagger: each(nl, .08), ease: 'power3.out', ...u }, at + .2)
            .fromTo(op(ticks), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(ticks.length, .05), immediateRender: true, ...u }, at + .4);
        },
        shared(tl, at) { grow(tl, trunk, at, .3); },
        random(tl, at) { pop(tl, P0, at); fan(tl, rods0, at + .4); tl.fromTo(op(armL), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .1, immediateRender: true, ...u }, at + .6); },
        arms(tl, at) { armB.forEach((list, k) => grow(tl, list, at + k * .25, .5)); },
        sub(tl, at) { subs.filter(Boolean).forEach(S => { pop(tl, S.p, at); fan(tl, S.rods, at + .4);
          tl.fromTo(op(S.names), { opacity: 0 }, { opacity: 1, duration: .4, stagger: .1, immediateRender: true, ...u }, at + .5); grow(tl, S.blocks, at + .7, .2); }); },
        end(tl, at) {
          pins.forEach((P, k) => { tl.to(P.grp.position, { y: 0, duration: .8, ease: 'bounce.out', ...u }, at + k * .2).fromTo(P.l.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .6 + k * .2);
            if (P.pl) tl.fromTo(P.pl.material, { opacity: 0 }, { opacity: .35, duration: .5, immediateRender: true, ...u }, at + .5); });
          grow(tl, after, at + .5); ribbons.forEach((R0, k) => grow(tl, [R0], at + .9 + k * .2));
        },
        focus(tl, at) {
          const keep = new Set(fa.sub ? [fa.key, ...Lf.filter(l => l.parent === fa.key).map(l => l.key)] : [fa.key]);
          const dimB = [...A.flatMap((a, k) => keep.has(a.key) ? [] : armB[k])];
          tl.to(v.pose, { ang: .8, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 2: v.pose.look[2] + az[fa.key] * .3, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(mats(dimB.map(b => b.m)), { opacity: .35, duration: .6, ...u }, at + .3)
            .to(op([...dimB.map(b => b.l), ...armL.filter((_, k) => !keep.has(A[k].key))]), { opacity: .4, duration: .6, ...u }, at + .3)
            .to(armB[A.indexOf(fa)].map(b => b.m.position), { y: .25, duration: .7, ease: back(1.4), ...u }, at + .4);
        }
      }
    };
  });

  /* efficacy — efficacy summary (8.0 scenario family; contract KZClinical.efficacy, shared with the regular demo form, the
     static template and the flagship PPTX page): a glass deck with one rail per endpoint, one section per axis (mean
     difference, rate difference, ratios on a log scale), back to front. Every effect is turned so that benefit points right: a glass zero wall stands in each section, each
     treat arm's difference grows from it as a bar (treat colour when the 95% CI excludes 0 the good way, red the wrong way,
     frosted glass when it crosses 0) with the CI as a thin rail above; the endpoints whose CI crosses 0 are lifted out; the
     camera then turns to the focus endpoint. */
  define('efficacy', (host, data) => {
    need(g.KZClinical, 'efficacy 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const K = g.KZClinical, M = K.efficacy(data), A = M.arms, R = M.rows, n = R.length, TY = M.axes, D = F().motion.fx.three.dur;
    const TREAT = g.KZ_TOKENS.charts.categorical[0], NS = '#C9CED3', ACC = F().accent_ink, nt = M.treat.length;
    const tc = Object.fromEntries(M.treat.map((i, q) => [i, nt > 1 ? hexMix(TREAT, '#ffffff', .38 * (1 - q / (nt - 1))) : TREAT]));
    const Lr = 6.4, Ll = 2.6, XZ = -1.2, gap = .9, pitch = Math.min(1.5, 8.4 / (n + (TY.length - 1) * gap));
    const f = (v, dp) => fmt(v, dp).replace('-', '−'), ben = (r, v) => { const e = r.axis === 'ratio' ? Math.log(v) : v; return r.better === 'lower' ? -e : e; };
    // z per row: sections back to front with a gap; one scale per type so the larger benefit reaches Lr and harm stays within Ll
    let z0 = 0; const RZ = {}, SZ = {};
    TY.forEach((t, k) => { const rs = R.filter(r => r.axis === t); SZ[t] = [z0, z0 + rs.length * pitch]; rs.forEach((r, i) => { RZ[r.key] = z0 + (i + .5) * pitch; }); z0 += rs.length * pitch + gap * pitch; });
    const depth = z0 - gap * pitch, Z = z => z - depth / 2;
    const SC = Object.fromEntries(TY.map(t => { const bs = R.filter(r => r.axis === t).flatMap(r => Object.values(r.cmp).flatMap(c => c.ci.map(b => ben(r, b))));
      const hi = Math.max(.001, ...bs), lo = Math.min(0, ...bs); return [t, Math.min(Lr / hi, lo < 0 ? Ll / -lo : Infinity)]; }));
    const v = view3d(host, { ang: 1.02, dist: 21 + n * .4, yaw: -.06, origin: [.4, 0, 1.2], look: [.4, 0, 1.2] }), T = v.T;
    v.extent(Lr + 5);
    const plate = new T.Mesh(rbox(T, Lr + Ll + 11, .2, depth + 1.8, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set(XZ + (Lr - Ll) / 2, -.2, .3); plate.receiveShadow = true; v.scene.add(plate);
    const rails = R.map((r, k) => { const m = new T.Mesh(new T.BoxGeometry(Lr + Ll + .6, .02, pitch * .78), pbr(T, { color: lin(T, k % 2 ? '#F4EEE6' : '#FBF7F1'), roughness: .8, transparent: true }));
      m.position.set(XZ + (Lr - Ll) / 2, .01, Z(RZ[r.key])); m.receiveShadow = true; v.scene.add(m); return m; });
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; l.renderOrder = 10; v.scene.add(l); return l; };
    const names = R.map(r => lab(r.label, { height: .52, weight: r.key === M.focus ? 800 : 700, color: r.key === M.focus ? ACC : INK().title, align: 'right' }, XZ - Ll - .5, .12, Z(RZ[r.key])));
    const walls = TY.map(t => { const [a, b] = SZ[t], m = new T.Mesh(new T.BoxGeometry(.07, 1.0, b - a + pitch * .2), pbr(T, { color: lin(T, ACC), roughness: .3, transparent: true, opacity: .55 }));
      m.geometry.translate(0, .5, 0); m.position.set(XZ, .02, Z((a + b) / 2)); m.scale.y = .001; v.scene.add(m); return m; });
    const heads = TY.map(t => lab(`${{ md: '均值差', rd: '率差（百分点）', ratio: '比值（对数）' }[t]} · 有利方向 →`, { height: .44, weight: 800, color: ACC, align: 'left' }, XZ + .2, 1.25, Z(SZ[t][0]) + .1));
    // per comparison: a bar from the wall to the benefit, the CI rail above it; per row one value label in the right column
    const bars = [], rowB = {};
    R.forEach(r => {
      const ks = Object.keys(r.cmp), dz = pitch * .26; rowB[r.key] = [];
      ks.forEach((key, j) => {
        const c = r.cmp[key], i = A.findIndex(a => a.key === key), z = Z(RZ[r.key]) + (j - (ks.length - 1) / 2) * dz, s = SC[r.axis];
        const b0 = ben(r, c.diff) * s, lo = Math.min(ben(r, c.ci[0]), ben(r, c.ci[1])) * s, hi = Math.max(ben(r, c.ci[0]), ben(r, c.ci[1])) * s;
        const col = c.verdict === 'worse' ? RISK() : c.verdict === 'better' ? tc[i] : NS, h = .34;
        const m = new T.Mesh(rbox(T, 1, h, dz * .8, .05).translate(.5, h / 2, 0), pbr(T, { color: lin(T, col), roughness: c.verdict === 'ns' ? .15 : .32, transparent: true, opacity: c.verdict === 'ns' ? .7 : 1 }));
        m.position.set(XZ, .02, z); m.scale.x = .001 * Math.sign(b0 || 1); m.castShadow = true; v.scene.add(m);
        const ci = new T.Mesh(new T.BoxGeometry(1, .05, .07).translate(.5, 0, 0), pbr(T, { color: lin(T, c.verdict === 'ns' ? '#8A9098' : INK().title), roughness: .4, transparent: true, opacity: 0 }));
        ci.position.set(XZ + lo, h + .14, z); ci.scale.x = Math.max(.02, hi - lo); v.scene.add(ci);
        const o = { m, ci, len: b0 || .001, r, c }; bars.push(o); rowB[r.key].push(o);
      });
    });
    const unit = r => (r.axis === 'rd' ? ' 个百分点' : r.axis === 'md' && r.unit ? ` ${r.unit}` : '');
    const vals = R.map(r => lab((r.measure ? r.measure + ' ' : '') + Object.values(r.cmp).map(c => f(c.diff, r.dp)).join(' / ') + unit(r), { height: .48, weight: r.key === M.focus ? 800 : 700,
      color: r.key === M.focus ? ACC : Object.values(r.cmp).some(c => c.verdict !== 'better') ? INK().muted : INK().title, align: 'left' }, XZ + Lr + .5, .12, Z(RZ[r.key])));
    const legend = lab(`差值：${M.treat.map(i => A[i].name).join(' / ')}，对${A[M.comp].name}`, { height: .42, weight: 700, color: INK().muted, align: 'left' }, XZ + Lr + .5, .12, Z(0) - .5);
    const u = v.upd(), op = list => list.filter(Boolean).map(l => l.material);
    const growRows = (tl, rs, at) => rs.forEach((r, k) => {
      const t0 = at + k * each(rs.length, .18);
      rowB[r.key].forEach((o, j) => tl.fromTo(o.m.scale, { x: .001 * Math.sign(o.len) }, { x: o.len, duration: .9, ease: 'power3.out', immediateRender: true, ...u }, t0 + j * .12)
        .fromTo(o.ci.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, t0 + .6));
      tl.fromTo(vals[R.indexOf(r)].material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, t0 + .7);
    });
    const sec = (t, tl, at) => { const k = TY.indexOf(t); if (k < 0) return;
      tl.fromTo(walls[k].scale, { y: .001 }, { y: 1, duration: .6, ease: back(1.4), immediateRender: true, ...u }, at).fromTo(heads[k].material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .2);
      growRows(tl, R.filter(r => r.axis === t), at + .4); };
    const off = R.filter(r => Object.values(r.cmp).some(c => c.verdict !== 'better')), fr = R.find(r => r.key === M.focus) || R[0];
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(rails.map(r => r.scale), { x: .01, duration: .9, stagger: each(n, .06), ease: 'power3.out', ...u }, at + .2)
            .fromTo(op([...names, legend]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(n + 1, .05), immediateRender: true, ...u }, at + .4);
        },
        effects(tl, at) { TY.forEach((t, k) => sec(t, tl, at + k * 1.4)); },
        ns(tl, at) {
          if (!off.length) return;
          const keep = new Set(off.map(r => r.key)), dim = bars.filter(o => !keep.has(o.r.key));
          tl.to(mats(dim.map(o => o.m)), { opacity: .6, duration: .5, ...u }, at).to(mats(dim.map(o => o.ci)), { opacity: .4, duration: .5, ...u }, at)
            .to(op(R.flatMap((r, k) => keep.has(r.key) ? [] : [names[k], vals[k]])), { opacity: .7, duration: .5, ...u }, at)
            .to(bars.filter(o => keep.has(o.r.key)).map(o => o.m.position), { y: .3, duration: .6, ease: back(1.6), ...u }, at + .2);
        },
        focus(tl, at) {
          const fz = Z(RZ[fr.key]), mine = rowB[fr.key], rest = bars.filter(o => o.r !== fr), fi = R.indexOf(fr);
          tl.to(v.pose, { ang: .95, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 2: v.pose.look[2] + fz * .3, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(bars.map(o => o.m.position), { y: .02, duration: .5, ...u }, at)
            .to(mats(rest.map(o => o.m)), { opacity: .7, duration: .6, ...u }, at + .3).to(mats(rest.map(o => o.ci)), { opacity: .6, duration: .6, ...u }, at + .3)
            .to(op(R.flatMap((r, k) => k === fi ? [] : [names[k], vals[k]])), { opacity: .8, duration: .6, ...u }, at + .3)
            .to(op([names[fi], vals[fi]]), { opacity: 1, duration: .4, ...u }, at + .3)
            .to(mats(mine.map(o => o.m)), { opacity: 1, duration: .4, ...u }, at + .3).to(mats(mine.map(o => o.ci)), { opacity: 1, duration: .4, ...u }, at + .3)
            .to(mine.map(o => o.m.scale), { y: 1.6, duration: .6, ease: back(2), ...u }, at + .5);
        }
      }
    };
  });

  /* soa — schedule of assessments (8.0 scenario family; contract KZClinical.soa, shared with the regular demo form, the
     static item table and the flagship PPTX page): a glass deck with one column per visit (left to right) and one rail per
     section (back to front). Period slabs slide in under their visits; the treatment periods (study drug, background,
     rescue…) run as flat strips along the front edge from their first to their last visit, the primary-endpoint visit
     rises as a tinted glass column through every rail and the other key events are named at the front; each section's
     assessments stack up as coins at every visit (one coin per item); pins mark the focus item's visits and the camera
     turns to it (round 9: no per-visit load). */
  define('soa', (host, data) => {
    need(g.KZClinical, 'soa 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const K = g.KZClinical, M = K.soa(data), V = M.visits, nv = V.length, SC = M.sections, ns = SC.length, D = F().motion.fx.three.dur;
    const CAT = g.KZ_TOKENS.charts.categorical, PH = g.KZ_TOKENS.charts.phases, ACC = F().accent_ink;
    const Lx = 15, cw = Lx / nv, X = i => -Lx / 2 + cw * (i + .5), pz = Math.min(1.5, 6 / ns), Z = si => -(ns - 1) * pz / 2 + si * pz, front = Z(ns - 1) + pz * .5 + 1.1;
    const coin = .13, r0 = Math.min(.42, cw * .36);
    const v = view3d(host, { ang: 1.0, dist: 23 + ns * .4, yaw: -.05, origin: [-1.2, 0, 2], look: [-1.2, 0, 1.6] }), T = v.T;
    v.extent(Lx / 2 + 4);
    const nb = M.bands.length, bz = k => front - .2 + k * .6, zb = Z(0) - pz * .5 - 1.5, zf = bz(nb) + 1.2;
    const plate = new T.Mesh(rbox(T, Lx + 1.2, .2, zf - zb, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set(0, -.2, (zb + zf) / 2); plate.receiveShadow = true; v.scene.add(plate);
    const rails = SC.map((q, si) => { const m = new T.Mesh(new T.BoxGeometry(Lx + .4, .02, pz * .7), pbr(T, { color: lin(T, si % 2 ? '#F4EEE6' : '#FBF7F1'), roughness: .8, transparent: true }));
      m.position.set(0, .01, Z(si)); m.receiveShadow = true; v.scene.add(m); return m; });
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; l.renderOrder = 10; v.scene.add(l); return l; };
    const backZ = Z(0) - pz * .5 - .35;
    const vl = V.map((x, i) => lab(x.v, { height: .4, weight: 700, color: INK().title }, X(i), .1, backZ - .45));
    const wl = V.map((x, i) => lab(x.week || '', { height: .34, weight: 600, color: INK().muted }, X(i), .1, backZ));
    // period slabs: one low slab per named period under its visits, coloured along the phase ramp
    const named = M.periods.filter(p => p.name);
    const slabs = named.map((p, k) => { const w = (p.to - p.from) * cw - .12, col = PH[Math.min(PH.length - 1, Math.round(k * (PH.length - 1) / Math.max(1, named.length - 1)))];
      const m = new T.Mesh(rbox(T, w, .08, .5, .04), pbr(T, { color: lin(T, col), roughness: .4, transparent: true }));
      m.position.set(X(p.from) - cw / 2 + .06 + w / 2, .04, backZ - 1.05); m.scale.x = .001; v.scene.add(m);
      return { m, l: lab(p.name, { height: .4, weight: 800, color: ACC }, X(p.from) - cw / 2 + (p.to - p.from) * cw / 2, .3, backZ - 1.55) }; });
    const names = SC.map((q, si) => lab(`${q.name || '其他'} · ${q.items.length} 项`, { height: .44, weight: 700, color: INK().title, align: 'right' }, -Lx / 2 - .7, .12, Z(si)));
    // coins: one per item at each visit, stacked; the whole stack grows with scale.y
    const stacks = SC.map((q, si) => q.counts.map((n, i) => { if (!n) return null; const grp = new T.Group(), col = lin(T, CAT[si % CAT.length]);
      for (let c = 0; c < n; c++) { const m = new T.Mesh(new T.CylinderGeometry(r0, r0, coin * .82, 32), pbr(T, { color: col, roughness: .3, transparent: true }));
        m.position.y = coin * (c + .5); m.castShadow = true; grp.add(m); }
      grp.position.set(X(i), .02, Z(si)); grp.scale.y = .001; v.scene.add(grp); return grp; }));
    // treatment periods: flat strips along the front edge, one per period, from its first to its last visit
    const BC = { drug: CAT[0], background: '#AEB6BF', rescue: '#F2C38A', washout: '#D5DADF', other: '#D5DADF' };
    const strips = M.bands.map((b, k) => { const w = (b.to - b.from + 1) * cw - .14;
      const m = new T.Mesh(rbox(T, w, .1, .34, .05), pbr(T, { color: lin(T, BC[b.kind]), roughness: .45, transparent: true }));
      m.position.set(X(b.from) - cw / 2 + .07 + w / 2, .05, bz(k)); m.scale.x = .001; v.scene.add(m);
      return { m, l: lab(b.label, { height: .42, weight: 700, color: INK().title, align: 'right' }, -Lx / 2 - .7, .12, bz(k)) }; });
    // the primary-endpoint visit: a tinted glass column through every rail; the other key events named at the front
    const pcols = M.primary.map(i => { const d_ = Z(ns - 1) + pz * .5 - (backZ - .2);   // over the section rails only, never across the strips
      const m = new T.Mesh(new T.BoxGeometry(cw * .82, .9, d_).translate(0, .45, 0), pbr(T, { color: lin(T, ACC), roughness: .2, transparent: true, opacity: .12 }));
      m.position.set(X(i), .02, backZ - .2 + d_ / 2); m.scale.y = .001; v.scene.add(m);
      return { m, l: lab('主要终点', { height: .46, weight: 800, color: ACC }, X(i), 1.55, backZ - .2) }; });
    const evl = M.events.filter(e => e.kind !== 'primary').map(e => lab(e.label, { height: .36, weight: 600, color: INK().muted }, X(e.i), .1, bz(nb) + .25));
    const fi = M.items.find(x => x.item === M.focus) || M.items[0], fz = Z(fi.section);
    const pins = fi.marks.map(i => { const top = coin * SC[fi.section].counts[i] + .25, grp = new T.Group();
      const m = new T.Mesh(new T.OctahedronGeometry(.2), pbr(T, { color: lin(T, ACC), roughness: .25, transparent: true, emissive: lin(T, ACC), emissiveIntensity: .15 }));
      grp.add(m); grp.position.set(X(i), top + 1.4, fz); grp.scale.setScalar(.001); v.scene.add(grp); return { grp, top }; });
    const focusL = lab(`重点：${fi.item} · ${fi.count} 次`, { height: .5, weight: 800, color: ACC }, 0, 1.9, fz);
    const u = v.upd(), op = list => list.filter(Boolean).map(l => l.material);
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        set(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(rails.map(r => r.scale), { x: .01, duration: .9, stagger: each(ns, .08), ease: 'power3.out', ...u }, at + .2)
            .fromTo(op([...vl, ...wl]), { opacity: 0 }, { opacity: 1, duration: .4, stagger: each(nv * 2, .03), immediateRender: true, ...u }, at + .4);
        },
        periods(tl, at) {
          slabs.forEach((s, k) => tl.fromTo(s.m.scale, { x: .001 }, { x: 1, duration: .7, ease: 'power3.out', immediateRender: true, ...u }, at + k * .15)
            .fromTo(s.l.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .3 + k * .15));
        },
        treatment(tl, at) {
          strips.forEach((s_, k) => tl.fromTo(s_.m.scale, { x: .001 }, { x: 1, duration: .8, ease: 'power3.out', immediateRender: true, ...u }, at + k * .2)
            .fromTo(s_.l.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .2 + k * .2));
          pcols.forEach(c => tl.fromTo(c.m.scale, { y: .001 }, { y: 1, duration: .7, ease: back(1.3), immediateRender: true, ...u }, at + .5)
            .fromTo(c.l.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .8));
          if (evl.length) tl.fromTo(op(evl), { opacity: 0 }, { opacity: 1, duration: .35, stagger: each(evl.length, .08), immediateRender: true, ...u }, at + .9);
        },
        sections(tl, at) {
          SC.forEach((q, si) => { const t0 = at + si * each(ns, .45);
            tl.fromTo(names[si].material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, t0);
            stacks[si].forEach((grp, i) => grp && tl.fromTo(grp.scale, { y: .001 }, { y: 1, duration: .7, ease: back(1.3), immediateRender: true, ...u }, t0 + .1 + i * each(nv, .04))); });
        },
        focus(tl, at) {
          tl.to(v.pose, { ang: .9, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(v.pose.look, { 2: v.pose.look[2] + fz * .3, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            .to(mats(stacks.flatMap((row, si) => si === fi.section ? [] : row.filter(Boolean).flatMap(grp => grp.children))), { opacity: .45, duration: .6, ...u }, at + .3)
            .to(op(names.filter((_, si) => si !== fi.section)), { opacity: .6, duration: .6, ...u }, at + .3)
            .fromTo(focusL.material, { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at + .5);
          pins.forEach((p, k) => tl.fromTo(p.grp.scale, { x: .001, y: .001, z: .001 }, { x: 1, y: 1, z: 1, duration: .3, immediateRender: true, ...u }, at + .4 + k * .12)
            .fromTo(p.grp.position, { y: p.top + 1.4 }, { y: p.top, duration: .7, ease: 'bounce.out', immediateRender: true, ...u }, at + .4 + k * .12));
        }
      }
    };
  });

  /* program — clinical development plan (8.0 scenario family; contract KZClinical.program, shared with the regular demo
     form, the static template and the editable Gantt): a glass deck with one rail per lane receding from the camera,
     time running left to right. Phase blocks rise on the rails, taller as the phase matures; a glass "now" plane sweeps
     to the current quarter and frosts everything ahead of it into plan; milestone pins drop onto the blocks (dark when
     past, white when ahead); the camera then turns to the focus lane. */
  define('program', (host, data) => {
    need(g.KZClinical, 'program 舞台需要 runtime/kz-clinical.js（在 kz-flagship-stages.js 之前加载）');
    const M = g.KZClinical.program(data), q = v => g.KZClinical.ttext(v, M.granularity), C = ST().palette;
    // the visible lanes (a collapsed parent stands for its children: merged phases, major milestones)
    const lanes = M.visible.map(ln => ({ ...ln, bars: ln.bars.length ? ln.bars : (ln.collapsed ? ln.summary || [] : []), milestones: [...ln.milestones, ...(ln.collapsed ? ln.summary_ms || [] : [])].sort((a, b) => a.t - b.t) })), n = lanes.length;
    const PC = g.KZ_TOKENS.charts.phases, span = M.to - M.from, qx = Math.min(.95, 17 / span), Lx = span * qx, pitch = Math.min(2.3, 11 / n), depth = n * pitch;
    const X = t => -Lx / 2 + (t - M.from) * qx, Z = i => -depth / 2 + pitch / 2 + i * pitch, now = M.today, tx = now == null ? null : X(now + M.today_w / 2);
    const hOf = pi => .3 + .2 * pi, D = F().motion.fx.three.dur;
    // a wide stage (catalog wide: true, the whole slide body): framed on the deck plus the name column around x = −2.4
    const v = view3d(host, { ang: 1.0, dist: (Lx / 2 + 3) * 2.26 + n * .2, yaw: 0, origin: [-2, 0, 0], look: [-2, 0, 1] }), T = v.T;
    v.extent(Lx / 2 + 4);
    const plate = new T.Mesh(rbox(T, Lx + 1.4, .2, depth + 1.2, .35), pbr(T, { color: 0xffffff, roughness: .4, transparent: true }));
    plate.position.set(0, -.2, 0); plate.receiveShadow = true; v.scene.add(plate);
    const rails = lanes.map((_, i) => { const r = new T.Mesh(new T.BoxGeometry(Lx + .6, .02, pitch * .62), pbr(T, { color: lin(T, i % 2 ? '#F4EEE6' : '#FBF7F1'), roughness: .8, transparent: true }));
      r.position.set(0, .01, Z(i)); r.receiveShadow = true; v.scene.add(r); return r; });
    // year fins on the deck and the year labels along the front edge
    const fins = [], yearL = [];
    for (let t = M.from; t < M.to; t++) if (t === M.from || t % 4 === 0) {
      if (t !== M.from) { const f = new T.Mesh(new T.BoxGeometry(.03, .05, depth + .6), pbr(T, { color: lin(T, '#D9CFC2'), roughness: .6, transparent: true })); f.position.set(X(t), .03, 0); v.scene.add(f); fins.push(f); }
      const e = Math.min(M.to, (Math.floor(t / 4) + 1) * 4), l = v.label(String(Math.floor(t / 4)), { height: .56, weight: 700, color: INK().muted, depthTest: false });
      l.position.set((X(t) + X(e)) / 2, .1, depth / 2 + 1); l.material.opacity = 0; v.scene.add(l); yearL.push(l);
    }
    const lab = (text, o, x, y, z) => { const l = v.label(text, { depthTest: false, ...o }); l.position.set(x, y, z); l.material.opacity = 0; v.scene.add(l); return l; };
    const nameL = lanes.map((ln, i) => lab(ln.name, { height: .64, weight: 700, color: INK().title, align: 'right' }, -Lx / 2 - .9, .2, Z(i) + (ln.note ? -.26 : 0)));
    const noteL = lanes.map((ln, i) => ln.note ? lab(ln.note, { height: .46, weight: 500, color: INK().muted, align: 'right' }, -Lx / 2 - .9, .2, Z(i) + .4) : null).filter(Boolean);
    // phase blocks: the part before the now plane and the part after it are separate meshes (the second one frosts)
    const blocks = [], planM = [];
    lanes.forEach((ln, i) => ln.bars.forEach(br => {
      const h = hOf(br.pi), x0 = X(br.s) + .05, x1 = X(br.e) - .05, cut = tx != null && tx < x1 ? Math.max(x0, tx) : x1, col = lin(T, PC[br.pi]);
      const mk = (a, b) => { const m = new T.Mesh(rbox(T, 1, h, pitch * .5, Math.min(.12, h * .3)).translate(.5, h / 2, 0), pbr(T, { color: col.clone(), roughness: .32, transparent: true }));
        m.position.set(a, .02, Z(i)); m.scale.x = .001; m.castShadow = true; m.receiveShadow = true; m.userData.len = b - a; v.scene.add(m); return m; };
      const solid = cut > x0 ? mk(x0, cut) : null, plan = cut < x1 ? mk(cut, x1) : null;
      if (plan) planM.push({ m: plan, col: lin(T, hexMix(PC[br.pi], '#FFFFFF', .4)) });
      blocks.push({ i, br, x0, x1, cut, solid, plan, h });
    }));
    // milestone pins: post + head by kind; labels stacked in levels so neighbours in one lane never overlap
    const head = (kind, mat) => { const g0 = head0(kind, mat); g0.scale.setScalar(1.35); return g0; };
    const head0 = (kind, mat) => {
      if (kind === 'start') return new T.Mesh(new T.SphereGeometry(.2, 24, 16), mat);
      if (kind === 'readout') return new T.Mesh(new T.OctahedronGeometry(.27), mat);
      if (kind === 'submit') return new T.Mesh(new T.ConeGeometry(.24, .46, 24), mat);
      if (kind === 'approve') { const s = new T.Shape(); for (let k = 0; k < 10; k++) { const r = k % 2 ? .13 : .3, a = k * Math.PI / 5; s[k ? 'lineTo' : 'moveTo'](Math.sin(a) * r, Math.cos(a) * r); }
        return new T.Mesh(new T.ExtrudeGeometry(s, { depth: .1, bevelEnabled: true, bevelSize: .02, bevelThickness: .02, bevelSegments: 2 }).translate(0, 0, -.05), mat); }
      return new T.Mesh(new T.CylinderGeometry(.21, .21, .16, 6).rotateX(Math.PI / 2), mat);
    };
    const pins = [];
    lanes.forEach((ln, i) => {
      const taken = [];
      ln.milestones.forEach(m => {
        const past = now != null && m.t < now, x = X(m.t + m.tw / 2);
        const blk = blocks.find(b => b.i === i && x >= b.x0 - .01 && x <= b.x1 + .01), top = blk ? blk.h + .02 : .02;
        // past = solid deep brand orange (the 2D "filled" glyph), still ahead = bright amber with an orange glow (the 2D
        // "hollow" one); a graphite head read as a black blot on the warm deck (8.0 colour review)
        const mat = pbr(T, past ? { color: lin(T, m.risk ? RISK() : C.fill[2]), roughness: .35, transparent: true }
          : { color: lin(T, m.risk ? '#F3B0AC' : C.fill[0]), roughness: .35, transparent: true, emissive: lin(T, m.risk ? RISK() : C.fill[1]), emissiveIntensity: .3 });
        const lbl = v.label(m.label, { height: .62, weight: m.key === M.focus ? 800 : 600, color: m.risk ? RISK() : INK().title, depthTest: false });
        const w = lbl.scale.x; let lv = 0;
        while (taken.some(([k, a, b]) => k === lv && !(x + w / 2 + .1 <= a || x - w / 2 - .1 >= b)) && lv < 3) lv++;
        taken.push([lv, x - w / 2, x + w / 2]);
        const post = new T.Mesh(new T.CylinderGeometry(.025, .025, 1, 8).translate(0, .5, 0), pbr(T, { color: lin(T, '#8C8378'), roughness: .5, transparent: true }));
        const hy = top + .8 + lv * .72, grp = new T.Group(), hd = head(m.kind, mat);
        post.scale.y = hy - top; post.position.y = top; hd.position.y = hy; hd.castShadow = true; grp.add(post, hd);
        grp.position.set(x, 0, Z(i)); v.scene.add(grp);
        lbl.position.set(x, hy + .6, Z(i)); lbl.material.opacity = 0; v.scene.add(lbl);
        pins.push({ m, i, grp, hd, post, lbl, past });
      });
    });
    let plane = null, edge = null, nowL = null;
    if (tx != null) {
      plane = new T.Mesh(rbox(T, .06, 1.7, depth + .8, .03), pbr(T, { color: 0xffffff, roughness: .15, transparent: true, opacity: .55 }));
      // 08 GANTT-06: the today marker stays quiet — a frosted plane with a grey edge and label, not an ink rule
      const GD = (g.KZ_TOKENS.gantt && g.KZ_TOKENS.gantt.today) || { line: '#A3A9B0', text: '#555A60' };
      edge = new T.Mesh(new T.BoxGeometry(.03, 1.72, .03), pbr(T, { color: lin(T, GD.line), roughness: .3, transparent: true }));
      plane.position.set(X(M.from), .85, 0); edge.position.set(X(M.from), .86, depth / 2 + .4); v.scene.add(plane, edge);
      nowL = lab(`当前 ${q(now)}`, { height: .5, weight: 700, color: GD.text }, X(M.from), 2.05, depth / 2 + .4);
    }
    const keyPin = pins.find(p => p.m.key === M.focus);
    const fLane = keyPin ? keyPin.i : Math.max(0, lanes.findIndex(l => l.key === M.focus || l.bars.some(b => b.key === M.focus)));
    const u = v.upd(), op = list => list.map(l => l.material);
    return {
      paint: v.paint, dirty: v.dirty, dispose: v.dispose,
      steps: {
        rails(tl, at) {
          tl.from(plate.position, { y: -2.2, duration: D, ease: ease(), ...u }, at).from(plate.material, { opacity: 0, duration: D * .7, ...u }, at)
            .from(rails.map(r => r.scale), { x: .01, duration: .9, stagger: each(n, .08), ease: 'power3.out', ...u }, at + .2)
            .from(mats(fins), { opacity: 0, duration: .5, ...u }, at + .4)
            .fromTo(op([...yearL, ...nameL, ...noteL]), { opacity: 0 }, { opacity: 1, duration: .45, stagger: each(yearL.length + n * 2, .05), immediateRender: true, ...u }, at + .4);
        },
        // blocks grow along time lane by lane; the camera eases in a little as the plan fills
        phases(tl, at) {
          blocks.forEach((b, k) => {
            const t0 = at + b.i * each(n, .18) + (b.br.s - M.from) / span * .5, len = b.x1 - b.x0;
            for (const m of [b.solid, b.plan].filter(Boolean)) {
              const rel0 = (m.position.x - b.x0) / len, rel1 = rel0 + m.userData.len / len;
              tl.fromTo(m.scale, { x: .001 }, { x: m.userData.len, duration: .9 * (rel1 - rel0) + .05, ease: 'none', immediateRender: true, ...u }, t0 + .9 * rel0);
            }
          });
          tl.to(v.pose, { dist: v.pose.dist * .96, duration: 2, ease: 'power2.inOut', ...u }, at);
        },
        // the now plane sweeps to the current quarter with the camera following it; what lies ahead frosts into plan
        today(tl, at) {
          if (!plane) return;
          const dur = 1.4 + (now - M.from) / span * 1.2;
          tl.fromTo([plane.position, edge.position, nowL.position], { x: X(M.from) }, { x: tx, duration: dur, ease: 'power1.inOut', immediateRender: true, ...u }, at)
            .fromTo(op([nowL]), { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: true, ...u }, at)
            .from([plane.material, edge.material], { opacity: 0, duration: .4, ...u }, at)
            .to(v.pose, { yaw: -.12, duration: dur * .6, ease: 'power1.inOut', ...u }, at).to(v.pose, { yaw: 0, duration: dur * .5, ease: 'power1.inOut', ...u }, at + dur * .6);
          planM.forEach(({ m, col }) => tl.to(m.material.color, { r: col.r, g: col.g, b: col.b, duration: .6, ...u }, at + dur * .7)
            .to(m.material, { opacity: .72, roughness: .65, duration: .6, ...u }, at + dur * .7));
        },
        milestones(tl, at) {
          pins.forEach((p, k) => tl.fromTo(p.grp.position, { y: 3.2 }, { y: 0, duration: .7, ease: 'bounce.out', immediateRender: true, ...u }, at + k * each(pins.length, .08))
            .fromTo(p.grp.scale, { x: .01, y: .01, z: .01 }, { x: 1, y: 1, z: 1, duration: .3, immediateRender: true, ...u }, at + k * each(pins.length, .08))
            .fromTo(p.lbl.material, { opacity: 0 }, { opacity: 1, duration: .35, immediateRender: true, ...u }, at + .4 + k * each(pins.length, .08)));
          tl.to(pins.map(p => p.hd.rotation), { y: Math.PI * 2, duration: 2.2, ease: 'power2.out', ...u }, at + .3);
        },
        // the camera pans a little toward the focus (no dolly, tilt or yaw: the name column and the year row sit at the
        // frame edges); the focus lane stays lit, the others step back
        focus(tl, at) {
          const fx = keyPin ? X(keyPin.m.t + keyPin.m.tw / 2) : 0;
          tl.to([v.pose.origin, v.pose.look], { 0: v.pose.look[0] + fx * .07, duration: 1.6, ease: 'power2.inOut', ...u }, at)
            // dimmed blocks also lose their clearcoat: a faded block keeps its full specular and reads as a white glare
            .to(mats(blocks.filter(b => b.i !== fLane).flatMap(b => [b.solid, b.plan].filter(Boolean))), { opacity: .4, clearcoat: 0, duration: .6, ...u }, at + .3)
            .to(mats(pins.filter(p => p.i !== fLane).flatMap(p => [p.hd, p.post])), { opacity: .3, duration: .6, ...u }, at + .3)
            .to(op([...pins.filter(p => p.i !== fLane).map(p => p.lbl), ...nameL.filter((_, i) => i !== fLane)]), { opacity: .4, duration: .6, ...u }, at + .3);
          if (keyPin) tl.to(keyPin.hd.scale, { x: 1.45, y: 1.45, z: 1.45, duration: .6, ease: back(2), ...u }, at + .5)
            .to(keyPin.hd.material, { emissiveIntensity: .6, duration: .6, ...u }, at + .5)
            .to(keyPin.lbl.scale, { x: keyPin.lbl.scale.x * 1.15, y: keyPin.lbl.scale.y * 1.15, duration: .5, ease: back(2), ...u }, at + .5);
        }
      }
    };
  });
})(window);
