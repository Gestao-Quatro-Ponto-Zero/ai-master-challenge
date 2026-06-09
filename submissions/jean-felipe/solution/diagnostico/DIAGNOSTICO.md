# Diagnóstico operacional — Dataset 1

Challenge 002 (Redesign de Suporte) · Jean Felipe

---

## Executive summary

A operação de suporte no recorte analisado tem **8.469 tickets únicos**, dos quais **67% permanecem sem resolução** (33% Open, 34% Pending). O tempo de ciclo médio entre primeira resposta e resolução é de **~7,7 horas** (mediana 6,7h) nos tickets fechados. **Refund request**, **Cancellation request** e canal **Social media** concentram os piores tempos. A satisfação média é **2,99/5** e **não correlaciona com o tempo de ciclo** — o que pesa mais é o tipo de pedido e o canal. O desperdício estimado no recorte é de **~59.600 horas** de trabalho equivalente.

---

## Como reproduzir

### Pré-requisitos

```bash
cd submissions/jean-felipe/solution/diagnostico
pip install -r requirements.txt
```

Dataset local (não versionado):

```
data/dataset1-support-tickets/customer_support_tickets.csv
```

### Executar

```bash
python analise_dataset1.py
```

Saídas em `output/`:

- `diagnostico_dataset1.txt` — relatório completo
- `gargalos_por_dimensao.png`
- `satisfacao_por_canal.png`

---

## 1. Parse do CSV — por que ~29k linhas viram ~8,5k tickets?

O arquivo `customer_support_tickets.csv` tem **~29.800 linhas físicas**, mas apenas **8.469 tickets únicos**. Isso **não é erro de parse** — é efeito de **campos multilinha**.

| Métrica | Valor |
|---------|-------|
| Linhas físicas no arquivo | 29.808 |
| Registros parseados | 8.469 |
| `Ticket ID` únicos | 8.469 |
| `Ticket Description` com `\n` | 6.150 (72,6%) |

Colunas como `Ticket Description` e `Resolution` contêm texto com quebras de linha **entre aspas duplas**, conforme RFC 4180. Cada quebra de linha dentro do campo conta como uma linha no editor, mas o parser CSV trata tudo como **um único registro**.

### Como o script faz o parse

```python
pd.read_csv(
    path,
    encoding="utf-8",
    quoting=csv.QUOTE_MINIMAL,
    engine="python",
)
```

Validação pós-parse: `len(df) == df["Ticket ID"].nunique()`. Se houver IDs duplicados, o script falha com erro explícito — sinal de parse quebrado (ex.: abrir o CSV no Excel e reexportar sem quoting).

> **Atenção:** O brief do challenge menciona ~30k registros; este arquivo do Kaggle tem **8.469 tickets** (IDs 1–8469). A contagem de linhas do arquivo (~29k) confunde com volume de tickets se o CSV não for parseado corretamente.

---

## 2. Timestamps vs duração — cálculo do tempo de ciclo

As colunas `First Response Time` (FRT) e `Time to Resolution` (TTR) **não são durações em horas**. São **timestamps** no formato `YYYY-MM-DD HH:MM:SS` — instantes em que eventos ocorreram (ou seriam registrados).

| Status | FRT | TTR | Interpretação |
|--------|-----|-----|---------------|
| **Open** | vazio | vazio | Ticket na fila, sem primeira resposta |
| **Pending Customer Response** | preenchido | vazio | Agente respondeu; aguardando cliente |
| **Closed** | preenchido | preenchido | Ciclo completo |

### Fórmula

Para tickets **Closed** com ambos os timestamps:

```
cycle_hours_signed = (TTR - FRT) em horas
cycle_hours        = |cycle_hours_signed|
```

### Por que usar valor absoluto?

Em **49,3%** dos tickets fechados (1.365 de 2.769), `TTR < FRT` — a resolução aparece **antes** da primeira resposta no dado. Isso é inconsistente com a lógica operacional real e indica **ruído nos dados sintéticos** (ordem dos timestamps trocada), não um ciclo negativo.

Por isso usamos **sempre o valor absoluto** da diferença: mede o intervalo entre os dois eventos independentemente da ordem registrada.

### Limitação

Sem timestamp de **abertura do ticket**, `cycle_hours` mede o intervalo entre primeira resposta e resolução — **não** o tempo total desde a abertura. É o melhor proxy disponível neste dataset.

---

## 3. Onde o fluxo trava

### Volume sem resolução

| Status | Tickets | % |
|--------|---------|---|
| Open | 2.819 | 33,3% |
| Pending Customer Response | 2.881 | 34,0% |
| Closed | 2.769 | 32,7% |

**5.700 tickets (67,3%)** ainda estão em Open ou Pending.

### Tempo de ciclo por dimensão (Closed)

| Dimensão | Pior | Média (h) |
|----------|------|-----------|
| **Canal** | Social media | 7,93 |
| **Tipo** | Cancellation request | 8,07 |
| **Prioridade** | High | 8,20 |

### Piores combinações (média ≥ 20 tickets)

1. Email + Technical issue + Low → **10,05 h**
2. Social media + Refund request + High → **9,94 h**
3. Social media + Refund request + Medium → **9,58 h**

### Stall operacional (além do tempo)

Combinações com maior % de tickets não resolvidos:

- Phone + Cancellation + Low → **80,6%** sem resolução
- Social media + Cancellation + High → **79,8%**
- Email + Product inquiry + Medium → **79,2%**

---

## 4. O que impacta satisfação

Base: **2.769 tickets Closed** com nota (escala 1–5).

| Variável | Pior | Melhor | Observação |
|----------|------|--------|------------|
| Canal | Phone (2,95) | Chat (3,08) | Diferença pequena (~0,13) |
| Tipo | Refund request (2,93) | Cancellation (3,03) | Refund puxa nota para baixo |
| Prioridade | Critical (2,96) | Low (3,05) | Critical não melhora com urgência |

**Correlação tempo de ciclo × satisfação: r = -0,001** (praticamente zero).

Conclusão: melhorar tempo de resolução sozinho **não move satisfação** neste dataset. Foco deve ir para **qualidade da resolução por tipo de pedido** (especialmente reembolsos) e **experiência por canal** (Phone/Social media).

---

## 5. Quanto estamos desperdiçando (horas)

### Metodologia

| Componente | Cálculo | Horas |
|------------|---------|-------|
| **A) Closed** | Soma real de `cycle_hours` | 21.439 h |
| **B) Pending** | 2.881 × mediana (6,7h) | 19.303 h |
| **C) Open** | 2.819 × mediana (6,7h) | 18.887 h |
| **Total estimado** | A + B + C | **59.629 h** |

Equivalente: **~1.491 semanas-pessoa** (40h/semana).

Custo ilustrativo a US$ 35/h agente: **~US$ 2,1M** no recorte.

### Recuperação conservadora

Tickets Closed acima do P75 de tempo de ciclo reduzidos ao P25 → **8.838 h recuperáveis** (41% do tempo já gasto em closed).

### Maior desperdício por dimensão (não resolvidos)

| Dimensão | Top | Horas estimadas |
|----------|-----|-----------------|
| Canal | Phone | 9.655 h |
| Tipo | Cancellation request | 7.899 h |
| Prioridade | Medium | 10.037 h |

---

## 6. Recomendações (input para automação)

1. **Triagem prioritária** de Refund/Cancellation em Social media e Email — maior tempo e maior volume não resolvido.
2. **SLA diferenciado** por combinação canal × tipo, não só por prioridade Critical (que não é a mais lenta).
3. **Automação de primeira resposta** nos 2.819 Open — maior alavanca de volume (33% da fila sem FRT).
4. **Não otimizar só por velocidade** — satisfação exige qualidade de resposta em Refund request.
5. Próxima etapa: cruzar com Dataset 2 (48k textos classificados) para propor roteamento e classificação automática.

---

## Arquivos desta entrega

| Arquivo | Descrição |
|---------|-----------|
| `analise_dataset1.py` | Script de análise reproduzível |
| `DIAGNOSTICO.md` | Este documento |
| `requirements.txt` | Dependências Python |
| `output/diagnostico_dataset1.txt` | Relatório gerado pelo script |

---

_Gerado em 2026-06-09. Reexecute `analise_dataset1.py` para atualizar números e gráficos._
