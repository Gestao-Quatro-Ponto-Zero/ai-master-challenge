# Configuração da aba `Hoje` (valores em 23/10/2026)
Células azuis são entradas; o resto é fórmula (ver `formulas.md`). O app lê B2:B26 pela API.
| Célula | Rótulo | Valor | Nota |
|---|---|---|---|
| B1 | Hoje: o relógio da ferramenta. Mude só as células azuis. Tudo que depende de data (idade do deal, janela de recompra, prazo da fila) lê daqui. |  |  |
| B2 | Fim dos dados (última data de fechamento) | 2017-12-31 | Fonte: aba Won. |
| B3 | Dias passados desde o fim dos dados (N) | 0 | Entrada. O job diário soma 1 aqui. 0 = 31/12/2017. |
| B4 | Hoje | 2017-12-31 | Data de referência de toda a planilha. |
| B5 | Ciclo normal de quem ganha (mediana, dias) | 57 | Percentil deste arquivo. Num CRM real, recalcular todo mês. |
| B6 | Deal ganho mais longo (dias) | 138 | Ganhos e perdidos param nos mesmos 138 dias: limite do dataset, não lei de vendas. |
| B7 | Janela 'entrando na recompra' (dias) | 30 | Produto entra na janela quando a próxima compra estimada está a até este número de dias. |
| B8 | Janela 'pouco fora da recompra' (dias) | 30 | Até este atraso o deal antigo fica no passo 3 normal; além disso vai pro fim, como recuperação. |
| B9 | Modo de dono | Carteiras | Carteiras = regra do SOP (dono da conta, vivos ficam, GTK 500 com especialista). Como está hoje = cada vendedor vê o que já tem. |
| B10 | Prazo da fila sem conta (dias úteis) | 10 | Contado a partir do fim dos dados. |
| B11 | Requalificação de deal passado do ciclo (dias) | 30 |  |
| B12 | Deals por vendedor na primeira passada (seg a sex) | 18 | Usado no backtest como top N. |
| B13 | Ordem dentro do passo | Valor depois ICP | Desempate depois da urgência da recompra: cada passo ordena primeiro pelos dias até a janela e só então por esta chave. 'Valor depois ICP' entrou em 23/10: no backtest, sem a urgência na frente, deu 26% mais receita que 'ICP depois valor' nos 18 primeiros, com a mesma taxa de ganho. Com a urgência na frente, a ordem em uso ganha mais deals e menos receita (aba Backtest). 'ICP depois valor' continua disponível. |
| B14 | Deals sem conta por dia (no Meu dia) | 5 | Quantos deals da fila aparecem na lista do vendedor por dia, depois dos vivos. Identificou a conta no app, o deal entra na lista pelas regras. |
| B15 | Resumo de hoje |  |  |
| B16 | Deals abertos com conta (Lista do Dia) | 664 |  |
| B17 | Passo 1: vivo e na hora de recomprar | 17 |  |
| B18 | Passo 2: outros vivos | 3 |  |
| B19 | Passo 3: antigos, conta na hora de recomprar | 137 |  |
| B20 | Passo 4: o resto | 43 |  |
| B21 | Deals sem conta (fila) | 1425 |  |
| B22 | Fila fora do prazo | 0 |  |
| B23 | Confirmar: a conta comprou de outro vendedor depois de abrir | 464 | Deals a confirmar: outro vendedor (não o do deal) fechou o mesmo produto na conta depois de o deal abrir. Pode ser o mesmo pedido já atendido ou demanda separada; os dados não dizem qual. Fora dos passos 1 a 4, no fim da lista, com a ação de confirmar. Confirmada demanda separada no app, o deal volta pros passos. |
| B24 | Integração (lido pelo Apps Script) |  |  |
| B25 | E-mail que recebe as mensagens diárias na demo | (e-mail do dono da demo) | Na demo, todas as mensagens dos vendedores vão pra este endereço, com o nome do vendedor no assunto. |
| B26 | Slack webhook (opcional) |  | Se preenchido, o job diário também posta no Slack. |

Entradas (azuis): B3 (dias passados, o relógio), B7, B8, B9 (modo de dono: Carteiras ou Como está hoje), B10, B11, B12, B13 (desempate dentro do passo, depois da urgência), B14, B25 (e-mail da demo), B26 (webhook do Slack, opcional). Tudo o mais recalcula.
