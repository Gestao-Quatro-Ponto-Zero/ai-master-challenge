# Metodologia de scoring

## O que o score significa

O score do G4 Focus mede **prioridade relativa de trabalho** dentro do snapshot analisado. Ele não deve ser comunicado como chance causal ou probabilidade perfeitamente calibrada de fechamento.

Essa distinção é importante: o dataset fornece o estado final de oportunidades históricas, mas não traz snapshots semanais, sequência de mudanças de etapa nem atividades comerciais. Um modelo treinado sem cuidado poderia aprender informações que ainda não existiam quando o vendedor precisava decidir.

## Evidência que limitou a ambição do modelo

Foi usado um corte temporal simples como teste de realidade, e não uma divisão aleatória:

| Período de fechamento | Registros | Taxa de `Won` |
|---|---:|---:|
| antes de 2017-10-01 | 4.726 | 64,37% |
| Q4 de 2017 | 1.985 | 60,25% |

Produto, setor, região e porte, quando usados como sinais estáticos, produziram AUC de aproximadamente **0,489** no holdout e Brier pior que o baseline. Incluir o agente elevou a AUC apenas para cerca de **0,518**, ganho insuficiente para justificar o risco de atribuir ao vendedor efeitos de território e carteira.

Esses resultados são o motivo para manter duas saídas distintas:

- **conversion probability:** estimativa conservadora e regularizada, sem linguagem de certeza;
- **priority score:** ordena trabalho ao combinar conversão, frescor/acionabilidade e valor.

Em outras palavras, a solução não tenta maquiar sinal fraco com complexidade. O salto preditivo depende de eventos de CRM e snapshots que não existem neste dataset.

## Composição

Para oportunidades `Engaging`, o contrato de produto é:

```text
priority_score =
    0,65 x conversion_component
  + 0,20 x actionability_component
  + 0,15 x value_component
```

Cada componente é limitado ao intervalo de 0 a 100, e o resultado final também. Os pesos expressam uma escolha de produto: conversão vem primeiro, mas não pode apagar urgência operacional nem impacto financeiro.

### 1. Conversão — 65%

Resume sinais disponíveis antes do fechamento e estimativas históricas regularizadas. Taxas de grupos pequenos precisam recuar em direção à média global (backoff/smoothing), para evitar que dois ou três casos produzam certeza artificial.

O vendedor não entra no componente principal. Desempenho por agente continua visível para análise, mas usá-lo diretamente poderia transformar diferenças de território, carteira ou distribuição de leads em tratamento desigual.

### 2. Acionabilidade e frescor — 20%

Representa quão plausível é obter avanço agora. Tempo desde o engajamento é comparado com a distribuição dos ciclos históricos, sem usar o fechamento futuro da oportunidade aberta. Deals muito envelhecidos perdem prioridade de aceleração e migram para uma fila explícita de resgate ou desqualificação.

Isso evita um comportamento perigoso: deixar oportunidades antigas permanentemente no topo apenas porque têm valor alto.

### 3. Valor — 15%

Usa valor disponível antes do fechamento — por exemplo, preço de catálogo normalizado e contexto relativo do portfólio — e não `close_value`. A transformação por percentil ou faixa reduz a dominação de outliers.

## Prospecting é um problema diferente

As 500 oportunidades `Prospecting` não têm `engage_date`. Compará-las diretamente com `Engaging` inventaria uma idade operacional. Por isso, elas recebem uma `qualification_score` e a fila **Qualificar**, considerando potencial e completude dos dados. A interface deve usar o nome correto desse score e nunca misturar os dois rankings sem contexto.

## Filas operacionais

| Fila | Pergunta que responde | Ação sugerida |
|---|---|---|
| **Foco agora** | Quais negociações combinam evidência, timing e impacto? | Preparar próxima ação e contato prioritário. |
| **Acelerar** | Quais estão promissoras, mas precisam avançar? | Remover bloqueio e confirmar próximo passo. |
| **Nutrir** | Quais merecem acompanhamento sem consumir o topo da agenda? | Cadência leve e revisão programada. |
| **Resgatar ou desqualificar** | Quais estão paradas além do padrão histórico? | Tentar um resgate objetivo ou limpar o pipeline. |
| **Qualificar** | Quais prospects devem receber a primeira investigação? | Completar dados e decidir se devem engajar. |

Os limites concretos das filas devem estar versionados no `model-report.json`; assim, UI, API e documentação podem ser auditadas contra o mesmo resultado.

## Explicabilidade e confiança

Cada oportunidade deve carregar:

- score total e componentes;
- dois ou mais motivos em linguagem de negócio;
- fila e ação recomendada;
- confiança (`alta`, `média` ou `baixa`);
- flags de qualidade, como conta ausente ou relacionamento incompleto;
- referência temporal usada no cálculo.

Confiança não mede chance de ganhar. Ela comunica qualidade/cobertura da evidência disponível para aquele registro.

## Leakage: o que é proibido no score aberto

- `deal_stage` final como preditor;
- `close_date`;
- `close_value`;
- qualquer agregado calculado com eventos posteriores ao snapshot;
- normalização ou encoding ajustado antes de separar treino e validação em uma evolução de ML.

Esses campos podem ser usados apenas como alvo ou evidência histórica, dentro de uma janela conhecida.

## Validação adequada para a próxima versão

Com snapshots reais, a unidade de treino ideal seria uma oportunidade em uma data de corte, com alvo como `Won nos próximos 60 dias`. A validação deveria:

1. separar treino e teste por tempo;
2. impedir a mesma oportunidade de aparecer nos dois lados;
3. ajustar transformações somente no treino;
4. medir PR-AUC/ROC-AUC, Brier score e calibração;
5. medir principalmente `precision@k`, `recall@k`, lift e valor capturado no tamanho de fila que um vendedor consegue trabalhar;
6. comparar com baselines simples: ordem por valor, ordem por recência e priorização atual;
7. acompanhar cobertura e impacto por região, manager e vendedor, sem usar o grupo como atalho decisório.

O critério de sucesso não é apenas métrica offline: é aumentar conversão ou velocidade sem piorar qualidade da carteira nem concentrar oportunidades injustamente.

## Fonte de verdade executável

Este documento explica a intenção. Para os parâmetros e diagnósticos da versão em execução, consulte:

- `solution/generated/model-report.json`;
- `solution/generated/data-quality.json`;
- testes em `solution/analytics/tests/`.
