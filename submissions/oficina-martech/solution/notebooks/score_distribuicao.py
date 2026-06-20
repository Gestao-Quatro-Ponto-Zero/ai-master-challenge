"""Gera process-log/execucoes/score-distribuicao.txt a partir do código atual.

Reproduz os checks de regressão (R1/R2/R3/R5/V9) + distribuição de tiers + a
fração real de stale. Rodar:  python -m notebooks.score_distribuicao
(ou, junto com as demais evidências, `make evidence`).

Mantido versionado para a evidência poder ser regenerada de forma idêntica
sempre que o scoring mudar (em vez de script inline perdido).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring.model import score_open_deals, brief_do_dia
from scoring.config import STALE_DAYS
from scoring.data import load_pipeline_health


def gerar() -> str:
    df = score_open_deals()
    health = load_pipeline_health()
    n = len(df)
    vivos = df[~df["is_stale"]]
    n_stale = int(df["is_stale"].sum())

    # R2 — Engaging com urgência saturada (=100)
    eng = df[(df["deal_stage"] == "Engaging") & df["urgency_sub"].notna()]
    r2 = (eng["urgency_sub"] >= 100).mean() if len(eng) else 0.0

    # R3 — top-10 Foco Agora sem stale + max days_open
    foco = df[df["tier"] == "Foco Agora"].head(10)
    r3_sem_stale = not bool(foco["is_stale"].any())
    r3_max = foco["days_open"].max()

    # R1 — value_sub independe de P (mesmo sales_price -> mesmo value_sub)
    sub = df[["sales_price", "value_sub"]].dropna().drop_duplicates()
    r1 = sub.groupby("sales_price")["value_sub"].nunique().max() == 1

    # V9 — soma do breakdown == score (todos)
    v9 = all(abs(round(sum(b["pontos"] for b in r["breakdown"])) - r["score"]) <= 1
             for _, r in df.iterrows())

    # R5 — brief de um agente COM contas: não pode repetir "não atribuída"
    agente = df[df["account"].notna()]["sales_agent"].value_counts().index[0]
    brief = brief_do_dia(df, agente)
    r5_sem_sem_conta = "não atribuída" not in brief

    pct_sem_conta = health["deals_sem_conta"] / health["open_deals"]

    dist = vivos["tier"].value_counts().reindex(
        ["Foco Agora", "Trabalhar", "Baixa Prioridade"]).fillna(0).astype(int)

    linhas = [
        f"Deals scorados: {n}",
        "",
        "Distribuicao (tier efetivo, vivos = não-stale):",
        f"Foco Agora          {dist['Foco Agora']}",
        f"Trabalhar           {dist['Trabalhar']}",
        f"Baixa Prioridade    {dist['Baixa Prioridade']}",
        f"Revisar/Descartar (is_stale > {STALE_DAYS}d = Won mais velho): "
        f"{n_stale} ({n_stale/n:.0%}) -> reportado como insight de pipeline inflado",
        "",
        f"[R1] value_sub independe de P: {r1}",
        f"[R2] Engaging com urgencia saturada (=100): {r2:.0%} (aceite <40%)",
        f"[R3] Top-10 Foco Agora sem stale: {r3_sem_stale} | "
        f"max days_open no top-10: {r3_max:.0f} (< {STALE_DAYS} por construção)",
        f"[V9] breakdown soma == score (TODOS os {n}): {v9}",
        f"[R5] Brief sem 'conta não atribuída' (deals sem conta excluídos): {r5_sem_sem_conta}",
        f"     Brief ({agente}): {brief}",
        "",
        f"[Saúde] sem conta / abertos = {health['deals_sem_conta']}/{health['open_deals']} "
        f"= {pct_sem_conta:.0%} (numerador e denominador ambos sobre ABERTOS)",
    ]
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    out = gerar()
    dest = (Path(__file__).resolve().parent.parent.parent
            / "process-log" / "execucoes" / "score-distribuicao.txt")
    dest.write_text(out, encoding="utf-8")
    print(out)
    print(f"-> gravado em {dest}")
