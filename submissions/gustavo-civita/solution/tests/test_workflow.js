/* Testes do fluxo de cada negociação. Uso: node tests/test_workflow.js */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function freshWorkflow() {
  const store = new Map();
  const context = vm.createContext({
    localStorage: {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => store.set(key, String(value)),
    },
    Date,
    JSON,
  });
  const source = fs.readFileSync(path.join(__dirname, "..", "app", "workflow.js"), "utf8");
  vm.runInContext(`${source}\nthis.Workflow = Workflow;`, context);
  return context.Workflow;
}

const CALL = { id: "A1", lista: "foco", vendedor: "Ana" };
const MESSAGE = { id: "B2", lista: "reativar", vendedor: "Ana" };
const statusOf = (workflow, deal) => workflow.statusOf(deal, workflow.byDeal()[deal.id]);
const tests = [];
const test = (name, run) => tests.push([name, run]);

test("negociação sem registro fica na fila, com a ação da sua lista", () => {
  const workflow = freshWorkflow();
  assert.equal(statusOf(workflow, CALL).fase, "fila");
  assert.equal(statusOf(workflow, CALL).modo, "ligar");
  assert.equal(statusOf(workflow, MESSAGE).modo, "mensagem");
  assert.equal(statusOf(workflow, { id: "C3", lista: "encerrar" }).modo, "encerrar");
});

test("ligou e não atendeu: sai da fila e volta em 2 dias como 2ª tentativa", () => {
  const workflow = freshWorkflow();
  workflow.add(CALL, "nao_atendeu");
  assert.equal(statusOf(workflow, CALL).fase, "agendada");
  workflow.advanceDay();
  assert.equal(statusOf(workflow, CALL).fase, "agendada");
  workflow.advanceDay();
  const status = statusOf(workflow, CALL);
  assert.equal(status.fase, "retorno");
  assert.match(status.tarefa, /2ª tentativa/);
});

test("três ligações sem resposta: troca para mensagem de confirmação, não encerra", () => {
  const workflow = freshWorkflow();
  for (let i = 0; i < 3; i += 1) {
    workflow.add(CALL, "nao_atendeu");
    workflow.advanceDay();
    workflow.advanceDay();
  }
  const status = statusOf(workflow, CALL);
  assert.equal(status.fase, "retorno");
  assert.equal(status.modo, "mensagem");
  assert.equal(status.confirmar, true);
  assert.match(status.tarefa, /confirmar o interesse/);
});

test("mensagem de confirmação sem resposta: aí sim vai para encerrar", () => {
  const workflow = freshWorkflow();
  for (let i = 0; i < 3; i += 1) workflow.add(CALL, "nao_atendeu");
  workflow.add(CALL, "enviou");
  assert.equal(statusOf(workflow, CALL).fase, "aguardando");
  for (let i = 0; i < 3; i += 1) workflow.advanceDay();
  const status = statusOf(workflow, CALL);
  assert.equal(status.fase, "esgotada");
  assert.equal(status.modo, "encerrar");
});

test("mensagem de confirmação respondida: volta para ligar, do zero", () => {
  const workflow = freshWorkflow();
  for (let i = 0; i < 3; i += 1) workflow.add(CALL, "nao_atendeu");
  workflow.add(CALL, "enviou");
  workflow.add(CALL, "respondeu");
  const status = statusOf(workflow, CALL);
  assert.equal(status.fase, "retorno");
  assert.equal(status.modo, "ligar");
  assert.equal(status.ligacoes, 0);
});

test("três mensagens sem resposta numa negociação de mensagem: encerrar", () => {
  const workflow = freshWorkflow();
  for (let i = 0; i < 3; i += 1) {
    workflow.add(MESSAGE, "enviou");
    for (let d = 0; d < 3; d += 1) workflow.advanceDay();
  }
  assert.equal(statusOf(workflow, MESSAGE).fase, "esgotada");
});

test("mensagem enviada: aguarda 3 dias e volta para a fila", () => {
  const workflow = freshWorkflow();
  workflow.add(MESSAGE, "enviou");
  assert.equal(statusOf(workflow, MESSAGE).fase, "aguardando");
  workflow.advanceDay();
  workflow.advanceDay();
  assert.equal(statusOf(workflow, MESSAGE).fase, "aguardando");
  workflow.advanceDay();
  const status = statusOf(workflow, MESSAGE);
  assert.equal(status.fase, "retorno");
  assert.equal(status.modo, "mensagem");
});

test("cliente respondeu: volta na hora, para ligar, e zera as tentativas", () => {
  const workflow = freshWorkflow();
  workflow.add(MESSAGE, "enviou");
  workflow.add(MESSAGE, "respondeu");
  const status = statusOf(workflow, MESSAGE);
  assert.equal(status.fase, "retorno");
  assert.equal(status.modo, "ligar");
  assert.equal(status.tentativas, 0);
});

test("retorno combinado: volta na data marcada, com a anotação guardada", () => {
  const workflow = freshWorkflow();
  const when = workflow.addDays(workflow.now(), 3).toISOString();
  workflow.add(CALL, "retornar", { retornoEm: when, nota: "pediu proposta revisada" });
  assert.equal(statusOf(workflow, CALL).fase, "agendada");
  workflow.advanceDay();
  workflow.advanceDay();
  workflow.advanceDay();
  const status = statusOf(workflow, CALL);
  assert.equal(status.fase, "retorno");
  assert.equal(status.historico[0].nota, "pediu proposta revisada");
});

test("fechou, perdeu ou encerrou: sai da lista", () => {
  for (const [tipo, resultado] of [["ganhou", "Fechou"], ["perdeu", "Sem interesse"], ["encerrou", "Encerrou no CRM"]]) {
    const workflow = freshWorkflow();
    workflow.add(CALL, tipo);
    const status = statusOf(workflow, CALL);
    assert.equal(status.fase, "concluida");
    assert.equal(status.resultado, resultado);
  }
});

test("desfazer apaga só o último registro daquela negociação", () => {
  const workflow = freshWorkflow();
  workflow.add(CALL, "nao_atendeu");
  workflow.add(MESSAGE, "enviou");
  workflow.add(CALL, "ganhou");
  workflow.undoLast(CALL.id);
  assert.equal(statusOf(workflow, CALL).fase, "agendada");
  assert.equal(statusOf(workflow, MESSAGE).fase, "aguardando");
  assert.equal(workflow.events().length, 2);
});

test("armazenamento corrompido não quebra a tela", () => {
  for (const lixo of ["isto não é uma lista", {}, [null], [{ id: "A1", tipo: "inventado" }]]) {
    const workflow = freshWorkflow();
    workflow.write("leadscorer.eventos.v3", lixo);
    assert.doesNotThrow(() => workflow.byDeal());
    assert.equal(statusOf(workflow, CALL).fase, "fila");
  }
});

test("evento depois de concluída não reabre a negociação", () => {
  const workflow = freshWorkflow();
  workflow.add(CALL, "ganhou");
  workflow.add(CALL, "nao_atendeu");
  assert.equal(statusOf(workflow, CALL).fase, "concluida");
  assert.equal(statusOf(workflow, CALL).resultado, "Fechou");
});

test("tipo de evento estranho no armazenamento é ignorado, mesmo com nome de método", () => {
  for (const tipo of ["toString", "constructor", "inventado"]) {
    const workflow = freshWorkflow();
    workflow.write("leadscorer.eventos.v3", [{ id: "A1", tipo, quando: new Date().toISOString() }]);
    assert.equal(statusOf(workflow, CALL).fase, "fila", tipo);
    // direto no cálculo, sem passar pelo filtro do armazenamento
    assert.equal(workflow.statusOf(CALL, [{ id: "A1", tipo, quando: new Date().toISOString() }]).fase, "fila", tipo);
  }
});

test("registro sem data válida é descartado, e retorno sem data volta no próprio dia", () => {
  const workflow = freshWorkflow();
  workflow.write("leadscorer.eventos.v3", [{ id: "A1", tipo: "nao_atendeu" }, { id: "A1", tipo: "enviou", quando: "ontem" }]);
  assert.equal(statusOf(workflow, CALL).fase, "fila");
  workflow.write("leadscorer.eventos.v3", [{ id: "A1", tipo: "retornar", quando: new Date().toISOString() }]);
  assert.equal(statusOf(workflow, CALL).fase, "retorno"); // não fica agendada para sempre
});

test("os prazos contam dias de calendário, não blocos de 24 horas", () => {
  const workflow = freshWorkflow();
  const late = new Date(2026, 10, 18, 23, 59);
  const due = workflow.addDays(late, 2);
  assert.deepEqual([due.getFullYear(), due.getMonth(), due.getDate(), due.getHours()], [2026, 10, 20, 0]);
  const acrossMonth = workflow.addDays(new Date(2026, 0, 30, 12), 3);
  assert.deepEqual([acrossMonth.getMonth(), acrossMonth.getDate()], [1, 2]);
});

let failed = 0;
for (const [name, run] of tests) {
  try {
    run();
    console.log(`ok   ${name}`);
  } catch (error) {
    failed += 1;
    console.log(`ERRO ${name}\n     ${error.message}`);
  }
}
console.log(`\n${tests.length - failed} de ${tests.length} testes passaram`);
process.exit(failed ? 1 : 0);
