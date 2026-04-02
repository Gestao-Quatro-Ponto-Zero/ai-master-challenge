# CONTEXT11.md — Lupa na Planilha + Confirmação Sazonalidade

## Mudança 1 — Lupa clicável ao lado do score na planilha

### O problema
O vendedor quer clicar direto na planilha para ver a explicação do score, sem ir a uma seção separada abaixo.

### A solução
Como st.dataframe() não suporta botões clicáveis dentro das células, a melhor abordagem no Streamlit é renderizar o Pipeline Completo como uma série de linhas customizadas, onde cada linha tem um botão/expander de lupa.

### Implementação

Substituir o st.dataframe() por um layout customizado com st.columns() para cada deal, com um expander na primeira coluna:

```python
st.subheader(f"📋 Pipeline Completo — {len(df_display)} registros")

# Ordenação
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

# Paginação
deals_por_pagina = 25
total_paginas = max(1, (len(df_display) - 1) // deals_por_pagina + 1)
pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, key="pag")
st.caption(f"Página {pagina} de {total_paginas} ({len(df_display)} deals)")

inicio = (pagina - 1) * deals_por_pagina
fim = min(inicio + deals_por_pagina, len(df_display))
df_pagina = df_display.iloc[inicio:fim]

# Cabeçalho
cols_header = st.columns([0.8, 1, 1.5, 1, 1.2, 0.8, 1.3, 0.6, 0.5])
for col, title in zip(cols_header, ["Score", "Estágio", "Conta", "Setor", "Produto", "Valor", "Vendedor", "Dias", "Rec."]):
    col.markdown(f"**{title}**")
st.divider()

# Cada deal como uma linha com expander de lupa
for idx, row in df_pagina.iterrows():
    # Cor do score
    if row['score'] > 70:
        score_str = f"🟢 {row['score']:.1f}"
    elif row['score'] > 40:
        score_str = f"🟡 {row['score']:.1f}"
    else:
        score_str = f"🔴 {row['score']:.1f}"
    
    badge = "🆕 Novo" if row['deal_stage'] == 'Prospecting' else "🔄 Em and."
    dias = f"{int(row['dias_pipeline'])}" if pd.notna(row.get('dias_pipeline')) else "—"
    rec = f"{int(row.get('recompras', 0))}x"
    
    # Linha de dados
    cols = st.columns([0.8, 1, 1.5, 1, 1.2, 0.8, 1.3, 0.6, 0.5])
    cols[0].markdown(score_str)
    cols[1].caption(badge)
    cols[2].markdown(f"**{row['account']}**")
    cols[3].caption(row['sector'])
    cols[4].caption(row['product'])
    cols[5].caption(f"${row['sales_price']:,.0f}")
    cols[6].caption(row['sales_agent'])
    cols[7].caption(dias)
    cols[8].caption(rec)
    
    # Expander de lupa logo abaixo da linha
    with st.expander(f"🔍 Pontuação detalhada — {row['account']}"):
        st.markdown(gerar_explicacao_detalhada(row))
    
    st.markdown("---")  # Separador leve entre deals
```

### Resultado visual

```
Score    Estágio    Conta          Setor       Produto        Valor    Vendedor         Dias  Rec.
──────────────────────────────────────────────────────────────────────────────────────────────────
🟢 87.0  🔄 Em and. Condax         retail      MG Special     $55      Versie Hille..   144   30x
🔍 Pontuação detalhada — Condax
  [clicou → abre tabela completa de fatores e pontos]
──────────────────────────────────────────────────────────────────────────────────────────────────
🟢 86.8  🔄 Em and. Rangreen       technolgy   MG Special     $55      Anna Snelling    144   14x
🔍 Pontuação detalhada — Rangreen
  [fechado — clique para expandir]
──────────────────────────────────────────────────────────────────────────────────────────────────
```

Cada deal ocupa uma linha. A lupa está logo abaixo, acoplada à linha. Clicou, abriu. Simples.

---

## Mudança 2 — Confirmação sobre sazonalidade

### Análise realizada
Investigamos se a sazonalidade trimestral é universal ou se varia por setor/produto. Resultado:

**TODOS os 10 setores seguem o padrão trimestral:**
- Menor diferença: software (+24.9 pontos percentuais)
- Maior diferença: employment (+34.5 pontos percentuais)
- NENHUM setor fora do padrão

**TODOS os 7 produtos seguem o padrão trimestral:**
- GTK 500: +58.8pp (100% no trimestre vs 41% fora)
- MG Advanced: +26.2pp (menor diferença entre produtos)
- NENHUM produto fora do padrão

**Não existe padrão bimestral** (pares 63.5% vs ímpares 62.8% — irrelevante)
**Padrão semestral é redundante** (jun+dez 80.7% — mesmos meses do trimestral)

### Decisão
**Manter sazonalidade aplicada a TODOS os deals.** O padrão é universal e afeta todas as combinações de setor e produto sem exceção. Não há subgrupo que precise de tratamento diferenciado.

Nenhuma mudança no fator sazonalidade.

---

## Checklist para o Claude Code

1. [ ] Pipeline Completo: cada deal como linha com st.columns + expander "🔍 Pontuação detalhada" acoplado
2. [ ] Layout de cabeçalho + linhas de dados (Score, Estágio, Conta, Setor, Produto, Valor, Vendedor, Dias, Rec.)
3. [ ] Expander de lupa logo abaixo de cada linha com explicação completa
4. [ ] Paginação: 25 deals por página
5. [ ] Ordenação (radio horizontal) acima da lista
6. [ ] Score com cor (🟢/🟡/🔴) e badge de estágio (🆕/🔄) na linha
7. [ ] Remover st.dataframe() e seletor separado de deal que existiam antes
8. [ ] Sazonalidade: SEM mudança — manter aplicada a todos os deals
9. [ ] Manter TUDO: filtros, KPIs, Top 5 dinâmico, checklist, boost recorrência, deals em acompanhamento, caixa "Como funciona"
