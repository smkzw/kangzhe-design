// Real-input runtime checks for examples/component-lab.html, driven through ego-browser (ego lite):
//   ego-browser nodejs < tests/ego/runtime_checks.mjs
// Any browser driver that sends trusted pointer/keyboard input can port these checks; they are not mocks.
// The script is read from stdin (no file location, no inherited env): set KZ_ROOT to this repository's absolute path.
// Prints one JSON report; exits non-zero when a check fails.
const KZ_ROOT = "/Users/smkzw/Developer/kangzhe-design";
const LAB = "file://" + KZ_ROOT + "/examples/component-lab.html";
const task = await taskSpace("kangzhe-design review");
const page = task.page("p1");
const checks = [];
const check = (name, pass, detail) => checks.push({ name, pass: !!pass, detail });
const wait = ms => page.waitForTimeout(ms);
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
await page.cdp("Emulation.setDeviceMetricsOverride", { width: 1920, height: 940, deviceScaleFactor: 1, mobile: false });
await page.goto("about:blank");
await page.goto(LAB);
await page.waitForFunction(() => document.documentElement.dataset.kzLabReady === "true", undefined, { timeout: 10000 });

// 1. Entrance: reveal layer animates translate/scale only; opacity runs on the glass card itself.
const enter = await page.evaluate(() => {
  const anims = document.getAnimations().map(a => ({ target: a.effect.target, props: a.effect.getKeyframes().flatMap(k => Object.keys(k)).filter(k => !["offset", "easing", "composite", "computedOffset"].includes(k)) }));
  const wrapperOpacity = anims.filter(a => a.target.matches("[data-kz-reveal]") && a.props.includes("opacity") && a.target.querySelector(".kz-card")).length;
  const cardOpacity = anims.filter(a => a.target.matches(".kz-card") && a.props.includes("opacity")).length;
  const wrapperTransform = anims.filter(a => a.target.matches("[data-kz-reveal]") && a.props.some(p => p === "translate" || p === "scale")).length;
  return { total: anims.length, wrapperOpacity, cardOpacity, wrapperTransform };
});
check("入场：玻璃父层不写 opacity（避免 backdrop root 失效）", enter.wrapperOpacity === 0 && enter.cardOpacity > 0 && enter.wrapperTransform > 0, enter);
await wait(1600);

// 2. Pointer light + spring tilt with real mouse input, settle and reset.
const box = await page.evaluate(() => { const r = document.querySelector(".kz-fold-lead .kz-card:not(.kz-kpi)").getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; });
await page.mouse.move(box[0] + box[2] * 0.15, box[1] + box[3] * 0.2);
await page.mouse.move(box[0] + box[2] * 0.18, box[1] + box[3] * 0.22, { label: "hover glass card" });
await wait(700);
const hover = await page.evaluate(() => { const c = document.querySelector(".kz-fold-lead .kz-card:not(.kz-kpi)"), st = getComputedStyle(c); return { lift: +st.getPropertyValue("--kz-lift"), lx: +st.getPropertyValue("--kz-lx"), transform: st.transform, shadow: st.boxShadow.slice(0, 160), max: st.getPropertyValue("--kz-tilt-max") }; });
const rot = (() => { const m = hover.transform.match(/matrix3d\(([^)]+)\)/); return m ? m[1].split(",").map(Number) : null; })();
check("悬停：抬升≈1、光源偏左上、产生 3D 倾斜", hover.lift > 0.95 && hover.lx < -0.4 && !!rot, hover);
check("倾斜上限不超过 tokens（正文 4°）", hover.max.trim() === "4deg", hover.max);
await page.mouse.move(5, 5, { label: "leave card" });
await wait(900);
const reset = await page.evaluate(() => { const st = getComputedStyle(document.querySelector(".kz-fold-lead .kz-card:not(.kz-kpi)")); return { lift: +st.getPropertyValue("--kz-lift"), lx: +st.getPropertyValue("--kz-lx") }; });
check("离开：弹簧回到静止", Math.abs(reset.lift) < 0.01 && Math.abs(reset.lx) < 0.01, reset);

// 3. Film: text cross-fade is deterministic under seek; carrier keeps identity.
const film = await page.evaluate(() => {
  const f = KZ_LAB.film; f.pause("qc");
  const at = p => { f.seek(p); return +getComputedStyle(f.root).getPropertyValue("--kz-film-text"); };
  const r = { mid: at(0.21), early: at(0.14), hold: at(0.05), seam: [at(0), at(0.99999)] };
  const s = f.snapshot(); f.resume("qc");
  return { ...r, sameNode: s.sameNode, connected: s.connected, blur: getComputedStyle(f.carrier).backdropFilter };
});
check("电影：文字在段落中点淡出为 0，停留段为 1", film.mid < 0.05 && film.hold === 1 && film.early > film.mid, film);
check("电影：载体同一节点且无 backdrop-filter（FILM-05）", film.sameNode && film.connected && (film.blur === "none" || film.blur === ""), film.blur);

// 4. KPI count-up ends on the true value.
const kpi = await page.evaluate(() => [...document.querySelectorAll("[data-kz-count]")].map(n => [n.textContent, n.dataset.kzCount]));
check("KPI 计数终值等于真值", kpi.every(([a, b]) => a === b), kpi);

// 5. Drilldown: card→panel morph, wide panel, keys isolated, fold back, focus returns.
await page.click("#open-details", { label: "open drilldown" });
await wait(80);
const opening = await page.evaluate(() => document.querySelector("dialog.kz-dialog").getAnimations().length);
await wait(600);
const opened = await page.evaluate(() => ({ ...KZ_LAB.drill.snapshot(), filmPaused: KZ_LAB.film.snapshot().reasons.includes("dialog") }));
check("下钻：打开有共享元素展开动画", opening > 0, opening);
check("下钻：宽幅（≥80vw）并暂停父电影", opened.open && opened.width / opened.viewport >= 0.8 && opened.filmPaused, opened);
const leaked = await page.evaluate(() => { let n = 0; const h = () => n++; document.addEventListener("keydown", h); const d = document.querySelector("dialog.kz-dialog"); for (const key of ["s", "o", "a", "ArrowRight", "PageDown"]) d.querySelector("button").dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true })); document.removeEventListener("keydown", h); return n; });
check("下钻：S/O/A/方向/翻页键不冒泡到宿主", leaked === 0, leaked);
await page.click("loc=role:button[name='关闭']", { label: "close drilldown" });
await wait(40);
const closing = await page.evaluate(() => ({ snap: KZ_LAB.drill.snapshot().open, native: document.querySelector("dialog.kz-dialog").open }));
await wait(500);
const closed = await page.evaluate(() => ({ native: document.querySelector("dialog.kz-dialog").open, focus: document.activeElement?.id, film: KZ_LAB.film.snapshot().reasons }));
check("下钻：收回动画期间状态即为关闭，动画后原生关闭", closing.snap === false && closing.native === true && closed.native === false, { closing, closed });
check("下钻：焦点回到触发按钮、父电影恢复", closed.focus === "open-details" && !closed.film.includes("dialog"), closed);

// 6. Sections reveal on natural scroll; data reveals play; ambient field shifts.
const before = await page.evaluate(() => { const t = document.querySelector("[data-kz-pending] [data-kz-reveal]"); return { pending: document.querySelectorAll("[data-kz-pending]").length, hiddenBeforeEntrance: !!t && getComputedStyle(t).opacity === "0", shift: getComputedStyle(document.querySelector(".kz-optical-field")).getPropertyValue("--kz-field-shift") }; });
check("段落：入场前保持不可见（不先闪现再淡入）", before.hiddenBeforeEntrance, before);
await page.mouse.move(960, 600);
for (let i = 0; i < 6; i++) await page.mouse.wheel(0, 500, { label: "scroll page" });
await wait(1400);
const after = await page.evaluate(() => ({ pending: document.querySelectorAll("[data-kz-pending]").length, shift: getComputedStyle(document.querySelector(".kz-optical-field")).getPropertyValue("--kz-field-shift"), lineProgress: KZ_LAB.line.getProgress(), y: scrollY }));
check("段落：首屏以下段落待入场，滚到后入场", before.pending >= 2 && after.pending < before.pending, { before, after });
check("光场：自然滚动带动环境层位移（限幅）", Math.abs(+after.shift) > 0 && Math.abs(+after.shift) <= 48, after.shift);
check("图表：进入视口后数据揭示完成", after.lineProgress === 1, after.lineProgress);

// 7. Line chart reveal draws left→right without scaling values.
const line = await page.evaluate(() => { const c = KZ_LAB.line; c.renderProgress(0.5); const d = c.chart.getOption().series[0].data; c.finish(); return { n: d.length, first: d[0], last: d[d.length - 1] }; });
check("折线：半程只显示左半段且首点为真值", line.n <= 3 && JSON.stringify(line.first) === JSON.stringify([0, 12]), line);

// 8. Reduced motion: no tilt, no entrance animations, film shows the static frame.
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.goto("about:blank");
await page.goto(LAB);
await page.waitForFunction(() => document.documentElement.dataset.kzLabReady === "true", undefined, { timeout: 10000 });
const rm = await page.evaluate(() => ({ anims: document.getAnimations().filter(a => a.playState === "running").length, film: KZ_LAB.film.snapshot(), pending: document.querySelectorAll("[data-kz-pending]").length }));
check("减少动态：无运行中的入场动画、无待入场段落", rm.anims === 0 && rm.pending === 0, { anims: rm.anims, pending: rm.pending });
check("减少动态：电影停在静态总览帧", rm.film.reasons.includes("reduced-motion") && Math.abs(rm.film.progress - 0.74) < 1e-6, rm.film.reasons);
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });

const failed = checks.filter(c => !c.pass);
console.log(JSON.stringify({ page: LAB, passed: checks.length - failed.length, failed: failed.length, checks }, null, 1));
if (failed.length) process.exitCode = 1;
