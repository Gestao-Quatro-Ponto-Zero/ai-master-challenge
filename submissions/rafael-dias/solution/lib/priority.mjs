/** Operational ordering. Potential cannot compensate for an overdue commitment. */
export function priorityDecision(deal, now = new Date().toISOString()) {
  const result = (rank, label, reason, action, eligible = true) => ({
    rank,
    label,
    reason,
    action,
    eligible,
  });
  if (["won", "lost"].includes(deal.status))
    return result(
      99,
      "Encerrada",
      "Negócio já encerrado.",
      "Consultar histórico",
      false,
    );
  if (deal.pauseUntil && Date.parse(deal.pauseUntil) > Date.parse(now))
    return result(
      90,
      "Pausa solicitada",
      "O cliente pediu uma pausa. Respeite a data combinada.",
      "Aguardar a data combinada",
      false,
    );
  if (deal.overdue)
    return result(
      0,
      "Retomar agora",
      `O compromisso “${deal.nextTask.label}” venceu. Confirme a decisão e combine uma nova data.`,
      "Retomar compromisso",
    );
  if (deal.healthDetails?.risks.some((r) => r.code === "financial_block"))
    return result(
      2,
      "Revisar condições",
      "O cliente informou um bloqueio financeiro. Revise a proposta sem antecipar o contato combinado.",
      "Rever as condições da proposta",
    );
  if (deal.scheduled)
    return result(
      90,
      "Na agenda",
      `Próximo compromisso: ${deal.nextTask.label}. Aguarde a data combinada; agendamento não comprova resposta.`,
      "Aguardar compromisso",
      false,
    );
  if (!deal.account)
    return result(
      4,
      "Identificar cliente",
      "A conta ainda não foi identificada. Complete o contexto antes da abordagem.",
      "Identificar conta e contato",
    );
  if (deal.healthDetails?.risks.length)
    return result(
      2,
      "Revisar negociação",
      deal.healthDetails.summary,
      "Investigar o bloqueio e combinar próximo passo",
    );
  if (deal.healthDetails?.recentReply)
    return result(
      1,
      "Avançar conversa",
      "O comprador participou recentemente. Confirme o avanço pendente.",
      deal.qualification
        ? "Preparar proposta ou decisão"
        : "Confirmar necessidade, decisor e prazo",
    );
  if (deal.deal_stage === "Prospecting")
    return result(
      3,
      "Qualificar",
      `${deal.account} está em prospecção. Descubra necessidade, decisor e prazo.`,
      "Iniciar qualificação",
    );
  if (deal.review)
    return result(
      2,
      "Revisar negociação",
      `Negociação com ${deal.age} dias no retrato de 2017; o ciclo típico do produto é ${deal.reference.days} dias. Confirme se continua válida.`,
      "Validar continuidade da negociação",
    );
  return result(
    3,
    "Explorar oportunidade",
    "A referência histórica ajuda na seleção, mas faltam evidências atuais do comprador.",
    "Confirmar contexto e próximo passo",
  );
}

export function rankOpportunities(deals, now = new Date().toISOString()) {
  return deals
    .filter((d) => priorityDecision(d, now).eligible)
    .sort((a, b) => {
      const pa = priorityDecision(a, now),
        pb = priorityDecision(b, now);
      return (
        pa.rank - pb.rank ||
        (a.overdue && b.overdue
          ? Date.parse(a.nextTask.dueAt) - Date.parse(b.nextTask.dueAt)
          : 0) ||
        // Compare seller-declared quotes only when both are USD totals; otherwise use the
        // same historical reference for both. Never compare a quote to unit price.
        Number(b.quote?.currency === "USD") -
          Number(a.quote?.currency === "USD") ||
        (a.quote?.currency === "USD" && b.quote?.currency === "USD"
          ? b.quote.amount - a.quote.amount
          : (b.score || 0) - (a.score || 0)) ||
        a.opportunity_id.localeCompare(b.opportunity_id)
      );
    });
}
