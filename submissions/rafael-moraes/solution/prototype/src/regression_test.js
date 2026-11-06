// Testes de regressão: casos que já quebraram (testes do Rafael e da auditoria) e casos que nunca podem quebrar.
// Formato: [texto, fila esperada ("!x" = qualquer uma menos x), prioridade esperada ou null, pergunta de impacto esperada ou null, origem]
const { buildIndex, triage, churnPriority, priorityFromAnswers } = require("./engine.js");
const m = require("../model.json"); const ix = buildIndex(m);
const cases = [
  // Testes do Rafael
  ["Quero cancelar!", "retencao", "P3", null, "Rafael: escapava da Retenção"],
  ["Quero cancelar a conta", "retencao", "P3", null, "Rafael"],
  ["Olá, meu monitor parou de funcionar.", "auto", "P3", true, "Rafael: pergunta de impacto"],
  ["tenho uma dúvida pode ajudar?", "detalhes", "P3", null, "Rafael"],
  ["Bom dia, estou com problemas para acessar minha conta, não reconhece meu email e nem está me enviando o email de recuperação.", "auto", null, null, "Rafael: ia para Admin rights"],
  // Auditoria — casos sensíveis
  ["Preciso cancelar a reserva da sala e também quero cancelar meu contrato", "retencao", null, null, "auditoria: dois assuntos"],
  ["Quero encerrar minha conta", "retencao", null, null, "auditoria"],
  ["Please close my account, I'm moving to another provider", "retencao", null, null, "auditoria"],
  ["Estou pensando seriamente em procurar outro fornecedor", "retencao", null, null, "auditoria"],
  ["Não quero mais usar o serviço de vocês", "retencao", null, null, "auditoria"],
  ["I want my money back", "retencao", null, null, "auditoria"],
  ["We are evaluating other vendors for next year", "retencao", null, null, "auditoria"],
  ["Não quero cancelar, só quero entender a fatura", "financeiro", null, null, "auditoria: negação"],
  ["Preciso cancelar a reunião de amanhã na sala 3", "!retencao", null, null, "falso positivo"],
  ["Please cancel the meeting invite for Friday", "!retencao", null, null, "falso positivo"],
  ["Estou sofrendo assédio moral do meu gestor", "ouvidoria", "P2", false, "auditoria: questionário em assédio"],
  ["Meu colega está me assediando no trabalho", "ouvidoria", null, false, "auditoria"],
  ["Quero denunciar um caso de fraude no setor de compras", "ouvidoria", null, null, "auditoria"],
  ["Vazou a planilha de salários de todo mundo no drive compartilhado", "seguranca", "P1", null, "auditoria: vazamento"],
  ["Acho que cliquei num link de phishing e digitei minha senha", "seguranca", "P2", null, "auditoria"],
  ["I think I got hacked, someone is sending emails from my account", "seguranca", "P2", null, "auditoria"],
  ["Recebi um e-mail pedindo meus dados bancários, é golpe?", "seguranca", null, null, "auditoria"],
  ["Fui demitido e preciso pegar meus arquivos pessoais do notebook", "rh", null, null, "auditoria"],
  ["A colaboradora saiu da empresa, desativem a conta", "rh", null, null, "RH"],
  ["Preciso de direitos de administrador para instalar um programa", "aprovacao", null, null, "privilégio"],
  ["Can you make me a local admin?", "aprovacao", null, null, "auditoria"],
  ["Fui cobrado duas vezes este mês", "financeiro", null, null, "auditoria: sem destino"],
  ["Quanto custa o plano empresarial?", "comercial", null, null, "auditoria: sem destino"],
  // Auditoria — prioridade
  ["URGENTE!!! preciso trocar o papel de parede", "!retencao", "P3", true, "auditoria: urgência falsa"],
  ["Não é urgente, mas o mouse está falhando", "!retencao", "P3", null, "auditoria: negação de urgência"],
  ["Planned outage tonight 10pm, FYI no action needed", null, "P3", null, "auditoria: manutenção virava P1"],
  ["Ninguém da minha equipe consegue acessar o ERP", null, "P1", null, "auditoria: impacto coletivo"],
  ["O servidor caiu e o financeiro inteiro está parado", null, "P1", null, "auditoria"],
  ["O sistema está fora do ar para todos os usuários", null, "P1", null, "P1"],
  ["Não consigo trabalhar, o computador não liga", null, "P2", false, "fato: parado"],
  ["Meu notebook quebrou e não consigo trabalhar", null, "P2", false, "fato"],
  ["Preciso de um teclado novo", "!retencao", "P3", false, "P3"],
];
let fail = 0;
for (const [t, lane, prio, ask, why] of cases) {
  const r = triage(t, m, ix);
  const laneOk = lane === null || (lane.startsWith("!") ? r.lane !== lane.slice(1) : r.lane === lane);
  const prioOk = prio === null || r.priority.level === prio;
  const askOk = ask === null || r.askImpact === ask;
  const ok = laneOk && prioOk && askOk; if (!ok) fail++;
  console.log(`${ok ? "OK   " : "FALHA"} ${r.lane.padEnd(10)} ${r.priority.level} ${r.askImpact ? "?" : " "} | ${t.slice(0, 60)}  (${why})${ok ? "" : `  esperado: ${lane} ${prio} ${ask}`}`);
}
const p3 = { level: "P3", why: { k: "p_churn_wait", p: [] } };
for (const [rs, d, want] of [["problem", "fix", "P2"], ["price", "decided", "P2"], ["competitor", "fix", "P2"], ["price", "fix", "P3"], ["nouse", "fix", "P3"]]) {
  const got = churnPriority(p3, rs, d).level; const ok = got === want; if (!ok) fail++;
  console.log(`${ok ? "OK   " : "FALHA"} churn ${rs}+${d}: ${got}`);
}
const p1 = priorityFromAnswers({ level: "P3", why: {} }, 0, 2); if (!(p1.level === "P1" && p1.confirm)) fail++;
console.log(`${p1.level === "P1" && p1.confirm ? "OK   " : "FALHA"} P1 por resposta do cliente fica "a confirmar"`);
console.log(fail ? `\n${fail} FALHA(S)` : `\nTodos os ${cases.length + 6} casos passaram`);
process.exit(fail ? 1 : 0);
