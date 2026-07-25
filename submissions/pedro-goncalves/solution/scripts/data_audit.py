from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
D1_PATH = ROOT / "data/raw/customer-support/customer_support_tickets.csv"
D2_PATH = ROOT / "data/raw/it-service/all_tickets_processed_improved_v3.csv"
ARTIFACTS = ROOT / "artifacts"
TABLES = ARTIFACTS / "tables"
DOCS = ROOT / "docs/gate-1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def kruskal_summary(data: pd.DataFrame, group: str, value: str) -> dict:
    eligible = data[[group, value]].dropna()
    samples = [part[value].to_numpy() for _, part in eligible.groupby(group)]
    if len(samples) < 2:
        return {"group": group, "n": len(eligible), "h": None, "p": None, "epsilon_sq": None}
    result = stats.kruskal(*samples)
    k = len(samples)
    n = len(eligible)
    epsilon_sq = max(0.0, (result.statistic - k + 1) / (n - k)) if n > k else 0.0
    return {
        "group": group,
        "n": n,
        "h": float(result.statistic),
        "p": float(result.pvalue),
        "epsilon_sq": float(epsilon_sq),
    }


def cramers_v_summary(data: pd.DataFrame, row: str, column: str) -> dict:
    contingency = pd.crosstab(data[row], data[column])
    chi2, p_value, _, _ = stats.chi2_contingency(contingency)
    n = int(contingency.to_numpy().sum())
    denominator = n * min(contingency.shape[0] - 1, contingency.shape[1] - 1)
    cramers_v = np.sqrt(chi2 / denominator) if denominator else 0.0
    return {
        "row": row,
        "column": column,
        "n": n,
        "chi2": float(chi2),
        "p": float(p_value),
        "cramers_v": float(cramers_v),
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    support = pd.read_csv(D1_PATH)
    it_tickets = pd.read_csv(D2_PATH)

    first_response = pd.to_datetime(support["First Response Time"], errors="coerce")
    resolution_time = pd.to_datetime(support["Time to Resolution"], errors="coerce")
    response_to_resolution_hours = (resolution_time - first_response).dt.total_seconds() / 3600
    paired_times = response_to_resolution_hours.dropna()

    support_text = (
        support["Ticket Subject"].fillna("")
        + " "
        + support["Ticket Description"].fillna("")
    ).str.strip()
    normalized_support_text = (
        support_text.str.lower()
        .str.replace(r"\{[^}]+\}", "{placeholder}", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    it_normalized = (
        it_tickets["Document"].fillna("").str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    )
    doc_label_counts = it_tickets.assign(_doc=it_normalized).groupby("_doc")["Topic_group"].nunique()

    pii_patterns = {
        "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
        "phone_like": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"),
    }
    support_pii = {
        name: int(support["Ticket Description"].fillna("").str.contains(pattern).sum())
        for name, pattern in pii_patterns.items()
    }
    repeated_unresolved = support["Ticket Description"].fillna("").str.contains(
        "contacted customer support multiple times, but the issue remains unresolved",
        case=False,
        regex=False,
    )
    it_pii = {
        name: int(it_tickets["Document"].fillna("").str.contains(pattern).sum())
        for name, pattern in pii_patterns.items()
    }

    closed = support[support["Ticket Status"].eq("Closed")].copy()
    associations = [
        kruskal_summary(closed, dimension, "Customer Satisfaction Rating")
        for dimension in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject"]
    ]

    missing_by_status = (
        support.groupby("Ticket Status", observed=True)
        .agg(
            tickets=("Ticket ID", "size"),
            first_response_missing=("First Response Time", lambda values: int(values.isna().sum())),
            resolution_missing=("Time to Resolution", lambda values: int(values.isna().sum())),
            csat_missing=("Customer Satisfaction Rating", lambda values: int(values.isna().sum())),
        )
        .reset_index()
    )
    missing_by_status.to_csv(TABLES / "support_missingness_by_status.csv", index=False)

    type_counts = support["Ticket Type"].value_counts().rename_axis("ticket_type").reset_index(name="tickets")
    type_counts["share"] = type_counts["tickets"] / len(support)
    type_counts.to_csv(TABLES / "support_ticket_type_distribution.csv", index=False)

    class_counts = it_tickets["Topic_group"].value_counts().rename_axis("topic_group").reset_index(name="tickets")
    class_counts["share"] = class_counts["tickets"] / len(it_tickets)
    class_counts.to_csv(TABLES / "it_topic_distribution.csv", index=False)

    csat_groups = (
        closed.groupby(["Ticket Channel", "Ticket Type"], observed=True)["Customer Satisfaction Rating"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .sort_values(["count", "mean"], ascending=[False, True])
    )
    csat_groups.to_csv(TABLES / "support_csat_by_channel_type.csv", index=False)

    audit = {
        "sources": {
            "dataset_1": {"path": str(D1_PATH.relative_to(ROOT)), "sha256": sha256(D1_PATH)},
            "dataset_2": {"path": str(D2_PATH.relative_to(ROOT)), "sha256": sha256(D2_PATH)},
        },
        "dataset_1": {
            "rows": int(len(support)),
            "columns": int(support.shape[1]),
            "ticket_id_unique": bool(support["Ticket ID"].is_unique),
            "exact_duplicate_rows": int(support.duplicated().sum()),
            "null_counts": {column: int(value) for column, value in support.isna().sum().items()},
            "ticket_types": support["Ticket Type"].value_counts().to_dict(),
            "ticket_statuses": support["Ticket Status"].value_counts().to_dict(),
            "ticket_channels": support["Ticket Channel"].value_counts().to_dict(),
            "ticket_priorities": support["Ticket Priority"].value_counts().to_dict(),
            "first_response_dates": sorted(first_response.dropna().dt.date.astype(str).unique().tolist()),
            "resolution_dates": sorted(resolution_time.dropna().dt.date.astype(str).unique().tolist()),
            "paired_timestamp_rows": int(len(paired_times)),
            "negative_response_to_resolution_rows": int((paired_times < 0).sum()),
            "zero_response_to_resolution_rows": int((paired_times == 0).sum()),
            "positive_response_to_resolution_rows": int((paired_times > 0).sum()),
            "negative_response_to_resolution_rate": float((paired_times < 0).mean()),
            "description_exact_duplicate_rows": int(support_text.duplicated(keep=False).sum()),
            "description_normalized_duplicate_rows": int(normalized_support_text.duplicated(keep=False).sum()),
            "description_unique_rows": int(support["Ticket Description"].fillna("").nunique()),
            "placeholder_description_rows": int(
                support["Ticket Description"].fillna("").str.contains(r"\{[^}]+\}", regex=True).sum()
            ),
            "placeholder_resolution_rows": int(
                support["Resolution"].fillna("").str.contains(r"\{[^}]+\}", regex=True).sum()
            ),
            "pii_pattern_counts_in_description": support_pii,
            "repeated_unresolved_rows": int(repeated_unresolved.sum()),
            "repeated_unresolved_by_status": (
                support.loc[repeated_unresolved, "Ticket Status"]
                .value_counts()
                .to_dict()
            ),
            "subject_type_association": cramers_v_summary(
                support, "Ticket Subject", "Ticket Type"
            ),
            "csat_associations_closed_only": associations,
        },
        "dataset_2": {
            "rows": int(len(it_tickets)),
            "columns": int(it_tickets.shape[1]),
            "null_counts": {column: int(value) for column, value in it_tickets.isna().sum().items()},
            "classes": it_tickets["Topic_group"].value_counts().to_dict(),
            "exact_duplicate_rows": int(it_tickets.duplicated().sum()),
            "duplicate_document_rows": int(it_normalized.duplicated(keep=False).sum()),
            "unique_normalized_documents": int(it_normalized.nunique()),
            "documents_with_conflicting_labels": int((doc_label_counts > 1).sum()),
            "empty_normalized_documents": int(it_normalized.eq("").sum()),
            "document_length_chars": {
                "median": float(it_normalized.str.len().median()),
                "p90": float(it_normalized.str.len().quantile(0.90)),
                "max": int(it_normalized.str.len().max()),
            },
            "pii_pattern_counts_in_document": it_pii,
        },
    }

    (ARTIFACTS / "data_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    d1 = audit["dataset_1"]
    d2 = audit["dataset_2"]
    report = f"""# Data Audit: Challenge 002

## Resumo executivo

O Dataset 1 é a base operacional disponível da empresa fictícia e contém **{d1['rows']:,} tickets**. O volume de aproximadamente 30 mil por ano permanece como contexto do brief, não como contagem do arquivo. A base permite analisar filas, status, textos e sinais de cuidado, mas não possui o horário de abertura. `First Response Time` e `Time to Resolution` são timestamps, não durações. Entre {d1['paired_timestamp_rows']:,} tickets com ambos os campos, **{pct(d1['negative_response_to_resolution_rate'])}** têm resolução anterior à primeira resposta. Portanto, FRT, TTR, desperdício de horas e ROI observado não podem ser calculados de forma válida.

O Dataset 2 contém **{d2['rows']:,} tickets** em oito classes e pode sustentar uma prova técnica de classificação, desde que documentos duplicados sejam mantidos no mesmo split. Há {d2['duplicate_document_rows']:,} linhas pertencentes a textos duplicados e {d2['documents_with_conflicting_labels']:,} documentos normalizados com rótulos conflitantes.

## Dataset 1: suporte ao cliente

- Linhas: **{d1['rows']:,}**
- Colunas: **{d1['columns']}**
- `Ticket ID` único: **{d1['ticket_id_unique']}**
- Tipos observados: **{len(d1['ticket_types'])}**, incluindo categorias não resumidas no brief.
- CSAT disponível em **{d1['rows'] - d1['null_counts']['Customer Satisfaction Rating']:,}** linhas, todas sujeitas ao filtro de elegibilidade por status.
- Datas observadas em `First Response Time`: **{', '.join(d1['first_response_dates'])}**
- Datas observadas em `Time to Resolution`: **{', '.join(d1['resolution_dates'])}**
- Pares temporalmente inválidos: **{d1['negative_response_to_resolution_rows']:,} de {d1['paired_timestamp_rows']:,}**
- Descrições com placeholder de template: **{d1['placeholder_description_rows']:,}**
- Descrições distintas: **{d1['description_unique_rows']:,}**
- Associação entre `Ticket Subject` e `Ticket Type`: **V de Cramér = {d1['subject_type_association']['cramers_v']:.3f}** (`p = {d1['subject_type_association']['p']:.3f}`)
- Relatos explícitos de contatos repetidos sem solução: **{d1['repeated_unresolved_rows']:,}**, sendo **{d1['repeated_unresolved_by_status']['Open']:,} abertos**, **{d1['repeated_unresolved_by_status']['Pending Customer Response']:,} pendentes** e **{d1['repeated_unresolved_by_status']['Closed']:,} encerrados**

### Foco no cliente

`Ticket Description` é o campo que preserva a voz do cliente e, por isso, deve ser lido antes de qualquer sugestão automática. As **{d1['placeholder_description_rows']:,} descrições** contêm placeholder de template e trechos ruidosos, mas ainda revelam situações operacionais do exercício. O principal sinal é o grupo de **{d1['repeated_unresolved_rows']:,} clientes** que relata contatos repetidos sem solução, inclusive {d1['repeated_unresolved_by_status']['Closed']:,} casos marcados como encerrados.

O protótipo usa regras explícitas e conservadoras para reconhecer reincidência, dano financeiro, cancelamento, risco legal, segurança, privacidade ou forte insatisfação. Qualquer sinal encaminha o caso para uma pessoa. Na base fornecida, o gate sinaliza casos para inspeção humana; sua taxa de erro deve ser revisada durante o piloto da empresa fictícia.

### Consequência analítica

1. Não calcular FRT, TTR ou touch time.
2. Não chamar diferenças de CSAT de causais.
3. Usar `Ticket Subject`, `Ticket Type` e `Ticket Priority` como campos operacionais existentes, sem deixar que anulem sinais encontrados na mensagem.
4. Priorizar a revisão dos relatos de contato repetido sem solução, inclusive os marcados como encerrados.
5. Tratar qualquer ROI como cenário parametrizado, nunca como economia observada.

## Dataset 2: classificação de tickets de TI

- Linhas: **{d2['rows']:,}**
- Classes: **{len(d2['classes'])}**
- Maior classe: **{max(d2['classes'], key=d2['classes'].get)} ({max(d2['classes'].values()):,})**
- Menor classe: **{min(d2['classes'], key=d2['classes'].get)} ({min(d2['classes'].values()):,})**
- Linhas em grupos de textos duplicados: **{d2['duplicate_document_rows']:,}**
- Documentos com rótulos conflitantes: **{d2['documents_with_conflicting_labels']:,}**
- Comprimento mediano do texto: **{d2['document_length_chars']['median']:.0f} caracteres**

### Consequência analítica

1. Separar grupos de textos normalizados entre treino e teste para evitar leakage.
2. Reportar macro-F1, recall por classe, matriz de confusão e cobertura versus precisão.
3. Não transferir a taxonomia de TI diretamente para o Dataset 1.
4. Apresentar o classificador como prova técnica para a fila de TI, não como classificador da fila de clientes.

## Integridade e privacidade

- Hash Dataset 1: `{audit['sources']['dataset_1']['sha256']}`
- Hash Dataset 2: `{audit['sources']['dataset_2']['sha256']}`
- Nenhum nome, email ou texto bruto de cliente é exportado nos artefatos analíticos.

## Veredito

**Dataset 1: uso restrito.** Inadequado para medir tempos operacionais ou ROI observado.

**Dataset 2: utilizável com controles.** Adequado para experimento de classificação com split agrupado, métricas por classe, calibração e abstenção.
"""
    (DOCS / "data-audit.md").write_text(report, encoding="utf-8")

    print(json.dumps({
        "dataset_1_rows": d1["rows"],
        "dataset_1_negative_time_rate": d1["negative_response_to_resolution_rate"],
        "dataset_2_rows": d2["rows"],
        "dataset_2_duplicate_document_rows": d2["duplicate_document_rows"],
        "report": str((DOCS / "data-audit.md").relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
