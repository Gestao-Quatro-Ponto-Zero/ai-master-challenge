// Teste ponta a ponta: abre a aplicação no Edge, usa como um vendedor e registra erros.
const puppeteer = require("puppeteer-core");
const path = require("path");

const URL = process.argv[2] || "http://localhost:8000/";
const SAIDA = path.join(__dirname, "capturas");
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";

(async () => {
  require("fs").mkdirSync(SAIDA, { recursive: true });
  const navegador = await puppeteer.connect({ browserURL: "http://127.0.0.1:9333" });
  const pagina = await navegador.newPage();
  await pagina.setViewport({ width: 1400, height: 900 });

  const erros = [];
  pagina.on("console", (m) => m.type() === "error" && erros.push("console: " + m.text()));
  pagina.on("pageerror", (e) => erros.push("pageerror: " + e.message));
  pagina.on("response", (r) => r.status() >= 400 && erros.push(`HTTP ${r.status()} ${r.url()}`));

  const passo = async (nome, fn) => {
    try { await fn(); console.log("OK   " + nome); }
    catch (e) { console.log("FALHA " + nome + ": " + e.message); erros.push(nome); }
  };
  const texto = (sel) => pagina.$eval(sel, (el) => el.innerText);

  await passo("abre a tela e carrega os cartões", async () => {
    await pagina.goto(URL, { waitUntil: "networkidle0" });
    await pagina.waitForSelector(".cartao-deal", { timeout: 15000 });
    const total = await texto(".cartao-resumo strong");
    if (total !== "2.089") throw new Error("total de abertos = " + total);
    await pagina.screenshot({ path: path.join(SAIDA, "1-quadro.png") });
  });

  await passo("cartão mostra o motivo principal", async () => {
    const motivo = await texto(".cartao-deal .motivo-cartao");
    if (!motivo.trim()) throw new Error("motivo vazio");
  });

  await passo("abre o detalhe e os pontos somam a nota", async () => {
    await pagina.click(".cartao-deal");
    await pagina.waitForSelector(".fator-total", { timeout: 10000 });
    const total = await texto(".fator-total strong"); // "35 + 26 + 30 = 91 pontos"
    const [conta, resultado] = total.replace(" pontos", "").split(" = ");
    const soma = conta.split(" + ").reduce((s, n) => s + Number(n), 0);
    if (soma !== Number(resultado)) throw new Error(total);
    if ((await pagina.$$(".motivos li")).length === 0) throw new Error("sem motivos");
    await pagina.screenshot({ path: path.join(SAIDA, "2-detalhe.png") });
    await pagina.keyboard.press("Escape");
    await pagina.waitForSelector(".painel", { hidden: true });
  });

  await passo("abre 'Como funciona a pontuação'", async () => {
    await pagina.click(".botao-ajuda");
    await pagina.waitForSelector(".regras-fator", { timeout: 10000 });
    await pagina.screenshot({ path: path.join(SAIDA, "3-como-funciona.png") });
    await pagina.click(".botao-fechar");
    await pagina.waitForSelector(".painel", { hidden: true });
  });

  await passo("filtra por vendedor", async () => {
    const vendedor = await pagina.$eval(".filtros select", (s) => s.options[1].value);
    await pagina.select(".filtros select", vendedor);
    await pagina.waitForFunction(
      (v) => [...document.querySelectorAll(".cartao-deal .linha-rodape span:first-child")].every((e) => e.innerText === v),
      { timeout: 10000 }, vendedor,
    );
    await pagina.waitForFunction(() => !document.querySelector("main.carregando"));
    await pagina.screenshot({ path: path.join(SAIDA, "4-filtro-vendedor.png") });
  });

  await passo("modo lista ordena por valor", async () => {
    await pagina.click(".botao-limpar");
    // Espera a lista completa voltar (2.089 negócios) antes de ordenar.
    await pagina.waitForFunction(() => document.querySelector(".cartao-resumo strong").innerText === "2.089");
    await pagina.click(".alternador button:last-child");
    await pagina.waitForSelector(".tabela tbody tr");
    const botoes = await pagina.$$(".cabecalho-ordenavel");
    await botoes[1].click(); // Valor
    const primeiroValor = await texto(".tabela tbody tr td:nth-child(8)");
    if (!primeiroValor.includes("26.768")) throw new Error("primeiro valor = " + primeiroValor);
    await pagina.screenshot({ path: path.join(SAIDA, "5-lista.png") });
  });

  await passo("tela de celular sem rolagem horizontal", async () => {
    await pagina.setViewport({ width: 390, height: 844 });
    await pagina.click(".alternador button:first-child");
    await pagina.waitForSelector(".cartao-deal");
    const largura = await pagina.evaluate(() => document.documentElement.scrollWidth);
    if (largura > 390) throw new Error("largura da página = " + largura);
    await pagina.screenshot({ path: path.join(SAIDA, "6-celular.png") });
  });

  await pagina.close(); navegador.disconnect();
  console.log(erros.length ? "\nERROS:\n" + erros.join("\n") : "\nSem erros no console nem respostas HTTP de erro.");
  process.exit(erros.length ? 1 : 0);
})();
