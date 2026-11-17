# Lacunas de dado

Informações que o case precisa e que os arquivos não trazem. Cada lacuna foi levantada durante a análise,
com a evidência de que não existe e a pergunta que ela impede de responder. Nenhuma foi preenchida com
suposição.

Arquivos verificados: Dataset 1 (`customer_support_tickets.csv`, 8.469 tickets, 17 colunas) e Dataset 2
(`all_tickets_processed_improved_v3.csv`, 47.837 textos, 2 colunas: `Document`, `Topic_group`).

| # | Lacuna | Evidência | O que fica sem resposta | Rodada |
|---|---|---|---|---|
| 1 | Número de atendentes | Nenhuma coluna de atendente nos dois datasets; o brief diz "o time está sobrecarregado" sem número | Capacidade do time, carga por pessoa, se falta gente | 1 e 28 |
| 2 | Setorização do atendimento (equipes e quantas são) | Nenhuma coluna de equipe ou setor; as 8 categorias do Dataset 2 classificam o assunto do ticket, não quem atende | Roteamento atual, gargalo por equipe | 28 |
| 3 | Data de abertura do ticket | Dataset 1 só tem 1ª resposta e resolução | Tempo até a 1ª resposta, espera dos 2.819 sem resposta, tendência ("subiu", "caiu") | 1, 3 e 21 |
| 4 | Tempo trabalhado por ticket | Os tempos são carimbos de data, não esforço | Horas de trabalho reais, produtividade | 1 e 23 |
| 5 | Custo da hora do atendente | Nenhum dado financeiro | Custo do desperdício em reais | 1 e 23 |
| 6 | Registro de tempo confiável | 1.365 de 2.769 fechados (49,3%) com resolução antes da 1ª resposta | Tempo de resolução de metade dos fechados | 2 e 3 |
| 7 | Satisfação de quem não fechou | Nota só nos 2.769 fechados; 5.700 (67,3%) sem nota | Satisfação de dois terços da base | 17 e 18 |
| 8 | Motivo da nota | Só existe o número de 1 a 5 | Por que o cliente deu a nota | 21 |
| 9 | Reabertura de ticket | Nenhuma coluna de reabertura | Resolução na primeira vez, retrabalho | 1 |
| 10 | Segmento do negócio e sistema de pagamento (com ou sem API) | Nenhuma coluna; 42 produtos de categorias diferentes | Integrações possíveis da automação | 5 |
| 11 | Volume real | O brief cita ~30.000 tickets por ano; o arquivo tem 8.469 sem data de abertura | Volume por dia, mês ou ano | 12 |
| 12 | Chave entre os dois datasets | Nenhum campo em comum | Treinar no Dataset 2 e medir o resultado no Dataset 1 | 12 |

As rodadas remetem a `process-log/01-entendimento-do-problema.md`.
