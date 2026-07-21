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
  SECAO 3 — decisao A (prioridade) e sua invariancia ao handle time
  SECAO 4 — teste de segunda ordem: o que teria que ser verdade pra inverter
  SECAO 5 — decisao B (FTE) e o ponto de cruzamento na faixa
  SECAO 6 — o que este bloco NAO entrega, e o gancho pro bloco 3

O que este script NAO entrega, por decisao explicita: ranking de prioridade.
Ver SECAO 6.

Uso:
    python 02_business_case.py

Dependencias: pandas  (ver requirements.txt)
Saida: escreve em stdout e em 02_business_case_saida.txt (mesmo diretorio).
"""

import io
import sys
from pathlib import Path

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


def curva_placeholder(tau: float) -> tuple[float, float]:
    """[PLACEHOLDER] Retorna (cobertura, precisao) para um dado tau.

    Substituir pela curva medida por classe no bloco 3. A interface e esta:
    tau -> (cobertura, precisao). Nada mais do modelo precisa mudar.
    """
    cobertura = 1.00 - 0.85 * tau   # 1.00 -> 0.15
    precisao = 0.60 + 0.38 * tau    # 0.60 -> 0.98
    return cobertura, precisao


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
    ("curva cobertura x precisao", "forma fechada monotona",
     "[PLACEHOLDER] substituida pela medicao do bloco 3"),
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
titulo("SECAO 3 — DECISAO A: 'POR ONDE EU COMECO?'")

print("""
DECISAO NOMEADA
  O Diretor de Operacoes olha o numero e decide em que categoria a
  automacao entra primeiro. Decisao de sequenciamento, nao de investimento.

PERGUNTA DE SENSIBILIDADE
  Em que ponto da faixa de handle time essa decisao vira?

RESPOSTA: em nenhum. E a razao e estrutural, nao e a faixa ser estreita.

  Sob a premissa de handle time uniforme entre categorias, H e escalar puro
  multiplicando TODAS as categorias pelo mesmo valor:

      horas(c) = [V * H * cobertura * g] * w_c
                  \\________ constante ________/

  O colchete e identico para toda categoria. A ordem entre categorias e
  portanto a ordem de w_c, qualquer que seja H. H nao encolhe a diferenca
  nem inverte par nenhum: ele cancela.

  Nao e que a faixa {H_MIN}-{H_MAX} min seja estreita demais pra virar a
  decisao. E que NENHUMA faixa vira, inclusive faixas absurdas. A premissa
  de handle time nao e carregadora para a decisao A. Ela poderia estar
  errada por uma ordem de grandeza sem alterar a resposta.

DEMONSTRACAO NUMERICA (ordem nos dois extremos da faixa e nos extremos de k)
""".replace("{H_MIN}", f"{H_MIN_MINUTOS:.0f}").replace("{H_MAX}", f"{H_MAX_MINUTOS:.0f}"))

cob_ref, prec_ref = curva_placeholder(0.50)
cenarios = [
    ("H=3min,  k=1.25", H_LO, 1.25),
    ("H=30min, k=1.25", H_HI, 1.25),
    ("H=3min,  k=4.00", H_LO, 4.00),
    ("H=30min, k=4.00", H_HI, 4.00),
]
ordens = {}
for rotulo, h, k in cenarios:
    serie = pd.Series(
        {c: horas_liquidas_ano(mix[c], cob_ref, prec_ref, k, h) for c in CATEGORIAS}
    ).sort_values(ascending=False)
    ordens[rotulo] = list(serie.index)

comp = pd.DataFrame({rot: ordem for rot, ordem in ordens.items()})
comp.index = [f"{i + 1}o" for i in range(len(comp))]
print(comp.to_string())

todas_iguais = all(o == ordens[cenarios[0][0]] for o in ordens.values())
print(f"\n  ordens identicas nos quatro cenarios: {todas_iguais}")
print("  (identicas por construcao algebrica, nao por coincidencia numerica)")

print("""
  Vale registrar o que essa invariancia NAO significa. Ela nao diz que a
  ordem esta certa — diz que a ordem nao depende da premissa de handle
  time. Se a ordem estiver errada, sera por outro motivo, e o teste da
  SECAO 4 mostra qual.
""")


# ==========================================================================
# SECAO 4 — TESTE DE SEGUNDA ORDEM
# ==========================================================================
titulo("SECAO 4 — TESTE DE SEGUNDA ORDEM: O QUE TERIA QUE SER VERDADE")

print(f"""
A SECAO 3 vale sob a premissa de que o handle time e UNIFORME entre
categorias. Essa premissa e arbitrada e provavelmente falsa: nao ha razao
para um chamado de Administrative rights custar o mesmo que um de Hardware.

Entao a pergunta certa nao e "a conclusao aguenta a faixa de H?" — ja
sabemos que sim. E: quanto o handle time de uma categoria menor teria que
ser MAIOR que o de {MAIOR} para inverter a ordem?

    w_c * H_c > w_maior * H_maior   <=>   H_c / H_maior > w_maior / w_c

A razao necessaria depende so do mix [dados]. Nao depende de H, de V, de k
nem da curva placeholder.
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
LEITURA — e aqui a invariancia da SECAO 3 tem um limite honesto:

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
    cob, prec = curva_placeholder(tau)
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

print("H* — handle time que faz o ganho cruzar 1 FTE   [PLACEHOLDER na curva]")
print(pd.DataFrame(grade).to_string(index=False))

print(f"""
LEITURA DA GRADE

  1. Existe interior otimo em tau. Nem tau baixo (cobertura alta, precisao
     ruim, muito retrabalho) nem tau alto (precisao alta, cobertura minima,
     poucos tickets tocados) minimizam H*. O melhor ponto fica no meio — e
     achar esse ponto por classe e exatamente o trabalho do bloco 3.

  2. As colunas de k alto morrem por cima. Quando a precisao fica abaixo do
     piso p*(k) da SECAO 2, nenhuma quantidade de handle time salva: a
     celula e 'nunca', nao um numero grande. Isso e o modelo se recusando a
     virar positivo por forca bruta de escala — que era o objetivo de ter
     o termo de erro.

  3. O cruzamento de {LIMIAR_FTE:.0f} FTE cai DENTRO da faixa de handle time arbitrada
     na maior parte da grade util. Ou seja: a decisao B, ao contrario da
     decisao A, E sensivel a premissa. Aqui a premissa e carregadora e o
     texto tem que dizer isso.
""")

print("FAIXA DE FTE LIBERADO NOS EXTREMOS DA FAIXA DE H")
print(f"  (tau=0.50 [PLACEHOLDER]; H de {H_MIN_MINUTOS:.0f} a {H_MAX_MINUTOS:.0f} min "
      f"[premissa arbitrada, sem fonte])\n")

cob50, prec50 = curva_placeholder(0.50)
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
NAO HA RANKING DE PRIORIDADE NESTA SAIDA. A omissao e deliberada.

A SECAO 3 provou que, sob handle time uniforme, a ordem das categorias por
horas recuperaveis E a ordem de w_c. Publicar esse ranking agora seria
publicar o histograma do dataset 2 com outro nome: {MAIOR} apareceria em
primeiro lugar porque {MAIOR} e {mix[MAIOR] * 100:.1f}% da base [dados]. Isso e
contagem, nao achado. Renomear uma contagem de 'priorizacao' e o tipo de
coisa que enche slide e nao sustenta pergunta.

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

titulo("FIM — BLOCO 1")
print(f"saida salva em: {SAIDA}")
sys.stdout.flush()
