# Diagnóstico operacional — 02/11/2026

## Contexto e objetivo

O usuário pediu para avançar depois do commit `9c78d01`. A A01 deveria responder
às perguntas de operação com números reproduzíveis, preservando o contrato D02:
snapshot não é taxa no tempo, satisfação tem uma população limitada e os dados
não medem esforço ativo ou duração total do ticket.

## Colaboração com IA

Codex retomou por instruções, status, plano e conhecimento relevante; os dois
recibos existentes passaram antes do uso dos dados. Escreveu o script, os testes,
os artefatos agregados e o [relatório](../docs/operational-diagnosis.md). A
[captura 13](chat-exports/13-operational-diagnosis-chat.md) preserva oito mensagens
novas, incluindo o final da pesquisa de PRs e a troca sobre o commit.

## Decisões, métodos e correções

- Configurar os limiares de exibição, sementes/permutação e cenários antes de
  inspecionar os resultados por grupo. A configuração é do agente e ilustrativa;
  não houve aprovação humana adicional de taxas, minutos ou custos.
- Analisar todas as partições simples, duplas e triplas de canal/prioridade/tipo.
  Cada partição descreve a mesma base; não se somam partições entre si. Grupos
  vazios mantêm taxas/notas indisponíveis, sem virar satisfação zero.
- Manter todos os 8.469 registros, com flags agregadas de descrição repetida e
  rótulo conflitante; sem correção silenciosa, deduplicação ou mudança dos brutos.
- Comparar médias de notas dos encerrados com uma fração de variação entre grupos
  e 999 permutações, com correção para três testes. Foram explicitadas as hipóteses
  de espaçamento das notas e permutabilidade, e os limites de proveniência/repetição.
  Não foi afirmada ausência de causas ou interações.
- Calcular capacidade hipotética subtraindo revisão, retrabalho e esforço fixo.
  Incluir cenário desfavorável e conservar resultado negativo; não usar métricas
  do classificador IT ou tempos decorrido/resolução como esforço manual.
- A primeira redação do intervalo de suporte das combinações usou limites ainda
  não conferidos. A verificação retornou 85–136 tickets e o texto foi corrigido
  antes da entrega. Os dados de cálculo não foram alterados para ajustar a narrativa.
- O check final do diff revelou que o CSV agregado usava CRLF padrão do writer.
  A geração foi fixada em LF para não produzir avisos de whitespace no Git;
  artefatos, testes, reprodução limpa e recibos foram regenerados após a correção.

## Execução e evidências

- [Código](../solution/diagnose_support.py), [configuração](../data/diagnosis-assumptions.json),
  [JSON](../data/diagnosis.json) e [150 segmentos](../data/diagnosis-segments.csv).
- [Testes](../tests/test_diagnosis.py): dez novos testes para populações, notas
  ausentes, grupos vazios, reconciliação, conflitos, variação/permutação, correção
  de testes, cenário calculado à mão, resultados negativos e integridade do CSV.
- [Suíte completa](../docs/review-evidence/diagnosis-tests.txt): 29 testes passaram.
- [Verificações](../docs/review-evidence/diagnosis-checks.json): diretório temporário
  novo, somente dois scripts próprios, configuração, manifesto e CSV bruto com hash
  copiados; JSON/CSV idênticos byte a byte. Não foi alegado novo download de rede.
- Sete partições reconciliadas em nove campos de contagem com os totais gerais.
  Não houve envio dos dados para serviços externos ou exposição de texto/PII
  individual nos resultados agregados.

O resultado encontrou 5.700 não encerrados (67,30%), 1.403 Critical não encerrados,
nota média 2,99/5 entre 2.769 encerrados e pouca variação marginal nas notas pelos
três campos testados. O cenário de referência dá 29,75 h/mês e o desfavorável
−26,67 h/mês; nenhum deles representa economia medida, caixa ou ROI financeiro.

## Estado e próxima ação

A01 concluída como diagnóstico da base, recomendações de investigação e cenários
explícitos. S01 deverá definir uma triagem assistida, handoff/falhas, anomalias
altas/baixas persistidas e filtráveis e medidas de sucesso. V00 continua antes de
qualquer seleção de modelo ou implementação do protótipo.

Os donos operacionais, a tabela oficial F07 e os recibos foram atualizados.
A auditoria anterior foi regenerada sem mudar seus resultados. Não houve treino,
avaliação de IA, medição de esforço real, deploy, commit ou publicação.

## Cobertura das conversas

Captura 13: oito mensagens adicionais de quatro turnos retornados após deduplicação
de IDs; `hasMore=true` para histórico anterior fora da página. O final desta A01
e as mensagens após a captura permanecem pendentes, sem reconstrução como citação.
