import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import {
  createDailyPlan,
  ensureDailyPlan,
  dailyProgress,
  actionGuide,
  afterAction,
} from "../lib/sales-guide.mjs";
import { materialize } from "../lib/workflow.mjs";
const start = "2026-11-06T15:00:00Z";
const deals = Array.from({ length: 25 }, (_, i) =>
  materialize(
    {
      opportunity_id: `D${i}`,
      account: `Conta ${i}`,
      sales_agent: "Ana",
      product: "GTX Pro",
      score: 90 - i,
      deal_stage: "Engaging",
      age: 20,
      reference: { days: 40 },
    },
    [],
    start,
  ),
);
test("plano escolhe até vinte tarefas reais e não cresce com as conclusões", () => {
  const plan = createDailyPlan(deals, start);
  assert.equal(plan.tasks.length, 20);
  assert.equal(plan.tasks[0].goal, "contact");
  const events = [
    { opportunityId: "D0", type: "contact", at: "2026-11-06T15:01:00Z" },
  ];
  const progress = dailyProgress(plan, events);
  assert.equal(progress.completed, 1);
  assert.equal(progress.total, 20);
  assert.equal(progress.percent, 5);
  assert.equal(dailyProgress(plan, [...events, ...events]).completed, 1);
});
test("nota ou reagendamento não concluem tarefa de contato; evento antigo também não", () => {
  const plan = createDailyPlan(
    deals.map((d) => ({ ...d, contact: { name: "Teste" } })),
    start,
  );
  for (const type of ["note", "followup"])
    assert.equal(
      dailyProgress(plan, [
        { opportunityId: "D0", type, at: "2026-11-06T15:01:00Z" },
      ]).completed,
      0,
    );
  assert.equal(
    dailyProgress(plan, [
      { opportunityId: "D0", type: "contact", at: "2026-11-06T14:59:00Z" },
    ]).completed,
    0,
  );
  assert.equal(
    dailyProgress(plan, [
      { opportunityId: "D0", type: "contact", at: "2026-11-06T15:01:00Z" },
    ]).completed,
    1,
  );
  assert.equal(
    dailyProgress(plan, [
      { opportunityId: "D0", type: "contact", at: "2026-11-07T15:01:00Z" },
    ]).completed,
    0,
  );
});
test("retornos de hoje entram antes de novas contas e carteira vazia não inventa meta", () => {
  const due = {
    ...deals[6],
    nextTask: { label: "Decidir proposta", dueAt: start },
    overdue: true,
  };
  assert.equal(
    createDailyPlan([...deals.slice(0, 6), due], start).tasks[0].opportunityId,
    "D6",
  );
  assert.equal(createDailyPlan([], start).tasks.length, 0);
  assert.equal(dailyProgress(null, []).percent, 0);
});
test("roteiro usa fatos da conta e muda de acordo com a ação e a qualificação", () => {
  const d = { ...deals[0], contact: { name: "Responsável verificado" } };
  const contact = actionGuide(d, "contact");
  assert.match(contact.objective, /Conta 0/);
  assert.match(contact.objective, /GTX Pro/);
  assert.ok(contact.branches.some((b) => b.action === "qualify"));
  assert.ok(
    contact.branches.some(
      (b) => b.when === "Não houve resposta" && b.action === "followup",
    ),
  );
  const qualified = {
    ...d,
    qualification: {
      need: "Ampliar capacidade",
      authority: "Diretoria",
      timing: "Novembro",
    },
  };
  assert.match(
    actionGuide(qualified, "proposal").objective,
    /Ampliar capacidade/,
  );
  assert.equal(afterAction("profile", d).action, "contact");
  assert.equal(afterAction("qualify", qualified).action, "proposal");
  assert.equal(afterAction("won", qualified).action, null);
});
test("histórico do cliente tem corte explícito e não introduz realizado na própria oportunidade", async () => {
  const d = JSON.parse(await fs.readFile("data/prepared.json", "utf8"));
  for (const deal of d.opportunities) {
    assert.equal(deal.close_value, undefined);
    if (deal.account_history?.lastWonDate)
      assert.ok(deal.account_history.lastWonDate <= d.asOf);
    if (!deal.account) assert.equal(deal.account_history, null);
  }
});

test("quatro lotes de cinco liberam a próxima sequência sem repetir oportunidades", () => {
  const plan = createDailyPlan([...deals, ...deals], start);
  assert.equal(new Set(plan.tasks.map((t) => t.opportunityId)).size, 20);
  assert.deepEqual(
    dailyProgress(plan, []).batches.map((b) => b.unlocked),
    [true, false, false, false],
  );
  const events = plan.tasks.slice(0, 5).map((t) => ({
    opportunityId: t.opportunityId,
    type: "contact",
    at: "2026-11-06T15:01:00Z",
  }));
  const progress = dailyProgress(plan, events);
  assert.equal(progress.activeBatch, 1);
  assert.equal(progress.completedBatches, 1);
  assert.deepEqual(
    progress.batches.map((b) => b.unlocked),
    [true, true, false, false],
  );
  const all = plan.tasks.map((t) => ({
    opportunityId: t.opportunityId,
    type: "contact",
    at: "2026-11-06T15:02:00Z",
  }));
  assert.equal(dailyProgress(plan, all).completedBatches, 4);
  assert.equal(dailyProgress(plan, all).percent, 100);
  assert.deepEqual(
    dailyProgress(createDailyPlan(deals.slice(0, 7), start), []).batches.map(
      (b) => b.total,
    ),
    [5, 2],
  );
});
test("migração preserva conclusões e não credita eventos anteriores nas novas tarefas", () => {
  const legacy = {
    createdAt: start,
    day: "2026-11-06",
    tasks: deals.slice(0, 5).map((d) => ({
      opportunityId: d.opportunity_id,
      goal: "profile",
      label: "Identificar contato",
    })),
  };
  const events = ["D0", "D6"].map((opportunityId) => ({
    opportunityId,
    type: "profile",
    at: "2026-11-06T15:01:00Z",
  }));
  const plan = ensureDailyPlan(legacy, deals, "2026-11-06T16:00:00Z", events);
  assert.equal(plan.tasks.length, 20);
  assert.deepEqual(
    plan.tasks.slice(0, 5).map((t) => t.opportunityId),
    legacy.tasks.map((t) => t.opportunityId),
  );
  assert.equal(dailyProgress(plan, events).completed, 1);
  assert.equal(plan.tasks[0].goal, "profile");
  assert.equal(plan.tasks[1].goal, "contact");
  assert.equal(ensureDailyPlan(plan, deals, start, events), plan);
});
