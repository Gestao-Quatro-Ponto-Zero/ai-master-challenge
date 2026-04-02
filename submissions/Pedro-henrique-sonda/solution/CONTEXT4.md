# CONTEXT4.md — Ajustes de Scoring e Top 5 Dinâmico

## Mudança 1 — Stage sai do cálculo do score (CONCEITUAL)

### O problema
Um deal em Prospecting com uma conta que converte 75% e produto forte tem o MESMO potencial que esse deal em Engaging. A única diferença é que um já foi contatado e outro não. Penalizar Prospecting no score empurra oportunidades excelentes para baixo do ranking — e o vendedor nunca liga para elas.

Na verdade, um deal em Prospecting com alto potencial é MAIS urgente — porque está parado esperando o primeiro contato. É exatamente o tipo de oportunidade que esfria se ninguém agir.

### A mudança
O score agora mede **potencial do deal**, não estágio de progresso. Stage sai do cálculo numérico e vira um **indicador visual separado**.

Um deal em Prospecting e o mesmo deal em Engaging (mesma conta, mesmo produto) terão o **mesmo score**.

### Nova fórmula (v3)

```
Score Probabilidade = (Setor_Produto × 0.35) + (Historico_Conta × 0.30) + (Sazonalidade × 0.20) + (Tempo × 0.15)
```

**Redistribuição dos pesos (Stage removido, 20% redistribuído):**
- Setor+Produto: de 0.30 → 0.35
- Histórico da Conta: de 0.25 → 0.30
- Sazonalidade: de 0.15 → 0.20
- Tempo: de 0.10 → 0.15

**Score Final permanece:**
```
Score Final = (Score Probabilidade × 0.70) + (Score Valor × 0.30)
```

### Stage como indicador visual
Na interface (Top 5 e tabela), o stage aparece como badge:
- 🆕 **Novo** — Prospecting (precisa de primeiro contato)
- 🔄 **Em andamento** — Engaging (já houve interação)

Isso dá contexto sem distorcer o score. O vendedor vê: "Score 78, deal NOVO — preciso ligar AGORA porque ninguém falou com esse cliente ainda."

### Fator Tempo para Prospecting
Com stage fora do score, Prospecting continua sem engage_date. Manter o tempo como neutro (50 pontos) para Prospecting. Isso é justo: não temos data para calcular, então não prejudicamos nem beneficiamos.

---

## Mudança 2 — Pontuação detalhada na explicação das prioridades

### O problema
A explicação atual diz "Probabilidade alta" mas o vendedor não sabe quanto cada fator contribuiu.

### A solução
Mostrar a pontuação EXATA de cada fator no card do Top 5. Formato:

```
#1 — RANGREEN                                          🆕 Novo
Score 78.2 | MG Special · $55 · Prospecting · —

📊 Pontuação detalhada:
   🏷️ Produto + Setor:  32.4 / 35 pts  — telecom + MG Special converte 73% (forte)
   🏢 Histórico conta:  27.6 / 30 pts  — Rangreen converte 75% (acima da média)
   📅 Sazonalidade:     19.0 / 20 pts  — mês de fechamento trimestral (boost)
   ⏱️ Tempo pipeline:    7.5 / 15 pts  — sem data (Prospecting)
   ─────────────────────────────────
   📈 Probabilidade:    86.5 / 100
   💰 Valor:            39.3 / 100     — $55 (baixo)
   ─────────────────────────────────
   🎯 Score Final:      78.2 / 100     = (86.5 × 0.70) + (39.3 × 0.30)
```

### Implementação

Para cada deal no Top 5, calcular e exibir:

```python
def gerar_explicacao_detalhada(row):
    # Pontos individuais de cada fator
    pts_setor_produto = row['fator_setor_produto'] * 0.35
    pts_conta = row['fator_historico_conta'] * 0.30
    pts_sazonalidade = row['fator_sazonalidade'] * 0.20
    pts_tempo = row['fator_tempo'] * 0.15
    
    # Labels descritivos
    label_combo = "forte" if row['taxa_combo'] >= 0.68 else "média" if row['taxa_combo'] >= 0.57 else "fraca"
    label_conta = "acima da média" if row['taxa_conta'] >= 0.68 else "na média" if row['taxa_conta'] >= 0.58 else "abaixo da média"
    
    # Sazonalidade
    mes_ref = row.get('mes_referencia', 12)
    if mes_ref in [3,6,9,12]:
        label_saz = "mês de fechamento trimestral (boost)"
    elif mes_ref in [2,5,8,11]:
        label_saz = "meio do trimestre"
    else:
        label_saz = "início do trimestre"
    
    # Tempo
    if pd.isna(row.get('dias_pipeline')):
        label_tempo = "sem data (Prospecting)"
    else:
        label_tempo = f"{int(row['dias_pipeline'])} dias no pipeline"
    
    # Valor
    if row['sales_price'] >= 5000:
        label_valor = "alto"
    elif row['sales_price'] >= 1000:
        label_valor = "médio"
    else:
        label_valor = "baixo"
    
    texto = f"""📊 **Pontuação detalhada:**
| Fator | Pontos | Detalhe |
|-------|--------|---------|
| 🏷️ Produto + Setor | {pts_setor_produto:.1f} / 35 | {row['sector']}+{row['product']} converte {row['taxa_combo']*100:.0f}% ({label_combo}) |
| 🏢 Histórico conta | {pts_conta:.1f} / 30 | {row['account']} converte {row['taxa_conta']*100:.0f}% ({label_conta}) |
| 📅 Sazonalidade | {pts_sazonalidade:.1f} / 20 | {label_saz} |
| ⏱️ Tempo pipeline | {pts_tempo:.1f} / 15 | {label_tempo} |
| **📈 Probabilidade** | **{row['score_probabilidade']:.1f} / 100** | |
| 💰 Valor | {row['score_valor']:.1f} / 100 | ${row['sales_price']:,.0f} ({label_valor}) |
| **🎯 Score Final** | **{row['score_final']:.1f} / 100** | = (Prob × 0.70) + (Valor × 0.30) |"""
    
    return texto
```

Para a tabela principal, manter explicação resumida (1 linha) como está.

---

## Mudança 3 — Top 5 dinâmico (deals saem quando recebem status)

### O conceito
O Top 5 deve ser sempre "os 5 deals que AINDA precisam de ação do vendedor". Quando o vendedor marca um deal com um status que indica que já houve ação, esse deal sai do Top 5 e o próximo da fila entra.

### Status que REMOVEM o deal do Top 5:
- ✅ Concluído — deal avançou
- 🔄 Em negociação — retorno positivo
- 📞 Contatado — aguardando retorno

### Status que MANTÊM o deal no Top 5:
- ⬜ Não contatado (padrão) — ainda precisa de ação
- ❌ Sem retorno — reagendar — precisa de nova tentativa

### Implementação

```python
def get_top5_deals(deals_filtrados, deal_status_df):
    """
    Retorna os top 5 deals que ainda precisam de ação.
    Exclui deals com status: contatado, em_negociacao, concluido
    """
    # Status que removem do top 5
    status_removem = ['contatado', 'em_negociacao', 'concluido']
    
    # IDs dos deals que já tiveram ação
    if not deal_status_df.empty:
        deals_com_acao = deal_status_df[
            deal_status_df['status'].isin(status_removem)
        ]['opportunity_id'].tolist()
    else:
        deals_com_acao = []
    
    # Filtrar: pegar deals que NÃO estão na lista de ação
    deals_pendentes = deals_filtrados[
        ~deals_filtrados['opportunity_id'].isin(deals_com_acao)
    ]
    
    # Ordenar por score e pegar top 5
    top5 = deals_pendentes.nlargest(5, 'score_final')
    
    return top5
```

### UX do Top 5 dinâmico

1. Vendedor abre a ferramenta → vê Top 5 com deals "⬜ Não contatado"
2. Marca deal #1 como "📞 Contatado — aguardando retorno" 
3. Deal #1 sai do Top 5 → deal #6 (próximo da fila) entra como novo #5
4. O vendedor sempre tem 5 deals pendentes para trabalhar
5. Se TODOS os deals foram contatados, mostrar mensagem: "🎉 Todos os deals prioritários já foram trabalhados! Revise os deals em acompanhamento abaixo."

### Seção adicional: "Deals em Acompanhamento"

Abaixo do Top 5, adicionar uma seção colapsável mostrando os deals que JÁ receberam status (contatado, em negociação, concluído). Isso permite que o vendedor acompanhe sem poluir o Top 5.

```
📋 Deals em Acompanhamento (X deals)
[expander - colapsado por padrão]

| Conta | Produto | Score | Status | Atualizado em |
|-------|---------|-------|--------|---------------|
| Scotfind | GTX Plus Pro | 78.3 | 📞 Contatado | 22/12/2017 |
| Rangreen | MG Special | 70.2 | 🔄 Em negociação | 22/12/2017 |
```

---

## Resumo de todas as mudanças de fórmula (v3)

### Score de Probabilidade
```python
score_prob = (fator_setor_produto * 0.35) + (fator_historico_conta * 0.30) + (fator_sazonalidade * 0.20) + (fator_tempo * 0.15)
```

### Fatores (sem mudança na lógica, só nos pesos)
- Setor+Produto: normalização entre 0.52 e 0.73 → 0-100 (peso 0.35)
- Histórico Conta: normalização entre 0.531 e 0.750 → 0-100 (peso 0.30)
- Sazonalidade: baseada no mês da data de referência (peso 0.20)
- Tempo: faixas ajustadas para o dataset, data de referência (peso 0.15)

### Score de Valor (sem mudança)
```python
score_valor = (math.log(sales_price) / math.log(26768)) * 100
```

### Score Final (sem mudança)
```python
score_final = (score_prob * 0.70) + (score_valor * 0.30)
```

### Stage → indicador visual (NÃO entra no cálculo)
- 🆕 Novo (Prospecting)
- 🔄 Em andamento (Engaging)

---

## Layout atualizado (v4)

```
┌──────────────────────────────────────────────────────────────────┐
│  🎯 Lead Scorer — Pipeline Intelligence                          │
│  📅 Data de referência: 22/12/2017 · XXXX deals em aberto        │
├──────────┬───────────────────────────────────────────────────────┤
│ SIDEBAR  │                                                       │
│          │  KPIs Linha 1: [Deals] [Prior. Alta] [Valor Total]    │
│ Filtros: │  KPIs Linha 2: [Conv%] [Ciclo Médio] [Ticket Med]    │
│ Escrit.  │───────────────────────────────────────────────────────│
│ Manager  │  ℹ️ Como funciona o Score? (expander)                  │
│ Vendedor │───────────────────────────────────────────────────────│
│ Stage    │  🔥 TOP 5 PRIORIDADES (deals pendentes de ação)       │
│ Score    │  ┌──────────────────────────────────┬───────────────┐ │
│          │  │ #1 — RANGREEN        🆕 Novo     │ Status ▼      │ │
│          │  │ Score 78.2 | MG Spec · $55 · ... │ ⬜ Não contat.│ │
│          │  │ 📊 Pontuação detalhada:           │               │ │
│          │  │ Setor+Prod: 32.4/35 | Conta: ... │               │ │
│          │  ├──────────────────────────────────┼───────────────┤ │
│          │  │ #2 — SCOTFIND       🔄 Andamento │ Status ▼      │ │
│          │  └──────────────────────────────────┴───────────────┘ │
│          │───────────────────────────────────────────────────────│
│          │  📋 Deals em Acompanhamento (X deals) [expander]      │
│          │───────────────────────────────────────────────────────│
│          │  📋 Pipeline Completo — XX registros                  │
│          │  Tabela ordenada por Score Final                       │
└──────────┴───────────────────────────────────────────────────────┘
```

---

## Checklist para o Claude Code

1. [ ] Remover stage do cálculo do score
2. [ ] Redistribuir pesos: Setor+Prod 0.35, Conta 0.30, Sazon 0.20, Tempo 0.15
3. [ ] Adicionar badge visual de stage (🆕 Novo / 🔄 Em andamento)
4. [ ] Pontuação detalhada nos cards Top 5 (tabela com pontos por fator)
5. [ ] Top 5 dinâmico: excluir deals com status contatado/em_negociacao/concluido
6. [ ] Quando deal recebe status de ação, próximo da fila entra no Top 5
7. [ ] Mensagem quando todos os prioritários foram trabalhados
8. [ ] Seção "Deals em Acompanhamento" (expander) com deals que já receberam status
9. [ ] Manter todos os KPIs e funcionalidades do CONTEXT3
10. [ ] Guardar fator_setor_produto, fator_historico_conta, fator_sazonalidade, fator_tempo como colunas no dataframe para usar na explicação detalhada
