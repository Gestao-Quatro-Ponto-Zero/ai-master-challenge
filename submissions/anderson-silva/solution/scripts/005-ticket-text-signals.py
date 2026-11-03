"""Text signals in the challenge 002 support tickets (Dataset 1): does the resolution carry meaning, and what do
the recurring description sentences say?

Usage:
  python 005-ticket-text-signals.py <csv> resolution-meaning <env-file> [--cache-dir DIR]
  python 005-ticket-text-signals.py <csv> description-phrases

resolution-meaning embeds the description, the resolution and the subject of every closed ticket through
OpenRouter (key read from <env-file>, never printed) and compares true pairs with shuffled pairs.
description-phrases is local: it finds the recurring template sentences, labels them and crosses the labels
with the other columns. Customer names and e-mails are never read.
"""
import argparse
import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

COLUMNS = ["Ticket ID", "Ticket Type", "Ticket Subject", "Ticket Description", "Ticket Status", "Resolution",
           "Ticket Priority", "Ticket Channel", "Customer Satisfaction Rating"]
CSAT = "Customer Satisfaction Rating"
SEED = 42
PERMUTATIONS = 200
EMBEDDING_BATCH = 128
EMBEDDING_BUDGET_USD = 0.10
CACHE_FILE = "002-customer-closed-embeddings.npz"
PLACEHOLDER = r"\{[a-z_]+\}"
PREFIX_CHARS = 30
CROSS_COLUMNS = ["Ticket Subject", "Ticket Type", "Ticket Priority", "Ticket Channel", "Ticket Status"]
SIGNAL_CROSS_COLUMNS = ["Ticket Status", "Ticket Priority"]
GENERIC_OPENER = "I'm having an issue with the {x}."
NO_PROBLEM = "Sem problema específico"
MULTIPLE = "Mais de um"

# Recurring sentences (20+ tickets, exploration in audit item 158), labeled once by the AI for approval.
# Each entry is the start of a template sentence after replacing {placeholders} with {x}.
PROBLEM_TEMPLATES = {
    "Acesso à conta": ["I'm unable to access my {x} account", "It keeps displaying an 'Invalid Credentials'",
                       "I've forgotten my password for my {x}", "I'm facing issues logging into my {x}",
                       "It says my account is locked", "How can I regain access to my account",
                       "How can I recover my account"],
    "Rede e conexão": ["The {x} is unable to establish a stable", "It keeps disconnecting intermittently",
                       "How can I troubleshoot this network problem", "I've recently set up my {x}, but it fails",
                       "I'm having trouble connecting my {x} to my home", "It doesn't detect any networks"],
    "Falha de software": ["I'm encountering a software bug in the {x}", "Whenever I try to perform a specific action",
                          "I've noticed a software bug in the {x} app", "It's causing data loss and unexpected",
                          "There seems to be a glitch in the {x} software", "It freezes frequently, making it"],
    "Hardware": ["My {x} is making strange noises", "I suspect there might be a hardware issue",
                 "It was working fine until yesterday", "The {x} is not turning on", "The screen is flickering",
                 "There seems to be a hardware problem with my {x}"],
    "Perda de dados": ["I've accidentally deleted important data", "Is there any way to recover the deleted",
                       "I've encountered a data loss issue", "All the files and documents seem to have",
                       "My {x} crashed, and I lost all the data", "Is there any way to recover the lost data"],
    "Bateria e carga": ["I'm using the original charger that came", "I've noticed a sudden decrease in battery",
                        "It used to last much longer"],
    "Mensagem de erro": ["I've noticed a peculiar error message", "It says '{x}'."],
}
SIGNAL_TEMPLATES = {
    "Tentativa prévia": ["I've performed a factory reset", "I've tried troubleshooting steps mentioned",
                         "I've tried clearing the cache", "I've checked the device settings",
                         "I've tried different settings and configurations", "I've reviewed the troubleshooting steps",
                         "I've checked for software updates, and my", "I've checked for any available software",
                         "I've tried using different cables", "I've followed online tutorials",
                         "I've followed the troubleshooting steps"],
    "Contato repetido": ["I've already contacted customer support multiple"],
    "Urgência ou impacto no trabalho": ["I need assistance as soon as possible", "I rely heavily on my {x} for my"],
    "Intermitente": ["The issue I'm facing is intermittent", "Sometimes it works fine, but other times"],
    "Após atualização": ["I've recently updated the firmware", "This problem started occurring after the recent",
                         "Could it be related to the update?"],
    "Vários aparelhos": ["I'm experiencing this issue on multiple devices"],
    "Segurança dos dados": ["I'm concerned about the security of my {x}"],
    "Não encontra a função": ["I'm unable to find the option to perform"],
    "Recurso específico": ["I've noticed that the issue occurs consistently"],
    "Dúvida se é só comigo": ["I'm not sure if this issue is specific to my"],
    "Receio de reparo": ["I'm worried that the issue might be hardware"],
    "Sem mudanças no aparelho": ["I haven't made any other changes to the device"],
    "Pedido de orientação": ["Could you please guide me through the steps"],
}


def format_percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def print_markdown(table, index_label):
    header = [index_label] + [str(column) for column in table.columns]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for label, row in table.astype(object).iterrows():
        print("| " + " | ".join([str(label)] + [str(value) for value in row]) + " |")


def load_sibling(file_name, module_name):
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name(file_name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def embed_all(runner, texts, api_key, spent):
    vectors = []
    for start in range(0, len(texts), EMBEDDING_BATCH):
        if spent > EMBEDDING_BUDGET_USD:
            raise SystemExit(f"Limite de US$ {EMBEDDING_BUDGET_USD:.2f} atingido")
        batch_vectors, cost, _ = runner.embed(texts[start:start + EMBEDDING_BATCH], api_key)
        vectors.append(batch_vectors)
        spent += cost
    return np.vstack(vectors), spent


def load_or_embed(closed, env_file, cache_dir):
    path = Path(cache_dir) / CACHE_FILE
    if path.exists():
        cached = np.load(path, allow_pickle=False)
        print(f"Vetores lidos de {path} (sem nova chamada de API)")
        return cached["descriptions"], cached["resolutions"], cached["subjects"], list(cached["subject_names"])
    runner = load_sibling("003-it-zero-shot-run.py", "zero_shot_runner")
    api_key = runner.read_api_key(env_file)
    subject_names = sorted(closed["Ticket Subject"].unique())
    descriptions, spent = embed_all(runner, closed["Ticket Description"].tolist(), api_key, 0.0)
    resolutions, spent = embed_all(runner, closed["Resolution"].tolist(), api_key, spent)
    subjects, spent = embed_all(runner, subject_names, api_key, spent)
    Path(cache_dir).mkdir(exist_ok=True)
    np.savez(path, descriptions=descriptions, resolutions=resolutions, subjects=subjects,
             subject_names=np.array(subject_names))
    print(f"Embeddings gerados: {len(closed)} descrições, {len(closed)} resoluções, {len(subject_names)} assuntos"
          f" | custo informado: US$ {spent:.4f} | guardados em {path}")
    return descriptions, resolutions, subjects, subject_names


def report_pair_similarity(descriptions, resolutions):
    rng = np.random.default_rng(SEED)
    observed = float(np.einsum("ij,ij->i", descriptions, resolutions).mean())
    shuffled = np.array([float(np.einsum("ij,ij->i", descriptions, resolutions[rng.permutation(len(resolutions))]).mean())
                         for _ in range(PERMUTATIONS)])
    p_value = (int((shuffled >= observed).sum()) + 1) / (PERMUTATIONS + 1)
    print(f"\n1. Semelhança média entre a descrição e a própria resolução: {observed:.4f}")
    print(f"   Com a resolução de outro ticket ({PERMUTATIONS} sorteios): média {shuffled.mean():.4f}"
          f" | máximo {shuffled.max():.4f} | p (acaso alcança o observado) = {p_value:.3f}")


def report_retrieval(descriptions, resolutions):
    similarity = resolutions @ descriptions.T
    own = np.diag(similarity)
    ranks = 1 + (similarity > own[:, None]).sum(axis=1)
    total = len(ranks)
    print(f"\n2. Para cada resolução, a posição da própria descrição entre as {total} (1 = a mais parecida):")
    print(f"   mediana {np.median(ranks):.0f} (ao acaso: {(total + 1) / 2:.0f})"
          f" | 1º lugar {format_percent((ranks == 1).mean())} (ao acaso: {format_percent(1 / total)})"
          f" | entre os 10 primeiros {format_percent((ranks <= 10).mean())} (ao acaso: {format_percent(10 / total)})")


def report_subject_match(closed, descriptions, resolutions, subjects, subject_names):
    truth = closed["Ticket Subject"].to_numpy()
    names = np.array(subject_names)
    chance = 1 / len(names)
    print(f"\n3. O assunto mais parecido é o próprio assunto do ticket ({len(names)} assuntos; ao acaso: {format_percent(chance)}):")
    for label, vectors in [("pela resolução", resolutions), ("pela descrição", descriptions)]:
        predicted = names[(vectors @ subjects.T).argmax(axis=1)]
        print(f"   {label}: {format_percent((predicted == truth).mean())}")


def report_resolution_meaning(tickets, env_file, cache_dir):
    closed = tickets[tickets["Resolution"].notna()].reset_index(drop=True)
    print(f"Sentido da resolução: {len(closed)} tickets fechados, embeddings OpenAI large pelo OpenRouter")
    descriptions, resolutions, subjects, subject_names = load_or_embed(closed, env_file, cache_dir)
    report_pair_similarity(descriptions, resolutions)
    report_retrieval(descriptions, resolutions)
    report_subject_match(closed, descriptions, resolutions, subjects, subject_names)


def find_labels(texts, templates):
    found = pd.DataFrame(False, index=texts.index, columns=list(templates))
    for label, starts in templates.items():
        for start in starts:
            found[label] |= texts.str.contains(re.escape(start[:PREFIX_CHARS]), regex=True)
    return found


def problem_of(found):
    count = found.sum(axis=1)
    single = found.idxmax(axis=1).where(count == 1)
    return single.fillna(pd.Series(np.where(count == 0, NO_PROBLEM, MULTIPLE), index=found.index))


def cramers_v(left, right):
    table = pd.crosstab(left, right)
    chi2, p_value, _, _ = stats.chi2_contingency(table, correction=False)
    return np.sqrt(chi2 / (table.to_numpy().sum() * (min(table.shape) - 1))), p_value


def report_problem_crosses(tickets, problem):
    tests = len(CROSS_COLUMNS) + 1
    rows = {}
    for column in CROSS_COLUMNS:
        v, p_value = cramers_v(problem, tickets[column])
        rows[column] = {"Teste": "V de Cramér", "Valor": f"{v:.3f}", "p": f"{p_value:.3f}",
                        "p (Bonferroni)": f"{min(1.0, p_value * tests):.3f}"}
    rated = tickets[CSAT].notna()
    groups = [values for _, values in tickets.loc[rated, CSAT].groupby(problem[rated])]
    h, p_value = stats.kruskal(*groups)
    rows[CSAT] = {"Teste": "Kruskal-Wallis", "Valor": f"H = {h:.2f}", "p": f"{p_value:.3f}",
                  "p (Bonferroni)": f"{min(1.0, p_value * tests):.3f}"}
    print("\nProblema relatado × outras colunas:")
    print_markdown(pd.DataFrame(rows).T, "Coluna")
    means = tickets.loc[rated, CSAT].groupby(problem[rated]).agg(["count", "mean"]).round(2)
    means.columns = ["Fechados com CSAT", "CSAT médio"]
    print("\nCSAT médio por problema relatado:")
    print_markdown(means.astype({"Fechados com CSAT": int}), "Problema")


def report_signal_crosses(tickets, signals):
    tests = len(signals.columns) * (len(SIGNAL_CROSS_COLUMNS) + 1)
    rated = tickets[CSAT].notna()
    rows = {}
    for label in signals.columns:
        has = signals[label]
        row = {"Tickets": int(has.sum()), "%": format_percent(has.mean())}
        for column in SIGNAL_CROSS_COLUMNS:
            v, p_value = cramers_v(has, tickets[column])
            row[f"{column}: V (p Bonf.)"] = f"{v:.3f} ({min(1.0, p_value * tests):.3f})"
        with_signal, without = tickets.loc[rated & has, CSAT], tickets.loc[rated & ~has, CSAT]
        _, p_value = stats.mannwhitneyu(with_signal, without)
        row["CSAT com / sem (p Bonf.)"] = (f"{with_signal.mean():.2f} / {without.mean():.2f}"
                                           f" ({min(1.0, p_value * tests):.3f})")
        rows[label] = row
    print(f"\nSinais do cliente × status, prioridade e CSAT (Bonferroni sobre {tests} testes):")
    print_markdown(pd.DataFrame(rows).T, "Sinal")


def report_description_phrases(tickets):
    texts = tickets["Ticket Description"].fillna("").str.replace(PLACEHOLDER, "{x}", regex=True)
    problems = find_labels(texts, PROBLEM_TEMPLATES)
    signals = find_labels(texts, SIGNAL_TEMPLATES)
    problem = problem_of(problems)
    total = len(tickets)
    print(f"Frases padrão da descrição: {total} tickets, busca pelos primeiros {PREFIX_CHARS} caracteres de cada frase")
    opener = texts.str.contains(re.escape(GENERIC_OPENER), regex=True)
    print(f"Abertura genérica \"{GENERIC_OPENER}\": {int(opener.sum())} ({format_percent(opener.mean())})")
    counts = problem.value_counts()
    print("\nProblema relatado: " + " | ".join(f"{name} {count} ({format_percent(count / total)})"
                                              for name, count in counts.items()))
    print(f"  Problema específico × abertura genérica: {int((opener & (problem == NO_PROBLEM)).sum())} com abertura"
          f" genérica e sem problema; {int((~opener & (problem == NO_PROBLEM)).sum())} sem os dois")
    any_signal = signals.any(axis=1)
    print(f"Tickets com pelo menos um sinal do cliente: {int(any_signal.sum())} ({format_percent(any_signal.mean())})"
          f" | com mais de um: {int((signals.sum(axis=1) > 1).sum())}")
    report_problem_crosses(tickets, problem)
    report_signal_crosses(tickets, signals)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("report", choices=["resolution-meaning", "description-phrases"])
    parser.add_argument("env_file", nargs="?")
    parser.add_argument("--cache-dir", default="cache")
    args = parser.parse_args()
    tickets = pd.read_csv(args.csv, usecols=COLUMNS)
    if args.report == "resolution-meaning":
        if not args.env_file:
            raise SystemExit("resolution-meaning precisa do arquivo .env")
        report_resolution_meaning(tickets, args.env_file, args.cache_dir)
        return
    report_description_phrases(tickets)


if __name__ == "__main__":
    main()
