/* KZ6-0929-A01 P3 — film wiring on top of KZMotion.Film.
   KZMotion.Film is the ONLY time owner. This module adds the meaningful part the base
   runtime does not provide: the four relation segments (carrier <-> node connectors,
   relation predicate chips, sequential sub-info) and the static-overview control.
   No extra rAF, no scroll-driven clock, no CSS keyframe animation on the carrier. */
(function (global) {
  'use strict';

  var T = [0, 0.22, 0.46, 0.68, 0.88, 1];              /* keyframe times, shared grammar */
  var R_IN = 0.045, R_OUT = 0.035;                      /* relation enter / leave ramps */

  /* Normalized carrier keyframes [x,y,w,h,r]. Every set keeps right edge <= 0.56 so the
     node column (left 0.70) is never entered, and left edge >= 0.02. */
  var GEO = {
    'film.site.home': [[0.18, 0.30, 0.38, 0.34, 0.34], [0.12, 0.24, 0.44, 0.36, 0.22], [0.04, 0.10, 0.34, 0.78, 0.06], [0.04, 0.10, 0.34, 0.78, 0.06], [0.10, 0.22, 0.44, 0.46, 0.22], [0.18, 0.30, 0.38, 0.34, 0.34]],
    'film.site.chapter': [[0.22, 0.34, 0.34, 0.30, 0.40], [0.14, 0.06, 0.42, 0.32, 0.26], [0.04, 0.40, 0.32, 0.46, 0.10], [0.04, 0.40, 0.32, 0.46, 0.10], [0.12, 0.26, 0.42, 0.44, 0.24], [0.22, 0.34, 0.34, 0.30, 0.40]],
    'film.stream.home': [[0.20, 0.28, 0.36, 0.32, 0.36], [0.12, 0.10, 0.44, 0.34, 0.24], [0.04, 0.16, 0.34, 0.70, 0.08], [0.04, 0.16, 0.34, 0.70, 0.08], [0.12, 0.24, 0.42, 0.46, 0.24], [0.20, 0.28, 0.36, 0.32, 0.36]],
    'film.stream.chapter': [[0.16, 0.30, 0.40, 0.34, 0.34], [0.10, 0.12, 0.46, 0.32, 0.24], [0.04, 0.22, 0.34, 0.60, 0.10], [0.04, 0.22, 0.34, 0.60, 0.10], [0.12, 0.26, 0.42, 0.44, 0.24], [0.16, 0.30, 0.40, 0.34, 0.34]],
    'film.l2.process': [[0.04, 0.20, 0.34, 0.50, 0.20], [0.04, 0.10, 0.38, 0.42, 0.16], [0.02, 0.22, 0.32, 0.56, 0.08], [0.02, 0.22, 0.32, 0.56, 0.08], [0.04, 0.18, 0.36, 0.52, 0.20], [0.04, 0.20, 0.34, 0.50, 0.20]]
  };

  var TINT = [[255, 251, 242, 0.70], [255, 249, 236, 0.66], [255, 255, 255, 0.80],
              [255, 255, 255, 0.80], [255, 250, 241, 0.70], [255, 251, 242, 0.70]];

  /* Per film: which relation predicate is used, relation lifetime, duration, static frame. */
  var CONFIG = {
    'film.site.home': {
      duration: 38000, staticProgress: 0.74,
      predicates: ['限定', '对应', '连接', '回收'],
      born: [0.08, 0.26, 0.50, 0.70], died: 0.97,
      sub: [
        '先明确需要解决的问题与纳入资料的边界。',
        '将资料按主题与形成时间组织，保留缺失信息。',
        '比较各组资料并识别仍需补足的限制。',
        '回到原有问题，确认现有资料是否足以支持理解。'
      ],
      captions: ['研究问题限定资料范围', '资料分组对应问题', '组间差异连接待确认事项', '审阅结果回到初始范围']
    },
    'film.site.chapter': {
      duration: 40000, staticProgress: 0.74,
      predicates: ['限定', '对应', '缺失', '回收'],
      born: [0.08, 0.26, 0.50, 0.70], died: 0.97,
      sub: [
        '先明确需要解决的问题与纳入资料的边界。',
        '将资料按主题与形成时间组织，保留缺失信息。',
        '第二阶段资料缺失，按缺失读取，不能按零或相邻值解读。',
        '回到原有问题，确认现有资料是否足以支持理解。'
      ],
      captions: ['研究问题限定资料范围', '资料分组对应问题', '组间差异连接待确认事项', '审阅结果回到初始范围']
    },
    'film.stream.home': {
      duration: 36000, staticProgress: 0.74,
      predicates: ['限定', '对应', '连接', '回收'],
      born: [0.08, 0.26, 0.50, 0.70], died: 0.97,
      sub: [
        '先明确需要解决的问题与纳入资料的边界。',
        '将资料按主题与形成时间组织，保留缺失信息。',
        '比较各组资料并识别仍需补足的限制。',
        '回到原有问题，确认现有资料是否足以支持理解。'
      ],
      captions: ['研究问题限定资料范围', '资料分组对应问题', '组间差异连接待确认事项', '审阅结果回到初始范围']
    },
    'film.stream.chapter': {
      duration: 42000, staticProgress: 0.74,
      predicates: ['限定', '核对', '连接', '回收'],
      born: [0.08, 0.26, 0.50, 0.70], died: 0.97,
      sub: [
        '先明确需要解决的问题与纳入资料的边界。',
        '按资料形成时间逐项核对；缺失记为 null，禁止按其他阶段推算。',
        '比较各组资料并识别仍需补足的限制。',
        '回到原有问题，确认现有资料是否足以支持理解。'
      ],
      captions: ['研究问题限定资料范围', '按资料形成时间逐项核对', '组间差异连接待确认事项', '审阅结果回到初始范围']
    },
    'film.l2.process': {
      duration: 34000, staticProgress: 0.72,
      predicates: ['顺序', '缺席', '登记', '回收'],
      born: [0.10, 0.30, 0.54, 0.74], died: 0.96,
      sub: [
        '以形成时间顺序逐项核对，不跳项、不合并。',
        '阶段二缺失记为 null，禁止按其他阶段推算，也不按零读取。',
        '比较各组资料并识别仍需补足的限制，登记为待确认事项。',
        '回到原有问题，确认现有资料是否足以支持理解。'
      ],
      captions: ['按资料形成时间逐项核对', '缺失记为 null，不插补', '组间差异连接待确认事项', '审阅结果回到初始范围']
    }
  };

  var LABELS = ['界定范围', '整理证据', '审阅差异', '回到问题'];
  var LABELS_STREAM_CHAPTER = ['界定范围', '逐项核对', '审阅差异', '回到问题'];
  var LABELS_L2 = ['逐项核对', '记录缺失', '组间比较', '回到范围'];

  function labelsFor(id) {
    if (id === 'film.l2.process') return LABELS_L2;
    if (id === 'film.stream.chapter') return LABELS_STREAM_CHAPTER;
    return LABELS;
  }

  /* KZMotion.sample() only carries x/y/w/h/r/tint/label/caption/index, so the segment index
     is derived from the returned frame index. Frame 5 is the loop-back frame == frame 0. */
  function segmentOf(frameIndex) { return frameIndex >= 5 ? 0 : Math.min(frameIndex, 3); }

  function buildFrames(id) {
    var g = GEO[id], c = CONFIG[id], lab = labelsFor(id), out = [];
    for (var i = 0; i < 6; i++) {
      var sIdx = i === 5 ? 0 : Math.min(i, 3);              /* f4 and f5 return to the opening context */
      out.push({
        t: T[i], x: g[i][0], y: g[i][1], w: g[i][2], h: g[i][3], r: g[i][4],
        tint: TINT[i].slice(), label: lab[sIdx], caption: c.captions[sIdx], stateIndex: sIdx
      });
    }
    return out;
  }

  /* Relation visibility: 0 outside [born, died); ramps in/out inside. */
  function relAlpha(p, born, died) {
    if (p < born || p >= died) return 0;
    var a = Math.min(1, (p - born) / R_IN);
    var b = Math.min(1, (died - p) / R_OUT);
    return Math.max(0, Math.min(a, b));
  }

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function mount(root) {
    var id = root.dataset.filmId;
    if (!CONFIG[id]) throw new Error('未知电影配置 ' + id);
    var cfg = CONFIG[id];
    var stage = root.querySelector('.kz-film-stage');
    var carrier = root.querySelector('.kz-film-carrier');
    var subEl = carrier.querySelector('.kz-film-carrier-sub');
    var metaEl = carrier.querySelector('.kz-film-carrier-meta');
    var svg = root.querySelector('.kz-film-links');
    var chipLayer = root.querySelector('.kz-film-chips');
    var nodeEls = Array.prototype.slice.call(root.querySelectorAll('.kz-rel'));
    var frames = buildFrames(id);
    if (nodeEls.length !== 4) throw new Error('电影需要 4 个关系节点');

    var NS = 'http://www.w3.org/2000/svg';
    var paths = [], chips = [], nodes = [];
    var W = 0, H = 0;
    var compact = function () { return global.matchMedia('(max-width:800px)').matches; };

    for (var i = 0; i < 4; i++) {
      var path = document.createElementNS(NS, 'path');
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', KZ_TOKENS.colors.brand);
      path.setAttribute('stroke-width', '2');
      path.setAttribute('stroke-linecap', 'round');
      path.setAttribute('opacity', '0');
      svg.appendChild(path);
      var chip = document.createElement('span');
      chip.className = 'kz-chip';
      chip.textContent = cfg.predicates[i];
      chip.style.opacity = '0';                 /* HTML elements need the CSS property, not the SVG attribute */
      chip.setAttribute('aria-hidden', 'true');
      chipLayer.appendChild(chip);
      paths.push(path);
      chips.push(chip);
      nodes.push({ el: nodeEls[i], nx: 0, ny: 0, nw: 0, nh: 0, len: 0, chipW: 0 });
    }

    /* Layout pass: cache node pixel rects and path lengths. Runs on resize only, so no
       per-frame layout reads (06 sec.14). */
    function layout() {
      W = stage.clientWidth; H = stage.clientHeight;
      svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      if (compact() || !W || !H) return;
      for (var i = 0; i < 4; i++) {
        var r = nodeEls[i].getBoundingClientRect();
        var sr = stage.getBoundingClientRect();
        nodes[i].nx = r.left - sr.left;
        nodes[i].ny = r.top - sr.top;
        nodes[i].nw = r.width;
        nodes[i].nh = r.height;
        nodes[i].chipW = chips[i].offsetWidth;
      }
    }

    function cable(cx, cy, nx, ny) {
      var dx = Math.max(36, (nx - cx) * 0.45);
      return 'M' + cx.toFixed(1) + ',' + cy.toFixed(1) +
        ' C' + (cx + dx).toFixed(1) + ',' + cy.toFixed(1) +
        ' ' + (nx - dx).toFixed(1) + ',' + ny.toFixed(1) +
        ' ' + nx.toFixed(1) + ',' + ny.toFixed(1);
    }

    var visibleCount = 0;

    function onRender(f, p) {
      var compactMode = compact();
      var st = cfg.sub[segmentOf(f.index)];
      if (subEl.textContent !== st) subEl.textContent = st;

      for (var i = 0; i < 4; i++) {
        var a = relAlpha(p, cfg.born[i], cfg.died);
        var n = nodes[i];
        n.el.style.opacity = a ? String(a) : '0';
        n.el.style.transform = 'translateY(' + ((1 - a) * 12).toFixed(1) + 'px)';
        if (compactMode || !W || !H) {
          paths[i].setAttribute('opacity', '0');
          chips[i].style.opacity = '0';
          continue;
        }
        var cx = (f.x + f.w) * W + 2, cy = (f.y + f.h / 2) * H;   /* start at the carrier edge so no cable is hidden under it */
        var ncx = n.nx - 6, ncy = n.ny + n.nh / 2;   /* terminate at the node edge, not its centre */
        var d = cable(cx, cy, ncx, ncy);
        if (paths[i].getAttribute('d') !== d) paths[i].setAttribute('d', d);
        n.len = d.length * 0.6;                            /* cheap upper-bound proxy for dash length */
        paths[i].setAttribute('opacity', String(a * 0.85));
        var midX = (cx + ncx) / 2, half = n.chipW / 2;
        var lo = (f.x + f.w) * W + half + 8, hi = n.nx - half - 12;
        var chipX = lo <= hi ? clamp(midX, lo, hi) : midX;
        chips[i].style.left = chipX.toFixed(1) + 'px';
        chips[i].style.top = ((cy + ncy) / 2).toFixed(1) + 'px';
        chips[i].style.opacity = String(a);
      }

      var count = 0;
      for (var j = 0; j < 4; j++) if (relAlpha(p, cfg.born[j], cfg.died) > 0.5) count++;
      visibleCount = count;
      if (metaEl) metaEl.textContent = '已建立关系 ' + count + ' / 4';
      root.dataset.kzProgress = p.toFixed(5);
      root.dataset.kzRelations = String(count);
    }

    layout();
    var film = new KZMotion.Film(root, {
      frames: frames,
      duration: cfg.duration,
      staticProgress: cfg.staticProgress,
      minCarrierWidth: 240,
      onRender: onRender
    });

    var ro = new ResizeObserver(function () { layout(); film.render(); });
    ro.observe(stage);

    var staticBtn = root.querySelector('[data-kz-static]');
    var kzRoot = root.closest('.kz');
    if (staticBtn) {
      staticBtn.setAttribute('aria-pressed', 'false');
      staticBtn.addEventListener('click', function () {
        var frozen = root.dataset.kzFrozen === 'true';
        if (frozen) {
          root.dataset.kzFrozen = 'false';
          if (kzRoot) kzRoot.dataset.kzFrozen = 'false';
          staticBtn.setAttribute('aria-pressed', 'false');
          staticBtn.textContent = '静态总览';
          film.resume('user');
        } else {
          root.dataset.kzFrozen = 'true';
          if (kzRoot) kzRoot.dataset.kzFrozen = 'true';
          staticBtn.setAttribute('aria-pressed', 'true');
          staticBtn.textContent = '恢复播放';
          film.pause('user');
          film.seek(cfg.staticProgress);
          var target = root.querySelector('[data-kz-static-note]');
          if (target && target.focus) target.focus({ preventScroll: false });
        }
      });
    }

    var handle = {
      id: id, film: film, frames: frames, nodes: nodes, cfg: cfg,
      relAlpha: relAlpha,
      layout: layout,
      snapshot: function () {
        var s = film.snapshot();
        s.relationsVisible = visibleCount;
        s.chipOrder = chips.map(function (c) { return c.style.opacity; });
        return s;
      },
      dispose: function () {
        try { ro.disconnect(); } catch (e) { }
        film.dispose();
        unregister(handle);
        root.dataset.kzMounted = 'false';
      }
    };
    return handle;
  }

  /* Mount every film inside the given root (defaults to the whole document).
     Returns ONLY the films mounted by this call — never the cumulative registry,
     so a caller can never capture an unrelated (e.g. parent) film by accident. */
  var registry = [];
  function mountAll(scope) {
    var host = scope || document;
    var list = [];
    if (host.matches && host.matches('[data-kz-film]')) list.push(host);
    list = list.concat([].slice.call(host.querySelectorAll('[data-kz-film]')));
    var mounted = [];
    list.forEach(function (el) {
      if (el.dataset.kzMounted === 'true') return;
      var handle = mount(el);
      el.dataset.kzMounted = 'true';
      registry.push(handle);
      mounted.push(handle);
    });
    return mounted;
  }
  function get(id) {
    for (var i = 0; i < registry.length; i++) if (registry[i].id === id) return registry[i];
    return null;
  }
  function disposeAll() {
    var copy = registry.slice();
    copy.forEach(function (h) { h.dispose(); });
    registry = [];
  }
  function unregister(handle) {
    var i = registry.indexOf(handle);
    if (i >= 0) registry.splice(i, 1);
  }

  global.KZ_FILMS = {
    mount: mount, mountAll: mountAll, get: get, disposeAll: disposeAll, unregister: unregister,
    GEO: GEO, T: T, CONFIG: CONFIG, buildFrames: buildFrames, relAlpha: relAlpha
  };
})(window);
