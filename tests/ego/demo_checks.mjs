// Demonstrative motion (15 DEMO): density receipts, per-scene layout and deck stepping, in ego lite.
// Run: ego-browser nodejs < tests/ego/demo_checks.mjs   (prints JSON; exit code 1 when any check fails)
// Gallery: examples/motion/ (sixteen forms, loop mode). Deck: reference HTML-PPT slides 8 (units) and 9 (decision);
// template deck examples/motion/deck/ (ten forms, four presets).
const task = await taskSpace("kangzhe-scene-checks");
const page = task.page("p1");
const ROOT = "file:///Users/smkzw/Developer/kangzhe-design/examples/";
const results = [];
const check = (name, pass, detail) => results.push({ name, pass: !!pass, detail });
await page.goto("about:blank");
const { targetInfo } = await page.cdp("Target.getTargetInfo", {});
const { windowId, bounds } = await task.cdp("Browser.getWindowForTarget", { targetId: targetInfo.targetId });
const wasMin = bounds.windowState === "minimized";
if (wasMin) await task.cdp("Browser.setWindowBounds", { windowId, bounds: { windowState: "normal" } });
// Collect script errors from the first line of every document (nothing in the runtime writes this list).
await page.cdp("Page.enable", {});
await page.cdp("Page.addScriptToEvaluateOnNewDocument", { source: "window.__kzErrors=[];addEventListener('error',e=>__kzErrors.push(String(e.message)));addEventListener('unhandledrejection',e=>__kzErrors.push(String(e.reason)));" });
const viewport = (width, height) => page.cdp("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });

// Visible text objects that overlap each other, leave the canvas or overflow their box; caption line count.
const PROBE = root => {
  const cv = root.querySelector("[data-kz-scene-canvas]"), C = cv.getBoundingClientRect();
  const skip = /kz-demo-(doc|tray|band|playhead|axis|bar|mark|links|bin|lane|paper|block|heat|dep|threshold|icon|dot)\b/;
  const els = [...cv.querySelectorAll("[data-kz-obj]")].filter(e => !(e instanceof SVGElement) && !skip.test(e.className) && getComputedStyle(e).visibility !== "hidden" && +getComputedStyle(e).opacity > .05 && e.textContent.trim());
  const R = els.map(e => ({ id: e.dataset.kzObj, r: e.getBoundingClientRect(), of: e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1 }));
  const out = [], hit = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2;
  for (const a of R) { if (a.r.left < C.left - 1 || a.r.right > C.right + 1 || a.r.top < C.top - 1 || a.r.bottom > C.bottom + 1) out.push("出界 " + a.id); if (a.of) out.push("溢出 " + a.id); }
  for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) if (hit(R[i].r, R[j].r)) out.push(`重叠 ${R[i].id}×${R[j].id}`);
  const cap = root.querySelector("[data-kz-scene-caption]"), lines = Math.round(cap.getBoundingClientRect().height / parseFloat(getComputedStyle(cap).lineHeight));
  if (lines > 2) out.push(`说明 ${lines} 行`);
  return out;
};

// 1. gallery: every form meets the density thresholds and every scene lays out cleanly at two viewports
await viewport(1600, 1000);
await page.goto(ROOT + "motion/index.html");
await page.waitForFunction(() => document.documentElement.dataset.kzGalleryReady === "true", undefined, { timeout: 15000 });
const dens = await page.evaluate(() => {
  const T = KZ_TOKENS.motion.scenes.density, out = {};
  for (const [f, s] of Object.entries(KZ_GALLERY)) {
    const a = s.audit(), thin = a.transitions.filter(t => t.changed < T.min_changed_per_scene).map(t => t.scene);
    const large = a.transitions.filter(t => t.travel >= T.large_travel || t.grow >= T.large_grow).length;
    // space: the fullest scene covers min_canvas_coverage of the canvas grid; figures, not only text boxes
    s.pause("qc"); const cov = s.stops.map(t => { s.seek(t); return s.coverage(); }); s.resume("qc");
    const peak = Math.max(...cov.map(c => c.cells)), figures = Math.max(...cov.map(c => c.figures));
    out[f] = { scenes: a.scenes, objects: a.objects, thin, large, peak, figures, pass: a.scenes >= T.min_scenes && a.objects >= T.min_objects && !thin.length && large >= T.min_large_scenes && peak >= T.min_canvas_coverage && figures >= T.min_figures };
  }
  return out;
});
check("十六种演示都达到 DEMO-03 密度、空间与图形门槛", Object.values(dens).every(d => d.pass) && Object.keys(dens).length === 16, dens);
const layout = {};
for (const [w, h] of [[1600, 1000], [1280, 800]]) {
  await viewport(w, h); await page.waitForTimeout(300);
  for (const f of await page.evaluate(() => Object.keys(KZ_GALLERY))) {
    const n = await page.evaluate(f => { const s = KZ_GALLERY[f]; s.pause("qc"); return s.stops.length; }, f);
    for (let i = 0; i < n; i++) {
      const issues = await page.evaluate(([f, i, P]) => { const s = KZ_GALLERY[f]; s.seek(s.stops[i]); return new Function("root", "return (" + P + ")(root)")(s.root); }, [f, i, PROBE.toString()]);
      if (issues.length) layout[`${w}x${h} ${f}-${i}`] = issues;
    }
    await page.evaluate(f => KZ_GALLERY[f].resume("qc"), f);
  }
}
check("每个 scene 无重叠、出界、溢出（1600×1000 与 1280×800）", !Object.keys(layout).length, layout);
// Every scene is a pure function of position: reached forward, backward or after a loop it renders the same
// classes, text and visibility (a class or text set in a later scene must not linger on an earlier one).
const pathFree = await page.evaluate(() => {
  const sig = s => [...s.canvas.querySelectorAll("[data-kz-obj]")].map(e => `${e.dataset.kzObj}|${e.getAttribute("class")}|${e.textContent}|${e.style.visibility}`).join("\n");
  const out = {};
  for (const [f, s] of Object.entries(KZ_GALLERY)) {
    s.pause("qc"); const n = s.stops.length, fwd = [];
    for (let i = 0; i < n; i++) { s.seek(s.stops[i]); fwd.push(sig(s)); }
    const bad = [];
    for (let i = n - 1; i >= 0; i--) { s.seek(s.stops[i]); if (sig(s) !== fwd[i]) bad.push("back " + i); }
    s.seek(s.stops[n - 1]); s.seek(.9999); s.seek(s.stops[0]); if (sig(s) !== fwd[0]) bad.push("loop 0");
    if (bad.length) out[f] = bad; s.resume("qc");
  }
  const u = KZ_GALLERY.units; u.pause("qc"); u.seek(u.stops[3]); const gap = u.canvas.querySelector('[data-kz-obj="gn1"]').textContent; u.resume("qc");
  return { out, gap };
});
check("scene 与到达路径无关（前进、后退、循环回到 scene 0 一致）", !Object.keys(pathFree.out).length, pathFree.out);
check("units 缺口 scene 显示缺口而不是继承的计数", pathFree.gap === "缺 3 份", pathFree.gap);
const gErr = await page.evaluate(() => window.__kzErrors || []);
// Data-shape regressions (code review, 7.1.3): variants of the gallery data must give true captions or throw.
const shapes = await page.evaluate(() => {
  const D = JSON.parse(JSON.stringify(KZ_MOTION_DATA)), host = document.createElement("div");
  host.style.cssText = "position:absolute;left:0;top:0;width:900px;height:500px"; document.body.append(host);
  const run = (kind, data) => { const el = document.createElement("div"); el.style.height = "500px"; host.replaceChildren(el); try { const st = KZDemo.mount(el, kind, data); st.pause("qc"); return { st, caps: st.spec.scenes.map(x => x.caption).join(" | ") }; } catch (e) { return { err: String(e.message) }; } };
  const out = {};
  const g = JSON.parse(JSON.stringify(D.gantt)); g.recover = { task: "collect", by: 1, action: "加派人手" };
  out.ganttSameTask = /推迟 1 个月/.test(run("gantt", g).caps || "");
  const g2 = JSON.parse(JSON.stringify(D.gantt)); g2.slip.by = 5; out.ganttOffAxisThrows = !!run("gantt", g2).err;
  const c = JSON.parse(JSON.stringify(D.curve)); c.window.to = 5; out.curveNullWindowThrows = !!run("curve", c).err;
  const c3 = JSON.parse(JSON.stringify(D.curve)); c3.series.push({ name: "第三组", role: "comparator", values: [50, 52, 55, 57, 60, 61, 63] });
  const r3 = run("curve", c3); r3.st.seek(r3.st.stops[1]); out.curveThirdShown = +getComputedStyle(r3.st.canvas.querySelector('[data-kz-obj="d2_6"]')).opacity > .5;
  const k = JSON.parse(JSON.stringify(D.consort)); delete k.arms[1].lost; k.arms[1].n = 164; out.consortNoLost = !run("consort", k).err;
  const k2 = JSON.parse(JSON.stringify(D.consort)); k2.arms[0].lost.push({ reason: "其他", n: 999 }); out.consortOverLostThrows = !!run("consort", k2).err;
  const f = JSON.parse(JSON.stringify(D.flow)); f.cases = [f.cases[0]]; out.flowNoFailNoWorst = !/问题集中/.test(run("flow", f).caps || "x问题集中");
  const f0 = JSON.parse(JSON.stringify(D.flow)); f0.cases[1].steps[1].back = "reg"; const r0 = run("flow", f0);
  out.flowBackToFirstInside = !r0.err && [...r0.st.canvas.querySelectorAll("path.is-trace")].every(pth => !/M-|L-/.test(pth.getAttribute("d")));
  const fb = JSON.parse(JSON.stringify(D.flow)); fb.cases[1].steps[1].back = "nope"; out.flowBadBackThrows = !!run("flow", fb).err;
  out.breakdownDecimals = !run("breakdown", { unit: "亿元", total: { label: "总额" }, parts: [{ label: "A", value: .3, children: [{ label: "a1", value: .1 }, { label: "a2", value: .2 }] }, { label: "B", value: .2 }] }).err;
  const m = JSON.parse(JSON.stringify(D.matrix)); m.x.levels = ["1", "2", "3", "4", "5"]; out.matrixNonSquare = /3 档 × 发生可能性 5 档/.test(run("matrix", m).caps || "");
  const t = JSON.parse(JSON.stringify(D.timeline)); t.tasks[0].end = t.max + 2; const rt = run("timeline", t);
  rt.st.seek(rt.st.stops.at(-1)); out.timelineNoStrayTick = +getComputedStyle(rt.st.canvas.querySelector('[data-kz-obj="tc0"]')).opacity < .05;
  const rn = run("network", D.network); rn.st.seek(rn.st.stops[3]);
  out.networkOnlyCurrentRoute = [...rn.st.canvas.querySelectorAll("path[data-kz-obj^='lk']")].filter(pth => /255, ?153, ?0|#FF9900/i.test(getComputedStyle(pth).stroke)).length === 3;
  const rf = run("flow", D.flow); rf.st.seek(0); const rail = rf.st.canvas.querySelector('[data-kz-obj="rail"]'), before = rf.st.coverage().cells; rail.remove(); out.coverageCountsStraightLinks = rf.st.coverage().cells < before;
  host.remove();
  return out;
});
check("数据形态回归：延误与追赶同一任务、时间轴外里程碑、空值窗口、第三条曲线、无脱落组、脱落超额、全部通过、退回首站、无效退回、小数子项、非方阵、轴外完成勾、通道高亮、直线覆盖", Object.values(shapes).every(Boolean), shapes);

// 2. deck: the demo slides step scene by scene like the film (06 MOTION-09)
await viewport(1920, 1080);
await page.goto("about:blank"); await page.goto(ROOT + "reference/htmlppt/index.html#/7");
await page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
await page.waitForTimeout(500);
const cur = () => page.evaluate(() => { const sl = [...document.querySelectorAll(".deck > .slide")], i = sl.findIndex(s => s.classList.contains("is-active")); const l = [...KZ_DECK.lives].find(x => x.film?.root?.closest?.(".slide.is-active")); return { slide: i + 1, scene: l?.film.scene, n: l?.film.stops.length, moving: l?.film.moving }; });
const settle = async () => { const t0 = Date.now(); let s; do { s = await cur(); if (!s.moving) break; await page.waitForTimeout(50); } while (Date.now() - t0 < 6000); return s; };
for (const slide of [8, 9]) {
  if ((await cur()).slide !== slide) { await page.keyboard.press("ArrowRight"); await page.waitForTimeout(400); }
  const s0 = await cur(); await page.waitForTimeout(1500); const s0b = await cur();
  check(`第 ${slide} 页按键进入停在 scene 0`, s0.slide === slide && s0.scene === 0 && s0b.scene === 0 && !s0b.moving, { s0, s0b });
  const seen = [0], issues = {};
  for (let k = 1; k < (s0.n || 0); k++) {
    await page.keyboard.press("ArrowRight"); const s = await settle(); seen.push(s.scene);
    const iss = await page.evaluate(P => new Function("root", "return (" + P + ")(root)")(document.querySelector(".slide.is-active .kz-demo")), PROBE.toString());
    if (iss.length) issues[k] = iss;
  }
  check(`第 ${slide} 页 → 逐个 scene 前进且版面干净`, seen.every((v, k) => v === k) && seen.length >= 4 && !Object.keys(issues).length, { seen, issues });
  await page.keyboard.press("ArrowLeft"); const b = await cur();
  check(`第 ${slide} 页 ← 瞬时退一个 scene`, b.scene === seen.length - 2 && !b.moving, b);
  await page.keyboard.press("ArrowRight"); await settle(); await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300);
  check(`第 ${slide} 页最后一个 scene 之后翻页`, (await cur()).slide === slide + 1);
  if (slide === 8) { await page.keyboard.press("ArrowLeft"); await page.waitForTimeout(300); const back = await cur(); check("从下一页退回演示页时显示最后一个 scene", back.slide === 8 && back.scene === back.n - 1, back); await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300); }
}

// A focused button keeps Space/Enter only; → still steps the scene (upstream would page on any target).
await page.goto("about:blank"); await page.goto(ROOT + "reference/htmlppt/index.html#/7");
await page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
await page.waitForTimeout(400);
await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300);
await page.evaluate(() => { const b = document.createElement("button"); b.id = "kz-qc-btn"; b.textContent = "qc"; document.querySelector(".slide.is-active .kz-body").append(b); b.focus(); });
await page.keyboard.press("ArrowRight"); const fb = await settle();
await page.evaluate(() => document.getElementById("kz-qc-btn").remove());
check("焦点在按钮上时 → 仍进一个 scene", fb.slide === 8 && fb.scene === 1, fb);

// 3. reduced motion: the stage shows its static scene and keys turn pages directly
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.goto("about:blank"); await page.goto(ROOT + "reference/htmlppt/index.html#/7");
await page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
await page.waitForTimeout(400);
await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300); const r1 = await cur(); await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300); const r2 = await cur();
check("减少动态：演示停在静态 scene，按键直接翻页", r1.slide === 8 && r1.scene > 0 && !r1.moving && r2.slide === 9, { r1, r2 });
await page.cdp("Emulation.setEmulatedMedia", { features: [] });

const dErr = await page.evaluate(() => window.__kzErrors || []);

// 4. template deck: every demo slide at three viewports — stage share, clean layout in every scene, preset rotation
const tpl = {}, presets = [];
for (const [w, h] of [[1920, 1080], [1280, 720], [2560, 1080]]) {
  await viewport(w, h);
  for (let n = 2; n <= 11; n++) {
    await page.goto("about:blank"); await page.goto(ROOT + `motion/deck/index.html#/${n}`);
    await page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
    await page.waitForTimeout(600);
    const r = await page.evaluate(P => {
      const T = KZ_TOKENS.motion.scenes.density, sl = document.querySelector(".slide.is-active"), f = [...KZ_DECK.lives].find(x => x.film?.root?.closest?.(".slide.is-active")).film;
      f.pause("qc"); const issues = {};
      for (let i = 0; i < f.stops.length; i++) { f.seek(f.stops[i]); const iss = new Function("root", "return (" + P + ")(root)")(f.root); if (iss.length) issues[i] = iss; }
      const S = sl.getBoundingClientRect(), D = f.root.getBoundingClientRect(), share = D.width * D.height / (S.width * S.height);
      const preset = sl.querySelector(".kz-body").dataset.preset, facts = sl.querySelector("[data-kz-demo-facts]");
      return { kind: f.root.dataset.kzDemo, preset, share: +share.toFixed(3), issues, factsOk: !facts || facts.children.length >= 3, pass: share >= T.min_stage_share && !Object.keys(issues).length && (!facts || facts.children.length >= 3) };
    }, PROBE.toString());
    if (w === 1920) presets.push(r.preset);
    if (!r.pass) tpl[`${w}x${h} ${n}`] = r;
  }
}
check("模板组十页：舞台占比、每个 scene 版面干净、事实条（1920×1080、1280×720、2560×1080）", !Object.keys(tpl).length, tpl);
check("模板组相邻演示页不重复预设，四个预设都出现", presets.every((p, i) => !i || p !== presets[i - 1]) && new Set(presets).size === 4, presets);
// stepping: → walks the scenes of a template slide one by one, then pages
await viewport(1920, 1080);
await page.goto("about:blank"); await page.goto(ROOT + "motion/deck/index.html#/2");
await page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
await page.waitForTimeout(600);
const tSeen = [(await cur()).scene];
for (let k = 1; k < 5; k++) { await page.keyboard.press("ArrowRight"); tSeen.push((await settle()).scene); }
await page.keyboard.press("ArrowRight"); await page.waitForTimeout(300);
check("模板组第 2 页 → 逐 scene 前进，最后一个 scene 后翻页", tSeen.join() === "0,1,2,3,4" && (await cur()).slide === 3, { tSeen, after: await cur() });

const errors = [...gErr, ...dErr, ...await page.evaluate(() => window.__kzErrors || [])];
check("无脚本错误", !errors.length, errors);
await page.cdp("Emulation.clearDeviceMetricsOverride", {});
if (wasMin) await task.cdp("Browser.setWindowBounds", { windowId, bounds: { windowState: "minimized" } });
console.log(JSON.stringify({ results }, null, 1));
if (results.some(r => !r.pass)) process.exitCode = 1;
