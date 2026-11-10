# 0003 — Diagnóstico com o DS1 sintético: cortar, testar, mostrar a incoerência e ainda assim estimar custo

- **Status:** Aceita (validada pelo Daniel em 2026-11-09, após ajustes dele)
- **Data:** 2026-11-09
- **Origem:** IA (achado de que o DS1 é sintético) · Daniel (como responder a cada pergunta)
- **Evidência:** `solution/analysis/00_data_profile.py`, `01_signal_tests.py`, `02_diagnostic_cuts.py` → `output/diagnostic_cuts.csv`

## Contexto
O DS1 foi gerado com variáveis independentes entre si (28 pares testados: 1 "significativo", o mesmo que o acaso produziria). Uma IA que responda ao brief "direto" entrega rankings que são ruído — ex.: Phone + High + Refund com CSAT 2,29 contra Email + High + Product inquiry com 3,57, quando o teste dá p=0,50.

## Decisão — uma resposta por pergunta (direcionamento do Daniel)

### 1. Onde o fluxo trava? → cortar primeiro, diagnosticar depois
Cortes por **canal, prioridade, tipo, assunto e produto**. Para cada grupo: volume, % sem 1ª resposta, % aguardando cliente, tempo 1ª resposta → resolução (só registros coerentes) e CSAT com IC 95%. Cada diferença entre grupos é testada (p-valor).

| Dimensão | Grupos | % sem 1ª resposta | p | Tempo mediano | p | CSAT | p |
|---|---|---|---|---|---|---|---|
| Canal | 4 | 33–35% | 0,77 | 6,0–6,5h | 0,79 | 2,95–3,08 | 0,28 |
| Prioridade | 4 | 33–34% | 0,23 | 5,9–7,1h | 0,09 | 2,96–3,05 | 0,63 |
| Tipo | 5 | 32–34% | 0,34 | 5,3–7,0h | 0,16 | 2,93–3,03 | 0,70 |
| Assunto | 16 | 30–38% | 0,16 | 5,2–8,5h | 0,80 | 2,80–3,18 | 0,81 |
| Produto | 42 | 26–40% | 0,66 | 3,5–9,7h | 0,08 | 2,54–3,22 | 0,67 |

**Leitura:** nenhum corte separa grupos (todos os p > 0,05). As faixas que parecem largas (produto: 3,5h a 9,7h) vêm de grupos pequenos. O gargalo que existe é **transversal**, não de um canal: 33% dos tickets sem 1ª resposta e 34% parados aguardando o cliente, em todos os cortes.

### 2. O que impacta a satisfação? → só entre os respondidos, com o viés documentado
- Análise feita **apenas nos 2.769 tickets fechados**, os únicos com CSAT.
- Nenhuma variável sozinha muda o CSAT. Todas juntas (70 variáveis, incluindo tempo e idade) explicam **2,1%** da variação; descontado o número de variáveis, **R² ajustado = −0,005**, ou seja, nada.
- **Tese do viés de sobrevivência** (registrada em `context/data-findings.md` e exibida no dashboard): o CSAT só existe para quem chegou ao fim. Os 67% sem resolução (sem resposta ou aguardando cliente) são justamente os candidatos mais prováveis à insatisfação, e não são medidos. Numa operação real, isso **superestima** a satisfação e esconde o efeito do tempo de espera. Recomendação: pesquisa também para tickets abandonados ou parados há mais de X dias.

### 3. Quanto estamos desperdiçando? → mostrar a incoerência e estimar o custo mesmo assim
**Mostrar que o dado não é condizente** (painel "Confiabilidade dos dados"): janela de 27h, 49% dos fechados resolvidos *antes* da 1ª resposta, resoluções em lorem ipsum, sem data de abertura.

**Indicadores de custo** — cada um rotulado pela origem:

| Indicador | Origem | Valor |
|---|---|---|
| Tickets sem 1ª resposta (backlog) | **Medido** | 2.819 (33,3%) |
| Tickets aguardando cliente (retrabalho de follow-up) | **Medido** | 2.881 (34,0%) |
| Tempo 1ª resposta → resolução | **Medido, só nos 50,7% coerentes** | média 7,6h · mediana 6,3h · p90 16h |
| Tempo médio na fila (abertura → 1ª resposta) | **Não mensurável** (não há data de abertura) → indicador de SLA, **fora do custo** (espera custa satisfação, não hora de atendente) | instrumentar |
| Tempo de manuseio humano por ticket | **Benchmark com fonte**, editável por tipo | 8,6 min (MetricNet/HDI) |
| Custo/hora do atendente | **Benchmark com fonte**, editável | R$ 21,30 (CAGED, CBO 4223-20, com encargos) |
| % automatizável e precisão | **Medido no DS2** (ADR-0009) | após a avaliação do classificador |

Desperdício recuperável = volume × mix (DS1) × tempo de manuseio (premissa) × custo/hora (premissa) × taxa de automação por nível (DS2). Todas as premissas ficam visíveis e ajustáveis no dashboard; o número nunca aparece sem a origem.

## Alternativas descartadas
- **Tratar os dados como reais e ranquear:** reproduz o baseline e cai no critério "zero evidência de verificação".
- **Ignorar o DS1:** perde a questão 1 (obrigatória).

## Consequências
- Responde às três perguntas com os números pedidos, testados, e separa o medido do estimado.
- Premissas com fonte definidas em [`docs/premissas-de-custo.md`](../premissas-de-custo.md) e `solution/analysis/cost_premises.json` (benchmarks com fonte, por escolha do Daniel).
