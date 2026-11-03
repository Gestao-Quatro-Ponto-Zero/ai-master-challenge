import re

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold, train_test_split

from comum import OUT_DIR, REVISAO_DIR, SEED, ler_ds2, normalizar, salvar_csv_excel, salvar_json

BLOCO = 2000
LIMIAR_GRUPO = 0.90
PALAVRAS_FUNCIONAIS = {"the", "is", "to", "and", "of", "a", "in"}
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_FONE = re.compile(r"\d{8,}")
RE_URL = re.compile(r"https?://\S+|www\.\S+", re.I)


def pct(x, n):
    return round(100 * float(x) / n, 2) if n else None


def trunc(s, n):
    return str(s)[:n]


def perfil(df):
    doc = df["Document"].fillna("").astype(str)
    n_pal = doc.str.split().str.len()
    vc = df["Topic_group"].value_counts()
    rng = np.random.RandomState(SEED)
    amostra = df.loc[rng.choice(len(df), 10, replace=False), ["id", "Document"]]
    salvar_csv_excel(amostra.assign(Document=amostra["Document"].map(lambda s: trunc(s, 200))),
                     REVISAO_DIR / "f1_amostra_idioma.csv")
    return {
        "linhas": len(df),
        "nulos": df.isna().sum().to_dict(),
        "textos_vazios": int((doc.str.strip() == "").sum()),
        "textos_menos_de_3_palavras": int((n_pal < 3).sum()),
        "classes": {k: {"n": int(v), "pct": pct(v, len(df))} for k, v in vc.items()},
        "palavras": {f"p{q}": float(np.percentile(n_pal, q)) for q in (5, 50, 95)} | {"max": int(n_pal.max())},
        "pct_nao_ascii": pct(doc.map(lambda s: not s.isascii()).sum(), len(df)),
        "dados_pessoais_acertos": {
            "email": int(doc.str.count(RE_EMAIL).sum()),
            "telefone_8mais_digitos": int(doc.str.count(RE_FONE).sum()),
            "url": int(doc.str.count(RE_URL).sum()),
            "docs_com_email": int(doc.str.contains(RE_EMAIL).sum()),
            "docs_com_telefone": int(doc.str.contains(RE_FONE).sum()),
            "docs_com_url": int(doc.str.contains(RE_URL).sum()),
        },
    }


def preprocessado(df):
    doc = df["Document"].fillna("").astype(str)
    n = len(df)
    tokens = doc.str.split()
    r = {
        "pct_com_maiuscula": pct(doc.str.contains(r"[A-Z]").sum(), n),
        "pct_com_pontuacao": pct(doc.str.contains(r"[^\w\s]").sum(), n),
        "pct_com_palavra_funcional": pct(tokens.map(lambda t: bool(PALAVRAS_FUNCIONAIS & set(t))).sum(), n),
        "pct_por_palavra_funcional": {w: pct(tokens.map(lambda t, w=w: w in t).sum(), n) for w in sorted(PALAVRAS_FUNCIONAIS)},
    }
    r["texto_pre_processado"] = (r["pct_com_maiuscula"] == 0 or r["pct_com_pontuacao"] == 0
                                 or r["pct_com_palavra_funcional"] == 0)
    rng = np.random.RandomState(SEED)
    amostra = df.loc[rng.choice(n, 5, replace=False), ["id", "Document", "Topic_group"]]
    salvar_csv_excel(amostra, REVISAO_DIR / "f1_amostra_texto.csv")
    return r


def duplicados_exatos(norm, y):
    grupos = pd.DataFrame({"norm": norm, "y": y, "i": range(len(norm))}).groupby("norm")
    tam = grupos["i"].transform("size")
    g = grupos.agg(n=("i", "size"), rotulos=("y", "nunique"))
    g = g[g["n"] >= 2]
    arestas = []
    for idx in grupos.indices.values():
        if len(idx) >= 2:
            arestas += [(idx[0], j) for j in idx[1:]]
    return {"grupos_tam_2mais": int(len(g)), "tickets_envolvidos": int((tam >= 2).sum()),
            "grupos_com_mais_de_um_rotulo": int((g["rotulos"] > 1).sum()),
            "tickets_em_grupos_com_conflito": int(g.loc[g["rotulos"] > 1, "n"].sum())}, arestas


def pares_cosseno(norm):
    X = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit_transform(norm).astype(np.float32).tocsr()
    I, J, S = [], [], []
    for ini in range(0, X.shape[0], BLOCO):
        sim = (X[ini:ini + BLOCO] @ X.T).tocoo()
        i = sim.row + ini
        keep = (sim.data >= 0.80 - 1e-6) & (i < sim.col)
        I.append(i[keep]); J.append(sim.col[keep]); S.append(sim.data[keep])
    return np.concatenate(I), np.concatenate(J), np.concatenate(S), X.shape


def main():
    df = ler_ds2()
    n, y = len(df), df["Topic_group"].values
    REVISAO_DIR.mkdir(parents=True, exist_ok=True)
    a = {"3.1_perfil": perfil(df), "3.2_preprocessamento": preprocessado(df)}
    norm = df["Document"].map(normalizar).tolist()

    a["3.4_duplicados_exatos"], arestas_exatas = duplicados_exatos(norm, y)

    I, J, S, forma = pares_cosseno(norm)
    a["3.5_quase_duplicados"] = {"tfidf_forma": list(forma),
                                 "pares_cos_0.80": int((S >= 0.80 - 1e-6).sum()),
                                 "pares_cos_0.90": int((S >= 0.90 - 1e-6).sum()),
                                 "pares_cos_0.95": int((S >= 0.95 - 1e-6).sum())}
    # tolerância 1e-6: float32 pode pôr um cosseno exato de 0,90 em 0,8999999
    m = S >= LIMIAR_GRUPO - 1e-6
    ex = np.array(arestas_exatas, dtype=np.int64).reshape(-1, 2)
    ri, ci = np.concatenate([I[m], ex[:, 0]]), np.concatenate([J[m], ex[:, 1]])
    G = coo_matrix((np.ones(len(ri)), (ri, ci)), shape=(n, n))
    _, group_id = connected_components(G, directed=False)
    df["group_id"] = group_id
    tam = df.groupby("group_id")["id"].transform("size")
    nrot = df.groupby("group_id")["Topic_group"].transform("nunique")
    g_tam = df.groupby("group_id").size()
    g_rot = df.groupby("group_id")["Topic_group"].nunique()
    maior = int(g_tam.max())
    a["3.5_quase_duplicados"] |= {
        "n_grupos": int(len(g_tam)), "n_grupos_tam_2mais": int((g_tam >= 2).sum()),
        "pct_tickets_em_grupos_tam_2mais": pct((tam >= 2).sum(), n),
        "maior_grupo": maior, "maior_grupo_pct_linhas": pct(maior, n),
        "alerta_encadeamento_maior_grupo_acima_1pct": maior > 0.01 * n,
        "grupos_com_conflito_de_rotulo": int((g_rot > 1).sum()),
        "tickets_em_grupos_com_conflito": int((nrot > 1).sum()),
    }

    conf = df[nrot > 1]
    amostra = conf.sample(min(30, len(conf)), random_state=SEED).sort_values(["group_id", "id"])
    salvar_csv_excel(amostra.assign(texto=amostra["Document"].map(lambda s: trunc(s, 300)))
                     [["group_id", "id", "Topic_group", "texto"]], REVISAO_DIR / "f1_conflitos_rotulo.csv")

    fronteira = []
    for lo, hi in [(0.85, 0.90), (0.90, 0.95)]:
        idx = np.flatnonzero((S >= lo - 1e-6) & (S < hi - 1e-6))
        sel = np.random.RandomState(SEED).choice(idx, min(20, len(idx)), replace=False)
        for k in sel:
            ia, ib = int(I[k]), int(J[k])
            fronteira.append({"id_a": ia, "id_b": ib, "cosseno": round(float(S[k]), 4),
                              "mesmo_rotulo": "s" if y[ia] == y[ib] else "n",
                              "texto_a": trunc(df.at[ia, "Document"], 300), "texto_b": trunc(df.at[ib, "Document"], 300)})
    salvar_csv_excel(pd.DataFrame(fronteira), REVISAO_DIR / "f1_pares_fronteira.csv")

    # 3.7 holdout congelado
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    _, hold_g = next(iter(sgkf.split(df, y, groups=group_id)))
    split_g = np.full(n, "treino", dtype=object); split_g[hold_g] = "holdout"
    _, hold_a = train_test_split(np.arange(n), test_size=0.2, stratify=y, random_state=SEED)
    split_a = np.full(n, "treino", dtype=object); split_a[hold_a] = "holdout"
    df["split_grupo"], df["split_aleatorio"] = split_g, split_a
    df[["id", "group_id", "split_grupo", "split_aleatorio"]].to_csv(OUT_DIR / "f1_splits.csv", index=False)

    tot = df["Topic_group"].value_counts(normalize=True)
    dist = {}
    for col in ["split_grupo", "split_aleatorio"]:
        h = df[df[col] == "holdout"]
        dist[col] = {"n_holdout": int(len(h)), "pct_linhas": pct(len(h), n),
                     "pct_por_classe": (h["Topic_group"].value_counts(normalize=True) * 100).round(2).to_dict()}
    dist["pct_por_classe_total"] = (tot * 100).round(2).to_dict()

    def exposicao(col):
        grupos_treino = set(df.loc[df[col] == "treino", "group_id"])
        h = df[df[col] == "holdout"]
        exp = h["group_id"].isin(grupos_treino)
        return {"n": int(exp.sum()), "pct": pct(exp.sum(), len(h))}

    dist["exposicao_vazamento"] = {"aleatorio": exposicao("split_aleatorio"), "grupo": exposicao("split_grupo")}
    a["3.7_holdout"] = dist
    # ruído = tickets que divergem do rótulo majoritário do próprio grupo (não o grupo inteiro)
    em_grupo = df[tam >= 2]
    cont = em_grupo.groupby(["group_id", "Topic_group"]).size()
    por_grupo = cont.groupby(level=0).agg(["sum", "max"])
    fora = int((por_grupo["sum"] - por_grupo["max"]).sum())
    conflito = por_grupo[por_grupo["sum"] > por_grupo["max"]]
    gmaior = int(conflito["sum"].idxmax())
    a["3.5_quase_duplicados"] |= {
        "tickets_fora_da_maioria_do_grupo": fora,
        "tickets_em_grupos_tam_2mais": int(len(em_grupo)),
        "pct_fora_da_maioria_sobre_tickets_em_grupos": pct(fora, len(em_grupo)),
        "pct_fora_da_maioria_sobre_base": pct(fora, n),
        "maior_grupo_em_conflito": {"group_id": gmaior, "tamanho": int(conflito.at[gmaior, "sum"]),
                                    "contagem_por_rotulo": cont.loc[gmaior].sort_values(ascending=False).to_dict()},
        "grupos_em_conflito_de_tamanho_2": int((conflito["sum"] == 2).sum()),
    }
    salvar_json(a, "f1_ds2_auditoria.json")

    p, q, e = a["3.1_perfil"], a["3.5_quase_duplicados"], dist["exposicao_vazamento"]
    print(f"linhas {p['linhas']}; vazios {p['textos_vazios']}; <3 palavras {p['textos_menos_de_3_palavras']}; não ASCII {p['pct_nao_ascii']}%")
    print(f"pré-processado: {a['3.2_preprocessamento']['texto_pre_processado']} "
          f"(maiúscula {a['3.2_preprocessamento']['pct_com_maiuscula']}%, pontuação {a['3.2_preprocessamento']['pct_com_pontuacao']}%)")
    print(f"exatos: {a['3.4_duplicados_exatos']}")
    print(f"quase-dup: {q}")
    print(f"holdout grupo {dist['split_grupo']['n_holdout']}, aleatório {dist['split_aleatorio']['n_holdout']}; exposição {e}")


if __name__ == "__main__":
    main()
