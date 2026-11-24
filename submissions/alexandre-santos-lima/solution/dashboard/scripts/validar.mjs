// Valida o dashboard no navegador: as 3 páginas, desktop (claro e escuro) e celular (390 px).
// Falha (exit 1) se houver erro de console, rolagem horizontal no celular ou seção faltando.
// Uso: node scripts/validar.mjs <url> <pasta_prints>
import { chromium } from "playwright";
import { existsSync, mkdirSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const [URL = "http://localhost:4173/", OUT = "validacao"] = process.argv.slice(2);
mkdirSync(OUT, { recursive: true });

async function abrir() {
  try {
    return await chromium.launch();
  } catch (e) {
    // navegador da versão exata não instalado: usa qualquer headless shell já baixado
    const base = join(homedir(), ".cache", "ms-playwright");
    const dirs = existsSync(base) ? readdirSync(base).filter((d) => d.startsWith("chromium_headless_shell-")).sort().reverse() : [];
    for (const d of dirs) {
      const exe = join(base, d, "chrome-headless-shell-linux64", "chrome-headless-shell");
      if (existsSync(exe)) return chromium.launch({ executablePath: exe });
    }
    throw new Error("Nenhum Chromium encontrado. Rode: npx playwright install chromium-headless-shell");
  }
}

const PAGINAS = {
  "#/": ["resumo", "churn", "relacoes", "uso", "satisfacao", "definicoes", "correlacoes", "segmentos", "previsao"],
  "#/sugestoes": ["plano", "medir", "porque", "investigar", "reduzir"],
  "#/dados": ["auditoria", "mapa", "contas"],
};
const falhas = [];
const b = await abrir();
for (const [nome, vp, esquema] of [
  ["desktop-claro", { width: 1440, height: 900 }, "light"],
  ["desktop-escuro", { width: 1440, height: 900 }, "dark"],
  ["celular", { width: 390, height: 844 }, "light"],
]) {
  const ctx = await b.newContext({ viewport: vp, colorScheme: esquema, isMobile: nome === "celular", hasTouch: nome === "celular" });
  const p = await ctx.newPage();
  const erros = [];
  p.on("pageerror", (e) => erros.push(String(e)));
  p.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  for (const [hash, secoes] of Object.entries(PAGINAS)) {
    await p.goto(URL + hash, { waitUntil: "networkidle" });
    await p.waitForTimeout(300);
    for (const s of secoes) if (!(await p.locator(`#${s}`).count())) falhas.push(`${nome} ${hash}: seção #${s} não encontrada`);
    const sobra = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    if (sobra > 0) falhas.push(`${nome} ${hash}: rolagem horizontal de ${sobra}px`);
    const arq = `${nome}${hash.replace("#/", "-").replace(/-$/, "-diagnostico")}.png`;
    await p.screenshot({ path: join(OUT, arq), fullPage: true });
  }
  if (erros.length) falhas.push(`${nome}: erros no console: ${erros.slice(0, 3).join(" | ")}`);
  await ctx.close();
}
await b.close();
if (falhas.length) {
  console.error("VALIDAÇÃO FALHOU:\n- " + falhas.join("\n- "));
  process.exit(1);
}
console.log(`Validação ok: 3 páginas × 3 visões, sem erros. Prints em ${OUT}/ (abra e confira o layout).`);
