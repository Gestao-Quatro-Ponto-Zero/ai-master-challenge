"use strict";

const DATA = window.LEAD_DATA;
const SESSION_KEY = "leadscorer.sessao";
const LAST_KEY = "leadscorer.ultimo";
const THEME_KEY = "leadscorer.tema";
const VIEW_KEY = "leadscorer.visao";
const PAGE_SIZE = 50;
const KANBAN_LIMIT = 25; // cartões por coluna; o resto fica a uma busca ou à lista
const EVERYONE = "Toda a empresa";
const APP_NAME = "Case G4 · AI Master";
const LOGO = '<img class="logo light" src="assets/g4-logo.png" alt="G4" width="76" height="30"><img class="logo dark" src="assets/g4-logo-escuro.png" alt="G4" width="76" height="30">';

/* Ícones Phosphor (fonte local em vendor/phosphor). */
const icon = (name) => `<i class="ph ph-${name}" aria-hidden="true"></i>`;

/* O que cada lista de origem significa para o vendedor. */
const LISTS = {
  foco: { tarefa: "Ligar", nome: "Em negociação" },
  abordar: { tarefa: "Enviar primeiro contato", nome: "Primeiro contato" },
  reativar: { tarefa: "Reativar com condição especial", nome: "Reativação" },
  encerrar: { tarefa: "Encerrar no CRM", nome: "Encerrar" },
};
const CONTACT_EVENTS = ["nao_atendeu", "retornar", "enviou", "ganhou", "perdeu"];
const POSITIVE_EVENTS = ["respondeu", "retornar", "ganhou"];

/* Setores e países vêm em inglês no CRM. */
const SECTORS = {
  retail: "Varejo", technology: "Tecnologia", medical: "Saúde", marketing: "Marketing",
  finance: "Finanças", software: "Software", entertainment: "Entretenimento",
  telecommunications: "Telecom", services: "Serviços", employment: "Emprego",
};
const COUNTRIES = {
  "United States": "Estados Unidos", Kenya: "Quênia", Philipines: "Filipinas", Japan: "Japão",
  Italy: "Itália", Norway: "Noruega", Korea: "Coreia", Jordan: "Jordânia", Brazil: "Brasil",
  Germany: "Alemanha", Panama: "Panamá", Belgium: "Bélgica", Romania: "Romênia", Poland: "Polônia",
};

const DEAL_BY_ID = Object.fromEntries(DATA.deals.map((deal) => [deal.id, deal]));
const LIVE_COUNT = DATA.deals.filter((deal) => deal.lista === "foco").length;
const state = {
  session: Workflow.read(SESSION_KEY, null), // { papel: "vendedor" | "gerente", nome }
  entering: null, // perfil escolhido na etapa 1 da entrada; null = ainda na etapa 1
  buscaNome: "",
  page: "hoje",
  openId: null, // negociação aberta no pop-up
  form: { retorno: false, nota: "", pendente: null },
  situacao: "todas",
  busca: "",
  filtroVendedor: "",
  filtroRegiao: "",
  filtroManager: "",
  filtroProduto: "",
  filtroAcao: "",
  ordem: { coluna: null, sentido: -1 }, // null = ordem de prioridade
  pagina: 0,
  printing: false, // gerando PDF: a tabela mostra todas as linhas
  vendedorAberto: null, // detalhe de um vendedor, na visão de gestão
  serie: "receita", // medida do gráfico de histórico no painel
  visao: Workflow.read(VIEW_KEY, "lista") === "kanban" ? "kanban" : "lista", // como a pessoa prefere ver as negociações
};

/* ---------- utilidades ---------- */

const $ = (id) => document.getElementById(id);
const money = (n) => "$" + Math.round(n).toLocaleString("pt-BR");
const pct = (p) => Math.round(p * 100) + "%";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const isoBR = (iso) => iso.split("T")[0].split("-").reverse().join("/");
const dayBR = (date) => {
  const d = new Date(date);
  return Number.isNaN(d.getTime()) ? "data inválida" : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
};
/* Busca sem depender de acento, hífen ou maiúscula: "saude" acha "Saúde", "mei mei" acha "Mei-Mei". */
const fold = (text) => String(text).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/-/g, " ").toLowerCase();
/* Uma sessão guardada só vale se o perfil e o nome existirem nos dados. */
const validSession = (s) => !!s && typeof s === "object" && typeof s.nome === "string"
  && ((s.papel === "vendedor" && !!DATA.vendedores[s.nome])
    || (s.papel === "gerente" && (s.nome === EVERYONE || DATA.deals.some((deal) => deal.manager === s.nome))));
const lastSession = () => {
  const last = lastSession();
  return validSession(last) ? last : null;
};
/* Célula de CSV: aspas escapadas e texto que começa como fórmula neutralizado. */
const csvCell = (value) => {
  const text = String(value ?? "");
  return `"${(/^[=+\-@\t\r]/.test(text) ? `'${text}` : text).replace(/"/g, '""')}"`;
};
const unique = (list, key) => [...new Set(list.map((item) => item[key]))].sort();
const sectorName = (sector) => (sector ? SECTORS[sector] || sector : "Não informado");
const byValue = (a, b) => b.valorEsperado - a.valorEsperado || b.preco - a.preco || a.id.localeCompare(b.id);
const isSeller = () => state.session && state.session.papel === "vendedor";
const lastEvent = (item) => item.status.historico[item.status.historico.length - 1];
const emptyForm = () => ({ retorno: false, nota: "", pendente: null, desde: 0 });
const DOUBLE_CLICK_MS = 400; // um segundo clique dentro disso não confirma nada
const GOOD_SCORE = 70;

/* Há quantos dias foi o último registro de contato; null se nunca houve. */
function daysSinceContact(item) {
  const last = lastEvent(item);
  if (!last) return null;
  return Math.round((Workflow.addDays(Workflow.now(), 0) - Workflow.addDays(last.quando, 0)) / 86400000);
}

function contactLabel(item) {
  const days = daysSinceContact(item);
  if (days === null) return '<span class="never">Nunca</span>';
  return days === 0 ? "Hoje" : days === 1 ? "Ontem" : `Há ${days} dias`;
}

/* Boa oportunidade sem atenção: score alto na lista e nenhum contato registrado. */
const isNeglected = (item) => hasScore(item.deal) && item.deal.score >= GOOD_SCORE && item.status.fase === "fila";
const sumOf = (items, key) => items.reduce((total, item) => total + item.deal[key], 0);

/* Quem entrou só enxerga o que é seu: o vendedor, as próprias negociações;
   o gerente, as do time. Sem senha: é um protótipo. */
function visibleDeals() {
  const { papel, nome } = state.session;
  if (papel === "vendedor") return DATA.deals.filter((deal) => deal.vendedor === nome);
  if (nome === EVERYONE) return DATA.deals;
  return DATA.deals.filter((deal) => deal.manager === nome);
}

function workItems() {
  const history = Workflow.byDeal();
  return visibleDeals().map((deal) => ({ deal, status: Workflow.statusOf(deal, history[deal.id]) }));
}

function queueOf(items, lista) {
  const queue = items.filter((item) => item.deal.lista === lista && item.status.fase === "fila");
  if (lista === "reativar") return queue.sort((a, b) => b.deal.preco - a.deal.preco || a.deal.idade - b.deal.idade);
  if (lista === "encerrar") return queue.sort((a, b) => b.deal.idade - a.deal.idade);
  return queue.sort((a, b) => byValue(a.deal, b.deal));
}

/* ---------- textos de cada negociação ---------- */

const hasScore = (deal) => deal.lista === "foco";

/* A chance aparece em faixas. O ganho real de cada faixa vem do teste. */
const BANDS = { alta: "Alta", media: "Média", baixa: "Baixa" };
function bandRate(faixa) {
  const rate = DATA.backtest.faixas.find((row) => row.faixa === faixa).ganhos;
  return rate < 0.05 ? "menos de 1 em cada 10" : `cerca de ${Math.round(rate * 10)} em cada 10`;
}

/* O texto do botão da linha: o que o vendedor faz com ela. */
function verbOf({ status }) {
  if (status.fase === "concluida") return `${icon("eye")}Ver`;
  if (status.fase === "aguardando") return `${icon("chat-circle-dots")}Respondeu?`;
  if (status.modo === "ligar") return `${icon("phone")}Ligar`;
  if (status.modo === "mensagem") return `${icon("chat-text")}Ver mensagem`;
  return `${icon("archive")}Encerrar`;
}

/* Mensagem pronta: modelo fixo preenchido com dados reais, não IA. */
function messageOf(deal, status) {
  const first = deal.vendedor.split(" ")[0];
  if (status && status.confirmar) {
    return {
      texto: `Olá, [nome do contato]! Aqui é ${first}, da [nossa empresa]. Tentei falar com você algumas vezes sobre o ${deal.produto} e não consegui. Ainda faz sentido conversarmos? Se não for o momento, é só me avisar e eu encerro por aqui.`,
    };
  }
  if (deal.lista === "abordar") {
    return {
      texto: `Olá, [nome do contato]! Aqui é ${first}, da [nossa empresa]. Estou entrando em contato porque o ${deal.produto} pode fazer sentido para a ${deal.conta || "[empresa]"}. Consigo te mostrar em 15 minutos como funciona. Você tem um horário amanhã ou depois?`,
    };
  }
  return {
    texto: `Olá, [nome do contato]! Aqui é ${first}, da [nossa empresa]. Há cerca de ${Math.round(deal.idade / 30)} meses conversamos sobre o ${deal.produto} e a proposta ficou em aberto. Consegui uma condição especial para retomarmos: [descreva o bônus]. Ela vale até [data]. Faz sentido conversarmos esta semana?`,
  };
}

function callScript(deal) {
  const points = ["Saia da ligação com o próximo passo e uma data."];
  if (deal.lista === "foco") points.push(`A negociação tem ${deal.idade} dias. Pergunte o que falta para decidir.`);
  const account = deal.conta ? DATA.contas[deal.conta] : null;
  if (account && account.ganhos) {
    const mine = account.porVendedor[deal.vendedor];
    points.push(`A ${deal.conta} já comprou ${account.ganhos} vezes${mine && mine.ganhos ? `, ${mine.ganhos} com você` : ""}. Use isso na abertura.`);
  }
  return points;
}

/* ---------- tabela de negociações ---------- */

const PRODUCTS = unique(DATA.deals, "produto");
let lastTable = { rows: [], marker: null }; // o que a tabela atual mostra, para exportar
const SORTABLE = { valor: (d) => d.preco, score: (d) => d.score };

/* Quem é o cliente e o que ele faz. */
function companyCell(deal, showOwner) {
  const owner = showOwner ? `<small class="owner">${icon("user")}${esc(deal.vendedor)}</small>` : "";
  if (!deal.conta) return `<strong class="unknown">Empresa não informada</strong><small>Código ${esc(deal.id)}</small>${owner}`;
  const account = DATA.contas[deal.conta];
  return `<strong>${esc(deal.conta)}</strong><small>${esc(sectorName(account.setor))} · ${account.funcionarios.toLocaleString("pt-BR")} funcionários</small>${owner}`;
}

/* Em que pé a negociação está, em poucas palavras. */
function stageLine(item) {
  const { deal, status } = item;
  if (status.fase === "retorno" || status.fase === "esgotada") return esc(status.tarefa);
  if (status.fase === "aguardando") return `Aguardando resposta · volta ${dayBR(status.volta)}`;
  if (status.fase === "agendada") return `${esc(status.tarefa)} · ${dayBR(status.volta)}`;
  if (status.fase === "concluida") return `${esc(status.resultado)} em ${dayBR(lastEvent(item).quando)}`;
  if (deal.lista === "abordar") return "Ainda não iniciada";
  if (deal.lista === "foco") return `${deal.idade} dias em negociação${deal.fechaEsteMes ? " · pode fechar este mês" : ""}`;
  return `Parada há ${deal.idade} dias`;
}

function rowHtml(item, marker, options) {
  const { deal } = item;
  const id = esc(deal.id);
  const score = hasScore(deal)
    ? `<span class="score ${deal.score >= 70 ? "high" : deal.score >= 40 ? "mid" : "low"}">${deal.score}</span>`
    : '<span class="dash">–</span>';
  return `
    <div class="tr${options.first ? " first" : ""}">
      <span class="c-pos">${marker}</span>
      <button class="c-company" data-open="${id}">${options.first ? '<em class="next">Próxima</em>' : ""}${companyCell(deal, options.showOwner)}</button>
      <span class="c-product"><strong>${esc(deal.produto)}</strong><small>${stageLine(item)}</small></span>
      <span class="c-value">${money(deal.preco)}</span>
      <span class="c-contact">${contactLabel(item)}</span>
      <span class="c-score">${score}</span>
      <span class="c-action"><button class="btn${options.first ? " primary" : ""}" data-open="${id}">${verbOf(item)}</button></span>
    </div>`;
}

const viewToggle = () => `
  <div class="tabs view-toggle" role="group" aria-label="Visualização">
    <button data-visao="lista" aria-pressed="${state.visao === "lista"}" title="Ver em lista">${icon("list-bullets")}<span>Lista</span></button>
    <button data-visao="kanban" aria-pressed="${state.visao === "kanban"}" title="Ver em colunas">${icon("kanban")}<span>Kanban</span></button>
  </div>`;

const KANBAN_COLUMNS = [
  ["retorno", "Retornos de hoje"],
  ["foco", "Para ligar"],
  ["abordar", "Primeiro contato"],
  ["reativar", "Reativação"],
  ["aguardando", "Aguardando"],
  ["encerrar", "Encerrar"],
  ["concluida", "Concluídas"],
];

/* As mesmas negociações, na mesma ordem de prioridade, separadas por situação. */
function kanbanHtml(items, options) {
  lastTable = { rows: items, marker: options.marker };
  const first = options.highlightFirst ? items[0] : null;
  const card = (item) => {
    const { deal } = item;
    const score = hasScore(deal) ? `<span class="score" title="Score">${deal.score}</span>` : "";
    return `
      <button class="kcard${item === first ? " first" : ""}" data-open="${esc(deal.id)}">
        ${item === first ? '<em class="next">Próxima</em>' : ""}
        <span class="kcard-who">${companyCell(deal, options.showOwner)}</span>
        <span class="kcard-line"><strong>${esc(deal.produto)}</strong><strong>${money(deal.preco)}</strong></span>
        <small>${stageLine(item)}</small>
        <span class="kcard-foot"><span>${verbOf(item)}</span>${score}</span>
      </button>`;
  };
  const columns = KANBAN_COLUMNS
    .map(([id, label]) => ({ label, items: items.filter((item) => situacaoOf(item) === id) }))
    .filter((column) => column.items.length);
  return `
    <div class="kanban">
      ${columns.map((column) => `
        <section class="kcol">
          <header><h2>${column.label}</h2><em>${column.items.length.toLocaleString("pt-BR")}</em></header>
          <div class="kcol-body">
            ${column.items.slice(0, KANBAN_LIMIT).map(card).join("")}
            ${column.items.length > KANBAN_LIMIT ? `<p class="kcol-more">Mais ${(column.items.length - KANBAN_LIMIT).toLocaleString("pt-BR")} nesta coluna. Use a busca, os filtros ou a lista para ver todas.</p>` : ""}
          </div>
        </section>`).join("")}
    </div>`;
}

/* Tabela paginada. `items` chega na ordem de prioridade; clicar numa coluna reordena. */
function tableHtml(items, options = {}) {
  if (!items.length) {
    lastTable = { rows: [], marker: options.marker };
    return `<div class="empty">${options.empty || "Nenhuma negociação com esse filtro."}</div>`;
  }
  if (options.kanban && state.visao === "kanban" && !state.printing) return kanbanHtml(items, options);
  const { coluna, sentido } = state.ordem;
  const sorted = (list) => (coluna ? [...list].sort((a, b) => sentido * (SORTABLE[coluna](a.deal) - SORTABLE[coluna](b.deal))) : list);
  // `breakAt` divide a tabela em duas partes (em Hoje: prioridade e "se sobrar tempo"); a ordenação não mistura as duas.
  const cut = options.breakHtml ? options.breakAt : items.length;
  const rows = [...sorted(items.slice(0, cut)), ...sorted(items.slice(cut))];
  const pages = Math.ceil(rows.length / PAGE_SIZE);
  state.pagina = Math.min(state.pagina, pages - 1);
  const start = state.pagina * PAGE_SIZE;
  const head = (key, label) => `<button class="c-${key} sort${coluna === key ? " on" : ""}" data-sort="${key}">${label}${coluna === key ? (sentido < 0 ? " ↓" : " ↑") : ""}</button>`;
  lastTable = { rows, marker: options.marker };
  const shown = state.printing ? rows : rows.slice(start, start + PAGE_SIZE);
  const offset = state.printing ? 0 : start;
  const breakRow = Math.max(cut, offset); // numa página que já começa na segunda parte, o título abre a página
  const body = shown.map((item, i) => (offset + i === breakRow ? options.breakHtml : "") + rowHtml(item, options.marker ? options.marker(item) : offset + i + 1, {
    first: options.highlightFirst && !coluna && offset + i === 0,
    showOwner: options.showOwner,
  })).join("");
  return `
    <div class="table${options.compact ? " compact" : ""}">
      <div class="thead">
        <span class="c-pos">${options.firstColumn || "#"}</span><span class="c-company">Empresa</span><span class="c-product">Produto e situação</span>
        <button class="c-value sort${coluna === "valor" ? " on" : ""}" data-sort="valor">Valor${coluna === "valor" ? (sentido < 0 ? " ↓" : " ↑") : ""}</button><span class="c-contact">Último contato</span>${head("score", "Score")}<span class="c-action">O que fazer</span>
      </div>
      ${body}
    </div>
    <div class="pager">
      <span>${start + 1} a ${Math.min(start + PAGE_SIZE, rows.length)} de ${rows.length.toLocaleString("pt-BR")} negociações${coluna ? ` · <button class="link" data-sort="">voltar à ordem de prioridade</button>` : ""}</span>
      <button class="btn" data-act="prev"${state.pagina === 0 ? " disabled" : ""}>Anterior</button>
      <button class="btn" data-act="next"${state.pagina >= pages - 1 ? " disabled" : ""}>Próxima</button>
    </div>`;
}

/* Busca e filtros comuns a todas as tabelas. */
function applyFilters(items) {
  const search = fold(state.busca.trim());
  return items
    .filter((item) => !state.filtroProduto || item.deal.produto === state.filtroProduto)
    .filter((item) => !state.filtroVendedor || item.deal.vendedor === state.filtroVendedor)
    .filter((item) => !state.filtroRegiao || item.deal.regiao === state.filtroRegiao)
    .filter((item) => !state.filtroManager || item.deal.manager === state.filtroManager)
    .filter((item) => !search || [item.deal.conta, item.deal.produto, item.deal.id, sectorName(item.deal.setor)].some((v) => v && fold(v).includes(search)));
}

const optionHtml = (value, label, current) => `<option value="${esc(value)}"${value === current ? " selected" : ""}>${esc(label)}</option>`;

const exportButtons = (what) => `
  <div class="exports">
    <button class="btn" data-act="csv" data-what="${what}" title="Baixar como planilha">${icon("file-csv")}CSV</button>
    <button class="btn" data-act="pdf" title="Salvar como PDF">${icon("file-pdf")}PDF</button>
  </div>`;

/* Na fila do dia só a busca; filtros e exportação ficam na Carteira. */
const searchHtml = () => `
  <label class="search">${icon("magnifying-glass")}<input type="search" id="busca" placeholder="Buscar na fila" value="${esc(state.busca)}" aria-label="Buscar"></label>`;

function toolbarHtml(extra = "", view = "") {
  return `
    <div class="toolbar">
      <input type="search" id="busca" placeholder="Buscar empresa, setor, produto ou código" value="${esc(state.busca)}" aria-label="Buscar">
      ${extra}
      <select id="filtro-produto" aria-label="Produto">${optionHtml("", "Todos os produtos", state.filtroProduto)}${PRODUCTS.map((p) => optionHtml(p, p, state.filtroProduto)).join("")}</select>
      ${view}
      ${exportButtons("table")}
    </div>`;
}

function pageHead(title, sub) {
  const who = `${state.session.nome} · ${roleLabel(state.session)}`;
  const when = Workflow.now().toLocaleDateString("pt-BR");
  return `<header class="head"><p class="print-only">${APP_NAME} · ${esc(who)} · ${when}</p><h1>${title}</h1><p>${sub}</p></header>`;
}

/* ---------- pop-up da negociação ---------- */

/* O que acontece com a negociação se a ação for confirmada. */
function effectOf(status, tipo, extra) {
  const rules = Workflow.RULES;
  if (tipo === "nao_atendeu") {
    return status.ligacoes + 1 >= rules.maximoTentativas
      ? `Será a ${status.ligacoes + 1}ª ligação sem resposta. Em vez de ligar de novo, o próximo passo vira uma mensagem para confirmar o interesse.`
      : `A negociação volta para Hoje em ${dayBR(Workflow.addDays(Workflow.now(), rules.religarEmDias))}, para nova tentativa.`;
  }
  if (tipo === "retornar") {
    return Workflow.isToday(extra.retornoEm)
      ? "O retorno é para hoje: a negociação continua em Hoje, no topo da lista."
      : `A negociação vai para Aguardando e volta para Hoje em ${dayBR(extra.retornoEm)}.`;
  }
  if (tipo === "enviou") {
    const until = dayBR(Workflow.addDays(Workflow.now(), rules.esperarRespostaDias));
    return status.tentativas + 1 >= rules.maximoTentativas
      ? `A negociação vai para Aguardando. É a última tentativa: sem resposta até ${until}, ela sai da fila e vai para Encerrar.`
      : `A negociação vai para Aguardando. Sem resposta até ${until}, volta para Hoje.`;
  }
  if (tipo === "respondeu") return "A negociação volta para Hoje, para você ligar.";
  return "A negociação sai da sua lista.";
}

/* Toda ação passa por aqui antes de ser salva, para evitar clique errado. */
function confirmBox(item) {
  const { tipo, extra } = state.form.pendente;
  return `
    <div class="now confirm">
      <h3>Confirmar: ${esc(Workflow.EVENTS[tipo].toLowerCase().replace("crm", "CRM"))}?</h3>
      <p>${effectOf(item.status, tipo, extra)}</p>
      <label class="note">Anotação <span>(opcional)</span>
        <textarea id="nota" rows="2" placeholder="O que foi combinado, com quem falou...">${esc(state.form.nota)}</textarea>
      </label>
      <div class="choices"><button class="btn primary" data-act="confirm">Confirmar</button><button class="btn" data-act="cancel">Cancelar</button></div>
    </div>`;
}

/* A única coisa que o vendedor precisa fazer no pop-up. */
function actionBox(item) {
  const { deal, status } = item;
  const id = esc(deal.id);
  if (state.form.pendente && state.form.pendente.id === deal.id) return confirmBox(item);
  const button = (act, label, primary) => `<button class="btn big${primary ? " primary" : ""}" data-act="${act}" data-id="${id}">${label}</button>`;

  if (status.fase === "concluida") {
    return `<div class="now done"><h3>${esc(status.resultado)} em ${dayBR(lastEvent(item).quando)}</h3><p>Não há mais nada a fazer aqui.</p><button class="link" data-act="undo" data-id="${id}">Desfazer</button></div>`;
  }
  if (status.fase === "aguardando") {
    return `<div class="now"><h3>Aguardando o cliente responder</h3><p>${status.tentativas >= Workflow.RULES.maximoTentativas
      ? `Era a última tentativa: se ele não responder até ${dayBR(status.volta)}, esta negociação vai para Encerrar.`
      : `Se ele não responder até ${dayBR(status.volta)}, esta negociação volta sozinha para Hoje.`}</p><div class="choices">${button("respondeu", "O cliente respondeu", true)}</div></div>`;
  }
  if (status.modo === "encerrar") {
    return `<div class="now"><h3>Encerre esta negociação no CRM</h3><p>${status.fase === "esgotada" ? esc(status.tarefa) + "." : "Está parada há tempo demais para valer um contato."}</p><div class="choices">${button("encerrou", "Encerrei no CRM", true)}</div></div>`;
  }
  if (status.modo === "mensagem") {
    const message = messageOf(deal, status);
    return `
      <div class="now">
        <h3>Mensagem sugerida</h3>
        <p class="hint">A ferramenta não envia nada. Copie o texto, troque o que está entre colchetes e envie você mesmo, pelo seu canal. Depois marque aqui que enviou.</p>
        <div class="message-box">
          <p class="message" id="message">${esc(message.texto)}</p>
          <button class="btn" data-act="copy">Copiar texto</button>
        </div>
        ${deal.conta ? "" : '<p class="muted miss">O CRM não tem o cliente desta negociação. Preencha o cliente antes de enviar.</p>'}
        <div class="choices">${button("enviou", "Já enviei esta mensagem", true)}</div>
      </div>`;
  }
  if (state.form.retorno) {
    return `
      <div class="now">
        <h3>Quando retornar?</h3>
        <div class="choices">${button("ret:1", "Amanhã")}${button("ret:3", "Em 3 dias")}${button("ret:7", "Em 1 semana")}</div>
        <div class="choices"><input type="date" id="retorno-data" aria-label="Outra data"><button class="btn" data-act="ret:data" data-id="${id}">Usar esta data</button><button class="link" data-act="cancel">Voltar</button></div>
      </div>`;
  }
  return `
    <div class="now">
      <h3>Ligue e marque o que aconteceu</h3>
      ${deal.conta ? "" : `<p class="muted miss">O CRM não tem o cliente desta negociação. Localize-a no CRM pelo código ${id} antes de ligar.</p>`}
      <div class="choices">${button("nao_atendeu", "Não atendeu")}${button("combinar", "Combinei um retorno")}${button("ganhou", "Fechou")}${button("perdeu", "Sem interesse")}</div>
    </div>`;
}

function companyBlock(deal) {
  if (!deal.conta) {
    return `<section><h3>Empresa</h3><p class="muted">O CRM não tem o cliente desta negociação. Só há o produto${deal.inicio ? ", o vendedor e a data de início" : " e o vendedor"}.</p></section>`;
  }
  const account = DATA.contas[deal.conta];
  const billions = Math.round(account.receitaMilhoes / 100) / 10;
  const revenue = account.receitaMilhoes >= 1000
    ? `US$ ${billions.toLocaleString("pt-BR")} ${billions < 2 ? "bilhão" : "bilhões"}`
    : `US$ ${Math.round(account.receitaMilhoes).toLocaleString("pt-BR")} milhões`;
  const mine = account.porVendedor[deal.vendedor] || { ganhos: 0, perdidos: 0 };
  const products = Object.entries(account.produtos).map(([name, n]) => `${esc(name)} (${n})`).join(", ");
  const fact = (label, value) => `<div><dt>${label}</dt><dd>${value}</dd></div>`;
  return `
    <section>
      <h3>Empresa</h3>
      <dl class="facts">
        ${fact("Setor", esc(sectorName(account.setor)))}
        ${fact("Faturamento", `${revenue} por ano`)}
        ${fact("Funcionários", account.funcionarios.toLocaleString("pt-BR"))}
        ${fact("País", esc(COUNTRIES[account.pais] || account.pais))}
        ${account.grupo ? fact("Grupo", `Subsidiária de ${esc(account.grupo)}`) : ""}
        ${fact("Telefone e e-mail", "Não constam no CRM")}
      </dl>
    </section>
    <section>
      <h3>Histórico com a gente</h3>
      <dl class="facts">
        ${fact("Negociações encerradas", `${account.ganhos} ganhas, ${account.perdidos} perdidas`)}
        ${fact(isSeller() ? "Com você" : `Com ${esc(deal.vendedor.split(" ")[0])}`, mine.ganhos + mine.perdidos ? `${mine.ganhos} ganhas, ${mine.perdidos} perdidas` : "Nenhuma ainda")}
        ${fact("Já comprou", `${money(account.receitaTotal)} no total`)}
        ${fact("Última compra", account.ultimaCompra ? isoBR(account.ultimaCompra) : "Nunca comprou")}
        ${fact("Mais comprados", products || "–")}
        ${fact("Outras negociações abertas", account.abertas > 1 ? `${account.abertas - 1} com esta empresa` : "Nenhuma")}
      </dl>
    </section>`;
}

/* De onde vem o score: os dois fatores e a posição, sem precisar abrir detalhes. */
const LIVE_RANK = DATA.deals
  .filter((deal) => deal.lista === "foco")
  .sort(byValue)
  .map((deal) => deal.id);

function scoreBlock(deal) {
  const live = DATA.deals.filter((d) => d.lista === "foco");
  const cheaper = live.filter((d) => d.preco < deal.preco).length;
  const pricePct = Math.round((cheaper / live.length) * 100);
  const steps = { alta: 3, media: 2, baixa: 1 }[deal.faixa];
  const dots = [1, 2, 3].map((n) => `<i class="${n <= steps ? "on" : ""}"></i>`).join("");
  return `
    <div class="why">
      <h3>Por que o score é ${deal.score}</h3>
      <div class="factor">
        <span>Valor do produto</span>
        <div class="meter"><i style="width:${Math.max(pricePct, 4)}%"></i></div>
        <strong>${money(deal.preco)}</strong>
        <small>${pricePct ? `Mais caro que ${pricePct}% das negociações com chance` : "Entre os produtos mais baratos das negociações com chance"}</small>
      </div>
      <div class="factor">
        <span>Chance de fechar</span>
        <div class="dots">${dots}</div>
        <strong>${BANDS[deal.faixa]}</strong>
        <small>Pela idade (${deal.idade} dias) e pelo momento do trimestre. No teste, ${bandRate(deal.faixa)} negociações desta faixa foram ganhas${deal.fechaEsteMes ? ". Pode fechar este mês" : ""}</small>
      </div>
      <p class="muted">Score = valor × chance, comparado com as outras: esta é a ${LIVE_RANK.indexOf(deal.id) + 1}ª de ${LIVE_COUNT} negociações com chance na empresa. <button class="link" data-page="como">Ver a conta e o teste</button></p>
    </div>`;
}

/* Por que agora, em uma frase. */
function headlineOf(deal) {
  if (deal.lista === "foco") return `Chance <strong>${BANDS[deal.faixa].toLowerCase()}</strong> de fechar${deal.fechaEsteMes ? ", e pode fechar este mês" : ""}.`;
  if (deal.lista === "abordar") return "Ainda não iniciada. A chance é desconhecida até a primeira conversa.";
  if (deal.lista === "reativar") return "Pelo histórico não fecha mais sozinha, mas é recente: vale uma mensagem com condição especial.";
  return "Pelo histórico não fecha mais. Manter aberta só infla o pipeline.";
}

function sheetHtml(item) {
  const { deal, status } = item;
  const account = deal.conta ? DATA.contas[deal.conta] : null;
  const facts = [
    ["Produto", esc(deal.produto)],
    ["Valor", money(deal.preco)],
    ...(hasScore(deal)
      ? [["Chance", BANDS[deal.faixa]], ["Score", deal.score]]
      : deal.lista === "abordar"
        ? [["Situação", "Não iniciada"], ["Chance", "Desconhecida"]]
        : [["Parada há", `${deal.idade} dias`], ["Chance", "Nenhuma"]]),
  ];
  const previous = [...status.historico].reverse().find((e) => e.nota);
  const timeline = status.historico.length
    ? `<ul class="timeline">${status.historico.map((e) => `<li><span>${dayBR(e.quando)}</span><div>${esc(Workflow.EVENTS[e.tipo])}${e.retornoEm ? ` para ${dayBR(e.retornoEm)}` : ""}${e.nota ? `<em>${esc(e.nota)}</em>` : ""}</div></li>`).join("")}</ul>
       ${status.fase === "concluida" ? "" : `<button class="link" data-act="undo" data-id="${esc(deal.id)}">Desfazer o último registro</button>`}`
    : '<p class="muted">Nenhum contato registrado ainda.</p>';
  const script = status.modo === "ligar" && status.fase !== "concluida"
    ? `<section><h3>Roteiro da ligação</h3><ul>${callScript(deal).map((p) => `<li>${esc(p)}</li>`).join("")}</ul></section>`
    : "";
  return `
    <header class="sheet-head">
      <div>
        <h2>${deal.conta ? esc(deal.conta) : "Empresa não informada"}</h2>
        <p class="muted">${account
          ? `${esc(sectorName(account.setor))} · ${account.funcionarios.toLocaleString("pt-BR")} funcionários · ${esc(COUNTRIES[account.pais] || account.pais)}${account.ganhos ? ` · já comprou ${account.ganhos} vezes` : ""}`
          : `O CRM não tem o cliente desta negociação. Código ${esc(deal.id)}.`}${isSeller() ? "" : ` · ${esc(deal.vendedor)}`}</p>
      </div>
      <button class="close" data-act="close" aria-label="Fechar">${icon("x")}</button>
    </header>
    <div class="sheet-body">
      <div class="sheet-main">
        <dl class="meta">${facts.map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("")}</dl>
        ${previous ? `<p class="reminder"><strong>Sua anotação de ${dayBR(previous.quando)}:</strong> ${esc(previous.nota)}</p>` : ""}
        ${actionBox(item)}
        ${deal.lista === "foco" ? scoreBlock(deal) : `<p class="headline">${headlineOf(deal)}</p>`}
        <div class="details">
          ${script}
          <section><h3>O que já foi feito</h3>${timeline}</section>
        </div>
      </div>
      <aside class="sheet-side details">
        ${companyBlock(deal)}
      </aside>
    </div>`;
}

function renderSheet() {
  const sheet = $("sheet");
  if (!state.openId || !state.session) {
    if (sheet.open) sheet.close();
    return;
  }
  const deal = DEAL_BY_ID[state.openId];
  const scroll = sheet.querySelector(".sheet-body") ? sheet.querySelector(".sheet-body").scrollTop : 0;
  sheet.innerHTML = sheetHtml({ deal, status: Workflow.statusOf(deal, Workflow.byDeal()[deal.id]) });
  if (!sheet.open) sheet.showModal();
  else sheet.querySelector(".sheet-body").scrollTop = scroll;
}

/* ---------- páginas do vendedor ---------- */

/*
 * A fila de hoje tem duas partes.
 *   prioridade: retornos combinados e negociações com chance, na ordem preço x chance
 *               que o teste histórico validou. É a meta do dia.
 *   extra:      primeiro contato e reativação ("se sobrar tempo"). O histórico não
 *               consegue ordenar essas, então vêm antes as que têm empresa cadastrada:
 *               sem empresa, o vendedor ainda precisa descobrir no CRM quem é o cliente.
 * Um retorno é prioridade quando há conversa viva (data combinada, cliente respondeu,
 * nova ligação) ou quando a negociação tem chance. A segunda mensagem de uma
 * reativação que ficou sem resposta continua em "se sobrar tempo".
 */
const isPriority = ({ deal, status }) => (deal.lista === "foco"
  ? status.fase === "fila" || status.fase === "retorno"
  : status.fase === "retorno" && status.modo === "ligar");

function todayParts(items) {
  const returns = items.filter((item) => item.status.fase === "retorno").sort((a, b) => byValue(a.deal, b.deal));
  const extra = [...returns.filter((item) => !isPriority(item)), ...queueOf(items, "abordar"), ...queueOf(items, "reativar")];
  return {
    prioridade: [...returns.filter(isPriority), ...queueOf(items, "foco")],
    extra: [...extra.filter((item) => item.deal.conta), ...extra.filter((item) => !item.deal.conta)],
  };
}

/* A negociação estava na parte de prioridade antes dos registros de hoje? */
function wasPriority(item) {
  const history = item.status.historico.filter((event) => !Workflow.isToday(event.quando));
  return isPriority({ deal: item.deal, status: Workflow.statusOf(item.deal, history) });
}

/* Prioridades já trabalhadas hoje: saíram da fila por um registro feito hoje. */
const doneToday = (items) => items.filter((item) => lastEvent(item) && item.status.fase !== "retorno"
  && Workflow.isToday(lastEvent(item).quando) && wasPriority(item)).length;

const actionOf = (item) => (item.status.fase === "retorno" ? "retorno" : item.status.modo);

function hojeBody() {
  const items = workItems();
  const parts = todayParts(items);
  const shown = (list) => applyFilters(list).filter((item) => !state.filtroAcao || actionOf(item) === state.filtroAcao);
  const prioridade = shown(parts.prioridade);
  const extra = shown(parts.extra);
  // Sem nenhuma prioridade no dia, o bloco de baixo é o próprio trabalho do dia.
  const nothingElse = !parts.prioridade.length && !doneToday(items);
  const divider = `
    <div class="tr-break">
      <strong>${nothingElse ? "Para abrir conversa" : "Se sobrar tempo"}</strong>
      <span>Primeiro contato e reativação${nothingElse ? "" : ": não entram na meta do dia"}. As que têm empresa cadastrada vêm primeiro.</span>
    </div>`;
  return tableHtml([...prioridade, ...extra], {
    kanban: true, compact: true, highlightFirst: !state.filtroAcao && !state.busca,
    breakAt: prioridade.length, breakHtml: extra.length ? divider : "",
    empty: items.length ? "Nada para fazer com esse filtro." : "Você não tem nenhuma negociação aberta no CRM. Quando uma for criada no seu nome, ela aparece aqui.",
  });
}

function pageHoje() {
  const items = workItems();
  const { prioridade, extra } = todayParts(items);
  const queue = [...prioridade, ...extra];
  const count = (action) => queue.filter((item) => actionOf(item) === action).length;
  const done = doneToday(items);
  const waiting = items.filter((item) => item.status.fase === "aguardando" || item.status.fase === "agendada").length;
  const parked = queueOf(items, "encerrar").length + items.filter((item) => item.status.fase === "esgotada").length;
  const total = done + prioridade.length;
  const tab = (value, label, n) => `<button data-acao="${value}" aria-pressed="${state.filtroAcao === value}">${label}<em>${n}</em></button>`;
  const more = extra.length ? `<small>Mais ${extra.length.toLocaleString("pt-BR")} se sobrar tempo</small>` : "";
  const progress = total
    ? `<p><strong>${done} de ${total}</strong> ${total === 1 ? "prioridade feita" : "prioridades feitas"} hoje${more}</p>
        <div class="track"><i style="width:${(done / total) * 100}%"></i></div>`
    : `<p><strong>Nenhuma prioridade hoje</strong></p>
        <p class="day-note">${extra.length
          ? "Você não tem negociação com chance de fechar nem retorno combinado. O dia é para abrir conversa."
          : "Você não tem negociação com chance de fechar nem retorno combinado."}</p>`;
  return `
    ${pageHead("Hoje", total
      ? "Siga a ordem da lista: a linha 1 é a que mais vale o seu tempo agora."
      : "Sem negociação com chance de fechar, a ferramenta não tem como dizer qual vale mais. A lista segue o preço.")}
    <div class="daybar">
      <div class="day-progress">
        ${progress}
      </div>
      <button class="day-stat" data-page="aguardando"><strong>${waiting}</strong> aguardando o cliente</button>
    </div>
    <div class="bar">
      <div class="tabs">
        ${tab("", "Tudo", queue.length)}${tab("retorno", "Retornos", count("retorno"))}${tab("ligar", "Ligar", count("ligar"))}${tab("mensagem", "Mensagem", count("mensagem"))}
      </div>
      ${searchHtml()}
      ${viewToggle()}
    </div>
    <div id="table-body">${hojeBody()}</div>
    ${parked ? `<p class="aside">${parked} negociações sem chance de fechar ficaram fora desta lista. <button class="link" data-situacao="encerrar">Ver</button></p>` : ""}`;
}

function aguardandoBody() {
  const waiting = applyFilters(workItems())
    .filter((item) => item.status.fase === "aguardando" || item.status.fase === "agendada")
    .sort((a, b) => a.status.volta - b.status.volta);
  return tableHtml(waiting, {
    firstColumn: "Volta",
    marker: (item) => dayBR(item.status.volta),
    empty: state.busca || state.filtroProduto
      ? "Nenhuma negociação aguardando com esse filtro."
      : "Nada aguardando. Quando você enviar uma mensagem ou combinar um retorno, a negociação aparece aqui.",
  });
}

function pageAguardando() {
  return `
    ${pageHead("Aguardando", "Nada aqui depende de você agora. Cada negociação volta sozinha para Hoje na data da primeira coluna; se era a última tentativa, vai para Encerrar.")}
    ${toolbarHtml()}
    <div id="table-body">${aguardandoBody()}</div>`;
}

/* ---------- carteira (vendedor e gerente) ---------- */

const SITUACOES = [
  ["todas", "Todas as situações"],
  ["semcontato", "Prioritárias sem contato"],
  ["retorno", "Retornos de hoje"],
  ["foco", "Para ligar"],
  ["abordar", "Primeiro contato"],
  ["reativar", "Reativação"],
  ["aguardando", "Aguardando"],
  ["encerrar", "Encerrar"],
  ["concluida", "Concluídas"],
];

function situacaoOf({ deal, status }) {
  if (status.fase === "fila") return deal.lista;
  if (status.fase === "esgotada") return "encerrar";
  if (status.fase === "agendada") return "aguardando";
  return status.fase;
}

function carteiraBody() {
  const found = applyFilters(workItems())
    .filter((item) => state.situacao === "todas" || (state.situacao === "semcontato" ? isNeglected(item) : situacaoOf(item) === state.situacao))
    .sort((a, b) => byValue(a.deal, b.deal));
  return tableHtml(found, { kanban: true, showOwner: !isSeller() });
}

function pageCarteira() {
  const sellers = isSeller() ? "" : `<select id="filtro-vendedor" aria-label="Vendedor">${optionHtml("", "Todos os vendedores", state.filtroVendedor)}${[...new Set([...unique(visibleDeals(), "vendedor"), state.filtroVendedor].filter(Boolean))].sort().map((v) => optionHtml(v, v, state.filtroVendedor)).join("")}</select>`;
  const regions = state.session.nome === EVERYONE
    ? `<select id="filtro-regiao" aria-label="Região">${optionHtml("", "Todas as regiões", state.filtroRegiao)}${unique(DATA.deals, "regiao").map((r) => optionHtml(r, r, state.filtroRegiao)).join("")}</select>`
    : "";
  const managers = state.session.nome === EVERYONE
    ? `<select id="filtro-manager" aria-label="Time">${optionHtml("", "Todos os times", state.filtroManager)}${unique(DATA.deals, "manager").map((m) => optionHtml(m, `Time de ${m}`, state.filtroManager)).join("")}</select>`
    : "";
  const situations = `<select id="situacao" aria-label="Situação">${SITUACOES.map(([id, label]) => optionHtml(id, label, state.situacao)).join("")}</select>`;
  return `
    ${pageHead("Carteira", isSeller() ? "Todas as suas negociações abertas, da de maior valor esperado para a menor." : "Todas as negociações abertas do time, da de maior valor esperado para a menor.")}
    ${toolbarHtml(situations + managers + sellers + regions, viewToggle())}
    <div id="table-body">${carteiraBody()}</div>`;
}

const TABLE_BODY = { hoje: hojeBody, aguardando: aguardandoBody, carteira: carteiraBody };

/* ---------- time (gerente) ---------- */

let lastTeam = []; // linhas da tabela de vendedores, para exportar

/* Vendedores que o perfil atual enxerga, inclusive os que não têm negociação aberta. */
function scopeSellers() {
  const { nome } = state.session;
  return Object.entries(DATA.vendedores)
    .filter(([, seller]) => (nome === EVERYONE || seller.manager === nome) && (!state.filtroRegiao || seller.regiao === state.filtroRegiao))
    .map(([name]) => name);
}

const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const monthLabel = (month) => `${MONTHS[Number(month.slice(5)) - 1]}/${month.slice(2, 4)}`;
const HISTORY_FROM = "2017-03"; // a base só registra fechamentos a partir de março de 2017

/* Soma mensal de um campo do histórico (receita, ganhos, perdidos, iniciadas) para um grupo de vendedores. */
function monthlySeries(sellers, field) {
  const wanted = new Set(sellers);
  const months = [...new Set(DATA.historicoMensal.map((row) => row.mes))].filter((month) => month >= HISTORY_FROM).sort();
  return months.map((month) => ({
    month,
    label: monthLabel(month),
    value: DATA.historicoMensal.filter((row) => row.mes === month && wanted.has(row.vendedor)).reduce((sum, row) => sum + row[field], 0),
  }));
}

function moneyShort(value) {
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1).replace(".", ",")} mi`;
  if (value >= 1e4) return `$${Math.round(value / 1e3)} mil`;
  return money(value);
}

/* Quantas negociações abertas há em cada situação. */
function pipelineOf(items) {
  const open = items.filter((item) => item.status.fase !== "concluida");
  const count = (lista) => open.filter((item) => item.deal.lista === lista).length;
  return { comChance: count("foco"), naoIniciadas: count("abordar"), reativar: count("reativar"), semChance: count("encerrar"), abertas: open.length };
}

const PIPELINE_SERIES = [
  { key: "comChance", label: "Com chance de fechar", tone: 1 },
  { key: "naoIniciadas", label: "Não iniciadas", tone: 3 },
  { key: "reativar", label: "Para reativar", tone: 2 },
  { key: "semChance", label: "Para encerrar", tone: "n" },
];

const tile = (value, label, note = "") => `<div class="tile"><span>${label}</span><strong>${value}</strong><small>${note}</small></div>`;
const blockHead = (title, sub) => `<header class="block-head"><h2>${title}</h2><p>${sub}</p></header>`;
const serieButton = (id, label) => `<button data-serie="${id}" aria-pressed="${state.serie === id}">${label}</button>`;
const chartCard = (title, takeaway, chart, tools = "") => `
  <section class="panel chart-card">
    <header><h2>${title}</h2><div class="chart-tools">${tools}<button class="chart-toggle" data-chart-view aria-pressed="false" title="Trocar entre gráfico e tabela">${icon("table")}Tabela</button></div></header>
    <p class="muted">${takeaway}</p>${chart}
  </section>`;
const quarterSum = (series, months) => series.filter((point) => months.includes(point.month.slice(5))).reduce((sum, point) => sum + point.value, 0);

function regionSelect() {
  if (state.session.nome !== EVERYONE) return "";
  return `<select id="filtro-regiao" aria-label="Região">${optionHtml("", "Todas as regiões", state.filtroRegiao)}${unique(DATA.deals, "regiao").map((r) => optionHtml(r, r, state.filtroRegiao)).join("")}</select>`;
}

function pagePainel() {
  const sellers = scopeSellers();
  const items = workItems().filter((item) => !state.filtroRegiao || item.deal.regiao === state.filtroRegiao);
  const pipeline = pipelineOf(items);
  const live = items.filter((item) => item.deal.lista === "foco" && item.status.fase !== "concluida");
  const dead = pipeline.reativar + pipeline.semChance;
  const revenue = monthlySeries(sellers, "receita");
  const started = monthlySeries(sellers, "iniciadas");
  const q3 = quarterSum(revenue, ["07", "08", "09"]);
  const q4 = quarterSum(revenue, ["10", "11", "12"]);
  const change = q3 ? Math.round((q4 / q3 - 1) * 100) : 0;
  const startedPeak = started.reduce((best, point) => (point.value > best.value ? point : best), started[0]);
  const startedLast = started[started.length - 1];

  const byTeam = state.session.nome === EVERYONE;
  const groups = unique(items.map((item) => item.deal), byTeam ? "manager" : "vendedor").map((name) => ({
    label: name,
    ...pipelineOf(items.filter((item) => item.deal[byTeam ? "manager" : "vendedor"] === name)),
  })).sort((a, b) => b.comChance - a.comChance || b.abertas - a.abertas);
  const bands = ["alta", "media", "baixa"].map((faixa) => ({ label: `Chance ${BANDS[faixa].toLowerCase()}`, value: live.filter((item) => item.deal.faixa === faixa).length }));

  const soon = live.filter((item) => item.deal.fechaEsteMes).length;

  // Atividade: o que os vendedores registraram na ferramenta.
  const isContact = (event) => CONTACT_EVENTS.includes(event.tipo);
  const contacted = items.filter((item) => item.status.historico.some(isContact));
  const weekAgo = Workflow.addDays(Workflow.now(), -7);
  const recent = items.reduce((sum, item) => sum + item.status.historico.filter((e) => isContact(e) && new Date(e.quando) >= weekAgo).length, 0);
  const priority = items.filter((item) => hasScore(item.deal) && item.deal.score >= GOOD_SCORE);
  const priorityDone = priority.filter((item) => item.status.historico.some(isContact)).length;
  const positive = contacted.filter((item) => item.status.historico.some((e) => POSITIVE_EVENTS.includes(e.tipo))).length;
  const active = new Set(contacted.map((item) => item.deal.vendedor)).size;
  const withDeals = new Set(items.map((item) => item.deal.vendedor)).size;

  const attention = sellers
    .map((name) => ({ name, count: items.filter((item) => item.deal.vendedor === name && isNeglected(item)).length }))
    .filter((row) => row.count)
    .sort((x, y) => y.count - x.count || x.name.localeCompare(y.name))
    .filter((row, index, all) => index < 5 || row.count === all[4].count); // empatados com o 5º também aparecem
  const history = state.serie === "iniciadas"
    ? { title: "Negociações iniciadas por mês", note: `O pico foi ${startedPeak.value.toLocaleString("pt-BR")} em ${startedPeak.label}; em ${startedLast.label} foram ${startedLast.value.toLocaleString("pt-BR")}.`, chart: Charts.columns(started, { format: (n) => n.toLocaleString("pt-BR"), name: "Negociações iniciadas" }) }
    : { title: "Receita ganha por mês", note: "Valor das negociações ganhas, pelo mês de fechamento.", chart: Charts.columns(revenue, { format: moneyShort, name: "Receita ganha" }) };

  return `
    <header class="head with-tools">
      <div><p class="print-only">${APP_NAME} · ${esc(state.session.nome)} · ${Workflow.now().toLocaleDateString("pt-BR")}</p><h1>Painel</h1><p>${byTeam ? "A empresa inteira" : `Time de ${esc(state.session.nome)}`}: como está o pipeline hoje e como veio o ano.</p></div>
      <div class="panel-tools">${regionSelect()}<button class="btn" data-act="pdf">${icon("file-pdf")}PDF</button></div>
    </header>
    <div class="tiles">
      ${tile(pipeline.comChance, "Com chance de fechar", `de ${pipeline.abertas.toLocaleString("pt-BR")} negociações abertas`)}
      ${tile(moneyShort(sumOf(live, "valorEsperado")), "Valor esperado das com chance", `preço × chance das ${pipeline.comChance} (${moneyShort(sumOf(live, "preco"))} a preço de tabela). Não é a previsão do trimestre: não inclui as não iniciadas nem o que ainda vai entrar`)}
      ${tile(pipeline.comChance + dead ? pct(dead / (pipeline.comChance + dead)) : "–", "Em andamento sem chance", `${dead.toLocaleString("pt-BR")} de ${(pipeline.comChance + dead).toLocaleString("pt-BR")} em andamento (fora as não iniciadas), para reativar ou encerrar`)}
      ${tile(moneyShort(q4), "Receita ganha no 4º trimestre", `${change >= 0 ? "+" : ""}${change}% contra o 3º trimestre (${moneyShort(q3)})`)}
    </div>
    ${blockHead("Pipeline hoje", "O que está aberto agora e em que situação.")}
    <div class="chart-grid main-side">
      ${chartCard(byTeam ? "Negociações abertas por time" : "Negociações abertas por vendedor", "Quem tem mais negociações com chance de fechar vem primeiro.", Charts.stacked(groups, PIPELINE_SERIES, { name: "Pipeline aberto", first: byTeam ? "Time" : "Vendedor" }))}
      ${chartCard(`As ${pipeline.comChance} com chance de fechar`, `Divididas pela faixa de chance. ${soon === 1 ? "1 pode" : `${soon} podem`} fechar este mês.`, Charts.bars(bands, { format: (n) => n.toLocaleString("pt-BR"), name: "Negociações", first: "Faixa" }))}
    </div>
    <section class="panel attention">
      <div><h2>Prioritárias sem contato</h2><p class="muted">Score ${GOOD_SCORE} ou mais e nenhum contato registrado. Quem tem mais vem primeiro.</p></div>
      ${attention.length ? `<ol class="rank">${attention.map((row) => `<li><button class="link" data-seller-detail="${esc(row.name)}">${esc(row.name)}</button><strong>${row.count}</strong></li>`).join("")}</ol>` : '<p class="muted">Nenhuma no momento.</p>'}
    </section>
    ${blockHead("Atividade do time", "Contatos que os vendedores registraram na ferramenta. Nesta versão, sem servidor, só aparecem os feitos neste navegador.")}
    <div class="tiles">
      ${tile(recent, "Contatos nos últimos 7 dias", "ligações, mensagens e fechamentos registrados")}
      ${tile(`${priorityDone} de ${priority.length}`, "Prioritárias já contatadas", `score ${GOOD_SCORE} ou mais`)}
      ${tile(contacted.length ? pct(positive / contacted.length) : "–", "Resposta positiva", contacted.length ? `${positive} de ${contacted.length} negociações contatadas` : "ainda sem contato registrado")}
      ${tile(`${active} de ${withDeals}`, "Vendedores usando", "dos que têm negociação aberta; registraram ao menos um contato")}
    </div>
    <p class="aside"><button class="btn" data-act="export">${icon("file-csv")}Baixar todos os registros de contato (CSV)</button> É a base para medir o piloto: cada ligação, mensagem, resposta e fechamento, com data.</p>
    ${blockHead("Como veio 2017", "De março a dezembro, o período que a base registra.")}
    <div class="chart-grid one">
      ${chartCard(history.title, history.note, history.chart, `<div class="tabs seg" role="group" aria-label="Medida">${serieButton("receita", "Receita ganha")}${serieButton("iniciadas", "Negociações iniciadas")}</div>`)}
    </div>`;
}

function pageVendedores() {
  const items = workItems().filter((item) => !state.filtroRegiao || item.deal.regiao === state.filtroRegiao);
  const wasContacted = (item) => item.status.historico.some((e) => CONTACT_EVENTS.includes(e.tipo));
  lastTeam = [];
  const rows = scopeSellers().sort().map((name) => {
    const mine = items.filter((item) => item.deal.vendedor === name);
    const pipeline = pipelineOf(mine);
    const seller = DATA.vendedores[name];
    const row = {
      vendedor: name,
      regiao: seller.regiao,
      manager: seller.manager,
      comChance: pipeline.comChance,
      valorDasVivas: sumOf(mine.filter((item) => item.deal.lista === "foco" && item.status.fase !== "concluida"), "preco"),
      prioritariasSemContato: mine.filter(isNeglected).length,
      naoIniciadas: pipeline.naoIniciadas,
      reativar: pipeline.reativar,
      encerrar: pipeline.semChance,
      contatadas: mine.filter(wasContacted).length,
    };
    lastTeam.push(row);
    const cell = (value) => `<td class="num">${value || '<span class="dash">–</span>'}</td>`;
    const note = !pipeline.abertas ? "nenhuma negociação aberta" : pipeline.comChance ? "" : "nenhuma com chance de fechar";
    return `
      <tr>
        <td><button class="link" data-seller-detail="${esc(name)}">${esc(name)}</button><small>${esc(seller.regiao)}${note ? ` · ${note}` : ""}</small></td>
        ${cell(row.comChance)}${cell(row.prioritariasSemContato)}${cell(row.naoIniciadas)}${cell(row.reativar)}${cell(row.encerrar)}${cell(row.contatadas)}
      </tr>`;
  }).join("");
  return `
    ${pageHead("Vendedores", "Clique num nome para ver o detalhe do vendedor.")}
    <div class="panel">
      <div class="panel-head"><h2>${lastTeam.length} vendedores</h2><div class="panel-tools">${regionSelect()}${exportButtons("team")}</div></div>
      <div class="table-wrap">
        <table class="team">
          <thead><tr><th>Vendedor</th><th class="num">Com chance</th><th class="num">Prioritárias sem contato</th><th class="num">Não iniciadas</th><th class="num">Reativar</th><th class="num">Encerrar</th><th class="num">Contatadas</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}

/* O detalhe de um vendedor: carteira de hoje, histórico e o que ele registrou na ferramenta. */
function pageVendedor() {
  const name = state.vendedorAberto;
  const seller = DATA.vendedores[name];
  const mine = workItems().filter((item) => item.deal.vendedor === name);
  const pipeline = pipelineOf(mine);
  const revenue = monthlySeries([name], "receita");
  const won = monthlySeries([name], "ganhos").reduce((sum, p) => sum + p.value, 0);
  const lost = monthlySeries([name], "perdidos").reduce((sum, p) => sum + p.value, 0);
  const total = revenue.reduce((sum, p) => sum + p.value, 0);
  const events = Workflow.events().filter((event) => event.vendedor === name).slice(-8).reverse();
  const situation = [
    { label: "Com chance de fechar", value: pipeline.comChance },
    { label: "Não iniciadas", value: pipeline.naoIniciadas },
    { label: "Para reativar", value: pipeline.reativar },
    { label: "Para encerrar", value: pipeline.semChance },
  ];
  const log = events.length
    ? `<ul class="timeline">${events.map((e) => `<li><span>${dayBR(e.quando)}</span><div>${esc(Workflow.EVENTS[e.tipo])} · ${esc(e.conta || e.produto)}${e.nota ? `<em>${esc(e.nota)}</em>` : ""}</div></li>`).join("")}</ul>`
    : '<p class="muted">Nenhum contato registrado na ferramenta por este vendedor, neste navegador.</p>';
  return `
    <header class="head with-tools">
      <div>
        <button class="link back" data-act="back-sellers">${icon("arrow-left")}Vendedores</button>
        <h1>${esc(name)}</h1>
        <p>${esc(seller.regiao)} · time de ${esc(seller.manager)}</p>
      </div>
      <div class="panel-tools"><button class="btn primary" data-seller="${esc(name)}">${icon("briefcase")}Abrir carteira</button><button class="btn" data-act="pdf">${icon("file-pdf")}PDF</button></div>
    </header>
    <div class="tiles">
      ${tile(pipeline.comChance, "Com chance de fechar", `de ${pipeline.abertas} negociações abertas`)}
      ${tile(mine.filter(isNeglected).length, "Prioritárias sem contato", "score 70 ou mais, sem registro")}
      ${tile(moneyShort(total), "Receita ganha em 2017", `${won} ganhas e ${lost} perdidas, de março a dezembro`)}
      ${tile(seller.cicloMedianoGanho === null ? "–" : `${seller.cicloMedianoGanho} dias`, "Ciclo mediano de ganho", "do início ao fechamento")}
    </div>
    <div class="chart-grid">
      ${chartCard("Receita ganha por mês", "Valor das negociações ganhas por este vendedor.", Charts.columns(revenue, { format: moneyShort, name: "Receita ganha" }))}
      ${chartCard("Carteira aberta hoje", "Quantas negociações em cada situação.", Charts.bars(situation, { format: (n) => n.toLocaleString("pt-BR"), name: "Negociações", first: "Situação" }))}
    </div>
    <div class="panel"><h2>Últimos contatos registrados</h2>${log}</div>
    <p class="muted">A taxa de ganho não difere de forma significativa entre vendedores (ver Como funciona). Este detalhe serve para acompanhar carteira e atividade, não para ranquear pessoas.</p>`;
}

/* ---------- como funciona ---------- */

function pageComo() {
  const curve = DATA.chancePorIdade;
  const peak = Math.max(...curve);
  const bars = curve.map((p) => `<div style="height:${Math.max(p / peak, 0.005) * 100}%"></div>`).join("");
  const test = DATA.backtest;
  const gain = (row) => `${row.ferramenta >= row.precoRecentes ? "+" : ""}${Math.round((row.ferramenta / row.precoRecentes - 1) * 100)}%`;
  const quarters = test.resumo
    .map((r) => `<tr><td>${esc(r.trimestre)}</td><td class="num">${money(r.ferramenta)}</td><td class="num">${money(r.precoRecentes)}</td><td class="num">${gain(r)}</td><td class="num">${r.semanasGanhas} de ${r.semanas}</td><td class="num">${money(r.soPreco)}</td><td class="num">${money(r.acaso)}</td></tr>`)
    .join("");
  const versus = (field) => test.resumo.map((r) => {
    const diff = Math.round((r.ferramenta / r[field] - 1) * 100);
    return `${diff >= 0 ? "+" : "−"}${Math.abs(diff)}% no ${r.trimestre}`;
  }).join(" e ");
  const liveGain = versus("precoVivas");
  const newestWeeks = test.resumo.map((r) => `${r.semanasGanhasNova} de ${r.semanas}`).join(" e ");
  const weekly = test.resumo.map((r) => {
    const diff = Math.round((r.ferramenta7 / r.precoRecentes7 - 1) * 100);
    return `${diff >= 0 ? "+" : "−"}${Math.abs(diff)}% no ${r.trimestre}`;
  }).join(" e ");
  const liveWeeks = test.resumo.reduce((sum, r) => sum + r.semanasGanhasVivas, 0);
  const spread = test.sensibilidade.flatMap((row) => Object.entries(row).filter(([key]) => key !== "dias").map(([key, value]) => ({ dias: row.dias, trimestre: key, value })));
  const worst = spread.reduce((a, b) => (b.value < a.value ? b : a));
  const best = spread.reduce((a, b) => (b.value > a.value ? b : a));
  const dead = DATA.deals.filter((d) => d.lista === "reativar" || d.lista === "encerrar");
  const pastCycle = dead.filter((d) => d.idade > DATA.cicloMaisLongo).length;
  const running = dead.length + LIVE_COUNT;
  const lostWeeks = test.semanas.filter((w) => w.ferramenta <= w.precoRecentes).map((w) => isoBR(w.data));
  const bands = test.faixas
    .map((b) => `<tr><td>${BANDS[b.faixa]}</td><td class="num">${b.deals.toLocaleString("pt-BR")}</td><td class="num">${(b.ganhos * 100).toFixed(1).replace(".", ",")}%</td></tr>`)
    .join("");
  const segments = DATA.segmentos
    .map((s) => `<tr><td>${esc(s.fator)}</td><td class="num">${s.grupos}</td><td class="num">${pct(s.min)} a ${pct(s.max)}</td><td class="num">${s.p.toFixed(2).replace(".", ",")}</td></tr>`)
    .join("");
  const rules = DATA.regras;
  const flow = Workflow.RULES;
  const soon = test.esteMes;
  return `
    ${pageHead("Como funciona", "De onde vêm os números, como foram testados e o que a ferramenta não sabe.")}
    <div class="panel">
      <h2>A conta</h2>
      <p><strong>Prioridade = preço de tabela do produto × chance de ganhar.</strong> O score de 0 a 100 é a posição desse valor entre as ${LIVE_COUNT} negociações com chance de fechar na empresa. O preço pesa mais na posição, mas a chance faz duas coisas: decide quem sai da lista e muda a ordem de quem fica (o teste abaixo mede as duas).</p>
      <p>A chance vem do histórico, olhando o mesmo ponto dos trimestres anteriores: das negociações que estavam abertas com a mesma idade há 3, 6 e 9 meses, quantas foram ganhas depois. O gráfico mostra como ela cai com a idade, do dia 0 ao dia ${DATA.cicloMaisLongo}.</p>
      <div class="curve">${bars}</div>
      <div class="axis"><span>dia 0</span><span>dia 45</span><span>dia 90</span><span>dia ${DATA.cicloMaisLongo}</span></div>
    </div>
    <div class="panel">
      <h2>O teste: a ordem da ferramenta é melhor que uma regra simples?</h2>
      <p>Voltamos no tempo em ${test.semanas.length} semanas seguidas (${isoBR(test.semanas[0].data)} a ${isoBR(test.semanas[test.semanas.length - 1].data)}). Em cada uma, calculamos tudo só com o que se sabia no dia e medimos a receita que as ${test.topN} primeiras negociações de cada vendedor geraram depois. A regra simples é "o produto mais caro primeiro, ignorando negociações com mais de ${test.regraSimplesDias} dias". Vários produtos têm o mesmo preço, então a regra simples tem muitos empates; eles são desempatados por sorteio, que é neutro.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Período</th><th class="num">Esta ferramenta</th><th class="num">Regra simples</th><th class="num">Diferença</th><th class="num">Semanas em que ganhou</th><th class="num">Só pelo preço</th><th class="num">Ao acaso</th></tr></thead>
          <tbody>${quarters}</tbody>
        </table>
      </div>
      <p class="muted">${lostWeeks.length ? `Semanas em que a ferramenta não ganhou da regra simples: ${lostWeeks.join(", ")}.` : "A ferramenta ganhou da regra simples em todas as semanas."} A vantagem sobre "só pelo preço" é grande porque essa ordenação inclui negociações mortas; a comparação honesta é com a regra simples. Os valores somam as semanas e a mesma negociação entra em várias delas: servem para comparar os métodos, não como receita da empresa, e "ganhou em 14 de 14" não são 14 provas independentes.</p>
      <p><strong>Onde a ferramenta não ganha.</strong> Uma regra simples mais esperta, "o mais caro primeiro e, no empate, a negociação mais nova", fica perto: a ferramenta rende ${versus("precoRecentesNova")} contra ela, ganhando em ${newestWeeks} semanas. Medindo sem repetir negociação (só o que foi ganho nos 7 dias seguintes a cada semana), a diferença contra a regra simples é ${weekly}. Ou seja: no 3º trimestre a ordem da ferramenta é melhor; no 4º, uma boa regra simples empata com ela. O que se sustenta nos dois é o corte (abaixo) e a ordem das faixas de chance.</p>
      <p><strong>É só ordenar por preço?</strong> Não. Usando o mesmo corte da ferramenta e ordenando só pelo preço, a ordem preço × chance rende ${liveGain}, e ganha em ${liveWeeks} das ${test.semanas.length} semanas.</p>
      <p><strong>O resultado depende dos ${test.regraSimplesDias} dias da regra simples?</strong> Em parte. Trocando o corte por ${test.sensibilidade.map((row) => row.dias).join(", ")} dias, a diferença vai de ${worst.value >= 0 ? "+" : "−"}${String(Math.abs(worst.value)).replace(".", ",")}% (corte de ${worst.dias} dias, ${worst.trimestre}) a +${String(best.value).replace(".", ",")}% (${best.dias} dias, ${best.trimestre}).</p>
    </div>
    <div class="panel">
      <h2>O teste: quem saiu da lista de ligação fechou depois?</h2>
      <p>Somando as ${test.semanas.length} semanas, a ferramenta tirou da lista de ligação ${test.parados.distintos.toLocaleString("pt-BR")} negociações diferentes (${test.parados.total.toLocaleString("pt-BR")} registros, porque a mesma negociação aparece em várias semanas). Foram ganhas depois: <strong>${test.parados.ganhos}</strong>. Encerradas como perdidas: ${test.parados.perdidos}. As demais continuaram abertas até o fim da base.</p>
    </div>
    <div class="panel">
      <h2>Por que a chance aparece em faixas</h2>
      <p>O percentual exato erra: para negociações de 60 a 75 dias, a ferramenta chegou a prever 37% quando 7% foram ganhas. A ordem, porém, se sustenta: faixa mais alta ganhou mais. Por isso a tela mostra Alta, Média ou Baixa.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Faixa</th><th class="num">Negociações no teste</th><th class="num">Ganhas depois</th></tr></thead>
          <tbody>${bands}</tbody>
        </table>
      </div>
      <p class="muted">"Pode fechar este mês": as negociações marcadas foram ganhas em ${rules.diasEsteMes} dias em ${pct(soon.ganhosMarcados)} dos casos; as não marcadas que ainda tinham chance, em ${(soon.ganhosNaoMarcadosVivas * 100).toFixed(1).replace(".", ",")}%. Hoje só ${DATA.deals.filter((d) => d.fechaEsteMes).length} das ${LIVE_COUNT} negociações com chance têm a marca.</p>
    </div>
    <div class="panel">
      <h2>O que não entra na conta, e por quê</h2>
      <p>Entre as negociações fechadas, a taxa de ganho é ${pct(DATA.historico.taxaGanho)} e quase não muda por vendedor, produto, setor, conta, manager ou região. A última coluna é a probabilidade de a diferença ser acaso: acima de 0,05 não há diferença real entre ganhar e perder. Isso não mede quem deixa negociação aberta sem fechar, que varia entre escritórios. A coluna "Grupos" conta só os que têm 30 ou mais negociações fechadas. O porte da conta pelo faturamento dá 0,03, mas sem direção (as quatro faixas, da menor para a maior, ganham 63%, 62%, 66% e 61%), então não serve para ordenar; além disso, ${pct(DATA.deals.filter((d) => !d.conta).length / DATA.deals.length)} das negociações abertas não têm a conta preenchida. Testamos também mais de 100 combinações (vendedor com produto, histórico da conta, carga do vendedor, desconto, dia da semana), com validação no tempo, e nenhuma melhorou a ordem de forma que se sustente.</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Fator</th><th class="num">Grupos</th><th class="num">Taxa de ganho (menor a maior)</th><th class="num">Chance de ser acaso</th></tr></thead>
          <tbody>${segments}</tbody>
        </table>
      </div>
    </div>
    <div class="panel">
      <h2>As listas e o fluxo</h2>
      <p><strong>Em negociação:</strong> ainda tem chance de fechar pelo histórico. <strong>Reativação:</strong> não tem mais, mas começou há até ${rules.reativarAte} dias (${rules.reativarAteCaro} para produtos a partir de ${money(rules.precoCaro)}). <strong>Encerrar:</strong> mais antiga que isso. <strong>Não iniciadas:</strong> sem data de início; ficam sem chance e sem score e são ordenadas pelo valor.</p>
      <p><strong>A tela Hoje tem duas partes.</strong> Em cima, a meta do dia: retornos combinados e negociações com chance, na ordem valor × chance; o contador conta só essas. Embaixo, "se sobrar tempo": primeiro contato e reativação. O histórico não consegue dizer qual dessas vale mais, então vêm antes as que têm empresa cadastrada. Essa ordem de baixo é bom senso, não foi testada.</p>
      <p><strong>Depois de cada contato:</strong> ligou e não atendeu, volta em ${flow.religarEmDias} dias. Enviou mensagem, fica em Aguardando e volta em ${flow.esperarRespostaDias} dias se não houver resposta. Depois de ${flow.maximoTentativas} ligações sem resposta, o próximo passo vira uma mensagem para confirmar o interesse; só se ela também ficar sem resposta a negociação vai para Encerrar. Negociações de mensagem vão para Encerrar depois de ${flow.maximoTentativas} mensagens sem resposta. Essas regras são escolhas de negócio: a base não registra tentativas de contato.</p>
    </div>
    <div class="panel">
      <h2>Limites</h2>
      <p><strong>Dois números para "morto".</strong> Das ${running.toLocaleString("pt-BR")} negociações em andamento, ${pastCycle.toLocaleString("pt-BR")} (${pct(pastCycle / running)}) já passaram dos ${DATA.cicloMaisLongo} dias, o ciclo mais longo em que alguma foi ganha. Contando também as que ainda não passaram mas, pelo padrão de trimestre, não fecham mais, são ${dead.length.toLocaleString("pt-BR")} (${pct(dead.length / running)}): é o "sem chance" do Painel.</p>
      <p><strong>A lista de hoje não pode ser validada.</strong> No fim dos trimestres anteriores, cerca de 60% das negociações do trimestre ainda estavam abertas; em ${isoBR(DATA.hoje)} são 10%. A base termina de um jeito diferente do resto do ano, e a chance das negociações em andamento de hoje pode estar superestimada.</p>
      <p><strong>O padrão de trimestre vem de 14 meses de uma base de exemplo.</strong> Numa empresa real ele precisa ser medido de novo com o histórico dela.</p>
      <p><strong>"Sem contato" é o que a ferramenta registrou.</strong> O CRM não guarda ligações, e-mails ou reuniões; no primeiro dia de uso, nenhuma negociação tem contato registrado. Também não há custo de produto (margem), e a maioria das negociações abertas não tem o cliente preenchido.</p>
      <p><strong>A reativação é uma aposta.</strong> O histórico não registra se alguém tentou retomar negociações paradas; por isso cada contato e cada resposta ficam registrados para medir.</p>
      <p><strong>Sem senha.</strong> A entrada separa o que o vendedor e o gerente veem, mas todos os dados estão no arquivo, e os registros ficam só neste navegador. Em produção, o acesso viria do login do CRM e os registros gravariam nele.</p>
    </div>`;
}

/* ---------- entrada ---------- */

const ROLES = [
  { id: "vendedor", nome: "Vendedor", icone: "user", texto: "Minha fila do dia e minha carteira" },
  { id: "gerente", nome: "Gerente", icone: "users-three", texto: "Meu time, vendedor por vendedor" },
  { id: "revops", nome: "Operações de receita", icone: "chart-line-up", texto: "A empresa inteira, todos os times" },
];

function roleLabel(session) {
  if (session.papel === "vendedor") return "Vendedor";
  return session.nome === EVERYONE ? "Operações de receita" : "Gerente";
}

/* Quem pode entrar em cada perfil, com um resumo da carteira. */
function peopleOf(role) {
  const key = role === "vendedor" ? "vendedor" : "manager";
  const names = role === "vendedor" ? Object.keys(DATA.vendedores).sort() : unique(DATA.deals, key);
  const teamSize = (manager) => Object.values(DATA.vendedores).filter((seller) => seller.manager === manager).length;
  return names.map((name) => {
    const deals = DATA.deals.filter((deal) => deal[key] === name);
    const live = deals.filter((deal) => deal.lista === "foco").length;
    const detail = role !== "vendedor"
      ? `${teamSize(name)} vendedores · ${live} com chance de fechar`
      : !deals.length
        ? "nenhuma negociação aberta"
        : `${live ? `${live} com chance de fechar` : "nenhuma com chance"} · ${deals.length} abertas`;
    return { name, region: role === "vendedor" ? DATA.vendedores[name].regiao : deals[0].regiao, detail };
  });
}

function peopleList() {
  const search = fold(state.buscaNome.trim());
  const people = peopleOf(state.entering).filter((person) => !search || fold(person.name).includes(search));
  if (!people.length) return '<div class="empty">Ninguém com esse nome.</div>';
  return unique(people, "region").map((region) => `
    <h2>${esc(region)}</h2>
    ${people.filter((person) => person.region === region).map((person) => `<button class="person" data-enter="${esc(person.name)}"><span><strong>${esc(person.name)}</strong><small>${person.detail}</small></span>${icon("caret-right")}</button>`).join("")}`).join("");
}

function pageEntrar() {
  const last = Workflow.read(LAST_KEY, null);
  const step = state.entering ? 2 : 1;
  const steps = `<ol class="steps-bar"><li class="${step === 1 ? "on" : "done"}"><b>1</b>Perfil</li><li class="${step === 2 ? "on" : ""}"><b>2</b>Nome</li></ol>`;
  const top = `<div class="enter-top"><p class="brand">${LOGO}<small>AI Master Challenge</small></p><button class="link" data-act="theme">${themeButton()}</button></div>`;

  if (step === 1) {
    return `
      <section class="enter">
        ${top}
        <h1>Como você quer entrar?</h1>
        ${steps}
        ${last ? `<button class="last" data-last="1"><span><strong>Continuar como ${esc(last.nome)}</strong><small>${roleLabel(last)} · último acesso neste navegador</small></span>${icon("arrow-right")}</button>` : ""}
        <div class="roles">
          ${ROLES.map((role) => `<button data-role="${role.id}">${icon(role.icone)}<strong>${role.nome}</strong><span>${role.texto}</span></button>`).join("")}
        </div>
        <p class="muted">Demonstração sem senha. Cada perfil vê só o que é seu, e dá para trocar de perfil a qualquer momento.</p>
        <p class="muted">Projeto de candidato para o AI Master Challenge. Não é um produto oficial do G4; os dados são fictícios.</p>
      </section>`;
  }
  const role = ROLES.find((r) => r.id === state.entering);
  return `
    <section class="enter">
      ${top}
      <button class="link back" data-act="back-role">${icon("arrow-left")}Trocar de perfil</button>
      <h1>${role.id === "vendedor" ? "Qual é o seu nome?" : "Qual é o seu time?"}</h1>
      ${steps}
      <label class="search">${icon("magnifying-glass")}<input type="search" id="busca-nome" placeholder="Buscar pelo nome" value="${esc(state.buscaNome)}" aria-label="Buscar nome"></label>
      <div class="people" id="people">${peopleList()}</div>
    </section>`;
}

/* ---------- tema ---------- */

const themeLabel = () => (document.documentElement.dataset.theme === "dark" ? "Modo claro" : "Modo escuro");
const themeButton = () => `${icon(document.documentElement.dataset.theme === "dark" ? "sun" : "moon")}<span>${themeLabel()}</span>`;

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  Workflow.write(THEME_KEY, next);
}

/* ---------- moldura ---------- */

const PAGES = {
  vendedor: [["hoje", "Hoje", "list-checks"], ["aguardando", "Aguardando", "hourglass"], ["carteira", "Carteira", "briefcase"], ["como", "Como funciona", "info"]],
  gerente: [["painel", "Painel", "chart-bar"], ["vendedores", "Vendedores", "users-three"], ["carteira", "Carteira", "briefcase"], ["como", "Como funciona", "info"]],
};

function render() {
  const view = $("view");
  document.body.classList.toggle("entering", !state.session);
  if (!state.session) {
    document.body.classList.remove("fixed");
    view.innerHTML = pageEntrar();
    return renderSheet();
  }
  const items = workItems();
  const counts = {
    hoje: todayParts(items).prioridade.length, // a meta do dia; o que é "se sobrar tempo" não conta
    aguardando: items.filter((item) => item.status.fase === "aguardando" || item.status.fase === "agendada").length,
    carteira: items.length,
  };
  $("nav").innerHTML = PAGES[state.session.papel]
    .map(([id, label, glyph]) => `<button data-page="${id}"${id === state.page ? ' aria-current="page"' : ""}>${icon(glyph)}<span>${label}</span>${id in counts && (isSeller() || id === "carteira") ? `<em>${counts[id].toLocaleString("pt-BR")}</em>` : ""}</button>`)
    .join("");
  $("user").innerHTML = `<strong>${esc(state.session.nome)}</strong><span>${roleLabel(state.session)}</span>`;
  document.querySelector(".account [data-act=theme]").innerHTML = themeButton();
  const builders = {
    hoje: pageHoje, aguardando: pageAguardando, carteira: pageCarteira, como: pageComo,
    painel: pagePainel, vendedores: () => (state.vendedorAberto ? pageVendedor() : pageVendedores()),
  };
  document.body.classList.toggle("fixed", state.page in TABLE_BODY);
  view.innerHTML = builders[state.page]();
  renderSheet();
}

function go(page) {
  state.page = page;
  state.vendedorAberto = null;
  state.pagina = 0;
  state.filtroProduto = "";
  state.filtroAcao = "";
  state.busca = "";
  state.ordem = { coluna: null, sentido: -1 };
  state.openId = null;
  state.form = emptyForm();
  hideToast();
  render();
  window.scrollTo(0, 0);
}

function enter(papel, nome) {
  state.session = { papel, nome };
  state.filtroVendedor = "";
  state.entering = null;
  Workflow.write(LAST_KEY, state.session);
  state.buscaNome = "";
  state.filtroVendedor = "";
  state.filtroRegiao = "";
  state.filtroManager = "";
  state.situacao = "todas";
  state.busca = "";
  Workflow.write(SESSION_KEY, state.session);
  go(papel === "vendedor" ? "hoje" : "painel");
}

let toastTimer;
function toast(message, undoId) {
  const box = $("toast");
  box.innerHTML = `${esc(message)}${undoId ? ` <button class="link" data-act="undo" data-id="${esc(undoId)}">Desfazer</button>` : ""}`;
  box.hidden = false;
  // A ficha é um <dialog> modal e cobre o resto da página; como popover, o aviso fica por cima dela.
  if (box.showPopover) {
    try {
      if (box.matches(":popover-open")) box.hidePopover();
      box.showPopover();
    } catch { /* navegador sem popover: o aviso aparece quando a ficha fecha */ }
  }
  clearTimeout(toastTimer);
  toastTimer = setTimeout(hideToast, 7000);
}

function hideToast() {
  const box = $("toast");
  clearTimeout(toastTimer);
  if (box.hidePopover) {
    try {
      if (box.matches(":popover-open")) box.hidePopover();
    } catch { /* idem */ }
  }
  box.hidden = true;
}

function download(name, columns, rows) {
  const lines = [columns.map(([, label]) => csvCell(label)).join(";")]
    .concat(rows.map((row) => columns.map(([key]) => csvCell(row[key])).join(";")));
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob(["\ufeff" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
}

function exportStatus({ deal, status }) {
  if (status.fase === "fila") return LISTS[deal.lista].tarefa;
  if (status.fase === "aguardando") return `Aguardando resposta até ${dayBR(status.volta)}`;
  if (status.fase === "agendada") return `${status.tarefa} em ${dayBR(status.volta)}`;
  if (status.fase === "concluida") return status.resultado;
  return status.tarefa;
}

/* Planilha com o que a tabela atual mostra, já filtrada e na mesma ordem. */
function exportTable() {
  if (!lastTable.rows.length) return toast("Não há negociações para exportar com esse filtro.");
  const rows = lastTable.rows.map((item, i) => {
    const { deal, status } = item;
    const last = lastEvent(item);
    return {
      posicao: lastTable.marker ? lastTable.marker(item) : i + 1,
      empresa: deal.conta || "Não informada",
      setor: deal.conta ? sectorName(deal.setor) : "",
      produto: deal.produto,
      valor: deal.preco,
      lista: LISTS[deal.lista].nome,
      situacao: exportStatus(item),
      chance: hasScore(deal) ? BANDS[deal.faixa] : "",
      score: hasScore(deal) ? deal.score : "",
      idadeDias: deal.idade ?? "",
      ultimoContato: last ? new Date(last.quando).toLocaleDateString("pt-BR") : "Nunca",
      vendedor: deal.vendedor,
      codigo: deal.id,
    };
  });
  download(`negociacoes-${state.page}.csv`, [
    ["posicao", "Posição"], ["empresa", "Empresa"], ["setor", "Setor"], ["produto", "Produto"], ["valor", "Valor"],
    ["lista", "Lista"], ["situacao", "O que fazer"], ["chance", "Chance"], ["score", "Score"], ["idadeDias", "Idade (dias)"],
    ["ultimoContato", "Último contato"], ["vendedor", "Vendedor"], ["codigo", "Código"],
  ], rows);
  toast(`${rows.length.toLocaleString("pt-BR")} negociações exportadas.`);
}

function exportTeam() {
  download("time.csv", [
    ["vendedor", "Vendedor"], ["regiao", "Região"], ["manager", "Manager"], ["comChance", "Com chance de fechar"],
    ["valorDasVivas", "Valor das vivas"], ["prioritariasSemContato", "Prioritárias sem contato"], ["naoIniciadas", "Não iniciadas"],
    ["reativar", "Reativação"], ["encerrar", "Encerrar"], ["contatadas", "Contatadas"],
  ], lastTeam);
  toast(`${lastTeam.length} vendedores exportados.`);
}

/* PDF sem biblioteca: a página é impressa com um estilo próprio, e o navegador salva como PDF. */
function exportPdf() {
  state.printing = true;
  render();
  window.print();
}

window.addEventListener("afterprint", () => {
  if (!state.printing) return;
  state.printing = false;
  render();
});

/* Registros de contato, só das negociações que o perfil atual enxerga. */
function exportCsv() {
  const columns = ["quando", "tipo", "retornoEm", "nota", "autor", "id", "lista", "vendedor", "manager", "regiao", "produto", "preco", "idadeDias", "conta", "setor"];
  const visible = new Set(visibleDeals().map((deal) => deal.id));
  const events = Workflow.events().filter((event) => visible.has(event.id));
  const lines = [columns.join(";")].concat(events.map((event) => columns.map((c) => csvCell(event[c])).join(";")));
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
  link.download = "contatos-vendedores.csv";
  link.click();
  URL.revokeObjectURL(link.href);
  toast(`${events.length.toLocaleString("pt-BR")} registros de contato exportados.`);
}

/* ---------- ações ---------- */

/* Salva o evento confirmado, fecha o pop-up e avisa para onde a negociação foi. */
function register(deal, tipo, extra = {}) {
  const nota = state.form.nota.trim();
  const autor = `${state.session.nome} (${roleLabel(state.session)})`; // quem registrou: o gerente também pode
  Workflow.add(deal, tipo, nota ? { ...extra, nota, autor } : { ...extra, autor });
  state.form = emptyForm();
  state.openId = null;
  const status = Workflow.statusOf(deal, Workflow.byDeal()[deal.id]);
  const messages = {
    nao_atendeu: status.confirmar
      ? `${status.ligacoes} ligações sem resposta. Continua em Hoje: agora é uma mensagem para confirmar o interesse.`
      : `Registrado. Volta para Hoje em ${dayBR(status.volta)} para a ${status.ligacoes + 1}ª tentativa.`,
    retornar: status.fase === "retorno"
      ? "Retorno marcado para hoje. Continua em Hoje, no topo da lista."
      : `Retorno marcado para ${dayBR(status.volta)}. Está em Aguardando.`,
    enviou: status.tentativas >= Workflow.RULES.maximoTentativas
      ? `Enviada. Era a última tentativa: sem resposta até ${dayBR(status.volta)}, vai para Encerrar.`
      : `Enviada. Está em Aguardando; sem resposta até ${dayBR(status.volta)}, volta para Hoje.`,
    respondeu: "Voltou para Hoje: ligar para o cliente.",
    ganhou: "Registrada como ganha. Saiu da sua lista.",
    perdeu: "Registrada como perdida. Saiu da sua lista.",
    encerrou: "Encerrada. Saiu da sua lista.",
  };
  toast(messages[tipo], deal.id);
}

function act(action, id, target) {
  const deal = id ? DEAL_BY_ID[id] : null;
  const ask = (tipo, extra = {}) => { state.form.pendente = { id, tipo, extra }; state.form.desde = Date.now(); };
  // O botão seguinte aparece no mesmo lugar do anterior: um duplo clique não pode valer como confirmação.
  const tooFast = () => Date.now() - state.form.desde < DOUBLE_CLICK_MS;
  if (action === "combinar") { state.form.retorno = true; state.form.desde = Date.now(); }
  else if (action === "cancel") state.form = emptyForm();
  else if (action === "confirm") {
    if (!state.form.pendente || tooFast()) return;
    const { id: pendingId, tipo, extra } = state.form.pendente;
    register(DEAL_BY_ID[pendingId], tipo, extra);
  } else if (action === "ret:data") {
    const value = $("retorno-data").value;
    if (!value) return toast("Escolha a data do retorno.");
    const chosen = new Date(`${value}T12:00:00`);
    if (Number.isNaN(chosen.getTime())) return toast("Data inválida. Confira o dia, o mês e o ano.");
    if (new Date(`${value}T23:59:59`) <= Workflow.now()) return toast("O retorno precisa ser em uma data futura.");
    if (chosen > Workflow.addDays(Workflow.now(), 365)) return toast("Escolha uma data nos próximos 12 meses.");
    ask("retornar", { retornoEm: chosen.toISOString() });
  } else if (action.startsWith("ret:")) {
    if (tooFast()) return;
    ask("retornar", { retornoEm: Workflow.addDays(Workflow.now(), Number(action.slice(4))).toISOString() });
  } else if (["nao_atendeu", "enviou", "respondeu", "ganhou", "perdeu", "encerrou"].includes(action)) ask(action);
  else if (action === "undo") {
    Workflow.undoLast(id);
    hideToast();
  } else if (action === "theme") {
    toggleTheme();
  } else if (action === "close") {
    state.openId = null;
    state.form = emptyForm();
  } else if (action === "prev") state.pagina -= 1;
  else if (action === "next") state.pagina += 1;
  else if (action === "export") return exportCsv();
  else if (action === "csv") return target === "team" ? exportTeam() : exportTable();
  else if (action === "pdf") return exportPdf();
  else if (action === "back-role") { state.entering = null; state.buscaNome = ""; }
  else if (action === "back-sellers") state.vendedorAberto = null;
  else if (action === "copy") {
    const text = $("message").textContent;
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(() => toast("Mensagem copiada."), () => toast("Não foi possível copiar. Selecione o texto e copie."));
    else toast("Selecione o texto e copie.");
    return;
  }
  render();
}

document.addEventListener("click", (event) => {
  syncSheet();
  if (event.target.id === "sheet") return act("close"); // clique fora do pop-up
  const target = event.target.closest("button");
  if (!target) return;
  const data = target.dataset;
  const note = $("nota");
  if (note) state.form.nota = note.value; // a anotação não se perde quando a tela é redesenhada

  if (target.id === "leave") {
    state.session = null;
    state.entering = null;
    state.openId = null;
    state.form = emptyForm();
    hideToast();
    lastTable = { rows: [], marker: null };
    Workflow.write(SESSION_KEY, null);
    return render();
  }
  if (data.role) {
    if (data.role === "revops") return enter("gerente", EVERYONE);
    state.entering = data.role;
    state.buscaNome = "";
    return render();
  }
  if (data.last) {
    const last = lastSession();
    return last ? enter(last.papel, last.nome) : render();
  }
  if (data.enter) return enter(state.entering, data.enter);
  if (data.page) return go(data.page);
  if (data.situacao) {
    go("carteira");
    state.situacao = data.situacao;
    state.busca = "";
    return render();
  }
  if (data.seller) {
    go("carteira");
    state.filtroVendedor = data.seller;
    state.filtroManager = "";
    state.filtroRegiao = "";
    state.situacao = "todas";
    return render();
  }
  if (data.sellerDetail) {
    state.vendedorAberto = scopeSellers().includes(data.sellerDetail) ? data.sellerDetail : null;
    state.page = "vendedores";
    render();
    return window.scrollTo(0, 0);
  }
  if (data.serie) {
    state.serie = data.serie === "iniciadas" ? "iniciadas" : "receita";
    return render();
  }
  if (data.visao) {
    state.visao = data.visao === "kanban" ? "kanban" : "lista";
    Workflow.write(VIEW_KEY, state.visao);
    state.pagina = 0;
    return render();
  }
  if ("acao" in data) {
    state.filtroAcao = data.acao;
    state.pagina = 0;
    return render();
  }
  if ("sort" in data) {
    const same = state.ordem.coluna === data.sort;
    state.ordem = data.sort ? { coluna: data.sort, sentido: same ? -state.ordem.sentido : -1 } : { coluna: null, sentido: -1 };
    state.pagina = 0;
    return render();
  }
  if (data.open) {
    state.openId = data.open;
    state.form = emptyForm();
    return render();
  }
  if (data.act) act(data.act, data.id, data.what);
});

document.addEventListener("change", (event) => {
  syncSheet();
  const { id, value } = event.target;
  if (id === "situacao") state.situacao = value;
  else if (id === "filtro-produto") state.filtroProduto = value;
  else if (id === "filtro-vendedor") state.filtroVendedor = value;
  else if (id === "filtro-regiao") state.filtroRegiao = value;
  else if (id === "filtro-manager") state.filtroManager = value;
  else return;
  state.pagina = 0;
  render();
});

/* A busca redesenha só a tabela, para o campo não perder o foco a cada letra. */
document.addEventListener("input", (event) => {
  if (event.target.id === "busca-nome") {
    state.buscaNome = event.target.value;
    $("people").innerHTML = peopleList();
    return;
  }
  if (event.target.id !== "busca") return;
  state.busca = event.target.value;
  state.pagina = 0;
  $("table-body").innerHTML = TABLE_BODY[state.page]();
});

/* Esc (ou qualquer fechamento do <dialog>) esquece a ficha e a ação pendente.
   Três caminhos, porque nem todo navegador dispara os eventos do <dialog> na mesma hora:
   o Esc ("cancel"), o fechamento ("close") e, por garantia, a conferência antes de cada ação. */
function forgetSheet() {
  if (!state.openId) return;
  state.openId = null;
  state.form = emptyForm();
}
function syncSheet() {
  if (state.openId && !$("sheet").open) forgetSheet(); // a ficha foi fechada sem passar pelos botões
}
$("sheet").addEventListener("cancel", forgetSheet);
$("sheet").addEventListener("close", forgetSheet);

/* Links diretos: ?vendedor=Nome, ?gerente=Nome ou ?perfil=revops */
const query = new URLSearchParams(location.search);
const linked = query.get("vendedor");
if (linked && DATA.vendedores[linked]) state.session = { papel: "vendedor", nome: linked };
if (query.get("gerente")) state.session = { papel: "gerente", nome: query.get("gerente") };
if (query.get("perfil") === "revops") state.session = { papel: "gerente", nome: EVERYONE };
if (!validSession(state.session)) state.session = null;
if (state.session) {
  state.page = state.session.papel === "vendedor" ? "hoje" : "painel";
  // Links para uma tela específica: &pagina=carteira, &visao=kanban, &abrir=CÓDIGO, &detalhe=Vendedor
  const wanted = query.get("pagina");
  if (PAGES[state.session.papel].some(([id]) => id === wanted)) state.page = wanted;
  if (query.get("visao") === "kanban" || query.get("visao") === "lista") state.visao = query.get("visao");
  if (visibleDeals().some((deal) => deal.id === query.get("abrir"))) state.openId = query.get("abrir");
  if (state.session.papel === "gerente" && scopeSellers().includes(query.get("detalhe"))) {
    state.page = "vendedores";
    state.vendedorAberto = query.get("detalhe");
  }
}
Charts.installTooltip();
Workflow.resetClock(); // o relógio de demonstração saiu da tela: a ferramenta usa sempre o dia real
render();
