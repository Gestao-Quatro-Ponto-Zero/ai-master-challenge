# Submissão — Daniel Spinelli — Challenge 001

## Sobre mim

* **Nome:** Daniel Spinelli
* **LinkedIn:** https://www.linkedin.com/in/daniel-spinelli-90420b270
* **Challenge escolhido:** 001 — Diagnóstico de Churn

---

# Executive Summary

A RavenStack apresentou deterioração consistente da retenção ao longo de 2024, com a taxa mensal de churn aumentando de 8,3% em janeiro para 19,2% em dezembro.

A investigação cruzou dados de contas, assinaturas, uso da plataforma, tickets de suporte e eventos de churn para identificar a causa raiz do problema.

Os resultados mostraram que as explicações mais intuitivas não são sustentadas pelos dados. Clientes churnados utilizam a plataforma em níveis semelhantes aos clientes retidos, apresentam indicadores de suporte comparáveis e mantêm níveis equivalentes de satisfação.

Por outro lado, observou-se crescimento contínuo dos feedbacks relacionados a funcionalidades insuficientes, concorrência e percepção de custo elevado. Além disso, o churn concentra-se de forma desproporcional em segmentos específicos (DevTools), canais específicos (Event) e mercados específicos (Alemanha e Estados Unidos).

A análise sugere que o principal problema da RavenStack não está na adoção do produto nem na operação de suporte, mas na aderência da proposta de valor para determinados perfis de cliente.

Como resultado, foi desenvolvido um protótipo funcional de priorização de risco para apoiar ações de retenção e Customer Success.

---

# Solução

## Abordagem

O objetivo da análise foi responder à pergunta central do CEO:

> "Se o uso da plataforma está crescendo e a satisfação parece estável, por que o churn continua aumentando?"

Antes de iniciar a investigação, foram definidas cinco hipóteses principais:

1. Clientes churnam porque utilizam pouco a plataforma.
2. Clientes churnam devido a problemas de suporte.
3. Clientes churnam por características específicas de plano ou faturamento.
4. O churn está concentrado em segmentos específicos.
5. Existe deterioração progressiva da retenção ao longo do tempo.

A análise foi conduzida utilizando os cinco datasets fornecidos:

* Accounts
* Subscriptions
* Feature Usage
* Support Tickets
* Churn Events

Durante o processo, todas as conclusões passaram por múltiplas rodadas de auditoria crítica utilizando IA para contestação metodológica, validação das hipóteses e refinamento das conclusões.

---

# Resultados / Findings

## 1. O churn acelerou significativamente ao longo de 2024

A análise mostrou que o aumento não foi apenas consequência do crescimento da base.

| Mês    | Taxa de Churn |
| ------ | ------------- |
| Jan/24 | 8,3%          |
| Jun/24 | 11,3%         |
| Set/24 | 11,5%         |
| Out/24 | 13,7%         |
| Nov/24 | 12,6%         |
| Dez/24 | 19,2%         |

### Conclusão

A retenção deteriorou-se de forma consistente ao longo de 2024, indicando um problema estrutural e não uma flutuação pontual.

---

## 2. Baixa adoção não explica o churn

Comparação entre contas retidas e churnadas:

| Métrica                    | Retidas | Churnadas |
| -------------------------- | ------- | --------- |
| Uso médio da plataforma    | 495     | 522       |
| Features únicas utilizadas | 27,4    | 28,3      |

### Conclusão

Clientes churnados continuam utilizando a plataforma em níveis semelhantes aos clientes ativos.

Não há evidência de que a principal causa do churn seja falta de adoção.

---

## 3. Suporte não se mostrou o principal driver

Comparação entre contas retidas e churnadas:

| Métrica                  | Retidas | Churnadas |
| ------------------------ | ------- | --------- |
| Tickets por conta        | 4,08    | 4,00      |
| Tempo médio de resolução | 36,4h   | 35,5h     |
| Satisfação média         | 3,95    | 4,00      |

### Conclusão

Os indicadores operacionais de suporte permanecem relativamente estáveis entre os grupos.

Não há evidência forte de que a operação de suporte seja a principal responsável pelo aumento do churn.

---

## 4. DevTools apresenta o maior risco estrutural

Taxa de churn por segmento:

| Segmento      | Taxa de Churn |
| ------------- | ------------- |
| DevTools      | 30,9%         |
| FinTech       | 22,3%         |
| HealthTech    | 21,9%         |
| EdTech        | 16,5%         |
| Cybersecurity | 16,0%         |

### Conclusão

DevTools apresenta vulnerabilidade significativamente superior à média da empresa e deve ser tratado como segmento prioritário para retenção.

---

## 5. FinTech representa o maior risco financeiro

MRR perdido por segmento:

| Segmento      | MRR Perdido |
| ------------- | ----------- |
| FinTech       | US$ 265.619 |
| Cybersecurity | US$ 230.670 |
| DevTools      | US$ 228.544 |
| EdTech        | US$ 204.444 |
| HealthTech    | US$ 202.810 |

### Conclusão

Embora DevTools apresente a maior taxa percentual de churn, FinTech representa o maior impacto financeiro para a empresa.

---

## 6. Clientes adquiridos via Event apresentam retenção inferior

Taxa de churn por canal:

| Canal   | Taxa de Churn |
| ------- | ------------- |
| Event   | 30,2%         |
| Other   | 24,3%         |
| Ads     | 23,5%         |
| Organic | 17,5%         |
| Partner | 14,6%         |

### Conclusão

Clientes provenientes de eventos apresentam retenção significativamente inferior aos clientes adquiridos por parceiros, indicando possível problema de qualificação ou fit dos leads.

---

## 7. Alemanha e Estados Unidos merecem investigação específica

Taxa de churn por país:

| País | Churn |
| ---- | ----- |
| DE   | 32,0% |
| US   | 23,4% |
| FR   | 22,7% |
| IN   | 20,4% |
| UK   | 19,0% |
| CA   | 17,4% |
| AU   | 12,5% |

### Conclusão

A Alemanha apresentou a maior taxa percentual de churn da base, enquanto os Estados Unidos concentraram a maior quantidade absoluta de cancelamentos.

Pequenas melhorias de retenção nesses mercados possuem potencial relevante de impacto.

---

## 8. O discurso dos clientes mudou ao longo de 2024

Os feedbacks associados ao churn cresceram continuamente ao longo do ano:

* Missing Features
* Switched to Competitor
* Too Expensive

### Conclusão

Os dados sugerem deterioração da percepção de valor da plataforma para determinados segmentos de clientes.

O churn parece estar mais relacionado à competitividade percebida e aderência da solução do que a problemas operacionais.

---

# Impacto Potencial das Intervenções

Foram simulados cenários simples de melhoria de retenção utilizando os segmentos mais problemáticos identificados.

| Alavanca          | Churn Atual | Churn Alvo | Contas Preservadas | MRR Preservado | ARR Preservado |
| ----------------- | ----------- | ---------- | ------------------ | -------------- | -------------- |
| Canal Event       | 30,2%       | 22,0%      | ~8 contas          | ~US$ 17.104    | ~US$ 205.248   |
| Segmento DevTools | 30,9%       | 22,0%      | ~10 contas         | ~US$ 20.225    | ~US$ 242.700   |

### Conclusão

Apenas essas duas iniciativas possuem potencial para preservar aproximadamente:

* US$ 37.329 de MRR
* US$ 447.948 de ARR

---

# Protótipo Desenvolvido

Foi desenvolvido o protótipo:

## RavenStack Churn Risk Prioritization Engine

Objetivo:

Transformar os fatores de risco identificados durante a investigação em uma ferramenta operacional para Customer Success.

Principais funcionalidades:

* Priorização de contas por risco
* Explicação dos drivers de risco
* Segmentação por mercado
* Priorização financeira
* Exportação de contas críticas

Localização:

```text
solution/prototype/
```

O protótipo não busca prever churn de forma autônoma.

Seu objetivo é operacionalizar os sinais identificados durante a análise para apoiar decisões de retenção.

---

# Recomendações

## Prioridade 1 — Revisar aquisição via Event

Implementar revisão do processo de qualificação e onboarding dos leads provenientes de eventos.

---

## Prioridade 2 — Programa específico para DevTools

Conduzir entrevistas com clientes churnados e validar lacunas de produto recorrentes.

---

## Prioridade 3 — Proteger receita em FinTech

Criar programa de retenção dedicado para contas de alto valor financeiro.

---

## Prioridade 4 — Investigar mercados de maior risco

Realizar análise específica para Alemanha e Estados Unidos, buscando entender fatores locais associados ao churn.

---

## Prioridade 5 — Reforçar competitividade do produto

Mapear funcionalidades ausentes e comparações com concorrentes citadas pelos clientes.

---

# Limitações

* O dataset é sintético.
* Não foi possível identificar concorrentes específicos.
* O modelo exploratório de churn apresentou ROC-AUC de 0,61, insuficiente para tomada de decisão automatizada.
* Por esse motivo, os resultados do modelo foram utilizados como apoio para construção de um motor explicável de priorização de risco.

---

# Process Log — Como usei IA

Toda a documentação do processo está disponível em:

```text process-log/```

Incluindo:

* Hipóteses iniciais
* Exploração dos dados
* Auditorias críticas
* Revisões metodológicas
* Construção do protótipo
* Iterações realizadas

---

# Evidências

As evidências completas estão disponíveis em:

```text process-log/```

Incluindo:

* Screenshots
* Workflow detalhado
* Histórico das auditorias
* Processo de validação das conclusões

---

*Submissão enviada em: 09/06/2026*
