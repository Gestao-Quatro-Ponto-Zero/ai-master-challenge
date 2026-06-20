-- 0003_actions — Camada de ação do vendedor (audit log persistente)
-- O app deixa de ser só visualização: o vendedor marca "contatado" / "descarta"
-- e a decisão fica registrada com ator e timestamp. O seed NÃO limpa esta tabela
-- (ações sobrevivem ao re-seed dos dados do CRM).

CREATE TABLE IF NOT EXISTS deal_actions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    action         TEXT NOT NULL CHECK (action IN ('contacted','discarded','reactivated')),
    actor          TEXT NOT NULL,            -- vendedor que agiu
    note           TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_actions_opp ON deal_actions(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_actions_created ON deal_actions(created_at);
