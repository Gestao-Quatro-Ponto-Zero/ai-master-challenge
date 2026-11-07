import test from "node:test";
import assert from "node:assert/strict";
import {
  createLocalWorkspaceRepository,
  WORKSPACE_KEY,
  PREFERENCES_KEY,
} from "../lib/workspace-storage.mjs";

function storage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
}
const snapshot = {
  version: 2,
  agent: "Ana",
  events: [
    {
      id: "E1",
      opportunityId: "D1",
      type: "contact",
      agent: "Ana",
      at: "2026-11-06T15:00:00Z",
      notes: "QA",
      nextAction: "Retornar",
      dueAt: "2026-11-07T15:00:00Z",
    },
  ],
  plans: {
    "2026-11-06|Ana": {
      day: "2026-11-06",
      createdAt: "2026-11-06T14:00:00Z",
      tasks: [{ opportunityId: "D1", goal: "contact", label: "Conversar" }],
    },
  },
};

test("repositório lê a chave existente e preserva eventos, planos legados e campos adicionais", () => {
  const previous = { ...snapshot, extra: "compatibility" };
  const saved = storage({ "g4-sales-workspace-v2": JSON.stringify(previous) });
  const repository = createLocalWorkspaceRepository(saved);
  assert.deepEqual(repository.load(), previous);
  repository.save(repository.load());
  assert.deepEqual(
    JSON.parse(saved.getItem("g4-sales-workspace-v2")),
    previous,
  );
});
test("armazenamento vazio não cria plano nem grava automaticamente", () => {
  const saved = storage();
  assert.equal(createLocalWorkspaceRepository(saved).load(), null);
  assert.equal(saved.getItem(WORKSPACE_KEY), null);
});
test("JSON corrompido ou eventos inválidos não são sobrescritos na leitura", () => {
  for (const value of [
    "{broken",
    JSON.stringify({ version: 2, events: "invalid" }),
  ]) {
    const saved = storage({ [WORKSPACE_KEY]: value });
    assert.throws(() => createLocalWorkspaceRepository(saved).load());
    assert.equal(saved.getItem(WORKSPACE_KEY), value);
  }
});
test("falha de gravação é propagada sem alterar a última versão recuperável", () => {
  const value = JSON.stringify(snapshot);
  const repository = createLocalWorkspaceRepository({
    getItem: () => value,
    setItem: () => {
      throw Error("QuotaExceeded");
    },
  });
  assert.throws(
    () => repository.save({ ...snapshot, events: [] }),
    /QuotaExceeded/,
  );
  assert.deepEqual(repository.load(), snapshot);
});
test("preferências visuais não alteram eventos nem planos", () => {
  const saved = storage({ [WORKSPACE_KEY]: JSON.stringify(snapshot) });
  const repository = createLocalWorkspaceRepository(saved);
  repository.savePreferences({ dark: true, collapsed: true });
  assert.deepEqual(repository.loadPreferences(), {
    dark: true,
    collapsed: true,
  });
  assert.deepEqual(repository.load(), snapshot);
  assert.ok(saved.getItem(PREFERENCES_KEY));
});
test("leitura mantém a filtragem existente de eventos reconhecidos sem perder os válidos", () => {
  const saved = storage({
    [WORKSPACE_KEY]: JSON.stringify({
      ...snapshot,
      events: [
        ...snapshot.events,
        null,
        { opportunityId: "D2", at: "now", type: "unknown" },
      ],
    }),
  });
  assert.deepEqual(
    createLocalWorkspaceRepository(saved).load().events,
    snapshot.events,
  );
});
