# CONTEXT6.md — Boost de Recorrência + Ordenação + Correções

## Mudança 1 — "Ordenar por" sai da sidebar, vai acima do Top 5

### O problema
O seletor "Ordenar por" está na sidebar junto com os filtros. Mas ele não é um filtro — é uma escolha de visualização. Deve ficar no corpo principal, logo acima do Top 5.

### Implementação
Remover o st.selectbox("Ordenar por") da sidebar. Colocar no corpo principal, entre a caixa "Como funciona o Score?" e o Top 5:

```python
# No corpo principal, após o expander "Como funciona o Score?"
st.divider()
ordenar_por = st.radio(
    "📊 Ordenar deals por:",
    options=["Probabilidade (maior chance de fechar)", "Valor (maior ticket)"],
    horizontal=True
)
```

Usar st.radio() com horizontal=True para ficar mais visual e rápido de clicar.

---

## Mudança 2 — Boost de Recorrência no Score (NOVO)

### O que descobrimos nos dados
Análise revelou que muitas contas compram o mesmo produto repetidamente:
- Hottechi comprou GTX Basic 37 vezes
- Condax comprou MG Special 30 vezes
- Stanredtax comprou MG Special 18 vezes com 100% de conversão

31,5% dos deals abertos são de combos conta+produto que já tiveram Won antes. Isso é um sinal forte de que o cliente compra de novo.

### A regra
A recorrência NÃO penaliza — apenas bonifica. Quem não tem recorrência fica neutro (não perde nada). Quem tem, ganha boost.

### Como funciona

**Cálculo da recorrência:** Para cada deal aberto, conta quantas vezes aquela conta já comprou (Won) aquele produto específico.

```python
# Contar Won históricos por conta+produto
recompras_historicas = pipeline[pipeline['deal_stage'] == 'Won'].groupby(['account', 'product']).size().to_dict()

# Para cada deal aberto:
vezes_comprou = recompras_historicas.get((row['account'], row['product']), 0)
```

**Boost aditivo (pontos extras sobre o score de probabilidade):**

| Recompras | Boost | Lógica |
|-----------|-------|--------|
| 0 | +0 pts | Sem histórico — neutro |
| 1-3 | +5 pts | Cliente já comprou — sinal positivo |
| 4-10 | +10 pts | Cliente recorrente |
| 11+ | +15 pts | Cliente fiel |

### Nova fórmula (v6 — FINAL)

```python
# Score de probabilidade (0-100) — sem mudança nos 4 fatores
score_probabilidade = (
    fator_setor_produto * 0.35 +
    fator_historico_conta * 0.30 +
    fator_sazonalidade * 0.20 +
    fator_tempo * 0.15
)

# Boost de recorrência (0, 5, 10 ou 15 pontos)
vezes_comprou = recompras_historicas.get((account, product), 0)
if vezes_comprou == 0:
    boost_recorrencia = 0
elif vezes_comprou <= 3:
    boost_recorrencia = 5
elif vezes_comprou <= 10:
    boost_recorrencia = 10
else:
    boost_recorrencia = 15

# Score final = probabilidade + boost, normalizado para 0-100
score_bruto = score_probabilidade + boost_recorrencia
# Normalizar: máximo teórico = 100 + 15 = 115
score = min(100, (score_bruto / 115) * 100)
```

**Importante:** O score máximo teórico agora é 115 (100 da probabilidade + 15 do boost). Normalizamos dividindo por 115 e multiplicando por 100, para que o score final fique na escala 0-100. Deals sem recorrência podem chegar a no máximo 87 (100/115×100). Deals com recorrência alta podem chegar a 100.

### O que o vendedor vê na explicação

Nos Top 5 e na seção de detalhes, a recorrência aparece como fator adicional:

```
📊 Pontuação detalhada:
| Fator                | Pontos     | Detalhe                                         |
|----------------------|-----------|--------------------------------------------------|
| 🏷️ Produto + Setor  | XX.X / 35 | setor+produto converte XX%                       |
| 🏢 Histórico conta  | XX.X / 30 | Conta converte XX%                               |
| 📅 Sazonalidade     | XX.X / 20 | mês de fechamento trimestral                     |
| ⏱️ Tempo pipeline   | XX.X / 15 | XX dias no pipeline                              |
| 📈 Probabilidade base | XX.X / 100 |                                                |
| 🔄 Recorrência      | +XX pts   | Conta comprou esse produto Xx (boost de fidelidade) |
| **🎯 Score Final**   | **XX.X / 100** | Normalizado (probabilidade + boost)         |
```

Se recorrência = 0, a linha mostra: "🔄 Recorrência | +0 pts | Primeira vez dessa combo — neutro"

---

## Mudança 3 — Remover Valor Esperado completamente

Confirmar que TUDO relacionado a valor esperado foi removido:
- [ ] Nenhuma coluna "V. Esperado" na tabela
- [ ] Nenhum "Valor Esperado: $X" nos cards Top 5
- [ ] Nenhuma opção "Valor Esperado" no seletor de ordenação
- [ ] Nenhum cálculo de valor_esperado no código
- [ ] Nenhuma menção na caixa "Como funciona o Score?"

---

## Mudança 4 — Seção "Detalhes dos Deals" no Pipeline Completo

### O problema
A coluna "Por que esse score?" na tabela está cortada e ilegível.

### A solução
Remover a coluna "Por que esse score?" da tabela principal. Adicionar abaixo da tabela uma seção com seletor de deal:

```python
st.divider()
st.subheader("🔍 Detalhes do Deal")
st.caption("Selecione um deal para ver a pontuação detalhada completa")

# Criar label legível para cada deal
df_filtrado['label'] = df_filtrado.apply(
    lambda r: f"{r['account']} — {r['product']} — Score {r['score']:.1f}", axis=1
)

deal_selecionado = st.selectbox(
    "Selecione um deal",
    options=df_filtrado.index.tolist(),
    format_func=lambda i: df_filtrado.loc[i, 'label']
)

if deal_selecionado is not None:
    row = df_filtrado.loc[deal_selecionado]
    # Mostrar pontuação detalhada completa (mesma dos Top 5)
    st.markdown(gerar_explicacao_detalhada(row))
```

### Tabela Pipeline Completo — colunas atualizadas
- Score (com cor)
- Estágio (badge)
- Conta
- Setor
- Produto
- Valor ($)
- Vendedor
- Dias
- Recorrência (Xx) — quantas vezes a conta comprou esse produto

Nova coluna "Recorrência" mostra o número de recompras históricas. Ex: "12x", "0x", "5x".

---

## Mudança 5 — Tratar "nan" nas contas

```python
df['account'] = df['account'].fillna('Conta não identificada')
df['sector'] = df['sector'].fillna('Setor desconhecido')
```

---

## Atualizar caixa "Como funciona o Score?"

```
## Como calculamos o Score de cada deal?

O score vai de 0 a 100 e mede a **probabilidade de fechar** o deal, com bônus para clientes recorrentes.

### Fatores da probabilidade:

🏷️ **Produto + Setor do cliente (35%)** — Combinações que historicamente fecham mais recebem mais pontos.

🏢 **Histórico da conta (30%)** — Contas com bom histórico de conversão pontuam mais.

📅 **Momento do trimestre (20%)** — Final de trimestre = mais fechamentos.

⏱️ **Tempo no pipeline (15%)** — Há quanto tempo o deal está em andamento.

### Bônus de recorrência:

🔄 **Recorrência** — Se a conta já comprou esse mesmo produto antes, o deal recebe um bônus no score. Quanto mais vezes comprou, maior o bônus. Se nunca comprou, não perde pontos — fica neutro.

- Nunca comprou: sem bônus
- 1 a 3 compras anteriores: +5 pontos
- 4 a 10 compras: +10 pontos
- 11+ compras: +15 pontos

### E o valor do deal?

O valor NÃO está no score. Use o filtro **💰 Faixa de Valor** para focar nos deals do tamanho que você quer, e use o score para priorizar dentro dessa faixa.

### Cores:

🟢 **Verde (acima de 70)** — Alta probabilidade. Priorize.
🟡 **Amarelo (40 a 70)** — Moderada. Acompanhe.
🔴 **Vermelho (abaixo de 40)** — Baixa. Reavalie.

### Estágio:

🆕 **Novo** (Prospecting) e 🔄 **Em andamento** (Engaging) NÃO afetam o score. O score mede potencial, não progresso.
```

---

## Checklist para o Claude Code

1. [ ] Mover "Ordenar por" da sidebar para o corpo principal (acima do Top 5, st.radio horizontal)
2. [ ] Opções de ordenação: apenas "Probabilidade" e "Valor" (sem valor esperado)
3. [ ] Implementar boost de recorrência: contar Won históricos por conta+produto
4. [ ] Boost: 0 recompras=+0, 1-3=+5, 4-10=+10, 11+=+15
5. [ ] Score final = (score_probabilidade + boost) normalizado para 0-100 (dividir por 115 × 100)
6. [ ] Mostrar recorrência na explicação detalhada dos Top 5
7. [ ] Adicionar coluna "Recorrência" na tabela (ex: "12x", "0x")
8. [ ] Remover coluna "Por que esse score?" da tabela
9. [ ] Adicionar seção "Detalhes do Deal" abaixo da tabela com seletor + pontuação completa
10. [ ] Remover TUDO de valor esperado (coluna, cálculo, menção)
11. [ ] Tratar nan em conta e setor
12. [ ] Atualizar caixa "Como funciona o Score?"
13. [ ] Manter: filtros (faixa de valor primeiro), KPIs, Top 5 dinâmico, checklist de status, badges, deals em acompanhamento
14. [ ] Os 4 fatores base NÃO mudam — boost é aditivo
