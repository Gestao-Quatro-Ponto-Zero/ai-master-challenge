# CONTEXT5_2.md — Filtro de Valor + Remover Valor Esperado + Explicação na Tabela

## Mudança 1 — Filtro de valor do deal na sidebar (PRIORITÁRIO)

### O problema
O vendedor quer primeiro definir "em qual faixa de valor eu quero focar" e depois ver a probabilidade dos deals nessa faixa. Hoje não existe filtro de valor.

### A solução
Adicionar na sidebar, ANTES do filtro de ordenação, um filtro de faixa de valor do produto:

```python
faixa_valor = st.selectbox(
    "💰 Faixa de Valor",
    options=[
        "Todos",
        "Premium ($5.000+)",
        "Médio ($1.000 - $5.000)",
        "Básico (até $1.000)"
    ],
    index=0
)
```

Aplicação:
- "Todos": sem filtro
- "Premium ($5.000+)": sales_price >= 5000 (GTX Plus Pro $5.482 e GTK 500 $26.768)
- "Médio ($1.000 - $5.000)": 1000 <= sales_price < 5000 (GTX Plus Basic $1.096, MG Advanced $3.393, GTXPro $4.821)
- "Básico (até $1.000)": sales_price < 1000 (MG Special $55, GTX Basic $550)

Este filtro afeta TUDO: KPIs, Top 5 e tabela Pipeline Completo.

### Nova ordem dos filtros na sidebar

1. **💰 Faixa de Valor** ← PRIMEIRO (o vendedor define o foco de valor)
2. Escritório Regional
3. Manager
4. Vendedor
5. Stage
6. 📊 Ordenar por (Probabilidade / Valor / ambos)
7. Faixa de Score (slider 0-100)

---

## Mudança 2 — Remover "Valor Esperado" completamente

### O problema
O conceito de "Valor Esperado" (probabilidade × valor) não faz sentido com dados reais. É uma abstração que confunde mais do que ajuda.

### O que remover
- Remover coluna "V. Esperado ($)" da tabela Pipeline Completo
- Remover "Valor Esperado: $X,XXX" dos cards Top 5
- Remover a opção "Valor Esperado (probabilidade × valor)" do seletor de ordenação
- Remover qualquer cálculo de valor_esperado do código
- Remover menção a valor esperado na caixa "Como funciona o Score?"

### Seletor de ordenação atualizado

```python
ordenar_por = st.selectbox(
    "📊 Ordenar por",
    options=["Probabilidade (maior chance de fechar)", 
             "Valor (maior ticket)"],
    index=0
)
```

Apenas duas opções: Probabilidade ou Valor. Simples e claro.

### Colunas da tabela Pipeline Completo (atualizadas)

- Score (com cor verde/amarelo/vermelho)
- Estágio (badge 🆕/🔄)
- Conta
- Setor
- Produto
- Valor ($) — dado real
- Vendedor
- Dias
- Por que esse score?

Sem coluna de Valor Esperado.

### Cards Top 5 (atualizados)

```
#1 — NOME DA CONTA                     🆕 Novo / 🔄 Em andamento
Score XX.X | Produto · $Valor · XX dias
```

Sem linha de "Valor Esperado".

---

## Mudança 3 — Explicação detalhada clicável no Pipeline Completo

### O problema
A coluna "Por que esse score?" na tabela mostra texto cortado. O vendedor não consegue ler a justificativa completa.

### A solução
Substituir a tabela st.dataframe() por uma visualização que permita expandir cada deal.

Implementação: usar um loop com st.expander() para cada deal, ou usar st.dataframe() para a visão resumida + um expander geral abaixo.

**Abordagem recomendada (performance):** Manter a tabela st.dataframe() como visão resumida (sem a coluna "Por que esse score?"), e abaixo da tabela adicionar:

```python
st.subheader("🔍 Detalhes dos Deals")
st.caption("Clique em um deal para ver a pontuação detalhada")

# Seletor de deal
deal_selecionado = st.selectbox(
    "Selecione um deal para ver detalhes",
    options=df_filtrado['opportunity_id'].tolist(),
    format_func=lambda x: f"{df_filtrado[df_filtrado['opportunity_id']==x].iloc[0]['account']} — {df_filtrado[df_filtrado['opportunity_id']==x].iloc[0]['product']} — Score {df_filtrado[df_filtrado['opportunity_id']==x].iloc[0]['score']:.1f}"
)

# Mostrar pontuação detalhada do deal selecionado
if deal_selecionado:
    row = df_filtrado[df_filtrado['opportunity_id'] == deal_selecionado].iloc[0]
    # Mostrar mesma tabela de pontuação detalhada dos Top 5
    st.markdown(gerar_explicacao_detalhada(row))
```

Isso mantém a tabela performática (st.dataframe) e permite ver detalhes de qualquer deal.

---

## Mudança 4 — Tratar "nan" no nome da conta

### O problema
Alguns deals aparecem como "#3 — nan" nos Top 5. Isso acontece porque a conta não tem match no accounts.csv.

### A solução
```python
# Após o merge, tratar contas sem match
df['account'] = df['account'].fillna('Conta não identificada')
df['sector'] = df['sector'].fillna('Setor desconhecido')
```

---

## Atualizar caixa "Como funciona o Score?"

Remover qualquer menção a valor esperado. O texto deve explicar:
1. O score mede probabilidade de fechar (0-100)
2. Os 4 fatores e seus pesos
3. O valor do deal aparece separado — use o filtro de faixa de valor para focar
4. As cores (verde/amarelo/vermelho)
5. O estágio não afeta o score

```
## Como calculamos o Score de cada deal?

O score vai de 0 a 100 e mede a **probabilidade de fechar** o deal, baseada em 4 fatores históricos:

🏷️ **Produto + Setor do cliente (35%)** — Algumas combinações historicamente fecham mais. Por exemplo, MG Special para telecom fecha 73% das vezes, enquanto MG Advanced para serviços fecha só 52%.

🏢 **Histórico da conta (30%)** — Contas com bom histórico de fechamento recebem pontuação maior. Uma conta que converte 75% vale mais que uma que converte 53%.

📅 **Momento do trimestre (20%)** — Deals fecham muito mais nos meses de final de trimestre (março, junho, setembro, dezembro).

⏱️ **Tempo no pipeline (15%)** — Há quanto tempo o deal está em andamento.

### E o valor do deal?

O valor NÃO está dentro do score — porque são coisas diferentes. O score diz "qual a chance de fechar". O valor diz "quanto vale se fechar". Use o filtro **💰 Faixa de Valor** para focar nos deals do tamanho que você quer trabalhar, e depois use o score para priorizar dentro dessa faixa.

### O que significa cada cor:

🟢 **Verde (acima de 70)** — Alta probabilidade de fechar. Priorize.
🟡 **Amarelo (40 a 70)** — Probabilidade moderada. Acompanhe.
🔴 **Vermelho (abaixo de 40)** — Baixa probabilidade. Reavalie.

### Sobre o estágio:

O estágio (🆕 Novo ou 🔄 Em andamento) NÃO afeta o score. Um deal novo com alto potencial aparece no topo — porque precisa do seu primeiro contato.
```

---

## Checklist para o Claude Code

1. [ ] Adicionar filtro "💰 Faixa de Valor" como PRIMEIRO filtro na sidebar
2. [ ] Filtro de valor afeta Top 5, KPIs e tabela
3. [ ] Remover TODA referência a "Valor Esperado": coluna, cálculo, cards, seletor, explicação
4. [ ] Seletor de ordenação: apenas "Probabilidade" e "Valor" (2 opções)
5. [ ] Remover coluna "Por que esse score?" da tabela st.dataframe()
6. [ ] Adicionar seção "🔍 Detalhes dos Deals" abaixo da tabela com seletor de deal + pontuação detalhada
7. [ ] Tratar "nan" em conta e setor (fillna com texto legível)
8. [ ] Atualizar caixa "Como funciona o Score?" (sem valor esperado, com menção ao filtro de valor)
9. [ ] Manter TUDO: filtros encadeados, KPIs, Top 5 dinâmico, checklist de status, badges de stage, deals em acompanhamento
10. [ ] Os 4 fatores de probabilidade NÃO mudam
