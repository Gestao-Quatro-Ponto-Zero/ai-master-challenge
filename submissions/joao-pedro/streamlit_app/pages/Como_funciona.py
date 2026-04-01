"""
Preview da Lógica - Visualização interativa do modelo de scoring
"""

import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_benchmarks, load_deals
from core.scoring_engine import calculate_score

st.set_page_config(page_title="Macro", page_icon="🧠", layout="wide")

# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    deals = load_deals(deal_stage='Engaging')
    return benchmarks, deals

benchmarks, deals = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("🧠 score model")
st.markdown("""
O modelo prioriza deals baseado em **urgência**, **probabilidade de fechar** e **valor estratégico**.
A **viabilidade** (capacidade do vendedor) é calculada separadamente para derivar ações.
""")

st.divider()

# =============================================================================
# FÓRMULA PRINCIPAL
# =============================================================================
st.subheader("📐 Fórmula do Score")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### Score = 50% Urgência + 30% Probabilidade + 20% Valor
    
    **Por que esses pesos?**
    - **50% Urgência:** Deals travados há muito tempo (165d mediana) precisam de ação AGORA
    - **30% Probabilidade:** Não adianta urgência se probabilidade é baixa
    - **20% Valor:** Importância estratégica (premium products, top accounts)
    
    **Viabilidade (separada):** Capacidade do vendedor resolver (prospecting + carga + especialização)
    """)

with col2:
    # Gráfico de pizza dos pesos
    fig = go.Figure(data=[go.Pie(
        labels=['Urgência (50%)', 'Probabilidade (30%)', 'Valor (20%)'],
        values=[50, 30, 20],
        hole=0.4,
        marker_colors=['#ff4b4b', '#1f77b4', '#2ca02c']
    )])
    fig.update_layout(title="Composição do Score", showlegend=True, height=300)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# COMPONENTE 1: URGÊNCIA
# =============================================================================
st.subheader("🔥 Componente 1: Urgência (50%)")

st.markdown("""
**Pergunta:** Há quanto tempo este deal está travado sem decisão?

**Lógica:** Baseada em **thresholds de tempo** derivados das medianas reais:
""")

# Tabela de thresholds
import pandas as pd

thresholds_df = pd.DataFrame([
    {'Dias no Pipeline': '≥200', 'Urgência Base': '100', 'Classificação': '🔥 CRÍTICO (frozen)', 'Razão': '3.5× tempo típico de Won'},
    {'Dias no Pipeline': '≥165', 'Urgência Base': '80', 'Classificação': '⚠️ CONGELADO', 'Razão': 'Mediana de Engaging (travado)'},
    {'Dias no Pipeline': '≥85', 'Urgência Base': '60', 'Classificação': '⏰ ATRASADO', 'Razão': '1.5× Won mediana (57d)'},
    {'Dias no Pipeline': '≥57', 'Urgência Base': '40', 'Classificação': '📅 NO LIMITE', 'Razão': 'Won mediana (tempo normal)'},
    {'Dias no Pipeline': '≥28', 'Urgência Base': '20', 'Classificação': '✓ Normal', 'Razão': '0.5× Won (ainda cedo)'},
    {'Dias no Pipeline': '<28', 'Urgência Base': '10', 'Classificação': '🆕 Recente', 'Razão': 'Acabou de entrar'},
])

st.dataframe(thresholds_df, use_container_width=True, hide_index=True)

st.markdown("""
**Multiplicadores (aumentam urgência):**
- Vendedor sobrecarregado (>100 deals): **+15% a +30%**
- Conta com histórico ruim (<40% WR): **+20%**
- Deal muito maior que experiência do vendedor (>3× ticket médio): **+15%**

**Exemplo:**  
Deal com 200 dias + vendedor com 120 deals = 100 × 1.15 = **115** (cap em 100)
""")

st.divider()

# =============================================================================
# COMPONENTE 2: PROBABILIDADE
# =============================================================================
st.subheader("🎯 Componente 2: Probabilidade (30%)")

st.markdown("""
**Pergunta:** Qual a chance real deste deal fechar?

**Lógica:** Prior bayesiano (63.15% global) × fatores contextuais
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### ✅ Fatores que AUMENTAM probabilidade:
    
    1. **Vendedor forte** (win rate > média global)
    2. **Produto de sucesso** (win rate > média)
    3. **Conta boa** (histórico > média)
    4. **Região forte**
    5. **Especialista** (vendedor expert neste produto): **+15%**
    """)

with col2:
    st.markdown("""
    ### ❌ Penalidades que REDUZEM probabilidade:
    
    1. **Tempo excessivo** (>35d): **-25%**
    2. **Deal oversized** (>3× ticket médio do vendedor): **-10%**
    3. **Vendedor sobrecarregado** (>150 deals): **-15%**
    """)

st.markdown("""
**Exemplo de cálculo:**
```
Base: 63.15% (global)
× Vendedor 70% / 63.15% = × 1.11
× Produto 65% / 63.15% = × 1.03
× Conta 58% / 63.15% = × 0.92
× Região (neutro) = × 1.0
× Especialista = × 1.15
× Tempo normal = × 1.0
× Sem oversize = × 1.0
× Carga ok = × 1.0

= 63.15 × 1.11 × 1.03 × 0.92 × 1.15 = 76.8%
```
""")

st.divider()

# =============================================================================
# COMPONENTE 3: VALOR
# =============================================================================
st.subheader("💎 Componente 3: Valor (20%)")

st.markdown("""
**Pergunta:** Qual a importância estratégica deste deal?

**Lógica:** **Percentil** (não valor absoluto) + ajustes estratégicos

**Por que percentil?**  
Mediana ($472) é 3.2× menor que média ($1,491) = distribuição com cauda pesada.  
Usar valor absoluto daria peso excessivo aos outliers.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### ✅ Bonus:
    
    - **Produto premium** (GTK 500): **+20%**
    - **Conta estratégica** (top 20 por volume): **+15%**
    """)

with col2:
    st.markdown("""
    ### ❌ Desconto:
    
    - **Probabilidade baixa** (<40%): **-30%** (valor esperado)
    - **Probabilidade média** (<55%): **-15%**
    """)

st.markdown("""
**Exemplo:**  
Deal de $5,000 está no percentil 85  
× Premium GTK 500: 85 × 1.20 = 102 → cap em 100  
× Conta top 20: já no cap  
× Prob 72% (boa): sem desconto  
**Valor final: 100**
""")

st.divider()

# =============================================================================
# VIABILIDADE (SEPARADA)
# =============================================================================
st.subheader("⚙️ Viabilidade: Capacidade do Vendedor (Separada)")

st.markdown("""
**Pergunta:** O vendedor CONSEGUE dar atenção adequada a este deal?

**Por que separada do score?**  
- Score = importância **objetiva** do deal (igual para todos)
- Viabilidade = capacidade **contextual** do vendedor
- Ação = f(Score, Viabilidade)

**Fórmula:**  
Viabilidade = 50 × prospecting_factor × load_factor × specialist_factor
""")

viab_df = pd.DataFrame([
    {'Fator': 'Prospecting', '0 novos': '0.5× (-50%)', '10-30': '1.0× (neutro)', '>30': '1.3× (+30%)', 'Razão': 'Sem prospects = protege deals ruins'},
    {'Fator': 'Carga', '>150 deals': '0.6× (-40%)', '40-100': '1.0× (neutro)', '<40': '1.3× (+30%)', 'Razão': 'Sobrecarga reduz atenção'},
    {'Fator': 'Especialização', 'Mismatch': '0.8× (-20%)', 'Neutro': '1.0×', 'Expert': '1.2× (+20%)', 'Razão': 'Expert fecha melhor'},
])

st.dataframe(viab_df, use_container_width=True, hide_index=True)

st.markdown("""
**Exemplos reais:**
- **Anna:** 112 deals, 0 prospecting → 50 × 0.5 × 0.8 = **20** (baixa)
- **Wilburn:** 31 deals, 25 prospecting → 50 × 1.0 × 1.3 = **65** (boa)
- **Marty:** 87 deals, 54 prospecting → 50 × 1.3 × 1.0 = **65** (boa)
""")

st.divider()

# =============================================================================
# MATRIZ DE AÇÃO
# =============================================================================
st.subheader("🎯 Matriz de Ação: Score × Viabilidade")

st.markdown("""
**Como derivamos a ação?**  
Combinamos **Score** (importância do deal) com **Viabilidade** (capacidade do vendedor).
""")

# Criar matriz visual
matriz_html = """
<style>
table.matriz {
    width: 100%;
    border-collapse: collapse;
}
table.matriz th, table.matriz td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: center;
}
table.matriz th {
    background-color: #1f77b4;
    color: white;
    font-weight: bold;
}
table.matriz tr:nth-child(even) {
    background-color: #f2f2f2;
}
.critical { background-color: #ff4b4b; color: white; font-weight: bold; }
.high { background-color: #ffa500; color: white; font-weight: bold; }
.medium { background-color: #ffeb3b; font-weight: bold; }
.low { background-color: #90ee90; }
</style>

<table class="matriz">
<tr>
    <th>Score \ Viabilidade</th>
    <th>Alta (≥60)</th>
    <th>Média (40-60)</th>
    <th>Baixa (<40)</th>
</tr>
<tr>
    <td class="critical">≥80 (Crítico)</td>
    <td class="critical">🔥 PUSH HARD</td>
    <td class="high">🔄 RE-QUALIFY</td>
    <td class="high">🔀 TRANSFER</td>
</tr>
<tr>
    <td class="high">70-79 (Alto)</td>
    <td class="high">🔥 PUSH HARD</td>
    <td class="medium">🔄 RE-QUALIFY</td>
    <td class="medium">🔀 TRANSFER ou ❌ DISCARD</td>
</tr>
<tr>
    <td class="medium">60-69 (Médio)</td>
    <td class="medium">⚡ ACCELERATE</td>
    <td class="medium">🔍 INVESTIGATE</td>
    <td class="low">🔀 CONSIDER TRANSFER</td>
</tr>
<tr>
    <td class="low"><60 (Baixo)</td>
    <td class="low">⏸ MONITOR</td>
    <td class="low">⏸ MONITOR</td>
    <td class="low">⏸ MONITOR</td>
</tr>
</table>
"""

st.markdown(matriz_html, unsafe_allow_html=True)

st.divider()

# =============================================================================
# SIMULADOR INTERATIVO
# =============================================================================
st.subheader("🎮 Simulador Interativo")

st.markdown("Ajuste os parâmetros e veja como o score muda:")

col1, col2, col3 = st.columns(3)

with col1:
    dias = st.slider("Dias no Pipeline", 0, 300, 165)
    prob_input = st.slider("Probabilidade (%)", 0, 100, 65)
    valor_percentil = st.slider("Valor (percentil)", 0, 100, 50)

with col2:
    seller_active = st.slider("Deals Ativos do Vendedor", 0, 200, 100)
    seller_prosp = st.slider("Prospecting do Vendedor", 0, 60, 15)

with col3:
    is_premium = st.checkbox("Produto Premium (GTK 500)?")
    is_top_account = st.checkbox("Conta Top 20?")
    is_specialist = st.checkbox("Vendedor Especialista?")

# Calcular urgência
if dias >= 200:
    urgencia = 100
elif dias >= 165:
    urgencia = 80
elif dias >= 85:
    urgencia = 60
elif dias >= 57:
    urgencia = 40
elif dias >= 28:
    urgencia = 20
else:
    urgencia = 10

# Multiplicador de carga
if seller_active > 150:
    urgencia *= 1.3
elif seller_active > 100:
    urgencia *= 1.15

urgencia = min(urgencia, 100)

# Probabilidade (simplificado)
probabilidade = prob_input

# Valor
valor = valor_percentil
if is_premium:
    valor *= 1.2
if is_top_account:
    valor *= 1.15
valor = min(valor, 100)

# Score
score = 0.5 * urgencia + 0.3 * probabilidade + 0.2 * valor

# Viabilidade
if seller_prosp == 0:
    prosp_factor = 0.5
elif seller_prosp < 10:
    prosp_factor = 0.8
elif seller_prosp <= 30:
    prosp_factor = 1.0
else:
    prosp_factor = 1.3

if seller_active > 150:
    load_factor = 0.6
elif seller_active > 100:
    load_factor = 0.8
elif seller_active >= 40:
    load_factor = 1.0
else:
    load_factor = 1.3

specialist_factor = 1.2 if is_specialist else 1.0

viabilidade = 50 * prosp_factor * load_factor * specialist_factor
viabilidade = min(viabilidade, 100)

# Derivar ação
if score >= 70:
    if viabilidade >= 60:
        acao = "🔥 PUSH HARD"
        cor = "#ff4b4b"
    elif viabilidade >= 40:
        acao = "🔄 RE-QUALIFY"
        cor = "#ffa500"
    else:
        acao = "🔀 TRANSFER"
        cor = "#1f77b4"
elif score >= 60:
    if viabilidade >= 60:
        acao = "⚡ ACCELERATE"
        cor = "#ffa500"
    else:
        acao = "🔍 INVESTIGATE"
        cor = "#ffeb3b"
else:
    acao = "⏸ MONITOR"
    cor = "#90ee90"

# Exibir resultados
st.markdown("### 📊 Resultado")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Score Final", f"{score:.1f}")

with col2:
    st.metric("Urgência", f"{urgencia:.1f}")

with col3:
    st.metric("Viabilidade", f"{viabilidade:.1f}")

with col4:
    st.markdown(f"<div style='background-color: {cor}; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;'>{acao}</div>", unsafe_allow_html=True)

# Gráfico de breakdown
fig = go.Figure(data=[
    go.Bar(
        x=['Urgência (50%)', 'Probabilidade (30%)', 'Valor (20%)'],
        y=[urgencia * 0.5, probabilidade * 0.3, valor * 0.2],
        marker_color=['#ff4b4b', '#1f77b4', '#2ca02c'],
        text=[f'{urgencia * 0.5:.1f}', f'{probabilidade * 0.3:.1f}', f'{valor * 0.2:.1f}'],
        textposition='auto'
    )
])
fig.update_layout(
    title=f'Breakdown do Score: {score:.1f}',
    yaxis_title='Contribuição',
    showlegend=False,
    height=300
)
st.plotly_chart(fig, use_container_width=True)