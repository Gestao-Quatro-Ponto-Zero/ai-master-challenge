// Renderiza cada legenda como PNG transparente 1920x1080 (o ffmpeg daqui não tem libass/drawtext).
// Uso: bun legenda.ts <legendas.json> <pasta_saida>
import puppeteer from "<pasta_do_puppeteer>/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
import { readFileSync } from "node:fs";

const [, , arq, pasta] = process.argv;
const itens = JSON.parse(readFileSync(arq, "utf8")) as { n: number; texto: string }[];
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
(async () => {
  const b = await puppeteer.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true });
  const p = await b.newPage();
  await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  for (const it of itens) {
    await p.setContent(`<!doctype html><html><head><style>
      html,body{margin:0;width:1920px;height:1080px;background:transparent}
      .w{position:absolute;left:0;right:0;bottom:54px;display:flex;justify-content:center}
      .c{max-width:1480px;padding:14px 30px 16px;border-radius:10px;background:rgba(8,10,14,.86);color:#fff;
         font:500 36px/1.32 "Helvetica Neue",Helvetica,Arial,sans-serif;text-align:center;letter-spacing:.1px;
         box-shadow:0 6px 24px rgba(0,0,0,.35);text-wrap:balance}
    </style></head><body><div class="w"><div class="c">${esc(it.texto)}</div></div></body></html>`, { waitUntil: "load" });
    await p.screenshot({ path: `${pasta}/cap_${String(it.n).padStart(2, "0")}.png` as `${string}.png`, omitBackground: true });
  }
  await b.close();
  console.log(itens.length, "legendas");
})();
