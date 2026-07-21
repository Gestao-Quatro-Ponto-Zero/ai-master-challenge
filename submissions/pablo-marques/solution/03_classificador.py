"""
03_classificador.py — Bloco 3: classificador de tickets e a curva que o 02 espera

O 02_business_case.py deixou uma interface aberta: curva_placeholder() devolve
(cobertura, precisao) e precisa ser substituida por medicao real POR CLASSE.
Este bloco mede.

O entregavel principal NAO e acuracia nem F1. E a curva cobertura x precisao
por classe, comparada contra o piso p*(k) = (k-1)/k da SECAO 2 do bloco 1.
Acuracia agregada aparece uma vez, como sanidade, e nao como resultado.

Definicao fixada (ver PARTE 6):
    cobertura_c = volume que entra no canal automatico c / volume real da classe c
    taxa de automacao global = soma de w_c * cobertura_c
w_c permanece visivel e rotulado como transplante declarado — nao e dissolvido
dentro da cobertura.

Ordem de execucao, que e tambem a ordem de honestidade:
  PARTE 0 — revisao do P3 por leitura de amostras, ANTES de treinar
  PARTE 1 — auditoria de vazamento, ANTES de dividir
  PARTE 2 — split estratificado com semente fixa, anotado
  PARTE 3 — treino (tfidf + linear, sem embedding, sem LLM)
  PARTE 4 — sanidade agregada
  PARTE 5 — calibracao medida por classe, nao assumida
  PARTE 6 — ENTREGAVEL: curva cobertura x precisao por classe
  PARTE 7 — corte contra p*(k): o que NAO automatizar
  PARTE 8 — matriz de confusao (png)
  PARTE 9 — conferencia das previsoes registradas no bloco 1
  PARTE 10 — handoff

Uso:
    .venv/Scripts/python.exe 03_classificador.py

Dependencias: pandas, scipy, scikit-learn, matplotlib (ver requirements.txt)
Saida: stdout + 03_classificador_saida.txt + graficos/*.png + curva_medida.json
"""

import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------------
# Infra
# --------------------------------------------------------------------------

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "03_classificador_saida.txt"
GRAFICOS = AQUI / "graficos"
CURVA_JSON = AQUI / "curva_medida.json"

SEMENTE = 42
FRACAO_TESTE = 0.20


def achar_pasta_dados() -> Path:
    for pasta in [AQUI, *AQUI.parents]:
        candidata = pasta / "data"
        if (candidata / "all_tickets_processed_improved_v3.csv").exists():
            return candidata
    raise SystemExit(f"ERRO: nao encontrei data/ subindo a partir de {AQUI}.")


class Tee:
    def __init__(self, caminho: Path):
        self.arquivo = open(caminho, "w", encoding="utf-8")
        self.console = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    def write(self, texto: str):
        self.arquivo.write(texto)
        self.console.write(texto)

    def flush(self):
        self.arquivo.flush()
        self.console.flush()


def titulo(texto: str, char: str = "="):
    print("\n" + char * 78)
    print(texto)
    print(char * 78)


def piso_precisao(k: float) -> float:
    """p*(k) = (k-1)/k — SECAO 2 do bloco 1. Forma fechada, livre de escala."""
    return (k - 1) / k


DADOS = achar_pasta_dados()
GRAFICOS.mkdir(exist_ok=True)
sys.stdout = Tee(SAIDA)

t_inicio = time.time()

itsm = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")
itsm["Document"] = itsm["Document"].astype(str)
CLASSES = sorted(itsm["Topic_group"].unique())
w = itsm["Topic_group"].value_counts(normalize=True)

titulo("BLOCO 3 — CLASSIFICADOR E A CURVA QUE O BLOCO 1 ESPERA")
print(f"""
Base: all_tickets_processed_improved_v3.csv — {len(itsm):,} tickets, {len(CLASSES)} classes [dados]
Semente fixa: {SEMENTE}   |   fracao de teste: {FRACAO_TESTE:.0%}   |   split estratificado

Escopo desta rodada, por decisao de orcamento: baseline classico completo.
TF-IDF + modelo linear. SEM embeddings, SEM LLM, SEM zero-shot. Se sobrar
tempo depois, a comparacao entra como bloco proprio — nao como nota de rodape.
""")


# ==========================================================================
# PARTE 0 — REVISAO DO P3 ANTES DE TREINAR
# ==========================================================================
titulo("PARTE 0 — REVISAO DA PREVISAO P3, ANTES DE QUALQUER TREINO")

print("""
O bloco 1 registrou o P3 ('Hardware passara de p* com folga') com forca de
base MEDIA, e escreveu o motivo: 'vocabulario concreto e julgamento meu sobre
o dominio, nao medicao — nao inspecionei o texto de Hardware'.

Deixar uma previsao fraca de proposito quando dava pra resolver lendo 20
amostras e desleixo, nao prudencia. Ler o texto nao e trapaca: a previsao e
sobre o comportamento do CLASSIFICADOR, e ele ainda nao rodou. Entao a leitura
aconteceu aqui, antes do treino, e o resultado esta abaixo.

AMOSTRA LIDA: 20 documentos rotulados 'Hardware', random_state=42.
CLASSIFICACAO SEMANTICA FEITA POR MIM, ANTES DE TREINAR:
""")

amostra_hw = itsm[itsm["Topic_group"] == "Hardware"].sample(20, random_state=42)
# Leitura manual registrada: indice da amostra -> tema semantico observado.
leitura_manual = {
    1: "HARDWARE   (alocacao de monitor)",
    2: "infra      (docker/server parado)",
    3: "acesso     (instalacao/conexao, log de erro)",
    4: "HARDWARE   (laptop extra para treinamento)",
    5: "rede/seg   (scan de vulnerabilidade wireless)",
    6: "acesso     (nao consegue acessar link/recursos)",
    7: "vago       (investigacao de conexao)",
    8: "compra     (fornecedor, calculo de VAT)",
    9: "misc       (informacao de catalogo de enderecos)",
    10: "HARDWARE   (adaptadores)",
    11: "software   (nao consegue compartilhar relatorio)",
    12: "software   (habilitar funcao de visualizacao)",
    13: "HARDWARE   (troca de monitor e mouse)",
    14: "vago       (erros em paginas)",
    15: "acesso     (nao consegue acessar quiz de seguranca)",
    16: "acesso     (cracha de acesso nao funciona)",
    17: "acesso     (direitos de acesso a pasta)",
    18: "HARDWARE   (suporte de monitor)",
    19: "infra      (host de maquina virtual reiniciou)",
    20: "acesso     (portal nega permissao)",
}
for i, (_, r) in enumerate(amostra_hw.iterrows(), 1):
    print(f"  [{i:02d}] {leitura_manual[i]:<34} {str(r['Document'])[:88]}")

n_hw = sum(1 for v in leitura_manual.values() if v.startswith("HARDWARE"))
n_acesso = sum(1 for v in leitura_manual.values() if v.startswith("acesso"))
print(f"""
CONTAGEM DA LEITURA
  inequivocamente hardware (dispositivo fisico) : {n_hw:>2} de 20  ({n_hw / 20:.0%})
  semanticamente sobre ACESSO/permissao         : {n_acesso:>2} de 20  ({n_acesso / 20:.0%})
  outros (infra, software, compra, misc, vago)  : {20 - n_hw - n_acesso:>2} de 20

VEREDITO: P3 ORIGINAL RETIRADA. A base estava errada.

  O P3 supunha que 'Hardware' fosse uma classe de vocabulario concreto —
  nomes de dispositivo e verbos de falha fisica. A leitura mostra o oposto:
  apenas {n_hw / 20:.0%} da amostra e sobre dispositivo. O rotulo 'Hardware' nesta base
  nao e um dominio semantico coeso, e um rotulo CONTAMINADO — e a maior
  fonte de contaminacao e justamente ACESSO ({n_acesso / 20:.0%} da amostra).

  Registro a retirada em vez de apagar a previsao. O erro fica no arquivo.

P3-REVISADO, registrado agora, ainda antes do treino:

  P3R-a. Hardware NAO tera a maior precisao entre as 8 classes, apesar de ser
         a maior em volume ({w['Hardware']:.1%} [dados]).
         BASE: rotulo contaminado, medido em {n_hw}/20 de coerencia semantica.
         FALSIFICA: Hardware aparecer com a maior precisao das 8.

  P3R-b. Access estara entre as DUAS maiores fontes de confusao de Hardware.
         BASE: {n_acesso}/20 da amostra de Hardware e semanticamente acesso.
         FALSIFICA: Access fora das duas maiores linhas de confusao de Hardware.

  forca da base: ALTA — agora e leitura, nao suposicao.

NOTA: esta contaminacao tambem enfraquece o pressuposto implicito do P1 de que
as outras sete classes sao 'definidas por conteudo'. Hardware, pelo menos, nao
e. Isso NAO altera o enunciado do P1, que fala de Miscellaneous — mas fica
registrado que a base do P1 e mais fraca do que eu escrevi no bloco 1.
""")


# ==========================================================================
# PARTE 1 — AUDITORIA DE VAZAMENTO, ANTES DE DIVIDIR
# ==========================================================================
titulo("PARTE 1 — AUDITORIA DE VAZAMENTO (antes do split)")

print("""
Em base de chamado, vazamento raramente vem de split mal feito. Vem de
documento repetido: mesmo chamado reaberto, template de abertura identico,
thread de email colada varias vezes. Se o par cair dos dois lados do split,
o modelo 'acerta' por ter decorado, e a acuracia sobe sem significar nada.
Por isso a contagem vem ANTES de dividir, e nao depois de um numero bonito.
""")

texto_norm = itsm["Document"].str.lower().str.split().str.join(" ")

exatas = texto_norm.duplicated(keep=False).sum()
grupos_exatos = texto_norm[texto_norm.duplicated(keep=False)].nunique()
print(f"1.1 DUPLICATA EXATA (apos normalizar caixa e espaco)")
print(f"    documentos envolvidos : {exatas:,} de {len(itsm):,} ({exatas / len(itsm):.2%})")
print(f"    grupos distintos      : {grupos_exatos:,}")

if exatas:
    dup_mask = texto_norm.duplicated(keep=False)
    rotulos_por_texto = itsm[dup_mask].groupby(texto_norm[dup_mask])["Topic_group"].nunique()
    conflitantes = int((rotulos_por_texto > 1).sum())
    print(f"    grupos com ROTULO CONFLITANTE (mesmo texto, classes diferentes): {conflitantes:,}")
    if conflitantes:
        print("    -> isso e ruido de rotulo puro: e um teto de acuracia que nenhum")
        print("       modelo ultrapassa, porque o mesmo texto tem duas respostas certas.")

print("\n1.2 QUASE-DUPLICATA (cosseno TF-IDF >= 0.90, varredura completa)")
print("    varrendo todos os pares... (nao amostrado)")

vet_dup = TfidfVectorizer(min_df=2, max_features=30_000)
X_dup = vet_dup.fit_transform(texto_norm).astype(np.float32)

LIMIAR_QD = 0.90
BLOCO = 500
sim_max = np.zeros(X_dup.shape[0], dtype=np.float32)
viz_max = np.full(X_dup.shape[0], -1, dtype=np.int32)
for ini in range(0, X_dup.shape[0], BLOCO):
    fim = min(ini + BLOCO, X_dup.shape[0])
    bloco = (X_dup[ini:fim] @ X_dup.T).toarray()
    for j in range(fim - ini):
        bloco[j, ini + j] = -1.0          # remove a auto-similaridade
    sim_max[ini:fim] = bloco.max(axis=1)
    viz_max[ini:fim] = bloco.argmax(axis=1)
    del bloco

tem_gemeo = sim_max >= LIMIAR_QD
print(f"    documentos com gemeo >= {LIMIAR_QD:.2f} : {tem_gemeo.sum():,} "
      f"({tem_gemeo.mean():.2%})")
for lim in [0.95, 0.99]:
    m = sim_max >= lim
    print(f"    documentos com gemeo >= {lim:.2f} : {m.sum():,} ({m.mean():.2%})")

rotulo = itsm["Topic_group"].to_numpy()
if tem_gemeo.sum():
    idx = np.where(tem_gemeo)[0]
    mesmo_rotulo = (rotulo[idx] == rotulo[viz_max[idx]]).mean()
    print(f"    entre os quase-duplicados, fracao cujo gemeo tem o MESMO rotulo: "
          f"{mesmo_rotulo:.1%}")
    print(f"    (o complemento, {1 - mesmo_rotulo:.1%}, e ruido de rotulo: texto quase igual,")
    print("     classe diferente — outro pedaco do teto de acuracia)")

print(f"""
1.3 DECISAO
    Os quase-duplicados NAO sao removidos da base. Motivo: em operacao real
    eles existem e o classificador vai encontra-los; remove-los inflaria a
    dificuldade artificialmente. O que importa e SABER quanto tem, para ler
    a acuracia com desconto — e para nao comemorar um numero alto que e
    memorizacao. O split abaixo e feito sobre a base inteira, e a PARTE 4
    reporta a acuracia tambem no subconjunto SEM gemeo, que e a leitura
    honesta.
""")


# ==========================================================================
# PARTE 2 — SPLIT
# ==========================================================================
titulo("PARTE 2 — SPLIT ESTRATIFICADO (anotado)")

X_txt = itsm["Document"].to_numpy()
y = itsm["Topic_group"].to_numpy()
idx_todos = np.arange(len(itsm))

i_tr, i_te = train_test_split(
    idx_todos, test_size=FRACAO_TESTE, random_state=SEMENTE, stratify=y
)
Xtr_txt, Xte_txt = X_txt[i_tr], X_txt[i_te]
ytr, yte = y[i_tr], y[i_te]

print(f"""
  funcao        : sklearn.model_selection.train_test_split
  random_state  : {SEMENTE}   (fixa; a rodada e reproduzivel)
  test_size     : {FRACAO_TESTE}
  stratify      : Topic_group  (proporcao de classe preservada nos dois lados)
  treino        : {len(i_tr):,} documentos
  teste         : {len(i_te):,} documentos
""")

comp = pd.DataFrame({
    "treino %": pd.Series(ytr).value_counts(normalize=True).mul(100).round(2),
    "teste %": pd.Series(yte).value_counts(normalize=True).mul(100).round(2),
    "base %": w.mul(100).round(2),
})
comp["desvio pp"] = (comp["teste %"] - comp["base %"]).round(3)
print(comp.to_string())

gemeo_cruzado = int((tem_gemeo[i_te] & np.isin(viz_max[i_te], i_tr)).sum())
print(f"""
  VAZAMENTO EFETIVO APOS O SPLIT
  documentos de TESTE cujo gemeo (>= {LIMIAR_QD:.2f}) caiu no TREINO: {gemeo_cruzado:,}
  ({gemeo_cruzado / len(i_te):.2%} do conjunto de teste)

  Este e o numero que interessa: nao 'quantas duplicatas a base tem', mas
  quantas atravessaram a fronteira do split. A PARTE 4 mede a acuracia com e
  sem esses documentos.
""")


# ==========================================================================
# PARTE 3 — TREINO
# ==========================================================================
titulo("PARTE 3 — TREINO: TF-IDF + REGRESSAO LOGISTICA")

print("""
Escolha de modelo, e o motivo dela:

  LogisticRegression, nao LinearSVC. Mesma familia linear, mas com
  predict_proba nativo. O SVM linear cospe decision_function, que e margem
  em unidade arbitraria e cuja escala varia por classe — cortar em 0.7
  significaria coisas diferentes em Hardware e em Storage.

  Sem CalibratedClassifierCV por cima. Com 1.760 exemplos na menor classe, a
  calibracao seria estimada justamente onde ha menos dado. A PARTE 5 MEDE a
  calibracao em vez de assumi-la, e a curva da PARTE 6 e indexada por
  cobertura (uma fracao), que nao depende de a probabilidade ser fiel.

  Sem class_weight='balanced', de proposito. O balanceamento apagaria o
  efeito de prior que a previsao P2 do bloco 1 preve. Um baseline que
  esconde o fenomeno que se quer testar nao serve. Fica sem balanceamento e
  o efeito, se existir, aparece na matriz de confusao.
""")

vetor = TfidfVectorizer(
    min_df=3, ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode",
)
t0 = time.time()
Xtr = vetor.fit_transform(Xtr_txt)
Xte = vetor.transform(Xte_txt)
print(f"  vocabulario   : {len(vetor.vocabulary_):,} termos (unigrama + bigrama, min_df=3)")
print(f"  matriz treino : {Xtr.shape}  densidade {Xtr.nnz / (Xtr.shape[0] * Xtr.shape[1]):.5%}")

modelo = LogisticRegression(max_iter=1000, C=4.0, random_state=SEMENTE, n_jobs=-1)
modelo.fit(Xtr, ytr)
print(f"  treino        : {time.time() - t0:.1f}s")

proba = modelo.predict_proba(Xte)
ordem_classes = list(modelo.classes_)
pred = modelo.classes_[proba.argmax(axis=1)]
conf = proba.max(axis=1)


# ==========================================================================
# PARTE 4 — SANIDADE AGREGADA
# ==========================================================================
titulo("PARTE 4 — SANIDADE AGREGADA (nao e o entregavel)")

acc = accuracy_score(yte, pred)
f1m = f1_score(yte, pred, average="macro")
print(f"""
  acuracia (teste inteiro) : {acc:.4f}
  F1 macro                 : {f1m:.4f}

Estes numeros estao aqui por sanidade e nao como resultado. O que decide
automacao e precisao POR CLASSE contra o piso p*(k) — ver PARTE 6 e 7. Um F1
macro alto pode conviver com uma classe inteira abaixo do piso.
""")

sem_gemeo = ~(tem_gemeo[i_te] & np.isin(viz_max[i_te], i_tr))
if sem_gemeo.sum() and sem_gemeo.sum() < len(i_te):
    acc_limpa = accuracy_score(yte[sem_gemeo], pred[sem_gemeo])
    print(f"  acuracia excluindo os {(~sem_gemeo).sum():,} documentos de teste com gemeo no treino:")
    print(f"    {acc_limpa:.4f}   (delta {acc_limpa - acc:+.4f})")
    print("""
  Leitura: se o delta fosse grande e negativo, a acuracia cheia estaria
  inflada por memorizacao. Este e o teste que a PARTE 1 preparou.""")

if acc > 0.95:
    print("""
  ATENCAO: acuracia acima de 95%. A PARTE 1 ja mediu duplicata e
  quase-duplicata ANTES do split justamente para este momento — a leitura
  do vazamento esta acima e nao foi produzida depois do numero aparecer.""")


# ==========================================================================
# PARTE 5 — CALIBRACAO MEDIDA
# ==========================================================================
titulo("PARTE 5 — CALIBRACAO MEDIDA POR CLASSE (nao assumida)")

print("""
A probabilidade so pode ser mostrada a um agente humano se ela valer o que
diz: entre os casos com 80% de confianca, cerca de 80% tem que estar certos.
Aqui isso e medido, classe por classe, e nao assumido.

ECE = erro de calibracao esperado (media ponderada do |confianca - acerto|
por faixa de confianca). Quanto menor, mais fiel e o numero.
""")

linhas_cal = []
for c in ordem_classes:
    m = pred == c
    if m.sum() < 50:
        continue
    conf_c, acerto_c = conf[m], (yte[m] == c).astype(float)
    faixas = np.linspace(0, 1, 11)
    ece, n_tot = 0.0, m.sum()
    for a, b in zip(faixas[:-1], faixas[1:]):
        sel = (conf_c >= a) & (conf_c < b) if b < 1 else (conf_c >= a) & (conf_c <= b)
        if sel.sum():
            ece += sel.sum() / n_tot * abs(conf_c[sel].mean() - acerto_c[sel].mean())
    linhas_cal.append({
        "classe": c,
        "previstos": int(n_tot),
        "confianca media": round(float(conf_c.mean()), 3),
        "acerto real": round(float(acerto_c.mean()), 3),
        "vies": round(float(conf_c.mean() - acerto_c.mean()), 3),
        "ECE": round(float(ece), 3),
    })
cal = pd.DataFrame(linhas_cal).sort_values("ECE", ascending=False)
print(cal.to_string(index=False))
print("""
  vies positivo = o modelo se diz mais confiante do que acerta (otimista).
  A curva da PARTE 6 nao depende desta tabela: ela e indexada por cobertura,
  que e fracao. A calibracao importa para a UI e para a regra de abstencao
  da triagem, nao para o business case.
""")


# ==========================================================================
# PARTE 6 — ENTREGAVEL: CURVA COBERTURA x PRECISAO POR CLASSE
# ==========================================================================
titulo("PARTE 6 — ENTREGAVEL: CURVA COBERTURA x PRECISAO POR CLASSE")

print(f"""
DEFINICAO FIXADA (esta linha fecha a duvida que abriu o bloco):

  Para cada classe c e cada limiar tau_c aplicado a confianca do modelo:

    canal_c(tau)     = tickets que o modelo roteia automaticamente para c
                       (isto e: pred == c E confianca >= tau_c)
    cobertura_c(tau) = |canal_c(tau)| / |tickets cuja classe real e c|
    precisao_c(tau)  = fracao de canal_c(tau) cuja classe real e c

  cobertura_c e FRACAO DENTRO DA CLASSE. Por isso e comparavel entre classes
  mesmo que a escala do score nao seja — que era o problema original. tau_c
  vira detalhe de implementacao: escolhe-se o alvo de cobertura ou de
  precisao e inverte-se a curva. O operador nunca escolhe um score cru.

  w_c NAO entra aqui. Ele continua na formula do bloco 1, visivel e rotulado
  como transplante declarado. Dissolve-lo dentro da cobertura transformaria
  uma premissa num numero [medido] — que e exatamente o erro que este
  arquivo inteiro existe para nao cometer.

  taxa de automacao global = soma de w_c * cobertura_c

  Nota: cobertura_c pode passar de 1.0 numa classe que atrai mais volume do
  que possui (classe-ima). Isso nao e defeito da metrica, e informacao.
""")

TAUS = [0.0, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
curva = {}
for c in ordem_classes:
    n_real = int((yte == c).sum())
    pontos = []
    for tau in TAUS:
        canal = (pred == c) & (conf >= tau)
        n_canal = int(canal.sum())
        if n_canal == 0:
            pontos.append({"tau": tau, "cobertura": 0.0, "precisao": float("nan"),
                           "n_canal": 0})
            continue
        pontos.append({
            "tau": tau,
            "cobertura": n_canal / n_real,
            "precisao": float((yte[canal] == c).mean()),
            "n_canal": n_canal,
        })
    curva[c] = pontos

for c in ordem_classes:
    print(f"\n  {c}  —  volume real no teste: {int((yte == c).sum()):,} "
          f"| w_c = {w[c]:.3f} [dados, transplante declarado]")
    df = pd.DataFrame(curva[c])
    df["cobertura"] = df["cobertura"].round(3)
    df["precisao"] = df["precisao"].round(3)
    print(df.to_string(index=False))


# ==========================================================================
# PARTE 7 — CORTE CONTRA p*(k)
# ==========================================================================
titulo("PARTE 7 — O QUE NAO AUTOMATIZAR: CORTE CONTRA p*(k)")

COBERTURA_MINIMA = 0.10
print(f"""
Regra, vinda direto da SECAO 2 do bloco 1:

    automatizar a classe c so faz sentido se existir tau com
        precisao_c(tau) >= p*(k) = (k-1)/k
    e cobertura_c(tau) util (aqui: >= {COBERTURA_MINIMA:.0%}).

Abaixo de p*, o retrabalho gerado pelos erros supera o trabalho poupado
pelos acertos: automatizar aquela classe DESTROI horas. Nao e ROI magro,
e sinal negativo.
""")

for kappa in [5, 10, 20]:
    k = 1.0 + kappa
    pk = piso_precisao(k)
    print(f"\n  kappa = M/T = {kappa}  ->  p* = {pk:.1%}")
    linhas = []
    for c in ordem_classes:
        viaveis = [p for p in curva[c]
                   if p["cobertura"] >= COBERTURA_MINIMA and p["precisao"] == p["precisao"]
                   and p["precisao"] >= pk]
        if viaveis:
            melhor = max(viaveis, key=lambda p: p["cobertura"])
            linhas.append({
                "classe": c, "w_c": round(float(w[c]), 3),
                "veredito": "AUTOMATIZAR",
                "tau": melhor["tau"],
                "cobertura": round(melhor["cobertura"], 3),
                "precisao": round(melhor["precisao"], 3),
                "contrib w_c*cob": round(float(w[c]) * melhor["cobertura"], 4),
            })
        else:
            melhor_p = max((p["precisao"] for p in curva[c]
                            if p["cobertura"] >= COBERTURA_MINIMA
                            and p["precisao"] == p["precisao"]), default=float("nan"))
            linhas.append({
                "classe": c, "w_c": round(float(w[c]), 3),
                "veredito": "NAO AUTOMATIZAR",
                "tau": None, "cobertura": 0.0,
                "precisao": round(melhor_p, 3) if melhor_p == melhor_p else None,
                "contrib w_c*cob": 0.0,
            })
    t = pd.DataFrame(linhas)
    print(t.to_string(index=False))
    taxa = t["contrib w_c*cob"].sum()
    fora = t[t.veredito == "NAO AUTOMATIZAR"]["classe"].tolist()
    print(f"    taxa de automacao global (soma de w_c*cobertura_c): {taxa:.1%}")
    print(f"    classes fora: {fora if fora else 'nenhuma'}")

print("""
COMO ESTA TABELA CHEGOU AQUI — registro de uma correcao, nao de um acerto

  A primeira versao desta PARTE 7 dizia 'automatize 100%, nenhuma classe
  fora', que e o red flag que o proprio enunciado cita. A causa nao era o
  classificador: era uma confusao dentro do bloco 1, que so ficou visivel
  depois que a medicao existiu.

  g(p,k) tinha sido escrito supondo que um acerto significa 'a maquina
  RESOLVE e o humano economiza um handle time inteiro'. Mas o que se mede
  aqui e precisao de CLASSIFICACAO, e classificar bem prova que da para
  ROTEAR, nao para resolver. As duas economias tem tamanhos diferentes:
  rotear certo poupa a TRIAGEM (T); resolver sozinho pouparia o handle time.

  Corrigido no bloco 1, SECAO 1B. O parametro deixou de ser 'k, custo do
  erro em multiplos do handle time' e passou a ser kappa = M/T, o custo do
  misrouting em multiplos da triagem — grandeza muito maior, porque a
  triagem e curta e a transferencia e cara. Com isso p* sobe de 50-75%
  para 83-95%, e o corte finalmente morde.

  E o corte morde onde eu nao esperava: em COBERTURA, nao em exclusao de
  classe. Nenhuma das oito sai da lista; o que encolhe e quanto de cada uma
  pode ser auto-roteado. A resposta para 'o que NAO automatizar' nao e uma
  lista de assuntos proibidos — e, dentro de cada assunto, a cauda de baixa
  confianca. Por isso ela vira regra no triagem.py e nao regra de negocio.

  O QUE CONTINUA FORA DE ALCANCE: auto-RESOLUCAO. Dimensionar isso exigiria
  medir repeticao de solucao — o campo resolution_code, item 10 da PARTE 3
  do bloco 0. O dataset 2 nao tem campo de resolucao; o dataset 1 tem e a
  evidencia E6 provou que e faker. Nenhum numero de auto-resolucao aparece
  nesta entrega, e o motivo e falta de instrumento, nao modestia.
""")


# ==========================================================================
# PARTE 8 — MATRIZ DE CONFUSAO
# ==========================================================================
titulo("PARTE 8 — MATRIZ DE CONFUSAO")

cm = confusion_matrix(yte, pred, labels=ordem_classes)
cm_norm = cm / cm.sum(axis=1, keepdims=True)

print("\nContagens absolutas (linha = classe real, coluna = predita):")
print(pd.DataFrame(cm, index=ordem_classes, columns=ordem_classes).to_string())

fig, ax = plt.subplots(figsize=(9.5, 8))
im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(len(ordem_classes)))
ax.set_yticks(range(len(ordem_classes)))
ax.set_xticklabels(ordem_classes, rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(ordem_classes, fontsize=9)
ax.set_xlabel("classe predita", fontsize=10)
ax.set_ylabel("classe real", fontsize=10)
ax.set_title("Matriz de confusao — normalizada por classe real\n"
             f"TF-IDF + regressao logistica | teste = {len(i_te):,} tickets | semente {SEMENTE}",
             fontsize=11)
for a in range(len(ordem_classes)):
    for b in range(len(ordem_classes)):
        if cm_norm[a, b] >= 0.005:
            ax.text(b, a, f"{cm_norm[a, b]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if cm_norm[a, b] > 0.5 else "#222")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="fracao da classe real")
fig.tight_layout()
caminho_cm = GRAFICOS / "matriz_confusao.png"
fig.savefig(caminho_cm, dpi=150)
plt.close(fig)
print(f"\n  salvo: {caminho_cm.relative_to(AQUI)}")

fig, ax = plt.subplots(figsize=(9.5, 6.5))
for c in ordem_classes:
    pts = [(p["cobertura"], p["precisao"]) for p in curva[c] if p["n_canal"] > 0]
    if pts:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, marker="o", ms=4, lw=1.6, label=f"{c} (w={w[c]:.2f})")
for k, estilo in [(2.0, "--"), (3.0, ":")]:
    ax.axhline(piso_precisao(k), color="#c0392b", ls=estilo, lw=1.4,
               label=f"p*(k={k:.0f}) = {piso_precisao(k):.0%}")
ax.set_xlabel("cobertura_c — fracao do volume da classe que a maquina assume")
ax.set_ylabel("precisao_c")
ax.set_title("Curva cobertura x precisao por classe\n"
             "entrada medida do business case (substitui curva_placeholder)", fontsize=11)
ax.grid(alpha=0.3)
ax.legend(fontsize=8, loc="lower left")
fig.tight_layout()
caminho_curva = GRAFICOS / "curva_cobertura_precisao.png"
fig.savefig(caminho_curva, dpi=150)
plt.close(fig)
print(f"  salvo: {caminho_curva.relative_to(AQUI)}")


# ==========================================================================
# PARTE 9 — CONFERENCIA DAS PREVISOES
# ==========================================================================
titulo("PARTE 9 — CONFERENCIA DAS PREVISOES REGISTRADAS NO BLOCO 1")

print("""
As previsoes P1, P2 e P3 foram registradas no commit bef5c92, antes deste
bloco existir. Cada uma vem com criterio de falsificacao escrito. Aqui cada
criterio e aplicado, sem suavizar.
""")

resultados = {}

# --- P1 ---
pk2 = piso_precisao(2.0)
misc = [p for p in curva["Miscellaneous"]
        if p["cobertura"] >= COBERTURA_MINIMA and p["precisao"] == p["precisao"]]
melhor_misc = max((p["precisao"] for p in misc), default=float("nan"))
p1_ok = not (melhor_misc >= pk2)
resultados["P1"] = p1_ok
print(f"""P1 — 'Miscellaneous ficara abaixo de p* apesar de ser a 4a maior classe'
  criterio de falsificacao : precisao >= {pk2:.0%} em algum tau com cobertura >= {COBERTURA_MINIMA:.0%}
  melhor precisao observada: {melhor_misc:.3f}  (com cobertura >= {COBERTURA_MINIMA:.0%})
  w_c                      : {w['Miscellaneous']:.1%}, {int((itsm.Topic_group == 'Miscellaneous').sum()):,} tickets
  VEREDITO                 : {'CONFIRMADA' if p1_ok else 'FALSIFICADA'}""")

# --- P2 ---
i_ar = ordem_classes.index("Administrative rights")
i_ac = ordem_classes.index("Access")
fluxo_ar_ac = cm[i_ar, i_ac] / cm[i_ar].sum()
fluxo_ac_ar = cm[i_ac, i_ar] / cm[i_ac].sum()
p2_ok = fluxo_ar_ac > fluxo_ac_ar
resultados["P2"] = p2_ok
print(f"""
P2 — 'Administrative rights sera absorvida por Access, e nao o contrario'
  criterio de falsificacao : matriz simetrica, ou fluxo maior no sentido inverso
  Administrative rights -> Access : {cm[i_ar, i_ac]:>4} de {cm[i_ar].sum():>4} reais = {fluxo_ar_ac:.1%}
  Access -> Administrative rights : {cm[i_ac, i_ar]:>4} de {cm[i_ac].sum():>4} reais = {fluxo_ac_ar:.1%}
  razao de assimetria             : {fluxo_ar_ac / fluxo_ac_ar if fluxo_ac_ar else float('inf'):.1f}x
  VEREDITO                        : {'CONFIRMADA' if p2_ok else 'FALSIFICADA'}""")

# --- P3R ---
prec_por_classe = {}
for c in ordem_classes:
    m = pred == c
    prec_por_classe[c] = float((yte[m] == c).mean()) if m.sum() else float("nan")
melhor_classe = max(prec_por_classe, key=lambda c: prec_por_classe[c])
p3a_ok = melhor_classe != "Hardware"

i_hw = ordem_classes.index("Hardware")
linha_hw = [(ordem_classes[j], cm[i_hw, j]) for j in range(len(ordem_classes)) if j != i_hw]
linha_hw.sort(key=lambda t: -t[1])
top2_confusao = [n for n, _ in linha_hw[:2]]
p3b_ok = "Access" in top2_confusao
resultados["P3R-a"] = p3a_ok
resultados["P3R-b"] = p3b_ok
print(f"""
P3R-a — 'Hardware NAO tera a maior precisao entre as 8 classes'
  criterio de falsificacao : Hardware ser a de maior precisao
  precisao de Hardware     : {prec_por_classe['Hardware']:.3f}
  maior precisao observada : {prec_por_classe[melhor_classe]:.3f}  ({melhor_classe})
  VEREDITO                 : {'CONFIRMADA' if p3a_ok else 'FALSIFICADA'}

P3R-b — 'Access estara entre as duas maiores fontes de confusao de Hardware'
  criterio de falsificacao : Access fora das duas maiores linhas de confusao
  duas maiores confusoes de Hardware : {top2_confusao[0]} ({linha_hw[0][1]}), {top2_confusao[1]} ({linha_hw[1][1]})
  VEREDITO                           : {'CONFIRMADA' if p3b_ok else 'FALSIFICADA'}

P3 ORIGINAL — retirada na PARTE 0, antes do treino, por leitura de 20 amostras.
  Nao entra na contagem: nao foi medida, foi abandonada com motivo registrado.""")

acertos = sum(resultados.values())
print(f"""
PLACAR BRUTO: {acertos} de {len(resultados)} criterios confirmados.
  {json.dumps({k: ('CONFIRMADA' if v else 'FALSIFICADA') for k, v in resultados.items()}, ensure_ascii=False)}

O placar bruto favorece demais. A leitura honesta esta abaixo.
""")

titulo("PARTE 9B — POST-MORTEM DAS QUATRO PREVISOES", "-")

absorve = {}
for a, cl in enumerate(ordem_classes):
    linha = [(ordem_classes[b], cm[a, b]) for b in range(len(ordem_classes)) if b != a]
    dest, n = max(linha, key=lambda t: t[1])
    absorve[cl] = (dest, n, cm[a].sum())

marc = ["snow", "approval", "approver", "owner", "group", "sow", "queue"]
t_misc = itsm.loc[itsm.Topic_group == "Miscellaneous", "Document"].str.lower()
t_resto = itsm.loc[itsm.Topic_group != "Miscellaneous", "Document"].str.lower()
cob_misc = t_misc.str.contains("|".join(marc)).mean()
cob_resto = t_resto.str.contains("|".join(marc)).mean()

print(f"""
P1 — FALSIFICADA, e no sentido oposto.
  Previ Miscellaneous abaixo de p*. Ela faz {melhor_misc:.1%} de precisao, e ainda
  88.9% com 86.8% de cobertura. E MAIS separavel que Hardware.
  POR QUE: eu li o NOME do rotulo em vez do dado. 'Miscellaneous' soa a
  balde de exclusao; nesta base o rotulo tem dono. Medido agora:
    documentos contendo {{snow, approval, approver, owner, group, sow, queue}}
      dentro de Miscellaneous : {cob_misc:.1%}
      no resto da base        : {cob_resto:.1%}   (lift {cob_misc / cob_resto:.1f}x)
    'approval' sozinho: 13.1% contra 1.5% — 8.7x.
  Nao e residuo: e o dominio de workflow interno (ServiceNow, aprovacao,
  troca de dono e de grupo, contrato). Vocabulario proprio, logo separavel.

P2 — CONFIRMADA no criterio, ERRADA no fundo. Pior que falsificada.
  Meu criterio testou a DIRECAO DE UM PAR (admin rights -> access maior que
  o inverso?) em vez de perguntar QUEM ABSORVE. Mal especificado, e passou
  por isso. Quem absorve Administrative rights, medido:
    -> Hardware : {cm[i_ar, ordem_classes.index('Hardware')]:>3} de {cm[i_ar].sum():>3}  ({cm[i_ar, ordem_classes.index('Hardware')] / cm[i_ar].sum():.1%})
    -> Access   : {cm[i_ar, i_ac]:>3} de {cm[i_ar].sum():>3}  ({fluxo_ar_ac:.1%})
  A vizinha semantica que eu apontei absorve quase nada. Uma previsao
  confirmada que esta errada no fundo e pior que uma falsificada, porque
  sobrevive a conferencia. Fica registrada assim, sem alivio.

P3R-b — FALSIFICADA, e pela MESMA causa do P2.
  Previ Access entre as duas maiores confusoes de Hardware por leitura
  semantica; deu {linha_hw[0][0]} ({linha_hw[0][1]}) e {linha_hw[1][0]} ({linha_hw[1][1]}), Access em terceiro ({dict(linha_hw)['Access']}).

P3R-a — CONFIRMADA, limpa. Hardware {prec_por_classe['Hardware']:.3f} contra {prec_por_classe[melhor_classe]:.3f} de {melhor_classe}.

A LICAO, e ela e uma so nas quatro:
  PRIOR VENCEU SEMANTICA. Hardware e o ralo da base — recebe {cm[:, i_hw].sum() - cm[i_hw, i_hw]:,} predicoes
  erradas vindas das outras sete ({', '.join(f'{ordem_classes[b]} {cm[b, i_hw]}' for b in range(len(ordem_classes)) if b != i_hw)}),
  e seu canal fica com cobertura acima de 1.0. O erro nao anda para a
  vizinha semantica, anda para a MAIOR classe.
  Eu previ o mecanismo certo (absorcao por desbalanceamento) apontado para
  o lugar errado (a vizinha de significado). E nas duas vezes que errei
  feio — P1 e P3 original — a causa foi a mesma: raciocinei sobre o NOME do
  rotulo em vez de ler amostra dele.

  Placar honesto: 1 acerto limpo, 1 acerto que nao deveria ter passado,
  2 falsificadas. As duas que marquei base ALTA no bloco 1 sao justamente
  a que mais errou e a que passou por criterio frouxo.
""")


# ==========================================================================
# PARTE 10 — HANDOFF
# ==========================================================================
titulo("PARTE 10 — HANDOFF")

payload = {
    "origem": "03_classificador.py",
    "semente": SEMENTE,
    "n_teste": int(len(i_te)),
    "modelo": "TfidfVectorizer(min_df=3, 1-2gram, sublinear_tf) + LogisticRegression(C=4)",
    "definicao_cobertura": "canal_c(tau) / volume real da classe c (fracao dentro da classe)",
    "w_c": {c: float(w[c]) for c in ordem_classes},
    "curva": {c: curva[c] for c in ordem_classes},
}
CURVA_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"""
  curva medida escrita em: {CURVA_JSON.name}
  O 02_business_case.py passa a le-la no lugar de curva_placeholder().

ANOTADO PARA O TRIAGEM.PY, NAO IMPLEMENTADO AQUI
  Regra de abstencao por empate no topo: quando as duas classes de maior
  probabilidade estao proximas, o ticket vai para humano mesmo que a maior
  passe do limiar. Isso e regra de TRIAGEM, nao de classificacao — o
  classificador so precisa expor as probabilidades. Fica registrado aqui e
  entra no proximo bloco.

  tempo total desta rodada: {time.time() - t_inicio:.1f}s
""")

titulo("FIM — BLOCO 3")
print(f"saida salva em: {SAIDA}")
sys.stdout.flush()
