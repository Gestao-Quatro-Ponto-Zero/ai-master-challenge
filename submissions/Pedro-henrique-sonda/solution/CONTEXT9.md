# CONTEXT9.md — Lupa de Pontuação na Planilha + Limpeza Final

## Mudança única — Explicação do score acoplada na planilha

### O problema
A explicação detalhada do score está numa seção separada abaixo da tabela. O vendedor quer ver a explicação direto na planilha, ao lado do score.

### A solução
Substituir o st.dataframe() do Pipeline Completo por uma renderização customizada onde cada deal tem um expander inline.

### Implementação

Trocar o st.dataframe() por um loop que renderiza cada deal como uma linha visual com expander:

```python
st.subheader(f"📋 Pipeline Completo — {len(df_display)} registros")

# Seletor de ordenação
ordenar_pipeline = st.radio(
    "📊 Ordenar por:",
    options=["Probabilidade", "Valor"],
    horizontal=True,
    key="ord_pipeline"
)

if ordenar_pipeline == "Valor":
    df_display = df_display.sort_values('sales_price', ascending=False)
else:
    df_display = df_display.sort_values('score', ascending=False)

# Cabeçalho da tabela
header_cols = st.columns([0.6, 0.8, 1.2, 1, 1, 0.8, 1.2, 0.6, 0.6])
headers = ["🔍", "Score", "Conta", "Setor", "Produto", "Valor", "Vendedor", "Dias", "Rec."]
for col, h in zip(header_cols, headers):
    col.markdown(f"**{h}**")

st.divider()

# Paginação
deals_por_pagina = 25
total_paginas = max(1, (len(df_display) - 1) // deals_por_pagina + 1)

col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
with col_pag2:
    pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, key="pagina_pipeline")
    st.caption(f"Página {pagina} de {total_paginas}")

inicio = (pagina - 1) * deals_por_pagina
fim = min(inicio + deals_por_pagina, len(df_display))
df_pagina = df_display.iloc[inicio:fim]

# Renderizar cada deal
for idx, row in df_pagina.iterrows():
    # Cor do score
    if row['score'] > 70:
        score_color = "🟢"
    elif row['score'] > 40:
        score_color = "🟡"
    else:
        score_color = "🔴"
    
    # Badge de stage
    badge = "🆕" if row['deal_stage'] == 'Prospecting' else "🔄"
    
    # Dias formatado
    dias = f"{int(row['dias_pipeline'])}" if pd.notna(row.get('dias_pipeline')) else "—"
    
    # Recorrência
    rec = f"{int(row.get('recompras', 0))}x"
    
    # Linha do deal com expander na primeira coluna
    with st.expander(f"{score_color} **{row['score']:.1f}** | {badge} {row['account']} — {row['product']} — ${row['sales_price']:,.0f} — {row['sales_agent']} — {dias} dias — Rec: {rec}"):
        st.markdown(gerar_explicacao_detalhada(row))
```

### Resultado visual

Cada deal aparece como uma linha compacta. O vendedor clica para expandir e ver a pontuação completa:

```
🟢 86.8 | 🔄 Rangreen — MG Special — $55 — Anna Snelling — 144 dias — Rec: 14x
  [clicou → abre pontuação detalhada completa com tabela de fatores]

🟢 84.9 | 🆕 Scotfind — GTX Plus Pro — $5,482 — Anna Snelling — — dias — Rec: 0x
  [fechado — clique para expandir]

🟡 65.2 | 🔄 Hottechi — GTX Basic — $550 — Kami Bicknell — 200 dias — Rec: 37x
  [fechado — clique para expandir]
```

### Remover
- Remover a seção "🔍 Ver pontuação detalhada de um deal" que estava abaixo da tabela (o seletor de deal separado)
- Remover o st.dataframe() do Pipeline Completo
- A explicação agora está DENTRO de cada expander na própria lista

---

## Limpeza geral

Verificar que tudo dos contexts anteriores está funcionando:
- [ ] Filtro de faixa de valor (primeiro na sidebar)
- [ ] Filtros encadeados (escritório → manager → vendedor)
- [ ] KPIs (linha 1 sempre, linha 2 condicional)
- [ ] Caixa "Como funciona o Score?"
- [ ] Seletor de ordenação acima do Top 5
- [ ] Top 5 dinâmico com checklist de status
- [ ] Deals em Acompanhamento (expander)
- [ ] Badges de stage (🆕/🔄)
- [ ] Normalização do boost correta (sem penalizar deals sem recorrência)
- [ ] Nenhuma referência a "valor esperado"
- [ ] nan tratado ("Conta não identificada")

---

## Checklist para o Claude Code

1. [ ] Substituir st.dataframe() do Pipeline por lista de expanders com pontuação detalhada
2. [ ] Cada deal = 1 expander: linha compacta com score, badge, conta, produto, valor, vendedor, dias, recorrência
3. [ ] Dentro do expander: pontuação detalhada completa (mesma dos Top 5)
4. [ ] Paginação: 25 deals por página
5. [ ] Remover seção separada "Ver pontuação detalhada" abaixo da tabela
6. [ ] Seletor de ordenação (radio horizontal) acima da lista do Pipeline
7. [ ] Manter TUDO dos contexts anteriores (verificar checklist de limpeza acima)
