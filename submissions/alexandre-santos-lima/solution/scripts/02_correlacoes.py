"""Correlação de cada variável (por categoria) com o churn, nas duas definições de churn.

Numéricas: média churn × retida, Mann-Whitney, AUC univariada (0,5 = sem poder de separar).
Categóricas: taxa de churn por nível, qui-quadrado, V de Cramér.
Todos os p-valores passam por Benjamini-Hochberg (q < 0,05 = sobrevive a múltiplos testes).
Também gera a matriz de Spearman entre categorias (heatmap).

Uso: uv run --with pandas,scipy,matplotlib python -I solution/scripts/02_correlacoes.py <outputs> <docs>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUT, DOCS = Path(sys.argv[1]), Path(sys.argv[2])
b = pd.read_csv(OUT / "account_360.csv", index_col="account_id")
CATS = ["perfil", "receita", "uso", "suporte"]
CATEG = ["perfil_industry", "perfil_country", "perfil_referral_source", "perfil_plan_tier",
         "perfil_is_trial", "perfil_coorte_signup"]
IGNORAR = {"perfil_account_name", "perfil_signup_date", "receita_primeira_assinatura",
           "uso_ultimo_registro", "suporte_ultimo_ticket"}
ALVOS = {"churn_flag_conta": "accounts.churn_flag", "churn_tem_evento": "tem evento em churn_events"}


def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    r = np.empty(n); r[o] = np.minimum(q, 1); return r


linhas = []
for alvo in ALVOS:
    y = b[alvo].astype(bool)
    for cat in CATS:
        for c in [c for c in b.columns if c.startswith(cat + "_") and c not in IGNORAR]:
            x = b[c]
            if c in CATEG:
                tab = pd.crosstab(x, y)
                chi2, p, _, _ = stats.chi2_contingency(tab)
                v = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
                taxas = y.groupby(x).agg(["mean", "size"])
                hi = taxas["mean"].idxmax(); lo = taxas["mean"].idxmin()
                linhas.append(dict(alvo=alvo, categoria=cat, variavel=c, tipo="categórica", efeito=v,
                                   medida="V de Cramér", p=p,
                                   leitura=f"maior: {hi} {taxas.loc[hi,'mean']:.0%} (n={taxas.loc[hi,'size']}); "
                                           f"menor: {lo} {taxas.loc[lo,'mean']:.0%} (n={taxas.loc[lo,'size']})"))
            else:
                x = pd.to_numeric(x, errors="coerce"); ok = x.notna()
                a1, a0 = x[ok & y], x[ok & ~y]
                if a1.nunique() + a0.nunique() < 3:
                    continue
                u, p = stats.mannwhitneyu(a1, a0)
                auc = u / (len(a1) * len(a0))
                linhas.append(dict(alvo=alvo, categoria=cat, variavel=c, tipo="numérica", efeito=auc,
                                   medida="AUC", p=p,
                                   leitura=f"churn {a1.mean():,.2f} × retida {a0.mean():,.2f} "
                                           f"({(a1.mean()/a0.mean()-1) if a0.mean() else np.nan:+.0%})"))
r = pd.DataFrame(linhas)
r["q_bh"] = r.groupby("alvo").p.transform(bh)
r["forca"] = np.where(r.medida == "AUC", (r.efeito - 0.5).abs() * 2, r.efeito)  # 0 = nada, 1 = perfeito
r["sobrevive"] = r.q_bh < 0.05
r = r.sort_values(["alvo", "categoria", "p"])
r.to_csv(OUT / "correlacoes_por_categoria.csv", index=False)

md = ["# Correlação com churn — por categoria\n",
      "Gerado por `solution/scripts/02_correlacoes.py`. `q` = p-valor corrigido (Benjamini-Hochberg). "
      "**Força** normalizada 0–1: para numéricas `|AUC−0,5|×2`; para categóricas V de Cramér. "
      "Referência: < 0,10 desprezível, 0,10–0,20 fraca, 0,20–0,40 moderada.\n"]
for alvo, desc in ALVOS.items():
    rr = r[r.alvo == alvo]; y = b[alvo]
    md.append(f"\n## Alvo: `{alvo}` ({desc}) — {int(y.sum())} de {len(y)} contas ({y.mean():.0%})\n")
    md.append(f"Variáveis testadas: {len(rr)} · sobrevivem à correção: **{int(rr.sobrevive.sum())}**\n")
    for cat in CATS:
        rc = rr[rr.categoria == cat]
        md.append(f"\n### {cat}\n\n| variável | força | medida | p | q | leitura |\n|---|---|---|---|---|---|")
        for _, l in rc.iterrows():
            flag = " ✅" if l.sobrevive else ""
            md.append(f"| `{l.variavel}`{flag} | {l.forca:.2f} | {l.medida} {l.efeito:.2f} | {l.p:.3f} | {l.q_bh:.3f} | {l.leitura} |")
(DOCS / "correlacoes_por_categoria.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# matriz de Spearman entre categorias (numéricas)
num = [c for c in b.columns if c.split("_")[0] in CATS and c not in IGNORAR and c not in CATEG]
num = [c for c in num if pd.api.types.is_numeric_dtype(b[c])]
sel = num + ["churn_flag_conta", "churn_tem_evento", "churn_eventos"]
corr = b[sel].astype(float).corr(method="spearman")
corr.to_csv(OUT / "spearman_entre_categorias.csv")
fig, ax = plt.subplots(figsize=(16, 14))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(sel)), sel, rotation=90, fontsize=7); ax.set_yticks(range(len(sel)), sel, fontsize=7)
fig.colorbar(im, shrink=0.6, label="Spearman ρ"); ax.set_title("Correlação entre variáveis de todas as categorias")
fig.tight_layout(); fig.savefig(OUT / "spearman_entre_categorias.png", dpi=110)

# resumo no terminal
for alvo in ALVOS:
    rr = r[r.alvo == alvo].sort_values("forca", ascending=False)
    print(f"\n=== {alvo}: {int(rr.sobrevive.sum())}/{len(rr)} sobrevivem")
    print(rr.head(12)[["categoria", "variavel", "forca", "p", "q_bh", "leitura"]].to_string(index=False))
# maiores correlações cruzadas entre categorias diferentes
cc = corr.where(np.triu(np.ones(corr.shape, bool), 1)).stack().rename("rho").reset_index()
cc = cc[cc.level_0.str.split("_").str[0] != cc.level_1.str.split("_").str[0]]
print("\n=== maiores |ρ| ENTRE categorias diferentes")
print(cc.reindex(cc.rho.abs().sort_values(ascending=False).index).head(15).to_string(index=False))
