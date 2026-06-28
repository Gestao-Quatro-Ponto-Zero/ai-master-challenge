# Estrategia de Produto

## Tese

O valor da entrega esta em reduzir ambiguidade executiva: sair de "o churn subiu e os times discordam" para "estes sao os vetores mais provaveis, estas contas estao em risco e estas acoes devem acontecer primeiro".

## Cadeia de Valor

```text
Dados cruzados
  -> sinais relevantes
  -> narrativas de negocio
  -> decisoes priorizadas
  -> acoes operacionais
```

## Framework de Diagnostico

Usaremos a sequencia:

```text
Measure -> Segment -> Investigate -> Act
```

- **Measure:** medir churn por contas e por ARR/MRR.
- **Segment:** quebrar por plano, industria, canal, tenure, suporte, uso e billing.
- **Investigate:** buscar a causa mais provavel e separar correlacao de causalidade.
- **Act:** gerar watchlist, playbooks e backlog de acoes por stakeholder.

## Perguntas de Produto

1. O crescimento de uso e saudavel ou e uso com friccao?
2. A satisfacao media esconde segmentos insatisfeitos de alto valor?
3. O churn esta concentrado em plano, industria, canal, billing ou momento da assinatura?
4. Tickets, escalacoes e tempo de resposta antecipam churn?
5. Quais contas devem ser abordadas primeiro para proteger ARR?

## Narrativas Esperadas

Cada narrativa deve responder quatro perguntas simples:

- O que esta acontecendo?
- Por que isso importa financeiramente?
- Quem e afetado?
- O que fazer agora?

## Categorias MECE de Churn

Quando o dataset permitir, os churn events devem ser classificados sem sobreposicao:

- **Estrutural:** fim natural de contrato, empresa encerrada ou fator externo pouco controlavel.
- **Competitivo:** troca por concorrente, preco ou proposta de valor superior.
- **Produto:** bugs, falta de feature, baixa ativacao ou falha em realizar valor.
- **Servico:** suporte, SLA, escalacao, atendimento ou CS.
- **Involuntario:** falha de pagamento, billing ou problema operacional de cobranca.

Se os dados nao permitirem essa separacao, isso deve aparecer como limitacao e recomendacao de instrumentacao.

## Modelo de Recomendacao

Cada acao recomendada deve conter:

- **Acao:** comando claro, sem abstracao generica.
- **Dono:** CEO, CS, Produto, Receita ou Suporte.
- **Segmento alvo:** contas, plano, industria, canal ou cohort.
- **Evidencia:** metricas e comparacao com grupo controle.
- **Impacto esperado:** ARR protegido, churn evitavel, reducao de friccao ou melhoria de SLA.
- **Esforco:** baixo, medio ou alto.
- **Confianca:** alta, media ou baixa.

## Priorizacao

Usaremos uma matriz simples:

```text
Prioridade = Impacto financeiro x Confianca / Esforco
```

Essa formula nao substitui julgamento, mas evita que recomendacoes interessantes porem pouco acionaveis tomem espaco das decisoes urgentes.

## Entregaveis para Stakeholders

### CEO

- Executive summary.
- Causa raiz mais provavel.
- ARR/MRR em risco.
- Top 3 decisoes recomendadas.
- Leitura em formato conclusao-primeiro: conclusao, evidencia, decisao.

### Customer Success

- Lista de contas em risco.
- Playbook de intervencao por segmento.
- Sinais de alerta para monitorar semanalmente.

### Produto

- Features associadas a churn, erro, baixa adocao ou uso de baixa qualidade.
- Hipoteses de melhoria e experimentos recomendados.

### Suporte

- Relacao entre tickets, escalacoes, SLA e churn.
- Filas ou problemas que devem virar plano de reducao de friccao.

### Receita

- Planos, billing frequency, upgrades, downgrades e cohorts com maior exposicao.
- Acoes para proteger contas de alto valor.

## O que nao fazer

- Nao entregar apenas dashboards sem recomendacao.
- Nao vender correlacao como causalidade.
- Nao usar medias gerais para esconder segmentos criticos.
- Nao recomendar "melhorar experiencia" sem acao, dono e indicador.
- Nao construir ferramenta antes de validar a historia que os dados contam.
