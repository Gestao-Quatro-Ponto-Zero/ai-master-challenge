import { evidenceEvents } from "./evidence.mjs";
import { calculateHealth } from "./health.mjs";
import { priorityDecision, rankOpportunities } from "./priority.mjs";
export const STAGES = [
  { id: "new", label: "A trabalhar" },
  { id: "contacted", label: "Contato realizado" },
  { id: "qualified", label: "SQL confirmado" },
  { id: "proposal", label: "Proposta enviada" },
  { id: "won", label: "Venda ganha" },
  { id: "lost", label: "Perdida" },
];
export const isClosed = (d) => ["won", "lost"].includes(d.status);
export function validateActivity(
  deal,
  activity,
  now = new Date().toISOString(),
) {
  const types = [
    "contact",
    "qualify",
    "proposal",
    "followup",
    "won",
    "lost",
    "note",
    "profile",
    "pause",
  ];
  if (!types.includes(activity.type)) return "Escolha uma ação válida.";
  if (isClosed(deal))
    return "Esta oportunidade já foi encerrada nesta demonstração.";
  for (const [key, allowed] of Object.entries({
    buyerResponse: ["unknown", "confirmed", "none"],
    nextStepAccepted: ["unknown", "yes", "no"],
    financialStatus: ["unknown", "compatible", "blocked"],
  })) {
    if (activity[key] && !allowed.includes(activity[key]))
      return "Escolha uma evidência válida.";
  }
  if (
    activity.occurredAt &&
    (!Number.isFinite(Date.parse(activity.occurredAt)) ||
      Date.parse(activity.occurredAt) > Date.parse(now))
  )
    return "Informe quando a ação aconteceu, sem data futura.";
  if (
    activity.type === "pause" &&
    (!activity.pauseUntil ||
      !Number.isFinite(Date.parse(activity.pauseUntil)) ||
      Date.parse(activity.pauseUntil) <= Date.parse(now))
  )
    return "Informe uma data futura para retomar após a pausa.";
  if (
    activity.quotedAmount != null &&
    activity.quotedAmount !== "" &&
    (!Number.isFinite(Number(activity.quotedAmount)) ||
      Number(activity.quotedAmount) <= 0 ||
      activity.quoteCurrency !== "USD")
  )
    return "Informe um valor de proposta positivo em USD.";
  if (activity.type === "profile") {
    if (!activity.account?.trim() || !activity.contactName?.trim())
      return "Informe a conta e o nome do contato.";
    if (!activity.email?.trim() && !activity.phone?.trim())
      return "Informe e-mail ou telefone do contato.";
    if (activity.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(activity.email))
      return "Informe um e-mail válido.";
    return null;
  }
  if (!activity.notes?.trim())
    return "Registre o contexto ou resultado da ação.";
  if (["contact", "qualify", "proposal", "followup"].includes(activity.type)) {
    if (
      !activity.nextAction?.trim() ||
      !activity.dueAt ||
      !Number.isFinite(Date.parse(activity.dueAt))
    )
      return "Combine a próxima ação e informe data e hora.";
    if (Date.parse(activity.dueAt) <= Date.parse(now))
      return "Agende a próxima ação para uma data e hora futura.";
  }
  if (activity.type === "qualify") {
    if (!deal.account) return "Identifique a conta antes de confirmar um SQL.";
    if (
      !activity.need?.trim() ||
      !activity.authority?.trim() ||
      !activity.timing?.trim()
    )
      return "Confirme necessidade, decisor e prazo com evidências para classificar como SQL.";
  }
  if (["proposal", "won"].includes(activity.type) && !deal.qualification)
    return "Confirme a qualificação comercial antes de avançar para proposta ou venda.";
  if (
    activity.type === "won" &&
    (!Number.isFinite(Number(activity.amount)) || Number(activity.amount) <= 0)
  )
    return "Informe o valor real da venda, maior que zero.";
  return null;
}
export function materialize(deal, events = [], now = new Date().toISOString()) {
  const state = {
    ...deal,
    originalAccount: deal.account,
    status: "new",
    activities: [],
    nextTask: null,
    qualification: null,
    contact: null,
    actualValue: null,
    pauseUntil: null,
    quote: null,
  };
  const relevant = evidenceEvents(events, deal.opportunity_id, now);
  for (const e of relevant) {
    state.activities.push(e);
    if (e.type === "profile") {
      state.account = e.account;
      state.contact = {
        name: e.contactName,
        email: e.email || "",
        phone: e.phone || "",
      };
    }
    if (e.type === "contact" && state.status === "new")
      state.status = "contacted";
    if (e.type === "qualify") {
      state.qualification = {
        need: e.need,
        authority: e.authority,
        timing: e.timing,
      };
      if (["new", "contacted", "qualified"].includes(state.status))
        state.status = "qualified";
    }
    if (e.type === "proposal") state.status = "proposal";
    if (
      ["contact", "qualify", "proposal", "followup"].includes(e.type) &&
      e.buyerResponse === "confirmed"
    )
      state.pauseUntil = null;
    if (
      e.type === "proposal" &&
      Number(e.quotedAmount) > 0 &&
      e.quoteCurrency === "USD"
    )
      state.quote = {
        amount: Number(e.quotedAmount),
        currency: "USD",
        at: e.occurredAt || e.at,
      };
    if (
      ["contact", "qualify", "proposal", "followup"].includes(e.type) &&
      e.nextAction &&
      e.dueAt
    )
      state.nextTask = {
        label: e.nextAction,
        dueAt: e.dueAt,
        accepted: e.nextStepAccepted || "unknown",
      };
    if (e.type === "pause") {
      state.pauseUntil = e.pauseUntil;
      state.nextTask = {
        label: "Retomar após a pausa solicitada",
        dueAt: e.pauseUntil,
        accepted: "yes",
      };
    }
    if (e.type === "won" || e.type === "lost") {
      state.status = e.type;
      state.nextTask = null;
      state.actualValue = e.type === "won" ? Number(e.amount) : 0;
      state.closedAt = e.at;
    }
  }
  state.overdue =
    !!state.nextTask && Date.parse(state.nextTask.dueAt) <= Date.parse(now);
  state.scheduled =
    !!state.nextTask && Date.parse(state.nextTask.dueAt) > Date.parse(now);
  state.healthDetails = calculateHealth(state, now);
  state.health = state.healthDetails.score;
  state.priority = priorityDecision(state, now);
  return state;
}
export function reasonFor(deal) {
  return deal.priority?.reason || priorityDecision(deal).reason;
}
export function prioritize(deals, now = new Date().toISOString()) {
  return rankOpportunities(deals, now);
}
export function funnelCounts(deals) {
  return Object.fromEntries(
    STAGES.map((s) => [s.id, deals.filter((d) => d.status === s.id).length]),
  );
}
