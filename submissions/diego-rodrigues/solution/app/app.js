'use strict';

const ESTADO = {
  scored: null, qualidade: null, evalj: null, briefings: null,
  acoes: [], modoDemo: false, vendedor: null,
};
const FILAS = ['fechar', 'preparar', 'iniciar', 'encerrar'];
const NOME_FILA = { fechar: 'Fechar', preparar: 'Preparar', iniciar: 'Iniciar', encerrar: 'Encerrar' };
const DICA_FILA = {
  fechar: 'têm chance medida de decidir nas próximas quatro semanas',
  preparar: 'vivos que decidem mais tarde no trimestre',
  iniciar: 'sem data de engajamento',
  encerrar: 'passaram da janela de decisão',
};
const ROTULO_ACAO = { feito: 'Feito', adiar: 'Adiar', nao_vivo: 'Não está vivo' };
const TEXTO_ACAO_FEITA = {
  feito: 'Marcado como feito.',
  adiar: 'Adiado.',
  nao_vivo: 'Marcado como não vivo.',
};
const CHAVE_LOCAL = 'lead-scorer-acoes';

const $ = (s, raiz = document) => raiz.querySelector(s);
const nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf3 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 3, maximumFractionDigits: 3 });
const usd = v => 'US$ ' + nf.format(v);
const pct = v => nf.format(Math.round(v * 100)) + '%';
const dataBr = iso => iso.split('-').reverse().join('/');

function h(tag, props = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === false || v == null) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, '');
    else e.setAttribute(k, v);
  }
  for (const f of filhos.flat(Infinity)) {
    if (f == null || f === false) continue;
    e.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return e;
}

async function carregarJson(caminho) {
  try {
    const r = await fetch(caminho, { cache: 'no-store' });
    return r.ok ? await r.json() : null;
  } catch (_) {
    return null;
  }
}

/* ações: servidor local quando existe, navegador quando não */

function lerLocais() {
  try { return JSON.parse(localStorage.getItem(CHAVE_LOCAL) || '[]'); } catch (_) { return []; }
}
function gravarLocal(registro) {
  try {
    const todas = lerLocais();
    todas.push(registro);
    localStorage.setItem(CHAVE_LOCAL, JSON.stringify(todas));
  } catch (_) { /* navegador sem armazenamento: a ação vale só nesta sessão */ }
}

const SERVIDOR_LOCAL = ['localhost', '127.0.0.1', '[::1]'].includes(location.hostname);

async function carregarAcoes() {
  ESTADO.modoDemo = !SERVIDOR_LOCAL;
  if (ESTADO.modoDemo) {
    ESTADO.acoes = lerLocais();
    return;
  }
  try {
    const r = await fetch('acoes', { cache: 'no-store' });
    if (r.ok) {
      ESTADO.acoes = await r.json();
      return;
    }
  } catch (_) { /* servidor local ausente: cai no modo demo */ }
  ESTADO.modoDemo = true;
  ESTADO.acoes = lerLocais();
}

function avisar(texto) {
  $('#aviso').textContent = texto;
}

async function registrarAcao(vendedor, opportunityId, acao) {
  const corpo = { vendedor, opportunity_id: opportunityId, acao };
  let registro = null;
  if (!ESTADO.modoDemo) {
    try {
      const r = await fetch('acao', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo),
      });
      if (r.status === 201) registro = await r.json();
      else if (r.status === 400) {
        const erro = await r.json().catch(() => ({}));
        avisar('Não gravei a ação: ' + (erro.erro || 'o servidor recusou o pedido.'));
        return;
      }
    } catch (_) { /* servidor ausente: segue para o navegador */ }
  }
  if (!registro) {
    registro = { ...corpo, ts: new Date().toISOString() };
    gravarLocal(registro);
    ESTADO.modoDemo = true;
    $('#faixa-demo').hidden = false;
    avisar('Ação salva só neste navegador.');
  } else {
    avisar(TEXTO_ACAO_FEITA[acao]);
  }
  ESTADO.acoes.push(registro);
  renderSegunda();
}

function acaoDoDeal(oid) {
  const feitas = ESTADO.acoes.filter(a => a.opportunity_id === oid);
  return feitas.length ? feitas[feitas.length - 1].acao : null;
}

/* topo */

function renderTopo() {
  const s = ESTADO.scored;
  $('#topo-data').textContent = 'Dados de ' + dataBr(s.hoje);
  const total = Math.max(13, s.semana_do_trimestre);
  const lista = $('#relogio-semanas');
  lista.replaceChildren();
  for (let i = 1; i <= total; i++) {
    lista.append(h('li', { class: i < s.semana_do_trimestre ? 'passada' : i === s.semana_do_trimestre ? 'atual' : '' }));
  }
  $('#relogio-legenda').replaceChildren(
    h('strong', {}, 'Semana ' + s.semana_do_trimestre + ' de ' + total + '.'),
    ' A janela de decisão deste negócio tem forma de trimestre.',
  );
}

/* tela 1: segunda-feira */

function ordenarVendedores() {
  return [...ESTADO.scored.vendedores].sort((a, b) =>
    b.por_fila.fechar - a.por_fila.fechar || b.vivos - a.vivos || a.vendedor.localeCompare(b.vendedor, 'pt-BR'));
}

function preencherSeletorVendedor() {
  const sel = $('#sel-vendedor');
  sel.replaceChildren();
  for (const v of ordenarVendedores()) {
    const resumo = v.por_fila.fechar > 0
      ? `${v.por_fila.fechar} para fechar, ${v.vivos} vivos`
      : v.vivos > 0 ? `${v.vivos} vivos` : v.tem_deal ? 'sem deal vivo' : 'sem deal no export';
    sel.append(h('option', { value: v.vendedor }, `${v.vendedor} (${resumo})`));
  }
  const dica = decodeURIComponent((location.hash.split('=')[1] || ''));
  const existe = ESTADO.scored.vendedores.some(v => v.vendedor === dica);
  ESTADO.vendedor = existe ? dica : sel.options[0].value;
  sel.value = ESTADO.vendedor;
  sel.addEventListener('change', () => {
    ESTADO.vendedor = sel.value;
    history.replaceState(null, '', '#segunda=' + encodeURIComponent(ESTADO.vendedor));
    renderSegunda();
  });
}

function textoBriefing(v) {
  const b = ESTADO.briefings && ESTADO.briefings.vendedores && ESTADO.briefings.vendedores[v.vendedor];
  if (b) return { texto: b.texto, origem: b.origem };
  return { texto: v.vivos === 0 ? `${v.vendedor}. ${v.frase_vazio}` : `${v.vendedor}, você tem ${v.vivos} deals vivos nesta semana.`, origem: 'template' };
}

function linhaFato(rotulo, valor) {
  return h('div', {}, h('dt', {}, rotulo), h('dd', {}, valor));
}

function cartaoPorQue(d) {
  return h('details', {},
    h('summary', {}, 'Por que este deal'),
    h('div', { class: 'porque' },
      h('div', {}, h('h4', {}, 'Valor'), h('p', {}, d.cartoes.valor)),
      h('div', {}, h('h4', {}, 'Momento'), h('p', {}, d.cartoes.momento)),
      h('div', {}, h('h4', {}, 'Prazo'), h('p', {}, d.cartoes.prazo)),
      h('div', {}, h('h4', {}, 'O que o score não sabe'),
        h('ul', { class: 'nao-sabe' }, d.nao_sabe.map(t => h('li', {}, t)))),
    ),
  );
}

function blocoAcoes(d) {
  const feita = acaoDoDeal(d.opportunity_id);
  if (feita) return h('p', { class: 'acao-feita' }, TEXTO_ACAO_FEITA[feita]);
  return h('div', { class: 'acoes' },
    Object.entries(ROTULO_ACAO).map(([acao, rotulo]) =>
      h('button', { type: 'button', onclick: () => registrarAcao(d.vendedor, d.opportunity_id, acao) }, rotulo)));
}

function itemFoco(d) {
  const fatos = [
    linhaFato('Valor de tabela', usd(d.valor_tabela)),
    d.idade != null ? linhaFato('Idade', d.idade + ' dias') : null,
    d.dias_restantes != null ? linhaFato('Prazo', d.dias_restantes + ' dias') : null,
    d.p_decide != null ? linhaFato('Chance de decidir em 28 dias', pct(d.p_decide)) : null,
  ];
  return h('li', { class: 'deal fila-' + d.fila },
    h('div', { class: 'deal-topo' },
      h('span', { class: 'selo' }, NOME_FILA[d.fila]),
      h('h3', {}, d.verbo),
    ),
    h('p', { class: 'deal-alvo' },
      h('strong', {}, d.produto), ' em ', d.conta ? d.conta : 'conta não registrada no CRM'),
    h('dl', { class: 'fatos' }, fatos),
    blocoAcoes(d),
    cartaoPorQue(d),
  );
}

function blocoFila(fila, deals, v) {
  const n = v.por_fila[fila];
  const valor = v.valor_por_fila[fila];
  return h('details', { class: 'bloco' },
    h('summary', {},
      h('span', { class: 'bloco-nome' }, NOME_FILA[fila]),
      h('span', { class: 'bloco-resumo' }, `${n} ${n === 1 ? 'deal' : 'deals'}, ${usd(valor)} de tabela`),
    ),
    n === 0
      ? h('p', { class: 'mudo' }, 'Nenhum deal nesta fila.')
      : h('ul', { class: 'linhas' }, deals.map(d => h('li', {},
          h('span', {}, d.produto),
          h('span', { class: 'mudo' }, d.conta || 'sem conta'),
          h('span', {}, usd(d.valor_tabela)),
          h('span', { class: 'mudo' }, d.idade != null ? d.idade + ' dias' : 'sem data'),
        ))),
  );
}

function renderSegunda() {
  const s = ESTADO.scored;
  const v = s.vendedores.find(x => x.vendedor === ESTADO.vendedor);
  const deals = s.deals.filter(d => d.vendedor === v.vendedor)
    .sort((a, b) => a.fila_ordem - b.fila_ordem || a.posicao - b.posicao);
  const foco = deals.filter(d => d.em_foco);
  const { texto, origem } = textoBriefing(v);

  const corpo = $('#segunda-corpo');
  corpo.replaceChildren();
  corpo.append(
    h('p', { class: 'briefing' }, texto),
    h('p', { class: 'origem' }, origem === 'ia' ? 'Texto escrito por IA e validado contra os fatos.' : 'Texto gerado por modelo fixo, sem IA.'),
  );

  if (!v.tem_deal) {
    corpo.append(h('div', { class: 'nota' },
      h('p', {}, h('strong', {}, 'Sem histórico.')),
      h('p', {}, 'Este vendedor não aparece em nenhum deal do export, então não há fila nem carga de referência para mostrar.'),
    ));
  } else if (v.vivos === 0) {
    corpo.append(h('div', { class: 'nota' },
      h('p', {}, h('strong', {}, 'Nada vivo nesta semana.')),
      h('p', {}, `Nos trimestres anteriores, ${nf.format(v.carga_referencia)} deals por vendedor, em mediana, estavam abertos nesta altura e depois fecharam. A lista abaixo é o que existe para trabalhar.`),
    ));
  } else if (v.por_fila.fechar === 0) {
    corpo.append(h('div', { class: 'nota' },
      h('p', {}, h('strong', {}, 'Nenhum deal com chance medida de decidir nas próximas quatro semanas.')),
      h('p', {}, 'Nesta semana do trimestre, deals vivos decidem mais tarde. Use o tempo para avançar uma etapa nos que estão em foco.'),
    ));
  }

  if (foco.length) {
    corpo.append(h('h2', { id: 'foco-titulo' }, 'Foco da semana'));
    corpo.append(h('ol', { class: 'foco', 'aria-labelledby': 'foco-titulo' }, foco.map(itemFoco)));
  }

  if (deals.length) {
    corpo.append(h('h2', {}, 'Todas as filas'));
    for (const fila of FILAS) corpo.append(blocoFila(fila, deals.filter(d => d.fila === fila), v));
  }
}

/* tela 2: o time */

function opcoes(sel, valores, textoTodos) {
  sel.replaceChildren(h('option', { value: '' }, textoTodos), ...valores.map(x => h('option', { value: x }, x)));
}

function preencherFiltros() {
  const vs = ESTADO.scored.vendedores;
  const unicos = f => [...new Set(vs.map(f))].sort((a, b) => a.localeCompare(b, 'pt-BR'));
  opcoes($('#f-regiao'), unicos(v => v.regiao), 'Todas as regiões');
  opcoes($('#f-gerente'), unicos(v => v.gerente), 'Todos os gerentes');
  opcoes($('#f-vendedor'), unicos(v => v.vendedor), 'Todos os vendedores');
  for (const id of ['#f-regiao', '#f-gerente', '#f-vendedor']) $(id).addEventListener('change', renderTime);
}

function vendedoresFiltrados() {
  const r = $('#f-regiao').value, g = $('#f-gerente').value, n = $('#f-vendedor').value;
  return ESTADO.scored.vendedores.filter(v =>
    (!r || v.regiao === r) && (!g || v.gerente === g) && (!n || v.vendedor === n));
}

function tabelaTime(vs) {
  const cab = ['Vendedor', 'Gerente', 'Região', 'Fechar', 'Preparar', 'Iniciar', 'Encerrar', 'Valor vivo', 'Valor vencido', 'Carga de referência'];
  return h('div', { class: 'rolagem' }, h('table', { class: 'larga' },
    h('caption', {}, `${vs.length} vendedores`),
    h('thead', {}, h('tr', {}, cab.map(c => h('th', { scope: 'col' }, c)))),
    h('tbody', {}, vs.map(v => {
      const valorVivo = ESTADO.scored.deals.filter(d => d.vendedor === v.vendedor && d.estado === 'vivo')
        .reduce((a, d) => a + d.valor_tabela, 0);
      return h('tr', { class: v.tem_deal ? '' : 'sem-deal' },
        h('th', { scope: 'row' }, v.vendedor, v.tem_deal ? null : h('span', { class: 'mudo sub' }, 'sem nenhum deal no export')),
        h('td', {}, v.gerente), h('td', {}, v.regiao),
        FILAS.map(f => h('td', {}, nf.format(v.por_fila[f]))),
        h('td', {}, usd(valorVivo)),
        h('td', {}, usd(v.valor_por_fila.encerrar)),
        h('td', {}, v.tem_deal ? nf.format(v.carga_referencia) : 'sem histórico'),
      );
    })),
  ));
}

function blocoAdocao(vs) {
  const nomes = new Set(vs.map(v => v.vendedor));
  const filaDe = new Map(ESTADO.scored.deals.map(d => [d.opportunity_id, d.fila]));
  const acoes = ESTADO.acoes.filter(a => nomes.has(a.vendedor));
  if (!acoes.length) {
    return h('div', { class: 'bloco-tela' }, h('h3', {}, 'Adoção'),
      h('p', {}, 'Ainda não há ações registradas. Quando os vendedores marcarem Feito, Adiar ou Não está vivo, aparecem aqui as contagens por fila e a taxa de discordância.'));
  }
  const porFila = FILAS.map(f => [f, acoes.filter(a => filaDe.get(a.opportunity_id) === f).length]);
  const naoVivo = acoes.filter(a => a.acao === 'nao_vivo').length;
  const textoAcoes = n => `${n} ${n === 1 ? 'ação' : 'ações'}`;
  return h('div', { class: 'bloco-tela' }, h('h3', {}, 'Adoção'),
    h('p', {}, `${new Set(acoes.map(a => a.vendedor)).size} de ${vs.length} vendedores com ao menos uma ação.`),
    h('ul', { class: 'lista-simples' }, porFila.map(([f, n]) => h('li', {}, `${NOME_FILA[f]}: ${textoAcoes(n)}`))),
    h('p', {}, `Discordância (marcaram "Não está vivo"): ${pct(naoVivo / acoes.length)} de ${textoAcoes(acoes.length)}.`),
  );
}

function blocoQualidade() {
  const q = ESTADO.qualidade;
  if (!q) return null;
  const apelidos = Object.entries(q.apelidos_de_produto || {}).map(([a, b]) => `${a} no CRM aparece como ${b} no catálogo`);
  const itens = [
    ...apelidos,
    ...Object.entries(q.setores_corrigidos || {}).map(([a, b]) => `Setor "${a}" corrigido para "${b}"`),
    ...Object.entries(q.paises_corrigidos || {}).map(([a, b]) => `País "${a}" corrigido para "${b}"`),
    `${nf.format(q.abertos_sem_conta)} deals abertos sem conta no CRM`,
    `${nf.format(q.prospecting_sem_data)} deals em Prospecting sem data de engajamento`,
    `${(q.vendedores_sem_deal || []).length} vendedores do cadastro sem nenhum deal: ${(q.vendedores_sem_deal || []).join(', ')}`,
  ];
  if ((q.produtos_sem_par || []).length) itens.push('Produtos sem par no catálogo: ' + q.produtos_sem_par.join(', '));
  return h('div', { class: 'bloco-tela' }, h('h3', {}, 'Qualidade do dado'),
    h('ul', { class: 'lista-simples' }, itens.map(t => h('li', {}, t))));
}

function blocoResumoGestor() {
  const gestores = ESTADO.briefings && ESTADO.briefings.gestores;
  if (!gestores) return null;
  const g = $('#f-gerente').value;
  const nomes = Object.keys(gestores).filter(n => !g || n === g).sort((a, b) => a.localeCompare(b, 'pt-BR'));
  return h('div', { class: 'bloco-tela' }, h('h3', {}, 'Resumo por gerente'),
    h('div', { class: 'resumos' }, nomes.map(n => h('div', { class: 'resumo' }, h('h4', {}, n), h('p', {}, gestores[n].texto)))));
}

function renderTime() {
  const vs = vendedoresFiltrados();
  const t = ESTADO.scored.time;
  const comVivo = vs.filter(v => v.vivos > 0).length;
  const corpo = $('#time-corpo');
  corpo.replaceChildren(
    h('div', { class: 'bloco-tela' }, h('h3', {}, 'Cobertura'),
      h('p', {}, `${comVivo} de ${vs.length} vendedores têm ao menos um deal vivo. No time inteiro, ${pct(t.pct_vencido)} do valor de tabela aberto (${usd(t.valor_vencido)} de ${usd(t.valor_aberto)}) já passou da janela de decisão.`)),
    tabelaTime(vs),
    blocoAdocao(vs),
    blocoResumoGestor(),
    blocoQualidade(),
  );
}

/* tela 3: como decide */

function tabelaSimples(titulo, colunas, linhas) {
  return h('div', { class: 'rolagem' }, h('table', {},
    h('caption', {}, titulo),
    h('thead', {}, h('tr', {}, colunas.map(c => h('th', { scope: 'col' }, c)))),
    h('tbody', {}, linhas.map(l => h('tr', {}, l.map((c, i) => i === 0 ? h('th', { scope: 'row' }, c) : h('td', {}, c))))),
  ));
}

function renderComoDecide() {
  const s = ESTADO.scored;
  const e = ESTADO.evalj;
  const corpo = $('#como-corpo');
  corpo.replaceChildren();

  corpo.append(h('div', { class: 'bloco-tela' },
    h('h3', {}, 'Quando um deal costuma decidir'),
    h('p', {}, `Aprendido nas datas ${s.datas_analogas.map(dataBr).join(', ')}: para cada deal que estava aberto, o que aconteceu nas quatro semanas seguintes e até o fim do trimestre.`),
    tabelaSimples('Por faixa de idade', ['Faixa (dias)', 'Deals observados', 'Decidem em 28 dias', 'Ganham até o fim do trimestre', 'Faixa juntada'],
      s.tabela_destino.map(f => [f.faixa, nf.format(f.n), pct(f.p_decide), pct(f.p_ganha_trimestre), f.agrupada ? 'sim' : 'não'])),
    h('p', {}, `Ciclo máximo observado: ${s.janela.ciclo_max} dias. A regra do fim do trimestre seguinte está ${s.janela.usa_prazo_trimestre ? 'ativa' : 'desligada'} (${s.janela.fechamentos_apos_prazo} de ${nf.format(s.janela.n_fechamentos)} fechamentos passaram desse prazo).`),
  ));

  if (!e) {
    corpo.append(h('div', { class: 'nota' }, h('p', {}, 'Os resultados do teste de volta ao passado não estão disponíveis. Gere com python -m avaliacao.numeros.')));
  } else {
    const nomes = { relogio: 'Relógio (a ferramenta)', preco_prazo: 'Preço e prazo', preco_138: 'Preço até 138 dias', aleatorio: 'Aleatório (média)', oraculo: 'Oráculo (conhece o futuro)' };
    const chaves = Object.keys(nomes);
    corpo.append(h('div', { class: 'bloco-tela' },
      h('h3', {}, 'O teste de volta ao passado'),
      h('p', {}, 'Em cada data, a ferramenta vê só o que existia naquele dia. Depois medimos quanto cada ordem teria ganho nas quatro semanas seguintes, com 5 deals por vendedor.'),
      tabelaSimples('Valor ganho por data de corte (US$)', ['Corte', 'Semana do trimestre', ...chaves.map(c => nomes[c])],
        e.tabela.map(l => [dataBr(l.corte), l.semana_do_trimestre, ...chaves.map(c => nf.format(l['valor_' + c]))])),
      tabelaSimples('Três medidas, somando os cortes', ['Política', 'Valor ganho (US$)', 'Taxa de acerto', 'Fração do teto'],
        chaves.map(c => [nomes[c], nf.format(e.somas['valor_' + c]), pct(e.acerto_medio['acerto_' + c]),
          e.somas.valor_oraculo ? pct(e.somas['valor_' + c] / e.somas.valor_oraculo) : ''])),
      h('ul', { class: 'lista-simples' }, Object.entries(e.razoes).map(([k, r]) => {
        const [a, b] = k.split(' / ');
        return h('li', {}, `${nomes[a]} sobre ${nomes[b].toLowerCase()}: ${nf2.format(r.razao)} vezes (intervalo de confiança de 95%: ${nf2.format(r.ic_inferior)} a ${nf2.format(r.ic_superior)}).`);
      })),
    ));

    const linhasPerm = Object.entries(e.permutacao).map(([nome, v]) => [nome, nf3.format(v.p), v.sinal ? 'tem sinal' : 'sem sinal']);
    const vc = e.permutacao_vendedor_controlado_por_gerente;
    linhasPerm.push(['vendedor, controlado também por gerente', nf3.format(vc.p), vc.sinal ? 'tem sinal' : 'sem sinal']);
    const vz = e.vazamento_do_campo_conta;
    corpo.append(h('div', { class: 'bloco-tela' },
      h('h3', {}, 'Regras que testamos e descartamos'),
      h('p', {}, 'Cada atributo foi testado contra o resultado real, embaralhando os resultados mil vezes. Um p-valor abaixo de 0,05 indicaria sinal.'),
      tabelaSimples('Atributos do deal', ['Atributo', 'p-valor', 'Conclusão'], linhasPerm),
      h('p', {}, `O campo de conta só aparece nos deals que já têm desfecho: ${nf.format(vz.fechados_sem_conta)} dos ${nf.format(vz.fechados)} fechados estão sem conta, contra ${nf.format(vz.abertos_sem_conta)} dos ${nf.format(vz.abertos)} abertos. Por isso os testes usam só deals com conta, e a presença de conta nunca entra como sinal.`),
    ));
  }

  const cfg = s.config;
  corpo.append(h('div', { class: 'bloco-tela duas' },
    h('div', {},
      h('h3', {}, 'O que a ferramenta aprende'),
      h('ul', { class: 'lista-simples' },
        h('li', {}, `Ciclo máximo de um deal: ${s.janela.ciclo_max} dias.`),
        h('li', {}, 'Se o fim do trimestre seguinte encerra o deal.'),
        h('li', {}, 'A chance de decidir por faixa de idade, nas datas análogas.'),
        h('li', {}, 'A carga de deals que cada vendedor costuma ter.'))),
    h('div', {},
      h('h3', {}, 'O que é configuração'),
      h('ul', { class: 'lista-simples' },
        h('li', {}, `Horizonte de ${cfg.horizonte_dias} dias.`),
        h('li', {}, `${cfg.foco_por_vendedor} deals em foco por vendedor.`),
        h('li', {}, `Chance mínima de ${pct(cfg.p_decide_min)} para entrar em fechar.`),
        h('li', {}, `Faixas juntadas quando têm menos de ${cfg.n_min_faixa} deals.`))),
  ));

  const naoSabe = [...new Set(s.deals.flatMap(d => d.nao_sabe))];
  corpo.append(h('div', { class: 'bloco-tela' },
    h('h3', {}, 'O que a ferramenta não sabe'),
    h('ul', { class: 'lista-simples' }, naoSabe.map(t => h('li', {}, t))),
  ));
}

/* navegação */

function mostrarTela() {
  const nome = (location.hash.slice(1).split('=')[0]) || 'segunda';
  const valida = ['segunda', 'time', 'como-decide'].includes(nome) ? nome : 'segunda';
  for (const sec of document.querySelectorAll('.tela')) sec.hidden = sec.id !== 'tela-' + valida;
  for (const a of document.querySelectorAll('.abas a')) {
    if (a.dataset.tela === valida) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  }
  avisar('');
  if (valida === 'time') renderTime();
  if (valida === 'como-decide') renderComoDecide();
}

async function iniciar() {
  const [scored, qualidade, evalj, briefings] = await Promise.all([
    carregarJson('data/scored.json'), carregarJson('data/qualidade.json'),
    carregarJson('data/eval.json'), carregarJson('data/briefings.json'),
  ]);
  if (!scored) {
    $('#conteudo').replaceChildren(h('p', { class: 'tela' }, 'Não encontrei data/scored.json. Rode python run.py na pasta solution.'));
    return;
  }
  Object.assign(ESTADO, { scored, qualidade, evalj, briefings });
  await carregarAcoes();
  $('#faixa-demo').hidden = !ESTADO.modoDemo;
  renderTopo();
  preencherSeletorVendedor();
  preencherFiltros();
  renderSegunda();
  mostrarTela();
  window.addEventListener('hashchange', mostrarTela);
}

iniciar();
