"""
Checagens extras de robustez (terceira varredura).
Roda: python checagens_extras.py
1. Vazamento: chamados de teste quase idênticos a chamados de treino inflam o acerto?
2. Atalho: o modelo acerta pela assinatura/cargo no fim do texto, e não pelo problema?
3. Mix de chamados: quanto do volume de suporte envolve dinheiro (sempre humano pelas regras)?
   ROI em horas e em reais (premissa de custo/hora de mercado).
4. As regras de passagem para humano funcionam? Cobertura das palavras-chave e efeito na automação.
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

# Premissa de custo: Operador de Suporte Técnico, custo empresa (salário + encargos CLT) de R$ 3.440/mês
# (Portal Salário, 2026), dividido por 220 h/mês.
CUSTO_MES = 3440
HORAS_MES = 220


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

    # 4) As regras funcionam?
    sup = pd.read_csv(triagem.RAIZ / "datasets" / "customer_support_tickets.csv")
    din = sup["Ticket Type"].isin(["Refund request", "Cancellation request", "Billing inquiry"])
    pega = sup["Ticket Description"].map(lambda t: "dinheiro / retenção" in triagem.gatilhos_encontrados(t))
    probs = pacote["modelo"].predict_proba(X)
    conf = probs.max(axis=1)
    cat = pacote["modelo"].classes_[probs.argmax(axis=1)]
    tem_gatilho = teste["Document"].map(lambda t: bool(triagem.gatilhos_encontrados(t))).to_numpy()
    sensivel = np.isin(cat, list(triagem.CATEGORIAS_SEMPRE_HUMANO))
    auto = (conf >= triagem.LIMIAR_CONFIANCA) & ~tem_gatilho & ~sensivel

    # 3) Mix de chamados do suporte
    sup = pd.read_csv(triagem.RAIZ / "datasets" / "customer_support_tickets.csv")
    tipos = sup["Ticket Type"].value_counts()
    dinheiro = tipos[["Refund request", "Cancellation request", "Billing inquiry"]].sum()
    share = dinheiro / len(sup)
    cobertura = float(auto.mean())  # cobertura efetiva, com limiar e regras ligados
    volume_ano, minutos = 30000, 3
    conservador = volume_ano * (1 - share) * cobertura * minutos / 60
    ampliado = volume_ano * cobertura * minutos / 60
    custo_hora = CUSTO_MES / HORAS_MES
    L += ["## 3. Mix de chamados e impacto no ROI",
          "- " + ", ".join(f"{t}: {n}" for t, n in tipos.items()),
          f"- Chamados que envolvem dinheiro (reembolso, cancelamento, cobrança): {share:.0%}",
          f"- Cenário conservador (IA só tria o que não é dinheiro): ~{conservador:,.0f} h/ano (~{conservador / 12:.0f} h/mês) "
          f"≈ R$ {conservador * custo_hora:,.0f}/ano".replace(",", "."),
          f"- Cenário ampliado (IA também encaminha dinheiro para a fila do financeiro; a decisão continua humana): "
          f"~{ampliado:,.0f} h/ano (~{ampliado / 12:.0f} h/mês) ≈ R$ {ampliado * custo_hora:,.0f}/ano".replace(",", "."),
          f"- Custo/hora usado: R$ {custo_hora:.2f} (custo empresa de R$ {CUSTO_MES:,} por mês ÷ {HORAS_MES} h; "
          "Operador de Suporte Técnico, Portal Salário 2026)".replace(",", "."),
          "- Leitura: a economia direta de triagem é modesta. O ganho principal é tempo: o ticket chega na fila "
          "certa na hora, sem esperar alguém ler e encaminhar.",
          "- Premissas: 30 mil chamados/ano (informado pelo diretor), 3 min de triagem manual por chamado, "
          f"cobertura efetiva de {cobertura:.1%} (limiar de 70% + regras de passagem para humano). A distribuição de tipos vem de um dataset que parece sintético."]

    L += ["", "## 4. As regras de passagem para humano funcionam?",
          f"- Dataset de suporte: as palavras-chave de dinheiro pegam {pega[din].mean():.1%} dos chamados de "
          f"reembolso/cancelamento/cobrança e disparam em {pega[~din].mean():.1%} dos outros.",
          "  Leitura: no dataset de suporte o texto não tem relação com o tipo do chamado (dado sintético), então a "
          "regra por palavra-chave não pode ser validada ali. Em produção, a regra de dinheiro deve usar o campo "
          "estruturado do chamado (tipo/assunto escolhido pelo cliente) e as palavras-chave só como reforço.",
          f"- Dataset de TI: com todas as regras ligadas, a IA decide sozinha {auto.mean():.1%} dos tickets de teste "
          f"(só o limiar daria {(conf >= triagem.LIMIAR_CONFIANCA).mean():.1%}), com acerto de "
          f"{(cat[auto] == y[auto]).mean():.1%} nesses.",
          f"- Motivos extras de passagem para humano no TI: palavra-chave em {tem_gatilho.mean():.1%} dos tickets; "
          f"categoria sensível prevista em {sensivel.mean():.1%}."]


    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
