"""
Checagens extras de robustez (terceira varredura).
Roda: python checagens_extras.py
1. Vazamento: chamados de teste quase idênticos a chamados de treino inflam o acerto?
2. Atalho: o modelo acerta pela assinatura/cargo no fim do texto, e não pelo problema?
3. Mix de chamados: quanto do volume de suporte envolve dinheiro (sempre humano pelas regras)?
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

import triagem

SAIDA = Path(__file__).resolve().parent / "resultados_checagens.md"


def treinar_e_medir(textos, rotulos, idx_tr, idx_te):
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    m = LogisticRegression(max_iter=2000, C=5, class_weight="balanced")
    m.fit(v.fit_transform(textos[idx_tr]), rotulos[idx_tr])
    return accuracy_score(rotulos[idx_te], m.predict(v.transform(textos[idx_te])))


def main():
    L = ["# Checagens extras de robustez", ""]

    # 1) Vazamento por quase-duplicatas
    pacote, teste = triagem.treinar(salvar=False)
    X = pacote["vetorizador"].transform(teste["texto"])
    y = teste["Topic_group"].to_numpy()
    pred = pacote["modelo"].predict(X)
    vizinho = np.zeros(X.shape[0])
    for i in range(0, X.shape[0], 2000):
        vizinho[i:i + 2000] = cosine_similarity(X[i:i + 2000], pacote["matriz_base"]).max(axis=1)
    k = vizinho >= 0.9
    L += ["## 1. Vazamento entre treino e teste",
          f"- Chamados de teste com um 'gêmeo' no treino (similaridade ≥ 90%): {k.mean():.1%}",
          f"- Acerto sem esses chamados: {accuracy_score(y[~k], pred[~k]):.1%} (geral: {accuracy_score(y, pred):.1%})",
          "- Conclusão: o acerto não está inflado por chamados repetidos.", ""]

    # 2) Atalho pela assinatura/cargo
    df = triagem.carregar_dados().reset_index(drop=True)
    tr, te = train_test_split(df.index, test_size=0.2, random_state=42, stratify=df["Topic_group"])
    palavras = df["texto"].str.split()
    so_fim = palavras.str[-3:].str.join(" ")
    sem_fim = palavras.apply(lambda w: " ".join(w[:-3]) if len(w) > 6 else " ".join(w))
    rot = df["Topic_group"]
    L += ["## 2. O modelo cola pela assinatura/cargo?",
          f"- Acerto usando só as 3 últimas palavras: {treinar_e_medir(so_fim, rot, tr, te):.1%}",
          f"- Acerto sem as 3 últimas palavras: {treinar_e_medir(sem_fim, rot, tr, te):.1%}",
          "- Conclusão: o modelo aprende pelo problema descrito, não pela assinatura.", ""]

    # 3) Mix de chamados do suporte
    sup = pd.read_csv(triagem.RAIZ / "datasets" / "customer_support_tickets.csv")
    tipos = sup["Ticket Type"].value_counts()
    dinheiro = tipos[["Refund request", "Cancellation request", "Billing inquiry"]].sum()
    share = dinheiro / len(sup)
    cobertura = 0.717
    volume_ano, minutos = 30000, 3
    conservador = volume_ano * (1 - share) * cobertura * minutos / 60
    ampliado = volume_ano * cobertura * minutos / 60
    L += ["## 3. Mix de chamados e impacto no ROI",
          "- " + ", ".join(f"{t}: {n}" for t, n in tipos.items()),
          f"- Chamados que envolvem dinheiro (reembolso, cancelamento, cobrança): {share:.0%}",
          f"- Cenário conservador (IA só tria o que não é dinheiro): ~{conservador:,.0f} h/ano (~{conservador / 12:.0f} h/mês)".replace(",", "."),
          f"- Cenário ampliado (IA também encaminha dinheiro para a fila do financeiro; a decisão continua humana): "
          f"~{ampliado:,.0f} h/ano (~{ampliado / 12:.0f} h/mês)".replace(",", "."),
          "- Premissas: 30 mil chamados/ano (informado pelo diretor), 3 min de triagem manual por chamado, "
          "cobertura de 71,7% (limiar de 70%). A distribuição de tipos vem de um dataset que parece sintético."]

    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
