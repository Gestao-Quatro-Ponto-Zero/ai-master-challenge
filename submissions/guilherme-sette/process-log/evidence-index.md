# Evidence Index

## Objetivo

Este arquivo organiza as evidências do processo em um formato fácil de auditar. A ideia é responder objetivamente a três perguntas:

1. Como a IA foi usada ao longo do desenvolvimento?
2. Onde houve iteração, correção e julgamento humano?
3. A solução final realmente funciona?

## 1. Evidência do uso de IA

### Screenshots das sessões

- [codex_01.png](./screenshots/codex_01.png)
  - evidência de exploração inicial e definição do recorte do problema
- [codex_02.png](./screenshots/codex_02.png)
  - evidência de análise dos CSVs e extração de insights de negócio
- [codex_03.png](./screenshots/codex_03.png)
  - evidência da consolidação da abordagem `Deal Forecast + Seller Fit`
- [codex_04.png](./screenshots/codex_04.png)
  - evidência de implementação/iteração da dashboard
- [codex_05.png](./screenshots/codex_05.png)
  - evidência de bugs, correções e empacotamento da submissão

### Export da conversa

- [conversation-history.md](./chat-exports/conversation-history.md)
  - transcript complementar da thread, útil para leitura contínua do processo

## 2. Evidência de iteração e julgamento

### Linha do tempo

- [timeline.md](./timeline.md)
  - mostra a sequência de iterações e o progresso da solução

### Bugs e correções

- [bugs-and-fixes.md](./bugs-and-fixes.md)
  - mostra onde houve erro, diagnóstico e correção

### Inventário de artefatos

- [artifacts-inventory.md](./artifacts-inventory.md)
  - lista os artefatos entregues e sua função

### Narrativa principal

- [README.md](./README.md)
  - conecta os artefatos e explica o raciocínio por trás do uso de IA

## 3. Evidência da solução funcionando

- [dash_01.png](./screenshots/dash_01.png)
  - captura da dashboard final em execução
- [dash_02.png](./screenshots/dash_02.png)
  - captura complementar da dashboard final em execução

## 4. Evidência no código e no PR

- branch de submissão: `submission/guilherme-sette`
- pasta da entrega: `submissions/guilherme-sette/`
- commits e PR mostram a evolução registrada em git

## Leitura recomendada

Para revisar a submissão com rapidez:

1. Leia o [README principal](../README.md)
2. Veja este índice
3. Abra os screenshots `codex_*`
4. Abra os screenshots `dash_*`
5. Consulte [bugs-and-fixes.md](./bugs-and-fixes.md) e [timeline.md](./timeline.md)
