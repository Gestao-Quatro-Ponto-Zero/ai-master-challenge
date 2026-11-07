export function scoreBand(score) {
  return score >= 80
    ? { tone: "green", label: "Alta prioridade" }
    : score >= 60
      ? { tone: "amber", label: "Prioridade intermediária" }
      : { tone: "red", label: "Baixa prioridade" };
}
export function spinQuestions(deal) {
  const account = deal.account || "a empresa",
    product = deal.product;
  const history = deal.account_history;
  return [
    {
      key: "S",
      label: "Situação",
      context: history?.won
        ? `${history.won} negócios ganhos com ${account} até 2017. Confirme o momento atual antes de usar esse histórico na conversa.`
        : `Oportunidade de ${product} na carteira; o interesse atual ainda precisa ser confirmado.`,
      question: deal.qualification?.need
        ? `Você comentou sobre “${deal.qualification.need}”. Como isso está hoje? O que mudou desde então?`
        : `Antes de te falar do ${product}, queria entender o momento da ${account}. O que vocês estão querendo melhorar hoje?`,
      investigate:
        "Comece ouvindo. Use a resposta para escolher a próxima pergunta, sem repetir o que o cliente já contou.",
    },
    {
      key: "P",
      label: "Problema",
      question: deal.qualification?.need
        ? `Quando você fala em “${deal.qualification.need}”, onde isso mais pega na rotina do time?`
        : "E hoje, o que mais atrapalha chegar nesse resultado? Me dá um exemplo de como isso aparece no dia a dia.",
      investigate:
        "Descubra uma dificuldade real. Se o cliente não relatar um problema, não presuma que ele existe.",
    },
    {
      key: "I",
      label: "Implicação",
      question: deal.qualification?.need
        ? `Quando essa dificuldade com “${deal.qualification.need}” aparece, o que acaba ficando para trás? Quem mais sente isso na operação?`
        : "Quando isso acontece, o que acaba ficando para trás? Você consegue me dar um exemplo do impacto para o time ou para o cliente?",
      investigate:
        "Use somente um problema que o cliente confirmou. Peça um exemplo ou uma dimensão do impacto, sem sugerir perdas inventadas.",
    },
    {
      key: "N",
      label: "Valor da solução",
      question:
        "Se a gente conseguisse resolver esse ponto, o que faria mais diferença para vocês? E o que você precisaria ver numa proposta para seguir com segurança?",
      investigate:
        "Deixe o cliente explicar o benefício esperado. Depois confirme decisor, prazo e um próximo compromisso.",
    },
  ];
}
export function moveIntent(deal, target) {
  const rank = {
    new: 0,
    contacted: 1,
    qualified: 2,
    proposal: 3,
    won: 4,
    lost: 4,
  };
  if (["won", "lost"].includes(deal.status))
    return {
      error:
        "Negócios encerrados ficam no histórico e não podem ser reabertos nesta versão.",
    };
  if (target === deal.status) return { noop: true };
  if (!(target in rank)) return { error: "Etapa inválida." };
  if (target !== "lost" && rank[target] < rank[deal.status])
    return {
      error:
        "O arraste registra avanços. Para corrigir uma etapa já confirmada, revise o histórico com o gestor.",
    };
  return {
    action: {
      contacted: "contact",
      qualified: "qualify",
      proposal: "proposal",
      won: "won",
      lost: "lost",
    }[target],
    target,
  };
}
