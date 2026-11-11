# Fluxo proposto: do ticket que entra até o fechamento

Aprovado pelo Jó em 2026-11-11 (rodada 47), com a recepção conversacional acrescentada na rodada 48. Cada etapa diz o que a IA faz, onde entra uma pessoa e qual dado sustenta a
etapa. O que é decisão e não achado do dado está marcado como **decisão**. O que ainda não tem valor definido
está marcado como **a definir**.

| # | Etapa | IA | Pessoa | Por que existe (dado) |
|---|---|---|---|---|
| 1 | Entrada | Registra data e hora de abertura, canal e cliente em todo ticket, de qualquer canal | Nenhuma | Nenhum ticket tem data de abertura hoje (lacuna 3); sem ela não há tempo de espera nem tendência |
| 2 | Recepção e conversa | Recebe o cliente de forma humanizada e conversa: a cada mensagem, trata o texto como a base de treino e recalcula a categoria e a confiança; enquanto a confiança ficar abaixo de 0,8, faz uma pergunta de esclarecimento | Nenhuma | Classificador com 87,0% de acerto no teste, contra 28,5% da linha de base. Simulação: com só as 10 primeiras palavras do ticket, o acerto é 78,2%; com o texto inteiro, 87,0%. Dos 3.271 tickets abaixo de 0,8 com 10 palavras, 35,6% passam de 0,8 com o texto inteiro. Mais informação do cliente aumenta o acerto. A conversa em si ainda não foi medida (**decisão** do Jó, rodada 48) |
| 3 | Roteamento | Confiança de 0,8 ou mais: envia direto para a fila da categoria | Se a confiança não passar de 0,8 depois do número máximo de perguntas, uma pessoa assume a conversa e faz a triagem | Com 0,8 sem conversa, a IA decide 68,4% com 96,4% de acerto e 31,6% iriam para triagem humana; a conversa da etapa 2 deve reduzir esse 31,6% (**decisão** do Jó, rodada 45) |
| 4 | Prioridade | Crítico entra no topo da fila e dispara alerta se ficar sem resposta além do prazo | Recebe o alerta e assume | A prioridade não muda o status hoje (p = 0,227): 692 críticos sem nenhuma resposta. Prazo do alerta: **a definir** com o diretor |
| 5 | Primeira resposta | Responde dúvida de produto, problema técnico e dúvida de cobrança com base no histórico e na documentação | Revisa por amostragem nos primeiros 30 dias | 2.819 tickets (33,3%) nunca tiveram resposta. A qualidade da IA não pode ser medida antes, porque o texto de resolução do Dataset 1 não tem sentido |
| 6 | Ação sobre dinheiro ou contrato | Coleta os dados, confere o pedido e deixa o caso pronto | **Sempre** decide e executa: reembolso, cancelamento, alteração ou estorno de cobrança | Reembolso e cancelamento são 3.447 tickets (40,7%), 867 críticos. Critério de **decisão** (ação irreversível), não achado do dado (resposta 5) |
| 7 | Acompanhamento | Faz follow-up do ticket que aguarda o cliente e avisa a pessoa quando o cliente responde | Retoma o caso | Dos 5.650 respondidos, 2.881 (51,0%) seguem aguardando o cliente: responder não é fechar (resposta 3). Intervalo do follow-up: **a definir** |
| 8 | Fechamento | Pede a nota de 1 a 5 e o NPS, com o motivo da nota; marca reabertura se o cliente voltar | Lê os motivos das notas baixas | Hoje 67,3% nunca avaliam e não há motivo nem reabertura (lacunas 7, 8 e 9) |
| 9 | Medição | Alimenta o dashboard com os 5 indicadores de linha de base e as métricas novas | O Jó e o diretor revisam em 30 dias e decidem o que sai do manual | Resposta 6 |

## Parâmetros

| Parâmetro | Valor | Origem |
|---|---|---|
| Limite de confiança para a IA rotear sozinha | 0,8 | Decisão do Jó, rodada 45; rever com 30 dias de operação |
| Número máximo de perguntas antes de passar para uma pessoa | a definir | Levantamento do processo; medir nos 30 dias quanto a conversa reduz a triagem humana |
| Prazo do alerta de crítico sem resposta | a definir | Diretor; o dado não tem tempo de espera |
| Intervalo do follow-up de quem aguarda o cliente | a definir | Levantamento do processo com o time |
| Amostra de revisão das respostas da IA | a definir | Levantamento do processo com o time |

## Limites deste desenho

- As filas por categoria seguem as 8 categorias do Dataset 2 (TI interna). As filas reais da empresa dependem do
  levantamento do processo e do time (lacunas 1 e 2).
- Integrações (sistema de pagamento, CRM, API) dependem dos sistemas da empresa (lacuna 10).
