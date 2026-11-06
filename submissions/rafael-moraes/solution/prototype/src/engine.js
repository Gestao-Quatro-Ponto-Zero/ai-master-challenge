// Motor de triagem: classificador (TF-IDF + regressão logística exportada do scikit-learn)
// + políticas definidas pelo Rafael (limiar, lista vermelha, prioridade).
// Roda no navegador e no Node (para o teste de paridade com o Python).

if (typeof module !== "undefined" && typeof ptToModelText === "undefined") {
  ({ ptToModelText, looksPortuguese } = require("./glossary_pt.js"));
}

function buildIndex(model) {
  const index = new Map();
  model.vocab.forEach((term, i) => index.set(term, i));
  return index;
}

// Replica TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, norm='l2')
function vectorize(text, model, index) {
  const tokens = (text.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []);
  const grams = tokens.slice();
  for (let i = 0; i < tokens.length - 1; i++) grams.push(tokens[i] + " " + tokens[i + 1]);
  const tf = new Map();
  for (const g of grams) {
    const j = index.get(g);
    if (j !== undefined) tf.set(j, (tf.get(j) || 0) + 1);
  }
  let norm = 0;
  const vec = [];
  for (const [j, c] of tf) {
    const w = (1 + Math.log(c)) * model.idf[j];
    vec.push([j, w]);
    norm += w * w;
  }
  norm = Math.sqrt(norm) || 1;
  return vec.map(([j, w]) => [j, w / norm]);
}

function predictProba(text, model, index) {
  const x = vectorize(text, model, index);
  const scores = model.coef.map((row, k) => {
    let s = model.intercept[k];
    for (const [j, w] of x) s += row[j] * w;
    return s;
  });
  const m = Math.max(...scores);
  const e = scores.map((s) => Math.exp(s - m));
  const sum = e.reduce((a, b) => a + b, 0);
  return { probs: e.map((v) => v / sum), known: x.length };
}

// ---------------- Políticas (decisões do Rafael no DECISIONS.md) ----------------
const POLICY = {
  threshold: 0.8,                       // Decisão 9
  thresholdByClass: { "Administrative rights": 0.9 },
  // Decisão 13: a categoria "Administrative rights" do Dataset 2 é, na prática, suporte a software
  // (Outlook, Windows, instalação). Só vai para pessoa o pedido que concede privilégio (regra abaixo).
};

// Regras escritas sobre o texto sem acento e em minúsculas. Cada uma documenta a decisão que a originou.
const RULES = {
  // Decisão 21: canal confidencial — nenhuma pergunta automática.
  ombuds: /\b(assedi\w*|discrimina\w*|denunci\w*|fraude|corrupc\w*|propina|abuso|harass\w*|bullying|discriminat\w*|fraud|whistleblow\w*|bribe\w*)\b/i,
  // Decisão 21: incidente de segurança.
  security: /\b(phishing|hacke\w*|invadid[oa]|invadiram|invasao|vazou|vazament\w*|vazad[oa]|golpe|malware|ransomware|virus|dados bancarios|clonad[oa]|dominio falso|look ?alike domain|spoof\w*|hacked|breach|leak(ed)?|scam|compromised|someone is (sending|using)|suspicious (link|email|login))\b/i,
  securityLeak: /\b(vazou|vazament\w*|vazad[oa]|leak(ed)?|breach)\b/i,
  // Decisões 10 e 19: risco de perder o cliente. Palavras fortes contam sempre (exceto se negadas).
  churn: /\b(reembolso|estorno|devolver o dinheiro|meu dinheiro de volta|inaceitavel|pessimo|absurdo|procon|reclame aqui|advogado|processo judicial|(trocar|mudar) de (empresa|fornecedor|operadora)|outro fornecedor|outra empresa|concorrente|nao quero mais (usar|o servico|continuar)|encerrar (minha|a|o|meu) (conta|contrato|assinatura|plano|cadastro)|ultima vez|refund|money back|chargeback|terminate (the |my |our )?(contract|subscription|service)|close (my|our) account|switch(ing)? to (another|a different|competitor)|moving to another|other (vendors|providers)|another (vendor|provider)|competitor|unacceptable|terrible|worst|last time|lawyer|legal action)\b/gi,
  cancel: /\b(cancelar|cancelamento|cancelem|cancela|cancel+(ation|ed|ing)?)\b/gi,
  // "Cancelar" não conta quando o objeto é reunião, agenda, convite etc. — verificado em CADA ocorrência (auditoria).
  cancelObjectNotChurn: /^\s+(\w+\s+){0,3}?(a |o |da |do |the |my |our )?(reuniao|reunioes|agenda|evento|convite|sala|compromisso|treinamento|chamada|reserva|meeting|meetings|invite|invitation|appointment|booking|reservation|call|event|session)\b/i,
  // Negação logo antes ("não quero cancelar", "don't want to cancel") anula aquela ocorrência.
  negatedBefore: /\b(nao|nem|nunca|sem|don'?t|do not|not|never|no)\s+(\w+\s+){0,2}$/i,
  hrSensitive: /\b(saiu da empresa|desligamento|desligad[oa]|demiss[aã]o|demitid[oa]|rescis[aã]o|folha de pagamento|salari\w*|atestado|licenca medica|advertencia|dados pessoais|left the company|leaver|leaving the company|resign(ed|ation)?|dismiss(al|ed)?|fired|offboard(ing)?|terminat(ion|ed) of employment|payroll|salar(y|ies)|sick leave|disciplinary)\b/i,
  privilege: /\b(administrador|direitos? de admin|acesso de admin|permissao de admin|privilegio|credenciais? de administrador|acesso total|admin local|me da admin|liberar acesso|conceder acesso|administrator (rights|access|account|credentials|privileges)|admin (rights|access)|local admin|elevated|full access|grant(ing)? access)\b/i,
  // Decisão 23: cobrança e comercial (a operação do briefing atende clientes; o modelo é de TI interna).
  billing: /\b(cobrad[oa]|cobranca|cobrança|cobraram|fatura|boleto|pagamento|pague[i]?|debito|debitado|cartao de credito|nota fiscal|charged|invoice|billing|payment|double charge)\b/i,
  sales: /\b(quanto custa|preco|precos|orcamento|cotacao|proposta comercial|contratar|plano (empresarial|anual|mensal|basico|premium)|planos|desconto|pricing|price|quote|how much|enterprise plan|discount)\b/i,
  // Decisão 22: só FATOS sobem a prioridade.
  stopped: /\b(nao consigo (trabalhar|acessar|logar|entrar|fazer login)|estou parad[oa]|esta(mos)? parad[oa]s?|fiquei parad[oa]|sem conseguir trabalhar|cannot (work|log ?in|login|access)|can'?t (work|log ?in|login|access)|unable to (work|log ?in|access)|i'?m blocked|we'?re blocked)\b/i,
  // Palavras de urgência sem fato: não sobem — disparam a pergunta de impacto.
  urgencyWord: /\b(urgente|urgencia|prioridade alta|importancia alta|imediatamente|o quanto antes|asap|urgent(ly)?|importance high|high importance|immediately|critical)\b/i,
  // Decisão 18: P1 = impacto coletivo.
  outage: /\b(fora do ar|caiu para todos|caiu pra todos|ninguem (\w+ ){0,4}consegue|ninguem esta conseguindo|todos os usuarios|toda a (empresa|equipe|area)|(financeiro|setor|time|equipe|departamento|area|empresa|escritorio) inteir[oa]|varias equipes|(site|sistema|servidor|erp|rede) (caiu|esta fora|parou)|outage|down for everyone|everyone is affected|all users|nobody (\w+ ){0,3}can|whole (team|company|department|office))\b/i,
  // Aviso de manutenção programada não é incidente (auditoria: "planned outage, FYI" virava P1).
  notIncident: /\b(planned|scheduled|programad[oa]|manutencao programada|fyi|no action needed|nenhuma acao|apenas aviso|so avisando|assessment)\b/i,
  failure: /\b(parou|quebrou|quebrad[oa]|nao liga|nao funciona|nao esta funcionando|nao abre|travando|travou|caiu|queimou|stopped working|not working|broken|dead|won'?t turn on|crash(ed|ing)?|freez(e|es|ing)|falhando)\b/i,
};

// Procura cancelamento ocorrência por ocorrência: ignora "cancelar a reunião" e "não quero cancelar".
function findChurn(plain) {
  for (const re of [RULES.churn, RULES.cancel]) {
    re.lastIndex = 0; let m;
    while ((m = re.exec(plain))) {
      const before = plain.slice(Math.max(0, m.index - 40), m.index);
      const after = plain.slice(m.index + m[0].length, m.index + m[0].length + 60);
      if (RULES.negatedBefore.test(before)) continue;
      if (re === RULES.cancel && RULES.cancelObjectNotChurn.test(after)) continue;
      return m[0];
    }
  }
  return null;
}

const LEVEL = { P1: 1, P2: 2, P3: 3 };
function raise(cur, next) { return LEVEL[next.level] < LEVEL[cur.level] ? next : cur; } // a IA só sobe, nunca rebaixa
const HUMAN_LANES = ["ouvidoria", "seguranca", "retencao", "rh", "aprovacao", "financeiro", "comercial"];

function triage(text, model, index, opts = {}) {
  const isPt = looksPortuguese(text);
  const pt = isPt ? ptToModelText(text) : null;
  const { probs, known } = predictProba(isPt ? pt.text : text, model, index);
  const plain = text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const order = probs.map((p, i) => [p, i]).sort((a, b) => b[0] - a[0]);
  const top = model.classes[order[0][1]];
  const second = model.classes[order[1][1]];
  const conf = order[0][0];
  const thr = POLICY.thresholdByClass[top] ?? POLICY.threshold;
  const m = (re) => plain.match(re);
  const ombuds = m(RULES.ombuds), security = m(RULES.security);
  const churn = opts.noChurn ? null : findChurn(plain);
  const hr = m(RULES.hrSensitive), privilege = m(RULES.privilege), billing = m(RULES.billing), sales = m(RULES.sales);
  const stopped = m(RULES.stopped), urgencyWord = m(RULES.urgencyWord), failure = m(RULES.failure);
  const outage = RULES.notIncident.test(plain) ? null : m(RULES.outage);

  // Quem age — ordem fixa, a primeira regra que bater decide.
  let lane, reason;
  // Segurança antes de Ouvidoria: "fraud received from look alike domain" é phishing (caso real do Dataset 2).
  if (security) { lane = "seguranca"; reason = { k: "r_security", p: [security[0]] }; }
  else if (ombuds) { lane = "ouvidoria"; reason = { k: "r_ombuds", p: [ombuds[0]] }; }
  else if (churn) { lane = "retencao"; reason = { k: "r_churn", p: [churn] }; }
  else if (hr) { lane = "rh"; reason = { k: "r_hr", p: [hr[0]] }; }
  else if (privilege) { lane = "aprovacao"; reason = { k: "r_priv", p: [privilege[0]] }; }
  else if (billing) { lane = "financeiro"; reason = { k: "r_billing", p: [billing[0]] }; }
  else if (sales) { lane = "comercial"; reason = { k: "r_sales", p: [sales[0]] }; }
  else if (known === 0) { lane = "detalhes"; reason = { k: "r_vague", p: [] }; }
  else if (conf >= thr) { lane = "auto"; reason = { k: "r_auto", p: [pct(conf), pct(thr)] }; }
  else { lane = "revisao"; reason = { k: "r_review", p: [pct(conf), pct(thr)] }; }

  // Prioridade — só fatos sobem (decisão 22).
  let priority = { level: "P3", why: { k: "p_none", p: [] } };
  if (churn) priority = { level: "P3", why: { k: "p_churn_wait", p: [] } };
  if (ombuds) priority = raise(priority, { level: "P2", why: { k: "p_ombuds", p: [] } });
  if (security) priority = raise(priority, RULES.securityLeak.test(plain)
    ? { level: "P1", why: { k: "p_leak", p: [] } } : { level: "P2", why: { k: "p_security", p: [] } });
  if (stopped) priority = raise(priority, { level: "P2", why: { k: "p_stopped_text", p: [stopped[0]] } });
  if (outage) priority = raise(priority, { level: "P1", why: { k: "p_outage", p: [outage[0]] } });

  // Pergunta de impacto: falha ou pedido de urgência sem fato de impacto (decisões 16 e 22). Ouvidoria nunca recebe perguntas.
  const asksUrgency = !!urgencyWord && !stopped && !outage;
  const askImpact = (asksUrgency || (!!failure && !stopped && !outage)) && ["auto", "revisao", "financeiro", "comercial"].includes(lane);
  return { askImpact, askReason: asksUrgency ? { k: "ask_urgency", p: [urgencyWord[0]] } : failure ? { k: "ask_failure", p: [failure[0]] } : null,
    top, second, conf, secondConf: order[1][0], thr, lane, reason, priority, probs, known, churn: !!churn,
    lang: isPt ? "pt" : "en", ptHits: pt ? pt.hits : [] };
}

// Decisão 19: duas perguntas para entender se o cliente já decidiu ou se dá para resolver.
const CHURN_REASONS = ["problem", "price", "nouse", "competitor", "other"];
const CHURN_DECISION = ["fix", "decided"];
function churnPriority(cur, reason, decision) {
  if (reason === "problem" && decision === "fix") return raise(cur, { level: "P2", why: { k: "p_churn_fix", p: [] } });
  if (decision === "decided" || reason === "competitor") return raise(cur, { level: "P2", why: { k: "p_churn_window", p: [] } });
  return { level: cur.level, why: LEVEL[cur.level] < 3 ? cur.why : { k: "p_churn_commercial", p: [] } };
}

// Respostas do cliente → prioridade. P1 vinda só da resposta do cliente fica "a confirmar" (auditoria).
function priorityFromAnswers(cur, work, scope) {
  let p = cur;
  if (work === 2) p = raise(p, { level: "P2", why: { k: "p_stopped", p: [] } });
  if (scope === 2) p = raise(p, { level: "P1", why: { k: "p_many", p: [] }, confirm: true });
  return p;
}

const INTAKE_TOPICS = ["Access", "Hardware", "Storage", "Administrative rights", "Purchase", "HR Support", "Internal Project", "BILLING", "SALES", "CHURN", "Miscellaneous"];
function intakeResult(topicCat, work, scope, cur) {
  let priority = priorityFromAnswers(cur, work, scope);
  if (topicCat === "CHURN") {
    if (LEVEL[priority.level] === 3) priority = { level: "P3", why: { k: "p_churn_wait", p: [] } };
    return { top: "CHURN", lane: "retencao", churn: true, priority, reason: { k: "r_intake_churn", p: [] } };
  }
  if (topicCat === "BILLING") return { top: "BILLING", lane: "financeiro", priority, reason: { k: "r_intake_team", p: ["BILLING"] } };
  if (topicCat === "SALES") return { top: "SALES", lane: "comercial", priority, reason: { k: "r_intake_team", p: ["SALES"] } };
  const lane = topicCat === "Miscellaneous" ? "revisao" : "auto";
  return { top: topicCat, lane, priority, reason: { k: lane === "auto" ? "r_intake" : "r_intake_other", p: [topicCat] } };
}

function pct(x) { return Math.round(x * 100) + "%"; }

if (typeof module !== "undefined") module.exports = { buildIndex, vectorize, predictProba, triage, findChurn, POLICY, RULES, HUMAN_LANES, INTAKE_TOPICS, intakeResult, priorityFromAnswers, churnPriority, CHURN_REASONS, CHURN_DECISION };
