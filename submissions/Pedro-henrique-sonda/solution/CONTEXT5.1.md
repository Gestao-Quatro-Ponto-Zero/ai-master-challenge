# CONTEXT5.md — Score Limpo + Ordenação pelo Vendedor

## O que mudou e por quê

### Problema das versões anteriores
Tentamos várias formas de combinar probabilidade e valor num único score: média ponderada (70/30), valor esperado, log do valor esperado. Nenhuma funcionou bem — ou o valor distorcia o ranking, ou os scores ficavam artificialmente próximos, ou deals de $55 apareciam acima de deals de $5.000.

### A raiz do problema
Estávamos tentando forçar duas dimensões diferentes (chance de fechar vs quanto vale) numa única fórmula. Isso sempre gera distorção porque são naturezas diferentes — probabilidade é uma estimativa de 0 a 100, valor é um número real em dólares.

### A solução limpa
**O score mede uma coisa só: probabilidade de fechar.** O valor do deal aparece como dado real ($), sem normalização nem transformação. O vendedor escolhe como quer ordenar seus deals.

---

## Nova estrutura (v5 — FINAL)

### Score = Probabilidade (0-100)

```python
score = (fator_setor_produto * 0.35) + (fator_historico_conta * 0.30) + (fator_sazonalidade * 0.20) + (fator_tempo * 0.15)
```

Os 4 fatores NÃO mudam. Os pesos NÃO mudam. Tudo que validamos nas etapas anteriores permanece. A única mudança é que não existe mais "Score Final" separado — o score É a probabilidade.

### Valor = dado real ($)

O valor do produto aparece como está: $55, $550, $1.096, $3.393, $4.821, $5.482, $26.768. Sem log, sem normalização, sem fórmula. É o preço de tabela do produto.

### Ordenação escolhida pelo vendedor

Na sidebar, adicionar um seletor de ordenação:

```python
ordenar_por = st.selectbox(
    "📊 Ordenar por",
    options=["Probabilidade (maior chance de fechar)", 
             "Valor (maior ticket)", 
             "Valor Esperado (probabilidade × valor)"],
    index=0
)
```

Comportamento:
- **Probabilidade**: ordena por score decrescente. Top 5 = deals com maior chance de fechar.
- **Valor**: ordena por sales_price decrescente, depois por score como desempate. Top 5 = deals de maior ticket.
- **Valor Esperado**: ordena por (score/100 × sales_price) decrescente. Top 5 = melhor equilíbrio entre chance e valor.

A ordenação afeta TUDO: Top 5 e tabela Pipeline Completo.

---

## Interface atualizada

### Sidebar (ordem dos elementos)

1. Escritório Regional
2. Manager
3. Vendedor
4. Stage
5. **📊 Ordenar por** (NOVO — Probabilidade / Valor / Valor Esperado)
6. Faixa de Score (slider 0-100)

### KPIs — sem mudança
Linha 1: Deals em Aberto, Prioridade Alta (score >70), Valor Potencial Total
Linha 2 (condicional): Taxa de Conversão, Ciclo Médio, Ticket Médio

### Caixa "Como funciona o Score?" — atualizada

```
## Como calculamos o Score de cada deal?

O score vai de 0 a 100 e mede a **probabilidade de fechar** o deal, baseada em 4 fatores históricos:

🏷️ **Produto + Setor do cliente (35%)** — Algumas combinações historicamente fecham mais. Por exemplo, MG Special para telecom fecha 73% das vezes, enquanto MG Advanced para serviços fecha só 52%.

🏢 **Histórico da conta (30%)** — Contas com bom histórico de fechamento recebem pontuação maior. Uma conta que converte 75% vale mais que uma que converte 53%.

📅 **Momento do trimestre (20%)** — Deals fecham muito mais nos meses de final de trimestre (março, junho, setembro, dezembro).

⏱️ **Tempo no pipeline (15%)** — Há quanto tempo o deal está em andamento.

### E o valor do deal?

O valor NÃO está dentro do score — porque são coisas diferentes. O score diz "qual a chance de fechar". O valor diz "quanto vale se fechar".

Você pode escolher como ordenar seus deals:
- **Por Probabilidade**: foco em fechar mais deals
- **Por Valor**: foco nos maiores tickets
- **Por Valor Esperado**: equilíbrio entre chance e valor (probabilidade × valor)

### O que significa cada cor:

🟢 **Verde (acima de 70)** — Alta probabilidade de fechar. Priorize.
🟡 **Amarelo (40 a 70)** — Probabilidade moderada. Acompanhe.
🔴 **Vermelho (abaixo de 40)** — Baixa probabilidade. Reavalie.

### Sobre o estágio:

O estágio (🆕 Novo ou 🔄 Em andamento) NÃO afeta o score. Um deal novo com alto potencial aparece no topo — porque precisa do seu primeiro contato.
```

### Top 5 Prioridades — muda conforme ordenação

O título muda conforme a ordenação selecionada:
- Probabilidade: "🔥 Top 5 — Maior Chance de Fechar"
- Valor: "🔥 Top 5 — Maior Ticket"
- Valor Esperado: "🔥 Top 5 — Melhor Retorno Esperado"

Cada card mostra:
```
#1 — NOME DA CONTA                     🆕 Novo / 🔄 Em andamento
Score XX.X | Produto · $Valor · XX dias
Valor Esperado: $X,XXX

📊 Pontuação detalhada:
| Fator              | Pontos     | Detalhe                                    |
|---------------------|-----------|---------------------------------------------|
| 🏷️ Produto + Setor | XX.X / 35 | setor+produto converte XX% (forte/média/fraca) |
| 🏢 Histórico conta | XX.X / 30 | Conta converte XX% (acima/na/abaixo média)  |
| 📅 Sazonalidade    | XX.X / 20 | mês fechamento trimestral / meio / início   |
| ⏱️ Tempo pipeline  | XX.X / 15 | XX dias / sem data                          |
| **📈 Score (Prob)** | **XX.X / 100** |                                        |
| 💰 Valor do deal    | $X,XXX    | (dado real, não entra no score)             |
| 💵 Valor Esperado   | $X,XXX    | = Score × Valor                             |
```

O Top 5 continua dinâmico (deals com status contatado/em_negociacao/concluido saem).

### Tabela Pipeline Completo

Colunas:
- Score (com cor verde/amarelo/vermelho)
- Estágio (badge 🆕/🔄)
- Conta
- Setor
- Produto
- Valor ($) — dado real
- Valor Esperado ($) — calculado: (score/100) × valor
- Vendedor
- Dias
- Por que esse score? (explicação — garantir largura adequada com column_config)

Ordenada conforme seleção do vendedor na sidebar.

---

## Coluna "Por que esse score?" na tabela — correção de largura

```python
st.dataframe(
    df_display,
    column_config={
        "Por que esse score?": st.column_config.TextColumn(
            width="large"
        )
    },
    use_container_width=True,
    hide_index=True
)
```

Alternativamente, se st.dataframe não suportar largura customizada, usar st.table() ou mostrar a explicação num expander abaixo da tabela.

---

## Checklist para o Claude Code

1. [ ] Score = Probabilidade pura (0-100). Remover qualquer cálculo de "Score Final" separado
2. [ ] Valor do deal aparece como dado real ($), sem transformação
3. [ ] Adicionar coluna "Valor Esperado" = (score/100) × sales_price
4. [ ] Adicionar seletor "Ordenar por" na sidebar (Probabilidade / Valor / Valor Esperado)
5. [ ] Top 5 e tabela mudam conforme ordenação selecionada
6. [ ] Título do Top 5 muda conforme ordenação
7. [ ] Atualizar caixa "Como funciona o Score?" com nova explicação
8. [ ] Atualizar pontuação detalhada nos Top 5 (mostrar valor e valor esperado separados)
9. [ ] Corrigir largura da coluna de explicação na tabela
10. [ ] Manter TUDO: filtros encadeados, KPIs, Top 5 dinâmico, checklist de status, badges de stage, deals em acompanhamento
11. [ ] Os 4 fatores de probabilidade NÃO mudam (pesos, faixas, lógica — tudo igual)
