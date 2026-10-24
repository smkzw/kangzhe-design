/* Additive wiring only: the upstream runtime owns navigation, hash, overview, presenter and print.
   One lifecycle per direct .slide child (KZHTMLPPT.bind); every component pauses when its slide is inactive. */
(function () {
  'use strict';
  const deck = document.querySelector('.deck'), D = window.KZ_DECK_DATA, mq = matchMedia('(prefers-reduced-motion: reduce)');
  // Static views from the same source: upstream ?preview (presenter thumbnails), print and reduced motion.
  let printing = false;
  const frozen = () => printing || mq.matches || document.body.dataset.preview === '1';
  const lives = new Set();
  // The slide stage is shorter than the site stage, so the carrier keeps the same states with taller geometry.
  const DECK_GEO = [{ x: .02, y: .02, w: .54, h: .9, r: .1 }, { x: .02, y: .02, w: .58, h: .95, r: .08 }, { x: .02, y: .02, w: .6, h: .96, r: .07 }, { x: .02, y: .02, w: .58, h: .94, r: .08 }];
  const deckFilm = { ...D.film, states: D.film.states.map((s, i) => ({ ...s, geometry: DECK_GEO[i] })) };
  const bridge = KZHTMLPPT.bind(deck, slide => {
    const page = KZMotion.mountPage(slide);
    const filmRoot = slide.querySelector('[data-kz-film]');
    const film = filmRoot ? KZRefSite.mountFoldFilm(filmRoot, deckFilm) : null;
    film?.pause('engine-inactive');
    const ce = slide.querySelector('[data-kz-chart]'), chart = ce ? KZCharts.mount(ce, D[ce.dataset.kzChart]) : null;
    const ge = slide.querySelector('[data-kz-gantt]'), gantt = ge ? KZGantt.mount(ge, D[ge.dataset.kzGantt]) : null;
    const life = {
      enter() {
        if (frozen()) { page.finish(); chart?.finish(); gantt?.finish(); film?.seek(film.staticProgress); return; }
        page.enter(); film?.resume('engine-inactive'); chart?.play(); gantt?.play();
      },
      leave() { page.leave(); film?.pause('engine-inactive'); chart?.pause(); gantt?.pause(); },
      finish() { page.finish(); chart?.finish(); gantt?.finish(); film?.seek(film.staticProgress); },
      dispose() { lives.delete(life); for (const x of [page, film, chart, gantt]) x?.dispose(); },
      film, chart, gantt
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
