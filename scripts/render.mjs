/**
 * 版式渲染 + 四道构建护栏（fail-closed：任一断言不过就不出图）
 *
 * 用法：node scripts/render.mjs [--only 01]
 * 产出：output/01-hero.png 等，2480×3508，300dpi
 */
import { chromium } from "playwright";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = 2480, H = 3508, SAFE = 120;

const SHEETS = [
  { id: "01", file: "01-hero.html", out: "01-hero.png" },
  { id: "02", file: "02-craft.html", out: "02-craft.png" },
  { id: "03", file: "03-future.html", out: "03-future.png" },
  { id: "B", file: "99-varB.html", out: "../proof/gate-d/varB.png" },
  { id: "C", file: "99-varC.html", out: "../proof/gate-d/varC.png" },
  { id: "D", file: "99-varD.html", out: "../proof/gate-d/varD.png" },
];

const onlyIdx = process.argv.indexOf("--only");
const only = onlyIdx > -1 ? process.argv[onlyIdx + 1] : null;
const targets = only ? SHEETS.filter((s) => s.id === only) : SHEETS;

/** 本机的 chromium 是既有版本（1248），playwright 包更新后会去找 1255。
 *  这里直接指到已装的 chrome.exe，避免每次都要下载一份新的浏览器。 */
function findChrome() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = path.join(process.env.LOCALAPPDATA || "", "ms-playwright");
  if (!fs.existsSync(base)) return undefined;
  for (const dir of fs.readdirSync(base)) {
    if (!dir.startsWith("chromium-")) continue;
    for (const rel of ["chrome-win64/chrome.exe", "chrome-win/chrome.exe"]) {
      const p = path.join(base, dir, rel);
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

const browser = await chromium.launch({ executablePath: findChrome() });
let failed = 0;

for (const sheet of targets) {
  const page = await browser.newPage({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
  });
  const url = pathToFileURL(path.join(ROOT, "src", sheet.file)).href;
  await page.goto(url, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(350);

  const report = await page.evaluate(
    ({ W, H, SAFE }) => {
      const bad = [];

      // 护栏 1：字体真的加载了（不然会静默回落到系统字体，字形全变）
      for (const fam of ["Noto Serif SC", "Noto Sans SC"]) {
        const ok = document.fonts.check(`300px "${fam}"`);
        if (!ok) bad.push({ rule: "font", msg: `字体未加载：${fam}` });
      }

      // 护栏 2：文字不溢出容器
      for (const el of document.querySelectorAll("[data-fit]")) {
        const oy = el.scrollHeight - el.clientHeight;
        const ox = el.scrollWidth - el.clientWidth;
        if (oy > 1 || ox > 1) {
          bad.push({
            rule: "overflow",
            msg: `溢出 ${ox}px×${oy}px：${el.textContent.trim().slice(0, 18)}`,
          });
        }
      }

      // 护栏 3：出血与安全区——所有标了 data-safe 的元素必须留在安全区内
      for (const el of document.querySelectorAll("[data-safe]")) {
        const r = el.getBoundingClientRect();
        if (r.left < SAFE - 0.5 || r.top < SAFE - 0.5 || r.right > W - SAFE + 0.5 || r.bottom > H - SAFE + 0.5) {
          bad.push({
            rule: "safe-area",
            msg: `出安全区：${el.textContent.trim().slice(0, 18)} [${Math.round(r.left)},${Math.round(r.top)},${Math.round(r.right)},${Math.round(r.bottom)}]`,
          });
        }
      }

      // 护栏 4：正文字号下限（<24px 在 A4 300dpi 上是 2.0mm，印不出也看不清）
      for (const el of document.querySelectorAll("body *")) {
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length);
        if (!hasText) continue;
        const fs = parseFloat(getComputedStyle(el).fontSize);
        if (fs < 24) bad.push({ rule: "font-size", msg: `${fs}px 太小：${el.textContent.trim().slice(0, 18)}` });
      }

      // 护栏 5：文字不许压到图片上（除非作者明确要压，那时不标 data-noimg）
      //   第一版就是没这道断言，"跟着房子走"被大图吃掉了半行。
      const clipRect = (el) => {
        let r = el.getBoundingClientRect();
        let p = el.parentElement;
        while (p) {
          const s = getComputedStyle(p);
          if (s.overflow !== "visible" || s.overflowX !== "visible" || s.overflowY !== "visible") {
            const pr = p.getBoundingClientRect();
            r = {
              left: Math.max(r.left, pr.left), top: Math.max(r.top, pr.top),
              right: Math.min(r.right, pr.right), bottom: Math.min(r.bottom, pr.bottom),
            };
          }
          p = p.parentElement;
        }
        return r;
      };
      const imgs = [...document.images].map((i) => clipRect(i));
      for (const el of document.querySelectorAll("[data-noimg]")) {
        const r = el.getBoundingClientRect();
        for (const ir of imgs) {
          const ox = Math.min(r.right, ir.right) - Math.max(r.left, ir.left);
          const oy = Math.min(r.bottom, ir.bottom) - Math.max(r.top, ir.top);
          if (ox > 1 && oy > 1) {
            bad.push({
              rule: "text-on-image",
              msg: `文字压图 ${Math.round(ox)}×${Math.round(oy)}px：${el.textContent.trim().slice(0, 18)}`,
            });
            break;
          }
        }
      }

      // 附：图片必须真的解码成功
      for (const img of document.images) {
        if (!img.complete || !img.naturalWidth) bad.push({ rule: "image", msg: `图片未加载：${img.getAttribute("src")}` });
      }

      // 附：画布尺寸
      if (document.documentElement.scrollWidth > W + 1) bad.push({ rule: "canvas", msg: "画布横向溢出" });

      return { bad };
    },
    { W, H, SAFE }
  );

  if (report.bad.length) {
    failed++;
    console.error(`\n✗ ${sheet.id} 断言失败 ${report.bad.length} 条`);
    for (const b of report.bad) console.error(`   [${b.rule}] ${b.msg}`);
    await page.close();
    continue;
  }

  fs.mkdirSync(path.join(ROOT, "output"), { recursive: true });
  const outPath = path.join(ROOT, "output", sheet.out);
  await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: W, height: H } });
  const kb = (fs.statSync(outPath).size / 1024).toFixed(0);
  console.log(`✓ ${sheet.id} 四项断言全过 → output/${sheet.out}  ${W}×${H}  ${kb} KB`);
  await page.close();
}

await browser.close();
if (failed) {
  console.error(`\n共 ${failed} 张未通过，已拒绝出图。`);
  process.exit(1);
}
