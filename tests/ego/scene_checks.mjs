// HTML-PPT scene stepping (06 MOTION-09) on the regular reference deck, with real keyboard and touch input in ego lite.
// Run: ego-browser nodejs < tests/ego/scene_checks.mjs   (prints JSON; exit code 1 when any check fails)
// Slide 5 carries the four-state film; slides 4 and 6 have no scenes.
const task = await taskSpace("kangzhe-scene-checks");
const page = task.page("p1");
const URL = "file:///Users/smkzw/Developer/kangzhe-design/examples/reference/htmlppt/index.html";
const results = [];
const check = (name, pass, detail) => results.push({ name, pass: !!pass, detail });
const ready = () => page.waitForFunction(() => document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
// Screenshots are not taken, but a minimized window also throttles rAF: restore it for the run.
await page.goto("about:blank");
const { targetInfo } = await page.cdp("Target.getTargetInfo", {});
const { windowId, bounds } = await task.cdp("Browser.getWindowForTarget", { targetId: targetInfo.targetId });
const wasMin = bounds.windowState === "minimized";
if (wasMin) await task.cdp("Browser.setWindowBounds", { windowId, bounds: { windowState: "normal" } });
// Collect script errors from the first line of every document (nothing in the runtime writes this list).
await page.cdp("Page.enable", {});
await page.cdp("Page.addScriptToEvaluateOnNewDocument", { source: "window.__kzErrors=[];addEventListener('error',e=>__kzErrors.push(String(e.message)));addEventListener('unhandledrejection',e=>__kzErrors.push(String(e.reason)));" });
await page.cdp("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });

const state = () => page.evaluate(() => {
  const slides = [...document.querySelectorAll(".deck > .slide")], i = slides.findIndex(s => s.classList.contains("is-active"));
  const film = window.KZ_DECK.lives && [...window.KZ_DECK.lives].find(l => l.film)?.film;
  return { slide: i + 1, scene: film?.scene, moving: film?.moving, p: film && +film.p.toFixed(4), last: film?.scenes.length - 1, reasons: film && [...film.reasons] };
});
const settle = async (ms = 4000) => { const t0 = Date.now(); let s; do { s = await state(); if (!s.moving) break; await page.waitForTimeout(50); } while (Date.now() - t0 < ms); return { ...s, ms: Date.now() - t0 }; };
const press = async k => { await page.keyboard.press(k); await page.waitForTimeout(60); };

// frame rate of this browser, so a slow display is visible in the report
await page.goto("about:blank"); await page.goto(URL + "#/4"); await ready(); await page.waitForTimeout(800);
const fps = await page.evaluate(() => new Promise(r => { let n = 0; const t0 = performance.now(); const f = () => { n++; performance.now() - t0 < 1000 ? requestAnimationFrame(f) : r(n); }; requestAnimationFrame(f); }));

// 1. attended entry: scene 0, waits for the presenter
await press("ArrowRight");
let s = await state(); await page.waitForTimeout(2500); const s2 = await state();
check("按键进入电影页停在 scene 0，不自动推进", s.slide === 5 && s.scene === 0 && !s2.moving && s2.p === s.p, { s, s2 });

// 2. → plays the move into scene 1 and stops; real-time speed regardless of frame rate
await press("ArrowRight"); const mid = await state(); const a1 = await settle();
check("→ 播放到 scene 1 的运动并停住，仍在本页", mid.moving && a1.scene === 1 && !a1.moving && a1.slide === 5, { mid, a1 });
const move = await page.evaluate(() => KZ_TOKENS.motion.film.storyboard.move_ms);
check("scene 运动按真实时间完成（不随帧率变慢）", a1.ms <= move + 1200 + 1000 / Math.max(1, fps), { settled_ms: a1.ms, move_ms: move, fps });
await page.waitForTimeout(2000);
check("停住后不自动进入下一 scene", (await state()).scene === 1 && !(await state()).moving);

// 3. ↓ and Space are also next; after the last scene the next press turns the page
await press("ArrowDown"); const a2 = await settle();
await press(" "); const a3 = await settle();
check("↓ 与空格各进一个 scene", a2.scene === 2 && a3.scene === 3 && a3.slide === 5, { a2, a3 });
await press("PageDown"); await page.waitForTimeout(300);
check("最后一个 scene 之后再按才翻页", (await state()).slide === 6, await state());

// 4. back from the next slide: the film is shown complete; ↑ / ← step back without rewinding
await press("ArrowLeft"); await page.waitForTimeout(300); const b0 = await state();
check("从后一页退回时显示最后一个 scene", b0.slide === 5 && b0.scene === b0.last && !b0.moving, b0);
await press("ArrowUp"); const b1 = await state();
check("↑ 回到上一 scene 为瞬时（不倒带）", b1.scene === b0.last - 1 && !b1.moving, b1);
await press("ArrowLeft"); await press("PageUp"); const b2 = await state();
check("← 与 PageUp 各退一个 scene", b2.scene === 0 && b2.slide === 5, b2);
await press("ArrowLeft"); await page.waitForTimeout(300);
check("scene 0 时 ← 翻到上一页", (await state()).slide === 4);

// 5. a second press during a move finishes that move; it does not skip a scene
await press("ArrowRight"); await press("ArrowRight"); await press("ArrowRight"); const c = await state();
check("运动中再按一次只是完成当前运动", c.slide === 5 && c.scene === 1 && !c.moving, c);

// 6. ↑/↓ on a slide without scenes turn the page (upstream does not bind them)
await page.goto("about:blank"); await page.goto(URL + "#/3"); await ready(); await page.waitForTimeout(500);
await press("ArrowDown"); const d1 = (await state()).slide; await press("ArrowUp"); const d2 = (await state()).slide;
check("无 scene 的页 ↓/↑ 照常翻页", d1 === 4 && d2 === 3, { d1, d2 });

// 7. unattended entry (deep link; same path as the presenter window) plays the scenes through once
await page.goto("about:blank"); await page.goto(URL + "#/5"); await ready(); await page.waitForTimeout(600);
const u = await state();
check("深链或演讲者窗口进入时一次走完全部 scene", u.moving || u.scene > 0, u);

// 8. swipes: left / up = next scene, right / down = previous
await page.goto("about:blank"); await page.goto(URL + "#/4"); await ready(); await page.waitForTimeout(500);
await press("ArrowRight"); await page.waitForTimeout(300);
// Each CDP call is a round trip; a gesture slower than swipe_max_ms is (correctly) not a swipe, so it is timed.
const gestures = [];
const swipe = async (x0, y0, x1, y1) => {
  const t0 = Date.now();
  await page.cdp("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: x0, y: y0 }] });
  await page.cdp("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: x1, y: y1 }] });
  await page.cdp("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  gestures.push(Date.now() - t0);
  await page.waitForTimeout(80);
  return gestures.at(-1);
};
// A gesture that reached the page slower than swipe_max_ms is rightly ignored; retry it (up to 3 times) only
// when the page did not react, so a slow CDP round trip is not mistaken for a bug.
const sw = async (...a) => { const before = (await state()).p; for (let k = 0; k < 3; k++) { await swipe(...a); if ((await state()).p !== before) return; } };
await sw(1400, 600, 700, 620); const w1 = await settle();
await sw(960, 800, 950, 300); const w2 = await settle();
await sw(950, 300, 960, 800); const w3 = await state();
check("左滑与上滑进下一 scene，下滑退回", w1.scene === 1 && w2.scene === 2 && w3.scene === 1 && w3.slide === 5, { w1, w2, w3, gesture_ms: gestures });

// 9. reduced motion: no stepping, the static overview frame; keys turn pages directly
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.goto("about:blank"); await page.goto(URL + "#/4"); await ready(); await page.waitForTimeout(400);
await press("ArrowRight"); const r1 = await state(); await press("ArrowRight"); const r2 = await state();
check("减少动态：电影停在静态总览帧，按键直接翻页", r1.slide === 5 && r1.reasons.includes("reduced-motion") && r2.slide === 6, { r1, r2 });
await page.cdp("Emulation.setEmulatedMedia", { features: [] });

const errs = await page.evaluate(() => window.__kzErrors || []);
await page.cdp("Emulation.clearDeviceMetricsOverride", {});
if (wasMin) await task.cdp("Browser.setWindowBounds", { windowId, bounds: { windowState: "minimized" } });
console.log(JSON.stringify({ fps, errors: errs, results }, null, 1));
if (results.some(r => !r.pass)) process.exitCode = 1;
