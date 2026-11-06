"""Perfis agregados e critérios de validade dos arquivos."""

import re

import pandas as pd

EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")
PHONE = re.compile(r"(?<!\w)\+?\d[\d(). -]{7,}\d(?!\w)")
URL = re.compile(r"https?://\S+|www\.\S+", re.I)
PLACEHOLDER = re.compile(r"\{[a-z_]+\}", re.I)
STAMP = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
DECIMAL = r"[+-]?\d+(?:\.\d+)?"

DIMENSIONS = {
    "canal": ("Ticket Channel", ("Email", "Phone", "Chat", "Social media")),
    "prioridade": ("Ticket Priority", ("Low", "Medium", "High", "Critical")),
    "tipo": (
        "Ticket Type",
        (
            "Technical issue",
            "Billing inquiry",
            "Product inquiry",
            "Refund request",
            "Cancellation request",
        ),
    ),
    "status": ("Ticket Status", ("Open", "Closed", "Pending Customer Response")),
}
DATE_COLUMNS = ("First Response Time", "Time to Resolution")


def strip_identifiers(value: str) -> str:
    value = EMAIL.sub(" marcador_email ", value)
    value = URL.sub(" marcador_url ", value)
    return PHONE.sub(" marcador_numero ", value)


def text_profile(text: pd.Series) -> dict:
    text = text.fillna("").str.strip()
    nonempty = text[text.ne("")]
    normalized = nonempty.str.normalize("NFKC").str.casefold().str.replace(r"\s+", " ", regex=True)
    counts = normalized.value_counts()
    return {
        "presentes": len(nonempty),
        "vazios": int(text.eq("").sum()),
        "menor_que_15_caracteres": int(nonempty.str.len().lt(15).sum()),
        "placeholders_chaves": int(nonempty.str.contains(PLACEHOLDER).sum()),
        "duplicadas_excedentes_normalizadas": int(normalized.duplicated().sum()),
        "maior_grupo_normalizado": int(counts.max()) if len(counts) else 0,
        "distintos_normalizados": len(counts),
        "sinais_email": int(nonempty.str.contains(EMAIL).sum()),
        "sinais_telefone_ou_numero_longo": int(nonempty.str.contains(PHONE).sum()),
        "sinais_url": int(nonempty.str.contains(URL).sum()),
        "prefixo_80_mais_comum_n": int(normalized.str[:80].value_counts().max())
        if len(counts)
        else 0,
    }


def timestamp_profile(values: pd.Series):
    values = values.fillna("").str.strip()
    candidate = values.str.fullmatch(STAMP)
    parsed = pd.to_datetime(values.where(candidate), format="%Y-%m-%d %H:%M:%S", errors="coerce")
    numeric = values.str.fullmatch(DECIMAL)
    negative = pd.to_numeric(values.where(numeric), errors="coerce").lt(0)
    valid = int(parsed.notna().sum())
    n = int(values.ne("").sum())
    return parsed, {
        "presentes": n,
        "timestamps_validos": valid,
        "numericos_sem_unidade": int(numeric.sum()),
        "numericos_negativos_sem_unidade": int(negative.sum()),
        "outros_ou_invalidos": n - valid - int(numeric.sum()),
        "primeiro": parsed.min().isoformat() if valid else None,
        "ultimo": parsed.max().isoformat() if valid else None,
        "fuso": "ausente no campo",
    }


def support_quality(raw: pd.DataFrame):
    df = raw.fillna("").apply(lambda column: column.str.strip())
    id_ok = df["Ticket ID"].ne("")
    excess_exact = df.duplicated() & id_ok
    unique_rows = df.loc[~excess_exact & id_ok].copy()
    conflict = unique_rows["Ticket ID"].duplicated(keep=False)
    clean = unique_rows.loc[~conflict].copy()
    unknown = {}
    for alias, (column, expected) in DIMENSIONS.items():
        values = clean[column]
        known = values.isin(expected)
        unknown[alias] = {
            "ausentes": int(values.eq("").sum()),
            "outras": int((~known & values.ne("")).sum()),
        }
        clean[alias] = values.where(known, "Outra categoria").where(values.ne(""), "Sem informação")
    response, response_stats = timestamp_profile(clean[DATE_COLUMNS[0]])
    resolution, resolution_stats = timestamp_profile(clean[DATE_COLUMNS[1]])
    gap = resolution - response
    raw_rating = pd.to_numeric(clean["Customer Satisfaction Rating"], errors="coerce")
    clean["nota"] = raw_rating.where(raw_rating.isin([1, 2, 3, 4, 5]))
    clean["timestamp_resposta"] = response.notna()
    clean["timestamp_resolucao"] = resolution.notna()
    clean["par_invertido"] = gap.lt(pd.Timedelta(0))
    clean["par_completo"] = gap.notna()
    clean["nota_invalida"] = clean["Customer Satisfaction Rating"].ne("") & clean["nota"].isna()
    clean["resolucao_presente"] = clean["Resolution"].ne("")
    clean["descricao_presente"] = clean["Ticket Description"].ne("")
    return clean, {
        "linhas_originais": len(raw),
        "linhas_utilizaveis": len(clean),
        "duplicatas_de_linha_raw_excedentes": int(raw.duplicated().sum()),
        "linhas_em_ids_repetidos": int((id_ok & df["Ticket ID"].duplicated(keep=False)).sum()),
        "exclusoes": {
            "sem_id": int((~id_ok).sum()),
            "duplicatas_de_linha_com_id": int(excess_exact.sum()),
            "linhas_restantes_com_id_conflitante": int(conflict.sum()),
        },
        "ausencias_por_coluna_raw": {str(k): int(v) for k, v in df.eq("").sum().items()},
        "dimensoes_desconhecidas": unknown,
        "tempo": {
            "campos": {DATE_COLUMNS[0]: response_stats, DATE_COLUMNS[1]: resolution_stats},
            "pares_completos": int(gap.notna().sum()),
            "pares_invertidos": int(clean["par_invertido"].sum()),
            "pares_iguais": int(gap.eq(pd.Timedelta(0)).sum()),
            "frt_horas": None,
            "ttr_horas": None,
            "intervalo_parcial_horas": None,
            "motivo": "Sem abertura; timestamps sem fuso e com inversões entre os dois campos. "
            "Sem validação da ordem dos eventos, o intervalo parcial fica indisponível.",
        },
        "texto": {
            c: text_profile(clean[c])
            for c in ("Ticket Description", "Ticket Subject", "Resolution")
        },
    }
