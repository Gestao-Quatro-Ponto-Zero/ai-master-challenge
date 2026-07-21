"""
05_contexto_similar.py — Bloco 5: chamados similares como CONTEXTO, nao como resposta

O enunciado (linha 82) pede "um sistema de respostas sugeridas baseado em
tickets similares". Este bloco nao entrega isso, e a PARTE 0 mede por que:
nenhum dos dois arquivos tem resolucao reaproveitavel.

  - dataset 1 tem a coluna Resolution, e a evidencia E6 do bloco 0 provou que
    ela e texto gerado aleatoriamente. A PARTE 0 reconfirma aqui, com um teste
    novo: a resolucao nao e mais parecida com o proprio problema do que com o
    problema de OUTRO cliente. Ela nao carrega informacao sobre o ticket dela.
  - dataset 2 tem texto de chamado genuino e nenhum campo de resolucao.

Isso nao e desculpa, e diagnostico: a operacao que gerou esse dado nao
consegue reaproveitar solucao porque nao registra solucao reaproveitavel. E o
campo que faltaria e nominal — resolution_code / kb_article_id, item 10 da
PARTE 3 do bloco 0.

O QUE ESTE BLOCO ENTREGA NO LUGAR

  Um PAINEL DE CONTEXTO. Para um chamado novo, os k chamados mais parecidos ja
  roteados, cada um com: similaridade, a fila para onde foi, e um campo
  'resolucao_aplicada' que sai impresso como INDISPONIVEL. O buraco fica na
  tela do agente, nao so na prosa.

  Nada aqui e mostrado ao cliente. Nada aqui e rascunho de resposta. A palavra
  "resposta" nao aparece na interface deste artefato de proposito: o que a
  medicao licencia e roteamento (bloco 1, SECAO 1B), e contexto de roteamento
  e o maximo que este bloco pode ser sem prometer o que nao mediu.

  Alem de servir ao agente, o voto dos vizinhos e uma SEGUNDA OPINIAO
  independente do modelo linear — e isso da para medir. As PARTES 3 e 4 medem
  se a concordancia entre vizinhos e modelo separa acerto de erro dentro da
  politica ja definida no bloco 4.

REAPROVEITAMENTO — nada novo e treinado aqui
  vetorizador, split, modelo e limiares: todos vem do Triador do bloco 4, que
  por sua vez le curva_medida.json do bloco 3. O indice de similaridade usa a
  MESMA matriz TF-IDF do classificador. Se usasse outro espaco de features, o
  vizinho exibido nao explicaria a decisao exibida ao lado dele.

Uso:
    .venv/Scripts/python.exe 05_contexto_similar.py

Dependencias: pandas, scipy, scikit-learn (ver requirements.txt)
Saida: stdout + 05_contexto_similar_saida.txt + contexto_medido.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.neighbors import NearestNeighbors

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

b4 = import_module("04_triagem")
Tee, titulo, Triador, Decisao = b4.Tee, b4.titulo, b4.Triador, b4.Decisao
achar_pasta_dados = b4.achar_pasta_dados

SAIDA = AQUI / "05_contexto_similar_saida.txt"
MEDIDO_JSON = AQUI / "contexto_medido.json"
SEMENTE = 42

# --------------------------------------------------------------------------
# PARAMETROS DO PAINEL — cada um com procedencia
# --------------------------------------------------------------------------

# [convencao do analista] quantos chamados similares o painel mostra. Nao sai
# dos dados: e quanto cabe na tela de um agente sem virar leitura de relatorio.
K_VIZINHOS = 3

# [convencao do analista] similaridade minima para um vizinho ser exibido.
# Existe para o painel poder devolver VAZIO. Um painel que sempre acha tres
# "parecidos" acha tres parecidos tambem quando nao ha nenhum — e ai ele nao
# informa, ele decora.
SIM_MINIMA = 0.30

# [dados, bloco 3] limiar a partir do qual dois documentos foram tratados como
# quase-duplicatas na auditoria de vazamento. Reaproveitado aqui com o sinal
# invertido: la era risco de memorizacao, aqui e densidade de repeticao.
SIM_GEMEO = 0.90

PARADAS = {
    "the", "and", "for", "you", "with", "this", "that", "have", "not", "are",
    "was", "can", "please", "hello", "hi", "your", "from", "our", "will",
    "would", "there", "they", "them", "has", "had", "but", "all", "any",
    "issue", "i'm", "im", "it", "is", "to", "of", "in", "on", "a", "my", "me",
    "do", "be", "as", "at", "an", "by", "or", "if", "so", "we", "us", "no",
}


def tokens(texto: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{3,}", str(texto).lower())
            if t not in PARADAS}


# --------------------------------------------------------------------------
# RETORNO ESTRUTURADO — o que a interface do proximo bloco vai consumir
# --------------------------------------------------------------------------

@dataclass
class Similar:
    """Um chamado parecido, ja roteado. Nao e uma resposta."""
    similaridade: float
    fila: str                  # o rotulo real do chamado historico
    trecho: str
    resolucao_aplicada: str    # sempre INDISPONIVEL nesta base — ver PARTE 6

    def __str__(self) -> str:
        return (f"    sim {self.similaridade:.3f} | fila '{self.fila}'\n"
                f"      texto    : {self.trecho}\n"
                f"      resolucao: {self.resolucao_aplicada}")


@dataclass
class Contexto:
    """O painel inteiro de um chamado: a decisao de roteamento + o contexto.

    'voto_vizinhos' e o rotulo majoritario entre os similares exibidos. E uma
    segunda opiniao, independente do modelo linear — nao um segundo palpite do
    mesmo modelo. Quando as duas discordam, o caso merece olho humano; quanto
    isso vale esta medido na PARTE 3, e NAO esta implementado como regra.
    """
    decisao: Decisao
    similares: list[Similar]
    voto_vizinhos: str | None
    concorda: bool | None
    aviso: str

    def to_dict(self) -> dict:
        return {"decisao": asdict(self.decisao),
                "similares": [asdict(s) for s in self.similares],
                "voto_vizinhos": self.voto_vizinhos,
                "concorda": self.concorda,
                "aviso": self.aviso}


AVISO_PADRAO = ("CONTEXTO PARA O AGENTE — nao e resposta ao cliente, nao e "
                "rascunho, nao fecha ticket.")


# --------------------------------------------------------------------------
# O PAINEL
# --------------------------------------------------------------------------

class PainelDeContexto:
    """Triador do bloco 4 + recuperacao de chamados similares do treino.

    Nao treina nada. Compoe.
    """

    def __init__(self, triador: Triador | None = None, k: int = K_VIZINHOS,
                 sim_minima: float = SIM_MINIMA):
        self.tri = triador if triador is not None else Triador()
        self.k = k
        self.sim_minima = sim_minima
        self.textos_tr, self.y_tr = self.tri._treino
        # brute force sobre a matriz esparsa do proprio classificador. Como o
        # TF-IDF do sklearn ja sai normalizado em L2, cosseno = produto interno.
        self.indice = NearestNeighbors(n_neighbors=self.k, metric="cosine",
                                       algorithm="brute")
        self.indice.fit(self.tri.Xtr)

    # -- recuperacao -------------------------------------------------------

    def _similares(self, sims: np.ndarray, idx: np.ndarray) -> list[Similar]:
        out = []
        for s, i in zip(sims, idx):
            if s < self.sim_minima:
                continue
            out.append(Similar(
                similaridade=float(s),
                fila=str(self.y_tr[i]),
                trecho=str(self.textos_tr[i])[:110],
                resolucao_aplicada=("[INDISPONIVEL — o campo resolution_code "
                                    "nao existe nesta base]"),
            ))
        return out

    @staticmethod
    def _voto(similares: list[Similar]) -> str | None:
        """Rotulo majoritario entre os exibidos; empate resolvido pelo mais similar."""
        if not similares:
            return None
        contagem: dict[str, float] = {}
        for s in similares:
            contagem[s.fila] = contagem.get(s.fila, 0) + 1
        maximo = max(contagem.values())
        empatados = [c for c, n in contagem.items() if n == maximo]
        if len(empatados) == 1:
            return empatados[0]
        for s in similares:                      # ja vem ordenado por similaridade
            if s.fila in empatados:
                return s.fila
        return empatados[0]

    def _montar(self, decisao: Decisao, sims, idx) -> Contexto:
        similares = self._similares(sims, idx)
        voto = self._voto(similares)
        return Contexto(decisao=decisao, similares=similares, voto_vizinhos=voto,
                        concorda=(None if voto is None else voto == decisao.categoria),
                        aviso=AVISO_PADRAO)

    # -- API unitaria (e a que a interface do proximo bloco chama) ---------

    def montar(self, texto: str) -> Contexto:
        X = self.tri.vetor.transform([texto])
        decisao = self.tri._decidir(self.tri.modelo.predict_proba(X)[0])
        dist, idx = self.indice.kneighbors(X, n_neighbors=self.k)
        return self._montar(decisao, 1.0 - dist[0], idx[0])

    def montar_lote(self, textos) -> tuple[list[Contexto], np.ndarray]:
        X = self.tri.vetor.transform(textos)
        decisoes = [self.tri._decidir(p) for p in self.tri.modelo.predict_proba(X)]
        dist, idx = self.indice.kneighbors(X, n_neighbors=self.k)
        sims = 1.0 - dist
        ctxs = [self._montar(d, sims[i], idx[i]) for i, d in enumerate(decisoes)]
        return ctxs, sims


def imprimir_painel(ctx: Contexto, texto: str, real: str | None = None):
    print(f"  chamado : {texto[:140]}")
    if real is not None:
        print(f"  real    : {real}")
    print(f"  {ctx.decisao}")
    print(f"  [{ctx.aviso}]")
    if not ctx.similares:
        print("    (nenhum chamado comparavel na base acima de "
              f"sim={SIM_MINIMA} — o painel devolve VAZIO em vez de inventar tres)")
    for s in ctx.similares:
        print(s)
    if ctx.voto_vizinhos is not None:
        veredito = "concordam" if ctx.concorda else "DISCORDAM"
        print(f"    -> voto dos vizinhos: '{ctx.voto_vizinhos}' | "
              f"modelo: '{ctx.decisao.categoria}' | {veredito}")
    print()


# ==========================================================================
# EXECUCAO
# ==========================================================================

if __name__ == "__main__":
    sys.stdout = Tee(SAIDA)
    t0 = time.time()

    titulo("BLOCO 5 — CONTEXTO DE CHAMADOS SIMILARES (nao e resposta sugerida)")
    print(f"""
O enunciado, linha 82, pede "um sistema de respostas sugeridas baseado em
tickets similares". Este bloco entrega chamados similares como CONTEXTO e se
recusa a chama-los de resposta. A PARTE 0 mede o motivo; as PARTES 2 a 4 medem
o que sobra; a PARTE 6 nomeia o campo que faltaria.

Parametros do painel:
  k vizinhos exibidos    : {K_VIZINHOS}      [convencao do analista]
  similaridade minima    : {SIM_MINIMA}   [convencao do analista] — abaixo disso o painel fica VAZIO
  limiar de "gemeo"      : {SIM_GEMEO}   [dados, bloco 3] mesmo limiar da auditoria de vazamento
""")

    # ----------------------------------------------------------------------
    titulo("PARTE 0 — POR QUE O DESENHO PEDIDO NAO EXISTE NESTES DADOS", "-")
    dados = achar_pasta_dados()
    ops = pd.read_csv(dados / "customer_support_tickets.csv")
    res = ops["Resolution"].dropna().astype(str)
    desc = ops.loc[res.index, "Ticket Description"].astype(str)

    print(f"""
DESENHO OBVIO, E POR QUE ELE MORRE

  "para um chamado novo, ache os 3 mais parecidos e mostre o que foi feito
   neles" exige duas colunas no mesmo arquivo: texto do problema e texto da
   solucao. Nenhum dos dois arquivos tem as duas.

  dataset 2 (all_tickets_processed_improved_v3.csv): texto genuino, 8 rotulos,
    NENHUM campo de resolucao. E o arquivo com que o classificador foi medido.

  dataset 1 (customer_support_tickets.csv): tem a coluna Resolution.
    resolucoes nao-nulas : {len(res):,}
    valores unicos       : {res.nunique():,}  ({res.nunique() / len(res):.1%} de unicidade)
    comprimento medio    : {res.str.len().mean():.0f} caracteres
""")

    # teste novo: a resolucao carrega informacao sobre o proprio ticket?
    rng = np.random.default_rng(SEMENTE)
    embaralhado = rng.permutation(len(desc))
    tok_r = [tokens(t) for t in res.to_numpy()]
    tok_d = [tokens(t) for t in desc.to_numpy()]
    proprio = np.array([len(r & d) / max(len(r), 1) for r, d in zip(tok_r, tok_d)])
    alheio = np.array([len(r & tok_d[j]) / max(len(r), 1)
                       for r, j in zip(tok_r, embaralhado)])
    t_stat, p_val = stats.ttest_rel(proprio, alheio)
    dif = proprio - alheio
    cohen_d = float(dif.mean() / dif.std(ddof=1))
    zero_proprio = float((proprio == 0).mean())
    zero_alheio = float((alheio == 0).mean())

    print(f"""TESTE NOVO — A RESOLUCAO FALA DO PROPRIO TICKET?

  Se a resolucao fosse real, ela dividiria vocabulario com o problema que
  resolveu: quem responde sobre uma fatura escreve "fatura". Entao mede-se a
  fracao de palavras da resolucao que aparecem na descricao DELA, e compara-se
  com a mesma fracao contra a descricao de OUTRO cliente sorteado (semente
  {SEMENTE}). O controle e pareado: mesma resolucao, problema trocado. Como a
  permutacao so embaralha os pares, os dois lados tem a MESMA distribuicao de
  comprimento de descricao — a comparacao nao e contaminada por tamanho.

    sobreposicao com o proprio problema      : {proprio.mean():.4f}
    sobreposicao com problema de outro       : {alheio.mean():.4f}
    diferenca                                : {proprio.mean() - alheio.mean():+.4f}
    teste t pareado                          : t={t_stat:.2f}, p={p_val:.3f}
    tamanho de efeito (d de Cohen pareado)   : {cohen_d:.3f}
    resolucoes SEM UMA UNICA palavra em comum
      com o proprio problema                 : {zero_proprio:.1%}
      com o problema de um estranho          : {zero_alheio:.1%}

  LEITURA, E ELA NAO E "DEU ZERO":

    A diferenca e estatisticamente significante (p={p_val:.3f}) e operacionalmente
    irrelevante (d={cohen_d:.3f}). Com {len(res):,} pares, um t-test detecta uma
    diferenca de {(proprio.mean() - alheio.mean())*100:.2f} ponto percentual sobre uma base de ~1%. Registro
    o p mesmo sendo inconveniente para a tese: suprimi-lo seria escolher o
    teste depois de ver o resultado.

    O numero que decide nao e o p, e a linha de baixo: {zero_proprio:.1%} das resolucoes
    nao tem UMA palavra em comum com o problema que teriam resolvido. Contra
    {zero_alheio:.1%} quando o problema e de outra pessoa. Nao ha o que recuperar em
    nenhum dos dois casos — a resolucao correta e a resolucao de um estranho
    sao igualmente inuteis para um agente.

  Isto e uma medida DIFERENTE da E6, nao uma mais forte: a E6 mostrou que
  nenhuma resolucao se repete ({res.nunique() / len(res):.0%} de unicidade); isto mostra que
  nenhuma CORRESPONDE. Uma base pode ter resolucoes todas distintas e ainda
  assim uteis — as duas medidas juntas e que fecham o caso.

  amostra (pares lidos agora, semente {SEMENTE}):""")

    for k, i in enumerate(rng.choice(len(res), size=3, replace=False), start=1):
        print(f"    [{k}] PROBLEMA : {desc.to_numpy()[i][:110]}")
        print(f"        RESOLUCAO: {res.to_numpy()[i]}")

    print("""
  CONSEQUENCIA — e o achado, nao a desculpa:

    a operacao que gerou este dado nao consegue reaproveitar solucao porque
    nao registra solucao reaproveitavel. Um sistema de respostas sugeridas nao
    e bloqueado por falta de modelo, de embedding ou de LLM. E bloqueado por
    um campo. Construir a camada de resposta em cima de texto livre desta
    qualidade produziria sugestoes como as tres impressas acima, entregues a
    um agente como se fossem precedente. Isso e pior que nao ter o recurso.
""")

    # ----------------------------------------------------------------------
    titulo("PARTE 1 — O QUE SOBRA, E COMO ELE SE CHAMA", "-")
    print("""
ARTEFATO: painel de contexto — chamados similares JA ROTEADOS.

  entrega ao agente : os 3 chamados historicos mais parecidos, com a
                      similaridade e a fila para onde cada um foi.
  NAO entrega       : texto para mandar ao cliente, rascunho, macro, ou
                      qualquer coisa que possa ser copiada e enviada.

  O nome importa e foi escolhido para nao mentir. "Resposta sugerida" promete
  que a maquina sabe o que responder; o que foi medido no bloco 3 e precisao
  de CLASSIFICACAO, que licencia escolher a fila e nada alem (bloco 1, SECAO
  1B). Um painel chamado "resposta sugerida" seria a mesma medicao com um
  nome que ela nao sustenta — e o agente confiaria nele de acordo com o nome.

  Por isso todo painel deste bloco sai com o carimbo:
    "CONTEXTO PARA O AGENTE — nao e resposta ao cliente, nao e rascunho,
     nao fecha ticket."

SEGUNDO USO, QUE E O QUE PAGA O CUSTO DO MODULO

  Os vizinhos votam. E um voto de vizinhanca, computado sobre a mesma matriz
  TF-IDF, mas independente dos coeficientes da regressao logistica: um erra
  por prior, o outro erra por vocabulario local. Quando os dois concordam, ha
  duas evidencias; quando discordam, o caso e ambiguo por dois motivos
  diferentes. As PARTES 3 e 4 medem se essa discordancia vale alguma coisa.
""")

    print("montando o painel (reaproveita o Triador do bloco 4; nada e treinado aqui)...")
    painel = PainelDeContexto()
    textos_te, y_te = painel.tri._teste
    ctxs, sims = painel.montar_lote(textos_te)
    print(f"  {len(textos_te):,} chamados de teste processados em {time.time() - t0:.1f}s")

    sim1 = sims[:, 0]
    votos = np.array([c.voto_vizinhos if c.voto_vizinhos is not None else ""
                      for c in ctxs])
    df = pd.DataFrame({
        "real": y_te,
        "categoria": [c.decisao.categoria for c in ctxs],
        "rota": [c.decisao.rota for c in ctxs],
        "confianca": [c.decisao.confianca for c in ctxs],
        "sim1": sim1,
        "voto": votos,
        "n_similares": [len(c.similares) for c in ctxs],
    })
    df["acertou"] = df.categoria == df.real
    df["tem_gemeo"] = df.sim1 >= SIM_GEMEO
    df["grupo"] = np.where(df.voto == "", "sem contexto",
                           np.where(df.voto == df.categoria, "concordam", "discordam"))

    # ----------------------------------------------------------------------
    titulo("PARTE 2 — DENSIDADE DE REPETICAO DE PROBLEMA", "-")
    faixas = [0.90, 0.70, 0.50, 0.30]
    print(f"""
Antes de perguntar se o painel ajuda, a pergunta e se existe o que recuperar.
Medido no conjunto de teste ({len(df):,} chamados), contra os {len(painel.textos_tr):,}
do treino: quao parecido e o vizinho mais proximo de cada chamado novo?

  similaridade do vizinho mais proximo — distribuicao
    mediana : {np.median(sim1):.3f}
    media   : {sim1.mean():.3f}""")
    for f in faixas:
        n = int((sim1 >= f).sum())
        print(f"    >= {f:.2f} : {n:6,}  ({n / len(df):5.1%})")
    print(f"    < {SIM_MINIMA:.2f} : {int((sim1 < SIM_MINIMA).sum()):6,}  "
          f"({(sim1 < SIM_MINIMA).mean():5.1%})  -> painel VAZIO, por construcao")

    print(f"""
O MESMO FATO DO BLOCO 3, COM O SINAL TROCADO — E COM UMA DISCREPANCIA A DECLARAR

  A PARTE 1 do bloco 3 mediu quase-duplicata como RISCO: documento repetido
  dos dois lados do split infla acuracia por memorizacao. La, 12.17% do
  conjunto de teste tinha gemeo >= 0.90 no treino. Aqui o mesmo fato e ATIVO —
  se o problema ja chegou antes, ha o que mostrar ao agente — mas o numero
  medido e {(sim1 >= SIM_GEMEO).mean():.1%}, e nao 12.17%.

  A DIFERENCA E DE METODO, NAO DE DADO, e fica registrada em vez de
  arredondada para o numero mais conveniente:

    bloco 3, auditoria : TfidfVectorizer(min_df=2, max_features=30000),
                         unigrama, sem sublinear_tf, ajustado na BASE INTEIRA
    bloco 5, painel    : o vetorizador DO CLASSIFICADOR — min_df=3, unigrama +
                         bigrama, sublinear_tf, ajustado so no TREINO

  Bigrama e sublinear_tf tornam a medida mais exigente: exigem que a ordem das
  palavras coincida, e achatam o peso do termo repetido. O mesmo par de
  documentos passa de 0.90 num espaco e nao passa no outro. Ou seja, 12.17% e
  o teto pessimista para a auditoria de vazamento (que deve superestimar o
  risco, e por isso o espaco frouxo era o certo la), e {(sim1 >= SIM_GEMEO).mean():.1%} e a leitura
  conservadora para o painel (que nao deve prometer contexto que nao tem).

  Cada bloco usou o espaco que erra para o lado seguro do seu proprio uso, e
  os dois numeros estao publicados. O espaco daqui nao foi escolhido por isso,
  no entanto: foi escolhido porque o vizinho exibido ao agente TEM de ser
  vizinho no mesmo espaco em que a decisao ao lado dele foi tomada. Se fossem
  espacos diferentes, o painel mostraria um contexto que nao explica a rota.

  E aqui esta a linha exata onde esta entrega para, e ela e a tese inteira em
  uma frase:

    repeticao de PROBLEMA e medivel nestes dados — esta medida acima.
    repeticao de SOLUCAO nao e — nao ha campo que a registre.

  A distancia entre as duas nao e um modelo. E uma coluna. Ver PARTE 6.
""")

    # ----------------------------------------------------------------------
    titulo("PARTE 3 — O VOTO DOS VIZINHOS COMO SEGUNDA OPINIAO", "-")
    voto_valido = df[df.voto != ""]
    print(f"""
Pergunta: quando o voto dos vizinhos discorda do modelo, o modelo erra mais?
Se sim, o painel nao e so conforto visual — e um detector de erro que ja esta
na tela, de graca, porque os vizinhos foram recuperados de qualquer forma.

  precisao do modelo (regressao logistica) no teste inteiro : {df.acertou.mean():.3f}
  precisao do voto de vizinhanca puro ({K_VIZINHOS}-NN, so onde ha voto)  : {(voto_valido.voto == voto_valido.real).mean():.3f}
    (o k-NN sozinho e pior, e por isso ele nao substitui o modelo — ele
     discorda dele, que e uma funcao diferente)
""")
    tab = df.groupby("grupo").agg(
        chamados=("grupo", "size"),
        **{"% do total": ("grupo", lambda s: round(len(s) / len(df) * 100, 1))},
        precisao_do_modelo=("acertou", "mean"),
    ).sort_values("chamados", ascending=False)
    tab["precisao_do_modelo"] = tab["precisao_do_modelo"].round(3)
    print(tab.to_string())

    conc = df[df.grupo == "concordam"]
    disc = df[df.grupo == "discordam"]
    separacao = conc.acertou.mean() - disc.acertou.mean()
    print(f"""
  SEPARACAO MEDIDA: {conc.acertou.mean():.3f} contra {disc.acertou.mean():.3f} = {separacao:+.3f}

  Sem gemeo (excluindo os {int(df.tem_gemeo.sum()):,} chamados com vizinho >= {SIM_GEMEO}, que sao
  o caso facil e inflariam a leitura):""")
    sg = df[~df.tem_gemeo]
    sg_c = sg[sg.grupo == "concordam"].acertou.mean()
    sg_d = sg[sg.grupo == "discordam"].acertou.mean()
    print(f"    concordam : {int((sg.grupo == 'concordam').sum()):,} chamados, precisao {sg_c:.3f}")
    print(f"    discordam : {int((sg.grupo == 'discordam').sum()):,} chamados, precisao {sg_d:.3f}")
    print(f"    separacao : {sg_c - sg_d:+.3f}")
    print(f"""
  Este e o mesmo movimento da PARTE 4 do bloco 3 (acuracia com e sem gemeo):
  se o efeito so existisse no subconjunto memorizado, ele nao seria efeito.
""")

    # ----------------------------------------------------------------------
    titulo("PARTE 4 — CRUZAMENTO COM A POLITICA DO BLOCO 4", "-")
    print("""
A politica do bloco 4 ja cortou o volume em tres rotas com quatro regras. A
pergunta aqui e se a discordancia dos vizinhos acrescenta informacao DENTRO
da rota auto — que e a unica onde nao ha humano olhando antes.
""")
    cruz = df.pivot_table(index="rota", columns="grupo", values="acertou",
                          aggfunc=["size", "mean"])
    print(cruz.round(3).to_string())

    auto = df[df.rota == "auto"]
    auto_c = auto[auto.grupo == "concordam"]
    auto_d = auto[auto.grupo == "discordam"]
    auto_s = auto[auto.grupo == "sem contexto"]
    piso = painel.tri.piso
    restante = auto[auto.grupo != "discordam"]
    print(f"""
DENTRO DA ROTA AUTO ({len(auto):,} chamados, precisao {auto.acertou.mean():.3f}, piso p*={piso:.1%})
  concordam    : {len(auto_c):5,} ({len(auto_c)/len(auto):5.1%})  precisao {auto_c.acertou.mean():.3f}
  discordam    : {len(auto_d):5,} ({len(auto_d)/len(auto):5.1%})  precisao {auto_d.acertou.mean():.3f}
  sem contexto : {len(auto_s):5,} ({len(auto_s)/len(auto):5.1%})  precisao {auto_s.acertou.mean() if len(auto_s) else float('nan'):.3f}

CONTRAFACTUAL — MEDIDO, NAO IMPLEMENTADO

  Se existisse uma regra R5 ("vizinhos discordam -> humano"), aplicada apos as
  quatro regras do bloco 4:

    sairiam do auto      : {len(auto_d):,} chamados ({len(auto_d)/len(df):.1%} do volume total)
    precisao do auto iria: {auto.acertou.mean():.3f} -> {restante.acertou.mean():.3f}  ({restante.acertou.mean() - auto.acertou.mean():+.3f})
    taxa de auto global  : {len(auto)/len(df):.1%} -> {len(restante)/len(df):.1%}
    precisao do desviado : {auto_d.acertou.mean():.3f}  (contra piso {piso:.1%})

  A R5 NAO entra nesta entrega, e o motivo e declarado: a politica do bloco 4
  ja foi medida e commitada com quatro regras, e promover a quinta mudaria a
  taxa de automacao publicada sem que o custo do desvio tenha sido discutido
  com quem paga por ele. O numero fica na mesa, do mesmo jeito que o custo da
  R1 ficou na PARTE 3 do bloco 4: quem decide troca cobertura por precisao com
  o preco a vista, e nao por gosto.

  O que ja vale hoje, sem regra nenhuma: o agente que recebe um chamado
  auto-roteado ve na propria tela se os vizinhos concordaram. Isso e revisao
  amostral dirigida em vez de aleatoria — e nao custa uma linha de politica.
""")

    # ----------------------------------------------------------------------
    titulo("PARTE 5 — O PAINEL COMO O AGENTE VE, EM CHAMADOS REAIS DO TESTE", "-")
    print("""
Um chamado de cada rota, os mesmos tres da PARTE 4 do bloco 4, agora com o
contexto ao lado da decisao.
""")
    for rota in ["auto", "humano", "aprovacao"]:
        sub = df[df.rota == rota]
        if sub.empty:
            continue
        i = int(sub.index[0])
        print(f"  ---- rota: {rota} ----")
        imprimir_painel(ctxs[i], str(textos_te[i]), str(y_te[i]))

    vazios = df[df.n_similares == 0]
    if len(vazios):
        i = int(vazios.index[0])
        print("  ---- caso em que o painel devolve VAZIO (nao ha comparavel) ----")
        imprimir_painel(ctxs[i], str(textos_te[i]), str(y_te[i]))

    # ----------------------------------------------------------------------
    titulo("PARTE 6 — O SLOT VAZIO: resolution_code", "-")
    print(f"""
Todo vizinho impresso acima carrega o campo:

    resolucao: [INDISPONIVEL — o campo resolution_code nao existe nesta base]

Ele esta na estrutura de dados, na dataclass Similar, e sai impresso vazio em
todos os {int(df.n_similares.sum()):,} vizinhos exibidos nesta rodada. Isso e deliberado. O
argumento fecha em circulo, e o circulo e o ponto mais forte desta proposta:

  1. o bloco 0 recomendou instrumentar resolution_code / kb_article_id
     (item 10 da PARTE 3), por analise dos dados e nao por boa pratica;
  2. o bloco 1 (SECAO 1B) mostrou que auto-RESOLUCAO nao e dimensionavel sem
     ele, e por isso nenhum numero de auto-resolucao aparece nesta entrega;
  3. o bloco 3 mediu classificacao e licenciou roteamento, so;
  4. o bloco 5 — este — tenta construir a camada de resposta que o enunciado
     pede e para no MESMO campo.

  Quatro blocos, quatro caminhos independentes, um unico gargalo. A
  recomendacao de instrumentacao nao e apendice de consultoria: e o que separa
  esta entrega da proxima.

O QUE MUDA NO DIA EM QUE O CAMPO EXISTIR — e nao e o modelo

  - a dataclass Similar ja tem o slot; ele passa a ser preenchido com o codigo
    de solucao do vizinho. Nenhuma mudanca de arquitetura.
  - nasce a metrica que hoje nao existe: taxa de repeticao de SOLUCAO
    (quantos chamados recebem o mesmo resolution_code). A PARTE 2 mediu
    repeticao de PROBLEMA — {(sim1 >= SIM_GEMEO).mean():.1%} com gemeo >= {SIM_GEMEO} e {(sim1 >= 0.70).mean():.1%} acima de 0.70,
    no espaco de features do classificador — e essa e o teto
    superior da outra: dois chamados com solucoes iguais nao precisam ter
    problemas parecidos, mas problemas quase identicos que recebem solucoes
    diferentes sao ou variacao de agente ou erro de registro, e as duas
    coisas sao achado.
  - so entao a camada de resposta pode ser proposta com numero, e so entao o
    nome "resposta sugerida" para de ser promessa.

ATE LA, A RECUSA E O ENTREGAVEL. O sistema pedido na linha 82 nao foi
construido porque construi-lo com estes dados significaria mostrar ao agente
frases como "Increase wife television along along need physical." rotuladas
como precedente. O que foi construido no lugar entrega o que o dado sustenta —
contexto de roteamento — e nomeia com precisao o que falta para entregar o
resto.
""")

    medido = {
        "origem": "05_contexto_similar.py",
        "artefato": "painel de contexto (chamados similares ja roteados)",
        "nao_e": "resposta sugerida / rascunho / texto ao cliente",
        "parametros": {"k_vizinhos": K_VIZINHOS, "sim_minima": SIM_MINIMA,
                       "sim_gemeo": SIM_GEMEO, "semente": SEMENTE},
        "dataset1_resolution": {
            "nao_nulas": int(len(res)),
            "unicidade": float(res.nunique() / len(res)),
            "sobreposicao_com_proprio_problema": float(proprio.mean()),
            "sobreposicao_com_problema_alheio": float(alheio.mean()),
            "ttest_pareado_p": float(p_val),
            "cohen_d_pareado": cohen_d,
            "frac_sem_palavra_em_comum_proprio": zero_proprio,
            "frac_sem_palavra_em_comum_alheio": zero_alheio,
        },
        "repeticao_de_problema": {
            "espaco": "vetorizador do classificador (min_df=3, 1-2gram, sublinear_tf, fit no treino)",
            "nota": ("bloco 3 mediu 12.17% de gemeos cruzando o split num espaco "
                     "mais frouxo (min_df=2, unigrama, sem sublinear_tf, fit na base "
                     "inteira); a diferenca e de metodo e esta declarada na PARTE 2"),
            **{f"frac_sim1_maior_igual_{f}": float((sim1 >= f).mean()) for f in faixas},
        },
        "voto_vizinhos": {
            "precisao_modelo_geral": float(df.acertou.mean()),
            "precisao_quando_concordam": float(conc.acertou.mean()),
            "precisao_quando_discordam": float(disc.acertou.mean()),
            "separacao": float(separacao),
            "separacao_sem_gemeo": float(sg_c - sg_d),
        },
        "contrafactual_R5": {
            "implementada": False,
            "sairiam_do_auto": int(len(auto_d)),
            "precisao_auto_atual": float(auto.acertou.mean()),
            "precisao_auto_com_R5": float(restante.acertou.mean()),
            "taxa_auto_atual": float(len(auto) / len(df)),
            "taxa_auto_com_R5": float(len(restante) / len(df)),
        },
        "bloqueio": "resolution_code / kb_article_id — item 10 da PARTE 3 do bloco 0",
    }
    MEDIDO_JSON.write_text(json.dumps(medido, indent=2, ensure_ascii=False),
                           encoding="utf-8")

    titulo("FIM — BLOCO 5")
    print(f"medicao salva em: {MEDIDO_JSON.name}")
    print(f"saida salva em: {SAIDA}")
    print(f"tempo total: {time.time() - t0:.1f}s")
    sys.stdout.flush()
