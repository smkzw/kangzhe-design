/* Site wiring: each stage loops on its own clock while visible (offscreen stages pause themselves). */
(function () {
  'use strict';
  const D = window.KZ_MOTION_DATA, stages = {};
  for (const el of document.querySelectorAll('[data-demo]')) stages[el.dataset.demo] = KZDemo.mount(el, el.dataset.demo, D[el.dataset.demo], { loop: true });
  // stacked layouts show the facts each form computed from its data (15 DEMO-05)
  for (const el of document.querySelectorAll('[data-facts]')) KZDemo.renderFacts(el, stages[el.dataset.facts]);
  window.KZ_GALLERY = stages;
  document.documentElement.dataset.kzGalleryReady = 'true';
})();
