"""Configuração do scoring — pesos e thresholds, todos justificados na EDA.

Fonte única de verdade dos parâmetros. Mudou aqui, mudou no app e nos testes.
Justificativas em ../PLANO-DO-PROJETO.md §6 e ../decisoes.md.
"""

# --- Probabilidade: smoothing bayesiano do win-rate do vendedor ---
GLOBAL_WIN_RATE = 0.632   # base global medida (EDA: win-rate global)
SMOOTHING_K = 8           # peso do prior; ~10% das células agente×produto têm n<10

# --- Ciclo de venda (EDA sobre 4.238 deals Won: p25=9, mediana=57, p75=88, p90=106, MÁX=138) ---
CYCLE_MEDIAN_DAYS = 57    # mediana do ciclo vencedor
CYCLE_P75_DAYS = 88       # p75 do ciclo vencedor
CYCLE_P90_DAYS = 106      # p90 do ciclo vencedor
# Nenhum deal Won na história passou de 138 dias — além disso é, por dados, "morto".
WON_MAX_DAYS = 138        # deal Won mais velho já observado

# --- Urgência: curva SINO ancorada no ciclo dos Won (ver features.aging_subscore) ---
# EDA: deals abertos (Engaging) têm mediana 165d (vs 57d dos Won) — a maioria já
# passou da janela em que algum Won fechou. Uma urgência que CRESCE com a idade
# (modelo antigo) recompensa cadáveres e marcava 93% dos Engaging como "crítico"
# — sinal sem poder discriminativo. O correto é uma sino: sobe até a janela
# produtiva (mediana→p75 dos Won, onde os deals costumam fechar), satura no platô
# e DECAI após, porque a chance de fechar despenca (zero Won além de 138d).
URGENCY_RAMP_END = CYCLE_MEDIAN_DAYS   # 57 — fim do aquecimento (0→100)
URGENCY_PEAK_END = CYCLE_P75_DAYS      # 88 — fim do platô na janela ideal
URGENCY_FLOOR = 10.0                   # piso pós-janela (ainda é um deal, mas quase morto)

# Deal "provavelmente morto": mais velho que QUALQUER fechamento histórico.
# Data-driven (138d = Won mais velho), substitui o antigo 3×mediana (171d), que
# não tinha base no outcome real. Com 138d, 61,8% dos abertos (1291/2089) caem em
# stale — pipeline genuinamente inflado, reportado como insight de saúde (não escondido).
STALE_DAYS = WON_MAX_DAYS              # 138 — além do Won mais velho da história

# --- Pesos do score (Engaging: têm os 3 componentes) ---
# Justificativa: probabilidade é o sinal primário; valor diferencia (preços 550–26.768);
# urgência separa quem está esfriando. Setor/região/manager NÃO entram (EDA: spread <5pp).
WEIGHTS_ENGAGING = {
    "probability": 0.45,
    "value": 0.35,
    "urgency": 0.20,
}
# Prospecting não tem engage_date -> sem urgência; renormaliza os outros dois.
WEIGHTS_PROSPECTING = {
    "probability": 0.45 / 0.80,   # 0.5625
    "value": 0.35 / 0.80,         # 0.4375
}

# --- Tiers operacionais (faixa de score 0-100) ---
TIER_FOCO_AGORA = 70      # >= 70
TIER_TRABALHAR = 45       # 45–69 ; < 45 = Baixa Prioridade

TIERS = {
    "Foco Agora": {"min": TIER_FOCO_AGORA, "icon": "🔥", "color": "#EF4444"},
    "Trabalhar": {"min": TIER_TRABALHAR, "icon": "⭐", "color": "#F59E0B"},
    "Baixa Prioridade": {"min": 0, "icon": "⏳", "color": "#64748B"},
}

# sanidade: pesos somam 1
assert abs(sum(WEIGHTS_ENGAGING.values()) - 1.0) < 1e-9
assert abs(sum(WEIGHTS_PROSPECTING.values()) - 1.0) < 1e-9
