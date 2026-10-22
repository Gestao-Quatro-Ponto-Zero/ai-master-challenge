"""Confere nos dados cada achado que as entregas públicas citam.

Não confia em número de ninguém: recalcula tudo a partir dos CSVs.

Uso (da pasta submissions/vinicius-alves):
    .venv/bin/python process-log/01-estado-da-arte/verificar_achados.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import cross_val_score, train_test_split

RAIZ = Path(__file__).resolve().parents[2]
D1 = RAIZ / "data/d1/customer_support_tickets.csv"
D2 = RAIZ / "data/d2/all_tickets_processed_improved_v3.csv"
SEMENTE = 42
saida = {}


def registra(chave, valor, texto):
    saida[chave] = valor
    print(f"  {texto}")


def dataset1():
    print("\n=== DATASET 1 · tickets de clientes ===")
    linhas_fisicas = sum(1 for _ in open(D1, encoding="utf-8"))
    d = pd.read_csv(D1)
    registra("d1_registros", len(d), f"Registros: {len(d):,} (o arquivo tem {linhas_fisicas:,} linhas físicas, porque as descrições têm quebra de linha)")

    status = d["Ticket Status"].value_counts()
    registra("d1_status", status.to_dict(), "Status: " + ", ".join(f"{k} {v:,} ({v/len(d):.1%})" for k, v in status.items()))
    aberto = d[d["Ticket Status"] == "Open"]
    registra("d1_open_sem_resposta", int(aberto["First Response Time"].isna().sum()), f"Open sem 1ª resposta: {aberto['First Response Time'].isna().sum():,} de {len(aberto):,}")

    frt = pd.to_datetime(d["First Response Time"])
    ttr = pd.to_datetime(d["Time to Resolution"])
    compra = pd.to_datetime(d["Date of Purchase"])
    todos = pd.concat([frt, ttr]).dropna()
    janela = (todos.max() - todos.min()).total_seconds() / 3600
    registra("d1_janela_horas", round(janela, 1), f"Todas as respostas e resoluções entre {todos.min()} e {todos.max()}: {janela:.1f} horas")
    registra("d1_compras", [str(compra.min().date()), str(compra.max().date())], f"Compras entre {compra.min().date()} e {compra.max().date()}")
    registra("d1_coluna_abertura", any(re.search(r"creat|open|abert", c, re.I) for c in d.columns),
             "Existe coluna com data de abertura? " + ("sim" if any(re.search(r"creat|opened|abert", c, re.I) for c in d.columns) else "não"))

    fechado = d[d["Ticket Status"] == "Closed"].copy()
    dif = (ttr[fechado.index] - frt[fechado.index]).dt.total_seconds() / 3600
    invertido = (dif < 0).mean()
    registra("d1_invertido", round(invertido, 4), f"Fechados com resolução ANTES da 1ª resposta: {invertido:.1%} ({(dif < 0).sum():,} de {len(fechado):,})")
    registra("d1_dif_media_h", round(dif.mean(), 2), f"Diferença resolução menos 1ª resposta: média {dif.mean():.2f} h, desvio {dif.std():.1f} h")

    ph = d["Ticket Description"].str.contains(r"\{product_purchased\}", regex=True).mean()
    registra("d1_placeholder", round(ph, 4), f"Descrições com {{product_purchased}} sem preencher: {ph:.1%}")
    primeira_frase = d["Ticket Description"].str.split(r"(?<=[.?!])\s", n=1, regex=True).str[0]
    registra("d1_frases_abertura", int(primeira_frase.nunique()), f"Frases de abertura diferentes: {primeira_frase.nunique()} (a mais comum aparece em {primeira_frase.value_counts(normalize=True).iloc[0]:.0%})")
    exemplos = fechado["Resolution"].sample(5, random_state=SEMENTE).tolist()
    registra("d1_resolucoes_exemplo", exemplos, "Resoluções sorteadas: " + " | ".join(exemplos))

    dominios = d["Customer Email"].str.split("@").str[1].value_counts()
    registra("d1_dominios", dominios.to_dict(), "Domínios de e-mail: " + ", ".join(f"{k} {v:,}" for k, v in dominios.items()))

    print("  Teste de sorteio (qui-quadrado contra distribuição igual). p alto = compatível com sorteio:")
    uniformes = {}
    for col in ["Ticket Type", "Ticket Subject", "Ticket Priority", "Ticket Channel", "Customer Gender", "Product Purchased", "Customer Satisfaction Rating"]:
        cont = d[col].value_counts()
        p = stats.chisquare(cont.values).pvalue
        uniformes[col] = {"opcoes": len(cont), "maior": round(cont.max() / cont.sum(), 4), "menor": round(cont.min() / cont.sum(), 4), "p": round(p, 3)}
        print(f"    {col:<30} {len(cont):>2} opções, de {cont.min()/cont.sum():.1%} a {cont.max()/cont.sum():.1%}, p = {p:.3f}")
    saida["d1_uniformidade"] = uniformes
    idade = d["Customer Age"]
    registra("d1_idade", [int(idade.min()), int(idade.max())], f"Idade dos clientes: de {idade.min()} a {idade.max()}, contagem por idade varia de {idade.value_counts().min()} a {idade.value_counts().max()}")

    print("  Prioridade e status (prioridade muda a chance de fechar?):")
    tab = pd.crosstab(d["Ticket Priority"], d["Ticket Status"])
    p = stats.chi2_contingency(tab).pvalue
    fechados_por_prior = (tab["Closed"] / tab.sum(axis=1)).round(3).to_dict()
    registra("d1_prioridade_status_p", round(p, 3), f"    Fechados por prioridade: {fechados_por_prior}, p = {p:.3f}")
    dif_f = dif.rename("h")
    por_prior = fechado.assign(h=dif_f).groupby("Ticket Priority")["h"].mean().round(2).to_dict()
    registra("d1_tempo_por_prioridade", por_prior, f"    Diferença média de horas por prioridade nos fechados: {por_prior}")

    print("  O que explica a satisfação (só fechados têm nota):")
    csat = fechado["Customer Satisfaction Rating"]
    registra("d1_csat_contagem", csat.value_counts().sort_index().to_dict(), f"    Notas 1 a 5: {csat.value_counts().sort_index().to_dict()}")
    r, p = stats.spearmanr(dif, csat)
    registra("d1_csat_vs_tempo", {"r": round(r, 3), "p": round(p, 3)}, f"    Nota x horas: r = {r:.3f}, p = {p:.3f}")
    associacoes = {}
    for col in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Customer Gender", "Ticket Subject"]:
        p = stats.chi2_contingency(pd.crosstab(fechado[col], csat)).pvalue
        associacoes[col] = round(p, 3)
    registra("d1_csat_associacoes_p", associacoes, f"    Nota x cada coluna (p): {associacoes}")
    X = pd.get_dummies(fechado[["Ticket Channel", "Ticket Priority", "Ticket Type", "Customer Gender", "Ticket Subject", "Product Purchased"]]).assign(idade=fechado["Customer Age"], horas=dif)
    acc = cross_val_score(LogisticRegression(max_iter=2000), X, csat, cv=5).mean()
    acaso = csat.value_counts(normalize=True).max()
    registra("d1_csat_modelo", {"acerto": round(acc, 3), "acaso": round(acaso, 3)}, f"    Modelo com todas as colunas prevendo a nota: acerta {acc:.1%}, chutar a nota mais comum acerta {acaso:.1%}")

    print("  O texto da descrição prevê o tipo do ticket?")
    texto = d["Ticket Description"].str.replace(r"\{[^}]+\}", " ", regex=True)
    vet = TfidfVectorizer(min_df=2, ngram_range=(1, 2))
    acc = cross_val_score(LogisticRegression(max_iter=2000), vet.fit_transform(texto), d["Ticket Type"], cv=5).mean()
    registra("d1_texto_preve_tipo", round(acc, 3), f"    Acerto: {acc:.1%} (acaso com 5 tipos: 20%)")
    return d


def dataset2(d1):
    print("\n=== DATASET 2 · tickets de TI ===")
    d = pd.read_csv(D2)
    registra("d2_registros", len(d), f"Registros: {len(d):,}")
    classes = d["Topic_group"].value_counts()
    registra("d2_classes", classes.to_dict(), "Equipes: " + ", ".join(f"{k} {v:,} ({v/len(d):.1%})" for k, v in classes.items()))
    dup = d["Document"].duplicated().sum()
    dup_conflito = d.groupby("Document")["Topic_group"].nunique().gt(1).sum()
    registra("d2_duplicados", int(dup), f"Textos repetidos: {dup:,}, e {dup_conflito:,} textos aparecem com equipes diferentes")
    palavras = d["Document"].str.split().str.len()
    registra("d2_palavras", {"mediana": int(palavras.median())}, f"Tamanho do texto: mediana de {int(palavras.median())} palavras")

    print("  Classificador simples (TF-IDF + regressão logística), 20% separado pra teste:")
    tr, te = train_test_split(d, test_size=0.2, stratify=d["Topic_group"], random_state=SEMENTE)
    vet = TfidfVectorizer(sublinear_tf=True, min_df=2, ngram_range=(1, 2))
    Xtr, Xte = vet.fit_transform(tr["Document"]), vet.transform(te["Document"])
    mod = LogisticRegression(max_iter=3000, C=5).fit(Xtr, tr["Topic_group"])
    pred = mod.predict(Xte)
    acc, f1 = accuracy_score(te["Topic_group"], pred), f1_score(te["Topic_group"], pred, average="macro")
    registra("d2_classificador", {"acerto": round(acc, 4), "f1_macro": round(f1, 4)}, f"    Acerto {acc:.1%}, F1 macro {f1:.1%}")
    prob = mod.predict_proba(Xte)
    conf = prob.max(axis=1)
    top2 = np.mean([y in mod.classes_[np.argsort(p)[-2:]] for y, p in zip(te["Topic_group"], prob)])
    registra("d2_top2", round(top2, 4), f"    Acerto se o atendente escolher entre as 2 sugestões: {top2:.1%}")
    print("  Trava de confiança (só vai sozinho se o modelo tiver certeza acima do limite):")
    trava = {}
    for lim in [0.5, 0.6, 0.7, 0.8, 0.9]:
        m = conf >= lim
        trava[lim] = {"cobertura": round(m.mean(), 3), "acerto": round(accuracy_score(te["Topic_group"][m], pred[m]), 3)}
        print(f"    limite {lim:.1f}: vai sozinho {m.mean():.1%} dos tickets, acertando {trava[lim]['acerto']:.1%}")
    saida["d2_trava"] = trava

    print("  O mesmo modelo lendo os tickets do Dataset 1:")
    texto_d1 = d1["Ticket Description"].str.replace(r"\{[^}]+\}", " ", regex=True).str.lower()
    destino = pd.Series(mod.predict(vet.transform(texto_d1))).value_counts(normalize=True)
    registra("d2_modelo_no_d1", destino.round(3).to_dict(), "    Pra onde mandaria: " + ", ".join(f"{k} {v:.0%}" for k, v in destino.items()))


if __name__ == "__main__":
    d1 = dataset1()
    dataset2(d1)
    destino = Path(__file__).with_name("verificacao.json")
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1, default=str))
    print(f"\nResultados salvos em {destino.name}")
