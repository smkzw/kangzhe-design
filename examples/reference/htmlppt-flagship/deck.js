/* Additive wiring only: the upstream runtime owns navigation, hash, overview, presenter and print.
   KZFlagship.mount adds the F1 chrome, mounts charts, the Gantt and the 3D stage, and binds every slide's scene
   timeline to the presenter's keys through KZHTMLPPT (14 FLAG-09, 06 MOTION-09). */
(function () {
  'use strict';
  const deck = document.querySelector('.deck');
  const fx = KZFlagship.mount(deck, { logo: window.KZ_LOGO, data: window.KZ_DECK_DATA });
  addEventListener('pagehide', () => fx.dispose(), { once: true });
  window.KZ_DECK = { fx };
  document.documentElement.dataset.kzDeckReady = 'true';
})();
