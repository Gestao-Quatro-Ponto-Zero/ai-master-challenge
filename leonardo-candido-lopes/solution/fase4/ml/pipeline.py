"""Fase 4 — Etapas 1 e 2: auditoria pré-treinamento + split por grupos estratificado.
Reprodutível: python pipeline.py  (seed=42). Não altera o CSV original."""
import json, hashlib, time
import numpy as np, pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.utils.class_weight import compute_class_weight
from text_prep import normalize

SEED = 42
SRC = "../../data/all_tickets_processed_improved_v3.csv"
SHORT_WORDS = 5          # textos com < 5 palavras -> flag (não exclusão automática)
GARBAGE_CHARS = 2        # textos com <= 2 caracteres úteis -> lixo (exclusão)
PREFIX_N = 15            # chave de quase-duplicata usada na auditoria anterior
COS_CONFLICT = 0.98      # par quase idêntico (cosseno TF-IDF) com rótulos diferentes -> quarentena
COS_PAIRS = 0.80         # pares calculados a partir deste cosseno (auditoria de vazamento residual)
COS_GROUP = 0.90         # componentes conexos p/ split (v2: 0.80 superagrupava -> grupo de 1.156 linhas; Purchase 5,8% treino vs 2,0% teste)
COS_AGGR = 0.90          # limiar da variante agressiva
LOG = []


def log(step, n_before, n_after, criterio, decisao):
    LOG.append(dict(step=step, antes=int(n_before), depois=int(n_after), removidos=int(n_before - n_after), criterio=criterio, decisao=decisao))
    print(f"[{step}] {n_before} -> {n_after} | {decisao}")


def cosine_pairs(texts, th):
    X = TfidfVectorizer().fit_transform(texts)
    R, C, V = [], [], []
    for s in range(0, X.shape[0], 4000):
        S = (X[s:s + 4000] @ X.T).tocoo()
        m = (S.data >= th) & (S.row + s != S.col)
        R.append(S.row[m] + s); C.append(S.col[m]); V.append(S.data[m])
    return np.concatenate(R), np.concatenate(C), np.concatenate(V)


def main():
    t0 = time.time()
    raw = pd.read_csv(SRC)
    df = raw.copy()
    df.insert(0, "row_id", np.arange(len(df)))
    N0 = len(df)
    A = {"total_original": N0}

    # 1. nulos
    nn = df.dropna(subset=["Document", "Topic_group"])
    log("1_nulos", N0, len(nn), "Document ou Topic_group nulo", "excluir (nenhum encontrado)")
    df["norm"] = df.Document.map(normalize)
    df["n_words"] = df.norm.str.split().str.len()
    df["n_chars"] = df.norm.str.replace(" ", "").str.len()
    y = df.Topic_group.values

    # 2. lixo e textos curtos
    garbage = df.n_chars <= GARBAGE_CHARS
    short = (df.n_words < SHORT_WORDS) & ~garbage
    df["short_flag"] = short
    A["garbage"] = int(garbage.sum())
    A["short_lt5"] = int(short.sum())
    A["short_by_words"] = {int(k): int(v) for k, v in df[short].n_words.value_counts().sort_index().items()}
    A["short_by_class"] = df[short].Topic_group.value_counts().to_dict()
    A["short_examples_first5"] = df[short].head(5)[["row_id", "Document", "Topic_group"]].to_dict("records")
    A["short_examples_all"] = df[short][["row_id", "Document", "Topic_group"]].to_dict("records")
    log("2_lixo", N0, N0 - garbage.sum(), f"<= {GARBAGE_CHARS} caracteres alfanuméricos", "excluir")
    log("2b_curtos", N0 - garbage.sum(), N0 - garbage.sum(), f"< {SHORT_WORDS} palavras", "manter com flag short_flag; sensibilidade com/sem")

    # 3. duplicatas exatas
    A["dup_exact_doc_label"] = int(df.duplicated(["Document", "Topic_group"]).sum())
    A["dup_exact_doc"] = int(df.Document.duplicated().sum())
    A["dup_normalized"] = int(df.norm.duplicated().sum())
    log("3_dup_exatas", N0 - garbage.sum(), N0 - garbage.sum(), "Document+Topic_group idênticos (e texto normalizado idêntico)", "manter 1 (nenhuma encontrada)")

    # 4. quase-duplicatas: prefixo 15 palavras (auditoria anterior) + cosseno
    pref = df.Document.str.split().str[:PREFIX_N].str.join(" ")
    df["prefix_key"] = pref
    dupk = pref.duplicated(keep=False)
    nl = df[dupk].groupby(pref[dupk]).Topic_group.nunique()
    conf_keys = set(nl[nl > 1].index)
    pconf = pref.isin(conf_keys).values
    A["prefix_groups"] = int(len(nl)); A["prefix_records_in_groups"] = int(dupk.sum())
    A["prefix_conflict_groups"] = int(len(conf_keys)); A["prefix_conflict_records"] = int(pconf.sum())
    A["prefix_conflict_label_patterns"] = (df[pconf].groupby("prefix_key").Topic_group.apply(lambda s: " | ".join(sorted(s.unique()))).value_counts().to_dict())
    A["prefix_conflict_examples"] = [dict(prefix=k[:140], labels=df[pref == k].Topic_group.value_counts().to_dict()) for k in list(sorted(conf_keys))[:10]]

    R, C, V = cosine_pairs(df.norm, COS_PAIRS)
    m98 = (V >= COS_CONFLICT) & (y[R] != y[C])
    cconf = np.zeros(N0, bool); cconf[np.unique(np.r_[R[m98], C[m98]])] = True
    A["cos98_conflict_records"] = int(cconf.sum()); A["cos98_overlap_prefix"] = int((cconf & pconf).sum())
    m90 = (V >= COS_AGGR) & (y[R] != y[C])
    c90 = np.zeros(N0, bool); c90[np.unique(np.r_[R[m90], C[m90]])] = True
    A["cos90_conflict_records"] = int(c90.sum())

    quarantine = (pconf | cconf) & ~garbage.values
    df["quarantine"] = quarantine
    n_after2 = N0 - garbage.sum()
    log("4_conflitantes", n_after2, n_after2 - quarantine.sum(),
        f"grupo prefixo-{PREFIX_N} com >1 rótulo OU par cosseno>={COS_CONFLICT} com rótulos diferentes", "quarentena (fora de treino/val/teste)")

    # 5. quase-duplicatas mesmo rótulo (prefixo): manter 1 representante (o primeiro)
    keep_mask = ~garbage.values & ~quarantine
    sub = df[keep_mask]
    same_dup = sub.duplicated("prefix_key", keep="first")
    df["near_dup_removed"] = False
    df.loc[sub.index[same_dup], "near_dup_removed"] = True
    n_after4 = keep_mask.sum()
    log("5_quase_dup_mesmo_rotulo", n_after4, n_after4 - same_dup.sum(), f"mesmo prefixo-{PREFIX_N} e mesmo rótulo", "manter 1 representante")

    df["status"] = np.select([garbage, df.quarantine, df.near_dup_removed], ["excluded_garbage", "quarantine", "excluded_near_dup"], "clean")

    # 6. grupos para o split: componentes conexos (cosseno>=0.80) unidos com grupos de prefixo
    pk_codes = pd.factorize(pref)[0]
    mg = V >= COS_GROUP
    rows = np.r_[R[mg], np.arange(N0)]; cols = np.r_[C[mg], pk_codes + N0]
    G = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(N0 + pk_codes.max() + 1,) * 2)
    _, lab = connected_components(G, directed=False)
    df["group_id"] = [hashlib.md5(str(g).encode()).hexdigest()[:10] for g in lab[:N0]]
    gs = df.group_id.value_counts()
    A["split_groups"] = int(len(gs)); A["split_max_group_size"] = int(gs.max()); A["split_max_group_size_clean"] = int(df[df.status=="clean"].group_id.value_counts().max()); A["split_groups_multi"] = int((gs > 1).sum())

    # 7. StratifiedGroupKFold (20 folds): 3 teste, 3 validação, 14 treino ≈ 15/15/70 — fold atribuído a TODAS as linhas (permite sensibilidade com mesmo split)
    sgkf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=SEED)
    fold = np.empty(N0, int)
    for i, (_, te) in enumerate(sgkf.split(df.norm, y, df.group_id)):
        fold[te] = i
    df["fold"] = fold
    df["split"] = np.where(fold < 3, "test", np.where(fold < 6, "val", "train"))

    clean = df[df.status == "clean"]
    A["final_clean"] = int(len(clean))
    A["split_sizes"] = clean.split.value_counts().to_dict()
    A["split_pct"] = {k: round(v / len(clean), 4) for k, v in A["split_sizes"].items()}
    A["dist_by_split"] = pd.crosstab(clean.Topic_group, clean.split).to_dict()
    A["dist_pct_by_split"] = pd.crosstab(clean.Topic_group, clean.split, normalize="columns").round(4).to_dict()
    A["dist_final"] = clean.Topic_group.value_counts().to_dict()
    gl = clean.Topic_group.value_counts(normalize=True)
    A["max_abs_dev_pp_by_split"] = {s_: round(float((clean[clean.split == s_].Topic_group.value_counts(normalize=True) - gl).abs().max() * 100), 2) for s_ in ["train", "val", "test"]}

    # 8. verificação de vazamento
    sp = {s: clean[clean.split == s] for s in ["train", "val", "test"]}
    leak = {}
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        leak[f"{a}_{b}_groups"] = len(set(sp[a].group_id) & set(sp[b].group_id))
        leak[f"{a}_{b}_norm_text"] = len(set(sp[a].norm) & set(sp[b].norm))
        leak[f"{a}_{b}_prefix15"] = len(set(sp[a].prefix_key) & set(sp[b].prefix_key))
    idx = {s: set(sp[s].index) for s in sp}
    cl = (df.status == "clean").values; spl = df.split.values
    across = cl[R] & cl[C] & (spl[R] != spl[C]) & (R < C)
    leak["pairs_cos>=0.90_across_splits"] = int((across & (V >= COS_GROUP)).sum())
    leak["pairs_cos_0.80-0.90_across_splits_residual"] = int((across & (V < COS_GROUP)).sum())
    tst = cl & (spl == "test"); trn = cl & (spl == "train")
    nb = np.zeros(N0, bool); m_ = (V >= COS_PAIRS) & ((tst[R] & trn[C]) | (tst[C] & trn[R])); nb[R[m_]] = True; nb[C[m_]] = True
    df["test_has_train_neighbor_0_80"] = nb & tst
    leak["test_rows_with_train_neighbor_cos>=0.80"] = int((nb & tst).sum())
    A["leakage_check"] = leak

    # 9. pesos por classe (treino)
    cls = np.array(sorted(clean.Topic_group.unique()))
    w = compute_class_weight("balanced", classes=cls, y=sp["train"].Topic_group)
    A["class_weights_train"] = {c: round(float(x), 4) for c, x in zip(cls, w)}

    # 10. conservador vs agressivo
    aggr_remove = garbage.values | pconf | cconf | c90 | short.values | df.near_dup_removed.values
    cos95_same = (V >= 0.95) & (y[R] == y[C])
    A["comparison"] = {
        "conservador_principal": {"removidos_ou_quarentena": int((df.status != "clean").sum()), "restantes": int(len(clean))},
        "agressivo": {"removidos_ou_quarentena": int(aggr_remove.sum()), "restantes": int(N0 - aggr_remove.sum()),
                      "inclui": "lixo + conflitos prefixo + conflitos cosseno>=0.90 + curtos<5 palavras + quase-dup mesmo rótulo"},
        "auditoria_anterior_fase3": {"removidos": 235, "restantes": 47602, "composicao": "133 curtos (<5 palavras) + 102 em 38 grupos prefixo-15 conflitantes"},
    }
    df["aggressive_keep"] = ~aggr_remove
    A["reconcile_235"] = {"short_lt5": int(short.sum()), "prefix_conflict_records": int(pconf.sum()), "overlap": int((short.values & pconf).sum()), "union": int((short.values | pconf).sum())}
    A["log"] = LOG
    A["params"] = dict(SEED=SEED, SHORT_WORDS=SHORT_WORDS, GARBAGE_CHARS=GARBAGE_CHARS, PREFIX_N=PREFIX_N, COS_CONFLICT=COS_CONFLICT, COS_PAIRS=COS_PAIRS, COS_GROUP=COS_GROUP, COS_AGGR=COS_AGGR, n_splits=20)
    A["runtime_s"] = round(time.time() - t0, 1)

    cols_out = ["row_id", "Document", "Topic_group", "n_words", "short_flag", "group_id", "split", "test_has_train_neighbor_0_80"]
    for s in sp:
        df.loc[sp[s].index, cols_out].to_csv(f"splits/{s}.csv", index=False)
    df[df.status == "quarantine"][["row_id", "Document", "Topic_group", "prefix_key", "group_id"]].to_csv("splits/quarantine.csv", index=False)
    df.drop(columns=["norm"]).to_csv("splits/all_rows_assignment.csv", index=False)
    json.dump(A, open("splits/audit_results.json", "w"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: A[k] for k in ["final_clean", "split_sizes", "split_pct", "leakage_check", "comparison", "reconcile_235"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
