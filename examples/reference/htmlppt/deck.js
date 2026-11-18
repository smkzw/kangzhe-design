/* Additive wiring only: the upstream runtime owns navigation, hash, overview, presenter and print.
   One lifecycle per direct .slide child (KZHTMLPPT.bind); every component pauses when its slide is inactive.
   The film steps by scene: the bridge offers next/previous presses to life.next()/prev() first (06 MOTION-09). */
(function () {
  'use strict';
  const deck = document.querySelector('.deck'), D = window.KZ_DECK_DATA, mq = matchMedia('(prefers-reduced-motion: reduce)');
  // Static views from the same source: upstream ?preview (presenter thumbnails), print and reduced motion.
  let printing = false;
  const frozen = () => printing || mq.matches || document.body.dataset.preview === '1';
  const lives = new Set();
  // The slide stage is shorter than the site stage, so the carrier keeps the same states with taller geometry.
  const DECK_GEO = [{ x: .02, y: .02, w: .54, h: .9, r: .1 }, { x: .02, y: .02, w: .58, h: .95, r: .08 }, { x: .02, y: .02, w: .6, h: .96, r: .07 }, { x: .02, y: .02, w: .58, h: .94, r: .08 }];
  const deckFilm = D.film && { ...D.film, states: D.film.states.map((s, i) => ({ ...s, geometry: DECK_GEO[i] })) };
  const bridge = KZHTMLPPT.bind(deck, slide => {
    const page = KZMotion.mountPage(slide);
    const filmRoot = slide.querySelector('[data-kz-film]');
    const demoRoot = slide.querySelector('[data-kz-demo-kind]');
    // One scene stepper per slide: the carrier film or a demonstrative stage (15 DEMO); both step by scene.
    const film = filmRoot ? KZRefSite.mountFoldFilm(filmRoot, deckFilm, { scenes: true })
      : demoRoot ? KZDemo.mount(demoRoot, demoRoot.dataset.kzDemoKind, D.demos[demoRoot.dataset.kzDemoData]) : null;
    film?.pause('engine-inactive');
    // demo-stack: the strip under the stage shows the facts the form computed (15 DEMO-05)
    const facts = slide.querySelector('[data-kz-demo-facts]'); if (facts && demoRoot) KZDemo.renderFacts(facts, film);
    // every chart on the slide (template pages can carry several, 13 BODY-02); `chart` stays the first for QC
    const charts = [...slide.querySelectorAll('[data-kz-chart]')].map(ce => KZCharts.mount(ce, D[ce.dataset.kzChart])), chart = charts[0] || null;
    const ge = slide.querySelector('[data-kz-gantt]'), gantt = ge ? KZGantt.mount(ge, D[ge.dataset.kzGantt]) : null;
    const life = {
      // info.direction 'backward': entered from a later slide, so show the last scene complete;
      // info.attended false (presenter window, deep link): play the scenes through once.
      enter(info = {}) {
        if (frozen()) { page.finish(); charts.forEach(c => c.finish()); gantt?.finish(); film?.seek(film.staticProgress); return; }
        page.enter(); charts.forEach(c => c.play()); gantt?.play();
        if (film) {
          film.toScene(info.direction === 'backward' ? film.scenes.length - 1 : 0);
          if (!info.attended && info.direction !== 'backward') film.playThrough();
          film.resume('engine-inactive');
        }
      },
      next() { return !frozen() && !!film?.next(); },
      prev() { return !frozen() && !!film?.prev(); },
      leave() { page.leave(); film?.pause('engine-inactive'); charts.forEach(c => c.pause()); gantt?.pause(); },
      finish() { page.finish(); charts.forEach(c => c.finish()); gantt?.finish(); film?.seek(film.staticProgress); },
      dispose() { lives.delete(life); for (const x of [page, film, ...charts, gantt]) x?.dispose(); },
      film, chart, charts, gantt
    };
    lives.add(life);
    return life;
  });
  const freezeAll = () => { if (frozen()) lives.forEach(l => l.finish()); };
  mq.addEventListener('change', freezeAll);
  addEventListener('beforeprint', () => { printing = true; freezeAll(); });
  addEventListener('afterprint', () => { printing = false; });
  addEventListener('pagehide', () => bridge.dispose(), { once: true });
  window.KZ_DECK = { bridge, lives };
  document.documentElement.dataset.kzDeckReady = 'true';
})();
