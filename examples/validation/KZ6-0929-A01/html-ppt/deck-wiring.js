/* KZ6-0929-A01 · P1B · deck wiring
 *
 * 职责（全部为增量接线，不新建引擎）：
 *   1) 把上游 .is-active 映射到 .deck[data-chrome]，使 hero 页隐藏正文 chrome；
 *   2) 用真实 DOM 物理序号写入每页打印页码，并与标记里的静态值交叉校验；
 *   3) 挂载随包 ECharts 折线图（KZCharts）与可编辑季度甘特（KZGantt）；
 *   4) 通过组件生命周期在离开页面时暂停，不留下持续消耗帧的隐藏页面。
 *
 * 明确不做：不修改导航、不写 hash、不接管键盘、不新建第二个 slideshow。
 * 缩放、翻页、hash、presenter、preview、打印基础能力全部仍由 upstream runtime.js 拥有。
 * 使用康哲 6.0.0 增量桥 KZHTMLPPT.bind（adapters/html-ppt-bridge.js）。
 */
(function (g) {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var deck = document.querySelector('.deck');
    if (!deck) return;

    var status = {
      bridge: 'missing',
      echarts: !!g.echarts,
      tokens: !!g.KZ_TOKENS,
      chart: 'absent',
      gantt: 'absent',
      printPages: 'absent',
      chrome: 'absent',
      errors: []
    };

    /* ---------- 1) 授权资产映射（供后续阶段核对 page-plan.json） ---------- */
    var assets = {};
    deck.querySelectorAll('[data-asset]').forEach(function (el) {
      var id = el.getAttribute('data-asset');
      assets[id] = (assets[id] || 0) + 1;
    });
    deck.setAttribute('data-asset-map', Object.keys(assets).sort().join(','));
    g.__kzAssetMap = assets;

    /* ---------- 2) 打印页码 = 真实物理序号 ----------
     * 标记里已写静态正确值（无 JS 也能正确打印）；此处用真实 DOM 序号覆写并校验，
     * 使页码不可能因页序调整而过期。总数含封面等页（01-core.md:14）。 */
    var slides = Array.prototype.slice.call(deck.querySelectorAll(':scope > .slide'));
    var total = slides.length;
    slides.forEach(function (slide, i) {
      slide.setAttribute('data-physical-index', String(i + 1));
      var chrome = slide.querySelector('.kz-print-chrome');
      if (!chrome) return;
      var n = i + 1;
      var want = n + ' / ' + total;
      var el = chrome.querySelector('[data-kz-print-page]');
      if (el) el.textContent = want;
      var declared = chrome.getAttribute('data-static-print-page');
      if (declared && declared !== want) {
        status.errors.push('print-page static!=physical on index ' + n + ': "' + declared + '" vs "' + want + '"');
      }
      slide.setAttribute('data-print-page', String(n));
      slide.setAttribute('data-print-total', String(total));
    });
    status.printPages = 'set:1..' + total;

    /* ---------- 3) 图表：唯一 ECharts 实现 ---------- */
    var inst = { chart: null, gantt: null };
    var chartEl = deck.querySelector('[data-kz-chart]');
    if (chartEl && g.KZCharts && g.KZ_DECK_DATA) {
      try {
        inst.chart = g.KZCharts.mount(chartEl, g.KZ_DECK_DATA.chart);
        status.chart = 'mounted';
      } catch (e) {
        status.chart = 'error';
        status.errors.push('chart: ' + e.message);
      }
    } else if (chartEl) {
      status.chart = 'blocked:missing-dependency';
    }

    /* ---------- 4) 甘特：可编辑季度模型 ---------- */
    var ganttEl = deck.querySelector('[data-kz-gantt]');
    if (ganttEl && g.KZGantt && g.KZ_DECK_DATA) {
      try {
        var gd = g.KZ_DECK_DATA.gantt;
        var ganttInput = gd.taskColor
          ? Object.assign({}, gd, { tasks: gd.tasks.map(function (t) {
              return Object.assign({}, t, { color: gd.taskColor });
            }) })
          : gd;
        inst.gantt = g.KZGantt.mount(ganttEl, ganttInput);
        status.gantt = 'mounted';
      } catch (e) {
        status.gantt = 'error';
        status.errors.push('gantt: ' + e.message);
      }
    } else if (ganttEl) {
      status.gantt = 'blocked:missing-dependency';
    }

    /* ---------- 5) 生命周期：chrome 切换 + 组件暂停/播放 ---------- */
    if (!g.KZHTMLPPT || typeof g.KZHTMLPPT.bind !== 'function') {
      deck.setAttribute('data-chrome-status', 'bridge-missing');
      deck.setAttribute('data-wiring-status', JSON.stringify(status));
      return;
    }

    g.KZHTMLPPT.bind(deck, function (slide) {
      // Upstream overview contains cloned .slide nodes; lifecycle applies only
      // to the seven direct children of the audience deck.
      if (slides.indexOf(slide) < 0) return {};
      var preview = document.body.getAttribute('data-preview') === '1';
      return {
        enter: function () {
          deck.setAttribute('data-chrome', slide.getAttribute('data-chrome') || 'body');
          // Upstream preview returns before go() populates the page counter.
          // Fill only its existing slot; navigation and preview-goto stay upstream.
          if (preview) {
            var counter = deck.querySelector(':scope > .deck-footer .slide-number');
            if (counter) {
              counter.setAttribute('data-current', String(slides.indexOf(slide) + 1));
              counter.setAttribute('data-total', String(total));
            }
          }
          if (slide.hasAttribute('data-kz-chart-page') && inst.chart) { preview ? inst.chart.finish() : inst.chart.play(); }
          if (slide.hasAttribute('data-kz-gantt-page') && inst.gantt) {
            inst.gantt.resume();
            preview ? inst.gantt.finish() : inst.gantt.play();
          }
        },
        leave: function () {
          if (inst.chart) inst.chart.pause();
          if (inst.gantt) inst.gantt.pause();
        }
      };
    });

    status.bridge = 'bound';
    status.chrome = deck.getAttribute('data-chrome') || 'unset';
    deck.setAttribute('data-chrome-status', 'bridge-bound');
    deck.setAttribute('data-wiring-status', JSON.stringify(status));
    /* 编程 API 暴露给自动化测试（不作为受众可见的导出入口） */
    g.__kzInstances = inst;
    g.__kzWiring = status;
  });
})(window);
