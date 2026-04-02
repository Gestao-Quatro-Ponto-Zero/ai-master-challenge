# CONTEXT3.md — Melhorias de Interface e Funcionalidades

## O que remover

### Remover: Gráfico de distribuição dos scores
Irrelevante para o vendedor. Ele não precisa saber como os scores se distribuem — precisa saber onde focar. Remover completamente.

### Remover: KPI "Score Médio"
Número abstrato que não ajuda o vendedor a tomar nenhuma decisão. Substituir por métricas acionáveis.

---

## O que adicionar/modificar

### 1. Novos KPIs (substituem os atuais)

A barra de KPIs deve mostrar 6 métricas em 2 linhas de 3 colunas:

**Linha 1 — Pipeline:**
- **Deals em Aberto**: total de deals filtrados
- **Prioridade Alta (>70)**: quantidade de deals com score acima de 70
- **Valor Potencial Total**: soma dos valores dos deals abertos filtrados

**Linha 2 — Performance do Vendedor** (só aparece quando um vendedor específico está selecionado no filtro, NÃO aparece quando "Todos" está selecionado):
- **Taxa de Conversão**: Won / (Won + Lost) do vendedor selecionado, em percentual. Calcular usando todos os deals históricos (Won e Lost) daquele vendedor.
- **Ciclo Médio de Fechamento**: média de dias entre engage_date e close_date dos deals Won daquele vendedor. Mostrar em dias.
- **Ticket Médio**: média de close_value dos deals Won daquele vendedor. Mostrar em $.

Quando "Todos" estiver selecionado nos filtros, a linha 2 mostra os números gerais (todos os vendedores agregados).

### 2. Nome da conta visível nos Top 5

PROBLEMA: Os cards de Top 5 Prioridades não mostram o nome da conta. O vendedor precisa saber QUEM ligar.

CORREÇÃO: Cada card do Top 5 deve mostrar:
```
#1 — NOME DA CONTA
Score 79.4 | MG Advanced · $3,393 · Engaging · 142 dias
💡 Probabilidade alta: Conta Cheers converte 70% historicamente (acima da média).
   Combinação entertainment + MG Advanced tem conversão forte (71%).
   Mês de fechamento trimestral (boost).
```

O nome da conta deve ser o elemento mais visível do card — usar st.subheader() ou fonte grande/negrito.

### 3. Explicação do score mais detalhada e didática

A explicação atual é curta demais. O vendedor precisa entender CADA fator que influenciou.

Novo formato da explicação para cada deal (tanto nos Top 5 quanto na tabela):

```
💡 Por que esse score?

📊 Histórico da conta: [Nome] tem [X%] de taxa de conversão — [acima/na/abaixo da] média.
🏷️ Produto + Setor: A combinação [setor] + [produto] converte [X%] historicamente — [forte/média/fraca].
📅 Momento do mercado: Estamos em mês de [fechamento trimestral/meio de trimestre/início de trimestre].
📍 Estágio: Deal em [Engaging/Prospecting] [há X dias / sem interação ainda].
💰 Valor potencial: $[valor] ([alto/médio/baixo] comparado ao portfólio).
```

Classificações:
- Taxa conta: ≥68% = "acima da média", 58-68% = "na média", <58% = "abaixo da média"
- Taxa combo: ≥68% = "forte", 57-68% = "média", <57% = "fraca"
- Valor: GTK 500 = "alto", GTX Pro/Plus Pro/MG Advanced = "médio", demais = "baixo"

### 4. Caixa "Como funciona o Score?" abaixo dos KPIs

Usar st.expander() com título "ℹ️ Como funciona o Score? (clique para entender)" logo abaixo dos KPIs.

Conteúdo da caixa (linguagem simples, sem termos técnicos):

```
## Como calculamos o Score de cada deal?

O score vai de 0 a 100 e combina duas coisas: **a chance de fechar** (70% do peso) e **o valor do deal** (30% do peso).

### O que influencia a chance de fechar:

🏷️ **Produto + Setor do cliente (30%)** — Algumas combinações de produto e setor do cliente historicamente fecham mais que outras. Por exemplo, vender GTX Pro para empresas de serviços fecha 72% das vezes, enquanto MG Advanced para o mesmo setor fecha só 52%.

🏢 **Histórico da conta (25%)** — Contas que já compraram antes e têm bom histórico de fechamento recebem pontuação maior. Uma conta que converte 75% dos deals vale mais que uma que converte 53%.

📍 **Estágio do deal (20%)** — Deals em Engaging (já houve contato real) pontuam mais que deals em Prospecting (ainda sem interação).

📅 **Momento do trimestre (15%)** — Historicamente, deals fecham muito mais nos meses de final de trimestre (março, junho, setembro, dezembro). Se estamos nesse período, todos os deals recebem um boost.

⏱️ **Tempo no pipeline (10%)** — Há quanto tempo o deal está em andamento. Deals muito novos ou muito antigos pontuam menos.

### O que significa cada cor:

🟢 **Verde (acima de 70)** — Prioridade alta. Esse deal tem boa chance de fechar e/ou bom valor. Foque aqui primeiro.

🟡 **Amarelo (40 a 70)** — Atenção. Mantenha o acompanhamento regular.

🔴 **Vermelho (abaixo de 40)** — Baixa prioridade. Considere deprioritizar ou reavaliar a abordagem.
```

### 5. Checklist de prioridades com status persistente

Adicionar um sistema de acompanhamento dos deals. O vendedor pode marcar o status de cada deal nos Top 5 (e opcionalmente na tabela completa).

**Status possíveis:**
- ⬜ Não contatado (padrão)
- 📞 Contatado — aguardando retorno
- 🔄 Em negociação — retorno positivo
- ❌ Sem retorno — reagendar
- ✅ Concluído — deal avançou

**Implementação:**

1. Criar arquivo `data/deal_status.csv` para persistir os status:
```csv
opportunity_id,status,updated_at,vendedor
HAXMC4IX,contatado,2017-12-22,Anna Snelling
UP409DSB,em_negociacao,2017-12-22,Maureen Marcano
```

2. Na seção Top 5, cada card tem um st.selectbox() com os status acima.

3. Quando o vendedor muda o status, salvar automaticamente no CSV.

4. Ao reabrir a ferramenta, carregar os status do CSV e exibir.

5. Deals marcados como "✅ Concluído" podem ser visualmente atenuados (cor mais clara) nos Top 5 — mas continuam aparecendo para referência.

**Código base:**
```python
import os
from datetime import datetime

STATUS_FILE = "data/deal_status.csv"
STATUS_OPTIONS = {
    "nao_contatado": "⬜ Não contatado",
    "contatado": "📞 Contatado — aguardando retorno",
    "em_negociacao": "🔄 Em negociação — retorno positivo",
    "sem_retorno": "❌ Sem retorno — reagendar",
    "concluido": "✅ Concluído — deal avançou"
}

def load_deal_status():
    if os.path.exists(STATUS_FILE):
        return pd.read_csv(STATUS_FILE)
    return pd.DataFrame(columns=["opportunity_id", "status", "updated_at", "vendedor"])

def save_deal_status(opportunity_id, status, vendedor):
    df = load_deal_status()
    # Atualizar ou inserir
    mask = df["opportunity_id"] == opportunity_id
    if mask.any():
        df.loc[mask, "status"] = status
        df.loc[mask, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        new_row = pd.DataFrame([{
            "opportunity_id": opportunity_id,
            "status": status,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "vendedor": vendedor
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(STATUS_FILE, index=False)
```

6. Na seção Top 5, para cada deal:
```python
for i, row in top5.iterrows():
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"#{rank} — {row['account']}")
            st.write(f"Score {row['score_final']:.1f} | {row['product']} · ${row['sales_price']} · {row['deal_stage']} · {row['dias_pipeline']} dias")
            st.caption(row['explicacao'])
        with col2:
            current_status = get_current_status(row['opportunity_id'])
            new_status = st.selectbox(
                "Status",
                options=list(STATUS_OPTIONS.keys()),
                format_func=lambda x: STATUS_OPTIONS[x],
                index=list(STATUS_OPTIONS.keys()).index(current_status),
                key=f"status_{row['opportunity_id']}"
            )
            if new_status != current_status:
                save_deal_status(row['opportunity_id'], new_status, row['sales_agent'])
```

### 6. Tabela principal — ajustes

A tabela principal (abaixo dos Top 5) deve manter:
- Score Final (com cor)
- Conta (VISÍVEL)
- Setor
- Produto
- Valor ($)
- Stage
- Vendedor
- Dias no Pipeline
- Por que esse score? (explicação curta — 1 linha resumida, não a versão completa dos Top 5)

---

## Layout final (v3)

```
┌──────────────────────────────────────────────────────────────┐
│  🎯 Lead Scorer — Pipeline Intelligence                      │
│  📅 Data de referência: 22/12/2017 · XXXX deals em aberto    │
├──────────┬───────────────────────────────────────────────────┤
│ SIDEBAR  │                                                   │
│          │  KPIs Linha 1: [Deals] [Prior. Alta] [Valor Total]│
│ Filtros: │  KPIs Linha 2: [Conv%] [Ciclo Médio] [Ticket Med] │
│ Escrit.  │  (linha 2 só quando vendedor selecionado)          │
│ Manager  │───────────────────────────────────────────────────│
│ Vendedor │  ℹ️ Como funciona o Score? (expander)              │
│ Stage    │───────────────────────────────────────────────────│
│ Score    │  🔥 SUAS TOP 5 PRIORIDADES                        │
│          │  ┌───────────────────────────────────┬──────────┐ │
│          │  │ #1 — NOME DA CONTA                │ Status ▼ │ │
│          │  │ Score 79.4 | MG Adv · $3,393 ·... │ ⬜ Não.. │ │
│          │  │ 💡 Explicação detalhada...         │          │ │
│          │  ├───────────────────────────────────┼──────────┤ │
│          │  │ #2 — CONTA Y                      │ Status ▼ │ │
│          │  │ ...                                │          │ │
│          │  └───────────────────────────────────┴──────────┘ │
│          │───────────────────────────────────────────────────│
│          │  📋 Pipeline Completo — XX registros              │
│          │  Tabela ordenada por Score Final                   │
└──────────┴───────────────────────────────────────────────────┘
```

---

## Checklist para o Claude Code

1. [ ] Remover gráfico de distribuição dos scores
2. [ ] Remover KPI "Score Médio"
3. [ ] Novos KPIs: Deals em Aberto, Prioridade Alta, Valor Total (linha 1)
4. [ ] Novos KPIs condicionais: Taxa Conversão, Ciclo Médio, Ticket Médio (linha 2, só com vendedor selecionado)
5. [ ] Nome da conta visível e destacado nos cards Top 5
6. [ ] Explicação do score detalhada e didática (com emojis, por fator)
7. [ ] Caixa expander "Como funciona o Score?" abaixo dos KPIs
8. [ ] Sistema de checklist com dropdown de status nos Top 5
9. [ ] Persistência de status em data/deal_status.csv
10. [ ] Tabela principal com explicação resumida (1 linha)
11. [ ] Calcular taxa de conversão, ciclo médio e ticket médio usando dados históricos (Won/Lost) por vendedor
