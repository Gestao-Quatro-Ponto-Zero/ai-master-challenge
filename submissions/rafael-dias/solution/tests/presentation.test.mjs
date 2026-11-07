import test from "node:test";
import assert from "node:assert/strict";
import { scoreBand, spinQuestions, moveIntent } from "../lib/presentation.mjs";
test("faixas do score têm limites consistentes e não representam probabilidade", () => {
  assert.equal(scoreBand(95).tone, "green");
  assert.equal(scoreBand(80).tone, "green");
  assert.equal(scoreBand(79).tone, "amber");
  assert.equal(scoreBand(60).tone, "amber");
  assert.equal(scoreBand(59).tone, "red");
});
test("SPIN usa contexto conhecido e condiciona implicações à resposta do cliente", () => {
  const d = {
    account: "Conta real",
    product: "GTX Pro",
    account_history: { won: 12 },
  };
  const q = spinQuestions(d);
  assert.equal(q.length, 4);
  assert.match(q[0].context, /12 negócios ganhos/);
  assert.match(q[0].context, /até 2017/);
  assert.doesNotMatch(q[0].question, /2017|A base registra/);
  assert.match(q[2].investigate, /cliente confirmou/);
  assert.match(q[1].investigate, /não presuma/);
  assert.match(
    spinQuestions({ ...d, qualification: { need: "Demora na operação" } })[1]
      .question,
    /Demora na operação/,
  );
});
test("arraste prepara o registro, sem conceder SQL ou venda automaticamente", () => {
  assert.equal(moveIntent({ status: "new" }, "qualified").action, "qualify");
  assert.equal(
    moveIntent({ status: "qualified" }, "proposal").action,
    "proposal",
  );
  assert.equal(moveIntent({ status: "proposal" }, "won").action, "won");
  assert.ok(moveIntent({ status: "new" }, "new").noop);
  assert.ok(moveIntent({ status: "won" }, "new").error);
  assert.ok(moveIntent({ status: "proposal" }, "contacted").error);
  assert.ok(moveIntent({ status: "new" }, "invalid").error);
});
