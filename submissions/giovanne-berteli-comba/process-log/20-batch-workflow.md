# Da qualidade do modelo à medição do trabalho — M07

O candidato questionou se carregar dados e gráficos reduziria tempo ou custo na
operação. A revisão reconheceu que o fluxo individual poderia acrescentar cópia,
troca de tela e confirmação. O candidato autorizou a mudança e pediu que o
aprendizado ficasse visível ao avaliador. A IA propôs e implementou lote e ensaio;
a direção de valor veio dessa objeção humana.

## Decisões e entrega

- CSV limitado e validado integralmente, sugestões apenas por ação explícita,
  tabela para conferência/correção e arquivo final com todas as linhas confirmadas.
  Reaproveita o serviço/modelo congelado. O arquivo não recalcula o diagnóstico.
- SQLite local separado, IDs estáveis, revisão com controle de versão, eventos
  preservados e exportação imutável. Falhas entram na revisão manual; recarregar
  não gera novas sugestões nem confirma automaticamente decisões.
- Protocolo prévio: oito tarefas de cada lado, uma por classe, grupos distintos
  do TRAIN, pareamento aproximado por comprimento sem selecionar por predição,
  ordem por hash e referências ocultas até o fim das duas etapas.
- Cronômetro do lote aberto até arquivo pronto, incluindo espera e pausas.
  Preparação do plano, CSV externo, download e entrega ao helpdesk ficam fora.
  É tempo decorrido do ensaio, sem conversão automática em caixa ou esforço ativo.
- Comparação mantém valores negativos, falhas e qualidade. Participante declarado
  e teste automatizado são identificados separadamente; todas as tentativas ficam
  no inventário. Não substitui o piloto prospectivo com dados representativos.
- Aprendizado destacado no README, start-here, guia do instrutor e Experimento;
  [explicação e instruções](../docs/operational-learning.md). Integrações continuam
  como ideias de continuidade. H01 exige uma pessoa executar as duas etapas.

## Verificação e correções

Os 93 testes de software passaram, sem skips. Cobrem importação inválida,
idempotência, confirmações, concorrência de revisão, falhas, interrupções, relógio,
amostragem só de treino, referências ocultas, diferença negativa e integração UI
com inferência real de um exemplo de treino. No teste de UI, a confirmação final
precisou de um rerun antes de clicar no botão habilitado; o teste foi corrigido
para respeitar essa interação, sem remover a proteção.

No navegador real, um CSV com dois exemplos de treino foi importado, sugestões
foram calculadas, linhas conferidas e registradas, a página recarregada e o lote
concluído. O download corresponde ao artefato fixado. Banco temporário e ator
**automated_test**; o tempo desse teste inclui preparação/interrupções e não é
evidência de produtividade humana. A primeira tentativa de abrir o seletor de
arquivo pelo input oculto falhou; o botão visível resolveu o upload. A conexão
com o servidor de teste foi retomada e as duas decisões persistidas sobreviveram.

O CodeTour real no VS Code/extension host isolado percorreu 13 âncoras. O verificador
reconciliou os 7.175 vetores e decisões finais salvos, sem carregar modelos, inferir
ou ajustar parâmetros. Todos os hashes congelados continuam iguais. Evidências:
[checagens](../docs/review-evidence/batch-delivery-checks.json),
[testes](../docs/review-evidence/batch-tests.txt),
[guia visível](../docs/review-evidence/batch-learning.png) e
[lote concluído](../docs/review-evidence/batch-workbench.png).

A captura 25 preserva 12 mensagens novas de quatro turnos retornados, com
hasMore=true, incluindo a objeção, a proposta e o pedido de execução. Comentários
mais recentes, resposta final atual e mensagens posteriores ao corte ficam para
a próxima extração. Não há execução humana H01 nem ganho de negócio medido.
P01 continua pendente; sem commit, push, publicação ou PR nesta etapa.
