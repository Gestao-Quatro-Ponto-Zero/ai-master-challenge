# -*- coding: utf-8 -*-
"""FASE 2 — Preparação dos dados e feature engineering.

Módulo reutilizável pelas fases 3 (diagnóstico), 5 (ML) e 6 (protótipo Streamlit).
Fonte única de verdade para features E premissas de negócio (nada de cópias
divergentes entre notebook, dashboard e simulador).

Regras herdadas da auditoria (docs/data_audit.md) e do decision log:
- D-005: `First Response Time` e `Time to Resolution` são timestamps SINTÉTICOS
  (horários aleatórios em ~3 dias). Toda feature derivada deles carrega o
  prefixo ``synthetic_`` no nome e NÃO fundamenta decisão de negócio.
- D-006: nulos são estruturais (função do Ticket Status) — nunca imputados;
  derivadas que só existem para um subconjunto usam dtypes anuláveis (NA).
- D-008/D-009: decisões da FASE 2 (painel de design) — ver process-log/decisions.md.

Convenção de status de feature (dicionário machine-readable ``FEATURE_STATUS``):
- ``measured``       — derivada direta de dado observado; pode alimentar análise.
- ``synthetic_demo`` — derivada dos timestamps sintéticos; APENAS demonstração,
                       proibida em agregados, gráficos de conclusão e modelos.
- ``assumption``     — calculada a partir de premissas declaradas (não medida);
                       serve para converter volume em horas/custo; PROIBIDA como
                       preditor ou em teste estatístico (seria tautologia).
- ``target_derived`` — derivada do Customer Satisfaction Rating; usá-la para
                       prever satisfação seria leakage trivial.
- ``demo_only``      — conteúdo para demonstração de UI (FASE 6); proibida em
                       treino/avaliação de modelo e em análises.

Uso:
    from src.data_prep import build_dataset1, build_dataset2
    d1 = build_dataset1()
    d2 = build_dataset2()
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data"
DATA_PROCESSED = ROOT / "data" / "processed"

# ===========================================================================
# PREMISSAS DECLARADAS (fonte única — consumidas pela FASE 3 e pelo ROI
# Simulator da FASE 6, onde viram sliders)
# ===========================================================================
# Honestidade sobre a origem: os valores abaixo são PREMISSAS DO AUTOR na
# ordem de grandeza de benchmarks públicos de suporte/CX; não há fonte única
# auditável por valor. Por isso cada premissa central tem faixa (low/base/high)
# e a análise de sensibilidade da FASE 3/6 varia essas faixas. Nenhum valor
# vem de medição nos dados (os tempos do dataset são sintéticos — D-005).

#: Esforço de agente por ticket, em MINUTOS DE AGENTE no ciclo de vida
#: completo (todas as interações + after-work), não tempo de relógio.
#: Racional da ordenação (Email > Phone ≈ Social > Chat):
#: - Email 18: assíncrono multi-toque (2-3 interações de ~6-8 min cada);
#: - Phone 15: síncrono 1:1 (chamada ~8-10 min + registro/ACW ~3-5 min);
#: - Social media 15: resposta pública + follow-up em DM, risco reputacional;
#: - Chat 10: ~15-18 min de relógio ÷ concorrência de 1,5-2 sessões por
#:   agente => esforço efetivo menor por ticket.
AHT_MIN_BY_CHANNEL: dict[str, dict[str, float]] = {
    "Email": {"low": 12.0, "base": 18.0, "high": 25.0},
    "Phone": {"low": 10.0, "base": 15.0, "high": 22.0},
    "Social media": {"low": 10.0, "base": 15.0, "high": 22.0},
    "Chat": {"low": 6.0, "base": 10.0, "high": 16.0},
}

#: Multiplicador de esforço por tipo (1.0 = neutro). Premissa do autor;
#: sensibilidade coberta pela variação do AHT base (não têm faixa própria).
EFFORT_MULT_BY_TYPE: dict[str, float] = {
    "Technical issue": 1.5,      # diagnóstico + troubleshooting
    "Refund request": 1.2,       # verificação + política + processamento
    "Cancellation request": 1.1, # retenção + processamento
    "Billing inquiry": 1.0,      # consulta + explicação
    "Product inquiry": 0.8,      # informacional, alta padronização
}

#: Multiplicador de esforço por prioridade (1.0 = neutro). Premissa do autor.
EFFORT_MULT_BY_PRIORITY: dict[str, float] = {
    "Low": 0.9,
    "Medium": 1.0,
    "High": 1.2,
    "Critical": 1.4,             # escalação, comunicação extra, urgência
}

#: Custo carregado do agente de suporte (R$/hora): salário BR ~R$ 2,5-3,5k
#: + encargos (~1,7x) sobre ~140h produtivas/mês => ~R$ 30-55/h.
AGENT_COST_BRL_PER_HOUR: dict[str, float] = {"low": 30.0, "base": 40.0, "high": 55.0}

#: Fator de anualização (D-001): o dataset é amostra de 8.469 tickets de uma
#: operação declarada de ~30.000 tickets/ano.
TICKETS_PER_YEAR = 30_000
ANNUALIZATION_FACTOR: float = TICKETS_PER_YEAR / 8_469  # ≈ 3,542

#: Matriz de SLA de resolução por prioridade, em horas. ILUSTRATIVA (premissa
#: do autor, ajustável) — usada apenas pela função `sla_violation` em demos;
#: nenhuma coluna de SLA é materializada sobre os tempos sintéticos (D-009).
SLA_TARGET_HOURS_BY_PRIORITY: dict[str, float] = {
    "Low": 48.0,
    "Medium": 24.0,
    "High": 8.0,
    "Critical": 4.0,
}

#: Premissa estrutural do modelo de esforço: efeitos de canal, tipo e
#: prioridade são INDEPENDENTES (multiplicativos, sem interações). É uma
#: escolha de modelagem, não um fato medido.
EFFORT_MODEL = "aht_base(channel) * mult(type) * mult(priority)"

PRIORITY_ORDER = ["Low", "Medium", "High", "Critical"]
PRIORITY_RANK: dict[str, int] = {p: i + 1 for i, p in enumerate(PRIORITY_ORDER)}

#: Bins de idade com larguras ~iguais (13/13/13/14 anos), fechados à direita:
#: [18,30], (30,43], (43,56], (56,70]. Idade no dataset é uniforme 18-70;
#: bins iguais evitam contagens desiguais por artefato de binagem.
AGE_BINS = [17, 30, 43, 56, 70]
AGE_LABELS = ["18-30", "31-43", "44-56", "57-70"]

#: Filtro de qualidade do Dataset 2. Tokenização: str.split() (whitespace).
MIN_WORDS_D2 = 3

# ===========================================================================
# Dicionário machine-readable de status por feature (a FASE 3 filtra por ele)
# ===========================================================================
FEATURE_STATUS: dict[str, str] = {
    # Grupo A — flags de status/prioridade
    "is_closed": "measured",
    "is_open": "measured",
    "is_pending": "measured",
    "is_unresolved": "measured",
    "is_critical": "measured",
    "is_high_urgency": "measured",
    "priority_rank": "measured",
    # Grupo A' — derivadas do rating (leakage se usadas para prever satisfação)
    "is_rated": "target_derived",
    "is_dissatisfied": "target_derived",
    "is_satisfied": "target_derived",
    # Grupo B — tempo sintético (D-005): demonstração apenas
    "synthetic_first_response_ts": "synthetic_demo",
    "synthetic_resolution_ts": "synthetic_demo",
    "synthetic_delta_resolution_minutes": "synthetic_demo",
    # Grupo C — premissas materializadas
    "est_handle_minutes": "assumption",
    "est_cost_brl": "assumption",
    # Grupo D — texto e cliente
    "description_chars": "measured",
    "description_words": "measured",
    "description_demo": "demo_only",  # texto template com placeholder resolvido — só p/ UI (FASE 6)
    "resolution_chars": "measured",
    "resolution_words": "measured",
    "age_group": "measured",
    "tickets_per_customer": "measured",
    "is_repeat_customer": "measured",
}


def features_by_status(status: str) -> list[str]:
    """Ex.: features_by_status('measured') -> colunas seguras para análise."""
    return [f for f, s in FEATURE_STATUS.items() if s == status]


# ===========================================================================
# Mecanismo real de SLA (função pura — pronta para dados reais)
# ===========================================================================

def sla_violation(
    duration_minutes: pd.Series,
    priority: pd.Series,
    targets_hours: dict[str, float] | None = None,
) -> pd.Series:
    """Regra REAL de violação de SLA: duração observada > alvo da prioridade.

    - ``duration_minutes``: duração NÃO-NEGATIVA (abertura→resolução) em
      minutos. Em dados reais é >= 0 por construção; valores negativos indicam
      input inválido e produzem ``pd.NA`` (nunca False silencioso).
    - Retorna boolean anulável: ``pd.NA`` onde a duração é nula ou inválida.

    IMPORTANTE (D-009): este mecanismo NÃO é aplicado como coluna do dataset —
    os tempos do Dataset 1 são sintéticos (D-005) e qualquer taxa de violação
    calculada sobre eles é ruído. O notebook da FASE 2 demonstra a função com
    durações fabricadas válidas e prova analiticamente que, sobre o delta
    sintético, o resultado seguiria a geometria triangular do gerador.
    """
    targets = targets_hours or SLA_TARGET_HOURS_BY_PRIORITY
    # .astype(float): .map sobre Series categórica devolve categorical
    target_min = priority.map(targets).astype(float) * 60.0
    valid = duration_minutes.notna() & (duration_minutes >= 0) & target_min.notna()
    out = pd.Series(pd.NA, index=duration_minutes.index, dtype="boolean")
    out[valid] = duration_minutes[valid] > target_min[valid]
    return out


# ===========================================================================
# Dataset 1 — customer_support_tickets
# ===========================================================================

def load_dataset1_raw() -> pd.DataFrame:
    """Carrega o CSV bruto do Dataset 1 (8.469 × 17)."""
    return pd.read_csv(DATA_RAW / "customer_support_tickets.csv")


def build_dataset1(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Aplica todo o feature engineering do Dataset 1.

    Dicionário completo (definição, fórmula, justificativa, status, caveats):
    docs/feature_engineering.md.
    """
    d = (df if df is not None else load_dataset1_raw()).copy()

    # --- dtypes categóricos (labels consistentes para groupbys da FASE 3+) --
    d["Ticket Priority"] = pd.Categorical(
        d["Ticket Priority"], categories=PRIORITY_ORDER, ordered=True
    )
    for c in ["Ticket Type", "Ticket Status", "Ticket Channel", "Customer Gender"]:
        d[c] = d[c].astype("category")

    # --- Grupo A: flags de status e prioridade ------------------------------
    d["is_closed"] = d["Ticket Status"].eq("Closed")
    d["is_open"] = d["Ticket Status"].eq("Open")
    d["is_pending"] = d["Ticket Status"].eq("Pending Customer Response")
    d["is_unresolved"] = ~d["is_closed"]  # backlog: Open + Pending (sinal central pós-D-005)
    d["is_critical"] = d["Ticket Priority"].eq("Critical")
    d["is_high_urgency"] = d["Ticket Priority"].isin(["High", "Critical"])
    d["priority_rank"] = d["Ticket Priority"].map(PRIORITY_RANK).astype("int8")

    # --- Grupo A': derivadas do rating (target_derived — ver FEATURE_STATUS)
    sat = d["Customer Satisfaction Rating"]
    d["is_rated"] = sat.notna()  # nestes dados ≡ is_closed (identidade validada abaixo)
    d["is_dissatisfied"] = (sat <= 2).where(sat.notna()).astype("boolean")
    d["is_satisfied"] = (sat >= 4).where(sat.notna()).astype("boolean")

    # --- Grupo B: tempo sintético (prefixo synthetic_ — D-005/D-009) --------
    d["synthetic_first_response_ts"] = pd.to_datetime(
        d["First Response Time"], errors="raise"
    )
    d["synthetic_resolution_ts"] = pd.to_datetime(
        d["Time to Resolution"], errors="raise"
    )
    delta = d["synthetic_resolution_ts"] - d["synthetic_first_response_ts"]
    d["synthetic_delta_resolution_minutes"] = delta.dt.total_seconds() / 60
    # (NaN estrutural para não-Closed; ~49,3% dos valores são NEGATIVOS —
    #  prova de que não é duração. Nenhuma coluna de SLA é materializada.)

    # --- Grupo C: esforço/custo estimados (assumption — premissas acima) ----
    # .map sobre dtype category devolve categorical — cast para float antes de operar
    base = d["Ticket Channel"].map(
        {k: v["base"] for k, v in AHT_MIN_BY_CHANNEL.items()}
    ).astype(float)
    mult_type = d["Ticket Type"].map(EFFORT_MULT_BY_TYPE).astype(float)
    mult_prio = d["Ticket Priority"].map(EFFORT_MULT_BY_PRIORITY).astype(float)
    d["est_handle_minutes"] = base * mult_type * mult_prio
    d["est_cost_brl"] = (
        d["est_handle_minutes"] / 60.0 * AGENT_COST_BRL_PER_HOUR["base"]
    )

    # --- Grupo D: texto e cliente --------------------------------------------
    desc = d["Ticket Description"]
    d["description_chars"] = desc.str.len().astype("int32")
    d["description_words"] = desc.str.split().str.len().astype("int32")
    d["description_demo"] = [
        t.replace("{product_purchased}", p) for t, p in zip(desc, d["Product Purchased"])
    ]  # SÓ para demonstração de UI (FASE 6); nunca para treino/avaliação de modelo

    res = d["Resolution"]
    d["resolution_chars"] = res.str.len().astype("Int32")   # NA estrutural p/ não-Closed
    d["resolution_words"] = res.str.split().str.len().astype("Int32")

    d["age_group"] = pd.cut(d["Customer Age"], bins=AGE_BINS, labels=AGE_LABELS)

    tpc = d.groupby("Customer Email")["Ticket ID"].transform("count")
    d["tickets_per_customer"] = tpc.astype("int16")  # caveat: e-mails repetidos podem
    d["is_repeat_customer"] = tpc > 1                # ser colisão do gerador sintético

    _validate_dataset1(d)
    return d


def _validate_dataset1(d: pd.DataFrame) -> None:
    """Sanity checks estruturais — falham alto se alguma premissa quebrar."""
    assert d["Ticket ID"].is_unique, "Ticket ID deixou de ser único"
    assert (d[["is_closed", "is_open", "is_pending"]].sum(axis=1) == 1).all(), (
        "flags de status devem ser mutuamente exclusivas"
    )
    assert d["is_unresolved"].eq(d["is_open"] | d["is_pending"]).all()
    # nulos estruturais (D-006): FRT existe exatamente para não-Open; TTR/rating p/ Closed
    assert d["synthetic_first_response_ts"].notna().eq(~d["is_open"]).all()
    assert d["synthetic_resolution_ts"].notna().eq(d["is_closed"]).all()
    assert d["is_rated"].eq(d["is_closed"]).all(), (
        "identidade estrutural is_rated == is_closed quebrou (ver dicionário §2.1)"
    )
    assert d["synthetic_delta_resolution_minutes"].notna().eq(d["is_closed"]).all()
    assert d["resolution_words"].notna().eq(d["is_closed"]).all()
    assert d["est_handle_minutes"].notna().all(), (
        "premissas de AHT não cobrem algum canal/tipo/prioridade"
    )
    assert not d["description_demo"].str.contains(
        r"\{product_purchased\}", regex=True
    ).any(), "placeholder residual em description_demo"
    assert d["age_group"].notna().all(), "idade fora dos bins declarados"
    # todas as features novas têm status declarado no dicionário
    new_cols = [c for c in d.columns if c not in _RAW_COLS_D1]
    missing = [c for c in new_cols if c not in FEATURE_STATUS]
    assert not missing, f"features sem status declarado: {missing}"


_RAW_COLS_D1 = [
    "Ticket ID", "Customer Name", "Customer Email", "Customer Age",
    "Customer Gender", "Product Purchased", "Date of Purchase", "Ticket Type",
    "Ticket Subject", "Ticket Description", "Ticket Status", "Resolution",
    "Ticket Priority", "Ticket Channel", "First Response Time",
    "Time to Resolution", "Customer Satisfaction Rating",
]


# ===========================================================================
# Dataset 2 — it_service_ticket_classification
# ===========================================================================

def load_dataset2_raw() -> pd.DataFrame:
    """Carrega o CSV bruto do Dataset 2 (47.837 × 2)."""
    return pd.read_csv(DATA_RAW / "it_service_ticket_classification.csv")


def build_dataset2(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Limpeza mínima + métricas de texto do Dataset 2.

    - ``doc_id`` é atribuído ANTES do filtro = índice da linha no CSV bruto
      (rastreabilidade permanente dos removidos).
    - Split estratificado/encoding pertencem à FASE 5; o mapeamento congelado
      de classes fica em ``TOPIC_CLASSES``.
    """
    d = (df if df is not None else load_dataset2_raw()).copy()

    d.insert(0, "doc_id", np.arange(len(d), dtype="int32"))
    d["Topic_group"] = pd.Categorical(d["Topic_group"], categories=TOPIC_CLASSES)
    d["word_count"] = d["Document"].str.split().str.len().astype("int32")
    d["char_count"] = d["Document"].str.len().astype("int32")

    removed = d[d["word_count"] < MIN_WORDS_D2]
    d = d[d["word_count"] >= MIN_WORDS_D2].reset_index(drop=True)
    d.attrs["rows_removed_short_docs"] = len(removed)
    d.attrs["removed_doc_ids"] = removed["doc_id"].tolist()
    d.attrs["removed_by_class"] = (
        removed["Topic_group"].value_counts().loc[lambda s: s > 0].to_dict()
    )

    _validate_dataset2(d)
    return d


#: Mapeamento congelado classe -> código (ordem alfabética, estável para a
#: FASE 5 — nunca redefinir downstream).
TOPIC_CLASSES = [
    "Access", "Administrative rights", "HR Support", "Hardware",
    "Internal Project", "Miscellaneous", "Purchase", "Storage",
]
TOPIC_CODE = {c: i for i, c in enumerate(TOPIC_CLASSES)}


def _validate_dataset2(d: pd.DataFrame) -> None:
    assert d["Document"].notna().all() and d["Topic_group"].notna().all()
    assert d["doc_id"].is_unique
    assert (d["word_count"] >= MIN_WORDS_D2).all()
    assert d["Topic_group"].nunique() == 8, "esperadas exatamente 8 classes"
    assert list(d["Topic_group"].cat.categories) == TOPIC_CLASSES


# ===========================================================================
# Persistência
# ===========================================================================

def save_processed(d1: pd.DataFrame, d2: pd.DataFrame) -> dict[str, Path]:
    """Grava os datasets processados em data/processed/ (parquet)."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    p1 = DATA_PROCESSED / "tickets_features.parquet"
    p2 = DATA_PROCESSED / "it_tickets_clean.parquet"
    d1.to_parquet(p1, index=False)
    d2.to_parquet(p2, index=False)
    return {"dataset1": p1, "dataset2": p2}


if __name__ == "__main__":
    d1 = build_dataset1()
    d2 = build_dataset2()
    paths = save_processed(d1, d2)
    print(f"Dataset 1: {d1.shape[0]:,} x {d1.shape[1]} -> {paths['dataset1']}")
    print(f"Dataset 2: {d2.shape[0]:,} x {d2.shape[1]} -> {paths['dataset2']}"
          f" ({d2.attrs['rows_removed_short_docs']} docs curtos removidos: "
          f"{d2.attrs['removed_by_class']})")
