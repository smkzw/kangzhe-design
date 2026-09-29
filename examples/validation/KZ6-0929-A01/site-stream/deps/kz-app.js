/* KZ6-0929-A01 P3 — page wiring: ECharts mount (with null gap marking), single-width
   drilldown dialog with breadcrumb stack, parent-film modal pause/resume, and a
   small set of QC probes exposed on window for the EGO QC pass. */
(function (global) {
  'use strict';

  var D = global.KZ_DATA;

  /* ---------- chart ---------- */
  function mountChart(el, statusEl) {
    if (!global.echarts || !global.KZCharts) {
      if (statusEl) statusEl.textContent = '图表运行时不可用；下方数据表为完整真值。';
      return null;
    }
    var data = D.chartOptionData();
    var handle;

    function markGap() {
      var c = global.echarts.getInstanceByDom(el);
      if (!c) return;
      c.setOption({
        series: [{
          id: data.series[0].id,
          markLine: {
            silent: true, symbol: ['none', 'none'], animation: false,
            lineStyle: { color: 'rgba(192,0,0,.42)', type: 'dashed', width: 1.5 },
            label: {
              show: true, position: 'insideEndTop', formatter: '未提供（null）',
              color: KZ_TOKENS.colors.risk, fontSize: 16
            },
            data: [{ xAxis: D.chart.null_category }]
          }
        }]
      });
    }

    try {
      handle = KZCharts.mount(el, data, { onProgress: function () { markGap(); } });
      markGap();
      if (statusEl) statusEl.textContent = '单位：' + D.chart.unit + '；' + D.chart.null_meaning + '。';
    } catch (err) {
      if (statusEl) statusEl.textContent = '图表未能挂载：' + err.message + '；下方数据表为完整真值。';
      return null;
    }
    return handle;
  }

  /* ---------- drilldown: L1 detail -> L2 limitations + independent process film ---------- */
  function cell(tag, text, cls) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    el.textContent = text;
    return el;
  }

  function row(cells) {
    var tr = document.createElement('tr');
    cells.forEach(function (c) { tr.appendChild(c); });
    return tr;
  }

  function buildL1(section) {
    var h = cell('h3', '归档数据与口径');
    var p = cell('p', '同一数据对象派生图表与表格；数值与单位不在页面之间手抄。');
    p.className = 'kz-method';

    var table = document.createElement('table');
    table.className = 'kz-datatable';
    var thead = document.createElement('thead');
    thead.appendChild(row([cell('th', '阶段'), cell('th', '数量（份）'), cell('th', '读取状态')]));
    var tbody = document.createElement('tbody');
    D.chart.categories.forEach(function (cat, i) {
      var v = D.chart.series[0].values[i];
      var status = v === null ? '缺失（null），非零，不插补' : '已提供';
      tbody.appendChild(row([
        cell('td', cat),
        v === null ? cell('td', D.formatValue(v), 'kz-null') : cell('td', D.formatValue(v)),
        cell('td', status)
      ]));
    });
    table.appendChild(thead);
    table.appendChild(tbody);

    var methodH = cell('h3', '资料核对方法');
    var methodP = cell('p', D.chart.method);
    methodP.className = 'kz-method';

    var recH = cell('h3', '逐项核对记录示例');
    var recP = cell('p', '形成时间、内容范围、对应阶段、缺失状态与登记备注构成一条记录；形成时间无法确定的记录单独标注，不并入任何阶段。');
    recP.className = 'kz-method';
    var recTable = document.createElement('table');
    recTable.className = 'kz-datatable';
    var rHead = document.createElement('thead');
    rHead.appendChild(row([cell('th', '记录'), cell('th', '形成时间'), cell('th', '对应阶段'), cell('th', '登记状态')]));
    var rBody = document.createElement('tbody');
    [
      ['记录 A', '2026-02', '第一阶段', '已核对'],
      ['记录 B', '2026-05', '第一阶段', '已核对'],
      ['记录 C', '2027-01', '第二阶段', '缺失（null），待确认'],
      ['记录 D', '2027-06', '第三阶段', '已核对'],
      ['记录 E', '2027-09', '第三阶段', '内容不一致，待确认'],
      ['记录 F', '2028-04', '第四阶段', '已核对'],
      ['记录 G', '时间不明', '未归入阶段', '待确认']
    ].forEach(function (r) {
      rBody.appendChild(row([
        cell('td', r[0]), cell('td', r[1]), cell('td', r[2]),
        r[3].indexOf('待确认') >= 0 ? cell('td', r[3], 'kz-null') : cell('td', r[3])
      ]));
    });
    recTable.appendChild(rHead);
    recTable.appendChild(rBody);

    var more = document.createElement('button');
    more.type = 'button';
    more.className = 'kz-button kz-button-primary';
    more.textContent = '查看解释限制与独立核对过程';
    more.setAttribute('data-kz-open-l2', '');

    section.append(h, p, table, methodH, methodP, recH, recP, recTable, more);
    return more;
  }

  function buildL2(section, host) {
    var limH = cell('h3', '解释限制');
    var ul = document.createElement('ul');
    D.chart.limitations.forEach(function (t) { ul.appendChild(cell('li', t)); });

    var filmH = cell('h3', '独立核对过程');
    var filmWrap = document.createElement('div');
    filmWrap.className = 'kz-film';
    filmWrap.setAttribute('data-kz-film', '');
    filmWrap.setAttribute('data-film-id', 'film.l2.process');

    var stage = document.createElement('div');
    stage.className = 'kz-film-stage kz-film-stage-dialog';
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'kz-film-links');
    svg.setAttribute('aria-hidden', 'true');
    var carrier = document.createElement('div');
    carrier.className = 'kz-film-carrier';
    carrier.setAttribute('data-kz-carrier-id', 'carrier-l2-process');
    var cl = cell('span', '', 'kz-film-carrier-label');
    var cs = cell('p', '', 'kz-film-carrier-sub');
    var cm = cell('div', '', 'kz-film-carrier-meta');
    carrier.append(cl, cs, cm);
    var nodes = document.createElement('ul');
    nodes.className = 'kz-film-nodes';
    D.process_steps.forEach(function (s) {
      var li = document.createElement('li');
      li.className = 'kz-rel';
      var ti = cell('h3', '', 'kz-rel-title');
      ti.append(cell('span', s.predicate, 'kz-rel-pred'), cell('span', s.label));
      var de = cell('p', s.detail, 'kz-rel-detail');
      li.append(ti, de);
      nodes.appendChild(li);
    });
    var chips = document.createElement('div');
    chips.className = 'kz-film-chips';
    stage.append(svg, carrier, nodes, chips);

    var captionLine = cell('p', '', 'kz-film-caption-line');
    captionLine.append(cell('strong', '当前关系：'), cell('span', '', 'kz-film-caption'));
    var controls = document.createElement('div');
    controls.className = 'kz-film-controls';
    var pause = cell('button', '暂停', 'kz-button');
    pause.type = 'button'; pause.setAttribute('data-kz-pause', '');
    var replay = cell('button', '重播', 'kz-button');
    replay.type = 'button'; replay.setAttribute('data-kz-replay', '');
    var slider = document.createElement('input');
    slider.type = 'range'; slider.min = '0'; slider.max = '1000'; slider.value = '0';
    slider.setAttribute('data-kz-progress', '');
    slider.setAttribute('aria-label', '核对过程电影进度');
    var ptext = cell('span', '0%', 'kz-film-progress');
    ptext.setAttribute('data-kz-progress-text', '');
    var staticBtn = cell('button', '静态总览', 'kz-button');
    staticBtn.type = 'button'; staticBtn.setAttribute('data-kz-static', '');
    controls.append(pause, replay, slider, ptext, staticBtn);

    filmWrap.append(stage, captionLine, controls);
    filmWrap.append(buildStaticList(D.process_steps.map(function (s) {
      return { predicate: s.predicate, label: s.label, detail: s.detail };
    }), 'film.l2.process'));

    section.append(limH, ul, filmH, filmWrap);
    return filmWrap;
  }

  function buildStaticList(items, filmId) {
    var wrap = document.createElement('div');
    var note = cell('p', '静态总览：以下为完整关系真值，随电影是否播放都不改变。', 'kz-static-note');
    note.setAttribute('data-kz-static-note', '');
    note.tabIndex = -1;
    var grid = document.createElement('div');
    grid.className = 'kz-static';
    grid.id = 'static-' + filmId;
    items.forEach(function (it) {
      var card = document.createElement('div');
      card.className = 'kz-card';
      var v = cell('span', '关系：' + it.predicate, 'kz-rel-verb');
      var t = cell('h3', it.label);
      var p = cell('p', it.detail);
      card.append(v, t, p);
      grid.appendChild(card);
    });
    wrap.append(note, grid);
    return wrap;
  }

  function mountDrilldown(opts) {
    opts = opts || {};
    var parentFilmId = opts.parentFilmId;
    var childHandle = null;

    var dd = new KZDrilldown.Drilldown({
      /* Host must live inside the .kz design scope, otherwise the .kz .kz-dialog*
         rules never match and the dialog falls back to the UA fit-content box. */
      host: document.querySelector('.kz') || document.body,
      onOpen: function () {
        var p = parentFilmId && global.KZ_FILMS.get(parentFilmId);
        if (p) { p.film.pause('modal'); }
      },
      onClose: function () {
        var p = parentFilmId && global.KZ_FILMS.get(parentFilmId);
        if (p) { p.film.resume('modal'); }
        if (childHandle) { childHandle.dispose(); childHandle = null; }
      }
    });

    function openL1(trigger) {
      dd.push({
        id: 'l1-archive',
        title: '归档数据与口径',
        render: function (section) {
          var more = buildL1(section);
          more.addEventListener('click', function () { openL2(this); });
          return {
            dispose: function () { }
          };
        }
      }, trigger);
    }

    function openL2(trigger) {
      dd.push({
        id: 'l2-limits',
        title: '解释限制与核对过程',
        render: function (section) {
          var wrap = buildL2(section);
          var handles = global.KZ_FILMS.mountAll(wrap);
          var h = handles[0] || null;
          if (!h) throw new Error('独立过程电影未能挂载');
          childHandle = h;
          return {
            pause: function () { h.film.pause('modal'); },
            resume: function () { h.film.resume('modal'); },
            dispose: function () { h.dispose(); childHandle = null; }
          };
        }
      }, trigger);
    }

    return { dd: dd, openL1: openL1, openL2: openL2 };
  }

  /* ---------- optional in-page anchor router (stream) ---------- */
  function highlightAnchors() {
    var links = document.querySelectorAll('.kz-anchors a[href^="#"]');
    if (!links.length) return;
    var ids = Array.prototype.map.call(links, function (a) { return a.getAttribute('href').slice(1); });
    function sync() {
      var hash = location.hash ? location.hash.slice(1) : ids[0];
      Array.prototype.forEach.call(links, function (a) {
        if (a.getAttribute('href') === '#' + hash) a.setAttribute('aria-current', 'true');
        else a.removeAttribute('aria-current');
      });
    }
    global.addEventListener('hashchange', sync);
    sync();
  }

  global.KZ_APP = { mountChart: mountChart, mountDrilldown: mountDrilldown, highlightAnchors: highlightAnchors, buildStaticList: buildStaticList };
})(window);
