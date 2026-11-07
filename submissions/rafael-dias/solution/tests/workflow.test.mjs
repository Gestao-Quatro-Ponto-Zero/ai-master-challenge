import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import {
  materialize,
  validateActivity,
  prioritize,
  funnelCounts,
  reasonFor,
} from "../lib/workflow.mjs";
const deal = {
  opportunity_id: "A",
  account: "Conta",
  sales_agent: "Ana",
  score: 90,
  age: 30,
  deal_stage: "Engaging",
  product: "GTX",
  reference: { days: 40 },
};
const event = (type, fields = {}) => ({
  id: type,
  opportunityId: "A",
  type,
  at: "2026-11-06T10:00:00Z",
  notes: "Contexto confirmado",
  ...fields,
});
const next = { nextAction: "Retomar decisão", dueAt: "2099-01-01T12:00:00Z" };
const qualification = {
  need: "Ampliar operação",
  authority: "Diretoria",
  timing: "Dezembro",
};
test("alto score não cria SQL nem inventa saúde antes de atividades", () => {
  const state = materialize(deal);
  assert.equal(state.status, "new");
  assert.equal(state.qualification, null);
  assert.equal(state.health, null);
  assert.ok(
    validateActivity(state, { type: "qualify", notes: "Teste", ...next }),
  );
});
test("fluxo de qualificação a venda exige evidências, valor e preserva o original", () => {
  let events = [event("contact", next)];
  let state = materialize(deal, events);
  assert.equal(state.status, "contacted");
  assert.equal(state.health, null);
  assert.ok(validateActivity(state, event("proposal", next)));
  assert.equal(
    validateActivity(state, event("qualify", { ...next, ...qualification })),
    null,
  );
  events.push(event("qualify", { ...next, ...qualification }));
  state = materialize(deal, events);
  assert.equal(state.status, "qualified");
  assert.equal(state.health, null);
  assert.equal(validateActivity(state, event("proposal", next)), null);
  events.push(event("proposal", next));
  state = materialize(deal, events);
  assert.equal(state.status, "proposal");
  events.push(event("qualify", { ...next, ...qualification }));
  state = materialize(deal, events);
  assert.equal(state.status, "proposal");
  assert.ok(validateActivity(state, event("won", { amount: 0 })));
  assert.equal(validateActivity(state, event("won", { amount: 2000 })), null);
  events.push(event("won", { amount: 2000 }));
  state = materialize(deal, events);
  assert.equal(state.status, "won");
  assert.equal(state.actualValue, 2000);
  assert.equal(state.nextTask, null);
  assert.equal(state.health, null);
  assert.equal(prioritize([state]).length, 0);
  assert.ok(validateActivity(state, event("note")));
  assert.equal(deal.status, undefined);
  assert.equal(deal.score, 90);
});
test("retorno sai do foco antes do prazo e reaparece vencido, considerando fuso", () => {
  const events = [
    event("contact", {
      nextAction: "Ligar",
      dueAt: "2026-11-06T09:00:00-03:00",
    }),
  ];
  let state = materialize(deal, events, "2026-11-06T11:59:00Z");
  assert.equal(state.scheduled, true);
  assert.equal(prioritize([state]).length, 0);
  state = materialize(deal, events, "2026-11-06T12:00:00Z");
  assert.equal(state.overdue, true);
  assert.equal(state.health, null);
  assert.match(reasonFor(state), /venceu/);
  assert.equal(
    prioritize([
      materialize({ ...deal, opportunity_id: "B", score: 100 }),
      state,
    ])[0].opportunity_id,
    "A",
  );
});
test("identificação atualiza contato sem alterar pontos nem criar SQL", () => {
  const missing = { ...deal, account: null };
  let state = materialize(missing);
  assert.ok(
    validateActivity(
      state,
      event("profile", { account: "Nova", contactName: "Ana" }),
    ),
  );
  assert.ok(
    validateActivity(state, event("qualify", { ...next, ...qualification })),
  );
  const profile = event("profile", {
    account: "Nova",
    contactName: "Ana",
    email: "ana@example.com",
  });
  assert.equal(validateActivity(state, profile), null);
  state = materialize(missing, [profile]);
  assert.equal(state.account, "Nova");
  assert.equal(state.contact.email, "ana@example.com");
  assert.equal(state.score, 90);
  assert.equal(state.status, "new");
});
test("tarefas exigem data futura e próximo passo, perda exige motivo", () => {
  const state = materialize(deal);
  assert.ok(
    validateActivity(
      state,
      event("contact", { nextAction: "Ligar", dueAt: "2017-01-01" }),
    ),
  );
  assert.ok(validateActivity(state, event("contact", { dueAt: next.dueAt })));
  assert.ok(validateActivity(state, event("lost", { notes: "" })));
  assert.equal(validateActivity(state, event("lost")), null);
});
test("atividades de um vendedor não vazam para oportunidades de outro", () => {
  const events = [event("qualify", { ...qualification, ...next })];
  const rows = [
    materialize(deal, events),
    materialize({ ...deal, opportunity_id: "B", sales_agent: "Bruno" }, events),
  ];
  assert.equal(rows[1].activities.length, 0);
  assert.equal(rows[1].qualification, null);
  const counts = funnelCounts(rows);
  assert.equal(counts.qualified, 1);
  assert.equal(counts.new, 1);
  assert.equal(
    Object.values(counts).reduce((a, b) => a + b),
    2,
  );
});
test("histórico por vendedor reconcilia empresa e não contamina o score", async () => {
  const data = JSON.parse(await fs.readFile("data/prepared.json", "utf8"));
  assert.equal(data.historicalByAgent.length, 35);
  assert.equal(
    data.historicalByAgent.reduce((n, h) => n + h.won, 0),
    4238,
  );
  assert.equal(
    data.historicalByAgent.reduce((n, h) => n + h.lost, 0),
    2473,
  );
  assert.equal(data.opportunities.length, 2089);
  for (const d of data.opportunities) assert.equal(d.close_value, undefined);
});
