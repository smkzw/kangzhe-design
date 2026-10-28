/* Kangzhe 7.1 — line icons for demonstrative stages (15 DEMO-08). Drawn for this package on a 24×24 grid, stroke
   1.8, round joins; colour follows currentColor, so state classes recolour them. No third-party artwork.
     KZIcons.svg(name, {title}) → <svg>      KZIcons.names → [...]
   Icons name things the material names (documents, subjects, sites, labs, visits); they do not stand in for
   mechanisms, anatomy or study results (04: no invented mechanism pictures). */
(function (global) {
  'use strict';
  const P = {
    doc: 'M6 3h8l4 4v14H6z M14 3v4h4 M9 12h6 M9 16h6',
    'doc-check': 'M6 3h8l4 4v14H6z M14 3v4h4 M9 14.5l2 2 4-4',
    'doc-x': 'M6 3h8l4 4v14H6z M14 3v4h4 M10 12l4 4 M14 12l-4 4',
    'doc-missing': 'M6 3h8l4 4v14H6z M14 3v4h4 M10.5 11.5a1.8 1.8 0 1 1 2.4 1.7c-.6.2-.9.7-.9 1.3 M12 17.5v.3',
    person: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21c0-4 3.6-6 8-6s8 2 8 6',
    people: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M2.5 20c0-3.5 2.9-5.5 6.5-5.5s6.5 2 6.5 5.5 M16 4.5a3 3 0 0 1 0 6 M17.5 14.5c2.4.5 4 2.3 4 5',
    site: 'M4 21V8l8-5 8 5v13z M10 21v-5h4v5 M12 8v5 M9.5 10.5h5',
    building: 'M4 21V5h10v16 M14 9h6v12 M7 9h2 M7 13h2 M7 17h2 M17 13h1 M17 17h1 M2 21h20',
    lab: 'M9 3h6 M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3 M7.5 15h9',
    pill: 'M10.5 3.5a5 5 0 0 1 7 7l-7 7a5 5 0 0 1-7-7z M7 10l7 7',
    syringe: 'M18 2l4 4 M20 4l-9.5 9.5 M14 6l4 4 M8.5 11.5l4 4 M10.5 13.5L4 20 M7 17l-2-2',
    calendar: 'M4 6h16v15H4z M4 10h16 M8 3v5 M16 3v5 M8 14h2 M14 14h2 M8 17h2',
    clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v5l3 2',
    check: 'M5 12.5l4.5 4.5L19 7',
    cross: 'M6 6l12 12 M18 6L6 18',
    warn: 'M12 3l10 18H2z M12 10v5 M12 18v.5',
    search: 'M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z M15.5 15.5L21 21',
    database: 'M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
    send: 'M3 5h18v14H3z M3 6l9 7 9-7',
    shield: 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z M8.5 12l2.5 2.5 4.5-4.5',
    flag: 'M5 21V4 M5 4h11l-2 4 2 4H5',
    chart: 'M4 4v16h16 M8 16v-5 M12 16V8 M16 16v-7',
    sign: 'M4 20h16 M5 16L15 6l3 3L8 19H5z',
    archive: 'M3 4h18v4H3z M5 8v12h14V8 M10 12h4',
    lock: 'M6 11h12v10H6z M8.5 11V7.5a3.5 3.5 0 0 1 7 0V11',
    rework: 'M4 12a8 8 0 0 1 14-5.3 M18 3v4h-4 M20 12a8 8 0 0 1-14 5.3 M6 21v-4h4',
    escalate: 'M12 20V5 M6 11l6-6 6 6 M5 21h14',
    unlink: 'M9 15l-2 2a3.5 3.5 0 0 1-5-5l2-2 M15 9l2-2a3.5 3.5 0 0 1 5 5l-2 2 M8 4v3 M4 8h3 M16 20v-3 M20 16h-3'
  };
  const NS = 'http://www.w3.org/2000/svg';
  function svg(name, { title } = {}) {
    if (!P[name]) throw Error('未知图标：' + name);
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '1.8'); s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round');
    s.setAttribute('class', 'kz-icon'); s.dataset.icon = name;
    if (title) { const t = document.createElementNS(NS, 'title'); t.textContent = title; s.append(t); } else s.setAttribute('aria-hidden', 'true');
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', P[name]); s.append(p);
    return s;
  }
  global.KZIcons = { svg, names: Object.keys(P) };
})(window);
