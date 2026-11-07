import test from "node:test";
import assert from "node:assert/strict";
import { materialize, prioritize, validateActivity } from "../lib/workflow.mjs";
import { selectSellerWorkspace } from "../lib/workspace-selectors.mjs";
import { createDailyPlan, localDay } from "../lib/sales-guide.mjs";

const now = "2026-11-06T15:00:00Z",
  DAY = 86400000;
const date = (days) => new Date(Date.parse(now) + days * DAY).toISOString();
const base = {
  opportunity_id: "A",
  account: "Conta QA",
  sales_agent: "Ana",
  product: "GTX",
  score: 90,
  age: 30,
  reference: { days: 40 },
  deal_stage: "Engaging",
};
let sequence = 0;
const e = (type, fields = {}, days = 0) => ({
  id: `E${++sequence}`,
  opportunityId: "A",
  type,
  at: date(days),
  notes: "Evidência fictícia de QA",
  ...fields,
});
const next = {
  nextAction: "Apresentar solução",
  dueAt: date(2),
  nextStepAccepted: "yes",
};
const q = {
  need: "Problema confirmado",
  authority: "Decisor identificado",
  timing: "Decisão neste mês",
};
const full = () => [
  e("qualify", { ...q, ...next, buyerResponse: "confirmed" }),
  e("proposal", {
    ...next,
    buyerResponse: "confirmed",
    financialStatus: "compatible",
    quotedAmount: "1000",
    quoteCurrency: "USD",
  }),
];
const state = (events = [], overrides = {}, at = now) =>
  materialize({ ...base, ...overrides }, events, at);

test("C01: alto valor não mascara silêncio do comprador", () => {
  const d = state(
    [e("qualify", { ...q, ...next, buyerResponse: "confirmed" }, -20)],
    { sales_price: 99999 },
  );
  assert.equal(d.healthDetails.tone, "red");
  assert.ok(d.healthDetails.risks.some((r) => r.code === "buyer_silence"));
});
test("C02/P1: retorno vencido de menor valor precede negócio maior agendado", () => {
  const smaller = state(
    [
      e(
        "contact",
        { buyerResponse: "confirmed", nextAction: "Retornar", dueAt: date(-1) },
        -2,
      ),
    ],
    { score: 40 },
  );
  const bigger = state(
    full().map((e) => ({ ...e, opportunityId: "B" })),
    { opportunity_id: "B", score: 99 },
  );
  assert.equal(prioritize([bigger, smaller], now)[0].opportunity_id, "A");
});
test("C03/P3: tentativas não contam como resposta nem renovam sua recência", () => {
  const attempts = Array.from({ length: 10 }, () =>
    e("contact", { buyerResponse: "none" }),
  );
  const d = state(attempts);
  assert.equal(d.healthDetails.lastBuyerReplyAt, null);
  assert.equal(d.health, null);
  assert.equal(
    d.healthDetails.factors.find((f) => f.key === "response").points,
    0,
  );
  const before = state([e("contact", { buyerResponse: "confirmed" }, -10)]);
  const after = state([
    e("contact", { buyerResponse: "confirmed" }, -10),
    ...attempts,
  ]);
  assert.equal(
    before.healthDetails.lastBuyerReplyAt,
    after.healthDetails.lastBuyerReplyAt,
  );
});
test("C04/P2: resposta recente pode priorizar descoberta sobre negócio caro parado", () => {
  const discovery = state([e("contact", { buyerResponse: "confirmed" })], {
    deal_stage: "Prospecting",
    score: 32,
  });
  const stalled = state(
    [e("contact", { buyerResponse: "none", opportunityId: "B" }, -20)],
    {
      opportunity_id: "B",
      score: 95,
    },
  );
  assert.equal(prioritize([stalled, discovery], now)[0].opportunity_id, "A");
});
test("C05: tarefa unilateral não comprova aceite", () => {
  const d = state([
    e("qualify", {
      ...q,
      ...next,
      buyerResponse: "confirmed",
      nextStepAccepted: "no",
    }),
  ]);
  assert.equal(
    d.healthDetails.factors.find((f) => f.key === "accepted").points,
    0,
  );
  assert.notEqual(d.healthDetails.tone, "green");
});
test("C06: compromisso futuro aguarda na agenda", () => {
  const d = state(full());
  assert.equal(d.health, 100);
  assert.equal(d.healthDetails.tone, "green");
  assert.equal(prioritize([d], now).length, 0);
});
test("C07/P5: retorno que vence fora do lote aparece acima da rodada", () => {
  const others = Array.from({ length: 6 }, (_, i) => ({
    ...base,
    opportunity_id: `B${i}`,
    score: 99 - i,
  }));
  const plan = createDailyPlan(
    others.map((d) => materialize(d, [], now)),
    now,
  );
  const urgent = state(
    [e("contact", { nextAction: "Retorno devido", dueAt: date(-1) }, -2)],
    { score: 30 },
  );
  const model = selectSellerWorkspace(
    [...others.map((d) => materialize(d, [], now)), urgent],
    "Ana",
    urgent.activities,
    { [`${localDay(now)}|Ana`]: plan },
    now,
  );
  assert.equal(model.top[0].opportunity_id, "A");
  assert.ok(!plan.tasks.some((t) => t.opportunityId === "A"));
});
test("C08: qualificação antiga exige reconfirmação", () => {
  const d = state([
    e("qualify", { ...q, ...next, buyerResponse: "confirmed" }, -40),
  ]);
  assert.equal(d.healthDetails.factors.find((f) => f.key === "need").points, 0);
  assert.equal(d.healthDetails.tone, "red");
});
test("C09: bloqueio financeiro prevalece sobre nota bruta alta", () => {
  const d = state([
    ...full(),
    e("proposal", { ...next, financialStatus: "blocked" }),
  ]);
  assert.equal(d.health, 90);
  assert.equal(d.healthDetails.tone, "red");
});
test("C10/P4: legado sem campo estruturado permanece desconhecido", () => {
  const d = state([
    e("qualify", { ...q, nextAction: next.nextAction, dueAt: next.dueAt }),
  ]);
  assert.equal(d.qualification.need, q.need);
  assert.equal(d.health, null);
  assert.equal(d.healthDetails.label, "Em validação");
  assert.equal(d.healthDetails.lastBuyerReplyAt, null);
});
test("C11: nota não melhora participação nem reinicia relógio", () => {
  const original = [e("contact", { buyerResponse: "confirmed" }, -10)];
  const a = state(original),
    b = state([
      ...original,
      e("note", { buyerResponse: "confirmed", financialStatus: "compatible" }),
    ]);
  assert.deepEqual(a.healthDetails, b.healthDetails);
});
test("C12: evidência repetida não duplica efeitos nem histórico projetado", () => {
  const events = full();
  assert.deepEqual(state(events), state([...events, ...events]));
});
test("C13: pausa explícita impede contato mesmo com compromisso antigo vencido", () => {
  const d = state([
    e("contact", { nextAction: "Retornar", dueAt: date(-1) }, -2),
    e("pause", { pauseUntil: date(7) }),
  ]);
  assert.equal(d.priority.label, "Pausa solicitada");
  assert.equal(prioritize([d], now).length, 0);
  assert.equal(state(d.activities, {}, date(8)).priority.rank, 0);
});
test("C14: encerrada não tem saúde nem prioridade ativa", () => {
  const d = state([...full(), e("won", { amount: 100 })]);
  assert.equal(d.health, null);
  assert.equal(prioritize([d], now).length, 0);
});
test("C15: valor fechado futuro não entra em saúde ou ordenação prévia", () => {
  const events = full();
  const a = state(events, { close_value: 1 }),
    b = state(events, { close_value: 999999 });
  assert.deepEqual(a.healthDetails, b.healthDetails);
  assert.deepEqual(a.priority, b.priority);
});
test("C16: ausência de data não inventa idade ou resposta recente", () => {
  const d = state([], { age: null, engage_date: null });
  assert.equal(d.age, null);
  assert.equal(d.health, null);
});
test("C17: nome da conta e vendedor não pontuam saúde", () => {
  const events = full();
  assert.deepEqual(
    state(events).healthDetails,
    state(events, { account: "Outra", sales_agent: "Outro" }).healthDetails,
  );
});
test("C18: resposta de outra oportunidade da conta não aquece esta", () => {
  const d = state(full().map((x) => ({ ...x, opportunityId: "B" })));
  assert.equal(d.health, null);
  assert.equal(d.activities.length, 0);
});
test("C19: ocorrência antiga registrada hoje continua antiga", () => {
  const d = state([
    e("contact", {
      buyerResponse: "confirmed",
      occurredAt: date(-20),
      recordedAt: now,
    }),
  ]);
  assert.equal(d.healthDetails.lastBuyerReplyAt, date(-20));
  assert.equal(d.healthDetails.recentReply, false);
});
test("C20: corte temporal impede evidência futura e lançamento posterior ao corte", () => {
  assert.equal(
    state([e("contact", { buyerResponse: "confirmed" }, 1)]).activities.length,
    0,
  );
  assert.equal(
    state([
      e("contact", {
        buyerResponse: "confirmed",
        occurredAt: date(-5),
        recordedAt: date(1),
      }),
    ]).activities.length,
    0,
  );
  const events = full();
  assert.equal(state(events, {}, date(-1)).health, null);
});
test("P6: valores de proposta só desempatam em moeda/unidade comparáveis", () => {
  const a = state(
    [e("proposal", { quotedAmount: 100, quoteCurrency: "USD" })],
    { score: 90 },
  );
  const b = state(
    [e("proposal", { quotedAmount: 200, quoteCurrency: "USD" })].map((x) => ({
      ...x,
      opportunityId: "B",
    })),
    { opportunity_id: "B", score: 90 },
  );
  assert.equal(prioritize([a, b], now)[0].opportunity_id, "B");
});
test("entrada rejeita ocorrência futura, proposta inválida e pausa sem data", () => {
  assert.ok(
    validateActivity(
      state(),
      { type: "note", notes: "QA", occurredAt: date(1) },
      now,
    ),
  );
  assert.ok(validateActivity(state(), { type: "pause", notes: "QA" }, now));
  assert.ok(
    validateActivity(
      state(),
      {
        type: "proposal",
        notes: "QA",
        quotedAmount: "-10",
        quoteCurrency: "USD",
      },
      now,
    ),
  );
});

test("bloqueio financeiro aparece no foco mesmo após concluir a tarefa da rodada", () => {
  const events = [
    ...full(),
    e("proposal", { ...next, financialStatus: "blocked" }),
  ];
  const d = state(events);
  const plan = {
    day: localDay(now),
    createdAt: date(-1),
    version: 2,
    tasks: [{ opportunityId: "A", goal: "proposal", label: "Enviar proposta" }],
  };
  const model = selectSellerWorkspace(
    [d],
    "Ana",
    events,
    { [localDay(now) + "|Ana"]: plan },
    now,
  );
  assert.equal(model.progress.completed, 1);
  assert.equal(model.top[0].opportunity_id, "A");
  assert.match(model.top[0].priority.action, /condições/);
});
test("primeira tentativa sem resposta não é rotulada imediatamente como silêncio prolongado", () => {
  assert.equal(
    state([e("contact", { buyerResponse: "none" })]).healthDetails.risks.length,
    0,
  );
});
test("data de evidência futura não conclui checkpoint antes do corte", () => {
  const plan = {
    day: localDay(now),
    createdAt: date(-1),
    version: 2,
    tasks: [{ opportunityId: "A", goal: "contact", label: "Conversar" }],
  };
  const events = [
    e("contact", { at: new Date(Date.parse(now) + 60000).toISOString() }),
  ];
  const model = selectSellerWorkspace(
    [state(events)],
    "Ana",
    events,
    { [localDay(now) + "|Ana"]: plan },
    now,
  );
  assert.equal(model.progress.completed, 0);
});

test("registrar hoje uma conversa antiga não conclui tarefa de hoje", () => {
  const plan = {
    day: localDay(now),
    createdAt: now,
    version: 2,
    tasks: [{ opportunityId: "A", goal: "contact", label: "Conversar" }],
  };
  const events = [
    e("contact", { occurredAt: date(-1), buyerResponse: "confirmed" }),
  ];
  const model = selectSellerWorkspace(
    [state(events)],
    "Ana",
    events,
    { [localDay(now) + "|Ana"]: plan },
    now,
  );
  assert.equal(model.progress.completed, 0);
});
