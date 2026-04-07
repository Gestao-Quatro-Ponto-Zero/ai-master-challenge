# Bugs e correções

## 1. Forecast exibido de forma inconsistente

**Sintoma**
- barra visual mostrava um tamanho incompatível com o valor em `%`

**Causa**
- o componente recebia valor em escala `0–1`, mas o texto era interpretado como `%`

**Correção**
- criação e uso de `forecast_pct` em escala `0–100`

## 2. Gráfico da HEAD quebrando por nome de coluna errado

**Sintoma**
- erro em Plotly informando que `best_owner` não existia no dataframe

**Causa**
- a agregação já havia sido renomeada para `suggested_owner`, mas o gráfico ainda apontava para `best_owner`

**Correção**
- troca do eixo para `suggested_owner`

## 3. Warning de Plotly no Streamlit

**Sintoma**
- aviso na interface sobre keyword arguments deprecated

**Causa**
- uso de `width="stretch"` em `st.plotly_chart`

**Correção**
- troca para `use_container_width=True` com `config=...`

## 4. HTML aparecendo como texto literal em alguns cards

**Sintoma**
- o bloco final do card aparecia com tags HTML visíveis

**Causa**
- montagem frágil do trecho final do card dentro do template

**Correção**
- simplificação da composição do HTML para o bloco `deal-reason`

## 5. Ação de transferência de owner na mão do vendedor

**Sintoma**
- a UX colocava no vendedor uma ação que na prática deveria ser decidida pela liderança

**Causa**
- acoplamento direto entre recomendação de owner e fila operacional do vendedor

**Correção**
- mover a movimentação de owner para a `HEAD`
- deixar o vendedor enxergar apenas que recebeu o negócio e o racional

## 6. Fila do vendedor tomada por higiene de CRM

**Sintoma**
- `Completar CRM` dominava a experiência principal do vendedor

**Causa**
- a priorização estava tratando higiene como se fosse ação comercial principal

**Correção**
- separar visualmente higiene de CRM da fila de foco comercial
