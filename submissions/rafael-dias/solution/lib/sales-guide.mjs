import { isClosed, prioritize } from "./workflow.mjs";
export const DAILY_BATCH_SIZE = 5;
export const DAILY_BATCH_COUNT = 4;

export function localDay(value = new Date()) {
  const d = new Date(value);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
export function createDailyPlan(deals, now = new Date().toISOString()) {
  const day = localDay(now);
  const due = deals
    .filter(
      (d) =>
        !isClosed(d) &&
        !d.pauseUntil &&
        d.nextTask &&
        (d.overdue || localDay(d.nextTask.dueAt) === day),
    )
    .sort((a, b) => a.nextTask.dueAt.localeCompare(b.nextTask.dueAt));
  const focus = prioritize(deals).filter((d) => d.account);
  const fallback = prioritize(deals).filter((d) => !d.account);
  const unique = [
    ...new Map(
      [...due, ...focus, ...fallback].map((d) => [d.opportunity_id, d]),
    ).values(),
  ].slice(0, DAILY_BATCH_SIZE * DAILY_BATCH_COUNT);
  return {
    day,
    createdAt: now,
    version: 2,
    batchSize: DAILY_BATCH_SIZE,
    tasks: unique.map((d) => ({
      opportunityId: d.opportunity_id,
      assignedAt: now,
      goal: !d.account
        ? "profile"
        : d.qualification && d.status !== "proposal"
          ? "proposal"
          : "contact",
      label:
        d.nextTask?.label ||
        (!d.account
          ? "Identificar a conta e o contato"
          : d.qualification
            ? "Apresentar proposta"
            : "Conversar com o cliente"),
      account: d.account || "Conta a identificar",
    })),
  };
}
export function ensureDailyPlan(plan, deals, now, events = []) {
  if (!plan) return createDailyPlan(deals, now);
  if (plan.version === 2) return plan;
  const completed = new Set(
    dailyProgress(plan, events, now)
      .tasks.filter((t) => t.done)
      .map((t) => t.opportunityId),
  );
  const fresh = createDailyPlan(deals, now);
  const preserved = plan.tasks.map((t) => {
    const updated = fresh.tasks.find(
      (n) => n.opportunityId === t.opportunityId,
    );
    return {
      ...t,
      ...(!completed.has(t.opportunityId) && updated
        ? { goal: updated.goal, label: updated.label }
        : {}),
      assignedAt: t.assignedAt || plan.createdAt,
    };
  });
  const originalIds = new Set(preserved.map((t) => t.opportunityId));
  return {
    ...plan,
    version: 2,
    batchSize: DAILY_BATCH_SIZE,
    tasks: [
      ...preserved,
      ...fresh.tasks.filter((t) => !originalIds.has(t.opportunityId)),
    ].slice(0, DAILY_BATCH_SIZE * DAILY_BATCH_COUNT),
  };
}
export function dailyProgress(plan, events, now = new Date().toISOString()) {
  if (!plan)
    return {
      tasks: [],
      completed: 0,
      total: 0,
      percent: 0,
      batches: [],
      activeBatch: 0,
      completedBatches: 0,
    };
  const tasks = plan.tasks.map((task) => {
    const accepts =
      task.goal === "profile"
        ? ["profile", "contact", "qualify", "proposal", "won", "lost"]
        : task.goal === "proposal"
          ? ["proposal", "won", "lost"]
          : ["contact", "qualify", "proposal", "won", "lost"];
    const done = events.some(
      (e) =>
        e.opportunityId === task.opportunityId &&
        Date.parse(e.recordedAt || e.at) <= Date.parse(now) &&
        Date.parse(e.occurredAt || e.at) <= Date.parse(now) &&
        Date.parse(e.at) >= Date.parse(task.assignedAt || plan.createdAt) &&
        Math.floor(Date.parse(e.occurredAt || e.at) / 60000) >=
          Math.floor(Date.parse(task.assignedAt || plan.createdAt) / 60000) &&
        localDay(e.occurredAt || e.at) === plan.day &&
        accepts.includes(e.type),
    );
    return { ...task, done };
  });
  const completed = tasks.filter((t) => t.done).length;
  const batches = [];
  for (let i = 0; i < tasks.length; i += DAILY_BATCH_SIZE) {
    const group = tasks.slice(i, i + DAILY_BATCH_SIZE);
    const done = group.filter((t) => t.done).length;
    batches.push({
      index: batches.length,
      tasks: group,
      completed: done,
      total: group.length,
      done: done === group.length,
    });
  }
  const firstPending = batches.findIndex((b) => !b.done);
  const activeBatch =
    firstPending === -1 ? Math.max(0, batches.length - 1) : firstPending;
  return {
    tasks,
    completed,
    total: tasks.length,
    percent: tasks.length ? Math.round((completed / tasks.length) * 100) : 0,
    batches: batches.map((b) => ({ ...b, unlocked: b.index <= activeBatch })),
    activeBatch,
    completedBatches: batches.filter((b) => b.done).length,
  };
}
export function actionGuide(deal, type) {
  const company = deal.account || "esta empresa",
    product = deal.product;
  const contact = deal.contact?.name || "o responsável pela compra";
  const branch = (when, then, action, nextAction) => ({
    when,
    then,
    action,
    nextAction,
  });
  if (type === "pause")
    return {
      title: "Respeite a pausa solicitada",
      objective: "Registre o motivo e quando o cliente autorizou retomar.",
      steps: [
        "Não insista durante a pausa combinada.",
        "O retorno reaparece quando a data chegar.",
      ],
      branches: [],
      suggestedNext: "Retomar após a pausa solicitada",
    };
  if (
    type === "contact" &&
    deal.healthDetails?.risks.some((r) => r.code === "financial_block")
  )
    return {
      title: "Revise as condições antes do retorno",
      objective:
        "O cliente informou um bloqueio financeiro. Prepare uma alternativa antes da data combinada.",
      steps: [
        "Revise escopo, valor e condições que podem resolver o bloqueio.",
        "Não antecipe o contato combinado sem outro motivo confirmado.",
        "No retorno, valide a alternativa e registre o que o cliente confirmou.",
      ],
      branches: [],
      suggestedNext: deal.nextTask?.label || "Validar condições com o cliente",
    };
  if (type === "profile")
    return {
      title: deal.contact
        ? "Confira quem participa da compra"
        : "Descubra com quem falar",
      objective: `Identifique um contato de ${company} que conheça a negociação de ${product}.`,
      steps: [
        deal.account
          ? `Confirme no CRM ou na origem do lead quem responde por ${product} em ${company}.`
          : "Confira a origem da oportunidade e identifique a empresa antes de abordar.",
        "Cadastre nome e pelo menos um canal verificado: telefone ou e-mail.",
        "Não deduza o comprador a partir do porte ou do setor da empresa.",
      ],
      branches: [
        branch(
          "Contato identificado",
          "Faça a primeira conversa e confirme se a negociação continua válida.",
          "contact",
          "Confirmar necessidade, decisor e prazo",
        ),
      ],
      suggestedNext: "Confirmar necessidade, decisor e prazo",
    };
  if (type === "qualify")
    return {
      title: "Confirme se já existe uma oportunidade de compra",
      objective: `Antes de classificar ${company} como SQL, registre o que o cliente confirmou.`,
      steps: [
        `Necessidade: qual problema ${product} precisa resolver? Registre nas palavras do cliente.`,
        `Decisão: ${contact} decide a compra? Se não, quem aprova e como?`,
        "Prazo: existe uma data ou acontecimento que orienta a decisão?",
      ],
      branches: [
        branch(
          "Os três pontos estão confirmados",
          "Salve o SQL, prepare a proposta e combine a apresentação ao decisor.",
          "proposal",
          "Apresentar proposta ao decisor",
        ),
        branch(
          "Falta uma resposta",
          "Continue a conversa para preencher a lacuna. Ainda não confirme SQL.",
          "contact",
          "Validar a informação pendente de qualificação",
        ),
      ],
      suggestedNext: "Apresentar proposta ao decisor",
    };
  if (type === "proposal")
    return {
      title: "Transforme a necessidade em uma proposta",
      objective: `Apresente ${product} para resolver “${deal.qualification?.need || "a necessidade ainda não confirmada"}”.`,
      steps: [
        "Confirme escopo, quantidade e preço negociado; o catálogo não é o valor final.",
        `Valide a aprovação com ${deal.qualification?.authority || "o decisor que precisa ser identificado"}.`,
        "Envie a proposta e combine quando e como o cliente dará o retorno.",
      ],
      branches: [
        branch(
          "Cliente aceitou e confirmou a compra",
          "Registre a venda com o valor real e a evidência da confirmação.",
          "won",
          null,
        ),
        branch(
          "Cliente trouxe dúvidas ou objeções",
          "Retome os pontos específicos antes de pedir a decisão.",
          "contact",
          "Resolver as objeções da proposta",
        ),
        branch(
          "Cliente pediu mais tempo",
          "Agende a data combinada, sem registrar o negócio como ganho.",
          "followup",
          "Retomar a decisão sobre a proposta",
        ),
      ],
      suggestedNext: "Retomar proposta e critérios de decisão",
    };
  if (type === "won")
    return {
      title: "Confirme o fechamento antes de comemorar",
      objective:
        "A venda só deve ser registrada quando houver uma confirmação verificável.",
      steps: [
        "Registre como o cliente confirmou a compra.",
        "Informe o valor real acordado em USD, sem copiar automaticamente o catálogo.",
        "Depois, combine entrega e passagem para atendimento com o time responsável.",
      ],
      branches: [],
      suggestedNext: null,
    };
  if (type === "lost")
    return {
      title: "Feche o ciclo com um motivo útil",
      objective:
        "Diferencie falta de resposta de uma perda efetivamente confirmada.",
      steps: [
        "Registre o motivo concreto: preço, escopo, momento, concorrência ou desistência.",
        "Inclua o contexto informado pelo cliente.",
        "Se só falta retorno, prefira agendar nova tentativa em vez de presumir perda.",
      ],
      branches: [
        branch(
          "Ainda não há uma decisão confirmada",
          "Agende uma tentativa de contato antes de encerrar.",
          "followup",
          "Confirmar se a compra ainda está em avaliação",
        ),
      ],
      suggestedNext: null,
    };
  if (type === "followup")
    return {
      title: "Transforme o retorno em um compromisso",
      objective: `Defina o que precisa ser retomado com ${company}, não apenas “fazer follow-up”.`,
      steps: [
        deal.nextTask
          ? `Revise o compromisso anterior: ${deal.nextTask.label}.`
          : "Escreva o assunto pendente da conversa.",
        "Combine uma data e hora realistas com o cliente.",
        "Quando chegar o prazo, registre o resultado e defina o avanço seguinte.",
      ],
      branches: [
        branch(
          "Chegou a hora combinada",
          "Retome o assunto, registre a resposta e o novo próximo passo.",
          "contact",
          "Confirmar a decisão e a próxima ação",
        ),
      ],
      suggestedNext:
        deal.nextTask?.label || "Retomar a decisão e combinar próximo passo",
    };
  if (type === "note")
    return {
      title: "Registre o que ajuda a próxima conversa",
      objective:
        "Guarde contexto concreto; uma nota sozinha não representa avanço de etapa.",
      steps: [
        "Registre uma informação confirmada ou uma objeção relevante.",
        "Se houve contato ou avanço comercial, use a ação correspondente para atualizar o pipeline.",
      ],
      branches: [
        branch(
          "Já sabe o que precisa validar",
          "Converse com o cliente e registre o resultado.",
          "contact",
          "Validar o ponto registrado na nota",
        ),
      ],
      suggestedNext: null,
    };
  return {
    title: deal.overdue
      ? "Cumpra o retorno que ficou pendente"
      : deal.review
        ? "Valide se a negociação continua de pé"
        : "Faça uma conversa com objetivo claro",
    objective: deal.qualification
      ? `Retome “${deal.qualification.need}” com ${contact} e confirme a decisão sobre ${product}.`
      : `Converse com ${contact} para entender se ${company} ainda avalia ${product}.`,
    steps: [
      deal.nextTask
        ? `Comece pelo combinado: ${deal.nextTask.label}.`
        : deal.review
          ? `A negociação era longa no histórico. Pergunte o que mudou desde a avaliação de ${product}.`
          : `Confirme o interesse atual em ${product}; estágio e score não garantem intenção de compra.`,
      deal.qualification
        ? `Pergunte o que falta para ${deal.qualification.authority} decidir.`
        : "Descubra o problema, quem decide e quando a compra pode acontecer.",
      "Registre a resposta ou a tentativa e marque um próximo passo específico.",
    ],
    branches: [
      branch(
        "Cliente respondeu e há interesse",
        "Confirme necessidade, decisor e prazo. Se já estão confirmados, avance para proposta.",
        deal.qualification ? "proposal" : "qualify",
        deal.qualification
          ? "Apresentar proposta ao decisor"
          : "Validar necessidade, decisor e prazo",
      ),
      branch(
        "Não houve resposta",
        "Registre a tentativa e agende uma nova abordagem. Não confirme SQL só por tentar contato.",
        "followup",
        "Nova tentativa de contato com objetivo definido",
      ),
      branch(
        "Cliente confirmou que não seguirá",
        "Registre a perda e o motivo concreto.",
        "lost",
        null,
      ),
    ],
    suggestedNext: deal.qualification
      ? "Apresentar proposta e combinar decisão"
      : "Validar necessidade, decisor e prazo",
  };
}
export function afterAction(type, deal) {
  const next = {
    pause: [
      "Pausa registrada. Retome na data combinada.",
      "A oportunidade fica fora da fila de contato até a data solicitada pelo cliente.",
      null,
    ],
    profile: [
      "Contato salvo. Agora valide o interesse.",
      "Converse com o responsável e confirme se a avaliação do produto continua ativa.",
      "contact",
    ],
    contact: deal.qualification
      ? [
          "Conversa registrada. Prepare o avanço.",
          "Se o cliente confirmou as condições, prepare a proposta. Se falta informação, use novo contato.",
          "proposal",
        ]
      : [
          "Conversa registrada. Confirme a qualificação.",
          "Só confirme SQL quando necessidade, decisor e prazo estiverem claros. Se ainda faltam respostas, continue o contato.",
          "qualify",
        ],
    qualify: [
      "SQL confirmado. Hora de apresentar uma solução.",
      "Prepare uma proposta com escopo e condições alinhados ao que o cliente confirmou.",
      "proposal",
    ],
    proposal: [
      "Proposta registrada. Acompanhe a decisão.",
      "No retorno combinado, valide dúvidas e critérios de aprovação antes de registrar o fechamento.",
      "contact",
    ],
    followup: [
      "Retorno agendado. O compromisso está na sua agenda.",
      "Na data combinada, registre o resultado da conversa.",
      "contact",
    ],
    won: [
      "Venda registrada. Alinhe a entrega.",
      "Faça a passagem para atendimento com escopo, condições e expectativas combinadas.",
      null,
    ],
    lost: [
      "Perda registrada. O motivo ficou no histórico.",
      "Use o motivo para revisar a abordagem de oportunidades semelhantes.",
      null,
    ],
    note: [
      "Contexto salvo. Use-o na próxima conversa.",
      "Retome o ponto registrado e confirme o próximo passo com o cliente.",
      "contact",
    ],
  };
  const [title, text, action] = next[type] || next.note;
  return { title, text, action };
}

export function recommendedAction(deal) {
  if (deal.status === "proposal") return "contact";
  if (deal.qualification) return "proposal";
  return deal.contact ? "contact" : "profile";
}
