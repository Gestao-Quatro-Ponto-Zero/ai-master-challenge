// Grava a demo da ferramenta, um clipe por bloco do roteiro (video/roteiro.json).
// Rodar da pasta do app: node --env-file=.env --import tsx <este arquivo> [ids...]
import puppeteer from "<pasta_do_puppeteer>/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createSessionToken, SESSION_COOKIE } from "<app>/src/app/lib/session";
import { getUserByEmail, judgeEmailFromEnv } from "<app>/src/engine/appdb";

const V = "<pasta_do_video>";
const BASE = "http://127.0.0.1:3100";
const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));
const dur = JSON.parse(readFileSync(V + "/duracoes.json", "utf8")) as Record<string, number>;
const alvo = (id: string) => Object.entries(dur).filter(([k]) => k.startsWith(id + "_")).reduce((s, [, d]) => s + d + 0.3, 0) * 1000;
const marcasPath = V + "/marcas.json";
const marcas: Record<string, [number, number][]> = existsSync(marcasPath) ? JSON.parse(readFileSync(marcasPath, "utf8")) : {};

(async () => {
  const u = getUserByEmail(judgeEmailFromEnv())!;
  const tok = await createSessionToken({ id: u.id, email: u.email });
  const b = await puppeteer.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--hide-scrollbars"] });
  const p = await b.newPage();
  await p.setViewport({ width: 1440, height: 810, deviceScaleFactor: 4 / 3 });
  const errs: string[] = [];
  p.on("pageerror", (e) => errs.push(String(e)));

  // Cursor visível, sem o indicador do Next em modo dev, sem a animação de entrada.
  await p.evaluateOnNewDocument(`(function(){
    try { localStorage.setItem("ravenstack:chat-aberto", "0"); } catch (e) {}
    function montar() {
      var st = document.createElement("style");
      st.textContent = "nextjs-portal{display:none!important}*{animation-duration:0s!important;animation-delay:0s!important}"
        + "#__cur{position:fixed;left:720px;top:420px;width:22px;height:22px;z-index:2147483647;pointer-events:none;transition:left .55s cubic-bezier(.4,0,.2,1),top .55s cubic-bezier(.4,0,.2,1)}"
        + "#__cur.clic::after{content:'';position:absolute;left:-14px;top:-14px;width:28px;height:28px;border-radius:50%;border:2px solid #f2994a;animation:__r .45s ease-out forwards!important;animation-duration:.45s!important}"
        + "@keyframes __r{from{transform:scale(.3);opacity:1}to{transform:scale(1.4);opacity:0}}";
      document.head.appendChild(st);
      var c = document.createElement("div");
      c.id = "__cur";
      c.innerHTML = '<svg viewBox="0 0 22 22" width="22" height="22"><path d="M3 2 L3 18 L7.5 13.8 L10.5 20.5 L13.2 19.3 L10.3 12.8 L16.5 12.8 Z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>';
      document.body.appendChild(c);
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", montar); else montar();
  })();`);

  let cur: [number, number] = [720, 420];
  const mover = async (x: number, y: number) => {
    cur = [x, y];
    await p.evaluate((x, y) => { const c = document.getElementById("__cur"); if (c) { c.style.left = x + "px"; c.style.top = y + "px"; } }, x, y).catch(() => {});
    await p.mouse.move(x, y, { steps: 12 });
    await espera(600);
  };
  const clicarEm = async (x: number, y: number) => {
    await mover(x, y);
    await p.evaluate(() => { const c = document.getElementById("__cur"); if (c) { c.classList.remove("clic"); void c.offsetWidth; c.classList.add("clic"); } }).catch(() => {});
    await p.mouse.click(x, y);
  };
  const centro = async (fn: string, ...args: unknown[]) => {
    const r = (await p.evaluate(new Function("...a", `const el = (${fn})(...a); if (!el) return null; el.scrollIntoView({block:"nearest"}); const b = el.getBoundingClientRect(); return [b.left + b.width/2, b.top + b.height/2];`) as never, ...args)) as [number, number] | null;
    if (!r) throw new Error("não achei: " + fn.slice(0, 120) + " " + JSON.stringify(args));
    return r;
  };
  const clicar = async (fn: string, ...args: unknown[]) => { const [x, y] = await centro(fn, ...args); await clicarEm(x, y); };
  const ir = async (rota: string) => {
    await p.goto(BASE + rota, { waitUntil: "networkidle0" });
    await p.evaluate((x, y) => { const c = document.getElementById("__cur"); if (c) { c.style.transition = "none"; c.style.left = x + "px"; c.style.top = y + "px"; void c.offsetWidth; c.style.transition = ""; } }, cur[0], cur[1]);
    await espera(700);
  };
  const botaoTexto = (t: string, raiz = "document") => `() => [...${raiz}.querySelectorAll("button, a")].find((x) => x.textContent?.trim().startsWith(${JSON.stringify(t)}))`;
  const secao = (titulo: string) => `document.querySelector(${"`section`"}) && [...document.querySelectorAll("section")].find((s) => s.querySelector("h2")?.textContent?.startsWith(${JSON.stringify(titulo)}))`;

  // aquece as rotas (modo dev compila na primeira visita)
  await p.setCookie({ name: SESSION_COOKIE, value: tok, domain: "127.0.0.1", path: "/" });
  for (const r of ["/", "/tela/2", "/tela/3", "/marcados", "/telas"]) await p.goto(BASE + r, { waitUntil: "networkidle0" });
  await p.deleteCookie({ name: SESSION_COOKIE, domain: "127.0.0.1" });
  await p.goto(BASE + "/login", { waitUntil: "networkidle0" });

  const blocos: Record<string, (rel: () => number) => Promise<void>> = {
    s0: async () => {
      await ir("/login");
      await clicar(`() => document.querySelector("input[type=email], input[name=email], input")`);
      await p.keyboard.type("avaliador@ravenstack.app", { delay: 45 });
      await espera(500);
      await p.setCookie({ name: SESSION_COOKIE, value: tok, domain: "127.0.0.1", path: "/" });
    },
    s1: async () => {
      await ir("/");
      const sec = await centro(`() => ${secao("Crescimento")}`);
      await mover(sec[0] - 300, sec[1]);
      for (let i = 0; i <= 10; i++) await mover(sec[0] - 300 + i * 60, sec[1] + 10);
      const rec = await centro(`() => ${secao("Receita nova")}`);
      for (let i = 0; i <= 6; i++) await mover(rec[0] - 240 + i * 80, rec[1]);
    },
    s2: async () => {
      const [x, y] = await centro(`() => [...document.querySelectorAll("label")].find((l) => l.textContent?.trim().startsWith("Setor"))?.querySelector("select")`);
      await clicarEm(x, y);
      const sel = await p.evaluateHandle(() => [...document.querySelectorAll("label")].find((l) => l.textContent?.trim().startsWith("Setor"))!.querySelector("select")!);
      await (sel as unknown as { select: (v: string) => Promise<void> }).select("DevTools");
      await p.waitForNetworkIdle({ idleTime: 600 }).catch(() => {});
      await espera(1800);
      await clicar(`() => document.querySelector("button[title='Ver o SQL deste gráfico']")`);
      await espera(3500);
    },
    s3: async () => {
      await ir("/tela/2");
      await clicar(`() => { const s = ${secao("Churn por indústria")}; return s?.querySelectorAll(".cursor-pointer")[0]; }`);
      await espera(2500);
      const [dx, dy] = await centro(`() => document.querySelector("[role=dialog] .overflow-y-auto") || document.querySelector("[role=dialog]")`);
      await mover(dx, dy);
      for (let i = 0; i < 6; i++) { await p.mouse.wheel({ deltaY: 160 }); await espera(350); }
      await clicar(`() => document.querySelector("[role=dialog]")?.querySelectorAll("section .cursor-pointer")[0]`);
      await espera(2500);
    },
    s4: async () => {
      await p.keyboard.press("Escape");
      await ir("/tela/3");
      const s = await centro(`() => ${secao("Recursos: uso")}`);
      for (let i = 0; i <= 8; i++) await mover(s[0] - 260 + i * 65, s[1] - 40 + (i % 3) * 30);
    },
    s5: async (rel) => {
      await clicar(botaoTexto("Perguntar ao analista"));
      await espera(900);
      const antes = await p.evaluate(() => document.querySelectorAll("aside[aria-label=Analista] button[aria-pressed]").length);
      await clicar(`() => document.querySelector("aside[aria-label=Analista] input")`);
      await p.keyboard.type("Qual a taxa de churn por setor, pelo churn_flag da conta? Mostre num gráfico de barras.", { delay: 28 });
      await p.keyboard.press("Enter");
      const a = rel();
      await p.waitForFunction((n) => document.querySelectorAll("aside[aria-label=Analista] button[aria-pressed]").length > n, { timeout: 150000 }, antes);
      await espera(1500);
      marcas.s5 = [[a / 1000, rel() / 1000]];
      await p.evaluate(() => { const s = document.querySelector("aside[aria-label=Analista] .overflow-y-auto"); s?.scrollTo({ top: s.scrollHeight, behavior: "smooth" }); });
      await espera(2500);
    },
    s6: async () => {
      await clicar(`() => { const bs = [...document.querySelectorAll("aside[aria-label=Analista] button")].filter((x) => x.textContent === "Enviar para uma tela"); return bs[bs.length - 1]; }`);
      await espera(1200);
      await clicar(botaoTexto("+ Nova tela", `document.querySelector("aside[aria-label=Analista]")`));
      await p.waitForFunction(() => [...document.querySelectorAll("aside[aria-label=Analista] button")].some((x) => x.textContent?.trim().startsWith("Na tela")), { timeout: 30000 });
      await espera(1500);
      const nome = await p.evaluate(() => { const b = [...document.querySelectorAll("aside[aria-label=Analista] button")].filter((x) => x.textContent?.trim().startsWith("Na tela")).pop(); const m = b?.textContent?.match(/Na tela "(.*)"/); return m ? m[1] : ""; });
      await clicar(`(n) => [...document.querySelectorAll("aside:not([aria-label=Analista]) button, nav button")].filter((x) => x.textContent?.trim() === n).pop()`, nome);
      await p.waitForNetworkIdle({ idleTime: 600 }).catch(() => {});
      await espera(2500);
    },
    s7: async (rel) => {
      await clicar(`() => [...document.querySelectorAll("main button[aria-pressed], section button[aria-pressed]")].find((b) => b.getAttribute("aria-pressed") === "false")`);
      await espera(1200);
      await clicar(botaoTexto("Gráficos marcados"));
      await p.waitForNetworkIdle({ idleTime: 600 }).catch(() => {});
      await espera(1200);
      await clicar(`() => document.querySelector("textarea")`);
      await p.evaluate(() => { const t = document.querySelector("textarea") as HTMLTextAreaElement; const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")!.set!; set.call(t, ""); t.dispatchEvent(new Event("input", { bubbles: true })); });
      await p.keyboard.type("Diretoria da RavenStack; decidir onde agir primeiro para reduzir o churn", { delay: 22 });
      await clicar(`() => [...document.querySelectorAll("button")].find((x) => /^Montar/.test(x.textContent?.trim() ?? ""))`);
      const a = rel();
      await p.waitForFunction(() => document.body.innerText.includes("Montando"), { timeout: 15000 }).catch(() => {});
      await p.waitForFunction(() => !document.body.innerText.includes("Montando"), { timeout: 200000 });
      await espera(1500);
      marcas.s7 = [[a / 1000, rel() / 1000]];
      const [ix, iy] = await centro(`() => [...document.querySelectorAll("span")].find((s) => s.textContent?.trim() === "Ideia central")`);
      await mover(ix, iy);
      for (let i = 0; i < 5; i++) { await p.mouse.wheel({ deltaY: 200 }); await espera(450); }
      await clicar(`() => document.querySelector('a[href="/api/marcados/pptx"]')`).catch(() => {});
      await espera(1500);
    },
    s8: async () => {
      await p.setContent(`<!doctype html><html><head><style>
        body{margin:0;height:100vh;display:grid;place-items:center;background:#0f1218;color:#e8ebf1;font-family:"IBM Plex Sans",system-ui}
        .c{display:grid;gap:18px;text-align:center}.t{font-size:44px;font-weight:600}.u{font-size:26px;color:#f2994a}.n{font-size:18px;color:#9aa4b5}</style></head>
        <body><div class="c"><div class="t">RavenStack · diagnóstico de churn</div><div class="u">ravenstack-churn.vercel.app</div>
        <div class="n">Relatório, contas em risco e process log: submissions/ronaldo-tkotz no PR do G4</div></div></body></html>`, { waitUntil: "load" });
      await p.evaluate(() => { const c = document.createElement("div"); c.id = "__cur"; document.body.appendChild(c); });
    },
  };

  const ids = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(blocos);
  if (!ids.includes("s0")) await p.setCookie({ name: SESSION_COOKIE, value: tok, domain: "127.0.0.1", path: "/" });
  for (const id of ids) {
    const rec = await p.screencast({ path: `${V}/clip_${id}.webm` as `${string}.webm` });
    const t0 = Date.now();
    const rel = () => Date.now() - t0;
    try {
      await blocos[id](rel);
    } catch (e) {
      console.log("ERRO no bloco", id, String(e).slice(0, 300));
      await p.screenshot({ path: `${V}/erro_${id}.png` });
    }
    const falta = alvo(id) + 700 - rel();
    if (falta > 0) await espera(falta);
    await rec.stop();
    console.log(id, "gravado em", Math.round(rel() / 100) / 10, "s; narração", Math.round(alvo(id) / 100) / 10, "s");
  }
  writeFileSync(marcasPath, JSON.stringify(marcas, null, 1));
  console.log("erros da página:", errs.length ? errs.slice(0, 5) : "nenhum");
  await b.close();
})();
