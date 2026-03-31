# CONTEXT8.md — Correção da Normalização + Pipeline como Planilha

## Mudança 1 — Corrigir normalização do boost (CRÍTICO)

### O problema
A divisão por 115 está sendo aplicada em TODOS os deals, inclusive os que não têm boost. Resultado: um deal com probabilidade 84.9 e zero recorrência fica com score 84.9 ÷ 115 × 100 = 73.8. Isso PENALIZA deals sem recorrência, que é exatamente o oposto do que definimos.

### A regra correta
- Deals SEM recorrência (boost = 0): score = probabilidade direta. Sem divisão, sem normalização.
- Deals COM recorrência (boost > 0): score = (probabilidade + boost) normalizado para caber em 0-100.

### Implementação

```python
# Score de probabilidade base (0-100)
score_probabilidade = (
    fator_setor_produto * 0.35 +
    fator_historico_conta * 0.30 +
    fator_sazonalidade * 0.20 +
    fator_tempo * 0.15
)

# Boost de recorrência
vezes_comprou = recompras.get((account, product), 0)
if vezes_comprou == 0:
    boost = 0
elif vezes_comprou <= 3:
    boost = 5
elif vezes_comprou <= 10:
    boost = 10
else:
    boost = 15

# Score final — normalização CONDICIONAL
if boost == 0:
    # Sem recorrência: score = probabilidade direta
    score = score_probabilidade
else:
    # Com recorrência: normalizar (probabilidade + boost) para 0-100
    score_bruto = score_probabilidade + boost
    score = (score_bruto / 115) * 100
```

### Exemplos para validar

| Deal | Probabilidade | Boost | Score bruto | Score final | Correto? |
|------|--------------|-------|-------------|-------------|----------|
| Deal A (0 recompras) | 84.9 | +0 | 84.9 | **84.9** | ✅ Sem penalidade |
| Deal B (14 recompras) | 84.9 | +15 | 99.9 | **86.8** | ✅ Boost aplicado |
| Deal C (5 recompras) | 70.0 | +10 | 80.0 | **69.6** | ✅ Boost aplicado |
| Deal D (0 recompras) | 70.0 | +0 | 70.0 | **70.0** | ✅ Sem penalidade |
| Deal E (2 recompras) | 60.0 | +5 | 65.0 | **56.5** | ✅ Boost aplicado |

**Observação importante:** Com essa lógica, deals COM boost baixo podem ter score MENOR que deals sem boost com mesma probabilidade (Deal D = 70.0 vs Deal C = 69.6). Isso acontece porque a normalização por 115 "comprime" o score. 

Para evitar isso, usar uma abordagem diferente: o boost NUNCA reduz o score abaixo da probabilidade base.

```python
if boost == 0:
    score = score_probabilidade
else:
    score_bruto = score_probabilidade + boost
    score_normalizado = (score_bruto / 115) * 100
    # Garantir que o boost nunca reduz o score
    score = max(score_probabilidade, score_normalizado)
```

Com isso:
| Deal | Probabilidade | Boost | Normalizado | Score final |
|------|--------------|-------|-------------|-------------|
| Deal C (5 recompras) | 70.0 | +10 | 69.6 | **70.0** (usa probabilidade, pois normalizado é menor) |
| Deal B (14 recompras) | 84.9 | +15 | 86.8 | **86.8** (normalizado é maior, aplica boost) |

O boost só sobe o score, nunca desce. Exatamente o que definimos.

### Explicação na pontuação detalhada

**Quando deal TEM boost e o boost efetivamente subiu o score:**
```
| 📈 Probabilidade   | 84.9 / 100 | soma dos 4 fatores                     |
| 🔄 Recorrência     | +15 pts    | Rangreen comprou MG Special 14x        |
| 📊 Score bruto     | 99.9       | = 84.9 + 15.0                          |
| 🎯 Score Final     | 86.8 / 100 | = 99.9 ÷ 115 × 100 (boost aplicado)    |
```

**Quando deal TEM boost mas normalização reduziria (boost não é suficiente):**
```
| 📈 Probabilidade   | 70.0 / 100 | soma dos 4 fatores                     |
| 🔄 Recorrência     | +10 pts    | Conta comprou produto 5x               |
| 🎯 Score Final     | 70.0 / 100 | probabilidade mantida (boost insuficiente para superar normalização) |
```

**Quando deal NÃO tem boost:**
```
| 📈 Probabilidade   | 84.9 / 100 | soma dos 4 fatores                     |
| 🔄 Recorrência     | +0 pts     | primeira vez dessa combinação — neutro  |
| 🎯 Score Final     | 84.9 / 100 | = probabilidade direta                 |
```

---

## Mudança 2 — Pipeline Completo volta a ser planilha (tabela)

### O problema
O Pipeline Completo foi trocado por uma lista paginada com expanders. O vendedor quer a visão de planilha (tabela) que permite ver muitos deals de uma vez e comparar rapidamente.

### A solução
Voltar ao st.dataframe() como visão principal. Adicionar a explicação detalhada como funcionalidade complementar, não substituta.

### Implementação

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

# Tabela principal (planilha)
# Colunas: Score, Estágio, Conta, Setor, Produto, Valor, Vendedor, Dias, Recorrência
st.dataframe(
    df_styled,
    use_container_width=True,
    hide_index=True
)

# Abaixo da tabela: seletor para ver explicação detalhada de qualquer deal
st.markdown("---")
st.markdown("🔍 **Ver pontuação detalhada de um deal:**")

deal_options = df_display.apply(
    lambda r: f"{r['account']} — {r['product']} — Score {r['score']:.1f} — ${r['sales_price']:,.0f}",
    axis=1
).tolist()

selected_idx = st.selectbox(
    "Selecione um deal",
    options=range(len(deal_options)),
    format_func=lambda i: deal_options[i],
    key="detail_select",
    label_visibility="collapsed"
)

if selected_idx is not None:
    row = df_display.iloc[selected_idx]
    with st.container(border=True):
        st.markdown(gerar_explicacao_detalhada(row))
```

### Colunas da tabela
- Score (com cor verde/amarelo/vermelho)
- Estágio (badge 🆕/🔄)
- Conta
- Setor
- Produto
- Valor ($)
- Vendedor
- Dias
- Recorrência (Xx)

Sem coluna de explicação na tabela — a explicação está no seletor abaixo.

---

## Checklist para o Claude Code

1. [ ] Corrigir normalização: SEM boost → score = probabilidade direta (sem divisão por 115)
2. [ ] COM boost → score = max(probabilidade, (probabilidade + boost) ÷ 115 × 100)
3. [ ] Boost NUNCA reduz o score abaixo da probabilidade base
4. [ ] Atualizar explicação na pontuação detalhada com 3 cenários (com boost efetivo, com boost insuficiente, sem boost)
5. [ ] Pipeline Completo volta a ser st.dataframe() (planilha/tabela)
6. [ ] Abaixo da tabela: seletor de deal + explicação detalhada completa
7. [ ] Seletor de ordenação acima do Pipeline (radio horizontal: Probabilidade / Valor)
8. [ ] Manter seletor de ordenação acima do Top 5 também
9. [ ] Manter TUDO: filtros, KPIs, Top 5 dinâmico, checklist, badges, deals em acompanhamento, caixa "Como funciona"
10. [ ] Testar: deal sem recorrência com probabilidade 85 deve ter score = 85 (não 73.9)
