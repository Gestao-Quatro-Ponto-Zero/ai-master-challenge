/**
 * Lead Scorer G4: API e job diário, vinculados à planilha sales_pipeline.
 *
 * A planilha é o motor (aba Hoje = relógio e regras, Lista do Dia = prioridade,
 * Fila Sem Conta, Visão Manager, KPIs Vendedor, Atividades = o que o app escreve).
 * Este script só lê e escreve nela. Nada de lógica de negócio aqui.
 *
 * GET  ?action=config                 relógio, modo, cortes, contagens
 * GET  ?action=users                  vendedores e managers (e-mail demo, papel)
 * GET  ?action=rep&email=...          KPIs + lista do dia + fila do vendedor
 * GET  ?action=manager&email=...      visão do manager (time, passos, alertas)
 * GET  ?action=snapshot               tudo de uma vez (o app usa como fallback)
 * POST {action:"activity", token, deal, rep, acao, valor, nota}   grava em Atividades
 *      acao = feito | ganho | perdido | separado (demanda separada confirmada) | recompra (deal = "Conta|Produto")
 * POST {action:"trigger", token, on: true|false}   liga ou desliga o job diário das 9h
 * POST {action:"advance", token}      anda o relógio um dia (simulação)
 * POST {action:"reset",   token}      volta o relógio pra 0 e limpa Atividades (demo)
 * POST {action:"notify",  token}      dispara as mensagens do dia agora
 *
 * dailyJob()       = advance + notify. installTrigger() agenda às 9h todo dia.
 * Token: propriedade de script API_TOKEN (setToken('...') uma vez).
 */

const TABS = {
  hoje: 'Hoje',
  lista: 'Lista do Dia',
  fila: 'Fila Sem Conta',
  manager: 'Visão Manager',
  kpis: 'KPIs Vendedor',
  atividades: 'Atividades',
  recompra: 'Recompra sem deal',
};

function ss() { return SpreadsheetApp.getActive(); }
function sheet(name) { return ss().getSheetByName(name); }

function setToken(token) { PropertiesService.getScriptProperties().setProperty('API_TOKEN', token); }
function getToken() { return PropertiesService.getScriptProperties().getProperty('API_TOKEN') || ''; }

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function iso(v) {
  if (v instanceof Date) return Utilities.formatDate(v, 'America/Sao_Paulo', 'yyyy-MM-dd');
  return v;
}

/** Lê um bloco com cabeçalho e devolve objetos {cabeçalho: valor}. */
function readTable(name, headerRow, firstCol, lastCol, maxRows) {
  const sh = sheet(name);
  let last = sh.getLastRow();
  if (maxRows) last = Math.min(last, headerRow + maxRows);
  if (last < headerRow + 1) return [];
  const width = lastCol - firstCol + 1;
  const values = sh.getRange(headerRow, firstCol, last - headerRow + 1, width).getValues();
  const headers = values[0].map(h => String(h).trim());
  const rows = [];
  for (let i = 1; i < values.length; i++) {
    const r = values[i];
    if (r[0] === '' || r[0] === null) continue;
    const o = {};
    headers.forEach((h, j) => { if (h) o[h] = iso(r[j]); });
    rows.push(o);
  }
  return rows;
}

function cell(name, a1) { return iso(sheet(name).getRange(a1).getValue()); }

function getConfig() {
  return {
    fimDosDados: cell(TABS.hoje, 'B2'),
    diasPassados: cell(TABS.hoje, 'B3'),
    hoje: cell(TABS.hoje, 'B4'),
    cicloNormal: cell(TABS.hoje, 'B5'),
    cicloMaisLongo: cell(TABS.hoje, 'B6'),
    janelaEntrando: cell(TABS.hoje, 'B7'),
    janelaPoucoFora: cell(TABS.hoje, 'B8'),
    modoDono: cell(TABS.hoje, 'B9'),
    prazoFilaDiasUteis: cell(TABS.hoje, 'B10'),
    requalificacaoDias: cell(TABS.hoje, 'B11'),
    dealsPorSemana: cell(TABS.hoje, 'B12'),
    ordemDentroDoPasso: cell(TABS.hoje, 'B13'),
    filaPorDia: cell(TABS.hoje, 'B14'),
    totais: {
      comConta: cell(TABS.hoje, 'B16'),
      passo1: cell(TABS.hoje, 'B17'),
      passo2: cell(TABS.hoje, 'B18'),
      passo3: cell(TABS.hoje, 'B19'),
      passo4: cell(TABS.hoje, 'B20'),
      semConta: cell(TABS.hoje, 'B21'),
      filaForaDoPrazo: cell(TABS.hoje, 'B22'),
      confirmar: cell(TABS.hoje, 'B23'),
    },
    triggerLigado: ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === 'dailyJob'),
  };
}

function getUsers() {
  const reps = readTable(TABS.kpis, 4, 1, 21).filter(r => r['Papel'] === 'vendedor').map(r => ({
    nome: r['Vendedor'], manager: r['Manager'], regiao: r['Região'],
    email: r['E-mail (demo)'], papel: r['Papel'],
  }));
  // managers ficam nas linhas 41 a 46 da mesma aba
  const sh = sheet(TABS.kpis);
  const m = sh.getRange(41, 1, 6, 5).getValues();
  m.forEach(r => { if (r[0]) reps.push({ nome: r[0], manager: r[1], regiao: r[2], email: r[3], papel: r[4] }); });
  return reps;
}

function findUser(email) {
  const e = String(email || '').toLowerCase().trim();
  return getUsers().find(u => String(u.email).toLowerCase() === e) || null;
}

function getLista() { return readTable(TABS.lista, 7, 1, 40); }
function getRecompra() { return readTable(TABS.recompra, 7, 1, 21); }
function getContas() {
  return sheet('Books').getRange(4, 1, 85, 1).getValues().map(r => String(r[0])).filter(Boolean).sort();
}
function getFila() { return readTable(TABS.fila, 7, 1, 15); }
function getKpis() { return readTable(TABS.kpis, 4, 1, 22, 35).filter(r => r['Papel'] === 'vendedor'); }
function getManagerRows() { return readTable(TABS.manager, 4, 1, 18, 35); }

function getRep(email) {
  const user = findUser(email);
  if (!user) return { error: 'usuário não encontrado', email };
  const nome = user.nome;
  const kpi = getKpis().find(r => r['Vendedor'] === nome) || null;
  const lista = getLista().filter(r => r['Trabalha hoje'] === nome)
    .sort((a, b) => Number(a['Ordem do dia']) - Number(b['Ordem do dia']));
  const fila = getFila().filter(r => r['Vendedor'] === nome)
    .sort((a, b) => Number(a['Ordem na fila']) - Number(b['Ordem na fila']));
  const recompra = getRecompra().filter(r => r['Dono (Books)'] === nome && (r['Entra na lista?'] === true || String(r['Entra na lista?']).toUpperCase() === 'TRUE'))
    .sort((a, b) => Number(a['Ordem (por dono)']) - Number(b['Ordem (por dono)']));
  const kpisTime = getKpis().filter(r => r['Manager'] === user.manager);
  return { user, config: getConfig(), kpi, kpisTime, lista, fila, recompra, contas: getContas() };
}

function getManager(email) {
  const user = findUser(email);
  if (!user) return { error: 'usuário não encontrado', email };
  const nome = user.nome;
  const time = getManagerRows().filter(r => r['Manager'] === nome);
  const sh = sheet(TABS.manager);
  const roll = sh.getRange(42, 1, 7, 12).getValues();
  const headers = roll[0];
  let resumo = null;
  for (let i = 1; i < roll.length; i++) {
    if (roll[i][0] === nome) { resumo = {}; headers.forEach((h, j) => resumo[h] = roll[i][j]); }
  }
  const nomes = time.map(r => r['Vendedor']);
  const lista = getLista().filter(r => nomes.indexOf(r['Trabalha hoje']) >= 0);
  const fila = getFila().filter(r => nomes.indexOf(r['Vendedor']) >= 0);
  const recompra = getRecompra().filter(r => nomes.indexOf(r['Dono (Books)']) >= 0 && (r['Entra na lista?'] === true || String(r['Entra na lista?']).toUpperCase() === 'TRUE'));
  const kpisTime = getKpis().filter(r => r['Manager'] === nome);
  return { user, config: getConfig(), time, resumo, kpisTime, lista, fila, recompra, contas: getContas() };
}

function getRevops() {
  const sh = sheet(TABS.manager);
  const roll = sh.getRange(42, 1, 7, 12).getValues();
  const headers = roll[0];
  const managers = [];
  for (let i = 1; i < roll.length; i++) { if (roll[i][0]) { const o = {}; headers.forEach((h, j) => o[h] = roll[i][j]); managers.push(o); } }
  return { config: getConfig(), reps: getManagerRows(), managers, recompra: getRecompra(), kpis: getKpis() };
}

function getSnapshot() {
  return {
    geradoEm: new Date().toISOString(),
    config: getConfig(),
    users: getUsers(),
    kpis: getKpis(),
    lista: getLista(),
    fila: getFila(),
    manager: getManagerRows(),
    recompra: getRecompra(),
  };
}

function doGet(e) {
  const p = (e && e.parameter) || {};
  try {
    switch (p.action) {
      case 'config': return json(getConfig());
      case 'users': return json(getUsers());
      case 'rep': return json(getRep(p.email));
      case 'manager': return json(getManager(p.email));
      case 'snapshot': return json(getSnapshot());
      case 'revops': return json(getRevops());
      default: return json({ ok: true, actions: ['config', 'users', 'rep', 'manager', 'snapshot'] });
    }
  } catch (err) {
    return json({ error: String(err) });
  }
}

function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents || '{}'); } catch (err) { return json({ error: 'JSON inválido' }); }
  // Primeira chamada, uma vez só: grava o token e agenda o job das 9h. Depois disso, 'setup' exige o token.
  if (body.action === 'setup' && body.token) {
    if (getToken() && body.token !== getToken()) return json({ error: 'token inválido' });
    setToken(body.token);
    let trigger = 'ok';
    try { installTrigger(); } catch (err) { trigger = 'falhou: ' + err; }
    return json({ ok: true, token: 'gravado', trigger });
  }
  if (!getToken() || body.token !== getToken()) return json({ error: 'token inválido' });
  try {
    switch (body.action) {
      case 'activity': return json(recordActivity(body));
      case 'conta': return json(recordConta(body));
      case 'advance': return json(advanceDay());
      case 'reset': return json(resetDemo());
      case 'notify': return json(notifyAll());
      case 'trigger': return json(setTrigger(body.on === true || body.on === 'true'));
      default: return json({ error: 'ação desconhecida' });
    }
  } catch (err) {
    return json({ error: String(err) });
  }
}

/**
 * Grava uma linha em Atividades.
 * acao = feito | ganho | perdido | separado (o vendedor confirmou com a conta que o deal a confirmar é demanda separada)
 *      | recompra (o vendedor abriu o deal ou ligou pra um par conta e produto da aba Recompra sem deal; deal = "Conta|Produto")
 */
function recordActivity(b) {
  const acao = String(b.acao || '').toLowerCase();
  if (['feito', 'ganho', 'perdido', 'separado', 'recompra'].indexOf(acao) < 0) return { error: 'acao deve ser feito, ganho, perdido, separado ou recompra' };
  if (!b.deal || !b.rep) return { error: 'deal e rep são obrigatórios' };
  const hoje = sheet(TABS.hoje).getRange('B4').getValue();
  const valor = acao === 'ganho' ? Number(b.valor || 0) : '';
  // Escreve na primeira linha vazia da coluna A (appendRow iria pro fim das fórmulas auxiliares de J:N).
  const sh = sheet(TABS.atividades);
  const colA = sh.getRange(1, 1, sh.getMaxRows(), 1).getValues();
  let row = 2;
  for (let i = colA.length - 1; i >= 0; i--) { if (colA[i][0] !== '' && colA[i][0] !== null) { row = i + 2; break; } }
  if (row > sh.getMaxRows()) sh.insertRowsAfter(sh.getMaxRows(), 100);
  sh.getRange(row, 1, 1, 7).setValues([[new Date(), hoje, b.deal, b.rep, acao, valor, b.nota || '']]);
  SpreadsheetApp.flush();
  return { ok: true, deal: b.deal, acao, dia: iso(hoje) };
}

/** Vendedor identificou a conta de um deal da fila: grava Status e Conta na Fila Sem Conta. */
function recordConta(b) {
  if (!b.deal || !b.conta) return { error: 'deal e conta são obrigatórios' };
  const sh = sheet(TABS.fila);
  const ids = sh.getRange(8, 1, Math.max(sh.getLastRow() - 7, 1), 1).getValues();
  let row = -1;
  for (let i = 0; i < ids.length; i++) { if (String(ids[i][0]) === String(b.deal)) { row = i + 8; break; } }
  if (row < 0) return { error: 'deal não está na fila', deal: b.deal };
  const contas = getContas();
  const typed = String(b.conta).trim();
  const canon = contas.find(c => c.toLowerCase() === typed.toLowerCase());
  const status = canon ? 'Identificada' : 'Não é nenhuma das 85';
  sh.getRange(row, 11, 1, 2).setValues([[status, canon || typed]]);
  // registra também em Atividades, pra ficar no histórico
  const hoje = sheet(TABS.hoje).getRange('B4').getValue();
  const atv = sheet(TABS.atividades);
  const colA = atv.getRange(1, 1, atv.getMaxRows(), 1).getValues();
  let r2 = 2;
  for (let i = colA.length - 1; i >= 0; i--) { if (colA[i][0] !== '' && colA[i][0] !== null) { r2 = i + 2; break; } }
  atv.getRange(r2, 1, 1, 7).setValues([[new Date(), hoje, b.deal, b.rep || '', 'conta', '', status + ': ' + (canon || typed)]]);
  SpreadsheetApp.flush();
  return { ok: true, deal: b.deal, status, conta: canon || typed };
}

function advanceDay() {
  const r = sheet(TABS.hoje).getRange('B3');
  r.setValue(Number(r.getValue() || 0) + 1);
  SpreadsheetApp.flush();
  return { ok: true, diasPassados: r.getValue(), hoje: cell(TABS.hoje, 'B4') };
}

function resetDemo() {
  sheet(TABS.hoje).getRange('B3').setValue(0);
  const sh = sheet(TABS.atividades);
  sh.getRange(2, 1, sh.getMaxRows() - 1, 7).clearContent();
  const fila = sheet(TABS.fila);
  fila.getRange(8, 11, fila.getMaxRows() - 7, 2).clearContent();
  SpreadsheetApp.flush();
  return { ok: true, hoje: cell(TABS.hoje, 'B4') };
}

/** Job diário: anda um dia e manda as mensagens. Agendado por installTrigger(). */
function dailyJob() {
  advanceDay();
  return notifyAll();
}

function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'dailyJob') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('dailyJob').timeBased().atHour(9).everyDays(1).inTimezone('America/Sao_Paulo').create();
  return 'ok';
}

/** Liga ou desliga o job diário. Desligado durante a avaliação, pra que o "hoje" da demo não ande sozinho. */
function setTrigger(on) {
  if (on) { installTrigger(); return { ok: true, triggerLigado: true }; }
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'dailyJob') ScriptApp.deleteTrigger(t); });
  return { ok: true, triggerLigado: false };
}

function buildMessage(rep, lista, fila, cfg) {
  const hojeDate = new Date(cfg.hoje + 'T12:00:00');
  const segunda = hojeDate.getDay() === 1;
  const passo = n => lista.filter(r => Number(r['Passo']) === n).length;
  const top = lista.filter(r => Number(r['Passo']) !== 5).slice(0, 5).map(r =>
    `${r['Ordem do dia']}. ${r['Conta']} · ${r['Produto']} (US$ ${r['Preço de tabela']}) — ${r['Próxima ação']}`
  ).join('\n');
  const head = segunda
    ? `Bom dia, ${rep}. Sua semana (${cfg.hoje}): ${lista.length} deals na lista, ${passo(1) + passo(2) + passo(3)} pra tocar até sexta.`
    : `Bom dia, ${rep}. Sua lista de ${cfg.hoje}: ${lista.length} deals, ${passo(1)} na hora de recomprar e vivos.`;
  const passos = `Passo 1 (vivo e na hora de recomprar): ${passo(1)} · Passo 2 (outros vivos): ${passo(2)} · Passo 3 (antigos, conta na hora de recomprar): ${passo(3)} · Passo 4: ${passo(4)} · Confirmar (outro vendedor fechou o produto depois de abrir): ${passo(5)}`;
  const filaTxt = fila.length ? `\nFila sem conta: ${fila.length} deals (${fila.filter(f => f['Escalada'] === 'Escalar pro manager').length} fora do prazo). Depois dos vivos, identifique a conta.` : '';
  return `${head}\n${passos}\n\nComece por aqui:\n${top}${filaTxt}\n\nAbra o app pra ver o porquê de cada deal e marcar o que fez.`;
}

function notifyAll() {
  const cfg = getConfig();
  const lista = getLista();
  const fila = getFila();
  const to = cell(TABS.hoje, 'B25');
  const webhook = String(cell(TABS.hoje, 'B26') || '').trim();
  const reps = getUsers().filter(u => u.papel === 'vendedor');
  let sent = 0;
  reps.forEach(u => {
    const minha = lista.filter(r => r['Trabalha hoje'] === u.nome).sort((a, b) => Number(a['Ordem do dia']) - Number(b['Ordem do dia']));
    if (!minha.length) return;
    const msg = buildMessage(u.nome, minha, fila.filter(f => f['Vendedor'] === u.nome), cfg);
    if (to) MailApp.sendEmail(to, `[Lead Scorer] ${u.nome}: sua lista de ${cfg.hoje}`, msg);
    if (webhook) UrlFetchApp.fetch(webhook, { method: 'post', contentType: 'application/json', payload: JSON.stringify({ text: msg }) });
    sent++;
  });
  return { ok: true, hoje: cfg.hoje, mensagens: sent, email: !!to, slack: !!webhook };
}
