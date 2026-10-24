/* Additive wiring only: the upstream runtime owns navigation, hash, overview, presenter and print.
   KZFlagship draws the light field, lenses and identity capsule; KZHTMLPPT.bind gives each direct .slide one
   component lifecycle. Charts and the Gantt reveal after the light has settled (14 FLAG-04). */
(function () {
  'use strict';
  const deck = document.querySelector('.deck'), D = window.KZ_DECK_DATA, TR = KZ_TOKENS.flagship.transition;
  const mq = matchMedia('(prefers-reduced-motion: reduce)');
  const fx = KZFlagship.mount(deck, { logo: window.KZ_LOGO });
  let printing = false;
  const frozen = () => printing || fx.frozen;
  const revealAt = TR.content_delay_ms + 2 * TR.step_ms;
  const lives = new Set();
  const bridge = KZHTMLPPT.bind(deck, slide => {
    const ce = slide.querySelector('[data-kz-chart]'), chart = ce ? KZCharts.mount(ce, D[ce.dataset.kzChart]) : null;
    const ge = slide.querySelector('[data-kz-gantt]'), gantt = ge ? KZGantt.mount(ge, D[ge.dataset.kzGantt]) : null;
    let timer = 0;
    const life = {
      enter() {
        clearTimeout(timer);
        if (frozen()) { chart?.finish(); gantt?.finish(); return; }
        timer = setTimeout(() => { chart?.play(); gantt?.play(); }, revealAt);
      },
      leave() { clearTimeout(timer); chart?.pause(); gantt?.pause(); },
      finish() { clearTimeout(timer); chart?.finish(); gantt?.finish(); },
      dispose() { clearTimeout(timer); lives.delete(life); chart?.dispose(); gantt?.dispose(); }
    };
    lives.add(life);
    return life;
  });
  const freezeAll = () => { if (frozen()) lives.forEach(l => l.finish()); };
  mq.addEventListener('change', freezeAll);
  addEventListener('beforeprint', () => { printing = true; freezeAll(); });
  addEventListener('afterprint', () => { printing = false; });
  addEventListener('pagehide', () => { bridge.dispose(); fx.dispose(); }, { once: true });
  window.KZ_DECK = { bridge, fx, lives };
  fx.ready.then(() => { document.documentElement.dataset.kzDeckReady = 'true'; });
})();
