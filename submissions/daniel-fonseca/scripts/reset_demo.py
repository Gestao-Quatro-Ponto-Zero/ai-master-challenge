"""Restaura os dados de demonstração do app (PRD v1.1 §8, plano do app — Etapa 1).

1. Apaga triagens, fila, caixa, eventos de uso e heartbeats (dados de teste e de visitantes).
2. Mantém o playbook validado e as soluções aprendidas no HITL (ex.: #15), desligando o vínculo com a fila apagada.
3. Repovoa pelo webhook de produção do n8n (com o X-Webhook-Secret), usando tickets reais do holdout do DS2:
   - REVIEW tickets que caem em "Revisão humana" (a fila fica com itens para decidir),
   - HUMAN tickets de categoria sensível (Somente humano, com a nota interna e o texto do Slack),
   - AUTO tickets com autonomia da IA (o Painel › Operação começa com dados).
   A escolha é determinística (menor id que atende ao critério), e o custo fica em torno de US$ 0,01.

Pré-requisitos: SUPABASE_DB_URL, N8N_BASE_URL e N8N_WEBHOOK_SECRET no .env; fluxo 1 publicado.
Uso: .venv/bin/python scripts/reset_demo.py [--sem-repovoar]
"""
import json
import os
import sys
import urllib.error
import urllib.request

import psycopg

import load_raw_datasets as raw

REVIEW, HUMAN, AUTO = 6, 2, 2
BLOCKED = ("salary", "payroll", "bonus", "termination", "dismissal", "resignation", "lawsuit", "legal",
           "harassment", "sick leave", "maternity")

PICK = """
with cand as (
  select t.id, t.document, t.topic_group, c.category, c.confidence, c.sensitive_share
  from (select id, document, topic_group from public.ds2_tickets
        where split = 'test' and array_length(regexp_split_to_array(document, '\\s+'), 1) between 10 and 60
        order by id limit 400) t
  join public.ds2_embeddings e on e.id = t.id
  cross join lateral public.classify_ticket(e.embedding) c
  where c.category = t.topic_group
)
select id, document, category, confidence from cand where {cond} order by id limit %s
"""
SENS = "('HR Support', 'Administrative rights')"
CONDS = {
    "review": f"category not in {SENS} and sensitive_share < 0.3 and confidence >= 0.5 and confidence < 0.9",
    "human": f"category in {SENS}",
    "auto": f"category not in {SENS} and sensitive_share < 0.3 and confidence >= 0.9",
}


def triage(text: str, ds2_id: int) -> dict:
    url = os.environ["N8N_BASE_URL"].rstrip("/") + "/webhook/g4-support/triage"
    req = urllib.request.Request(url, method="POST", data=json.dumps({"ticket_text": text, "source": "holdout", "ds2_id": ds2_id}).encode(),
                                 headers={"Content-Type": "application/json", "X-Webhook-Secret": os.environ["N8N_WEBHOOK_SECRET"]})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code}


if __name__ == "__main__":
    raw.load_env()
    with psycopg.connect(os.environ["SUPABASE_DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute("update public.validated_resolutions set hitl_id = null where hitl_id is not null")
        cur.execute("update public.triage_runs set resolution_id = null")
        for table in ("usage_events", "notifications", "hitl_queue", "triage_runs", "heartbeat"):
            cur.execute(f"delete from public.{table}")
            print(f"{table}: {cur.rowcount} linhas apagadas")
        conn.commit()
        if "--sem-repovoar" in sys.argv:
            raise SystemExit(0)
        picks = []
        for kind, n in (("review", REVIEW), ("human", HUMAN), ("auto", AUTO)):
            cur.execute(PICK.format(cond=CONDS[kind]), (n * 3,))
            rows = [r for r in cur.fetchall() if not any(f" {b} " in f" {r[1]} " for b in BLOCKED)][:n]
            picks += [(kind, *r) for r in rows]
    for kind, ds2_id, text, category, conf in picks:
        out = triage(text, ds2_id)
        print(f"{kind:6s} ds2 {ds2_id:5d} {category:22s} {conf:.2f} → {out.get('status', out)}")
    # Tudo o que o script cria é demonstração: aparece para todos os visitantes na tela Tickets (ADR-0015).
    with psycopg.connect(os.environ["SUPABASE_DB_URL"]) as conn:
        n = conn.execute("update public.triage_runs set is_demo = true where not is_demo").rowcount
        conn.commit()
    print(f"triage_runs: {n} marcadas como demonstração")
