// Flagship runtime checks on the reference deck (14 FLAG-03/04/05/06/09) with real keyboard input in ego lite.
// Run: ego-browser nodejs < tests/ego/flagship_checks.mjs   (prints JSON; exit code 1 when any check fails)
// Note: ego lite 0.6.0.20 drops rAF to ~1 fps after any rAF animation, so this file asserts states, not frame rates.
const task = await taskSpace("kangzhe-flagship-checks");
const page = task.page("p1");
const URL = "file:///Users/smkzw/Developer/kangzhe-design/examples/reference/htmlppt-flagship/index.html";
const results = [];
const check = (name, pass, detail) => results.push({ name, pass: !!pass, detail });
const ready = () => page.waitForFunction(() => document.documentElement.dataset.kzfReady === "true" && document.documentElement.dataset.kzDeckReady === "true", undefined, { timeout: 15000 });
await page.cdp("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });

// 1. live deck: field, lenses, capsule, calm geometry
await page.goto("about:blank"); await page.goto(URL + "#/1"); await ready();
await page.evaluate(() => { window.__errs = []; addEventListener("error", e => window.__errs.push(String(e.message))); });
const boot = await page.evaluate(() => ({
  field: document.querySelector(".kzf-field")?.tagName,
  // upstream overview clones every slide; only the live deck children and the capsule own lenses
  lenses: [...document.querySelectorAll(".deck > .slide .kzf-lens, .kzf-identity")].map(e => getComputedStyle(e).backdropFilter).filter(v => v.startsWith("url")).length,
  total: document.querySelectorAll(".deck > .slide .kzf-lens, .kzf-identity").length,
  name: document.querySelector(".kzf-identity-name")?.textContent,
  logo: document.querySelector(".kzf-identity img")?.getAttribute("src"),
  chrome: document.querySelectorAll(".kz-mark, .kz-foot, .kz-chrome").length
}));
check("光场为 WebGL canvas", boot.field === "CANVAS", boot.field);
check("Chromium 上透镜都用 SVG 位移", boot.lenses === boot.total && boot.total > 0, `${boot.lenses}/${boot.total}`);
check("身份胶囊是官方 Logo + 产品中心医学部", boot.name === "产品中心医学部" && /logo_bot\.svg$/.test(boot.logo || ""), boot);
check("没有固定页眉页脚", boot.chrome === 0, boot.chrome);

// 2. real paging: capsule glides to the page-kind corner; entrances finish after the light; content page has calm rects
const idPos = () => page.evaluate(() => { const r = document.querySelector(".kzf-identity").getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), kind: document.documentElement.dataset.kzfKind }; });
const p1 = await idPos();
await page.keyboard.press("ArrowRight"); await page.keyboard.press("ArrowRight"); await page.keyboard.press("ArrowRight");
// entrances start on the next committed frame; ego lite 0.6.0.20 can delay that by ~2 s, so allow 6 s
await page.waitForTimeout(6000);
const p4 = await idPos();
check("翻到内容页后胶囊移到右上", p4.kind === "content" && p4.x > p1.x + 600 && p4.y < 200, { p1, p4 });
const enter = await page.evaluate(() => { const s = document.querySelector(".deck > .slide.is-active"); const els = [...s.querySelectorAll("[data-kzf-in]")]; return { n: els.length, shown: els.filter(e => +getComputedStyle(e).opacity > 0.98).length, calm: s.querySelectorAll("[data-kzf-calm]").length, pool: s.querySelectorAll("[data-kzf-pool]").length, lenses: s.querySelectorAll(".kzf-lens").length }; });
check("内容页元素全部入场", enter.n > 0 && enter.shown === enter.n, enter);
check("内容页标了安静区且至多一个聚光对象", enter.calm >= 2 && enter.pool <= 1, enter);
check("每页透镜不超过上限", enter.lenses <= 3, enter.lenses);
const order = await page.evaluate(() => { const T = KZ_TOKENS.flagship.transition; const a = document.querySelector(".deck > .slide.is-active [data-kzf-in]").getAnimations()[0]; return { delay: a?.effect.getTiming().delay, min: T.content_delay_ms }; });
check("内容在光停下后入场（delay ≥ content_delay_ms）", order.delay >= order.min, order);
// rapid paging: the second turn inside min_interval_ms moves the light without a second whole-page wave (WCAG 2.3.1)
await page.keyboard.press("ArrowRight"); await page.keyboard.press("ArrowRight");
const rapid = await page.evaluate(() => KZ_DECK.fx.transition);
check("连续快速翻页不重复整页光波", rapid.wave === false, rapid);
await page.keyboard.press("ArrowLeft"); await page.keyboard.press("ArrowLeft");
await page.keyboard.press("ArrowLeft"); await page.waitForTimeout(400);
check("翻页无脚本错误", (await page.evaluate(() => window.__errs)).length === 0, await page.evaluate(() => window.__errs));

// 3. QC freeze is deterministic: same ?kzf-t frame twice gives the same field pixels
const sample = async () => { await page.goto("about:blank"); await page.goto(URL + "?kzf-t=6#/6"); await ready(); await page.waitForTimeout(300);
  return page.evaluate(() => { const c = document.querySelector("canvas.kzf-field"), gl = c.getContext("webgl2"), px = new Uint8Array(4 * 16); const out = [];
    for (const [x, y] of [[0.1, 0.1], [0.5, 0.5], [0.9, 0.2], [0.8, 0.9]]) { gl.readPixels(Math.round(c.width * x), Math.round(c.height * (1 - y)), 2, 2, gl.RGBA, gl.UNSIGNED_BYTE, px); out.push([...px.slice(0, 3)]); } return out; }); };
const s1 = await sample(), s2 = await sample();
check("?kzf-t 定格可复现", JSON.stringify(s1) === JSON.stringify(s2), { s1, s2 });

// 4. content page stays calm inside the reading cards (frozen): field under the chart paper ≈ canvas colour
const calm = await page.evaluate(() => {
  const c = document.querySelector("canvas.kzf-field"), gl = c.getContext("webgl2"), r = document.querySelector(".deck > .slide.is-active .kzf-data").getBoundingClientRect();
  const px = new Uint8Array(4), k = c.width / innerWidth; let worst = 0;
  for (let i = 1; i < 6; i++) for (let j = 1; j < 6; j++) { const x = r.left + r.width * i / 6, y = r.top + r.height * j / 6; gl.readPixels(Math.round(x * k), Math.round(c.height - y * k), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); worst = Math.max(worst, 251 - Math.min(px[0], px[1], px[2] + 4)); }
  return worst; });
check("内容页纸卡背后的光场接近画布色（最大偏差 ≤ 24/255）", calm <= 24, calm);

// 5. reduced motion and upstream ?preview show the final state
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.goto("about:blank"); await page.goto(URL + "#/6"); await ready(); await page.waitForTimeout(800);
const rm = await page.evaluate(() => ({ running: document.getAnimations().filter(a => a.playState === "running" && a.effect?.target?.closest?.(".deck > .slide")).map(a => a.animationName || a.transitionProperty || "waapi"), hidden: [...document.querySelectorAll(".deck > .slide.is-active [data-kzf-in]")].filter(e => +getComputedStyle(e).opacity < 0.98).length }));
check("减少动态：无运行中的入场、内容直接可见", rm.running.length === 0 && rm.hidden === 0, rm);
await page.cdp("Emulation.setEmulatedMedia", { features: [] });
await page.goto("about:blank"); await page.goto(URL + "?preview=6#/6"); await page.waitForTimeout(1500);
const pv = await page.evaluate(() => ({ field: document.querySelector(".kzf-field")?.className, gl: !!document.querySelector("canvas.kzf-field") }));
check("?preview 不创建 WebGL，改用 CSS 光场", !pv.gl && /fallback/.test(pv.field || ""), pv);

// 6. review regressions: deep link boot, ?kzf-p from the previous page, reduced-motion page turns, print
await page.goto("about:blank"); await page.goto(URL + "#/6"); await ready(); await page.waitForTimeout(300);
const deep = await page.evaluate(() => ({ t: KZ_DECK.fx.transition, leaving: document.querySelectorAll(".deck > .slide.kzf-leaving").length }));
check("深链打开不播放转场、封面不残留", deep.t.from === 5 && deep.t.to === 5 && deep.leaving === 0, deep);
await page.goto("about:blank"); await page.goto(URL + "?kzf-p=0.5#/6"); await ready(); await page.waitForTimeout(300);
const mid = await page.evaluate(() => ({ t: KZ_DECK.fx.transition, leaving: [...document.querySelectorAll(".deck > .slide.kzf-leaving")].map(s => s.dataset.kzfKind) }));
check("?kzf-p 定格在从上一页过来的转场中途", mid.t.from === 4 && mid.t.to === 5 && mid.leaving.length === 1, mid);
await page.cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.goto("about:blank"); await page.goto(URL + "#/1"); await ready(); await page.waitForTimeout(300);
for (let i = 0; i < 5; i++) await page.keyboard.press("ArrowRight");
await page.waitForTimeout(150);
const rmTurn = await page.evaluate(() => {
  const s = [...document.querySelectorAll(".deck > .slide")], prev = s[4], c = document.querySelector("canvas.kzf-field"), glc = c.getContext("webgl2");
  const r = document.querySelector(".deck > .slide.is-active .kzf-data").getBoundingClientRect(), px = new Uint8Array(4), k = c.width / innerWidth; let worst = 0;
  for (let i = 1; i < 6; i++) for (let j = 1; j < 6; j++) { glc.readPixels(Math.round((r.left + r.width * i / 6) * k), Math.round(c.height - (r.top + r.height * j / 6) * k), 1, 1, glc.RGBA, glc.UNSIGNED_BYTE, px); worst = Math.max(worst, 251 - Math.min(px[0], px[1], px[2] + 4)); }
  return { prevVisible: getComputedStyle(prev).visibility, worst };
});
check("减少动态：翻页后光场重画为内容页、上一页立即隐藏", rmTurn.worst <= 24 && rmTurn.prevVisible === "hidden", rmTurn);
await page.cdp("Emulation.setEmulatedMedia", { media: "print", features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
await page.waitForTimeout(200);
const pr = await page.evaluate(() => ({ vis: [...document.querySelectorAll(".deck > .slide")].map(s => getComputedStyle(s).visibility[0]).join(""), id: getComputedStyle(document.querySelector(".kzf-identity")).display }));
check("打印（含减少动态）每页可见、身份胶囊保留", !pr.vis.includes("h") && pr.id !== "none", pr);
await page.cdp("Emulation.setEmulatedMedia", { media: "", features: [] });

await page.cdp("Emulation.clearDeviceMetricsOverride", {});
const failed = results.filter(r => !r.pass).length;
console.log(JSON.stringify({ page: URL, passed: results.length - failed, failed, results }, null, 1));
if (failed) process.exitCode = 1;
