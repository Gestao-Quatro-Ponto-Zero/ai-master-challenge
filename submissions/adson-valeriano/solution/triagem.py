"""
Núcleo da triagem: classificador de tickets + regras de passagem para humano + busca de tickets similares.

Decisões de projeto (ver README):
- Classificador simples (TF-IDF + regressão logística): rápido, barato, explicável. Serve de base.
- A IA só decide sozinha quando a confiança passa do LIMIAR_CONFIANCA.
- Alguns casos SEMPRE vão para humano, independente da confiança (dinheiro, urgência, acesso privilegiado).
"""
from pathlib import Path
import re

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parents[3]          # raiz do repositório
DATASET_TI = RAIZ / "datasets" / "all_tickets_processed_improved_v3.csv"
MODELO_PATH = Path(__file__).resolve().parent / "modelo_triagem.joblib"

LIMIAR_CONFIANCA = 0.70  # decisão de negócio: 72% de cobertura com ~95,6% de acerto no teste

# Categorias em que a IA nunca encaminha sozinha
CATEGORIAS_SEMPRE_HUMANO = {"Administrative rights"}  # pior precisão (~77%) e tema de segurança

# Palavras que indicam dinheiro, urgência ou risco -> sempre humano
GATILHOS_HUMANO = {
    "dinheiro / retenção": [
        "refund", "reembolso", "estorno", "charge", "charged", "cobran", "billing", "invoice",
        "fatura", "payment", "pagamento", "cancel", "cancelar", "cancelamento",
    ],
    "urgência / incidente": [
        "urgent", "urgente", "critical", "crítico", "critico", "outage", "down", "fora do ar",
        "not working for everyone", "parou tudo",
    ],
    "segurança / dados": [
        "hack", "hacked", "breach", "vazamento", "phishing", "virus", "vírus", "fraud", "fraude",
        "password leaked", "senha vazou",
    ],
}


def normalizar(texto: str) -> str:
    """Deixa o texto no mesmo formato do dataset de treino (minúsculo, sem números e pontuação)."""
    texto = str(texto).lower()
    texto = re.sub(r"[^a-zà-ú\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(DATASET_TI).dropna()
    df["texto"] = df["Document"].map(normalizar)
    return df


def treinar(salvar: bool = True, seed: int = 42):
    """Treina com 80% dos dados e guarda os 20% de teste para avaliação honesta."""
    df = carregar_dados()
    treino, teste = train_test_split(df, test_size=0.2, random_state=seed, stratify=df["Topic_group"])

    vetorizador = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    X_treino = vetorizador.fit_transform(treino["texto"])
    modelo = LogisticRegression(max_iter=2000, C=5, class_weight="balanced")
    modelo.fit(X_treino, treino["Topic_group"])

    pacote = {
        "vetorizador": vetorizador,
        "modelo": modelo,
        "base_textos": treino["texto"].tolist(),
        "base_originais": treino["Document"].tolist(),
        "base_categorias": treino["Topic_group"].tolist(),
        "matriz_base": X_treino,
    }
    if salvar:
        joblib.dump(pacote, MODELO_PATH)
    return pacote, teste


def carregar_modelo():
    if not MODELO_PATH.exists():
        pacote, _ = treinar(salvar=True)
        return pacote
    return joblib.load(MODELO_PATH)


def gatilhos_encontrados(texto: str) -> list[str]:
    t = str(texto).lower()
    return [motivo for motivo, palavras in GATILHOS_HUMANO.items() if any(p in t for p in palavras)]


def triar(texto: str, prioridade: str | None = None, pacote=None, k_similares: int = 3) -> dict:
    """Recebe o texto de um ticket e devolve categoria, confiança, decisão e tickets parecidos."""
    pacote = pacote or carregar_modelo()
    vet, modelo = pacote["vetorizador"], pacote["modelo"]

    x = vet.transform([normalizar(texto)])
    probs = modelo.predict_proba(x)[0]
    ordem = probs.argsort()[::-1]
    categoria = modelo.classes_[ordem[0]]
    confianca = float(probs[ordem[0]])
    alternativas = [(modelo.classes_[i], float(probs[i])) for i in ordem[1:3]]

    motivos = []
    if prioridade and prioridade.lower() in {"critical", "crítica", "critica"}:
        motivos.append("prioridade crítica")
    motivos += gatilhos_encontrados(texto)
    if categoria in CATEGORIAS_SEMPRE_HUMANO:
        motivos.append(f"categoria sensível ({categoria})")
    if confianca < LIMIAR_CONFIANCA:
        motivos.append(f"confiança baixa ({confianca:.0%} < {LIMIAR_CONFIANCA:.0%})")

    decisao = "HUMANO" if motivos else "AUTOMÁTICO"

    # Recuperação de tickets parecidos (a parte "R" de um RAG): dá contexto ao atendente
    sims = cosine_similarity(x, pacote["matriz_base"])[0]
    top = sims.argsort()[::-1][:k_similares]
    similares = [
        {"texto": pacote["base_originais"][i][:220], "categoria": pacote["base_categorias"][i],
         "similaridade": float(sims[i])}
        for i in top
    ]

    return {
        "categoria": categoria,
        "confianca": confianca,
        "alternativas": alternativas,
        "decisao": decisao,
        "motivos_humano": motivos,
        "fila_destino": categoria if decisao == "AUTOMÁTICO" else f"Triagem humana (sugestão: {categoria})",
        "similares": similares,
    }


if __name__ == "__main__":
    exemplo = "hello my laptop screen is broken and keyboard not working please send replacement thanks"
    r = triar(exemplo)
    print(r["categoria"], f"{r['confianca']:.0%}", r["decisao"], r["motivos_humano"])
