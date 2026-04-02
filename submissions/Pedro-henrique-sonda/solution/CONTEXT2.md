# CONTEXT2.md — Correções e Melhorias após Etapa 2

## Problemas identificados na versão atual

### Problema 1 — Scores empatados (CRÍTICO)
Muitos deals têm o mesmo score. Motivo: dos 4 fatores do scoring, 2 são idênticos para todos os deals neste momento:
- Sazonalidade: março 2026 = 95 para todos (peso 35%) — mas os dados são de 2016-2017, então devemos usar o mês da data de referência do dataset
- Tempo no pipeline: todos os Engaging têm 3000+ dias porque usamos datetime.now() em dados de 2016 (peso 15%)

Isso significa que **50% do peso do score não diferencia nada**. Só setor+produto (30%) e stage (20%) variam — gerando poucos scores únicos.

**Soluções:**
1. Adicionar um 5º fator — Histórico da Conta (21,9 pontos de variação)
2. Usar a data de referência do dataset (engage_date mais recente dos deals abertos = 2017-12-22) ao invés de datetime.now() para calcular dias no pipeline E para definir o mês da sazonalidade. Mês de referência: dezembro = mês de fechamento trimestral.
3. Ajustar faixas de tempo para a distribuição real dos dados

### Problema 2 — Top 5 prioridades não existe
O objetivo definido era: "O vendedor abre e em 10 segundos sabe quais 5 deals precisa atacar nos próximos 30 minutos." Hoje a ferramenta mostra uma tabela enorme sem destaque. O vendedor tem que interpretar sozinho.

**Solução: criar uma seção "🔥 Suas Top 5 Prioridades" no topo da página**, antes da tabela completa. Cards grandes e visíveis com os 5 deals de maior score, com explicação de por que estão ali.

### Problema 3 — Vendedor não entende o score
A tabela mostra apenas o número do score. O vendedor não sabe por que um deal tem 83 e outro tem 65.

**Solução: adicionar coluna "Por que esse score?" com explicação em texto natural** para cada deal. Exemplo: "Probabilidade alta: conta Rangreen converte 75% historicamente. Combinação services + GTX Pro tem boa conversão. Estamos em mês de fechamento trimestral."

---

## Nova fórmula de scoring (v2)

### Data de referência (IMPORTANTE)

Os dados são de 2016-2017. Toda a aplicação deve usar uma DATA DE REFERÊNCIA calculada automaticamente ao invés de datetime.now():

```python
# Data de referência = engage_date mais recente entre deals abertos
data_referencia = deals_abertos[deals_abertos['engage_date'].notna()]['engage_date'].max()
# No dataset atual, isso resulta em 2017-12-22
# Mês de referência para sazonalidade: 12 (dezembro = fechamento trimestral)
```

Isso afeta:
- Cálculo de dias no pipeline (usar data_referencia - engage_date)
- Fator de sazonalidade (usar data_referencia.month ao invés de datetime.now().month)

### Redistribuição dos pesos

A fórmula original tinha pesos inadequados porque 2 fatores não diferenciam na prática. Nova distribuição:

```
Score Probabilidade = (Setor_Produto × 0.30) + (Historico_Conta × 0.25) + (Stage × 0.20) + (Sazonalidade × 0.15) + (Tempo × 0.10)
```

**Mudanças:**
- Sazonalidade: de 0.35 para 0.15 (ainda relevante conceitualmente, mas como é igual para todos agora, reduzir peso)
- Tempo: de 0.15 para 0.10 (mesmo motivo — não diferencia no dataset atual)
- NOVO — Histórico da Conta: peso 0.25 (21,9 pontos de variação, 85 contas com dados)

### Fator NOVO — Histórico da Conta (peso 0.25)

Calcula a taxa de conversão histórica (Won / (Won+Lost)) para cada conta nos dados.

```python
# Para cada conta:
taxa_conta = won / (won + lost)

# Normalização (mesma lógica do setor+produto):
# Min histórico: 53.1% = 0.531
# Max histórico: 75.0% = 0.750
historico_conta = ((taxa_conta - 0.531) / (0.750 - 0.531)) * 100
historico_conta = max(0, min(100, historico_conta))  # Clamp 0-100
```

Se a conta não tiver histórico suficiente (menos de 5 deals fechados), usar taxa média geral (0.632) como fallback.

### Todos os fatores (v2 completa)

**Fator 1 — Combinação Setor + Produto (peso 0.30)** — sem mudança

**Fator 2 — Histórico da Conta (peso 0.25)** — NOVO
```python
taxa_conta = won / (won + lost)  # por conta
historico_conta = ((taxa_conta - 0.531) / (0.750 - 0.531)) * 100
historico_conta = max(0, min(100, historico_conta))
# Fallback se <5 deals: usar 0.632
```

**Fator 3 — Stage (peso 0.20)** — sem mudança
- Engaging: 75
- Prospecting: 40

**Fator 4 — Sazonalidade (peso 0.15)** — peso reduzido
Usar o mês da DATA DE REFERÊNCIA, não datetime.now(). 
- Mês de fechamento trimestral (3,6,9,12): 95
- Segundo mês (2,5,8,11): 55
- Primeiro mês (1,4,7,10): 35

**Fator 5 — Tempo no pipeline (peso 0.10)** — CORRIGIDO

IMPORTANTE: Os dados são de 2016-2017. Usar datetime.now() resulta em 3.000+ dias para todos os deals, tornando este fator inútil.

**Solução:** Calcular a data de referência como a engage_date mais recente entre os deals abertos. No dataset, essa data é 2017-12-22. Todos os cálculos de "dias no pipeline" devem usar essa data como "hoje".

```python
# Calcular data de referencia
data_referencia = deals_abertos[deals_abertos['engage_date'].notna()]['engage_date'].max()

# Dias no pipeline = data_referencia - engage_date
dias = (data_referencia - engage_date).days
```

Com essa correção, a distribuição fica:
- 0-30 dias: 27 deals (1,7%)
- 30-60 dias: 45 deals (2,8%)
- 60-90 dias: 61 deals (3,8%)
- 90-180 dias: 759 deals (47,8%)
- 180-365 dias: 657 deals (41,3%)
- 365+ dias: 40 deals (2,5%)

Como a maioria dos deals está entre 90 e 365 dias, as faixas precisam ser ajustadas para este dataset:

| Faixa | Pontos | Lógica |
|-------|--------|--------|
| 0-60 dias | 45 | Deal recente — ainda cru |
| 60-120 dias | 55 | Amadurecendo |
| 120-240 dias | 55 | Pipeline ativo |
| 240-365 dias | 50 | Longo — pode estar esfriando |
| 365+ dias | 40 | Muito longo — provável deal travado |
| Sem engage_date (Prospecting) | 50 | Neutro |

### Score de Valor — sem mudança
```python
score_valor = (math.log(sales_price) / math.log(26768)) * 100
```

### Score Final — sem mudança na estrutura
```python
score_final = (score_probabilidade * 0.70) + (score_valor * 0.30)
```

---

## Nova interface (v2)

### Layout atualizado

```
┌──────────────────────────────────────────────────────────┐
│  🎯 Lead Scorer — Pipeline Intelligence                  │
│  Subtítulo: Priorize seus deals com dados                │
├──────────┬───────────────────────────────────────────────┤
│ SIDEBAR  │                                               │
│          │  KPIs (4 colunas)                              │
│ Filtros: │  [Deals] [Score Médio] [Alta Prior.] [Valor]  │
│ Escrit.  │───────────────────────────────────────────────│
│ Manager  │  🔥 SUAS TOP 5 PRIORIDADES                    │
│ Vendedor │  ┌─────────────────────────────────────────┐  │
│ Stage    │  │ #1 Conta X — Score 84                   │  │
│ Score    │  │ GTX Pro · $4,821 · Engaging · 45 dias   │  │
│          │  │ "Conta com 75% de conversão histórica.   │  │
│          │  │  Combinação forte. Mês de fechamento."   │  │
│          │  ├─────────────────────────────────────────┤  │
│          │  │ #2 Conta Y — Score 81                   │  │
│          │  │ ...                                      │  │
│          │  └─────────────────────────────────────────┘  │
│          │───────────────────────────────────────────────│
│          │  📋 Pipeline Completo — XX registros          │
│          │  Tabela com: Score | Conta | Setor | Produto  │
│          │  | Valor | Stage | Dias | Por que esse score  │
│          │───────────────────────────────────────────────│
│          │  📊 Distribuição dos Scores (gráfico)         │
└──────────┴───────────────────────────────────────────────┘
```

### Seção "Top 5 Prioridades"
- Mostra os 5 deals com maior Score Final (após filtros aplicados)
- Cada card mostra: posição (#1 a #5), conta, score, produto, valor, stage, dias no pipeline
- Inclui explicação do score em texto natural
- Usar st.container() ou st.expander() com visual destacado
- Se o vendedor está selecionado no filtro, mostra os top 5 DELE

### Coluna "Por que esse score?"
Para cada deal, gerar explicação contextual. Modelo:

```python
def gerar_explicacao(row):
    partes = []
    
    # Classificar probabilidade
    if row['score_probabilidade'] > 70:
        nivel = "alta"
    elif row['score_probabilidade'] > 40:
        nivel = "média"  
    else:
        nivel = "baixa"
    
    partes.append(f"Probabilidade {nivel}")
    
    # Conta
    if row['taxa_conta'] >= 0.68:
        partes.append(f"Conta {row['account']} converte {row['taxa_conta']*100:.0f}% historicamente (acima da média)")
    elif row['taxa_conta'] <= 0.58:
        partes.append(f"Conta {row['account']} converte {row['taxa_conta']*100:.0f}% historicamente (abaixo da média)")
    
    # Setor+Produto
    if row['taxa_combo'] >= 0.68:
        partes.append(f"Combinação {row['sector']}+{row['product']} tem conversão forte ({row['taxa_combo']*100:.0f}%)")
    elif row['taxa_combo'] <= 0.57:
        partes.append(f"Combinação {row['sector']}+{row['product']} tem conversão fraca ({row['taxa_combo']*100:.0f}%)")
    
    # Sazonalidade
    mes = datetime.now().month
    if mes in [3,6,9,12]:
        partes.append("Mês de fechamento trimestral (boost)")
    
    # Stage
    if row['deal_stage'] == 'Prospecting':
        partes.append("Ainda em Prospecting (sem interação)")
    
    return ". ".join(partes) + "."
```

### Cores do Score na tabela
Manter:
- 🟢 Verde: score > 70
- 🟡 Amarelo: score 40-70
- 🔴 Vermelho: score < 40

---

## Checklist para o Claude Code

1. [ ] Adicionar Fator 5 (Histórico da Conta) ao scoring
2. [ ] Redistribuir pesos conforme nova fórmula
3. [ ] Corrigir merge de produtos (GTXPro → GTX Pro)
4. [ ] Tratar contas sem match (setor = "unknown")
5. [ ] Criar seção "Top 5 Prioridades" acima da tabela
6. [ ] Adicionar coluna "Por que esse score?" com explicação em texto
7. [ ] Manter sidebar com filtros encadeados
8. [ ] Manter KPIs no topo
9. [ ] Adicionar gráfico de distribuição dos scores
10. [ ] Ordenar tabela por Score Final decrescente
