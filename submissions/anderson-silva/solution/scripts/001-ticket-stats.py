"""Deterministic statistics for the challenge 002 support tickets (Dataset 1).

Usage:
  python 001-ticket-stats.py <csv> status-by-channel [--product NAME]
  python 001-ticket-stats.py <csv> time-columns [--product NAME]
  python 001-ticket-stats.py <csv> resolution-before-response [--product NAME] [--sample N]
  python 001-ticket-stats.py <csv> seconds-match [--product NAME]
  python 001-ticket-stats.py <csv> difference-patterns [--product NAME]
  python 001-ticket-stats.py <csv> date-breakdown [--product NAME]
  python 001-ticket-stats.py <csv> duration-by-group [--product NAME]
  python 001-ticket-stats.py <csv> reverse-engineering [--product NAME]
  python 001-ticket-stats.py <csv> clock-reconstruction [--product NAME]
  python 001-ticket-stats.py <csv> ticket-sample [--product NAME] [--sample N]
  python 001-ticket-stats.py <csv> text-patterns [--product NAME]
  python 001-ticket-stats.py <csv> director-questions [--product NAME]

Customer names and e-mails are never read.
"""
import argparse
import math
import re
from datetime import time

import numpy as np
import pandas as pd
from scipy import stats

STATUS_ORDER = ["Closed", "Pending Customer Response", "Open"]
TIME_COLUMNS = ["Date of Purchase", "First Response Time", "Time to Resolution"]
GROUP_COLUMNS = ["Product Purchased", "Ticket Type", "Ticket Priority", "Ticket Channel"]
CSAT_COLUMN = "Customer Satisfaction Rating"
RANK_GROUP_COLUMNS = ["Ticket Priority", "Ticket Channel", "Ticket Type", CSAT_COLUMN]
TEXT_COLUMNS = ["Ticket Subject", "Ticket Description", "Resolution"]
AGE_COLUMN = "Customer Age"
CUSTOMER_COLUMNS = [AGE_COLUMN, "Customer Gender"]
COLUMNS_USED = (["Ticket ID", "Ticket Status", CSAT_COLUMN] + GROUP_COLUMNS + TIME_COLUMNS + TEXT_COLUMNS
                + CUSTOMER_COLUMNS)
MIDNIGHT = time(0)
SAMPLE_SEED = 42
SECONDS_PER_MINUTE = 60
HOUR_BIN_EDGES = [-np.inf, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, np.inf]
PRIORITY_ORDER = ["Low", "Medium", "High", "Critical"]
PLACEHOLDER_PATTERN = r"\{[a-z_]+\}"
WORD_PATTERN = r"[a-z]{4,}"
SENTENCE_BREAK = r"(?<=[.?!])\s+"
TOP_SENTENCES = 5
PERMUTATIONS = 200
# Premise of audit item 95: the two time columns only mark that a step happened; they never measure duration.
STAGE_LABELS = {"Open": "Aberto", "Pending Customer Response": "Aguardando o cliente", "Closed": "Fechado"}
STAGE_ORDER = ["Aberto", "Aguardando o cliente", "Fechado"]
STALLED_STAGES = ["Aberto", "Aguardando o cliente"]
STAGE_GROUP_COLUMNS = ["Ticket Channel", "Ticket Priority", "Ticket Type", "Product Purchased"]
CSAT_GROUP_COLUMNS = ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Product Purchased",
                      "Customer Gender"]
TOP_PRODUCTS = 5
# Dataset 2, audit item 107: tickets routed alone with at least 95% accuracy, out of all tickets.
AUTO_ROUTED_TICKETS = 33852
DATASET_2_TICKETS = 47837
TICKETS_PER_BLOCK = 1000
MINUTES_PER_HOUR = 60
EXAMPLE_TRIAGE_MINUTES = 3


def load_tickets(path, product):
    frame = pd.read_csv(path, usecols=COLUMNS_USED)
    if product is None:
        return frame
    selected = frame[frame["Product Purchased"] == product]
    if selected.empty:
        raise SystemExit(f"Product not found: {product}")
    return selected


def format_percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def print_markdown(table, index_label):
    header = [index_label] + [str(column) for column in table.columns]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    # object dtype keeps integer columns from being printed as floats by iterrows
    for label, row in table.astype(object).iterrows():
        print("| " + " | ".join([str(label)] + [str(value) for value in row]) + " |")


def summarize(series):
    described = series.describe()
    keys = ["count", "min", "25%", "50%", "75%", "max", "mean"]
    return " | ".join(f"{key}={described[key]:.2f}" for key in keys)


def report_status_by_channel(tickets):
    counts = pd.crosstab(tickets["Ticket Channel"], tickets["Ticket Status"]).reindex(columns=STATUS_ORDER, fill_value=0)
    totals = counts.sum(axis=1)
    shares = counts.div(totals, axis=0).map(format_percent)
    shares.insert(0, "Tickets", totals)
    print_markdown(shares, "Canal")

    chi2, p_value = stats.chisquare(totals)
    print("\nVolume por canal contra divisão igual (qui-quadrado de aderência):")
    print(f"  esperado por canal = {totals.sum() / len(totals):.1f} | qui2 = {chi2:.3f} | p = {p_value:.3f}")

    chi2, p_value, dof, _ = stats.chi2_contingency(counts)
    print("\nStatus x canal (qui-quadrado de independência):")
    print(f"  qui2 = {chi2:.3f} | gl = {dof} | p = {p_value:.3f}")

    open_share = counts["Open"] / totals
    high, low = open_share.idxmax(), open_share.idxmin()
    difference = open_share[high] - open_share[low]
    standard_error = math.sqrt(sum(open_share[c] * (1 - open_share[c]) / totals[c] for c in (high, low)))
    print(f"\nMaior e menor fatia de Open: {high} {format_percent(open_share[high])} x {low} {format_percent(open_share[low])}")
    print(f"  diferença = {difference * 100:.1f} pontos | erro padrão da diferença = {standard_error * 100:.1f} pontos"
          f" | diferença / erro padrão = {difference / standard_error:.2f}")


def report_time_columns(tickets, path):
    header = pd.read_csv(path, nrows=0).columns
    date_like = [column for column in header if "Date" in column or "Time" in column]
    print(f"Tickets: {len(tickets)}")
    print(f"Colunas do arquivo com 'Date' ou 'Time' no nome: {date_like}")

    print("\nAmostra de valores brutos (3 primeiros não vazios):")
    for column in TIME_COLUMNS:
        print(f"  {column}: {tickets[column].dropna().head(3).tolist()}")

    print("\nPreenchimento por status (tickets com valor):")
    filled = tickets[TIME_COLUMNS].notna().groupby(tickets["Ticket Status"]).sum().T.reindex(columns=STATUS_ORDER)
    filled.loc["(tickets no status)"] = tickets["Ticket Status"].value_counts().reindex(STATUS_ORDER)
    print_markdown(filled, "Coluna")

    parsed = {column: pd.to_datetime(tickets[column], errors="coerce") for column in TIME_COLUMNS}
    print("\nFaixa de valores:")
    for column, values in parsed.items():
        valid = values.dropna()
        not_converted = int(tickets[column].notna().sum()) - len(valid)
        with_clock_time = int((valid.dt.time != MIDNIGHT).sum())
        print(f"  {column}: {valid.min()} a {valid.max()} | dias distintos = {valid.dt.date.nunique()}"
              f" | com hora diferente de 00:00 = {with_clock_time} | não convertidos = {not_converted}")

    both = parsed["First Response Time"].notna() & parsed["Time to Resolution"].notna()
    hours = (parsed["Time to Resolution"][both] - parsed["First Response Time"][both]).dt.total_seconds() / 3600
    print(f"\nTime to Resolution menos First Response Time, em horas ({int(both.sum())} tickets com as duas):")
    print(f"  {summarize(hours)}")
    print(f"  negativos (resolução antes da primeira resposta) = {int((hours < 0).sum())}")

    days = (parsed["First Response Time"] - parsed["Date of Purchase"]).dt.total_seconds().dropna() / 86400
    print(f"\nFirst Response Time menos Date of Purchase, em dias ({len(days)} tickets):")
    print(f"  {summarize(days)}")


def report_resolution_before_response(tickets, sample_size):
    first_response = pd.to_datetime(tickets["First Response Time"], errors="coerce")
    resolution = pd.to_datetime(tickets["Time to Resolution"], errors="coerce")
    hours = (resolution - first_response).dt.total_seconds() / 3600
    is_negative = hours < 0
    negative = tickets[is_negative].assign(**{"Resolução − 1ª resposta (h)": hours[is_negative].round(2)})
    print(f"Tickets com resolução antes da primeira resposta: {len(negative)}")

    sample = negative.sample(n=min(sample_size, len(negative)), random_state=SAMPLE_SEED).sort_values("Ticket ID")
    columns = ["Product Purchased", "Ticket Channel", "First Response Time", "Time to Resolution",
               "Resolução − 1ª resposta (h)"]
    print(f"\nAmostra aleatória de {len(sample)} (semente {SAMPLE_SEED}), ordenada por Ticket ID:")
    print_markdown(sample.set_index("Ticket ID")[columns], "Ticket ID")


def label_sign(hours):
    if hours < 0:
        return "Negativa"
    if hours > 0:
        return "Positiva"
    return "Zero"


def report_seconds_match(tickets):
    both = tickets["First Response Time"].notna() & tickets["Time to Resolution"].notna()
    first_response = pd.to_datetime(tickets.loc[both, "First Response Time"])
    resolution = pd.to_datetime(tickets.loc[both, "Time to Resolution"])
    hours = (resolution - first_response).dt.total_seconds() / 3600
    same_second = first_response.dt.second == resolution.dt.second

    groups = same_second.groupby(hours.map(label_sign)).agg(["size", "sum"])
    groups.loc["Total"] = [len(same_second), int(same_second.sum())]
    table = pd.DataFrame({
        "Tickets": groups["size"],
        "Segundos iguais": groups["sum"],
        "% iguais": (groups["sum"] / groups["size"]).map(format_percent),
    })
    print(f"Tickets com primeira resposta e resolução: {len(same_second)}")
    print("\nSegundos iguais nos dois horários, por sinal de (resolução − primeira resposta):")
    print_markdown(table, "Diferença")
    print(f"\nReferência: se os segundos fossem independentes, a coincidência esperada seria"
          f" 1/{SECONDS_PER_MINUTE} = {format_percent(1 / SECONDS_PER_MINUTE)}")


def label_hour_bins(edges):
    labels = []
    for low, high in zip(edges[:-1], edges[1:]):
        if low == -np.inf:
            labels.append(f"< {high}")
        elif high == np.inf:
            labels.append(f">= {low}")
        else:
            labels.append(f"{low} a {high}")
    return labels


def report_difference_distribution(first_response, resolution, hours):
    labels = label_hour_bins(HOUR_BIN_EDGES)
    observed = pd.cut(hours, HOUR_BIN_EDGES, right=False, labels=labels).value_counts(sort=False)

    # Reference: every resolution paired with every first response, i.e. no link between the two columns.
    all_pairs = np.subtract.outer(resolution.to_numpy(), first_response.to_numpy()) / np.timedelta64(1, "h")
    expected_share = pd.Series(pd.cut(all_pairs.ravel(), HOUR_BIN_EDGES, right=False, labels=labels)) \
        .value_counts(sort=False, normalize=True).reindex(labels)

    table = pd.DataFrame({
        "Tickets": observed,
        "% observado": (observed / observed.sum()).map(format_percent),
        "% esperado sem relação entre as colunas": expected_share.map(format_percent),
    })
    print("\n1. Distribuição de (resolução − primeira resposta), em faixas de 4 horas [início, fim):")
    print_markdown(table, "Faixa (h)")
    chi2, p_value = stats.chisquare(observed, expected_share * observed.sum())
    print(f"  observado x esperado sem relação (qui-quadrado de aderência): qui2 = {chi2:.3f} | p = {p_value:.3f}")


def report_negative_share(closed, hours):
    is_negative = hours < 0
    print(f"\n2. Fatia de negativos por grupo (geral: {int(is_negative.sum())} de {len(hours)}"
          f" = {format_percent(is_negative.mean())}):")
    for column in GROUP_COLUMNS:
        counts = pd.crosstab(closed[column], is_negative).reindex(columns=[False, True], fill_value=0)
        totals = counts.sum(axis=1)
        share = counts[True] / totals
        table = pd.DataFrame({
            "Fechados": totals,
            "Negativos": counts[True],
            "% negativos": share.map(format_percent),
        }).loc[share.sort_values(ascending=False).index]
        chi2, p_value, dof, _ = stats.chi2_contingency(counts)
        print(f"\n{column} (qui-quadrado de independência: qui2 = {chi2:.3f} | gl = {dof} | p = {p_value:.3f}):")
        print_markdown(table, column)


def report_difference_patterns(tickets):
    closed = tickets[tickets["First Response Time"].notna() & tickets["Time to Resolution"].notna()]
    first_response = pd.to_datetime(closed["First Response Time"])
    resolution = pd.to_datetime(closed["Time to Resolution"])
    hours = (resolution - first_response).dt.total_seconds() / 3600
    print(f"Tickets com primeira resposta e resolução: {len(closed)}")
    report_difference_distribution(first_response, resolution, hours)
    report_negative_share(closed, hours)


def report_date_breakdown(tickets):
    """Test the idea that HH:MM:SS durations were converted to date-times on a single base date."""
    for column in ["First Response Time", "Time to Resolution"]:
        raw = tickets[column].dropna()
        values = pd.to_datetime(raw)
        per_day = values.dt.date.value_counts().sort_index()
        table = pd.DataFrame({"Tickets": per_day, "%": (per_day / per_day.sum()).map(format_percent)})
        print(f"\n{column}: {len(values)} valores | texto bruto com data = {int(raw.str.contains('-').sum())}")
        print_markdown(table, "Data")

        base_day = per_day.idxmax()
        hours_from_base = (values - pd.Timestamp(base_day)).dt.total_seconds() / 3600
        span_hours = (values.max() - values.min()).total_seconds() / 3600
        print(f"  amplitude (máximo − mínimo) = {span_hours:.2f} h")
        print(f"  se fosse duração sobre a meia-noite de {base_day}: de {hours_from_base.min():.2f} h a"
              f" {hours_from_base.max():.2f} h | negativas = {int((hours_from_base < 0).sum())}"
              f" | 24 h ou mais = {int((hours_from_base >= 24).sum())}")


def hours_since_base_day(values):
    base_day = values.dt.date.value_counts().idxmax()
    return (values - pd.Timestamp(base_day)).dt.total_seconds() / 3600


def report_duration_by_group(tickets):
    """Read each time column as a duration since midnight of its most frequent day and compare groups."""
    for column in ["First Response Time", "Time to Resolution"]:
        present = tickets[tickets[column].notna()]
        hours = hours_since_base_day(pd.to_datetime(present[column]))
        is_valid = hours >= 0
        print(f"\n{column} lida como duração (horas desde a meia-noite do dia mais frequente):"
              f" {int(is_valid.sum())} valores | negativos excluídos = {int((~is_valid).sum())}")
        for group_column, order in [("Ticket Priority", PRIORITY_ORDER), ("Ticket Channel", None)]:
            grouped = hours[is_valid].groupby(present.loc[is_valid, group_column])
            summary = grouped.describe()[["count", "25%", "50%", "75%", "mean"]]
            summary = summary.reindex(order) if order else summary
            summary = summary.round(2).astype({"count": int})
            summary.columns = ["Tickets", "Q1 (h)", "Mediana (h)", "Q3 (h)", "Média (h)"]
            statistic, p_value = stats.kruskal(*[group for _, group in grouped])
            print(f"\n  {group_column} (Kruskal-Wallis: H = {statistic:.3f} | p = {p_value:.3f}):")
            print_markdown(summary, group_column)


def print_group_rank_test(hours, frame, column):
    present = frame[column].notna() & hours.notna()
    labels = frame.loc[present, column]
    labels = labels.astype(int) if column == CSAT_COLUMN else labels
    grouped = hours[present].groupby(labels)
    summary = grouped.describe()[["count", "25%", "50%", "75%"]]
    summary = summary.reindex(PRIORITY_ORDER) if column == "Ticket Priority" else summary
    summary = summary.round(2).astype({"count": int})
    summary.columns = ["Tickets", "Q1 (h)", "Mediana (h)", "Q3 (h)"]
    statistic, p_value = stats.kruskal(*[group for _, group in grouped])
    print(f"\n{column} (Kruskal-Wallis: H = {statistic:.3f} | p = {p_value:.3f}):")
    print_markdown(summary, column)


def report_difference_by_group(tickets):
    """Test A: rank test of (resolution - first response) by group; invariant to adding any constant."""
    closed = tickets[tickets["First Response Time"].notna() & tickets["Time to Resolution"].notna()]
    hours = (pd.to_datetime(closed["Time to Resolution"])
             - pd.to_datetime(closed["First Response Time"])).dt.total_seconds() / 3600
    print(f"Teste A: diferença (resolução − primeira resposta) por grupo, {len(closed)} fechados.")
    print("  Kruskal-Wallis usa só a ordem dos valores: o resultado não muda se somarmos uma constante.")
    for column in RANK_GROUP_COLUMNS:
        print_group_rank_test(hours, closed, column)
    rated = closed[CSAT_COLUMN].notna()
    rho, p_value = stats.spearmanr(hours[rated], closed.loc[rated, CSAT_COLUMN])
    print(f"\nSpearman entre a diferença e o CSAT: rho = {rho:.3f} | p = {p_value:.3f} | n = {int(rated.sum())}")


def report_reference_structure(tickets):
    """Test B: do the time values or their shared seconds follow the Ticket ID (sequential generation)?"""
    with_response = tickets[tickets["First Response Time"].notna()].sort_values("Ticket ID")
    print(f"\nTeste B: estrutura da referência, {len(with_response)} tickets com primeira resposta,"
          f" ordenados por Ticket ID.")
    for column in ["First Response Time", "Time to Resolution"]:
        present = with_response[column].notna()
        values = pd.to_datetime(with_response.loc[present, column]).astype("int64")
        rho, p_value = stats.spearmanr(with_response.loc[present, "Ticket ID"], values)
        print(f"  Spearman Ticket ID x {column}: rho = {rho:.3f} | p = {p_value:.3f} | n = {int(present.sum())}")

    seconds = pd.to_datetime(with_response["First Response Time"]).dt.second.to_numpy()
    steps = np.diff(seconds) % SECONDS_PER_MINUTE
    is_small_step = np.isin(steps, [0, 1])
    print(f"  passo dos segundos entre tickets vizinhos igual a 0 ou 1 s: {int(is_small_step.sum())} de {len(steps)}"
          f" = {format_percent(is_small_step.mean())} | esperado ao acaso = {format_percent(2 / SECONDS_PER_MINUTE)}")
    chi2, p_value = stats.chisquare(np.bincount(steps, minlength=SECONDS_PER_MINUTE))
    print(f"  passos espalhados por igual entre 0 e 59 s (qui-quadrado): qui2 = {chi2:.3f} | p = {p_value:.3f}")
    chi2, p_value = stats.chisquare(np.bincount(seconds, minlength=SECONDS_PER_MINUTE))
    print(f"  segundos espalhados por igual entre 0 e 59 (qui-quadrado): qui2 = {chi2:.3f} | p = {p_value:.3f}")


def span_hours(values):
    return (values.max() - values.min()).total_seconds() / 3600


def report_clock_reconstruction(tickets):
    """Unwrap the shared seconds along Ticket ID into a reference clock, remove it, and test what is left.

    Assumes the clock never advances 60 s or more between neighbouring tickets, so each step is
    (seconds difference mod 60). The reconstructed values are known only up to a constant.
    """
    rows = tickets[tickets["First Response Time"].notna()].sort_values("Ticket ID").reset_index(drop=True)
    first_response = pd.to_datetime(rows["First Response Time"])
    resolution = pd.to_datetime(rows["Time to Resolution"])
    steps = first_response.dt.second.diff().mod(SECONDS_PER_MINUTE)
    id_gaps = rows["Ticket ID"].diff()

    print(f"Reconstrução do relógio: {len(rows)} tickets com primeira resposta, ordenados por Ticket ID.")
    step_buckets = pd.cut(steps, [-0.5, 0.5, 1.5, 5.5, 29.5, 59.5], labels=["0", "1", "2 a 5", "6 a 29", "30 a 59"])
    gap_labels = id_gaps.clip(upper=3).map({1.0: "1", 2.0: "2", 3.0: "3 ou mais"})
    counts = pd.crosstab(step_buckets, gap_labels)
    shares = counts.div(counts.sum(axis=0), axis=1).map(format_percent).astype(object)
    shares.loc["(pares)"] = counts.sum(axis=0)
    print("\nPasso dos segundos entre vizinhos (linhas) por distância de ID entre eles (colunas):")
    print_markdown(shares, "Passo (s)")
    print(f"  maior passo = {int(steps.max())} s (a reconstrução supõe menos de {SECONDS_PER_MINUTE} s)")

    elapsed = pd.to_timedelta(steps.fillna(0).cumsum(), unit="s")
    first_shifted = first_response - elapsed
    resolution_shifted = resolution - elapsed
    print(f"\nRelógio reconstruído: avança {elapsed.iloc[-1].total_seconds() / 3600:.2f} h do primeiro ao último ID")
    print(f"  amplitude de First Response Time: original = {span_hours(first_response):.2f} h"
          f" | sem o relógio = {span_hours(first_shifted):.2f} h")
    print(f"  amplitude de Time to Resolution: original = {span_hours(resolution.dropna()):.2f} h"
          f" | sem o relógio = {span_hours(resolution_shifted.dropna()):.2f} h")
    rho, _ = stats.spearmanr(first_shifted.astype("int64"), first_response.astype("int64"))
    print(f"  Spearman entre First Response Time original e sem o relógio: rho = {rho:.3f}")

    # Under "value = clock - duration", duration = clock - value; shown relative to its minimum.
    for column, shifted in [("First Response Time", first_shifted), ("Time to Resolution", resolution_shifted)]:
        duration = (shifted.max() - shifted).dt.total_seconds() / 3600
        print(f"\nDuração reconstruída de {column} (relógio − valor, a menos de uma constante),"
              f" {int(duration.notna().sum())} tickets:")
        for group_column in RANK_GROUP_COLUMNS:
            print_group_rank_test(duration, rows, group_column)


def report_ticket_sample(tickets, per_cell):
    """Random sample stratified by ticket type and status, printed as readable blocks (no personal data)."""
    sample = tickets.groupby(["Ticket Type", "Ticket Status"]).sample(n=per_cell, random_state=SAMPLE_SEED)
    sample = sample.assign(status_order=sample["Ticket Status"].map(STATUS_ORDER.index))
    sample = sample.sort_values(["Ticket Type", "status_order", "Ticket ID"])
    print(f"Amostra: {len(sample)} tickets, {per_cell} por combinação de tipo e status, sorteio com semente"
          f" {SAMPLE_SEED}. Universo: {len(tickets)} tickets.")
    for _, ticket in sample.iterrows():
        csat = "—" if pd.isna(ticket[CSAT_COLUMN]) else int(ticket[CSAT_COLUMN])
        resolution = "—" if pd.isna(ticket["Resolution"]) else ticket["Resolution"]
        print(f"\n### Ticket {ticket['Ticket ID']}")
        print(f"- Produto: {ticket['Product Purchased']} | Tipo: {ticket['Ticket Type']} | Status: {ticket['Ticket Status']}"
              f" | Prioridade: {ticket['Ticket Priority']} | Canal: {ticket['Ticket Channel']} | CSAT: {csat}")
        print(f"- Assunto: {ticket['Ticket Subject']}")
        print(f"- Descrição: {ticket['Ticket Description']}")
        print(f"- Resolução: {resolution}")


def cramers_v(counts):
    chi2, p_value, _, _ = stats.chi2_contingency(counts)
    smaller_side = min(counts.shape) - 1
    return math.sqrt(chi2 / (counts.to_numpy().sum() * smaller_side)), p_value


def print_share(label, count, total):
    print(f"  {label}: {count} de {total} = {format_percent(count / total)}")


def report_placeholders(descriptions):
    print("\n1. Marcadores não substituídos na descrição")
    total = len(descriptions)
    found = descriptions.str.findall(PLACEHOLDER_PATTERN)
    print_share("descrições com algum marcador {…}", int((found.str.len() > 0).sum()), total)
    markers = found.explode().dropna().value_counts()
    print(f"  marcadores distintos = {len(markers)} | os {TOP_SENTENCES} mais frequentes:")
    for marker in markers.head(TOP_SENTENCES).index:
        print_share(f"  descrições com {marker}", int(descriptions.str.contains(re.escape(marker)).sum()), total)
    truncated = descriptions.str.count(r"\{") > descriptions.str.count(PLACEHOLDER_PATTERN)
    print_share("descrições com marcador cortado (chave aberta sem fechar)", int(truncated.sum()), total)


def report_classification_consistency(tickets, descriptions):
    print("\n2. Tipo, assunto e descrição (associação: V de Cramér, 0 = nenhuma, 1 = total)")
    first_sentence = descriptions.str.split(SENTENCE_BREAK, n=1, regex=True).str[0]
    pairs = [("Ticket Type", tickets["Ticket Type"], "Ticket Subject", tickets["Ticket Subject"]),
             ("Ticket Type", tickets["Ticket Type"], "1ª frase da descrição", first_sentence),
             ("Ticket Subject", tickets["Ticket Subject"], "1ª frase da descrição", first_sentence)]
    print(f"  valores distintos: tipo = {tickets['Ticket Type'].nunique()} | assunto = {tickets['Ticket Subject'].nunique()}"
          f" | 1ª frase = {first_sentence.nunique()}")
    for left_name, left, right_name, right in pairs:
        strength, p_value = cramers_v(pd.crosstab(left, right))
        print(f"  {left_name} x {right_name}: V = {strength:.3f} | p = {p_value:.3f}")


def report_description_composition(descriptions):
    print("\n3. Composição da descrição")
    sentences = descriptions.str.split(SENTENCE_BREAK, regex=True)
    total = len(descriptions)
    for position, label in [(0, "1ª frase"), (-1, "última frase")]:
        picked = sentences.str[position].str.strip()
        top = picked.value_counts().head(TOP_SENTENCES)
        print(f"  {label}: {picked.nunique()} distintas | as {TOP_SENTENCES} mais comuns cobrem"
              f" {format_percent(top.sum() / total)} das descrições")
        for sentence, count in top.items():
            print(f"    {count:>5} | {sentence[:110]}")


def report_resolution_content(closed):
    print(f"\n4. Resolução dos tickets com resolução ({len(closed)})")
    words = closed["Resolution"].str.split().str.len()
    print(f"  palavras por resolução: {summarize(words)}")
    print(f"  resoluções distintas = {closed['Resolution'].nunique()}")
    description_words = closed["Ticket Description"].str.lower().str.findall(WORD_PATTERN).map(set).tolist()
    resolution_words = closed["Resolution"].str.lower().str.findall(WORD_PATTERN).map(set).tolist()
    def overlap_share(order):
        return sum(bool(description_words[i] & r) for i, r in zip(order, resolution_words)) / len(closed)

    own = overlap_share(range(len(closed)))
    generator = np.random.default_rng(SAMPLE_SEED)
    shuffled = np.array([overlap_share(generator.permutation(len(closed))) for _ in range(PERMUTATIONS)])
    p_value = (int((shuffled >= own).sum()) + 1) / (PERMUTATIONS + 1)
    print(f"  resolução com alguma palavra (4+ letras) em comum com a própria descrição: {format_percent(own)}")
    print(f"  mesma medida trocando a descrição por a de outro ticket ({PERMUTATIONS} sorteios, semente {SAMPLE_SEED}):"
          f" média = {format_percent(shuffled.mean())} | máximo = {format_percent(shuffled.max())}"
          f" | p (acaso alcança o observado) = {p_value:.3f}")


def report_fill_by_status(tickets):
    print("\n5. Preenchimento de resolução e CSAT por status (tickets com valor)")
    filled = tickets[["Resolution", CSAT_COLUMN]].notna().groupby(tickets["Ticket Status"]).sum().T
    filled = filled.reindex(columns=STATUS_ORDER)
    filled.loc["(tickets no status)"] = tickets["Ticket Status"].value_counts().reindex(STATUS_ORDER)
    print_markdown(filled, "Coluna")


def report_text_patterns(tickets):
    descriptions = tickets["Ticket Description"].fillna("")
    print(f"Padrões de texto: {len(tickets)} tickets.")
    report_placeholders(descriptions)
    report_classification_consistency(tickets, descriptions)
    report_description_composition(descriptions)
    report_resolution_content(tickets[tickets["Resolution"].notna()])
    report_fill_by_status(tickets)


def count_and_share(counts):
    shares = counts.div(counts.sum(axis=1), axis=0)
    return counts.astype(int).astype(str) + " (" + shares.map(format_percent) + ")"


def report_marker_consistency(tickets):
    markers = pd.DataFrame({"1ª resposta preenchida": tickets["First Response Time"].notna(),
                            "Resolução preenchida": tickets["Time to Resolution"].notna()})
    table = markers.groupby(tickets["Ticket Status"]).sum().reindex(STATUS_ORDER)
    table.insert(0, "Tickets", tickets["Ticket Status"].value_counts().reindex(STATUS_ORDER))
    print("Marcadores de tempo por status (premissa do item 95: marcam a etapa, não medem duração):")
    print_markdown(table, "Status")


def stage_counts(tickets, stage, column):
    counts = pd.crosstab(tickets[column], stage).reindex(columns=STAGE_ORDER, fill_value=0)
    return counts.reindex(PRIORITY_ORDER) if column == "Ticket Priority" else counts


def report_stalled_products(counts):
    stalled = counts[STALLED_STAGES].sum(axis=1) / counts.sum(axis=1)
    ranked = stalled.sort_values(kind="stable")
    for title, products in [("menor", ranked.head(TOP_PRODUCTS)), ("maior", ranked.tail(TOP_PRODUCTS)[::-1])]:
        print(f"  {TOP_PRODUCTS} produtos com {title} parcela parada (aberto + aguardando): "
              + ", ".join(f"{name} {format_percent(share)} de {int(counts.loc[name].sum())}"
                          for name, share in products.items()))


def report_risk_segments(tickets, stage):
    for column, value in [("Ticket Priority", "Critical"), ("Ticket Channel", "Social media")]:
        segment = tickets[column] == value
        still_open = int((segment & (stage == "Aberto")).sum())
        print(f"  {value} ainda aberto: {still_open} de {int(segment.sum())} = {format_percent(still_open / segment.sum())}")


def report_where_flow_stalls(tickets, stage):
    print("\n## 1. Onde o fluxo trava (acúmulo em estágio não final)")
    overall = stage.value_counts().reindex(STAGE_ORDER, fill_value=0)
    print("Estágios: " + " | ".join(f"{name} {count} ({format_percent(count / len(stage))})"
                                    for name, count in overall.items()))
    rows = {}
    for column in STAGE_GROUP_COLUMNS:
        counts = stage_counts(tickets, stage, column)
        strength, p_value = cramers_v(counts)
        rows[column] = {"Grupos": len(counts), "V de Cramér": f"{strength:.3f}", "p": f"{p_value:.3f}",
                        "p (Bonferroni)": f"{min(1.0, p_value * len(STAGE_GROUP_COLUMNS)):.3f}"}
        if column == "Product Purchased":
            report_stalled_products(counts)
            continue
        print(f"\nEstágio por {column}:")
        print_markdown(count_and_share(counts), column)
    print("\nAssociação entre estágio e cada variável:")
    print_markdown(pd.DataFrame(rows).T, "Variável")
    print("\nSegmentos de risco:")
    report_risk_segments(tickets, stage)


def epsilon_squared(statistic, total, groups):
    return (statistic - groups + 1) / (total - groups)


def report_csat_drivers(tickets):
    print("\n## 2. O que impacta o CSAT")
    closed = tickets["Ticket Status"] == "Closed"
    rated = tickets[closed & tickets[CSAT_COLUMN].notna()]
    print(f"CSAT preenchido: {len(rated)} de {int(closed.sum())} fechados"
          f" | em tickets não fechados: {int((~closed & tickets[CSAT_COLUMN].notna()).sum())}")
    distribution = rated[CSAT_COLUMN].astype(int).value_counts().sort_index()
    print("Notas: " + " | ".join(f"{score}: {count} ({format_percent(count / len(rated))})"
                                 for score, count in distribution.items())
          + f" | média {rated[CSAT_COLUMN].mean():.2f}")
    tests = len(CSAT_GROUP_COLUMNS) + 1
    rows = {}
    for column in CSAT_GROUP_COLUMNS:
        groups = rated.groupby(column)[CSAT_COLUMN]
        statistic, p_value = stats.kruskal(*[values for _, values in groups])
        means = groups.mean()
        rows[column] = {"Teste": "Kruskal-Wallis", "Grupos": len(means), "Estatística": f"H = {statistic:.2f}",
                        "p": f"{p_value:.3f}", "p (Bonferroni)": f"{min(1.0, p_value * tests):.3f}",
                        "Efeito": f"ε² = {epsilon_squared(statistic, len(rated), len(means)):.4f}",
                        "Menor média": f"{means.idxmin()} {means.min():.2f}",
                        "Maior média": f"{means.idxmax()} {means.max():.2f}"}
    rho, p_value = stats.spearmanr(rated[AGE_COLUMN], rated[CSAT_COLUMN])
    rows[AGE_COLUMN] = {"Teste": "Spearman", "Grupos": "-", "Estatística": f"ρ = {rho:.3f}", "p": f"{p_value:.3f}",
                        "p (Bonferroni)": f"{min(1.0, p_value * tests):.3f}", "Efeito": f"ρ² = {rho ** 2:.4f}",
                        "Menor média": "-", "Maior média": "-"}
    print_markdown(pd.DataFrame(rows).T, "Variável")


def report_waste(tickets, stage):
    print("\n## 3. Quanto estamos desperdiçando")
    counts = stage_counts(tickets, stage, "Ticket Type")
    counts.loc["Total"] = counts.sum()
    table = count_and_share(counts)
    table["Total"] = counts.sum(axis=1)
    print("Onde: tickets por tipo e estágio (contagens reais, % da linha):")
    print_markdown(table, "Tipo")
    share = AUTO_ROUTED_TICKETS / DATASET_2_TICKETS
    coefficient = TICKETS_PER_BLOCK * share / MINUTES_PER_HOUR
    print(f"\nQuanto: horas de triagem economizadas a cada {TICKETS_PER_BLOCK} tickets"
          f" = {TICKETS_PER_BLOCK} × {format_percent(share)} × m ÷ {MINUTES_PER_HOUR} = {coefficient:.2f} × m")
    print(f"  taxa de referência do Dataset 2: {AUTO_ROUTED_TICKETS} de {DATASET_2_TICKETS} = {share:.4f}")
    print(f"  exemplo com m = {EXAMPLE_TRIAGE_MINUTES} min: {coefficient * EXAMPLE_TRIAGE_MINUTES:.1f} horas"
          f" a cada {TICKETS_PER_BLOCK} tickets")


def report_director_questions(tickets):
    stage = tickets["Ticket Status"].map(STAGE_LABELS)
    print(f"Diagnóstico do Dataset 1: {len(tickets)} tickets.\n")
    report_marker_consistency(tickets)
    report_where_flow_stalls(tickets, stage)
    report_csat_drivers(tickets)
    report_waste(tickets, stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("report", choices=["status-by-channel", "time-columns", "resolution-before-response",
                                           "seconds-match", "difference-patterns", "date-breakdown",
                                           "duration-by-group", "reverse-engineering", "clock-reconstruction",
                                           "ticket-sample", "text-patterns", "director-questions"])
    parser.add_argument("--product")
    parser.add_argument("--sample", type=int, help="10 tickets in resolution-before-response; 1 per cell in ticket-sample")
    args = parser.parse_args()
    tickets = load_tickets(args.csv, args.product)
    if args.report == "status-by-channel":
        report_status_by_channel(tickets)
    elif args.report == "time-columns":
        report_time_columns(tickets, args.csv)
    elif args.report == "resolution-before-response":
        report_resolution_before_response(tickets, args.sample or 10)
    elif args.report == "seconds-match":
        report_seconds_match(tickets)
    elif args.report == "difference-patterns":
        report_difference_patterns(tickets)
    elif args.report == "date-breakdown":
        report_date_breakdown(tickets)
    elif args.report == "duration-by-group":
        report_duration_by_group(tickets)
    elif args.report == "reverse-engineering":
        report_difference_by_group(tickets)
        report_reference_structure(tickets)
    elif args.report == "clock-reconstruction":
        report_clock_reconstruction(tickets)
    elif args.report == "ticket-sample":
        report_ticket_sample(tickets, args.sample or 1)
    elif args.report == "director-questions":
        report_director_questions(tickets)
    else:
        report_text_patterns(tickets)


if __name__ == "__main__":
    main()
