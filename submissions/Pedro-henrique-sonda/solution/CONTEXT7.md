# CONTEXT7.md — Clareza no Score + Ordenação + Explicação na Tabela

## Mudança 1 — Mostrar a conta completa do score na explicação

### O problema
O score mostra 86.8/100 mas o vendedor vê "Probabilidade base: 84.9" e "Boost: +15" e não entende como 84.9 + 15 = 86.8. A normalização por 115 é invisível e confusa.

### A solução
Mostrar TODAS as etapas do cálculo na pontuação detalhada, incluindo a normalização:

```
📊 Pontuação detalhada:

| Fator                | Pontos      | Detalhe                                         |
|----------------------|------------|--------------------------------------------------|
| 🏷️ Produto + Setor  | 27.6 / 35  | technolgy+MG Special converte 69% (forte)        |
| 🏢 Histórico conta  | 30.0 / 30  | Rangreen converte 75% (acima da média)           |
| 📅 Sazonalidade     | 19.0 / 20  | mês de fechamento trimestral (boost)             |
| ⏱️ Tempo pipeline   |  8.2 / 15  | 144 dias no pipeline                             |
|                      |            |                                                   |
| 📈 **Probabilidade** | **84.9**   | soma dos 4 fatores acima (máx 100)               |
| 🔄 Recorrência      | **+15.0**  | Rangreen comprou MG Special 14x (cliente fiel)   |
|                      |            |                                                   |
| 📊 Score bruto       | **99.9**   | = 84.9 + 15.0                                    |
| 🎯 **Score Final**   | **86.8**   | = 99.9 ÷ 115 × 100 (normalizado para escala 0-100) |
| 💰 Valor do deal     | $55        | (dado real, não entra no score)                  |
```

O ponto chave é a linha "Score bruto" que mostra a soma real, e a linha "Score Final" que explica a divisão por 115. Assim o vendedor vê:
1. Os 4 fatores somam 84.9
2. O boost adiciona +15
3. Total bruto: 99.9
4. Normalizado: 99.9 ÷ 115 × 100 = 86.8

### Explicação simplificada para a caixa "Como funciona o Score?"

Adicionar um parágrafo explicando a normalização em linguagem simples:

```
### Por que o score máximo é 100?

Os 4 fatores de probabilidade somam até 100 pontos. O bônus de recorrência pode adicionar até 15 pontos extras, totalizando 115. Para manter o score na escala de 0 a 100, dividimos o total por 115 e multiplicamos por 100. 

Na prática: um deal sem recorrência pode chegar a no máximo ~87. Um deal com recorrência máxima pode chegar a 100. Isso garante que clientes recorrentes sempre se destaquem.
```

---

## Mudança 2 — Seletor de ordenação aparece em DOIS lugares

### O problema
O seletor "Ordenar por" aparece só antes do Top 5. O vendedor quer poder mudar a ordenação do Pipeline Completo também, independentemente.

### A solução
O seletor de ordenação aparece em dois lugares:

**1. Acima do Top 5** (já existe):
```python
st.divider()
ordenar_top5 = st.radio(
    "📊 Ordenar Top 5 por:",
    options=["Probabilidade (maior chance de fechar)", "Valor (maior ticket)"],
    horizontal=True,
    key="ordenar_top5"
)
```

**2. Acima do Pipeline Completo** (NOVO):
```python
st.divider()
st.subheader("📋 Pipeline Completo")
ordenar_pipeline = st.radio(
    "📊 Ordenar pipeline por:",
    options=["Probabilidade (maior chance de fechar)", "Valor (maior ticket)"],
    horizontal=True,
    key="ordenar_pipeline"
)
```

Cada um controla sua respectiva seção independentemente. O vendedor pode ter Top 5 por probabilidade e Pipeline por valor, por exemplo.

---

## Mudança 3 — Explicação do score DENTRO da tabela Pipeline Completo

### O problema
A explicação do score está abaixo da tabela num seletor separado. O vendedor quer clicar direto na tabela e ver a explicação.

### A solução
Substituir o st.dataframe() por uma renderização com st.expander() para cada deal. Mas isso seria lento com 2000+ deals.

**Abordagem prática:** Manter st.dataframe() como visão principal, mas adicionar uma coluna "📊" que, quando o vendedor seleciona um deal na tabela, mostra a explicação logo abaixo.

**Implementação com st.dataframe + seleção:**

```python
st.subheader(f"📋 Pipeline Completo — {len(df_display)} registros")

# Radio de ordenação
ordenar_pipeline = st.radio(
    "📊 Ordenar por:",
    options=["Probabilidade", "Valor"],
    horizontal=True,
    key="ord_pipeline"
)

# Ordenar
if ordenar_pipeline == "Valor":
    df_display = df_display.sort_values('sales_price', ascending=False)
else:
    df_display = df_display.sort_values('score', ascending=False)

# Tabela com colunas: Score, Estágio, Conta, Setor, Produto, Valor, Vendedor, Dias, Recorrência
st.dataframe(
    df_styled,
    use_container_width=True,
    hide_index=True
)

# Seletor de deal para ver detalhes (logo abaixo da tabela)
st.markdown("---")
st.markdown("**🔍 Selecione um deal acima para ver a pontuação detalhada:**")

deal_options = df_display.apply(
    lambda r: f"{r['account']} — {r['product']} — Score {r['score']:.1f} — ${r['sales_price']:,.0f}",
    axis=1
).tolist()

selected_idx = st.selectbox(
    "Deal",
    options=range(len(deal_options)),
    format_func=lambda i: deal_options[i],
    key="detail_select"
)

if selected_idx is not None:
    row = df_display.iloc[selected_idx]
    st.markdown(gerar_explicacao_detalhada(row))
```

**Alternativa mais elegante (se performance permitir):** Usar paginação. Mostrar 20 deals por vez com st.expander() para cada um:

```python
# Paginação
deals_por_pagina = 20
total_paginas = (len(df_display) - 1) // deals_por_pagina + 1
pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1)

inicio = (pagina - 1) * deals_por_pagina
fim = inicio + deals_por_pagina
df_pagina = df_display.iloc[inicio:fim]

for idx, row in df_pagina.iterrows():
    # Cor do score
    if row['score'] > 70:
        cor = "🟢"
    elif row['score'] > 40:
        cor = "🟡"
    else:
        cor = "🔴"
    
    badge = "🆕" if row['deal_stage'] == 'Prospecting' else "🔄"
    
    with st.expander(
        f"{cor} {row['score']:.1f} | {badge} {row['account']} — {row['product']} — ${row['sales_price']:,.0f} — {row['sales_agent']} — {int(row.get('dias_pipeline', 0)) if pd.notna(row.get('dias_pipeline')) else '—'} dias — Recorrência: {int(row.get('recompras', 0))}x"
    ):
        st.markdown(gerar_explicacao_detalhada(row))
```

**Recomendação:** Usar a abordagem de paginação com expander. É mais intuitiva — o vendedor vê a lista e clica para expandir qualquer deal. 20 por página mantém a performance.

---

## Checklist para o Claude Code

1. [ ] Mostrar conta completa do score na explicação: 4 fatores → probabilidade → boost → score bruto → normalização → score final
2. [ ] Adicionar linhas "Score bruto" e explicação da normalização (÷115×100) na pontuação detalhada
3. [ ] Atualizar caixa "Como funciona o Score?" com parágrafo sobre normalização
4. [ ] Seletor de ordenação em DOIS lugares: acima do Top 5 E acima do Pipeline Completo
5. [ ] Cada seletor controla sua seção independentemente
6. [ ] Pipeline Completo: substituir st.dataframe por lista paginada com st.expander por deal
7. [ ] Paginação: 20 deals por página, cada deal é um expander clicável
8. [ ] Dentro do expander: pontuação detalhada completa (mesma dos Top 5)
9. [ ] Linha do expander mostra: cor do score, badge stage, conta, produto, valor, vendedor, dias, recorrência
10. [ ] Manter TUDO: filtros, KPIs, Top 5 dinâmico, checklist, badges, deals em acompanhamento
