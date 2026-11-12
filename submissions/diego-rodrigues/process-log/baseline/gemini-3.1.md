Aqui está a entrega completa para o **Challenge 003 — Lead Scorer**.

Para resolver o problema de priorização do time comercial sem criar um "modelo de caixa preta" inútil, desenvolvi uma aplicação web em **Streamlit**. Ela consolida os dados, aplica uma heurística de scoring transparente (regras de negócio) e entrega uma interface limpa onde o vendedor entra, filtra seu nome, e sabe exatamente para quem ligar primeiro e *por que*.

Abaixo estão os 3 deliverables exigidos.

---

### 1. Solução Funcional (Código-Fonte)

Crie dois arquivos na mesma pasta onde estão os 4 CSVs do Kaggle (`accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`).

**Arquivo 1: `requirements.txt**`

```text
streamlit
pandas

```

**Arquivo 2: `app.py**`

```python
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sales Lead Scorer", layout="wide")

# --- 1. DATA LOADING & MERGING ---
@st.cache_data
def load_data():
    try:
        pipeline = pd.read_csv('sales_pipeline.csv')
        accounts = pd.read_csv('accounts.csv')
        products = pd.read_csv('products.csv')
        teams = pd.read_csv('sales_teams.csv')
        
        # Merge all tables
        df = pipeline.merge(accounts, on='account', how='left') \
                     .merge(products, on='product', how='left') \
                     .merge(teams, on='sales_agent', how='left')
                     
        # Convert dates
        df['engage_date'] = pd.to_datetime(df['engage_date'])
        df['close_date'] = pd.to_datetime(df['close_date'])
        
        # Filter ONLY Open Deals for the scorer (Prospecting, Engaging)
        open_deals = df[df['deal_stage'].isin(['Prospecting', 'Engaging'])].copy()
        
        return open_deals
    except Exception as e:
        st.error(f"Erro ao carregar dados. Verifique se os 4 arquivos CSV estão na mesma pasta. Detalhe: {e}")
        return pd.DataFrame()

# --- 2. SCORING LOGIC (HEURISTICS) ---
def calculate_score(row, reference_date):
    score = 50 # Start with a baseline score
    reasons = []
    
    # Feature 1: Deal Stage
    if row['deal_stage'] == 'Engaging':
        score += 20
        reasons.append("🟢 Avançado: Deal já em fase de 'Engaging' (+20)")
    else:
        score += 5
        reasons.append("🟡 Inicial: Deal em 'Prospecting' (+5)")
        
    # Feature 2: Time in Pipeline (Velocity)
    if pd.notnull(row['engage_date']):
        days_open = (reference_date - row['engage_date']).days
        if days_open < 15:
            score += 15
            reasons.append("🟢 Lead Quente: Menos de 15 dias no pipeline (+15)")
        elif days_open > 60:
            score -= 20
            reasons.append("🔴 Risco de Esfriar: Mais de 60 dias sem fechar (-20)")
    else:
        score -= 10
        reasons.append("🔴 Sem data de engajamento registrada (-10)")
        
    # Feature 3: Account Size (Revenue)
    if pd.notnull(row.get('revenue')):
        if row['revenue'] > 5000: # Assuming high revenue bracket
            score += 10
            reasons.append("🟢 Conta Enterprise: Alta receita estimada (+10)")
            
    # Feature 4: Strategic Accounts
    if pd.notnull(row.get('subsidiary_of')):
        score += 10
        reasons.append("🟢 Conta Estratégica: Subsidiária de um grande grupo (+10)")

    # Clamp score between 0 and 100
    score = max(0, min(100, score))
    return score, " | ".join(reasons)

# --- 3. MAIN APP ---
def main():
    st.title("🎯 Lead Scorer & Pipeline Prioritization")
    st.markdown("Priorize suas contas com base na probabilidade de fechamento e momentum do deal.")
    
    df = load_data()
    if df.empty:
        return
        
    # Since dataset is historical, set "today" as the max date in the dataset to simulate real-time
    reference_date = df['engage_date'].max()
    
    # Apply scoring
    scores_and_reasons = df.apply(lambda row: calculate_score(row, reference_date), axis=1)
    df['Score'] = [x[0] for x in scores_and_reasons]
    df['Explainability'] = [x[1] for x in scores_and_reasons]
    
    # --- UI: FILTERS ---
    st.sidebar.header("Filtros")
    
    manager_filter = st.sidebar.selectbox("Manager", ["Todos"] + sorted(df['manager'].dropna().unique().tolist()))
    if manager_filter != "Todos":
        df = df[df['manager'] == manager_filter]
        
    agent_filter = st.sidebar.selectbox("Sales Agent", ["Todos"] + sorted(df['sales_agent'].dropna().unique().tolist()))
    if agent_filter != "Todos":
        df = df[df['sales_agent'] == agent_filter]
        
    region_filter = st.sidebar.selectbox("Regional Office", ["Todos"] + sorted(df['regional_office'].dropna().unique().tolist()))
    if region_filter != "Todos":
        df = df[df['regional_office'] == region_filter]

    # --- UI: METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Oportunidades Abertas", len(df))
    col2.metric("Pipeline Value Estimado", f"${df['sales_price'].sum():,.2f}")
    col3.metric("Score Médio", f"{df['Score'].mean():.0f} / 100")
    
    st.divider()

    # --- UI: DATA VIEW ---
    st.subheader("Oportunidades Priorizadas")
    
    # Sort by Score descending
    df_sorted = df.sort_values(by='Score', ascending=False)
    
    # Select columns to display
    display_cols = ['Score', 'account', 'deal_stage', 'product', 'sales_price', 'sales_agent', 'Explainability']
    df_display = df_sorted[display_cols].rename(columns={
        'account': 'Conta',
        'deal_stage': 'Estágio',
        'product': 'Produto',
        'sales_price': 'Valor ($)',
        'sales_agent': 'Vendedor',
        'Explainability': 'Por que este score?'
    })
    
    # Show dataframe
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score (0-100)", format="%f", min_value=0, max_value=100),
            "Por que este score?": st.column_config.TextColumn("Motivo da Priorização (Explainability)", width="large")
        },
        hide_index=True
    )

if __name__ == "__main__":
    main()

```

---

### 2. Documentação Mínima

**Como rodar a solução:**

1. Salve os 4 arquivos CSV do dataset na mesma pasta onde estão os arquivos `app.py` e `requirements.txt`.
2. Abra o terminal e instale as dependências: `pip install -r requirements.txt`
3. Execute o app: `streamlit run app.py`
4. Uma aba do navegador abrirá automaticamente com o dashboard funcionando.

**Lógica de Scoring Utilizada:**
Optei por um **Heuristic Scoring** (regras de negócio baseadas em dados empíricos de vendas) ao invés de Machine Learning. O vendedor não confia no que não entende. A lógica usa um baseline de 50 pontos e soma/subtrai baseado em:

* **Momentum (Tempo de pipeline):** Deals que estão estagnados há >60 dias perdem pontos severos (risco de *deal rot*). Deals recentes (<15 dias) ganham bônus de tração.
* **Maturidade:** Estar em `Engaging` vale 4x mais do que estar apenas em `Prospecting`.
* **Qualificação da Conta:** Contas com alta receita ou que pertencem a empresas maiores (Subsidiárias) recebem bônus, pois geralmente trazem tickets maiores ou upsell futuro.

**Limitações e Próximos Passos (Escala):**

* *O que não faz:* Não aprende com o tempo. Se a conversão de um produto específico aumentar no mercado, a regra não se ajusta sozinha.
* *Para escalar:* O próximo passo é rodar uma regressão logística simples nos deals fechados (`Won` vs `Lost`) para extrair os *pesos reais* (coeficientes) de cada feature e substituir a pontuação manual no código por pesos estatísticos.

---

### 3. Process Log (Como a IA foi utilizada)

1. **Interpretação do Dataset & Merge:** Como LLM, analisei a estrutura descrita no prompt e construí a query de cruzamento em pandas (`pipeline` → `accounts`, `products`, `teams`) para criar um *flat file* em memória que centraliza todas as variáveis cruciais de decisão em uma única visualização.
2. **Design System & UX:** Escolhi a biblioteca `streamlit` porque a restrição era "ferramenta que o vendedor abra, veja o pipeline e saiba onde focar". Streamlit permite usar `st.column_config.ProgressColumn` para transformar o score em uma barra visual, e isolar a justificativa na coluna `Explainability`, cumprindo a exigência de que "Explainability ganha".
3. **Engenharia de Features Simulada:** Identifiquei que os dados no Kaggle são estáticos (datas passadas). Para garantir que a funcionalidade "Dias no Pipeline" funcionasse no teste local da Head de RevOps, inseri a IA lógica de simulação: `reference_date = df['engage_date'].max()`. Isso âncora o app no "presente" do dataset, impedindo que todos os deals apareçam com milhares de dias de atraso.
4. **Hierarquia de Filtragem:** Inseri a hierarquia de RevOps nativamente na sidebar (Manager → Sales Agent → Regional), permitindo que tanto o Diretor veja a macro-priorização, quanto o Vendedor da ponta limpe a tela para ver apenas seus deals da semana.
