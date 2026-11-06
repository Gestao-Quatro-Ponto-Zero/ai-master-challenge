# Teste independente em português (tickets escritos pelo Rafael)

Regra: nenhum ajuste do glossário com base nestes tickets. Correções de **lógica** (bugs) são permitidas e registradas.

| # | Ticket | Resultado | Avaliação do Rafael | Observação |
|---|---|---|---|---|
| 1 | "Quero cancelar!" | Foi para "IA pede detalhes"; após as perguntas, encaminhado para Administrative rights (verde) | **Errado — bug** | A regra "texto sem informação" era checada antes da lista vermelha, e as perguntas ao cliente não tinham opção de cancelamento. Corrigido: lista vermelha vem antes de tudo + opção "Cancelar ou pedir reembolso" + teste de regressão. Ao investigar, também foi removida a tradução "quero → wants", que puxava para Storage. |
| 2 | "Olá, meu monitor parou de funcionar." | Hardware 100%, verde, prioridade Normal | Correto | Gerou a decisão 16: pergunta de impacto para definir a prioridade |
| 3 | "Boa tarde, estou tendo um problema." | IA pede detalhes → cliente escolheu "Senha ou acesso", "estou parado" → Access, prioridade Alta | Correto | — |
| 4 | "Quero cancelar a conta" | Retenção, P2 | Questionado pelo Rafael: deveria ser P2 de cara? | Gerou a decisão 19: entra P3 com tag de risco e as respostas do cliente decidem se sobe. O print também revelou que a correção listava só categorias de TI (corrigido) e levou a IA a identificar o falso positivo "cancelar a reunião" (corrigido) |
