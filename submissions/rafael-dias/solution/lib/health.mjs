import { occurredAt } from "./evidence.mjs";

// Pilot policy, not a calibrated probability. Change with a version and tests.
export const HEALTH_POLICY = Object.freeze({
  version: "health-v2.0",
  replyDays: 7,
  qualificationDays: 30,
  financialDays: 30,
  minimumCoverage: 70,
  greenCoverage: 85,
});
const DAY = 86400000;
const last = (events, predicate) => events.findLast(predicate);

/** Inputs must be the deduplicated, time-bounded opportunity events. */
export function calculateHealth(deal, now, policy = HEALTH_POLICY) {
  const events = deal.activities || [];
  const conversations = events.filter((e) =>
    ["contact", "qualify", "proposal", "followup", "pause"].includes(e.type),
  );
  const age = (e) => (Date.parse(now) - Date.parse(occurredAt(e))) / DAY;
  const qualification = last(events, (e) => e.type === "qualify");
  const freshQualification =
    !!qualification && age(qualification) <= policy.qualificationDays;
  const reply = last(conversations, (e) => e.buyerResponse === "confirmed");
  const responseObserved = conversations.some((e) =>
    ["confirmed", "none"].includes(e.buyerResponse),
  );
  const firstUnanswered = conversations.find((e) => e.buyerResponse === "none");
  const recentReply = !!reply && age(reply) <= policy.replyDays;
  const task = deal.nextTask;
  const acceptedKnown = !!task && ["yes", "no"].includes(task.accepted);
  const financial = last(
    events,
    (e) =>
      e.type === "proposal" &&
      ["compatible", "blocked"].includes(e.financialStatus),
  );
  const freshFinancial = !!financial && age(financial) <= policy.financialDays;
  const factor = (key, label, max, known, points, explanation) => ({
    key,
    label,
    max,
    known,
    points: known ? points : 0,
    explanation,
  });
  const factors = [
    factor(
      "need",
      "Necessidade",
      15,
      !!qualification,
      freshQualification && !!qualification.need ? 15 : 0,
      !qualification
        ? "Ainda não confirmada"
        : freshQualification
          ? "Registrada na qualificação"
          : "Reconfirme: informação antiga",
    ),
    factor(
      "authority",
      "Decisor",
      15,
      !!qualification,
      freshQualification && !!qualification.authority ? 15 : 0,
      !qualification
        ? "Ainda não confirmado"
        : freshQualification
          ? "Processo de decisão registrado"
          : "Reconfirme o decisor",
    ),
    factor(
      "timing",
      "Prazo de compra",
      10,
      !!qualification,
      freshQualification && !!qualification.timing ? 10 : 0,
      !qualification
        ? "Ainda não confirmado"
        : freshQualification
          ? "Prazo declarado pelo cliente"
          : "Reconfirme o prazo",
    ),
    factor(
      "response",
      "Participação do comprador",
      15,
      responseObserved,
      recentReply ? 15 : 0,
      !responseObserved
        ? "Registros antigos não comprovam resposta"
        : recentReply
          ? `Conversa confirmada nos últimos ${policy.replyDays} dias`
          : "Sem resposta recente confirmada",
    ),
    factor(
      "recency",
      "Atualidade da conversa",
      10,
      responseObserved,
      !reply
        ? 0
        : age(reply) <= policy.replyDays
          ? 10
          : age(reply) <= policy.replyDays * 2
            ? 5
            : 0,
      reply
        ? `Última conversa há ${Math.floor(age(reply))} dia(s)`
        : responseObserved
          ? "Tentativa sem conversa confirmada"
          : "Data de conversa desconhecida",
    ),
    factor(
      "accepted",
      "Próximo passo aceito",
      15,
      acceptedKnown,
      task?.accepted === "yes" && !deal.overdue ? 15 : 0,
      !acceptedKnown
        ? "Aceite do cliente não informado"
        : task.accepted === "no"
          ? "Agendamento interno, sem aceite"
          : deal.overdue
            ? "Compromisso venceu; confirme nova data"
            : "Aceite declarado pelo vendedor",
    ),
    factor(
      "due",
      "Data do próximo passo",
      10,
      !!task,
      task && !deal.overdue ? 10 : 0,
      task
        ? deal.overdue
          ? "Prazo vencido"
          : "Próximo compromisso futuro"
        : "Ainda não agendado",
    ),
    factor(
      "financial",
      "Viabilidade financeira",
      10,
      !!financial,
      freshFinancial && financial.financialStatus === "compatible" ? 10 : 0,
      !financial
        ? "Condições ainda não confirmadas"
        : financial.financialStatus === "blocked"
          ? "Bloqueio financeiro informado"
          : freshFinancial
            ? "Compatibilidade declarada pelo vendedor"
            : "Reconfirme as condições",
    ),
  ];
  const coverage = factors.reduce((n, f) => n + (f.known ? f.max : 0), 0);
  const points = factors.reduce((n, f) => n + f.points, 0);
  const risks = [];
  if (deal.overdue) risks.push({ code: "overdue", label: "Retorno vencido" });
  if (financial?.financialStatus === "blocked")
    risks.push({
      code: "financial_block",
      label: "Condições financeiras bloqueadas",
    });
  if (
    !recentReply &&
    ((reply && age(reply) > policy.replyDays) ||
      (!reply && firstUnanswered && age(firstUnanswered) > policy.replyDays))
  )
    risks.push({
      code: "buyer_silence",
      label: "Sem resposta recente do comprador",
    });
  if (qualification && !freshQualification)
    risks.push({
      code: "stale_qualification",
      label: "Qualificação precisa ser reconfirmada",
    });
  const closed = ["won", "lost"].includes(deal.status);
  const enough = coverage >= policy.minimumCoverage && !!reply;
  const score = !closed && enough ? points : null;
  const green =
    score >= 80 &&
    coverage >= policy.greenCoverage &&
    recentReply &&
    freshQualification &&
    task?.accepted === "yes" &&
    !risks.length;
  const tone = closed
    ? "unknown"
    : risks.length
      ? "red"
      : green
        ? "green"
        : score === null
          ? "unknown"
          : "amber";
  const label = closed
    ? "Encerrada"
    : risks.length
      ? "Risco identificado"
      : green
        ? "Saudável"
        : score === null
          ? "Em validação"
          : "Atenção";
  return {
    version: policy.version,
    score,
    points,
    coverage,
    unknownPoints: 100 - coverage,
    range: [points, points + 100 - coverage],
    tone,
    label,
    risks: closed ? [] : risks,
    factors,
    lastBuyerReplyAt: reply ? occurredAt(reply) : null,
    recentReply,
    freshQualification,
    summary: closed
      ? "Sem saúde ativa após o encerramento."
      : risks[0]?.label ||
        (score === null
          ? "Confirme resposta do cliente e os sinais pendentes."
          : green
            ? "Conversa recente, qualificação e próximo passo aceito."
            : "Confira os pontos pendentes antes de avançar."),
  };
}
