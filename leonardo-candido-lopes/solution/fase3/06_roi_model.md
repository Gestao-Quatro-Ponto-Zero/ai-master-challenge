# 06 — Modelo de ROI paramétrico (3 cenários)

**Desafio 002 — Redesign de Suporte · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
Cálculo reproduzível: `fase3/roi_calc.py` → `fase3/roi_results.json`. Todos os valores abaixo saem das fórmulas da seção 2; nenhum foi digitado à mão.

> **Natureza deste documento: [PROJEÇÃO].** Nenhum dos dois datasets traz custo, headcount, volume histórico mensal ou tempo de atendimento. Por isso, **todas as premissas são editáveis** e vêm de (a) benchmarks públicos com fonte, (b) a distribuição real de categorias do Dataset 2 ou (c) estimativa do autor, sempre rotulada. Moeda: **R$**, porque a operação de referência é brasileira. Benchmarks em US$ entram só como referência de ordem de grandeza.

---

## Leitura rápida para o COO

- **Capacidade recuperada (cenário base):** 150 h/mês, ≈ 1,03 FTE. O valor econômico potencial é R$ 6.098/mês.
- **Economia financeira realizada (cenário base):** R$ 3.049/mês contra um custo recorrente de R$ 5.000/mês. Resultado mensal: **−R$ 1.951**. **No cenário base, o projeto não se paga só com economia de caixa.**
- **Ponto de equilíbrio (base):** ~**8.200 chamados/mês** com 50% da capacidade convertida em economia. Se 75% for convertida, cai para 5.467; se 100%, para 4.100.
- **Otimista:** R$ 16.837/mês líquido, payback de 3,0 meses. **Conservador:** −R$ 6.788/mês, não se paga.
- **Leitura honesta:** o caso financeiro **depende de escala** (volume) e de **o que a empresa faz com as horas liberadas**. Com volumes menores, a justificativa é **qualidade e controle**: triagem correta, SLA mensurável e auditoria. O caixa vem depois. Isso precisa ser dito ao COO antes do investimento, não depois.

---

## 1. Premissas do modelo

| # | Variável | Conservador | Base | Otimista | Fonte / justificativa | Tipo | Editável? |
|---|---|---:|---:|---:|---|---|---|
| V | Volume mensal de chamados | 3.000 | 5.000 | 8.000 | Não existe nos datasets (o D2 tem 47.837 tickets sem data). Faixa hipotética para um service desk de médio porte. | Hipótese | **Sim — prioridade nº 1** |
| pe | % elegível à automação | 11,0% | 18,4% | 25,9% | **Dados reais do D2:** conservador = Purchase (5,15%) + Storage (5,81%); base = + metade de Access (14,89% × 0,5); otimista = Purchase + Storage + Access inteiro. Ver justificativa no `02_redesign_operacional.md`. | Derivada dos dados + hipótese | Sim |
| ts | Taxa de sucesso da automação (resolve sem humano) | 36% | 50% | 65% | **Gartner (ago/2024, n=5.728):** só 14% dos problemas são totalmente resolvidos em self-service, **36% nos casos "muito simples"**. O conservador usa os 36% porque as classes elegíveis são as mais padronizadas. Base e otimista são hipóteses do autor. | Benchmark + hipótese | Sim |
| aht | Tempo médio de atendimento humano poupado por chamado (min) | 8 | 12 | 18 | **HDI / MetricNet:** tempo de contato no service desk "pouco abaixo de 10 min"; incidentes de 12 a 22 min; reset de senha de 1 a 3 min; requisições de serviço de 35 a 96 min. | Benchmark | Sim |
| tri | Tempo de triagem/roteamento manual poupado por chamado (min) — aplica-se a **todo** o volume | 0,5 | 1,0 | 1,5 | Estimativa do autor. **Sem benchmark público encontrado.** Medir na baseline (KPI 13 do `05_kpis.md`). | Hipótese | **Sim — medir** |
| tf | Fricção por tentativa automática que falha (min de agente) | 2,0 | 1,5 | 1,0 | Estimativa do autor: o agente lê o histórico da tentativa antes de assumir. | Hipótese | Sim |
| r | % de retrabalho por erro de automação (ticket "resolvido" que reabre) | 15% | 10% | 5% | Estimativa do autor. Sem benchmark confiável; medir via taxa de reabertura (KPI 11). | Hipótese | Sim |
| k | Esforço extra no retrabalho (fração do aht, somado à perda da economia) | 0,5 | 0,5 | 0,5 | Estimativa do autor: o cliente reabre irritado e o atendimento demora mais. | Hipótese | Sim |
| ch | Custo-hora carregado do agente (R$) | 28,02 | 40,64 | 48,34 | **salario.com.br (CBO 2124-20, Analista de Suporte Técnico, 2026):** mediana R$ 3.000, média R$ 4.109, média no Sudeste R$ 4.399, jornada de 42h/semana (≈ 182h/mês). Fator de encargos CLT de 1,7 / 1,8 / 2,0 (estimativa usual de mercado, **validar com o RH**). Fórmula: salário × fator ÷ 182. Referência internacional: BLS (mai/2024), mediana de US$ 29,01/h para *computer user support specialists*. | Benchmark + hipótese (encargos) | Sim |
| real | Taxa de realização financeira (% das horas liberadas que viram economia de caixa) | 25% | 50% | 75% | **Decisão de gestão, não de dados.** Economia só acontece se as horas evitarem contratação, hora extra, terceirização ou backlog pago. Ver seção 4. | Hipótese de gestão | **Sim — decisão do COO** |
| tool | Custo mensal de ferramentas de IA (R$) | 2.000 | 1.500 | 1.000 | Estimativa do autor (licença/API de LLM ou NLP + hospedagem). **Substituir por cotação.** | Hipótese | Sim |
| mnt | Custo de manutenção mensal (R$) | 5.000 | 3.500 | 2.500 | Estimativa do autor: fração de analista para curadoria da base de conhecimento, revisão de amostras e retreino. | Hipótese | Sim |
| impl | Custo de implementação, one-time (R$) | 120.000 | 80.000 | 50.000 | Estimativa do autor: integração com o sistema de tickets, base de conhecimento, piloto e treinamento. **Substituir por orçamento.** | Hipótese | Sim |
| FTE | Horas produtivas por FTE/mês | 146 | 146 | 146 | 182h × 80% de utilização. HDI/MetricNet citam utilização sustentável perto de 70–80%. | Benchmark + convenção | Sim |

**Referências de ordem de grandeza (não entram na conta):** MetricNet, custo por ticket na América do Norte: média de US$ 15,56 em 2016 (faixa de US$ 2,93 a 46,69); 2021: voz US$ 17,19, e-mail US$ 16,13, chat US$ 15,72. MetricNet *shift-left*: N1 ≈ US$ 22/ticket vs self-service ≈ US$ 2/ticket.

**Fontes:**
- Gartner — https://www.gartner.com/en/newsroom/press-releases/2024-08-19-gartner-survey-finds-only-14-percent-of-customer-service-issues-are-fully-resolved-in-self-service
- HDI — https://www.thinkhdi.com/~/media/HDICorp/Files/Library-Archive/Insider%20Articles/contact-handle-time.pdf
- MetricNet — https://www.metricnet.com/resources/service-desk-cost-per-ticket-motm · https://www.metricnet.com/resources/metrics-unleashed-shift-left
- BLS — https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm
- salario.com.br — https://www.salario.com.br/profissao/analista-de-suporte-tecnico-cbo-212420/

---

## 2. Fórmulas (explícitas)

```
E   = V × pe                                   chamados elegíveis à automação/mês
S   = E × ts                                   chamados resolvidos automaticamente/mês
F   = E − S                                    tentativas que falham e vão para humano
H_auto = [ S × (1 − r) × aht  −  S × r × k × aht ] / 60     horas poupadas pelo autoatendimento (líquidas de retrabalho)
H_tri  = V × tri / 60                          horas poupadas pela triagem automática (todo o volume)
H_fric = F × tf / 60                           horas perdidas com fricção das falhas
H   = H_auto + H_tri − H_fric                  CAPACIDADE RECUPERADA (h/mês)
FTE = H / 146                                  equivalente em pessoas
VP  = H × ch                                   VALOR ECONÔMICO POTENCIAL da capacidade (R$/mês)
ER  = VP × real                                ECONOMIA FINANCEIRA REALIZADA (R$/mês)
C   = tool + mnt                               custo recorrente mensal
L   = ER − C                                   resultado líquido mensal
ROI mensal           = L / C
ROI potencial mensal = (VP − C) / C            (se 100% da capacidade virasse caixa — teto teórico)
ROI ano 1            = (12 × L − impl) / (impl + 12 × C)
Payback (meses)      = impl / L                (só se L > 0)
```

---

## 3. Resultados por cenário

| Indicador | Conservador | Base | Otimista |
|---|---:|---:|---:|
| Chamados elegíveis/mês (E) | 329 | 920 | 2.068 |
| Chamados automatizados com sucesso/mês (S) | 118 | 460 | 1.344 |
| Tentativas que falham → humano (F) | 210 | 460 | 724 |
| Horas poupadas — autoatendimento (H_auto) | 12,2 | 78,2 | 373,0 |
| Horas poupadas — triagem (H_tri) | 25,0 | 83,3 | 200,0 |
| Horas perdidas — fricção (H_fric) | 7,0 | 11,5 | 12,1 |
| **Capacidade recuperada (h/mês)** | **30,2** | **150,1** | **561,0** |
| Equivalente em FTE | 0,21 | 1,03 | 3,84 |
| **Valor econômico potencial (R$/mês)** | **R$ 847** | **R$ 6.098** | **R$ 27.116** |
| **Economia financeira realizada (R$/mês)** | **R$ 212** | **R$ 3.049** | **R$ 20.337** |
| Custo mensal total da solução | R$ 7.000 | R$ 5.000 | R$ 3.500 |
| Resultado líquido mensal (ER − C) | −R$ 6.788 | −R$ 1.951 | R$ 16.837 |
| ROI mensal (sobre economia realizada) | -97% | -39% | 481% |
| ROI potencial mensal (teto teórico) | -88% | 22% | 675% |
| ROI ano 1 (inclui implementação) | -99% | -74% | 165% |
| Payback | —  (não se paga) | —  (não se paga) | 3,0 meses |

**Leitura:**
- **[PROJEÇÃO] Conservador:** a automação é marginal (30,2 h/mês) e não cobre o custo. Mostra o risco de implantar com volume baixo e escopo estreito.
- **[PROJEÇÃO] Base:** libera ≈ 1,03 FTE. Se 100% virasse caixa, o ROI mensal seria 22%. Com 50% de realização, o resultado mensal é negativo (−R$ 1.951). **A decisão no cenário base é estratégica (qualidade, SLA, escala), não de corte de custo.**
- **[PROJEÇÃO] Otimista:** com escala (8.000/mês), escopo maior e tempo de atendimento maior, o retorno fica claro (payback ≈ 3,0 meses).
- Em todos os cenários, **a triagem (H_tri) responde por parte relevante das horas** (base: 83,3 de 150,1 h). Como essa é a premissa sem benchmark, **medir o tempo de triagem real é o primeiro passo do piloto**.

---

## 4. Capacidade recuperada ≠ economia realizada

| Conceito | O que é | Quando vira dinheiro |
|---|---|---|
| **Capacidade recuperada (H)** | Horas de agente que deixam de ser gastas em triagem manual e em tickets resolvidos automaticamente | Sempre existe se a automação funciona, mas é **tempo**, não caixa |
| **Valor econômico potencial (VP)** | H × custo-hora: quanto essas horas "valem" | É um **teto teórico**. Útil para comparar alternativas, nunca para prometer economia |
| **Economia realizada (ER)** | A parte do VP que efetivamente reduz desembolso | Só quando a empresa **(a)** deixa de contratar para absorver crescimento, **(b)** corta hora extra/terceiros, **(c)** reduz multa de SLA, ou **(d)** realoca por decisão formal. **O modelo não assume demissões** |

Por que separar: somar VP como "economia" é o erro mais comum em business cases de IA. Ele infla o ROI e destrói a credibilidade quando o caixa não aparece. Horas liberadas que viram ociosidade valem zero. Horas reinvestidas em N2, backlog (67,3% dos tickets do D1 não estão fechados, mesmo sendo sintético) ou base de conhecimento geram **valor de qualidade**, que deve ser medido por KPI (FCR, CSAT, SLA) e não somado ao ROI financeiro.

> *Contexto profissional externo (não é evidência dos datasets):* no redesign do "Link de Análise Especial", que o Leonardo conduziu e que passou de 2–5 dias para tempo real, o ganho principal veio de consolidar processos e eliminar risco de desatualização e perda financeira. Não veio de corte de pessoas. Por isso o modelo trata a taxa de realização como decisão explícita.

---

## 5. Sensibilidade (uma variável por vez)

Cada linha troca **só** aquela variável pelo valor conservador e depois pelo otimista, mantendo todas as outras no cenário base (resultado base = −R$ 1.951/mês).

| # | Variável | Resultado mensal com valor conservador | Resultado mensal com valor otimista | Amplitude |
|---:|---|---:|---:|---:|
| 1 | Volume mensal | −R$ 3.171 | −R$ 122 | R$ 3.049 |
| 2 | Taxa de realização financeira | −R$ 3.475 | −R$ 426 | R$ 3.049 |
| 3 | Custo manutenção mensal | −R$ 3.451 | −R$ 951 | R$ 2.500 |
| 4 | Tempo de triagem manual poupado | −R$ 2.798 | −R$ 1.104 | R$ 1.693 |
| 5 | Custo-hora do agente | −R$ 2.898 | −R$ 1.373 | R$ 1.525 |
| 6 | Tempo médio por chamado | −R$ 2.481 | −R$ 1.156 | R$ 1.325 |
| 7 | % elegível à automação | −R$ 2.499 | −R$ 1.403 | R$ 1.097 |
| 8 | Taxa de sucesso da automação | −R$ 2.461 | −R$ 1.404 | R$ 1.057 |
| 9 | Custo mensal ferramentas IA | −R$ 2.451 | −R$ 1.451 | R$ 1.000 |
| 10 | % retrabalho por erro | −R$ 2.091 | −R$ 1.811 | R$ 280 |
| 11 | Fricção por tentativa falha | −R$ 2.029 | −R$ 1.873 | R$ 156 |

**Leitura:**
- As 3 variáveis que mais mexem no resultado são **Volume mensal**, **Taxa de realização financeira** e **Custo manutenção mensal**. Duas delas são decisões de gestão (o que fazer com as horas, quanto investir em manutenção), não de tecnologia.
- Nenhuma variável isolada vira o cenário base para positivo. É preciso combinar escala com realização. **Ponto de equilíbrio (base): ≈ 8.200 chamados/mês.**
- A % de retrabalho e a fricção pesam pouco no caixa. Pesam muito na **experiência do cliente**, e por isso são controladas por KPI e risco (`07_riscos.md`), não pelo ROI.

---

## 6. O que falta para tornar o modelo preciso

1. **Volume mensal real** por categoria e canal, com sazonalidade (12 meses de histórico).
2. **Tempo médio de atendimento real por categoria** (hoje vem de benchmark), principalmente Purchase, Storage e Access.
3. **Tempo real de triagem e roteamento**, incluindo re-roteamentos (transferências entre filas).
4. **Custo-hora carregado real** (salário + encargos + benefícios + infraestrutura) por nível (N1/N2).
5. **Cotação real** de ferramenta (licença/API) e **orçamento de implementação**.
6. **Taxa de sucesso medida em piloto** (substitui as premissas de 36/50/65%).
7. **Decisão formal do COO sobre a taxa de realização**: contratações evitadas, terceiros, horas extras.
8. **Custos evitados não modelados:** multas de SLA, churn ligado a CSAT, custo de ticket mal roteado. Ficaram de fora por falta de dados e podem melhorar o caso.
9. **Fila Financeiro/Comercial (B2C)** não entra neste ROI. Ela precisa de um modelo próprio, com custo de chargeback e reembolso.
