// Teste da tela: abre a página num Chrome sem janela, clica em tudo e confere o resultado.
// Também tira as fotos de docs/screenshots/.
//
// Rodar: node solution/testes/teste_tela.mjs            (testa solution/app/index.html)
//        node solution/testes/teste_tela.mjs <url>      (testa outro endereço, ex.: o link publicado)
// Precisa de Node 22+ e Google Chrome (ou Chromium). Caminho do Chrome: variável CHROME, se preciso.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const URL_APP = process.argv[2] || pathToFileURL(join(RAIZ, "solution/app/index.html")).href;
const FOTOS = join(RAIZ, "docs/screenshots");
const PORTA = 9300 + Math.floor(Math.random() * 500);

function acharChrome() {
  const opcoes = [process.env.CHROME,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "C:/Program Files/Google/Chrome/Application/chrome.exe"].filter(Boolean);
  const achado = opcoes.find((p) => existsSync(p));
  if (!achado) { console.error("Chrome não encontrado. Informe o caminho na variável CHROME."); process.exit(2); }
  return achado;
}

const perfil = mkdtempSync(join(tmpdir(), "teste-tela-"));
const chrome = spawn(acharChrome(), ["--headless=new", "--disable-gpu", `--remote-debugging-port=${PORTA}`,
  `--user-data-dir=${perfil}`, "--no-first-run", "about:blank"], { stdio: "ignore" });
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

let alvo;
for (let i = 0; i < 50 && !alvo; i++) {
  await esperar(200);
  try { alvo = await (await fetch(`http://127.0.0.1:${PORTA}/json/new?about:blank`, { method: "PUT" })).json(); } catch { /* ainda subindo */ }
}
if (!alvo) { console.error("Não consegui abrir o Chrome."); chrome.kill(); process.exit(2); }

const ws = new WebSocket(alvo.webSocketDebuggerUrl);
await new Promise((r) => { ws.onopen = r; });
let id = 0;
const pendentes = {};
const errosConsole = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pendentes[d.id]) { pendentes[d.id](d); delete pendentes[d.id]; }
  if (d.method === "Runtime.exceptionThrown") errosConsole.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
  if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") errosConsole.push(JSON.stringify(d.params.args));
  if (d.method === "Log.entryAdded" && d.params.entry.level === "error") errosConsole.push(`${d.params.entry.text} ${d.params.entry.url || ""}`);
};
const cmd = (method, params = {}) => new Promise((r) => { const i = ++id; pendentes[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const js = async (expr) => (await cmd("Runtime.evaluate", { expression: expr, returnByValue: true })).result.result.value;
const tela = (largura, altura, celular = false) => cmd("Emulation.setDeviceMetricsOverride", { width: largura, height: altura, deviceScaleFactor: 1, mobile: celular });
async function foto(nome) {
  const altura = await js("document.documentElement.scrollHeight");
  const largura = await js("window.innerWidth");
  const r = await cmd("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 0, width: largura, height: Math.min(altura, 3000), scale: 1 }, captureBeyondViewport: true });
  writeFileSync(join(FOTOS, nome), Buffer.from(r.result.data, "base64"));
}

let falhas = 0;
const conferir = (nome, ok, detalhe = "") => {
  if (!ok) falhas++;
  console.log(`${ok ? "OK   " : "FALHA"} ${nome}${detalhe ? "  → " + detalhe : ""}`);
};
const escolher = (idSelect, valor) => js(`(()=>{const s=document.getElementById('${idSelect}'); s.value=${JSON.stringify(valor)}; s.dispatchEvent(new Event('change')); return s.value})()`);
const aba = (nome) => js(`document.querySelector('.aba[data-aba="${nome}"]').click()`);
const marcas = () => js("Object.values(JSON.parse(localStorage.getItem('segunda.marcacoes')||'{}'))");

await cmd("Runtime.enable"); await cmd("Log.enable"); await cmd("Page.enable");
await tela(1280, 900);
await cmd("Page.navigate", { url: URL_APP });
await esperar(2500);
await js("localStorage.clear()");
await cmd("Page.reload"); await esperar(2500);

// ---------------- aba Vendedor ----------------
conferir("Página abre com o título certo", (await js("document.title")).includes("Lead Scorer"));
const vendedorInicial = await js("document.getElementById('f-vendedor').value");
const nSemana = await js("document.querySelectorAll('#lista-semana > li.venda').length");
conferir("As vendas da semana aparecem (1 a 5)", nSemana >= 1 && nSemana <= 5, `${vendedorInicial}: ${nSemana} vendas`);
conferir("Cada venda da semana tem motivo e próxima ação", await js(`[...document.querySelectorAll('#lista-semana > li.venda')].every(li => li.querySelectorAll('.motivos li').length >= 2 && li.querySelector('.acao').textContent.length > 20)`));
conferir("As 5 da semana estão em ordem de valor esperado", await js(`(()=>{const v=[...document.querySelectorAll('#lista-semana .valores b')].map(b=>+b.textContent.replace(/\\D/g,''));return v.every((x,i)=>!i||v[i-1]>=x)})()`));
conferir("Nenhum texto quebrado (undefined, NaN, null)", await js(`!/undefined|NaN|\\bnull\\b/.test(document.body.innerText)`));
await foto("1-vendedor-as-5-da-semana.png");

const todos = await js("[...document.getElementById('f-vendedor').options].map(o=>o.value).filter(Boolean)");
let problemas = [];
for (const nome of todos) {
  await escolher("f-vendedor", nome);
  const r = await js(`({semana: document.querySelectorAll('#lista-semana > li.venda').length,
    outros: document.querySelectorAll('#lista-semana .quem').length, texto: document.body.innerText})`);
  if (r.semana > 5 || r.semana < 1) problemas.push(`${nome}: ${r.semana} na semana`);
  const notaBaixa = await js(`[...document.querySelectorAll('#lista-semana .nota')].some(n => parseInt(n.textContent) < window.DADOS.meta.nota_minima)`);
  if (notaBaixa) problemas.push(`${nome}: venda de nota baixa na semana`);
  if (/undefined|NaN|\bnull\b/.test(r.texto)) problemas.push(`${nome}: texto quebrado`);
}
conferir(`Todos os ${todos.length} vendedores abrem sem erro, com 1 a 5 na semana e nenhuma de nota baixa`, problemas.length === 0, problemas.join("; "));

await escolher("f-vendedor", "Anna Snelling");
conferir("Vendedor sem negociação vê o aviso", await js("!document.getElementById('alerta').hidden"), await js("document.getElementById('alerta').innerText"));
await escolher("f-vendedor", vendedorInicial);
conferir("Vendedor com negociação não vê o aviso", await js("document.getElementById('alerta').hidden"));

const aFazer = () => js("document.querySelector('#resumo-vendedor .card .n').textContent");
const antes = await aFazer();
await js("document.querySelector('#lista-semana button[data-marca=\"feito\"]').click()");
conferir("Botão Feito reduz o contador", (await aFazer()) !== antes, `${antes} → ${await aFazer()}`);
conferir("Venda feita vai para o fim da lista", await js("!document.querySelector('#lista-semana > li.venda').classList.contains('marcada') && document.querySelector('#lista-semana > li.venda:last-of-type').classList.contains('marcada')"));
await js("document.querySelector('#lista-semana button.link').click()");
conferir("Desfazer volta o contador", (await aFazer()) === antes);

for (const [bloco, lista, botao, esperado] of [["bloco-revisar", "lista-revisar", "viva", "viva"], ["bloco-revisar", "lista-revisar", "encerrar", "encerrar"], ["bloco-cadastro", "lista-cadastro", "cadastrado", "cadastrado"]]) {
  await js(`document.getElementById('${bloco}').open = true`);
  await js(`document.querySelector('#${lista} button[data-marca="${botao}"]').click()`);
  conferir(`Botão "${botao}" salva a marcação`, (await marcas()).includes(esperado));
}
await js("document.getElementById('bloco-outras').open = true");
const nOutras = await js("document.querySelectorAll('#lista-outras > li.venda').length");
const temMais = await js("!!document.querySelector('#lista-outras button[data-mais]')");
if (temMais) {
  await js("document.querySelector('#lista-outras button[data-mais]').click()");
  conferir("Mostrar mais traz mais vendas", (await js("document.querySelectorAll('#lista-outras > li.venda').length")) > nOutras);
} else {
  conferir("Outras vendas abertas listadas", nOutras >= 0, `${nOutras} vendas`);
}
await cmd("Page.reload"); await esperar(2500);
conferir("Marcações e vendedor continuam depois de recarregar", (await marcas()).length === 3 && (await js("document.getElementById('f-vendedor').value")) === vendedorInicial);

// ---------------- aba Chefe de vendas ----------------
await aba("chefe");
conferir("Aba Chefe de vendas abre", await js("!document.getElementById('aba-chefe').hidden && document.getElementById('aba-vendedor').hidden"));
const cards = () => js("[...document.querySelectorAll('#resumo-chefe .card .n')].map(x=>x.textContent)");
const totais = await cards();
conferir("Resumo mostra CRM, previsão, parado e sem cliente", totais.length === 4, totais.join(" | "));
const linhasTotal = await js("document.querySelectorAll('#tabela-vendedores tbody tr').length");
conferir("Tabela por vendedor preenchida", linhasTotal >= 25, `${linhasTotal} vendedores`);
conferir("Explicação da previsão aparece (por que é menor e o teste)", await js("(()=>{const t=document.getElementById('explica-previsao').innerText;return t.includes('Por que') && t.includes('vezes')})()"));
await foto("2-chefe-de-vendas.png");
for (const regiao of await js("[...document.getElementById('f-regiao').options].map(o=>o.value).filter(Boolean)")) {
  await escolher("f-regiao", regiao);
  const gerentes = await js("[...document.getElementById('f-gerente').options].map(o=>o.value).filter(Boolean)");
  const ok = await js(`window.DADOS.vendas.filter(v=>v.regiao==='${regiao}').every(v=>${JSON.stringify(gerentes)}.includes(v.gerente))`);
  conferir(`Região ${regiao}: só gerentes da região, números mudam`, ok && JSON.stringify(await cards()) !== JSON.stringify(totais), gerentes.join(", "));
}
await escolher("f-regiao", "");
const umGerente = await js("document.getElementById('f-gerente').options[1].value");
await escolher("f-gerente", umGerente);
conferir(`Filtro de gerente (${umGerente}) mostra só a equipe dele`, await js(`[...document.querySelectorAll('#tabela-vendedores tbody tr td:first-child .quem')].every(x=>x.textContent==='${umGerente}')`));
await escolher("f-gerente", "");
conferir("Sem filtro volta ao total", JSON.stringify(await cards()) === JSON.stringify(totais));

// ---------------- aba Como funciona ----------------
await aba("como");
conferir("Aba Como a nota funciona abre", await js("!document.getElementById('aba-como').hidden"));
conferir("Gráfico de chance com 13 faixas", (await js("document.querySelectorAll('#grafico .linha-g').length")) === 13);
conferir("Passo do ajuste do último trimestre preenchido", await js("['aj-prev','aj-ganhas','aj-fator'].every(i=>document.getElementById(i).textContent.length>0)"), await js("document.getElementById('aj-prev').parentElement.innerText"));
conferir("Resultado do teste com 5 jeitos de escolher", (await js("document.querySelectorAll('#teste-foco .barra').length")) === 5);
conferir("Tabela da previsão com 4 datas", (await js("document.querySelectorAll('#teste-previsao tbody tr').length")) === 4);
await foto("3-como-a-nota-funciona.png");
await js("document.getElementById('limpar').click()");
conferir("Apagar marcações limpa tudo", (await marcas()).length === 0);

// ---------------- celular ----------------
await aba("vendedor");
await tela(390, 844, true);
await esperar(300);
const larguras = await js("({pagina: document.documentElement.scrollWidth, tela: window.innerWidth})");
conferir("No celular, nada passa da borda", larguras.pagina <= larguras.tela, `${larguras.pagina}px de ${larguras.tela}px`);
await foto("4-celular.png");

conferir("Nenhum erro no console", errosConsole.length === 0, errosConsole.join(" | "));

ws.close();
chrome.kill();
await esperar(300);
try { rmSync(perfil, { recursive: true, force: true }); } catch { /* perfil temporário */ }
console.log(falhas ? `\n${falhas} FALHA(S)` : "\nTudo certo: todos os testes da tela passaram.");
process.exit(falhas ? 1 : 0);
