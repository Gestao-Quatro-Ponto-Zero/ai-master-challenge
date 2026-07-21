"""
02_business_case.py — Bloco 1: modelo parametrico de horas recuperaveis

O Bloco 0 provou que nenhum caminho nos dados produz 'horas desperdicadas'
por medicao direta: o arquivo que tem metrica tem metrica falsa, o arquivo
que tem texto real nao tem metrica.

Este bloco NAO tenta contornar isso. Ele monta o business case como funcao
explicita, com cada insumo marcado por procedencia, e reporta o que a
estrutura da funcao permite concluir SEM depender das premissas.

O que este script entrega:
  SECAO 0 — divergencia entre briefing e arquivo (tamanho E natureza)
  SECAO 1 — o modelo, e a algebra que elimina V e H
  SECAO 2 — resultado livre de premissa: piso de precisao p*(k)
  SECAO 3 — decisao A: o que a algebra garante e o que ela NAO garante
  SECAO 4 — quantificacao do que a SECAO 3 nao garante
  SECAO 5 — decisao B (FTE) e o ponto de cruzamento na faixa
  SECAO 6 — o que este bloco NAO entrega, e o gancho pro bloco 3
  SECAO 7 — previsoes registradas antes de medir

O que este script NAO entrega, por decisao explicita: ranking de prioridade.
Nenhuma tabela deste arquivo ordena categorias por horas recuperaveis. Ver
SECAO 6.

Uso:
    python 02_business_case.py

Dependencias: pandas  (ver requirements.txt)
Saida: escreve em stdout e em 02_business_case_saida.txt (mesmo diretorio).
"""

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Infra (mesma do bloco 0)
# --------------------------------------------------------------------------

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "02_business_case_saida.txt"


def achar_pasta_dados() -> Path:
    """Sobe a arvore de diretorios procurando a pasta data/ com os dois CSVs."""
    for pasta in [AQUI, *AQUI.parents]:
        candidata = pasta / "data"
        if (candidata / "customer_support_tickets.csv").exists():
            return candidata
    raise SystemExit(
        "ERRO: nao encontrei data/customer_support_tickets.csv subindo a partir de "
        f"{AQUI}. Rode a partir do repositorio."
    )


class Tee:
    """Escreve simultaneamente no console e no arquivo de saida."""

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


# ==========================================================================
# PARAMETROS — cada um com procedencia declarada
# ==========================================================================
#
# Regra fixa desta entrega: onde nao ha fonte, o texto escreve
# "premissa arbitrada, sem fonte" com todas as letras. Nao existe
# "estudos da industria indicam" em lugar nenhum deste arquivo.

# [enunciado] challenges/process-002-support/README.md, linha 11:
# "A operacao atende ~30.000 tickets por ano"
V_ANO = 30_000

# [premissa arbitrada, sem fonte] tempo medio de trabalho humano por ticket.
# A faixa e deliberadamente larga PORQUE nao ha fonte. Escalar linear: ver
# SECAO 1 — nao recebe eixo de sensibilidade, recebe uma linha de texto.
H_MIN_MINUTOS = 3.0
H_MAX_MINUTOS = 30.0

# [premissa arbitrada, sem fonte] custo do erro como MULTIPLO adimensional do
# handle time. Um ticket automatizado errado custa k vezes o que custaria ter
# sido feito certo na primeira vez (transferencia + retrabalho). k=1 significa
# "errar sai de graca"; k=4 significa "errar custa 4 chamados".
K_MIN = 1.25
K_MAX = 4.00
K_GRADE = [1.25, 1.50, 2.00, 2.50, 3.00, 4.00]

# [premissa arbitrada, sem fonte] horas produtivas por FTE por ano.
# Divisor linear puro: dobrou, metade do FTE. Nao muda nenhuma conclusao,
# so a escala do eixo.
HORAS_POR_FTE_ANO = 1_760

# [convencao do analista, nao achado dos dados] limiar de materialidade.
# "1 FTE" nao sai de lugar nenhum dos arquivos — e a linha que EU escolhi
# para separar "isso e conversa de headcount" de "isso e ruido de arredondamento".
# Quem le pode mover essa linha; o modelo nao muda.
LIMIAR_FTE = 1.0

# [PLACEHOLDER — substituido pela medicao do bloco 3]
# tau e o limiar de confianca do classificador. Seu efeito so existe atraves
# da curva cobertura x precisao, que ainda NAO foi medida. A forma fechada
# abaixo e um marcador auditavel, escolhido apenas por ser monotono no sentido
# certo (subir tau compra precisao pagando com cobertura). Os numeros que
# dependem dela se movem quando o bloco 3 rodar; os das SECOES 2 a 4 nao.
TAU_GRADE = [0.00, 0.25, 0.50, 0.75, 1.00]


CURVA_JSON = AQUI / "curva_medida.json"
CURVA_MEDIDA = None
if CURVA_JSON.exists():
    CURVA_MEDIDA = json.loads(CURVA_JSON.read_text(encoding="utf-8"))


def curva_placeholder(tau: float) -> tuple[float, float]:
    """[PLACEHOLDER] Retorna (cobertura, precisao) para um dado tau.

    Usada apenas quando curva_medida.json nao existe. Mantida no arquivo
    para que a saida do bloco 1 continue reproduzivel sem o bloco 3.
    """
    cobertura = 1.00 - 0.85 * tau   # 1.00 -> 0.15
    precisao = 0.60 + 0.38 * tau    # 0.60 -> 0.98
    return cobertura, precisao


def curva(tau: float, classe: str | None = None) -> tuple[float, float]:
    """(cobertura, precisao) no limiar tau.

    Se curva_medida.json existe, devolve a MEDICAO do bloco 3 [medido].
    Sem classe, devolve o agregado ponderado por w_c — usado na grade da
    SECAO 5, que e uma visao de operacao inteira. Com classe, devolve a
    curva daquela classe, que e o que a SECAO 7 usa para decidir corte.

    Definicao de cobertura (fixada no bloco 3):
      cobertura_c = volume do canal automatico c / volume real da classe c.
      Fracao DENTRO da classe — por isso comparavel entre classes mesmo com
      score nao comparavel. w_c permanece fora, visivel e rotulado.
    """
    if CURVA_MEDIDA is None:
        return curva_placeholder(tau)

    def interp(pontos):
        taus = [p["tau"] for p in pontos]
        cob = [p["cobertura"] for p in pontos]
        pre = [p["precisao"] if p["precisao"] == p["precisao"] else 0.0 for p in pontos]
        return (float(np.interp(tau, taus, cob)), float(np.interp(tau, taus, pre)))

    if classe is not None:
        return interp(CURVA_MEDIDA["curva"][classe])

    pesos = CURVA_MEDIDA["w_c"]
    cob_ag = sum(pesos[c] * interp(CURVA_MEDIDA["curva"][c])[0] for c in pesos)
    # precisao agregada ponderada pelo VOLUME AUTOMATIZADO de cada canal
    massa = {c: pesos[c] * interp(CURVA_MEDIDA["curva"][c])[0] for c in pesos}
    total = sum(massa.values())
    pre_ag = (sum(massa[c] * interp(CURVA_MEDIDA["curva"][c])[1] for c in pesos) / total
              if total else 0.0)
    return cob_ag, pre_ag


# ==========================================================================
# O MODELO
# ==========================================================================

def fator_ganho(precisao: float, k: float) -> float:
    """Horas liquidas economizadas por ticket automatizado, em unidades de H.

    Acerto  (fracao p)   : a maquina resolve, o humano economiza 1 H.
    Erro    (fracao 1-p) : o humano resolve mesmo assim, e ainda paga a
                           penalidade de retrabalho -> custa k H em vez de 1 H,
                           logo o delta contra a linha de base e -(k-1) H.

        g(p, k) = p - (1 - p) * (k - 1)

    Adimensional. Nao contem V, nao contem H, nao contem horas/FTE.
    """
    return precisao - (1 - precisao) * (k - 1)


def precisao_de_equilibrio(k: float) -> float:
    """Precisao minima para que automatizar nao destrua horas.

    g(p, k) = 0  =>  p* = (k - 1) / k

    Livre de V, de H, de mix e da curva placeholder. Depende SO de k.
    """
    return (k - 1) / k


def horas_liquidas_ano(peso: float, cobertura: float, precisao: float,
                       k: float, h_horas: float, v_ano: int = V_ANO) -> float:
    """Horas humanas liquidas recuperadas por ano numa categoria.

        horas(c) = V * w_c * H * cobertura(c,tau) * g(p(c,tau), k)

    V e H aparecem como produto multiplicativo puro. Ver SECAO 1.
    """
    return v_ano * peso * h_horas * cobertura * fator_ganho(precisao, k)


# --------------------------------------------------------------------------
# Carga: o mix vem do dataset 2, medido
# --------------------------------------------------------------------------

DADOS = achar_pasta_dados()
sys.stdout = Tee(SAIDA)

ops = pd.read_csv(DADOS / "customer_support_tickets.csv")
itsm = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")

contagem = itsm["Topic_group"].value_counts()
mix = (contagem / contagem.sum())          # [dados] dataset 2
CATEGORIAS = list(mix.index)
MAIOR = CATEGORIAS[0]

H_LO = H_MIN_MINUTOS / 60
H_HI = H_MAX_MINUTOS / 60


titulo("BLOCO 1 — BUSINESS CASE PARAMETRICO")
print("""
Este bloco entrega uma FUNCAO, nao um numero. Todo numero abaixo carrega
uma marca de procedencia:

  [dados]                          medido nos arquivos deste repositorio
  [enunciado]                      afirmado pelo briefing do desafio
  [premissa arbitrada, sem fonte]  escolhido por mim, sem respaldo externo
  [convencao do analista]          linha de corte que eu escolhi, nao achado
  [PLACEHOLDER]                    marcador ate o bloco 3 medir

Numero sem marca nao existe neste arquivo.
""")

titulo("REGISTRO DE PROCEDENCIA DOS INSUMOS", "-")
registro = [
    ("V — volume anual", f"{V_ANO:,} tickets/ano",
     "[enunciado] README linha 11"),
    ("w_c — mix por categoria", "8 classes, medido",
     "[dados] dataset 2 (transplante declarado, ver SECAO 1)"),
    ("H — handle time medio", f"{H_MIN_MINUTOS:.0f} a {H_MAX_MINUTOS:.0f} min/ticket",
     "[premissa arbitrada, sem fonte]"),
    ("k — custo do erro", f"{K_MIN:.2f}x a {K_MAX:.2f}x o handle time",
     "[premissa arbitrada, sem fonte]"),
    ("horas/FTE/ano", f"{HORAS_POR_FTE_ANO:,} h",
     "[premissa arbitrada, sem fonte]"),
    ("limiar de materialidade", f"{LIMIAR_FTE:.0f} FTE",
     "[convencao do analista] nao e achado dos dados"),
    ("curva cobertura x precisao",
     "medida por classe" if CURVA_MEDIDA else "forma fechada monotona",
     "[dados] bloco 3, curva_medida.json" if CURVA_MEDIDA
     else "[PLACEHOLDER] substituida pela medicao do bloco 3"),
]
print(f"{'INSUMO':<28} {'VALOR':<30} PROCEDENCIA")
print("-" * 110)
for nome, valor, proc in registro:
    print(f"{nome:<28} {valor:<30} {proc}")


# ==========================================================================
# SECAO 0 — DIVERGENCIA ENTRE BRIEFING E ARQUIVO
# ==========================================================================
titulo("SECAO 0 — O BRIEFING DESCREVE UM DATASET QUE NAO E ESTE")

res = ops["Resolution"].dropna()
print(f"""
O enunciado afirma duas coisas sobre o Dataset 1 que o arquivo contradiz.
As duas juntas — e nao cada uma isolada — determinam de onde pode vir o
volume do business case.

DIVERGENCIA DE TAMANHO
  briefing (linha 45) : "~30.000 registros"
  arquivo             : {len(ops):,} linhas   [dados]
  razao               : {30000 / len(ops):.1f}x

DIVERGENCIA DE NATUREZA
  briefing (linha 45) : "com texto real de descricao e resolucao"
  arquivo             : {len(res):,} resolucoes nao-nulas, {res.nunique():,} valores unicos
                        ({res.nunique() / len(res) * 100:.0f}% de unicidade), {res.str.len().mean():.0f} caracteres em media
  evidencia E6        : nenhuma resolucao se repete, e o texto e faker
                        ("Increase wife television along along need physical.")

CONSEQUENCIA
  A divergencia nao e de contagem, e de natureza: o briefing descreve um
  arquivo com resolucao real, e este arquivo nao tem resolucao real. Logo o
  briefing nao esta descrevendo este arquivo.

  Isso resolve a ambiguidade do "~30.000". A linha 11 diz "a operacao atende
  ~30.000 tickets por ano" e a linha 45 diz "~30.000 registros". Como o
  briefing comprovadamente nao descreve este arquivo, o 30.000 NAO pode ser
  lido como "o arquivo e a operacao anual". So resta a leitura de negocio:
  volume declarado pelo cliente.

  V = {V_ANO:,}/ano entra como [enunciado], nunca como [dados].
  Os {len(ops):,} do arquivo nao sao multiplicados por fator nenhum.

  Os dados dao FORMA. O briefing da ESCALA. Nao se misturam.
""")


# ==========================================================================
# SECAO 1 — O MODELO
# ==========================================================================
titulo("SECAO 1 — O MODELO E A ALGEBRA QUE ELIMINA V E H")

print("""
    horas_liquidas(c, tau, k) =
        V * w_c * H * cobertura(c, tau) * g(p(c, tau), k)

    onde   g(p, k) = p - (1 - p) * (k - 1)

Leitura de g: de cada 100 tickets que a maquina assume, p acertos poupam
1 H cada; os (1-p) erros nao poupam nada E ainda custam (k-1) H de
retrabalho. g e o saldo liquido, em unidades de H, por ticket automatizado.

TRATAMENTO DE V E DE H — e por que nao tem eixo de sensibilidade
""")
print(f"""  V e H entram como produto multiplicativo puro. Nao interagem com tau,
  nao interagem com k, nao interagem com o mix. Dobrar H dobra toda a
  coluna de horas; dobrar V faz o mesmo; nenhum dos dois altera qual
  categoria e maior, nem o sinal do resultado, nem o piso de precisao.

  Dar eixo de sensibilidade a um escalar linear seria encenacao: a "analise"
  produziria uma reta pela origem cuja inclinacao ja esta escrita na formula.
  Entao V e H ficam registrados como escalares e nao como eixos:

     dobrou H  -> dobrou horas e dobrou FTE. Nada mais muda.
     dobrou V  -> idem.

  Os eixos que sobram — os unicos que mudam CONCLUSAO e nao so escala —
  sao tau e k. A grade e essa, e so essa.

O MIX — transplante declarado
  w_c vem do dataset 2 [dados]: service desk INTERNO de TI (HR Support,
  Access, Administrative rights, Internal Project). O Dataset 1 e suporte
  B2C de produto de consumo (Canon EOS, GoPro, Amazon Echo). Nao sao a
  mesma populacao.

  Uso o mix do dataset 2 porque a taxa de automacao so e mensuravel na
  taxonomia dele — o classificador do bloco 3 vai emitir precisao por
  classe NESSAS 8 classes. Ponderar por 'Ticket Type' do dataset 1
  deixaria o modelo internamente incoerente: o numero medido depois nao
  corresponderia as classes ponderadas antes.

  O preco esta declarado: isto e ESTRUTURA IMPORTADA de outra operacao,
  nao o mix desta. Sem fonte para o mix desta operacao.

  O dataset 1 nao entra com peso nenhum. Seu mix por tipo (20.7/20.6/20.0/
  19.4/19.3) e por canal (25.3/25.2/25.0/24.5) e uniforme — evidencia E7,
  sorteio. Canal cai pelo mesmo motivo que tipo: a regua tem que ser a
  mesma. O dataset 1 contribui com esquema, com o achado estrutural do
  CSAT e com a recomendacao de instrumentacao, nao com pesos.
""")

print("MIX APLICADO — w_c  [dados] dataset 2, transplante declarado")
tab_mix = pd.DataFrame({
    "tickets": contagem,
    "w_c %": (mix * 100).round(1),
})
print(tab_mix.to_string())
print(f"\n  desbalanceamento: {contagem.max() / contagem.min():.1f}x  [dados]")


# ==========================================================================
# SECAO 2 — RESULTADO LIVRE DE PREMISSA: O PISO DE PRECISAO
# ==========================================================================
titulo("SECAO 2 — PISO DE PRECISAO p*(k)  [resultado em forma fechada]")

print("""
Ao expressar o custo do erro como multiplo adimensional k do handle time —
e nao como uma grandeza propria em minutos, que seria mais uma premissa
inventada — V, H e o mix saem inteiros da equacao do SINAL:

    g(p, k) = 0   <=>   p* = (k - 1) / k

Este e o unico numero desta entrega que nao depende de premissa nenhuma
de escala. Nao depende de V [enunciado], nao depende de H [arbitrado], nao
depende de horas/FTE [arbitrado] e nao depende da curva [PLACEHOLDER].
Depende so de k.

Leitura: abaixo de p*, automatizar aquela classe DESTROI horas. O retrabalho
gerado pelos erros supera o trabalho poupado pelos acertos. Nao e questao de
ROI magro — e sinal negativo.
""")

print(f"{'k (custo do erro)':<22} {'p* minima':<14} leitura")
print("-" * 78)
for k in K_GRADE:
    p_estrela = precisao_de_equilibrio(k)
    leitura = {
        1.25: "erro quase de graca: quase toda classe passa",
        1.50: "erro custa 50% a mais: piso ainda folgado",
        2.00: "errar custa o dobro: precisao tem que passar de 50%",
        2.50: "aperta: 60% de precisao ja e o minimo",
        3.00: "errar custa 3 chamados: 2 em 3 tem que estar certo",
        4.00: "punitivo: 3 em 4 certos so pra empatar",
    }[k]
    print(f"{k:<22.2f} {p_estrela * 100:>6.1f}%        {leitura}")

print("""
CONSEQUENCIA OPERACIONAL — este e o entregavel do bloco pro bloco 3:

  O classificador nao precisa ser "bom". Ele precisa entregar, POR CLASSE e
  no limiar escolhido, precisao acima de p*(k). Classe que nao alcanca p*
  nao entra na automacao — e essa e a resposta com numero para a pergunta
  do enunciado sobre o que NAO automatizar.

  Note o que isso faz com a metrica: o que decide nao e acuracia media nem
  F1 agregado. E precisao por classe contra um piso. Um F1 alto conquistado
  com recall nas classes grandes pode esconder precisao abaixo de p* nas
  pequenas, e ai a automacao dessas classes entra com sinal negativo.
""")


# ==========================================================================
# SECAO 3 — DECISAO A E SUA INVARIANCIA
# ==========================================================================
titulo("SECAO 3 — DECISAO A: O QUE A ALGEBRA GARANTE E O QUE ELA NAO GARANTE")

print(f"""
DECISAO NOMEADA
  O Diretor de Operacoes decide em que categoria a automacao entra
  primeiro. Decisao de sequenciamento, nao de investimento.

PERGUNTA DE SENSIBILIDADE
  Em que ponto da faixa de handle time essa decisao vira?

RESPOSTA, E ELA TEM DUAS METADES QUE PRECISAM SER LIDAS JUNTAS:

  A invariancia e ao NIVEL do handle time. Nao e a RAZAO entre categorias.
  E quem decide por onde comecar e a razao, nao o nivel.

  METADE 1 — o nivel cancela, e cancela por algebra.

    Sob handle time uniforme, H e escalar puro multiplicando todas as
    categorias pelo mesmo valor:

        horas(c) = [ V * H * cobertura * g ] * w_c
                    \\_______ constante _______/

    O colchete nao depende de c. A ordem entre categorias e portanto a
    ordem de w_c, qualquer que seja H. Nao e que a faixa de {H_MIN_MINUTOS:.0f} a {H_MAX_MINUTOS:.0f} min
    seja estreita demais pra virar a decisao — e que NENHUMA faixa vira.
    A premissa poderia estar errada por uma ordem de grandeza e a resposta
    seria a mesma. Errar o nivel de H nao custa nada aqui.

  METADE 2 — a razao NAO cancela, e e ela que manda.

    A premissa de uniformidade e arbitrada e quase certamente falsa: nao
    ha motivo para um chamado de Administrative rights custar o mesmo que
    um de Hardware. Assim que H varia por categoria, ele sai do colchete
    e entra no termo que varia:

        horas(c) = [ V * cobertura * g ] * w_c * H_c
                    \\____ constante ____/    \\_ varia _/

    A ordem passa a ser a de (w_c * H_c). O nivel continua cancelando; a
    razao H_c/H_c' passa a decidir tudo. Ou seja:

        a decisao A e imune a errar QUANTO custa um ticket,
        e totalmente exposta a errar QUAIS tickets custam mais.

    A SECAO 4 quantifica exatamente essa exposicao. Ela nao e uma ressalva
    que retrata esta secao — e a outra metade da mesma resposta, e o
    motivo de este bloco nao publicar ranking (SECAO 6).

VERIFICACAO DA METADE 1
  Se o nivel cancela, a participacao percentual de cada categoria nas
  horas totais tem que ser identica em qualquer H. Medido nos dois
  extremos da faixa arbitrada e nos dois extremos de k:
""")

cob_ref, prec_ref = curva(0.50)


def participacoes(h_horas: float, k: float) -> pd.Series:
    """Fracao de cada categoria nas horas liquidas totais.

    Com a curva medida do bloco 3, cobertura e precisao deixam de ser
    constantes entre categorias, entao a curva e consultada POR CLASSE.
    """
    def par(c):
        cob_c, pre_c = curva(0.50, classe=c) if CURVA_MEDIDA else (cob_ref, prec_ref)
        return horas_liquidas_ano(mix[c], cob_c, pre_c, k, h_horas)
    s = pd.Series({c: par(c) for c in CATEGORIAS})
    return s / s.sum()


base = participacoes(H_LO, 1.25)
desvio_max = max(
    (participacoes(h, k) - base).abs().max()
    for h, k in [(H_HI, 1.25), (H_LO, 4.00), (H_HI, 4.00)]
)
print(f"    desvio maximo absoluto de participacao entre os cenarios: "
      f"{desvio_max * 100:.3f} pp")
print("    (zero por construcao algebrica — nao e coincidencia numerica)")
print("""
  Nao ha tabela de ordem aqui de proposito. Imprimir a ordem seria imprimir
  o ranking que a SECAO 6 explica por que este bloco nao publica.
""")


# ==========================================================================
# SECAO 4 — TESTE DE SEGUNDA ORDEM
# ==========================================================================
titulo("SECAO 4 — QUANTIFICACAO DA METADE 2: O QUE TERIA QUE SER VERDADE")

print(f"""
Esta secao mede a exposicao anunciada na METADE 2 da SECAO 3. A pergunta
certa nao e "a conclusao aguenta a faixa de H?" — a METADE 1 ja respondeu
que sim, e por algebra. A pergunta que sobra e sobre a razao:

  quanto o handle time de uma categoria teria que ser MAIOR que o de
  {MAIOR} para que ela passasse na frente?

    w_c * H_c > w_maior * H_maior   <=>   H_c / H_maior > w_maior / w_c

A razao necessaria depende so do mix [dados]. Nao depende de H, de V, de k
nem da curva placeholder — e o mesmo tipo de resultado da SECAO 2: forma
fechada, livre de escala.

(A tabela abaixo esta ordenada por w_c, que ja e publico como [dados] na
SECAO 1. Ela nao ordena categorias por horas recuperaveis — ver SECAO 6.)
""")

w_maior = mix[MAIOR]
linhas = []
for c in CATEGORIAS[1:]:
    razao_necessaria = w_maior / mix[c]
    if razao_necessaria < 1.5:
        veredito = "PLAUSIVEL — a ordem aqui nao esta protegida"
    elif razao_necessaria < 3.0:
        veredito = "possivel, exigiria diferenca grande"
    else:
        veredito = "implausivel — ordem robusta"
    linhas.append({
        "categoria": c,
        "w_c %": round(mix[c] * 100, 1),
        f"H_c / H_{MAIOR.split()[0]} necessario": f"{razao_necessaria:.2f}x",
        "veredito": veredito,
    })
print(pd.DataFrame(linhas).to_string(index=False))

razao_segundo = w_maior / mix[CATEGORIAS[1]]
print(f"""
LEITURA — a exposicao e assimetrica, e e isso que orienta a acao:

  O primeiro lugar NAO esta protegido. Basta {CATEGORIAS[1]} custar
  {razao_segundo:.2f}x o handle time de {MAIOR} para assumir a lideranca — uma
  violacao de {(razao_segundo - 1) * 100:.0f}% da premissa de uniformidade, que e perfeitamente
  plausivel em qualquer operacao real.

  Ja o fundo da lista esta protegido: inverter as classes pequenas exigiria
  razoes de 5x a 8x, que seriam visiveis a olho nu em qualquer operacao.

  Traduzindo pro Diretor: a premissa de handle time uniforme e barata para
  decidir o que NAO priorizar, e cara para decidir o que priorizar em
  primeiro lugar. Se so um campo for instrumentado, que seja
  handle_time_seconds por categoria (Onda 1 da PARTE 3 do bloco 0) — e a
  SECAO 4 e a justificativa quantitativa desse pedido.
""")


# ==========================================================================
# SECAO 5 — DECISAO B: FTE
# ==========================================================================
titulo("SECAO 5 — DECISAO B: 'ISSO E CONVERSA DE HEADCOUNT OU E RUIDO?'")

print(f"""
DECISAO NOMEADA
  O Diretor decide se a capacidade liberada justifica realocar gente, ou se
  o ganho e pequeno demais para mudar qualquer coisa no quadro.

POR QUE FTE E NAO R$
  Converter para dinheiro exigiria inventar custo por hora de agente e
  custo de construir a solucao — duas premissas arbitradas NOVAS empilhadas
  sobre as que ja existem. Premissa sobre premissa vira ficcao composta.
  FTE para na ultima fronteira que o modelo alcanca sem inventar dinheiro;
  quem tem o custo/hora real multiplica em dois segundos.

    FTE_liberado = horas_liquidas_totais / {HORAS_POR_FTE_ANO:,}

  O divisor {HORAS_POR_FTE_ANO:,} h/ano e [premissa arbitrada, sem fonte].
  E divisor linear puro: se a operacao usa 1.500 ou 2.000, os FTE mudam
  proporcionalmente e nenhuma conclusao de sinal ou de ordem se altera.

  O limiar de {LIMIAR_FTE:.0f} FTE e [convencao do analista]. Nao e achado dos dados,
  nao esta em arquivo nenhum: e a linha que eu escolhi para separar
  "materialidade" de "ruido de arredondamento". Quem le pode move-la.

GRADE DE SENSIBILIDADE — os dois eixos que sobraram: tau x k
  Cada celula responde: qual handle time faz o ganho cruzar {LIMIAR_FTE:.0f} FTE?

    H* = horas_por_FTE / (V * cobertura(tau) * g(p(tau), k))

  Celula em minutos. 'nunca' = g <= 0, automatizar destroi horas em qualquer
  H (precisao abaixo do piso da SECAO 2). '> faixa' = so cruzaria com handle
  time acima de {H_MAX_MINUTOS:.0f} min, fora da faixa arbitrada.
""")

grade = []
for tau in TAU_GRADE:
    cob, prec = curva(tau)
    linha = {"tau": f"{tau:.2f}", "cob": f"{cob * 100:.0f}%", "prec": f"{prec * 100:.0f}%"}
    for k in K_GRADE:
        g = fator_ganho(prec, k)
        if g <= 0:
            linha[f"k={k:.2f}"] = "nunca"
        else:
            h_estrela_min = HORAS_POR_FTE_ANO / (V_ANO * cob * g) * 60
            if h_estrela_min > H_MAX_MINUTOS:
                linha[f"k={k:.2f}"] = "> faixa"
            else:
                linha[f"k={k:.2f}"] = f"{h_estrela_min:.0f} min"
    grade.append(linha)

ETIQ = "[medido, bloco 3]" if CURVA_MEDIDA else "[PLACEHOLDER na curva]"
print(f"H* — handle time que faz o ganho cruzar 1 FTE   {ETIQ}")
print(pd.DataFrame(grade).to_string(index=False))

ABERTURA_GRADE = (
    "ANTES DE TUDO: os valores das celulas acima vem da curva MEDIDA no bloco 3\n"
    "  e podem ser citados. Os itens abaixo marcam o que era previsao minha e o\n"
    "  que a medicao confirmou ou desmentiu."
) if CURVA_MEDIDA else (
    "ANTES DE TUDO: os VALORES das celulas acima nao sao resultado. Eles saem da\n"
    "  curva placeholder, que eu escolhi, e vao mudar quando o bloco 3 medir a\n"
    "  curva real por classe."
)

print(f"""
LEITURA DA GRADE — separando o que e estrutura do que e medicao

  {ABERTURA_GRADE}

  1. O OTIMO INTERIOR EM TAU — previsto, e DESMENTIDO pela medicao.
     Eu escrevi que este item era o unico "estrutural" da grade: que o
     minimo de H* nao ficaria nem em tau baixo nem em tau alto, porque
     cobertura e precisao se movem em sentidos opostos em qualquer
     classificador com limiar.
     A grade medida nao tem otimo interior. O minimo esta na BORDA, em
     tau = 0, e H* so cresce a partir dali.
     POR QUE eu errei: o argumento do trade-off pressupoe que em tau baixo
     a precisao seja ruim o bastante para o retrabalho pesar. Nao e o caso
     aqui — a precisao ja comeca em 87%, muito acima de p*(k=4) = 75%.
     Com o termo de erro pequeno desde o inicio, subir tau so custa
     cobertura e nao compra nada. O trade-off existe, mas esta inteiro do
     lado errado do joelho da curva.
     Registro isto como o item que mais falhou desta grade justamente
     porque era o unico que eu tinha declarado imune a medicao.

  2. O mecanismo do 'nunca' — e o que a medicao fez com ele.
     Quando a precisao cai abaixo do piso p*(k) da SECAO 2, nenhuma
     quantidade de handle time salva: a celula vira 'nunca'. Com a curva
     placeholder, colunas inteiras de k alto morriam assim. Com a curva
     MEDIDA, nenhuma celula e 'nunca': a precisao real fica entre 87% e 99%,
     acima de p*(k=4)=75% em toda a faixa. A previsao de que k alto mataria
     classes estava errada — nao porque o mecanismo seja falso, mas porque
     eu subestimei a precisao alcancavel com tfidf+linear nesta base.

  3. O cruzamento de {LIMIAR_FTE:.0f} FTE cai dentro da faixa de handle
     time arbitrada na maior parte da grade util. O que se pode afirmar
     hoje nao e onde ele cai, e sim que ele E sensivel a premissa de
     handle time, ao contrario da decisao A. Essa assimetria entre as duas
     decisoes e estrutural; a posicao do cruzamento nao e.
""")

print("FAIXA DE FTE LIBERADO NOS EXTREMOS DA FAIXA DE H")
print(f"  (tau=0.50 {ETIQ}; H de {H_MIN_MINUTOS:.0f} a {H_MAX_MINUTOS:.0f} min "
      f"[premissa arbitrada, sem fonte])\n")

cob50, prec50 = curva(0.50)
faixa = []
for k in K_GRADE:
    g = fator_ganho(prec50, k)
    fte_lo = V_ANO * H_LO * cob50 * g / HORAS_POR_FTE_ANO
    fte_hi = V_ANO * H_HI * cob50 * g / HORAS_POR_FTE_ANO
    horas_lo = V_ANO * H_LO * cob50 * g
    horas_hi = V_ANO * H_HI * cob50 * g
    if g <= 0:
        faixa.append({"k": f"{k:.2f}", "g(p,k)": f"{g:+.2f}",
                      "horas/ano": "negativo", "FTE liberado": "negativo",
                      f"cruza {LIMIAR_FTE:.0f} FTE?": "nunca"})
    else:
        faixa.append({
            "k": f"{k:.2f}",
            "g(p,k)": f"{g:+.2f}",
            "horas/ano": f"{round(horas_lo, -2):,.0f} a {round(horas_hi, -2):,.0f}",
            "FTE liberado": f"{fte_lo:.1f} a {fte_hi:.1f}",
            f"cruza {LIMIAR_FTE:.0f} FTE?": "sim, dentro da faixa" if fte_hi >= LIMIAR_FTE >= fte_lo
            else ("sim, em toda a faixa" if fte_lo >= LIMIAR_FTE else "nao cruza na faixa"),
        })
print(pd.DataFrame(faixa).to_string(index=False))

print("""
REGRA DE ARREDONDAMENTO APLICADA
  Horas em centenas, FTE em uma casa, e sempre em FAIXA — nunca ponto.
  Insumo arbitrado nao produz saida precisa. Um numero como "2.847,3 horas
  economizadas por ano" em cima de um handle time chutado nao e mais
  informativo que "2.800 a 6.000"; e so mais facil de acreditar, o que e
  exatamente o problema.
""")


# ==========================================================================
# SECAO 6 — O QUE ESTE BLOCO NAO ENTREGA
# ==========================================================================
titulo("SECAO 6 — O QUE ESTE BLOCO NAO ENTREGA (e por que)")

print(f"""
NAO HA RANKING DE PRIORIDADE NESTA SAIDA. Nenhuma tabela deste arquivo
ordena categorias por horas recuperaveis. A omissao e deliberada e vale
conferir: as unicas tabelas ordenadas aqui sao o mix (SECAO 1) e as razoes
de inversao (SECAO 4), ambas ordenadas por w_c, que e [dados] cru.

A METADE 1 da SECAO 3 mostrou que, sob handle time uniforme, a ordem das
categorias por horas recuperaveis E exatamente a ordem de w_c. Publicar
esse ranking seria publicar o histograma do dataset 2 com outro nome:
{MAIOR} apareceria em primeiro lugar porque {MAIOR} e {mix[MAIOR] * 100:.1f}% da base
[dados]. Isso e contagem, nao achado. Renomear uma contagem de
'priorizacao' e o tipo de coisa que enche slide e nao sustenta pergunta.

E a METADE 2 mostrou o outro motivo, independente do primeiro: mesmo que
alguem quisesse publicar essa ordem, ela viraria com {razao_segundo:.2f}x de diferenca
de handle time entre as duas primeiras. Nao ha ranking defensavel aqui —
nem por falta de conteudo, nem por falta de robustez.

O QUE FALTA PARA O RANKING NASCER DE VERDADE

  A formula tem quatro termos por categoria e hoje so um varia entre elas:

      horas(c) = V * H * w_c * cobertura(c,tau) * g(p(c,tau), k)
                         ----   --------------------------------
                      varia [dados]    constante [PLACEHOLDER]

  cobertura e precisao estao constantes entre categorias porque ainda nao
  foram medidas. Quando o bloco 3 rodar, elas passam a variar por classe —
  e e ai que o ranking ganha conteudo, porque separabilidade e volume sao
  coisas diferentes:

    - classe grande e mal separavel (precisao abaixo de p*) pode cair para
      fora da automacao mesmo liderando o volume;
    - classe pequena e limpa pode subir, porque cobertura alta com precisao
      alta rende g proximo de 1 onde a classe grande rende g negativo.

  Ou seja: o bloco 3 nao ajusta o ranking na margem. Ele e a unica fonte de
  desempate que existe, porque hoje as duas unicas coisas que diferenciam
  categorias sao volume [dados] e uma constante [PLACEHOLDER].

GANCHO PARA O BLOCO 3 — a interface esta fechada
  1. medir, por classe, a curva cobertura x precisao em funcao de tau
     (substituir curva_placeholder(); nada mais do modelo muda)
  2. comparar a precisao de cada classe contra o piso p*(k) da SECAO 2
  3. escolher tau por classe, nao global — o otimo e por classe
  4. as classes que nao alcancam p* em nenhum tau sao a resposta com numero
     para 'o que NAO automatizar'
  5. so entao publicar ranking

RESUMO DO QUE JA ESTA DECIDIDO E NAO DEPENDE DO BLOCO 3
  - o piso de precisao p*(k) — forma fechada, livre de V, H, mix e curva
  - a invariancia da decisao A ao handle time — algebrica
  - o limite dessa invariancia: {razao_segundo:.2f}x inverte o primeiro lugar
  - que a decisao B E sensivel a premissa, ao contrario da A
""")

if CURVA_MEDIDA is None:
    print("  STATUS: curva ainda nao medida — ranking permanece nao publicado.")
else:
    print("""  STATUS: curva MEDIDA (bloco 3). Os cinco passos acima foram cumpridos,
  entao o ranking deixa de ser contagem disfarcada e passa a ser publicavel.
  Ele aparece abaixo pela primeira vez nesta entrega.
""")
    titulo("SECAO 6B — RANKING, AGORA QUE HA DESEMPATE MEDIDO", "-")
    K_REF = 2.00
    piso = precisao_de_equilibrio(K_REF)
    H_MEIO = (H_LO + H_HI) / 2
    linhas_rk = []
    for c in CATEGORIAS:
        melhor = None
        for tau in [t / 100 for t in range(0, 100, 5)]:
            cob_c, pre_c = curva(tau, classe=c)
            if cob_c <= 0:
                continue
            h = horas_liquidas_ano(mix[c], cob_c, pre_c, K_REF, H_MEIO)
            if melhor is None or h > melhor[0]:
                melhor = (h, tau, cob_c, pre_c)
        h, tau, cob_c, pre_c = melhor
        linhas_rk.append({
            "categoria": c,
            "w_c %": round(mix[c] * 100, 1),
            "pos VOLUME": CATEGORIAS.index(c) + 1,
            "tau otimo": round(tau, 2),
            "cobertura_c": round(cob_c, 3),
            "precisao_c": round(pre_c, 3),
            "passa p*": "sim" if pre_c >= piso else "NAO",
            "horas/ano": round(h, -2),
        })
    rk = pd.DataFrame(linhas_rk).sort_values("horas/ano", ascending=False).reset_index(drop=True)
    rk.insert(0, "pos HORAS", range(1, len(rk) + 1))
    print(f"  k = {K_REF:.2f}  ->  p* = {piso:.0%}   |   H = ponto medio da faixa arbitrada")
    print("  tau escolhido POR CLASSE, maximizando horas liquidas [medido, bloco 3]")
    print("  horas em centenas: insumo arbitrado nao produz saida precisa\n")
    print(rk.to_string(index=False))
    inversoes = int((rk["pos HORAS"].values != rk["pos VOLUME"].values).sum())
    fora = [l["categoria"] for l in linhas_rk if l["passa p*"] == "NAO"]
    print(f"""
  posicoes que mudaram contra o ranking de volume: {inversoes} de {len(rk)}
  classes que NAO passam p*({K_REF:.2f}): {fora if fora else 'nenhuma'}
""")
    if inversoes == 0:
        print("""  RESULTADO: a medicao NAO desempatou nada. O ranking por horas recuperaveis
  saiu identico ao ranking por volume, posicao por posicao.

  Isso contraria o que a SECAO 6 esperava. Ela previa que a separabilidade
  variaria bastante entre classes e reordenaria a lista — 'classe grande e
  mal separavel pode cair para fora mesmo liderando o volume'. Nao caiu:
  todas as oito passam p*(k=2), e a cobertura otima fica entre 76% e 96% em
  todas. Com precisao e cobertura parecidas entre classes, w_c volta a ser o
  unico termo que varia, e o ranking colapsa de novo no histograma.

  A consequencia e desconfortavel e fica registrada: a recusa da SECAO 6 em
  publicar ranking estava CERTA, e continua certa depois da medicao. Este
  ranking nao carrega informacao alem da contagem — ele so agora pode ser
  exibido com essa afirmacao provada em vez de suposta. O valor da medicao
  do bloco 3 nao esta em reordenar prioridade; esta em mostrar que nao ha
  o que reordenar, e em fixar tau por classe, que a contagem nao daria.""")
    else:
        print(f"""  RESULTADO: a medicao reordenou {inversoes} das {len(rk)} posicoes. A diferenca
  contra o ranking de volume e exatamente o que o bloco 3 acrescentou, e e o
  motivo de este ranking existir e o anterior nao.""")

# ==========================================================================
# SECAO 7 — PREVISOES REGISTRADAS
# ==========================================================================
titulo("SECAO 7 — PREVISOES REGISTRADAS ANTES DE MEDIR")

p_estrela_2 = precisao_de_equilibrio(2.00) * 100
razao_acesso = contagem["Access"] / contagem["Administrative rights"]

print(f"""
Estas sao PREVISOES, nao achados. Estao aqui porque so podem ser escritas
agora: depois que o bloco 3 rodar, qualquer coisa que eu escrever sobre o
comportamento do classificador ja sera posterior a medicao e nao valera
nada como evidencia.

O commit que carrega este arquivo e datado e anterior ao bloco 3. Se as
previsoes se confirmarem, o historico prova que foram feitas antes. Se
errarem, o bloco 3 registra o erro e a razao dele — e isso vale quase
tanto, porque mostra em que ponto a leitura de dominio falhou.

Cada previsao vem com a base que a sustenta e com o criterio que a
falsifica. Previsao sem criterio de falsificacao e horoscopo.

Referencia usada em todas: p*(k=2.00) = {p_estrela_2:.0f}% [SECAO 2, forma fechada].


P1. Miscellaneous ficara ABAIXO de p* apesar de ser a 4a maior classe
    forca da base: ALTA

    ENUNCIADO
      A precisao de Miscellaneous nao alcancara {p_estrela_2:.0f}% em nenhum tau que
      preserve cobertura util, e a classe ficara de fora da automacao
      mesmo respondendo por {mix['Miscellaneous'] * 100:.1f}% do volume ({contagem['Miscellaneous']:,} tickets) [dados].

    BASE
      As outras sete classes sao definidas por CONTEUDO: cada nome
      descreve um dominio (Hardware, Storage, Purchase, Access...).
      Miscellaneous e definida por EXCLUSAO — e o balde do que nao coube
      nas outras. Uma classe assim nao tem vocabulario proprio: seus
      documentos nao compartilham tema, compartilham apenas a ausencia de
      pertencimento aos outros rotulos. Nao ha regiao coerente no espaco
      de features para o modelo encontrar, porque a regiao e o complemento
      de todas as outras.
      Isso e propriedade da construcao do rotulo, nao do classificador —
      por isso a base e alta e nao depende de qual modelo o bloco 3 use.

    O QUE FALSIFICA
      Precisao de Miscellaneous >= {p_estrela_2:.0f}% em algum tau com cobertura acima
      de 10% da classe.

    POR QUE IMPORTA
      Se confirmada, e o caso que demonstra com numero a tese da SECAO 6:
      VOLUME NAO DECIDE AUTOMACAO. A 4a maior classe da base sai de fora
      por separabilidade, nao por tamanho — e nenhum ranking construido
      sobre contagem enxergaria isso.


P2. Administrative rights sera absorvida por Access, e nao o contrario
    forca da base: ALTA

    ENUNCIADO
      Na matriz de confusao, o fluxo Administrative rights -> Access sera
      substancialmente maior que o fluxo Access -> Administrative rights.
      A assimetria e a previsao; a existencia da confusao sozinha nao.

    BASE
      Duas causas independentes apontam para o MESMO lado:
      (a) semantica — conceder direito administrativo E um caso
          particular de conceder acesso. As classes nao sao disjuntas no
          conteudo; uma e quase subconjunto da outra. Confusao mutua ja
          seria esperada so por isso.
      (b) prior — Access tem {contagem['Access']:,} tickets contra {contagem['Administrative rights']:,} de
          Administrative rights, razao de {razao_acesso:.1f}x [dados]. Diante de um
          documento ambiguo, um classificador que aprendeu o prior
          resolve o empate a favor da classe majoritaria.
      A semantica cria a ambiguidade, o desbalanceamento decide para onde
      ela cai. E o que torna a previsao direcional e nao apenas "essas
      duas se confundem".

    O QUE FALSIFICA
      Matriz de confusao aproximadamente simetrica entre as duas, ou
      fluxo maior no sentido Access -> Administrative rights.

    POR QUE IMPORTA
      Se confirmada, Administrative rights nao precisa de mais dados nem
      de modelo melhor: precisa de uma decisao de TAXONOMIA. Duas classes
      que se sobrepoem no conteudo ou viram uma, ou ganham regra de
      desempate fora do texto. Isso e conclusao de processo, nao de ML.


P3. Hardware passara de p* com folga
    forca da base: MEDIA — a mais fraca das tres, registrada como tal

    ENUNCIADO
      A precisao de Hardware ficara acima de {p_estrela_2:.0f}% ja em tau baixo,
      mantendo cobertura alta.

    BASE
      Vocabulario concreto e de baixa ambiguidade: nomes de dispositivo e
      verbos de falha fisica. Com stopwords removidas e 292 caracteres de
      media [dados, bloco 0], o sinal restante e majoritariamente
      substantivo — que e o que favorece uma classe de dominio material.
      Somado a isso, o prior de {mix['Hardware'] * 100:.1f}% joga a favor.

    POR QUE A BASE E MAIS FRACA
      "Vocabulario concreto" e julgamento meu sobre o dominio, nao
      medicao. Nao inspecionei o texto de Hardware antes de escrever
      isto. P1 e P2 se apoiam em propriedades verificaveis da construcao
      dos rotulos e do desbalanceamento; P3 se apoia numa expectativa
      sobre linguagem. Registro assim para nao contar um acerto barato
      junto com dois caros.

    O QUE FALSIFICA
      Precisao de Hardware abaixo de {p_estrela_2:.0f}% em todo tau com cobertura util.


P4. (COROLARIO de P1, nao previsao independente)

    Se P1 se confirmar, o ranking por horas recuperaveis apos o bloco 3
    NAO sera igual ao ranking por volume — a 4a posicao ja cai fora.
    Registro como corolario e nao como previsao propria justamente para
    nao inflar a contagem de acertos: ele nao carrega informacao alem de
    P1 e nao deve ser contado como um segundo acerto se P1 der certo.


NOTA DE HONESTIDADE SOBRE ESTA SECAO
  Acertar P1, P2 e P3 nao valida o modelo das SECOES 1 a 5. Valida a
  leitura de dominio que sustenta a escolha do que medir. Sao coisas
  diferentes e nao devem ser somadas na conclusao final.
""")

titulo("FIM — BLOCO 1")
print(f"saida salva em: {SAIDA}")
sys.stdout.flush()
