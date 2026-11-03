"""Deterministic profile, baseline classifier and zero-shot comparison of the challenge 002 IT tickets (Dataset 2).

Usage:
  python 002-it-ticket-stats.py <csv> {profile,classifier,zero-shot,disagreements,problem-groups} [--results-dir DIR] [--cache-dir DIR]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_SEED = 42
SAMPLES_PER_TOPIC = 2
SAMPLE_CHARS = 220
TOP_WORDS = 8
MIN_TOPIC_DOC_SHARE = 0.02
CV_FOLDS = 5
NGRAM_RANGE = (1, 2)
MIN_DOC_FREQ = 2
MAX_ITERATIONS = 1000
CONFIDENCE_THRESHOLDS = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
ACCURACY_TARGETS = [0.90, 0.95]
TEMPLATE_PREFIX_WORDS = 5
TEMPLATE_MIN_TICKETS = 20
TOP_PREFIXES = 5
SUSPECT_CONFIDENCE = 0.9
SUSPECT_SAMPLE = 10
TOP_PAIRS = 5
ZERO_SHOT_FILES = {
    "Embeddings OpenAI large": "001-it-embeddings-large-similarities.csv",
    "Jev 1.14": "002-it-jev-probabilities.csv",
}
ORDER_CHECK_FILE = "003-it-jev-order-check.csv"
SUPERVISED_NAME = "Fase 1: TF-IDF supervisionado"
COVERAGE_LEVELS = [0.25, 0.50, 0.75]
NO_ANSWER = "(sem resposta)"
DISAGREEMENT_SAMPLE = 20
READING_CHARS = 300
TOP_DISAGREEMENT_PAIRS = 8
WORD_PAIRS = 4
TOP_GROUP_WORDS = 10
MIN_GROUP_DOC_SHARE = 0.05
EMBEDDING_CACHE_FILES = ("001-it-embeddings-large.npy", "001-it-embeddings-large-done.npy")
GROUP_COUNT_CANDIDATES = [10, 15, 20, 25, 30, 40]
SILHOUETTE_SAMPLE = 10000
KMEANS_INITS = 4
PROBLEM_GROUP_WORDS = 8
MIN_PROBLEM_WORD_SHARE = 0.10
PROBLEM_GROUP_EXAMPLES = 2
PROBLEM_EXAMPLE_CHARS = 160
PROBLEM_GROUPS_FILE = "004-it-problem-groups.csv"
# Groups read as standardized messages or forms in audit item 151.
STANDARDIZED_GROUPS = [7, 14, 30, 33, 36, 37, 38, 39, 40]
DUPLICATE_THRESHOLDS = [0.99, 0.97, 0.95, 0.90]
SIMILARITY_CHUNK = 2000
DUPLICATE_EXAMPLES = 2
DUPLICATE_EXAMPLE_CHARS = 130
NEAR_DUPLICATES_FILE = "005-it-near-duplicates.csv"


def format_percent(value):
    return f"{value * 100:.1f}%".replace(".", ",")


def print_markdown(table, index_label):
    header = [index_label] + [str(column) for column in table.columns]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for label, row in table.astype(object).iterrows():
        print("| " + " | ".join([str(label)] + [str(value) for value in row]) + " |")


def summarize(series):
    described = series.describe()
    keys = ["min", "25%", "50%", "75%", "max", "mean"]
    return " | ".join(f"{key}={described[key]:.1f}" for key in keys)


def report_structure(frame):
    print(f"Linhas: {len(frame)} | colunas: {list(frame.columns)}")
    print(f"Vazios por coluna: {frame.isna().sum().to_dict()}")
    documents = frame["Document"].fillna("")
    duplicated = documents.duplicated(keep=False)
    conflicting = frame[duplicated].groupby("Document")["Topic_group"].nunique()
    print(f"Documentos repetidos (todas as cópias): {int(duplicated.sum())}"
          f" | textos repetidos distintos = {documents[duplicated].nunique()}"
          f" | repetidos com rótulos diferentes = {int((conflicting > 1).sum())}")
    print("\nSinais de pré-processamento (documentos que contêm):")
    for label, pattern in [("letra maiúscula", r"[A-Z]"), ("dígito", r"[0-9]"), ("pontuação", r"[.,;:!?]"),
                           ("caractere fora de a-z e espaço", r"[^a-z ]")]:
        count = int(documents.str.contains(pattern, regex=True).sum())
        print(f"  {label}: {count} de {len(documents)} = {format_percent(count / len(documents))}")


def report_topics(frame, words):
    counts = frame["Topic_group"].value_counts()
    lengths = words.str.len().groupby(frame["Topic_group"]).median()
    table = pd.DataFrame({
        "Tickets": counts,
        "%": (counts / counts.sum()).map(format_percent),
        "Mediana de palavras": lengths.reindex(counts.index),
    })
    print(f"\nCategorias (Topic_group): {len(counts)}")
    print_markdown(table, "Categoria")
    print(f"\nPalavras por documento (geral): {summarize(words.str.len())}")


def report_distinctive_words(frame, words):
    doc_words = words.map(set)
    overall = doc_words.explode().value_counts() / len(frame)
    print(f"\nVocabulário: {len(overall)} palavras distintas")
    print(f"Mais frequentes no geral (em % dos documentos): "
          + ", ".join(f"{word} {format_percent(share)}" for word, share in overall.head(TOP_WORDS).items()))
    print(f"\nPalavras mais características de cada categoria (presença na categoria ÷ presença geral;"
          f" só palavras em pelo menos {format_percent(MIN_TOPIC_DOC_SHARE)} dos documentos da categoria):")
    for topic, topic_words in doc_words.groupby(frame["Topic_group"]):
        in_topic = topic_words.explode().value_counts() / len(topic_words)
        frequent = in_topic[in_topic >= MIN_TOPIC_DOC_SHARE]
        lift = (frequent / overall.reindex(frequent.index)).sort_values(ascending=False).head(TOP_WORDS)
        print(f"  {topic}: " + ", ".join(f"{word} ({ratio:.1f}x)" for word, ratio in lift.items()))


def report_samples(frame):
    print(f"\nAmostra: {SAMPLES_PER_TOPIC} documentos por categoria, sorteio com semente {SAMPLE_SEED}"
          f" (primeiros {SAMPLE_CHARS} caracteres):")
    sample = frame.groupby("Topic_group").sample(n=SAMPLES_PER_TOPIC, random_state=SAMPLE_SEED)
    for (index, row) in sample.iterrows():
        print(f"  [{row['Topic_group']}] linha {index}: {str(row['Document'])[:SAMPLE_CHARS]}")


def fit_out_of_fold(documents, labels):
    # Imported here so the profile report does not need scikit-learn installed.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline

    # The vectorizer sits inside the pipeline, so each fold learns its vocabulary only from its training part.
    model = make_pipeline(
        TfidfVectorizer(ngram_range=NGRAM_RANGE, min_df=MIN_DOC_FREQ, sublinear_tf=True),
        LogisticRegression(max_iter=MAX_ITERATIONS),
    )
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SAMPLE_SEED)
    probabilities = cross_val_predict(model, documents, labels, cv=folds, method="predict_proba", n_jobs=-1)
    return np.unique(labels), probabilities


def report_scores(labels, predicted, order, show_baseline=True):
    from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

    majority = order[0]
    baseline = pd.Series(majority, index=labels.index)
    if show_baseline:
        print(f"\nChute ingênuo (sempre {majority}): acerto {format_percent(accuracy_score(labels, baseline))}"
              f" | F1 macro {format_percent(f1_score(labels, baseline, average='macro', zero_division=0))}")
    print(f"Modelo: acerto {format_percent(accuracy_score(labels, predicted))}"
          f" | F1 macro {format_percent(f1_score(labels, predicted, labels=list(order), average='macro'))}")
    precision, recall, f1, support = precision_recall_fscore_support(labels, predicted, labels=order, zero_division=0)
    table = pd.DataFrame({
        "Tickets": support,
        "Precisão": [format_percent(value) for value in precision],
        "Revocação": [format_percent(value) for value in recall],
        "F1": [format_percent(value) for value in f1],
    }, index=order)
    print("\nPor categoria (precisão = acerto quando o modelo aponta a categoria;"
          " revocação = parte da categoria que o modelo encontra):")
    print_markdown(table, "Categoria")


def report_confusion(labels, predicted, order):
    matrix = pd.crosstab(labels, predicted, normalize="index").reindex(index=order, columns=order, fill_value=0)
    print("\nMatriz de confusão (linha = rótulo, coluna = previsão, em % da linha):")
    print_markdown(matrix.map(format_percent), "Rótulo \\ Previsão")


def report_coverage(confidence, is_correct):
    rows = []
    for threshold in CONFIDENCE_THRESHOLDS:
        covered = confidence >= threshold
        accuracy = is_correct[covered].mean() if covered.any() else float("nan")
        rows.append({"Limiar": f"{threshold:.2f}", "Tickets": int(covered.sum()),
                     "Cobertura": format_percent(covered.mean()), "Acerto nos cobertos": format_percent(accuracy)})
    print("\nCobertura × acerto (o ticket é encaminhado sozinho quando a confiança do modelo atinge o limiar):")
    print_markdown(pd.DataFrame(rows).set_index("Limiar"), "Limiar")
    ranked_confidence = confidence.sort_values(ascending=False, kind="stable")
    ranked_correct = is_correct[ranked_confidence.index].to_numpy()
    cumulative = ranked_correct.cumsum() / np.arange(1, len(ranked_correct) + 1)
    for target in ACCURACY_TARGETS:
        reach = np.flatnonzero(cumulative >= target)
        if len(reach) == 0:
            print(f"Acerto de {format_percent(target)}: nenhum limiar alcança.")
            continue
        last = reach[-1]
        print(f"Acerto de pelo menos {format_percent(target)}: cobertura máxima {format_percent((last + 1) / len(cumulative))}"
              f" ({last + 1} tickets), limiar de confiança {ranked_confidence.iloc[last]:.3f}")


def flag_templates(words):
    prefix = words.map(lambda tokens: " ".join(tokens[:TEMPLATE_PREFIX_WORDS])
                       if len(tokens) >= TEMPLATE_PREFIX_WORDS else None)
    prefix_counts = prefix.value_counts()
    return prefix.map(prefix_counts).ge(TEMPLATE_MIN_TICKETS), prefix_counts


def report_templates(words, labels, predicted, is_correct):
    from sklearn.metrics import f1_score

    templated, prefix_counts = flag_templates(words)
    rest = ~templated
    print(f"\nTickets de abertura repetida (as {TEMPLATE_PREFIX_WORDS} primeiras palavras iguais em pelo menos"
          f" {TEMPLATE_MIN_TICKETS} tickets): {int(templated.sum())} = {format_percent(templated.mean())}")
    print("  Aberturas mais repetidas: "
          + ", ".join(f"\"{text}\" ({count})" for text, count in prefix_counts.head(TOP_PREFIXES).items()))
    by_topic = labels[templated].value_counts()
    print("  Por categoria: " + ", ".join(f"{topic} {count} ({format_percent(count / (labels == topic).sum())}"
                                         f" da categoria)" for topic, count in by_topic.items()))
    print(f"  Acerto: todos {format_percent(is_correct.mean())} | só eles {format_percent(is_correct[templated].mean())}"
          f" | sem eles {format_percent(is_correct[rest].mean())}")
    print(f"  F1 macro sem eles: {format_percent(f1_score(labels[rest], predicted[rest], average='macro'))}")


def report_suspects(frame, labels, predicted, confidence):
    is_error = predicted != labels
    suspect = is_error & (confidence >= SUSPECT_CONFIDENCE)
    print(f"\nRótulos suspeitos (o modelo discorda do rótulo com confiança de pelo menos {SUSPECT_CONFIDENCE:.2f}):"
          f" {int(suspect.sum())} = {format_percent(suspect.mean())} dos tickets"
          f" e {format_percent(suspect.sum() / is_error.sum())} dos erros")
    pairs = (labels[suspect] + " → " + predicted[suspect]).value_counts().head(TOP_PAIRS)
    print("  Pares mais comuns (rótulo → previsão): " + ", ".join(f"{pair} ({count})" for pair, count in pairs.items()))
    sample = frame[suspect].sample(n=min(SUSPECT_SAMPLE, int(suspect.sum())), random_state=SAMPLE_SEED)
    print(f"  Amostra de {len(sample)} para leitura, semente {SAMPLE_SEED} (primeiros {SAMPLE_CHARS} caracteres):")
    for index in sample.index:
        print(f"  linha {index} | rótulo {labels[index]} | previsão {predicted[index]} ({confidence[index]:.2f}):"
              f" {str(frame.at[index, 'Document'])[:SAMPLE_CHARS]}")


def report_classifier(frame, words):
    documents = frame["Document"].fillna("")
    labels = frame["Topic_group"]
    print(f"Modelo: TF-IDF (n-gramas de {NGRAM_RANGE[0]} a {NGRAM_RANGE[1]} palavras, mínimo de {MIN_DOC_FREQ}"
          f" documentos, escala sublinear) + regressão logística | validação cruzada estratificada em"
          f" {CV_FOLDS} partes, semente {SAMPLE_SEED}. Toda previsão vem de uma parte que o modelo não viu.")
    classes, probabilities = fit_out_of_fold(documents, labels)
    predicted = pd.Series(classes[probabilities.argmax(axis=1)], index=frame.index)
    confidence = pd.Series(probabilities.max(axis=1), index=frame.index)
    is_correct = predicted == labels
    order = labels.value_counts().index
    report_scores(labels, predicted, order)
    report_confusion(labels, predicted, order)
    report_coverage(confidence, is_correct)
    report_templates(words, labels, predicted, is_correct)
    report_suspects(frame, labels, predicted, confidence)


def load_zero_shot(path, index, categories):
    table = pd.read_csv(path).drop_duplicates("row", keep="last").set_index("row").reindex(index)
    scores = table[categories]
    present = scores.notna().all(axis=1)
    predicted = pd.Series(NO_ANSWER, index=index, dtype=object)
    predicted[present] = scores[present].idxmax(axis=1)
    ordered = np.sort(scores[present].to_numpy(), axis=1)
    # Jev gives probabilities (confidence = top probability, as in phase 1); embeddings give similarities,
    # so confidence is the margin between the two most similar categories (fixed before the run).
    is_probability = "choice" in table.columns
    confidence = pd.Series(-np.inf, index=index)
    confidence[present] = ordered[:, -1] if is_probability else ordered[:, -1] - ordered[:, -2]
    return predicted, confidence, table, int((~present).sum())


def accuracy_at_coverage(confidence, is_correct, share):
    top = confidence.sort_values(ascending=False, kind="stable").index[:int(round(share * len(confidence)))]
    return is_correct[top].mean()


def max_coverage(confidence, is_correct, target):
    ranked = is_correct[confidence.sort_values(ascending=False, kind="stable").index].to_numpy()
    cumulative = ranked.cumsum() / np.arange(1, len(ranked) + 1)
    reach = np.flatnonzero(cumulative >= target)
    return (reach[-1] + 1) / len(ranked) if len(reach) else 0.0


def report_comparison(methods, labels, order, templated):
    from sklearn.metrics import f1_score

    rows = {}
    for name, (predicted, confidence) in methods.items():
        is_correct = predicted == labels
        row = {"Acerto": format_percent(is_correct.mean()),
               "F1 macro": format_percent(f1_score(labels, predicted, labels=list(order), average="macro"))}
        for share in COVERAGE_LEVELS:
            row[f"Acerto nos {share * 100:.0f}% mais confiantes"] = format_percent(
                accuracy_at_coverage(confidence, is_correct, share))
        for target in ACCURACY_TARGETS:
            row[f"Cobertura com acerto ≥ {target * 100:.0f}%"] = format_percent(
                max_coverage(confidence, is_correct, target))
        row["Acerto sem aberturas repetidas"] = format_percent(is_correct[~templated].mean())
        rows[name] = row
    print("\nComparação nos mesmos 47.837 tickets (cobertura = parte dos tickets em que o método está mais confiante):")
    print_markdown(pd.DataFrame(rows).T, "Método")


def report_order_check(path, labels, jev_table, categories):
    check = pd.read_csv(path).drop_duplicates("row", keep="last").set_index("row")
    original = jev_table.loc[check.index, categories].idxmax(axis=1)
    reversed_order = check[categories].idxmax(axis=1)
    truth = labels[check.index]
    print(f"\nChecagem de ordem do Jev ({len(check)} tickets sorteados por categoria, ordem das opções invertida):")
    print(f"  Mesma resposta nas duas ordens: {format_percent((original == reversed_order).mean())}"
          f" | acerto na ordem original {format_percent((original == truth).mean())}"
          f" | na ordem invertida {format_percent((reversed_order == truth).mean())}")
    answered = jev_table.dropna(subset=categories)
    predicted = answered[categories].idxmax(axis=1)
    picked_first = predicted == answered["first_option"]
    is_error = predicted != labels[answered.index]
    print(f"  Rodada completa: resposta = 1ª opção da lista em {format_percent(picked_first.mean())} dos tickets"
          f" e em {format_percent(picked_first[is_error].mean())} dos erros"
          f" (sem viés, o esperado nos erros é {format_percent(1 / len(categories))})")


def report_run_costs(results_dir):
    print("\nCusto e tempo informados pela API:")
    for file_name in list(ZERO_SHOT_FILES.values()) + [ORDER_CHECK_FILE]:
        table = pd.read_csv(Path(results_dir) / file_name)
        line = f"  {file_name}: {len(table)} linhas | US$ {table['cost_usd'].sum():.4f}"
        if "latency_s" in table.columns:
            line += (f" | latência mediana {table['latency_s'].median():.3f} s"
                     f" | 90% abaixo de {table['latency_s'].quantile(0.9):.3f} s")
        print(line + f" | modelo {', '.join(table['model'].astype(str).unique())}")


def report_zero_shot(frame, words, results_dir):
    labels = frame["Topic_group"]
    order = labels.value_counts().index
    categories = list(order)
    classes, probabilities = fit_out_of_fold(frame["Document"].fillna(""), labels)
    methods = {SUPERVISED_NAME: (pd.Series(classes[probabilities.argmax(axis=1)], index=frame.index),
                                 pd.Series(probabilities.max(axis=1), index=frame.index))}
    tables = {}
    for name, file_name in ZERO_SHOT_FILES.items():
        predicted, confidence, table, missing = load_zero_shot(Path(results_dir) / file_name, frame.index, categories)
        print(f"{name}: {len(frame) - missing} tickets respondidos, {missing} sem resposta")
        methods[name], tables[name] = (predicted, confidence), table
    templated, _ = flag_templates(words)
    report_comparison(methods, labels, order, templated)
    for name in ZERO_SHOT_FILES:
        print(f"\n### {name}")
        report_scores(labels, methods[name][0], order, show_baseline=False)
        report_confusion(labels, methods[name][0], order)
    print("\n### Jev 1.14: rótulos suspeitos (nos embeddings não se aplica, porque a similaridade não é probabilidade)")
    report_suspects(frame, labels, *methods["Jev 1.14"])
    report_order_check(Path(results_dir) / ORDER_CHECK_FILE, labels, tables["Jev 1.14"], categories)
    report_run_costs(results_dir)


def report_group_words(words, group, reference, title):
    doc_words = words.map(set)
    in_group = doc_words[group].explode().value_counts() / int(group.sum())
    in_reference = doc_words[reference].explode().value_counts() / int(reference.sum())
    frequent = in_group[in_group >= MIN_GROUP_DOC_SHARE]
    # A word absent from the reference gets the smallest possible share there, so it still ranks high.
    lift = (frequent / in_reference.reindex(frequent.index).fillna(1 / int(reference.sum())))
    top = lift.sort_values(ascending=False).head(TOP_GROUP_WORDS)
    print(f"  {title}: " + ", ".join(f"{word} ({format_percent(frequent[word])}, {ratio:.1f}x)"
                                     for word, ratio in top.items()))


def report_disagreements(frame, words, results_dir):
    labels = frame["Topic_group"]
    categories = list(labels.value_counts().index)
    classes, probabilities = fit_out_of_fold(frame["Document"].fillna(""), labels)
    supervised = pd.Series(classes[probabilities.argmax(axis=1)], index=frame.index)
    embeddings = load_zero_shot(Path(results_dir) / ZERO_SHOT_FILES["Embeddings OpenAI large"], frame.index,
                                categories)[0]
    jev = load_zero_shot(Path(results_dir) / ZERO_SHOT_FILES["Jev 1.14"], frame.index, categories)[0]
    consensus = (embeddings == jev) & (jev != labels)
    print(f"Discordância de consenso (embeddings e Jev concordam entre si e discordam do rótulo):"
          f" {int(consensus.sum())} = {format_percent(consensus.mean())} dos tickets")
    print(f"  Nesses tickets, a fase 1 (que aprendeu com os rótulos) escolhe o rótulo em"
          f" {format_percent((supervised[consensus] == labels[consensus]).mean())}"
          f" e a categoria do consenso em {format_percent((supervised[consensus] == jev[consensus]).mean())}"
          f" (no conjunto todo, a fase 1 acerta {format_percent((supervised == labels).mean())})")
    pairs = (labels[consensus] + " → " + jev[consensus]).value_counts()
    print("  Pares mais comuns (rótulo → consenso): "
          + ", ".join(f"{pair} ({count})" for pair, count in pairs.head(TOP_DISAGREEMENT_PAIRS).items()))
    print(f"\nPalavras que distinguem cada par dos tickets em que rótulo e consenso coincidem na categoria do consenso"
          f" (presença no par, razão; só palavras em pelo menos {format_percent(MIN_GROUP_DOC_SHARE)} do par):")
    for pair in pairs.head(WORD_PAIRS).index:
        label, predicted = pair.split(" → ")
        group = consensus & (labels == label) & (jev == predicted)
        reference = (labels == predicted) & (jev == predicted) & (embeddings == predicted)
        report_group_words(words, group, reference, f"{pair} ({int(group.sum())} contra {int(reference.sum())})")
    sample = frame[consensus].sample(n=DISAGREEMENT_SAMPLE, random_state=SAMPLE_SEED)
    print(f"\nAmostra aleatória de {DISAGREEMENT_SAMPLE} discordâncias de consenso, semente {SAMPLE_SEED}"
          f" (primeiros {READING_CHARS} caracteres):")
    for index in sample.index:
        print(f"  linha {index} | rótulo {labels[index]} | consenso {jev[index]} | fase 1 {supervised[index]}:"
              f" {str(frame.at[index, 'Document'])[:READING_CHARS]}")


def choose_group_count(vectors):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    fitted = {}
    for count in GROUP_COUNT_CANDIDATES:
        model = KMeans(n_clusters=count, n_init=KMEANS_INITS, random_state=SAMPLE_SEED).fit(vectors)
        score = silhouette_score(vectors, model.labels_, metric="cosine", sample_size=SILHOUETTE_SAMPLE,
                                 random_state=SAMPLE_SEED)
        fitted[count] = (score, model)
    print(f"\nEscolha do número de grupos (silhueta com distância de cosseno, amostra de {SILHOUETTE_SAMPLE}):")
    print_markdown(pd.DataFrame({"Silhueta": {count: f"{score:.4f}" for count, (score, _) in fitted.items()}}),
                   "Grupos")
    best = max(fitted, key=lambda count: fitted[count][0])
    return best, fitted[best][1]


def describe_problem_groups(frame, words, vectors, labels, centers):
    doc_words = words.map(set)
    overall = doc_words.explode().value_counts() / len(frame)
    unit_centers = centers / np.linalg.norm(centers, axis=1, keepdims=True)
    closeness = np.einsum("ij,ij->i", vectors, unit_centers[labels])
    sizes = pd.Series(labels).value_counts()
    rows, examples, cumulative = {}, {}, 0
    for rank, cluster in enumerate(sizes.index, start=1):
        members = np.flatnonzero(labels == cluster)
        in_group = doc_words.iloc[members].explode().value_counts() / len(members)
        frequent = in_group[in_group >= MIN_PROBLEM_WORD_SHARE]
        lift = (frequent / overall.reindex(frequent.index)).sort_values(ascending=False).head(PROBLEM_GROUP_WORDS)
        cumulative += len(members)
        rows[rank] = {"Tickets": len(members), "%": format_percent(len(members) / len(frame)),
                      "% acumulado": format_percent(cumulative / len(frame)),
                      "Palavras características (presença no grupo)":
                          ", ".join(f"{word} ({format_percent(frequent[word])})" for word in lift.index)}
        examples[rank] = members[np.argsort(-closeness[members], kind="stable")[:PROBLEM_GROUP_EXAMPLES]]
    print(f"\nGrupos por volume (palavras em pelo menos {format_percent(MIN_PROBLEM_WORD_SHARE)} do grupo,"
          f" ordenadas pela razão entre a presença no grupo e no total):")
    print_markdown(pd.DataFrame(rows).T, "Grupo")
    print(f"\nOs {PROBLEM_GROUP_EXAMPLES} tickets mais próximos do centro de cada grupo"
          f" (primeiros {PROBLEM_EXAMPLE_CHARS} caracteres):")
    for rank, members in examples.items():
        for index in members:
            print(f"  grupo {rank} | linha {index}: {str(frame.at[index, 'Document'])[:PROBLEM_EXAMPLE_CHARS]}")
    rank_of = {cluster: rank for rank, cluster in enumerate(sizes.index, start=1)}
    return pd.Series(labels).map(rank_of), closeness


def report_problem_groups(frame, words, cache_dir, results_dir):
    vectors_path, done_path = (Path(cache_dir) / name for name in EMBEDDING_CACHE_FILES)
    done = np.load(done_path)
    if not done.all():
        raise SystemExit(f"Embeddings incompletos: {int(done.sum())} de {len(done)}")
    vectors = np.load(vectors_path)
    print(f"Agrupamento pelo texto, sem usar o Topic_group: {len(frame)} tickets, embeddings OpenAI large"
          f" ({vectors.shape[1]} dimensões, normalizados), KMeans com semente {SAMPLE_SEED}")
    count, model = choose_group_count(vectors)
    print(f"\nEscolhido: {count} grupos (maior silhueta entre os candidatos)")
    groups, closeness = describe_problem_groups(frame, words, vectors, model.labels_, model.cluster_centers_)
    output = Path(results_dir) / PROBLEM_GROUPS_FILE
    pd.DataFrame({"row": frame.index, "group": groups.to_numpy(),
                  "closeness_to_center": np.round(closeness, 6)}).to_csv(output, index=False)
    print(f"\nGrupo de cada ticket gravado em {output}")


def nearest_neighbors(vectors):
    neighbor = np.empty(len(vectors), dtype=np.int64)
    similarity = np.empty(len(vectors), dtype=np.float32)
    for start in range(0, len(vectors), SIMILARITY_CHUNK):
        block = vectors[start:start + SIMILARITY_CHUNK] @ vectors.T
        block[np.arange(len(block)), np.arange(start, start + len(block))] = -np.inf  # ignore the ticket itself
        neighbor[start:start + len(block)] = block.argmax(axis=1)
        similarity[start:start + len(block)] = block.max(axis=1)
    return neighbor, similarity


def report_near_duplicates(frame, cache_dir, results_dir):
    vectors_path, done_path = (Path(cache_dir) / name for name in EMBEDDING_CACHE_FILES)
    if not np.load(done_path).all():
        raise SystemExit("Embeddings incompletos")
    neighbor, similarity = nearest_neighbors(np.load(vectors_path))
    groups = pd.read_csv(Path(results_dir) / PROBLEM_GROUPS_FILE).set_index("row")["group"].reindex(frame.index)
    standardized = groups.isin(STANDARDIZED_GROUPS).to_numpy()
    total = len(frame)
    print(f"Quase duplicatas: para cada um dos {total} tickets, o vizinho mais parecido pelos embeddings OpenAI large"
          f" (semelhança de cosseno; 1 = mesmo sentido)")
    rows = {}
    for threshold in DUPLICATE_THRESHOLDS:
        close = similarity >= threshold
        rows[f"≥ {threshold:.2f}"] = {
            "Tickets": int(close.sum()), "% do total": format_percent(close.mean()),
            "Em grupos de mensagem padronizada": int((close & standardized).sum()),
            "Fora deles": int((close & ~standardized).sum()),
            "% do total, fora deles": format_percent((close & ~standardized).mean())}
    print_markdown(pd.DataFrame(rows).T, "Vizinho com semelhança")
    uppers = [np.inf] + DUPLICATE_THRESHOLDS[:-1]
    rng = np.random.default_rng(SAMPLE_SEED)
    print(f"\nExemplos fora dos grupos de mensagem padronizada ({DUPLICATE_EXAMPLES} por faixa, semente {SAMPLE_SEED},"
          f" primeiros {DUPLICATE_EXAMPLE_CHARS} caracteres):")
    for low, high in zip(DUPLICATE_THRESHOLDS, uppers):
        band = np.flatnonzero((similarity >= low) & (similarity < high) & ~standardized)
        for index in rng.choice(band, size=min(DUPLICATE_EXAMPLES, len(band)), replace=False):
            other = neighbor[index]
            print(f"  {similarity[index]:.3f} | linha {index}: {str(frame.at[index, 'Document'])[:DUPLICATE_EXAMPLE_CHARS]}")
            print(f"        | linha {other}: {str(frame.at[other, 'Document'])[:DUPLICATE_EXAMPLE_CHARS]}")
    output = Path(results_dir) / NEAR_DUPLICATES_FILE
    pd.DataFrame({"row": frame.index, "neighbor_row": neighbor, "similarity": np.round(similarity, 6),
                  "standardized_group": standardized}).to_csv(output, index=False)
    print(f"\nVizinho de cada ticket gravado em {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv")
    parser.add_argument("report", choices=["profile", "classifier", "zero-shot", "disagreements", "problem-groups",
                                           "near-duplicates"])
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--cache-dir", default="cache")
    args = parser.parse_args()
    frame = pd.read_csv(args.csv)
    words = frame["Document"].fillna("").str.split()
    if args.report == "classifier":
        report_classifier(frame, words)
        return
    if args.report == "zero-shot":
        report_zero_shot(frame, words, args.results_dir)
        return
    if args.report == "disagreements":
        report_disagreements(frame, words, args.results_dir)
        return
    if args.report == "problem-groups":
        report_problem_groups(frame, words, args.cache_dir, args.results_dir)
        return
    if args.report == "near-duplicates":
        report_near_duplicates(frame, args.cache_dir, args.results_dir)
        return
    report_structure(frame)
    report_topics(frame, words)
    report_distinctive_words(frame, words)
    report_samples(frame)


if __name__ == "__main__":
    main()
