"""Constantes do modelo. Valores vindos dos notebooks 03 (LightGBM) e do plano (seção 3.5)."""
from __future__ import annotations

HORIZON_DAYS = 30             # alvo do modelo: "este deal vira ganho nos próximos 30 dias, a partir de hoje?"
GAP_DAYS = HORIZON_DAYS       # fotos de treino terminam em T - 30: o desfecho de 30 dias de cada foto já é conhecido em T
TARGET_COL = "won_30d"        # rótulo de treino/teste (1 = fechou como Won em até HORIZON_DAYS após a foto)
SHRINK_K = 30                 # força do encolhimento das taxas para a média
RECENT_DAYS = 90              # janela do "desempenho recente" do vendedor
TRAIN_START_OFFSET_DAYS = 14  # primeira foto de treino = primeiro fechamento + 14 dias
LOW_CONFIDENCE_AGENT_N = 30   # vendedor com menos fechados que isso => confiança "low"

# Limiares de idade vêm do ciclo dos deals JÁ fechados. Percentis, e não o máximo: um zumbi antigo fechado numa
# limpeza de carteira não pode empurrar a régua e trazer centenas de zumbis de volta para a lista.
STALE_QUANTILE = 0.90         # "Decidir agora": passou do prazo em que 90% dos deals fecham
REVIEW_QUANTILE = 0.99        # "A revisar" (zumbi): mais velho que 99% dos deals fechados

NUM_FEATURES = [
    "price", "agent_wr", "agent_n", "product_wr", "agent_product_wr",
    "agent_recent_wr", "agent_load", "age_days", "age_vs_cycle",   # age_vs_cycle = idade / P99 do ciclo fechado
]
CAT_FEATURES = ["product", "series", "sales_agent", "manager", "regional_office"]

# Nunca entram como feature (seriam vazamento ou dados de conta, excluídos por decisão do plano).
EXCLUDED_FROM_MODEL = ["close_date", "close_value", "duração do deal", "dados de conta"]

# Backtest com datas móveis: as últimas fotos cujo desfecho de 30 dias já é conhecido (T = ref - 30 - k * espaçamento).
BACKTEST_SNAPSHOT_COUNT = 4
BACKTEST_SPACING_DAYS = 14
BACKTEST_PROTOCOL = "won_30d.v1"   # métricas só são comparáveis entre versões do mesmo protocolo

FOCUS_SCORE = 80
FOLLOW_UP_SCORE = 40

LGBM_PARAMS = dict(
    learning_rate=0.03, num_leaves=15, min_child_samples=150, subsample=0.8, subsample_freq=1,
    colsample_bytree=0.8, reg_lambda=10, verbose=-1, random_state=0, n_jobs=2, metric="auc",
)
LGBM_MAX_ESTIMATORS = 800
LGBM_EARLY_STOPPING = 100     # paciência alta: o AUC de validação tem picos espúrios no início (árvore ~5) e só estabiliza depois
LGBM_MIN_ESTIMATORS = 50
VALIDATION_FRACTION_OF_SNAPSHOTS = 0.75   # as últimas 25% das fotos viram validação temporal

BANDS = ("focus", "follow_up", "low", "stale_risk", "review", "prospecting")
STAGES = ("Engaging", "Prospecting")

SUGGESTED_ACTIONS = {
    "focus": "Agende uma conversa com quem decide ainda esta semana.",
    "follow_up": "Mantenha o ritmo e revise na próxima semana.",
    "low": "Pouco valor esperado. Só vale o tempo se for rápido.",
    "stale_risk": "Decidir agora: este deal passou do prazo em que 90% dos deals fecham.",
    "review": "Mais antigo que qualquer deal já fechado. Encerrar ou reativar.",
    "prospecting": "Sem contato registrado. Inicie o engajamento.",
}

# Níveis de prioridade mostrados ao vendedor (chave, rótulo, score mínimo, score máximo). Única fonte das faixas de score.
PRIORITY_LEVELS = (
    ("high", "Alta", FOCUS_SCORE, 100),
    ("medium", "Média", FOLLOW_UP_SCORE, FOCUS_SCORE - 1),
    ("low", "Baixa", 0, FOLLOW_UP_SCORE - 1),
)

# Visões (abas) da lista do vendedor: quais faixas entram e a ordenação padrão. Única fonte desse agrupamento.
VIEWS = {
    "focus": {"bands": ("focus", "follow_up"), "sort": "score"},      # semana: prioridade Alta e Média (o dia sai daqui)
    "decide": {"bands": ("stale_risk",), "sort": "score"},
    "follow": {"bands": ("low",), "sort": "score"},
    "prospecting": {"bands": ("prospecting",), "sort": "score"},
    "review": {"bands": ("review",), "sort": "score"},
    "all": {"bands": BANDS, "sort": "score"},
    "ev": {"bands": tuple(b for b in BANDS if b != "review"), "sort": "expected_value"},
}
VIEW_OF_BAND = {"focus": "focus", "stale_risk": "decide", "follow_up": "focus", "low": "follow",
                "prospecting": "prospecting", "review": "review"}
