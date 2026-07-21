"""
01_exploracao.py — Bloco 0: auditoria de viabilidade dos dados

Objetivo: determinar, ANTES de qualquer analise de negocio, o que estes
dados sustentam e o que nao sustentam.

A saida e organizada em tres partes:
  PARTE 1 — o que os dados SUSTENTAM  (medicao real)
  PARTE 2 — o que os dados NAO SUSTENTAM  (evidencia forense)
  PARTE 3 — recomendacao de instrumentacao  (colunas ausentes nomeadas)

Uso:
    python 01_exploracao.py

Dependencias: pandas, scipy  (ver requirements.txt)
Saida: escreve em stdout e em 01_exploracao_saida.txt (mesmo diretorio).
"""

import io
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

# --------------------------------------------------------------------------
# Infra: resolucao de caminho e tee de saida
# --------------------------------------------------------------------------

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "01_exploracao_saida.txt"


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


def dist(serie: pd.Series, rotulo: str) -> pd.DataFrame:
    """Contagem + percentual de uma categorica, ordenada por volume."""
    c = serie.value_counts(dropna=False)
    return pd.DataFrame({rotulo: c, "%": (c / len(serie) * 100).round(1)})


# --------------------------------------------------------------------------
# Carga
# --------------------------------------------------------------------------

DADOS = achar_pasta_dados()
sys.stdout = Tee(SAIDA)

ops = pd.read_csv(DADOS / "customer_support_tickets.csv")
itsm = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")

frt = pd.to_datetime(ops["First Response Time"], errors="coerce")
ttr = pd.to_datetime(ops["Time to Resolution"], errors="coerce")

titulo("BLOCO 0 — AUDITORIA DE VIABILIDADE DOS DADOS")
print(f"pasta de dados: {DADOS}")
print(f"customer_support_tickets.csv      : {len(ops):>7,} linhas x {ops.shape[1]:>2} colunas")
print(f"all_tickets_processed_improved_v3 : {len(itsm):>7,} linhas x {itsm.shape[1]:>2} colunas")
print(f"\nduplicatas integrais — ops: {ops.duplicated().sum()} | itsm: {itsm.duplicated().sum()}")

titulo("INVENTARIO DE COLUNAS — customer_support_tickets.csv", "-")
inventario = pd.DataFrame({
    "dtype": ops.dtypes.astype(str),
    "nulos": ops.isna().sum(),
    "%nulo": (ops.isna().mean() * 100).round(1),
    "unicos": ops.nunique(),
})
print(inventario.to_string())

titulo("INVENTARIO DE COLUNAS — all_tickets_processed_improved_v3.csv", "-")
inventario2 = pd.DataFrame({
    "dtype": itsm.dtypes.astype(str),
    "nulos": itsm.isna().sum(),
    "%nulo": (itsm.isna().mean() * 100).round(1),
    "unicos": itsm.nunique(),
})
print(inventario2.to_string())


# ==========================================================================
# PARTE 1 — O QUE OS DADOS SUSTENTAM
# ==========================================================================
titulo("PARTE 1 — O QUE OS DADOS SUSTENTAM (medicao real)")
print("""
Volume, mix e estrutura de preenchimento sao fatos verificaveis nos arquivos,
independentemente de como os valores foram gerados. Sustentam analise.
""")

print(f"\n1.1 VOLUME OPERACIONAL: {len(ops):,} tickets")
print("    (nota: nao ha data de abertura — este volume NAO e anualizavel a")
print("     partir dos dados. Ver PARTE 2, evidencia E1.)")

for col in ["Ticket Channel", "Ticket Type", "Ticket Priority", "Ticket Status"]:
    print(f"\n1.2 MIX POR {col.upper()}")
    print(dist(ops[col], "tickets").to_string())

print(f"\n1.3 CATALOGO DE PRODUTOS: {ops['Product Purchased'].nunique()} produtos distintos")
print("    top 10 por volume de tickets:")
print(dist(ops["Product Purchased"], "tickets").head(10).to_string())

print("\n1.4 PERFIL DO CLIENTE")
print(f"    idade — min {ops['Customer Age'].min()} / mediana "
      f"{ops['Customer Age'].median():.0f} / max {ops['Customer Age'].max()}")
print(dist(ops["Customer Gender"], "tickets").to_string())

print("\n1.5 ACHADO ESTRUTURAL: CSAT existe se e somente se Ticket Status == 'Closed'")
tab = ops.groupby("Ticket Status", dropna=False).agg(
    tickets=("Customer Satisfaction Rating", "size"),
    csat_preenchido=("Customer Satisfaction Rating", "count"),
)
tab["csat_nulo"] = tab.tickets - tab.csat_preenchido
tab["%_nulo"] = (tab.csat_nulo / tab.tickets * 100).round(1)
print(tab.to_string())
cobertura = ops["Customer Satisfaction Rating"].notna().mean() * 100
print(f"""
    Interpretacao: o dado faltante NAO e aleatorio, e estrutural. Qualquer
    analise de satisfacao vive num recorte de {tab.loc['Closed', 'tickets']:,} tickets ({cobertura:.1f}% da base),
    e esse recorte e definido pela propria variavel de status. Em operacao
    real isso e vies de sobrevivencia: quem abandonou o ticket nao avalia.""")

print("\n1.6 COBERTURA DOS DEMAIS CAMPOS DEPENDENTES DE STATUS")
disp = ops.assign(
    tem_1a_resposta=frt.notna(),
    tem_ts_resolucao=ttr.notna(),
    tem_texto_resolucao=ops["Resolution"].notna(),
).groupby("Ticket Status")[
    ["tem_1a_resposta", "tem_ts_resolucao", "tem_texto_resolucao"]
].mean().mul(100).round(1)
print(disp.to_string())
print("    (mesma estrutura: os tres campos seguem o status, nao o processo.)")

print(f"\n1.7 DATASET DE CLASSIFICACAO — {len(itsm):,} tickets de TI em "
      f"{itsm['Topic_group'].nunique()} categorias")
d2 = dist(itsm["Topic_group"], "tickets")
print(d2.to_string())
razao = d2["tickets"].max() / d2["tickets"].min()
print(f"\n    desbalanceamento: {razao:.1f}x entre a maior e a menor classe")
print(f"    comprimento medio do texto: {itsm['Document'].str.len().mean():.0f} caracteres")
print("""
    Este e o unico dos dois arquivos com texto de ticket genuino (chamados de
    TI anonimizados, com stopwords removidas). Nao possui tempo, canal, cliente
    nem satisfacao — apenas texto e rotulo.""")


# ==========================================================================
# PARTE 2 — O QUE OS DADOS NAO SUSTENTAM
# ==========================================================================
titulo("PARTE 2 — O QUE OS DADOS NAO SUSTENTAM (evidencia forense)")
print("""
Sete evidencias independentes de que as variaveis de processo do
customer_support_tickets.csv foram geradas artificialmente. Nao e ressalva
de rodape: define quais analises sao impossiveis.
""")

# --- E1 ---
print("\nE1. NAO EXISTE TIMESTAMP DE ABERTURA DO TICKET")
temporais = [c for c in ops.columns if ops[c].astype(str).str.match(r"\d{4}-\d{2}-\d{2}").any()]
print(f"    colunas com formato de data encontradas: {temporais}")
dp = pd.to_datetime(ops["Date of Purchase"])
print(f"    'Date of Purchase' = compra do PRODUTO ({dp.min().date()} a {dp.max().date()}),")
print("     nao abertura do chamado. Nao serve de marco inicial.")
print("    CONSEQUENCIA: tempo de resolucao real e INCALCULAVEL. Sem marco")
print("    inicial nao existe duracao — nao e dificil, e impossivel.")

# --- E2 ---
delta_h = (ttr - frt).dt.total_seconds() / 3600
neg = (delta_h < 0).sum()
print("\nE2. O PROXY DE DURACAO (Time to Resolution - First Response Time) E RUIDO")
print(f"    pares validos                              : {delta_h.notna().sum():,}")
print(f"    resolvidos ANTES da primeira resposta      : {neg:,} ({neg / delta_h.notna().sum() * 100:.1f}%)")
print(f"    media                                      : {delta_h.mean():+.2f} h")
print(f"    mediana                                    : {delta_h.median():+.2f} h")
print(f"    desvio-padrao                              : {delta_h.std():.2f} h")
print(f"    minimo / maximo                            : {delta_h.min():+.2f} h / {delta_h.max():+.2f} h")
print("    CONSEQUENCIA: distribuicao uniforme centrada em zero com causalidade")
print("    invertida em 1 de cada 6 casos. Nao e processo, e sorteio.")

# --- E3 ---
span = frt.max() - frt.min()
print("\nE3. TODOS OS TIMESTAMPS CABEM NUMA JANELA DE ~27 HORAS")
print(f"    First Response Time: {frt.min()}  ->  {frt.max()}")
print(f"    amplitude total    : {span}")
por_dia = frt.dt.date.value_counts().sort_index()
print("    distribuicao por dia:")
for d, n in por_dia.items():
    print(f"      {d}: {n:>6,}")
print("    CONSEQUENCIA: nao ha serie temporal. Morrem sazonalidade, curva de")
print("    chegada por hora/dia, e comparacao de backlog entre periodos.")

# --- E4 ---
csat = ops["Customer Satisfaction Rating"].dropna()
obs = csat.value_counts().sort_index()
chi2_u, p_u = stats.chisquare(obs.values)
print("\nE4. O CSAT E UNIFORME — NAO TEM FORMA DE SATISFACAO REAL")
print("    distribuicao observada:")
for nota, n in obs.items():
    print(f"      nota {nota:.0f}: {n:>4,}  ({n / len(csat) * 100:.1f}%)")
print(f"    teste qui-quadrado de aderencia ao uniforme: chi2={chi2_u:.2f}, p={p_u:.3f}")
print("    p alto = indistinguivel de uniforme. CSAT real de suporte tem forma")
print("    em J (concentra em 1 e em 5), nunca uniforme.")

# --- E5 ---
print("\nE5. O CSAT NAO VARIA COM NENHUMA DIMENSAO OPERACIONAL")
medias = []
for c in ["Ticket Priority", "Ticket Channel", "Ticket Type"]:
    g = ops.groupby(c)["Customer Satisfaction Rating"].mean()
    medias.extend(g.tolist())
    print(f"\n    {c}:")
    for k, v in g.items():
        print(f"      {k:<24} {v:.3f}")
print(f"\n    amplitude total entre TODOS os grupos: {max(medias) - min(medias):.3f} ponto")
print("    CONSEQUENCIA: nao ha sinal a explicar. Toda analise de 'o que derruba")
print("    a satisfacao' e impossivel — e o CSAT nao serve de guarda-corpo para")
print("    decidir o que nao automatizar.")

# --- E6 ---
res = ops["Resolution"].dropna()
print("\nE6. O TEXTO DE 'Resolution' E GERADO ALEATORIAMENTE")
print(f"    resolucoes nao-nulas : {len(res):,}")
print(f"    valores unicos       : {res.nunique():,}  (nenhuma se repete)")
print(f"    comprimento medio    : {res.str.len().mean():.0f} caracteres")
print("    amostra de pares problema -> resolucao:")
amostra = ops[ops["Resolution"].notna()].sample(5, random_state=7)
for i, (_, r) in enumerate(amostra.iterrows(), 1):
    print(f"\n      [{i}] DESC: {str(r['Ticket Description'])[:150]}")
    print(f"          RESO: {r['Resolution']}")
print("\n    CONSEQUENCIA: a analise de resolucao quase-duplicada — que e a")
print("    metrica-mae para dimensionar automacao — e impossivel neste arquivo.")

# --- E7 ---
ct = pd.crosstab(ops["Ticket Subject"], ops["Ticket Type"])
chi2_i, p_i, gl, _ = stats.chi2_contingency(ct)
tem_placeholder = ops["Ticket Description"].str.contains(r"\{.*?\}", regex=True).mean() * 100
print("\nE7. 'Ticket Type' E 'Ticket Subject' FORAM SORTEADOS INDEPENDENTEMENTE")
print(f"    tabela de contingencia {ct.shape[0]}x{ct.shape[1]}")
print(f"    teste qui-quadrado de independencia: chi2={chi2_i:.2f}, gl={gl}, p={p_i:.3f}")
print("    p alto = independencia nao rejeitada. Existem tickets do tipo")
print("    'Refund request' com assunto 'Network problem'.")
print(f"\n    Alem disso: {tem_placeholder:.1f}% das descricoes contem placeholder de")
print("    template nao expandido ('{product_purchased}'), alem de residuo de")
print("    scraping ('{{item.price}}', '<!--', '@Product:@S&C=M&C1.3-TAC=N').")

titulo("SINTESE DA PARTE 2", "-")
print("""
O customer_support_tickets.csv serve como ESQUEMA de uma operacao de suporte,
nao como MEDICAO de uma. Suas variaveis categoricas sao sorteadas, o texto de
resolucao e artificial, o CSAT e uniforme e os timestamps nao formam processo.

O all_tickets_processed_improved_v3.csv e o inverso: texto genuino e rotulo
real, sem nenhuma metrica operacional.

Consequencia para a entrega: o arquivo que tem metrica tem metrica falsa; o
arquivo que tem texto real nao tem metrica. Portanto nenhum caminho nos dados
produz 'horas desperdicadas' por medicao direta. O business case em horas
precisa ser um MODELO PARAMETRICO EXPLICITO: volume e mix reais vindos dos
dados, tempo de manuseio entrando como premissa declarada e auditavel, com
faixa e analise de sensibilidade.
""")


# ==========================================================================
# PARTE 3 — RECOMENDACAO DE INSTRUMENTACAO
# ==========================================================================
titulo("PARTE 3 — RECOMENDACAO DE INSTRUMENTACAO (entregavel)")
print("""
As colunas abaixo estao ausentes do dataset operacional. Elas nao sao uma
limitacao deste exercicio: sao o diagnostico. Uma operacao que nao registra
estes campos nao consegue localizar onde perde tempo — e sem localizar, nao
ha o que automatizar com criterio. Instrumentar e pre-requisito de automacao.
""")

campos = [
    ("opened_at", "timestamp",
     "Abertura do ticket.",
     "Sem ele nao existe duracao. E o campo mais critico da lista.",
     "tempo de resolucao, curva de chegada, sazonalidade, SLA"),
    ("first_response_at", "timestamp",
     "Primeira resposta humana ou automatica.",
     "Existe hoje, mas sem opened_at nao vira metrica.",
     "tempo de primeira resposta"),
    ("resolved_at / closed_at", "timestamp",
     "Resolucao e fechamento, separados.",
     "Resolvido != fechado; a diferenca revela fechamento automatico.",
     "tempo de ciclo, taxa de fechamento por inatividade"),
    ("queue_entered_at / queue_exited_at", "timestamp",
     "Entrada e saida de cada fila.",
     "Separa ESPERA de TRABALHO — gargalo de capacidade e de complexidade",
     "decomposicao fila x atendimento"),
    ("handle_time_seconds", "inteiro",
     "Tempo efetivo de trabalho humano no ticket.",
     "Hoje o handle time e premissa arbitrada; medido, vira fato.",
     "custo real por categoria, business case sem premissa"),
    ("assigned_agent_id", "id",
     "Agente responsavel a cada momento.",
     "Sem ele nao ha produtividade, carga nem curva de aprendizado.",
     "carga por agente, variabilidade de desempenho"),
    ("transfer_count / escalation_count", "inteiro",
     "Quantas vezes o ticket trocou de dono ou subiu de nivel.",
     "Roteamento errado e um dos maiores desperdicios invisiveis.",
     "custo de misrouting, alvo de triagem automatica"),
    ("reopened_count", "inteiro",
     "Reaberturas apos fechamento.",
     "E a metrica de qualidade real da resolucao.",
     "retrabalho, falso 'resolvido', guarda-corpo de automacao"),
    ("interaction_count", "inteiro",
     "Numero de trocas de mensagem com o cliente.",
     "Proxy direto de esforco e de atrito.",
     "esforco do cliente, deteccao de ticket problematico"),
    ("resolution_code / kb_article_id", "categorico",
     "Solucao aplicada, padronizada, e artigo de base usado.",
     "Texto livre nao agrega; codigo padronizado mede repeticao.",
     "taxa de repeticao, dimensionamento de automacao"),
    ("csat_requested_at / csat_channel", "timestamp / categorico",
     "Quando a pesquisa foi enviada e por onde.",
     "Hoje so ha nota de ticket fechado — vies de sobrevivencia puro.",
     "CSAT corrigido por nao-resposta"),
]

print(f"{'CAMPO':<36} {'TIPO':<22} {'DESBLOQUEIA'}")
print("-" * 110)
for nome, tipo, _, _, desbloqueia in campos:
    print(f"{nome:<36} {tipo:<22} {desbloqueia}")

print("\n\nDETALHAMENTO:\n")
for i, (nome, tipo, oque, porque, _) in enumerate(campos, 1):
    print(f"{i:>2}. {nome}  ({tipo})")
    print(f"    o que e : {oque}")
    print(f"    por que : {porque}\n")

print("""
PRIORIZACAO SUGERIDA
  Onda 1 (destrava o business case): opened_at, resolved_at, handle_time_seconds
  Onda 2 (destrava o diagnostico)  : queue_*, transfer_count, reopened_count
  Onda 3 (destrava a qualidade)    : resolution_code, interaction_count, csat_*
""")

titulo("FIM — BLOCO 0")
print(f"saida salva em: {SAIDA}")
sys.stdout.flush()
