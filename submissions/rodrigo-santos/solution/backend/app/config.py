"""
Configurações centrais da aplicação.

Tudo que um dev ou gestor possa querer ajustar (caminhos, pontos do score,
faixas de prioridade) fica aqui, para não precisar mexer na lógica.
"""

from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

# Pasta raiz do projeto (solution/), dois níveis acima deste arquivo.
PASTA_RAIZ = Path(__file__).resolve().parents[2]

# Pasta com os CSVs de origem.
PASTA_DADOS = PASTA_RAIZ / "dados"

# Tela já compilada (gerada por `npm run build` no frontend). Se existir,
# a própria API serve a tela em http://localhost:8000, sem precisar de Node.
PASTA_FRONTEND_COMPILADO = PASTA_RAIZ / "frontend" / "dist"

# ---------------------------------------------------------------------------
# Data de referência ("hoje")
# ---------------------------------------------------------------------------

# Os dados históricos terminam em 2017. Se for None, usamos a maior data
# encontrada nos CSVs como "hoje". Quando os dados forem reais/atuais,
# basta trocar por date.today().
DATA_REFERENCIA: date | None = None

# ---------------------------------------------------------------------------
# Score de prioridade (ver app/servicos/pontuacao.py e o relatório de validação)
# ---------------------------------------------------------------------------

# Pontos máximos de cada parte do score (a soma deve ser 100).
PONTOS_MAXIMOS = {
    "situacao": 40,    # o negócio está vivo? (em negociação, em prospecção ou parado)
    "valor": 40,       # quanto o negócio vale
    "reta_final": 20,  # quão perto está do prazo em que os negócios se resolvem
}

# Fração dos pontos de situação que um negócio em prospecção recebe
# (ainda não começou a negociação, então vale menos que um ativo).
FRACAO_SITUACAO_PROSPECCAO = 0.5

# Chance usada no valor esperado de negócios parados (abertos há mais tempo
# que qualquer negócio do histórico). Na validação, nenhum deles fechou depois.
CHANCE_PARADO = 0.0

# Faixas de prioridade pelo score (0 a 100). Negócio parado é sempre "Baixa".
LIMITE_PRIORIDADE_ALTA = 60
LIMITE_PRIORIDADE_MEDIA = 40

# ---------------------------------------------------------------------------
# Validação (backtest) — ver app/servicos/validacao.py
# ---------------------------------------------------------------------------

# Datas de corte: em cada uma, "voltamos no tempo", pontuamos os negócios que
# estavam abertos naquele dia e comparamos com o que aconteceu depois.
DATAS_CORTE_VALIDACAO = ["2017-05-01", "2017-07-01", "2017-09-01", "2017-11-01"]

# Suavização das taxas de vitória testadas na validação: quantos negócios
# "imaginários" com a taxa média somamos a cada grupo (evita 100% com 2 negócios).
SUAVIZACAO_AMOSTRAS = 20

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

# Origens autorizadas a chamar a API (front-end em desenvolvimento).
ORIGENS_PERMITIDAS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
