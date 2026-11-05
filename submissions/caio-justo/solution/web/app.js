"use strict";

const estado = { filtros: null, consulta: new URLSearchParams(location.search) };
const conteudo = document.getElementById("conteudo");

const RESPOSTAS_MINIMAS = 30;
const RESPOSTAS = [
  ["vivo", "Vivo"],
  ["depois", "Voltar depois"],
  ["perdido", "Perdido"],
  ["errado", "Registro errado"],
];

function h(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const inteiro = (n) => Number(n).toLocaleString("pt-BR");
const dinheiro = (n) => "$" + inteiro(Math.round(n));
const pct = (x, casas = 0) => (100 * x).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }) + "%";
const milhoes = (n) => "$" + (n / 1e6).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "M";

function param(nome, padrao) {
  return estado.consulta.get(nome) || padrao;
}
function definir(mudancas) {
  for (const [k, v] of Object.entries(mudancas)) {
    if (v) estado.consulta.set(k, v);
    else estado.consulta.delete(k);
  }
  history.replaceState(null, "", "?" + estado.consulta.toString());
}
const modo = () => param("modo", "real");

async function buscar(caminho) {
  const r = await fetch(caminho);
  const dados = await r.json();
  if (!r.ok) throw new Error(dados.erro || "Falha ao carregar");
  return dados;
}
async function enviar(caminho, corpo) {
  const r = await fetch(caminho, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ modo: modo(), ...corpo }) });
  const dados = await r.json();
  if (!r.ok) throw new Error(dados.erro || "Falha ao salvar");
  return dados;
}

function carregando() {
  conteudo.innerHTML = '<div class="esqueleto"></div>'.repeat(5);
}
function mostrarErro(erro, tentar) {
  conteudo.innerHTML = `<div class="erro"><h2>Não consegui carregar esta tela</h2><p>${h(erro.message)}. Confira se o servidor está rodando e tente de novo.</p><div class="acoes"><button id="tentar">Tentar de novo</button></div></div>`;
  document.getElementById("tentar").addEventListener("click", tentar);
}

let tempoToast;
function aviso(texto, desfazer) {
  const toast = document.getElementById("toast");
  toast.innerHTML = `<span>${h(texto)}</span>`;
  if (desfazer) {
    const botao = document.createElement("button");
    botao.textContent = "Desfazer";
    botao.addEventListener("click", async () => {
      toast.hidden = true;
      await desfazer();
    });
    toast.appendChild(botao);
  }
  toast.hidden = false;
  clearTimeout(tempoToast);
  tempoToast = setTimeout(() => { toast.hidden = true; }, 6000);
}

function linhaDeal(d, botoes, opcoes = {}) {
  const nota = d.nota == null ? "" : `<div><span class="nota ${d.nota >= 80 ? "alta" : ""}">${d.nota}</span><span class="nota-legenda">nota</span></div>`;
  return `<li class="deal ${d.adiado ? "adiado" : ""}" data-id="${h(d.id)}">
    ${nota || "<div></div>"}
    <div>
      <div class="deal-nome">${h(d.conta || "Conta não preenchida")}</div>
      <div class="deal-dados">${h(d.produto)}, <span class="num">${dinheiro(d.preco)}</span>${d.idade != null ? `, <span class="num">${d.idade}</span> dias` : ""}</div>
    </div>
    <div class="deal-motivos">
      <ul class="motivos">${d.motivos.map((m) => `<li>${h(m)}</li>`).join("")}</ul>
      <p class="acao">${h(d.acao)}</p>
    </div>
    <div class="botoes">${botoes || ""}</div>
  </li>`;
}

const botoesTrabalho = (d) => `
  <button data-acao="resultado" data-valor="ganhou">Ganhei</button>
  <button data-acao="resultado" data-valor="perdeu">Perdi</button>
  <button data-acao="adiar" data-valor="${d.adiado ? "" : "1"}" aria-pressed="${d.adiado ? "true" : "false"}">${d.adiado ? "Adiado" : "Adiar"}</button>`;

const botoesChecagem = (d) => RESPOSTAS.map(([valor, rotulo]) => `<button data-acao="checagem" data-valor="${valor}" aria-pressed="${d.resposta === valor}">${rotulo}</button>`).join("");

async function telaSemana() {
  const vendedores = estado.filtros.vendedores;
  const padrao = vendedores.reduce((melhor, v) => (v.ativos > melhor.ativos ? v : melhor), vendedores[0]);
  const atual = param("vendedor", padrao.nome);
  const dados = await buscar(`/api/semana?vendedor=${encodeURIComponent(atual)}&modo=${modo()}`);
  const respondidos = dados.checar.filter((d) => d.resposta).length;
  const opcoes = vendedores.map((v) => `<option value="${h(v.nome)}" ${v.nome === atual ? "selected" : ""}>${h(v.nome)}</option>`).join("");
  const naoTrabalhados = dados.qualificar_total
    ? `<ol class="fila" id="qualificar">${dados.qualificar.map((d) => linhaDeal(d, "")).join("")}</ol><p class="nota-rodape">Os ${dados.qualificar.length} de maior preço, de ${dados.qualificar_total}. Eles ainda não têm data de início, então não dá para medir a idade.</p>`
    : "";
  const semAtivos = !dados.foco.length;
  conteudo.innerHTML = `
    <div class="topo">
      <div>
        <h1>Sua semana, ${h(atual.split(" ")[0])}</h1>
        <p class="fraco">Foto do CRM em ${new Date(estado.filtros.hoje + "T12:00").toLocaleDateString("pt-BR")}, a última data do dataset. A nota mostra prioridade, não a chance de fechar.</p>
      </div>
      <div class="filtros"><label>Vendedor<select id="vendedor">${opcoes}</select></label></div>
    </div>
    ${semAtivos && naoTrabalhados ? `<section class="secao"><div class="secao-cab"><h2>Comece por estes negócios não trabalhados</h2><p>Você não tem negócios ativos no tempo normal, então a prioridade é abrir pipeline novo.</p></div>${naoTrabalhados}</section>` : ""}
    ${semAtivos && !naoTrabalhados ? `<section class="secao"><div class="secao-cab"><h2>Foco da semana</h2></div><p class="vazio">Nada em foco agora. Novos negócios aparecem aqui assim que entrarem em Engaging.</p></section>` : ""}
    ${semAtivos ? "" : `<section class="secao">
      <div class="secao-cab"><h2>Foco da semana</h2><p>Negócios que ainda estão no tempo normal, do mais caro para o mais barato.</p></div>
      <ol class="fila" id="foco">${dados.foco.map((d) => linhaDeal(d, botoesTrabalho(d))).join("")}</ol>
      ${dados.mais_foco.length ? `<details><summary>Mais negócios em foco <span class="fraco num">${dados.mais_foco.length}</span></summary><ol class="fila">${dados.mais_foco.map((d) => linhaDeal(d, botoesTrabalho(d))).join("")}</ol></details>` : ""}
    </section>`}
    <section class="secao">
      <div class="secao-cab"><h2>Confirme estes negócios parados</h2><p>Sorteamos <span class="num">${dados.checar.length}</span> dos seus <span class="num">${dados.parados_total}</span> negócios parados há mais de ${dados.limite} dias. Sua resposta ajuda a saber quanto do pipeline ainda é real.</p></div>
      ${dados.checar.length ? `<p class="fraco"><span class="num">${respondidos}</span> de <span class="num">${dados.checar.length}</span> respondidos</p><ol class="fila" id="checar">${dados.checar.map((d) => linhaDeal(d, botoesChecagem(d))).join("")}</ol>` : `<p class="vazio">Nenhum negócio seu caiu no sorteio.</p>`}
    </section>
    ${dados.demais.length ? `<details><summary>Outros negócios ativos <span class="fraco num">${dados.demais.length}</span></summary><ol class="fila">${dados.demais.map((d) => linhaDeal(d, botoesTrabalho(d))).join("")}</ol></details>` : ""}
    ${!semAtivos && naoTrabalhados ? `<details><summary>Ainda não trabalhados <span class="fraco num">${dados.qualificar_total}</span></summary>${naoTrabalhados}</details>` : ""}
  `;
  document.getElementById("vendedor").addEventListener("change", (e) => { definir({ vendedor: e.target.value }); renderizar(); });
  conteudo.querySelectorAll("button[data-acao]").forEach((botao) => botao.addEventListener("click", () => agir(botao, atual)));
}

async function agir(botao, vendedor) {
  const linha = botao.closest(".deal");
  const negocio = linha.dataset.id;
  const { acao, valor } = botao.dataset;
  linha.querySelectorAll("button").forEach((b) => { b.disabled = true; });
  try {
    if (acao === "checagem") {
      const repetiu = botao.getAttribute("aria-pressed") === "true";
      await enviar("/api/checagem", { negocio, vendedor, resposta: repetiu ? null : valor });
      aviso(repetiu ? "Resposta removida." : "Resposta salva.");
    } else if (acao === "resultado") {
      await enviar("/api/resultado", { negocio, vendedor, resultado: valor });
      aviso(valor === "ganhou" ? "Marcado como ganho." : "Marcado como perdido.", async () => {
        await enviar("/api/resultado", { negocio, vendedor, resultado: null });
        await renderizar();
      });
    } else {
      await enviar("/api/adiar", { negocio, vendedor, adiado: Boolean(valor) });
      aviso(valor ? "Foi para o fim da lista." : "Voltou para a posição normal.");
    }
    await renderizar(false);
  } catch (erro) {
    aviso(erro.message);
    linha.querySelectorAll("button").forEach((b) => { b.disabled = false; });
  }
}

function blocoChecagem(c) {
  const textos = {
    aguardando: "Ainda sem decisão. Ela sai quando as 100 respostas chegarem.",
    limpar: `Menos de ${pct(c.limite_limpeza)} do valor segue real. A proposta é tirar os parados da fila, depois da revisão do RevOps.`,
    recuperar: `Pelo menos ${pct(c.limite_limpeza)} do valor segue real. A proposta é abordar os ${inteiro(c.parados)} parados de novo, por preço.`,
    inconclusivo: `A margem cruza a linha de ${pct(c.limite_limpeza)}. Vale sortear mais negócios antes de decidir.`,
  };
  const e = c.estimativa;
  const estimativa = e.parcela == null || c.respondidos < RESPOSTAS_MINIMAS
    ? `<p class="fraco">A estimativa aparece a partir de ${RESPOSTAS_MINIMAS} respostas. Antes disso, ela enganaria mais do que ajudaria.</p>`
    : `<span class="grande">${pct(e.parcela)}</span><p>do valor segue real, entre ${pct(e.baixo)} e ${pct(e.alto)}: de ${milhoes(c.valor_real.baixo)} a ${milhoes(c.valor_real.alto)}.</p>${c.respondidos < c.amostra ? `<p class="fraco">Estimativa parcial, com ${c.respondidos} de ${c.amostra} respostas.</p>` : ""}`;
  return `<section class="leitura">
    <h3>Quanto dos ${milhoes(c.valor_total)} parados ainda é real?</h3>
    <div class="progresso" role="img" aria-label="${c.respondidos} de ${c.amostra} respostas"><span style="transform: scaleX(${c.respondidos / c.amostra})"></span></div>
    <p class="fraco"><span class="num">${c.respondidos}</span> de <span class="num">${c.amostra}</span> respostas</p>
    ${estimativa}
    <p>${h(textos[c.decisao])}</p>
    <div class="acoes"><a class="botao" href="/api/limpeza.csv?modo=${modo()}">Baixar lista para o RevOps</a></div>
  </section>`;
}

function blocoPlacar(p) {
  const textos = { ajuda: "O destaque ajudou.", atrapalha: "O destaque atrapalhou.", sem_diferenca: "Não apareceu diferença clara." };
  let corpo;
  if (!p.completo) {
    const feito = Math.min(p.destaque.n, p.controle.n);
    corpo = `<div class="progresso" role="img" aria-label="${feito} de ${p.meta_por_grupo} por grupo"><span style="transform: scaleX(${Math.min(1, feito / p.meta_por_grupo)})"></span></div>
      <p class="fraco"><span class="num">${feito}</span> de <span class="num">${p.meta_por_grupo}</span> por grupo com ${p.dias_acompanhamento} dias completos</p>
      <p>Sem veredito até a meta, para ninguém decidir espiando um resultado parcial. Hoje há <span class="num">${p.sorteados.destaque}</span> negócios em destaque e <span class="num">${p.sorteados.controle}</span> sem destaque. Os novos entram no sorteio conforme chegam do CRM.</p>
      <p class="fraco">Resultados registrados até agora: <span class="num">${p.registrados}</span>.</p>`;
  } else {
    corpo = `<span class="grande">${(100 * p.diferenca.valor >= 0 ? "+" : "") + (100 * p.diferenca.valor).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} pontos</span>
      <p><strong>${h(textos[p.veredito])}</strong> Ganho em ${p.dias_acompanhamento} dias: ${pct(p.destaque.taxa, 1)} com destaque, ${pct(p.controle.taxa, 1)} sem. A diferença real fica entre ${(100 * p.diferenca.baixo).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} e ${(100 * p.diferenca.alto).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} pontos.</p>
      <p class="fraco">Por vendedor: ${p.vendedores.favor} a favor e ${p.vendedores.contra} contra.</p>`;
  }
  return `<section class="leitura">
    <h3>Destacar um negócio muda o resultado?</h3>
    ${corpo}
    <p class="fraco">Este teste mostra se o destaque desloca resultado entre negócios. Ele sozinho não prova que a receita total cresce.</p>
  </section>`;
}

function tabelaPorteiro(porteiro, plantado) {
  const linhas = Object.entries(porteiro).map(([nome, r]) => `<tr>
    <th scope="row">${h(nome[0].toUpperCase() + nome.slice(1))}</th>
    <td class="num">${r.auc.toFixed(3).replace(".", ",")}</td>
    <td class="num">${r.baixo.toFixed(3).replace(".", ",")} a ${r.alto.toFixed(3).replace(".", ",")}</td>
    <td class="${r.aberto ? "estado-aberto" : "estado-fechado"}">${r.aberto ? "Pode entrar" : "Ainda não provou"}</td>
  </tr>`).join("");
  const semEfeito = plantado[0];
  const forte = plantado.find((p) => p.abriu === p.repeticoes);
  return `<div class="tabela-rolo"><table>
    <thead><tr><th>Critério</th><th class="dir">Acerto no mês seguinte</th><th class="dir">Faixa provável</th><th>Situação</th></tr></thead>
    <tbody>${linhas}</tbody>
  </table></div>
  <p class="nota-rodape">0,50 equivale a sorte. O critério só entra se a faixa inteira ficar acima de 0,53. Com o efeito plantado em testes, o porteiro abriu ${semEfeito.abriu} de ${semEfeito.repeticoes} vezes sem efeito e ${forte.abriu} de ${forte.repeticoes} vezes com ${Math.round(forte.diferenca_real_pp)} pontos de diferença. Efeitos pequenos, perto de 7 pontos, passam despercebidos.</p>`;
}

function tabelaCenarios(cenarios) {
  return `<div class="tabela-rolo"><table>
    <thead><tr><th>Para detectar</th><th class="dir">Negócios no teste</th><th class="dir">Semanas de entrada</th><th class="dir">Semanas até a resposta</th></tr></thead>
    <tbody>${Object.entries(cenarios).map(([nome, c]) => `<tr><th scope="row">${h(nome.replace("pp", " pontos"))}</th><td class="num">${inteiro(c.total)}</td><td class="num">${Math.round(c.semanas_de_entrada)}</td><td class="num">${Math.round(c.semanas_com_90d)}</td></tr>`).join("")}</tbody>
  </table></div>
  <p class="nota-rodape">Calculado sobre a taxa histórica de ganho em 90 dias e cerca de 192 negócios novos por semana.</p>`;
}

function tabelaReplay(r) {
  const ordem = Object.entries(r.valor_ganho).sort((a, b) => b[1] - a[1]);
  return `<div class="tabela-rolo"><table>
    <thead><tr><th>Forma de escolher</th><th class="dir">Valor ganho nos 60 dias seguintes</th></tr></thead>
    <tbody>${ordem.map(([nome, valor]) => `<tr><th scope="row">${h(nome[0].toUpperCase() + nome.slice(1))}</th><td class="num">${dinheiro(valor)}</td></tr>`).join("")}</tbody>
  </table></div>
  <p class="nota-rodape">A fila aberta em ${r.datas} datas de 2017, com os ${r.por_vendedor} primeiros de cada vendedor. Mostra o que aquelas listas teriam incluído, não o efeito de agir de outro jeito. A lista usa preço sem parados, com o negócio mais antigo no empate: as duas versões ganharam ${r.deals_ganhos["preço sem parados"]} negócios, e a diferença de valor vem só do empate.</p>`;
}

async function telaHead() {
  const manager = param("manager", "");
  const regiao = param("regiao", "");
  const consulta = new URLSearchParams({ modo: modo() });
  if (manager) consulta.set("manager", manager);
  if (regiao) consulta.set("regiao", regiao);
  const d = await buscar("/api/head?" + consulta);
  const opcoes = (lista, atual) => `<option value="">Todos</option>` + lista.map((v) => `<option value="${h(v)}" ${v === atual ? "selected" : ""}>${h(v)}</option>`).join("");
  const p = d.pipeline;
  conteudo.innerHTML = `
    <div class="topo">
      <div><h1>O pipeline, e o que já foi provado</h1><p class="fraco">Nada aqui prevê quem vai fechar. Esta tela mostra o que os dados sustentam e o que ainda está em teste.</p></div>
      <div class="filtros">
        <label>Região<select id="regiao">${opcoes(estado.filtros.regioes, regiao)}</select></label>
        <label>Manager<select id="manager">${opcoes(estado.filtros.managers, manager)}</select></label>
      </div>
    </div>
    <section class="secao">
      <dl class="medidas">
        <div class="medida"><dt>Ativos</dt><dd><span class="valor">${inteiro(p.ativos)}</span><span class="apoio">${milhoes(p.ativos_valor)} a preço de tabela</span></dd></div>
        <div class="medida"><dt>Parados há mais de ${p.limite} dias</dt><dd><span class="valor">${inteiro(p.parados)}</span><span class="apoio">${milhoes(p.parados_valor)} a preço de tabela</span></dd></div>
        <div class="medida"><dt>Ainda não trabalhados</dt><dd><span class="valor">${inteiro(p.qualificar)}</span><span class="apoio">${milhoes(p.qualificar_valor)} a preço de tabela</span></dd></div>
      </dl>
    </section>
    <section class="secao">
      <div class="secao-cab"><h2>Testes em andamento</h2><p>Os dois valem para a empresa inteira, mesmo com filtro de região ou manager.</p></div>
      <div class="colunas">${blocoChecagem(d.checagem)}${blocoPlacar(d.placar)}</div>
    </section>
    ${modo() === "demo" ? `<section class="secao"><div class="secao-cab"><h2>Simulador</h2><p>Só altera o banco de demonstração.</p></div>
      <form class="simulador" id="simulador">
        <label>Parcela viva, em %<input type="number" id="viva" min="0" max="100" value="20" inputmode="numeric"></label>
        <label>Efeito do destaque, em pontos<input type="number" id="efeito" min="-50" max="50" value="10" inputmode="numeric"></label>
        <button class="primario" type="submit">Simular respostas</button>
        <button type="button" id="limpar">Limpar demonstração</button>
      </form></section>` : ""}
    <section class="secao"><div class="secao-cab"><h2>Porteiro de critérios</h2><p>Um critério só entra na nota se prever o mês seguinte com dados que já existiam antes.</p></div>${tabelaPorteiro(d.porteiro, d.porteiro_plantado)}</section>
    <section class="secao"><div class="secao-cab"><h2>Por que a lista usa esta regra</h2><p>Quatro regras testadas na fila histórica, além de um sorteio.</p></div>${tabelaReplay(d.replay)}</section>
    <section class="secao"><div class="secao-cab"><h2>Quanto tempo leva para saber</h2><p>Efeitos menores pedem mais negócios e mais tempo.</p></div>${tabelaCenarios(d.cenarios)}</section>
  `;
  document.getElementById("regiao").addEventListener("change", (e) => { definir({ regiao: e.target.value }); renderizar(); });
  document.getElementById("manager").addEventListener("change", (e) => { definir({ manager: e.target.value }); renderizar(); });
  const simulador = document.getElementById("simulador");
  if (simulador) {
    simulador.addEventListener("submit", async (e) => {
      e.preventDefault();
      await enviar("/api/demo/simular", { viva: Number(document.getElementById("viva").value) / 100, efeito: Number(document.getElementById("efeito").value) / 100 });
      await renderizar();
      aviso("Respostas simuladas.");
    });
    document.getElementById("limpar").addEventListener("click", async () => {
      await enviar("/api/demo/limpar", {});
      await renderizar();
      aviso("Demonstração limpa.");
    });
  }
}

async function renderizar(mostrarCarregando = true) {
  const tela = param("tela", "semana");
  document.querySelectorAll(".aba").forEach((aba) => {
    const q = new URLSearchParams(estado.consulta);
    q.set("tela", aba.dataset.tela);
    aba.href = "?" + q;
    if (aba.dataset.tela === tela) aba.setAttribute("aria-current", "page");
    else aba.removeAttribute("aria-current");
  });
  document.getElementById("modo").value = modo();
  document.getElementById("aviso-demo").hidden = modo() !== "demo";
  if (mostrarCarregando) carregando();
  try {
    if (!estado.filtros) estado.filtros = await buscar("/api/filtros");
    await (tela === "head" ? telaHead() : telaSemana());
  } catch (erro) {
    mostrarErro(erro, () => renderizar());
  }
}

document.getElementById("modo").addEventListener("change", (e) => {
  definir({ modo: e.target.value === "demo" ? "demo" : "" });
  renderizar();
});
document.querySelectorAll(".aba").forEach((aba) => aba.addEventListener("click", (e) => {
  e.preventDefault();
  definir({ tela: aba.dataset.tela });
  renderizar();
}));
renderizar();
