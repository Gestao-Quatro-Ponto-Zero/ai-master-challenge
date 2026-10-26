"""Constantes e caminhos do projeto.

Aqui moram só parâmetros e limiares escolhidos; nenhum resultado calculado dos dados.
"""

from pathlib import Path

# --- Caminhos (relativos a este arquivo, então valem em qualquer máquina) -------------------
SOLUTION_DIR = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = SOLUTION_DIR.parent
RAW_DIR = SOLUTION_DIR / "data" / "raw"
PROCESSED_DIR = SOLUTION_DIR / "data" / "processed"
DOCS_DIR = SUBMISSION_DIR / "docs"
DEALS_CSV = PROCESSED_DIR / "deals.csv"
FACTS_JSON = PROCESSED_DIR / "facts.json"
BACKTEST_JSON = PROCESSED_DIR / "backtest_metrics.json"  # gerado no bloco 3

# --- Limpeza ----------------------------------------------------------------------------
DEFAULT_REFERENCE_DATE = "2017-12-31"  # "hoje": a data máxima do dataset (parâmetro, nunca fixo no código)
PRODUCT_NAME_MAP = {"GTXPro": "GTX Pro"}  # nome no pipeline -> nome no catálogo
SECTOR_MAP = {"technolgy": "technology"}  # erro de digitação no cadastro de contas
NO_ACCOUNT_LABEL = "Conta não informada"
OPEN_STAGES = ("Engaging", "Prospecting")
CLOSED_STAGES = ("Won", "Lost")
STAGE_ORDER = ("Won", "Lost", "Engaging", "Prospecting")

# --- Backtest e modelo (usados nos blocos 3 e 4) ------------------------------------------
HORIZON_DAYS = 90  # 1 trimestre
FIRST_SNAPSHOT = "2017-03-31"  # 1ª foto mensal de treino (regra do bloco 2, investigação 2a)
SENSITIVITY_FIRST_SNAPSHOT = "2017-02-28"  # só como sensibilidade
BACKTEST_CUTS = ["2017-06-30", "2017-07-31", "2017-08-31", "2017-09-30"]
UI_BACKTEST_SNAPSHOTS = ["2017-06-30", "2017-09-30"]
TOP_FRAC = 0.20
RANDOM_SEEDS = 200
BOOTSTRAP_REPS = 1000
KNOT_GRID = range(0, 181, 5)
CRITERION_TIE_TOL = 0.01  # até 1 ponto percentual de receita capturada é empate (e empate não vence)
ADJUST_BIN_DAYS = 15  # ajuste único pré-definido: faixas de idade de 15 dias...
ADJUST_PSEUDO_COUNT = 20  # ...com pseudo-contagem de 20 deals rumo à taxa média de treino
ATTRIBUTE_L2 = 1.0  # penalidade L2 nos coeficientes do atributo (teste de atributos)
FOQUE_AGE_BANDS = ((0, 30), (31, 60), (61, None))  # faixas de idade para o achado "Foque 61+ dias"
CATEGORIES = ("Foque", "Reative", "Limpe", "Qualifique")  # as 4 listas de ação, na ordem de exibição

# --- Curva v2 (correção após revisão do Rafael; ver docs/SCORING.md e process-log/07_correcao-curva.md) ---
# Mudança pós-backtest: a curva v1 ("platô + queda") dava a mesma chance de 0 a ~95 dias. A v2 é monotônica
# desde o dia 0 (faixas de idade isotônicas) e treina só com fotos da mesma fase do trimestre do corte.
V2_PSEUDO_COUNT = 0  # sem pseudo-contagem: a do ajuste único (20) empurrava a cauda sem ganhos para 7% a 27%
FOQUE_HALF_FRACTION = 0.5  # Foque: idade até onde a chance ainda é pelo menos metade da chance de um deal novo
LIMPE_MIN_CHANCE = 0.02  # Limpe: chance abaixo de 2% (ou idade acima do maior ciclo já ganho até o corte)
AGE_SCAN_MAX_DAYS = 730  # varredura de idades para achar os limiares da curva (a curva é constante depois da última faixa)
QUARTER_END_PHASE = 3  # 3º mês do trimestre (mar, jun, set, dez): fotos "de fim de trimestre"
EXPLAIN_CURVE_AGES = (30, 60, 90)  # idades citadas na linha 2 de "Como funciona o score"
CURVE_TABLE_AGES = (0, 15, 30, 45, 60, 75, 90, 105, 120, 150)  # idades da tabela da curva no SCORING
DIAGNOSTIC_AGE_BANDS = ((0, 30), (31, 60), (61, 90), (91, 105), (106, 120))  # faixas do diagnóstico por fase
INTRA_FOQUE_MAX_AGE = 90  # população da métrica de ordem dentro do Foque: Engaging abertos em T com idade <= 90 dias

# --- Recalibração (MODEL_CARD, bloco 5) -----------------------------------------------------
RECALIBRATION_SHIFT_PP = 10  # X: alerta quando a taxa de ganho em 90 dias de uma faixa de idade se afasta da chance do modelo em mais de X pp
RECALIBRATION_MIN_BAND_N = 100  # faixas com menos deals que isso não disparam o alerta (ruído de amostra)

# --- Critérios pré-definidos das investigações do bloco 2 ---------------------------------
# 2a: o win rate do 1º trimestre é artefato de recorte se as três condições valerem.
Q1_MARCH_TOLERANCE_PP = 5  # março a +-5 pp da média dos meses de fim de trimestre seguintes
TRUNCATION_GAP_DAYS = 7  # ciclo mínimo da coorte a no máximo 7 dias do piso imposto pelo recorte
FAST_CYCLE_DAYS = 14  # "fechamento rápido" (mediana dos perdidos é 14 dias)
# 2c: o preço de tabela serve como valor do deal aberto se...
RATIO_MEAN_RANGE = (0.95, 1.05)  # ...a razão close_value/tabela média de cada produto cair nesta faixa
RATIO_QUARTER_MAX_PP = 3  # ...e a média trimestral variar no máximo 3 pp
# Faixas de idade do briefing (ponto de partida; os limiares reais saem do modelo, no bloco 3)
BRIEFING_FRESH_DAYS = 90
SNAPSHOT_AGE_BINS = [-1, 30, 60, 90, 138, 200, 1000]  # as mesmas faixas de process-log/scripts/snapshot.py
SNAPSHOT_DATES = ["2017-06-30", "2017-09-30"]  # fotos do briefing

# --- Números estruturais permitidos na prosa dos documentos ------------------------------
# O teste de números aceita um token da prosa se ele sair de facts.json (ou do JSON do backtest)
# ou se estiver aqui. Cada valor é um parâmetro de desenho, não um resultado.
ALLOWED_CONSTANTS = {
    BRIEFING_FRESH_DAYS: "90 dias: horizonte de ganho (1 trimestre) e 1ª faixa de idade do briefing",
    round(TOP_FRAC * 100): "top 20% do score, base da métrica primária",
    5: "tolerância de 5 pp (2a) e percentil 5 do close_value/tabela (2c)",
    95: "percentil 95 (aleatório e close_value/tabela)",
    100: "escala do score (0 a 100)",
    KNOT_GRID[-1]: "180 dias: maior joelho testado na curva de idade",
    RANDOM_SEEDS: "200 sorteios do baseline aleatório",
    RANDOM_SEEDS - 1: "última semente do baseline aleatório (sementes 0 a 199)",
    BOOTSTRAP_REPS: "1.000 reamostragens do bootstrap",
    RATIO_MEAN_RANGE[0]: "limite inferior da razão close_value/tabela média (2c)",
    RATIO_MEAN_RANGE[1]: "limite superior da razão close_value/tabela média (2c)",
}

# --- Documentos cobertos por `python -m scorer.docs` e pelo teste de números ----------------
# (SCORING.md, MODEL_CARD.md e README.md entram nos blocos 3 e 5.)
COVERED_DOCS = [
    DOCS_DIR / "DATA_QUALITY.md",
    DOCS_DIR / "SCOPE.md",
    DOCS_DIR / "SCORING.md",
    DOCS_DIR / "MODEL_CARD.md",
    SUBMISSION_DIR / "README.md",
]
BACKTEST_TABLES_MD = PROCESSED_DIR / "backtest_tables.md"  # gerado no bloco 3
