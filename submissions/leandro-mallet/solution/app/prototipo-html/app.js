/* Foco da Semana — lê o arquivo de deals pontuados e mostra onde focar.
 *
 * Fonte dos dados, em ordem:
 *   1. ?dados=<caminho> na URL (para testar outro arquivo)
 *   2. ../data/scored/deals_scored.json (score oficial)
 *   3. sample/deals_scored.sample.json (exemplo, mostra um aviso)
 *
 * Tudo roda no navegador: sem build, sem dependências.
 */
"use strict";

const FONTE_OFICIAL = "../data/scored/deals_scored.json";
const FONTE_EXEMPLO = "sample/deals_scored.sample.json";

const COMPONENTES = {
  chance: { nome: "Chance de fechar", cor: "--c-chance", texto: "Quanto deals parecidos (mesmo produto, perfil de cliente e vendedor) fecharam no passado." },
  valor: { nome: "Valor em jogo", cor: "--c-valor", texto: "Quanto este deal pode trazer, já descontada a chance de fechar." },
  tempo: { nome: "Tempo no pipeline", cor: "--c-tempo", texto: "Se o deal está dentro do prazo normal do produto ou está esfriando." },
  conta: { nome: "Histórico da conta", cor: "--c-conta", texto: "Como esta empresa já se comportou em negociações anteriores." },
};
const MARCADORES = {
  esfriando: "Esfriando",
  sem_conta: "Sem empresa",
  sem_data: "Sem 1º contato",
};
const ACOES = { focar: "Focar", requalificar: "Requalificar", desistir: "Desistir" };
const ESTAGIOS = { Prospecting: "Prospecção", Engaging: "Em negociação" };

const dinheiro = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const inteiro = new Intl.NumberFormat("pt-BR");

const app = {
  dados: null,
  deals: [],
  pesos: null,
  escala: "pontos", // "pontos" (componentes somam o score) ou "cem" (cada componente vai de 0 a 100)
  estado: { view: "dia", regiao: "", manager: "", vendedor: "" },
  todos: { busca: "", acao: "", ordem: "score", dir: -1, limite: 50 },
  equipes: [],
};

const $ = (sel, raiz = document) => raiz.querySelector(sel);
const conteudo = $("#conteudo");

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function dataBR(iso) {
  if (!iso) return "—";
  const [a, m, d] = String(iso).slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}
function deals(n) { return `${inteiro.format(n)} ${n === 1 ? "deal" : "deals"}`; }
function primeiroNome(nome) { return String(nome || "").split(" ")[0]; }
function guardar(chave, valor) { try { localStorage.setItem(chave, valor); } catch (_) { /* sem armazenamento */ } }
function ler(chave) { try { return localStorage.getItem(chave) || ""; } catch (_) { return ""; } }

/* ---------- Carregamento ---------- */

async function buscarJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) { const e = new Error(`HTTP ${r.status}`); e.status = r.status; throw e; }
  return r.json();
}

async function carregar() {
  const pedido = new URLSearchParams(location.search).get("dados");
  if (location.protocol === "file:") return mostrarErroArquivo();
  try {
    if (pedido) return iniciar(await buscarJSON(pedido), pedido);
    try {
      return iniciar(await buscarJSON(FONTE_OFICIAL), FONTE_OFICIAL);
    } catch (e) {
      if (e.status !== 404 && !(e instanceof SyntaxError)) throw e;
      return iniciar(await buscarJSON(FONTE_EXEMPLO), FONTE_EXEMPLO);
    }
  } catch (e) {
    mostrarErro(
      "Não foi possível ler o arquivo de deals",
      `O arquivo <code>${esc(pedido || FONTE_OFICIAL)}</code> não abriu (${esc(e.message)}). Confira se ele existe e se o servidor foi iniciado na pasta <code>solution/</code>.`
    );
  }
}

function validar(json) {
  if (!json || !Array.isArray(json.deals)) throw new Error("o arquivo não tem a lista \"deals\"");
  return json.deals.filter((d) => d && d.opportunity_id && d.sales_agent);
}

function iniciar(json, origem) {
  let deals;
  try { deals = validar(json); } catch (e) {
    return mostrarErro("O arquivo de deals está num formato inesperado", `${esc(e.message)}. Veja o formato em <code>COMO-RODAR.md</code>.`);
  }
  app.dados = json;
  app.deals = deals.map((d) => ({ ...d, score: Number(d.score) || 0, expected_value: Number(d.expected_value) || 0, flags: d.flags || [], reasons: d.reasons || [], components: d.components || {} }));
  app.pesos = json.component_weights || null;
  app.escala = detectarEscala(app.deals);

  const equipes = new Map();
  for (const d of app.deals) {
    const k = d.sales_agent;
    if (!equipes.has(k)) equipes.set(k, { vendedor: k, manager: d.manager || "Sem manager", regiao: d.regional_office || "Sem região" });
  }
  app.equipes = [...equipes.values()].sort((a, b) => a.vendedor.localeCompare(b.vendedor));

  $("#ref-data").textContent = json.reference_date ? `Pipeline em ${dataBR(json.reference_date)}` : "";
  const aviso = $("#aviso");
  if (json.is_sample || origem === FONTE_EXEMPLO) {
    aviso.hidden = false;
    aviso.textContent = "Dados de exemplo: os deals são reais, mas o score ainda é provisório. A tela passa a usar o score oficial assim que o arquivo data/scored/deals_scored.json existir.";
  }

  lerHash();
  if (!app.estado.vendedor && app.estado.view === "dia") app.estado.vendedor = ler("foco.vendedor");
  if (app.estado.vendedor && !equipes.has(app.estado.vendedor)) app.estado.vendedor = "";
  ligarFiltros();
  render();
  window.addEventListener("hashchange", () => { lerHash(); render(); });
}

function detectarEscala(deals) {
  const amostra = deals.slice(0, 200);
  const somam = amostra.filter((d) => {
    const s = Object.values(d.components).reduce((a, v) => a + (Number(v) || 0), 0);
    return Math.abs(s - d.score) <= 2;
  }).length;
  return somam >= amostra.length * 0.9 ? "pontos" : "cem";
}

/* ---------- Estado na URL ---------- */

function lerHash() {
  const [view, qs] = location.hash.replace(/^#/, "").split("?");
  const p = new URLSearchParams(qs || "");
  app.estado.view = ["dia", "time", "todos"].includes(view) ? view : "dia";
  app.estado.regiao = p.get("regiao") || "";
  app.estado.manager = p.get("manager") || "";
  app.estado.vendedor = p.get("vendedor") || "";
}

function escreverHash() {
  const p = new URLSearchParams();
  for (const k of ["regiao", "manager", "vendedor"]) if (app.estado[k]) p.set(k, app.estado[k]);
  const qs = p.toString();
  const novo = `#${app.estado.view}${qs ? "?" + qs : ""}`;
  if (location.hash !== novo) history.replaceState(null, "", novo);
}

function irPara(view, mudancas = {}) {
  Object.assign(app.estado, { view }, mudancas);
  if (app.estado.vendedor) guardar("foco.vendedor", app.estado.vendedor);
  escreverHash();
  render();
  conteudo.focus({ preventScroll: true });
  window.scrollTo({ top: 0 });
}

/* ---------- Filtros ---------- */

function opcoes(select, valores, rotuloVazio, atual) {
  select.innerHTML = `<option value="">${rotuloVazio}</option>` + valores.map((v) => `<option${v === atual ? " selected" : ""}>${esc(v)}</option>`).join("");
}

function atualizarFiltros() {
  const { regiao, manager, vendedor } = app.estado;
  const regioes = [...new Set(app.equipes.map((e) => e.regiao))].sort();
  const managers = [...new Set(app.equipes.filter((e) => !regiao || e.regiao === regiao).map((e) => e.manager))].sort();
  const vendedores = app.equipes.filter((e) => (!regiao || e.regiao === regiao) && (!manager || e.manager === manager)).map((e) => e.vendedor);
  opcoes($("#f-regiao"), regioes, "Todas", regiao);
  opcoes($("#f-manager"), managers, "Todos", manager);
  opcoes($("#f-vendedor"), vendedores, app.estado.view === "dia" ? "Escolha seu nome" : "Todos", vendedor);
}

function ligarFiltros() {
  $("#f-regiao").addEventListener("change", (e) => irPara(app.estado.view, { regiao: e.target.value, manager: "", vendedor: "" }));
  $("#f-manager").addEventListener("change", (e) => {
    const m = e.target.value;
    const eq = app.equipes.find((x) => x.manager === m);
    irPara(app.estado.view, { manager: m, vendedor: "", regiao: m && eq ? eq.regiao : app.estado.regiao });
  });
  $("#f-vendedor").addEventListener("change", (e) => {
    const v = e.target.value;
    const eq = app.equipes.find((x) => x.vendedor === v);
    irPara(app.estado.view, v && eq ? { vendedor: v, manager: eq.manager, regiao: eq.regiao } : { vendedor: "" });
  });
  $("#filtros").addEventListener("submit", (e) => e.preventDefault());
}

function noEscopo(d) {
  const { regiao, manager, vendedor } = app.estado;
  return (!regiao || d.regional_office === regiao) && (!manager || d.manager === manager) && (!vendedor || d.sales_agent === vendedor);
}

/* ---------- Peças visuais ---------- */

function chavesComponentes() {
  const vistas = new Set();
  for (const d of app.deals.slice(0, 50)) Object.keys(d.components).forEach((k) => vistas.add(k));
  const conhecidas = Object.keys(COMPONENTES).filter((k) => vistas.has(k));
  return [...conhecidas, ...[...vistas].filter((k) => !COMPONENTES[k])];
}
function infoComp(k) {
  return COMPONENTES[k] || { nome: k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase()), cor: "--c-extra", texto: "" };
}
function maxComp(k) {
  if (app.pesos && app.pesos[k]) return Number(app.pesos[k]);
  return app.escala === "pontos" ? null : 100;
}

function barraScore(d) {
  const ks = chavesComponentes();
  let partes;
  if (app.escala === "pontos") {
    partes = ks.map((k) => ({ k, w: Math.max(0, Number(d.components[k]) || 0) }));
  } else {
    const n = ks.length || 1;
    partes = ks.map((k) => ({ k, w: Math.max(0, Number(d.components[k]) || 0) / n }));
  }
  const titulo = ks.map((k) => `${infoComp(k).nome}: ${d.components[k] ?? "—"}`).join(", ");
  return `<div class="barra" role="img" aria-label="Score ${d.score}. ${esc(titulo)}">${partes
    .map((p) => `<i style="width:${Math.min(100, p.w)}%;background:var(${infoComp(p.k).cor})"></i>`)
    .join("")}</div>`;
}

function legenda() {
  return `<div class="legenda" aria-hidden="true">${chavesComponentes()
    .map((k) => `<span><i style="background:var(${infoComp(k).cor})"></i>${esc(infoComp(k).nome)}</span>`)
    .join("")}</div>`;
}

function marcadores(d) {
  if (!d.flags.length) return "";
  return `<div class="marcas">${d.flags
    .map((f) => `<span class="marcador marcador-${esc(f)}">${esc(MARCADORES[f] || f.replace(/_/g, " "))}</span>`)
    .join("")}</div>`;
}
function selo(acao) {
  return acao ? `<span class="acao acao-${esc(acao)}">${esc(ACOES[acao] || acao)}</span>` : "";
}
function tituloDeal(d) { return `${esc(d.product)} ${d.account ? "para " + esc(d.account) : "(empresa não cadastrada)"}`; }
/* Motivo que explica a ação: prefere frases sobre tempo, empresa ou contato. */
function motivoDaAcao(d) { return d.reasons.find((r) => /dias|empresa|conta|contato|cliente/i.test(r)) || d.reasons[0]; }
function subDeal(d) {
  const partes = [ESTAGIOS[d.deal_stage] || d.deal_stage];
  if (d.days_in_pipeline != null) partes.push(`${d.days_in_pipeline} dias aberto`);
  else partes.push("sem data de 1º contato");
  if (d.sector) partes.push(`setor ${d.sector}`);
  return esc(partes.join(", "));
}

function estado(titulo, texto, extra = "", classe = "") {
  return `<div class="estado ${classe}"><h2>${titulo}</h2><p>${texto}</p>${extra}</div>`;
}

/* ---------- Tela: Meu dia ---------- */

function telaDia() {
  const v = app.estado.vendedor;
  if (!v) return telaEscolha();
  const meus = app.deals.filter((d) => d.sales_agent === v).sort((a, b) => b.score - a.score);
  const eq = app.equipes.find((e) => e.vendedor === v);
  if (!meus.length) {
    return estado(`${esc(v)} não tem deals abertos`, "Nenhuma oportunidade em prospecção ou negociação neste arquivo. Escolha outro nome no filtro Vendedor ou abra a visão do manager.",
      `<button class="botao" data-ir="time">Ver o time</button>`);
  }

  const foco = meus.filter((d) => d.action === "focar");
  const topo = (foco.length >= 5 ? foco : [...foco, ...meus.filter((d) => d.action === "requalificar")]).slice(0, 5);
  const idsTopo = new Set(topo.map((d) => d.opportunity_id));
  const requal = meus.filter((d) => d.action === "requalificar" && !idsTopo.has(d.opportunity_id)).sort((a, b) => b.expected_value - a.expected_value);
  const desist = meus.filter((d) => d.action === "desistir").sort((a, b) => (b.days_in_pipeline ?? 0) - (a.days_in_pipeline ?? 0));
  const esfriando = meus.filter((d) => d.flags.includes("esfriando")).length;
  const emJogo = meus.reduce((a, d) => a + d.expected_value, 0);

  return `
    <div class="saudacao">
      <div>
        <h1>Bom dia, ${esc(primeiroNome(v))}</h1>
        <p>${esc(v)}, time de ${esc(eq?.manager || "—")} (${esc(eq?.regiao || "—")}). Estes são os deals que mais valem o seu tempo hoje.</p>
      </div>
      <div class="numeros">
        <div class="numero"><b>${inteiro.format(meus.length)}</b><span>deals abertos</span></div>
        <div class="numero"><b>${dinheiro.format(emJogo)}</b><span>valor esperado</span></div>
        <div class="numero"><b>${inteiro.format(esfriando)}</b><span>esfriando</span></div>
      </div>
    </div>

    <section class="secao" aria-labelledby="t-foco">
      <div class="secao-titulo">
        <h2 id="t-foco">Seus 5 deals para hoje</h2>
        <p>Toque num deal para ver como o score foi calculado.</p>
      </div>
      ${legenda()}
      ${topo.length ? `<ol class="foco">${topo.map((d, i) => cartao(d, i + 1)).join("")}</ol>`
        : estado("Nenhum deal para focar agora", "Todos os seus deals pedem requalificação ou estão parados há muito tempo. Comece pela lista abaixo.")}
    </section>

    <section class="secao" aria-labelledby="t-limpar">
      <div class="secao-titulo">
        <h2 id="t-limpar">Requalificar ou desistir</h2>
        <p>Deals que estão tirando tempo do seu dia. Decida o próximo passo de cada um.</p>
      </div>
      <div class="colunas">
        ${painelMini("requalificar", "Requalificar", "Vale uma conversa para confirmar interesse, prazo e quem decide.", requal, motivoDaAcao)}
        ${painelMini("desistir", "Desistir", "Parados há muito tempo e com pouca chance. Encerre e libere a agenda.", desist, motivoDaAcao)}
      </div>
    </section>

    <section class="secao" aria-labelledby="t-resto">
      <div class="secao-titulo">
        <h2 id="t-resto">Todos os seus deals</h2>
        <p>${deals(meus.length)}, do maior score para o menor.</p>
      </div>
      <button class="botao-sec" data-ir="todos" data-vendedor="${esc(v)}">Abrir a lista completa</button>
    </section>`;
}

function cartao(d, pos) {
  return `<li><button class="deal" data-deal="${esc(d.opportunity_id)}" aria-label="Deal ${pos}: ${tituloDeal(d)}, score ${d.score}. Ver detalhes">
    <span class="deal-pos">${pos}</span>
    <span class="deal-score"><b>${d.score}</b>${barraScore(d)}<small>de 100</small></span>
    <span class="deal-meio">
      <span class="deal-titulo">${tituloDeal(d)}</span>
      <span class="deal-sub" style="display:block">${subDeal(d)}</span>
      <ul class="motivos">${d.reasons.slice(0, 3).map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
      ${marcadores(d)}
    </span>
    <span class="deal-dir">
      <span><span class="deal-valor">${dinheiro.format(d.expected_value)}</span><br><span class="deal-valor-rot">valor esperado</span></span>
      ${selo(d.action)}
    </span>
  </button></li>`;
}

function painelMini(acao, titulo, texto, lista, motivo) {
  const id = `mini-${acao}`;
  const aberto = app.abertos?.[id];
  const mostrar = aberto ? lista : lista.slice(0, 6);
  return `<div class="painel">
    <h3>${selo(acao)} ${inteiro.format(lista.length)} ${lista.length === 1 ? "deal" : "deals"}</h3>
    <p>${texto}</p>
    ${lista.length ? `<ul class="mini">${mostrar.map((d) => `<li><button data-deal="${esc(d.opportunity_id)}">
        <span class="mini-score">${d.score}</span>
        <span class="mini-titulo">${tituloDeal(d)}</span>
        <span class="mini-valor">${dinheiro.format(d.expected_value)}</span>
        <span class="mini-motivo">${esc(motivo(d) || "")}</span>
      </button></li>`).join("")}</ul>
      ${lista.length > 6 ? `<button class="botao-sec mais" data-expandir="${id}">${aberto ? "Mostrar menos" : `Mostrar os ${lista.length}`}</button>` : ""}`
      : `<p style="margin-top:12px">Nada aqui. Bom sinal.</p>`}
  </div>`;
}

function telaEscolha() {
  const grupos = new Map();
  for (const e of app.equipes.filter((x) => (!app.estado.regiao || x.regiao === app.estado.regiao) && (!app.estado.manager || x.manager === app.estado.manager))) {
    const k = `${e.manager} (${e.regiao})`;
    if (!grupos.has(k)) grupos.set(k, []);
    grupos.get(k).push(e.vendedor);
  }
  const contagem = {};
  for (const d of app.deals) contagem[d.sales_agent] = (contagem[d.sales_agent] || 0) + 1;
  return `
    <div class="saudacao"><div><h1>Quem é você?</h1><p>Escolha seu nome para ver os deals em que vale focar hoje.</p></div></div>
    <div class="escolha">${[...grupos.entries()].sort().map(([g, vs]) => `
      <div><h3>${esc(g)}</h3><ul>${vs.map((v) => `<li><button data-vendedor-escolha="${esc(v)}">${esc(v)} <span>${deals(contagem[v] || 0)}</span></button></li>`).join("")}</ul></div>`).join("")}
    </div>`;
}

/* ---------- Tela: Visão do manager ---------- */

function telaTime() {
  const deals = app.deals.filter(noEscopo);
  const escopo = app.estado.vendedor || app.estado.manager || app.estado.regiao || "Todos os times";
  if (!deals.length) {
    return estado("Nenhum deal aberto neste filtro", "Mude a região, o manager ou o vendedor no topo da tela.");
  }
  const porVend = new Map();
  for (const d of deals) {
    if (!porVend.has(d.sales_agent)) porVend.set(d.sales_agent, { vendedor: d.sales_agent, manager: d.manager, deals: 0, valor: 0, focar: 0, esfriando: 0, desistir: 0, soma: 0 });
    const v = porVend.get(d.sales_agent);
    v.deals++; v.valor += d.expected_value; v.soma += d.score;
    if (d.action === "focar") v.focar++;
    if (d.action === "desistir") v.desistir++;
    if (d.flags.includes("esfriando")) v.esfriando++;
  }
  const linhas = [...porVend.values()].sort((a, b) => b.valor - a.valor);
  const total = deals.reduce((a, d) => a + d.expected_value, 0);
  const esfr = deals.filter((d) => d.flags.includes("esfriando"));
  const esfrValor = esfr.reduce((a, d) => a + d.expected_value, 0);
  const salvar = esfr.filter((d) => d.action !== "desistir").sort((a, b) => b.expected_value - a.expected_value || b.score - a.score).slice(0, 12);
  const semVend = app.equipes.filter((e) => (!app.estado.regiao || e.regiao === app.estado.regiao) && (!app.estado.manager || e.manager === app.estado.manager) && !porVend.has(e.vendedor));

  return `
    <div class="saudacao">
      <div><h1>${esc(escopo)}</h1><p>Pipeline aberto do time, quem está com deals esfriando e onde a ajuda do manager rende mais.</p></div>
      <div class="numeros">
        <div class="numero"><b>${inteiro.format(deals.length)}</b><span>deals abertos</span></div>
        <div class="numero"><b>${dinheiro.format(total)}</b><span>valor esperado</span></div>
        <div class="numero"><b>${Math.round((esfr.length / deals.length) * 100)}%</b><span>esfriando (${dinheiro.format(esfrValor)})</span></div>
      </div>
    </div>

    <section class="secao" aria-labelledby="t-salvar">
      <div class="secao-titulo">
        <h2 id="t-salvar">Esfriando, mas ainda vale salvar</h2>
        <p>Os maiores valores entre os deals parados além do normal. Bons candidatos para uma conversa com o vendedor.</p>
      </div>
      ${salvar.length ? `<div class="tabela-wrap"><table>
        <thead><tr><th>Score</th><th>Deal</th><th>Vendedor</th><th class="num">Dias aberto</th><th class="num">Valor esperado</th><th>Ação</th></tr></thead>
        <tbody>${salvar.map((d) => `<tr data-deal="${esc(d.opportunity_id)}" tabindex="0">
          <td><span class="td-score">${d.score}${barraScore(d)}</span></td>
          <td>${tituloDeal(d)}</td><td>${esc(d.sales_agent)}</td>
          <td class="num">${d.days_in_pipeline ?? "—"}</td><td class="num">${dinheiro.format(d.expected_value)}</td><td>${selo(d.action)}</td></tr>`).join("")}</tbody>
      </table></div>` : `<p>Nenhum deal esfriando com chance de salvar neste filtro.</p>`}
    </section>

    <section class="secao" aria-labelledby="t-vend">
      <div class="secao-titulo">
        <h2 id="t-vend">Por vendedor</h2>
        <p>Toque num nome para abrir o dia daquele vendedor.</p>
      </div>
      <div class="tabela-wrap"><table>
        <thead><tr><th>Vendedor</th><th>Manager</th><th class="num">Deals</th><th class="num">Valor esperado</th><th class="num">Score médio</th><th class="num">Para focar</th><th class="num">Esfriando</th><th class="num">Desistir</th></tr></thead>
        <tbody>${linhas.map((l) => `<tr data-vendedor-escolha="${esc(l.vendedor)}" tabindex="0">
          <td><b>${esc(l.vendedor)}</b></td><td>${esc(l.manager || "—")}</td>
          <td class="num">${l.deals}</td><td class="num">${dinheiro.format(l.valor)}</td>
          <td class="num">${Math.round(l.soma / l.deals)}</td><td class="num">${l.focar}</td>
          <td class="num">${l.esfriando}</td><td class="num">${l.desistir}</td></tr>`).join("")}
        </tbody>
      </table></div>
      ${semVend.length ? `<p style="margin-top:10px;color:var(--tinta-2);font-size:13px">Sem deals abertos: ${semVend.map((e) => esc(e.vendedor)).join(", ")}.</p>` : ""}
    </section>`;
}

/* ---------- Tela: Todos os deals ---------- */

function telaTodos() {
  const t = app.todos;
  const busca = t.busca.trim().toLowerCase();
  let lista = app.deals.filter(noEscopo).filter((d) => !t.acao || d.action === t.acao);
  if (busca) lista = lista.filter((d) => [d.opportunity_id, d.product, d.account, d.sales_agent, d.sector].some((x) => String(x || "").toLowerCase().includes(busca)));
  const chave = { score: (d) => d.score, valor: (d) => d.expected_value, dias: (d) => d.days_in_pipeline ?? -1, deal: (d) => tituloDeal(d), vendedor: (d) => d.sales_agent };
  const f = chave[t.ordem] || chave.score;
  lista.sort((a, b) => { const x = f(a), y = f(b); return (x > y ? 1 : x < y ? -1 : 0) * t.dir; });
  const col = (k, rotulo, num) => `<th class="${num ? "num" : ""}"${t.ordem === k ? ` aria-sort="${t.dir > 0 ? "ascending" : "descending"}"` : ""}><button data-ordem="${k}">${rotulo}${t.ordem === k ? (t.dir > 0 ? " ↑" : " ↓") : ""}</button></th>`;
  const mostrar = lista.slice(0, t.limite);

  return `
    <div class="saudacao"><div><h1>Todos os deals abertos</h1><p>${deals(lista.length)} no filtro atual.</p></div></div>
    <div class="barra-ferr">
      <input type="search" id="busca" placeholder="Buscar por produto, empresa, vendedor ou ID" value="${esc(t.busca)}" aria-label="Buscar">
      <select id="f-acao" aria-label="Ação">
        <option value="">Todas as ações</option>
        ${Object.entries(ACOES).map(([k, v]) => `<option value="${k}"${t.acao === k ? " selected" : ""}>${v}</option>`).join("")}
      </select>
    </div>
    ${lista.length ? `<div class="tabela-wrap"><table>
      <thead><tr>${col("score", "Score")}${col("deal", "Deal")}${col("vendedor", "Vendedor")}<th>Estágio</th>${col("dias", "Dias aberto", true)}${col("valor", "Valor esperado", true)}<th>Ação</th></tr></thead>
      <tbody>${mostrar.map((d) => `<tr data-deal="${esc(d.opportunity_id)}" tabindex="0">
        <td><span class="td-score">${d.score}${barraScore(d)}</span></td>
        <td>${tituloDeal(d)}</td><td>${esc(d.sales_agent)}</td><td>${esc(ESTAGIOS[d.deal_stage] || d.deal_stage)}</td>
        <td class="num">${d.days_in_pipeline ?? "—"}</td><td class="num">${dinheiro.format(d.expected_value)}</td><td>${selo(d.action)}</td></tr>`).join("")}
      </tbody></table></div>
      ${lista.length > t.limite ? `<button class="botao-sec mais" data-mais-linhas>Mostrar mais ${Math.min(50, lista.length - t.limite)}</button>` : ""}`
      : estado("Nenhum deal encontrado", "Nenhum deal combina com a busca e os filtros. Limpe a busca ou mude os filtros do topo.", `<button class="botao-sec" data-limpar>Limpar busca</button>`)}`;
}

/* ---------- Detalhe do deal ---------- */

function abrirDetalhe(id) {
  const d = app.deals.find((x) => x.opportunity_id === id);
  if (!d) return;
  const ks = chavesComponentes();
  const comp = ks.map((k) => {
    const v = Number(d.components[k]) || 0;
    const max = maxComp(k);
    const info = infoComp(k);
    const pct = max ? (v / max) * 100 : Math.min(100, v);
    return `<li>
      <div class="det-comp-linha"><span>${esc(info.nome)}</span><span>${max ? `${v} de ${max} pontos` : `${v} pontos`}</span></div>
      ${info.texto ? `<p>${esc(info.texto)}</p>` : ""}
      <div class="barra"><i style="width:${Math.max(0, Math.min(100, pct))}%;background:var(${info.cor})"></i></div>
    </li>`;
  }).join("");
  const somaPesos = app.pesos ? Object.values(app.pesos).reduce((a, b) => a + Number(b), 0) : null;
  const comoLer = app.escala === "pontos"
    ? `O score é a soma dos pontos abaixo${somaPesos ? ` (máximo ${somaPesos})` : ""}.`
    : "Cada parte vai de 0 a 100; o score combina as partes.";

  $("#detalhe-corpo").innerHTML = `<div class="det">
    <div class="det-topo">
      <div><h2 id="detalhe-titulo">${tituloDeal(d)}</h2><p>${subDeal(d)}</p></div>
      <button class="fechar" data-fechar aria-label="Fechar">×</button>
    </div>
    <div class="det-score"><b>${d.score}</b><div>${barraScore(d)}</div>${selo(d.action)}</div>
    <p style="color:var(--tinta-2);font-size:13px">${comoLer}</p>
    <h3>Por que este score</h3>
    <ul class="motivos">${d.reasons.map((r) => `<li>${esc(r)}</li>`).join("") || "<li>Sem motivos registrados.</li>"}</ul>
    ${marcadores(d)}
    <h3>Como o score foi montado</h3>
    <ul class="det-comp">${comp}</ul>
    <h3>Dados do deal</h3>
    <dl class="fatos">
      <dt>Valor esperado</dt><dd>${dinheiro.format(d.expected_value)}</dd>
      <dt>Estágio</dt><dd>${esc(ESTAGIOS[d.deal_stage] || d.deal_stage)}</dd>
      <dt>1º contato</dt><dd>${dataBR(d.engage_date)}</dd>
      <dt>Dias aberto</dt><dd>${d.days_in_pipeline ?? "—"}</dd>
      <dt>Empresa</dt><dd>${esc(d.account || "Não cadastrada")}</dd>
      <dt>Setor</dt><dd>${esc(d.sector || "—")}</dd>
      <dt>Vendedor</dt><dd>${esc(d.sales_agent)}</dd>
      <dt>Manager</dt><dd>${esc(d.manager || "—")}</dd>
      <dt>Região</dt><dd>${esc(d.regional_office || "—")}</dd>
      <dt>ID</dt><dd>${esc(d.opportunity_id)}</dd>
    </dl>
  </div>`;
  const dlg = $("#detalhe");
  if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
  $("[data-fechar]", dlg).focus();
}

/* ---------- Render e eventos ---------- */

function render() {
  if (!app.dados) return;
  const eq = app.estado.vendedor && app.equipes.find((x) => x.vendedor === app.estado.vendedor);
  if (eq) { app.estado.manager = eq.manager; app.estado.regiao = eq.regiao; }
  const eqM = !eq && app.estado.manager && app.equipes.find((x) => x.manager === app.estado.manager);
  if (eqM) app.estado.regiao = eqM.regiao;
  document.querySelectorAll(".aba").forEach((a) => { if (a.dataset.view === app.estado.view) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  atualizarFiltros();
  const telas = { dia: telaDia, time: telaTime, todos: telaTodos };
  conteudo.innerHTML = telas[app.estado.view]();
  const titulos = { dia: "Meu dia", time: "Visão do manager", todos: "Todos os deals" };
  document.title = `${titulos[app.estado.view]} · Foco da Semana`;
}

document.addEventListener("click", (e) => {
  const alvo = e.target.closest("[data-deal],[data-vendedor-escolha],[data-ir],[data-expandir],[data-ordem],[data-mais-linhas],[data-limpar],[data-fechar],.aba");
  if (!alvo) {
    const dlg = $("#detalhe");
    if (e.target === dlg) dlg.close();
    return;
  }
  if (alvo.matches(".aba")) { e.preventDefault(); return irPara(alvo.dataset.view); }
  if (alvo.dataset.fechar !== undefined) return $("#detalhe").close();
  if (alvo.dataset.deal) return abrirDetalhe(alvo.dataset.deal);
  if (alvo.dataset.vendedorEscolha) {
    const eq = app.equipes.find((x) => x.vendedor === alvo.dataset.vendedorEscolha);
    return irPara("dia", { vendedor: eq.vendedor, manager: eq.manager, regiao: eq.regiao });
  }
  if (alvo.dataset.ir) return irPara(alvo.dataset.ir, alvo.dataset.vendedor ? { vendedor: alvo.dataset.vendedor } : {});
  if (alvo.dataset.expandir) {
    app.abertos = app.abertos || {};
    app.abertos[alvo.dataset.expandir] = !app.abertos[alvo.dataset.expandir];
    return render();
  }
  if (alvo.dataset.ordem) {
    const k = alvo.dataset.ordem;
    app.todos.dir = app.todos.ordem === k ? -app.todos.dir : (k === "deal" || k === "vendedor" ? 1 : -1);
    app.todos.ordem = k;
    return render();
  }
  if (alvo.dataset.maisLinhas !== undefined) { app.todos.limite += 50; return render(); }
  if (alvo.dataset.limpar !== undefined) { app.todos.busca = ""; app.todos.acao = ""; return render(); }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.matches("tr[data-deal],tr[data-vendedor-escolha]")) e.target.click();
});

let esperaBusca;
document.addEventListener("input", (e) => {
  if (e.target.id === "busca") {
    clearTimeout(esperaBusca);
    esperaBusca = setTimeout(() => {
      app.todos.busca = e.target.value; app.todos.limite = 50; render();
      const b = $("#busca"); b.focus(); b.setSelectionRange(b.value.length, b.value.length);
    }, 200);
  }
});
document.addEventListener("change", (e) => {
  if (e.target.id === "f-acao") { app.todos.acao = e.target.value; app.todos.limite = 50; render(); }
});

/* ---------- Erros ---------- */

function mostrarErro(titulo, texto) {
  conteudo.innerHTML = estado(esc(titulo), texto, `<button class="botao" onclick="location.reload()">Tentar de novo</button>`, "estado-erro");
}

function mostrarErroArquivo() {
  conteudo.innerHTML = estado(
    "Abra pelo servidor local",
    "O navegador não deixa uma página aberta direto do disco ler o arquivo de deals. Na pasta <code>solution/</code>, rode <code>python -m http.server 8000</code> e abra <code>http://localhost:8000/app/</code>. Ou escolha o arquivo JSON aqui:",
    `<input type="file" id="arquivo" accept=".json,application/json" aria-label="Escolher arquivo de deals">`,
    "estado-erro"
  );
  $("#arquivo").addEventListener("change", async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try { iniciar(JSON.parse(await f.text()), f.name); }
    catch (err) { mostrarErro("O arquivo escolhido não é um JSON válido", esc(err.message)); }
  });
}

carregar();
