/* Reference wiring for site/stream pages: behaviour only; all reading content is already in the HTML. */
(function () {
  'use strict';
  const q = (s, r = document) => r.querySelector(s), qa = (s, r = document) => [...r.querySelectorAll(s)];
  const el = KZDrilldown.element, clamp01 = x => Math.max(0, Math.min(1, x));
  const life = [];

  // First-screen film from a storyboard: carrier facts, step rail, nodes and links share the film clock.
  function mountFoldFilm(root, spec) {
    const sb = KZMotion.storyboard(spec.states);
    const nodes = qa('[data-kz-node]', root), steps = qa('.kz-steps [data-phase]'), svg = q('.kz-film-links', root), facts = q('.kz-carrier-facts', root);
    const span = .03, linkProgress = (i, p) => {
      // Node i joins when state i begins (node 0 from the start); all but node 0 withdraw in the closing move.
      const start = sb.enterAt[i] ?? 0;
      if (i === 0) return 1;
      if (p < start) return 0;
      return p < sb.closeAt ? clamp01((p - start) / span) : 1 - clamp01((p - sb.closeAt) / span);
    };
    let shown = -1;
    const film = new KZMotion.Film(root, { frames: sb.frames, duration: sb.duration, onRender(f, p, self) {
      const phase = sb.phaseAt(p);
      steps.forEach((n, i) => { n.dataset.state = i < phase ? 'done' : i === phase ? 'current' : 'todo'; n.setAttribute('aria-current', i === phase ? 'step' : 'false'); });
      const pairs = nodes.map((n, i) => { const k = linkProgress(i, p); n.style.opacity = String(.42 + .58 * k); n.style.translate = `${(1 - k) * 8}px 0`; return { id: 'n' + i, from: self.carrier, to: n, progress: k }; });
      if (svg) KZMotion.drawLinks(svg, pairs);
      const index = spec.states.findIndex(s => s.label === f.label);
      if (facts && index !== shown) { shown = index; facts.replaceChildren(...(spec.states[index]?.facts || []).map(t => el('li', null, t))); }
      if (facts) facts.style.opacity = f.textAlpha.toFixed(3);
    } });
    life.push(film);
    return film;
  }

  function table(rows) {
    const t = el('table', 'kz-ref-table');
    for (const [a, b] of rows) { const tr = el('tr'); tr.append(el('th', null, a), el('td', null, b)); t.append(tr); }
    return t;
  }
  function mountDetails(details, film) {
    const drill = new KZDrilldown.Drilldown({ host: q('.kz') || document.body, onOpen() { film?.pause('dialog'); }, onClose() { film?.resume('dialog'); } });
    const render = id => (container, manager) => {
      const d = details[id];
      container.append(el('p', 'kz-ref-intro', d.intro), table(d.rows));
      if (d.next) { const b = el('button', 'kz-button', '查看' + details[d.next].title); b.type = 'button'; b.style.marginTop = '20px'; b.addEventListener('click', () => manager.push({ id: d.next, title: details[d.next].title, render: render(d.next) }, b)); container.append(b); }
      return {};
    };
    for (const b of qa('[data-kz-detail]')) b.addEventListener('click', e => { const id = b.dataset.kzDetail; drill.push({ id, title: details[id].title, render: render(id) }, e.currentTarget); });
    life.push(drill);
    return drill;
  }

  function mountMotion() {
    const fold = q('.kz-fold');
    if (fold) { const page = KZMotion.mountPage(fold); page.enter(); life.push(page); }
    const counters = qa('.kz-fold [data-kz-count]').map(n => KZMotion.countUp(n, { to: Number(n.dataset.kzCount), decimals: Number(n.dataset.kzDecimals || 0) }));
    setTimeout(() => counters.forEach(c => c.play()), 180);
    qa('[data-kz-section]').forEach(s => life.push(KZMotion.mountTilt(s)));
    life.push(KZMotion.mountSections(document), KZMotion.mountField(document), ...counters);
  }

  // Data reveals start once, when the chart first scrolls into view.
  function whenVisible(node, play) {
    const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) { io.disconnect(); play(); } }, { threshold: .3 });
    io.observe(node); life.push({ dispose: () => io.disconnect() });
  }
  function chart(id, data) {
    const node = q('#' + id); if (!node) return null;
    const c = KZCharts.mount(node, data); life.push(c); whenVisible(node, () => c.play()); return c;
  }

  window.KZRefSite = {
    mountFoldFilm,
    mount(kind) {
      const R = window.KZ_REF, out = {};
      mountMotion();
      const filmRoot = q('.kz-fold .kz-film');
      if (filmRoot) out.film = mountFoldFilm(filmRoot, kind === 'chapter' ? R.chapter.film : R.home.film);
      out.drill = mountDetails(R.details, out.film);
      out.completeness = chart('chart-completeness', R.home.completeness);
      out.trend = chart('chart-trend', R.chapter.trend);
      const g = q('#gantt');
      if (g) { out.gantt = KZGantt.mount(g, R.chapter.gantt); life.push(out.gantt); whenVisible(g, () => out.gantt.play()); }
      out.dispose = () => life.splice(0).reverse().forEach(x => x.dispose?.());
      document.documentElement.dataset.kzRefReady = 'true';
      return out;
    }
  };
})();
